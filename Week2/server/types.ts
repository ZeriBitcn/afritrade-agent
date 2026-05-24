export interface DocumentChunk {
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

export interface IngestDocumentPayload {
  title: string;
  category: string;
  content: string;
  fileName: string;
}
