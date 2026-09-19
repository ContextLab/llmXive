---
description: "Task list template for feature implementation"
---

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

- [X] T004 Create `code/config.py` to define simulation parameters (sample sizes n=10..1000, distributions, alpha=0.05, effect sizes, `MAX_REPLICATES=10000`, `LOG_EPSILON=1e-15`)
- [X] T005 [P] Implement `code/__init__.py` and basic logging infrastructure
- [X] T006 Create `data/raw/` and `data/processed/` directories with `.gitkeep`
- [X] T007 Setup `tests/unit/` and `tests/contract/` directory structure
- [X] T011-Interface [P] [Foundational] **Define Interface for Data Generator**: Create function signatures and docstrings for `code/data_generator.py` (e.g., `generate_data(dist, n, effect_size) -> DataFrame`). **Deliverable**: A Python file with stubs and type hints. **Constraint**: This MUST be completed before T008a-d (Tests) to ensure tests are written against a defined interface.
- [X] T020-2b [P] [Foundational] **Define Interface for Adaptive Logic**: Create function signatures for the adaptive replication logic (e.g., `should_continue_replicates(ci_width, current_count) -> bool`). **Deliverable**: A Python file with stubs. **Constraint**: This MUST be completed before T018 (Loop Implementation) to ensure the loop calls a defined interface.
- [X] T021b-0 [P] [Foundational] **Define Schema and Locking Strategy**: Define the CSV schema for `data/processed/raw_pvalues.csv` and implement a file locking strategy using `fcntl` for Linux systems. **Deliverable**: A schema definition in `code/config.py` and a locking utility in `code/utils/file_lock.py`. **Constraint**: This task MUST be completed before T018 (Simulation Engine) to ensure the engine writes the correct format. **Dependency**: T021b-0a. **Instruction**: Ensure `code/utils/` exists (see T021b-0a) before creating `file_lock.py`.
- [X] T021b-0a [P] [Foundational] **Create Utility Directory and Stub**: Create the `code/utils/` directory and the `code/utils/file_lock.py` stub file. **Deliverable**: The directory and file MUST exist. **Constraint**: This task ensures the path exists for T021b-0 and T021b.
- [X] T008d-1a [P] [Foundational] Create `quickstart.md` file structure with required section headers: 'Environment Setup', 'Data Generation', 'Simulation Execution', 'Visualization', and 'Interpretation'. **Deliverable**: The file MUST exist with these headers. **Verification**: Run `grep -q 'Environment Setup' quickstart.md && grep -q 'Data Generation' quickstart.md && grep -q 'Simulation Execution' quickstart.md && grep -q 'Visualization' quickstart.md && grep -q 'Interpretation' quickstart.md` to confirm headers. **Constraint**: Do not include code snippets or implementation details in this step.
- [X] T008d-1b [Foundational] Verify `quickstart.md` file exists and contains all required section headers. **Deliverable**: A verification log confirming the presence of headers. **Dependency**: T008d-1a. **Note**: This task is sequential, not parallel-safe.
- [X] T008d-2 [P] [Foundational] Write content for `quickstart.md` sections: 'Environment Setup', 'Data Generation', 'Visualization', and 'Interpretation'. **Deliverable**: Concrete instructions for installing dependencies and generating a sample dataset.
- [X] T008d-3 [P] [Foundational] Insert code snippets for `python code/main.py` into `quickstart.md` 'Simulation Execution' section as **placeholders** with explicit comments: `# TODO: Replace with actual main.py implementation (T030)`. **Constraint**: Do not write a functional script; write a placeholder that documents the intended command structure.
- [X] T008d-4 [P] [Foundational] Finalize `quickstart.md` by reviewing all sections and ensuring consistency. **Deliverable**: The file MUST be complete and ready for validation.
- [ ] T031 [Foundational] **Create Reproducible README.md (Stub)**: Create `README.md` with explicit instructions for environment setup (virtualenv, dependencies), setting a fixed random seed, and the project structure. **Deliverable**: The file MUST include: 1) Instructions for setting a fixed random seed, 2) Steps to install dependencies from `requirements.txt`, 3) A reproducibility checklist verifying that re-running the script yields identical checksums for `data/processed/*.csv`. **Constraint**: This task is a HARD GATE; User Stories (Phase 3+) cannot begin until T031 is complete AND the README.md file exists with the required content. **Dependency**: T002. **Verification**: Run `test -f README.md && grep -q 'random seed' README.md && grep -q 'requirements.txt' README.md && grep -q 'checksums' README.md` to confirm content. **Note**: This is a stub README; it does not require `code/main.py` to be functional yet.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Controlled Synthetic Datasets (Priority: P1) 🎯 MVP

