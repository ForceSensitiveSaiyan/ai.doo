# VERA Overview

VERA is a verification-first OCR platform. Upload scanned documents, let PaddleOCR extract text, then review, correct, and validate the results before exporting. AI summaries via Ollama are available after validation.

## How It Works

1. **Upload** a scanned image or multi-page PDF.
2. **OCR** runs automatically in a background Celery worker (PaddleOCR).
3. **Review** the extracted tokens in the web UI. Low-confidence and flagged tokens are highlighted for attention.
4. **Correct** any misread tokens and fill in structured fields.
5. **Validate** the page or document. Validation is a hard gate -- nothing proceeds without explicit human approval.
6. **Summarize** (optional) using a local LLM via Ollama.
7. **Export** the validated text as JSON, CSV, or plain text.

## Key Features

| Feature | Description |
|---|---|
| Multi-page PDF support | PDFs are split into individual pages; each page is reviewed independently |
| Token-level confidence | Every OCR token has a confidence score and label (`trusted`, `medium`, `low`) |
| Forced review | Tokens flagged for mandatory human review before validation can proceed |
| AI summaries | Bullet-point summaries and structured field extraction via Ollama (post-validation) |
| Structured fields | Key-value pairs (vendor, date, total, etc.) extracted automatically and editable by reviewers |
| Audit trail | Every action (upload, correction, validation, export) is logged with actor and timestamp |
| Export formats | JSON, CSV, and plain text |
| Document type detection | Automatic classification (invoice, receipt, statement) based on content keywords |
| Rate limiting | Configurable upload rate limits via SlowAPI |
| Prometheus metrics | Request count and latency metrics at `/metrics` |

## Architecture

VERA runs as five Docker services plus an optional backup sidecar:

```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐
│  Frontend   │────▶│  Backend    │────▶│  PostgreSQL  │
│  Next.js    │     │  FastAPI    │     │  :5432       │
│  :3000      │     │  :4000      │     └──────────────┘
└─────────────┘     └──────┬──────┘
                           │
                    ┌──────▼──────┐     ┌──────────────┐
                    │   Redis     │◀────│   Worker     │
                    │   :6379     │     │   Celery     │
                    └─────────────┘     └──────┬───────┘
                                               │
                                        ┌──────▼───────┐
                                        │   Ollama     │
                                        │ (external)   │
                                        │  :11434      │
                                        └──────────────┘
```

| Service | Image / Framework | Role |
|---|---|---|
| **frontend** | Next.js | Web UI for document review |
| **backend** | FastAPI | REST API, serves files, orchestrates tasks |
| **worker** | Celery | Runs PaddleOCR and AI summary tasks in the background |
| **postgres** | PostgreSQL 16 | Primary database (documents, tokens, corrections, audit log) |
| **redis** | Redis 7 | Celery broker and result backend |
| **backup** | PostgreSQL 16 (sidecar) | Automated daily database backups |

Ollama runs externally in the shared `ollama_network` Docker network. VERA connects to it for AI summaries but degrades gracefully if Ollama is unavailable.

## Document Lifecycle

Every document passes through a strict status progression:

```
uploaded → processing → ocr_done → review_in_progress → validated → summarized → exported
                │                                                        ▲
                └──► failed                                              │
                └──► canceled                              (optional, skippable)
```

| Status | Meaning |
|---|---|
| `uploaded` | File received, queued for OCR |
| `processing` | Celery worker is running PaddleOCR |
| `ocr_done` | OCR complete, tokens stored, ready for review |
| `review_in_progress` | Reviewer has started correcting tokens |
| `validated` | All tokens reviewed, corrections applied, human-approved |
| `summarized` | AI summary generated via Ollama |
| `exported` | Document data exported (JSON/CSV/TXT) |
| `failed` | OCR processing failed |
| `canceled` | Processing canceled by user |

!!! warning "Validation is a hard gate"
    Summaries and exports are only available after a document (or all its pages) has been explicitly validated. There is no way to skip the review step.

## Authentication

VERA delegates authentication to **Hub** (the central ai.doo user management service). When Hub is configured (`HUB_BASE_URL` and `HUB_AUTH_API_KEY`), all document endpoints require a valid session. When Hub is not configured, VERA runs in open mode with no authentication.

## Data Model

VERA stores five core tables in PostgreSQL:

| Table | Purpose |
|---|---|
| `documents` | Top-level document metadata and status |
| `document_pages` | Individual pages within multi-page documents |
| `tokens` | OCR-extracted tokens with confidence, bounding box, and flags |
| `corrections` | Human corrections linking original to corrected text |
| `audit_logs` | Immutable event log for every document action |
