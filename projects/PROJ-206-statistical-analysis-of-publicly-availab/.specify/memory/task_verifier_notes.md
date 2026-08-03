# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — No linting or formatting configuration files (e.g., `.ruff.toml`, `.flake8`, `pyproject.toml` with Black settings) or setup scripts are present in the provided evidence, so the requirement to configure ruff/flake8 and Black is not satisfied. The implementer must add the appropriate configuration files and ensure they are integrated into the project.
- **T004** — No evidence was provided showing that the required directories (`data/raw/`, `data/processed/`, `state/projects/`) actually exist or contain any files; the claim is unsubstantiated. The implementer must create and demonstrate the presence of these directories (and optionally include placeholder files) to satisfy the task.
- **T006** — declared artifact(s) missing/empty/invalid: src/utils/logging.py
- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T008** — The provided evidence only describes election poll aggregation features and contains no code, script, or files that compute SHA‑256 hashes or modify `state/projects/PROJ-206-*.yaml`. The required state‑management utility and its YAML updates are entirely missing.
- **T010** — declared artifact(s) missing/empty/invalid: src/data/harmonize.py
- **T011** — declared artifact(s) missing/empty/invalid: src/data/weights.py
- **T012** — declared artifact(s) missing/empty/invalid: src/data/weights.py
- **T013** — declared artifact(s) missing/empty/invalid: src/data/harmonize.py
- **T014** — declared artifact(s) missing/empty/invalid: src/data/harmonize.py
- **T015** — declared artifact(s) missing/empty/invalid: src/main.py
- **T016** — No evidence of modified `src/data/` scripts, no hash generation logic, and no updated `state/projects/PROJ-206-*.yaml` files were provided. The required artifacts are missing, so the task is not satisfied.
- **T017** — declared artifact(s) missing/empty/invalid: src/models/frequentist.py
- **T018** — declared artifact(s) missing/empty/invalid: src/models/frequentist.py
- **T019** — declared artifact(s) missing/empty/invalid: src/evaluation/metrics.py
- **T022** — No code, script, or configuration file is provided that sets up a PyMC NUTS sampler to run on CPU‑only, specifies the number of tuning steps, or fixes random seeds. The required artifact is missing, so the task is not satisfied.
- **T028** — The implementer supplied no code, documentation, or example report demonstrating the added logic to frame findings as “predictive accuracy” and “associational uncertainty.” Without any artifact (e.g., modified report generation script, sample output, or test showing the new phrasing), the task requirement is not met. The missing deliverable is the implementation and evidence of the new framing in the output reports.
