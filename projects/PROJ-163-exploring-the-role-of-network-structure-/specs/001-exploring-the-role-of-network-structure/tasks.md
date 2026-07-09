# Tasks: Exploring the Role of Network Structure in Superconducting Qubit Coupling

**Input**: Design documents from `/specs/001-explore-network-structure-superconducting-qubit-coupling/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root (per plan.md structure)
- Paths shown below assume single project - adjusted based on plan.md structure

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

- [ ] T001 Create project structure per implementation plan (`code/`, `data/raw/`, `data/processed/`, `tests/`)
- [ ] T002 Initialize Python 3.11 project with dependencies: `qiskit-ibm-runtime`, `networkx`, `pandas`, `scipy`, `matplotlib`, `requests`, `pytest`
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create `code/hygiene.py` to compute `sha256sum` for all files in `data/` and update `state/projects/PROJ-163-...yaml` artifact hashes
- [X] T005 [P] Implement basic logging infrastructure in `code/__init__.py` and `code/main.py`
- [ ] T006 [P] Setup environment configuration management (load IBM Quantum API tokens/defaults)
- [~] T007 Create base data models (dataclasses) for `QubitDevice`, `GraphMetric`, `PerformanceMetric`, `CorrelationResult` in `code/models.py`
- [~] T008 [US1] Update `spec.md` (FR-003) to formally retract the "historical time window" requirement for topology, documenting the resolution as a cross-sectional study (per Plan.md Spec Gap). This task must be completed before T028/T029.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Retrieve and Parse IBM Quantum Calibration Data (Priority: P1) 🎯 MVP

**Goal**: Automatically fetch the latest calibration properties for all publicly accessible IBM Quantum backends, ensuring data freshness (≤ 30 days).

**Independent Test**: A script can be run to download data for specific devices (e.g., `ibmq_manila`, `ibmq_quito`) and verify the output JSON/CSV contains valid graph adjacency lists, non-null coherence time values, and timestamps indicating data freshness.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T010 [P] [US1] Contract test for API response schema parsing in `tests/test_fetcher.py` using `jsonschema` library to validate against `specs/001-explore-network-structure-superconducting-qubit-coupling/contracts/raw_calibration.schema.yaml`
- [~] T011 [P] [US1] Integration test for live API fetch with rate-limit handling in `tests/test_integration_fetch.py`

### Implementation for User Story 1

- [~] T012 [US1] Implement `fetch_backends_list` in `code/fetcher.py` to retrieve all accessible backend names
- [~] T013a [US1] Implement `retry_with_exponential_backoff` in `code/fetcher.py` with explicit parameters: max 3 attempts, 2^N backoff delay, and 60-second timeout to handle 503 errors as a distinct unit of work.
- [~] T013b [US1] Implement `fetch_backend_properties` in `code/fetcher.py` using the retry logic from T013a, handling 503 errors and malformed data (log warning and exclude device) per US1 Acceptance Scenario 2.
- [~] T014 [US1] Implement `validate_data_freshness` in `code/fetcher.py` to exclude devices with data > 30 days old, ensuring the 60-second timeout constraint is enforced.
- [~] T015a [US1] Implement `extract_topology_data` in `code/fetcher.py` to extract `coupling_map` and qubit indices from raw JSON.
- [ ] T015b [US1] Implement `extract_performance_metrics` in `code/fetcher.py` to extract `T1`, `T2`, `gate_errors`, and `readout_errors` from raw JSON.
- [ ] T016 [US1] Save raw JSON snapshots to `data/raw/` with timestamps and checksums
- [ ] T017 [US1] Generate structured CSV `data/processed/raw_calibration.csv` containing all valid device metrics

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Construct Connectivity Graphs and Compute Topological Metrics (Priority: P2)

**Goal**: Transform raw coupling maps into graph structures and compute topological descriptors (average shortest-path length, clustering coefficient, edge betweenness, etc.).

**Independent Test**: A script can be run on a known graph (e.g., simple line or ring) to verify computed metrics match theoretical expectations, then applied to real device data.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for graph metric calculation on synthetic graphs in `tests/test_graph_builder.py`
- [ ] T019 [P] [US2] Integration test for processing real device coupling maps in `tests/test_graph_builder.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement `build_coupling_graph` in `code/graph_builder.py` to create undirected NetworkX graphs from `coupling_map` lists
- [ ] T021 [US2] Implement `compute_shortest_path_metrics` in `code/graph_builder.py` (average shortest-path length, diameter) handling disconnected components
- [ ] T022 [US2] Implement `compute_clustering_and_assortativity` in `code/graph_builder.py` (global clustering coefficient, degree assortativity)
- [ ] T023 [US2] Implement `compute_edge_betweenness_and_spectral_gap` in `code/graph_builder.py` (edge betweenness distribution, spectral gap of Laplacian)
- [ ] T024 [US2] Handle disconnected graphs: set spectral gap to 0, compute path-length metrics only for connected components
- [ ] T025 [US2] Generate structured CSV `data/processed/graph_metrics.csv` linking `device_id`, `metric_name`, `value`, `is_finite`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Execute Statistical Correlation and Robustness Analysis (Priority: P3)

