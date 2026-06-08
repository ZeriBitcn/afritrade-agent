import pdfplumber
import csv
from embeddings import MiniLMEmbeddingModel
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance
import os
import re
from glob import glob

# Configuration
COLLECTION_NAME = "ecowas_tariffs"

def load_secrets():
    """Load secrets from .streamlit/secrets.toml without needing extra dependencies."""
    secrets = {}
    secrets_path = os.path.join(".streamlit", "secrets.toml")
    if os.path.exists(secrets_path):
        with open(secrets_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                match = re.match(r'^\s*([A-Za-z0-9_]+)\s*=\s*["\'](.*)["\']\s*$', line)
                if match:
                    secrets[match.group(1)] = match.group(2)
    return secrets

def extract_layout_aware_text(page):
    """Detect vertical gutters to split double-column PDFs, ensuring correct sentence flow."""
    words = page.extract_words()
    if not words:
        return ""
    
    width = float(page.width)
    height = float(page.height)
    
    # Analyze the middle region (40% to 60% of page width)
    mid_start = int(0.4 * width)
    mid_end = int(0.6 * width)
    
    overlap_counts = [0] * (mid_end - mid_start)
    for w in words:
        w_x0 = w["x0"]
        w_x1 = w["x1"]
        start_idx = max(mid_start, int(w_x0))
        end_idx = min(mid_end, int(w_x1))
        for x in range(start_idx, end_idx):
            if 0 <= x - mid_start < len(overlap_counts):
                overlap_counts[x - mid_start] += 1
                
    if not overlap_counts:
        return page.extract_text() or ""
        
    min_overlap = min(overlap_counts)
    
    # If overlap in the gutter is low (allowing 3 header/footer lines crossing the center), split columns
    if min_overlap < 4:
        gutter_xs = [i + mid_start for i, count in enumerate(overlap_counts) if count == min_overlap]
        gutter_center = sum(gutter_xs) / len(gutter_xs)
        
        left_bbox = (0, 0, gutter_center, height)
        right_bbox = (gutter_center, 0, width, height)
        
        left_page = page.within_bbox(left_bbox)
        right_page = page.within_bbox(right_bbox)
        
        left_text = left_page.extract_text() or ""
        right_text = right_page.extract_text() or ""
        
        return left_text + "\n" + right_text
    else:
        return page.extract_text() or ""

def main():
    # 1. Load configuration
    secrets = load_secrets()
    QDRANT_URL = secrets.get("QDRANT_URL")
    QDRANT_API_KEY = secrets.get("QDRANT_API_KEY")
    
    if not QDRANT_URL or not QDRANT_API_KEY:
        print("Warning: QDRANT_URL or QDRANT_API_KEY not found in secrets.toml!")
        # Fall back to env variables if available
        QDRANT_URL = QDRANT_URL or os.getenv("QDRANT_URL")
        QDRANT_API_KEY = QDRANT_API_KEY or os.getenv("QDRANT_API_KEY")

    if not QDRANT_URL:
        print("Error: QDRANT_URL is not set. Please add it to .streamlit/secrets.toml.")
        return

    # Look for data folder in a case-insensitive way
    PDF_FOLDER = "Data" if os.path.exists("Data") else "data"
    if not os.path.exists(PDF_FOLDER):
        print(f"Warning: PDF directory '{PDF_FOLDER}' not found. Creating it.")
        os.makedirs(PDF_FOLDER)

    print(f"Using PDF folder: '{PDF_FOLDER}'")
    print("Loading embedding model (sentence-transformers/all-MiniLM-L6-v2)...")
    model = MiniLMEmbeddingModel('sentence-transformers/all-MiniLM-L6-v2')

    print(f"Connecting to Qdrant Cloud at {QDRANT_URL}...")
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=60.0)

    # Create collection (recreate if it exists for a clean build)
    try:
        print(f"Recreating collection '{COLLECTION_NAME}' to ensure a clean build...")
        try:
            client.delete_collection(collection_name=COLLECTION_NAME)
        except Exception:
            pass
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
        print(f"Collection '{COLLECTION_NAME}' created successfully.")
    except Exception as e:
        print(f"Error initializing collection: {e}")
        return

    documents = []

    # Extract text from PDFs
    pdf_files = glob(os.path.join(PDF_FOLDER, "*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {PDF_FOLDER}!")
    else:
        print(f"Found {len(pdf_files)} PDF(s) to process.")
        for pdf_path in pdf_files:
            print(f"Processing PDF: {pdf_path}")
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    for page_num, page in enumerate(pdf.pages):
                        text = extract_layout_aware_text(page)
                        if text and len(text.strip()) > 100:  # Skip empty or very short pages
                            documents.append({
                                "text": text.strip(),
                                "source": os.path.basename(pdf_path),
                                "page": page_num + 1
                            })
            except Exception as e:
                print(f"Error reading {pdf_path}: {e}")

    # Extract text from CSVs
    csv_files = glob(os.path.join(PDF_FOLDER, "*.csv"))
    if not csv_files:
        print(f"No CSV files found in {PDF_FOLDER}!")
    else:
        print(f"Found {len(csv_files)} CSV(s) to process.")
        for csv_path in csv_files:
            print(f"Processing CSV: {csv_path}")
            try:
                with open(csv_path, "r", encoding="utf-8-sig") as f:
                    reader = csv.reader(f)
                    headers = next(reader, None)
                    if headers:
                        for row_idx, row in enumerate(reader):
                            if not any(row):
                                continue
                            row_text = ", ".join([f"{h}: {val}" for h, val in zip(headers, row) if h and val])
                            documents.append({
                                "text": row_text,
                                "source": os.path.basename(csv_path),
                                "page": row_idx + 1
                            })
            except Exception as e:
                print(f"Error reading {csv_path}: {e}")

    print(f"Extracted {len(documents)} documents from source files.")

    # Chunk large pages (split into ~500-character segments for better search)
    chunks = []
    for doc in documents:
        text = doc["text"]
        chunk_size = 500
        if len(text) <= chunk_size:
            chunks.append({
                "text": text,
                "source": doc["source"],
                "page": doc["page"]
            })
        else:
            for i in range(0, len(text), chunk_size):
                chunk = text[i:i+chunk_size]
                if len(chunk) > 50:
                    chunks.append({
                        "text": chunk,
                        "source": doc["source"],
                        "page": doc["page"]
                    })

    print(f"Created {len(chunks)} text chunks.")

    # Generate embeddings and upload to Qdrant in batches
    BATCH_SIZE = 50
    if chunks:
        print(f"Uploading {len(chunks)} chunks to Qdrant collection '{COLLECTION_NAME}' in batches of {BATCH_SIZE}...")
        for i in range(0, len(chunks), BATCH_SIZE):
            batch_chunks = chunks[i:i+BATCH_SIZE]
            batch_texts = [chunk["text"] for chunk in batch_chunks]
            
            # Batch encode sentences
            embeddings = model.encode(batch_texts)
            
            points = []
            for j, chunk in enumerate(batch_chunks):
                point_id = i + j
                points.append({
                    "id": point_id,
                    "vector": embeddings[j].tolist(),
                    "payload": {
                        "text": chunk["text"],
                        "source": chunk["source"],
                        "page": chunk["page"]
                    }
                })
                
            client.upsert(
                collection_name=COLLECTION_NAME,
                points=points
            )
            print(f"Uploaded {min(i + BATCH_SIZE, len(chunks))}/{len(chunks)} chunks")
        print("Ingestion complete!")
    else:
        print("No content to ingest.")

if __name__ == "__main__":
    main()
