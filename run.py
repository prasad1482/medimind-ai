# -*- coding: utf-8 -*-
"""
MediMind AI - One-Click Launcher
Runs the Flask backend server with proper Python path setup.
"""

import os
import sys

# Ensure Python can print UTF-8 on Windows
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Ensure the project root is on the path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def main():
    print("\n" + "=" * 60)
    print("  MediMind AI - Medical Knowledge Assistant")
    print("=" * 60)

    # Check .env exists
    env_path = os.path.join(PROJECT_ROOT, ".env")
    if not os.path.exists(env_path):
        print("\n  ERROR: .env file not found!")
        print("  Please create a .env file with your API keys:")
        print("    GROQ_API_KEY=...")
        print("    PINECONE_API_KEY=...")
        print("    PINECONE_INDEX_HOST=...")
        print("    PINECONE_INDEX_NAME=...")
        sys.exit(1)
    else:
        print("  [OK] .env file found")

    # Check PDF exists
    pdf_path = os.path.join(PROJECT_ROOT, "data", "Medical_book.pdf")
    if not os.path.exists(pdf_path):
        print("  [!] WARNING: Medical PDF not found at data/Medical_book.pdf")
        print("  The server will start but RAG retrieval may fail.")
        print("  Place your medical PDF at: data/Medical_book.pdf")
        print("  Then run: python backend/ingest.py")
    else:
        size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
        print(f"  [OK] Medical_book.pdf found ({size_mb:.1f} MB)")

    print()
    print("  Server starting at: http://localhost:5000")
    print("  Open your browser to: http://localhost:5000")
    print("  Press Ctrl+C to stop.")
    print("=" * 60 + "\n")

    # Import and run directly (keeps Python path intact)
    from backend.app import app
    app.run(host="0.0.0.0", port=5000, debug=False)


if __name__ == "__main__":
    main()
