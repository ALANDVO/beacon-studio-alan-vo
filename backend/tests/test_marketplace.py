"""Plugin marketplace CRUD tests."""
import pytest
from unittest.mock import Mock, patch
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.core.config import Settings


@pytest.mark.asyncio
async def test_plugin_crud():
    """Test plugin CRUD operations in demo mode."""
    # Mock settings to enable demo mode
    mock_settings = Settings(
        APP_ENV="development",
        DEMO_MODE="true",
    )
    with patch("app.api.deps.get_settings", return_value=mock_settings):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:

            # 1. List plugins (should be empty)
            resp = await client.get("/api/v1/plugins")
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 0
            assert data["items"] == []

            # 2. Create a plugin (operator role is allowed)
            plugin_payload = {
                "name": "Test Plugin",
                "description": "A test plugin for marketplace",
                "harness": "claude-code",
                "category": "web",
                "tags": ["api", "demo"],
                "install_command": "npm install test-plugin",
                "author": "Test Author",
                "stars": 0,
            }
            resp = await client.post("/api/v1/plugins", json=plugin_payload)
            assert resp.status_code == 201
            created = resp.json()
            plugin_id = created["id"]
            assert created["name"] == plugin_payload["name"]
            assert created["harness"] == plugin_payload["harness"]

            # 3. Get the plugin by ID
            resp = await client.get(f"/api/v1/plugins/{plugin_id}")
            assert resp.status_code == 200
            fetched = resp.json()
            assert fetched["id"] == plugin_id
            assert fetched["name"] == plugin_payload["name"]

            # 4. Update the plugin (operator role)
            update_payload = {
                "name": "Updated Plugin",
                "description": "Updated description",
                "harness": "cursor",
                "category": "desktop",
                "tags": ["updated"],
                "install_command": "npm install updated-plugin",
                "author": "Updated Author",
                "stars": 5,
            }
            resp = await client.put(f"/api/v1/plugins/{plugin_id}", json=update_payload)
            assert resp.status_code == 200
            updated = resp.json()
            assert updated["id"] == plugin_id
            assert updated["name"] == "Updated Plugin"
            assert updated["harness"] == "cursor"

            # 5. List plugins again (should contain updated plugin)
            resp = await client.get("/api/v1/plugins")
            assert resp.status_code == 200
            list_data = resp.json()
            assert list_data["total"] == 1
            assert list_data["items"][0]["id"] == plugin_id

            # 6. Delete plugin (admin role)
            resp = await client.delete(f"/api/v1/plugins/{plugin_id}")
            assert resp.status_code == 204

            # 7. Verify deletion (list empty)
            resp = await client.get("/api/v1/plugins")
            assert resp.status_code == 200
            final_data = resp.json()
            assert final_data["total"] == 0

            print("Plugin CRUD test passed.")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
