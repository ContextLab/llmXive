# Tasks: Assessing the Impact of Data Filtering on Gravitational Lens Detection Rates

**Input**: Design documents from `/specs/001-assessing-the-impact-of-data-filtering-o/`
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

- [ ] T001a Create project directory structure per implementation plan in `projects/PROJ-285-assessing-the-impact-of-data-filtering-o/`
- [ ] T001b Initialize `code/requirements.txt` with dependencies (pandas, astropy, scipy, matplotlib, numpy, statsmodels, requests)
- [ ] T002 [P] Configure linting (flake8/black) and formatting tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement deterministic synthetic data generator in `code/src/injector.py` to create DES-like catalog with `SNR`, `morphology_score`, `RA`, `Dec` and known ground-truth injection positions; MUST save injection positions to `data/raw/injection_ground_truth.csv` to serve as explicit input for T021 (FR-008)
- [ ] T005 [P] Implement chunked CSV loader in `code/src/loader.py` to process synthetic data without loading full dataset into RAM (FR-001); MUST log peak memory usage to `data/processed/memory_profile.log` and include an explicit assertion step that fails the build if usage exceeds 7GB to satisfy SC-005
- [ ] T006 Create coordinate matching utility in `code/src/utils.py` to handle RA/Dec matching with ≤ 1.0 arcsec tolerance (FR-003, FR-008)
- [ ] T007 Setup `pytest` configuration and unit test scaffolding in `tests/unit/`
- [ ] T008 Implement basic error handling and logging infrastructure in `code/src/`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Detection Metrics Across Threshold Grid (Priority: P1) 🎯 MVP

**Goal**: Apply a systematic grid of SNR (5–20σ) and morphology (0.3–0.9) thresholds to the catalog to generate a complete detection matrix.

**Independent Test**: Run the filtering script on the synthetic dataset and verify the output CSV contains rows for every unique threshold pair (multiple SNR steps × 7 Morph steps) with non-negative integer counts.

### Tests for User Story 1

- [ ] T009 [P] [US1] Unit test for threshold grid generation logic in `tests/unit/test_filter.py` (verify grid dimensions)
- [ ] T010 [P] [US1] Unit test for handling missing values (NA/NaN) in `tests/unit/test_filter.py` (verify exclusion without crash)

### Implementation for User Story 1

