import asyncio
import json
import logging
import socket
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from zeroconf.asyncio import AsyncServiceInfo, AsyncZeroconf

SERVICE_TYPE = "_lmz-control-api._tcp.local."

logger = logging.getLogger(__name__)


async def get_default_route_srcip() -> str:
    """
    Get the IP address of the default route.

    Uses `ip route` to get the default route and then extracts the preferred source address.
    """
    try:
        proc = await asyncio.create_subprocess_shell(
            "ip -j -4 route",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, _ = await proc.communicate()
        routes = json.loads(stdout)
    except Exception as e:
        raise RuntimeError("Failed to call and parse routes from ip command: " + str(e))

    try:
        default_route = next(route for route in routes if route["dst"] == "default")
        return default_route["prefsrc"]  # type: ignore
    except StopIteration:
        raise RuntimeError("No default route found")
    except KeyError:
        raise RuntimeError("Default route has no preferred source")


@asynccontextmanager
async def lmz_zeroconf(
    name: str | None = None,
    address: str | None = None,
    port: int = 8000,
) -> AsyncGenerator[None, None]:
    zeroconf = AsyncZeroconf()

    hostname = socket.gethostname()
    name = name or hostname

    try:
        address = address or await get_default_route_srcip()
    except RuntimeError as e:
        logger.warning(
            "Failed to get IP address: %s."
            " Zeroconf will be disabled. Maybe try set LMZ_ZEROCONF_IP?",
            e,
        )
        yield
        return

    service_info = AsyncServiceInfo(
        addresses=[socket.inet_aton(address)],
        name=f"{name}.{SERVICE_TYPE}",
        port=port,
        server=f"{hostname}.local",
        type_=SERVICE_TYPE,
    )

    logger.info(
        "Registering zeroconf service [name=%s, address=%s, port=%d].",
        name,
        address,
        port,
    )

    try:
        await zeroconf.async_register_service(service_info)
        yield
    finally:
        await zeroconf.async_close()
