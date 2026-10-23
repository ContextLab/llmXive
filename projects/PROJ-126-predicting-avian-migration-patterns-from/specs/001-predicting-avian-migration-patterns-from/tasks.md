# Tasks: Predicting Avian Migration Patterns from Publicly Available eBird Data

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, and all JSON‑Schema contracts under `specs/001-predicting-avian-migration-patterns-from/contracts/`.  
All tasks produce real artifacts under `code/`, `data/`, or `tests/` and must fail loudly if any external download fails.

## Phase 0 – Setup and first end‑to‑end analysis  

- [X] T001 [US1] Create `code/config.py` with deterministic seeds, directory constants, full‑continent bounding box, XGBoost defaults, and analysis parameters.  
  - **Paths**: `code/config.py`  
  - **Verification**: `python -c "import code.config"` exits 0; the module defines constants for FR‑001 and FR‑004.  

- [ ] T002 [US1] Implement the eBird Basic Dataset loader in `code/data_loader.py`.   <!-- FAILED-IN-EXECUTION: code/data_loader.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data_loader.py exit=1 --> <!-- FAILED: unspecified -->
  - Stream `datasets.load_dataset("vvud/eb-data", split="train", streaming=True)`.  
  - Filter rows: `species_code == "SRUT"` and complete‑checklist criteria (`duration_min ≥ 1`, `num_observers ≥ 1`, `distance_km ≤ 10`).  
  - Keep records with latitude/longitude inside the full North American bbox (`LAT_MIN=15, LAT_MAX=75, LON_MIN=-170, LON_MAX=-50`) and years 2015‑2022.  
  - Write chunked CSV (`chunksize=50_000`) to `data/raw/ebd_subset.csv`.  
  - Compute SHA‑256 checksum and store in `data/raw/checksums.json`.  
  - **Fail loudly** on any fetch error (no synthetic fallback).  
  - **Verification**: CSV exists, non‑empty, contains only SRUT rows within bbox/years; spot‑check ≥ 3 rows match the streamed source.  

- [ ] T003 [US1] Implement MODIS environmental data acquisition and preprocessing in `code/data_loader.py`.  
  - Download MODIS 8‑day LST (MOD11A2) and 16‑day NDVI (MOD13Q1) composites from the **verified HuggingFace archive** `https://huggingface.co/datasets/earthmod/modis-8day/resolve/main/modis_8day.npz`.  
  - Load the NPZ, extract `lst` and `ndvi` arrays.  
  - Fill cloud gaps with a 7‑day moving‑average interpolation (`MAX_GAP_DAYS = 7`); flag cells with >30 % missing weeks as `missing_env`.  
  - Resample both products to a 0.5° × 0.5° grid and aggregate to true weekly means via `rasterio.warp.reproject`.  
  - Write NetCDFs `data/raw/modis_lst_weekly.nc` and `data/raw/modis_ndvi_weekly.nc`.  
  - Validate coverage: compute per‑cell valid‑week fraction; cells with < 95 % coverage are logged and excluded (FR‑011).  
  - **Verification**: NetCDF files exist, contain weekly grids covering the bbox; `data/outputs/modis_coverage.txt` reports ≥ 95 % coverage for retained cells.  

- [ ] T004 [US1] Implement grid aggregation and first‑arrival derivation in `code/preprocessing.py`.  
  - Bin filtered eBird checklists to 0.5° cells (`grid_cell_id = f"{lat:.1f}_{lon:.1f}"`) and ISO weeks.  
  - Exclude cells with total annual observations < 10 (`data_quality_flag="insufficient_data"`).  
  - For each cumulative‑count threshold *k* ∈ {3, 5, 10}, **adjust the threshold by the per‑cell effort covariate** (offset = `effort_covariate / mean_effort_global`) before comparing to cumulative counts; compute the week where the offset‑adjusted cumulative count first reaches *k*. If never reached, set `first_arrival_week = null` and flag `data_quality_flag="undetermined"`.  
  - Attach lagged predictors `lst_lag_1…4`, `ndvi_lag_1…4` (weekly means from the MODIS NetCDFs) and the **effort_covariate** (total complete checklists per cell‑year, used only as a predictor).  
  - Write `data/processed/first_arrival_sweep.csv` that validates against **`contracts/grid_cell_observation.schema.yaml`** (single schema).  
  - **Verification**: `jsonschema.validate` passes for the CSV; a spot‑check of three cell‑years matches raw counts and lagged values.  

