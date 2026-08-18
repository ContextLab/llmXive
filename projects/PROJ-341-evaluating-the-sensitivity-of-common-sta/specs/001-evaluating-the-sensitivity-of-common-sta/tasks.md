# Tasks: Evaluating the Sensitivity of Common Statistical Tests to Dataset Size

**Input**: Design documents from `/specs/001-evaluating-the-sensitivity-of-common-sta/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: (, https://www.wikidata.org/wiki/Q18615098)

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

- [X] T001a [P] Create project directory structure: `code/`, `data/`, `tests/`, `data/raw/`, `data/simulation/`, `data/visualization/`, `data/reports/`
- [X] T001b [P] Create configuration files: `.gitignore`, `README.md`, `requirements.txt` (with `numpy`, `scipy`, `pandas`, `matplotlib`, `seaborn`, `statsmodels`, `scikit-learn`, `requests`, `ucimlrepo`, `openml`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Create `data/simulation_metadata.json` schema for storing seeds, config, and timestamps (Constitution Principle VI, Principle V). **Verification**: Ensure schema includes keys: `seeds` (dict), `config` (dict), `timestamps` (dict), and verify by writing a dummy JSON file and loading it.
- [X] T006 [P] Implement deterministic random seed manager in `code/simulation/__init__.py` to enforce reproducibility across all modules
- [X] T007 [P] Create base data generator utilities in `code/simulation/data_generator.py` supporting Normal and Multinomial distributions
- [X] T008 [P] Setup CI workflow (`.github/workflows/sim.yml`) with modest CPU and RAM constraints and a 6h timeout
- [X] T009 [P] Implement checksum utility for `data/raw/` public datasets to ensure data hygiene (Constitution Principle III)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Simulation Engine for Type I/II Error Estimation (Priority: P1) 🎯 MVP

**Goal**: Run a simulation that generates synthetic data with known ground truth across sample sizes (n=5 to n=500) to empirically calculate Type I and Type II error rates for t-test, ANOVA, and chi-squared tests with ≥10,000 iterations.

**Independent Test**:

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for synthetic data generation in `tests/unit/test_data_generator.py` verifying distribution parameters
- [X] T011a [P] [US1] Write unit test `test_chi_squared_fallback_2x2` in `tests/unit/test_chi_squared_fallback.py` verifying Yates/Fisher triggers for 2x2 table with expected count=3
- [X] T011b [P] [US1] Write unit test to verify binomial variance check logic in `tests/unit/test_data_generator.py` using formula: observed_variance <= 1.96 * sqrt(p*(1-p)/N)

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/simulation/test_runner.py` to execute t-test, ANOVA, and chi-squared on generated data; The system must detect expected cell counts that are too low and route to fallback logic. (FR-002, FR-007); MUST flag n < 30 for normality warnings; supports hardcoded alpha=0.05 initially.
- [X] T012b [US1] Refactor `code/simulation/test_runner.py` to accept `alpha` as a dynamic parameter instead of hardcoding 0.05; this enables SC-004 sensitivity analysis (FR-002, SC-004). **Verification**: Run a test with alpha=0.01 and alpha=0.10 and verify output changes accordingly.
- [X] T013 [US1] Implement logic in `code/simulation/chi_squared_utils.py` to handle low expected cell counts by applying Yates' continuity correction or Fisher's Exact Test (FR-007, Edge Cases). **Verification**: Ensure output schema includes `method_used` (str) and `log_level` (str), and that the method is logged to stderr and recorded in the output CSV when fallback is triggered. (Reference: FR-007)
- [X] T013b [US1] Implement logic in `code/simulation/test_runner.py` to flag sample sizes n < 30 as "small sample warning" where normality assumptions are severely violated (Edge Cases)
- [X] T014a [US1] Create `code/main.py` skeleton with argument parsing for sample size, effect size, test type, and alpha
- [X] T014b [US1] Implement parameter loop logic in `code/main.py` to iterate through n=5..500 (step 5), effect sizes, and hypotheses, enforcing a hard constraint of [deferred] iterations per condition (FR-001). **Verification**: Run the loop for [deferred] iterations for a single condition and check `data/simulation_metadata.json` for the recorded N value (10000).
- [ ] T015a [US1] **Execute Reduced Grid Verification**: Run a subset simulation (n=5..50, 100 iterations) to verify data flow and output schema before full run. **Verification**: Check `data/simulation_metadata.json` for `total_iterations` >= 100 and `runtime_seconds` < 60.
- [ ] T015b [US1] **Execute Full Simulation Grid**: Run the full simulation (n=5..500, 3 tests, 3 effects, 2 hypotheses, 10k iterations) via `code/main.py` with vectorized batch processing. **Verification**: Check `data/simulation_metadata.json` for `total_iterations` >= 900,000 and `runtime_seconds` < 21600. If timeout is approached, trigger T015c.
- [ ] T015c [US1] **Performance Fallback Strategy**: If Tb exceeds 5 hours, implement a fallback to reduce iteration count (e.g., to a moderate level) or sample the n-grid (e.g., step 10) and re-run. **Verification**: Log the fallback action and updated iteration count in `simulation_metadata.json`.
- [ ] T016 [US1] Write output results to `data/simulation/p_values_raw.csv` containing sample size, effect size, test type, raw p-values, and hypothesis state. **Implementation**: Implement a chunked/vectorized loop in `code/simulation/test_runner.py` to collect all p-values and append to CSV in batches to prevent memory overflow. **Verification**: Verify file exists, contains header row with columns: `sample_size`, `effect_size`, `test_type`, `p_value`, `hypothesis_state`, and that the row count equals (number of conditions * [deferred]).
- [ ] T017 [US1] Implement aggregation logic to calculate empirical Type I (p < alpha when null true) and Type II (p > alpha when alt true) error rates per condition (FR-002)
- [ ] T018 [US1] Save aggregated error rates to `data/simulation/error_rates_summary.csv`. **Implementation**: Implement logic in `code/analysis/aggregator.py` to read `p_values_raw.csv`, group by `sample_size`, `effect_size`, `test_type`, calculate the proportion of rejections (p < alpha), compute Wilson score intervals, and write the summary. **Verification**: Run pytest fixture `test_aggregator_accuracy` which reads a known subset of `p_values_raw.csv` and asserts the calculated `type1_error_rate` matches the expected value within a tolerance.
- [ ] T035 [US1] **Sensitivity Analysis**: Implement sensitivity analysis for alpha thresholds (0.01, 0.05, 0.10) across *all three* test types (t-test, ANOVA, chi-squared) to observe critical sample size shifts (SC-004); depends on T012b refactored for dynamic alpha and T018 for error rate data. **Verification**: Ensure output includes a table of thresholds for alpha=0.01, 0.05, 0.10 for each test type.
- [ ] T047a [P] [US1] Unit test for streaming/batch processing logic in `tests/unit/test_streaming.py` using mocked data to verify memory usage remains < 7GB during iteration (FR-001, T047). **Verification**: Assert `peak_ram_mb < 7168` in mock environment.
- [ ] T047b [US1] Integration test for streaming/batch processing in `tests/integration/test_streaming_integration.py` using a reduced grid (n=5..50) to verify full pipeline memory constraints (FR-001, T047). **Verification**: Assert `peak_ram_mb < 7168` and `total_runtime` within limits for reduced grid.

