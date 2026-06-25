# 05 · Workflows

> Step-by-step guides for the common changes in this recipe. Each ends with the narrowest verify command to run.

## Add or swap a TTS vendor

1. Add a `build_<vendor>(env)` function in `server/src/vendors.py` following the existing pattern (one SDK call, docstring with source URL).
2. Add an entry in `REGISTRY`: `"name": (build_<vendor>, ["REQUIRED_ENV_VAR", ...])`. Empty list for a keyless/managed vendor.
3. Update the root `README.md` Vendors table.
4. Verify: `bun run verify:backend` (compile) + `cd server && pytest tests -v`.

## Change the default TTS vendor

1. Set `TTS_VENDOR` in `server/.env.local` (or update the `os.getenv` default in `agent.py`).
2. Add the vendor's credentials if it is a BYO vendor.
3. Verify: `bun run doctor:local` to confirm creds are present, then `bun run verify:local`.

## Change the pipeline (STT model, LLM model, greeting)

1. STT: edit `DeepgramSTT(model=..., language=...)` in `Agent.start()` (`server/src/agent.py`).
2. LLM: edit `OpenAI(model=...)` in `Agent.start()`.
3. Greeting: set `AGENT_GREETING` (env) or edit the default string in `agent.py`.
4. Verify: `bun run verify:backend` + `cd server && pytest tests -v`.

## Add or change a browser-facing route

1. Add the FastAPI handler in `server/src/server.py` (return the `{ code, msg, data }` envelope).
2. Add the `/api/<name>` → `/<name>` mapping in `web/next.config.ts` `rewrites()`.
3. Add a client helper in `web/src/services/api.ts`.
4. Extend `web/scripts/verify-api-contracts.ts` with the new path + envelope assertions.
5. Verify: `bun run verify:web` (and `bun run verify:local:fastapi` if it should go through the real backend).

## Adjust session parameters (codec, scenario, flags)

1. Edit the `parameters` dict in `Agent.start()` (`audio_scenario`, `data_channel`, `enable_metrics`, `enable_error_message`). `output_audio_codec` is accepted per-request via `parameters` on `POST /startAgent`.
2. Verify: `bun run verify:local:fastapi`.

## Run / debug locally

```bash
bun run dev              # both processes
bun run doctor:local     # check creds + .env.local before a live call
```

## Verify before finishing

| Change touches…              | Run                                                                   |
| ---------------------------- | --------------------------------------------------------------------- |
| Web only                     | `bun run verify:web`                                                  |
| Backend logic / vendor config| `bun run verify:backend` + `cd server && pytest tests -v`             |
| Route/proxy boundary         | `bun run verify:web:proxy` and/or `bun run verify:local:fastapi`      |
| Anything end-to-end (local)  | `bun run verify:local`                                                |

## Deploy

1. Deploy `web/` as a Next.js app.
2. Deploy `server/` (or any reachable FastAPI host); the published backend-only image is `ghcr.io/AgoraIO-Conversational-AI/recipe-agent-tts-vendors` on `v*` tags.
3. Set `AGENT_BACKEND_URL` in the web deployment so rewrites reach the backend.
4. Set `TTS_VENDOR` + BYO credentials in the backend deployment env if not using the default `minimax`.

## Related Deep Dives

- [tts_vendor_matrix](L2/tts_vendor_matrix.md) — full vendor matrix; reference when adding or auditing a vendor.
- [session_lifecycle](L2/session_lifecycle.md) — client-side join/stop, EventTimeline wiring.
