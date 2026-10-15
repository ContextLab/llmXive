# Tasks: Predicting Avian Song Variation with Climatic and Geographic Factors

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, and all contract schemas.  
All tasks are unchecked unless explicitly marked as completed (`[X]`) in a prior run and still valid.

---

## Phase 0 – Project Scaffold & Core Infrastructure  

- [X] T002 [P] Initialize Python project scaffold **[FR‑001]**  
  - **File**: `requirements.txt` (pins exact versions of pandas, numpy, scikit‑learn, statsmodels, scipy, matplotlib, seaborn, pyyaml, requests, rasterio, geopandas, pyproj, pytest) and `pyproject.toml` (basic build metadata).  
  - **Verification**: `pip install -r requirements.txt` succeeds without warnings; `pyproject.toml` is syntactically valid.

- [ ] T003 [P] Configure linting and formatting tools **[FR‑001]**  
  - **Files**: `.ruff.toml` (enable ruff linting), `pyproject.toml` (add `[tool.black]` section), optional `.pre-commit-config.yaml`.  
  - **Verification**: CI step `ruff check .` returns exit 0; `black --check .` returns exit 0.

- [X] T005 [P] Implement configuration loader with default `join_radius_km = 10` km **[FR‑001]**  
  - **File**: `code/config.py` exposing a `Config` dataclass that reads environment variables (e.g., `JOIN_RADIUS_KM`) and falls back to the default 10 km.  
  - **Verification**: `python -c "from code.config import Config; assert Config().join_radius_km == 10"` runs without assertion error.

- [X] T007 [P] Create schema definition files for all entities **[FR‑001]**  
  - **Files**: `contracts/song_record.schema.yaml`, `contracts/climate_snapshot.schema.yaml`, `contracts/analysis_dataset.schema.yaml`, `contracts/aggregated_pvalues.schema.yaml`, `contracts/analysis_output.schema.yaml`.  
  - **Verification**: `jsonschema.validate({}, schema)` succeeds for a minimal valid instance of each entity.

---

## Phase 0 – Data Acquisition (Verified Input)

- [ ] T001 [P] Download verified `analysis_dataset.parquet` from HuggingFace **[FR‑001]**  
  - **File**: `data/raw/analysis_dataset.parquet` (download URL listed in `contracts/analysis_dataset.schema.yaml`).  
  - **Requirement**: Compute SHA‑256 checksum and append `analysis_dataset.parquet  <sha256>` to `data/checksums.txt`.  
  - **Verification**: Checksum line exists; `utils.update_state_file()` records hash in project state YAML.

- [X] T004a [P] Detect CRS of any user‑supplied climate raster **[FR‑001]**  
  - **File**: `code/ingestion.py` (uses `rasterio` to read CRS).  
  - **Verification**: Logs detected CRS; proceeds to reprojection if needed.

- [X] T004b [P] Reproject raster to EPSG:4326 when necessary **[FR‑001]**  
  - **File**: `code/ingestion.py` (uses `pyproj`/`rasterio.warp`).  
  - **Verification**: Reprojected raster saved; CRS check confirms EPSG:4326.

---

## Phase 1 – Merge Validation

- [ ] T018 [P] Validate merge quality and compute match proportion **[SC‑001]**   <!-- FAILED-IN-EXECUTION: code/ingestion.py exit=1 -->
  - **File**: `code/ingestion.py` (after loading `analysis_dataset.parquet`).  
  - **Steps**: Verify species IDs and coordinate precision; log mismatches; abort if >5 % of rows mismatched; record `match_rate` in `outputs/merge_validation.json`.  
  - **Verification**: JSON file exists and contains `match_rate`; CI test asserts `match_rate` is a float between 0 and 1.

- [ ] T017 [P] Record final dataset checksum & state entry **[FR‑001]**  
  - **File**: `data/processed/analysis_dataset.parquet` (copied from raw after validation).  
  - **Requirement**: Append checksum line to `data/checksums.txt` and call `utils.update_state_file()`.  
  - **Verification**: Checksum line present; state YAML contains matching hash.

---

## Phase 2 – Exploratory Data Analysis (User Story 2)

- [ ] T010 [P] Compute summary statistics **[FR‑002]**  
  - **File**: `code/eda.py`.  
  - **Output**: `outputs/summary_stats.json` (mean, std, min, max for all continuous variables).  
  - **Verification**: JSON loads; all required fields present.

- [ ] T011 [P] Compute Pearson correlation matrix **[FR‑002]**  
  - **File**: `code/eda.py`.  
  - **Output**: `outputs/correlation_matrix.json`.  
  - **Verification**: Matrix is symmetric, diagonal entries exactly 1.0, all values ∈ [-1.0, 1.0].

- [ ] T012 [P] Compute VIF for Model B predictors and flag pairs **[FR‑005]**  
  - **File**: `code/eda.py`.  
  - **Output**: `outputs/vif_pairs.json` (list of `{predictor, vif, partner, partner_corr}` where `vif > 5`).  
  - **Verification**: Test asserts at least one entry when VIF exceeds threshold.

- [ ] T013 [P] Compute Moran's I on Model B residuals **[FR‑003]**  
  - **File**: `code/eda.py`.  
  - **Output**: `outputs/morans_i.json` (statistic and p‑value).  
  - **Verification**: Test checks JSON keys and that p‑value is a float.

