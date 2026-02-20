FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN curl -LsSf https://github.com/octeep/wireproxy/releases/latest/download/wireproxy_linux_amd64.tar.gz | tar -xz -C /usr/local/bin/

RUN curl -LsSf https://astral.sh/uv/install.sh | sh

ENV PATH="/root/.local/bin:$PATH"

COPY pyproject.toml .

# If you have a lockfile, copy it too:
COPY uv.lock .

RUN uv pip install --system .

COPY . .

CMD wireproxy -c wireproxy.conf & sleep 5 && python main.py
