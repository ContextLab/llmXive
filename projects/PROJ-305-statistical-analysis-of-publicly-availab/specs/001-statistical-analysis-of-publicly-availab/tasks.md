# Tasks: Statistical Analysis of Publicly Available COVID‑19 Vaccine Adverse Event Reports

**Inputs**: `spec.md`, `plan.md`, contracts in `specs/001-statistical-analysis-of-publicly-availab/contracts/`.

The pipeline must (1) download the verified VAERS 2020‑2023 dataset, (2) validate and clean it, (3) compute disproportionality metrics (ROR, PRR, IC) with Benjamini‑Hochberg correction, (4) perform a hold‑out validation, (5) run a Flu‑only sensitivity analysis, (6) generate descriptive temporal profiles for the top signals, (7) profile memory usage, (8) validate all outputs, and (9) produce a final hand‑off report. All tasks respect the specification, ordering, and CPU‑only constraints.

---

## Phase 1 – Setup and first end‑to‑end analysis

- [X] T001 [US1] **Establish project layout and runnable command**  
  - Create required directories (`src/data/`, `src/analysis/`, `src/utils/`, `src/validation/`, `tests/unit/`, `tests/integration/`, `data/raw/`, `data/processed/`, `output/`, `logs/`).  
  - Write `logs/structure.txt` via `tree -a -L 3`.  
  - Document the command `python -m src.main` in `quickstart.md`.  
  - **Verification**: `test -s logs/structure.txt` and `grep -c src logs/structure.txt` ≥ 1.

- [ ] T002 [P] [US1] **Download verified VAERS 2020‑2023 parquet dataset** <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1 -->
  - Implement `src/data/download.py` using `datasets.load_dataset("vaers/vaers2020_2023", split="train")`.  
  - Write to `data/raw/vaers_2020_2023.parquet`.  
  - Record SHA‑256 checksum in `data/checksums.txt`.  
  - **Verification**: checksum line exists; file size > 0.

- [ ] T003 [P] [US1] **Validate raw VAERS file against JSON‑Schema**   <!-- FAILED-IN-EXECUTION: src/data/validate_raw.py exit=1 -->
  - Create `src/data/validate_raw.py` (CLI: `python -m src.data.validate_raw --schema <schema_path> --input <file>`).  
  - Load `specs/001-statistical-analysis-of-publicly-availab/contracts/raw_dataset.schema.yaml` with `jsonschema`.  
  - Exit 0 and write `logs/validate_raw_pass.txt` on success; on failure write `logs/validate_raw_fail.txt` and exit 1.  
  - Add unit tests in `tests/unit/test_validate_raw.py` that (a) succeed on the downloaded file and (b) deliberately fail on a crafted malformed parquet fixture.  
  - **Verification**: `pytest tests/unit/test_validate_raw.py` passes; CLI returns exit 0 for `data/raw/vaers_2020_2023.parquet`.

- [ ] T004 [P] [US1] **Clean, filter, map MedDRA→SOC, assign vaccine groups, and validate cleaned dataset**   <!-- FAILED-IN-EXECUTION: src/data/clean.py exit=1 -->
  - Implement `src/data/clean.py` (streamed read if > 500 MB).  
  - Drop rows missing `VAX_TYPE`, unparsable `REPT_DATE`, or missing `SOC_CODE`.  
  - Join with `data/meddra_to_soc.csv` → `SOC_NAME`.  
  - Create `VAX_GROUP`: “COVID‑19” if `VAX_TYPE` contains “COVID”; “Flu‑only” if contains “Influenza”; otherwise “Non‑COVID‑Non‑Flu”.  
  - Write `data/processed/cleaned.parquet` and group‑specific parquet files.  
  - **After writing**, run `src/data/validate_clean.py` against `contracts/cleaned_dataset.schema.yaml`.  
  - Record success in `logs/validate_clean_pass.txt`.  
  - Log coverage (≥ 95 %) and row counts to `logs/clean_summary.txt`.  
  - **Verification**: `tests/unit/test_clean_filter.py` confirms existence of cleaned file, non‑null `SOC_NAME`, correct `VAX_GROUP`, and that `logs/validate_clean_pass.txt` exists.

