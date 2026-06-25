# Deep Dive — Session Lifecycle

> **When to Read This:** You are touching client-side join, RTC/RTM wiring, EventTimeline, transcript handling, vendor dropdown initialization, or mid-call control. For the contracts these calls hit, see [06_interfaces](../06_interfaces.md).

The browser owns the full RTC/RTM client lifecycle; the backend owns tokens and the agent session. The two meet only at `/api/*`.

## End-to-end flow

1. **Config** — `LandingPage.tsx` calls `getConfig()` (`web/src/services/api.ts`) → `GET /api/get_config`. Backend mints a Token007 (RTC+RTM, 3600s) for a concrete non-zero UID and returns `{ app_id, token, uid, channel_name, agent_uid }`.
2. **Vendor list** — `LandingPage.tsx` calls `getVendors()` → `GET /api/vendors`. Returns `{ default, vendors[] }`. The pre-call card (`QuickstartPreCallCard.tsx`) renders the vendor dropdown from this list.
3. **Join** — `ConversationComponent.tsx` joins the RTC channel with the returned token/UID, publishes the microphone, and logs in to RTM.
4. **Start agent** — `startAgent(channelName, rtcUid, userUid, vendor?)` → `POST /api/startAgent`. Backend calls `build_vendor(selected)` (credentials validated here), starts the async session, and returns `agent_id`.
5. **Converse** — user audio flows through Deepgram STT → OpenAI LLM → selected TTS. Agent voice returns into the channel. RTM delivers events.
6. **EventTimeline** — `ConversationComponent.tsx` uses `AgoraVoiceAI` from `agora-agent-client-toolkit` to subscribe to RTM events. Each event is mapped to a `TimelineEvent` (kind: `state|metric|error|turn`) and appended to a buffer capped at 50. `EventTimeline.tsx` renders them reverse-chronologically.
7. **Stop** — `stopAgent(agentId)` → `POST /api/stopAgent`. The client also releases RTC/RTM media on end-call.

## Backend session bookkeeping

`Agent` (`server/src/agent.py`) keeps an in-memory map `self._sessions[agent_id] = session`.

- `stop(agent_id)` pops the session and calls `session.stop()`.
- If the session is missing (e.g. process restarted), it falls back to `self.client.stop_agent(agent_id)` — the stateless cloud path. This is why stop is robust across restarts but `_sessions` itself is **not** a durable store.

## Vendor selection in the UI

`LandingPage.tsx` manages `selectedVendor` state (initialized from `getVendors().default`). The pre-call dropdown sets it. When the user starts a conversation, `startAgent(..., selectedVendor)` passes the chosen vendor to the backend. The vendor can be changed per-session without restarting the server.

## EventTimeline and `TimelineEvent`

`TimelineEvent` type (from `EventTimeline.tsx`):

```typescript
type TimelineEvent = {
  id: string;
  ts: number;
  kind: "state" | "metric" | "error" | "turn";
  label: string;
  detail?: string;
};
```

- Import `TimelineEvent` from `EventTimeline.tsx` only — never create a separate types file.
- The buffer is capped at 50 events; `EventTimeline` renders them in reverse-chronological order.
- Kind styling: `state` = blue, `metric` = emerald, `error` = red, `turn` = violet.

## Transcript handling (`web/src/lib/conversation.ts`)

- `normalizeTranscript(transcript, localUid)` — maps `uid === '0'` to the local UID and runs `normalizeTranscriptSpacing` on text.
- `normalizeTimestampMs(ts)` — promotes second-precision timestamps to ms.
- `getMessageList` / `getCurrentInProgressMessage` — split finalized vs in-progress turns (by `TurnStatus.IN_PROGRESS`).
- `mapAgentVisualizerState(agentState, isConnected, connectionState)` — maps SDK state + RTC connection state → UIKit visualizer state (`joining`, `listening`, `analyzing`, `talking`, `ambient`, `disconnected`).

## What stays where

- **Client owns:** RTC join, mic publish, RTM login, transcript/metrics/state/event listeners, EventTimeline buffer, token renewal, explicit end-call media release.
- **Backend owns:** token minting, vendor selection + build, session start/stop.
- Do not move token logic into the web app or add Route Handlers for it (see [07_gotchas](../07_gotchas.md)).

## Related L1

- [02_architecture](../02_architecture.md) · [03_code_map](../03_code_map.md) · [06_interfaces](../06_interfaces.md)
