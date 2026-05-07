# Durga

A self-hosted, sensitive-by-default personal AI assistant that declares what she does.

<!-- CI/build badges intentionally omitted while Durga's own CI is being set up.
     Re-add here once kaylacar/durga has its own pipelines. -->

***

## What Durga is

Durga is a personal AI assistant you run yourself. She watches the files you point her at, answers questions over them, and talks back when called. The codebase is a fork of [khoj-ai/khoj](https://github.com/khoj-ai/khoj), kept under AGPL-3.0, with the Khoj team's runtime preserved underneath. The Durga layer on top is the part that makes her different: explicit declaration of behavior, a transparent execution trail, and defaults that minimize what leaves the machine she runs on.

She has two intended use cases:

- **Single-operator.** A live, voice-driven sidekick. Push to talk, hear an answer, keep working. Built around the way the owner actually uses an assistant on camera.
- **Self-hosted multi-user.** A personal AI a small team or client can run on their own infrastructure, with isolated per-user data and no required cloud.

There is no Durga Cloud. There is no hosted SaaS. The only Durga is the one you run.

***

## Why she's different

Most personal AI assistants are opaque. You ask, something happens, an answer comes back, and you have no auditable record of what was read, what was sent to a model, or what the model decided.

Durga is a reference implementation of [Tech Enrichment](https://techenrichment.com)'s declaration stack. Specifically:

- **Declared behavior.** Each Durga instance serves [`/.well-known/agents.txt`](https://github.com/kaylacar/agents-txt) and [`/.well-known/ai.txt`](https://github.com/kaylacar/ai-txt). The capabilities Durga exposes, the rate limits she enforces, the training/data policy she runs under — all published in the format other agents and operators can read.
- **Transparent execution.** Every chat turn produces a [RER](https://github.com/kaylacar/rer)-style receipt: what she read, which model she called, how many tokens she used, what she returned. Hash-chained, verifiable offline.
- **Pre-flight gating.** Tool calls run through [agentpreflight](https://github.com/kaylacar/agentpreflight) before they execute. Filesystem, network, secrets, and scope rules fire before a bad call leaves the agent.
- **Owner-controlled data.** The defaults are local-only. No telemetry, no analytics, no cloud sync, no calls home. Anything outbound is opt-in and explicit.
- **Sensitivity tags.** Files in your workspace can be marked sensitive (`# durga: sensitive` frontmatter). Tagged files are summarized or redacted locally before any prompt is built — they are never shipped to the LLM as raw text.

If you want a personal AI that you can point at and say "show me what you actually did," Durga is the project for that.

***

## Quick start

Durga ships as a Docker Compose stack, the same way Khoj does upstream. The default Compose path builds Durga from this checkout so the quickstart exercises Durga code, not the upstream Khoj image.

```bash
git clone https://github.com/kaylacar/durga.git
cd durga
docker compose up --build
```

Then open `http://localhost:42110`.

The default configuration is anonymous, single-user, local-only, with telemetry disabled. Configure model providers and storage via the environment variables in `docker-compose.yml`; outbound model or search calls should be explicit opt-ins.

For the original installation flow inherited from Khoj, see the [upstream setup docs](https://docs.khoj.dev/get-started/setup). Most of it still applies — replace product names accordingly. Durga's own docs will live in `documentation/` once the rebrand pass lands.

***

## Architecture

```
┌─────────────┐   ┌──────────┐   ┌──────────┐
│ web / desk  │ → │  server  │ → │    db    │
│  client     │   │ (FastAPI)│   │ (pg + pgvector) │
└─────────────┘   └────┬─────┘   └──────────┘
                       │
                  ┌────┴─────┐
                  │  proxy   │   codex CLI / OpenAI / Anthropic /
                  │ (LLMs)   │   Ollama / llama.cpp / Gemini
                  └──────────┘
```

- **server** — Python / FastAPI. Inherits Khoj's indexer, search, and chat orchestration. Adds the Durga governance layer (agents.txt route, ai.txt route, RER receipts, preflight hooks, sensitivity-tag handling).
- **web** — Next.js client. Inherits Khoj's UI; rebranded surface and additional governance views.
- **db** — Postgres + pgvector for indexed content and conversation history.
- **proxy** — model provider abstraction. Talks to local (Ollama, llama.cpp) or hosted (OpenAI, Anthropic, Gemini, codex) backends.
- **sandbox / search** — optional Khoj subsystems (Terrarium for code execution, SearxNG for web search). Off by default.

***

## Sensitive defaults

These are the promises Durga makes when you run her with the shipped config:

- **Local only.** Telemetry off. Analytics off. No cloud sync. No calls home.
- **Outbound is opt-in.** Each provider key (OpenAI, Anthropic, Gemini, Serper, etc.) is a separate, explicit environment variable. Unset means no calls.
- **Sensitivity tags are honored.** Files marked `# durga: sensitive` are summarized or redacted locally before any prompt is built. The raw text never reaches the model.
- **Receipts on.** Every chat turn writes a RER-style receipt to disk. You can read it. You can verify it without Durga running.
- **Per-user isolation.** When run multi-user, indexed content is isolated per user account. (Khoj's multi-user mode is being audited for Durga's stricter assumptions; treat as `verify before relying on` until the audit lands.)

What still leaves the machine when Durga is running, if you've configured it:

- The prompts and context you send to the LLM provider you chose. Providers see what you ask. That's the model call.
- Web search queries, if web search is enabled and configured.
- Anything the embedded sandbox or web fetcher reaches out to, if those features are enabled.

If you don't configure those, none of it leaves.

***

## Roadmap

See [`DURGA_PLAN.md`](./DURGA_PLAN.md) for the full plan. Short version:

- **Voice that works on camera.** Push-to-talk, low-latency TTS (Edge Neural or OpenAI), Whisper-large-v3 STT, output routed to OS audio so OBS can capture it.
- **The governance layer.** `agents.txt` and `ai.txt` routes, RER receipts on every turn, agentpreflight on every tool call, sensitivity tags as a first-class concept.
- **Multi-tenant audit.** Verify Khoj's per-user isolation, strip remaining telemetry surface, document exactly what data leaves the machine in each configuration.
- **On-camera UX.** Floating transcript, mid-reply interrupt, "pull up the spec" quick-reference mode.

Durga is going to diverge from Khoj over time. The goal is not to track every upstream feature — it is to keep a clean fork point so security and bug fixes can still be pulled from `khoj-ai/khoj` while the Durga layer evolves on its own.

***

## Built on khoj-ai/khoj

Durga is a fork of [khoj-ai/khoj](https://github.com/khoj-ai/khoj), distributed under the GNU Affero General Public License v3.0 (AGPL-3.0).

The original work — the file watcher, the indexer, the chat orchestration, the multi-client architecture, the Obsidian / Emacs / desktop integrations, and a great deal more — is the work of the Khoj team and contributors. Durga is honestly a wrapper-and-additions on top of a substantial open-source project. Credit where it's due.

If you want vanilla Khoj or hosted Khoj Cloud, go to [khoj.dev](https://khoj.dev). They are not the same product as Durga and should not be confused.

Full attribution and copyright in [`NOTICE.md`](./NOTICE.md). License in [`LICENSE`](./LICENSE).

***

## Contact

Kayla Cardillo / Tech Enrichment — `contactkaylacard@gmail.com`

Project: [github.com/kaylacar/durga](https://github.com/kaylacar/durga) (forked from [khoj-ai/khoj](https://github.com/khoj-ai/khoj))

Tech Enrichment: [techenrichment.com](https://techenrichment.com) · Brand: [machinesrule.com](https://machinesrule.com) · Standards: [machinepolicy.org](https://machinepolicy.org)
