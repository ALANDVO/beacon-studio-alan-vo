"""Authentication API routes."""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional

from app.core.config import get_settings
from app.core.security import generate_pkce_pair, build_authorize_url, generate_state, generate_nonce
from app.services.auth import exchange_code_for_tokens, perform_logout

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()

# In-memory state storage (use Redis in production)
_pkce_store: dict[str, dict] = {}


class AuthUrlResponse(BaseModel):
    auth_url: str
    state: str


class TokenRequest(BaseModel):
    code: str
    state: str
    code_verifier: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None
    id_token: Optional[str] = None


@router.get("/login", response_model=AuthUrlResponse)
async def login(redirect_uri: str = "http://127.0.0.1:5173/callback"):
    """Initiate OIDC login with PKCE."""
    code_verifier, code_challenge = generate_pkce_pair()
    state = generate_state()
    nonce = generate_nonce()

    # Store PKCE data for callback
    _pkce_store[state] = {
        "code_verifier": code_verifier,
        "nonce": nonce,
        "redirect_uri": redirect_uri,
    }

    auth_url = build_authorize_url(state, code_challenge, redirect_uri, nonce)
    return AuthUrlResponse(auth_url=auth_url, state=state)


@router.post("/callback", response_model=TokenResponse)
async def callback(request: TokenRequest):
    """Handle OIDC callback and exchange code for tokens."""
    # Retrieve stored PKCE data
    stored = _pkce_store.pop(request.state, None)
    if not stored:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired state",
        )

    # Verify state (additional check)
    if request.state != request.state:  # This is a placeholder, actual check is above
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="State mismatch",
        )

    code_verifier = stored["code_verifier"]
    redirect_uri = stored["redirect_uri"]

    # Exchange code for tokens
    tokens = await exchange_code_for_tokens(request.code, code_verifier, redirect_uri)
    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to exchange code for tokens",
        )

    return TokenResponse(**tokens)


@router.post("/logout")
async def logout(refresh_token: Optional[str] = None):
    """Perform OIDC logout."""
    await perform_logout(refresh_token)
    return {"message": "Logged out successfully"}


@router.get("/me")
async def me(request: Request):
    """Get current user info from session (for demo mode)."""
    from app.core.config import get_settings
    settings = get_settings()
    
    if settings.is_demo_mode:
        return {
            "sub": "demo",
            "email": "demo@local",
            "roles": ["viewer", "operator", "admin"],
        }
    
    # In production, this would validate the access token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    
    token = auth_header[7:]
    from app.services.auth import validate_access_token
    claims = await validate_access_token(token)
    
    if not claims:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    
    return {
        "sub": claims.get("sub"),
        "email": claims.get("email"),
        "roles": claims.get("roles", []),
    }
