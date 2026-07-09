# Tasks: Investigating the Relationship Between Brain Network Dynamics and Baseline Working Memory Performance

**Input**: Design documents from `/specs/359-investigating-the-relationship-between-baseline-working-memory-performance/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US0, US1, US2, US3)
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
 - User stories from spec.md (with their priorities P0, P1, P2, P3...)
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

- [ ] T001 Create project structure per implementation plan: `projects/PROJ-359-investigating-the-relationship-between-b/code/` with `src/`, `tests/`, `data/raw/`, `data/preprocessed/`, `data/results/`, `data/logs/`, `data/motion/`
- [ ] T002 Initialize Python 3.11 project with pinned dependencies in `requirements.txt` (fMRIPrep 23.1.3, Nilearn, NetworkX, bctpy, scikit-learn, statsmodels, pandas, matplotlib, pyyaml, openneuro-py)
- [ ] T003 [P] Configure linting (ruff), formatting (black), and pre-commit hooks for reproducibility

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `src/utils.py` with logging infrastructure, JSON log writers, and deterministic seeding (`RANDOM_SEED` env var)
- [ ] T005 [P] Implement `src/download.py` to fetch `ds000278` (OpenNeuro HCP rs-fMRI release) via OpenNeuro API. **MANDATORY**: This task MUST download `ds000278` which contains the required resting-state scans (`sub-*/func/*_space-MNI_desc-preproc_bold.nii.gz`). The Spec (FR-001) and Plan have been updated to reflect this dataset. Verify checksums and handle HTTP errors. If `ds000278` is unavailable or lacks resting-state data, abort with error: "Required resting-state dataset ds000278 not found."
- [ ] T006 Create `contracts/dataset_schema.schema.yaml`, `contracts/pipeline_output.schema.yaml`, `contracts/regression_output_schema.schema.yaml`, and `contracts/regression_result.schema.yaml` for validation
- [ ] T007 [Depends on T005 completion] Implement `src/validators.py` for ID matching (FR-009) and behavioral column verification (FR-012) with fatal error on mismatch. **Dependency Note**: This task depends on T005 completion; the validator MUST NOT run before the download finishes.
- [ ] T008 Setup Docker execution wrapper for fMRIPrep with `--memory 5g --nprocs 1 --mem_mb 4500` to fit CI constraints (FR-002). **Note**: Increased from 4g to 5g to ensure OS headroom on 7GB runner.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 0 - Data Validation & Preprocessing Integrity (Priority: P0) 🎯 MVP

**Goal**: Ensure data validity, ID matching, and behavioral column presence before any processing.

**Independent Test**: Run `src/validators.py` on a mock dataset with missing IDs and high motion; verify exit code 1 and correct JSON log entries.

### Tests for User Story 0 (MANDATORY) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US0] Contract test for ID validation in `tests/contract/test_id_validation.py` (verify missing ID raises exit 1)
- [ ] T010 [P] [US0] Contract test for behavioral column check in `tests/contract/test_behavioral_schema.py` (verify missing column raises exit 1)
- [ ] T011 [P] [US0] Integration test for power analysis threshold in `tests/integration/test_power_gate.py` (verify abort if N < 30)

### Implementation for User Story 0

- [ ] T012 [US0] Implement ID matching logic in `src/validators.py`: parse participant IDs from `sub-*/` folders and behavioral TSV; abort with `ID_VALIDATION: FAIL` if mismatch (FR-009)
- [ ] T013 [US0] Implement behavioral column check in `src/validators.py`: verify `nback_dprime` or `wm_accuracy` exists; abort with `BEHAVIORAL_COLUMN: FAIL` if missing (FR-012)
- [ ] T014 [US0] Define motion exclusion constant `MOTION_THRESHOLD_MM = 3.0` in `src/utils.py` (matching FR-002 and Constitution Principle VII). **IMPORTANT**: Use 3.0 mm as mandated by Spec FR-002. Do NOT implement filtering logic here; logic resides in T023.
- [ ] T015 [US0] Implement power analysis script `src/power_analysis.py`: use `statsmodels` to calculate power for N participants, α=0.05, effect=0.15; write the **achieved power** value explicitly to `data/results/power_analysis.txt` in format `ACHIEVED_POWER=0.XX` (FR-010, SC-003)
- [ ] T016 [US0] Implement JSON logger in `src/utils.py` to record `exclusion_motion`, `exclusion_missing_wm`, `exclusion_missing_id`, `total_runtime_seconds`, `pipeline_status` (FR-007)

**Checkpoint**: At this point, User Story 0 should be fully functional and testable independently

---

## Phase 4: User Story 1 - Compute Baseline Network Metrics (Priority: P1)

**Goal**: Generate cleaned fMRI data and network metrics for valid participants.

**Independent Test**: Run preprocessing on a small subset (N=5) of ds000278; verify 400x400 matrices and metric CSVs are generated correctly.

### Tests for User Story 1 (MANDATORY) ⚠️

- [ ] T017 [P] [US1] Contract test for connectivity matrix shape in `tests/contract/test_matrix_schema.py` (verify 400x400 symmetric float matrix)
- [ ] T018 [P] [US1] Integration test for fMRIPrep execution in `tests/integration/test_fmriprep_wrapper.py` (verify memory limits and exit codes)

### Implementation for User Story 1

- [ ] T019 [US1] Implement fMRIPrep wrapper in `src/preprocess.py`: execute Docker with memory constraints; parse `confounds.tsv` to EXTRACT motion metrics but DO NOT filter subjects here; log raw motion metrics to `data/motion/`. (FR-002)
- [ ] T020 [US1] Implement ROI extraction in `src/metrics.py`: load Schaefer 400-region parcellation from `; extract time series from preprocessed NIfTI (FR-003)
- [ ] T021 [US1] Implement correlation matrix calculation in `src/metrics.py`: compute symmetric Pearson correlation for each participant; save to `data/preprocessed/` (FR-003)
- [ ] T022 [US1] Implement network metric calculation in `src/metrics.py`: compute Global Efficiency, Modularity (Q), FPN Strength, DMN Strength using `bctpy` or `NetworkX`; save to `baseline_metrics.csv` (FR-004)
- [ ] T023 [US1] Implement exclusion logging in `src/preprocess.py`: read `data/motion/` metrics, apply `MOTION_THRESHOLD_MM` (3.0 mm from T014/Spec FR-002) to filter subjects, update JSON log with `exclusion_motion` count, and write the filtered list for downstream use. **IMPORTANT**: Use 3.0 mm as per FR-002.

