---
name: loop-engineering
description: >-
  Design and review autonomous or semi-autonomous agent loops — systems where
  an agent prompts itself, runs on a schedule or event, and iterates toward a
  goal without a human at the keyboard. Use this whenever the user wants to
  build, design, harden, or audit any kind of self-running agent, agentic
  workflow, control loop, background worker, cron/heartbeat/webhook-driven
  agent, "Ralph loop", auto-PR-fixer, monitoring agent, or any long-running
  task that should keep going on its own until done. Trigger this even when the
  user says "agentic workflow", "automation that runs itself", "an agent that
  keeps trying until X", or "make my agent stop running away / burning tokens"
  without using the word "loop". Also use it to review an existing loop's
  stopping conditions, guardrails, verification, and escalation paths.
---

# Loop Engineering

Loop engineering is the discipline that comes after prompt engineering. A prompt
optimizes a single interaction. A **loop** optimizes the autonomous behavior that
surrounds it — *when* the agent runs, *what* triggers it, *how* it verifies its
own work, *when* it stops, and *when* it hands back to a human.

The hard part is never the loop itself. A bare agent loop (call model → run tool
→ observe → repeat) is ~30 lines and every framework's core is the same. The
whole job is the engineering *around* it: verification, stopping conditions,
guardrails, context management, and escalation. Build those wrong and you are one
edge case away from an agent that loops forever, burns the budget, or silently
ships garbage.

This skill has two modes. Detect which one the user needs:

- **Design mode** — the user is building a new loop. Walk the whiteboard, then
  the seven principles, then hand them a concrete design.
- **Review mode** — the user has a loop already (a script, a workflow, an agent).
  Use the seven principles as a diagnostic checklist and report what's missing.

Most requests are one or the other; some are both. Don't force the framework on a
user who just wants a quick answer — but for anything that will run unattended,
the failure modes below are real and worth raising.

## Principle 0 — Whiteboard before platform

Before writing any code or choosing any framework, answer five questions on paper.
If you can answer these, the implementation is a few hours. If you skip them, you
are building a demo, not a production loop.

1. **What triggers it?** Time (cron), interval (heartbeat), external event (hook),
   or a goal it chases until met? (See `references/loop-patterns.md`.)
2. **What does it check each cycle?** The single observation that decides whether
   there's work to do.
3. **What action does it take?** Ideally one well-scoped action per cycle.
4. **When does it stop?** This must be *machine-checkable*, not "when it's done."
5. **When does it escalate to a human?** The path out when the goal can't be met.

> "Write the loop on a whiteboard before you open any platform."

## The seven principles

These are the load-bearing ideas, distilled across the field. In **design mode**
build each one in; in **review mode** check each one off and flag what's absent.

### 1. Leverage has moved from the prompt to the loop
What the agent does in any single cycle matters less than when it runs, what
triggers it, and when it stops. Spend your design effort on the loop's control
flow, not on perfecting one prompt.

### 2. "Done" must be a machine-checkable endpoint
`tests pass` ✓. `improve the code` ✗. `researched the competitors` ✗.
`covered competitors X, Y, Z, each with at least one named source` ✓. A goal
without a checkable success condition has no convergence criterion — it just
iterates until the budget is gone. **Define "done" before the loop starts**, and
write success/failure criteria into the agent's prompt where it can evaluate them.

### 3. Verify with deterministic tools, never the agent's self-report
The agent saying "I'm done" is not evidence. A CI run, a test runner, a schema
check, a diff against expected output — that is evidence. Verify in layers:
per-action, per-iteration, and terminal. The verifier is the part you trust;
the agent is the part you check.

**Beware the agent gaming the proxy.** A success signal is a *proxy* for the goal,
and an agent optimizing to make the signal go green will, if it can, satisfy the
signal instead of the goal — delete or skip the failing test, weaken the
assertion, edit the validator's config, add `continue-on-error`, hardcode the
expected output. This is reward hacking / Goodhart's law, and it is one of the most
common ways an autonomous loop "succeeds" while producing garbage. Defend it: make
the verifier and its config **read-only / out of reach** of the agent, diff every
change and reject ones that touch tests/CI/the checker or weaken coverage, and
keep an invariant the agent can't edit (e.g. test count must not drop). When you
choose a success condition, ask "how would a lazy agent make this green *without*
doing the work?" and close that path.

