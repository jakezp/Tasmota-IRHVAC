"""Climate platform for Tasmota IRHVAC integration."""
from __future__ import annotations

# Standard library imports
import asyncio
import json
import logging
import uuid

# Third-party imports
import voluptuous as vol

# Home Assistant core imports
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    cached_property,
    callback,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import event as ha_event
from homeassistant.helpers.restore_state import RestoreEntity
import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util

# Home Assistant component imports
from homeassistant.components import mqtt
try:
    from homeassistant.components.mqtt.schemas import MQTT_ENTITY_COMMON_SCHEMA
except ImportError:
    from homeassistant.components.mqtt.mixins import MQTT_ENTITY_COMMON_SCHEMA

# Climate related imports
from homeassistant.components.climate import (
    PLATFORM_SCHEMA as CLIMATE_PLATFORM_SCHEMA,
    ClimateEntity,
)
from homeassistant.components.climate.const import (
    FAN_AUTO,
    FAN_DIFFUSE,
    FAN_FOCUS,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_MIDDLE,
    FAN_OFF,
    FAN_ON,
    HVACMode,
    HVACAction,
    ATTR_PRESET_MODE,
    ATTR_FAN_MODE,
    ATTR_SWING_MODE,
    ATTR_HVAC_MODE,
    PRESET_AWAY,
    PRESET_ECO,
    PRESET_NONE,
    ClimateEntityFeature,
    SWING_BOTH,
    SWING_HORIZONTAL,
    SWING_OFF,
    SWING_VERTICAL,
)

# Home Assistant const imports
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_TEMPERATURE,
    CONF_NAME,
    CONF_UNIQUE_ID,
    PRECISION_HALVES,
    PRECISION_TENTHS,
    PRECISION_WHOLE,
    STATE_ON,
    STATE_OFF,
    STATE_UNKNOWN,
    STATE_UNAVAILABLE,
    UnitOfTemperature,
)

# Local imports
from .const import (
    ATTR_ECONO,
    ATTR_TURBO,
    ATTR_QUIET,
    ATTR_LIGHT,
    ATTR_FILTERS,
    ATTR_CLEAN,
    ATTR_BEEP,
    ATTR_SLEEP,
    ATTR_SWINGV,
    ATTR_SWINGH,
    ATTR_LAST_ON_MODE,
    ATTR_STATE_MODE,
    ATTRIBUTES_IRHVAC,
    CONF_AVAILABILITY_TOPIC,
    STATE_AUTO,
    HVAC_FAN_AUTO,
    HVAC_FAN_MIN,
    HVAC_FAN_MEDIUM,
    HVAC_FAN_MAX,
    HVAC_MODE_AUTO_FAN,
    HVAC_MODE_FAN_AUTO,
    HVAC_FAN_MAX_HIGH,
    HVAC_FAN_AUTO_MAX,
    HVAC_MODES,
    CONF_EXCLUSIVE_GROUP_VENDOR,
    CONF_VENDOR,
    CONF_PROTOCOL,
    CONF_COMMAND_TOPIC,
    CONF_STATE_TOPIC,
    CONF_TEMP_SENSOR,
    CONF_HUMIDITY_SENSOR,
    CONF_POWER_SENSOR,
    CONF_MQTT_DELAY,
    CONF_MIN_TEMP,
    CONF_MAX_TEMP,
    CONF_TARGET_TEMP,
    CONF_INITIAL_OPERATION_MODE,
    CONF_AWAY_TEMP,
    CONF_PRECISION,
    CONF_TEMP_STEP,
    CONF_MODES_LIST,
    CONF_FAN_LIST,
    CONF_SWING_LIST,
    CONF_QUIET,
    CONF_TURBO,
    CONF_ECONO,
    CONF_MODEL,
    CONF_CELSIUS,
    CONF_LIGHT,
    CONF_FILTER,
    CONF_CLEAN,
    CONF_BEEP,
    CONF_SLEEP,
    CONF_KEEP_MODE,
    CONF_SWINGV,
    CONF_SWINGH,
    CONF_TOGGLE_LIST,
    CONF_IGNORE_OFF_TEMP,
    DATA_KEY,
    DOMAIN,
    DEFAULT_NAME,
    DEFAULT_STATE_TOPIC,
    DEFAULT_COMMAND_TOPIC,
    DEFAULT_MQTT_DELAY,
    DEFAULT_TARGET_TEMP,
    DEFAULT_MIN_TEMP,
    DEFAULT_MAX_TEMP,
    DEFAULT_PRECISION,
    DEFAULT_FAN_LIST,
    DEFAULT_MODES_LIST,  # Explicitly importing DEFAULT_MODES_LIST from const.py
    DEFAULT_CONF_QUIET,
    DEFAULT_CONF_TURBO,
    DEFAULT_CONF_ECONO,
    DEFAULT_CONF_MODEL,
    DEFAULT_CONF_CELSIUS,
    DEFAULT_CONF_LIGHT,
    DEFAULT_CONF_FILTER,
    DEFAULT_CONF_CLEAN,
    DEFAULT_CONF_BEEP,
    DEFAULT_CONF_SLEEP,
    DEFAULT_CONF_KEEP_MODE,
    DEFAULT_STATE_MODE,
    DEFAULT_IGNORE_OFF_TEMP,
    ON_OFF_LIST,
    STATE_MODE_LIST,
    SERVICE_ECONO_MODE,
    SERVICE_TURBO_MODE,
    SERVICE_QUIET_MODE,
    SERVICE_LIGHT_MODE,
    SERVICE_FILTERS_MODE,
    SERVICE_CLEAN_MODE,
    SERVICE_BEEP_MODE,
    SERVICE_SLEEP_MODE,
    SERVICE_SET_SWINGV,
    SERVICE_SET_SWINGH,
    TOGGLE_ALL_LIST,
)

# Add OFF mode to the default modes list
# This ensures the OFF button/mode is available in the UI
# When OFF mode is selected, 'Power' is set to 'Off' in the MQTT payload
DEFAULT_MODES_LIST_WITH_OFF = [HVACMode.OFF] + list(DEFAULT_MODES_LIST)

DEFAULT_SWING_LIST = [SWING_OFF, SWING_VERTICAL]
DEFAULT_INITIAL_OPERATION_MODE = HVACMode.OFF

_LOGGER = logging.getLogger(__name__)

SUPPORT_FLAGS = ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE

if hasattr(ClimateEntityFeature, "TURN_ON"):
    SUPPORT_FLAGS |= ClimateEntityFeature.TURN_ON | ClimateEntityFeature.TURN_OFF

