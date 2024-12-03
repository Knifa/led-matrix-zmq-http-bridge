# led-matrix-zmq-http-bridge

This is an HTTP bridge for [led-matrix-zmq-server](https://github.com/knifa/led-matrix-zmq-server). You can set brightness, color temperature, etc. via a JSON API.

Zeroconf is used to publish the bridge as a service so it can be discovered by e.g. Home Assistant.

## Docker

A [Docker image](https://github.com/knifa/led-matrix-zmq-http-bridge/pkgs/container/led-matrix-zmq-http-bridge) is available for `amd64` and `arm64`.

The container must be run with `--network host` for Zeroconf to work.

```shell
docker run \
  --rm \
  --network host \
  -e "LMZ_CONTROL_ENDPOINT=ipc:///run/lmz/control.sock" \
  -e "LMZ_ZEROCONF_NAME=My Matrix" \
  -v /run/lmz:/run/lmz \
  ghcr.io/knifa/led-matrix-zmq-http-bridge:latest
```

## Usage

See [lmz/settings.py](lmz/settings.py) for possible environment variables.

```bash
uv sync
uv run python -m lmz
```

### GET `/brightness`

Get the current brightness of the display (0-100%).

```bash
curl http://localhost:4200/brightness

# {"brightness": 50}
```

### POST `/brightness`

Set the brightness of the display (0-100%)

```bash
curl \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"brightness": 50}' \
    http://localhost:4200/brightness

# {"status": "ok"}
```

### GET `/configuration`

Get the configuration of the display, i.e., resolution.

```bash
curl http://localhost:4200/configuration

# {"width": 64, "height": 32}
```

### GET `/temperature`
```bash
curl http://localhost:4200/temperature

# {"temperature": 2500}
```

###  POST `/temperature`

Set the color temperature of the display (2000-6500K).

```bash
curl \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"temperature": 2500}' \
    http://localhost:4200/temperature

# {"status": "ok"}
```

## Zeroconf

The bridge is published as a Zeroconf service under the type `_lmz-http-bridge._tcp.local.`.
