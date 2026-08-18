# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003a** — No `.flake8` file in the `code/` directory is presented, nor any excerpt of its contents showing the required `[flake8]` section with `max-line-length = 88` and `ignore = E203, E266, W503`. Without this artifact, the task requirement is not satisfied.
- **T011** — The repository lacks the required `data/raw/bronze.parquet` file, and the `parse_step_logs()` implementation is incomplete (it only begins parsing and is truncated, and does not itself load the parquet file). Consequently the task’s core requirement—to load the bronze parquet and produce daily step totals—is not met.
- **T015** — declared artifact(s) missing/empty/invalid: data/processed/daily_aggregates.csv, schema.yaml
- **T019b** — No artifact (e.g., verification script output, log, or documentation) was provided showing that the `mood_std` column in `daily_aggregates.csv` was checked and confirmed to be unchanged and available for downstream analyses. Without such evidence, the task requirement is not satisfied.
- **T024b** — No `model_results.json` file is present in the provided evidence, and no content consolidating fixed effects, random effects, diagnostics, LOPO results, or sensitivity analysis is shown. The required aggregated JSON artifact is missing, so the task is not satisfied.
- **T025** — declared artifact(s) missing/empty/invalid: data/processed/model_results.json, schema.yaml
- **T034b** — No `docs/` files were presented; there is no evidence that API documentation for `analysis.py` or a Data Dictionary for `daily_aggregates.csv` were created or updated. The required documentation artifacts are missing.
