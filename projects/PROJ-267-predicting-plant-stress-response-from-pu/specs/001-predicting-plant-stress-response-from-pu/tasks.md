# Tasks: Predicting Plant Stress Response from Publicly Available Proteomic Data

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, contracts (`dataset.schema.yaml`, `model_output.schema.yaml`), original idea, prior `tasks.md`, verifier feedback.  
**Branch**: `001-predict-plant-stress-response`

The tasks follow the three‑phase research template (setup → full study → reproducible handoff).  
All tasks are unchecked; they will be marked ✅ only after the described artifact is produced and the verification step passes.

---

## Phase 1 – Setup and first end‑to‑end analysis  

- [X] **T001** [US1] Create the project skeleton, add a `logs/` directory, and document a runnable quick‑start command.  
  - **Artifacts**: `data/raw/`, `data/processed/`, `logs/`, `results/`, `code/main.py`, `quickstart.md`, `docs/structure.txt`  
  - **Verification**: Running `python -m code.main --stage quickstart` on a clean runner creates `logs/pipeline.log` and exits with status 0; the command and its output are reproduced verbatim in `quickstart.md`; `docs/structure.txt` contains a tree listing of the repository.

- [ ] **T017** [Constitution I] Create a reproducibility module (`code/utils/constants.py`) that pins all random seeds for numpy, random, and scikit-learn.  
  - **Artifacts**: `code/utils/constants.py`  
  - **Verification**: A test script verifies that `np.random.seed` and `random.seed` are called using the constants defined in the module; all stochastic components in `code/` are verified to import and use these constants.

- [ ] **T003** [US1] Provide a project‑wide logger (`code/utils/logger.py`) and ensure **all** pipeline modules import and use it.   <!-- FAILED-IN-EXECUTION: code/utils/verify_logging_imports.py exit=1 -->
  - **Artifacts**: `code/utils/logger.py`, updated imports in `code/data/*.py`, `code/models/*.py`, `code/viz/*.py`  
  - **Verification**: After a full pipeline run, `logs/pipeline.log` contains INFO entries for dropped rows, missing‑column warnings, and any raised errors; a script scans the `code/` directory to verify that every module imports and uses `get_logger`.

- [ ] **T002** [US1] Implement real‑data ingestion that streams download of GEO/ProteomeXchange files, verifies SHA‑256 checksums, and selects the dataset with the largest sample size (n) per species-stress pair (breaking ties by earliest publication date) per FR-001; abort on failure (no silent fallback).  
  - **Artifacts**: `code/data/download.py`, `code/utils/checksums.py`, `data/raw/` (populated with the test accession GSE14784 and a matching ProteomeXchange file), `data/raw/checksums.sha256`  
  - **Verification**: After `python -m code.main --stage ingest`, the raw files exist and are > 1 KB; `checksums.sha256` matches; any download error raises an exception and the CI job fails (no fallback).

- [ ] **T004** [US1] Implement fold-wise preprocessing to avoid data leakage (Constitution VI): for each CV fold, apply low‑abundance filter (< 50 % detection), median imputation, and batch‑effect correction with `pycombat` on the training split and apply the resulting parameters to the test split; perform identifier mapping via R `biomaRt` through `rpy2`, and merge proteomic & transcriptomic tables into the unified matrix.  
  - **Artifacts**: `code/data/preprocess.py`, `data/processed/unified_matrix.csv`  
  - **Verification**: `unified_matrix.csv` validates against `contracts/dataset.schema.yaml`; `logs/pipeline.log` records the number of rows dropped due to unmapped identifiers and columns dropped because > 90 % missing.

- [ ] **T005** Add schema‑validation utilities and unit tests.  
  - **Artifacts**: `code/utils/schema_check.py`, `tests/unit/test_schema_validation.py`  
  - **Verification**: `python -c "from code.utils.schema_check import validate_dataset; validate_dataset('data/processed/unified_matrix.csv')"` exits without error; `pytest -q tests/unit/test_schema_validation.py` passes.

