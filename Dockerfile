FROM node:26-bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV NODE_OPTIONS="--max-old-space-size=350"
ENV PORT=8080

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip git ca-certificates ffmpeg \
    && npm install -g openclaw@latest \
    && pip3 install --no-cache-dir --break-system-packages flask requests auto-editor yt-dlp \
    && node -v && openclaw --version \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY start_247.py /app/start_247.py

EXPOSE 8080
CMD ["python3", "/app/start_247.py"]
