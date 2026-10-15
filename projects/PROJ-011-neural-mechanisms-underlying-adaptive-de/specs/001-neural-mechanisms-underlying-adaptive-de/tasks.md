# Tasks: Neural Mechanisms Underlying Adaptive Decision-Making in Response to Social Feedback

**Input**: Design documents from `/specs/001-neural-mechanisms-adaptive-decision/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`

## Phase 1 – Setup and Reproducibility  

- [ ] T001 [P] Establish reproducibility settings: pin global random seeds (`numpy`, `random`, `torch` if used) in a config file `code/utils/reproducibility.py` and verify that scripts import this module.  
  - **Path**: `code/utils/reproducibility.py`, `README.md` (seed documentation)  
  - **Verification**: Running `python -c "import code.utils.reproducibility as r; assert r.SEED == 42"` exits with status 0; `make quickstart` produces deterministic output across runs.

- [ ] T002 [P] Run the Reference‑Validator Agent on all citations in `spec.md`, `plan.md`, and `README.md`.  
  - **Path**: `scripts/run_reference_validator.sh` (wrapper), `state/reference_validation_report.yaml`  
  - **Verification**: Script exits with status 0 only if all citations are verified; report contains no `unreachable` or `mismatch` entries.

- [ ] T003 [P] Document the project layout and dependencies in `quickstart.md` and `requirements.txt`.  
  - **Path**: `quickstart.md`, `requirements.txt`  
  - **Verification**: `make quickstart` prints the exact command documented and exits with status 0.

## Phase 3 – User Story 1: Data Acquisition & Pre‑processing (Priority P1)  

- [ ] T010 [P] [US1] Contract test for data validation (`tests/contract/test_data_validation.py`).  
  - **Verification**: Test fails before implementation, passes after T012.  

- [ ] T011 [P] [US1] Integration test for ROI extraction (`tests/integration/test_roi_extraction.py`).  
  - **Verification**: Test fails before implementation, passes after T017.  

- [ ] T012 [US1] Implement `code/preprocessing/data_validation.py` to verify the OpenNeuro **ds003694** structure and write the dataset manifest.  
  - **Path**: `code/preprocessing/data_validation.py`, `state/dataset_manifest.json`  
  - **Verification**: Raises `FileNotFoundError` with a clear message if the expected files are absent; otherwise creates the manifest file.  

- [ ] T013 [US1] Implement `code/preprocessing/data_download.py` to fetch OpenNeuro ds003694 via `openneuro-py`.  
  - **Path**: `code/preprocessing/data_download.py`, `data/raw/`  
  - **Verification**: On failure the script aborts with a loud exception; on success the raw NIfTI and behavioral files appear under `data/raw/`.  

- [ ] T014 [US1] Implement `code/preprocessing/motion_correction.py` using lightweight `nilearn` pipelines.  
  - **Path**: `code/preprocessing/motion_correction.py`, `data/processed/mc/`  
  - **Verification**: Produces motion‑corrected NIfTI files; a checksum file `state/mc_hashes.yaml` is written.  

- [ ] T014b [US1] Implement `code/preprocessing/validate_motion_correction.py` to ensure default `nilearn` parameters were used and document them.  
  - **Path**: `code/preprocessing/validate_motion_correction.py`, `data/reports/mc_params.yaml`  
  - **Verification**: Script exits with status 0 only if parameters match the documented defaults.  

- [ ] T015 [US1] Implement `code/preprocessing/normalization.py` for MNI152NLin2009cAsym spatial normalization.  
  - **Path**: `code/preprocessing/normalization.py`, `data/processed/norm/`  
  - **Verification**: Normalized files have affine matrices matching the MNI template; a log `data/reports/normalization.log` is created.  

- [ ] T016 [US1] Implement `code/preprocessing/smoothing.py` with a moderate (5 mm) kernel.  
  - **Path**: `code/preprocessing/smoothing.py`, `data/processed/smooth/`  
  - **Verification**: Smoothed files exist; `data/reports/smoothing.yaml` records kernel size.  

- [ ] T017 [US1] Implement `code/preprocessing/roi_extraction.py` to extract BOLD time‑series from dlPFC, ventral striatum, and ACC using the Harvard‑Oxford atlas, processing data in 50‑time‑point chunks.  
  - **Path**: `code/preprocessing/roi_extraction.py`, `data/processed/roi/`  
  - **Verification**: For each participant a parquet file `roi_<sub>.parquet` with three region columns and matching time‑point length is created; schema validated against `contracts/roi_data.schema.yaml`.  

