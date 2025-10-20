# Use uma imagem base do Python
FROM python:3.9-slim

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar os arquivos do seu projeto para dentro do container
COPY . /app
WORKDIR /app

# Define que o que subir aqui é para produção
ENV FLASK_ENV=production

# Instalar pacotes Python necessários
RUN pip install --no-cache-dir -r requirements.txt

# Rodar o flask
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]