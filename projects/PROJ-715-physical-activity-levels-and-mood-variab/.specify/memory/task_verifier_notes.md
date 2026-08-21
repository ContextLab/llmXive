# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003a** — No `.flake8` file in a `code/` directory is provided, nor any excerpt of its contents showing the required `[flake8]` section with `max-line-length = 88` and `ignore = E203, E266, W503`. Without the actual file, the task requirement is not satisfied.
- **T011** — The `parse_step_logs()` function in `code/preprocess.py` does not load `data/raw/bronze.parquet` itself (it expects a DataFrame argument) and the required `data/raw/bronze.parquet` file is absent from the repository. Consequently the implementation does not meet the task’s specification.
- **T015** — The `daily_aggregates.csv` file exists, but the required `daily_aggregates.schema.yaml` file is missing, so the validation step cannot be performed. Additionally, there is no evidence (e.g., script or log) that the `assert not df['mood_std'].isna().any()` check was executed before writing. The missing schema file must be added and the validation/assertion demonstrated to satisfy the task.
- **T019b** — declared artifact(s) missing/empty/invalid: data/processed/verification.log
- **T024c** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T034b** — No evidence of an updated `specs/001-physical-activity-levels-and-mood-variability/` directory containing the required API documentation for `analysis.py` and a Data Dictionary for `daily_aggregates.csv` is provided, nor any indication that a root‑level `docs/` directory was removed or deprecated. These artifacts are missing, so the task is not satisfied.
