# Tasks: llmXive follow-up: extending "Infinite Worlds with Versatile Interactions"

**Input**: Design documents from `/specs/001-llmxive-followup/`
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

- [X] T001a [P] Create directory structure: Execute `mkdir -p src/sim src/analysis src/data src/cli src/tests data/raw data/processed docs state` to establish the project skeleton. (Dep: None)
- [X] T001b [P] Create initial empty files: Create `src/__init__.py`, `src/sim/__init__.py`, `src/analysis/__init__.py`, `src/data/__init__.py`, `src/cli/__init__.py`, `src/tests/__init__.py`, `data/raw/.gitkeep`, `data/processed/.gitkeep`, `docs/.gitkeep`, `state/.gitkeep`. (Dep: T001a)
- [X] T002 Initialize Python project with `requirements.txt` containing pinned versions: `numpy>=1.24`, `pandas>=2.0`, `scikit-learn>=1.3`, `statsmodels>=0.14`, `huggingface_hub>=0.19`, `torch==2.1.0+cpu`, `matplotlib>=3.8`, `seaborn>=0.13`, `pyyaml>=6.0`. (Dep: T001b)
- [X] T003 [P] Configure linting (ruff) and formatting tools with `pyproject.toml` settings. (Dep: T001b)
- [X] T010b [P] Create skeleton file `src/analysis/novelty.py` with placeholder functions for semantic novelty quantification (Required for T035). (Dep: T001b)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete
**⚠️ ORDERING**: T007 (Data Models) MUST complete before T004, T005, and T006.

- [X] T007 Create base data models: `SimulationRun`, `MetricRecord`, `ParameterGrid` in `src/data_models.py`. (Dep: T001b)
- [X] T004 [US1] Implement `src/sim/eco_director.py` with schema definition, update loop, and runtime parameter injection mechanism (CLI args + YAML loader) to satisfy FR-001's "without code recompilation" constraint. (Dep: T007)
- [X] T005 [P] [US1] Implement `src/sim/neural_baseline.py` (Throttled M Parameter Proxy) with CPU-only constraints. (Dep: T007)
- [X] T006a [P] [US1] Implement `src/sim/physics_oracle.py` (Stochastic Physics Sandbox) to validate external constraints (FR-008) and explicitly log specific physics constraint violation values (e.g., mass/energy deviation) into `MetricRecord`. **Critical**: This task MUST ensure the data flow from the oracle to `MetricRecord` is complete and verified, resolving the 'Rejected' status for T034. (Dep: T007)
- [X] T008b [P] [US1] Implement **Graceful Termination Handler** as a standalone shared module `src/sim/termination_handler.py` (NOT embedded in CLI) that performs the actual mid-simulation shutdown, saves partial state if applicable, logs the specific 'Out of Bounds' reason, and exits cleanly without crashing the CI job. (Dep: T001b)
- [X] T006b [US1] Implement internal memory/time limit **detection and signal emission** within the CA engine/simulation loop in `src/sim/eco_director.py` to satisfy FR-003's strict enforcement requirement. This task MUST call the termination handler defined in T008b and verify that the signal emission results in the specific 'Out of Bounds' reason logging (e.g., 'Memory Explosion') required by FR-003. (Dep: T004, T008b)
- [X] T006c [US1] Implement **Handler Integration**: Ensure `src/sim/eco_director.py` correctly imports and calls `src/sim/termination_handler.py` when detection thresholds are met. (Dep: T006b, T008b)
- [X] T006d [US1] Implement **Detection Verification**: Unit tests and integration checks to verify that the signal emission in T006b correctly triggers T008b and logs the specific reason. (Dep: T006c)
- [X] T008a [P] [US1] Create CLI entry point `src/cli/run_simulation.py` with argument parsing for `--config`, `--steps`, `--seed`. (Dep: T004, T005, T006a)
- [X] T008c [P] [US1] Implement timeout enforcement logic in `src/cli/run_simulation.py` to handle time-bound baseline runs (Edge Case 2), outputting a structured JSON status log with a 'Time-Bound' flag. (Dep: T008a, T008b)
- [X] T009 [P] Configure deterministic random seeds in `src/config.py` and ensure reproducibility across runs. (Dep: T001b)
- [X] T010 [P] Implement logging infrastructure: Create `src/logging_config.py` that configures a rotating file handler writing JSON to `logs/simulation.log`; verify log file contains `step_latency` key. (Dep: T001b)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute CPU-Constrained Simulation Baseline (Priority: P1) 🎯 MVP

