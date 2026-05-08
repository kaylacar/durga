# Durga Red-Team Report

Reviewer: adversarial security review of the recent Durga changes (v0.1.0 candidate). Scope: only the files explicitly listed in the change set. Assumes original khoj-ai/khoj invariants hold unless a Durga change broke them.

Verdict: **Do not ship as v0.1.0 yet.** There is one critical issue (arbitrary-file-read primitive on an unauthenticated endpoint), several high-severity issues that undermine the SECURITY.md promise, and meaningful gaps in the test suite. Most fixes are small.

Counts: 1 critical, 6 high, 7 medium, 6 low, 4 informational.

---

## CRITICAL

### C-1. Unauthenticated arbitrary-file-read via `DURGA_AGENTS_TXT_PATH` / `DURGA_AI_TXT_PATH`
File: `src/khoj/routers/well_known.py:45-65, 106-119, 122-139`

The four `/.well-known/` endpoints are mounted unauthenticated. If the operator points either env var at any path the Durga process can read, that file is served verbatim, with content-type `text/plain` (for the `.txt` routes) or `application/json` (for `.json`).

There is no:

* path canonicalization / no allow-list of safe directories
* check that the file lives under `_STATIC_DIR`
* size cap (a `/dev/zero` or huge log file would be slurped to memory)
* content-type or shape validation (a non-JSON file is still returned with `application/json` content-type, though `_inject_generated_at_json` falls back to returning the raw body when JSON parse fails)

Attack scenarios:

1. Operator misconfig: sets `DURGA_AGENTS_TXT_PATH=/etc/passwd` (or the equivalent on Windows, e.g. `C:\Users\teche\.khoj\env`) thinking it is harmless. Anyone on the public internet hits `/.well-known/agents.txt` and exfiltrates the file.
2. Worse: `DURGA_AGENTS_TXT_PATH=/proc/self/environ` returns the entire process environment — `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `STRIPE_API_KEY`, `KHOJ_DJANGO_SECRET_KEY`, `RESEND_API_KEY`, `TWILIO_AUTH_TOKEN`, `AWS_SECRET_KEY`, telemetry receiver URL, etc. Same path works for `~/.khoj/env`, `/proc/self/cmdline`, the user's SSH private key if Durga is running as that user, indexed-document raw text via PostgreSQL data files, etc.
3. Symlink TOCTOU: if the env var points at a path inside an attacker-writable directory (e.g. `/tmp/agents.txt` on a shared host), the attacker swaps in a symlink and reads any file the Durga UID can read.
4. The override file is re-read on every request (no cache), so polling drift attacks are trivial.

This is the single worst issue in the change set. The endpoint is an unauthenticated public surface that is documented to serve a specific RFC 8615 declaration; turning it into a `cat` primitive is an obvious footgun.

Recommended fix:

* Treat the env vars as filenames, not full paths: resolve to `_STATIC_DIR / Path(env_value).name` and reject anything that would escape `_STATIC_DIR` after `Path.resolve()`.
* Or require the override path to live under a single configurable directory (e.g. `DURGA_WELL_KNOWN_DIR`) and refuse `..` / symlinks (`os.path.realpath` + `commonpath` check).
* Cap the read size (e.g. 64 KB; anything larger is garbage for an agents.txt anyway).
* For the `.json` endpoints, parse the file as JSON and refuse to serve it on `JSONDecodeError` — never return non-JSON bytes as `application/json`.
* Log at WARNING (not just on `OSError`) when the override path resolves outside the safe directory, and fall through to the bundled default.

---

## HIGH

### H-1. `state.telemetry` grows unboundedly when telemetry is disabled
File: `src/khoj/routers/helpers.py:224-232`, `src/khoj/utils/helpers.py:282-283`, `src/khoj/configure.py:441-461`

`update_telemetry_state` always appends `log_telemetry(...)` to `state.telemetry`. When telemetry is disabled, `log_telemetry` returns `[]`, so each request appends an empty list to the global. The list is only cleared in `upload_telemetry()` *after a successful upload*, which short-circuits when `telemetry_disabled` is True (the new Durga guard).

Effect: in the privacy-first default configuration, `state.telemetry` grows by one element per API request, forever. Single-process leak, not catastrophic, but on a busy multi-user server this is unbounded memory growth on top of every request. Eventually OOMs the process.

Fix: short-circuit in `update_telemetry_state` itself when `state.telemetry_disabled`, before constructing the dict and appending. (Bonus: stop allocating the per-request `user_state` dict when nobody is going to read it.)

### H-2. `_autoUpdateEnabled` env semantics differ from server `is_env_var_true`
File: `src/interface/desktop/main.js:9-14`, `src/khoj/utils/helpers.py:761-763`

Desktop accepts `DURGA_AUTOUPDATE` values `'1'` or `'true'`. Server `is_env_var_true` *only* accepts case-insensitive `'true'`. Result:

* `DURGA_TELEMETRY_ENABLE=1` is silently ignored on the server side. A user who copies the desktop convention will *think* they enabled telemetry and not see it firing — or, more concerning, will set `DURGA_TELEMETRY_DISABLE=1` thinking they disabled telemetry (the server will not honor `1` and telemetry will remain in whatever its other state is).
* Any future env var documented as accepting `1` will be inconsistent with the rest of the codebase.

Pick one. Recommend updating `is_env_var_true` to accept `{"1", "true", "yes", "on"}` (case-insensitive), and document.

### H-3. Desktop CSP still allows outbound to `app.khoj.dev` and `assets.khoj.dev`
File: `src/interface/desktop/main.js:434, 439`

The CSP is built with `defaultDomains = "'self' ${hostURL} https://app.khoj.dev https://assets.khoj.dev"` and `img-src` adds `https://*.khoj.dev`. Even with the default `hostURL` flipped to `127.0.0.1:42110`, the desktop client is permitted to talk to (and load images from) the upstream Khoj SaaS. A malicious or compromised page rendered in the desktop window can exfiltrate via image loads to `https://attacker-controlled-subdomain.khoj.dev`-shaped URLs (well, anything matching `*.khoj.dev`), and `connect-src` of `${hostURL}` is fine, but the broad `default-src` includes `app.khoj.dev` for connect/script too.

