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
- [X] T004 [P] Create `code/config.yaml` for global seeds, topology targets, and simulation parameters (initial template only)
- [X] T004c [P] **NEW**: Implement logic to create and populate `code/config.yaml` with pinned global random seeds and topology targets as the immutable source of truth (FR-007). This task ensures the file exists and contains the required seed data before any generation or simulation runs.
- [ ] T004b [P] Implement logic to inject specific random seeds used during a run into `data/run_log.json` (do NOT update config.yaml) to ensure reproducibility (FR-007), including a verification step that explicitly checks the presence and correctness of these seeds against the config, outputting verification results to `data/run_log.json`.
- [ ] T005 [P] Implement logging infrastructure in `code/src/utils/logging.py` to capture seeds, parameters, and runtime metrics, writing to `data/run_log.json`
- [X] T006 [P] Create `code/src/utils/io.py` for saving/loading graphs (`gpickle`, `json`) and managing `data/` directory checksums
- [X] T007 [P] Implement base configuration loader in `code/src/utils/config.py` to validate `config.yaml` against required schema
- [X] T008 [P] Setup `code/tests/conftest.py` with fixtures for temporary data directories and seeded random states
- [X] T016a [P] Implement global timeout utility function in `code/src/generators/timeout.py` with explicit logging. If the timeout is hit during batch generation, the process MUST fail with an error (exit code 1) and log the failure, not proceed silently. The function must read the timeout value from `config.yaml` (key: `simulation_timeout_seconds`) and use it as the default timeout threshold.
- [ ] T018a [P] **MOVED FROM PHASE 3**: Implement batch aggregation script in `code/src/generators/aggregate_batch.py` to combine per-topology-class batches into a single global batch, generate `data/raw/global_batch_manifest.json`, and verify the combined total meets the configured target count (from `config.yaml`) for FR-001/SC-001. This task MUST implement a 10-attempt retry loop for disconnected networks per the spec's Edge Cases. If the target count (≥95% valid graphs) is not met after retries, the script MUST exit with code 1.

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
- [X] T012 [P] [US1] Integration test in `code/tests/test_integration.py` implementing `test_batch_success_rate` to verify ≥95% success rate for valid connected graphs and `test_manifest_generation` to verify `global_batch_manifest.json` content.

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement Erdős-Rényi generator in `code/src/generators/er.py` inheriting from base
- [X] T014 [P] [US1] Implement Watts-Strogatz generator in `code/src/generators/sw.py` inheriting from base, utilizing the shared clustering retry logic, global timeout (T016a), and Threshold-based warning logging
- [X] T015 [P] [US1] Implement Barabási-Albert generator in `code/src/generators/sf.py` inheriting from base
- [X] T016 [P] [US1] Implement base generator logic in `code/src/generators/base.py` with shared logic for connectivity checks, a configurable retry limit (read from `config.yaml`), and warning logging for failed attempts, utilizing T016a for timeout mechanism.
- [X] T017 [P] [US1] Implement metric extraction function in `code/src/generators/metrics.py` (degree distribution, clustering, average path length)
- [X] T019 [P] [US1] Implement metadata logging module in `code/src/generators/metadata.py` to record algorithm, edge_probability, preferential_attachment_params, and seed for every generated graph, saving to `data/metadata/graph_<id>.json`
- [X] T018 [US1] Create batch generation script in `code/src/generators/batch_runner.py` to produce per-topology-class batches, utilizing T019 for logging and T016a for timeout, outputting per-class batches to `data/raw/`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Run energy propagation simulation (Priority: P2)

**Goal**: Execute simplified Ising spin-flip dynamics on generated networks, measure diffusion rates, and ensure numerical stability on CPU.

**Independent Test**: Can be fully tested by running the simulator on a single network, verifying the energy density profile evolves, and confirming spatial variance increases.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Unit test for spin-flip logic in `code/tests/test_simulation.py` implementing `test_energy_conservation_within_tolerance` (assert energy conservation within 1e-6) and `test_spin_flip_boltzmann_match` (assert spin flip probability matches Boltzmann factor).
- [X] T022 [P] [US2] Unit test for spatial variance calculation in `code/tests/test_simulation.py` implementing `test_spatial_variance_calculation` to verify mathematical definition.
- [X] T023 [P] [US2] Unit test for divergence detection and abort logic in `code/tests/test_simulation.py` implementing `test_divergence_abort` to verify simulation aborts on energy divergence.

### Implementation for User Story 2

