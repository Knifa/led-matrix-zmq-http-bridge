FROM alpine:latest AS build

RUN apk add --no-cache \
  py3-pip \
  python3

RUN mkdir -p /opt/lmz/
WORKDIR /opt/lmz/

RUN python -m venv .venv-build && \
  source .venv-build/bin/activate && \
  pip install --upgrade uv

ENV PATH="/opt/lmz/.venv-build/bin:$PATH"

RUN uv venv

ENV PATH="/opt/lmz/.venv/bin:$PATH"

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev


FROM alpine:latest AS run

RUN apk add --no-cache \
  iproute2 \
  python3

RUN mkdir -p /opt/lmz/
COPY --from=build /opt/lmz/.venv /opt/lmz/.venv

ENV PATH="/opt/lmz/.venv/bin:$PATH"

COPY lmz ./lmz

CMD ["python", "-m", "lmz"]