This contradicts SECURITY.md's claim that the desktop client doesn't contact `app.khoj.dev` by default. Even a script error or a `<img>` beacon would cause traffic to a third party.

Fix: build CSP from the configured `hostURL` only, plus `'self'`. Drop the hardcoded `khoj.dev` domains. If you need them for the (now opt-in) "use the hosted service" path, add them only when `hostURL` actually points at `app.khoj.dev`.

### H-4. Hardcoded `app.khoj.dev` upgrade prompts in helpers.py and main.js error handler
Files: `src/khoj/routers/helpers.py:2148, 2198, 2377`, `src/interface/desktop/main.js:281, 288`

Three error paths in `helpers.py` render Markdown links to `https://app.khoj.dev/settings`. In a self-hosted Durga deployment, telling the user "go upgrade at app.khoj.dev" sends them to a third-party SaaS that has nothing to do with their data — and trains the user to click a link to a domain they didn't sign up for. If `app.khoj.dev` is ever taken over, every Durga user sees a phishing redirect.

`main.js:288` falls back to "Contact team@khoj.dev to report this issue." Same problem: routes user reports to an upstream that no longer maintains this fork.

Fix: make these error strings reference the user's configured `hostURL` (or a `DURGA_SUPPORT_URL` / `DURGA_SUPPORT_EMAIL` env var) and fall back to nothing rather than to the upstream brand.

### H-5. `_inject_generated_at_json` re-serializes attacker-influenced JSON without schema validation, and silently passes through malformed JSON
File: `src/khoj/routers/well_known.py:95-103, 114-119`

When the override file *parses* as JSON, `_inject_generated_at_json` injects `generatedAt` into the top-level dict and re-serializes — fine, but it also accepts any structure. When the override is malformed JSON, the function returns the raw bytes and `_serve_json` ships them as `application/json`. The endpoint thus serves arbitrary bytes with a JSON content-type, breaking parsers downstream and bypassing any agent that does strict JSON validation.