- [ ] T029a [P] [US2] Define and validate JSON schema for `data/analysis/simulation_results.json` against the `SimulationRun` entity to ensure all required fields (network_id: str, seed: int, diffusion_rate: float, topology_class: str, steps_run: int, status: str) are present.
- [ ] T029 [US2] Implement result serialization to `data/analysis/simulation_results.json` with fields: network_id, seed, diffusion_rate, topology_class, steps_run, status, ensuring schema compliance (T029a).
- [X] T024 [P] [US2] Implement simplified Ising spin-flip dynamics in `code/src/simulation/dynamics.py` (CPU-only, no GPU dependencies, default precision)
- [X] T025 [P] [US2] Implement energy density profile tracking and spatial variance calculation in `code/src/simulation/metrics.py`
- [X] T026 [P] [US2] Implement numerical stability checks (divergence detection) in `code/src/simulation/stability.py`
- [X] T027 [US2] Implement diffusion rate calculator in `code/src/simulation/diffusion.py` to calculate rate of change of spatial variance (finite difference), verifying mathematical definition matches spec and asserting variance monotonicity with tolerance for stochastic noise (not strict assertion), outputting verification results to `data/analysis/diffusion_verification.json`.
- [X] T028 [US2] Create simulation runner script in `code/src/simulation/run_simulation.py` that loads graphs from `data/raw/` and executes multiple time steps, utilizing T024-T027 for core logic and T029 for result serialization. This task depends on T029a and T029 being implemented first.

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
- [X] T034 [P] [US3] Implement ANOVA testing and multiple-comparison correction (both Bonferroni and Benjamini-Hochberg options) in `code/src/analysis/anova.py`, ensuring correction applies to ANOVA F-tests AND regression p-values (all family-wise error tests), verifying correction is applied to p-values (not coefficients), and generating a unit test `code/tests/test_analysis.py` with specific assertions for these corrections.
- [ ] T035 [P] [US3] Implement sensitivity sweep for clustering coefficient thresholds in `code/src/analysis/sensitivity.py`, saving results to `data/analysis/sensitivity_sweep.json` with configurable cutoffs (defaulting to distinct values, but configurable in `config.yaml`), verifying file content per SC-005, and generating a unit test `code/tests/test_analysis.py` with assertions for threshold validation.
- [X] T036 [P] [US3] Implement visualization pipeline in `code/src/analysis/plotting.py` to generate ≥3 figures (scatter, heatmaps) at 300 DPI
- [ ] T037 [US3] Create master analysis script in `code/src/analysis/run_analysis.py` to aggregate simulation results from T029 (handling missing data via mean/median/variance aggregation), run tests (T033, T034, T035), call the plotting module (T036), and save `data/analysis/final_results.json` (schema: {regression_results, anova_results, sensitivity_results, figures_generated}). This task depends on T035 being complete.
- [ ] T044 [US3] Implement statistical power analysis in `code/src/analysis/power.py` to consume output from T037 (which aggregates T033/T034 results), calculate the achieved power against the configured target (if any) using `statsmodels.stats.power`, and generate a design validation report (`data/analysis/power_analysis_report.json`) indicating whether the design target is met. This task depends on T037.
- [X] T038 [US3] Implement report generator in `code/src/analysis/report.py` to frame findings as associational (ROC-001) by explicitly implementing logic to avoid causal language (e.g., filtering terms like "cause", "effect", "determine" from coefficient descriptions) and outputting text for verification.
- [X] T038a [P] [US3] Implement report verification script in `code/src/analysis/verify_report.py` to programmatically verify that the generated report text from T038 explicitly contains the phrase "associational" or similar disclaimers and structurally adheres to ROC-001 by checking for absence of causal language, outputting verification results to `data/analysis/report_verification.json`.
- [~] T045 [P] Run full batch validation script `code/scripts/validate_batch.py` to verify SC-001 (configured target count from `config.yaml`), SC-002 (runtime < 60m/network), and SC-005 (check `data/analysis/sensitivity_sweep.json` for configurable cutoffs) with explicit exit code 0 criteria, outputting validation results to `data/analysis/validation_report.json`.
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
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Dependency Note**: T016a (Timeout utility) is a prerequisite for T014 (Watts-Strogatz) and T018 (Batch runner) and is located in Phase 2 to ensure it is completed first.
- **Dependency Note**: T029a (Schema validation) is a prerequisite for T029 (Serialization) to ensure data integrity.
- **Dependency Note**: T018a (Batch aggregation) must complete before T028 (Simulation runner) can execute.
- **Dependency Note**: T035 (Sensitivity sweep) must complete before T037 (Master analysis) and T045 (Validation) can execute.
- **Dependency Note**: T044 (Power analysis) must complete after T037 to validate SC-003.
- **Dependency Note**: T047 (Config verification) must complete to ensure reproducibility before final reporting.
- **Dependency Note**: T046 (Coverage) must complete to ensure test coverage before final reporting.
- **Execution Order**: T045 (Validation) is the final task in Phase 5 and must run after T035, T044, and T037 are complete.

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [X] T049 Reconcile run-book vs implementation for `code/main.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/main.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
