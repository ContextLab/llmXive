# Tasks: Predicting Plant Stress Response from Publicly Available Proteomic Data

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, contracts (`dataset.schema.yaml`, `model_output.schema.yaml`), original idea, prior tasks.md and verifier feedback.  
**Branch**: `001-predict-plant-stress-response`

The tasks below follow the three‑phase research template (setup → full study → reproducible handoff). Each task is a concrete, checkable unit with required artifact paths and verification steps.

## Phase 1 – Setup and first end‑to‑end analysis

- [ ] T001 Create project skeleton: directories `data/raw/`, `data/processed/`, `logs/`, `docs/`, `results/`; add `requirements.txt`; create `code/main.py` with a `--stage noop` option that exits 0; generate a directory‑tree listing `docs/structure.txt`.  
  **Verification**: `docs/structure.txt` contains a tree listing; `python -m code.main --stage noop` exits 0; the command documented in `quickstart.md` runs successfully on a clean runner.

- [ ] T006 Configure project‑wide logging: add `code/utils/logger.py` that writes INFO/WARN messages to `logs/pipeline.log`. Ensure all pipeline modules import and use this logger.  
  **Verification**: `logs/pipeline.log` exists after any pipeline run and contains entries for dropped rows, missing columns, and any raised errors.

- [ ] T002 Implement real‑data ingestion: add `code/data/download.py` and `code/utils/checksums.py` to stream download GEO/ProteomeXchange files, verify SHA‑256 checksums, and raise exceptions on failure (no silent fallback).  
  **Verification**: `data/raw/` holds downloaded files > 1 KB, `data/raw/checksums.sha256` is present, and any download error raises an exception (no silent fallback).

- [ ] T003 Add linting and formatting configuration: create `.flake8`, `pyproject.toml` with Black settings, and a CI script `ci/lint.sh` that runs `flake8` and `black --check`.  
  **Verification**: `.flake8`, `pyproject.toml`, and `ci/lint.sh` exist; `ci/lint.sh` runs without errors on the codebase.

- [ ] T004 Implement preprocessing: low‑abundance filter (< 50 % detection), Left‑Censored Missing (LCM) imputation, biomaRt identifier mapping via `rpy2`, and merge proteomic & transcriptomic tables into a unified matrix. Files: `code/data/normalize.py`, `code/data/merge.py`, `code/data/pipeline.py`. Uses logger from T006.  
  **Verification**: `data/processed/unified_matrix.csv` exists, is non‑empty, passes schema validation, and `logs/pipeline.log` records drop counts and mapping statistics.

- [ ] T005 Add schema‑validation utilities using Pydantic for the dataset and model‑output contracts. Files: `code/utils/schema_check.py` and unit test `tests/unit/test_schema_validation.py`.  
  **Verification**: Running `python -c "from code.utils.schema_check import validate_dataset; validate_dataset('data/processed/unified_matrix.csv')"` succeeds; the unit test passes.

- [ ] T007 Implement pipeline sanity‑check modules: `code/data/sample_check.py`, `code/data/cv_strategy.py`, and `code/data/completeness.py`.  
  **Verification**: JSON reports `results/sample_stats.json`, `results/cv_strategy.json`, and `results/data_completeness.json` are generated with real counts; if no paired data exist the pipeline halts with a clear “Data Unavailable” message.

## Phase 2 – Complete the study and validate its evidence

- [ ] T008 Train RandomForestRegressor and SVR models on within‑stress data using strict 5‑fold cross‑validation. File: `code/modeling/train.py`.  
  **Verification**: `results/within_stress_metrics.json` contains per‑fold R² and RMSE for both models.

- [ ] T009 Perform cross‑stress evaluation, null‑model baseline, raw‑feature baseline, and stress‑label permutation control; compute R²‑drop metrics and store all results. Files: `code/modeling/cross_stress_eval.py`, `code/modeling/baselines.py`, `code/modeling/evaluate.py`, `code/modeling/metrics.py`.  
  **Verification**: JSON artifacts `results/cross_stress_metrics.json`, `results/null_model_metrics.json`, `results/raw_feature_baseline.json`, `results/shuffle_control.json`, and `results/r2_drop.json` exist and contain real values.

- [ ] T010 Extract the top‑20 protein feature importances for each model and write them to a JSON file that conforms to `model_output.schema.yaml`. File: `code/modeling/feature_importance.py`.  
  **Verification**: `results/feature_importance.json` is present, schema‑validated, and lists exactly 20 proteins per model with non‑zero importance scores.

