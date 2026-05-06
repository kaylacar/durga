# Khoj → Durga Rebrand: User-Facing String Changes

This document lists every file that will be (or has been) modified for the user-facing rebrand of the Khoj fork to Durga. The pass deliberately under-rebrands rather than over-rebrands. Internal identifiers, package names, attribution, asset URLs, API endpoint paths, class/function/variable names, and database tables are left untouched.

Conventions used:
- "Khoj" → "Durga" (proper noun in user-facing prose / titles)
- "Khoj AI" → "Durga AI"
- "Khoj Cloud" / "Khoj Team" / "Khoj Futurist" — FLAGGED for review (these are Khoj-specific product/company terms; renaming may change semantics)
- "khoj" (lowercase) is left alone almost everywhere — it appears as URL slug, agent slug, internal author identifier (e.g. `by === "khoj"`), and is part of compound identifiers we must not touch

---

## Patterns observed (DO NOT auto-rebrand these)

These show up frequently and must be preserved:

- **Compound identifiers**: `khoj-ai/khoj` (GitHub org/repo), `app.khoj.dev`, `assets.khoj.dev`, `docs.khoj.dev`, `blog.khoj.dev`, `team@khoj.dev`, `khoj.dev` — asset/URL strings, intentionally preserved per instructions
- **Internal data values**: `by === "khoj"` (chat message author), `slug === "khoj"` (default agent slug), `agent.name === "khoj"` (default agent display)
- **React component names**: `KhojLogo`, `KhojLogoType`, `KhojSearchLogo`, `KhojAgentLogo`, `KhojAutomationLogo` — class/function names, do not touch
- **CSS class / styles module identifiers**: `div.khoj`, `div.khojfullHistory`, `div.khojChatMessage`, `.khoj-configure`, `.khoj-header`, `.khoj-nav`, `.khoj-logo` — DOM-level class names that JS depends on
- **Python module references**: `khoj.utils.helpers`, `khoj.app.settings`, etc. — module imports
- **Logger name**: `logger = logging.getLogger("khoj")` — namespacing
- **Asset filenames**: `khoj_lantern_128x128.png`, `khoj-logo-sideways-500.png`, `khoj_hero.png`, `khoj.webmanifest`, `khoj_app_hero_image.avif`, `khoj.css`, `khoj_logo.png`, `khoj.svg` — physical files, not changed (will swap assets later per scope)
- **Webmanifest path reference**: `manifest: "/static/khoj.webmanifest"` — path to physical file, leave
- **API/state field names**: `khoj_version`, `khoj_cloud_subscription_url` — wire format
- **Storage keys**: `khoj-cloud-deprecation-dismissed` (localStorage key) — would lose state on rebrand; leave
- **Config file paths**: `~/.khoj/khoj.log` in CLI default — path, internal
- **Environment variables**: `KHOJ_DOMAIN`, `KHOJ_NO_HTTPS` — env var names
- **Email senders / addresses**: `noreply@khoj.dev`, `team@khoj.dev`, `khoj@khoj.dev` — Khoj-owned addresses, leave

---

## Files modified

### `src/khoj/main.py`
Server log greetings (visible to anyone running the server).

| Line | Before | After |
|------|--------|-------|
| 107 | `logger.info("🌑 Shutting down Khoj")` | `logger.info("🌑 Shutting down Durga")` |
| 134 | `logger.info(f"🚒 Initializing Khoj v{state.khoj_version}")` | `logger.info(f"🚒 Initializing Durga v{state.khoj_version}")` |
| 148 | `logger.info("🌘 Starting Khoj")` | `logger.info("🌘 Starting Durga")` |
| 219 | `logger.info("🌖 Khoj is ready to engage")` | `logger.info("🌖 Durga is ready to engage")` |
| 243 | `logger.info("🌒 Stopping Khoj")` | `logger.info("🌒 Stopping Durga")` |

Lines 1, 70, 79 are NOT changed — module docstring, env var name, and cors origin URL.

### `src/khoj/utils/cli.py`
CLI help text shown by `--help`.

| Line | Before | After |
|------|--------|-------|
| 11 | `description="Start Khoj; An AI personal assistant for your Digital Brain"` | `description="Start Durga; An AI personal assistant for your Digital Brain"` |
| 28 | `help="Print the installed Khoj version and exit"` | `help="Print the installed Durga version and exit"` |
| 33 | `help="Run Khoj in single user mode with no login required..."` | `help="Run Durga in single user mode with no login required..."` |
| 39 | `help="Start Khoj in non-interactive mode..."` | `help="Start Durga in non-interactive mode..."` |

