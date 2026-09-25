# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — No code, script, or log file was provided that actually checks the metadata for the required columns and implements the fatal‑exit behavior described in T002. Consequently, the required artifact is missing.
- **T003** — declared artifact(s) missing/empty/invalid: data/raw/metadata.csv, data/processed/behavioral/retention_metrics.json
- **T004a** — declared artifact(s) missing/empty/invalid: data/processed/behavioral/retention_metrics.json, data/processed/behavioral/power_metrics.json
- **T004b** — No artifact (e.g., log output, updated `reproducibility_report.json` showing `pipeline_metrics.power_warning: true` or appropriate messages) was provided to demonstrate that the power‑logging logic was implemented and executed. Without such evidence the requirement cannot be confirmed.
- **T005a** — No directory structure (`code/` with `code/data/`, `code/analysis/`, `code/utils/`) was presented or described; the claim lacks any concrete artifact evidence confirming the folders exist. The implementer must provide a listing or screenshot showing the created directories.
- **T005b** — No evidence (e.g., directory listings, screenshots, or file paths) was provided showing that a `data/` folder with the required `raw/`, `processed/`, and `artifacts/` subfolders actually exists. Without such artifacts, the task cannot be confirmed as completed.
- **T005c** — The response contains no evidence (e.g., a file tree, screenshots, or commands) that the `tests/` directory and its `contract/`, `integration/`, and `unit/` subdirectories were actually created. Without such proof, the task requirement is not satisfied.
- **T006** — No evidence of a Git repository being initialized nor a `.gitignore` file for data and artifacts is provided; the claim lacks any displayed artifact or path confirming the required files exist.