If the override is JSON but a list or scalar (e.g. `[]` or `"haha"`), `isinstance(data, dict)` is False and the original parsed value is silently dropped — `_inject_generated_at_json` returns `body` unchanged. This is fine for safety but contradicts the test expectation (`assert "generatedAt" in data`).

Fix: when JSON parse fails, log and fall through to the bundled default rather than serving raw bytes as JSON. Validate the top-level shape (must be an object) before serving.

### H-6. Unbounded TTS audio buffering + no per-request timeout = trivial memory + thread DoS
File: `src/khoj/processor/speech/text_to_speech.py:82-127`

`_edge_tts_async` collects every `chunk["data"]` into a Python list and joins at the end. There is no cap on input text length and no cap on cumulative chunk size. A user (or any agent that has bearer token) can request TTS for a very long text and force the server to buffer the entire MP3 in memory before the streaming response begins.

`_generate_edge_tts` runs that work via a fresh `ThreadPoolExecutor(max_workers=1)` per call (wasteful but not the security problem) and calls `.result()` *without a timeout*. If Microsoft's edge endpoint hangs, the FastAPI request thread blocks indefinitely. Same hazard in `_generate_eleven_labs`: `requests.post(tts_url, ..., stream=True)` has no `timeout=` kwarg.

Combining the two: an authenticated attacker hitting `/api/speech` with large text on a slow upstream can starve the worker pool and pin RAM with a few requests.

Fix:

* Cap input `text` length (e.g. 4096 chars; raise `TextToSpeechError` otherwise).
* Stream chunks straight through to the response generator instead of buffering the whole thing.
* Pass `timeout=` to `requests.post`.
* Use `asyncio.wait_for(..., timeout=...)` in `_edge_tts_async`, or add a timeout to the executor call.

---

## MEDIUM

### M-1. `voice_id` is interpolated into a URL path with no validation
File: `src/khoj/processor/speech/text_to_speech.py:111-126`

`tts_url = f"{ELEVEN_API_URL}/{voice_id}/stream"`. If `voice_id` contains `/` or `?`, an attacker can re-target the request inside `api.elevenlabs.io` (e.g. swap `/text-to-speech/{id}/stream` for an entirely different ElevenLabs API endpoint). With ElevenLabs that is bounded to ElevenLabs-controlled URLs, but it still:

* lets the attacker probe for and consume non-TTS quotas under the operator's API key
* makes the operator's billing log attribute non-TTS usage to the Durga app
* if a future voice_id contains `\r\n`, `requests` will raise, but the error message is then fed back via `TextToSpeechError(f"... {response.text}")`

Fix: validate `voice_id` against `^[A-Za-z0-9_-]{8,32}$` (the ElevenLabs ID shape) before formatting, raise `TextToSpeechError` otherwise. Same for the Edge voice (`^[a-z]{2,3}-[A-Z]{2}-[A-Za-z0-9]+Neural$`).

### M-2. `_looks_like_edge_voice` is too permissive
File: `src/khoj/processor/speech/text_to_speech.py:77-79`

`return bool(voice_id) and "-" in voice_id and "Neural" in voice_id`. `voice_id = "x-Neural"`, `"------Neural"`, `"foo-Neural?api_key=..."` all match. Combined with M-1, this widens the routing-bypass surface.

Fix: anchor with a real regex.

### M-3. ElevenLabs API-key empty-string check
File: `src/khoj/processor/speech/text_to_speech.py:55-56, 113`

`is_eleven_labs_enabled()` returns True when the env var is set to the empty string. `xi-api-key: ""` is then sent on every TTS call. Doesn't leak the key but does:

* fingerprint the deployment to ElevenLabs
* generate noisy 401s in operator logs that look like a credential leak

Fix: `return ELEVEN_LABS_API_KEY is not None and ELEVEN_LABS_API_KEY != ""`.

### M-4. `get_conversation_by_id` is still in the adapter
File: `src/khoj/database/adapters/__init__.py:1072-1074`

