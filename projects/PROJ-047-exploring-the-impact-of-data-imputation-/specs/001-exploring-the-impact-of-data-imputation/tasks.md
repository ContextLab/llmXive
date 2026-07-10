# Tasks: Exploring the Impact of Data Imputation Methods on Causal Inference

**Input**: Design documents from `/specs/001-data-imputation-mnar-impact/`
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

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan, specifically creating these files: `code/simulation/__init__.py`, `code/analysis/__init__.py`, `tests/__init__.py`, `data/raw/.gitkeep`, `data/processed/.gitkeep`, `data/results/.gitkeep`, `code/main.py`, `code/requirements.txt`.
- [ ] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt`. Format: `package==version`. Required packages: `numpy==1.26.0`, `pandas==2.1.0`, `scikit-learn==1.3.0`, `statsmodels==0.14.0`, `matplotlib==3.8.0`, `seaborn==0.13.0`, `pytest==7.4.0`, `causalgraphicalmodels==0.0.1`.
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools for `code/` and `tests/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create `code/simulation/config.py` defining hyperparameters: beta sweep `[0.0, 0.2, 0.5, 0.8, 1.0]`, sample size `N=1000`, replications per beta `200`, and random seed management
- [ ] T005 [P] [Foundational] Define base classes/interfaces in `code/simulation/scm_generator.py`: create abstract `SCMGenerator` class and `SyntheticDataset` dataclass with fields `X`, `T`, `Y`, `ground_truth_ate`, `seed`.
- [ ] T006 [P] [Foundational] Implement `regenerate_ground_truth(seed, beta)` function in `code/simulation/scm_generator.py` to deterministically regenerate the exact $\tau_{true}$ and $\beta$ parameters for any given seed, ensuring Constitution Principle VI compliance. **Add unit tests** in `tests/test_scm_generator.py` with function name `test_regenerate_ground_truth`. The test must verify that for `seed=42` and `beta=0.5`, the function returns `tau_true=0.5` and `beta=0.5` exactly (hardcoded expected values).
- [ ] T007 [P] [Foundational] Define base classes/interfaces in `code/simulation/missingness.py`: create abstract `MissingnessInjector` class and `MissingnessPattern` dataclass with fields `mask`, `alpha`, `beta`, `target_rate`.
- [ ] T008 Create `code/analysis/__init__.py` and base data structures for `SyntheticDataset`, `ImputationResult`, and `CausalEstimate` entities
- [ ] T009 [P] [Foundational] Create `code/main.py` with an empty CLI entry point skeleton (no loop logic yet) that accepts `--config` and `--output` arguments.

---

## Phase 3: User Story 1 - Synthetic Data Generation with Explicit MNAR Mechanisms (Priority: P1) 🎯 MVP

**Goal**: Generate synthetic SCMs with known ground-truth ATE and controlled MNAR missingness to enable bias quantification.

**Independent Test**: Can be fully tested by generating a dataset, verifying the ground-truth ATE matches the theoretical value, and confirming the missingness pattern correlates with the outcome variable as specified.

### Implementation for User Story 1

- [ ] T010 [P] [US1] Implement concrete logic in `code/simulation/scm_generator.py`: create `generate_scm(seed, n, tau_true)` function that returns a `SyntheticDataset` object with `X`, `T`, `Y`, `ground_truth_ate`.
- [ ] T011 [P] [US1] Implement concrete logic in `code/simulation/missingness.py`: create `inject_mnar(data, beta, target_rate)` function using logistic regression to generate mask `M` based on `Y` (FR-002).
- [ ] T012 [US1] Implement `code/simulation/missingness.py` function `tune_alpha(beta, target_rate)` to find $\alpha$ that yields the desired missingness rate for a given $\beta$.
- [ ] T013 [US1] Add collinearity diagnostic check in `code/simulation/scm_generator.py` to flag runs where VIF > 10 (Edge Case: near-perfect collinearity).
- [ ] T014 [US1] [Requires: T010, T011] Implement verification logic in `code/simulation/verify_us1.py`: Calculate Spearman $\rho$ between $M$ and unobserved $Y$. If $\rho \le $ or $p \ge 0.01$, **flag** the run as `invalid_mnar`. **Define `run_id` as a SHA-256 hash of `seed` and `beta`**. Write results to `data/results/us1_verification.json` with schema: `{ "run_id": "<hash>", "correlation": float, "p_value": float, "is_mnar_valid": bool, "status": "valid" | "failed_low_correlation" }`. The main loop (T029a) must skip aggregation for runs where `is_mnar_valid` is false.
- [ ] T015 [US1] Create `tests/test_scm_generator.py` to test deterministic generation given a seed and verify ground-truth ATE storage.
- [ ] T016 [US1] Create `tests/test_missingness.py` to test that missingness correlates with `Y` and that `tune_alpha` converges to target rate.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (synthetic data generation with MNAR)

