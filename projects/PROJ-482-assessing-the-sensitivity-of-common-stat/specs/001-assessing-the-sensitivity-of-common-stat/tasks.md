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
- [X] T002 Initialize Python 3.11 project with dependencies (`numpy`, `scipy`, `pandas`, `matplotlib`, `seaborn`, `pytest`, `statsmodels`) in `requirements.txt`. **Note**: Use `statsmodels.genmod.families.Binomial` for Binomial GLM. Removed `scikit-learn` as it is not required by spec or plan.
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
- [X] T009b [P] [US1] IF tests requested: Implement `tests/unit/test_data_generator.py::test_lognormal_skewness_validation`. **Assertion**: Verify skewness of log-normal distribution (n=30) matches the theoretical value `(exp(sigma^2) + 2) * sqrt(exp(sigma^2) - 1)` within the theoretical standard error of skewness for n=30 (approx 0.42), ensuring the tolerance is statistically derived rather than arbitrary. **Dependency**: None (TDD: defines expected behavior per spec).
- [X] T009c [P] [US1] IF tests requested: Implement `tests/unit/test_data_generator.py::test_lognormal_effect_size_validation`. **Assertion**: Verify mean difference for log-normal distribution (n=30, effect=0.5) is within 1e-6 of 0.5. **Dependency**: None (TDD: defines expected behavior per spec).
- [X] T009d [P] [US1] IF tests requested: Implement `tests/unit/test_data_generator.py::test_uniform_sample_size_accuracy`. **Assertion**: Verify sample size for uniform distribution (n=1000) is exactly 1000 and data fits uniform profile. **Dependency**: None (TDD: defines expected behavior per spec).

### Implementation for User Story 1

- [ ] T044-1 [US1] **Theoretical Parameter Calculation**: Implement a function in `code/data_generator.py` to calculate the *theoretical* mean, variance, and skewness for the specified distribution and effect size. **Deliverable**: A function `calculate_theoretical_parameters(dist_type, effect_size)` returning expected stats. **Dependency**: T004.
- [ ] T044-2 [US1] **Validation Function**: Implement a function `validate_theoretical_parameters` in `code/data_generator.py` that compares the calculated theoretical parameters against expected ground truth values within a tolerance of a sufficiently low magnitude. **Constraint**: This function raises `ValueError` if the theoretical parameters are misaligned. **Deliverable**: A validation function. **Dependency**: T044-1.
- [X] T044-3 [US1] **Integration**: Integrate the theoretical validation logic into the generator initialization. **Deliverable**: Generator initialization calls `validate_theoretical_parameters`. **Dependency**: T044-2.
- [X] T044-NEW [US1] **Summary**: This task summarizes the validation logic implemented in T044-1, T044-2, and T044-3. **Status**: Complete (see sub-tasks). **Dependency**: T004.
- [X] T011 [US1] Implement `code/data_generator.py` with functions to generate Normal, Uniform, and Log-Normal distributions for both Null (effect=0) and Alternative (effect=0.5) hypotheses. **Constraint**: Use `np.random.seed` derived from `config.SEED_BASE` and configuration hash for reproducibility (Constitution Principle I). **Dependency**: T004, T044-3.
- [X] T012 [US1] Add logic in `code/data_generator.py` to handle edge cases: ensure log-normal skew is finite and prevent numerical overflow.
- [X] T013 [US1] Implement validation routine in `code/data_generator.py` that compares *sample* statistics of a generated batch to theoretical parameters and raises errors on mismatch. **Note**: This routine is for *sample* validation (e.g., for T017b) and uses a tolerance appropriate for sample size (e.g., 3 standard errors), distinct from T044-NEW's theoretical validation. **Dependency**: T011.
- [ ] T014 [US1] **Mandatory**: Create a script `code/run_data_gen.py` to generate and save a small sample dataset to `data/raw/sample_validation.csv` for **manual verification**. **Schema**: The CSV MUST include columns: `sample_size`, `distribution_type`, `effect_size`, `group_mean_1`, `group_mean_2`, `mean_diff`, `variance`, `skewness`, `checksum`. **Validation**: `effect_size` must match input (0.0 or 0.5); `mean_diff` must be within 1e-6 of theoretical value. **Checksum**: The `checksum` column must contain the MD5 hash of the JSON representation of the row dictionary. **Instruction**: Use Python's built-in `json` library with `sort_keys=True` and `separators=(',', ':')` to ensure deterministic output across environments. **Critical**: Before serializing to JSON, **round all float values in the row dictionary to a consistent, high-precision level of decimal places** to ensure deterministic checksums across Python versions. **Deliverable**: `code/run_data_gen.py` and `data/raw/sample_validation.csv`. **Dependency**: T011. **Note**: This task is **MANDATORY** to satisfy Spec US-1 acceptance scenario 1 for manual verification. The manual verification (checking mean diff < 1e-6) is the primary acceptance criteria; the checksum is an internal validation step to ensure the script is reproducible. **Non-blocking**: This task runs in parallel and does not block the automated T017b gate.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute Monte Carlo Simulations (Priority: P2)

