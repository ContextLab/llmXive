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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory structure (`code/`, `data/raw/`, `data/processed/`, `tests/`, `logs/`). **Deliverable**: Empty directories with `.gitkeep` files.
- [X] T002 Initialize Python 3.11 project with dependencies (`numpy`, `scipy`, `pandas`, `matplotlib`, `seaborn`, `scikit-learn`, `pytest`, `statsmodels`, `betareg` or equivalent) in `requirements.txt`.
- [X] T003 [P] Configure linting (flake8/black) and formatting tools in `setup.cfg` or `pyproject.toml`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/config.py` to define simulation parameters (sample sizes n=10..1000, distributions, alpha=0.05, effect sizes, `MAX_REPLICATES=10000`, `LOG_EPSILON=1e-15`, `SEED_BASE=42`).
- [X] T005 [P] Implement `code/__init__.py` and basic logging infrastructure.
- [X] T006 Create `data/raw/` and `data/processed/` directories with `.gitkeep`.
- [X] T007 Setup `tests/unit/` and `tests/contract/` directory structure.
- [X] T008d [P] [Foundational] Create and populate `quickstart.md` with Environment Setup, Data Generation, Simulation Execution, Visualization, and Interpretation sections. **Deliverable**: A complete markdown file with code placeholders. **Constraint**: This task is a documentation deliverable, not a code dependency for data generation.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Controlled Synthetic Datasets (Priority: P1) 🎯 MVP

**Goal**: Generate synthetic datasets across a range of sample sizes (starting from small) and distributions (normal, uniform, log-normal) with known ground truth for null and alternative hypotheses.

**Independent Test**: Verify generated data statistics (mean, variance, shape) match theoretical parameters within tolerance (±1e-6) before any testing occurs.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T009a [P] [US1] IF tests requested: Implement `tests/unit/test_data_generator.py::test_normal_mean_validation`. **Assertion**: Verify sample mean difference for normal distribution (n=50, effect=0.0) is within 1e-6 of 0.0. **Dependency**: None (TDD: defines expected behavior per spec).
- [X] T009b [P] [US1] IF tests requested: Implement `tests/unit/test_data_generator.py::test_lognormal_skewness_validation`. **Assertion**: Verify skewness of log-normal distribution (n=30) matches theoretical value within 5% tolerance. **Dependency**: None (TDD: defines expected behavior per spec).
- [X] T009c [P] [US1] IF tests requested: Implement `tests/unit/test_data_generator.py::test_lognormal_effect_size_validation`. **Assertion**: Verify mean difference for log-normal distribution (n=30, effect=0.5) is within 1e-6 of 0.5. **Dependency**: None (TDD: defines expected behavior per spec).
- [X] T009d [P] [US1] IF tests requested: Implement `tests/unit/test_data_generator.py::test_uniform_sample_size_accuracy`. **Assertion**: Verify sample size for uniform distribution (n=1000) is exactly 1000 and data fits uniform profile. **Dependency**: None (TDD: defines expected behavior per spec).

### Implementation for User Story 1

- [X] T011 [US1] Implement `code/data_generator.py` with functions to generate Normal, Uniform, and Log-Normal distributions for both Null (effect=0) and Alternative (effect=0.5) hypotheses. **Constraint**: Use `np.random.seed` derived from `config.SEED_BASE` and configuration hash for reproducibility (Constitution Principle I).
- [X] T012 [US1] Add logic in `code/data_generator.py` to handle edge cases: ensure log-normal skew is finite and prevent numerical overflow.
- [X] T013 [US1] Implement validation routine in `code/data_generator.py` that compares generated sample statistics to theoretical parameters and raises errors on mismatch.
- [X] T014 [US1] Create a script `code/run_data_gen.py` to generate and save a small sample dataset to `data/raw/sample_validation.csv` for **manual verification only**. **Schema**: The CSV MUST include columns: `sample_size`, `distribution_type`, `effect_size`, `group_mean_1`, `group_mean_2`, `mean_diff`, `variance`, `skewness`, `checksum`. **Validation**: `effect_size` must match input (0.0 or 0.5); `mean_diff` must be within 1e-6 of theoretical value; `checksum` must be MD5 of the JSON representation of the row dictionary (keys sorted alphabetically, encoded as UTF-8, no whitespace, using `json.dumps(row, sort_keys=True, separators=(',', ':'))`). **Instruction**: Use Python's built-in `json` library with `sort_keys=True` and `separators=(',', ':')` to ensure deterministic output across environments. **Dependency**: T011. **Note**: This task generates a **manual verification artifact** and is **NOT a dependency for the automated T017b gate** (which uses T013). It is **optional** and can be skipped if automated validation is sufficient. **CRITICAL**: The automated Ground-Truth Validation Gate (T017b) relies exclusively on the logic in T013, NOT on the artifact generated by T014. T014 is for human inspection only and does not block the simulation pipeline.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute Monte Carlo Simulations (Priority: P2)

**Goal**: Perform adaptive Monte Carlo replicates (min 1000, extend until 95% CI width ≤ 0.01 or A maximum of a substantial number of samples will be considered.) for t-test, ANOVA, and Chi-squared tests, switching to Fisher's Exact for small counts.

**Independent Test**: Run a small subset of a known scenario (t-test, normal, n=50, null true) and verify observed Type I error rate is close to the nominal significance level.

### Shared Validation (Blocking Gate)

- [X] T017b [US1/US2] **Run Ground-Truth Validation Gate**: Execute the validation routine from T013 on a fresh batch of generated data before starting the Monte Carlo loop. **Implementation**: Run `python code/data_generator.py --validate` and check exit code. **Constraint**: This task MUST pass (exit code 0) before T018 can begin. **Deliverable**: A log entry confirming ground-truth parameters were verified for the current configuration batch. **Dependency**: T013 must be complete. **Note**: This task relies on the automated logic in T013, NOT on the manual artifact T014. T014 is strictly optional and does not block this gate.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T015 [P] [US2] IF tests requested: Implement `tests/unit/test_simulation.py::test_type1_error_classification`. **Assertion**: Verify Type I error classification logic correctly identifies rejections of true null hypotheses. **Dependency**: None (TDD).
- [X] T016 [P] [US2] IF tests requested: Implement `tests/unit/test_simulation.py::test_fisher_exact_trigger`. **Assertion**: Verify `scipy.stats.chi2_contingency` returns p < 0.05 for a 2x2 table with counts [[high, low], [low, high]] and that Fisher's Exact is triggered for expected counts < 5. **Deliverable**: A test case asserting these conditions. **Dependency**: None (TDD).
- [X] T017 [P] [US2] IF tests requested: Implement `tests/integration/test_simulation_loop.py::test_adaptive_termination`. **Assertion**: Verify adaptive replication loop terminates when CI width ≤ 0.01 or max replicates reached. **Dependency**: None (TDD).

### Implementation for User Story 2

- [X] T018 [US2] Implement `code/simulation_engine.py`:
 - **Data Generation**: Call `code/data_generator.py` for each configuration.
 - **Test Execution**: T-test (`scipy.stats.ttest_ind`), ANOVA (`scipy.stats.f_oneway`), Chi-squared (`scipy.stats.chi2_contingency`), Fisher's Exact (`scipy.stats.fisher_exact`) triggered when expected cell counts < 5.
 - **Seeding**: Implement deterministic seeding strategy where each replicate uses a unique seed derived from the configuration hash and replicate index (Constitution Principle I).
 - **Classification**: Classify outcomes as Type I or Type II based on p-value and alpha.
 - **Streaming**: Stream p-values to `data/processed/raw_pvalues.csv` in real-time (append mode, no file locking required for single runner). **Schema**: Columns `sample_size`, `distribution_type`, `test_type`, `p_value`, `hypothesis_type`. **Constraint**: Store raw p-values exactly as generated; do NOT apply any clipping or transformation. Use **append mode** with a **configurable batch size**. **Note**: This engine MUST incorporate the adaptive control logic from T020-2 to determine when to stop replicates. **Dependency**: T011, T017b.
- [X] T020-1 [US2] Implement **Clopper-Pearson (Exact Binomial)** confidence interval calculation in `code/analyzer.py`. **Input**: A list of binary outcomes representing error and correct states, and `alpha=0.05`. **Output**: A tuple (lower_bound, upper_bound) for the 95% CI. **Constraint**: Use **Clopper-Pearson** intervals (exact binomial) for binary outcomes as mandated by Plan Constitution Principle VII and Complexity Tracking. **Deliverable**: A function `clopper_pearson_ci(outcomes, alpha=0.05)` that returns the interval. **Dependency**: None.
- [X] T020-2 [US2] Implement adaptive control loop logic in `code/simulation_engine.py`: start with a sufficient number of replicates, calculate 95% CI width using T020-1 (Clopper-Pearson: `width = Upper - Lower`), and trigger additional replicates until width ≤ 0.01. **Constraint**: If replicates are reached and CI width > 0.01, the run MUST log 'UNSTABLE' to `logs/simulation.log` at WARNING level with the exact string 'UNSTABLE'. **Dependency**: T020-1 must be complete. **Note**: This logic is integrated into T018.
- [X] T021c [US2] Implement explicit validation routine in `code/simulation_engine.py` to compare observed Type I error rates against the theoretical nominal alpha level for the null hypothesis scenarios. **Constraint**: The validation gate checks for the existence and validity of `data/processed/aggregated_results.csv`. **Deliverable**: A report written to `data/processed/validation_report.csv` containing the observed vs. theoretical error rates and the difference. **Dependency**: T018 must be complete. **Note**: This task validates the *result* (error rates), not the streaming implementation detail. The validation logic MUST verify that `aggregated_results.csv` exists and contains valid error rates (0 <= rate <= 1) independent of how the data was stored (streaming or batch).
- [X] T022 [US2] Create `code/run_simulation.py` to orchestrate the full batch: Multiple sample sizes × distributions × 3 tests, saving intermediate results to `data/processed/`. **Dependency**: Must consume the output of T018 (`data/processed/raw_pvalues.csv`) and T021c (`data/processed/validation_report.csv`). **Execution Order**: T017b -> T018 (incorporating T020-2) -> T021c -> T022. **Note**: T022 is the orchestrator; its implementation requires the code of T018 to be present. **Fallback**: If input files are missing, T022 must exit with code 1 and log 'ERROR: Missing input files'. **Dependency**: T018, T021c must be complete.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Aggregate Results and Visualize (Priority: P3)

**Goal**: Aggregate error rates, compute confidence intervals, fit regression models, and generate publication-ready CSV and plots.

**Independent Test**: Verify CSV output contains all required columns and plots correctly map sample size to error rate with confidence intervals.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US3] IF tests requested: Implement `tests/unit/test_analyzer.py::test_csv_export_format`. **Assertion**: Verify CSV export contains all required columns (sample_size, distribution, test, error_rate, ci_lower, ci_upper). **Dependency**: None (TDD).
- [X] T024 [P] [US3] IF tests requested: Implement `tests/unit/test_analyzer.py::test_clopper_pearson_ci`. **Assertion**: Verify Clopper-Pearson CI calculation returns correct bounds for known proportions. **Dependency**: None (TDD).
- [X] T025 [P] [US3] IF tests requested: Implement `tests/unit/test_analyzer.py::test_cox_snell_r_squared`. **Assertion**: Verify Cox-Snell pseudo-R² calculation matches theoretical formula for Beta Regression. **Dependency**: None (TDD).

### Implementation for User Story 3

- [X] T026 [US3] Implement `code/analyzer.py` to load simulation results, aggregate by (n, distribution, test), and compute **Clopper-Pearson** confidence intervals for final reporting (per Plan Constitution Principle VII). **Note**: This task consumes the raw p-values from T018.
- [X] T026b [US3] Implement **stability measurement** in `code/analyzer.py`: Calculate the Type I error rate **for each sample size** (not a single aggregate variance). Perform a **trend analysis** using **linear regression** of error rate vs. sample size to verify SC-002. **Output**: Write results to `data/processed/stability_trend.csv`, generate a plot of error rate vs. sample size, **calculate the aggregate stability metric** (slope of the regression line), and **verify the robustness claim** defined in SC-002 (slope < 0.01). **Deliverable**: A report containing the slope and a boolean success flag. **Dependency**: T026 must be complete.
- [X] T027-1 [US3] Implement regression analysis in `code/analyzer.py`: Fit a **Beta Regression** model (using `statsmodels` or `betareg`) to predict the **error rate** (proportion, bounded between 0 and 1) based on log-transformed sample size, distribution type, and test type. **Target**: `error_rate` (continuous proportion). **Input**: Aggregated error rates from T026. **Output**: Regression coefficients (beta), p-values, and model fit statistics. **Constraint**: Use a Beta Regression family. **Note**: This task directly models the magnitude of deviation from nominal alpha by analyzing the error rate itself as a function of predictors, adhering to the Plan's 'Note on Spec Deviation'. **Dependency**: T026 must be complete.
- [X] T027-2 [US3] Calculate **Cox-Snell pseudo-R²** using the formula appropriate for Beta Regression (based on log-likelihoods of the fitted model and a null model) and report the value. **Constraint**: Do NOT use McFadden pseudo-R² as it is invalid for Beta Regression. **Deliverable**: The Cox-Snell R² value. **Dependency**: T027-1 must be complete.
- [X] T027-3 [US3] Verify if Cox-Snell R² meets the amended SC-005 threshold (> 0.1). If the threshold is not met, log a critical warning. **Note**: This replaces the McFadden threshold check. **Dependency**: T027-2 must be complete.
- [X] T027-4 [US3] Export regression results to `data/processed/regression_results.json`. **Schema**: JSON object with keys `beta` (list of floats, precision), `p_value` (float, precision), `cox_snell_r_squared` (float, precision), and `test_type` (string) for each test type. **Dependency**: T027-1, T027-2, T027-3 must be complete.
- [X] T027c-1 [US3] Retrieve ground-truth parameters (effect size, distribution type) from `config.py` and `data_generator.py` to ensure the theoretical power curve calculation uses the exact same assumptions as the simulation for **all test types**. **Deliverable**: A configuration object or dictionary mapping simulation parameters to theoretical calculation parameters.
- [X] T027c [US3] **Calculate Theoretical Power Curves**: Implement a unified function in `code/analyzer.py` to calculate theoretical power curves for **t-test**, **ANOVA**, and **Chi-Squared** tests using `scipy.stats` (nct, ncf, ncx2 respectively). **Effect Size Definition**: `effect_size=0.5` maps to Cohen's d/f/w = 0.5. **Formula**: Use appropriate non-centrality parameters for each test. Compute the MAE between observed power curves and theoretical power curves for each test type. **Success Criterion**: MAE < 0.01 for each test. **Deliverable**: A consolidated report containing the MAE for each test type, plots comparing observed vs. theoretical power curves, and a boolean `success` flag indicating if SC-004 is met. **File**: `data/processed/power_curve_validation.csv` and `data/processed/plots/power_curve_*.png`. **Dependency**: T027c-1 must be complete. **Note**: This task consolidates T027c-2, T027c-3, T027c-4 into a single efficient implementation.
- [X] T028 [US3] Implement `code/visualizer.py` to generate publication-ready plots (PNG/SVG): Error Rate vs. Sample Size curves with CI bands, distinguishing distributions. **Requirement**: Explicitly label the confidence interval bands as 'confidence level' in the legend and axis labels, and add a caption explaining the Clopper-Pearson method used.
- [X] T029 [US3] Create `code/export_results.py` to write final aggregated data to `data/processed/error_rates.csv` and save plots to `data/processed/plots/`.
- [X] T030 [US3] Create `code/main.py` as the single entry point to orchestrate the full pipeline: Setup -> US1 (Data Gen) -> US2 (Simulation) -> US3 (Analysis/Export). **CLI Args**: `--config`, `--output`, `--verbose`. **Orchestration**: Call T011, T018, T026, T028 in sequence. **Exit Codes**: 0 for success, 1 for validation failure, 2 for missing inputs.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T031 [P] Documentation updates in `README.md` explaining how to run the simulation and interpret results. **Content**: Must include execution commands, parameter explanations, and interpretation of error rate curves.
- [X] T032a Refactor `code/simulation_engine.py` to separate data generation logic from test execution logic.
- [X] T032b Refactor `code/analyzer.py` to separate aggregation logic from visualization logic.
- [X] T033 [P] Performance verification: Create `code/benchmark.py` to measure the execution time of the full simulation suite. **Deliverable**: The script MUST write results to `logs/benchmark.log`. **Schema**: The log MUST contain a JSON structure with a key `total_runtime_seconds` and the value in seconds. **Verification**: Run the benchmark and confirm the total time is < 6 hours. **Constraint**: The script must explicitly check the 6-hour constraint and fail if not met.
- [X] T034 [P] Add final integration tests in `tests/integration/test_full_pipeline.py`.
- [X] T035 [US3] **Regression Interaction**: Add an interaction term between sample size and distribution type to the regression model in `code/analyzer.py` to capture interaction effects (improves model accuracy). **Rationale**: Standard statistical practice to account for interaction effects.
- [X] T036 [US2] **Timeout Limit**: Add a `TIMEOUT_SECONDS` parameter to `config.py` and implement a time-check within the adaptive loop in `code/simulation_engine.py` that breaks the loop and logs a 'TIMEOUT' warning if exceeded. **Rationale**: Prevent resource exhaustion and ensure the simulation completes within the 6-hour constraint even if statistical convergence is slow.
- [X] T037 [US1] **Log-Normal Parameter Alignment**: Refactor the log-normal generation logic in `code/data_generator.py` to explicitly calculate the scale parameter based on the desired effect size and group means, ensuring the theoretical mean difference matches the input effect size. **Rationale**: Correct the ground-truth parameters for the log-normal distribution to ensure the alternative hypothesis is accurately represented.
- [X] T038 [US3] **GLM Diagnostics**: Verify that the Beta Regression family is correctly specified, and add a diagnostic check in `code/analyzer.py` to report the deviance residual distribution. **Rationale**: Ensure the statistical model is correctly specified for the bounded nature of error rates, preventing misleading R² values.
- [X] T039 [US2] **Checkpoints**: Implement a checkpoint runner to save intermediate simulation states at regular intervals to prevent data loss on long-running simulations. **File**: `code/checkpoint_runner.py`. **Rationale**: Ensure robustness for long-running simulations.
- [X] T040 [US2] **Equal Group Sizes**: Verify and enforce equal group sizes in the ANOVA data generation step within `code/simulation_engine.py` before calling `scipy.stats.f_oneway` to ensure the theoretical comparison is valid. **Rationale**: Ensure the theoretical power curve (T027c) is calculated against the exact same experimental conditions as the simulation to avoid invalid MAE comparisons.
- [X] T041 [US2] **Adaptive Loop Concurrency**: Refactor `code/simulation_engine.py` to support parallel execution of independent replicates within a single configuration batch (using `multiprocessing` or `concurrent.futures`), ensuring the adaptive termination condition is correctly synchronized across workers. **Rationale**: The current sequential implementation may struggle to meet the 6-hour constraint for configurations requiring near-maximum replicates; parallelization is required to ensure feasibility on the CPU-only runner. **Dependency**: T018, T020-2.
- [X] T042 [US3] **Regression Robustness Check**: Implement a secondary validation in `code/analyzer.py` that fits a robust regression model (e.g., using Huber loss or RANSAC) to the error rate vs. sample size data to verify that the primary Beta Regression results are not driven by outliers at extreme sample sizes (n=10 or n=1000). **Rationale**: Small sample sizes (n=10) and extreme skew may produce unstable error rate estimates that disproportionately influence the regression slope; a robust check ensures the trend is genuine. **Dependency**: T027-1, T027c-1.
- [X] T043 [US1] **Distribution Parameter Sensitivity**: Add a task to `code/data_generator.py` to verify that the generated log-normal distribution maintains the specified skewness within a a tolerance of a small, predefined percentage across the full range of sample sizes (n=10 to n=1000), logging a warning if the skewness drifts significantly due to sampling noise. **Rationale**: The log-normal distribution is highly sensitive to sample size; ensuring the skewness remains stable validates the "known ground truth" assumption for the alternative hypothesis. **Dependency**: T011, T013.

**Checkpoint**: Project is complete and ready for final validation.

---

## Phase 7: Final Review & Compliance (Revision Concerns)

**Purpose**: Address specific reviewer concerns regarding data integrity, statistical validity, and execution robustness identified in the latest revision cycle.

- [ ] T044 [US1] **Strict Synthetic Validation**: Refactor `code/data_generator.py` to ensure that if the synthetic data generation logic fails to produce data matching theoretical ground truth parameters (within tolerance), the script MUST raise an exception and exit with a non-zero code. **Constraint**: There is NO 'real data fetch' mechanism; this task validates the *synthetic generator* itself. **Rationale**: Prevents silent fabrication of data; ensures the execution stage discovers generation issues immediately. The validation must strictly compare generated statistics (mean, variance, skewness) against the known theoretical parameters defined in `config.py` and `data_generator.py`. If the deviation exceeds the tolerance (e.g., 1e-6 for means, [deferred] for skewness), the script MUST raise a `ValueError` with a descriptive message and exit.
- [ ] T045 [US2] **Adaptive Loop Concurrency Verification**: IF T041 is implemented: Implement a unit test in `tests/unit/test_simulation.py::test_parallel_adaptive_termination` to verify that the parallel execution in T041 correctly aggregates error counts and respects the global CI width threshold without race conditions. **IF T041 is NOT implemented: SKIP this task.** **Rationale**: Ensures the parallelization logic does not introduce statistical errors in the adaptive termination condition. **Dependency**: T041 must be implemented.
- [ ] T046 [US3] **Regression Model Diagnostics**: Extend the Beta Regression diagnostic output in `code/analyzer.py` to include a check for overdispersion (if applicable) and log a warning if the dispersion parameter significantly exceeds 1. **Rationale**: Ensures the validity of the regression coefficients and p-values when modeling error rates.
- [ ] T047 [US2] **Fisher's Exact Test Threshold Verification**: IF T041 is implemented: Add a unit test in `tests/unit/test_simulation.py::test_fisher_exact_threshold` to verify that the switch to Fisher's Exact Test occurs exactly when the expected cell count is < 5, and not for counts >= 5. **IF T041 is NOT implemented: SKIP this task.** **Rationale**: Ensures strict adherence to the statistical validity constraint defined in FR-002. **Dependency**: T041 must be implemented.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Final Review (Phase 7)**: Depends on Phase 6 completion; addresses specific revision concerns.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data generation logic (T011) and T017b (Ground-Truth Validation)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 simulation results and raw p-value storage (T018)

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
Task: "Implement tests/unit/test_data_generator.py::test_normal_mean_validation"
Task: "Implement tests/unit/test_data_generator.py::test_lognormal_skewness_validation"
Task: "Implement tests/unit/test_data_generator.py::test_lognormal_effect_size_validation"
Task: "Implement tests/unit/test_data_generator.py::test_uniform_sample_size_accuracy"

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
- **CI Method**: The adaptive replication loop (T020) and final reporting (T026) use **Clopper-Pearson (exact binomial)** intervals, as mandated by the Plan Constitution Principle VII and Complexity Tracking. This ensures stability for small proportions.
- **Regression Data**: The regression model (T027-1) uses **Beta Regression** to model continuous error rates, replacing the invalid Binomial GLM on logit-transformed deviations. This aligns with the Plan's 'Note on Spec Deviation'.
- **Execution Order**: Phase 4 tasks must be executed in the order: T017b -> T018 (incorporating T020-2) -> T021c -> T022. T017b (Ground-Truth Validation) must run before T018. T018 (Simulation) must run before T020 (CI Calculation) and T021 (Streaming). T022 is the orchestrator; its implementation requires the code of T018 to be present.
- **Robustness**: T036 (checkpoint runner) restored.
- **Cox-Snell R²**: T027 explicitly calculates Cox-Snell pseudo-R² and verifies against the amended SC-005 threshold.
- **Power Curves**: T027c covers all three test types required by SC-004 in a unified implementation. T027c-5 logic is integrated into T027c.
- **UNSTABLE Flag**: T020-2 explicitly flags 'UNSTABLE' if MAX_REPLICATES (10,000) is reached, ensuring deterministic handling of partial results.
- **Streaming Enforcement**: T018 enforces the streaming pipeline as a hard requirement for raw data storage.
- **CI Method Alignment**: T020-1/T020-2 use Clopper-Pearson, consistent with Plan.
- **Data Transformation**: T027 explicitly documents the use of Beta Regression for continuous proportions, replacing the invalid logit transformation.
- **Scope Creep**: T036 (checkpoint runner) restored.
- **Removed Tasks**: T027b removed (logic integrated into T027). T021 (original) merged into T018 logic. T008d-1a, 1b, 2, 3, 4 merged into T008d. Phase 7 removed (hallucinated reviews). T027c-2, T027c-3, T027c-4 merged into T027c.
- **Reviewer Concerns**: T035 addresses interaction terms in regression; T038 addresses CI visualization clarity; T039 addresses code documentation; T040 addresses ANOVA group size consistency for theoretical power curve validation.
- **New Revision Concerns**: T036 addresses timeout limits for adaptive loops; T037 addresses log-normal parameter alignment; T038 addresses GLM specification for bounded variables; T039 addresses code documentation; T040 addresses ANOVA group size consistency.
- **T041**: Addresses the potential failure to meet the 6-hour compute constraint by introducing parallel execution for the adaptive Monte Carlo loop.
- **T042**: Addresses the risk of outlier-driven regression results at extreme sample sizes by adding a robustness check.
- **T043**: Addresses the sensitivity of the log-normal distribution's skewness to sample size, ensuring the ground truth assumption holds across the full range.
- **Manual vs Automated Flow**: T014 (sample_validation.csv) is strictly for manual inspection and does NOT block the automated T017b gate. The automated gate relies on T013 (validation logic). T014 is optional and can be skipped.
- **Phase 7 (New)**: Addresses critical data integrity and statistical validity concerns raised in the latest review cycle (T044-T047).
- **Conditional Tasks**: T045 and T047 are conditional on T041 being implemented.
- **Statistical Validity**: T027-1, T027-2, T027-3 now correctly implement Beta Regression and Cox-Snell pseudo-R², resolving the Plan's identified contradiction.
- **Data Integrity**: T044 correctly validates synthetic generation without fetching non-existent real data.
- **Validation Gate**: T021c validates the result (error rates) independent of the streaming implementation.
- **Consolidated Tasks**: T027c-2, T027c-3, T027c-4 removed; T027c is now the single unified task.
- **Conditional Execution**: T045 and T047 explicitly state "IF T041 not implemented: SKIP".
- **Synthetic Data Validation**: T044 ensures that synthetic data generation is strictly validated against theoretical ground truth, with no fallback to "real data fetch" or synthetic fabrication.
- **Beta Regression**: T027-1 correctly models continuous error rates using Beta Regression, avoiding invalid logit transforms on deviation scores.
- **Cox-Snell R²**: T027-2 and T027-3 implement the scientifically valid Cox-Snell pseudo-R² for Beta Regression, resolving the Plan's identified contradiction.
- **Result-Based Validation**: T021c validates the presence and validity of `aggregated_results.csv` independent of streaming implementation details.
- **Unified Power Curves**: T027c consolidates power curve calculations for all test types into a single efficient implementation.
- **Conditional Parallel Tests**: T045 and T047 are explicitly conditional on T041 to prevent orphan tasks.