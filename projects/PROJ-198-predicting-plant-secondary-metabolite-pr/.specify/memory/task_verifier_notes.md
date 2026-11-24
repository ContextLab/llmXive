# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The evidence includes `.ruff.toml` and `pyproject.toml`, but the required `.flake8` file and `.env.example` (with the placeholder keys) are missing, so the linting/formatting and env‑variable template requirements are not fully satisfied.
- **T005** — the task writes platform-owned path(s) inside the project: `state/` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T006** — Requested task execution failed; rerun successfully: code/data/download.py exit=1
