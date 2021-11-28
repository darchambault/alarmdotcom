""" Alarm Control Panel platform for Alarm.com """

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from homeassistant.exceptions import HomeAssistantError

from homeassistant.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_DISARMED,
)

from homeassistant.components.alarm_control_panel import (
    FORMAT_NUMBER,
    AlarmControlPanelEntity,
)
from homeassistant.components.alarm_control_panel.const import (
    SUPPORT_ALARM_ARM_AWAY,
    SUPPORT_ALARM_ARM_HOME,
)

from .const import DOMAIN

from pyalarmdotcomredux import AlarmdotcomClient, AlarmdotcomClientError


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> bool:
    """Setup entities"""
    alarm_client = hass.data[DOMAIN][entry.entry_id]

    entity = AlarmEntity(alarm_client, entry.data.get("code"))
    _LOGGER.debug("Triggering first Alarm.com panel update")
    await entity.async_update()
    async_add_entities([entity])


class AlarmEntity(AlarmControlPanelEntity):
    """Representation of an Alarm.com-based alarm panel."""

    _attr_code_format = FORMAT_NUMBER
    _attr_supported_features = SUPPORT_ALARM_ARM_HOME | SUPPORT_ALARM_ARM_AWAY

    STATE_MAPPING = {
        AlarmdotcomClient.ALARM_STATE_DISARMED: STATE_ALARM_DISARMED,
        AlarmdotcomClient.ALARM_STATE_ARMED_STAY: STATE_ALARM_ARMED_HOME,
        AlarmdotcomClient.ALARM_STATE_ARMED_AWAY: STATE_ALARM_ARMED_AWAY,
        AlarmdotcomClient.ALARM_STATE_ARMED_NIGHT: STATE_ALARM_ARMED_NIGHT,
    }

    def __init__(self, alarm_client: AlarmdotcomClient, code: str) -> None:
        self._alarm_client = alarm_client
        self._code = code

    async def async_update(self) -> None:
        """Trigger update"""
        alarm_data = await self._alarm_client.async_get_alarm_data()
        _LOGGER.debug(
            "Updated Alarm.com alarm data for '%s' (id %s)",
            alarm_data["description"],
            alarm_data["id"],
        )
        self._attr_unique_id = alarm_data["id"]
        self._attr_name = alarm_data["description"]
        self._attr_state = self.STATE_MAPPING[alarm_data["state"]]

    async def async_alarm_disarm(self, code=None) -> None:
        """Send disarm command."""
        if self._validate_code(code):
            try:
                await self._alarm_client.async_alarm_disarm()
            except AlarmdotcomClientError as err:
                raise HomeAssistantError(
                    "Disarming {alarm_name} failed with error: {err}".format(
                        alarm_name=self.name,
                        err=err,
                    )
                ) from err

    async def async_alarm_arm_home(self, code=None) -> None:
        """Send arm home command."""
        if self._validate_code(code):
            try:
                await self._alarm_client.async_alarm_arm_stay()
            except AlarmdotcomClientError as err:
                raise HomeAssistantError(
                    "Arming (Home) {alarm_name} failed with error: {err}".format(
                        alarm_name=self.name,
                        err=err,
                    )
                ) from err

    async def async_alarm_arm_away(self, code=None) -> None:
        """Send arm away command."""
        if self._validate_code(code):
            try:
                await self._alarm_client.async_alarm_arm_away()
            except AlarmdotcomClientError as err:
                raise HomeAssistantError(
                    "Arming (Away) {alarm_name} failed with error: {err}".format(
                        alarm_name=self.name,
                        err=err,
                    )
                ) from err

    def _validate_code(self, code):
        """Validate given code."""
        check = self._code is None or code == self._code
        if not check:
            _LOGGER.warning("Wrong code entered")
        return check
