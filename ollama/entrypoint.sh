#!/bin/bash
set -e

export OLLAMA_MODELS="${OLLAMA_MODELS:-/models}"
MODEL="${DEFAULT_MODEL:-gemma4:e2b}"

echo "Starting Ollama (models dir: $OLLAMA_MODELS)…"
ollama serve &
OLLAMA_PID=$!

# Wait until Ollama is ready
until curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; do
  sleep 1
done
echo "Ollama ready"

# Pull model only if not already present
if ollama list 2>/dev/null | grep -q "^${MODEL}"; then
  echo "Model ${MODEL} already present — skipping pull"
else
  echo "Pulling model: ${MODEL}"
  ollama pull "${MODEL}"
  echo "Model ${MODEL} pulled successfully"
fi

wait $OLLAMA_PID
