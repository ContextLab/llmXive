# Tasks: Decoding Internal States from Longitudinal Calcium Imaging Data

**Input**: Design documents from `/specs/001-decoding-internal-states/`
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

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per `plan.md` by executing `mkdir -p code/data code/analysis code/utils code/tests specs/001-decoding-internal-states/contracts` to establish the exact directory tree defined in the plan.
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` pinning `numpy`, `pandas`, `scikit-learn`, `scipy`, `requests`, `tqdm`, `nwb`, `pytest`
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `code/utils/memory_monitor.py` to enforce a configurable RAM limit and raise `MemoryExceededError`
- [ ] T005 [P] Implement `code/utils/logger.py` for structured logging of pipeline stages
- [ ] T006 Create base data schemas in `specs/001-decoding-internal-states/contracts/` (`dataset.schema.yaml`, `output.schema.yaml`, `alignment_results.schema.yaml`, `correlation_results.schema.yaml`)
- [X] T007 Implement `code/data/loader.py` with chunked loading strategy to ensure memory safety
- [X] T008 [P] Implement `code/data/split.py` for time-based train/test splitting with a majority-to-minority ratio. to satisfy FR-008 (held-out dataset split for statistical validation)
- [X] T009 Setup environment configuration management by creating `code/config.py` to manage specific keys: `DATASET_URL`, `RANDOM_SEED`, `MEMORY_LIMIT_GB`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download Allen Brain Atlas data, normalize dF/F, detrend, deconvolve, and ensure memory safety.

**Independent Test**: The pipeline can be tested by executing `code/data/download.py` and `code/data/preprocess.py` on a small sample file and verifying that the output is a normalized NumPy array with no NaN values and a memory footprint ≤ 5 GB.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for data schema in `code/tests/test_preprocess.py` (verify no NaNs, correct shape)
- [X] T011 [P] [US1] Integration test for memory limit in `code/tests/test_preprocess.py` (verify `MemoryExceededError` on oversized input)

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/data/download.py` to fetch specific Allen Brain Atlas Visual Coding subset (ROI traces + metadata) with checksum validation
- [X] T013 [US1] Implement `code/data/preprocess.py` `dF/F` normalization, detrending, and missing data handling: interpolate if ≤5% missing, otherwise raise `DataValidationError` with message "Missing data exceeds 5% threshold" (FR-002)
- [X] T014 [US1] Implement `code/data/preprocess.py` deconvolution step using OASIS algorithm to estimate spike rates (FR-011); output is required input for T020
- [X] T015 [US1] Implement resampling logic in `code/data/preprocess.py` to align behavioral metadata sampling rate with imaging data
- [X] T016 [US1] Implement specific logic in `code/data/download.py` and `code/data/loader.py` to intercept dataset size checks and explicitly raise `MemoryExceededError` with the message "Memory limit exceeded" if the dataset exceeds 5GB (FR-001, SC-001)
- [X] T017 [US1] Add logging for data download, preprocessing steps, and memory usage in `code/utils/logger.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Latent State Extraction via NMF (Priority: P2)

**Goal**: Apply CPU-tractable NMF with temporal regularization to extract latent components and weights.

**Independent Test**: The NMF execution can be tested by running the decomposition on a small real subset and verifying that the output matrices are non-negative, CPU-only, and complete within the CI time limit.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for NMF output shape and non-negativity in `code/tests/test_nmf.py`
- [X] T019 [P] [US2] Integration test for CPU-only enforcement in `code/tests/test_nmf.py` (verify no CUDA calls)

### Implementation for User Story 2

- [X] T020 [US2] Implement `code/analysis/nmf_engine.py` custom solver with temporal smoothness regularization (SparseNMF/ConvNMF approach) to satisfy FR-010; consumes deconvolved output from T014 (Note: Removed [P] tag due to dependency on T014)
- [X] T021 [US2] Implement NMF execution logic in `code/analysis/nmf_engine.py` with configurable k (a range of values) and A limited number of retries for convergence.
- [X] T022 [US2] Implement sensitivity sweep logic in `code/analysis/nmf_engine.py` to iterate through specific k values and aggregate results for sensitivity analysis (FR-003)
- [X] T023 [US2] Implement parallel multi-seed sweep in `code/analysis/nmf_engine.py` to generate NMF components for multiple random seeds
- [ ] T024 [US2] Implement sequential aggregation of NMF results from T023 to calculate cosine similarity across seeds and verify stability threshold ≥0.95 (SC-004); write stability report to `code/analysis/stability_report.json` with explicit pass/fail status
- [ ] T025 [US2] Integrate `code/data/loader.py` to feed chunked data into NMF engine without loading full matrix
- [ ] T026 [US2] Implement alignment of extracted component weights with behavioral metadata timestamps in `code/analysis/alignment.py`
- [ ] T027 [US2] Calculate alignment error metric and validate against ≤1 frame threshold (SC-005); raise error if threshold exceeded

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Behavioral Alignment and Statistical Validation (Priority: P3)

**Goal**: Align weights with behavior, perform Spearman correlation with 1000-iteration permutation test, and validate against null models.

**Independent Test**: The statistical module can be tested by running it on shuffled behavioral metadata; the system must report p-values > 0.05 for the shuffled data.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Contract test for correlation results schema in `code/tests/test_stats.py`
- [ ] T029 [P] [US3] Integration test for permutation test significance in `code/tests/test_stats.py` (verify p > 0.05 on shuffled data)

### Implementation for User Story 3

- [ ] T030 [US3] Implement `code/analysis/stats.py` Spearman correlation calculation between component weights and behavioral metrics (Note: Removed [P] tag due to dependency on T026)
- [ ] T031 [US3] Implement `code/analysis/stats.py` permutation test with a sufficient number of iterations to ensure statistical reliability to generate null distribution and p-values (FR-005) with explicit enforcement that Benjamini-Hochberg FDR correction is applied ONLY to the held-out set results after splitting (FR-008, Plan Phase 2 Step 6)
- [ ] T032 [US3] Implement `code/analysis/null_model.py` to generate "linear mixing of behavior" null model (FR-009) for comparison against NMF results
- [ ] T033 [US3] Implement validation logic to compare NMF components derived from the training set against the test set: run NMF on training set, apply weights to test set, calculate correlation on test set only, and report to prove non-tautological correlation (FR-008); explicitly reference held-out set generated by T008
- [ ] T034 [US3] Implement `code/analysis/null_model.py` to generate "linear mixing of behavior" null model (FR-009) for comparison against NMF results
- [ ] T035 [US3] Perform explicit statistical comparison between NMF-derived correlations and the linear mixing null model: calculate difference in correlation strength and p-values, and generate a comparison report
- [ ] T036 [US3] Generate final results report to `results/final_report.md` with p-values, significance flags, explicit comparison against the linear mixing null model, and validation results from T033
- [ ] T037 [US3] Restrict statistical testing to the held-out test set generated by `code/data/split.py` (FR-008)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Documentation updates in `specs/001-decoding-internal-states/quickstart.md` including specific command to run `main.py` with `--seed 42` and expected output files
- [ ] T039 Code cleanup and refactoring of `code/analysis/nmf_engine.py` for performance
- [ ] T040 Performance optimization for chunked loading in `code/data/loader.py`
- [ ] T041 [P] Additional unit tests in `code/tests/unit/` for edge cases (missing data > 5%, convergence failure)
- [ ] T042 Run `quickstart.md` validation to ensure end-to-end pipeline execution on CI

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (preprocessed traces)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (component weights) and US1 output (behavioral metadata)

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
Task: "Contract test for data schema in code/tests/test_preprocess.py"
Task: "Integration test for memory limit in code/tests/test_preprocess.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/download.py"
Task: "Implement code/data/preprocess.py dF/F normalization"
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