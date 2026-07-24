# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T021a** — The repository lacks the required output file `data/processed/cleaned_sessions.csv`, and the provided `code/analysis/data_cleaner.py` is truncated and does not show implementation of the status‑='incomplete' filtering nor the final CSV export. Consequently the specified exclusion, imputation, and output steps are not demonstrably completed.
- **T021c** — The repository contains a `clean_data.py` script, but the provided excerpt is truncated and shows no implementation of a command‑line interface, checksum generation, or recording of the checksum in a project state file. Moreover, the required output file `data/processed/cleaned_sessions.csv` does not exist. The task’s core deliverables are therefore missing.
- **T023a** — The required output file `data/processed/metrics_summary.csv` does not exist, so the deliverable is missing. Consequently the task’s core requirement (producing the summary CSV with the specified columns) is not satisfied.
- **T023b** — declared artifact(s) missing/empty/invalid: data/processed/descriptive_stats.csv
- **T025b** — The `run_analysis.py` file contains a partially‑implemented `load_and_validate_data()` function, but the code is truncated before it validates the numeric columns and their value ranges, and the required `data/processed/cleaned_sessions.csv` file is absent, so the loader cannot be exercised. The implementation must be completed to include all type/range checks and the expected CSV must be present.
- **T026** — declared artifact(s) missing/empty/invalid: data/processed/metrics_summary.csv
- **T029b** — The required workflow file `.github/workflows/reproducibility_check.yml` is not present in the repository (listed as missing). Consequently the deliverable does not exist, so the task is not satisfied.
- **T036b** — declared artifact(s) missing/empty/invalid: data/processed/power_report.md
- **T031b** — The repository lacks the required `contracts/session.schema.yaml` file, and `simulator.py` falls back to stub functions (`load_schema` returns a minimal placeholder schema and `validate_session` always returns True). Consequently, the simulator does not perform real schema validation nor abort on mismatches. The task’s core requirement is therefore unmet.
- **T043** — declared artifact(s) missing/empty/invalid: data/processed/cleaned_sessions.csv, data/sample_size_verification.json