**Checkpoint**: User Story 1 is functional and verified only after T015b, T016, T018, and T035 are marked complete.

---

## Phase 4: User Story 2 - Threshold Identification and Reliability Visualization (Priority: P2)

**Goal**: Visualize the relationship between sample size and error rates to identify the specific sample size threshold where error rates deviate significantly from the nominal alpha level (0.05) or where power drops below an acceptable level (e.g., the conventional threshold for statistical power).

**Independent Test**: The system can be tested by feeding it the output CSV from User Story 1 and generating a plot where the X-axis is sample size and the Y-axis is error rate, with a horizontal line at 0.05 (Wikipedia: O'Brien–Fleming boundary, https://en.wikipedia.org/wiki/O'Brien–Fleming_boundary) (for Type I) or 0.20 (for Type II), and a highlighted vertical line indicating the calculated threshold where the confidence interval crosses the nominal limit.

### Tests for User Story 2 (OPTIONAL- only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for Wilson score interval calculation in `tests/unit/test_threshold_finder.py`

### Implementation for User Story 2

- [ ] T020 [US2] Implement `code/analysis/threshold_finder.py` to compute binomial confidence intervals (Wilson score) for all error rates (FR-003); depends on T018
- [ ] T021 [US2] Implement logic in `code/analysis/threshold_finder.py` to identify the smallest sample size where the Type I error lower confidence interval bound exceeds the nominal significance threshold (FR-004)
- [ ] T022 [US2] Implement logic in `code/analysis/threshold_finder.py` to identify the smallest n where power CI remains < 0.80 for 3 consecutive increments (FR-004)
- [ ] T023 [US2] Save threshold metrics to `data/simulation/thresholds.json` including test type, effect size, and identified n. **Verification**: Verify JSON contains keys: `test_type`, `effect_size`, `n_threshold`, `ci_lower`, `ci_upper`.
- [ ] T024 [US2] Implement `code/visualization/plotter.py` to generate line plots with confidence interval bands for sample size vs. error rate (FR-005)
- [ ] T025 [US2] Add annotations to plots marking the identified reliability thresholds and nominal alpha/power lines
- [ ] T026 [US2] Generate comparative plots for t-test, ANOVA, and chi-squared divergence at low sample sizes (n < 30)
- [ ] T027 [US2] Save all plots to `data/visualization/` directory with descriptive filenames

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Validation Against Real-World Small-Sample Datasets (Priority: P3)

