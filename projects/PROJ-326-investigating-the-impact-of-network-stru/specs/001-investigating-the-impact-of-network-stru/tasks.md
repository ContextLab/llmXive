# Tasks: Network Topology Energy Transfer in Spin Systems

**Version**: 3.1.0
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

- [X] T000 [P] **MANDATORY GATE**: Create `code/src/utils/reference_validator.py` as a standalone executable script (runnable via `python -m code.src.utils.reference_validator` or `./run_validator.sh`) to verify all citations in `plan.md` and `spec.md`. Output: `state/citations_verified.json`. **This task MUST pass before T002, T004c, or any other Foundational task can begin.** If validation fails, the pipeline halts with exit code 1. The Reference-Validator is an internal implementation artifact; the pipeline fails only if the result (verified citations) is missing or contains errors.

### Logging & Configuration Infrastructure

- [X] T002 [P] Initialize Python project with pinned dependencies in `code/requirements.txt` (networkx>=3.2, numpy>=1.26, scipy>=1.12, matplotlib>=3.8, seaborn>=0.13, pandas>=2.1, pytest>=7.4, coverage.py, pytest-mock). **Depends on T000 passing.** **Verification**: Run `pip install -r requirements.txt --dry-run` or verify file content against the list. **Note**: `networkx>=3.2` is pinned to ensure consistent `random_state` parameter support.
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `code/`. **Verification**: Run `ruff check.` and `black --check.` to ensure no errors.
- [X] T004c [P] Create `code/config.yaml` as the immutable source of truth for global seeds, topology targets, simulation parameters, and `simulation_timeout_seconds`. Output: `code/config.yaml` with a template structure including keys: `global_seed`, `topology_targets`, `simulation_params`, `simulation_timeout_seconds` (default), `stratification_params`, `thresholds`, `analysis`. **Depends on T000 passing.**
- [X] T004b [P] Implement seed injection logic in `code/src/utils/config.py` to load `global_seed` from `config.yaml` and propagate it to all generators, simulation, and analysis modules. **Depends on T004c (completion required) and T002 (pinned networkx version).** This task MUST explicitly set `numpy.random.seed(seed)`, `random.seed(seed)`, and pass `random_state=seed` to `networkx.watts_strogatz_graph`, `networkx.barabasi_albert_graph`, `networkx.erdos_renyi_graph` (verified against networkx>=3.2 API), and all simulation/analysis functions. Output: `code/src/utils/config.py` with function `load_config() -> dict` and `set_seed(seed: int) -> None`.
- [ ] T005 [P] Create `code/src/utils/logging.py` to initialize logging infrastructure. **Depends on T004c and T004b (completion required).** This task MUST create `data/run_log.json` as an empty JSON array `[]` if it does not exist, and implement `log_metric` helper to append entries with fields: `timestamp` (ISO 8601), `event_type` (enum: graph_generated, simulation_start, simulation_end, divergence_detected, timeout_reached), `run_id` (string), `seed` (int), `status` (string), `duration_seconds` (float). **Events to log**: `graph_generated`, `simulation_start`, `simulation_end`, `divergence_detected`, `timeout_reached`. **Verification**: Verify `data/run_log.json` exists as `[]` and `log_metric` appends a valid JSON object. **Schema Check**: Assert `set(entry.keys()) == {'timestamp', 'event_type', 'run_id', 'seed', 'status', 'duration_seconds'}`. Output: `code/src/utils/logging.py` with functions `init_logging() -> None` and `log_metric(event: dict) -> None`.
- [X] T006 [P] Create `code/src/utils/io.py` for saving/loading graphs (`gpickle`, `json`) and managing `data/` directory checksums. **Output**: `state/checksums.json`. **Verification**: Verify `state/checksums.json` exists and contains valid SHA-256 hashes for `data/` files using `hashlib`.
- [X] T007 [P] Implement base configuration loader in `code/src/utils/config.py` to validate `config.yaml` against required schema. **Verification**: Run a unit test that loads `config.yaml` and asserts schema validity.
- [X] T008 [P] Setup `code/tests/conftest.py` with fixtures for temporary data directories and seeded random states. **Verification**: Run a dummy test using the fixtures to ensure they initialize correctly.