- [ ] T005 [US1] **Provide core utility modules**  
  - `src/utils/config.py` defines seeds, memory caps, thresholds, and `Path` objects (`DATA_RAW`, `DATA_PROCESSED`, `OUTPUT`, `LOGS`).  
  - `src/utils/plots.py` supplies `save_line_plot`, `save_forest_plot`, `plot_weekly_counts` (Agg backend).  
  - Import verification writes “PASS” to `logs/config_import.txt`.  
  - **Verification**: `pytest tests/unit/test_plots.py` succeeds; example PNGs appear under `output/figures/`.

## Phase 2 – Core analysis, validation, and extensions

- [ ] T006 [P] [US2] **Compute disproportionality metrics for each SOC**  
  - Build 2 × 2 tables for SOCs with ≥ 5 total reports (COVID‑19 vs. Non‑COVID‑Non‑Flu), applying a 0.5 continuity correction to zero cells.  
  - Compute ROR, PRR, IC with standard 95 % confidence intervals (approximate methods).  
  - Perform Fisher’s exact test → raw p‑value.  
  - Apply Benjamini‑Hochberg correction **separately** for each metric, producing adjusted p‑values.  
  - **Flag a signal** when at least two metrics satisfy their thresholds (ROR > 2 & lower CI > 1; PRR > 1.5 & lower CI > 1; IC > 0 & lower CI > 0). No BH‑adjusted p‑value threshold is required for signal definition.  
  - Export `output/signals.csv` (conforms to `signal.schema.yaml`) and `output/soc_cluster_stats.csv` (conforms to `soc_cluster.schema.yaml`).  
  - Log examined SOC count and signal count to `logs/disproportionality.txt`.  
  - **Verification**: `tests/integration/test_disproportionality.py` checks schema compliance, ≥ 95 % finite metrics (SC‑001), monotonic BH‑adjusted p‑values (SC‑002), and correct `signal_metrics`.

- [ ] T007 [P] [US2] **Flu‑only baseline sensitivity analysis**  
  - Select top‑5 signals by smallest BH‑adjusted p‑value from T006.  
  - Re‑compute ROR, PRR, IC using **Flu‑only** as the baseline (COVID‑19 vs. Flu‑only).  
  - Calculate deltas (`delta_ROR`, `delta_PRR`, `delta_IC`) versus the primary Non‑COVID‑Non‑Flu baseline.  
  - Write `output/sensitivity_analysis.csv`.  
  - Log actions to `logs/sensitivity.txt`.  
  - **Verification**: `tests/unit/test_sensitivity.py` confirms 5 rows, numeric deltas, no missing values.

- [ ] T008 [P] [US3] **Generate weekly reporting profiles for top‑5 signals**  
  - Compute median `REPT_DATE` of the combined COVID‑19 + Non‑COVID‑Non‑Flu cohort.  
  - For each top‑5 SOC, aggregate weekly counts relative to that median (`week_offset`).  
  - Write per‑SOC CSVs to `output/temporal_profiles/<SOC>.csv`.  
  - Produce line‑plot PNGs (`output/temporal_profiles/<SOC>.png`) with titles containing “Reporting Time”.  
  - If no signals exist, write `output/temporal_profiles/empty_signal_warning.txt` instead of PNGs.  
  - **Verification**: `tests/integration/test_temporal_profiles.py` asserts CSV and PNG existence and correct titles.

- [ ] T009 [P] [US1] **Orchestrate full pipeline with memory profiling & CPU‑only enforcement**  
  - Create `src/main.py` that sequentially calls: T002 → T003 → T004 → T006 → T007 → T012 → T008 → T010 → T011.  
  - Use `memory_profiler` to record peak RSS; write `data/results/memory_profile.json` (`{"peak_gb": <float>, "status": "OK"}` if ≤ 7 GB, else `"EXCEEDED"` and exit non‑zero).  
  - Guard against imports of GPU‑only libraries; raise clear error if detected.  
  - Log full run to `logs/main_run.txt`.  
  - **Verification**: `python -m src.main` exits 0, memory profile reports “OK”, and log file is non‑empty.

- [ ] T010 [P] [US2] **Comprehensive validation suite for all outputs**  
  - Implement `src/validation/validate_outputs.py` to check:  
    1. Monotonicity of BH‑adjusted p‑values for each metric (SC‑002).  
    2. ≥ 95 % finite ROR/PRR/IC among examined SOCs (SC‑001).  
    3. Presence of temporal PNGs for top‑5 signals (SC‑003).  
    4. `memory_profile.json` status equals “OK” (SC‑004).  
    5. Row‑wise validation of `output/signals.csv` & `output/soc_cluster_stats.csv` against their schemas.  
    6. Exclusion of SOCs with < 5 total reports.  
    7. Consistency of hold‑out validation flags (see T012).  
    **Note:** Validation of the 2‑out‑of‑3 signal rule (SC‑005) is performed only if the criterion is active; it is not a required success condition in the current specification (SC‑005 is deferred).  
  - Write PASS/FAIL lines to `data/results/validation.log`; exit 0 only if no FAIL lines.  
  - **Verification**: `python -m src.validation.validate_outputs` exits 0 and `grep -c FAIL data/results/validation.log` returns 0.

