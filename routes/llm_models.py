from fastapi import APIRouter, Depends

import ollama_client
from auth import get_api_key
from db.models import ApiKey

router = APIRouter()


@router.get("/models")
async def list_models(api_key: ApiKey = Depends(get_api_key)):
    models = await ollama_client.list_models()
    return {
        "models": [
            {
                "name": m.get("name"),
                "size": m.get("size"),
                "modified_at": m.get("modified_at"),
            }
            for m in models
        ]
    }
