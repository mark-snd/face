from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict
from uuid import UUID, uuid4
import json
import logging

from app.core.database import async_session_maker
from app.services.event_service import EventService

router = APIRouter()
logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_sessions: Dict[str, UUID] = {}

    async def connect(self, websocket: WebSocket, user_id: str) -> UUID:
        await websocket.accept()
        session_id = uuid4()
        self.active_connections[user_id] = websocket
        self.user_sessions[user_id] = session_id
        logger.info(f"User {user_id} connected with session {session_id}")
        return session_id

    def disconnect(self, user_id: str):
        self.active_connections.pop(user_id, None)
        session_id = self.user_sessions.pop(user_id, None)
        logger.info(f"User {user_id} disconnected from session {session_id}")

    async def send_to_user(self, user_id: str, data: dict):
        if websocket := self.active_connections.get(user_id):
            await websocket.send_json(data)

    def get_session_id(self, user_id: str) -> UUID | None:
        return self.user_sessions.get(user_id)


manager = ConnectionManager()


@router.websocket("/ws/events/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    session_id = await manager.connect(websocket, user_id)

    # Send session info
    await websocket.send_json({
        "type": "connected",
        "session_id": str(session_id),
        "message": "Connection established",
    })

    try:
        async with async_session_maker() as db:
            event_service = EventService(db)

            while True:
                data = await websocket.receive_text()

                try:
                    message = json.loads(data)
                    message_type = message.get("type")

                    if message_type in ["DROWSY", "YAWN"]:
                        # Log detection event
                        await event_service.log_event(
                            user_id=UUID(user_id),
                            session_id=session_id,
                            event_type=message_type,
                            ear=message.get("ear"),
                            mar=message.get("mar"),
                            emotion=message.get("emotion"),
                            confidence=message.get("confidence"),
                        )
                        await db.commit()

                        # Get updated stats
                        stats = await event_service.get_session_stats(
                            user_id=UUID(user_id),
                            session_id=session_id,
                        )

                        await websocket.send_json({
                            "type": "stats",
                            "data": stats,
                        })

                    elif message_type == "ping":
                        await websocket.send_json({"type": "pong"})

                    elif message_type == "get_stats":
                        stats = await event_service.get_session_stats(
                            user_id=UUID(user_id),
                            session_id=session_id,
                        )
                        await websocket.send_json({
                            "type": "stats",
                            "data": stats,
                        })

                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from user {user_id}: {data}")
                    await websocket.send_json({
                        "type": "error",
                        "message": "Invalid JSON format",
                    })

    except WebSocketDisconnect:
        manager.disconnect(user_id)
        logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(user_id)
