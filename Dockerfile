FROM ubuntu:latest as build

RUN apt-get update && \
  apt-get install -y \
    pipx \
    python3 \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.local/bin:$PATH"

RUN pipx install uv


RUN mkdir -p /build/
WORKDIR /build/

COPY pyproject.toml uv.lock ./
RUN uv sync


FROM ubuntu:latest as run

RUN apt-get update && \
  apt-get install -y \
    python3 \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/
COPY --from=build /build/.venv /opt/.venv

ENV PATH="/opt/.venv/bin:$PATH"

COPY lmz ./lmz

CMD ["python", "-m", "lmz"]
