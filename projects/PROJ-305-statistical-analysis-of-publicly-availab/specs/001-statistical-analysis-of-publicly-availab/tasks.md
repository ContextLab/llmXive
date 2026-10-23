# Tasks: Statistical Analysis of Publicly Available COVID‑19 Vaccine Adverse Event Reports

**Inputs**: `spec.md`, `plan.md`, contracts in `specs/001-statistical-analysis-of-publicly-availab/contracts/`.

The pipeline must (1) download the verified VAERS 2020‑2023 dataset, (2) validate and clean it, (3) compute disproportionality metrics (ROR, PRR, IC) with Benjamini‑Hochberg correction, (4) perform a hold‑out validation, (5) run a Flu‑only sensitivity analysis, (6) generate descriptive temporal profiles for the top signals, (7) profile memory usage, (8) validate all outputs, and (9) produce a final hand‑off report. All tasks respect the specification, ordering, and CPU‑only constraints.

---

## Phase 1 – Setup and first end‑to‑end analysis

- [ ] T001 [P] [US1] Establish project layout, runnable command, and directory evidence.  
  - Create required directories (`src/data/`, `src/analysis/`, `src/utils/`, `src/validation/`, `tests/unit/`, `tests/integration/`, `data/raw/`, `data/processed/`, `output/`, `logs/`).  
  - Produce `logs/structure.txt` via `tree -a -L 3`.  
  - Document the runnable command (`python -m src.main`) and input provenance in `quickstart.md`.  
  - **Verification**: `test -s logs/structure.txt` succeeds and `grep -c src logs/structure.txt` ≥ 1.

- [ ] T002 [P] [US1] Download the verified VAERS 2020‑2023 parquet dataset.  
  - Implement `src/data/download.py` that uses `datasets.load_dataset("vaers/vaers2020_2023", split="train")` to fetch the parquet file.  
  - Write the file to `data/raw/vaers_2020_2023.parquet`.  
  - Compute a SHA‑256 checksum and record `data/raw/vaers_2020_2023.parquet <sha256>` in `data/checksums.txt`.  
  - On any download or checksum error raise an exception (no synthetic fallback).  
  - **Verification**: `grep -c "vaers_2020_2023.parquet" data/checksums.txt` returns 1 and `stat --format=%s data/raw/vaers_2020_2023.parquet` > 0.

- [ ] T003 [P] [US1] Implement a robust schema‑validation CLI for the raw VAERS file.  
  - Create `src/data/validate.py` with a CLI `python -m src.data.validate --schema <schema_path> --input <file>`.  
  - The CLI must load the JSON‑Schema at `specs/001-statistical-analysis-of-publicly-availab/contracts/raw_dataset.schema.yaml` and validate `data/raw/vaers_2020_2023.parquet`.  
  - On success write `logs/validate_raw_pass.txt` containing “PASS” and exit 0; on failure write `logs/validate_raw_fail.txt` with the validation error and exit 1.  
  - Add unit tests in `tests/unit/test_validate_raw.py` that (a) succeed on the downloaded file and (b) deliberately fail on a malformed fixture `tests/fixtures/malformed_missing_vax_type.parquet`.  
  - **Verification**: `pytest tests/unit/test_validate_raw.py` passes and the CLI returns exit 0 for the real file.

- [ ] T004 [P] [US1] Clean, filter, map MedDRA→SOC, and assign vaccine groups.  
  - Implement `src/data/clean.py` to read `data/raw/vaers_2020_2023.parquet` (streamed if > 500 MB).  
  - Drop rows with missing `VAX_TYPE`, unparsable `REPT_DATE`, or missing `SOC_CODE`.  
  - Join with `data/meddra_to_soc.csv` to obtain `SOC_NAME`.  
  - Create `VAX_GROUP` column:  
    * “COVID‑19” if `VAX_TYPE` contains “COVID” (case‑insensitive)  
    * “Flu‑only” if `VAX_TYPE` contains “Influenza”  
    * “Non‑COVID‑Non‑Flu” otherwise.  
  - Write the cleaned dataset to `data/processed/cleaned.parquet` and also write group‑specific parquet files (`data/processed/covid.parquet`, `.../non_covid.parquet`, `.../flu.parquet`).  
  - Log mapping coverage (≥ 95 %) and per‑group row counts to `logs/clean_summary.txt`.  
  - Run the raw‑schema validator (T003) as a gate before writing the cleaned file.  
  - **Verification**: `tests/unit/test_clean_filter.py` confirms existence of `cleaned.parquet`, non‑null `SOC_NAME`, and correct `VAX_GROUP` assignment.

