from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from pydantic import BaseModel, Field

from .control import LmzControl
from .settings import settings
from .zeroconf import lmz_zeroconf


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    if not settings.zeroconf_enabled:
        yield
        return

    async with lmz_zeroconf(
        name=settings.zeroconf_name,
        address=settings.zeroconf_ip,
        port=settings.api_port,
    ):
        yield


app = FastAPI(lifespan=lifespan)
control = LmzControl(settings.control_endpoint)

OK_STATUS = {"status": "ok"}


class TemperatureRequest(BaseModel):
    temperature: int = Field(description="Color temperature (Kelvin)", ge=2000, le=6500)


class BrightnessRequest(BaseModel):
    brightness: int = Field(description="Brightness level (%)", ge=0, le=100)


@app.post("/temperature")
async def set_temperature(request: TemperatureRequest):
    await control.set_temperature(request.temperature)
    return OK_STATUS


@app.post("/brightness")
async def set_brightness(request: BrightnessRequest):
    await control.set_brightness(request.brightness)
    return OK_STATUS
