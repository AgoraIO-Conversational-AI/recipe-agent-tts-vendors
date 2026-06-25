# 08 · Security

> Trust boundaries, secret handling, and auth for the TTS vendors recipe.

## Trust boundaries

| Hop                            | Auth                                                                    |
| ------------------------------ | ----------------------------------------------------------------------- |
| Browser → agent backend        | None in local dev (the `/api/*` rewrite is same-origin).                |
| Agent backend → Agora cloud    | Token007, generated from `AGORA_APP_ID` + `AGORA_APP_CERTIFICATE`.      |
| Agora cloud → managed TTS      | Agora-managed key (transparent); applies to `minimax` and `openai`.     |
| Agora cloud → BYO TTS vendor   | BYO API key passed in the vendor config when the agent session starts.  |

## Secret handling

- **Server-only secrets:** `AGORA_APP_CERTIFICATE` and all BYO vendor API keys live only in `server/.env.local` and never reach the browser. The browser receives a short-lived token, not the certificate or any vendor key.
- `server/.env.local` is gitignored; `server/.env.example` ships placeholder comments only.
- Tokens (`generate_convo_ai_token`) expire after 3600s and are minted per `get_config` call for a concrete non-zero UID.
- The `/vendors` endpoint exposes `needs_key` and `required_env` (env var names) but never exposes credential values.

## CORS

The backend sets `CORSMiddleware` with `allow_origins=["*"]` — open by design for a local/dev recipe. **Lock this down to known origins before any production deployment.**

## Validation

- `Agent.start()` rejects empty `channel_name` and non-positive `agent_uid`/`user_uid` before issuing tokens or starting a session.
- `build_vendor(name)` raises `ValueError` listing all missing credential env vars before any SDK call is made — no partial construction with missing secrets.
- Route errors are sanitized: `_log_route_error` logs only non-`None` context; SDK exceptions map to 400/500 without leaking internals to the client beyond the message.

## Deployment notes

- Set `AGENT_BACKEND_URL` only to a backend you control; the rewrite forwards browser requests there verbatim.
- The published Docker image is **backend-only** (`:8000`); it does not bundle secrets. Inject all env vars at container start.
- On the default `minimax` vendor, no BYO API key is needed and no key is stored or passed. For BYO vendors, supply credentials via env, not baked into the image.

## Related Deep Dives

- None.