- [ ] T005 [P] [US1] Provide core utility modules.  
  - `src/utils/config.py` defines constants: `SEED = 42`, `MAX_MEMORY_GB = 7`, `BH_ALPHA = 0.05`, metric thresholds (`ROR_THRESH = 2.0`, `ROR_CI_LOWER = 1.0`, `PRR_THRESH = 1.5`, `PRR_CI_LOWER = 1.0`, `IC_THRESH = 0.0`, `IC_CI_LOWER = 0.0`), and `Path` objects for key directories (`DATA_RAW`, `DATA_PROCESSED`, `OUTPUT`, `LOGS`).  
  - `src/utils/plots.py` supplies `save_line_plot`, `save_forest_plot`, and `plot_weekly_counts`, all using the Agg backend to generate non‑empty PNGs.  
  - Import verification writes “PASS” to `logs/config_import.txt`.  
  - **Verification**: `pytest tests/unit/test_plots.py` succeeds and example PNGs are created under `output/figures/`.

---

## Phase 2 – Core analysis, validation, and extensions

- [ ] T006 [P] [US2] Compute disproportionality metrics for each SOC.  
  - Implement `src/analysis/disproportionality.py` to:  
    1. Build 2 × 2 contingency tables for every SOC with ≥ 5 total reports across the COVID‑19 and Non‑COVID‑Non‑Flu groups, applying a continuity correction of 0.5 to any zero cell.  
    2. Compute ROR (Clopper‑Pearson CI), PRR (beta‑binomial CI), and IC (Poisson‑Gamma CI).  
    3. Perform Fisher’s exact test → raw p‑value.  
    4. Apply Benjamini‑Hochberg correction **separately** for each metric, producing adjusted p‑values (`p_adj_ROR`, `p_adj_PRR`, `p_adj_IC`).  
    5. Flag a signal (`is_signal = True`) when **at least two** metrics satisfy their literature‑based thresholds (ROR > 2.0 & lower CI > 1.0, PRR > 1.5 & lower CI > 1.0, IC > 0 & lower CI > 0). Record the passing metric names in `signal_metrics` (JSON array).  
  - Export `output/signals.csv` (conforms to `signal.schema.yaml`) and `output/soc_cluster_stats.csv` (conforms to `soc_cluster.schema.yaml`).  
  - Log examined SOC count and signal count to `logs/disproportionality.txt`.  
  - **Verification**: `tests/integration/test_disproportionality.py` checks schema compliance, ≥ 95 % finite metrics (SC‑001), monotonicity of each BH‑adjusted p‑value list (SC‑002), and correct population of `signal_metrics`.

- [ ] T007 [P] [US2] Perform the Flu‑only baseline sensitivity analysis.  
  - Using the primary results from T006, select the top‑5 signals by smallest BH‑adjusted p‑value.  
  - Re‑compute ROR, PRR, and IC for those SOCs with COVID‑19 as the target vaccine and the **Flu‑only** cohort as the alternative baseline (primary baseline remains Non‑COVID‑Non‑Flu).  
  - Calculate deltas (`delta_ROR`, `delta_PRR`, `delta_IC`) between Flu‑only and primary baselines and write `output/sensitivity_analysis.csv`.  
  - Log actions to `logs/sensitivity.txt`.  
  - **Verification**: `tests/unit/test_sensitivity.py` confirms the file has exactly 5 rows, numeric delta columns, and no missing values.

- [ ] T008 [P] [US3] Generate descriptive weekly reporting profiles for the top‑5 signals.  
  - Compute the median `REPT_DATE` of the combined COVID‑19 + Non‑COVID‑Non‑Flu cohort.  
  - For each of the top‑5 SOCs, aggregate weekly counts relative to that median (`week_offset`). Write per‑SOC CSVs to `output/temporal_profiles/<SOC>.csv`.  
  - Produce line‑plot PNGs (`output/temporal_profiles/<SOC>.png`) via `src.utils.plots.plot_weekly_counts`; each title must contain “Reporting Time”.  
  - If no signals exist, write `output/temporal_profiles/empty_signal_warning.txt` instead of PNGs.  
  - **Verification**: `tests/integration/test_temporal_profiles.py` asserts existence of the CSVs and PNGs with correct titles.

- [ ] T009 [P] [US1] Orchestrate the full pipeline with memory profiling and CPU‑only enforcement.  
  - Create `src/main.py` that sequentially invokes: download (T002) → raw validation (T003) → cleaning (T004) → disproportionality (T006) → hold‑out validation (T012) → sensitivity (T007) → temporal profiling (T008) → final report generation (T011).  
  - Use `memory_profiler` to record peak RSS and write `data/results/memory_profile.json` (`{"peak_gb": <float>, "status": "OK"}` if ≤ 7 GB, else `"EXCEEDED"` and exit non‑zero).  
  - Guard against any import of GPU‑only libraries; attempts raise a clear error.  
  - Log the full run to `logs/main_run.txt`.  
  - **Verification**: `python -m src.main` exits 0, `memory_profile.json` reports `"status": "OK"`, and `logs/main_run.txt` is non‑empty.

