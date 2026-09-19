# Architecture — TTS Vendors Recipe

Two processes. The browser talks only to Next.js `/api/*`, which rewrites to the
agent backend. The agent backend owns Agora tokens and agent lifecycle.

The net-new work in this recipe is the **TTS vendor switchboard** in
`server/src/vendors.py`: a data-driven registry that builds 17 TTS vendors
from a `REGISTRY` mapping. The agent reads `TTS_VENDOR` and swaps only the TTS leg of
the cascade; STT and LLM stay on the proven keyless configs. The default vendor
(`minimax`) is Agora-managed (keyless), so no separate TTS service is needed.

## Request flow

```
Browser
  │  GET /api/get_config            → token + channel/UIDs  (always key-less)
  │  POST /api/startAgent           → start agent session
  ▼
Next.js  (rewrites /api/* → AGENT_BACKEND_URL)
  ▼
Agent backend (server/, :8000)
  │  builds session with:
  │    stt = DeepgramSTT(nova-3, en)
  │    llm = OpenAI(gpt-4o-mini)
  │    tts = build_vendor(TTS_VENDOR)   # validates BYO creds here, in start()
  │    parameters: data_channel=rtm, enable_metrics=true,
  │                enable_error_message=true
  │    advanced_features: enable_rtm=true
  ▼
Agora ConvoAI Cloud
  │  user speech → Deepgram STT (managed, nova-3, en)
  │  text → OpenAI (Agora-managed, keyless, gpt-4o-mini)
  │  reply → <TTS_VENDOR> (default MiniMax, Agora-managed, keyless)
  │  RTM events → browser:
  │    AGENT_STATE_CHANGED, AGENT_METRICS, AGENT_ERROR,
  │    MESSAGE_ERROR, TRANSCRIPT_UPDATED
  ▼
EventTimeline + annotated transcript in the web UI
```

`POST /api/stopAgent { agentId }` ends the session.

## The vendor registry

`server/src/vendors.py` is a **data-driven switchboard**:

- `REGISTRY` maps each `TTS_VENDOR` value to its builder and required credential
  environment variables.
- `build_vendor(name, env)` validates those credentials, then calls the vendor's
  builder. Each builder applies its defaults and supported `TTS_MODEL` /
  `TTS_VOICE` overrides; Smallest AI also supports `TTS_LANGUAGE`.
- `available()` / `required_env(name)` expose the registry for tests and docs.

Entries with empty `creds` (`minimax`, `openai`, `rime`) are 🟢 keyless. The framework
code is identical across the sibling vendor recipes; only `CATEGORY` and `REGISTRY`
differ.

## Why creds are validated in start(), not __init__

`Agent.__init__` only reads `TTS_VENDOR` (no credential check). The selected
vendor is built in `start()` via `build_vendor`. This keeps `/get_config` and the
managed docker smoke key-less even when a BYO `TTS_VENDOR` is selected — the call
only fails (with a clear error) once you actually start a conversation.

## Event surface

All events arrive over RTM. The web client uses `AgoraVoiceAI` from
`agora-agent-client-toolkit` to subscribe. Each event is appended to a
`TimelineEvent[]` buffer (capped at 50) and rendered by `EventTimeline`.

| SDK event | Kind | What it carries |
| --- | --- | --- |
| `AGENT_STATE_CHANGED` | `state` | `listening`, `thinking`, `speaking`, `idle` |
| `AGENT_METRICS` | `metric` | Stage type, metric name, value (ms) |
| `AGENT_ERROR` | `error` | Error type + message |
| `MESSAGE_ERROR` | `error` | RTM message error code + message |
| `TRANSCRIPT_UPDATED` | `turn` | Role (agent/user) + text snippet |

## API (agent backend, port 8000)

| Endpoint | Method | Description |
| --- | --- | --- |
| `/get_config` | GET | Token + channel/UID config |
| `/startAgent` | POST | Start the agent session (builds the selected TTS) |
| `/stopAgent` | POST | Stop the agent by `agent_id` |

The browser calls these as `/api/*`; Next rewrites them to `AGENT_BACKEND_URL`.

## Auth

- Browser → agent backend: none (local dev).
- Agent backend → Agora cloud: Token007, generated from `AGORA_APP_ID` +
  `AGORA_APP_CERTIFICATE`.
- Agora cloud → TTS vendor: on the default `minimax` vendor, an Agora-managed key
  (transparent to this recipe). For any BYO vendor, the credentials you supply in
  the environment are passed through in the vendor config.
