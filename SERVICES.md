# Tasmota IRHVAC Services

This document provides detailed information about all the services available in the Tasmota IRHVAC integration.

## Overview

The Tasmota IRHVAC integration provides several services to control special features of your air conditioner that are not part of the standard climate entity interface. These services allow you to control features such as:

- Economy mode
- Turbo mode
- Quiet mode
- Light control
- Filter mode
- Clean mode
- Beep sounds
- Sleep mode
- Vertical and horizontal swing positions

## Important Notes

- Not all air conditioners support all features. Using a service for an unsupported feature may have no effect.
- The availability of these features depends on the IR protocol used by your AC and the capabilities of the Tasmota IRHVAC library.
- You are using these services at your own risk, as they may behave differently depending on your specific AC model.

## Available Services

### `tasmota_irhvac.set_econo`

Controls the economy mode of the air conditioner.

**Parameters:**

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `entity_id` | Yes | The entity ID of the climate device | `climate.living_room_ac` |
| `econo` | Yes | The desired state (`"on"` or `"off"`) | `"on"` |
| `state_mode` | No | Sets StateMode in MQTT message (default: `"SendStore"`) | `"StoreOnly"` |

**Example:**

```yaml
service: tasmota_irhvac.set_econo
target:
  entity_id: climate.living_room_ac
data:
  econo: "on"
  state_mode: "SendStore"
```

### `tasmota_irhvac.set_turbo`

Controls the turbo mode of the air conditioner.

**Parameters:**

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `entity_id` | Yes | The entity ID of the climate device | `climate.living_room_ac` |
| `turbo` | Yes | The desired state (`"on"` or `"off"`) | `"on"` |
| `state_mode` | No | Sets StateMode in MQTT message (default: `"SendStore"`) | `"StoreOnly"` |

**Example:**

```yaml
service: tasmota_irhvac.set_turbo
target:
  entity_id: climate.living_room_ac
data:
  turbo: "on"
  state_mode: "SendStore"
```

### `tasmota_irhvac.set_quiet`

Controls the quiet mode of the air conditioner.

**Parameters:**

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `entity_id` | Yes | The entity ID of the climate device | `climate.living_room_ac` |
| `quiet` | Yes | The desired state (`"on"` or `"off"`) | `"on"` |
| `state_mode` | No | Sets StateMode in MQTT message (default: `"SendStore"`) | `"StoreOnly"` |

**Example:**

```yaml
service: tasmota_irhvac.set_quiet
target:
  entity_id: climate.living_room_ac
data:
  quiet: "on"
  state_mode: "SendStore"
```

### `tasmota_irhvac.set_light`

Controls the light of the air conditioner.

**Parameters:**

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `entity_id` | Yes | The entity ID of the climate device | `climate.living_room_ac` |
| `light` | Yes | The desired state (`"on"` or `"off"`) | `"on"` |
| `state_mode` | No | Sets StateMode in MQTT message (default: `"SendStore"`) | `"StoreOnly"` |

**Example:**

```yaml
service: tasmota_irhvac.set_light
target:
  entity_id: climate.living_room_ac
data:
  light: "on"
  state_mode: "SendStore"
```

### `tasmota_irhvac.set_filters`

Controls the filter mode of the air conditioner.

**Parameters:**

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `entity_id` | Yes | The entity ID of the climate device | `climate.living_room_ac` |
| `filters` | Yes | The desired state (`"on"` or `"off"`) | `"on"` |
| `state_mode` | No | Sets StateMode in MQTT message (default: `"SendStore"`) | `"StoreOnly"` |

**Note:** The parameter is named `filters` instead of `filter` because "filter" is a reserved word.

**Example:**

```yaml
service: tasmota_irhvac.set_filters
target:
  entity_id: climate.living_room_ac
data:
  filters: "on"
  state_mode: "SendStore"
```

### `tasmota_irhvac.set_clean`

Controls the clean mode of the air conditioner.

**Parameters:**

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `entity_id` | Yes | The entity ID of the climate device | `climate.living_room_ac` |
| `clean` | Yes | The desired state (`"on"` or `"off"`) | `"on"` |
| `state_mode` | No | Sets StateMode in MQTT message (default: `"SendStore"`) | `"StoreOnly"` |

**Example:**

```yaml
service: tasmota_irhvac.set_clean
target:
  entity_id: climate.living_room_ac
data:
  clean: "on"
  state_mode: "SendStore"
```

### `tasmota_irhvac.set_beep`

Controls the beep sounds of the air conditioner.

**Parameters:**

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `entity_id` | Yes | The entity ID of the climate device | `climate.living_room_ac` |
| `beep` | Yes | The desired state (`"on"` or `"off"`) | `"on"` |
| `state_mode` | No | Sets StateMode in MQTT message (default: `"SendStore"`) | `"StoreOnly"` |

**Example:**

```yaml
service: tasmota_irhvac.set_beep
target:
  entity_id: climate.living_room_ac
data:
  beep: "on"
  state_mode: "SendStore"
```

