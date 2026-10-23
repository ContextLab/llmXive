# Tasks: Exploring the Impact of Network Topology on Heat Dissipation in 2D Materials

**Input**: Design documents from `/specs/001-network-topology-heat-dissipation/`  
**Prerequisites**: `plan.md` (required), `spec.md` (required for user stories), `research.md`, `data-model.md`, `contracts/`

**Tests**: The examples below include test tasks. Tests are OPTIONAL – only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

---

## Phase 1: Setup and first end‑to‑end analysis

- [ ] T001 Create the project structure (`src/`, `tests/`, `data/raw/`, `data/processed/`, `results/`, `state/`, `contracts/`, `logs/`, `docs/`). Initialise `requirements.txt`, `config.yaml`, and `pyproject.toml`.
- [ ] T002a [P] Create `requirements.txt` with pinned versions: `networkx>=3.2`, `pandas>=2.2`, `numpy>=1.26`, `scipy>=1.12`, `scikit-learn>=1.4`, `matplotlib>=3.8`, `seaborn>=0.13`, `pyyaml>=6.0`, `jsonschema>=4.22`.
- [ ] T002b [P] Install dependencies via `pip install -r requirements.txt`.
- [ ] T003 [P] Add linting/formatting configuration (`.ruff.toml`, `pyproject.toml` with Black settings).  
  **Deliverables**: `.ruff.toml`, `pyproject.toml`.
- [ ] T004 [P] Initialise directory hierarchy and add `.gitkeep` files (`data/raw`, `data/processed`, `results`, `state`, `contracts`, `logs`, `docs`, `src`, `src/data`, `src/graphs`, `src/metrics`, `src/analysis`, `src/utils`, `tests/unit`, `tests/integration`, `tests/contract`).
- [ ] T005 [P] Add constant files:  
  - `src/constants/material_lattice.yaml` (graphene 0.246 nm, placeholder for MoS₂)  
  - `src/constants/lattice_resistance.yaml` (`R_lattice: 1.2e-4 K/W`)  
  - `src/constants/config_defaults.py` (`BASELINE_THRESHOLD_NM = 2.0`, `VALIDATION_MODE_DEFAULT = False`).
- [ ] T005b [P] Populate `src/constants/material_lattice.yaml` with verified MoS₂ lattice constant (≈ 0.316 nm) and add error handling if missing.  
  **Deliverable**: Updated `src/constants/material_lattice.yaml`.
- [ ] T006a [P] Create `logging.conf` with format `%(asctime)s - %(name)s - %(levelname)s - %(message)s` and log file `logs/pipeline.log`.
- [ ] T006b [P] Implement `src/utils/logger.py` exposing `get_logger()`.
- [ ] T007a [P] Add `contracts/dataset.schema.yaml` (defect‑coordinate schema).  
- [ ] T007b [P] Add `contracts/graph.schema.yaml` (topology‑graph schema).  
- [ ] T007c [P] Add `contracts/analysis.schema.yaml` (analysis‑result schema).  
- [ ] T008a [P] Implement `src/utils/checksum.py` with function `calculate_sha256(file_path: str) -> str`.  
- [ ] T008b [P] Add unit test `tests/unit/test_checksum.py` verifying correct SHA‑256 output for a known file.  
- [ ] T009a [P] Implement `src/data/materials.py` to load lattice constants from `src/constants/material_lattice.yaml`.  
- [ ] T009b [P] Add test `tests/unit/test_materials.py` confirming constants load correctly.  

---

## Phase 2: Foundational (blocking prerequisites)

