# ServiceNotFound bug at KNX integration startup/runtime for cover services
I'm developing a custom integration that interacts with KNX cover entities. During initial tests, I ran into `ServiceNotFound` exceptions despite the cover entity reporting `supported_features: 207`, which includes `set_position` and `set_tilt_position`.

This repository contains a minimal integration setup that reproduces the issue:

## Problem Description
My Home Assistant setup includes a KNX integration with a cover entity (e.g., `cover.fenster_buro_ost`). I've observed that while I can successfully control this entity's position and tilt using the Home Assistant UI, attempts to call `cover.set_position` or `cover.set_tilt_position` programmatically from a custom component consistently result in `ServiceNotFound` errors.

This occurs even when:

1. My custom component correctly defines `knx` as a dependency, ensuring it loads after the KNX integration has started.
2. The target KNX cover entity is found and correctly reports its `supported_features` as `207` (indicating support for `SET_POSITION` and `SET_TILT_POSITION`).
3. A check using `hass.services.has_service("cover", "set_position")` or `hass.services.has_service("cover", "set_tilt_position")` explicitly returns `False` at the time of the service call.

This strongly suggests a discrepancy in how KNX cover services are registered or made available for programmatic access within the Home Assistant Core, even after the entity itself is present and functional via the UI.

## Environment
Home Assistant Core: 2025.5.3
Home Assistant Supervisor: 2025.05.3
Home Assistant OS: 15.2
Installation type: Home Assistant OS

## Minimal Reproducible Setup

The following files are located in custom_components/cover_tilt_test/:

### manifest.json
* Minimal required content
* Define `knx` as dependency

### configuration.yaml
* Setup a working KNX cover
* Setup two input_boolean entities
* Setup the test integration `cover_tilt_test`, which is configured with the KNX cover and the two input booleans

### __init__.py
Startup a simple integration which logs out what's going on. The are no other features than switch the cover height and angle between two values depending on the boolean entities.

## Steps to Reproduce
1. Place the provided `manifest.json` and `__init__.py` files into your `custom_components/cover_tilt_test/` directory.
2. Update your `configuration.yaml` with the provided minimal configuration, ensuring `cover.fenster_buro_ost` refers to a functional KNX cover entity in your setup.
3. Perform a full restart of your Home Assistant instance.
4. Observe the Home Assistant logs during startup.
5. After Home Assistant has fully started and is stable, toggle the `input_boolean.test_bug_height_control` or `input_boolean.test_bug_tilt_control` helper in the Home Assistant UI.
6. Observe the Home Assistant logs again.

## Expected Behavior
* Upon startup, the `cover_tilt_test` integration should initialize after `knx`.
* The target entity `cover.fenster_buro_ost` should be found.
* `hass.services.has_service("cover", "set_position")` and `hass.services.has_service("cover", "set_tilt_position")` should return True.
* Subsequent calls to `hass.services.async_call("cover", "set_position", ...)` and `hass.services.async_call("cover", "set_tilt_position", ...)` should execute successfully, as indicated by the entity's `supported_features: 207`.

## Actual Behavior
The following behavior is observed in the Home Assistant logs:


