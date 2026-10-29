"""API dependencies."""
from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.services.auth import validate_access_token

class CurrentUser:
    def __init__(self, sub: str, email: str, roles: list[str]):
        self.sub = sub
        self.email = email
        self.roles = roles

    def has_role(self, role: str) -> bool:
        return role in self.roles


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_session():
        yield session


async def get_current_user(authorization: Optional[str] = Header(None)) -> CurrentUser:
    from app.core.config import get_settings
    settings = get_settings()
    
    # Demo mode: return fake user
    if settings.is_demo_mode:
        return CurrentUser(sub="demo", email="demo@local", roles=["viewer", "operator", "admin"])
    
    # Require authorization header
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization[7:]  # Remove "Bearer "
    claims = await validate_access_token(token)
    
    if not claims:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract user info from claims
    sub = claims.get("sub", "")
    email = claims.get("email", "")
    roles = claims.get("roles", [])
    
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing subject",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return CurrentUser(sub=sub, email=email, roles=roles)


def require_role(required_role: str):
    async def _require_role(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not user.has_role(required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role: {required_role}",
            )
        return user
    return _require_role