- [ ] T014 [P] Assemble full EDA report **[FR‑002]**  
  - **File**: `outputs/eda_report.json` (consolidates summary, correlation, VIF, Moran's I).  
  - **Verification**: JSON loads; contains keys `summary_stats`, `correlation_matrix`, `vif_pairs`, `morans_i`.

---

## Phase 3 – Power Analysis

- [ ] T016 [P] Perform a priori and post‑hoc power analysis **[SC‑002]**  
  - **File**: `code/power.py`.  
  - **Inputs**: Effect size = 0.15, α = 0.05, predictors = 5, actual sample size from `analysis_dataset.parquet`.  
  - **Output**: `outputs/power_analysis.json` (required_n, actual_n, achieved_power, underpowered flag).  
  - **Verification**: Test asserts `underpowered` is true only when `actual_n < required_n`.

---

## Phase 4 – Predictive Modeling (User Story 3)

- [ ] T020 [P] Fit Null models for both outcomes **[FR‑003]**  
  - **File**: `code/modeling.py`.  
  - **Outputs**: `data/models/null_song_metric_1.pkl`, `null_song_metric_2.pkl`.  

- [ ] T021 [P] Fit Climate‑Only (Model A) for both outcomes **[FR‑003]**  
  - **Outputs**: `data/models/model_a_song_metric_1.pkl`, `model_a_song_metric_2.pkl`.  

- [ ] T022 [P] Fit Full models (Model B) for both outcomes **[FR‑003]**  
  - **Outputs**: `data/models/model_b_song_metric_1.pkl`, `model_b_song_metric_2.pkl`.  

- [ ] T023 [P] Verify Model B improves over Null (R² gain & F‑test p < 0.05) **[SC‑002]**  
  - **File**: `code/modeling.py`.  
  - **Output**: `outputs/model_performance.json` (R², adj R², global F‑test p‑value for each model).  
  - **Verification**: CI test asserts `delta_r2 > 0` and `p_value_global < 0.05` for both outcomes.

- [ ] T024 [P] Aggregate all predictor p‑values **[FR‑006]**  
  - **File**: `code/modeling.py`.  
  - **Output**: `aggregated_pvalues.parquet` (conforms to `contracts/aggregated_pvalues.schema.yaml`).  

- [ ] T025c [P] Apply global Benjamini‑Hochberg FDR correction **[FR‑006]**  
  - **File**: `code/modeling.py`.  
  - **Output**: Updated `aggregated_pvalues.parquet` with `q_value` column; also stored in `outputs/fdr_corrected_pvalues.parquet`.  
  - **Verification**: Schema validation passes; spot‑check ensures at least one q ≤ 0.05 when corresponding p is low.

- [ ] T026 [P] Summarize modeling results **[FR‑003]**  
  - **File**: `outputs/model_summary.csv` (validated by `contracts/analysis_output.schema.yaml`).  

---

## Phase 5 – Sensitivity & Omitted‑Variable Bias

- [ ] T030 [P] Sensitivity sweep over significance thresholds {0.01, 0.05, 0.10} **[SC‑003]**  
  - **File**: `code/modeling.py`.  
  - **Output**: `outputs/sensitivity_report.json` (threshold, num_significant, R²).  

- [ ] T031 [P] Compute Jaccard stability between successive thresholds **[SC‑003]**  
  - **File**: `code/modeling.py`.  
  - **Output**: `outputs/sensitivity_report.json` (adds `jaccard_to_next` for each threshold).  
  - **Verification**: Test asserts Jaccard values are between 0 and 1.

- [ ] T032 [P] Omitted‑variable‑bias assessment (optional proxies) **[FR‑003]**  
  - **Output**: `outputs/omitted_variable_bias.json`.  

---

## Phase 6 – Reporting, Figures & Provenance

- [ ] T040 [P] Generate required figures **[FR‑002]**  
  - **Files**: `outputs/figures/correlation_heatmap.png`, `vif_pair_bar.png`, `morans_i_plot.png`, `r2_vs_threshold.png`.  
  - **Verification**: Each PNG exists, > 5 KB, opens with Pillow.

- [ ] T042 [P] Record provenance links for each figure and statistic **[IV‑Single Source of Truth]**  
  - **File**: `outputs/provenance.json` (maps each artifact to source row IDs and code module).  
  - **Verification**: JSON loads; contains entries for all figures and key statistics.

---

## Phase 7 – Runtime Enforcement

- [ ] T041 [P] Orchestrate full pipeline and enforce total runtime < 1 h **[SC‑005]**  
  - **File**: `code/main.py`.  
  - **Behavior**: Executes all phases, logs wall‑clock time to `outputs/runtime_log.txt`.  
  - **Verification**: CI step parses the log and fails if duration > 3600 seconds.

---

## Phase 8 – Tests (Concrete Test Tasks)

- [ ] T050 [P] Create/Update ingestion tests **[FR‑001]**  
  - **File**: `tests/test_ingestion.py` (checks checksum handling, schema validation, CRS reprojection, merge‑validation).  

- [ ] T051 [P] Create/Update EDA tests **[FR‑002]**  
  - **File**: `tests/test_eda.py` (symmetry, diagonal, VIF flagging, Moran's I detection).  

- [ ] T052 [P] Create/Update power analysis tests **[SC‑002]**  
  - **File**: `tests/test_power.py` (required vs actual sample size, underpowered flag).  

- [ ] T053 [P] Create/Update modeling tests **[FR‑003]**  
  - **File**: `tests/test_modeling.py` (model improvement, global FDR, sensitivity sweep, Jaccard).  

- [ ] T054 [P] Create/Update figure generation tests **[FR‑002]**  
  - **File**: `tests/test_figures.py` (file existence, size, openability).  

- [ ] T055 [P] Create/Update runtime test **[SC‑005]**  
  - **File**: `tests/test_runtime.py` (parses `runtime_log.txt` and asserts < 3600 s).  

All tests must pass in CI.

---

*All tasks must be executed in the order indicated by their dependencies. Tasks marked `[P]` may run in parallel provided their file targets do not overlap.*  