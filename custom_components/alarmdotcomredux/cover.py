""" Support for Alarm.com garage doors"""

from datetime import timedelta
import logging

import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from homeassistant.components.cover import (
    DEVICE_CLASS_GARAGE,
    SUPPORT_CLOSE,
    SUPPORT_OPEN,
    CoverEntity,
)

from .const import DOMAIN

from pyalarmdotcomredux import (
    AlarmdotcomClient,
    AlarmdotcomClientError,
    AlarmdotcomClientAuthError,
)


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> bool:
    """Setup entities"""
    alarm_client: AlarmdotcomClient = hass.data[DOMAIN][entry.entry_id]

    async def async_update_data():
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with async_timeout.timeout(10):
                cover_data = await alarm_client.async_get_garage_doors_data()
                _LOGGER.debug("Found %s covers from Alarm.com", len(cover_data))
                return cover_data
        except AlarmdotcomClientAuthError as err:
            # Raising ConfigEntryAuthFailed will cancel future updates
            # and start a config flow with SOURCE_REAUTH (async_step_reauth)
            raise ConfigEntryAuthFailed from err
        except AlarmdotcomClientError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        # Name of the data. For logging purposes.
        name="alarmdotcom covers",
        update_method=async_update_data,
        # Polling interval. Will only be polled if there are subscribers.
        update_interval=timedelta(seconds=30),
    )

    #
    # Fetch initial data so we have data when entities subscribe
    #
    # If the refresh fails, async_config_entry_first_refresh will
    # raise ConfigEntryNotReady and setup will try again later
    #
    # If you do not want to retry setup on failure, use
    # coordinator.async_refresh() instead
    #
    await coordinator.async_config_entry_first_refresh()

    async_add_entities(
        AlarmdotcomCoverEntity(coordinator, idx, alarm_client)
        for idx, ent in enumerate(coordinator.data)
    )


class AlarmdotcomCoverEntity(CoordinatorEntity, CoverEntity):
    """Alarm.com Cover entity

    The CoordinatorEntity class provides:
      should_poll
      async_update
      async_added_to_hass
      available

    """

    _attr_supported_features = SUPPORT_OPEN | SUPPORT_CLOSE
    _attr_device_class = DEVICE_CLASS_GARAGE
    _attr_is_closing = False
    _attr_is_closing = False

    def __init__(self, coordinator, idx, alarm_client: AlarmdotcomClient):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)
        self.idx = idx
        self._alarm_client = alarm_client

    @property
    def unique_id(self):
        return self.coordinator.data[self.idx]["id"]

    @property
    def name(self):
        return self.coordinator.data[self.idx]["description"]

    @property
    def is_closed(self):
        """Return true if cover is closed, else False."""
        return (
            self.coordinator.data[self.idx]["state"]
            == AlarmdotcomClient.GARAGE_DOOR_STATE_CLOSED
        )

    @property
    def is_open(self):
        """Return true if cover is open, else False."""
        return (
            self.coordinator.data[self.idx]["state"]
            == AlarmdotcomClient.GARAGE_DOOR_STATE_OPEN
        )

    async def async_close_cover(self, **kwargs):
        """Issue close command to cover."""
        if self.is_closing or self.is_closed:
            return

        try:
            await self._alarm_client.async_close_garage_door(
                self.coordinator.data[self.idx]["id"]
            )
        except AlarmdotcomClientError as err:
            raise HomeAssistantError(
                "Closing of cover {cover_name} failed with error: {err}".format(
                    cover_name=self.name, err=err
                )
            ) from err

    async def async_open_cover(self, **kwargs):
        """Issue open command to cover."""
        if self.is_opening or self.is_open:
            return

        try:
            await self._alarm_client.async_open_garage_door(
                self.coordinator.data[self.idx]["id"]
            )
        except AlarmdotcomClientError as err:
            raise HomeAssistantError(
                "Opening of cover {cover_name} failed with error: {err}".format(
                    cover_name=self.name, err=err
                )
            ) from err