- [ ] T018 [US1] Implement `code/preprocessing/qc_filter.py` to exclude participants with >10 % volumes exceeding 3 mm translation (SC‑001).  
  - **Path**: `code/preprocessing/qc_filter.py`, `state/exclusions.yaml` (populated with participant IDs and reasons)  
  - **Verification**: After run, `state/exclusions.yaml` contains only participants that failed the motion threshold; downstream tasks read this file to skip excluded IDs.  

- [ ] T018b [US1] Implement `code/preprocessing/qc_reporter.py` to generate `data/reports/qc_summary.json` (SC‑001 summary) **including** exclusion rate, and update `state/exclusions.yaml` with the final exclusion list.  
  - **Path**: `code/preprocessing/qc_reporter.py`, `data/reports/qc_summary.json`, `state/exclusions.yaml`  
  - **Verification**: `qc_summary.json` conforms to the schema shown in the spec and contains keys `total_participants`, `excluded_count`, `exclusion_rate`, `threshold_volumes_percent`, `threshold_motion_mm`, `exclusion_reasons`.  

- [ ] T019 [US1] Create `code/main.py` entry point (initialisation only).  
  - **Path**: `code/main.py`  
  - **Verification**: Running `python -m code.main --help` displays usage without executing the pipeline.  

- [ ] T049 [US1] Implement `code/preprocessing/streaming_loader.py` to stream the full ds003694 dataset participant‑wise; if streaming truly fails, the script aborts with an informative error (no sampling fallback) and logs the strategy in `data/reports/sampling_policy.json`.  
  - **Path**: `code/preprocessing/streaming_loader.py`, `data/reports/sampling_policy.json`  
  - **Verification**: Loader processes all participants; `sampling_policy.json` records `"strategy": "full_stream"` and any error messages if streaming is impossible.  

## Phase 4 – User Story 2: Computational Modeling of Belief Updating (Priority P2)  

- [ ] T021 [P] [US2] Contract test for model convergence (`tests/contract/test_model_convergence.py`).  
  - **Verification**: Fails before T024, passes after convergence logic is added.  

- [ ] T022 [P] [US2] Integration test for synthetic data recovery (`tests/integration/test_synthetic_recovery.py`).  
  - **Verification**: Fails before T023, passes once synthetic generator and model are linked.  

- [ ] T023 [US2] Implement `code/modeling/synthetic_data_generator.py` to create `data/synthetic/ground_truth.csv`.  
  - **Path**: `code/modeling/synthetic_data_generator.py`, `data/synthetic/ground_truth.csv`  
  - **Verification**: CSV contains columns `subject_id,true_alpha,true_precision,generated_choices`; model recovery test checks α within ±0.1 for ≥ 90 % of subjects.  

- [ ] T024a [US2] Implement `code/modeling/n_valid_calculator.py` to read `state/exclusions.yaml` and write `state/n_valid.yaml`.  
  - **Path**: `code/modeling/n_valid_calculator.py`, `state/n_valid.yaml`  
  - **Verification**: `n_valid.yaml` contains an integer field `N_valid` equal to the number of participants that passed QC.  

- [ ] T024 [US2] Implement `code/modeling/belief_updater.py` using `pymc` with the `numpyro` CPU backend, including RAM‑usage guard (‑‑max‑ram 70 %) and runtime estimator (`code/utils/runtime_estimator.py`).  
  - **Path**: `code/modeling/belief_updater.py`, `data/models/belief_updater_trace.nc`  
  - **Verification**: Script writes a trace file; `data/models/convergence_report.json` records per‑participant R‑hat and ESS; runtime stays < 6 h for the given `N_valid`.  

- [ ] T025 [US2] Implement `code/modeling/validation.py` to check convergence (R‑hat < 1.01, ESS > 400) and retry up to three times on failure.  
  - **Path**: `code/modeling/validation.py`, `data/models/convergence_report.json` (updated)  
  - **Verification**: After execution, the report lists `converged: true/false` per participant.  

