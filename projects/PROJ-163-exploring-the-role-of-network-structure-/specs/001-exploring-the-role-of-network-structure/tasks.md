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

## Phase 0: Pre-Flight & Validation

**Purpose**: Validate design artifacts and enforce core constraints before coding begins.

*No active tasks in this phase. Validation is handled by the project initialization and schema creation tasks in Phase 1 and 2.*

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, directory structure, and basic configuration.

- [X] T001 [P] **Project Structure**: Create directory structure `code/`, `data/raw/`, `data/processed/`, `tests/`, `docs/`, `state/projects/` at repository root. **Verification**: Run `python -c "import os; dirs=['code','data/raw','data/processed','tests','docs','state/projects']; assert all(os.path.isdir(d) for d in dirs)"`.
- [X] T002 [P] **Dependencies**: Create `requirements.txt` with pinned versions: `qiskit-ibm-runtime`, `networkx`, `pandas`, `scipy`, `scikit-learn`, `matplotlib`, `requests`, `pytest`, `jsonschema`. Verify installation with `pip install -r requirements.txt`.
- [X] T003 [P] **Linting/Formatting**: Create `.ruff.toml` with `select = ["E", "F", "I"]` and `.black.toml` with `line-length = 88`. **Verification**: Run `python -c "import os; assert os.path.exists('.ruff.toml') and os.path.exists('.black.toml')"` and `ruff check .` (expect success if code is clean).
- [X] T009 [P] **Schema Creation**: Create `specs/001-explore-network-structure-superconducting-qubit-coupling/contracts/raw_calibration.schema.yaml` defining the JSON schema for IBM Quantum backend properties. **Content**:
  ```yaml
  type: object
  properties:
    device_id: {type: string}
    timestamp: {type: string, format: date-time}
    coupling_map: {type: array, items: {type: array, items: {type: integer}}}
    properties: {type: object}
  required: [device_id, timestamp, coupling_map, properties]
  ```
  **Verification**: Run `python -c "import yaml; yaml.safe_load(open('specs/001-explore-network-structure-superconducting-qubit-coupling/contracts/raw_calibration.schema.yaml'))"` and assert it is valid YAML.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/hygiene.py` to compute `sha256sum` for all files in `data/` and update `state/projects/PROJ-163-...yaml` artifact hashes
- [X] T005 [P] Implement basic logging infrastructure in `code/__init__.py` and `code/main.py`
- [X] T006a [P] **Environment Config**: Create `code/config.py` to load IBM Quantum API tokens from environment variables (`IBMQ_TOKEN`, `IBMQ_URL`) and default settings.
- [X] T006b [P] **CI Test Fixture**: Create `tests/fixtures/mock_backend_properties.json` with deterministic mock data for one device to enable pipeline testing without live API access. **Constraint**: This fixture is ONLY for schema/structure validation. It MUST NOT be used to verify real-data logic or API connectivity.
- [X] T007 Create base data models (dataclasses) for `QubitDevice`, `GraphMetric`, `PerformanceMetric`, `CorrelationResult` in `code/models.py`
- [X] T008a [P] **Cross-Sectional Constant**: Create `code/stats_engine.py` (stub) and add constant `CROSS_SECTIONAL_MODE = True`. **Verification**: Run `python -c "from code.stats_engine import CROSS_SECTIONAL_MODE; assert CROSS_SECTIONAL_MODE is True"`.
- [X] T008b [P] **Cross-Sectional Docstring**: Add docstring to `code/stats_engine.py` explicitly stating: "Topology and performance metrics are extracted from the same calibration snapshot (simultaneous data). Historical time window logic is disabled per Plan.md Spec Gap and FR-003 resolution." Verify docstring is present.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Retrieve and Parse IBM Quantum Calibration Data (Priority: P1) 🎯 MVP

**Goal**: Automatically fetch the latest calibration properties for all publicly accessible IBM Quantum backends, ensuring data freshness (≤ 30 days).

**Independent Test**: A script can be run to download data for specific devices (e.g., `ibmq_manila`, `ibmq_quito`) and verify the output JSON/CSV contains valid graph adjacency lists, non-null coherence time values, and timestamps indicating data freshness.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] **Contract Test**: Implement contract test for API response schema parsing in `tests/test_fetcher.py` using `jsonschema` library to validate against `specs/001-explore-network-structure-superconducting-qubit-coupling/contracts/raw_calibration.schema.yaml`. **Prerequisite: T009**.

### Implementation for User Story 1

- [X] T012 [US1] Implement `fetch_backends_list` in `code/fetcher.py` to retrieve all accessible backend names
- [X] T013 [US1] **Unified Fetcher**: Implement `fetch_backend_properties` in `code/fetcher.py` including:
 1. `retry_with_exponential_backoff` logic (`max_attempts=5`, `base_delay=2.0`, `timeout=30`).
 2. Handling 503 errors and malformed data (log warning "Device {id} excluded: {reason}").
 3. **Verification**: Ensure function returns `None` or raises on unrecoverable errors; no silent fallback to synthetic data. **Test**: Assert that a simulated network error raises `ConnectionError` and does not return mock data.
 **Prerequisite: T009, T010**.
- [X] T014 [US1] Implement `validate_data_freshness` in `code/fetcher.py` to exclude devices with data > 30 days old.
- [X] T014b [US1] **Integrate Freshness Check**: Update `fetch_backend_properties` to call `validate_data_freshness` and filter out stale devices before returning. **Verification**: Run `python -c "from code.fetcher import fetch_backend_properties; # Simulate stale data check"` (logic check).
- [X] T015a [US1] Implement `extract_topology_data` in `code/fetcher.py` to extract `coupling_map` and qubit indices from raw JSON.
- [X] T015b [US1] Implement `extract_performance_metrics` in `code/fetcher.py` to extract T1, T2, `cx` gate errors, `readout_errors`.
- [X] T016 [US1] **Save Raw Snapshots**: Implement logic to save raw JSON to `data/raw/{device_id}_{YYYYMMDD_HHMMSS}.json`. **Entry Point**: Run `python code/fetcher.py --save-snapshots`. **Verification**: Assert: 1) File exists at expected path, 2) `sha256sum` matches entry in `state/projects/...yaml`, 3) File is non-empty. If `IBMQ_TOKEN` missing, use fixture from T006b. **Prerequisite: T013**.
- [X] T017 [US1] **Generate Processed CSV**: Implement logic to generate `data/processed/raw_calibration.csv` with columns: `device_id`, `timestamp`, `t1_mean`, `t2_mean`, `cx_error_mean`, `readout_error_mean`, `coupling_map`. **Entry Point**: Run `python code/fetcher.py --generate-processed`. **Verification**: Run `python -c "import pandas as pd; df=pd.read_csv('data/processed/raw_calibration.csv'); assert list(df.columns) == ['device_id', 'timestamp', 't1_mean', 't2_mean', 'cx_error_mean', 'readout_error_mean', 'coupling_map']; assert len(df) > 0 or len(df) == 0 (if no valid devices)"`. **Constraint**: Stale devices (from T014b) must be absent. **Prerequisite: T016**.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Construct Connectivity Graphs and Compute Topological Metrics (Priority: P2)

**Goal**: Transform raw coupling maps into graph structures and compute topological descriptors (average shortest-path length, clustering coefficient, edge betweenness, etc.).

**Independent Test**: A script can be run on a known graph (e.g., simple line or ring) to verify computed metrics match theoretical expectations, then applied to real device data.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for graph metric calculation on synthetic graphs in `tests/test_graph_builder.py`
- [X] T019 [P] [US2] Integration test for processing real device coupling maps in `tests/test_graph_builder.py`

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement `build_coupling_graph` in `code/graph_builder.py` to create undirected NetworkX graphs from `coupling_map` lists
- [X] T021 [US2] Implement `compute_shortest_path_metrics` in `code/graph_builder.py` (average shortest-path length, diameter) handling disconnected components
- [X] T022 [US2] Implement `compute_clustering_and_assortativity` in `code/graph_builder.py` (global clustering coefficient, degree assortativity)
- [X] T023 [US2] Implement `compute_edge_betweenness_and_spectral_gap` in `code/graph_builder.py` (edge betweenness distribution, spectral gap of Laplacian)
- [X] T024 [US2] **Handle Disconnected Graphs**: Implement logic to set spectral gap to 0 for disconnected graphs and compute path-length metrics only for the largest connected component. **Verification**: Run `python -c "from code.graph_builder import build_coupling_graph; import networkx as nx; g = build_coupling_graph([[0,1], [2,3]]); # Assert spectral gap is 0 for disconnected graph"` (logic check). **Prerequisite: T023**.
- [X] T025 [US2] **Generate Graph Metrics CSV**: Implement logic to generate `data/processed/graph_metrics.csv` with columns: `device_id`, `metric_name`, `value`, `is_finite`. **Entry Point**: Run `python code/graph_builder.py --generate-metrics`. **Prerequisite: T016, T017**. **Verification**: Assert file exists; assert columns `device_id`, `metric_name`, `value`, `is_finite` exist; assert row count > 0.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Execute Statistical Correlation and Robustness Analysis (Priority: P3)

**Goal**: Perform Spearman rank-correlation tests between graph metrics and performance indicators, apply Benjamini–Hochberg FDR correction, and conduct robustness checks.

**Independent Test**: The analysis pipeline can be run on a small synthetic dataset with known correlations to verify Spearman coefficient, p-values, and FDR correction logic.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Unit test for Spearman correlation and FDR correction in `tests/test_stats_engine.py`
- [X] T027 [P] [US3] Integration test for full pipeline with synthetic data in `tests/test_stats_engine.py`

### Implementation for User Story 3

- [X] T028 [US3] **Load and Merge**: Implement `load_and_merge_metrics` in `code/stats_engine.py` to join graph metrics and performance metrics by `device_id` ONLY. **Prerequisite: T016, T017, T025**. Enforce `CROSS_SECTIONAL_MODE` logic. **Verification**: Assert merged DataFrame has non-zero rows and correct columns.
- [X] T029 [US3] **Correlation Engine**: Implement `compute_spearman_correlations` in `code/stats_engine.py` for all metric pairs using simultaneous data. **Documentation**: Add comment: "Implements cross-sectional analysis per FR-003. Topology and performance extracted from same snapshot." **Prerequisite: T028**. **Verification**: Assert output DataFrame has columns `metric_a`, `metric_b`, `rho`, `p_value`.
- [X] T030 [US3] Implement `apply_benjamini_hochberg_fdr` in `code/stats_engine.py` to adjust p-values and flag significant results (`adj_p < 0.05`).
- [X] T031a [US3] Implement `robustness_check_lodo` in `code/stats_engine.py` to perform leave-one-device-out (LODO) analysis and verify stability of significant correlations (|Δρ| ≤ 0.1) across subsets.
- [X] T031b [US3] **Historical Window Robustness**: Implement `robustness_check_time_window` in `code/stats_engine.py`.
 1. **Attempt** to fetch performance metrics from a 30-day historical window (if API supports it) using `backend.properties(date=...)`.
 2. Compare correlation stability against the full dataset.
 3. **Constraint**: Do NOT fetch historical topology (static).
 4. **Documentation**: If API does not support historical fetches (expected), update `research.md` with EXACT text: "FR-004 Time Window check could not be performed as the IBM Quantum API does not expose historical performance states for past dates. Correlation stability is assessed via LODO (T031a) and cross-sectional variance only."
 5. **Verification**: Assert that the function attempts the API call and logs the result (success or failure). **Prerequisite: T029, T030**.
- [X] T032 [US3] Implement `sensitivity_analysis` in `code/stats_engine.py` sweeping a configurable set of p-value thresholds. Define `P_VALUE_THRESHOLDS` constant.
- [X] T033 [US3] Implement `power_analysis` in `code/stats_engine.py` to estimate Minimum Detectable Effect Size (MDES) given sample size (N), number of tests, power=0.8, alpha=0.05, and report 95% CI if N < 30.
- [X] T034 [US3] **Generate Correlation Results**: Implement logic to generate `data/processed/correlation_results.csv` with columns `metric_a`, `metric_b`, `spearman_rho`, `p_value`, `adj_p_value`, `is_significant`, `is_excluded`. **Entry Point**: Run `python code/stats_engine.py --generate-results`. **Verification**: Assert file exists; assert non-zero rows; assert `adj_p_value` column exists; assert `is_significant` column exists. **Prerequisite: T031a, T031b**.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Reporting

**Purpose**: Generate visualizations and final reports

- [X] T035 [US3] Implement `generate_scatter_plots` in `code/viz.py` for significant correlations
- [X] T036 [US3] Implement `generate_heatmap` in `code/viz.py` for the full correlation matrix
- [X] T037 [US3] **Generate Report**: Implement logic to generate `docs/report.md`.
 - **Sections**: Methodology (referencing T028/T029 and `research.md`), Correlation Results, Robustness Checks (LODO and Time Window Limitation), Power Analysis.
 - **Entry Point**: Run `python code/viz.py --generate-report`.
 - **Verification**: Assert `docs/report.md` exists; assert file contains string "LODO"; assert file contains string "Time Window Limitation" OR "Time Window Results" (depending on T031b outcome); assert `is_excluded` flag is discussed. **Prerequisite: T034, T031b**.
- [X] T038 [P] Run `code/hygiene.py` to update artifact hashes and state file
- [X] T039 [P] Validate `quickstart.md` and ensure all scripts run end-to-end

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
Task: "Implement unified fetcher with retry logic in code/fetcher.py"
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
- **Constraint**: All analysis tasks must run on CPU-only CI (limited cores, modest RAM). No GPU models, no low-bit quantization, no large LLMs. Use `scipy`, `networkx`, `pandas`, `scikit-learn` only.
- **Data Integrity**: No synthetic/fake data generation. All metrics must derive from real IBM Quantum API data. T006b provides mock data ONLY for CI pipeline validation.
- **Data Flow**: US1 (Fetch) → US2 (Graph) → US3 (Stats). Ensure US3 tasks run after US1/US2 produce `data/processed/` files. T028 and T029 explicitly depend on T016, T017, and T025.
- **Scientific Correction**: US3 tasks (T028, T029, T031a, T031b) must use simultaneous data (T028) and LODO robustness (T031a) per Plan.md Spec Gap and T008 constant. T031b implements the real FR-004 historical window check (performance only) or documents the API limitation.