""" Sensor platform for Alarm.com """

from datetime import timedelta
import logging

import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from homeassistant.components.sensor import (
    DEVICE_CLASS_TEMPERATURE,
    DEVICE_CLASS_HUMIDITY,
    STATE_CLASS_MEASUREMENT,
    SensorEntity,
)

from homeassistant.const import (
    PERCENTAGE,
    TEMP_FAHRENHEIT,
)

from .const import DOMAIN

from pyalarmdotcomredux import (
    AlarmdotcomClient,
    AlarmdotcomClientError,
    AlarmdotcomClientAuthError,
)


_LOGGER = logging.getLogger(__name__)

SENSORS_DEFS = {
    "ambientTemp": {
        "label": "Ambient Temperature",
        "type": DEVICE_CLASS_TEMPERATURE,
        "unit": TEMP_FAHRENHEIT,
    },
    "humidityLevel": {
        "label": "Humidity Level",
        "type": DEVICE_CLASS_HUMIDITY,
        "unit": PERCENTAGE,
    },
}


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
                thermostats_data = await alarm_client.async_get_thermostats_data()
                sensor_data = []
                for thermostat in thermostats_data:
                    for sensor in ["ambientTemp", "humidityLevel"]:
                        sensor_data.append(
                            {
                                "id": "{}-{}".format(thermostat["id"], sensor),
                                "description": "{} {}".format(
                                    thermostat["description"],
                                    SENSORS_DEFS[sensor]["label"],
                                ),
                                "device_class": SENSORS_DEFS[sensor]["type"],
                                "unit": SENSORS_DEFS[sensor]["unit"],
                                "value": thermostat[sensor],
                            }
                        )
                _LOGGER.debug("Found %s sensors from Alarm.com", len(sensor_data))
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
        ThermostatSensorEntity(coordinator, idx)
        for idx, ent in enumerate(coordinator.data)
    )


class ThermostatSensorEntity(CoordinatorEntity, SensorEntity):
    """An entity using CoordinatorEntity.

    The CoordinatorEntity class provides:
      should_poll
      async_update
      async_added_to_hass
      available

    """

    _attr_state_class = STATE_CLASS_MEASUREMENT

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
    def native_value(self):
        """Return entity native value."""
        return self.coordinator.data[self.idx]["value"]

    @property
    def native_unit_of_measurement(self):
        """Return entity native unit of measurement."""
        return self.coordinator.data[self.idx]["unit"]

    @property
    def device_class(self):
        return self.coordinator.data[self.idx]["device_class"]
