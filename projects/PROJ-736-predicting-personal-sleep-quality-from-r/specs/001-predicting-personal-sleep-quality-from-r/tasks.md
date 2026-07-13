# Tasks: Predicting Personal Sleep Quality from Resting‑State fMRI Connectivity

**Input**: Design documents from `/specs/001-predict-sleep-quality/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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

- [X] T001a [P] Create directory structure: `code/`, `tests/`, `data/`, `docs/`, `data/raw/`, `data/processed/`, `data/results/`, `code/data/`, `code/modeling/`, `code/utils/`
- [X] T001b [P] Create `code/__init__.py`, `code/data/__init__.py`, `code/modeling/__init__.py`, `code/utils/__init__.py`, `tests/__init__.py`
- [X] T001c [P] Create `requirements.txt` with pinned versions: nilearn, scikit-learn, pandas, numpy, nibabel, networkx, pytest, psutil, seaborn, matplotlib

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Implement `code/config.py` with seeds, paths, and hyperparameters (variance_threshold set to a low default, PCA retention defaults, subset size 100)
- [X] T003 [P] Implement `code/utils/logging.py` for structured JSON logging (FR-010)
- [X] T004 [P] Create `code/utils/metrics.py` for Pearson r, R², and p-value calculation utilities
- [X] T005 Implement `code/data/download_hcp.py` to fetch HCP minimally preprocessed CIFTI files and `hcp1200_behavioral_data.csv` from `hcp_1200/behavioral/` with checksum verification. **Output**: Save to `data/raw/behavioral/hcp1200_behavioral_data.csv`. <!-- FAILED: unspecified -->
- [X] T006 Implement `code/data/preprocess.py` for Schaefer parcellation, nuisance regression, and 0.01-0.1 Hz band-pass filtering (FR-001)
- [X] T007 Implement `code/data/feature_engineering.py` for pairwise Pearson correlation, Fisher-z transformation, and upper-triangular vector extraction (FR-002)
- [ ] T007b [US1] Implement subject filtering logic in `code/data/download_hcp.py` (or a helper module) to identify subjects with valid Sleep Scores and exclude those with >0.3mm framewise displacement (US1 Acceptance 2). **This task MUST be executed after T005 outputs the behavioral file.** <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [X] T008 [US1] Implement `code/data/preprocess.py` to process ONLY the filtered subjects from T007b (FR-001)
- [X] T009 [US1] Implement `code/data/feature_engineering.py` to process ONLY the filtered subjects from T007b (FR-002)
- [X] T010 Create `tests/contract/` directory and schema definitions (`dataset.schema.yaml`, `result.schema.yaml`)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - End‑to‑end Data Pipeline (Priority: P1) 🎯 MVP

**Goal**: Obtain preprocessed whole‑brain functional connectivity vectors for every HCP participant with Sleep questionnaire data.

**Independent Test**: Run the data‑pipeline script on the HCP 1200-subject release (restricted to subjects with Sleep questionnaire data) and verify that the expected `.npy` files are produced.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T011 [P] [US1] Contract test for data schema in `tests/contract/test_dataset_schema.py`
- [X] T012 [P] [US1] Integration test for pipeline execution on a single subject in `tests/integration/test_single_subject_pipeline.py`

### Implementation for User Story 1

- [X] T014a [US1] Implement orchestration in `code/main.py` to **import and invoke** the download function from `code/data/download_hcp.py` (T005) to fetch raw data. <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [X] T014b [US1] Implement orchestration in `code/main.py` to **import and invoke** the preprocessing function from `code/data/preprocess.py` (T006) to process filtered subjects. <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified -->
- [X] T014c [US1] Implement orchestration in `code/main.py` to **import and invoke** the feature engineering function from `code/data/feature_engineering.py` (T007) to process filtered subjects. <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified -->
- [X] T014d [US1] Implement `code/main.py` orchestration to: (1) download raw data, (2) preprocess time series, (3) compute connectivity vectors, and (4) save `.npy` files to `data/processed/` <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested -->
- [ ] T015 [US1] Add logging for data ingestion, preprocessing, and feature engineering stages to `data/logs/pipeline_run.json` (FR-010)
- [X] T016 [US1] Implement error handling to log excluded subjects and abort if success rate <80% (SC-001)
- [X] T017 [P] [US1] Create unit tests for Fisher-z transformation and variance calculations in `tests/unit/test_feature_engineering.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Predictive Modeling & Statistical Validation (Priority: P2)

**Goal**: Train an elastic‑net regression model on connectivity features, evaluate out‑of‑sample performance, and assess statistical significance.

**Independent Test**: Execute the modeling script on the feature matrix produced by US‑1 and confirm that the script returns performance metrics, permutation‑test p‑value, and bootstrap confidence intervals.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for result schema in `tests/contract/test_result_schema.py`
- [X] T019 [P] [US2] Integration test for nested CV loop on a small synthetic dataset in `tests/integration/test_nested_cv.py`

### Implementation for User Story 2

- [X] T020a [US2] Implement `code/modeling/pipeline_factory.py` to encapsulate the nested CV logic. **Must accept an optional `data_subset` parameter** (list of subject IDs) to allow re-running the pipeline on a stratified subset (for T022) or the full dataset (for T024). **Atomic implementation**: Must include Variance Thresholding and PCA fitted strictly within the training fold. <!-- SKIPPED: YAML+regex parse failed (while parsing a block mapping
expected <block end>, but found ':'
 in "<unicode string>", line 1, column 1:
:
 ^) -->
