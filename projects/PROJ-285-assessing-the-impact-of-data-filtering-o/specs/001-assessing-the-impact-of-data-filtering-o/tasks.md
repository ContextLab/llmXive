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

- [ ] T001a Create project directory structure per implementation plan in `projects/PROJ-285-assessing-the-impact-of-data-filtering-o/` including: `code/`, `code/src/`, `data/`, `data/raw/`, `data/processed/`, `tests/`, `tests/unit/`, `tests/integration/`
- [X] T001b Initialize `code/requirements.txt` with dependencies (pandas, astropy, scipy, matplotlib, numpy, statsmodels, requests, pyyaml, datasets)
- [ ] T002 [P] Configure linting (flake8/black) and formatting tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement data ingestion for the **Strong Lens Finding Challenge (SLFC)** dataset (the verified proxy for DES) in `code/src/data_loader.py`. Extract `is_lens` labels from the SLFC dataset and save them to `data/raw/real_labels.csv` to serve as ground truth for purity calculation (FR-003). **Do NOT use this file for injection recovery.**
- [ ] T006 [Depends on T004] Implement **Simulated Injection Generation** in `code/src/data_loader.py`. **Inject synthetic lens images** at random coordinates into the SLFC background to create a ground truth catalog. Save this to `data/raw/injection_ground_truth.csv` with columns `RA`, `Dec`, `injected_id`. This satisfies FR-008's requirement for an explicit *injection/recovery* simulation catalog. **This task is the sole producer of the injection catalog to avoid race conditions with T004.**
- [ ] T005 [P] Implement chunked CSV/Parquet loader in `code/src/loader.py` to process the **SLFC dataset** without loading the full dataset into RAM (FR-001). MUST log peak memory usage to `data/processed/memory_profile.csv`. If usage exceeds **6GB** (per plan.md constraint), **log a warning but do not fail the build**, satisfying SC-005's measurement requirement.
- [X] T007 [P] Create coordinate matching utility in `code/src/utils.py` to handle RA/Dec matching with ≤ 1.0 arcsec tolerance (FR-003, FR-008)
- [~] T008 [P] Setup `pytest` configuration and unit test scaffolding in `tests/unit/` <!-- SKIPPED: YAML+regex parse failed (mapping values are not allowed here
 in "<unicode string>", line 2, column 13:
 contents: |
 ^) -->
- [~] T009 [P] Implement basic error handling and logging infrastructure in `code/src/`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Detection Metrics Across Threshold Grid (Priority: P1) 🎯 MVP

**Goal**: Apply a systematic grid of SNR (5–20σ) and morphology (0.3–0.9) thresholds to the SLFC catalog to generate a complete detection matrix.

**Independent Test**: Run the filtering script on the SLFC dataset and verify the output CSV contains rows for every unique threshold pair across all SNR and Morph steps with non-negative integer counts.

### Tests for User Story 1

- [X] T010 [P] [US1] Unit test for threshold grid generation logic in `tests/unit/test_filter.py` (verify grid dimensions)
- [X] T011 [P] [US1] Unit test for handling missing values (NA/NaN) in `tests/unit/test_filter.py` (verify exclusion without crash)

### Implementation for User Story 1

