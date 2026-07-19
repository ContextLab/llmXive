# Tasks: Network Topology Energy Transfer in Spin Systems

**Input**: Design documents from `/specs/001-network-topology-energy-transfer/`
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

- [X] T001a [P] Create project directories: `code/`, `code/src/`, `code/src/generators/`, `code/src/simulation/`, `code/src/analysis/`, `code/src/utils/`, `code/tests/`, `data/raw/`, `data/analysis/`, `paper/`
- [X] T001b [P] Create empty placeholder files in `code/src/` subpackages (`__init__.py`) and `code/tests/__init__.py`
- [X] T001c [P] Create `.gitignore` for Python (`__pycache__`, `.pyc`, `data/`, `paper/`) in repository root

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 [P] Initialize Python project with pinned dependencies in `code/requirements.txt` (networkx, numpy, scipy, matplotlib, seaborn, pandas, pytest, coverage.py)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `code/`
- [X] T004c [P] Create `code/config.yaml` as the immutable source of truth for global seeds, topology targets, and simulation parameters. Output: `code/config.yaml` with a template structure including keys: `global_seed`, `topology_targets`, `simulation_params`. This task MUST precede T004b.
- [X] T004b [P] Implement logic to inject specific random seeds used during a run into `data/run_log.json` and verify them against `code/config.yaml` (T004c). Output: `data/run_log.json` with schema: `{ "run_id": str, "seeds": { "global": int, "generator": int, "simulation": int }, "verification_status": "PASS"|"FAIL" }`. This task depends on T004c.
- [X] T005 [P] Implement logging infrastructure in `code/src/utils/logging.py` to capture seeds, parameters, and runtime metrics, writing to `data/run_log.json`
- [X] T006 [P] Create `code/src/utils/io.py` for saving/loading graphs (`gpickle`, `json`) and managing `data/` directory checksums
- [X] T007 [P] Implement base configuration loader in `code/src/utils/config.py` to validate `config.yaml` against required schema
- [X] T008 [P] Setup `code/tests/conftest.py` with fixtures for temporary data directories and seeded random states
- [X] T016a [P] Implement global timeout utility function in `code/src/generators/timeout.py` with explicit logging. The timeout applies to the *entire batch process* (total job time), not individual graph retries. If the global timeout is hit, the process MUST fail with an error (exit code 1) and log the failure. The function must read the timeout value from `config.yaml` (key: `simulation_timeout_seconds`). This task does NOT contradict the 'Disconnected Networks' Edge Case, which handles individual graph retries within the batch.
- [X] T018b [P] Implement a configurable retry logic for disconnected networks in `code/src/generators/retry_logic.py`. If a specific threshold of failed attempts is reached for a specific graph, log a warning, flag the run as `[DISCONNECTED_NETWORK_FAILURE]`, and proceed to the next graph. Do NOT halt the entire batch. Output: Log entry with count of failed attempts. This task depends on T016a for global timeout handling.
- [X] T051 [US1] Implement explicit connectivity verification in `code/src/generators/base.py` to enforce `nx.is_connected()` before returning any generated graph. This task MUST include a retry loop for each graph; if multiple attempts fail, the system MUST log a warning and proceed to the next graph (per spec edge case). Output: Modified `code/src/generators/base.py` and unit test `code/tests/test_generators.py::test_sw_retries_on_disconnect`. This task resolves the semantic conflict with T018b by ensuring strict connectivity rejection is the primary logic.
- [X] T056 [P] Implement 'Sample Size Adjustment' logic for Phase 2 contingency. If the rejection rate for clustering targets > 40%, automatically increase the target batch size by a configured factor and log "Sample Size Adjustment" to `data/run_log.json`. Output: Modified `code/src/generators/batch_runner.py` and log entry. This task addresses the unimplemented plan contingency.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate synthetic spin network datasets (Priority: P1) 🎯 MVP

