# Installer Script

The installer script automates the full ai.doo stack setup.

## Usage

```bash
curl -fsSL https://get.aidoo.biz/install.sh | bash
```

Or download and run manually:

```bash
wget https://get.aidoo.biz/install.sh
chmod +x install.sh
./install.sh
```

## What It Does

1. **Checks prerequisites** — verifies Docker, Docker Compose, and curl are installed.
2. **Detects GPU** — checks for NVIDIA GPU via `nvidia-smi`.
3. **Interactive prompts** — asks which products to install, admin password, and domain names.
4. **Creates directory structure** — sets up `~/aidoo/` with configs and secrets.
5. **Generates secrets** — creates random passwords and API keys using `openssl rand`.
6. **Pulls images** — downloads Docker images from GHCR.
7. **Starts the stack** — launches services in order: Ollama, Hub, then PIKA/VERA.
8. **Health checks** — verifies all services are running.
9. **Optional** — offers to set up Caddy reverse proxy for TLS.

## Options

| Flag | Description |
|------|-------------|
| `--no-gpu` | Skip GPU detection, use CPU mode |
| `--products pika,vera` | Skip product selection prompt |
| `--password <pass>` | Set admin password (skip interactive prompt) |
| `--domain example.com` | Set domain for reverse proxy |
| `--yes` | Accept all defaults (non-interactive) |

### Non-interactive example

```bash
./install.sh --products pika,vera --password 'MySecure1' --no-gpu --yes
```

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
