# Per-task edit-generation prompt (spec 013 / FR-018)

## Project context

- **Project**: {{project_id}}
- **Round**: {{round_number}}
- **Revision spec**: `{{revision_spec_path}}`

## Action item

- **Task ID**: `{{task_id}}`
- **Severity**: `{{severity}}`
- **Text**: {{action_item_text}}

## Current manuscript (windowed)

The relevant section of `paper/source/main.tex` (and any other relevant files) is included below. Lines are numbered to help you locate the edit target.

```latex
{{manuscript_window}}
```

## Your task

Produce EXACTLY ONE structured edit in JSON form that addresses this action item. See the system prompt for the allowed forms (`search_and_replace` or `unified_diff`).

Important reminders:

- **Output JSON only.** No prose, no markdown fences, no commentary.
- **Localized scope.** Address ONLY this action item; do not touch neighbouring content the reviewer did not flag.
- **`search` must match exactly once.** If the verbatim text appears multiple times in the file, include enough surrounding context to make the match unique.
- **No section/abstract/bibliography deletions.** Edits whose `replace` is empty AND that match `\begin{abstract}...\end{abstract}` or `\bibliography{...}` are rejected.
{{science_note}}

Emit your edit now.
