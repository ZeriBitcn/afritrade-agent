import React from "react";
import { FileText, Cpu, Sliders, CheckSquare, Layers } from "lucide-react";

interface DocumentChunk {
  id: string;
  docId: string;
  docTitle: string;
  docSection: string;
  category: string;
  fileName: string;
  content: string;
  embedding: number[];
  wordCount: number;
}

interface MatchResult {
  chunk: DocumentChunk;
  score: number;
}

interface SearchResultListProps {
  matches: MatchResult[];
  loading: boolean;
}

export default function SearchResultList({ matches, loading }: SearchResultListProps) {
  if (loading) {
    return (
      <div className="border border-zinc-200 bg-white rounded-xl p-6 text-center shadow-xs">
        <div className="flex flex-col items-center justify-center space-y-3">
          <div className="h-8 w-8 border-2 border-amber-805 border-t-transparent rounded-full animate-spin text-amber-800" />
          <p className="text-xs text-zinc-500 font-sans">
            Querying Qdrant index & computing semantic embeddings similarity...
          </p>
        </div>
      </div>
    );
  }

  if (!matches || matches.length === 0) {
    return (
      <div className="border border-zinc-200 bg-white rounded-xl p-8 text-center text-zinc-500 shadow-xs">
        <div className="flex flex-col items-center justify-center space-y-2">
          <FileText className="h-8 w-8 text-zinc-300" />
          <p className="text-xs font-sans">
            No matching documents retrieved yet. Type a query on the left to activate similarity search.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between text-xs text-zinc-500 font-sans">
        <span className="flex items-center font-semibold text-zinc-700">
          <Cpu className="h-3.5 w-3.5 mr-1 text-amber-700" /> Matches Retrieved from Vector Database
        </span>
        <span className="text-[10px] font-mono uppercase font-semibold text-emerald-800 bg-emerald-55/60 px-2 py-0.5 rounded">
          Sorted by Similarity
        </span>
      </div>

      <div className="space-y-3.5">
        {matches.map((item, idx) => {
          const { chunk, score } = item;
          const matchPercent = Math.round(score * 100);
          
          return (
            <div
              key={chunk.id}
              className="border border-zinc-200 bg-white rounded-xl overflow-hidden shadow-xs hover:border-zinc-300 transition-all"
            >
              {/* Header */}
              <div className="bg-zinc-50 border-b border-zinc-200 px-4 py-3 flex items-center justify-between">
                <div className="flex items-center space-x-2 truncate">
                  <FileText className="h-4 w-4 text-zinc-500 shrink-0" />
                  <span className="font-sans font-semibold text-zinc-800 text-xs truncate">
                    {chunk.docTitle}
                  </span>
                  <span className="text-[9px] text-zinc-400 font-mono hidden md:inline shrink-0">
                    ({chunk.fileName})
                  </span>
                </div>
                
                <div className="flex items-center space-x-2 shrink-0">
                  <span className="text-[10px] font-mono bg-amber-50 text-amber-900 border border-amber-200 px-1.5 py-0.2 rounded-sm font-semibold capitalize">
                    {chunk.category}
                  </span>
                  <span className="text-xs font-mono font-bold text-amber-800">
                    S={score.toFixed(3)}
                  </span>
                </div>
              </div>

              {/* Content body */}
              <div className="p-4 text-left">
                <p className="font-mono text-[10px] text-amber-900 uppercase tracking-wider mb-1.5 font-bold">
                  {chunk.docSection}
                </p>
                <p className="text-zinc-600 text-xs leading-relaxed font-sans whitespace-pre-wrap">
                  {chunk.content}
                </p>

                {/* Mathematical Vector visualization */}
                <div className="mt-3 pt-3 border-t border-zinc-100">
                  <div className="flex items-center justify-between text-[10px] text-zinc-400 font-mono mb-2">
                    <span className="flex items-center">
                      <Sliders className="h-3 w-3 mr-1" />
                      Hugging Face Embedding Vector (384-dimensions)
                    </span>
                    <span>Cosine Score: {matchPercent}%</span>
                  </div>

                  {/* Render a block visualizer of the actual 384 dimensional values */}
                  <div className="flex flex-wrap gap-0.5 max-h-4 overflow-hidden bg-zinc-900 p-1.5 rounded-xs">
                    {chunk.embedding.slice(0, 128).map((val, eIdx) => {
                      // Normalize val to full color ranges based on negative/positive vectors
                      const red = Math.floor((val + 1) * 120);
                      const green = Math.floor((1 - val) * 120);
                      const blue = Math.floor(Math.abs(val) * 255);
                      
                      return (
                        <span
                          key={eIdx}
                          title={`Index ${eIdx}: ${val}`}
                          style={{ backgroundColor: `rgb(${red}, ${green}, ${blue})` }}
                          className="h-1 w-1.5 rounded-2xs inline-block shrink-0"
                        />
                      );
                    })}
                    <span className="text-[8px] font-mono text-zinc-600 ml-1 leading-none shrink-0 border-l border-zinc-800 pl-1">
                      +256 dimensions
                    </span>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
