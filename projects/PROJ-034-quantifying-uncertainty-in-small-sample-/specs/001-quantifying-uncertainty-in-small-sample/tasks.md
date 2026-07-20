# Tasks: Quantifying Uncertainty in Small Sample Regression Models

**Input**: Design documents from `/specs/001-quantify-uncertainty-small-sample/`
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

 Tasks MUST be organized by user story so each story can:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 0: Research & Verification (Blocking Prerequisite)

**Purpose**: Verify external sources and citations before implementation begins.

**⚠️ CRITICAL**: No implementation tasks can begin until this phase is complete.

- [X] T000 [P] Verify UCI Dataset Citation: Consult the primary source for the "Concrete Compressive Strength" dataset (UCI Machine Learning Repository). **Invoke the Reference-Validator Agent** to verify the dataset ID, URL, and citation details against the plan's assumptions. Record the verified citation in `research.md` and confirm the dataset contains sufficient features (≥3 predictors) and sample size potential. **Output**: `data/raw/uci_citation_verified.json` containing the verified URL and citation string, **and update `state/projects/PROJ-034-quantifying-uncertainty-in-small-sample-.yaml` with the verification status** as required by Constitution Principle II.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan: **Create the directory tree**: `code/simulation`, `code/models`, `code/metrics`, `code/validation`, `code/plots`, `code/scripts`, `data/raw`, `data/simulated`, `data/results`, `tests/unit`, `tests/integration`, `docs/paper`.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 [P] Initialize Python 3.11 project: Create `requirements.txt` with pinned versions (numpy, pandas, scipy, scikit-learn, cmdstanpy, matplotlib, seaborn, pyyaml, pytest) and run `python -m venv venv && pip install -r requirements.txt`
- [ ] T003 [P] Configure linting: Create `pyproject.toml` with `[tool.black]` (line-length=88) and `[tool.flake8]` (max-line-length=88, exclude=venv) sections
- [ ] T004 [P] Setup `code/` directory structure: `simulation/`, `models/`, `metrics/`, `validation/`, `plots/`, `scripts/`
- [ ] T005 [P] Implement `code/simulation/config.py` defining `SimulationConfig` schema (N, predictors, correlation matrix, noise, true coefficients)
- [ ] T006 [P] Implement `code/simulation/engine.py`: **Fully implement** the `calculate_vif` function (FR-006) and `generate_synthetic_data` with the exact signature: `def generate_synthetic_data(config: SimulationConfig, seed: int) -> DatasetInstance`. The `DatasetInstance` must include fields: `X` (np.ndarray), `y` (np.ndarray), `beta_true` (np.ndarray), `vif_scores` (dict). **Do not use a skeleton**; provide a complete, working implementation.
- [ ] T007 [P] Create `data/raw/`, `data/simulated/`, and `data/results/` directory structure with `.gitkeep` files in each
- [ ] T009 [P] Setup pytest configuration: Create `pytest.ini` (addopts="-v --tb=short") and `tests/conftest.py` with shared fixtures

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Simulation Engine for Coverage Probability Estimation (Priority: P1) 🎯 MVP

**Goal**: Generate synthetic datasets with controlled sample sizes ($N < 50$) and specific correlation structures to test coverage.

**Independent Test**: Run a single simulation batch with fixed seeds; verify generated data matrices have requested correlation coefficients and true parameters are stored.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for correlation matrix generation in `tests/unit/test_simulation.py` (Verify $\rho$ within a predefined tolerance threshold.)
- [ ] T011 [P] [US1] Unit test for rank-checking logic in `tests/unit/test_simulation.py` (Verify handling of $N=5$ or rank-deficient cases)

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `code/simulation/engine.py`: Generate $X$ matrix with Cholesky decomposition for target correlation
- [ ] T013 [US1] Implement `code/simulation/engine.py`: Generate $y$ vector using true coefficients and Gaussian noise
- [ ] T014 [US1] Implement `code/simulation/engine.py`: Add full VIF calculation and flagging (VIF > 10) for collinearity verification (FR-006), **persisting the flag in the `DatasetInstance` metadata** saved to `data/simulated/`. (Note: `calculate_vif` is already implemented in T006; this task focuses on integration and metadata persistence).
- [ ] T015 [US1] Implement `code/simulation/engine.py`: Add positive semi-definite check and auto-regeneration logic for invalid matrices (limited number of attempts per config)
- [ ] T016 [US1] Implement `code/simulation/engine.py`: Save `DatasetInstance` objects (X, y, $\beta_{true}$) to `data/simulated/` with metadata (JSON). **Explicitly mandate serializing the `beta_true` vector** into the JSON output to satisfy FR-001.
- [ ] T017 [US1] Add logging for simulation run parameters: Write to `data/results/simulation.log` in JSON format with fields: `N`, `rho`, `seed`, `duration`, `vif_max`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Comparative Uncertainty Quantification Pipeline (Priority: P2)

