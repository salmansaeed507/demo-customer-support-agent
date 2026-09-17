dev:
	uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 5071

migrate:
	uv run alembic upgrade head