**Goal**: Run the comparative simulation between the neural baseline and the CA Eco-Director on a standard GitHub Actions free-tier runner to establish performance bounds.

**Independent Test**: The system can be tested by running the simulation script for a fixed duration on the CI runner and verifying that the job completes without OOM errors or timeout, while logging latency per step. The test must also verify the 'Power-Limited' flag and fallback dataset behavior if the primary dataset is unavailable. **Crucially**, the test must verify that if a 'Time-Bound' run occurs, the resulting `baseline_partial.parquet` file contains the 'Time-Bound' flag and a minimum of 1000 steps, as validated by T057a.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T011a [P] [US1] Unit test for parameter schema validation in `src/sim/eco_director.py`. (Dep: T004)
- [X] T011b [P] [US1] Unit test for eco_director.py state transitions in `tests/unit/test_eco_director.py`. (Dep: T004)
- [X] T012 [P] [US1] Integration test for simulation pipeline memory limits in `tests/integration/test_simulation_pipeline.py`. (Dep: T008b)

### Implementation for User Story 1

- [X] T013 [US1] Implement throttling logic in `src/sim/neural_baseline.py` to ensure it runs within 6h CPU limits. (Dep: T005)
- [X] T018 [US1] Implement strict dataset loader in `src/data/loader.py` that raises an explicit `DataUnavailableError` on fetch failure. **Do NOT implement synthetic fallback here**; the fallback is handled by T015b upon catching this error. (Dep: T008a)
- [X] T018b [US1] **Streaming Data Loader**: Implement robust streaming in `src/data/loader.py` using `datasets.load_dataset(..., streaming=True)` with chunked processing for large datasets. Explicitly document the chunking strategy. This task replaces the need for T050 by embedding streaming in the core loader. (Dep: T018)
- [X] T015b [US1] Implement logic to flag results as 'Power-Limited' and fallback to a smaller synthetic dataset. This task MUST catch `DataUnavailableError` from T018 and trigger `src/data/synthetic_fallback.py` to generate a dataset with [deferred] steps, flagging the run as 'Power-Limited' in the JSON status log. **Note**: This triggers on data unavailability regardless of timeout status. If T008c also flags 'Time-Bound', both flags may be present. **Requirement**: The fallback dataset must still attempt to meet the target step count if possible; if not, the reduced step count must be explicitly recorded in the log. (Dep: T018, T018b, T008c)
- [X] T016a [US1] Create configuration file `config/default.yaml` defining the default simulation parameters (steps=10000, seeds, etc.) required for T016b. (Dep: T008a)
- [X] T057a [US1] **Fix Timeout & Partial State Saving**: Implement the robust logic in `src/cli/run_simulation.py` to handle timeouts and save `baseline_partial.parquet` when a run is time-bound. This task fixes the 'Rejected' feedback for T016b. It must ensure the file is written even if the run is terminated early, and the 'Time-Bound' flag is correctly set. (Dep: T008c)
- [ ] T016b [US1] Implement runner logic in `src/cli/run_simulation.py` to execute the simulation for a minimum of 10,000 time-steps using `config/default.yaml`. **Verification Step**: Implement logic to verify the step count is reached; if a predefined time-bound threshold is hit, the run must be flagged as 'Time-Bound Baseline' and saved as `data/raw/baseline_partial.parquet`. This task relies on the fix in T057a. (Dep: T013, T018, T018b, T016a, T057a)
- [X] T017 [US1] Implement validation script `src/analysis/validate_metrics.py` that scans `data/raw/*.parquet` for NaN values and exits with code 1 if found. (Dep: T016b)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Sweep Algorithmic Parameters for Coherence Analysis (Priority: P2)

