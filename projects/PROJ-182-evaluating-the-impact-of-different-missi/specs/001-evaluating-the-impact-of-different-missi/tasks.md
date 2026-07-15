# Tasks: Evaluating the Impact of Different Missing Data Mechanisms on Regression Discontinuity Designs

**Input**: Design documents from `/specs/001-evaluating-missing-data-rd/`
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

- [ ] T001 Create project structure per implementation plan: `code/src/generators`, `code/src/estimators`, `code/src/metrics`, `code/src/viz`, `code/tests/unit`, `code/tests/integration`, `data/`, `results/`, `contracts/`, `config/`
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (numpy>=1.24.0, pandas>=2.0.0, scikit-learn>=1.3.0, statsmodels>=0.14.0, seaborn>=0.12.0, matplotlib>=3.7.0, pyyaml>=6.0, pytest>=7.0.0)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create contract schemas in `contracts/` (`simulation_config.schema.yaml`, `estimation_result.schema.yaml`, `aggregated_metric.schema.yaml`) with JSON Schema structure ($schema, type, properties with types, required fields)
- [ ] T005 [P] Implement configuration loader in `code/src/config_loader.py` to read `config/simulation.yaml` (sample_size, true_effect, seed), `config/missingness.yaml` (rates, mechanisms), `config/estimation.yaml` (bandwidth_rule, imputation_count)
- [ ] T006 Create base data model classes in `code/src/models.py` (`SimulationConfig`: sample_size:int, true_effect:float, **exclusion_restriction:float**; `MissingnessPattern`: mask:bool; `EstimationResult`: estimate:float, se:float; `AggregatedMetric`: bias:float, rmse:float, coverage:float)
- [X] T007 Setup validation utility in `code/src/validators.py` to enforce contract schemas on all generated/processed data
- [X] T008 Configure logging infrastructure in `code/src/logging_config.py` to track simulation progress and errors
- [ ] T009 Create orchestration script `code/main.py` with placeholder logic to validate configuration before simulation starts

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Simulate RD Data with Controlled Missingness (Priority: P1) 🎯 MVP

**Goal**: Generate synthetic RD datasets with known ground truth and apply MCAR, MAR, MNAR missingness mechanisms.

**Independent Test**: Run `code/src/generators/rd_data.py` and `code/src/generators/missingness.py` with fixed seeds; verify missingness patterns via statistical tests (Chi-square for MCAR, correlation for MAR/MNAR).

### Implementation for User Story 1

- [ ] T013 [US1] Implement synthetic RD data generator in `code/src/generators/rd_data.py`: Formula `Y = beta0 + beta1*X + beta2*Z + tau*D + epsilon`, where `X~Uniform(-1,1)`, `Z~Normal(0,1)`, `D=(X>0)`, `epsilon~Normal(0, sigma)`. **Include exclusion restriction Z* (independent of X, affects missingness)**. *Note: Implements Linear Model as resolved in spec amendment.*
- [X] T014 [US1] Implement MCAR mask generator in `code/src/generators/missingness.py`: Read missingness rate from `config/missingness.yaml`; apply Bernoulli(p=rate) mask independent of all variables.
- [ ] T015 [US1] Implement MAR mask generator in `code/src/generators/missingness.py`: Logistic regression on Z (covariate) to generate mask; target rate from config.
- [ ] T016 [US1] Implement MNAR mask generator in `code/src/generators/missingness.py`: Probit link on Y (outcome) to generate mask; target rate from config. **Include exclusion restriction Z* logic for Heckman identification**. *Note: Uses ground truth Y for generation, but resulting dataset passed to estimators has Y masked.*
- [ ] T018 [US1] Add validation logic to ensure missingness patterns match definitions: **FAIL simulation** if MCAR p < 0.05 (dependence) OR if MAR/MNAR p >= 0.05 (no correlation). Explicitly map to US-1 Acceptance Scenario 1 (p > 0.05 for MCAR success) and Scenarios 2/3 (p < 0.05 for MAR/MNAR success).
- [ ] T017 [US1] Integrate generators into `code/main.py` to produce initial dataset and save to `data/simulated_raw.csv`

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation. **NOT Parallel** with implementation.

- [ ] T010 [US1] Unit test for MCAR mechanism in `code/tests/unit/test_missingness.py` (verify independence)
- [ ] T011 [US1] Unit test for MAR mechanism in `code/tests/unit/test_missingness.py` (verify correlation with covariate)
- [ ] T012 [US1] Unit test for MNAR mechanism in `code/tests/unit/test_missingness.py` (verify correlation with outcome)
- [ ] T044 [US1] Statistical verification task: Run Chi-square (MCAR) and Pearson correlation (MAR/MNAR) on `data/simulated_raw.csv`; assert p >= 0.05 for MCAR and p < 0.05 for MAR/MNAR.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute RD Estimators with Correction Strategies (Priority: P2)

