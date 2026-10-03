# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence was provided that the required directories (`code/`, `data/`, `tests/`, `state/`) actually exist or contain any files; the only material shown is a feature specification, not a project skeleton. The implementer must create and show the specified folder structure.
- **T003** — No linting or formatting configuration artifacts (e.g., .flake8, pyproject.toml, ruff.toml, black configuration, or pre‑commit setup) were supplied, so the claim that linting (flake8/ruff) and formatting (black) are configured is unsupported.
- **T004** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T005** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T006** — No evidence of a `data/` directory with the required `raw/` and `processed/` subfolders, nor any checksum scripts, was provided. The implementer must add the directory structure and the scripts that compute and verify file checksums.
- **T016** — The repository contains a `code/data/preprocess.py` file, but the visible code does not show any logic that writes a `data/validation_report.json` or halts execution when >5 % of records miss a critical variable, and the required `data/validation_report.json` file is absent. Consequently, the mean‑imputation and validation‑report requirements are not demonstrably fulfilled.
- **T017** — declared artifact(s) missing/empty/invalid: data/processed/features.parquet, schema.yaml
- **T021** — declared artifact(s) missing/empty/invalid: code/simulation/run_baseline.py
- **T022** — declared artifact(s) missing/empty/invalid: code/models/evaluate.py
- **T023** — No code, configuration, or log output was provided showing that the system now records the turn number and the full feature vector whenever the meta‑critic decides to abstain. Without concrete artifacts (e.g., updated source files, example log entries, or test output), the requirement is not satisfied.
- **T030** — declared artifact(s) missing/empty/invalid: data/results/statistical_report.md
- **T031** — No statistical analysis artifact (e.g., test results, p‑value, or report) is provided; without a computed Mann‑Whitney U/Kolmogorov‑Smirnov test showing median difference ≠ 0 and p < 0.05 for the token‑consumption reduction metric, the requirement is not satisfied. The implementer must supply the actual test output or a reproducible script and its results.
- **T032** — No documentation files or changes in `docs/` or `quickstart.md` were provided; the only artifact is a feature specification, which does not satisfy the required documentation updates. The implementer must add the actual updated documentation files.
