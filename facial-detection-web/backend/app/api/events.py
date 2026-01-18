from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.services.event_service import EventService

router = APIRouter(prefix="/events", tags=["events"])


class EventResponse(BaseModel):
    id: str
    user_id: str
    session_id: str
    event_type: str
    ear: Optional[float]
    mar: Optional[float]
    emotion: Optional[str]
    confidence: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class SessionStatsResponse(BaseModel):
    session_id: str
    drowsy_count: int
    yawn_count: int
    total_events: int


class UserStatsResponse(BaseModel):
    user_id: str
    period_days: int
    daily_stats: dict


@router.get("/session/{user_id}/{session_id}", response_model=SessionStatsResponse)
async def get_session_stats(
    user_id: UUID,
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    service = EventService(db)
    stats = await service.get_session_stats(user_id, session_id)
    return stats


@router.get("/user/{user_id}", response_model=UserStatsResponse)
async def get_user_stats(
    user_id: UUID,
    days: int = Query(default=7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    service = EventService(db)
    stats = await service.get_user_stats(user_id, days)
    return stats


@router.get("/recent/{user_id}", response_model=list[EventResponse])
async def get_recent_events(
    user_id: UUID,
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    service = EventService(db)
    events = await service.get_recent_events(user_id, limit)
    return [
        EventResponse(
            id=str(e.id),
            user_id=str(e.user_id),
            session_id=str(e.session_id),
            event_type=e.event_type,
            ear=e.ear,
            mar=e.mar,
            emotion=e.emotion,
            confidence=e.confidence,
            created_at=e.created_at,
        )
        for e in events
    ]