**Goal**: Systematically vary CA parameters to identify which algorithmic properties correlate with high coherence/diversity scores.

**Independent Test**: The system can be tested by running a single parameter sweep and verifying that the output dataset contains distinct entries for each configuration with corresponding metric scores. The test must also verify that the model adjustment/fallback strategy is triggered correctly if the lag-1 autocorrelation check fails.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T043 [P] [US2] Unit test for parameter grid generation in `tests/unit/test_param_grid.py`. (Dep: T023)
- [X] T019 [P] [US2] Integration test for LMM data preparation in `tests/integration/test_lmm_data_prep.py`. (Dep: T026a)

### Implementation for User Story 2

- [X] T021a [US2] Implement `src/analysis/acf_validator.py` to compute ACF and check lag-1 autocorrelation < 0.1 (FR-007). (Dep: T016b)
- [X] T023 [US2] Implement parameter sweep orchestration in `src/cli/run_simulation.py` including grid generation, runner wrapper, and data aggregation. (Dep: T004, T005, T006a)
- [X] T026a [US2] Implement parameter sweep runner in `src/cli/run_simulation.py` to execute simulations for each configuration in the grid. (Dep: T023)
- [X] T026b [US2] Define configuration loading logic in `src/cli/run_simulation.py` to read `target_steps` from `config.yaml` (defaulting to a configurable integer) and record metrics to `data/processed/`. (Dep: T026a)
- [X] T025 [US2] Ensure `data/raw/` logs are saved for every parameter configuration: Add serialization logic to `src/sim/eco_director.py` to write state snapshots to `data/raw/{run_id}.parquet` during simulation loop. (Dep: T026a)
- [X] T020a [US2] Implement core Linear Mixed-Effects Model logic in `src/analysis/lmm_runner.py` (FR-004) using `statsmodels` with formula `coherence ~ param + (1|time_step)` to treat 'time-step' as a random effect. (Dep: T026a, T025, T027)
- [X] T020b [US2] Integrate configuration adjustments from T032b (Partial Correlation) and T054a (ACF Adjustment) into the LMM runner. (Dep: T020a, T032b, T054a)
- [X] T020c [US2] Execute the LMM analysis using the integrated configuration. (Dep: T020b)
- [X] T022 [US2] Implement `src/analysis/rf_runner.py` for Random Forest feature importance analysis (FR-009). (Dep: T026a)
- [X] T024 [US2] Implement logic to exclude unstable configurations (state explosion) from statistical analysis (Edge Case 1). **Output**: Create `src/analysis/filter.py` with a function to filter out runs where memory usage exceeds a predefined high threshold. (Dep: T026a)
- [X] T027 [US2] Implement streaming data processing in `src/analysis/lmm_runner.py` to handle large simulation logs via chunked iteration, ensuring memory usage stays within 7GB limits for long-horizon runs. (Dep: T026a)
- [X] T032 [US2] Implement partial correlation analysis in `src/analysis/partial_corr.py`: Calculate partial correlation between 'memory depth' and 'diversity' (controlling for other factors). **Output**: A configuration update file for T032b. **Note**: This runs before T020 to allow configuration adjustment. (Dep: T026a)
- [X] T032b [US2] Implement logic to act on partial correlation results: If coefficient >= 0.05, update the LMM configuration (e.g., add random effects or flags) and flag the run as 'Invalid' in the final report generation (T033). **This task must complete before T020 runs.** (Dep: T032)

---

## Phase 5: User Story 3 - Validate Statistical Parity and Latency Trade-offs (Priority: P3)

