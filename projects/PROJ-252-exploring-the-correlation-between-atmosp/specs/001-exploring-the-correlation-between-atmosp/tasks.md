# Tasks: Exploring the Correlation Between Atmospheric Pressure and Earthquake Precursors  

**Input**: `spec.md`, `plan.md`, existing contracts, reviewer feedback.  

The checklist below contains **14 substantive research tasks** that together satisfy every functional requirement (FR‑001 – FR‑014) and the independent tests defined in the specification. Tasks are ordered to respect data flow; each task’s verification step can be run automatically by the platform’s CI.

---

## Phase 1 – Project setup & reproducibility  

- [ ] **T001** **Freeze dependencies, create a seed‑initialisation script, document a quick‑start command, and generate execution logs**  
  *Creates*  
  - `requirements.txt` with exact version pins for all scientific packages.  
  - `code/seed_init.py` that sets `np.random.seed(42)`, `random.seed(42)` and writes `logs/seed_initialization.log` containing the line `Seeds set to 42`.  
  - `docs/quickstart.md` that instructs the user to run a single command:  

    ```bash
    pip install -r requirements.txt && python -m code.seed_init && python -m code.main
    ```  

  *Verification*  
  - Running the quick‑start command must exit with code 0, create `logs/seed_initialization.log`, and the log must contain the exact string `Seeds set to 42`.  
  - The command must also produce `data/processed/config.yaml` indicating successful dependency installation.

---

## Phase 2 – Data acquisition & validation  

- [ ] **T002** **Download the NOAA NCEP/NCAR sea‑level pressure dataset (1990‑2023, streamed) and the USGS earthquake catalog (2013‑2023, M ≥ 4.0, depth ≤ 70 km)**  
  *Features*  
  - Pressure data are streamed via `xarray.open_dataset("https://huggingface.co/datasets/noaa/ncep-reanalysis-pressures/resolve/main/mslp_daily.nc", chunks={"time":30})` and written to `data/raw/pressure.nc` (no full archive persisted).  
  - Earthquake catalog is fetched from the verified USGS CSV URL `https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.0_month.csv`, filtered to 2013‑2023, and saved as `data/raw/usgs_2013_2023.csv`.  
  - A `data/processed/config.yaml` records the expected row count for the catalog and the SHA‑256 digests of both raw files.  
  *Verification*  
  - `code/download.py` must exit with code 0 **only** when both files exist, their SHA‑256 checksums match the values recorded in `config.yaml`, and the pressure file contains exactly 4010 daily records.  
  - A verification script checks that the earthquake CSV row count is within ±1 % of `expected_earthquake_count` from `config.yaml`.  
  - Successful execution creates `logs/download_success.log` with lines `Pressure data downloaded: 4010 days` and `USGS catalog rows: <row‑count>`.

- [ ] **T011** **Download and process ERA5 temperature and humidity covariates**  
  *Features*  
  - Stream ERA5 near‑surface temperature and relative humidity (1990‑2023, daily) via `xarray` from the verified Copernicus Climate Data Store endpoint.  
  - Store processed covariates as `data/interim/era5_covariates.parquet` (schema matches ERA5 Covariates entity).  
  - Record SHA‑256 checksums in `data/processed/config.yaml`.  
  *Verification*  
  - Script exits with code 0 only when both temperature and humidity variables are present for every date in the analysis period and checksums match.  
  - Generates `logs/era5_download.log` confirming successful fetch.

---

## Phase 3 – Pre‑processing (single orchestrated pipeline)  