**Goal**: Generate synthetic datasets across a range of sample sizes (starting from small) and distributions (normal, uniform, log-normal) with known ground truth for null and alternative hypotheses.

**Independent Test**: Verify generated data statistics (mean, variance, shape) match theoretical parameters within tolerance (±1e-6) before any testing occurs.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T008a [P] [US1] Define and write test cases for normal distribution generation in `tests/unit/test_data_generator.py` **Dependency**: T011-Interface.
- [X] T008b [P] [US1] Define and write test cases for log-normal skewness validation in `tests/unit/test_data_generator.py` **Dependency**: T011-Interface.
- [X] T008c [P] [US1] Define and write test cases for log-normal effect size validation in `tests/unit/test_data_generator.py` **Dependency**: T011-Interface.
- [X] T008d [P] [US1] Define and write test cases for uniform distribution sample size accuracy in `tests/unit/test_data_generator.py` **Dependency**: T011-Interface.

### Implementation for User Story 1

- [X] T011 [US1] Implement `code/data_generator.py` with functions to generate Normal, Uniform, and Log-Normal distributions for both Null (effect=0) and Alternative (effect=0.5) hypotheses. **Dependency**: T011-Interface.
- [X] T012 [US1] Add logic in `code/data_generator.py` to handle edge cases: ensure log-normal skew is finite and prevent numerical overflow.
- [X] T013 [US1] Implement validation routine in `code/data_generator.py` that compares generated sample statistics to theoretical parameters and raises errors on mismatch.
- [X] T014 [US1] Create a script `code/run_data_gen.py` to generate and save a small sample dataset to `data/raw/sample_validation.csv` for manual verification. **Schema**: The CSV MUST include columns: `sample_size`, `distribution_type`, `effect_size`, `group_mean_1`, `group_mean_2`, `mean_diff`, `variance`, `skewness`, `checksum`. **Validation**: `effect_size` must match input (0.0 or 0.5); `mean_diff` must be within 1e-6 of theoretical value; `checksum` must be MD5 of the JSON representation of the row dictionary (keys sorted alphabetically, encoded as UTF-8, no whitespace). **Instruction**: Use Python's built-in `json` library with `sort_keys=True` and `separators=(',', ':')` to ensure deterministic output across environments. **Dependency**: T011.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute Monte Carlo Simulations (Priority: P2)

**Goal**: Perform adaptive Monte Carlo replicates (min 1000, extend until % CI width ≤ 0.01) for t-test, ANOVA, and Chi-squared tests, switching to Fisher's Exact for small counts.

**Independent Test**: Run a small subset of a known scenario (t-test, normal, n=50, null true) and verify observed Type I error rate is close to the nominal significance level.

### Shared Validation (Blocking Gate)

