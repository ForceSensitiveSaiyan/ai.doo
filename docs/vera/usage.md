# Usage Guide

This guide covers the day-to-day workflow for using VERA to process scanned documents.

## Uploading Documents

VERA accepts single images and multi-page PDFs.

**Supported formats:**

- Images: JPEG, PNG
- Documents: PDF (multi-page supported)

**Size limit:** Configurable via `MAX_UPLOAD_MB` (default 25 MB).

To upload, click the upload button in the web UI or use the API directly:

```bash
curl -X POST http://localhost:4000/documents/upload \
  -F "file=@invoice.pdf" \
  -b "vera_session=YOUR_SESSION_COOKIE"
```

After upload, VERA immediately queues the document for OCR processing. Multi-page PDFs are automatically split into individual pages, each processed independently.

!!! info "Processing time"
    OCR processing runs in a background Celery worker. Processing time depends on document complexity and page count. You can monitor progress via the status stream endpoint or the web UI.

## Reviewing OCR Results

Once processing completes (status `ocr_done`), the document is ready for review.

### Token Display

Each page shows its extracted tokens with visual indicators:

| Confidence Label | Meaning | Action Required |
|---|---|---|
| `trusted` | High confidence (OCR is very sure) | Review optional |
| `medium` | Moderate confidence | Review recommended |
| `low` | Low confidence (likely misread) | Review required |

Tokens with `forced_review: true` must be explicitly reviewed before the page can be validated.

### Correcting Tokens

To correct a misread token:

1. Click on the token in the review UI.
2. Edit the text to the correct value.
3. The correction is tracked as a diff (original text vs. corrected text).

All corrections are saved to the `corrections` table and recorded in the audit log.

### Bounding Boxes

Each token includes a bounding box (`bbox`) with coordinates `[x_min, y_min, x_max, y_max]` relative to the page image. The UI overlays these on the scanned image so you can see exactly where each token was detected.

## Structured Fields

VERA automatically extracts structured key-value pairs from document text based on document type (invoice, receipt, statement). Common fields include:

- **Vendor** / company name
- **Date**
- **Total** / amount due
- **Subtotal**

You can manually edit structured fields during review or update them via the API:

```bash
curl -X POST http://localhost:4000/documents/{id}/fields \
  -H "Content-Type: application/json" \
  -d '{"structured_fields": {"vendor": "Acme Corp", "total": "142.50"}}' \
  -b "vera_session=YOUR_SESSION_COOKIE"
```

## Validating Documents

Validation is the core gate in VERA's workflow. A document (or page) cannot be summarized or exported until it is validated.

### Single-Page Documents

Submit corrections and mark the review as complete:

```bash
curl -X POST http://localhost:4000/documents/{id}/validate \
  -H "Content-Type: application/json" \
  -d '{
    "corrections": [
      {"token_id": "abc123", "corrected_text": "Invoice"}
    ],
    "reviewed_token_ids": ["abc123", "def456"],
    "review_complete": true,
    "structured_fields": {"vendor": "Acme Corp"}
  }' \
  -b "vera_session=YOUR_SESSION_COOKIE"
```

### Multi-Page Documents

For multi-page PDFs, validate each page individually:

```bash
curl -X POST http://localhost:4000/documents/{doc_id}/pages/{page_id}/validate \
  -H "Content-Type: application/json" \
  -d '{
    "corrections": [],
    "reviewed_token_ids": ["tok1", "tok2"],
    "review_complete": true,
    "page_version": 1
  }' \
  -b "vera_session=YOUR_SESSION_COOKIE"
```

!!! warning "Page versioning"
    Multi-page validation requires a `page_version` field to prevent conflicts when multiple reviewers work on the same document. If the version does not match, the API returns `409 Conflict`.

The parent document transitions to `validated` only when **all** pages are validated.

## Generating Summaries

After validation, request an AI-generated summary via Ollama:

```bash
# Document-level summary
curl http://localhost:4000/documents/{id}/summary \
  -b "vera_session=YOUR_SESSION_COOKIE"

# Page-level summary
curl http://localhost:4000/documents/{doc_id}/pages/{page_id}/summary \
  -b "vera_session=YOUR_SESSION_COOKIE"
```

You can override the default model with a query parameter:

```bash
curl "http://localhost:4000/documents/{id}/summary?model=llama3.2:3b" \
  -b "vera_session=YOUR_SESSION_COOKIE"
```

The response includes:

- `bullet_summary` -- a list of bullet-point strings
- `structured_fields` -- AI-extracted key-value pairs
- `validation_status` -- updated document status

!!! note "Ollama required"
    Summaries require a running Ollama instance with the configured model pulled. If Ollama is unavailable, the endpoint returns `503`.

## Exporting

Export validated documents in three formats:

| Format | Content-Type | Description |
|---|---|---|
| `json` | `application/json` | Full payload with document ID, validated text, and structured fields |
| `csv` | `text/csv` | Key-value rows: document_id, validated_text, plus each structured field |
| `txt` | `text/plain` | Raw validated text only |

```bash
# JSON (default)
curl "http://localhost:4000/documents/{id}/export" \
  -b "vera_session=YOUR_SESSION_COOKIE"

# CSV
curl "http://localhost:4000/documents/{id}/export?format=csv" \
  -b "vera_session=YOUR_SESSION_COOKIE"

# Plain text
curl "http://localhost:4000/documents/{id}/export?format=txt" \
  -b "vera_session=YOUR_SESSION_COOKIE"
```

Page-level export is also available for multi-page documents:

```bash
curl "http://localhost:4000/documents/{doc_id}/pages/{page_id}/export?format=json" \
  -b "vera_session=YOUR_SESSION_COOKIE"
```

!!! info "Export marks the document"
    Exporting transitions the document status to `exported`. This is recorded in the audit log.

## Multi-Page Workflow Summary

For a multi-page PDF, the typical workflow is:

1. **Upload** the PDF. VERA splits it into individual pages.
2. **Monitor** processing via the status stream or polling endpoint.
3. **Review** each page independently -- correct tokens, fill structured fields.
4. **Validate** each page (with `page_version` for conflict detection).
5. Once all pages are validated, the parent document status becomes `validated`.
6. **Summarize** at the document or page level.
7. **Export** the full document or individual pages.

## Canceling Processing

If a document is stuck in `uploaded` or `processing` status, you can cancel it:

```bash
curl -X POST http://localhost:4000/documents/{id}/cancel \
  -b "vera_session=YOUR_SESSION_COOKIE"
```

This revokes the Celery task and sets the document status to `canceled`.

## Audit Trail

Every document has a complete audit log accessible via:

```bash
curl http://localhost:4000/documents/{id}/audit \
  -b "vera_session=YOUR_SESSION_COOKIE"
```

Events include: `ocr_completed`, `ocr_canceled`, `fields_updated`, `validated`, `exported`, and more. Each entry records the event type, actor, detail payload, and timestamp.
