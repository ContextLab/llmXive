# Tasks: Network Topology Energy Transfer in Spin Systems

**Version**: 1.4.0
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

- [X] T001a [P] Create project directories: `code/`, `code/src/`, `code/src/generators/`, `code/src/simulation/`, `code/src/analysis/`, `code/src/utils/`, `code/tests/`, `data/raw/`, `data/analysis/`, `paper/`. **Verification**: Verify directories exist via `os.path.isdir` or `ls`.
- [X] T001b [P] Create empty placeholder files in `code/src/` subpackages (`__init__.py`) and `code/tests/__init__.py`. **Verification**: Verify file existence and size == 0.
- [X] T001c [P] Create `.gitignore` for Python (`__pycache__`, `.pyc`, `data/`, `paper/`) in repository root. **Verification**: Verify file exists and contains specific patterns.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. T000 is the mandatory gate for Constitution Principle II.

### MANDATORY GATE: Reference Validation

- [X] T000 [P] **MANDATORY GATE**: Create `code/src/utils/reference_validator.py` and execute it to verify all citations in `plan.md` and `spec.md`. Output: `state/citations_verified.json`. **This task MUST pass before T002, T004c, or any other Foundational task can begin.** If validation fails, the pipeline halts with exit code 1. The Reference-Validator is an internal implementation artifact; the pipeline fails only if the result (verified citations) is missing or contains errors.

### Logging & Configuration Infrastructure

- [X] T002 [P] Initialize Python project with pinned dependencies in `code/requirements.txt` (networkx, numpy, scipy, matplotlib, seaborn, pandas, pytest, coverage.py). **Depends on T000 passing.** **Verification**: Run `pip install -r requirements.txt --dry-run` or verify file content against the list.
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `code/`. **Verification**: Run `ruff check .` and `black --check .` to ensure no errors.
- [X] T004c [P] Create `code/config.yaml` as the immutable source of truth for global seeds, topology targets, simulation parameters, and `simulation_timeout_seconds`. Output: `code/config.yaml` with a template structure including keys: `global_seed`, `topology_targets`, `simulation_params`, `simulation_timeout_seconds`, `stratification_params`. **Depends on T000 passing.**
- [X] T004b [P] Implement seed injection logic in `code/src/utils/config.py` to load `global_seed` from `config.yaml` and propagate it to all generators, simulation, and analysis modules. **Depends on T004c (completion required).** This task MUST explicitly set `numpy.random.seed(seed)`, `random.seed(seed)`, and pass `random_state=seed` to `networkx.watts_strogatz_graph`, `networkx.barabasi_albert_graph`, `networkx.erdos_renyi_graph`, and all simulation/analysis functions. Output: `code/src/utils/config.py` with function `load_config() -> dict` and `set_seed(seed: int) -> None`.
- [X] T005 [P] Create `code/src/utils/logging.py` to initialize logging infrastructure. **Depends on T004c and T004b (completion required).** This task MUST create `data/run_log.json` as an empty JSON array `[]` if it does not exist, and implement `log_metric` helper to append entries with fields: `timestamp` (ISO 8601), `event_type` (enum: graph_generated, simulation_start, simulation_end, divergence_detected, timeout_reached), `run_id` (string), `seed` (int), `status` (string), `duration_seconds` (float). **Events to log**: `graph_generated`, `simulation_start`, `simulation_end`, `divergence_detected`, `timeout_reached`. **Verification**: Verify `data/run_log.json` exists as `[]` and `log_metric` appends a valid JSON object with required fields. Output: `code/src/utils/logging.py` with functions `init_logging() -> None` and `log_metric(event: dict) -> None`.
- [X] T006 [P] Create `code/src/utils/io.py` for saving/loading graphs (`gpickle`, `json`) and managing `data/` directory checksums. **Output**: `state/checksums.json`. **Verification**: Verify `state/checksums.json` exists and contains valid SHA-256 hashes for `data/` files using `hashlib`.
- [X] T007 [P] Implement base configuration loader in `code/src/utils/config.py` to validate `config.yaml` against required schema. **Verification**: Run a unit test that loads `config.yaml` and asserts schema validity.
- [X] T008 [P] Setup `code/tests/conftest.py` with fixtures for temporary data directories and seeded random states. **Verification**: Run a dummy test using the fixtures to ensure they initialize correctly.

