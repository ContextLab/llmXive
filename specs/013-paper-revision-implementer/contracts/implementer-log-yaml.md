# Contract — `specs/auto-revisions/<PROJ-ID>/round-<N>/implementer-log.yaml`

Per-round changelog written by the `llmXive-implementer` agent
(FR-004). One file per implementer round; rounds are 1-indexed and
match the round directory name (`round-1`, `round-2`, …).

## Schema

```yaml
schema_version: "1"
round_number: 1
project_id: "PROJ-578-https-arxiv-org-abs-2605-14906"
revision_spec_path: "specs/auto-revisions/PROJ-578-.../round-1/"

# Agent identity (FR-004)
implementer_agent: "llmXive-implementer-v1.0"   # name only (dedupe key part 1)
agent_version: "1.0.0"                          # dedupe key part 2
model_name: "qwen.qwen3.5-122b"
backend: "dartmouth"
canonical_identity: "llmXive-implementer-v1.0 (qwen.qwen3.5-122b on dartmouth, 2026-05-19)"

# Run metadata
started_at: "2026-05-19T09:50:00Z"
ended_at:   "2026-05-19T10:14:00Z"
duration_s: 1440.0
exit_reason: "all-tasks-processed"   # or "wall-clock-budget-exceeded"

# Round summary
total_tasks: 116
tasks_done: 113
tasks_compile_failed: 3
tasks_file_not_found: 0
tasks_skipped: 0
tasks_needs_external_data: 0

# Recompile of the manuscript at end of round (FR-010)
final_compile:
  attempted: true
  succeeded: true
  resulting_pdf_sha256: "abc123..."
  resulting_pdf_bytes: 2295450

# Author addition (FR-006..FR-008)
author_added: true   # false if this implementer was already in the list
author_entry:
  name: "llmXive-implementer-v1.0"
  kind: "llm"
  agent_version: "1.0.0"
  model_name: "qwen.qwen3.5-122b"
  backend: "dartmouth"
  first_contributed_at: "2026-05-19T10:14:00Z"

# Per-task outcomes (one entry per task in the round's tasks.md, in document order)
task_outcomes:
  - task_id: "a46d18f9a8b0"
    action_item_severity: "writing"
    action_item_text: "Provide verification_status for all citations in state/citations"
    status: "done"
    edit_kind: "search_and_replace"  # or "unified_diff"
    files_modified: ["paper/source/main.tex"]
    before_hashes:
      "paper/source/main.tex": "a1b2c3..."
    after_hashes:
      "paper/source/main.tex": "d4e5f6..."
    model_response_excerpt: |
      Replacing the unverified citation block at line 234 with the
      verified-status table. Edit: search_and_replace, single match.
    duration_s: 4.2
    error_reason: null
  - task_id: "ae329aa3f800"
    action_item_severity: "writing"
    action_item_text: "Verify GPT-5.4 and Gemini-3.1-Pro citations"
    status: "compile-failed"
    edit_kind: "search_and_replace"
    files_modified: ["paper/source/main.tex"]
    before_hashes:
      "paper/source/main.tex": "d4e5f6..."
    after_hashes: {}    # empty because rolled back
    model_response_excerpt: |
      Adding new \citep{} for GPT-5.4 system card...
    duration_s: 12.7
    error_reason: "lualatex exit 1: Undefined control sequence \\citepp"
  - ...
```

## Invariants

- `schema_version` is `"1"`; bump on backwards-incompatible changes.
- `round_number` matches the parent directory name.
- `task_outcomes` length == `total_tasks` (every task accounted for).
- `tasks_done + tasks_compile_failed + tasks_file_not_found + tasks_skipped + tasks_needs_external_data == total_tasks`.
- `task_outcomes[i].before_hashes` is non-empty for every task that was attempted (so we have an audit trail of the file state before each edit).
- `task_outcomes[i].after_hashes` is empty IFF the task was rolled back (`compile-failed`) or never applied (`skipped`, `file-not-found`).
- The file is written ONCE at the end of the round (atomic write — tmpfile + rename).

## Reader API

```python
# src/llmxive/state/revision_history.py (the same module owns this artifact + revision_history.yaml)
def load_round(project_id: str, round_number: int, *, repo_root: Path) -> ImplementerLog: ...
def save_round(project_id: str, round_number: int, log: ImplementerLog, *, repo_root: Path) -> None: ...
def list_rounds(project_id: str, *, repo_root: Path) -> list[int]: ...
```
