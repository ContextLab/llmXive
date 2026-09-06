---
description: "Task list template for feature implementation"
---

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
- [X] T010b [P] [US1] Implement `src/analysis/novelty.py` with concrete function signatures: `def quantify_novelty(events: list, base_entropy: float, method: str = "default") -> float:` and `def calculate_event_entropy(transitions: list) -> float`. Implement a quantitative assessment method for semantic novelty that allows the specific mathematical definition to be configured (e.g., via `method` parameter) rather than hardcoding a specific formula, ensuring flexibility for the research phase. (Dep: T001b)

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
- [X] T006d [P] [US1] **Unit Test Signal Emission**: Write unit tests in `tests/unit/test_termination_signal.py` to verify signal emission logic in T006b. (Dep: T006b)
- [X] T006d1 [P] [US1] **Integration Test Handler Trigger**: Write integration tests in `tests/integration/test_termination_trigger.py` to verify the handler is triggered correctly. (Dep: T006c)
- [X] T006d2 [P] [US1] **Assertion for Log Content**: Write assertions in `tests/integration/test_log_content.py` to verify the specific 'Out of Bounds' reason is logged. (Dep: T006d1)
- [X] T008a [P] [US1] Create CLI entry point `src/cli/run_simulation.py` with argument parsing for `--config`, `--steps`, `--seed`. (Dep: T004, T005, T006a)
- [X] T008c [P] [US1] Implement timeout enforcement logic in `src/cli/run_simulation.py` to handle time-bound baseline runs (Edge Case 2), outputting a structured JSON status log with a 'Time-Bound' flag. (Dep: T008a, T008b)
- [X] T009 [P] Configure deterministic random seeds in `src/config.py` and ensure reproducibility across runs. (Dep: T001b)
- [X] T010 [P] Implement logging infrastructure: Create `src/logging_config.py` that configures a rotating file handler writing JSON to `logs/simulation.log`; verify log file contains `step_latency` key. (Dep: T001b)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute CPU-Constrained Simulation Baseline (Priority: P1) 🎯 MVP

**Goal**: Run the comparative simulation between the neural baseline and the CA Eco-Director on a standard GitHub Actions free-tier runner to establish performance bounds.

**Independent Test**: The system can be tested by running the simulation script for a fixed duration on the CI runner and verifying that the job completes without OOM errors or timeout, while logging latency per step. The test must also verify the 'Power-Limited' flag and fallback dataset behavior if the primary dataset is unavailable. **Crucially**, the test must verify that if a 'Time-Bound' run occurs, the resulting `baseline_partial.parquet` file contains the 'Time-Bound' flag and a minimum of 1000 steps, as validated by T016c.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T011a [P] [US1] Unit test for parameter schema validation in `src/sim/eco_director.py`. (Dep: T004)
- [X] T011b [P] [US1] Unit test for eco_director.py state transitions in `tests/unit/test_eco_director.py`. (Dep: T004)
- [X] T012 [P] [US1] Integration test for simulation pipeline memory limits in `tests/integration/test_simulation_pipeline.py`. (Dep: T008b)

### Implementation for User Story 1

