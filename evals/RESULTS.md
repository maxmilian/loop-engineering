# Validation Results

How well does this skill actually help? We ran the case library in `evals.json`
through an LLM **with the skill** and the same model **with no skill** (baseline),
then graded every answer against objective assertions (does it surface the specific
guardrail / failure mode / fix the case requires?).

> Honest summary: on **well-posed** prompts a strong base model already covers the
> ground, so the skill's measurable lift there is ~0. The skill's value shows up on
> **subtle / under-specified** cases — and as **consistency** (far lower variance).

## Method

- **with_skill**: the model reads `SKILL.md` (+ references as directed), then answers.
- **baseline**: same model, same prompt, no skill.
- Each answer graded pass/fail per assertion; pass rate = passed / total assertions.
- Model: a current frontier model (Claude Opus class). One run per cell.

## Results by iteration

| Iteration | Cases | Focus | With skill | Baseline | Δ |
|---|---|---|---|---|---|
| 1 | 3 | well-posed design/review/diagnosis | 100% | 100% | **+0** |
| 2 | 3 | subtle / under-specified (the traps) | 100% | 87% | **+13%** |
| 3 | 5 | breadth across all loop patterns | 100% | 100% | **+0** |
| 4 | 5 | adversarial framing (designed to discriminate) | 100% | 100% | **+0** |

Across 16 cases, only iteration 2 produced a measurable gap — and that was 2 assertions
out of 16. Read that honestly: **against a frontier model (Opus class), this skill is
at the ceiling.** A strong model already pushes back on full autonomy, names irreversible
boundaries, and surfaces idempotency / budget / no-progress traps unprompted, even when
the prompt is framed to invite an agreeable answer (iteration 4). The skill does not add
capability the model lacks here; see "What this means".

### Iteration 1 — well-posed cases (ceiling effect)
CI-PR-fixer design, flawed ticket-bot review, runaway research-loop diagnosis.
Both configs scored 100%. When the task is clearly specified, a strong model
already produces the guardrails, verification, and stopping conditions unaided.

### Iteration 2 — subtle cases (where the skill earns its keep)
A *positively-framed* review of a loop that looks safe but isn't ("we added the
caps, it's solid — anything left?"), a cron-to-Slack summarizer, and a
"retry-until-valid-JSON" helper. Here the baseline missed things the skill caught:

- **cron stale-prompt / silent-rot** failure mode (an unattended job whose
  assumptions rot over months) — skill raised it; baseline only mentioned generic
  model-upgrade drift.
- **blind-retry waste / feed-the-error-back** and **resumable state** on the batch
  JSON helper — skill added them; baseline retried blindly.

Result: **100% vs 87%**, and the skill answers were also more consistent and, on
these cases, cheaper (the baseline over-elaborated — token variance ±163k vs the
skill's ±945).

### Iteration 3 — breadth across patterns (coverage, ceiling effect again)
Five diverse, *well-specified* cases — hook (webhook-storm issue triage), heartbeat
(folder-watcher review), goal (validator-fixer + anti-cheat), cron (stale-issue
closer), and long-horizon context (monorepo audit). Both configs scored 100% on all
five. This validates **coverage** — the skill reliably hits every right point across
all four loop patterns + context engineering — but on well-posed prompts it doesn't
beat a strong baseline.

### Iteration 4 — adversarial framing (still ceiling)
Five cases written specifically to *discriminate* — each framed so the user nudges toward
an agreeable, generic answer: "help me wire up auto-merge + auto-deploy, no human in the
loop" (should push back), "I'll just bump retries 3→20, right?" (wrong fix), "works in
test, breaks in prod" (under-specified), "we trimmed the system prompt but it's still
slow" (tool outputs are the real hog), "every 10 min process new DB rows, easy right?"
(hidden idempotency). The baseline scored 100% anyway — the frontier model pushes back and
surfaces every trap on its own. The skill did not measurably beat it.

## Weak-model experiment — where the skill actually moves the needle

The frontier runs above are at the ceiling, so they can't show lift. So we re-ran a
representative 8-case subset on a **small/fast model (Haiku class)**, both with and
without the skill — the setting where a coverage guarantee should matter most.

| Config (Haiku) | Pass rate | Assertions |
|---|---|---|
| **with skill** | **90.0%** | 38 / 42 |
| baseline (no skill) | 74.2% | 31 / 42 |
| **Δ** | **+16 pp** | **+7** |

This is the real signal: **the skill lifts a weaker model by ~16 points.** The lift
concentrated on the *self-report / verification / human-gate* family — without the
skill, the weak model treated "it posts the model's output with no check" or "done =
the model said DONE" as a parsing/quality nit; with the skill it named the conceptual
flaw (trust the verifier not the agent; gate irreversible outward actions) and the
no-progress / publish-gate gaps. One regression (an idempotency-on-overlap case the
baseline caught via generic race-condition reasoning and the skilled run only half-
covered) keeps it honest.

**A gap the eval surfaced:** on the "agent games its own success proxy" cases
(cheating a validator / making tests green by deleting them), *both* configs missed it
— so this was a genuine hole in the skill, not just a model limitation. It has since
been added to Principle 3 and the review checklist (verifier must be read-only to the
agent; reject changes that touch or weaken the checker). That is the eval loop doing
its job: improving the skill, not just scoring it.

## What this means

On a **frontier** model these tasks are at the ceiling — the skill doesn't add
capability the model already has. On a **weaker** model the skill delivers a real,
measured **+16-point** lift. Either way, the skill's value is:

1. **Lift on the cases that actually bite** — subtle, positively-framed, or
   under-specified loops where a strong model otherwise rubber-stamps or misses a
   specific failure mode (iteration 2).
2. **A coverage guarantee** — every answer hits all seven principles across every
   loop pattern, instead of depending on the model happening to think of them.
3. **Consistency** — dramatically lower output variance, which matters when many
   people (or weaker models / smaller context budgets) use it.
4. **Shared vocabulary** — context rot, Ralph-Wiggum drift, webhook storm,
   stale-prompt, semi-autonomous boundary — so teams describe loop failures the same way.

## Reproducing

The graded prompts are in `evals.json` (with the input scripts under `evals/files/`).
Run each prompt with and without the skill and grade against each case's
`expected_output`. Contributions of new cases — especially subtle/under-specified
ones that *discriminate* — are very welcome; see the repo README.
