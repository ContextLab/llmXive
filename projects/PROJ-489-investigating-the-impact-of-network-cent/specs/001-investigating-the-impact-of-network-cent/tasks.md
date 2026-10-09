# Tasks: Investigating the Impact of Network Centrality on Neural Synchrony During Sleep Stages

**Input**: Design documents from `/specs/001-network-centrality-sleep-synchrony/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by implementation phase and user story to enable independent development and testing. Data flow is respected: US1 (preprocessing) → US2 (metrics) → US3 (analysis).

## Format: `- [ ] T### [P?] [USx?] description with exact artifact paths`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[USx]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions
- Each task names its scientific requirement, concrete output, and observable check

---

## Phase 1: Setup and Foundation (Shared Infrastructure)

**Goal**: Project initialization, dependencies, and basic structure ready for user story implementation.

- [ ] T001 Create project structure: `code/`, `data/raw/`, `data/processed/`, `data/metrics/`, `data/results/`, `tests/unit/`, `tests/integration/`, `reports/`. Verify all directories exist. Document the runnable entry point in `specs/001-network-centrality-sleep-synchrony/quickstart.md` with the command `python code/main.py` and expected outputs (FR-001 provenance).

- [ ] T002 [P] Initialize Python 3.11 environment with pinned dependencies in `code/requirements.txt`: mne, statsmodels, networkx, scipy, pandas, numpy, pyedflib. Create `code/config.yaml` with signal-processing parameters (bandpass filter 0.5–45 Hz, ICA kurtosis threshold 5.0, theta 4–8 Hz, alpha 8–13 Hz band definitions, random seed pinning). Verify import success by running `python -c "import mne, statsmodels, networkx, scipy, pandas, numpy, pyedflib; print('OK')"`.

- [ ] T003 [P] Implement `code/__init__.py` and logging infrastructure in `code/main.py`. Create `code/loaders.py` with functions `load_raw_edf(subject_id)` and `load_annotations(subject_id)` to handle `data/raw/` directory structure. Implement data integrity check utility function `verify_checksum(filepath, expected_hash)` in `code/loaders.py`. Unit test in `tests/unit/test_loaders.py` verifies checksum logic on a synthetic file.

---

## Phase 2: User Story 1 – Data Acquisition and Preprocessing Pipeline (Priority P1)

**Goal**: Automatically download Sleep-EDF dataset from PhysioNet, preprocess EEG (filtering, ICA, epoching), and segment into labeled 30-second epochs. Output: cleaned signal arrays and epoch metadata in `data/processed/`.

**Independent Test**: Pipeline executes on a real Sleep-EDF subset (≥3 subjects), produces epoch counts matching expected 30-second windows per subject, and no NaN values remain in filtered signal arrays.

- [ ] T004 [US1] Implement `code/download.py` with function `download_sleep_edf(output_dir='data/raw/')` to fetch Sleep-EDF dataset from PhysioNet via MNE-Python's `mne.datasets.sleep_physionet.fetch_data()`. Verify file checksums using MNE's built-in validation. Log download progress and file counts to `data/raw/download_log.txt`. Implement error handling: if a single `.edf` file is corrupted, log the error, skip that file, and continue with remaining subjects (Edge Case: Data Corruption). Output: ≥30 subjects' `.edf` files in `data/raw/` with verified integrity. Test in `tests/integration/test_download.py` confirms ≥3 subjects are downloaded and checksums pass.

- [ ] T005 [US1] Implement `code/preprocess.py` with function `apply_bandpass_filter(raw_signal, low_freq=0.5, high_freq=45.0)` using MNE's `mne.filter.filter_data()`. Apply to all raw EEG channels. Output: filtered signal arrays (numpy format). Unit test in `tests/unit/test_preprocess.py` verifies filter response on synthetic sinusoids (pass 10 Hz, attenuate 0.1 Hz and 100 Hz).

