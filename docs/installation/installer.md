# Installer Script

The automated installer script sets up the full ai.doo stack on a fresh Linux server in under 10 minutes.

## Download and Run

```bash
curl -fsSL https://raw.githubusercontent.com/aidoo-systems/ollama/master/scripts/install.sh | bash
```

Or clone the repo and run directly:

```bash
git clone https://github.com/aidoo-systems/ollama.git
cd ollama
./scripts/install.sh
```

## What It Does

- Checks prerequisites (Docker, Docker Compose, curl)
- GPU detection (NVIDIA via `nvidia-smi`)
- Interactive product selection (PIKA, VERA, or both)
- Secret generation and directory setup
- Docker image pull and service startup
- Health checks and readiness verification

## Options

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

## Next Steps

After installation:

1. Open Hub at `http://your-server:2000` and log in with your admin credentials
2. Pull a model from the Models tab (e.g. `llama3.2:3b`)
3. Activate your license key in the License tab
4. Open PIKA at `:8000` or VERA at `:3000` and log in with your Hub credentials

For production deployments with TLS and hostname routing, see the [Reverse Proxy](../admin/reverse-proxy.md) guide.
