# Backup & Restore

Each ai.doo service stores data differently. This guide covers what to back up, how to automate it, and how to restore.

## What to Back Up

| Service | Data | Storage | Location |
|---|---|---|---|
| Hub | User accounts, license, audit log | SQLite | `data/hub.db` |
| PIKA | Document embeddings | ChromaDB (file-based) | `data/chroma/` |
| PIKA | Chat history, collections | SQLite | `data/pika.db` |
| VERA | Jobs, documents, users | PostgreSQL | Database `vera` |
| VERA | Task queue | Redis | Ephemeral — no backup needed |
| Ollama | Downloaded models | Docker volume | `ollama_models` |

## Hub Backup

Hub uses a single SQLite file. Stop writes or use `.backup` to get a consistent copy.

```bash
# Simple file copy (stop Hub first for consistency)
docker compose -f ollama/docker-compose.yml stop hub
cp ollama/data/hub.db /backup/hub/hub-$(date +%Y%m%d).db
docker compose -f ollama/docker-compose.yml start hub
```

!!! tip
    For zero-downtime backups, use SQLite's online backup API:

    ```bash
    docker compose -f ollama/docker-compose.yml exec hub \
      sqlite3 /app/data/hub.db ".backup '/tmp/hub-backup.db'"
    docker compose -f ollama/docker-compose.yml cp hub:/tmp/hub-backup.db /backup/hub/
    ```

## PIKA Backup

PIKA stores embeddings in ChromaDB (file-based) and metadata in SQLite. Back up the entire `data/` directory.

```bash
docker compose -f pika/docker-compose.yml stop pika
tar czf /backup/pika/pika-data-$(date +%Y%m%d).tar.gz -C pika data/
docker compose -f pika/docker-compose.yml start pika
```

## VERA Backup

VERA uses PostgreSQL for persistent data. Redis is used only as a Celery broker and result backend — it can be rebuilt from scratch.

### PostgreSQL Dump

```bash
docker compose -f vera/docker-compose.yml exec db \
  pg_dump -U vera -d vera --format=custom \
  > /backup/vera/vera-$(date +%Y%m%d).dump
```

!!! note
    `pg_dump` runs while the database is online and produces a consistent snapshot. No downtime is required.

### Uploaded Files

If VERA stores uploaded documents on disk rather than in the database, also back up the uploads directory:

```bash
tar czf /backup/vera/vera-uploads-$(date +%Y%m%d).tar.gz -C vera data/uploads/
```

## Ollama Models

Models are stored in the `ollama_models` Docker volume. You can back up the volume or simply re-pull models after a restore.

```bash
# Export the volume to a tarball
docker run --rm \
  -v ollama_models:/data \
  -v /backup/ollama:/backup \
  alpine tar czf /backup/ollama-models-$(date +%Y%m%d).tar.gz -C /data .
```

!!! tip
    Models can be several gigabytes each. If bandwidth is available, it is often faster to re-pull them with `./scripts/pull-models.sh` than to restore from a backup.

## Example Cron Jobs

Add these to your server's crontab (`crontab -e`):

```cron
# Daily at 02:00 — Hub
0 2 * * * cp /path/to/ollama/data/hub.db /backup/hub/hub-$(date +\%Y\%m\%d).db

# Daily at 02:15 — PIKA
15 2 * * * tar czf /backup/pika/pika-data-$(date +\%Y\%m\%d).tar.gz -C /path/to/pika data/

# Daily at 02:30 — VERA PostgreSQL
30 2 * * * docker compose -f /path/to/vera/docker-compose.yml exec -T db pg_dump -U vera -d vera --format=custom > /backup/vera/vera-$(date +\%Y\%m\%d).dump

# Weekly on Sunday at 03:00 — Ollama models
0 3 * * 0 docker run --rm -v ollama_models:/data -v /backup/ollama:/backup alpine tar czf /backup/ollama-models-$(date +\%Y\%m\%d).tar.gz -C /data .

# Daily at 04:00 — prune backups older than 30 days
0 4 * * * find /backup -name "*.db" -o -name "*.tar.gz" -o -name "*.dump" -mtime +30 -delete
```

## Restore Procedures

### Hub

```bash
docker compose -f ollama/docker-compose.yml stop hub
cp /backup/hub/hub-20260317.db ollama/data/hub.db
docker compose -f ollama/docker-compose.yml start hub
```

### PIKA

```bash
docker compose -f pika/docker-compose.yml down
rm -rf pika/data/
tar xzf /backup/pika/pika-data-20260317.tar.gz -C pika/
docker compose -f pika/docker-compose.yml up -d
```

### VERA

```bash
docker compose -f vera/docker-compose.yml exec -T db \
  pg_restore -U vera -d vera --clean --if-exists \
  < /backup/vera/vera-20260317.dump
```

!!! warning
    `--clean` drops existing objects before restoring. This is safe for a full restore but will destroy any data created after the backup was taken.

### Ollama Models

```bash
# Restore the volume
docker run --rm \
  -v ollama_models:/data \
  -v /backup/ollama:/backup \
  alpine sh -c "cd /data && tar xzf /backup/ollama-models-20260317.tar.gz"
```

Or simply re-pull:

```bash
cd ollama
./scripts/pull-models.sh llama3.2:3b qwen2.5-coder:14b
```
