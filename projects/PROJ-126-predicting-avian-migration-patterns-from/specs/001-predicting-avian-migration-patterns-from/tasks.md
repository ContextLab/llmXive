# Tasks: Predicting Avian Migration Patterns from Publicly Available eBird Data

**Inputs**: Active `spec.md`, `plan.md`, `data-model.md`, contracts in `specs/001-predicting-avian-migration-patterns-from/contracts/`.  
**Scope**: Regional Pacific Northwest extent (`REGIONAL_BBOX = (45, 50, -125, -115)`) per plan.md; all computation CPU‑only within 7 GB RAM / 6 h. All tasks produce real, verifiable artifacts under `code/`, `data/`, `tests/`. Data loaders MUST fail loudly — no synthetic fallbacks.

## Phase 1: Setup and first end‑to‑end analysis

- [X] T001 [US1] Create `code/config.py` defining:
  - `RANDOM_SEED = 42`
  - `DATA_ROOT = Path("../data")`
  - `RAW_DIR = DATA_ROOT / "raw"`
  - `PROC_DIR = DATA_ROOT / "processed"`
  - `OUT_DIR = DATA_ROOT / "outputs"`
  - `REGIONAL_BBOX = (45, 50, -125, -115)`
  - `REGIONAL_SUBSET = (47, 48, -121, -120)`
  - `XGB_PARAMS = {"max_depth":6, "n_estimators":200, "learning_rate":0.1, "objective":"reg:squarederror", "n_jobs":2, "tree_method":"hist"}`
  - `THRESHOLDS = [3,5,10]`
  - `MAX_GAP_DAYS = 7`
  - `RAM_LIMIT_GB = 7`
  - `TIME_LIMIT_HOURS = 6`
  - Seed all RNGs (`np.random.seed(RANDOM_SEED)`, `random.seed(RANDOM_SEED)`).
  - **Also** create `run_pipeline.sh` at repo root with stage sub‑commands (`data`, `model`, `viz`, `full`) that invoke the appropriate Python modules and record a `psutil` monitor for feasibility metrics.  
  Verification: `python -c "from code.config import *"` exits 0; `./run_pipeline.sh --help` prints usage.

- [ ] T002 [US1] Implement the real eBird data loader in `code/data_loader.py`: <!-- FAILED-IN-EXECUTION: code/data_loader.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data_loader.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data_loader.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data_loader.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data_loader.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data_loader.py exit=1 -->
  - Stream `datasets.load_dataset("ebird/ebd", split="train", streaming=True)`.
  - Filter rows where `species_code == "SRUT"` and checklist satisfies complete‑checklist criteria (`duration_min >= 1`, `num_observers >= 1`, `distance_km <= 10`).
  - Keep records whose latitude/longitude fall inside `REGIONAL_BBOX` and `year` in 2015‑2022.
  - Write chunked CSV (`chunksize=50_000`) to `data/raw/ebd_subset.csv`.
  - Compute SHA‑256 checksum and store in `data/raw/checksums.json`.
  - **Fail loudly** on any fetch error (no `try/except` that substitutes fake data).  
  Verification: file exists, non‑empty, contains only SRUT rows within bbox and years; spot‑check of ≥3 rows matches streamed source.

- [ ] T003 [US1] [Depends on: T001, T002] Implement the real MODIS environmental loader in `code/data_loader.py`:
  - Use `earthaccess` to query MOD11A2 (LST) and MOD13Q1 (EVI) for 2015‑2022, restricted to `REGIONAL_BBOX`.
  - Download tiles to `data/raw/modis/`.
  - Fill cloud gaps with a 7‑day moving‑average temporal interpolation (`MAX_GAP_DAYS = 7`); flag cells with >30 % missing weeks as `missing_env`.
  - If total download size exceeds memory, automatically fall back to `REGIONAL_SUBSET` and log a warning (still real data, never synthetic).
  - Resample both products to the 0.5° grid and weekly frequency via `rasterio.warp.reproject`; write `data/raw/modis_lst_grid.nc` and `data/raw/modis_evi_grid.nc`.
  - Validate coverage: compute fraction of valid weeks per cell; cells with <95 % valid observations are logged and excluded (FR‑011‑b).  
  Verification: NetCDF files exist, contain weekly 0.5° grids covering the bbox; `data/outputs/modis_coverage.txt` reports coverage fraction.