---

## Phase 3: User Story 1 - Generate synthetic spin network datasets (Priority: P1) 🎯 MVP

**Goal**: Generate connected graphs (Erdős-Rényi, Scale-Free, Small-World) with controlled clustering coefficients and verify topology metrics.

**Independent Test**: Can be fully tested by generating a batch of networks, computing their topological metrics, and verifying the distributions match expected parameters.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️
*Execute if TESTS_ENABLED=true*

- [X] T009 [P] [US1] Unit test for Erdős-Rényi generation in `code/tests/test_generators.py` implementing `test_er_generates_connected_graph` to verify connectivity and edge probability, and `test_er_clustering_distribution` to verify clustering coefficient distribution.
- [X] T010 [P] [US1] Unit test for Watts-Strogatz (Small-World) generation in `code/tests/test_generators.py` implementing `test_sw_retries_on_disconnect` to verify -attempt retry logic and `test_sw_clustering_target` to verify clustering coefficient target achievement.
- [X] T011 [P] [US1] Unit test for Barabási-Albert (Scale-Free) generation in `code/tests/test_generators.py` implementing `test_sf_power_law_fit` to verify degree distribution R² ≥ 0.95.
- [X] T012 [P] [US1] Integration test in `code/tests/test_integration.py` implementing `test_batch_success_rate` to verify ≥95% success rate for valid connected graphs and `test_manifest_generation` to verify `global_batch_manifest.json`.

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement Erdős-Rényi generator in `code/src/generators/er.py` inheriting from `BaseGenerator` (import path: `from code.src.generators.base import BaseGenerator`). **Depends on T016.**
- [X] T014 [P] [US1] Implement Watts-Strogatz generator in `code/src/generators/sw.py` inheriting from `BaseGenerator` (import path: `from code.src.generators.base import BaseGenerator`). **Depends on T016.**
- [X] T015 [P] [US1] Implement Barabási-Albert generator in `code/src/generators/sf.py` inheriting from `BaseGenerator` (import path: `from code.src.generators.base import BaseGenerator`). **Depends on T016.**
- [X] T016 [P] [US1] Implement base generator logic in `code/src/generators/base.py` with shared logic for connectivity checks, a configurable retry limit (read from `config.yaml`, default configurable), and warning logging. **Note**: Includes strict connectivity retry enforcement with configurable max_retries.
- [X] T017 [P] [US1] [FR-004] Implement metric extraction logic (degree distribution, clustering, average path length) as required by FR-004 in `code/src/generators/metrics.py`. **Depends on T016.** This task MUST write metrics to the `global_batch_manifest.json` defined in T018e.
- [X] T018a [P] [US1] Create `code/src/generators/batch_runner.py` file structure. **Depends on T004c and T016.**
- [ ] T018b [P] [US1] Implement `main()` orchestration logic in `code/src/generators/batch_runner.py`. **Depends on T018a.** This task MUST load `config.yaml` and initialize the generation pipeline.
- [ ] T018c [P] [US1] [FR-004][FR-001] Define JSON schema for `global_batch_manifest.json` including `stratification_summary` and `generation_algorithm` fields. **Depends on T018b, T017.** **Output**: `contracts/manifest.schema.yaml`. **Verification**: Run `code/tests/contract/test_schemas.py::test_manifest_stratification` to verify. <!-- FAILED: unspecified -->
- [X] T018d [P] [US1] Implement iteration logic over topology classes and aggregate_batches in `code/src/generators/batch_runner.py` to aggregate results. **Depends on T018c.**
- [ ] T018e [P] [US1] Implement manifest writing logic to `data/raw/global_batch_manifest.json` with schema validation. **Depends on T018d.**
- [ ] T018f [P] [US1] [FR-001][SC-001] Implement **Global Success Rate Monitoring** in `code/src/generators/batch_runner.py`. **Depends on T018e.** This task MUST: (1) Track `failed_attempts` per graph and `success_rate` globally; (2) Enforce the "≥95% valid connected graphs within 10 attempts" edge case logic; (3) Explicitly fail the batch (or flag a critical error) if the aggregate success rate drops below `config.yaml:thresholds.success_rate_min` after exhausting retries for all graphs; (4) Log the final success rate to `data/run_log.json`. **Verification**: Run a test that simulates low success rates and asserts the batch fails or flags critical error.
- [X] T019 [P] [US1] Implement metadata logging module in `code/src/generators/metadata.py` to record algorithm, edge_probability, preferential_attachment_params, and seed for every generated graph, saving to `data/metadata/graph_<id>.json`.
- [X] T020 [P] [FR-001] Implement stratified sampling loop controller in `code/src/generators/stratified_runner.py` that explicitly enforces target distribution by generating graphs until bin quotas are met. **Depends on T090, T062a, T062b, T018e.** This task MUST orchestrate the trigger (T090) to enforce quotas.
- [X] T062a [P] [FR-001][SC-005] Define stratification configuration in `code/config.yaml` under `stratification_params`: keys `bins` (list of floats: 0.1, 0.2, 0.3, 0.4, 0.5), `target_counts` (dict mapping bin to count), and `tolerance` (float). **Depends on FR-001/SC-005 stratification configuration.**
- [X] T062b [P] [FR-001][SC-005] Implement binning logic in `code/src/generators/binning.py` to classify generated graphs into clustering coefficient bins. **Depends on T062a.**
- [X] T062e [P] [FR-001][SC-005] Implement quota checker in `code/src/generators/quota_checker.py`. **Depends on T062a.**
- [X] T090 [US1] [FR-001][SC-005] Implement **Stratified Generation Trigger** in `code/src/generators/generation_trigger.py`. **Depends on T013, T014, T015, T016, T062a, T062b, T062e.** This task MUST explicitly check quota status and trigger generation for specific bins. It MUST ensure that the stratified runner (T020) does not proceed until the quota checker signals a deficit in a specific bin. **Verification**: Run a test that simulates a deficit in a specific bin and asserts the trigger activates generation for that bin.

