## LSRC Mini App – Roadmap & Debug Checklist

Use this file to track all requested changes and debugging steps. We’ll keep it short, prioritized, and check items off as we complete them.

### Priority 0 — Stability and Data Integrity
- [ ] Ensure every recording creates/links a fragment: `listen_audio_id` and `sound_audio_id` never null when audio saved
- [ ] Handle permission denials gracefully (clear UI text, retry button, no sandbox fallback unless truly needed)
- [ ] Validate audio blob sizes (> 2 KB) before saving, surface warning if too short
- [ ] Robust error banner for Supabase failures (Storage, DB insert/update, RLS)

### Priority 1 — Telegram Mini App correctness
- [ ] Confirm BotFather Mini App URL points to current Vercel URL
- [ ] Detect Telegram web_app context and adapt UI (hide “Enable microphone” if not applicable)
- [ ] Fallback upload always available (file input) with progress indicator

### Priority 2 — UX polish
- [ ] Unify copy/buttons across phases (Listen → Sound → Reflect → Create)
- [ ] Show inline toasts for: recording start/stop/save/link
- [ ] Session summary: display linked audio filenames and durations
- [ ] Disable/enable navigation buttons appropriately during saves

### Priority 3 — Supabase schema and security
- [ ] Re-enable RLS with safe anon policies for: `capsules`, `fragments`, `audio_files`, `reflections`
- [ ] Storage bucket policies: allow public read, constrained writes
- [ ] Add simple rate limiting (client-side) to avoid rapid-fire inserts

### Priority 4 — Product features
- [ ] Exchange capsules between users
- [ ] Collection of inspiring score texts (seed + rotation)
- [ ] Session progress tracking (per user)
- [ ] Optional reflection transcription pipeline (flag-controlled)

### Priority 5 — Observability
- [ ] Add lightweight client logs toggle (DEBUG_MODE) with user-safe redaction
- [ ] Record key client events in a `client_events` table (optional)

### Deployment / Ops
- [ ] Vercel environment variables set: `SUPABASE_URL`, `SUPABASE_ANON_KEY`
- [ ] Add “build timestamp” to console on each deploy
- [ ] Manual Redeploy instruction: “Use existing Build Cache = No”

### Notes
- Keep this file as the single source of truth for requested changes.
- We’ll check items off here and in our internal TODO list as we progress.


