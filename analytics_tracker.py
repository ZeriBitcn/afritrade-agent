import sqlite3
import os
import random
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "analytics.db")

def init_db():
    """Initializes the SQLite tables for analytics and seeds mock data if the database is empty."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS visitors (
            session_id TEXT PRIMARY KEY,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            referrer TEXT DEFAULT 'Direct/Organic'
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            query TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            latency REAL,
            route_requested INTEGER,
            tariff_requested INTEGER,
            start_hub TEXT,
            end_hub TEXT,
            commodity TEXT,
            success INTEGER,
            error_message TEXT,
            FOREIGN KEY (session_id) REFERENCES visitors(session_id)
        )
    """)
    conn.commit()
    conn.close()
    
    # Seed mock data if empty
    seed_mock_data()

def seed_mock_data():
    """Seeds realistic historical data to represent distribution campaigns over the last 5 days."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if we already have queries
    cursor.execute("SELECT COUNT(*) FROM queries")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return
        
    print("Seeding mock analytics data for Week 4...")
    
    # 1. Define channels and referrers
    referrers = [
        'WhatsApp/Telegram Outreach', 
        'LinkedIn Campaign', 
        'Campus Ambassadors', 
        'Direct/Organic'
    ]
    referrer_weights = [0.45, 0.35, 0.12, 0.08] # 45% WhatsApp, 35% LinkedIn, 12% Campus, 8% Organic
    
    # 2. Generate visitors (approx. 62 visitors over the last 5 days)
    visitor_sessions = []
    base_time = datetime.now() - timedelta(days=5)
    
    for i in range(62):
        sess_id = f"sess_mock_{i:03d}_{random.randint(1000, 9999)}"
        ref = random.choices(referrers, weights=referrer_weights)[0]
        # Distribute signup/visits across the last 5 days
        visit_offset = random.random() * 5 # random float from 0 to 5 days
        visit_time = base_time + timedelta(days=visit_offset)
        
        cursor.execute("""
            INSERT INTO visitors (session_id, first_seen, last_seen, referrer)
            VALUES (?, ?, ?, ?)
        """, (sess_id, visit_time, visit_time + timedelta(minutes=random.randint(2, 45)), ref))
        
        visitor_sessions.append((sess_id, visit_time, ref))
        
    # 3. Generate query templates based on experiments
    queries_pool = [
        # WhatsApp/Telegram / General Queries
        ("What is the tariff rate on rice from Abidjan to Bamako?", "Abidjan", "Bamako", "rice", 0, 1),
        ("Tariff on smartphones from Lagos to Accra", "Lagos", "Accra", "smartphones", 0, 1),
        ("Explain duty and fastest route from Kano to Niamey for perishable crop", "Kano", "Niamey", "crops", 1, 1),
        ("What's the duty rate on smartphones from Cotonou to Ouagadougou?", "Cotonou", "Ouagadougou", "smartphones", 0, 1),
        ("How do I ship agricultural machinery from Lagos to Dakar?", "Lagos", "Dakar", "machinery", 1, 0),
        ("Is there an ETLS exemption for domestic maize from Lome to Accra?", "Lome", "Accra", "maize", 0, 1),
        ("Explain common external tariff for book import to Senegal", "Dakar", "Dakar", "books", 0, 1),
        ("What is the fastest corridor route between Abidjan and Ouagadougou?", "Abidjan", "Ouagadougou", "goods", 1, 0),
        
        # LinkedIn inspired queries (Tariffs, road roadblocks, FX rates, road conditions)
        ("What are the non-tariff barriers on Lome-Ouagadougou route?", "Lome", "Ouagadougou", "goods", 1, 1),
        ("Kano to Niamey road checkpoints and travel times", "Kano", "Niamey", "goods", 1, 0),
        ("Tariff on pharmaceutical medicines from Accra to Lagos", "Accra", "Lagos", "medicines", 0, 1),
        ("Fastest multi-modal transport from Dakar to Bamako by rail and road", "Dakar", "Bamako", "goods", 1, 0),
        ("Show me the exchange rate rules and duties for shipping computers to Cotonou", "Lagos", "Cotonou", "computers", 0, 1),
        ("How many check points between Lagos and Accra?", "Lagos", "Accra", "goods", 1, 0),
    ]
    
    # 4. Generate query logs (approx. 138 queries distributed across visitors)
    query_count = 0
    for sess_id, first_seen, ref in visitor_sessions:
        # Each visitor does 1-4 queries
        num_queries = random.randint(1, 4)
        for q_idx in range(num_queries):
            # Select random query template
            template = random.choice(queries_pool)
            query_text, start, end, commodity, has_route, has_tariff = template
            
            # Add some variability to query text
            decorations = ["", "Please show ", "Help me find ", "What's the "]
            q_text = random.choice(decorations) + query_text.lower()
            if random.random() < 0.2:
                q_text += "?"
                
            # Compute query time shortly after session first_seen
            q_time = first_seen + timedelta(seconds=random.randint(10, 120) * q_idx)
            latency = round(random.uniform(0.8, 3.8), 2)
            
            # Most succeed, a few fail
            success = 1 if random.random() > 0.05 else 0
            err_msg = None if success else "Internal timeout connecting to API pool"
            
            cursor.execute("""
                INSERT INTO queries (session_id, query, timestamp, latency, route_requested, tariff_requested, start_hub, end_hub, commodity, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sess_id, q_text, q_time, latency,
                1 if has_route else 0,
                1 if has_tariff else 0,
                start, end, commodity, success, err_msg
            ))
            query_count += 1
            
    conn.commit()
    conn.close()
    print(f"Successfully seeded {len(visitor_sessions)} sessions and {query_count} queries.")