- [ ] T011 Record total CPU time and peak memory usage to `results/runtime_metrics.json`; enforce the 6‑hour / 7 GB limits with a non‑zero exit on breach. Files: `code/reporting/metrics.py` plus unit test `tests/unit/test_runtime_limits.py`.  
  **Verification**: `results/runtime_metrics.json` contains `cpu_time_seconds` and `peak_memory_gb`; the unit test forces a limit breach and expects a non‑zero exit status.

- [ ] T012 Generate publication‑ready figures (prediction scatter, cross‑stress heat‑map, feature‑importance bar chart) and save them as PNGs under `results/`. Files: `code/reporting/plots.py` and `code/reporting/generate_report.py`.  
  **Verification**: PNG files `results/prediction_scatter.png`, `results/cross_stress_heatmap.png`, and `results/feature_importance_bar.png` exist and are produced directly from the metric JSONs (no manual editing).

- [ ] T013 Add edge‑case unit tests covering: all‑missing columns, mismatched identifiers, samples without transcriptomic matches, ambiguous species metadata, and CV‑integrity (no train/test overlap). Produce `results/cv_integrity_report.json`. File: `tests/unit/test_pipeline.py`.  
  **Verification**: `pytest -q` passes; `results/cv_integrity_report.json` records exact split IDs and confirms zero overlap.

## Phase 3 – Reproducible results and paper handoff

- [ ] T014 Update `README.md` with installation steps, usage examples, concrete GEO/ProteomeXchange accession URLs actually downloaded, and a Results section that cites the generated artifact files. Add comprehensive docstrings to every public function in `code/`.  
  **Verification**: README contains the required sections; `pydocstyle code/` reports no missing docstrings.

- [ ] T015 Execute the full reproducible workflow (`python -m code.main --stage all`), confirm that all previous artifacts are regenerated identically, and write `docs/results_summary.md` summarizing methods, actual findings (including any negative or “Data Unavailable” outcomes), limitations, and the handoff package for the paper stage.  
  **Verification**: A fresh run reproduces all JSON metrics within tolerance; `docs/results_summary.md` references only existing artifact files.

- [ ] T016 Verify Quickstart workflow: run the command documented in `quickstart.md` on a clean runner, capture the console output, and store a log `quickstart_run.log`.  
  **Verification**: The log file exists and shows successful end‑to‑end execution without errors.

- [ ] T017 Generate a directory‑tree listing `docs/structure.txt` (e.g., using `tree -a . > docs/structure.txt`).  
  **Verification**: `docs/structure.txt` is non‑empty and matches the repository structure.

### Dependency & Requirement Coverage

| Requirement | Task(s) | Command demonstrating completion |
|-------------|---------|-----------------------------------|
| FR‑001 (download, largest‑n selection) | T002 | `python -m code.main --stage data` → `data/raw/checksums.sha256` |
| FR‑002 (filter, LCM imputation) | T004 | `data/processed/unified_matrix.csv` + log entries |
| FR‑003 (biomaRt merge) | T004 | Mapping drop counts in `logs/pipeline.log` |
| FR‑004 (RF / SVR on CPU) | T008 | `results/within_stress_metrics.json` |
| FR‑005 (CV, cross‑stress, controls) | T008, T009 | `results/cross_stress_metrics.json`, `results/shuffle_control.json` |
| FR‑006 (feature importance) | T010 | `results/feature_importance.json` |
| FR‑007 (figures) | T012 | PNG files under `results/` |
| FR‑008 (runtime metrics) | T011 | `results/runtime_metrics.json` |
| SC‑001 (vs null model) | T009 | `results/null_model_metrics.json` |
| SC‑002 (R² drop) | T009 | `results/r2_drop.json` |
| SC‑003 (resource limits) | T011, T015 | Limit assertions exercised in tests |
| SC‑004 (data completeness) | T007 | `results/data_completeness.json` |
| SC‑005 (CV integrity) | T013 | `results/cv_integrity_report.json` |
| Lint/formatting | T003 | CI lint script passes |
| Documentation & docstrings | T014 | `pydocstyle` passes |
| Quickstart verification | T016 | `quickstart_run.log` shows successful run |
| Directory‑tree listing | T017 | `docs/structure.txt` present |

**Execution order** (respecting data flow & logger dependency):  
T001 → T006 → T002 → T003 → T004 → T005 → T007 → T008 → T009 → T010 → T011 → T012 → T013 → T014 → T015 → T016 → T017.  

All tasks remain unchecked until their artifacts are produced and verified; completed tasks may be marked `[x]` after a successful run.  