**Goal**: Generate connected graphs (Erdős-Rényi, Scale-Free, Small-World) with controlled clustering coefficients and verify topology metrics.

**Independent Test**: Can be fully tested by generating a batch of networks, computing their topological metrics, and verifying the distributions match expected parameters.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Unit test for Erdős-Rényi generation in `code/tests/test_generators.py` implementing `test_er_generates_connected_graph` to verify connectivity and edge probability, and `test_er_clustering_distribution` to verify clustering coefficient distribution.
- [X] T010 [P] [US1] Unit test for Watts-Strogatz (Small-World) generation in `code/tests/test_generators.py` implementing `test_sw_retries_on_disconnect` to verify 10-attempt retry logic and `test_sw_clustering_target` to verify clustering coefficient target achievement.
- [X] T011 [P] [US1] Unit test for Barabási-Albert (Scale-Free) generation in `code/tests/test_generators.py` implementing `test_sf_power_law_fit` to verify degree distribution R² ≥ 0.95.
- [X] T012 [P] [US1] Integration test in `code/tests/test_integration.py` implementing `test_batch_success_rate` to verify ≥95% success rate for valid connected graphs and `test_manifest_generation` to verify `global_batch_manifest.json` content. <!-- FAILED: unspecified -->

### Implementation for User Story 1

- [X] T016 [P] [US1] Implement base generator logic in `code/src/generators/base.py` with shared logic for connectivity checks, a configurable retry limit (read from `config.yaml`), and warning logging for failed attempts, utilizing T016a for timeout mechanism.
- [X] T013 [P] [US1] Implement Erdős-Rényi generator in `code/src/generators/er.py` inheriting from base
- [X] T014 [P] [US1] Implement Watts-Strogatz generator in `code/src/generators/sw.py` inheriting from base, utilizing the shared clustering retry logic (T018b), global timeout (T016a), and Threshold-based warning logging
- [X] T015 [P] [US1] Implement Barabási-Albert generator in `code/src/generators/sf.py` inheriting from base
- [X] T017 [P] [US1] Implement metric extraction function in `code/src/generators/metrics.py` (degree distribution, clustering, average path length)
- [X] T019 [P] [US1] Implement metadata logging module in `code/src/generators/metadata.py` to record algorithm, edge_probability, preferential_attachment_params, and seed for every generated graph, saving to `data/metadata/graph_<id>.json`
- [X] T018 [US1] Create batch generation script skeleton in `code/src/generators/batch_runner.py` to produce per-topology-class batches. This task depends on T018b for retry logic and T016a for timeout.
- [ ] T018c [US1] Implement batch aggregation script in `code/src/generators/aggregate_batch.py` to combine per-topology-class batches into a single global batch. Output: `data/raw/global_batch_manifest.json` with schema: `{ "total_generated": int, "valid_count": int, "success_rate": float, "total_attempts": int, "failed_graphs": [list of ids] }`. This task depends on T018 (Batch Generation) and T018b.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Run energy propagation simulation (Priority: P2)

**Goal**: Execute simplified Ising spin-flip dynamics on generated networks, measure diffusion rates, and ensure numerical stability on CPU.

**Independent Test**: Can be fully tested by running the simulator on a single network, verifying the energy density profile evolves, and confirming spatial variance increases.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Unit test for spin-flip logic in `code/tests/test_simulation.py` implementing `test_energy_conservation_within_tolerance` (assert energy conservation within 1e-6) and `test_spin_flip_boltzmann_match` (assert spin flip probability matches Boltzmann factor).
- [X] T022 [P] [US2] Unit test for spatial variance calculation in `code/tests/test_simulation.py` implementing `test_spatial_variance_calculation` to verify mathematical definition.
- [X] T023 [P] [US2] Unit test for divergence detection and abort logic in `code/tests/test_simulation.py` implementing `test_divergence_raises_error` to verify `SimulationDivergenceError` is raised.

### Implementation for User Story 2

