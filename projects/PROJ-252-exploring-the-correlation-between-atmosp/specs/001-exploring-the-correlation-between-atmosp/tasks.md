# Tasks: Exploring the Correlation Between Atmospheric Pressure and Earthquake Precursors  

**Input**: `spec.md`, `plan.md`, existing code/data contracts, reviewer feedback.  

The list below groups related work into **10 substantive research tasks** that together satisfy every functional requirement (FR‑001 – FR‑011) and the independent tests defined in the specification.  Tasks are ordered to respect data flow; each task’s verification step can be run automatically by the platform’s CI.

---

## Phase 1 – Project setup & reproducibility  

- [X] **T001** [P] [US1] **Create reproducible project documentation, pin dependencies, and set random seeds**  
  *Creates* `docs/quickstart.md` (runnable command, required‑input provenance) and ensures `requirements.txt` is frozen.  
  *Adds* a `code/__init__.py` that sets `np.random.seed(42)` and `random.seed(42)`.  
  *Verification*:  
    • Run `python -m pip install -r requirements.txt` – must succeed without warnings.  
    • Execute the command shown in `quickstart.md`; it must exit with code 0, print “Pipeline completed successfully”, and produce `logs/seed_initialization.log` confirming the seeds were set.

---

## Phase 2 – Data acquisition & preprocessing  

- [ ] **T002** [P] [US1] **Download full global NOAA NCEP/NCAR pressure dataset and USGS earthquake catalog**   <!-- FAILED-IN-EXECUTION: code/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download.py exit=1; code/analysis.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download.py exit=1; code/preprocess.py exit=1 -->
  *Features*  
    • Fetch the **global** NOAA NCEP/NCAR daily sea‑level pressure files for 2013‑2023 from the verified URL listed in `plan.md`.  
    • Download the **USGS 2013‑2023** earthquake catalog (M ≥ 4.0, depth ≤ 70 km) via the official USGS API.  
    • Abort with exit code 1 if any download fails (no silent abort).  
    • Write raw files to `data/raw/` and generate `data/processed/config.yaml` containing at least:  

   ```yaml
   pilot_mode: false
   expected_global_pressure_files: 4010   # number of daily files 2013‑2023
   expected_earthquake_count: 1234      # placeholder, verified at runtime
   moving_average_days: 30
   min_permutation_iterations: 10000
   max_permutation_iterations: 100000
   convergence_variance_threshold: 1e-5
   ```  

  *Verification*:  
    • Run `code/download.py`; it must exit with code 0 only when both datasets are fully present.  
    • After download, a built‑in check script validates that the number of pressure files matches `expected_global_pressure_files` and that the earthquake CSV row count matches `expected_earthquake_count` ± 1 %.  
    • The script writes `logs/download_success.log` containing “Global NOAA pressure data downloaded: N files” and “USGS earthquake catalog rows: M”.

- [ ] **T003** [P] [US1] **Full preprocessing pipeline in `code/preprocess.py`**   <!-- FAILED-IN-EXECUTION: code/preprocess.py exit=1 -->
  *Sub‑steps (executed sequentially)*  
    1. `interpolate_pressure_grid()` → reads raw NOAA files, interpolates to a 0.5° grid, writes `data/interim/pressure_grid_fine.parquet`.  
    2. `generate_land_mask()` → `data/interim/land_mask.geojson` (Natural Earth low‑resolution).  
    3. `apply_ocean_mask()` → reads the land mask, computes interpolation reliability, excludes events with reliability < 95 %; writes `data/interim/masked_events.csv`.  
    4. `exclude_missing_pressure()` → drops any records lacking pressure values in the 0‑48 h pre‑event window; writes `data/interim/clean_events.csv`.  
    5. `calculate_left_censored_anomaly()` → left‑censored 30‑day moving‑average anomaly; writes `data/interim/anomalies_raw.csv`.  
    6. `deduplicate_events()` → retains the most recent revision per `event_id`; writes `data/interim/deduplicated_with_anomalies.csv`.  
    7. `create_master_dataset()` → merges all interim files into `data/processed/master_dataset.parquet`, validates against `contracts/earthquake.schema.yaml` and `contracts/pressure-anomaly.schema.yaml`, generates SHA‑256 checksum `master_dataset.parquet.sha256` and a JSON validation report `validation_report.json`.  

  *Verification*:  
    • After the pipeline runs, a verification script checks that `masked_events.csv` and `clean_events.csv` exist, contain only land events with reliability ≥ 95 %, and that `validation_report.json` lists **no missing required variables**.  
    • `tests/unit/schema_validation_check.py` (built‑in) must pass; any schema violation causes exit code 1.

---

## Phase 3 – Statistical association analysis  

- [ ] **T004** [P] [US2] **Statistical testing and climate‑index stratification in `code/analysis.py`**  
  *Operations*  
    1. `run_ks_test()` → two‑sample Kolmogorov–Smirnov on “event” vs. “control” windows; output `data/processed/ks_test_results.json`.  
    2. `run_permutation_test()` → 10 000 shuffles (or until convergence per `config.yaml`); output `data/processed/permutation_results.json`.  
    3. `calculate_p_value()` → compares observed KS statistic to the 95 th percentile of the permuted null; writes `data/processed/p_value_calc.json`.  
    4. `compute_effect_size()` → Cohen’s d for the observed difference; adds to `data/processed/statistical_results.json`.  
    5. `apply_fdr_correction()` → Benjamini‑Hochberg across all tests performed in this phase; writes `data/processed/fdr_corrected_results.json`.  
    6. `stratify_by_climate_indices()` → downloads ENSO and PDO indices from NOAA, matches control windows by month/day and climate phase, writes `data/interim/climate_stratified_controls.parquet`.  
    7. `finalize_association()` → bundles all results, ensures the `framing` field is set to “associational”.  

  *Verification*:  
    • A post‑run sanity script checks that `statistical_results.json` contains keys `p_value`, `effect_size`, `framing` = “associational”, and `test_method`.  
    • The script also confirms that the climate‑stratified control file exists and contains the same number of records as the event set.

