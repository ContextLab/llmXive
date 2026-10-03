# Tasks: Exploring the Impact of Data Imputation Methods on Causal Inference

**Input**: Design documents from `/specs/001-data-imputation-mnar-impact/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan, specifically creating these files as empty placeholders: `code/simulation/__init__.py`, `code/analysis/__init__.py`, `tests/__init__.py`, `data/raw/.gitkeep`, `data/processed/.gitkeep`, `data/results/.gitkeep`, `code/main.py`, `code/requirements.txt`.
- [X] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt`. Format: `package==version`. Required packages: `numpy==1.26.0`, `pandas==2.1.0`, `scikit-learn==1.3.0`, `statsmodels==0.14.0`, `matplotlib==3.8.0`, `seaborn==0.13.0`, `pytest==7.4.0`, `causalinference==0.2.0`. **Note**: `causalinference` is used for causal estimation; SCM generation is implemented via custom `scm_generator.py` (T005/T010). `causalgraphicalmodels` is NOT used. (Note: T001 creates the empty file; T002 populates it).
- [X] T003a [P] Create `code/pyproject.toml` to configure Black (line-length=88) and Ruff (target-version=py311, select=["E", "F", "I"]).
- [X] T003b [P] Create `code/.ruff.toml` to configure specific Ruff rules: `ignore=['E501']`, `target-version='py311'`, and select patterns for test files. **Specific Rules**: `select=['E', 'F', 'I', 'W']`, `per-file-ignores` for test files.
- **Note**: T002, T003a, T003b are grouped as 'Configuration' tasks in Phase 1.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/simulation/config.py` defining hyperparameters: beta sweep `[0.0, 0.2, 0.5, 0.8, 1.0]`, sample size `N=1000`, replications per beta `200`, and random seed management
- [X] T005 [P] [Foundational] Define base classes/interfaces in `code/simulation/scm_generator.py`: create abstract `SCMGenerator` class and `SyntheticDataset` dataclass with fields `X`, `T`, `Y`, `ground_truth_ate`, `seed`.
- [X] T006 [P] [Foundational] Implement `regenerate_ground_truth(seed, beta)` function in `code/simulation/scm_generator.py` to deterministically regenerate the exact $\tau_{true}$ and $\beta$ parameters for any given seed, ensuring Constitution Principle VI compliance. **Add unit tests** in `tests/test_scm_generator.py` with function name `test_regenerate_ground_truth`. The test must verify that for `seed=42` and `beta=0.5`, the function returns `tau_true=0.5` (hardcoded constant) and `beta=0.5` exactly.
- [X] T007 [P] [Foundational] Define base classes/interfaces in `code/simulation/missingness.py`: create abstract `MissingnessInjector` class and `MissingnessPattern` dataclass with fields `mask`, `alpha`, `beta`, `target_rate`.
- [X] T008 Create `code/analysis/__init__.py` and base data structures for `SyntheticDataset`, `ImputationResult`, and `CausalEstimate` entities
- [X] T009 [P] [Foundational] Create `code/main.py` with an empty CLI entry point skeleton (no loop logic yet) that accepts `--config` and `--output` arguments.

---

## Phase 3: User Story 1 - Synthetic Data Generation with Explicit MNAR Mechanisms (Priority: P1) 🎯 MVP

**Goal**: Generate synthetic SCMs with known ground-truth ATE and controlled MNAR missingness to enable bias quantification.

**Independent Test**: Can be fully tested by generating a dataset, verifying the ground-truth ATE matches the theoretical value, and confirming the missingness pattern correlates with the outcome variable as specified.

### Implementation for User Story 1

- [X] T010 [P] [US1] Implement concrete logic in `code/simulation/scm_generator.py`: create `generate_scm(seed, n, tau_true)` function that returns a `SyntheticDataset` object with `X`, `T`, `Y`, `ground_truth_ate`, `seed`.
- [X] T011 [P] [US1] Implement concrete logic in `code/simulation/missingness.py`: create `inject_mnar(data, beta, target_rate)` function using logistic regression to generate mask `M` based on `Y` (FR-002).
- [X] T012 [US1] Implement `code/simulation/missingness.py` function `tune_alpha(beta, target_rate)` to find $\alpha$ that yields the desired missingness rate for a given $\beta$.
- [X] T013 [US1] Create collinearity diagnostic check in `code/simulation/scm_generator.py` to calculate Variance Inflation Factor (VIF) for each confounder using `statsmodels.stats.outliers_influence.variance_inflation_factor`. If VIF > 10, log a warning but DO NOT discard the run; store the VIF value in the run metadata. (Edge Case: near-perfect collinearity).
- [ ] T014 [US1] Add verification logic in `code/simulation/verify_us1.py`: Calculate Spearman $\rho$ between $M$ and the **generated complete Y (before masking)** for **multiple runs**. Define `run_id` as a SHA-256 hash of the string `f"{seed}_{beta}"`. Write results to `data/results/us1_verification.json` with schema: `{ "run_id": "<hash>", "correlation": float, "p_value": float, "status": "passed|failed|reported" }`. **CRITICAL**: Process all runs. If $\rho > 0.5$ and $p < 0.01$, set `status` to "passed". If $\rho \le 0.5$ or $p \ge 0.01$, set `status` to "failed" but DO NOT discard the run; log a warning and proceed. The main loop (T029a) must process ALL runs regardless of status. This task enforces the spec's verification requirement by flagging failures without filtering data. The output JSON must include the exact correlation and p-value for every run to allow downstream aggregation to flag invalid runs without excluding them. **Integration**: T029a will import and call the verification function defined here to log metrics.
- [X] T015 [US1] Create `tests/test_scm_generator.py` to test deterministic generation given a seed and verify ground-truth ATE storage.
- [X] T016 [US1] Create `tests/test_missingness.py` to test that missingness correlates with `Y` and that `tune_alpha` converges to target rate.
- [X] T055 [US1] **MNAR Mechanism Validation (KS Test)**: Implement `code/simulation/missingness.py` function `validate_mnar_ks(data_complete, data_incomplete)` to perform a Kolmogorov-Smirnov test between the complete outcome distribution and the observed outcome distribution. **Logic**: If the p-value < 0.05, the distributions are significantly different, confirming the MNAR mechanism is active (as per Plan Methodology Section 1). Write the result (statistic, p-value, status) to `data/results/mnar_validation.json`. **Integration**: Call this function in `code/main.py` (T029a) after data generation but before imputation to ensure the mechanism is valid for each run. **Rationale**: This addresses the "tautology" concern by providing an independent statistical check on the observed data properties rather than just confirming the generated mask correlates with Y. **Status**: This task is now in Phase 3 to ensure it is available for T029a.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (synthetic data generation with MNAR)

---

## Phase 4: User Story 2 - Standard Imputation Pipeline Execution (Priority: P2)

**Goal**: Apply Mean, KNN, and MICE imputation to incomplete datasets and estimate ATE using IPW and PSM.

**Independent Test**: Can be fully tested by running the imputation and estimation pipeline on a single generated dataset and verifying output ATEs are produced for all methods without runtime errors.

### Implementation for User Story 2

- [X] T017 [P] [US2] Implement `code/analysis/imputation.py` function `apply_mean_imputation(data)`
- [X] T018 [P] [US2] Implement `code/analysis/imputation.py` function `apply_knn_imputation(data, k=5)` using `sklearn.impute.KNNImputer` (CPU only, FR-003)
- [X] T019 [P] [US2] Implement `code/analysis/imputation.py` function `apply_mice_imputation(data)` using `sklearn.impute.IterativeImputer` with `BayesianRidge` or `RandomForestRegressor` (CPU only, FR-003).
- [X] T020 [P] [US2] **Implement Standard Error & CI Combination Logic**: Create `code/analysis/se_combination.py` with two functions: `apply_rubins_rules(estimates_list)` for MICE and `apply_bootstrap_ci(ate_estimates, n_boot=1000)` for Mean/KNN. **Resampling Strategy**: For `apply_bootstrap_ci`, use `scipy.stats.bootstrap` to resample the ATE estimates (not the raw data) with replacement a sufficient number of times. This task must output robust standard errors and confidence intervals.
- [X] T021 [P] [US2] Implement `code/analysis/causal_estimation.py` function `estimate_ate_ipw(data, treatment_col, outcome_col)` using `statsmodels` (FR-004). **Call T020** for SE/CI calculation.
- [X] T022 [P] [US2] Implement `code/analysis/causal_estimation.py` function `estimate_ate_psm(data, treatment_col, outcome_col)` using nearest neighbor matching (FR-004). **Call T020** for SE/CI calculation.
- [X] T023 [US2] Create `code/analysis/pipeline.py` function `run_imputation_and_estimation(data)` to orchestrate: Input incomplete data → Apply 3 imputations → Apply multiple estimators to each → Return matrix of ATE estimates. **This function must be the single entry point for US2 logic.**
- [ ] T024 [US2] [Requires: T023] **Implement Error Handling in pipeline.py**: Add error handling to T023 to detect and flag non-convergent imputation runs or infinite estimates (Edge Case: extreme missingness). **Specific Logic**: Wrap imputation calls in `try/except` blocks catching `ConvergenceWarning` and `ValueError`. If caught, or if `np.isinf(ate)` is detected, set the `status` field in the output to `'failed'` and log the error to `data/results/run_errors.log`. Do not crash the main loop.
- [X] T025 [US2] Create `tests/test_imputation.py` to verify imputation methods produce complete dataframes without NaNs
- [X] T026 [US2] Create `tests/test_causal_estimation.py` to verify IPW and PSM return valid floats and standard errors

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (data generation + imputation + estimation)

---

## Phase 5: User Story 3 - Bias Quantification and Sensitivity Analysis (Priority: P3)

**Goal**: Calculate bias metrics, perform statistical testing, and execute sensitivity analysis across $\beta$ levels.

**Independent Test**: Can be fully tested by running the analysis on a small batch (e.g., 10 runs) and verifying bias metrics are calculated, statistical tests return p-values, and sensitivity plots show monotonic trends.

### Implementation for User Story 3

- [X] T027 [P] [US3] Implement `code/analysis/metrics.py` function `calculate_bias_metrics(estimates, ground_truth)` returning absolute bias and RMSE (FR-005)
- [ ] T028 [US3] [Requires: T029c, T029d] Implement `code/analysis/metrics.py` function `run_statistical_test(bias_matrix)`: **Per FR-006, implement the specific decision tree:** 1) Run Shapiro-Wilk test on bias distribution (derived from `data/results/simulation_summary.csv` aggregated by beta level). 2) If $p < 0.05$ (non-normal) → Use **Friedman Test**. 3) If $p \ge$ the conventional significance threshold (normal) → Use **Repeated-Measures ANOVA**. 4) **INDEPENDENTLY AND MANDATORILY**: Calculate skewness via `scipy.stats.skew`. If **|skewness| > 1** (as defined in the plan's 'Complexity Tracking' table) → Compute **Bootstrap CIs** (A sufficient number of iterations) for the difference in medians between the best and worst performing methods as a robust alternative. **Output**: Write the test result (p-value, test type used, conclusion, bootstrap_ci_diff) to `data/results/statistical_test_results.json` with schema: `{ "test_type": "anova|friedman", "p_value": float, "test_statistic": float, "skewness": float, "bootstrap_ci_diff": float }`. **Mandatory**: If |skewness| > 1, `bootstrap_ci_diff` MUST be populated (not null). If not met, `bootstrap_ci_diff` MUST be set to `null` or `0.0` to ensure deterministic schema. The `test_type` field must strictly reflect the primary normality-based test (ANOVA or Friedman); the bootstrap result is a parallel robust metric, not a replacement for the primary test type. **Crucial**: The Bootstrap calculation must be performed regardless of the ANOVA/Friedman result if skewness > 1.
- [X] T029a [US3] [Requires: T023, T014, T055, T029b] **Loop Orchestration**: Implement `code/main.py` logic to iterate through $\beta \in \{0.0, 0.2, 0.5, 0.8, 1.0\}$. For each $\beta$, iterate for **sufficient replications** to ensure convergence. **Invoke T023 (run_imputation_and_estimation)** for the pipeline step. Call `T014` (Gen) to log metrics. **Invoke T055** to validate the MNAR mechanism via KS test before imputation. **Implement Ground Truth Storage**: For each run, call `regenerate_ground_truth(seed, beta)` and store `tau_true`, `alpha`, `beta` in the run data (Merging T029b logic here). **Constitution VI**: Ensure these values are explicitly stored for every row. **Do NOT call T028 inside the loop**. Instead, after the loop completes, invoke T029c (Aggregation), T029d (Validation), and then T028 (Stats). **This task orchestrates the internal calls to T029b and T029c functions.** **Output**: Generate raw run data to a temporary file or memory buffer, which is then consumed by T029c.
- [ ] T029c [US3] [Requires: T029a, T029b] **Data Aggregation**: Implement function `def aggregate_results(runs_list: List[Dict]) -> pd.DataFrame` in `code/analysis/aggregation.py`. Input: List of run dictionaries. Output: DataFrame. **Schema**: `[beta, method, estimator, ate, bias, rmse, coverage_rate, seed, run_id, ground_truth_ate, beta, status, vif, mnar_correlation, mnar_p_value]`. **Explicitly calculate coverage_rate** as the proportion of CIs (from T020) that contain `ground_truth_ate`, averaged per (method, estimator, beta) combination. **Mandatory**: Call `regenerate_ground_truth(seed, beta)` to verify integrity before storing `ground_truth_ate` to satisfy Constitution Principle VI. **CRITICAL**: DO NOT filter out rows where `status='failed'`. Instead, for rows where `status='failed'`, set `bias` and `rmse` to `NaN` but **preserve the row** and the `status='failed'` flag in the output CSV. This ensures downstream analysis can inspect failure modes (extreme missingness) as required by Spec Edge Case 2. Write results to `data/results/simulation_summary.csv`.
- [ ] T029d [US3] [Requires: T029c] **Schema Validation**: Implement function `def validate_schema(df: pd.DataFrame) -> bool` in `code/analysis/validation.py`. Validate that `data/results/simulation_summary.csv` contains ALL required columns: `[beta, method, estimator, ate, bias, rmse, coverage_rate, seed, run_id, ground_truth_ate, beta, status, vif, mnar_correlation, mnar_p_value]`. If missing, raise an error.
- [ ] T030 [US3] [Requires: T029c] **Intermediate Sensitivity Aggregation**: Implement `code/analysis/sensitivity.py` to aggregate the `simulation_summary.csv` into `data/results/sensitivity_analysis_dataset.csv`. This task calculates the mean absolute bias and mean coverage rate per beta level. **Output**: Generate the intermediate CSV file required by T031. This task is the producer for T031.
- [X] T031 [US3] [Requires: T030] **Monotonic Trend Verification & Sensitivity Dataset (FR-007/SC-005)**: Implement `code/analysis/sensitivity.py` to calculate and verify monotonic trends for bias and coverage using the output from T030. **Primary Artifact**: Explicitly generate and save `data/results/sensitivity_analysis.json` containing the final monotonicity confirmation. **Verification**: Verify Spearman $\rho > 0.9$ and $p < 0.05$ for bias trend, and negative slope ($p < 0.05$) for coverage trend. **Output**: Calculate Spearman rho and p-value directly from the aggregated data in `data/results/sensitivity_analysis_dataset.csv` (produced by T030). Write the final consolidated result to `data/results/sensitivity_analysis.json` with keys: `{ "monotonicity_confirmed": bool, "spearman_rho": float, "p_value": float, "negative_slope_confirmed": bool }`. The `spearman_rho` and `p_value` MUST correspond to the **bias** monotonicity check as required by SC-005.
- [X] T032 [US3] **Power Analysis**: Implement `code/analysis/power.py` to calculate statistical power for the bias comparison.
- [X] T033 [US3] Create `tests/test_metrics.py` to verify bias calculations match manual checks on small synthetic data <!-- FAILED: unspecified -->
- [X] T034 [US3] Create `tests/test_sensitivity.py` to verify monotonic trend detection logic
- [X] T035 [US3] **Oracle Benchmark**: Implement `code/analysis/oracle.py` to run IPW on complete (unmasked) data. Calculate bias relative to this oracle benchmark to distinguish imputation failure from MNAR parameter distortion. **Success Criterion**: If `bias_vs_oracle` > 0.1, flag the run as "imputation_failure" in the output JSON. **Output**: Write results to `data/results/oracle_benchmark.json` with schema: `{ "method": str, "bias_vs_oracle": float, "bias_vs_truth": float, "flag": "imputation_failure|normal" }`.
- [ ] T036 [US3] [Requires: T029c] **Power Sensitivity Analysis**: Implement logic to vary the number of runs per beta (e.g., multiple trials) and calculate post-hoc power using `statsmodels.stats.power.tt_ind_solve_power` with effect size `Cohen's d = 0.5` and target power `0.8`. **Distinction**: Unlike T033 (Post-hoc on observed effect), this task performs a sensitivity analysis by varying the *assumed* effect size to determine required sample sizes. Flag if power < 80% in `data/results/power_analysis.json`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T037 [P] Create `.github/workflows/simulation.yml` with steps to install dependencies, run `pytest`, and execute `main.py`.
- [X] T038 [P] Add timeout configuration to `.github/workflows/simulation.yml` (set `timeout-minutes:`) and verify execution time does not exceed the maximum duration of the free-tier CPU. (SC-003).
- [X] T039 [P] Implement `code/utils/hashing.py` to generate SHA-256 content hashes for all files in `data/`.
- [X] T040 [P] Implement logic to update `state/projects/PROJ-047-exploring-the-impact-of-data-imputation-.yaml` `artifact_hashes` map using the hashes generated in T039.
- [X] T041 [P] [US3] Create `code/visualization.py` as a unified CLI script to handle all plot generation requests (`--plot bias_vs_beta`, `--plot coverage_vs_beta`, `--plot bias_distributions`).
- [ ] T047 [P] [US3] Create `code/visualization.py` as a unified CLI script to handle all plot generation requests (`--plot bias_vs_beta`, `--plot coverage_vs_beta`, `--plot bias_distributions`). This task resolves the missing script referenced in T046 and consolidates the logic from T042a-c into a single, maintainable entry point that reads from `data/results/simulation_summary.csv` and outputs to `docs/paper/figures/`. Ensure strict adherence to the schema validation defined in T029d. **Requires: T029c, T029d** (Data validation must pass before plotting). **Note**: Documentation updates for this script are handled in T042.

