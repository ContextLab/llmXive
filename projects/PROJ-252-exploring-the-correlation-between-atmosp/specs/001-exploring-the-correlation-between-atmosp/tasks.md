# Tasks: Exploring the Correlation Between Atmospheric Pressure and Earthquake Precursors

**Input**: Design documents from `/specs/001-exploring-the-correlation-between-atmosp/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`

**Tests**: The examples below include test tasks. Tests are **MANDATORY** to ensure reproducibility and validation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

---

## Phase 1 – Setup and First End‑to‑End Analysis

- [ ] T001 Establish the existing code layout and dependencies, document a runnable command in `docs/quickstart.md`, and validate input provenance.  
  *Path*: `docs/quickstart.md`, `code/requirements.txt`

- [ ] T002 Implement the primary computation entry point and focused correctness tests in the source/test files named by the plan. Include invalid‑input handling required by the specification.  
  *Path*: `code/main.py`, `tests/unit/test_entrypoint.py`

- [ ] T003 Connect the entry point to the computation and run a small valid case, producing real result rows under `data/results/` with required fields and units.  
  *Path*: `data/results/sample_output.csv`

- [ ] T004 Create `docs/deviations.md` with a header, table of contents, and a formal record of scope reductions (e.g., FR‑001 global‑data block, FR‑011 climate‑index deferment).  
  *Path*: `docs/deviations.md`

- [ ] T005 Create `docs/quickstart.md` describing how to invoke the full pipeline on the pilot test data.  
  *Path*: `docs/quickstart.md`

---

## Phase 2 – Foundational (Blocking Prerequisites)

- [ ] T008 Create base data‑validation schemas in `contracts/` (`earthquake.schema.yaml`, `pressure-anomaly.schema.yaml`).  
  *Path*: `contracts/earthquake.schema.yaml`, `contracts/pressure-anomaly.schema.yaml`

- [ ] T008b [P] Create sample data fixture `tests/fixtures/sample_earthquake.yaml` containing at least one valid earthquake record and one valid pressure‑anomaly record matching the schemas in T008.  
  *Path*: `tests/fixtures/sample_earthquake.yaml`

- [ ] T011d Create `data/processed/config.yaml` defining pilot‑scope parameters.  
  ```yaml
  pilot_mode: true
  expected_earthquake_count: 12
  moving_average_days: 30
  min_permutation_iterations: 10000
  max_permutation_iterations: 100000
  convergence_variance_threshold: 1e-5
  ```  
  *Path*: `data/processed/config.yaml`

- [ ] T011b Create a formal deviation record in `docs/deviations.md` for FR‑001 (Global Data Download Blocked). Assign Deviation ID **DEV‑001**.  
  *Path*: `docs/deviations.md`

- [ ] T025b Create a formal deviation record in `docs/deviations.md` for FR‑011 (Climate‑Index Stratification Deferred). Assign Deviation ID **DEV‑002**.  
  *Path*: `docs/deviations.md`

---

## Phase 3 – User Story 1: Data Acquisition & Pre‑processing (Priority P1)

- [ ] T009 [P] Contract test for data‑schema validation in `tests/contract/test_data_schema.py`. Validates `earthquake.schema.yaml` and `pressure-anomaly.schema.yaml` against `tests/fixtures/sample_earthquake.yaml`.  
  *Path*: `tests/contract/test_data_schema.py`

- [ ] T010 Integration test for download pipeline in `tests/integration/test_download_pipeline.py`.  
  *Requirements*:  
  1. Fetch USGS 2018 Alaska subset (M≥4.0, depth≤70 km) from the official USGS API.  
  2. Assert row count matches `data/processed/config.yaml` → `expected_earthquake_count` (12) within 1 % tolerance.  
  3. Verify the script logs the absence of a global NOAA NCEP/NCAR source and references **DEV‑001**.  
  4. Exit with code 0 on success.  
  *Path*: `tests/integration/test_download_pipeline.py`

- [ ] T011a Implement `code/download.py` to fetch **verified test pressure data** and the **USGS 2018 Alaska subset**. The script checks `plan.md` for the global NOAA source; if missing, it logs **DEV‑001** and aborts the global download.  
  *Path*: `code/download.py`

- [ ] T012 Add checksumming and raw‑data immutability checks to `code/download.py`.  
  *Path*: `code/download.py`

