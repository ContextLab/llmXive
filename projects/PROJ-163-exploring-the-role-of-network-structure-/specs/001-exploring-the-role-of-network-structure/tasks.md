# Tasks: Exploring the Role of Network Structure in Superconducting Qubit Coupling

**Input**: `spec.md`, `plan.md`, `research.md`, `data‑model.md`, contracts in `specs/001‑exploring‑network‑structure‑superconducting‑qubit‑coupling/contracts/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories)  

---

## Phase 1 – Setup & First End‑to‑End Analysis  

| Goal | Run an executable analysis on a tiny real input early. |
|------|-------------------------------------------------------|

- [ ] T001 [P] **Project Structure** – Create the directory skeleton `code/`, `data/raw/`, `data/processed/`, `tests/`, `docs/`, `state/projects/` at repository root.  
  *Verification*: `python -c "import os; dirs=['code','data/raw','data/processed','tests','docs','state/projects']; assert all(os.path.isdir(d) for d in dirs)"`.

- [ ] T002 [P] **Dependencies** – Add a pinned `requirements.txt` containing `qiskit‑ibm‑runtime`, `networkx`, `pandas`, `scipy`, `scikit‑learn`, `matplotlib`, `requests`, `pytest`, `jsonschema`.  
  *Verification*: `pip install -r requirements.txt && python -c "import importlib; [importlib.import_module(p.split('==')[0]) for p in open('requirements.txt')]"`.

- [ ] T003 [P] **Linting / Formatting** – Add `.ruff.toml` (select E,F,I) and `.black.toml` (line‑length 88).  
  *Verification*: `ruff check . && black --check .`.

- [ ] T009 [P] **Raw Calibration Schema** – Create `specs/001‑exploring‑network‑structure‑superconducting‑qubit‑coupling/contracts/raw_calibration.schema.json` exactly as defined in the specification.  
  *Verification*: `python -c "import json; json.load(open('specs/001‑exploring‑network‑structure‑superconducting‑qubit‑coupling/contracts/raw_calibration.schema.json'))"`.

- [ ] T010 [P] **Performance Metrics Schema** – Create `specs/001‑exploring‑network‑structure‑superconducting‑qubit‑coupling/contracts/performance_metrics.schema.json` with the fields `device_id`, `timestamp`, `t1_mean`, `t2_mean`, `cx_error_mean`, `readout_error_mean`, `chip_family`.  
  *Verification*: `python -c "import json; json.load(open('specs/001‑exploring‑network‑structure‑superconducting‑qubit‑coupling/contracts/performance_metrics.schema.json'))"`.

- [ ] T011 [P] **Graph Metrics Schema** – Create `specs/001‑exploring‑network‑structure‑superconducting‑qubit‑coupling/contracts/graph_metrics.schema.json` (fields `device_id`, `metric_name`, `value`, `is_finite`).  
  *Verification*: `python -c "import json; json.load(open('specs/001‑exploring‑network‑structure‑superconducting‑qubit‑coupling/contracts/graph_metrics.schema.json'))"`.

- [ ] T012 [P] **Correlation Results Schema** – Create `specs/001‑exploring‑network‑structure‑superconducting‑qubit‑coupling/contracts/correlation_results.schema.json` (fields `metric_a`, `metric_b`, `rho`, `p_value`, `adj_p_value`).  
  *Verification*: `python -c "import json; json.load(open('specs/001‑exploring‑network‑structure‑superconducting‑qubit‑coupling/contracts/correlation_results.schema.json'))"`.

- [ ] T011a [P] **Contract Registry (Part 1)** – Create `specs/001‑exploring‑network‑structure‑superconducting‑qubit‑coupling/contracts/registry.yaml` listing the four schema files above.  
  *Verification*: `python -c "import yaml, sys; yaml.safe_load(open('specs/001‑exploring‑network‑structure‑superconducting‑qubit‑coupling/contracts/registry.yaml'))"`.

---

## Phase 2 – Foundational (Blocking)  

| Goal | Core infrastructure that must exist before any user‑story work. |
|------|-----------------------------------------------------------------|

- [ ] T004b [P] **State File Init** – Create `state/projects/PROJ‑163‑exploring‑the‑role‑of‑network‑structure‑-.yaml` with empty `artifact_hashes`.  
  *Verification*: `python -c "import yaml; d=yaml.safe_load(open('state/projects/PROJ‑163‑exploring‑the‑role‑of‑network‑structure‑-.yaml')); assert isinstance(d.get('artifact_hashes'), dict)"`.

- [ ] T004 [P] **Hygiene & Reproducibility** – Implement `code/hygiene.py` to (1) SHA‑256 all files under `data/`, (2) record git commit, (3) hash `requirements.txt`, (4) capture Python version, and write `state/projects/PROJ‑163‑…reproducibility.yaml`.  
  *Verification*: `python code/hygiene.py && test -f state/projects/PROJ‑163‑…reproducibility.yaml`.

- [ ] T005a [P] **Logging Config** – Add `code/logging_config.py` exposing `get_logger(name)` returning a JSON‑formatted logger with a file handler.  
  *Verification*: `python -c "from code.logging_config import get_logger; assert get_logger('test')"`.

- [ ] T005b [P] **Root Logger Setup** – Update `code/main.py` to import `get_logger` and initialise a console logger.  
  *Verification*: `python code/main.py --help` runs without import errors.

- [ ] T006a [P] **Env Config** – Add `code/config.py` that loads `IBMQ_TOKEN` and `IBMQ_URL` from environment, raising a clear `RuntimeError` if missing.  
  *Verification*: `python -c "from code.config import load_config; load_config()"` fails with informative message when env vars are absent.

- [ ] T006b [P] **Token Validation Script** – Create `scripts/validate_token.py` that attempts a connection via `qiskit_ibm_runtime` and exits 1 with “ERROR: Invalid or missing IBMQ_TOKEN” on failure.  
  *Verification*: Run script with no token → exit 1 and message; with a valid token → exit 0.

- [ ] T007a [P] **Data Models (Part 1)** – Define `QubitDevice` and `GraphMetric` dataclasses in `code/models.py`.  
  *Verification*: `python -c "from code.models import QubitDevice, GraphMetric; assert hasattr(QubitDevice,'device_id')"`.

- [ ] T007b [P] **Data Models (Part 2)** – Extend `code/models.py` with `PerformanceMetric` and `CorrelationResult` dataclasses.  
  *Verification*: `python -c "from code.models import PerformanceMetric, CorrelationResult; assert hasattr(CorrelationResult,'rho')"`.

- [ ] T008a [P] **Cross‑Sectional Flag** – Add constant `CROSS_SECTIONAL_MODE = True` to `code/stats_engine.py`.  
  *Verification*: `python -c "from code.stats_engine import CROSS_SECTIONAL_MODE; assert CROSS_SECTIONAL_MODE"`.

- [ ] T008b [P] **Cross‑Sectional Docstring** – Add a module‑level docstring to `code/stats_engine.py` stating that topology and performance are taken from the same snapshot and that historical topology lag is disabled.  
  *Verification*: `grep -q "same snapshot" code/stats_engine.py`.

- [ ] T013 [P] **Chip‑Family Extraction** – Implement `extract_chip_family(backend_name, properties)` in `code/fetcher.py` returning strings like “Falcon”, “Hummingbird”, or “Unknown”.  
  *Verification*: `python -c "from code.fetcher import extract_chip_family; assert extract_chip_family('ibmq_falcon_16',{})=='Falcon'"`.

- [ ] T014 [P] **Chip‑Family Integration** – Extend `extract_performance_metrics` in `code/fetcher.py` to include the `chip_family` field in its output dicts.  
  *Verification*: Run a mock fetch and assert the dict contains `chip_family`.

- [ ] T018 [P] **Historical Performance Fetcher** – Implement `fetch_historical_performance_data()` in `code/fetcher.py` that pulls performance snapshots for the last 30 days for all public backends.  
  *Verification*: Function returns a non‑empty list of dicts containing `timestamp`.

- [ ] T019 [P] **Historical Data Storage** – Save each historical snapshot to `data/historical/{device_id}_{YYYYMMDD}.json`.  
  *Verification*: After running the fetcher, at least one file exists under `data/historical/`.

- [ ] T020 [P] **Historical Data Processor** – Implement `process_historical_data()` in `code/fetcher.py` to aggregate all JSON files under `data/historical/` into a single CSV `data/processed/historical_performance_metrics.csv` with columns `device_id`, `date`, `t1_mean`, `t2_mean`, `cx_error_mean`, `readout_error_mean`, `chip_family`.  
  *Verification*: Running the function creates the CSV and the file validates against `performance_metrics.schema.json`.

- [ ] T021b [P] **Cross‑Sectional Enforcement** – Refactor `code/stats_engine.py` to raise `RuntimeError` if any call attempts to use a topology lag (e.g., a parameter named `historical_topology`).  
  *Verification*: Unit test passes when the error is raised for illegal usage.

---

## Phase 3 – User Story 1: Retrieve & Parse IBM Quantum Calibration Data (US1)

| Goal | Fetch the latest calibration data for all accessible back‑ends, enforce freshness, and persist raw / processed artefacts. |
|------|-----------------------------------------------------------------------------------------------------------------------------------|

- [ ] T010b [P] [US1] **Contract Test (Raw Schema)** – Add `tests/test_fetcher.py` that validates API responses against `raw_calibration.schema.json` using `jsonschema`.  
  *Verification*: `pytest tests/test_fetcher.py::test_schema_validation -q` passes.

- [ ] T013a-test [P] [US1] **Retry‑Backoff Test** – Mock `requests.get` to raise `ConnectionError` twice then succeed; assert exponential delays (2 s, 4 s, 8 s).  
  *Verification*: `pytest tests/test_fetcher.py::test_retry_with_exponential_backoff -q` passes.

- [ ] T013b-test [P] [US1] **Error‑Handling Test** – Mock a 503 response; verify the fetcher logs a warning and excludes the device.  
  *Verification*: `pytest tests/test_fetcher.py::test_fetch_backend_properties_error -q` passes.

- [ ] T013c-test [P] [US1] **No‑Synthetic‑Fallback Test** – Mock total API failure; ensure the fetcher raises `RuntimeError` rather than returning synthetic data.  
  *Verification*: `pytest tests/test_fetcher.py::test_no_synthetic_fallback -q` passes.

- [ ] T012b [US1] **Fetch Backend List** – Implement `fetch_backends_list()` in `code/fetcher.py` to return a list of public backend names via the IBM Quantum provider.  
  *Verification*: Running the function yields a non‑empty list of strings.

- [ ] T013a-impl [US1] **Retry Wrapper** – Add `retry_with_exponential_backoff(func, max_attempts=5, base_delay=2.0)` in `code/fetcher.py`.  
  *Verification*: Unit tests above succeed.

- [ ] T013b-impl [US1] **Backend Property Fetcher** – Implement `fetch_backend_properties(backend_name)` that returns the JSON payload, logs and excludes devices on 503 or malformed data.  
  *Verification*: Integration test passes.

- [ ] T013c-impl [US1] **Synthetic‑Fallback Guard** – Ensure `fetch_backend_properties` raises `RuntimeError` if no valid data is obtained.  
  *Verification*: `test_no_synthetic_fallback` passes.

- [ ] T014b [US1] **Validate Data Freshness** – Implement `validate_data_freshness(calibration_timestamp)` that returns `True` only if the timestamp is ≤ 30 days old; otherwise logs and discards.  
  *Verification*: Simulated stale timestamp leads to exclusion.

- [ ] T014c [US1] **Integrate Freshness Check** – Update `fetch_backend_properties` to call `validate_data_freshness` before returning data.  
  *Verification*: Running the fetcher on a stale mock returns no entry.

- [ ] T015a [US1] **Extract Topology Data** – Implement `extract_topology_data(raw_json)` returning the `coupling_map` list and qubit indices.  
  *Verification*: Unit test confirms correct extraction from a sample payload.

- [ ] T015b [US1] **Extract Performance Metrics** – Implement `extract_performance_metrics(raw_json)` returning a dict with `t1_mean`, `t2_mean`, `cx_error_mean`, `readout_error_mean`.  
  *Verification*: Unit test validates numeric outputs.

- [ ] T016 [US1] **Save Raw Snapshots** – Add CLI flag `--save-snapshots` to `code/fetcher.py`; for each backend, write `data/raw/{device_id}_{YYYYMMDD_HHMMSS}.json`.  
  *Verification*: After execution, at least one file exists; its SHA‑256 appears in `state/projects/…yaml`.

- [ ] T017a [US1] **Generate Performance Metrics CSV** – Read all raw JSON files, compute per‑device averages, and write `data/processed/performance_metrics.csv` with columns `device_id`, `timestamp`, `t1_mean`, `t2_mean`, `cx_error_mean`, `readout_error_mean`, `chip_family`.  
  *Verification*: CSV exists, non‑empty, and conforms to `performance_metrics.schema.json`.

- [ ] T017b [US1] **Validate Performance Metrics CSV** – Add a script `scripts/validate_performance_csv.py` that loads the CSV and validates each row against `performance_metrics.schema.json`.  
  *Verification*: Running the script exits 0 with no validation errors.

---

## Phase 4 – User Story 2: Construct Connectivity Graphs & Compute Topological Metrics (US2)

| Goal | Turn coupling maps into undirected graphs and compute the full suite of topological descriptors. |
|------|------------------------------------------------------------------------------------------------|

- [ ] T020a-test [P] [US2] **Graph Construction Test** – Verify that `build_coupling_graph([[0,1],[1,2]])` yields a NetworkX graph with 3 nodes and 2 edges.  
  *Verification*: `pytest tests/test_graph_builder.py::test_build_coupling_graph -q` passes.

- [ ] T020a-impl [US2] **Build Coupling Graph** – Implement `build_coupling_graph(coupling_map)` in `code/graph_builder.py` returning an undirected `networkx.Graph`.  
  *Verification*: Unit test passes.

- [ ] T021a [US2] **Compute Shortest‑Path Metrics** – Implement `compute_shortest_path_metrics(G)` returning average shortest‑path length and diameter, handling disconnected graphs by operating on the largest connected component.  
  *Verification*: Example on a disconnected graph returns correct values and `is_finite=False` where appropriate.

- [ ] T022 [US2] **Compute Clustering & Assortativity** – Implement `compute_clustering_and_assortativity(G)` returning global clustering coefficient and degree assortativity.  
  *Verification*: Unit test on a known graph matches NetworkX reference values.

- [ ] T023 [US2] **Compute Edge Betweenness & Spectral Gap** – Implement `compute_edge_betweenness_and_spectral_gap(G)` returning the mean edge betweenness and the Laplacian spectral gap (0 for disconnected graphs).  
  *Verification*: Test on a two‑component graph asserts spectral gap = 0.

- [ ] T024 [US2] **Handle Disconnected Graphs** – Ensure that when `G` is disconnected, `spectral_gap` is set to 0 and path‑length metrics are computed only on the largest component.  
  *Verification*: Manual check as described in the verification of T023.

- [ ] T025a [US2] **Per‑Device Graph Metrics** – Loop over all raw JSON files, build each device’s graph, compute all metrics above, and store results in a pandas DataFrame.  
  *Verification*: DataFrame contains one row per `(device_id, metric_name)` pair without NaNs.

- [ ] T025b [US2] **Generate Graph Metrics CSV** – Write the DataFrame to `data/processed/graph_metrics.csv` with columns `device_id`, `metric_name`, `value`, `is_finite`.  
  *Verification*: CSV exists and validates against `graph_metrics.schema.json`.

---

## Phase 5 – User Story 3: Statistical Correlation & Robustness Analysis (US3)

| Goal | Correlate topology descriptors with performance indicators, apply FDR, and run robustness checks. |
|------|---------------------------------------------------------------------------------------------------|

- [ ] T027 [US3] **Full Pipeline Synthetic Test** – `tests/test_stats_engine.py::test_full_pipeline_synthetic` runs the entire stats pipeline on a tiny synthetic dataset and checks that all output files are created.  
  *Verification*: Test passes.

- [ ] T029 [US3] **Load & Merge Metrics** – Implement `load_and_merge_metrics(perf_path, graph_path)` in `code/stats_engine.py` that reads the two CSVs and merges on `device_id`.  
  *Verification*: Merged DataFrame has expected shape when both inputs exist.

- [ ] T030 [US3] **Spearman Correlation Engine** – Implement `compute_spearman_correlations(df)` producing a DataFrame with columns `metric_a`, `metric_b`, `rho`, `p_value`.  
  *Verification*: Known toy data yields the correct Spearman ρ.

- [ ] T031c [US3] **Benjamini‑Hochberg FDR** – Implement `apply_benjamini_hochberg_fdr(df, alpha=0.05)` adding `adj_p_value` and `is_significant` columns.  
  *Verification*: Adjusted p‑values match manual calculation on a small example.

- [ ] T032 [US3] **Time‑Window Robustness Check** – Implement `robustness_check_time_window()` that compares current performance metrics to the 30‑day historical aggregates (produced by T020) and returns a stability score.  
  *Verification*: Function runs without error and returns a float between 0 and 1.

- [ ] T033 [US3] **Leave‑One‑Device‑Out (LODO) Check** – Implement `leave_one_device_out(df)` returning a list of correlation results each computed with one device omitted.  
  *Verification*: Length of result list equals number of devices.

- [ ] T034a [US3] **Core Spearman Calculation** – Compute correlation coefficients and raw p‑values for every `(graph_metric, performance_metric)` pair.  
  *Verification*: Results stored in an intermediate DataFrame.

- [ ] T034b [US3] **FDR Adjustment** – Apply BH‑FDR to the intermediate results (same as T031c).  
  *Verification*: `adj_p_value` column populated.

- [ ] T034c [US3] **Write Correlation Results CSV** – Persist the final DataFrame to `data/processed/correlation_results.csv` respecting the schema.  
  *Verification*: CSV exists, non‑empty, and validates against `correlation_results.schema.json`.

- [ ] T035 [US3] **Scatter Plot Generation** – Implement `generate_scatter_plots(df, out_dir)` in `code/viz.py` for each significant correlation pair, saving PNGs to `docs/figures/`.  
  *Verification*: At least one PNG created for a significant pair.

- [ ] T036 [US3] **Correlation Heatmap** – Implement `generate_heatmap(df, out_path)` producing a matrix heatmap of all ρ values.  
  *Verification*: Heatmap PNG saved.

- [ ] T037 [US3] **Report Generation** – Create `docs/report.md` that programmatically inserts tables of significant correlations, MDES analysis (see T051), and robustness summaries.  
  *Verification*: Markdown file renders without missing placeholders.

- [ ] T047 [US3] **MDES Summary** – Extend `docs/report.md` with a table visualising the Minimum Detectable Effect Size (computed by T051).  
  *Verification*: Table appears with numeric MDES.

- [ ] T054 [US3] **Correlation Results Schema Validation** – Add a script `scripts/validate_correlation_schema.py` that loads `correlation_results.csv` and validates each row against `correlation_results.schema.json`.  
  *Verification*: Script exits 0 on the current CSV.

- [ ] T055 [US3] **Graph Metrics Schema Validation** – Add `scripts/validate_graph_schema.py` that validates `graph_metrics.csv` against its schema.  
  *Verification*: Script exits 0 on the current CSV.

---

## Phase 6 – Polishing & Reproducibility  

| Goal | Final artefacts, documentation, and reproducibility checks. |
|------|-------------------------------------------------------------|

- [ ] T038 [P] **Artifact Hash Update** – Run `code/hygiene.py` to refresh all SHA‑256 hashes in the state file.  
  *Verification*: `state/projects/…yaml` now contains non‑empty `artifact_hashes`.

- [ ] T039 [US3] **Quickstart Validation** – Verify that `quickstart.md`’s command (`python -m proj.run`) executes end‑to‑end and produces all expected output files.  
  *Verification*: Running the command on a fresh runner succeeds.

- [ ] T042 [P] **Robustness Documentation** – Update `docs/report.md` to clearly state that the primary analysis is cross‑sectional and that the “historical time window” applies only to performance‑metric stability checks.  
  *Verification*: `grep -q "cross‑sectional" docs/report.md`.

- [ ] T043 [P] **Data Integrity Audit** – Extend `code/hygiene.py` to recompute checksums of all CSV artefacts and log any mismatches.  
  *Verification*: Script reports “All data integrity checks passed”.

- [ ] T045 [P] **Live API Sanity Check** – Add `scripts/sanity_check_api.py` that performs a lightweight fetch of a single backend and prints its `device_id` and timestamp.  
  *Verification*: Script runs without exception.

- [ ] T046 [P] **Reproducibility Audit** – Re‑run `code/hygiene.py` and confirm `state/projects/…reproducibility.yaml` contains `git_hash`, `requirements_hash`, and `python_version`.  
  *Verification*: All three fields are non‑empty strings.

---

## Phase 7 – Review Resolution & Additional Robustness  

| Goal | Address reviewer concerns and add extra robustness analyses. |
|------|--------------------------------------------------------------|

- [ ] T049 [P] [US1] **No‑Synthetic‑Fallback Enforcement** – Add a defensive assertion in `code/fetcher.py` that raises `RuntimeError` if no valid data is returned.  
  *Verification*: Test `test_no_synthetic_fallback` passes.

- [ ] T050 [P] [US1] **Rate‑Limit Backoff Test** – Add `tests/test_fetcher_errors.py::test_rate_limit_backoff` that simulates 429 responses and checks exponential backoff behavior.  
  *Verification*: Test passes.

- [ ] T051 [P] [US3] **MDES Calculation** – Implement `compute_mdes(n, power=0.8, alpha=0.05)` in `code/stats_engine.py` returning the minimum detectable Spearman ρ.  
  *Verification*: `python -c "from code.stats_engine import compute_mdes; print(compute_mdes(30))"` prints a float.

- [ ] T052 [P] [US3] **LODO Robustness Implementation** – Implement `leave_one_device_out(df)` (already in T033) and ensure it records whether any single device drives a result to significance.  
  *Verification*: Function returns a dict with a `max_influence` flag.

- [ ] T053 [P] [US3] **Chip‑Family Partial Correlation** – Implement `partial_corr_chip_family(df)` that computes partial Spearman correlations controlling for `chip_family`.  
  *Verification*: Returns a DataFrame with `partial_rho` column.

- [ ] T011b [P] **Contract Registry (Part 2)** – Update `registry.yaml` to also list `mdes_report.schema.yaml`, `correlation_results.schema.yaml`, and `graph_metrics.schema.yaml`.  
  *Verification*: Registry file contains all five schema paths.

---

## Phase 8 – Final Validation & Execution Readiness  

| Goal | Verify the whole pipeline works on real IBM Quantum data and is ready for the execution stage. |
|------|------------------------------------------------------------------------------------------------|

- [ ] T056 [P] **End‑to‑End Integration Test (Real API)** – `tests/test_end_to_end.py` runs the full pipeline on a small subset of public back‑ends (`ibmq_manila`, `ibmq_quito`) and checks that every artefact (`performance_metrics.csv`, `graph_metrics.csv`, `correlation_results.csv`, figures, report) is produced.  
  *Verification*: Test passes on CI.

- [ ] T057 [P] **Documentation Final Review** – Ensure `quickstart.md`, `README.md`, and `docs/report.md` accurately describe the cross‑sectional design, MDES limits, and robustness checks.  
  *Verification*: Manual review (scripted check for presence of key headings).

- [ ] T058 [P] **Final Artifact Hash Update** – Run `code/hygiene.py` once more to capture final hashes.  
  *Verification*: State file contains entries for all CSVs, PNGs, and the report.

- [ ] T059 [P] **Execution Readiness Script** – Add `scripts/execution_readiness.py` that verifies (1) `IBMQ_TOKEN` present, (2) required Python packages installed, (3) all data files exist, and prints “READY” or “NOT READY”.  
  *Verification*: Running the script in a clean environment prints “READY”.

---

## Phase 9 – Final Review  

| Goal | Close the loop on the “historical window” interpretation and ensure all documentation reflects the agreed design. |
|------|------------------------------------------------------------------------------------------------------------------------|

- [ ] T060 [P] **Clarify Historical Window Interpretation** – Update `docs/report.md` and the docstring in `code/stats_engine.py` to state explicitly that the historical‑window logic is used **only** for performance‑metric stability checks (FR‑004) and **not** for topology data.  
  *Verification*: `grep -n "historical time window" -r docs/ code/` shows the clarified wording and no contradictory statements.

--- 

*All tasks above follow the canonical `- [ ] T### [P?] [USx?] description …` format, reference exact artifact paths, and include indented verification steps. Pending tasks (unchecked) are those that currently lack a verifiable artefact; completing them will satisfy the remaining verification failures identified by the independent reviewer.*
