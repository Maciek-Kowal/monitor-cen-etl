# Baza: Obraz z środowiskiem Playwright
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

ENV DEBIAN_FRONTEND=noninteractive

# Instalacja sterowników dla pyodbc
RUN apt-get update && apt-get install -y curl apt-transport-https gnupg2 \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/ubuntu/22.04/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 unixodbc-dev

# Instalacja Google Chrome
RUN curl -fSsL https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor | tee /usr/share/keyrings/google-chrome.gpg > /dev/null \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" | tee /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    xvfb \
    libnss3 \
    libgconf-2-4 \
    libxss1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app

# Instalacja bibliotek
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopia reszty
COPY . .
RUN sed -i 's/\r$//' run_all.sh
# Nadanie uprawnień
RUN chmod +x run_all.sh

CMD ["./run_all.sh"]