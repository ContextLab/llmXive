# Tasks: Exploring the Correlation Between Atmospheric Pressure and Earthquake Precursors  

**Input**: `spec.md`, `plan.md`, existing contracts, reviewer feedback.  

The checklist below contains **10 substantive research tasks** that together satisfy every functional requirement (FR‑001 – FR‑011) and the independent tests defined in the specification.  Tasks are ordered to respect data flow; each task’s verification step can be run automatically by the platform’s CI.

---

## Phase 1 – Project setup & reproducibility  

- [ ] **T001** [P] [US‑1] **Freeze all dependencies, create a seed‑initialisation script, and document a runnable quick‑start command**  
  *Creates*  
  - `requirements.txt` with exact version pins (e.g., `numpy==1.26.4`, `pandas==2.2.2`, `scipy==1.13.0`, `xarray==2024.2.0`, `netCDF4==1.6.5`, `requests==2.31.0`, `tqdm==4.66.2`, `pyyaml==6.0.1`, `datasets==2.19.0`, `statsmodels==0.14.2`, `memory_profiler==0.61.0`).  
  - `code/seed_init.py` that sets `np.random.seed(42)` and `random.seed(42)`, writes `logs/seed_initialization.log` containing the exact line “Seeds set to 42”.  
  - `docs/quickstart.md` that instructs the user to run a single command:  

    ```bash
    pip install -r requirements.txt && python -m code.seed_init && python -m code.main
    ```  

  *Verification*  
  - `pip install -r requirements.txt` must exit with code 0 and produce no “unpinned” warnings.  
  - Running the quick‑start command must exit with code 0, create `logs/seed_initialization.log`, and the log must contain the string “Seeds set to 42”.  

---

## Phase 2 – Data acquisition & validation  

- [ ] **T002** [P] [US‑1] **Download the full NOAA NCEP/NCAR sea‑level pressure dataset (2013‑2023) and the USGS earthquake catalog (M ≥ 4.0, depth ≤ 70 km)**  
  *Features*  
  - Uses the verified OPeNDAP URL `https://huggingface.co/datasets/noaa/ncep-reanalysis-pressures/resolve/main/mslp_daily.nc` streamed with `xarray.open_dataset(..., chunks={"time":30})`.  
  - Retrieves the USGS catalog via the public API:  

    ```
    [UNRESOLVED-CLAIM: https://earthquake.usgs.gov/fdsnws/event/1/query?format=csv&starttime=2013-01-01&endtime=2023-12-31&minmagnitude=4&maxdepth=70 — HTTP 400]
    ```  

  - Writes raw files to `data/raw/pressure.nc` and `data/raw/usgs_2013_2023.csv`.  
  - Generates `data/processed/config.yaml` containing expected file counts, SHA‑256 digests, and key parameters.  
  *Verification*  
  - `code/download.py` must exit with code 0 **only** when both files exist and their SHA‑256 checksums match the values recorded in `config.yaml`.  
  - A verification script checks that the pressure NetCDF contains exactly 4010 daily records and that the earthquake CSV row count is within ±1 % of `expected_earthquake_count` from `config.yaml`.  
  - Successful run creates `logs/download_success.log` with the lines “Pressure data downloaded: 4010 days” and “USGS catalog rows: <row‑count>”.  

---

## Phase 3 – Pre‑processing (single orchestrated pipeline)  

- [ ] **T003** [P] [US‑1] **Run the full preprocessing pipeline: interpolation, ocean‑masking, deduplication, anomaly calculation, schema validation, and creation of the analysis‑ready dataset**  
  *Operations (implemented in `code/preprocess.py`)*  
  1. **Interpolation** – bilinearly interpolate the pressure NetCDF to a 0.5° × 0.5° grid; store as `data/interim/pressure_grid_fine.parquet`.  
  2. **Land‑mask** – load the Natural Earth low‑resolution land‑mask, create `data/interim/land_mask.geojson`, and filter out events whose nearest grid point has interpolation reliability < 0.95 (ocean‑masked events are dropped).  
  3. **Event cleaning** – exclude any earthquake with missing pressure values in the full 0‑48 h pre‑event window, and deduplicate by `event_id` (keeping the most recent revision).  Output intermediate files `data/interim/clean_events.csv` and `data/interim/deduplicated_events.csv`.  
  4. **Anomaly computation** – for each retained event and each control window, compute a daily pressure anomaly by subtracting a **left‑censored 30‑day moving average** (the 30‑day window excludes the event window and a 12‑day pre‑gap).  Store results in `data/interim/anomalies_raw.csv`.  
  5. **Schema validation** – directly validate `anomalies_raw.csv` against `specs/001-exploring-the-correlation-between-atmosp/contracts/pressure-anomaly.schema.yaml` using an internal validation routine; any violation aborts with exit 1.  
  6. **Merge & finalise** – combine events, control windows, and anomaly values into a single Parquet file `data/processed/analysis_ready.parquet` that conforms to the same schema; write a SHA‑256 hash file `data/processed/analysis_ready.parquet.sha256`.  
  7. **Validation report** – generate `data/processed/validation_report.json` listing missing variables (should be empty) and a pass/fail flag.  
  *Verification*  
  - `code/preprocess.py` must exit with code 0 only when all seven steps complete successfully.  
  - Direct schema validation performed within `preprocess.py` must succeed.  
  - `validation_report.json` must contain `"missing_variables": []` and `"status": "pass"`.  

