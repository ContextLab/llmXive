# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T012** — the task writes platform-owned path(s) inside the project: `state/projects/` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T007** — The `pyproject.toml` file is present with full content, but the required `.flake8` file, while listed, has no shown contents or size to confirm it is non‑empty; without evidence that it contains a linting configuration, the task’s requirement is not fully satisfied.
- **T051** — declared artifact(s) missing/empty/invalid: projects/PROJ-267-exploring-the-relationship-between-atmos/output/sensitivity_report.md
- **T011a** — Requested task execution failed; rerun successfully: code/01_fetch_coefficients.py exit=1
