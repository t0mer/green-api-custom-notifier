import logging
import mimetypes
import os
import tempfile
from os.path import basename
from urllib.parse import unquote, urlparse

import requests
import voluptuous as vol
from whatsapp_api_client_python import API
import homeassistant.helpers.config_validation as cv
from homeassistant.components.notify import (
    ATTR_TARGET, ATTR_TITLE, ATTR_DATA, PLATFORM_SCHEMA, BaseNotificationService)

ATTR_INSTANCE = "instance_id"
ATTR_TOKEN = "token"
ATTR_API_URL = "api_url"
ATTR_MEDIA_URL = "media_url"
ATTR_FILE = "file"
ATTR_LINK_PREVIEW = "link_preview"

# Instances with this prefix live on the original cluster, which has no
# instance-specific hostname.
LEGACY_PREFIX = "1101"
DEFAULT_API_URL = "https://api.green-api.com"
DEFAULT_MEDIA_URL = "https://media.green-api.com"
DOWNLOAD_TIMEOUT = 30
# Green-API accepts files up to 100 MB.
MAX_DOWNLOAD_BYTES = 100 * 1024 * 1024

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
        media = _media_from_api(api) or default_media
    else:
        media = default_media
    return api, media


def _media_from_api(api):
    """https://7105.api.greenapi.com -> https://7105.media.greenapi.com"""
    parsed = urlparse(api)
    labels = parsed.netloc.split(".")
    if "api" not in labels:
        return None
    labels[labels.index("api")] = "media"
    return parsed._replace(netloc=".".join(labels)).geturl()


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
        """Send a message to every target."""
        # Allow literal "\n" (as typed in the UI or single-quoted YAML) as a line break.
        message = (message or "").replace("\\n", "\n")
        title = kwargs.get(ATTR_TITLE)
        if title:
            message = f"*{title}*\n{message}"
        data = kwargs.get(ATTR_DATA) or {}
        # A target in the service call overrides the default from the configuration.
        targets = kwargs.get(ATTR_TARGET) or ([self._target] if self._target else [])
        if not targets:
            _LOGGER.error("No target given and no default target configured")
            return

        for target in targets:
            try:
                self._send(target, message, data)
            except Exception as err:  # never let one target break the others
                _LOGGER.error("Sending message to %s failed: %s", target, err)

    def _send(self, target, message, data):
        _LOGGER.info("Sending message to %s", target)
        file = data.get(ATTR_FILE)
        if file:
            if self._send_file(target, file, message):
                return
        response = self._greenAPI.sending.sendMessage(
            target, message, linkPreview=cv.boolean(data.get(ATTR_LINK_PREVIEW, False)))
        _check(response, "sendMessage")

    def _send_file(self, target, file, caption):
        """Send a local file or a file downloaded from an http(s) URL.

        Returns False when the file can't be found, so the text is sent alone.
        """
        if urlparse(file).scheme in ("http", "https"):
            if self.hass is None or not self.hass.config.is_allowed_external_url(file):
                raise ValueError(
                    f"URL '{file}' is not allowed; add it to allowlist_external_urls in the homeassistant configuration")
            with tempfile.TemporaryDirectory() as tmp_dir:
                self._upload_and_send(target, _download(file, tmp_dir), caption)
            return True

        path = self._local_path(file)
        if not os.path.isfile(path):
            _LOGGER.warning("Sending message to %s without the file '%s': file not found", target, path)
            return False
        self._upload_and_send(target, path, caption)
        return True

    def _local_path(self, file):
        # "/local/..." is how the frontend addresses <config>/www.
        if file.startswith("/local/") and self.hass is not None:
            return self.hass.config.path("www", file[len("/local/"):])
        return file

    def _upload_and_send(self, target, path, caption):
        upload = self._greenAPI.sending.uploadFile(path)
        _check(upload, f"uploadFile ({path})")
        url_file = upload.data["urlFile"]
        file_name = basename(urlparse(url_file).path)
        response = self._greenAPI.sending.sendFileByUrl(target, url_file, file_name, caption=caption)
        _check(response, "sendFileByUrl")


def _check(response, action):
    if response.code != 200:
        raise RuntimeError(f"{action} failed: {response.code} {response.error or response.data}")


def _download(url, tmp_dir):
    """Download url into tmp_dir and return the local path."""
    # No redirects: they could lead outside allowlist_external_urls.
    with requests.get(url, timeout=DOWNLOAD_TIMEOUT, allow_redirects=False, stream=True) as response:
        if response.status_code != 200:
            raise RuntimeError(f"downloading {url} failed: HTTP {response.status_code}")
        content = bytearray()
        for chunk in response.iter_content(chunk_size=65536):
            content += chunk
            if len(content) > MAX_DOWNLOAD_BYTES:
                raise RuntimeError(f"downloading {url} failed: larger than {MAX_DOWNLOAD_BYTES} bytes")
        content_type = response.headers.get("Content-Type", "")
    name = basename(unquote(urlparse(url).path)) or "file"
    if not os.path.splitext(name)[1]:
        name += mimetypes.guess_extension(content_type.split(";")[0].strip()) or ""
    path = os.path.join(tmp_dir, name)
    with open(path, "wb") as fh:
        fh.write(content)
    return path
