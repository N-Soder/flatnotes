from fastapi import WebSocket
from fastapi.websockets import WebSocketDisconnect
from pycrdt.websocket import WebsocketServer

# Single server instance shared across all note rooms.
# Rooms are created on demand and cleaned up when the last client disconnects.
ws_server = WebsocketServer(auto_clean_rooms=True)


class FastAPIChannel:
    """Adapts a FastAPI WebSocket to the pycrdt Channel protocol."""

    def __init__(self, websocket: WebSocket, room_name: str):
        self._ws = websocket
        self._room_name = room_name

    @property
    def path(self) -> str:
        return self._room_name

    def __aiter__(self):
        return self

    async def __anext__(self) -> bytes:
        try:
            msg = await self._ws.receive()
            if msg.get("type") == "websocket.disconnect":
                raise StopAsyncIteration
            if msg.get("bytes"):
                return msg["bytes"]
            if msg.get("text"):
                return msg["text"].encode()
            raise StopAsyncIteration
        except (WebSocketDisconnect, RuntimeError):
            raise StopAsyncIteration

    async def send(self, message: bytes) -> None:
        try:
            await self._ws.send_bytes(message)
        except (WebSocketDisconnect, RuntimeError):
            pass

    async def recv(self) -> bytes:
        return await self.__anext__()
