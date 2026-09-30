# OpenCode Assist

Home Assistant conversation agent that forwards Assist turns to an HTTP
gateway in front of an [OpenCode](https://opencode.ai) agent. Assist on phones,
in the browser and on voice satellites then talks to that agent.

Home Assistant never receives the OpenCode server password. The gateway holds
it, pins the agent and model, and exposes only the endpoint below.

## Gateway contract

```http
POST /conversation
Authorization: Bearer <token>
Content-Type: application/json

{"text": "...", "conversation_id": "ses_..." | null, "user": "Name" | null}
```

Response:

```json
{"text": "...", "conversation_id": "ses_..."}
```

`401` means a wrong token and `400` an empty or malformed request. The
integration validates the token during setup by sending an empty `text` and
expecting `400`.

## Installation

1. In HACS, add this repository as a custom repository of type *Integration*
   and install **OpenCode Assist**.
2. Restart Home Assistant.
3. Add the **OpenCode Assist** integration with the gateway URL and token.
4. In *Settings → Voice assistants*, select it as the conversation agent.

Each Assist conversation maps to one gateway conversation, so follow-up
questions keep context. The mapping is kept in memory; a restart starts fresh
conversations.
