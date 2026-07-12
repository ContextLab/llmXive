# Tasks: Lottery Draw Integrity and Anomaly Detection

**Input**: Design documents from `/specs/001-lottery-draw-integrity/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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

- [ ] T001a [P] Create project directories: `mkdir -p data/raw data/processed data/results code tests/unit tests/integration`
- [ ] T001b [P] Initialize `__init__.py` files: `touch code/__init__.py tests/__init__.py tests/unit/__init__.py tests/integration/__init__.py`
- [ ] T002 Initialize Python 3.11 project with pinned dependencies (`pandas`, `numpy`, `scipy`, `requests`, `pyyaml`, `memory_profiler`, `pytest`) in `requirements.txt`
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin. This includes data ingestion as a prerequisite for all analysis.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `code/data_utils.py` for deterministic CSV loading and checksum verification (Constitution Principle III)
- [ ] T005 [P] Implement `code/constants.py` defining draw parameters (e.g., `NUMBERS_PER_DRAW=6`, `MAX_BALL=49`, `BIRTHDAY_THRESHOLD=31`)
- [ ] T006 [P] Create `code/exceptions.py` for custom data errors (e.g., `MissingSalesError`, `InvalidDrawFormatError`)
- [ ] T007 [P] Setup `tests/conftest.py` with fixtures for mock data and fixed random seeds
- [ ] T008 [P] Implement `code/ingestion.py` as a 'Pre-CI Data Fetch' script to download the UK National Lottery historical draws CSV from `https://data.gov.uk/dataset/lottery-draws` (Primary) or fallback to `https://raw.githubusercontent.com/datasets/lottery-data/master/uk_lotto.csv` (Mirror). **Output**: Save to `data/raw/lottery_draws.csv`. **Steps**: 1. Verify URL reachability via HEAD request. 2. Download and save. 3. Generate SHA256 checksum and log. 4. Handle missing `total_sales` by logging a warning but retaining the row for frequency analysis.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Draw Uniformity Analysis (Priority: P1) 🎯 MVP

**Goal**: Ingest historical draw data and calculate `draw_uniformity_deviation` (per-draw and rolling) to quantify birthday clustering and consecutive patterns.

**Independent Test**: Can be fully tested by running the ingestion script against a static, known CSV dataset and verifying the calculated `draw_uniformity_deviation` matches a manually computed reference value for that specific draw.

### Implementation for User Story 1

- [ ] T009 [US1] Implement `code/metrics.py` function `calculate_birthday_ratio(draw_numbers)` returning float (0.0 to 1.0)
- [ ] T010 [US1] Implement `code/metrics.py` function `calculate_consecutive_ratio(draw_numbers)` returning float (0.0 to 1.0)
- [ ] T011 [US1] Implement `code/metrics.py` function `calculate_multiples_ratio(draw_numbers)` returning float (0.0 to 1.0)
- [ ] T011a [US1] Implement `code/metrics.py` function `calculate_per_draw_chi_square(draw_numbers)`. **Requirement**: Calculate Chi-Square statistic for the single draw (n=6) against uniform distribution. **Note**: Mark this metric as `legacy` in schema and output due to statistical degeneracy (n=6), but implement to satisfy FR-002 literal text. Output key: `draw_uniformity_deviation_legacy`.
- [ ] T011b [US1] Implement `code/metrics.py` function `calculate_rolling_uniformity_deviation(dataframe, window_size=50)`. **Formula**: 1. Aggregate frequency counts for the 50 draws in the window (total N=300 balls). 2. Calculate Chi-Square goodness-of-fit against a uniform distribution of 300 balls. 3. Assign the resulting statistic to the timestamp of the LAST draw in the window. Output key: `draw_uniformity_deviation_rolling`.
- [ ] T012 [US1] Implement `code/processing.py` to join raw draws with metrics. **Output 1**: `data/processed/per_draw_metrics.json` (contains `draw_uniformity_deviation_legacy` from T011a). **Output 2**: `data/processed/rolling_window_metrics.json` (contains `draw_uniformity_deviation_rolling` from T011b). Flag `is_majority_birthday` if `birthday_cluster_ratio > 0.5` (using entity name `birthday_cluster_ratio` from spec).
- [ ] T013 [US1] Handle missing `total_sales` by logging a warning and excluding from sales-dependent checks while retaining in frequency analysis (Spec Edge Case); ensure `draw_uniformity_deviation` is calculated regardless of sales data presence
- [ ] T014 [US1] Save processed metrics to `data/processed/draw_metrics.json` with schema validation (consolidating legacy and primary metrics)
- [ ] T015 [US1] Unit test `test_metrics.py` for `calculate_birthday_ratio` with known inputs (e.g., [1,2,3,4,5,6] -> 1.0, [32,33,34,35,36,37] -> 0.0)
- [ ] T016 [US1] Unit test `test_metrics.py` for `calculate_rolling_uniformity_deviation` ensuring stability on constant data

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Jackpot Correlation and Anomaly Detection (Priority: P2)

