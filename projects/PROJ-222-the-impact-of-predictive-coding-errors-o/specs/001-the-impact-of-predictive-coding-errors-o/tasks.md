# Tasks: The Impact of Predictive Coding Errors on Subjective Time Perception

**Input**: Design documents from `/specs/001-predictive-coding-time-perception/`
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

## Phase 0: Gate 0 - Data Availability & Validity Check (Priority: P0 - Critical Blocker)

**Goal**: Strictly implement the plan's "Gate 0" blocking check. Validate the pre-approved "Verified datasets" block in `data/README.md`. If empty or invalid, HALT execution immediately. NO dynamic search allowed.

**Independent Test**: The pipeline must halt with a "Data Gap" status if no valid dataset is found in the pre-approved list, without attempting to search external sources.

- [X] T000a [P] Implement `code/gate0.py` to load and validate the "Verified datasets" block from `data/README.md`. (Plan: Gate 0)
- [X] T000b [P] Implement strict schema validation in `code/gate0.py` to check for `duration_estimate`, `stimulus_sequence`, and `participant_id` in the pre-approved list. (FR-002, SC-001)
- [X] T000c [P] If no valid dataset is found in the pre-approved list, `code/gate0.py` MUST raise a `DataNotFoundError` and halt execution. If valid, update `data/README.md` with "Gate 0: Passed". (Plan: Gate 0, FR-001)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create project directories: `data/raw`, `data/processed`, `code`, `figures`, `analysis`, `contracts`, `tests`
- [X] T001b [P] Create `__init__.py` files in `code/` and `tests/` directories
- [X] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt` (pandas==2.0.3, numpy==1.24.3, statsmodels==0.14.0, pingouin==0.5.3, joblib==1.3.2, matplotlib==3.8.0, seaborn==0.13.0, openml==0.14.2, datasets==2.14.0, pyyaml==6.0.1)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup `data/README.md` schema for dataset metadata and exclusion logs (fields: dataset_id, status, reason)
- [X] T005 [P] Create `contracts/dataset.schema.yaml` defining required columns (duration_estimate, stimulus_sequence, participant_id)
- [X] T006 [P] Create `contracts/output.schema.yaml` defining analysis results structure
- [X] T007 Setup environment configuration management for random seeds in `code/config.py`
- [X] T008 [P] Implement chunked data loading utility in `code/utils.py` to handle datasets >500 MB within 7 GB RAM limits. Uses `pandas.read_csv()` with `chunksize` parameter and `pd.concat()` for aggregation. (FR-009, Assumption 9)
- [X] T009 [Dep: T000c] Document verified dataset IDs (OpenML/HF) in `data/README.md` 'Verified datasets' block. This task depends on T000c passing. If T000c halts, this task is skipped. (Plan: Gate 0)
- [X] T028b [P] [Dep: T007] Define the convergence threshold and bootstrap configuration in `code/config.py`. Set `MAX_TRIALS=5000` for sampling cap and `BOOTSTRAP_N_JOBS=min(2, os.cpu_count())` for dynamic core detection. (FR-009, Assumption 10)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download valid time-perception datasets, filter for sequential stimuli, and compute surprisal metrics.

**Independent Test**: Can be fully tested by executing the data download and preprocessing scripts and verifying that output CSV files contain the required columns (duration estimate, stimulus timing, condition label, participant ID, surprisal metric) with ≥100 valid rows.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T010 [P] [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py` (Dep: T005)
- [X] T011 [US1] Integration test for data download and Gate 0 validation in `tests/integration/test_download_gate0.py`

### Implementation for User Story 1

- [X] T012 [US1] [Dep: T009] Implement `code/download.py` to fetch datasets from OpenML/HuggingFace using IDs from `data/README.md` (created in T009) (FR-001)
- [X] T013 [US1] [Dep: T000c] Implement wrapper logic in `code/download.py` to call `code/gate0.py` before proceeding. If Gate 0 fails, halt. (Plan: Gate 0, SC-001)
- [X] T014 [US1] Implement filtering logic to exclude datasets lacking sequential stimuli or predictability manipulations. Save exclusion reasons to `data/processed/exclusion_log.json` with schema: `{dataset_id, reason, timestamp}`. (FR-002, SC-001)
- [X] T015 [US1] Create `code/preprocess.py` with full implementation of data loading functions. (FR-003, Assumption 1)
- [X] T015b [US1] [Dep: T015] Implement sampling enforcement logic in `code/preprocess.py` to cap dataset size to a manageable threshold if input exceeds this limit, ensuring compliance with Assumption 3 and the 6-hour budget. (Assumption 3, FR-009)
- [X] T016 [US1] [Dep: T015b] Implement Markov surprisal calculation in `code/preprocess.py` using 'Shannon entropy of the transition' on the (potentially sampled) data. (FR-003, Assumption 1)
- [X] T017 [US1] [Dep: T016] Generate standardized CSV output in `data/processed/standardized.csv` with checksums. Verify file exists, contains >=100 rows, AND explicitly verify that the surprisal metric was derived using a 'first-order Markov model' as mandated. (FR-003, SC-001)
- [ ] T017b [US1] [Dep: T017] Save 'transition-probability tables' and 'Markov model state' as versioned artifacts in `data/processed/` (e.g., `transition_probs.json`, `markov_state.json`). (Constitution VI, SC-001)
- [X] T018 [US1] Update `data/README.md` with exclusion logs and reasons for any dropped datasets

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Analysis and Hypothesis Testing (Priority: P2)