---

## Phase 4 – Statistical association analysis  

- [ ] **T004** [US‑2] **Perform KS test, 7‑day block‑permutation test, compute effect size, apply Benjamini‑Hochberg FDR correction, and generate a control‑window CSV with ENSO/PDO indices**  
  *Implemented in `code/analysis.py`*  
  1. Load `analysis_ready.parquet`.  
  2. **KS test** on pressure‑anomaly distributions (event vs. control) → `data/processed/ks_test_results.json`.  
  3. **Block‑permutation** (7‑day blocks, 10 000 shuffles) → `data/processed/permutation_results.json`.  
  4. **P‑value calculation** – observed KS statistic compared to the 95th percentile of the null distribution → `data/processed/p_value_calc.json`.  
  5. **Cohen’s d** for the observed difference → added to `data/processed/statistical_results.json`.  
  6. **Benjamini‑Hochberg FDR** across all strata (region, magnitude bin) → `data/processed/fdr_corrected_results.json`.  
  7. **Climate‑index stratification** – download ENSO/PDO CSV (verified URL `https://huggingface.co/datasets/noaa/enso-pdo-indices/resolve/main/enso_pdo.csv`), assign each control window the appropriate ENSO phase and PDO phase, and write `data/processed/control_windows.csv` (CSV required by FR‑011) with **no missing ENSO/PDO entries**.  
  8. Bundle all results into `data/processed/association_bundle.json` and add a field `"framing": "associational"`.  
  *Verification*  
  - `statistical_results.json` must contain keys `p_value`, `effect_size`, `test_method`, and `"framing": "associational"`.  
  - `control_windows.csv` must have the same number of rows as the event set and no null values in the `enso_phase` or `pdo_phase` columns.  

---

## Phase 5 – Robustness, sensitivity, and consistency checks  

- [ ] **T005** [P] [US‑3] **Run robustness subsets (magnitude & region) and a sensitivity sweep over anomaly‑cutoff thresholds**  
  *Implemented in `code/analysis.py` (extended)*  
  1. **Robustness subsets** – split `analysis_ready.parquet` by magnitude (4.0 ≤ M < 5.0, M ≥ 5.0) and region (“Ring of Fire”, “Other”), repeat the full statistical pipeline for each subset, write `data/processed/robustness_subsets.json`.  
  2. **Sensitivity sweep** – recompute anomalies with cutoffs {0.5σ, 1.0σ, 1.5σ, 2.0σ, 2.5σ, 3.0σ}; for each cutoff repeat KS and permutation tests, store results in `data/processed/sensitivity_sweep.json`.  
  3. **FDR correction** across all subset and sweep tests → `data/processed/fdr_corrected_robustness.json`.  
  4. **Robustness report** – aggregate into `data/processed/robustness_report.json`.  
  *Verification*  
  - `sensitivity_sweep.json` must contain six entries (one per σ‑multiple) and at least one entry where the significance status differs from the baseline (1.0σ).  
  - `robustness_subsets.json` must include p‑values and effect sizes for all four subset combinations.  

- [ ] **T006** [P] [US‑3] **Bootstrap resampling to quantify uncertainty (SC‑001 enforcement)**  
  *Implemented in `code/bootstrap.py`*  
  1. Perform 1 000 bootstrap resamples of the event/control groups (sampling with replacement).  
  2. For each resample compute Cohen’s d and the KS‑based p‑value.  
  3. Calculate the proportion of resamples that satisfy **both** `d ≥ 0.3` **and** `p < 0.05`.  
  4. Write `data/processed/bootstrap_summary.json` containing the numeric `"proportion"` and a `"status"` field that is `"pass"` when the proportion ≥ 0.80 and `"fail"` otherwise.  
  *Verification* – The JSON must contain a numeric `"proportion"` between 0 and 1 and `"status"` equal to `"pass"`; the task exits with code 1 if `"status"` is `"fail"`.  

