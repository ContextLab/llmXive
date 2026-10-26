# Tasks: Linking Resting‑State fMRI Entropy to Real‑World Decision Risk‑Taking  

**Inputs**: `spec.md`, `plan.md`, data‑model, contracts, original research idea, and any prior verifier feedback.  
All tasks follow the canonical checklist format `- [ ] T### [USx?] description … with file path`.  
Verification steps are given as indented continuation lines.  
The project layout follows the platform convention (`code/`, `data/`, `results/`, `figures/`, `reports/`).  
All scripts run on CPU‑only GitHub‑Actions runners and use only real, publicly‑available data.

---

## Phase 0 – Power Planning (pre‑modeling)

- [ ] T014 [US0] Perform an a‑priori power analysis before any statistical modeling. `code/src/stats/power_pre.py`.
  - Compute analytical power for a mixed‑effects F‑test using `statsmodels.stats.power.FTestPower` with effect size f² = 0.05, α = 0.05, and N = anticipated QC‑passed subjects (default 200).  
  - Write `results/power_analysis_pre.json` containing `power`, `effect_size_f2`, `n_subjects`, `alpha`, and `underpowered` (true if power < 0.80).  
  - Verification: JSON file parses without error and `underpowered` flag correctly reflects the computed power (satisfying SC‑006).

---

## Phase 1 – Project scaffolding, data acquisition & quality control  

- [ ] T001 Create the project code layout, a runnable quick‑start command, and a passing test suite. `code/src/run_pipeline.py`, `quickstart.md`, `code/tests/`.
  - Verify that the directory tree `code/src/` contains `__init__.py` in each sub‑package (`data/`, `analysis/`, `stats/`, `reporting/`, `utils/`).  
  - Verify `quickstart.md` documents the command `python -m code.src.run_pipeline --subjects 5` and that running it with `--dry‑run` exits with code 0 and prints “Pipeline completed (dry‑run)”.  
  - Verify `pytest code/tests/` finishes with “0 failed, X passed”.

- [ ] T002 Implement a robust HCP download script with credential handling. `code/src/data/download_hcp.py`.
  - The script checks for the environment variable `HCP_TOKEN`; if missing or invalid it raises `RuntimeError` with a clear message.  
  - It deterministically selects the first 200 subject IDs (sorted, seed 42).  
  - It uses the verified Hugging Face dataset `hcp` (accessed via `datasets.load_dataset("hcp", "rest", split="train", streaming=False)`) to download the minimally preprocessed 4 mm Schaefer‑400 time series and the accompanying behavioral table containing DSRT scores, age, sex, and mean FD.  
  - For each subject it writes a Parquet file `data/raw/timeseries/subject_<ID>.parquet` and a combined behavioral table `data/raw/dsrt_scores.parquet`.  
  - Verification: Running `python -m code.src.data.download_hcp --subjects 5` creates exactly 5 parquet files in `data/raw/timeseries/` and a non‑empty `data/raw/dsrt_scores.parquet` that contains the columns `subject_id`, `dsrt_score`, `age`, `sex`, `mean_fd`.

- [ ] T003 Implement QC that filters subjects by motion and missing DSRT, producing the required QC artifacts. `code/src/data/qc.py`.
  - The script reads `data/raw/dsrt_scores.parquet`, computes mean FD per subject, and excludes any subject with `mean_fd ≥ 0.2 mm` **or** a missing `dsrt_score`.  
  - It writes two artifacts:  
    1. `data/derived/clean_subjects.parquet` – rows with `status = "valid"` and `selected = True`, plus a SHA‑256 `checksum` column.  
    2. `data/derived/subject_qc.csv` – full QC log containing `subject_id, age, sex, mean_fd, dsrt_score, status, reason, selected, checksum`.  
  - Verification: After running on the 5‑subject test set, `clean_subjects.parquet` contains ≤ 5 rows, each with a non‑empty `checksum`; `subject_qc.csv` lists every subject, correctly flags excluded subjects, includes a valid SHA‑256 checksum for each row, **and** passes schema validation against `contracts/subject_qc.schema.yaml` (e.g., `python -m utils.validate_schema data/derived/subject_qc.csv contracts/subject_qc.schema.yaml`).

