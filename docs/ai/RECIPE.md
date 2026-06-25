---
recipe_version: 1.0.0
recipe_status: experimental
extension_points:
  - id: tts.vendor
    name: TTS vendor selection and configuration
  - id: api.routes
    name: Browser-facing API routes
  - id: agent.pipeline-config
    name: STT model/language, LLM model, greeting, session parameters
  - id: web.conversation-ui
    name: Conversation UI panels, EventTimeline, vendor dropdown
  - id: verification.contracts
    name: Contract, proxy, and local FastAPI smoke verification
invariants:
  - id: api.rewrite-boundary
    summary: Browser calls stay on /api/* and Next rewrites to FastAPI; no Route Handlers for agent/token logic.
  - id: secrets.server-only
    summary: Agora App Certificate and any BYO vendor credentials stay in the Python backend.
  - id: tts.registry-driven
    summary: The TTS leg is always built via build_vendor(name) from vendors.py; never hardcode a single vendor in agent.py.
  - id: tts.creds-in-start
    summary: BYO vendor credentials are validated in start(), not __init__, so /get_config stays key-less.
  - id: stt-llm.keyless
    summary: STT (DeepgramSTT nova-3) and LLM (OpenAI gpt-4o-mini) are Agora-managed and keyless; only the TTS leg is swapped.
  - id: token.uid-concrete
    summary: Backend resolves missing, zero, or negative UIDs before issuing an RTC+RTM token.
stable_contracts:
  - id: env.required
    summary: AGORA_APP_ID and AGORA_APP_CERTIFICATE are always required; TTS_VENDOR defaults to minimax (keyless); AGENT_BACKEND_URL is required by deployed web rewrites.
  - id: api.core-routes
    summary: GET /api/get_config, POST /api/startAgent, POST /api/stopAgent, and GET /api/vendors remain the browser-facing contract.
  - id: response.envelope
    summary: Successful backend responses use { code, msg, data }.
  - id: startAgent.vendor-field
    summary: POST /api/startAgent accepts an optional vendor field that overrides TTS_VENDOR for that session; start() returns vendor in the response data.
---

# Recipe Contract

This base recipe defines the reusable surface for a Python-backed Agora Conversational AI **TTS vendors** quickstart: a cascading STT→LLM→TTS pipeline where the TTS leg is a data-driven switchboard across all 13 A4.1 vendors.

## Recipe Role

- Role: `base` recipe (self-contained, clone-and-run; no `Extends` pin).
- Target audience: developers who want to compare TTS vendors side-by-side or build a voice agent with a specific TTS provider.
- Reuse model: clone, bind project, set `TTS_VENDOR` + optional key, run, then swap vendors or customize the pipeline.

## Recipe Scope

- Python FastAPI token generation and managed agent lifecycle.
- Cascading pipeline: `DeepgramSTT(nova-3, en)` → `OpenAI(gpt-4o-mini)` (keyless) → `<TTS_VENDOR>` (13 vendors, default `minimax` keyless).
- Data-driven TTS vendor registry in `server/src/vendors.py` — one readable `build_<vendor>` per vendor.
- In-UI TTS vendor dropdown (pre-call screen) backed by `GET /api/vendors`.
- Next.js browser UI with RTC audio, RTM-driven EventTimeline (state/metric/error/turn), and annotated transcript.
- Rewrite-only `/api/*` browser facade hiding backend placement.
- Contract, proxy, and local FastAPI smoke verification that need no live Agora calls.

## Baseline Implementation Guidance

Use this repo's source and progressive disclosure docs as the starting point, then customize. Do not recreate the Agora ConvoAI integration from memory — vendor schemas, SDK builder fields, token behavior, and RTM details drift. Copy verified patterns from this repo.

## Extension Points

| ID | Surface | How to extend | Required follow-up |
| -- | ------- | ------------- | ------------------ |
| `tts.vendor` | `server/src/vendors.py` | Add a `build_<vendor>` function + entry in `REGISTRY`. | Run `verify:backend` + `pytest tests`; document new vendor in root README Vendors table. |
| `api.routes` | `server/src/server.py`, `web/next.config.ts`, `web/src/services/api.ts` | Add FastAPI route, add rewrite, add browser fetch helper. | Extend `web/scripts/verify-api-contracts.ts`; add proxy/fastapi coverage if it belongs in local verification. |
| `agent.pipeline-config` | `server/src/agent.py` | Change `DeepgramSTT` model/language, `OpenAI` model, `greeting`, `turn_detection`, or `parameters` dict. | Run `verify:backend` + `pytest tests`; document new env in `server/.env.example` (never add `PORT`). |
| `web.conversation-ui` | `web/src/components/*`, `web/src/lib/conversation.ts` | Customize pre-call (including vendor dropdown), EventTimeline, transcript, or metrics panels. | Preserve RTC/RTM lifecycle ownership, transcript UID normalization, and `TimelineEvent` import from `EventTimeline.tsx`. |
| `verification.contracts` | `web/scripts/*.ts`, root `package.json` | Add checks for new browser/backend boundaries. | Keep checks runnable without live Agora credentials. |

## Invariants

- Browser code calls only `/api/get_config`, `/api/startAgent`, `/api/stopAgent`, and `/api/vendors` for the default flow.
- Next.js owns `/api/*` through rewrites only; no `web/app/api/**/route.ts` for agent/token logic.
- FastAPI owns token generation, `AGORA_APP_CERTIFICATE`, BYO vendor credentials, and agent lifecycle.
- TTS vendor is always built via `build_vendor(name)` from `vendors.py`; the framework code (`build_vendor`/`required_env`/`available`) is shared across sibling vendor recipes — keep it identical.
- BYO vendor credentials are validated in `start()`, not `__init__`; `/get_config` stays key-less.
- STT and LLM legs remain on their proven keyless configs (`DeepgramSTT nova-3`, `OpenAI gpt-4o-mini`).
- The backend issues one RTC+RTM-capable token for a concrete non-zero UID.

## Stable Contracts

| Contract | Stable shape |
| -------- | ------------ |
| Required backend env | `AGORA_APP_ID`, `AGORA_APP_CERTIFICATE` |
| Optional backend env | `TTS_VENDOR` (default `minimax`), `TTS_VOICE`, `TTS_MODEL`, `AGENT_GREETING`, `PORT` (env only) |
| Required web deploy env | `AGENT_BACKEND_URL` |
| `GET /api/get_config` | Query `channel?`, `uid?`; returns `data.app_id`, `data.token`, `data.uid`, `data.channel_name`, `data.agent_uid`. |
| `GET /api/vendors` | Returns `data.default` (active `TTS_VENDOR`), `data.vendors[]` (`name`, `needs_key`, `required_env`). |
| `POST /api/startAgent` | Body `{ channelName, rtcUid, userUid, vendor? }`; returns `data.agent_id`, `data.channel_name`, `data.vendor`, `data.status`. |
| `POST /api/stopAgent` | Body `{ agentId }`; returns `{ code: 0, msg: "success" }`. |
| Success envelope | `{ "code": 0, "msg": "success", "data": ... }` where the route has data. |
| Verification entry points | `bun run verify:web`, `bun run verify:backend`, `bun run verify:web:proxy`, `bun run verify:local:fastapi`, `bun run verify:local`. |

## Internal / Subject to Change

- Visual layout, component composition, Tailwind classes, and assets under `web/src/components/`.
- Exact STT/LLM model names, TTS defaults, voice IDs, and greeting text, as long as they stay documented extension points.
- In-memory `Agent._sessions` details; the stable behavior is start by channel/user and stop by returned `agent_id`.
- Verification internals under `web/scripts/`; the stable surface is the root script names and what they assert.
- `agora-agents` SDK minor-version behavior; this recipe lower-bounds `>=2.3.0` but does not freeze every field.

## Related Progressive Disclosure Docs

- `L1/01_setup.md` — setup, env, vendor creds, and commands.
- `L1/02_architecture.md` — request flow, vendor registry, and topology.
- `L1/05_workflows.md` — common modification workflows.
- `L1/06_interfaces.md` — route, rewrite, env, and vendor registry contracts.
- `L1/L2/tts_vendor_matrix.md` — full vendor matrix with all SDK constructors, fields, and credential details.
- `L1/L2/session_lifecycle.md` — RTC/RTM/session orchestration and EventTimeline wiring.
