FROM python:3.12-slim

# Instala dependências do sistema e Playwright
RUN apt-get update && apt-get install -y \
    wget gnupg curl unzip fonts-liberation libnss3 libatk-bridge2.0-0 \
    libxss1 libasound2 libgbm1 libgtk-3-0 libxshmfence-dev

# Define diretório da aplicação
WORKDIR /app

# Copia requirements.txt e instala venv + dependências
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --break-system-packages -r requirements.txt

# Instala os navegadores do playwright (modo Python)
RUN python3 -m playwright install

# Copia o restante da aplicação
COPY . .

# Executa a aplicação
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
