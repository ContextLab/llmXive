# Tasks: Exploring the Impact of Network Structure on Synchronization in Complex Physical Systems  

**Input**: `spec.md`, `plan.md`, `contracts/`, existing research artefacts.  

The checklist follows the canonical `- [ ] T### [P?] [USx?] description …` format.  
Checked boxes (`[X]`) denote work that has already passed verification; unchecked boxes denote work that still needs to be produced or re‑produced.  Indented continuation lines spell out the exact artefact path, verification command or test, and any required scientific checks.

---

## Phase 1 – Project scaffold & quick‑start (setup)

| ID | Description |
|----|-------------|
- [X] T001 Create the standard project directory layout (`src/`, `tests/`, `data/raw/`, `data/processed/`, `results/`, `docs/`).  
   • Verify with `tree -L 2` that all folders exist.  
- [X] T002 Initialize a pinned Python environment (`requirements.txt` containing `networkx`, `numpy`, `scipy`, `pandas`, `scikit-learn`, `matplotlib`, `pytest`).  
   • Verification: `pip install -r requirements.txt` completes without errors.  
- [ ] T003 Draft a runnable quick‑start guide in `docs/quickstart.md` that shows the single command `python -m src.main --config config.yaml` and lists expected output files (`results/sim_results.json`, `results/regression_summary.json`, etc.).   <!-- FAILED-IN-EXECUTION: src/main.py exit=1 -->
   • Verification: the markdown file exists and the command runs end‑to‑end after Phase 3 is complete.  

---

## Phase 2 – Core infrastructure (foundational, blocks all user‑story work)

- [X] T004 Create `config.yaml` with deterministic seeds, synchronization threshold parameters (`r_target: 0.8`, `t_min: 100`), and default paths (`data/raw/`, `results/`).  
   • Verification: `yaml.safe_load` succeeds and contains the required keys.  

- [ ] T005a Implement `src/loader.py` to **download** real network files from the verified SNAP and Network Repository URLs listed in `plan.md`.  
   • Files are saved under `data/raw/`.  
   • Verification: after running `python -m src.loader`, `ls data/raw/*.mtx data/raw/*.csv` shows ≥ 10 files.  

- [X] T005b Compute SHA‑256 checksums for every downloaded file and write them to `data/checksums.txt` (format: `<hash>  <filename>`).  
   • Verification: `sha256sum -c data/checksums.txt` returns all OK.  

- [ ] T005c Add a lightweight validator in `src/loader.py` that raises an exception (no silent fallback) if any download fails, ensuring the runner retries on a real GPU if needed.  
   • Verification: simulate a 404 by altering a URL and confirm the script aborts with a clear error.  

- [ ] T005d After downloads, write a YAML state file `state/data_availability.yaml` with a boolean flag `regression_blocked` that is **true** when the number of raw networks is < 10.  
   • Verification: `cat state/data_availability.yaml` shows the flag correctly set.  

- [ ] T006 Create `src/data_models.py` defining the dataclasses `NetworkGraph`, `TopologicalMetrics`, `SimulationResult`, and `RegressionModel` that directly mirror the JSON schemas in `contracts/`.  
   • Verification: a simple import `from src.data_models import NetworkGraph` succeeds and `NetworkGraph.__annotations__` matches the schema.  

- [ ] T007 Provide `src/utils.py` with a `get_logger()` wrapper (already available platform‑wide) and a helper `save_json(obj, path)` that writes with `indent=2` and validates against the appropriate schema.  
   • Verification: `utils.save_json({}, "tmp.json")` creates a readable file.  

- [~] T008a Set up `pytest` configuration in `tests/conftest.py` (fixtures for temporary directories, deterministic RNG seed).  
   • Verification: `pytest -q tests/conftest.py` runs without errors.  

- [~] T008b Add generic property‑based tests in `tests/test_properties.py` (e.g., “graph connectivity invariance”, “metric bounds”).  
   • Verification: `pytest -q tests/test_properties.py` passes.  

