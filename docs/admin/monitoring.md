# Monitoring

All ai.doo services expose health check and Prometheus metrics endpoints for observability.

## Health Check Endpoints

| Service | Endpoint | Port | Healthy Response |
|---|---|---|---|
| Ollama | `GET /api/tags` | 11434 | `200` with model list |
| Hub | `GET /health` | 2000 | `200 {"status": "ok"}` |
| PIKA | `GET /health` | 8000 | `200 {"status": "ok"}` |
| VERA API | `GET /health` | 4000 | `200 {"status": "ok"}` |

Quick check from the host:

```bash
curl -sf http://localhost:2000/health && echo "Hub OK"
curl -sf http://localhost:8000/health && echo "PIKA OK"
curl -sf http://localhost:4000/health && echo "VERA OK"
```

## Docker Healthchecks

Each service's `docker-compose.yml` should include a healthcheck so Docker can detect failures and restart containers automatically.

```yaml
# Example for Hub (internal port 8000, mapped to 2000 on host)
services:
  hub:
    image: ghcr.io/aidoo-biz/hub:latest
    healthcheck:
      test: ["CMD", "curl", "-sf", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 15s
```

```yaml
# Example for PIKA
services:
  pika:
    image: ghcr.io/aidoo-biz/pika:latest
    healthcheck:
      test: ["CMD", "curl", "-sf", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
```

```yaml
# Example for VERA (internal port 8000, mapped to 4000 on host)
services:
  backend:
    image: ghcr.io/aidoo-biz/vera-backend:latest
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
```

!!! tip
    Use `docker ps` to see health status. Containers show `(healthy)`, `(unhealthy)`, or `(health: starting)` next to their status.

## Prometheus Metrics

Each service exposes metrics in Prometheus exposition format at `/metrics`.

| Service | Endpoint |
|---|---|
| Hub | `http://hub:8000/metrics` (Docker) / `http://localhost:2000/metrics` (host) |
| PIKA | `http://pika:8000/metrics` (Docker) / `http://localhost:8000/metrics` (host) |
| VERA API | `http://backend:8000/metrics` (Docker) / `http://localhost:4000/metrics` (host) |

### Hub Metrics

| Metric | Type | Labels | Description |
|---|---|---|---|
| `hub_http_requests_total` | counter | method, endpoint, status_code | Total HTTP requests |
| `hub_http_request_duration_seconds` | histogram | method, endpoint | Request latency distribution |
| `hub_model_operations_total` | counter | operation (`list`, `pull`, `delete`) | Model management operations |
| `hub_auth_attempts_total` | counter | result (`success`, `failure`) | Login attempts |

### PIKA Metrics

| Metric | Type | Labels | Description |
|---|---|---|---|
| `pika_http_requests_total` | counter | method, endpoint, status_code | Total HTTP requests |
| `pika_http_request_duration_seconds` | histogram | method, endpoint | Request latency |
| `pika_query_count_total` | counter | confidence | Queries by confidence level |
| `pika_query_duration_seconds` | histogram | — | Query latency (RAG + LLM) |
| `pika_active_queries` | gauge | — | Queries currently running |
| `pika_queued_queries` | gauge | — | Queries waiting in FIFO queue |
| `pika_index_documents_total` | gauge | — | Indexed document count |
| `pika_index_chunks_total` | gauge | — | Total chunks in vector store |
| `pika_ollama_healthy` | gauge | — | Ollama reachability (1 = up) |
| `pika_circuit_breaker_state` | gauge | — | Circuit breaker state (0 = closed, 1 = open, 2 = half-open) |
| `pika_active_sessions` | gauge | — | Active user sessions |

### VERA Metrics

| Metric | Type | Labels | Description |
|---|---|---|---|
| `vera_http_requests_total` | counter | method, endpoint, status_code | Total HTTP requests |
| `vera_http_request_duration_seconds` | histogram | method, endpoint | Request latency |
| `vera_ocr_duration_seconds` | histogram | — | OCR processing time per document |
| `vera_summary_duration_seconds` | histogram | — | Summary generation time |
| `vera_summary_llm_failures_total` | counter | — | Failed LLM summary attempts |

### Prometheus Configuration

Add the ai.doo targets to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: aidoo-hub
    static_configs:
      - targets: ["hub:8000"]

  - job_name: aidoo-pika
    static_configs:
      - targets: ["pika:8000"]

  - job_name: aidoo-vera
    static_configs:
      - targets: ["backend:8000"]
```

!!! note
    If Prometheus runs outside Docker, use the host-mapped ports (e.g. `localhost:2000`). If it runs on the same `ollama_network`, use the service names as shown above.

## Grafana Dashboard

### Setup

1. Add Prometheus as a data source in Grafana (`http://prometheus:9090`).
2. Import or create a dashboard with the panels below.

### Recommended Panels

| Panel | Query | Visualisation |
|---|---|---|
| Hub request rate | `rate(hub_http_requests_total[5m])` | Time series |
| Hub error rate | `rate(hub_http_requests_total{status_code=~"5.."}[5m])` | Time series |
| Hub P95 latency | `histogram_quantile(0.95, rate(hub_http_request_duration_seconds_bucket[5m]))` | Time series |
| Auth failures | `rate(hub_auth_attempts_total{result="failure"}[5m])` | Time series |
| PIKA active queries | `pika_active_queries` | Stat |
| PIKA queue depth | `pika_queued_queries` | Stat |
| PIKA circuit breaker | `pika_circuit_breaker_state` | Stat with thresholds (red = 1) |
| VERA OCR P95 | `histogram_quantile(0.95, rate(vera_ocr_duration_seconds_bucket[5m]))` | Time series |
| VERA LLM failures | `rate(vera_summary_llm_failures_total[5m])` | Time series |
| Model operations | `increase(hub_model_operations_total[24h])` | Stat, by operation |

### Alerts

Consider setting up Grafana alerts for:

- **Service down** — health check returning non-200 for > 2 minutes.
- **High error rate** — 5xx rate exceeds 5% of total requests over 5 minutes.
- **Auth brute force** — `rate(hub_auth_attempts_total{result="failure"}[10m])` exceeds threshold.
- **PIKA circuit breaker open** — `pika_circuit_breaker_state == 1` for > 1 minute.
- **Disk space** — Ollama models volume exceeding 80% capacity.
