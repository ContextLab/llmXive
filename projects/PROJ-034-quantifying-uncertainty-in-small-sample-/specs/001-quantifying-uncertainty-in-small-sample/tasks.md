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

**⚠️ CRITICAL**: No implementation tasks can begin until this phase is complete. This task is a hard blocking prerequisite for the entire project.

- [ ] T000 [S] [Blocking] Verify UCI Citation via Reference-Validator Agent: **Invoke** the Reference-Validator Agent to fetch and verify the "Concrete Compressive Strength" dataset metadata from the UCI Machine Learning Repository. **Output**: The agent must save the verified citation details to `data/raw/uci_citation_verified.json` and update `state/projects/PROJ-034-quantifying-uncertainty-in-small-sample-.yaml` with the verification status. **Schema**: Update the YAML file with key `uci_citation_verified: {status: "verified", url: "<url>", timestamp: "<ISO8601>"}`. **Constraint**: This task must use the Reference-Validator Agent workflow, NOT a custom script. **Note**: This task is a hard blocking prerequisite; it cannot run in parallel with Setup or Foundational tasks that depend on the verified URL.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 [P] Create Project Directory Structure: **Create** the entire directory tree defined in `plan.md` (including `code/simulation`, `code/models`, `code/metrics`, `code/validation`, `code/plots`, `code/scripts`, `data/raw`, `data/simulated`, `data/results`, `tests/unit`, `tests/integration`, `docs/paper`). **Verification**: After creation, run `tree` (or equivalent) and save the output to `tree_manifest.json` in the project root. **Schema**: The manifest must be a JSON list of absolute paths for every created directory and file.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 [P] Initialize Python 3.11 project: Create `requirements.txt` with pinned versions (numpy, pandas, scipy, scikit-learn, cmdstanpy, matplotlib, seaborn, pyyaml, pytest) and run `python -m venv venv && pip install -r requirements.txt`
- [X] T003 [P] Configure linting: Create `pyproject.toml` with `[tool.black]` (line-length=88) and `[tool.flake8]` (max-line-length=88, exclude=venv) sections
- [X] T005 [P] Implement `code/simulation/config.py` defining `SimulationConfig` schema (N, predictors, correlation matrix, noise, true coefficients)
- [X] T006A [P] Implement `code/simulation/engine.py`: **Fully implement** the `calculate_vif` function (FR-006). **Input**: `X` (np.ndarray). **Output**: `dict` mapping feature names to VIF scores. **Logic**: Use `sklearn.linear_model.LinearRegression` to calculate R-squared for each predictor against others. **Dependency**: This task is the producer of the VIF calculation logic.
- [X] T006B [P] Implement `code/simulation/engine.py`: **Fully implement** the `generate_synthetic_data` function with the exact signature: `def generate_synthetic_data(config: SimulationConfig, seed: int) -> DatasetInstance`. **Output**: `DatasetInstance` with fields: `X` (np.ndarray), `y` (np.ndarray), `beta_true` (np.ndarray), `vif_scores` (dict). **Logic**: Use Cholesky decomposition for correlation, add Gaussian noise. **Dependency**: This task depends on T006A completion.
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

- [X] T012 [P] [US1] Implement `code/simulation/engine.py`: Generate $X$ matrix with Cholesky decomposition for target correlation. **Dependency**: Requires T006B.
- [X] T013 [US1] Implement `code/simulation/engine.py`: Generate $y$ vector using true coefficients and Gaussian noise. **Dependency**: Requires T012.
- [X] T014 [US1] Implement `code/simulation/engine.py`: Add full VIF calculation integration and flagging (VIF > 10) for collinearity verification (FR-006), **persisting the flag in the `DatasetInstance` metadata** saved to `data/simulated/`. **Note**: Use the `calculate_vif` function implemented in **T006A**; do not re-implement the logic. This task focuses on integration and metadata persistence.
- [X] T015 [US1] Implement `code/simulation/engine.py`: Add positive semi-definite check and auto-regeneration logic for invalid matrices (limited number of attempts per config).
- [X] T016 [US1] Implement `code/simulation/engine.py`: Save `DatasetInstance` objects (X, y, $\beta_{true}$) to `data/simulated/` with metadata (JSON). **Explicitly mandate**: Convert `beta_true` (np.ndarray) to a **list** for JSON serialization and preserve the `dtype` in the metadata JSON to ensure ground truth integrity (FR-001).
- [ ] T017 [S] [US1] Add logging for simulation run parameters: Write to `data/results/simulation.log` in JSON format with fields: `N`, `rho`, `seed`, `duration`, `vif_max`, `regeneration_attempts`, `regeneration_reason`. **Data Types**: `regeneration_attempts` (int), `regeneration_reason` (string, one of: "PSD_failure", "VIF_limit", "rank_deficient"). **Dependency**: Requires T015 completion to ensure the `regeneration_attempts` field is populated. **Hygiene**: After writing, **generate a SHA-256 checksum** of the log file and record it in `state/projects/PROJ-034-quantifying-uncertainty-in-small-sample-.yaml` under `artifact_hashes` with key `simulation_log`.

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

