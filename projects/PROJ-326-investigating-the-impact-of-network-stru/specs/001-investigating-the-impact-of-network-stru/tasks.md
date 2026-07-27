# Tasks: Network Topology Energy Transfer in Spin Systems

**Version**: 1.0.5
**Stage owned**: `tasked`
**Generated**: 2025-01-15
**Spec**: `specs/001-network-topology-energy-transfer/spec.md`
**Plan**: `specs/001-network-topology-energy-transfer/plan.md`

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create project directories: `code/`, `code/src/`, `code/src/generators/`, `code/src/simulation/`, `code/src/analysis/`, `code/src/utils/`, `code/tests/`, `data/raw/`, `data/analysis/`, `paper/`
- [X] T001b [P] Create empty placeholder files in `code/src/` subpackages (`__init__.py`) and `code/tests/__init__.py`
- [X] T001c [P] Create `.gitignore` for Python (`__pycache__`, `.pyc`, `data/`, `paper/`) in repository root

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. T000 is the mandatory gate for Constitution Principle II.

### MANDATORY GATE: Reference Validation

- [X] T000 [P] **MANDATORY GATE**: Create `code/src/utils/reference_validator.py` and execute it to verify all citations in `plan.md` and `spec.md` against primary sources. Output: `state/citations_verified.json`. **This task MUST pass before T002, T004c, or any other Foundational task can begin.** If validation fails, the pipeline halts with exit code 1. The Reference-Validator is an internal implementation artifact; the pipeline fails only if the result (verified citations) is missing or contains errors.

### Logging & Configuration Infrastructure

- [X] T002 [P] Initialize Python project with pinned dependencies in `code/requirements.txt` (networkx, numpy, scipy, matplotlib, seaborn, pandas, pytest, coverage.py). **Depends on T000 passing.**
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `code/`
- [X] T004c [P] Create `code/config.yaml` as the immutable source of truth for global seeds, topology targets, simulation parameters, and `simulation_timeout_seconds`. Output: `code/config.yaml` with a template structure including keys: `global_seed`, `topology_targets`, `simulation_params`, `simulation_timeout_seconds`, `stratification_params`. **Depends on T000 passing.**
- [ ] T004b [P] [FR-007] Implement seed injection logic in `code/src/utils/config.py` to load `global_seed` from `config.yaml` and propagate it to all generators. **Depends on T004c.** This task MUST explicitly set `numpy.random.seed(seed)`, `random.seed(seed)`, and pass `random_state=seed` to `networkx.watts_strogatz_graph`, `networkx.barabasi_albert_graph`, and `networkx.erdos_renyi_graph`. <!-- FAILED: unspecified -->
- [ ] T005 [US1] Create `code/src/utils/logging.py` to initialize logging infrastructure. **Depends on T004c and T004b.** This task MUST create `data/run_log.json` as an empty JSON array `[]` if it does not exist, and implement `log_metric` helper to append entries with fields: `timestamp` (ISO 8601), `event_type` (enum: graph_generated, simulation_start, simulation_end, divergence_detected, timeout_reached), `run_id` (string), `seed` (int), `status` (string), `duration_seconds` (float). **Events to log**: `graph_generated`, `simulation_start`, `simulation_end`, `divergence_detected`, `timeout_reached`.
- [X] T006 [P] Create `code/src/utils/io.py` for saving/loading graphs (`gpickle`, `json`) and managing `data/` directory checksums <!-- FAILED: unspecified -->
- [X] T007 [P] Implement base configuration loader in `code/src/utils/config.py` to validate `config.yaml` against required schema
- [X] T008 [P] Setup `code/tests/conftest.py` with fixtures for temporary data directories and seeded random states

### Stratified Sampling & Connectivity (Moved from Phase 6 to Phase 2)

