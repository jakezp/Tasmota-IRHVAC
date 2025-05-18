# Tasmota IRHVAC Configuration Guide

This document provides detailed information about all configuration options available for the Tasmota IRHVAC integration.

## Configuration Methods

The integration supports two configuration methods:

1. **UI Configuration** (recommended): Configure through the Home Assistant UI
2. **YAML Configuration** (legacy): Configure through the `configuration.yaml` file

## UI Configuration

To configure the integration through the UI:

1. Go to Home Assistant → Settings → Devices & Services
2. Click the "+ Add Integration" button
3. Search for "Tasmota IRHVAC" and select it
4. Follow the configuration steps

### Configuration Steps

The UI configuration flow consists of the following steps:

#### 1. Device Information
- **Host**: The IP address or hostname of your Tasmota device
- **Username**: The username for your Tasmota device (if authentication is enabled)
- **Password**: The password for your Tasmota device (if authentication is enabled)

#### 2. IR Protocol
- **Vendor**: The IR protocol for your AC (e.g., SAMSUNG_AC, LG_AC, MITSUBISHI_AC)
- **HVAC Model**: The model number for your AC (default: 1)
- **MQTT Delay**: Delay between MQTT commands in seconds (default: 0)

#### 3. Sensors
- **Temperature Sensor**: Entity ID of a temperature sensor (optional but recommended)
- **Humidity Sensor**: Entity ID of a humidity sensor (optional)
- **Power Sensor**: Entity ID of a binary sensor to track power state (optional)

#### 4. Temperature Settings
- **Minimum Temperature**: Lowest temperature setting allowed (default: 16°C)
- **Maximum Temperature**: Highest temperature setting allowed (default: 32°C)
- **Target Temperature**: Default target temperature (default: 24°C)
- **Away Temperature**: Temperature used in away mode (default: 26°C)
- **Temperature Precision**: Precision for temperature control (1.0, 0.5, or 0.1)
- **Temperature Step**: Step size for temperature adjustments (default: 1.0)
- **Celsius Mode**: Whether to use Celsius (On) or Fahrenheit (Off)

#### 5. Modes and Fan Speeds
- **Supported Modes**: Operation modes supported by your AC
- **Supported Fan Speeds**: Fan speeds supported by your AC
- **Supported Swing Modes**: Swing modes supported by your AC
- **Default Vertical Swing**: Default position for vertical swing
- **Default Horizontal Swing**: Default position for horizontal swing

#### 6. Presets
- **Enabled Presets**: Special features to enable as presets
- **Default Presets**: Presets that are enabled by default

#### 7. Additional Features
- **Toggle List**: Features that should be treated as toggles
- **Default Quiet Mode**: Default state for quiet mode (On/Off)
- **Default Turbo Mode**: Default state for turbo mode (On/Off)
- **Default Econo Mode**: Default state for economy mode (On/Off)
- **Default Light Mode**: Default state for light (On/Off)
- **Default Filter Mode**: Default state for filter mode (On/Off)
- **Default Clean Mode**: Default state for clean mode (On/Off)
- **Default Beep Mode**: Default state for beep sounds (On/Off)
- **Default Sleep Mode**: Default value for sleep mode
- **Keep Mode When Off**: Whether to keep the last mode when turning off
- **Ignore Off Temperature**: Whether to ignore temperature changes when off

## YAML Configuration

To configure the integration through YAML, add the following to your `configuration.yaml` file:

```yaml
climate:
  - platform: tasmota_irhvac
    name: "Living Room AC"
    command_topic: "cmnd/your_tasmota_device/irhvac"
    state_topic: "tele/your_tasmota_device/RESULT"
    # Additional configuration options...
```

### Required Configuration Options

| Option | Description | Example |
|--------|-------------|---------|
| `platform` | Must be `tasmota_irhvac` | `tasmota_irhvac` |
| `name` | Name of the climate entity | `"Living Room AC"` |
| `command_topic` | MQTT topic for sending commands | `"cmnd/tasmota_ac/irhvac"` |
| `state_topic` | MQTT topic for receiving state updates | `"tele/tasmota_ac/RESULT"` |
| `vendor` | IR protocol for your AC | `"SAMSUNG_AC"` |

### Optional Configuration Options

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `state_topic_2` | Secondary MQTT topic for state updates | `None` | `"stat/tasmota_ac/RESULT"` |
| `availability_topic` | MQTT topic for device availability | `None` | `"tele/tasmota_ac/LWT"` |
| `temperature_sensor` | Entity ID of a temperature sensor | `None` | `sensor.living_room_temp` |
| `humidity_sensor` | Entity ID of a humidity sensor | `None` | `sensor.living_room_humidity` |
| `power_sensor` | Entity ID of a binary sensor for power state | `None` | `binary_sensor.ac_power` |
| `mqtt_delay` | Delay between MQTT commands in seconds | `0` | `0.5` |
| `min_temp` | Minimum temperature setting | `16` | `18` |
| `max_temp` | Maximum temperature setting | `32` | `30` |
| `target_temp` | Default target temperature | `26` | `24` |
| `initial_operation_mode` | Initial operation mode | `"off"` | `"cool"` |
| `away_temp` | Temperature used in away mode | `24` | `28` |
| `precision` | Temperature precision | `1` | `0.5` |
| `temp_step` | Temperature adjustment step size | `1` | `0.5` |
| `hvac_model` | Model number for your AC | `"1"` | `"2"` |
| `celsius_mode` | Whether to use Celsius | `"On"` | `"Off"` |
| `keep_mode_when_off` | Keep last mode when turning off | `False` | `True` |
| `ignore_off_temp` | Ignore temperature changes when off | `False` | `True` |

