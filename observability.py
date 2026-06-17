"""
observability.py — Structured Logging & Error Tracking for AfriTrade Agent

Provides:
  - AgentLogger: structured JSON logging per LangGraph node
  - Per-node entry/exit timing
  - LLM call tracking (model, latency, token estimates)
  - Error capture with traceback
  - SQLite persistence for error events (powers Analytics dashboard)

Logs are written to logs/agent.log (rotating, 5MB max, 3 backups).
"""

import logging
import json
import os
import time
import traceback as tb
import sqlite3
from datetime import datetime
from logging.handlers import RotatingFileHandler

# ──────────────────────────────────────────────
# Log directory setup
# ──────────────────────────────────────────────
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "agent.log")

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "analytics.db")


class JSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects for structured log analysis."""

    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Attach extra structured fields if present
        for field in ["node", "duration_ms", "model", "latency_ms", "status",
                      "prompt_tokens_est", "response_tokens_est", "error_type",
                      "session_id", "query", "hop", "chunks_retrieved",
                      "chunks_passed", "grade_scores"]:
            if hasattr(record, field):
                log_entry[field] = getattr(record, field)
        return json.dumps(log_entry, default=str)


def _get_file_handler():
    handler = RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    handler.setFormatter(JSONFormatter())
    handler.setLevel(logging.DEBUG)
    return handler


def _get_console_handler():
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "[%(asctime)s] %(levelname)s | %(name)s | %(message)s",
        datefmt="%H:%M:%S"
    ))
    handler.setLevel(logging.INFO)
    return handler


class AgentLogger:
    """
    Structured logger for AfriTrade Agent.
    
    Usage:
        logger = AgentLogger(session_id="abc123")
        logger.log_node_entry("router", {"query": "..."})
        # ... do work ...
        logger.log_node_exit("router", duration_ms=42.5, output_summary="Extracted 2 cities")
    """

    def __init__(self, session_id: str = "unknown"):
        self.session_id = session_id
        self._logger = logging.getLogger("afritrade.agent")

        # Avoid duplicate handlers on re-instantiation
        if not self._logger.handlers:
            self._logger.setLevel(logging.DEBUG)
            self._logger.addHandler(_get_file_handler())
            self._logger.addHandler(_get_console_handler())

        self._timers: dict = {}

    def log_node_entry(self, node_name: str, state_snapshot: dict = None):
        """Log when a LangGraph node begins execution."""
        self._timers[node_name] = time.time()
        summary = {}
        if state_snapshot:
            # Only log safe, small fields
            for k in ["query", "commodity", "start_hub", "end_hub",
                       "route_requested", "tariff_requested"]:
                if k in state_snapshot:
                    summary[k] = state_snapshot[k]

        self._logger.info(
            f"Node [{node_name}] started",
            extra={"node": node_name, "session_id": self.session_id,
                   "query": summary.get("query", "")}
        )

    def log_node_exit(self, node_name: str, duration_ms: float = None,
                      output_summary: str = ""):
        """Log when a LangGraph node completes execution."""
        if duration_ms is None and node_name in self._timers:
            duration_ms = round((time.time() - self._timers.pop(node_name)) * 1000, 1)

        self._logger.info(
            f"Node [{node_name}] completed in {duration_ms}ms — {output_summary}",
            extra={"node": node_name, "duration_ms": duration_ms,
                   "session_id": self.session_id}
        )

    def log_llm_call(self, model: str, prompt_tokens_est: int,
                     response_tokens_est: int, latency_ms: float, status: str):
        """Track every LLM API call with cost-relevant metrics."""
        self._logger.info(
            f"LLM call [{model}] — {status} in {latency_ms}ms "
            f"(~{prompt_tokens_est} prompt / ~{response_tokens_est} response tokens)",
            extra={
                "model": model, "prompt_tokens_est": prompt_tokens_est,
                "response_tokens_est": response_tokens_est,
                "latency_ms": latency_ms, "status": status,
                "session_id": self.session_id
            }
        )

    def log_retrieval_hop(self, hop: int, chunks_retrieved: int,
                          chunks_passed: int, grade_scores: list = None):
        """Track multi-hop RAG retrieval rounds with grading results."""
        self._logger.info(
            f"RAG Hop {hop}: retrieved {chunks_retrieved} chunks, "
            f"{chunks_passed} passed grading",
            extra={
                "hop": hop, "chunks_retrieved": chunks_retrieved,
                "chunks_passed": chunks_passed,
                "grade_scores": grade_scores or [],
                "session_id": self.session_id
            }
        )

    def log_error(self, node_name: str, error: Exception,
                  traceback_str: str = None):
        """Capture errors with full context; also persists to SQLite for dashboard."""
        if traceback_str is None:
            traceback_str = tb.format_exc()

        error_type = type(error).__name__
        error_message = str(error)

        self._logger.error(
            f"Error in [{node_name}]: {error_type} — {error_message}",
            extra={
                "node": node_name, "error_type": error_type,
                "session_id": self.session_id
            }
        )

        # Persist to SQLite for the Analytics dashboard
        _persist_error_event(node_name, error_type, error_message,
                             self.session_id)


# ──────────────────────────────────────────────
# SQLite Error Event Persistence
# ──────────────────────────────────────────────
def init_error_table():
    """Create the error_events table if it doesn't exist."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS error_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                node_name TEXT,
                error_type TEXT,
                error_message TEXT,
                session_id TEXT
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[observability] Failed to init error_events table: {e}")


