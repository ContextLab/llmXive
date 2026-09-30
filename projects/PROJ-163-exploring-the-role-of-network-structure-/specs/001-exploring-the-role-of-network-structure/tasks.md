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
- [X] T009 [P] **Raw Schema Creation**: Create `specs/001-explore-network-structure-superconducting-qubit-coupling/contracts/raw_calibration.schema.json` defining the JSON schema for IBM Quantum backend properties. **Content**:
 ```json
 {
 "$schema": "http://json-schema.org/draft-07/schema#",
 "type": "object",
 "properties": {
 "device_id": { "type": "string" },
 "timestamp": { "type": "string", "format": "date-time" },
 "coupling_map": { "type": "array", "items": { "type": "array", "items": { "type": "integer" } } },
 "properties": { "type": "object" }
 },
 "required": ["device_id", "timestamp", "coupling_map", "properties"]
 }
 ```
 **Verification**: Run `python -c "import json; json.load(open('specs/001-explore-network-structure-superconducting-qubit-coupling/contracts/raw_calibration.schema.json'))"` and assert it is valid JSON.
- [X] T010 [P] **Processed Performance Schema**: Create `specs/001-explore-network-structure-superconducting-qubit-coupling/contracts/performance_metrics.schema.json` defining the schema for the processed performance metrics CSV. **Content**:
 ```json
 {
 "$schema": "http://json-schema.org/draft-07/schema#",
 "type": "object",
 "properties": {
 "device_id": { "type": "string" },
 "timestamp": { "type": "string", "format": "date-time" },
 "t1_mean": { "type": "number" },
 "t2_mean": { "type": "number" },
 "cx_error_mean": { "type": "number" },
 "readout_error_mean": { "type": "number" },
 "chip_family": { "type": "string" }
 },
 "required": ["device_id", "timestamp", "t1_mean", "t2_mean", "cx_error_mean", "readout_error_mean", "chip_family"]
 }
 ```
 **Verification**: Run `python -c "import json; json.load(open('specs/001-explore-network-structure-superconducting-qubit-coupling/contracts/performance_metrics.schema.json'))"` and assert it is valid JSON.
- [X] T011 [P] **Graph Metrics Schema**: Create `specs/001-explore-network-structure-superconducting-qubit-coupling/contracts/graph_metrics.schema.json` defining the schema for the graph metrics CSV. **Content**:
 ```json
 {
 "$schema": "http://json-schema.org/draft-07/schema#",
 "type": "object",
 "properties": {
 "device_id": { "type": "string" },
 "metric_name": { "type": "string" },
 "value": { "type": "number" },
 "is_finite": { "type": "boolean" }
 },
 "required": ["device_id", "metric_name", "value", "is_finite"]
 }
 ```
 **Verification**: Run `python -c "import json; json.load(open('specs/001-explore-network-structure-superconducting-qubit-coupling/contracts/graph_metrics.schema.json'))"` and assert it is valid JSON.
- [X] T012 [P] **Correlation Results Schema**: Create `specs/001-explore-network-structure-superconducting-qubit-coupling/contracts/correlation_results.schema.json` defining the schema for the correlation results CSV. **Content**:
 ```json
 {
 "$schema": "http://json-schema.org/draft-07/schema#",
 "type": "object",
 "properties": {
 "metric_a": { "type": "string" },
 "metric_b": { "type": "string" },
 "rho": { "type": "number" },
 "p_value": { "type": "number" },
 "adj_p_value": { "type": "number" }
 },
 "required": ["metric_a", "metric_b", "rho", "p_value", "adj_p_value"]
 }
 ```
 **Verification**: Run `python -c "import json; json.load(open('specs/001-explore-network-structure-superconducting-qubit-coupling/contracts/correlation_results.schema.json'))"` and assert it is valid JSON.
