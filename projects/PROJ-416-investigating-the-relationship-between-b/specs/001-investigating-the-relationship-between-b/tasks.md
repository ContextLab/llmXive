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

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup `data/raw`, `data/processed`, `data/metrics` directory structure with `.gitignore` rules
- [X] T005 [P] Implement `code/data/checksum.py` for SHA256 verification of downloaded data
- [X] T006 [P] Setup `code/main.py` orchestration entry point with argument parsing
- [X] T007 Create `code/config.py` for environment variables (OpenNeuro ID, paths, seeds)
- [X] T008 Implement `code/utils/logging.py` with structured logging for pipeline provenance
- [ ] T009 Setup `tests/unit` and `tests/integration` directory structures <!-- SKIPPED: YAML+regex parse failed (mapping values are not allowed here
 in "<unicode string>", line 2, column 13:
 contents: |
 ^) -->

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Download and Preprocess fMRI Data (Priority: P1) 🎯 MVP

**Goal**: Download resting-state fMRI data from OpenNeuro, validate variable presence (pre/post scores), preprocess (motion, slice, norm), and enforce strict exclusion criteria.

**Independent Test**: Run on a single subject's data; verify output NIfTI files exist, dimensions match expected space, and motion metrics are logged.

### Test Implementation for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST. Ensure they FAIL before implementing the code they test.

- [ ] T010 [P] [US1] Unit test for `code/data/validate.py` to ensure it halts on missing `pre_treatment_score` or `post_treatment_score` in metadata
- [ ] T011 [P] [US1] Unit test for `code/data/preprocess.py` to verify motion threshold logic (>3mm/3°) flags subjects correctly <!-- ATOMIZE: requested -->

### Code Implementation for User Story 1

- [ ] T012 [US1] Implement `code/data/download.py` to fetch data from OpenNeuro (or halt if no verified source ID is provided)
- [X] T012a [US1] Implement `code/data/download.py` to explicitly check for a verified OpenNeuro ID; if missing, halt execution with a fatal error and log "Missing verified dataset source" to align with Plan Summary "STATUS: BLOCKED" and FR-011
- [ ] T013 [US1] Implement `code/data/validate.py` to check for paired pre/post fMRI and clinical scores; verify the instrument is a validated anxiety scale (e.g., GAD-7, HAM-A) with citable documentation or halt with fatal error (FR-011, FR-009)
- [X] T014 [US1] Implement `code/data/preprocess.py` for motion correction, slice timing, and normalization using `nilearn` (CPU-optimized, subset N=10 for CI feasibility)
- [~] T015 [US1] Implement quality control in `code/data/preprocess.py` to calculate Mean Framewise Displacement (FD) and exclude subjects >3mm/3° translation/rotation; ensure FD is saved as a mandatory covariate column in `data/metrics/network_metrics.csv` ONLY for subjects who PASSED the motion threshold (i.e., were not excluded) (FR-015b merged)
- [~] T016 [US1] Add logging for excluded subjects and specific exclusion reasons in `logs/preprocessing.log`
- [~] T017 [US1] Implement `code/data/save_metadata.py` to store subject list, exclusion reasons, and motion metrics in `data/metrics/subject_info.json`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compute Network Metrics (Priority: P2)

**Goal**: Compute functional connectivity matrices and derive network properties (modularity, global/local efficiency) using a standard atlas (AAL/Schaefer).

**Independent Test**: Run on a single preprocessed subject; verify matrices and metrics exist with values in expected mathematical bounds (Q≥0, Eff≥0).

### Test Implementation for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for `code/analysis/network.py` to ensure modularity Q is non-negative and efficiency values are finite
- [X] T019 [P] [US2] Integration test for `code/analysis/network.py` to verify output CSV contains all three metrics per subject

### Code Implementation for User Story 2

- [X] T020 [US2] Implement `code/analysis/network.py` to extract ROI time series using AAL or Schaefer atlas (parcellations with a moderate number of regions)
- [X] T021 [US2] Implement functional connectivity matrix calculation (Pearson correlation) in `code/analysis/network.py`
- [~] T022 [US2] Implement network metric calculation (Modularity Q, Global Efficiency, Local Efficiency) using `networkx` or `brainconn`
- [X] T023 [US2] Add NaN/Infinity handling in `code/analysis/network.py` to exclude invalid metrics and log events
- [ ] T024 [US2] Save connectivity matrices and metrics to `data/metrics/network_metrics.csv` and `data/metrics/matrices/`
- [X] T025 [US2] Implement `code/analysis/validate_metrics.py` to enforce bounds (Q≥0, Eff≥0) and halt on systematic failures

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Reporting (Priority: P3)