- [ ] T013a Implement `code/preprocess.py::generate_land_mask()` to create `data/interim/land_mask.geojson` using `geopandas` (Natural Earth low‑resolution).  
  *Path*: `code/preprocess.py`, `data/interim/land_mask.geojson`

- [ ] T013b Implement `code/preprocess.py::apply_ocean_mask()` to load the land mask, compute interpolation reliability for each event, and exclude events over oceans where reliability < 95 %. Write filtered events to `data/interim/masked_events.csv`.  
  *Path*: `code/preprocess.py`, `data/interim/masked_events.csv`

- [ ] T013c Implement `code/preprocess.py::exclude_missing_pressure()` to drop any records with missing pressure values in the 0‑48 h pre‑event window. Write the cleaned set to `data/interim/clean_events.csv`.  
  *Path*: `code/preprocess.py`, `data/interim/clean_events.csv`

- [ ] T014 Implement `code/preprocess.py::calculate_left_censored_anomaly()` to compute daily pressure anomalies using a left‑censored 30‑day moving average (configurable via `data/processed/config.yaml`). Output to `data/interim/anomalies_raw.csv`.  
  *Path*: `code/preprocess.py`, `data/interim/anomalies_raw.csv`

- [ ] T016 Implement deduplication logic in `code/preprocess.py` (retain the most recent revision per `event_id`). Output to `data/interim/deduplicated_with_anomalies.csv`.  
  *Path*: `code/preprocess.py`, `data/interim/deduplicated_with_anomalies.csv`

- [ ] T017 Run `code/preprocess.py --output data/processed/master_dataset.csv` to produce the analysis‑ready dataset. Validate against schemas, row‑count tolerance, and generate a SHA‑256 checksum `data/processed/master_dataset.csv.sha256`. On validation failure, emit a JSON report and exit with code 1.  
  *Path*: `code/preprocess.py`, `data/processed/master_dataset.csv`, `data/processed/master_dataset.csv.sha256`, `data/processed/validation_report.json`

- [ ] T017b Verification test asserting the row‑count tolerance for `master_dataset.csv`.  
  *Path*: `tests/integration/test_master_dataset_rowcount.py`

- [ ] T018 Implement a JSON validation‑report generator in `code/preprocess.py` that lists missing required variables (FR‑008).  
  *Path*: `code/preprocess.py`, `data/processed/validation_report.json`

---

## Phase 4 – User Story 2: Statistical Association Analysis (Priority P2)

- [ ] T019 Unit test for KS‑test calculation (`tests/unit/test_statistics.py`).  
  *Path*: `tests/unit/test_statistics.py`

- [ ] T020 Unit test for permutation‑test convergence (`tests/unit/test_permutation.py`).  
  *Path*: `tests/unit/test_permutation.py`

- [ ] T022b Unit test for null‑hypothesis generation (`tests/unit/test_null_hypothesis.py`).  
  *Path*: `tests/unit/test_null_hypothesis.py`

- [ ] T021 Implement `code/analysis.py::run_ks_test()` to perform a two‑sample Kolmogorov–Smirnov test on `anomaly_value` for “event” vs. “control” windows. Output `statistic` and `p_value`.  
  *Path*: `code/analysis.py`, `data/processed/ks_test_results.json`

- [ ] T022 Implement the permutation test in `code/analysis.py::run_permutation_test()`. Reads iteration limits and convergence threshold from `data/processed/config.yaml`. Writes results to `data/processed/permutation_results.json`.  
  *Path*: `code/analysis.py`, `data/processed/permutation_results.json`

- [ ] T023 Implement p‑value calculation comparing the observed KS statistic to the 95th percentile of the permuted null distribution. Write to `data/processed/p_value_calc.json`.  
  *Path*: `code/analysis.py`, `data/processed/p_value_calc.json`

- [ ] T024 Compute Cohen’s d effect size for significant results (p < 0.05) and append to `data/processed/statistical_results.json`.  
  *Path*: `code/analysis.py`, `data/processed/statistical_results.json`

- [ ] T025 Implement a proxy control‑window stratification by matching month/day across non‑event years (basic date matching). Include a `framing_status` key set to `PROXY_NOT_FULFILLING_FR011` and reference **DEV‑002**. Output to `data/processed/climate_proxy_comparison.json`.  
  *Path*: `code/analysis.py`, `data/processed/climate_proxy_comparison.json`

