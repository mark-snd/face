from fastapi import APIRouter
from datetime import datetime

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "facial-detection-api",
    }


@router.get("/")
async def root():
    return {
        "message": "Facial Detection API",
        "version": "1.0.0",
        "docs": "/docs",
    }