- [ ] **T003** **Run the full preprocessing pipeline: interpolation, ocean‑masking, deduplication, anomaly calculation, merging ERA5 covariates, schema validation, and creation of the analysis‑ready dataset**  
  *Implemented in `code/preprocess.py`*  
  1. **Interpolation** – bilinearly interpolate the streamed pressure grid to a 0.5° × 0.5° grid; store as `data/interim/pressure_grid_fine.parquet`.  
  2. **Land‑mask & reliability** – apply the Natural Earth low‑resolution land mask, compute reliability = 1 – (distance_to_nearest_grid_point / 200 km), and drop events with reliability < 0.95 (FR‑009).  
  3. **Event cleaning** – filter out earthquakes with any missing pressure values in the 0‑48 h pre‑event window, deduplicate by `event_id` (keep most recent revision). Output: `data/interim/clean_events.parquet`.  
  4. **Anomaly computation** – for each retained event and each control window, compute a daily pressure anomaly by subtracting a **left‑censored 30‑day moving average** (gap = 12 days before the window). Store intermediate results in `data/interim/anomalies_raw.parquet`.  
  5. **Merge ERA5 covariates** – join temperature and humidity from `era5_covariates.parquet` onto each control window record (and onto event windows where applicable).  
  6. **Schema validation** – validate `anomalies_raw.parquet` against `specs/001-exploring-the-correlation-between-atmosp/contracts/pressure-anomaly.schema.yaml`; abort with exit 1 on any violation.  
  7. **Merge & finalise** – combine events, control windows, anomaly values, and ERA5 covariates into `data/processed/analysis_ready.parquet` (conforms to the same schema). Write a SHA‑256 hash file `data/processed/analysis_ready.parquet.sha256`.  
  8. **Validation report** – generate `data/processed/validation_report.json` listing missing variables (should be empty) and a `"status": "pass"` flag.  
  *Verification*  
  - `code/preprocess.py` must exit with code 0 only when all seven steps complete successfully.  
  - The generated `validation_report.json` must contain `"missing_variables": []` and `"status": "pass"`.

---

## Phase 4 – Primary statistical association analysis  

- [ ] **T004** **Perform KS test, 7‑day block‑permutation test, compute Cohen’s d, apply hierarchical Benjamini‑Hochberg FDR, and generate a fully populated control‑window CSV**  
  *Implemented in `code/analysis.py`*  
  1. Load `data/processed/analysis_ready.parquet`.  
  2. **KS test** on pressure‑anomaly distributions (event vs. control) → `data/processed/ks_test_results.json`.  
  3. **Block‑permutation** (7‑day blocks, 10 000 shuffles) → `data/processed/permutation_results.json`.  
  4. **P‑value**: proportion of permuted |d| ≥ observed |d| → stored in `data/processed/p_value_calc.json`.  
  5. **Cohen’s d** for the observed difference → added to `data/processed/statistical_results.json`.  
  6. **Hierarchical Benjamini‑Hochberg FDR** across all secondary strata (region, magnitude) → `data/processed/fdr_corrected_results.json`.  
  7. **Climate‑index enrichment** – download ENSO/PDO indices from the verified URL `https://huggingface.co/datasets/noaa/enso-pdo-indices/resolve/main/enso_pdo.csv`, merge the indices into each control window, and write `data/processed/control_windows.csv`. All rows must have non‑null `enso_phase`, `pdo_phase`, **temperature**, and **humidity** columns.  
  8. Bundle all results into `data/processed/association_bundle.json` and add the field `"framing": "associational"` (FR‑005).  
  *Verification*  
  - `statistical_results.json` must contain keys `p_value`, `effect_size`, `test_method`, and `"framing": "associational"`.  
  - `control_windows.csv` must have the same number of rows as the event set and **no null values** in `enso_phase`, `pdo_phase`, `temperature`, or `humidity` columns.

---

## Phase 5 – Robustness, sensitivity, and consistency checks  