- [ ] T025b [US2] Implement `code/modeling/convergence_reporter.py` to aggregate convergence logs and compute the overall convergence rate against `N_valid`.  
  - **Path**: `code/modeling/convergence_reporter.py`, `data/models/convergence_report.json`  
  - **Verification**: JSON contains fields `converged_count`, `N_valid`, `convergence_rate`.  

- [ ] T025c [US2] Implement `code/modeling/failure_handler.py` to log permanently excluded participants in `data/models/failure_log.json`.  
  - **Path**: `code/modeling/failure_handler.py`, `data/models/failure_log.json`  
  - **Verification**: Log lists participant IDs with reason “non‑convergence after 3 attempts”.  

- [ ] T025d [US2] **[SC‑002]** Verify that the overall convergence rate is ≥ 90 % and fail the pipeline otherwise.  
  - **Path**: `code/modeling/convergence_rate_check.py` (new script)  
  - **Verification**: Script reads `data/models/convergence_report.json`; exits with non‑zero status if `convergence_rate < 0.90`.  

- [ ] T028 [US2] Extend `code/main.py` to read the convergence report, filter out non‑converging participants, and write `state/valid_participants.yaml`.  
  - **Path**: `code/main.py` (updated), `state/valid_participants.yaml`  
  - **Verification**: YAML contains a list `valid_participants` that excludes IDs present in `failure_log.json`.  

- [ ] T027 [US2] Implement `code/modeling/model_output.py` to save individual α parameters and group‑level hyperparameters for the valid participants only.  
  - **Path**: `code/modeling/model_output.py`, `data/models/params.parquet`  
  - **Verification**: Parquet file conforms to `contracts/model_params.schema.yaml`.  

## Phase 5 – User Story 3: Neural‑Behavioral Correlation & Hypothesis Testing (Priority P3)  

- [ ] T029 [P] [US3] Contract test for GLM‑correlation (`tests/contract/test_glm_correlation.py`).  
  - **Verification**: Fails before T031, passes after GLM implementation.  

- [ ] T030 [P] [US3] Integration test for permutation testing (`tests/integration/test_permutation_test.py`).  
  - **Verification**: Fails before T033, passes after permutation script is functional.  

- [ ] T037a [US3] Implement `code/analysis/loader.py` to merge filtered α parameters and ROI time‑series into `data/processed/unified_analysis_data.parquet`.  
  - **Path**: `code/analysis/loader.py`, `data/processed/unified_analysis_data.parquet`  
  - **Verification**: Parquet has columns `participant_id, alpha, dlPFC, ventral_striatum, ACC` and rows = `N_valid`.  

- [ ] T037b [US3] Implement `code/analysis/main_analysis.py` to orchestrate the analysis pipeline and produce `data/analysis/analysis_run_log.json`.  
  - **Path**: `code/analysis/main_analysis.py`, `data/analysis/analysis_run_log.json`  
  - **Verification**: Log records timestamps and the successful completion of each downstream task.  

- [ ] T031 [US3] Implement `code/analysis/glm_analysis.py` to run a GLM with parametric modulation by feedback discrepancy and output beta maps per ROI.  
  - **Path**: `code/analysis/glm_analysis.py`, `data/analysis/glm_beta.parquet`  
  - **Verification**: Parquet contains `participant_id, region, beta_discrepancy`; values pass a sanity check (|β| < 10).  

- [ ] T032 [US3] Implement `code/analysis/partial_correlation.py` to compute LOSO partial correlations between neural activation and α, controlling for input discrepancy.  
  - **Path**: `code/analysis/partial_correlation.py`, `data/analysis/partial_corr.parquet`  
  - **Verification**: Parquet conforms to `contracts/neural_signatures.schema.yaml` (fields `correlation_alpha`, `p_value`, `fdr_q_value`).  

- [ ] T032b **[SC‑003]** Verify that the partial correlation coefficient `correlation_alpha` ≥ 0.3 for the primary analysis; fail otherwise.  
  - **Path**: `code/analysis/partial_corr_check.py` (new script)  
  - **Verification**: Script reads `data/analysis/partial_corr.parquet`; exits non‑zero if any `correlation_alpha < 0.3`.  

- [ ] T033 [US3] Implement `code/analysis/permutation_test.py` for voxel‑wise inference with early‑stopping and Benjamini‑Hochberg FDR correction (q < 0.05).  
  - **Path**: `code/analysis/permutation_test.py`, `data/analysis/fdr_status.json`  
  - **Verification**: JSON contains `fdr_applied: true` and the computed `q_threshold`; runtime stays < 6 h.  