---
## Phase 4: User Story 2 - Run energy propagation simulation (Priority: P2)

**Goal**: Execute simplified Ising spin-flip dynamics on generated networks, measure diffusion rates, and ensure numerical stability on CPU.

**Independent Test**: Can be fully tested by running the simulator on a single network, verifying the energy density profile evolves, and confirming spatial variance increases.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️
*Execute if TESTS_ENABLED=true*

- [X] T021 [P] [US2] Unit test for spin-flip logic in `code/tests/test_simulation.py` implementing `test_energy_conservation_within_tolerance` and `test_spin_flip_boltzmann_match`.
- [X] T022 [P] [US2] Unit test for spatial variance calculation in `code/tests/test_simulation.py` implementing `test_spatial_variance_calculation`.
- [X] T023 [P] [US2] Unit test for divergence detection and abort logic in `code/tests/test_simulation.py` implementing `test_divergence_raises_error`.

### Implementation for User Story 2

- [X] T024 [P] [US2] Implement simplified Ising spin-flip dynamics in `code/src/simulation/dynamics.py` (CPU-only, no GPU dependencies). **Note**: Must explicitly log and store 'null results' (no correlation) as reproducible artifacts to satisfy Constitution Principle I.
- [X] T025 [P] [US2] Implement energy density profile tracking and spatial variance calculation in `code/src/simulation/metrics.py`.
- [X] T026 [P] [US2] Implement numerical stability checks (divergence detection) in `code/src/simulation/stability.py`. **Depends on T024, T025.** **Critical Constraint**: This task MUST implement the spec's mandatory edge case: if energy values exceed significantly elevated levels, the system MUST **abort the run** for that network, log `divergence_detected` via `logging.py`, and flag the result as `[SIMULATION_DIVERGENCE]`. **NO** retry or recovery logic is permitted. **Verification**: Run a test that forces energy divergence and asserts the run is aborted, logged, and flagged.
- [X] T027 [US2] Implement diffusion rate calculator in `code/src/simulation/diffusion.py`.
- [X] T028a [US2] Create simulation runner script in `code/src/simulation/run_simulation.py`.
- [ ] T080 [US2] [FR-002][Edge Case] Implement **Simulation Timeout Enforcement** in `code/src/simulation/run_simulation.py`. **Depends on T028a and T004c.** This task MUST wrap the simulation loop in a `signal.alarm` (Unix) or `threading.Timer` (cross-platform) context using `config.yaml`'s `simulation_timeout_seconds`. **Critical Constraint**: The code MUST enforce a hard cap on execution time regardless of configuration. (e.g., `The effective timeout is determined by the minimum of the configured timeout and a predefined maximum threshold.`). If the timeout triggers, the task MUST abort the run, log `timeout_reached` via `logging.py`, and flag the result as `[TIMEOUT_EXCEEDED]` without raising a fatal exception that stops the batch. **Verification**: Run a test that forces a `time.sleep` longer than the timeout and asserts the run is flagged and logged correctly.
- [X] T070 [US2] [FR-002][SC-002][FR-010] Implement **CPU-time profiling and FR-010 Validation** in `code/src/simulation/profiler.py`. **Depends on T080.** This task MUST measure per-step execution time and explicitly validate FR-010 (100 steps < 60 mins) in the full pipeline context, using the timeout enforcement logic from T080.
- [ ] T029 [US2] Implement result serialization to `data/analysis/simulation_results.json`.
- [ ] T083 [P] [General] **Data Flow Integrity Check**: Create `code/tests/integration/test_data_flow.py` to verify that `simulation_results.json` is generated *before* `aggregated_results.json` is attempted, and that `aggregated_results.json` fails gracefully if the simulation file is missing or empty. **Depends on T029 and T081.** **Test Setup**: Use `pytest-mock` (or `unittest.mock`) to mock the file system to delete `simulation_results.json` before running the aggregator to trigger the graceful failure condition.

