"""API v1 router."""
from fastapi import APIRouter

from app.api.v1 import health, plugins, auth

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="", tags=["auth"])
api_router.include_router(plugins.router, prefix="", tags=["plugins", "audit", "context", "gtm"])