- [~] T009 Create `src/validators.py` with functions that load a JSON file and validate it against the corresponding schema in `contracts/`.  
   • Verification: `python -m src.validators --self-test` exits with code 0, confirming validators work on sample files.  

- [~] T044 [P] Add a schema‑exercise test suite `tests/test_schema_validation.py` that loads each contract schema (`network_metrics.schema.yaml`, `regression_model.schema.yaml`, `regression_summary.schema.yaml`, `simulation_result.schema.yaml`) and validates a representative JSON instance against it using `src.validators`.  
   • Verification: `pytest -q tests/test_schema_validation.py` passes, guaranteeing every schema is exercised.  

---

## Phase 3 – User Story 1: Topological feature extraction & Kuramoto simulation (P1)

### Tests (must fail before implementation – TDD)

- [~] T010 Write unit tests for `src/topology.py` in `tests/test_topology.py` covering:  
   • `test_degree_sum_equals_twice_edges`  
   • `test_clustering_bounds` (0 ≤ C ≤ 1)  
   • `test_avg_path_length_disconnected_returns_null`.  
   • Verification: `pytest -q tests/test_topology.py` must fail until implementation is complete.  

- [~] T011 Write unit tests for `src/simulation.py` in `tests/test_simulation.py` covering:  
   • `test_ring_graph_analytical_match_pct` (≤ 5 % error)  
   • `test_k_sweep_converges`.  
   • Verification: `pytest -q tests/test_simulation.py` must fail until implementation is complete.  

- [~] T012 Write contract test for disconnected‑graph handling (expects `coupling_strength_threshold` = `null` and status = `disconnected`).  
   • Verification: `pytest -q tests/test_disconnected_handling.py` must fail until implementation is complete.  

- [~] T020 [US1] Implement a unit‑test `test_ring_graph_analytical_match_pct` that constructs a ring graph (N=200) and verifies the Kuramoto simulation threshold is within 5 % of the known analytical value.  
   • Verification: `pytest -q tests/test_simulation.py::test_ring_graph_analytical_match_pct` passes, satisfying SC‑006.  

### Implementation

- [~] T013 [US1] Implement `src/topology.py` to compute **exactly** the three required metrics (mean degree, degree variance, global clustering coefficient, average path length) using NetworkX on the **original** input graph (no BFS reduction).  
   • Output: one `NetworkMetrics` JSON per input graph saved under `data/processed/metrics_{network_id}.json`.  
   • Verification: `pytest -q tests/test_topology.py` passes and the JSON validates against `network_metrics.schema.yaml`.  

- [~] T014 [US1] Implement `src/simulation.py` with the Kuramoto model (N = 200 oscillators, RK45 integrator, `rtol=1e-6`, `atol=1e-9`). Perform a **K‑sweep** over `K ∈ [0, 5]` in increments of `0.1` to locate the synchronization robustness threshold (minimum K where `r(t) > 0.8` for `t > 100`).  
   • Output: a `SimulationResult` JSON saved under `results/sim_{network_id}.json`.  
   • Verification: `pytest -q tests/test_simulation.py` passes; JSON validates against `simulation_result.schema.yaml`.  

- [~] T015 [US1] Add a guard in `src/simulation.py` that **immediately returns** `coupling_strength_threshold = null`, `status = "disconnected"` when the input graph’s `is_connected` flag is false (no K‑sweep performed).  
   • Verification: unit test `test_disconnected_graph` (from T012) passes.  

- [ ] T016 [US1] Create orchestration script `src/main.py` that iterates over every file in `data/raw/`, calls `topology.compute_metrics()`, then `simulation.run()`, and aggregates all per‑network JSONs into a single array `results/sim_results.json`.   <!-- FAILED-IN-EXECUTION: src/main.py exit=1 -->
   • Verification: after `python -m src.main --config config.yaml`, the file `results/sim_results.json` exists, is valid JSON, and contains one entry per raw network.  