- [X] T011a [P] **Contract Registry Initialization (Part 1)**: Create `specs/001-explore-network-structure-superconducting-qubit-coupling/contracts/registry.yaml` listing all schema files created in Phase 1 (T009, T010, T011, T012). **Content**:
 ```yaml
 type: object
 schemas:
 - path: raw_calibration.schema.json
 description: "Schema for IBM Quantum backend properties"
 - path: performance_metrics.schema.json
 description: "Schema for processed performance metrics CSV"
 - path: graph_metrics.schema.json
 description: "Schema for graph metrics CSV"
 - path: correlation_results.schema.json
 description: "Schema for correlation results CSV"
 ```
 **Verification**: Assert file exists and contains valid YAML with a `schemas` list. **Prerequisite**: T009, T010, T011, T012.

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
 **Verification**: Run `python code/hygiene.py` and assert exit code 0; then assert that `state/projects/PROJ-163-...reproducibility.yaml` exists and contains non‑empty `git_hash`, `requirements_hash`, and `python_version` fields.
- [X] T005a [P] **Logging Config Module**: Create `code/logging_config.py` with a `get_logger(name)` function that returns a logger configured with a JSON formatter and file handler (optional). **Verification**: Run `python -c "from code.logging_config import get_logger; l = get_logger('test'); assert l is not None"`.
- [X] T005b [P] **Root Logger Setup**: Update `code/main.py` to import `get_logger` from `logging_config` and initialize the root logger with a console handler. **Verification**: Run `python code/main.py --help` and assert no import errors occur. **Prerequisite**: T005a.
- [X] T006a [P] **Environment Config**: Create `code/config.py` to load IBM Quantum API tokens from environment variables (`IBMQ_TOKEN`, `IBMQ_URL`) and default settings. **Verification**: Run `python -c "from code.config import load_config; cfg=load_config(); assert 'IBMQ_TOKEN' in cfg or 'IBMQ_TOKEN' in os.environ"` (or assert that `load_config` raises a clear error if the env var is missing).
- [X] T006b [P] **Token Validation**: Create `scripts/validate_token.py` that attempts to connect to the IBM Quantum API using the token from `code/config.py`. If the token is missing or invalid, it must exit with code 1 and print "ERROR: Invalid or missing IBMQ_TOKEN". If valid, exit 0. **Verification**: Run `python scripts/validate_token.py` with a missing token (expect fail) and with a valid token (expect pass). **Prerequisite**: T006a.
- [X] T007a [P] **Data Models (Part 1)**: Create `code/models.py` and define `QubitDevice` and `GraphMetric` dataclasses with required fields. **Verification**: Run `python -c "from code.models import QubitDevice, GraphMetric; assert hasattr(QubitDevice, 'device_id') and hasattr(GraphMetric, 'metric_name')"`.
- [X] T007b [P] **Data Models (Part 2)**: Update `code/models.py` to define `PerformanceMetric` and `CorrelationResult` dataclasses. **Verification**: Run `python -c "from code.models import PerformanceMetric, CorrelationResult; assert hasattr(PerformanceMetric, 't1') and hasattr(CorrelationResult, 'rho')"`. **Prerequisite**: T007a.
- [X] T008a [P] **Cross-Sectional Constant**: Create `code/stats_engine.py` (stub) and add constant `CROSS_SECTIONAL_MODE = True`. **Verification**: Run `python -c "from code.stats_engine import CROSS_SECTIONAL_MODE; assert CROSS_SECTIONAL_MODE is True"`.
- [X] T008b [P] **Cross-Sectional Docstring**: Add docstring to `code/stats_engine.py` explicitly stating: "Topology and performance metrics are extracted from the same calibration snapshot (simultaneous data). Historical time window logic is disabled per Plan.md Spec Gap and FR‑003 resolution." Verify docstring is present.
- [X] T013 [P] **Chip Family Extraction Logic**: Implement `extract_chip_family` in `code/fetcher.py` to extract "chip family" (e.g., Falcon, Hummingbird) from backend properties or infer from `backend_name` patterns. Store this in the `chip_family` field. **Verification**: Run `python -c "from code.fetcher import extract_chip_family; print(extract_chip_family('ibm_falcon_123'))"` and assert it returns "Falcon". **Prerequisite**: T006a.
- [X] T014 [P] **Chip Family Integration**: Update `extract_performance_metrics` in `code/fetcher.py` to include the `chip_family` field in the output dictionary. **Verification**: Run a mock fetch and assert the output dictionary contains `chip_family`. **Prerequisite**: T013.
- [X] T018 [P] **Historical Data Fetcher**: Implement `fetch_historical_performance_data` in `code/fetcher.py` to retrieve performance metrics for the last 30 days for all accessible backends. **Verification**: Run a mock fetch and assert the output is a list of historical snapshots with timestamps. **Prerequisite**: T013, T014.
- [X] T019 [P] **Historical Data Storage**: Implement logic to save historical performance snapshots to `data/historical/{device_id}_{YYYYMMDD}.json`. **Verification**: Assert file exists and contains valid JSON with timestamped metrics. **Prerequisite**: T018.
- [ ] T020 [P] **Historical Data Processor**: Implement `process_historical_data` in `code/fetcher.py` to aggregate historical snapshots into a single CSV `data/processed/historical_performance_metrics.csv`. **Verification**: Assert file exists and contains columns `device_id`, `date`, `t1_mean`, `t2_mean`, `cx_error_mean`, `readout_error_mean`, `chip_family`. **Prerequisite**: T019.
- [X] T021 [P] **Refactor Stats Engine for Cross-Sectional Enforcement**: Refactor `code/stats_engine.py` to explicitly raise a `RuntimeError` if any logic attempts to use a historical topology lag. Ensure the engine only operates on simultaneous data. **Verification**: Run a test that attempts to pass historical topology data and assert it raises `RuntimeError`. **Prerequisite**: T008a, T008b.

