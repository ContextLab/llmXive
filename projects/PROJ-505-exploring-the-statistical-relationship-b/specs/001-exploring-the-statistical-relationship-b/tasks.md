# Tasks: Exploring the Statistical Relationship Between Solar Wind Composition and Geomagnetic Indices

**Input**: Design documents from `/specs/001-solar-wind-composition-geomagnetic/`
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

- [ ] T001 Create project directory structure: Run a setup script to create `projects/PROJ-505-exploring-the-statistical-relationship-b/` and all subdirectories (`code/`, `data/`, `tests/`, `code/ingestion`, `code/analysis`, `code/utils`, `data/raw`, `data/processed`, `data/artifacts`, `tests/unit`, `tests/integration`). **Verification**: Execute `test -d projects/PROJ-505-exploring-the-statistical-relationship-b/code/ingestion && echo 'OK'` for each directory. <!-- ATOMIZE: Consolidated from T001-T012 -->

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [X] T017 Initialize Python project with `requirements.txt` (pandas, numpy, scikit-learn, statsmodels, scipy, pytest, ruff, black).
- [X] T018 [P] Implement `code/utils/io.py` for checksumming and parquet loading.
- [X] T019 Create base configuration for random seeds and file paths in `code/config.py`.
- [X] T020 Setup error handling and logging infrastructure in `code/utils/logging.py`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Temporal Alignment (Priority: P1) 🎯 MVP

**Goal**: Download, parse, and align time-series data from ACE/WIND and NOAA into a unified hourly dataset. Handles real-data fetch attempts and falls back to synthetic generation due to data gaps.

**Independent Test**: Execute the ingestion script and verify the output CSV/Parquet contains exactly one row per hour for the study period, with no missing values in core index columns (Dst, Kp) and monotonically increasing timestamps.

### Implementation for User Story 1

- [ ] T021a [US1] Implement `code/ingestion/generate_synthetic_data.py` (Data Logic): Create the core logic to generate a multi-year hourly dataset mimicking ACE/WIND composition and NOAA indices distributions. **Verification**: Unit test `tests/unit/test_synthetic.py::test_distributions` confirms realistic ranges and no NaNs.
- [ ] T021b [US1] Implement `code/ingestion/generate_synthetic_data.py` (Seeding): Implement random seed pinning and reproducibility logic. **Verification**: Unit test `tests/unit/test_synthetic.py::test_reproducibility` confirms identical output for same seed.
- [ ] T021c [US1] Implement `code/ingestion/generate_synthetic_data.py` (Output): Implement writing logic to `data/processed/synthetic_aligned.parquet`. **Verification**: Unit test `tests/unit/test_synthetic.py::test_output_format` confirms file schema.
- [ ] T022 [US1] Implement `code/ingestion/download_ace.py`: Attempt fetch from CDAWeb. **Logic**: Do NOT catch exceptions silently. If fetch fails, raise `ConnectionError` with a clear message. The execution stage will catch this and trigger the fallback generator (T021). **Verification**: Unit test `tests/unit/test_download.py::test_no_fallback_on_network_error` confirms exception is raised, not suppressed.
- [ ] T023 [US1] Implement `code/ingestion/download_noaa.py`: Attempt fetch from NOAA Dst/Kp archives. **Logic**: Do NOT catch exceptions silently. If fetch fails, raise `ConnectionError` with a clear message. The execution stage will catch this and trigger the fallback generator (T021). **Verification**: Unit test `tests/unit/test_download.py::test_no_fallback_on_network_error` confirms exception is raised, not suppressed.
- [ ] T024 [US1] Implement `code/ingestion/align.py`: Merge real/synthetic sources (orchestrated by execution stage). Handle data gaps (>6h) via interpolation/flagging, resample to a regular hourly median, apply epsilon floor for zero-velocity/IMF ratios, and handle instrument version transitions. **Memory Constraint**: Monitor memory usage; if > 6GB, `raise MemoryError` immediately (do not defer). **Verification**: Unit test `tests/unit/test_align.py::test_offset_limit` confirms temporal offset ≤ 30 minutes. Unit test `tests/unit/test_align.py::test_memory_limit` confirms `MemoryError` on threshold.
- [ ] T043 [US1] Verification: Ensure `download_ace.py` and `download_noaa.py` do not silently catch exceptions. **Verification**: Run `pytest tests/unit/test_download.py::test_no_fallback_on_network_error` and confirm pass.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests AFTER implementation to verify the logic**

