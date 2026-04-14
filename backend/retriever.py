"""
MediMind AI — Hybrid Retriever
Combines Pinecone semantic search with BM25 keyword reranking.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rank_bm25 import BM25Okapi
from backend.config import get_pinecone_index, get_embedding_model, TOP_K


def semantic_search(query: str, index, model, top_k: int = TOP_K):
    """
    Embed the query and search Pinecone for semantically similar chunks.
    Returns a list of (score, metadata) tuples.
    """
    query_embedding = model.encode([query])[0].tolist()

    response = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True,
    )

    results = []
    for match in response.get("matches", []):
        results.append({
            "score": match["score"],
            "text": match["metadata"].get("text", ""),
            "source": match["metadata"].get("source", "Unknown"),
            "page": match["metadata"].get("page", "?"),
            "chunk_index": match["metadata"].get("chunk_index", 0),
            "id": match["id"],
        })
    return results


def bm25_rerank(query: str, candidates: list, top_k: int = 4) -> list:
    """
    Rerank semantic search candidates using BM25 keyword relevance.
    Returns the top_k most relevant chunks.
    """
    if not candidates:
        return []

    # Tokenize corpus for BM25
    tokenized_corpus = [doc["text"].lower().split() for doc in candidates]
    bm25 = BM25Okapi(tokenized_corpus)

    tokenized_query = query.lower().split()
    bm25_scores = bm25.get_scores(tokenized_query)

    # Merge scores: 60% semantic + 40% BM25 (normalized)
    max_semantic = max(doc["score"] for doc in candidates) or 1.0
    max_bm25 = max(bm25_scores) or 1.0

    for i, doc in enumerate(candidates):
        semantic_norm = doc["score"] / max_semantic
        bm25_norm = bm25_scores[i] / max_bm25
        doc["hybrid_score"] = 0.6 * semantic_norm + 0.4 * bm25_norm

    # Sort by hybrid score descending
    reranked = sorted(candidates, key=lambda x: x["hybrid_score"], reverse=True)
    return reranked[:top_k]


def retrieve(query: str, top_k: int = 4) -> dict:
    """
    Full hybrid retrieval pipeline.
    Returns context string, sources list, and raw chunks for the LLM.
    """
    index = get_pinecone_index()
    model = get_embedding_model()

    # Step 1: Broad semantic search (fetch 2x for reranking)
    candidates = semantic_search(query, index, model, top_k=TOP_K)

    if not candidates:
        return {
            "context": "No relevant medical information found in the knowledge base.",
            "sources": [],
            "chunks": [],
        }

    # Step 2: BM25 reranking
    final_chunks = bm25_rerank(query, candidates, top_k=top_k)

    # Step 3: Build context block for LLM
    context_parts = []
    sources = []

    for i, chunk in enumerate(final_chunks, 1):
        context_parts.append(
            f"[Source {i} — Page {chunk['page']}]\n{chunk['text']}"
        )
        if chunk['page'] not in [s['page'] for s in sources]:
            sources.append({
                "page": chunk['page'],
                "excerpt": chunk['text'][:200] + "..." if len(chunk['text']) > 200 else chunk['text'],
                "score": round(chunk.get("hybrid_score", chunk["score"]), 3),
            })

    context = "\n\n---\n\n".join(context_parts)

    return {
        "context": context,
        "sources": sources,
        "chunks": final_chunks,
    }