**Goal**: Validate the simulation findings by applying the identified thresholds to 2-3 public small-sample datasets (UCI Breast Cancer, UCI Wine, OpenML Adult) to confirm that simulated p-value distributions and bootstrapped power estimates align with observed behavior in real data.

**Independent Test**: The system can be tested by loading a public dataset with a known small sample size, applying the statistical tests, and verifying that the observed p-value distribution or bootstrapped power estimates fall within the confidence intervals predicted by the simulation for that sample size.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [P] [US3] Integration test for dataset download and checksum verification in `tests/integration/test_data_validation.py`

### Implementation for User Story 3

- [X] T029a [US3] Implement `code/analysis/validator.py` to download the UCI Breast Cancer (Wisconsin Diagnostic) dataset using `ucimlrepo` with dataset ID 197 (FR-006). **Verification**: Verify file exists in `data/raw/` and checksum matches the recorded value.
- [X] T029b [US3] Implement `code/analysis/validator.py` to download the UCI Wine dataset using `ucimlrepo` with dataset ID 198 (FR-006). **Verification**: Verify file exists in `data/raw/` and checksum matches the recorded value.
- [X] T029c [US3] Implement `code/analysis/validator.py` to download the OpenML Adult dataset using `ucimlrepo` with dataset ID 522 (FR-006). **Verification**: Verify file exists in `data/raw/` and checksum matches the recorded value.
- [X] T029d [US3] Implement checksum verification for all downloaded datasets (Breast Cancer, Wine, Adult) in `code/analysis/validator.py` and record checksums in `data/simulation_metadata.json` (Constitution Principle III). **Verification**: Verify checksums in metadata match the downloaded files.
- [X] T030 [US3] Implement data preprocessing in `code/analysis/validator.py` to prepare small-sample datasets for t-test, ANOVA, and chi-squared
- [ ] T031 [US3] Run t-test, ANOVA, and chi-squared on real datasets and save observed p-value distributions to `data/simulation/real_data_pvalues.csv` (FR-006). **Implementation**: Implement logic in `code/analysis/validator.py` to apply the same statistical tests used in the simulation to the real data subsets and record p-values. **Verification**: Verify file exists and contains columns: `dataset_id`, `test_type`, `p_value`, and that `dataset_id` contains specific IDs and `p_value` contains valid floats.
- [ ] T032 [US3] Implement bootstrapped power estimation on real datasets, calculate Kolmogorov-Smirnov (KS) distance against simulated predictions, and save results to `data/simulation/real_data_power.json` (FR-006, SC-003). **Implementation**: For the Adult dataset (no known ground truth), derive a 'proxy ground truth' by bootstrapping the observed effect size from the real data to construct a simulated prediction curve. Compare observed p-values against this bootstrapped prediction using KS distance. **Verification**: Verify JSON contains keys: `dataset_id`, `ks_distance`, `power_estimate`, and that `ks_distance <= 0.10`. Also verify the KS calculation function returns a float within the valid probability range and matches a pre-calculated value for a dummy dataset.
- [ ] T033a [US3] Implement Pass/Fail decision logic for SC-003: Generate a validation conclusion stating whether KS <= 0.10 for each dataset (SC-003). **Verification**: Verify output includes explicit 'PASS' or 'FAIL' status for each dataset based on the KS threshold.
- [ ] T034 [US3] Save validation metrics and KS statistics to `data/simulation/validation_metrics.json`. **Implementation**: Aggregate results from `real_data_power.json` and T033a conclusion. **Verification**: Verify JSON contains keys: `total_datasets`, `passed_validation_count`, `avg_ks_distance`.
- [X] T033 [US3] Generate validation report in `data/reports/validation_report.md` stating whether simulation held true or deviations were observed (US-3 Scenario 3)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T037 [P] Add comprehensive logging to all simulation steps for debugging reproducibility issues
- [X] T038 [P] Update `quickstart.md` with instructions to run the full simulation and generate the validation report
- [X] T039 [P] Run `pytest` suite to ensure all unit and integration tests pass

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
- **User Story 2 (P2)**: Depends on US1 output (`error_rates_summary.csv`) to generate plots and thresholds
- **User Story 3 (P3)**: Depends on US2 output (`thresholds.json`) and US1 output (`p_values_raw.csv`) for comparison

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data generation (T015, T016) before aggregation (T017, T018)
- Threshold calculation (T020) before visualization (T024)
- Dataset download (T029a/T029b/T029c) before validation (T031)

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US2 and US3 can start in parallel if US1 data generation is decoupled (but US2/3 logic depends on US1 results)
- All unit tests for a user story marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for synthetic data generation in tests/unit/test_data_generator.py"
Task: "Unit test for chi-squared fallback logic in tests/unit/test_chi_squared_fallback.py"
Task: "Write unit test to verify binomial variance check logic in tests/unit/test_data_generator.py"