PLATFORM_SCHEMA = CLIMATE_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_UNIQUE_ID): cv.string,
        vol.Exclusive(CONF_VENDOR, CONF_EXCLUSIVE_GROUP_VENDOR): cv.string,
        vol.Exclusive(CONF_PROTOCOL, CONF_EXCLUSIVE_GROUP_VENDOR): cv.string,
        vol.Required(
            CONF_COMMAND_TOPIC, default=DEFAULT_COMMAND_TOPIC
        ): mqtt.valid_publish_topic,
        vol.Optional(CONF_AVAILABILITY_TOPIC): mqtt.util.valid_topic,
        vol.Optional(CONF_TEMP_SENSOR): cv.entity_id,
        vol.Optional(CONF_HUMIDITY_SENSOR): cv.entity_id,
        vol.Optional(CONF_POWER_SENSOR): cv.entity_id,
        vol.Optional(
            CONF_STATE_TOPIC, default=DEFAULT_STATE_TOPIC
        ): mqtt.valid_subscribe_topic,
        vol.Optional(CONF_STATE_TOPIC + "_2"): mqtt.util.valid_topic,
        vol.Optional(CONF_MQTT_DELAY, default=DEFAULT_MQTT_DELAY): vol.Coerce(float),
        vol.Optional(CONF_MAX_TEMP, default=DEFAULT_MAX_TEMP): vol.Coerce(float),
        vol.Optional(CONF_MIN_TEMP, default=DEFAULT_MIN_TEMP): vol.Coerce(float),
        vol.Optional(CONF_TARGET_TEMP, default=DEFAULT_TARGET_TEMP): vol.Coerce(float),
        vol.Optional(
            CONF_INITIAL_OPERATION_MODE, default=DEFAULT_INITIAL_OPERATION_MODE
        ): vol.In(HVAC_MODES),
        vol.Optional(CONF_AWAY_TEMP): vol.Coerce(float),
        vol.Optional(CONF_PRECISION, default=DEFAULT_PRECISION): vol.In(
            [PRECISION_TENTHS, PRECISION_HALVES, PRECISION_WHOLE]
        ),
        vol.Optional(CONF_TEMP_STEP, default=PRECISION_WHOLE): vol.In(
            [PRECISION_HALVES, PRECISION_WHOLE]
        ),
        vol.Optional(CONF_MODES_LIST, default=DEFAULT_MODES_LIST_WITH_OFF): vol.All(
            cv.ensure_list, [vol.In(HVAC_MODES)]
        ),
        vol.Optional(CONF_FAN_LIST, default=DEFAULT_FAN_LIST): vol.All(
            cv.ensure_list,
            [
                vol.In(
                    [
                        FAN_ON,
                        FAN_OFF,
                        FAN_AUTO,
                        FAN_LOW,
                        FAN_MEDIUM,
                        FAN_HIGH,
                        FAN_MIDDLE,
                        FAN_FOCUS,
                        FAN_DIFFUSE,
                        HVAC_FAN_MIN,
                        HVAC_FAN_MEDIUM,
                        HVAC_FAN_MAX,
                        HVAC_FAN_AUTO,
                        HVAC_FAN_MAX_HIGH,
                        HVAC_FAN_AUTO_MAX,
                    ]
                )
            ],
        ),
        vol.Optional(CONF_SWING_LIST, default=DEFAULT_SWING_LIST): vol.All(
            cv.ensure_list,
            [vol.In([SWING_OFF, SWING_BOTH, SWING_VERTICAL, SWING_HORIZONTAL])],
        ),
        vol.Optional(CONF_QUIET, default=DEFAULT_CONF_QUIET): cv.string,
        vol.Optional(CONF_TURBO, default=DEFAULT_CONF_TURBO): cv.string,
        vol.Optional(CONF_ECONO, default=DEFAULT_CONF_ECONO): cv.string,
        vol.Optional(CONF_MODEL, default=DEFAULT_CONF_MODEL): cv.string,
        vol.Optional(CONF_CELSIUS, default=DEFAULT_CONF_CELSIUS): cv.string,
        vol.Optional(CONF_LIGHT, default=DEFAULT_CONF_LIGHT): cv.string,
        vol.Optional(CONF_FILTER, default=DEFAULT_CONF_FILTER): cv.string,
        vol.Optional(CONF_CLEAN, default=DEFAULT_CONF_CLEAN): cv.string,
        vol.Optional(CONF_BEEP, default=DEFAULT_CONF_BEEP): cv.string,
        vol.Optional(CONF_SLEEP, default=DEFAULT_CONF_SLEEP): cv.string,
        vol.Optional(CONF_KEEP_MODE, default=DEFAULT_CONF_KEEP_MODE): cv.boolean,
        vol.Optional(CONF_SWINGV): cv.string,
        vol.Optional(CONF_SWINGH): cv.string,
        vol.Optional(CONF_TOGGLE_LIST, default=[]): vol.All(
            cv.ensure_list,
            [vol.In(TOGGLE_ALL_LIST)],
        ),
        vol.Optional(CONF_IGNORE_OFF_TEMP, default=DEFAULT_IGNORE_OFF_TEMP): cv.boolean,
    }
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(MQTT_ENTITY_COMMON_SCHEMA.schema)
if hasattr(mqtt, "MQTT_BASE_PLATFORM_SCHEMA"):
    PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(mqtt.MQTT_BASE_PLATFORM_SCHEMA.schema)
else:
    PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(mqtt.config.MQTT_BASE_SCHEMA.schema)

IRHVAC_SERVICE_SCHEMA = vol.Schema({vol.Required(ATTR_ENTITY_ID): cv.entity_ids})

SERVICE_SCHEMA_ECONO_MODE = IRHVAC_SERVICE_SCHEMA.extend(
    {
        vol.Required(ATTR_ECONO): vol.In(ON_OFF_LIST),
        vol.Optional(ATTR_STATE_MODE, default=DEFAULT_STATE_MODE): vol.In(
            STATE_MODE_LIST
        ),
    }
)
SERVICE_SCHEMA_TURBO_MODE = IRHVAC_SERVICE_SCHEMA.extend(
    {
        vol.Required(ATTR_TURBO): vol.In(ON_OFF_LIST),
        vol.Optional(ATTR_STATE_MODE, default=DEFAULT_STATE_MODE): vol.In(
            STATE_MODE_LIST
        ),
    }
)
SERVICE_SCHEMA_QUIET_MODE = IRHVAC_SERVICE_SCHEMA.extend(
    {
        vol.Required(ATTR_QUIET): vol.In(ON_OFF_LIST),
        vol.Optional(ATTR_STATE_MODE, default=DEFAULT_STATE_MODE): vol.In(
            STATE_MODE_LIST
        ),
    }
)
SERVICE_SCHEMA_LIGHT_MODE = IRHVAC_SERVICE_SCHEMA.extend(
    {
        vol.Required(ATTR_LIGHT): vol.In(ON_OFF_LIST),
        vol.Optional(ATTR_STATE_MODE, default=DEFAULT_STATE_MODE): vol.In(
            STATE_MODE_LIST
        ),
    }
)
SERVICE_SCHEMA_FILTERS_MODE = IRHVAC_SERVICE_SCHEMA.extend(
    {
        vol.Required(ATTR_FILTERS): vol.In(ON_OFF_LIST),
        vol.Optional(ATTR_STATE_MODE, default=DEFAULT_STATE_MODE): vol.In(
            STATE_MODE_LIST
        ),
    }
)
SERVICE_SCHEMA_CLEAN_MODE = IRHVAC_SERVICE_SCHEMA.extend(
    {
        vol.Required(ATTR_CLEAN): vol.In(ON_OFF_LIST),
        vol.Optional(ATTR_STATE_MODE, default=DEFAULT_STATE_MODE): vol.In(
            STATE_MODE_LIST
        ),
    }
)
SERVICE_SCHEMA_BEEP_MODE = IRHVAC_SERVICE_SCHEMA.extend(
    {
        vol.Required(ATTR_BEEP): vol.In(ON_OFF_LIST),
        vol.Optional(ATTR_STATE_MODE, default=DEFAULT_STATE_MODE): vol.In(
            STATE_MODE_LIST
        ),
    }
)
SERVICE_SCHEMA_SLEEP_MODE = IRHVAC_SERVICE_SCHEMA.extend(
    {
        vol.Required(ATTR_SLEEP): cv.string,
        vol.Optional(ATTR_STATE_MODE, default=DEFAULT_STATE_MODE): vol.In(
            STATE_MODE_LIST
        ),
    }
)
SERVICE_SCHEMA_SET_SWINGV = IRHVAC_SERVICE_SCHEMA.extend(
    {
        vol.Required(ATTR_SWINGV): vol.In(
            ["off", "auto", "highest", "high", "middle", "low", "lowest"]
        ),
        vol.Optional(ATTR_STATE_MODE, default=DEFAULT_STATE_MODE): vol.In(
            STATE_MODE_LIST
        ),
    }
)
SERVICE_SCHEMA_SET_SWINGH = IRHVAC_SERVICE_SCHEMA.extend(
    {
        vol.Required(ATTR_SWINGH): vol.In(
            ["off", "auto", "left max", "left", "middle", "right", "right max", "wide"]
        ),
        vol.Optional(ATTR_STATE_MODE, default=DEFAULT_STATE_MODE): vol.In(
            STATE_MODE_LIST
        ),
    }
)

