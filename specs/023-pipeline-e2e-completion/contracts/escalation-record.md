# Contract: Exhaustion-Evidence Escalation Record

**Feature**: 023-pipeline-e2e-completion (US4, FR-017)
**Location**: `state/escalations/<project-id>__<timestamp>.yaml`

A project may enter `human_input_needed` (outside the publication
sign-off gate) ONLY accompanied by a record proving a bounded automated
loop was exhausted. Writers without such a record are prohibited and
removed by this feature.

## Schema

```yaml
project_id: PROJ-###
stage: <stage at escalation>
timestamp: ISO-8601
loop: <which bounded automation was exhausted, e.g. "feasibility-rebrainstorm", "revision-kickback">
bound: <the configured cap, e.g. 3>
rounds_used: <must equal bound>
attempts:                      # last attempts, machine-checkable evidence
  - round: 1
    summary: <what was tried>
    outcome: <why it failed>
  # ... one entry per round
recommended_action: <plain-language ask for the human>
digest_id: <null until aggregated>
```

## Rules

- `rounds_used >= bound` is validated at write time (fail fast if an
  escalation is attempted before exhaustion).
- Infrastructure failures NEVER produce this record (FR-015): they resolve
  to retry-later.
- Engine failures produce a tracked GitHub issue (FR-016), not this
  record; the project stays schedulable.
- A periodic digest aggregates open records (sets `digest_id`); no
  per-project pings.
- Steady-state target: ~zero open records (SC-005); the count is
  observable from the directory listing.
