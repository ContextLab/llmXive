# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — No directory tree was provided, and there is no evidence that the required `projects/PROJ-430-the-impact-of-asynchronous-communication` folder hierarchy (code, data, tests, docs, config) was actually created. The implementer must show the `tree` output confirming the structure exists.
- **T010** — The `code/data_ingestion.py` file is only partially implemented and contains placeholder code without real GitHub fetching logic, and the required output file `data/raw/events.json` does not exist. Consequently the script cannot be run to produce the non‑empty JSON event log as specified.
- **T012** — The provided `code/metrics.py` defines `identify_pairs_and_calculate_metrics` instead of the required `calculate_and_persist_pair_metrics`, and the file `data/derived/timestamp_features.parquet` does not exist, so the expected output artifact is missing. The implementation does not demonstrably produce the required schema or persist the results.
- **T015** — The required output file `data/derived/project_metrics.csv` does not exist, so there is no evidence of a `median_variance` column or any aggregated project‑level metrics. Consequently the verification test cannot be run. The task needs the CSV file with the correct median aggregation.
- **T021b** — declared artifact(s) missing/empty/invalid: data/derived/pair_sentiment.parquet, data/derived/timestamp_features.parquet
- **T022b** — declared artifact(s) missing/empty/invalid: data/validation/manual_ground_truth.csv, schema.yaml