- [X] T024 [P] [US2] Implement simplified Ising spin-flip dynamics in `code/src/simulation/dynamics.py` (CPU-only, no GPU dependencies, default precision)
- [X] T025 [P] [US2] Implement energy density profile tracking and spatial variance calculation in `code/src/simulation/metrics.py`
- [X] T026 [P] [US2] Implement numerical stability checks (divergence detection) in `code/src/simulation/stability.py`
- [X] T052 [US2] Add explicit numerical stability assertions in `code/src/simulation/stability.py` to detect energy divergence (values significantly exceeding initial excitation) and raise a `SimulationDivergenceError` rather than returning a partial result. This task MUST flag the run as `[SIMULATION_DIVERGENCE]` in the output. Output: Modified `code/src/simulation/stability.py` and unit test `code/tests/test_simulation.py::test_divergence_raises_error`. This task addresses the 'Simulation Divergence' edge case.
- [X] T027 [US2] Implement diffusion rate calculator in `code/src/simulation/diffusion.py` to calculate rate of change of spatial variance (finite difference), verifying mathematical definition matches spec and asserting variance monotonicity with tolerance for stochastic noise (not strict assertion), outputting verification results to `data/analysis/diffusion_verification.json`.
- [ ] T029a [P] [US2] Define and validate JSON schema for `data/analysis/simulation_results.json` against the `SimulationRun` entity. Output: `contracts/simulation_run_schema.json` with fields: `network_id` (str), `seed` (int), `diffusion_rate` (float), `topology_class` (str), `steps_run` (int), `status` (str), `runtime_duration_seconds` (float), `generation_algorithm` (str), `parameter_values` (dict). **CRITICAL**: This schema MUST include `generation_algorithm` and `parameter_values` to satisfy Constitution Principle VI (Data Hygiene/Provenance) and enable SC-001/SC-002 validation. This task is a prerequisite for T029.
- [X] T028 [US2] Create simulation runner script in `code/src/simulation/run_simulation.py` that loads graphs from `data/raw/` and executes multiple time steps. **MUST explicitly measure and log the wall-clock execution duration** for each run and populate the `runtime_duration_seconds` field defined in T029a. **MUST capture and include the graph generation algorithm name and parameter values** (from metadata, T019) into the result record to satisfy Constitution Principle VI. Utilizes T024-T027 for core logic and T029 for result serialization. This task depends on T029a and T019.
- [ ] T029 [US2] Implement result serialization to `data/analysis/simulation_results.json` using the schema defined in T029a. Ensure all fields (network_id, seed, diffusion_rate, topology_class, steps_run, status, runtime_duration_seconds, generation_algorithm, parameter_values) are present and valid. Output: `data/analysis/simulation_results.json`. This task depends on T028 (data producer) and T029a. <!-- FAILED: unspecified -->

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Correlate metrics and test significance (Priority: P3)

**Goal**: Perform regression/ANOVA analysis, apply multiple-comparison correction, run sensitivity sweeps, and generate figures.

**Independent Test**: Can be fully tested by running the analysis pipeline on a pre-generated dataset, verifying statistical tests produce p-values, and confirming figures are generated.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T030 [P] [US3] Unit test for regression analysis in `code/tests/test_analysis.py` implementing `test_linear_regression_coefficients` and `test_non_linear_regression_fit`.
- [X] T031 [P] [US3] Unit test for ANOVA and multiple-comparison correction (Bonferroni/BH) in `code/tests/test_analysis.py` implementing `test_anova_f_statistic` and `test_bh_correction_applied`.
- [X] T032 [P] [US3] Unit test for sensitivity sweep logic in `code/tests/test_analysis.py` implementing `test_sensitivity_sweep_thresholds` to verify distinct cutoffs.

### Implementation for User Story 3

