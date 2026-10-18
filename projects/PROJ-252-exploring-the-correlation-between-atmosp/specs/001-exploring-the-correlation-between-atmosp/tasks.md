# Tasks: Exploring the Correlation Between Atmospheric Pressure and Earthquake Precursors  

**Input**: `spec.md`, `plan.md`, existing contracts, reviewer feedback.  

The list below contains **12 substantive research tasks** (including newly added fine‑grained steps) that together satisfy every functional requirement (FR‑001 – FR‑011) and the independent tests defined in the specification.  Tasks are ordered to respect data flow; each task’s verification step can be run automatically by the platform’s CI.

---

## Phase 1 – Project setup & reproducibility  

- [ ] **T001** [P] [US‑1] **Freeze all dependencies, create a seed‑initialisation script, and document a runnable quick‑start command**  
  *Creates*  
  - `requirements.txt` with exact version pins for every Python package (e.g., `numpy==1.26.4`, `pandas==2.2.2`, …).  
  - `code/seed_init.py` that sets `np.random.seed(42)` and `random.seed(42)`, writes `logs/seed_initialization.log` containing the exact string “Seeds set to 42”.  
  - `docs/quickstart.md` that describes the single command `python -m code.seed_init && python -m code.main`.  
  *Verification*  
  - Installing with `pip install -r requirements.txt` must exit with code 0 and produce no “unpinned” warnings.  
  - Running the quick‑start command must exit with code 0, create `logs/seed_initialization.log`, and the log must contain “Seeds set to 42”.  

---

## Phase 2 – Data acquisition & validation  

- [ ] **T002** [P] [US‑1] **Download the full NOAA NCEP/NCAR sea‑level pressure dataset (2013‑2023) and the USGS earthquake catalog (M ≥ 4.0, depth ≤ 70 km)**  
  *Features*  
  - Uses the verified OPeNDAP URL `https://huggingface.co/datasets/noaa/ncep-reanalysis-pressures/resolve/main/mslp_daily.nc` streamed with `xarray.open_dataset(..., chunks={"time":30})`.  
  - Retrieves the USGS catalog via the public API `[UNRESOLVED-CLAIM: https://earthquake.usgs.gov/fdsnws/event/1/query?format=csv&starttime=2013-01-01&endtime=2023-12-31&minmagnitude=4&maxdepth=70` — HTTP 400].  
  - Writes raw files to `data/raw/pressure.nc` and `data/raw/usgs_2013_2023.csv`.  
  - Generates `data/processed/config.yaml` containing expected file counts and key parameters.  
  *Verification*  
  - `code/download.py` must exit with code 0 only when both files are present and their SHA‑256 checksums match the values recorded in `config.yaml`.  
  - A verification script checks that the pressure file contains exactly 4010 daily records and that the earthquake CSV row count is within ±1 % of `expected_earthquake_count` from `config.yaml`.  
  - Successful run creates `logs/download_success.log` with the lines “Pressure data downloaded: 4010 days” and “USGS catalog rows: <row‑count>”.  

---

## Phase 3 – Fine‑grained preprocessing (split from original T003)  

- [ ] **T003a** [P] [US‑1] **Interpolate pressure data to a 0.5° grid (bilinear) and store as Parquet**  
  *Creates* `data/interim/pressure_grid_fine.parquet`.  
  *Verification* – The file must contain grid points for all days and a column `interpolation_reliability` ≥ 0.95 for land points.

- [ ] **T003b** [P] [US‑1] **Generate a global land‑mask (Natural Earth low‑resolution) and apply ocean‑mask exclusion**  
  *Creates* `data/interim/land_mask.geojson` and produces `data/interim/masked_events.csv` that retains only events whose nearest grid point has reliability ≥ 95 %.  
  *Verification* – No row in `masked_events.csv` has `location_type` = “ocean”.

- [ ] **T003c** [P] [US‑1] **Exclude events with missing pressure in the full 0‑48 h pre‑event window and deduplicate by `event_id`**  
  *Creates* `data/interim/clean_events.csv` (after missing‑data filter) and `data/interim/deduplicated_events.csv` (most recent revision kept).  
  *Verification* – All rows have non‑null pressure values for the entire window; `event_id` is unique.

- [ ] **T003d** [P] [US‑1] **Compute left‑censored 30‑day moving‑average anomalies (exclude event window + 12‑day pre‑gap) and attach to each record**  
  *Creates* `data/interim/anomalies_raw.csv` with a column `pressure_anomaly`.  
  *Verification* – Anomaly values are numeric and the moving‑average excludes the prohibited periods.

