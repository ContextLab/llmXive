# Tasks: Exploring the Impact of Data Imputation Methods on Causal Inference

**Input**: Design documents from `/specs/001-exploring-the-impact-of-data-imputation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root (per plan.md structure)
- Paths shown below assume single project - adjust based on plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per `plan.md` by running:
  `mkdir -p code data/raw data/processed data/results tests/unit tests/integration docs state`
  `touch code/__init__.py tests/__init__.py state/.gitkeep docs/.gitkeep`
  Ensure all directories and `__init__.py` files exist before proceeding.
- [ ] T002 Initialize Python 3.11 project with `code/requirements.txt` containing exact pins:
  `numpy>=1.24.0`, `pandas>=2.0.0`, `scikit-learn>=1.3.0`, `statsmodels>=0.14.0`, `linearmodels>=6.0.0`, `matplotlib>=3.7.0`, `seaborn>=0.12.0`, `pytest>=7.0.0`, `ruff>=0.1.0`, `arttest>=1.0.0`.
- [ ] T003 [P] Configure `pytest` and linting tools by creating `code/pytest.ini` (content: `[pytest] testpaths = ../tests`) and `code/.ruff.toml` (content: `[lint] select = ["E", "F"]`) in `code/`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.
**Ordering Note**: T005 MUST complete before T010, T017, T020.

- [ ] T004 [P] Implement deterministic random seed management utility in `code/utils_seeds.py` with function signature:
  `def get_seed(replication_id: int) -> int` returning a unique integer seed for each replication_id.
- [ ] T005 Create base data structures and type hints in `code/models.py` defining:
  `class SyntheticDataset` (attrs: `treatment: np.ndarray`, `outcome: np.ndarray`, `confounders: np.ndarray`, `missingness_indicator: np.ndarray`, `ground_truth_ate: float`),
  `class ImputationResult` (attrs: `method: str`, `imputed_data: pd.DataFrame`, `convergence_status: bool`),
  `class CausalEstimate` (attrs: `imputation_method: str`, `estimator: str`, `estimated_ate: float`, `standard_error: float`, `bias: float`, `rmse: float`).
- [ ] T006 [P] Setup logging infrastructure in `code/logging_config.py` to configure a logger writing to `logs/simulation.log` with format `'%(asctime)s - %(levelname)s - %(message)s'` and handlers for `convergence_failures` and `missingness_rates`.
- [ ] T007 [P] Implement VIF checker in `code/utils_vif.py` with function signature:
  `def check_vif(df: pd.DataFrame) -> float` returning the maximum VIF value; raise ValueError if > 10.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Simulate MNAR Data and Compute Ground Truth (Priority: P1) 🎯 MVP

**Goal**: Generate synthetic datasets with known ground-truth ATE and explicitly parameterized MNAR missingness.

**Independent Test**: Running the generation script with fixed seeds produces a dataset where the calculated ATE from complete data matches the injected $\tau_{true}$ within 0.01 tolerance, and the missingness indicator $M$ correlates with $Y$ as specified by $\beta$.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T008 [P] [US1] Unit test for ground-truth ATE recovery in `tests/unit/test_data_gen.py` (verify `abs(calculated_ate - tau_true) / abs(tau_true) < 0.01`)
- [ ] T009 [P] [US1] Unit test for MNAR mechanism fidelity in `tests/unit/test_data_gen.py` (verify logistic regression of $M$ on $Y$ recovers $\beta$ within 10% error)

### Implementation for User Story 1

- [ ] T010 [US1] Implement synthetic SCM data generator in `code/generate_data.py` with function signature:
  `def generate_scm(n_samples: int, tau_true: float, seed: int) -> pd.DataFrame` returning a DataFrame with `treatment`, `outcome`, `confounders`, and `ground_truth_ate`.
- [ ] T011 [US1] Implement MNAR missingness injector in `code/generate_data.py` with function signature:
  `def inject_mnar(df: pd.DataFrame, beta: float, target_rate: float) -> pd.DataFrame` solving for $\alpha$ to achieve `target_rate` missingness using logistic model $P(M=1|Y) = \text{logit}^{-1}(\alpha + \beta Y)$.
- [ ] T011a [US1] Implement missingness mechanism verification in `code/generate_data.py` with function signature:
  `def verify_mnar_mechanism(df: pd.DataFrame, injected_beta: float) -> dict` fitting logistic regression of $M$ on $Y$, recovering $\hat{\beta}$, and returning `{'recovered_beta': float, 'error_pct': float, 'passed': bool}`. **Logic**: If `error_pct > 10`, raise an exception or flag the replication for exclusion immediately; this check runs *before* any imputation or estimation steps.
- [ ] T012a [US1] Implement zero-variance treatment detection and regeneration loop in `code/generate_data.py` with logic:
  `if np.var(treatment) == 0: regenerate_data()`. Ensure this check runs before VIF check.
- [ ] T012 [US1] Add VIF check and regeneration loop in `code/generate_data.py` with logic:
  `while max_vif > 10 and retries < 5: regenerate_data()`. Raise exception if max retries exceeded.
- [ ] T013 [US1] Implement edge-case handling for extreme sparsity (>90% missing) in `code/generate_data.py` with logic:
  If missingness rate > 0.90, add column `is_reliable=False` to the DataFrame and log a warning; do not crash.
- [ ] T014 [US1] Create orchestration script `code/run_simulation.py` with CLI args `--seeds` (list), `--n-reps` (int), looping 200 replications and saving raw datasets to `data/raw/seed_{i}.csv`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Apply Standard Imputation and Estimate Causal Effects (Priority: P2)

**Goal**: Apply Mean, KNN, and MICE imputation to incomplete datasets and estimate ATE using IPW and PSM.

**Independent Test**: Feeding a single incomplete dataset produces three valid ATE estimates (Mean, KNN, MICE) with no runtime errors, and IPW/PSM estimators output valid standard errors.

**Ordering Note**: T023 depends on T020, T021. Phase 4 cannot start until T014 (Phase 3) is fully complete and `data/raw/` is populated.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T015 [P] [US2] Unit test for MICE convergence handling in `tests/unit/test_imputation.py` (verify exception catch and retry/exclude logic)
- [ ] T016 [P] [US2] Integration test for full imputation+estimation pipeline on a single seed in `tests/integration/test_pipeline.py`

### Implementation for User Story 2

- [ ] T017 [P] [US2] Implement Mean Imputation wrapper in `code/impute.py` with function signature:
  `def impute_mean(df: pd.DataFrame, cols: list) -> pd.DataFrame` returning the imputed DataFrame.
- [ ] T018 [P] [US2] Implement KNN Imputation (k=5) in `code/impute.py` with function signature:
  `def impute_knn(df: pd.DataFrame, k: int=5) -> pd.DataFrame` using `sklearn.impute.KNNImputer`.
- [ ] T019 [P] [US2] Implement MICE Imputation (multiple iterations) in `code/impute.py` with function signature:
  `def impute_mice(df: pd.DataFrame, n_iter: int=5) -> tuple[pd.DataFrame, bool]` returning (imputed_data, convergence_status).
- [ ] T020 [US2] Implement IPW estimator in `code/estimate_ate.py` with function signature:
  `def estimate_ipw(df: pd.DataFrame, treatment_col: str, outcome_col: str) -> dict` returning `{'ate': float, 'se': float}`.
- [ ] T021 [US2] Implement PSM estimator in `code/estimate_ate.py` with function signature:
  `def estimate_psm(df: pd.DataFrame, treatment_col: str, outcome_col: str) -> dict` returning `{'ate': float, 'se': float}`.
- [ ] T022 [US2] Implement Oracle (Complete Case) baseline in `code/estimate_ate.py` with function signature:
  `def estimate_oracle(df: pd.DataFrame, treatment_col: str, outcome_col: str) -> dict` returning `{'ate': float, 'se': float}`.
- [ ] T023 [US2] Integrate imputation and estimation modules in `code/run_simulation.py` to loop 200 replications, apply Mean/KNN/MICE, run IPW/PSM/Oracle, and save results to `data/processed/estimates_{seed}.parquet`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Quantify Bias and Perform Statistical Sensitivity Analysis (Priority: P3)

**Goal**: Calculate bias/RMSE, perform ART ANOVA, and sweep MNAR parameter $\beta$ to identify breakdown points.

**Independent Test**: Running the analysis script on 200 replications outputs a bias table, ART ANOVA p-value, and a sensitivity plot showing bias vs. $\beta$.

**Ordering Note**: T026 and T026a depend on T023. T029 and T030 depend on T026. Phase 5 cannot start until Phase 4 (specifically T023) is fully complete.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Unit test for ART ANOVA calculation in `tests/unit/test_analysis.py` (verify non-parametric test execution)
- [ ] T025 [P] [US3] Unit test for sensitivity sweep logic in `tests/unit/test_analysis.py` (verify breakdown point identification)

### Implementation for User Story 3

- [ ] T026 [US3] Implement bias and RMSE calculation in `code/analyze.py` with function signature:
  `def calculate_bias(results_df: pd.DataFrame, true_ate: float) -> pd.DataFrame` computing $|\hat{\tau}_{imp} - \tau_{true}|$ and RMSE, storing these as "Total Deviation".
- [ ] T027 [US3] Implement Repeated-Measures ART ANOVA in `code/analyze.py` using the `arttest` library (or manual implementation if `arttest` is unavailable) with function signature:
  `def run_art_anova(bias_df: pd.DataFrame, subject_col: str, method_col: str) -> dict` returning `{'f_stat': float, 'p_value': float}`. **Logic**: Must perform the Aligned Rank Transform (align residuals, rank, then test) to handle non-normality and the repeated-measures structure (multiple replications per seed).
- [ ] T028 [US3] Implement 95% Confidence Interval Coverage analysis in `code/analyze.py` with function signature:
  `def calculate_ci_coverage(results_df: pd.DataFrame, ci_level: float=0.95) -> float` returning the percentage of replications where the confidence interval (estimated_ate +/- critical_value*se) contains the true ATE ($\tau_{true}$).
- [ ] T029 [US3] Implement MNAR strength ($\beta$) sensitivity sweep in `code/analyze.py` with function signature:
  `def find_breakdown_point(bias_df: pd.DataFrame, betas: list, threshold: float=0.10) -> float | None` identifying the *first* value in the ordered set {0.1, 0.5, 1.0, 2.0} where Mean imputation bias > 10% of true ATE. **Logic**: Iterate through `betas` in ascending order; return the first `beta` where the condition is met, or `None` if no match is found.
- [ ] T030 [US3] Generate sensitivity plots (Bias vs. $\beta$) in `code/analyze.py` using `matplotlib`/`seaborn`, saving to `data/results/bias_vs_beta.png`.
- [ ] T031 [US3] Create final report generation script in `code/analyze.py` to output bias tables, ANOVA results, and coverage metrics to `data/results/final_report.md` (Markdown table + JSON summary).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Documentation updates in `docs/quickstart.md`, `docs/data-model.md`, and `docs/contracts.md` with specific content: installation steps, data schema, and API contracts.
- [ ] T033a [P] Refactor `code/impute.py` to reduce cyclomatic complexity to a lower magnitude and ensure type hints are complete for all public functions.
- [ ] T033b [P] Vectorize loops in `code/estimate_ate.py` to replace iterative ATE calculations with batch operations where possible.
- [ ] T034a [P] Implement multiprocessing in `code/run_simulation.py` to parallelize the 200 replications across available CPU cores.
- [ ] T034b [P] Add profiling logic to `code/run_simulation.py` to measure total runtime and verify completion within 6 hours on a 2-core CPU runner.
- [ ] T035 [P] Additional unit tests for edge cases (zero variance treatment, MICE failure, extreme sparsity) in `tests/unit/`.
- [ ] T036 Run `quickstart.md` validation by executing all commands in `docs/quickstart.md` and verifying end-to-end reproducibility (pass/fail criteria: no errors, outputs match expected).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
  - **Ordering Note**: T005 must complete before T010, T017, T020.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - **Ordering Note**: Phase 3 (T014) must complete before Phase 4 (T023) starts.
  - **Ordering Note**: Phase 4 (T023) must complete before Phase 5 (T026) starts.
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data generation output from US1 (T014 -> T023)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on estimation output from US2 (T023 -> T026)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utilities before services
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models/Utilities within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for ground-truth ATE recovery in tests/unit/test_data_gen.py"
Task: "Unit test for MNAR mechanism fidelity in tests/unit/test_data_gen.py"

# Launch foundational utilities for User Story 1 together:
Task: "Implement synthetic SCM data generator in code/generate_data.py"
Task: "Implement MNAR missingness injector in code/generate_data.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify ground truth and MNAR mechanism)
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
   - Developer A: User Story 1 (Data Generation)
   - Developer B: User Story 2 (Imputation & Estimation)
   - Developer C: User Story 3 (Analysis & Sensitivity)
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
- **Critical Ordering**: T005 -> T010/T017/T020; T014 -> T023; T023 -> T026; T026 -> T029/T030.
- **Critical Constraints**: T027 MUST use `arttest` (or manual ART implementation) for repeated-measures; T029 MUST return *first* beta or `None` via ascending iteration; T011a MUST verify beta recovery *before* imputation.