# Review-Mode Diagnostic Checklist

Use this when auditing an existing loop (a script, a workflow doc, an agent config).
Read the actual artifact first. Then go principle by principle, mark
**present / partial / missing**, cite where it lives (or should), and give the one
highest-value fix. Order the report by severity, not by principle number.

## Severity ordering (lead with these)
A missing guardrail is more dangerous than a missing optimization. Triage in this
order:
1. **No budget exit** (iteration cap / token cap / wall-clock) → can run away and
   drain spend. Highest severity.
2. **No escalation path** → fails silently, no human ever finds out.
3. **No machine-checkable success condition** → never converges, or "succeeds"
   without actually being done.
4. **Verification by self-report** → ships unverified work that looks done.
5. **No no-progress detection** → spins on the same state burning budget.
6. **Hook with no rate limit / backpressure** → storm drains budget in minutes.
7. **Context not externalized** → drifts and rots over long runs.
8. Everything else (token trimming, altitude, pattern fit) → quality, not safety.

## Per-principle questions

**1. Leverage in the loop, not the prompt**
- Is the design effort in the control flow, or is it one big prompt doing everything?
- Partial credit: good prompt but no real loop structure around it.

**2. Machine-checkable "done"**
- Find the stated success condition. Can a script evaluate it without a human?
- Red flag: success defined as "the task is complete" / "the code is improved."

**3. Deterministic verification**
- What actually checks the work — a test/CI/schema/diff, or the agent's word?
- Are there verification layers (per-action, per-iteration, terminal)?
- Can the agent **game the proxy** — delete/skip/weaken tests, edit the validator
  or CI config, add `continue-on-error`, hardcode expected output? Is the verifier
  read-only to the agent, and are changes that touch it / weaken coverage rejected?
- Red flag: the only check is the model asserting success.
- Red flag: the agent can edit the very thing that judges it.

**4. Exits & guardrails**
- Success exit present? Failure exit? Budget exit (which limits, what numbers)?
- No-progress / loop-fingerprint detection?
- Escalation path on failure — where do stuck cases go?
- For hook loops: rate limit + backpressure?
- Are budget/no-progress caps enforced in *code*, not just asked of the agent?

**5. Context as a finite resource**
- Are raw tool outputs trimmed before entering context, or dumped whole?
- For long runs: is there compaction / note-taking / sub-agent delegation?
- Red flag: full GraphQL/JSON/tool blobs passed straight into the decision context.

**6. Filesystem-as-memory, fresh-context cycles**
- Where does durable state live — on disk or only in conversation history?
- Does each cycle re-read state, or trust remembered values?
- Red flag: long-lived session relying on numbers it "saw earlier."

**7. Semi-autonomous boundary**
- Which actions are irreversible/outward-facing (publish, merge, delete, email)?
- Do those stop and wait for a human, or fire automatically?
- Red flag: full autonomy through irreversible actions with no gate.

## Report format
Keep it tight. For each finding:
- **Principle / area** — present / partial / missing — severity
- **Where** — file:line or config location (or "absent; should live in X")
- **Fix** — the single most valuable change

Don't enumerate what's already correct beyond a one-line acknowledgment. Spend the
words on the gaps and the fixes.
