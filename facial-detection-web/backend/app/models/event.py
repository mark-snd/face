from sqlalchemy import Column, String, Float, DateTime, Index, Text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.core.database import Base


class DetectionEvent(Base):
    __tablename__ = "detection_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    event_type = Column(String(20), nullable=False)  # DROWSY, YAWN
    ear = Column(Float, nullable=True)
    mar = Column(Float, nullable=True)
    emotion = Column(String(20), nullable=True)
    confidence = Column(Float, nullable=True)
    metadata = Column(Text, nullable=True)  # JSON string for additional data
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_user_time', 'user_id', 'created_at'),
        Index('idx_session_time', 'session_id', 'created_at'),
        Index('idx_event_type', 'event_type'),
    )


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(String(1), default='Y')
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
