# customer-support-agent

FastAPI service for the ShopPilot customer support demo.

## Setup

```bash
ln -sfn ../api-gateway/common common
uv sync
export PYTHONPATH=.
```

## Run locally

```bash
make dev
# or
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 5071
```

## Migrations

```bash
export DATABASE_URL=postgresql://demo:demo@localhost:5432/demo
alembic upgrade head
```

## API

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Health check |
| `GET/POST /products`, `GET/PATCH/DELETE /products/{id}` | Product management |
| `GET/POST /tickets`, `GET/PATCH/DELETE /tickets/{id}` | Ticket management |
| `GET/POST /orders`, `GET/PATCH/DELETE /orders/{id}` | Order management |
| `GET /orders/{id}/status` | Order status |
| `POST /checkout` | Checkout (creates order, decrements stock) |
| `GET/POST /knowledge-docs`, `GET/PATCH/DELETE /knowledge-docs/{id}` | Knowledge base |
| `POST /knowledge-docs/{id}/reindex` | Reindex stub |
| `GET/POST /chat/threads`, `GET/PATCH/DELETE /chat/threads/{id}` | Chat threads |
| `POST /chat/threads/{id}/clear` | Clear thread messages |
| `GET/POST /chat/threads/{id}/messages` | Thread messages |
| `POST /agent/turn` | Simulated agent interaction |

## Docker

```bash
docker build -t customer-support-agent .
docker run -p 8000:8000 customer-support-agent
```
