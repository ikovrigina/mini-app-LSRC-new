# LSRC V2 Roadmap (Telegram-first)

## Purpose

This document defines a low-risk migration path to LSRC v2:
- Keep the working Telegram Mini App as the primary channel
- Introduce a cleaner v2 product flow (Quick Loop + Deep Session)
- Refactor backend logic so Telegram and future Web share the same API
- Avoid a full rewrite and avoid disrupting current users

---

## Product Decision (Now)

### Recommended channel strategy
- Keep `Telegram Mini App` as primary in v2
- Add `Web` as secondary channel after core v2 loop is stable
- Delay `iOS App Store` until retention and repeat usage are validated

### Why
- Telegram already works and has distribution
- Fastest path to test behavioral changes in core loop
- Lower engineering and deployment risk than a platform rewrite

---

## Target V2 Core Loop

### Default loop (Quick Loop, 45-90 sec)
1. Home (`Quick Loop`, `Deep Session`, `Archive`)
2. Prompt (single human score)
3. Listen (short timed attention, recording optional)
4. Sound response (one short audio)
5. Reflect (one line or one quick tag)
6. Save (private by default, share optional)

### Deep Session (optional)
- Adds multi-cycle listen/sound
- Adds longer reflection
- Adds optional score creation

---

## Architecture Plan

### Current pain
- Frontend contains too much domain logic
- Telegram-specific behavior is mixed into product flow
- Audio and capsule saving are tightly coupled to UI transitions

### V2 target
- Shared backend endpoints for session/capsule/audio/scores
- Frontend becomes a state-driven client (Telegram first, Web later)
- Telegram bot remains orchestration shell, not business-logic center

### Proposed layers
- `Mini App UI`: screens and local state machine
- `API layer`: session lifecycle, score selection, save logic
- `Data layer`: Supabase tables and storage
- `Bot layer`: launch, commands, fallback audio flows, notifications

---

## 2-Sprint Execution Plan

## Sprint 1 (stabilize + v2 core in Telegram)

### Goal
Ship v2 Quick Loop in Telegram without breaking current functionality.

### Scope
- New v2 UI flow in Mini App
- Preserve existing tables (`scores`, `capsules`, `fragments`, `audio_files`, `reflections`)
- Introduce feature flag for rollout

### Tasks
- Frontend (`index.html` / `miniapp.html`)
  - Add Home screen with 3 entry points: Quick/Deep/Archive
  - Remove auto-start recording from first transition
  - Make recording optional in Listen step
  - Simplify Reflect to quick input by default
  - Make score creation optional before save
  - Add post-save "result card" (human-readable feedback)

- State management
  - Introduce explicit client state machine:
    - `home -> prompt -> listen -> sound -> reflect -> save -> result`
  - Separate Quick and Deep paths cleanly

- Data write path
  - Ensure one stable capsule lifecycle:
    - create capsule on start
    - create/update fragment per cycle
    - save reflection once per cycle or at end
  - Ensure save works if user skips optional score creation

- Bot integration (`telegram-bot.py`)
  - Keep launch and deep-link behavior unchanged
  - Add optional command to open Quick Loop directly
  - Keep fallback messaging for audio errors only

- Guardrails
  - Add `V2_ENABLED` flag in config/environment
  - Keep v1 flow available behind fallback route for rollback

### Acceptance criteria
- User can complete Quick Loop end-to-end in Telegram in < 90 sec
- No forced mic permission to enter session
- Capsule saves successfully with or without final score
- Rollback to v1 is possible via feature flag

---

## Sprint 2 (shared API + Web readiness)

### Goal
Decouple logic from Telegram and prepare zero-friction web companion.

### Scope
- Move core business logic into backend endpoints
- Keep Telegram UI using same API contract
- Add minimal web entry that reuses v2 flow

### Tasks
- Backend/API (`server.py` or lightweight API service)
  - Add endpoints:
    - `POST /sessions/start`
    - `POST /sessions/{id}/fragment`
    - `POST /sessions/{id}/reflection`
    - `POST /sessions/{id}/complete`
    - `GET /scores/random`
    - `GET /archive/me`
  - Move weighted score selection and capsule completion logic to server

- Frontend refactor
  - Replace direct DB writes from UI with API calls
  - Keep optimistic UI but centralize error handling
  - Normalize payload formats for Telegram/Web clients

- Bot updates
  - Keep bot as transport/auth wrapper
  - Add telemetry events for session start/complete

- Web companion (minimal)
  - Simple web entry with same v2 Quick Loop screens
  - Anonymous or lightweight auth mode
  - Same backend API, same save model

### Acceptance criteria
- Telegram and Web use identical core endpoints
- Session completion rate is measurable per channel
- No data model divergence between Telegram and Web

---

## Deployment Plan (Safe Rollout)

### Stage 1: Internal test
- Deploy v2 behind `V2_ENABLED=false` by default
- Enable for a test user list
- Verify DB writes and audio uploads on real devices

### Stage 2: Soft launch
- Enable v2 for 10-20% users or invited cohort
- Monitor failures and completion rates for 3-5 days

### Stage 3: Full launch
- Set `V2_ENABLED=true`
- Keep v1 fallback path for one additional release cycle

### Rollback
- Disable `V2_ENABLED`
- Route users back to v1 screens
- Keep collected v2 data (schema-compatible by design)

---

## Telegram Integration Notes

### Keep
- Existing bot launch and Mini App opening
- Existing transport metadata (`telegram_webapp`)

### Improve
- Deep link to specific mode:
  - `/start quick`
  - `/start deep`
- Friendly fallback if mic access fails:
  - allow upload
  - allow continue without recording in Quick mode

### Do not do now
- Full voice-message-based flow through chat as default
- Heavy bot-side orchestration for every user action

---

## Data and Metrics (Required for next platform decision)

Track weekly:
- Quick Loop completion rate
- Median time to complete
- D1 and D7 return rate
- Share-to-archive rate
- Save-private vs save-public ratio
- Audio upload failure rate

Decision thresholds before iOS:
- Stable completion
- Meaningful repeat usage
- Clear user demand outside Telegram

---

## Platform Decision Framework

### Keep Telegram as primary if
- Most active users are already in Telegram
- Quick Loop retention improves after v2
- Engineering bandwidth is limited

### Add Web second if
- You need open public access and easier sharing
- Non-Telegram users show demand
- You want SEO/portfolio traffic conversion

### Build iOS only if
- Repeat usage is proven
- Product narrative is stable
- Team can support app release/maintenance lifecycle

---

## Work Breakdown by File (initial)

- `index.html` / `miniapp.html`
  - v2 screen flow and UI copy updates
- `telegram-bot.py`
  - launch/deeplink routing and minimal telemetry
- `server.py`
  - shared session endpoints and completion logic
- `config.js` / env vars
  - feature flag and API base URL
- `SETUP_INSTRUCTIONS.md`
  - update deploy/runbook for v2 flag rollout

---

## Risks and Mitigations

- Risk: Breaking current users during rewrite
  - Mitigation: feature flag + v1 fallback

- Risk: Audio reliability in Telegram contexts
  - Mitigation: optional recording in Quick mode, upload fallback

- Risk: Scope creep (Telegram + Web + iOS at once)
  - Mitigation: Telegram-first staged plan, metric-gated expansion

---

## Recommended Next Action

Start Sprint 1 immediately:
- implement v2 Quick Loop screens
- keep current storage/data model
- ship behind feature flag
- test on real Telegram devices before wider rollout
