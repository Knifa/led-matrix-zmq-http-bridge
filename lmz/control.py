import asyncio
import struct
from enum import IntEnum

import zmq
import zmq.asyncio


class MessageType(IntEnum):
    BRIGHTNESS = 0
    TEMPERATURE = 1


def get_brightness_message(brightness: int) -> bytes:
    return _pack_message(MessageType.BRIGHTNESS, "B", brightness)


def get_temperature_message(temperature: int) -> bytes:
    return _pack_message(MessageType.TEMPERATURE, "H", temperature)


def _pack_message(message_type: MessageType, pack_format: str, *args) -> bytes:
    return struct.pack(f"<B{pack_format}", message_type, *args)


class LmzControl:
    def __init__(self, addr: str) -> None:
        self._lock = asyncio.Lock()

        self._context = zmq.asyncio.Context()
        self._socket = self._context.socket(zmq.REQ)
        self._socket.rcvtimeo = 1000
        self._socket.connect(addr)

    async def set_brightness(self, brightness: int) -> None:
        await self._send_message(get_brightness_message(brightness))

    async def set_temperature(self, temperature: int) -> None:
        await self._send_message(get_temperature_message(temperature))

    async def _send_message(self, message: bytes) -> None:
        async with self._lock:
            await self._socket.send(message)
            await self._socket.recv()
