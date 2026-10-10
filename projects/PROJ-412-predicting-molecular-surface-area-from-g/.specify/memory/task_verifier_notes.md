# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T005** — declared artifact(s) missing/empty/invalid: specs/001-predicting-molecular-surface-area/contracts/model_schema.yaml
- **T010** — `code/utils/seed.py` exists and implements a functional seed-pinning utility (random/NumPy/PyTorch seeding, default 42), and `code/config.py` defines `RANDOM_SEED: int = 42`. However, the task explicitly requires the seed to be set **from `code/config.py`**, and `seed.py` never imports or references `RANDOM_SEED` — it hardcodes its own `DEFAULT_SEED = 42` instead, so the two are only coincidentally equal and will silently diverge if the config value changes. Fix: import `RANDOM_SEED` from `code/config.py` (e.g., `from ..config import RANDOM_SEED` or equivalent) and use it as the default in `se
- **T014-Pilot** — Requested task execution failed; rerun successfully: code/data/pilot_study.py exit=1
- **T014-Merge** — declared artifact(s) missing/empty/invalid: data/processed/graphs_with_features.parquet
- **T015d** — declared artifact(s) missing/empty/invalid: data/processed/conformer_params.json, data/processed/noise_floor_report.json
- **T016** — declared artifact(s) missing/empty/invalid: data/splits/train_indices.csv, data/splits/test_indices.csv, data/splits/split_report.json, data/splits/split_error_report.json
- **T016-Report** — declared artifact(s) missing/empty/invalid: data/processed/paired_dataset.parquet, data/splits/train_indices.csv, data/splits/test_indices.csv, data/processed/final_dataset_stats.json
- **T040** — declared artifact(s) missing/empty/invalid: results/reports/model_metrics.json
- **T025** — declared artifact(s) missing/empty/invalid: results/reports/model_comparison.json
- **T028** — declared artifact(s) missing/empty/invalid: results/predictions/gcn_predictions.parquet, results/predictions/baseline_3d_predictions.parquet, data/processed/sensitivity_absolute.csv
- **T052-Run** — declared artifact(s) missing/empty/invalid: code/main.py, results/reports/pipeline_execution.log
- **T052-Verify-Parse** — declared artifact(s) missing/empty/invalid: results/reports/pipeline_execution.log, results/reports/runtime_raw.json
