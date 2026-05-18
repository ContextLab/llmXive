# Contract: RevisionSpec directory

## Purpose

Define the on-disk layout produced by the `revision_planner` when it auto-kicks the 5-stage speckit pipeline. The implementer agent consumes this layout.

## Path

```
specs/auto-revisions/<PROJ-ID>/round-<N>/
```

`<N>` is 1-indexed; round 1 is the first auto-revision triggered for this project.

## Required files

| File | Producer stage | Contract |
|-|-|-|
| `spec.md` | speckit-specify | Standard speckit spec. The `User description` field is auto-seeded from the consolidated action items: "Address these reviewer-raised action items: <bulleted list of action_items>". |
| `clarifications.md` (or in-place clarifications in spec.md) | speckit-clarify | Auto-mode: no human Q&A — every clarification is auto-resolved using "best practice + spec assumption". |
| `plan.md` | speckit-plan | Standard. |
| `tasks.md` | speckit-tasks | Standard checklist format. MUST have ≥1 task. |
| `analyze-report.md` | speckit-analyze | Standard. After up to 3 iterations of remediation, MUST contain zero findings. |
| `result.yaml` | revision_planner (wrapper) | Records pipeline outcome (see below). |

## `result.yaml` schema

```yaml
project_id: PROJ-564-qwen-image-vae-2-0-technical-report
round: 1
triggered_by_review_round: 2          # the paper-review round whose verdict triggered this auto-revision
revision_kind: paper_writing          # paper_writing | paper_science
seed_action_items:
  - id: a3f1c9b2e5d8
    text: ...
    severity: writing
stage_results:
  specify:
    status: success
    duration_s: 12.4
    started_at: '2026-05-17T14:30:00Z'
    ended_at:   '2026-05-17T14:30:12Z'
  clarify:
    status: success
    duration_s: 8.1
  plan:
    status: success
    duration_s: 24.6
  tasks:
    status: success
    duration_s: 6.3
    task_count: 12
  analyze:
    status: success
    duration_s: 18.2
    iterations: 1
    final_finding_count: 0
final_outcome: ready_for_implementation   # OR: paper_revision_blocked
```

## Allowed `final_outcome` values

- `ready_for_implementation` — all 5 stages succeeded; analyzer reached 0 findings within 3 iterations.
- `paper_revision_blocked` — analyzer could not reach 0 findings after 3 iterations. `result.yaml` MUST also include a `block_diagnostic` field with the analyzer's last findings list.

## Discovery contract

The implementer agent finds work by:

1. Reading `state/revisions/index.yaml` for `ready_for_implementation` entries.
2. For each entry, the agent runs `speckit-implement` against the `revision_spec_path`.
3. On success, the agent transitions the project to `PAPER_REVIEW` and removes the entry from the index.
4. On failure, the agent attaches a diagnostic to the project YAML and the round counter remains.

## `state/revisions/index.yaml` schema

```yaml
ready:
  - project_id: PROJ-564-...
    revision_spec_path: specs/auto-revisions/PROJ-564-.../round-1
    queued_at: '2026-05-17T14:30:30Z'
blocked:
  - project_id: PROJ-565-...
    revision_spec_path: specs/auto-revisions/PROJ-565-.../round-2
    blocked_at: '2026-05-17T14:35:00Z'
    diagnostic_path: specs/auto-revisions/PROJ-565-.../round-2/result.yaml
```
