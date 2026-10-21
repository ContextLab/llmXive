# Tasks: Linking Resting‑State fMRI Entropy to Real‑World Decision Risk‑Taking

**Inputs**: `spec.md`, `plan.md`, data‑model, contracts, original research idea, and prior verifier feedback.  
All tasks are expressed as checkbox items following the canonical format  
`- [ ] T### [P?] [USx?] description … with exact artifact paths`.  
Verification steps are listed as indented continuation lines.

---

## Phase 1 – Project scaffolding, data acquisition & quality control  

- [ ] T001 [US1] **Create the project code layout, a runnable quick‑start command, and confirm the test suite passes.**  
  - Create the source tree under `code/src/` (`data/`, `analysis/`, `stats/`, `config/`, `utils/`, `reporting/`).  
  - Add at least one real Python file in each sub‑module (e.g., `download_hcp.py`, `qc.py`, `entropy.py`, `run_pipeline.py`).  
  - Write `quickstart.md` that documents the exact command:  

    ```bash
    python -m code.src.run_pipeline --subjects 5
    ```  

    (the module path matches the file location).  
  - Ensure `requirements.txt` pins the real dependencies (including `pyentropy==0.4.*`).  
  - **Verification**: Run `pytest code/tests/` and capture the terminal log; the log must end with “=== 0 failed, 0 passed …”. Execute the quick‑start command; it must exit with status 0 and print “Pipeline completed”.  

- [ ] T002 [US1] **Implement HCP data download script with credential handling.**  
  - File: `code/src/data/download_hcp.py`.  
  - The script checks for the environment variable `HCP_TOKEN`; if missing or invalid it raises `RuntimeError` with a clear message.  
  - Deterministically select the first 200 subject IDs (sorted, seed 42).  
  - Use the verified Hugging Face dataset `jonxuxu/HCP-flat` (streaming optional) to download the minimally preprocessed 4 mm Schaefer‑400 time series **and** the embedded behavioral table containing DSRT scores, age, sex, and mean FD.  
  - Write per‑subject Parquet files to `data/raw/timeseries/subject_<ID>.parquet` and a combined behavioral table to `data/raw/dsrt_scores.parquet`.  
  - **Verification**: Run the script with `--subjects 5`; it must create exactly 5 parquet files and the combined table, and the first file must contain a `timeseries` column with > 100 time points.  

- [ ] T003 [US1] **Implement QC module that filters subjects by motion and missing DSRT, producing the required QC artifacts.**  
  - File: `code/src/data/qc.py`.  
  - Reads `data/raw/dsrt_scores.parquet`, computes mean FD per subject, and excludes any subject with `mean_fd ≥ 0.2 mm` **or** missing `dsrt_score`.  
  - Writes two artifacts:  
    1. `data/derived/clean_subjects.parquet` – rows with `status = "valid"` and a boolean `selected = True`.  
    2. `data/derived/subject_qc.csv` – full QC log containing `subject_id, age, sex, mean_fd, dsrt_score, status, reason, selected, checksum`.  
  - **Verification**: After running on the 5‑subject test set, `clean_subjects.parquet` must contain ≤ 5 rows, and `subject_qc.csv` must list every subject with an appropriate `status` and a non‑empty `checksum` column.  

---

## Phase 2 – Entropy computation (small‑scale sanity check → full‑scale run)  

- [ ] T004 [US2] **Compute multiscale sample entropy per parcel, flag invalid parcels, and store results with checksums.**  
  - File: `code/src/analysis/entropy.py`.  
  - Uses the real `pyentropy` library (`pyentropy.sample_entropy`). Implements `multiscale_entropy(ts, scales=(1,2,3,4,5), m=2, r=0.15)` that coarse‑grains the time series, computes sample entropy for each scale, and returns the average across scales.  
  - For each subject‑parcel pair writes a row to `data/derived/entropy_matrix.parquet` adhering to `entropy.schema.yaml` (columns: `subject_id`, `parcel_id`, `entropy`, `checksum`).  
  - Parcels with fewer than 120 time points are written to `data/derived/invalid_parcels.csv` and their entropy set to `NaN`.  
  - **Verification**: After processing the 5‑subject test set, the parquet file must have shape (≤ 5 × 400, 4) and contain at least one `NaN` entry corresponding to a deliberately short series (unit test).  