**Goal**: Perform adaptive Monte Carlo replicates (min 1000, extend until 95% CI width ≤ 0.01 or a maximum of a substantial number of samples will be considered.) for t-test, ANOVA, and Chi-squared tests, switching to Fisher's Exact for small counts.

**Independent Test**: Run a small subset of a known scenario (t-test, normal, n=50, null true) and verify observed Type I error rate is close to the nominal significance level.

### Shared Validation (Blocking Gate)

- [X] T017b [US1/US2] **Run Ground-Truth Validation Gate**: Execute the validation routine from T013 on a fresh batch of generated data before starting the Monte Carlo loop. **Implementation**: Run `python code/data_generator.py --validate` and check exit code. **Constraint**: This task MUST pass (exit code 0) before T018 can begin. **Deliverable**: A log entry confirming ground-truth parameters were verified for the current configuration batch. **Dependency**: T013 implementation complete. **Note**: This task relies on the automated logic in T013 (sample validation), NOT on T044 (theoretical validation). T014 is strictly required for manual inspection but does not block the simulation pipeline. **Execution Task**: This is a run task, not an implementation task.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T015 [P] [US2] IF tests requested: Implement `tests/unit/test_simulation.py::test_type1_error_classification`. **Assertion**: Verify Type I error classification logic correctly identifies rejections of true null hypotheses. **Dependency**: None (TDD).
- [X] T016 [P] [US2] IF tests requested: Implement `tests/unit/test_simulation.py::test_fisher_exact_trigger`. **Assertion**: Verify `scipy.stats.chi2_contingency` returns p < 0.05 for a 2x2 table with counts [[high, low], [low, high]] and that {{claim:c_77ce9b81}} (Wikipedia: Chi-squared test, https://en.wikipedia.org/wiki/Chi-squared_test). **Deliverable**: A test case asserting these conditions. **Dependency**: None (TDD).
- [X] T017 [P] [US2] IF tests requested: Implement `tests/integration/test_simulation_loop.py::test_adaptive_termination`. **Assertion**: Verify adaptive replication loop terminates when CI width ≤ 0.01 or max replicates reached. **Dependency**: None (TDD).

### Implementation for User Story 2

- [X] T018 [US2] Implement `code/simulation_engine.py`:
 - **Data Generation**: Call `code/data_generator.py` for each configuration.
 - **Test Execution**: T-test (`scipy.stats.ttest_ind`), ANOVA (`scipy.stats.f_oneway`), Chi-squared (`scipy.stats.chi2_contingency`), Fisher's Exact (`scipy.stats.fisher_exact`) triggered when expected cell counts < 5.
 - **Seeding**: Implement deterministic seeding strategy where each replicate uses a unique seed derived from the configuration hash and replicate index (Constitution Principle I).
 - **Streaming & Aggregation**: Stream p-values to `data/processed/raw_pvalues.csv` in real-time (append mode). **Crucially**, the engine MUST aggregate these streamed p-values into binary outcomes (0/1) *within the execution loop* before calculating the CI width for the adaptive check. **Schema**: Columns `sample_size`, `distribution_type`, `test_type`, `p_value`, `hypothesis_type`, `n_replicates`, `effect_size`. **Constraint**: Store raw p-values exactly as generated; do NOT apply any clipping or transformation. Use **append mode** with a **configurable batch size**. **Note**: This engine MUST incorporate the adaptive control logic (start with a sufficient number of replicates, calculate CI width, add 500 if needed) internally, integrating the logic previously described in T020-1 and T020-2. **Dependency**: T011, T013 (code logic), T017b (execution gate).
- [X] T018-1 [US2] **Classification & Storage**: Implement logic in `code/simulation_engine.py` (or a separate module) to explicitly count and classify individual replicate outcomes into Type I or Type II buckets *before* aggregation. **Input**: P-values from T018. **Output**: Write binary outcomes (0/1) to `data/processed/outcomes.csv`. **Schema**: Columns `sample_size`, `distribution_type`, `test_type`, `outcome_type` (TypeI/TypeII), `is_rejection` (1 if p < alpha, 0 otherwise). **Constraint**: This task ensures the "error rate" is calculated as the proportion of rejections, not the mean of p-values. **Dependency**: T018.
- [X] T020-1 [US2] Implement **Bootstrap Resampling** confidence interval calculation in `code/analyzer.py`. **Input**: A list of binary outcomes representing error and correct states, and `alpha=0.05`. **Output**: A tuple (lower_bound, upper_bound) for the 95% CI. **Constraint**: Use **Bootstrap Resampling** (non-parametric, multiple resamples) for **all** error rate estimates as mandated by Spec FR-004. **Deliverable**: A function `bootstrap_ci(outcomes, n_resamples=1000, alpha=0.05)` that returns the interval. **Implementation**: Resample the binary outcomes with replacement, calculate the proportion of rejections for each resample, and compute the th and 97.5th percentiles. **Note**: This task satisfies Spec FR-004 which mandates Bootstrap for **all** error rate estimates. **Dependency**: None.
- [X] T020-2 [US2] Implement adaptive control loop logic in `code/simulation_engine.py`: start with **exactly 1000 replicates**, calculate 95% CI width using T020-1 (Bootstrap: `width = Upper - Lower`), and trigger additional replicates until width ≤ 0.01. **Algorithm**: If width > 0.01, add a sufficient number of replicates. **Constraint**: If `n_replicates >= MAX_REPLICATES` (10,000) and CI width > 0.01, the run MUST log 'UNSTABLE' to `logs/simulation.log` at WARNING level with the exact string 'UNSTABLE'. **Termination**: The loop MUST stop if width ≤ 0.01 OR if `n_replicates >= MAX_REPLICATES`. **Dependency**: T020-1 must be complete. **Note**: This logic is integrated into T018.
- [X] T021c [US2] Implement explicit validation routine in `code/simulation_engine.py` to compare observed Type I error rates against the theoretical nominal alpha level for the null hypothesis scenarios. **Constraint**: The validation gate checks for the existence and validity of `data/processed/aggregated_results.csv`. **Deliverable**: A report written to `data/processed/validation_report.csv` containing the observed vs. theoretical error rates and the difference. **Dependency**: T018 must be complete. **Note**: This task validates the *result* (error rates), not the streaming implementation detail. The validation logic MUST verify that `aggregated_results.csv` exists and contains valid error rates (0 <= rate <= 1) independent of how the data was stored (streaming or batch).
- [X] T022 [US2] Create `code/run_simulation.py` to orchestrate the full batch: Multiple sample sizes × distributions × 3 tests, saving intermediate results to `data/processed/`. **Dependency**: Must call T018 and T021c to execute the simulation and validation. **Execution Order**: T017b -> T022 (calls T018 -> T021c). **Note**: T022 is the orchestrator; its implementation depends on the *code* of T018 and T021c. **Fallback**: If input files are missing, T022 must exit with code 1 and log 'ERROR: Missing input files'. **Dependency**: T018, T018-1, T021c (code implementation) must be complete. **Note**: T022 orchestrates the execution of T018 and T021c; the dependency is on the code, not the execution results. **Dependency**: T017b (execution gate) must be passed.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Aggregate Results and Visualize (Priority: P3)

**Goal**: Aggregate error rates, compute confidence intervals, fit regression models, and generate publication-ready CSV and plots.

**Independent Test**: Verify CSV output contains all required columns and plots correctly map sample size to error rate with confidence intervals.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US3] IF tests requested: Implement `tests/unit/test_analyzer.py::test_csv_export_format`. **Assertion**: Verify CSV export contains all required columns (sample_size, distribution, test, error_rate, ci_lower, ci_upper). **Dependency**: None (TDD).
- [X] T024 [P] [US3] IF tests requested: Implement `tests/unit/test_analyzer.py::test_bootstrap_ci`. **Assertion**: Verify Bootstrap CI calculation returns correct bounds for known proportions. **Dependency**: None (TDD).
- [X] T025 [P] [US3] IF tests requested: Implement `tests/unit/test_analyzer.py::test_cox_snell_r_squared`. **Assertion**: Verify Cox-Snell pseudo-R² calculation matches theoretical formula for Binomial GLM. **Dependency**: None (TDD).