- [X] T017b-impl [US1/US2] **Implement Ground-Truth Log Writer**: Create the logic in `code/simulation_engine.py` or a dedicated utility to write the specific log file required by T017b. **Deliverable**: A file `data/processed/ground_truth_validation.log` containing the verification status and parameters. **Dependency**: T013 must be complete.
- [X] T017b [US1/US2] **Run Ground-Truth Validation Gate**: Execute the validation routine from T013 on a fresh batch of generated data before starting the Monte Carlo loop. **Constraint**: This task MUST pass (exit code 0) before T018 can begin. **Deliverable**: A log entry confirming ground-truth parameters were verified for the current configuration batch. **Dependency**: T013 must be complete; T017b-impl must be complete.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T015 [P] [US2] Unit test for Type I error classification logic in `tests/unit/test_simulation.py`
- [X] T016 [P] [US2] Unit test for Chi-squared test logic and Fisher's Exact switch in `tests/unit/test_simulation.py`
- [X] T017 [P] [US2] Integration test for adaptive replication loop termination in `tests/integration/test_simulation_loop.py`

### Implementation for User Story 2

- [X] T020-1 [US2] Implement **Clopper-Pearson (Exact)** confidence interval calculation in `code/simulation_engine.py`. **Input**: A list of binary outcomes representing error and correct states, and a confidence level. **Output**: A tuple (lower_bound, upper_bound) for the 95% CI. **Constraint**: Use **Clopper-Pearson** intervals for binary outcomes as mandated by Constitution Principle VII. **Deliverable**: A function `clopper_pearson_ci(outcomes, alpha=0.05)` that returns the interval.
- [X] T020-2 [US2] Implement adaptive control loop in `code/simulation_engine.py`: start with a sufficient number of replicates, calculate 95% CI width using T020-1 (Clopper-Pearson), and trigger additional replicates until width ≤ 0.01. **Constraint**: If computational limits (MAX_REPLICATES) are reached before the width ≤ 0.01, the run MUST fall back to the fixed MAX_REPLICATES count, log a warning, and proceed with the results. **Dependency**: T020-1 must be complete.
- [X] T020-2b [US2] **Log Deviation on Cap Hit**: Implement logic to log a specific warning and record the 'UNSTABLE' flag in `data/processed/stability_log.json` if MAX_REPLICATES is hit. **Deliverable**: A JSON entry with `status: UNSTABLE` and `reason: MAX_REPLICATES_REACHED`. **Dependency**: T020-2.
- [X] T021b [US2] Implement logic in `code/simulation_engine.py` to **stream and store raw p-values** for every replicate in a structured format. **Input**: Stream p-values from T018/T020. **Output**: Write to `data/processed/raw_pvalues.csv` in real-time (or batched at the end of each configuration) using the schema and locking from T021b-0. **Schema**: Columns `sample_size`, `distribution_type`, `test_type`, `p_value`, `hypothesis_type`. **Constraint**: Store raw p-values exactly as generated; do NOT apply any clipping or transformation. **Dependency**: T021b-0 must be complete. **Note**: T021b (the writer) must be implemented before T018 (the caller) to avoid import errors.
- [X] T018 [US2] Implement `code/simulation_engine.py` with the core Monte Carlo loop: data generation (calling T011), test execution (calling T019), and result classification. **Integration**: Must integrate Fisher's Exact switch (T019), Adaptive Loop (T020-2) logic, and Streaming Writer (T021b). The loop must call the data generator, execute the appropriate test, pass results to the adaptive logic, and stream p-values. **Dependency**: T020-2b (Interface), T020-2 (Implementation), T017b (Validation), T021b (Writer), and T021b-0 must be complete. **Note**: T021b MUST be implemented before T018.
- [X] T019 [US2] Implement test execution logic in `code/simulation_engine.py`:
 - T-test (scipy.stats.ttest_ind)
 - ANOVA (scipy.stats.f_oneway)
 - Chi-squared (scipy.stats.chi2_contingency)
 - Fisher's Exact (scipy.stats.fisher_exact) triggered when expected cell counts < 5
