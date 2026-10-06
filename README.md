# coding-harness

- `backend/` — FastAPI auth API (SQLModel; SQLite locally, Postgres in deployment) plus the `routers/brain_harness` coding-agent CLI.
- `frontend/` — Bun + React + Tailwind template.

## Docker (full local stack)

```bash
docker compose up --build
```

| Service  | URL                    | Notes                                  |
|----------|------------------------|----------------------------------------|
| frontend | http://localhost:8080  | nginx serving the Bun build, proxies `/auth` to the API |
| api      | http://localhost:8000  | FastAPI on Postgres                    |
| worker   | http://127.0.0.1:8100  | agent execution worker (`mock_worker.py`), no secrets |
| postgres | internal only          | data in the `pgdata` volume            |

Images: `backend/Dockerfile` (targets `api` and `worker`) and `frontend/Dockerfile`. All run as non-root with read-only root filesystems.
Point the agent CLI at the containerized worker: `python cli.py "..." --worker http://localhost:8100`.

## Backend

```bash
cd backend
cp .env.example .env   # set JWT_SECRET, DATABASE_URL, GROQ_API_KEY
uv sync
uv run uvicorn main:app --reload
uv run ruff check .
uv run pytest
```

Health probes: `GET /health` (liveness), `GET /ready` (checks the database).

## Frontend

```bash
cd frontend
bun install
bun dev
```