- [X] T062a [P] [FR-001][SC-005] Define stratification configuration in `code/config.yaml` under `stratification_params`: keys `bins` (list of floats: 0.1, 0.2, 0.3, 0.4, 0.5), `target_counts` (dict mapping bin to count), and `tolerance` (float).
- [X] T062b [P] [FR-001][SC-005] Implement binning logic in `code/src/generators/binning.py` to classify generated graphs into clustering coefficient bins. Output: `code/src/generators/binning.py` with function `classify_graph(graph)`.
- [X] T062c [US1] [FR-001][SC-005] Implement stratified sampling loop controller in `code/src/generators/stratified_runner.py` that explicitly enforces target distribution by generating graphs until bin quotas are met. **Depends on T062a, T062b, T056, and T018.** This task MUST call T062f to trigger generation and T062e to check quotas.
- [X] T062e [P] [FR-001][SC-005] Implement quota checker in `code/src/generators/quota_checker.py`. Output: `code/src/generators/quota_checker.py` with function `check_quotas(current_counts, target_counts)` returning a boolean. **Depends on T062a.**
- [X] T062f [P] [FR-001][SC-005] Implement graph generation trigger in `code/src/generators/generation_trigger.py`. Output: `code/src/generators/generation_trigger.py` with function `generate_for_bin(bin_id, count)`. **Depends on T013, T014, T015.**
- [ ] T056 [US1] [FR-001] Implement 'Sample Size Adjustment' logic in `code/src/generators/batch_runner.py` to adjust batch size if rejection rate exceeds threshold, based on configuration in `config.yaml`. **Depends on T004c and T018.** This task MUST calculate rejection rate as `rejected_attempts / total_attempts`. If rate > 0.2, it MUST increase `batch_size` by [deferred] for the next iteration. <!-- FAILED: unspecified -->
- [X] T018c [P] [FR-004][FR-001] Implement function `aggregate_batches` in `code/src/generators/aggregate_batch.py` to define the output schema for `global_batch_manifest.json` including `stratification_summary`. **Depends on T018.**
- [X] T062d [P] [FR-001][SC-005] Update `data/raw/global_batch_manifest.json` schema to include `stratification_summary` (bin counts). **Depends on T018c.**
- [X] T051 [P] [FR-001] Implement explicit connectivity verification in `code/src/generators/base.py` to enforce `nx.is_connected()` before returning any generated graph. This task MUST include a retry loop for each graph; if multiple attempts fail, the system MUST log a warning and proceed to the next graph (per spec edge case). Output: Modified `code/src/generators/base.py` and unit test `code/tests/test_generators.py::test_sw_retries_on_disconnect`.
- [X] T018b [P] [FR-001] Implement a configurable retry logic for disconnected networks in `code/src/generators/retry_logic.py`. Logic: Must reference T051 as the primary source of truth for retry behavior.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate synthetic spin network datasets (Priority: P1) 🎯 MVP

**Goal**: Generate connected graphs (Erdős-Rényi, Scale-Free, Small-World) with controlled clustering coefficients and verify topology metrics.

**Independent Test**: Can be fully tested by generating a batch of networks, computing their topological metrics, and verifying the distributions match expected parameters.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T009 [P] [US1] Unit test for Erdős-Rényi generation in `code/tests/test_generators.py` implementing `test_er_generates_connected_graph` to verify connectivity and edge probability, and `test_er_clustering_distribution` to verify clustering coefficient distribution.
- [X] T010 [P] [US1] Unit test for Watts-Strogatz (Small-World) generation in `code/tests/test_generators.py` implementing `test_sw_retries_on_disconnect` to verify -attempt retry logic and `test_sw_clustering_target` to verify clustering coefficient target achievement.
- [X] T011 [P] [US1] Unit test for Barabási-Albert (Scale-Free) generation in `code/tests/test_generators.py` implementing `test_sf_power_law_fit` to verify degree distribution R² ≥ 0.95.
- [X] T012 [P] [US1] Integration test in `code/tests/test_integration.py` implementing `test_batch_success_rate` to verify ≥95% success rate for valid connected graphs and `test_manifest_generation` to verify `global_batch_manifest.json` content.

### Implementation for User Story 1

