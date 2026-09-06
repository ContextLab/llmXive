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

- [X] T000 [P] Write Citation Verification Script: **Create** `code/scripts/verify_citation.py`. This script must invoke the Reference-Validator Agent via the project's CLI interface (e.g., `python -m code.scripts.run_validator --target "Concrete Compressive Strength"`) to verify the dataset citation. **Output**: The script must save the verified citation details to `data/raw/uci_citation_verified.json` and update `state/projects/PROJ-034-quantifying-uncertainty-in-small-sample-.yaml` with the verification status. **Constraint**: Do not instruct the user to manually run agents; the script must perform the verification logic using the CLI. <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 [P] Create Project Directory Structure: **Create** the entire directory tree defined in `plan.md` (including `code/simulation`, `code/models`, `code/metrics`, `code/validation`, `code/plots`, `code/scripts`, `data/raw`, `data/simulated`, `data/results`, `tests/unit`, `tests/integration`, `docs/paper`). **Verification**: After creation, run `tree` (or equivalent) and save the output to `tree_manifest.txt` in the project root to prove the structure exists.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 [P] Initialize Python 3.11 project: Create `requirements.txt` with pinned versions (numpy, pandas, scipy, scikit-learn, cmdstanpy, matplotlib, seaborn, pyyaml, pytest) and run `python -m venv venv && pip install -r requirements.txt`
- [X] T003 [P] Configure linting: Create `pyproject.toml` with `[tool.black]` (line-length=88) and `[tool.flake8]` (max-line-length=88, exclude=venv) sections
- [X] T005 [P] Implement `code/simulation/config.py` defining `SimulationConfig` schema (N, predictors, correlation matrix, noise, true coefficients)
- [X] T006 [P] Implement `code/simulation/engine.py`: **Fully implement** the `calculate_vif` function (FR-006) and `generate_synthetic_data` with the exact signature: `def generate_synthetic_data(config: SimulationConfig, seed: int) -> DatasetInstance`. The `DatasetInstance` must include fields: `X` (np.ndarray), `y` (np.ndarray), `beta_true` (np.ndarray), `vif_scores` (dict). **Do not use a skeleton**; provide a complete, working implementation. This task is the **producer** of the VIF calculation logic. **Dependency**: This task depends on T005 completion.
- [ ] T007 [P] Create `data/raw/`, `data/simulated/`, and `data/results/` directory structure with `.gitkeep` files in each
- [X] T009 [P] Setup pytest configuration: Create `pytest.ini` (addopts="-v --tb=short") and `tests/conftest.py` with shared fixtures

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Simulation Engine for Coverage Probability Estimation (Priority: P1) 🎯 MVP

**Goal**: Generate synthetic datasets with controlled sample sizes ($N < 50$) and specific correlation structures to test coverage.

