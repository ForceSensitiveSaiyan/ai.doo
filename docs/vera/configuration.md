# Configuration

VERA is configured through environment variables, typically set in a `.env` file at the project root. Docker Compose reads this file automatically.

## Environment Variables

### Database

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://vera:vera@postgres:5432/vera` | PostgreSQL connection string (async driver) |
| `POSTGRES_USER` | `vera` | PostgreSQL user (used by the `postgres` container) |
| `POSTGRES_PASSWORD` | `vera` | PostgreSQL password |
| `POSTGRES_DB` | `vera` | PostgreSQL database name |

### Celery / Redis

| Variable | Default | Description |
|---|---|---|
| `CELERY_BROKER_URL` | `redis://:vera_redis@redis:6379/0` | Redis URL for Celery task broker |
| `CELERY_RESULT_BACKEND` | `redis://:vera_redis@redis:6379/0` | Redis URL for Celery result backend |
| `REDIS_PASSWORD` | `vera_redis` | Redis AUTH password |
| `STUCK_TASK_TIMEOUT_MINUTES` | `30` | Minutes before a stuck processing task is recovered |

### Ollama (AI Summaries)

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_URL` | `http://ollama:11434` | Ollama API endpoint |
| `OLLAMA_MODEL` | `llama3.1` | Default model for AI summaries |
| `OLLAMA_TIMEOUT` | `300` | Timeout in seconds for Ollama requests |

!!! info "Ollama is optional"
    VERA works without Ollama. If the Ollama service is unreachable, AI summaries are unavailable but all other features (upload, OCR, review, export) continue normally.

### Upload & Retention

| Variable | Default | Description |
|---|---|---|
| `MAX_UPLOAD_MB` | `25` | Maximum upload file size in megabytes |
| `RETENTION_DAYS` | `30` | Number of days to retain documents before cleanup |
| `UPLOAD_RATE_LIMIT` | `10/minute` | Rate limit for the upload endpoint (SlowAPI format) |
| `DATA_DIR` | `/data` | Directory for uploaded files (mounted as a volume) |

### Authentication (Hub)

| Variable | Default | Description |
|---|---|---|
| `HUB_BASE_URL` | `http://hub:8000` | Base URL of the Hub authentication service |
| `HUB_AUTH_API_KEY` | _(empty)_ | API key for Hub service-to-service auth |

!!! warning "Authentication behavior"
    When `HUB_BASE_URL` is not set or Hub is unreachable, VERA runs in **open mode** with no authentication. Set both `HUB_BASE_URL` and `HUB_AUTH_API_KEY` for production deployments.

### Security

| Variable | Default | Description |
|---|---|---|
| `SECURE_COOKIES` | `true` | Set session cookies with `Secure` flag. Disable (`false`) for local HTTP-only development |
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). Use `DEBUG` only for development |

### Networking & CORS

| Variable | Default | Description |
|---|---|---|
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated list of allowed CORS origins |
| `BACKEND_PORT` | `4000` | Host port mapped to the backend container |
| `FRONTEND_PORT` | `3000` | Host port mapped to the frontend container |
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:4000` | Backend URL used by the frontend (client-side) |

### Resource Limits

| Variable | Default | Description |
|---|---|---|
| `BACKEND_MEMORY_LIMIT` | `1G` | Memory limit for the backend container |
| `WORKER_MEMORY_LIMIT` | `4G` | Memory limit for the Celery worker container |
| `WORKER_CPU_LIMIT` | `2.0` | CPU limit for the Celery worker container |

### Backup

| Variable | Default | Description |
|---|---|---|
| `BACKUP_HOST_DIR` | `./backups` | Host directory for database backups |
| `BACKUP_RETENTION_DAYS` | `7` | Days to keep backup files |
| `BACKUP_INTERVAL_SECONDS` | `86400` | Interval between automated backups (default: 24 hours) |

## Docker Secrets

VERA supports Docker secrets for sensitive values. The `hub_auth_api_key` secret is configured in `docker-compose.yml`:

```yaml
secrets:
  hub_auth_api_key:
    file: ${HUB_AUTH_API_KEY_FILE:-./secrets/hub_auth_api_key}
```

To set up the secret:

```bash
mkdir -p secrets
echo "your-hub-api-key-here" > secrets/hub_auth_api_key
chmod 600 secrets/hub_auth_api_key
```

!!! tip "Secrets directory"
    The `secrets/` directory is gitignored. Never commit API keys to version control.

## .env Setup

Copy the example and edit:

```bash
cp .env.example .env
```

A minimal `.env` for local development:

```ini
# Database
DATABASE_URL=postgresql+psycopg://vera:vera@postgres:5432/vera
POSTGRES_PASSWORD=vera

# Redis / Celery
REDIS_PASSWORD=vera_redis
CELERY_BROKER_URL=redis://:vera_redis@redis:6379/0
CELERY_RESULT_BACKEND=redis://:vera_redis@redis:6379/0

# Ollama (optional)
OLLAMA_URL=http://ollama:11434
OLLAMA_MODEL=llama3.1

# Hub auth (optional for local dev)
# HUB_BASE_URL=http://hub:8000
# HUB_AUTH_API_KEY=your-key-here

# CORS
CORS_ORIGINS=http://localhost:3000
```

## Database Migrations (Alembic)

VERA uses Alembic for PostgreSQL schema management. Always run migrations after pulling new code or on first startup:

```bash
docker compose exec backend alembic upgrade head
```

Check current migration status:

```bash
docker compose exec backend alembic current
```

View migration history:

```bash
docker compose exec backend alembic history --verbose
```

!!! danger "Always run migrations"
    Skipping `alembic upgrade head` after a code update can cause runtime errors if the database schema is out of date. The backend does **not** auto-migrate on startup.
