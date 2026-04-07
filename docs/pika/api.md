# PIKA API Reference

All API endpoints are served under the `/api/v1` prefix unless otherwise noted. Authentication is via session cookie (web UI) or `X-API-Key` header (programmatic access).

!!! note "Session architecture"
    PIKA uses stateless signed cookies (no server-side session store). Sessions expire after the configured `SESSION_MAX_AGE` (default 24 hours). If a user is disabled in Hub, PIKA checks user status periodically (every 5 minutes) and will reject requests from disabled users on the next check cycle. For immediate revocation, restart the PIKA service.

## Health and Status

### `GET /api/v1/health`

Full health check of PIKA and its dependencies.

**Authentication:** None required

**Response:**

```json
{
  "status": "healthy",
  "version": "1.3.1",
  "ollama": {
    "connected": true,
    "current_model": "llama3.2:3b",
    "model_loaded": true,
    "error": null
  },
  "index": {
    "document_count": 12,
    "chunk_count": 347
  },
  "disk": {
    "data_dir": "./data",
    "free_bytes": 53687091200,
    "free_gb": 50.0,
    "warning": false
  }
}
```

| Status | Meaning |
|---|---|
| `healthy` | Ollama connected, model loaded, disk OK |
| `degraded` | Ollama connected but model not loaded, or disk space low (< 1 GB) |
| `unhealthy` | Ollama unreachable |

---

### `GET /api/v1/status/quick`

Lightweight status for UI polling (optimised for frequent calls).

**Response:**

```json
{
  "status": "healthy",
  "ollama_connected": true,
  "circuit_breaker_open": false,
  "index_chunks": 347,
  "indexing_in_progress": false
}
```

---

### `GET /metrics`

Prometheus metrics endpoint. Returns metrics in Prometheus text format.

**Key metrics:**

| Metric | Type | Description |
|---|---|---|
| `pika_http_requests_total` | Counter | Total HTTP requests by method, endpoint, status |
| `pika_http_request_duration_seconds` | Histogram | Request latency |
| `pika_queries_total` | Counter | Total RAG queries by status and confidence |
| `pika_query_duration_seconds` | Histogram | Query processing time |
| `pika_active_queries` | Gauge | Queries currently processing |
| `pika_queued_queries` | Gauge | Queries waiting in queue |
| `pika_index_documents_total` | Gauge | Documents in index |
| `pika_index_chunks_total` | Gauge | Chunks in index |
| `pika_ollama_healthy` | Gauge | Ollama connectivity (1/0) |
| `pika_circuit_breaker_state` | Gauge | 0=closed, 1=half_open, 2=open |
| `pika_query_cache_hits_total` | Counter | Cache hits |
| `pika_query_cache_misses_total` | Counter | Cache misses |

---

## Queries

### `POST /api/v1/query`

Start an asynchronous RAG query. The query is placed in a FIFO queue and processed in the background.

**Authentication:** Required (admin, user, or API key)

**Request:**

```json
{
  "question": "What is the refund policy?",
  "top_k": 5
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `question` | string | Yes | The question to ask (1 -- 10,000 chars) |
| `top_k` | integer | No | Number of chunks to retrieve (1 -- 50, default from settings) |

**Response (202):**

```json
{
  "query_id": "a1b2c3d4",
  "status": "queued",
  "queue_position": 1,
  "queue_length": 3,
  "estimated_wait_seconds": 15
}
```

**Error responses:**

| Status | Condition |
|---|---|
| `429` | User queue limit reached (`MAX_QUEUED_PER_USER`) |
| `503` | Global queue full (`MAX_QUEUE_SIZE`) |

---

### `GET /api/v1/query/status`

Poll for the result of the current user's most recent query.

**Response:**

```json
{
  "query_id": "a1b2c3d4",
  "question": "What is the refund policy?",
  "status": "completed",
  "result": {
    "answer": "According to the company handbook, refunds are available within 30 days...",
    "sources": [
      {
        "filename": "handbook.pdf",
        "chunk_index": 12,
        "content": "Refund requests must be submitted within 30 calendar days...",
        "similarity": 0.82
      }
    ],
    "confidence": "high"
  },
  "error": null,
  "queue_position": null,
  "queue_length": null,
  "estimated_wait_seconds": null
}
```

| Status value | Meaning |
|---|---|
| `pending` | Query accepted, not yet queued |
| `queued` | Waiting in the queue |
| `running` | Currently being processed |
| `completed` | Result ready in `result` field |
| `error` | Failed — see `error` field |
| `cancelled` | Cancelled by user |
| `none` | No active query |

---

### `POST /api/v1/query/stream`

Stream a query response via Server-Sent Events (SSE). Returns results in real time rather than requiring polling.

**Request:** Same as `POST /api/v1/query`

**SSE event types:**

| Event | Data | Description |
|---|---|---|
| `metadata` | `{"type": "metadata", "sources": [...], "confidence": "high"}` | Sources and confidence (sent first) |
| `token` | `{"type": "token", "content": "The"}` | A single response token |
| `done` | `{"type": "done", "answer": "..."}` | Full answer (final event) |
| `error` | `{"type": "error", "message": "..."}` | Error occurred |

**Example:**

```bash
curl -N -X POST http://localhost:8000/api/v1/query/stream \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the refund policy?"}'
```

---

### `POST /api/v1/query/cancel`

Cancel the current user's running or queued query.

**Response:**

```json
{
  "cancelled": true,
  "message": "Query cancelled successfully"
}
```

---

### `DELETE /api/v1/query/status`

Clear the current user's query status (useful after reading a completed result).

---

## Documents

### `POST /upload`

Upload a document file. The file is saved to the documents directory but is **not** automatically indexed.

!!! note
    This endpoint is at `/upload` (no `/api/v1` prefix).

**Authentication:** Required (admin or API key)

**Request:** Multipart form upload

```bash
curl -X POST http://localhost:8000/upload \
  -H "X-API-Key: your-api-key" \
  -F "file=@report.pdf"
