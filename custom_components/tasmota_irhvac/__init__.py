"""The Tasmota Irhvac climate component."""
import logging
from homeassistant import config_entries
from homeassistant.const import (
    CONF_NAME,
    EVENT_HOMEASSISTANT_START, 
    Platform
)    
from homeassistant.core import HomeAssistant
from homeassistant.helpers import discovery
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import device_registry as dr

from .const import (
    DOMAIN,
    CONF_VENDOR,
    CONF_MODEL,
    DEFAULT_CONF_MODEL,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.CLIMATE]

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Tasmota IRHVAC integration."""
    _LOGGER.debug("Setting up Tasmota IRHVAC integration")
    
    hass.data[DOMAIN] = {}
    
    # Set up the climate platform for YAML configuration
    if DOMAIN in config:
        _LOGGER.debug("Setting up YAML configuration")
        hass.async_create_task(
            discovery.async_load_platform(
                hass, Platform.CLIMATE, DOMAIN, {}, config
            )
        )
    
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Tasmota IRHVAC from a config entry."""
    _LOGGER.debug("Setting up config entry: %s", entry.data)
    _LOGGER.debug("Config entry options: %s", entry.options)
    
    # Merge options with data for backward compatibility
    config = {
        **entry.data,
        **entry.options
    }
    
    hass.data[DOMAIN][entry.entry_id] = config

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    
    return True

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    _LOGGER.debug("Reloading entry with options: %s", entry.options)
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading config entry")

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    # Remove entry data
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        _LOGGER.debug("Config entry unloaded successfully")
    return unload_ok