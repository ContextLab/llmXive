# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The `tests/test_scaffolding.py` file is missing, and the required sub‑folders `data/raw` and `data/processed` are not present in the listed project contents. Without these artifacts the scaffold verification cannot succeed.
- **T004** — the task writes platform-owned path(s) inside the project: `state/...yaml` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T007** — Requested task execution failed; rerun successfully: code/main.py exit=1
