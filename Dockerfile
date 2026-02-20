FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

RUN apt-get update && apt-get install -y ffmpeg curl ca-certificates && rm -rf /var/lib/apt/lists/*
RUN curl -LsSf https://github.com/octeep/wireproxy/releases/latest/download/wireproxy_linux_amd64.tar.gz | tar -xz -C /usr/local/bin/

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv pip install --system .
COPY . .

CMD echo "$WGCF_CONF_CONTENT" > wgcf-profile.conf && \
    echo "$WIREPROXY_CONF_CONTENT" > wireproxy.conf && \
    wireproxy -c wireproxy.conf & \
    sleep 5 && \
    python main.py
