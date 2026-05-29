# Reviser Self-Consistency Pass — shared prompt snippet (spec 015, FR-011)

# SINGLE SOURCE OF TRUTH (Constitution Principle I): editing this file changes
# the self-consistency contract for EVERY reviser at once. Do NOT copy this
# text into individual reviser modules — the convergence revisers append this
# block to the self-consistency check call at render time via
# `src/llmxive/convergence/revisers/_self_consistency.py`.
#
# Consumers (the R2 "second pass" that FR-011 requires):
#   - SpecReviser / PaperSpecReviser
#   - PlanReviser / PaperPlanReviser
#   - TasksReviser / PaperTasksReviser
#   - FleshOutReviser
#   - ImplementerReviser / PaperImplementReviser
#
# FR-011 (issue §1): "the step's reviser MUST address every R1 concern, run a
# self-consistency pass, and emit a structured response + change-log per
# concern." This block IS the self-consistency pass: a second LLM call where
# the reviser audits its OWN just-produced revision before the engine sees it.

## Self-Consistency Audit (you are checking your OWN revision)

You just revised one or more artifacts to address a list of reviewer concerns.
Before this revision is accepted, audit it against THREE questions:

  (a) **Resolution.** For EACH concern, is it GENUINELY resolved by the revised
      artifact text — not merely claimed-resolved in the change-log while the
      artifact body is unchanged or still wrong?
  (b) **No new contradiction.** Did the revision introduce any internal
      contradiction (two statements that cannot both hold), or break a
      cross-reference (an FR/SC/`T###`/`\label{}`/section pointer that no
      longer resolves)?
  (c) **No unrelated deletion.** Did the revision delete or gut content that
      was NOT the target of any concern (e.g. dropping a whole section, a
      preserved `## Search trail`, a numerical result, a citation) — i.e. a
      regression masquerading as a fix?

Be strict but honest. A clean revision SHOULD pass. Do NOT invent problems to
look thorough — a false "problem" forces a wasteful corrective re-pass. Only
flag issues you can point at concretely (quote the offending text or name the
concern id / artifact path / identifier).

## Output contract (ONE YAML document, no prose around it)

```yaml
ok: true            # true iff (a) all resolved AND (b) no contradiction AND (c) no unrelated deletion
problems:           # empty list iff ok: true. Otherwise one entry per concrete problem.
  - "<concrete problem; name the concern id / artifact path / identifier; quote the offending text>"
```

Rules:

- `ok` MUST be `false` whenever `problems` is non-empty (and vice-versa).
- Each `problems` entry MUST be concrete and actionable — it is fed straight
  back to you as an appended corrective instruction for ONE re-pass. Generic
  "looks incomplete" is useless; say exactly what to fix and where.
- This audit runs AT MOST once; the corrective re-pass that consumes your
  `problems` is final. Spend your scrutiny here, not on a hypothetical 3rd pass.
