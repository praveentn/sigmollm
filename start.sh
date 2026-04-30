#!/bin/bash
set -e

MODEL="${DEFAULT_MODEL:-gemma:2b}"

echo "==> Starting Ollama..."
ollama serve &

until curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; do
    sleep 1
done
echo "==> Ollama ready"

if ollama list | grep -q "$MODEL"; then
    echo "==> Model $MODEL already present, skipping pull"
else
    echo "==> Pulling $MODEL (first boot, may take a few minutes)..."
    ollama pull "$MODEL"
    echo "==> Done"
fi

echo "==> Starting FastAPI on port ${PORT:-8000}..."
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
