FROM python:3.9-slim

# Instalar dependencias del sistema para Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    xvfb \
    libglib2.0-0 \
    libnss3 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    libgbm1 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    fonts-liberation \
    xdg-utils \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Establecer como entorno Docker
ENV DOCKER_ENV=true
ENV PORT=8080
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Copiar requirements.txt primero para aprovechar la caché
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Instalar navegadores para Playwright
RUN playwright install chromium

# Copiar el resto del código
COPY . .

# Crear directorios de datos y logs
RUN mkdir -p data logs && chmod -R 777 data logs

# Verificación final de configuración
RUN echo "Verificando configuración..." \
    && echo "Python: $(python --version)" \
    && echo "Playwright: $(python -m playwright --version 2>&1 || echo 'No disponible')"

# Exponer puerto
EXPOSE 8080

# Ejecutar con Gunicorn
CMD gunicorn --bind 0.0.0.0:$PORT 'app.api:create_app()' --log-file=-