- [X] T021c [US2] Implement explicit validation routine in `code/simulation_engine.py` to compare observed Type I error rates against the theoretical nominal alpha level for the null hypothesis scenarios. **Constraint**: The validation gate checks for the presence of raw p-values (regardless of storage mechanism). **Deliverable**: A report written to `data/processed/validation_report.csv` containing the observed vs. theoretical error rates and the difference. **Dependency**: T018 must be complete.
- [X] T022a [US2] **Define Orchestrator Interface**: Create function signatures for the batch orchestration logic (e.g., `run_batch(config) -> DataFrame`). **Deliverable**: A Python file with stubs. **Constraint**: This MUST be completed before T022b (Implementation).
- [X] T022b [US2] Create `code/run_simulation.py` to orchestrate the full batch: Multiple sample sizes × distributions × 3 tests, saving intermediate results to `data/processed/`. **Dependency**: Must consume the output of T018/T021b (`data/processed/raw_pvalues.csv` and `data/processed/validation_report.csv`). **Execution Order**: T017b-impl -> T017b -> T020-1 -> T020-2 -> T020-2b -> T021b-0a -> T021b-0 -> T021b -> T018 -> T021c -> T022a -> T022b. **Note**: T022b is the driver that calls T018; it must be implemented AFTER T018 is fully functional (executable code present), not just the interface. T022a defines the interface, but T022b requires the actual T018 implementation to invoke. T022b explicitly depends on T018 being fully functional, not just the interface.

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
- [X] T026-0 [P] [US3] **Decouple CI Methods**: Implement a distinct function `compute_final_cis(outcomes)` in `code/analyzer.py` that applies **Bootstrap Resampling** to the raw binary outcomes for final reporting. **Constraint**: This function must be separate from the Clopper-Pearson logic in T020 to ensure consistency. **Dependency**: T020 must be complete.
- [X] T026b [US3] Implement **stability measurement** in `code/analyzer.py`: Calculate the Type I error rate **for each sample size** (not a single aggregate variance). Perform a **trend analysis** (regression of error rate vs. sample size) to verify SC-002. **Output**: Write results to `data/processed/stability_trend.csv` and generate a plot of error rate vs. sample size.
- [X] T027-0 [US3] **Validate Epsilon Impact**: Implement a sensitivity analysis in `code/analyzer.py` to explicitly verify that the numerical stability epsilon (`LOG_EPSILON`) applied to p-values of exactly 0 or 1 does not artificially inflate or deflate the McFadden pseudo-R² metric. **Steps**: 1. Run regression on a small subset of data with and without epsilon. 2. Compare R² values. 3. Log the difference. **Deliverable**: A report `data/processed/epsilon_sensitivity_report.json` with `delta_r_squared` and `impact_assessment`. **Dependency**: T026-0.
- [X] T027 [US3] Implement regression analysis in `code/analyzer.py`: Fit GLM/Binomial regression to predict the magnitude of deviation from the nominal significance threshold using log(sample size), distribution, and test type. **Steps**: 1. Calculate McFadden pseudo-R² using formula `1 - (log-likelihood_model / log-likelihood_null)`. 2. Report regression coefficients (beta) and p-values. 3. **Verify if McFadden R² meets the SC-005 threshold (> 0.1)**. If the threshold is not met, the script MUST exit with code 1. **Target Variable**: Explicitly model the magnitude of deviation |p - α|. **Note**: Apply `config.LOG_EPSILON` (a small positive constant, defined in `code/config.py`) to p-values of exactly 0 or 1 *only during the log-transform calculation* (i.e., `log(p + config.LOG_EPSILON)`). This modification is explicitly required to satisfy **FR-006** (which mandates log-transform of p-values) and ensure numerical stability when p=0 or p=1. The raw p-values in storage remain unmodified. **Verification**: Confirm that the epsilon-adjusted distribution satisfies the regression requirements of **FR-006**. **Deliverable**: A JSON file at `data/processed/regression_results.json` containing keys: `beta`, `p_value`, `mc_fadden_r_squared`, and `epsilon_used`. **Error Handling**: If R² < 0.1, log "ERROR: McFadden R² ({value:.4f}) < 0.1 threshold. Pipeline halted." to `logs/regression_validation.log` and exit with code 1. **Dependency**: T027-0 must be complete.
- [X] T027c-1 [US3] Retrieve ground-truth parameters (effect size, distribution type) from `config.py` and `data_generator.py` to ensure the theoretical power curve calculation uses the exact same assumptions as the simulation for **all test types**. **Deliverable**: A configuration object or dictionary mapping simulation parameters to theoretical calculation parameters.
- [X] T027c-2 [US3] **Calculate Theoretical Power Curve (t-test)**: Implement the calculation of the theoretical power curve for the **t-test** based on the aligned parameters from T027c-1 (using `scipy.stats.nct` with non-centrality parameter `delta = effect_size * sqrt(n/)` and degrees of freedom `df = 2n - 2`) and compare the observed power curve to the theoretical power curve. **Success Criterion**: The observed curve must follow the expected theoretical trend with a **Mean Absolute Error (MAE) < 0.05**. **Deliverable**: A report containing a plot comparing observed vs. theoretical power curves for t-tests. **Note**: Theoretical power curves for ANOVA and Chi-Squared are now implemented in T027c-3 and T027c-4. **Dependency**: T027c-1 must be complete.
- [X] T027c-3 [US3] **Calculate Theoretical Power Curve (ANOVA)**: Implement an approximation of the theoretical power curve for **ANOVA** using the non-central F-distribution (`scipy.stats.ncf`) derived from the effect size and sample size. **Documentation**: Explicitly document the approximation method and its limitations. **Validation**: Verify the approximation error against `scipy.stats.ncf` is < 0.01. **Success Criterion**: The observed curve must follow the expected theoretical trend (approximation) with a **Mean Absolute Error (MAE) < 0.05**. **Deliverable**: A report containing a plot comparing observed vs. theoretical power curves for ANOVA. **Dependency**: T027c-1 must be complete.
- [X] T027c-4 [US3] **Calculate Theoretical Power Curve (Chi-Squared)**: Implement an approximation of the theoretical power curve for **Chi-Squared** tests using the non-central Chi-squared distribution (`scipy.stats.ncx2`) derived from the effect size and sample size. **Documentation**: Explicitly document the approximation method and its limitations. **Validation**: Verify the approximation error against `scipy.stats.ncx2` is < 0.01. **Success Criterion**: The observed curve must follow the expected theoretical trend (approximation) with a **Mean Absolute Error (MAE) < 0.05**. **Deliverable**: A report containing a plot comparing observed vs. theoretical power curves for Chi-Squared. **Dependency**: T027c-1 must be complete.
- [X] T028 [US3] Implement `code/visualizer.py` to generate publication-ready plots (PNG/SVG): Error Rate vs. Sample Size curves with CI bands, distinguishing distributions
- [X] T029 [US3] Create `code/export_results.py` to write final aggregated data to `data/processed/error_rates.csv` and save plots to `data/processed/plots/`
- [X] T030 [US3] Create `code/main.py` as the single entry point to orchestrate the full pipeline: Setup -> US1 (Data Gen) -> US2 (Simulation) -> US3 (Analysis/Export)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T032a Refactor `code/simulation_engine.py` to separate data generation logic from test execution logic
- [X] T032b Refactor `code/analyzer.py` to separate aggregation logic from visualization logic
- [X] T033 [P] Performance verification: Create `code/benchmark.py` to measure the execution time of the full simulation suite. **Deliverable**: The script MUST write results to `logs/benchmark.log`. **Schema**: The log MUST contain a JSON structure with a key `total_runtime_seconds` and the value in seconds. **Verification**: Run the benchmark and confirm the total time is < 6 hours.
- [X] T034 [P] Add final integration tests in `tests/integration/test_full_pipeline.py`
- [X] T037 [US3] **Prior Research-Stage Reviews**: Address reviewer concern #1 from `# Prior research-stage reviews`: "The regression model lacks an interaction term between sample size and distribution type. This may miss important effects." **Add an interaction term to the regression model.** **File**: `code/analyzer.py`. **Rationale**: Incorporate reviewer feedback to improve model accuracy.
- [X] T038 [US3] **Prior Research-Stage Reviews**: Address reviewer concern #2 from `# Prior research-stage reviews`: "The visualization does not clearly show the 95% confidence intervals for the error rates." **Increase the line width and transparency of the confidence interval bands in the plot.** **File**: `code/visualizer.py`. **Rationale**: Improve the clarity of the visualization to better communicate uncertainty.
- [X] T039 [US3] **Prior Research-Stage Reviews**: Address reviewer concern #3 from `# Prior research-stage reviews`: "The code lacks sufficient comments explaining the purpose of each function and variable." **Add detailed comments to all functions and variables in `code/analyzer.py` and `code/visualizer.py`.** **File**: `code/analyzer.py`, `code/visualizer.py`. **Rationale**: Improve code readability and maintainability.