- [X] T033 [P] [US3] Implement linear and non-linear regression in `code/src/analysis/regression.py`
- [X] T034a [P] [US3] Implement ANOVA testing in `code/src/analysis/anova.py` to compute F-statistic, degrees of freedom, and p-values. Output: Intermediate results in `data/analysis/anova_raw.json`.
- [X] T034b [P] [US3] Implement multiple-comparison correction (Bonferroni and Benjamini-Hochberg) in `code/src/analysis/anova.py` applying corrections to p-values from T034a. Generate unit test `code/tests/test_analysis.py::test_bh_correction_applied` to verify correction is applied correctly. Output: `data/analysis/anova_corrected.json`.
- [X] T035a [P] [US3] Define JSON schema for sensitivity sweep results. Output: `contracts/sensitivity_sweep_schema.json` with key `cutoffs` (list of floats) and `results` (list of objects).
- [ ] T035b [US3] Implement sensitivity sweep for clustering coefficient thresholds in `code/src/analysis/sensitivity.py`, saving results to `data/analysis/sensitivity_sweep.json` using the schema from T035a. **Explicitly link this task to FR-008** by ensuring the sweep varies thresholds and **reports how diffusion rates vary** across the sweep (correlating thresholds with diffusion rates). Verify file content per SC-005 (≥5 distinct cutoffs). Generate unit test `code/tests/test_analysis.py::test_sensitivity_sweep_thresholds`. Output: `data/analysis/sensitivity_sweep.json`. This task depends on T035a. <!-- FAILED: unspecified -->
- [X] T053 [US3] Implement explicit threshold logging in `code/src/analysis/sensitivity.py` to record the exact clustering coefficient cutoffs used in the sensitivity sweep (FR-008) and verify they match the configuration in `config.yaml`, ensuring SC-005 is met with ≥5 distinct cutoffs. Output: Modified `code/src/analysis/sensitivity.py` and verification log. This task addresses the FR-008/SC-005 requirement.
- [X] T036 [P] [US3] Implement visualization pipeline in `code/src/analysis/plotting.py` to generate ≥3 figures (scatter, heatmaps) at 300 DPI
- [ ] T037a [US3] Implement data aggregation and filtering in `code/src/analysis/aggregate_results.py`. This task loads `data/analysis/simulation_results.json`, filters out runs with status `[SIMULATION_DIVERGENCE]` or `[DISCONNECTED_NETWORK_FAILURE]`, and aggregates metrics (mean, median, variance) for downstream analysis. Output: `data/analysis/aggregated_results.json`. This task depends on T029. <!-- FAILED: unspecified -->
- [X] T037b [US3] Execute statistical tests in `code/src/analysis/run_statistics.py`. This task consumes `data/analysis/aggregated_results.json`, runs regression (T033) and ANOVA (T034a, T034b), and saves intermediate statistical outputs. Output: `data/analysis/statistical_outputs.json`. This task depends on T037a, T033, T034a, T034b.
- [X] T037c [US3] Generate visualization figures in `code/src/analysis/plot_results.py`. This task consumes statistical outputs from T037b and generates ≥3 figures (scatter, heatmaps) at 300 DPI, saving them to `paper/`. Output: PNG files in `paper/`. This task depends on T037b, T036.
- [ ] T037d [US3] Create final serialization script in `code/src/analysis/serialize_final.py`. This task aggregates results from T037b (statistics), T037c (figures), and T035b (sensitivity), and saves `data/analysis/final_results.json`. Schema: `{ "regression_results": {}, "anova_results": {}, "sensitivity_results": {}, "figures_generated": [], "excluded_runs_count": int }`. This task depends on T037b, T037c, T035b.
- [ ] T044 [US3] Implement statistical power analysis in `code/src/analysis/power.py` to consume output from T037d, calculate achieved power against the configured target using `statsmodels.stats.power`, and generate a design validation report `data/analysis/power_analysis_report.json`. Schema: `{ "achieved_power": float, "sample_size_shortfall": int, "recommendation": str }`. This task depends on T037d. This task addresses the missing artifact concern. <!-- FAILED: unspecified -->
- [X] T038 [US3] Implement report generator in `code/src/analysis/report.py` to frame findings as associational (ROC-001) by explicitly implementing logic to avoid causal language (e.g., filtering terms like "cause", "effect", "determine" AND performing a structural check for causal implications) and outputting text for verification.
- [X] T038a [P] [US3] Implement report verification script in `code/src/analysis/verify_report.py` to programmatically verify that the generated report text from T038 explicitly contains the phrase "associational" and structurally adheres to ROC-001, outputting verification results to `data/analysis/report_verification.json` with schema: `{ "contains_associational_disclaimer": bool, "causal_language_found": bool }`.
- [X] T054 [US3] Add explicit causal language filtering in `code/src/analysis/report.py` to scan generated text for forbidden terms (e.g., "cause", "effect", "determine") and replace them with associational equivalents, ensuring ROC-001 is strictly enforced. Output: Modified `code/src/analysis/report.py` and unit test `code/tests/test_analysis.py::test_causal_language_filtering`. This task addresses the ROC-001 requirement.
- [ ] T045a [P] [US3] Implement batch validation logic in `code/src/validation/validate_batch.py` to verify SC-001 (configured target count), SC-002 (runtime < 60m/network, using `runtime_duration_seconds` from T029), and SC-005 (check `data/analysis/sensitivity_sweep.json` for ≥5 distinct cutoffs). **MUST explicitly extract `runtime_duration_seconds`, `generation_algorithm`, and `parameter_values` from `data/analysis/simulation_results.json` (produced by T029) to perform the validation**. This task depends on T029 and T035b.
- [ ] T055 [US3] Implement explicit validation of `runtime_duration_seconds` in `code/src/validation/validate_batch.py` to ensure SC-002 (≤60 mins/network) is checked against the actual wall-clock time recorded in `data/analysis/simulation_results.json`, not an estimated value. Output: Modified `code/src/validation/validate_batch.py` and unit test `code/tests/test_validation.py::test_runtime_validation`. This task addresses the SC-002 validation requirement.
- [X] T045b [US3] Generate the validation report `data/analysis/validation_report.json` using the logic from T045a. Schema: `{ "sc_001_status": "PASS"|"FAIL", "sc_002_status": "PASS"|"FAIL", "sc_005_status": "PASS"|"FAIL", "details": {} }`. This task depends on T045a.
- [X] T046 [P] Add `pytest` coverage report generation
- [X] T047 [P] Verify `config.yaml` documentation and reproducibility of random seeds (T004c ensures the file exists).
- [X] T048 [P] Run quickstart.md validation, outputting validation results to `data/analysis/quickstart_validation.json`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T041 [P] Update `code/README.md` **Installation** section with environment setup instructions
- [X] T042 [P] Update `code/README.md` **Usage** section with execution commands
- [X] T043 [P] Update `code/README.md` **Configuration** section with `config.yaml` explanation

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires output from US1 (generated graphs)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires output from US1 and US2 (metrics and diffusion rates)

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
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for Erdős-Rényi generation in code/tests/test_generators.py"
Task: "Unit test for Watts-Strogatz generation in code/tests/test_generators.py"

