# Security and Privacy in Durga

Durga is a sensitive personal AI assistant. The brand promise is **privacy-first, local-by-default, transparent about what data leaves the user's machine**. This document is the canonical statement of what that means in practice — what Durga collects, what crosses the network, what stays local, how multi-user isolation works, and how to opt into the things that are off by default.

This document describes the **Durga fork** of khoj-ai/khoj. Where Durga's defaults diverge from upstream Khoj, that divergence is called out explicitly.

---

## TL;DR

- **Telemetry**: OFF by default. Opt-in via `DURGA_TELEMETRY_ENABLE=true` AND a configured `DURGA_TELEMETRY_SERVER` URL. Both are required; either alone is a no-op.
- **Auto-update of the desktop client**: OFF by default. Opt-in via `DURGA_AUTOUPDATE=1`.
- **Default desktop / Obsidian server URL**: `http://127.0.0.1:42110` (local-only). Override via in-app settings or `DURGA_SERVER_URL`. Upstream Khoj defaults to `https://app.khoj.dev` (a third-party hosted service); Durga does not.
- **LLM API calls**: leave the machine if and only if the user configures a remote LLM provider. Local providers (Ollama, llama.cpp, LM Studio) do not leave the machine.
- **File index, embeddings, conversation history, voice audio**: stay on the user's machine.
- **No analytics SDKs are bundled** in any client (web, desktop, Obsidian, Emacs). No PostHog, Sentry, Mixpanel, Amplitude, Segment, or similar.

---

## Data flow inventory

### 1. What Durga collects on disk (local only)

All of this lives on the machine running the Durga server. None of it is uploaded anywhere by Durga itself.

| Item | Location | Notes |
|------|----------|-------|
| User accounts (`KhojUser`) | PostgreSQL (or embedded `pgserver`) | email, hashed password, phone (if Twilio configured), OAuth ids |
| Indexed documents (`Entry`) | PostgreSQL | raw text + embeddings of every file Durga has indexed for the user |
| Full file text (`FileObject`) | PostgreSQL | full source text of indexed files |
| Conversations (`Conversation`) | PostgreSQL | full chat history per user, JSON-encoded |
| Long-term memory (`UserMemory`) | PostgreSQL | summaries derived from conversations |
| API keys (`KhojApiUser`) | PostgreSQL | per-user API keys for connecting clients |
| Server-side state (`ProcessLock`, `RateLimitRecord`, etc.) | PostgreSQL | operational only |
| Voice audio | Memory | streamed to Whisper for transcription, not persisted; transcribed text lives in `Conversation` like any other message |
| Server identifier | `~/.khoj/env` | random UUID generated on first run; only used as a telemetry primary key, which is itself off |

### 2. What leaves the machine (only when the user configures it)

These are all **opt-in by environment variable or explicit configuration**. With a fresh self-hosted Durga and no env vars set, none of the following endpoints are contacted.