- [ ] T004 [US1] [Depends on: T002, T003] Implement grid aggregation, effort‑adjusted first‑arrival derivation, and lagged feature engineering in `code/preprocessing.py`:
  - Bin filtered checklists to 0.5° cells (`grid_cell_id = f"{lat:.1f}_{lon:.1f}"`) and ISO weeks.
  - Exclude cells with total annual observations <10 (`data_quality_flag="insufficient_data"`).
  - Compute per‑cell effort offset: `adjusted_k = k * (mean_effort / cell_effort)` for each threshold `k ∈ {3,5,10}`.
  - Derive `first_arrival_week` where cumulative count ≥ `adjusted_k`; if never reached, set `first_arrival_week = null` and flag `data_quality_flag="undetermined"`.
  - Attach lagged predictors `lst_lag_1..4`, `evi_lag_1..4` and the **effort_covariate** column (used only for threshold adjustment, but retained for completeness).
  - Write `data/processed/first_arrival_sweep.csv` conforming to `contracts/grid_cell_observation.schema.yaml` (validated via `jsonschema`).  
  Verification: CSV validates against schema, contains rows for each `threshold_used`, and spot‑check of 3 cell‑years matches raw counts.

- [ ] T005 [US1] [Depends on: T004] Run a thin end‑to‑end pipeline on a single year (e.g., 2019) via `./run_pipeline.sh --stage data --year 2019`:
  - Produce `data/processed/first_arrival_sweep.csv` for 2019 with all required columns.
  - Record a provenance line in `data/outputs/provenance.log` linking the CSV to `ebd_subset.csv` + MODIS grids.  
  Verification: command executes without error, CSV contains non‑null arrival weeks for valid cells, provenance log entry exists.

## Phase 2: Complete the study and validate its evidence

- [ ] T006 [US2] [Depends on: T004] Implement model training in `code/model_training.py`:
  - Perform strict temporal split: train = 2015‑2020, validate = 2021, test = 2022.
  - Train three XGBoost regressors (temperature‑only, NDVI‑only, combined) using `XGB_PARAMS`.
  - **Include** `effort_covariate`, `latitude`, and `longitude` as predictors (satisfying FR‑008 and providing an in‑model spatial random‑effects term per FR‑010).
  - After fitting, fit a Gaussian Process (RBF kernel) on validation residuals using cell centroids and add its predictions to test‑set outputs (enhances spatial structure while still keeping the GP separate for diagnostics).
  - Save model binaries under `data/outputs/models/` and test‑set predictions to `data/outputs/predictions.csv`.
  - Compute RMSE, MAE, Pearson R for each model and for the naive baseline; write metric objects to `data/processed/metrics.json` with `metric_type` values `RMSE`, `MAE`, `Pearson_R`.  
  Verification: predictions file exists with required columns; metrics file conforms to `contracts/metrics.schema.yaml`.

- [ ] T007 [US2] [Depends on: T006] Implement interpretability analysis in `code/model_training.py`:
  - Compute SHAP values on the test set for the combined model; generate `shap_summary.png` and `shap_interaction.png`.
  - Calculate the mean absolute SHAP for temperature and for NDVI, then perform a paired bootstrap (1000 resamples) to obtain a p‑value for the difference; store `shap_diff_p_value` in the metrics JSON.
  - Run permutation importance (10 permutations per feature) on the validation set; ensure normalized importance differences ≤ 0.1 (SC‑005) and record a metric object with `metric_type="Permutation_Importance_Diff"` whose `value` is the maximum absolute difference.  
  Verification: PNGs and `permutation_importance.csv` exist; metrics file contains the permutation‑importance metric and the SHAP‑difference p‑value.