SERVICE_TO_METHOD = {
    SERVICE_ECONO_MODE: {
        "method": "async_set_econo",
        "schema": SERVICE_SCHEMA_ECONO_MODE,
    },
    SERVICE_TURBO_MODE: {
        "method": "async_set_turbo",
        "schema": SERVICE_SCHEMA_TURBO_MODE,
    },
    SERVICE_QUIET_MODE: {
        "method": "async_set_quiet",
        "schema": SERVICE_SCHEMA_QUIET_MODE,
    },
    SERVICE_LIGHT_MODE: {
        "method": "async_set_light",
        "schema": SERVICE_SCHEMA_LIGHT_MODE,
    },
    SERVICE_FILTERS_MODE: {
        "method": "async_set_filters",
        "schema": SERVICE_SCHEMA_FILTERS_MODE,
    },
    SERVICE_CLEAN_MODE: {
        "method": "async_set_clean",
        "schema": SERVICE_SCHEMA_CLEAN_MODE,
    },
    SERVICE_BEEP_MODE: {
        "method": "async_set_beep",
        "schema": SERVICE_SCHEMA_BEEP_MODE,
    },
    SERVICE_SLEEP_MODE: {
        "method": "async_set_sleep",
        "schema": SERVICE_SCHEMA_SLEEP_MODE,
    },
    SERVICE_SET_SWINGV: {
        "method": "async_set_swingv",
        "schema": SERVICE_SCHEMA_SET_SWINGV,
    },
    SERVICE_SET_SWINGH: {
        "method": "async_set_swingh",
        "schema": SERVICE_SCHEMA_SET_SWINGH,
    },
}

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the generic thermostat platform."""
    vendor = config.get(CONF_VENDOR)
    protocol = config.get(CONF_PROTOCOL)
    name = config.get(CONF_NAME)

    if DATA_KEY not in hass.data:
        hass.data[DATA_KEY] = {}

    if vendor is None:
        if protocol is None:
            _LOGGER.error('Neither vendor nor protocol provided for "%s"!', name)
            return

        vendor = protocol

    tasmota_irhvac = TasmotaIrhvac(
        hass,
        vendor,
        config,
    )
    uuidstr = uuid.uuid4().hex
    hass.data[DATA_KEY][uuidstr] = tasmota_irhvac

    async_add_entities([tasmota_irhvac])

    async def async_service_handler(service):
        """Map services to methods on TasmotaIrhvac."""
        method = SERVICE_TO_METHOD.get(service.service, {})
        params = {
            key: value for key, value in service.data.items() if key != ATTR_ENTITY_ID
        }
        entity_ids = service.data.get(ATTR_ENTITY_ID)
        if entity_ids:
            devices = [
                device
                for device in hass.data[DATA_KEY].values()
                if device.entity_id in entity_ids
            ]
        else:
            devices = hass.data[DATA_KEY].values()

        update_tasks = []
        for device in devices:
            if not hasattr(device, method["method"]):
                continue
            await getattr(device, method["method"])(**params)
            update_tasks.append(asyncio.create_task(device.async_update_ha_state(True)))

        if update_tasks:
            await asyncio.wait(update_tasks)

    for irhvac_service in SERVICE_TO_METHOD:
        schema = SERVICE_TO_METHOD[irhvac_service].get("schema", IRHVAC_SERVICE_SCHEMA)
        hass.services.async_register(
            DOMAIN, irhvac_service, async_service_handler, schema=schema
        )


async def async_update_options(self, config_entry):
        """Update options."""
        await self.async_reload(config_entry)

async def async_reload(self, config_entry):
        """Reload the config entry."""
        # Merge options and data
        config = {
            **config_entry.data,
            **config_entry.options
        }

        # Update settings
        self._min_temp = config.get(CONF_MIN_TEMP, DEFAULT_MIN_TEMP)
        self._max_temp = config.get(CONF_MAX_TEMP, DEFAULT_MAX_TEMP)
        self._attr_target_temperature_step = config.get(CONF_TEMP_STEP, DEFAULT_PRECISION)
        # Update other settings as needed
        
        # Force state refresh
        await self.async_update_ha_state(force_refresh=True)

async def async_setup_entry(hass: HomeAssistant,
                          config_entry: ConfigEntry,
                          async_add_entities: AddEntitiesCallback) -> bool:
    """Set up the Tasmota IRHVAC climate device from config entry."""
    
    config = {
        # Basic configuration
        CONF_NAME: config_entry.data.get(CONF_NAME),
        CONF_VENDOR: config_entry.data.get(CONF_VENDOR),
        CONF_COMMAND_TOPIC: config_entry.data.get(CONF_COMMAND_TOPIC),
        CONF_STATE_TOPIC: config_entry.data.get(CONF_STATE_TOPIC),
        CONF_AVAILABILITY_TOPIC: config_entry.data.get(CONF_AVAILABILITY_TOPIC),
        
        # Temperature settings
        CONF_MIN_TEMP: config_entry.data.get(CONF_MIN_TEMP, DEFAULT_MIN_TEMP),
        CONF_MAX_TEMP: config_entry.data.get(CONF_MAX_TEMP, DEFAULT_MAX_TEMP),
        CONF_TARGET_TEMP: config_entry.data.get(CONF_TARGET_TEMP, DEFAULT_TARGET_TEMP),
        CONF_PRECISION: config_entry.data.get(CONF_PRECISION, DEFAULT_PRECISION),
        CONF_AWAY_TEMP: config_entry.data.get(CONF_AWAY_TEMP),
        
        # MQTT settings
        CONF_MQTT_DELAY: config_entry.data.get(CONF_MQTT_DELAY, DEFAULT_MQTT_DELAY),
        
        # Mode settings
        CONF_MODEL: config_entry.data.get(CONF_MODEL, DEFAULT_CONF_MODEL),
        CONF_MODES_LIST: config_entry.data.get(CONF_MODES_LIST, DEFAULT_MODES_LIST_WITH_OFF),
        CONF_FAN_LIST: config_entry.data.get(CONF_FAN_LIST, DEFAULT_FAN_LIST),
        CONF_SWING_LIST: config_entry.data.get(CONF_SWING_LIST, DEFAULT_SWING_LIST),
        
        # Feature settings
        CONF_QUIET: config_entry.data.get(CONF_QUIET, DEFAULT_CONF_QUIET),
        CONF_TURBO: config_entry.data.get(CONF_TURBO, DEFAULT_CONF_TURBO),
        CONF_ECONO: config_entry.data.get(CONF_ECONO, DEFAULT_CONF_ECONO),
        CONF_LIGHT: config_entry.data.get(CONF_LIGHT, DEFAULT_CONF_LIGHT),
        CONF_FILTER: config_entry.data.get(CONF_FILTER, DEFAULT_CONF_FILTER),
        CONF_CLEAN: config_entry.data.get(CONF_CLEAN, DEFAULT_CONF_CLEAN),
        CONF_BEEP: config_entry.data.get(CONF_BEEP, DEFAULT_CONF_BEEP),
        CONF_SLEEP: config_entry.data.get(CONF_SLEEP, DEFAULT_CONF_SLEEP),
        
        # Additional settings
        CONF_CELSIUS: config_entry.data.get(CONF_CELSIUS, DEFAULT_CONF_CELSIUS),
        CONF_KEEP_MODE: config_entry.data.get(CONF_KEEP_MODE, DEFAULT_CONF_KEEP_MODE),
        CONF_SWINGV: config_entry.data.get(CONF_SWINGV),
        CONF_SWINGH: config_entry.data.get(CONF_SWINGH),
        CONF_TOGGLE_LIST: config_entry.data.get(CONF_TOGGLE_LIST, []),
        CONF_IGNORE_OFF_TEMP: config_entry.data.get(CONF_IGNORE_OFF_TEMP, DEFAULT_IGNORE_OFF_TEMP),
        CONF_TEMP_STEP: config_entry.data.get(CONF_TEMP_STEP, DEFAULT_PRECISION),

        # Add preset configurations
        "enabled_presets": config_entry.data.get("enabled_presets", []),
        "default_presets": config_entry.data.get("default_presets", []),
    }

    # Optional sensor entities
    for sensor_type in [CONF_TEMP_SENSOR, CONF_HUMIDITY_SENSOR, CONF_POWER_SENSOR]:
        if sensor := config_entry.data.get(sensor_type):
            config[sensor_type] = sensor

    # Debug log the initial configuration
    _LOGGER.debug("Initial configuration data: %s", config_entry.data)
    _LOGGER.debug("Processed config: %s", config)

    
    # Update config with any options that have been set
    if config_entry.options:
        _LOGGER.debug("Found options to apply: %s", config_entry.options)
        for key, value in config_entry.options.items():
            if key in config:
                # Validate option values before applying
                if key in [CONF_MIN_TEMP, CONF_MAX_TEMP, CONF_TARGET_TEMP]:
                    try:
                        value = float(value)
                    except (TypeError, ValueError):
                        _LOGGER.warning("Invalid temperature value for %s: %s", key, value)
                        continue
                config[key] = value
                _LOGGER.debug("Updated %s to %s", key, value)

    _LOGGER.debug("Final processed config: %s", config)

    try:
        # Create the climate entity
        tasmota_irhvac = TasmotaIrhvac(
            hass,
            config[CONF_VENDOR],
            config,
        )
        async_add_entities([tasmota_irhvac])

        _LOGGER.debug("Created TasmotaIrhvac instance with presets: %s",
                     tasmota_irhvac._attr_preset_modes)
        
        # Register services
        async def async_service_handler(service: ServiceCall) -> None:
            """Map services to methods on TasmotaIrhvac."""
            method = SERVICE_TO_METHOD.get(service.service, {})
            params = {
                key: value for key, value in service.data.items() 
                if key != ATTR_ENTITY_ID
            }
            
            # Get target devices
            entity_ids = service.data.get(ATTR_ENTITY_ID)
            devices = [
                device for device in hass.data[DOMAIN].values()
                if not entity_ids or device.entity_id in entity_ids
            ]

            update_tasks = []
            for device in devices:
                if not hasattr(device, method.get("method", "")):
                    continue
                await getattr(device, method["method"])(**params)
                update_tasks.append(device.async_update_ha_state(True))

            if update_tasks:
                await asyncio.gather(*update_tasks)

        # Register all services
        for service_name, service_details in SERVICE_TO_METHOD.items():
            if not hass.services.has_service(DOMAIN, service_name):
                schema = service_details.get("schema", IRHVAC_SERVICE_SCHEMA)
                hass.services.async_register(
                    DOMAIN, 
                    service_name, 
                    async_service_handler, 
                    schema=schema
                )

        return True

    except Exception as e:
        _LOGGER.error("Error setting up Tasmota IRHVAC: %s", str(e))
        raise

class TasmotaIrhvac(RestoreEntity, ClimateEntity):
    """Representation of a Generic Thermostat device."""

    # It can remove from HA >= 2025.1
    # see https://developers.home-assistant.io/blog/2024/01/24/climate-climateentityfeatures-expanded/
    _enable_turn_on_off_backwards_compatibility = False
    _last_on_mode: HVACMode | None
    # _attr_has_entity_name = True
    # _attr_translation_key = "tasmota_irhvac"

    def __init__(self,hass,vendor,config):
        """Initialize the thermostat."""
        # Set basic attributes first
        self._attr_name = config.get(CONF_NAME)
        # Use host for unique_id if available, otherwise use command topic
        if config.get('host'):
            self._attr_unique_id = f"tasmota_irhvac_{config['host'].replace('.', '_')}"
        else:
            self._attr_unique_id = f"tasmota_irhvac_{config[CONF_COMMAND_TOPIC].replace('/', '_')}"
            _LOGGER.debug("No host provided, using command topic as unique_id")
        self._attr_should_poll = False
        
        # Add device info
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._attr_unique_id)},
            "name": self._attr_name,
            "manufacturer": "Tasmota",
            "model": f"IR HVAC ({vendor})",
            "sw_version": config.get(CONF_MODEL, DEFAULT_CONF_MODEL),
        }

        # MQTT settings
        self.topic = config.get(CONF_COMMAND_TOPIC)
        self.hass = hass
        self._vendor = vendor
        self.state_topic = config[CONF_STATE_TOPIC]
        self.state_topic2 = config.get(CONF_STATE_TOPIC + "_2")
        self.availability_topic = config.get(CONF_AVAILABILITY_TOPIC)
        if (self.availability_topic) is None:
            path = self.topic.split("/")
            self.availability_topic = "tele/" + path[1] + "/LWT"
        self._mqtt_delay = config[CONF_MQTT_DELAY]

        # Sensor configurations
        self._temp_sensor = str(config.get(CONF_TEMP_SENSOR)) if config.get(CONF_TEMP_SENSOR) else None
        self._humidity_sensor = str(config.get(CONF_HUMIDITY_SENSOR)) if config.get(CONF_HUMIDITY_SENSOR) else None
        self._power_sensor = str(config.get(CONF_POWER_SENSOR)) if config.get(CONF_POWER_SENSOR) else None
        
        # Temperature settings
        self._away_temp = config.get(CONF_AWAY_TEMP)
        self._saved_target_temp = config[CONF_TARGET_TEMP] or self._away_temp
        self._temp_precision = config[CONF_PRECISION]
        self._min_temp = config[CONF_MIN_TEMP]
        self._max_temp = config[CONF_MAX_TEMP]
        self._def_target_temp = config[CONF_TARGET_TEMP]

        # State settings
        self._enabled = False
        self.power_mode = None
        self._active = False
        self._is_away = False
        
        # Mode settings
        self._modes_list = config[CONF_MODES_LIST]
        self._attr_hvac_mode = config.get(CONF_INITIAL_OPERATION_MODE)
        self._attr_hvac_modes = config[CONF_MODES_LIST]

        # Fan settings
        self._attr_fan_modes = config.get(CONF_FAN_LIST)
        self._attr_fan_mode = (
            self._attr_fan_modes[0]
            if isinstance(self._attr_fan_modes, list) and len(self._attr_fan_modes)
            else None
        )

        # Fan quirks handling
        self._quirk_fan_max_high = all([
            isinstance(self._attr_fan_modes, list),
            HVAC_FAN_MAX_HIGH in self._attr_fan_modes,
            HVAC_FAN_AUTO_MAX in self._attr_fan_modes,
        ])

        if self._quirk_fan_max_high:
            new_fan_list = []
            for val in self._attr_fan_modes:
                if val == HVAC_FAN_MAX_HIGH:
                    new_fan_list.append(FAN_HIGH)
                elif val == HVAC_FAN_AUTO_MAX:
                    new_fan_list.append(HVAC_FAN_MAX)
                else:
                    new_fan_list.append(val)
            self._attr_fan_modes = new_fan_list if len(new_fan_list) else None

        # Set quirk_fan_prettify if we have min/max fan modes that need prettification
        self._quirk_fan_prettify = any(mode in (self._attr_fan_modes or []) for mode in [HVAC_FAN_MIN, HVAC_FAN_MAX])
        
        # Log the fan modes and prettification status
        _LOGGER.debug("Fan modes before prettification: %s", self._attr_fan_modes)
        _LOGGER.debug("Fan prettification enabled: %s", self._quirk_fan_prettify)
        
        # Apply prettification if needed
        if self._quirk_fan_prettify and self._attr_fan_modes:
            self._attr_fan_modes = [self.fan_prettify(mode) for mode in self._attr_fan_modes]
            _LOGGER.debug("Fan modes after prettification: %s", self._attr_fan_modes)
        
        # Set initial fan mode
        self._attr_fan_mode = (
            self._attr_fan_modes[0]
            if isinstance(self._attr_fan_modes, list) and len(self._attr_fan_modes)
            else None
        )

        # Swing settings
        self._attr_swing_modes = config.get(CONF_SWING_LIST)
        self._attr_swing_mode = (
            self._attr_swing_modes[0]
            if isinstance(self._attr_swing_modes, list) and len(self._attr_swing_modes)
            else None
        )

        # Feature settings
        self._quiet = config[CONF_QUIET].lower()
        self._turbo = config[CONF_TURBO].lower()
        self._econo = config[CONF_ECONO].lower()
        self._model = config[CONF_MODEL]
        self._celsius = config[CONF_CELSIUS]
        self._light = config[CONF_LIGHT].lower()
        self._filter = config[CONF_FILTER].lower()
        self._clean = config[CONF_CLEAN].lower()
        self._beep = config[CONF_BEEP].lower()
        self._sleep = config[CONF_SLEEP].lower()
        
        # FEATURE ORGANIZATION:
        # The Tasmota IRHVAC integration organizes features into two categories:
        #
        # 1. FEATURE TOGGLES:
        #    - These are additional features that can be toggled on/off independently
        #    - They don't affect the core operation mode of the AC
        #    - Examples: light, filter, clean, beep
        #    - These are controlled via service calls (e.g., tasmota_irhvac.set_light)
        #
        # 2. FEATURE PRESETS:
        #    - These are mutually exclusive operation modes
        #    - Only one preset can be active at a time
        #    - They affect how the AC operates (e.g., energy saving, maximum cooling)
        #    - Examples: econo (maps to ECO), turbo, quiet, sleep
        #    - These are controlled via the preset_mode selector in the UI
        
        # All possible feature toggles - can be toggled on/off independently
        self._feature_toggles = {
            "light": self._light,
            "filter": self._filter,
            "clean": self._clean,
            "beep": self._beep,
        }
        
        # All possible feature presets - mutually exclusive operation modes
        self._feature_presets = {
            "econo": self._econo,  # Maps to standard ECO preset
            "turbo": self._turbo,
            "quiet": self._quiet,
            "sleep": self._sleep,
        }

        # Initialize preset modes
        self._is_away = False
        self._saved_target_temp = None
        
        # Get configured presets
        enabled_presets = config.get("enabled_presets", [])
        default_presets = config.get("default_presets", [])
        
        _LOGGER.debug("Initializing with enabled presets: %s, default presets: %s",
                    enabled_presets, default_presets)

        # Initialize feature presets and toggles
        self._active_feature_presets = {}
        self._active_feature_toggles = {}
        
        for preset in enabled_presets:
            initial_state = "on" if preset in default_presets else "off"
            setattr(self, f"_{preset}", initial_state)
            
            # Determine if this is a preset or toggle feature
            if preset in self._feature_presets:
                self._active_feature_presets[preset] = initial_state
            elif preset in self._feature_toggles:
                self._active_feature_toggles[preset] = initial_state

        # Set up available preset modes
        self._attr_preset_modes = [PRESET_NONE]
        if self._away_temp is not None:
            self._attr_preset_modes.append(PRESET_AWAY)
        
        # Add feature presets (mutually exclusive modes)
        preset_features = [p for p in enabled_presets if p in self._feature_presets]
        if preset_features:
            # Ensure proper capitalization for UI display
            self._attr_preset_modes.extend(preset_features)
            
        # Add ECO preset if econo is enabled
        if "econo" in preset_features:
            self._attr_preset_modes.append(PRESET_ECO)

        # Additional settings
        self._sub_state = None
        self._keep_mode = config[CONF_KEEP_MODE]
        self._last_on_mode = None
        self._swingv = (
            config.get(CONF_SWINGV).lower()
            if config.get(CONF_SWINGV) is not None
            else None
        )
        self._swingh = (
            config.get(CONF_SWINGH).lower()
            if config.get(CONF_SWINGH) is not None
            else None
        )
        self._fix_swingv = None
        self._fix_swingh = None
        self._toggle_list = config[CONF_TOGGLE_LIST]
        self._state_mode = DEFAULT_STATE_MODE
        self._ignore_off_temp = config[CONF_IGNORE_OFF_TEMP]

        # Tracking settings
        self._use_track_state_change_event = False
        self._unsubscribes = []

        # Temperature attributes
        self._attr_target_temperature_step = config[CONF_TEMP_STEP]
        self._attr_target_temperature = None
        self._attr_current_temperature = None
        self._attr_current_humidity = None
        
        # Set temperature unit after celsius setting is initialized
        self._attr_temperature_unit = (
            UnitOfTemperature.CELSIUS
            if self._celsius.lower() == "on"
            else UnitOfTemperature.FAHRENHEIT
        )
        
        # Support flags
        self._support_flags = SUPPORT_FLAGS
        if self._away_temp is not None or self._active_feature_presets:
            self._support_flags = self._support_flags | ClimateEntityFeature.PRESET_MODE
        
        _LOGGER.debug("Initialized with preset modes: %s, Feature presets: %s, Feature toggles: %s",
                 self._attr_preset_modes, self._active_feature_presets, self._active_feature_toggles)
        
        if self._attr_swing_mode is not None:
            self._support_flags = self._support_flags | ClimateEntityFeature.SWING_MODE

    def fan_prettify(self, mode):
        """Convert internal fan mode values to display values with proper styling."""
        if not self._quirk_fan_prettify:
            return mode
        
        # Handle case insensitivity
        if isinstance(mode, str):
            mode_lower = mode.lower()
            if mode_lower == HVAC_FAN_MIN.lower():
                return FAN_LOW  # This will display as "Low" with proper icon
            if mode_lower == HVAC_FAN_MAX.lower():
                return FAN_AUTO  # This will display as "Auto" with proper icon
        
        return mode

    def fan_unprettify(self, mode):
        """Convert display values back to internal fan mode values."""
        if not self._quirk_fan_prettify:
            return mode
        
        # Handle case insensitivity
        if isinstance(mode, str):
            mode_lower = mode.lower()
            if mode_lower == FAN_LOW.lower():
                return HVAC_FAN_MIN
            if mode_lower == FAN_AUTO.lower():
                return HVAC_FAN_MAX
        
        return mode

    def regist_track_state_change_event(self, entity_id):
        """Register state change event tracking."""
        if not entity_id:
            return
            
        # Ensure entity_id is a string
        if not isinstance(entity_id, str):
            _LOGGER.error("Invalid entity_id: %s (type: %s)", entity_id, type(entity_id))
            return
        
        if self._use_track_state_change_event:
            ha_event.async_track_state_change_event(
                self.hass, [entity_id], self._async_sensor_changed
            )
        else:
            ha_event.async_track_state_change(
                self.hass, entity_id, self._async_sensor_changed
            )

    async def async_added_to_hass(self):
        """Run when entity about to be added."""
        # Replacing `async_track_state_change` with `async_track_state_change_event`
        # See, https://developers.home-assistant.io/blog/2024/04/13/deprecate_async_track_state_change/
        if hasattr(ha_event, "async_track_state_change_event"):
            self._use_track_state_change_event = True

        # Make sure MQTT integration is enabled and the client is available
        await mqtt.async_wait_for_mqtt_client(self.hass)
        await super().async_added_to_hass()

        _LOGGER.debug(
            "Entity added to hass. Preset modes: %s, Supported features: %s",
            self._attr_preset_modes,
            self._support_flags
        )

        # Add listeners for sensors if configured
        if self._temp_sensor:
            _LOGGER.debug("Setting up temperature sensor: %s", self._temp_sensor)
            self.regist_track_state_change_event(self._temp_sensor)
            if temp_state := self.hass.states.get(self._temp_sensor):
                self._async_update_temp(temp_state)

        if self._humidity_sensor:
            _LOGGER.debug("Setting up humidity sensor: %s", self._humidity_sensor)
            self.regist_track_state_change_event(self._humidity_sensor)
            if humidity_state := self.hass.states.get(self._humidity_sensor):
                self._async_update_humidity(humidity_state)

        if self._power_sensor:
            _LOGGER.debug("Setting up power sensor: %s", self._power_sensor)
            self.regist_track_state_change_event(self._power_sensor)
            if power_state := self.hass.states.get(self._power_sensor):
                await self._async_power_sensor_changed(None, power_state)

         # Add MQTT subscriptions
        self._unsubscribes = await self._subscribe_topics()

        # Restore previous state
        old_state = await self.async_get_last_state()
        if old_state is not None:
            # If we have no initial temperature, restore
            if old_state.attributes.get(ATTR_TEMPERATURE) is not None:
                self._attr_target_temperature = float(
                    old_state.attributes[ATTR_TEMPERATURE]
                )
            if old_state.attributes.get(ATTR_PRESET_MODE) == PRESET_AWAY:
                self._is_away = True
            if old_state.attributes.get(ATTR_FAN_MODE) is not None:
                self._attr_fan_mode = old_state.attributes.get(ATTR_FAN_MODE)
            if old_state.attributes.get(ATTR_SWING_MODE) is not None:
                self._attr_swing_mode = old_state.attributes.get(ATTR_SWING_MODE)
            if old_state.attributes.get(ATTR_LAST_ON_MODE) is not None:
                self._last_on_mode = old_state.attributes.get(ATTR_LAST_ON_MODE)

            for attr, prop in ATTRIBUTES_IRHVAC.items():
                val = old_state.attributes.get(attr)
                if val is not None:
                    setattr(self, "_" + prop, val)
            if old_state.state:
                self._attr_hvac_mode = (
                    HVACMode.OFF
                    if old_state.state in [STATE_UNKNOWN, STATE_UNAVAILABLE]
                    else old_state.state
                )
                self._enabled = self._attr_hvac_mode != HVACMode.OFF
                if self._enabled:
                    self._last_on_mode = self._attr_hvac_mode
            if self._swingv != "auto":
                self._fix_swingv = self._swingv
            if self._swingh != "auto":
                self._fix_swingh = self._swingh

        # No previous target temperature, try and restore defaults
        if self._attr_target_temperature is None or self._attr_target_temperature < 1:
            self._attr_target_temperature = self._def_target_temp
            _LOGGER.warning(
                "No previously saved target temperature, setting to default value %s",
                self._attr_target_temperature,
            )

        if self._attr_hvac_mode is HVACMode.OFF:
            self.power_mode = STATE_OFF
            self._enabled = False
        else:
            self.power_mode = STATE_ON
            self._enabled = True

        for key in self._toggle_list:
            setattr(self, "_" + key.lower(), "off")

        if self._temp_sensor:
            self.regist_track_state_change_event(self._temp_sensor)

            temp_sensor_state = self.hass.states.get(self._temp_sensor)
            if (
                temp_sensor_state
                and temp_sensor_state.state != STATE_UNKNOWN
                and temp_sensor_state.state != STATE_UNAVAILABLE
            ):
                self._async_update_temp(temp_sensor_state)

        if self._humidity_sensor:
            self.regist_track_state_change_event(self._humidity_sensor)

            humidity_sensor_state = self.hass.states.get(self._humidity_sensor)
            if (
                humidity_sensor_state
                and humidity_sensor_state.state != STATE_UNKNOWN
                and humidity_sensor_state.state != STATE_UNAVAILABLE
            ):
                self._async_update_humidity(humidity_sensor_state)

        if self._power_sensor:
            self.regist_track_state_change_event(self._power_sensor)

    async def _subscribe_topics(self):
        """(Re)Subscribe to topics."""
        unsubscribe = []

        @callback
        async def available_message_received(message: mqtt.ReceiveMessage) -> None:
            try:
                msg = message.payload
                _LOGGER.debug(msg)
                if msg == "Online" or msg == "Offline":
                    self._attr_available = True if msg == "Online" else False
                    self.async_schedule_update_ha_state()
            except Exception as e:
                _LOGGER.error("Error processing availability message: %s", str(e))

        @callback
        async def state_message_received(message: mqtt.ReceiveMessage) -> None:
            """Handle new MQTT state messages."""
            try:
                json_payload = json.loads(message.payload)
                _LOGGER.debug(json_payload)

                # If listening to `tele`, result looks like: {"IrReceived":{"Protocol":"XXX", ... ,"IRHVAC":{ ... }}}
                # we want to extract the data.
                if "IrReceived" in json_payload:
                    json_payload = json_payload["IrReceived"]

                # By now the payload must include an `IRHVAC` field.
                if "IRHVAC" not in json_payload:
                    return

                payload = json_payload["IRHVAC"]

                if payload["Vendor"] == self._vendor:
                    # All values in the payload are Optional
                    prev_power = self.power_mode
                    if "Power" in payload:
                        self.power_mode = payload["Power"].lower()
                    if "Mode" in payload:
                        self._attr_hvac_mode = payload["Mode"].lower()
                        # Some vendors send/receive mode as fan instead of fan_only
                        if self._attr_hvac_mode == HVACAction.FAN:
                            self._attr_hvac_mode = HVACMode.FAN_ONLY
                    if "Temp" in payload:
                        if payload["Temp"] > 0:
                            if self.power_mode == STATE_OFF and self._ignore_off_temp:
                                self._attr_target_temperature = (
                                    self._attr_target_temperature
                                )
                            else:
                                self._attr_target_temperature = payload["Temp"]
                    if "Celsius" in payload:
                        self._celsius = payload["Celsius"].lower()
                    if "Quiet" in payload:
                        self._quiet = payload["Quiet"].lower()
                    if "Turbo" in payload:
                        self._turbo = payload["Turbo"].lower()
                    if "Econo" in payload:
                        self._econo = payload["Econo"].lower()
                    if "Light" in payload:
                        self._light = payload["Light"].lower()
                    if "Filter" in payload:
                        self._filter = payload["Filter"].lower()
                    if "Clean" in payload:
                        self._clean = payload["Clean"].lower()
                    if "Beep" in payload:
                        self._beep = payload["Beep"].lower()
                    if "Sleep" in payload:
                        self._sleep = payload["Sleep"]
                    if "SwingV" in payload:
                        self._swingv = payload["SwingV"].lower()
                        if self._swingv != "auto":
                            self._fix_swingv = self._swingv
                    if "SwingH" in payload:
                        self._swingh = payload["SwingH"].lower()
                        if self._swingh != "auto":
                            self._fix_swingh = self._swingh
                    if (
                        "SwingV" in payload
                        and payload["SwingV"].lower() == STATE_AUTO
                        and "SwingH" in payload
                        and payload["SwingH"].lower() == STATE_AUTO
                    ):
                        if SWING_BOTH in (self._attr_swing_modes or []):
                            self._attr_swing_mode = SWING_BOTH
                        elif SWING_VERTICAL in (self._attr_swing_modes or []):
                            self._attr_swing_mode = SWING_VERTICAL
                        elif SWING_HORIZONTAL in (self._attr_swing_modes or []):
                            self._attr_swing_mode = SWING_HORIZONTAL
                        else:
                            self._attr_swing_mode = SWING_OFF
                    elif (
                        "SwingV" in payload
                        and payload["SwingV"].lower() == STATE_AUTO
                        and SWING_VERTICAL in (self._attr_swing_modes or [])
                    ):
                        self._attr_swing_mode = SWING_VERTICAL
                    elif (
                        "SwingH" in payload
                        and payload["SwingH"].lower() == STATE_AUTO
                        and SWING_HORIZONTAL in (self._attr_swing_modes or [])
                    ):
                        self._attr_swing_mode = SWING_HORIZONTAL
                    else:
                        self._attr_swing_mode = SWING_OFF

                    if "FanSpeed" in payload:
                        fan_mode = payload["FanSpeed"].lower()
                        _LOGGER.debug("Received fan mode from MQTT: %s", fan_mode)
                        
                        # ELECTRA_AC fan modes fix
                        if self._quirk_fan_max_high:
                            if fan_mode == HVAC_FAN_MAX:
                                self._attr_fan_mode = FAN_AUTO  # Changed from FAN_HIGH to FAN_AUTO
                            elif fan_mode == HVAC_FAN_AUTO:
                                self._attr_fan_mode = HVAC_FAN_MAX
                            else:
                                self._attr_fan_mode = self.fan_prettify(fan_mode)
                        else:
                            self._attr_fan_mode = self.fan_prettify(fan_mode)
                        
                        _LOGGER.debug("Fan mode after prettification: %s", self._attr_fan_mode)

                    if self._attr_hvac_mode is not HVACMode.OFF:
                        self._last_on_mode = self._attr_hvac_mode

                    # Set default state to off
                    if self.power_mode == STATE_OFF:
                        self._attr_hvac_mode = HVACMode.OFF
                        self._enabled = False
                    else:
                        self._enabled = True

                    # Set toggles to 'off'
                    for key in self._toggle_list:
                        setattr(self, "_" + key.lower(), "off")

                    # Update HA UI and State
                    self.async_schedule_update_ha_state()

                    # Check power sensor state
                    if (
                        self._power_sensor
                        and prev_power is not None
                        and prev_power != self.power_mode
                    ):
                        await asyncio.sleep(3)
                        state = self.hass.states.get(self._power_sensor)
                        await self._async_power_sensor_changed(None, state)
            except json.JSONDecodeError as e:
                _LOGGER.error("Error decoding MQTT message: %s", str(e))
            except KeyError as e:
                _LOGGER.error("Missing key in MQTT message: %s", str(e))
            except Exception as e:
                _LOGGER.error("Error processing MQTT message: %s", str(e))

        try:
            unsubscribe.append(
                await mqtt.async_subscribe(
                    self.hass, self.state_topic, state_message_received
                )
            )
            unsubscribe.append(
                await mqtt.async_subscribe(
                    self.hass, self.availability_topic, available_message_received
                )
            )
            if self.state_topic2:
                unsubscribe.append(
                    await mqtt.async_subscribe(
                        self.hass, self.state_topic2, state_message_received
                    )
                )
        except mqtt.MqttNotConnectedError:
            _LOGGER.error("MQTT is not connected, cannot subscribe to topics")
        except Exception as e:
            _LOGGER.error("Error subscribing to MQTT topics: %s", str(e))

        return unsubscribe

    async def async_will_remove_from_hass(self):
        """Unsubscribe when removed."""
        for unsubscribe in self._unsubscribes:
            unsubscribe()

    @property
    def precision(self):
        """Return the precision of the system."""
        if self._temp_precision is not None:
            return self._temp_precision
        return super().precision

    # This extension property is written throughout the instance, so use @property instead of @cached_property.
    @property
    def hvac_action(self):
        """Return the current running hvac operation if supported.

        Need to be one of CURRENT_HVAC_*.
        """
        if self._attr_hvac_mode == HVACMode.OFF:
            return HVACAction.OFF
        elif self._attr_hvac_mode == HVACMode.HEAT:
            return HVACAction.HEATING
        elif self._attr_hvac_mode == HVACMode.COOL:
            return HVACAction.COOLING
        elif self._attr_hvac_mode == HVACMode.DRY:
            return HVACAction.DRYING
        elif self._attr_hvac_mode == HVACMode.FAN_ONLY:
            return HVACAction.FAN

    # This extension property is written throughout the instance, so use @property instead of @cached_property.
    @property
    def extra_state_attributes(self):
        """Return the state attributes of the device."""
        return {
            attr: getattr(self, "_" + prop) for attr, prop in ATTRIBUTES_IRHVAC.items()
        }

    @property
    def last_on_mode(self):
        """Return the last non-idle mode ie. heat, cool."""
        return self._last_on_mode

    async def async_set_hvac_mode(self, hvac_mode):
        """Set hvac mode."""
        await self.set_mode(hvac_mode)
        # Ensure we update the current operation after changing the mode
        await self.async_send_cmd()

    async def async_turn_on(self):
        """Turn thermostat on."""
        self._attr_hvac_mode = (
            self._last_on_mode if self._last_on_mode is not None else HVACMode.AUTO
        )
        self.power_mode = STATE_ON
        await self.async_send_cmd()

    async def async_turn_off(self):
        """Turn thermostat off."""
        self._attr_hvac_mode = HVACMode.OFF
        self.power_mode = STATE_OFF
        await self.async_send_cmd()

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        hvac_mode = kwargs.get(ATTR_HVAC_MODE)
        if temperature is None:
            return

        if hvac_mode is not None:
            await self.set_mode(hvac_mode)

        self._attr_target_temperature = temperature
        if not self._attr_hvac_mode == HVACMode.OFF:
            self.power_mode = STATE_ON
        await self.async_send_cmd()

    async def async_set_fan_mode(self, fan_mode):
            """Set new target fan mode."""
            # First check if the fan mode is directly in the list
            if fan_mode in (self._attr_fan_modes or []):
                self._attr_fan_mode = fan_mode
            else:
                # If not found directly, check if it's a prettified mode that needs unprettifying
                unprettified_mode = self.fan_unprettify(fan_mode)
                if unprettified_mode in (self._attr_fan_modes or []):
                    self._attr_fan_mode = unprettified_mode
                else:
                    # If still not found, log error and return
                    _LOGGER.error(
                        "Invalid fan mode selected. Got '%s'. Allowed modes are: %s",
                        fan_mode,
                        ", ".join(str(mode) for mode in (self._attr_fan_modes or [])),
                    )
                    return
                    
            if not self._attr_hvac_mode == HVACMode.OFF:
                self.power_mode = STATE_ON
            await self.async_send_cmd()

    async def async_set_swing_mode(self, swing_mode):
        """Set new target swing operation."""
        if swing_mode not in (self._attr_swing_modes or []):
            _LOGGER.error(
                "Invalid swing mode selected. Got '%s'. Allowed modes are:", swing_mode
            )
            _LOGGER.error(self._attr_swing_modes)
            return
        self._attr_swing_mode = swing_mode
        # note: set _swingv and _swingh in send_ir() later
        if not self._attr_hvac_mode == HVACMode.OFF:
            self.power_mode = STATE_ON
        await self.async_send_cmd()

    @property
    def preset_modes(self) -> list[str] | None:
        """Return the list of available preset modes."""
        _LOGGER.debug("Available preset modes: %s", self._attr_preset_modes)
        return self._attr_preset_modes

    @property
    def preset_mode(self) -> str | None:
        """Return the current preset mode."""
        if self._is_away:
            return PRESET_AWAY

        # Check if any feature preset is active
        for preset, state in self._active_feature_presets.items():
            if state.lower() == "on":
                # Special case for econo - map to standard ECO preset
                if preset == "econo":
                    return PRESET_ECO
                # Return the preset name with proper capitalization
                # This ensures the UI displays it correctly with proper icons
                return preset

        return PRESET_NONE

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode.
        
        Presets are mutually exclusive operation modes:
        - AWAY: Uses away temperature
        - ECO: Energy saving mode (maps to 'econo')
        - Other feature presets: turbo, quiet, sleep
        
        This is different from toggleable features like light, filter, clean, beep
        which can be turned on/off independently via service calls.
        
        PRESET MODES vs ADDITIONAL FEATURES:
        
        Preset Modes:
        - Represent mutually exclusive operational states
        - Only one can be active at a time
        - Selected through the climate.set_preset_mode service or UI dropdown
        - Examples: Away, Eco (energy saving), Turbo (maximum performance), Quiet
        
        Additional Features:
        - Represent toggleable options that can be enabled/disabled independently
        - Multiple can be active simultaneously
        - Controlled through dedicated service calls (e.g., tasmota_irhvac.set_light)
        - Examples: Light, Filter, Clean, Beep
        """
        _LOGGER.debug("Setting preset mode to: %s", preset_mode)
        
        # Handle Away preset
        if preset_mode == PRESET_AWAY:
            if not self._is_away:
                self._is_away = True
                self._saved_target_temp = self._attr_target_temperature
                self._attr_target_temperature = self._away_temp
                
        # Handle None preset (turn off all presets)
        elif preset_mode == PRESET_NONE:
            if self._is_away:
                self._is_away = False
                self._attr_target_temperature = self._saved_target_temp
            # Turn off all feature presets
            for feature in self._active_feature_presets:
                setattr(self, f"_{feature}", "off")
                self._active_feature_presets[feature] = "off"
                
        # Handle ECO preset (maps to econo)
        elif preset_mode == PRESET_ECO and "econo" in self._active_feature_presets:
            if self._is_away:
                self._is_away = False
                self._attr_target_temperature = self._saved_target_temp
                
            # Turn on econo, turn off other feature presets
            for feature in self._active_feature_presets:
                if feature == "econo":
                    setattr(self, f"_{feature}", "on")
                    self._active_feature_presets[feature] = "on"
                else:
                    setattr(self, f"_{feature}", "off")
                    self._active_feature_presets[feature] = "off"
                    
        # Handle other feature presets
        elif preset_mode in self._active_feature_presets:
            # Turn off away mode if it's on
            if self._is_away:
                self._is_away = False
                self._attr_target_temperature = self._saved_target_temp
            
            # Turn on the selected preset, turn off other presets
            for feature in self._active_feature_presets:
                if feature == preset_mode:
                    setattr(self, f"_{feature}", "on")
                    self._active_feature_presets[feature] = "on"
                else:
                    setattr(self, f"_{feature}", "off")
                    self._active_feature_presets[feature] = "off"

        await self.async_send_cmd()

    async def async_set_econo(self, econo, state_mode=DEFAULT_STATE_MODE):
        """Set new target econo mode.
        
        This is a feature preset (mutually exclusive operation mode).
        When turned on, it will turn off other feature presets.
        """
        if econo not in ON_OFF_LIST:
            return
            
        self._econo = econo.lower()
        self._state_mode = state_mode
        
        # Update active feature presets tracking
        if "econo" in self._active_feature_presets:
            self._active_feature_presets["econo"] = econo.lower()
            
            # If turning on econo, turn off other feature presets
            if econo.lower() == "on":
                for feature in self._active_feature_presets:
                    if feature != "econo":
                        setattr(self, f"_{feature}", "off")
                        self._active_feature_presets[feature] = "off"
        
        await self.async_send_cmd()

    async def async_set_turbo(self, turbo, state_mode):
        """Set new target turbo mode.
        
        This is a feature preset (mutually exclusive operation mode).
        When turned on, it will turn off other feature presets.
        """
        if turbo not in ON_OFF_LIST:
            return
            
        self._turbo = turbo.lower()
        self._state_mode = state_mode
        
        # Update active feature presets tracking
        if "turbo" in self._active_feature_presets:
            self._active_feature_presets["turbo"] = turbo.lower()
            
            # If turning on turbo, turn off other feature presets
            if turbo.lower() == "on":
                for feature in self._active_feature_presets:
                    if feature != "turbo":
                        setattr(self, f"_{feature}", "off")
                        self._active_feature_presets[feature] = "off"
        
        await self.async_send_cmd()

    async def async_set_quiet(self, quiet, state_mode):
        """Set new target quiet mode.
        
        This is a feature preset (mutually exclusive operation mode).
        When turned on, it will turn off other feature presets.
        """
        if quiet not in ON_OFF_LIST:
            return
            
        self._quiet = quiet.lower()
        self._state_mode = state_mode
        
        # Update active feature presets tracking
        if "quiet" in self._active_feature_presets:
            self._active_feature_presets["quiet"] = quiet.lower()
            
            # If turning on quiet, turn off other feature presets
            if quiet.lower() == "on":
                for feature in self._active_feature_presets:
                    if feature != "quiet":
                        setattr(self, f"_{feature}", "off")
                        self._active_feature_presets[feature] = "off"
        
        await self.async_send_cmd()

    async def async_set_light(self, light, state_mode):
        """Set new target light mode.
        
        This is a feature toggle (can be enabled/disabled independently).
        """
        if light not in ON_OFF_LIST:
            return
            
        self._light = light.lower()
        self._state_mode = state_mode
        
        # Update active feature toggles tracking
        if "light" in self._active_feature_toggles:
            self._active_feature_toggles["light"] = light.lower()
        
        await self.async_send_cmd()

    async def async_set_filters(self, filters, state_mode):
        """Set new target filters mode.
        
        This is a feature toggle (can be enabled/disabled independently).
        """
        if filters not in ON_OFF_LIST:
            return
            
        self._filter = filters.lower()
        self._state_mode = state_mode
        
        # Update active feature toggles tracking
        if "filter" in self._active_feature_toggles:
            self._active_feature_toggles["filter"] = filters.lower()
        
        await self.async_send_cmd()

    async def async_set_clean(self, clean, state_mode):
        """Set new target clean mode.
        
        This is a feature toggle (can be enabled/disabled independently).
        """
        if clean not in ON_OFF_LIST:
            return
            
        self._clean = clean.lower()
        self._state_mode = state_mode
        
        # Update active feature toggles tracking
        if "clean" in self._active_feature_toggles:
            self._active_feature_toggles["clean"] = clean.lower()
        
        await self.async_send_cmd()

    async def async_set_beep(self, beep, state_mode):
        """Set new target beep mode.
        
        This is a feature toggle (can be enabled/disabled independently).
        """
        if beep not in ON_OFF_LIST:
            return
            
        self._beep = beep.lower()
        self._state_mode = state_mode
        
        # Update active feature toggles tracking
        if "beep" in self._active_feature_toggles:
            self._active_feature_toggles["beep"] = beep.lower()
        
        await self.async_send_cmd()

    async def async_set_sleep(self, sleep, state_mode):
        """Set new target sleep mode.
        
        This is a feature preset (mutually exclusive operation mode).
        When set, it will turn off other feature presets.
        """
        self._sleep = sleep.lower()
        self._state_mode = state_mode
        
        # Update active feature presets tracking
        if "sleep" in self._active_feature_presets:
            self._active_feature_presets["sleep"] = sleep.lower()
            
            # If setting sleep to a non-off value, turn off other feature presets
            if sleep.lower() != "off" and sleep != "-1":
                for feature in self._active_feature_presets:
                    if feature != "sleep":
                        setattr(self, f"_{feature}", "off")
                        self._active_feature_presets[feature] = "off"
        
        await self.async_send_cmd()

    async def async_set_swingv(self, swingv, state_mode):
        """Set new target swingv."""
        self._swingv = swingv.lower()
        if self._swingv != "auto":
            self._fix_swingv = self._swingv
            if self._attr_swing_mode == SWING_BOTH:
                if SWING_HORIZONTAL in (self._attr_swing_modes or []):
                    self._attr_swing_mode = SWING_HORIZONTAL
            elif self._attr_swing_mode == SWING_VERTICAL:
                self._attr_swing_mode = SWING_OFF
        else:
            if self._attr_swing_mode == SWING_HORIZONTAL:
                if SWING_BOTH in (self._attr_swing_modes or []):
                    self._attr_swing_mode = SWING_BOTH
            else:
                if SWING_VERTICAL in (self._attr_swing_modes or []):
                    self._attr_swing_mode = SWING_VERTICAL
        self._state_mode = state_mode
        await self.async_send_cmd()

    async def async_set_swingh(self, swingh, state_mode):
        """Set new target swingh."""
        self._swingh = swingh.lower()
        if self._swingh != "auto":
            self._fix_swingh = self._swingh
            if self._attr_swing_mode == SWING_BOTH:
                if SWING_VERTICAL in (self._attr_swing_modes or []):
                    self._attr_swing_mode = SWING_VERTICAL
            elif self._attr_swing_mode == SWING_HORIZONTAL:
                self._attr_swing_mode = SWING_OFF
        else:
            if self._attr_swing_mode == SWING_VERTICAL:
                if SWING_BOTH in (self._attr_swing_modes or []):
                    self._attr_swing_mode = SWING_BOTH
            else:
                if SWING_HORIZONTAL in (self._attr_swing_modes or []):
                    self._attr_swing_mode = SWING_HORIZONTAL
        self._state_mode = state_mode
        await self.async_send_cmd()

    async def async_send_cmd(self):
        await self.send_ir()

    @cached_property
    def min_temp(self):
        """Return the minimum temperature."""
        if self._min_temp:
            return self._min_temp

        # get default temp from super class
        return super().min_temp

    @cached_property
    def max_temp(self):
        """Return the maximum temperature."""
        if self._max_temp:
            return self._max_temp

        # Get default temp from super class
        return super().max_temp

    async def _async_sensor_changed(
        self, entity_id_or_event, old_state=None, new_state=None
    ):
        # Replacing `async_track_state_change` with `async_track_state_change_event`
        # See, https://developers.home-assistant.io/blog/2024/04/13/deprecate_async_track_state_change/
        if self._use_track_state_change_event:
            entity_id = entity_id_or_event.data["entity_id"]
            old_state = entity_id_or_event.data["old_state"]
            new_state = entity_id_or_event.data["new_state"]
        else:
            entity_id = entity_id_or_event

        if new_state is None:
            return

        if entity_id == self._temp_sensor:
            self._async_update_temp(new_state)
            self.async_schedule_update_ha_state()
        elif entity_id == self._humidity_sensor:
            self._async_update_humidity(new_state)
            self.async_schedule_update_ha_state()
        elif entity_id == self._power_sensor:
            await self._async_power_sensor_changed(old_state, new_state)

    # Store the last power sensor change time and debounce delay
    _last_power_sensor_change = None
    _power_sensor_debounce_delay = 0.5  # seconds
    
    async def _async_power_sensor_changed(self, old_state, new_state):
        """Handle power sensor changes with debounce to prevent race conditions."""
        if new_state is None:
            return

        if old_state is not None and new_state.state == old_state.state:
            return
            
        # Get current time for debounce check
        current_time = dt_util.utcnow()
        
        # If we've had a recent change, skip this update to debounce
        if self._last_power_sensor_change is not None:
            time_since_last_change = (current_time - self._last_power_sensor_change).total_seconds()
            if time_since_last_change < self._power_sensor_debounce_delay:
                _LOGGER.debug(
                    "Debouncing power sensor change: %s seconds since last change",
                    time_since_last_change
                )
                return
        
        # Update the last change time
        self._last_power_sensor_change = current_time
        
        # Process the state change
        if new_state.state == STATE_ON:
            _LOGGER.debug("Power sensor changed to ON")
            if self._attr_hvac_mode == HVACMode.OFF or self.power_mode == STATE_OFF:
                self._attr_hvac_mode = self._last_on_mode
                self.power_mode = STATE_ON
                self.async_schedule_update_ha_state()

        elif new_state.state == STATE_OFF:
            _LOGGER.debug("Power sensor changed to OFF")
            if self._attr_hvac_mode != HVACMode.OFF or self.power_mode == STATE_ON:
                self._attr_hvac_mode = HVACMode.OFF
                self.power_mode = STATE_OFF
                self.async_schedule_update_ha_state()

    @callback
    def _async_update_temp(self, state):
        """Update thermostat with latest state from sensor."""
        try:
            self._attr_current_temperature = float(state.state)
        except ValueError as ex:
            _LOGGER.debug("Unable to update from sensor: %s", ex)

    @callback
    def _async_update_humidity(self, state):
        """Update thermostat with latest state from humidity sensor."""
        try:
            if state.state != STATE_UNKNOWN and state.state != STATE_UNAVAILABLE:
                self._attr_current_humidity = int(float(state.state))
        except ValueError as ex:
            _LOGGER.error("Unable to update from humidity sensor: %s", ex)

    @property
    def _is_device_active(self):
        """If the toggleable device is currently active."""
        return self.power_mode == STATE_ON

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return self._support_flags

