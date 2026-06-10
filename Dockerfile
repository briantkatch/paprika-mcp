# syntax=docker/dockerfile:1

# ---- Builder stage ----
# Installs paprika-mcp and its dependencies into an isolated virtualenv.
# git is required because paprika-recipes is pulled from a git tag.
FROM python:3.13-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# Build into a self-contained venv so we can copy just that into the runtime.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --upgrade pip \
    && pip install .

# ---- Runtime stage ----
# Slim image with only the venv; no build tooling or git.
FROM python:3.13-slim AS runtime

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    HOST=0.0.0.0 \
    PORT=8080

# Run as a non-root user.
RUN useradd --create-home --uid 10001 paprika

COPY --from=builder /opt/venv /opt/venv
COPY docker-healthcheck.py /opt/healthcheck.py

USER paprika
WORKDIR /home/paprika

EXPOSE 8080

# Probe the plain-HTTP /healthz route (the /mcp endpoint needs a session handshake).
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD ["python", "/opt/healthcheck.py"]

# Serve MCP over Streamable HTTP; clients connect to http://<host>:8080/mcp.
ENTRYPOINT ["paprika-mcp-web"]
