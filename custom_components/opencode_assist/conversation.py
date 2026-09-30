"""Conversation entity that forwards Assist turns to the OpenCode gateway."""

import logging

import aiohttp

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CONF_TOKEN, CONF_URL, TURN_TIMEOUT

_LOGGER = logging.getLogger(__name__)

UNAVAILABLE = "Asystent jest teraz niedostępny. Sprawdź, czy komputer i model działają."


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
    async_add_entities([OpenCodeConversationEntity(entry)])


class OpenCodeConversationEntity(conversation.ConversationEntity):
    _attr_has_entity_name = True
    _attr_name = None
    _attr_supports_streaming = False

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = entry.entry_id
        # Home Assistant conversation id -> OpenCode session id. Lost on
        # restart, which only starts a fresh conversation.
        self._sessions: dict[str, str] = {}

    @property
    def supported_languages(self) -> str:
        return MATCH_ALL

    async def _async_handle_message(
        self, user_input: conversation.ConversationInput, chat_log: conversation.ChatLog
    ) -> conversation.ConversationResult:
        user = None
        if user_input.context.user_id and (
            ha_user := await self.hass.auth.async_get_user(user_input.context.user_id)
        ):
            user = ha_user.name

        try:
            async with async_get_clientsession(self.hass).post(
                f"{self._entry.data[CONF_URL]}/conversation",
                json={
                    "text": user_input.text,
                    "conversation_id": self._sessions.get(chat_log.conversation_id),
                    "user": user,
                },
                headers={"Authorization": f"Bearer {self._entry.data[CONF_TOKEN]}"},
                timeout=aiohttp.ClientTimeout(total=TURN_TIMEOUT),
            ) as resp:
                resp.raise_for_status()
                body = await resp.json()
            answer = body["text"]
            self._sessions[chat_log.conversation_id] = body["conversation_id"]
        except (aiohttp.ClientError, TimeoutError, KeyError, ValueError) as err:
            _LOGGER.warning("OpenCode gateway turn failed: %s", err)
            answer = UNAVAILABLE

        chat_log.async_add_assistant_content_without_tools(
            conversation.AssistantContent(agent_id=user_input.agent_id, content=answer)
        )
        return conversation.async_get_result_from_chat_log(user_input, chat_log)