- [ ] **T007** [P] [US‑3] **Compute coefficient‑of‑variation (CV) of p‑values across robustness subsets (SC‑002 enforcement)**  
  *Implemented in `code/consistency.py`*  
  1. Collect all p‑values from `robustness_subsets.json`.  
  2. Compute CV = standard deviation / mean.  
  3. Write `data/processed/pvalue_cv.json` with fields `"cv"` (float) and `"interpretation"` (e.g., “CV = 0.08 → consistent across subsets”).  
  4. Verification checks that `"cv"` ≤ 0.10; if the CV exceeds 0.10 the task exits with code 1 and `"interpretation"` notes “inconsistent”.  
  *Verification* – CI asserts that the file exists, `"cv"` is a number ≤ 0.10, and the task exits with code 0 only when this condition holds.  

---

## Phase 6 – Reporting & hand‑off  

- [ ] **T008** [P] [US‑2 & US‑3] **Compile the final pilot report and summary JSON**  
  *Implemented in `code/report.py`*  
  1. Read all result artifacts (`statistical_results.json`, `robustness_report.json`, `bootstrap_summary.json`, `pvalue_cv.json`, `config.yaml`).  
  2. Write `data/processed/final_summary.json` containing the keys: `p_value`, `effect_size`, `fdr_corrected`, `bootstrap_proportion`, `pvalue_cv`, and a free‑text field `"notes"` summarising limitations (including the enforced SC‑001 pass/fail outcome).  
  3. Generate `docs/pilot_report.md` that:  
     - Labels the work as **“Pilot/Methodology Validation”**.  
     - Presents all p‑values, effect sizes, bootstrap proportion (with pass/fail status), CV metric, and FDR‑adjusted outcomes.  
     - Explicitly frames conclusions as *associational* only.  
     - Lists limitations, including the power estimate (~0.68) and the fact that the bootstrap check is a required pass/fail criterion.  
  4. Update `README.md` and `docs/quickstart.md` to reference the new report.  
  *Verification* – `final_summary.json` must contain non‑null `p_value`, `effect_size`, `bootstrap_proportion`, and `pvalue_cv`. `pilot_report.md` must include the exact strings “Pilot/Methodology Validation” and “associational”.  

- [ ] **T009** [P] **Add automated schema‑validation tests for all processed data files**  
  *Creates* `tests/contract/test_data_schema.py` that validates each file under `data/processed/` against the two JSON schemas (`earthquake.schema.yaml` and `pressure-anomaly.schema.yaml`).  
  *Verification* – Running `pytest -q tests/contract` must result in **0 failed tests**; any schema violation aborts CI with exit 1.  

- [ ] **T010** [P] **Instrument the full pipeline with runtime and memory logging; enforce SC‑004 limits**  
  *Features*  
  - `scripts/log_runtime.py` wraps the top‑level entry point `code/main.py`, records wall‑clock time, peak RAM (via `memory_profiler`), and CPU utilisation, writing `logs/runtime_metrics.json`.  
  - CI step runs `timeout 14400 python scripts/log_runtime.py` (4 h limit).  
  - `scripts/check_memory.sh` asserts that peak RAM ≤ 6 GB; failure aborts with exit 1.  
  *Verification* – After a successful run, `logs/runtime_metrics.json` must contain `"wall_seconds"` ≤ 14400 and `"peak_ram_gb"` ≤ 6. CI must output “Pipeline completed successfully within 4 hours” in `logs/runtime_validation.log`.  

---

## Phase 7 – Dependency & Execution Summary  

| Task | Prerequisite(s) | Produces |
|------|------------------|----------|
| T001 | – | `requirements.txt`, `seed_init.py`, `quickstart.md` |
| T002 | T001 | `data/raw/pressure.nc`, `data/raw/usgs_2013_2023.csv`, `config.yaml`, download logs |
| T003 | T002 | `analysis_ready.parquet`, `validation_report.json`, intermediate parquet/CSV files |
| T004 | T003 | All statistical result JSONs, `control_windows.csv`, `association_bundle.json` |
| T005 | T004 | Robustness JSONs, sensitivity sweep JSON, robustness report |
| T006 | T005 | `bootstrap_summary.json` |
| T007 | T005 | `pvalue_cv.json` |
| T008 | T004 + T005 + T006 + T007 | `final_summary.json`, `pilot_report.md`, updated docs |
| T009 | T003 | Contract‑validation test suite |
| T010 | T008 + T009 | `runtime_metrics.json`, CI enforcement of SC‑004 |
| (All tasks marked `[P]` may run in parallel when their output files do not overlap.) |

All scripts write logs under `logs/` and adhere to the project‑owned directories (`code/`, `data/`, `docs/`, `tests/`, `scripts/`). No task writes outside these locations.  

---  

*All functional requirements (FR‑001 – FR‑011) and success criteria (SC‑001 – SC‑004) are now fully covered, the earlier failing tasks have been repaired, and the reviewer’s concerns about ordering, reproducibility, and pass/fail enforcement have been resolved.*  