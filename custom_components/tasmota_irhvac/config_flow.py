"""Config flow for Tasmota IRHVAC integration."""
from __future__ import annotations

import logging
from typing import Any
import asyncio
import async_timeout

import voluptuous as vol
import aiohttp
from aiohttp import BasicAuth

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow 
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.components import mqtt
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_USERNAME,
    CONF_PASSWORD,
)

from .const import (
    DOMAIN,
    # Import all constants from const.py
    CONF_VENDOR,
    CONF_COMMAND_TOPIC,
    CONF_STATE_TOPIC,
    CONF_AVAILABILITY_TOPIC,
    CONF_TEMP_SENSOR,
    CONF_HUMIDITY_SENSOR,
    CONF_POWER_SENSOR,
    CONF_MODEL,
    CONF_MQTT_DELAY,
    CONF_MIN_TEMP,
    CONF_MAX_TEMP,
    CONF_TARGET_TEMP,
    CONF_AWAY_TEMP,
    CONF_PRECISION,
    CONF_TEMP_STEP,
    CONF_MODES_LIST,
    CONF_FAN_LIST,
    CONF_SWING_LIST,
    CONF_QUIET,
    CONF_TURBO,
    CONF_ECONO,
    CONF_LIGHT,
    CONF_FILTER,
    CONF_CLEAN,
    CONF_BEEP,
    CONF_SLEEP,
    CONF_CELSIUS,
    CONF_KEEP_MODE,
    CONF_SWINGV,
    CONF_SWINGH,
    CONF_TOGGLE_LIST,
    CONF_IGNORE_OFF_TEMP,
    # Default values
    DEFAULT_NAME,
    DEFAULT_MQTT_DELAY,
    DEFAULT_MIN_TEMP,
    DEFAULT_MAX_TEMP,
    DEFAULT_TARGET_TEMP,
    DEFAULT_PRECISION,
    DEFAULT_CONF_MODEL,
    DEFAULT_CONF_QUIET,
    DEFAULT_CONF_TURBO,
    DEFAULT_CONF_ECONO,
    DEFAULT_CONF_LIGHT,
    DEFAULT_CONF_FILTER,
    DEFAULT_CONF_CLEAN,
    DEFAULT_CONF_BEEP,
    DEFAULT_CONF_SLEEP,
    DEFAULT_CONF_CELSIUS,
    DEFAULT_CONF_KEEP_MODE,
    DEFAULT_IGNORE_OFF_TEMP,
    DEFAULT_MODES_LIST,
    DEFAULT_FAN_LIST,
    DEFAULT_SWING_LIST,
    TOGGLE_ALL_LIST,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_USERNAME): str,
        vol.Optional(CONF_PASSWORD): str,
    }
)

class TasmotaIRHVACOptionsFlow(OptionsFlow):
    """Handle Tasmota IRHVAC options."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.entry_id = config_entry.entry_id
        self.data = dict(config_entry.data)
        self.options = dict(config_entry.options)

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Manage the options."""
        errors = {}

        if user_input is not None:
            _LOGGER.debug("Received user input for options: %s", user_input)
            try:
                # Validate temperature ranges
                min_temp = user_input.get(CONF_MIN_TEMP, self.data.get(CONF_MIN_TEMP, DEFAULT_MIN_TEMP))
                max_temp = user_input.get(CONF_MAX_TEMP, self.data.get(CONF_MAX_TEMP, DEFAULT_MAX_TEMP))
                target_temp = user_input.get(CONF_TARGET_TEMP, self.data.get(CONF_TARGET_TEMP, DEFAULT_TARGET_TEMP))

                if max_temp <= min_temp:
                    errors[CONF_MAX_TEMP] = "invalid_temp_range"
                elif target_temp < min_temp or target_temp > max_temp:
                    errors[CONF_TARGET_TEMP] = "invalid_target_temp"
                else:
                    return self.async_create_entry(title="", data=user_input)

            except Exception as ex:
                _LOGGER.error("Error updating options: %s", str(ex))
                errors["base"] = "unknown"

        # Prepare schema with current values
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    CONF_MIN_TEMP,
                    default=self.options.get(
                        CONF_MIN_TEMP, 
                        self.data.get(CONF_MIN_TEMP, DEFAULT_MIN_TEMP)
                    ),
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_MAX_TEMP,
                    default=self.options.get(
                        CONF_MAX_TEMP, 
                        self.data.get(CONF_MAX_TEMP, DEFAULT_MAX_TEMP)
                    ),
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_TARGET_TEMP,
                    default=self.options.get(
                        CONF_TARGET_TEMP, 
                        self.data.get(CONF_TARGET_TEMP, DEFAULT_TARGET_TEMP)
                    ),
                ): vol.Coerce(float),
                vol.Optional(
                CONF_TEMP_STEP,
                default=self.options.get(
                    CONF_TEMP_STEP, self.data.get(CONF_TEMP_STEP, DEFAULT_PRECISION)
                )
                ): vol.In([0.5, 1.0]),
                vol.Optional(
                    CONF_MODES_LIST,
                    default=self.options.get(
                        CONF_MODES_LIST, 
                        self.data.get(CONF_MODES_LIST, DEFAULT_MODES_LIST)
                    ),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=DEFAULT_MODES_LIST,
                        multiple=True,
                    ),
                ),
                vol.Optional(
                    CONF_FAN_LIST,
                    default=self.options.get(
                        CONF_FAN_LIST, 
                        self.data.get(CONF_FAN_LIST, DEFAULT_FAN_LIST)
                    ),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=DEFAULT_FAN_LIST,
                        multiple=True,
                    ),
                ),
                vol.Optional(
                    CONF_SWING_LIST,
                    default=self.options.get(
                        CONF_SWING_LIST, 
                        self.data.get(CONF_SWING_LIST, DEFAULT_SWING_LIST)
                    ),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=["off", "vertical", "horizontal", "both"],
                        multiple=True,
                    ),
                ),
            }),
            errors=errors,
        )

class TasmotaIRHVACConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tasmota IRHVAC."""

    VERSION = 1

    def __init__(self):
        """Initialize."""
        self._data = {}
        self._device_info = None
        self._mqtt_topics = None
        _LOGGER.debug("Config flow initialized for domain: %s", DOMAIN)

    # Add this to enable options
    async def async_step_import(self, import_config):
        """Import a config entry."""
        return await self.async_step_user(import_config)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> TasmotaIRHVACOptionsFlow:
        """Get the options flow for this handler."""
        return TasmotaIRHVACOptionsFlow(config_entry)

    async def _get_tasmota_info(self, host: str, auth: tuple | None = None) -> dict[str, Any] | None:
        """Get Tasmota device information."""
        _LOGGER.debug("Starting Tasmota device step")
        errors = {} 
        try:
            async with async_timeout.timeout(10):
                async with aiohttp.ClientSession() as session:
                    # Convert auth tuple to BasicAuth if provided
                    auth_obj = BasicAuth(auth[0], auth[1]) if auth else None
                    
                    # Get device status
                    url = f"http://{host}/cm"
                    params = {"cmnd": "Status 0"}
                    async with session.get(url, params=params, auth=auth_obj) as response:
                        if response.status != 200:
                            _LOGGER.error("Failed to get device status: %s", response.status)
                            return None
                        status = await response.json()

                    # Get IR protocols by first triggering the error message
                    params = {"cmnd": 'IRhvac {"Vendor":""}'}
                    async with session.get(url, params=params, auth=auth_obj) as response:
                        if response.status == 200:
                            ir_response = await response.json()
                            ir_info = {"Protocols": []}
                            
                            # Check if we got the error message with vendor list
                            if isinstance(ir_response.get("IRHVAC"), str):
                                error_msg = ir_response["IRHVAC"]
                                if "Wrong Vendor (" in error_msg:
                                    # Extract vendors from the error message
                                    vendors = error_msg.split("(")[1].rstrip(")").split("|")
                                    ir_info["Protocols"] = vendors
                                    _LOGGER.debug("Found IR protocols: %s", vendors)

                            # If no protocols found, use defaults
                            if not ir_info["Protocols"]:
                                ir_info["Protocols"] = [
                                    "SAMSUNG_AC",
                                    "LG_AC",
                                    "MITSUBISHI_AC",
                                    "DAIKIN_AC",
                                    "HITACHI_AC",
                                    "FUJITSU_AC",
                                    "PANASONIC_AC"
                                ]
                                _LOGGER.debug("Using default IR protocols")

                    return {
                        "status": status,
                        "ir": ir_info,
                        "hostname": host,
                    }

        except (asyncio.TimeoutError, aiohttp.ClientError) as ex:
            _LOGGER.error("Error connecting to Tasmota device: %s", str(ex))
            return None
        except Exception as ex:
            _LOGGER.error("Unexpected error: %s", str(ex))
            return None

    def _get_mqtt_topics(self, device_name: str) -> dict[str, str]:
        """Generate MQTT topics based on device name."""
        safe_name = device_name.lower().replace(" ", "_")
        if not safe_name:
            safe_name = "tasmota_irhvac"
        
        return {
            CONF_COMMAND_TOPIC: f"cmnd/{safe_name}/irhvac",
            CONF_STATE_TOPIC: f"tele/{safe_name}/RESULT",
            CONF_AVAILABILITY_TOPIC: f"tele/{safe_name}/LWT",
        }

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        _LOGGER.debug("Starting user step")
        errors = {}

        _LOGGER.debug("Starting user step with translations context")
        if user_input is not None:
            # Check if already configured
            await self.async_set_unique_id(f"tasmota_irhvac_{user_input[CONF_HOST].replace('.', '_')}")
            self._abort_if_unique_id_configured()

            auth = None
            if user_input.get(CONF_USERNAME) and user_input.get(CONF_PASSWORD):
                auth = (user_input[CONF_USERNAME], user_input[CONF_PASSWORD])

            try:
                device_info = await self._get_tasmota_info(user_input[CONF_HOST], auth)
                
                if device_info is None:
                    errors["base"] = "cannot_connect"
                else:
                    self._device_info = device_info
                    # Get device name from Tasmota
                    device_name = device_info["status"].get("Status", {}).get("FriendlyName", [DEFAULT_NAME])[0]
                    self._mqtt_topics = self._get_mqtt_topics(device_name)
                    
                    # Store basic info
                    self._data.update({
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_NAME: device_name,
                        **self._mqtt_topics
                    })
                    
                    return await self.async_step_ir()
            except Exception as ex:
                _LOGGER.error("Unexpected error: %s", str(ex))
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_ir(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Configure IR settings."""
        errors = {}  

        if user_input is not None:
            # Generate a unique ID for the config entry
            unique_id = f"tasmota_irhvac_{self._data['host']}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()
            
            self._data.update(user_input)
            return await self.async_step_sensors()

        # Get available IR protocols from device
        ir_protocols = self._device_info["ir"].get("Protocols", [])
        
        if not ir_protocols:
            _LOGGER.warning("No IR protocols found, using default list")
            ir_protocols = [
                "SAMSUNG_AC",
                "LG_AC",
                "MITSUBISHI_AC",
                "DAIKIN_AC",
                "HITACHI_AC",
                "FUJITSU_AC",
                "PANASONIC_AC"
            ]

        return self.async_show_form(
            step_id="ir",
            data_schema=vol.Schema({
                vol.Required(CONF_VENDOR): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=ir_protocols,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    ),
                ),
                vol.Optional("hvac_model", default=DEFAULT_CONF_MODEL): str,
                vol.Optional(CONF_MQTT_DELAY, default=DEFAULT_MQTT_DELAY): vol.Coerce(float),
            }),
            description_placeholders={
                "device_ip": self._data[CONF_HOST]
            },
            errors=errors,
        )
    
    async def async_step_temperature(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Configure temperature settings."""
        _LOGGER.debug("Starting temperature step")
        errors = {}

        if user_input is not None:
            min_temp = user_input.get(CONF_MIN_TEMP, DEFAULT_MIN_TEMP)
            max_temp = user_input.get(CONF_MAX_TEMP, DEFAULT_MAX_TEMP)
            target_temp = user_input.get(CONF_TARGET_TEMP, DEFAULT_TARGET_TEMP)

            if max_temp <= min_temp:
                errors["max_temp"] = "invalid_temp_range"
            elif target_temp < min_temp or target_temp > max_temp:
                errors["target_temp"] = "invalid_target_temp"
            else:
                self._data.update(user_input)
                return await self.async_step_modes()

        return self.async_show_form(
            step_id="temperature",
            data_schema=vol.Schema({
                vol.Required("min_temp", default=DEFAULT_MIN_TEMP): vol.Coerce(float),
                vol.Required("max_temp", default=DEFAULT_MAX_TEMP): vol.Coerce(float),
                vol.Required(CONF_TARGET_TEMP, default=DEFAULT_TARGET_TEMP): vol.Coerce(float),
                vol.Optional(CONF_AWAY_TEMP): vol.Coerce(float),
                vol.Optional(CONF_PRECISION, default=DEFAULT_PRECISION): vol.In([0.1, 0.5, 1.0]),
                vol.Required(CONF_TEMP_STEP,default=DEFAULT_PRECISION): vol.In([0.5, 1.0]),            
                vol.Optional(CONF_CELSIUS, default=DEFAULT_CONF_CELSIUS): vol.In(["On", "Off"]),
            }),
            errors=errors,
        )
    
    async def async_step_sensors(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Configure sensor entities."""
        errors = {}

        if user_input is not None:
            try:
                # Only save valid entity IDs
                cleaned_input = {}
                for key, value in user_input.items():
                    if value:
                        if not isinstance(value, str):
                            errors[key] = "invalid_entity_id"
                            continue
                        if not value.startswith(("sensor.", "binary_sensor.")):
                            errors[key] = "invalid_entity_id"
                            continue
                        cleaned_input[key] = value

                if not errors:
                    self._data.update(cleaned_input)
                    return await self.async_step_temperature()

            except Exception as ex:
                _LOGGER.error("Error processing sensor input: %s", str(ex))
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="sensors",
            data_schema=vol.Schema({
                vol.Optional(CONF_TEMP_SENSOR): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor",
                        multiple=False,
                    )
                ),
                vol.Optional(CONF_HUMIDITY_SENSOR): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="sensor",
                        multiple=False,
                    )
                ),
                vol.Optional(CONF_POWER_SENSOR): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain="binary_sensor",
                        multiple=False,
                    )
                ),
            }),
            errors=errors,
        )

    async def async_step_modes(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Configure operation modes."""
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_presets()

        return self.async_show_form(
            step_id="modes",
            data_schema=vol.Schema({
                vol.Required(CONF_MODES_LIST, default=DEFAULT_MODES_LIST): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=DEFAULT_MODES_LIST,
                        multiple=True,
                    ),
                ),
                vol.Required(CONF_FAN_LIST, default=DEFAULT_FAN_LIST): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=DEFAULT_FAN_LIST,
                        multiple=True,
                    ),
                ),
                vol.Required(CONF_SWING_LIST, default=DEFAULT_SWING_LIST): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=["off", "vertical", "horizontal", "both"],
                        multiple=True,
                    ),
                ),
                vol.Optional(CONF_SWINGV): str,
                vol.Optional(CONF_SWINGH): str,
            }),
        )

    async def async_step_presets(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Configure preset modes."""
        _LOGGER.debug("Starting presets step")
        errors = {}

        if user_input is not None:
            _LOGGER.debug("Received presets input: %s", user_input)
            self._data.update(user_input)
            return await self.async_step_features()

        # Get all available presets
        available_presets = [
            ("econo", "Economy Mode"),
            ("turbo", "Turbo Mode"),
            ("quiet", "Quiet Mode"),
            ("light", "Light Mode"),
            ("filter", "Filter Mode"),
            ("clean", "Clean Mode"),
            ("beep", "Beep Mode"),
            ("sleep", "Sleep Mode"),
        ]

        try:
            return self.async_show_form(
                step_id="presets",
                data_schema=vol.Schema({
                    vol.Optional("enabled_presets", default=[]): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[{"value": id, "label": name} for id, name in available_presets],
                            multiple=True,
                            mode=selector.SelectSelectorMode.LIST,
                        ),
                    ),
                    vol.Optional("default_presets", default=[]): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[{"value": id, "label": name} for id, name in available_presets],
                            multiple=True,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        ),
                    ),
                }),
                errors=errors,
            )
        except Exception as ex:
            _LOGGER.error("Error in presets step: %s", str(ex))
            errors["base"] = "unknown"
            return self.async_show_form(
                step_id="presets",
                data_schema=vol.Schema({}),
                errors=errors,
            )

    async def async_step_features(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Configure additional features."""
        if user_input is not None:
            self._data.update(user_input)
            return self.async_create_entry(
                title=self._data[CONF_NAME],
                data=self._data,
            )

        return self.async_show_form(
            step_id="features",
            data_schema=vol.Schema({
                vol.Optional(CONF_TOGGLE_LIST, default=[]): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=TOGGLE_ALL_LIST,
                        multiple=True,
                    ),
                ),
                vol.Optional(CONF_QUIET, default=DEFAULT_CONF_QUIET): vol.In(["On", "Off"]),
                vol.Optional(CONF_TURBO, default=DEFAULT_CONF_TURBO): vol.In(["On", "Off"]),
                vol.Optional(CONF_ECONO, default=DEFAULT_CONF_ECONO): vol.In(["On", "Off"]),
                vol.Optional(CONF_LIGHT, default=DEFAULT_CONF_LIGHT): vol.In(["On", "Off"]),
                vol.Optional(CONF_FILTER, default=DEFAULT_CONF_FILTER): vol.In(["On", "Off"]),
                vol.Optional(CONF_CLEAN, default=DEFAULT_CONF_CLEAN): vol.In(["On", "Off"]),
                vol.Optional(CONF_BEEP, default=DEFAULT_CONF_BEEP): vol.In(["On", "Off"]),
                vol.Optional(CONF_SLEEP, default=DEFAULT_CONF_SLEEP): str,
                vol.Optional(CONF_KEEP_MODE, default=DEFAULT_CONF_KEEP_MODE): bool,
                vol.Optional(CONF_IGNORE_OFF_TEMP, default=DEFAULT_IGNORE_OFF_TEMP): bool,
            }),
        )

