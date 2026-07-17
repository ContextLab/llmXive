# Tasks: llmXive follow-up: extending "EvalVerse" with CPU-tractable Feature Distillation

**Input**: Design documents from `/specs/001-llmxive-feature-distillation/`
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

- [ ] T001 Create project structure per implementation plan (`src/`, `tests/`, `specs/`)
- [X] T002 Initialize Python 3.11 project with pinned dependencies (`opencv-python`, `librosa`, `scikit-learn`, `xgboost`, `psutil`) in `requirements.txt`
- [ ] T003 [P] Configure linting (`ruff`) and formatting (`black`) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure and GATES that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T014 [P] Implement `src/data/download.py` to fetch and unzip EvalVerse dataset from Zenodo/Repo if local cache is empty. **Output**: Raw data in `data/raw/`. **Constraint**: Must handle initial fetch and unzip logic.
- [X] T004 [P] Implement `scripts/checksum_data.py` to verify EvalVerse local download via SHA-256 and record hash in `state/artifact_hashes`. **Prerequisite**: Must run AFTER T014 to verify fetched data.
- [X] T005 [P] Create `src/config.py` with constants, random seeds, and thresholds
- [X] T006 [P] Implement `src/utils.py` for logging, error handling, and file I/O helpers
- [X] T007 Create base data structures (`VideoClip`, `FeatureVector`, `DimensionScore`) in `src/data/models.py`
- [X] T008 [P] Implement individual error handling in `src/data/preprocess.py` to gracefully skip missing audio tracks and handle optical flow failures (returning null/zero vectors)
- [ ] T009 Setup environment configuration management and local cache directory structure (`data/raw`, `data/processed`)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dimensional Viability Analysis (Priority: P1) 🎯 MVP

**Goal**: Determine which technical sub-dimensions are "feature-sufficient" (r ≥ 0.85) vs "VLM-required" (lower 95% CI < 0.70) using low-level features against human expert scores.

**Independent Test**: The system extracts features, trains models, and outputs a ranked list of dimensions with correlation coefficients and confidence intervals.

**⚠️ GATE**: T018 (Validation Gate) and T040 (Quality Gate) must pass (exit 0) before T012-T017, T019, T020 execute.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T010 [P] [US1] Contract test for feature extraction output schema in `tests/contract/test_feature_schema.py`
- [X] T011 [P] [US1] Integration test for full correlation pipeline on a 10-clip sample in `tests/integration/test_us1_pipeline.py`

### Implementation for User Story 1

- [X] T014 [US1] Implement data loading and parsing of EvalVerse CSV/Parquet metadata (expert scores) in `src/data/download.py`. **Note**: This task now handles the initial fetch/unzip logic if cache is empty.
- [X] T040 [US1] **GATE**: Calculate global error rate across the dataset in `src/data/preprocess.py` after T014. **Output**: `state/global_error_rate.json`. **Constraint**: If error_count/total_count > 0.05, EXCLUDE those samples from the final correlation calculation (log exclusion count) and continue (do NOT halt pipeline). This task MUST complete before T012 and T013. **Prerequisite**: T014.
- [ ] T018 [US1] **GATE**: Implement preliminary validation (FR-009) in `src/models/evaluate.py` to correlate VLM proxy scores against human expert scores on n ≥ 30 subset. **Output**: `state/validation_status.json`. **Constraint**: Exit with code 1 ONLY if (1) human scores are missing, OR (2) VLM proxy correlation r < 0.70 AND human scores are missing. If human scores exist, proceed regardless of VLM alignment. This task MUST complete successfully before T012-T017, T019, T020 are allowed to run. **Prerequisite**: T014.
- [ ] T012 [US1] Implement optical flow extraction (magnitude/variance) and HOG density in `src/data/preprocess.py` (OpenCV CPU-only). **Prerequisite**: T040, T018.
- [ ] T013 [US1] Implement audio feature extraction (spectral centroid, zero-crossing rate) in `src/data/preprocess.py` (Librosa) with missing audio handling. **Prerequisite**: T040, T018.
- [ ] T015 [US1] Implement Ridge/Lasso and XGBoost training pipeline in `src/models/train.py` targeting human expert scores. **Prerequisite**: T012, T013.
- [ ] T016 [US1] Implement Pearson/Spearman correlation calculation and bootstrapping for 95% CIs in `src/models/metrics.py`. **Prerequisite**: T015.
- [ ] T019 [US1] Implement baseline comparisons (Mean Predictor, Shuffled Features) in `src/models/evaluate.py`. **Required**: This task is mandatory for validity per Plan.md Complexity Tracking. Output `data/baseline_results.csv`. **Prerequisite**: T016.
- [ ] T020 [US1] Implement permutation-based multiple-comparison correction in `src/models/metrics.py`. **Required**: Per Plan.md Complexity Tracking. Output `data/permutation_results.csv`. **Prerequisite**: T016.
- [ ] T017 [US1] Implement logic to flag dimensions as "feature-sufficient" (r ≥ 0.85) or "VLM-required" (lower CI < 0.70) in `src/reports/generate.py`. **Prerequisite**: T019, T020.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compute Feasibility Profiling (Priority: P2)

