import secrets
import hashlib
import base64
from urllib.parse import urlencode
from typing import Tuple

from app.core.config import get_settings

settings = get_settings()


def generate_pkce_pair() -> Tuple[str, str]:
    """Generate PKCE code verifier and challenge."""
    code_verifier = secrets.token_urlsafe(32)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode().rstrip("=")
    return code_verifier, code_challenge


def build_authorize_url(
    state: str,
    code_challenge: str,
    redirect_uri: str,
    nonce: str,
) -> str:
    """Build Keycloak authorization URL with PKCE."""
    params = {
        "client_id": settings.keycloak_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid profile email",
        "state": state,
        "nonce": nonce,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    return f"{settings.keycloak_url}/realms/{settings.keycloak_realm}/protocol/openid-connect/auth?{urlencode(params)}"


def generate_state() -> str:
    return secrets.token_urlsafe(32)


def generate_nonce() -> str:
    return secrets.token_urlsafe(32)


def verify_state(stored: str, received: str) -> bool:
    return secrets.compare_digest(stored, received)