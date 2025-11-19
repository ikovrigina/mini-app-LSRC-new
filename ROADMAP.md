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
- [x] Hide the "score" heading text on the main screen (do not display it)
- [x] Remove diagnostics panel (PASS/PASS/PASS) from UI; end-users shouldn't see it
- [x] Remove helper text under microphone button ("optional — enables live recording if allowed")
- [ ] Keep the initial score fixed across all phases (do not change on returning to Listen); also hide the word "score" in Listen phase
- [x] Remove the "Listen source" choice screen entirely; go straight to Listening
- [x] On entering Listening, immediately request mic (once per session) and auto-start recording
- [x] In Listening show only a single prominent "Stop" button (record auto-starts)
- [ ] Persist mic permission state to avoid repeated prompts within the session
- [x] After pressing Stop in Listening, go to Sound screen; pressing "Sound" auto-starts recording (no extra prompts), show only a single "Stop" button
- [x] Remove "Sound back" title and "your response to what you heard" text from Sound phase - just start recording immediately
- [ ] After pressing Stop in Sound, show two choices: "Listen" (start a new listening cycle) and "Reflect"
- [ ] If user chooses "Listen" after Sound, show two buttons: "Listen to environment" and "Listen to past listening (previous cycle)"
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
 - [ ] Reflect: user can submit reflection as text OR as audio
   - [ ] If text: save to `reflections.text`, link to current fragment
   - [ ] If audio: save audio to Storage + `audio_files`, link via `reflections.audio_id`
   - [ ] Transcribe reflection audio to text and store in `reflections.transcription_text`
   - [ ] Extract keywords from final text (typed or transcribed) into `reflections.keywords`
   - [ ] Ensure RLS allows anon insert for reflections in current testing mode
 - [ ] Create phase after Reflect:
   - [ ] Input for user score; save to `scores` with `source = user_created` and link to capsule
   - [ ] Replace quiet confirmation with: "Your score has been added to the listening archive. It is now part of the collective pool."
  - [ ] After confirmation show two actions: "New capsule" (start fresh) and "Listen to a capsule from archive" (pick and play a past capsule)

### Archive
- [ ] Add Archive screen (Capsule Archive)
  - [ ] List capsules (most recent first) with the title of the created score
  - [ ] Tap to open capsule details and play its listen/sound audios
  - [ ] Back navigation to return to Create/intro

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