**Goal**: Compute correlation between jackpot magnitude and uniformity deviation, acknowledging data limitations regarding Quick Pick rates.

**Independent Test**: Can be tested by providing a pre-processed dataset with known correlations and verifying the system outputs the correct correlation coefficient and p-value within an acceptable tolerance.

### Implementation for User Story 2

- [ ] T017a [US2] Implement `code/analysis.py` function `compute_correlation_continuous(dataframe, method='spearman')` using `data/processed/per_draw_metrics.json` (from T011a). **Requirement**: Compute correlation between `jackpot_amount` (continuous) and `draw_uniformity_deviation_legacy`. Return coefficient, p-value, and `control_variable_note` (FR-004). **Primary Output**: `data/results/correlation_result.json`.
- [ ] T018 [US2] Implement logic to flag tiers with < 5 draws as "Insufficient Data" and exclude from regression (Spec Edge Case). **Output Format**: Add a top-level key `warnings` in `data/results/correlation_result.json` containing an array of objects with keys `type` (string: "insufficient_data") and `reason` (string).
- [ ] T019 [US2] Implement outlier handling: run analysis with and without extreme jackpots (> 10x global mean of `jackpot_amount`) and report delta. **Output Format**: Add a top-level key `outlier_sensitivity_delta` (float) to `data/results/correlation_result.json`, representing the absolute difference in correlation coefficient between the full dataset and the dataset with jackpots > 10x mean removed.
- [ ] T018b [US2] **Optional Exploratory**: Implement binning by "Small/Medium/Large" tiers. **Constraint**: Do NOT include in `final_report.json`. Save results to `data/results/exploratory_binned_analysis.json` only.
- [ ] T020 [US2] Unit test `test_analysis.py` for correlation computation against a small synthetic dataset with known r-value
- [ ] T021 [US2] Integration test `test_pipeline.py` to verify end-to-end flow from raw CSV to correlation JSON output

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness Validation and Sensitivity Analysis (Priority: P3)

**Goal**: Perform bootstrapping and sensitivity analysis to ensure results are not artifacts of arbitrary thresholds.

**Independent Test**: Can be tested by running the validation script on a small subset of data and verifying that the confidence intervals and sensitivity report are generated within the prescribed time limit and contain no null values.

### Implementation for User Story 3

