import logging
import json
import os
from os.path import basename
from urllib.parse import urlparse
import voluptuous as vol
from whatsapp_api_client_python import API
import homeassistant.helpers.config_validation as cv
from homeassistant.components.notify import (
    ATTR_TARGET, ATTR_TITLE, ATTR_DATA, PLATFORM_SCHEMA, BaseNotificationService)

ATTR_INSTANCE = "instance_id"
ATTR_TOKEN = "token"


_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(ATTR_TARGET): cv.string,
    vol.Required(ATTR_INSTANCE): cv.string,
    vol.Required(ATTR_TOKEN): cv.string,
    vol.Optional(ATTR_TITLE): cv.string,
})

def get_service(hass, config, discovery_info=None):
    """Get the custom notifier service."""
    title = config.get(ATTR_TITLE)
    token = config.get(ATTR_TOKEN)
    instance_id = config.get(ATTR_INSTANCE)
    target = config.get(ATTR_TARGET)
    return GreenAPINotificationService(title, token, instance_id, target)

class GreenAPINotificationService(BaseNotificationService):
    
    def __init__(self, title, token, instance_id, target):
        """Initialize the service."""
        self._title = title
        self._token = token
        self._instance_id = instance_id
        self._target = target
        self._greenAPI = API.GreenAPI(self._instance_id, self._token)

    def send_message(self, message="", **kwargs):
        
        """Send a message to the target."""
        
        try:
            title = kwargs.get(ATTR_TITLE)
            if title is not None:
                title = f"*{title}*"
                message = f"{title}\n{message}"
            data = kwargs.get(ATTR_DATA)
            target = kwargs.get(ATTR_TARGET)[0] if kwargs.get(ATTR_TARGET) is not None else self._target #Allow setting the target from either the service-call or the service config. Service call target can override the default config.
            _LOGGER.info(f"Sending message to {target}")
            if data is not None:
                file_path = data.get("file")
                if file_path is not None:
                    if os.path.exists(file_path):
                        upload_file_response = self._greenAPI.sending.uploadFile(file_path)
                        if upload_file_response.code != 200:
                            raise Exception(upload_file_response.code, "Failed to upload file: " + file_path)
                        url_file = upload_file_response.data["urlFile"]
                        url = urlparse(url_file)
                        file_name = basename(url.path)
                        send_file_by_url_response = self._greenAPI.sending.sendFileByUrl(target, url_file, file_name, caption=message)
                        return
                    else:
                        _LOGGER.warn("Sending message to %s: excluding the file '%s' that was not found", kwargs.get(ATTR_TARGET)[0], file_path)
            self._greenAPI.sending.sendMessage(target, message, linkPreview=False)
        except Exception as e:
            _LOGGER.error("Sending message to %s: has failed with the following error %s", kwargs.get(ATTR_TARGET)[0], str(e))

