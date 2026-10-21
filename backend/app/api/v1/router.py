from fastapi import APIRouter

from app.api.v1 import health, plugins

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(plugins.router, prefix="", tags=["plugins", "audit", "context", "gtm"])