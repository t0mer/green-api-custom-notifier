"""GreenAPI WhatsApp notification service (legacy YAML path)."""

from __future__ import annotations

import logging
import os
from os.path import basename
from urllib.parse import urlparse

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.notify import (
    ATTR_DATA,
    ATTR_TARGET,
    ATTR_TITLE,
    PLATFORM_SCHEMA,
    BaseNotificationService,
)

from .const import CONF_INSTANCE_ID, CONF_TOKEN

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(ATTR_TARGET): cv.string,
        vol.Required(CONF_INSTANCE_ID): cv.string,
        vol.Required(CONF_TOKEN): cv.string,
        vol.Optional(ATTR_TITLE): cv.string,
    }
)


async def async_get_service(hass, config, discovery_info=None):
    """Get the GreenAPI notification service (YAML path)."""
    from whatsapp_api_client_python import API  # noqa: PLC0415

    return GreenAPINotificationService(
        token=config[CONF_TOKEN],
        instance_id=config[CONF_INSTANCE_ID],
        target=config.get(ATTR_TARGET),
        api=API,
    )


class GreenAPINotificationService(BaseNotificationService):

    def __init__(self, token: str, instance_id: str, target: str | None, api) -> None:
        self._token = token
        self._instance_id = instance_id
        self._target = target
        self._greenAPI = api.GreenAPI(self._instance_id, self._token)

    def send_message(self, message: str = "", **kwargs) -> None:
        """Send a message to the target."""
        try:
            title = kwargs.get(ATTR_TITLE)
            if title is not None:
                message = f"*{title}*\n{message}"

            targets = kwargs.get(ATTR_TARGET)
            target = targets[0] if targets is not None else self._target

            _LOGGER.info("Sending message to %s", target)

            data = kwargs.get(ATTR_DATA)
            if data is not None:
                file_path = data.get("file")
                if file_path is not None:
                    if os.path.exists(file_path):
                        upload_response = self._greenAPI.sending.uploadFile(file_path)
                        if upload_response.code != 200:
                            raise Exception(
                                upload_response.code,
                                f"Failed to upload file: {file_path}",
                            )
                        url_file = upload_response.data["urlFile"]
                        file_name = basename(urlparse(url_file).path)
                        self._greenAPI.sending.sendFileByUrl(
                            target, url_file, file_name, caption=message
                        )
                        return
                    else:
                        _LOGGER.warning(
                            "Sending message to %s: file '%s' not found, sending text only",
                            target,
                            file_path,
                        )

            self._greenAPI.sending.sendMessage(target, message, linkPreview=False)

        except Exception as e:
            _LOGGER.error("Failed to send message to %s: %s", target, e)
