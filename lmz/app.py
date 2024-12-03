from contextlib import AsyncExitStack, asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from led_matrix_zmq import LmzControlAsync, LmzMessageError
from pydantic import BaseModel, Field

from .settings import settings
from .zeroconf import lmz_zeroconf

lmz_control = LmzControlAsync(settings.control_endpoint)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    async with AsyncExitStack() as stack:
        await stack.enter_async_context(lmz_control)

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


@app.get("/brightness")
async def get_brightness() -> Brightness:
    return Brightness(brightness=await lmz_control.get_brightness())


@app.post("/brightness")
async def set_brightness(request: Brightness) -> JSONResponse:
    await lmz_control.set_brightness(request.brightness)
    return OK_RESPONSE


@app.get("/configuration")
async def get_configuration() -> Configuration:
    config = await lmz_control.get_configuration()
    return Configuration(width=config.width, height=config.height)


@app.get("/temperature")
async def get_temperature() -> Temperature:
    return Temperature(temperature=await lmz_control.get_temperature())


@app.post("/temperature")
async def set_temperature(request: Temperature) -> JSONResponse:
    await lmz_control.set_temperature(request.temperature)
    return OK_RESPONSE