Lines 14, 47, 49 not changed — they reference `~/.khoj/khoj.log` (path) and `version("khoj")` (package name lookup).

### `src/khoj/interface/email/welcome.html`
Welcome email template.

| Line | Before | After |
|------|--------|-------|
| 7 | `<title>Welcome to Khoj</title>` | `<title>Welcome to Durga</title>` |
| 16 | `alt="Khoj Logo"` | `alt="Durga Logo"` |
| 51-52 | `Khoj stores whatever documents...` | `Durga stores whatever documents...` |
| 59 | `Let Khoj run for longer and...` | `Let Durga run for longer and...` |
| 68 | `- The Khoj Team` | `- The Durga Team` |

Asset URLs (`assets.khoj.dev`, `app.khoj.dev`, `docs.khoj.dev`, `blog.khoj.dev`, `github.com/khoj-ai/khoj`, `twitter.com/khoj_ai`, `linkedin.com/company/khoj-ai`) are preserved.

### `src/khoj/interface/email/magic_link.html`

| Line | Before | After |
|------|--------|-------|
| 7 | `<title>Welcome to Khoj</title>` | `<title>Welcome to Durga</title>` |
| 16 | `alt="Khoj Logo"` | `alt="Durga Logo"` |
| 19 | `Use this code to login to Khoj:` | `Use this code to login to Durga:` |
| 29 | `- The Khoj Team` | `- The Durga Team` |

### `src/khoj/interface/email/task.html`

| Line | Before | After |
|------|--------|-------|
| 6 | `<title>Khoj AI - Automation</title>` | `<title>Durga AI - Automation</title>` |
| 11 | `alt="Khoj Logo"` | `alt="Durga Logo"` |
| 27 | `<div ...>- Khoj</div>` | `<div ...>- Durga</div>` |

### `src/khoj/interface/email/feedback.html`
This template is sent to the team mailbox; user-visible at receipt.

| Line | Before | After |
|------|--------|-------|
| 4 | `<title>Khoj Feedback Form</title>` | `<title>Durga Feedback Form</title>` |
| 10 | `alt="Khoj Logo"` | `alt="Durga Logo"` |
| 20 | `<h3>Khoj's Response</h3>` | `<h3>Durga's Response</h3>` |

### `src/khoj/routers/email.py`
Email subject lines and the sender display name.

| Line | Before | After |
|------|--------|-------|
| 47 | `"subject": "Your login code to Khoj"` | `"subject": "Your login code to Durga"` |
| 66 | `f"{name}, four ways to use Khoj" if name else "Four ways to use Khoj"` | `f"{name}, four ways to use Durga" if name else "Four ways to use Durga"` |
| 130 | `f"Khoj <{os.environ.get('RESEND_EMAIL', 'khoj@khoj.dev')}>"` | `f"Durga <{os.environ.get('RESEND_EMAIL', 'khoj@khoj.dev')}>"` |

Line 87 (`f"Sentiment: ... Khoj Response: {kquery}"`) — internal log only — left unchanged.

### `src/khoj/interface/web/error.html`
Server-side rendered error page.

| Line | Before | After |
|------|--------|-------|
| 7 | `<title>Khoj - Service Temporarily Unavailable</title>` | `<title>Durga - Service Temporarily Unavailable</title>` |
| 133 | `<h1>Khoj Temporarily Unavailable</h1>` | `<h1>Durga Temporarily Unavailable</h1>` |

Asset URLs and `team@khoj.dev`, `github.com/khoj-ai/khoj` preserved per instructions.

### `src/khoj/interface/web/base_config.html`

| Line | Before | After |
|------|--------|-------|
| 7 | `<title>Khoj</title>` | `<title>Durga</title>` |

CSS class names (`khoj-configure`, `khoj-header-wrapper`, `khoj-nav-selected`) kept — DOM-level identifiers used by JS.

### `src/khoj/interface/web/utils.html`

| Line | Before | After |
|------|--------|-------|
| 4 | `alt="Khoj"` (logo image alt text) | `alt="Durga"` |

CSS classes (`khoj-header`, `khoj-logo`, `khoj-nav`) and id `khoj-nav-menu*` left as-is (DOM identifiers).

