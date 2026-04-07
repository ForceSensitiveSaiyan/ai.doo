# Installer Script

!!! warning "Coming Soon"
    The automated installer script is under development and not yet available. In the meantime, follow the [Quick Start](quick-start.md) guide for manual installation.

The installer script will automate the full ai.doo stack setup, including:

- Checking prerequisites (Docker, Docker Compose, curl)
- GPU detection (NVIDIA via `nvidia-smi`)
- Interactive product selection (PIKA, VERA, or both)
- Secret generation and directory setup
- Docker image pull and service startup
- Health checks and optional Caddy reverse proxy for TLS

## Planned Options

| Flag | Description |
|------|-------------|
| `--no-gpu` | Skip GPU detection, use CPU mode |
| `--products pika,vera` | Skip product selection prompt |
| `--password <pass>` | Set admin password (skip interactive prompt) |
| `--domain example.com` | Set domain for reverse proxy |
| `--yes` | Accept all defaults (non-interactive) |

## Directory Structure

After installation, your `~/aidoo/` directory will contain:

```
~/aidoo/
├── .env                 # Environment variables
├── docker-compose.yml   # Stack definition
├── secrets/             # Docker secrets
│   ├── hub_admin_password
│   ├── hub_auth_api_key
│   └── hub_secret_key
└── data/                # Persistent data
    ├── ollama/          # Model storage
    ├── hub/             # Hub database
    ├── pika/            # PIKA documents + ChromaDB
    └── vera/            # VERA uploads
```
