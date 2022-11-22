"""Code to handle an Envisalink bridge."""
from __future__ import annotations

import logging
import re

import aiohttp
from pyenvisalink import EnvisalinkAlarmPanel

from homeassistant import core
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_TIMEOUT,
    CONF_USERNAME,
    Platform,
)
from homeassistant.helpers import aiohttp_client
import homeassistant.helpers.device_registry as dr

from .const import (
    _LOGGER,
    CONF_EVL_KEEPALIVE,
    CONF_EVL_VERSION,
    CONF_PANEL_TYPE,
    CONF_ZONEDUMP_INTERVAL,
    DOMAIN,
)

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR, Platform.ALARM_CONTROL_PANEL]


class Envisalink:
    """Manages a single Envisalink bridge."""

    @classmethod
    async def bridge_mac_address(
        cls, hass: core.HomeAssistant, host: str, username: str, password: str
    ):
        """Uses the http API to get the MAC address for the Envisalink bridge"""
        try:
            session = aiohttp_client.async_get_clientsession(hass)
            async with session.get(
                f"http://{host}/3",
                raise_for_status=True,
                timeout=10,
                auth=aiohttp.BasicAuth(username, password),
            ) as resp:
                response_text = await resp.text()
            mac_address = re.findall(r"MAC: ([A-F0-9]{12})", response_text)[0]
            _LOGGER.debug("Found mac: %s", mac_address)
            return dr.format_mac(mac_address)
        except aiohttp.ClientError as err:
            _LOGGER.warning("Failed to get envisalink Network status page: %s", err)
            return None

    def __init__(self, hass: core.HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the system."""
        self.config_entry: ConfigEntry = config_entry
        self.hass = hass
        self.authorized = False
        # Jobs to be executed when API is reset.
        self.reset_jobs: list[core.CALLBACK_TYPE] = []
        self.logger = logging.getLogger(__name__)

        host = self.config_entry.get(CONF_HOST)
        port = self.config_entry.get(CONF_PORT)
        panel_type = self.config_entry.get(CONF_PANEL_TYPE)
        version = self.config_entry.get(CONF_EVL_VERSION)
        user = self.config_entry.get(CONF_USERNAME)
        password = self.config_entry.get(CONF_PASSWORD)
        keep_alive = self.config_entry.get(CONF_EVL_KEEPALIVE)
        zone_dump = self.config_entry.get(CONF_ZONEDUMP_INTERVAL)
        connection_timeout = self.config_entry.get(CONF_TIMEOUT)

        self.controller = EnvisalinkAlarmPanel(
            host=host,
            port=port,
            panelType=panel_type,
            envisalinkVersion=version,
            userName=user,
            password=password,
            zoneTimerInterval=zone_dump,
            keepAliveInterval=keep_alive,
            eventLoop=hass.loop,
            connectionTimeout=connection_timeout,
            zoneBypassEnabled=False,
        )
        self.mac_address = Envisalink.bridge_mac_address(hass, host, user, password)
        # store (this) bridge object in hass data
        hass.data.setdefault(DOMAIN, {})[self.config_entry.entry_id] = self

    @property
    def host(self) -> str:
        """Return the host of this bridge."""
        return self.config_entry.data[CONF_HOST]

    async def async_initialize_bridge(self) -> bool:
        """Initialize Connection with the Envisalink TPI."""
        # try:
        #     with async_timeout.timeout(10):
        #         await self.api.initialize()

        # except (LinkButtonNotPressed, Unauthorized):
        #     # Usernames can become invalid if hub is reset or user removed.
        #     # We are going to fail the config entry setup and initiate a new
        #     # linking procedure. When linking succeeds, it will remove the
        #     # old config entry.
        #     create_config_flow(self.hass, self.host)
        #     return False
        # except (
        #     asyncio.TimeoutError,
        #     client_exceptions.ClientOSError,
        #     client_exceptions.ServerDisconnectedError,
        #     client_exceptions.ContentTypeError,
        #     BridgeBusy,
        # ) as err:
        #     raise ConfigEntryNotReady(
        #         f"Error connecting to the Hue bridge at {self.host}"
        #     ) from err
        # except Exception:  # pylint: disable=broad-except
        #     self.logger.exception("Unknown error connecting to Hue bridge")
        #     return False

        # await async_setup_devices(self)
        # await async_setup_hue_events(self)
        await self.hass.config_entries.async_forward_entry_setups(
            self.config_entry, PLATFORMS
        )

        # add listener for config entry updates.
        self.reset_jobs.append(self.config_entry.add_update_listener(_update_listener))
        self.authorized = True
        return True

    async def async_reset(self) -> bool:
        """Reset this bridge to default state.

        Will cancel any scheduled setup retry and will unload
        the config entry.
        """
        # The bridge can be in 3 states:
        #  - Setup was successful, self.api is not None
        #  - Authentication was wrong, self.api is None, not retrying setup.

        # If the authentication was wrong.
        if self.controller is None:
            return True

        while self.reset_jobs:
            self.reset_jobs.pop()()

        # Unload platforms
        unload_success = await self.hass.config_entries.async_unload_platforms(
            self.config_entry, PLATFORMS
        )

        if unload_success:
            self.hass.data[DOMAIN].pop(self.config_entry.entry_id)

        return unload_success

    async def handle_unauthorized_error(self) -> None:
        """Create a new config flow when the authorization is no longer valid."""
        if not self.authorized:
            # we already created a new config flow, no need to do it again
            return
        self.logger.error(
            "Unable to authorize to bridge %s, setup the linking again", self.host
        )
        self.authorized = False
        create_config_flow(self.hass, self.host)


async def _update_listener(hass: core.HomeAssistant, entry: ConfigEntry) -> None:
    """Handle ConfigEntry options update."""
    await hass.config_entries.async_reload(entry.entry_id)


def create_config_flow(hass: core.HomeAssistant, host: str) -> None:
    """Start a config flow."""
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_IMPORT},
            data={"host": host},
        )
    )
