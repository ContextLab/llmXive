# Data Model: Pipeline End-to-End Completion

**Date**: 2026-06-10 | **Feature**: [spec.md](spec.md)

Entities here map onto *existing* canonical records wherever possible
(Constitution I). Only two record types are new: the **sign-off record**
(the GitHub issue + its parsed outcome) and the **per-paper status
record**. Everything else is a repaired flow through existing models.

## Project (existing — `projects/<id>/.llmxive/config.json` + state)

| Field (relevant subset) | Type | Notes |
|-|-|-|
| `current_stage` | Stage enum (~34 states) | unchanged |
| `revision_spec_path` | str \| None | EXISTS today; the field the graph discards. After US1 it is durably persisted and cleared only when the implementer consumes it. |
| `kickback_count` | int | existing bounded cap (3) → honest terminal |
| `stage_history` | list[Transition] | must contain every phase for SC-001 |

**State transitions touched** (no new stages):

- `paper_review --evaluate:all-accept--> paper_accepted --> awaiting_publication_signoff`
- `paper_review --evaluate:revise--> paper_review` **+ persisted `revision_spec_path`** (next pick dispatches implementer, not reviewers)
- `awaiting_publication_signoff --maintainer approve--> posted` (DOI minted)
- `awaiting_publication_signoff --maintainer reject--> paper_review` (reason → review feedback)
- `flesh_out_complete --validator accept--> validated ...` (now scheduled)
- `flesh_out_complete --infeasible verdict--> archived idea + constrained re-brainstorm (bounded N) --> brainstormed | rejected/backlog` (never `human_input_needed`)

**Invariants**:

- A project with non-None `revision_spec_path` is never re-dispatched to reviewers for the same artifact hash.
- `posted` requires exactly one minted DOI; re-running the publisher converges without a second mint.
- `human_input_needed` is reachable only with an attached exhaustion-evidence escalation record (outside the sign-off gate, population ≈ 0).

## Review verdict set (existing — `projects/<id>/[paper/]reviews/*.md`)

| Property | Type | Notes |
|-|-|-|
| per-specialist records | review-record contract files | existing frontmatter contract |
| completeness | derived | all required specialists present for current artifact |
| currency / staleness | derived | verdict's artifact hash vs live hash (`_infer_live_hash`, advancement.py) |

**Rule (FR-004, edge case)**: complete + current → evaluate without
re-dispatch; complete + stale → re-review only the changed artifact, with
the staleness reason recorded; incomplete → dispatch only the missing
specialists.

## Revision work-spec (existing — `specs/auto-revisions/<project>/...` + `state/revisions/index.yaml`)

| Field | Type | Notes |
|-|-|-|
| spec path | str | referenced by `project.revision_spec_path` |
| source concerns | KickbackRecord | severity-routed, from advancement evaluation |
| round | int | bounded by kickback cap |
| consumed_by | run id | set when the implementer completes it |

**New producer** (US6): audit-defect and compile-failure repair rounds
generate work-specs through the same machinery (no parallel repair format).
**Persistence rule (FR-003)**: `specs/` is included in every CI persist step.

## Escalation record (new shape on existing escalation path — `state/escalations/`)

See [contracts/escalation-record.md](contracts/escalation-record.md).

| Field | Type | Notes |
|-|-|-|
| `project_id`, `stage`, `timestamp` | str | |
| `loop` | str | which bounded automation was exhausted |
| `evidence` | object | rounds/attempt counts, last N attempt summaries — machine-checkable (SC-005) |
| `digest_id` | str \| None | set when aggregated into a periodic digest |

## Sign-off record (new — GitHub issue + `projects/<id>/paper/signoff.yaml`)

See [contracts/signoff-issue.md](contracts/signoff-issue.md).

| Field | Type | Notes |
|-|-|-|
| `issue_number` | int | the durable record; tags maintainers |
| `decision` | pending \| approved \| rejected | rejection precedence over approval |
| `decided_by` | str \| None | validated against maintainer list |
| `rejection_reason` | str \| None | routed into the revision loop |
| `doi` | str \| None | written exactly once (idempotence key) |
| `reminders_sent` | list[date] | reminder cadence without scheduler load |

## Paper status record (new — `state/paper_status/<id>.json`)

See [contracts/paper-status-record.md](contracts/paper-status-record.md).

| Field | Type | Notes |
|-|-|-|
| `status` | audited \| restyled_unaudited \| fallback_original | site shows exactly this (FR-024) |
| `failure` | {stage, reason} \| None | machine-readable, replaces silent fallback (FR-022) |
| `audit` | {passed, defects[]} \| None | defects feed repair work-specs (FR-023) |
| `repair_rounds` | int | bounded loop counter |
