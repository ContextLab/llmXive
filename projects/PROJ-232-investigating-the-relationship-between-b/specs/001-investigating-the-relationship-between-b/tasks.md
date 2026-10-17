# Tasks: Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Musical Emotion Perception

**Inputs**: `spec.md`, `plan.md`, data model/contracts, verifier rejection feedback.  
**Goal**: Smallest complete reproducible study linking resting-state functional connectivity metrics (HCP 1200 Subjects Release) to BMRQ musical reward scores, satisfying FR-001–FR-006.

**Data source decision**: The spec and constitution mandate the **HCP 1200 Subjects Release (Music Task subset)**. Full fMRIPrep preprocessing of raw NIfTI exceeds the free CPU runner; per plan, fMRIPrep is off‑CI and CI validates logic on a small real subset. The loader must fail loudly on any fetch failure — no synthetic fallback ever.

---

## Phase 1: Setup and first end-to-end analysis

- [ ] T001 [P] [US1] Implement the data acquisition module `code/src/data/download.py` that (a) fetches the HCP 1200 Subjects Release (Music Task subset) participant/behavioral table, (b) verifies the BMRQ column exists in the real behavioral data — if absent, write `data/data_gap_report.md` listing the missing variable and exit non‑zero (halt; no proxies), (c) downloads raw rs-fMRI NIfTI + behavioral records for a specified subject list, streaming to `data/raw/<subject_id>/`, computing SHA‑256 checksums stored alongside (`data/raw/<subject_id>/checksums.sha256`). Failed per‑subject downloads must be logged and skipped; a total failure must raise, never fall back to generated data. Add contract tests in `code/tests/test_download.py` validating downloaded records against `specs/001-investigating-the-relationship-between-b/contracts/dataset.schema.yaml` (subject_id, age, sex, bmrq_total, fd_mean, motion_excluded).  
  *Verification*: `python -m code.src.data.download --subjects <n>` produces real files under `data/raw/` with checksums; schema validation tests pass; missing‑BMRQ simulation is triggered via `--simulate-missing-bmrq` flag and exits 1 with the gap report.

- [ ] T002 [US1] Implement the off‑CI fMRIPrep wrapper `code/src/data/preprocess.py` (CPU‑only, motion correction, bandpass 0.01–0.1 Hz). This is the only implementation path that satisfies FR-002 and Principle VI. The script runs on the full dataset on a local/GPU machine; it writes per‑subject `data/preprocessing/run_log.json` containing `subject_id`, `fd_mean`, and `motion_excluded` (true when FD > 0.5 mm). No synthetic FD values are generated – if FD cannot be computed the script raises.  
  *Verification*: Running on a real subject produces a `run_log.json` with numeric `fd_mean` and boolean `motion_excluded`; unit test confirms the FD > 0.5 threshold logic.

- [ ] T013 [P] [US1] Implement a CI‑tractable surrogate preprocessing `code/src/data/preprocess_ci.py` using `nilearn` (motion‑correction + confound regression + bandpass filter). This runs on a single subject during CI to validate the pipeline logic; this surrogate does NOT satisfy FR-002. It also writes `fd_mean` and `motion_excluded` to the same `run_log.json` format for consistency.  
  *Verification*: CI run on one subject produces the expected `run_log.json`; tests ensure the surrogate path does not invoke fMRIPrep.

- [ ] T003 [US1] Implement `code/src/analysis/connectivity.py`: extract time series with the Schaefer‑200 atlas (`nilearn.datasets.fetch_atlas_schaefer_2018`, 200 rois), compute the 200×200 Pearson correlation matrix per included subject, enforce symmetry, set diagonal to 1.0, save to `data/connectivity/<subject_id>_matrix.npy`. Include focused unit tests in `code/tests/test_connectivity.py` asserting symmetry, diagonal = 1.0, and values in [‑1, 1] (FR‑003, spec US‑1 acceptance).  
  *Verification*: Matrix files exist for all non‑excluded subjects and pass the symmetry/diagonal/range tests.

- [ ] T004 [US2] Implement `code/src/analysis/graph_metrics.py` computing per subject from the real connectivity matrices: global efficiency, modularity, participation coefficient, within‑network efficiency for DMN, Salience, and Visual networks (Schaefer Yeo‑7 label mapping), **flattened upper‑triangle edge strengths**, and VIF across the scalar predictors. If any VIF > 5, apply PCA retaining ≥ 95 % variance and record it. Outputs: `data/metrics/<subject_id>_metrics.json` and `data/vif_report.json`. Unit tests in `code/tests/test_metrics.py` verify metric values on a known toy matrix (toy input only for correctness test, never for results).  
  *Verification*: JSON metrics exist per subject with all required keys; VIF report contains numeric entries; tests pass.

- [ ] T005 [US2] Implement `code/src/analysis/merge.py` joining per‑subject metrics (**including the flattened edge‑strength vector**) with behavioral data (BMRQ, age, sex, FD), and excluding motion‑excluded or BMRQ‑missing subjects (listwise, no imputation). Write `data/merged_dataset.csv`, and print final N and BMRQ mean ± SD.  
  *Verification*: CSV contains only complete, included subjects with all required columns (scalar metrics + edge strengths); console/summary artifact reports N and BMRQ distribution.

- [ ] T006 [US2] Run the power gate in `code/src/analysis/stats.py`: given the achieved N, compute power to detect r = 0.20 at α = 0.05 (e.g. `statsmodels` power functions). Write `data/power_gate_status.json` (`{"status": "pass"|"fail", "achieved_power": <float>, "n": <int>}`) and, on failure, `data/power_failure_report.md` stating the shortfall honestly (SC‑005). The study proceeds with results reported alongside the power limitation rather than fabricating subjects.  
  *Verification*: JSON exists with numeric achieved_power; report generated when power < 0.80.

