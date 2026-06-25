# 03 · Code Map

> Where things live. Two top-level modules: `web/` (Next.js client) and `server/` (FastAPI backend). Orchestration is in the root `package.json`.

## Root

| Path                  | Responsibility                                                        |
| --------------------- | --------------------------------------------------------------------- |
| `package.json`        | Bun workspace; `setup`, `dev`, `doctor*`, `verify*`, `clean` scripts. |
| `README.md`           | Setup, run modes, vendor table, env, troubleshooting.                 |
| `ARCHITECTURE.md`     | System shape, request flow, vendor registry, event surface.           |
| `AGENTS.md`           | Coding-agent handbook + How to Load / Git Conventions / Doc Commands. |
| `Dockerfile`          | Backend-only image (`:8000`).                                         |
| `.github/workflows/`  | `ci.yml` (backend pytest matrix + web verify), `docker.yml`, `nightly.yml`. |

## `server/` — FastAPI backend (:8000)

| Path                              | Responsibility                                                           |
| --------------------------------- | ------------------------------------------------------------------------ |
| `src/server.py`                   | FastAPI app, CORS, route handlers (`get_config`, `vendors`, `startAgent`, `stopAgent`), error mapping, uvicorn entrypoint. |
| `src/agent.py`                    | `Agent` class: `AsyncAgora` client, vendor selection, `start()`/`stop()`, `_sessions`. |
| `src/vendors.py`                  | TTS vendor registry: `REGISTRY`, `build_vendor()`, `available()`, `required_env()`, `needs_key()`. |
| `scripts/run_fake_server.py`      | Boots `server.app` with a `FakeAgent` for the local FastAPI smoke test. |
| `tests/test_vendors.py`           | Constructs every vendor with dummy creds; asserts `to_config()` shape and BYO-missing error. |
| `tests/test_agent_config.py`      | Constructs `Agent`; asserts default `vendor == "minimax"`. |
| `tests/test_agent_construction.py`| Builds the real `AgoraAgent`, fakes the SDK session, asserts `start()` return shape. |
| `tests/conftest.py`               | `fake_env` fixture (AGORA_APP_ID, AGORA_APP_CERTIFICATE, TTS_VENDOR=minimax); no cloud, no real creds. |
| `.env.example`                    | Env template with all 13 vendor blocks commented out (do not add `PORT`). |
| `requirements*.txt`               | Runtime + dev (pytest) deps.                                            |

## `server/src/server.py` routes

- `GET /get_config` — token + channel/UID config.
- `GET /vendors` — list all registry entries + `needs_key` + `required_env`.
- `POST /startAgent` — start the agent with the selected TTS vendor.
- `POST /stopAgent` — stop by `agent_id`.

## `web/` — Next.js client (:3000)

| Path                                       | Responsibility                                                        |
| ------------------------------------------ | --------------------------------------------------------------------- |
| `next.config.ts`                           | `/api/*` rewrites to `AGENT_BACKEND_URL`; strict mode; Turbopack root. |
| `src/services/api.ts`                      | Browser API client: `getConfig`, `getVendors`, `startAgent`, `stopAgent`. |
| `src/lib/conversation.ts`                  | Transcript normalization, timestamp/UID mapping, visualizer state.    |
| `src/lib/agora.ts`                         | `DEFAULT_AGENT_UID` constant.                                         |
| `src/components/LandingPage.tsx`           | Conversation entry: config + vendor fetch, agent start, RTM login, teardown. |
| `src/components/ConversationComponent.tsx` | RTC join, mic publish, transcript/metrics/state/event listeners.      |
| `src/components/EventTimeline.tsx`         | `EventTimeline` component + **`TimelineEvent` type export**.          |
| `src/components/QuickstartPreCallCard.tsx` | Pre-call card with TTS vendor dropdown.                               |
| `src/components/Quickstart*.tsx`           | Transcript, pipeline metrics, layout panels.                          |
| `scripts/verify-api-contracts.ts`          | Asserts rewrites + client paths + response envelope (no network).     |
| `scripts/verify-local-proxy.ts`            | Stub backend; proxies `/api/*` through the rewrite map.               |
| `scripts/verify-local-fastapi.ts`          | Spawns real FastAPI with `FakeAgent`; proxies routes end-to-end.      |
| `scripts/doctor.ts`                        | Web prerequisite check.                                               |

## Related Deep Dives

- None. For runtime flow see [02_architecture](02_architecture.md); for contracts see [06_interfaces](06_interfaces.md).
