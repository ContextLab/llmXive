# Tasks: Predicting Species Distribution Shifts Using Historical Occurrence Records and Climate Data

**Input**: `spec.md`, `plan.md`, existing research artifacts, and reviewer feedback.
**Goal**: Deliver a reproducible end‑to‑end pipeline that satisfies every functional requirement (FR‑001 – FR‑011) and success criteria (SC‑001 – SC‑003) while respecting the platform constitution (real data only, CPU‑only execution, strict provenance).

---

## Phase 0 – Project bootstrap (foundational, can run in parallel)

- [ ] T001 [P] Create project scaffold, `requirements.txt`, `.flake8`, `pyproject.toml`, and `quickstart.md`; add `.gitkeep` files in all new directories (`code/`, `data/raw/`, `data/processed/`, `models/`, `metrics/`, `logs/`, `reports/`, `tests/`, `contracts/`).
- [X] T002 [P] Add `code/config.py` with global constants (species list, paths, `THINNING_DISTANCE_KM`, random seeds, `n_jobs=2`).
- [ ] T003 [P] Initialise logging configuration (`logs/` with format `%(asctime)s - %(name)s - %(levelname)s - %(message)s`) and create YAML schema for `logs/preprocess_counts.yaml`. <!-- FAILED-IN-EXECUTION: code/init_logging.py exit=-1 -->

---

## Phase 1 – Data acquisition (User Story 1)

- [ ] T004 [US1] Implement `code/download.py` to: <!-- FAILED-IN-EXECUTION: code/download.py exit=-1 (TIMEOUT) -->
 1. **Historical occurrences** (1970‑2000) → `data/raw/occurrence_1970_2000.csv` (GBIF API, pagination, species list from `config.py`, required columns `source_identifier`, `download_timestamp`, `original_dataset_name`).
 2. **Recent occurrences** (2005‑2020) → `data/raw/occurrence_2005_2020.csv` (same logic, different year filter).
 3. **WorldClim historical rasters** (bio1‑bio19, 1970‑2000) → `data/raw/climate_historical/` (subset to each species’ bounding box).
 4. **WorldClim recent rasters** (bio1‑bio19, 2005‑2020) → `data/raw/climate_recent/` (subset to bounding boxes).
 5. **CMIP6 SSP2‑4.5 future rasters** (2050, bio1‑bio19) → `data/raw/climate_future/` (subset to bounding boxes).
 6. Verify presence of all 19 variables per species; exit with code 1 on any missing file.

- [ ] T010 [P] Strengthen `code/download.py`: <!-- FAILED-IN-EXECUTION: code/download.py exit=2 -->
 * Use `requests` with `stream=True` and chunked writes for any raster > 2 GB.
 * After each download compute SHA‑256 checksum; compare to known values (or file size) and abort on mismatch.
 * Update `data/manifest.json` (URL, timestamp, checksum, file size) automatically after each successful download.

- [ ] T015 [P] Generate and validate data contracts:
 * Write YAML schema files under `contracts/` (`occurrence_record.schema.yaml`, `climate_raster.schema.yaml`, `climate_variable.schema.yaml`, `data_sufficiency.schema.yaml`, `model_artifact.schema.yaml`, `model_metrics.schema.yaml`, `occurrence.schema.yaml`).
 * Run a validation script that checks downloaded CSVs and raster metadata against these schemas; abort on schema violations.

---

## Phase 2 – Pre‑processing & data‑sufficiency (User Story 1)

- [ ] T005 [US1] Implement `code/preprocess.py` to:
 1. Filter records by breeding months, drop duplicates.
 2. Spatially thin occurrences using `config.THINNING_DISTANCE_KM`; log per‑species counts to `logs/preprocess_counts.yaml`.
 3. Extract **all** 19 climate variables from the raster sets (historical & recent) at occurrence points → `data/processed/occurrence_full.csv`.
 4. Perform VIF analysis on the 19 variables, iteratively remove highest‑VIF until `< 5`; write selected variable names to `metrics/selected_climate_variables.json`.
 5. Subset `occurrence_full.csv` to the selected variables → `data/processed/occurrence_model.csv`.
 6. Compute data‑sufficiency for the **recent** period (2005‑2020) using a power analysis (Cohen’s h = 0.50, α = 0.05, power ≥ 0.80) and write `metrics/data_sufficiency.json` (schema includes `species`, `count`, `n_min`, `status`, `dataset_period`). Species failing this check are flagged `INSUFFICIENT_DATA`.