### 4. Define all exits and guardrails before going live
A production loop needs, at minimum:
- a **success** exit (verifier confirms the goal),
- a **failure** exit (unrecoverable error, retry limit hit),
- a **budget** exit (max iterations, token cap, wall-clock timeout — whichever
  trips first),
- **no-progress detection** (state stops changing across recent steps → break;
  a.k.a. loop fingerprinting), and
- an **escalation path** (can't reach the goal → stop and alert a human queue,
  never silently continue).

Success and failure criteria belong in the prompt; budget and no-progress caps
belong in the controller code, because you cannot trust the agent to enforce its
own ceiling. For hook-triggered loops, add **rate limiting / backpressure** — a
webhook storm (10,000 events → 10,000 runs) can drain a day's budget in minutes.

### 5. Treat context as a finite resource
Every token spends the model's attention budget, with diminishing returns; recall
degrades as context grows ("context rot"). Aim for the *smallest set of
high-signal tokens*. Tool outputs — not the system prompt — are usually the token
hog (often the majority of what the agent sees), so trim raw tool results to the
fields that matter before they enter context. For long-horizon loops use the three
levers in `references/context-engineering.md`: **compaction**, **structured
note-taking**, and **sub-agent architectures**.

### 6. Use the filesystem as memory; start each cycle with fresh context
Conversation history is a fragile place to keep state — it drifts and rots as it
grows ("Ralph Wiggum drift"). Durable state lives *outside* the context window: in
the codebase, a TODO/PROGRESS file, git history, or a state JSON. Each cycle
should reconstruct what it needs from that external memory rather than depending on
what's still in the conversation. Re-read the state file every cycle instead of
trusting a number you saw twenty steps ago. This is what makes a loop survivable
across hundreds of iterations and context resets.

### 7. The hard part is verification, stopping, and escalation — not autonomy
Don't sell or build "fully autonomous." The credible, safe design is
**semi-autonomous**: the agent runs freely up to the point of an irreversible or
outward-facing action (publishing, merging, deleting, emailing), then stops and
asks. Reversible internal work → automate. Irreversible/external work → gate it
behind a human. This is both safer and more trustworthy than full autonomy.

## Design mode: produce a concrete loop design

When the user is building a loop, work through this and hand back an actual design,
not a lecture:

1. **Run the whiteboard five** (Principle 0) with the user. Pin down the trigger
   pattern using `references/loop-patterns.md`.
2. **Write the machine-checkable success condition** (Principle 2). If you can't
   write one, the goal is underspecified — surface that now, it's the most common
   root cause of runaway loops.
3. **Specify all exits and guardrails** (Principle 4) with concrete numbers:
   iteration cap, token/cost budget, wall-clock timeout, no-progress rule.
4. **Choose the verification mechanism** (Principle 3) — name the actual tool/check.
5. **Decide the context strategy** (Principles 5–6) — what's durable state on disk,
   what's reconstructed each cycle, when compaction/sub-agents kick in.
6. **Mark the escalation boundary** (Principle 7) — exactly which actions stop and
   wait for a human.
7. **Sketch the control flow** — the loop body as pseudocode or a real script,
   with the exits wired in. Keep the body small; the intelligence is in the
   guardrails, not the loop.

## Review mode: diagnose an existing loop

When the user already has a loop, read it (the script, the policy doc, the agent
config) and produce a findings report. Use `references/review-checklist.md` for the
full diagnostic; the short version is one pass per principle:

For each of the seven principles, answer: **present / partial / missing**, cite
where in their code or config it lives (or should), and give the single most
valuable fix. Lead with the missing guardrails — a loop with no budget exit or no
escalation path is the highest-severity finding. Don't pad the report with
principles they already nailed; spend the words on the gaps.

## References

Load these as needed — don't pull them all in at once.

- `references/loop-patterns.md` — the four trigger patterns (heartbeat, cron, hook,
  goal), their failure modes, and how production loops combine them.
- `references/context-engineering.md` — managing context across long-horizon loops:
  compaction, structured note-taking, sub-agents, just-in-time retrieval.
- `references/review-checklist.md` — the full per-principle diagnostic for review
  mode, with severity ordering.
- `references/sources.md` — the 12 source articles this skill distills, with
  one-line summaries, for when the user wants to go deeper or cite origins.
