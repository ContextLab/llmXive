# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No evidence was provided showing that the required directories (`code/`, `tests/`, `data/`, `docs/`) actually exist or contain any files; without such artifacts the claim that the project structure was created cannot be verified.
- **T003** — declared artifact(s) missing/empty/invalid: pre-commit-config.yaml
- **T004** — No GitHub Actions workflow file (e.g., `.github/workflows/ci.yml`) is present or described, and there is no evidence that a CPU‑only CI pipeline with limited cores, memory, and a timeout has been set up. The required artifact is missing.
- **T010** — The required schema files `alloy_entry.schema.yaml` and `model_result.schema.yaml` are absent from `specs/001-predict-heusler-hysteresis/contracts/` (the only artifact listed is a missing `schema.yaml`). Without these files, the canonical schemas have not been defined.
- **T016** — declared artifact(s) missing/empty/invalid: code/src/ingestion/nist_fetcher.py, data/raw/manual_curated.csv
- **T017** — declared artifact(s) missing/empty/invalid: code/src/ingestion/journal_supplement_parser.py
- **T028** — declared artifact(s) missing/empty/invalid: data/processed/completeness_report.json
- **T028b** — The `scarcity_checker.py` script is present, but the required input file `data/processed/alloys_raw.csv` does not exist, so the checker cannot count rows or trigger T046. The missing (or empty) CSV must be added for the task to be fulfilled.
- **T032** — The provided `feature_engineering_pipeline.py` is truncated (e.g., an unfinished `process_row` function and no code that writes `alloys_features.csv`). Moreover, the required input file `data/processed/alloys_raw.csv` and the expected output `data/processed/alloys_features.csv` are absent from the repository. Consequently the task’s requirement—to read the raw CSV, compute descriptors, and save the enriched CSV—is not satisfied.
- **T037** — declared artifact(s) missing/empty/invalid: data/processed/model_metrics.json
