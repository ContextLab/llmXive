# Tasks: Statistical Analysis of Publicly Available COVID‑19 Vaccine Adverse Event Reports

**Inputs**: `spec.md`, `plan.md`, contracts in `specs/001-statistical-analysis-of-publicly-availab/contracts/`.

The goal is a reproducible, CPU‑only pipeline that (1) downloads real VAERS 2020‑2023 data, (2) validates and cleans it, (3) computes disproportionality metrics (ROR, PRR, IC) with Benjamini‑Hochberg correction, (4) runs sensitivity and temporal analyses, (5) profiles memory, (6) produces final validated outputs and a hand‑off report. All tasks respect the specification, ordering, and data‑flow constraints.

---

## Phase 1: Setup and first end‑to‑end analysis

- [X] T001 [P] [US1] Establish the project layout, runnable commands, and filesystem evidence artifact.  
  - Create required directories (`src/data/`, `src/analysis/`, `src/utils/`, `src/validation/`, `tests/unit/`, `tests/integration/`, `data/raw/`, `data/processed/`, `output/`, `logs/`).  
  - Produce `logs/structure.txt` via `tree -a -L 3` (fallback to `find . -maxdepth 3 -type d`).  
  - Document the runnable command (`python -m src.main`) and input provenance in `quickstart.md`.  
  - **Verification**: `test -s logs/structure.txt` and a grep count of listed directories must succeed.

- [ ] T002 [P] [US1] Download the verified VAERS 2020‑2023 parquet dataset from Hugging Face. <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1 -->
  - Implement `src/data/download.py` that uses `datasets.load_dataset("chrisvoncsefalvay/vaers-outcomes", split="train")` (or the appropriate split) to fetch the parquet file.  
  - Write the downloaded parquet to `data/raw/vaers_2020_2023.parquet`.  
  - Compute a SHA‑256 checksum of the file and record `<file> <sha256>` in `data/checksums.txt`.  
  - On any download or checksum error raise an exception (no synthetic fallback).  
  - **Verification**: `grep -c "vaers_2020_2023.parquet" data/checksums.txt` returns 1 and the file size > 0 KB.

- [ ] T003 [P] [US1] Implement the schema validator CLI `src/data/validate.py`.  
  - Load `specs/001-statistical-analysis-of-publicly-availab/contracts/dataset.schema.yaml` and verify required columns (`VAERS_ID`, `VAX_TYPE`, `SOC_CODE`, `SOC_NAME`, `REPT_DATE`) are present and non‑null.  
  - CLI: `python -m src.data.validate --input <path>`.  
  - On success write `logs/validate_pass.txt` (“PASS”) and exit 0; on failure write `logs/validate_fail.txt` with details and exit 1.  
  - Include unit tests in `tests/unit/test_validate.py` and a malformed fixture at `tests/fixtures/malformed_missing_vax_type.csv`.  
  - **Verification**: `pytest tests/unit/test_validate.py` passes; CLI behaves as specified.

- [ ] T004 [P] [US1] Clean, filter, map MedDRA→SOC, and split the real VAERS data into analysis groups (FR‑001).  
  - Implement `src/data/clean.py`: read `data/raw/vaers_2020_2023.parquet` (streamed if > 500 MB), drop rows with missing `VAX_TYPE`, unparsable `REPT_DATE`, or missing `SOC_NAME`.  
  - Join with `data/meddra_to_soc.csv` to obtain `SOC_CODE`/`SOC_NAME`.  
  - Create `VAX_GROUP` column:  
    * “COVID‑19” if `VAX_TYPE` contains “COVID” (case‑insensitive)  
    * “Flu‑only” if `VAX_TYPE` contains “Influenza”  
    * “Non‑COVID‑Non‑Flu” otherwise.  
  - Write `data/processed/cleaned.parquet` and group‑specific parquet files (`covid.parquet`, `non_covid.parquet`, `flu.parquet`).  
  - Log mapping coverage (≥ 95 %) and per‑group row counts to `logs/clean_summary.txt`.  
  - Run `src/data/validate.py` as a gate on `data/processed/cleaned.parquet`.  
  - **Verification**: unit test `tests/unit/test_clean_filter.py` confirms file existence, non‑null `SOC_NAME`, and correct partitioning.

