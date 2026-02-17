FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml .

# If you use requirements.txt instead, uncomment the next line:
# COPY requirements.txt .

# Install uv to manage dependencies efficiently
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

RUN uv pip install --system .

COPY . .

CMD ["uv", "run", "main.py"]
