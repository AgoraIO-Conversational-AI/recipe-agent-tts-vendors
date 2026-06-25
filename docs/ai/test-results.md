# Progressive Disclosure — Test Results

> Test run for `recipe-agent-tts-vendors` progressive disclosure docs.
> Date: 2026-06-25 · Standard: AgoraIO-Community/ai-devkit progressive-disclosure.

## Step 1 — Structural checks

| Check                                               | Result |
| --------------------------------------------------- | ------ |
| `L0_repo_card.md` ≤ 50 lines                        | Pass (36) |
| All 8 L1 files present                              | Pass |
| Each L1 has purpose blockquote + Related Deep Dives | Pass (8/8) |
| L1 line counts                                      | 39–112 — mostly within target; see note |
| L2 `_index.md` present                              | Pass |
| Each L2 deep dive opens with "When to Read This"    | Pass (2/2) |
| Relative links resolve (`docs/ai/` + AGENTS.md)     | Pass (39/39, 0 broken) |
| AGENTS.md has How to Load / Git Conventions / Doc Commands | Pass |

**Note on L1 line counts:** `07_gotchas.md` (43) and `08_security.md` (39) are below the 80–200 soft target but are complete and table-dense for their subject matter. Accepted; padding would not improve agent usability.

## Step 2/3 — Question runs

Questions span the five standard categories. Each answer was checked against the repo source before being marked Pass. "Level" is the lowest disclosure level that fully answers the question.

### Setup & Build

| # | Question | Expected answer | Source of truth | Level | Status |
|---|----------|-----------------|-----------------|-------|--------|
| 1 | How do I install and run it locally? | `bun run setup` then `bun run dev` (backend :8000 + web :3000). | `L1/01_setup.md` ↔ `package.json` scripts | L1 | Pass |
| 2 | Which env vars are always required? | `AGORA_APP_ID` and `AGORA_APP_CERTIFICATE`. | `L1/01_setup.md`, `06_interfaces.md` ↔ `agent.py`, `.env.example` | L1 | Pass |
| 3 | Is this zero-key? | Yes — defaults to managed `minimax` TTS (keyless); BYO keys are optional and vendor-specific. | `L1/01_setup.md`, `07_gotchas.md` ↔ `README.md`, `agent.py`, `vendors.py` | L1 | Pass |

### Test & Run

| # | Question | Expected answer | Source of truth | Level | Status |
|---|----------|-----------------|-----------------|-------|--------|
| 4 | How do I run backend tests without cloud creds? | `cd server && pytest tests -v`; `conftest.py` sets fake env with `TTS_VENDOR=minimax`; no cloud needed. | `L1/04_conventions.md`, `01_setup.md` ↔ `tests/conftest.py` | L1 | Pass (ran: 4 passed) |
| 5 | What's the narrowest gate for a web-only change? | `bun run verify:web`. | `L1/05_workflows.md` ↔ `package.json` | L1 | Pass |
| 6 | What does `verify:local:fastapi` do? | Spawns real FastAPI with `FakeAgent` and proxies routes through the rewrite map; no live Agora calls. | `L1/03_code_map.md`, `05_workflows.md` ↔ `web/scripts/verify-local-fastapi.ts` | L1 | Pass |

### Conventions

| # | Question | Expected answer | Source of truth | Level | Status |
|---|----------|-----------------|-----------------|-------|--------|
| 7 | What response shape do backend routes use? | `{ code, msg, data }`; `data` only when there's a payload. | `L1/04_conventions.md`, `06_interfaces.md` ↔ `server.py` | L1 | Pass |
| 8 | How are errors mapped to HTTP codes? | `ValueError→400`, `RuntimeError→500`, else 500 via `_to_http_error`. | `L1/04_conventions.md` ↔ `server.py` | L1 | Pass |
| 9 | What are the commit/branch conventions? | Conventional commits `type: description`; branches `type/short-description`; no AI tool names, no Co-Authored-By. | `AGENTS.md` Git Conventions | L1 | Pass |

### Development

| # | Question | Expected answer | Source of truth | Level | Status |
|---|----------|-----------------|-----------------|-------|--------|
| 10 | How do I add a new TTS vendor? | Add `build_<vendor>` + `REGISTRY` entry in `vendors.py`; update README Vendors table; run `verify:backend` + `pytest tests`. | `L1/05_workflows.md` ↔ `vendors.py`, `test_vendors.py` | L1 | Pass |
| 11 | Where is the `/api/*` boundary defined and what must I not add? | Rewrites in `web/next.config.ts`; never add `app/api/**/route.ts` for agent/token logic. | `L1/04_conventions.md`, `07_gotchas.md` ↔ `next.config.ts`, `verify-api-contracts.ts` | L1 | Pass |
| 12 | Where does token generation live and why must vendor creds stay there too? | `server/` (`generate_convo_ai_token` in `server.py`); App Certificate and BYO keys stay server-side. | `L1/02_architecture.md`, `08_security.md` ↔ `server.py`, `agent.py` | L1 | Pass |

### Deep Dive

| # | Question | Expected answer | Source of truth | Level | Status |
|---|----------|-----------------|-----------------|-------|--------|
| 13 | What SDK class and constructor fields does the Cartesia vendor use? | `V.CartesiaTTS(api_key=..., voice_id=..., model_id="sonic-2")`; creds: `CARTESIA_API_KEY`; voice override: `TTS_VOICE`. | `L2/tts_vendor_matrix.md` ↔ `vendors.py` `build_cartesia` | L2 | Pass |
| 14 | How does the in-UI vendor dropdown work end-to-end? | `LandingPage` calls `getVendors()` → `GET /api/vendors`; dropdown sets `selectedVendor`; `startAgent(..., selectedVendor)` sends it as `vendor` field in `POST /api/startAgent`; backend honors it over `TTS_VENDOR`. | `L2/session_lifecycle.md` ↔ `LandingPage.tsx`, `server.py`, `agent.py` | L2 | Pass |
| 15 | How does stop survive a backend restart? | `_sessions` is in-memory; missing session falls back to `self.client.stop_agent(agent_id)` (stateless cloud path). | `L2/session_lifecycle.md` ↔ `agent.py` | L2 | Pass |

## Step 4 — Analysis

- All 15 questions answered at the expected disclosure level (12 at L1, 3 at L2).
- No missing-coverage findings; no broken references.
- One soft deviation: `07_gotchas.md` (43 lines) and `08_security.md` (39 lines) below the 80–200 target (accepted; table-dense, topic-complete).

## Step 5 — Summary

| Category       | Questions | Pass | Notes |
| -------------- | :-------: | :--: | ----- |
| Setup & Build  | 3 | 3 | — |
| Test & Run     | 3 | 3 | backend tests executed: 4 passed |
| Conventions    | 3 | 3 | — |
| Development    | 3 | 3 | — |
| Deep Dive      | 3 | 3 | resolved at L2 as designed |
| **Total**      | **15** | **15** | — |

## Step 6 — Fixes / Retest

No failing questions; no fixes required. Evidence collected during this run:

- `pytest tests -v` in throwaway venv `/tmp/v_tts` → `4 passed in 0.58s` (venv removed after run).
- Relative link check → `39 checked, 0 broken`.
