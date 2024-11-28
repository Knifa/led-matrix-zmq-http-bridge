FROM alpine:latest

RUN apk add --no-cache \
    iproute2 \
    py3-pip \
    python3

RUN mkdir -p /opt/led-matrix-zmq-control-api
WORKDIR /opt/led-matrix-zmq-control-api

RUN python -m venv .venv && \
    source .venv/bin/activate && \
    pip install --upgrade uv

RUN apk del py3-pip

ENV PATH="/opt/led-matrix-zmq-control-api/.venv/bin:$PATH"

COPY pyproject.toml uv.lock ./
RUN uv sync

COPY lmz ./lmz

CMD ["python", "-m", "lmz"]
