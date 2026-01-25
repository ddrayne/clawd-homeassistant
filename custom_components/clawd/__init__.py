"""The Clawd integration."""

import inspect
import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TOKEN, Platform
from homeassistant.core import HomeAssistant

from .const import (
    CONF_MODEL,
    CONF_SESSION_KEY,
    CONF_STRIP_EMOJIS,
    CONF_TIMEOUT,
    CONF_TTS_MAX_CHARS,
    CONF_USE_SSL,
    DEFAULT_MODEL,
    DEFAULT_SESSION_KEY,
    DEFAULT_STRIP_EMOJIS,
    DEFAULT_TIMEOUT,
    DEFAULT_TTS_MAX_CHARS,
    DEFAULT_USE_SSL,
    DOMAIN,
)
from .gateway_client import ClawdGatewayClient

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.CONVERSATION]
SERVICE_RECONNECT = "reconnect"
SERVICE_SET_SESSION = "set_session"
_SERVICE_REGISTERED = "_service_registered"
_RECONNECT_SCHEMA = vol.Schema({vol.Optional("entry_id"): str})
_SESSION_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SESSION_KEY): vol.All(str, vol.Length(min=1)),
        vol.Optional("entry_id"): str,
    }
)

_OPTION_KEYS = {
    CONF_TOKEN,
    CONF_USE_SSL,
    CONF_TIMEOUT,
    CONF_SESSION_KEY,
    CONF_MODEL,
    CONF_STRIP_EMOJIS,
    CONF_TTS_MAX_CHARS,
}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Clawd from a config entry."""
    _LOGGER.info("Setting up Clawd integration")

    # Migrate option-like keys from data to options for existing entries.
    if not entry.options:
        migrated = {
            key: entry.data.get(key)
            for key in _OPTION_KEYS
            if key in entry.data
        }
        if migrated:
            hass.config_entries.async_update_entry(entry, options=migrated)

    options = entry.options

    # Create Gateway client with config from entry.data
    gateway_client = ClawdGatewayClient(
        host=entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
        token=options.get(CONF_TOKEN, entry.data.get(CONF_TOKEN)),
        use_ssl=options.get(
            CONF_USE_SSL, entry.data.get(CONF_USE_SSL, DEFAULT_USE_SSL)
        ),
        timeout=options.get(
            CONF_TIMEOUT, entry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
        ),
        session_key=options.get(
            CONF_SESSION_KEY,
            entry.data.get(CONF_SESSION_KEY, DEFAULT_SESSION_KEY),
        ),
        model=options.get(CONF_MODEL, entry.data.get(CONF_MODEL, DEFAULT_MODEL)),
    )

    # Connect to Gateway
    try:
        await gateway_client.connect()
        _LOGGER.info(
            "Connected to Clawd Gateway at %s:%s",
            entry.data[CONF_HOST],
            entry.data[CONF_PORT],
        )
    except Exception as err:
        _LOGGER.error("Failed to connect to Gateway: %s", err)
        return False

    # Store client in hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = gateway_client

    if not hass.data[DOMAIN].get(_SERVICE_REGISTERED):
        async def _async_handle_reconnect(call) -> None:
            entry_id = call.data.get("entry_id")
            clients = hass.data.get(DOMAIN, {})

            if entry_id:
                target = clients.get(entry_id)
                if not target:
                    _LOGGER.warning("Reconnect requested for unknown entry: %s", entry_id)
                    return
                targets = [target]
            else:
                targets = [
                    client
                    for key, client in clients.items()
                    if key != _SERVICE_REGISTERED
                ]

            for client in targets:
                await client.disconnect()
                await client.connect()

        hass.services.async_register(
            DOMAIN, SERVICE_RECONNECT, _async_handle_reconnect, schema=_RECONNECT_SCHEMA
        )

        async def _async_handle_set_session(call) -> None:
            entry_id = call.data.get("entry_id")
            session_key = call.data[CONF_SESSION_KEY]
            clients = hass.data.get(DOMAIN, {})

            if entry_id:
                target = clients.get(entry_id)
                if not target:
                    _LOGGER.warning(
                        "Session update requested for unknown entry: %s",
                        entry_id,
                    )
                    return
                targets = [target]
            else:
                targets = [
                    client
                    for key, client in clients.items()
                    if key != _SERVICE_REGISTERED
                ]

            for client in targets:
                client.set_session_key(session_key)

        hass.services.async_register(
            DOMAIN,
            SERVICE_SET_SESSION,
            _async_handle_set_session,
            schema=_SESSION_SCHEMA,
        )
        hass.data[DOMAIN][_SERVICE_REGISTERED] = True

    # Forward setup to conversation platform
    try:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except Exception:
        _LOGGER.exception("Failed to set up conversation platform")
        await gateway_client.disconnect()
        hass.data[DOMAIN].pop(entry.entry_id, None)
        return False

    # Register reload listener
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading Clawd integration")

    # Get client before unloading
    gateway_client: ClawdGatewayClient | None = (
        hass.data.get(DOMAIN, {}).get(entry.entry_id)
    )
    if gateway_client is None:
        _LOGGER.debug(
            "Entry not found in hass.data during unload: %s", entry.entry_id
        )

    # Unload conversation platform even if the client was already cleared.
    try:
        unload_result = hass.config_entries.async_unload_platforms(
            entry, PLATFORMS
        )
        if inspect.isawaitable(unload_result):
            unload_ok = await unload_result
        else:
            unload_ok = bool(unload_result) if unload_result is not None else True
    except ValueError:
        _LOGGER.warning(
            "Conversation platform was not loaded for entry: %s", entry.entry_id
        )
        unload_ok = True

    # Always disconnect and cleanup, even if unload failed
    if gateway_client is not None:
        await gateway_client.disconnect()
        _LOGGER.info("Disconnected from Clawd Gateway")
    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    try:
        await async_unload_entry(hass, entry)
    except Exception:
        _LOGGER.exception(
            "Failed to unload entry during reload: %s", entry.entry_id
        )
    await async_setup_entry(hass, entry)
