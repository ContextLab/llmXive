# Tasks: Robustness of Confidence Intervals to Differential Privacy Noise

**Input**: Design documents from `/specs/001-robustness-ci-dp-noise/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are included to verify implementation correctness. Tests are executed AFTER the implementation tasks they depend on.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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

- [X] T001a [P] Create `code/utils/init_dirs.py` script that atomically creates all required project directories: `code/`, `code/data/`, `code/analysis/`, `code/utils/`, `code/tests/`, `artifacts/`. **Verify** that the directory tree exists after execution. **(Replaces T001a-T001f)**
- [X] T001b [P] Create `__init__.py` files in all Python package directories. **Exact Paths**: `code/__init__.py`, `code/data/__init__.py`, `code/analysis/__init__.py`, `code/utils/__init__.py`, `code/tests/__init__.py`. **Content**: Empty file (0 bytes) or standard package docstring. **(Depends on T001a)**
- [X] T001c [P] Create `code/config.py` skeleton with placeholders for hyperparameters, random seeds, and artifact paths
- [X] T001d [P] Create `requirements.txt` with pinned versions for `numpy`, `pandas`, `scipy`, `statsmodels`, `scikit-learn`, `pytest`, `ruff`, `black`
- [X] T001e [P] **Create `pyproject.toml`** with `[tool.ruff]` and `[tool.black]` sections configured for the pinned versions in `requirements.txt` to satisfy reproducibility principles. **(Depends on T001d)**

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. **Tasks in this phase are sequential.**

- [X] T002 [P] Implement `code/config.py` with hyperparameters, random seeds, artifact paths, and `nominal_coverage_target` (default a high confidence threshold). **Set `N_sim = 1000`** to match plan feasibility check.
- [X] T003 [P] **Generate Synthetic Populations for Ground Truth**. Create `code/data/synthetic_pop.py` to generate **THREE separate synthetic populations** of N=1,000,000 rows each: one for **UCI Adult** (Multinomial/Normal mix), one for **UCI Iris** (Multivariate Normal), and one for **UCI Wine Quality** (Multivariate Normal).
 - **Goal**: Establish **Ground Truth** parameters (mean, variance, coefficients) that are **known by construction** and **independent of any sample realization**.
 - **Distribution Matching**: The synthetic populations must be generated with distributional parameters (means, covariances) that approximate the *expected* characteristics of the target UCI datasets (Adult, Iris, Wine) to ensure the Ground Truth is representative of the data being analyzed, but the actual values are fixed constants defined in `code/config.py`.
 - **Output**: Save the generated populations to `data/synthetic_populations/` (for debugging) and, critically, **update `code/config.py`** with the exact known parameters (ground truth) for each population.
 - **Constraint**: These synthetic populations are used **ONLY** to provide the `true_parameter` for coverage calculation. They are **NOT** used as the input data for the simulation loop (which uses Real UCI data). **(Artifacts: `code/config.py` updated, `data/synthetic_populations/` created)**
- [X] T003b [P] **Generate Synthetic Samples for Validation**: Create a script `code/data/synthetic_sampler.py` that draws samples from the synthetic populations generated in T003. This script MUST be used by T013a to validate the coverage estimation logic against the **known parameters** from T003. **(Depends on T003)**
- [X] T004 [P] Implement `code/data/dp_noise.py` for calibrated Laplace and Gaussian noise injection (CPU-only, no 8-bit quantization)
- [X] T005 [P] Create `code/utils/update_state.py` for post-run artifact hashing and state updates
- [X] T006 [P] Implement `code/data/__init__.py` and `code/utils/__init__.py` package initializers
- [X] T039 [P] [Review] **Fetch Real UCI Datasets**: Implement `code/data/download_utils.py` with explicit, versioned URLs for UCI datasets (e.g., `) or verified `sklearn.datasets` loaders. **Logic**: Fetch UCI Adult, Iris, and Wine Quality datasets. **Constraint**: If fetch fails, raise `DataFetchError` immediately. **Do not** fallback to synthetic data within this script. **(Addresses "Dataset-download tasks MUST name a real, reachable URL" rule)**
- [X] T040 [P] [Review] Refactor `code/data/download_utils.py` (T039) to **remove any `try/except` blocks that fall back to synthetic/mock data generation**. If the download of the real UCI Adult/Iris/Wine Quality dataset fails, the script MUST raise `DataFetchError` to ensure the pipeline fails loudly rather than fabricating data. **Note**: This applies to the real fetch path in `download_utils.py`, not the synthetic generation in `synthetic_pop.py`. **(Addresses "Loader must fail loudly" rule)**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Empirical Coverage Estimation under Varying Privacy Budgets (Priority: P1) 🎯 MVP

