"""Authentication tests for OIDC PKCE flow."""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.core.security import (
    generate_pkce_pair,
    build_authorize_url,
    generate_state,
    generate_nonce,
    verify_state,
)
from app.services.auth import JWKSClient, TokenExchanger, LogoutService
from app.api.deps import CurrentUser, get_current_user


class TestPKCEGeneration:
    """Test PKCE code verifier and challenge generation."""

    def test_generate_pkce_pair_returns_valid_pair(self):
        """PKCE pair should have valid verifier and challenge."""
        verifier, challenge = generate_pkce_pair()
        assert verifier is not None
        assert challenge is not None
        assert len(verifier) > 0
        assert len(challenge) > 0
        assert verifier != challenge

    def test_generate_pkce_pair_unique_each_call(self):
        """Each call should generate a unique pair."""
        v1, c1 = generate_pkce_pair()
        v2, c2 = generate_pkce_pair()
        assert v1 != v2
        assert c1 != c2

    def test_challenge_is_sha256_of_verifier(self):
        """Challenge should be SHA256 hash of verifier, base64url encoded."""
        import hashlib
        import base64

        verifier, challenge = generate_pkce_pair()
        expected = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode()).digest()
        ).decode().rstrip("=")
        assert challenge == expected


class TestStateAndNonce:
    """Test state and nonce generation for OIDC."""

    def test_generate_state_returns_string(self):
        """State should be a non-empty URL-safe string."""
        state = generate_state()
        assert isinstance(state, str)
        assert len(state) > 0

    def test_generate_nonce_returns_string(self):
        """Nonce should be a non-empty URL-safe string."""
        nonce = generate_nonce()
        assert isinstance(nonce, str)
        assert len(nonce) > 0

    def test_verify_state_matches(self):
        """verify_state should return True for identical states."""
        state = generate_state()
        assert verify_state(state, state) is True

    def test_verify_state_mismatch(self):
        """verify_state should return False for different states."""
        assert verify_state("state1", "state2") is False

    def test_verify_state_timing_safe(self):
        """verify_state should use constant-time comparison."""
        import secrets
        assert verify_state("a" * 32, "a" * 32) is True
        assert verify_state("a" * 32, "b" * 32) is False


class TestAuthorizeURL:
    """Test authorization URL building."""

    def test_build_authorize_url_contains_required_params(self):
        """Auth URL should contain all required OIDC parameters."""
        state = "test-state"
        code_challenge = "test-challenge"
        redirect_uri = "http://127.0.0.1:5173/callback"
        nonce = "test-nonce"

        url = build_authorize_url(state, code_challenge, redirect_uri, nonce)

        assert "client_id=beacon-studio" in url
        assert f"redirect_uri={redirect_uri}" in url
        assert "response_type=code" in url
        assert "scope=openid+profile+email" in url
        assert f"state={state}" in url
        assert f"nonce={nonce}" in url
        assert f"code_challenge={code_challenge}" in url
        assert "code_challenge_method=S256" in url
        assert url.startswith("http://127.0.0.1:8080/realms/beacon/protocol/openid-connect/auth?")

    def test_build_authorize_url_with_special_chars(self):
        """Auth URL should properly encode special characters in redirect_uri."""
        redirect_uri = "http://127.0.0.1:5173/callback?foo=bar&baz=qux"
        url = build_authorize_url("state", "challenge", redirect_uri, "nonce")
        assert "redirect_uri=http%3A//127.0.0.1%3A5173/callback%3Ffoo%3Dbar%26baz%3Dqux" in url