### `src/khoj/interface/web/home/index.html`
Server-side rendered home/landing page.

| Line | Before | After |
|------|--------|-------|
| 6 | `<title>Khoj AI</title>` | `<title>Durga AI</title>` |
| 19 | `<strong>Khoj Cloud is being deprecated on April 15, 2026.</strong>` | FLAG (see REVIEW) |
| 21 | `To continue using Khoj, you can` | FLAG (see REVIEW) |
| 46 | `alt="Khoj"` (logo alt) | `alt="Durga"` |
| 296 | `<h2 ...>Khoj for Windows</h2>` | `<h2 ...>Durga for Windows</h2>` |
| 297 | `chat with Khoj from your desktop` | `chat with Durga from your desktop` |
| 303 | `<h2 ...>Khoj for Mac</h2>` | `<h2 ...>Durga for Mac</h2>` |
| 304 | `Native Mac app to sync documents and access Khoj from your menu bar.` | `Native Mac app to sync documents and access Durga from your menu bar.` |
| 313 | `<h2 ...>Khoj for Linux</h2>` | `<h2 ...>Durga for Linux</h2>` |
| 314 | `Run Khoj natively on your Linux desktop.` | `Run Durga natively on your Linux desktop.` |
| 323 | `<h2 ...>Khoj for Android</h2>` | `<h2 ...>Durga for Android</h2>` |
| 324 | `Take Khoj with you on your Android device.` | `Take Durga with you on your Android device.` |
| 428 | `<p class="footer-made">Made with ❤️ by Khoj</p>` | FLAG (Khoj attribution-adjacent — see REVIEW) |

The deprecation banner text on line 19-21 is FLAGGED — "Khoj Cloud" refers to the upstream Khoj-hosted SaaS specifically. A fork named Durga has no "Khoj Cloud" to deprecate. This banner may be removable entirely, or the wording may need substantive edits beyond find/replace. Listing in REVIEW so the human can decide.

Line 428 is also FLAGGED — `Made with ❤️ by Khoj` is borderline attribution. The `LICENSE` and `NOTICE`-style attribution must be preserved under AGPL, but a footer credit on a forked website is debatable.

### `README.md`
Top-level project README.

