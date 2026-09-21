# Tasks: Neural Mechanisms Underlying Adaptive Decision-Making in Response to Social Feedback

**Input**: Design documents from `/specs/001-neural-mechanisms-adaptive-decision/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

<!--
 ============================================================================
 IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

 The /speckit-tasks command MUST replace these with actual tasks based on:
 - User stories from spec.md (with their priorities P1, P2, P3...)
 - Feature requirements from plan.md
 - Entities from data-model.md
 - Endpoints from contracts/

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directories (`data/raw`, `data/processed`, `data/models`, `code/preprocessing`, `code/modeling`, `code/analysis`, `code/utils`, `code/reporting`, `tests/unit`, `tests/integration`, `tests/contract`, `state`, `docs`) and initialize `__init__.py` files in `code/`, `tests/` packages.

- [X] T002 Initialize a Python project with dependencies (numpy, pandas, scipy, scikit-learn, nibabel, nilearn, pymc, numpyro, openneuro-py, pytest, pyyaml) in `requirements.txt` using a compatible modern Python version.
- [X] T003 [P] Configure linting (flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [X] T004 Setup `code/utils/io.py` for robust file loading and CSV/JSON parsing
- [X] T005 [P] Implement `code/utils/hashing.py` for `sha256sum` computation (utility function only)
- [X] T006 [P] Setup `code/utils/config.py` for environment configuration and seed management (numpy/pymc)
- [X] T006b [P] Implement `code/utils/runtime_estimator.py` to estimate runtime for MCMC sampling based on N and sample count. **Must be used by T024**.
- [X] T007 Create `data/` directory structure (`raw`, `processed`, `models`) and `state/` for artifact hashes
- [X] T008 Configure `pytest` with `conftest.py` for test fixtures and temporary data directories
- [X] T009 Setup logging infrastructure in `code/utils/logger.py` to track QC failures and model convergence

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw fMRI and behavioral data, perform motion correction/normalization, extract ROI time-series, and enforce QC thresholds.

**Independent Test**: The pipeline can be validated by running it on a small subset of dummy or sample data and verifying that output files contain the expected ROI time-series matrices and behavioral matrices with no missing values or motion artifacts exceeding the threshold.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for data validation in `tests/contract/test_data_validation.py` (verifies OpenNeuro ds structure: `sub-*/func/sub-*_task-social_bold.nii.gz` and `sub-*/beh/*.tsv` presence).
- [X] T011 [P] [US1] Integration test for ROI extraction in `tests/integration/test_roi_extraction.py` (verifies dimensions match timepoints)

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/preprocessing/data_validation.py` to verify presence of NIfTI and behavioral logs (private_belief, social_feedback, choice). **Updated**: Must explicitly verify ds003694 file structure (`sub-*/func/sub-*_task-social_bold.nii.gz`, `sub-*/beh/sub-*_task-social_beh.tsv`) and raise `FileNotFoundError` if missing. **Must run before T013**.
- [X] T013 [US1] Implement `code/preprocessing/data_download.py` to fetch OpenNeuro **ds003694** using `openneuro-py`. **CRITICAL SAFETY**: Must raise `FileNotFoundError` or `ConnectionError` immediately if fetch fails. **NO** `try/except` blocks that fall back to synthetic/mock data. If fetch fails, the run must FAIL LOUDLY. Include logic to exclude participants with missing assets (NIfTI, logs, motion) and write reasons to `state/exclusions.yaml`. **Must run after T012**.
- [X] T014 [US1] Implement `code/preprocessing/motion_correction.py` using **lightweight `nilearn` pipelines** (specifically `nilearn.image.resample_img`, `nilearn.preprocessing.clean_img`) for motion correction and normalization. **Do NOT use custom `scipy.optimize` implementations**. Must document all parameters used in `data/reports/motion_params.yaml`. **Must run after T013**.
- [X] T014b [US1] Implement `code/preprocessing/validate_motion_correction.py` to validate the output of T014 against standard `nilearn` defaults and ensure parameters are documented. **Must run after T014**.
- [X] T015 [US1] Implement `code/preprocessing/normalization.py` for spatial normalization to MNI space using `nilearn` with `MNI152NLin2009cAsym` template and `affine` registration.
- [X] T016 [US1] Implement `code/preprocessing/smoothing.py` for spatial smoothing with a moderate kernel width.
- [X] T017 [US1] Implement `code/preprocessing/roi_extraction.py` to extract BOLD signals from dlPFC, ventral striatum, and ACC masks using the **Harvard-Oxford Atlas** (specific coordinates defined in config). **CRITICAL SAFETY**: Must implement streaming/chunked processing (e.g., 50 timepoints at a time) to ensure memory usage stays < 6GB. Log the chunking strategy used. **Must run after T049**.
- [X] T018 [US1] Implement `code/preprocessing/qc_filter.py` to **enforce** exclusion of participants with >10% volumes exceeding 3mm translation (SC-001). **Must strictly prevent** these participants from being processed in downstream tasks. Log reasons to `state/exclusions.yaml`. **This is a hard gate before any downstream processing**.
- [X] T018b [US1] Implement `code/preprocessing/qc_reporter.py` to calculate the final exclusion rate against the SC-001 threshold (10% volumes > 3mm) using the **enforced** set from T018, and **generate `data/reports/qc_summary.json`** with stability metrics. **Must also generate `state/exclusions.yaml`** containing the list of excluded participant IDs and reasons. **Must run after T018**.
 - **Artifact Schema**: `data/reports/qc_summary.json` must contain:
 ```json
 {
 "total_participants": 0,
 "excluded_count": 0,
 "exclusion_rate": 0.0,
 "threshold_volumes_percent": 10.0,
 "threshold_motion_mm": 3.0,
 "exclusion_reasons": ["motion", "missing_data"]
 }
 ```
 - **Artifact Schema**: `state/exclusions.yaml` must contain:
 ```yaml
 excluded_participants:
   - sub-01: "motion > 3mm"
   - sub-02: "missing behavioral logs"
 ```
 - **Verification**: Task must verify that `data/reports/qc_summary.json` and `state/exclusions.yaml` exist, are valid, and contain all required keys before marking as complete.
 - [X] T019 [US1] Create `code/main.py` entry point (setup only) - initializes config and logging, does not run pipeline logic yet.
- [X] T049 [US1] Implement `code/preprocessing/streaming_loader.py` to load OpenNeuro ds003694 files from `data/raw` using `nibabel` and `nilearn` in chunks (e.g., 50 timepoints or 1 participant at a time). **Must process the full dataset** in chunks to compute motion statistics and ROI signals without loading all data into RAM. **Must log** the exact chunking strategy and total participants processed. **If** the full dataset cannot be processed within the 6h/GB RAM limit, **then** this task must implement a well-defined sampling strategy (e.g., `itertools.islice` first N=30 participants with a fixed seed) and explicitly document the sample size and power limitation in `data/reports/sampling_policy.json`. **Do NOT** use a synthetic or toy dataset as a fallback. **Must run after T013, before T017**.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Computational Modeling of Belief Updating (Priority: P2)

**Goal**: Implement a hierarchical Bayesian model to estimate individual belief-updating rates (alpha) and validate convergence.

**Independent Test**: The model can be tested by feeding it synthetic data generated from a *different* generative process with noise characteristics distinct from the fitting model, verifying that the posterior estimates converge to the ground truth within a defined error margin.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Contract test for model convergence in `tests/contract/test_model_convergence.py` (verifies R-hat < 1.01 and ESS > 400).
- [X] T022 [P] [US2] Integration test for synthetic data recovery in `tests/integration/test_synthetic_recovery.py`

### Implementation for User Story 2

- [X] T023 [P] [US2] Implement `code/modeling/synthetic_data_generator.py` to create ground-truth behavioral data for validation.
 - **Deliverables**: A CSV file `data/synthetic/ground_truth.csv` with columns: `subject_id`, `true_alpha`, `true_precision`, `generated_choices`.
 - **Verification**: The model (T024) must recover `true_alpha` within ±0.1 of the ground truth for ≥90% of synthetic subjects.
- [X] T024a [US2] Implement `code/modeling/n_valid_calculator.py` to read `state/exclusions.yaml` (from T018b) and calculate `N_valid` (participants passing motion QC). Write `N_valid` to `state/n_valid.yaml`. **Must run after T018b**.
- [X] T024 [US2] Implement `code/modeling/belief_updater.py` using `pymc` with `numpyro` CPU backend. **CRITICAL SAFETY**: Must read `N_valid` from `state/n_valid.yaml` (output of T024a). **Must include** a memory check that aborts sampling if RAM usage > 70% (7GB) to prevent OOM on the runner. **Must calculate** the required number of MCMC draws (e.g., Multiple chains, 2000 samples) to ensure runtime < 6h using `code/utils/runtime_estimator.py` (T006b). If N_valid is too large for 6h, **reduce the number of samples/draws** rather than excluding participants. **Must run after T024a**. **Note**: This task atomically implements memory guarding, runtime estimation, and sample reduction logic.
- [X] T025 [US2] Implement `code/modeling/validation.py` to check convergence (R-hat, ESS) and handle non-convergence (multiple restart attempts up to 3).
- [X] T025b [US2] Implement `code/modeling/convergence_reporter.py` to aggregate convergence logs. **Must calculate** the global convergence rate against the `N_valid` (from T024a) using results from **T024 only**.
 - **Metric**: `convergence_rate = converged_count / N_valid (original count from T024a)`. **Do NOT include** exclusions from T025c in the denominator.
 - Generate `data/models/convergence_report.json`. **Must run after T025**.
 - **Note**: This task reports the rate against `N_valid`. Non-converging participants are excluded from subsequent analysis in T025c, but the rate metric itself uses the original `N_valid` as per SC-002.
- [X] T025c [US2] Implement `code/modeling/failure_handler.py` to handle convergence failure: if a participant fails to converge after 3 restarts, **exclude them from the dataset used in T027** and flag them for sensitivity analysis in `data/models/failure_log.json`. **Do NOT raise a fatal error**. **Must run after T025b**.
- [X] T028 [US2] Implement `code/main.py` logic for P2 integration: Read convergence reports (T025b), filter non-converging participants (via T025c), and prepare valid participant list for T027. **Sequential Dependency: Must run after T025b, before T027**.
 - **Artifact**: Must generate `state/valid_participants.yaml` containing the list of participant IDs that passed both motion QC and model convergence.
 - **Verification**: Unit test must verify that participants listed in `data/models/failure_log.json` are NOT present in `state/valid_participants.yaml`.
- [X] T027 [US2] Create `code/modeling/model_output.py` to save individual alpha parameters and group-level hyperparameters to `data/models/` for valid participants only (input filtered by T028).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Neural-Behavioral Correlation and Hypothesis Testing (Priority: P3)

**Goal**: Perform GLM analysis to link neural activation to computational parameters and apply FDR-corrected permutation testing.

**Independent Test**: The analysis can be tested on simulated data where the correlation between a specific ROI and the updating parameter is known, verifying that the statistical test correctly identifies the significant association.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US3] Contract test for GLM correlation in `tests/contract/test_glm_correlation.py` (verifies parametric modulation output).
- [X] T030 [P] [US3] Integration test for permutation testing in `tests/integration/test_permutation_test.py`

### Implementation for User Story 3

#### Integration Prerequisites (Must Run First)
**Purpose**: Establish data flow and unified inputs for all downstream analysis tasks. **T037a and T037b MUST complete before T031-T036.**

- [X] T037a [US3] Implement `code/analysis/loader.py` to load filtered alpha parameters (from T027 via T028) and ROI time-series (from T017) into a unified dataframe. **Dependencies: Must run after T027, T028, T025b**. **Must run before T031-T036**.
 - **Artifact**: Must save the unified dataframe to `data/processed/unified_analysis_data.parquet`.
 - **Verification**: Verify shape matches `N_valid` (from T024a) and column count is 5 (subject_id, alpha, dlPFC_signal, VS_signal, ACC_signal).
- [X] T037b [US3] Implement `code/analysis/main_analysis.py` to orchestrate data flow from P2 to P3 using `loader.py`. **Must run before T031-T036**.
 - **Artifact**: Must generate `data/analysis/analysis_run_log.json` documenting the execution order and data sources.
 - **Verification**: Verify that T031-T036 are triggered in sequence and no errors occur.

#### Core Analysis Implementation
**Purpose**: Implement the statistical models and hypothesis tests required by FR-003, FR-004, and FR-005. **All tasks in this section MUST run after T037a.**

- [X] T031 [US3] Implement `code/analysis/glm_analysis.py` to perform GLM analysis with **parametric modulation by feedback discrepancy** and extract beta values (satisfies FR-003). **Verification**: Output must contain beta values for parametric modulation of feedback discrepancy. **Must run after T037a**.
- [X] T032 [US3] Implement `code/analysis/partial_correlation.py` to compute partial correlation between neural activation and alpha (controlling for input discrepancy) and **output the correlation coefficient (r) for SC-003 verification**. **Must run after T037a**.
- [X] T033 [US3] Implement `code/analysis/permutation_test.py` for voxel-wise inference with **A sufficient number of permutations** (reduced for CPU feasibility) and **joint FDR correction (Benjamini-Hochberg)** across the entire search volume (q < 0.05) to control family-wise error (satisfies FR-004).
 - **Internal Verification**: The script must verify that FDR correction was applied correctly and write `data/analysis/fdr_status.json` with a boolean `fdr_applied` and the `q_threshold`.
 - **CRITICAL SAFETY**: Must use an iterative permutation approach with early stopping if FDR threshold is met to ensure runtime < 6h. **Must run after T037a**.
 - **Dependencies**: Must run after T027 (for alpha parameters) and T037a (for data loading).
 - **Note**: This task atomically implements iterative permutation, early stopping, and FDR correction logic.
- [X] T034 [US3] Implement `code/analysis/confound_control.py` to include motion parameters and aCompCor components as regressors
- [X] T035 [US3] Implement `code/analysis/loso_validation.py` for Leave-One-Subject-Out cross-validation to prevent tautology

#### Sensitivity & Reporting
**Purpose**: Verify robustness and generate final outputs.

- [X] T036a [US3] Implement `code/analysis/sensitivity_sweeper.py` to re-run correlation logic for a sweep of **belief-updating rate (alpha) threshold/cutoff values** {0.01, 0.05, 0.1} (a parameter in the computational model's update equation) to verify robustness of the headline correlation rates (FR-006); depends on T037a (filtered alpha set from integration loader). **Must NOT re-run the model**, but rather apply different decision thresholds to the existing alpha estimates to test classification robustness.
 - **Verification**: Must output `data/analysis/sensitivity_stability_report.csv` containing stability metrics (change < 0.05) as required by FR-006.
- [X] T036b [US3] Implement `code/analysis/sensitivity_reporter.py` to aggregate sweep results and generate `data/analysis/sensitivity_stability_report.csv` containing stability metrics (change < 0.05) as required by FR-006
- [X] T038a [US3] Implement `code/reporting/generate_stats.py` to compile final statistics into `results/final_stats.json`
- [X] T038b [US3] Implement `code/reporting/generate_figures.py` to create figures and save to `results/figures/`
- [X] T038c [US3] Implement `code/reporting/generate_research_doc.py` to compile `docs/research.md` with all results

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T039a [P] Update `README.md` with sections: Installation, Data Download, Usage, and Troubleshooting
- [X] T039b [P] Generate API documentation for modules: preprocessing, modeling, analysis in `docs/api/`
- [X] T040a [Sequential] Implement `code/modeling/belief_updater.py` refactoring for CPU memory optimization (chunking, masking) with a target peak RAM usage < 6GB. **Must run after T024**.
 - **Verification**: Run memory profiler to confirm peak RAM < 6GB on N=30 dataset.
- [X] T041a [P] Implement `code/utils/runtime_reporter.py` to generate `results/runtime_report.json` verifying the total pipeline runtime < 6h. **Must run after T038c**.
- [X] T042 [P] Additional unit tests in `tests/unit/` for edge cases (motion exclusion, non-convergence)
- [X] T043 Run `quickstart.md` validation to ensure end-to-end reproducibility
- [X] T020 [Terminal] Implement `code/utils/hash_artifacts.py` to compute sha256 checksums for **all final files** in `data/` and `code/` and store them in `state/artifact_hashes.yaml` in the required format. **Must run AFTER T038c (all data processing and model generation complete).** **Note: This is a terminal task, NOT parallel.**
- [X] T044 [P] Implement `code/utils/runtime_stress_test.py` to perform a **runtime stress test and convergence timeout check** on a representative sample (**N=5 participants selected by median motion**) to verify the 6-hour constraint before full execution.
 - **Artifact**: Must generate `results/stress_test_report.json` with pass/fail status.
 - **Verification**: Verify that the test fails if runtime > 6h.
- [X] T046 [P] Implement `docs/reproducibility_checklist.md` documenting the exact steps, seeds, and environment variables required to reproduce the final `results/final_stats.json` from raw data, explicitly citing the `state/artifact_hashes.yaml` for data integrity verification.
- [X] T047 [P] Implement `code/analysis/power_analyzer.py` to perform a post-hoc power analysis on the final `results/final_stats.json` (correlation r, N) to estimate achieved power and report it in `data/reports/power_analysis.json`. **Must run after T038a**.
- [X] T048 [P] Implement `code/analysis/assumption_checker.py` to verify normality and homoscedasticity assumptions of the GLM residuals and partial correlation, generating `data/reports/assumption_checks.json` with pass/fail status and diagnostic plots. **Must run after T032**.
- [X] T051 [US3] Implement `code/analysis/voxel_downsampler.py` to prepare the search volume for T033. **Strategy**: Load the full brain mask, down-sample to a standard resolution (e.g., isotropic) or apply a pre-defined MNI mask to reduce the number of voxels, ensuring the permutation test (T033) can run within 6h/7GB RAM while maintaining **voxel-wise coverage** (not ROI-level). **Must run after T037a, before T033**.
 - **Artifact**: Must generate `data/analysis/search_volume_mask.nii.gz` (down-sampled mask).
 - **Verification**: Verify that the mask covers the full brain volume (within resolution constraints) and that the number of voxels is reduced by at least 50% compared to the original.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable
 - **CRITICAL**: T032 (Partial Correlation) MUST run AFTER T024 (Model Fitting) to ensure alpha parameters exist.
 - **CRITICAL**: T031 (GLM) MUST run AFTER T017 (ROI Extraction) to ensure BOLD signals exist.
 - **CRITICAL**: T037a/T037b (Integration) MUST run BEFORE T031-T036 to establish data flow.
 - **CRITICAL**: T037a depends on T027, T028, T025b.
 - **CRITICAL**: T051 (Voxel Downsampling) MUST run BEFORE T033 (Permutation Test).

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- **Main.py Execution**: T019 (Init) -> T028 (P2 Logic) -> T037 (P3 Logic) are **SEQUENTIAL** modifications to `code/main.py` to prevent parallel conflicts.

### Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data validation in tests/contract/test_data_validation.py"
Task: "Integration test for ROI extraction in tests/integration/test_roi_extraction.py"

# Launch all models for User Story 1 together:
Task: "Implement data_validation.py"
Task: "Implement data_download.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Modeling)
 - Developer C: User Story 3 (Analysis)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Constraint Reminder**: All tasks must run on CPU-only (limited cores, limited RAM). No GPU, no 8-bit quantization. Use `numpyro` backend for `pymc`.
- **Data Integrity**: No synthetic data for final results. **No synthetic fallbacks** in data loading (T013).
- **Main.py Execution**: T019 (Init) -> T028 (P2 Logic) -> T037 (P3 Logic) are sequential. Do not run T028 or T037 in parallel.
- **Hashing**: T020 runs only after all processing (Phase N) to hash final artifacts. **Not parallel**.
- **Runtime Check**: T044 must be executed to verify the 6-hour constraint before full-scale runs.
- **Safety**: T013 (No Synthetic Fallback), T017 (Memory Chunking), T024 (Memory Check + Sample Reduction), T033 (Runtime Cap + FDR) are **active requirements** in the current plan, not deferred tasks.
- **Convergence**: T025c excludes non-converging participants but does not abort the project. T025b measures convergence against the original N_valid.
- **Standard Pipelines**: T014 uses lightweight `nilearn` pipelines, validated by T014b.
- **FDR Correction**: T033 uses joint FDR correction across the entire search volume (down-sampled via T051) and includes internal verification.
- **GLM Modulation**: T031 explicitly includes parametric modulation by feedback discrepancy.
- **Data Flow**: T037a must complete before T031 and T032. T024a must complete before T024.
- **Phase N+1 Removed**: All safety and integrity tasks previously deferred to a hypothetical "Phase N+1" have been integrated into the current execution plan (T013, T017, T024, T033, T051) to ensure executability and compliance with Constitution Principles.
- **Reproducibility**: T046 ensures the final report is fully reproducible by documenting the exact environment and data hashes required.
- **Sensitivity**: T036a sweeps the belief-updating rate (alpha) parameter to verify robustness of the correlation rate.
- **Power Analysis**: T047 addresses the need to quantify statistical power post-hoc, ensuring the study's conclusions are supported by adequate sensitivity.
- **Assumption Checking**: T048 ensures the validity of statistical inferences by verifying the underlying assumptions of the models used.
- **Runtime Management**: Runtime is managed by reducing MCMC samples (T024) and voxel count (T051) rather than excluding participants.
- **Tag Clarification**: T020 is marked [Terminal] (not [P]) to reflect its sequential nature. T040a is marked [Sequential] to reflect its dependency on T024.
- **Atomization**: T024b, T024c, T024d and T033b, T033c have been merged into T024 and T033 respectively to resolve circular dependencies and ensure coherent logic implementation.
- **Voxel-Wise Compliance**: T051 ensures voxel-wise analysis is performed by down-sampling the search volume rather than falling back to ROI-level analysis, satisfying FR-004.

---

## Phase N+1: Review-Driven Revisions & Gap Resolution

**Purpose**: Address specific reviewer concerns regarding data streaming, dataset specification, and computational feasibility that were not fully resolved in the initial pass.

### Review Concern: Real Dataset Streaming Strategy
> **Reviewer Note**: The plan mentions "sampled" data but does not explicitly task the streaming of the *full* real dataset (OpenNeuro ds003694) in chunks. Relying on a fixed small sample without a streaming strategy risks missing population-level effects and violates the "Real data + real results only" principle if the sample is arbitrary.
> **Action**: Task must explicitly implement streaming of the full dataset to calculate statistics online, falling back to a defined sample only if the full stream is computationally impossible.

- [X] T049 [US1] Implement `code/preprocessing/streaming_loader.py` to load OpenNeuro ds003694 files from `data/raw` using `nibabel` and `nilearn` in chunks (e.g., 50 timepoints or 1 participant at a time). **Must process the full dataset** in chunks to compute motion statistics and ROI signals without loading all data into RAM. **Must log** the exact chunking strategy and total participants processed. **If** the full dataset cannot be processed within the 6h/7GB RAM limit, **then** this task must implement a well-defined sampling strategy (e.g., `itertools.islice` first N=30 participants with a fixed seed) and explicitly document the sample size and power limitation in `data/reports/sampling_policy.json`. **Do NOT** use a synthetic or toy dataset as a fallback. **Must run after T013, before T017**.

### Review Concern: Explicit Dataset Specification
> **Reviewer Note**: The plan references "OpenNeuro ds00XXXX" and "ds003694" but the download task (T013) is generic. The execution stage needs a concrete, verified URL or dataset ID to avoid guessing.
> **Action**: Task must hardcode the specific dataset ID and validation logic for ds003694.

- [X] T012 [US1] Updated `code/preprocessing/data_validation.py` to explicitly target **OpenNeuro ds003694**. **Must** verify the presence of specific files: `sub-*/func/sub-*_task-social_bold.nii.gz` and `sub-*/beh/sub-*_task-social_beh.tsv`. **Must** raise a `FileNotFoundError` with a clear message if `ds003694` structure is not found. **Do NOT** attempt to guess other datasets. **Must** write the specific dataset ID used to `state/dataset_manifest.json`. **Must run before T013**.

### Review Concern: Computational Feasibility of Full Voxel-Wise Analysis
> **Reviewer Note**: Running 5000 permutations on a full brain volume (voxel-wise) with 30 participants on a 2-core/7GB CPU runner is likely to exceed the 6-hour limit or cause OOM, even with early stopping. The plan assumes it will work but does not provide a concrete fallback or scaling strategy.
> **Action**: Task must implement a "CPU-safe" fallback that switches to ROI-level analysis if the voxel-wise permutation test hits resource limits.

- [X] T051 [US3] Implement `code/analysis/voxel_downsampler.py` to prepare the search volume for T033. **Strategy**: Load the full brain mask, down-sample to a standard resolution (e.g., 4mm isotropic) or apply a pre-defined MNI mask to reduce the number of voxels, ensuring the permutation test (T033) can run within 6h/7GB RAM while maintaining **voxel-wise coverage** (not ROI-level). **Must run after T037a, before T033**.
 - **Artifact**: Must generate `data/analysis/search_volume_mask.nii.gz` (down-sampled mask).
 - **Verification**: Verify that the mask covers the full brain volume (within resolution constraints) and that the number of voxels is reduced by at least 50% compared to the original.

