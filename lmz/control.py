import abc
import dataclasses
import enum
import logging
import struct
from typing import Any, Generic, Iterator, Self, Type, TypeVar

import zmq
import zmq.asyncio

logger = logging.getLogger(__name__)


class MessageError(Exception):
    pass


class MessageId(enum.IntEnum):
    NULL_REPLY = 0

    GET_BRIGHTNESS_REQUEST = enum.auto()
    GET_BRIGHTNESS_REPLY = enum.auto()
    SET_BRIGHTNESS_REQUEST = enum.auto()

    GET_TEMPERATURE_REQUEST = enum.auto()
    GET_TEMPERATURE_REPLY = enum.auto()
    SET_TEMPERATURE_REQUEST = enum.auto()


@dataclasses.dataclass
class Args(abc.ABC):
    @staticmethod
    @abc.abstractmethod
    def pack_format() -> str:
        raise NotImplementedError

    def __iter__(self) -> Iterator:
        for field in dataclasses.fields(self):
            yield getattr(self, field.name)


@dataclasses.dataclass
class NullArgs(Args):
    @staticmethod
    def pack_format() -> str:
        return "x"


@dataclasses.dataclass
class BrightnessArgs(Args):
    brightness: int

    @staticmethod
    def pack_format() -> str:
        return "B"


@dataclasses.dataclass
class TemperatureArgs(Args):
    temperature: int

    @staticmethod
    def pack_format() -> str:
        return "H"


ArgsT = TypeVar("ArgsT", bound=Args)


class Message(Generic[ArgsT], abc.ABC):
    id_: MessageId

    args: ArgsT
    args_t: Type[ArgsT]

    def __init__(self, args: ArgsT) -> None:
        self.args = args

    def to_bytes(self) -> bytes:
        return struct.pack(f"<B{self.args_t.pack_format()}", self.id_, *self.args)

    @classmethod
    def from_bytes(cls, data: bytes) -> Self:
        id_ = data[0]
        if id_ != cls.id_:
            raise ValueError(f"Invalid message ID: {id_}")

        try:
            _, *args_tuple = struct.unpack(f"<B{cls.args_t.pack_format()}", data)
        except struct.error as e:
            raise ValueError(f"Invalid message data: {e}")

        args = cls.args_t(*args_tuple)
        return cls(args)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, self.__class__):
            return False

        return self.id_ == other.id_ and self.args == other.args


class NullReply(Message[NullArgs]):
    id_ = MessageId.NULL_REPLY
    args_t = NullArgs


class GetBrightnessRequest(Message[NullArgs]):
    id_ = MessageId.GET_BRIGHTNESS_REQUEST
    args_t = NullArgs


class GetBrightnessReply(Message[BrightnessArgs]):
    id_ = MessageId.GET_BRIGHTNESS_REPLY
    args_t = BrightnessArgs


class SetBrightnessRequest(Message[BrightnessArgs]):
    id_ = MessageId.SET_BRIGHTNESS_REQUEST
    args_t = BrightnessArgs


class GetTemperatureRequest(Message[NullArgs]):
    id_ = MessageId.GET_TEMPERATURE_REQUEST
    args_t = NullArgs


class GetTemperatureReply(Message[TemperatureArgs]):
    id_ = MessageId.GET_TEMPERATURE_REPLY
    args_t = TemperatureArgs


class SetTemperatureRequest(Message[TemperatureArgs]):
    id_ = MessageId.SET_TEMPERATURE_REQUEST
    args_t = TemperatureArgs


MessageT = TypeVar("MessageT", bound=Message)


class LmzControl:
    def __init__(self, addr: str) -> None:
        self._addr = addr

        self._zmq_context = zmq.asyncio.Context()
        self._zmq_context.sndtimeo = 1000
        self._zmq_context.rcvtimeo = 1000
        self._zmq_context.linger = 0
        self._zmq_socket: zmq.asyncio.Socket | None = None

    async def __aenter__(self) -> Self:
        self._reset_socket()
        return self

    async def __aexit__(self, *args) -> None:
        if self._zmq_socket:
            self._zmq_socket.close()
            self._zmq_socket = None

    async def get_brightness(self) -> int:
        reply = await self._send_recv(
            GetBrightnessRequest(NullArgs()),
            GetBrightnessReply,
        )

        return reply.args.brightness

    async def set_brightness(self, brightness: int) -> None:
        await self._send_recv(
            SetBrightnessRequest(BrightnessArgs(brightness)),
            NullReply,
        )

    async def get_temperature(self) -> int:
        reply = await self._send_recv(
            GetTemperatureRequest(NullArgs()),
            GetTemperatureReply,
        )

        return reply.args.temperature

    async def set_temperature(self, temperature: int) -> None:
        await self._send_recv(
            SetTemperatureRequest(TemperatureArgs(temperature)),
            NullReply,
        )

    def _reset_socket(self) -> None:
        if self._zmq_socket:
            self._zmq_socket.close()

        self._zmq_socket = self._zmq_context.socket(zmq.REQ)
        self._zmq_socket.connect(self._addr)

    async def _send_recv(
        self,
        req_msg: MessageT,
        rep_type: Type[MessageT],
    ) -> MessageT:
        assert self._zmq_socket
        req_bytes = req_msg.to_bytes()

        try:
            await self._zmq_socket.send(req_bytes)
        except zmq.error.Again as e:
            self._reset_socket()
            raise MessageError("Timeout") from e

        try:
            rep_bytes = await self._zmq_socket.recv()
            return rep_type.from_bytes(rep_bytes)
        except zmq.error.Again as e:
            self._reset_socket()
            raise MessageError("Timeout") from e
        except ValueError as e:
            raise MessageError("Invalid reply") from e
