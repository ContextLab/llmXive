# Tasks: Predicting Species Distribution Shifts Using Historical Occurrence Records and Climate Data

**Inputs**: `spec.md`, `plan.md`, existing research artifacts, and reviewer feedback.  
**Goal**: Deliver a reproducible end‑to‑end pipeline that satisfies every functional requirement (FR‑001 – FR‑019) and success criteria (SC‑001 – SC‑005) while respecting the platform constitution (real data only, CPU‑only execution, strict provenance).

---

## Phase 0 – Project bootstrap (foundational, can run in parallel)

- [ ] T001 [P] **Create full project scaffold**  
  - Create `requirements.txt`, `pyproject.toml`, and a root‑level `.flake8`.  
  - Add a `quickstart.md` placeholder.  
  - Populate each top‑level directory (`code/`, `data/raw/`, `data/processed/`, `models/`, `metrics/`, `logs/`, `reports/`, `tests/`, `contracts/`) with a `.gitkeep` file **including `metrics/` and `logs/`**.  
  - **Verification**: `git ls-files` shows the `.gitkeep` files in **all** directories and `.flake8` resides at the repository root.

- [X] T002 [P] **Add global configuration** – `code/config.py` with constants (species list, paths, `THINNING_DISTANCE_KM`, random seeds, `n_jobs=2`). *(Already completed and verified.)*

- [ ] T003 [P] **Initialize structured logging**  
  - Create `logs/logging_config.yaml` defining format `%(asctime)s - %(name)s - %(levelname)s - %(message)s` and level INFO.  
  - Add a small helper `code/logging_setup.py` that loads this YAML and configures the root logger.  
  - Ensure all scripts import `setup_logger = get_logger(__name__)` from `llmxive_toolkit`.  
  - **Verification**: Running any pipeline script creates `logs/<script>.log` matching the YAML schema and `logs/preprocess_counts.yaml` contains a non‑empty list of objects each matching `contracts/log_counts.schema.yaml`.

---

## Phase 1 – Data acquisition (User Story 1)

- [ ] T004 [US1] **Implement robust download script** – `code/download.py` must:   <!-- FAILED-IN-EXECUTION: tests/unit/test_download.py exit=1 -->
  1. Stream historical occurrence records (1970‑2000) from GBIF/eBird via `pygbif`, write to `data/raw/occurrence_historic.csv` **including columns** `gbif_key`, `source`, `download_timestamp`, `dataset_name`.  
  2. Stream recent occurrence records (2005‑2020) to `data/raw/occurrence_recent.csv` with the same provenance columns.  
  3. Stream WorldClim v2 historical rasters (bio1‑bio19) to `data/raw/climate_historic/`.  
  4. Stream WorldClim CMIP6 SSP2‑4.5 2050 rasters to `data/raw/climate_future/`.  
  5. Update `data/manifest.json` with URL, download timestamp, file size, and **verified** SHA‑256 checksum field.  
  6. Abort with a non‑zero exit code if any download fails, times out, or checksum mismatch occurs.  
  - **Verification**: After execution, `data/manifest.json` contains an entry for each file, the expected files exist on disk, and provenance columns are present in both CSVs.

- [ ] T010 [US1] **Add SHA‑256 checksum verification** (enhancement of `code/download.py`)  
  - For every raster (and any large CSV), download the accompanying `.sha256` file (or compute expected hash from a provided manifest).  
  - After each download, **compute the local SHA‑256**, compare to the expected value, and **abort on mismatch**, deleting the corrupted file.  
  - Record the verified checksum in `data/manifest.json`.  
  - **Verification**: Running the script on a fresh runner with an intentionally corrupted file results in an abort and a clear error message; successful runs write matching `checksum_sha256` values to the manifest.

- [ ] T015 [P] **Generate and validate data contracts**   <!-- FAILED-IN-EXECUTION: code/validate_contracts.py exit=1 -->
  - Write YAML schema files under `contracts/` for all core artifacts (`occurrence.schema.yaml`, `occurrence_record.schema.yaml`, `climate_raster.schema.yaml`, `climate_variable.schema.yaml`, `data_sufficiency.schema.yaml`, `model_artifact.schema.yaml`, `model_metrics.schema.yaml`, `log_counts.schema.yaml`).  
  - Add a validation utility `code/validate_contracts.py` that loads each artifact and validates against its schema, aborting on any violation.  
  - **Verification**: `python -m code.validate_contracts` exits with code 0 on a fresh download; any schema breach prints the offending file and line.

---

## Phase 2 – Pre‑processing & data‑sufficiency (User Story 1)