# Removed duplicate implementation of async_set_preset_mode
# The more comprehensive implementation at lines 1281-1313 is kept

    async def set_mode(self, hvac_mode):
        """Set hvac mode.
        
        This method handles the HVAC mode setting, including the OFF mode.
        When setting to OFF, it stores the last active mode for future use.
        """
        hvac_mode = hvac_mode.lower()
        
        # Handle OFF mode specifically
        if hvac_mode == HVACMode.OFF:
            # Store the current mode as last_on_mode if we're currently on
            if self._attr_hvac_mode != HVACMode.OFF:
                self._last_on_mode = self._attr_hvac_mode
            
            self._attr_hvac_mode = HVACMode.OFF
            self._enabled = False
            self.power_mode = STATE_OFF
            _LOGGER.debug("Setting mode to OFF, last_on_mode: %s", self._last_on_mode)
            
        # Handle other modes
        elif hvac_mode in self._attr_hvac_modes:
            self._attr_hvac_mode = hvac_mode
            self._last_on_mode = hvac_mode
            self._enabled = True
            self.power_mode = STATE_ON
            _LOGGER.debug("Setting mode to %s", hvac_mode)
            
        # Handle invalid modes
        else:
            _LOGGER.warning("Invalid HVAC mode: %s. Setting to OFF. Available modes: %s",
                           hvac_mode, self._attr_hvac_modes)
            self._attr_hvac_mode = HVACMode.OFF
            self._enabled = False
            self.power_mode = STATE_OFF

    async def send_ir(self):
        """Send the payload to tasmota mqtt topic."""
        try:
            # Log the current fan mode before unprettifying
            _LOGGER.debug("Current fan mode before unprettifying: %s", self._attr_fan_mode)
            
            # Unprettify the fan mode for sending to the device
            fan_speed = self.fan_unprettify(self._attr_fan_mode)
            _LOGGER.debug("Fan mode after unprettifying: %s", fan_speed)
            
            # tweak for some ELECTRA_AC devices
            if self._quirk_fan_max_high:
                if fan_speed == FAN_AUTO:  # Changed from FAN_HIGH to FAN_AUTO
                    fan_speed = HVAC_FAN_MAX
                    _LOGGER.debug("Applied ELECTRA_AC quirk: FAN_AUTO -> HVAC_FAN_MAX")
                elif fan_speed == HVAC_FAN_MAX:
                    fan_speed = HVAC_FAN_AUTO
                    _LOGGER.debug("Applied ELECTRA_AC quirk: HVAC_FAN_MAX -> HVAC_FAN_AUTO")

            # Set the swing mode - default off
            self._swingv = STATE_OFF if self._fix_swingv is None else self._fix_swingv
            self._swingh = STATE_OFF if self._fix_swingh is None else self._fix_swingh

            if SWING_BOTH in (self._attr_swing_modes or []) or SWING_VERTICAL in (
                self._attr_swing_modes or []
            ):
                if (
                    self._attr_swing_mode == SWING_BOTH
                    or self._attr_swing_mode == SWING_VERTICAL
                ):
                    self._swingv = STATE_AUTO

            if SWING_BOTH in (self._attr_swing_modes or []) or SWING_HORIZONTAL in (
                self._attr_swing_modes or []
            ):
                if (
                    self._attr_swing_mode == SWING_BOTH
                    or self._attr_swing_mode == SWING_HORIZONTAL
                ):
                    self._swingh = STATE_AUTO

            _dt = dt_util.now()
            _min = _dt.hour * 60 + _dt.minute

            # Populate the payload
            payload_data = {
                "StateMode": self._state_mode,
                "Vendor": self._vendor,
                "Model": self._model,
                "Power": self.power_mode,
                "Mode": self._last_on_mode if self._keep_mode else self._attr_hvac_mode,
                "Celsius": self._celsius,
                "Temp": self._attr_target_temperature,
                "FanSpeed": fan_speed,
                "SwingV": self._swingv,
                "SwingH": self._swingh,
                "Quiet": self._quiet,
                "Turbo": self._turbo,
                "Econo": self._econo,
                "Light": self._light,
                "Filter": self._filter,
                "Clean": self._clean,
                "Beep": self._beep,
                "Sleep": self._sleep,
                "Clock": int(_min),
                "Weekday": int(_dt.weekday()),
            }
            self._state_mode = DEFAULT_STATE_MODE
            for key in self._toggle_list:
                setattr(self, "_" + key.lower(), "off")

            payload = json.dumps(payload_data)

            # Publish mqtt message
            if float(self._mqtt_delay) != float(DEFAULT_MQTT_DELAY):
                await asyncio.sleep(float(self._mqtt_delay))

            try:
                await mqtt.async_publish(self.hass, self.topic, payload)
            except mqtt.MqttNotConnectedError:
                _LOGGER.error("MQTT is not connected, cannot publish command")
                return
            except Exception as e:
                _LOGGER.error("Error publishing MQTT message: %s", str(e))
                return

            # Update HA UI and State
            self.async_schedule_update_ha_state()
            
        except Exception as e:
            _LOGGER.error("Error preparing IR command: %s", str(e))
