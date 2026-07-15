# Tasks: Evaluating the Sensitivity of Common Statistical Tests to Dataset Size

**Input**: Design documents from `/specs/001-evaluating-the-sensitivity-of-common-sta/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: {{claim:c_95b15b65}} ({{claim:c_ea32db88}}, https://www.wikidata.org/wiki/Q18615098)

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

- [ ] T005 [P] Create `data/simulation_metadata.json` schema for storing seeds, config, and timestamps (Constitution Principle VI, Principle V) <!-- FAILED: unspecified -->
- [X] T006 [P] Implement deterministic random seed manager in `code/simulation/__init__.py` to enforce reproducibility across all modules
- [X] T007 [P] Create base data generator utilities in `code/simulation/data_generator.py` supporting Normal and Multinomial distributions
- [X] T008 [P] Setup CI workflow (`.github/workflows/sim.yml`) with modest CPU and RAM constraints and a 6h timeout
- [X] T009 [P] Implement checksum utility for `data/raw/` public datasets to ensure data hygiene (Constitution Principle III)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Simulation Engine for Type I/II Error Estimation (Priority: P1) 🎯 MVP

**Goal**: Run a simulation that generates synthetic data with known ground truth across sample sizes (n=5 to n=500) to empirically calculate Type I and Type II error rates for t-test, ANOVA, and chi-squared tests with ≥10,000 iterations. [UNRESOLVED-CLAIM: c_8c8bd193 — status=not_enough_info]

**Independent Test**: {{claim:c_46a368b8}}

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for synthetic data generation in `tests/unit/test_data_generator.py` verifying distribution parameters
- [X] T011a [P] [US1] Write unit test `test_chi_squared_fallback_2x2` in `tests/unit/test_chi_squared_fallback.py` verifying Yates/Fisher triggers for 2x2 table with expected count=3
- [X] T011b [P] [US1] Write unit test to verify binomial variance check logic in `tests/unit/test_data_generator.py` using formula: observed_variance <= 1.96 * sqrt(p*(1-p)/N)

### Implementation for User Story 1

- [X] T012b [US1] Refactor `code/simulation/test_runner.py` to accept `alpha` as a dynamic parameter instead of hardcoding 0.05; this enables SC-004 sensitivity analysis (FR-002, SC-004)
- [X] T015a [US1] Implement vectorized numpy operations in `code/simulation/test_runner.py` to handle [deferred] iterations per condition efficiently; verify runtime of the full simulation grid < 6h on CI via benchmark step in `.github/workflows/sim.yml` [UNRESOLVED-CLAIM: c_d8795938 — status=not_enough_info] (FR-001, Constitution VI)
- [X] T012 [US1] Implement `code/simulation/test_runner.py` to execute t-test, ANOVA, and chi-squared on generated data; The system must detect expected cell counts less than 5 and route to fallback logic. [UNRESOLVED-CLAIM: c_f5333042 — status=not_enough_info] (FR-007); MUST flag n < 30 for normality warnings [UNRESOLVED-CLAIM: c_35234d45 — status=not_enough_info]; supports dynamic alpha (FR-002, FR-007)
- [X] T013 [US1] Implement logic in `code/simulation/chi_squared_utils.py` to {{claim:c_61a9fcdd}} (1405.1250, https://arxiv.org/abs/1405.1250) (FR-007, Edge Cases)
- [X] T013b [US1] Implement logic in `code/simulation/test_runner.py` to flag sample sizes n < 30 as "small sample warning" where normality assumptions are severely violated (Edge Cases)
- [X] T014a [US1] Create `code/main.py` skeleton with argument parsing for sample size, effect size, test type, and alpha
- [ ] T014b [US1] Implement parameter loop logic in `code/main.py` to iterate through n=5..500 (step 5), effect sizes, and hypotheses, enforcing a hard constraint of [deferred] iterations per condition (FR-001) <!-- FAILED: unspecified -->
- [ ] T016 [US1] Write output results to `data/simulation/p_values_raw.csv` containing sample size, effect size, test type, raw p-values, and hypothesis state
- [X] T017 [US1] Implement aggregation logic to calculate empirical Type I (p < alpha when null true) and Type II (p > alpha when alt true) error rates per condition (FR-002)
- [ ] T018 [US1] Save aggregated error rates to `data/simulation/error_rates_summary.csv` <!-- FAILED: unspecified -->

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Threshold Identification and Reliability Visualization (Priority: P2)

**Goal**: Visualize the relationship between sample size and error rates to identify the specific sample size threshold where error rates deviate significantly from {{claim:c_96ae5f60}} (Wikipedia: P-value, https://en.wikipedia.org/wiki/P-value) or where power drops below 0.80.

**Independent Test**: The system can be tested by feeding it the output CSV from User Story 1 and generatinga plot where the X-axis is sample size and the Y-axis is error rate, with a horizontal line at 0.05 and a highlighted vertical line indicating the calculated threshold.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for Wilson score interval calculation in `tests/unit/test_threshold_finder.py`

### Implementation for User Story 2

- [X] T020 [US2] Implement `code/analysis/threshold_finder.py` to compute binomial confidence intervals (Wilson score) for all error rates (FR-003); depends on T018
- [X] T021 [US2] Implement logic in `code/analysis/threshold_finder.py` to The system will identify the smallest sample size where the Type I error lower confidence interval bound exceeds 0.05. [UNRESOLVED-CLAIM: c_c3ece5e8 — status=not_enough_info] (FR-004)
- [X] T022 [US2] Implement logic in `code/analysis/threshold_finder.py` to identify the smallest n where power CI remains < 0.80) for 3 consecutive increments (FR-004)
- [X] T023 [US2] Save threshold metrics to `data/simulation/thresholds.json` including test type, effect size, and identified n <!-- FAILED: unspecified -->
- [X] T024 [US2] Implement `code/visualization/plotter.py` to generate line plots with 95% CI bands for sample size vs. error rate (FR-005)
- [X] T025 [US2] Add annotations to plots marking the identified reliability thresholds and nominal alpha/power lines
- [X] T026 [US2] Generate comparative plots for t-test, ANOVA, and chi-squared divergence at low sample sizes (n < 30) [UNRESOLVED-CLAIM: c_9c268ce8 — status=not_enough_info]
- [X] T027 [US2] Save all plots to `data/visualization/` directory with descriptive filenames

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Validation Against Real-World Small-Sample Datasets (Priority: P3)

**Goal**: Validate the simulation findings by applying the identified thresholds to a small number of public small-sample datasets (UCI Breast Cancer, UCI Wine, UCI Adult) to confirm that simulated p-value distributions align with observed behavior.

**Independent Test**: The system can be tested by loading a public dataset with a known small sample size, applying the statistical tests, and verifying that the observed p-value distribution falls within the confidence intervals predicted by the simulation.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [P] [US3] Integration test for dataset download and checksum verification in `tests/integration/test_data_validation.py`

### Implementation for User Story 3

- [X] T029a [US3] Implement `code/analysis/validator.py` to download the {{claim:c_51a94046}} (1711.07831, https://arxiv.org/abs/1711.07831) using `ucimlrepo` with the corresponding dataset identifier. (FR-006)
- [X] T029b [US3] Implement `code/analysis/validator.py` to download the UCI Wine dataset using `ucimlrepo` with the corresponding dataset identifier. (FR-006)
- [X] T029c [US3] Implement `code/analysis/validator.py` to download the {{claim:c_aae0c4fb}} (1810.10076, https://arxiv.org/abs/1810.10076) using `ucimlrepo` with the dataset ID corresponding to the Adult dataset. (FR-006)
- [X] T029d [US3] Implement checksum verification for all downloaded datasets (Breast Cancer, Wine, Adult) in `code/analysis/validator.py` and record checksums in `data/simulation_metadata.json` (Constitution Principle III) <!-- FAILED: unspecified -->
- [X] T030 [US3] Implement data preprocessing in `code/analysis/validator.py` to prepare small-sample datasets for t-test, ANOVA, and chi-squared
- [ ] T031 [US3] Run t-test, ANOVA, and chi-squared on real datasets and save observed p-value distributions to `data/simulation/real_data_pvalues.csv` (FR-006)
- [ ] T032 [US3] Implement bootstrapped power estimation on real datasets, calculate Kolmogorov-Smirnov (KS) distance against simulated predictions, Bootstrapped power estimation on real datasets must verify Kolmogorov-Smirnov distance less than or equal to 0.10. [UNRESOLVED-CLAIM: c_53304eb8 — status=not_enough_info], and save results to `data/simulation/real_data_power.json` (FR-006, SC-003) <!-- FAILED: unspecified -->
- [ ] T034 [US3] Save validation metrics and KS statistics to `data/simulation/validation_metrics.json` <!-- FAILED: unspecified -->
- [X] T033 [US3] Generate validation report in `data/reports/validation_report.md` stating whether simulation held true or deviations were observed (US-3 Scenario 3)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T035 [US1] Implement sensitivity analysis for alpha thresholds across standard significance levels. to observe critical sample size shifts (SC-004); depends on T012b refactored for dynamic alpha
- [ ] T036 [P] Optimize `code/main.py` for memory usage to The simulation must ensure less than 7GB RAM usage during full simulation run. [UNRESOLVED-CLAIM: c_d27d0b77 — status=not_enough_info] <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested -->
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
- Data generation (T016) before aggregation (T017)
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
Task: "Refactor code/simulation/test_runner.py for dynamic alpha"
Task: "Implement code/simulation/test_runner.py with fallback logic"
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
- **Alpha Constraint**: T012b must be completed before T012 to ensure dynamic alpha support for SC-004.
- **Data Flow Constraint**: T016 (output CSV) must complete before T020 (threshold calculation) and T031 (validation) can execute.
- **Real-Data Constraint**: T029a/T029b/T029c must explicitly use `ucimlrepo` and specific numeric IDs (197, 198, 522) to fetch datasets [UNRESOLVED-CLAIM: c_f0a6c398 — status=not_enough_info], not generic "download from UCI" instructions.
- **Note on Spec.md**: This is a plan-root cause. The tasks enforce the [deferred] minimum as per FR-001.
