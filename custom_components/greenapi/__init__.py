"""GreenAPI WhatsApp notifier — setup and teardown."""

from __future__ import annotations

import functools
import logging
import os
import re
from dataclasses import dataclass
from os.path import basename
from urllib.parse import urlparse

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall

from .const import CONF_INSTANCE_ID, CONF_NAME, CONF_TOKEN, DOMAIN

_LOGGER = logging.getLogger(__name__)

_NOTIFY_DOMAIN = "notify"

_SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required("message"): cv.string,
        vol.Optional("title"): cv.string,
        vol.Optional("target"): cv.string,
        vol.Optional("data"): dict,
    }
)


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


@dataclass
class GreenAPIData:
    """Runtime data stored on the config entry."""

    instance_id: str
    token: str
    service_name: str


type GreenAPIConfigEntry = ConfigEntry[GreenAPIData]


async def async_setup_entry(hass: HomeAssistant, entry: GreenAPIConfigEntry) -> bool:
    """Set up GreenAPI from a config entry."""
    from whatsapp_api_client_python import API  # noqa: PLC0415

    data = {**entry.data, **entry.options}

    instance_id: str = data[CONF_INSTANCE_ID]
    token: str = data[CONF_TOKEN]
    name: str = data.get(CONF_NAME) or instance_id
    service_name: str = f"greenapi_{_slugify(name)}"

    entry.runtime_data = GreenAPIData(
        instance_id=instance_id,
        token=token,
        service_name=service_name,
    )

    greenapi = API.GreenAPI(instance_id, token)

    async def handle_send_message(call: ServiceCall) -> None:
        message: str = call.data["message"]
        title: str | None = call.data.get("title")
        extra_data: dict | None = call.data.get("data")

        if title:
            message = f"*{title}*\n{message}"

        dest: str | None = call.data.get("target")
        if not dest:
            _LOGGER.error("No target specified — pass 'target' in the service call data")
            return

        _LOGGER.info("Sending message to %s", dest)

        try:
            if extra_data:
                file_path = extra_data.get("file")
                if file_path:
                    if os.path.exists(file_path):
                        upload_response = await hass.async_add_executor_job(
                            greenapi.sending.uploadFile, file_path
                        )
                        if upload_response.code != 200:
                            raise Exception(
                                upload_response.code,
                                f"Failed to upload file: {file_path}",
                            )
                        url_file = upload_response.data["urlFile"]
                        file_name = basename(urlparse(url_file).path)
                        await hass.async_add_executor_job(
                            functools.partial(
                                greenapi.sending.sendFileByUrl,
                                dest,
                                url_file,
                                file_name,
                                caption=message,
                            )
                        )
                        return
                    else:
                        _LOGGER.warning(
                            "Sending message to %s: file '%s' not found, sending text only",
                            dest,
                            file_path,
                        )

            await hass.async_add_executor_job(
                functools.partial(
                    greenapi.sending.sendMessage, dest, message, linkPreview=False
                )
            )
        except Exception as e:
            _LOGGER.error("Failed to send message to %s: %s", dest, e)

    hass.services.async_register(
        _NOTIFY_DOMAIN, service_name, handle_send_message, schema=_SERVICE_SCHEMA
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: GreenAPIConfigEntry) -> bool:
    """Unload a config entry."""
    hass.services.async_remove(_NOTIFY_DOMAIN, entry.runtime_data.service_name)
    return True