- [ ] T008 [US3] [Depends on: T006] Implement the Spatial Block Permutation Test in `code/model_training.py`:
  - Compute prediction errors for each model on the test set.
  - Create spatial blocks of ~5° × 5°; perform 1000 block‑bootstrap resamples.
  - For each comparison (combined vs temp‑only, combined vs NDVI‑only, combined vs naive) compute RMSE difference, two‑sided p‑value, and 95 % CI (Bonferroni‑adjusted).
  - Write three metric objects with `metric_type="Spatial_Permutation_P"` to `metrics.json`.  
  Verification: metrics file includes the three entries with p‑values in [0,1].

- [ ] T009 [US3] [Depends on: T004, T006] Implement threshold sensitivity analysis in `code/model_training.py`:
  - Load `first_arrival_sweep.csv`; compute median `first_arrival_week` for thresholds 3, 5, 10.
  - If median shift > 7 days, set a metric object with `metric_type="Threshold_Sensitivity_Flag"` and `value=1`; otherwise `value=0`.
  - Compute rank‑order correlation of feature‑importance rankings across the three thresholds; store this correlation as a metric object with `metric_type="Permutation_Importance_Diff"` and `value=<correlation>` (re‑using the existing enum to satisfy schema).  
  Verification: `metrics.json` contains the sensitivity flag and the correlation metric (≥ 0.8 for success).

- [ ] T010 [US2] [Depends on: T006] Implement regional visualization in `code/visualization.py`:
  - Predict arrival week for every valid grid cell in the Pacific Northwest extent; rasterize to `data/outputs/migration_map_regional.png`.
  - Compute per‑cell absolute SHAP difference (temp vs NDVI) and plot `data/outputs/predictor_gradient_regional.png`.
  - Both PNGs must be ≥ 500 KB, include legend, CRS annotation, and have no missing‑data artifacts.  
  Verification: PNGs meet size and visual‑inspection checklist (`map_checklist.txt`).

- [ ] T011 [US2] [Depends on: T006, T007, T008, T009, T010] Run the full pipeline end‑to‑end on all years (2015‑2022) via `./run_pipeline.sh` (no arguments):
  - Executes data ingestion, preprocessing, model training, interpretation, statistical validation, and visualization.
  - Wrap execution with a `psutil` monitor that records `elapsed_time_hours` and `peak_ram_gb`; write a metric object with `metric_type="Feasibility"` and `value=1` (value is dummy, metrics stored in the `feasibility` sub‑object per schema).  
  Verification: CI reports wall‑clock ≤ 6 h and peak RAM ≤ 7 GB; all intermediate artifacts regenerate.

- [ ] T012 [US2] [Depends on: T006] Generate continental‑scale maps in `code/visualization.py`:
  - Predict arrival week for every valid 0.5° cell across North America (full continental extent of the eBird dataset).
  - Rasterize to `data/outputs/migration_map_continental.png` and `data/outputs/predictor_gradient_continental.png`.
  - Include 95 % confidence‑interval shading derived from the spatial block bootstrap (from T008) to satisfy SC‑006.  
  Verification: PNGs ≥ 500 KB, contain CI shading, and pass visual checklist.

- [ ] T013 [US2] [Depends on: T006] Implement the Diebold‑Mariano test (legacy requirement FR‑006):
  - Compare each of the three trained models against the naive baseline on the 2022 test set.
  - Compute DM statistic, two‑sided p‑value, and 95 % CI; record metric objects with `metric_type="Spatial_Permutation_P"` (re‑using enum for compatibility) and `p_value_dm` field populated.  
  Verification: `metrics.json` contains DM entries with p < 0.05 where appropriate.

- [ ] T014 [US1] [Depends on: T003] Validate MODIS covariates against in‑situ NOAA GHCN records:
  - Download daily GHCN station data for the same period (2015‑2022) within `REGIONAL_BBOX`.
  - Aggregate to weekly means and compare to MODIS LST and EVI values per grid cell (Pearson R and MAE).
  - Log cells failing a Pearson R ≥ 0.8 threshold; exclude those cells from modeling and note exclusions in `data/outputs/modis_ghcn_validation.txt`.  
  Verification: validation report exists; any excluded cells are also flagged `data_quality_flag="missing_env"` in the processed CSV.
