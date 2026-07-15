# Tasks: Assessing the Sensitivity of Common Statistical Tests to Dataset Size

**Input**: Design documents from `/specs/001-assess-test-sensitivity/`
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

- [X] T001a Create `code/` directory
- [X] T001b Create `data/raw/` directory
- [X] T001c Create `data/processed/` directory
- [X] T002 Initialize Python 3.11 project with dependencies (`numpy`, `scipy`, `pandas`, `matplotlib`, `seaborn`, `scikit-learn`, `pytest`) in `requirements.txt`
- [X] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/config.py` to define simulation parameters (sample sizes n=10..1000, distributions, alpha=0.05, effect sizes)
- [X] T005 [P] Implement `code/__init__.py` and basic logging infrastructure
- [X] T006 Create `data/raw/` and `data/processed/` directories with `.gitkeep`
- [X] T007 Setup `tests/unit/` and `tests/contract/` directory structure
- [X] T008d [P] [Foundational] Generate `quickstart.md` with setup and run instructions. **Deliverable**: The file MUST include sections: 'Environment Setup', 'Data Generation', 'Simulation Execution', 'Visualization', and 'Interpretation'. It MUST include specific code snippets for `python code/main.py` and define required environment variables.
- [ ] T035 [P] [Foundational] Validate `quickstart.md` by running the documented commands and verifying all steps complete successfully. **Dependency**: T008d must be complete.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Controlled Synthetic Datasets (Priority: P1) 🎯 MVP

**Goal**: Generate synthetic datasets across a range of sample sizes (starting from small) and distributions (normal, uniform, log-normal) with known ground truth for null and alternative hypotheses.

**Independent Test**: Verify generated data statistics (mean, variance, shape) match theoretical parameters within tolerance (±1e-6) before any testing occurs.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T008a [P] [US1] Define and write test cases for normal distribution generation in `tests/unit/test_data_generator.py`
- [X] T008b [P] [US1] Define and write test cases for log-normal skewness validation in `tests/unit/test_data_generator.py`
- [X] T008c [P] [US1] Define and write test cases for log-normal effect size validation in `tests/unit/test_data_generator.py`
- [X] T008d [P] [US1] Define and write test cases for uniform distribution sample size accuracy in `tests/unit/test_data_generator.py`

### Implementation for User Story 1

- [X] T011 [US1] Implement `code/data_generator.py` with functions to generate Normal, Uniform, and Log-Normal distributions for both Null (effect=0) and Alternative (effect=0.5) hypotheses
- [X] T012 [US1] Add logic in `code/data_generator.py` to handle edge cases: ensure log-normal skew is finite and prevent numerical overflow
- [X] T013 [US1] Implement validation routine in `code/data_generator.py` that compares generated sample statistics to theoretical parameters and raises errors on mismatch
- [X] T014 [US1] Create a script `code/run_data_gen.py` to generate and save a small sample dataset to `data/raw/sample_validation.csv` for manual verification. **Schema**: The CSV MUST include columns: `sample_size`, `distribution_type`, `effect_size`, `group_mean_1`, `group_mean_2`, `mean_diff`, `variance`, `skewness`, `checksum`. **Validation**: `effect_size` must match input (0.0 or 0.5); `mean_diff` must be within 1e-6 of theoretical value; `checksum` must be MD5 of the row data.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute Monte Carlo Simulations (Priority: P2)

**Goal**: Perform adaptive Monte Carlo replicates (min 1000, extend until 95% CI width ≤ 0.01) for t-test, ANOVA, and Chi-squared tests, switching to Fisher's Exact for small counts.

**Independent Test**: Run a small subset (100 reps) of a known scenario (t-test, normal, n=50, null true) and verify observed Type I error rate is close to 0.05.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T015 [P] [US2] Unit test for Type I error classification logic in `tests/unit/test_simulation.py`
- [X] T016 [P] [US2] Unit test for Fisher's Exact switch trigger (expected cell < 5) in `tests/unit/test_simulation.py`
- [X] T017 [P] [US2] Integration test for adaptive replication loop termination in `tests/integration/test_simulation_loop.py`

### Implementation for User Story 2

- [X] T018 [US2] Implement `code/simulation_engine.py` with the core Monte Carlo loop: data generation (calling T011), test execution (calling T019), and result classification. **Integration**: Must integrate Fisher's Exact switch (T019) and Adaptive Loop (T020) logic. The loop must call the data generator, execute the appropriate test, and pass results to the adaptive logic.
- [X] T019 [US2] Implement test execution logic in `code/simulation_engine.py`:
 - T-test (scipy.stats.ttest_ind)
 - ANOVA (scipy.stats.f_oneway)
 - Chi-squared (scipy.stats.chi2_contingency)
 - Fisher's Exact (scipy.stats.fisher_exact) triggered when expected cell counts < 5
- [X] T020 [US2] Implement adaptive replication logic in `code/simulation_engine.py`: start with 1000 replicates, calculate **Clopper-Pearson exact intervals** (internal convergence check only) to monitor CI width in real-time, and implement the **adaptive control loop** that triggers additional replicates until width ≤ 0.01 or **maximum cap of [deferred] total replicates** reached. **Verification**: Ensure final reported CIs (T026) use Bootstrap Resampling per FR-004; Clopper-Pearson is used here only for efficient internal convergence checking of binary outcomes.
- [X] T021 [US2] Implement Type I (reject true null) and Type II (fail to reject false null) error counting logic with fixed alpha=0.05. **Logic**: This task is an **in-memory callback** integrated directly into the simulation loop of T018. It processes the live stream of p-values as they are generated, classifying them immediately. **Output**: Write aggregated counts to `data/processed/error_counts.csv` at the end of each configuration run.
- [X] T021b [US2] Implement logic in `code/simulation_engine.py` to **store raw p-values** for every replicate in a structured format. **Output**: Write to `data/processed/raw_pvalues.csv`. **Schema**: Columns `sample_size`, `distribution_type`, `test_type`, `p_value`, `hypothesis_type`. **Constraint**: Store raw p-values exactly as generated; do NOT apply any clipping or transformation.
- [X] T022 [US2] Create `code/run_simulation.py` to orchestrate the full batch: Multiple sample sizes × 3 distributions × 3 tests, saving intermediate results to `data/processed/`. **Dependency**: Must consume the output of T021b (`data/processed/raw_pvalues.csv`) and T021 (`data/processed/error_counts.csv`).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Aggregate Results and Visualize (Priority: P3)

**Goal**: Aggregate error rates, compute bootstrap CIs, fit regression models, and generate publication-ready CSV and plots.

**Independent Test**: Verify CSV output contains all required columns and plots correctly map sample size to error rate with confidence intervals.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US3] Unit test for CSV export format and column presence in `tests/unit/test_analyzer.py`
- [X] T024 [P] [US3] Unit test for bootstrap CI calculation in `tests/unit/test_analyzer.py`
- [X] T025 [P] [US3] Unit test for regression model McFadden R² calculation in `tests/unit/test_analyzer.py`

### Implementation for User Story 3

- [X] T026 [US3] Implement `code/analyzer.py` to load simulation results, aggregate by (n, distribution, test), and compute 95% **Bootstrap Resampling** confidence intervals for final reporting (per FR-004).
- [X] T026b [US3] Implement **stability measurement** in `code/analyzer.py`: Calculate the Type I error rate **for each sample size** (not a single aggregate variance). Perform a **trend analysis** (regression of error rate vs. sample size) to verify SC-002. **Output**: Write results to `data/processed/stability_trend.csv` and generate a plot of error rate vs. sample size.
- [X] T027 [US3] Implement regression analysis in `code/analyzer.py`: Fit GLM/Binomial regression to predict the magnitude of deviation from the nominal significance threshold using log(sample size), distribution, and test type; report beta and p-values.
- [ ] T027b [US3] Implement regression analysis in `code/analyzer.py` to model the **log-transformed p-value distribution** (consuming raw p-values stored by T021b). **Input**: Load `data/processed/raw_pvalues.csv`. **Logic**: Apply a numerical stability epsilon of `1e-300` to p-values of exactly 0 or 1 *only during the log-transform calculation* (i.e., `log(p + 1e-300)`). **Do not modify the stored raw data**. Fit the model and report regression coefficients (beta) and p-values as required by FR-006. **Dependency**: T021b must be complete.
- [X] T028 [US3] Implement `code/visualizer.py` to generate publication-ready plots (PNG/SVG): Error Rate vs. Sample Size curves with CI bands, distinguishing distributions
- [X] T029 [US3] Create `code/export_results.py` to write final aggregated data to `data/processed/error_rates.csv` and save plots to `data/processed/plots/`
- [X] T030 [US3] Create `code/main.py` as the single entry point to orchestrate the full pipeline: Setup -> US1 (Data Gen) -> US2 (Simulation) -> US3 (Analysis/Export)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031 [P] Documentation updates in `README.md` explaining how to run the simulation and interpret results
- [X] T032a Refactor `code/simulation_engine.py` to separate data generation logic from test execution logic
- [X] T032b Refactor `code/analyzer.py` to separate aggregation logic from visualization logic
- [X] T033 [P] Performance verification: Create `code/benchmark.py` to measure the execution time of the full simulation suite. **Deliverable**: The script MUST write results to `logs/benchmark.log`. **Verification**: Run the benchmark and confirm the total time is < 6 hours.
- [X] T034 [P] Add final integration tests in `tests/integration/test_full_pipeline.py`

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data generation logic (T011)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 simulation results and raw p-value storage (T021b)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Define and write test cases for normal distribution generation in tests/unit/test_data_generator.py"
Task: "Define and write test cases for log-normal skewness validation in tests/unit/test_data_generator.py"
Task: "Define and write test cases for log-normal effect size validation in tests/unit/test_data_generator.py"
Task: "Define and write test cases for uniform distribution sample size accuracy in tests/unit/test_data_generator.py"

# Launch implementation for User Story 1:
Task: "Implement code/data_generator.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify ground truth)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Simulation core)
4. Add User Story 3 → Test independently → Deploy/Demo (Final results)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Gen)
 - Developer B: User Story 2 (Simulation)
 - Developer C: User Story 3 (Analysis)
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
- **Critical Constraint**: All simulations must run on CPU-only (limited cores, constrained RAM). Do not use GPU or heavy model loading. Use `scipy` and `numpy` only.
- **Data Integrity**: Do not fabricate data. All inputs must be generated via the `data_generator` with known ground truth.
- **CI Method**: The adaptive replication loop (T020) uses **Clopper-Pearson exact intervals** for internal convergence checking (optimization for binary outcomes). Final reported CIs (T026) MUST use **Bootstrap Resampling** as per FR-004 for visualization and reporting.
- **Regression Data**: Raw p-values MUST be stored by T021b (unmodified) and consumed by T027b. T027b applies a numerical stability epsilon (`1e-300`) *only* during log-transform calculation.
- **Execution Order**: Phase 4 tasks must be executed in the order: T018 -> T019 -> T020 -> T021b -> T021 -> T022. T021 is an in-memory callback integrated into T018, but T021b (file writer) must complete before T022 (orchestrator) consumes the file.