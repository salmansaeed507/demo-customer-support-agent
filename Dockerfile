FROM python:3.12-slim AS base

WORKDIR /app

RUN adduser --disabled-password --gecos "" appuser

COPY pyproject.toml .
COPY common/ common/
COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini .

# Flat `src/` + `common/` layout; run via PYTHONPATH (same as api-gateway).
ENV PYTHONPATH=/app
RUN pip install --no-cache-dir .

USER appuser

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