- [ ] T010 [P] [US2] Implement a comprehensive validation suite for all outputs.  
  - Create `src/validation/validate_outputs.py` that checks:  
    1. Monotonicity of BH‑adjusted p‑values for each metric (SC‑002).  
    2. ≥ 95 % finite ROR/PRR/IC among examined SOCs (SC‑001).  
    3. Presence of temporal PNGs for the top‑5 signals (SC‑003).  
    4. `memory_profile.json` status equals “OK” (SC‑004).  
    5. Every `is_signal=True` row lists ≥ 2 entries in `signal_metrics` (SC‑005).  
    6. Row‑wise validation of `output/signals.csv` against `signal.schema.yaml` and `output/soc_cluster_stats.csv` against `soc_cluster.schema.yaml`.  
    7. Exclusion of SOCs with < 5 total reports.  
    8. Hold‑out validation flag consistency (see T012).  
  - Write PASS/FAIL lines to `data/results/validation.log` and exit 0 only if no FAIL lines appear.  
  - **Verification**: `python -m src.validation.validate_outputs` exits 0 and `grep -c FAIL data/results/validation.log` returns 0.

- [ ] T011 [P] [US2] Generate the final markdown report and figure hand‑off.  
  - Implement `src/report/generate_report.py` that assembles `output/report.md` containing:  
    * Memory usage summary, validation PASS lines.  
    * Top‑10 signal table (from `output/signals.csv`).  
    * Sensitivity Δ‑table.  
    * Forest plot (`output/figures/forest_top_signals.png`).  
    * References to temporal PNGs.  
    * Limitations section explicitly stating “findings are associational (not causal)”, “Reporting Time” only, and “Background Rate Unknown”.  
  - Forbidden strings (“Post‑Vaccination Time”, “Causal Effect”, “Incidence Rate”) must not appear.  
  - Log generation to `logs/report_generation.txt`.  
  - **Verification**: `grep -E "Post‑Vaccination|Causal Effect|Incidence Rate" output/report.md` returns no matches.

- [ ] T012 [P] [US2] Perform independent hold‑out validation of identified signals.  
  - Randomly split `data/processed/cleaned.parquet` into a **training set** (80 %) and a **hold‑out set** (20 %) using the fixed seed from `src.utils.config.SEED`.  
  - Re‑run the disproportionality calculations on the hold‑out set (reuse code from T006).  
  - For each SOC flagged as a signal in the training run, verify that it also meets the 2‑out‑of‑3 metric thresholds **and** has BH‑adjusted p‑value < 0.05 in the hold‑out run.  
  - Write `output/holdout_signals.csv` containing only those SOCs that pass both training and hold‑out criteria, and log the process to `logs/holdout.txt`.  
  - **Verification**: `tests/unit/test_holdout_validation.py` checks that every row in `holdout_signals.csv` appears in `output/signals.csv` and that the hold‑out criteria are satisfied.

- [ ] T016 [P] Update the project dependency list.  
  - Edit `requirements.txt` to include the exact packages required by the pipeline: `pandas`, `numpy`, `scipy`, `matplotlib`, `datasets`, `pyarrow`, `statsmodels`, `psutil`, `memory_profiler`, `requests`, `jsonschema`, `pytest`, `ruff`, `black`.  
  - **Verification**: run `grep -E "pandas|numpy|scipy|matplotlib|datasets|pyarrow|statsmodels|psutil|memory_profiler|requests|jsonschema|pytest|ruff|black" requirements.txt` and ensure each appears at least once.  

---  

### Dependency‑requirement mapping (summary)

| Spec / FR | Satisfying Task(s) |
|-----------|-------------------|
| FR‑001 (download & clean) | T002, T003, T004 |
| FR‑002 (ROR/PRR/IC) | T006 |
| FR‑003 (BH correction) | T006 |
| FR‑004 (weekly profile) | T008 |
| FR‑005 (2‑out‑of‑3 + hold‑out) | T006, T012 |
| FR‑006 (CPU‑only) | T009 |
| FR‑007 (Flu‑only sensitivity) | T007 |
| SC‑001 (≥ 95 % finite metrics) | T010 |
| SC‑002 (monotonic BH) | T010 |
| SC‑003 (temporal plots) | T010 |
| SC‑004 (memory ≤ 7 GB) | T009, T010 |
| SC‑005 (signal‑metric list) | T010 |

All tasks respect the required data flow, use only real VAERS data, and avoid any fabricated inputs or GPU‑only computations.