| Endpoint | When | Triggering config |
|----------|------|-------------------|
| OpenAI (`api.openai.com`) | Chat completion, embeddings, TTS, STT — only if user picks an OpenAI model | `OPENAI_API_KEY` and a configured OpenAI chat model |
| Anthropic (`api.anthropic.com`) | Chat completion — only if user picks a Claude model | `ANTHROPIC_API_KEY` and a configured Claude chat model |
| Google Gemini (`generativelanguage.googleapis.com`) | Chat completion — only if user picks a Gemini model | `GEMINI_API_KEY` and a configured Gemini chat model |
| OpenAI-compatible providers (Ollama, LM Studio, llama.cpp, vLLM, LiteLLM, Groq, Together, etc.) | Chat completion — only if user picks one of these models | Endpoint URL + key configured per `AiModelApi`. Local (loopback) endpoints stay on-machine. |
| Serper.dev (`google.serper.dev`) | Web search — only if `/online` command is used | `SERPER_DEV_API_KEY` |
| Jina Reader (`r.jina.ai`) | Web page reading — only if `/online` is used and Firecrawl/Olostep aren't configured | (free tier; `JINA_API_KEY` optional) |
| Firecrawl (`api.firecrawl.dev` or self-hosted) | Web page reading | `FIRECRAWL_API_KEY` and/or `FIRECRAWL_API_URL` |
| Exa, Olostep | Web search/scraping | `EXA_API_KEY`, `OLOSTEP_API_KEY` |
| Resend (`api.resend.com`) | Sending magic-link / welcome / task notification email | `RESEND_API_KEY`. With no Resend key, Durga falls back to Google OAuth or runs in single-user `--anonymous-mode` and does not send email. |
| Stripe (`api.stripe.com`) | Subscription billing webhook (only relevant if running a hosted Durga for paying users) | `STRIPE_API_KEY` + `STRIPE_SIGNING_SECRET` + `KHOJ_CLOUD_SUBSCRIPTION_URL` |
| AWS S3 | Image upload (generated images, user-attached images) | `AWS_ACCESS_KEY` + `AWS_SECRET_KEY`. Without these, generated/attached images are returned inline as base64 data URIs and never leave the machine. |
| Twilio (`api.twilio.com`) | WhatsApp / SMS channel | `TWILIO_AUTH_TOKEN` + `TWILIO_ACCOUNT_SID` |
| Notion (`api.notion.com`) | Indexing the user's Notion workspace | per-user OAuth token, configured by the user via `/settings` |
| GitHub (`api.github.com`) | Indexing the user's repo | per-user PAT, configured by the user via `/settings` |
| Google OAuth (`accounts.google.com`) | Sign-in with Google | `GOOGLE_CLIENT_ID` + `GOOGLE_CLIENT_SECRET` |
| Google Calendar / Drive / Vertex | Per-feature integrations | per-feature OAuth / API keys |

If you do not set any of the above, the only network traffic leaving Durga's machine is the localhost HTTP between the browser/Obsidian/desktop client and the Durga server.

### 3. What is OFF by default in Durga (and was ON in upstream Khoj)

This is the heart of Durga's privacy posture vs. upstream.