- [ ] T017b [US1] Generate a **verification package** for SC‑003:  
   1. Read `results/sim_results.json`.  
   2. Sort the underlying raw‑file list alphabetically, pick the first 5 network IDs.  
   3. Write `results/verification_report.json` with schema `{ "networks": [{ "id": str, "threshold": number|null }], "status": "ready" }`.  
   4. Write `results/manual_verification_log.csv` (headers `network_id,threshold,verified_by,timestamp`) populating the 5 rows.  
   • Verification: both files exist, CSV parses with `pandas.read_csv`, and the thresholds match those in `sim_results.json`.  

- [ ] T017c [US1] Create a human‑readable gate file `results/manual_verification_pending.md` that instructs a reviewer to inspect `manual_verification_log.csv` and confirm the r > 0.8 condition. Append `"review_pending": true` to `verification_report.json`.  
   • Verification: the markdown file exists and the JSON field is present.  

- [ ] T018 [US1] Add a strict test (`tests/test_standard_metrics_only.py`) that fails if `src/topology.py` attempts to compute any metric beyond the three required (e.g., eigenvector centrality).  
   • Verification: test passes, guaranteeing compliance with FR‑001.  

- [ ] T019 [US1][Review‑Response] (optional) Extend `src/topology.py` with a **flag‑controlled** block that can compute higher‑order motifs (triangles, 4‑node cliques) and Louvain modularity, storing results in `results/secondary_metrics.json`. These metrics are **excluded** from the primary regression model.  
   • Verification: when the flag `--extra-metrics` is passed, the JSON appears; otherwise it does not.  

---

## Phase 4 – User Story 2: Regression analysis & multicollinearity handling (P2)

- [ ] T021 [US2] After regression, run an ANOVA test on the fitted model and verify that the ANOVA p‑value is < 0.05. Record the result in `results/anova_report.json` and fail the pipeline if the condition is not met.  
   • Verification: `pytest -q tests/test_anova.py` passes and the JSON contains `anova_p_value < 0.05`.  

- [ ] T022 [US2] Validate that **all** topological predictors used in regression are derived strictly from static adjacency structure (no circularity).  
   • Verification: script `src/validate_predictors.py` scans provenance metadata; exits with non‑zero code if any predictor source is non‑static.  

- [ ] T023a [US2] Implement `fit_linear(X, y)` in `src/stats.py` returning a scikit‑learn `LinearRegression` fitted model plus R², coefficients, and p‑values (via `statsmodels`).  
   • Verification: `pytest -q tests/test_fit_linear.py` passes and returns expected statistics.  

- [ ] T023b [US2] Implement `fit_polynomial(X, y, degree=2)` returning a `PolynomialFeatures` pipeline with the same statistics as above.  
   • Verification: `pytest -q tests/test_fit_polynomial.py` passes.  

- [ ] T024 [US2] Add a VIF inspection routine in `src/stats.py`.  
   • If any predictor’s VIF > 5, **either** (a) drop the highest‑VIF predictor and re‑fit, **or** (b) fall back to Ridge regression (`alpha=1.0`).  
   • Record the remediation action (`"removed predictor X"` or `"ridge α=1.0"`).  
   • Verification: `pytest -q tests/test_vif.py` triggers a VIF > 5 scenario and checks that the remediation is logged correctly.  

- [ ] T025 [US2] Add a gating step that reads `state/data_availability.yaml`.  
   • If `regression_blocked` is true **or** the CSV has <N = 10 rows, skip regression and write `results/descriptive_stats.json` (mean, median, std, count, warning).  
   • Verification: after `python -m src.stats --mode check`, the appropriate file exists and contains a `warning_message`.  

- [ ] T026 [US2] Implement a null‑hypothesis test that flags the overall model as **significant** only if at least one predictor has `p_value < 0.05`. Write a boolean `significant` field into `results/regression_summary.json`.  
   • Verification: `pytest -q tests/test_significance_flag.py` passes and the JSON field matches expectation.  

- [ ] T027 [US2] **Enforce** regression R² > 0.6 as required by SC‑001 and Constitution Principle VII. Fail the pipeline if the condition is not met.  
   • Verification: after regression, script checks `r_squared` and aborts with clear error if ≤ 0.6.  

