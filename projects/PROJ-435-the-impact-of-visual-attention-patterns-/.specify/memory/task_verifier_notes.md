# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The only artifact provided is the `scripts/init_project.py` script, which merely calls a `setup_data_structure` function that is not present in the evidence, and no actual directories (`code/`, `data/raw/`, `data/derived/`, `data/processed/`, `tests/`, `state/`) are shown to exist. The required project structure is therefore missing.
- **T003** — No linting or formatting configuration files (e.g., `.ruff.toml`, `.flake8`, `pyproject.toml` with Black settings) or setup scripts are present in the provided artifacts, so the requirement to configure ruff/flake8 and Black cannot be verified. The implementer must add the appropriate configuration files and/or documentation showing the tools are installed and integrated into the project.
- **T008a** — The provided `code/config/logging_config.yaml` contains a detailed logging dict (version, formatters, handlers, etc.) but it lacks the top‑level keys `level`, `format`, and `handlers` that the task explicitly required. Consequently the file does not match the specified concrete schema. The missing required keys must be added (e.g., `level: INFO`, `format: "...", handlers: [console, file]`).
- **T005** — The `code/config.yaml` lacks a `dataset_id` field (it only has a `dataset_url`), and the data loading script downloads via `requests` instead of using `datasets.load_dataset(..., revision="v1.0")`. Moreover, the required output files (`data/raw/eye_tracking_raw.parquet`, `state/data_hashes.json`, and `state/runtime_events.json`) are absent. The implementation does not verify the dataset ID against the config nor log the resolved ID.
- **T004b** — declared artifact(s) missing/empty/invalid: data/raw/eye_tracking_raw.parquet, data/derived/empirical_outcomes.csv
- **T021** — declared artifact(s) missing/empty/invalid: data/derived/empirical_outcomes.csv, state/runtime_events.json, data/derived/valence_scores.csv
- **T020a** — declared artifact(s) missing/empty/invalid: code/utils/synthetic_data_generator.py, data/synthetic/ground_truth.csv
- **T023** — declared artifact(s) missing/empty/invalid: data/derived/preprocessed_gaze.csv, data/derived/empirical_outcomes.csv, data/derived/valence_scores.csv, data/derived/merged_dataset_full.csv
- **T024** — declared artifact(s) missing/empty/invalid: data/derived/merged_dataset_full.csv, data/derived/regression_results.csv
- **T020** — declared artifact(s) missing/empty/invalid: tests/integration/test_mixed_effects_recovery.py, data/synthetic/ground_truth.csv
- **T033** — declared artifact(s) missing/empty/invalid: data/derived/robustness_report.csv
- **T039** — declared artifact(s) missing/empty/invalid: data/derived/robustness_report.csv
