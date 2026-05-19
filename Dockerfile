# Imagem Python slim (reduz tamanho)
FROM python:3.11-slim

WORKDIR /app

# Instala apenas dependÃªncias necessÃ¡rias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# Copia cÃ³digo da aplicaÃ§Ã£o
COPY 05_api_flask.py .

# Copia dados e modelos (prÃ©-treinados)
COPY data/ ./data/
COPY models/ ./models/

# Render usa PORT como variÃ¡vel de ambiente, padrÃ£o 10000
EXPOSE 10000

# Rodar com Gunicorn (melhor para produÃ§Ã£o)
# Render injeta PORT como variÃ¡vel de ambiente
ENV PORT=10000
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--workers", "1", "--worker-class", "sync", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "05_api_flask:app"]


