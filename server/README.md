# Agora Agent Backend — TTS Vendors Recipe

FastAPI service that owns Agora token generation and agent session lifecycle for
the TTS vendors recipe. It is the service the web client reaches through the
Next.js `/api/*` rewrite proxy (port 8000).

## What this service does

Starts a conversational AI agent whose **TTS leg is selected at runtime** from a
data-driven registry (`src/vendors.py`), while keeping the STT and LLM legs on the
proven keyless configs. It also enables the three flags that drive the web event
surface:

- `data_channel = "rtm"` — routes all events over RTM to the browser
- `enable_metrics = True` — emits per-stage latency (STT, LLM, TTS)
- `enable_error_message = True` — surfaces agent and message errors over RTM

**Pipeline:** `DeepgramSTT(nova-3, en)` → `OpenAI(gpt-4o-mini)` (Agora-managed, keyless) → `<TTS_VENDOR>` (default `minimax`, keyless)

The default `minimax` vendor is Agora-managed (keyless), so the recipe is
**zero-key** out of the box. There is **no separate `llm/` service**.

## The vendor registry

`src/vendors.py` is a data-driven switchboard:

- `REGISTRY` maps each `TTS_VENDOR` value to its builder and required credential
  environment variables.
- `build_vendor(name, env)` builds the vendor, raising `ValueError` listing any
  missing credential env vars.
- `required_env(name)` / `available()` expose the registry.
- `gemini` uses the production global endpoint and requires
  `GEMINI_API_KEY`. It defaults to voice `Puck` and model
  `gemini-3.8-flash-tts` (the SDK defaults); `TTS_VOICE` / `TTS_MODEL`
  override them. Style is left at the SDK default.
- `sarvam` requires `SARVAM_API_KEY` and pins model `bulbul:v3` with speaker
  `ishita` and language `en-IN`; `TTS_MODEL` / `TTS_VOICE` override the model
  and speaker. Sarvam speakers are model-specific, so an overridden speaker
  must exist for the selected model.
- `rime`, `cartesia`, and `fishaudio` default to Agora-managed credentials
  (`credential_mode="managed"`, no key). Setting the vendor key
  (`RIME_API_KEY`, `CARTESIA_API_KEY`, `FISH_API_KEY`) switches to BYOK.
  Fish Audio BYOK also requires `FISH_REFERENCE_ID`; in managed mode it is
  an optional override of the default voice `59cb5986671546eaa6ca8ae6f29f6d22`.
  Managed Cartesia defaults to model `sonic-3.6` and managed Fish Audio to
  backend `s2.1-pro`; in managed mode `TTS_MODEL` overrides them. BYOK keeps
  `sonic-2` / `speech-1.6` and ignores `TTS_MODEL`.

`agent.py` reads `TTS_VENDOR` in `__init__` (no validation) and calls
`build_vendor(self.vendor)` in `start()` — so BYO credentials are validated only
when a conversation starts, and `/get_config` stays key-less.

## Run

Use the repo-root `README.md` for the full local flow (`bun run dev`). To work on
this module directly:

The root commands below select the correct virtualenv interpreter on macOS,
Linux, and Windows, so activation is not required:

```shell
bun run setup:server
bun run backend
```

## Environment

Required:

- `AGORA_APP_ID` — Agora project App ID.
- `AGORA_APP_CERTIFICATE` — Agora project App Certificate.

Optional:

| Variable | Default | Notes |
| --- | :---: | --- |
| `TTS_VENDOR` | `minimax` | Which TTS vendor to build (see the root README Vendors table) |
| `TTS_VOICE` | per-vendor | Optional voice override for the selected vendor |
| `TTS_MODEL` | per-vendor | Optional model override for the selected vendor |
| `TTS_LANGUAGE` | `en` | Optional Smallest AI ISO 639-1 language code |
| `GEMINI_API_KEY` | — | Required when `TTS_VENDOR=gemini` |
| `RIME_API_KEY` | — | Optional; switches Rime from Agora-managed credentials to BYOK |
| `CARTESIA_API_KEY` | — | Optional; switches Cartesia from Agora-managed credentials to BYOK |
| `FISH_API_KEY` | — | Optional; switches Fish Audio from Agora-managed credentials to BYOK (then `FISH_REFERENCE_ID` is required) |
| `FISH_REFERENCE_ID` | `59cb5986671546eaa6ca8ae6f29f6d22` (managed) | Fish Audio voice model ID; optional override in managed mode, required for BYOK |
| `AGENT_GREETING` | built-in | Optional opening line override |

Selecting a BYO `TTS_VENDOR` additionally requires that vendor's credential env
vars (see `required_env` in `src/vendors.py` and the root README). These are
validated when the agent starts, not at construction.

## API

- `GET /get_config` — token + channel/UID config
- `POST /startAgent` — start an agent session (builds the selected TTS)
- `POST /stopAgent` — stop an agent session

The repo-root `bun run verify:local:fastapi` exercises these routes through the
Next proxy using a fake agent (`scripts/run_fake_server.py`), so no live Agora
session is required.