- [X] T012 [US1] Implement `filter_by_thresholds()` in `code/src/filter.py` to iterate SNR (`range(5, 21, 1)`) and Morph (`np.arange(0.3, 0.95, 0.1)`) and count detections (FR-002). **Explicitly ensure the grid includes a representative threshold value near the upper bound of the parameter range.**.
- [ ] T013 [US1] Implement logic to exclude rows with missing SNR or morphology values per US-1 acceptance criteria
- [ ] T014 [US1] Generate `data/processed/detection_matrix.csv` containing `snr_threshold`, `morph_threshold`, `detection_count` (FR-002)
- [ ] T014b [US1] [Depends on T014] Generate `data/processed/detected_candidates.csv` containing the list of `RA`, `Dec`, `is_lens`, and `threshold_pair_id` for all candidates passing each threshold pair. This artifact is required for T018 (purity), T020a (variance), and T021 (recovery).
- [ ] T015 [US1] Add logging for grid iteration progress in `code/src/filter.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Validate Purity, Variance, Sensitivity, and Recovery (Priority: P2)

**Goal**: Cross-reference detection candidates against the SLFC ground truth validation catalog to calculate True Positives (TP), False Positives (FP), and Purity metrics, and perform secondary analyses.

**Independent Test**: Provide the detection matrix and validation catalog; verify the script correctly identifies overlaps within 1.0 arcsec tolerance and calculates `TP / (TP + FP)`.

### Tests for User Story 2

- [ ] T016 [P] [US2] Unit test for coordinate matching logic in `tests/unit/test_validate.py` (verify 1.0 arcsec tolerance)
- [ ] T017 [P] [US2] Unit test for purity calculation edge cases (division by zero) in `tests/unit/test_validate.py`

### Implementation for User Story 2

- [ ] T018 [US2] [Depends on T014, T014b, T004] **Calculate Purity Metrics**:
 1. Cross-reference `data/processed/detected_candidates.csv` (T014b) with `data/raw/real_labels.csv` (T004) using coordinate matching.
 2. Calculate TP, FP, and Purity for each threshold pair.
 3. Append `tp_count`, `fp_count`, `purity_score` to `data/processed/detection_matrix.csv`.

- [ ] T020a [US2] [Depends on T014b] **Calculate Detection Rate Variance**:
 1. For **EACH threshold pair** (row) in the analysis, perform 100 bootstrap resamples of the *rows* in `data/processed/detected_candidates.csv` corresponding to that threshold.
 2. Calculate the **variance of detection counts** across these 100 resamples for that specific row.
 3. Append `detection_rate_variance` (per-row metric) to `data/processed/detection_matrix.csv` to satisfy SC-001. **Output must be a per-row metric, not a global scalar.**

- [ ] T020b [US2] [Depends on T014b, T018, T004] **Perform Sensitivity Analysis**:
 1. **Baseline Definition**: The baseline SNR is **10σ**.
 2. Sweep SNR cutoff (Base 10σ ± 0.5σ, ± 1.0σ).
 3. Calculate `false_positive_rate` (FP / Total Non-Lenses) for each step. **Use the total non-lens count derived from `data/raw/real_labels.csv` (T004) as the denominator.**
 4. Calculate `fpr_delta` as `FPR(sweep) - FPR(baseline=10σ)`.
 5. Output to `data/processed/sensitivity_sweep.csv` to satisfy FR-006 and SC-002.

- [ ] T021 [US2] [Depends on T014b, T006] **Validate Injection Recovery**:
 1. Compare `data/processed/detected_candidates.csv` (filtered results from T014b) against `data/raw/injection_ground_truth.csv` (T006).
 2. Confirm ≥ 95% of simulated lenses are recovered within 1.0 arcsec.
 3. Generate `data/processed/recovery_report.json` with `recovery_rate` and `pass` boolean to satisfy FR-008.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Comparison and Visualization (Priority: P3)

**Goal**: Perform Cumulative Link Models (CLM) and Bootstrap goodness-of-fit tests to compare detection distributions and generate plots.

**Independent Test**: Feed the metrics CSV to the stats module and verify it outputs a valid p-value, CLM coefficient, and two `.png` plot files.

### Tests for User Story 3

- [ ] T024 [P] [US3] Unit test for Bootstrap goodness-of-fit implementation in `tests/unit/test_stats.py`
- [ ] T025 [P] [US3] Unit test for Benjamini-Yekutieli FDR correction in `tests/unit/test_stats.py`

### Implementation for User Story 3

- [ ] T026 [US3] Implement **Cumulative Link Models (CLM)** trend analysis in `code/src/stats.py` to compare detection distributions (replacing Logistic Regression per Plan Complexity); output raw p-values to `data/processed/raw_p_values.csv` for use in T028a (FR-005, SC-003)
- [ ] T027 [US3] Implement Bootstrap goodness-of-fit test in `code/src/stats.py` for nested data. **Null Hypothesis**: Observed detection counts across thresholds follow the expected cumulative distribution. **Metric**: Sum of squared residuals between observed and expected counts per threshold bin. Output raw p-values to `data/processed/raw_p_values.csv` (FR-005)
- [ ] T028 [US3] [Depends on T026, T027] Consolidate all raw p-values from T026 and T027 into `data/processed/raw_p_values.csv`
- [ ] T028a [US3] [Depends on T028] Apply **Benjamini-Yekutieli (BY)** FDR correction to p-values in `data/processed/raw_p_values.csv` to control family-wise error across the threshold grid; write corrected p-values to `data/processed/fdr_results.csv` (FR-005)
- [ ] T029 [US3] Implement visualization module in `code/src/viz.py` to generate `detection_rate_vs_threshold.png` and `purity_curve.png` (FR-007)
- [ ] T030 [US3] Ensure plot generation respects disk limits (no massive image files) (FR-007)
- [ ] T030a [US3] Add verification step to assert generated PNG files do not exceed disk limits; fail build if limit exceeded (FR-007)
- [ ] T031 [US3] Output final summary CSV to `data/processed/final_summary.csv` containing `clm_coefficient`, `bootstrap_p_value`, `fdr_corrected_p_value`, and trend conclusion (SC-003). **Verification**: Assert that `bootstrap_p_value < 0.05` to confirm a significant trend as required by SC-003. **If the condition is not met, the task must fail.**

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032a [P] Update `README.md` with usage examples and setup instructions
- [ ] T032b [P] Generate `docs/api.md` documentation for core modules
- [ ] T033a Code cleanup and refactoring of `code/src/stats.py` to reduce cyclomatic complexity < 10
- [ ] T033b Code cleanup and refactoring of `code/src/filter.py` to reduce cyclomatic complexity < 10
- [ ] T034 Performance optimization: verify chunking reduces memory usage to < 6 GB (SC-005)
- [ ] T035 [P] Integration test for full pipeline flow in `tests/integration/test_pipeline.py`
- [ ] T036 Run `quickstart.md` validation to ensure end-to-end execution on free-tier CI (SC-004)

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
- **User Story 2 (P2)**: Depends on US1 (needs `data/processed/detection_matrix.csv` and `detected_candidates.csv` output from T014/T014b)
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
 - Developer B: User Story 2 (Validation/Purity) - *Must wait for T014/T014b output*
 - Developer C: User Story 3 (Stats/Viz) - *Must wait for T020 output*
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Data Hygiene**: All data ingestion must use fixed random seeds for reproducibility (Constitution Principle I).
- **Real Data**: This project uses the **Strong Lens Finding Challenge (SLFC)** dataset as the verified proxy for DES (Plan Assumption).
- **Performance**: Ensure all processing is chunked to fit within 6GB RAM limit (SC-005, Plan Constraints).
- **Statistical Methodology**: This project strictly follows `spec.md` FR-005 (Benjamini-Yekutieli) and Plan Complexity Tracking (Cumulative Link Models), overriding any conflicting methodology mentioned in `plan.md` or `spec.md` regarding Logistic Regression.
- **Injection Simulation**: T006 explicitly generates simulated injections to satisfy FR-008, distinct from real labels in T004.