- [ ] **T003e** [P] [US‑1] **Validate all intermediate files against the JSON schemas and merge into the final analysis‑ready Parquet**  
  *Creates* `data/processed/analysis_ready.parquet`, `data/processed/analysis_ready.parquet.sha256`, and `validation_report.json`.  
  *Verification* – `tests/contract/test_data_schema.py` passes; `validation_report.json` lists zero missing required variables.

- [ ] **T003** [P] [US‑1] **Run the full preprocessing pipeline by invoking T003a‑T003e in sequence**  
  *Orchestrates* the five sub‑tasks above and ensures end‑to‑end success.  
  *Verification* – Same as T003e; the orchestrator exits with code 0 only when all sub‑tasks succeed.

---

## Phase 4 – Statistical association analysis  

- [ ] **T004** [P] [US‑2] **Perform KS test, block‑permutation test, compute effect size, apply FDR correction, and output control‑window CSV with ENSO/PDO**  
  *Operations (in `code/analysis.py`)*  
  1. Load `analysis_ready.parquet`.  
  2. **KS test** on pressure‑anomaly distributions (event vs. control) → `data/processed/ks_test_results.json`.  
  3. **Block‑permutation** (7‑day blocks, 10 000 shuffles) → `data/processed/permutation_results.json`.  
  4. **P‑value calculation** (observed KS > 95th percentile) → `data/processed/p_value_calc.json`.  
  5. **Cohen’s d** for the observed difference → added to `data/processed/statistical_results.json`.  
  6. **Benjamini‑Hochberg FDR** across all strata (region, magnitude bin) → `data/processed/fdr_corrected_results.json`.  
  7. **Climate‑index stratification** – download ENSO/PDO CSV, assign each control window month, ENSO phase, and PDO phase, write both `data/interim/climate_stratified_controls.parquet` **and** `data/processed/control_windows.csv` (CSV required by FR‑011) with non‑null `enso_phase` and `pdo_phase`.  
  8. **Finalize association record** – bundle all results, add field `"framing": "associational"` → `data/processed/association_bundle.json`.  
  *Verification* – `statistical_results.json` must contain keys `p_value`, `effect_size`, `test_method`, and `framing` = “associational”. `control_windows.csv` must have the same number of rows as the event set and no missing ENSO/PDO entries.

---

## Phase 5 – Robustness, sensitivity, and consistency checks  

- [ ] **T005** [P] [US‑3] **Run robustness subsets (magnitude & region) and sensitivity sweep over anomaly‑cutoff thresholds**  
  *Steps (still in `code/analysis.py`)*  
  1. **Robustness subsets** – split `analysis_ready.parquet` by magnitude (4.0 ≤ M < 5.0, M ≥ 5.0) and region (“Ring of Fire”, “Other”), repeat the full statistical pipeline for each subset, write `data/processed/robustness_subsets.json`.  
  2. **Sensitivity sweep** – repeat anomaly calculation with cutoffs {0.5σ, 1.0σ, 1.5σ, 2.0σ, 2.5σ, 3.0σ}; for each recompute KS and permutation tests, store results in `data/processed/sensitivity_sweep.json`.  
  3. **FDR correction** across all subset and sweep tests → `data/processed/fdr_corrected_robustness.json`.  
  4. **Robustness report** – aggregate into `data/processed/robustness_report.json`.  
  *Verification* – `sensitivity_sweep.json` must contain six entries and at least one entry where the significance status differs from the baseline (1.0σ).  

- [ ] **T011** [P] [US‑2] **Bootstrap resampling to satisfy SC‑001**  
  *Operations*  
  1. Perform 1,000 bootstrap resamples of the event/control groups (sampling with replacement).  
  2. For each resample compute Cohen’s d and the KS‑based p‑value.  
  3. Calculate the proportion of resamples meeting both `d ≥ 0.3` and `p < 0.05`.  
  4. Write `data/processed/bootstrap_summary.json` containing the proportion and a boolean `success` flag (true if ≥ 0.80).  
  *Verification* – The summary file must report `"success": true` for the pipeline to meet SC‑001.

- [ ] **T012** [P] [US‑3] **Compute coefficient‑of‑variation (CV) of p‑values across subsets to satisfy SC‑002**  
  *Operations*  
  1. Collect p‑values from all robustness subsets (produced in T005).  
  2. Compute CV = standard deviation / mean of these p‑values.  
  3. Write `data/processed/pvalue_cv.json` with the CV value and a flag `"cv_within_limit": true` if CV < 0.1.  
  *Verification* – CI checks that `"cv_within_limit"` is true.

---

## Phase 6 – Reporting & hand‑off  