**Goal**: Apply four estimation procedures (Naïve, MI, IPW, Selection) to generated datasets and compute estimates.

**Independent Test**: Run estimators on a small subset of data; verify output includes point estimates, standard errors, and handles convergence failures gracefully.

### Implementation for User Story 2

- [ ] T023 [P] [US2] Implement Naïve Local-Linear RD estimator in `code/src/estimators/naive_rd.py`: Use statsmodels or custom IK implementation; **fallback to 0.05 * (max(X)-min(X)) if IK < 0.05 * range (per Plan resolution of spec [deferred])**.
- [ ] T024 [P] [US2] Implement Multiple Imputation (MICE) in `code/src/estimators/multiple_imputation.py`: Use statsmodels.imputation.mice with multiple imputations and default convergence criteria; predictors: X, Z, D; Rubin's rules for pooling.
- [ ] T025 [P] [US2] Implement Inverse-Probability Weighting in `code/src/estimators/ipw.py`: Logistic regression on observed data only (X, Z, D).
- [ ] T026 [P] [US2] Implement Selection-Model (Heckman) in `code/src/estimators/selection_model.py`: Use statsmodels.sandbox.regression.gmm or manual MLE; **include Z* as instrument**; catch convergence error; **check Z* presence/collinearity before fit**; return NaN if invalid.
- [ ] T027 [US2] Create estimator orchestration in `code/src/estimators/runner.py` to apply all estimators to a single dataset
- [ ] T028 [US2] Integrate estimators into `code/main.py` to process simulated data and save `data/estimation_results.csv`
- [ ] T029 [US2] Add error handling for bandwidth selection failures and Heckman convergence issues (log specific error codes)

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for Naïve Local-Linear estimator in `code/tests/unit/test_naive_rd.py`
- [ ] T020 [P] [US2] Unit test for Multiple Imputation logic in `code/tests/unit/test_multiple_imputation.py`
- [ ] T021 [P] [US2] Unit test for IPW estimator in `code/tests/unit/test_ipw.py`
- [ ] T022 [P] [US2] Unit test for Selection-Model (Heckman) in `code/tests/unit/test_selection_model.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Aggregate Monte-Carlo Metrics and Visualize Results (Priority: P3)

**Goal**: Run a sufficient number of replications per configuration to ensure statistical robustness., aggregate metrics (Bias, RMSE, Coverage), and generate visualizations.

**Independent Test**: Run a reduced replication count (e.g., a small number) and verify output files contain correct columns and heatmap generation works.

### Implementation for User Story 3

- [ ] T032 [P] [US3] Implement aggregation logic in `code/src/metrics/aggregation.py`: **Bias = mean(est - true); RMSE = sqrt(mean((est - true)^2)); Coverage = mean(L <= true <= U)**. **Use nominal confidence level from `config/estimation.yaml` (default 0.95) as per SC-001**.
- [ ] T033 [P] [US3] Implement visualization script in `code/src/viz/heatmaps.py` (Bias and Coverage heatmaps)
- [ ] T034 [US3] Create Monte-Carlo loop in `code/main.py` to iterate **[deferred] times** per configuration (**3 mechanisms x 3 rates x 4 estimators = 36 configs **) as per FR-006.
- [ ] T035 [US3] Integrate aggregation into `code/main.py` to save `results/metrics.csv` and `results/best_estimators.json`
- [ ] T036 [US3] Generate final visualizations and save to `results/` (e.g., `bias_heatmap.png`, `coverage_heatmap.png`)
- [ ] T037 [US3] Add logic to identify and report the estimator with lowest RMSE for each mechanism

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US3] Integration test for aggregation logic in `code/tests/integration/test_aggregation.py`
- [ ] T031 [P] [US3] Integration test for visualization in `code/tests/integration/test_viz.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Documentation updates in `docs/` (README, quickstart, data-model)
- [ ] T039 Code cleanup and refactoring of estimator modules
- [ ] T040 Performance optimization: Ensure each replication runs <0.2s to meet 6-hour CI limit (**Vectorize loops using numpy; profile with timeit; ensure <0.2s/rep; if not, refactor or flag as critical failure**).
- [ ] T041 [P] Additional unit tests for edge cases (zero bandwidth, missingness rate = 0/1) in `code/tests/unit/`
- [ ] T042 Security hardening: Validate all user inputs and configuration files against schemas
- [ ] T043 Run quickstart.md validation to ensure end-to-end reproducibility
- [ ] T045 [P] **Run feasibility benchmark**: Execute multiple replications of all 36 configs; verify total time < 6 hours (scaled) before full run.

