# PIKA Overview

**PIKA** (Private Intelligent Knowledge Assistant) is a self-hosted document Q&A system powered by Retrieval-Augmented Generation (RAG). Upload PDFs, DOCX files, or plain text, then ask questions and get answers grounded in your documents — all running locally via Ollama.

## Key Features

| Feature | Description |
|---|---|
| **RAG pipeline** | Documents are chunked, embedded with Sentence Transformers, stored in ChromaDB, and retrieved at query time to ground LLM responses |
| **Multi-user auth** | Role-based access (admin/user) with session management, CSRF protection, and rate limiting. Auth delegated to Hub for centralised identity |
| **Circuit breaker** | Graceful degradation when Ollama is unavailable — queries fail fast instead of hanging |
| **Streaming responses** | Answers stream token-by-token via Server-Sent Events for a responsive UI |
| **Query queue** | FIFO queue with per-user fairness and configurable concurrency limits |
| **Query cache** | Repeated questions are served from cache (configurable TTL) |
| **Backup / restore** | Full-system ZIP export of documents, vector store, and configuration with configurable retention |
| **Prometheus metrics** | Built-in `/metrics` endpoint for monitoring query latency, queue depth, circuit breaker state, and more |

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                     PIKA :8000                      │
│                                                     │
│  ┌──────────┐   ┌───────────┐   ┌───────────────┐  │
│  │ Jinja2   │   │ FastAPI   │   │ Prometheus    │  │
│  │ Web UI   │──▶│ API       │   │ /metrics      │  │
│  └──────────┘   └─────┬─────┘   └───────────────┘  │
│                       │                             │
│            ┌──────────▼──────────┐                  │
│            │    RAG Engine       │                  │
│            │  chunk → embed →    │                  │
│            │  retrieve → prompt  │                  │
│            └───┬────────────┬───┘                  │
│                │            │                       │
│  ┌─────────────▼──┐  ┌─────▼──────────┐            │
│  │ ChromaDB       │  │ Sentence       │            │
│  │ (vector store) │  │ Transformers   │            │
│  │ SQLite-backed  │  │ all-MiniLM-L6  │            │
│  └────────────────┘  └────────────────┘            │
│                                                     │
└──────────────────────┬──────────────────────────────┘
                       │ http://ollama:11434
              ┌────────▼────────┐
              │  Ollama         │
              │  (shared)       │
              └────────┬────────┘
                       │
              ┌────────▼────────┐
              │  Hub            │
              │  (auth, license)│
              └─────────────────┘
```

## Document Lifecycle

```
Upload (.pdf / .docx / .txt / .md)
  │
  ▼
Validate (extension, size ≤ 50 MB)
  │
  ▼
Store in documents/ directory
  │
  ▼
Index  ─── Extract text ──▶ Chunk (500 tokens, 50 overlap)
  │                              │
  │                              ▼
  │                        Embed (all-MiniLM-L6-v2)
  │                              │
  │                              ▼
  │                        Store vectors in ChromaDB
  │
  ▼
Ready for queries
  │
  ▼
Query ── Embed question ──▶ Retrieve top-K chunks
  │                              │
  │                              ▼
  │                        Build prompt with context
  │                              │
  │                              ▼
  │                        Send to Ollama (streamed)
  │                              │
  │                              ▼
  │                        Return answer + sources + confidence
  ▼
Feedback (thumbs up / down) stored for quality tracking
```

## Confidence Scoring

Each answer includes a confidence level based on the similarity of retrieved chunks:

| Level | Threshold | Meaning |
|---|---|---|
| **high** | >= 0.7 | Strong match — answer is well-supported by documents |
| **medium** | >= 0.5 | Moderate match — answer may be partially supported |
| **low** | >= 0.3 | Weak match — answer has limited document support |
| **none** | < 0.3 | No relevant documents found |

!!! tip "Improving confidence"
    Upload more relevant documents and experiment with `CHUNK_SIZE` and `TOP_K` settings to improve retrieval quality for your use case.

## Tech Stack

| Component | Technology |
|---|---|
| API framework | FastAPI (Python 3.11+) |
| Vector store | ChromaDB (SQLite-backed, persistent) |
| Embeddings | Sentence Transformers (`all-MiniLM-L6-v2`) |
| LLM inference | Ollama (local, shared service) |
| Web UI | Jinja2 templates + vanilla JS |
| Auth | Hub-delegated (centralised identity) |
| Metrics | Prometheus client |
| Rate limiting | SlowAPI |
