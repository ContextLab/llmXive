# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T064** — The repository contains the required `code/run_streaming_test.py` script, but the expected output artifacts (`data/processed/filtered_data.parquet` and `data/results/streaming_execution_report.json`) are absent, indicating the test has not been executed or does not produce the required files. The missing outputs must be generated (and memory usage verified) for the task to be considered complete.
- **T066** — declared artifact(s) missing/empty/invalid: data/results/real_data_analysis_report.json
- **T067** — declared artifact(s) missing/empty/invalid: data/results/integrity_verification.json, data/results/fabrication_audit_report.json
- **T069** — The repository contains modified `main.py` and `ingest.py` snippets that begin to handle a harmonized parquet file, but the required output artifacts `data/results/harmonization_report.json` and `data/results/real_data_analysis_report.json` are absent, and the provided code is truncated so we cannot confirm that the original “No Real Data” halt condition was fully removed. The task’s core deliverables are therefore not present.
- **T069#1** — The repository contains modified `main.py` and `ingest.py` snippets, but neither script creates the required `data/results/harmonization_report.json` nor `data/results/real_data_analysis_report.json` files. Those output artifacts are missing, so the task’s deliverables are not satisfied.