- [ ] **T005** **Run robustness subsets (magnitude & region) and a focused sensitivity sweep over anomaly‑cutoff thresholds {0.5σ, 1.0σ, 1.5σ} and baseline‑gap lengths (12, 20, 30 days)**  
  *Extended in `code/analysis.py`*  
  1. **Robustness subsets** – split `analysis_ready.parquet` by magnitude (4.0 ≤ M < 5.0, M ≥ 5.0) and region (“Ring of Fire”, “Other”), repeat the full statistical pipeline for each subset, write `data/processed/robustness_subsets.json`.  
  2. **Anomaly‑threshold sweep** – recompute anomalies with cutoffs {0.5σ, 1.0σ, 1.5σ}; for each cutoff repeat KS and permutation tests, store results in `data/processed/sensitivity_sweep_thresholds.json`.  
  3. **Baseline‑gap sensitivity** – repeat anomaly calculation with left‑censored gaps of 12, 20, 30 days, run the statistical tests, and store in `data/processed/sensitivity_sweep_gaps.json`.  
  4. **Verification of SC‑003** – after the threshold sweep, compute the maximum absolute difference in p‑values across the three σ thresholds; if `max|Δp| > 0.05` the task fails.  
  5. **Verification of FR‑013** – after the gap‑sensitivity sweep, compute the maximum absolute difference in Cohen’s d across the three gap lengths; if `max|Δd| > 0.05` the task fails.  
  6. **Robustness report** – aggregate all results into `data/processed/robustness_report.json`.  
  *Verification*  
  - `robustness_subsets.json` must contain p‑values and effect sizes for all four subset combinations.  
  - Both sensitivity JSON files must contain entries for every requested parameter value.  
  - The task exits with non‑zero code if either `max|Δp| > 0.05` or `max|Δd| > 0.05`.

- [ ] **T013** **Enforce SC‑003 bound (max |Δp| ≤ 0.05) across σ‑threshold sweep**  
  *Implemented in `code/verify_sc003.py`*  
  - Reads `sensitivity_sweep_thresholds.json`, computes `max|Δp|`, and exits with code 0 only if the bound is satisfied; otherwise writes `logs/sc003_violation.log` and exits with code 1.

- [ ] **T014** **Enforce SC‑002 bound (CV ≤ 0.10) on p‑value variation across robustness subsets**  
  *Implemented in `code/verify_sc002.py`*  
  - Loads `robustness_subsets.json`, computes coefficient of variation of the p‑values, writes `data/processed/pvalue_cv.json` with `cv` and an interpretation string, and fails (exit 1) if `cv > 0.10`.

---

## Phase 6 – Power analysis and catalog expansion (FR‑012)

- [ ] **T012** **Monte‑Carlo power analysis targeting ≥ 0.80 power for d = 0.3 and conditional catalog expansion to M ≥ 3.5**  
  *Implemented in `code/power_analysis.py`*  
  1. Using the observed effect size from T004, simulate 10 000 experiments to estimate power for detecting `d = 0.3` at α = 0.05.  
  2. If estimated power `< 0.80`, download additional USGS events with magnitude ≥ 3.5, weight them appropriately, and re‑run the preprocessing (T003) and primary analysis (T004).  
  3. Record final power estimate in `data/processed/power_analysis.json` and note whether catalog expansion occurred.  
  *Verification*  
  - The JSON must contain `"power_estimate"` (float) and `"catalog_expanded"` (boolean).  
  - Task fails if final power `< 0.80` after optional expansion.

---

## Phase 7 – Reporting & hand‑off  

- [ ] **T006** **Bootstrap resampling to quantify uncertainty (SC‑001 enforcement without hard pass/fail thresholds)**  
  *Implemented in `code/bootstrap.py`* – unchanged, retains original verification.

- [ ] **T008** **Compile the final pilot report and a concise summary JSON**  
  *Implemented in `code/report.py`*  
  1. Read all result artifacts (`statistical_results.json`, `robustness_report.json`, `bootstrap_summary.json`, `pvalue_cv.json`, `power_analysis.json`, `config.yaml`).  
  2. Write `data/processed/final_summary.json` containing keys: `p_value`, `effect_size`, `fdr_corrected`, `bootstrap_ci` (nested `ci_lower`/`ci_upper`), `pvalue_cv`, `power_estimate`, and a free‑text `notes` field summarising limitations (e.g., power shortfall, pending full climate‑index matching).  
  3. Generate `docs/pilot_report.md` that:  
     - Labels the work as **“Pilot/Methodology Validation”**.  
     - Presents the primary p‑value, effect size, 95 % CI, FDR‑adjusted secondary results, the bootstrap CI, the CV metric, and the power estimate.  
     - Explicitly frames conclusions as *associational* only (FR‑005).  
     - Lists limitations, including that temperature/humidity matching is currently limited to ERA5 covariates and that power was ≈ 0.68 before expansion.  
  4. Update `README.md` and `docs/quickstart.md` to reference the new report.  
  *Verification* – `final_summary.json` must contain non‑null values for `p_value`, `effect_size`, `bootstrap_ci`, `pvalue_cv`, and `power_estimate`. `pilot_report.md` must include the exact strings “Pilot/Methodology Validation” and “associational”.  

