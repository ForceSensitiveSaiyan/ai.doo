# Using PIKA

## Uploading Documents

PIKA accepts **PDF**, **DOCX**, **TXT**, and **Markdown** files up to 50 MB each (configurable via `MAX_UPLOAD_SIZE_MB`).

### Via the Web UI

1. Log in and navigate to the **Admin** panel.
2. Use the upload form to select one or more files.
3. After upload, click **Reindex** to process the new documents into the vector store.

### Via the API

```bash
curl -X POST http://localhost:8000/upload \
  -H "X-API-Key: your-api-key" \
  -F "file=@report.pdf"
```

!!! note "Indexing is a separate step"
    Uploading a document stores the file but does not automatically add it to the search index. Trigger indexing via the admin panel or the `/api/v1/index/start` endpoint.

### Supported Formats

| Format | Extension | Notes |
|---|---|---|
| PDF | `.pdf` | Text extracted via pypdf. Scanned/image-only PDFs will yield no text |
| Word | `.docx` | Paragraph text extracted via python-docx |
| Plain text | `.txt` | Read as UTF-8 |
| Markdown | `.md` | Read as UTF-8 (rendered as plain text for chunking) |

## Asking Questions

### Via the Web UI

1. Open PIKA at `http://localhost:8000`.
2. Type your question in the chat input.
3. PIKA retrieves relevant document chunks, sends them to Ollama as context, and streams the answer back.
4. Each answer shows:
    - The response text (streamed token-by-token)
    - **Sources** — the document chunks used, with similarity scores
    - **Confidence** level (high / medium / low / none)

### Via the API

Submit a query and poll for results:

```bash
# Start a query
curl -X POST http://localhost:8000/api/v1/query \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the refund policy?"}'

# Poll for status
curl http://localhost:8000/api/v1/query/status \
  -H "X-API-Key: your-api-key"
```

Or use the streaming endpoint for real-time token delivery:

```bash
curl -N http://localhost:8000/api/v1/query/stream \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the refund policy?"}'
```

!!! tip "Adjusting retrieval"
    Pass `"top_k": 10` in your query to retrieve more context chunks. Higher values may improve answer quality for broad questions but increase latency.

## Feedback

After receiving an answer, you can submit feedback to help track answer quality:

- **Web UI:** Click the thumbs-up or thumbs-down button next to any answer.
- **API:** `POST /api/v1/feedback` with a rating of `"up"` or `"down"`.

```bash
curl -X POST http://localhost:8000/api/v1/feedback \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "query_id": "abc12345",
    "question": "What is the refund policy?",
    "answer": "The refund policy states...",
    "rating": "up"
  }'
```

Feedback is stored locally and visible in the admin audit log.

## Document Management

### Listing Documents

View all uploaded documents and their indexing status:

- **Web UI:** Admin panel shows documents with chunk counts.
- **API:** `GET /documents` returns file metadata; `GET /api/v1/documents` returns indexed documents with chunk counts.

### Deleting Documents

Remove a document from the file system:

```bash
curl -X DELETE http://localhost:8000/documents/report.pdf \
  -H "X-API-Key: your-api-key"
```

!!! warning "Reindex after deletion"
    Deleting a file removes it from disk but does not automatically remove its chunks from the vector store. Reindex to clean up stale entries.

### Reindexing

Trigger a full reindex of all documents in the `documents/` directory:

- **Synchronous:** `POST /api/v1/index` (blocks until complete)
- **Asynchronous:** `POST /api/v1/index/start` (returns immediately, poll `/api/v1/index/status`)

## Backup and Restore

### Creating a Backup

1. In the admin panel, click **Create Backup**.
2. PIKA creates a ZIP archive containing documents, vector store data, and configuration.
3. Download the backup when ready.

Via API:

```bash
# Start backup
curl -X POST http://localhost:8000/admin/backup/start \
  -H "X-API-Key: your-api-key"

# Check status
curl http://localhost:8000/admin/backup/status \
  -H "X-API-Key: your-api-key"

# Download
curl -O http://localhost:8000/admin/backup/download \
  -H "X-API-Key: your-api-key"
```

### Restoring from Backup

Upload a backup ZIP to restore all PIKA data:

```bash
curl -X POST http://localhost:8000/admin/restore \
  -H "X-API-Key: your-api-key" \
  -F "file=@pika-backup.zip"
```

!!! warning "Restore overwrites data"
    Restoring replaces all current documents, vector store data, and configuration. Create a backup of your current state first.

## API Key Authentication

For programmatic access, set the `PIKA_API_KEY` environment variable and include it in requests:

```bash
# As a header (recommended)
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/v1/health

# Or as a query parameter
curl "http://localhost:8000/api/v1/health?api_key=your-api-key"
```

Endpoints that require authentication return `401 Unauthorized` if no valid session or API key is provided. Admin-only endpoints (backup, restore, model management) additionally require admin-level access.

## Query History

PIKA stores per-user query history (up to 50 entries by default):

```bash
# Get recent history
curl http://localhost:8000/api/v1/history \
  -H "X-API-Key: your-api-key"

# Clear history
curl -X DELETE http://localhost:8000/api/v1/history \
  -H "X-API-Key: your-api-key"
```