**Goal**: Verify the pipeline runs on a multi-core CPU within 7GB RAM and processes 10k clips in < 6 hours.

**Independent Test**: The system executes the full pipeline on a representative subset and logs peak memory and time per clip.

**⚠️ GATE**: T021 must pass (exit 0) before T022-T025 execute.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Unit test for memory profiling logic with mock data in `tests/unit/test_profiles.py`
- [ ] T022 [P] [US2] Integration test for timing constraints on a 100-clip batch in `tests/integration/test_us2_timing.py`

### Implementation for User Story 2

- [ ] T024 [US2] Implement logic to calculate per-clip inference time and project total time for N=10,000 clips in `src/models/evaluate.py`. **Output**: `data/timing_profile.csv`. **Constraint**: Must output projected_total_hours based on linear scaling.
- [ ] T021 [US2] **GATE**: Implement memory and time profiling wrapper in `src/data/profiles.py` using `psutil` on a sample batch. **Output**: `state/feasibility_gate.json`. **Constraint**: If peak_memory > 7GB OR projected_total_hours (from T024) > 6.0, exit with code 1 and flag "non-viable". This task MUST complete before T022. **Prerequisite**: T024.
- [ ] T022 [US2] Implement batch processing logic to process N clips and aggregate timing stats in `src/cli/run_pipeline.py`
- [ ] T023 [US2] Implement structured report generation for memory/time metrics in `src/reports/generate.py`
- [ ] T025 [US2] Generate final feasibility report `reports/feasibility_profile.json` containing peak_memory_gb and projected_total_hours.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis of Feature Thresholds (Priority: P3)

**Goal**: Ensure decision boundaries (0.85) are robust by sweeping thresholds in the high range (e.g., 0.85, 0.90).

**Independent Test**: The system re-runs classification logic with varied thresholds and reports stability/flip rates.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Contract test for sensitivity analysis output schema in `tests/contract/test_sensitivity_schema.py`

### Implementation for User Story 3

- [ ] T026 [P] [US3] Implement threshold sweep logic in `src/models/metrics.py`. **Output**: Intermediate results for stability calculation. **Constraint**: The sweep MUST include the specific set of thresholds: {0.80, 0.85, 0.90}.
- [ ] T027 [US3] Implement stability calculation (flip rate) and "threshold-sensitive" flagging in `src/models/evaluate.py`. **Output**: `data/sensitivity_analysis.csv` with columns [dimension, threshold, status, flip_rate].
- [ ] T028 [US3] Generate full sensitivity matrix table `data/sensitivity_matrix_full.csv` showing classification outcome for *each dimension* at *all tested thresholds*. **Required**: This artifact is mandatory for methodological verification (US-3 Acceptance Scenario 3).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and ensure rigor

- [ ] T029 [P] Documentation updates in `docs/` and `specs/`
- [ ] T030 Code cleanup and refactoring for CPU optimization
- [ ] T031 [P] Additional unit tests for edge cases (all-black frames, missing audio) in `tests/unit/`
- [ ] T032 [P] Run `quickstart.md` validation and ensure all tasks pass on local CPU environment

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **Critical Order**: T014 (Fetch) MUST run before T004 (Verify).
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
 - **Critical Order**: T014 (Data Load) MUST complete before T040.
 - T040 and T018 (Gates) MUST complete before T012, T013.
 - T012, T013 MUST complete before T015.
 - T015 MUST complete before T016.
 - T016 MUST complete before T019 and T020.
 - T019, T020 MUST complete before T017.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
 - **Critical Order**: T024 (Projection) MUST complete before T021 (Gate).
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

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
Task: "Contract test for feature extraction output schema in tests/contract/test_feature_schema.py"
Task: "Integration test for full correlation pipeline on a small sample in tests/integration/test_us1_pipeline.py"

# Launch all models for User Story 1 together (after Gates T018, T040 pass):
Task: "Implement optical flow extraction in src/data/preprocess.py"
Task: "Implement audio feature extraction in src/data/preprocess.py"
Task: "Implement baseline comparisons in src/models/evaluate.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
 - Ensure T014 (Fetch) runs before T004 (Verify).
3. Complete Phase 3: User Story 1 (Ensure T018 and T040 Gates pass)
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
 - Developer A: User Story 1 (Focus on Gates T018, T040 first)
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- **GATE Tasks (T018, T021, T040)**: These tasks MUST exit with code 0 to proceed. If they exit with code 1, the pipeline halts immediately (except T040 which excludes samples).
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence