import pdfplumber
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

# 1. Load configuration
secrets = load_secrets()
QDRANT_URL = secrets.get("QDRANT_URL", "https://your-cluster.cloud.qdrant.io")
QDRANT_API_KEY = secrets.get("QDRANT_API_KEY", "your-api-key")

# Look for data folder in a case-insensitive way
PDF_FOLDER = "Data" if os.path.exists("Data") else "data"
if not os.path.exists(PDF_FOLDER):
    print(f"Warning: PDF directory '{PDF_FOLDER}' not found. Creating it.")
    os.makedirs(PDF_FOLDER)

print(f"Using PDF folder: '{PDF_FOLDER}'")
print("Loading embedding model (sentence-transformers/all-MiniLM-L6-v2)...")
model = MiniLMEmbeddingModel('sentence-transformers/all-MiniLM-L6-v2')

print(f"Connecting to Qdrant Cloud at {QDRANT_URL}...")
client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

# Create collection if it doesn't exist
try:
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
    )
    print(f"Collection '{COLLECTION_NAME}' created successfully.")
except Exception as e:
    print(f"Collection may already exist or error occurred: {e}")

# Extract text from PDFs
documents = []
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
                text = page.extract_text()
                if text and len(text.strip()) > 100:  # Skip empty or very short pages
                    documents.append({
                        "text": text.strip(),
                        "source": os.path.basename(pdf_path),
                        "page": page_num + 1
                    })
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")

print(f"Extracted {len(documents)} pages from PDFs.")

# Chunk large pages (split into ~500-character segments for better search)
chunks = []
for doc in documents:
    text = doc["text"]
    chunk_size = 500
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i+chunk_size]
        if len(chunk) > 50:
            chunks.append({
                "text": chunk,
                "source": doc["source"],
                "page": doc["page"]
            })

print(f"Created {len(chunks)} text chunks.")

# Generate embeddings and upload to Qdrant
if chunks:
    print(f"Uploading {len(chunks)} chunks to Qdrant collection '{COLLECTION_NAME}'...")
    for idx, chunk in enumerate(chunks):
        embedding = model.encode(chunk["text"]).tolist()
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=[{
                "id": idx,
                "vector": embedding,
                "payload": {
                    "text": chunk["text"],
                    "source": chunk["source"],
                    "page": chunk["page"]
                }
            }]
        )
        if idx % 50 == 0 or idx == len(chunks) - 1:
            print(f"Uploaded {idx + 1}/{len(chunks)} chunks")
    print("Ingestion complete!")
else:
    print("No content to ingest.")
