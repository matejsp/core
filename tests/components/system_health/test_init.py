"""Tests for the system health component init."""
import asyncio

import pytest

from homeassistant.setup import async_setup_component

from tests.async_mock import AsyncMock, Mock
from tests.common import get_system_health_info, mock_platform


@pytest.fixture
def mock_system_info(hass):
    """Mock system info."""
    hass.helpers.system_info.async_get_system_info = AsyncMock(
        return_value={"hello": True}
    )


async def test_info_endpoint_return_info(hass, hass_ws_client, mock_system_info):
    """Test that the info endpoint works."""
    assert await async_setup_component(hass, "system_health", {})
    client = await hass_ws_client(hass)

    resp = await client.send_json({"id": 6, "type": "system_health/info"})
    resp = await client.receive_json()
    assert resp["success"]
    data = resp["result"]

    assert len(data) == 1
    data = data["homeassistant"]
    assert data == {"hello": True}


async def test_info_endpoint_register_callback(hass, hass_ws_client, mock_system_info):
    """Test that the info endpoint allows registering callbacks."""

    async def mock_info(hass):
        return {"storage": "YAML"}

    hass.components.system_health.async_register_info("lovelace", mock_info)
    assert await async_setup_component(hass, "system_health", {})
    client = await hass_ws_client(hass)

    resp = await client.send_json({"id": 6, "type": "system_health/info"})
    resp = await client.receive_json()
    assert resp["success"]
    data = resp["result"]

    assert len(data) == 2
    data = data["lovelace"]
    assert data == {"storage": "YAML"}

    # Test our test helper works
    assert await get_system_health_info(hass, "lovelace") == {"storage": "YAML"}


async def test_info_endpoint_register_callback_timeout(
    hass, hass_ws_client, mock_system_info
):
    """Test that the info endpoint timing out."""

    async def mock_info(hass):
        raise asyncio.TimeoutError

    hass.components.system_health.async_register_info("lovelace", mock_info)
    assert await async_setup_component(hass, "system_health", {})
    client = await hass_ws_client(hass)

    resp = await client.send_json({"id": 6, "type": "system_health/info"})
    resp = await client.receive_json()
    assert resp["success"]
    data = resp["result"]

    assert len(data) == 2
    data = data["lovelace"]
    assert data == {"error": "Fetching info timed out"}


async def test_info_endpoint_register_callback_exc(
    hass, hass_ws_client, mock_system_info
):
    """Test that the info endpoint requires auth."""

    async def mock_info(hass):
        raise Exception("TEST ERROR")

    hass.components.system_health.async_register_info("lovelace", mock_info)
    assert await async_setup_component(hass, "system_health", {})
    client = await hass_ws_client(hass)

    resp = await client.send_json({"id": 6, "type": "system_health/info"})
    resp = await client.receive_json()
    assert resp["success"]
    data = resp["result"]

    assert len(data) == 2
    data = data["lovelace"]
    assert data == {"error": "TEST ERROR"}


async def test_platform_loading(hass):
    """Test registering via platform."""
    hass.config.components.add("fake_integration")
    mock_platform(
        hass,
        "fake_integration.system_health",
        Mock(
            async_register=lambda hass, register: register.async_register_info(
                AsyncMock(return_value={"hello": "info"})
            )
        ),
    )

    assert await async_setup_component(hass, "system_health", {})
    assert await get_system_health_info(hass, "fake_integration") == {"hello": "info"}
