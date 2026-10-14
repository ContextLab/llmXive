# Tasks: Investigating the Relationship Between Brain Network Dynamics and Creative Problem Solving

**Input**: Design documents from `/specs/518-brain-dynamics-creativity/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests are MANDATORY where defined by spec acceptance criteria.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

Paths are relative to the project directory (`projects/PROJ-518-investigating-the-relationship-between-b/`). Source lives in `code/`, tests in `code/tests/` (per plan structure), results in `data/interim/` and `docs/outputs/`.

---

## Completed work (preserved — verified by prior review receipts)

- [ ] T002 Pinned dependencies in `requirements.txt` (nilearn, networkx, scikit-learn, numpy, pandas, matplotlib, scipy, brainconn, statsmodels).
- [ ] T005 `code/config.py` with `WINDOW_SIZES = [20,30,40]`, `STEP = 5`, `FWE_METHOD`, and `validate_fwe_config()`.
- [ ] T006 `code/utils/logging.py` `log_exclusion(reason, subject_id)` writing CSV rows to `data_exclusion_log.txt` with standardized reason codes (`MISSING_SCAN`, `MISSING_SCORE`, `HIGH_MOTION`).
- [X] T018/T019/T020b Subject filtering (missing scans, missing scores, motion > 0.5 mm FD in > 20 % volumes) with standardized exclusion logging.
- [ ] T033–T036.3 [US4] CAQ availability validation (`validate_caq_availability`), `run_validation()` in `code/main.py`, `DATA_MISSING_CREATIVITY` error handling with `sys.exit(1)`, and contract tests `tests/contract/test_loader.py`.
- [ ] T012 `fetch_hcp_data(subject_id)` fetching raw fMRI + behavioral JSON from OpenNeuro (HCP S1200) into `data/raw/hcp_{subject_id}/`.
- [ ] T013 `preprocess_fmri` in `code/data/preprocess.py` (motion correction, normalization, band‑pass 0.01–0.1 Hz) writing `data/processed/fmri_clean/{subject_id}.nii.gz`.
- [X] T014/T014.0–T014.6 Sliding‑window connectivity, per‑participant static connectivity strength, covariate construction, and alignment validation in `code/analysis/connectivity.py`.
- [X] T015/T016 Louvain community detection (γ = 1.0) and whole‑brain flexibility metric in `code/analysis/dynamics.py`.
- [X] T043/T051/T051b/T017/T017.1/T017.2 OLS regression (`creativity ~ excess_flexibility + age + sex + education + static_strength`), static‑only baseline, ΔR² computation and 4‑decimal formatting, `data/interim/results.csv` with `global_empirical_p_value` from the permutation test.
- [ ] T022 `plot_flexibility_vs_creativity` with regression line, 95 % confidence band, NaN handling, saved as `docs/outputs/flexibility_vs_creativity.png`.
- [X] T057/T058 Image compression (≤ 5 MB, `RuntimeError` on failure) and NaN‑robust plotting.
- [ ] T027 Vectorized permutation test (10,000 shuffles, seed 42) returning `empirical_p_value`, `distribution_of_max_stats`, `shuffle_correlations`.
- [X] T046/T046.1 Sensitivity sweep over window lengths {20, 30, 40} with per‑window connectivity recomputation and `construct_sensitivity_df`.
- [X] T045/T045.1–T045.3 ROI‑wise correlations and FWE correction (max‑T / Bonferroni).
- [X] T060/T060.1 Runtime profiling on a real 10‑subject subset, scaling projection, and `docs/outputs/profiling_report.txt` (memory < 7 GB, runtime < 6 h).
- [ ] T041 Dependency security check on `requirements.txt`.

**Note (T007 correction)**: The earlier `code/utils/versioning.py` task that wrote artifact hashes into `state/projects/...yaml` has been removed; hashing now only updates `data/checksums.json`.

## Phase 1: Repair rejected artifacts and reach a real end‑to‑end result

- [ ] T101 US2 **Repair `plot_residuals` and generate the missing diagnostic plots.**  
  *Description*: Update `code/viz/plots.py::plot_residuals` to compute residuals from the OLS fit (`model.predict(X)`) and plot residuals‑vs‑fitted and QQ‑plot.  
  *Deliverables*: `docs/outputs/model_residuals.png` and `docs/outputs/model_qq.png` (≤ 5 MB, compressed).  
  *Verification*: `pytest code/tests/unit/test_plots.py` asserting both files exist and are non‑empty after execution on the fitted model from T103.  
  *Dependency*: **depends_on: T103** (must run after the full regression model is fitted).

- [ ] T102 US3 **Produce the real permutation and sensitivity result tables.**  
  *Description*: Run the permutation engine (T027) and the sensitivity sweep (T046/T046.1) on the filtered dataset.  
  *Deliverables*:  
    1. `data/interim/permutation_results.csv` – single‑row file containing the empirical two‑tailed p‑value (`empirical_p_value`).  
    2. `data/interim/sensitivity_summary.csv` – columns: `window_length`, `correlation_coefficient`, `p_value`, `permutation_p_value`, `n_samples`.  
    3. `data/interim/permutation_shuffles.csv` – optional detailed per‑shuffle `shuffle_id` and `correlation` (for debugging).  
  *Verification*: `pytest code/tests/unit/test_analysis.py::test_sensitivity_csv_schema` checking presence and non‑null values for all required columns; `pytest code/tests/unit/test_permutation.py::test_empirical_p_value_present`.

- [ ] T103 US1 **Run the full documented pipeline end‑to‑end.**  
  *Description*: Execute `code/main.py` from validation through preprocessing, flexibility computation, regression, permutation, sensitivity, and visualisation.  
  *Deliverables*:  
    - `data/interim/results.csv` (renamed from previous `regression_summary.csv`) containing: `model_id`, `coefficient_flexibility`, `p_value_flexibility`, `r_squared`, `delta_r_squared`, `permutation_p_value`, `ci_lower`, `ci_upper`, `window_length`, `n_samples`.  
    - Pearson correlation `r` and two‑tailed p‑value recorded in the same CSV.  
  *Verification*: `pytest code/tests/integration/test_regression_summary.py` validates CSV schema (including `ci_lower`/`ci_upper`), checks numeric precision (4 decimal places for ΔR²), and asserts presence of confidence‑interval fields.  
  *Dependency*: **depends_on: T102** (must run after permutation and sensitivity results are available).

- [ ] T111 **Generate phase‑randomized null model for flexibility.**  
  *Description*: In `code/analysis/dynamics.py`, implement a phase‑randomization of each subject’s time‑series, recompute community assignments, and calculate `null_flexibility_mean`. Store `null_flexibility_mean` and `excess_flexibility` (`observed - null`) in `data/interim/flexibility_metrics.csv`.  
  *Verification*: Schema validation against `contracts/flexibility_metric.schema.yaml` (`pytest code/tests/unit/test_flexibility_schema.py`).  

- [ ] T112 **Align regression predictor with contract (excess flexibility).**  
  *Description*: Update the specification (spec.md) so that the predictor in FR‑005 is `excess_flexibility` rather than raw `network_flexibility`, matching the `RegressionResult` contract. This change will be reviewed by the methodology panel.  
  *What‑changed*: plan‑root cause; flagged for kick‑back.  

- [ ] T113 **Rename preprocessing output to match data‑model.**  
  *Description*: Move/rename existing preprocessed NIfTI files from `data/processed/{subject_id}_preprocessed.nii.gz` to `data/processed/fmri_clean/{subject_id}.nii.gz`. Update any downstream scripts to use the new path.  
  *Verification*: Existence of files at the new location and successful loading in downstream tasks.

- [ ] T114 **Update data‑model file schema to reflect actual artifact locations.**  
  *Description*: Edit `specs/001-investigating-the-relationship-between-b/data-model.md` so that the file table lists `data/processed/fmri_clean/{id}.nii.gz` and `data/interim/results.csv` as the canonical outputs.  

## Phase 2: Complete validation of the evidence

- [ ] T104 [P] **Write the missing unit tests for core scientific functions** (`calculate_flexibility`, `fit_regression`, `run_permutation_test`).  
  *Test names*: `test_calculate_flexibility_averages`, `test_fit_regression_coefficients`, `test_permutation_seed_reproducibility`.  
  *Verification*: `pytest code/tests/unit/` passes with 0 failures.

- [ ] T105 [P] **Code cleanup and lint conformance.**  
  *Description*: Run `black` on all `code/` files and ensure `flake8 code/` exits with 0 errors.  
  *Dependency*: **depends_on: T104** (lint must run after new test files are added).  

- [ ] T106 **Verify reproducibility in a fresh environment.**  
  *Description*: Create a new virtualenv, install `requirements.txt`, and rerun the quick‑start workflow (`quickstart.md`).  
  *Deliverable*: `docs/outputs/quickstart_run_log.txt` with timestamps and deterministic messages.  
  *Verification*: Compute SHA‑256 checksums for all CSV artifacts (`data/interim/*.csv`) and assert they match the checksums recorded in `data/checksums.json`. PNG checksums are ignored (see executability‑ff9230e9).  

- [ ] T107 [P] **Document every generated artifact.**  
  *Description*: Update `README.md` with a table describing each output file, its columns, units, and the FR/SC it satisfies.  
  *Dependency*: **depends_on: T101,T102,T103** (documentation must reference existing artifacts).  

- [ ] T108 **Write the results handoff for the paper stage.**  
  *Description*: Populate `specs/001-investigating-the-relationship-between-b/research.md` with a concise methods/results section, programmatically linking to the actual CSV and PNG artifacts.  
  *Path corrected*: now points to the correct `specs/001-investigating-the-relationship-between-b/` directory.  

## Phase 3: Documentation and paper handoff (unchanged)

- (All remaining tasks from the original list remain as‑is; no changes required.)