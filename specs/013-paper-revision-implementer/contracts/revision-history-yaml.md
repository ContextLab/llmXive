# Contract — `projects/<PROJ-ID>/paper/revision_history.yaml`

Append-only summary of every implementer round across the paper's
lifetime (FR-009). One entry per round. Lives alongside the paper
artifacts so it travels with the project on any export.

This is a SUMMARY of what's in
`specs/auto-revisions/<PROJ-ID>/round-<N>/implementer-log.yaml`; the
per-task detail stays in the per-round log. `revision_history.yaml` is
optimized for "what rounds happened?" queries from the dashboard, the
publisher, and the post-paper appendix renderer.

## Schema

```yaml
schema_version: "1"
project_id: "PROJ-578-https-arxiv-org-abs-2605-14906"

# One entry per round. Append-only.
rounds:
  - round_number: 1
    ran_at: "2026-05-19T10:14:00Z"
    implementer_agent: "llmXive-implementer-v1.0"
    canonical_identity: "llmXive-implementer-v1.0 (qwen.qwen3.5-122b on dartmouth, 2026-05-19)"
    tasks_done: 113
    tasks_failed: 3            # compile-failed + file-not-found + needs-external-data
    tasks_skipped: 0
    resulting_pdf_sha256: "abc123..."   # null if compile-after-all-tasks-failed
    implementer_log_path: "specs/auto-revisions/PROJ-578-.../round-1/implementer-log.yaml"
    task_outcomes:             # summary only — id, severity, status, short text
      - {id: "a46d18f9a8b0", severity: "writing", status: "done",
         text: "Provide verification_status for all citations in state/citations"}
      - {id: "ae329aa3f800", severity: "writing", status: "compile-failed",
         text: "Verify GPT-5.4 and Gemini-3.1-Pro citations"}
      - ...
  - round_number: 2
    ran_at: "2026-05-20T09:00:00Z"
    ...
```

## Invariants

- `schema_version` is `"1"`.
- `rounds` is strictly append-only — entries are never removed or
  reordered. New rounds always have `round_number == max(existing) + 1`.
- `rounds[i].task_outcomes` length matches the corresponding
  `implementer-log.yaml::task_outcomes` length.
- `tasks_done + tasks_failed + tasks_skipped` equals the round's
  `total_tasks`.
- `resulting_pdf_sha256` is null IFF the recompile after all tasks
  failed (FR-012); otherwise it matches the SHA-256 of the PDF at the
  path stored in the project's metadata.

## Consumers

- **publisher agent** — reads to determine the 2-state vs 3-state
  status badge (FR-022).
- **post-paper appendix renderer** (`gen_appendix.py`) — reads to
  render the "Revision history" section in the published PDF.
- **dashboard** — reads to render the per-round summary on the project
  modal (FR-020).
- **3-consecutive-zero detector** (FR-015) — reads the last 3 rounds'
  `tasks_done` counts.

## Reader API

```python
# src/llmxive/state/revision_history.py
def load(project_id: str, *, repo_root: Path) -> RevisionHistory: ...
def append_round(project_id: str, round: RevisionRound, *, repo_root: Path) -> None: ...
def last_n_rounds(project_id: str, n: int, *, repo_root: Path) -> list[RevisionRound]: ...
```

`append_round()` is atomic (tmpfile + rename) and idempotent on
`round_number` — calling it twice with the same round number raises
`ValueError("round N already recorded")`.
