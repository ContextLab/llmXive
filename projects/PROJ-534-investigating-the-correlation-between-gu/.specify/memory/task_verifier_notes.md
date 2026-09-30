# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence of the required directories (`src/`, `tests/`, `data/raw`, `data/processed`, `data/results`, `logs/`) is provided; the claim cannot be verified without actual filesystem artifacts.
- **T003** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T004** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T005** — declared artifact(s) missing/empty/invalid: src/utils/config.py
- **T006** — No pytest configuration file (e.g., `pytest.ini` or `pyproject.toml` with pytest settings) or test directory structure (e.g., `tests/` with `__init__.py` and sample test modules) was presented. The required artifacts to satisfy task T006 are missing.
- **T008** — declared artifact(s) missing/empty/invalid: src/data/synthetic_gen.py, data/raw/synthetic_data.csv, schema.yaml
- **T009** — declared artifact(s) missing/empty/invalid: data/raw/synthetic_data.csv, schema.yaml
- **T010** — declared artifact(s) missing/empty/invalid: src/data/ingestion.py, data/raw/synthetic_data.csv, schema.yaml
- **T011** — The repository contains a partially‑implemented `src/data/filtering.py` that defines the filtering logic, but the file is truncated and does not include any code that writes the filtered DataFrame to `data/processed/filtered_cohort.csv`. Moreover, the required output CSV is absent from the project directory. The task’s core requirement—to produce and save the filtered cohort file—is therefore not satisfied.
- **T013** — The `filtering.py` file is truncated and does not show the actual listwise‑deletion logic nor a log statement writing the dropped‑row count to `logs/filtering.log`. Moreover, the required schema file `contracts/dataset.schema.yaml` is missing, so we cannot confirm the covariate list matches the specification. The task therefore remains unfinished.
- **T016** — The required `data/processed/filtered_cohort.csv` file does not exist, and the referenced `contracts/dataset.schema.yaml` (or `schema.yaml`) is also missing. Moreover, the provided test script is incomplete (truncated) and does not actually load and validate the CSV against the schema or check the required non‑null fields. The task’s core artifacts are absent, so the requirement is not satisfied.
- **T017** — declared artifact(s) missing/empty/invalid: src/analysis/diversity.py
- **T018** — declared artifact(s) missing/empty/invalid: src/analysis/correlation.py
- **T019** — declared artifact(s) missing/empty/invalid: src/analysis/correlation.py
- **T020** — declared artifact(s) missing/empty/invalid: src/analysis/beta_diversity.py
