# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T020** — The repository lacks the required output file `data/processed/historical_performance_metrics.csv`, and `code/fetcher.py` does not contain a complete implementation of `process_historical_data` (the file is truncated, contains a syntax error, and no such function is defined). Consequently the task’s specification is not met.
- **T017a** — declared artifact(s) missing/empty/invalid: data/processed/performance_metrics.csv
- **T017b** — declared artifact(s) missing/empty/invalid: data/processed/performance_metrics.csv
- **T025b** — The required `data/processed/graph_metrics.csv` file does not exist, and the provided `code/graph_builder.py` snippet shows only helper functions without any command‑line handling or CSV‑writing logic for the `--generate-metrics` entry point. Consequently the task’s core output and verification steps are missing.
- **T028** — The required input files `data/processed/performance_metrics.csv` and `data/processed/graph_metrics.csv` are absent, so the function cannot be exercised. Moreover, the implementation contains a typo in the `pd.merge` call (`perdf=` instead of `left=`), which would raise an error even if the files existed. Both issues prevent the task’s verification from succeeding.
- **T034c** — declared artifact(s) missing/empty/invalid: data/processed/correlation_results.csv
- **T054** — declared artifact(s) missing/empty/invalid: data/processed/correlation_results.csv, schema.yaml
- **T055** — declared artifact(s) missing/empty/invalid: data/processed/graph_metrics.csv, schema.yaml
