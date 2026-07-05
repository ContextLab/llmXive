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

- [X] T002 [P] Initialize Python project with pinned dependencies in `code/requirements.txt` (networkx, numpy, scipy, matplotlib, seaborn, pandas, pytest)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `code/`
- [X] T004 [P] Create `code/config.yaml` for global seeds, topology targets, and simulation parameters
- [X] T004b [P] Implement logic to inject specific random seeds used during a run into `data/run_log.json` (do NOT update config.yaml) to ensure reproducibility (FR-007)
- [ ] T005 [P] Implement logging infrastructure in `code/src/utils/logging.py` to capture seeds, parameters, and runtime metrics, writing to `data/run_log.json`
- [ ] T006 [P] Create `code/src/utils/io.py` for saving/loading graphs (`gpickle`, `json`) and managing `data/` directory checksums
- [ ] T007 [P] Implement base configuration loader in `code/src/utils/config.py` to validate `config.yaml` against required schema
- [X] T008 [P] Setup `code/tests/conftest.py` with fixtures for temporary data directories and seeded random states

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate synthetic spin network datasets (Priority: P1) 🎯 MVP

**Goal**: Generate connected graphs (Erdős-Rényi, Scale-Free, Small-World) with controlled clustering coefficients and verify topology metrics.

**Independent Test**: Can be fully tested by generating a batch of networks, computing their topological metrics, and verifying the distributions match expected parameters.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Unit test for Erdős-Rényi generation in `code/tests/test_generators.py`
- [~] T010 [P] [US1] Unit test for Watts-Strogatz (Small-World) generation with retry logic in `code/tests/test_generators.py` <!-- ATOMIZE: requested -->
- [~] T011 [P] [US1] Unit test for Barabási-Albert (Scale-Free) generation in `code/tests/test_generators.py`
- [~] T012 [P] [US1] Integration test verifying connectivity and clustering target success rates in `code/tests/test_integration.py`

### Implementation for User Story 1

- [~] T016a [P] Implement global timeout utility function in `code/src/generators/timeout.py` with explicit logging and fallback behavior (log warning, proceed) if timeout is hit or a maximum number of retries is exhausted, defining function signature and verifying timeout triggers after X seconds
- [~] T016 [US1] Implement base generator logic in `code/src/generators/base.py` with shared logic for connectivity checks, A retry limit

The specific value to remove/generalize: 'a configurable number'

Rewritten passage:
A retry limit will be established to manage transient failures, with the specific threshold determined during the implementation phase., and warning logging for failed attempts, utilizing T016a for timeout mechanism
- [~] T013 [P] [US1] Implement Erdős-Rényi generator in `code/src/generators/er.py` inheriting from base
- [~] T014 [P] [US1] Implement Watts-Strogatz generator in `code/src/generators/sw.py` inheriting from base, utilizing the shared clustering retry logic, global timeout (T016a), and 10-attempt warning logging
- [~] T015 [P] [US1] Implement Barabási-Albert generator in `code/src/generators/sf.py` inheriting from base
- [~] T017 [P] [US1] Implement metric extraction function in `code/src/generators/metrics.py` (degree distribution, clustering, average path length)
- [~] T019 [P] [US1] Implement metadata logging module in `code/src/generators/metadata.py` to record algorithm, edge_probability, preferential_attachment_params, and seed for every generated graph, saving to `data/metadata/graph_<id>.json`
- [~] T018 [US1] Create batch generation script in `code/src/generators/batch_runner.py` to produce per-topology-class batches, utilizing T019 for logging and T016a for timeout, outputting per-class batches to `data/raw/`
- [~] T018a [US1] Implement batch aggregation script in `code/src/generators/aggregate_batch.py` to combine per-topology-class batches into a single global batch, generate `data/raw/global_batch_manifest.json`, and verify the combined total meets the ≥100 threshold (FR-001/SC-001)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Run energy propagation simulation (Priority: P2)

**Goal**: Execute simplified Ising spin-flip dynamics on generated networks, measure diffusion rates, and ensure numerical stability on CPU.

**Independent Test**: Can be fully tested by running the simulator on a single network, verifying the energy density profile evolves, and confirming spatial variance increases.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T021 [P] [US2] Unit test for spin-flip logic in `code/tests/test_simulation.py` <!-- FAILED: unspecified -->
- [~] T022 [P] [US2] Unit test for spatial variance calculation in `code/tests/test_simulation.py`
- [~] T023 [P] [US2] Unit test for divergence detection and abort logic in `code/tests/test_simulation.py`

### Implementation for User Story 2