- [ ] T020 [US2] Implement `code/modeling/train.py` to **invoke T020a** on the full dataset, tune ElasticNetCV, output Pearson r and R² per fold, and **save outer-fold predictions** to `data/processed/predictions.npy` for T023 (FR-004, FR-005). <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [X] T022 [US2] Implement `code/modeling/evaluate.py` to perform 1,000 label permutations on a **stratified subset of 100 subjects** (based on Sleep Score). **Must invoke T020a with the subset parameter**. **Must register a signal handler for graceful shutdown** to flush the permutation null distribution to disk if aborted. **Deliverable**: Approximate p-value derived from subset (Plan Override of FR-006).
- [ ] T023 [US2] Implement `code/modeling/evaluate.py` to perform 1,000 bootstrap resamples of **outer-fold predictions** (loaded from `data/processed/predictions.npy`) for % CI on R² (FR-007). <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [X] T024a [US2] Implement logic in `code/modeling/evaluate.py` to check for 'all edges removed' edge case: if variance thresholding results in zero features, log a warning and skip the grid point without crashing (Spec Edge Case 2).
- [X] T024 [US2] Implement sensitivity analysis in `code/modeling/evaluate.py` to iterate variance thresholds including low values and PCA retention {0.95, 0.90, 0.85}. **Must invoke T020a with full dataset**. **Must enforce a cumulative 3-hour time budget** for the 9 grid points; if exceeded, log completed rows as a list in `ResultReport.json['sensitivity_analysis']` and set `incomplete: true` before aborting.
- [X] T025 [US2] Implement `code/modeling/evaluate.py` to enforce CPU-only execution, monitor RAM usage (≤6 GB) using `psutil`, and abort if wall-clock time exceeds a predefined threshold using `signal` module (FR-009). **Must integrate the signal handler logic from T022/T024 to ensure partial results are flushed.**
- [X] T026 [US2] Generate `data/results/ResultReport.json` containing all metrics, p-values, CIs, and sensitivity analysis results (SC-002)
- [X] T026c [US2] Explicitly document in `ResultReport.json` that the permutation-test p-value is an **approximation** derived from a 100-subject subset (Plan Override of FR-006) and not the full dataset.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Interpretation & Visualization (Priority: P3)

**Goal**: Identify which brain connections drive the prediction and visualise them on a cortical surface.

**Independent Test**: Run the feature‑importance script on the trained model from US‑2 and verify that a brain‑surface plot is generated without errors.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Contract test for visualization output in `tests/contract/test_viz_schema.py`
- [X] T028 [P] [US3] Integration test for plot generation in `tests/integration/test_visualization.py`

### Implementation for User Story 3

- [X] T029 [US3] Implement `code/modeling/interpret.py` to extract non-zero elastic-net coefficients and map them back to brain edges using the Schaefer atlas (FR-008)
- [X] T030 [US3] Implement logic to handle failed edge mappings (log warning, continue) (US3 Acceptance 2)
- [ ] T031 [US3] Generate brain-surface plot using Nilearn `plot_connectome` highlighting top N (configurable) predictive connections. **Must handle case where <50 non-zero coefficients exist by plotting all available and logging a warning** (SC-004). <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [X] T032 [US3] Save visualization to `data/results/` as `.png` or `.svg` and log file path in `ResultReport.json`
- [ ] T033 [P] [US3] Verify plot file exists and contains ≥50 edges: Use Python's built-in `xml.etree.ElementTree` to parse SVG and count both `<line>` and `<path>` elements (to handle different rendering backends). Implement retry or error logging if validation fails (SC-004). **Do not use OpenCV.**

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [X] T034 [P] Update `README.md` with quickstart instructions and environment setup
- [X] T035 Run contract tests against `ResultReport.json` schema to ensure reproducibility (SC-006) <!-- SKIPPED: non-mapping output -->
- [X] T036 Implement Docker containerization strategy (Dockerfile) to guarantee environment reproducibility (Plan: Constitution Check)
- [X] T037 Run end-end integration test on `ubuntu-latest` runner to verify a multi-hour time limit and GB RAM constraint (FR-009, SC-005)
- [X] T038 Finalize `ResultReport.json` with all metrics and paths; verify no manual entry (Plan: Constitution Check)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output

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

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data schema in tests/contract/test_dataset_schema.py"
Task: "Integration test for pipeline execution on a single subject in tests/integration/test_single_subject_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement subject filtering logic in code/data/download_hcp.py"
Task: "Implement main.py orchestration"
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
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
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
- **Critical**: Variance Thresholding and PCA MUST be fitted within the training fold of every CV iteration to prevent data leakage (Plan: Critical Methodological Correction).
- **Critical**: Permutation test runs on a stratified subset of 100 subjects (Plan Override of FR-006) to meet -hour compute constraint. The resulting p-value is an approximation.
- **Critical**: All tasks must run on CPU-only CI (limited vCPU, GB RAM) without GPU dependencies.
- **Critical**: Graceful shutdown logic is integrated into T022 and T024 to ensure partial results are saved if the 5-hour limit is hit.
- **Critical**: T024 enforces a 3-hour sub-budget for the sensitivity grid to prevent mid-run aborts without partial logging.