- [ ] **T006** Perform the data‑inventory check required by FR‑009; if the ≥ 3 paired‑sample threshold is not met for a species‑stress pair, record a “Data Insufficient” status and trigger the fallback path.  
  - **Artifacts**: `code/data/inventory_check.py`, `results/data_completeness.json` (contains per‑species‑stress counts and a boolean `paired_enough`)  
  - **Verification**: Running the pipeline prints a concise message indicating either “Paired data sufficient – proceeding to regression” or “Paired data insufficient – invoking fallback classification (FR‑010)”. The JSON file matches the message.

- [ ] **T018** [Plan Step 9] Implement the pre-study power analysis to determine if the available sample size is sufficient for the anticipated effect size before proceeding to modeling.  
  - **Artifacts**: `code/utils/power_analysis.py`, `results/power_analysis.json`  
  - **Verification**: `results/power_analysis.json` contains a `power_sufficient` boolean and the required sample size calculation based on literature-derived effect sizes.

---

## Phase 2 – Complete the study and validate its evidence  

- [ ] **T007** Train Random Forest and SVR regression models on within‑stress data using 5-fold cross‑validation (or LOOCV if n < 50) and include one‑hot encoded species covariates, ensuring all stochastic processes use the pinned seeds from `code/utils/constants.py`.  
  - **Artifacts**: `code/models/train_regressor.py`, `results/within_stress_metrics.json` (per‑fold R², RMSE for each model)  
  - **Verification**: The JSON file conforms to `model_output.schema.yaml` (except `train_stress` = `test_stress` for within‑stress runs) and includes a non‑null `r2` > ‑1.

- [ ] **T008** Perform cross‑stress evaluation, compute a null‑model baseline, and run the shuffled‑target permutation control (p < 0.05 required).  
  - **Artifacts**: `code/models/evaluate_cross_stress.py`, `results/cross_stress_metrics.json`, `results/null_model_metrics.json`, `results/shuffled_target_control.json` (contains `shuffled_target_p`)  
  - **Verification**: `cross_stress_metrics.json` lists `train_stress` ≠ `test_stress` entries; `null_model_metrics.json` reports `null_model_r2`; `shuffled_target_control.json` reports `shuffled_target_p` < 0.05.

- [ ] **T009** Extract the top‑20 protein feature importances for each regression model and write them to a JSON file that validates against `model_output.schema.yaml`.  
  - **Artifacts**: `code/models/feature_importance.py`, `results/feature_importance.json` (contains `model_type`, `cv_strategy`, and a list of 20 proteins with importance scores)  
  - **Verification**: JSON schema validation succeeds; the list length is exactly 20 and all importance scores are > 0.

- [ ] **T010** Generate publication‑ready figures directly from the metric JSONs:  
    1. Scatter plot of predicted vs. actual gene expression (`results/figures/prediction_scatter.png`).  
    2. Heat‑map of R² values for every training‑stress → testing‑stress pair (`results/figures/cross_stress_heatmap.png`).  
    3. Bar chart of the top‑20 feature importances (`results/figures/feature_importance_bar.png`).  
  - **Artifacts**: `code/viz/plots.py`, PNG files under `results/figures/`  
  - **Verification**: Each PNG is non‑empty, saved at ≥ 300 dpi, and an automated contrast‑check script verifies that all figures meet the minimum colour-contrast ratio of 4.5:1 (SC-008).

- [ ] **T011** Record total CPU time and peak memory usage, enforce the 6‑hour / 7 GB limits, and write `results/runtime_metrics.json`.  
  - **Artifacts**: `code/utils/metrics.py`, `results/runtime_metrics.json` (fields: `cpu_time_seconds`, `peak_memory_gb`, `limit_exceeded` boolean)  
  - **Verification**: The pipeline aborts with a non‑zero exit code if limits are exceeded; otherwise `limit_exceeded` is `false`.

- [ ] **T012** If the data‑inventory check (T006) indicated insufficient paired samples, run the fallback proteomics‑only classification (FR‑010): train a Random Forest classifier to predict stress condition and report accuracy and F1‑score.  
  - **Artifacts**: `code/models/train_classifier.py`, `results/fallback_classification.json` (fields: `accuracy`, `f1_score`, `model_type` = `"RandomForestClassifier"`)  
  - **Verification**: Accuracy ≥ 0.70 and F1 ≥ 0.65; JSON schema validation (custom schema defined in `contracts/fallback_classifier.schema.yaml`).

---

## Phase 3 – Reproducible results and paper handoff  

