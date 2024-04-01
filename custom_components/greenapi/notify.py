import logging
import voluptuous as vol
from whatsapp_api_client_python import API
import homeassistant.helpers.config_validation as cv
from homeassistant.components.notify import (
    ATTR_TARGET, ATTR_TITLE, PLATFORM_SCHEMA, BaseNotificationService)

ATTR_INSTANCE = "instance_id"
ATTR_TOKEN = "token"


_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(ATTR_TARGET): cv.string,
    vol.Required(ATTR_INSTANCE): cv.string,
    vol.Required(ATTR_TOKEN): cv.string,
    vol.Optional(ATTR_TITLE): cv.string,
})

def get_service(hass, config, discovery_info=None):
    """Get the custom notifier service."""
    target = config.get(ATTR_TARGET)
    title = config.get(ATTR_TITLE)
    token = config.get(ATTR_TOKEN)
    instance_id = config.get(ATTR_INSTANCE)
    return GreenAPINotificationService(target, title, token, instance_id)

class GreenAPINotificationService(BaseNotificationService):
    
    def __init__(self, target, title, token,instance_id):
        """Initialize the service."""
        self._targets = target.split(',')
        self._title = title
        self._token = token
        self._instance_id = instance_id
        self._greenAPI = API.GreenAPI(self._instance_id, self._token)

    def send_message(self, message="", **kwargs):
        """Send a message to the target."""
        try:
            for target in self._targets:
                _LOGGER.info("Sending message to %s: %s", target, message)
                self._greenAPI.sending.sendMessage(target, message)
        except Exception as e:
            _LOGGER.error("Sending message to %s: %s has failed with the following error %s", self._target, message, str(e))