- [ ] T006 [US1] Implement `code/preprocess.py` with function `remove_ica_artifacts(filtered_signal, kurtosis_threshold=5.0, power_ratio_threshold=3.0)` using MNE's `mne.preprocessing.ICA`. Identify components with kurtosis > threshold or high-frequency power > 3× baseline. Remove flagged components and reconstruct signal. Output: cleaned signal arrays. Unit test in `tests/unit/test_preprocess.py` verifies artifact flagging on synthetic high-kurtosis and high-frequency components.

- [ ] T007 [US1] Implement `code/preprocess.py` with function `epoch_by_sleep_stage(cleaned_signal, annotations, epoch_duration_sec=30)` to segment cleaned EEG into 30-second non-overlapping windows. Label each epoch with sleep stage (Wake, N1, N2, N3, REM) from the accompanying `.edf` annotation file. Extract `waking_night_id` and `sleep_night_id` from the recording metadata to enable temporal proximity checks. Output: `data/processed/epochs_{subject_id}.npz` (containing segmented signal and stage labels) and `data/processed/metadata_{subject_id}.json` (containing night IDs and epoch counts). Unit test in `tests/unit/test_preprocess.py` verifies epoch shape (30 × sample_rate, channels) and stage label distribution.

- [ ] T008 [US1] Implement `code/preprocess.py` with function `validate_no_nans(signal_array)` to check for NaN values in output arrays. If NaNs are present, raise an exception with the count and location. Integrate into the preprocessing pipeline so that validation runs after epoching. Output: `data/processed/validation_log.txt` listing each subject and NaN status. Unit test confirms exception is raised when NaNs are present.

- [ ] T009 [US1] Integrate preprocessing steps into `code/main.py` orchestration script: call T004 (download) → T005 (filter) → T006 (ICA) → T007 (epoch) → T008 (validate). Run end-to-end on ≥3 real subjects from Sleep-EDF. Verify output files exist in `data/processed/` and epoch counts are reasonable (e.g., ≥10 epochs per subject per stage). Log runtime and memory usage. Output: `data/processed/preprocessing_complete.txt` with subject counts and validation summary. Integration test in `tests/integration/test_pipeline.py` runs full pipeline on a 3-subject subset and verifies all output files are present and valid.

---

## Phase 3: User Story 2 – Metric Computation (Centrality and Synchrony) (Priority P2)

**Goal**: Compute network centrality metrics (degree, betweenness, eigenvector) from waking resting-state functional connectivity and neural synchrony (Phase Lag Index) from sleep-stage epochs. Output: `data/metrics/SubjectMetrics.csv` with one row per subject, columns for each centrality metric and sleep-stage synchrony score.

**Independent Test**: Generate summary CSV with centrality and synchrony scores for ≥3 subjects, openable in a spreadsheet without errors, all numeric columns populated and in expected ranges (centrality 0–1, synchrony 0–1).

- [ ] T010 [US2] Implement `code/metrics.py` with function `compute_connectivity_matrix(waking_signal, freq_bands={'theta': (4, 8), 'alpha': (8, 13)})` to construct functional connectivity matrices using coherence in theta and alpha bands from waking resting-state EEG. Use `scipy.signal.coherence()` or MNE's coherence estimator. Output: symmetric connectivity matrices (numpy arrays) with values strictly between 0 and 1. Unit test in `tests/unit/test_metrics.py` verifies matrix symmetry and value range on synthetic signals.

- [ ] T011 [US2] Implement `code/metrics.py` with function `compute_centrality_metrics(connectivity_matrix)` using NetworkX to calculate degree, betweenness, and eigenvector centrality for each node (electrode). Output: dictionary with three arrays (one per metric), length = number of electrodes. Validate on a synthetic test graph with known topology (e.g., star graph) and verify centrality values match pre-calculated reference values within tolerance 1e-6. Unit test in `tests/unit/test_metrics.py` includes synthetic graph validation.

- [ ] T012 [US2] Implement `code/metrics.py` with function `compute_pli(epoch_signal, electrode_pairs=None)` to calculate Phase Lag Index across all electrode pairs for a single 30-second epoch. If `electrode_pairs` is None, compute for all pairs. Output: array of PLI values (one per pair). Aggregate to mean global synchrony score (scalar, 0–1) per sleep stage. Unit test in `tests/unit/test_metrics.py` verifies PLI calculation on synthetic phase-locked signals.