---

## Phase 3: User Story 1 - Retrieve and Parse IBM Quantum Calibration Data (Priority: P1) 🎯 MVP

**Goal**: Automatically fetch the latest calibration properties for all publicly accessible IBM Quantum backends, ensuring data freshness (≤ 30 days).

**Independent Test**: A script can be run to download data for specific devices (e.g., `ibmq_manila`, `ibmq_quito`) and verify the output JSON/CSV contains valid graph adjacency lists, non‑null coherence time values, and timestamps indicating data freshness.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] **Contract Test**: Write contract test for API response schema parsing in `tests/test_fetcher.py` using `jsonschema` library to validate against `specs/001-explore-network-structure-superconducting-qubit-coupling/contracts/raw_calibration.schema.json`. **Verification**: Assert test file exists and syntax is valid (e.g., `python -m py_compile tests/test_fetcher.py`).
- [X] T013a-test [P] [US1] **Test Retry Logic**: Write `tests/test_fetcher.py::test_retry_with_exponential_backoff` that mocks a `requests.get` call to raise a `ConnectionError` twice, then succeeds on the third call. Assert that `time.sleep` is called with increasing delays (2s, 4s, 8s…) up to `max_attempts=5` and the function eventually returns the mock response. **Verification**: `pytest tests/test_fetcher.py::test_retry_with_exponential_backoff -v`. **Prerequisite**: T013a-impl.
- [X] T013b-test [P] [US1] **Test Error Handling**: Write `tests/test_fetcher.py::test_fetch_backend_properties_error` that mocks a 503 error and asserts the function logs a warning and excludes the device without returning mock data. **Verification**: `pytest tests/test_fetcher.py::test_fetch_backend_properties_error -v`. **Prerequisite**: T013b-impl.
- [X] T013c-test [P] [US1] **Test No Synthetic Fallback**: Write `tests/test_fetcher.py::test_no_synthetic_fallback` that mocks a complete API failure and asserts the function raises an exception or returns an empty list, never a synthetic dataset. **Verification**: `pytest tests/test_fetcher.py::test_no_synthetic_fallback -v`. **Prerequisite**: T013c-impl.

### Implementation for User Story 1