- [ ] T005 [US1,US2] **Run a small end‑to‑end pipeline (5 subjects) to validate the full data flow.**  
  - Entry point: `code/src/run_pipeline.py`.  
  - Command:  

    ```bash
    python -m code.src.run_pipeline --subjects 5
    ```  

  - Executes steps 1–4 sequentially, writing:  
    - `results/entropy_matrix.parquet` (same schema as above)  
    - `results/covariates.parquet` (subject_id, age, sex, mean_fd, dsrt_score, checksum)  
  - Batches processing ≤ 50 parcels to keep peak RAM < 4 GB (SC‑002).  
  - **Verification**: After the run, check that the two result files exist, have the correct column sets, and that the pipeline log reports “Completed 5 subjects, 400 parcels”.  

- [ ] T006 [US2] **Run the full‑cohort entropy computation (200 subjects) and record runtime/memory metrics.**  
  - Re‑invoke the pipeline with `--subjects 200`.  
  - Writes the same two result files as T005 but for the full cohort.  
  - Additionally creates `results/pipeline_metrics.json` containing `runtime_seconds` and `peak_memory_gb`.  
  - **Verification**: The JSON file must be present, and `runtime_seconds` ≤ 5400 (≤ 1.5 h) and `peak_memory_gb` ≤ 7 GB (SC‑001, SC‑002).  

---

## Phase 3 – Statistical modeling, permutation correction & power analysis  

- [ ] T007 [US3] **Fit mass‑univariate mixed‑effects model per parcel and compute VIF diagnostics.**  
  - File: `code/src/stats/model.py`.  
  - Loads `results/entropy_matrix.parquet` and `results/covariates.parquet`.  
  - Computes VIF for covariates `age`, `sex`, `mean_fd`; if any VIF ≥ 5, the covariate with the highest VIF is dropped and the VIF table is updated (recorded in `results/vif_report.csv`).  
  - Fits a `statsmodels.MixedLM` per parcel with formula  

    ```
    DSRT ~ Entropy + Age + Sex + MeanFD
    ```

    and a random intercept for `Subject`.  
  - Writes `results/model_coefficients.csv` conforming to `stat_results.schema.yaml` (including `checksum`).  
  - **Verification**: The CSV must have exactly 400 rows, a non‑null `vif` column, and at least one parcel where the model converged (no NaNs in `beta_entropy`).  

- [ ] T008 [US3] **Perform Freedman‑Lane max‑t permutation testing (1 000 shuffles) with timeout handling.**  
  - File: `code/src/stats/permutation.py`.  
  - Uses `joblib` to parallelize across available CPU cores.  
  - For each permutation, shuffles the DSRT scores, refits the mixed model, records the t‑statistic for the entropy predictor, and stores the maximum absolute t across parcels.  
  - Stops early if the wall‑clock time reaches 3 h, raising a clear `TimeoutError`.  
  - Saves `results/max_t_distribution.npy` and `results/corrected_pvalues.csv` (parcel_id, p_raw, p_fwe, significant).  
  - **Verification**: After a successful run, the `max_t_distribution.npy` array length equals 1 000 and `corrected_pvalues.csv` contains the `significant` boolean column.  

- [ ] T009 [US3] **Compute a priori power analysis and verify collinearity constraints.**  
  - File: `code/src/stats/power.py`.  
  - Calculates analytical power for an OLS‑equivalent F‑test using `statsmodels.stats.power.FTestPower` with effect size f² = 0.05 (≈ d = 0.3), α = 0.05, and N equal to the number of subjects in the QC‑passed cohort.  
  - Writes `results/power_analysis.json` containing `power`, `effect_size_f2`, `n_subjects`, `alpha`, and `underpowered` (true if power < 0.80).  
  - **Verification**: The JSON file must be syntactically valid and the `underpowered` flag must correctly reflect the computed power (SC‑006).  