- [ ] T013 [US2] Implement `code/metrics.py` with function `compute_vif(centrality_metrics_dict)` to calculate Variance Inflation Factor for all centrality metrics using `statsmodels.stats.outliers_influence.variance_inflation_factor()`. Flag metrics with VIF > 5.0 as collinear. Output: JSON report `data/metrics/vif_report.json` with VIF values and collinearity flags. Unit test in `tests/unit/test_metrics.py` verifies VIF calculation on synthetic correlated and uncorrelated data.

- [ ] T014 [US2] Implement `code/metrics.py` with function `aggregate_subject_metrics(subject_id, processed_epochs_dir, connectivity_matrix, centrality_dict, vif_report)` to combine all metrics for one subject into a single row: subject_id, degree, betweenness, eigenvector, pli_wake, pli_n1, pli_n2, pli_n3, pli_rem, waking_night_id, sleep_night_id, temporal_proximity_flag. Handle missing sleep stages by excluding the subject–stage pair from further analysis (Edge Case: Missing Sleep Stages). Output: one-row pandas DataFrame. Unit test in `tests/unit/test_metrics.py` verifies row structure and handles missing stages gracefully.

- [ ] T015 [US2] Integrate metric computation into `code/main.py`: iterate over all preprocessed subjects in `data/processed/`, call T010 (connectivity) → T011 (centrality) → T012 (PLI) → T013 (VIF) → T014 (aggregate) for each subject. Collect all rows into a single DataFrame and save as `data/metrics/SubjectMetrics.csv`. Output: CSV file with ≥3 subjects (or as many as successfully preprocessed), all required columns, no missing values in numeric fields. Integration test in `tests/integration/test_metrics.py` loads the CSV, verifies schema (column names and types), and confirms all numeric columns are within expected ranges.

---

## Phase 4: User Story 3 – Statistical Analysis and Reporting (Priority P3)

**Goal**: Execute Linear Mixed-Effects (LME) analysis between centrality metrics and sleep-stage synchrony, apply False Discovery Rate (FDR) correction, validate sample size, and generate final report with results and limitations.

**Independent Test**: Analysis script runs on metrics CSV (≥3 subjects), produces JSON report with LME coefficients, raw p-values, and FDR-corrected p-values; programmatically validate JSON schema and p-value ordering (raw ≤ corrected).

- [ ] T016 [US3] Implement `code/analysis.py` with function `check_sample_size(metrics_df)` to validate N ≥ 30 subjects. If N < 30, log a warning message (do NOT halt execution). Output: integer N and boolean flag `insufficient_sample`. Unit test in `tests/unit/test_analysis.py` verifies warning is logged when N < 30.

- [ ] T017 [US3] Implement `code/analysis.py` with function `compute_global_coherence(connectivity_matrix)` to calculate mean coherence across all electrode pairs as a subject-level covariate (global signal strength proxy). Output: scalar value per subject. Unit test in `tests/unit/test_analysis.py` verifies output is a float in [0, 1].

- [ ] T018 [US3] Implement `code/analysis.py` with function `fit_lme_model(metrics_df)` to fit Linear Mixed-Effects model with formula `centrality_metric ~ pli_stage + global_coherence + (1|subject)` using `statsmodels.formula.api.mixedlm()`. Fit one model per centrality metric (degree, betweenness, eigenvector) and per sleep stage (N1, N2, N3, REM). Extract coefficients, standard errors, and raw p-values. Output: dictionary of model results. Unit test in `tests/unit/test_analysis.py` verifies model fitting on synthetic data and coefficient extraction.

- [ ] T019 [US3] Implement `code/analysis.py` with function `apply_fdr_correction(raw_pvalues)` to apply Benjamini-Hochberg FDR correction to the family of all raw p-values (3 metrics × 4 stages = 12 tests). Verify that corrected p-values are ≥ raw p-values and that the family-wise error rate is controlled. Output: array of FDR-corrected p-values. Unit test in `tests/unit/test_analysis.py` verifies ordering (raw ≤ corrected) and FDR logic on synthetic p-value arrays.