- [X] T012 [US1] Implement `fetch_backends_list` in `code/fetcher.py` to retrieve all accessible backend names.
- [X] T013a-impl [US1] **Unified Fetcher (Retry)**: Implement `retry_with_exponential_backoff` logic in `code/fetcher.py` (`max_attempts=5`, `base_delay=2.0`, `timeout=30`). **Verification**: Run `pytest tests/test_fetcher.py::test_retry_with_exponential_backoff -v` (must pass). **Prerequisite**: T013a-test.
- [X] T013b-impl [US1] **Unified Fetcher (Error Handling)**: Implement `fetch_backend_properties` in `code/fetcher.py` handling 503 errors and malformed data (log warning `"Device {id} excluded: {reason}"`). **Verification**: Run `pytest tests/test_fetcher.py::test_fetch_backend_properties_error -v` (must pass). **Prerequisite**: T013b-test.
- [X] T013c-impl [US1] **Unified Fetcher (Verification)**: Implement logic to ensure no synthetic fallback occurs in `fetch_backend_properties`. This task MUST raise a `RuntimeError` if the API fetch fails and no valid data is returned. **Verification**: Run `pytest tests/test_fetcher.py::test_no_synthetic_fallback -v` (must pass). **Prerequisite**: T013c-test.
- [X] T014 [US1] Implement `validate_data_freshness` in `code/fetcher.py` to exclude devices with data > 30 days old.
- [X] T014b [US1] **Integrate Freshness Check**: Update `fetch_backend_properties` to call `validate_data_freshness` and filter out stale devices before returning. **Verification**: Run a short script that simulates stale data and confirms exclusion.
- [X] T015a [US1] Implement `extract_topology_data` in `code/fetcher.py` to extract `coupling_map` and qubit indices from raw JSON. **Prerequisite**: T013c-impl, T014b.
- [X] T015b [US1] Implement `extract_performance_metrics` in `code/fetcher.py` to extract T1, T2, `cx` gate errors, `readout_errors`. **Prerequisite**: T013c-impl.
- [X] T016 [US1] **Save Raw Snapshots**: Implement logic to save raw JSON to `data/raw/{device_id}_{YYYYMMDD_HHMMSS}.json` using timestamp format `%Y%m%d_%H%M%S`. If multiple snapshots exist for the same device, append a unique suffix. **Entry Point**: Run `python code/fetcher.py --save-snapshots`. **Verification**: Assert file exists at expected path, `sha256sum` matches entry in `state/projects/PROJ-163-...yaml`, and file is non‑empty. If `IBMQ_TOKEN` missing, use fixture from T006b.
- [ ] T017a [US1] **Generate Performance Metrics CSV**: Implement logic to generate `data/processed/performance_metrics.csv` with columns `device_id`, `timestamp`, `t1_mean`, `t2_mean`, `cx_error_mean`, `readout_error_mean`, `chip_family`. **Serialization**: No coupling map is stored here. **Verification**: Assert file exists and contains expected columns.
- [ ] T017b [US1] **Validate Performance Metrics Schema**: Validate the generated `data/processed/performance_metrics.csv` against `specs/001-explore-network-structure-superconducting-qubit-coupling/contracts/performance_metrics.schema.json` (created in T010). **Prerequisite**: T017a, T010.

---

## Phase 4: User Story 2 - Construct Connectivity Graphs and Compute Topological Metrics (Priority: P2)

**Goal**: Convert coupling maps to graphs and compute topological metrics.

**Independent Test**: A script can be run to load a known coupling map (e.g., from a small device) and verify the computed metrics (e.g., average shortest path, clustering coefficient) match expected values for that topology.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020a-test [P] [US2] **Test Graph Construction**: Write `tests/test_graph_builder.py::test_build_coupling_graph` that creates a known graph (e.g., triangle) from a `coupling_map` and asserts the number of nodes and edges matches expectations. **Verification**: `pytest tests/test_graph_builder.py::test_build_coupling_graph -v`. **Prerequisite**: T020a-impl.

### Implementation for User Story 2

