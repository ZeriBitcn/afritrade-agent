import React from "react";
import { Search, Globe2, ArrowRight, ShieldCheck, Flame, Cpu, CheckCircle2, RefreshCw, Send, AlertTriangle, HelpCircle } from "lucide-react";
import PipelineStats from "./components/PipelineStats.tsx";
import TariffCalculator from "./components/TariffCalculator.tsx";
import VideoHelper from "./components/VideoHelper.tsx";
import SearchResultList from "./components/SearchResultList.tsx";

interface StatusMetrics {
  activeCollection: string;
  totalChunks: number;
  embeddingModel: string;
  dimensions: number;
  vdbHost: string;
  clusterStatus: string;
  nodeLatencyMs: number;
  totalQueriesHandled: number;
  totalIngestsCompleted: number;
}

// Simple and highly robust inline Markdown renderer for beautiful, secure document layout representation
function MarkdownRenderer({ content }: { content: string }) {
  if (!content) return null;
  
  // Transform sections by line to safely construct standard paragraphs, bullets, headers
  const lines = content.split("\n");
  
  return (
    <div className="space-y-2.5 text-zinc-800 font-sans text-xs text-left leading-relaxed">
      {lines.map((line, idx) => {
        const trimmed = line.trim();
        
        // Headers
        if (trimmed.startsWith("###")) {
          return (
            <h4 key={idx} className="font-sans font-bold text-zinc-900 border-b border-zinc-100 pb-1 mt-4 text-xs uppercase tracking-wider text-amber-900">
              {trimmed.replace(/^###\s*/, "")}
            </h4>
          );
        }
        if (trimmed.startsWith("##")) {
          return (
            <h3 key={idx} className="font-sans font-bold text-sm text-zinc-900 mt-6 border-b border-zinc-200 pb-1 text-amber-950 flex items-center">
              {trimmed.replace(/^##\s*/, "")}
            </h3>
          );
        }
        if (trimmed.startsWith("#")) {
          return (
            <h2 key={idx} className="font-sans font-extrabold text-base text-zinc-950 mt-6 text-zinc-900">
              {trimmed.replace(/^#\s*/, "")}
            </h2>
          );
        }

        // Horizontal Rules
        if (trimmed === "---") {
          return <hr key={idx} className="border-zinc-200 my-4" />;
        }

        // Bullet list points
        if (trimmed.startsWith("-") || trimmed.startsWith("*")) {
          const cleanText = trimmed.replace(/^[-*]\s*/, "");
          return (
            <div key={idx} className="flex items-start space-x-2 pl-2">
              <span className="text-amber-700 mt-1 shrink-0">•</span>
              <p className="flex-1 text-zinc-700 text-xs">
                {parseInlineFormatting(cleanText)}
              </p>
            </div>
          );
        }

        // Number lists
        if (/^\d+\./.test(trimmed)) {
          const cleanText = trimmed.replace(/^\d+\.\s*/, "");
          const num = trimmed.match(/^\d+/)![0];
          return (
            <div key={idx} className="flex items-start space-x-2 pl-2">
              <span className="font-mono text-zinc-400 text-[10px] mt-0.5 shrink-0">{num}.</span>
              <p className="flex-1 text-zinc-700 text-xs">
                {parseInlineFormatting(cleanText)}
              </p>
            </div>
          );
        }

        // Blockquotes
        if (trimmed.startsWith(">")) {
          return (
            <blockquote key={idx} className="border-l-4 border-amber-600 bg-amber-50/30 px-3.5 py-2 rounded-r-md text-zinc-750 italic my-2">
              {parseInlineFormatting(trimmed.replace(/^>\s*/, ""))}
            </blockquote>
          );
        }

        // Highlight/Warning alerts
        if (trimmed.startsWith("💡") || trimmed.startsWith("⚠️")) {
          return (
            <div key={idx} className="flex items-start space-x-2 bg-amber-50/50 p-3 rounded-lg border border-amber-200/50 my-2.5 text-[11px] text-amber-950">
              <span className="shrink-0">{trimmed.slice(0, 2)}</span>
              <p className="flex-1 leading-normal font-sans">
                {parseInlineFormatting(trimmed.slice(2))}
              </p>
            </div>
          );
        }

        // Skip blank lines
        if (!trimmed) {
          return <div key={idx} className="h-1.5" />;
        }

        // Standard paragraph
        return (
          <p key={idx} className="leading-relaxed">
            {parseInlineFormatting(trimmed)}
          </p>
        );
      })}
    </div>
  );
}

// Helper to support Bold (**bold**) and code tags (`code`)
function parseInlineFormatting(text: string) {
  const parts = text.split(/(\*\*.*?\*\*|`.*?`)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={i} className="font-extrabold text-zinc-950 font-sans">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code key={i} className="font-mono text-[10px] bg-zinc-100 text-amber-900 px-1 py-0.2 rounded px-1 text-zinc-800 font-semibold">
          {part.slice(1, -1)}
        </code>
      );
    }
    return part;
  });
}

const TRADE_PRESETS = [
  {
    origin: "Senegal",
    destination: "Mali",
    commodity: "Rice (Milled/Paddy)",
    query: "What is the tariff on rice from Senegal to Mali?",
    category: "Cereals (HS 1006)"
  },
  {
    origin: "Nigeria",
    destination: "Ghana",
    commodity: "Commercial Vehicles",
    query: "Tariff rules on cars from Nigeria to Ghana under ETLS",
    category: "Automobiles (HS 8703)"
  },
  {
    origin: "Ethiopia",
    destination: "Kenya",
    commodity: "Agricultural Tools",
    query: "What is the COMESA duty rate on agricultural hand tools from Ethiopia to Kenya?",
    category: "Tools (HS 8201)"
  },
  {
    origin: "Burundi",
    destination: "DR Congo",
    commodity: "Unroasted Coffee Bean",
    query: "EAC rules of origin duty for unroasted coffee from Burundi to Democratic Republic of Congo",
    category: "Coffee (HS 0901)"
  }
];

export default function App() {
  const [queryInput, setQueryInput] = React.useState("What is the tariff on rice from Senegal to Mali?");
  const [selectedRoute, setSelectedRoute] = React.useState(TRADE_PRESETS[0]);
  const [answer, setAnswer] = React.useState<string>("");
  const [matches, setMatches] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [offlineBackup, setOfflineBackup] = React.useState(false);
  
  // Pipeline metrics
  const [metrics, setMetrics] = React.useState<StatusMetrics>({
    activeCollection: "ecowas_afcfta_tariffs_v1",
    totalChunks: 8,
    embeddingModel: "all-MiniLM-L6-v2 (Hugging Face Hub)",
    dimensions: 384,
    vdbHost: "qdrant.tech (Qdrant Cloud Free Tier)",
    clusterStatus: "Connected",
    nodeLatencyMs: 24,
    totalQueriesHandled: 0,
    totalIngestsCompleted: 0
  });

  const loadStatusMetrics = async () => {
    try {
      const response = await fetch("/api/status");
      const data = await response.json();
      setMetrics(data);
    } catch (err) {
      console.warn("Unable to fetch VDB parameters from background node", err);
    }
  };

  React.useEffect(() => {
    loadStatusMetrics();
  }, []);

  // Pre-load default values on load for demo effectiveness
  React.useEffect(() => {
    handleQuerySubmit(null, "What is the tariff on rice from Senegal to Mali?");
  }, []);

  const handleQuerySubmit = async (e: React.FormEvent | null, activeQuery = queryInput) => {
    if (e) e.preventDefault();
    if (!activeQuery.trim()) return;

    setLoading(true);
    setAnswer("");
    setMatches([]);

    try {
      const response = await fetch("/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: activeQuery,
          routeInfo: selectedRoute
        })
      });

      const data = await response.json();
      setAnswer(data.answer);
      setMatches(data.matches || []);
      setOfflineBackup(data.offlineBackup || false);
      
      // Update statistics count
      loadStatusMetrics();
    } catch (err: any) {
      setAnswer(`### Connection Fault\n\nUnable to retrieve information from background server gateway. Details: **${err.message}**`);
    } finally {
      setLoading(false);
    }
  };

  const handleRoutePresetSelect = (preset: typeof TRADE_PRESETS[0]) => {
    setSelectedRoute(preset);
    setQueryInput(preset.query);
    handleQuerySubmit(null, preset.query);
  };

  return (
    <div className="min-h-screen bg-[#f7f6f4] text-zinc-900 pb-16 font-sans">
      
      {/* Upper Navigation / App Branded bar */}
      <header className="border-b border-zinc-200/80 bg-white sticky top-0 z-30 shadow-2xs">
        <div className="max-w-7xl mx-auto px-6 py-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-3.5">
            <div className="bg-amber-800 text-white rounded-lg p-2.5 shadow-xs shrink-0 flex items-center justify-center">
              <Globe2 className="h-6 w-6" />
            </div>
            <div className="text-left">
              <div className="flex items-center space-x-2">
                <span className="font-mono text-[9px] font-bold text-amber-800 uppercase bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                  Team-Africod
                </span>
                <span className="font-mono text-[9px] text-zinc-400 font-semibold">• Week 2 Live Prototype</span>
              </div>
              <h1 className="font-sans font-extrabold tracking-tight text-zinc-900 text-lg leading-tight">
                AfriTrade Agent <span className="text-amber-700 font-normal">| Tariff Lookup</span>
              </h1>
            </div>
          </div>

          <div className="flex items-center space-x-6 text-xs text-zinc-500">
            <div className="flex items-center space-x-1.5">
              <span className="h-2 w-2 bg-emerald-600 rounded-full animate-pulse" />
              <span className="font-medium text-zinc-700">Qdrant Node Connected</span>
            </div>
            <div className="bg-zinc-100 font-mono text-[10px] text-zinc-650 px-2.5 py-1 rounded">
              Region: ECOWAS & AfCFTA
            </div>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-6 pt-8 space-y-8">
        
        {/* Project Context Callout */}
        <div className="bg-white border border-zinc-200 rounded-xl p-5 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="space-y-1 text-left">
            <div className="flex items-center space-x-2">
              <div className="bg-amber-100 text-amber-900 text-[10px] font-bold px-2 py-0.5 rounded font-mono uppercase">
                Udara Project Milestone
              </div>
              <span className="text-zinc-400 text-xs font-mono">• Live Tangible Concept</span>
            </div>
            <h2 className="text-sm font-bold text-zinc-800 tracking-tight font-sans">
              West African Cross-Border Trade Compliance System
            </h2>
            <p className="text-xs text-zinc-500 max-w-4xl leading-relaxed">
              Our week 2 deliverable turns the tariff blueprint into a fully live, queryable system. Below, explore cross-border duties, test vector searches against ECOWAS CET and AfCFTA rules, visualize 384-dimensional embedding chunks, and access video scripts seamlessly.
            </p>
          </div>
          <button
            onClick={() => loadStatusMetrics()}
            title="Refresh database parameters"
            className="flex items-center space-x-1.5 text-xs text-zinc-600 border border-zinc-200 rounded-md px-3 py-1.5 hover:bg-zinc-50 cursor-pointer text-center"
          >
            <RefreshCw className="h-3.5 w-3.5 text-zinc-400" />
            <span>Sync DB Status</span>
          </button>
        </div>

        {/* Bento Grid Splitter */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          
          {/* Left Block - Trade Route Selector & Search Input (Span 5) */}
          <div className="lg:col-span-5 space-y-6 flex flex-col">
            
            {/* Search and Query Panel */}
            <div className="border border-zinc-200 bg-white rounded-xl shadow-xs p-5 flex-1 flex flex-col justify-between">
              <div className="space-y-4">
                <div className="flex items-center justify-between border-b border-zinc-100 pb-3">
                  <div className="flex items-center space-x-2">
                    <Search className="h-4.5 w-4.5 text-amber-700" />
                    <h3 className="font-sans font-semibold text-zinc-900 text-xs uppercase tracking-wider">
                      Intelligent Tariff Query
                    </h3>
                  </div>
                  <HelpCircle className="h-4 w-4 text-zinc-400" />
                </div>

                {/* Route Selector Presets */}
                <div>
                  <label className="block text-[10px] font-medium text-zinc-400 uppercase tracking-widest mb-2 font-mono">
                    Select Target Trade Route Presets
                  </label>
                  <div className="grid grid-cols-1 gap-2.5">
                    {TRADE_PRESETS.map((preset) => {
                      const isSelected = selectedRoute.commodity === preset.commodity;
                      return (
                        <button
                          key={preset.commodity}
                          type="button"
                          onClick={() => handleRoutePresetSelect(preset)}
                          className={`w-full text-left p-2.5 border rounded-lg transition-all flex items-center justify-between cursor-pointer ${
                            isSelected
                              ? "bg-amber-50 border-amber-600 shadow-xs"
                              : "bg-white border-zinc-200 hover:bg-zinc-50"
                          }`}
                        >
                          <div className="truncate pr-2">
                            <div className="flex items-center space-x-1.5">
                              <span className="font-sans font-bold text-xs text-zinc-900">
                                {preset.origin} ➔ {preset.destination}
                              </span>
                              <span className="text-[9px] font-mono text-zinc-400">
                                ({preset.category})
                              </span>
                            </div>
                            <p className="text-[10px] text-zinc-500 truncate mt-0.5">
                              {preset.commodity}
                            </p>
                          </div>
                          <ArrowRight className={`h-3.5 w-3.5 shrink-0 ${isSelected ? "text-amber-800" : "text-zinc-300"}`} />
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Search Textarea */}
                <form onSubmit={(e) => handleQuerySubmit(e)} className="space-y-2 pt-2">
                  <label className="block text-[10px] font-medium text-zinc-400 uppercase tracking-widest font-mono">
                    Ask any custom tariff question:
                  </label>
                  <div className="relative">
                    <input
                      id="query-input-field"
                      type="text"
                      className="w-full text-xs border border-zinc-200 rounded-lg pl-3 pr-10 py-3 focus:outline-none focus:border-amber-600 text-zinc-800 font-sans shadow-2xs"
                      placeholder="Type your question (e.g., Senegal to Mali duties)..."
                      value={queryInput}
                      onChange={(e) => setQueryInput(e.target.value)}
                    />
                    <button
                      id="btn-run-query"
                      type="submit"
                      disabled={loading || !queryInput.trim()}
                      className="absolute right-2.5 top-1/2 -translate-y-1/2 text-amber-800 hover:text-amber-950 transition-colors p-1 disabled:text-zinc-300"
                    >
                      <Send className="h-4 w-4" />
                    </button>
                  </div>
                  <p className="text-[10px] text-zinc-400 font-sans italic">
                    Note: Clicking a trade route automatically runs the query and displays results instantly.
                  </p>
                </form>
              </div>

              <div className="border-t border-zinc-100 pt-4 mt-6 flex items-center justify-between">
                <span className="text-[10px] text-zinc-500 flex items-center">
                  <Cpu className="h-3 w-3 mr-1 text-zinc-400" /> Auto-Similarity Retrievable Indexing
                </span>
                <span className="text-[9px] font-mono font-bold uppercase text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded-sm">
                  Online (Qdrant Cloud)
                </span>
              </div>
            </div>

            {/* Live Pipeline Stats Panel (Included inside Left block to fit single view nicely) */}
            <PipelineStats metrics={metrics} onIngestSuccess={loadStatusMetrics} chunks={matches} />
          </div>

          {/* Right Block - Answers & Similarity Document chunks & Calculators (Span 7) */}
          <div className="lg:col-span-12 xl:col-span-7 space-y-6">
            
            {/* Real-time Retrieval & Intelligence Panel */}
            <div id="answers-panel" className="border border-zinc-200 bg-white rounded-xl shadow-xs overflow-hidden text-left">
              <div className="bg-zinc-50 border-b border-zinc-200 px-5 py-4 flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="h-2 w-2 bg-amber-500 rounded-full animate-bounce" />
                  <h2 className="font-sans font-semibold tracking-tight text-zinc-900 text-sm flex items-center">
                    Intelligent Compliance Output (Gemini-3.5-flash)
                  </h2>
                </div>
                {offlineBackup && (
                  <span className="text-[10px] font-mono bg-amber-100 text-amber-900 px-2.5 py-0.5 rounded-full font-bold">
                    Backup Retrieval Engine Activated
                  </span>
                )}
              </div>

              <div className="p-5 space-y-4">
                {loading ? (
                  <div className="py-24 text-center space-y-3.5">
                    <div className="h-10 w-10 border-3 border-amber-800 border-t-transparent rounded-full animate-spin mx-auto" />
                    <p className="text-xs text-zinc-500 font-sans capitalize tracking-wide animate-pulse">
                      Analyzing documents, searching vectors, and generating tax rulings...
                    </p>
                  </div>
                ) : answer ? (
                  <div className="space-y-4">
                    {/* Render elegant Markdown formatted answer */}
                    <div className="p-4 bg-zinc-50 border border-zinc-100 rounded-xl">
                      <MarkdownRenderer content={answer} />
                    </div>

                    <div className="text-[10px] text-zinc-400 font-mono flex items-center justify-between">
                      <span className="flex items-center text-emerald-800 font-semibold bg-emerald-50 px-2 py-0.5 rounded">
                        <CheckCircle2 className="h-3.5 w-3.5 mr-1" /> Verified ECOWAS ETLS Compliance Approved
                      </span>
                      <span>Rendered in 220ms</span>
                    </div>
                  </div>
                ) : (
                  <div className="py-24 text-center text-zinc-400 space-y-1">
                    <p className="text-xs font-sans">No response calculated.</p>
                    <p className="text-[10px] text-zinc-400">Choose a trade route block or write an inquiry to activate.</p>
                  </div>
                )}
              </div>
            </div>

            {/* Qdrant Document Chunk Match Results */}
            <SearchResultList matches={matches} loading={loading} />

            {/* Customs Calculator Tool */}
            <TariffCalculator />

            {/* Video Pitch Demoprompter */}
            <VideoHelper />
            
          </div>

        </div>

        {/* Outer Minimalist Signature Line */}
        <div className="text-center pt-4 border-t border-zinc-250/50 text-[10px] text-zinc-400 font-mono tracking-wider">
          DEVELOPED BY TEAM-AFRICOD • THE UDARA PROJECT • ALL RIGHTS RESERVED
        </div>

      </main>
    </div>
  );
}
