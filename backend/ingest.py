"""
MediMind AI — PDF Ingestion Pipeline
Reads the medical PDF, splits into chunks, embeds, and upserts to Pinecone.
"""

import os
import sys
import time
import uuid
from tqdm import tqdm

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import (
    get_pinecone_index,
    get_embedding_model,
    PDF_PATH,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


BATCH_SIZE = 100  # Pinecone upsert batch size


def load_and_split_pdf(pdf_path: str):
    """Load PDF and split into overlapping text chunks."""
    print(f"[Ingest] Loading PDF: {pdf_path}")
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()
    print(f"[Ingest] Loaded {len(documents)} pages")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""],
    )
    chunks = splitter.split_documents(documents)
    print(f"[Ingest] Created {len(chunks)} chunks")
    return chunks


def embed_chunks(chunks, model):
    """Generate embeddings for all chunks."""
    print("[Ingest] Generating embeddings...")
    texts = [c.page_content for c in chunks]
    embeddings = model.encode(texts, batch_size=64, show_progress_bar=True)
    return embeddings


def upsert_to_pinecone(chunks, embeddings, index):
    """Upsert all embedded chunks to Pinecone in batches."""
    print("[Ingest] Upserting to Pinecone...")
    vectors = []

    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        # Sanitize metadata: remove None values and truncate long strings
        source = chunk.metadata.get("source", "Medical_book.pdf")
        page = chunk.metadata.get("page", 0)
        text = chunk.page_content.strip()

        vectors.append({
            "id": f"chunk-{i:06d}-{uuid.uuid4().hex[:8]}",
            "values": embedding.tolist(),
            "metadata": {
                "text": text[:2000],           # Pinecone metadata limit
                "source": str(source),
                "page": int(page) + 1,         # 1-indexed for display
                "chunk_index": i,
            }
        })

    # Upload in batches
    total_batches = (len(vectors) + BATCH_SIZE - 1) // BATCH_SIZE
    for batch_num in tqdm(range(total_batches), desc="Uploading batches"):
        start = batch_num * BATCH_SIZE
        end = start + BATCH_SIZE
        batch = vectors[start:end]
        index.upsert(vectors=batch)
        time.sleep(0.1)  # Avoid rate limiting

    print(f"[Ingest] ✅ Successfully upserted {len(vectors)} vectors to Pinecone!")


def check_index_stats(index):
    """Print current Pinecone index statistics."""
    stats = index.describe_index_stats()
    total_vectors = stats.get("total_vector_count", 0)
    print(f"\n[Ingest] 📊 Index Stats:")
    print(f"  Total vectors: {total_vectors}")
    print(f"  Dimension: {stats.get('dimension', 'N/A')}")
    return total_vectors


def run_ingestion():
    """Main ingestion pipeline."""
    print("\n" + "="*60)
    print("  MediMind AI — Medical PDF Ingestion Pipeline")
    print("="*60 + "\n")

    if not os.path.exists(PDF_PATH):
        print(f"[Ingest] ❌ PDF not found at: {PDF_PATH}")
        sys.exit(1)

    # Initialize clients
    index = get_pinecone_index()
    model = get_embedding_model()

    # Check if already indexed
    total = check_index_stats(index)
    if total > 0:
        ans = input(f"\n[Ingest] ⚠️  Index already has {total} vectors. Re-ingest? (y/N): ")
        if ans.lower() != "y":
            print("[Ingest] Skipping ingestion. Using existing index.")
            return

    # Pipeline
    chunks = load_and_split_pdf(PDF_PATH)
    embeddings = embed_chunks(chunks, model)
    upsert_to_pinecone(chunks, embeddings, index)

    # Final stats
    time.sleep(2)  # Wait for index to update
    check_index_stats(index)
    print("\n[Ingest] 🎉 Ingestion complete! MediMind AI is ready.\n")


if __name__ == "__main__":
    run_ingestion()
