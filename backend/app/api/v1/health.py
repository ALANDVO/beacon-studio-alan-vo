from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_session
from app.core.config import get_settings

router = APIRouter(tags=["health"])
settings = get_settings()


@router.get("/")
async def health_check() -> dict:
    return {
        "status": "healthy",
        "service": "beacon-studio",
        "version": "1.0.0",
        "environment": settings.app_env,
    }


@router.get("/db")
async def health_check_db(session: AsyncSession = Depends(get_session)) -> dict:
    try:
        await session.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}