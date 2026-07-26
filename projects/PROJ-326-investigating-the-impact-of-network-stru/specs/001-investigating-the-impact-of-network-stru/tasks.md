# Task List: Network Topology Energy Transfer in Spin Systems

**Version**: 1.0.1  
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
- [X] T004c [P] Create `code/config.yaml` as the immutable source of truth for global seeds, topology targets, simulation parameters, and `simulation_timeout_seconds`. Output: `code/config.yaml` with a template structure including keys: `global_seed`, `topology_targets`, `simulation_params`, `simulation_timeout_seconds`. **Depends on T000 passing.**
- [ ] T005 [US1] Create `code/src/utils/logging.py` to initialize logging infrastructure. **Depends on T004c.** This task MUST create `data/run_log.json` as an empty JSON array `[]` if it does not exist, and implement `log_metric` helper to append entries with fields: `timestamp`, `event_type`, `run_id`, `seed`, `status`, and `duration_seconds`. **Events to log**: `graph_generated`, `simulation_start`, `simulation_end`, `divergence_detected`, `timeout_reached`.
- [ ] T004b [P] [FR-007] Implement seed injection logic in `code/src/utils/config.py` to load `global_seed` from `config.yaml` and propagate it to all generators. **Depends on T005 (logging init) and T004c.**
- [ ] T006 [P] Create `code/src/utils/io.py` for saving/loading graphs (`gpickle`, `json`) and managing `data/` directory checksums
- [X] T007 [P] Implement base configuration loader in `code/src/utils/config.py` to validate `config.yaml` against required schema
- [X] T008 [P] Setup `code/tests/conftest.py` with fixtures for temporary data directories and seeded random states

### Stratified Sampling & Connectivity (Moved from Phase 6 to Phase 2)

- [X] T062a [P] [FR-001][SC-005] Define stratification configuration in `code/config.yaml` under `stratification_params`: keys `bins` (list of floats: 0.1, 0.2, 0.3, 0.4, 0.5), `target_counts` (dict mapping bin to count), and `tolerance` (float).
- [X] T062b [P] [FR-001][SC-005] Implement binning logic in `code/src/generators/binning.py` to classify generated graphs into clustering coefficient bins. Output: `code/src/generators/binning.py` with function `classify_graph(graph)`.
- [ ] T062c [US1] [FR-001][SC-005] Implement stratified sampling loop in `code/src/generators/stratified_runner.py` that explicitly enforces target distribution by generating graphs until bin quotas are met. **Depends on T062a and T062b.**
- [X] T062d [P] [FR-001][SC-005] Update `data/raw/global_batch_manifest.json` schema to include `stratification_summary` (bin counts).
- [X] T051 [P] [FR-001] Implement explicit connectivity verification in `code/src/generators/base.py` to enforce `nx.is_connected()` before returning any generated graph. This task MUST include a retry loop for each graph; if multiple attempts fail, the system MUST log a warning and proceed to the next graph (per spec edge case). Output: Modified `code/src/generators/base.py` and unit test `code/tests/test_generators.py::test_sw_retries_on_disconnect`.
- [X] T018b [P] [FR-001] Implement a configurable retry logic for disconnected networks in `code/src/generators/retry_logic.py`. Logic: Must reference T051 as the primary source of truth for retry behavior.
- [ ] T056 [US1] [FR-001] Implement 'Sample Size Adjustment' logic in `code/src/generators/batch_runner.py` to adjust batch size if rejection rate exceeds threshold, based on configuration in `config.yaml`. **Depends on T004c.**

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
- [X] T017 [P] [US1] Implement metric extraction function in `code/src/generators/metrics.py` (degree distribution, clustering, average path length)
- [X] T019 [P] [US1] Implement metadata logging module in `code/src/generators/metadata.py` to record algorithm, edge_probability, preferential_attachment_params, and seed for every generated graph, saving to `data/metadata/graph_<id>.json`.
- [ ] T018 [US1] Create `code/src/generators/batch_runner.py` with a `main()` function that loads `config.yaml` and iterates over topology classes to generate batches. **Depends on T004c and T016.**
- [ ] T018c [P] [FR-001] Implement function `aggregate_batches` in `code/src/generators/aggregate_batch.py` to define the output schema for `global_batch_manifest.json` including `stratification_summary`. **Depends on T018.**

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
- [ ] T026b [US2] Implement hard runtime abort mechanism and logging in `code/src/simulation/stability.py`. **Depends on T029a (schema) and T005 (logging).** This task MUST enforce the time limit defined in `config.yaml` and log `timeout_reached` events. **Must run BEFORE T028.**
- [X] T052 [US2] Add explicit numerical stability assertions in `code/src/simulation/stability.py` to detect energy divergence.
- [ ] T026a [US2] Implement energy conservation check in `code/src/simulation/dynamics.py`.
- [ ] T027 [US2] Implement diffusion rate calculator in `code/src/simulation/diffusion.py`.
- [~] T027b [US2] Implement transient phase metric extraction in `code/src/simulation/metrics.py`.
- [ ] T028 [US2] Create simulation runner script in `code/src/simulation/run_simulation.py`. **Depends on T026b (runtime logging) and T029a (schema).** This task MUST explicitly measure and log `runtime_duration_seconds` and populate the schema defined in T029a.
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