- [ ] T012a [P] Implement `src/data_ingestion/verify_data.py` to check for the existence of paired real datasets; writes `state/data_status.json` (`data_found`, `is_unpaired`). Depends on T043/T044.  
- [ ] T012b [P] Implement `src/utils/data_gap_report.py` that reads `state/data_status.json` and, if no data, writes `results/data_gap_report.json` describing the limitation.  
- [ ] T043 [P] Implement `src/data_ingestion/fetch_materials_cloud.py` to download defect‑coordinate CSVs from Materials Cloud into `data/raw/materials_cloud_{sample_id}.csv`. On failure, log error and set `data_found: false` in `state/data_status.json`.  
- [ ] T044 [P] Implement `src/data_ingestion/fetch_zenodo.py` to download CSVs from Zenodo into `data/raw/zenodo_{sample_id}.csv`. On failure, log error and set `data_found: false` in `state/data_status.json`.  
- [ ] T045 [P] Implement `src/data_ingestion/dataset_registry.py` maintaining `state/dataset_registry.json` (mapping `sample_id` → source URL, DOI, checksum). Halts scientific analysis if no verified source exists.  
- [ ] T012c [P] Implement `src/orchestration/fallback_orchestrator.py` that reads `state/data_status.json`; if `data_found` is false, sets `validation_mode: true` and `fallback_mode: synthetic` in both `state/data_status.json` and `config.yaml`; otherwise clears those flags.  

---

## Phase 3: User Story 1 – Data Ingestion & Graph Construction (Priority P1)

- [ ] T010 [P] Unit test `tests/unit/test_data_ingestion.py` for coordinate parsing & missing‑value handling.  
- [ ] T011 [P] Integration test `tests/integration/test_graph_construction.py` verifying edge creation at a known threshold.  
- [ ] T012 [P] Contract test `tests/contract/test_graph_schema.py` validating serialized graphs against `graph.schema.yaml`.  
- [ ] T013 [P] Implement `src/data_ingestion/loader.py` to stream CSV/Parquet, drop rows with missing `x`/`y`, log warnings, and write a dropped‑row audit `data/processed/dropped_rows.csv`. Honors `validation_mode` (synthetic generation) and depends on T012c, T043, T044.  
- [ ] T014 [P] Implement `src/data_ingestion/threshold.py` to compute the proximity threshold:  
  - Retrieves material‑specific lattice constant via `src/data/materials.py`.  
  - Uses `statistical_override` flag from `config.yaml` (default False).  
  - If override active → `threshold = lattice_constant * scaling_factor` (default scaling 1.0).  
  - Else → fixed `BASELINE_THRESHOLD_NM` (2.5 nm).  
  - Writes `state/threshold_config.json`. Depends on T005, T009a, T005b.  
- [ ] T015 [P] Implement `src/graphs/constructor.py` using `scipy.spatial.cKDTree` to add edges for all defect pairs within the computed threshold. Exposes `construct_graph(coordinates, threshold)`.  
- [ ] T016 [P] Implement `src/graphs/serializer.py` converting a NetworkX graph to a JSON‑compatible dict conforming to `graph.schema.yaml`; saves to `data/processed/graphs/{sample_id}.json`. Depends on T015.  
- [ ] T017 [P] Implement `src/data_ingestion/generate_synthetic.py` (seeded, version‑controlled) that creates a synthetic `DefectSample` CSV when `validation_mode: true`. Updates `state/data_status.json` (`fallback_mode: synthetic`). Depends on T012c.  
- [ ] T017a [P] Add utility `src/utils/validation_mode_flag.py` exposing `is_validation_mode()` (reads `config.yaml`).  

**Checkpoint**: US‑1 must pass its independent tests and produce a valid graph JSON for each sample.

---

## Phase 4: User Story 2 – Topological Metric Calculation (Priority P2)

