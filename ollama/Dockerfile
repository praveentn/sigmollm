FROM ollama/ollama:latest

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Models are stored in the Railway volume mounted at /models
ENV OLLAMA_MODELS=/models
ENV DEFAULT_MODEL=gemma4:e2b

EXPOSE 11434

ENTRYPOINT ["/entrypoint.sh"]
