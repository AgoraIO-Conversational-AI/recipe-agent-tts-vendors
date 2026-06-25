# 01 · Setup

> Install dependencies, configure env, and run the TTS vendors recipe locally. **Zero-key by default** — the full pipeline runs without any TTS API key on the managed `minimax` vendor.

## Prerequisites

- Python 3.10+ (backend runs on 3.10 and 3.13 in CI)
- [Bun](https://bun.sh/) (runs the web app and orchestration scripts)
- [Agora CLI](https://github.com/AgoraIO/cli) (optional; easiest way to mint App ID + Certificate)

## Install

```bash
bun run setup            # installs web deps + creates server/ venv from requirements.txt
```

`setup` runs `setup:env` (copies `server/.env.example` → `server/.env.local` if missing), `setup:server` (recreates `server/venv`, installs `requirements.txt`), and `setup:web` (`bun install`).

## Configure env

Backend env file is `server/.env.local` (template: `server/.env.example`).

| Variable                | Required | Default         | Notes                                                        |
| ----------------------- | :------: | --------------- | ------------------------------------------------------------ |
| `AGORA_APP_ID`          |    ✅    | —               | Agora Console → Project → App ID                             |
| `AGORA_APP_CERTIFICATE` |    ✅    | —               | Agora Console → Project → App Certificate                    |
| `TTS_VENDOR`            |          | `minimax`       | Which TTS vendor to use (keyless managed vendors: `minimax`, `openai`) |
| `TTS_VOICE`             |          | per-vendor      | Optional voice override for the selected vendor              |
| `TTS_MODEL`             |          | per-vendor      | Optional model override for the selected vendor              |
| `AGENT_GREETING`        |          | built-in line   | Optional opening utterance override                          |
| _vendor creds_          |    \*    | —               | Required only for the selected BYO vendor (see below)        |

\* Required only when `TTS_VENDOR` is set to a BYO (non-managed) vendor.

Fill credentials via the Agora CLI or by hand:

```bash
agora login
agora project use <your-project>
agora project env write server/.env.local   # writes App ID + Certificate
# then optionally add TTS_VENDOR + its key for a BYO vendor
```

> Do **not** add `PORT` to `server/.env.example` — see [07_gotchas](07_gotchas.md).

## BYO vendor credentials

The `minimax` and `openai` vendors are Agora-managed (keyless). All others require credentials in `server/.env.local`. Set `TTS_VENDOR=<name>` and the corresponding env vars:

| `TTS_VENDOR` | Required env vars |
| ------------ | ----------------- |
| `minimax` 🟢 | _none_ |
| `openai` 🟢 | _none_ |
| `elevenlabs` | `ELEVENLABS_API_KEY` |
| `cartesia` | `CARTESIA_API_KEY` |
| `deepgram` | `DEEPGRAM_API_KEY` |
| `google` | `GOOGLE_TTS_API_KEY` |
| `amazon` | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION` |
| `microsoft` | `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION` |
| `humeai` | `HUME_API_KEY` |
| `rime` | `RIME_API_KEY` |
| `fishaudio` | `FISH_API_KEY`, `FISH_REFERENCE_ID` |
| `sarvam` | `SARVAM_API_KEY` |
| `murf` | `MURF_API_KEY` |

🟢 = keyless (Agora-managed). Missing creds for a BYO vendor raise a clear `ValueError` listing the exact env vars when the conversation starts — not at server boot.

## Run

```bash
bun run dev              # backend (:8000) + web (:3000) via concurrently
```

Open <http://localhost:3000> → **Start Conversation** → pick a vendor from the dropdown → speak. Watch the **Event Timeline** update in real time. Backend API docs at <http://localhost:8000/docs>.

## Quick commands

```bash
bun run doctor           # shared prereqs (bun + node_modules); no creds needed
bun run doctor:local     # + .env.local + AGORA_APP_ID/CERTIFICATE present
bun run verify           # web-only gate (doctor + api contracts + web build)
bun run verify:local     # full local gate: backend compile + fastapi smoke + proxy + web build
bun run clean            # remove venvs and build artifacts
```

Backend unit tests run standalone (no cloud, no creds):

```bash
cd server && pytest tests -v
```

## Related Deep Dives

- [tts_vendor_matrix](L2/tts_vendor_matrix.md) — full vendor matrix with all SDK constructors and credential details.