- [ ] T005 **Pre‑process occurrence and climate data** (`code/preprocess.py`)  
  1. Apply species‑specific breeding‑season month filter.  
  2. Remove exact duplicate latitude/longitude pairs.  
  3. Perform spatial thinning: compute nearest‑neighbor distances; enforce a minimum of **10 km** or the 95th‑percentile distance if the user overrides via `config.THINNING_DISTANCE_KM`.  
  4. Log before/after counts per species to `logs/preprocess_counts.yaml`.  
  5. Extract all 19 Bioclim variables from historical rasters at each thinned point → `data/processed/occurrence_full_historic.csv`.  
  6. Run VIF analysis, iteratively drop variables with VIF > 10, save selected variable list to `metrics/selected_climate_variables.json`.  
  7. Subset the full table to the selected variables → `data/processed/occurrence_model_historic.csv`.  
  8. Repeat steps 1‑7 for recent occurrence records (using recent climate rasters) → `data/processed/occurrence_model_recent.csv`.  
  9. Conduct power analysis (bootstrap AUC 500 times per species) to detect ΔAUC ≥ 0.05 with power ≥ 0.8; write results to `metrics/data_sufficiency.json` (conforms to `data_sufficiency.schema.yaml`).  
  - **Verification**: `logs/preprocess_counts.yaml` contains a non‑empty list of objects matching `log_counts.schema.yaml`; `metrics/data_sufficiency.json` includes a status of `SUFFICIENT` for at least 95 % of target species.

- [ ] T018 [P] **Compute data‑acquisition completeness metrics** (`code/completeness.py`)  
  - After preprocessing, calculate (a) proportion of target species with ≥ 100 thinned records and (b) proportion of records with non‑null climate values.  
  - Write summary to `metrics/data_acquisition_completeness.json`.  
  - **Verification**: The JSON contains keys `species_coverage` and `climate_coverage` with values ≥ 0.95 and ≥ 0.99 respectively; the file validates against an implicit schema used in the pipeline.

- [ ] T011 [P] **Unit & integration testing suite** (`tests/`)  
  - `tests/unit/test_download.py` checks pagination, streaming, and checksum handling.  
  - `tests/unit/test_preprocess.py` validates breeding‑season filter, thinning distance, VIF removal, and power‑analysis flagging.  
  - `tests/unit/test_gpu_check.py` ensures the GPU guard aborts when `torch.cuda.is_available()` is True.  
  - `tests/unit/test_train.py` verifies block generation, model fitting, and metric output shapes.  
  - `tests/unit/test_evaluate.py` confirms projection, AUC/TSS calculation, ΔAUC/TSS, and MESS masking.  
  - `tests/integration/test_end_to_end.py` runs the full pipeline on a single low‑complexity species (e.g., *Cardinalis cardinalis*) and asserts creation of all expected artifacts.  
  - **Verification**: `pytest -q` passes with 0 failures on a fresh runner.

---

## Phase 3 – Cross‑cutting safety (GPU guard)

- [ ] T006 [P] **GPU safety gate** (`code/utils/gpu_check.py`)  
  - Detect CUDA availability via `torch.cuda.is_available()` and any `sklearn`/`xgboost` CUDA flags.  
  - Write result to `logs/gpu_check.log` and exit with code 1 if a GPU is present, preventing any downstream CPU‑only code from accidentally invoking CUDA.  
  - Import and call this guard at the start of `code/train.py` and `code/evaluate.py`.  
  - **Verification**: Running `code/train.py` on a machine with a GPU produces a log entry and exits with status 1; on CPU‑only runners it proceeds normally.

---

## Phase 4 – Bias‑correction layer (pre‑training)

- [ ] T012 [P] **Generate shared bias‑correction layer** (`code/bias_correction.py`)  
  - Read `data/processed/occurrence_model_historic.csv` **and** `data/processed/occurrence_model_recent.csv` combined to compute a kernel‑density raster `data/processed/bias_layer.tif`.  
  - The raster must include metadata matching `climate_raster.schema.yaml` (raster_id, variable_name = “bias”, checksum, etc.).  
  - **Verification**: Raster file exists, is a valid GeoTIFF, passes schema validation, and downstream tasks reference `bias_layer.tif` for both historic and recent background sampling.

---

## Phase 5 – Model training & baseline (User Story 2)

- [ ] T007 [US2] **Train SDM algorithms with spatial block CV** (`code/train.py`)  
  1. Load `data/processed/occurrence_model_historic.csv`.  
  2. Generate spatial block indices (K = 5) via `code/utils/spatial_blocks.py`.  
  3. Run GPU guard (`gpu_check.py`).  
  4. Train three algorithms on each of the ≤ 5 target species (FR‑019):  
     - Random Forest (`n_estimators=500`).  
     - Bioclim envelope (range‑based).  
     - MaxEnt‑style surrogate (logistic regression on VIF‑filtered predictors).  
  5. Save each model as `models/{species}_{algorithm}_historic.pkl` with accompanying metadata JSON (`model_artifact.schema.yaml`).  
  6. Compute AUC and TSS on each held‑out block; store per‑fold results in `metrics/training_metrics_{species}_{algorithm}.json`.  
  7. Train a null prevalence model (baseline) and a bias‑only background model; persist their metrics in `metrics/baseline_performance.json`.  
  - **Verification**: All model artifacts validate against `model_artifact.schema.yaml`; each `training_metrics` file contains exactly 5 fold entries and the **system‑wide** average AUC across all trained models is ≥ 0.70 (fulfilling SC‑001).