- [ ] T005 [P] [US1] Implement utility modules `src/utils/config.py` and `src/utils/plots.py`.  
  - **Prerequisite**: T004.  
  - `config.py` defines: `SEED = 42`, `MAX_MEMORY_GB = 7`, `BH_ALPHA = 0.05`, metric thresholds (`ROR_THRESH = 2.0`, `ROR_CI_LOWER = 1.0`, `PRR_THRESH = 1.5`, `PRR_CI_LOWER = 1.0`, `IC_THRESH = 0.0`, `IC_CI_LOWER = 0.0`), and `Path` objects for key directories.  
  - `plots.py` provides functions: `save_line_plot`, `save_forest_plot`, `plot_weekly_counts`, `plot_signal_table`; all generate non‑empty PNGs using the Agg backend.  
  - Import verification writes “PASS” to `logs/config_import.txt`.  
  - **Verification**: `pytest tests/unit/test_plots.py` succeeds and produces example PNGs in `output/figures/`.

## Phase 2: Core analysis, validation, and extensions

- [ ] T006 [P] [US2] Compute disproportionality metrics end‑to‑end on the cleaned data and produce primary result tables.  
  - Build 2×2 contingency tables for each SOC with ≥ 5 total reports across COVID‑19 and Non‑COVID‑Non‑Flu groups; apply continuity correction + 0.5 to any zero cell.  
  - Compute:  
    * ROR with Wald 95 % CI  
    * PRR with Wald 95 % CI  
    * IC (log₂ formulation) with variance per Norén et al. (2009) and Wald CI  
    * Fisher’s exact test → raw p‑value `p_value_raw`.  
  - Apply Benjamini‑Hochberg correction **separately for each metric** (ROR, PRR, IC) to obtain `p_adj_ROR`, `p_adj_PRR`, `p_adj_IC`.  
  - Flag a signal (`is_signal = True`) when **at least two** of the three metric thresholds are satisfied (ROR > 2.0 & lower CI > 1.0, PRR > 1.5 & lower CI > 1.0, IC > 0 & lower CI > 0). Record passing metrics in `signal_metrics` (JSON array).  
  - Export:  
    * `output/signals.csv` adhering to `signal.schema.yaml` (includes all per‑metric adjusted p‑values).  
    * `output/soc_cluster_stats.csv` adhering to `soc_cluster.schema.yaml`.  
  - Log examined SOC count and signal count to `logs/disproportionality.txt`.  
  - **Verification**: integration test `tests/integration/test_disproportionality.py` checks schema compliance, ≥ 95 % finite metrics (SC‑001), monotonicity of each BH‑adjusted p‑value list (SC‑002), and correct `signal_metrics` population (FR‑005).

- [ ] T015 [P] [US2] Estimate empirical false‑discovery rate via bootstrap and record the empirical FDR.  
  - Perform 1 000 bootstrap resamples of the cleaned dataset, recompute disproportionality metrics and apply the 2‑out‑of‑3 rule on each resample.  
  - Calculate the proportion of resamples that produce a signal meeting the rule; this proportion is the empirical FDR.  
  - Write the value to `output/empirical_fdr.txt` (single line with a float).  
  - Log the bootstrap run details to `logs/bootstrap.txt`.  
  - **Verification**: unit test `tests/unit/test_bootstrap_fdr.py` asserts the file exists, the value is a float between 0 and 1, and that it is ≤ 0.05 for the final accepted signals.

- [ ] T007 [P] [US2] Perform the Flu‑only baseline sensitivity analysis (FR‑007).  
  - Using the primary results from T006 (COVID‑vs‑Non‑COVID baseline), select the top‑5 signals by smallest BH‑adjusted p‑value.  
  - Re‑compute ROR, PRR, IC for those SOCs **keeping COVID‑19 as the target vaccine** while using the **Flu‑only** dataset as an *alternative* baseline; the primary baseline remains **Non‑COVID‑Non‑Flu** (all other vaccines).  
  - Calculate deltas between the metrics obtained with the primary baseline (Non‑COVID‑Non‑Flu) and the alternative Flu‑only baseline (`delta_ROR = ROR_flu_baseline – ROR_non_covid_baseline`, `delta_PRR = PRR_flu_baseline – PRR_non_covid_baseline`, `delta_IC = IC_flu_baseline – IC_non_covid_baseline`) and write `output/sensitivity_analysis.csv`.  
  - Log actions to `logs/sensitivity.txt`.  
  - **Verification**: unit test `tests/unit/test_sensitivity.py` confirms numeric delta columns and exactly 5 rows (or logs shortfall).