- [X] T013 [US1] Implement throttling logic in `src/sim/neural_baseline.py` to ensure it runs within 6h CPU limits. (Dep: T005)
- [X] T018 [US1] Implement strict dataset loader in `src/data/loader.py` that raises an explicit `DataUnavailableError` on fetch failure. **Do NOT implement synthetic fallback here**; the fallback is handled by T015b upon catching this error. (Dep: T008a)
- [X] T018b [P] [US2] **Streaming Data Loader**: Implement robust streaming in `src/data/loader.py` using `datasets.load_dataset(..., streaming=True)` with chunked processing for large datasets. **Explicit Logic**: The loader MUST iterate until the step count reaches the target (e.g., [deferred]), regardless of chunk boundaries, to ensure the minimum step count constraint is met even if chunks do not align. Explicitly document the chunking strategy. This task replaces the need for T050 by embedding streaming in the core loader. (Dep: T018)
- [X] T015b [US1] Implement logic to flag results as 'Power-Limited' and fallback to a smaller synthetic dataset. This task MUST catch `DataUnavailableError` from T018 and trigger `src/data/synthetic_fallback.py` to generate a dataset with [deferred] steps, flagging the run as 'Power-Limited' in the JSON status log. **Note**: This triggers on data unavailability regardless of timeout status. If T008c also flags 'Time-Bound', both flags may be present. **Requirement**: The fallback dataset must still attempt to meet the target step count if possible; if not, the reduced step count must be explicitly recorded in the log. **Verification**: This task must verify that the streaming loader (T018b) is active when processing large datasets. **Dependency Note**: T015b depends on T018 for error handling; T018b verification is a separate US2 task. (Dep: T018, T008c)
- [X] T016a [US1] Create configuration file `config/default.yaml` defining the default simulation parameters (steps=10000, seeds, etc.) required for T016b. (Dep: T008a)
- [X] T057a [US1] **Fix Timeout & Partial State Saving**: Implement the robust logic in `src/cli/run_simulation.py` to handle timeouts and save `baseline_partial.parquet` when a run is time-bound. This task fixes the 'Rejected' feedback for T016b. It must ensure the file is written even if the run is terminated early, and the 'Time-Bound' flag is correctly set. (Dep: T008c)
- [ ] T016b [US1] Implement runner logic in `src/cli/run_simulation.py` to execute the simulation core loop for a minimum of `target_steps` read from `config/default.yaml`. **Hard Constraint**: The system MUST use the `target_steps` value from the config file (which may be a symbolic `[deferred]` constant or a configurable integer) and MUST NOT terminate before reaching this configured value. If the config is missing, default to a safe minimum but log a warning. (Dep: T013, T018, T016a, T057a)
- [ ] T016c [US1] **Verification & Flagging**: Implement logic in `src/cli/run_simulation.py` to verify the step count is reached (>= `target_steps` from config) and flag the run as 'Time-Bound Baseline' if a predefined time-bound threshold is hit. Save `data/raw/baseline_partial.parquet` with the correct flag. This task depends on T016b completing the core loop. (Dep: T016b, T057a)
- [X] T016d [US1] **Hard Constraint Enforcement**: Implement and verify the logic in `src/cli/run_simulation.py` that enforces the `target_steps` minimum as a hard constraint. This task must verify that the loop terminates ONLY after the step count reaches the configured `target_steps`, even if the config is deferred or missing. (Dep: T016b)
- [X] T017 [US1] Implement validation script `src/analysis/validate_metrics.py` that scans `data/raw/*.parquet` for NaN values and exits with code 1 if found. (Dep: T016c)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Sweep Algorithmic Parameters for Coherence Analysis (Priority: P2)

**Goal**: Systematically vary CA parameters to identify which algorithmic properties correlate with high coherence/diversity scores.

**Independent Test**: The system can be tested by running a single parameter sweep and verifying that the output dataset contains distinct entries for each configuration with corresponding metric scores. The test must also verify that the model adjustment/fallback strategy is triggered correctly if the lag-1 autocorrelation check fails.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T043 [P] [US2] Unit test for parameter grid generation in `tests/unit/test_param_grid.py`. (Dep: T023)
- [X] T019 [P] [US2] Integration test for LMM data preparation in `tests/integration/test_lmm_data_prep.py`. (Dep: T026a)

### Implementation for User Story 2

