# Tasks: Quantifying the Impact of Network Structure on Energy Dissipation in Driven Granular Materials

**Input**: Design documents from `/specs/001-network-dissipation/`
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
 - Delivered as a MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-468-quantifying-the-impact-of-network-struct/`)
- [ ] T002 Initialize Python 3.11 project with pinned dependencies in `requirements.txt`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create `data/` directory structure (`raw/`, `processed/`) and `results/` in root
- [ ] T005 [P] Create `code/` directory structure with `__init__.py`
- [ ] T006 [P] Create `tests/` directory structure (`unit/`, `integration/`) with `__init__.py`
- [~] T007 Create `contracts/` directory and define `dataset.schema.yaml` for processed data and `results.schema.yaml` for analysis output
- [~] T008a [P] Implement `code/utils.py` function `estimate_memory_usage` that performs linear extrapolation from the **first 1000 lines** of the input file to predict total RAM usage, returning the estimated MB (FR-008)
- [~] T008b [P] Implement `code/utils.py` function `check_subsample_trigger` that compares the estimated memory from T008a against the 6GB threshold and returns a boolean flag for subsampling (FR-008)
- [~] T009 Create `code/main.py` CLI entry point with argument parsing for input file and output directory
- [~] T010 [P] Update `README.md` to document the invocation parameters and exit codes for the automated `Reference-Validator Agent` gate (Constitution Principle II)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Data Extraction and Metric Calculation (Priority: P1) 🎯 MVP

**Goal**: Ingest raw DEM output, extract contact networks, and calculate topology/energy metrics per timestep.

**Independent Test**: Run on a single small-scale synthetic DEM dataset; verify output CSV has non-null values for coordination, clustering, heterogeneity, and dissipation for every timestep.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T011 [P] [US1] Unit test `test_extract_handles_zero_overlap_returns_empty_graph` in `tests/unit/test_extract.py` verifying graph construction logic
- [~] T012 [P] [US1] Unit test `test_dissipation_fallback_zero_work` in `tests/unit/test_extract.py` verifying absolute energy change fallback when Work_Input is 0
- [~] T013 [P] [US1] Integration test `test_pipeline_flow_synthetic_data` in `tests/integration/test_pipeline_flow.py` verifying end-to-end CSV generation with non-null metrics <!-- FAILED: unspecified -->

### Implementation for User Story 1

- [~] T014a [US1] Implement `code/extract.py` class `YadeParser` with method `parse_positions` and `parse_forces` to extract raw data (FR-001)
- [~] T014b [US1] Implement `code/extract.py` method `build_contact_network` (edges defined by overlap > 0) and `calc_coordination_clustering` (FR-002, FR-002b)
- [~] T014c [US1] Implement `code/extract.py` method `calc_dissipation`: Calculate `Work_Input - (ΔKE + ΔPE)`; if `Work_Input > 0`, prepare for normalization; else return `|ΔKE + ΔPE|` (FR-003)
- [~] T014d [US1] Implement `code/extract.py` method `normalize_dissipation`: Calculate `normalized_dissipation_rate = Dissipation / Work_Input` if `Work_Input > 0`, else `NaN`; **write this column to the per-timestep CSV output** (FR-003, FR-004)
- [~] T014e [US1] Integration verification: Implement a test harness in `code/extract.py` to verify `YadeParser` instance produces a valid CSV row per timestep containing all required metrics (coordination, clustering, heterogeneity, normalized_dissipation) <!-- FAILED: unspecified -->
- [~] T015 [US1] Implement force heterogeneity (CV of contact forces) calculation **integrated into the per-timestep loop of `extract.py`**; **verify `force_heterogeneity` column exists and is non-null for all rows in `data/processed/metrics.csv`** (FR-002b)
- [~] T016a [US1] Implement handling for **missing force values**: log warnings; if <50% of *total expected contacts* missing, impute **missing force values** as 0.0, set `force_heterogeneity` to 0.0, and add `data_quality_flag` column with value `UNRELIABLE` (Spec Edge Cases: Missing Forces)
- [~] T016b [US1] Implement handling for **missing contacts (topological disconnect)**: if >50% of *total expected contacts* are missing, **exclude the entire timestep** from output; if <50% missing, set `clustering_coefficient` to 0.0 (representing no clustering) and do NOT impute forces, flagging the row (Spec Edge Cases: Disconnected Networks)
- [ ] T017 [US1] Implement "Topology-Only" (degree distribution entropy) and "Force-Only" (mean force magnitude on force chains) metrics to avoid circularity (FR-009)
- [ ] T018 [US1] Implement metadata extraction (driving amplitude, friction) and populate `metadata` header in processed CSV (Plan Phase 2)
- [ ] T019 [US1] Integrate subsampling trigger in `extract.py` using `check_subsample_trigger` from T008b if RAM > 6GB (FR-008)
- [ ] T020 [US1] Write processed data to `data/processed/` with derivation logs (Data Hygiene)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Correlation and Regression Analysis (Priority: P2)

**Goal**: Perform correlation and regression analysis with autocorrelation correction and robustness checks.

**Independent Test**: Feed pre-processed CSV with known correlations; verify output report identifies coefficients within 0.01 tolerance and correct p-values.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Unit test `test_pearson_spearman_correlation` in `tests/unit/test_analyze.py`
- [ ] T022 [P] [US2] Unit test `test_gls_newey_west_regression` in `tests/unit/test_analyze.py`
- [ ] T023 [P] [US2] Unit test `test_adf_stationarity_segmentation` in `tests/unit/test_analyze.py`

### Implementation for User Story 2

- [ ] T024 [US2] Implement Pearson and Spearman correlation analysis **using the `normalized_dissipation_rate` column** (from T014d), excluding 'ESTIMATED'/'UNRELIABLE' rows (FR-004)
- [ ] T025 [US2] Implement Generalized Least Squares (GLS) with AR(1) error structure or Newey-West corrected OLS **using the `normalized_dissipation_rate` column** (FR-005)
- [ ] T026 [US2] Include `driving_amplitude` as a control variable in the regression model (FR-005b)
- [ ] T027 [US2] Implement Augmented Dickey-Fuller (ADF) test; if non-stationary (p > 0.05), segment into 1000-timestep windows (FR-010)
- [ ] T027b [US2] Implement **aggregation logic** for segmented results: calculate weighted mean of coefficients and pooled p-values from windows; **write `results/regression_segments.csv` with aggregated metrics** (FR-010)
- [ ] T028 [US2] Implement non-linearity check: flag if residual quadratic term p < 0.05 or skewness > 0.5 (Spec US-2)
- [ ] T029 [US2] Implement Variance Inflation Factor (VIF) diagnostic for predictor collinearity (Assumption)
- [ ] T029b [US2] Implement **VIF reporting logic**: if VIF > 5, **append `collinearity_flag: HIGH` to `results/regression_summary.json`** and update T039 to include this flag in the report (Assumptions)
- [ ] T030 [US2] Generate intermediate analysis results to `results/` with coefficients, SEs, and p-values
- [ ] T031 [US2] Implement sensitivity analysis logic: sweep subsampling fraction, **generate `results/sensitivity_analysis.csv`**, and **verify slope coefficient variance < 0.05** to ensure robustness (Assumptions)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Cross-Dataset Validation and Visualization (Priority: P3)

**Goal**: Validate correlations across datasets and generate publication-ready PDF report.

**Independent Test**: Provide two distinct datasets; verify combined plot, ANOVA slope consistency, and PDF generation.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T032 [P] [US3] Integration test for multi-dataset ANOVA slope comparison in `tests/integration/test_validation.py`
- [ ] T033 [P] [US3] End-to-end test for PDF report generation in `tests/integration/test_report_gen.py`

### Implementation for User Story 3

- [ ] T034 [US3] Implement mixed-effects model or ANOVA to test for slope differences across datasets; **generate `results/anova_test.csv` containing F-statistic and p-value** (FR-006)
- [ ] T034b [US3] Implement **ANOVA interpretation logic**: read `results/anova_test.csv`; if p > 0.05, set `slope_consistency_text = "Slopes Consistent"`; else `slope_consistency_text = "Slopes Differ"`; **pass this string to the report generator** (SC-003)
- [ ] T035 [US3] Implement scatter plot generation with regression lines overlay for multiple datasets
- [ ] T036 [US3] Implement correlation heatmap and residual distribution plot generation (FR-007)
- [ ] T037 [US3] Implement time-series plot of dissipation rate vs. force heterogeneity (FR-007)
- [ ] T038 [US3] Implement logic to label "Non-significant" results (p > 0.05) and add explanatory notes (Spec US-3)
- [ ] T039 [US3] Generate final PDF report including all plots, statistical summaries, **`slope_consistency_text` from T034b**, **`collinearity_flag` from T029b**, and "Data Validity" section (Code vs. Science); **ensure automated `Reference-Validator Agent` gate passes before finalizing** (Plan Phase 3 Gated Step)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Documentation updates in `README.md` and `quickstart.md`
- [ ] T041 Code cleanup and refactoring in `code/`
- [ ] T042 Performance optimization for large file processing
- [ ] T043 [P] Additional unit tests for edge cases (truncated files, disconnected networks)
- [ ] T044 Security hardening (input validation)
- [ ] T045 Run `quickstart.md` validation to ensure reproducible execution

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires output from US1 (processed CSV)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires output from US2 (analysis results)

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
Task: "Unit test test_extract_handles_zero_overlap_returns_empty_graph in tests/unit/test_extract.py"
Task: "Unit test test_dissipation_fallback_zero_work in tests/unit/test_extract.py"

# Launch all models for User Story 1 together:
Task: "Create `data/` directory structure"
Task: "Create `code/` directory structure"
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