from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import DetectionEvent


class EventService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_event(
        self,
        user_id: UUID,
        session_id: UUID,
        event_type: str,
        ear: Optional[float] = None,
        mar: Optional[float] = None,
        emotion: Optional[str] = None,
        confidence: Optional[float] = None,
        metadata: Optional[str] = None,
    ) -> DetectionEvent:
        event = DetectionEvent(
            user_id=user_id,
            session_id=session_id,
            event_type=event_type,
            ear=ear,
            mar=mar,
            emotion=emotion,
            confidence=confidence,
            metadata=metadata,
            created_at=datetime.utcnow(),
        )
        self.db.add(event)
        await self.db.flush()
        return event

    async def get_session_stats(
        self,
        user_id: UUID,
        session_id: UUID,
    ) -> dict:
        # Get event counts for this session
        query = select(
            DetectionEvent.event_type,
            func.count(DetectionEvent.id).label('count'),
        ).where(
            DetectionEvent.user_id == user_id,
            DetectionEvent.session_id == session_id,
        ).group_by(DetectionEvent.event_type)

        result = await self.db.execute(query)
        counts = {row.event_type: row.count for row in result}

        return {
            'session_id': str(session_id),
            'drowsy_count': counts.get('DROWSY', 0),
            'yawn_count': counts.get('YAWN', 0),
            'total_events': sum(counts.values()),
        }

    async def get_user_stats(
        self,
        user_id: UUID,
        days: int = 7,
    ) -> dict:
        since = datetime.utcnow() - timedelta(days=days)

        # Get daily event counts
        query = select(
            func.date(DetectionEvent.created_at).label('date'),
            DetectionEvent.event_type,
            func.count(DetectionEvent.id).label('count'),
        ).where(
            DetectionEvent.user_id == user_id,
            DetectionEvent.created_at >= since,
        ).group_by(
            func.date(DetectionEvent.created_at),
            DetectionEvent.event_type,
        ).order_by(func.date(DetectionEvent.created_at))

        result = await self.db.execute(query)
        rows = result.all()

        # Organize by date
        daily_stats = {}
        for row in rows:
            date_str = row.date.isoformat()
            if date_str not in daily_stats:
                daily_stats[date_str] = {'drowsy': 0, 'yawn': 0}
            if row.event_type == 'DROWSY':
                daily_stats[date_str]['drowsy'] = row.count
            elif row.event_type == 'YAWN':
                daily_stats[date_str]['yawn'] = row.count

        return {
            'user_id': str(user_id),
            'period_days': days,
            'daily_stats': daily_stats,
        }

    async def get_recent_events(
        self,
        user_id: UUID,
        limit: int = 50,
    ) -> list[DetectionEvent]:
        query = select(DetectionEvent).where(
            DetectionEvent.user_id == user_id,
        ).order_by(
            DetectionEvent.created_at.desc()
        ).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())
