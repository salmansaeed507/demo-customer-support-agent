from fastapi import FastAPI

from .api.internal import router as internal_router
from .api.routes import router
from .config import settings

app = FastAPI(
    title="Customer Support Agent",
    version="0.1.0",
)
app.include_router(router)
app.include_router(internal_router)


@app.get("/health")
def health():
    return {"status": "ok", "service": settings.service_name}