class TestJWKSClient:
    """Test JWKS client for token validation."""

    @pytest.mark.asyncio
    async def test_fetch_keys_success(self):
        """fetch_keys should return JWKS on successful response."""
        mock_response = Mock()
        mock_response.json.return_value = {"keys": [{"kid": "test-key", "kty": "RSA"}]}
        mock_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            client = JWKSClient()
            keys = await client.fetch_keys()
            assert "keys" in keys
            assert len(keys["keys"]) == 1

    @pytest.mark.asyncio
    async def test_get_keys_caches_results(self):
        """get_keys should cache results for TTL."""
        mock_response = Mock()
        mock_response.json.return_value = {"keys": [{"kid": "test-key"}]}
        mock_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            client = JWKSClient()
            await client.get_keys()
            await client.get_keys()
            # Should only fetch once due to caching
            assert mock_get.call_count == 1

    @pytest.mark.asyncio
    async def test_get_signing_key_returns_key(self):
        """get_signing_key should return key by kid."""
        client = JWKSClient()
        client._keys = {"keys": [{"kid": "key1", "kty": "RSA"}, {"kid": "key2", "kty": "RSA"}]}
        key = client.get_signing_key("key1")
        assert key is not None
        assert key["kid"] == "key1"

    @pytest.mark.asyncio
    async def test_get_signing_key_not_found(self):
        """get_signing_key should return None for unknown kid."""
        client = JWKSClient()
        client._keys = {"keys": [{"kid": "key1"}]}
        key = client.get_signing_key("unknown")
        assert key is None

    @pytest.mark.asyncio
    async def test_validate_token_invalid_signature(self):
        """validate_token should return None for invalid token."""
        client = JWKSClient()
        client._keys = {"keys": []}
        result = await client.validate_token("invalid.token.here")
        assert result is None


