# Per-task RESEARCH-revision edit prompt

You are revising a **research-stage** project. There is **no paper manuscript yet** —
you edit the project's own research artifacts: source code under `code/`, specs under
`specs/`, reproducibility docs under `docs/`, and data descriptors under `data/`.

## Project context

- **Project**: {{project_id}}
- **Round**: {{round_number}}
- **Revision spec**: `{{revision_spec_path}}`

## Action item to address

- **Task ID**: `{{task_id}}`
- **Severity**: `{{severity}}`
- **Concern**: {{action_item_text}}

## Authored project files (your editable surface)

You may edit any file under `code/`, `specs/`, `docs/`, `data/`, or `tests/` (give the path
**project-relative**, e.g. `code/data/validator.py` or `docs/reproducibility/licenses.md`).

{{file_tree}}

## Target file (if the concern names one)

{{target_window}}

## Your task

Produce **EXACTLY ONE** structured edit in JSON form (see the system prompt for the
allowed `search_and_replace` / `unified_diff` forms) that addresses THIS action item:

- **Modify an existing file** → `search_and_replace` whose `search` matches the file
  text exactly once (copy it character-for-character, no line-number prefixes), or a
  `unified_diff`.
- **Create a new file** the concern says is missing (e.g. a license note, a small doc)
  → a `unified_diff` against `/dev/null` with the new file's full contents.
- **Relocate a misplaced file** the concern says is in the wrong place (e.g. "move
  logs/ to docs/reproducibility/", "checksums belong under data/") → `move_file`
  with `file` (current path) and `to` (new path).
- **Remove a redundant/duplicate file** the concern says to prune/consolidate (e.g.
  "consolidate the three checksum manifests") → `delete_file` with `file`.

Important reminders:

- **Output JSON only.** No prose, no markdown fences, no commentary.
- **Project-relative `file` path** under `code/`, `specs/`, `docs/`, `data/`, or `tests/`. Do NOT
  target `paper/…` — no paper exists at this stage.
- **Localized scope.** Address ONLY this action item; do not touch unrelated content.
- **`search` must match exactly once.** Include enough surrounding context to be unique.
- **Strip line-number prefixes.** The windows above show `NNN: <text>`; the `NNN: ` is
  NOT in the file. Your `search` must be the file text only.
- Prefer the SMALLEST real change that resolves the concern. If the concern is broad
  (e.g. "add type hints across modules"), make a concrete, correct edit to ONE file —
  the next round addresses the rest.

Emit your edit now.