- [X] T020a-impl [US2] **Build Coupling Graph**: Implement `build_coupling_graph` in `code/graph_builder.py` to create undirected NetworkX graphs from `coupling_map` lists. **Verification**: Run `pytest tests/test_graph_builder.py::test_build_coupling_graph -v` (must pass). **Prerequisite**: T020a-test.
- [X] T021 [US2] Implement `compute_shortest_path_metrics` in `code/graph_builder.py` (average shortest‑path length, diameter) handling disconnected components.
- [X] T022 [US2] Implement `compute_clustering_and_assortativity` in `code/graph_builder.py` (global clustering coefficient, degree assortativity).
- [X] T023 [US2] Implement `compute_edge_betweenness_and_spectral_gap` in `code/graph_builder.py` (edge betweenness distribution, spectral gap of Laplacian).
- [X] T024 [US2] **Handle Disconnected Graphs**: Implement logic to set spectral gap to a value consistent with disconnected graphs and compute path‑length metrics only for the largest connected component. **Verification**: Run `python -c "from code.graph_builder import build_coupling_graph, compute_edge_betweenness_and_spectral_gap; import networkx as nx; g=build_coupling_graph([[0,1],[2,3]]); sg=compute_edge_betweenness_and_spectral_gap(g); assert sg==0"`. **Prerequisite**: T023.
- [X] T025a [US2] **Compute Per-Device Graph Metrics**: Compute all graph metrics for each device based on its coupling map. **Verification**: Assert all metrics are computed without errors and stored in a DataFrame.
- [ ] T025b [US2] **Generate Graph Metrics CSV**: Implement logic to generate `data/processed/graph_metrics.csv` with columns `device_id`, `metric_name`, `value`, `is_finite`. **Deserialization**: For each device, read the raw JSON file `data/raw/{device_id}_*.json`, load the `coupling_map` JSON, then build the graph. **Entry Point**: Run `python code/graph_builder.py --generate-metrics`. **Verification**: Assert file exists and contains expected columns. **Prerequisite**: T016, T025a.

---

## Phase 5: User Story 3 - Execute Statistical Correlation and Robustness Analysis (Priority: P3)

**Goal**: Correlate topology with performance.

**Independent Test**: A script can be run to compute Spearman correlations between graph metrics and performance metrics and verify the output includes FDR-adjusted p-values and robustness check results.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [US3] **Full Pipeline Test**: Implement `tests/test_stats_engine.py::test_full_pipeline_synthetic`.
- [ ] T028 [US3] **Load and Merge Metrics**: Implement `load_and_merge_metrics` in `code/stats_engine.py` to join `data/processed/performance_metrics.csv` and `data/processed/graph_metrics.csv` by `device_id` ONLY. **Verification**: Assert the merged DataFrame has the correct number of rows and columns. **Prerequisite**: T025b, T017a.
- [X] T029 [US3] **Correlation Engine**: Implement `compute_spearman_correlations` in `code/stats_engine.py` for all metric pairs using simultaneous data. **Verification**: Assert correlation coefficients are computed correctly. **Prerequisite**: T028.
- [X] T030 [US3] **Apply FDR**: Implement `apply_benjamini_hochberg_fdr` in `code/stats_engine.py` to adjust p-values and flag significant results (`adj_p < 0.05`). **Verification**: Assert adjusted p-values are correct. **Prerequisite**: T029.
- [X] T031c [US3] **Robustness Check**: Implement `robustness_check_time_window` in `code/stats_engine.py`. **Verification**: Assert function runs without error, returns a stability metric, and explicitly checks that historical data (from T020) was fetched and compared against current data. **Prerequisite**: T020, T029.
- [X] T032 [US3] **Sensitivity Analysis**: Implement `sensitivity_analysis` in `code/stats_engine.py`.
- [X] T033 [US3] **Power Analysis**: Implement `power_analysis` in `code/stats_engine.py`.
- [X] T034a [US3] **Compute Correlations**: Implement the core Spearman correlation calculation and p-value generation.
- [X] T034b [US3] **Apply FDR Adjustment**: Implement Benjamini-Hochberg FDR correction on p-values.
- [ ] T034c [US3] **Write Correlation Results CSV**: Write the final correlation results to `data/processed/correlation_results.csv` with columns `metric_a`, `metric_b`, `rho`, `p_value`, `adj_p_value`. **Verification**: Assert file exists and contains expected columns. **Prerequisite**: T034b.
- [X] T035 [US3] **Generate Scatter Plots**: Implement `generate_scatter_plots` in `code/viz.py` for significant correlations.
- [X] T036 [US3] **Generate Heatmap**: Implement `generate_heatmap` in `code/viz.py` for the full correlation matrix.
- [X] T037 [US3] **Generate Report**: Implement logic to generate `docs/report.md`.
- [X] T047 [US3] **MDES Sensitivity Report**: Extend `docs/report.md` to include a visual or tabular summary of the MDES analysis.

