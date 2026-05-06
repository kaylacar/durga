# Durga — positioning (internal)

Working brand doc for Durga. Not the public README. This is the file we look at when somebody asks "wait, what's the pitch."

Owner: Kayla Cardillo / Tech Enrichment.

---

## Tagline candidates

In order of preference, with why:

1. **"A personal AI assistant that declares what she does."**
   Plain, true, and the differentiator is right in the line. "Declares" is the load-bearing word — it ties Durga to the agents.txt / ai.txt thesis without saying "governance" out loud. Ten words.

2. **"Self-hosted personal AI. Sensitive by default. Receipts on every call."**
   Three short claims. Each is verifiable in the code. Best for technical audiences (HN, GitHub) where people are tired of marketing copy.

3. **"The personal AI you can read the source of — and the receipts."**
   Punchier, slightly less honest. "Read the receipts" is doing real work — it points at RER without naming it. Risk: people who don't know the receipts exist will read this as a generic open-source brag.

4. **"Your AI sidekick. Local. Declared. Auditable."**
   Three-word rhythm, pulls "sidekick" out of Kayla's actual use case. Useful for the brand site, weaker for a repo header.

**Recommendation:** lead with #1 in the README. Keep #2 in reserve for HN/launch copy where the audience knows what those words mean. #3 and #4 belong on machinesrule.com, not in the repo.

---

## The pitch

Durga is a self-hosted personal AI assistant. She is a fork of Khoj — the same indexer, the same file watcher, the same chat surface — with an additional layer that makes her behavior legible. Each instance serves an `agents.txt` and an `ai.txt`, declaring the capabilities and policies the operator has chosen. Each chat turn produces a hash-chained receipt of what was read, what was sent, and what came back. Tool calls are gated by agentpreflight before they execute. Files marked sensitive are redacted or summarized locally before they ever reach a model. The defaults are local-only, no telemetry, no cloud. There is no Durga Cloud — the only Durga is the one you run.

---

## Differentiator

Most personal AI projects compete on either capability ("our agent is smarter") or privacy ("we don't see your data"). Both are real axes. Durga competes on a third one: **legibility**. You can answer the question "what did the assistant just do" without trusting anybody's marketing.

| Other personal AI                        | Durga                                                |
|------------------------------------------|------------------------------------------------------|
| Closed runtime, opaque execution         | Hash-chained receipts of every call, verifiable offline |
| Privacy promise (you trust the vendor)   | Local-only defaults you can read in the code         |
| Capability declared in marketing copy    | Capability declared in `/.well-known/agents.txt`     |
| Tool calls run, then are logged          | Tool calls validated by agentpreflight before they run |
| Sensitive content sent to the model      | Sensitive-tagged files summarized/redacted locally first |
| One mode: trust us                       | One mode: own it                                     |

The frame is not "Durga is better than X." The frame is "Durga is the version of this where you actually know what's happening." Some people don't want that. Fine. The ones who do, didn't have a clean answer before.

---

## The two doors angle

Tech Enrichment's broader thesis is that the internet now has two audiences — humans and agents — and most surfaces are only built for one. Sites publish HTML for humans and let agents guess. Tools publish UIs for humans and let agents reverse-engineer the affordances. Meaning degrades every time it crosses an interpretive layer that wasn't built for the reader on the other side.

Durga is the small version of that argument, applied to a personal AI assistant. She has two doors. One is the chat interface and the desktop client — the human door, inherited from Khoj. The other is the declared agent surface — `agents.txt` exposes what she can do, `ai.txt` exposes the policy under which she does it, and the RER receipts expose what actually happened. Both doors are explicit. Neither one has to guess.

This is why Durga is built on the Tech Enrichment standards rather than just citing them. The thesis is "explicit declaration at every interpretive layer." A personal AI assistant that doesn't declare its own behavior is making the same mistake Tech Enrichment is trying to fix on the rest of the web. Durga is, deliberately, the dogfood.

---

## Voice / persona

Two layers to keep separate:

**The product's voice — how Durga writes (READMEs, docs, error messages, UI copy):**

- Short sentences. Declarative. No qualifiers we don't mean.
- No marketing words: "powerful," "seamless," "revolutionary," "next-generation," "blazing-fast." If a line still works after you delete the adjective, the adjective was lying.
- No emoji in body copy. (The Khoj-inherited UI keeps a few; we don't add new ones.)
- We name things plainly. "Receipt," not "verifiable execution artifact." "Tagged sensitive," not "compliance-classified."
- We attribute. Khoj built the runtime. We built the layer on top. Saying so is honest and it's also strategically right — it tells engineers what they're getting.
- Negative space is fine. If a section doesn't have content yet, it doesn't get written. We do not pad.

**Durga's voice — how the assistant talks back to the operator:**

- Grounded. Not chirpy, not theatrical, not "I'm an AI assistant!"
- Calls the operator by their name, not "user."
- When she doesn't know, she says so. When the receipt says she read three files, she says she read three files.
- On camera (the single-operator use case): brief, finishable answers. The operator is filming. Durga finishes a thought in one breath, not a paragraph.
- No moralizing. If a request can be served, serve it. Sensitivity tags handle the actual data hygiene; the personality doesn't lecture.

---

## What Durga is not

State this plainly so we don't drift:

- Not a SaaS. There is no Durga Cloud and there isn't going to be.
- Not a Khoj competitor in the "we're better" sense. Khoj is upstream; we use their work and we say so.
- Not a general productivity tool. The pitch is specifically the *governed, declared, transparent* angle. People who don't care about that should run Khoj or ChatGPT.
- Not vendor-locked. Codex, OpenAI, Anthropic, Gemini, Ollama, llama.cpp — all supported via the same provider abstraction.
- Not a from-scratch project. We are honest that the heavy lifting is Khoj's. Our value is the layer.
- Not the place for Tech Enrichment's full standards story. That lives on machinesrule.com and machinepolicy.org. The Durga repo links there; it doesn't recap the whole thesis.

---

## Audience map

- **Repo README** — engineers evaluating the project. Lead with what it is, how to run it, what makes it different. Honest about the fork.
- **machinesrule.com** — humans encountering the brand. Lead with "two doors." Durga is one of the proof points, not the headline.
- **HN / launch posts** — technical audience tired of pitches. Lead with the receipt and the declaration. Show the `agents.txt` route. Show a RER receipt. Let them argue.
- **Client conversations** — people considering running Durga for a team. Lead with sensitive defaults and per-user isolation, then governance.

Same product. Different door.
