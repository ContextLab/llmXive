# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No project files, directory tree, or any code/scripts were presented; the claim provides only the original specification without the required artifact (the created project structure). Consequently, the required output does not exist.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml` with Black settings, `.ruff.toml` or a `ruff` section, or a pre‑commit hook file) were presented, nor any evidence that ruff and Black have been installed or integrated into the project. Without these artifacts the requirement to configure linting (ruff) and formatting (black) is not satisfied.
- **T004** — No `pytest` configuration file (e.g., `pytest.ini`, `conftest.py`) or test directory (e.g., `tests/` with test modules) was found in the provided artifacts, so the required setup is missing.
- **T005** — declared artifact(s) missing/empty/invalid: src/utils/logger.py
- **T006** — declared artifact(s) missing/empty/invalid: src/utils/power_analysis.py
- **T006b** — declared artifact(s) missing/empty/invalid: src/utils/power_analysis.py, data/processed/results/power_analysis_report.tsv
- **T007** — declared artifact(s) missing/empty/invalid: src/preprocessing/id_generator.py
- **T008** — No evidence of the required directories (`data/raw/`, `data/processed/`, `data/processed/results/`) being created is provided; the artifact list is empty, so the task’s core deliverable is missing.
- **T009** — declared artifact(s) missing/empty/invalid: src/preprocessing/covariate_handler.py, src/utils/logger.py
- **T011** — The required file `tests/integration/test_pipeline.py` does not exist, so no integration test for the ingestion pipeline is present. Without this artifact, the task’s requirement is not satisfied.
- **T012** — declared artifact(s) missing/empty/invalid: src/ingestion/agp_loader.py
- **T013** — declared artifact(s) missing/empty/invalid: src/ingestion/ukbb_loader.py
- **T014** — declared artifact(s) missing/empty/invalid: src/ingestion/harmonizer.py
- **T015** — No code, script, or configuration file was presented that adds validation logic to prevent PII leakage or records checksums in the `state/` directory. The required artifact is missing, so the task’s requirement is not satisfied.