---

## Phase 3: User Story 1 - Generate synthetic spin network datasets (Priority: P1) 🎯 MVP

**Goal**: Generate connected graphs (Erdős-Rényi, Scale-Free, Small-World) with controlled clustering coefficients and verify topology metrics.

**Independent Test**: Can be fully tested by generating a batch of networks, computing their topological metrics, and verifying the distributions match expected parameters.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T009 [P] [US1] Unit test for Erdős-Rényi generation in `code/tests/test_generators.py` implementing `test_er_generates_connected_graph` to verify connectivity and edge probability, and `test_er_clustering_distribution` to verify clustering coefficient distribution.
- [X] T010 [P] [US1] Unit test for Watts-Strogatz (Small-World) generation in `code/tests/test_generators.py` implementing `test_sw_retries_on_disconnect` to verify -attempt retry logic and `test_sw_clustering_target` to verify clustering coefficient target achievement.
- [X] T011 [P] [US1] Unit test for Barabási-Albert (Scale-Free) generation in `code/tests/test_generators.py` implementing `test_sf_power_law_fit` to verify degree distribution R² ≥ 0.95.
- [X] T012 [P] [US1] Integration test in `code/tests/test_integration.py` implementing `test_batch_success_rate` to verify ≥95% success rate for valid connected graphs and `test_manifest_generation` to verify `global_batch_manifest.json`.

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement Erdős-Rényi generator in `code/src/generators/er.py` inheriting from base
- [X] T014 [P] [US1] Implement Watts-Strogatz generator in `code/src/generators/sw.py` inheriting from base
- [X] T015 [P] [US1] Implement Barabási-Albert generator in `code/src/generators/sf.py` inheriting from base
- [X] T016 [P] [US1] Implement base generator logic in `code/src/generators/base.py` with shared logic for connectivity checks, a configurable retry limit (read from `config.yaml`, default a standard threshold if missing), and warning logging. **Note**: Includes strict connectivity retry enforcement with configurable max_retries.
- [X] T017 [P] [US1] [FR-004] Implement metric extraction logic (degree distribution, clustering, average path length) as required by FR-004 in `code/src/generators/metrics.py`. **Depends on T016.** This task MUST write metrics to the `global_batch_manifest.json` defined in T018c.
- [X] T018a [P] [US1] Create `code/src/generators/batch_runner.py` file structure. **Depends on T004c and T016.**
- [X] T018b [P] [US1] Implement `main()` orchestration logic in `code/src/generators/batch_runner.py`. **Depends on T018a.** This task MUST load `config.yaml` and initialize the generation pipeline.
- [X] T018c [P] [US1] [FR-004][FR-001] Implement iteration logic over topology classes and aggregate_batches in `code/src/generators/batch_runner.py` to define the output schema for `global_batch_manifest.json` including `stratification_summary`. **Depends on T018b.** **Verification**: Run `code/tests/contract/test_schemas.py::test_manifest_stratification` to verify.
- [X] T019 [P] [US1] Implement metadata logging module in `code/src/generators/metadata.py` to record algorithm, edge_probability, preferential_attachment_params, and seed for every generated graph, saving to `data/metadata/graph_<id>.json`.
- [X] T020 [P] [FR-001] Implement stratified sampling loop controller in `code/src/generators/stratified_runner.py` that explicitly enforces target distribution by generating graphs until bin quotas are met. **Depends on T062a, T062b and T018.**
- [X] T062a [P] [FR-001][SC-005] Define stratification configuration in `code/config.yaml` under `stratification_params`: keys `bins` (list of floats: 0.1, 0.2, 0.3, 0.4, 0.5), `target_counts` (dict mapping bin to count), and `tolerance` (float). **Depends on FR-001/SC-005 stratification configuration.**
- [X] T062b [P] [FR-001][SC-005] Implement binning logic in `code/src/generators/binning.py` to classify generated graphs into clustering coefficient bins. **Depends on T062a.**
- [X] T062c [P] [US1] [FR-001][SC-005] Implement stratified sampling loop controller in `code/src/generators/stratified_runner.py` that explicitly enforces target distribution by generating graphs until bin quotas are met. **Depends on T062a, T062b and T018.**
- [X] T062e [P] [FR-001][SC-005] Implement quota checker in `code/src/generators/quota_checker.py`. **Depends on T062a.**
- [X] T062f [P] [FR-001][SC-005] Implement graph generation trigger in `code/src/generators/generation_trigger.py`. **Depends on T013, T014, T015, T016.**

