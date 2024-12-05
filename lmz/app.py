import logging
from contextlib import AsyncExitStack, asynccontextmanager
from typing import Annotated, AsyncGenerator

from fastapi import APIRouter, FastAPI, File, Request, status
from fastapi.responses import JSONResponse
from led_matrix_zmq import LmzControlAsync, LmzFrameAsync, LmzMessageError
from pydantic import BaseModel, Field

from .settings import settings
from .zeroconf import lmz_zeroconf

logger = logging.getLogger(__name__)

lmz_control: LmzControlAsync | None = None
lmz_frame: LmzFrameAsync | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    async with AsyncExitStack() as stack:
        if settings.control_enabled:
            global lmz_control
            lmz_control = LmzControlAsync(settings.control_endpoint)
            await stack.enter_async_context(lmz_control)

        if settings.frame_enabled:
            global lmz_frame
            lmz_frame = LmzFrameAsync(settings.frame_endpoint)
            await stack.enter_async_context(lmz_frame)

        if settings.zeroconf_enabled:
            await stack.enter_async_context(
                lmz_zeroconf(
                    name=settings.zeroconf_name,
                    address=settings.zeroconf_ip,
                    port=settings.api_port,
                )
            )

        yield


app = FastAPI(lifespan=lifespan)
control_api = APIRouter()
frame_api = APIRouter()

OK_RESPONSE = JSONResponse(content={"status": "ok"})


@app.exception_handler(LmzMessageError)
async def app_message_error_handler(
    request: Request, exc: LmzMessageError
) -> JSONResponse:
    return JSONResponse(
        content={"status": "error", "error": str(exc)},
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    )


@app.get("/healthcheck")
async def healthcheck() -> JSONResponse:
    return OK_RESPONSE


class Brightness(BaseModel):
    brightness: int = Field(description="Brightness", ge=0, le=255)


class Configuration(BaseModel):
    width: int = Field(description="Width (pixels)", ge=1, le=65535)
    height: int = Field(description="Height (pixels)", ge=1, le=65535)


class Temperature(BaseModel):
    temperature: int = Field(description="Color temperature (Kelvin)", ge=2000, le=6500)


@control_api.get("/brightness")
async def get_brightness() -> Brightness:
    assert lmz_control is not None
    return Brightness(brightness=await lmz_control.get_brightness())


@control_api.post("/brightness")
async def set_brightness(request: Brightness) -> JSONResponse:
    assert lmz_control is not None
    await lmz_control.set_brightness(request.brightness)
    return OK_RESPONSE


@control_api.get("/configuration")
async def get_configuration() -> Configuration:
    assert lmz_control is not None
    config = await lmz_control.get_configuration()
    return Configuration(width=config.width, height=config.height)


@control_api.get("/temperature")
async def get_temperature() -> Temperature:
    assert lmz_control is not None
    return Temperature(temperature=await lmz_control.get_temperature())


@control_api.post("/temperature")
async def set_temperature(request: Temperature) -> JSONResponse:
    assert lmz_control is not None
    await lmz_control.set_temperature(request.temperature)
    return OK_RESPONSE


@frame_api.post("/frame")
async def send_frame(frame: Annotated[bytes, File()]) -> JSONResponse:
    assert lmz_frame is not None
    await lmz_frame.send(frame)
    return OK_RESPONSE


if settings.control_enabled:
    app.include_router(control_api)

if settings.frame_enabled:
    app.include_router(frame_api)