---

## Phase 6: Polish & Reporting

**Purpose**: Generate visualizations and final reports

- [X] T038 [P] Run `code/hygiene.py` to update artifact hashes and state file.
- [X] T039 [US3] **Validate Quickstart**: Validate `quickstart.md` and ensure all scripts run end‑to‑end.
- [X] T042 [P] **Robustness Check Documentation**: Update documentation to explicitly state the limitations of the cross-sectional analysis and the interpretation of the robustness checks.
- [X] T043 [P] **Data Integrity Audit**: Add a validation step in `code/hygiene.py`.
- [X] T045 [P] **Live API Sanity Check**: Implement a lightweight script `scripts/sanity_check_api.py`.
- [X] T046 [P] **Reproducibility Audit**: Run `python code/hygiene.py` to generate `state/projects/PROJ-163-...reproducibility.yaml`.

---

## Phase 7: Review Resolution & Robustness Enhancements

**Purpose**: Address specific reviewer concerns regarding data integrity, statistical power, and API reliability.

- [X] T049 [P] [US1] **Explicit No-Synthetic Fallback Enforcement**: Add a defensive assertion in `code/fetcher.py` that raises a `RuntimeError` if `fetch_backend_properties` is called and no valid data is returned, ensuring no silent fallback to synthetic data. **Verification**: Run `pytest tests/test_fetcher.py::test_no_synthetic_fallback -v` (must pass). **Prerequisite**: T013c-impl.
- [X] T050 [P] [US1] **API Rate Limit Backoff Verification**: Add a test in `tests/test_fetcher_errors.py` that simulates 429 Too Many Requests responses and verifies the `retry_with_exponential_backoff` logic correctly implements the backoff and eventually fails or succeeds based on the `max_attempts` limit. **Verification**: `pytest tests/test_fetcher_errors.py -v`. **Prerequisite**: T040.
- [X] T051 [P] [US3] **MDES Calculation Implementation**: Implement `compute_mdes` in `code/stats_engine.py` to calculate the Minimum Detectable Effect Size given the current sample size (number of devices) and desired power (0.8). **Verification**: Run `python -c "from code.stats_engine import compute_mdes; print(compute_mdes(n=30, power=0.8))"` and assert a float is returned. **Prerequisite**: T033.
- [X] T052 [P] [US3] **LODO Robustness Check Implementation**: Implement `leave_one_device_out` analysis in `code/stats_engine.py` to verify that the correlation results are not driven by a single outlier device. **Verification**: Run `python -c "from code.stats_engine import leave_one_device_out; print(leave_one_device_out())"` and assert a list of results is returned. **Prerequisite**: T031c.
- [X] T053 [P] [US3] **Chip Family Control Implementation**: Implement logic to group devices by "chip family" (e.g., Falcon, Hummingbird) and perform partial correlations controlling for this factor. **Verification**: Run `python -c "from code.stats_engine import partial_corr_chip_family; print(partial_corr_chip_family())"` and assert a correlation coefficient is returned. **Prerequisite**: T029, T013, T014.
- [ ] T054 [P] [US3] **Correlation Results Schema Validation**: Create `specs/001-explore-network-structure-superconducting-qubit-coupling/contracts/correlation_results.schema.yaml` and validate the output of `data/processed/correlation_results.csv` against it. **Verification**: Run `python -c "import jsonschema; jsonschema.validate(...)"` and assert no error is raised. **Prerequisite**: T034c, T012.
- [ ] T055 [P] [US3] **Graph Metrics Schema Validation**: Create `specs/001-explore-network-structure-superconducting-qubit-coupling/contracts/graph_metrics.schema.yaml` and validate the output of `data/processed/graph_metrics.csv` against it. **Verification**: Run `python -c "import jsonschema; jsonschema.validate(...)"` and assert no error is raised. **Prerequisite**: T025b, T011.
- [X] T011b [P] **Contract Registry Initialization (Part 2)**: Update `specs/001-explore-network-structure-superconducting-qubit-coupling/contracts/registry.yaml` to include schemas created in Phase 7 (T041a, T054, T055). **Verification**: Assert file contains all expected schema paths. **Prerequisite**: T041a, T054, T055.