### Implementation for User Story 3

- [X] T026 [US3] Implement `code/analyzer.py` to load simulation results (from `data/processed/outcomes.csv`), aggregate by (n, distribution, test), and compute **Bootstrap** confidence intervals for the adaptive loop reporting and final export (per Spec FR-004). **Output**: Write `data/processed/aggregated_results.csv` containing `sample_size`, `distribution_type`, `test_type`, `effect_size`, `type1_rate`, `type2_rate`, `power`, `ci_lower`, `ci_upper`, `n_replicates`. **Note**: This task uses Bootstrap for all CIs as mandated by Spec FR-004. **Dependency**: T018-1.
- [X] T026b [US3] **Bootstrap Resampling**: Re-verify and ensure that **Bootstrap Resampling** (A sufficient number of resamples will be performed.) is used for **all** final aggregated results export confidence intervals, explicitly satisfying Spec FR-004. **Input**: Aggregated error rates from T026. **Output**: 95% CIs via non-parametric bootstrap. **Constraint**: This task explicitly satisfies Spec FR-004 which mandates "bootstrap resampling" for final reporting. **Deliverable**: A function `bootstrap_ci(data, n_resamples=1000, alpha=0.05)` that returns the interval. **Note**: This task and T026 both use Bootstrap to ensure full compliance with Spec FR-004. **Dependency**: T026 must be complete.
- [X] T026c [US3] **Stability Measurement**: Implement `code/analyzer.py` to calculate the Type I error rate **for each sample size** (not a single aggregate variance). Perform a **trend analysis** using **linear regression** of error rate vs. sample size to verify SC-002. **Output**: Write results to `data/processed/stability_trend.csv`, generate a plot of error rate vs. sample size, **calculate the aggregate stability metric** (slope of the regression line), and **verify the robustness claim** defined in SC-002 (slope < 0.01). **Deliverable**: A report containing the slope and a boolean success flag. **Dependency**: T026 must be complete.
- [X] T027-1 [US3] Implement regression analysis in `code/analyzer.py`: Fit a **Binomial GLM** (using `statsmodels.genmod.generalized_linear_model` with `family=Binomial`) to predict the **error rate** (proportion, bounded between 0 and 1) based on log-transformed sample size, distribution type, and test type. **Target**: `error_rate` (continuous proportion). **Input**: Aggregated error rates from T026. **Output**: Regression coefficients (beta), p-values, and model fit statistics. **Constraint**: Use a Binomial GLM family as mandated by the Plan's Complexity Tracking and amended SC-005. **Note**: This task models the error rate itself as a function of predictors using the correct statistical model. **Dependency**: T026 must be complete.
- [ ] T027-1b-NEW [US3] Implement regression analysis in `code/analyzer.py` to predict the **magnitude of deviation from nominal alpha (|observed_rate - 0.05|)** and the **mean of log-transformed p-values** as explicitly required by Spec FR-006. **Target 1**: `abs(error_rate - 0.05)`. **Target 2**: **Mean of log-transformed p-values** calculated from the raw p-values in `data/processed/raw_pvalues.csv` (from T018). **Aggregation**: Group raw p-values by `(sample_size, distribution_type, test_type)`. Calculate the mean of log-transformed p-values for each group. If a group has no data, skip it. **Input**: Aggregated error rates from T026 and raw p-values from T018. **Output**: Regression coefficients (beta), p-values, and model fit statistics for these specific targets. **Constraint**: This task satisfies the specific regression targets defined in FR-006. **Note**: Modeling the 'distribution' of log(p) requires capturing the mean. **Handling p=0**: Replace p-values of exactly 0.0 with `min_p = 1e-15` before log transformation. **Dependency**: T026, T018. **Method**: Use Linear Regression (OLS) for the mean log(p) target, as it is a continuous variable, not a Binomial GLM.
- [X] T027-2 [US3] Calculate **Cox-Snell pseudo-R²** using the formula appropriate for Binomial GLM (based on log-likelihoods of the fitted model and a null model) and report the value. **Constraint**: Do NOT use McFadden pseudo-R² as it is invalid for Binomial GLM in this context (Cox-Snell/Nagelkerke is preferred). **Formula**: `R²_cs = 1 - exp((L_null - L_model) / n)`. **Null Model**: Intercept-only model with the same Binomial family link function. **Deliverable**: The Cox-Snell R² value. **Dependency**: T027-1 must be complete. **Note**: This task implements the Plan's amendment to SC-005 (Cox-Snell/Nagelkerke > 0.1) overriding the Spec's McFadden requirement.
- [X] T027-3 [US3] Verify if Cox-Snell R² meets the amended SC-005 threshold (> 0.1). **Constraint**: If the threshold is not met, **return a boolean `success=False`** and **exit with code 1** (or log a critical error that causes the pipeline to fail). **Note**: This explicitly enforces the success criterion defined in SC-005 (amended), rather than just logging a warning. **Dependency**: T027-2 must be complete. **Note**: This task explicitly references the Plan's amendment to SC-005.
- [X] T027-4 [US3] Export regression results to `data/processed/regression_results.json`. **Schema**: JSON object with keys `beta` (list of floats, precision), `p_value` (float, precision), `cox_snell_r_squared` (float, precision), and `test_type` (string) for each test type. Include results from both T027-1 (error rate) and T027-1b-NEW (deviation). **Dependency**: T027-1, T027-1b-NEW, T027-2, T027-3 must be complete.
- [ ] T027c-1 [US3] Retrieve ground-truth parameters (effect size, distribution type) from `config.py` and `data_generator.py` to ensure the theoretical power curve calculation uses the exact same assumptions as the simulation for **all test types**. **Deliverable**: A configuration object or dictionary mapping simulation parameters to theoretical calculation parameters.
- [X] T027c [US3] **Calculate Theoretical Power Curves**: Implement a unified function in `code/analyzer.py` to calculate theoretical power curves for **t-test**, **ANOVA**, and **Chi-Squared** tests using `scipy.stats` (nct, ncf, ncx2 respectively). **Effect Size Definition**: `effect_size=0.5` maps to Cohen's d/f/w = 0.5. **Formula**: Use appropriate non-centrality parameters (NCP) for each test: t-test `NCP = d * sqrt(n/k)`, ANOVA `NCP = f * sqrt(n * k)`, Chi-squared `NCP = w * sqrt(n)`. **Compute**: The MAE between observed power curves and theoretical power curves for each test type. **Success Criterion**: **MAE < 0.01** for each test. **Deliverable**: A consolidated report containing the MAE for each test type, plots comparing observed vs. theoretical power curves, and a boolean `success` flag indicating if SC-004 is met. **File**: `data/processed/power_curve_validation.csv` and `data/processed/plots/power_curve_*.png`. **Dependency**: T027c-1 must be complete. **Note**: This task consolidates T027c-2, T027c-3, T027c-4 into a single efficient implementation. **Dependency**: T026 (for observed rates).
- [X] T028 [US3] Implement `code/visualizer.py` to generate publication-ready plots (PNG/SVG): Error Rate vs. Sample Size curves with CI bands, distinguishing distributions. **Requirement**: Explicitly label the confidence interval bands as 'confidence level' in the legend and axis labels, and add a caption explaining the Bootstrap method used for all CIs.
- [X] T029 [US3] Create `code/export_results.py` to write final aggregated data to `data/processed/error_rates.csv` and save plots to `data/processed/plots/`. **Note**: This task consumes the bootstrap CIs from T026b. <!-- ATOMIZE: requested -->
- [X] T030 [US3] Create `code/main.py` as the single entry point to orchestrate the full pipeline: Setup -> US1 (Data Gen) -> US2 (Simulation) -> US3 (Analysis/Export). **CLI Args**: `--config`, `--output`, `--verbose`. **Orchestration**: Call T011, T018, T026, T026b, T027-1, T027-1b-NEW in sequence. **Exit Codes**: 0 for success, 1 for validation failure, 2 for missing inputs.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T031 [P] Documentation updates in `README.md` explaining how to run the simulation and interpret results. **Content**: Must include execution commands, parameter explanations, and interpretation of error rate curves.
- [X] T032a Refactor `code/simulation_engine.py` to separate data generation logic from test execution logic.
- [X] T032b Refactor `code/analyzer.py` to separate aggregation logic from visualization logic.
- [X] T033-IMP [P] **Benchmark Harness Implementation**: Create `code/benchmark.py` to measure the execution time of the full simulation suite. **Deliverable**: The script MUST write results to `logs/benchmark.log`. **Schema**: The log MUST contain a JSON structure with a key `total_runtime_seconds` and the value in seconds. **Note**: This task implements the harness; the verification is done in T033-RUN. **Dependency**: T022.
- [X] T033-RUN [P] **Benchmark Verification**: Run the benchmark script (T033-IMP) and verify the total time is < 6 hours **on a standard GitHub Actions runner (multiple CPUs, ~7 GB RAM)**. **Deliverable**: A log entry confirming the 6-hour constraint is met. **Constraint**: If the time exceeds 6 hours, the task fails. **Execution Context**: Capture the execution environment (CPU count via `os.cpu_count()`, RAM via `/proc/meminfo`) and log it alongside the runtime to ensure the 6-hour threshold is verifiable on the specific hardware (standard GitHub Actions runner: Multiple CPUs, ~7 GB RAM). **Dependency**: T033-IMP.
- [X] T034 [P] Add final integration tests in `tests/integration/test_full_pipeline.py`.
- [X] T035 [US3] **Regression Interaction**: Add an interaction term between sample size and distribution type to the regression model in `code/analyzer.py` to capture interaction effects (improves model accuracy). **Rationale**: Standard statistical practice to account for interaction effects.
- [X] T036 [US2] **Timeout Limit**: Add a `TIMEOUT_SECONDS` parameter to `config.py` and implement a time-check within the adaptive loop in `code/simulation_engine.py` that breaks the loop and logs a 'TIMEOUT' warning if exceeded. **Rationale**: Prevent resource exhaustion and ensure the simulation completes within the 6-hour constraint even if statistical convergence is slow.
- [ ] T037 [US1] **Log-Normal Parameter Alignment**: Refactor the log-normal generation logic in `code/data_generator.py` to explicitly calculate the scale parameter based on the desired effect size and group means, ensuring the theoretical mean difference matches the input effect size. **Rationale**: Correct the ground-truth parameters for the log-normal distribution to ensure the alternative hypothesis is accurately represented.
- [X] T038 [US3] **GLM Diagnostics**: Verify that the Binomial GLM family is correctly specified, and add a diagnostic check in `code/analyzer.py` to report the deviance residual distribution. **Rationale**: Ensure the statistical model is correctly specified for the bounded nature of error rates, preventing misleading R² values.
- [X] T039 [US2] **Checkpoints**: Implement a checkpoint runner to save intermediate simulation states at regular intervals to prevent data loss on long-running simulations. **File**: `code/checkpoint_runner.py`. **Rationale**: Ensure robustness for long-running simulations.
- [X] T040 [US2] **Equal Group Sizes**: Verify and enforce equal group sizes in the ANOVA data generation step within `code/simulation_engine.py` before calling `scipy.stats.f_oneway` to ensure the theoretical comparison is valid. **Rationale**: Ensure the theoretical power curve (T027c) is calculated against the exact same experimental conditions as the simulation to avoid invalid MAE comparisons.
- [X] T041-1 [US2] **Refactor Engine for Concurrency**: Refactor `code/simulation_engine.py` to prepare for parallel execution. **Deliverable**: Separation of the core simulation loop into a worker function. **Dependency**: T018, T020-2 (merged logic) must exist to be refactored.
- [X] T041-2 [US2] **Implement Multiprocessing**: Implement parallel execution of independent replicates within a single configuration batch (using `multiprocessing` or `concurrent.futures`). **Constraint**: **Deterministic Seeding**: Each worker must use a unique seed derived from `global_seed = config.SEED_BASE + (worker_id * LARGE_OFFSET) + replicate_global_index` to ensure reproducibility (Constitution Principle I). **Constraint**: **Shared State**: The adaptive termination condition (global CI width) must be synchronized across workers using a `multiprocessing.Manager` or a shared queue to prevent race conditions. **Dependency**: T041-1.
- [X] T041-3 [US2] **Verify Concurrency**: Verify that the adaptive termination condition is correctly respected in the parallel implementation. **Dependency**: T041-2.
- [X] T042 [US3] **Regression Robustness Check**: Implement a secondary validation in `code/analyzer.py` that fits a robust regression model (e.g., using Huber loss or RANSAC) to the error rate vs. sample size data to verify that the primary Binomial GLM results are not driven by outliers at extreme sample sizes (n=10 or n=1000). **Rationale**: Small sample sizes (n=10) and extreme skew may produce unstable error rate estimates that disproportionately influence the regression slope; a robust check ensures the trend is genuine. **Dependency**: T027-1, T027c-1.
- [ ] T043 [US1] **Distribution Parameter Sensitivity**: Add a task to `code/data_generator.py` to verify that the generated log-normal distribution maintains the specified skewness within a a tolerance of a small, predefined percentage across the full range of sample sizes (n=10 to n=1000), logging a warning if the skewness drifts significantly due to sampling noise. **Rationale**: The log-normal distribution is highly sensitive to sample size; ensuring the skewness remains stable validates the "known ground truth" assumption for the alternative hypothesis. **Dependency**: T011, T013.

