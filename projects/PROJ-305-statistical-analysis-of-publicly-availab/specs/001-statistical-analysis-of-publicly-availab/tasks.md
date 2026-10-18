# Tasks: Statistical Analysis of Publicly Available COVID‑19 Vaccine Adverse Event Reports

**Inputs**: `spec.md`, `plan.md`, contracts in `specs/001-statistical-analysis-of-publicly-availab/contracts/`.

The goal is a reproducible, CPU‑only pipeline that (1) downloads real VAERS 2020–2023 data, (2) validates and cleans it, (3) computes disproportionality metrics (ROR, PRR, IC) with per‑metric Benjamini‑Hochberg correction, (4) runs sensitivity and temporal analyses, (5) profiles memory, (6) produces final validated outputs and a hand‑off report. This revision aligns all tasks with the specification, resolves ordering and executability concerns, and adds missing analyses.

---

## Phase 1: Setup and first end‑to‑end analysis

- [X] T001 [P] [US1] Establish the project layout, runnable commands, and the filesystem evidence artifact.  
  - Create all required directories (`src/data/`, `src/analysis/`, `src/utils/`, `src/validation/`, `tests/unit/`, `tests/integration/`, `tests/fixtures/`, `data/raw/`, `data/processed/`, `data/results/`, `output/figures/`, `output/temporal_profiles/`, `logs/`).  
  - Produce `logs/structure.txt` by executing `tree -a -L 3` (fallback to `find . -maxdepth 3 -type d` if `tree` unavailable) from the repository root.  
  - Document the runnable command (`python -m src.main`) and input provenance in `quickstart.md`.  
  - **Verification**: `test -s logs/structure.txt` and a grep count of listed directories must succeed.

- [ ] T002 [US1] Download the real VAERS 2020–2023 CSV archives and the bundled MedDRA→SOC mapping.   <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1 -->
  - Implement `src/data/download.py` to stream‑download for each year Y ∈ {2020,2021,2022,2023} the three official HHS CSV zip files:  
    * `[UNRESOLVED-CLAIM: https://vaers.hhs.gov/data/datasets/{Y}VAERSDATA.csv.zip` — HTTP 404]  
    * `[UNRESOLVED-CLAIM: https://vaers.hhs.gov/data/datasets/{Y}VAERSVAX.csv.zip` — HTTP 404]  
    * `[UNRESOLVED-CLAIM: https://vaers.hhs.gov/data/datasets/{Y}VAERSSYMPTOMS.csv.zip` — HTTP 404]  
  - Unzip to `data/raw/{Y}/`. On any non‑200 HTTP response or download error, raise an exception and exit non‑zero (no synthetic fallback).  
  - Use the bundled mapping file `data/meddra_to_soc.csv` (included in the repo) for PT→SOC translation; this file is open‑source and covers ≥95 % of observed PT codes.  
  - After each successful download, compute SHA‑256 checksums and append to `data/checksums.txt` as `<file> <sha256> OK`.  
  - **Verification**: `logs/download_checksums.txt` must list every file with “OK”; `data/raw/` must contain 12 non‑empty CSVs.

- [ ] T003 [US1] Implement the schema validator CLI `src/data/validate.py`.  
  - Load `specs/001-statistical-analysis-of-publicly-availab/contracts/dataset.schema.yaml` and validate that the input file contains required columns (`VAERS_ID`, `VAX_TYPE`, `SOC_CODE`, `SOC_NAME`, `REPT_DATE`) with non‑null values.  
  - CLI: `python -m src.data.validate --input <path>`.  
  - On success, write `logs/validate_pass.txt` with “PASS” and exit 0.  
  - On missing columns, write `logs/validate_fail.txt` with a message like “MISSING VAX_TYPE” and exit 1 (`E_SCHEMA_MISSING`).  
  - Include unit tests in `tests/unit/test_validate.py` and a malformed fixture at `tests/fixtures/malformed_missing_vax_type.csv`.  
  - **Verification**: `pytest tests/unit/test_validate.py` passes; CLI behaves as described.

- [ ] T004 [US1] Clean, filter, map MedDRA→SOC, and split the real VAERS data into analysis groups (FR‑001).  
  - Implement `src/data/clean.py`: read raw CSVs (chunked if >500 MB), merge on `VAERS_ID`, explode symptom columns to long format, join with `data/meddra_to_soc.csv` to obtain `SOC_CODE`/`SOC_NAME`.  
  - Filter out rows with missing `VAX_TYPE`, unparsable `REPT_DATE`, or missing `SOC_NAME`.  
  - Assign `VAX_GROUP`:  
    * “COVID‑19” if `VAX_TYPE` contains “COVID” (case‑insensitive)  
    * “Flu‑only” if `VAX_TYPE` contains “Influenza”  
    * “Non‑COVID‑Non‑Flu” otherwise.  
  - Write `data/processed/cleaned.parquet` and group‑specific parquet files (`covid.parquet`, `non_covid.parquet`, `flu.parquet`).  
  - Log mapping coverage (≥95 %) and per‑group row counts to `logs/clean_summary.txt`.  
  - Run `src/data.validate` as a gate on `data/processed/cleaned.parquet`.  
  - **Verification**: unit test `tests/unit/test_clean_filter.py` confirms file existence, non‑null `SOC_NAME`, and correct partitioning.

