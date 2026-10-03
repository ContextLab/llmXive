# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — No directory tree, file list, or count of `__init__.py` files was provided, so we cannot confirm that every new directory under `projects/PROJ-llmxive-follow-up-extending-claw-swe-ben/code/` now contains an `__init__.py`. The required artifact (the created `__init__.py` files and matching count) is missing.
- **T045** — The `threshold_validator.py` script is present and implements the required logic, but the required dataset file `data/filtered_swe_bench_v1.parquet` is missing, so the script cannot actually count rows or produce the expected log/exit behavior. Additionally, the `main()` function is truncated, leaving it unclear whether it exits with code 0 on success. The missing parquet file (and incomplete entry‑point) must be provided/fixed for the task to be considered complete.
- **T016** — declared artifact(s) missing/empty/invalid: data/intermediate/baseline_run.jsonl, schema.yaml
- **T028** — declared artifact(s) missing/empty/invalid: data/results.csv
- **T030c** — declared artifact(s) missing/empty/invalid: data/results/comparison_report.md, data/results.csv, data/analysis_flags.json
- **T039** — declared artifact(s) missing/empty/invalid: data/results.csv, data/intermediate/baseline_run.jsonl, state/projects/PROJ-904-llmxive-follow-up-extending-claw-swe-ben.yaml
- **T054** — The repository contains the `representativeness_validator.py` script, but the required input file `data/filtered_swe_bench_v1.parquet` is missing, so the script cannot be executed to produce the KS statistic, p‑value, or the warning. Consequently the verification step cannot be satisfied.
