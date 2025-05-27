import logging
import voluptuous as vol
from typing import Any

from homeassistant.core import HomeAssistant, callback, Event, State
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.const import ATTR_SUPPORTED_FEATURES
from homeassistant.components.cover import CoverEntityFeature # Benötigt für CoverEntityFeature
from homeassistant.exceptions import ServiceNotFound # Wichtig für den try-except Block

_LOGGER = logging.getLogger(__name__)

DOMAIN = "cover_tilt_test" # Muss mit dem 'domain' in manifest.json übereinstimmen

# Konfigurationsschema für diese Integration (top-level config)
CONF_TARGET_COVER_ENTITY_ID = "target_cover_entity_id"
CONF_HEIGHT_CONTROL_ENTITY_ID = "height_control_entity_id"
CONF_TILT_CONTROL_ENTITY_ID = "tilt_control_entity_id"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema( # Der Konfigurationsblock unter dem Domain-Namen
            {
                vol.Required(CONF_TARGET_COVER_ENTITY_ID): str,
                vol.Required(CONF_HEIGHT_CONTROL_ENTITY_ID): str,
                vol.Required(CONF_TILT_CONTROL_ENTITY_ID): str,
            }
        )
    },
    extra=vol.ALLOW_EXTRA, # Erlaubt andere Top-Level-Keys in configuration.yaml (z.B. 'cover:', 'light:')
)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Cover Service Test integration."""
    _LOGGER.debug(f"[{DOMAIN}] async_setup called.")

    # Konfiguration aus dem config-Dictionary holen
    conf = config[DOMAIN]
    target_cover_entity_id = conf[CONF_TARGET_COVER_ENTITY_ID]
    height_control_entity_id = conf[CONF_HEIGHT_CONTROL_ENTITY_ID]
    tilt_control_entity_id = conf[CONF_TILT_CONTROL_ENTITY_ID]

    # Eine Instanz der Manager-Klasse erstellen, die die Logik enthält
    manager = CoverServiceTestManager(
        hass,
        target_cover_entity_id,
        height_control_entity_id,
        tilt_control_entity_id
    )

    # Listeners registrieren, damit Änderungen an den Input-Boolean Schaltern erkannt werden
    manager._listeners.append(
        async_track_state_change_event(
            hass,
            [height_control_entity_id, tilt_control_entity_id],
            manager._async_handle_input_change,
        )
    )
    _LOGGER.debug(f"[{DOMAIN}] Listeners registered for input_booleans.")

    # Optional: Initialen Check sofort ausführen, um den aktuellen Zustand zu verarbeiten
    await manager._async_handle_input_change(None)

    _LOGGER.info(f"[{DOMAIN}] Integration 'Cover Service Test' successfully set up.")
    return True

class CoverServiceTestManager:
    """Manages the testing of cover service calls."""

    def __init__(
            self,
            hass: HomeAssistant,
            target_cover_entity_id: str,
            height_control_entity_id: str,
            tilt_control_entity_id: str,
    ) -> None:
        self.hass = hass
        self._target_cover_entity_id = target_cover_entity_id
        self._height_control_entity_id = height_control_entity_id
        self._tilt_control_entity_id = tilt_control_entity_id
        self._listeners = []
        _LOGGER.debug(f"[{DOMAIN}] Manager initialized for target: {target_cover_entity_id}")

    @callback
    async def _async_handle_input_change(self, event: Event | None) -> None:
        """Handle changes to input_boolean entities."""
        _LOGGER.debug(f"[{DOMAIN}] Input change detected. Event: {event}")

        has_pos_service = self.hass.services.has_service("cover", "set_position")
        has_tilt_service = self.hass.services.has_service("cover", "set_tilt_position")
        _LOGGER.debug(f"[{DOMAIN}] Check services availability: set_position={has_pos_service}, set_tilt_position={has_tilt_service}")

        height_state = self.hass.states.get(self._height_control_entity_id)
        tilt_state = self.hass.states.get(self._tilt_control_entity_id)

        target_cover_state: State | None = self.hass.states.get(self._target_cover_entity_id)

        if not target_cover_state:
            _LOGGER.error(f"[{DOMAIN}] Target cover entity '{self._target_cover_entity_id}' not found. Cannot proceed.")
            # Es könnte sinnvoll sein, hier den Listener zu entfernen oder eine Wiederholung zu planen,
            # falls die Ziel-Entität später verfügbar wird. Für ein Minimalbeispiel ist es OK so.
            return

        supported_features = target_cover_state.attributes.get(ATTR_SUPPORTED_FEATURES, 0)
        _LOGGER.debug(f"[{DOMAIN}] Target cover '{self._target_cover_entity_id}' supported_features: {supported_features}")

        # --- Höhe setzen ---
        if height_state and height_state.state in ["on", "off"]:
            height_to_set = 90.0 if height_state.state == "on" else 80.0
            _LOGGER.debug(f"[{DOMAIN}] Processing height control. New state: {height_state.state}, setting to {height_to_set}%")

            if supported_features & CoverEntityFeature.SET_POSITION:
                try:
                    _LOGGER.debug(f"[{DOMAIN}] Calling cover.set_position for {self._target_cover_entity_id} with position {height_to_set}")
                    await self.hass.services.async_call(
                        "cover",
                        "set_position",
                        {"entity_id": self._target_cover_entity_id, "position": height_to_set},
                        blocking=True # Blocking, um auf Fertigstellung zu warten
                    )
                    _LOGGER.debug(f"[{DOMAIN}] Successfully called cover.set_position.")
                except ServiceNotFound as e:
                    _LOGGER.error(f"[{DOMAIN}] Service cover.set_position NOT FOUND for {self._target_cover_entity_id}. Error: {e}")
                except Exception as e:
                    _LOGGER.error(f"[{DOMAIN}] Error calling cover.set_position for {self._target_cover_entity_id}: {e}")
            else:
                _LOGGER.warning(f"[{DOMAIN}] Target cover {self._target_cover_entity_id} does not support SET_POSITION. Supported features: {supported_features}")
        else:
            _LOGGER.debug(f"[{DOMAIN}] Height control not active or state not 'on'/'off'. Current height_state: {height_state.state if height_state else 'None'}")


        # --- Winkel setzen ---
        if tilt_state and tilt_state.state in ["on", "off"]:
            angle_to_set = 90.0 if tilt_state.state == "on" else 80.0
            _LOGGER.debug(f"[{DOMAIN}] Processing tilt control. New state: {tilt_state.state}, setting to {angle_to_set}%")

            if supported_features & CoverEntityFeature.SET_TILT_POSITION:
                try:
                    _LOGGER.debug(f"[{DOMAIN}] Calling cover.set_tilt_position for {self._target_cover_entity_id} with tilt_position {angle_to_set}")
                    await self.hass.services.async_call(
                        "cover",
                        "set_tilt_position",
                        {"entity_id": self._target_cover_entity_id, "tilt_position": angle_to_set},
                        blocking=True
                    )
                    _LOGGER.debug(f"[{DOMAIN}] Successfully called cover.set_tilt_position.")
                except ServiceNotFound as e:
                    # DIES IST DIE ERWARTETE FEHLERMELDUNG BEI DEM BUG
                    _LOGGER.error(f"[{DOMAIN}] Service cover.set_tilt_position NOT FOUND for {self._target_cover_entity_id} despite supported_features ({supported_features}). Error: {e}")
                except Exception as e:
                    _LOGGER.error(f"[{DOMAIN}] Error calling cover.set_tilt_position for {self._target_cover_entity_id}: {e}")
            else:
                _LOGGER.warning(f"[{DOMAIN}] Target cover {self._target_cover_entity_id} does not support SET_TILT_POSITION. Supported features: {supported_features}")
        else:
            _LOGGER.debug(f"[{DOMAIN}] Tilt control not active or state not 'on'/'off'. Current tilt_state: {tilt_state.state if tilt_state else 'None'}")