**English** · [繁體中文](README.zh-TW.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

# Loop Engineering — a skill for designing & reviewing autonomous agent loops

![Loop Engineering — design & review the loop an agent runs on its own: trigger, check, act, verify, with success/failure/budget exits and a human gate](assets/hero.png)

Loop engineering is the discipline that comes after prompt engineering. A prompt
optimizes a single interaction; a **loop** optimizes the autonomous behavior that
surrounds it — *when* an agent runs, *what* triggers it, *how* it verifies its own
work, *when* it stops, and *when* it hands back to a human.

This skill gives a coding agent a battle-tested framework for two jobs:

- **Design mode** — build a new self-running agent / loop / background worker.
- **Review mode** — audit an existing loop's stopping conditions, guardrails,
  verification, and escalation paths.

It distills 12 sources (Anthropic's context-engineering guidance, the Ralph loop /
RPI methodology, Claude Code's agent-loop docs, and the 2026 "loop engineering"
writing) into seven load-bearing principles plus reference material.

**Quick start (Claude Code):**

```bash
git clone https://github.com/maxmilian/loop-engineering ~/.claude/skills/loop-engineering
```

Start a new session — that's it. (Other tools: [Install](#install).)

> In benchmark testing against a no-skill baseline on deliberately tricky cases,
> the skill raised the pass rate from 87% → 100% while producing more consistent,
> cheaper answers — its edge shows up on the subtle failure modes a strong model
> otherwise misses (cron stale-prompt drift, blind-retry waste, missing
> human-gates on irreversible actions). [Reproduce it →](#reproduce-the-benchmark)
>
> On a **weaker model (Haiku class)** the lift is far larger — **+16 points**
> (74% → 90% on an 8-case subset) — which is exactly where a coverage guarantee
> matters most.

## The seven principles (TL;DR)

1. **Leverage moved from the prompt to the loop** — design the control flow, not one mega-prompt.
2. **"Done" must be machine-checkable** — `tests pass` ✓, `improve the code` ✗.
3. **Verify with deterministic tools, never the agent's self-report.**
4. **Define all exits before going live** — success / failure / budget exits, no-progress detection, escalation path.
5. **Treat context as a finite resource** — trim tool outputs; use compaction, note-taking, sub-agents.
6. **Use the filesystem as memory; start each cycle with fresh context.**
7. **The hard part is verification, stopping, and escalation — not autonomy.** Prefer *semi-autonomous*: gate irreversible/outward actions behind a human.

## What's in here

```
loop-engineering/
├── SKILL.md                          # the skill itself (frontmatter + instructions)
├── references/
│   ├── loop-patterns.md              # heartbeat / cron / hook / goal + Ralph loop
│   ├── context-engineering.md        # compaction, note-taking, sub-agents, JIT retrieval
│   ├── review-checklist.md           # per-principle diagnostic, severity-ordered
│   └── sources.md                    # the 12 source articles, with one-line summaries
├── evals/                            # validation case library + benchmark evidence
│   ├── evals.json                    # 11 graded design / review / diagnose cases
│   ├── RESULTS.md                    # with-skill vs no-skill results, 3 iterations
│   └── files/                        # input scripts the review cases point at
└── assets/                           # README hero image
```

A skill is just a folder with a `SKILL.md` (YAML frontmatter + Markdown). That
portability is why it installs almost anywhere.

## Install

### Claude Code
Personal (all projects) or project-scoped — copy the folder into a `skills/` dir:

```bash
# personal
git clone https://github.com/maxmilian/loop-engineering ~/.claude/skills/loop-engineering
# or project-scoped
git clone https://github.com/maxmilian/loop-engineering .claude/skills/loop-engineering
```

Start a new session; Claude auto-discovers it from the `description` and invokes it
when you design or review an agent loop. (Prefer a prebuilt bundle? Download
`loop-engineering.skill` from the [latest release](https://github.com/maxmilian/loop-engineering/releases/latest)
and install it via your plugin/skill manager.)

### Codex
Codex loads skills natively from its skills directory. Drop the folder in:

```bash
git clone https://github.com/maxmilian/loop-engineering ~/.codex/skills/loop-engineering
```

If your Codex setup keys off `AGENTS.md` instead, add a pointer line such as:
`For designing or reviewing autonomous agent loops, follow skills/loop-engineering/SKILL.md.`

### GitHub Copilot CLI
Copilot auto-discovers skills from installed plugins. Place the folder under your
Copilot skills/plugins directory (e.g. `~/.copilot/skills/loop-engineering`) and
restart the CLI.

### Gemini CLI
Gemini activates skills via its skill mechanism. Put the folder in your Gemini
skills directory (e.g. `~/.gemini/skills/loop-engineering`); Gemini loads the
metadata at session start and activates the full content on demand. If you drive
Gemini through `GEMINI.md`, add a pointer line to `skills/loop-engineering/SKILL.md`.

### Cursor / Windsurf / any agent with an instructions file
These don't have a formal skill loader, but the content works as-is. Reference it
from your rules/instructions file (`.cursorrules`, `AGENTS.md`, etc.):

```
When building or reviewing an autonomous/semi-autonomous agent loop, background
worker, or cron/webhook-driven agent, follow the framework in
skills/loop-engineering/SKILL.md (and its references/ files).
```

### Lowest common denominator
Any LLM tool: paste `SKILL.md` into context when you're designing or reviewing a
loop, and pull in a `references/*.md` file when the skill points to it.

## Using it

You don't invoke it explicitly — describe the task and the agent picks it up:

- *"I want an agent that watches CI overnight and fixes failing PRs on its own."* → design mode
- *"Review this background worker before we scale it to more queues."* → review mode
- *"My research agent keeps burning tokens and never finishes."* → diagnosis

## Reproduce the benchmark

The numbers above aren't hand-waving — the held-out cases are in this repo so you
can re-run them yourself, and the full per-iteration results (with an honest note
on where the skill *doesn't* help) are in [`evals/RESULTS.md`](evals/RESULTS.md).

- **The eval set** lives in [`evals/evals.json`](evals/evals.json): 11
  deliberately tricky cases spanning all four loop patterns (heartbeat / cron /
  hook / goal) plus long-horizon context, across **design**, **review**, and
  **diagnose** modes — from a CI/PR-fixer design to a flawed support-ticket bot
  (code in [`evals/files/`](evals/files/)) to a runaway research loop. Each case
  ships an `expected_output` rubric of the specific things a correct answer must
  nail (machine-checkable done-condition, all exits with real numbers,
  deterministic verification, human-gate on irreversible actions, etc.). The
  87% → 100% headline comes from the subtle/under-specified subset; the
  per-iteration breakdown is in [`evals/RESULTS.md`](evals/RESULTS.md).

**Method (same as the headline number):**

1. For each case, run the `prompt` **twice** — once with the skill installed
   (control flow above) and once on a clean baseline with no skill — across
   several runs each to average out variance.
2. Grade every run against its `expected_output` rubric (LLM-graded against the
   listed assertions; the rubric items are written to be objectively checkable).
3. Aggregate the per-assertion pass rate for each configuration and compare.

The pass-rate / variance / token aggregation in the headline figure was driven by
Anthropic's `skill-creator` benchmark harness (`grader` + `aggregate_benchmark`),
but any with-skill / without-skill comparison graded against the rubric will
surface the same gap. The skill's edge concentrates on the subtle
failure modes — stale-prompt drift, blind-retry waste, missing human-gates — that
a strong model otherwise skips when left to its own defaults.

## Contributing

Contributions are very welcome — new worked examples, extra loop patterns, sharper review heuristics, translations, or fixes. Open an issue or a PR.

**AI-assisted contributions are explicitly welcome.** This is a skill *about* agentic loops, so drafting your changes with Claude Code / Codex / Copilot / Gemini (or any coding agent) is encouraged — it fits the topic perfectly. Just review what your agent produces before submitting: make sure it's correct, grounded in a real source where it makes a claim (see `references/sources.md`), and that you'd stand behind it. Dogfooding this skill on your own PR is a plus.


## License / attribution

Released under the **MIT License** — see [`LICENSE`](LICENSE).

Distilled from public writing on loop engineering, agent loops, and context
engineering — see `references/sources.md` for the full source list and links.