- [ ] T033b **[SC‑004]** Verify that the FDR‑corrected q‑value reported in `data/analysis/fdr_status.json` is < 0.05; fail otherwise.  
  - **Path**: `code/analysis/fdr_q_check.py` (new script)  
  - **Verification**: Script exits non‑zero if `q_threshold >= 0.05`.  

- [ ] T034 [US3] Implement `code/analysis/confound_control.py` to add motion parameters and aCompCor components as regressors in the GLM.  
  - **Path**: `code/analysis/confound_control.py`  
  - **Verification**: GLM design matrix includes the additional columns; a log `data/reports/confound_matrix.yaml` records shapes.  

- [ ] T035 [US3] Implement `code/analysis/loso_validation.py` for Leave‑One‑Subject‑Out cross‑validation of the neural‑behavioral link.  
  - **Path**: `code/analysis/loso_validation.py`, `data/analysis/loso_results.parquet`  
  - **Verification**: Each fold’s correlation coefficient is stored; overall mean r matches the full‑sample result within 0.02.  

- [ ] T036a [US3] Implement `code/analysis/sensitivity_sweeper.py` to re‑run the correlation for α‑thresholds {0.01, 0.05, 0.1} without refitting the Bayesian model.  
  - **Path**: `code/analysis/sensitivity_sweeper.py`, `data/analysis/sensitivity_raw.csv`  
  - **Verification**: CSV lists `threshold, correlation_alpha, delta` and `delta < 0.05` for all thresholds.  

- [ ] T036b [US3] Implement `code/analysis/sensitivity_reporter.py` to aggregate sweep results into `data/analysis/sensitivity_stability_report.csv`.  
  - **Path**: `code/analysis/sensitivity_reporter.py`, `data/analysis/sensitivity_stability_report.csv`  
  - **Verification**: Report includes a summary row with `max_change < 0.05`.  

- [ ] T038a [US3] Implement `code/reporting/generate_stats.py` to compile final statistics into `results/final_stats.json`.  
  - **Path**: `code/reporting/generate_stats.py`, `results/final_stats.json`  
  - **Verification**: JSON contains keys `partial_corr_r`, `p_value`, `fdr_q_value`, `power_estimate`.  

- [ ] T038b [US3] Implement `code/reporting/generate_figures.py` to produce PNG figures saved under `results/figures/`.  
  - **Path**: `code/reporting/generate_figures.py`, `results/figures/`  
  - **Verification**: At least three figures (GLM beta map, correlation scatter, permutation histogram) are present and readable.  

- [ ] T038c [US3] Implement `code/reporting/generate_research_doc.py` to assemble `docs/research.md` linking to all generated artifacts.  
  - **Path**: `code/reporting/generate_research_doc.py`, `docs/research.md`  
  - **Verification**: The markdown file contains hyperlinks to `final_stats.json`, the figures, and the analysis tables.  

## Phase 2 – Complete the study and validate its evidence  

- [ ] T004 Run the full analysis pipeline (preprocessing, modeling, and neural‑behavioral analysis) and produce the final result file.  
  - **Path**: `code/main.py --full-run`, `data/results/full_run.parquet`  
  - **Verification**: After execution, downstream validation script `code/utils/verify_full_run.py` runs without error, confirming that `data/results/full_run.parquet` exists and contains all required columns; exit code 0.

- [ ] T005 Add comprehensive integration, sensitivity, and runtime checks; record outcomes alongside result artifacts.  
  - **Path**: `tests/integration/`, `results/runtime_report.json`  
  - **Verification**: `pytest -m integration` passes; `runtime_report.json` includes `total_runtime < 6h` and `peak_memory < 6GB`.  

- [ ] T006 Generate the final tables and figures directly from validated outputs, including uncertainty statements where required.  
  - **Path**: `code/reporting/generate_stats.py`, `code/reporting/generate_figures.py`, `results/tables/`, `results/figures/`  
  - **Verification**: Scripts run without error and produce at least one CSV table and one PNG figure that validate against the schemas in `contracts/`.  

## Phase N – Polish & Cross‑cutting concerns  