---

## Phase 7: Revision & Hardening (Review Concerns)

**Purpose**: Address specific reviewer concerns regarding data integrity, statistical robustness, and execution feasibility.

- [X] T042 [P] [US3] **Documentation Update**: Update `docs/paper/notes.md` and any relevant README files to replace references to `code/run_simulation.py` and `code/analysis.py` with the correct entry point `code/visualization.py` (created in T047). **Note**: This task corrects the documentation to reflect the actual implementation, removing references to hallucinated scripts.
- [X] T048 [P] [US3] **Explicit MNAR Mechanism Documentation**: Update `code/simulation/missingness.py` and `docs/paper/notes.md` to explicitly document that the "ground truth" refers to the generative parameter and that ATE is not identifiable from observed data. Add a warning log in `main.py` (T029a) that prints this disclaimer before every run.
- [X] T049 [P] [US3] **Robust SE/CI Verification**: Extend `tests/test_se_combination.py` to verify that `apply_bootstrap_ci` and `apply_rubins_rules` produce standard errors within expected bounds for a known synthetic distribution (e.g., normal data with known variance).
- [~] T050 [P] [US3] **Convergence Failure Handling**: [Requires: T024] Enhance `code/analysis/pipeline.py` (T024) to explicitly log the convergence failure reason (e.g., "MICE failed to converge after 10 iterations") and ensure this log is captured in `data/results/run_errors.log` with a unique run ID. **Crucially**: Update `code/analysis/aggregation.py` (T029c) to preserve rows where `status='failed'` with NaN metrics, ensuring these runs are included in the final dataset for failure mode analysis as required by the spec's Edge Cases.
- [~] T051 [P] [US3] **Power Analysis Validation**: Update `code/analysis/power.py` to output a detailed report in `data/results/power_analysis.json` that includes the calculated effect size, sample size, and the specific power value, ensuring the "flag if power < 80%" logic is clearly visible in the output. **Documentation**: If power < 80%, append a Limitation section to `docs/paper/notes.md` detailing the underpowered comparison.
- [X] T052 [P] [US3] **Runtime Optimization**: Profile `code/main.py` (T029a) to identify bottlenecks in the 200-run loop. If runtime exceeds several hours, implement `joblib.Parallel` with `n_jobs=2` for independent beta-level loops to ensure SC-003 compliance (completion within 4 hours).
- [X] T053 [P] [US3] **Schema Rigor**: Add a strict Pydantic model in `code/analysis/schemas.py` for `simulation_summary.csv` and `statistical_test_results.json`. Update T029d and T028 to use these models for validation, raising a `ValidationError` if any field is missing or of the wrong type.
- [X] T054 [P] [US3] **MNAR Parameter Sweep Verification**: Add a unit test in `tests/test_missingness.py` to verify that `tune_alpha` correctly converges to the target missingness rate for extreme $\beta$ values (0.0, 1.0), ensuring the sweep covers the full range of MNAR intensity.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Revision (Phase 7)**: Depends on completion of all User Story phases and initial execution feedback

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other user stories
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
- Phase 7 tasks (T049-T054) can be executed in parallel as they are independent hardening steps

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
- **Statistical Rigor**: Use FR-006 decision tree (Shapiro -> ANOVA/Friedman -> Bootstrap) as primary test. Bootstrap is conditional on skewness and mandatory if |skewness| > 1.
- **Verification**: All statistical tests must output JSON verification files with pass/fail flags.
- **No Filtering**: Do not discard runs based on correlation thresholds (T014) or status='failed' (T029c).
- **Single Source of Truth**: Every metric must trace back to a specific run in the simulation, allowing for reproducibility and verification.
- **Data Collection**: Log all relevant data points (parameters, results, errors) for each run to enable detailed analysis and debugging.
- **MNAR Validation**: Task T055 provides independent validation of the missingness mechanism using the Kolmogorov-Smirnov test, addressing the tautology concern in the plan.
- **T030/T031 Relationship**: T030 produces the intermediate sensitivity dataset; T031 consumes it to verify monotonicity.
- **T042 Role**: T042 updates documentation to reflect the correct visualization entry point (`code/visualization.py`).
