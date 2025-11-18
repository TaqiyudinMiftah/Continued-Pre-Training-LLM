# --- UBAH BARIS INI (Gunakan image versi Python) ---
FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

WORKDIR /app

# Install Task (Go-Task)
RUN sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d -b /usr/local/bin

COPY requirements.txt .

# Sekarang pip pasti ada dan bisa jalan
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p data/page data/url data/results

CMD ["task", "run"]