- [ ] T028 [US2] Add cross‑validation logic in `src/stats.py` that implements the spec‑defined conditional strategy: use Leave‑One‑Out CV when dataset size < 50, otherwise use 10‑fold CV (random_state=42). Return `{ "mean_r2": float, "std_r2": float }`.  
   • Verification: `pytest -q tests/test_crossval_logic.py` confirms the correct CV method is chosen based on dataset size.  

- [ ] T029 [US2] Write `results/cv_report.json` containing `mean_r2`, `std_r2`, `stability_flag` (true if `std_r2` < 0.1), and `robustness_pass` (true if `std_r2` < 0.1).  
   • Verification: file exists, JSON validates via `src.validators.validate_cv_report`, and flags are correct.  

- [ ] T030 [US2] Global timeout wrapper in `src/main.py` that measures total wall‑clock time; if > 6 h, writes `results/pipeline_status.json` with `{ "network_id": "<last_completed>", "duration": <seconds>, "status": "TIMEOUT" }`, otherwise `"SUCCESS"`.  
   • Verification: run pipeline with artificial delay flag; expect `pipeline_status.json` with status TIMEOUT.  

- [ ] T045 [US2] Create an independent mini‑pipeline task that samples ten real networks from `data/raw/`, runs the full metric‑computation, simulation, and regression workflow on this subset, and produces `results/mini_regression_summary.json`. This provides a self‑contained end‑to‑end test for User Story 2.  
   • Verification: after execution, the mini summary JSON exists, validates against `regression_summary.schema.yaml`, and the pipeline completes without needing the full dataset.  

- [ ] T050 [P] Implement unit test `test_ring_graph_analytical_match_pct` in `tests/test_simulation.py` that constructs a ring graph (N=200) and asserts the Kuramoto synchronization threshold is within 5 % of the analytical solution, thereby satisfying SC‑006.  
   • Verification: `pytest -q tests/test_simulation.py::test_ring_graph_analytical_match_pct` passes.  

- [ ] T051 [P] Implement unit test `test_anova_pvalue` in `tests/test_anova.py` that loads `results/regression_summary.json`, runs ANOVA via statsmodels, and asserts `anova_p_value < 0.05`, fulfilling SC‑001.  
   • Verification: `pytest -q tests/test_anova.py::test_anova_pvalue` passes and the JSON contains the required p‑value.  

---

## Phase 5 – User Story 3: Cross‑validation reporting & visualisation (P3)

- [ ] T032 [US3] Unit test `test_crossval_small_dataset` and `test_crossval_large_dataset` in `tests/test_crossval.py`. Both must verify that the conditional CV (LOOCV for <50, 10‑fold for ≥50) is performed and that the returned mean/std conform to expectations.  
   • Verification: `pytest -q tests/test_crossval.py` passes.  

- [ ] T033 [US3] Unit test `test_heatmap_file_exists` in `tests/test_viz.py`.  
   • Verification: `pytest -q tests/test_viz.py::test_heatmap_file_exists` passes and PNG size > 0.  

- [ ] T034 [US3] Implement `src/viz.py` function `generate_heatmap(df, x, y, z, out_path)` that creates a PNG heatmap of the synchronization threshold (`z`) across any two topological predictors (`x`, `y`). Save to `results/heatmap_thresholds.png`.  
   • Verification: file exists and `identify -format %m results/heatmap_thresholds.png` returns a non‑zero size.  

- [ ] T034b [US3] Implement `generate_comparison_plot(df, out_path)` that produces a bar chart of each predictor’s regression coefficient with error bars, saved as `results/comparison_plot.png`.  
   • Verification: file exists; `file results/comparison_plot.png` reports PNG format.  

- [ ] T034c [US3] Implement `generate_model_comparison_plot(df_primary, df_secondary, out_path)` that places the two models’ R² side‑by‑side in `results/model_comparison_plot.png`.  
   • Verification: file exists and PNG is non‑empty.  