- [ ] **T013** Update documentation: `README.md` with installation steps, concrete GEO/ProteomeXchange accession URLs, usage examples, and a “Results” section that cites the generated artifact files. Add comprehensive docstrings to every public function in `code/`.  
  - **Artifacts**: `README.md`, updated docstrings across `code/`  
  - **Verification**: `pydocstyle code/` reports no missing docstrings; the README builds without broken links.

- [ ] **T019** [Constitution V] Implement an artifact tracking utility that computes SHA-256 hashes of all generated files and updates the project state file.  
  - **Artifacts**: `code/utils/state_manager.py`, updated `state/projects/PROJ-267-predicting-plant-stress-response-from-pu.yaml`  
  - **Verification**: The project state file contains a complete `artifact_hashes` map that matches the actual disk content of all produced files.

- [ ] **T014** Execute the full reproducible workflow (`python -m code.main --stage all`) on a clean runner, confirm that all previous artifacts are regenerated identically, and write a results summary.  
  - **Artifacts**: `docs/results_summary.md` (methods, actual findings, negative outcomes, limitations, and handoff statement)  
  - **Verification**: A fresh run produces JSON/CSV/PNG files whose content hashes match those recorded in `state/projects/PROJ-267-predicting-plant-stress-response-from-pu.yaml`.

- [ ] **T015** Verify the Quickstart workflow on a clean environment, capture the console output, and store it as `quickstart_run.log`.  
  - **Artifacts**: `quickstart_run.log`  
  - **Verification**: Log shows successful execution of the end‑to‑end pipeline (or graceful fallback) with exit status 0; the log is referenced in `quickstart.md`.

- [ ] **T016** Generate a directory‑tree listing for the `docs/` folder and store it in `docs/structure.txt`.  
  - **Artifacts**: `docs/structure.txt` (produced e.g., by `tree -a docs/ > docs/structure.txt`)  
  - **Verification**: File is non‑empty and matches the actual repository layout.

---

## Dependency & Requirement Coverage  

| Spec ID | Task(s) | Command demonstrating completion |
|---------|---------|-----------------------------------|
| FR‑001 (download, largest‑n selection) | T002 | `python -m code.main --stage ingest` → `data/raw/` |
| FR‑002 (filter, median imputation) | T004 | `data/processed/unified_matrix.csv` + log entries |
| FR‑003 (biomaRt merge) | T004 | Mapping statistics in `logs/pipeline.log` |
| FR‑004 (RF / SVR on CPU) | T007 | `results/within_stress_metrics.json` |
| FR‑005 (CV, cross‑stress, controls) | T007, T008 | `results/cross_stress_metrics.json`, `results/shuffled_target_control.json` |
| FR‑006 (feature importance) | T009 | `results/feature_importance.json` |
| FR‑007 (figures) | T010 | PNG files under `results/figures/` |
| FR‑008 (runtime metrics) | T011 | `results/runtime_metrics.json` |
| FR‑009 (data‑inventory) | T006 | `results/data_completeness.json` |
| FR‑010 (fallback classification) | T012 | `results/fallback_classification.json` (if invoked) |
| SC‑001 (vs null model) | T008 | `results/null_model_metrics.json` |
| SC‑002 (R² drop) | T008 | `results/cross_stress_metrics.json` |
| SC‑003 (resource limits) | T011, T014 | Limit assertions in `results/runtime_metrics.json` |
| SC‑004 (data completeness) | T006 | `results/data_completeness.json` |
| SC‑005 (CV integrity) | T004, T007 | Fold-wise logic in `code/data/preprocess.py` |
| SC‑006 (fallback classification performance) | T012 | Accuracy ≥ 0.70, F1 ≥ 0.65 |
| SC‑008 (visual accessibility) | T010 | Contrast-check script verification |
| SC‑009 (permutation test) | T008 | `shuffled_target_p` < 0.05 in `results/shuffled_target_control.json` |

**Execution order** (respecting data flow, reproducibility, and logger dependency):  

T001 → T017 → T003 → T002 → T004 → T005 → T006 → T018 → T007 → T008 → T009 → T010 → T011 → T012 → T013 → T019 → T014 → T015 → T016.

All tasks remain unchecked until their artifacts are produced and the verification steps succeed.