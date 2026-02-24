# ai.doo

Static marketing site for [aidoo.biz](https://aidoo.biz), served from an Ubuntu VPS with Caddy. Also includes a small Python/Flask backend powering the AI chat widget.

## Hosting overview

- **Stack**: Static HTML/CSS/JS — no build step; Python/Flask chat API running as a systemd service
- **Server**: Ubuntu VPS running [Caddy](https://caddyserver.com/)
- **Web root**: `/var/www/aidoo.biz`
- **Chat API**: `/opt/aidoo-api/` (gunicorn on `127.0.0.1:8765`, proxied by Caddy)
- **TLS**: Automatic via Caddy (provisions and renews certificates)
- **Deploy**: Pushes to `main` auto-deploy via GitHub Actions (rsync over SSH)

## Auto-deploy workflow

The workflow at `.github/workflows/deploy.yml` runs two jobs on every push to `main`:

### Job 1: `deploy` (static site)
1. Checks out the repo
2. Fetches the PIKA changelog from its private repo and builds `pika/changelog.html`
3. Rsyncs site files to `/var/www/aidoo.biz/`, excluding `.git`, `.github`, `README.md`, `api/`, and other non-web files
4. Caddy serves the updated files immediately (no restart needed)

### Job 2: `deploy-api` (chat backend, runs after `deploy`)
1. Rsyncs `api/` to `/opt/aidoo-api/` on the VPS
2. Runs `pip install` to pick up any dependency changes
3. Restarts the `aidoo-api` systemd service

### Required GitHub secrets

Stored under the **VPS** environment in Settings > Secrets and variables > Actions:

| Secret | Description |
|--------|-------------|
| `VPS_HOST` | Server IP or hostname |
| `VPS_USER` | SSH username on the VPS |
| `VPS_SSH_KEY` | Private ed25519 key for SSH auth |
| `OPENAI_API_KEY` | OpenAI API key for the chat widget |
| `PIKA_REPO_TOKEN` | GitHub token to fetch the PIKA changelog |

The matching public key must be in `~/.ssh/authorized_keys` on the VPS for the deploy user.

## VPS setup

### 1) Install Caddy

```
sudo apt update
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf "https://dl.cloudsmith.io/public/caddy/stable/gpg.key" | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf "https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt" | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install -y caddy
```

### 2) Configure Caddy

```
sudo tee /etc/caddy/Caddyfile >/dev/null <<'EOF'
aidoo.biz, www.aidoo.biz {
    root * /var/www/aidoo.biz
    reverse_proxy /api/* localhost:8765
    file_server
}
EOF

sudo systemctl reload caddy
```

### 3) Prepare the web root

```
sudo mkdir -p /var/www/aidoo.biz
sudo chown -R <deploy-user>:<deploy-user> /var/www/aidoo.biz
```

### 4) Set up the deploy key

```
ssh-keygen -t ed25519 -f ~/deploy_key -C "github-actions-deploy" -N ""
cat ~/deploy_key.pub >> ~/.ssh/authorized_keys
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

Copy the contents of `~/deploy_key` into the `VPS_SSH_KEY` GitHub secret, then delete both key files from the VPS.

### 5) Set up the chat API backend

```bash
# Create venv and install dependencies
sudo apt install python3.12-venv
mkdir -p /opt/aidoo-api
python3 -m venv /opt/aidoo-api/venv
/opt/aidoo-api/venv/bin/pip install flask openai gunicorn

# Create env file
echo "OPENAI_API_KEY=sk-..." | sudo tee /etc/aidoo-api.env
sudo chmod 600 /etc/aidoo-api.env

# Install systemd service
sudo tee /etc/systemd/system/aidoo-api.service >/dev/null <<'EOF'
[Unit]
Description=ai.doo Chat API
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/aidoo-api
EnvironmentFile=/etc/aidoo-api.env
ExecStart=/opt/aidoo-api/venv/bin/gunicorn -w 2 -b 127.0.0.1:8765 chat:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable aidoo-api
sudo systemctl start aidoo-api

# Allow deploy user to restart the service without a password
echo "<deploy-user> ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart aidoo-api" \
  | sudo tee /etc/sudoers.d/aidoo-deploy

# Set correct ownership so deploy user can rsync to /opt/aidoo-api/
sudo chown -R <deploy-user> /opt/aidoo-api
```

### Smoke test

```bash
curl -s -X POST https://aidoo.biz/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"What is PIKA?"}' | python3 -m json.tool
```

## Manual deploy

If needed, you can bypass the workflow and deploy manually:

```
rsync -avz --delete ./ <deploy-user>@<vps-host>:/var/www/aidoo.biz/
```
