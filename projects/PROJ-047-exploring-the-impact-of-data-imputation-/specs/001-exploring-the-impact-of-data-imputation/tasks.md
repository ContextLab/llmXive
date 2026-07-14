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

- [ ] T001 Create project structure per implementation plan, specifically creating these files as empty placeholders: `code/simulation/__init__.py`, `code/analysis/__init__.py`, `tests/__init__.py`, `data/raw/.gitkeep`, `data/processed/.gitkeep`, `data/results/.gitkeep`, `code/main.py`, `code/requirements.txt`.
- [X] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt`. Format: `package==version`. Required packages: `numpy==1.26.0`, `pandas==2.1.0`, `scikit-learn==1.3.0`, `statsmodels==0.14.0`, `matplotlib==3.8.0`, `seaborn==0.13.0`, `pytest==7.4.0`, `causalgraphicalmodels==0.0.1`. (Note: T001 creates the empty file; T002 populates it).
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools for `code/` and `tests/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/simulation/config.py` defining hyperparameters: beta sweep `[0.0, 0.2, 0.5, 0.8, 1.0]`, sample size `N=1000`, replications per beta `200`, and random seed management
- [X] T005 [P] [Foundational] Define base classes/interfaces in `code/simulation/scm_generator.py`: create abstract `SCMGenerator` class and `SyntheticDataset` dataclass with fields `X`, `T`, `Y`, `ground_truth_ate`, `seed`.
- [ ] T006 [P] [Foundational] Implement `regenerate_ground_truth(seed, beta)` function in `code/simulation/scm_generator.py` to deterministically regenerate the exact $\tau_{true}$ and $\beta$ parameters for any given seed, ensuring Constitution Principle VI compliance. **Add unit tests** in `tests/test_scm_generator.py` with function name `test_regenerate_ground_truth`. The test must verify that for `seed=42` and `beta=0.5`, the function returns `tau_true=0.5` (hardcoded constant) and `beta=0.5` exactly.
- [X] T007 [P] [Foundational] Define base classes/interfaces in `code/simulation/missingness.py`: create abstract `MissingnessInjector` class and `MissingnessPattern` dataclass with fields `mask`, `alpha`, `beta`, `target_rate`.
- [ ] T008 Create `code/analysis/__init__.py` and base data structures for `SyntheticDataset`, `ImputationResult`, and `CausalEstimate` entities
- [X] T009 [P] [Foundational] Create `code/main.py` with an empty CLI entry point skeleton (no loop logic yet) that accepts `--config` and `--output` arguments.

---

## Phase 3: User Story 1 - Synthetic Data Generation with Explicit MNAR Mechanisms (Priority: P1) 🎯 MVP

**Goal**: Generate synthetic SCMs with known ground-truth ATE and controlled MNAR missingness to enable bias quantification.

**Independent Test**: Can be fully tested by generating a dataset, verifying the ground-truth ATE matches the theoretical value, and confirming the missingness pattern correlates with the outcome variable as specified.

### Implementation for User Story 1

- [~] T010 [P] [US1] Implement concrete logic in `code/simulation/scm_generator.py`: create `generate_scm(seed, n, tau_true)` function that returns a `SyntheticDataset` object with `X`, `T`, `Y`, `ground_truth_ate`.
- [~] T011 [P] [US1] Implement concrete logic in `code/simulation/missingness.py`: create `inject_mnar(data, beta, target_rate)` function using logistic regression to generate mask `M` based on `Y` (FR-002).
- [~] T012 [US1] Implement `code/simulation/missingness.py` function `tune_alpha(beta, target_rate)` to find $\alpha$ that yields the desired missingness rate for a given $\beta$.
- [~] T013 [US1] Add collinearity diagnostic check in `code/simulation/scm_generator.py` to flag runs where VIF > 10 (Edge Case: near-perfect collinearity).
- [~] T014 [US1] [Requires: T010, T011] Implement verification logic in `code/simulation/verify_us1.py`: Calculate Spearman $\rho$ between $M$ and the **generated complete Y (before masking)**. Define `run_id` as a SHA-256 hash of the string `f"{seed}_{beta}"`. Write results to `data/results/us1_verification.json` with schema: `{ "run_id": "<hash>", "correlation": float, "p_value": float, "status": "reported" }`. **CRITICAL**: DO NOT filter, discard, or flag runs as invalid based on correlation thresholds. Report the metric for ALL runs regardless of value. The main loop (T029a) must process ALL runs; no skipping based on correlation.
- [~] T015 [US1] Create `tests/test_scm_generator.py` to test deterministic generation given a seed and verify ground-truth ATE storage.
- [~] T016 [US1] Create `tests/test_missingness.py` to test that missingness correlates with `Y` and that `tune_alpha` converges to target rate.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (synthetic data generation with MNAR)

---

## Phase 4: User Story 2 - Standard Imputation Pipeline Execution (Priority: P2)

**Goal**: Apply Mean, KNN, and MICE imputation to incomplete datasets and estimate ATE using IPW and PSM.

**Independent Test**: Can be fully tested by running the imputation and estimation pipeline on a single generated dataset and verifying output ATEs are produced for all methods without runtime errors.

### Implementation for User Story 2

- [~] T017 [P] [US2] Implement `code/analysis/imputation.py` function `apply_mean_imputation(data)`
- [~] T018 [P] [US2] Implement `code/analysis/imputation.py` function `apply_knn_imputation(data, k=5)` using `sklearn.impute.KNNImputer` (CPU only, FR-003)
- [~] T019 [P] [US2] Implement `code/analysis/imputation.py` function `apply_mice_imputation(data)` using `sklearn.impute.IterativeImputer` with `BayesianRidge` or `RandomForestRegressor` (CPU only, FR-003).
- [~] T020 [P] [US2] **Implement Standard Error & CI Combination Logic**: Create `code/analysis/se_combination.py` with two functions: `apply_rubins_rules(estimates_list)` for MICE and `apply_bootstrap_ci(ate_estimates, n_boot=1000)` for Mean/KNN. This task must output robust standard errors and confidence intervals. **Resampling Strategy**: For `apply_bootstrap_ci`, resample the ATE estimates (not the raw data) with replacement. This task defines the standard utility for robust SEs used by all methods.
- [~] T021 [P] [US2] Implement `code/analysis/causal_estimation.py` function `estimate_ate_ipw(data, treatment_col, outcome_col)` using `statsmodels` (FR-004). **Call T020** for SE/CI calculation.
- [~] T022 [P] [US2] Implement `code/analysis/causal_estimation.py` function `estimate_ate_psm(data, treatment_col, outcome_col)` using nearest neighbor matching (FR-004). **Call T020** for SE/CI calculation.
- [~] T023 [US2] Create `code/analysis/pipeline.py` function `run_imputation_and_estimation(data)` to orchestrate: Input incomplete data → Apply 3 imputations → Apply multiple estimators to each → Return matrix of ATE estimates. **This function must be the single entry point for US2 logic.**
- [~] T024 [US2] Add error handling in `pipeline.py` to detect and flag non-convergent imputation runs or infinite estimates (Edge Case: extreme missingness)
- [~] T025 [US2] Create `tests/test_imputation.py` to verify imputation methods produce complete dataframes without NaNs
- [~] T026 [US2] Create `tests/test_causal_estimation.py` to verify IPW and PSM return valid floats and standard errors

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (data generation + imputation + estimation)

---

## Phase 5: User Story 3 - Bias Quantification and Sensitivity Analysis (Priority: P3)

**Goal**: Calculate bias metrics, perform statistical testing, and execute sensitivity analysis across $\beta$ levels.

**Independent Test**: Can be fully tested by running the analysis on a small batch (e.g., 10 runs) and verifying bias metrics are calculated, statistical tests return p-values, and sensitivity plots show monotonic trends.

### Implementation for User Story 3

- [~] T027 [P] [US3] Implement `code/analysis/metrics.py` function `calculate_bias_metrics(estimates, ground_truth)` returning absolute bias and RMSE (FR-005)
- [ ] T028 [P] [US3] Implement `code/analysis/metrics.py` function `run_statistical_test(bias_matrix)`: **Per FR-006, implement the specific decision tree:** 1) Run Shapiro-Wilk test on bias distribution. 2) If $p < 0.05$ (non-normal) → Use **Friedman Test**. 3) If $p \ge 0.05$ (normal) → Use **Repeated-Measures ANOVA**. 4) **Conditionally**: If skewness > 1 OR < -1 (calculated via `scipy.stats.skew`) → Compute **Bootstrap CIs** (A sufficient number of iterations) for the difference in medians between the best and worst performing methods as a robust alternative to the primary test. **Output**: Write the test result (p-value, test type used, conclusion, bootstrap_ci_diff if applicable) to `data/results/statistical_test_results.json`.
- [ ] T029a [US3] [Requires: T023] **Loop Orchestration**: Implement `code/main.py` logic to iterate through $\beta \in \{0.0, 0.2, 0.5, 0.8, 1.0\}$. For each $\beta$, iterate a sufficient number of times. **Invoke T023 (run_imputation_and_estimation)** for the pipeline step. Call `T010` (Gen), `T011` (Inject). **Import and call the verification function defined in T014** to log metrics, but DO NOT skip any runs based on the verification result.
- [ ] T029b [US3] [Requires: T029a] **Data Generation & Ground Truth Storage**: For each run, call `regenerate_ground_truth(seed, beta)` and store `tau_true`, `alpha`, `beta` in the run data.
- [ ] T029c [US3] [Requires: T029a, T029b] **Data Aggregation**: Aggregate results from T029a and T029b into `data/results/simulation_summary.csv`. **Schema**: `[beta, method, estimator, ate, bias, rmse, coverage_rate, seed, run_id, ground_truth_ate, beta_value, status]`. **Explicitly calculate coverage_rate** as the proportion of CIs (from T020) that contain `ground_truth_ate`, averaged per (method, estimator, beta) combination. Ensure `ground_truth_ate` and `beta_value` are included for every row to satisfy Constitution VI.
- [ ] T029d [US3] [Requires: T029c] **Schema Validation**: Validate that `data/results/simulation_summary.csv` contains all columns required for T031 plots (bias_vs_beta, coverage_vs_beta, bias_distributions). If missing, raise an error.
- [ ] T030 [US3] [Requires: T029c] **Bias Trend Verification**: Compute Spearman rank correlation $\rho$ AND regression slope for bias vs. $\beta$. Verify $\rho > 0.9$, $p < 0.05$, and slope is positive. **Unit of Analysis**: Use the mean bias per beta level (aggregated from all runs) for the regression. **Output**: Write verification result (pass/fail, $\rho$, p-value, slope, status) to `data/results/bias_trend_verification.json`.
- [ ] T031 [US3] [Requires: T029c] **Monotonic Trend Verification & Sensitivity Dataset (FR-007/SC-005)**: Implement `code/analysis/sensitivity.py` to calculate and verify monotonic trends for bias and coverage. **Primary Artifact**: Explicitly generate and save `data/results/sensitivity_analysis_dataset.csv` containing the mean absolute bias and mean coverage rate per beta level (aggregated). **Verification**: Verify Spearman $\rho > 0.9$ and $p < 0.05$ for bias trend, and negative slope ($p < 0.05$) for coverage trend. **Output**: Write results to `data/results/sensitivity_analysis.json` with `monotonicity_confirmed` and `negative_slope_confirmed` flags.
- [ ] T032 [US3] [REMOVED - Merged into T031]
- [ ] T033 [US3] Create `tests/test_metrics.py` to verify bias calculations match manual checks on small synthetic data
- [ ] T034 [US3] Create `tests/test_sensitivity.py` to verify monotonic trend detection logic
- [ ] T035 [US3] [REMOVED - Merged into T031]
- [ ] T036 [US3] **Oracle Benchmark (Plan T036)**: Implement `code/analysis/oracle.py` to run IPW on complete (unmasked) data. Calculate bias relative to this oracle benchmark to distinguish imputation failure from MNAR parameter distortion. Write results to `data/results/oracle_benchmark.json`.
- [ ] T037 [US3] **Power Sensitivity Analysis (Plan T032)**: Implement logic to vary the number of runs per beta (e.g., multiple trials) and calculate post-hoc power. Flag if power < 80% in `data/results/power_analysis.json`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Create `.github/workflows/simulation.yml` with steps to install dependencies, run `pytest`, and execute `main.py`.
- [ ] T039 [P] Add timeout configuration to `.github/workflows/simulation.yml` (set `timeout-minutes:`) and verify execution time does not exceed the maximum duration of the free-tier CPU. (SC-003).
- [ ] T040 [P] Implement `code/utils/hashing.py` to generate SHA-256 content hashes for all files in `data/`.
- [ ] T041 [P] Implement logic to update `state/projects/PROJ-047-exploring-the-impact-of-data-imputation-.yaml` `artifact_hashes` map using the hashes generated in T040.
- [ ] T042a [US3] [Requires: T029d] Generate `docs/paper/bias_vs_beta.png` from `data/results/simulation_summary.csv` using a dedicated script `code/analysis/plot_bias.py`.
- [ ] T042b [US3] [Requires: T029d] Generate `docs/paper/coverage_vs_beta.pdf` from `data/results/simulation_summary.csv` using a dedicated script `code/analysis/plot_coverage.py`.
- [ ] T042c [US3] [Requires: T029d] Generate `docs/paper/bias_distributions.png` from `data/results/simulation_summary.csv` using a dedicated script `code/analysis/plot_distributions.py`.
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
- **Critical Constraint**: All code must run on CPU-only GitHub Actions free tier (Multiple CPU, GB RAM, h limit). No GPU, no 8-bit quantization, no large models.
- **Data Integrity**: Never fabricate data. Use `code/simulation/scm_generator.py` for all "ground truth".
- **Statistical Rigor**: Use FR-006 decision tree (Shapiro -> ANOVA/Friedman -> Bootstrap) as primary test. Bootstrap is conditional on skewness.
- **Verification**: All statistical tests must output JSON verification files with pass/fail flags.
- **No Filtering**: Do not discard runs based on correlation thresholds (T014).