**Checkpoint**: At this point, User Stories 0 AND 1 should both work independently

---

## Phase 5: User Story 2 - Associate Baseline Metrics with Baseline Cognition (Priority: P2)

**Goal**: Fit a linear regression model predicting baseline working memory from network metrics with permutation testing.

**Independent Test**: Run regression on a synthetic dataset with known coefficients; verify permutation p-values and Holm-Bonferroni correction match expected values.

### Tests for User Story 2 (MANDATORY) ⚠️

- [ ] T024 [P] [US2] Contract test for model summary schema in `tests/contract/test_regression_output.py` (verify columns: beta, se, p_perm, p_corrected)
- [ ] T025 [P] [US2] Integration test for permutation test in `tests/integration/test_permutation_test.py` (verify null distribution generation and p-value calculation)

### Implementation for User Story 2

- [ ] T026 [US2] Implement data merging in `src/regression.py`: join `baseline_metrics.csv` with behavioral data on participant ID; drop rows with missing WM scores (log `exclusion_missing_wm`) (FR-005)
- [ ] T026.5 [US2] **Plan Override**: Explicitly skip Principal Component Analysis (PCA). The Plan.md Phase 2 instructs PCA, but Spec FR-005 mandates direct regression on the four baseline metrics. Document this skip in `data/logs/pipeline_log.json` as "PCA_SKIPPED: Spec FR-005 requires direct regression."
- [ ] T027 [US2] Implement multiple linear regression in `src/regression.py`: Predict WM score from the **four baseline metrics** (Global Efficiency, Modularity, FPN Strength, DMN Strength) + Age + Sex. **DO NOT use PCA or LASSO**. Perform permutation testing (≥1000 shuffles) and apply Holm-Bonferroni correction. Write `model_summary.csv` with columns: `predictor, beta, se, p_perm, p_corrected, ci_lower, ci_upper` (FR-005, SC-001, SC-002).
- [ ] T028 [US2] Implement validation check in `src/regression.py`: verify `model_summary.csv` against `contracts/regression_output_schema.schema.yaml`

**Checkpoint**: At this point, User Stories 0, 1, AND 2 should all work independently