### `tasmota_irhvac.set_sleep`

Controls the sleep mode of the air conditioner.

**Parameters:**

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `entity_id` | Yes | The entity ID of the climate device | `climate.living_room_ac` |
| `sleep` | Yes | The desired sleep mode value | `"1"` |
| `state_mode` | No | Sets StateMode in MQTT message (default: `"SendStore"`) | `"StoreOnly"` |

**Note:** The `sleep` parameter can be any string value supported by your AC model. Common values include:
- `"-1"`: Sleep mode off
- `"0"`, `"1"`, `"2"`, `"3"`: Different sleep mode levels

**Example:**

```yaml
service: tasmota_irhvac.set_sleep
target:
  entity_id: climate.living_room_ac
data:
  sleep: "1"
  state_mode: "SendStore"
```

### `tasmota_irhvac.set_swingv`

Controls the vertical swing position of the air conditioner.

**Parameters:**

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `entity_id` | Yes | The entity ID of the climate device | `climate.living_room_ac` |
| `swingv` | Yes | The desired vertical position | `"middle"` |
| `state_mode` | No | Sets StateMode in MQTT message (default: `"SendStore"`) | `"StoreOnly"` |

**Supported Values for `swingv`:**
- `"off"`: Swing off
- `"auto"`: Automatic swing
- `"highest"`: Highest position
- `"high"`: High position
- `"middle"`: Middle position
- `"low"`: Low position
- `"lowest"`: Lowest position

**Example:**

```yaml
service: tasmota_irhvac.set_swingv
target:
  entity_id: climate.living_room_ac
data:
  swingv: "middle"
  state_mode: "SendStore"
```

### `tasmota_irhvac.set_swingh`

Controls the horizontal swing position of the air conditioner.

**Parameters:**

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `entity_id` | Yes | The entity ID of the climate device | `climate.living_room_ac` |
| `swingh` | Yes | The desired horizontal position | `"middle"` |
| `state_mode` | No | Sets StateMode in MQTT message (default: `"SendStore"`) | `"StoreOnly"` |

**Supported Values for `swingh`:**
- `"off"`: Swing off
- `"auto"`: Automatic swing
- `"left max"`: Maximum left position
- `"left"`: Left position
- `"middle"`: Middle position
- `"right"`: Right position
- `"right max"`: Maximum right position
- `"wide"`: Wide swing

**Example:**

```yaml
service: tasmota_irhvac.set_swingh
target:
  entity_id: climate.living_room_ac
data:
  swingh: "middle"
  state_mode: "SendStore"
```

## State Mode Parameter

All services support an optional `state_mode` parameter that controls how the state is handled:

- `"SendStore"` (default): Sends the IR command and stores the new state
- `"StoreOnly"`: Only stores the new state without sending an IR command

This parameter is useful in scenarios where you want to update the state in Home Assistant without actually sending a command to the AC.

## Using Services in Automations

### Example: Turn on Turbo Mode When Temperature is High

```yaml
automation:
  - alias: "Turn on AC Turbo when temperature is high"
    trigger:
      platform: numeric_state
      entity_id: sensor.living_room_temperature
      above: 28
    condition:
      condition: state
      entity_id: climate.living_room_ac
      state: 'cool'
    action:
      service: tasmota_irhvac.set_turbo
      target:
        entity_id: climate.living_room_ac
      data:
        turbo: "on"
```

### Example: Turn on Quiet Mode at Night

```yaml
automation:
  - alias: "Turn on AC Quiet Mode at Night"
    trigger:
      platform: time
      at: '22:00:00'
    condition:
      condition: state
      entity_id: climate.living_room_ac
      state: 'on'
    action:
      service: tasmota_irhvac.set_quiet
      target:
        entity_id: climate.living_room_ac
      data:
        quiet: "on"
```

## Creating Template Switches

You can create template switches to control these special features through the UI. Here's an example for creating switches for all special features:

```yaml
switch:
  - platform: template
    switches:
      living_room_ac_econo:
        friendly_name: "Economy Mode"
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
            
  - platform: template
    switches:
      living_room_ac_turbo:
        friendly_name: "Turbo Mode"
        value_template: "{{ is_state_attr('climate.living_room_ac', 'turbo', 'on') }}"
        turn_on:
          service: tasmota_irhvac.set_turbo
          data:
            entity_id: climate.living_room_ac
            turbo: 'on'
        turn_off:
          service: tasmota_irhvac.set_turbo
          data:
            entity_id: climate.living_room_ac
            turbo: 'off'
```

You can add similar template switches for all the special features you want to control.

## Troubleshooting

If the services don't work as expected:

1. Check if your AC model supports the feature you're trying to control
2. Verify that the IR LED has a clear line of sight to the AC's receiver
3. Check the Home Assistant logs for any error messages
4. Try using the Tasmota console to send IR commands directly and observe the response

For more detailed troubleshooting, see the [TROUBLESHOOTING.md](TROUBLESHOOTING.md) file.