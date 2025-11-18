# Gunakan image official Playwright agar browser & dependency sistem sudah terinstall
FROM mcr.microsoft.com/playwright:v1.48.0-jammy

# Set working directory
WORKDIR /app

# Install Task (Go-Task) untuk menjalankan Taskfile.yml
# Jika Taskfile.yml Anda formatnya standard, kita butuh tool 'task'
RUN sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d -b /usr/local/bin

# Copy requirements dan install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy seluruh source code ke dalam image
COPY . .

# Buat folder data untuk output
RUN mkdir -p data/page data/url data/results

# Command default saat container jalan
CMD ["task", "run"]