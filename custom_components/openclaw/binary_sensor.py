"""Binary sensor for OpenClaw gateway connectivity."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .gateway_client import OpenClawGatewayClient

SCAN_INTERVAL = timedelta(seconds=10)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up OpenClaw binary sensor."""
    gateway_client: OpenClawGatewayClient = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([OpenClawGatewayConnectivitySensor(entry, gateway_client)])


class OpenClawGatewayConnectivitySensor(BinarySensorEntity):
    """Binary sensor for gateway connection status."""

    _attr_has_entity_name = True
    _attr_name = "Gateway Connectivity"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_should_poll = True

    def __init__(
        self, config_entry: ConfigEntry, gateway_client: OpenClawGatewayClient
    ) -> None:
        """Initialize the binary sensor."""
        self._config_entry = config_entry
        self._gateway_client = gateway_client
        self._attr_unique_id = f"{config_entry.entry_id}_gateway_connectivity"

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info for the gateway."""
        return {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": "OpenClaw Gateway",
            "manufacturer": "OpenClaw",
            "model": "Gateway",
        }

    @property
    def is_on(self) -> bool:
        """Return True if the gateway is connected."""
        return self._gateway_client.connected