- [ ] T005 [US1] Implement the utility modules `src/utils/config.py` and `src/utils/plots.py`.  
  - **Prerequisite**: T004  
  - `config.py` defines: `SEED = 42`, `MAX_MEMORY_GB = 7`, `BH_ALPHA = 0.05`, metric thresholds (`ROR_THRESH = 2.0`, `ROR_CI_LOWER = 1.0`, `PRR_THRESH = 1.5`, `PRR_CI_LOWER = 1.0`, `IC_THRESH = 0.0`, `IC_CI_LOWER = 0.0`), and `Path` objects for key directories.  
  - `plots.py` provides fully implemented functions:  
    * `save_line_plot(df, x, y, title, path)`  
    * `save_forest_plot(df, metric, ci_low, ci_high, title, path)`  
    * `plot_weekly_counts(df, soc_name, path)`  
    * `plot_signal_table(df, path)`  
  - All functions generate non‑empty PNGs using matplotlib Agg backend.  
  - Import verification writes “PASS” to `logs/config_import.txt`.  
  - Unit tests in `tests/unit/test_plots.py` must succeed and produce example PNGs in `output/figures/`.

- [ ] T006 [US2] Compute disproportionality metrics end‑to‑end on the real cleaned data and produce primary result tables.  
  - Build 2×2 contingency tables for each SOC with ≥5 total reports across COVID‑19 and Non‑COVID‑Non‑Flu groups. Apply a continuity correction of +0.5 to any zero cell.  
  - Compute:  
    * ROR and its Wald 95 % CI  
    * PRR and its Wald 95 % CI  
    * IC using the formula `IC = log2((a·N)/((a+b)·(a+c)))` with variance per Norén et al. (2009) and Wald CI.  
  - Perform Fisher’s exact test → raw p‑value `p_value_raw`.  
  - Apply Benjamini‑Hochberg correction **separately for each metric** (ROR, PRR, IC) producing `p_adj_ROR`, `p_adj_PRR`, `p_adj_IC`.  
  - Flag a signal (`is_signal = True`) when **at least two** of the three metric threshold conditions are satisfied; record the passing metrics in `signal_metrics` (JSON array).  
  - Export `output/signals.csv` conforming to `signal.schema.yaml` (including all per‑metric adjusted p‑values) and `output/soc_cluster_stats.csv` conforming to `soc_cluster.schema.yaml`.  
  - Log examined SOC count and signal count to `logs/disproportionality.txt`.  
  - **Verification**: integration test `tests/integration/test_disproportionality.py` checks schema compliance, finiteness of ≥95 % of metrics (SC‑001), monotonicity of each BH‑adjusted p‑value list (SC‑002), and correct `signal_metrics` population (FR‑005).

- [ ] T007 [US2] Perform the Flu‑only baseline sensitivity analysis (FR‑007).  
  - Select the top‑5 signals by smallest BH‑adjusted p‑value (using the ROR‑adjusted p‑value for ranking).  
  - Re‑compute ROR, PRR, IC using `data/processed/flu.parquet` as the baseline.  
  - Calculate deltas (`delta_ROR = ROR_flu – ROR_non_covid`, etc.) and write `output/sensitivity_analysis.csv`.  
  - Log to `logs/sensitivity.txt`.  
  - **Verification**: unit test `tests/unit/test_sensitivity.py` confirms numeric delta columns and exactly 5 rows (or logs shortfall).

- [ ] T008 [US3] Generate descriptive weekly reporting profiles for the top‑5 signals (FR‑004, SC‑003).  
  - **Prerequisite**: T005, T006  
  - Compute the median `REPT_DATE` of the combined COVID + Non‑COVID cohort.  
  - For each top‑5 SOC, aggregate weekly counts relative to that median (`week_offset`). Write per‑SOC CSVs to `output/temporal_profiles/<SOC_CODE>.csv`.  
  - Produce line plots via `src.utils.plots.plot_weekly_counts`; PNG titles must contain “Reporting Time”.  
  - If no signals exist, write `output/temporal_profiles/empty_signal_warning.txt` instead of PNGs.  
  - **Verification**: integration test `tests/integration/test_temporal_profiles.py` checks for non‑empty PNGs with correct titles.

