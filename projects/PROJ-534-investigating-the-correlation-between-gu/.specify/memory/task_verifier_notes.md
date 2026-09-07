# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No directory structure (`src/`, `tests/`, `data/raw`, `data/processed`, `data/results`) is shown or referenced in the provided artifacts; the implementer only supplied a feature specification without any file system evidence. The required folders are missing.
- **T002** — No linting or formatting configuration files (e.g., `pyproject.toml` with ruff/black settings, `.ruff.toml`, or a pre‑commit hook) were supplied, nor any evidence that the tools have been installed or integrated into the project. The required artifacts to demonstrate that ruff and black are configured are missing.
- **T003** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T004** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T005** — declared artifact(s) missing/empty/invalid: src/utils/config.py
- **T006** — No pytest configuration file (e.g., `pytest.ini` or `pyproject.toml` with pytest settings) or test directory (e.g., `tests/` with placeholder test modules) was provided. Without these artifacts the requirement to set up pytest and its test structure is not satisfied.
- **T010** — The required `data/processed/filtered_cohort.csv` file does not exist, and the referenced schema file `contracts/dataset.schema.yaml` (or `schema.yaml`) is also missing, so the contract test cannot actually validate anything. The test script is present but without the data and schema it cannot be executed, meaning the task’s core requirement is unmet.
- **T011** — declared artifact(s) missing/empty/invalid: src/data/synthetic_gen.py
- **T012** — declared artifact(s) missing/empty/invalid: src/data/ingestion.py
- **T013** — declared artifact(s) missing/empty/invalid: src/data/filtering.py
- **T014** — declared artifact(s) missing/empty/invalid: src/data/filtering.py
- **T015** — The required file `src/data/filtering.py` does not exist, so no logic, imputation handling, or logging has been implemented. The task’s core artifact is missing entirely.
- **T016** — The required artifact `tests/unit/test_diversity.py` does not exist on disk, so no unit tests for Shannon, Simpson, or Chao1 calculations are present. The task cannot be considered fulfilled until this file is created with appropriate test cases.
- **T017** — The required artifact `tests/unit/test_correlation.py` does not exist, so no unit test code is present to verify the Pearson/Spearman auto‑switch logic or its logging. The task therefore remains unfulfilled.
- **T018** — The required artifact `tests/unit/test_correlation.py` does not exist on disk, so no unit test for the Benjamini‑Hochberg correction was provided. The task remains undone.
- **T027** — The required output file `data/results/correlation_results.json` does not exist, and the schema file `contracts/analysis_output.schema.yaml` (or `schema.yaml`) is also missing, so the contract test cannot actually validate anything. The present test script is incomplete (truncated) and cannot run against the absent artifacts.
- **T019** — declared artifact(s) missing/empty/invalid: src/analysis/diversity.py
- **T020** — declared artifact(s) missing/empty/invalid: src/analysis/correlation.py