- [~] T024 [P] [US2] Implement simplified Ising spin-flip dynamics in `code/src/simulation/dynamics.py` (CPU-only, no GPU dependencies, default precision)
- [~] T025 [P] [US2] Implement energy density profile tracking and spatial variance calculation in `code/src/simulation/metrics.py`
- [~] T026 [P] [US2] Implement numerical stability checks (divergence detection) in `code/src/simulation/stability.py`
- [~] T027 [US2] Implement diffusion rate calculator in `code/src/simulation/diffusion.py` to calculate rate of change of spatial variance (finite difference), verifying mathematical definition matches spec and asserting variance monotonicity
- [~] T029a [P] [US2] Define and validate JSON schema for `data/analysis/simulation_results.json` against the `SimulationRun` entity to ensure all required fields (network ID, seed, diffusion rate, topology class) are present
- [~] T029 [US2] Implement result serialization to `data/analysis/simulation_results.json` with seed, network ID, diffusion rate, and topology class, saving to `data/analysis/simulation_results.json`, ensuring schema compliance (T029a)
- [~] T028 [US2] Create simulation runner script in `code/src/simulation/run_simulation.py` that loads graphs from `data/raw/` and executes multiple time steps, utilizing T024-T027 for core logic and T029 for result serialization, after core logic (T024-T027), serialization (T029), and schema validation (T029a) are implemented

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Correlate metrics and test significance (Priority: P3)

**Goal**: Perform regression/ANOVA analysis, apply multiple-comparison correction, run sensitivity sweeps, and generate figures.

**Independent Test**: Can be fully tested by running the analysis pipeline on a pre-generated dataset, verifying statistical tests produce p-values, and confirming figures are generated.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T030 [P] [US3] Unit test for regression analysis in `code/tests/test_analysis.py`
- [~] T031 [P] [US3] Unit test for ANOVA and multiple-comparison correction (Bonferroni/BH) in `code/tests/test_analysis.py`
- [~] T032 [P] [US3] Unit test for sensitivity sweep logic in `code/tests/test_analysis.py`

### Implementation for User Story 3

- [~] T033 [P] [US3] Implement linear and non-linear regression in `code/src/analysis/regression.py`
- [~] T034 [P] [US3] Implement ANOVA testing and multiple-comparison correction (both Bonferroni and Benjamini-Hochberg options) in `code/src/analysis/anova.py`, ensuring correction applies to ANOVA F-tests AND regression p-values (all family-wise error tests), and verifying correction is applied to regression coefficients
- [~] T035 [P] [US3] Implement sensitivity sweep for clustering coefficient thresholds in `code/src/analysis/sensitivity.py`, saving results to `data/analysis/sensitivity_sweep.json` with ≥5 distinct cutoffs and verifying file content per SC-005
- [~] T036 [P] [US3] Implement visualization pipeline in `code/src/analysis/plotting.py` to generate ≥3 figures (scatter, heatmaps) at 300 DPI
- [~] T037 [US3] Create master analysis script in `code/src/analysis/run_analysis.py` to aggregate simulation results from T029, run tests (T033, T034, T035), call the plotting module (T036), and save `data/analysis/final_results.json`
- [~] T038 [US3] Implement report generator in `code/src/analysis/report.py` to frame findings as associational (ROC-001) and document p-values/effect sizes, outputting text for verification
- [~] T038a [P] [US3] Implement report verification script in `code/src/analysis/verify_report.py` to programmatically verify that the generated report text from T038 explicitly contains the phrase "associational" or similar disclaimers
- [~] T044 [US3] Implement statistical power analysis in `code/src/analysis/power.py` to consume output from T033/T034 (effect sizes, variances), calculate the actual achieved power based on generated sample size (≥100) and observed variance, measure against target r ≥ 0.3, and generate a design validation report (`data/analysis/power_analysis_report.json`) confirming SC-003

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T041 [P] Update `code/README.md` **Installation** section with environment setup instructions
- [~] T042 [P] Update `code/README.md` **Usage** section with execution commands
- [~] T043 [P] Update `code/README.md` **Configuration** section with `config.yaml` explanation
- [~] T045 [P] Run full batch validation script `code/scripts/validate_batch.py` to verify SC-001 (100+ graphs), SC-002 (runtime < 60m/network), and SC-005 (**check `data/analysis/sensitivity_sweep.json` for ≥5 cutoffs**) with explicit exit code 0 criteria
- [~] T046 [P] Add `pytest` coverage report generation
- [~] T047 [P] Verify `config.yaml` documentation and reproducibility of random seeds
- [~] T048 [P] Run quickstart.md validation

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