---

## Research Notes

**FR-001 ("triangular kernel model")**: The spec originally mandated generating data with a "triangular kernel model". However, kernels are used for *estimation* (local regression), not *generation* of synthetic data. The Plan clarifies a "Linear Model" approach. **Task T012 has been added to update spec.md to reflect this resolution.** The implementation follows the Plan's Linear Model (T013).

**SC-001 ("[deferred]" nominal level)**: The spec defers the nominal confidence level. The Plan defaults to 0.95. T032 implements this as configurable (default 0.95).

**FR-003 ("[deferred]" bandwidth floor)**: The spec defers the bandwidth floor. The Plan resolves this to 0.05. T023 implements 0.05 with a citation to the Plan.

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

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- **Note**: Tests (T010-T012, T019-T022, etc.) are NOT parallel with implementation; they depend on code existence.
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all generators for User Story 1 together (after T013 is done):
Task: "Implement MCAR mask generator in code/src/generators/missingness.py"
Task: "Implement MAR mask generator in code/src/generators/missingness.py"
Task: "Implement MNAR mask generator in code/src/generators/missingness.py"
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
 - Developer A: User Story 1 (Data Generation)
 - Developer B: User Story 2 (Estimators)
 - Developer C: User Story 3 (Aggregation & Viz)
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
- **Feasibility Check**: All estimators must run on CPU-only CI (A small number of cores, a limited amount of RAM). No GPU, no 8-bit quantization. Use `statsmodels` for Heckman/MICE, `scikit-learn` for IPW.
- **Data Integrity**: All synthetic data must be generated on-the-fly with pinned seeds. No fake/fabricated results allowed.
- **Convergence Handling**: Heckman model must catch convergence errors and return NaN, not crash the pipeline.
- **Bandwidth Fallback**: Imbens-Kalyanaraman rule must have a 0.05 floor fallback (per Plan) to prevent division by zero.
- **Z* Requirement**: Exclusion restriction Z* is mandatory for Heckman identification (Plan).
- **Research Gap Resolution**: The spec defers specific missingness rates and bandwidth floors. The plan resolves these to 0.05 (bandwidth) and 0.95 (nominal level) but requires the implementation to be configurable. T014, T015, T016, T023, and T032 explicitly handle these values via configuration, ensuring the code is robust to any valid input.
- **Execution Order Correction**: T034 (Monte-Carlo loop) is scheduled AFTER T032 (Aggregation logic) to ensure the aggregation logic is available for the loop to call. T035 saves the final results.
- **Heckman Identification**: T026 explicitly includes the exclusion restriction Z* as required by the plan to ensure the Heckman model is identified.
- **IPW Blindness**: T025 ensures IPW uses only observed data, preventing leakage of ground truth.
- **Naïve Baseline**: T023 implements listwise deletion as the Naïve baseline.
- **Convergence Handling**: T026 and T029 ensure convergence failures are caught and logged, preventing pipeline crashes.
- **Bandwidth Fallback**: T023 implements the fallback logic for the IK rule.
- **Missingness Verification**: T018 ensures the generated missingness patterns match the theoretical definitions.
- **Performance Optimization**: T040 ensures the simulation runs within the 6-hour CI limit.
- **Feasibility Benchmark**: T045 ensures the full simulation is feasible before running the full A sufficient number of replications will be conducted to ensure statistical robustness and reliable estimation of model performance..
- **Data Hygiene**: All data is synthetic and generated on-the-fly, ensuring no PII or external dataset issues.
- **Reproducibility**: All random seeds are pinned in `config/simulation.yaml`.
- **Contract Validation**: All outputs are validated against the contract schemas in `contracts/`.
- **Versioning Discipline**: All artifacts carry a content hash, and the `state` YAML is updated on any change.
- **Single Source of Truth**: All metrics trace to `results/metrics.csv`.
- **Simulation Transparency**: All estimators are encapsulated in `code/estimators/` with parameters in `config/estimation.yaml`.
- **Missingness Protocol**: Mechanisms are strictly implemented per spec, with seeds and rates logged.
- **Inference Framing**: Findings are descriptive of estimator properties, not causal claims.
- **Threshold Justification**: The IK rule is the community standard, with sensitivity analysis over {0.5, 1.0, 1.5}.
- **Collinearity**: Running variable and covariates are generated independently.
- **Measurement Validity**: `statsmodels` and `scikit-learn` are assumed validated.
- **Compute Feasibility**: {{claim:c_7081c5f3}} (Wikipedia: Tor tambroides, https://en.wikipedia.org/wiki/Tor_tambroides) per configuration are assumed to complete within 6 hours on CPU cores, provided each replication is <0.2s.