**Goal**: Confirm if optimal CA configuration achieves statistical parity with neural baseline and meets ≥90% latency reduction target.

**Independent Test**: The system can be tested by comparing aggregate metrics and verifying the latency reduction calculation is explicitly reported.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T041 [P] [US3] Unit test for latency reduction calculation in `tests/unit/test_latency_calc.py`. (Dep: T030b)
- [X] T042 [P] [US3] Integration test for sensitivity analysis report in `tests/integration/test_sensitivity_report.py`. (Dep: T029)

### Implementation for User Story 3

- [X] T029 [P] [US3] Implement `src/analysis/sensitivity.py` to sweep coherence decision cutoffs across a range of representative thresholds, calculate inconsistency rates, and generate `src/analysis/reports/sensitivity_report.md`. **Note**: This task is independent of LMM success (T020) and runs on the raw metric distributions. (Dep: T026a)
- [X] T030a [US3] Implement statistical parity test in `src/analysis/parity_test.py` using Welch's t-test or Mann-Whitney U to calculate p-values for coherence/diversity parity (SC-002). (Dep: T020c)
- [X] T030b [US3] Implement latency reduction calculator in `src/analysis/latency_calc.py` to verify ≥90% target (SC-001, FR-005). (Dep: T013, T016b, T023)
- [X] T034 [US3] Validate results against `physics_oracle.schema.yaml` to ensure non-tautological coherence (FR-008) and verify that specific physics constraint violation values (e.g., mass/energy deviation) are recorded in `MetricRecord` as per T006a. **Requirement**: The final report (T033) must explicitly include these specific violation values as evidence of non-tautology. (Dep: T006a, T006e)
- [X] T033 [US3] Generate final report: Generate `docs/report.md` containing the comparison table, p-values from `data/processed/summary.csv`, and the 'Invalid' flag from T032b if applicable. **Must depend on T062 (SC-006 Verification), T063 (ACF Adjustment Verification), and T034 (Physics Validation)** to ensure all criteria are met. (Dep: T030a, T030b, T034, T062, T063)
- [X] T035 [US3] Implement semantic novelty quantification in `src/analysis/novelty.py` by comparing event entropy distributions between CA and Neural runs, ensuring the metric is not derived solely from the CA rules. (Dep: T010b)

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T036 [P] Documentation updates in `docs/` and `quickstart.md`. (Dep: T033)
- [X] T037 Code cleanup and refactoring for modularity. (Dep: T033)
- [X] T038 Performance optimization for simulation loop (vectorization where possible). (Dep: T016b)
- [X] T039 [P] Additional unit tests for edge cases in `tests/unit/`. (Dep: T033)
- [X] T040 Run `quickstart.md` validation to ensure end-to-end reproducibility. (Dep: T036)

---

## Phase R: Revision & Analysis Resolution (Addressing Review Concerns)

**Purpose**: Address specific reviewer concerns regarding data integrity, streaming implementation, and statistical rigor identified in prior analysis passes.

