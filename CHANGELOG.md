# Changelog

All notable changes to the Tasmota IRHVAC integration will be documented in this file.

## [2.0.0] - 2025-05-18

### Major Changes
- Complete code restructuring and consolidation
- Added UI configuration flow for easier setup
- Improved error handling and stability
- Added support for more AC protocols and features

### New Features
- **UI Configuration**: Added a step-by-step configuration flow in the Home Assistant UI
- **Options Flow**: Added ability to update configuration after initial setup
- **Enhanced Error Handling**: Better error messages and recovery from connection issues
- **Improved State Management**: More reliable state tracking and updates
- **Service Enhancements**: Added state_mode parameter to all services for more control
- **Documentation**: Comprehensive documentation for all features and configuration options

### Improvements
- Optimized MQTT message handling for better performance
- Enhanced temperature precision handling
- Better support for different AC protocols
- Improved logging for easier troubleshooting
- Code quality improvements and better type hinting
- Better handling of sensor unavailability

### Fixed
- **Samsung AC Turbo Mode**: Fixed Turbo mode detection for Samsung ACs by analyzing the Data field pattern instead of the Turbo parameter
  - Identified specific bit patterns in positions 6 and 7 of the Data field that indicate Turbo mode status
  - Turbo ON pattern: "B" at position 6 and "7" at position 7 (e.g., "0x0292B7000000F001B2FE779011F0")
  - Turbo OFF pattern: "D" at position 6 and "1" at position 7 (e.g., "0x0292D1000000F001D2FE719011F0")
- Improved handling of Turbo mode for non-Samsung ACs by moving Turbo field processing outside vendor-specific code
- Added comprehensive logging for Samsung AC Turbo mode detection
- Added test cases to verify Samsung AC Turbo mode detection for both Samsung and non-Samsung devices

### Breaking Changes
- Configuration structure has been updated (backward compatibility maintained)
- Some service parameters have been standardized
- Default values for some configuration options have changed

### Migration Notes
- Existing YAML configurations will continue to work
- For optimal experience, it's recommended to remove the YAML configuration and set up through the UI
- If using special features (econo, turbo, etc.), check the updated service documentation

## [1.2.0] - 2024-12-15

### Added
- Support for horizontal swing control
- Added set_swingv and set_swingh services
- Support for more AC protocols

### Fixed
- Fixed issues with some AC protocols not responding correctly
- Improved error handling for MQTT connection issues

## [1.1.0] - 2024-06-10

### Added
- Support for temperature precision settings
- Added toggle_list configuration option
- Support for keep_mode_when_off option

### Fixed
- Fixed issues with temperature reporting
- Improved state synchronization

## [1.0.0] - 2023-11-01

### Initial Release
- Basic climate entity functionality
- YAML configuration support
- Support for common AC protocols
- Special feature services (econo, turbo, quiet, etc.)