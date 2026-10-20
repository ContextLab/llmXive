# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — The `pyproject.toml` and `scripts/lint.sh` files exist with the correct required content (`[tool.black]` line-length 88, `[tool.ruff]` select E/F/W/C90, and the script runs `black --check .` then `ruff .`). However, the task's explicit verification requirement — that `bash scripts/lint.sh` exits with status 0 on the current code base — has no supporting execution evidence (no run log, exit status, or tool output), so there is no proof the lint check actually passes or that black/ruff are even installed. The implementer should run the script and provide its exit status/output as evidence.
- **T004** — Requested task execution failed; rerun successfully: code/download_pantheon.py exit=1
