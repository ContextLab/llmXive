# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T004** — No linting/formatting configuration files (e.g., `pyproject.toml` with ruff/black settings, `.pre-commit-config.yaml`, or installed hook scripts) are present or referenced, so the required setup for ruff, black, and pre‑commit hooks is missing. The task therefore is not satisfied.
- **T005** — No `config.py` file or its contents are present in the provided evidence; the required path definitions and random seed pinning are not demonstrated. The implementer must add a non‑empty `config.py` that defines the specified data directories and sets a fixed random seed.
- **T007** — declared artifact(s) missing/empty/invalid: state.yaml
- **T011** — The required artifact `tests/unit/test_ingest.py` does not exist on disk, so no unit tests for URL validation and CSV parsing are present. The task cannot be considered completed until this file is created with appropriate test cases.
- **T012** — The required file `tests/integration/test_ingest_integration.py` is missing from the repository, so no integration test for missing image handling exists. The task’s primary artifact is absent, making the claim unsubstantiated.
- **T016** — No code, script, log, or data artifact demonstrating the fallback linkage derivation was provided; there is no evidence that trials are mapped to stimulus IDs, that a >10% failure rate triggers the required halt, or that the proportion of successfully linked trials meets SC‑001. The implementer must supply the implementation (e.g., a Python module or script) and output showing the mapping results and the halt condition when applicable.
- **T017** — declared artifact(s) missing/empty/invalid: data/processed/linked_trials.csv
- **T018** — declared artifact(s) missing/empty/invalid: state.yaml
- **T023** — The repository lacks the required `data/processed/confounding_report.json` file, and the shown `code/data/preprocess.py` does not contain any implementation of a confounding check or generation of a correlation matrix/report. Consequently, the task’s deliverable is missing and the code does not fulfill the specified requirement.