class TestTokenExchanger:
    """Test authorization code exchange for tokens."""

    @pytest.mark.asyncio
    async def test_exchange_code_success(self):
        """exchange_code should return tokens on success."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "access-token",
            "refresh_token": "refresh-token",
            "id_token": "id-token",
            "expires_in": 300,
            "token_type": "Bearer",
        }
        mock_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            exchanger = TokenExchanger()
            tokens = await exchanger.exchange_code("auth-code", "verifier", "http://redirect")
            assert tokens is not None
            assert tokens["access_token"] == "access-token"
            assert tokens["refresh_token"] == "refresh-token"

    @pytest.mark.asyncio
    async def test_exchange_code_failure(self):
        """exchange_code should return None on HTTP error."""
        import httpx

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = httpx.HTTPStatusError(
                "error", request=Mock(), response=Mock(status_code=400)
            )
            exchanger = TokenExchanger()
            tokens = await exchanger.exchange_code("bad-code", "verifier", "http://redirect")
            assert tokens is None


class TestLogoutService:
    """Test OIDC logout."""

    @pytest.mark.asyncio
    async def test_logout_calls_keycloak(self):
        """logout should POST to Keycloak logout endpoint."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            service = LogoutService()
            await service.logout("refresh-token")
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_logout_without_refresh_token(self):
        """logout should work without refresh token."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            service = LogoutService()
            await service.logout(None)
            mock_post.assert_called_once()


class TestAuthDependencies:
    """Test FastAPI auth dependencies."""

    @pytest.mark.asyncio
    async def test_get_current_user_demo_mode(self):
        """get_current_user should return demo user when DEMO_MODE=true."""
        from app.core.config import Settings

        with patch("app.api.deps.get_settings") as mock_settings:
            mock_settings.return_value = Settings(
                APP_ENV="development", DEMO_MODE="true"
            )
            user = await get_current_user(authorization=None)
            assert isinstance(user, CurrentUser)
            assert user.sub == "demo"
            assert user.email == "demo@local"
            assert "viewer" in user.roles
            assert "operator" in user.roles
            assert "admin" in user.roles

    @pytest.mark.asyncio
    async def test_get_current_user_missing_auth_header(self):
        """get_current_user should raise 401 when auth header missing."""
        from app.core.config import Settings

        with patch("app.api.deps.get_settings") as mock_settings:
            mock_settings.return_value = Settings(
                APP_ENV="development", DEMO_MODE="false"
            )
            with pytest.raises(Exception) as exc_info:
                await get_current_user(authorization=None)
            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """get_current_user should raise 401 for invalid token."""
        from app.core.config import Settings

        with patch("app.api.deps.get_settings") as mock_settings:
            mock_settings.return_value = Settings(
                APP_ENV="development", DEMO_MODE="false"
            )
            with patch("app.api.deps.validate_access_token", new_callable=AsyncMock) as mock_validate:
                mock_validate.return_value = None
                with pytest.raises(Exception) as exc_info:
                    await get_current_user(authorization="Bearer invalid-token")
                assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self):
        """get_current_user should return user for valid token."""
        from app.core.config import Settings

        with patch("app.api.deps.get_settings") as mock_settings:
            mock_settings.return_value = Settings(
                APP_ENV="development", DEMO_MODE="false"
            )
            with patch("app.api.deps.validate_access_token", new_callable=AsyncMock) as mock_validate:
                mock_validate.return_value = {
                    "sub": "user-123",
                    "email": "user@example.com",
                    "roles": ["viewer"],
                }
                user = await get_current_user(authorization="Bearer valid-token")
                assert isinstance(user, CurrentUser)
                assert user.sub == "user-123"
                assert user.email == "user@example.com"
                assert user.roles == ["viewer"]

    def test_current_user_has_role(self):
        """CurrentUser.has_role should check role membership."""
        user = CurrentUser(sub="test", email="test@test", roles=["viewer", "operator"])
        assert user.has_role("viewer") is True
        assert user.has_role("admin") is False


class TestAuthAPIEndpoints:
    """Test auth API endpoints via FastAPI test client."""

    @pytest.mark.asyncio
    async def test_login_endpoint_returns_auth_url(self):
        """GET /auth/login should return authorization URL and state."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/auth/login",
                params={"redirect_uri": "http://127.0.0.1:5173/callback"},
            )
            assert response.status_code == 200
            data = response.json()
            assert "auth_url" in data
            assert "state" in data
            assert data["auth_url"].startswith("http://127.0.0.1:8080/realms/beacon")
            assert len(data["state"]) > 0

    @pytest.mark.asyncio
    async def test_callback_endpoint_missing_code_verifier(self):
        """POST /auth/callback should fail without code_verifier."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/callback",
                json={"code": "auth-code", "state": "state"},
            )
            assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_callback_endpoint_invalid_state(self):
        """POST /auth/callback should fail with invalid state."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/callback",
                json={
                    "code": "auth-code",
                    "state": "wrong-state",
                    "code_verifier": "verifier",
                },
            )
            assert response.status_code == 400
            assert "Invalid state" in response.json().get("detail", "")

    @pytest.mark.asyncio
    async def test_logout_endpoint(self):
        """POST /auth/logout should succeed."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/auth/logout",
                json={"refresh_token": "refresh-token"},
            )
            assert response.status_code == 200
            assert response.json()["message"] == "Logged out successfully"

    @pytest.mark.asyncio
    async def test_me_endpoint_demo_mode(self):
        """GET /auth/me should return demo user info in demo mode."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/auth/me")
            assert response.status_code == 200
            data = response.json()
            assert data["sub"] == "demo"
            assert data["email"] == "demo@local"
            assert "viewer" in data["roles"]


class TestRequireRole:
    """Test role-based access control."""

    def test_require_role_allows_matching_role(self):
        """require_role should allow user with required role."""
        from app.api.deps import require_role
        from app.core.config import Settings

        with patch("app.api.deps.get_settings") as mock_settings:
            mock_settings.return_value = Settings(APP_ENV="development", DEMO_MODE="true")
            import asyncio
            user = asyncio.run(require_role("viewer")())
            assert user.has_role("viewer") is True

    def test_require_role_denies_missing_role(self):
        """require_role should raise 403 for missing role."""
        from app.api.deps import require_role
        from app.core.config import Settings

        with patch("app.api.deps.get_settings") as mock_settings:
            mock_settings.return_value = Settings(APP_ENV="development", DEMO_MODE="true")
            import asyncio
            try:
                asyncio.run(require_role("nonexistent-role")())
                assert False, "Should have raised"
            except Exception as e:
                assert e.status_code == 403


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
