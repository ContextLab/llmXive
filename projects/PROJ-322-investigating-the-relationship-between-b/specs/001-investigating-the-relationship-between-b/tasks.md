# Tasks: Investigating the Relationship Between Brain Network Reconfiguration and Recovery from Mild Traumatic Brain Injury

**Input**: Design documents from `/specs/001-brain-network-reconfiguration/`
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

- [X] T001 Create directory structure: `code/`, `data/raw/`, `data/processed/`, `data/results/`, `tests/` <!-- FAILED: unspecified -->

- [X] T002 Initialize Python 3.11 project with `requirements.txt` (pin `nilearn`, `networkx`, `statsmodels`, `pandas`, `numpy`, `scikit-learn`, `pyyaml`, `huggingface_hub`)

- [X] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/__init__.py` and shared configuration loader (`code/config.py`)

- [X] T007 Implement memory monitoring utility (`code/memory_monitor.py`) to enforce ≤6GB RAM limit during batch processing (FR-001, SC-005); expose `get_current_ram_gb()` and `is_limit_exceeded()` functions.

- [X] T005a [P] Initialize logging infrastructure (`code/logging_config.py`) with basic file handlers and rotation; do NOT configure memory hooks yet.

- [X] T005b [P] [Depends on T007] Configure logging hooks in `code/logging_config.py` to read memory state from T007 and emit "Time Limit Warning" logs when RAM usage approaches 6GB.

- [ ] T006 Create base data entities: `Subject`, `ConnectivityMatrix`, `GraphMetrics` classes in `code/entities.py`

- [ ] T008a [P] Implement synthetic data generator (`code/synthetic_data.py`) for "Methodology Validation Mode" with seeded random states.

- [X] T008b [P] [Depends on T004] Implement "Methodology Validation Mode" switch logic in `code/config.py` to set global `is_synthetic` flag based on data availability check. This task establishes the global project state for the mode.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Automated Data Acquisition and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Automatically locate, download, and perform minimal preprocessing on longitudinal resting-state fMRI datasets, ensuring data fits within RAM constraints.

**Independent Test**: The system can be tested by running `code/data_ingestion.py` against a specific OpenNeuro dataset ID; success is confirmed if the script outputs `data/results/manifest.csv` listing subject IDs, time points, and file paths, and logs "Memory OK" if peak RAM ≤ 6GB.

### Implementation for User Story 1

- [ ] T011 [US1] Implement `code/data_ingestion.py` to download OpenNeuro data (e.g., `ds000006` or similar mTBI dataset) and generate `data/results/manifest.csv`

- [X] T012 [US1] Implement `code/preprocessing.py` for minimal confound regression using `nilearn` and AAL parcellation

- [~] T013 [US1] Add logic to skip subjects with missing time points (acute/chronic) and log exclusion reasons (Edge Case)

- [~] T014 [US1] Add logic to handle AAL atlas failure (skip subject, log error) without crashing (Edge Case)

- [~] T016 [US1] Implement contingency check: if `n < 20`, switch to non-parametric bootstrapping by implementing `code/bootstrapping.py` (1000 iterations) and generating `data/results/bootstrapped_ci.json` (FR-009)

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation. Execution of these tasks requires the code from T011-T016 to exist.

- [X] T009 [P] [US1] Define and implement unit test `tests/unit/test_memory_monitor.py::test_get_current_ram_gb_returns_float` and `tests/unit/test_memory_monitor.py::test_is_limit_exceeded_raises_memory_error_when_ram_gt_6gb`

- [X] T010 [P] [US1] Define and implement integration test `tests/integration/test_data_ingestion.py::test_ingestion_skips_subjects_with_missing_time_points_and_logs_exclusion`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Graph Metric Calculation and Correlation Analysis (Priority: P2)

**Goal**: Compute global/local efficiency and modularity, then fit a linear mixed-effects model to test correlation with cognitive recovery.

**Independent Test**: The system can be tested by running `code/graph_metrics.py` and `code/statistical_model.py` on a small dataset; success is confirmed if `data/results/metrics.json` contains computed values and `data/results/model_results.json` contains fixed-effect coefficients, p-values, and confidence intervals.

### Implementation for User Story 2

- [X] T019 [P] [US2] Implement `code/graph_metrics.py` to compute Global Efficiency, Local Efficiency, and Modularity (Q) from connectivity matrices using `networkx` (FR-002)

- [~] T020 [US2] Implement proportional sparsity thresholding on connectivity matrices before metric calculation. (FR-008)

- [X] T021 [US2] Implement `code/statistical_model.py` to fit Linear Mixed-Effects Model: `CognitiveScore ~ Efficiency + Modularity + Time + (1|Subject)` (FR-003)

- [ ] T022a [US2] Implement VIF calculation; if VIF > 5, attempt PCA on graph metrics. Success criteria: eigenvalues > 0 AND cumulative variance explained > 60%. If successful, output `data/results/pca_metrics.json`.

- [ ] T022b [US2] [Depends on T022a] If PCA fails (catch `numpy.linalg.LinAlgError` for singular matrix/rank deficiency OR if cumulative variance < 60%), generate `data/results/descriptive_vif_report.json`. This report MUST contain the correlation matrix of predictors and variance decomposition to describe the joint relationship (FR-006).

- [~] T023 [US2] Handle non-convergence: log warning, skip subject, continue processing batch (Edge Case)

- [~] T024a [US2] Search for real independent functional metric (e.g., Return-to-Work) by querying OpenNeuro metadata API for clinical/behavioral derivatives and checking for columns like 'ReturnToWork', 'RTW', or 'EmploymentStatus' in the manifest.

- [~] T024b [US2] [Depends on T024a] If T024a found no real independent metric, immediately write `validation_gap: true` flag with a detailed search log in `data/results/gaps.json` and SKIP the `code/validation.py` implementation and `external_validation.json` generation (FR-007). If a metric is found, implement validation correlation in `code/validation.py` and output `data/results/external_validation.json` (FR-007).

- [~] T025 [US2] Ensure output JSON includes `is_synthetic` flag if running in Methodology Validation Mode (Plan Contingency)

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Define and implement unit test `tests/unit/test_graph_metrics.py::test_global_efficiency_returns_positive_scalar_for_connected_graph` and `tests/unit/test_graph_metrics.py::test_modularity_returns_value_between_0_and_1`

- [X] T018 [P] [US2] Define and implement unit test `tests/unit/test_collinearity.py::test_vif_calculation_returns_infinite_for_perfectly_collinear_predictors` and `tests/unit/test_collinearity.py::test_pca_fallback_triggers_when_vif_gt_5_and_variance_explained_gt_60`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness Validation and Sensitivity Reporting (Priority: P3)

**Goal**: Perform permutation testing (sufficient iterations) and sensitivity analysis on correlation cutoffs to ensure robustness.

**Independent Test**: The system can be tested by running `code/robustness.py`; success is confirmed if output includes a histogram of the null distribution, a table showing correlation coefficient variation across thresholds, AND the final `analysis_report.json` contains a `compliance_status` object with `runtime_ok` and `memory_ok` flags verifying SC-004/SC-005.

### Implementation for User Story 3

- [X] T028 [P] [US3] Implement `code/robustness.py` with a sufficient number of permutation iterations to calculate empirical p-value. (FR-004, SC-002)

- [ ] T029 [US3] Implement sensitivity analysis: sweep correlation thresholds based on data-driven representative values (e.g., quantiles of correlation distribution) and output `data/results/sensitivity_analysis.csv` (FR-005, SC-003)

- [~] T030 [US3] Implement hard stop at 6 hours runtime with "Time Limit Warning" at 5 hours (FR-003, SC-004)

- [ ] T031 [US3] Generate final `data/results/analysis_report.json` containing all metrics, p-values, flags (synthetic, pilot, validation_gap), and limitations. Explicitly aggregate runtime and memory logs from T005b/T007 to verify SC-004/SC-005 compliance: read logs, parse metrics, compute `runtime_ok` (total_time <= 5h) and `memory_ok` (peak_ram <= 6GB) booleans, and include `compliance_status: { runtime_ok, memory_ok }` in the report.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Define and implement unit test `tests/unit/test_robustness.py::test_permutation_pvalue_is_less_than_parametric_pvalue_for_known_signal` and `tests/unit/test_robustness.py::test_permutation_iterations_match_input_parameter`

- [X] T027 [P] [US3] Define and implement integration test `tests/integration/test_sensitivity.py::test_sensitivity_sweep_outputs_table_with_varying_thresholds_and_correlation_coefficients`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T032 [P] Documentation updates in `docs/` and `README.md`

- [ ] T033 Code cleanup and refactoring for memory efficiency

- [ ] T034 Performance optimization for batch processing (ensure ≤5h runtime)

- [ ] T035 [P] Additional unit tests for edge cases in `tests/unit/`

- [ ] T036 Run `quickstart.md` validation to ensure pipeline executes end-to-end

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on model results from US2

### Within Each User Story

- Implementation tasks (T011-T016, T019-T025, T028-T031) MUST be completed before their corresponding Test tasks (T009/T010, T017/T018, T026/T027) to ensure code exists for testing.
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2), EXCEPT T005b which depends on T007. **Note: T005a (Logger init) is independent of T007 and can run in parallel with T007.**
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel (after implementation)
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all implementation tasks for User Story 1 together:
Task: "Implement code/data_ingestion.py to download OpenNeuro data"
Task: "Implement code/preprocessing.py for minimal confound regression"

# After implementation, launch tests:
Task: "Define and implement unit test for memory monitoring utility in tests/unit/test_memory_monitor.py::test_get_current_ram_gb_returns_float"
Task: "Define and implement integration test for data ingestion with missing time points in tests/integration/test_data_ingestion.py::test_ingestion_skips_subjects_with_missing_time_points_and_logs_exclusion"
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
 - Developer B: User Story 2 (Graph Metrics & Modeling)
 - Developer C: User Story 3 (Robustness & Validation)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies (except T005b which depends on T007)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All tasks must run on CPU-only CI with constrained resources (limited cores and RAM, no GPU). No 8-bit/4-bit quantization or deep learning training.
- **Data Integrity**: Only use real OpenNeuro datasets or explicitly flagged synthetic data for validation mode. No fake data fabrication for scientific claims.
- **Requirement Compliance**: Tasks must fully implement the logic required by FRs (e.g., bootstrapping, descriptive VIF reporting, external validation) rather than just flagging or preparing for them.