# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — No linting or formatting configuration files (e.g., `.ruff.toml`, `.flake8`, `pyproject.toml` with Black settings) or setup scripts are present in the provided evidence, so the requirement to configure ruff/flake8 and Black is not satisfied. The implementer must add the appropriate configuration files and ensure they are integrated into the project.
- **T004** — No evidence was provided showing that the required directories (`data/raw/`, `data/processed/`, `state/projects/`) actually exist or contain any files; the claim is unsubstantiated. The implementer must create and demonstrate the presence of these directories (and optionally include placeholder files) to satisfy the task.
- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T008** — The provided evidence only describes election poll aggregation features and contains no code, script, or files that compute SHA‑256 hashes or modify `state/projects/PROJ-206-*.yaml`. The required state‑management utility and its YAML updates are entirely missing.
- **T015** — declared artifact(s) missing/empty/invalid: src/main.py
- **T016** — No evidence of modified `src/data/` scripts, no hash generation logic, and no updated `state/projects/PROJ-206-*.yaml` files were provided. The required artifacts are missing, so the task is not satisfied.
