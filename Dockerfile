FROM python:3.9-slim

# Instalar dependencias del sistema
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
    fonts-liberation \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Instalar una versión específica de Google Chrome (134.0.6052.0)
RUN wget -q -O /tmp/chrome.deb https://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_134.0.6052.0-1_amd64.deb \
    && apt-get update \
    && apt install -y /tmp/chrome.deb \
    && rm /tmp/chrome.deb \
    && rm -rf /var/lib/apt/lists/*

# Comprobar la versión de Chrome instalada
RUN google-chrome --version

# Instalar ChromeDriver exactamente compatible con Chrome 134.0.6052.0
RUN mkdir -p /tmp/chromedriver \
    && cd /tmp/chromedriver \
    && wget -q --no-verbose -O chromedriver.zip "https://storage.googleapis.com/chrome-for-testing-public/134.0.6052.0/linux64/chromedriver-linux64.zip" \
    && unzip chromedriver.zip \
    && mv chromedriver-linux64/chromedriver /usr/local/bin/chromedriver \
    && chmod +x /usr/local/bin/chromedriver \
    && rm -rf /tmp/chromedriver \
    && chromedriver --version

# Crear directorio de trabajo
WORKDIR /app

# Establecer como entorno Docker
ENV DOCKER_ENV=true
ENV PORT=8080
ENV CHROMEDRIVER_PATH=/usr/local/bin/chromedriver
ENV CHROME_VERSION=134.0.6052.0

# Copiar requirements.txt primero para aprovechar la caché
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Crear directorios de datos y logs
RUN mkdir -p data logs && chmod -R 777 data logs

# Verificación final de configuración
RUN echo "Verificando configuración..." \
    && echo "Chrome: $(google-chrome --version)" \
    && echo "ChromeDriver: $(chromedriver --version)" \
    && echo "Python: $(python --version)"

# Exponer puerto
EXPOSE 8080

# Ejecutar con Gunicorn
CMD gunicorn --bind 0.0.0.0:$PORT 'app.api:create_app()' --log-file=-