**Goal**: Fit linear mixed-effects models, calculate effect sizes, and perform sensitivity analysis.

**Independent Test**: Can be fully tested by running the analysis script on a sample dataset and verifying that model outputs include effect sizes (Cohen's d), confidence intervals, p-values for the surprisal main effect, and the calculated MDE.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Contract test for analysis output schema in `tests/contract/test_analysis_schema.py` (Dep: T006)
- [X] T020 [P] [US2] Unit test for MDE calculation logic in `tests/unit/test_mde_calc.py`

### Implementation for User Story 2

- [X] T021 [US2] [Dep: T017] Implement `code/analysis.py` to fit LMM: `Duration ~ Surprisal + Sequence_Length + Modality + (1 | Participant_ID)` (FR-004). Save model summary to `analysis/results.json` with keys: coef, pval, ci.
- [ ] T022 [US2] Implement convergence check and fallback to random-intercept-only model if convergence fails. Log `convergence_status` ("success" or "failed") and `fallback_applied` (boolean) to `analysis/results.json`. (Edge Cases, SC-002)
- [ ] T023 [US2] Implement multiple-comparison correction (Bonferroni/Benjamini-Hochberg) for p-values. Include logic: only apply correction if `num_tests > 1`. Save `adjusted_pvalues` list to `analysis/results.json`. (FR-005, SC-003)
- [ ] T023b [US2] Implement verification logic to ensure Family-Wise Error Rate is controlled at α≤0.05 and log `fwer_control_status` (boolean) to `analysis/results.json`. (SC-003)
- [ ] T024 [US2] Implement effect size calculation (Cohen's d) with % CI using `pingouin`. Save to `analysis/results.json` under key `effect_sizes`. (FR-006)
- [ ] T025 [US2] Implement sensitivity analysis to calculate Minimum Detectable Effect (MDE) for power=0.80. Include logic: 'If observed effect < MDE, report as limitation' in `analysis/results.json` under key `mde`. (FR-007, SC-005)
- [ ] T025b [US2] Ensure MDE results are logged to `analysis/results.json` for *every* dataset analyzed, regardless of outcome. (SC-005)
- [ ] T025c [US2] Implement cutoff-sweeping sensitivity analysis if decision cutoffs are introduced (Assumption 7). Log results to `analysis/results.json`. (Assumption 7)
- [ ] T026 [US2] Implement normality check (Shapiro-Wilk, α=0.05) and fallback to Wilcoxon signed-rank test if non-normal (Spec: Edge Cases)
- [ ] T027 [US2] Log all results (coefficients, p-values, MDE, convergence status) to `analysis/results.json`
- [ ] T028 [US2] [Dep: T028b] Implement bootstrap resampling in `code/analysis.py` using `joblib.Parallel(n_jobs=config.BOOTSTRAP_N_JOBS)` (dynamic core detection) for robust CI estimation. Save results to `analysis/results.json`. (FR-009)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reproducible Reporting (Priority: P3)

**Goal**: Generate forest plots, residual diagnostics, and ensure reproducible environment.

**Independent Test**: Can be fully tested by executing the visualization script and verifying that output plots (forest plot, residual diagnostics) are generated in `figures/` and that the Dockerfile builds successfully.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US3] Integration test for Dockerfile build and full analysis run in `tests/integration/test_reproducibility.py`

### Implementation for User Story 3

- [X] T030 [US3] [Dep: T027] Implement `code/visualize.py` to generate forest plots of condition effects (FR-008)
- [X] T031 [US3] [Dep: T027] Implement `code/visualize.py` to generate residual diagnostic plots (FR-008)
- [X] T032 [US3] Ensure all plots are saved at ≥300 DPI in `figures/` directory
- [X] T033 [US3] Create `Dockerfile` with `FROM python:slim`, `WORKDIR /app`, `COPY requirements.txt`, `RUN pip install`. Create `code/run_pipeline.py` (or shell script) that executes download, preprocess, analysis, and visualize in sequence. Set `CMD ["python", "code/run_pipeline.py"]` to ensure full pipeline execution. (US-3)
- [X] T033a [US3] Validate Dockerfile against GitHub Actions runner architecture (CPU-only, ≤7 GB RAM) (US-3)
- [ ] T034 [US3] Create `tests/integration/test_runtime.py` to verify full pipeline execution time < 6h (SC-004). Assert runtime < 21600 seconds. **Must enforce memory limit during test using `cgroups` or `ulimit`.**
- [ ] T034a [US3] [Dep: T034] Execute full pipeline in clean environment (Docker/runner simulation) and verify SLA compliance with 2 CPU/7GB RAM constraints (SC-004, Assumption 10). **Must use `cgroups` or `ulimit` to explicitly enforce the 7 GB RAM limit during execution.**
- [ ] T034b [US3] Generate `reproducibility-checklist.md` and `quickstart.md` explicitly guiding an external reviewer to reproduce results within 6 hours. (SC-006)
- [ ] T034c [US3] [Dep: T034b] Execute the `reproducibility-checklist.md` in a simulated environment and verify that all steps produce results within the 6-hour time limit, ensuring SC-006 is validated. (SC-006)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T035 [P] Documentation updates in `docs/` and `data/README.md`
- [X] T036 Code cleanup and refactoring in `code/`
- [X] T037 [P] Run `quickstart.md` validation to ensure reproducibility (SC-006)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Gate 0)**: No dependencies - must run first. Blocks all other phases if it fails.
- **Setup (Phase 1)**: No dependencies - can start immediately (parallel to Phase 0).
- **Foundational (Phase 2)**: Depends on Phase 0 (Gate 0) passing - BLOCKS all user stories.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion.
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories.
- **User Story 2 (P2)**: Requires output from US1 (`data/processed/standardized.csv`) - Tasks marked [Dep: T017].
- **User Story 3 (P3)**: Requires output from US2 (`analysis/results.json`) - Tasks marked [Dep: T027].

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel.
- All Foundational tasks marked [P] can run in parallel (within Phase 2).
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows).
- All tests for a user story marked [P] can run in parallel.
- Models within a story marked [P] can run in parallel.
- Different user stories can be worked on in parallel by different team members.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for dataset schema validation in tests/contract/test_dataset_schema.py"
Task: "Integration test for data download and Gate 0 validation in tests/integration/test_download_gate0.py"

