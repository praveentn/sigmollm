FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    zstd \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://ollama.com/install.sh | sh

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV OLLAMA_MODELS=/models
ENV OLLAMA_HOST=0.0.0.0
ENV OLLAMA_URL=http://localhost:11434

EXPOSE 8000

RUN chmod +x /app/start.sh
CMD ["/app/start.sh"]
