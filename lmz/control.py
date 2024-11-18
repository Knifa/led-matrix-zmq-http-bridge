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
    QUEUE_SIZE = 10

    def __init__(self, addr: str) -> None:
        self._addr = addr

        self._zmq_context = zmq.asyncio.Context()
        self._zmq_context.sndtimeo = 1000
        self._zmq_context.rcvtimeo = 1000
        self._zmq_context.linger = 0
        self._zmq_socket: zmq.Socket | None = None

        self._queue: asyncio.Queue[bytes] = asyncio.Queue()
        self._task_handle: asyncio.Task | None = None

    async def __aenter__(self) -> "LmzControl":
        self._reset_socket()
        self._task_handle = asyncio.create_task(self._task())
        return self

    async def __aexit__(self, *args) -> None:
        if self._task_handle:
            self._task_handle.cancel()
            await self._task_handle
            self._task_handle = None

        if self._zmq_socket:
            self._zmq_socket.close()
            self._zmq_socket = None

    def set_brightness(self, brightness: int) -> None:
        self._enqueue_message(get_brightness_message(brightness))

    def set_temperature(self, temperature: int) -> None:
        self._enqueue_message(get_temperature_message(temperature))

    def _reset_socket(self) -> None:
        if self._zmq_socket:
            self._zmq_socket.close()

        self._zmq_socket = self._zmq_context.socket(zmq.REQ)
        self._zmq_socket.connect(self._addr)

    def _enqueue_message(self, message: bytes) -> None:
        if self._queue.qsize() >= self.QUEUE_SIZE:
            logger.warning("Control message queue full, dropping oldest message.")
            self._queue.get_nowait()

        self._queue.put_nowait(message)

    async def _send_message(self, message: bytes) -> None:
        assert self._zmq_socket

        try:
            await self._zmq_socket.send(message)
            await self._zmq_socket.recv()
        except zmq.error.Again as e:
            logger.error("Unable to send control message: %s", e)
            self._reset_socket()

    async def _task(self) -> None:
        try:
            while True:
                message = await self._queue.get()
                logger.debug("Sending control message: %r", message)
                await self._send_message(message)
        except asyncio.CancelledError:
            logger.info("Control task cancelled.")