# Launch all models for User Story 1 together:
Task: "Implement Erdős-Rényi generator in code/src/generators/er.py"
Task: "Implement Watts-Strogatz generator in code/src/generators/sw.py"
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
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, cross-file conflicts, cross-story dependencies that break independence
- **Dependency Note**: T016a (Timeout utility) is a prerequisite for T014 (Watts-Strogatz) and T018 (Batch runner) and is located in Phase 2 to ensure it is completed first.
- **Dependency Note**: T029a (Schema validation) is a prerequisite for T029 (Serialization) to ensure data integrity.
- **Dependency Note**: T018b (Retry Logic) and T018c (Aggregation) must complete before T028 (Simulation runner) can execute.
- **Dependency Note**: T035b (Sensitivity sweep) must complete before T037d (Final Serialization) and T045 (Validation) can execute.
- **Dependency Note**: T044 (Power analysis) must complete after T037d to validate SC-003.
- **Dependency Note**: T047 (Config verification) must complete to ensure reproducibility before final reporting.
- **Dependency Note**: T046 (Coverage) must complete to ensure test coverage before final reporting.
- **Execution Order**: T045b (Validation) is the final task in Phase 5 and must run after T035b, T044, and T037d are complete.
- **Dependency Note**: T004c (Config creation) must complete before T004b (Seed injection) to ensure the config file exists for verification.
- **Dependency Note**: T028 (Simulation runner) depends on T029a (Schema) and T024-T027 (Dynamics). T029 (Serialization) depends on T028 (Runner) to ensure data is generated before saving.
- **Dependency Note**: T045a (Validation) depends on T029 (Simulation Results) to extract runtime and provenance metrics for SC-001/SC-002 validation.
- **Dependency Note**: T051 (Connectivity Verification) resolves the semantic conflict with T018b by enforcing strict rejection logic.
- **Dependency Note**: T056 (Sample Size Adjustment) implements the plan's Phase 2 contingency logic.
- **Dependency Note**: T037a (Aggregation) must complete before T037b (Statistics).
- **Dependency Note**: T037b (Statistics) must complete before T037c (Plotting) and T037d (Serialization).
- **Dependency Note**: T037c (Plotting) must complete before T037d (Serialization).
- **Dependency Note**: T037d (Serialization) is the final aggregation step before T044, T038, and T045.
- **Dependency Note**: The original coarse T037 task has been removed and replaced by the atomized tasks T037a, T037b, T037c, and T037d to resolve the executability concern regarding task granularity.

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [X] T049 Reconcile run-book vs implementation for `code/main.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/main.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.

- [ ] T050 [US3] Implement CLI entry point in `code/main.py` to orchestrate the full pipeline (T018 → T028 → T037) based on `config.yaml` arguments, ensuring the entry point matches the command invoked in `quickstart.md`. This task addresses the execution feedback regarding the missing `main.py` script referenced in T049 and ensures the pipeline is runnable end-to-end.

- [X] T051 [US1] Implement explicit connectivity verification in `code/src/generators/base.py` to enforce `nx.is_connected()` before returning any generated graph, ensuring the "Disconnected Networks" edge case is handled by rejection rather than silent fallback.
- [X] T052 [US2] Add explicit numerical stability assertions in `code/src/simulation/stability.py` to detect energy divergence (values exceeding significantly amplified magnitudes relative to initial excitation) and raise a `SimulationDivergenceError` rather than returning a partial result, ensuring the "Simulation Divergence" edge case is handled by abort.
- [X] T053 [US3] Implement explicit threshold logging in `code/src/analysis/sensitivity.py` to record the exact clustering coefficient cutoffs used in the sensitivity sweep (FR-008) and verify they match the configuration in `config.yaml`, ensuring SC-005 is met with ≥5 distinct cutoffs.
- [X] T054 [US3] Add explicit causal language filtering in `code/src/analysis/report.py` to scan generated text for forbidden terms (e.g., "cause", "effect", "determine") and replace them with associational equivalents, ensuring ROC-001 is strictly enforced.
- [ ] T055 [US3] Implement explicit validation of `runtime_duration_seconds` in `code/src/validation/validate_batch.py` to ensure SC-002 (≤60 mins/network) is checked against the actual wall-clock time recorded in `data/analysis/simulation_results.json`, not an estimated value.
- [X] T056 [P] Implement 'Sample Size Adjustment' logic for Phase 2 contingency. If the rejection rate for clustering targets > 40%, automatically increase the target batch size by a configured factor and log "Sample Size Adjustment" to `data/run_log.json`. Output: Modified `code/src/generators/batch_runner.py` and log entry. This task addresses the unimplemented plan contingency.