---
## Phase 4: User Story 2 - Run energy propagation simulation (Priority: P2)

**Goal**: Execute simplified Ising spin-flip dynamics on generated networks, measure diffusion rates, and ensure numerical stability on CPU.

**Independent Test**: Can be fully tested by running the simulator on a single network, verifying the energy density profile evolves, and confirming spatial variance increases.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Unit test for spin-flip logic in `code/tests/test_simulation.py` implementing `test_energy_conservation_within_tolerance` and `test_spin_flip_boltzmann_match`.
- [X] T022 [P] [US2] Unit test for spatial variance calculation in `code/tests/test_simulation.py` implementing `test_spatial_variance_calculation`.
- [X] T023 [P] [US2] Unit test for divergence detection and abort logic in `code/tests/test_simulation.py` implementing `test_divergence_raises_error`.

### Implementation for User Story 2

- [X] T024 [P] [US2] Implement simplified Ising spin-flip dynamics in `code/src/simulation/dynamics.py` (CPU-only, no GPU dependencies). **Note**: Must explicitly log and store 'null results' (no correlation) as reproducible artifacts to satisfy Constitution Principle I.
- [X] T025 [P] [US2] Implement energy density profile tracking and spatial variance calculation in `code/src/simulation/metrics.py`.
- [X] T026 [P] [US2] Implement numerical stability checks (divergence detection) in `code/src/simulation/stability.py`.
- [X] T070 [US2] [FR-002][SC-002][FR-010] Implement **CPU-time profiling** in `code/src/simulation/profiler.py` to measure per-step execution time and explicitly validate FR-010 (100 steps < 60 mins) in the full pipeline context.
- [X] T070b [US2] [FR-002][SC-002][FR-010] Implement **FR-010 Validation** in `code/src/simulation/profiler.py`.

- [X] T027 [US2] Implement diffusion rate calculator in `code/src/simulation/diffusion.py`.
- [X] T028a [US2] Create simulation runner script in `code/src/simulation/run_simulation.py`.
- [X] T029 [US2] Implement result serialization to `data/analysis/simulation_results.json`.

---

## Phase 5: User Story 3 - Correlate metrics and test significance (Priority: P3)

**Goal**: Perform regression/ANOVA analysis, apply multiple-comparison correction, run sensitivity sweeps, and generate figures.

**Independent Test**: Can be fully tested by running the analysis pipeline on a pre-generated dataset, verifying statistical tests produce p-values, and confirming figures are generated.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T030 [P] [US3] Unit test for regression analysis in `code/tests/test_analysis.py`.
- [X] T031 [P] [US3] Unit test for ANOVA and multiple-comparison correction (Bonferroni/BH) in `code/tests/test_analysis.py`.
- [X] T032 [P] [US3] Unit test for sensitivity sweep logic in `code/tests/test_analysis.py`.

### Implementation for User Story 3

- [X] T033 [P] [US3] [FR-005] Implement linear regression in `code/src/analysis/regression.py`.
- [X] T033b [P] [US3] [FR-005] Implement non-linear regression (polynomial, exponential) in `code/src/analysis/regression.py`.
- [X] T034a [P] [US3] Implement ANOVA testing in `code/src/analysis/anova.py`.
- [X] T034b [P] [US3] [FR-006] Implement and apply multiple-comparison correction (Bonferroni and Benjamini-Hochberg) in `code/src/analysis/anova.py`.
- [X] T035a [P] [US3] Define JSON schema for sensitivity sweep results.
- [X] T035b [US3] [FR-008] Implement sensitivity sweep for clustering coefficient thresholds in `code/src/analysis/sensitivity.py`.
- [X] T044 [US3] Implement statistical power analysis in `code/src/analysis/power.py`.

---

## Phase 6: Review & Revision (Post-Analyze Fixes)

**Purpose**: Address specific gaps identified by the `/speckit.analyze` agent regarding task granularity, edge case handling, and data flow integrity.