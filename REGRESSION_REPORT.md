# REGRESSION REPORT — Durga fork integration review

Date: 2026-05-03
Reviewer: senior-engineer regression pass (NOT security)
Scope: integration bugs across the eight parallel agent changes (TTS, push-to-talk, rebrand, well_known, sensitive defaults, cross-tenant fix, docs, pyproject)

---

## TL;DR

- **Critical: 1**, **High: 3**, **Medium: 4**, **Low: 4**
- **Most likely-to-bite-us:** the `pyproject.toml` version field. `0.1.0-durga` is **not PEP 440 compliant** and `[tool.hatch.version]` block still exists alongside a static `version`. Hatchling will reject the package at build time with `InvalidVersion`. Confirmed by reproducing locally with the `packaging` library.
- **Verdict on droplet deployment:** **WILL FAIL** unless the existing image at `ghcr.io/khoj-ai/khoj:latest` is being used (which is what `docker-compose.yml` line 45 does by default — meaning any Durga code change does not actually ship). If a fresh `docker compose build` against the local Dockerfile is attempted, `pip install --no-cache-dir .` errors during the `server-deps` stage on the version. Either path produces a deployment that is NOT the Durga build the agents wrote.

---

## CRITICAL

### C1. `pyproject.toml` static version `0.1.0-durga` is non-PEP-440; `[tool.hatch.version]` block still present
- **Agent:** #8 (pyproject.toml)
- **File:** `pyproject.toml:100` and `pyproject.toml:136-138`
- **What breaks:** Two compounding problems:
  1. `version = "0.1.0-durga"` is not PEP 440. Confirmed: `from packaging.version import Version; Version("0.1.0-durga")` raises `InvalidVersion`. Hatchling validates the project version on build and fails.
  2. `[tool.hatch.version] source = "vcs"` is still present. With a static `version` *and* this VCS source block but `version` NOT listed in `project.dynamic`, hatch's behavior depends on version: hatch-vcs >= 0.3 will at minimum log "static version takes precedence", and recent hatchling validates that the `[tool.hatch.version]` block is unused. Even when it accepts the static version, the build then re-fails on (1).
  3. Dockerfile `RUN sed -i "s/dynamic = \[\"version\"\]/version = \"$VERSION\"/" pyproject.toml` is now a **no-op** because there is no `dynamic = ["version"]` line to replace. The `ARG VERSION=0.0.0` machinery is dead.
- **Fix:**
  - Either: remove `version = "0.1.0-durga"`, restore `dynamic = ["version"]`, keep `[tool.hatch.version]`. Set version via the env-var/sed mechanism that already exists in the Dockerfile.
  - Or: keep static, change to PEP 440 like `version = "0.1.0+durga"` (local-version segment, `+` not `-`) or `0.1.0.dev0`, **and delete the entire `[tool.hatch.version]` block**, **and remove or update the Dockerfile sed (line 34 in `Dockerfile`, line 33 in `prod.Dockerfile`)**.
- **Test gap:** No CI step does `pip install .` against the modified pyproject. A 30-second smoke test would catch this.

---

## HIGH