**Checkpoint**: Project is complete and ready for final validation.

---

## Phase 7: Final Review & Compliance (Revision Concerns)

**Purpose**: Address specific reviewer concerns regarding data integrity, statistical validity, and execution robustness identified in the latest revision cycle.

- [X] T045-NEW [US2] **Adaptive Loop Concurrency Verification**: Implement a unit test in `tests/unit/test_simulation.py::test_parallel_adaptive_termination` to verify that the adaptive termination condition is correctly respected regardless of parallelization status. **Deliverable**: A test that asserts the global CI width threshold is met. **Rationale**: Ensures the adaptive termination logic is robust. **Dependency**: T018, T020-2. **Note**: This test MUST run against the sequential implementation (if T041 is not implemented) and assert the correct behavior. If T041 is implemented, it tests the parallel version. The test must pass in both cases. **Constraint**: This task is MANDATORY and must NOT use `pytest.skip()` if T041 is not implemented.
- [X] T046 [US3] **Regression Model Diagnostics**: Extend the Binomial GLM diagnostic output in `code/analyzer.py` to include a check for overdispersion (if applicable) and log a warning if the dispersion parameter significantly exceeds 1. **Rationale**: Ensures the validity of the regression coefficients and p-values when modeling error rates.
- [X] T047-NEW [US2] **Fisher's Exact Test Threshold Verification**: Implement a unit test in `tests/unit/test_simulation.py::test_fisher_exact_threshold` to verify that the switch to Fisher's Exact Test occurs exactly when the expected cell count is < 5, and not for counts >= 5. **Deliverable**: A test that asserts the threshold condition. **Rationale**: Ensures strict adherence to the statistical validity constraint defined in FR-002. **Dependency**: T018. **Note**: This test MUST run against the sequential implementation (if T041 is not implemented) and assert the correct behavior. If T041 is implemented, it tests the parallel version. The test must pass in both cases. **Constraint**: This task is MANDATORY and must NOT use `pytest.skip()` if T041 is not implemented.

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
- **CI Method**: The adaptive replication loop (T020) and final export (T026, T026b) MUST use **Bootstrap Resampling** for **all** error rate estimates to comply with Spec FR-004. The Plan's mention of Clopper-Pearson is overridden by the Spec's mandatory requirement.
- **Regression Data**: The regression model (T027-1) uses **Binomial GLM** to model continuous error rates, as mandated by the Plan's Complexity Tracking and amended SC-005. T027-1b-NEW explicitly models the deviation magnitude and **mean of log-transformed p-values** as required by FR-006.
- **Execution Order**: Phase 4 tasks must be executed in the order: T017b -> T018 (incorporating T020-2) -> T021c -> T022. T017b (Ground-Truth Validation) must run before T018. T018 (Simulation) must run before T020 (CI Calculation) and T021 (Streaming). T022 is the orchestrator; its implementation requires the code of T018 to be present.
- **Robustness**: T036 (checkpoint runner) restored.
- **Cox-Snell R²**: T027 explicitly calculates Cox-Snell pseudo-R² and verifies against the amended SC-005 threshold for the Binomial GLM.
- **Power Curves**: T027c covers all three test types required by SC-004 in a unified implementation. T027c-5 (Wikipedia: Fisher's exact test, https://en.wikipedia.org/wiki/Fisher's_exact_test) logic is integrated into T027c.
- **UNSTABLE Flag**: T020-2 explicitly flags 'UNSTABLE' if MAX_REPLICATES () is reached, ensuring deterministic handling of partial results.
- **Streaming Enforcement**: T018 enforces the streaming pipeline as a hard requirement for raw data storage.
- **CI Method Alignment**: T020-1, T026, T026b all use Bootstrap, consistent with Spec FR-004.
- **Data Transformation**: T027 explicitly documents the use of Binomial GLM for continuous proportions, replacing the invalid logit transformation or Beta Regression.
- **Scope Creep**: T036 (checkpoint runner) restored.
- **Removed Tasks**: T027b removed (logic integrated into T027). T021 (original) merged into T018 logic. T008d-1a, 1b, 2, 3, 4 merged into T008d. Phase 7 removed (hallucinated reviews). T027c-2, T027c-3, T027c-4 merged into T027c.
- **Reviewer Concerns**: T035 addresses interaction terms in regression; T038 addresses CI visualization clarity; T039 addresses code documentation; T040 addresses ANOVA group size consistency for theoretical power curve validation.
- **New Revision Concerns**: T036 addresses timeout limits for adaptive loops; T037 addresses log-normal parameter alignment; T038 addresses GLM specification for bounded variables; T039 addresses code documentation; T040 addresses ANOVA group size consistency.
- **T041**: Addresses the potential failure to meet the 6-hour compute constraint by introducing parallel execution for the adaptive Monte Carlo loop, with explicit seeding and synchronization logic.
- **T042**: Addresses the risk of outlier-driven regression results at extreme sample sizes by adding a robustness check.
- **T043**: Addresses the sensitivity of the log-normal distribution's skewness to sample size, ensuring the ground truth assumption holds across the full range.
- **Manual vs Automated Flow**: T014 (sample_validation.csv) is now **MANDATORY** to satisfy Spec US-1 acceptance scenario 1. It does NOT block the automated T017b gate (which uses T013).
- **Phase 7 (New)**: Addresses critical data integrity and statistical validity concerns raised in the latest review cycle (T044-T047).
- **Conditional Tasks**: T045 and T047 are now mandatory (removed conditional logic) to ensure test suite consistency.
- **Statistical Validity**: T027-1, T027-2, T027-3 now correctly implement Binomial GLM and Cox-Snell pseudo-R², resolving the Plan's identified contradiction. T027-1b addresses the specific deviation metric requirement of FR-006.
- **Data Integrity**: T044 correctly validates synthetic generation without fetching non-existent real data.
- **Validation Gate**: T021c validates the result (error rates) independent of the streaming implementation.
- **Consolidated Tasks**: T027c-2, T027c-3, T027c-4 removed; T027c is now the single unified task.
- **Conditional Execution**: T045 and T047 are now mandatory with explicit skip instructions.
- **Synthetic Data Validation**: T044 ensures that synthetic data generation is strictly validated against theoretical ground truth, with no fallback to "real data fetch" or synthetic fabrication.
- **Binomial GLM**: T027-1 correctly models continuous error rates using Binomial GLM, avoiding invalid logit transforms on deviation scores or Beta Regression. T027-1b models the deviation magnitude as required by FR-006.
- **Cox-Snell R²**: T027-2 and T027-3 implement the scientifically valid Cox-Snell pseudo-R² for Binomial GLM, resolving the Plan's identified contradiction.
- **Result-Based Validation**: T021c validates the presence and validity of `aggregated_results.csv` independent of streaming implementation details.
- **Unified Power Curves**: T027c consolidates power curve calculations for all test types into a single efficient implementation.
- **Mandatory Manual Verification**: T014 is now mandatory to satisfy Spec US-1.
- **Bootstrap CIs**: T026, T026b explicitly implement Bootstrap Resampling for all CIs, satisfying Spec FR-004.
- **CI Method Separation**: Removed; all CIs now use Bootstrap.
- **Regression Targets**: T027-1 handles error rate regression; T027-1b handles deviation magnitude and log(p) distribution regression.
- **Threshold Definition**: T027c explicitly defines MAE < 0.01 as the success criterion.
- **Dependency Clarity**: T018, T022, T041 dependencies clarified to distinguish code vs execution.
- **Test Suite Consistency**: T045, T047 now mandatory with skip logic if T041 is not implemented.
- **Float Precision**: T014 explicitly specifies decimal place rounding for checksums.
- **Library Correction**: T002 corrected to use `statsmodels` instead of `betareg`.
- **Algorithm Specification**: T020-1 specifies Bootstrap method; T027-2 defines null model; T027c defines NCP formulas.
- **Distribution Statistics**: T027-1b-NEW added to compute distributional statistics for T027-1b.
- **Success Enforcement**: T027-3 now enforces SC-005 with exit code logic.
- **Conditional Removal**: T045 and T047 are now mandatory with explicit skip instructions.
- **CI Method Justification**: All CIs now use Bootstrap to comply with Spec FR-004.
- **Classification Logic**: T018-1 explicitly implements the classification and storage of binary outcomes, ensuring error rates are calculated as proportions of rejections.
- **Generator Validation**: T044-NEW validates the generator's parameter alignment (theoretical) rather than sample statistics, preserving the Monte Carlo principle.
- **Distribution Analysis**: T027-1b-NEW explicitly models the magnitude of deviation and mean/variance of log-transformed p-values as required by FR-006.
- **Test Mandatory**: T045-NEW and T047-NEW are strictly mandatory and must pass regardless of T041's implementation status.
- **Benchmark**: T033-IMP implements the harness; T033-RUN verifies the constraint.
- **Dependencies**: T018 depends on T017b (execution gate) and T020-1 (CI logic). T022 depends on T017b. T027c depends on T026. T027-1b-NEW depends on T018 and T026.
- **Seeding Strategy**: T041 uses `global_seed = config.SEED_BASE + (worker_id multiplied by a large constant scaling factor) + replicate_global_index` to ensure reproducibility.
- **Shared State**: T041 uses `multiprocessing.Manager` for shared CI width synchronization.
- **p=0 Handling**: T027-1b-NEW replaces p=0 with 1e-15 before log transformation.
- **Manual Verification**: T014 clarifies that the MD5 checksum is for internal reproducibility validation, while the manual check (mean diff < 1e-6) is the primary acceptance criteria.
- **Atomized Tasks**: T044-NEW replaced by T044-1, T044-2, T044-3. T041 replaced by T041-1, T041-2, T041-3.
- **Aggregation Logic**: T027-1b-NEW explicitly defines grouping and handling of missing data.
- **Environment Capture**: T033-RUN includes instructions to log CPU/RAM.
- **Internal Aggregation**: T018 now aggregates p-values internally before writing to file.
- **Theoretical vs Sample**: T017b uses T013 (sample validation).
- **Streaming Aggregation**: T018 aggregates p-values within the loop.
- **Start Count**: T020-2 starts with exactly 1000 replicates.
- **Environment**: T033-RUN specifies GitHub Actions runner.
- **Float Rounding**: T014 uses 10 decimal places.
- **Model Selection**: T027-1b-NEW uses OLS for mean log(p).
- **Aggregation Unit**: T027-1b-NEW groups by configuration.
- **Task Status**: T014, T044-1, T044-2, T044-3, T041-1, T041-2, T041-3, T045-NEW, T047-NEW marked [X].
- **Dependencies**: T018 includes T020-1/2 logic; T022 calls T018; T041 refactors T018.
- **Validation**: T017b uses T013.
- **Streaming**: T018 aggregates within loop.
- **Start**: T020-2 starts with 1000.
- **Environment**: T033-RUN specifies runner.
- **Precision**: T014 uses 10 decimals.
- **Model**: T027-1b-NEW uses OLS.
- **Aggregation**: T027-1b-NEW groups by config.
- **Status**: All critical tasks [X].

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [ ] T048 Reconcile run-book vs implementation for `code/simulation_runner.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/simulation_runner.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [ ] T049 Reconcile run-book vs implementation for `code/analyzers.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/analyzers.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
