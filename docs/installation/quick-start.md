# Quick Start

Get the ai.doo suite running in under 10 minutes.

## Prerequisites

Ensure you have Docker and Docker Compose installed:

```bash
docker --version         # 24.0+
docker compose version   # v2.20+
```

See [Hardware Requirements](requirements.md) for GPU and system specs.

---

## 1. Start Ollama + Hub

Hub is the central management service. It handles user accounts, model management, and licensing. Start it first.

```bash
cd ollama
make up              # NVIDIA GPU (default)
# make up CPU=1      # CPU-only
# make up ROCM=1     # AMD GPU
```

This creates the shared `ollama_network` Docker network that PIKA and VERA connect to.

Verify both services are running:

```bash
curl http://localhost:11434/api/tags    # Ollama — should return JSON
curl http://localhost:2000/health       # Hub — should return "ok"
```

## 2. Pull an AI Model

Pull at least one model. `llama3.2:3b` is a good default (~2 GB):

```bash
./scripts/pull-models.sh llama3.2:3b
```

Or pull via the Hub UI at [http://localhost:2000](http://localhost:2000) → Models tab.

## 3. Set Up Hub

1. Open [http://localhost:2000](http://localhost:2000) in your browser.
2. On first visit, create your **admin account** (username + password).
3. Note your admin credentials — you'll use them to log in to PIKA and VERA.
4. (Optional) Create additional user accounts under the **Users** tab.
5. (Optional) Activate a license key under **Admin > License**.

### Generate an auth API key

PIKA and VERA authenticate users via Hub. They need an API key to communicate with Hub's internal auth endpoint.

Set `HUB_AUTH_API_KEY` in your Hub `.env` file (or Docker secret). Use a random value:

```bash
# Generate a random key
openssl rand -hex 32
```

Add it to `ollama/.env`:

```
HUB_AUTH_API_KEY=<paste-your-key-here>
```

Restart Hub to pick up the new key:

```bash
docker compose restart hub
```

You'll use this same key in PIKA and VERA's configuration.

---

## 4. Start PIKA (Document Q&A)

```bash
cd pika
cp .env.example .env
```

Edit `.env` and set these two variables (using the API key from step 3):

```
HUB_BASE_URL=http://hub:8000
HUB_AUTH_API_KEY=<same-key-from-hub>
```

Start PIKA:

```bash
docker compose up -d
```

Verify:

```bash
curl http://localhost:8000/health    # should return "ok"
```

Open [http://localhost:8000](http://localhost:8000) and log in with your Hub admin credentials.

---

## 5. Start VERA (OCR Validation)

```bash
cd vera
cp .env.example .env
```

Edit `.env` and set:

```
HUB_BASE_URL=http://hub:8000
HUB_AUTH_API_KEY=<same-key-from-hub>
```

Start VERA:

```bash
docker compose up -d --build
docker compose exec backend alembic upgrade head
```

Verify:

```bash
curl http://localhost:4000/health    # Backend
curl http://localhost:3000           # Frontend
```

Open [http://localhost:3000](http://localhost:3000) and log in with your Hub credentials.

!!! note
    VERA has 5 services (backend, frontend, worker, postgres, redis). First startup takes longer as images build. Use `docker compose ps` to check all services are healthy.

---

## 6. Verify Everything

Run all health checks:

```bash
curl http://localhost:11434/api/tags    # Ollama
curl http://localhost:2000/health       # Hub
curl http://localhost:8000/health       # PIKA
curl http://localhost:4000/health       # VERA backend
```

### Default Ports

| Service | URL | Description |
|---------|-----|-------------|
| Ollama | `http://localhost:11434` | AI inference API |
| Hub | `http://localhost:2000` | Management UI |
| PIKA | `http://localhost:8000` | Document Q&A |
| VERA frontend | `http://localhost:3000` | OCR validation UI |
| VERA backend | `http://localhost:4000` | VERA API |

---

## Troubleshooting

**Hub won't start:**
Check logs with `docker compose logs hub`. Common issues: missing `python-multipart` (fixed in v1.3.0), data directory permissions.

**PIKA/VERA can't authenticate:**
Verify `HUB_BASE_URL` and `HUB_AUTH_API_KEY` are set and match between Hub and the app. The API key must be identical.

**Ollama unreachable from PIKA/VERA:**
Ensure the services are on the `ollama_network`. Check with `docker network inspect ollama_network`.

**VERA OCR not processing:**
Check the Celery worker is running: `docker compose ps` — the `worker` service should show as healthy.

See [Troubleshooting](../troubleshooting.md) for more.

---

## Next Steps

- [Configure a reverse proxy](../admin/reverse-proxy.md) for TLS
- [Activate your license](../admin/licensing.md)
- [Set up backups](../admin/backup-restore.md)
- [Monitor with Prometheus](../admin/monitoring.md)