### Startup Log (showing correct loading order):
```
2025-05-27 21:59:14.873 WARNING (SyncWorker_0) [homeassistant.loader] We found a custom integration cover_tilt_test which has not been tested by Home Assistant. This component might cause stability problems, be sure to disable it if you experience issues with Home Assistant
...
2025-05-27 21:59:19.711 INFO (MainThread) [homeassistant.bootstrap] Setting up stage 2: {'timer', 'template', 'go2rtc', 'scene', 'default_config', 'cover', 'knx', 'sun', 'counter', 'tag', 'shopping_list', 'input_select', 'met', 'hardware', 'schedule', 'input_text', 'cover_tilt_test', 'input_button', 'application_credentials', 'input_boolean', 'zone', 'script', 'analytics', 'system_health', 'person', 'input_datetime', 'automation', 'input_number'} | {'backup', 'logger', 'hassio', 'frontend', 'network'}
...
2025-05-27 21:59:21.387 INFO (MainThread) [homeassistant.setup] Setting up knx
2025-05-27 21:59:21.388 INFO (MainThread) [homeassistant.setup] Setup of domain knx took 0.00 seconds
...
2025-05-27 21:59:22.603 INFO (MainThread) [xknx.log] XKNX v3.6.0 starting automatic connection to KNX bus.
...
2025-05-27 21:59:22.738 INFO (MainThread) [homeassistant.components.binary_sensor] Setting up knx.binary_sensor
...
2025-05-27 21:59:22.741 INFO (MainThread) [homeassistant.components.switch] Setting up knx.switch
2025-05-27 21:59:22.741 INFO (MainThread) [homeassistant.components.sensor] Setting up knx.sensor
2025-05-27 21:59:22.748 INFO (MainThread) [homeassistant.components.cover] Setting up knx.cover
...
2025-05-27 21:59:22.761 INFO (MainThread) [homeassistant.components.light] Setting up knx.light
...
2025-05-27 21:59:22.786 INFO (MainThread) [homeassistant.setup] Setting up cover_tilt_test
2025-05-27 21:59:22.786 DEBUG (MainThread) [custom_components.cover_tilt_test] [cover_tilt_test] async_setup called.
2025-05-27 21:59:22.786 DEBUG (MainThread) [custom_components.cover_tilt_test] [cover_tilt_test] Manager initialized for target: cover.fenster_buro_ost
2025-05-27 21:59:22.786 DEBUG (MainThread) [custom_components.cover_tilt_test] [cover_tilt_test] Listeners registered for input_booleans.
2025-05-27 21:59:22.787 DEBUG (MainThread) [custom_components.cover_tilt_test] [cover_tilt_test] Input change detected. Event: None
2025-05-27 21:59:22.787 DEBUG (MainThread) [custom_components.cover_tilt_test] [cover_tilt_test] Check services availability: set_position=False, set_tilt_position=False
2025-05-27 21:59:22.787 DEBUG (MainThread) [custom_components.cover_tilt_test] [cover_tilt_test] Target cover 'cover.fenster_buro_ost' supported_features: 207
2025-05-27 21:59:22.787 DEBUG (MainThread) [custom_components.cover_tilt_test] [cover_tilt_test] Processing height control. New state: off, setting to 80.0%
2025-05-27 21:59:22.787 DEBUG (MainThread) [custom_components.cover_tilt_test] [cover_tilt_test] Calling cover.set_position for cover.fenster_buro_ost with position 80.0
2025-05-27 21:59:22.787 ERROR (MainThread) [custom_components.cover_tilt_test] [cover_tilt_test] Service cover.set_position NOT FOUND for cover.fenster_buro_ost. Error: Action cover.set_position not found
2025-05-27 21:59:22.788 DEBUG (MainThread) [custom_components.cover_tilt_test] [cover_tilt_test] Processing tilt control. New state: off, setting to 80.0%
2025-05-27 21:59:22.788 DEBUG (MainThread) [custom_components.cover_tilt_test] [cover_tilt_test] Calling cover.set_tilt_position for cover.fenster_buro_ost with tilt_position 80.0
2025-05-27 21:59:22.788 ERROR (MainThread) [custom_components.cover_tilt_test] [cover_tilt_test] Service cover.set_tilt_position NOT FOUND for cover.fenster_buro_ost despite supported_features (207). Error: Action cover.set_tilt_position not found
2025-05-27 21:59:22.788 INFO (MainThread) [custom_components.cover_tilt_test] [cover_tilt_test] Integration 'Cover Service Test' successfully set up.
2025-05-27 21:59:22.788 INFO (MainThread) [homeassistant.setup] Setup of domain cover_tilt_test took 0.00 seconds
```

As shown, `cover_tilt_test` starts after KNX, the entity is found and reports `supported_features: 207`, yet `has_service` reports `False` and service calls fail.

### Log during input_boolean toggle (after HA is stable):
```
2025-05-27 22:00:50.180 DEBUG (MainThread) [custom_components.cover_tilt_test] [cover_tilt_test] Input change detected. Event: <Event state_changed[L]: entity_id=input_boolean.test_bug_height_control, old_state=<state input_boolean.test_bug_height_control=off; editable=False, icon=mdi:arrow-expand-vertical, friendly_name=Test Bug Height Control @ 2025-05-27T21:59:19.969970+02:00>, new_state=<state input_boolean.test_bug_height_control=on; editable=False, icon=mdi:arrow-expand-vertical, friendly_name=Test Bug Height Control @ 2025-05-27T22:00:50.174423+02:00>>
2025-05-27 22:00:50.183 DEBUG (MainThread) [custom_components.cover_tilt_test] [cover_tilt_test] Check services availability: set_position=False, set_tilt_position=False
2025-05-27 22:00:50.183 DEBUG (MainThread) [custom_components.cover_tilt_test] [cover_tilt_test] Target cover 'cover.fenster_buro_ost' supported_features: 207
2025-05-27 22:00:50.183 DEBUG (MainThread) [custom_components.cover_tilt_test] [cover_tilt_test] Processing height control. New state: on, setting to 90.0%
2025-05-27 22:00:50.183 DEBUG (MainThread) [custom_components.cover_tilt_test] [cover_tilt_test] Calling cover.set_position for cover.fenster_buro_ost with position 90.0
2025-05-27 22:00:50.184 ERROR (MainThread) [custom_components.cover_tilt_test] [cover_tilt_test] Service cover.set_position NOT FOUND for cover.fenster_buro_ost. Error: Action cover.set_position not found
2025-05-27 22:00:50.184 DEBUG (MainThread) [custom_components.cover_tilt_test] [cover_tilt_test] Processing tilt control. New state: off, setting to 80.0%
2025-05-27 22:00:50.184 DEBUG (MainThread) [custom_components.cover_tilt_test] [cover_tilt_test] Calling cover.set_tilt_position for cover.fenster_buro_ost with tilt_position 80.0
2025-05-27 22:00:50.185 ERROR (MainThread) [custom_components.cover_tilt_test] [cover_tilt_test] Service cover.set_tilt_position NOT FOUND for cover.fenster_buro_ost despite supported_features (207). Error: Action cover.set_tilt_position not found
```
Even after Home Assistant has fully started, the `has_service` checks still return `False`, and service calls continue to fail.

## Additional Context
Crucially, controlling `cover.fenster_buro_ost` manually via the Home Assistant UI (after Home Assistant has fully started) works flawlessly for both position and tilt. This strong contradiction suggests that while the UI can access these services, they are not properly registered or available through the standard `hass.services` API for other integrations.

If I'm doing something fundamentally wrong, please let me know!
