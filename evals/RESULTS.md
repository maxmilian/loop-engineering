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

## What this means

The skill is **not** a capability the base model lacks on clear tasks. Its value is:

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
