# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — Requested task execution failed; rerun successfully: src/main.py exit=1
- **T005a** — Checked `src/loader.py` execution log and `data/raw/` contents: only 9 *.mtx* files were successfully downloaded and converted (com‑DBLP failed with 404) and no *.csv* files exist, so the required “≥ 10 files” condition is not met. The loader also never processes any Network Repository URLs. The task therefore remains incomplete.
- **T005c** — The `src/loader.py` code does implement the validator correctly (`fetch_snap_dataset` raises `RuntimeError` on HTTPError/URLError/unexpected errors, and `load_real_data` has no silent fallback). However, the task's verification requirement — simulating a 404 by altering a URL and confirming the script aborts with a clear error — has no supporting evidence: no test script, log, or execution output demonstrating the abort behavior was provided. The implementer should run a 404-simulation test (e.g., a bad URL in the dataset list) and attach the resulting error log/output as proof.
- **T005d** — the task writes platform-owned path(s) inside the project: `state/data_availability.yaml` (shadows `state/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
- **T006** — The module `src/data_models.py` exists and defines `TopologicalMetrics` and `NetworkGraph`, but it does not itself define `SimulationResult` and `RegressionModel` — it re-exports them via `from data_models import ...`, which depends on the top-level `code/data_models.py` being importable; there is no evidence (no `__init__.py`/path setup shown, no execution evidence) that `from src.data_models import NetworkGraph` actually succeeds from the project root, and this cross-module import is likely to fail. Additionally, the two `NetworkGraph` definitions (in `src/` and `code/`) diverge (graph objec
- **T007** — The current `src/utils.py` does contain a `save_json` that writes with `indent=2` and a `get_logger` wrapper, but the only execution evidence on record is the T007 test run, which FAILED (exit 2, `ImportError: cannot import name 'save_json' from 'src.utils'`), and there is no subsequent successful run demonstrating the required verification (`utils.save_json({}, "tmp.json")` creating a readable file). Additionally, the task says save_json "validates against the appropriate schema," but the implementation makes schema validation purely optional via a `schema_path` argument that defaults to None
- **T008b** — The test file `tests/test_properties.py` exists and contains three property-based tests, but **the tests cannot pass** due to critical import and implementation issues:

1. **Import Path Mismatch**: The test imports `from topology import compute_metrics` and `from simulation import check_disconnected, run_kuramoto_simulation`, expecting these modules in the Python path. However, the actual implementations are in `code/topology.py` and `code/simulation.py`. The test file's path setup (`sys.path.insert(0, str(code_dir))`) should resolve this, but the test would need to be run from the project ro
- **T009** — The task requires `python -m src.validators --self-test` to exit with code 0, confirming validators work on sample files. While the historical execution log shows the command exited with code 0, the log contains **empty stdout and stderr**, which is suspicious. More critically, the `_self_test()` function in `src/validators.py` (lines 280–298) only attempts to **load schema files from the `contracts/` directory** — it does not validate any actual JSON data files against those schemas. The function logs successful schema loading but performs no validation of sample JSON files against the loaded
- **T044** — The test file `tests/test_schema_validation.py` exists and is well-structured, but the task cannot be completed because **all four required schema files are MISSING**:

1. `network_metrics.schema.yaml` — MISSING
2. `regression_model.schema.yaml` — MISSING
3. `regression_summary.schema.yaml` — MISSING
4. `simulation_result.schema.yaml` — MISSING

The test execution log shows the parametrized test collected only 1 item and **SKIPPED** it (not passed), which occurs because the glob pattern `contracts/*.schema.yaml` found no schema files. The task explicitly requires that "every schema is exercise
- **T010** — The test file `tests/test_topology.py` exists and contains all three required test functions (`test_degree_sum_equals_twice_edges`, `test_clustering_bounds`, `test_avg_path_length_disconnected_returns_null`), but the execution evidence shows that **two of the three tests are currently failing**, which directly contradicts the task requirement.

**Specific failures:**

1. **`test_degree_sum_equals_twice_edges` FAILED**: The test expects the sum of degree_distribution values to equal `2 * num_edges` (6), but gets 4. The current implementation returns a dict mapping `node -> degree`, so summing t
- **T011** — The test file `tests/test_simulation.py` exists and contains the two required test functions (`test_ring_graph_analytical_match_pct` and `test_k_sweep_converges`), but the tests **currently fail** due to critical mismatches between the test expectations and the underlying implementation.

**Specific failures:**

1. **`SynchronizationStatus.FAILED` does not exist**: The `code/src/simulation.py` implementation attempts to use `SynchronizationStatus.FAILED`, but the enum defined in `code/data_models.py` only defines `SYNCHRONIZED`, `NOT_SYNCHRONIZED`, `DISCONNECTED`, and `ERROR`. The test executi
- **T016** — Requested task execution failed; rerun successfully: src/main.py exit=1