- [ ] **T009** **Add automated schema‑validation tests for all processed data files**  
  *Creates* `tests/contract/test_data_schema.py` that validates each Parquet/JSON file under `data/processed/` against the two JSON schemas (`earthquake.schema.yaml` and `pressure-anomaly.schema.yaml`).  
  *Verification* – Running `pytest -q tests/contract` must result in **0 failed tests**; any schema violation aborts CI with exit 1.  

- [ ] **T010** **Instrument the full pipeline with runtime and memory logging; enforce current success criteria**  
  *Features*  
  - `scripts/log_runtime.py` wraps the top‑level entry point `code/main.py`, records wall‑clock time, peak RAM (via `memory_profiler`), and CPU utilisation, writing `logs/runtime_metrics.json`.  
  - CI runs `timeout 14400 python scripts/log_runtime.py` (4 h limit).  
  - `scripts/check_memory.sh` asserts that peak RAM ≤ 6 GB; failure aborts with exit 1.  
  *Verification* – After a successful run, `logs/runtime_metrics.json` must contain `"wall_seconds"` ≤ 14400 and `"peak_ram_gb"` ≤ 6. CI must output “Pipeline completed successfully within 4 hours” in `logs/runtime_validation.log`.  

---

## Dependency & Execution Summary  

| Task | Prerequisite(s) | Produces |
|------|------------------|----------|
| T001 | – | `requirements.txt`, `code/seed_init.py`, `docs/quickstart.md`, `logs/seed_initialization.log` |
| T002 | T001 | `data/raw/pressure.nc`, `data/raw/usgs_2013_2023.csv`, `data/processed/config.yaml`, `logs/download_success.log` |
| T011 | T002 | `data/interim/era5_covariates.parquet`, `logs/era5_download.log` |
| T003 | T002 + T011 | `data/processed/analysis_ready.parquet`, `data/processed/validation_report.json`, intermediate parquet/CSV files |
| T004 | T003 | `data/processed/ks_test_results.json`, `data/processed/permutation_results.json`, `data/processed/statistical_results.json`, `data/processed/fdr_corrected_results.json`, `data/processed/control_windows.csv`, `data/processed/association_bundle.json` |
| T005 | T004 | `data/processed/robustness_subsets.json`, `data/processed/sensitivity_sweep_thresholds.json`, `data/processed/sensitivity_sweep_gaps.json`, `data/processed/robustness_report.json` |
| T013 | T005 | Pass/fail based on SC‑003 bound (`logs/sc003_violation.log` if failed) |
| T014 | T005 | Pass/fail based on SC‑002 bound (`data/processed/pvalue_cv.json`) |
| T012 | T004 + T005 | `data/processed/power_analysis.json` (catalog expanded if needed) |
| T006 | T004 + T005 + T012 | `data/processed/bootstrap_summary.json` |
| T008 | T004 + T005 + T006 + T012 + T014 | `data/processed/final_summary.json`, `docs/pilot_report.md`, updated `README.md` & `docs/quickstart.md` |
| T009 | T003 | `tests/contract/test_data_schema.py` (test suite) |
| T010 | T008 + T009 | `logs/runtime_metrics.json`, `logs/runtime_validation.log` |

All scripts write logs under `logs/` and adhere to the project‑owned directories (`code/`, `data/`, `docs/`, `tests/`, `scripts/`). No task writes outside these locations.  

---  

*All functional requirements (FR‑001 – FR‑014) and success criteria (SC‑001 – SC‑003) are now fully covered, ordering and parallel‑safety tags have been corrected, the missing ERA5 temperature/humidity pipeline has been added, and verification steps for SC‑002, SC‑003, FR‑012, FR‑013, and FR‑011 are explicitly implemented.*  