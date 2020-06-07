import configparser
from .somfy import Somfy
import logging

from datetime import timedelta
import logging

import voluptuous as vol

import homeassistant.components.alarm_control_panel as alarm
from homeassistant.components.alarm_control_panel.const import (
    SUPPORT_ALARM_ARM_AWAY
)
from homeassistant.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_DISARMED,
    STATE_ALARM_ARMING,
    STATE_ALARM_DISARMING
)

from . import DOMAIN as SOMFY_DOMAIN

DEFAULT_ALARM_NAME = "Somfy Protexiom Alarm"
ACTIVATION_ALARM_CODE = None
ALARM_STATE = None

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_entities, discovery_info=None):
    alarms = []

    controller = hass.data[SOMFY_DOMAIN]["controller"]

    alarms.append(SomfyAlarm(hass, controller))
    add_entities(alarms)


def set_arm_state(state, hass, somfy, code=None):
    """Send set arm state command."""
    _LOGGER.debug("########## Somfy set arm state  ################")
    _LOGGER.debug("Somfy set arm state %s, Code ", state, code)
    ACTIVATION_ALARM_CODE = hass.data[SOMFY_DOMAIN]["activation_alarm_code"]
    _LOGGER.debug("Somfy activation_alarm_code %s", ACTIVATION_ALARM_CODE)

    if ACTIVATION_ALARM_CODE is not None and code != ACTIVATION_ALARM_CODE:
        _LOGGER.debug("Wrong activation code %s and %s", code, ACTIVATION_ALARM_CODE)
        return

    try: 
        _LOGGER.debug("Somfy Loggin - Start")
        somfy.login()
        _LOGGER.debug("Somfy Loggin - End")
        if state.lower() == STATE_ALARM_DISARMED.lower():
            _LOGGER.debug("Somfy protexiom desactivate alarm - Start") 
            _activate_result = somfy.unset_all_zone()
            _LOGGER.debug("Somfy protexiom desactivate alarm - End") 
        elif state.lower() == STATE_ALARM_ARMED_AWAY.lower():
            _LOGGER.debug("Somfy protexiom alarm activation - Start") 
            _activate_result = somfy.set_all_zone()
            _LOGGER.debug("Somfy protexiom alarm activation - End") 
        else:
            _LOGGER.debug("No match")
    except:
        _LOGGER.debug("Somfy could not activate alarm")
        _LOGGER.debug("Error when trying to log in")
    try:    
        _state_result = somfy.get_state()
        _LOGGER.debug("state")
        _LOGGER.debug(_state_result)
    except:
        _LOGGER.debug("Error when trying to get state")    
    try:
        somfy.logout()
        hass.data[SOMFY_DOMAIN]["state"] = _state_result
    except:
        _LOGGER.debug("Error when trying to log out !")


class SomfyAlarm(alarm.AlarmControlPanel):

    def __init__(self, hass, controller):
        self._state = None
        self.somfy = controller
        self._hass = hass
        self._changed_by = None

    @property
    def name(self):
        """Return the name of the device."""
        return DEFAULT_ALARM_NAME

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        return SUPPORT_ALARM_ARM_AWAY

    @property
    def code_format(self):
        """Return one or more digits/characters."""
        return alarm.FORMAT_NUMBER

    @property
    def changed_by(self):
        """Return the last change triggered by."""
        return self._changed_by

    def update(self):
        """Update alarm status."""
        _LOGGER.debug("########## Control Panel Update  ################")
        state = self._hass.data[SOMFY_DOMAIN]["state"]
        _LOGGER.debug("########## State A %s B %s C %s ################",state['zone_a'],state['zone_b'],state['zone_c'])
        _LOGGER.debug("########## State B %s ################",state['zone_b'])
        _LOGGER.debug("########## State C %s ################",state['zone_c'])
        #   "zone_a": {"OFF": STATE_ON,"ON": STATE_OFF},
        #   "zone_b": {"OFF": STATE_ON,"ON": STATE_OFF},
        #   "zone_c": {"OFF": STATE_ON,"ON": STATE_OFF},
        #if state['alarm'] == "Pas d'alarme\n" :
        #    self._state = STATE_ALARM_DISARMED
        #else:
        #    self._state = STATE_ALARM_ARMED_AWAY
        if state['zone_a'] == "ON" and state['zone_b'] == "ON" and state['zone_c'] == "ON":
            self._state = STATE_ALARM_DISARMED
        else:
            self._state = STATE_ALARM_ARMED_AWAY
        _LOGGER.debug("########## End Control Panel Update : State Alarm : %s ################", self._state)
        
    def alarm_disarm(self, code=None):
        """Send disarm command."""
        _LOGGER.debug("########## Control Panel Disarm  ################")
        set_arm_state("DISARMED", self._hass, self.somfy, code)

    def alarm_arm_home(self, code=None):
        """Send arm home command."""
        _LOGGER.debug("########## Control Panel Armed Home  ################")
        set_arm_state("ARMED_HOME", self._hass, self.somfy, code)

    def alarm_arm_away(self, code=None):
        """Send arm away command."""
        _LOGGER.debug("########## Control Panel Armed Away  ################")
        set_arm_state("ARMED_AWAY", self._hass, self.somfy, code)
