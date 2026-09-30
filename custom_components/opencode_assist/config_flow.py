"""Config flow for OpenCode Assist."""

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_TOKEN, CONF_URL, DEFAULT_URL, DOMAIN

SCHEMA = vol.Schema(
    {
        vol.Required(CONF_URL, default=DEFAULT_URL): str,
        vol.Required(CONF_TOKEN): str,
    }
)


class OpenCodeAssistConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            url = user_input[CONF_URL].rstrip("/")
            session = async_get_clientsession(self.hass)
            try:
                # An empty prompt passes authentication and is then rejected
                # with 400, so it checks the token without starting a turn.
                async with session.post(
                    f"{url}/conversation",
                    json={"text": ""},
                    headers={"Authorization": f"Bearer {user_input[CONF_TOKEN]}"},
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status == 401:
                        errors["base"] = "invalid_auth"
                    elif resp.status != 400:
                        errors["base"] = "cannot_connect"
            except (aiohttp.ClientError, TimeoutError):
                errors["base"] = "cannot_connect"
            if not errors:
                self._async_abort_entries_match({CONF_URL: url})
                return self.async_create_entry(
                    title="OpenCode dom", data={CONF_URL: url, CONF_TOKEN: user_input[CONF_TOKEN]}
                )
        return self.async_show_form(step_id="user", data_schema=SCHEMA, errors=errors)