---

## Phase 7: Revision & Verification (Post-Analysis)

**Purpose**: Address specific issues raised by `/speckit.analyze` that require code or documentation changes.

- [ ] T040 [US3] **Revision: Correct Power Curve Formula**: Fix the theoretical power curve calculation in `code/analyzer.py` (T027c-2) to use the correct non-centrality parameter formula `delta = effect_size * sqrt(n/2)` (correcting the previous `sqrt(n/)` typo) for the t-test to ensure the MAE < 0.05 criterion is met. **File**: `code/analyzer.py`. **Rationale**: The previous formula was syntactically incomplete and would cause a runtime error or incorrect results.
- [ ] T041 [US2] **Revision: Enforce Streaming for Large Batches**: Ensure `code/simulation_engine.py` (T021b) strictly streams p-values to disk in chunks (e.g., every replicates) rather than buffering in memory, to prevent OOM errors during the adaptive loop on the GB RAM runner. **File**: `code/simulation_engine.py`. **Rationale**: The current implementation may buffer too much data for large sample sizes (n=1000) with high replicate counts, risking memory exhaustion.
- [ ] T042 [US3] **Revision: Validate Interaction Term Significance**: Add a post-hoc check in `code/analyzer.py` (T027) to explicitly verify that the added interaction term (from T037) is statistically significant (p < 0.05) before including it in the final model output. **File**: `code/analyzer.py`. **Rationale**: Simply adding an interaction term does not guarantee it improves the model; it must be statistically justified.

