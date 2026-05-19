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

# Render usa PORT como variável de ambiente, padrão 10000
EXPOSE 10000

# Rodar com Gunicorn (melhor para produção)
# Render injeta PORT como variável de ambiente
ENV PORT=10000
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--workers", "1", "--worker-class", "sync", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "05_api_flask:app"]

