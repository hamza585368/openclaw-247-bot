FROM python:3.11-slim

RUN apt-get update && apt-get install -y curl git ffmpeg && \
    curl -fsSL https://nodejs.org -o /tmp/node.tgz && \
    tar -xzf /tmp/node.tgz -C /usr/local --strip-components=1 && \
    rm -f /tmp/node.tgz && \
    npm install -g openclaw@latest && \
    pip install --no-cache-dir flask requests kaggle yt-dlp auto-editor && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY start_247.py /app/start_247.py

ENV PORT=8080
EXPOSE 8080

CMD ["python3", "/app/start_247.py"]
