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

## Kubernetes (Helm)

Chart: `deploy/helm/coding-harness` (api, frontend, worker, optional bundled Postgres, Ingress, HPA/PDB, NetworkPolicies).

```bash
./deploy/kind/up.sh        # kind cluster + Traefik + local images + chart -> http://localhost:8081
tilt up                    # same cluster, rebuilds images and redeploys on change
```

| Values file        | Use |
|--------------------|-----|
| `values.yaml`      | defaults: images from `ghcr.io/shahryar908`, bundled Postgres, generated secrets |
| `values-dev.yaml`  | kind/Tilt: local `:dev` images, 1 replica each, `localhost` ingress |
| `values-prod.yaml` | external DB + secrets via `secrets.existingSecret` (keys `JWT_SECRET`, `DATABASE_URL`), HPA, cert-manager TLS |

Ingress routes `/auth` to the API and everything else to the frontend.
The worker runs model-generated commands, so it gets no service-account token, no secrets and no
database access, and its NetworkPolicy blocks all egress (`worker.networkPolicy.allowEgress`) and
only accepts traffic from the API or pods labelled `app.kubernetes.io/component=harness`.
NetworkPolicies need a CNI that enforces them (kind's default kindnet does).

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
