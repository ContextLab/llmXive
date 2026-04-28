# Data Model: Agentic Pipeline Refactor

**Date**: 2026-04-28

This document captures every persistent entity, its fields, validation
rules, and state transitions. Wire formats live in [`contracts/`](contracts/).

## E1. Project

A research effort the pipeline is advancing.

**Storage**: `state/projects/<PROJ-ID>.yaml` (one file per project).
**Wire format**: [`contracts/project-state.schema.yaml`](contracts/project-state.schema.yaml).

| Field | Type | Required | Notes |
|-|-|-|-|
| `id` | string | yes | Pattern `^PROJ-\d{3,}-[a-z0-9-]+$`. Globally unique. |
| `title` | string | yes | Human-readable title. |
| `field` | string | yes | e.g., `biology`, `materials-science`. |
| `current_stage` | enum | yes | One of the 30+ values defined in `contracts/project-state.schema.yaml` (e.g., `brainstormed`, `specified`, `clarified`, `planned`, `tasked`, `analyzed`, `in_progress`, `research_complete`, `research_review`, `research_accepted`, `paper_drafting_init`, `paper_specified`, …, `paper_accepted`, `posted`, plus cross-stage `human_input_needed` / `blocked`). |
| `points_research` | object | yes | Map of research-stage point bucket → accumulated points. Numeric, ≥ 0. |
| `points_paper` | object | yes | Map of paper-stage point bucket → accumulated points. Numeric, ≥ 0. |
| `speckit_research_dir` | string | no | Path to the project's research Spec Kit feature directory (e.g., `projects/PROJ-001-foo/specs/001-something`). Set from `specified` onward. |
| `speckit_paper_dir` | string | no | Path to the project's paper Spec Kit feature directory. Set from `paper_specified` onward. |
| `revision_round` | int | no | Number of revision rounds the project has been through. |
| `human_escalation_reason` | string | no | Set when `current_stage=human_input_needed`. |
| `created_at` | ISO 8601 | yes | UTC. |
| `updated_at` | ISO 8601 | yes | UTC. Set by every mutating agent. |
| `last_run_id` | string | no | Most recent run that touched this project. |
| `last_run_status` | enum | no | One of {`success`, `failed`, `skipped`, `blocked`}. |
| `failed_stage` | string | no | If `last_run_status=failed`, the stage that failed. Used for resume. |
| `artifact_hashes` | object | yes | Map of artifact-relative-path → SHA-256. Used for tamper detection (FR-007 manual-edit edge case). |
| `assigned_agent` | string | no | Agent name currently working on the project (if locked). |

### Validation rules

- `id` MUST be unique across `state/projects/`.
- `points[stage]` MUST be ≥ 0.0 and ≤ a reasonable upper bound (e.g., 100).
- `current_stage` MUST be consistent with `points` per the advancement
  thresholds: e.g., `current_stage="ready"` requires
  `points["technical_design"] >= 5.0`.
- `artifact_hashes` MUST cover every file under
  `projects/<PROJ-ID>/{idea,technical-design,implementation-plan,code,paper}/`.

### State transitions (Spec-Kit-per-project lifecycle)

```text
                            (Brainstorm Agent)
                                  │
                                  ▼
                            brainstormed
                                  │ (Flesh-Out Agent uses Lit-Search; duplicate-detect)
                                  ▼
                            flesh_out_complete
                                  │ (Idea-Selector promotes; Project-Initializer scaffolds)
                                  ▼
                            project_initialized
                                  │ (Specifier Agent: /speckit.specify)
                                  ▼
                            specified
                                  │ (Clarifier Agent: /speckit.clarify; primary-source verification)
                                  ▼
                            clarified
                                  │ (Planner Agent: /speckit.plan)
                                  ▼
                            planned
                                  │ (Tasker Agent: /speckit.tasks)
                                  ▼
                            tasked
                                  │ (Tasker Agent: /speckit.analyze + resolve loop, ≤ 5 rounds)
                                  ▼
                            analyzed
                                  │ (Implementer Agent: /speckit.implement; partial allowed)
                                  ▼
                            in_progress  ◀─── (resumed by next scheduled run)
                                  │
                                  │ (last task done)
                                  ▼
                            research_complete
                                  │ (Research-Reviewer Agents vote)
                                  ▼
                            research_review
                                  │
       ┌─────────────────┬────────┼────────────────┬─────────────────┐
       │ accept ≥ thresh │ minor  │ full revision  │ reject          │
       ▼                 ▼        ▼                ▼                 │
research_accepted  minor_revision  full_revision  research_rejected  │
       │                 │            │                              │
       │            (re-Tasker)  (back to Specifier)              (back to brainstormed)
       │
       │  (Paper-Initializer scaffolds)
       ▼
paper_drafting_init
       │  (Paper-Specifier → Paper-Clarifier → Paper-Planner →
       │   Paper-Tasker (analyze loop) → Paper-Implementers
       │   (writing, figures, statistics, lit-search, ref-verifier,
       │    proofreader, latex-build, latex-fix))
       ▼
paper_in_progress  ◀─── (resumed by next scheduled run)
       │
       ▼
paper_complete
       │  (Paper-Reviewer Agents vote)
       ▼
paper_review
       │
   ┌───┴────┬────────────────────┬──────────────────┬────────────────┐
   │ accept │ minor revision     │ major: writing   │ major: science │ fundamental
   ▼        ▼                    ▼                  ▼                ▼  flaws
posted   minor_revision_paper  paper_clarify    research_clarify  brainstormed
              │                    │                  │
        (re-Paper-Tasker)    (paper pipeline)   (research pipeline)
```