---
## Phase 5: User Story 3 - Correlate metrics and test significance (Priority: P3)

**Goal**: Perform regression/ANOVA analysis, apply multiple-comparison correction, run sensitivity sweeps, and generate figures.

**Independent Test**: Can be fully tested by running the analysis pipeline on a pre-generated dataset, verifying statistical tests produce p-values, and confirming figures are generated.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️
*Execute if TESTS_ENABLED=true*

- [X] T030 [P] [US3] Unit test for regression analysis in `code/tests/test_analysis.py`.
- [X] T031 [P] [US3] Unit test for ANOVA and multiple-comparison correction (Bonferroni/BH) in `code/tests/test_analysis.py`.
- [X] T032 [P] [US3] Unit test for sensitivity sweep logic in `code/tests/test_analysis.py`.

### Implementation for User Story 3

- [X] T033 [P] [US3] [FR-005] Implement linear regression in `code/src/analysis/regression.py`.
- [X] T033b [P] [US3] [FR-005] Implement non-linear regression (polynomial, exponential) in `code/src/analysis/regression.py`.
- [X] T034a [P] [US3] Implement ANOVA testing in `code/src/analysis/anova.py`.
- [ ] T034b [P] [US3] [FR-006] Implement and apply multiple-comparison correction (Bonferroni and Benjamini-Hochberg) in `code/src/analysis/anova.py`. **Depends on T033, T034a.** This task MUST: (1) Apply correction; (2) Explicitly output `correction_method` (e.g., "Benjamini-Hochberg") and `rationale` (e.g., "Default for FDR control") to **both** `data/analysis/statistical_report.json` AND `data/analysis/aggregated_results.json` to ensure auditability without inspecting source code.
- [X] T035a [P] [US3] Define JSON schema fields for sensitivity sweep results. **Output**: `contracts/sensitivity_sweep.schema.yaml` (YAML format).
- [X] T035b [US3] [FR-008] Create `contracts/sensitivity_sweep.schema.yaml` file with the defined fields.
- [X] T036a [P] [US3] Define threshold range and step size for sensitivity sweep: **Mandatory Range** from `config.yaml:analysis.sweep.min` (default a threshold value) to `config.yaml:analysis.sweep.max` (default a moderate baseline value) in uniform steps of `config.yaml:analysis.sweep.step` (default).
- [X] T036b [US3] Implement sensitivity sweep logic in `code/src/analysis/sensitivity.py`.
- [ ] T036c [US3] Write output to `data/analysis/sensitivity_sweep.json`.
- [ ] T036d [US3] [FR-008][SC-005] Implement **Sensitivity Sweep Validation** in `code/tests/contract/test_sensitivity.py`. **Depends on T036c.** This task MUST verify that `data/analysis/sensitivity_sweep.json` contains the required "≥5 distinct thresholds" mandated by SC-005. **Verification**: Run a test that asserts the count of unique thresholds in the output file is ≥ 5.
- [X] T044 [US3] Implement statistical power analysis in `code/src/analysis/power.py`. **Verification**: Include a verification step to ensure the resulting `power_analysis_report.json` meets the target power (≥0.8) or explicitly documents the batch size adjustment if the 6-hour limit is reached.
- [ ] T081 [US3] [FR-006][ROC-001] Implement **Associational Framing & Result Aggregation** in `code/src/analysis/aggregator.py`. **Depends on T033, T034a, T035b, T034b.** This task MUST: (1) Aggregate results from regression and ANOVA into `data/analysis/aggregated_results.json` with the following schema structure: `{ "results": [...], "methodology_note": "Findings are associational; no random assignment of network topology was performed", "correction_method": "...", "correction_rationale": "..." }`; (2) Ensure all p-values in the output are paired with their corrected significance status. **Verification**: Run `code/tests/contract/test_schemas.py::test_aggregated_results_framing` to verify the presence of the note and the structure of corrected p-values.
- [ ] T092 [US3] [FR-008] Implement **Visualization Pipeline** in `code/src/analysis/visualizer.py`. **Depends on T081, T036c.** This task MUST generate the required + PNG figures (scatter plots, heat maps) with ≥300 DPI resolution. It MUST read from `aggregated_results.json` and `sensitivity_sweep.json` to ensure figures reflect the final corrected data.
- [ ] T082 [US3] [FR-007] Implement **Final Report Generation** in `code/src/analysis/report.py`. **Depends on T081 and T044.** This task MUST generate `data/analysis/final_results.json` (excluding timestamps as per T037d) and `paper/results.md`. The `paper/results.md` MUST include a "Limitations" section explicitly discussing the observational nature of the design (ROC-001) and the constraints of CPU-only simulation. **Crucial**: This task MUST read the `methodology_note` and `correction_method` from `aggregated_results.json` (produced by T081) to ensure consistency. **Verification**: Verify `paper/results.md` contains the text "associational" and "observational". **Reproducibility Check**: Verify that `config.yaml` and `data/raw/metadata.json` contain the full parameter set required for exact reproduction as mandated by FR-007 and Constitution Principle I.

---
## Phase 6: Review & Revision (Post-Analyze Fixes)

**Purpose**: Address specific gaps identified by the `/speckit.analyze` agent regarding task granularity, edge case handling, and data flow integrity.

- [ ] T093 [General] **End-to-End Orchestration**: Implement `code/src/main.py` to orchestrate the full pipeline (T000 -> T020 -> T080 -> T081 -> T082). **Depends on T000, T020, T080, T081, T082.** This task MUST enforce the execution order: Generate -> Simulate -> Analyze -> Report, and halt immediately if T000 fails.

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
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
