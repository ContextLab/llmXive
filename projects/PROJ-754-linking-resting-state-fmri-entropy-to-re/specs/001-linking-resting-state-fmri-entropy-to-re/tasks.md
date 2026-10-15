# Tasks: Linking Resting‑State fMRI Entropy to Real‑World Decision Risk‑Taking

**Inputs**: Active `spec.md`, `plan.md`, `data-model.md`, contracts/, original research idea, and prior verifier feedback (T002 rejected for missing directory evidence).

## Phase 1: Setup and first end‑to‑end analysis

- [ ] T001 [US1] Establish the code layout and validate input provenance.  
  Create the source tree `code/src/data/`, `code/src/analysis/`, `code/src/stats/`, `code/src/config/`, `code/src/utils/`, `code/src/entities/`, `code/src/reporting/`, `code/tests/unit/`, `code/tests/integration/` with module stubs so every directory contains at least one real Python file. Reuse the existing pinned `requirements.txt` and `pyproject.toml`. Document a runnable end‑to‑end command in `quickstart.md`. Validation: `pytest code/tests/` passes; `quickstart.md` names the exact command; all listed directories exist with at least one file.

- [ ] T002 [US1] Implement the HCP data acquisition module in `code/src/data/download_hcp.py` (FR‑001).   <!-- FAILED-IN-EXECUTION: code/src/data/download_hcp.py exit=1 -->
  Deterministically select subjects: sort all available HCP subject IDs, seed 42, take the first 200. Download minimally preprocessed 4 mm Schaefer‑400 time series and the HCP behavioral table containing DSRT scores, age, sex, and mean FD. Write per‑subject parquet files under `data/raw/timeseries/` and a combined behavioral parquet `data/raw/dsrt_scores.parquet`. The script must raise a clear error if `HCP_TOKEN` is missing or invalid; no synthetic fallback. Validation: a 5‑subject smoke run completes, first subject parquet has shape (timepoints × 400) with real IDs.

- [X] T003 [US1] Implement data validation and motion QC in `code/src/data/qc.py` (FR‑002, edge cases).  
  Verify required columns; exclude subjects with mean FD ≥ 0.2 mm and subjects missing DSRT, logging exclusion counts and reasons. Output `data/derived/clean_subjects.parquet` (status = "valid") and `data/derived/subject_qc.csv`. Migrate existing motion‑exclusion unit test to `code/tests/unit/test_qc.py` and extend for missing DSRT. Validation: pytest passes; no excluded subject appears in `clean_subjects.parquet`.

- [X] T004 [US2] Implement multiscale sample entropy in `code/src/analysis/entropy.py` (FR‑003).  
  Use the **pyentropy** library (`pyentropy==0.4.*`) and its `sample_entropy` function. Function signature: `multiscale_entropy(ts, scales=(1,2,3,4,5), m=2, r=0.15)`. Compute sample entropy for each coarse‑grained scale, average across scales 1‑5 to a single value per parcel. Flag parcels with insufficient timepoints (write IDs to `data/derived/invalid_parcels.csv`) and set their entropy to NaN. Include unit tests in `code/tests/unit/test_entropy.py` using deterministic synthetic series (sine, noise). Validation: pytest passes; low‑complexity series yields lower entropy than high‑complexity series.

- [ ] T005 [US1,US2] Connect the end‑to‑end pipeline and run a small real case.   <!-- FAILED-IN-EXECUTION: code/src/run_pipeline.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/src/run_pipeline.py exit=1 -->
  Entry point `code/src/run_pipeline.py --subjects 5` executes download → QC → entropy → writes:  
  - `results/entropy_matrix.parquet` (subjects × parcels, conforms to `entropy.schema.yaml` with metadata fields `n_subjects`, `n_parcels`, `scales`, `r_values`, `seed`).  
  - `results/covariates.parquet` (subject_id, age, sex, mean_fd, dsrt_score).  
  Process parcels in batches ≤ 50 to keep peak RAM < 4 GB (SC‑002). Validation: matrix shape (5, 400), real subject IDs, finite entropy for ≥95 % parcels; command completes on real HCP data.

## Phase 2: Complete the study and validate its evidence

- [ ] T006 [US2] Run the full‑cohort entropy computation (FR‑003).  
  Execute `code/src/run_pipeline.py --subjects 200` (or the full QC‑passed cohort). Produce `results/entropy_matrix.parquet` and `results/covariates.parquet`. Record runtime and peak memory in `results/pipeline_metrics.json` (SC‑001, SC‑002). Validation: rows match the valid cohort from T003; any invalid parcels are NaN and listed in `data/derived/invalid_parcels.csv`.

- [ ] T007 [US3] Implement covariate diagnostics and the mass‑univariate mixed model (FR‑004, SC‑005).  
  Compute VIF for age, sex, mean FD (`statsmodels.stats.outliers_influence.variance_inflation_factor`). Flag VIF ≥ 5. Fit per‑parcel MixedLM: `DSRT ~ Entropy + Age + Sex + MeanFD` with a random intercept for Subject (`statsmodels.MixedLM`). **No OLS fallback**; if a parcel fails to converge, log the failure and continue (the row will contain NaNs). Output `results/model_coefficients.csv` conforming to `stat_results.schema.yaml` (parcel_id, beta_entropy, se_entropy, t_entropy, p_raw, p_fwe, significant, checksum). Unit tests in `code/tests/unit/test_stats.py` verify coefficient recovery on a synthetic design. Validation: pytest passes; 400 rows present; VIF column included.