- [ ] T026 Generate `data/processed/statistical_results.json` containing `p_value`, `effect_size`, `framing` (“associational”), and `test_method`. Validate schema.  
  *Path*: `code/analysis.py`, `data/processed/statistical_results.json`

---

## Phase 5 – User Story 3: Robustness & Sensitivity (Priority P3)

- [ ] T027 Unit test for sensitivity‑analysis sweep (`tests/unit/test_sensitivity.py`).  
  *Path*: `tests/unit/test_sensitivity.py`

- [ ] T028 Implement robustness checks in `code/analysis.py` to stratify results by magnitude bins (4.0–5.0, > 5.0) and geographic region (Ring of Fire vs. Other). Output separate p‑values and effect sizes.  
  *Path*: `code/analysis.py`, `data/processed/robustness_subsets.json`

- [ ] T029 Implement sensitivity analysis sweeping the anomaly‑cutoff over {0.5σ, 1.0σ, 1.5σ, 2.0σ, 2.5σ, 3.0σ}. Report variation in significance rates.  
  *Path*: `code/analysis.py`, `data/processed/sensitivity_sweep.json`

- [ ] T030 Apply Benjamini‑Hochberg FDR correction across all subset tests and sensitivity sweeps. Write corrected p‑values and flags to `data/processed/fdr_corrected_results.json`.  
  *Path*: `code/analysis.py`, `data/processed/fdr_corrected_results.json`

- [ ] T031 Generate `data/processed/robustness_report.json` summarising magnitude‑subsets, region‑subsets, and sensitivity‑sweep results. Verify presence of required keys.  
  *Path*: `data/processed/robustness_report.json`

- [ ] T037a Implement `code/report.py` to aggregate `statistical_results.json` and `robustness_report.json` into `data/processed/final_summary.json`.  
  *Path*: `code/report.py`, `data/processed/final_summary.json`

- [ ] T032 Compile the final pilot report in `docs/pilot_report.md`, explicitly labeling findings as “Pilot/Methodology Validation”, documenting all limitations, and referencing `docs/deviations.md`.  
  *Path*: `docs/pilot_report.md`

- [ ] T038 Future Enhancement: When a verified ENSO/PDO source appears in `plan.md`, replace the proxy logic in T025 with full climate‑index stratification and remove the `PROXY_NOT_FULFILLING_FR011` flag.  
  *Path*: `code/analysis.py`, `data/processed/climate_proxy_comparison.json`

---

## Phase 6 – Polish & Cross‑Cutting Concerns

- [ ] T033 Update documentation (`README.md`, `docs/quickstart.md`, `docs/`) to reflect pilot limitations and deviation records.  
  *Path*: `README.md`, `docs/quickstart.md`, `docs/`

- [ ] T034 Refactor code for memory efficiency; ensure peak RAM < 6 GB on the CPU‑only runner. Verify with `memory_profiler`.  
  *Path*: `code/`, verification script `scripts/check_memory.sh`

- [ ] T035 Validate full pipeline execution on the test dataset within the 6‑hour limit using `timeout 21600 python code/main.py`. Log must contain “Pipeline completed successfully within 6 hours”.  
  *Path*: `logs/quickstart_validation.log`

- [ ] T036 Add additional unit tests for ocean‑masking and missing‑data exclusion logic (`tests/unit/test_ocean_mask.py`, `tests/unit/test_missing_pressure.py`).  
  *Path*: `tests/unit/test_ocean_mask.py`, `tests/unit/test_missing_pressure.py`

- [ ] T037b Implement deterministic entry point `code/main.py` that orchestrates download, preprocessing, analysis, and reporting. CLI arguments: `--config data/processed/config.yaml --output-dir data/processed`. Exit with code 1 on any failure and log the error.  
  *Path*: `code/main.py`

--- 

## Dependencies & Execution Order (summary)

| Phase | Prerequisite Tasks | Dependent Tasks |
|------|--------------------|-----------------|
| **Setup** | – | T001‑T005 |
| **Foundational** | T001‑T005 | T008, T008b, T011d, T011b, T025b |
| **US 1** | Foundational | T009, T010, T011a‑T018 |
| **US 2** | US 1 (master dataset) | T019‑T026 |
| **US 3** | US 2 (statistical results) | T027‑T032, T038 |
| **Polish** | All previous phases | T033‑T037b |

*Tasks marked `[P]` may run in parallel when their file targets do not overlap.*