def _persist_error_event(node_name: str, error_type: str,
                         error_message: str, session_id: str):
    """Write a single error event to the SQLite error_events table."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO error_events (node_name, error_type, error_message, session_id)
            VALUES (?, ?, ?, ?)
        """, (node_name, error_type, error_message, session_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[observability] Failed to persist error event: {e}")


def get_error_metrics() -> dict:
    """
    Returns error metrics for the Analytics dashboard:
      - error_count_24h: errors in the last 24 hours
      - error_rate: errors / total queries (%)
      - recent_errors: last 10 error events
      - errors_by_node: count per node name
    """
    metrics = {
        "error_count_24h": 0,
        "error_rate": 0.0,
        "recent_errors": [],
        "errors_by_node": {}
    }
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Error count (last 24h)
        cursor.execute("""
            SELECT COUNT(*) FROM error_events
            WHERE timestamp >= datetime('now', '-1 day')
        """)
        metrics["error_count_24h"] = cursor.fetchone()[0] or 0

        # Error rate (errors / total queries)
        cursor.execute("SELECT COUNT(*) FROM queries")
        total_queries = cursor.fetchone()[0] or 0
        cursor.execute("SELECT COUNT(*) FROM error_events")
        total_errors = cursor.fetchone()[0] or 0
        if total_queries > 0:
            metrics["error_rate"] = round(total_errors / total_queries * 100, 1)

        # Recent errors
        cursor.execute("""
            SELECT timestamp, node_name, error_type, error_message, session_id
            FROM error_events
            ORDER BY timestamp DESC
            LIMIT 10
        """)
        metrics["recent_errors"] = [
            {
                "timestamp": row["timestamp"],
                "node": row["node_name"],
                "type": row["error_type"],
                "message": row["error_message"][:120],
                "session": row["session_id"][:12] + "..."
            }
            for row in cursor.fetchall()
        ]

        # Errors by node
        cursor.execute("""
            SELECT node_name, COUNT(*) as cnt
            FROM error_events
            GROUP BY node_name
            ORDER BY cnt DESC
        """)
        metrics["errors_by_node"] = {
            row["node_name"]: row["cnt"] for row in cursor.fetchall()
        }

        conn.close()
    except Exception as e:
        print(f"[observability] Failed to get error metrics: {e}")

    return metrics


# Initialize the error table on import
init_error_table()
