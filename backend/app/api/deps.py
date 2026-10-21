from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_session():
        yield session


class CurrentUser:
    def __init__(self, sub: str, email: str, roles: list[str]):
        self.sub = sub
        self.email = email
        self.roles = roles

    def has_role(self, role: str) -> bool:
        return role in self.roles


async def get_current_user() -> CurrentUser:
    from app.core.config import get_settings
    settings = get_settings()
    if settings.is_demo_mode:
        return CurrentUser(sub="demo", email="demo@local", roles=["viewer", "operator", "admin"])
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_role(required_role: str):
    async def _require_role(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not user.has_role(required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role: {required_role}",
            )
        return user
    return _require_role