- [ ] T008 [US3] Implement Freedman–Lane max‑t permutation FWE correction (FR‑005).  
  Shuffle DSRT residuals, recompute per‑parcel t‑statistics, record the max‑t across parcels per permutation. Start with 500 permutations and increase by 500 until either 10 000 permutations or the 95 % CI width on each p_fwe ≤ 0.02, whichever comes first. Abort with a clear timeout error before the 6 h CI limit (SC‑001). Seed 42 pinned. Outputs: `results/max_t_distribution.npy` and `results/corrected_pvalues.csv` (parcel_id, p_raw, p_fwe, significant). Unit test `code/tests/unit/test_permutations.py` checks uniform null and max‑t ≥ any single t. Validation: pytest passes; 400 rows in corrected_pvalues.csv.

- [ ] T009 [US3] Implement post‑hoc power analysis (SC‑006).  
  Compute F‑test power for effect size d = 0.3 at the achieved N, α = 0.05. Write `results/power_metrics.json` with fields `power`, `effect_size_d`, `n_subjects`, `alpha`, `underpowered` (true if power < 0.80). Validation: JSON exists and flag matches computed power.

- [ ] T010 [US3] Run the primary analysis on the low‑motion valid cohort (FR‑002, FR‑006).  
  Execute T007‑T009 on the QC‑passed cohort (already low‑motion). Produce final `results/model_coefficients.csv`, `results/corrected_pvalues.csv`, and `results/power_metrics.json`. A null result (zero significant parcels) is acceptable and must be reported. Validation: files exist, row counts 400, all numbers traceable to real entropy matrix from T006.

- [ ] T011 [US3] Run the full sensitivity analysis (FR‑008, SC‑004).  
  Driver `code/src/stats/sensitivity_driver.py` sweeps:  
    - Entropy tolerance `r` ∈ {0.1, 0.15, 0.2}  
    - Embedding dimension `m` ∈ {2, 3, 4} (scale parameter)  
  For each (r, m) combo, recompute entropy from the raw time series, then refit the MixedLM (same specification as T007) with **1000** Freedman–Lane permutations per combo (time‑budgeted). Output `results/sensitivity_grid.csv` with columns `r`, `m`, `num_significant_parcels`, `max_beta`, `mean_p_value`. Validation: 12 rows (3 r × 4 m); all counts derived from real recomputation.

- [ ] T012 [US3] Generate figures and maps (SC‑003).  
  `code/src/reporting/figures.py` creates:  
    - Parcel‑wise β and –log10(p_fwe) brain map `results/significant_map.nii.gz` (nilearn, Schaefer‑400).  
    - Histogram of p_fwe `figures/pvalue_histogram.png`.  
    - Sensitivity heatmap `figures/sensitivity_heatmap.png`.  
  All figures are regenerated directly from CSV/NIfTI outputs; no manual editing. Validation: files exist and re‑running the script reproduces identical images.

- [ ] T013 [US3] Produce the final PDF report (SC‑003).  
  Convert `reports/results_summary.md` to PDF via pandoc (`pandoc reports/results_summary.md -o reports/link_entropy_risk.pdf`). The markdown report includes cohort size, exclusion stats, entropy parameters, mixed‑effects model specification (including any convergence failures), permutation count, VIF values, power analysis (with underpowered flag), sensitivity table, and explicit associational framing per FR‑006. Validation: PDF generated, size > 10 KB, all numbers cross‑checked against result artifacts.

- [ ] T014 [US1,US2,US3] Re‑run the documented workflow and create the paper‑stage handoff.  
  Re‑execute the quickstart command end‑to‑end, confirm `pytest code/tests/` passes and that all artifacts under `results/`, `figures/`, `reports/` regenerate identically (seed‑pinned). Write `reports/paper_handoff.md` listing required sections, artifact paths (including the newly created PDF), and the under‑powered flag requirement. No script writes to `state/`; artifact hashing is performed automatically by the platform. Validation: clean re‑run yields byte‑identical CSV/NIfTI/PDF files; handoff lists all deliverables.

- [ ] T015 [US3] Robustness re‑analysis on an even stricter low‑motion subset (Constitution VI).  
  Apply a tighter motion threshold (FD < 0.1 mm) to the QC‑passed cohort, generate a new covariate table `results/low_motion_covariates.parquet`, recompute entropy (reuse T004), and refit the MixedLM (reuse T007) on this subset. Produce `results/robust_model_coefficients.csv` and `results/robust_corrected_pvalues.csv`. Compare results to primary analysis and record any discrepancies in `reports/robustness_note.md`. Validation: files exist; differences logged.

- [ ] T016 [US1,US2] Data‑hygiene checksum generation.  
  After each major pipeline stage, compute SHA‑256 checksums for all files under `data/raw/` and `data/derived/`, write a consolidated list `results/checksums.txt`. This satisfies Constitution III. Validation: file present; each line contains `<checksum>  <relative‑path>`.
