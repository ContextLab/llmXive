# Tasks: Exploring the Influence of Network Topology on Heat Transport in Disordered Materials

**Input**: Design documents from `/specs/001-exploring-the-influence-of-network-topol/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/
**Branch**: `001-exploring-the-influence-of-network-topol`
**Spec**: `specs/001-exploring-the-influence-of-network-topol/spec.md`

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
  
  Tasks MUST be organized by user story so each story can:
  - Be implemented independently
  - Be tested independently
  - Be delivered as an MVP increment
  
  DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

## Phase 0: Documentation Alignment

**Purpose**: Resolve contradictions in upstream artifacts (spec.md, plan.md) before code implementation begins.
**Dependency**: None. Must be completed before Phase 1.

- [ ] T047 [P] [Doc] Update `plan.md` and `spec.md` to replace branch name `001-gene-regulation` with `001-exploring-the-influence-of-network-topol` to resolve branch naming contradiction.
- [ ] T048 [P] [Doc] Update `plan.md` Constitution Check to explicitly state that external atomic coordinate seeds are fetched from verified sources (e.g., Zenodo, Materials Project) to satisfy Principle III (Data Hygiene).
- [ ] T049 [P] [Doc] Update `plan.md` FR/SC Mapping for FR-006 to specify "anharmonic force constant estimation via perturbation theory" OR "Harmonic Lattice Dynamics with mass disorder" (aligned with Plan's approved methodology) to align with spec requirements.
- [ ] T050 [P] [Doc] Fix formatting error in `spec.md` FR-004 line to ensure valid Markdown rendering and correct requirement text.

---

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
- [ ] T007 Create Pydantic base entities `NetworkRealization` (fields: node_count: int, edge_list: List[Tuple[int, int]], topology_type: str, cutoff_factor: float, seed: int, validation_status: Literal['valid', 'disconnected', 'failed']) and `TransportResult` (fields: network_id: str, kappa: float, error_estimate: float, convergence_status: str, runtime: float) in `code/utils/models.py`
- [ ] T008 Setup random seed management (np.random.seed(42)) in `code/utils/seeds.py`
- [ ] T017a [P] [Foundational] Implement 'Physical Stability Filter' in `code/utils/validation.py` to check for bond-distance thresholds and atomic stability based on Assumptions (no FR-010 tag)
- [ ] T018a [P] [FR-001] Implement explicit connectivity validation logic to ensure >95% of realizations are connected in `code/generate_networks.py` (Distinct deliverable for FR-001)

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

- [ ] T015 [P] [US1] Implement distance-based cutoff logic (x NN default, retry up to 2.0x) and connectivity check in `code/generate_networks.py` (Moved from Phase 2 to US1 block)
- [ ] T012 [P] [US1] Implement Small-World (Watts-Strogatz) graph generator in `code/generate_networks.py` (Depends on T015)
- [ ] T013 [P] [US1] Implement Scale-Free (Barabási-Albert) graph generator in `code/generate_networks.py` (Depends on T015)
- [ ] T014 [P] [US1] Implement Random (Erdős-Rényi) graph generator in `code/generate_networks.py` (Depends on T015)
- [ ] T016 [US1] Implement topological metric extraction (clustering, degree variance, spectral gap, betweenness) in `code/generate_networks.py`
- [ ] T018 [US1] Implement ensemble generation loop with `meta.json` logging for each realization in `code/generate_networks.py` (Depends on T015, T017a, T018a)
- [ ] T018b [US1] Implement ensemble generation per cutoff (x, 1.5x, 1.8x, 2.0x) in `code/generate_networks.py` (Split from T019a)
- [ ] T019a [US1] Implement transport simulation runner **stub** in `code/generate_networks.py` that calls a **placeholder** function (not the real runner) to satisfy dependency checks without executing US2 logic (Split from T019b)
- [ ] T020 [US1] Save generated graphs to `data/networks/` and checksums to `state/projects/PROJ-236-exploring-the-influence-of-network-topol.yaml`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compute Phonon Transport and Thermal Conductivity (Priority: P2)

**Goal**: Calculate effective thermal conductivity (κ) for each network realization using Harmonic Lattice Dynamics (HLA) with mass disorder and Green-Kubo solver on CPU-only hardware (per Plan's Critical Methodology Update).

**Independent Test**: Can be fully tested by running the simulation on a small, known test case (e.g., a 1D chain) and verifying the output κ matches the analytical or literature value within 10%, while confirming the process completes on a CPU-only runner.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Unit test for force constant derivation from mass disorder in `tests/unit/test_transport.py`
- [ ] T022 [P] [US2] Unit test for convergence check logic in `tests/unit/test_transport.py`
- [ ] T023 [P] [US2] Integration test for HLA solver timeout enforcement in `tests/integration/test_transport_solver.py`

### Implementation for User Story 2

- [ ] T024 [US2] [FR-006] Implement force constant derivation via **Harmonic Lattice Dynamics with mass disorder** (based on bond distances and atomic masses) in `code/compute_transport.py` (Aligned with Plan's approved methodology)
- [ ] T025a [US2] Implement Harmonic Lattice Dynamics (HLA) Green-Kubo solver core in `code/compute_transport.py` (reads `data/networks/*.graphml`, writes `data/transport/results.csv`, uses **reduced units (sigma=1.0, epsilon=1.0), Temperature T=1.0**)
- [ ] T025b [US2] Implement convergence check and retry logic (A limited number of retries is permitted.) in `code/utils/validation.py`
- [ ] T025c [US2] Implement timeout enforcement (min limit) per realization and result serialization in `code/compute_transport.py`
- [ ] T029 [US2] Save transport results to `data/transport/transport_results.csv` with metadata in `code/compute_transport.py`
- [ ] T029b [US2] Implement transport simulation runner per cutoff in `code/compute_transport.py` (Split from T019b, moved to US2)

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
- [ ] T035 [US3] Implement bootstrap resampling (A sufficient number of iterations will be performed to ensure convergence of the results.) for confidence intervals **and Variance Inflation Factor (VIF) check (threshold > 5)** in `code/analyze_correlations.py` (Integrated T037 logic)
- [ ] T036 [US3] Implement multiple-comparison correction (Bonferroni/FDR) for p-values in `code/analyze_correlations.py`
- [ ] T036b [US3] Implement result aggregation for sensitivity analysis (from T019c) in `code/analyze_correlations.py` (Moved from US1)
- [ ] T036c [US3] Implement result aggregation per cutoff for sensitivity analysis in `code/analyze_correlations.py` (Split from T019c)
- [ ] T036d [US3] [FR-008] Implement explicit verification step to validate the robustness of the topology-transport correlation across cutoffs in `code/analyze_correlations.py`
- [ ] T038 [US3] [SC-005] Implement power-law fit (R² calculation) between disorder parameters and conductivity in `code/analyze_correlations.py`
- [ ] T039 [US3] Implement associational framing logic to explicitly scrub causal language from final output artifacts (plots, CSV headers, summary text) in `code/analyze_correlations.py`
- [ ] T040a [US3] Generate publication-ready scatter plots (Metric vs Conductivity) with error bars in `code/analyze_correlations.py`
- [ ] T040b [US3] Generate error bar plots for bootstrap confidence intervals in `code/analyze_correlations.py`
- [ ] T040c [US3] Generate power-law fit plots with R² annotation in `code/analyze_correlations.py`
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

- **Phase 0 (Docs)**: No dependencies - MUST start immediately
- **Setup (Phase 1)**: Depends on Phase 0 - Can start immediately after
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on T018 (networks) for input data
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

1. Complete Phase 0: Documentation Alignment
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Phase 0 + Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0 + Setup + Foundational together
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
- **Critical Constraint**: All transport simulations (T025a, T029b) must run within 45 minutes on CPU cores; if convergence fails, the task must exclude the realization and log the failure, never hang or require GPU.
- **Critical Constraint**: No synthetic/fake data generation for input; all network realizations must be procedurally generated from real atomic coordinate seeds, and transport results must be computed from real simulations, not hardcoded values.
- **Methodology Note**: The Plan explicitly mandates **Harmonic Lattice Dynamics (HLA) with mass disorder** and **Green-Kubo** solver. All tasks in Phase 4 (T024, T025a) must adhere to this approved physics model, not Anharmonic Lattice Dynamics or Perturbation Theory.
- **Branch Note**: The feature branch is `001-exploring-the-influence-of-network-topol`. Phase 0 tasks (T047-T050) must be completed first to align upstream artifacts.
- **Constitution Note**: The `plan.md` Constitution Check must be updated to reflect fetching external atomic coordinate seeds from verified sources (Zenodo/Materials Project).
- **FR-006 Note**: Force constant derivation in T024 must align with the Plan's approved methodology (HLA with mass disorder) rather than Perturbation Theory.
- **Spec Note**: The `spec.md` FR-004 line formatting error must be fixed in Phase 0.

## Revision Tasks: Addressing Review Concerns

**Purpose**: New tasks added to address specific reviewer concerns regarding branch naming consistency, data fetch protocols, and force constant methodology. (Moved to Phase 0).

- [ ] T047 [P] [Doc] Update `plan.md` and `spec.md` to replace branch name `001-gene-regulation` with `001-exploring-the-influence-of-network-topol` to resolve branch naming contradiction.
- [ ] T048 [P] [Doc] Update `plan.md` Constitution Check to explicitly state that external atomic coordinate seeds are fetched from verified sources (e.g., Zenodo, Materials Project) to satisfy Principle III (Data Hygiene).
- [ ] T049 [P] [Doc] Update `plan.md` FR/SC Mapping for FR-006 to specify "anharmonic force constant estimation via perturbation theory" OR "Harmonic Lattice Dynamics with mass disorder" (aligned with Plan's approved methodology) to align with spec requirements.
- [ ] T050 [P] [Doc] Fix formatting error in `spec.md` FR-004 line to ensure valid Markdown rendering and correct requirement text.