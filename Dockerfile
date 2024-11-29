FROM alpine:latest as build

ARG TARGETPLATFORM

RUN apk add --no-cache \
  py3-pip \
  python3

RUN mkdir -p /build/led-matrix-zmq-control-api
WORKDIR /build/led-matrix-zmq-control-api

RUN python -m venv .venv && \
  source .venv/bin/activate && \
  pip install --upgrade uv

ENV PATH="/build/led-matrix-zmq-control-api/.venv/bin:$PATH"

# linux/arm/v7 requires additional build dependencies.
RUN \
  if [ "$TARGETPLATFORM" = "linux/arm/v7" ]; then \
    apk add --no-cache \
      cargo \
      python3-dev \
  fi

COPY pyproject.toml uv.lock ./
RUN uv sync

FROM alpine:latest as run

RUN apk add --no-cache \
  python3

RUN mkdir -p /opt/led-matrix-zmq-control-api
COPY --from=build /build/led-matrix-zmq-control-api/.venv /opt/led-matrix-zmq-control-api/.venv

ENV PATH="/opt/led-matrix-zmq-control-api/.venv/bin:$PATH"

COPY lmz ./lmz

CMD ["python", "-m", "lmz"]