- [ ] T012 [US1] Validate MODIS covariates against NOAA GHCN stations in `code/modis_validation.py`.  
  - Download daily GHCN temperature records for 2015‑2022 within the continental bbox.  
  - Aggregate to weekly means per grid cell and compute Pearson R and MAE against the MODIS LST weekly values.  
  - Log any cell with Pearson R < 0.95 to `data/outputs/modis_ghcn_validation.txt`; exclude those cells from modeling by marking `data_quality_flag="missing_env"` in `first_arrival_sweep.csv`.  
  - **Verification**: Validation report exists; flagged cells are absent from the final modeling CSV.  

- [ ] T005 [US1] Run a thin end‑to‑end pipeline on a small sampled region/year to verify data flow and model training without full compute.  
  - Sample a single 0.5° grid cell and a single year (e.g., 2020) from `first_arrival_sweep.csv`.  
  - Execute the full preprocessing, model training (using a reduced XGBoost config), and prediction steps on this subset via `code/run_thin_pipeline.py`.  
  - Verify that all intermediate files are created and that a prediction CSV with at least one row is produced.  
  - **Verification**: Script exits 0; output files exist; sanity‑check asserts predicted arrival week is within 1‑52.  

## Phase 1 – Complete the study and validate its evidence  

- [ ] T006 [US2] Train Gradient Boosting Regressors in `code/model_training.py`.  
  - Temporal split: train = 2015‑2020, validate = 2021, test = 2022.  
  - Train three XGBoost models (temperature‑only, NDVI‑only, combined) using `XGB_PARAMS` from `config.py`.  
  - Predictors: lagged environmental variables, `effort_covariate`, latitude, longitude, and a **Gaussian Process spatial random‑effects term** (e.g., `sklearn.gaussian_process.GaussianProcessRegressor` with a suitable kernel) to capture residual spatial structure (FR‑010).  
  - Save model binaries to `data/outputs/models/` (`*_temp.json`, `*_ndvi.json`, `*_combined.json`).  
  - Generate test‑set predictions (`data/outputs/predictions.csv`) with columns `grid_cell_id, year, week_number, predicted_arrival_day, actual_arrival_day, residual, shap_lst, shap_ndvi`.  
  - Compute RMSE, MAE, Pearson R for each model and for a naive baseline (mean training‑set arrival week). Write a `metrics.json` file containing objects of type `model_metrics.schema.yaml`.  
  - **Verification**: Model files are valid JSON; predictions CSV exists with required columns; `metrics.json` validates against `contracts/model_metrics.schema.yaml`.  

- [ ] T007 [US2] Perform primary statistical comparison via Diebold‑Mariano test (HAC‑corrected) in `code/evaluation.py`.  
  - Compare prediction errors of each XGBoost model against the naive baseline on the 2022 test set.  
  - Record DM statistic, two‑sided p‑value, and 95 % confidence interval for each comparison.  
  - Append metric objects with `metric_type="Diebold_Mariano"` and populate the `p_value_dm` field.  
  - **Verification**: `metrics.json` contains three DM entries; each p‑value is a number in `[0,1]`.  

- [ ] T008 [US2] Conduct secondary spatial block bootstrap validation in `code/evaluation.py`.  
  - Partition the continental grid into ~5° × 5° spatial blocks.  
  - Perform 1 000 block‑bootstrap resamples of test‑set errors for each model pair (combined vs temp‑only, combined vs NDVI‑only, combined vs naive).  
  - Compute RMSE difference distribution, two‑sided p‑value, and 95 % CI (Bonferroni‑adjusted).  
  - Store three metric objects with `metric_type="Spatial_Block_Bootstrap_P"` and a `value` field equal to the p‑value.  
  - **Verification**: `metrics.json` now includes three bootstrap‑p‑value entries; values lie in `[0,1]`.  

- [ ] T009 [US2] Run interpretability analyses in `code/model_interpretation.py`.  
  - Compute SHAP values for the combined model on the test set; generate `shap_summary.png` and `shap_interaction.png` in `data/outputs/`.  
  - Calculate mean absolute SHAP for temperature and NDVI; perform a paired bootstrap (1 000 resamples) to obtain a p‑value for the difference; record `shap_diff_p_value` in `metrics.json`.  
  - Execute permutation importance (10 permutations per feature) on the validation set; ensure the maximum absolute difference between any two normalized importance scores ≤ 0.1 (SC‑005). Store a metric object with `metric_type="Permutation_Importance_Diff"` and `value` equal to the observed maximum difference.  
  - **Verification**: PNGs exist and are ≥ 500 KB; `metrics.json` contains `shap_diff_p_value` and the permutation‑importance metric with a numeric value ≤ 0.1.  