- [X] T016 [P] [US1] Implement base generator logic in `code/src/generators/base.py` with shared logic for connectivity checks, a configurable retry limit (read from `config.yaml`), and warning logging.
- [X] T013 [P] [US1] Implement Erdős-Rényi generator in `code/src/generators/er.py` inheriting from base
- [X] T014 [P] [US1] Implement Watts-Strogatz generator in `code/src/generators/sw.py` inheriting from base
- [X] T015 [P] [US1] Implement Barabási-Albert generator in `code/src/generators/sf.py` inheriting from base
- [X] T017 [P] [US1] Implement metric extraction function in `code/src/generators/metrics.py` (degree distribution, clustering, average path length). **Depends on T016.** This task MUST write metrics to the `global_batch_manifest.json` defined in T018c.
- [X] T019 [P] [US1] Implement metadata logging module in `code/src/generators/metadata.py` to record algorithm, edge_probability, preferential_attachment_params, and seed for every generated graph, saving to `data/metadata/graph_<id>.json`.
- [ ] T018 [US1] Create `code/src/generators/batch_runner.py` with a `main()` function that loads `config.yaml` and iterates over topology classes to generate batches. **Depends on T004c and T016.** <!-- FAILED: unspecified -->
- [X] T018c [P] [FR-004][FR-001] Implement function `aggregate_batches` in `code/src/generators/aggregate_batch.py` to define the output schema for `global_batch_manifest.json` including `stratification_summary`. **Depends on T018.**

---

## Phase 4: User Story 2 - Run energy propagation simulation (Priority: P2)

**Goal**: Execute simplified Ising spin-flip dynamics on generated networks, measure diffusion rates, and ensure numerical stability on CPU.

**Independent Test**: Can be fully tested by running the simulator on a single network, verifying the energy density profile evolves, and confirming spatial variance increases.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Unit test for spin-flip logic in `code/tests/test_simulation.py` implementing `test_energy_conservation_within_tolerance` and `test_spin_flip_boltzmann_match`.
- [X] T022 [P] [US2] Unit test for spatial variance calculation in `code/tests/test_simulation.py` implementing `test_spatial_variance_calculation`.
- [X] T023 [P] [US2] Unit test for divergence detection and abort logic in `code/tests/test_simulation.py` implementing `test_divergence_raises_error`.

### Implementation for User Story 2

- [X] T024 [P] [US2] Implement simplified Ising spin-flip dynamics in `code/src/simulation/dynamics.py` (CPU-only, no GPU dependencies).
- [X] T025 [P] [US2] Implement energy density profile tracking and spatial variance calculation in `code/src/simulation/metrics.py`.
- [X] T026 [P] [US2] Implement numerical stability checks (divergence detection) in `code/src/simulation/stability.py`.
- [ ] T070 [US2] [FR-002][SC-002] Implement **CPU-time profiling** in `code/src/simulation/profiler.py` to measure per-step execution time and validate SC-002 (≤60 min runtime) during unit tests. **Depends on T024.** This task MUST measure `time_per_spin_flip_iteration` and output to `data/analysis/profiler_report.json`.
- [X] T026a [US2] [FR-002][SC-002] Implement energy conservation check in `code/src/simulation/dynamics.py`. **Depends on T024 and T025.** This task MUST call the `get_energy_profile()` function from T025 to access the energy values and verify conservation within a specified tolerance.
- [ ] T026b [US2] Implement hard runtime abort mechanism and logging in `code/src/simulation/stability.py`. **Depends on T029a (schema), T005 (logging), T004c (config), and T070.** This task MUST enforce the time limit defined in `config.yaml` under `simulation_params.timeout_seconds`. It MUST use `signal.alarm(simulation_params.timeout_seconds)` for Unix systems or `threading.Timer` for cross-platform, ensuring a hard abort on timeout. **Must run BEFORE T028.** It MUST log `runtime_duration_seconds` to the schema defined in T029a.
- [X] T052 [US2] Add explicit numerical stability assertions in `code/src/simulation/stability.py` to detect energy divergence.
- [X] T027 [US2] Implement diffusion rate calculator in `code/src/simulation/diffusion.py`. **Depends on T025.** This task MUST calculate `diffusion_rate` as the rate of change of spatial variance over time steps and return it as a field in the dictionary passed to the serialization function defined in T029.
- [X] T027b [US2] Implement transient phase metric extraction in `code/src/simulation/metrics.py`.
- [X] T028 [US2] Create simulation runner script in `code/src/simulation/run_simulation.py`. **Depends on T026b (runtime logging), T029a (schema), and T070 (profiling).** This task MUST explicitly measure and log `runtime_duration_seconds` and populate the schema defined in T029a.
- [ ] T029 [US2] Implement result serialization to `data/analysis/simulation_results.json`. **Depends on T028.**
- [ ] T029a [P] [FR-003] Define JSON schema for `simulation_results.json` including `runtime_duration_seconds`, `generation_algorithm`, and `diffusion_rate`. **Depends on T004c.**