- [X] T021a [US2] Implement `src/analysis/acf_validator.py` to compute ACF and check lag-1 autocorrelation < 0.1 (FR-007). (Dep: T016c)
- [X] T023 [US2] Implement parameter sweep orchestration in `src/cli/run_simulation.py` including grid generation, runner wrapper, and data aggregation. (Dep: T004, T005, T006a)
- [X] T026a [US2] Implement parameter sweep runner in `src/cli/run_simulation.py` to execute simulations for each configuration in the grid. (Dep: T023)
- [ ] T026b [US2] Define configuration loading logic in `src/cli/run_simulation.py` to read `target_steps` from `config.yaml` (defaulting to a configurable integer) and record metrics to `data/processed/`. (Dep: T026a)
- [X] T025 [US2] Ensure `data/raw/` logs are saved for every parameter configuration: Add serialization logic to `src/sim/eco_director.py` to write state snapshots to `data/raw/{run_id}.parquet` during simulation loop. (Dep: T026a)
- [X] T020a [US2] Implement core Linear Mixed-Effects Model logic in `src/analysis/lmm_runner.py` (FR-004) using `statsmodels` with formula `coherence ~ param + (1|time_step)` to treat 'time-step' as a random effect. (Dep: T026a, T025, T027)
- [X] T020b [US2] Integrate configuration adjustments from T032 (Partial Correlation) and T054a (ACF Adjustment) into the LMM runner. **This task must complete before T020c runs.** (Dep: T032, T054a, T020a)
- [X] T020c [US2] Implement script to execute LMM and save results to `data/processed/lmm_results.csv` using the integrated configuration. (Dep: T020b)
- [X] T022 [US2] Implement `src/analysis/rf_runner.py` for Random Forest feature importance analysis (FR-009). (Dep: T026a)
- [X] T024 [US2] Implement logic to exclude unstable configurations (state explosion) from statistical analysis (Edge Case 1). **Output**: Create `src/analysis/filter.py` with a function to filter out runs where memory usage exceeds a predefined high threshold. (Dep: T026a)
- [X] T027 [US2] Implement streaming data processing in `src/analysis/lmm_runner.py` to handle large simulation logs via chunked iteration, ensuring memory usage stays within 7GB limits for long-horizon runs. (Dep: T026a)
- [X] T028 [US2] **Two-Way ANOVA Implementation**: Implement `src/analysis/anova_runner.py` to perform a Two-Way ANOVA framework as mandated by Constitution Principle VII. **Mandatory Output**: The results MUST explicitly identify specific algorithmic properties (neighborhood radius, memory depth, non-linearity) driving performance parity. (Dep: T026a)
- [X] T032 [US2] Implement partial correlation analysis in `src/analysis/partial_corr.py`: Calculate partial correlation between 'memory depth' and 'diversity' (controlling for other factors). **Output**: A configuration update file for T020b. **Note**: This runs before T020 to allow configuration adjustment. (Dep: T026a)
- [X] T032c [US2] **Verify Configuration Consumption**: Generate the configuration update file from T032 and verify that T020b reads and applies it. Output a log `data/processed/config_consumption_log.json` confirming the adjustment was applied. (Dep: T032, T020b)
- [X] T054 [P] [US2] Add a diagnostic task in `src/analysis/acm_validator.py` to compute and log the full Autocorrelation Function (ACF) plot for a representative subset of parameter configurations, verifying the lag-1 assumption visually and numerically. **Threshold**: Flag any configuration where the lag-1 autocorrelation >= 0.1 OR the decay rate is < 0.05 per step. (Dep: T021a)
- [X] T054a [US2] Implement the **Model Adjustment Logic** required by FR-007: If T054 detects lag-1 >= 0.1, this task ensures the LMM runner switches to robust standard errors or adjusts random effects. **Mandatory Gate**: T054a MUST block the LMM runner (T020b) until the adjustment is applied. It is not just a diagnostic; it implements the mandatory FR-007 adjustment. (Dep: T054, T021a)
- [X] T063a [US2] **Log Adjustment Application**: Output the specific adjusted model parameters and a log file `data/processed/acf_adjustment_log.json` confirming the adjustment was applied by T054a. (Dep: T054a)
- [X] T063 [US2] Implement a "Verify ACF Adjustment Application" task in `src/analysis/verify_acf_adjustment.py` to confirm that the LMM run (T020c) actually applied the robust standard errors or adjusted random effects when T054a detected lag-1 >= 0.1. **Output**: A verification log that T033 depends on. (Dep: T021a, T054a, T063a)
- [X] T059 [P] [US2] Add a "Parameter Grid Exhaustiveness" test in `tests/unit/test_param_grid.py` to verify that the grid generation covers all required combinations of `neighborhood_radius`, `memory_depth`, and `non_linearity` as defined in the spec, ensuring no configurations are accidentally skipped. (Dep: T023)
- [X] T060 [US2] Implement a "Statistical Power Analysis" task in `src/analysis/power_analysis.py` to estimate the minimum number of simulation runs (noise seeds) required to detect a medium effect size with [deferred] power, and update the configuration in `config/default.yaml` if the current seed count is insufficient. (Dep: T026a)