def log_visitor(session_id: str, referrer: str = 'Direct/Organic'):
    """Logs or updates a visitor session."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verify referrer value
        if not referrer:
            referrer = 'Direct/Organic'
            
        cursor.execute("""
            INSERT INTO visitors (session_id, first_seen, last_seen, referrer)
            VALUES (?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?)
            ON CONFLICT(session_id) DO UPDATE SET last_seen = CURRENT_TIMESTAMP
        """, (session_id, referrer))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging visitor: {e}")

def log_query(session_id: str, query: str, latency: float, route_requested: bool, 
              tariff_requested: bool, start_hub: str, end_hub: str, commodity: str, 
              success: bool, error_message: str = None):
    """Logs a single query request with its metadata and response metrics."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO queries (session_id, query, latency, route_requested, tariff_requested, start_hub, end_hub, commodity, success, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id, query, latency,
            1 if route_requested else 0,
            1 if tariff_requested else 0,
            start_hub, end_hub, commodity,
            1 if success else 0, error_message
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging query: {e}")

def get_metrics() -> dict:
    """Aggregates and returns database metrics for the Streamlit dashboard."""
    metrics = {
        "total_visitors": 0,
        "total_queries": 0,
        "avg_latency": 0.0,
        "success_rate": 100.0,
        "top_routes": [],
        "feature_usage": {"Tariff Lookup": 0, "Route Finder": 0},
        "traffic_sources": {},
        "recent_queries": []
    }
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 1. Total Unique Visitors
        cursor.execute("SELECT COUNT(DISTINCT session_id) FROM visitors")
        metrics["total_visitors"] = cursor.fetchone()[0] or 0
        
        # 2. Total Queries
        cursor.execute("SELECT COUNT(*) FROM queries")
        metrics["total_queries"] = cursor.fetchone()[0] or 0
        
        if metrics["total_queries"] > 0:
            # 3. Average Latency
            cursor.execute("SELECT AVG(latency) FROM queries")
            metrics["avg_latency"] = round(cursor.fetchone()[0] or 0.0, 2)
            
            # 4. Success Rate
            cursor.execute("SELECT SUM(success) * 100.0 / COUNT(*) FROM queries")
            metrics["success_rate"] = round(cursor.fetchone()[0] or 0.0, 1)
            
            # 5. Top 5 Routes
            cursor.execute("""
                SELECT start_hub, end_hub, COUNT(*) as route_count 
                FROM queries 
                WHERE start_hub IS NOT NULL AND end_hub IS NOT NULL AND start_hub != '' AND end_hub != ''
                GROUP BY start_hub, end_hub
                ORDER BY route_count DESC
                LIMIT 5
            """)
            metrics["top_routes"] = [
                {"route": f"{row['start_hub']} ➔ {row['end_hub']}", "count": row['route_count']}
                for row in cursor.fetchall()
            ]
            
            # 6. Feature Usage (Tariff vs Route)
            cursor.execute("SELECT SUM(tariff_requested), SUM(route_requested) FROM queries")
            row = cursor.fetchone()
            metrics["feature_usage"] = {
                "Tariff Lookup": row[0] or 0,
                "Route Finder": row[1] or 0
            }
        
        # 7. Traffic sources breakdown
        cursor.execute("SELECT referrer, COUNT(*) as count FROM visitors GROUP BY referrer ORDER BY count DESC")
        metrics["traffic_sources"] = {row['referrer']: row['count'] for row in cursor.fetchall()}
        
        # 8. Recent Queries
        cursor.execute("""
            SELECT q.query, q.timestamp, q.latency, q.success, v.referrer
            FROM queries q
            LEFT JOIN visitors v ON q.session_id = v.session_id
            ORDER BY q.timestamp DESC
            LIMIT 10
        """)
        metrics["recent_queries"] = [
            {
                "query": row["query"],
                "timestamp": row["timestamp"],
                "latency": f"{row['latency']:.2f}s",
                "status": "Success ✓" if row["success"] == 1 else "Failed ⚠️",
                "channel": row["referrer"]
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
    except Exception as e:
        print(f"Error compiling metrics: {e}")
        
    return metrics