- [ ] T020 [US3] Implement `code/analysis.py` with function `compute_residual_diagnostics(lme_model)` to perform Shapiro-Wilk normality test on LME residuals for diagnostic purposes (not for model selection). Output: JSON file `data/results/residuals_diagnostics.json` with test statistic, p-value, and interpretation. Unit test in `tests/unit/test_analysis.py` verifies JSON schema and Shapiro-Wilk calculation.

- [ ] T021 [US3] Integrate analysis into `code/main.py`: load `data/metrics/SubjectMetrics.csv` → T016 (sample size check) → T017 (global coherence) → T018 (LME fitting) → T019 (FDR correction) → T020 (diagnostics). Collect all results into a single JSON structure: `data/results/analysis_results.json` containing LME coefficients, raw p-values, FDR-corrected p-values, and diagnostic information. Output: JSON file with schema `{"models": {"metric_stage": {"coefficient": float, "se": float, "raw_p": float, "fdr_p": float}}, "diagnostics": {...}, "sample_size": int}`. Unit test in `tests/unit/test_analysis.py` verifies JSON schema and p-value ordering.

- [ ] T022 [US3] Implement `code/report.py` with function `generate_report(analysis_results, metrics_df, vif_report)` to create a human-readable Markdown report `reports/final_report.md` containing:
  - Summary of sample size (N) and any warnings if N < 30.
  - Table of LME coefficients and FDR-corrected p-values for each metric–stage pair.
  - Significance flags: "Significant" if FDR-corrected p < 0.05, else "Non-Significant".
  - VIF report: list any centrality metrics with VIF > 5.0 and note them as collinear (do NOT claim independent effects).
  - Confounding limitation section: if `temporal_proximity_flag == True` for any subject, note that waking and sleep data originate from the same night and may share confounds.
  - Diagnostic section: Shapiro-Wilk results for residual normality.
  - Honest statement of limitations (observational design, no causal claims, missing sleep stages excluded).
  
  Output: Markdown file `reports/final_report.md`. Unit test in `tests/unit/test_report.py` verifies Markdown structure and presence of required sections.

- [ ] T023 [US3] Implement `code/report.py` with function `generate_json_report(analysis_results, metrics_df, vif_report)` to output a JSON summary `data/results/analysis_report.json` with all numerical results in machine-readable format. Schema: `{"results": [{metric, stage, coefficient, se, raw_p, fdr_p, significant}], "sample_size": int, "vif_flags": [...], "temporal_proximity_flags": [...]}`. Unit test in `tests/unit/test_report.py` verifies JSON schema and field completeness.

- [ ] T024 [US3] Run full end-to-end pipeline from `code/main.py` on the complete preprocessed dataset (all subjects from T009). Verify that:
  - `data/results/analysis_results.json` is created with all required fields.
  - `reports/final_report.md` is generated and readable.
  - All FDR-corrected p-values are ≥ raw p-values.
  - Significant results (FDR p < 0.05) are clearly flagged.
  - VIF and temporal proximity warnings are included.
  
  Log runtime and memory usage. Output: `data/results/pipeline_complete.txt` with completion timestamp and artifact summary. Integration test in `tests/integration/test_full_pipeline.py` runs the complete pipeline and validates all output files.

---

## Phase 5: Validation and Handoff

**Goal**: Verify reproducibility, document results, and prepare for paper-stage handoff.

- [ ] T025 [P] Create `specs/001-network-centrality-sleep-synchrony/quickstart.md` with step-by-step instructions to run the pipeline from a fresh clone:
  ```
  1. git clone <repo>
  2. cd <repo>
  3. python -m pip install -r code/requirements.txt
  4. python code/main.py
  ```
  Expected output: `data/results/analysis_results.json`, `reports/final_report.md`, `data/metrics/SubjectMetrics.csv`. Estimated runtime: < 4 hours on 2 vCPU. Peak memory: < 4 GB RAM.

- [ ] T026 [P] Document the data model in `specs/001-network-centrality-sleep-synchrony/data-model.md` (if not already present) with definitions of all entities (Subject, WakingNetwork, SleepStageEpoch), their attributes, and relationships. Include schema for all output CSV and JSON files.

