import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import api_router
from app.core.config import settings
from app.core.database import Base, engine
from app.core.security import decode_token
from app.services.events import triage_hub
import app.models  # noqa: F401 ensures model metadata is loaded

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s medikiosk %(message)s")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="MediKiosk API", version="1.0.0", description="AI-assisted multilingual clinical intake. Clinical decisions remain with doctors.", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[item.strip() for item in settings.cors_origins.split(",")], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(api_router)


@app.get("/health", tags=["System"])
def health() -> dict:
    return {"status": "healthy", "service": "medikiosk-backend"}


@app.get("/health/detailed", tags=["System"])
def detailed_health() -> dict:
    checks = {"backend": "healthy", "database": "healthy", "redis": "configured", "storage": "local mock storage ready"}
    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
    except Exception:
        checks["database"] = "unhealthy"
    return {"status": "healthy" if checks["database"] == "healthy" else "degraded", "checks": checks}


@app.websocket("/ws/triage")
async def triage_events(socket: WebSocket) -> None:
    token = socket.query_params.get("token", "")
    try:
        claims = decode_token(token)
        if claims.get("role") not in {"TRIAGE_STAFF", "ADMIN"}:
            await socket.close(code=4403)
            return
    except Exception:
        await socket.close(code=4401)
        return
    await triage_hub.connect(socket)
    try:
        while True:
            await socket.receive_text()
    except WebSocketDisconnect:
        triage_hub.disconnect(socket)
