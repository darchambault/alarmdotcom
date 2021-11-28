""" Binary Sensor platform for Alarm.com """

from datetime import timedelta
import logging

import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_DOOR,
    DEVICE_CLASS_MOTION,
    BinarySensorEntity,
)

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
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
                sensor_data = await alarm_client.async_get_sensors_data()
                _LOGGER.debug(
                    "Found %s binary sensors from Alarm.com", len(sensor_data)
                )
                return sensor_data
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
        name="alarmdotcom sensors",
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
        ContactSensorEntity(coordinator, idx)
        for idx, ent in enumerate(coordinator.data)
    )


class ContactSensorEntity(CoordinatorEntity, BinarySensorEntity):
    """An entity using CoordinatorEntity.

    The CoordinatorEntity class provides:
      should_poll
      async_update
      async_added_to_hass
      available

    """

    DEVICE_CLASS_MAPPING = {
        AlarmdotcomClient.DEVICETYPE_CONTACT: DEVICE_CLASS_DOOR,
        AlarmdotcomClient.DEVICETYPE_MOTION: DEVICE_CLASS_MOTION,
    }
    ON_STATE_MAPPING = {
        AlarmdotcomClient.DEVICETYPE_CONTACT: 2,
        AlarmdotcomClient.DEVICETYPE_MOTION: 4,
    }

    def __init__(self, coordinator, idx):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)
        self.idx = idx

    @property
    def name(self):
        """Name of the entity."""
        return self.coordinator.data[self.idx]["description"]

    @property
    def unique_id(self):
        """Unique ID of the entity."""
        return self.coordinator.data[self.idx]["id"]

    @property
    def is_on(self):
        """Return entity state."""
        is_on = (
            self.coordinator.data[self.idx]["state"]
            == self.ON_STATE_MAPPING[self.coordinator.data[self.idx]["deviceType"]]
        )
        _LOGGER.debug(
            "Sensor of type %s is at state %s and has to be at %s to be ON -- currently %s",
            self.coordinator.data[self.idx]["deviceType"],
            self.coordinator.data[self.idx]["state"],
            self.ON_STATE_MAPPING[self.coordinator.data[self.idx]["deviceType"]],
            "ON" if is_on else "OFF",
        )
        return is_on

    @property
    def device_class(self):
        return self.DEVICE_CLASS_MAPPING[self.coordinator.data[self.idx]["deviceType"]]