---

## Phase 5: User Story 3 - Validate Statistical Parity and Latency Trade-offs (Priority: P3)

**Goal**: Confirm if optimal CA configuration achieves statistical parity with neural baseline and meets ≥90% latency reduction target.

**Independent Test**: The system can be tested by comparing aggregate metrics and verifying the latency reduction calculation is explicitly reported.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T041 [P] [US3] Unit test for latency reduction calculation in `tests/unit/test_latency_calc.py`. (Dep: T030b)
- [X] T042 [P] [US3] Integration test for sensitivity analysis report in `tests/integration/test_sensitivity_report.py`. (Dep: T029)

### Implementation for User Story 3

- [X] T029 [P] [US3] Implement `src/analysis/sensitivity.py` to sweep coherence decision cutoffs across a range of representative thresholds, calculate **inconsistency_rate** metrics for each, and generate `src/analysis/reports/sensitivity_report.md` in the specific format required by the spec's acceptance criteria. **Note**: This task is independent of LMM success (T020) and runs on the raw metric distributions. (Dep: T026a)
- [X] T030a [US3] Implement statistical parity test in `src/analysis/parity_test.py` using Welch's t-test or Mann-Whitney U to calculate p-values for coherence/diversity parity (SC-002). (Dep: T020c)
- [X] T030b [US3] Implement latency reduction calculator in `src/analysis/latency_calc.py` to verify ≥90% target (SC-001, FR-005). **Mandatory**: This task MUST include results from the permutation test (T067) to statistically prove the reduction is not due to random variance. (Dep: T013, T016c, T023, T067)
- [X] T034 [US3] Validate results against `physics_oracle.schema.yaml` to ensure non-tautological coherence (FR-008) and verify that specific physics constraint violation values (e.g., mass/energy deviation) are recorded in `MetricRecord` as per T006a. **Requirement**: The final report (T033) must explicitly include these specific violation values as evidence of non-tautology. **Input**: This task consumes `data/processed/physics_flow_verification.json` from T006e. (Dep: T006a, T006e, T034a, T034b)
- [X] T034a [US3] **Verify Oracle External Validity**: Implement logic to explicitly verify that the physics oracle constraints are 'external' and not derived from the CA rules. **Method**: Compare the source code lineage of the oracle constraints against the CA rule definitions to ensure no overlap. This verification is mandatory for T034. (Dep: T006a)
- [X] T034b [US3] **Verify Oracle Externality (Source Code Lineage)**: Implement a dedicated verification script `src/analysis/verify_oracle_externality.py` that performs a static analysis of `src/sim/physics_oracle.py` and `src/sim/eco_director.py` to ensure the physics constraints used in the oracle are not derived from or identical to the CA update rules. This task provides the explicit evidence required to satisfy FR-008's "external" requirement, preventing tautology. (Dep: T006a, T004)
- [X] T033a [US3] **Integrate Sensitivity Data**: Merge the sensitivity results from T029 into the final report template, ensuring the data is explicitly included in `docs/report.md`. (Dep: T029, T033)
- [X] T033b [US3] **Integrate SC-006 Verification**: Merge the verification result from T062 into the final report template, ensuring the verification result is explicitly included. (Dep: T062, T033)
- [X] T033c [US3] **Integrate Latency & Confidence**: Merge the point estimate and confidence interval from T055 into the final report template, ensuring the result is explicitly included. (Dep: T055, T033)
- [X] T033 [US3] Generate final report: Generate `docs/report.md` containing the comparison table, p-values from `data/processed/summary.csv`, and the 'Invalid' flag from T032b if applicable. **Must depend on T062 (SC-006 Verification), T063 (ACF Adjustment Verification), T034 (Physics Validation), T033a, T033b, T033c**. **Template**: Use `docs/report_template.md` and output JSON schema `report_schema.json`. (Dep: T030a, T030b, T034, T062, T063, T033a, T033b, T033c)
- [X] T035 [US3] Implement semantic novelty quantification in `src/analysis/novelty.py` by comparing event entropy distributions between CA and Neural runs, ensuring the metric is not derived solely from the CA rules. (Dep: T010b)
- [X] T055 [US3] Implement a "Latency Reduction Confidence Interval" calculation in `src/analysis/latency_calc.py` to report the 95% confidence interval for the ≥90% latency reduction claim, ensuring the result is not just a point estimate but statistically robust against variance. **Mandatory**: This task MUST include results from the permutation test (T067). (Dep: T030b, T067)
- [X] T056 [US2] Implement a "Non-Linearity Interaction Check" in `src/analysis/rf_runner.py` to explicitly report the top 3 non-linear interaction terms (e.g., `memory_depth * non_linearity`) that the LMM might have missed, ensuring the Random Forest analysis fulfills FR-009's specific requirement. (Dep: T022)
- [ ] T057 [US1] Implement a "Time-Bound Baseline Validation" task in `src/analysis/validate_metrics.py` to specifically check for the presence of the `Time-Bound` flag in `data/raw/baseline_partial.parquet` and verify that the partial run contains **>= 1000 steps** to be statistically meaningful, failing the task if the partial run is too short. (Dep: T016c)
- [X] T058 [US3] Implement a "Physics Oracle Consistency" check in `src/analysis/parity_test.py` to ensure that the coherence scores are not correlated with the specific physics oracle parameters used, verifying the non-tautological nature of the metric as required by FR-008. (Dep: T034)
- [X] T062 [US3] Implement a "SC-006 Verification" task in `src/analysis/verify_sc006.py` to explicitly check that the partial correlation coefficient is < 0.05 for the final reported results. **Blocking**: This task must return a failure status if the threshold is not met, preventing T033 (Report Generation) from completing successfully. **Mandatory**: This task MUST use the bootstrapped confidence interval from T066. If the CI crosses zero, the verification MUST fail. **Output**: Write `data/processed/sc006_status.json` with `pass: true/false`. (Dep: T032, T032c, T066)
- [X] T064 [P] [US1] Implement "Data Source Verification" in `src/cli/verify_data.py` that reads `state.yaml` to verify the data source recipe and updates `src/data/loader.py` to use the specified package/recipe, removing any fallback to guessed URLs or hand-rolled fetchers. (Dep: T018)
- [X] T006e [US1] **Data Flow Verification**: Implement and verify the data flow from `src/sim/physics_oracle.py` (T006a) to `MetricRecord` to ensure specific physics constraint violation values are recorded. This task ensures the data is available for T034. **Output**: Write `data/processed/physics_flow_verification.json`. (Dep: T006a, T025)

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T036 [P] Documentation updates in `docs/` and `quickstart.md`. (Dep: T033)
- [X] T037 Code cleanup and refactoring for modularity. (Dep: T033)
- [X] T038 Performance optimization for simulation loop (vectorization where possible). (Dep: T016c)
- [X] T039 [P] Additional unit tests for edge cases in `tests/unit/`. (Dep: T033)
- [X] T040 Run `quickstart.md` validation to ensure end-to-end reproducibility. (Dep: T036)

