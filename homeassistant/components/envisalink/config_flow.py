"""Config flow to configure the envisalink integration."""
from __future__ import annotations

import asyncio

from pyenvisalink import EnvisalinkAlarmPanel
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.envisalink.bridge import EnvisalinkDevice
from homeassistant.const import (
    CONF_CODE,
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_TIMEOUT,
    CONF_USERNAME,
    EVENT_HOMEASSISTANT_STOP,
)
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult


from .const import (
    _LOGGER,
    CONF_DEFAULT_EVL_VERSION,
    CONF_DEFAULT_KEEPALIVE,
    CONF_DEFAULT_PANIC,
    CONF_DEFAULT_PORT,
    CONF_DEFAULT_TIMEOUT,
    CONF_DEFAULT_USERNAME,
    CONF_DEFAULT_ZONEDUMP_INTERVAL,
    CONF_EVL_KEEPALIVE,
    CONF_EVL_VERSION,
    CONF_PANEL_TYPE,
    CONF_PANIC,
    CONF_PANIC_AMBULANCE,
    CONF_PANIC_FIRE,
    CONF_PANIC_POLICE,
    CONF_ZONEDUMP_INTERVAL,
    DOMAIN,
    PANEL_TYPE_DSC,
    PANEL_TYPE_HONEYWELL,
)


class EnvisalinkConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a envisalink config flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the Envisalink flow."""
        self.mac_address: str | None = None

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Create config entry. Show the setup form to the user."""
        errors = {}

        if user_input is not None:
            valid = await self.is_valid(**user_input)
            if valid:
                if not self.unique_id and self.mac_address:
                    await self.async_set_unique_id(
                        self.mac_address, raise_on_progress=False
                    )
                return self.async_create_entry(
                    title=f"Envisalink {self.mac_address}",
                    data=user_input,
                )

            errors["base"] = "invalid_auth"

        data_schema = {
            vol.Required(CONF_HOST): str,
            vol.Required(CONF_USERNAME, default=CONF_DEFAULT_USERNAME): str,
            vol.Required(CONF_PASSWORD): str,
            vol.Required(
                CONF_PORT,
                default=CONF_DEFAULT_PORT,
            ): int,
            vol.Required(CONF_PANEL_TYPE): vol.In(
                [PANEL_TYPE_DSC, PANEL_TYPE_HONEYWELL]
            ),
            vol.Required(CONF_EVL_VERSION, default=CONF_DEFAULT_EVL_VERSION): vol.In(
                [3, 4]
            ),
        }
        return self.async_show_form(
            step_id="user", data_schema=vol.Schema(data_schema), errors=errors
        )

    # todo:
    # change def connection_lost(self, exc): in pyenvisalink/envisalink_base_client.py so that
    # if we get disconnected during login to to existing connections, we don't retry/keep the socket
    # open.
    # todo:
    # introduce options config flow as second step
    # todo:
    # remove polling for zone status - introduce all the zones
    async def is_valid(self, **kwargs) -> bool:
        """Check if login credentials are valid."""
        hass = self.hass
        loop = hass.loop
        host = kwargs[CONF_HOST]
        port = kwargs[CONF_PORT]
        user_name = kwargs[CONF_USERNAME]
        password = kwargs[CONF_PASSWORD]
        timeout = CONF_DEFAULT_TIMEOUT
        controller = EnvisalinkAlarmPanel(
            host=host,
            port=port,
            userName=user_name,
            password=password,
            panelType=kwargs[CONF_PANEL_TYPE],
            envisalinkVersion=kwargs[CONF_EVL_VERSION],
            connectionTimeout=timeout,
            eventLoop=loop,
        )
        sync_connect: asyncio.Future[bool] = loop.create_future()
        login_future: asyncio.Future[bool] = loop.create_future()

        @callback
        def stop_envisalink(event):
            """Shutdown envisalink connection and thread on exit."""
            _LOGGER.info("Shutting down Envisalink")
            controller.stop()

        @callback
        def async_login_fail_callback(data):
            """Handle when the evl rejects our login."""
            _LOGGER.error("The Envisalink rejected your credentials")
            if not sync_connect.done():
                login_future.set_result(False)
                sync_connect.set_result(False)

        @callback
        def async_connection_fail_callback(data):
            """Network failure callback."""
            _LOGGER.error(
                "Could not establish a connection with the Envisalink- retrying"
            )
            if not sync_connect.done():
                login_future.set_result(False)
                hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, stop_envisalink)
                sync_connect.set_result(True)

        @callback
        def async_connection_success_callback(data):
            """Handle a successful connection."""
            _LOGGER.info("Established a connection with the Envisalink")
            if not sync_connect.done():
                login_future.set_result(True)
                hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, stop_envisalink)
                sync_connect.set_result(True)

        controller.callback_login_failure = async_login_fail_callback
        controller.callback_login_timeout = async_connection_fail_callback
        controller.callback_login_success = async_connection_success_callback
        controller.start()
        try:
            login_result = await asyncio.wait_for(login_future, timeout=timeout * 2)
            if not login_result:
                return False
        except asyncio.TimeoutError:
            return False
        finally:
            stop_envisalink(None)
        self.mac_address = EnvisalinkDevice.bridge_mac_address(
            hass, host, user_name, password
        )
        return True

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> EnvisalinkOptionsFlowHandler:
        """Options callback for envisalink."""
        return EnvisalinkOptionsFlowHandler(config_entry)


class EnvisalinkOptionsFlowHandler(config_entries.OptionsFlow):
    """Config flow options for envisalink."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        """Initialize envisalink options flow."""
        self.config_entry = entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title=DOMAIN, data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_PANIC,
                        default=self.config_entry.options.get(
                            CONF_PANIC, CONF_DEFAULT_PANIC
                        ),
                    ): vol.In(
                        [CONF_PANIC_AMBULANCE, CONF_PANIC_FIRE, CONF_PANIC_POLICE]
                    ),
                    vol.Required(
                        CONF_EVL_KEEPALIVE,
                        default=self.config_entry.options.get(
                            CONF_EVL_KEEPALIVE, CONF_DEFAULT_KEEPALIVE
                        ),
                    ): int,
                    vol.Required(
                        CONF_ZONEDUMP_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_ZONEDUMP_INTERVAL, CONF_DEFAULT_ZONEDUMP_INTERVAL
                        ),
                    ): int,
                    vol.Optional(CONF_CODE): int,
                    vol.Optional(CONF_TIMEOUT, default=CONF_DEFAULT_TIMEOUT): int,
                }
            ),
        )
