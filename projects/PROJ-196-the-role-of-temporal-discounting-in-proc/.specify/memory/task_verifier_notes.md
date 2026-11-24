# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The project root contains `data/raw`, `code`, `tests`, and `docs`, and the scaffold test file is present, but there is no evidence that the required `data/processed` sub‑folder actually exists (empty directories are not listed). Adding an empty `data/processed` directory is needed to satisfy the task.
- **T004** — the task writes platform-owned path(s) inside the project: `state/...yaml` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T007** — Requested task execution failed; rerun successfully: code/main.py exit=1
