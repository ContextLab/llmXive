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
- [X] T045 [P] **Live API Sanity Check**: Implement a lightweight script `scripts/sanity_check_api.py` that fetches properties for a single known device (e.g., `ibmq_manila`) to verify API connectivity and token validity BEFORE any full pipeline run. **Verification**: Script must output "OK" and print the device ID and timestamp. If it fails, the pipeline must abort. **Prerequisite**: T006a (Environment Config).
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
- [X] T004 [P] Create `code/hygiene.py` to compute `sha256sum` for all files in `data/` and update `state/projects/PROJ-163-...yaml` artifact hashes via a read-modify-write operation. **Prerequisite**: T004b.
- [X] T005 [P] Implement basic logging infrastructure in `code/__init__.py` and `code/main.py`
- [X] T006a [P] **Environment Config**: Create `code/config.py` to load IBM Quantum API tokens from environment variables (`IBMQ_TOKEN`, `IBMQ_URL`) and default settings.
- [X] T006b [P] **CI Test Fixture**: Create `tests/fixtures/mock_backend_properties.json` with deterministic mock data for one device to enable pipeline testing without live API access. **Constraint**: This fixture is ONLY for schema/structure validation. It MUST NOT be used to verify real-data logic or API connectivity.
- [X] T007 Create base data models (dataclasses) for `QubitDevice`, `GraphMetric`, `PerformanceMetric`, `CorrelationResult` in `code/models.py`
- [X] T008a [P] **Cross-Sectional Constant**: Create `code/stats_engine.py` (stub) and add constant `CROSS_SECTIONAL_MODE = True`. **Verification**: Run `python -c "from code.stats_engine import CROSS_SECTIONAL_MODE; assert CROSS_SECTIONAL_MODE is True"`.
- [X] T008b [P] **Cross-Sectional Docstring**: Add docstring to `code/stats_engine.py` explicitly stating: "Topology and performance metrics are extracted from the same calibration snapshot (simultaneous data). Historical time window logic is disabled per Plan.md Spec Gap and FR-003 resolution." Verify docstring is present.
- [X] T011 [P] **Contract Registry Initialization**: Create `specs/001-explore-network-structure-superconducting-qubit-coupling/contracts/registry.yaml` listing all schema files (T009, T041a, etc.) and their paths. **Content**:
 ```yaml
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
 **Verification**: Assert file exists and contains valid YAML with a `schemas` list. **Prerequisite**: T009 (and T041a when created).
- [X] T041a [P] **MDES Schema Definition**: Create `specs/001-explore-network-structure-superconducting-qubit-coupling/contracts/mdes_report.schema.yaml` defining the JSON schema for `MDES_report.json`. **Content**:
 ```yaml
 type: object
 properties:
 sample_size: {type: integer}
 mdes: {type: number}
 power: {type: number}
 alpha: {type: number}
 low_power_flag: {type: string, enum: ["Low Power: MDES > 0.5 (Large Effect Required)", "Adequate Power"]}
 confidence_interval: {type: array, items: {type: number}}
 required: [sample_size, mdes, power, alpha, low_power_flag, confidence_interval]
 ```
 **Verification**:
 1. Run `python -c "import yaml; data=yaml.safe_load(open('specs/001-explore-network-structure-superconducting-qubit-coupling/contracts/mdes_report.schema.yaml')); assert data['properties']['low_power_flag']['enum'] == ['Low Power: MDES > 0.5 (Large Effect Required)', 'Adequate Power']"` and assert it is valid YAML.
 2. **File Existence**: Assert that the file `specs/001-explore-network-structure-superconducting-qubit-coupling/contracts/mdes_report.schema.yaml` exists on disk.
 3. **Registry Check**: Assert that the schema is registered in `contracts/registry.yaml` (T011) by parsing the registry and confirming the path is listed.
 **Prerequisite**: T011.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Retrieve and Parse IBM Quantum Calibration Data (Priority: P1) 🎯 MVP

**Goal**: Automatically fetch the latest calibration properties for all publicly accessible IBM Quantum backends, ensuring data freshness (≤ 30 days).

**Independent Test**: A script can be run to download data for specific devices (e.g., `ibmq_manila`, `ibmq_quito`) and verify the output JSON/CSV contains valid graph adjacency lists, non-null coherence time values, and timestamps indicating data freshness.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] **Contract Test**: Write contract test for API response schema parsing in `tests/test_fetcher.py` using `jsonschema` library to validate against `specs/001-explore-network-structure-superconducting-qubit-coupling/contracts/raw_calibration.schema.yaml`. **Verification**: Assert test file exists and syntax is valid (e.g., `python -m py_compile tests/test_fetcher.py`). **Prerequisite**: T009.
- [X] T013 [US1] **Unified Fetcher**: Implement `fetch_backend_properties` in `code/fetcher.py` including:
 1. `retry_with_exponential_backoff` logic (`max_attempts=5`, `base_delay=2.0`, `timeout=30`).
 2. Handling 503 errors and malformed data (log warning "Device {id} excluded: {reason}").
 3. **Verification**: Ensure function returns `None` or raises on unrecoverable errors; no silent fallback to synthetic data. **Test**: Assert that a simulated network error raises `ConnectionError` and does not return mock data. **Prerequisite**: T009, T010.

### Implementation for User Story 1

- [X] T012 [US1] Implement `fetch_backends_list` in `code/fetcher.py` to retrieve all accessible backend names
- [X] T014 [US1] Implement `validate_data_freshness` in `code/fetcher.py` to exclude devices with data > 30 days old.
- [X] T014b [US1] **Integrate Freshness Check**: Update `fetch_backend_properties` to call `validate_data_freshness` and filter out stale devices before returning. **Verification**: Run `python -c "from code.fetcher import fetch_backend_properties; # Simulate stale data check"` (logic check).
- [X] T015a [US1] Implement `extract_topology_data` in `code/fetcher.py` to extract `coupling_map` and qubit indices from raw JSON.
- [X] T015b [US1] Implement `extract_performance_metrics` in `code/fetcher.py` to extract T1, T2, `cx` gate errors, `readout_errors`.
- [X] T016 [US1] **Save Raw Snapshots**: Implement logic to save raw JSON to `data/raw/{device_id}_{YYYYMMDD_HHMMSS}.json` using timestamp format `%Y%m%d_%H%M%S`. If multiple snapshots exist for the same device, append a unique suffix. **Entry Point**: Run `python code/fetcher.py --save-snapshots`. **Verification**: Assert: 1) File exists at expected path, 2) `sha256sum` matches entry in `state/projects/...yaml` (requires T004 completion), 3) File is non-empty. If `IBMQ_TOKEN` missing, use fixture from T006b. **Prerequisite**: T013, T004b.
- [X] T017 [US1] **Generate Processed CSV**: Implement logic to generate `data/processed/raw_calibration.csv` with columns: `device_id`, `timestamp`, `t1_mean`, `t2_mean`, `cx_error_mean`, `readout_error_mean`, `coupling_map`.
 - **Serialization**: The `coupling_map` column MUST be serialized as a JSON string (e.g., `json.dumps(map_list)`) to ensure deterministic parsing by downstream tasks.
 - **Validation**: Implement logic in `code/fetcher.py` to validate that saved raw JSON conforms to `contracts/raw_calibration.schema.yaml` (T009) before downstream processing. Assert that invalid JSON raises a `ValidationError`.
 - **JSON Validation**: **Critical**: Before writing the CSV, the task MUST explicitly validate that the `coupling_map` string is valid JSON by running `json.loads(row['coupling_map'])` on every row. If any row fails, the pipeline must abort with a clear error.
 - **Entry Point**: Run `python code/fetcher.py --generate-processed`.
 - **Verification**: Run `python -c "import pandas as pd; df=pd.read_csv('data/processed/raw_calibration.csv'); assert list(df.columns) == ['device_id', 'timestamp', 't1_mean', 't2_mean', 'cx_error_mean', 'readout_error_mean', 'coupling_map']; assert len(df) > 0 or len(df) == 0 (if no valid devices)"; import json; [json.loads(row['coupling_map']) for _, row in df.iterrows()]` to confirm valid JSON structure for all rows.
 - **Constraint**: Stale devices (from T014b) must be absent.
 - **Prerequisite**: T016, T013, T004b.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Construct Connectivity Graphs and Compute Topological Metrics (Priority: P2)

**Goal**: Transform raw coupling maps into graph structures and compute topological descriptors (average shortest-path length, clustering coefficient, edge betweenness, etc.).

**Independent Test**: A script can be run on a known graph (e.g., simple line or ring) to verify computed metrics match theoretical expectations, then applied to real device data.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Implement `build_coupling_graph` in `code/graph_builder.py` to create undirected NetworkX graphs from `coupling_map` lists
- [X] T018 [P] [US2] Unit test for graph metric calculation on synthetic graphs in `tests/test_graph_builder.py`
- [X] T019 [P] [US2] Integration test for processing real device coupling maps in `tests/test_graph_builder.py`

### Implementation for User Story 2

- [X] T021 [US2] Implement `compute_shortest_path_metrics` in `code/graph_builder.py` (average shortest-path length, diameter) handling disconnected components
- [X] T022 [US2] Implement `compute_clustering_and_assortativity` in `code/graph_builder.py` (global clustering coefficient, degree assortativity)
- [X] T023 [US2] Implement `compute_edge_betweenness_and_spectral_gap` in `code/graph_builder.py` (edge betweenness distribution, spectral gap of Laplacian)
- [X] T024 [US2] **Handle Disconnected Graphs**: Implement logic to set spectral gap to a value consistent with disconnected graphs and compute path-length metrics only for the largest connected component. **Verification**: Run `python -c "from code.graph_builder import build_coupling_graph; import networkx as nx; g = build_coupling_graph([[0,1], [2,3]]); from code.graph_builder import compute_edge_betweenness_and_spectral_gap; sg = compute_edge_betweenness_and_spectral_gap(g); assert sg == 0"`. **Prerequisite**: T023.
- [X] T025 [US2] **Generate Graph Metrics CSV**: Implement logic to generate `data/processed/graph_metrics.csv` with columns: `device_id`, `metric_name`, `value`, `is_finite`.
 - **Deserialization**: The task MUST explicitly deserialize the `coupling_map` JSON string from `data/processed/raw_calibration.csv` (T017) back into a list before graph construction. Use `json.loads(row['coupling_map'])`.
 - **Entry Point**: Run `python code/graph_builder.py --generate-metrics`.
 - **Prerequisite**: T016, T017, T020.
 - **Verification**: Assert file exists; assert columns `device_id`, `metric_name`, `value`, `is_finite` exist; assert row count > 0.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Execute Statistical Correlation and Robustness Analysis (Priority: P3)

**Goal**: Perform Spearman rank-correlation tests between graph metrics and performance indicators, apply Benjamini–Hochberg FDR correction, and conduct robustness checks.

**Independent Test**: The analysis pipeline can be run on a small synthetic dataset with known correlations to verify Spearman coefficient, p-values, and FDR correction logic.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Unit test for Spearman correlation and FDR correction in `tests/test_stats_engine.py`
- [X] T027 [P] [US3] Integration test for full pipeline with synthetic data in `tests/test_stats_engine.py`

### Implementation for User Story 3

- [X] T028 [US3] **Load and Merge with Alignment Check**: Implement `load_and_merge_metrics` in `code/stats_engine.py` to join graph metrics and performance metrics by `device_id` ONLY.
 - **Deserialization**: The task MUST explicitly deserialize the `coupling_map` JSON string from `data/processed/raw_calibration.csv` (T017) back into a list if needed for downstream logic.
 - **Data Alignment Verification**: Before merging, explicitly check that every `device_id` in the merged dataset has matching `timestamp` values for both topology and performance metrics (within a **1-hour** tolerance). If mismatched, log an error and exclude the device.
 - **Prerequisite**: T016, T017, T025. Enforce `CROSS_SECTIONAL_MODE` logic.
 - **Verification**: Assert merged DataFrame has non-zero rows and correct columns. Assert that devices with mismatched timestamps (>1 hour) are excluded.
- [X] T029 [US3] **Correlation Engine**: Implement `compute_spearman_correlations` in `code/stats_engine.py` for all metric pairs using simultaneous data. **Documentation**: Add comment: "Implements cross-sectional analysis per FR-003. Topology and performance extracted from same snapshot." **Prerequisite**: T028. **Verification**: Assert output DataFrame has columns `metric_a`, `metric_b`, `rho`, `p_value`.
- [X] T030 [US3] Implement `apply_benjamini_hochberg_fdr` in `code/stats_engine.py` to adjust p-values and flag significant results (`adj_p < 0.05`).
- [X] T041b [US3] **Cross-Device Variance Stability**: Implement `robustness_check_variance_stability` in `code/stats_engine.py` to compute the variance of correlation coefficients across device subsets as a fallback robustness metric when the Time Window API fails. **Verification**: Assert that the function returns a stability score and logs the result. **Prerequisite**: T029, T030.
- [X] T031b [US3] **Historical Window Robustness**: Implement `robustness_check_time_window` in `code/stats_engine.py`.
 1. **Attempt** to fetch performance metrics from a 30-day historical window (if API supports it) using `backend.properties(date=...)`.
 2. Compare correlation stability against the full dataset.
 3. **Constraint**: Do NOT fetch historical topology (static).
 4. **Documentation**: If API does not support historical fetches (expected) OR if the available historical data is less than a month, update `research.md` AND `docs/report.md` with EXACT text: "FR-004 Time Window check could not be performed as the IBM Quantum API does not expose historical performance states for past dates (or insufficient history). Correlation stability is assessed via LODO (T031a) and Cross-Device Variance Stability (T041b)."
 5. **Trigger Fallback**: If the API call fails or returns insufficient data (<30 days), explicitly call `robustness_check_variance_stability` (T041b) and record the 'Requirement Variance' in `research.md`.
 6. **Verification**: Assert that the function attempts the API call and logs the result (success or failure). **Prerequisite**: T029, T030. **Inputs**: `research.md`, `docs/report.md`.
- [X] T031a [US3] Implement `robustness_check_lodo` in `code/stats_engine.py` to perform leave-one-device-out (LODO) analysis and verify stability of significant correlations (|Δρ| ≤ 0.1) across subsets.
- [X] T032 [US3] Implement `sensitivity_analysis` in `code/stats_engine.py` sweeping a configurable set of p-value thresholds. Define `P_VALUE_THRESHOLDS` constant.
- [X] T033 [US3] **Power Analysis**: Implement `power_analysis` in `code/stats_engine.py` to estimate Minimum Detectable Effect Size (MDES) given sample size (N), number of tests, power=0.8, alpha=0.05, and report % CI if N < 30. **Prerequisite**: T041a (Schema must exist).
- [X] T034 [US3] **Generate Correlation Results**: Implement logic to generate `data/processed/correlation_results.csv` with columns `metric_a`, `metric_b`, `spearman_rho`, `p_value`, `adj_p_value`, `is_significant`, `is_excluded`.
 - **Prerequisite**: T031a, T031b. **Note**: T041b is a conditional fallback triggered only if T031b fails. T034 should proceed once T031a and T031b are complete. If T031b fails and T041b runs, T034 uses T041b's results.
 - **Entry Point**: Run `python code/stats_engine.py --generate-results`.
 - **Verification**: Assert file exists; assert non-zero rows; assert `adj_p_value` column exists; assert `is_significant` column exists.
- [X] T041 [US3] **Statistical Power Validation**: Enhance `power_analysis` in `code/stats_engine.py` to output a `MDES_report.json` file containing the calculated MDES for the observed sample size (N). If N < 30, the report must explicitly state "Low Power: MDES > 0.5 (Large Effect Required)" and flag results with p < 0.05 as "Exploratory Only". **Verification**: Assert `MDES_report.json` exists and contains the "Low Power" flag when N is small. **Prerequisite**: T033, T041a.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Reporting

**Purpose**: Generate visualizations and final reports

- [X] T035 [US3] Implement `generate_scatter_plots` in `code/viz.py` for significant correlations
- [X] T036 [US3] Implement `generate_heatmap` in `code/viz.py` for the full correlation matrix
- [X] T037 [US3] **Generate Report**: Implement logic to generate `docs/report.md`.
 - **Sections**: Methodology (referencing T028/T029 and `research.md`), Correlation Results, Robustness Checks (LODO and Time Window Limitation/Variance Stability), Power Analysis.
 - **Entry Point**: Run `python code/viz.py --generate-report`.
 - **Verification**: Assert `docs/report.md` exists; assert file contains string "LODO"; assert file contains string "Time Window Limitation" OR "Cross-Device Variance Stability" (depending on T031b/T041b outcome); assert `is_excluded` flag is discussed. **Prerequisite**: T034, T031b, T041b.
- [X] T038 [P] Run `code/hygiene.py` to update artifact hashes and state file. **Prerequisite**: T004b.
- [X] T039 [P] Validate `quickstart.md` and ensure all scripts run end-to-end

---

## Phase 7: Review Resolution & Robustness Enhancements

**Purpose**: Address specific reviewer concerns regarding data integrity, statistical power, and API reliability.

- [X] T040 [P] [US1] **API Rate Limit Enforcement**: Implement strict exponential backoff with jitter in `code/fetcher.py` for 429/503 errors. Add `rate_limit_handler` wrapper that tracks request timestamps per device and enforces a minimum 2-second gap between requests to the same endpoint. **Verification**: Run unit test simulating 429 response and assert retries occur with increasing delays.
- [X] T042 [US3] **Robustness Check Documentation**: Update `docs/report.md` (T037) to include a dedicated "Limitations" section. This section must explicitly detail: 1) The cross-sectional nature of the analysis (no temporal lag), 2) The inability to fetch historical performance data for the Time Window check (per T031b), and 3) The statistical power limitations of the current device sample size. **Verification**: Assert `docs/report.md` contains the string "Limitations" and the specific text regarding historical data unavailability.
- [X] T043 [US1] **Data Integrity Audit**: Add a validation step in `code/hygiene.py` that checks for `null` or `NaN` values in critical performance columns (`t1_mean`, `t2_mean`, `cx_error_mean`) in `data/processed/raw_calibration.csv`. If any are found, the script must log a WARNING and exclude those rows from downstream analysis, rather than crashing or imputing. **Verification**: Inject a row with `NaN` into the raw CSV and assert the pipeline completes with a warning and the row is excluded from `graph_metrics.csv`.

---

## Phase 8: Final Validation & Execution Readiness

**Purpose**: Ensure the entire pipeline is robust, reproducible, and ready for the execution stage. (Note: API sanity check T045 has been moved to Phase 1).

- [X] T044 [P] **End-to-End Integration Test**: Implement `tests/test_end_to_end.py` to run the full pipeline (Fetch → Graph → Stats → Report) using the mock fixture (T006b) to verify data flow and artifact generation without live API calls. **Verification**: Assert that `data/processed/` files and `docs/report.md` are generated with correct schema. **Prerequisite**: T006b, T017, T025, T034, T037.
- [ ] T046 [P] **Reproducibility Audit**: Update `code/hygiene.py` to generate a `state/projects/PROJ-163-...reproducibility.yaml` file containing the exact `git commit hash`, `requirements.txt` hash, and `python --version` used during the run. **Verification**: Assert file exists and contains non-empty `git_hash` and `python_version` fields. **Prerequisite**: T004b.
- [X] T047 [US3] **MDES Sensitivity Report**: Extend `docs/report.md` (T037) to include a visual or tabular summary of the MDES analysis (T041) explaining the "Low Power" flag implications for the observed correlations. **Verification**: Assert `docs/report.md` contains a section "Minimum Detectable Effect Size" with the MDES value and CI. **Prerequisite**: T033, T041.
- [X] T048 [P] **API Fallback & Error Handling Validation**: Implement a dedicated integration test `tests/test_fetcher_errors.py` that mocks specific API failure modes (429 Rate Limit, 503 Service Unavailable, 401 Unauthorized) and verifies the `fetcher.py` logic handles them according to T040 (backoff) and T013 (failure without synthetic fallback). **Verification**: Assert that the test suite passes when mocking these errors and that no synthetic data is generated. **Prerequisite**: T040, T013.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete
- **Review Resolution (Phase 7)**: Depends on Phase 6 completion to ensure all artifacts exist for audit and documentation updates.
- **Final Validation (Phase 8)**: Depends on all previous phases to ensure the full pipeline is ready for the execution stage.

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
- **Scientific Correction**: US3 tasks (T028, T029, T031a, T031b) must use simultaneous data (T028) and LODO robustness (T031a) per Plan.md Spec Gap and T008 constant. T031b implements the real FR-004 historical window check (performance only) or documents the API limitation and triggers T041b (Cross-Device Variance Stability) as a fallback.
- **Review Resolution**: Phase 7 tasks (T040-T043) address specific reviewer concerns regarding rate limiting, statistical power transparency, and data integrity validation. These must be completed before final project sign-off.
- **Execution Readiness**: Phase 8 tasks (T044-T048) ensure the pipeline is fully validated, reproducible, and ready for the execution stage, including end-to-end testing, MDES reporting, and explicit verification of API error handling and data alignment. API connectivity is validated early in Phase 1 (T045).

---

## Project Structure (Updated)

### Documentation (this feature)
```text
specs/001-explore-network-structure-superconducting-qubit-coupling/
├── plan.md # This file
├── research.md # Phase 0 output
├── data-model.md # Phase 1 output
├── quickstart.md # Phase 1 output
├── contracts/ # Phase 1 output
│ ├── raw_calibration.schema.yaml
│ ├── graph_metrics.schema.yaml
│ ├── correlation_results.schema.yaml
│ ├── mdes_report.schema.yaml # Added in Phase 2
│ └── registry.yaml # Added in Phase 2 (T011)
└── tasks.md # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)
```text
projects/PROJ-163-exploring-the-role-of-network-structure-/
├── code/
│ ├── __init__.py
│ ├── fetcher.py # FR-001: API fetching, freshness check
│ ├── graph_builder.py # FR-002: Graph construction, metrics
│ ├── stats_engine.py # FR-003, FR-004, FR-006, FR-007: Correlations, FDR, Power, PCA
│ ├── hygiene.py # Principle V: Checksums and state update
│ ├── viz.py # FR-005: Plot generation
│ └── main.py # Orchestration
├── data/
│ ├── raw/ # JSON snapshots from API
│ └── processed/ # CSVs for metrics and correlations
├── tests/
│ ├── test_fetcher.py # Mocked unit tests
│ ├── test_graph_builder.py
│ ├── test_stats_engine.py
│ └── test_integration_fetch.py # Live API integration test
└── requirements.txt
```

**Structure Decision**: Single project structure selected. The pipeline is linear (Fetch → Transform → Analyze → Visualize) and does not require a microservices or multi-repo architecture. The separation of `fetcher`, `graph_builder`, and `stats_engine` ensures modularity and testability.