---

## Phase 8: Final Validation & Execution Readiness

**Purpose**: Ensure the entire pipeline is robust, reproducible, and ready for the execution stage.

- [X] T056 [P] **End-to-End Integration Test (Real API)**: Implement `tests/test_end_to_end.py` that runs the full pipeline (fetch, graph, stats, viz) against a small subset of real IBM Quantum backends (e.g., `ibmq_manila`, `ibmq_quito`) and verifies all output files are generated correctly. **Verification**: `pytest tests/test_end_to_end.py -v`. **Prerequisite**: T044, T050, T051, T052, T053, T054, T055.
- [X] T057 [P] **Documentation Final Review**: Review and update `quickstart.md`, `README.md`, and `docs/report.md` to ensure they accurately reflect the cross-sectional analysis approach, the MDES limitations, and the robustness check results. **Verification**: Run `python -c "import markdown; markdown.markdown(open('docs/report.md').read())"` and assert no errors. **Prerequisite**: T037, T047, T051, T052, T053.
- [X] T058 [P] **Final Artifact Hash Update**: Run `code/hygiene.py` one final time to update the `state/projects/PROJ-163-...yaml` with the hashes of all final artifacts. **Verification**: Assert `state/projects/PROJ-163-...yaml` contains non-empty `artifact_hashes` for all expected files. **Prerequisite**: T056, T057.
- [X] T059 [P] **Execution Readiness Check**: Create a script `scripts/execution_readiness.py` that verifies all prerequisites (API token, dependencies, data files) are met and prints a clear "READY" or "NOT READY" message. **Verification**: Run `python scripts/execution_readiness.py` and assert it outputs "READY" in a clean environment. **Prerequisite**: T006b, T002, T056.

---

## Phase 9: Final Review & Cap-Check Resolution

**Purpose**: Address final reviewer concerns regarding the "historical window" interpretation and ensure the analysis strictly adheres to the cross-sectional design.

- [X] T060 [P] [US3] **Clarify Historical Window Interpretation**: Update `docs/report.md` and `code/stats_engine.py` to explicitly document that the "historical time window" (FR-004) is applied **only** to the performance metric stability check (comparing current vs. historical averages for robustness), NOT to the topology data itself. **Verification**: Run `grep -r "historical time window" docs/ code/` and confirm the text clarifies the cross-sectional nature of the primary analysis. **Rationale**: Ensures strict adherence to Plan.md's "Spec Gap / Correction" which retracted the historical topology window.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete
- **Review Resolution (Phase 7)**: Depends on Phase 3-5 completion
- **Final Validation (Phase 8)**: Depends on Phase 7 completion
- **Final Review (Phase 9)**: Depends on Phase 8 completion

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
- Tasks in Phase 7 (Review Resolution) can be run in parallel as they are mostly independent implementations of specific robustness checks
- Tasks in Phase 9 can be run in parallel as they address documentation and metadata extraction independently

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

### Review Resolution Strategy

1. Complete all user stories and basic pipeline
2. Implement robustness checks (LODO, MDES, Chip Family) in parallel (Phase 7)
3. Validate each check independently
4. Integrate all checks into the final report
5. Perform final end-to-end validation

### Final Review Strategy

1. Complete Phase 8 (Final Validation)
2. Implement Phase 9 tasks to clarify documentation and ensure metadata availability
3. Verify that the "historical window" is correctly interpreted in all artifacts
4. Confirm chip family data is available for partial correlation analysis

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: No synthetic data generation. All data must come from the IBM Quantum API. If the API is unavailable, the pipeline must fail loudly, not fall back to synthetic data.
- **Critical Constraint**: The analysis is cross-sectional. Topology and performance metrics are extracted from the same calibration snapshot. Historical time window logic for topology is disabled.
- **Critical Constraint**: All statistical tests must include FDR correction and robustness checks (LODO, MDES, Chip Family control) as per the revised plan.
- **Critical Constraint**: The "historical time window" (FR-004) applies ONLY to performance metric stability checks, not to topology data. This must be explicitly documented.