---

## Phase 4: User Story 2 - Standard Imputation Pipeline Execution (Priority: P2)

**Goal**: Apply Mean, KNN, and MICE imputation to incomplete datasets and estimate ATE using IPW and PSM.

**Independent Test**: Can be fully tested by running the imputation and estimation pipeline on a single generated dataset and verifying output ATEs are produced for all methods without runtime errors.

### Implementation for User Story 2

- [ ] T017 [P] [US2] Implement `code/analysis/imputation.py` function `apply_mean_imputation(data)`
- [ ] T018 [P] [US2] Implement `code/analysis/imputation.py` function `apply_knn_imputation(data, k=5)` using `sklearn.impute.KNNImputer` (CPU only, FR-003)
- [ ] T019 [P] [US2] Implement `code/analysis/imputation.py` function `apply_mice_imputation(data)` using `sklearn.impute.IterativeImputer` with `BayesianRidge` or `RandomForestRegressor` (CPU only, FR-003).
- [ ] T020 [P] [US2] **Implement Standard Error & CI Combination Logic**: Create `code/analysis/se_combination.py` with two functions: `apply_rubins_rules(estimates_list)` for MICE and `apply_bootstrap_ci(data, estimator_func, n_boot=1000)` for Mean/KNN. This task must output robust standard errors and confidence intervals.
- [ ] T021 [P] [US2] Implement `code/analysis/causal_estimation.py` function `estimate_ate_ipw(data, treatment_col, outcome_col)` using `statsmodels` (FR-004). **Call T020** for SE/CI calculation.
- [ ] T022 [P] [US2] Implement `code/analysis/causal_estimation.py` function `estimate_ate_psm(data, treatment_col, outcome_col)` using nearest neighbor matching (FR-004). **Call T020** for SE/CI calculation.
- [ ] T023 [US2] Create `code/analysis/pipeline.py` function `run_imputation_and_estimation(data)` to orchestrate: Input incomplete data → Apply 3 imputations → Apply multiple estimators to each → Return matrix of ATE estimates. **This function must be the single entry point for US2 logic.**
- [ ] T024 [US2] Add error handling in `pipeline.py` to detect and flag non-convergent imputation runs or infinite estimates (Edge Case: extreme missingness)
- [ ] T025 [US2] Create `tests/test_imputation.py` to verify imputation methods produce complete dataframes without NaNs
- [ ] T026 [US2] Create `tests/test_causal_estimation.py` to verify IPW and PSM return valid floats and standard errors

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (data generation + imputation + estimation)

---

## Phase 5: User Story 3 - Bias Quantification and Sensitivity Analysis (Priority: P3)

**Goal**: Calculate bias metrics, perform statistical testing, and execute sensitivity analysis across $\beta$ levels.

**Independent Test**: Can be fully tested by running the analysis on a small batch (e.g., 10 runs) and verifying bias metrics are calculated, statistical tests return p-values, and sensitivity plots show monotonic trends.

### Implementation for User Story 3