```

**Response:**

```json
{
  "status": "uploaded",
  "filename": "report.pdf"
}
```

| Status | Condition |
|---|---|
| `400` | Missing filename, invalid extension, or path traversal attempt |
| `413` | File exceeds `MAX_UPLOAD_SIZE_MB` |

---

### `GET /documents`

List all documents in the documents directory with file metadata.

**Response:**

```json
[
  {
    "filename": "report.pdf",
    "path": "./documents/report.pdf",
    "size_bytes": 245760,
    "modified_at": "2025-03-15T10:30:00",
    "file_type": "pdf"
  }
]
```

---

### `GET /api/v1/documents`

List indexed documents with their chunk counts.

**Response:**

```json
[
  {
    "filename": "report.pdf",
    "chunk_count": 42
  }
]
```

---

### `DELETE /documents/{filename}`

Delete a document from the file system.

!!! note
    This endpoint is at `/documents/{filename}` (no `/api/v1` prefix). Reindex after deletion to remove stale chunks from the vector store.

**Response:**

```json
{
  "status": "deleted",
  "filename": "report.pdf"
}
```

---

## Indexing

### `POST /api/v1/index`

Synchronous reindex of all documents. Blocks until complete.

**Authentication:** Required (admin or API key)

**Response:**

```json
{
  "status": "indexed",
  "total_documents": 12,
  "total_chunks": 347
}
```

---

### `POST /api/v1/index/start`

Start asynchronous background indexing with progress reporting.

**Response (202):**

```json
{
  "index_id": "idx-abc123",
  "status": "started",
  "message": "Indexing started"
}
```

---

### `GET /api/v1/index/status`

Poll indexing progress.

**Response:**

```json
{
  "active": true,
  "index_id": "idx-abc123",
  "status": "running",
  "total_documents": 12,
  "processed_documents": 5,
  "current_file": "handbook.pdf",
  "percent": 42,
  "total_chunks": 150,
  "error": null,
  "completed_at": null
}
```

---

### `POST /api/v1/index/cancel`

Cancel an active indexing operation.

---

### `GET /api/v1/index/stats`

Get index statistics (admin only).

**Response:**

```json
{
  "total_documents": 12,
  "total_chunks": 347,
  "collection_name": "pika_documents"
}
```

---

### `GET /api/v1/index/info`

Combined index stats and document list in a single call (optimised).

---

## Models

### `GET /api/v1/models`

List available Ollama models.

**Response:**

```json
[
  {
    "name": "llama3.2:3b",
    "size": "2.0 GB",
    "size_bytes": 2147483648,
    "is_current": true
  }
]
```

---

### `POST /api/v1/models/current`

Switch the active model (admin or API key required).

**Request:**

```json
{
  "model": "llama3.1:8b"
}
```

---

### `POST /api/v1/models/pull`

Pull a new model from the Ollama registry (admin or API key required). Returns `202 Accepted`.

**Request:**

```json
{
  "model": "llama3.1:8b"
}
```

**Poll progress:** `GET /api/v1/models/pull/status`

---

## History and Feedback

### `GET /api/v1/history`

Get the current user's recent query history.

**Query parameters:**

| Parameter | Default | Description |
|---|---|---|
| `limit` | `20` | Number of history entries to return |

**Response:**

```json
[
  {
    "id": "abc123",
    "question": "What is the refund policy?",
    "answer": "According to the handbook...",
    "confidence": "high",
    "sources": ["handbook.pdf"],
    "timestamp": "2025-03-15T10:30:00"
  }
]
```

---

### `DELETE /api/v1/history`

Clear the current user's query history.

---

### `POST /api/v1/feedback`

Submit feedback on a query answer.

**Request:**

```json
{
  "query_id": "abc12345",
  "question": "What is the refund policy?",
  "answer": "According to the handbook...",
  "rating": "up"
}
```

| Field | Type | Values |
|---|---|---|
| `rating` | string | `"up"` or `"down"` |

**Response:**

```json
{
  "status": "received",
  "rating": "up"
}
```

---

## Rate Limits

All rate limits are configurable via environment variables.

| Endpoint group | Default limit | Config variable |
|---|---|---|
| Auth (`/admin/login`) | 5/minute | `RATE_LIMIT_AUTH` |
| Queries (`/api/v1/query`) | 30/minute | `RATE_LIMIT_QUERY` |
| Admin ops (backup/restore) | 10/minute | `RATE_LIMIT_ADMIN` |

Rate-limited responses return `429 Too Many Requests` with a `retry_after` field.