- [ ] T008 [P] [US3] Generate descriptive weekly reporting profiles for the top‑5 signals (FR‑004, SC‑003).  
  - **Prerequisite**: T006, T005.  
  - Compute the median `REPT_DATE` of the combined COVID + Non‑COVID cohort.  
  - For each top‑5 SOC, aggregate weekly counts relative to that median (`week_offset`). Write per‑SOC CSVs to `output/temporal_profiles/<SOC_CODE>.csv`.  
  - Produce line plots via `src.utils.plots.plot_weekly_counts`; PNG titles must contain “Reporting Time”.  
  - If no signals exist, write `output/temporal_profiles/empty_signal_warning.txt` instead of PNGs.  
  - **Verification**: integration test `tests/integration/test_temporal_profiles.py` checks for non‑empty PNGs with correct titles.

- [ ] T009 [S] [US1] Create the pipeline orchestrator `src/main.py` with memory profiling and CPU‑only enforcement (FR‑006, SC‑004).  
  - Sequentially invoke: download → validate → clean → disproportionality → bootstrap FDR (T015) → sensitivity → temporal → validation → report generation.  
  - Use `memory_profiler` to record peak RSS; write `data/results/memory_profile.json` with `{"peak_gb": <float>, "status": "OK"}` if ≤ 7 GB, else `"EXCEEDED"` and exit non‑zero.  
  - Ensure no GPU/CUDA libraries are imported; any attempt to import such a library should raise an error.  
  - **Verification**: `python -m src.main` exits 0, `memory_profile.json` reports “OK”, and `logs/main_run.txt` is non‑empty.

- [ ] T010 [P] [US2] Add the independent validation suite enforcing all quantitative success criteria (runs after T009).  
  - Implement `src/validation/validate_outputs.py` with checks:  
    1. BH monotonicity for each metric (SC‑002).  
    2. ≥ 95 % finite ROR/PRR/IC among examined SOCs (SC‑001).  
    3. Presence of temporal PNGs for top‑5 signals (SC‑003).  
    4. `memory_profile.json` status “OK” (SC‑004).  
    5. Every `is_signal=True` row lists ≥2 entries in `signal_metrics` (SC‑005).  
    6. Row‑wise validation of `output/signals.csv` against `signal.schema.yaml` and `output/soc_cluster_stats.csv` against `soc_cluster.schema.yaml`.  
    7. Exclusion of SOCs with <5 total reports.  
    8. **Empirical FDR check**: read `output/empirical_fdr.txt` and assert the value ≤ 0.05.  
  - Write PASS/FAIL lines to `data/results/validation.log`; exit 0 only if no FAIL lines.  
  - **Verification**: `python -m src.validation.validate_outputs` exits 0 and `grep -c FAIL data/results/validation.log` returns 0.

- [ ] T011 [P] [US2] Generate the final report and figure hand‑off.  
  - Compile `output/report.md` containing: memory summary, validation PASS lines, top‑10 signal table (from `output/signals.csv`), sensitivity Δ‑table, forest plot (`output/figures/forest_top_signals.png`), references to temporal PNGs, and a limitations section stating “findings are associational (not causal)”, “Reporting Time” only, and “Background Rate Unknown”.  
  - **Forbidden exact strings**: “Post‑Vaccination Time”, “Causal Effect”, “Incidence Rate”.  
  - **Verification**: `grep -E "Post‑Vaccination|Causal Effect|Incidence Rate" output/report.md` returns no matches.

- [ ] T013 [P] [US2] Age‑ and sex‑stratified disproportionality analyses (addresses coverage‑1fbc3e8e).  
  - For each SOC, compute separate 2×2 tables within age groups `<18`, `18‑64`, `≥65` and within sexes `M`, `F`, `U`.  
  - Produce supplemental CSVs `output/stratified_age_{group}.csv` and `output/stratified_sex_{group}.csv`.  
  - Summarize any notable deviations in `output/stratified_summary.txt`.  
  - **Verification**: unit test `tests/unit/test_stratification.py` validates row counts and non‑null metrics.

- [ ] T016 [P] [US2] Align dependency list with actual task requirements (addresses technical‑context mismatch).  
  - Update `requirements.txt` to include: `pandas`, `numpy`, `scipy`, `matplotlib`, `datasets`, `pyarrow`, `statsmodels`, `psutil`, `memory_profiler`, `requests`, `jsonschema`, `pytest`, `ruff`, `black`.  
  - **Verification**: run `grep -E "pandas|numpy|scipy|matplotlib|datasets|pyarrow|statsmodels|psutil|memory_profiler|requests|jsonschema|pytest|ruff|black" requirements.txt` and ensure each package appears at least once.  
  - No code change required; this task documents the needed packages for CI.

*All unchecked tasks remain pending until their implementations and verification steps succeed. The checklist respects data flow, CPU‑only constraints, and the full set of functional and success criteria defined in the specification. Gold‑plating tasks not tied to any FR/SC have been removed, and the pipeline now includes the required empirical FDR validation.* 