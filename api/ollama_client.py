import time

import httpx
from fastapi import HTTPException

from config import settings

_TIMEOUT = httpx.Timeout(connect=10.0, read=180.0, write=30.0, pool=10.0)


async def chat(model: str, messages: list[dict], options: dict | None = None) -> dict:
    payload: dict = {"model": model, "messages": messages, "stream": False}
    if options:
        payload["options"] = options

    t0 = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.post(f"{settings.ollama_url}/api/chat", json=payload)
            r.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Ollama error {e.response.status_code}: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Ollama unreachable: {e}")

    data = r.json()
    data["latency_ms"] = int((time.monotonic() - t0) * 1000)
    return data


async def generate(model: str, prompt: str, options: dict | None = None) -> dict:
    payload: dict = {"model": model, "prompt": prompt, "stream": False}
    if options:
        payload["options"] = options

    t0 = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            r = await client.post(f"{settings.ollama_url}/api/generate", json=payload)
            r.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Ollama error {e.response.status_code}: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Ollama unreachable: {e}")

    data = r.json()
    data["latency_ms"] = int((time.monotonic() - t0) * 1000)
    return data


async def list_models() -> list[dict]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{settings.ollama_url}/api/tags")
            r.raise_for_status()
        return r.json().get("models", [])
    except Exception:
        return []


async def pull_model(name: str) -> None:
    async with httpx.AsyncClient(timeout=httpx.Timeout(600.0)) as client:
        r = await client.post(f"{settings.ollama_url}/api/pull", json={"name": name, "stream": False})
        r.raise_for_status()


async def delete_model(name: str) -> None:
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.request("DELETE", f"{settings.ollama_url}/api/delete", json={"name": name})
        r.raise_for_status()