---

## Phase 6: User Story 3 - Visualize and Report Effect Sizes (Priority: P3)

**Goal**: Generate deterministic PDF reports with effect sizes and confidence intervals.

**Independent Test**: Run visualization script twice with `RANDOM_SEED=42`; verify SHA-256 hashes of output PDFs are identical.

### Tests for User Story 3 (MANDATORY) ⚠️

- [ ] T029 [P] [US3] Contract test for PDF reproducibility in `tests/contract/test_visualization_repro.py` (verify identical hashes on re-run)
- [ ] T030 [P] [US3] Integration test for figure content in `tests/integration/test_figure_content.py` (verify bar labels match predictor names)

### Implementation for User Story 3

- [ ] T031 [US3] Implement plotting utility in `src/visualize.py`: load `model_summary.csv`; generate bar plot with error bars for effect sizes (FR-006)
- [ ] T032 [US3] Implement PDF report generation in `src/visualize.py`: include regression table and effect size plot; save as `effect_sizes.pdf` (FR-006)
- [ ] T033 [US3] Implement deterministic seeding in `src/visualize.py`: set `RANDOM_SEED` for matplotlib and numpy; verify reproducibility (FR-011, SC-004)
- [ ] T034 [US3] Implement validation in `src/visualize.py`: verify output against `contracts/regression_result.schema.yaml`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Run full pipeline integration test on ds000278 subset (N≥30) to verify 24-hour runtime and memory constraints (FR-008, SC-005)
- [ ] T038 [P] Code cleanup and refactoring of `src/regression.py`. **Target**: Ensure max cyclomatic complexity < 10 for non-permutation logic. Permutation loops are exempt if necessary, but helper functions (e.g., p-value calculation, CI generation) must be extracted to separate functions to meet this target.
- [ ] T039 Add unit tests for utility functions in `src/utils.py` (log_json, seed_manager) and `src/validators.py` (ID matching, column check)
- [ ] T040 [P] Verify `quickstart.md` instructions work in a fresh CI environment
- [ ] T041 Generate final `data/logs/pipeline_log.json` with `pipeline_status: SUCCESS` and runtime stats

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P0 → P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 0 (P0)**: Can start after Foundational (Phase 2) - No dependencies on other stories; acts as a gatekeeper
- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - Requires valid data from US0
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires metrics from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires model results from US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Validators/Download before Preprocessing
- Preprocessing before Metric Extraction
- Metric Extraction before Regression
- Regression before Visualization
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2) *except* T007 which depends on T005 completion
- Once Foundational phase completes, US0, US1, US2, US3 can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Contract test for connectivity matrix shape in tests/contract/test_matrix_schema.py"
Task: "Integration test for fMRIPrep execution in tests/integration/test_fmriprep_wrapper.py"

# Launch implementation tasks for User Story 1:
Task: "Implement fMRIPrep wrapper in src/preprocess.py"
Task: "Implement ROI extraction in src/metrics.py"
Task: "Implement correlation matrix calculation in src/metrics.py"
```

---

## Implementation Strategy

### MVP First (User Story 0 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 0 (Data Validation & Gate)
4. **STOP and VALIDATE**: Ensure data is valid and power is sufficient before proceeding
5. Deploy/demo validation script if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 0 → Test independently → Gate data quality
3. Add User Story 1 → Test independently → Generate metrics
4. Add User Story 2 → Test independently → Run regression
5. Add User Story 3 → Test independently → Generate report
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 0 (Validation)
 - Developer B: User Story 1 (Preprocessing/Metrics)
 - Developer C: User Story 2 (Regression)
 - Developer D: User Story 3 (Visualization)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical Constraint**: All tasks MUST run on CPU-only CI (a limited number of cores, constrained RAM).. No GPU libraries allowed.
- **Data Integrity**: No fake data allowed. Must use real ds000278 data (resting-state).
- **Motion Threshold**: Use 3.0 mm as per FR-002 and Constitution Principle VII.
- **Power Analysis**: Must output 'achieved power' value regardless of threshold (SC-003).
- **Regression**: Must use the four specific metrics (Global Efficiency, Modularity, FPN Strength, DMN Strength) directly, not PCA components (FR-005).
- **Dataset Correction**: Spec FR-001 and Plan have been updated to mandate ds000278 (resting-state) instead of ds000277 (task-based) to align with the hypothesis.