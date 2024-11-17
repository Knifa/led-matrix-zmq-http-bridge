import asyncio
import logging
import struct
from enum import IntEnum

import zmq
import zmq.asyncio

logger = logging.getLogger(__name__)


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
        self._addr = addr
        self._lock = asyncio.Lock()

        self._context = zmq.asyncio.Context()
        self._context.sndtimeo = 1000
        self._context.rcvtimeo = 1000
        self._context.linger = 0

        self._socket: zmq.Socket = self._init_socket(self._context, addr)

    async def set_brightness(self, brightness: int) -> None:
        await self._send_message(get_brightness_message(brightness))

    async def set_temperature(self, temperature: int) -> None:
        await self._send_message(get_temperature_message(temperature))

    async def _send_message(self, message: bytes) -> None:
        async with self._lock:
            assert self._socket

            try:
                await self._socket.send(message)
                await self._socket.recv()
            except zmq.error.Again as e:
                logger.error("Unable to send control message: %s", e)
                self._reset_socket()

    def _init_socket(self, context: zmq.Context, addr: str) -> zmq.Socket:
        socket = context.socket(zmq.REQ)
        socket.connect(addr)
        return socket

    def _reset_socket(self) -> None:
        if self._socket:
            self._socket.close()
            del self._socket

        self._socket = self._init_socket(self._context, self._addr)