All transitions are authored only by the **Advancement-Evaluator
Agent** (rule-based, non-LLM). No LLM agent may write `current_stage`.

The full enum and cross-field invariants are in
[`contracts/project-state.schema.yaml`](contracts/project-state.schema.yaml).

## E2. Stage

Enumerated set defined in
[`contracts/project-state.schema.yaml`](contracts/project-state.schema.yaml)
(30+ values covering brainstorming → research Spec Kit pipeline →
research review → paper Spec Kit pipeline → paper review → posted, plus
cross-stage `human_input_needed` and `blocked`).

Advancement thresholds are parsed from `web/about.html` at preflight.
Per FR-038, the about page is the single source of truth; code reads
via the parser and never hardcodes these values. The about page MUST
be updated in this PR to publish thresholds for:

| Threshold | Used by |
|-|-|
| `research_accept_threshold` | `research_review` → `research_accepted` |
| `paper_accept_threshold` | `paper_review` → `paper_accepted` |
| Per-stage Spec Kit progression checkpoints | per-stage advancement (e.g., `tasked` → `analyzed`) |
| Tasker-loop max rounds | escalation to `human_input_needed` (default 5) |

## E3. Artifact

Any file an agent reads or writes inside a project's canonical layout.

| Field | Type | Required | Notes |
|-|-|-|-|
| `path` | string | yes | Repo-relative, under `projects/<PROJ-ID>/`. |
| `kind` | enum | yes | `idea`, `technical_design`, `implementation_plan`, `code`, `data`, `paper`, `review`. |
| `format` | enum | yes | `markdown`, `latex`, `python`, `notebook`, `csv`, `json`, `yaml`, `figure`. |
| `content_hash` | string | yes | SHA-256 hex. |
| `produced_by_agent` | string | no | Agent name (null for human-authored). |
| `produced_at` | ISO 8601 | yes | UTC. |
| `parent_artifact` | string | no | Path of the artifact this one was derived from. |

### Validation rules

- `path` MUST start with `projects/<PROJ-ID>/` and MUST NOT contain `..`.
- `content_hash` MUST match the SHA-256 of the file's bytes when
  recorded.
- `format` MUST match the file extension (`.md`→markdown, `.tex`→latex,
  …).

## E4. Review Record

A signed record of a review of an artifact.

**Storage**: `projects/<PROJ-ID>/reviews/<author>__<YYYY-MM-DD>__<type>.md`,
with a YAML frontmatter conforming to `contracts/review-record.schema.yaml`.

