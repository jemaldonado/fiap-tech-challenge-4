FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

COPY 05_api_flask.py .
COPY swagger.yaml .
COPY data/ ./data/
COPY models/ ./models/

EXPOSE 10000

ENV PORT=10000
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--workers", "1", "--worker-class", "sync", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "05_api_flask:app"]