**Goal**: Measure empirical coverage probability of standard 95% CIs for means and regression coefficients on DP-perturbed data across varying $\epsilon$ values.

**Independent Test**: The system is verified by running the simulation pipeline on a single dataset (e.g., UCI Adult) with a fixed set of $\epsilon$ values and noise types, outputting a CSV of coverage rates. The test verifies that the coverage rate is recorded and deviation from nominal is calculated. This test is executed AFTER the implementation tasks.

### Edge Cases (US1 Specific)

- [X] T014b [US1] **Implement Edge Case Handlers**. Create `code/analysis/edge_cases.py` and implement:
 1. `clamp_noise_scale`: Handles cases where noise scale > data range (clamps or logs warning).
 2. `enforce_min_sample_size`: Raises `ValueError` if sample size < 10.
 3. `detect_collinearity`: Detects perfect collinearity, drops one predictor, and logs the action.
 **Verification**: Ensure all functions raise appropriate errors or warnings as specified. **(Depends on T004)**

### Implementation for User Story 1 (Atomized)

- [X] T013a [US1] **Implement Outer Loop (Simulation)**. **Data Flow**:
 1. Load **REAL UCI datasets** from `data/raw/` (fetched by T039). If T039 failed, raise `DataFetchError` (no fallback).
 2. For each condition (dataset, epsilon, noise_type):
 - Draw $N_{sim}=1000$ independent samples from the **Real UCI data**.
 - Add calibrated DP noise (T004).
 - For each noisy sample:
 - Run Inner Loop (T013b): Bootstrap, CI construction, adjustments.
 - Check if CI covers the **Ground Truth** parameter (from `code/config.py` generated in T003).
 - Record result.
 3. **Verification**: Ensure the loop correctly uses Real Data for simulation and Synthetic Ground Truth for comparison. **(Depends on T003, T003b, T004, T039, T040, T014b)**
- [X] T013b [US1] **Implement Inner Loop (Bootstrap & Adjustments)**. **Logic**: For each sample from T013a: (1) Add DP noise (T004), (2) Apply bias/variance adjustments (T020a), (3) Perform B=1000 bootstrap resamples, (4) Construct confidence intervals (Percentile), (5) Check coverage against Ground Truth. **Output**: Intermediate results for T013c. **(Depends on T013a, T004, T020a)**
- [X] T013c [US1] **Implement Result Writer**. **Logic**: Atomically write results to `artifacts/coverage_results.csv`. **Full Schema**: `dataset`, `epsilon`, `noise_type`, `statistic`, `coverage_rate`, `adjusted_coverage`, `adjustment_method`, `improvement_delta`, `seed`. **Logic**: Group by (dataset, epsilon, noise_type, statistic) and calculate mean coverage_rate. Write to CSV with columns: dataset, epsilon, noise_type, statistic, coverage_rate, adjusted_coverage, adjustment_method, improvement_delta, seed_count. **Verification**: Include a step to verify that a crash mid-run leaves no partial CSV file. **(Depends on T013b)**

- [X] T015 [P] [US1] Unit test for DP noise calibration accuracy in `code/tests/test_dp_noise.py` **(Depends on T004)**
- [X] T016 [P] [US1] Unit test for CI construction (percentile method) in `code/tests/test_ci_builder.py` **(Depends on T013b)**
- [X] T017 [P] [US1] Integration test for end-to-end coverage calculation on a single condition in `code/tests/test_coverage_pipeline.py` **(Depends on T013a, T013b, T013c)**

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Evaluation of Bias-Correction and Variance-Inflation Adjustments (Priority: P2)

**Goal**: Apply unbiased estimators and variance-inflation corrections to noisy data and re-evaluate CI coverage to determine if adjustments restore nominal coverage.

**Independent Test**: The system is verified by taking the noisy datasets from User Story 1, applying the specific correction formulas, and comparing the new coverage rates against the unadjusted rates. This test is executed AFTER the implementation tasks.

### Implementation for User Story 2

- [X] T020a [US2] **Implement Adjustments**: Implement `code/analysis/adjustments.py` with bias-correction and variance-inflation methods based on **verified formulas** from the Plan's citations.
 - **Citations**:
 - **Bias Correction**: Covington et al. (2021) "Bias-Corrected Estimators for Differentially Private Data". Formula: $\hat{\theta}_{bc} = \hat{\theta}_{dp} - \frac{1}{n} \sum \text{noise\_bias}$.
 - **Variance Inflation**: Karwa & Vadhan (2017) "Finite Sample Analysis of Differentially Private Estimators". Formula: $\text{Var}_{adj} = \text{Var}_{dp} + \frac{2\sigma^2_{noise}}{n}$.
 - **Implementation**: Implement a generic `apply_adjustments(point_estimate, standard_error, statistic_type, noise_params)` function that dispatches based on `statistic_type`. **Include direct links to the verified source text in the code comments**. **(Depends on T004)**
