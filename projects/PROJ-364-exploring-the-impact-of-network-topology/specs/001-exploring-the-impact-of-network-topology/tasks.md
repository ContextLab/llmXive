# Tasks: Exploring the Impact of Network Topology on Heat Dissipation in 2D Materials

**Input**: Design documents from `/specs/001-network-topology-heat-dissipation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

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

- [X] T001 Create project structure: `src/`, `tests/`, `data/raw/`, `data/processed/`, `results/`, `state/`, `contracts/`, `logs/`, `docs/`. Initialize `requirements.txt`, `config.yaml`, and `pyproject.toml`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. Note: Tasks T008a/T008b were previously flagged for missing artifacts but are now re-validated and active; they are the source of truth for reproducibility.

- [X] T002a [P] Create `requirements.txt` with pinned versions: `networkx>=3.2`, `pandas>=2.2`, `numpy>=1.26`, `scipy>=1.12`, `scikit-learn>=1.4`, `matplotlib>=3.8`, `seaborn>=0.13`, `pyyaml>=6.0`, `jsonschema>=4.22`.
- [X] T002b [P] Install dependencies: Run `pip install -r requirements.txt` in the project root.
- [X] T003 [P] Implement linting and formatting configuration:
 1. Create `.ruff.toml` with rules `select = ["E", "F", "W"]`.
 2. Create `pyproject.toml` with `[tool.black] line-length = 88`.
 **Deliverables**: `.ruff.toml`, `pyproject.toml`.
- [X] T004 [P] Initialize project directory structure and version control tracking: Create `data/raw`, `data/processed`, `results`, `state`, `contracts`, `logs`, `docs`, `src`, `src/data`, `src/graphs`, `src/metrics`, `src/analysis`, `src/utils`, `tests/unit`, `tests/integration`, `tests/contract` directories and add `.gitkeep` files to all. **DEPENDS: T001**.
- [X] T005 [P] Create `src/constants/material_lattice.yaml` and `src/constants/lattice_resistance.yaml` file structures with placeholder comments.
 1. Create `src/constants/material_lattice.yaml` with keys for `graphene` (0.246 nm) and `MoS2` (commented as "VALUE REQUIRED").
 2. Create `src/constants/lattice_resistance.yaml` with `R_lattice` (1.2e-4 K/W from DOI: 10.1103/PhysRevB.93.045417).
 3. Create `src/constants/config_defaults.py` defining `BASELINE_THRESHOLD_NM = 2.0` and `VALIDATION_MODE_DEFAULT = False`.
 **Deliverables**: `src/constants/material_lattice.yaml`, `src/constants/lattice_resistance.yaml`, `src/constants/config_defaults.py`.
- [X] T005b [P] Populate `src/constants/material_lattice.yaml` with the verified lattice constant for MoS2.
 1. Search peer-reviewed literature or Materials Cloud for the MoS2 lattice constant.
 2. Update `src/constants/material_lattice.yaml` with the verified value (e.g., "0.316 nm" from DOI: 10.1021/acs.nanolett.5b01838).
 3. If no verified value is found, raise a `ValueError` with the message "MoS2 lattice constant not found" and exit with code 1.
 4. **Build Process**: Run `pytest` to verify the error handling works correctly if the value is missing or invalid.
 **Deliverables**: Updated `src/constants/material_lattice.yaml` with verified MoS2 value. **DEPENDS**: T005.
- [X] T006a [P] Create `logging.conf` with format string `%(asctime)s - %(name)s - %(levelname)s - %(message)s` and file path `logs/pipeline.log`.
- [X] T006b [P] Implement `src/utils/logger.py` to load `logging.conf` and provide a `get_logger()` function.
- [X] T007a [P] Create `contracts/dataset.schema.yaml` defining the schema for defect coordinate data (columns: `sample_id`, `x`, `y`, `material_type`, `thermal_conductivity`).
- [X] T007b [P] Create `contracts/graph.schema.yaml` defining the schema for `TopologyGraph` objects (nodes, edges, metrics).
- [X] T007c [P] Create `contracts/analysis.schema.yaml` defining the schema for `AnalysisResult` objects (correlations, p-values, CIs).
- [X] T008a [P] Implement `src/utils/checksum.py` with function `calculate_sha256(file_path: str) -> str`.
 - **Deliverables**: `src/utils/checksum.py`, `tests/unit/test_checksum.py`.
- [X] T008b [P] Implement `tests/unit/test_checksum.py` to verify `calculate_sha256` returns correct hash for a test file.
 - **Deliverables**: `tests/unit/test_checksum.py`.
- [X] T009a [P] Implement `src/data/materials.py` that loads material lattice constants from `src/constants/material_lattice.yaml`. **No placeholder strings**; the constants file is generated by T005/T005b.
- [X] T009b [P] Implement `tests/unit/test_materials.py` to verify `MATERIAL_CONSTANTS` values are loaded correctly.
- [X] T012a [P] [US1] Implement `src/data_ingestion/verify_data.py` to check for the existence of paired real datasets. It writes `state/data_status.json` with keys `data_found` (bool), `is_unpaired` (bool). **Note**: This task depends on T043/T044 to attempt data fetches first. **DEPENDS**: T043, T044.
- [X] T012b [P] Implement `src/utils/data_gap_report.py` that reads `state/data_status.json` and, if `data_found` is false, writes `results/data_gap_report.json` describing the dataset limitation per the plan.
- [X] T043 [P] [US1] Implement `src/data_ingestion/fetch_materials_cloud.py` to query and download defect coordinate datasets from Materials Cloud using their API or direct URL patterns.
 - **Constraint**: If download fails, catch the error, log it, and write `state/data_status.json` `data_found: false`. **DO NOT** raise a fatal error that halts the pipeline immediately; allow T012a to handle the status.
 - **Output**: Save raw CSV to `data/raw/materials_cloud_{sample_id}.csv` if successful.
 - **Deliverable**: `src/data_ingestion/fetch_materials_cloud.py`, `tests/unit/test_fetch_materials_cloud.py`.
- [X] T044 [P] [US1] Implement `src/data_ingestion/fetch_zenodo.py` to download datasets from Zenodo using DOI resolution.
 - **Constraint**: If download fails, catch the error, log it, and write `state/data_status.json` `data_found: false`. **DO NOT** raise a fatal error that halts the pipeline immediately; allow T012a to handle the status.
 - **Output**: Save raw CSV to `data/raw/zenodo_{sample_id}.csv` if successful.
 - **Deliverable**: `src/data_ingestion/fetch_zenodo.py`, `tests/unit/test_fetch_zenodo.py`.
- [X] T045 [P] [US1] Implement `src/data_ingestion/dataset_registry.py` to maintain a `state/dataset_registry.json` mapping `sample_id` to source URL, DOI, and checksum.
 - **Logic**: Before processing, check this registry. If a verified real source exists, use it. If not, trigger the data gap report (T012b) and halt scientific analysis.
 - **Deliverable**: `src/data_ingestion/dataset_registry.py`.
- [X] T012c [P] [US1] **NEW**: Implement `src/orchestration/fallback_orchestrator.py` to manage the transition to synthetic mode.
 - **Logic**: Read `state/data_status.json` (from T012a). If `data_found` is false, set `validation_mode: true` and `fallback_mode: synthetic` in `state/data_status.json` AND update `config.yaml` to set `validation_mode: true`. If `data_found` is true, set `validation_mode: false` and `fallback_mode: none`.
 - **Deliverable**: `src/orchestration/fallback_orchestrator.py`. **DEPENDS**: T012a, T043, T044.

---

## Phase 3: User Story 1 - Data Ingestion and Graph Construction (Priority: P1) 🎯 MVP

**Goal**: Ingest raw defect coordinate datasets and convert them into network graphs where nodes represent defects and edges represent proximity.

**Independent Test**: Load a known sample dataset (500x500 pixel graphene simulation with 100 known defects) and verify the resulting graph has exactly 100 nodes and edge density matches the threshold logic.

### Tests for User Story 1 ⚠️

- [X] T010 [P] [US1] Unit test for coordinate parsing and missing value handling in `tests/unit/test_data_ingestion.py`.
- [X] T011 [P] [US1] Integration test for graph construction with known threshold in `tests/integration/test_graph_construction.py`.
- [X] T012 [P] [US1] Contract test validating output against `graph.schema.yaml` in `tests/contract/test_graph_schema.py`.

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement `src/data_ingestion/loader.py` to load CSV/Parquet with `chunksize` streaming; drop rows with missing x/y and log warnings (FR‑001, US1‑Scenario 2). **Logic**: If `validation_mode` is true (set by T012c), load from synthetic generator output; otherwise load from `data/raw`. **Deliverables**: warning log, `DataIngestionError` if all rows dropped, audit file `data/processed/dropped_rows.csv`. **DEPENDS**: T012c, T043, T044.
- [X] T014 [US1] Implement `src/data_ingestion/threshold.py` to calculate the proximity threshold: retrieve material‑specific lattice constants from `src/data/materials.py` (T009a) and `statistical_override` flag from `config.yaml` (T005). Apply statistical multiplier if `statistical_override` is true; otherwise use the fixed physical distance (`BASELINE_THRESHOLD_NM` from `src/constants/config_defaults.py`). **Output**: Write calculated threshold to `state/threshold_config.json`. **DEPENDS**: T005, T009a, T005b. **Modularity**: Expose `calculate_threshold(material_type, config)` as a reusable function for T034.
- [X] T015 [US1] Implement `src/graphs/constructor.py` using `scipy.spatial.cKDTree` for O(N log N) edge creation within the computed threshold. **Modularity**: Expose `construct_graph(coordinates, threshold)` as a reusable function for T034.
- [X] T016 [US1] Implement `src/graphs/serializer.py` to convert NetworkX graphs to JSON‑compatible dicts conforming to `graph.schema.yaml`. **Output**: Save to `data/processed/graphs/{sample_id}.json` after validating against `graph.schema.yaml`. **DEPENDS**: T015.
- [X] T017 [S] [US1] Implement `src/data_ingestion/generate_synthetic.py` for validation‑only mode (seeded, versioned, checksummed). **CRITICAL SAFETY GUARD**: This script runs **only** when `validation_mode: true` in `config.yaml` (set by T012c). When invoked, it generates synthetic data and updates `state/data_status.json` `fallback_mode` to `synthetic`. **DEPENDS**: T012c.
- [X] T017a [P] Add documentation and a small utility `src/utils/validation_mode_flag.py` that reads `config.yaml` and provides a boolean `is_validation_mode()` used by all downstream tasks to enforce synthetic‑only execution.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently.

---

## Phase 4: User Story 2 - Topological Metric Calculation (Priority: P2)

**Goal**: Calculate specific network topology metrics (clustering, path length, degree distribution, LCC, percolation) for each generated graph.

**Independent Test**: Run metric calculator on a synthetic Erdos‑Renyi graph and verify calculated metrics match theoretical expectations within tolerance.

### Tests for User Story 2 ⚠️

- [X] T018 [P] [US2] Unit test for clustering coefficient and LCC fraction calculation in `tests/unit/test_metrics.py`.
- [X] T019 [P] [US2] Unit test for disconnected graph handling (path length on LCC only) in `tests/unit/test_disconnected_graphs.py`.
- [X] T020 [P] [US2] Integration test for percolation threshold binary search in `tests/integration/test_percolation.py`.

### Implementation for User Story 2

- [X] T021 [P] [US2] Implement `src/metrics/clustering.py` for global clustering coefficient and density‑normalized variant (Plan Section 3).
- [X] T022b [US2] Implement zero‑defect handling in `src/metrics/zero_defect.py`:
 - Detect `node_count == 0`.
 - Set `average_path_length` to `null`.
 - Add field `average_path_length_semantic: "infinity"` and `zero_defect_flag: true` to the `TopologyGraph` dictionary.
 - Log warning: `"[US2] Zero defects detected for sample {sample_id}. Assigned null path length with semantic infinity."`.
 **Deliverable**: Modified `TopologyGraph` dict with new fields.
- [X] T022 [US2] Implement `src/metrics/paths_and_lcc.py` to compute:
 1. Average path length **only** on the Largest Connected Component (LCC); if the graph is disconnected, set `average_path_length` to `null` and `is_connected: false`.
 2. `lcc_fraction` = `|LCC| / total_nodes`.
 3. Incorporate zero‑defect semantics from T022b by calling the helper functions defined in `src/metrics/zero_defect.py`.
 **DEPENDS**: T022b. **Modularity**: Expose `calculate_paths_and_lcc(graph)` as a reusable function for T034.
- [X] T023 [US2] Implement `src/metrics/percolation.py` to estimate critical distance `d_c` via binary search where LCC fraction exceeds a configurable threshold (default 0.9). Serialize `d_c` into the `TopologyGraph` JSON dict.
- [X] T025b [US2] Implement `src/metrics/lattice_correction.py` to apply the **background lattice correction** to *thermal resistance* values (not to topological metrics):
 - Formula: `1 / R_total = 1 / R_defect + 1 / R_lattice`.
 - `R_lattice` is read from `src/constants/lattice_resistance.yaml` via T005.
 - If `validation_mode` is true, skip correction and log a warning.
 - Verify that if `average_path_length_semantic == "infinity"` the correction step treats `R_defect` as zero (i.e., infinite resistance) and propagates `null` appropriately.
 **DEPENDS**: T005.
- [X] T025 [US2] Implement `src/metrics/aggregator.py` to combine all metric components (clustering, path length, LCC fraction, percolation, degree distribution) into a single `TopologyGraph` dict, **after** applying lattice correction (T025b). **DEPENDS**: T022b, T022, T023, T025b. **Modularity**: Expose `aggregate_metrics(graph, config)` as a reusable function for T034.
- [X] T026 [P] [US2] (Optional) Add unit tests for the aggregator to ensure correct schema compliance.

**Checkpoint**: User Stories 1 & 2 should now work independently.

---

## Phase 5: User Story 3 - Correlation Analysis and Statistical Validation (Priority: P3)

**Goal**: Perform correlation analysis (linear/non‑linear, Pearson/Spearman) between topological metrics and thermal conductivity, including bootstrap and multiple‑comparison correction.

**Independent Test**: Run analysis on a synthetic dataset with injected correlation (r = 0.8) and verify detection with p < 0.05.

### Tests for User Story 3 ⚠️

- [X] T026_test [P] [US3] Unit test for bootstrap resampling confidence intervals in `tests/unit/test_bootstrap.py`.
- [X] T027 [P] [US3] Unit test for Bonferroni correction logic in `tests/unit/test_pvalue_correction.py`.
- [X] T031b_test [P] [US3] Unit test for Gaussian Process regressor convergence and behavior in `tests/unit/test_gp_regressor.py`.
- [X] T033 [P] [US3] Integration test for multiple-comparison correction validity (simulate data, verify family-wise error rate control) in `tests/integration/test_correction_validity.py`.
- [X] T028 [P] [US3] Integration test for full correlation pipeline with known inputs in `tests/integration/test_correlation_pipeline.py`.

### Implementation for User Story 3

- [X] T029 [P] [US3] Implement `src/analysis/confounders.py` for partial correlation and ANCOVA controlling for defect density, material purity, and temperature (Plan Section 4).
- [X] T030 [US3] Implement `src/analysis/dimensionality.py` to perform PCA on the full metric set, retaining components that explain ≥ 95 % variance.
- [X] T031 [US3] Implement `src/analysis/correlation.py` for Pearson and Spearman tests on retained principal components; also fit linear and polynomial (degree 2) regressions.
- [X] T031b [US3] Implement `src/analysis/gp_regressor.py` for Gaussian Process regression with automatic kernel selection and hyper‑parameter optimization (required by FR‑003).
- [X] T031d [US3] Implement `src/analysis/population_correlation.py`:
 - Input: `data/processed/joined_metrics.csv`.
 - Logic: Automatically inspect schema for missing `sample_id` joins. If unpaired, aggregate mean topology metrics and mean thermal conductivity per source dataset. Perform correlation on these aggregated means.
 - Output: `results/population_correlation.json`.
 - **CRITICAL**: Output must include a flag `analysis_type: population_aggregate` in the result JSON to distinguish from paired correlations.
 **DEPENDS**: T012a (for status) and internal schema inspection logic.
- [X] T031d1 [P] Add helper `src/analysis/schema_inspector.py` that detects missing joins without relying solely on `state/data_status.json`.
- [X] T032 [US3] Implement `src/analysis/bootstrap.py` for 1 000 resamples, generating 95 % confidence intervals for all coefficients (FR‑004, US3‑Scenario 2).
- [X] T033_corr [US3] Implement `src/analysis/correction.py` for multiple‑comparison correction:
 - Use Bonferroni when ≤ 5 tests, otherwise Benjamini‑Hochberg FDR.
- [X] T034 [US3] Implement `src/analysis/sensitivity.py` to repeat the full pipeline (T029-T033_corr) for proximity‑threshold multipliers: `[1.5, 2.0, 2.5]` (mapping to 3.0nm, 4.0nm, 5.0nm based on `BASELINE_THRESHOLD_NM` from `src/constants/config_defaults.py`) as per SC-005 and FR-010.
 - **Logic**: For each multiplier `m` in `[1.5, 2.0, 2.5]`:
  1. Calculate `absolute_threshold = m * BASELINE_THRESHOLD_NM`.
  2. **Re-run** threshold calculation (T014), graph construction (T015), and metric extraction (T025) for the *same* dataset by calling the reusable functions exposed in those tasks.
  3. If `validation_mode` is true (real data missing), run the pipeline **only** to validate the code path; **skip all hypothesis testing (T029-T033_corr)** and flag results as `validation_only`.
  4. Record the primary correlation coefficient (or metric stability) for each run.
  5. Compute `std_dev` across the runs.
  6. Write `std_dev` and `robustness_status` (`target_met` if ≤ 0.05, else `target_exceeded`) into `results/sensitivity_analysis.json`.
 - **Output**: `results/sensitivity_analysis.json`.
 - **Dependencies**: Requires modules from T014, T015, T025, T029, T030, T031, T031b, T031d, T032, T033_corr to be available. **Note**: If `validation_mode` is true, T029-T033_corr are skipped during execution.
 **DEPENDS**: T014, T015, T025, T012c.
- [X] T035 [US3] Implement `src/analysis/visualizer.py` to generate scatter plots with regression lines; save PNGs to `results/`.
- [X] T036a [US3] **Early Exit Guard**: Implement `src/analysis/safety_guard.py` to read `state/data_status.json` and `config.yaml`. If `validation_mode` is true OR `has_real_data` is false, immediately halt the statistical pipeline (T029-T035) and write a `results/safety_exit.log` file. This prevents any hypothesis testing on synthetic data. **DEPENDS**: T012c.
- [X] T036b [US3] Implement `src/analysis/synthetic_warning.py` to generate `results/synthetic_warning.log` if the pipeline was halted by T036a.
- [X] T036c [US3] Implement `src/analysis/reporter.py` to aggregate all `AnalysisResult` objects:
 - Read `config.yaml` (`validation_mode`) and `state/data_status.json` (`has_real_data`, `is_unpaired`, `fallback_mode`).
 - If `validation_mode` is true **or** `has_real_data` is false, produce a flagged result with `is_synthetic: true` and skip all hypothesis‑testing steps (relying on T036a to have halted the pipeline).
 - If `is_unpaired` is true, incorporate output from T031d.
 - Include fields `std_dev` and `robustness_status` from T034.
 - Write final JSON to `results/analysis_report.json`.
 **DEPENDS**: T036a, T034.

**Checkpoint**: All user stories should now be independently functional and respect the synthetic‑data safety guard.

---

## Phase 6: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T037 [P] Update `docs/quickstart.md` with data ingestion examples, synthetic‑fallback instructions, and explanation of the `validation_mode` flag.
- [X] T038 [P] Ensure type safety: run `mypy --strict` on `src/`, fix all errors, and verify 0 errors remain (Consolidated from T038a/b/c).
- [X] T039 [P] Performance optimization: verify streaming ingestion keeps RAM < 7 GB for a synthetic set of 50 samples, each with [deferred] defects.
 - **Action**: Add profiling script `src/utils/profile_memory.py`.
 - **Deliverable**: The script must write `results/memory_profile.json` containing peak RAM usage and a `pass` or `fail` status based on the 7GB limit.
- [X] T040 [P] Add comprehensive docstrings to all public API functions.
- [X] T041 [P] Run `quickstart.md` validation to ensure end‑to‑end pipeline execution (including synthetic‑mode path).
- [X] T042 [P] Verify `state/` hashes update correctly on any data or code change; implement `src/utils/state_tracker.py` to compute and store hashes.
- [X] T046 [P] **RESOLVED**: Create `code/utils/checksum_data.py` (a wrapper script for T008a logic) to satisfy the quickstart run-book command.
 - **Action**: Create the file and verify the quickstart command `python code/utils/checksum_data.py` runs without error. **Update docs/quickstart.md to reference this script.**
 **DEPENDS**: T008a.
- [X] T047 [P] **RESOLVED**: Create `code/main.py` (the pipeline entry point) to satisfy the quickstart run-book command.
 - **Action**: Create the file and verify the quickstart command `python code/main.py` runs the full pipeline (including fallback logic) without error. **Update docs/quickstart.md to reference this script.**
 **DEPENDS**: T012c, T017, T036a.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies – can start immediately.
- **Foundational (Phase 2)**: Depends on Setup; BLOCKS all user stories.
- **User Stories (Phase 3+)**: All depend on Foundational. Stories can proceed in parallel once Phase 2 is complete.
- **Polish (Final Phase)**: Depends on completion of desired user stories.

### User Story Dependencies

- **User Story 1 (P1)**: Starts after Foundational; no other story dependencies.
- **User Story 2 (P2)**: Starts after Foundational; depends on US1 output (graphs).
- **User Story 3 (P3)**: Starts after Foundational; depends on US2 output (metrics) **and** US1 for any direct graph‑metric joins.
- **Data Acquisition (Phase 2)**: Must be completed to enable real-data validation of US3.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation.
- Core utilities before services, services before aggregators, aggregators before analysis/reporting.
- Story complete before moving to next priority (optional parallelism allowed).

### Parallel Opportunities

- All Setup tasks marked `[P]` can run in parallel.
- All Foundational tasks marked `[P]` can run in parallel within Phase 2.
- Once Foundational is complete, all user stories can start in parallel (if team capacity allows).
- Tests for a user story marked `[P]` can run in parallel.
- Different user stories can be worked on in parallel by different developers.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 (Setup).
2. Complete Phase 2 (Foundational) – ensure `config.yaml`, constants files, and status checker are ready.
3. Complete Phase 3 (User Story 1) – verify graph construction passes independent tests.
4. **STOP and VALIDATE**: Run US1 tests; demo graph output.

### Incremental Delivery

1. After MVP, add User Story 2, run its tests, demo metric outputs.
2. Add User Story 3, run its full pipeline (including synthetic‑mode safety checks), produce final report.
3. **Critical Step**: Execute Phase 2 (Data Acquisition) to attempt real-data ingestion. If real data is found, re-run US3. If not, the pipeline must halt scientific conclusions as per the safety guard.
4. Polish: documentation, type safety, performance profiling, final end‑to‑end validation.

---

## Notes

- **[P]** tasks = different files, no dependencies.
- **[Story]** label maps task to a specific user story for traceability.
- Tests must fail before implementation; commit after each logical group.
- Synthetic‑mode (`validation_mode: true`) is **strictly** for pipeline validation; no scientific conclusions are drawn.
- All real data fetches must be reproducible; checksums recorded in `state/`.
- Threshold defaults to 2.0 nm (physically motivated) but can be overridden via `statistical_override` and the multipliers used in sensitivity analysis.
- Zero‑defect graphs receive `null` path length with `average_path_length_semantic: "infinity"` to satisfy edge‑case requirements.
- Background lattice correction is applied to thermal resistance only, preserving physical meaning.
- Sensitivity analysis follows the Spec's multiplier set `[1.5, 2.0, 2.5]` anchored to `BASELINE_THRESHOLD_NM` and reports robustness per SC-005.
- Data‑gap reporting ensures the final output transparently notes any missing paired dataset.
- **Safety Guard**: T036a ensures that if synthetic data is detected, the statistical pipeline (T029-T035) is halted immediately to prevent false scientific conclusions.
- **Data Fetching**: T043 and T044 must **never** fall back to synthetic data; they must catch errors and write status, allowing T012a/T012c to handle the fallback.
- **MoS2 Constants**: T005b ensures MoS2 lattice constant is verified and populated before execution.
- **Run-Book Resolution**: T046 and T047 resolve the missing script issues by explicitly creating the required files and verifying the quickstart commands, including updating `docs/quickstart.md`.