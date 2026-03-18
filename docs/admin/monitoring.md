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
# Example for Hub
services:
  hub:
    image: ghcr.io/aidoo-biz/hub:latest
    healthcheck:
      test: ["CMD", "curl", "-sf", "http://localhost:2000/health"]
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
# Example for VERA
services:
  backend:
    image: ghcr.io/aidoo-biz/vera-backend:latest
    healthcheck:
      test: ["CMD", "curl", "-sf", "http://localhost:4000/health"]
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
| Hub | `http://hub:2000/metrics` |
| PIKA | `http://pika:8000/metrics` |
| VERA API | `http://vera-backend:4000/metrics` |

### Key Metrics

| Metric | Type | Description |
|---|---|---|
| `http_requests_total` | counter | Total HTTP requests by method, path, and status code |
| `http_request_duration_seconds` | histogram | Request latency distribution |
| `auth_attempts_total` | counter | Login attempts by result (`success`, `failure`, `locked`) |
| `auth_lockouts_total` | counter | Accounts locked due to failed attempts |
| `model_pull_total` | counter | Model pull operations by status |
| `model_pull_duration_seconds` | histogram | Time to pull a model |
| `active_users` | gauge | Currently active user sessions |
| `license_seats_used` | gauge | Number of seats consumed |
| `license_days_remaining` | gauge | Days until license expiry (-1 if unlicensed) |

### Prometheus Configuration

Add the ai.doo targets to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: aidoo-hub
    static_configs:
      - targets: ["hub:2000"]

  - job_name: aidoo-pika
    static_configs:
      - targets: ["pika:8000"]

  - job_name: aidoo-vera
    static_configs:
      - targets: ["vera-backend:4000"]
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
| Request rate | `rate(http_requests_total[5m])` | Time series, grouped by service |
| Error rate | `rate(http_requests_total{status=~"5.."}[5m])` | Time series |
| P95 latency | `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))` | Time series, by service |
| Auth failures | `rate(auth_attempts_total{result="failure"}[5m])` | Time series |
| Active users | `active_users` | Stat |
| License seats | `license_seats_used` | Gauge (max = license seat limit) |
| License expiry | `license_days_remaining` | Stat with thresholds (red < 30) |
| Model pulls | `increase(model_pull_total[24h])` | Stat |

### Alerts

Consider setting up Grafana alerts for:

- **Service down** — health check returning non-200 for > 2 minutes.
- **High error rate** — 5xx rate exceeds 5% of total requests over 5 minutes.
- **Auth brute force** — `auth_lockouts_total` increases by more than 3 in 10 minutes.
- **License expiring** — `license_days_remaining` falls below 30.
- **Disk space** — Ollama models volume exceeding 80% capacity.
