# 02 · Architecture

> Two co-located processes. The browser talks only to Next.js `/api/*`, which rewrites to the FastAPI agent backend. The backend builds a cascading STT→LLM→TTS pipeline where the TTS leg is selected from a data-driven registry of 13 vendors.

## Topology

```
Browser (localhost:3000)
  │  fetch /api/*
  ▼
Next.js (web/)  ──rewrite──▶  Agent backend (server/, :8000)
                                 │  builds cascading pipeline:
                                 │    stt = DeepgramSTT(nova-3, en)
                                 │    llm = OpenAI(gpt-4o-mini)          [keyless]
                                 │    tts = build_vendor(TTS_VENDOR)      [default minimax, keyless]
                                 │  flags: data_channel=rtm, enable_metrics=true,
                                 │         enable_error_message=true, enable_rtm=true
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

- **`web/`** — Next.js 16 / React 19 / TypeScript. Owns UI plus the RTC/RTM client lifecycle. Calls only `/api/*`.
- **`server/`** — Python FastAPI (:8000). Owns Agora token generation, agent lifecycle, and the vendor registry. SDK: `agora-agents>=2.3.0` (`import agora_agent`).
- No `llm/` service. STT and LLM are Agora-managed. Only the TTS leg is swappable.

## Request lifecycle

1. Browser `GET /api/get_config` → Next rewrites to backend `/get_config`; backend mints a Token007 from `AGORA_APP_ID` + `AGORA_APP_CERTIFICATE` and returns channel + UIDs. Always succeeds key-less.
2. Browser fetches `GET /api/vendors`; backend returns the vendor list + default. Pre-call dropdown is populated.
3. Browser joins the RTC channel, then `POST /api/startAgent { channelName, rtcUid, userUid, vendor? }`; backend calls `build_vendor(selected)` — BYO credentials validated here — then starts the async session.
4. Agora routes user audio through Deepgram STT → OpenAI LLM → selected TTS vendor. Agent voice returns into the channel. RTM delivers events.
5. Web client's `AgoraVoiceAI` SDK receives RTM events and appends `TimelineEvent` objects (capped at 50) to `EventTimeline`.
6. `POST /api/stopAgent { agentId }` ends the session.

## The vendor registry

`server/src/vendors.py` is a **data-driven switchboard**:

- `REGISTRY` maps each `TTS_VENDOR` key to `(builder, required_env_list)`.
- `build_vendor(name, env?)` validates that all required env vars are present, then calls the builder. A missing var raises a clear `ValueError` listing the names — never an opaque SDK error.
- `available()` / `required_env(name)` / `needs_key(name)` expose the registry for tests, the `/vendors` endpoint, and docs.
- Entries with empty required lists (`minimax`, `openai`) are Agora-managed and keyless.

## Why creds are validated in start(), not __init__

`Agent.__init__` reads `TTS_VENDOR` but does **not** check vendor credentials. The selected vendor is built in `start()` via `build_vendor`. This keeps `/get_config` and the managed Docker smoke key-less even when a BYO `TTS_VENDOR` is configured — the call fails (with a clear error) only when a conversation actually starts.

## Key abstractions

- **`Agent`** (`server/src/agent.py`) — async wrapper around `AgoraAgent`; owns the `AsyncAgora` client, env, vendor selection, and the in-memory `_sessions` map keyed by `agent_id`.
- **`build_vendor(name)`** (`server/src/vendors.py`) — constructs and returns the SDK TTS vendor object for the given registry key.
- **`EventTimeline`** (`web/src/components/EventTimeline.tsx`) — renders `TimelineEvent[]` in reverse-chronological order; exports the `TimelineEvent` type.
- **Rewrite proxy** (`web/next.config.ts`) — the only browser→backend boundary; no Next Route Handlers exist for agent/token logic.

## Tech decisions

- **Rewrites, not Route Handlers** — hides backend placement behind `/api/*` so the same client works locally and deployed (set `AGENT_BACKEND_URL`).
- **Registry-driven TTS** — adding or changing a vendor is a single-function edit in `vendors.py` without touching `agent.py` or the test suite shape.
- **Creds validated at `start()`** — server boots without BYO vendor keys; clear error only when a conversation starts.
- **RTM event surface** — `data_channel="rtm"` + `enable_metrics=True` + `enable_error_message=True` expose the full event surface (state, metric, error, turn) to the browser.

## Related Deep Dives

- [tts_vendor_matrix](L2/tts_vendor_matrix.md) — every vendor's SDK constructor, credential fields, and defaults.
- [session_lifecycle](L2/session_lifecycle.md) — browser orchestration of config + start/stop, RTC/RTM, EventTimeline wiring.