- [ ] T033 [P] [US3] Implement linear and non-linear regression in `code/src/analysis/regression.py`
- [ ] T034a [P] [US3] Implement ANOVA testing in `code/src/analysis/anova.py`.
- [ ] T034b [P] [US3] Implement multiple-comparison correction (Bonferroni and Benjamini-Hochberg) in `code/src/analysis/anova.py`.
- [ ] T035a [P] [US3] Define JSON schema for sensitivity sweep results.
- [ ] T035b [US3] [FR-008] Implement sensitivity sweep for clustering coefficient thresholds in `code/src/analysis/sensitivity.py`. **Depends on T029.**
- [ ] T035c [US3] [FR-008] Implement correlation of thresholds with diffusion rates in `code/src/analysis/sensitivity.py`. **Depends on T035b.**
- [ ] T044 [US3] Implement statistical power analysis in `code/src/analysis/power.py`. **Depends on T037b.**
- [ ] T044a [US3] Implement 'Sample Size Adjustment' feedback loop in `code/src/analysis/power.py`. **Depends on T044, T037b, and T018.** This task MUST re-run batch generation if power is insufficient.
- [ ] T045a [US3] Implement batch validation logic in `code/src/validation/validate_batch.py`.
- [ ] T046 [P] Add `pytest` coverage report generation
- [ ] T047 [P] Update `code/README.md` **Installation** section with environment setup instructions
- [ ] T048 [P] Update `code/README.md` **Usage** section with execution commands
- [ ] T057 [P] [FR-005] Implement Partial Correlation analysis in `code/src/analysis/regression.py`. **Depends on T029.**
- [ ] T058 [P] [FR-005] Implement Ridge Regression analysis in `code/src/analysis/regression.py`. **Depends on T029.**
- [ ] T037a [US3] [FR-005] Implement aggregation of results in `code/src/analysis/aggregate_results.py`. **Depends on T035c, T057, T058, and T029.**
- [ ] T037b [US3] [FR-005] Implement statistical reporting in `code/src/analysis/statistics.py`. **Depends on T037a.**
- [ ] T059 [US3] [FR-005] Implement integration test for full analysis pipeline in `code/tests/test_integration.py`. **Depends on T057, T058, and T037a.**

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T041 [P] Update `code/README.md` **Installation** section with environment setup instructions
- [X] T042 [P] Update `code/README.md` **Usage** section with execution commands
- [X] T043 [P] Update `code/README.md` **Configuration** section with `config.yaml` explanation
- [ ] T063 [US2] Add explicit **energy conservation check** in `code/src/simulation/dynamics.py`.
- [ ] T064a [P] [FR-005] Define VIF threshold in `code/config.yaml` under `collinearity_params`.
- [ ] T064b [P] [FR-005] Implement VIF calculation function in `code/src/analysis/regression.py`.
- [ ] T064c [P] [FR-005] Implement logging of VIF scores to `data/analysis/collinearity_report.json`.
- [ ] T065 [US3] Add a **robustness check** task in `code/src/analysis/plot_results.py` to generate a "sensitivity heatmap".
- [ ] T066a [P] [FR-003] Define IQR multiplier in `code/config.yaml` under `outlier_params`.
- [ ] T066b [P] [FR-003] Implement IQR calculation and flagging logic in `code/src/analysis/aggregate_results.py`.
- [ ] T066c [P] [FR-003] Implement exclusion logic in `aggregate_results.py` to flag or exclude extreme diffusion rate outliers based on IQR.
- [ ] T067 [US3] Add **automated seed rotation** logic in `code/main.py`.

---

## Phase 6: Review & Revision (Post-Analyze Fixes)

**Purpose**: Address specific gaps identified by the `/speckit.analyze` agent regarding task granularity, edge case handling, and data flow integrity.

- [ ] T068 [P] [FR-001] Verify `data/raw/global_batch_manifest.json` contains `stratification_summary` after T018c execution.
- [ ] T069 [P] [FR-003] Verify `data/analysis/simulation_results.json` contains `runtime_duration_seconds` after T029 execution.