# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The evidence shows the top‑level project directories (`code/`, `data/`, `tests/`, `outputs/`, `state/`) exist, but it does not confirm the required sub‑directories `data/raw`, `data/processed`, `data/features`, `tests/contract`, `tests/unit`, and `tests/integration` are present. Without explicit evidence of those folders, the prescribed `mkdir -p …` structure is not fully realized.
- **T003** — The evidence shows only the project root path; there are no listed `.black` or `.flake8` configuration files in that directory, so the required linting/formatting config files are missing.
- **T012b** — declared artifact(s) missing/empty/invalid: data/irb_request_template.md
- **T012c_doc** — declared artifact(s) missing/empty/invalid: docs/data_collection_protocol.md
- **T013_clean** — declared artifact(s) missing/empty/invalid: code/filter_features.py, data/processed/raw_facial_features.csv, data/processed/clean_facial.csv
- **T014_clean** — declared artifact(s) missing/empty/invalid: code/filter_features.py, data/processed/raw_vocal_features.csv, data/processed/clean_vocal.csv
- **T015_merge** — declared artifact(s) missing/empty/invalid: code/merge_features.py, data/processed/clean_facial.csv, data/processed/clean_vocal.csv, data/processed/clean_features.csv
- **T016_report** — declared artifact(s) missing/empty/invalid: outputs/correlation_report.csv, outputs/unified_analysis_report.md
- **T012_trigger_collection** — declared artifact(s) missing/empty/invalid: data/irb_request_template.md, docs/data_collection_protocol.md, data/study_log.md, state/pipeline_status.yaml
- **T023_report** — declared artifact(s) missing/empty/invalid: outputs/unified_analysis_report.md
- **T029_gen** — declared artifact(s) missing/empty/invalid: code/checksums.py
- **T029_store** — declared artifact(s) missing/empty/invalid: state/raw_data_hashes.json, state/feature_hashes.json
- **T030_gen** — declared artifact(s) missing/empty/invalid: code/checksums.py
- **T030_store** — declared artifact(s) missing/empty/invalid: state/feature_hashes.json
- **T032** — declared artifact(s) missing/empty/invalid: code/audit_trail.py, state/audit_log.md