- [X] T026 [US1] Unit test for data alignment logic in `tests/unit/test_ingestion.py` (verify 1-hour resampling and median aggregation).
- [X] T027 [US1] Unit test for synthetic data generator in `tests/unit/test_synthetic.py` (verify realistic distributions and no NaNs in critical columns).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Multivariate Regression and Predictive Power Assessment (Priority: P2)

**Goal**: Perform multivariate linear regression to assess if composition ratios (O/Fe, He/H, C/O) provide independent predictive power for Dst/Kp beyond bulk coupling functions.

**Independent Test**: Run the regression module and verify output includes coefficient tables, p-values, and ΔR² between baseline (coupling functions only) and full (coupling + composition) models.

### Implementation for User Story 2

- [X] T028 [US2] Implement `code/analysis/coupling_functions.py`: Derive Akasofu epsilon, Newell function, and other bulk-parameter coupling functions from aligned data.
- [X] T029 [US2] Implement `code/analysis/regression.py`: Fit baseline model (coupling functions only) and full model (coupling + composition ratios); calculate coefficients, p-values, and VIF; **explicitly flag and output a warning artifact for any predictor with VIF ≥ 5**. **Prerequisite: T024 (align.py) must be complete.** **Failure Propagation**: If T024 raises `MemoryError`, this task must fail with a clear error message indicating the dependency failure. **Pre-computation**: Verify aligned dataset is loaded and contains no NaNs in target/predictor columns; raise descriptive error if found. **Verification**: Unit test `tests/unit/test_regression.py::test_nan_detection_raises_error`.
- [X] T030 [US2] Implement `code/analysis/cross_validation.py`: Perform k-fold cross-validation to assess out-of-sample R² for both models and calculate ΔR². **Prerequisite: T029 (regression.py) must be complete.**
- [ ] T031 [US2] Integrate regression results into `data/artifacts/`. **Output**: `data/artifacts/regression_results.csv` (columns: `model_type`, `coefficient`, `std_err`, `p_value`, `vif`) and `data/artifacts/model_metrics.json` (keys: `baseline_r2`, `full_r2`, `delta_r2`, `cv_r2_baseline`, `cv_r2_full`). **Verification**: Integration test `tests/integration/test_regression.py::test_regression_artifacts_exist`.
- [ ] T044 [US2] Add a pre-computation check in `code/analysis/regression.py`: Verify that the aligned dataset from T024 is fully loaded and contains no NaN values in the target columns (Dst, Kp) or predictor columns before fitting the model. If NaNs are present, raise a descriptive error citing the specific column and row count, rather than relying on `statsmodels` to drop rows silently. **Verification**: Unit test `tests/unit/test_regression.py::test_nan_detection_raises_error`.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T032 [US2] Unit test for coupling function derivation in `tests/unit/test_coupling.py` (verify Akasofu epsilon/Newell function calculations).
- [X] T033 [US2] Integration test for regression pipeline in `tests/integration/test_regression.py` (verify ΔR² calculation and VIF check).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance and Sensitivity Analysis (Priority: P3)

**Goal**: Validate statistical significance using block permutation tests and perform sensitivity analysis on thresholds to ensure robustness.

**Independent Test**: Run the significance module and verify block permutation generates a null distribution, and sensitivity analysis reports predictor stability across thresholds.

### Implementation for User Story 3

