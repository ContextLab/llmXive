# Tasks: Exploring the Impact of Network Topology on Heat Dissipation in 2D Materials  

**Inputs**: `spec.md`, `plan.md`, existing code base, data‑model contracts, reviewer feedback.  

The list follows the platform’s canonical task format.  Tasks are grouped by research phase, respect data‑flow dependencies, and reference the exact artifact paths they create or modify.  All tasks are currently **unchecked**; checked boxes are retained only if a verifier has already marked them complete.  

---  

## Phase 1 – Project scaffolding & first end‑to‑end run  

| Goal | Run a minimal, reproducible pipeline on a tiny real (or validated synthetic) sample and produce a result file under `data/results/`. |
|------|------------------------------------------------------------------------------------------------------------------------------------|

- [ ] **T001** [US1] Create the core project layout (directories `code/`, `data/raw/`, `data/processed/`, `results/`, `state/`, `contracts/`, `logs/`, `docs/`) and add placeholder `.gitkeep` files.  
  *Path*: `.` (project root)  

- [ ] **T002** [US1] Add a pinned `requirements.txt` with the exact library versions required for the study.  
  *Path*: `requirements.txt`  

- [ ] **T003** [US1] Create a minimal `quickstart.md` that documents how to install dependencies and run the end‑to‑end pipeline on the smallest valid dataset.  
  *Path*: `docs/quickstart.md`  

- [ ] **T004** [US1] Add a static configuration file `config.yaml` containing default values for the proximity threshold, scaling factor, the `validation_mode` flag **and** a `statistical_override` boolean to switch between fixed and lattice‑constant‑scaled thresholds.  
  *Path*: `config.yaml`  

- [ ] **T005** [US1] Implement a thin entry‑point script `code/main.py` that orchestrates the whole workflow (ingestion → graph construction → metric extraction → analysis → reporting).  
  *Path*: `code/main.py`  

- [ ] **T006** [US1] Write a unit test `tests/unit/test_end_to_end.py` that invokes `code/main.py` on a synthetic 1‑sample dataset and asserts that `data/results/end_to_end.json` is created and validates against `analysis.schema.yaml`.  
  *Path*: `tests/unit/test_end_to_end.py`  

---  

## Phase 2 – Data ingestion & graph construction (User Story 1, P1)  

| Goal | Produce a validated `TopologyGraph` JSON for every real (or synthetic) sample. |
|------|--------------------------------------------------------------------------------|

- [ ] **T010** [US1] Add the constant file `src/constants/material_lattice.yaml` containing at least graphene (0.246 nm) and MoS₂ (0.316 nm) entries.  
  *Path*: `src/constants/material_lattice.yaml`  

- [ ] **T009** [US1] Create `src/data/materials.py` that loads material‑specific lattice constants from `src/constants/material_lattice.yaml`.  
  *Path*: `src/data/materials.py`  

- [ ] **T013** [US1] Implement `src/data_ingestion/dataset_registry.py` that maintains `state/dataset_registry.json` mapping each `sample_id` to its source URL, DOI, and checksum. The registry is consulted by downstream tasks to confirm provenance.  
  *Path*: `src/data_ingestion/dataset_registry.py`  

- [ ] **T011** [US1] Implement `src/data_ingestion/fetch_materials_cloud.py` to download defect‑coordinate CSVs from Materials Cloud into `data/raw/`. The script must verify SHA‑256 checksums (recorded in `state/dataset_registry.json`) and abort on failure.  
  *Path*: `src/data_ingestion/fetch_materials_cloud.py`  

- [ ] **T012** [US1] Implement `src/data_ingestion/fetch_zenodo.py` to download defect‑coordinate CSVs from Zenodo into `data/raw/`, with the same checksum verification as T011.  
  *Path*: `src/data_ingestion/fetch_zenodo.py`  

- [ ] **T014** [US1] Implement `src/data_ingestion/loader.py` that streams any CSV/Parquet in `data/raw/`, drops rows with missing `x` or `y`, logs a warning with `row_number` and `sample_id`, and writes an audit file `data/processed/dropped_rows.csv`. The loader must raise an exception if the source file cannot be read (no silent synthetic fallback).  
  *Path*: `src/data_ingestion/loader.py`  

- [ ] **T015** [US1] Implement `src/data_ingestion/threshold.py` that computes the proximity threshold:  
  - If `config.yaml` sets `statistical_override: true`, use `threshold = lattice_constant(material_type) * scaling_factor` (default scaling = 1.0).  
  - Otherwise use the fixed baseline `BASELINE_THRESHOLD_NM = 2.5` nm.  
  The computed value is written to `state/threshold_config.json`.  
  *Path*: `src/data_ingestion/threshold.py`  

- [ ] **T016** [US1] Implement `src/graphs/constructor.py` using `scipy.spatial.cKDTree` to add an undirected edge between any two defects whose Euclidean distance ≤ computed threshold. Expose `construct_graph(coordinates: np.ndarray, threshold: float) -> networkx.Graph`.  
  *Path*: `src/graphs/constructor.py`  

- [ ] **T017** [US1] Implement `src/graphs/serializer.py` that converts a NetworkX graph into a JSON‑compatible dict matching `graph.schema.yaml` and writes it to `data/processed/graphs/{sample_id}.json`.  
  *Path*: `src/graphs/serializer.py`  

- [ ] **T018** [US1] Add integration test `tests/integration/test_graph_construction.py` that loads a tiny known CSV, runs the full ingestion‑threshold‑construction pipeline, and asserts that the resulting JSON graph contains the expected node and edge counts.  
  *Path*: `tests/integration/test_graph_construction.py`  

---  

## Phase 3 – Topological metric extraction (User Story 2, P2)  

| Goal | Enrich each `TopologyGraph` JSON with all required metrics and flags. |
|------|-----------------------------------------------------------------------|

- [ ] **T019** [US2] Implement `src/metrics/clustering.py` that computes the global clustering coefficient and the density‑normalized clustering `C / ρ` (where ρ = node_count / sample_area).  
  *Path*: `src/metrics/clustering.py`  

- [ ] **T020** [US2] Implement `src/metrics/paths_and_lcc.py` that:  
  1. Calculates the average shortest‑path length **only** on the largest connected component (returns `null` if the graph is disconnected or has zero nodes).  
  2. Sets `is_connected` flag.  
  3. Computes `lcc_fraction = |LCC| / total_nodes`.  
  *Path*: `src/metrics/paths_and_lcc.py`  

- [ ] **T021** [US2] Implement `src/metrics/percolation.py` that performs a binary‑search bisection over the interval `[0.5 nm, 10 nm]` (tolerance 0.01 nm) to find the smallest distance at which `lcc_fraction` exceeds 0.5. Store the result as `percolation_threshold`.  
  *Path*: `src/metrics/percolation.py`  

- [ ] **T022** [US2] Implement `src/metrics/zero_defect.py` that detects `node_count == 0`, sets `average_path_length: null`, adds a `zero_defects` flag to `metadata.flags`, and logs a specific warning.  
  *Path*: `src/metrics/zero_defect.py`  

- [ ] **T023** [US2] Implement `src/metrics/fully_connected.py` that detects an all‑to‑all edge set, sets `average_path_length = 1.0`, adds a `fully_connected` flag, and ensures the true value is used downstream.  
  *Path*: `src/metrics/fully_connected.py`  

- [ ] **T024** [US2] Create `src/metrics/aggregator.py` that calls the metric modules above, merges their outputs into a single dictionary conforming to `graph.schema.yaml`, and writes the enriched JSON back to `data/processed/graphs/{sample_id}.json`.  
  *Path*: `src/metrics/aggregator.py`  

- [ ] **T025** [US2] Add unit test `tests/unit/test_metrics.py` covering clustering, density‑normalized clustering, and correct handling of zero‑defect and fully‑connected cases.  
  *Path*: `tests/unit/test_metrics.py`  

---  

## Phase 4 – Statistical analysis & validation (User Story 3, P3)  

| Goal | Produce a validated `AnalysisResult` JSON, bootstrap confidence intervals, Bonferroni‑adjusted p‑values, partial‑correlation results, a sensitivity‑analysis report, and a power‑analysis report. |
|------|------------------------------------------------------------------------------------------------------------------------------------------|

- [ ] **T026** [US3] Implement `src/analysis/confounders.py` that computes partial correlations controlling for defect density (nodes per unit area) and for `material_type` (one‑hot encoded). Use the residual‑on‑residual method and return both raw and adjusted coefficients.  
  *Path*: `src/analysis/confounders.py`  

- [ ] **T027** [US3] Implement `src/analysis/dimensionality.py` that runs PCA on the four scalar topological metrics (clustering, average path length, LCC fraction, percolation threshold), retains components explaining ≥ 95 % of variance, and returns the transformed dataset.  
  *Path*: `src/analysis/dimensionality.py`  

