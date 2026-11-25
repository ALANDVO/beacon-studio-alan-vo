"""Plugin marketplace CRUD tests."""
import pytest
from unittest.mock import Mock, patch
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.core.config import Settings


async def truncate_plugins():
    from app.core.database import engine
    from sqlalchemy import text
    async with engine.begin() as conn:
        await conn.execute(text('DELETE FROM plugins'))


@pytest.mark.asyncio
async def test_plugin_crud():
    """Test plugin CRUD operations in demo mode."""
    from app.core.database import init_db
    await truncate_plugins()
    await init_db()

    # Mock settings to enable demo mode
    mock_settings = Settings(
        APP_ENV="development",
        DEMO_MODE="true",
    )
    with patch("app.core.config.get_settings", return_value=mock_settings):
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


@pytest.mark.asyncio
async def test_plugin_search():
    """Test plugin search by name/description."""
    await truncate_plugins()

    mock_settings = Settings(APP_ENV="development", DEMO_MODE="true")
    with patch("app.core.config.get_settings", return_value=mock_settings):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:

            # Create plugins with different names/descriptions
            plugins = [
                {"name": "Alpha Plugin", "description": "An alpha plugin", "harness": "claude-code", "category": "web", "tags": [], "install_command": "npm alpha", "author": "A", "stars": 0},
                {"name": "Beta Plugin", "description": "A beta plugin", "harness": "cursor", "category": "desktop", "tags": [], "install_command": "npm beta", "author": "B", "stars": 0},
                {"name": "Gamma Plugin", "description": "Gamma description", "harness": "cursor", "category": "web", "tags": [], "install_command": "npm gamma", "author": "C", "stars": 0},
            ]
            
            for p in plugins:
                resp = await client.post("/api/v1/plugins", json=p)
                assert resp.status_code == 201

            # Search by name
            resp = await client.get("/api/v1/plugins?search=Alpha")
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 1
            assert any("Alpha" in i["name"] for i in data["items"])

            # Search by description
            resp = await client.get("/api/v1/plugins?search=description")
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] >= 1  # Gamma has "Gamma description"

            # Search with no matches
            resp = await client.get("/api/v1/plugins?search=nonexistent")
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 0


@pytest.mark.asyncio
async def test_plugin_filter_by_harness():
    """Test plugin filtering by harness."""
    await truncate_plugins()

    mock_settings = Settings(APP_ENV="development", DEMO_MODE="true")
    with patch("app.core.config.get_settings", return_value=mock_settings):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:

            # Create plugins with different harnesses
            plugins = [
                {"name": "Plugin A", "description": "Plugin A desc", "harness": "claude-code", "category": "web", "tags": [], "install_command": "npm a", "author": "A", "stars": 0},
                {"name": "Plugin B", "description": "Plugin B desc", "harness": "cursor", "category": "desktop", "tags": [], "install_command": "npm b", "author": "B", "stars": 0},
                {"name": "Plugin C", "description": "Plugin C desc", "harness": "claude-code", "category": "web", "tags": [], "install_command": "npm c", "author": "C", "stars": 0},
            ]
            
            for p in plugins:
                resp = await client.post("/api/v1/plugins", json=p)
                assert resp.status_code == 201

            # Filter by claude-code
            resp = await client.get("/api/v1/plugins?harness=claude-code")
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 2
            assert all(p["harness"] == "claude-code" for p in data["items"])

            # Filter by cursor
            resp = await client.get("/api/v1/plugins?harness=cursor")
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 1
            assert data["items"][0]["harness"] == "cursor"


@pytest.mark.asyncio
async def test_plugin_filter_by_category():
    """Test plugin filtering by category."""
    await truncate_plugins()

    mock_settings = Settings(APP_ENV="development", DEMO_MODE="true")
    with patch("app.core.config.get_settings", return_value=mock_settings):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:

            # Create plugins with different categories
            plugins = [
                {"name": "Web Plugin 1", "description": "Web plugin 1", "harness": "claude-code", "category": "web", "tags": [], "install_command": "npm w1", "author": "A", "stars": 0},
                {"name": "Web Plugin 2", "description": "Web plugin 2", "harness": "cursor", "category": "web", "tags": [], "install_command": "npm w2", "author": "B", "stars": 0},
                {"name": "Desktop Plugin", "description": "Desktop plugin", "harness": "cursor", "category": "desktop", "tags": [], "install_command": "npm d", "author": "C", "stars": 0},
            ]
            
            for p in plugins:
                resp = await client.post("/api/v1/plugins", json=p)
                assert resp.status_code == 201

            # Filter by web
            resp = await client.get("/api/v1/plugins?category=web")
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 2
            assert all(p["category"] == "web" for p in data["items"])

            # Filter by desktop
            resp = await client.get("/api/v1/plugins?category=desktop")
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 1
            assert data["items"][0]["category"] == "desktop"
