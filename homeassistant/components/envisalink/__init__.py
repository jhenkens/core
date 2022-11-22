"""Support for Envisalink devices."""

from .bridge import Envisalink
from .services import async_register_services
from homeassistant.config_entries import ConfigEntry

from homeassistant.core import HomeAssistant
import homeassistant.helpers.device_registry as dr

from .const import (
    CONF_EVL_VERSION,
    DOMAIN,
    _LOGGER,
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up for Envisalink device from config entry"""
    envisalink = Envisalink(hass, entry)
    controller = envisalink.controller

    async_register_services(hass)

    _LOGGER.info("Start envisalink")
    controller.start()

    # if not await sync_connect:
    #     return False

    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, envisalink.mac_address)},
        identifiers={(DOMAIN, envisalink.mac_address)},
        manufacturer="EyezOn",
        name="Envisalink",
        model=f"EVL{str(entry.get(CONF_EVL_VERSION))}",
    )

    return True