**Goal**: Run OLS, Non-parametric Bootstrap, and Bayesian Regression on simulated data and calculate empirical coverage.

**Independent Test**: Feed a single pre-generated dataset; verify all three methods produce intervals and binary "covered" flags.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for OLS interval calculation in `tests/unit/test_models.py`
- [ ] T019 [P] [US2] Unit test for Bootstrap BCa interval calculation in `tests/unit/test_models.py`
- [ ] T020 [P] [US2] Unit test for Bayesian convergence checks (R-hat) in `tests/unit/test_models.py`

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement `code/models/ols.py`: OLS fit and standard 95% confidence interval calculation
- [ ] T022 [US2] Implement `code/models/bootstrap.py`: Non-parametric bootstrap with BCa interval correction
- [ ] T023 [US2] Implement `code/models/bayesian.py`: CmdStanPy model definition with Normal(0, 10) priors and Half-Cauchy scale
- [ ] T024 [US2] Implement `code/models/bayesian.py`: Execution wrapper (multiple chains, a sufficient number of samples per chain, an adequate warmup period) and divergent transition check
- [ ] T025 [US2] Implement `code/metrics/coverage.py`: Logic to compare intervals against $\beta_{true}$ and return binary "covered" status
- [ ] T026 [US2] Implement `code/main.py`: Orchestration loop for Monte Carlo replications. **CRITICAL**: Implement a **fixed `for` loop over N=200 replications**. For each run, if the model fails convergence (R-hat > 1.05) or VIF > 10, **flag it as under-coverage or record the exclusion reason in a separate log**, but **DO NOT resample**. Output aggregated results to `data/results/coverage_metrics.json` with the **exact schema**:
 ```json
 {
 "coverage_rate": float,
 "interval_width": float,
 "valid_n": int,
 "invalid_run_count": int,
 "failure_reasons": {"r_hat_fail": int, "vif_fail": int, "other": int},
 "method_id": "string"
 }
 ```
- [ ] T027 [US2] Implement `code/main.py`: Filter logic to exclude runs with R-hat > 1.05 or VIF > 10 from final coverage calculation; output filtered results to `data/results/filtered_metrics.json`. Ensure this task runs only after T026 completes successfully.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4.5: Comparative Analysis (Critical Dependency for US3)

**Goal**: Generate comparative metrics and plots for all three methods to assess trade-offs, as required by FR-007 and SC-003.

- [ ] T027.5 [US2] Implement `code/scripts/analyze_comparative.py`: Analyze `data/results/coverage_metrics.json` to generate **comparative metrics and calibration plots for all three methods**. **Algorithm**: Calculate coverage deviation and average interval width for OLS, Bootstrap, and Bayesian. **Output**: `data/results/comparative_metrics.json` with schema: `{"methods": [{"name": "string", "coverage": float, "width": float, "deviation": float}], "calibration_plot_path": "string"}`. **The plot must show all three methods side-by-side**. **Dependency**: Requires T027 to be complete.

**Checkpoint**: Comparative analysis complete; US3 can now proceed.

---

## Phase 5: User Story 3 - Real-World Validation on UCI Dataset (Priority: P3)

**Goal**: Apply methods to a real-world small-sample dataset (UCI Concrete) to confirm simulation findings.

**Independent Test**: Load UCI Concrete, subsample to $N=40$, run all three methods, verify output includes intervals and diagnostic plots.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Integration test for UCI dataset loading and subsampling in `tests/integration/test_validation.py`

### Implementation for User Story 3

- [ ] T029 [US3] Implement `code/validation/uci_runner.py`: Fetch UCI Concrete Compressive Strength dataset using the **verified URL from T000** and cache to `data/raw/`.
- [ ] T030 [US3] Implement `code/validation/uci_runner.py`: Subsample logic to $N < 50$ using stratified random sampling with **explicit validation ensuring at least 3 predictors are retained**. If N <= p (sample size <= predictors), **SKIP that specific configuration, log a warning: "Rank-deficient: N={N} <= p={p}", and continue to the next configuration**. Do NOT raise a hard exception. Output validated subsample to `data/raw/uci_subsampled.csv` with metadata confirming predictor count and N > p status (or log of skipped attempts).
- [ ] T031 [US3] Implement `code/validation/uci_runner.py`: **Run all three methods** (OLS, Bootstrap, Bayesian) on the subsampled data. **Dependency**: Depends on T027.5 and T030. Generate interval estimates for all methods and save to `data/results/uci_validation_results.json`.
- [ ] T032 [US3] Implement `code/validation/uci_runner.py`: Generate interval stability metrics and width comparison (Bayesian vs OLS)
- [ ] T033 [US3] Implement `code/validation/uci_runner.py`: Generate diagnostic plots (posterior distributions, interval widths) saved to `data/results/`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final reporting

