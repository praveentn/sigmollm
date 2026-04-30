from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from config import settings
from db.database import engine
from db.models import Base
from routes.admin import router as admin_router
from routes.chat import router as chat_router
from routes.generate import router as generate_router
from routes.llm_models import router as models_router
from ui.router import router as ui_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.get(f"{settings.ollama_url}/api/tags")
        print(f"✓ Connected to Ollama at {settings.ollama_url}")
    except Exception as e:
        print(f"⚠ Ollama not reachable at {settings.ollama_url}: {e}")

    yield


app = FastAPI(
    title="SigmoLLM API",
    description="LLM-as-a-Service powered by Ollama",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,
    lifespan=lifespan,
)

app.include_router(chat_router, prefix="/api", tags=["LLM"])
app.include_router(generate_router, prefix="/api", tags=["LLM"])
app.include_router(models_router, prefix="/api", tags=["LLM"])
app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])
app.include_router(ui_router, prefix="/ui", tags=["UI"])


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/ui/")


@app.get("/health", tags=["Health"])
async def health():
    error_detail = None
    models = []
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{settings.ollama_url}/api/tags")
            r.raise_for_status()
            ollama_ok = True
            models = [m.get("name") for m in r.json().get("models", [])]
    except Exception as e:
        ollama_ok = False
        error_detail = str(e)

    return {
        "status": "ok",
        "ollama": "reachable" if ollama_ok else "unreachable",
        "ollama_url": settings.ollama_url,
        "default_model": settings.default_model,
        "loaded_models": models,
        **({"ollama_error": error_detail} if error_detail else {}),
    }