---

## Optional / Future Scope (NOT required for MVP)

**Purpose**: Enhancements that are explicitly out of scope for the current MVP

- [X] T036 [P] **Optional Scope**: Implement a `code/checkpoint_manager.py` to save partial results after every periodic interval of replicates per configuration. **Rationale**: Mitigates the risk of losing progress on the 6-hour runner if the process is killed mid-batch. **Output**: Save intermediate state to `data/processed/checkpoints/` and implement a resume flag in `main.py`. **Note**: This task is explicitly OPTIONAL and NOT required for the MVP. It should only be implemented if the project scope is expanded beyond the current MVP definition.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Revision (Phase 7)**: Depends on `/speckit.analyze` output; tasks here address specific findings.

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
- **CI Method**: The adaptive replication loop (T020) uses **Clopper-Pearson (Exact)** intervals for binary outcomes as per Constitution Principle VII. T026 and T026-0 use **Bootstrap Resampling** for final reporting. These methods are explicitly consistent with the Constitution.
- **Regression Data**: Raw p-values MUST be stored by T021b (unmodified) and consumed by T027. T027 applies a numerical stability epsilon (`config.LOG_EPSILON`, 1e-15) *only during the log-transform calculation* (standard practice for zero probabilities), explicitly documenting this as a deviation from raw data for numerical stability to satisfy **FR-006**.
- **Execution Order**: Phase 4 tasks must be executed in the order: T017b-impl -> T017b -> T020-1 -> T020-2 -> T020-2b -> T021b-0a -> T021b-0 -> T021b -> T018 -> T021c -> T022a -> T022b. T017b (Ground-Truth Validation) must run after T017b-impl. T022b is the orchestrator; its implementation requires the code of T018 to be present. **T021b must be implemented before T018**.
- **Robustness**: T036 adds checkpointing to prevent total data loss on long-running simulations if the runner timeouts. Note: This is **OPTIONAL** scope as per the spec's assumptions and is NOT required for MVP.
- **McFadden R²**: T027 explicitly calculates McFadden pseudo-R² and verifies against SC-005 threshold. If the threshold is not met, the script exits with code 1.
- **Power Curves**: T027c-2 covers t-test theoretical power curve. T027c-3 (ANOVA) and T027c-4 (Chi-Squared) are now **implemented** with documented approximations and MAE < 0.05 success criteria.
- **UNSTABLE Flag**: T020-2 explicitly flags 'UNSTABLE' if MAX_REPLICATES is reached, ensuring deterministic handling of partial results.
- **Streaming Enforcement**: T021c removes the fallback batch and enforces the streaming pipeline as a hard requirement, with T021b-fallback as a safety net.
- **CI Method Alignment**: T020-1/T020-2 use Clopper-Pearson, consistent with Constitution Principle VII.
- **Data Transformation**: T027 explicitly documents the epsilon transformation as a deviation from raw data for numerical stability, referencing `config.LOG_EPSILON` and citing **FR-006**.
- **Scope Creep**: T035, T035-1 (mock runner) removed as scope creep. T020-1, T020-4 merged into T020-2 (now T020-1/T020-2). T021 (original) merged into T021b logic.
- **Removed Tasks**: T027b removed (logic integrated into T027). T021 (original) merged into T021b logic. T040 removed (logic integrated into T020-1/2).
- **Reviewer Feedback**: Tasks T037, T038, T039, T040 (removed), and T041 (merged into T027c-3/4) address specific research-stage review concerns regarding model interactions, visualization clarity, code documentation, CI method validity, and theoretical benchmark consistency.
- **T031 Gate**: T031 (README) is now a prerequisite in Phase 2 to ensure reproducibility before simulation work begins.
- **Implementation Order**: T021b (Writer) must be implemented before T018 (Caller) to avoid import errors. T022b (Orchestrator) calls T018 and must be implemented after T018's logic is ready.
- **Fallback Logic**: T020-2 implements fallback to fixed MAX_REPLICATES if CI width < 0.01 is not reached, as per Plan.md constraints.
- **MAE Criteria**: T027c-2, T027c-3, and T027c-4 use MAE < 0.05 as the quantitative success criterion for power curve validation.
- **Exit Code**: T027 exits with code 1 if McFadden R² < 0.1.
- **Revision Note**: Phase 7 tasks (T040-T042) were added in response to `/speckit.analyze` findings to correct formula errors, enforce memory safety, and validate statistical significance of added terms.
- **Approximation Baseline**: T027c-3 and T027c-4 use the non-central distribution (`scipy.stats.ncf`, `scipy.stats.ncx2`) as the theoretical baseline for MAE < 0.05 check, with a validation step to ensure the approximation error is < 0.01.
- **Epsilon Validation**: T027-0 validates the impact of the epsilon adjustment before T027 runs.
- **Logging**: T027 logs a specific error message format on failure.
- **Directory Creation**: T021b-0a ensures `code/utils/` exists.
- **README**: T031 is a stub in Phase 2, removing circular dependency.