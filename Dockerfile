FROM python:3.11-slim
ENV PORT=8080
RUN pip install --no-cache-dir flask requests
WORKDIR /app
COPY start_247.py /app/start_247.py
EXPOSE 8080
CMD ["python3", "/app/start_247.py"]