- [ ] T018 [P] Unit test `tests/unit/test_metrics.py` for clustering coefficient & LCC fraction.  
- [ ] T019 [P] Unit test `tests/unit/test_disconnected_graphs.py` confirming average‑path‑length is computed only on the LCC.  
- [ ] T020 [P] Integration test `tests/integration/test_percolation.py` validating the binary‑search percolation‑threshold algorithm.  
- [ ] T021 [P] Implement `src/metrics/clustering.py` computing global clustering coefficient and density‑normalized clustering (`C / ρ`).  
- [ ] T022b [P] Implement `src/metrics/zero_defect.py` – detects `node_count == 0`, sets `average_path_length: null`, adds `average_path_length_semantic: "infinity"` and `zero_defect_flag: true`; logs a warning.  
- [ ] T022 [P] Implement `src/metrics/paths_and_lcc.py` to compute:  
  1. Average path length on the LCC (null if disconnected).  
  2. `is_connected` flag.  
  3. `lcc_fraction = |LCC| / total_nodes`.  
  Uses helper from T022b. Exposes `calculate_paths_and_lcc(graph)`.  
- [ ] T023 [P] Implement `src/metrics/percolation.py` performing binary search over `[0.5 nm, 10 nm]` (tolerance 0.01 nm) to find the distance where `lcc_fraction` exceeds 0.5; stores `percolation_threshold` in the graph dict.  
- [ ] T025b [P] Implement `src/metrics/lattice_correction.py` applying the background lattice correction to thermal resistance (`1/R_total = 1/R_defect + 1/R_lattice`). Skips correction in `validation_mode`. Handles infinite resistance when `average_path_length_semantic == "infinity"`.  
- [ ] T025 [P] Implement `src/metrics/aggregator.py` that merges clustering, path/LCC, percolation, degree distribution, and lattice‑correction results into a single `TopologyGraph` dict (validated against `graph.schema.yaml`). Exposes `aggregate_metrics(graph, config)`.  
- [ ] T026 [P] (Optional) Add unit tests for the aggregator to verify schema compliance.  

**Checkpoint**: After Phase 4, each sample has a fully populated `TopologyGraph` JSON containing all required fields and flags.

---

## Phase 5: User Story 3 – Correlation Analysis & Statistical Validation (Priority P3)

- [ ] T026_test [P] Unit test `tests/unit/test_bootstrap.py` confirming 95 % CI generation from 1 000 resamples.  
- [ ] T027 [P] Unit test `tests/unit/test_pvalue_correction.py` verifying Bonferroni correction (`adjusted_p = raw_p × 20`).  
- [ ] T031b_test [P] Unit test `tests/unit/test_gp_regressor.py` ensuring Gaussian Process regressor converges on a small synthetic dataset.  
- [ ] T033 [P] Integration test `tests/integration/test_correction_validity.py` simulating multiple hypotheses and checking family‑wise error control.  
- [ ] T028 [P] Integration test `tests/integration/test_correlation_pipeline.py` running the full pipeline on a synthetic dataset with an injected r = 0.8 correlation.  
- [ ] T029 [P] Implement `src/analysis/confounders.py` providing partial‑correlation and ANCOVA controls for defect density and `material_type`.  
- [ ] T030 [P] Implement `src/analysis/dimensionality.py` performing PCA on all scalar topological metrics; retains components explaining ≥ 95 % variance.  
- [ ] T031 [P] Implement `src/analysis/correlation.py` that:  
  - Computes Pearson & Spearman coefficients for each retained PC vs. thermal conductivity.  
  - Fits linear regression and polynomial regressions (degrees 1‑3).  
  - Returns model parameters and R².  