---

## Phase 4 – Robustness and sensitivity checks  

- [ ] **T005** [P] [US3] **Robustness & sensitivity analyses in `code/analysis.py`**  
  *Steps*  
    1. `robustness_subsets()` → stratify master dataset by magnitude bins (4.0–5.0, > 5.0) and region (“Ring of Fire”, “Other”); produce `data/processed/robustness_subsets.json` with separate p‑values/effect sizes.  
    2. `sensitivity_sweep()` → vary anomaly cutoff over {0.5σ, 1.0σ, 1.5σ, 2.0σ, 2.5σ, 3.0σ}; record significance rates in `data/processed/sensitivity_sweep.json`.  
    3. `apply_fdr_to_robustness()` → Benjamini‑Hochberg across all subset and sweep tests; write `data/processed/fdr_corrected_robustness.json`.  
    4. `generate_robustness_report()` → consolidate results into `data/processed/robustness_report.json`.  

  *Verification*:  
    • A verification script asserts that `sensitivity_sweep.json` contains six entries and that at least one cutoff changes the significance status.  
    • Schema validation of `robustness_report.json` (keys: `subsets`, `sensitivity`, `fdr_corrected`) must pass.

---

## Phase 5 – Reporting & hand‑off  

- [ ] **T006** [P] [US2 & US3] **Aggregate results and produce the pilot report**  
  *Actions*  
    1. `code/report.py` reads `statistical_results.json`, `robustness_report.json`, and `config.yaml`; writes `data/processed/final_summary.json`.  
    2. Generate `docs/pilot_report.md` that (a) labels findings as **“Pilot/Methodology Validation”**, (b) presents p‑values, effect sizes, and FDR‑corrected outcomes, (c) explicitly frames conclusions as “associational”, (d) lists all limitations (global data blocked → T002, climate‑index proxy → T004).  
    3. Update `README.md` and `docs/quickstart.md` to point to the new report and to the deviation records in `docs/deviations.md`.  

  *Verification*:  
    • Post‑run script checks that `final_summary.json` contains non‑null `p_value` and `effect_size` fields and that `pilot_report.md` includes the strings “Pilot/Methodology Validation” and “associational”.

- [ ] **T007** [P] [US1] **Add contract schema tests**  
  *Creates* `tests/contract/test_data_schema.py` that validates every file in `data/processed/` against the two YAML schemas in `contracts/`.  
  *Verification*: All contract tests must pass; any schema violation aborts the CI run.

- [ ] **T008** [P] **Enforce runtime constraints and generate logs**  
  *Scripts* `scripts/check_memory.sh` (uses `memory_profiler` to assert peak RAM < 6 GB) and a timeout wrapper `timeout 21600 python code/main.py`.  
  *Adds* `scripts/log_runtime.py` that records wall‑clock time and peak memory, writing `logs/runtime_metrics.json`.  
  *Verification*: CI log `logs/quickstart_validation.log` must contain the line “Pipeline completed successfully within 6 hours” and `logs/runtime_metrics.json` must report “peak_ram_gb” ≤ 6.

- [ ] **T009** [P] **Global NOAA pressure dataset download (full coverage of FR‑001)**  
  *Features*  
    • Mirrors the download logic of T002 but is dedicated to the **full global** dataset.  
    • Validates checksum of each daily file against published NOAA hashes.  
    • Writes a manifest `data/raw/noaa_global_manifest.yaml` summarizing file counts and total size.  
  *Verification*: The manifest must report the expected number of files (4010) and the script must exit with code 0 only when all files are present and checksums match.

- [ ] **T010** [P] **Record runtime and memory metrics for SC‑004**  
  *Features*  
    • Wraps the entire pipeline (`code/main.py`) with `scripts/log_runtime.py`.  
    • Generates `logs/runtime_metrics.json` containing `wall_seconds`, `peak_ram_gb`, and `cpu_utilization_percent`.  
  *Verification*: A CI step asserts that `runtime_metrics.json` exists and that `wall_seconds` ≤ 21600 (6 h) and `peak_ram_gb` ≤ 6.

---

## Dependencies & Execution Order (summary)

| Task | Prerequisites | Produces |
|------|----------------|----------|
| T001 | – | Documentation, pinned environment, random‑seed log |
| T002 | T001 | `data/raw/` (global NOAA & USGS), `data/processed/config.yaml`, download logs |
| T003 | T002 | Interpolated grid, land mask, masked & cleaned event files, master dataset, validation report |
| T004 | T003 | Statistical result files, climate‑stratified control set |
| T005 | T004 | Robustness/subset files, sensitivity sweep, robustness report |
| T006 | T004 + T005 | Final summary and pilot report |
| T007 | T003 | Contract‑validation test suite |
| T008 | T006 + T007 | CI runtime‑constraint verification and runtime log |
| T009 | T001 | Full global NOAA pressure files and manifest (fulfills FR‑001) |
| T010 | T008 | Runtime metrics JSON (fulfills SC‑004) |

*Tasks marked `[P]` may run in parallel when their output files do not overlap.*  