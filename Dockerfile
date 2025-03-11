FROM python:3.9-slim

# Instalar dependencias básicas del sistema
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Establecer como entorno Docker
ENV DOCKER_ENV=true
ENV PORT=8080

# Copiar requirements.txt primero para aprovechar la caché
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Crear directorios de datos y logs
RUN mkdir -p data logs data/debug && chmod -R 777 data logs data/debug

# Verificación final de configuración
RUN echo "Verificando configuración..." \
    && echo "Python: $(python --version)" \
    && echo "Requests: $(pip show requests | grep Version)" \
    && echo "BeautifulSoup4: $(pip show beautifulsoup4 | grep Version)"

# Exponer puerto
EXPOSE 8080

# Ejecutar con Gunicorn
CMD gunicorn --bind 0.0.0.0:$PORT 'app.api:create_app()' --log-file=-