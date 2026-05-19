# Contract — `llmXive-implementer` agent

## Trigger

The implementer runs as part of the regular `llmxive run` scheduler
tick. The scheduler picks projects whose `current_stage ==
READY_FOR_IMPLEMENTATION` (FR-001). `READY_FOR_IMPLEMENTATION` is
removed from `scheduler._NEVER_PICK` as part of this spec.

## Inputs

| Field | Source | Required |
|-|-|-|
| `project_id` | `Project.id` | yes |
| `revision_spec_path` | `Project.revision_spec_path` (set by `revision_planner` in spec 012) | yes; null → no-op |
| `paper/source/main.tex` | filesystem | yes |
| `paper/metadata.json` | filesystem | yes |
| revision spec `tasks.md` | `<revision_spec_path>/tasks.md` | yes |
| revision spec action items | `<revision_spec_path>/*.md` (one per action item) | yes |

## Per-task loop (FR-003)

For each task in `tasks.md`, in document order:

1. **Read** the action item file referenced by the task.
2. **Locate** the relevant manuscript section via keyword / section title / quoted phrase. The LLM prompt receives the action item text + a windowed view of the current `main.tex`.
3. **Generate** the edit. The LLM MUST emit either a `search_and_replace` or `unified_diff` block (research.md §2). Free-form whole-file rewrites are rejected (FR-005).
4. **Validate** the edit pre-flight (research.md §2 pre-flight checks). On reject → record as `skipped`, continue.
5. **Snapshot** the affected files: `before_bytes` + `before_hash` (research.md §3).
6. **Apply** the edit.
7. **Compile** the manuscript via the existing LaTeX build pipeline. On compile-success → record `done`. On compile-failure → restore `before_bytes`, record `compile-failed`.
8. **Append** the outcome to `specs/auto-revisions/<PROJ-ID>/round-<N>/implementer-log.yaml`.

## Post-loop steps (FR-006..FR-013)

After all tasks are processed:

1. **If ≥1 task succeeded**:
   - Append a new `AuthorEntry` (kind=llm) to `paper/metadata.json::authors` if this implementer's `(name, agent_version)` isn't already present (FR-008).
   - Update the LaTeX `\author{}` block in `main.tex` to reflect the new author list (FR-007).
   - Recompile the manuscript (FR-010). The output replaces `paper/pdf/main.pdf`.
   - Compute `resulting_pdf_sha256` and append a `RevisionRound` entry to `paper/revision_history.yaml` (FR-009).
2. **If 0 tasks succeeded**:
   - Increment a per-project `consecutive_zero_round_count` counter (stored under `state/<id>.implementer.yaml`).
   - If counter hits 3 → transition to `PAPER_REVISION_BLOCKED` (FR-015) with a diagnostic record; do NOT route to PAPER_REVIEW.
3. **Clear** `Project.revision_spec_path` (FR-014).
4. **Transition** `current_stage`: `READY_FOR_IMPLEMENTATION → PAPER_REVIEW` (FR-013).

## Outputs

| Path | Written | Notes |
|-|-|-|
| `specs/auto-revisions/<PROJ-ID>/round-<N>/implementer-log.yaml` | always | per-task outcomes |
| `projects/<PROJ-ID>/paper/source/main.tex` (and other source files) | on ≥1 successful task | edits applied in place |
| `projects/<PROJ-ID>/paper/metadata.json` | on ≥1 successful task | authors extended (FR-006); no other fields touched (FR-016) |
| `projects/<PROJ-ID>/paper/revision_history.yaml` | on ≥1 successful task | new round appended (FR-009) |
| `projects/<PROJ-ID>/paper/pdf/main.pdf` | on successful recompile | replaces existing PDF (FR-010); NOT replaced if compile-after-rollback fails (FR-012) |
| run-log entry | always | `agent_name: llmXive-implementer`, `outcome: success` (even if some tasks failed) |

## Invariants

- **Authors append-only** (FR-008). Existing entries never modified or deleted.
- **`paper/metadata.json`** — only `authors` and `revision_history` reference fields may change (FR-016).
- **Section deletions prohibited** (FR-017). Abstract, bibliography, whole sections are never removed.
- **Compile gate** — every edit is followed by a recompile; failures roll back (FR-003 step f, FR-012).
- **State transition is unconditional** — `READY_FOR_IMPLEMENTATION → PAPER_REVIEW` fires once the loop completes, regardless of per-task outcomes (except the 3-consecutive-zero failsafe in FR-015).

## Failure modes

| Failure | Detection | Response |
|-|-|-|
| LLM returns malformed edit | pre-flight reject | task → `skipped`, continue |
| `search_and_replace` ambiguous (multiple matches) | pre-flight reject | task → `skipped`, continue |
| `unified_diff` doesn't apply | `git apply --check` | task → `skipped`, continue |
| LaTeX compile fails after edit | build pipeline exit nonzero | rollback files, task → `compile-failed`, continue |
| File referenced by task doesn't exist | filesystem check before edit | task → `file-not-found`, continue |
| Implementer hits wall-clock budget mid-round | budget exceeded | commit completed tasks, do NOT transition stage; next tick resumes |
| 3 consecutive rounds with 0 successes | `consecutive_zero_round_count == 3` | transition to `PAPER_REVISION_BLOCKED` (FR-015) |
