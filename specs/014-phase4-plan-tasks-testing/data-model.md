# Data Model: Phase 4 Validation & Hardening

Phase 1 output for [plan.md](./plan.md). Entities are the data structures this feature reads, writes, or validates. Each maps to a `contracts/` schema (see [contracts/](./contracts/)).

## Reference Project

A real project used as validation input.

| Field | Type | Notes |
|-|-|-|
| project_id | str | e.g. `PROJ-261-evaluating-the-impact-of-code-duplicatio` |
| current_stage | str | Read from `state/projects/<id>.yaml`; MUST be `clarified` at entry (FR-002/FR-019) |
| speckit_research_dir | str | Path to `projects/<id>/specs/001-<slug>` (where Planner/Tasker write) |
| field | str | Domain (`computer science`, `chemistry`) — drives domain-specific artifacts |

Reference set for this feature: PROJ-261 (CS) and PROJ-262 (Chemistry). State transitions during a run: `clarified → planned → tasked → analyze_in_progress → analyzed` (cap-hit without convergence still advances to `analyzed` best-effort; `→ human_input_needed` only on an explicit Mode-B `escalate` verdict or backend failure).

## Plan Artifact Set

The five documents the Planner writes in one multi-file response, split on `<!-- FILE: <path> -->` markers (`plan_cmd._split_multi_file`).

| Artifact | Required | Validation |
|-|-|-|
| plan.md | yes | non-empty; not template (`guard_emit`); MUST contain a Constitution Check section addressing every numbered principle (FR-020) |
| research.md | yes | non-empty; every URL/identifier returns 2xx/3xx (FR-006, `_research_guard.assert_urls_reachable`) |
| data-model.md | yes | non-empty; every entity has a `contracts/` schema (FR-007) |
| quickstart.md | yes | non-empty; not template |
| contracts/<schema>.schema.yaml | ≥1 | every schema corresponds to a data-model entity (FR-007) |

Reset (FR-018): all of the above are deleted before a re-run; `spec.md` is PRESERVED.

## Analyze Revision Round

One Mode-A→Mode-B iteration of the Tasker loop (`tasks_cmd.py:188`).

| Field | Type | Notes |
|-|-|-|
| round_index | int | 0-based |
| analyze_report | str | verbatim `/speckit.analyze` output for this round |
| mode_b_patch | object\|null | the Mode-B JSON: `issues_resolved[]`, `issues_remaining[]`, `verdict` (`clean`/`needs-rerun`/`escalate`); null on a clean first pass |
| verdict | str | `clean` \| `needs-rerun` \| `escalate` |
| files_rewritten | list[str] | which of spec.md/plan.md/tasks.md were rewritten this round |
| diffs | object | path → unified diff (before/after) for each rewritten file |

Bounded by `TASKER_MAX_REVISION_ROUNDS` (config default 5). 0 rounds = clean on first analyze (success). Cap-hit WITHOUT convergence → best-effort advance to `analyzed`, recording `converged: false` in `tasker_rounds.yaml`. An explicit Mode-B `verdict: escalate` writes `human_input_needed.yaml` (per the 2026-05-21 decision).

## Inspection Record

One JSON file per `(project, agent)` under `specs/014-…/inspections/<project_id>/<agent>.json`. Extends the spec-011 schema (all spec-011 required keys retained → existing records stay valid) with a `rounds` array.

| Field | Type | Notes |
|-|-|-|
| project_id | str | |
| agent_name | str | `planner` \| `tasker` |
| agent_version | str | from registry `prompt_version` |
| model, backend | str | resolved model id + backend name |
| started_at, ended_at | ISO-8601 | |
| duration_s | float | |
| outcome | str | `committed` \| `abstained` \| `failed` \| `held` \| `no-op` \| `escalated` |
| reset_artifacts | list[str] | paths deleted by FR-018 reset before this invocation |
| prompts | object | `{system, user}` verbatim |
| raw_response | str | verbatim LLM text (redacted of secrets via `_inspection._redact`) |
| parsed_output | object | for Planner: the FILE-split map; for Tasker: final tasks.md summary |
| file_diffs | object | path → unified diff for every file the agent wrote |
| rounds | list[AnalyzeRevisionRound] | **NEW**; `[]` for the Planner; one entry per Tasker analyze round (FR-004) |
| error | str\|null | populated on `failed`/`held`/`escalated` |

Commit-safe (FR-004): no secrets/keys; only model id + truncated request id.

## Carry-forward Manifest

`specs/014-…/carry-forward.yaml`. Same shape as `specs/011-…/carry-forward.yaml`.

```yaml
spec: 014-phase4-plan-tasks-testing
generated_at: <ISO-8601>
final_commit: <sha|HEAD>
projects:
  - project_id: PROJ-261-…
    final_state: analyzed            # or human_input_needed / held
    status: passed                   # passed | failed | held
    agents_run:
      - {name: planner, iterations: 1, final_outcome: committed}
      - {name: tasker,  iterations: 1, final_outcome: committed, analyze_rounds: <n>}
    justification: <one line; cites inspection path on failure>
```

## Phase Report

`specs/014-…/phase-report.md` (SC-010/SC-011). Human-readable summary: per-canonical stage chain, Planner/Tasker outcomes, Tasker round count, FR→evidence table, any silently-broken behavior caught (naming the inspection-record path), and the Mode-B coverage statement (real run and/or regression tests, per project).

## New exceptions (in `_research_guard.py`)

| Exception | Raised when | Caller behavior |
|-|-|-|
| IncompleteArtifactSet(missing, reason) | fewer than the five required artifacts present, an empty artifact, or a failed FILE-marker split (FR-005) | Planner unlinks artifacts, `outcome: failed`, hold at `clarified` |
| UnreachableReference(url, reason) | a `research.md` URL/identifier is not 2xx/3xx (FR-006) | same as above |
| InconsistentDataModel(reason, invalid_schemas) | data-model.md defines no entities, or a contracts/ schema is empty/unparseable/not a schema (FR-007, structural — no 1:1 name match) | same as above |

Both subclass `RuntimeError` so the existing base-class failure handling (which already catches `TemplateRefused`/`RuntimeError` from the write path) maps them to `failed` without further wiring.

## Run-log Entry (existing — read-only)

One JSONL line per agent invocation under `state/run-log/<YYYY-MM>/<run-id>.jsonl` with `agent`, `project_id`, `started_at`, `ended_at`, `outcome`, `error`. Phase 4 validation reads these (FR-014); it does not change the format.