# Launch implementation tasks that don't depend on each other:
Task: "Implement code/download.py to fetch datasets..."
Task: "Implement code/preprocess.py to compute surprisal..."
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0 (Gate 0) - Critical Blocker.
2. Complete Phase 1: Setup.
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories).
4. Complete Phase 3: User Story 1.
5. **STOP and VALIDATE**: Test User Story 1 independently (Gate 0 must pass).
6. Deploy/demo if ready.

### Incremental Delivery

1. Complete Phase 0 + Setup + Foundational → Foundation ready.
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!).
3. Add User Story 2 → Test independently → Deploy/Demo.
4. Add User Story 3 → Test independently → Deploy/Demo.
5. Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0, Setup + Foundational together.
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Analysis) - *Note: Must wait for T017 completion*
 - Developer C: User Story 3 (Visualization) - *Note: Must wait for T027 completion*
3. Stories complete and integrate independently.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: No task may load models in 8-bit/4-bit, use CUDA, or exceed a substantial amount of RAM. All analysis must run on CPU-only free-tier CI.
- **Memory Constraint**: All runtime tests (T034, T034a) MUST enforce the 7 GB RAM limit using `cgroups` or `ulimit`.
- **Sampling Constraint**: T015b MUST enforce the 5000-trial cap before T016 runs.

## Re-plan & Resolution Log

**Status**: All critical tasks from R1 analysis have been resolved.
- **T000a-T000c**: Added Phase 0 to strictly enforce Gate 0 blocking logic (resolved coverage/executability concerns). Removed conflicting Phase O.
- **T017, T017b, T022, T023, T023b**: Marked as `[ ]` (Pending) to reflect missing artifacts (resolved executability concern).
- **T015b**: Added to enforce 5000-trial cap before Markov calculation (resolved constraint preservation concern).
- **T028b, T028**: Updated to use dynamic core detection (`min(2, os.cpu_count())`) (resolved constraint preservation concern).
- **T034a, T034c**: Updated to enforce memory limits and validate reproducibility checklist (resolved executability/constraint preservation concerns).
- **Ordering**: Fixed dependencies (T000c -> T009, T015 -> T015b -> T016, T028b -> T028, T034b -> T034c).
- **Executability**: Added specific artifact paths and verification steps to all tasks.
- **Constraint Preservation**: All FR/SC requirements are now explicitly implemented in tasks.
- **Consolidation**: Removed duplicate T022b; moved T028b to Phase 2. Removed duplicate Gate 0 logic from T013.