---

## Phase R: Revision & Analysis Resolution (Addressing Review Concerns)

**Purpose**: Address specific reviewer concerns regarding data integrity, streaming implementation, and statistical rigor identified in prior analysis passes.

- [X] T018b [P] [US2] **Streaming Loader**: (Moved from T050) Implement robust streaming loader in `src/data/loader.py` to handle the LingBot-World 2.0 dataset via `datasets.load_dataset(..., streaming=True)` with chunked processing, ensuring the full dataset contributes to statistics without OOM, and explicitly documenting the chunking strategy in the task description. (Dep: T018)
- [X] T051 [US2] Add a hard assertion in `src/analysis/lmm_runner.py` to verify that the streaming loader in Tb is active when processing datasets exceeding 1GB, raising a `RuntimeError` if a full-load attempt is detected, ensuring memory constraints are strictly enforced. (Dep: T018b)
- [X] T053 [US3] Implement a "Synthetic Fallback Gate" in `src/data/synthetic_fallback.py` that includes a mandatory `assert False` or explicit `raise RuntimeError("Synthetic fallback blocked by policy")` if the fallback is triggered **without** a valid `DataUnavailableError` from T018, ensuring no silent synthetic data generation occurs. **Crucial**: If `DataUnavailableError` IS caught, the system MUST proceed with the synthetic dataset as per Edge Case 3. (Dep: T015b)
- [X] T065 [US2] **Review Concern: Data Flow Completeness for Physics Oracle**: Implement a dedicated integration test `tests/integration/test_physics_oracle_flow.py` that explicitly traces a single simulation step from `src/sim/eco_director.py` through `src/sim/physics_oracle.py` to `MetricRecord` and finally to `data/processed/physics_flow_verification.json`. This task must verify that the specific violation values (e.g., mass deviation) are not just logged but are correctly serialized into the final JSON artifact consumed by T034, resolving any ambiguity in the data lineage. **Blocking**: This task is a prerequisite for T034. (Dep: T006a, T006e, T025)
- [X] T066 [US2] **Review Concern: Statistical Power of Partial Correlation**: Reactivate and implement `src/analysis/partial_corr.py` (T032) to include a bootstrapping confidence interval for the partial correlation coefficient. The task must calculate the 95% CI and flag the result as "Inconclusive" if the interval crosses zero, ensuring the SC-006 verification (T062) is based on statistically robust evidence rather than a single point estimate. (Dep: T032, T060)
- [X] T067 [US3] **Review Concern: Robustness of Latency Reduction Claim**: Reactivate and implement `src/analysis/latency_calc.py` (T030b) to perform a permutation test (non-parametric) alongside the confidence interval calculation (T055). This task must verify that the observed ≥90% reduction is not a result of random variance by shuffling the latency labels between CA and Neural runs [deferred] times and computing the empirical p-value. **Mandatory**: T030b and T055 MUST include results from this task. (Dep: T030b, T055)
- [X] T068 [US2] **Review Concern: Model Adjustment Transparency**: Create a detailed "Adjustment Decision Log" in `src/analysis/verify_acf_adjustment.py` (T063) that explicitly documents *why* a specific adjustment (robust SE vs. random effect change) was chosen for each parameter configuration based on the ACF diagnostic (T054). This log must be included in the final report (T033) to ensure full transparency of the statistical modeling choices required by FR-007. (Dep: T054, T054a, T063)
- [X] T069 [US1] **Review Concern: Fallback Dataset Representativeness**: Update `src/data/synthetic_fallback.py` (T015b) to include a statistical comparison (Kolmogorov-Smirnov test) between the fallback synthetic dataset distribution and the expected distribution of the real dataset. The task must flag the run as "Power-Limited (Unverified Distribution)" if the distributions differ significantly, ensuring the fallback data is not silently assumed to be representative. (Dep: T015b, T018)
- [X] T015c [US1] **Review Concern: Fallback Density**: Implement a verification task in `src/data/synthetic_fallback.py` to ensure the generated 'smaller synthetic dataset' meets the 'sufficient data density' requirement of SC-004. **Metric**: The dataset MUST contain at least 1,000 valid steps and meet a variance threshold. If not, the run must fail or be flagged as insufficient. (Dep: T015b, T018)
