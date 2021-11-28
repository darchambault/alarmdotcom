"""The Alarm.com Redux integration."""
from __future__ import annotations
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

from homeassistant.helpers.aiohttp_client import async_get_clientsession

from pyalarmdotcomredux import AlarmdotcomClient

PLATFORMS: list[str] = ["alarm_control_panel", "binary_sensor", "cover", "sensor"]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Alarm.com from a config entry."""
    alarm = AlarmdotcomClient(
        entry.data.get("username"),
        entry.data.get("password"),
        async_get_clientsession(hass),
        twofactorcookie=entry.data.get("twofactorcookie"),
    )
    hass.data[DOMAIN] = {entry.entry_id: alarm}

    _LOGGER.debug("Setup platforms")
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