**Independent Test**: Run a single simulation batch with fixed seeds; verify generated data matrices have requested correlation coefficients and true parameters are stored.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for correlation matrix generation in `tests/unit/test_simulation.py`: Verify that the generated correlation matrix matches the target $\rho$ within an acceptable tolerance.
- [X] T011 [P] [US1] Unit test for rank-checking logic in `tests/unit/test_simulation.py`: Verify handling of $N=5$ or rank-deficient cases with explicit assertions.

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/simulation/engine.py`: Generate $X$ matrix with Cholesky decomposition for target correlation
- [X] T013 [US1] Implement `code/simulation/engine.py`: Generate $y$ vector using true coefficients and Gaussian noise
- [X] T014 [US1] Implement `code/simulation/engine.py`: Add full VIF calculation integration and flagging (VIF > 10 (2005.02245, https://arxiv.org/abs/2005.02245) [UNRESOLVED-CLAIM: c_b53a36c1 — status=not_enough_info]) for collinearity verification (FR-006), **persisting the flag in the `DatasetInstance` metadata** saved to `data/simulated/`. **Note**: Use the `calculate_vif` function implemented in **T006**; do not re-implement the logic. This task focuses on integration and metadata persistence.
- [X] T015 [US1] Implement `code/simulation/engine.py`: Add positive semi-definite check and auto-regeneration logic for invalid matrices (limited number of attempts per config)
- [X] T016 [US1] Implement `code/simulation/engine.py`: Save `DatasetInstance` objects (X, y, $\beta_{true}$) to `data/simulated/` with metadata (JSON). **Explicitly mandate**: Convert `beta_true` (np.ndarray) to a **list** for JSON serialization and preserve the `dtype` in the metadata JSON to ensure ground truth integrity (FR-001).
- [ ] T017 [US1] Add logging for simulation run parameters: Write to `data/results/simulation.log` in JSON format with fields: `N`, `rho`, `seed`, `duration`, `vif_max`, **AND** `regeneration_attempts` and `regeneration_reason` to verify the "stable" assumption against actual behavior.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Comparative Uncertainty Quantification Pipeline (Priority: P2)

**Goal**: Run OLS, Non-parametric Bootstrap, and Bayesian Regression on simulated data and calculate empirical coverage.

**Independent Test**: Feed a single pre-generated dataset; verify all three methods produce intervals and binary "covered" flags.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for OLS interval calculation in `tests/unit/test_models.py`
- [X] T019 [P] [US2] Unit test for Bootstrap BCa interval calculation in `tests/unit/test_models.py`
- [X] T020 [P] [US2] Unit test for Bayesian convergence checks (R-hat) in `tests/unit/test_models.py`

### Implementation for User Story 2

- [X] T021 [P] [US2] Implement `code/models/ols.py`: OLS fit and standard 95% confidence interval calculation
- [X] T022 [US2] Implement `code/models/bootstrap.py`: Non-parametric bootstrap with BCa interval correction
- [X] T023 [US2] Implement `code/models/bayesian.py`: CmdStanPy model definition with Normal(0, 10) priors and Half-Cauchy scale
- [ ] T024 [US2] Implement `code/models/bayesian.py`: Execution wrapper (multiple chains, a sufficient number of samples per chain, an adequate warmup period) and divergent transition check
- [ ] T025 [US2] Implement `code/metrics/coverage.py`: Logic to compare intervals against $\beta_{true}$ and return binary "covered" status
- [ ] T026 [US2] Implement `code/main.py`: Orchestration loop for Monte Carlo replications. **CRITICAL**: Implement a **fixed `for` loop over N=200 replications **.
 1. **Timeout/Budget**: Enforce a **total execution time limit of 6 hours [UNRESOLVED-CLAIM: c_b3f57302 — status=not_enough_info] ** for the entire 200-run loop (SC-004). If the total time exceeds 6 hours, log a warning and stop, but do not use a per-run timeout that exceeds the total budget.
 2. **Coverage Logic**: For each run, if the model fails convergence (R-hat > 1.05 [UNRESOLVED-CLAIM: c_74ab97f2 — status=refuted]) or VIF > 10, **flag the run as "INVALID"** and **exclude it from the final coverage calculation denominator**. Do NOT count it as "NOT COVERED". Log these invalid runs separately.
 3. **Artifact Output**: Save **individual run results** to `data/results/run_{i}.json` for every iteration `i` across the full experimental range., containing: `seed`, `vif_max`, `r_hat`, `covered` (bool), `interval_width`, `method_id`, and `is_valid` (bool).
 4. **Aggregation**: Output aggregated results to `data/results/coverage_metrics.json` with the **exact schema**:
 ```json
 {
 "coverage_rate": float,
 "interval_width": float,
 "total_n": 200,
 "valid_n": int,
 "invalid_run_count": int,
 "failure_reasons": {"r_hat_fail": int, "vif_fail": int, "other": int},
 "method_id": "string"
 }
 ```
 **Dependency**: Requires T006 (engine) and T021-T025 (models) to be complete.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4.5: Comparative Analysis (Critical Dependency for US3)

**Goal**: Generate comparative metrics and plots for all three methods to assess trade-offs, as required by FR-007 and SC-003.

- [ ] T027.5 [Cross-Story] Implement `code/scripts/analyze_comparative.py`: **Read** `data/results/coverage_metrics.json` and individual run logs to generate **comparative metrics and the calibration plot artifact**.
 1. **Binning Logic**: **Aggregate data across the 200 replications** by binning the results based on **realized VIF** (e.g., Low, Medium, High) or **N**. This is required to generate a statistically valid calibration curve.
 2. **Algorithm**: Calculate coverage deviation and average interval width for OLS, Bootstrap, and Bayesian **within each bin**.
 3. **Plot Generation**: **Generate the calibration plot** (Interval Width vs. Coverage Probability) comparing all three methods side-by-side. **Save the plot** to `data/results/calibration_plot.png`. The plot must explicitly show Interval Width on the X-axis and Coverage Probability on the Y-axis, with points representing the binned aggregates.
 4. **Provenance**: Embed the **content hash** of the input data (`coverage_metrics.json`) into the plot metadata or filename to satisfy Constitution Principle IV.
 5. **Output**: Save `data/results/comparative_metrics.json` with schema: `{"methods": [{"name": "string", "coverage": float, "width": float, "deviation": float}], "calibration_plot_path": "data/results/calibration_plot.png", "input_hash": "string"}`.
 6. **Dependency**: **Must run only after T026 completes successfully**. This task replaces the previous T027 and T034, consolidating the logic.

**Checkpoint**: Comparative analysis complete; US3 can now proceed.

---

## Phase 5: User Story 3 - Real-World Validation on UCI Dataset (Priority: P3)

**Goal**: Apply methods to a real-world small-sample dataset (UCI Concrete) to confirm simulation findings.

**Independent Test**: Load UCI Concrete, subsample to $N=40$, run all three methods, verify output includes intervals and diagnostic plots.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Integration test for UCI dataset loading and subsampling in `tests/integration/test_validation.py`

### Implementation for User Story 3

- [ ] T029 [US3] Implement `code/validation/uci_runner.py`: Fetch UCI Concrete Compressive Strength dataset using the **verified URL from T000** and cache to `data/raw/`.
- [ ] T030 [US3] Implement `code/validation/uci_runner.py`: **Subsample logic** with a deterministic configuration space.
 1. **Configuration Space**: Iterate over `N=40` and feature subsets of size 3, 4, 5, and 6 [UNRESOLVED-CLAIM: c_01d9f77d — status=not_enough_info].
 2. **Validation**: For each configuration, check if $N > p$. If $N \le p$, **log a warning** "Rank-deficient: N={N} <= p={p}" and **continue** to the next configuration.
 3. **Graceful Failure**: If **no valid subsample** is found after exhausting the entire configuration space, **log a warning** "VALIDATION_SKIPPED: No valid subsample found for N < 50 and p >= 3" and **skip the validation step** (do not raise a RuntimeError).
 4. **Output**: Save the **first valid subsample** to `data/raw/uci_subsampled.csv` with metadata confirming predictor count and N > p status.
 5. **Dependency**: Depends on T029.
- [ ] T031 [US3] Implement `code/validation/uci_runner.py`: **Run all three methods** (OLS, Bootstrap, Bayesian) on the subsampled data. **Dependency**: **Explicitly depends on T030 (data prep) and model implementations (T021-T024)**. Generate interval estimates for all methods and save to `data/results/uci_validation_results.json`. **Note**: This task is independent of T027.5 (simulation analysis).
- [ ] T032 [US3] Implement `code/validation/uci_runner.py`: Generate interval stability metrics and width comparison (Bayesian vs OLS)
- [ ] T033 [US3] Implement `code/validation/uci_runner.py`: Generate diagnostic plots (posterior distributions, interval widths) saved to `data/results/`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final reporting

- [ ] T035 [P] Create `code/scripts/run_full_simulation.sh` for reproducible end-to-end execution on CI
- [ ] T036 [P] Implement `code/scripts/verify_runtime.py`: **Create a script** that reads `data/results/runtime_log.json` (generated by the simulation runner) and **exits with code 1** if `total_duration` > 21600s (6 hours). **Update** `run_full_simulation.sh` to call this script after the simulation and fail the build if it returns 1. **Dependency**: Requires T026 to be complete and functional.
- [ ] T037 [P] Update `README.md` with execution instructions (Installation, Usage, Data Flow) and a Mermaid diagram. **Diagram Content**: "Data Flow: Simulation (engine.py) -> Models (ols, bootstrap, bayesian) -> Metrics (coverage.py) -> Results (json/csv)".
- [ ] T038 [P] Run `pytest` on all unit and integration tests; ensure **full pass rate** and generate `pytest-report.xml` as the required artifact.
- [ ] T039 [P] Generate `specs/001-quantifying-uncertainty-in-small-sample/research.md` draft using the project template. **Required Sections**: Abstract (summary of methods), Methods (detailed simulation setup), Results (placeholder for coverage metrics), Discussion (implications of small-sample uncertainty).
- [ ] T040 [P] Add explicit error handling in `code/simulation/engine.py` and `code/validation/uci_runner.py` to fail loudly if real data fetch fails, ensuring no synthetic fallback is used (Constitution Principle II).
- [ ] T041 [P] Add a final validation script `code/scripts/validate_results.py` that checks `data/results/coverage_metrics.json` for expected keys and non-zero valid counts before generating plots.

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
- **User Story 3 (P3)**: Depends on data preparation (T030) and model implementations (T021-T024). **Independent** of T027.5 (simulation analysis).

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
- **Retry Logic**: Simulation (T026) must run a fixed number of replications (200) and count invalid runs separately, excluding them from coverage calculation.