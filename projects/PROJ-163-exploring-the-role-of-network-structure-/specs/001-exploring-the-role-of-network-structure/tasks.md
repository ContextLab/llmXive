# Tasks: Exploring the Role of Network Structure in Superconducting Qubit Coupling

**Input**: Design documents from `/specs/001-explore-network-structure-superconducting-qubit-coupling/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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

  Tasks MUST be organized by user story so each story can be independently completable and testable.

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
- [X] T003 [P] **Linting/Formatting**: Create `.ruff.toml` with `select = ["E", "F", "I"]` and `.black.toml` with `line-length = 88`. **Verification**: Run `python -c "import os; assert os.path.exists('.ruff.toml') and os.path.exists('.black.toml')"` and `ruff check.` (expect success if code is clean).
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

- [X] T004b [P] **State File Initialization**: Create `state/projects/PROJ-163-exploring-the-role-of-network-structure-.yaml` with the initial structure and empty `artifact_hashes` map. **Content**:
 ```yaml
 project_id: "PROJ-163-exploring-the-role-of-network-structure-"
 updated_at: "2024-05-21T00:00:00Z"
 artifact_hashes: {}
 ```
 **Verification**: Run `python -c "import yaml; data=yaml.safe_load(open('state/projects/PROJ-163-exploring-the-role-of-network-structure-.yaml')); assert 'artifact_hashes' in data and isinstance(data['artifact_hashes'], dict)"`.
- [X] T004 [P] **Hygiene & Reproducibility**: Create `code/hygiene.py` to:
 1. Compute `sha256sum` for all files in `data/` and update `state/projects/PROJ-163-...yaml` artifact hashes.
 2. Fetch the current `git commit hash` using `git rev-parse HEAD`.
 3. Read `requirements.txt` and compute its `sha256sum`.
 4. Capture the Python version via `python --version`.
 5. Write all these values (`git_hash`, `requirements_hash`, `python_version`) to `state/projects/PROJ-163-...reproducibility.yaml`.
 **Verification**: Run `python code/hygiene.py` and assert exit code 0; then assert that `state/projects/PROJ-163-...reproducibility.yaml` exists and contains non‑empty `git_hash`, `requirements_hash`, and `python_version` fields.
- [X] T005a [P] **Logging Config Module**: Create `code/logging_config.py` with a `get_logger(name)` function that returns a logger configured with a JSON formatter and file handler (optional). **Verification**: Run `python -c "from code.logging_config import get_logger; l = get_logger('test'); assert l is not None"`.
- [X] T005b [P] **Root Logger Setup**: Update `code/main.py` to import `get_logger` from `logging_config` and initialize the root logger with a console handler. **Verification**: Run `python code/main.py --help` and assert no import errors occur. **Prerequisite**: T005a.
- [X] T006a [P] **Environment Config**: Create `code/config.py` to load IBM Quantum API tokens from environment variables (`IBMQ_TOKEN`, `IBMQ_URL`) and default settings. **Verification**: Run `python -c "from code.config import load_config; cfg=load_config(); assert 'IBMQ_TOKEN' in cfg or 'IBMQ_TOKEN' in os.environ"` (or assert that `load_config` raises a clear error if the env var is missing).
- [X] T006b [P] **Token Validation**: Create `scripts/validate_token.py` that attempts to connect to the IBM Quantum API using the token from `code/config.py`. If the token is missing or invalid, it must exit with code 1 and print "ERROR: Invalid or missing IBMQ_TOKEN". If valid, exit 0. **Verification**: Run `python scripts/validate_token.py` with a missing token (expect fail) and with a valid token (expect pass). **Prerequisite**: T006a.
- [X] T007a [P] **Data Models (Part 1)**: Create `code/models.py` and define `QubitDevice` and `GraphMetric` dataclasses with required fields. **Verification**: Run `python -c "from code.models import QubitDevice, GraphMetric; assert hasattr(QubitDevice, 'device_id') and hasattr(GraphMetric, 'metric_name')"`.
- [X] T007b [P] **Data Models (Part 2)**: Update `code/models.py` to define `PerformanceMetric` and `CorrelationResult` dataclasses. **Verification**: Run `python -c "from code.models import PerformanceMetric, CorrelationResult; assert hasattr(PerformanceMetric, 't1') and hasattr(CorrelationResult, 'rho')"`. **Prerequisite**: T007a.
- [X] T008a [P] **Cross-Sectional Constant**: Create `code/stats_engine.py` (stub) and add constant `CROSS_SECTIONAL_MODE = True`. **Verification**: Run `python -c "from code.stats_engine import CROSS_SECTIONAL_MODE; assert CROSS_SECTIONAL_MODE is True"`.
- [X] T008b [P] **Cross-Sectional Docstring**: Add docstring to `code/stats_engine.py` explicitly stating: "Topology and performance metrics are extracted from the same calibration snapshot (simultaneous data). Historical time window logic is disabled per Plan.md Spec Gap and FR‑003 resolution." Verify docstring is present.
- [X] T011 [P] **Contract Registry Initialization**: Create `specs/001-explore-network-structure-superconducting-qubit-coupling/contracts/registry.yaml` listing all schema files (T009, T041a, etc.) and their paths. **Content**:
 ```yaml
 type: object
 schemas:
 - path: raw_calibration.schema.yaml
   description: "Schema for IBM Quantum backend properties"
 - path: graph_metrics.schema.yaml
   description: "Schema for graph metrics"
 - path: correlation_results.schema.yaml
   description: "Schema for correlation results"
 - path: mdes_report.schema.yaml
   description: "Schema for MDES report"
 ```
 **Verification**: Assert file exists and contains valid YAML with a `schemas` list. **Prerequisite**: T009, T041a.

---

## Phase 3: User Story 1 - Retrieve and Parse IBM Quantum Calibration Data (Priority: P1) 🎯 MVP

**Goal**: Automatically fetch the latest calibration properties for all publicly accessible IBM Quantum backends, ensuring data freshness (≤ 30 days).

**Independent Test**: A script can be run to download data for specific devices (e.g., `ibmq_manila`, `ibmq_quito`) and verify the output JSON/CSV contains valid graph adjacency lists, non‑null coherence time values, and timestamps indicating data freshness.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] **Contract Test**: Write contract test for API response schema parsing in `tests/test_fetcher.py` using `jsonschema` library to validate against `specs/001-explore-network-structure-superconducting-qubit-coupling/contracts/raw_calibration.schema.yaml`. **Verification**: Assert test file exists and syntax is valid (e.g., `python -m py_compile tests/test_fetcher.py`).
- [X] T013a-test [P] [US1] **Test Retry Logic**: Write `tests/test_fetcher.py::test_retry_with_exponential_backoff` that mocks a `requests.get` call to raise a `ConnectionError` twice, then succeeds on the third call. Assert that `time.sleep` is called with increasing delays (2s, 4s, 8s…) up to `max_attempts=5` and the function eventually returns the mock response. **Verification**: `pytest tests/test_fetcher.py::test_retry_with_exponential_backoff -v`. **Prerequisite**: T013a-impl.
- [X] T013b-test [P] [US1] **Test Error Handling**: Write `tests/test_fetcher.py::test_fetch_backend_properties_error` that mocks a 503 error and asserts the function logs a warning and excludes the device without returning mock data. **Verification**: `pytest tests/test_fetcher.py::test_fetch_backend_properties_error -v`. **Prerequisite**: T013b-impl.
- [X] T013c-test [P] [US1] **Test No Synthetic Fallback**: Write `tests/test_fetcher.py::test_no_synthetic_fallback` that mocks a complete API failure and asserts the function raises an exception or returns an empty list, never a synthetic dataset. **Verification**: `pytest tests/test_fetcher.py::test_no_synthetic_fallback -v`. **Prerequisite**: T013c-impl.

### Implementation for User Story 1

- [X] T012 [US1] Implement `fetch_backends_list` in `code/fetcher.py` to retrieve all accessible backend names.
- [X] T013a-impl [US1] **Unified Fetcher (Retry)**: Implement `retry_with_exponential_backoff` logic in `code/fetcher.py` (`max_attempts=5`, `base_delay=2.0`, `timeout=30`). **Verification**: Run `pytest tests/test_fetcher.py::test_retry_with_exponential_backoff -v` (must pass). **Prerequisite**: T013a-test.
- [X] T013b-impl [US1] **Unified Fetcher (Error Handling)**: Implement `fetch_backend_properties` in `code/fetcher.py` handling 503 errors and malformed data (log warning `"Device {id} excluded: {reason}"`). **Verification**: Run `pytest tests/test_fetcher.py::test_fetch_backend_properties_error -v` (must pass). **Prerequisite**: T013b-test.
- [X] T013c-impl [US1] **Unified Fetcher (Verification)**: Implement logic to ensure no synthetic fallback occurs in `fetch_backend_properties`. **Verification**: Run `pytest tests/test_fetcher.py::test_no_synthetic_fallback -v` (must pass). **Prerequisite**: T013c-test.
- [X] T014 [US1] Implement `validate_data_freshness` in `code/fetcher.py` to exclude devices with data > 30 days old.
- [X] T014b [US1] **Integrate Freshness Check**: Update `fetch_backend_properties` to call `validate_data_freshness` and filter out stale devices before returning. **Verification**: Run a short script that simulates stale data and confirms exclusion.
- [X] T015a [US1] Implement `extract_topology_data` in `code/fetcher.py` to extract `coupling_map` and qubit indices from raw JSON. **Prerequisite**: T013c-impl, T014b.
- [X] T015b [US1] Implement `extract_performance_metrics` in `code/fetcher.py` to extract T1, T2, `cx` gate errors, `readout_errors`. **Prerequisite**: T013c-impl.
- [X] T016 [US1] **Save Raw Snapshots**: Implement logic to save raw JSON to `data/raw/{device_id}_{YYYYMMDD_HHMMSS}.json` using timestamp format `%Y%m%d_%H%M%S`. If multiple snapshots exist for the same device, append a unique suffix. **Entry Point**: Run `python code/fetcher.py --save-snapshots`. **Verification**: Assert file exists at expected path, `sha256sum` matches entry in `state/projects/PROJ-163-...yaml`, and file is non‑empty. If `IBMQ_TOKEN` missing, use fixture from T006b.
- [X] T017a [US1] **Generate Performance Metrics CSV**: Implement logic to generate `data/processed/performance_metrics.csv` with columns `device_id`, `timestamp`, `t1_mean`, `t2_mean`, `cx_error_mean`, `readout_error_mean`. **Serialization**: No coupling map is stored here. **Verification**: Assert file exists and contains expected columns.
- [X] T017b [US1] **Validate Performance Metrics Schema**: Validate the generated `data/processed/performance_metrics.csv` against the schema defined in `specs/001-explore-network-structure-superconducting-qubit-coupling/contracts/raw_calibration.schema.yaml`. **Prerequisite**: T017a.
- [X] T018 [P] [US2] Unit test for graph metric calculation on synthetic graphs in `tests/test_graph_builder.py`.
- [X] T019 [P] [US2] Integration test for processing real device coupling maps in `tests/test_graph_builder.py`.
- [X] T020a-test [P] [US2] **Test Graph Construction**: Write `tests/test_graph_builder.py::test_build_coupling_graph` that creates a known graph (e.g., triangle) from a `coupling_map` and asserts the number of nodes and edges matches expectations. **Verification**: `pytest tests/test_graph_builder.py::test_build_coupling_graph -v`. **Prerequisite**: T018.
- [X] T020a-impl [US2] **Build Coupling Graph**: Implement `build_coupling_graph` in `code/graph_builder.py` to create undirected NetworkX graphs from `coupling_map` lists. **Verification**: Run `pytest tests/test_graph_builder.py::test_build_coupling_graph -v` (must pass). **Prerequisite**: T020a-test.
- [X] T021 [US2] Implement `compute_shortest_path_metrics` in `code/graph_builder.py` (average shortest‑path length, diameter) handling disconnected components.
- [X] T022 [US2] Implement `compute_clustering_and_assortativity` in `code/graph_builder.py` (global clustering coefficient, degree assortativity).
- [X] T023 [US2] Implement `compute_edge_betweenness_and_spectral_gap` in `code/graph_builder.py` (edge betweenness distribution, spectral gap of Laplacian).
- [X] T024 [US2] **Handle Disconnected Graphs**: Implement logic to set spectral gap to a value consistent with disconnected graphs and compute path‑length metrics only for the largest connected component. **Verification**: Run `python -c "from code.graph_builder import build_coupling_graph, compute_edge_betweenness_and_spectral_gap; import networkx as nx; g=build_coupling_graph([[0,1],[2,3]]); sg=compute_edge_betweenness_and_spectral_gap(g); assert sg==0"`. **Prerequisite**: T023.
- [X] T025a [US2] **Compute Per-Device Graph Metrics**: Compute all graph metrics for each device based on its coupling map. **Verification**: Assert all metrics are computed without errors and stored in a DataFrame.
- [X] T025b [US2] **Generate Graph Metrics CSV**: Implement logic to generate `data/processed/graph_metrics.csv` with columns `device_id`, `metric_name`, `value`, `is_finite`. **Deserialization**: For each device, read the raw JSON file `data/raw/{device_id}_*.json`, load the `coupling_map` JSON, then build the graph. **Entry Point**: Run `python code/graph_builder.py --generate-metrics`. **Prerequisite**: T016, T025a.
- [X] T026 [US3] **Spearman & FDR**: Implement `compute_spearman_correlations` and `apply_benjamini_hochberg_fdr` in `code/stats_engine.py`.
- [X] T027 [US3] **Full Pipeline Test**: Implement `tests/test_stats_engine.py::test_full_pipeline_synthetic`.
- [X] T028 [US3] **Load and Merge Metrics**: Implement `load_and_merge_metrics` in `code/stats_engine.py` to join `data/processed/performance_metrics.csv` and `data/processed/graph_metrics.csv` by `device_id` ONLY.
- [X] T029 [US3] **Correlation Engine**: Implement `compute_spearman_correlations` in `code/stats_engine.py` for all metric pairs using simultaneous data.
- [X] T030 [US3] **Apply FDR**: Implement `apply_benjamini_hochberg_fdr` in `code/stats_engine.py` to adjust p-values and flag significant results (`adj_p < 0.05`).
- [X] T031c [US3] **Robustness Check**: Implement `robustness_check_time_window` in `code/stats_engine.py`.
- [X] T032 [US3] **Sensitivity Analysis**: Implement `sensitivity_analysis` in `code/stats_engine.py`.
- [X] T033 [US3] **Power Analysis**: Implement `power_analysis` in `code/stats_engine.py`.
- [X] T034a [US3] **Compute Correlations**: Implement the core Spearman correlation calculation and p-value generation.
- [X] T034b [US3] **Apply FDR Adjustment**: Implement Benjamini-Hochberg FDR correction on p-values.
- [X] T034c [US3] **Write Correlation Results CSV**: Write the final correlation results to `data/processed/correlation_results.csv`.
- [X] T035 [US3] **Generate Scatter Plots**: Implement `generate_scatter_plots` in `code/viz.py` for significant correlations.
- [X] T036 [US3] **Generate Heatmap**: Implement `generate_heatmap` in `code/viz.py` for the full correlation matrix.
- [X] T037 [US3] **Generate Report**: Implement logic to generate `docs/report.md`.
- [X] T038 [P] Run `code/hygiene.py` to update artifact hashes and state file.
- [X] T039 [US3] **Validate Quickstart**: Validate `quickstart.md` and ensure all scripts run end‑to‑end.
- [X] T040 [P] [US1] **API Rate Limit Enforcement**: Implement strict exponential backoff with jitter in `code/fetcher.py`.
- [X] T041a [P] **MDES Schema Definition**: Create `specs/001-explore-network-structure-superconducting-qubit-coupling/contracts/mdes_report.schema.yaml`.
- [X] T042 [P] **Robustness Check Documentation**: Update documentation to explicitly state the limitations of the cross-sectional analysis and the interpretation of the robustness checks.
- [X] T043 [P] **Data Integrity Audit**: Add a validation step in `code/hygiene.py`.
- [X] T044 [P] **End-to-End Integration Test**: Implement `tests/test_end_to_end.py`.
- [X] T045 [P] **Live API Sanity Check**: Implement a lightweight script `scripts/sanity_check_api.py`.
- [X] T046 [P] **Reproducibility Audit**: Run `python code/hygiene.py` to generate `state/projects/PROJ-163-...reproducibility.yaml`.
- [X] T047 [US3] **MDES Sensitivity Report**: Extend `docs/report.md` to include a visual or tabular summary of the MDES analysis.
- [X] T048 [P] **API Fallback & Error Handling Validation**: Implement a dedicated integration test `tests/test_fetcher_errors.py`.

---

## Phase 5: Polish & Reporting

**Purpose**: Generate visualizations and final reports

## Phase 7: Review Resolution & Robustness Enhancements

**Purpose**: Address specific reviewer concerns regarding data integrity, statistical power, and API reliability.

## Phase 8: Final Validation & Execution Readiness

**Purpose**: Ensure the entire pipeline is robust, reproducible, and ready for the execution stage.