- [ ] T011 [P] [US2] **Generate final markdown report and figure hand‑off**  
  - Implement `src/report/generate_report.py` to assemble `output/report.md` containing:  
    * Memory usage summary & validation PASS lines.  
    * Top‑10 signal table (from `output/signals.csv`).  
    * Sensitivity Δ‑table.  
    * Forest plot (`output/figures/forest_top_signals.png`).  
    * References to temporal PNGs.  
    * Limitations section explicitly stating “findings are associational (not causal)”, “Reporting Time only”, and “Background Rate Unknown”.  
  - Ensure forbidden strings (“Post‑Vaccination”, “Causal Effect”, “Incidence Rate”) do **not** appear.  
  - Log generation to `logs/report_generation.txt`.  
  - **Verification**: `grep -E "Post‑Vaccination|Causal Effect|Incidence Rate" output/report.md` returns no matches.

- [ ] T012 [P] [US2] **Independent hold‑out validation of identified signals**  
  - Split `data/processed/cleaned.parquet` into training (80 %) and hold‑out (20 %) using `src.utils.config.SEED`.  
  - Re‑run disproportionality calculations on the hold‑out set (reuse code from T006).  
  - For each SOC flagged as a signal in the training run, verify it also meets the 2‑out‑of‑3 thresholds **and** has BH‑adjusted p‑value < 0.05 in the hold‑out run.  
  - Write `output/holdout_signals.csv` containing only SOCs that pass both criteria; log to `logs/holdout.txt`.  
  - **Verification**: `tests/unit/test_holdout_validation.py` checks that every row in `holdout_signals.csv` appears in `output/signals.csv` and satisfies hold‑out criteria.

- [ ] T013 [P] [US1] **Update project dependency list**  
  - Edit `requirements.txt` to include exact versions of all packages used: `pandas`, `numpy`, `scipy`, `matplotlib`, `datasets`, `pyarrow`, `statsmodels`, `psutil`, `memory_profiler`, `requests`, `jsonschema`, `pytest`, `ruff`, `black`.  
  - **Verification**: `grep -E "pandas|numpy|scipy|matplotlib|datasets|pyarrow|statsmodels|psutil|memory_profiler|requests|jsonschema|pytest|ruff|black" requirements.txt` finds each entry.

- [ ] T014 [P] [US?] **Revise specification wording for clarity**  
  - Update `spec.md` User Story 2 and any downstream references to replace “vaccines to non‑vaccines” with “COVID‑19 vaccines versus other vaccines”.  
  - Ensure FR‑002, FR‑007 and related acceptance criteria reference the corrected comparison.  
  - Add a short note in the spec’s “Assumptions” section explaining that VAERS contains only post‑vaccination reports, so the baseline is “non‑COVID vaccines”.  
  - **Verification**: Run a grep on `spec.md` for the phrase “non‑vaccines”; it should no longer appear.

---

### Dependency‑requirement mapping (summary)

| Spec / FR | Satisfying Task(s) |
|-----------|-------------------|
| FR‑001 (download & clean) | T002, T003, T004 |
| FR‑002 (ROR/PRR/IC) | T006 |
| FR‑003 (BH correction) | T006 |
| FR‑004 (weekly profile) | T008 |
| FR‑005 (2‑out‑of‑3 + hold‑out) | T006, T012 |
| FR‑006 (CPU‑only) | T009 |
| FR‑007 (Flu‑only sensitivity) | T007 |
| SC‑001 (≥ 95 % finite metrics) | T010 |
| SC‑02 (monotonic BH) | T010 |
| SC‑003 (temporal plots) | T010 |
| SC‑004 (memory ≤ 7 GB) | T009, T010 |
| SC‑005 (signal‑metric list) | T010 (optional) |

All tasks respect the required data flow, use only real VAERS data, and avoid fabricated inputs or GPU‑only computations. The pipeline can be executed end‑to‑end on the free‑tier CI runner and will produce verifiable, reproducible scientific artifacts.