The unscoped helper has no remaining callers in user-facing code (verified). It is left "for upstream-merge compatibility." This is a footgun: every future refactor or merge has the chance of regressing. Anyone copy-pasting from upstream brings it back live.

Fix: either delete the method (and resolve merges manually each time) or replace its body with `raise NotImplementedError("Use get_conversation_by_user; cross-tenant lookups are not allowed in Durga.")`. SECURITY.md explicitly calls this out as the leak vector that Durga fixed; the fix should be enforced, not just documented.

### M-5. Push-to-talk hotkey does not check `event.isTrusted`
File: `src/interface/web/app/components/chatInputArea/chatInputArea.tsx:454-471`

A page-level XSS or a hostile browser extension can `dispatchEvent(new KeyboardEvent("keydown", {...}))` with the right code/modifier combo and silently start the microphone, provided the user has previously granted mic permission to the origin (which they will have if they ever used voice once). The handler never checks `e.isTrusted`. The visible "Recording..." banner is the only signal — and on mobile, where the banner may not be in viewport, the user could miss it.

Fix: `if (!e.isTrusted) return;` at the top of `handleKeyDown` and `handleKeyUp`.

### M-6. `setURL` defaults missing-scheme to `http://`
File: `src/interface/desktop/main.js:367-374`

`if (!url.match(/^[a-zA-Z]+:\/\//)) url = "http://" + url;`. A user typing `my-server.example.com` gets `http://my-server.example.com`, and the bearer token in `pushDataToKhoj` is then sent over plaintext HTTP. Combined with H-3, even on the modern web that token is interceptable on any open Wi-Fi.

Fix: default to `https://` when the host is not loopback / `*.local`. Loopback can stay HTTP.

### M-7. Tests don't catch the C-1, H-5, or H-6 attacks
File: `tests/test_well_known.py`

The override tests only verify that a benign override file is served. They do not:

