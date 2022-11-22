"""Support for Envisalink sensors (shows panel info)."""
from __future__ import annotations

import logging
from typing import Any
from collections.abc import Mapping
from .envisalink_device import EnvisalinkDevice

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    SIGNAL_KEYPAD_UPDATE,
    SIGNAL_PARTITION_UPDATE,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Perform the setup for Envisalink sensor entities."""
    entities = []
    async_add_entities(entities)


class EnvisalinkSensor(EnvisalinkDevice, SensorEntity):
    """Representation of an Envisalink keypad."""

    def __init__(self, hass, partition_name, partition_number, info, controller):
        """Initialize the sensor."""
        self._icon = "mdi:alarm"
        self._partition_number = partition_number

        _LOGGER.debug("Setting up sensor for partition: %s", partition_name)
        super().__init__(f"{partition_name} Keypad", info, controller)

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_KEYPAD_UPDATE, self.async_update_callback
            )
        )
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_PARTITION_UPDATE, self.async_update_callback
            )
        )

    @property
    def icon(self) -> str | None:
        """Return the icon if any."""
        return self._icon

    @property
    def native_value(self) -> str:
        """Return the overall state."""
        return self._info["status"]["alpha"]

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return the state attributes."""
        return self._info["status"]

    @callback
    def async_update_callback(self, partition):
        """Update the partition state in HA, if needed."""
        if partition is None or int(partition) == self._partition_number:
            self.async_write_ha_state()
