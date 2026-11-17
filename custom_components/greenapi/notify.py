import logging
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
ATTR_API_URL = "api_url"
ATTR_MEDIA_URL = "media_url"

# Instances with this prefix live on the original cluster, which has no
# instance-specific hostname.
LEGACY_PREFIX = "1101"
DEFAULT_API_URL = "https://api.green-api.com"
DEFAULT_MEDIA_URL = "https://media.green-api.com"

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(ATTR_TARGET): cv.string,
    vol.Required(ATTR_INSTANCE): cv.string,
    vol.Required(ATTR_TOKEN): cv.string,
    vol.Optional(ATTR_TITLE): cv.string,
    vol.Optional(ATTR_API_URL): cv.url,
    vol.Optional(ATTR_MEDIA_URL): cv.url,
})


def resolve_hosts(instance_id, api_url=None, media_url=None):
    """Return the (api, media) hosts for an instance.

    Explicit URLs win. Otherwise the instance-specific hosts are derived from
    the first four digits of the instance ID, e.g. 7105 ->
    https://7105.api.greenapi.com and https://7105.media.greenapi.com.
    """
    prefix = str(instance_id)[:4]
    if prefix == LEGACY_PREFIX:
        default_api, default_media = DEFAULT_API_URL, DEFAULT_MEDIA_URL
    else:
        default_api = f"https://{prefix}.api.greenapi.com"
        default_media = f"https://{prefix}.media.greenapi.com"
    api = (api_url or default_api).rstrip("/")
    if media_url:
        media = media_url.rstrip("/")
    elif api_url:
        media = api.replace(".api.", ".media.", 1) if ".api." in api else default_media
    else:
        media = default_media
    return api, media


def get_service(hass, config, discovery_info=None):
    """Get the custom notifier service."""
    api_url, media_url = resolve_hosts(
        config[ATTR_INSTANCE], config.get(ATTR_API_URL), config.get(ATTR_MEDIA_URL))
    return GreenAPINotificationService(
        config.get(ATTR_TITLE),
        config[ATTR_TOKEN],
        config[ATTR_INSTANCE],
        config.get(ATTR_TARGET),
        api_url,
        media_url,
    )


class GreenAPINotificationService(BaseNotificationService):

    def __init__(self, title, token, instance_id, target, api_url, media_url):
        """Initialize the service."""
        self._title = title
        self._target = target
        self._greenAPI = API.GreenAPI(instance_id, token, host=api_url, media=media_url)

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

