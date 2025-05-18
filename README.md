# Tasmota IRHVAC Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)

Home Assistant integration for controlling IR Air Conditioners via Tasmota IRHVAC command and compatible hardware.

## Overview

This integration allows you to control hundreds of different air conditioner models through Tasmota-powered IR transceivers. It provides a complete climate entity interface in Home Assistant with support for:

- Multiple operation modes (heat, cool, dry, fan_only, auto)
- Fan speed control
- Swing mode control (vertical, horizontal, both)
- Temperature control
- Special features (econo, turbo, quiet, light, filter, clean, beep, sleep)

The integration supports both YAML configuration (for backward compatibility) and UI configuration through the Home Assistant UI.

## Hardware Requirements

To use this integration, you'll need:
- An ESP8266/ESP32 device flashed with Tasmota firmware (v8.1 or newer, tested up to latest versions)
- IR LED and IR receiver components
- MQTT broker configured in Home Assistant

### Hardware Setup

The recommended hardware setup includes:
- ESP8266/ESP32 board (like NodeMCU, Wemos D1 Mini, etc.)
- IR LED (with appropriate resistor)
- IR receiver (like TSOP38238, VS1838B)

![Schematics](https://raw.githubusercontent.com/user/Tasmota-IRHVAC/master/images/schematics.jpeg)

**Note:** It's recommended to connect the IR LED to the VU pin (if available) instead of VIN when powering the board via microUSB.

## Installation

### HACS Installation (Recommended)

1. Make sure [HACS](https://hacs.xyz/) is installed in your Home Assistant instance
2. Add this repository as a custom repository in HACS:
   - Go to HACS → Integrations → ⋮ (top right) → Custom repositories
   - Add the URL of this repository
   - Category: Integration
3. Click "Install" on the Tasmota IRHVAC integration
4. Restart Home Assistant

### Manual Installation

1. Download the latest release from the repository
2. Extract the `tasmota_irhvac` folder from the `custom_components` directory
3. Copy the folder to your Home Assistant's `custom_components` directory
4. Restart Home Assistant

## Configuration

The integration can be configured in two ways:

### UI Configuration (Recommended)

1. Go to Home Assistant → Settings → Devices & Services
2. Click the "+ Add Integration" button
3. Search for "Tasmota IRHVAC" and select it
4. Follow the configuration steps:
   - Enter your Tasmota device information (host, username, password)
   - Select the IR protocol for your AC
   - Configure temperature sensors (optional)
   - Set temperature ranges and preferences
   - Select supported modes and fan speeds
   - Configure additional features

### YAML Configuration (Legacy)

Add the following to your `configuration.yaml` file:

```yaml
climate:
  - platform: tasmota_irhvac
    name: "Living Room AC"
    command_topic: "cmnd/your_tasmota_device/irhvac"
    state_topic: "tele/your_tasmota_device/RESULT"
    temperature_sensor: sensor.living_room_temperature
    vendor: "YOUR_AC_VENDOR"
    supported_modes:
      - "heat"
      - "cool"
      - "dry"
      - "fan_only"
      - "auto"
      - "off"
    supported_fan_speeds:
      - "auto"
      - "low"
      - "medium"
      - "high"
    supported_swing_list:
      - "off"
      - "vertical"
```

See the [CONFIGURATION.md](CONFIGURATION.md) file for detailed configuration options.

## Tasmota Configuration

1. Flash your ESP device with Tasmota firmware (tasmota-ir.bin recommended)
2. Configure Tasmota with the appropriate GPIO settings:
   - Set an available GPIO pin as "IRsend (8)"
   - Set another available GPIO pin as "IRrecv (51)"

![Tasmota Configuration](https://raw.githubusercontent.com/user/Tasmota-IRHVAC/master/images/tasmota_config.jpeg)

3. Configure MQTT in Tasmota to connect to your Home Assistant's MQTT broker

## Usage

### Basic Control

Once configured, the integration will create a climate entity in Home Assistant that you can control through:
- The climate card in the Lovelace UI
- Automations and scripts
- Voice assistants

### Special Features

The integration provides several services to control additional AC features:

- `tasmota_irhvac.set_econo`: Control economy mode
- `tasmota_irhvac.set_turbo`: Control turbo mode
- `tasmota_irhvac.set_quiet`: Control quiet mode
- `tasmota_irhvac.set_light`: Control the AC's light
- `tasmota_irhvac.set_filters`: Control filter mode
- `tasmota_irhvac.set_clean`: Control clean mode
- `tasmota_irhvac.set_beep`: Control beep sounds
- `tasmota_irhvac.set_sleep`: Control sleep mode
- `tasmota_irhvac.set_swingv`: Control vertical swing position
- `tasmota_irhvac.set_swingh`: Control horizontal swing position

See the [SERVICES.md](SERVICES.md) file for detailed service documentation.

### Template Switches

You can create template switches to control special features. Example:

```yaml
switch:
  - platform: template
    switches:
      living_room_ac_econo:
        friendly_name: "Econo Mode"
        value_template: "{{ is_state_attr('climate.living_room_ac', 'econo', 'on') }}"
        turn_on:
          service: tasmota_irhvac.set_econo
          data:
            entity_id: climate.living_room_ac
            econo: 'on'
        turn_off:
          service: tasmota_irhvac.set_econo
          data:
            entity_id: climate.living_room_ac
            econo: 'off'
```

## Troubleshooting

See the [TROUBLESHOOTING.md](TROUBLESHOOTING.md) file for common issues and solutions.

## Additional Resources

- [Configuration Options](CONFIGURATION.md)
- [Service Documentation](SERVICES.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [Changelog](CHANGELOG.md)

## Community Support

For questions, feature requests, and troubleshooting, please use the [GitHub Issues](https://github.com/user/Tasmota-IRHVAC/issues) section of the repository.

## License

This project is licensed under the MIT License - see the LICENSE file for details.