- [ ] T011 [P] Add comprehensive unit & integration tests under `tests/`:
 * `tests/unit/test_download.py` – pagination, metadata columns, streaming download, checksum verification.
 * `tests/unit/test_preprocess.py` – breeding‑season filter, thinning distance, VIF selection, data‑sufficiency flagging.
 * `tests/unit/test_gpu_check.py` – simulated GPU presence/absence handling.
 * `tests/unit/test_train.py` – block generation, model fitting, metric output.
 * `tests/unit/test_evaluate.py` – projection, AUC/TSS calculation, delta suitability, delta AUC/TSS, bootstrap logic.
 * `tests/integration/test_end_to_end.py` – run the full pipeline on a single low‑complexity species subset; assert creation of all expected artifacts.

---

## Phase 3 – GPU safety gate (cross‑cutting)

- [ ] T006 [P] Add `code/utils/gpu_check.py` that:
 * Calls `torch.cuda.is_available()` and inspects any `sklearn`/`xgboost` CUDA flags.
 * Writes result to `logs/gpu_check.log`.
 * Exits with code 1 if a GPU is detected, aborting the pipeline before any model training.

- Ensure `code/train.py` imports and runs this check as the first step.

---

## Phase 4 – Bias correction (cross‑cutting, before training)

- [ ] T012 [P] Create `code/bias_correction.py` implementing the bias‑layer generation required by the quick‑start run‑book (target‑group background or KDE). The script must read `data/processed/occurrence_model.csv`, produce `data/processed/bias_layer.tif`, and be invoked automatically **after preprocessing and before model training**.

---

## Phase 5 – Model training & baseline (User Story 2)

- [ ] T007 [US2] Implement `code/train.py` to:
 1. Generate spatial block CV indices (`K = 5`) via `code/utils/spatial_blocks.py`.
 2. Call the bias‑correction script (`bias_correction.py`) to create the bias layer.
 3. Train **Random Forest**, **Bioclim** (percentile envelope), and **MaxEnt‑style logistic regression** on `data/processed/occurrence_model.csv` using CPU‑only `scikit‑learn` (respecting blocks).
 4. Save model objects to `models/{species}_{algo}_historical.pkl`.
 5. Compute AUC and TSS on each held‑out block; write `metrics/training_metrics.csv`.
 6. Train a null prevalence model → `metrics/baseline_performance.csv`.
 7. Train a bias‑only random‑background model → `metrics/bias_null_metrics.csv`.

---

## Phase 6 – Projection, evaluation & statistical inference (User Story 3)

- [ ] T008 [US3] Implement `code/evaluate.py` to:
 1. **Projection**: Apply each trained model to recent climate rasters (`data/raw/climate_recent/`) and future climate rasters (`data/raw/climate_future/`) → suitability maps `projections/{species}_{algo}_recent.tif` and `projections/{species}_{algo}_2050.tif`.
 2. **Performance**: Evaluate recent projections against `data/raw/occurrence_2005_2020.csv` → per‑model AUC/TSS, stored in `metrics/evaluation_recent.csv`.
 3. **Delta suitability**: Compute mean suitability difference (2050 – recent) per species/algorithm → `metrics/delta_suitability.csv`.
 4. **Delta AUC/TSS** (FR‑009): Evaluate the 2050 projections against the same recent occurrence records, compute AUC/TSS, then calculate `delta_AUC = AUC_2050 – AUC_recent` and `delta_TSS = TSS_2050 – TSS_recent`; store results in `metrics/delta_auc_tss.csv`.
 5. **Hierarchical bootstrap on performance metrics** (FR‑010): Perform a hierarchical bootstrap (≥ 1000 iterations) on the per‑species AUC and TSS values (both recent and 2050) to obtain confidence intervals and p‑values; output `metrics/bootstrap_auc_tss.json`.
 6. **Threshold sensitivity**: Sweep absolute thresholds {0.01, 0.05, 0.10} around 0.5, recalculate rates, apply Holm‑Bonferroni correction → `metrics/sensitivity_report.csv`.

---

## Phase 7 – Final results, disclaimer & runtime budget

- [ ] T009 [P] Assemble final deliverables:
 * `metrics/final_results.csv` summarising model performance, delta suitability, delta AUC/TSS, bootstrap confidence intervals, and corrected p‑values.
 * `reports/associational_disclaimer.txt` containing the exact string “Findings are associational and assume niche stability”.
 * Log total pipeline wall‑time to `metrics/runtime.log`; if > 360 min, exit with code 1 and produce `metrics/runtime_optimization_report.txt` with concrete recommendations (e.g., reduce species count, increase batch size).

---

## Phase 8 – Quick‑start documentation

- [ ] T016 [P] Generate `quickstart.md` that documents the minimal steps to run the pipeline on a single species (including required commands, environment setup, and expected output files). Verify that executing the steps reproduces all artifacts listed in the contracts.