**Goal**: Perform Spearman rank-correlation tests between graph metrics and performance indicators, apply Benjamini–Hochberg FDR correction, and conduct robustness checks.

**Independent Test**: The analysis pipeline can be run on a small synthetic dataset with known correlations to verify Spearman coefficient, p-values, and FDR correction logic.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test for Spearman correlation and FDR correction in `tests/test_stats_engine.py`
- [ ] T027 [P] [US3] Integration test for full pipeline with synthetic data in `tests/test_stats_engine.py`

### Implementation for User Story 3

- [ ] T028 [US3] Implement `load_and_merge_metrics` in `code/stats_engine.py` to join graph metrics and performance metrics by `device_id` ONLY, ignoring timestamps (cross-sectional logic per T008 spec retraction).
- [ ] T029 [US3] Implement `compute_spearman_correlations` in `code/stats_engine.py` for all metric pairs using simultaneous data, handling missing values by exclusion, and explicitly documenting the deviation from original FR-003 temporal window.
- [ ] T030 [US3] Implement `apply_benjamini_hochberg_fdr` in `code/stats_engine.py` to adjust p-values and flag significant results (`adj_p < 0.05`)
- [ ] T031a [US3] Implement `robustness_check_lodo` in `code/stats_engine.py` to perform leave-one-device-out (LODO) analysis and verify stability of significant correlations (|Δρ| ≤ 0.1) across subsets.
- [ ] T031b [US3] Implement `robustness_check_time_window` in `code/stats_engine.py` to retrieve performance metrics from a fixed 30-day historical window and compare correlation direction/magnitude with the full dataset (satisfying SC-004).
- [ ] T032 [US3] Implement `sensitivity_analysis` in `code/stats_engine.py` sweeping a configurable set of p-value thresholds (derived from a constant) over conventional values
- [ ] T033 [US3] Implement `power_analysis` in `code/stats_engine.py` to estimate Minimum Detectable Effect Size (MDES) given sample size (N), number of tests performed (multiple comparison burden), and report 95% CI if N < 30
- [ ] T034 [US3] Generate `data/processed/correlation_results.csv` with `metric_a`, `metric_b`, `spearman_rho`, `p_value`, `adj_p_value`, `is_significant`, `is_excluded`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Reporting

**Purpose**: Generate visualizations and final reports

- [ ] T035 [US3] Implement `generate_scatter_plots` in `code/viz.py` for significant correlations
- [ ] T036 [US3] Implement `generate_heatmap` in `code/viz.py` for the full correlation matrix
- [ ] T037 [US3] Generate final summary report artifact `docs/report.md` aggregating plots from T035/T036, including sections for: Methodology (referencing T008), Correlation Results, Robustness Checks (LODO and Time Window), and Power Analysis.
- [ ] T038 [P] Run `code/hygiene.py` to update artifact hashes and state file
- [ ] T039 [P] Validate `quickstart.md` and ensure all scripts run end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data for graph construction
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 data for correlation

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
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
Task: "Contract test for API response schema parsing in tests/test_fetcher.py"
Task: "Integration test for live API fetch in tests/test_integration_fetch.py"

# Launch all models for User Story 1 together:
Task: "Implement fetch_backends_list in code/fetcher.py"
Task: "Implement exponential backoff retry logic in code/fetcher.py"
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
- **Constraint**: All analysis tasks must run on CPU-only CI (limited cores, modest RAM). No GPU models, no 8-bit quantization, no large LLMs. Use `scipy`, `networkx`, `pandas` only.
- **Data Integrity**: No synthetic/fake data generation. All metrics must derive from real IBM Quantum API data.
- **Data Flow**: US1 (Fetch) → US2 (Graph) → US3 (Stats). Ensure US3 tasks run after US1/US2 produce `data/processed/` files.
- **Scientific Correction**: US3 tasks (T028, T029, T031a, T031b) must use simultaneous data (T028) and cross-sectional robustness (LODO + Time Window) per Plan.md Spec Gap and T008 spec retraction, ignoring the original FR-003 temporal window requirement for topology.