- [ ] T027 [P] Run the documented quickstart workflow on a fresh environment to verify reproducibility. Confirm that all output files are generated with expected schema and content. Output: `data/results/reproducibility_check.txt` documenting success or any issues encountered.

- [ ] T028 [P] Create `specs/001-network-centrality-sleep-synchrony/methods.md` documenting the analysis methods: data source (Sleep-EDF, PhysioNet), preprocessing (bandpass filter, ICA, epoching), metrics (centrality, PLI, global coherence), and statistical approach (LME with FDR correction). Include citations to key papers and software packages. Link to actual output files and code locations.

---

## Dependencies & Execution Order

### Critical Path

1. **Phase 1** (T001–T003): Foundation. No dependencies. Enables all subsequent phases.
2. **Phase 2** (T004–T009): User Story 1. Depends on Phase 1. Produces `data/processed/` outputs required by Phase 3.
3. **Phase 3** (T010–T015): User Story 2. Depends on Phase 2. Produces `data/metrics/SubjectMetrics.csv` required by Phase 4.
4. **Phase 4** (T016–T024): User Story 3. Depends on Phase 3. Produces final analysis results and reports.
5. **Phase 5** (T025–T028): Validation & handoff. Depends on Phase 4. Finalizes documentation and verifies reproducibility.

### Parallel Opportunities

- Within Phase 1: T002 and T003 can run in parallel (different files, no data dependencies).
- Within Phase 2: After T004 completes, T005, T006, and T007 can be developed in parallel but must be integrated sequentially in T009 (data flow).
- Within Phase 3: T010–T014 can be developed in parallel but must be integrated sequentially in T015 (data flow).
- Within Phase 4: T016–T020 can be developed in parallel but must be integrated sequentially in T021 (data flow).
- Phase 5: T025–T028 can run in parallel after Phase 4 completes.

### Data Flow

- T004 (download) → T005–T008 (preprocess) → T009 (integrate) → `data/processed/`
- `data/processed/` → T010–T014 (metrics) → T015 (integrate) → `data/metrics/SubjectMetrics.csv`
- `data/metrics/SubjectMetrics.csv` → T016–T020 (analysis) → T021 (integrate) → `data/results/`
- `data/results/` → T022–T024 (reporting) → `reports/` and final artifacts

---

## Success Criteria Verification

| Task ID | Requirement | Observable Check | Output File(s) |
| :--- | :--- | :--- | :--- |
| T001 | Project structure (FR-001 provenance) | All directories exist; `quickstart.md` contains runnable command | `specs/.../quickstart.md` |
| T004 | Download Sleep-EDF with checksum (FR-001) | ≥30 subjects in `data/raw/`; checksums pass | `data/raw/download_log.txt` |
| T009 | Preprocessing pipeline end-to-end | ≥3 subjects processed; no NaNs in output | `data/processed/preprocessing_complete.txt` |
| T015 | Metric computation & aggregation | `SubjectMetrics.csv` with ≥3 rows, all columns populated | `data/metrics/SubjectMetrics.csv` |
| T021 | LME analysis with FDR correction | `analysis_results.json` with coefficients and p-values; raw ≤ corrected | `data/results/analysis_results.json` |
| T024 | Full pipeline execution | All outputs present; runtime < 4h; memory < 4 GB | `data/results/pipeline_complete.txt` |
| T025 | Quickstart reproducibility | Fresh clone can run pipeline successfully | `specs/.../quickstart.md` |

---

## Notes

- All tasks are designed to run on a CPU-only GitHub Actions runner (2 vCPU, ~7 GB RAM, ~14 GB disk, ≤6 h).
- The pipeline implements the plan's methodological approach: LME models with FDR correction (upgraded from Bonferroni per plan.md), global coherence covariate, and temporal proximity tracking.
- Edge cases (missing sleep stages, corrupted files, collinearity) are explicitly handled in the relevant tasks.
- No synthetic data or fabricated fallbacks are used; all analysis is on real Sleep-EDF data streamed from PhysioNet.
- Verification is deterministic: each task produces a concrete output file with verifiable schema and content.