| Default | Upstream Khoj | Durga | How to opt in |
|---------|--------------|-------|---------------|
| Usage telemetry upload | Enabled. Sends `server_id`, OS, API endpoint hit, client name, server version every ~2 minutes to `https://khoj.beta.haletic.com/v1/telemetry`. Disable required `KHOJ_TELEMETRY_DISABLE=true`. | Disabled. No endpoint set. Even with telemetry enabled, no upload happens unless a server URL is configured. | Set BOTH `DURGA_TELEMETRY_ENABLE=true` and `DURGA_TELEMETRY_SERVER=https://your-receiver/v1/telemetry`. |
| Desktop app auto-update | Enabled. ToDesktop runtime initialized at boot; checks ToDesktop infrastructure for updates on every launch. | Disabled. ToDesktop runtime is not initialized; no update check is made. | Set `DURGA_AUTOUPDATE=1` before launching the desktop app. |
| Desktop default server URL | `https://app.khoj.dev` (Khoj's hosted SaaS — your indexed files would be uploaded there). | `http://127.0.0.1:42110` (local). | Open the desktop app's host setting and point at your server URL, or set `DURGA_SERVER_URL` before launching. |
| Obsidian default server URL | `https://app.khoj.dev`. | `http://127.0.0.1:42110`. | Change `khojUrl` in plugin settings. |

### 4. What ALWAYS stays on the machine

| Item | Notes |
|------|-------|
| File index (raw text + embeddings) | `Entry` rows in PostgreSQL. Never POSTed anywhere by Durga. (LLM prompts include retrieved snippets — see "LLM context note" below.) |
| Conversation history | `Conversation.conversation_log` JSON. Never uploaded by Durga. |
| Long-term memory summaries | `UserMemory`. Local. |
| Voice audio | Buffered in memory, transcribed by Whisper (locally if using the bundled model; via OpenAI if you configured OpenAI as your STT provider), discarded after transcription. The transcribed *text* is treated like any other message. |
| Server identifier | Was used as the telemetry primary key. Now unused unless telemetry is opted in. Stays in `~/.khoj/env` either way. |

### 5. LLM context note (important)

When a chat message is sent to a remote LLM provider (OpenAI, Anthropic, Gemini, etc.):

- **The user's message text** is sent.
- **Retrieved snippets** from the user's indexed documents — chosen by the local RAG step — are included in the prompt.
- **Recent conversation history** is included.
- **System prompt + agent personality** are included.

This is the unavoidable shape of RAG against a hosted LLM. If you do not want any document content to leave the machine, configure a **local** chat model (Ollama, llama.cpp, LM Studio). Durga uses the same OpenAI-compatible client for both, so the only thing that changes is the endpoint URL.

---

## Multi-user data isolation

Durga inherits Khoj's multi-tenant model. Every persistent record is owned by a `KhojUser` (the `AUTH_USER_MODEL`), and most queries filter by user. This section is the audit summary, not a marketing claim.

### Model-level FK to KhojUser

These tables have a direct ForeignKey or OneToOne to `KhojUser` (verified in `src/khoj/database/models/__init__.py`):

- `GoogleUser` (OneToOne)
- `KhojApiUser` (FK)
- `Subscription` (OneToOne)
- `NotionConfig`, `GithubConfig` (FK)
- `UserConversationConfig`, `UserVoiceModelConfig`, `UserTextToImageModelConfig` (OneToOne)
- `Conversation` (FK, `on_delete=CASCADE`)
- `PublicConversation` (FK as `source_owner` — public by design)
- `ReflectiveQuestion` (FK, nullable)
- `FileObject` (FK, nullable — see below)
- `Entry` (FK, nullable — see below)
- `UserRequests` (FK)
- `DataStore` (FK as `owner`, nullable)
- `UserMemory` (FK)
- `Agent` (FK as `creator`, nullable for admin-managed agents)

### Tables NOT directly user-owned (intentional)

These exist for cross-user or operational reasons, not user data:

- `ChatModel`, `AiModelApi`, `VoiceModelOption`, `SearchModelConfig`, `SpeechToTextModelOptions`, `TextToImageModelConfig`, `ServerChatSettings`, `WebScraper` — server-wide model configuration. Admin-managed.
- `ProcessLock`, `RateLimitRecord` — operational.
- `EntryDates` — joined to `Entry` (which is user-scoped).
- `McpServer` — server-wide MCP server registry. Note: there is no per-user MCP server scoping today; all configured MCP servers are visible to all users on the same Durga server. For a single-user deployment this is fine. For a multi-tenant deployment, do not register an MCP server that contains tenant-specific secrets.

### Nullable user FKs

`Entry.user`, `FileObject.user`, `DataStore.owner`, `Agent.creator`, and `ReflectiveQuestion.user` allow `NULL`. This is intentional:

- **`Entry` and `FileObject`** can be associated with an `Agent` instead of a user (knowledge base for an agent, e.g., the default Khoj agent). The `Entry.save()` validator enforces that an entry has either a user or an agent, not both. Search filtering uses `Q(user=user) | Q(agent=agent)`, where `agent` is only set when an agent context applies.
- **`Agent.creator=NULL`** means an admin-managed (default) agent. The `Agent.save()` method auto-sets `managed_by_admin=True` when there's no creator.
- **`DataStore.owner=NULL`** means a server-level key/value pair. The `private` flag on `DataStore` further controls visibility.

### Query-level enforcement

Spot-checked `src/khoj/database/adapters/__init__.py`. The pattern for user-owned data is consistent:

- `Conversation`: `aget_conversation_by_user`, `acreate_conversation_session`, `adelete_conversation_by_user`, `aset_conversation_title` — all filter by `user=user`.
- `Entry`: `apply_filters` and `search_with_embeddings` use `Q(user=user) | Q(agent=agent)`. Without a user or agent passed in, returns `Entry.objects.none()`.
- `FileObject`: every accessor (`get`, `aget`, `delete`, `bulk_delete`, list) filters by `user=user`.
- `UserMemory`: filters by `user=user` and optionally `agent=agent`.
- `Agent`: privacy-level enforced via `Q(privacy_level=PUBLIC) | Q(privacy_level=PROTECTED) | Q(creator=user)` — public agents are intentionally visible to everyone; protected and private require ownership.

### Cross-tenant lookups Durga has tightened

One leak vector existed in upstream Khoj that Durga has fixed:

- `ConversationAdapters.get_conversation_by_id(conversation_id)` does **not** filter by user. Two upstream callers exist:
  - `routers/helpers.py:search_documents` — used the unscoped lookup to fetch `conversation.file_filters` for biasing the user's RAG search. A malicious `conversation_id` from another tenant would have read another user's file-filter list.
  - `routers/helpers.py:run_query_at_scheduled_time` — used the unscoped lookup to validate that a scheduled job's conversation still exists. A crafted job could have probed for the existence of arbitrary conversation IDs.

  Both call sites have been changed in Durga to use `aget_conversation_by_user` / `get_conversation_by_user`, which scope by the requesting user. The unscoped helper is left in place for upstream-merge compatibility but has no remaining call sites in user-facing code paths.

### Authentication and authorization

- `UserAuthenticationBackend` (in `khoj/configure.py`) attaches the authenticated `KhojUser` to every request via `request.user`.
- Most adapter methods that touch user data use the `@require_valid_user` / `@arequire_valid_user` decorator, which raises if `user` is missing.
- API key auth (`KhojApiUser`) is per-user; the key authenticates as its owning user.
- Anonymous mode (`--anonymous-mode`) creates one default user; do not enable on a multi-user deployment.

---

## Defaults and how to opt in

| Feature | Default | Opt-in |
|---------|---------|--------|
| Telemetry | OFF | `DURGA_TELEMETRY_ENABLE=true` AND `DURGA_TELEMETRY_SERVER=<url>` |
| Auto-update (desktop) | OFF | `DURGA_AUTOUPDATE=1` |
| Web search (Serper) | OFF | `SERPER_DEV_API_KEY=<key>` |
| Web scraping (Firecrawl) | OFF | `FIRECRAWL_API_KEY=<key>` |
| Email (Resend) | OFF | `RESEND_API_KEY=<key>` |
| Image upload to S3 | OFF | `AWS_ACCESS_KEY` + `AWS_SECRET_KEY` + bucket env vars |
| Subscription / billing (Stripe) | OFF | `STRIPE_API_KEY` + `STRIPE_SIGNING_SECRET` + `KHOJ_CLOUD_SUBSCRIPTION_URL` |
| WhatsApp / SMS (Twilio) | OFF | `TWILIO_AUTH_TOKEN` + `TWILIO_ACCOUNT_SID` |
| Google sign-in | OFF | `GOOGLE_CLIENT_ID` + `GOOGLE_CLIENT_SECRET` |
| Notion / GitHub / Google integrations | OFF (per-user, in-app) | User adds via `/settings` |
| Anonymous (single-user, no login) mode | OFF | `--anonymous-mode` CLI flag |

Legacy upstream env vars are still honored for compatibility:
- `KHOJ_TELEMETRY_ENABLE` is treated the same as `DURGA_TELEMETRY_ENABLE`.
- `KHOJ_TELEMETRY_DISABLE` still forces telemetry off (redundant under Durga, still safe to set).
- `KHOJ_TELEMETRY_SERVER` is treated the same as `DURGA_TELEMETRY_SERVER`.
- `KHOJ_AUTOUPDATE` is treated the same as `DURGA_AUTOUPDATE`.
- `KHOJ_URL` is treated the same as `DURGA_SERVER_URL`.

---

## Reporting a vulnerability

Durga is a fork. If the issue is in code that Durga inherited unchanged from upstream Khoj, please report it to both:

- Durga: open a private security advisory at `github.com/kaylacar/durga` (or email Tech Enrichment).
- Upstream: `team@khoj.dev`.

If the issue is specific to Durga's changes (the files listed under "Per-file changes" in the audit), report only to Durga.

---

## What to verify before exposing Durga to the public internet

This list is non-exhaustive — operational hardening is the deployer's responsibility.

- Set `KHOJ_DJANGO_SECRET_KEY` to a strong random value.
- Set `KHOJ_DOMAIN` to your actual domain (not `khoj.dev`, the default).
- Run behind HTTPS. Do not set `KHOJ_NO_HTTPS=true` in production.
- Use a managed PostgreSQL with backups, not the embedded `pgserver`.
- Restrict admin panel access (`/admin`) at the network layer.
- Decide whether you want public agents at all — if not, set every agent to `PrivacyLevel.PRIVATE`.
- Audit your configured LLM providers; remember that prompt content (including retrieved document snippets) is sent to whichever provider you pick.
