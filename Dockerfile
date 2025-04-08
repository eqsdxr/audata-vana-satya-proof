FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PATH=".venv/bin:$PATH"

COPY uv.lock pyproject.toml /app/

RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-install-project --no-dev

COPY . /app/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# Make sure fpcalc required by acoust id library is executable
RUN chmod +x /app/fpcalc && \
    ln -s /app/fpcalc /usr/local/bin/fpcalc

# Install chromaprint required by acoustid library
RUN apt-get update && apt-get install -y \
    libchromaprint-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /sealed && chmod 777 /sealed

CMD [".venv/bin/python3", "-m", "audata_proof"]