Edits applied:
- Line 1: alt text `"Khoj Logo"` → `"Durga Logo"`
- Line 13: `<b>Your AI second brain</b>` — left as-is (taglines are descriptive, not branded)
- Line 30: trendshift alt `"khoj-ai%2Fkhoj | Trendshift"` — left (badge URL data)
- Line 37: bullet referencing Pipali — left (third-party project)
- Line 38: `Read about Khoj's excellent performance...` → `Read about Durga's excellent performance...`
- Line 44: `[Khoj](https://khoj.dev) is a personal AI app...` → `[Durga](https://khoj.dev) is a personal AI app...`
- Line 53: `Khoj is open-source, self-hostable. Always.` → `Durga is open-source, self-hostable. Always.`
- Line 60: GIF alt — leave (image URL)
- Line 62: `Go to https://app.khoj.dev to see Khoj live.` → `Go to https://app.khoj.dev to see Durga live.`
- Line 69: `To get started with self-hosting Khoj, [read the docs](...)` → `To get started with self-hosting Durga, [read the docs](...)`
- Line 73: `Khoj is available as a cloud service ... Khoj Enterprise` → FLAG (line 73 mentions "Khoj Enterprise" and pricing page on khoj.dev; the fork doesn't offer Khoj Enterprise. Wording rewrite needed beyond find/replace — will rebrand the literal "Khoj" string but leave for human review of the `khoj.dev/teams` link semantics)
  - For this pass: `Khoj is available...` → `Durga is available...` and `learn more about Khoj Enterprise` → `learn more about Durga Enterprise`
- Line 77: `Q: Can I use Khoj without self-hosting?` → `Q: Can I use Durga without self-hosting?`
- Line 79: `You can use Khoj right away at...` → `You can use Durga right away at...`
- Line 81: `Q: What kinds of documents can Khoj read?` → `Q: What kinds of documents can Durga read?`
- Line 83: `Khoj supports a wide variety...` → `Durga supports a wide variety...`
- Line 87: `step-by-step guide to custom agents.` (the link mentions Khoj in URL slug — leave)
- Line 101: `Khoj is open source. It is sustained by...` → `Durga is open source. It is sustained by...`

GitHub URLs, badge URLs, and Discord/blog/asset URLs are preserved.

### `src/interface/web/app/layout.tsx`
Root metadata for the React app.

| Line | Before | After |
|------|--------|-------|
| 9 | `title: "Khoj AI - Ask Anything"` | `title: "Durga AI - Ask Anything"` |
| 11 | `"Khoj is a personal research assistant. ..."` | `"Durga is a personal research assistant. ..."` |
| 18 | keywords: `"... Khoj, open source, ..."` | `"... Durga, open source, ..."` |
| 20 | `siteName: "Khoj AI"` | `siteName: "Durga AI"` |
| 21 | `title: "Khoj AI"` | `title: "Durga AI"` |
| 23 | `"Khoj is a personal research assistant. ..."` | `"Durga is a personal research assistant. ..."` |

Asset URLs / icon paths preserved.

### `src/interface/web/app/agents/layout.tsx`

| Line | Before | After |
|------|--------|-------|
| 5 | `title: "Khoj AI - Agents"` | `title: "Durga AI - Agents"` |
| 13 | `siteName: "Khoj AI"` | `siteName: "Durga AI"` |
| 14 | `title: "Khoj AI - Agents"` | `title: "Durga AI - Agents"` |

### `src/interface/web/app/automations/layout.tsx`

| Line | Before | After |
|------|--------|-------|
| 7 | `title: "Khoj AI - Automations"` | `title: "Durga AI - Automations"` |
| 9 | `"Use Khoj Automations to get..."` | `"Use Durga Automations to get..."` |
| 15 | `siteName: "Khoj AI"` | `siteName: "Durga AI"` |
| 16 | `title: "Khoj AI - Automations"` | `title: "Durga AI - Automations"` |
| 18 | `"Use Khoj Automations to get..."` | `"Use Durga Automations to get..."` |

### `src/interface/web/app/chat/layout.tsx`

| Line | Before | After |
|------|--------|-------|
| 6 | `title: "Khoj AI - Chat"` | `title: "Durga AI - Chat"` |
| 14 | `siteName: "Khoj AI"` | `siteName: "Durga AI"` |
| 15 | `title: "Khoj AI - Chat"` | `title: "Durga AI - Chat"` |

### `src/interface/web/app/search/layout.tsx`

| Line | Before | After |
|------|--------|-------|
| 6 | `title: "Khoj AI - Search"` | `title: "Durga AI - Search"` |
| 8 | `"Find anything in documents you've shared with Khoj..."` | `"Find anything in documents you've shared with Durga..."` |
| 14 | `siteName: "Khoj AI"` | `siteName: "Durga AI"` |
| 15 | `title: "Khoj AI - Search"` | `title: "Durga AI - Search"` |

### `src/interface/web/app/settings/layout.tsx`

| Line | Before | After |
|------|--------|-------|
| 7 | `title: "Khoj AI - Settings"` | `title: "Durga AI - Settings"` |
| 8 | `"Configure Khoj to get personalized..."` | `"Configure Durga to get personalized..."` |
| 14 | `siteName: "Khoj AI"` | `siteName: "Durga AI"` |
| 15 | `title: "Khoj AI - Settings"` | `title: "Durga AI - Settings"` |
| 16 | `"Setup, configure, and personalize Khoj, ..."` | `"Setup, configure, and personalize Durga, ..."` |

### `src/interface/web/app/share/chat/layout.tsx`

| Line | Before | After |
|------|--------|-------|
| 5 | `title: "Khoj AI - Ask Anything"` | `title: "Durga AI - Ask Anything"` |
| 13 | `siteName: "Khoj AI"` | `siteName: "Durga AI"` |
| 14 | `title: "Khoj AI - Ask Anything"` | `title: "Durga AI - Ask Anything"` |

### `src/interface/web/app/page.tsx`
Home (chat landing) page.

| Line | Before | After |
|------|--------|-------|
| 460 | `?.name ?? "Khoj"}` (default agent display name) | `?.name ?? "Durga"}` |
| 485 | `{getIconFromIconName("Lightbulb", "orange")} Khoj` (default dropdown item) | `{getIconFromIconName("Lightbulb", "orange")} Durga` |
| 584 | `<title>Khoj AI - Your Second Brain</title>` | `<title>Durga AI - Your Second Brain</title>` |

`setSelectedAgent("khoj")`, `key="0-khoj"`, `useState<string | null>("khoj")` — these are agent-slug data values. Backend stores the default agent under slug `"khoj"`. Changing the slug breaks API calls to `/api/agents` and would need a database migration. NOT changed.

### `src/interface/web/app/chat/page.tsx`

| Line | Before | After |
|------|--------|-------|
| 201 | `const defaultTitle = "Khoj AI - Chat";` | `const defaultTitle = "Durga AI - Chat";` |

### `src/interface/web/app/share/chat/page.tsx`

| Line | Before | After |
|------|--------|-------|
| 157 | `useState("Khoj AI - Chat")` | `useState("Durga AI - Chat")` |

### `src/interface/web/app/settings/page.tsx`

| Line | Before | After |
|------|--------|-------|
| 247 | `Access Khoj from the` | `Access Durga from the` |
| 295 | `Set this API key in the Khoj apps you want to connect to this Khoj account` | `Set this API key in the Durga apps you want to connect to this Durga account` |
| 306 | `Apps using this API key will no longer connect to this Khoj account` | `Apps using this API key will no longer connect to this Durga account` |
| 711 | `"Khoj will learn and remember from your conversations."` | `"Durga will learn and remember from your conversations."` |
| 712 | `"Khoj will no longer learn or remember from your conversations."` | `"Durga will no longer learn or remember from your conversations."` |
| 782 | `\`Your ${source} integration to Khoj has been disconnected.\`` | `\`Your ${source} integration to Durga has been disconnected.\`` |
| 831 | `What should Khoj refer to you as?` | `What should Durga refer to you as?` |
| 868 | `day trial of the Khoj Futurist plan` | FLAG ("Khoj Futurist" is a Khoj-specific paid plan name — see REVIEW) |
| 1065 | `placeholder="Enter API Key of your Khoj integration on Notion"` | `placeholder="Enter API Key of your Durga integration on Notion"` |

`khoj-conversations.zip` (line 588) is a download filename and `khoj_cloud_subscription_url` (line 951) is an API field name — not changed.

### `src/interface/web/app/components/loginPrompt/loginPopup.tsx`

| Line | Before | After |
|------|--------|-------|
| 36 | `<CardHeader ...>Welcome to Khoj!</CardHeader>` | `<CardHeader ...>Welcome to Durga!</CardHeader>` |
| 38 | `Sign in to get started with Khoj, your AI research assistant.` | `Sign in to get started with Durga, your AI research assistant.` |

### `src/interface/web/app/components/loginPrompt/loginPrompt.tsx`

| Line | Before | After |
|------|--------|-------|
| 265 | `<div ...>Get started with Khoj</div>` | `<div ...>Get started with Durga</div>` |

### `src/interface/web/app/components/chatInputArea/chatInputArea.tsx`

| Line | Before | After |
|------|--------|-------|
| 186 | `"Hey there, you need to be signed in to send messages to Khoj AI"` | `"Hey there, you need to be signed in to send messages to Durga AI"` |

### `src/interface/web/app/components/chatHistory/chatHistory.tsx`

| Line | Before | After |
|------|--------|-------|
| 499 | `if (data.agent.is_hidden) return "Khoj";` (display name when agent hidden) | `if (data.agent.is_hidden) return "Durga";` |
| 568 | `<h1>{data?.slug || "Conversation with Khoj"}</h1>` | `<h1>{data?.slug || "Conversation with Durga"}</h1>` |

`by === "khoj"`, `chatMessage.by === "khoj"` — author identifier; NOT changed.

### `src/interface/web/app/components/agentCard/agentCard.tsx`

| Line | Before | After |
|------|--------|-------|
| 243 | `\`Khoj AI - Agent ${props.data.slug}\`` (browser history title) | `\`Durga AI - Agent ${props.data.slug}\`` |
| 344 | `\`Khoj AI - Agents\`` (browser history title) | `\`Durga AI - Agents\`` |

### `src/interface/web/app/components/profileCard/profileCard.tsx`

| Line | Before | After |
|------|--------|-------|
| 43 | `{description \|\| "A Khoj agent"}` | `{description \|\| "A Durga agent"}` |

### `src/interface/web/app/components/deprecationBanner.tsx`
This entire banner is FLAGGED. The deprecation messaging refers specifically to "Khoj Cloud" — the Khoj-Inc-hosted SaaS being shut down on April 15, 2026. A fork operating under Durga has no obligation to display this message at all, and the message is semantically incorrect for the fork.

| Line | Before | After |
|------|--------|-------|
| 8 | `const DISMISS_KEY = "khoj-cloud-deprecation-dismissed";` | NO CHANGE (localStorage key — changing breaks dismissal state for existing users) |
| 29 | `<strong>Khoj Cloud is being deprecated on April 15, 2026.</strong>` | NO CHANGE — see REVIEW |
| 34 | `To continue using Khoj, you can` | NO CHANGE — see REVIEW |

### `src/interface/web/app/automations/page.tsx`

| Line | Before | After |
|------|--------|-------|
| 841 | `<FormDescription>What do you want Khoj to do?</FormDescription>` | `<FormDescription>What do you want Durga to do?</FormDescription>` |

### `src/interface/web/app/search/page.tsx`

| Line | Before | After |
|------|--------|-------|
| 381 | `Add context for your Khoj knowledge base.` | `Add context for your Durga knowledge base.` |

### `src/interface/web/app/common/utils.ts`
Welcome console banner shown to anyone opening DevTools.

| Line | Before | After |
|------|--------|-------|
| 27-31 | ASCII art spelling "KHOJ AI" | NO CHANGE — see REVIEW (would need to redraw ASCII art for "DURGA AI") |
| 36 | `I am ✨Khoj✨, your open-source, personal AI copilot.` | `I am ✨Durga✨, your open-source, personal AI copilot.` |
| 38 | `See my source code at https://github.com/khoj-ai/khoj` | NO CHANGE (URL preserved per instructions) |
| 39 | `Read my operating manual at https://docs.khoj.dev` | NO CHANGE (URL preserved per instructions) |

The ASCII art is FLAGGED because regenerating "DURGA AI" art is a creative decision (spacing, font, etc.).

### `src/khoj/interface/web/assets/utils.js`
DevTools console banner shown to anyone opening the browser console on a server-rendered page (mirror of the React `utils.ts` welcomeConsole).

| Line | Before | After |
|------|--------|-------|
| 29 | `I am ✨Khoj✨, your open-source, personal AI copilot.` | `I am ✨Durga✨, your open-source, personal AI copilot.` |

ASCII art (lines 20-24) and source/manual URLs (lines 31-32) NOT changed (creative + URL preserved).

### `src/interface/web/public/khoj.webmanifest`
PWA manifest. Display name shown in OS install prompts.

| Line | Before | After |
|------|--------|-------|
| 3 | `"name": "Khoj AI - Get Answers, Create Anything"` | `"name": "Durga AI - Get Answers, Create Anything"` |
| 4 | `"short_name": "Khoj"` | `"short_name": "Durga"` |
| 8 | `"description": "Khoj is your open, personal AI..."` | `"description": "Durga is your open, personal AI..."` |

`"id"`, icon paths (`khoj_lantern_*.png`), and screenshot paths NOT changed (asset URLs / PWA install ID).

---

## REVIEW — borderline cases NOT auto-edited, flagged for human decision

These cases were flagged. Each has nuance the operator should resolve:

1. **`src/interface/web/app/components/deprecationBanner.tsx`** (whole component) — refers specifically to upstream Khoj Cloud SaaS shutdown on April 15, 2026. For a fork operating under Durga branding, this banner is at minimum misleading and probably should be deleted or repurposed entirely, not just rebranded. Decision: leave for human.

2. **`src/khoj/interface/web/home/index.html` lines 19-21** — same Khoj Cloud deprecation banner. Same reasoning.

3. **`src/khoj/interface/web/home/index.html` line 428** — `Made with ❤️ by Khoj`. This is a footer credit. AGPL attribution requires preserving authorship metadata; whether a footer credit qualifies is a judgment call. Leaving for human.

4. **`src/interface/web/app/settings/page.tsx` line 868** — `Khoj Futurist plan`. "Futurist" is a Khoj-specific paid tier (per pricing on khoj.dev). The fork may not offer this tier at all. Wording rewrite needed beyond rebrand.

5. **`src/interface/web/app/common/utils.ts` lines 27-31** — ASCII art spelling KHOJ AI. Regenerating ASCII art is a design choice. Leaving for human.

6. **`README.md` line 73** — references `Khoj Enterprise` and `khoj.dev/teams` URL. Mechanical Khoj→Durga string swap applied; the URL still points to Khoj's enterprise page, which doesn't make sense for Durga. Human should redirect or remove that paragraph.

7. **`team@khoj.dev` references throughout** (settings/page.tsx, automations/page.tsx, error.html, email.py, etc.) — Durga should arguably point users at a Durga support address instead of Khoj's. Left for human to decide once a Durga support address exists.

8. **`https://khoj.dev/#pricing`** in settings/page.tsx line 875 — pricing page URL. Same issue.

9. **All `documentation/docs/**/*.md*` files** — 269 occurrences across 40 files. Heavy URL/product cross-references (Khoj Cloud, blog.khoj.dev, github.com/khoj-ai/khoj, Khoj-specific UI screenshots). A mechanical Khoj→Durga sweep would create many semi-broken sentences. Recommend a separate, focused docs pass after the launch site is built. Listing out the most prominent ones for awareness:
   - `documentation/docs/get-started/setup.mdx` (54 occurrences)
   - `documentation/docs/contributing/development.mdx` (21)
   - `documentation/docs/clients/emacs.md` (16)
   - `documentation/docs/clients/obsidian.md` (16)
   - `documentation/docs/clients/desktop.md` (13)
   - `documentation/docs/advanced/ollama.mdx` (11)
   - `documentation/docs/features/chat.md` (9)
   - `documentation/docs/get-started/privacy-security.md` (9)
   - `documentation/docs/clients/whatsapp.md` (8)
   - `documentation/docs/advanced/use-openai-proxy.md` (8)
   - … plus 30 others
   - `documentation/README.md` itself

10. **`src/interface/desktop/*.html`** — Electron app UI titles. Per scope: "Frontend display names in `src/interface/web/`" — the desktop interface lives under `src/interface/desktop/`, not `src/interface/web/`. Out of explicit scope. FLAGGED. Files: `splash.html`, `shortcut.html`, `settings.html`, `about.html`, plus `utils.js` which sets the title bar HTML to "Khoj for Windows/macOS/Linux".

11. **`src/interface/obsidian/manifest.json`** — Obsidian plugin manifest with `"id": "khoj"`, `"name": "Khoj"`, `"author": "Khoj Inc."`. Changing the `id` breaks plugin identity for existing installs. Author attribution is preserved per AGPL. FLAGGED.

12. **`.github/workflows/build_khoj_el.yml`, `test_khoj_el.yml`** — workflow filenames and likely internal references. Not user-facing in the intended sense; would force CI breakage on rename. NOT TOUCHED.

13. **Emacs interface (`src/interface/emacs/`)** — not surveyed in detail in this pass; many user-facing strings likely. Recommend a separate pass if Emacs client is in scope.

14. **`src/khoj/database/adapters/__init__.py` and other Python source** — not surveyed. The instructions list only "src/khoj/routers/email.py" + email templates as in-scope Python files. Other Python source likely contains user-facing strings (error messages, prompts) but rebranding them risks affecting LLM behavior (e.g. Khoj-named system prompts) which is a separate decision.

---

## Summary

**Files modified by this pass:** 25

**Borderline cases flagged for review:** 14 categories (covering many files in `documentation/`, electron desktop interface, deprecation banner, Khoj-Cloud-specific text, Khoj-Futurist plan name, ASCII art, attribution footer, support email addresses, Khoj enterprise reference, Obsidian plugin id, Emacs interface, and other Python source)

**Compound identifiers explicitly preserved (matching pattern, NOT touched):**
- `khoj-ai`, `khoj.dev`, `assets.khoj.dev`, `app.khoj.dev`, `docs.khoj.dev`, `blog.khoj.dev`, `github.com/khoj-ai`, `twitter.com/khoj_ai`, `linkedin.com/company/khoj-ai`
- `KhojLogo`, `KhojLogoType`, `KhojSearchLogo`, `KhojAgentLogo`, `KhojAutomationLogo`, `KhojUser`
- `khoj_version`, `khoj_cloud_subscription_url`, `khoj-cloud-deprecation-dismissed`
- `KHOJ_DOMAIN`, `KHOJ_NO_HTTPS` (env vars)
- `khoj.webmanifest`, `khoj_lantern_*.png`, `khoj-logo-*.png`, `khoj_hero.png` (asset filenames)
- `~/.khoj/khoj.log` (default config path)
- `by === "khoj"`, `slug === "khoj"`, `agent.name === "khoj"` (data values)
- `div.khoj`, `div.khojChatMessage`, `.khoj-configure`, `.khoj-header`, `.khoj-nav`, etc. (CSS class names)
