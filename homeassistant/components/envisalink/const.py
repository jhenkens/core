"""Support for Envisalink devices."""
import homeassistant.helpers.config_validation as cv
import logging
import voluptuous as vol

DOMAIN = "envisalink"


CONF_EVL_KEEPALIVE = "keepalive_interval"
CONF_EVL_VERSION = "evl_version"
CONF_PANEL_TYPE = "panel_type"
CONF_PANIC = "panic_type"
CONF_PARTITIONNAME = "name"
CONF_PARTITIONS = "partitions"
CONF_ZONEDUMP_INTERVAL = "zonedump_interval"
CONF_ZONENAME = "name"
CONF_ZONES = "zones"
CONF_ZONETYPE = "type"
CONF_ARM_HOME_MODE = "arm_home_mode"
CONF_OUTPUTS = "outputs"


DATA_EVL = "envisalink"
PANEL_TYPE_HONEYWELL = "HONEYWELL"
PANEL_TYPE_DSC = "DSC"

CONF_PANIC_AMBULANCE = "Ambulance"
CONF_PANIC_FIRE = "Fire"
CONF_PANIC_POLICE = "Police"

CONF_DEFAULT_USERNAME = "user"
CONF_DEFAULT_PORT = 4025
CONF_DEFAULT_EVL_VERSION = 4
CONF_DEFAULT_KEEPALIVE = 60
CONF_DEFAULT_ZONEDUMP_INTERVAL = 30
CONF_DEFAULT_ZONETYPE = "opening"
CONF_DEFAULT_PANIC = CONF_PANIC_POLICE
CONF_DEFAULT_TIMEOUT = 10

SERVICE_CUSTOM_FUNCTION = "invoke_custom_function"
ATTR_PARTITION = "partition"
ATTR_CUSTOM_FUNCTION = "pgm"

_LOGGER = logging.getLogger(__name__)


SIGNAL_ZONE_UPDATE = "envisalink.zones_updated"
SIGNAL_PARTITION_UPDATE = "envisalink.partition_updated"
SIGNAL_KEYPAD_UPDATE = "envisalink.keypad_updated"
SIGNAL_ZONE_BYPASS_UPDATE = "envisalink.zone_bypass_updated"

ZONE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ZONENAME): cv.string,
        vol.Optional(CONF_ZONETYPE, default=CONF_DEFAULT_ZONETYPE): cv.string,
    }
)
PARTITION_SCHEMA = vol.Schema({vol.Required(CONF_PARTITIONNAME): cv.string})
