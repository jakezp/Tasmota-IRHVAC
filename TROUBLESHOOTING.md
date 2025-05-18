# Troubleshooting Guide for Tasmota IRHVAC

This guide provides solutions for common issues you might encounter when using the Tasmota IRHVAC integration.

## Table of Contents

1. [Setup Issues](#setup-issues)
2. [Connection Issues](#connection-issues)
3. [Command Issues](#command-issues)
4. [State Reporting Issues](#state-reporting-issues)
5. [Protocol-Specific Issues](#protocol-specific-issues)
6. [Advanced Troubleshooting](#advanced-troubleshooting)
7. [FAQ](#frequently-asked-questions)

## Setup Issues

### Integration Not Found

**Issue**: The Tasmota IRHVAC integration doesn't appear in the integrations list.

**Solution**:
- Make sure you've installed the integration correctly
- Restart Home Assistant after installation
- If using HACS, verify the integration is properly installed through HACS

### Configuration Errors

**Issue**: Error messages during configuration.

**Solution**:
- Check that all required fields are filled correctly
- Verify your Tasmota device is accessible at the provided IP address
- Ensure your MQTT broker is properly configured in Home Assistant
- Check the Home Assistant logs for specific error messages

### Entity Not Created

**Issue**: The climate entity doesn't appear after configuration.

**Solution**:
- Check Home Assistant logs for errors
- Verify that the MQTT topics are correct
- Restart Home Assistant
- Try removing and re-adding the integration

## Connection Issues

### MQTT Connection Problems

**Issue**: The integration shows as unavailable or disconnected.

**Solution**:
- Verify your MQTT broker is running
- Check MQTT credentials in both Home Assistant and Tasmota
- Ensure the MQTT topics match between Tasmota and the integration configuration
- Check if the availability topic is correctly set

### Tasmota Device Unreachable

**Issue**: Cannot connect to the Tasmota device.

**Solution**:
- Verify the device is powered on and connected to your network
- Check if the IP address is correct (Tasmota devices may change IP if using DHCP)
- Try pinging the device or accessing its web interface
- Check if authentication credentials are correct

## Command Issues

### Commands Not Being Sent

**Issue**: The AC doesn't respond to commands from Home Assistant.

**Solution**:
- Check the MQTT command topic in your configuration
- Verify the Tasmota device is receiving the commands (check Tasmota console)
- Ensure the IR LED is properly connected and functioning
- Position the IR LED with a clear line of sight to the AC's receiver

### Commands Sent But AC Doesn't Respond

**Issue**: Commands appear to be sent but the AC doesn't respond.

**Solution**:
- Verify the correct vendor/protocol is selected
- Check if the IR LED is positioned correctly with line of sight to the AC
- Try different hvac_model values if available for your protocol
- Test sending a raw IR command directly through Tasmota console

## State Reporting Issues

### State Not Updating

**Issue**: The climate entity state doesn't update when using the AC remote.

**Solution**:
- Ensure the IR receiver is properly connected and functioning
- Verify the state_topic is correct
- Try using both state_topic and state_topic_2
- Check if the IR receiver has a clear line of sight to the remote

### Incorrect State Reported

**Issue**: The reported state doesn't match the actual AC state.

**Solution**:
- Verify the correct vendor/protocol is selected
- Check if your AC remote uses a different protocol than expected
- Some AC functions may not be correctly decoded by Tasmota
- Try pointing the remote directly at the IR receiver when testing

## Protocol-Specific Issues

### SAMSUNG_AC Issues

**Issue**: Some functions don't work with Samsung ACs.

**Solution**:
- Try different hvac_model values (1, 2, or 3)
- Some Samsung models have limited support for swing modes
- Verify the IR codes using the Tasmota console

### MITSUBISHI_AC Issues

**Issue**: Mode changes don't work correctly.

**Solution**:
- Set `keep_mode_when_off: True` in your configuration
- Some Mitsubishi models require specific swing mode settings

### DAIKIN_AC Issues

**Issue**: Temperature or fan speed issues with Daikin ACs.

**Solution**:
- Daikin often requires specific temperature precision settings
- Try setting precision to 0.5 or 1.0
- Some Daikin models have unique fan speed naming

### Other Protocols

**Issue**: Your AC brand/protocol isn't working correctly.

**Solution**:
- Check if your AC protocol is fully supported by Tasmota
- Try capturing and analyzing the IR codes from your remote
- Some protocols may have limited feature support

## Advanced Troubleshooting

### Debugging with Tasmota Console

To troubleshoot IR command issues:

1. Access your Tasmota device's web interface
2. Go to the Console
3. Monitor for IR received messages when using your remote
4. Test sending IR commands directly:
   ```
   IRhvac {"Vendor":"SAMSUNG_AC", "Power":"On", "Mode":"Cool", "Temp":23}
   ```
5. Check for any error messages or unexpected behavior

### Analyzing IR Codes

If your AC isn't responding correctly:

1. Use your original remote and point it at the IR receiver
2. Capture the IR codes in the Tasmota console
3. Compare the received codes with what the integration is sending
4. You may need to use raw IR codes if the protocol isn't fully supported

### Logging

Enable debug logging for the integration:

1. Add the following to your `configuration.yaml`:
   ```yaml
   logger:
     default: info
     logs:
       custom_components.tasmota_irhvac: debug
   ```
2. Restart Home Assistant
3. Check the logs for detailed information about commands and state changes

## Frequently Asked Questions

### Can I control multiple ACs with one Tasmota device?

Yes, you can create multiple climate entities pointing to the same Tasmota device but with different configuration settings. However, the IR LED must be positioned to reach all AC units.

### My AC has features not available in the integration. Can I add them?

You can use the raw IR sending capability through scripts to send any IR command your AC supports, even if it's not directly exposed in the integration.

### Why does my AC show as unavailable sometimes?

This usually happens when there are MQTT connection issues or if the Tasmota device is unreachable. Check your network connection and MQTT broker status.

### Can I use this integration without an IR receiver?

Yes, but you won't be able to track state changes made with the original remote. The IR receiver is optional but recommended for the best experience.

### My AC temperature display doesn't match Home Assistant. Why?

Some ACs display temperatures differently than what they actually set. The integration reports the temperature value sent in the IR command, which might differ from what the AC displays.

### How can I create a custom IR command for my AC?

You can use the `mqtt.publish` service to send custom IR commands:

```yaml
service: mqtt.publish
data:
  topic: "cmnd/tasmota_device/IRhvac"
  payload: '{"Vendor":"YOUR_AC_VENDOR", "Power":"On", "Mode":"Cool", "Temp":23, "FanSpeed":"Auto"}'
```

### Can I use this with HomeKit/Google Home/Alexa?

Yes, the climate entity created by this integration can be exposed to these platforms through the standard Home Assistant integrations for those services.

## Still Having Issues?

If you're still experiencing problems after trying these troubleshooting steps:

1. Check the [GitHub repository](https://github.com/user/Tasmota-IRHVAC/issues) for similar issues
2. Gather logs and detailed information about your setup
3. Open a new issue on GitHub with all relevant details