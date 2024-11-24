# led-matrix-zmq-control-api

A simple HTTP JSON API for sending control messages to [led-matrix-zmq-server](https://github.com/knifa/led-matrix-zmq-server).

Zeroconf is used to publish the API endpoint as a service so it can be discovered by e.g. Home Assistant.

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

# {"statuc": "ok"}
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

# {"statuc": "ok"}
```

## Zeroconf

The API is published as a Zeroconf service under the type `_lmz-control-api._tcp.local.`.
