# Agora Conversational AI — TTS Vendors Recipe (Python)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue)](https://www.python.org/)
[![Bun](https://img.shields.io/badge/bun-latest-black)](https://bun.sh/)

The **TTS vendors** recipe in the Agora Conversational AI recipes family.
A voice assistant whose **TTS leg is a data-driven switchboard** over every
A4.1 TTS vendor. It **runs zero-key on the default `minimax` TTS** (Agora-managed,
no API key required); set `TTS_VENDOR=<x>` plus that vendor's key to swap in any
other voice. The STT and LLM legs stay on the proven keyless configs, so only the
speech leg changes.

**Pipeline:** `DeepgramSTT(nova-3, en)` → `OpenAI(gpt-4o-mini)` (keyless) → **`<TTS_VENDOR>`** (default `minimax`, keyless)

## Vendors

Two ways to pick a vendor:
- **In the UI** — the pre-call screen has a **TTS vendor dropdown**; choose one and
  start. No restart needed. (A "needs key" vendor still requires its env vars set on
  the server; if they're missing, startup reports exactly which.)
- **By env** — set `TTS_VENDOR` (the default for the dropdown) + the vendor's key in
  `server/.env.local`; optionally override the voice with `TTS_VOICE` or the model
  with `TTS_MODEL`.

| Vendor | `TTS_VENDOR` | Required env | Default voice/model |
| --- | --- | --- | --- |
| MiniMax (managed) | `minimax` 🟢 | _none_ | voice `English_captivating_female1`, model `speech_2_6_turbo` |
| OpenAI (managed) | `openai` 🟢 | _none_ | voice `alloy` |
| ElevenLabs | `elevenlabs` | `ELEVENLABS_API_KEY` | voice `21m00Tcm4TlvDq8ikWAM`, model `eleven_turbo_v2_5` |
| Cartesia | `cartesia` | `CARTESIA_API_KEY` | voice `a0e99841-438c-4a64-b679-ae501e7d6091`, model `sonic-2` |
| Deepgram | `deepgram` | `DEEPGRAM_API_KEY` | model `aura-asteria-en` |
| Google | `google` | `GOOGLE_TTS_API_KEY` | voice `en-US-Neural2-F` |
| Amazon Polly | `amazon` | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION` | voice `Joanna` (engine `neural`) |
| Microsoft Azure | `microsoft` | `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION` | voice `en-US-JennyNeural` |
| Hume AI | `humeai` | `HUME_API_KEY` | voice `ito` |
| Rime | `rime` 🟢 | `RIME_API_KEY` (optional) | managed model `mistv3`; BYOK speaker `cove`, model `mistv2` |
| Fish Audio | `fishaudio` | `FISH_API_KEY`, `FISH_REFERENCE_ID` | backend `speech-1.6` |
| Sarvam | `sarvam` | `SARVAM_API_KEY` | speaker `meera`, language `en-IN` |
| Murf | `murf` | `MURF_API_KEY` | SDK default |
| Gradium | `gradium` | `GRADIUM_API_KEY` | SDK default |
| Mistral | `mistral` | `MISTRAL_API_KEY` | voice `en_paul_neutral`, model `voxtral-mini-tts-2603` |

🟢 = keyless. The selected vendor's credentials are validated **when the agent
starts** (not at construction), so `/get_config` always works key-less.

### Sample code — how each vendor is wired

Every vendor is a small, copy-pasteable builder in [`server/src/vendors.py`](server/src/vendors.py)
that shows the real SDK constructor. For example:

```python
from agora_agent.agentkit import vendors as V

# MiniMax — Agora-managed, key-less:
V.MiniMaxTTS(model="speech_2_6_turbo", voice_id="English_captivating_female1")

# OpenAI — Agora-managed, key-less:
V.OpenAITTS(voice="alloy")

# ElevenLabs — set ELEVENLABS_API_KEY:
V.ElevenLabsTTS(
    key=env["ELEVENLABS_API_KEY"],
    model_id="eleven_turbo_v2_5",
    voice_id="21m00Tcm4TlvDq8ikWAM",
    base_url="https://api.elevenlabs.io",
)
```

The agent attaches the chosen one with `.with_tts(build_vendor(name))`; STT
(`DeepgramSTT`) and LLM (`OpenAI`) stay on their key-less configs. To add or
change a vendor, edit its `build_<vendor>` function + the `REGISTRY` line.

## Prerequisites

- [Python 3.10+](https://www.python.org/)
- [Bun](https://bun.sh/)
- [Agora CLI](https://github.com/AgoraIO/cli) — makes generating an App ID + App Certificate easy

## Run It

```bash
# 1. Install web deps + create the Python venv
bun run setup

# 2. Add Agora credentials (CLI), or edit server/.env.local by hand
agora login
agora project use <your-project>          # select which project to use
agora project env write server/.env.local # writes App ID + Certificate

# 3. Run backend + web
bun run dev
```

Open [http://localhost:3000](http://localhost:3000) → **Start Conversation** → speak.
Watch the **Event Timeline** panel update in real time.

To try a different voice, pick it from the **dropdown** on the pre-call screen (no
restart). For a "needs key" vendor, set its key in `server/.env.local` first (see
[Vendors](#vendors)).

### Working from a clone

`bun run setup` creates the Python venv and installs web dependencies.
`bun run dev` brings up both services. You still need Agora credentials in
`server/.env.local` before a conversation can connect.

Services:

- Frontend — http://localhost:3000
- Backend — http://localhost:8000
- API docs — http://localhost:8000/docs

## Deploy

Deploy `web` (Next.js) and `server` (a reachable FastAPI backend). Set
`AGENT_BACKEND_URL` in the web deployment so the Next rewrites reach the backend.

A backend-only Docker image is published to
`ghcr.io/AgoraIO-Conversational-AI/recipe-agent-tts-vendors` on `v*` tags.
It exposes **BACKEND-ONLY** (:8000). On the default `minimax` vendor no separate
TTS container is needed — MiniMax is Agora-managed.

## Environment variables

| Variable | Required | Default | Notes |
| --- | :---: | :---: | --- |
| `AGORA_APP_ID` | ✅ | — | Agora Console → Project → App ID |
| `AGORA_APP_CERTIFICATE` | ✅ | — | Agora Console → Project → App Certificate |
| `TTS_VENDOR` | | `minimax` | Which TTS vendor to use (see [Vendors](#vendors)) |
| `TTS_VOICE` | | per-vendor | Optional voice override for the selected vendor |
| `TTS_MODEL` | | per-vendor | Optional model override for the selected vendor |
| `AGENT_GREETING` | | built-in | Optional opening line override |
| _vendor creds_ | | — | Required only for the selected BYO vendor (see [Vendors](#vendors)) |

## Commands

```bash
bun run setup            # install web deps + create server/ venv
bun run dev              # run backend (:8000) + web (:3000)

bun run doctor           # prerequisite check (no creds needed)
bun run doctor:local     # + .env.local + credentials checks

bun run verify           # web-only gate (no Agora creds needed)
bun run verify:local     # full local gate: backend compile + smoke tests + web build
bun run clean            # remove venvs and build artifacts
```

Tests run standalone (no Agora cloud needed): `pytest` in `server/`, plus
`bun run verify` in `web/`. CI runs them on Linux/macOS/Windows × Python 3.10 & 3.13.

## Architecture

```
Browser (localhost:3000)
  │  fetch /api/*
  ▼
Next.js  ──rewrite──▶  Agent backend  (server/, localhost:8000)
                          │  starts agent session
                          │  TTS leg = build_vendor(TTS_VENDOR)
                          │  flags: enable_rtm=true, enable_metrics=true,
                          │         enable_error_message=true
                          ▼
                       Agora ConvoAI Cloud
                          │  Deepgram STT (managed, en)
                          │  OpenAI (Agora-managed, keyless, gpt-4o-mini)
                          │  <TTS_VENDOR> (default MiniMax, keyless)
                          │  RTM events → browser
                          ▼
                       EventTimeline + annotated transcript in the web UI
```

The TTS vendor switchboard lives in `server/src/vendors.py` — one readable
`build_<vendor>` function per vendor (the sample code) plus a `REGISTRY` mapping
name → builder + required env. See [ARCHITECTURE.md](./ARCHITECTURE.md).

## What You Get

- A **vendor switchboard** for the TTS leg: one readable `build_<vendor>` function
  per vendor (covering all 15 A4.1 TTS vendors), selected via `TTS_VENDOR` or the
  in-UI dropdown.
- A **Next.js** web client (:3000) with a live **EventTimeline** (state, metric,
  error, turn events; reverse-chronological, capped at 50) and an **annotated
  transcript** that shows the current agent state in the header.
- A **FastAPI** agent backend (:8000) that owns Agora token generation and the
  agent session lifecycle.
- **Zero-key by default** — the full pipeline runs with no TTS API key on the
  managed `minimax` vendor.

## How It Works

1. The browser calls `/api/get_config`; the backend mints an Agora token. This
   works key-less even when a BYO `TTS_VENDOR` is selected — credentials are only
   checked at agent start.
2. The browser joins the RTC channel, then calls `/api/startAgent`; the backend
   builds the selected TTS via `build_vendor(TTS_VENDOR)` (raising a clear error
   if a BYO vendor is missing its credentials) and starts the agent with
   `data_channel="rtm"`, `enable_metrics=True`, and `enable_error_message=True`.
3. The agent speaks with the user. Agora emits RTM events for every state change,
   per-stage metric, transcript turn, and error.
4. The web client's `AgoraVoiceAI` SDK receives these events and appends a
   `TimelineEvent` for each one (capped at 50).
5. `EventTimeline` renders the events in reverse-chronological order with a
   colored badge per kind. The transcript header shows the current agent state.
6. `/api/stopAgent` ends the session.

## Repo Map

- `web/` — Next.js frontend (:3000); RTC/RTM lifecycle, EventTimeline, transcript.
- `server/` — FastAPI agent backend (:8000); Agora tokens + agent lifecycle.
- `server/src/vendors.py` — one readable builder per TTS vendor + the registry.
- `ARCHITECTURE.md` — system shape and component boundaries.
- `AGENTS.md` — guide for coding agents working in this repo.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `TTS vendor '<x>' requires environment variable(s): ...` at start | Set the listed env vars for that `TTS_VENDOR` (see [Vendors](#vendors)), or switch back to `minimax`. |
| No events appear in the timeline | Ensure `enable_rtm`, `enable_metrics`, `enable_error_message` are set (they are, by default in this recipe). |
| Local calls fail under a global proxy (Clash, etc.) | Configure your proxy to send `127.0.0.1`, `localhost`, and RFC-1918 ranges DIRECT. |

## More Docs

- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [AGENTS.md](./AGENTS.md)

## License

Released under the [MIT License](./LICENSE).