# Launch all models for User Story 1 together:
Task: "Implement basic code/simulation/test_runner.py"
Task: "Refactor code/simulation/test_runner.py for dynamic alpha"
Task: "Create code/main.py skeleton"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Core Simulation)
4. **STOP and VALIDATE**: Test User Story 1 independently by running a small subset (e.g., n=5, 100 iterations) to verify output format and reproducibility.
5. Deploy/demo if ready.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently (visualize US1 data) → Deploy/Demo
4. Add User Story 3 → Test independently (validate US1/US2) → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Simulation Engine)
 - Developer B: User Story 2 (Analysis/Visualization) - *Note: Can start coding logic, but needs US1 data for final run*
 - Developer C: User Story 3 (Validation) - *Note: Can start dataset download logic, but needs US1 data for final comparison*
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
- **Compute Constraint**: Ensure all simulation tasks (T012, T014, T015) use vectorization or batch processing to stay within 6h/2CPU limits. Do not use 8-bit quantization or GPU.
- **Alpha Constraint**: T012b must be completed before T012 to ensure dynamic alpha support for SC-004. (Note: T012 is basic impl, T012b adds alpha).
- **Data Flow Constraint**: T015 (Execution) and T016 (output CSV) must complete before T017, T018, T020, and T031 can execute.
- **Real-Data Constraint**: T029a/T029b/T029c must explicitly use `ucimlrepo` and specific numeric IDs (197, 198, 522) to fetch datasets, not generic "download from UCI" instructions.
- **Note on Spec.md**: This is a plan-root cause. The tasks enforce the [deferred] minimum as per FR-001.