**Checkpoint**: A documented command runs download → preprocess → connectivity → metrics → merge on real HCP subjects, producing real result rows under `data/`. No report writing from expected or invented values.

## Phase 2: Complete the study and validate its evidence

- [ ] T007 [US3] Implement and run the partial‑correlation analysis in `code/src/analysis/stats.py`: for each network metric vs BMRQ total, controlling for age, sex, and FD (residualized/partial correlation), with the **null hypothesis explicitly stated as r = 0**. Apply FDR correction (q < 0.05) across all tests. Write `data/analysis_results.csv` conforming to `specs/001-investigating-the-relationship-between-b/contracts/output.schema.yaml` (metric_name, correlation_r, p_value, p_value_fdr, significant, sample_size, power_achieved). Add contract tests validating the CSV against the schema.  
  *Verification*: CSV validates; `significant` is True only where FDR‑adjusted p < 0.05; null‑hypothesis framing is documented in the accompanying `data/analysis_results_metadata.txt`.

- [ ] T008 [US3] Implement and run regularized regression in `code/src/analysis/stats.py`: Ridge and Lasso (5‑fold CV, fixed seed) predicting BMRQ from **both scalar network metrics and the edge‑strength feature vector** (or its PCA‑reduced form if VIF triggered), compared against the intercept‑only null model. Outputs: `data/regression_cv_results.json` (mean and per‑fold R², selected coefficients) and `data/null_model_results.json`. Report R² honestly against the null baseline (SC‑002), including negative/overfit results if they occur.  
  *Verification*: Both JSONs exist with real CV numbers; comparison to null baseline is recorded.

- [ ] T009 [US3] Implement `code/src/analysis/visualize.py` generating, directly from the validated outputs: (1) `figures/scatter_pred_actual.png` — cross‑validated predicted vs actual BMRQ with regression line and R² annotation; (2) `figures/metric_importance.png` — bar chart of absolute regression coefficients / partial correlations per metric; (3) `figures/scatter_top_metric_bmrq.png` — scatter of the strongest metric–BMRQ correlation with partial‑r annotation; (4) `figures/network_diagram.png` — schematic network diagram highlighting DMN, Salience, and Visual subnetworks on the Schaefer atlas (Plan Task 4.2).  
  *Verification*: PNG files exist and are generated from the actual result artifacts (no hard‑coded values).

- [ ] T010 [US3] Add independent correctness and sensitivity checks and record outcomes: (a) re‑run of the connectivity/metrics pipeline on a held‑out real subject to confirm determinism, writing `data/determinism_check.json` with hashes of the two runs; (b) sensitivity of partial correlations to the FD threshold (0.3 vs 0.5 mm exclusion) reported in `data/sensitivity_fd_threshold.json`; (c) runtime/RAM measurement of the pipeline recorded in `data/resource_usage.json` against the free‑tier limits (SC‑004).  
  *Verification*: The three JSON artifacts exist with real measured values; sensitivity results are discussed relative to the primary analysis.

- [ ] T014 [US3] Implement bootstrap stability analysis off‑CI: run 1000 bootstrap resamples of the full dataset, recompute all network metrics and regression coefficients, and summarize stability (e.g., confidence intervals) in `data/bootstrap_stability.json`. This satisfies Phase 3 Task 3.4 from the plan.  
  *Verification*: JSON artifact exists; summary statistics conform to the plan’s description.

## Phase 3: Reproducible results and paper handoff

- [ ] T011 [P] Write `specs/001-investigating-the-relationship-between-b/research.md` (methods/results account) linked to actual output cells in `data/analysis_results.csv`, `data/regression_cv_results.json`, `data/bootstrap_stability.json`, and figure files. Report N, achieved power, FDR‑corrected findings, null or negative results honestly, and the associational (non‑causal) framing required by the spec assumptions.  
  *Verification*: Every reported number traces to a named result artifact; limitations (power, sample, off‑CI preprocessing) are stated.

- [ ] T012 [P] Update `specs/001-investigating-the-relationship-between-b/quickstart.md` with the single documented command chain (or `main.py` orchestration entry point in `code/src/main.py`) that re‑runs the workflow from declared inputs on the CI‑tractable real subset, confirms all tests (`code/tests/`) and schema validations pass, and documents the paper‑stage handoff: full off‑CI fMRIPrep run and figure/table finalization belong to the paper pipeline.  
  *Verification*: Fresh execution of the documented command completes and produces the end‑to‑end artifacts; handoff requirements are named, not duplicated as research tasks.

---

## Dependencies and requirement coverage

- **FR-001** (data acquisition, checksums): T001. **FR-002** (preprocessing, bandpass, FD): T002 (off‑CI fMRIPrep) satisfies the requirement; T013 is a CI surrogate for logic validation only. **FR-003** (Schaefer‑200, Pearson FC): T003. **FR-004** (graph metrics, VIF, edge strengths): T004, T005, T008. **FR-005** (partial correlation, regularized regression, 5‑fold CV): T007, T008. **FR-006** (FDR q < 0.05): T007. **SC-001/SC-002**: T007/T008. **SC-003**: T007. **SC-004**: T010. **SC-005**: T006.

- Execution order respects data flow: T001 → T002/T013 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T014 → T011 → T012. Parallel‑safety tags `[P]` only on tasks that truly have no strict upstream dependency.

- Verifier‑rejected lint/format configuration is a platform‑level concern; no additional task is required because the platform provides default formatting enforcement. (If later required, a minimal task can be added.)

- All scientific requirements are preserved; no weakening of FR/SC constraints occurs.