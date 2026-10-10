# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — The requirements.txt exists but omits pinned `torch==2.1.0` and `torch-geometric==2.4.0` as actual entries — they appear only in a comment claiming they're installed via separate index URLs, which does not satisfy the task's requirement that the file contain pinned versions of all eleven listed packages. Fix by adding both pins (e.g., with `--extra-index-url` directives if needed) directly in `code/requirements.txt`.
- **T002b** — `code/config.py` exists and correctly defines `TIME_BUDGET=6.0`, `MAX_RAM_GB=7.0`, `RANDOM_SEED=42`, and `SENSITIVITY_THRESHOLDS=[0.01, 0.05, 0.1]`, but the required `MAX_MOLECULES: int = 5000` constant is entirely absent from the file. Add `MAX_MOLECULES: int = 5000` (the fixed pilot-study cap) to complete the task.
- **T004** — The schema file exists at the corrected `contracts/` path and is well-formed, but it does not define the required field `surface_area` — the target label is named `sasa` instead. The task explicitly enumerates the expected fields (SMILES, node_features, edge_features, surface_area, molecular_weight), so the schema should either rename `sasa` to `surface_area` or include a `surface_area` field (e.g., as an alias) to match the contract.
- **T005** — declared artifact(s) missing/empty/invalid: specs/001-predicting-molecular-surface-area/contracts/model_schema.yaml
- **T006** — declared artifact(s) missing/empty/invalid: specs/001-predicting-molecular-surface-area/contracts/sensitivity_schema.yaml
- **T014-Pilot** — declared artifact(s) missing/empty/invalid: code/data/pilot_study.py, data/processed/pilot_report.json
- **T014-Merge** — declared artifact(s) missing/empty/invalid: data/processed/graphs_with_features.parquet
- **T015d** — declared artifact(s) missing/empty/invalid: data/processed/conformer_params.json, data/processed/noise_floor_report.json
- **T016** — declared artifact(s) missing/empty/invalid: data/splits/train_indices.csv, data/splits/test_indices.csv, data/splits/split_report.json, data/splits/split_error_report.json
- **T016-Report** — declared artifact(s) missing/empty/invalid: data/processed/paired_dataset.parquet, data/splits/train_indices.csv, data/splits/test_indices.csv, data/processed/final_dataset_stats.json
- **T040** — declared artifact(s) missing/empty/invalid: results/reports/model_metrics.json
- **T025** — declared artifact(s) missing/empty/invalid: results/reports/model_comparison.json
- **T028** — declared artifact(s) missing/empty/invalid: results/predictions/gcn_predictions.parquet, results/predictions/baseline_3d_predictions.parquet, data/processed/sensitivity_absolute.csv
- **T052-Run** — declared artifact(s) missing/empty/invalid: code/main.py, results/reports/pipeline_execution.log
- **T052-Verify-Parse** — declared artifact(s) missing/empty/invalid: results/reports/pipeline_execution.log, results/reports/runtime_raw.json