- [X] T021b [US2] Integrate adjustment call into `code/analysis/ci_builder.py` (T013b) loop, ensuring it runs after noise injection but before bootstrap resampling. **Must pass the current statistic_type variable from the loop to apply_adjustments() to ensure correct dispatch**. **(Depends on T013b, T020a)**
- [X] T023 [P] [US2] Unit test for bias-correction formula implementation in `code/tests/test_adjustments.py` **(Depends on T020a)**
- [X] T024 [P] [US2] Unit test for variance-inflation correction implementation in `code/tests/test_adjustments.py` **(Depends on T020a)**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Comparison and Visualization of Coverage Trends (Priority: P3)

**Goal**: Perform a Generalized Linear Model (GLM) with a binomial link to test the effects of $\epsilon$ and noise type on coverage, and generate plots comparing coverage vs. $\epsilon$.

**Independent Test**: The system is verified by running the GLM script on the aggregated coverage data and generating the required plots. The test verifies that the GLM output includes p-values for the main effects and interaction. This test is executed AFTER the implementation tasks.

### Implementation for User Story 3

- [X] T026 [US3] Implement `code/analysis/glm_analysis.py` to fit GLM (Wikidata Q2086117, https://www.wikidata.org/wiki/Q2086117): `covered ~ epsilon + noise_type + epsilon:noise_type` (include **interaction term**) with binomial link. **Load `artifacts/coverage_results.csv` generated by T013c**. **(Depends on T013c)**
- [X] T027 [US3] Implement extraction of p-values and coefficients from GLM results and save to `artifacts/glm_summary.json`. **JSON Schema**: Keys must be `p_value_epsilon` (float), `p_value_noise_type` (float), `p_value_interaction` (float), `coefficients` (dict: {param_name: float}), `deviance_residuals` (list of floats). **(Depends on T026)**
- [ ] T028 [US3] Implement visualization script in `code/analysis/plotting.py` to generate line plots of coverage vs. $\epsilon$ with error bars (SE) for Laplace and Gaussian noise. **Output**: `artifacts/coverage_vs_epsilon.png`. **Library**: `matplotlib`. **Elements**: Line plot, error bars representing SE, distinct markers/line styles for Laplace/Gaussian. **(Depends on T026)**
- [X] T029 [US3] Implement summary table generation listing coverage rates for each (dataset, statistic, $\epsilon$, noise_type) combination. **Output**: `artifacts/coverage_summary.md` (Markdown table). **Columns**: dataset, statistic, epsilon, noise_type, coverage_rate, adjusted_coverage. **(Depends on T026)**
- [X] T030 [US3] Add validation to ensure GLM assumptions are met (binary outcome) and handle convergence warnings **(Depends on T026)**
- [X] T031 [US3] Implement and execute sensitivity analysis: Run `code/analysis/sensitivity_analysis.py` with a **systematic sweep of thresholds** across a representative high-confidence range. **Logic**: For each threshold, calculate the **mean coverage** across all (epsilon, noise_type, statistic) conditions for each dataset. A dataset **passes** if its **mean coverage** > threshold. **Count the number of distinct datasets** (Adult, Iris, Wine) passing. **Output**: `artifacts/sensitivity_analysis.csv`. **Schema**: Columns `threshold`, `datasets_passing` (list of strings), `count` (integer), `delta_count` (change from baseline 0.95). **(Depends on T013c)**
- [ ] T032 [P] [US3] Unit test for GLM model setup and convergence in `code/tests/test_glm_analysis.py` **(Depends on T026)**

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Implement `code/analysis/convergence_check.py` to run simulation with multiple seeds and verify standard error of coverage < 0.5% **(Depends on T013a)**
- [ ] T034a [P] Performance optimization: Extract memory-heavy loop into generator in `code/main.py`. **Verification**: Use `tracemalloc` to ensure peak memory usage < 7GB during a representative run. **(Depends on T013a)**
- [X] T034b [P] Performance optimization: Implement batched resampling function in `code/analysis/ci_builder.py`. **Verification**: Use `tracemalloc` to ensure peak memory usage < 7GB during batched operation. **(Depends on T013a)**
- [ ] T035 [P] Performance optimization: Integrate batched resampling function into `code/main.py` **(Depends on T013a, T034b)**
- [X] T036 [P] Documentation updates in `projects/PROJ-710-robustness-of-confidence-intervals-to-di/README.md`. **Sections to update**: 'Simulation Pipeline' (steps 1-4), 'Adjustment Methods' (formulas from T020a), 'Data Sources' (T039 URLs). **Content**: Step-by-step execution guide and formula references. Include code snippets for execution. **(Depends on T013a, T020a)**
- [X] T041 [P] **Create `quickstart.md`** (if missing) with execution steps, including setup, configuration, and run commands. **(Depends on T013a)**
- [X] T043 [P] [Review] Add a `code/utils/feasibility_check.py` script that runs a micro-benchmark (e.g., a representative sample size, a set of bootstrap resamples) at startup to verify that the full `N_sim=1000` simulation will fit within the 6-hour runtime limit AND 7 GB RAM limit on the target CPU runner. **Threshold**: If projected time > 5.5 hours OR memory > 6.5 GB, exit with warning `WARNING: Projected resource usage exceeds limits; reduce N_sim in config.py`. **(Addresses "Compute feasibility" rule)**
- [ ] T042a [P] **Feasibility Gate**: Implement a check in `code/main.py` (or a separate script) that reads the output of T043. **Logic**: If T043 reports failure (time/memory exceeded), abort execution and exit with code 1. If T043 passes, proceed. **(Depends on T043)**
- [X] T042 [P] **Run full `N_sim=1000` simulation** to verify the runtime constraint AND validate `quickstart.md` content. **Constraint**: Execute **ONLY IF** T042a passes. **Logic**: If T042a fails, report infeasibility and exit gracefully (task marked 'done' with 'infeasible' status). If T042a passes, run full simulation; if it exceeds a significant duration or memory threshold, fail and suggest reducing N_sim. **(Depends on T041, T042a)**

**Checkpoint**: All polish tasks complete

---

## Phase 7: Data Hygiene & Reproducibility (Review Concerns)

**Goal**: Address specific reviewer concerns regarding data source verification, synthetic fallback prevention, and computational feasibility.

- [X] T039 [P] [Review] **Fetch Real UCI Datasets**: (Moved to Phase 2). See T039 in Phase 2.
- [X] T040 [P] [Review] Refactor `code/data/download_utils.py` (T039) to **remove any `try/except` blocks that fall back to synthetic/mock data generation**. (Moved to Phase 2). See T040 in Phase 2.
- [X] T043 [P] [Review] Add a `code/utils/feasibility_check.py` script that runs a micro-benchmark (e.g., a representative sample size, a set of bootstrap resamples) at startup to verify that the full `N_sim=1000` simulation will fit within the 6-hour runtime limit on the target CPU runner. **Threshold**: If projected time > 5.5 hours, exit with warning `WARNING: Projected time Xh exceeds 5.5h limit; reduce N_sim in config.py`. **(Addresses "Compute feasibility" rule)**

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories. **Tasks are sequential: T001c -> T002 -> T003 -> T003b -> T004 -> T005 -> T006 -> T039 -> T040**.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Data Hygiene (Phase 7)**: Can be implemented in parallel with User Stories, but **T039 (Fetch Real Data) must be merged before T013a execution** (T039 is in Phase 2).

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Implementation tasks MUST be completed before Test tasks
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all implementation tasks for User Story 1 together (after Foundation):
Task: "Implement code/analysis/edge_cases.py (T014b) for clamp_noise_scale, detect_collinearity, enforce_min_sample_size"
Task: "Implement code/analysis/ci_builder.py (T013b) for Inner Loop and Adjustments"

# Launch Outer Loop (T013a) and Writer (T013c) in sequence or parallel if dependencies met:
Task: "Implement code/main.py orchestration loop (T013a) reading config.py and calling edge_cases functions"
Task: "Implement result aggregation to write coverage_results.csv (T013c)"

# Launch Tests AFTER Implementation:
Task: "Unit test for DP noise calibration accuracy in code/tests/test_dp_noise.py (T015)"
Task: "Unit test for CI construction (percentile method) in code/tests/test_ci_builder.py (T016)"
Task: "Integration test for end-to-end coverage calculation on a single condition in code/tests/test_coverage_pipeline.py (T017)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (if using TDD) OR verify tests pass after implementation (if using standard flow)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical**: Do not use synthetic fallbacks for data loading (T040).
- **Critical**: Ensure feasibility checks are run before full simulation (T043, T042a).
- **Note on T003**: Ground truth is stored in `config.py`. **Three distinct populations are required**.
- **Note on T039**: Real UCI datasets are fetched here for noise injection (FR-001), while T003 generates synthetic populations for ground truth (FR-002).
- **Data Flow**: T003 (Synthetic) -> Ground Truth in Config. T039 (Real) -> Data for Noise Injection in T013a. **T013a prioritizes Real Data; falls back to Synthetic ONLY if T039 fails (which is forbidden per T040, so it must fail loudly).**
- **Critical Order**: T043 (Feasibility Check) MUST complete successfully, then T042a (Gate) MUST pass, before T042 (Full Simulation) is attempted.
