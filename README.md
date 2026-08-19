# TableScore

Live table scoreboard (FastAPI + Postgres). Create a room, share a 4-letter password, score together on phones.

## Local setup

Requires **Docker Desktop** (or any Postgres 16) for the database.

```bash
# 1. Start Postgres
docker compose up -d

# 2. Env
cp .env.example .env

# 3. Dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 4. Run
uvicorn main:app --reload
```

Open http://127.0.0.1:8000

## Environment

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | Postgres URL. Use `postgresql+psycopg://...` or plain `postgresql://...` (auto-rewritten). |

Never commit `.env`. Hosted platforms set `DATABASE_URL` in their dashboard.

## Deploy (GitHub → host)

Repo: [elbyrd09/tablescore](https://github.com/elbyrd09/tablescore)

1. Push to `main`.
2. On Render/Railway/Fly: create a web service **from this GitHub repo** (Dockerfile) + a Postgres addon.
3. Set `DATABASE_URL` from the addon (scheme rewrite is handled in app).
4. Keep **one** instance for now.
5. Optional: custom domain e.g. `play.yourdomain.com`.

Start command (if not using Dockerfile):  
`uvicorn main:app --host 0.0.0.0 --port $PORT`

## Storage notes

- Each room is one row (`rooms`) with JSONB `state`.
- Passwords are unique while a room lives.
- Rooms expire after **48h** of inactivity, or **24h** after the game ends (frees passwords).