- [ ] T027 [P] [US3] Implement `code/analysis/metrics.py` function `calculate_bias_metrics(estimates, ground_truth)` returning absolute bias and RMSE (FR-005)
- [ ] T028 [P] [US3] Implement `code/analysis/metrics.py` function `run_statistical_test(bias_matrix)`: **Per Plan T014, implement a Linear Mixed-Effects Model (LMM)** using `statsmodels` or `linearmodels` with `run_id` as a random effect to test for bias differences across methods. If LMM fails to converge, fall back to ANOVA/Friedman. **If the distribution is skewed (assessed via Shapiro-Wilk), compute bootstrap confidence intervals as a robust alternative.** **Output**: Write the test result (p-value, test type used, conclusion, robust_ci if applicable) to `data/results/statistical_test_results.json`.
- [ ] T029a [US3] [Requires: T023] **Loop Orchestration**: Implement `code/main.py` logic to iterate through $\beta \in \{0.0, 0.2, 0.5, 0.8, 1.0\}$. For each $\beta$, iterate a sufficient number of times. **Invoke T023 (run_imputation_and_estimation)** for the pipeline step. Call `T010` (Gen), `T011` (Inject), `T014` (Verify). **Skip** aggregation for runs flagged `invalid_mnar` in T014.
- [ ] T029b [US3] [Requires: T029a] **Data Aggregation**: Aggregate results from T029a into `data/results/simulation_summary.csv`. **Schema**: `[beta, method, estimator, ate, bias, rmse, seed, run_id, ground_truth_ate, beta_value, status]`. Ensure `ground_truth_ate` and `beta_value` are included for every row to satisfy Constitution VI. **Also calculate Spearman correlation and regression slope for bias vs. beta here.**
- [ ] T029c [US3] [Requires: T029b] **Schema Validation**: Validate that `data/results/simulation_summary.csv` contains all columns required for T031 plots (bias_vs_beta, coverage_vs_beta, bias_distributions). If missing, raise an error.
- [ ] T030 [US3] [Requires: T029b] **Bias Trend Verification**: Compute Spearman rank correlation $\rho$ AND regression slope for bias vs. $\beta$. Verify $\rho > 0.9$, $p < 0.05$, and slope is positive. **Output**: Write verification result (pass/fail, $\rho$, p-value, slope, status) to `data/results/bias_trend_verification.json`.
- [ ] T031 [US3] Generate plots in `data/results/`: `data/results/bias_vs_beta.png`, `data/results/coverage_vs_beta.pdf`, and `data/results/bias_distributions.png`. Verify files exist and are non-empty.
- [ ] T032 [US3] Create `tests/test_metrics.py` to verify bias calculations match manual checks on small synthetic data
- [ ] T033 [US3] Create `tests/test_sensitivity.py` to verify monotonic trend detection logic
- [ ] T035 [US3] [Requires: T029b] **Coverage Slope Verification**: Perform linear regression of coverage rate against $\beta$. Verify slope is negative and $p < 0.05$. **Output**: Write verification result (slope, p-value, pass/fail, status) to `data/results/coverage_slope_verification.json`.
- [ ] T036 [US3] Create `tests/test_regression.py` to verify the coverage slope regression logic.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Create `.github/workflows/simulation.yml` with steps to install dependencies, run `pytest`, and execute `main.py`.
- [ ] T038 [P] Add timeout configuration to `.github/workflows/simulation.yml` (set `timeout-minutes: 240`) and verify execution time does not exceed the maximum duration of the free-tier CPU. (SC-003).
- [ ] T039 [P] Implement `code/utils/hashing.py` to generate SHA-256 content hashes for all files in `data/`.
- [ ] T040 [P] Implement logic to update `state/projects/PROJ-047-exploring-the-impact-of-data-imputation-.yaml` `artifact_hashes` map using the hashes generated in T039.
- [ ] T041 [P] Update `.github/workflows/simulation.yml` to include a step that detects GPU usage (e.g., `nvidia-smi` check or environment variable) and fails the job if GPU is detected, ensuring strict CPU-only compliance.
- [ ] T042a [US3] [Requires: T029c] Generate `docs/paper/bias_vs_beta.png` from `data/results/simulation_summary.csv` using a dedicated script `code/analysis/plot_bias.py`.
- [ ] T042b [US3] [Requires: T029c] Generate `docs/paper/coverage_vs_beta.pdf` from `data/results/simulation_summary.csv` using a dedicated script `code/analysis/plot_coverage.py`.
- [ ] T042c [US3] [Requires: T029c] Generate `docs/paper/bias_distributions.png` from `data/results/simulation_summary.csv` using a dedicated script `code/analysis/plot_distributions.py`.
- [ ] T043 Run full regression test suite on the complete pipeline to ensure no runtime errors under extreme missingness (>50%)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data generation to function
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 pipeline output to calculate metrics

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Configs before services/logic
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1, US2, and US3 implementation can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Imputation methods (Mean, KNN, MICE) and Estimators (IPW, PSM) can be implemented in parallel

---

## Parallel Example: User Story 2

```bash
# Launch all imputation implementations together:
Task: "Implement Mean imputation in code/analysis/imputation.py"
Task: "Implement KNN imputation in code/analysis/imputation.py"
Task: "Implement MICE imputation in code/analysis/imputation.py"

# Launch all estimation implementations together:
Task: "Implement IPW estimation in code/analysis/causal_estimation.py"
Task: "Implement PSM estimation in code/analysis/causal_estimation.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test US1 (generate data, verify MNAR mechanism, verify ground truth)
5. Deploy/demo if ready (demonstrating synthetic data generation capability)

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Imputation + Estimation working)
4. Add User Story 3 → Test independently → Deploy/Demo (Full simulation + stats)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Data Gen)
   - Developer B: User Story 2 (Imputation + Estimation)
   - Developer C: User Story 3 (Metrics + Sensitivity)
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
- **Critical Constraint**: All code must run on CPU-only GitHub Actions free tier (Multiple CPU, GB RAM, 6h limit). No GPU, no 8-bit quantization, no large models.
- **Data Integrity**: Never fabricate data. Use `code/simulation/scm_generator.py` for all "ground truth".
- **Statistical Rigor**: Use LMM as primary test (Plan T014); Bootstrap as fallback.
- **Verification**: All statistical tests must output JSON verification files with pass/fail flags.