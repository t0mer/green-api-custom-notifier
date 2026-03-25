"""Config flow for GreenAPI WhatsApp notifier."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries

from .const import CONF_INSTANCE_ID, CONF_NAME, CONF_TOKEN, DOMAIN

_SETUP_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): str,
        vol.Required(CONF_INSTANCE_ID): str,
        vol.Required(CONF_TOKEN): str,
    }
)


class GreenAPIConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the initial setup wizard."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_INSTANCE_ID])
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=_SETUP_SCHEMA,
        )