- [ ] T004 Compute multiscale sample entropy per parcel, flag invalid parcels, and store results with checksums and metadata. `code/src/analysis/entropy.py`.
  - Implements `multiscale_entropy(ts, scales=(1,2,3,4,5), m=2, r=0.15)` using `pyentropy.sample_entropy`.  
  - For each subject‑parcel pair it writes a row to `data/derived/entropy_matrix.parquet` adhering to `contracts/entropy.schema.yaml` (columns: `subject_id`, `parcel_id`, `entropy`, `checksum`).  
  - Creates `data/derived/entropy_metadata.json` containing the required `metadata` fields (`n_subjects`, `n_parcels`, `scales`, `r_values`, `seed`, `includes_noise_variance`, `resampling_correlation`, `ks_pvalue`) to satisfy `contracts/entropy_schema.schema.yaml`.  
  - Parcels with fewer than 120 time points are recorded in `data/derived/invalid_parcels.csv` (columns `subject_id`, `parcel_id`, `reason`) and their entropy set to `NaN`.  
  - Verification: After processing the 5‑subject test set, `entropy_matrix.parquet` has shape ≤ 5 × 400 with a `checksum` column, `entropy_metadata.json` exists and validates against `contracts/entropy_schema.schema.yaml`, and `invalid_parcels.csv` exists with at least one row.

- [ ] T005 Run a small end‑to‑end pipeline (5 subjects) to validate the full data flow. `code/src/run_pipeline.py`.
  - Executes the sequence T002 → T003 → T004, then copies the derived artifacts to the `results/` directory:  
    1. `results/entropy_matrix.parquet` (copy of `data/derived/entropy_matrix.parquet`).  
    2. `results/covariates.parquet` containing `subject_id, age, sex, mean_fd, dsrt_score, checksum`.  
  - Batches processing ≤ 50 parcels at a time to keep peak RAM < 4 GB (SC‑002).  
  - Verification: After the run, both result files exist, have the correct columns, and the pipeline log ends with “Completed 5 subjects, 400 parcels”.

---

## Phase 2 – Full‑cohort entropy computation & resource monitoring  

- [ ] T006 Run the full‑cohort entropy computation (200 subjects) and record runtime/memory metrics. `code/src/run_pipeline.py --subjects 200`.
  - Writes the same two result files as T005 but for the full cohort.  
  - Additionally creates `results/pipeline_metrics.json` with keys `runtime_seconds` and `peak_memory_gb`.  
  - Verification: `pipeline_metrics.json` exists and reports `runtime_seconds ≤ 5400` (≤ 1.5 h) and `peak_memory_gb ≤ 7`.

---

## Phase 3 – Statistical modeling, permutation correction & power analysis  

- [ ] T007 Fit a mass‑univariate mixed‑effects model per parcel and compute VIF diagnostics. `code/src/stats/model.py`.
  - Loads `results/entropy_matrix.parquet` and `results/covariates.parquet`.  
  - Computes VIF for covariates `age`, `sex`, `mean_fd`; **does not drop** any covariate even if VIF ≥ 5, but records all VIF values in `results/vif_report.csv` and issues a warning if any exceed 5.  
  - Fits a mixed‑effects model per parcel using `statsmodels.MixedLM` with formula `DSRT ~ Entropy + Age + Sex + MeanFD` and a random intercept for Subject `(1|Subject)`.  
  - Writes `results/model_coefficients.csv` conforming to `contracts/stat_results.schema.yaml` (including `checksum`).  
  - Verification: The CSV contains exactly 400 rows, a populated `vif` column, a non‑null `checksum` column, at least one parcel where `beta_entropy` is not `NaN`, **and** passes schema validation against `contracts/statistical_result_schema.schema.yaml`.

- [ ] T008 Perform Freedman‑Lane max‑t permutation testing (1 000 shuffles) with timeout handling. `code/src/stats/permutation.py`.
  - Uses `joblib.Parallel` to parallelize across available CPU cores.  
  - For each permutation it shuffles the DSRT scores, refits the mixed‑effects model for all parcels, records the t‑statistic for the entropy predictor, and stores the maximum absolute t across parcels.  
  - Stops early if wall‑clock time reaches 3 h, raising a clear `TimeoutError`.  
  - Saves `results/max_t_distribution.npy` and `results/corrected_pvalues.csv` (columns: `parcel_id, p_raw, p_fwe, significant`).  
  - Verification: After a successful run, `max_t_distribution.npy` length equals 1 000 and `corrected_pvalues.csv` contains the boolean `significant` column.

- [ ] T009 Compute a post‑hoc power analysis based on the actual sample size. `code/src/stats/power_post.py`.
  - Calculates analytical power for an OLS‑equivalent F‑test using `statsmodels.stats.power.FTestPower` with effect size f² = 0.05, α = 0.05, and N equal to the number of QC‑passed subjects.  
  - Writes `results/power_analysis.json` containing `power`, `effect_size_f2`, `n_subjects`, `alpha`, and `underpowered` (true if power < 0.80).  
  - Verification: The JSON file is syntactically valid and the `underpowered` flag correctly reflects the computed power (satisfying SC‑006).

