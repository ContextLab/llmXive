# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003b** — The file `code/pyproject.toml` exists with a `[tool.black]` section and `line-length = 88`, but the `target-version` is `['py38', 'py39', 'py310', 'py311']` instead of the required `['py3']`. The task's stated requirement is not met exactly; the implementer should set `target-version = ['py3']` (or the task owner should amend the requirement if the expanded list is intended).
- **T007** — Requested task execution failed; rerun successfully: code/ingest.py exit=1
