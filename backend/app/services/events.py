import asyncio
from fastapi import WebSocket


class TriageEventHub:
    def __init__(self) -> None:
        self.connections: set[WebSocket] = set()

    async def connect(self, socket: WebSocket) -> None:
        await socket.accept()
        self.connections.add(socket)

    def disconnect(self, socket: WebSocket) -> None:
        self.connections.discard(socket)

    async def broadcast(self, event: dict) -> None:
        stale: list[WebSocket] = []
        for socket in self.connections:
            try:
                await socket.send_json(event)
            except Exception:
                stale.append(socket)
        for socket in stale:
            self.disconnect(socket)


triage_hub = TriageEventHub()
