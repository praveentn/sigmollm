#!/bin/bash
set -e

MODEL="${DEFAULT_MODEL:-gemma:2b}"

echo "==> Starting Ollama serve (models dir: $OLLAMA_MODELS)"
ollama serve &
OLLAMA_PID=$!

# Wait until Ollama's HTTP API is accepting requests
echo "==> Waiting for Ollama API to be ready..."
until curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; do
    sleep 1
done
echo "==> Ollama API is ready"

# Pull model only if it's not already in the volume
if ollama list 2>/dev/null | grep -q "${MODEL}"; then
    echo "==> Model '${MODEL}' already present in /models — skipping pull"
else
    echo "==> Pulling model '${MODEL}' into /models (this may take a few minutes on first boot)..."
    ollama pull "${MODEL}"
    echo "==> Model '${MODEL}' ready"
fi

echo "==> Ollama is serving '${MODEL}' on port 11434"

# Hand control back to the serve process so the container stays alive
wait $OLLAMA_PID
