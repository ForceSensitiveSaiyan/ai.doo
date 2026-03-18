# PIKA Configuration

PIKA is configured via environment variables, loaded through [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/). Variables can be set in a `.env` file, as system environment variables, or via Docker secrets.

## Environment Variables

### Core Settings

| Variable | Default | Description |
|---|---|---|
| `APP_NAME` | `PIKA` | Application name shown in UI and logs |
| `DEBUG` | `false` | Enable debug mode (human-readable logs, verbose output) |

### Ollama Connection

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API endpoint. Use `http://ollama:11434` in Docker |
| `OLLAMA_MODEL` | `llama3.2:3b` | Default model for Q&A generation |
| `OLLAMA_TIMEOUT` | `120` | Timeout in seconds for Ollama requests |

!!! note "Docker vs native"
    When running PIKA in Docker alongside the shared Ollama service, set `OLLAMA_BASE_URL=http://ollama:11434`. For native development with a local Ollama install, use `http://localhost:11434`.

### RAG Pipeline

| Variable | Default | Description |
|---|---|---|
| `CHUNK_SIZE` | `500` | Token chunk size for document splitting (100 -- 10,000) |
| `CHUNK_OVERLAP` | `50` | Overlap tokens between consecutive chunks |
| `TOP_K` | `5` | Number of chunks to retrieve per query (1 -- 50) |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence Transformer model for embeddings |

### Confidence Thresholds

| Variable | Default | Description |
|---|---|---|
| `CONFIDENCE_HIGH` | `0.7` | Similarity threshold for "high" confidence |
| `CONFIDENCE_MEDIUM` | `0.5` | Similarity threshold for "medium" confidence |
| `CONFIDENCE_LOW` | `0.3` | Similarity threshold for "low" confidence |

### Authentication

| Variable | Default | Description |
|---|---|---|
| `PIKA_ADMIN_PASSWORD` | _(none)_ | Password for admin page. If unset, admin is open |
| `PIKA_API_KEY` | _(none)_ | API key for programmatic access. If unset, API is open |
| `PIKA_SESSION_SECRET` | _(auto-generated)_ | Secret for signing session cookies. Set a stable value in production |

!!! warning "Production security"
    Always set `PIKA_ADMIN_PASSWORD`, `PIKA_API_KEY`, and `PIKA_SESSION_SECRET` in production. Leaving them unset makes the admin panel and API accessible without authentication.

### Hub Integration

| Variable | Default | Description |
|---|---|---|
| `HUB_BASE_URL` | _(empty)_ | Hub service URL (e.g., `http://hub:8000`). Set both Hub variables to enable centralised auth |
| `HUB_AUTH_API_KEY` | _(empty)_ | API key for Hub authentication. Supports Docker secrets |

When both `HUB_BASE_URL` and `HUB_AUTH_API_KEY` are set, PIKA delegates user authentication and license validation to Hub.

### Query Queue

| Variable | Default | Description |
|---|---|---|
| `MAX_CONCURRENT_QUERIES` | `1` | Queries running simultaneously. Use `1` for CPU, `2+` for GPU |
| `MAX_QUEUED_PER_USER` | `3` | Maximum pending queries per user |
| `MAX_QUEUE_SIZE` | `100` | Maximum total queue length |
| `QUEUE_TIMEOUT` | `300` | Seconds before a queued query times out |

### Circuit Breaker

| Variable | Default | Description |
|---|---|---|
| `CIRCUIT_BREAKER_ENABLED` | `true` | Enable circuit breaker for Ollama calls |
| `CIRCUIT_BREAKER_FAILURE_THRESHOLD` | `5` | Consecutive failures before the breaker opens |
| `CIRCUIT_BREAKER_RECOVERY_TIMEOUT` | `30` | Seconds before a half-open test is attempted |

### Query Cache

| Variable | Default | Description |
|---|---|---|
| `QUERY_CACHE_ENABLED` | `true` | Enable caching of query results |
| `QUERY_CACHE_TTL` | `300` | Cache entry time-to-live in seconds |
| `QUERY_CACHE_MAX_SIZE` | `100` | Maximum number of cached query results |

### Storage Paths

| Variable | Default | Description |
|---|---|---|
| `DOCUMENTS_DIR` | `./documents` | Directory for uploaded document files |
| `CHROMA_PERSIST_DIR` | `./data/chroma` | ChromaDB persistence directory |
| `AUDIT_LOG_PATH` | `./data/audit.log` | Path to the audit log file |

### Rate Limiting

| Variable | Default | Description |
|---|---|---|
| `RATE_LIMIT_AUTH` | `5/minute` | Rate limit for authentication endpoints |
| `RATE_LIMIT_QUERY` | `30/minute` | Rate limit for query endpoints |
| `RATE_LIMIT_ADMIN` | `10/minute` | Rate limit for admin operations (backup/restore) |

### Security

| Variable | Default | Description |
|---|---|---|
| `MAX_UPLOAD_SIZE_MB` | `50` | Maximum file upload size in MB (max 500) |
| `ALLOWED_EXTENSIONS` | `.pdf,.docx,.txt,.md` | Comma-separated list of allowed upload file extensions |

### Miscellaneous

| Variable | Default | Description |
|---|---|---|
| `BACKUP_RETENTION_COUNT` | `5` | Number of backups to retain (`0` = unlimited) |
| `MAX_HISTORY_ITEMS` | `50` | Query history entries per user |
| `MAX_FEEDBACK_ITEMS` | `500` | Total feedback entries to keep |
| `SESSION_CLEANUP_INTERVAL` | `300` | Seconds between session cleanup runs |
| `AUDIT_LOG_MAX_SIZE_MB` | `10` | Rotate audit log after this size |

## Docker Secrets

PIKA reads secrets from `/run/secrets/` when available, falling back to environment variables. This is the recommended approach for sensitive values in Docker Swarm or Compose deployments.

Supported secrets:

| Secret file | Fallback env var |
|---|---|
| `/run/secrets/pika_session_secret` | `PIKA_SESSION_SECRET` |
| `/run/secrets/hub_auth_api_key` | `HUB_AUTH_API_KEY` |

Example `docker-compose.yml` snippet:

```yaml
services:
  pika:
    image: ghcr.io/aidoo/pika:latest
    secrets:
      - pika_session_secret
      - hub_auth_api_key
    environment:
      OLLAMA_BASE_URL: http://ollama:11434

secrets:
  pika_session_secret:
    file: ./secrets/pika_session_secret.txt
  hub_auth_api_key:
    file: ./secrets/hub_auth_api_key.txt
```

## .env File Setup

Copy the example file and customise:

```bash
cp .env.example .env
```

Minimal production `.env`:

```ini
# Ollama (Docker)
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.1:8b

# Authentication (required for production)
PIKA_ADMIN_PASSWORD=your-secure-password
PIKA_API_KEY=your-api-key
PIKA_SESSION_SECRET=change-me-to-random-string

# Hub integration
HUB_BASE_URL=http://hub:8000
HUB_AUTH_API_KEY=your-hub-api-key

# RAG tuning
CHUNK_SIZE=500
TOP_K=5
```

!!! tip "GPU deployments"
    If your Ollama instance has GPU access, increase `MAX_CONCURRENT_QUERIES` to `2` or higher to process queries in parallel.