* assert that an override pointing at an arbitrary file outside `_STATIC_DIR` is rejected (would fail today; that's exactly C-1)
* assert that a malformed-JSON override is *not* served as `application/json` (would fail today; that's H-5)
* assert that a giant override is bounded (would fail today; partial of H-6)
* assert that the well-known routes are served unauthenticated and that *no other* route under `/.well-known/` accidentally got registered

Add tests for each of those before claiming spec conformance.

---

## LOW

### L-1. `edge-tts >= 7.0.0` is unpinned; `uv.lock` does not contain it
File: `pyproject.toml:81`, `uv.lock`

The dep is open-ended. Any future 7.x release of `edge-tts` (a single-maintainer reverse-engineered library that talks to a Microsoft endpoint that *can change at any time*) gets pulled in. The `uv.lock` does not contain `edge-tts`, so the lockfile is stale; first `uv sync` after this change resolves freely.

This is a textbook supply-chain risk: the package is well-regarded but a single-maintainer GitHub project; account compromise → malicious post-install → arbitrary code in the Durga server's process. SECURITY.md says no analytics SDKs are bundled — but a future malicious `edge-tts` could absolutely add one.

Fix: pin to a specific known-good version (`edge-tts == 7.x.y`), regenerate `uv.lock`, and consider hash-pinning. At minimum, pin the major+minor.

### L-2. CRLF in Generated-At injection
File: `src/khoj/routers/well_known.py:68-92`

`splitlines()` then `"\n".join(out)`. A file with `\r\n` line endings ends up with `\n`-only output. Fine for text/plain, but if the file already had `Generated-At:` followed by trailing whitespace and a CR, that may matter for downstream parsers that key off CRLF. Cosmetic — not an injection — because the stamp itself is a controlled `datetime.now()` string.

Fix: none required; just be aware. If you want bit-for-bit fidelity to the override, preserve the original line endings.

### L-3. `_now_iso` does not use `replace(microsecond=...)` / leap-second-safe
File: `src/khoj/routers/well_known.py:39-42`

Cosmetic. `datetime.now(timezone.utc).isoformat(timespec="milliseconds")` is the obvious one-liner.

### L-4. `markdown_renderer` uses `lxml` which can fetch external entities by default
File: `src/khoj/processor/speech/text_to_speech.py:32, 72-74`

`MarkdownIt().render(md_text)` produces HTML, which is then parsed by `BeautifulSoup(html, features="lxml")`. lxml does not fetch external entities by default *for HTML parsing*, so XXE is not directly applicable here, but the input is markdown that has been auto-generated from chat output. If a future model output includes an HTML construct that lxml mis-parses, the "audio buffering" cap (H-6) is your only line of defense. Low risk under current usage.

### L-5. `text_to_speech` swallows microphone-side errors silently in the browser
File: `src/interface/web/app/components/chatInputArea/chatInputArea.tsx:419-421`

If `getUserMedia` rejects (user denies permission), the catch block only logs to console. The push-to-talk indicator still says "Recording..." until key-up. User believes they are recording and may say something they don't want submitted. The next time they enable the mic, the buffer they thought was discarded could in fact have been captured (on this code path it is not, but the UX trains the user to trust an indicator that lies).

Fix: surface mic-permission errors to the UI; hide the "Recording..." banner if `mediaRecorder` is null after the timeout.

### L-6. `app://khoj.dev` left in default CORS origins
File: `src/khoj/main.py:79`

Allows the Khoj desktop app's custom URL scheme to make CORS requests against the Durga server. A user who installs both the upstream Khoj desktop app and a Durga server on the same machine could end up with the Khoj desktop app talking to Durga. Probably benign (they would still need a token), but it leaks "Durga is here" to the upstream client.

Fix: replace `app://khoj.dev` with `app://durga.local` or whatever the rebranded scheme is, or drop it.

---

## INFORMATIONAL

### I-1. The `agents.txt` / `ai.txt` content claims `Site-URL: https://durga.local`
The bundled defaults declare `https://durga.local` — fine for the spec example, but a self-hosted Durga's actual URL is whatever the operator chose. Agents that follow `Site-URL` will hit `durga.local` (DNS will not resolve outside the operator's machine). Recommend interpolating the configured `KHOJ_DOMAIN`/`DURGA_DOMAIN` at request time when the override is not set.

### I-2. The contact email in agents.txt / agents.json / ai.txt / ai.json is hardcoded to `contactkaylacard@gmail.com`
This is fine for Tech Enrichment's reference deployment but every fork that ships these defaults will leak Kayla's personal email as the contact. Make the contact a `DURGA_CONTACT_EMAIL` env var with a sane fallback.

### I-3. Telemetry `state.telemetry_disabled` boolean precedence is awkward but correct
`not (DURGA_ENABLE or KHOJ_ENABLE) or KHOJ_DISABLE`. Reads weirdly but is correct: disabled by default, opt-in via either ENABLE, override-back-to-disabled via legacy DISABLE. Add a unit test that pins down the truth table; no existing test covers this.

### I-4. The "third guard" is genuine but only fires at upload time
File: `src/khoj/configure.py:441`. The `not constants.telemetry_server` guard fires only inside the every-2-minutes `upload_telemetry` job. Telemetry events are still constructed and appended to `state.telemetry` between uploads (see H-1). Functionally correct as a network kill-switch, but does not stop the in-process accumulation.

---

## TL;DR for the reviewer asking "would I ship this as v0.1.0"

No.

Fix C-1 today (single most embarrassing finding: a "privacy-first personal AI" that ships with an unauthenticated `/etc/passwd` reader if the operator points one env var the wrong way). Fix H-1 because it bites every privacy-first deployment. Fix H-3 and H-4 because they directly contradict the SECURITY.md promise that the desktop client and server-side error messages don't reach upstream Khoj. The rest can land as a 0.1.1.

The `get_conversation_by_user` switch in helpers.py is real — both call sites are properly scoped, and the unscoped variant has no remaining callers. Good. Leave the unscoped helper as a NotImplementedError or delete it.

The push-to-talk implementation is competent — it handles repeats, blur, and editable-target detection. The one gap is `e.isTrusted`. Add it.