**Goal**: Perform ANCOVA analysis (Post ~ Pre + Metric), apply FDR correction, run sensitivity analysis, and generate diagnostic plots. Note: Ridge regression is explicitly rejected per Plan Methodological Clarification.

**Independent Test**: Run on sample data; verify regression coefficients, p-values, effect sizes, and plots are generated.

### Test Implementation for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Unit test for `code/analysis/stats.py` to verify FDR correction logic and VIF calculation
- [X] T027 [P] [US3] Unit test for `code/analysis/plots.py` to ensure scatter plots and residuals are generated without error

### Code Implementation for User Story 3

- [X] T028 [US3] Implement `code/analysis/stats.py` to perform ANCOVA (Post ~ Pre + Metric + Confounds + FD_Covariate) with `statsmodels` <!-- ATOMIZE: requested -->
- [X] T029 [US3] Implement VIF calculation in `code/analysis/stats.py`; if VIF > 5, apply separate univariate models with FDR correction (Per Plan Methodological Clarification #2: Ridge regression is rejected as methodologically unsound for hypothesis testing). Do NOT implement Ridge regression fallback.
- [X] T029b [US3] Implement logic in `code/analysis/stats.py` to document the methodological divergence from Spec FR-005/FR-012 in the final report, explicitly stating that Univariate models with FDR were chosen over Ridge regression per Plan guidance.
- [X] T030 [US3] Implement multiple comparison correction (FDR/Bonferroni) in `code/analysis/stats.py` for >1 metric hypothesis
- [X] T031 [US3] Implement power analysis in `code/analysis/stats.py` (G*Power logic) to: HALT if N < 5; FLAG limitation if 5 <= N < 10; calculate and save the 'minimum N required' value to the report (SC-004)
- [X] T032 [US3] Implement sensitivity analysis in `code/analysis/stats.py` sweeping motion thresholds {2mm, 3mm} and p-values {uncorrected, 0.05, 0.1}, ensuring 'uncorrected' is treated as a distinct sweep point (FR-010)
- [X] T033 [US3] Implement `code/analysis/plots.py` to generate scatter plots with regression lines and residual diagnostics
- [ ] T034 [US3] Generate final report in `reports/results.md` with associational framing (FR-008); include logic to check `metadata.study_design` for string 'randomized' OR `metadata.randomized` for boolean true; frame findings as ASSOCIATIONAL if neither condition is met (SC-005); include all metrics, coefficients, and the minimum N value
- [ ] T035 [US3] Save all statistical outputs (coefficients, p-values, VIF, power calc, min_N) to `data/metrics/statistical_results.csv`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Update `docs/quickstart.md` with execution instructions for N=10 subset
- [ ] T037a [P] Refactor code to add comprehensive docstrings to all public functions in `code/analysis/` and `code/data/`
- [ ] T037b [P] Refactor `code/data/preprocess.py` to reduce cyclomatic complexity where possible without losing readability
- [ ] T038 Performance optimization for preprocessing loop (ensure N=10 completes <6h)
- [ ] T039 [P] Add unit tests for `code/analysis/stats.py` edge cases (collinearity, NaNs)
- [ ] T040 Run `quickstart.md` validation to ensure end-to-end flow works on CI

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (preprocessed data)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (network metrics)

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
- **Critical Constraint**: All data processing must fit within 2 CPU cores, 7GB RAM, 14GB disk, and 6 hours. Use N=10 subset.
- **Critical Constraint**: No GPU/CUDA. No 8-bit/4-bit quantization. No deep learning training.
- **Critical Constraint**: If dataset variables (pre/post scores) are missing, the pipeline MUST halt immediately (FR-011).
- **Critical Constraint**: Ridge regression is explicitly REJECTED per Plan Methodological Clarification; use Univariate models with FDR correction instead.
- **Critical Constraint**: Sensitivity analysis must include uncorrected p-value case and specific motion thresholds {2mm, 3mm}.
- **Critical Constraint**: Report must frame findings as ASSOCIATIONAL if study_design is not 'randomized' (string) OR metadata.randomized is not true (boolean).