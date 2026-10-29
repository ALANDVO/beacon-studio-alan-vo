"""Authentication service with JWKS validation and PKCE support."""
import json
import time
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import httpx
from jose import jwt, jwk
from jose.exceptions import JWTError

from app.core.config import get_settings
from app.core.security import generate_pkce_pair, build_authorize_url, generate_state, generate_nonce, verify_state

settings = get_settings()


class JWKSClient:
    """Client for fetching and caching JWKS from Keycloak."""

    def __init__(self):
        self._keys: Dict[str, Any] = {}
        self._fetched_at: float = 0
        self._cache_ttl = 3600  # 1 hour

    @property
    def jwks_url(self) -> str:
        return f"{settings.keycloak_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/certs"

    async def fetch_keys(self) -> Dict[str, Any]:
        """Fetch JWKS from Keycloak."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(self.jwks_url)
            response.raise_for_status()
            return response.json()

    async def get_keys(self) -> Dict[str, Any]:
        """Get cached keys or fetch new ones."""
        now = time.time()
        if not self._keys or (now - self._fetched_at) > self._cache_ttl:
            self._keys = await self.fetch_keys()
            self._fetched_at = now
        return self._keys

    def get_signing_key(self, kid: str) -> Optional[Any]:
        """Get signing key by key ID."""
        keys = self._keys.get("keys", [])
        for key in keys:
            if key.get("kid") == kid:
                return jwk.construct(key)
        return None

    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token and return claims."""
        try:
            # Get unverified header to find kid
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")
            if not kid:
                return None

            # Get signing key
            await self.get_keys()
            signing_key = self.get_signing_key(kid)
            if not signing_key:
                return None

            # Validate token
            claims = jwt.decode(
                token,
                signing_key.to_pem().decode(),
                algorithms=["RS256"],
                audience=settings.oidc_audience,
                issuer=settings.oidc_issuer,
            )
            return claims
        except JWTError:
            return None
        except Exception:
            return None


class TokenExchanger:
    """Exchange authorization code for tokens."""

    def __init__(self):
        self.token_url = f"{settings.keycloak_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/token"

    async def exchange_code(
        self, code: str, code_verifier: str, redirect_uri: str
    ) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for tokens."""
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": settings.keycloak_client_id,
            "code_verifier": code_verifier,
            "redirect_uri": redirect_uri,
        }
        if settings.keycloak_client_secret:
            data["client_secret"] = settings.keycloak_client_secret

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(self.token_url, data=data)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError:
            return None


class LogoutService:
    """Handle OIDC logout."""

    async def logout(self, refresh_token: Optional[str] = None) -> None:
        """Perform OIDC logout."""
        logout_url = f"{settings.keycloak_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/logout"

        params = {
            "client_id": settings.keycloak_client_id,
        }
        if settings.keycloak_client_secret:
            params["client_secret"] = settings.keycloak_client_secret
        if refresh_token:
            params["refresh_token"] = refresh_token

        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(logout_url, params=params)


# Global instances
jwks_client = JWKSClient()
token_exchanger = TokenExchanger()
logout_service = LogoutService()


async def validate_access_token(token: str) -> Optional[Dict[str, Any]]:
    return await jwks_client.validate_token(token)


async def exchange_code_for_tokens(code: str, code_verifier: str, redirect_uri: str) -> Optional[Dict[str, Any]]:
    return await token_exchanger.exchange_code(code, code_verifier, redirect_uri)


async def perform_logout(refresh_token: Optional[str] = None) -> None:
    await logout_service.logout(refresh_token)