- [X] T021A [P] [US2] Implement `code/models/ols.py`: Define OLS model class and `fit` method.
- [X] T021B [P] [US2] Implement `code/models/ols.py`: Implement 95% confidence interval calculation logic.
- [X] T021C [P] [US2] Implement `code/models/ols.py`: Add `get_interval` method returning (lower, upper).
- [X] T022A [P] [US2] Implement `code/models/bootstrap.py`: Define Bootstrap model class and `fit` method.
- [X] T022B [P] [US2] Implement `code/models/bootstrap.py`: Implement BCa interval correction logic.
- [X] T022C [P] [US2] Implement `code/models/bootstrap.py`: Add `get_interval` method returning (lower, upper).
- [X] T023A [S] [US2] Implement `code/models/bayesian.py`: Define the CmdStanPy model string for Bayesian regression with Normal(, 10) priors and Half-Cauchy scale.
- [X] T023B [S] [US2] Implement `code/models/bayesian.py`: Implement the compilation wrapper and `compile_model` function.
- [X] T023C [S] [US2] Implement `code/models/bayesian.py`: Implement the execution wrapper with strict convergence checks. **Deliverables**:
 1. **File Path**: Implement in `code/models/bayesian.py`.
 2. **Arguments**: Must accept `num_chains` (default 4), `iter_warmup` (default 1000), `iter_sampling` (default 2000), `seed`. **Constraint**: `iter_sampling` MUST be 2000 to satisfy FR-003.
 3. **Convergence Check**: Must calculate R-hat **per chain** and raise `ConvergenceError` if any chain has R-hat > 1.05.
 4. **Output Artifact**: Save samples to `data/results/bayesian_samples.h5` and a JSON summary `data/results/bayesian_diagnostics.json` containing `chain_id`, `r_hat`, `divergent_count` for each chain. **Schema**: The JSON must include a `chain_metrics` list: `[{"chain_id": int, "r_hat": float, "divergent_count": int},...]`.
 **Dependency**: Requires T023A and T023B.

**Checkpoint**: Models ready for orchestration

---

## Phase 4.5: Orchestration & Comparative Analysis (Critical Integration)

**Goal**: Run the full Monte Carlo simulation, aggregate results, and generate comparative plots.

- [ ] T026 [S] [US2] Implement `code/main.py`: Orchestration loop for Monte Carlo replications. **CRITICAL**: Implement a **Strict 200-Run Loop**.
 1. **Target**: Execute exactly **200 replications** (SC-004). **Logic**: Loop `for i in range(200)`. If a run fails (convergence/VIF), skip it but **continue** the loop until 200 **valid** runs are completed. **Do not** stop early due to time limits; the -hour limit is a success criterion for the *entire* process, not a stop condition for the loop. If the process exceeds 6 hours, the CI job will fail, which is the correct behavior for missing the success criterion.
 2. **Coverage Logic**: For each run, if the model fails convergence (R-hat > 1.05) or VIF > 10, **flag the run as "INVALID"** and **exclude it from the final coverage calculation denominator**. Do NOT count it as "NOT COVERED". Log these invalid runs separately.
 3. **Artifact Output**: Save **individual run results** to `data/results/run_{i}.json` for every iteration `i` across the full experimental range., containing: `seed`, `vif_max`, `r_hat` (scalar for the run), `covered` (bool), `interval_width`, `method_id`, `is_valid` (bool), `chain_metrics` (list of `{chain_id, r_hat, divergent_count}`), and `timestamp`.
 4. **Aggregation**: Output aggregated results to `data/results/coverage_metrics.json` with the **exact schema**:
 ```json
 {
 "coverage_rate": float,
 "interval_width": float,
 "total_n": int, // Total runs attempted (should be >= 200)
 "valid_n": int, // Runs used in coverage calculation (should be 200)
 "invalid_run_count": int,
 "failure_reasons": {"r_hat_fail": int, "vif_fail": int, "other": int},
 "method_id": "string",
 "partial_completion": false // Always false for this strict loop
 }
 ```
 **Dependency**: Requires T006 (engine), T021A-C (OLS), T022A-C (Bootstrap), and T023A-C (Bayesian) to be complete. T023C must be completed before T026 to ensure the `chain_metrics` schema is available.