- [X] T018b [P] [US2] **Streaming Loader**: (Moved from T050) Implement robust streaming loader in `src/data/loader.py` to handle the LingBot-World 2.0 dataset via `datasets.load_dataset(..., streaming=True)` with chunked processing, ensuring the full dataset contributes to statistics without OOM, and explicitly documenting the chunking strategy in the task description. (Dep: T018)
- [X] T051 [US2] Add a hard assertion in `src/analysis/lmm_runner.py` to verify that the streaming loader in T018b is active when processing datasets exceeding 1GB, raising a `RuntimeError` if a full-load attempt is detected, ensuring memory constraints are strictly enforced. (Dep: T018b)
- [X] T053 [US3] Implement a "Synthetic Fallback Gate" in `src/data/synthetic_fallback.py` that includes a mandatory `assert False` or explicit `raise RuntimeError("Synthetic fallback blocked by policy")` if the fallback is triggered **without** a valid `DataUnavailableError` from T018, ensuring no silent synthetic data generation occurs. **Crucial**: If `DataUnavailableError` IS caught, the system MUST proceed with the synthetic dataset as per Edge Case 3. (Dep: T015b)
- [X] T054 [P] [US2] Add a diagnostic task in `src/analysis/acm_validator.py` to compute and log the full Autocorrelation Function (ACF) plot for a representative subset of parameter configurations, verifying the lag-1 assumption visually and numerically. **Threshold**: Flag any configuration where the lag-1 autocorrelation >= 0.1 OR the decay rate is < 0.05 per step. (Dep: T021a)
- [X] T054a [US2] Implement the **Model Adjustment Logic** required by FR-007: If T054 detects lag-1 >= 0.1, this task ensures the LMM runner switches to robust standard errors or adjusts random effects. It is not just a diagnostic; it implements the mandatory FR-007 adjustment. (Dep: T054, T021a)
- [X] T055 [US3] Implement a "Latency Reduction Confidence Interval" calculation in `src/analysis/latency_calc.py` to report the 95% confidence interval for the ≥90% latency reduction claim, ensuring the result is not just a point estimate but statistically robust against variance. (Dep: T030b)
- [X] T056 [US2] Implement a "Non-Linearity Interaction Check" in `src/analysis/rf_runner.py` to explicitly report the top 3 non-linear interaction terms (e.g., `memory_depth * non_linearity`) that the LMM might have missed, ensuring the Random Forest analysis fulfills FR-009's specific requirement. (Dep: T022)
- [ ] T057 [US1] Implement a "Time-Bound Baseline Validation" task in `src/analysis/validate_metrics.py` to specifically check for the presence of the `Time-Bound` flag in `data/raw/baseline_partial.parquet` and verify that the partial run contains **>= 1000 steps** to be statistically meaningful, failing the task if the partial run is too short. (Dep: T016b)
- [X] T058 [US3] Implement a "Physics Oracle Consistency" check in `src/analysis/parity_test.py` to ensure that the coherence scores are not correlated with the specific physics oracle parameters used, verifying the non-tautological nature of the metric as required by FR-008. (Dep: T034)
- [X] T059 [P] [US2] Add a "Parameter Grid Exhaustiveness" test in `tests/unit/test_param_grid.py` to verify that the grid generation covers all required combinations of `neighborhood_radius`, `memory_depth`, and `non_linearity` as defined in the spec, ensuring no configurations are accidentally skipped. (Dep: T023)
- [X] T060 [US2] Implement a "Statistical Power Analysis" task in `src/analysis/power_analysis.py` to estimate the minimum number of simulation runs (noise seeds) required to detect a medium effect size with [deferred] power, and update the configuration in `config/default.yaml` if the current seed count is insufficient. (Dep: T026a)
- [X] T062 [US3] Implement a "SC-006 Verification" task in `src/analysis/verify_sc006.py` to explicitly check that the partial correlation coefficient is < 0.05 for the final reported results. **Blocking**: This task must return a failure status if the threshold is not met, preventing T033 (Report Generation) from completing successfully. (Dep: T032, T032b)
- [X] T063 [US2] Implement a "Verify ACF Adjustment Application" task in `src/analysis/verify_acf_adjustment.py` to confirm that the LMM run (T020) actually applied the robust standard errors or adjusted random effects when T054a detected lag-1 >= 0.1. **Output**: A verification log that T033 depends on. (Dep: T021a, T054a)
- [X] T064 [P] [US1] Implement "Data Source Verification" in `src/cli/verify_data.py` that reads `state.yaml` to verify the data source recipe and updates `src/data/loader.py` to use the specified package/recipe, removing any fallback to guessed URLs or hand-rolled fetchers. (Dep: T018)
- [X] T006e [US1] **Data Flow Verification**: Implement and verify the data flow from `src/sim/physics_oracle.py` (T006a) to `MetricRecord` to ensure specific physics constraint violation values are recorded. This task ensures the data is available for T034. (Dep: T006a)