- [ ] T035 [US3] Extend `src/main.py` (or a new driver `src/run_viz.py`) to automatically invoke the CV routine (T028) and then call the three visualisation functions once the regression summary is available.  
   • Verification: after a full run, all three PNG files exist.  

- [ ] T046 [US3] Add a visualization test that consumes the mini‑regression output from T045, runs the three heatmap/comparison plots on that subset, and verifies the PNG files are generated. This makes User Story 3 independently shippable.  
   • Verification: `python -m src.run_viz --input results/mini_regression_summary.json` creates the three PNGs and the test suite confirms their existence.  

---

## Phase N – Polish, robustness & documentation (cross‑cutting)

- [ ] T038 [P] Populate `docs/` with:  
   • `api_topology.md` (docstrings from `src/topology.py`)  
   • `api_simulation.md` (docstrings from `src/simulation.py`)  
   • `api_stats.md` (docstrings from `src/stats.py`)  
   • Ensure each file is non‑empty.  

- [ ] T039 Code cleanup – run `ruff check src/ tests/` and `black --check src/ tests/`; fix any reported issues.  
   • Verification: both commands exit with code 0.  

- [ ] T040 Streaming optimisation – modify `src/loader.py` to use `datasets.load_dataset(..., streaming=True)` for any raw file > 100 MB, processing it chunk‑wise for metric computation.  
   • Verification: test `tests/test_streaming.py` loads a >100 MB dummy file in streaming mode without memory overflow.  

- [ ] T041 Add edge‑case unit tests in `tests/edge_cases.py` covering:  
   • Graph with only 2 nodes (`test_n2_graph`)  
   • Graph containing self‑loops (`test_self_loops`).  
   • Verification: `pytest -q tests/edge_cases.py` passes.  

- [ ] T042 Validate the end‑to‑end pipeline by executing `python -m src.main --config config.yaml` and asserting that **all** files listed in the “Verification” column of every task exist and pass their schema checks.  
   • Verification: script `src/end_to_end_check.py` runs after pipeline and exits 0 only if every artifact is present and validates.  

- [ ] T043 Update `research.md` with a concise “Results” section that programmatically inserts the key numbers from `results/regression_summary.json` (R², significant predictors, VIF scores) and cites the corresponding figure files.  
   • Verification: script `src/update_research_md.py` runs and the inserted numbers match the JSON values.  

- [ ] T043b [P][Review‑Response] Extend the same `research.md` section with a comparative paragraph describing the secondary analysis (higher‑order metrics) and reporting its R² and p‑values, explicitly stating whether it improved predictive power over the primary model.  
   • Verification: after running `src/update_research_md.py`, the paragraph exists and values are consistent with `regression_summary.json` secondary block.  

---

## Dependency & Execution Order Summary  

| Phase | Must finish before | Parallelizable (`[P]`) |
|-------|-------------------|------------------------|
| 1 – Scaffold | – | T001, T003 |
| 2 – Core infra | Phase 1 | T005a‑d, T006‑T009, T044 |
| 3 – US 1 | Phase 2 | Tests (T010‑T012) → Implementation (T013‑T019) → Orchestration (T016‑T017c) |
| 4 – US 2 | Phase 2 & US 1 outputs | Aggregation (T022) → Gating (T025) → Regression & VIF (T023a‑c, T024) → ANOVA (T021) → CV & reporting (T028‑T029b) → Mini‑pipeline (T045) |
| 5 – US 3 | US 2 results | Visualisation (T034‑T035) → Mini‑visualisation test (T046) |
| N – Polish | All previous phases | Linting (T039), docs (T038), timeout (T030), streaming (T040), edge tests (T041), final validation (T042), manuscript update (T043‑T043b) |

*All tasks respect the specification’s functional requirements (FR‑001 – FR‑006), success criteria (SC‑001 – SC‑006), and the platform’s CPU‑first compute policy.  No synthetic data is generated; every loader fetches real network files from the verified URLs.  The pipeline is fully reproducible and ready for the verification stage.*  