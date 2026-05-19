# Imagem Python slim (reduz tamanho)
FROM python:3.11-slim

WORKDIR /app

# Instala apenas dependências necessárias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# Copia código da aplicação
COPY 05_api_flask.py .
COPY swagger.yaml .

# Copia dados e modelos (pré-treinados)
COPY data/ ./data/
COPY models/ ./models/

# Render usa porta configurável, padrão 8000
EXPOSE 8000

# Gunicorn é mais estável que Flask dev server para produção
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--worker-class", "sync", "--timeout", "120", "05_api_flask:app"]

