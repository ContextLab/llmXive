# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003b** — The task requires a code linting configuration file (e.g., `.flake8` or equivalent) with a standard max-line-length and E501 ignored, but the evidence collector found no artifact at any path — no configuration file exists in the project. The implementer must create the linting config (e.g., a `setup.cfg`/`.flake8` with `max-line-length = 100` (or similar standard limit) and `extend-ignore = E501`) in the project root.
- **T007** — the task writes platform-owned path(s) inside the project: `state/projects/PROJ-066-investigating-correlations-between-molec.yaml` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
