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

- [X] T001a [P] Create `code/utils/init_dirs.py` script that atomically creates all required project directories: `code/`, `code/data/`, `code/analysis/`, `code/utils/`, `code/tests/`, `artifacts/`. **(Replaces T001a-T001f)**
- [ ] T001b [P] Create `__init__.py` files in all Python package directories (`code/`, `code/data/`, `code/analysis/`, `code/utils/`, `code/tests/`) **(Depends on T001a)**
- [X] T001c [P] Create `code/config.py` skeleton with placeholders for hyperparameters, random seeds, and artifact paths
- [X] T001d [P] Create `requirements.txt` with pinned versions for `numpy`, `pandas`, `scipy`, `statsmodels`, `scikit-learn`, `pytest`, `ruff`, `black`
- [ ] T001e [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 [P] Implement `code/config.py` with hyperparameters, random seeds, artifact paths, and `nominal_coverage_target` (default a high confidence threshold). **Set `N_sim = 1000`** to match plan feasibility check.
- [ ] T003 [P] Implement `code/data/synthetic_pop.py` to generate N=1,000,000 synthetic populations for **UCI Adult**, **UCI Iris**, and **UCI Wine Quality** distributions. The generation MUST create a population with **known parameters** (mean, variance, coefficients) to serve as ground truth. **Output to `code/data/ground_truth.json`** containing these known parameters for each population. **Note**: This task generates data from scratch; no real dataset fetch is required for the population itself. If real datasets are used for validation, they must be fetched separately and the fetch must fail loudly (see T038). **(Artifacts: `code/data/ground_truth.json`)**
- [X] T004 [P] Implement `code/data/dp_noise.py` for calibrated Laplace and Gaussian noise injection (CPU-only, no 8-bit quantization)
- [X] T005 [P] Create `code/utils/update_state.py` for post-run artifact hashing and state updates
- [X] T006 [P] Implement `code/data/__init__.py` and `code/utils/__init__.py` package initializers
- [X] T014a [P] [US1] Implement `code/analysis/edge_cases.py` function `clamp_noise_scale` to handle cases where noise scale exceeds data range (small $\epsilon$). **(Creates module for T013a)**
- [ ] T014b [P] [US1] Implement `code/analysis/edge_cases.py` function `detect_collinearity` to handle collinear predictors in regression, dropping one and logging the action. **(Creates module for T013a)**
- [ ] T014c [P] [US1] Implement `code/analysis/edge_cases.py` function `enforce_min_sample_size` to enforce minimum sample size for valid bootstrap (n < 10 check). **(Creates module for T013a)**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Empirical Coverage Estimation under Varying Privacy Budgets (Priority: P1) 🎯 MVP

**Goal**: Measure empirical coverage probability of standard 95% CIs for means and regression coefficients on DP-perturbed data across varying $\epsilon$ values.

**Independent Test**: The system is verified by running the simulation pipeline on a single dataset (e.g., UCI Adult) with a fixed set of $\epsilon$ values and noise types, outputting a CSV of coverage rates. The test verifies that the coverage rate is recorded and deviation from nominal is calculated. This test is executed AFTER the implementation tasks.

### Implementation for User Story 1

- [ ] T013a [US1] Implement `code/main.py` orchestration loop. **Reads `ground_truth.json` (T003)**. **Implements Outer Loop with `N_sim=1000`** (result of feasibility check in T040) independent samples $\times$ Inner Loop (bootstrap resamples). **Iterates over 'statistic' types (Mean, Regression) defined in ground_truth.json** (schema: `{'mean': {'dataset':..., 'parameter':...}, 'regression': {'dataset':..., 'coefficient':...}}`). **Calls functions from `code/analysis/edge_cases.py` (T014)**. **Writes intermediate coverage rows to `artifacts/coverage_intermediate.csv`**. **(Depends on T003, T004, T014)**
- [ ] T013d [US1] Implement result aggregation to read `artifacts/coverage_intermediate.csv` and write `artifacts/coverage_results.csv` (columns: dataset, epsilon, noise_type, statistic, covered, ci_lower, ci_upper, point_estimate, **deviation_from_nominal**). Explicitly calculate and store the `deviation_from_nominal` value for each row using `config.nominal_coverage_target` (not hardcoded 0.95) to satisfy SC-001. **Ensure 'dataset' and 'statistic (Mean/Regression)' are distinct columns**. **(Depends on T013a)**
- [ ] T015 [P] [US1] Unit test for DP noise calibration accuracy in `code/tests/test_dp_noise.py` **(Depends on T004)**
- [ ] T016 [P] [US1] Unit test for CI construction (percentile method) in `code/tests/test_ci_builder.py` **(Depends on T013a)**
- [ ] T017 [P] [US1] Integration test for end-to-end coverage calculation on a single condition in `code/tests/test_coverage_pipeline.py` **(Depends on T013a, T013d)**

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Evaluation of Bias-Correction and Variance-Inflation Adjustments (Priority: P2)

**Goal**: Apply unbiased estimators and variance-inflation corrections to noisy data and re-evaluate CI coverage to determine if adjustments restore nominal coverage.

**Independent Test**: The system is verified by taking the noisy datasets from User Story 1, applying the specific correction formulas, and comparing the new coverage rates against the unadjusted rates. This test is executed AFTER the implementation tasks.

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement `code/analysis/adjustments.py` with bias-correction and variance-inflation methods. **Mandatory**: Verify the specific formulas against the cited literature (**Covington et al. 2021** and **Karwa & Vadhan 2017**) before implementation to satisfy the "Verified Accuracy" constitution principle. **Implement a generic `apply_adjustments(point_estimate, standard_error, statistic_type, noise_params)` function that dispatches based on `statistic_type` (e.g., 'mean' -> Bias-Correction, 'regression' -> Variance-Inflation) to ensure the correct adjustment is applied to the correct statistic.** **Formulas to implement**:
 - **Bias-Correction (Mean)**: $\hat{\mu}_{adj} = \bar{x} - \frac{\sigma^2}{2n}$ (or as per Covington et al. 2021)
 - **Variance-Inflation (Regression)**: $SE_{adj} = SE \times \sqrt{1 + \frac{\lambda}{n}}$ (or as per Karwa & Vadhan 2017)
 - **Include direct links to the verified source text in the code comments.** **(Depends on T004)**
- [ ] T021b [US2] Integrate adjustment call into `code/main.py` (T013a) loop, ensuring it runs after noise injection but before bootstrap resampling. **Must pass the current statistic_type variable from the loop to apply_adjustments() to ensure correct dispatch**. **(Depends on T013a, T020)**
- [ ] T022 [US2] Extend `artifacts/coverage_results.csv` to include columns for `adjusted_coverage`, `adjustment_method`, and `improvement_delta` **(Depends on T013d, T021b)**
- [ ] T023 [P] [US2] Unit test for bias-correction formula implementation in `code/tests/test_adjustments.py` **(Depends on T020)**
- [ ] T024 [P] [US2] Unit test for variance-inflation correction implementation in `code/tests/test_adjustments.py` **(Depends on T020)**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Comparison and Visualization of Coverage Trends (Priority: P3)

**Goal**: Perform a Generalized Linear Model (GLM) with a binomial link to test the effects of $\epsilon$ and noise type on coverage, and generate plots comparing coverage vs. $\epsilon$.

**Independent Test**: The system is verified by running the GLM script on the aggregated coverage data and generating the required plots. The test verifies that the GLM output includes p-values for the main effects and interaction. This test is executed AFTER the implementation tasks.

### Implementation for User Story 3

- [ ] T026 [P] [US3] Implement `code/analysis/glm_analysis.py` to fit GLM: `covered ~ epsilon + noise_type` (main effects only, as per spec) with binomial link. **Load `artifacts/coverage_results.csv` generated by T013d**. **(Depends on T013d)**
- [ ] T027 [US3] Implement extraction of p-values and coefficients from GLM results and save to `artifacts/glm_summary.json` **(Depends on T026)**
- [ ] T028 [US3] Implement visualization script in `code/analysis/plotting.py` to generate line plots of coverage vs. $\epsilon$ with error bars (SE) for Laplace and Gaussian noise **(Depends on T026)**
- [ ] T029 [US3] Implement summary table generation listing coverage rates for each (dataset, statistic, $\epsilon$, noise_type) combination **(Depends on T026)**
- [ ] T030 [US3] Add validation to ensure GLM assumptions are met (binary outcome) and handle convergence warnings **(Depends on T026)**
- [ ] T031 [US3] Implement and execute sensitivity analysis: Run `code/analysis/sensitivity_analysis.py` with thresholds [0.90, 0.93, 0.95] derived from `config.nominal_coverage_target` and generate `artifacts/sensitivity_analysis.csv`. **Mandatory**: The sweep MUST report the 'change in the count of datasets passing the criterion' (as per spec FR-006), not per statistic. **(Depends on T013d)**
- [ ] T032 [P] [US3] Unit test for GLM model setup and convergence in `code/tests/test_glm_analysis.py` **(Depends on T026)**

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Implement `code/analysis/convergence_check.py` to run simulation with multiple seeds and verify standard error of coverage < 0.5% **(Depends on T013a)**
- [ ] T034a [P] Performance optimization: Extract memory-heavy loop into generator in `code/main.py` **(Depends on T013a)**
- [ ] T034b [P] Performance optimization: Implement batched resampling function in `code/analysis/ci_builder.py` **(Depends on T013a)**
- [ ] T035 [P] Performance optimization: Integrate batched resampling function into `code/main.py` **(Depends on T013a, T034b)**
- [ ] T036 [P] Documentation updates in `projects/PROJ-710-robustness-of-confidence-intervals-to-di/README.md` explaining the simulation pipeline and adjustment methods
- [ ] T037 [P] Run `quickstart.md` validation to ensure the entire pipeline runs within 6 hours on a standard runner

---

## Phase 7: Data Hygiene & Reproducibility (Review Concerns)

**Goal**: Address specific reviewer concerns regarding data source verification, synthetic fallback prevention, and computational feasibility.

- [ ] T038 [P] [Review] Refactor `code/data/synthetic_pop.py` to **remove any `try/except` blocks that fall back to synthetic/mock data generation**. If the download of the real UCI Adult/Iris/Wine Quality dataset fails (when used for validation only), the script MUST raise a specific exception (e.g., `DataFetchError`) to ensure the pipeline fails loudly rather than fabricating data. **Note**: The core population generation is synthetic and does not depend on UCI fetch; this rule applies only if UCI fetch is attempted for validation. **(Addresses "Loader must fail loudly" rule)**
- [ ] T039 [P] [Review] Implement `code/data/download_utils.py` with explicit, versioned URLs for UCI datasets (e.g., `) or verified `sklearn.datasets` loaders. **Document the exact fetch mechanism in comments**. **(Addresses "Dataset-download tasks MUST name a real, reachable URL" rule)**
- [ ] T040 [P] [Review] Add a `code/utils/feasibility_check.py` script that runs a micro-benchmark (e.g., 100 samples, 10 bootstrap resamples) at startup to verify that the full `N_sim=1000` simulation will fit within the 6-hour runtime limit on the target CPU runner. If the projected time exceeds 5.5 hours, the script must exit with a warning to reduce `N_sim` in `config.py`. **(Addresses "Compute feasibility" rule)**
- [ ] T041 [P] [Review] Ensure `code/main.py` implements a **chunked processing strategy** for the `N_sim` loop: process and write results in batches of 100 simulations to `artifacts/coverage_results.csv` using **atomic writes** (write to temp file then rename) to prevent memory accumulation and ensure data integrity if the process crashes mid-write. **(Addresses "Large real datasets: STREAM" and memory constraints, and SSoT integrity)**

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Data Hygiene (Phase 7)**: Can be implemented in parallel with User Stories, but must be merged before final integration test.

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
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all implementation tasks for User Story 1 together (after Foundation):
Task: "Implement code/analysis/edge_cases.py (T014a-T014c) for clamp_noise_scale, detect_collinearity, enforce_min_sample_size"
Task: "Implement code/main.py orchestration loop (T013a) reading ground_truth.json and calling edge_cases functions"

# Launch aggregation (after main.py logic):
Task: "Implement result aggregation to write coverage_results.csv (T013d)"

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
- **Critical**: Do not use synthetic fallbacks for data loading (T038).
- **Critical**: Ensure feasibility checks are run before full simulation (T040).
- **Note on T003**: While the generation is parallel-safe, the artifact consumption requires a 'Producer before Consumer' barrier, which is implicitly handled by the phase structure.