- [ ] T026.1 [P] [US2] Generate Runtime Log: **Create** `code/scripts/generate_runtime_log.py`. This script must read all `data/results/run_{i}.json` files, calculate the total duration, and save an aggregated `data/results/runtime_log.json` containing `total_duration`, `start_time`, `end_time`, and `run_count`. **Dependency**: Requires T026 to be complete and functional.

- [ ] T027.5 [P] [Cross-Story] Implement `code/scripts/analyze_comparative.py`: **Read** `data/results/coverage_metrics.json` and individual run logs to generate **comparative metrics and the calibration plot artifact**.
 1. **Binning Logic**: **Aggregate data across the completed replications** by binning the results based on **realized VIF** with explicit edges: **Low (<= 5), Medium (> 5 and <= 10), High (> 10)**. **Algorithm**: Calculate coverage deviation and average interval width for OLS, Bootstrap, and Bayesian **within each bin** using the **mean** aggregation function.
 2. **Plot Generation**: **Generate the calibration plot** (Interval Width vs. Coverage Probability) comparing **all three methods (OLS, Bootstrap, Bayesian) in a single comparative visualization**. **Save the plot** to `data/results/calibration_plot.png`. The plot must explicitly show Interval Width on the X-axis and Coverage Probability on the Y-axis, with points representing the binned aggregates for all three methods overlaid or grouped.
 3. **Provenance**: Embed the **content hash** of the input data (`coverage_metrics.json`) into the plot metadata or filename to satisfy Constitution Principle IV.
 4. **Output**: Save `data/results/comparative_metrics.json` with schema: `{"methods": [{"name": "string", "coverage": float, "width": float, "deviation": float}], "calibration_plot_path": "data/results/calibration_plot.png", "input_hash": "string"}`.
 5. **Dependency**: **Must run only after T026 completes successfully**.

**Checkpoint**: Comparative analysis complete; US3 can now proceed.

---

## Phase 5: User Story 3 - Real-World Validation on UCI Dataset (Priority: P3)

**Goal**: Apply methods to a real-world small-sample dataset (UCI Concrete) to confirm simulation findings.

**Independent Test**: Load UCI Concrete, subsample to $N=40$, run all three methods, verify output includes intervals and diagnostic plots.

**Note**: This phase is **independent** of T027.5 (simulation analysis).

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Integration test for UCI dataset loading and subsampling in `tests/integration/test_validation.py`

### Implementation for User Story 3

- [ ] T029 [S] [US3] Fetch UCI Dataset via Reference-Validator Agent: **Invoke** the Reference-Validator Agent to fetch the UCI Concrete Compressive Strength dataset using the **verified URL from T000** and cache to `data/raw/`. **Constraint**: Must use the Reference-Validator Agent workflow, not custom scripts.
- [ ] T030 [S] [US3] Implement `code/validation/uci_runner.py`: **Subsample logic** with a deterministic configuration space.
 1. **Configuration Space**: **For N=40**, iterate over **all combinations** of feature subsets of varying small sizes.
 2. **Validation**: For each configuration, check if $N > p$. If $N \le p$, **log a warning** "Rank-deficient: N={N} <= p={p}" and **continue** to the next configuration.
 3. **Graceful Failure**: If **no valid subsample** is found after exhausting the entire configuration space, **raise a RuntimeError** with message "VALIDATION_FAILED: No valid subsample found for N < 50 and p >= 3". **Do not skip the validation step**. This ensures FR-005 is strictly met or the project halts visibly.
 4. **Output**: Save the **first valid subsample** to `data/raw/uci_subsampled.csv` with metadata confirming predictor count and N > p status.
 5. **Dependency**: Depends on T029.