### H1. `docker-compose.yml` ships `image: ghcr.io/khoj-ai/khoj:latest`, not the Durga image
- **Agent:** boundary issue (no agent owns docker-compose; #7/README assumes it works)
- **File:** `docker-compose.yml:45`
- **What breaks:** The README says `git clone … && docker compose up`. That command pulls the upstream Khoj image. NONE of the changes from the other seven agents (TTS, push-to-talk, rebrand, /.well-known, telemetry defaults, cross-tenant fix) actually run. The user gets vanilla upstream Khoj behavior — including telemetry on by default, default ElevenLabs-only TTS, no /.well-known endpoint, "Khoj" branding everywhere.
- The `build:` block exists on lines 47-48 but is commented out.
- **Fix:** Either flip the default to `build: { context: . }` and uncomment, or push the Durga image to a registry and reference it. Update README to reflect whichever path is chosen.
- **Test gap:** No integration test that loads `docker-compose.yml` and asserts the served `/` shows "Durga" branding or that `/.well-known/agents.txt` exists.

### H2. Dockerfile build path WILL fail on C1 if anyone ever switches to the local build
- **Agent:** #8 + Dockerfile owner
- **File:** `Dockerfile:34`, `prod.Dockerfile:33`
- **What breaks:** When the user follows H1's fix (uncomment `build:`), the build will fail at `pip install --no-cache-dir .` because of C1. So fixing H1 unlocks C1. Both must be fixed.
- **Fix:** Resolve C1 first.

### H3. `well_known.py` — `/agents.json` and `/ai.json` use the `*_TXT_PATH` env var as their override
- **Agent:** #4 (well_known)
- **File:** `src/khoj/routers/well_known.py:128-129`, `:138-139`
- **What breaks:**
  ```python
  @well_known_router.get("/agents.json", ...)
  async def agents_json() -> Response:
      return _serve_json("DURGA_AGENTS_TXT_PATH", "agents.json")
  ```
  If the operator sets `DURGA_AGENTS_TXT_PATH=/etc/durga/agents.txt` (the documented behavior — that env var is named for the .txt file), the JSON endpoint will read the .txt file, fail JSON parse (caught silently in `_inject_generated_at_json`), and serve plain text bytes with `Content-Type: application/json`. Same for `DURGA_AI_TXT_PATH`.
- **Fix:** Add separate `DURGA_AGENTS_JSON_PATH` and `DURGA_AI_JSON_PATH` env vars, or document loudly that the existing TXT vars are NOT consulted by the JSON routes. Tests in `tests/test_well_known.py` only exercise the *.txt override path.
- **Test gap:** `test_agents_override` and `test_ai_override` only test the .txt path. Add `test_agents_json_override` and `test_ai_json_override` (with both a real JSON file and a TXT file pointed at the JSON route).

---

## MEDIUM

### M1. Speech endpoint blocks the FastAPI event loop during synthesis
- **Agent:** #1 (TTS)
- **File:** `src/khoj/routers/api_chat.py:212`, `src/khoj/processor/speech/text_to_speech.py:93-108`
- **What breaks:** `text_to_speech` is `async def` but calls `generate_text_to_speech(...)` synchronously. The Edge TTS path spawns a `ThreadPoolExecutor(max_workers=1)`, submits `asyncio.run(...)`, and **blocks the calling thread on `.result()`**. The calling thread is the FastAPI event-loop thread. So a /api/speech call blocks the entire asyncio loop for the full synthesis duration (typical 1-3 seconds for Edge TTS). Other concurrent requests stall.
  - The ElevenLabs path uses `requests.post(..., stream=True)` which similarly blocks. This is pre-existing upstream behavior.
- **Fix:** Wrap the call in `await asyncio.to_thread(generate_text_to_speech, **params)` in `api_chat.py`. Or make `generate_text_to_speech` a proper coroutine and await `_edge_tts_async` directly (no thread pool, no nested loop).
- **Test gap:** No load test exercises concurrent speech requests.

### M2. `_looks_like_edge_voice` "Neural" heuristic is fragile
- **Agent:** #1 (TTS)
- **File:** `src/khoj/processor/speech/text_to_speech.py:77-79`
- **What breaks:** The check requires both `-` and `Neural` in the voice id. Edge TTS catalog also includes voices ending in `Multilingual`, `Standard`, and a few region-specific names (`zh-CN-XiaoxiaoMultilingualNeural` is fine, but Microsoft has been adding non-Neural variants). If Microsoft adds a new voice without "Neural" in its name (or if Kayla seeds the DB with `en-US-AriaMultilingualNeural` — fine, still has "Neural") this still works. But any catalog name without "Neural" is treated as ElevenLabs and tries to call ElevenLabs with an Edge voice ID, which will fail.
  - Conversely, an ElevenLabs voice with a literal "-Neural" suffix in the ID (none currently exist; their IDs are alphanumeric 20-char) would route to Edge.
- **Fix:** Match on the regex pattern `^[a-z]{2}-[A-Z]{2}-` (BCP-47 locale prefix) which is far more reliable than substring "Neural". Or, store the provider explicitly in `VoiceModelOption` and route on that field.
- **Test gap:** No tests for `_looks_like_edge_voice` at all.

### M3. Push-to-talk hotkey `Ctrl+Shift+Space` collides with Windows IME language switch
- **Agent:** #2 (chatInputArea push-to-talk)
- **File:** `src/interface/web/app/components/chatInputArea/chatInputArea.tsx:70-77`, `:454-487`
- **What breaks:** Ctrl+Shift+Space is a default Windows IME hotkey for switching input methods (e.g., Chinese/Japanese input toggle). The handler calls `e.preventDefault()` unconditionally on match, so users with multi-language Windows configs lose their IME toggle when this app is focused. Also, pressing the combo when there is no permission for `getUserMedia` (e.g., mic blocked) silently does nothing, with no visible feedback beyond the "Recording..." indicator that briefly flashes.
- **Fix:** Make the hotkey configurable. Provide a settings entry. Or pick a less-collision-prone combo (e.g., Alt+`).
- **Test gap:** No frontend tests at all in `src/interface/web/`.

### M4. `is_eleven_labs_enabled` flag still exposed to the frontend, naming is now misleading
- **Agent:** #1 (TTS) didn't touch this; #3 (rebrand) didn't touch this
- **File:** `src/khoj/routers/helpers.py:2966, :2999`, `src/interface/web/app/common/auth.ts:84`
- **What breaks:** The boolean `is_eleven_labs_enabled` is sent in user config. With the new TTS, Edge TTS may be enabled while ElevenLabs is not — meaning TTS is available but the flag says false. The settings UI gates voice option visibility on `voice_model_options.length > 0` (settings/page.tsx:1207), so it doesn't directly cause a regression today. But the flag is now semantically wrong and will mislead anyone who consumes it.
- **Fix:** Add a parallel `is_edge_tts_enabled` field, or rename to `is_text_to_speech_enabled` (compute via `is_text_to_speech_enabled()` which already exists in `text_to_speech.py`).

---

## LOW

### L1. Empty static version after Dockerfile sed no-op leaves `state.khoj_version` undefined-ish
- **Agent:** #8
- **File:** `src/khoj/main.py:215` reads `state.khoj_version = version("khoj")`
- **What breaks:** Once C1 is fixed and the package installs, `version("khoj")` returns whatever was set. If hatch-vcs is restored, this is the git-derived version. If C1 is fixed by hardcoding `0.1.0+durga`, that string ends up in the cache-bust query strings (`/static/assets/khoj.css?v=0.1.0+durga`) — `+` is technically reserved in URL query strings; will be auto-encoded by browsers. Cosmetic.
- **Fix:** Use `0.1.0.dev0` or `0.1.0` to avoid `+`.

### L2. `BeautifulSoup(html, features="lxml")` + `findAll(text=True)` will break on BS4 4.13+
- **Agent:** #1 (TTS)
- **File:** `src/khoj/processor/speech/text_to_speech.py:74`
- **What breaks:** `findAll` was renamed to `find_all` (alias still works but emits DeprecationWarning). `text=True` was renamed to `string=True` in 4.13. Today: `beautifulsoup4 ~= 4.12.3` is pinned, so it works. If the dep is ever bumped to 4.13+ this silently returns no text → all TTS output becomes the empty string.
- **Fix:** Use `find_all(string=True)`. Two-character change, future-proof.

### L3. `docker-compose.yml` ships `KHOJ_ADMIN_PASSWORD=password` and `KHOJ_DJANGO_SECRET_KEY=secret` while README claims "anonymous, single-user, local-only"
- **Agent:** #7 (docs) didn't update docker-compose
- **File:** `docker-compose.yml:71, :73-74`, README line 51
- **What breaks:** `--anonymous-mode` is set on line 125, so admin creds are unused at runtime. But the README's "no accounts" claim is technically false until those lines are removed or commented. Also if a user disables anonymous mode, they inherit `admin@example.com / password` and `secret` Django key.
- **Fix:** Generate random secrets in an entrypoint script, or document loudly that these defaults must be changed before exposing the service to the network.

### L4. `agents.txt` and `ai.txt` static defaults hardcode `https://durga.local` as `Site-URL`
- **Agent:** #4 (well_known)
- **File:** `src/khoj/static/well-known/agents.txt:8, :13, :17, :22, :26, :32, :36, :41, :45, :62`, same in `ai.json`
- **What breaks:** When deployed to `https://174-138-85-227.nip.io` (or any host other than `durga.local`), the Site-URL and capability-endpoint URLs in the served `agents.txt` are wrong. Agents reading the declaration will try to call the wrong host.
- **Fix:** Template the host from `KHOJ_DOMAIN` (or a new `DURGA_PUBLIC_URL`) at request time, or document that operators must set `DURGA_AGENTS_TXT_PATH` to a file with their real public URLs.

---

## Things I checked that are FINE

- Default agent slug/name: `DEFAULT_AGENT_NAME = "Khoj"` and `DEFAULT_AGENT_SLUG = "khoj"` preserved in `src/khoj/database/adapters/__init__.py:673-674`. Frontend `setSelectedAgent("khoj")`, `by === "khoj"`, `slug === "khoj"` all preserved. Rebrand pass correctly identified these as data values.
- Cross-tenant fix in `helpers.py:1325, 2564` matches the `aget_conversation_by_user`/`get_conversation_by_user` signatures (both accept `user=` and `conversation_id=` kwargs).
- `/.well-known/` route does not collide with `web_client.py`'s existing `/.well-known/assetlinks.json` route. The `well_known_router` only handles four paths; assetlinks falls through to `web_client`.
- Auth middleware does not protect `/.well-known/*` (no `@requires(["authenticated"])` on those endpoints). Public as intended.
- Static well-known files are present in the source tree at `src/khoj/static/well-known/` and will ship with the Docker image via `COPY . .` on Dockerfile line 56. Path resolution in `well_known.py` (`_STATIC_DIR`) is correct.
- `lxml == 4.9.3` is in `pyproject.toml` deps (line 73). `BeautifulSoup(features="lxml")` will work today (see L2 for future risk).
- Telemetry triple-guard works correctly. Empty string `telemetry_server` short-circuits before any URL is dereferenced. Env var precedence (`DURGA_*` > `KHOJ_*`) parses correctly. The legacy `KHOJ_TELEMETRY_DISABLE` still forces off.
- Push-to-talk does NOT conflict with the sidebar Ctrl+B hotkey or the chatMessage container Space-to-activate-link handler (the latter early-returns when no anchor is focused).
- The push-to-talk recording state machine handles the spin-up race correctly via the `[recording, mediaRecorder]` effect deps.
- The click-to-record toggle flow at `chatInputArea.tsx:864-867` is unchanged by the push-to-talk additions.

---

## Multi-agent stepping-on-toes

- **Agent #7 (docs/README) and the absent docker-compose owner** stepped past each other. README claims a `docker compose up` workflow that the docker-compose.yml does not deliver (H1 + L3).
- **Agent #8 (pyproject) and the Dockerfile owner** stepped past each other. The static version in pyproject made the Dockerfile sed a no-op without anyone removing it. Combined effect: C1.
- **Agent #1 (TTS) and Agent #3 (rebrand)** did not coordinate on `is_eleven_labs_enabled` — the API field is now misleading (M4).
- **Agent #4 (well_known) and Agent #7 (docs)** did not coordinate on `Site-URL` — the static defaults bake in `durga.local` (L4) but README says you can run on any port/host.

No security issues are claimed in this report; that is the red-team agent's lane.

---

## Test gaps to flag for follow-up

| Area | Test that would have caught it |
|---|---|
| C1 | CI step `pip install .` against the pyproject (would catch in <30s) |
| H1 | E2E test that `docker compose up` brings up something serving `/.well-known/agents.txt` |
| H3 | `test_agents_json_override` and `test_ai_json_override` in `tests/test_well_known.py` |
| M1 | Concurrent /api/speech load test |
| M2 | Unit tests for `_looks_like_edge_voice` covering all three known voice-id shapes (Edge, ElevenLabs, malformed) |
| M3 | Frontend tests for chatInputArea (entire `src/interface/web/` has zero tests) |
| Rebrand | Visual regression / snapshot tests of titles and key strings |
