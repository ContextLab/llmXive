# Tasks: Robustness of Confidence Intervals to Differential Privacy Noise

**Input**: Design documents from `/specs/001-robustness-ci-dp-noise/`
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

- [ ] T001a [P] Create project directory structure: `projects/PROJ-710-robustness-of-confidence-intervals-to-di/code/`, `projects/PROJ-710-robustness-of-confidence-intervals-to-di/code/data/`, `projects/PROJ-710-robustness-of-confidence-intervals-to-di/code/analysis/`, `projects/PROJ-710-robustness-of-confidence-intervals-to-di/code/utils/`, `projects/PROJ-710-robustness-of-confidence-intervals-to-di/code/tests/`, `projects/PROJ-710-robustness-of-confidence-intervals-to-di/artifacts/` <!-- ATOMIZE: requested -->
- [X] T001b [P] Create `__init__.py` files in all Python package directories (`code/`, `code/data/`, `code/analysis/`, `code/utils/`, `code/tests/`)
- [X] T001c [P] Create `code/config.py` skeleton with placeholders for hyperparameters, random seeds, and artifact paths
- [X] T001d [P] Create `requirements.txt` with pinned versions for `numpy`, `pandas`, `scipy`, `statsmodels`, `scikit-learn`, `pytest`, `ruff`, `black`
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/config.py` with hyperparameters, random seeds, artifact paths, and `nominal_coverage_target` (default 0.95)
- [ ] T005 [P] Implement `code/data/synthetic_pop.py` to generate N=1,000,000 synthetic populations for **UCI Adult**, **UCI Iris**, and **UCI Wine Quality** distributions. The generation MUST create a population with **known parameters** (mean, variance, coefficients) to serve as ground truth, ensuring independence from sample realization. **Output to `code/data/ground_truth.json`** containing these known parameters for each population. <!-- FAILED: unspecified --> <!-- ATOMIZE: requested -->
- [X] T006 [P] Implement `code/data/dp_noise.py` for calibrated Laplace and Gaussian noise injection (CPU-only, no 8-bit quantization)
- [X] T007 [P] Create `code/utils/update_state.py` for post-run artifact hashing and state updates
- [X] T008 [P] Implement `code/data/__init__.py` and `code/utils/__init__.py` package initializers

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Empirical Coverage Estimation under Varying Privacy Budgets (Priority: P1) 🎯 MVP

**Goal**: Measure empirical coverage probability of standard 95% CIs for means and regression coefficients on DP-perturbed data across varying $\epsilon$ values.

**Independent Test**: The system can be tested by running the simulation pipeline on a single dataset (e.g., UCI Adult) with a fixed set of $\epsilon$ values and noise types, outputting a CSV of coverage rates. The test verifies that the coverage rate is recorded and deviation from nominal is calculated.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests BEFORE the implementation tasks they depend on**

- [X] T009 [P] [US1] Unit test for DP noise calibration accuracy in `code/tests/test_dp_noise.py`
- [X] T010 [P] [US1] Unit test for CI construction (percentile method) in `code/tests/test_ci_builder.py`
- [ ] T011 [P] [US1] Integration test for end-to-end coverage calculation on a single condition in `code/tests/test_coverage_pipeline.py` (depends on T013 orchestration logic) <!-- FAILED: unspecified -->

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/analysis/ci_builder.py` for 1,000 bootstrap resamples and 95% CI construction (Percentile method)
- [ ] T014 [P] [US1] Implement logic to handle edge cases: clamping noise scale for small $\epsilon$, collinearity detection in regression, and minimum sample size enforcement for bootstrap. This logic must be encapsulated as reusable functions to be called by the orchestration loop.
- [ ] T013 [US1] Implement `code/main.py` orchestration logic: Outer Loop (**[deferred] independent samples**) $\times$ Inner Loop (1,000 bootstrap resamples). **Crucially**, the CI construction (T012) MUST be executed for *every single one* of the [deferred] outer samples to generate the full coverage distribution. **Read ground_truth.json from `code/data/ground_truth.json` (T005)**. **Calculate deviation_from_nominal using `config.nominal_coverage_target`**. **Write intermediate coverage rows to `artifacts/coverage_intermediate.csv`**. Integrate the edge-case logic from T014 into this loop. <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested -->
- [ ] T015 [US1] Implement result aggregation to read `artifacts/coverage_intermediate.csv` and write `artifacts/coverage_results.csv` (columns: dataset, epsilon, noise_type, statistic, covered, ci_lower, ci_upper, point_estimate, **deviation_from_nominal**). Explicitly calculate and store the `deviation_from_nominal` value for each row using the nominal target from config.py to satisfy SC-001.
- [ ] T016 [US1] Add validation to ensure all computations use double-precision floats and CPU-only execution
- [ ] T017 [US1] Add logging for simulation progress and completion of each (dataset, $\epsilon$, noise_type) combination

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Evaluation of Bias-Correction and Variance-Inflation Adjustments (Priority: P2)