- [ ] T039a [P] Update `README.md` with Installation, Data Download, Usage, and Troubleshooting sections.  
  - **Verification**: Running `make quickstart` after the update still succeeds; `README.md` contains the headings `Installation`, `Data Download`, `Usage`, `Troubleshooting`.  

- [ ] T039b [P] Generate API documentation in `docs/api/`.  
  - **Verification**: `docs/api/` directory exists with HTML/Markdown files; `pytest --doctest-glob='docs/api/*.md'` passes.  

- [ ] T040a [Sequential] Refactor `code/modeling/belief_updater.py` for CPU memory optimisation (peak < 6 GB).  
  - **Verification**: Run `python -m memory_profiler code/modeling/belief_updater.py` and assert peak memory < 6 GB.  

- [ ] T041a [P] Implement `code/utils/runtime_reporter.py` to produce `results/runtime_report.json`.  
  - **Verification**: `results/runtime_report.json` exists and contains keys `total_runtime` (≤ 6 h) and `peak_memory` (≤ 6 GB).  

- [ ] T042 [P] Add additional unit tests for edge cases (motion exclusion, non‑convergence).  
  - **Verification**: New tests are discovered by `pytest` and all pass.  

- [ ] T043 [Terminal] Validate `quickstart.md` end‑to‑end reproducibility.  
  - **Verification**: CI step runs `make quickstart` and asserts exit 0 and that expected output files (e.g., `data/results/demo_output.parquet`) are created.  

- [ ] T020 [Terminal] Implement `code/utils/hash_artifacts.py` to compute SHA‑256 checksums for all final files and store them in `state/artifact_hashes.yaml`.  
  - **Verification**: Test that `state/artifact_hashes.yaml` contains an entry for every file under `data/` and `code/`.  

- [ ] T044 [P] Implement `code/utils/runtime_stress_test.py` to stress‑test a representative sample (N = 5) and output `results/stress_test_report.json`.  
  - **Verification**: `results/stress_test_report.json` exists and reports runtime < 6 h for the sample.  

- [ ] T046 [P] Create `docs/reproducibility_checklist.md` documenting exact steps, seeds, and environment variables, citing `state/artifact_hashes.yaml`.  
  - **Verification**: File exists; contains hyperlinks to `state/artifact_hashes.yaml` and lists all seed values used.  

- [ ] T047 [P] Implement `code/analysis/power_analyzer.py` to perform a post‑hoc power analysis and write `data/reports/power_analysis.json`.  
  - **Verification**: `data/reports/power_analysis.json` is created and includes fields `estimated_power` and `effect_size`.  

- [ ] T048 [P] Implement `code/analysis/assumption_checker.py` to verify GLM residual normality and homoscedasticity, outputting `data/reports/assumption_checks.json`.  
  - **Verification**: `data/reports/assumption_checks.json` exists and contains boolean flags `normality_pass` and `homoscedasticity_pass`.  

- [ ] T051 [US3] Implement `code/analysis/voxel_downsampler.py` to down‑sample the full‑brain mask, reducing voxel count by ≥ 50 % and writing `data/analysis/search_volume_mask.nii.gz`.  
  - **Verification**: Output mask file exists; voxel count ≤ 50 % of the original mask (checked via a script).  

- [ ] T058 [P] Add a final compliance check script `code/utils/verification_suite.py` that runs all contract‑validation commands and exits with status 0 only if every JSON/YAML artifact validates against its schema.  
  - **Verification**: Running `python -m code.utils.verification_suite` exits with status 0 on a clean repo; non‑zero otherwise.  

- [ ] T060 [P] Generate `data-model.md` from the ER diagram and schema definitions, and validate it against the specifications.  
  - **Path**: `data-model.md` (generated), `contracts/data-model.schema.yaml` (hypothetical)  
  - **Verification**: Script `code/utils/generate_data_model.py` runs and produces `data-model.md`; a contract test confirms the file exists and matches expected structure.  

- [ ] T061 [P] Pin random seeds globally (see T001) and verify via `code/utils/reproducibility_test.py`.  
  - **Verification**: Test script runs and asserts deterministic output across multiple invocations.  

- [ ] T062 [P] Run the Reference‑Validator Agent (see T002) as part of CI; fail the build if any citation is unverified.  
  - **Verification**: CI step executes `scripts/run_reference_validator.sh`; non‑zero exit aborts the pipeline.  