# 07 · Gotchas

> Non-obvious pitfalls specific to the TTS vendors recipe. Read before changing the vendor registry, agent config, env, or verify scripts.

## BYO vendor credentials are validated at agent start, not boot

The server boots without BYO credentials (so `doctor`/contract checks work). `POST /startAgent` returns **400** if the selected vendor's credentials are missing. `Agent.__init__` raises only for missing `AGORA_APP_ID`/`AGORA_APP_CERTIFICATE`. Don't move vendor credential checks into `__init__`.

## Never hardcode a TTS vendor in agent.py

`agent.py` must always call `build_vendor(selected)` to build the TTS leg — never instantiate a vendor SDK class directly. The registry pattern is shared across sibling recipes; keep it consistent.

## The in-UI vendor switcher passes vendor per-request

`POST /startAgent` accepts an optional `vendor` field that overrides `TTS_VENDOR` for that session. `Agent.start()` honors it as `selected = (vendor or self.vendor).strip()`. The env default is only the initial dropdown selection; the UI dropdown sends the final choice.

## Do not put `PORT` in `server/.env.example`

`verify:local:fastapi` injects a random `PORT` and loads env with `load_dotenv(override=True)`. A `PORT` line in `.env.example` (copied to `.env.local`) would clobber the injected port and break the smoke test.

## Keep `/api/*` ownership in rewrites

Adding `web/app/api/**/route.ts` for agent/token logic breaks the boundary — `verify-api-contracts.ts` explicitly fails if a `route.ts` exists under `app/api`. Token logic and vendor credentials belong in `server/`.

## camelCase request fields

`StartAgentRequest` uses `channelName`, `rtcUid`, `userUid` (camelCase) to match the browser client. Renaming one side without the other breaks the contract tests.

## Import TimelineEvent from EventTimeline.tsx

The `TimelineEvent` type is exported from `web/src/components/EventTimeline.tsx`. Do not create a separate types file or re-export it elsewhere — all consumers import from the component.

## UID normalization in transcripts

`normalizeTranscript` maps `uid === '0'` to the local UID. Token issuance also rejects zero/negative UIDs and generates a concrete one. Preserve both — speaker mapping and tokens depend on concrete UIDs.

## Local calls under a global proxy

Global proxies (Clash, etc.) can break `localhost`/RFC-1918 traffic. Configure the proxy to send `127.0.0.1`, `localhost`, and private ranges DIRECT, or use `socksio` (in `requirements.txt`) + `all_proxy` to route the backend through SOCKS.

## Related Deep Dives

- [tts_vendor_matrix](L2/tts_vendor_matrix.md) — correct SDK constructor fields per vendor.