- [ ] T022 [US3] Implement `code/validation.py` function `bootstrap_correlation(data, iterations=1000)` generating 95% CI
- [ ] T023 [US3] Implement `code/validation.py` function `sweep_birthday_thresholds(data, thresholds)` to evaluate performance across a range of threshold values.
- [ ] T024 [US3] Implement Bonferroni correction logic in `code/validation.py` for 'birthday, consecutive, multiples' patterns (FR-007). **Input**: Collect p-values from the three specific tests (birthday, consecutive, multiples) generated by T010, T011, and T011a logic. **Output**: Adjusted p-values and corrected alpha.
- [ ] T025 [US3] Implement `code/validation.py` function `analyze_time_binned_aggregates(dataframe)` to satisfy Plan's 'time-binned' requirement as a secondary validation
- [ ] T026 [US3] Implement `code/main.py` orchestration to run all analysis steps and aggregate results into `data/results/final_report.json`
- [ ] T027 [US3] Unit test `test_validation.py` for bootstrap CI generation (verify width and centering)
- [ ] T028 [US3] Unit test `test_validation.py` for sensitivity analysis output structure

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T029 [P] Generate `quickstart.md` with instructions to run the Pre-CI data fetch and the main analysis pipeline
- [ ] T030 Code cleanup and refactoring to ensure memory usage stays under 7GB; implement `memory_profiler` checks and chunk data if > 500MB. **Deliverable**: A script `tests/test_memory_limit.py` that runs the full pipeline and asserts max RSS < 7GB.
- [ ] T031 [P] Add unit tests for edge cases: Zero variance jackpot tier, missing sales data, extreme outliers
- [ ] T032 Run `pytest` with coverage and ensure complete branch coverage on core logic
- [ ] T033a [P] Create `data/schemas/final_report.schema.json` defining the exact structure of `final_report.json` (including `correlation_coefficient`, `p_value`, `confidence_interval`, `bonferroni_adjusted_p`, `sensitivity_table`, `is_significant`, `outlier_sensitivity_delta`, `warnings`).
- [ ] T033 [P] Verify `data/results/final_report.json` contains all required fields and validate against `data/schemas/final_report.schema.json` (created in T033a). **Action**: Assert `p_value < 0.05` implies `is_significant` is true.
- [ ] T034 Generate a 'Metric Stability Note' in `final_report.json` flagging if the per-draw `draw_uniformity_deviation` (T011a) shows high variance due to n=6 degeneracy
- [ ] T035 Generate a 'Constitution Compliance Note' in `final_report.json` explicitly stating that Quick Pick control was omitted due to data unavailability (FR-003), as per Plan's proposed amendment, and flagging the governance gap for review

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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **Must complete first** as it produces the `draw_uniformity_deviation` metric required by US2 and US3.
- **User Story 2 (P2)**: Depends on US1 output (processed metrics).
- **User Story 3 (P3)**: Depends on US2 output (correlation results) to perform bootstrapping and sensitivity analysis.

### Within Each User Story

- Models/Constants before Services
- Core logic (metrics, analysis) before orchestration
- Unit tests before integration tests
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel
- Unit tests within a story marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all unit tests for User Story 1 together:
Task: "Unit test test_metrics.py for calculate_birthday_ratio"
Task: "Unit test test_metrics.py for calculate_rolling_uniformity_deviation"

# Launch metric implementation in parallel:
Task: "Implement calculate_birthday_ratio"
Task: "Implement calculate_per_draw_chi_square"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Ingestion + Metrics)
4. **STOP and VALIDATE**: Verify `draw_uniformity_deviation` calculation against a manual reference.
5. Deploy/demo if ready.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Data Integrity**: Ensure all data sources are real and verified. No synthetic data generation for input.
- **Compute Safety**: Ensure rolling window calculations and bootstrapping are optimized to run within 6 hours on 2 CPU cores.
- **Constitution Compliance**: Explicitly handle the missing Quick Pick data as per the Plan's amendment (flag, do not fabricate) and generate the required compliance note (T035).
- **Metric Validity**: Acknowledge the scientific critique of per-draw Chi-Square (T011a) by flagging its instability in the final report (T034), while still implementing the Spec requirement. **Primary Analysis** must use the per-draw metric (T011a) for correlation (T017a) to satisfy FR-002, with rolling window (T011b) as robustness check.