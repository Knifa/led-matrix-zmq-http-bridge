from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings for the API server, loaded from environment variables.

    You can set these by setting environment variables with the same name as
    the attribute, prefixed with `LMZ_`. For example, to set the API port, you
    would set the environment variable `LMZ_API_PORT`.
    """

    """The endpoint to send control messages to."""
    control_endpoint: str = "ipc:///run/led-matrix-zmq-control.sock"

    """The host to bind the API to."""
    api_host: str = "0.0.0.0"

    """The port to bind the API to."""
    api_port: int = 4200

    """Whether to enable zeroconf registration."""
    zeroconf_enabled: bool = True

    """The name to register with zeroconf.

    Defaults to the hostname of the machine."""
    zeroconf_name: str | None = None

    """The IP address to register with zeroconf.

    Defaults to the preferred source address of the default route, which is
    _probably_ where requests will come from."""
    zeroconf_ip: str | None = None

    class Config:
        env_prefix = "LMZ_"


settings = Settings()
