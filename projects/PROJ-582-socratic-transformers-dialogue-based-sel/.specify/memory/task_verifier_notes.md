# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — Checked `code/requirements.txt` (lists all required packages plus extras) and `code/pyproject.toml` (contains the required metadata and `[tool.black]`/`[tool.ruff]` sections). The `code/ruff.toml` file exists but does **not** contain any configuration that explicitly targets the `src/` and `tests/` directories, as the task requires. Add the appropriate directory targeting (e.g., `src = ["src"]` and `tests = ["tests"]` or equivalent) to satisfy the requirement.
- **T003** — Requested task execution failed; rerun successfully: code/src/data/download.py exit=1