- [X] T034 [US3] Implement `code/analysis/permutation_test.py`: Execute block permutation test (minimum 1,000 iterations, 24h blocks, **max [deferred] iterations**) to generate null distributions for composition coefficients. **Logic**: Continue iterating until p-value standard error < 0.001 (calculated as sqrt(p*(1-p)/N)) OR N reaches [deferred]. Calculate and output the percentile range of the null distribution. Log final iteration count and stability status. **Prerequisite: T029 (regression.py) must be complete.**
- [X] T035 [US3] Implement `code/analysis/sensitivity.py`: Sweep significance thresholds across a range of standard levels (e.g., 0.05, 0.10).. **Explicitly apply Benjamini-Hochberg FDR correction to the 6 hypothesis tests (O/Fe-Dst, O/Fe-Kp, He/H-Dst, He/H-Kp, C/O-Dst, C/O-Kp)**. **Output**: `data/artifacts/fdr_results.csv` (columns: `hypothesis`, `raw_p`, `fdr_p`, `significant`). Report variation in significant predictors. **Prerequisite: T029 (regression.py) must be complete.**
- [X] T036 [US3] Implement final reporting logic in `code/main.py`: Aggregate all results. **Data Provenance**: Since real data sources are unavailable per Plan.md, explicitly label data as 'Synthetic' in the final report. **Verification**: Check `data/artifacts/final_report.json` contains `source_type: "Synthetic"`.
- [ ] T046 [US3] Update `code/main.py` to include a "Data Provenance" section in the final report output. **Output**: Append a JSON block to `data/artifacts/final_report.json` with keys `source_type` (value: "Synthetic" for this project instance due to data gap) and `fetch_attempts` (list of attempted URLs and their failure status). **Verification**: Check `data/artifacts/final_report.json` contains the expected JSON structure.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T037 [US3] Unit test for block permutation logic in `tests/unit/test_permutation.py` (verify 24-hour block shuffling and null distribution generation).
- [X] T038 [US3] Integration test for sensitivity analysis in `tests/integration/test_sensitivity.py` (verify threshold sweep and FDR correction application).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T039 [P] Documentation updates in `README.md` (explicitly state data gap and synthetic nature if fallback used).
- [X] T040 [P] Refactor `code/analysis/regression.py` to reduce cyclomatic complexity to < 10.
- [X] T041 [P] Refactor `code/analysis/permutation_test.py` to reduce cyclomatic complexity to < 10.
- [ ] T042 [P] Run quickstart.md validation. **Definition**: Execute `./quickstart.sh` and verify exit code 0. **Verification**: Check `exit_code == 0`.

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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2). **Internal Dependency**: T022 and T023 are independent of T021; T024 orchestrates their output.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2). **Dependency**: Depends on T024 (US1) output.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2). **Dependency**: Depends on T029 (US2) model output.

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
Task: "Unit test for data alignment logic in tests/unit/test_ingestion.py"
Task: "Unit test for synthetic data generator in tests/unit/test_synthetic.py"

# Launch all models for User Story 1 together:
Task: "Implement code/ingestion/generate_synthetic_data.py (T021a, T021b, T021c)"
Task: "Implement code/ingestion/download_ace.py (T022)"
Task: "Implement code/ingestion/download_noaa.py (T023)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Ensure T021a-c are done before T022/T023/T024)
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
 - Developer A: User Story 1 (T021a-c, T022, T023, T024)
 - Developer B: User Story 2 (T028, T029, T030)
 - Developer C: User Story 3 (T034, T035)
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
- **Critical Note**: All data used in this pipeline is synthetic due to unavailability of verified real-world ACE SWICS and NOAA Dst/Kp sources. Scientific hypothesis testing is not possible; only pipeline validation is achieved. All output artifacts MUST be explicitly labeled as 'synthetic' in the final report. The pipeline is designed to handle real data per FR-001/002 if available, but will raise exceptions and log failures if real fetch is attempted and fails.
- **Data Integrity Rule**: The ingestion scripts (T022, T023) must NOT silently fall back to synthetic data on network failure. They must raise an exception to allow the execution stage to identify the real data gap. Synthetic generation is a distinct, logged step only invoked after explicit failure of real fetch attempts.