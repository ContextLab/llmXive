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
- **T011** — declared artifact(s) missing/empty/invalid: src/data/filtering.py, data/processed/filtered_cohort.csv
- **T012** — declared artifact(s) missing/empty/invalid: src/data/filtering.py
- **T013** — The required file `src/data/filtering.py` does not exist, and the schema file `contracts/dataset.schema.yaml` (or `schema.yaml`) is also missing, so no listwise‑deletion logic or logging can be present. The implementer must add the filtering module and the schema definition to satisfy the task.
