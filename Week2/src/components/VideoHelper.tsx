import React from "react";
import { Video, Play, BookOpen, Layers, CheckCircle } from "lucide-react";

export default function VideoHelper() {
  const [activeSegment, setActiveSegment] = React.useState<number>(1);
  const [isPlaying, setIsPlaying] = React.useState(false);
  const [countdown, setCountdown] = React.useState(60);

  React.useEffect(() => {
    let timer: NodeJS.Timeout;
    if (isPlaying && countdown > 0) {
      timer = setInterval(() => {
        setCountdown((c) => c - 1);
      }, 1000);
    } else if (countdown === 0) {
      setIsPlaying(false);
      setCountdown(60);
    }
    return () => clearInterval(timer);
  }, [isPlaying, countdown]);

  const toggleTimer = () => {
    setIsPlaying(!isPlaying);
    if (!isPlaying) {
      setCountdown(60);
    }
  };

  const segments = [
    {
      id: 1,
      duration: "0:00 - 0:15",
      title: "Introduction",
      script: "This is Week 2 for Team-Africod. Our project, AfriTrade Agent, now has a live, text-based prototype. You can visit this URL to try it yourself."
    },
    {
      id: 2,
      duration: "0:15 - 0:35",
      title: "Demonstrate the Query",
      script: "The task was to show a live tariff lookup. So let me type in a question that reflects a real West African trade route: 'What is the tariff on rice from Senegal to Mali?'"
    },
    {
      id: 3,
      duration: "0:35 - 0:55",
      title: "Show results & explain VDB",
      script: "Now, I'll run the query. The app searches our vector database of ECOWAS tariff documents and retrieves the most relevant information. As you can see, it finds and displays the correct tariff rule, citing the source. The data pipeline is working: ingestion from PDFs, embedding, and retrieval from our Qdrant vector database."
    },
    {
      id: 4,
      duration: "0:55 - 1:00",
      title: "Outro & Next Week",
      script: "Live and public. Next week, we integrate the LLM. This is AfriTrade Agent for The Udara Project."
    }
  ];

  return (
    <div id="video-helper" className="border border-zinc-200 bg-white rounded-xl shadow-xs overflow-hidden">
      {/* Header */}
      <div className="bg-zinc-50 border-b border-zinc-200 px-5 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-2.5">
          <Video className="h-5 w-5 text-amber-700" />
          <h2 className="font-sans font-semibold tracking-tight text-zinc-900 text-sm">
            Week 2 Video Sandbox & Demoprompter
          </h2>
        </div>
        <div className="flex items-center space-x-2">
          {isPlaying && (
            <span className="text-[10px] font-mono text-rose-700 bg-rose-50 px-2 py-0.5 rounded-full animate-pulse font-bold">
              REC: {countdown}s Left
            </span>
          )}
          <button
            onClick={toggleTimer}
            className={`px-3 py-1 rounded text-xs font-medium cursor-pointer transition-colors ${
              isPlaying
                ? "bg-rose-600 hover:bg-rose-700 text-white"
                : "bg-amber-800 hover:bg-amber-900 text-white"
            }`}
          >
            {isPlaying ? "Stop Timer" : "Practice Timing"}
          </button>
        </div>
      </div>

      <div className="p-5">
        <div className="flex items-start space-x-3 mb-4 bg-amber-50/50 p-3 rounded-lg border border-amber-100 text-xs text-amber-950 leading-relaxed">
          <BookOpen className="h-4 w-4 text-amber-700 mt-0.5 shrink-0" />
          <div>
            <span className="font-bold">Required Pitch Timing (60s total)</span>: Prioritize reading standard segments below while recording your screen. Click segments to isolate text and rehearse!
          </div>
        </div>

        {/* Script Selection Blocks */}
        <div className="space-y-3">
          {segments.map((seg) => {
            const isActive = activeSegment === seg.id;
            return (
              <div
                key={seg.id}
                onClick={() => setActiveSegment(seg.id)}
                className={`p-3 border rounded-lg cursor-pointer transition-all ${
                  isActive
                    ? "border-amber-700 bg-amber-50/20 shadow-xs"
                    : "border-zinc-200 bg-white hover:bg-zinc-50/60"
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-mono text-[10px] text-zinc-400 font-bold bg-zinc-100 px-1.5 py-0.2 rounded-sm">
                    {seg.duration}
                  </span>
                  <span className="font-sans font-medium text-xs text-zinc-800">
                    {seg.title}
                  </span>
                </div>
                <p className={`text-xs mt-1 leading-relaxed ${isActive ? "text-zinc-900 font-medium" : "text-zinc-500"}`}>
                  &ldquo;{seg.script}&rdquo;
                </p>
                {isActive && (
                  <div className="mt-2 text-[10px] text-amber-800 flex items-center">
                    <CheckCircle className="h-3 w-3 mr-1" /> Rehearsing Segment {seg.id}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        <div className="mt-4 pt-3 border-t border-zinc-100 flex items-center justify-between text-[11px] text-zinc-500 font-mono">
          <span className="flex items-center">
            <Layers className="h-3.5 w-3.5 mr-1 text-zinc-400" /> Target Route: Senegal ➔ Mali
          </span>
          <span>Pitch: Team-Africod (AfriTrade Agent)</span>
        </div>
      </div>
    </div>
  );
}
