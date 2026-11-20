FROM python:3.11-slim

ENV NODE_OPTIONS="--max-old-space-size=350"
ENV PATH="/usr/local/bin:${PATH}"
ENV PORT=8080

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates git tar gzip ffmpeg \
    && curl -fsSL "https://nodejs.org" -o /tmp/node.tgz \
    && tar -xzf /tmp/node.tgz -C /usr/local --strip-components=1 \
    && rm -f /tmp/node.tgz \
    && npm install -g openclaw@latest \
    && pip install --no-cache-dir flask requests auto-editor yt-dlp \
    && node -v && openclaw --version \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY start_247.py /app/start_247.py

EXPOSE 8080
CMD ["python3", "/app/start_247.py"]