**Goal**: Apply unbiased estimators and variance-inflation corrections to noisy data and re-evaluate CI coverage to determine if adjustments restore nominal coverage.

**Independent Test**: The system can be tested by taking the noisy datasets from User Story 1, applying the specific correction formulas (e.g., from the 2021 Covington et al. paper), and comparing the new coverage rates against the unadjusted rates.

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement `code/analysis/adjustments.py` with bias-correction and variance-inflation methods. **Mandatory**: Verify the specific formulas against the cited literature (**Covington et al. 2021** and **Karwa & Vadhan 2017**) before implementation to satisfy the "Verified Accuracy" constitution principle. **Apply bias-correction (Covington) to means and variance-inflation (Karwa & Vadhan) to regression coefficients. [UNRESOLVED-CLAIM: c_0460b7a4 — status=not_enough_info] **.
- [~] T021 [US2] Modify the orchestration logic in `code/main.py` (T013) to apply adjustments to point estimates and standard errors before CI construction <!-- FAILED: unspecified -->
- [~] T022 [US2] Extend `artifacts/coverage_results.csv` to include columns for `adjusted_coverage`, `adjustment_method`, and `improvement_delta`
- [~] T023 [US2] Integrate adjustment logic into the simulation loop, ensuring it runs after noise injection but before bootstrap resampling
- [~] T024 [US2] Add logging to record which adjustment methods were applied and the resulting coverage rates for each condition

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for bias-correction formula implementation in `code/tests/test_adjustments.py`
- [X] T019 [P] [US2] Unit test for variance-inflation correction implementation in `code/tests/test_adjustments.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Comparison and Visualization of Coverage Trends (Priority: P3)

**Goal**: Perform a Generalized Linear Model (GLM) with a binomial link to test the effects of $\epsilon$ and noise type on coverage, and generate plots comparing coverage vs. $\epsilon$.

**Independent Test**: The system can be tested by running the GLM script on the aggregated coverage data and generating the required plots. The test verifies that the GLM output includes p-values for the main effects and interaction.

### Implementation for User Story 3

- [X] T026 [P] [US3] Implement `code/analysis/glm_analysis.py` to fit GLM: `covered ~ epsilon + noise_type + epsilon:noise_type` with binomial link. **Load `artifacts/coverage_results.csv` generated by T015**.
- [~] T027 [US3] Implement extraction of p-values and coefficients from GLM results and save to `artifacts/glm_summary.json`
- [X] T028 [US3] Implement visualization script in `code/analysis/plotting.py` to generate line plots of coverage vs. $\epsilon$ with error bars (SE) for Laplace and Gaussian noise
- [~] T029 [US3] Implement summary table generation listing coverage rates for each (dataset, statistic, $\epsilon$, noise_type) combination
- [~] T030 [US3] Add validation to ensure GLM assumptions are met (binary outcome) and handle convergence warnings

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US3] Unit test for GLM model setup and convergence in `code/tests/test_glm_analysis.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T031 [P] Implement `code/analysis/convergence_check.py` to run simulation with multiple seeds and verify standard error of coverage < 0.5%
- [ ] T032 [P] Implement `code/analysis/sensitivity_analysis.py` to sweep decision thresholds for 'acceptable coverage'. **Mandatory**: Thresholds MUST be configurable via `config.py` (e.g., a list of values) to allow sweeping *arbitrary* thresholds, not hardcoded to specific values, ensuring robustness to arbitrary choices as per FR-006.
- [ ] T037 [US3] Execute sensitivity analysis sweep: Run `code/analysis/sensitivity_analysis.py` with thresholds defined in `config.py` (default: [high, 0.93, 0.95]) and generate `artifacts/sensitivity_analysis.csv` to satisfy SC-005 and FR-006.
- [ ] T033 Code cleanup and refactoring to ensure memory usage stays within acceptable limits (process one condition at a time)
- [ ] T034 Performance optimization: batch bootstrap resampling to reduce overhead in `code/analysis/ci_builder.py`
- [ ] T035 [P] Documentation updates in `projects/PROJ-710-robustness-of-confidence-intervals-to-di/README.md` explaining the simulation pipeline and adjustment methods
- [ ] T036 Run `quickstart.md` validation to ensure the entire pipeline runs within 6 hours on a standard runner

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementing
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for DP noise calibration accuracy in code/tests/test_dp_noise.py"
Task: "Unit test for CI construction (percentile method) in code/tests/test_ci_builder.py"
Task: "Integration test for end-to-end coverage calculation on a single condition in code/tests/test_coverage_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement code/analysis/ci_builder.py for a sufficient number of bootstrap resamples to ensure stable 95% CI construction (Percentile method)"
Task: "Implement logic to handle edge cases: clamping noise scale for small epsilon, collinearity detection in regression, and minimum sample size enforcement for bootstrap"
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
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence