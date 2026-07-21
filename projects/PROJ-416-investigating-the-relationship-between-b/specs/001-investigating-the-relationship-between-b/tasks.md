# Tasks: Investigate Brain Network Dynamics and VR Therapy Response

**Input**: Design documents from `/specs/416-brain-network-dynamics/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

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

 Tasks MUST be organized by user story so each story can:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan: Create directories `code/`, `code/data/`, `code/analysis/`, `data/raw/`, `data/processed/`, `data/metrics/`, `reports/`, `tests/unit/`, `tests/integration/`, `docs/`; create files `requirements.txt`, `code/main.py`, `code/config.py`, `tests/conftest.py`.
- [X] T002 Initialize Python 3.10 project with `nibabel`, `nilearn`, `scikit-learn`, `networkx`, `pandas`, `numpy`, `matplotlib`, `scipy`, `pytest`
- [X] T003 [P] Configure linting (flake8/black) and formatting tools
- [ ] T001a [P] [Research] Identify and verify a valid OpenNeuro dataset ID containing both resting-state fMRI and paired pre/post clinical anxiety scores. 
    - Search OpenNeuro for datasets matching the inclusion criteria (anxiety disorder, VR therapy context if available, or general anxiety with fMRI).
    - Verify the dataset has the required variables: `pre_treatment_score`, `post_treatment_score`, `motion_metrics`.
    - Write the verified ID and access details to `data/verified_sources.json` in the format: `{"openneuro_id": "ds-XXXX", "verified_date": "YYYY-MM-DD", "notes": "..."}`.
    - This task MUST be completed before T012 or T041 can proceed.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup `data/raw`, `data/processed`, `data/metrics` directory structure with `.gitignore` rules
- [X] T005 [P] Implement `code/data/checksum.py` for SHA256 verification of downloaded data
- [X] T006 [P] Setup `code/main.py` orchestration entry point with argument parsing
- [X] T007 Create `code/config.py` for environment variables (OpenNeuro ID, paths, seeds)
- [X] T008 Implement `code/utils/logging.py` with structured logging for pipeline provenance
- [X] T009 Setup `tests/unit` and `tests/integration` directory structures

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Download and Preprocess fMRI Data (Priority: P1) 🎯 MVP

**Goal**: Download resting-state fMRI data from OpenNeuro, validate variable presence (pre/post scores), preprocess (motion, slice, norm), and enforce strict exclusion criteria.

**Independent Test**: Run on a single subject's data; verify output NIfTI files exist, dimensions match expected space, and motion metrics are logged.

### Test Implementation for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST. Ensure they FAIL before implementing the code they test.

- [X] T010 [P] [US1] Unit test for `code/data/validate.py` to ensure it halts on missing `pre_treatment_score` or `post_treatment_score` in metadata
- [X] T011 [P] [US1] Unit test for `code/data/preprocess.py` to verify motion threshold logic (>3mm/3°) flags subjects correctly

### Code Implementation for User Story 1

- [X] T012 [US1] Implement `code/data/download.py` to fetch data from OpenNeuro using the ID from `data/verified_sources.json` (populated by T001a). 
    - If the ID is missing or invalid, raise a `FatalError` immediately and log "Missing verified dataset source".
    - Do NOT attempt to fetch from arbitrary IDs.
- [X] T013 [US1] Implement comprehensive validation logic in `code/data/validate.py`: 
    1. Check for paired pre/post fMRI and clinical scores at the dataset level; verify the instrument is a validated anxiety scale (e.g., GAD-7, HAM-A) with citable documentation or halt with fatal error (FR-011, FR-009).
    2. If dataset variables (pre/post scores) are missing, halt with "Missing required variable: [variable_name]" (FR-011, SC-001).
    3. Check for the presence of specific confounders (medication status, age, comorbidities) in metadata; update model configuration to conditionally include detected confounders as covariates.
    4. Log a limitation in `reports/limitations.md` if expected confounders are missing from metadata (FR-013).
    5. Iterate through subjects, check for individual completeness (pre AND post scans present), exclude ONLY incomplete subjects, and log the exclusion reason (Edge Case: Incomplete Scans).
    *Must complete BEFORE T014*.
- [X] T014 [US1] Implement `code/data/preprocess.py` for motion correction, slice timing, and normalization using `nilearn` (CPU-optimized). 
    - Use `nilearn.image.resample_img` and `nilearn.image.smooth_img` with specific parameters: smoothing kernel appropriate for the data resolution, high-pass filter 0.01 Hz.
    - Target a feasibility subset of N=10 subjects for CI (Spec FR-002 targets N=20; pipeline logic must support N=20 but CI runs N=10).
    - Output preprocessed NIfTI files to `data/processed/`.
- [X] T015 [US1] Implement quality control in `code/data/preprocess.py` (or `code/data/qc.py`) to:
    1. Calculate Mean Framewise Displacement (FD) for each subject.
    2. Exclude subjects if translation > 3mm OR rotation > 3° (distinct checks as per FR-002, SC-002).
    3. Extract clinical confounders (medication, age, comorbidities) from metadata if available.
    4. Save `mean_fd` (float), `translation_mm`, `rotation_deg`, and clinical confounders to `data/metrics/network_metrics.csv` as mandatory columns. 
    *Must run AFTER T014 to process the output NIfTI, but BEFORE US2 consumes the metrics*.
- [X] T016 [US1] Add logging for excluded subjects and specific exclusion reasons in `logs/preprocessing.log`
- [X] T017 [US1] Implement `code/data/save_metadata.py` to store subject list, exclusion reasons, and motion metrics in `data/metrics/subject_info.json` with schema: `{"subject_id": "...", "status": "included|excluded", "exclusion_reason": "..."}`.
    *Must run AFTER T015 to capture final exclusion decisions. This is the strict final step of US1*.

**Checkpoint**: At this point, User Story 1 is fully functional ONLY after T017 completes.

---

## Phase 4: User Story 2 - Compute Network Metrics (Priority: P2)

**Goal**: Compute functional connectivity matrices and derive network properties (modularity, global/local efficiency) using a standard atlas (AAL/Schaefer).

**Independent Test**: Run on a single preprocessed subject; verify matrices and metrics exist with values in expected mathematical bounds (Q≥0, Eff≥0).

**⚠️ BLOCKING DEPENDENCY**: This phase CANNOT start until T017 (US1) is complete. US2 requires preprocessed NIfTI files from US1.

### Test Implementation for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for `code/analysis/network.py` to ensure modularity Q is non-negative and efficiency values are finite
- [X] T019 [P] [US2] Integration test for `code/analysis/network.py` to verify output CSV contains all three metrics per subject

### Code Implementation for User Story 2

- [X] T020 [US2] Implement `code/analysis/network.py` to extract ROI time series using AAL or Schaefer atlas (parcellations with a moderate number of regions). 
    - **Dependency**: Requires preprocessed NIfTI files from T014 (US1).
- [X] T021 [US2] Implement functional connectivity matrix calculation (Pearson correlation) in `code/analysis/network.py`
- [X] T022 [US2] Implement network metric calculation (Modularity Q, Global Efficiency, Local Efficiency) using `bctpy` (Brain Connectivity Toolbox Python) to ensure mathematical correctness and compliance with SC-003 bounds
- [X] T023 [US2] Add NaN/Infinity handling in `code/analysis/network.py` to exclude invalid metrics and log events
- [X] T024 [US2] Save connectivity matrices and metrics to `data/metrics/network_metrics.csv` and `data/metrics/matrices/`
- [X] T025 [US2] Implement `code/analysis/validate_metrics.py` to enforce bounds (Q≥0, Eff≥0) and halt on systematic failures

**Checkpoint**: At this point, At least User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Reporting (Priority: P3)

**Goal**: Perform ANCOVA analysis (Post ~ Pre + Metric), apply FDR correction, run sensitivity analysis, and generate diagnostic plots. Implement Univariate Models as primary path, with Ridge regression as conditional fallback per Spec.

**Independent Test**: Run on sample data; verify regression coefficients, p-values, effect sizes, and plots are generated.

**⚠️ BLOCKING DEPENDENCY**: This phase CANNOT start until T024 (US2) is complete. US3 requires network metrics from US2.

### Test Implementation for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Unit test for `code/analysis/stats.py` to verify FDR correction logic and VIF calculation
- [X] T027 [P] [US3] Unit test for `code/analysis/plots.py` to ensure scatter plots and residuals are generated without error

### Code Implementation for User Story 3

- [X] T028 [US3] Implement `code/analysis/stats.py` to perform ANCOVA (Post ~ Pre + Metric + Confounds + FD_Covariate) with `statsmodels`.
    - **Dependency**: Requires network metrics from T024 (US2) and motion metrics from T015 (US1).
- [X] T029 [US3] Implement VIF calculation in `code/analysis/stats.py`. 
    - **PRIMARY PATH**: If VIF <= 5, use standard OLS regression with FDR correction (Plan preference).
    - **FALLBACK PATH**: If VIF > 5, apply Ridge regression with lambda=1.0 as required by Spec FR-005/FR-012. If the Ridge model fails to converge or R² < 0.05, switch to separate univariate models with FDR correction.
    - Log the model type used (OLS or Ridge) in the output.
- [X] T029b [US3] Implement logic in `code/analysis/stats.py` to append a Methodological Note to `reports/results.md`, explicitly documenting the primary path (Univariate) and the conditional fallback (Ridge) as implemented.
- [X] T030 [US3] Implement multiple comparison correction (FDR/Bonferroni) in `code/analysis/stats.py` for >1 metric hypothesis
- [X] T031 [US3] Implement power analysis in `code/analysis/stats.py` using `statsmodels.stats.power.FTestPower.solve_power` with parameters: alpha=0.05, power=0.8, effect_size=0.15 (standard convention for small effects in neuroimaging, Cohen 1988; override via config if research phase determines otherwise).
    - HALT if N < 5.
    - FLAG limitation if 5 <= N < 10.
    - Calculate the 'minimum N required' value.
    - **Output**: Save the full calculation details (including `min_N_required`, `effect_size`, `alpha`, `power`) to `data/metrics/power_analysis.json` with the following schema: `{"min_N_required": <int>, "effect_size": <float>, "alpha": <float>, "power": <float>, "method": "FTestPower"}`.
- [X] T031b [US3] Implement logic in `code/analysis/stats.py` to consume `data/metrics/power_analysis.json` generated by T031, and include the `min_N_required` value and method details in the final report generation.
- [X] T032 [US3] Implement sensitivity analysis in `code/analysis/stats.py` sweeping motion thresholds over a range of magnitudes (justification: a stricter standard for high-quality fMRI is adopted, while the Spec threshold remains at 3.0mm) and p-values over {, 0.1} and other conventional significance thresholds and reporting variation in outcome rates (FR-010, SC-006).
- [X] T033 [US3] Implement `code/analysis/plots.py` to generate scatter plots with regression lines and residual diagnostics
- [X] T034 [US3] Generate final report in `reports/results.md` with associational framing (FR-008); include logic to check `metadata.study_design` for string 'randomized' OR `metadata.randomized` for boolean true; if neither exists OR if fields are missing, default to framing findings as ASSOCIATIONAL (SC-005); include all metrics, coefficients, and the minimum N value.
- [X] T035 [US3] Save all statistical outputs (coefficients, p-values, VIF, power calc, min_N) to `data/metrics/statistical_results.csv` with columns: `subject_id`, `metric`, `coefficient`, `p_value_uncorrected`, `p_value_corrected`, `vif`, `min_N_required`, `model_type`.
- [ ] T045 [US3] [Integration] Implement `tests/integration/test_data_flow.py` to verify the output of T015 (motion metrics) is correctly consumed by T028 (stats) as a covariate, and that T024 (network metrics) is correctly consumed by T028.
    - **Moved from Phase N+1 to Phase 5** to ensure integration testing happens during implementation.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T036 [P] Update `docs/quickstart.md` with execution instructions for N=10 subset
- [X] T037a [P] Refactor code to add comprehensive docstrings to all public functions in `code/analysis/` and `code/data/`
- [X] T037b [P] Refactor `code/data/preprocess.py` to reduce cyclomatic complexity to <=10. Target functions: `preprocess_subject`, `calculate_motion_metrics`.
- [X] T038 Performance optimization for preprocessing loop (ensure N=10 completes <6h)
- [X] T039 [P] Add unit tests for `code/analysis/stats.py` edge cases (collinearity, NaNs)
- [X] T040 Run `quickstart.md` validation to ensure end-to-end flow works on CI

---

## Phase N+1: Revision & Review Resolution (Addressing Plan/Spec Conflicts)

**Goal**: Resolve specific methodological conflicts identified in the plan review and ensure strict adherence to data hygiene rules.

- [ ] T041 [US1] Implement a strict "Verified Source" gate in `code/data/download.py`: Read the OpenNeuro ID from `data/verified_sources.json` (populated by T001a). If the ID is missing or invalid, the script MUST raise a `FatalError` immediately and exit. Do NOT attempt to fetch from arbitrary IDs. This resolves the "STATUS: BLOCKED" issue in the plan by enforcing the gate before any network calls.
- [ ] T043 [US1] Update `code/data/validate.py` to strictly enforce the "Real Data Only" rule: Remove any `try/except` blocks that fallback to synthetic data generation. If `nilearn` or `bids` fails to load a specific subject's data, the pipeline must crash with a detailed error log, not a synthetic substitute. Add a unit test `tests/unit/test_validate.py` that asserts the process exits with code 1 on a simulated download failure.
- [ ] T044 [US3] Enhance `code/analysis/stats.py` sensitivity analysis (T032) to explicitly sweep the motion threshold over a specific set of representative values and p-value over {0.05, 0.1} and a stricter threshold as defined in the revised constraints, and generate a summary table in `reports/sensitivity_analysis.md` showing the count of significant findings at each threshold.

**Note**: Task T042 has been removed as the methodological conflict is resolved by the code logic in T029 (Univariate primary, Ridge fallback).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Revision (Phase N+1)**: Depends on completion of all core implementation tasks (Phase 3-5) to verify and patch specific logic.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **BLOCKING DEPENDENCY**: Requires US1 output (preprocessed data from T014)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **BLOCKING DEPENDENCY**: Requires US2 output (network metrics from T024)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Validation before processing
- Processing before metrics
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for code/data/validate.py"
Task: "Unit test for code/data/preprocess.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/download.py"
Task: "Implement code/data/validate.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (Download -> Preprocess -> QC)
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
 - Developer B: User Story 2 (Network Metrics) - *Requires US1 output*
 - Developer C: User Story 3 (Stats) - *Requires US2 output*
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
- **Critical Constraint**: All data processing must fit within 2 CPU cores, 7GB RAM, 14GB disk, and 6 hours. Use N=10 subset for CI.
- **Critical Constraint**: No GPU/CUDA. No 8-bit/4-bit quantization. No deep learning training.
- **Critical Constraint**: If dataset variables (pre/post scores) are missing, the pipeline MUST halt immediately with "Missing required variable: [variable_name]" (FR-011).
- **Critical Constraint**: Implement Univariate Models as PRIMARY path. Implement Ridge regression as conditional FALLBACK (VIF > 5) as per FR-005/FR-012.
- **Critical Constraint**: Sensitivity analysis must sweep motion thresholds {2.0, 3.0} mm and p-values {0.01, 0.05, 0.1}.
- **Critical Constraint**: Report must frame findings as ASSOCIATIONAL if `metadata.study_design` is not 'randomized' (string) OR `metadata.randomized` is not true (boolean), or if fields are missing.
- **Critical Constraint**: G*Power calculation must explicitly save 'minimum N required' to `data/metrics/power_analysis.json` and `reports/results.md` (SC-004).
- **Critical Constraint**: T045 (Data Flow Verification) is now part of Phase 5 to ensure integration testing happens during implementation.