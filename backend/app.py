"""
MediMind AI — Flask API Server
Main entry point for the backend REST API.
"""

import os
import sys
import json
import time
import traceback
from datetime import datetime

# ── Ensure project root is on path ───────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS

from backend.retriever import retrieve
from backend.llm import generate_response, generate_streaming

# ── App Setup ─────────────────────────────────────────────
app = Flask(
    __name__,
    static_folder=os.path.join(PROJECT_ROOT, "frontend"),
)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ── Request Logging ───────────────────────────────────────
@app.before_request
def log_request():
    if request.path.startswith("/api"):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {request.method} {request.path}")


# ── Health Check ──────────────────────────────────────────
@app.route("/api/health", methods=["GET"])
def health():
    """Returns server health status and index stats."""
    try:
        from backend.config import get_pinecone_index
        index = get_pinecone_index()
        stats = index.describe_index_stats()
        # Handle both dict-style and object-style Pinecone responses
        if hasattr(stats, "total_vector_count"):
            vector_count = stats.total_vector_count
        else:
            vector_count = stats.get("total_vector_count", 0)
        return jsonify({
            "status": "healthy",
            "model": "llama-3.3-70b-versatile",
            "vectors_indexed": vector_count,
            "timestamp": datetime.utcnow().isoformat(),
        })
    except Exception as e:
        traceback.print_exc()
        # Return 200 so the frontend shows "online" even if Pinecone stats fail
        return jsonify({
            "status": "degraded",
            "model": "llama-3.3-70b-versatile",
            "vectors_indexed": 0,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        })


# ── Chat Endpoint ─────────────────────────────────────────
@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Main chat endpoint.
    Accepts: { "query": str, "stream": bool }
    Returns: { "answer": str, "sources": list, "query": str, "time_taken": float }
    """
    data = request.get_json(silent=True) or {}
    query = data.get("query", "").strip()
    use_stream = data.get("stream", False)

    if not query:
        return jsonify({"error": "Query cannot be empty."}), 400

    if len(query) > 1000:
        return jsonify({"error": "Query too long. Please keep it under 1000 characters."}), 400

    start_time = time.time()

    try:
        # ── Retrieval ──
        retrieval = retrieve(query)
        context   = retrieval["context"]
        sources   = retrieval["sources"]

        # ── Generation (streaming) ──
        if use_stream:
            def event_stream():
                try:
                    for chunk in generate_streaming(query, context):
                        yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                    yield f"data: {json.dumps({'done': True, 'sources': sources})}\n\n"
                except Exception as ex:
                    yield f"data: {json.dumps({'error': str(ex)})}\n\n"

            return Response(
                event_stream(),
                mimetype="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Accel-Buffering": "no",
                }
            )

        # ── Generation (non-streaming) ──
        answer  = generate_response(query, context)
        elapsed = round(time.time() - start_time, 2)

        return jsonify({
            "answer":     answer,
            "sources":    sources,
            "query":      query,
            "time_taken": elapsed,
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "error":   "An internal error occurred. Please try again.",
            "details": str(e),
        }), 500


# ── Ingest Trigger ────────────────────────────────────────
@app.route("/api/ingest", methods=["POST"])
def trigger_ingest():
    """Trigger PDF ingestion pipeline (admin use)."""
    try:
        from backend.ingest import run_ingestion
        import threading
        thread = threading.Thread(target=run_ingestion, daemon=True)
        thread.start()
        return jsonify({"message": "Ingestion started in background."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Serve Frontend ────────────────────────────────────────
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    """Serve the HTML frontend."""
    frontend_dir = os.path.join(PROJECT_ROOT, "frontend")
    if path and os.path.exists(os.path.join(frontend_dir, path)):
        return send_from_directory(frontend_dir, path)
    return send_from_directory(frontend_dir, "index.html")


# ── Entry Point ───────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  MediMind AI Server Starting…")
    print("=" * 60)
    print(f"  Frontend:  http://localhost:5000")
    print(f"  Health:    http://localhost:5000/api/health")
    print(f"  Chat API:  http://localhost:5000/api/chat")
    print("=" * 60 + "\n")
    app.run(host="0.0.0.0", port=5000, debug=False)