**Checkpoint**: At this point, User Story 1 and User Story 2 should both be functional independently

---

## Phase 5: User Story 3 - Correlate metrics and test significance (Priority: P3)

**Goal**: Perform regression/ANOVA analysis, apply multiple-comparison correction, run sensitivity sweeps, and generate figures.

**Independent Test**: Can be fully tested by running the analysis pipeline on a pre-generated dataset, verifying statistical tests produce p-values, and confirming figures are generated.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T030 [P] [US3] Unit test for regression analysis in `code/tests/test_analysis.py`.
- [X] T031 [P] [US3] Unit test for ANOVA and multiple-comparison correction (Bonferroni/BH) in `code/tests/test_analysis.py`.
- [X] T032 [P] [US3] Unit test for sensitivity sweep logic in `code/tests/test_analysis.py`.

### Implementation for User Story 3

- [X] T033 [P] [US3] Implement linear and non-linear regression in `code/src/analysis/regression.py`
- [X] T034a [P] [US3] Implement ANOVA testing in `code/src/analysis/anova.py`.
- [X] T034b [P] [US3] Implement multiple-comparison correction (Bonferroni and Benjamini-Hochberg) in `code/src/analysis/anova.py`.
- [X] T035a [P] [US3] Define JSON schema for sensitivity sweep results.
- [ ] T035b [US3] [FR-008] Implement sensitivity sweep for clustering coefficient thresholds in `code/src/analysis/sensitivity.py`. **Depends on T029 and T004c.** Input: list of thresholds ranging from low to moderate values (read from `config.yaml` under `stratification_params.bins`). Output: `data/analysis/sensitivity_sweep.json`. This task MUST iterate over the thresholds, run the simulation/analysis for each, and record the results.
- [~] T035c [US3] [FR-008] Implement correlation of thresholds with diffusion rates in `code/src/analysis/sensitivity.py`. **Depends on T035b.** This task MUST perform a linear regression of `threshold` vs `diffusion_rate` and save the coefficients to `data/analysis/sensitivity_sweep.json`. <!-- FAILED: unspecified -->
- [X] T044 [US3] Implement statistical power analysis in `code/src/analysis/power.py`. **Depends on T037b.**
- [X] T044a [US3] Implement 'Sample Size Adjustment' feedback loop in `code/src/analysis/power.py`. **Depends on T044, T037b, and T044b.** This task MUST re-run batch generation if power is insufficient. <!-- ATOMIZE: requested -->
- [X] T044b [P] [FR-001] Implement 'Re-entrant Batch Runner' wrapper in `code/src/analysis/power.py`. **Depends on T018.** This task MUST wrap T018 to make it re-entrant by resetting the `global_batch_manifest.json` and re-seeding the generator, handling the state reset required for the feedback loop. <!-- ATOMIZE: requested -->
- [X] T045a [US3] Implement batch validation logic in `code/src/validation/validate_batch.py`.
- [X] T046 [P] Add `pytest` coverage report generation
- [X] T047 [P] Update `code/README.md` **Installation** section with environment setup instructions
- [X] T048 [P] Update `code/README.md` **Usage** section with execution commands
- [X] T057 [P] [FR-005] Implement Partial Correlation analysis in `code/src/analysis/regression.py`. **Depends on T029.**
- [X] T058 [P] [FR-005] Implement Ridge Regression analysis in `code/src/analysis/regression.py`. **Depends on T029.**
- [X] T037a [US3] [FR-005] Implement data loading/merging logic in `code/src/analysis/aggregate_results.py`. **Depends on T035c, T057, T058, and T029.** This task MUST load all required JSON artifacts and merge them into a single DataFrame.
- [X] T037c [P] [FR-005] Implement statistical aggregation logic in `code/src/analysis/aggregate_results.py`. **Depends on T037a.** This task MUST compute summary statistics (mean, std, etc.) for the merged data.
- [X] T037d [P] [FR-005] Implement final serialization in `code/src/analysis/aggregate_results.py`. **Depends on T037c.** This task MUST write the aggregated results to `data/analysis/aggregated_results.json`.
- [X] T037b [US3] [FR-005] Implement statistical reporting in `code/src/analysis/statistics.py`. **Depends on T037a.**
- [X] T059 [US3] [FR-005] Implement integration test for full analysis pipeline in `code/tests/test_integration.py`. **Depends on T057, T058, and T037a.**

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T041 [P] Update `code/README.md` **Installation** section with environment setup instructions
- [X] T042 [P] Update `code/README.md` **Usage** section with execution commands
- [X] T043 [P] Update `code/README.md` **Configuration** section with `config.yaml` explanation
- [X] T063 [US2] Add explicit **energy conservation check** in `code/src/simulation/dynamics.py`.
- [X] T064a [P] [FR-005] Define VIF threshold in `code/config.yaml` under `collinearity_params`.
- [X] T064b [P] [FR-005] Implement VIF calculation function in `code/src/analysis/regression.py`.
- [X] T064c [P] [FR-005] Implement logging of VIF scores to `data/analysis/collinearity_report.json`.
- [X] T065 [US3] Add a **robustness check** task in `code/src/analysis/plot_results.py` to generate a "sensitivity heatmap".
- [X] T066a [P] [FR-003] Define IQR multiplier in `code/config.yaml` under `outlier_params`.
- [X] T066b [P] [FR-003] Implement IQR calculation and flagging logic in `code/src/analysis/aggregate_results.py`.
- [X] T066c [P] [FR-003] Implement exclusion logic in `aggregate_results.py` to flag or exclude extreme diffusion rate outliers based on IQR.
- [X] T067 [US3] Add **automated seed rotation** logic in `code/main.py`.