---

## Phase 4 – Sensitivity sweep & result visualisation  

- [ ] T010 Run a full sensitivity analysis over entropy tolerance `r` and embedding dimension `m`. `code/src/stats/sensitivity_driver.py`.
  - Sweeps `r ∈ {0.1, 0.15, 0.2}` and `m ∈ {2, 3, 4, 5}` (12 total combos). For each combo it:  
    1. Re‑computes entropy (re‑uses `entropy.py`).  
    2. Re‑fits the mixed‑effects model (re‑uses `model.py`).  
    3. Performs 1 000 permutations (re‑uses `permutation.py`).  
  - Stores a summary table `data/derived/sensitivity_records.parquet` with columns `r`, `m`, `num_significant_parcels`, `max_beta_entropy`, `mean_p_fwe`.  
  - Verification: The parquet file contains exactly 12 rows; each `num_significant_parcels` is a non‑negative integer derived from real permutation results.

- [ ] T011 Generate all figures and the final PDF report. `code/src/reporting/figures.py` & `code/src/reporting/generate_report.py`.
  - Figures created:  
    1. `results/significant_map.nii.gz` – parcel‑wise β map (NIfTI) using Nilearn with the Schaefer‑400 atlas.  
    2. `figures/pvalue_histogram.png` – histogram of `p_fwe`.  
    3. `figures/sensitivity_heatmap.png` – heatmap of `num_significant_parcels` across the (r, m) grid.  
  - `generate_report.py` converts `reports/results_summary.md` to PDF via Pandoc, producing `reports/link_entropy_risk.pdf`.  
  - The markdown report **explicitly includes** the sentence: “All statistical findings are reported as associations and do not imply causation.” (fulfilling FR‑006).  
  - Verification: All three figure files exist and are > 5 KB each; the PDF is > 10 KB; the PDF text search confirms presence of the associational disclaimer; SHA‑256 checksums of each figure and the PDF are recorded in `results/checksums.txt`.

- [ ] T015 Perform a low‑motion robustness re‑analysis (mean FD < 0.2 mm). `code/src/robustness/low_motion.py`.
  - Subsets `clean_subjects.parquet` to subjects with `mean_fd < 0.2 mm`.  
  - Re‑runs entropy computation, modeling, permutation testing, and reporting **only on this subset**.  
  - Writes subset artifacts prefixed with `low_motion_` (e.g., `results/low_motion_model_coefficients.csv`).  
  - Generates a supplemental PDF `reports/low_motion_robustness.pdf` that mirrors the main report and includes a statement that results are consistent (or not) with the full‑sample analysis.  
  - Verification: All subset files exist, the PDF contains the associational disclaimer, and a comparison table of significant parcel counts between full and low‑motion analyses is present.

- [ ] T016 Create the final hand‑off document linking all deliverables. `reports/paper_handoff.md`.
  - Lists:  
    - PDF report path (`reports/link_entropy_risk.pdf`) and robustness PDF (`reports/low_motion_robustness.pdf`).  
    - NIfTI map (`results/significant_map.nii.gz`).  
    - All CSV/Parquet result files with their checksums (referencing `results/checksums.txt`).  
    - Power‑analysis outcomes (`results/power_analysis_pre.json` and `results/power_analysis.json`).  
    - Sensitivity analysis table summary.  
  - Verification: The markdown file exists, contains a table where each artifact has a 64‑character hex SHA‑256 string, and a regex check for a valid SHA‑256 passes.

---

## Dependency mapping (FR → Task)

| FR ID | Covered by |
|------|-------------|
| FR‑001 | T002 |
| FR‑002 | T003 |
| FR‑003 | T004 |
| FR‑004 | T007 |
| FR‑005 | T008 |
| FR‑006 | T011, T016 |
| FR‑007 | All tasks (CPU‑only) |
| FR‑008 | T010 |
| FR‑010 (checksum handling) | Implemented throughout T001‑T016 via SHA‑256 columns (no separate FR needed) |
| FR‑011 (power analysis pre‑modeling) | T014 |
| FR‑012 (low‑motion robustness) | T015 |
| FR‑013 (associational framing) | T011, T016 |

All success criteria (SC‑001 – SC‑006) are exercised by the verification steps embedded in the tasks above.  

---

