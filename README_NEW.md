[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)

**work in progress**

# Tasmota-IRHVAC (modified to configure devices in the UI)
Home Assistant platform for controlling IR Air Conditioners via Tasmota IRHVAC command and compatible hardware
This platform can **control hunderds of Air Conditioners**, out of the box, via **Tasmota IR transceivers**. It is based on the latest ***“tasmota-ircustom.bin”*** (tested successfully with Tasmota-ir v14.1.1). Currently it **works on Home Assistant 2024.12.1 (or newer)** (Tested successfully with Home Assistant 2025.01)
All additional testing and development done on the [ESP01M](https://www.aliexpress.com/item/1005005541358624.html)

## Forked from - Tasmota-IRHVAC
This repo is forked from [christo-atanasov](https://github.com/hristo-atanasov)'s [Tasmota-IRHVAC](https://github.com/hristo-atanasov/Tasmota-IRHVAC) repo. He did all the hard work, and I am not claiming any of his work as my own. I've modified his code to allow me to add the Tasmota IR devices using the HA UI. I am not claiming any of this work as my own, but I did modify it to meet my specific use case. 

## Hardware setup
1. Flash the latest version of Tasmota_IR firmware using the [Tasmota web flasher](https://tasmota.github.io/install/)
2. After flashing the device, connect to the tasmota_xxxx wifi created
3. Open http://192.168.4.1 and configure the your wifi, the save and reboot.

## Tasmota configuration
Once connected, follow the steps below to configure the device.

### Configuration -> Other
Enter the following in the template field, and select *Activate* (if you are using the ESP01M)
```json
{"NAME":"Tasmota IR-Gateway","GPIO":[0,0,0,0,1056,0,0,0,0,0,1088,0,0,0],"FLAG":0,"BASE":18}
```
![image2](/images/configure_other.png)

Enter a *Web Admin Password*, descriptive *Device Name* and *Friendly Name* (all optional) and save the configuration. If you configured a password, you will be prompted for credentials after reboot. Username: *admin*, and the password you configured.

### Configuration -> MQTT
Enter your MQTT details here and save
![image3](/images/configure_mqtt.png)

## Identify your AC
After configuration open the Tasmota console, point your AC remote to the IR receiver and press the button for turning the AC on. If everything in working, you should see a line like below (example with Fujitsu Air Conditioner). Note down the protocol.
```json
{'IrReceived': {'Protocol': 'FUJITSU_AC', 'Bits': 128, 'Data': '0x0x1463001010FE09304013003008002025', 'Repeat': 0, 'IRHVAC': {'Vendor': 'FUJITSU_AC', 'Model': 1, 'Power': 'On', 'Mode': 'fan_only', 'Celsius': 'On', 'Temp': 20, 'FanSpeed': 'Auto', 'SwingV': 'Off', 'SwingH': 'Off', 'Quiet': 'Off', 'Turbo': 'Off', 'Econo': 'Off', 'Light': 'Off', 'Filter': 'Off', 'Clean': 'Off', 'Beep': 'Off', 'Sleep': -1}}}
```
If vendor is not *‘Unknown’* and you see the *‘IRHVAC’* key, containing information, you can be sure that it will work for you.

## Install HA custom component
Next step is to install Tasmota Irhvac in Home assistant. You have 2 options.

### Option 1: Using HACS

Restart Home Assistant!
### Option 2: Manual installation
Download the files from this repo, and copy the folder named *"tasmota_irhvac"* to *"/config/custom_components"* folder on your Home Assistant service.
Reastart Home Assistant!

## Discovery AC modes and settings
Use your AC remote and the IR Transceiver do the following steps to find the AC values that you have to fill in the next section. View the Tasmota IR console while while pushing the buttons on your remote. They will appear in the ‘IrReceived’ JSON line (mentioned earlier).
* Cycle through all AC modes, using the mode button. Focus on the `"Mode":"XXX"` values, and note these down to use in the next section.
* Cycle through all fan speeds, using the fan button(s). Focus on the `"FanSpeed":"XXX"` values, and note these down to use in the next section.
* Note down minimum and maximum temperatures for your AC
* If you have any other functions, like *turbo*, *clean*, *quite*, push those buttons and note the changes in the Tasmota IR console.

## Configure your Tasmota IR device in Home Assistant
Go to Settings -> Devices & Services
Select *+ ADD INTEGRATION* and search for **Tasmota Irhvac**
When prompted, enter your Tasmota IR device IP address (and optionally the username as *admin* and your device password, if set)
Follow the setup steps, filling in all the required values based on what you discover in the previous section.
Once completed, your device can be used in Home Assistant, by configuring a thermostat card.

----

### Information from the original [README.md](https://github.com/hristo-atanasov/Tasmota-IRHVAC/blob/master/README.md)

## Schematics to make a Tasmota IT Transceiver
The schematics to make a Tasmota IR Transceiver is shown on the picture. I recommend not to put this 100ohm resistor that is marked with light blue X. If you’re planning to power the board with microUSB and you have pin named *VU* connect the IRLED to it instead of *VIN*.

![image1](/images/schematics.jpeg)

After restart add the config from *"configuration.yaml"* in your *"configuration.yaml"* file, but don’t save it yet, because you’ll need to replace all values with your speciffic AC values.

This is a pic of 2 of my Tasmota IR transceivers, that I have mounted under my ACs so when using the ACs remote they have direct visual and update the state in Home Assistant (yes, it can do that too).

![image2](/images/multisensors.jpeg)

As an addition you can add these 2 scripts from *scripts.yaml* in your *scripts.yaml* and use them to send all kind of HEX IR codes and RAW IR codes, by just naming your multisensors using room name (lowercase) and the word “Multisensor”. Like *“kitchenMultisensor”* or *“livingroomMultisensor”*.

```yaml
ir_code:
  sequence:
  - data_template:
      payload: '{"Protocol":"{{ protocol }}","Bits": {{ bits }},"Data": 0x{{ data }}}'
      topic: 'cmnd/{{ room }}Multisensor/irsend'
    service: mqtt.publish
ir_raw:
  sequence:
  - data_template:
      payload: '0, {{ data }}'
      topic: 'cmnd/{{ room }}Multisensor/irsend'
    service: mqtt.publish
```

You can then use these scripts, for the exmple, in a *button card*. Create a new card, put inside it the content of the *card_configuration.yaml*, change *bits:*, *data:*, *protocol:* and *room:* with your desired values and test it. :)

```yaml
cards:
  - cards:
      - action: service
        color: white
        icon: 'mdi:power'
        name: Turn On Audio HEX
        service:
          action: ir_code
          data:
            bits: 12
            data: A80
            protocol: SONY
            room: kitchen
          domain: script
        style:
          - color: white
          - background: green
          - '--disabled-text-color': white
        type: 'custom:button-card'
      - action: service
        color: white
        icon: 'mdi:power'
        name: Turn Off Audio HEX
        service:
          action: ir_code
          data:
            bits: 12
            data: E85
            protocol: SONY
            room: kitchen
          domain: script
        style:
          - color: white
          - background: red
          - '--disabled-text-color': white
        type: 'custom:button-card'
      - action: service
        color: white
        icon: 'mdi:power'
        name: Test AC Raw
        service:
          action: ir_raw
          data:
            data: >-
              3290, 1602,  424, 390,  424, 390,  424, 1232,  398, 390,  424,
              1212,  420, 390,  424, 390,  424, 390,  424, 1232,  398, 1234, 
              398, 390,  424, 390,  426, 390,  424, 1232,  400, 1230,  398,
              392,  424, 390,  426, 390,  426, 390,  424, 390,  424, 390,  424,
              390,  424, 392,  424, 390,  424, 392,  424, 390,  424, 390,  424,
              390,  424, 1232,  398, 390,  424, 390,  426, 390,  424, 390,  424,
              392,  424, 390,  424, 392,  426, 1230,  400, 390,  424, 390,  426,
              390,  424, 390,  424, 1232,  400, 1232,  398, 1232,  398, 1232, 
              400, 1232,  398, 1232,  400, 1232,  400, 1232,  400, 390,  426,
              390,  424, 1206,  424, 390,  424, 390,  424, 392,  424, 390,  424,
              392,  424, 390,  426, 390,  424, 390,  424, 1230,  402, 1230, 
              402, 390,  424, 390,  424, 1230,  402, 390,  424, 390,  424, 390, 
              424, 390,  424, 390,  426, 390,  424, 1230,  402, 1228,  402,
              390,  424, 390,  424, 390,  426, 390,  424, 390,  426, 390,  424,
              390,  424, 390,  426, 390,  426, 390,  424, 390,  424, 390,  426,
              390,  424, 390,  424, 392,  426, 390,  424, 390,  424, 392,  424,
              390,  424, 390,  424, 390,  424, 390,  424, 390,  424, 390,  424,
              390,  424, 390,  426, 390,  426, 390,  424, 390,  424, 392,  424,
              390,  424, 390,  424, 390,  424, 390,  424, 392,  424, 390,  424,
              390,  424, 390,  426, 390,  424, 392,  424, 390,  424, 392,  424,
              390,  424, 390,  424, 1228,  404, 388,  424, 390,  424, 392,  424,
              1228,  404, 1228,  402, 1228,  402, 390,  426, 1228,  402, 390, 
              424, 390,  424
            room: bedroom
          domain: script
        style:
          - color: white
          - background: blue
          - '--disabled-text-color': white
        type: 'custom:button-card'
    type: vertical-stack
type: vertical-stack
```

More info about parts needed and discussion about it: [IN THIS HA COMMUNITY THREAD](https://community.home-assistant.io/t/tasmota-mqtt-irhvac-controler/162915/31)
