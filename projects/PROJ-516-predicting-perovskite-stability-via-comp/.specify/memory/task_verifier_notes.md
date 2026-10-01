# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T004** — declared artifact(s) missing/empty/invalid: code/state_manager.py, state/project_state.yaml
- **T012c** — declared artifact(s) missing/empty/invalid: data/raw/nrel_perovskites.csv, data/raw/mp_perovskites.csv
- **T012e** — declared artifact(s) missing/empty/invalid: data/raw/perovskites_merged.csv
- **T013** — declared artifact(s) missing/empty/invalid: data/raw/metadata.json
- **T013b** — No `metadata.json` file (or diff) showing the added `precision_from_registry` flag and updated `precision_source` field is provided, nor any verification output confirming that every record correctly records its provenance. The required artifact and proof of its correctness are missing.
- **T061** — The `code/utils/uncertainty_calculator.py` file exists, but the required input file `data/raw/perovskites_merged.csv` and the output file `data/processed/descriptors_uncertainty.csv` are both missing, and the script does not contain logic that reads the raw data and writes the new CSV with a `total_uncertainty` column. The task’s core output is therefore not present.
- **T014b** — declared artifact(s) missing/empty/invalid: data/processed/descriptors_features.csv
- **T014c** — declared artifact(s) missing/empty/invalid: data/processed/descriptors_features.csv
- **T015a** — declared artifact(s) missing/empty/invalid: data/processed/descriptors_filtered.csv, data/processed/exclusion_log.csv
- **T016a** — The `vif_calculator.py` script is truncated and contains placeholder `pass` statements; it never computes VIF nor writes `vif_report.csv`. Moreover, the required input file `data/processed/descriptors_filtered.csv` and the expected output `data/processed/vif_report.csv` are absent. The task’s core functionality and artifacts are missing.
- **T017** — declared artifact(s) missing/empty/invalid: data/processed/descriptors_final.csv, data/processed/descriptors_filtered.csv, state/project_state.yaml
- **T053** — The required file `data/processed/validation_report.md` is missing, so no content can be verified to contain the “Instrumentation Audit” and “Data Quality Assessment” sections or the consolidated logic. The task’s primary artifact is absent.
- **T054** — The repository lacks the required `data/raw/instrumentation_fallbacks.log` and the generated `data/processed/missing_instrumentation_report.csv`; both are missing. Moreover, the `generate_missing_instrumentation_report` function is incomplete (truncated) and does not contain the logic to read the log and write the CSV. The task’s core output is therefore not present.
