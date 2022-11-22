"""Handle Envisalink Service calls."""
from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.const import ATTR_DEVICE_ID

from homeassistant.core import HomeAssistant, ServiceCall
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.service import verify_domain_control

from .const import (
    ATTR_CUSTOM_FUNCTION,
    ATTR_PARTITION,
    DOMAIN,
    SERVICE_CUSTOM_FUNCTION,
)

LOGGER = logging.getLogger(__name__)


SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): cv.string,
        vol.Required(ATTR_CUSTOM_FUNCTION): cv.string,
        vol.Required(ATTR_PARTITION): cv.string,
    }
)


def async_register_services(hass: HomeAssistant) -> None:
    """Register services for Envisalink."""

    async def handle_custom_function(call: ServiceCall) -> None:
        """Handle custom/PGM service."""
        device_id = call.data.get(ATTR_DEVICE_ID)
        partition = call.data.get(ATTR_PARTITION)
        custom_function = call.data.get(ATTR_CUSTOM_FUNCTION)
        # TODO - lookup controller from device_id
        # controller.command_output(code, partition, custom_function)

    if not hass.services.has_service(DOMAIN, SERVICE_CUSTOM_FUNCTION):
        # Register a local handler for scene activation
        hass.services.async_register(
            DOMAIN,
            SERVICE_CUSTOM_FUNCTION,
            verify_domain_control(hass, DOMAIN)(handle_custom_function),
            schema=SERVICE_SCHEMA,
        )
