# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence was provided that the required directories (`code/`, `data/`, `tests/`, `state/`) actually exist or contain any files; the only material shown is a feature specification, not a project skeleton. The implementer must create and show the specified folder structure.
- **T003** — No linting or formatting configuration artifacts (e.g., .flake8, pyproject.toml, ruff.toml, black configuration, or pre‑commit setup) were supplied, so the claim that linting (flake8/ruff) and formatting (black) are configured is unsupported.
- **T004** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T005** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T006** — No evidence of a `data/` directory with the required `raw/` and `processed/` subfolders, nor any checksum scripts, was provided. The implementer must add the directory structure and the scripts that compute and verify file checksums.
- **T016** — The repository contains `code/data/preprocess.py` with mean‑imputation code, but the required `data/validation_report.json` file is absent, and the visible portion of the script does not show the “halt execution” logic that writes this report when >5 % of records miss a critical variable. The task’s validation‑report generation requirement is therefore unmet.
- **T017** — declared artifact(s) missing/empty/invalid: data/processed/features.parquet, schema.yaml
- **T019** — The required file `tests/integration/test_simulation_loop.py` is missing from the repository, so the integration test for the simulation loop does not exist. No artifact fulfills the task’s requirement.
- **T020** — No evidence of a `code/simulation/convolve_ref/` directory containing a concrete CONVOLVE implementation (with a specific commit/tag) was provided; the required artifact is missing, so the task is not satisfied.
- **T021** — declared artifact(s) missing/empty/invalid: code/simulation/run_baseline.py
- **T022** — declared artifact(s) missing/empty/invalid: code/models/evaluate.py
- **T024** — declared artifact(s) missing/empty/invalid: data/results/baseline_comparison.json