- [ ] **T028** [US3] Implement `src/analysis/correlation.py` that, for each retained principal component, computes:  
  - Pearson and Spearman correlation coefficients with thermal conductivity.  
  - Linear regression and polynomial regressions of degrees 1 – 3, selecting the degree with the lowest 5‑fold CV MSE.  
  The function returns a list of dictionaries ready for JSON serialization.  
  *Path*: `src/analysis/correlation.py`  

- [ ] **T029** [US3] Implement `src/analysis/bootstrap.py` that performs 1 000 bootstrap resamples of the (component, conductivity) pairs, computes the 95 % confidence interval for every correlation coefficient, and attaches the interval to the corresponding `AnalysisResult`.  
  *Path*: `src/analysis/bootstrap.py`  

- [ ] **T030** [US3] Implement `src/analysis/correction.py` that applies a **fixed** Bonferroni correction (family size m = 20) to all raw p‑values, storing `adjusted_p_value = min(raw_p * 20, 1.0)`.  
  *Path*: `src/analysis/correction.py`  

- [ ] **T031** [US3] Implement `src/analysis/sensitivity.py` that re‑runs the entire pipeline for the four proximity‑threshold multipliers `[1.0, 1.5, 2.0, 2.5]` (relative to the baseline 2.5 nm). It records the primary correlation coefficient from each run, computes the standard deviation across runs, and writes `results/sensitivity_analysis.json` containing `thresholds`, `correlation_sd`, and a boolean `robustness_status` (true if SD ≤ 0.05).  
  *Path*: `src/analysis/sensitivity.py`  

- [ ] **T045** [US3] Implement `src/analysis/power.py` that computes statistical power for detecting a target effect size `r ≥ 0.3` at `α = 0.05` given the actual sample size `N`. It outputs a JSON report `results/power_analysis.json` with fields `sample_size`, `effect_size`, `alpha`, `power`, and a `recommendation` if power < 0.8.  
  *Path*: `src/analysis/power.py`  

- [ ] **T046** [US3] Add unit and integration tests (`tests/unit/test_power.py`, `tests/integration/test_full_analysis.py` updates) that verify the power‑analysis module returns sensible values and that `T034` now checks the presence of `results/power_analysis.json`.  
  *Path*: `tests/unit/test_power.py`  

- [ ] **T032** [US3] Implement `src/analysis/visualizer.py` that generates scatter plots of each raw topological metric versus thermal conductivity, overlays the selected regression line, and saves PNGs to `results/plots/metric_vs_conductivity_<metric>.png`.  
  *Path*: `src/analysis/visualizer.py`  

- [ ] **T033** [US3] Create `src/analysis/reporter.py` that aggregates all `AnalysisResult` objects, attaches the sensitivity‑analysis summary, includes flags for `validation_mode` or synthetic data, incorporates the power‑analysis report, and writes the final report to `results/analysis_report.json` (conforms to `analysis.schema.yaml`).  
  *Path*: `src/analysis/reporter.py`  

- [ ] **T034** [US3] Add integration test `tests/integration/test_full_analysis.py` that runs the complete pipeline on a small synthetic dataset with a known injected correlation (r ≈ 0.8) and asserts that:  
  1. At least one Bonferroni‑adjusted p‑value < 0.05,  
  2. The bootstrap 95 % CI contains the injected coefficient,  
  3. `results/sensitivity_analysis.json` reports `robustness_status = true`,  
  4. `results/power_analysis.json` exists and reports `power ≥ 0.5` (exploratory).  
  *Path*: `tests/integration/test_full_analysis.py`  

---  

## Phase 5 – Polish, reproducibility & hand‑off (Phase 3 of the template)  

| Goal | Ensure the repository is clean, documented, and ready for the paper‑stage hand‑off. |
|------|--------------------------------------------------------------------------------------|

- [ ] **T035** [US‑H] Update `docs/quickstart.md` to include:  
  1. How to run the pipeline in normal mode (`python code/main.py`).  
  2. How to enable synthetic‑fallback (`validation_mode: true` in `config.yaml`).  
  3. How to toggle the statistical‑override threshold (`statistical_override: true`).  
  4. Expected output locations (`data/processed/graphs/`, `results/analysis_report.json`).  
  *Path*: `docs/quickstart.md`  

- [ ] **T036** [US‑H] Run `mypy --strict` across the `src/` tree, fix any type errors, and commit the cleaned code.  
  *Path*: `src/` (type‑checked)  