---

## Phase 6: Review & Revision (Post-Analyze Fixes)

**Purpose**: Address specific gaps identified by the `/speckit.analyze` agent regarding task granularity, edge case handling, and data flow integrity.

- [X] T068 [P] [FR-001] Verify `data/raw/global_batch_manifest.json` contains `stratification_summary` after T018c execution.
- [X] T069 [P] [FR-003] Verify `data/analysis/simulation_results.json` contains `runtime_duration_seconds` after T029 execution.
- [ ] T071 [US3] [FR-006] Add explicit **Bonferroni vs. BH comparison** task in `code/src/analysis/anova.py` to log both correction methods and report which is selected based on `config.yaml` preference. **Depends on T034b.** This task MUST ensure the output artifact `data/analysis/statistical_report.json` contains a `correction_methods` object listing both Bonferroni and BH results, and a `selected_method` field indicating the one used per config. [UNRESOLVED-CLAIM: c_42e8eac5 — status=not_enough_info]
- [ ] T072 [US3] [FR-008] Implement **threshold sweep visualization** in `code/src/analysis/plot_results.py` to generate a line plot of diffusion rate vs. clustering threshold, ensuring ≥5 distinct points are plotted. **Depends on T035c.**
- [ ] T073 [US3] [ROC-001] Add **associational framing check** in `code/src/analysis/report_generator.py` to automatically append a disclaimer to all generated figures and tables stating "Findings are associational, not causal (ROC-001)." **Depends on T037b.** This task MUST run after T037b and append the exact string to all figure captions and table footers.
- [ ] T074 [US1] [FR-001] Implement **graph diversity validator** in `code/src/generators/validate_batch.py` to ensure the final batch contains at least 3 distinct topology classes (ER, SF, WS) and that No single class exceeds a majority of the total batch. [UNRESOLVED-CLAIM: c_2219119d — status=not_enough_info] **Depends on T018.** This task MUST return a status object. [UNRESOLVED-CLAIM: c_2b7fb994 — status=not_enough_info]
- [X] T074a [P] [FR-001] Implement **graph diversity enforcement runner** in `code/src/generators/validate_batch.py`. **Depends on T074.** This task MUST act on the status object from T074 to flag or reject batches.
- [X] T075 [US2] [FR-003] Add **spatial variance monotonicity check** in `code/src/simulation/metrics.py` to verify that spatial variance increases (or remains stable) over time steps, flagging any runs where it decreases significantly as potential numerical artifacts. **Depends on T025.**