<h1 align="center">
  <img src="https://img.shields.io/badge/MediMind-AI-00b4cc?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB2aWV3Qm94PSIwIDAgNDQgNDQiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjQ0IiBoZWlnaHQ9IjQ0IiByeD0iMTMiIGZpbGw9IiMwMGI0Y2MiLz48cGF0aCBkPSJNMjIgMTB2MjRNMTAgMjJoMjQiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMy44IiBzdHJva2UtbGluZWNhcD0icm91bmQiLz48L3N2Zz4=" alt="MediMind AI" />
  <br/>MediMind AI
</h1>

<p align="center">
  <strong>AI-powered Medical Knowledge Assistant</strong><br/>
  Retrieval-Augmented Generation (RAG) chatbot using Groq LLM + Pinecone Vector DB
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Flask-2.x-000000?style=flat-square&logo=flask&logoColor=white" />
  <img src="https://img.shields.io/badge/Groq-LLaMA_3.3_70B-F55036?style=flat-square" />
  <img src="https://img.shields.io/badge/Pinecone-Vector_DB-00B4CC?style=flat-square" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" />
</p>

---

## Overview

**MediMind AI** is a professional medical knowledge chatbot that uses **Retrieval-Augmented Generation (RAG)** to answer medical questions from a curated medical textbook. It combines:

- 🧠 **LLaMA 3.3 70B** (via Groq API) for fast, intelligent responses
- 📚 **Pinecone** vector database for semantic retrieval
- 🔍 **Hybrid search** — Pinecone semantic search + BM25 keyword reranking
- 🎨 **Professional dark-blue medical UI** built with pure HTML/CSS/JS

> ⚠️ **Disclaimer:** MediMind AI is for educational purposes only. It is not a substitute for professional medical advice, diagnosis, or treatment.

---

## Features

| Feature | Description |
|---|---|
| 🤖 RAG-based QA | Retrieves relevant medical text chunks before answering |
| 🔍 Hybrid Retrieval | Semantic (Pinecone) + keyword (BM25) reranking |
| 💬 Concise Responses | Short, focused answers — no information overload |
| 📋 Source Citations | Expandable source panel with page references |
| 🗂️ Clickable Sidebar | 6 medical topics + 4 quick-query shortcuts |
| ⚡ Fast Inference | Groq's LPU delivers sub-3s responses |
| 🌙 Dark Medical UI | Professional navy-blue glassmorphism design |
| 📱 Responsive | Works on desktop and mobile |

---

## Screenshots

> Dark-blue professional medical UI with animated particle background, collapsible sidebar, and formatted chat responses.

---

## Tech Stack

```
Frontend  →  HTML5 + Vanilla CSS + Vanilla JavaScript
Backend   →  Python 3.10 + Flask + Flask-CORS
LLM       →  Groq API (llama-3.3-70b-versatile)
Vectors   →  Pinecone (serverless)
Embeddings→  sentence-transformers (all-MiniLM-L6-v2)
Retrieval →  Hybrid: Pinecone semantic + BM25 reranking
```

---

## Project Structure

```
medimind-ai/
├── .env                      # API keys (not committed)
├── .gitignore
├── run.py                    # One-click server launcher
├── requirements.txt          # Python dependencies
├── README.md
│
├── data/
│   └── Medical_book.pdf      # Source medical PDF (place here)
│
├── backend/
│   ├── app.py                # Flask REST API server
│   ├── config.py             # Config, Pinecone & embedding init
│   ├── llm.py                # Groq LLM wrapper + system prompt
│   ├── retriever.py          # Hybrid retrieval pipeline
│   └── ingest.py             # PDF → chunks → Pinecone ingestion
│
└── frontend/
    ├── index.html            # App shell
    ├── style.css             # Professional dark-blue medical theme
    └── app.js                # All UI logic & API calls
```

---

## Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/medimind-ai.git
cd medimind-ai
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up environment variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_HOST=https://your-index.svc.pinecone.io
PINECONE_INDEX_NAME=medical-index
```

> Get your keys at: [Groq Console](https://console.groq.com) | [Pinecone Console](https://app.pinecone.io)

### 4. Add your medical PDF

Place your medical reference PDF at:
```
data/Medical_book.pdf
```

### 5. Ingest the PDF into Pinecone

```bash
python backend/ingest.py
```

This will chunk the PDF, generate embeddings, and upload to Pinecone (run once).

### 6. Start the server

```bash
python run.py
```

Open your browser at: **http://localhost:5000**

---

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Serves the frontend UI |
| `/api/health` | GET | Server status + vector count |
| `/api/chat` | POST | Send a query, get AI answer + sources |
| `/api/ingest` | POST | Trigger background PDF re-ingestion |

### Chat Request Example

```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the symptoms of pneumonia?"}'
```

### Chat Response Example

```json
{
  "answer": "Pneumonia is characterized by...",
  "sources": [
    {
      "page": 312,
      "excerpt": "Pneumonia is an inflammation of the lung...",
      "score": 0.876
    }
  ],
  "query": "What are the symptoms of pneumonia?",
  "time_taken": 2.33
}
```

---

## How RAG Works

```
User Question
     │
     ▼
[Embed query] ── all-MiniLM-L6-v2
     │
     ▼
[Pinecone Semantic Search] ── Top-K chunks
     │
     ▼
[BM25 Keyword Reranking] ── Hybrid score (60% semantic + 40% BM25)
     │
     ▼
[Top-4 Chunks] → Context injected into LLM prompt
     │
     ▼
[Groq LLM] ── llama-3.3-70b-versatile
     │
     ▼
Concise, cited medical answer
```

---

## Requirements

```
flask
flask-cors
python-dotenv
groq
pinecone-client
sentence-transformers
rank-bm25
PyMuPDF
```

Install with:
```bash
pip install -r requirements.txt
```

---

## Configuration

All config is in `backend/config.py`:

| Variable | Default | Description |
|---|---|---|
| `EMBEDDING_MODEL_NAME` | `all-MiniLM-L6-v2` | Sentence transformer model |
| `EMBEDDING_DIM` | `384` | Vector dimension |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | LLM model |
| `TOP_K` | `6` | Chunks fetched from Pinecone |
| `CHUNK_SIZE` | `512` | Tokens per chunk |
| `CHUNK_OVERLAP` | `50` | Token overlap between chunks |

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  Built with ❤️ for medical education<br/>
  <em>Not a substitute for professional medical advice. Always consult a qualified healthcare professional.</em>
</p>