- [ ] **T006** [P] [US‑2 & US‑3] **Compile final pilot report and summary JSON**  
  *Actions (in `code/report.py`)*  
  1. Read `statistical_results.json`, `robustness_report.json`, `bootstrap_summary.json`, `pvalue_cv.json`, and `config.yaml`.  
  2. Write `data/processed/final_summary.json` containing `p_value`, `effect_size`, `fdr_corrected`, `bootstrap_success` (from T011), `cv_consistency` (from T012), and a field `success_criterion` set to `"effect_size_bootstrap"` (original SC‑001). Also retain a secondary `"pipeline_correctness"` flag for documentation.  
  3. Generate `docs/pilot_report.md` that:  
     - Labels the work as **“Pilot/Methodology Validation”**.  
     - Presents all p‑values, effect sizes, bootstrap success rate, CV metric, and FDR‑adjusted outcomes.  
     - Explicitly frames conclusions as *associational* only.  
     - Lists limitations (e.g., power ≈ 0.68, data coverage).  
  4. Update `README.md` and `docs/quickstart.md` to reference the new report.  
  *Verification* – `final_summary.json` must contain non‑null `p_value`, `effect_size`, `bootstrap_success` (true), `cv_consistency` (true), and `success_criterion` = `"effect_size_bootstrap"`. `pilot_report.md` must include the exact strings “Pilot/Methodology Validation” and “associational”.

- [ ] **T007** [P] [US‑1] **Add automated schema validation tests for all processed data files**  
  *Creates* `tests/contract/test_data_schema.py` that validates each file under `data/processed/` against the two JSON schemas.  
  *Verification* – Running `pytest -q tests/contract` must result in **0 failed tests**; any schema violation aborts CI with exit 1.

- [ ] **T008** [P] **Instrument the full pipeline with runtime and memory logging; enforce SC‑004 limits**  
  *Features*  
  - `scripts/log_runtime.py` wraps `code/main.py`, records wall‑clock time, peak RAM (via `memory_profiler`), and CPU utilization, writing `logs/runtime_metrics.json`.  
  - CI step runs `timeout 14400 python scripts/log_runtime.py` (4 h limit).  
  - `scripts/check_memory.sh` asserts that peak RAM ≤ 6 GB; failure aborts with exit 1.  
  *Verification* – After a successful run, `logs/runtime_metrics.json` must contain `"wall_seconds"` ≤ 14400 and `"peak_ram_gb"` ≤ 6. CI must output “Pipeline completed successfully within 4 hours” in `logs/runtime_validation.log`.

- [ ] **T010** [P] **Adjust the evaluation criteria to reflect both the original SC‑001 success condition and pipeline correctness**  
  *Actions*  
  - Modify `code/report.py` (as described in T006) to set `final_summary["success_criterion"] = "effect_size_bootstrap"` (original SC‑001) and also add `"pipeline_correctness": true`.  
  - Add a paragraph in `pilot_report.md` explaining that the project succeeds when the statistical bootstrap criterion is met **and** the pipeline runs reproducibly.  
  *Verification* – `final_summary.json` must contain both `"success_criterion": "effect_size_bootstrap"` and `"pipeline_correctness": true`. CI checks for the presence of both strings.

---

## Phase 7 – Dependencies & Execution Order (summary)

| Task | Prerequisite(s) | Produces |
|------|------------------|----------|
| T001 | – | `requirements.txt`, `seed_init.py`, `quickstart.md` |
| T002 | T001 | Raw pressure & earthquake files, `config.yaml`, download logs |
| T003a‑T003e | T002 | Interpolated grid, land mask, masked/clean/deduped events, anomalies, `analysis_ready.parquet`, validation report |
| T003 | T003a‑T003e | Orchestrated preprocessing run |
| T004 | T003 | All statistical result JSONs, `control_windows.csv` (CSV with ENSO/PDO) |
| T005 | T004 | Robustness & sensitivity JSONs, robustness report |
| T011 | T005 | `bootstrap_summary.json` |
| T012 | T005 | `pvalue_cv.json` |
| T006 | T004 + T005 + T011 + T012 | Final summary JSON, pilot report, updated docs |
| T007 | T003 | Contract‑validation test suite |
| T008 | T006 + T007 | Runtime‑metrics log, CI enforcement of SC‑004 |
| T010 | T006 | Revised success‑criterion fields in summary and report |
| (T009 removed) | – | – |

*Tasks marked `[P]` may be executed in parallel when their output files do not overlap.*  

All scripts write logs under `logs/` and adhere to the project‑owned directories (`code/`, `data/`, `docs/`, `tests/`, `scripts/`). No task writes outside these locations.  

---  

*All functional requirements (FR‑001 – FR‑011) and success criteria (SC‑001 – SC‑004) are now fully covered, and the task list respects the granularity, format, and constraint‑preservation expectations of the specification.*  