---

## Phase 4 – Sensitivity sweep & result visualisation  

- [ ] T010 [US3] **Run a full sensitivity analysis over entropy tolerance `r` and embedding dimension `m`.**  
  - Driver: `code/src/stats/sensitivity_driver.py`.  
  - Sweeps `r ∈ {0.1, 0.15, 0.2}` and `m ∈ {2, 3, 4, 5}` (total 12 combos). For each combo it recomputes entropy (reuse `entropy.py`), refits the mixed model (reuse `model.py`), and performs 1 000 permutations (reuse `permutation.py`).  
  - Stores a summary table `data/derived/sensitivity_records.parquet` with columns `r`, `m`, `num_significant_parcels`, `max_beta_entropy`, `mean_p_fwe`.  
  - **Verification**: The parquet file must contain exactly 12 rows and the `num_significant_parcels` column must be derived from real permutation results (non‑negative integer).  

- [ ] T011 [US3] **Generate all figures and the final PDF report.**  
  - Figures module: `code/src/reporting/figures.py` creates:  
    1. `results/significant_map.nii.gz` – parcel‑wise β map (NIfTI) using Nilearn with the Schaefer‑400 atlas.  
    2. `figures/pvalue_histogram.png` – histogram of `p_fwe`.  
    3. `figures/sensitivity_heatmap.png` – heatmap of `num_significant_parcels` across the (r, m) grid.  
  - Report generation: `code/src/reporting/generate_report.py` converts `reports/results_summary.md` to PDF via Pandoc, producing `reports/link_entropy_risk.pdf`.  
  - The markdown report includes cohort size, exclusion stats, entropy parameters, model specification, VIF table, permutation count, power analysis (including under‑powered flag), and the sensitivity table.  
  - **Verification**: All three figure files must exist, be non‑empty (> 5 KB), and the PDF must be > 10 KB. A checksum of each figure and the PDF is recorded in `results/checksums.txt`.  

---

## Phase 5 – Reproducibility hand‑off  

- [ ] T012 [US1,US2,US3] **Re‑run the documented quick‑start workflow end‑to‑end and confirm deterministic reproducibility.**  
  - Execute the command from `quickstart.md` (`python -m code.src.run_pipeline --subjects 200`).  
  - After completion, compute SHA‑256 checksums for all files under `data/derived/`, `results/`, and `figures/`; write them to `results/checksums.txt`.  
  - Verify that the newly generated checksums match those recorded in the previous run (i.e., files are byte‑identical).  
  - **Verification**: A diff of the checksum files must be empty, and the CI log should state “Re‑run reproducibility check passed”.  

- [ ] T013 [US1] **Create the paper‑stage handoff document linking all deliverables.**  
  - File: `reports/paper_handoff.md`.  
  - Lists:  
    - PDF report path (`reports/link_entropy_risk.pdf`)  
    - NIfTI map (`results/significant_map.nii.gz`)  
    - All CSV/Parquet result files with their checksums  
    - Statement of whether the study is under‑powered (from `power_analysis.json`)  
    - Any robustness notes (e.g., low‑motion subset analysis)  
  - No script writes to `state/`; the handoff is pure documentation.  
  - **Verification**: The markdown file must be present, contain a table with each artifact and its checksum, and pass a simple regex check for a 64‑character hex string per line.  

---

### Dependency mapping (FR → Task)

| FR ID | Covered by |
|------|-------------|
| FR‑001 | T002 |
| FR‑002 | T003 |
| FR‑003 | T004 |
| FR‑004 | T007 |
| FR‑005 | T008 |
| FR‑006 | T011 (report framing) |
| FR‑007 | All tasks run on CPU‑only (explicitly noted) |
| FR‑008 | T010 (sensitivity sweep) |
| FR‑009 (checksum) | T001, T013, T016 (merged into T013) |

All success criteria (SC‑001 – SC‑006) are exercised by the verification steps embedded in the tasks above.