- [ ] **T042** [US‑H] Implement `code/generate_synthetic.py` that creates a synthetic defect‑coordinate CSV dataset adhering to `DefectSample` schema, using a fixed random seed (`--seed 42`). This dataset is used by profiling and validation scripts.  
  *Path*: `code/generate_synthetic.py`  

- [ ] **T043** [US‑H] Add unit test `tests/unit/test_generate_synthetic.py` that verifies the synthetic generator produces the correct number of samples and deterministic output given the seed.  
  *Path*: `tests/unit/test_generate_synthetic.py`  

- [ ] **T037** [US‑H] Create a profiling script `src/utils/profile_memory.py` that streams a synthetic dataset of 50 samples × 10 k defects, records peak RAM usage, and writes `results/memory_profile.json`. The script must assert that peak RAM < 7 GB.  
  *Path*: `src/utils/profile_memory.py`  

- [ ] **T047** [US‑H] Create a runtime‑benchmark script `src/utils/runtime_benchmark.py` that runs the full pipeline on the synthetic dataset and records total wall‑clock time, asserting it is ≤ 6 hours. Results are written to `results/runtime_benchmark.json`.  
  *Path*: `src/utils/runtime_benchmark.py`  

- [ ] **T048** [US‑H] Create a random‑seed utility `src/utils/random_seed.py` exposing `set_global_seed(seed: int)` which seeds `numpy`, `random`, and any other libraries used. All stochastic modules must import and call this function at start.  
  *Path*: `src/utils/random_seed.py`  

- [ ] **T049** [US‑H] Add unit test `tests/unit/test_random_seed.py` ensuring that after calling `set_global_seed`, two successive calls to a random number generator produce identical sequences.  
  *Path*: `tests/unit/test_random_seed.py`  

- [ ] **T050** [US‑H] Implement `src/analysis/filter_missing.py` that scans the merged dataset, removes any samples where `thermal_conductivity` is null, logs the number of exclusions, and passes the filtered table to downstream analysis modules.  
  *Path*: `src/analysis/filter_missing.py`  

- [ ] **T038** [US‑H] Create a SHA‑256 state tracker `src/utils/state_tracker.py` that walks the repository, hashes every file under `data/`, `results/`, and `code/`, and writes a manifest `state/artifact_hashes.json`. This is used by the platform for reproducibility checks.  
  *Path*: `src/utils/state_tracker.py`  

- [ ] **T039** [US‑H] Add comprehensive docstrings (PEP 257 style) to all public functions in `src/`. Run `pydocstyle` and fix any violations.  
  *Path*: `src/`  

- [ ] **T040** [US‑H] Execute the full end‑to‑end pipeline (real data if available, otherwise synthetic mode) and verify that:  
  1. `results/analysis_report.json` validates against `analysis.schema.yaml`.  
  2. All plots exist under `results/plots/`.  
  3. No task logs any “fallback to synthetic data” warning unless `validation_mode` is true.  
  *Path*: `results/`  

- [ ] **T041** [US‑H] Run `src/utils/state_tracker.py` after a successful pipeline run and commit the generated `state/artifact_hashes.json` to ensure reproducibility tracking.  
  *Path*: `state/artifact_hashes.json`  

---  

### Dependency & Execution Order  

| Phase | Depends on |
|-------|------------|
| Phase 1 | none |
| Phase 2 | Phase 1 |
| Phase 3 | Phase 2 (graph JSONs) |
| Phase 4 | Phase 3 (enriched `TopologyGraph` JSONs) |
| Phase 5 | Phases 1‑4 (complete artifacts) |

Parallel execution is allowed for tasks marked `[P]` (different files, no data‑flow dependency).  

---  

### Revision notes  

- Reordered tasks to respect import and data‑registry dependencies (T010 before T009; T013 before T011, T012, T014).  
- Added missing functionality for power analysis (FR‑014, SC‑009), runtime benchmarking (SC‑004), missing‑conductivity filtering (FR‑011), random‑seed reproducibility (Principle I), and the `statistical_override` flag (FR‑008).  
- Introduced synthetic data generation (Task T042) to support profiling and validation without external data.  
- Updated `config.yaml` (T004) and `quickstart.md` (T035) to reflect new configuration options.  
- Added dedicated utility scripts and corresponding tests to ensure deterministic behavior and compliance with all success criteria.  

---  

*End of `tasks.md`.*  