- [ ] T034 [P] Implement `code/plots/calibration.py` to generate final publication-ready calibration plots (Interval Width vs. Coverage) for all three methods (FR-007). **Dependency**: Requires comparative metrics from T027.5.
- [ ] T035 [P] Create `code/scripts/run_full_simulation.sh` for reproducible end-to-end execution on CI
- [ ] T036 [P] Implement `code/scripts/verify_runtime.py`: Automated script to run the full simulation (multiple runs) and generate `data/results/runtime_log.json` with `total_duration` field; **add a check in run_full_simulation.sh that FAILS the build (exit code 1) if `total_duration` > 21600s (6 hours)**. **Dependency**: Requires T027 to be complete and functional.
- [ ] T037 [P] Update `README.md` with execution instructions (Installation, Usage, Data Flow) and a Mermaid diagram. **Diagram Content**: "Data Flow: Simulation (engine.py) -> Models (ols, bootstrap, bayesian) -> Metrics (coverage.py) -> Results (json/csv)".
- [ ] T038 [P] Run `pytest` on all unit and integration tests; ensure **full pass rate** and generate `pytest-report.xml` as the required artifact.
- [ ] T039 [P] Generate `specs/001-quantify-uncertainty-small-sample/research.md` draft using the project template. **Required Sections**: Abstract (summary of methods), Methods (detailed simulation setup), Results (placeholder for coverage metrics), Discussion (implications of small-sample uncertainty).
- [ ] T040 [P] Add explicit error handling in `code/simulation/engine.py` and `code/validation/uci_runner.py` to fail loudly if real data fetch fails, ensuring no synthetic fallback is used (Constitution Principle II).
- [ ] T041 [P] Add a final validation script `code/scripts/validate_results.py` that checks `data/results/coverage_metrics.json` for expected keys and non-zero valid counts before generating plots.
- [ ] T042 [P] Implement `code/scripts/post_hoc_analysis.py`: Generate a final report comparing the simulation results (US2) with the real-world validation (US3), discussing any discrepancies in coverage or interval width.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Research)**: No dependencies - can start immediately. **Blocks all implementation**.
- **Setup (Phase 1)**: Depends on Phase 0 - can start immediately after.
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion.
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories.
- **User Story 2 (P2)**: Depends on User Story 1 (requires `data/simulated/` output).
- **User Story 3 (P3)**: Depends on User Story 2 (requires comparative metrics from T027.5) AND data preparation (T030).

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation.
- Models before services.
- Services before endpoints.
- Core implementation before integration.
- Story complete before moving to next priority.

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel.
- All Foundational tasks marked [P] can run in parallel **except T006 which depends on T005 completion**.
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows).
- All tests for a user story marked [P] can run in parallel.
- Models within a story marked [P] can run in parallel.
- Different user stories can be worked on in parallel by different team members.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for correlation matrix generation in tests/unit/test_simulation.py"
Task: "Unit test for rank-checking logic in tests/unit/test_simulation.py"

# Launch all models for User Story 1 together:
Task: "Implement code/simulation/engine.py: Generate X matrix"
Task: "Implement code/simulation/engine.py: Generate y vector"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Research
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently (verify correlation and ground truth storage)
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Core comparison logic)
4. Add User Story 3 → Test independently → Deploy/Demo (Real-world validation)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together.
2. Once Foundational is done:
 - Developer A: User Story 1 (Simulation Engine)
 - Developer B: User Story 2 (Model Pipeline) - *Can start once T006 is done*
 - Developer C: User Story 3 (Validation) - *Can start once T007 is done*
3. Stories complete and integrate independently.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Constraint**: All tasks must run on CPU-only CI with limited cores and constrained memory. Do not use GPU-specific libraries or 8-bit quantization.
- **Data**: Ensure UCI dataset fetch uses the verified URL from T000.
- **Real Data Only**: No synthetic data generation for the validation dataset (US3); must use the real UCI Concrete dataset.
- **Runtime**: Ensure 200 Monte Carlo replications complete within 6 hours on free-tier CI. **Hard fail if exceeded**.
- **Fail Loudly**: Data loaders must raise exceptions on fetch failure; no synthetic fallbacks allowed.
- **Retry Logic**: Simulation (T026) must run a fixed number of replications (200) and flag invalid runs, not resample.