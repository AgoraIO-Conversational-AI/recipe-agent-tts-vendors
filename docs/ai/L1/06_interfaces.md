# 06 · Interfaces

> Boundary contracts: backend routes, the `/api/*` rewrite map, env vars, the response envelope, and the vendor registry API.

## Backend routes (port 8000)

The browser calls these as `/api/<name>`; Next rewrites to the backend `/<name>`.

### `GET /get_config`

- Query (optional): `channel?: string`, `uid?: int` (≤ 0 or missing → backend generates one).
- Returns `data`: `{ app_id, token, uid (string), channel_name, agent_uid (string) }`.
- Token is a Token007 RTC+RTM token, expiry 3600s, for a concrete non-zero UID.
- Always succeeds key-less (no vendor creds checked here).

### `GET /vendors`

- No query params.
- Returns `data`: `{ default: string, vendors: [ { name, needs_key, required_env[] } ] }`.
- `default` is the current `TTS_VENDOR` env value (default `minimax`).
- Used to populate the pre-call vendor dropdown in the web UI.

### `POST /startAgent`

- Body: `{ channelName: string, rtcUid: int, userUid: int, vendor?: string }`.
  - `vendor` overrides `TTS_VENDOR` for this session (the in-UI dropdown uses this).
- Returns `data`: `{ agent_id, channel_name, vendor, status: "started" }`.
- 400 if `channelName`/`rtcUid`/`userUid` invalid, or the selected vendor has missing credentials.

### `POST /stopAgent`

- Body: `{ agentId: string }`.
- Returns `{ code: 0, msg: "success" }` (no `data`).

## Response envelope

```json
{ "code": 0, "msg": "success", "data": { } }
```

`data` omitted when the route has no payload. Non-zero `code` or missing `data` = error on the client side.

## Rewrite map (`web/next.config.ts`)

| Browser path        | Backend destination |
| ------------------- | ------------------- |
| `/api/get_config`   | `/get_config`       |
| `/api/vendors`      | `/vendors`          |
| `/api/startAgent`   | `/startAgent`       |
| `/api/stopAgent`    | `/stopAgent`        |

`rewrites()` returns `[]` when `AGENT_BACKEND_URL` is unset. The contract is asserted by `verify-api-contracts.ts` and exercised by `verify-local-proxy.ts`.

## Browser API client (`web/src/services/api.ts`)

- `getConfig({ channel?, uid? }) → GetConfigResponse`
- `getVendors() → { default: string, vendors: VendorOption[] }`
- `startAgent(channelName, rtcUid, userUid, vendor?) → agent_id`
- `stopAgent(agentId) → void`

## Environment variables

| Variable                | Scope              | Required | Default         |
| ----------------------- | ------------------ | :------: | --------------- |
| `AGORA_APP_ID`          | backend            |    ✅    | —               |
| `AGORA_APP_CERTIFICATE` | backend            |    ✅    | —               |
| `TTS_VENDOR`            | backend            |          | `minimax`       |
| `TTS_VOICE`             | backend            |          | per-vendor      |
| `TTS_MODEL`             | backend            |          | per-vendor      |
| `AGENT_GREETING`        | backend            |          | built-in line   |
| _vendor creds_          | backend            |    \*    | —               |
| `AGENT_BACKEND_URL`     | web (deploy)       |    ✅\** | —               |
| `PORT`                  | backend (env only) |          | `8000` — do **not** put in `.env.example` |

\* Required only for the selected BYO vendor; validated at `start()` time.
\** Required wherever the web app is deployed; rewrites are empty without it.

## Vendor registry API (`server/src/vendors.py`)

| Function | Signature | Returns |
| -------- | --------- | ------- |
| `available()` | `() → List[str]` | Sorted list of all registry keys. |
| `needs_key(name)` | `(str) → bool` | `True` if the vendor requires BYO credentials. |
| `required_env(name)` | `(str) → List[str]` | Env var names required for the vendor. |
| `build_vendor(name, env?)` | `(str, dict?) → SDK vendor` | Builds and returns the vendor; raises `ValueError` if creds are missing. |

## Event surface (RTM)

Set at agent start via `parameters`:

| Parameter | Value | Purpose |
| --------- | ----- | ------- |
| `data_channel` | `"rtm"` | Route all events over RTM to the browser. |
| `enable_metrics` | `True` | Emit per-stage latency (STT, LLM, TTS). |
| `enable_error_message` | `True` | Surface agent + message errors over RTM. |
| `audio_scenario` | `"chorus"` | Ultra-low-latency profile for web clients. |
| `advanced_features.enable_rtm` | `True` | Enable RTM event delivery. |

RTM event types surfaced as `TimelineEvent.kind`:

| SDK event | Kind | Carries |
| --------- | ---- | ------- |
| `AGENT_STATE_CHANGED` | `state` | `listening`, `thinking`, `speaking`, `idle` |
| `AGENT_METRICS` | `metric` | Stage type, metric name, value (ms) |
| `AGENT_ERROR` | `error` | Error type + message |
| `MESSAGE_ERROR` | `error` | RTM error code + message |
| `TRANSCRIPT_UPDATED` | `turn` | Role (agent/user) + text |

## Related Deep Dives

- [tts_vendor_matrix](L2/tts_vendor_matrix.md) — every vendor's SDK constructor fields and credential details.
- [session_lifecycle](L2/session_lifecycle.md) — browser orchestration and EventTimeline wiring.