- [ ] T031b [P] Implement `src/analysis/gp_regressor.py` (CPU‑friendly) for optional non‑linear exploration.  
- [ ] T031d [P] Implement `src/analysis/population_correlation.py` that detects missing one‑to‑one joins, aggregates metrics & conductivity per dataset, performs correlation on these aggregates, and flags `analysis_type: population_aggregate` in the output JSON.  
- [ ] T032 [P] Implement `src/analysis/bootstrap.py` performing 1 000 bootstrap resamples to produce 95 % confidence intervals for all coefficients (FR‑004).  
- [ ] T033_corr [P] Implement `src/analysis/correction.py` applying **Bonferroni** correction (fixed family size m = 20) to all p‑values (FR‑005).  
- [ ] T034 [P] Implement `src/analysis/sensitivity.py` that repeats the full pipeline for proximity‑threshold multipliers `[1.0, 1.5, 2.0, 2.5]` (baseline 2.5 nm → 2.5, 3.75, 5.0, 6.25 nm). For each run it records the primary correlation coefficient, computes the standard deviation across runs, and writes `results/sensitivity_analysis.json` with fields `thresholds`, `correlation_sd`, and `robustness_status` (target ≤ 0.05). Skips hypothesis testing when `validation_mode` is true.  
- [ ] T035 [P] Implement `src/analysis/visualizer.py` generating scatter plots with regression lines for each metric vs. conductivity; saves PNGs to `results/plots/`.  
- [ ] T036a [P] Implement `src/analysis/safety_guard.py` that reads `state/data_status.json` and `config.yaml`; if `validation_mode` or `has_real_data` is false, aborts the statistical pipeline and writes `results/safety_exit.log`.  
- [ ] T036b [P] Implement `src/analysis/synthetic_warning.py` creating `results/synthetic_warning.log` when the safety guard triggers.  
- [ ] T036c [P] Implement `src/analysis/reporter.py` that aggregates all `AnalysisResult` objects, incorporates sensitivity metrics, handles synthetic‑mode flags, and writes the final `results/analysis_report.json`.  

**Checkpoint**: After Phase 5 the pipeline either (a) produces a full statistical report with Bonferroni‑adjusted p‑values, bootstrap CIs, partial‑correlation results, and sensitivity analysis, **or** (b) safely exits with a synthetic‑mode warning and no scientific conclusions.

---

## Phase 6: Polish & reproducible hand‑off (Phase 3 of the template)

- [ ] T037 [P] Update `docs/quickstart.md` with examples for data ingestion, synthetic‑fallback, and the `validation_mode` flag.  
- [ ] T038 [P] Run `mypy --strict src/` and fix all type‑checking errors.  
- [ ] T039 [P] Add profiling script `src/utils/profile_memory.py` that streams a max‑size synthetic dataset (50 samples × 10 k defects) and writes `results/memory_profile.json` containing peak RAM usage and pass/fail status against the 7 GB limit.  
- [ ] T040 [P] Add comprehensive docstrings to all public API functions.  
- [ ] T041 [P] Validate the end‑to‑end pipeline via `docs/quickstart.md` (including synthetic‑mode path).  
- [ ] T042 [P] Implement `src/utils/state_tracker.py` that computes SHA‑256 hashes for every artifact and stores them in `state/` for reproducibility.  
- [ ] T046 [P] Create `code/utils/checksum_data.py` (wrapper around `src/utils/checksum.py`) and verify it runs via `python code/utils/checksum_data.py`. Update `docs/quickstart.md` accordingly.  
- [ ] T047 [P] Create `code/main.py` as the pipeline entry point (invokes orchestrator, ingestion, graph construction, metrics, analysis, and reporting). Verify it runs with `python code/main.py`. Update `docs/quickstart.md` accordingly.  

---

## Dependencies & Execution Order

| Phase | Depends On |
|-------|------------|
| Phase 1 (Setup) | None |
| Phase 2 (Foundational) | Phase 1 |
| Phase 3 (US 1) | Phase 2 |
| Phase 4 (US 2) | Phase 3 (graph JSONs) |
| Phase 5 (US 3) | Phase 4 (metric JSONs) |
| Phase 6 (Polish) | All prior phases |

Parallelism is allowed for tasks marked `[P]` (different files, no data‑flow dependencies).  

---

## Revision notes

- **T008a** and **T008b** were reopened because the previous implementations were missing/invalid. They are now unchecked and fully specified above.  
- All other previously checked tasks remain unchanged as they satisfied their respective verification criteria.  

---
