"""
MediMind AI — Configuration Module
Loads environment variables and initializes shared clients.
"""

import os
from dotenv import load_dotenv
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

load_dotenv()

# ── API Keys ──────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_HOST = os.getenv("PINECONE_INDEX_HOST")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "medical-index")

# ── Model Config ──────────────────────────────────────────
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
GROQ_MODEL = "llama-3.3-70b-versatile"

# ── Retrieval Config ──────────────────────────────────────
TOP_K = 6                     # How many chunks to retrieve from Pinecone
CHUNK_SIZE = 512              # Tokens per chunk
CHUNK_OVERLAP = 50            # Token overlap between chunks
PDF_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "Medical_book.pdf")

# ── Pinecone Client ───────────────────────────────────────
_pinecone_client = None
_pinecone_index = None

def get_pinecone_client():
    """Initialize and return the Pinecone client."""
    global _pinecone_client
    if _pinecone_client is None:
        if not PINECONE_API_KEY:
            raise ValueError("PINECONE_API_KEY is not set")
        _pinecone_client = Pinecone(api_key=PINECONE_API_KEY)
    return _pinecone_client


def get_pinecone_index():
    """Initialize and return the Pinecone index object."""
    global _pinecone_index
    if _pinecone_index is None:
        if not PINECONE_INDEX_HOST:
            raise ValueError("PINECONE_INDEX_HOST is not set")
        client = get_pinecone_client()
        try:
            _pinecone_index = client.Index(name=PINECONE_INDEX_NAME, host=PINECONE_INDEX_HOST)
        except TypeError:
            _pinecone_index = client.Index(PINECONE_INDEX_NAME, host=PINECONE_INDEX_HOST)
    return _pinecone_index

# ── Embedding Model (loaded once, cached) ─────────────────
_embedding_model = None

def get_embedding_model():
    """Lazy-load the SentenceTransformer embedding model."""
    global _embedding_model
    if _embedding_model is None:
        print(f"[Config] Loading embedding model: {EMBEDDING_MODEL_NAME}")
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _embedding_model
