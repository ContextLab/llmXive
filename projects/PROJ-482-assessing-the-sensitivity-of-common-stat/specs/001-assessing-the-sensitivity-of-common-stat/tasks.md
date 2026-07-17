# Tasks: Assessing the Sensitivity of Common Statistical Tests to Dataset Size

**Input**: Design documents from `/specs/001-assess-test-sensitivity/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. [UNRESOLVED-CLAIM: c_018388b7 — status=not_enough_info] Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story. [UNRESOLVED-CLAIM: c_c6628f3b — status=not_enough_info]

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

- [X] T004 Create `code/config.py` to define simulation parameters (sample sizes n=10..1000, distributions, alpha=0.05, effect sizes, `MAX_REPLICATES=10000`, `LOG_EPSILON=1e-15`)
- [X] T005 [P] Implement `code/__init__.py` and basic logging infrastructure
- [X] T006 Create `data/raw/` and `data/processed/` directories with `.gitkeep`
- [X] T007 Setup `tests/unit/` and `tests/contract/` directory structure
- [X] T008d-1 [P] [Foundational] Create `quickstart.md` file structure with required section headers: 'Environment Setup', 'Data Generation', 'Simulation Execution', 'Visualization', and 'Interpretation'. **Deliverable**: The file MUST exist with these headers but no content yet.
- [X] T008d-2 [P] [Foundational] Write content for `quickstart.md` sections: 'Environment Setup', 'Data Generation', 'Visualization', and 'Interpretation'. **Deliverable**: The file MUST include specific instructions for setup and data generation, excluding the 'Simulation Execution' code snippets for now. [UNRESOLVED-CLAIM: c_9e49733c — status=not_enough_info]
- [X] T008d-3 [P] [Foundational] Insert code snippets for `python code/main.py` into `quickstart.md` 'Simulation Execution' section as **placeholders** with explicit comments: `# TODO: Replace with actual main.py implementation (T030)`. **Constraint**: Do not write a functional script; write a placeholder that documents the intended command structure.
- [X] T008d-4 [P] [Foundational] Finalize `quickstart.md` by reviewing all sections and ensuring consistency. **Deliverable**: The file MUST be complete and ready for validation.

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
- [X] T014 [US1] Create a script `code/run_data_gen.py` to generate and save a small sample dataset to `data/raw/sample_validation.csv` for manual verification. **Schema**: The CSV MUST include columns: `sample_size`, `distribution_type`, `effect_size`, `group_mean_1`, `group_mean_2`, `mean_diff`, `variance`, `skewness`, `checksum`. [UNRESOLVED-CLAIM: c_442444d9 — status=not_enough_info] **Validation**: `effect_size` must match input (0.0 or 0.5); `mean_diff` must be within 1e-6 of theoretical value; `checksum` must be MD5 (Wikidata Q185235, https://www.wikidata.org/wiki/Q185235) of the row data.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute Monte Carlo Simulations (Priority: P2)

**Goal**: Perform adaptive Monte Carlo replicates (min 1000, extend until 95% CI width ≤ 0.01) for t-test, ANOVA, and Chi-squared tests, switching to Fisher's Exact for small counts.

**Independent Test**: Run a small subset of a known scenario (t-test, normal, n=50, null true) and verify observed Type I error rate is close to the nominal significance level.

### Validation Gate (Blocking)

- [ ] T017b [P] [US1] **Run Ground-Truth Validation Gate**: Execute the validation routine from T013 on a fresh batch of generated data before starting the Monte Carlo loop. **Constraint**: This task MUST pass (exit code 0) before T018 can begin. **Deliverable**: A log entry confirming ground-truth parameters were verified for the current configuration batch. **Dependency**: T013 must be complete.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T015 [P] [US2] Unit test for Type I error classification logic in `tests/unit/test_simulation.py`
- [X] T016 [P] [US2] Unit test for Fisher's Exact switch trigger (expected cell < 5 (Wikipedia: Fisher's exact test, https://en.wikipedia.org/wiki/Fisher's_exact_test)) in `tests/unit/test_simulation.py`
- [X] T017 [P] [US2] Integration test for adaptive replication loop termination in `tests/integration/test_simulation_loop.py`

### Implementation for User Story 2

- [X] T018 [US2] Implement `code/simulation_engine.py` with the core Monte Carlo loop: data generation (calling T011), test execution (calling T019), and result classification. **Integration**: Must integrate Fisher's Exact switch (T019) and Adaptive Loop (T020) logic. The loop must call the data generator, execute the appropriate test, and pass results to the adaptive logic.
- [X] T019 [US2] Implement test execution logic in `code/simulation_engine.py`:
 - T-test (scipy.stats.ttest_ind)
 - ANOVA (scipy.stats.f_oneway)
 - Chi-squared (scipy.stats.chi2_contingency)
 - Fisher's Exact (scipy.stats.fisher_exact) triggered when expected cell counts < 5
- [ ] T020-1 [US2] Implement Bootstrap Resampling confidence interval calculation in `code/simulation_engine.py`. **Input**: A list of binary outcomes (1=error, 0=correct). **Output**:A tuple (lower_bound, upper_bound) for the 95% CI. **Constraint**: Use a sufficient number of resamples.
- [ ] T020-2 [US2] Implement adaptive control loop in `code/simulation_engine.py`: start with 1000 (hep-lat/0202016, https://arxiv.org/abs/hep-lat/0202016) replicates, calculate 95% CI width using T020-1 (Bootstrap), and trigger additional replicates until width ≤ 0.01 OR `config.MAX_REPLICATES` (10000) is reached. **Fallback**: If `config.MAX_REPLICATES` is reached before convergence, terminate the loop and log a warning. **Dependency**: T020-1 must be complete.
- [ ] T021b [US2] Implement logic in `code/simulation_engine.py` to **stream and store raw p-values** for every replicate in a structured format. **Input**: Stream p-values from T018/T020. **Output**: Write to `data/processed/raw_pvalues.csv` in real-time (or batched at the end of each configuration). **Schema**: Columns `sample_size`, `distribution_type`, `test_type`, `p_value`, `hypothesis_type`. **Constraint**: Store raw p-values exactly as generated; do NOT apply any clipping or transformation. **Dependency**: T018/T020 must be integrated.
- [ ] T021 [US2] Implement Type I (reject true null) and Type II (fail to reject false null) error counting logic. **Input**: Read `data/processed/raw_pvalues.csv` generated by T021b. **Logic**: Classify each row based on `p_value < config.ALPHA` and `hypothesis_type`. **Output**: Write aggregated counts to `data/processed/error_counts.csv` at the end of each configuration run. **Dependency**: T021b must be complete.
- [ ] T021c [US2] Implement explicit validation routine in `code/simulation_engine.py` to compare observed Type I error rates against the theoretical nominal alpha level for the null hypothesis scenarios. **Deliverable**: A report written to `data/processed/validation_report.csv` containing the observed vs. theoretical error rates and the difference. **Dependency**: T021 must be complete.
- [ ] T022 [US2] Create `code/run_simulation.py` to orchestrate the full batch: Multiple sample sizes × distributions × 3 tests, saving intermediate results to `data/processed/`. **Dependency**: Must consume the output of T021b (`data/processed/raw_pvalues.csv`) and T021 (`data/processed/error_counts.csv`) and T021c (`data/processed/validation_report.csv`). **Execution Order**: T018 -> T019 -> T020-1 -> T020-2 -> T021b -> T021 -> T021c -> T022. <!-- FAILED: unspecified -->

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
- [ ] T026b [US3] Implement **stability measurement** in `code/analyzer.py`: Calculate the Type I error rate **for each sample size** (not a single aggregate variance). Perform a **trend analysis** (regression of error rate vs. sample size) to verify SC-002. **Output**: Write results to `data/processed/stability_trend.csv` and generate a plot of error rate vs. sample size.
- [X] T027 [US3] Implement regression analysis in `code/analyzer.py`: Fit GLM/Binomial regression to predict the magnitude of deviation from the nominal significance threshold using log(sample size), distribution, and test type; report beta and p-values. **Target Variable**: Explicitly model the magnitude of deviation |p - α|. **Deliverable**: A report containing regression coefficients (beta) and p-values for all predictors.
- [ ] T027b [US3] Implement data preparation function in `code/analyzer.py` to apply a numerical stability epsilon of `config.LOG_EPSILON` (1e-15) to p-values of exactly 0 or 1 *only during the log-transform calculation* (i.e., `log(p + config.LOG_EPSILON)`). **Constraint**: Do not modify the stored raw data. **Documentation**: Explicitly state in the code comments that this is a deviation from the raw data required by FR-006 to handle numerical stability, and that the resulting regression models the 'modified distribution'. **Input**: Load `data/processed/raw_pvalues.csv`. **Dependency**: T021b must be complete.
- [ ] T027c-1 [US3] **Align Theoretical Power Parameters**: Retrieve ground-truth parameters (effect size, distribution type) from `config.py` and `data_generator.py` to ensure the theoretical power curve calculation uses the exact same assumptions as the simulation. **Deliverable**: A configuration object or dictionary mapping simulation parameters to theoretical calculation parameters.
- [ ] T027c-2 [US3] **Calculate Theoretical Power Curve**: Implement the calculation of the theoretical power curve based on the aligned parameters from T027c-1 (using `scipy.stats` or `statsmodels` power functions) and compute the mean absolute error (MAE) between the observed power curve and the theoretical power curve. **Deliverable**: A report containing the MAE metric and a plot comparing observed vs. theoretical power curves. **Dependency**: T027c-1 must be complete.
- [ ] T028 [US3] Implement `code/visualizer.py` to generate publication-ready plots (PNG/SVG): Error Rate vs. Sample Size curves with CI bands, distinguishing distributions
- [ ] T029 [US3] Create `code/export_results.py` to write final aggregated data to `data/processed/error_rates.csv` and save plots to `data/processed/plots/`
- [ ] T030 [US3] Create `code/main.py` as the single entry point to orchestrate the full pipeline: Setup -> US1 (Data Gen) -> US2 (Simulation) -> US3 (Analysis/Export)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031 [P] Documentation updates in `README.md` explaining how to run the simulation and interpret results
- [X] T032a Refactor `code/simulation_engine.py` to separate data generation logic from test execution logic
- [X] T032b Refactor `code/analyzer.py` to separate aggregation logic from visualization logic
- [ ] T033 [P] Performance verification: Create `code/benchmark.py` to measure the execution time of the full simulation suite. **Deliverable**: The script MUST write results to `logs/benchmark.log`. **Schema**: The log MUST contain a JSON structure with a key `total_runtime_seconds` and the value in seconds. [UNRESOLVED-CLAIM: c_c8b021a2 — status=not_enough_info] **Verification**: Run the benchmark and confirm the total time is < 6 hours.
- [X] T034 [P] Add final integration tests in `tests/integration/test_full_pipeline.py`
- [ ] T036 [P] [Foundational] Implement a `code/checkpoint_manager.py` to save partial results after every periodic interval of replicates per configuration. **Rationale**: Mitigates the risk of losing progress on the 6-hour runner if the process is killed mid-batch. **Output**: Save intermediate state to `data/processed/checkpoints/` and implement a resume flag in `main.py`. **Note**: This is optional scope as per the spec's assumptions, but included for robustness.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data generation logic (T011) and T017b (Ground-Truth Validation)
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
- **CI Method**: The adaptive replication loop (T020) uses **Bootstrap Resampling** for both internal convergence checking and final reporting, as per FR-004. T020-1 implements the calculation; T020-2 uses it for the stop condition.
- **Regression Data**: Raw p-values MUST be stored by T021b (unmodified) and consumed by T027b. T027b applies a numerical stability epsilon (`config.LOG_EPSILON`) *only* during log-transform calculation, explicitly documenting this as a deviation from raw data for numerical stability.
- **Execution Order**: Phase 4 tasks must be executed in the order: T018 -> T019 -> T020-1 -> T020-2 -> T021b -> T021 -> T021c -> T022. T017b (Ground-Truth Validation) must run before T018. T021 reads T021b's file (changed from 'in-memory callback').
- **Robustness**: T036 adds checkpointing to prevent total data loss on long-running simulations if the runner times out. Note: This is optional scope as per the spec's assumptions.
- **Theoretical Power**: T027c-1 explicitly aligns parameters with ground-truth definitions. T027c-2 calculates the theoretical power curve and MAE to satisfy SC-004.
- **Validation**: T021c explicitly validates observed Type I error rates against theoretical alpha to satisfy SC-001. T017b ensures ground-truth validation is a blocking gate.
- **Logging**: T033 mandates specific log artifacts (`logs/benchmark.log` with JSON structure) to ensure executability.
- **Task Granularity**: T020, T027b, T027c are atomized into sub-tasks for independent testing and implementation.
- **Parallel Safety**: T036 is moved to Phase 6 and marked [Foundational] to run before simulation.
- **Convergence**: T020-2 ensures the final convergence decision uses Bootstrap Resampling, aligning with FR-004.
- **Data Transformation**: T027b explicitly documents the epsilon transformation as a deviation from raw data for numerical stability, referencing `config.LOG_EPSILON`. [UNRESOLVED-CLAIM: c_0a83a2cc — status=not_enough_info]
- **Scope Creep**: T036 is noted as optional scope but included for robustness.
- **Removed Tasks**: T035, T035-1 (mock runner) removed as scope creep. T020-1, T020-4 merged into T020-2. T020-3 merged into T020-2.