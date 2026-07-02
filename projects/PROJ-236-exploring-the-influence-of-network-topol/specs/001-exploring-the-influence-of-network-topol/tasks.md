# Tasks: Exploring the Influence of Network Topology on Heat Transport in Disordered Materials

**Input**: Design documents from `/specs/001-exploring-the-influence-of-network-topol/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/
**Branch**: `001-exploring-the-influence-of-network-topol` (Note: spec.md and plan.md must be updated to match this branch name)

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
  
  Tasks MUST be organized by user story so each story can be:
  - Implemented independently
  - Tested independently
  - Delivered as an MVP increment
  
  DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan in `projects/PROJ-236-exploring-the-influence-of-network-topol/` by executing: `mkdir -p code/utils code/tests/unit code/tests/integration data/raw data/networks data/transport data/analysis plots state/projects`
- [ ] T002 Initialize Python 3.11 project with dependencies in `code/requirements.txt` including: `numpy`, `networkx`, `scipy`, `scikit-learn`, `pandas`, `matplotlib`, `seaborn`, `ase`, `pyyaml`, `pydantic`, `pytest`, `pytest-cov`, `ruff`, `black`, `mypy`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup configuration loader for `code/simulation_config.yaml` in `code/utils/io.py`
- [ ] T005 [P] Implement checksumming utility for `data/` artifacts in `code/utils/io.py`
- [ ] T006 [P] Create base logging infrastructure in `code/utils/logging.py`
- [ ] T007 Create Pydantic base entities `NetworkRealization` (fields: node_count, edge_list, topology_type, cutoff_factor, seed, validation_status) and `TransportResult` (fields: network_id, kappa, error_estimate, convergence_status, runtime) in `code/utils/models.py`
- [ ] T008 Setup random seed management (np.random.seed(42)) in `code/utils/seeds.py`
- [ ] T015 [US1] Implement distance-based cutoff logic (1.5x NN default, retry up to 2.0x) and connectivity check in `code/generate_networks.py` (Must precede graph generators)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Construct and Validate Network Realizations (Priority: P1) 🎯 MVP

**Goal**: Generate reproducible ensembles of Small-World, Scale-Free, and Random atomic connectivity networks with distance-based cutoffs and topological sanity checks.

**Independent Test**: Can be fully tested by running the network generation script on a fixed seed and verifying that the output network realizations match the theoretical degree distributions and that the distance-based cutoff yields a connected graph for >95% of realizations.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Unit test for network topology metrics (clustering, path length) in `tests/unit/test_network_gen.py`
- [ ] T010 [P] [US1] Unit test for connectivity retry logic in `tests/unit/test_network_gen.py`
- [ ] T011 [P] [US1] Integration test for ensemble generation with physical validity filter in `tests/integration/test_network_ensemble.py`

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement Small-World (Watts-Strogatz) graph generator in `code/generate_networks.py` (Depends on T015)
- [ ] T013 [P] [US1] Implement Scale-Free (Barabási-Albert) graph generator in `code/generate_networks.py` (Depends on T015)
- [ ] T014 [P] [US1] Implement Random (Erdős-Rényi) graph generator in `code/generate_networks.py` (Depends on T015)
- [ ] T016 [US1] Implement topological metric extraction (clustering, degree variance, spectral gap, betweenness) in `code/generate_networks.py`
- [ ] T017 [US1] [FR-010] Implement physical validity filter (physical energy minimization check for atomic stability) in `code/utils/validation.py` (Must precede T018/T019)
- [ ] T018 [US1] Implement ensemble generation loop with `meta.json` logging for each realization in `code/generate_networks.py` (Depends on T015, T017)
- [ ] T019a [US1] Implement ensemble generation per cutoff (1.2x, 1.5x, 1.8x, 2.0x) in `code/generate_networks.py`
- [ ] T019b [US1] Implement transport simulation runner per cutoff in `code/compute_transport.py`
- [ ] T019c [US1] Implement result aggregation for sensitivity analysis in `code/analyze_correlations.py`
- [ ] T020 [US1] Save generated graphs to `data/networks/` and checksums to `state/projects/PROJ-236-exploring-the-influence-of-network-topol.yaml`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compute Phonon Transport and Thermal Conductivity (Priority: P2)

**Goal**: Calculate effective thermal conductivity (κ) for each network realization using anharmonic lattice dynamics (Mode-Coupling Approximation with Lennard-Jones potential) on CPU-only hardware.

**Independent Test**: Can be fully tested by running the simulation on a small, known test case (e.g., a 1D chain) and verifying the output κ matches the analytical or literature value within 10%, while confirming the process completes on a CPU-only runner.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Unit test for force constant derivation from perturbation theory in `tests/unit/test_transport.py`
- [ ] T022 [P] [US2] Unit test for convergence check logic in `tests/unit/test_transport.py`
- [ ] T023 [P] [US2] Integration test for MCA solver timeout enforcement in `tests/integration/test_transport_solver.py`

### Implementation for User Story 2

- [ ] T024 [US2] [FR-006] Implement force constant derivation via anharmonic force constant estimation (perturbation theory) in `code/compute_transport.py` (Depends on T017 output; Must precede T025)
- [ ] T025 [US2] Implement Mode-Coupling Approximation (MCA) solver for thermal conductivity (reads `data/networks/*.graphml`, writes `data/transport/results.csv`, LJ epsilon=1.0, sigma=3.4) with mandatory convergence validation loop (flag and rerun on failure) in `code/compute_transport.py`
- [ ] T026 [US2] Implement convergence check and retry logic (max 3 retries) in `code/utils/validation.py`
- [ ] T027 [US2] Implement timeout enforcement (45 min limit) per realization in `code/compute_transport.py`
- [ ] T028 [US2] Implement result aggregation and error handling for singular matrices in `code/compute_transport.py`
- [ ] T029 [US2] Save transport results to `data/transport/transport_results.csv` with metadata in `code/compute_transport.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Analyze Topology-Transport Correlations (Priority: P3)

**Goal**: Perform statistical regression analyses between network metrics and thermal conductivity, including bootstrap resampling, FDR correction, and multicollinearity checks.

**Independent Test**: Can be fully tested by running the analysis on a synthetic dataset with a known correlation (e.g., r=0.8) and verifying that the bootstrapped confidence interval captures the true value and the p-value is < 0.05.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US3] Unit test for bootstrap resampling implementation in `tests/unit/test_analysis.py`
- [ ] T031 [P] [US3] Unit test for FDR/Bonferroni correction logic in `tests/unit/test_analysis.py`
- [ ] T032 [P] [US3] Unit test for VIF multicollinearity check in `tests/unit/test_analysis.py`
- [ ] T033 [P] [US3] Integration test for full correlation pipeline with known synthetic data in `tests/integration/test_correlation_pipeline.py`

### Implementation for User Story 3

- [ ] T034 [P] [US3] Implement linear regression and correlation coefficient calculation in `code/analyze_correlations.py`
- [ ] T035 [US3] Implement bootstrap resampling (1000 iterations) for confidence intervals in `code/analyze_correlations.py`
- [ ] T036 [US3] Implement multiple-comparison correction (Bonferroni/FDR) for p-values in `code/analyze_correlations.py`
- [ ] T037 [US3] [FR-009] Implement Variance Inflation Factor (VIF) check and predictor handling in `code/analyze_correlations.py`
- [ ] T038 [US3] [SC-005] Implement power-law fit (R² calculation) between disorder parameters and conductivity in `code/analyze_correlations.py`
- [ ] T039 [US3] Implement associational framing logic to explicitly scrub causal language from final output artifacts (plots, CSV headers, summary text) in `code/analyze_correlations.py`
- [ ] T040 [US3] Generate publication-ready scatter plots with error bars in `code/analyze_correlations.py`
- [ ] T041 [US3] Save analysis results to `data/analysis/correlation_results.csv` and plots to `data/analysis/plots/`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T042 [P] Update `quickstart.md` with execution instructions for the full pipeline
- [ ] T043 Code cleanup and refactoring for type hinting consistency (verify with `mypy --strict`)
- [ ] T044 Performance optimization for large ensemble generation (implement multiprocessing in `generate_networks.py` targeting [deferred] runtime reduction)
- [ ] T045 [P] Add additional unit tests for edge cases (zero variance, disconnected graphs) in `tests/unit/`
- [ ] T046 Run `bash quickstart.sh` validation and update `state/projects/PROJ-236-exploring-the-influence-of-network-topol.yaml` `artifact_hashes` map

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on T015/T018 (network generation) for input data
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on T018 (networks) AND T029 (transport results) for input data

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
Task: "Unit test for network topology metrics in tests/unit/test_network_gen.py"
Task: "Unit test for connectivity retry logic in tests/unit/test_network_gen.py"

# Launch all models for User Story 1 together:
Task: "Implement Small-World graph generator in code/generate_networks.py"
Task: "Implement Scale-Free graph generator in code/generate_networks.py"
Task: "Implement Random graph generator in code/generate_networks.py"
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
- **Critical Constraint**: All transport simulations (T024-T029) must run within 45 minutes on 2 CPU cores; if convergence fails, the task must exclude the realization and log the failure, never hang or require GPU.
- **Critical Constraint**: No synthetic/fake data generation for input; all network realizations must be procedurally generated from real atomic coordinate seeds, and transport results must be computed from real simulations, not hardcoded values.
- **Branch Note**: The feature branch in this file is `001-exploring-the-influence-of-network-topol`. The `spec.md` and `plan.md` files currently list `001-gene-regulation` which is a contradiction; these upstream files must be corrected to match this branch name.
- **Constitution Note**: The `plan.md` Constitution Check currently states "No external datasets are fetched" which contradicts Constitution Principle III. This must be corrected in `plan.md` to reflect that external datasets (or physical seeds) are fetched from canonical sources.
- **FR-006 Note**: The `plan.md` FR/SC Mapping for FR-006 currently mentions "uniform LJ potential" which contradicts the spec. This must be corrected to "perturbation theory" in `plan.md`.
- **Spec Note**: The `spec.md` FR-004 line has a formatting error (broken text) that must be fixed in `spec.md`.