### Mode and Fan Speed Configuration

| Option | Description | Example |
|--------|-------------|---------|
| `supported_modes` | List of supported operation modes | See below |
| `supported_fan_speeds` | List of supported fan speeds | See below |
| `supported_swing_list` | List of supported swing modes | See below |

#### Supported Modes Example

```yaml
supported_modes:
  - "heat"
  - "cool"
  - "dry"
  - "fan_only"
  - "auto"
  - "off"
```

#### Supported Fan Speeds Example

```yaml
supported_fan_speeds:
  - "auto"
  - "low"
  - "medium"
  - "high"
  - "max"
```

#### Supported Swing List Example

```yaml
supported_swing_list:
  - "off"
  - "vertical"
  - "horizontal"
  - "both"
```

### Default Feature States

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `default_quiet_mode` | Default state for quiet mode | `"Off"` | `"On"` |
| `default_turbo_mode` | Default state for turbo mode | `"Off"` | `"On"` |
| `default_econo_mode` | Default state for economy mode | `"Off"` | `"On"` |
| `default_light_mode` | Default state for light | `"Off"` | `"On"` |
| `default_filter_mode` | Default state for filter mode | `"Off"` | `"On"` |
| `default_clean_mode` | Default state for clean mode | `"Off"` | `"On"` |
| `default_beep_mode` | Default state for beep sounds | `"Off"` | `"On"` |
| `default_sleep_mode` | Default value for sleep mode | `"-1"` | `"0"` |
| `default_swingv` | Default vertical swing position | `""` | `"auto"` |
| `default_swingh` | Default horizontal swing position | `""` | `"auto"` |

### Advanced Configuration

#### Toggle List

Some AC features are toggle functions that don't retain their state. You can specify these features in the `toggle_list` option:

```yaml
toggle_list:
  - "Beep"
  - "Clean"
  - "Econo"
  - "Filter"
  - "Light"
  - "Quiet"
  - "Sleep"
  - "SwingH"
  - "SwingV"
  - "Turbo"
```

#### Special Mode Mappings

Some AC protocols have different naming conventions for modes. The integration provides special mappings for these cases:

```yaml
supported_modes:
  # Instead of "auto" and "fan_only"
  - "auto_fan_only"  # If remote shows fan but Tasmota says auto
  - "fan_only_auto"  # If remote shows auto but Tasmota says fan
```

```yaml
supported_fan_speeds:
  # Instead of "high" and "max"
  - "auto_max"  # Would become max
  - "max_high"  # Would become high
```

## Protocol-Specific Configuration

Different AC protocols may have specific requirements or limitations. Here are some examples:

### MITSUBISHI_AC

```yaml
keep_mode_when_off: True  # Required for MITSUBISHI_AC
```

### SAMSUNG_AC

```yaml
supported_swing_list:
  - "off"
  - "vertical"
  # Horizontal swing may not be supported
```

### DAIKIN_AC

```yaml
supported_fan_speeds:
  - "auto"
  - "quiet"
  - "low"
  - "medium"
  - "high"
```

## Complete Configuration Example

```yaml
climate:
  - platform: tasmota_irhvac
    name: "Living Room AC"
    command_topic: "cmnd/tasmota_ac/irhvac"
    state_topic: "tele/tasmota_ac/RESULT"
    state_topic_2: "stat/tasmota_ac/RESULT"
    availability_topic: "tele/tasmota_ac/LWT"
    temperature_sensor: sensor.living_room_temperature
    humidity_sensor: sensor.living_room_humidity
    power_sensor: binary_sensor.ac_power
    vendor: "SAMSUNG_AC"
    mqtt_delay: 0.5
    min_temp: 16
    max_temp: 30
    target_temp: 24
    initial_operation_mode: "cool"
    away_temp: 26
    precision: 0.5
    temp_step: 0.5
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
      - "horizontal"
      - "both"
    default_quiet_mode: "Off"
    default_turbo_mode: "Off"
    default_econo_mode: "Off"
    hvac_model: "1"
    celsius_mode: "On"
    default_light_mode: "Off"
    default_filter_mode: "Off"
    default_clean_mode: "Off"
    default_beep_mode: "Off"
    default_sleep_mode: "0"
    default_swingv: "auto"
    default_swingh: "auto"
    keep_mode_when_off: False
    ignore_off_temp: False
    toggle_list:
      - "Clean"
      - "Turbo"