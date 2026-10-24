# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The evidence only confirms the existence of the project root `projects/PROJ-040-robustness-of-statistical-tests-to-data-`; it does not show that the required sub‑directories (`code/data`, `code/utils`, `code/viz`, `tests`, `data/raw`, `data/processed`, `data/results`, `docs`) were actually created. These directories must be present (and non‑empty where appropriate) to satisfy the task.
- **T005** — the task writes platform-owned path(s) inside the project: `state/projects/PROJ-040-robustness-of-statistical-tests-to-data-.yaml` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T006** — The collector shows `code/viz/` is missing, while all other required directories exist. The task demands the full directory structure, so the absent `code/viz/` directory makes the implementation incomplete.