- [ ] T010 [US2] Perform threshold‑sensitivity analysis in `code/sensitivity.py`.  
  - Load `first_arrival_sweep.csv`; for thresholds 3, 5, 10 compute the median `first_arrival_week`.  
  - If the median shift across thresholds exceeds 7 days, set a metric object `metric_type="Threshold_Sensitivity_Flag"` with `value=1`; otherwise `value=0`.  
  - For each threshold, compute the feature‑importance ranking (from permutation importance); calculate the Spearman rank‑order correlation across the three rankings and store it as a metric object with `metric_type="Threshold_Rank_Correlation"` and `value` equal to the correlation (must be ≥ 0.8 for success).  
  - **Verification**: `metrics.json` contains the sensitivity flag and the correlation metric; correlation ≥ 0.8 is reported.  

- [ ] T015 [US2] Validate output artifacts against `output.schema.yaml`.  
  - Run `jsonschema.validate` on `metrics.json` and each model output JSON file using `contracts/output.schema.yaml`.  
  - Fail loudly if any artifact does not conform.  
  - **Verification**: Validation passes; no schema errors reported.  

- [ ] T016 [US2] Execute feasibility CI test.  
  - A pytest test `tests/test_feasibility.py` reads `metrics.json.feasibility` and asserts `elapsed_time_hours ≤ 6` and `peak_ram_gb ≤ 7`.  
  - T014 (full pipeline) now runs this test as part of its verification.  
  - **Verification**: `pytest -q tests/test_feasibility.py` exits 0.  

## Phase 2 – Reproducible results and paper handoff  

- [ ] T011 [US2] Generate continental‑scale visualizations in `code/visualization.py`.  
  - Predict arrival week for every valid 0.5° cell across North America using the combined model plus the GP random‑effects adjustment.  
  - Rasterize predictions to `data/outputs/migration_map_continental.png`.  
  - Compute per‑cell absolute SHAP difference (temp vs NDVI) and rasterize to `data/outputs/predictor_gradient_continental.png`, overlayting 95 % confidence‑interval shading derived from the spatial block bootstrap (T008).  
  - Both PNGs must be ≥ 500 KB, include a legend, CRS annotation, and contain no missing‑data artifacts.  
  - **Verification**: File sizes ≥ 500 KB; a quick visual checklist (`map_checklist.txt`) confirms legend, CRS, and no NaN patches.  

- [ ] T013 [US2] Build a provenance manifest in `code/provenance.py`.  
  - After each pipeline stage, append a line to `data/outputs/provenance.log` of the form:  
    `output_file ← input_file1 + input_file2 [+ …]`.  
  - Include entries for raw eBird CSV, MODIS NetCDFs, processed CSV, model binaries, predictions, metrics, and both PNG maps.  
  - **Verification**: `provenance.log` contains one line per generated artifact and passes a simple parser test (`tests/test_provenance.py`).  

- [ ] T014 [US1] Execute the full end‑to‑end pipeline via `./run_pipeline.sh` (no arguments).  
  - The script runs data ingestion, preprocessing, MODIS validation, model training, evaluation, interpretability, sensitivity, validation, visualization, and provenance logging.  
  - A `psutil` monitor records `elapsed_time_hours` and `peak_ram_gb`; these are written into `metrics.json` under the `feasibility` sub‑object (conforming to `contracts/metrics.schema.yaml`).  
  - CI asserts `elapsed_time_hours ≤ 6` and `peak_ram_gb ≤ 7` via the pytest feasibility test (T016).  
  - **Verification**: CI logs show wall‑clock ≤ 6 h and peak RAM ≤ 7 GB; `metrics.json` contains the feasibility sub‑object with numeric values; pytest feasibility test passes.  

---  

### Mapping of functional requirements → tasks  

| FR | Covered by |
|----|------------|
| FR‑001 | T002 |
| FR‑002 / FR‑002a | T003 |
| FR‑003 | T004 (effort offset applied) |
| FR‑004 | T006 |
| FR‑005 | T009 |
| FR‑006 | T007 (primary DM) |
| FR‑007 | T011 |
| FR‑008 | T004 (effort_covariate as predictor) |
| FR‑009 | T008 |
| FR‑010 | T006 (Gaussian Process random‑effects) |
| FR‑011 | T012 |
| FR‑012 | T013 |

All success criteria (SC‑001 … SC‑007) are verified in the respective tasks’ “Verification” sections.  
