# API Reference

VERA exposes a REST API on port `4000` (default). All document endpoints require authentication when Hub is configured.

## Authentication

### POST /api/auth/login

Authenticate via Hub and create a session cookie.

**Rate limit:** 5 requests/minute.

```bash
curl -X POST http://localhost:4000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "secret"}'
```

**Response** `200 OK`:

```json
{
  "username": "alice",
  "role": "user"
}
```

Sets a `vera_session` HTTP-only cookie (24-hour expiry).

**Errors:**

| Status | Detail |
|---|---|
| `401` | Invalid credentials |
| `503` | Authentication not configured (Hub not connected) |

---

### POST /api/auth/logout

Clear the current session.

```bash
curl -X POST http://localhost:4000/api/auth/logout \
  -b "vera_session=YOUR_SESSION_COOKIE"
```

**Response** `200 OK`:

```json
{"status": "ok"}
```

---

### GET /api/auth/status

Check current authentication state.

```bash
curl http://localhost:4000/api/auth/status \
  -b "vera_session=YOUR_SESSION_COOKIE"
```

**Response** `200 OK` (authenticated):

```json
{
  "authenticated": true,
  "auth_required": true,
  "username": "alice",
  "role": "user"
}
```

**Response** `200 OK` (Hub not configured):

```json
{
  "authenticated": true,
  "auth_required": false
}
```

---

### GET /api/csrf-token

Issue a CSRF token for state-changing requests.

```bash
curl http://localhost:4000/api/csrf-token \
  -b "vera_session=YOUR_SESSION_COOKIE"
```

**Response** `200 OK`:

```json
{"csrf_token": "abc123..."}
```

---

## Documents

### POST /documents/upload

Upload a scanned document (image or PDF) for OCR processing.

**Rate limit:** Configurable via `UPLOAD_RATE_LIMIT` (default `10/minute`).

```bash
curl -X POST http://localhost:4000/documents/upload \
  -F "file=@scan.pdf" \
  -b "vera_session=YOUR_SESSION_COOKIE"
```

**Response** `200 OK`:

```json
{
  "document_id": "a1b2c3d4",
  "image_url": "/files/a1b2c3d4.png",
  "image_width": 0,
  "image_height": 0,
  "status": "uploaded",
  "page_count": 3,
  "pages": [
    {
      "page_id": "e5f6a7b8",
      "page_index": 0,
      "image_url": "/files/e5f6a7b8.png",
      "status": "uploaded",
      "review_complete": false,
      "version": 1
    }
  ],
  "structured_fields": {},
  "review_complete": false
}
```

**Errors:**

| Status | Detail |
|---|---|
| `413` | File exceeds upload size limit |
| `415` | Unsupported file type or MIME type |
| `400` | PDF has no pages / file failed security scan |
| `503` | Background worker or PDF support not available |

---

### GET /documents/{document_id}

Retrieve document metadata, pages, and status.

```bash
curl http://localhost:4000/documents/{document_id} \
  -b "vera_session=YOUR_SESSION_COOKIE"
```

**Response** `200 OK`:

```json
{
  "document_id": "a1b2c3d4",
  "image_url": "/files/a1b2c3d4.png",
  "image_width": 2480,
  "image_height": 3508,
  "status": "ocr_done",
  "page_count": 1,
  "pages": [
    {
      "page_id": "e5f6a7b8",
      "page_index": 0,
      "image_url": "/files/e5f6a7b8.png",
      "image_width": 2480,
      "image_height": 3508,
      "status": "ocr_done",
      "review_complete": false,
      "version": 1
    }
  ],
  "structured_fields": {"vendor": "Acme Corp"},
  "review_complete": false
}
```

---

### GET /documents/{document_id}/pages/{page_id}

Retrieve a single page with all its OCR tokens.

```bash
curl http://localhost:4000/documents/{document_id}/pages/{page_id} \
  -b "vera_session=YOUR_SESSION_COOKIE"
```

**Response** `200 OK`:

```json
{
  "document_id": "a1b2c3d4",
  "page_id": "e5f6a7b8",
  "page_index": 0,
  "image_url": "/files/e5f6a7b8.png",
  "image_width": 2480,
  "image_height": 3508,
  "status": "ocr_done",
  "review_complete": false,
  "version": 1,
  "tokens": [
    {
      "id": "tok_001",
      "line_id": "line_0",
      "line_index": 0,
      "token_index": 0,
      "text": "Invoice",
      "confidence": 0.97,
      "confidence_label": "trusted",
      "forced_review": false,
      "bbox": [100, 50, 250, 80],
      "flags": []
    },
    {
      "id": "tok_002",
      "line_id": "line_0",
      "line_index": 0,
      "token_index": 1,
      "text": "Numb3r",
      "confidence": 0.42,
      "confidence_label": "low",
      "forced_review": true,
      "bbox": [260, 50, 400, 80],
      "flags": ["low_confidence"]
    }
  ]
}
```

---

### POST /documents/{document_id}/validate

Submit corrections and validate a single-page document.

```bash
curl -X POST http://localhost:4000/documents/{document_id}/validate \
  -H "Content-Type: application/json" \
  -d '{
    "corrections": [
      {"token_id": "tok_002", "corrected_text": "Number"}
    ],
    "reviewed_token_ids": ["tok_001", "tok_002"],
    "review_complete": true,
    "structured_fields": {"vendor": "Acme Corp", "total": "142.50"}
  }' \
  -b "vera_session=YOUR_SESSION_COOKIE"
```

**Request body:**

| Field | Type | Description |
|---|---|---|
| `corrections` | `CorrectionSchema[]` | List of `{token_id, corrected_text}` pairs |
| `reviewed_token_ids` | `string[]` | IDs of all tokens the reviewer has seen |
| `review_complete` | `bool` | Set `true` to finalize validation |
| `structured_fields` | `object \| null` | Updated structured key-value pairs |

**Response** `200 OK`:

```json
{
  "validated_text": "Invoice Number: 12345\nVendor: Acme Corp\nTotal: $142.50",
  "validation_status": "validated",
  "validated_at": "2026-03-17T10:30:00",
  "structured_fields": {"vendor": "Acme Corp", "total": "142.50"}
}
```

**Errors:**

| Status | Detail |
|---|---|
| `404` | Document not found |
| `409` | Review incomplete (forced-review tokens not reviewed) |

---

### POST /documents/{document_id}/pages/{page_id}/validate

Validate a single page within a multi-page document.

```bash
curl -X POST http://localhost:4000/documents/{doc_id}/pages/{page_id}/validate \
  -H "Content-Type: application/json" \
  -d '{
    "corrections": [],
    "reviewed_token_ids": ["tok_001"],
    "review_complete": true,
    "structured_fields": null,
    "page_version": 1
  }' \
  -b "vera_session=YOUR_SESSION_COOKIE"
```

Accepts the same body as document-level validation, plus:

| Field | Type | Description |
|---|---|---|
| `page_version` | `int` | Required. Must match current page version for optimistic concurrency |

**Errors:**

| Status | Detail |
|---|---|
| `400` | Page version is required |
| `404` | Document or page not found |
| `409` | Review incomplete or version conflict |

---

### GET /documents/{document_id}/export

Export a validated document.

```bash
# JSON (default)
curl "http://localhost:4000/documents/{id}/export"

# CSV
curl "http://localhost:4000/documents/{id}/export?format=csv"

# Plain text
curl "http://localhost:4000/documents/{id}/export?format=txt"
```

**Query parameters:**

| Parameter | Default | Options |
|---|---|---|
| `format` | `json` | `json`, `csv`, `txt` |

**Response** `200 OK` (JSON):

```json
{
  "document_id": "a1b2c3d4",
  "validated_text": "Invoice Number: 12345\nVendor: Acme Corp",
  "structured_fields": {"vendor": "Acme Corp", "total": "142.50"}
}
```

**Errors:**

| Status | Detail |
|---|---|
| `404` | Document not found |
| `409` | Document not validated |

!!! note "Page-level export"
    Use `GET /documents/{doc_id}/pages/{page_id}/export?format=json` to export individual pages.

---

### GET /documents/{document_id}/summary

Generate an AI summary of a validated document via Ollama.

```bash
curl "http://localhost:4000/documents/{id}/summary" \
  -b "vera_session=YOUR_SESSION_COOKIE"

# Override model
curl "http://localhost:4000/documents/{id}/summary?model=llama3.2:3b"
```

**Query parameters:**

| Parameter | Default | Description |
|---|---|---|
| `model` | _(from config)_ | Override the Ollama model |

**Response** `200 OK`:

```json
{
  "bullet_summary": [
    "Invoice from Acme Corp dated 2026-03-15",
    "Total amount due: $142.50",
    "Payment terms: Net 30"
  ],
  "structured_fields": {"vendor": "Acme Corp", "total": "142.50", "date": "2026-03-15"},
  "validation_status": "summarized"
}
```

**Errors:**

| Status | Detail |
|---|---|
| `404` | Document not found |
| `409` | Document not validated |

!!! note "Page-level summary"
    Use `GET /documents/{doc_id}/pages/{page_id}/summary` for per-page summaries.

---

### POST /documents/{document_id}/fields

Update structured fields for a document.

```bash
curl -X POST http://localhost:4000/documents/{id}/fields \
  -H "Content-Type: application/json" \
  -d '{"structured_fields": {"vendor": "Acme Corp", "total": "142.50"}}' \
  -b "vera_session=YOUR_SESSION_COOKIE"
```

**Response** `200 OK`:

```json
{"structured_fields": {"vendor": "Acme Corp", "total": "142.50"}}
```

---

### POST /documents/{document_id}/cancel

Cancel a document that is in `uploaded` or `processing` status.

```bash
curl -X POST http://localhost:4000/documents/{id}/cancel \
  -b "vera_session=YOUR_SESSION_COOKIE"
```

**Response** `200 OK`:

```json
{"status": "canceled"}
```

**Errors:**

| Status | Detail |
|---|---|
| `404` | Document not found |
| `409` | Document is not processing / no active task |

---

### GET /documents/{document_id}/audit

Retrieve the audit trail for a document.

```bash
curl http://localhost:4000/documents/{id}/audit \
  -b "vera_session=YOUR_SESSION_COOKIE"
```

**Response** `200 OK`:

```json
{
  "audit_log": [
    {
      "id": "log_001",
      "event_type": "exported",
      "actor": "local_user",
      "detail": {"format": "json"},
      "created_at": "2026-03-17T10:45:00"
    }
  ]
}
```

---

## Status & Monitoring

### GET /documents/{document_id}/pages/status

Get status summary for all pages in a document.

```bash
curl http://localhost:4000/documents/{document_id}/pages/status \
  -b "vera_session=YOUR_SESSION_COOKIE"
```

**Response** `200 OK`:

```json
{
  "document_id": "a1b2c3d4",
  "status": "ocr_done",
  "review_complete": false,
  "pages": [
    {
      "page_id": "e5f6a7b8",
      "page_index": 0,
      "status": "ocr_done",
      "review_complete": false,
      "token_count": 142,
      "forced_review_count": 5,
      "updated_at": "2026-03-17T10:00:00",
      "version": 1
    }
  ]
}
```

---

### GET /documents/{document_id}/status/stream

Server-Sent Events stream for real-time status updates.

```bash
curl -N http://localhost:4000/documents/{document_id}/status/stream \
  -b "vera_session=YOUR_SESSION_COOKIE"
```

!!! note "Cross-origin SSE"
    The `EventSource` browser API does not support custom headers. When the frontend runs on a different origin from the backend, authentication relies on cookies sent with `withCredentials: true`. Ensure `CORS_ORIGINS` includes the frontend origin.

**Query parameters:**

| Parameter | Default | Description |
|---|---|---|
| `interval` | `2.0` | Polling interval in seconds (minimum `0.5`) |

---

### GET /health

Health check endpoint. Returns `200` if the backend and database are operational.

```bash
curl http://localhost:4000/health
```

**Response** `200 OK`:

```json
{"status": "ok"}
```

!!! tip "No authentication required"
    The `/health` and `/metrics` endpoints do not require a session cookie.

---

### GET /metrics

Prometheus metrics endpoint. Returns request count and latency metrics.

```bash
curl http://localhost:4000/metrics
```

Returns `text/plain` in Prometheus exposition format.

---

## LLM Management

### GET /llm/models

List available models from the connected Ollama instance.

### GET /llm/health

Check Ollama connectivity and list available models.

### POST /llm/models/pull

Pull a model from the Ollama registry.

```bash
curl -X POST http://localhost:4000/llm/models/pull \
  -H "Content-Type: application/json" \
  -d '{"model": "llama3.2:3b"}' \
  -b "vera_session=YOUR_SESSION_COOKIE"
```

### POST /llm/models/pull/stream

Pull a model with streaming progress (NDJSON).