| Field | Type | Required | Notes |
|-|-|-|-|
| `reviewer_name` | string | yes | Agent name OR human GitHub username. |
| `reviewer_kind` | enum | yes | `llm` or `human`. |
| `artifact_path` | string | yes | Path of the artifact being reviewed. |
| `artifact_hash` | string | yes | SHA-256 at review time (anti-tamper). |
| `score` | number | yes | `0.5` for `llm`, `1.0` for `human`. Rejecting reviews score `0.0`. |
| `verdict` | enum | yes | Research-stage reviews use one of {`accept`, `minor_revision`, `full_revision`, `reject`}; paper-stage reviews use one of {`accept`, `minor_revision`, `major_revision_writing`, `major_revision_science`, `fundamental_flaws`}. The reviewer's stage (`research` vs `paper`) is implied by the `reviews/` subdirectory the file lives in. |
| `feedback` | string | yes | Free-form review body (the file's markdown body). |
| `reviewed_at` | ISO 8601 | yes | UTC. |
| `prompt_version` | string | no | If `reviewer_kind=llm`, the prompt template version used. |
| `model_name` | string | no | If `reviewer_kind=llm`, the LLM model name. |
| `backend` | string | no | If `reviewer_kind=llm`, the backend (`dartmouth` / `huggingface` / `local`). |

### Validation rules

- `score` MUST be exactly `0.5` for `llm` accept, `1.0` for `human`
  accept, or `0.0` for any reject (per FR-007 self-review edge case:
  rejected reviews still count toward audit but not toward advancement).
- An LLM reviewer MUST NOT review an artifact it authored: the
  Advancement-Evaluator MUST verify
  `reviewer_name != artifact.produced_by_agent` before counting points.
- `artifact_hash` MUST match the live artifact's hash; otherwise the
  review is stale and points are NOT counted.

## E5. Run-Log Entry

One append-only line per agent invocation.

**Storage**: `state/run-log/<YYYY-MM>/<run-id>.jsonl` (one line per
agent invocation; one file per scheduled run).
**Wire format**: [`contracts/run-log-entry.schema.json`](contracts/run-log-entry.schema.json).

| Field | Type | Required | Notes |
|-|-|-|-|
| `run_id` | string | yes | UUID v4 of the parent scheduled run. |
| `entry_id` | string | yes | UUID v4 of this individual agent invocation. |
| `parent_entry_id` | string | no | If this is a sub-task spawned by Atomizer, the parent's `entry_id`. |
| `agent_name` | string | yes | Must exist in `agents/registry.yaml`. |
| `project_id` | string | yes | The project being acted on. |
| `task_id` | string | yes | Stable identifier for the unit of work. |
| `inputs` | array<string> | yes | Repo-relative input artifact paths. |
| `outputs` | array<string> | yes | Repo-relative output artifact paths. |
| `backend` | enum | yes | `dartmouth`, `huggingface`, `local`. |
| `model_name` | string | yes | The model id used. |
| `prompt_version` | string | yes | Versioned identifier for the prompt template. |
| `started_at` | ISO 8601 | yes | UTC. |
| `ended_at` | ISO 8601 | yes | UTC. |
| `outcome` | enum | yes | `success`, `failed`, `skipped`, `quarantined`. |
| `failure_reason` | string | no | If `outcome != success`, a one-line reason. |
| `cost_estimate_usd` | number | yes | $0 by default; non-zero only for opt-in paid backends (FR-013). |

### Validation rules

- `ended_at` MUST be ≥ `started_at`.
- `cost_estimate_usd` MUST be exactly `0.0` unless an opt-in paid backend
  is active for that agent.
- Every line in a run-log file MUST share the same `run_id`.

## E6. Agent (registry record)

Declarative definition of one specialist agent.

**Storage**: One entry in `agents/registry.yaml`.
**Wire format**: [`contracts/agent-registry.schema.yaml`](contracts/agent-registry.schema.yaml).

| Field | Type | Required | Notes |
|-|-|-|-|
| `name` | string | yes | Unique. snake_case. |
| `purpose` | string | yes | One sentence. |
| `inputs` | array<enum> | yes | Subset of artifact `kind` values. |
| `outputs` | array<enum> | yes | Subset of artifact `kind` values. |
| `prompt_path` | string | yes | Repo-relative path under `agents/prompts/`. |
| `prompt_version` | string | yes | Semver. Bumped when prompt content changes. |
| `default_backend` | enum | yes | `dartmouth`, `huggingface`, `local`. |
| `fallback_backends` | array<enum> | yes | Ordered list. |
| `default_model` | string | yes | Resolved at runtime against `list()` (FR-031). |
| `tools` | array<string> | no | Names of in-process tool functions the agent may call. |
| `wall_clock_budget_seconds` | int | yes | The leaf-task budget. Default 300. |
| `paid_opt_in` | bool | yes | Default `false`. Must be `true` to use any non-free backend. |

### Validation rules

- `name` is unique across the registry.
- `inputs` and `outputs` are non-empty for every agent except
  Status-Reporter (which produces a side-effect comment, not an
  artifact) and Advancement-Evaluator (which only mutates project state).
- `paid_opt_in` MUST be `false` for every agent in the v1 registry
  (Principle IV; SC-002).
- `prompt_path` MUST point to a file that exists.
- `wall_clock_budget_seconds` MUST be ≤ 1800 (well under the runner's
  6-hour ceiling, leaving room for many leaves per run).

## E7. Backend

A configured LLM service.

**Storage**: One entry in `agents/registry.yaml` under `backends:`.

| Field | Type | Required | Notes |
|-|-|-|-|
| `name` | string | yes | `dartmouth`, `huggingface`, `local`. |
| `kind` | enum | yes | `openai_compatible`, `hf_inference`, `local_transformers`. |
| `auth_env_vars` | array<string> | yes | e.g., `["DARTMOUTH_CHAT_API_KEY"]`. |
| `base_url` | string | no | For `openai_compatible`. |
| `daily_quota_estimate` | int | no | Soft estimate used by scheduler to throttle. |
| `is_paid` | bool | yes | `false` for every v1 backend. |

## E8. Citation

An external reference attached to an artifact, with verification status.

**Storage**: `state/citations/<PROJ-ID>.yaml` (list).
**Wire format**: [`contracts/citation.schema.yaml`](contracts/citation.schema.yaml).

| Field | Type | Required | Notes |
|-|-|-|-|
| `cite_id` | string | yes | Stable id. |
| `artifact_path` | string | yes | The artifact in which this citation appears. |
| `artifact_hash` | string | yes | Hash at validation time. |
| `kind` | enum | yes | `url`, `arxiv`, `doi`, `dataset`. |
| `value` | string | yes | The cited identifier or URL. |
| `cited_title` | string | no | Title as it appears in the artifact. |
| `cited_authors` | array<string> | no | Authors as they appear in the artifact. |
| `verification_status` | enum | yes | `verified`, `unreachable`, `mismatch`, `pending`. |
| `verified_against_url` | string | no | The URL the validator fetched. |
| `fetched_title` | string | no | Title from the primary source. |
| `verified_at` | ISO 8601 | no | UTC. |

### Validation rules

- A `verification_status` of `verified` requires both
  `fetched_title` non-empty AND case-insensitive token-overlap with
  `cited_title` ≥ 0.7 (per Principle II — match, not just reachability).
- A project MUST NOT advance to `done` while any of its citations are
  in `unreachable` or `mismatch` status (FR-020).

## E9. Lock

Per-project advisory lock preventing concurrent mutating runs.

**Storage**: `state/locks/<PROJ-ID>.lock` (zero-byte sentinel; absence =
unlocked).

| Field | Type | Required | Notes |
|-|-|-|-|
| `project_id` | string | yes | Implicit in filename. |
| `holder_run_id` | string | yes | The `run_id` that holds the lock. Stored in file content (one line). |
| `acquired_at` | ISO 8601 | yes | UTC. Stored in file content. |
| `expires_at` | ISO 8601 | yes | `acquired_at + workflow timeout`. Stored in file content. |

### Acquisition protocol

1. Read the file. If absent → write the file with current run id and
   timestamps, commit, push.
2. If present and `expires_at` is in the past → forcibly release (treat
   as crashed prior run), then acquire as in step 1.
3. If present and not expired → skip this project this run.

## E10. Task (and Atomization Tree)

A unit of work assigned to an agent.

**Storage**: Embedded in run-log entries via `task_id` and
`parent_entry_id`. The atomization tree is reconstructable by walking
`parent_entry_id` references.

| Field | Type | Required | Notes |
|-|-|-|-|
| `task_id` | string | yes | UUID v4. |
| `parent_task_id` | string | no | Null for top-level tasks. |
| `agent_name` | string | yes | The agent assigned to this task. |
| `project_id` | string | yes | |
| `wall_clock_estimate_seconds` | int | yes | Set by the Atomizer (or by the scheduler for non-atomized tasks). |
| `inputs` | array<string> | yes | Same shape as run-log `inputs`. |
| `expected_outputs` | array<string> | yes | Declared outputs the Joiner expects. |
| `is_leaf` | bool | yes | `true` if no further atomization is needed. |
| `siblings_total` | int | no | If part of an atomized set, the total number of siblings (used by Joiner to know when to fire). |

### Atomization invariants

- Every leaf task's `wall_clock_estimate_seconds` ≤ the agent's
  `wall_clock_budget_seconds` (FR-032).
- A non-leaf task's `expected_outputs` MUST be reconstructable by
  concatenating/merging its children's `expected_outputs`; the Joiner
  uses this contract to perform the merge.
- The Joiner is automatically scheduled when the run-log shows every
  sibling task in the set has reached `outcome=success`. The Joiner
  emits a single run-log entry that lists every sibling's `task_id`
  in its `inputs` field.

## Cross-entity invariants

- Every Run-Log Entry's `project_id` and `agent_name` MUST exist
  (project file present in `state/projects/`, agent in
  `agents/registry.yaml`).
- A Project's `current_stage` MUST be reachable from the union of its
  Review Records and Citations: the Advancement-Evaluator Agent is the
  ONLY writer of `current_stage`, and its rule set is checked in
  `tests/contract/test_advancement_invariants.py`.
- Every Artifact referenced by a Review Record's `artifact_path` MUST
  exist; stale review records are flagged at preflight.