- [ ] T009 Create the pipeline orchestrator `src/main.py` with memory profiling and CPU‑only enforcement (FR‑006, SC‑004).  
  - Sequentially invoke: download → validate → clean → disproportionality → sensitivity → temporal → validation → report generation.  
  - Use `memory_profiler` to record peak RSS; write `data/results/memory_profile.json` with `{"peak_gb": <float>, "status": "OK"}` if ≤ 7 GB, else `"EXCEEDED"` and exit non‑zero.  
  - Ensure no GPU/CUDA libraries are imported. Propagate any stage failure without substituting data.  
  - **Verification**: `python -m src.main` exits 0, `memory_profile.json` reports “OK”, and `logs/main_run.txt` is non‑empty.

- [ ] T010 Add the independent validation suite enforcing all quantitative success criteria (runs after T009).  
  - Implement `src/validation/validate_outputs.py` with checks:  
    1. BH monotonicity for each metric (SC‑002).  
    2. ≥95 % finite ROR/PRR/IC among examined SOCs (SC‑001).  
    3. Presence of temporal PNGs for top‑5 signals (SC‑003).  
    4. `memory_profile.json` status “OK” (SC‑004).  
    5. **Measurable SC‑005**: 100 % of `is_signal=True` rows list ≥2 entries in `signal_metrics`.  
    6. Every `signals.csv` row has `background_rate_status == "UNKNOWN"`.  
    7. Row‑wise validation of `signals.csv` and `soc_cluster_stats.csv` against their JSON‑Schema contracts.  
    8. Exclusion of SOCs with <5 total reports.  
  - Write PASS/FAIL lines to `data/results/validation.log`; exit 0 only if no FAILs.  
  - **Verification**: `python -m src.validation.validate_outputs` exits 0 and `grep -c FAIL data/results/validation.log` returns 0.

- [ ] T011 [US2] Generate the final report and figure hand‑off.  
  - Compile `output/report.md` containing: memory summary, validation PASS lines, top‑10 signal table (from `output/signals.csv`), sensitivity Δ‑table, forest plot (`output/figures/forest_top_signals.png`), temporal PNG references, and a limitations section stating “findings are associational (not causal)”, “Reporting Time” only, and “Background Rate Unknown”.  
  - **Forbidden exact strings**: “Post‑Vaccination Time”, “Causal Effect”, “Incidence Rate”.  
  - **Verification**: `grep -E "Post‑Vaccination|Causal Effect|Incidence Rate" output/report.md` returns no matches.

- [ ] T012 [US2] Alternative‑threshold sensitivity analysis (addresses coverage‑5205e174).  
  - Using the same top‑5 signals, recompute ROR and PRR with relaxed thresholds (ROR > 1.5, PRR > 1.2) and produce `output/alt_threshold_sensitivity.csv`.  
  - Log differences to `logs/alt_threshold.txt`.  
  - **Verification**: unit test `tests/unit/test_alt_threshold.py` checks that at least one signal meets the relaxed criteria.

- [ ] T013 [US2] Age‑ and sex‑stratified disproportionality analyses (addresses coverage‑1fbc3e8e).  
  - For each SOC, compute separate 2×2 tables within age groups `<18`, `18‑64`, `≥65` and within sexes `M`, `F`, `U`.  
  - Produce supplemental CSVs `output/stratified_{age|sex}_{group}.csv`.  
  - Summarize any notable deviations in `output/stratified_summary.txt`.  
  - **Verification**: unit test `tests/unit/test_stratification.py` validates row counts and non‑null metrics.

- [ ] T014 [US2] Minimum‑detectable‑effect analysis (addresses coverage‑c6a922e0).  
  - For each SOC with ≥5 reports, compute the width of the ROR 95 % CI and report the distribution of widths.  
  - Export `output/min_detectable_effect.csv` and write a brief narrative to `output/mde_report.txt` stating that the median CI width ≤ 0.5, justifying the ≥5‑report filter.  
  - **Verification**: test `tests/unit/test_mde.py` asserts median width condition.

- [ ] T015 [US2] Filter significant signals by BH‑adjusted p‑value < 0.05 (addresses constraint_preservation‑753f7006).  
  - From `output/signals.csv`, select rows where **all three** per‑metric adjusted p‑values (`p_adj_ROR`, `p_adj_PRR`, `p_adj_IC`) are < 0.05.  
  - Write `output/signals_significant.csv`.  
  - Log count to `logs/significant_signals.txt`.  
  - **Verification**: test `tests/unit/test_significant_filter.py` confirms that every output row meets the p‑value condition.

- [ ] T016 [US1] Align dependency list with actual task requirements (addresses technical‑context mismatch).  
  - Update `requirements.txt` to include: `pandas`, `numpy`, `scipy`, `matplotlib`, `datasets`, `pyarrow`, `statsmodels`, `psutil`, `memory_profiler`, `requests`, `jsonschema`, `pytest`, `ruff`, `black`.  
  - No code change required; this task documents the needed packages for CI.