- [ ] T011 [US1] Implement `filter_by_thresholds()` in `code/src/filter.py` to iterate SNR (low-to-high) and Morph (0.3-0.9, step 0.1) and count detections (FR-002)
- [ ] T012 [US1] Implement logic to exclude rows with missing SNR or morphology values per US-1 acceptance criteria
- [ ] T013 [US1] Generate `data/processed/detection_matrix.csv` containing `snr_threshold`, `morph_threshold`, `detection_count` (FR-002)
- [ ] T014 [US1] Add logging for grid iteration progress in `code/src/filter.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Validate Purity Against Independent Catalog (Priority: P2)

**Goal**: Cross-reference detection candidates against the independent validation catalog to calculate True Positives (TP), False Positives (FP), and Purity metrics.

**Independent Test**: Provide a mock detection list and validation catalog; verify the script correctly identifies overlaps within 1.0 arcsec tolerance and calculates `TP / (TP + FP)`.

### Tests for User Story 2

- [ ] T015 [P] [US2] Unit test for coordinate matching logic in `tests/unit/test_validate.py` (verify 1.0 arcsec tolerance)
- [ ] T016 [P] [US2] Unit test for purity calculation edge cases (division by zero) in `tests/unit/test_validate.py`

### Implementation for User Story 2

- [ ] T017 [US2] [Depends on T013] Implement `calculate_purity()` in `code/src/validate.py` to cross-reference `data/processed/detection_matrix.csv` (from T013) with `data/raw/validation_catalog.csv` (FR-003)
- [ ] T018 [US2] Implement coordinate matching logic using `astropy.coordinates.SkyCoord` with a tolerance appropriate for the survey resolution. (FR-003, FR-008)
- [ ] T019 [US2] [Depends on T013] Update `data/processed/detection_matrix.csv` to include `tp_count`, `fp_count`, `purity_score` columns
- [ ] T019a [US2] Calculate `detection_rate_variance` for every threshold pair by computing the variance of detection counts across multiple bootstrap resamples of the input data; append this metric to `data/processed/detection_matrix.csv` to satisfy SC-001
- [ ] T020 [US2] Implement sensitivity analysis logic: 1) Perform SNR sweep over ±0.5σ, ±1.0σ offsets; 2) Calculate false-positive rates for each offset; 3) Prepare data for variation report (FR-006, SC-002)
- [ ] T020b [US2] Write sensitivity analysis results to `data/processed/sensitivity_sweep.csv` with columns `snr_offset`, `false_positive_rate`, and `fpr_delta` (variation from baseline) to explicitly satisfy FR-006 and SC-002
- [ ] T021 [US2] Validate injection recovery rate: confirm ≥ 95% of simulated lenses are recovered with the chosen tolerance; MUST generate `data/processed/recovery_report.json` containing `recovery_rate` and a `pass` boolean to explicitly verify FR-008

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Comparison and Visualization (Priority: P3)

**Goal**: Perform Logistic Regression/Bootstrap goodness-of-fit tests and generate plots showing detection rate and purity curves.

**Independent Test**: Feed the metrics CSV to the stats module and verify it outputs a valid p-value, logistic coefficient, and two `.png` plot files.

### Tests for User Story 3

- [ ] T022 [P] [US3] Unit test for Bootstrap goodness-of-fit implementation in `tests/unit/test_stats.py`
- [ ] T023 [P] [US3] Unit test for Benjamini-Hochberg FDR correction in `tests/unit/test_stats.py`

### Implementation for User Story 3

- [ ] T024 [US3] Implement Logistic Regression trend analysis in `code/src/stats.py` to compare detection distributions; output raw p-values to `data/processed/raw_p_values.csv` for use in T026a (FR-005, SC-003)
- [ ] T025 [US3] Implement Bootstrap goodness-of-fit test in `code/src/stats.py` for nested data; output raw p-values to `data/processed/raw_p_values.csv` for use in T026a (FR-005)
- [ ] T026 [US3] Ensure `data/processed/raw_p_values.csv` is generated with all p-values from T024 and T025
- [ ] T026a [US3] Apply Benjamini-Hochberg FDR correction to p-values in `data/processed/raw_p_values.csv` to control family-wise error across the threshold grid; write corrected p-values to `data/processed/fdr_results.csv` (FR-005)
- [ ] T027 [US3] Implement visualization module in `code/src/viz.py` to generate `detection_rate_vs_threshold.png` and `purity_curve.png` (FR-007)
- [ ] T028 [US3] Ensure plot generation respects disk limits (no massive image files) (FR-007)
- [ ] T028a [US3] Add verification step to assert generated PNG files do not exceed disk limits; fail build if limit exceeded (FR-007)
- [ ] T029 [US3] Output final summary CSV to `data/processed/final_summary.csv` containing `logistic_p_value`, `bootstrap_p_value`, `fdr_corrected_p_value`, and trend conclusion (SC-003)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030a [P] Update `README.md` with usage examples and setup instructions
- [ ] T030b [P] Generate `docs/api.md` documentation for core modules
- [ ] T031a Code cleanup and refactoring of `code/src/stats.py` to reduce cyclomatic complexity < 10
- [ ] T031b Code cleanup and refactoring of `code/src/filter.py` to reduce cyclomatic complexity < 10
- [ ] T032 Performance optimization: verify chunking reduces memory usage to < 7 GB (SC-005)
- [ ] T033 [P] Integration test for full pipeline flow in `tests/integration/test_pipeline.py`
- [ ] T034 Run `quickstart.md` validation to ensure end-to-end execution on free-tier CI (SC-004)

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
- **User Story 2 (P2)**: Depends on US1 (needs `data/processed/detection_matrix.csv` output from T013)
- **User Story 3 (P3)**: Depends on US2 (needs purity metrics and statistical data)
- **Polish**: Depends on all US1, US2, US3 completion

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utilities before services
- Services before endpoints/visualization
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (with data dependencies managed)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Unit test for threshold grid generation logic in tests/unit/test_filter.py"
Task: "Unit test for handling missing values in tests/unit/test_filter.py"

# Launch implementation tasks:
Task: "Implement filter_by_thresholds() in code/src/filter.py"
Task: "Implement logic to exclude rows with missing SNR or morphology values"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (grid generation and counting)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Purity metrics)
4. Add User Story 3 → Test independently → Deploy/Demo (Stats & Viz)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Filtering)
   - Developer B: User Story 2 (Validation/Purity) - *Must wait for T013 output*
   - Developer C: User Story 3 (Stats/Viz) - *Must wait for T019 output*
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Data Hygiene**: All synthetic data generation must use fixed random seeds for reproducibility (Constitution Principle I).
- **Real Data**: This project uses synthetic data mimicking DES properties due to lack of verified external URL (Plan Assumption).
- **Performance**: Ensure all processing is chunked to fit within 7GB RAM limit (SC-005).
- **Statistical Methodology**: This project strictly follows `spec.md` FR-005 (Benjamini-Hochberg FDR) and US-3 (Logistic Regression), overriding any conflicting methodology mentioned in `plan.md`. The plan's reference to "Beta Regression" is noted as a contradiction and must be resolved in the plan artifact before execution.