- [ ] T007.1 [P] **Baseline null‑model creation** (sub‑task) – ensures null model is generated and evaluated for SC‑001 comparison.  

---

## Phase 6 – Projection, evaluation & statistical inference (User Story 3)

- [ ] T008 [US3] **Evaluate models on recent data and project to future climate** (`code/evaluate.py`)  
  1. Load each trained model from `models/`.  
  2. Apply bias‑corrected background sampling using the **shared** `data/processed/bias_layer.tif`.  
  3. Project suitability onto recent climate rasters → `projections/{species}_{algorithm}_recent.tif`.  
  4. Project onto 2050 SSP2‑4.5 rasters → `projections/{species}_{algorithm}_2050.tif`.  
  5. Compute AUC, TSS, and Brier score on the recent test set (`data/raw/occurrence_recent.csv`); store in `metrics/evaluation_recent_{species}_{algorithm}.json`.  
  6. Compute AUC/TSS on the 2050 projections against the same recent test set; calculate ΔAUC and ΔTSS, save to `metrics/delta_auc_tss_{species}_{algorithm}.json`.  
  7. Generate MESS (Multivariate Environmental Similarity Surface) between historical and future climate layers; mask non‑analog pixels and record proportion of analog space (`mop_proportion`) in the same JSON.  
  8. Perform a hierarchical bootstrap (≤ 500 iterations) across species and spatial blocks to obtain confidence intervals and p‑values for ΔAUC, ΔTSS, and MESS‑derived stability; write `metrics/bootstrap_{species}_{algorithm}.json`.  
  9. Apply Benjamini‑Hochberg correction to all p‑values and store corrected values in the same JSON.  
  - **Verification**: All JSON files conform to `model_metrics.schema.yaml` and `performance_metric.schema.yaml`; the bootstrap file contains `p_value` ≤ 1 and `corrected_p_value` ≤ 1.

---

## Phase 7 – Final results, disclaimer & runtime budget

- [ ] T009 [P] **Assemble final deliverables**  
  - Consolidate per‑species, per‑algorithm results into `metrics/final_results.csv` (columns: species, algorithm, historic_AUC, recent_AUC, delta_AUC, historic_TSS, recent_TSS, delta_TSS, MESS_proportion, composite_stability, p_value, corrected_p_value).  
  - Write `reports/associational_disclaimer.txt` containing the exact sentence: **“Findings are associational and assume niche stability.”**  
  - Record total wall‑clock time in `metrics/runtime.log`; if runtime > 360 min, exit with error and produce `metrics/runtime_optimization_report.txt` outlining concrete reductions (e.g., lower bootstrap iterations, fewer species).  
  - **Verification**: The CSV passes a schema check (all required columns present, numeric ranges respected); the disclaimer file exists verbatim; runtime log is parsable and the pipeline exits with non‑zero code only when the 6‑hour limit is exceeded.

---

## Phase 8 – Quick‑start documentation

- [ ] T016 [P] **Generate clear quick‑start guide** (`quickstart.md`)  
  - Document a minimal one‑species run: required environment (`pip install -r requirements.txt`), command `python -m code.download --species Cardinalis_cardinalis --period historic`, `python -m code.preprocess`, `python -m code.train`, `python -m code.evaluate`, and expected output locations.  
  - Include a verification command that checks for the presence of `metrics/final_results.csv` and prints the first three rows.  
  - **Verification**: Following the guide on a fresh runner reproduces all listed artifacts without errors.

---

## Dependency‑to‑requirement mapping (for reviewer reference)

| Requirement | Satisfying Task(s) |
|-------------|-------------------|
| FR‑001, FR‑002, FR‑016 | T004, T010, T015 |
| FR‑003, FR‑014 | T005 |
| FR‑004 | T007 (CPU‑only libraries) |
| FR‑007 | T007 (spatial block CV) |
| FR‑009, FR‑018, FR‑019 | T008 (bootstrap, power analysis, iteration limits) |
| FR‑017 | T012 (single shared bias layer) |
| FR‑018 | T005 (power analysis) |
| FR‑009 (ΔAUC/TSS) | T008 |
| SC‑001, SC‑004, SC‑005 | T007, T008, T009, T018 |
| SC‑002 (runtime) | T009 (runtime monitoring) |
| Edge‑case handling (INSUFFICIENT_DATA, missing climate) | T005 (flags), T008 (skip/exclude) |

--- 

*All tasks are unchecked except the already‑verified scaffold creation (T002). Reopened tasks (T001, T003, T004, T010) must be completed before the pipeline can be considered runnable.*  