- [ ] T031 [S] [US3] Implement `code/validation/uci_runner.py`: **Run all three methods** (OLS, Bootstrap, Bayesian) on the subsampled data. **Dependency**: **Explicitly depends on T030 (data prep) and model implementations (T021A-C, T022A-C, T023A-C)**. Generate interval estimates for all methods and save to `data/results/uci_validation_results.json`. **Note**: This task is independent of T027.5 (simulation analysis).
- [ ] T032 [S] [US3] Implement `code/validation/uci_runner.py`: Generate interval stability metrics and width comparison (Bayesian vs OLS)
- [ ] T033 [S] [US3] Implement `code/validation/uci_runner.py`: Generate diagnostic plots (posterior distributions, interval widths) saved to `data/results/`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final reporting

- [ ] T035 [P] Create `code/scripts/run_full_simulation.sh` for reproducible end-to-end execution on CI
- [ ] T036 [P] Implement `code/scripts/verify_runtime.py`: **Create a script** that reads `data/results/runtime_log.json` (generated by **T026.1**) and **exits with code 1** if `total_duration` > 21600s (6 hours). **Update** `run_full_simulation.sh` to call this script after the simulation and fail the build if it returns 1. **Dependency**: Requires T026.1 to be complete.
- [ ] T037 [P] Update `README.md` with execution instructions (Installation, Usage, Data Flow) and a Mermaid diagram. **Diagram Content**: "Data Flow: Simulation (engine.py) -> Models (ols, bootstrap, bayesian) -> Metrics (coverage.py) -> Results (json/csv)".
- [ ] T038 [P] Run `pytest` on all unit and integration tests; ensure **full pass rate** and generate `pytest-report.xml` as the required artifact.
- [ ] T039 [P] Generate `specs/001-quantifying-uncertainty-in-small-sample/research.md` draft using the project template. **Required Sections**: Abstract (summary of methods), Methods (detailed simulation setup), Results (placeholder for coverage metrics), Discussion (implications of small-sample uncertainty).
- [ ] T040 [S] [US3] Enforce Fail-Loudly for Data Fetch: **Update** `code/validation/uci_runner.py` to remove any `try/except` blocks that might silently fallback to synthetic data. If the UCI fetch fails (after Reference-Validator Agent attempt), the script must raise a `DataFetchError` with a clear message pointing to the verified URL. This aligns with Constitution Principle II and resolves the "synthetic fallback" risk.
- [ ] T041 [P] Add a final validation script `code/scripts/validate_results.py` that checks `data/results/coverage_metrics.json` for expected keys and non-zero valid counts before generating plots.

---

## Phase 7: Resolution of Analysis Concerns (Revision Pass)

**Purpose**: Address specific issues raised by the `/speckit.analyze` agent regarding unresolved claims and data integrity.

- [ ] T042 [P] [Revision] Resolve "not_enough_info" claims in T000, T026, T030: **Update** `code/scripts/verify_citation.py` (T000 logic) to explicitly handle the "Concrete Compressive Strength" dataset ID from the UCI repository (e.g., `uci_machine_learning_concrete`) and ensure the script fetches the correct metadata. **Update** `code/main.py` (T026) to explicitly define the Monte Carlo error margin as `z * sqrt(p*(1-p)/N)` where p is coverage and N is valid runs. **Update** `code/validation/uci_runner.py` (T030) to explicitly list the feature subset indices used for the "3, 4, 5, 6" predictor counts to ensure reproducibility.
- [ ] T043 [P] [Revision] Resolve "refuted" claim in T024 (R-hat > 1.05): **Update** `code/models/bayesian.py` (T023C) to implement a **strict convergence check** that raises a `ConvergenceError` if R-hat > 1.05 for any parameter in any chain. The orchestration loop in T026 must catch this specific error, log it as "INVALID" (not "NOT COVERED"), and proceed to the next seed. This ensures the "refuted" claim is addressed by enforcing the strict threshold rather than ignoring it.
- [ ] T044 [P] [Revision] Ensure "Fail Loudly" in T029: **Update** `code/validation/uci_runner.py` to remove any `try/except` blocks that might silently fallback to synthetic data. If the UCI fetch fails, the script must raise a `DataFetchError` with a clear message pointing to the verified URL. This aligns with Constitution Principle II and resolves the "synthetic fallback" risk.