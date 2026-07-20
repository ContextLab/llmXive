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

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002a [P] Create `requirements.txt` with pinned versions: `networkx>=3.2`, `pandas>=2.2`, `numpy>=1.26`, `scipy>=1.12`, `scikit-learn>=1.4`, `matplotlib>=3.8`, `seaborn>=0.13`, `pyyaml>=6.0`, `jsonschema>=4.22`.
- [X] T002b [P] Install dependencies: Run `pip install -r requirements.txt` in the project root.
- [ ] T003a [P] Create `.ruff.toml` configuration file with linting rules (e.g., `select = ["E", "F", "W"]`).
- [X] T003b [P] Create `pyproject.toml` configuration for formatting (e.g., `[tool.black] line-length = 88`).
- [ ] T004a [P] Create directory structure: `mkdir -p data/raw data/processed results state contracts logs docs src src/data src/graphs src/metrics src/analysis src/utils tests/unit tests/integration tests/contract`.
- [ ] T004b [P] Add `.gitkeep` files to all created directories to ensure version control tracking.
- [X] T005 [P] [Foundational] Configure `config.yaml` with defaults: `threshold:`, `seed: 42`, `statistical_override: false`. **CRITICAL SUB-TASK**: Fetch the `R_lattice` value from the literature source cited in Plan Section 3 (DOI: 10.1103/PhysRevB.93.045417) and write the **verified numeric value** to `config.yaml` under key `R_lattice`. Do NOT use a placeholder. Also set `lattice_variance_threshold` to `0.05` in `config.yaml` for T025b.
- [ ] T006a [P] Create `logging.conf` with format string `%(asctime)s - %(name)s - %(levelname)s - %(message)s` and file path `logs/pipeline.log`.
- [ ] T006b [P] Implement `src/utils/logger.py` to load `logging.conf` and provide a `get_logger()` function.
- [ ] T007a [P] Create `contracts/dataset.schema.yaml` defining the schema for defect coordinate data (columns: `sample_id`, `x`, `y`, `material_type`, `thermal_conductivity`).
- [ ] T007b [P] Create `contracts/graph.schema.yaml` defining the schema for `TopologyGraph` objects (nodes, edges, metrics).
- [ ] T007c [P] Create `contracts/analysis.schema.yaml` defining the schema for `AnalysisResult` objects (correlations, p-values, CIs).
- [ ] T008a [P] Implement `src/utils/checksum.py` with function `calculate_sha256(file_path: str) -> str`.
- [ ] T008b [P] Implement `tests/unit/test_checksum.py` to verify `calculate_sha256` returns correct hash for a test file.
- [ ] T009a [P] Implement `src/data/materials.py` with dictionary `MATERIAL_CONSTANTS = {'graphene': {'lattice': 0.246}, 'MoS2': {'lattice': 'representative lattice constant'}}`. **CRITICAL**: This file MUST read the `R_lattice` value from `config.yaml` (set by T005) at runtime. Do NOT hardcode `R_lattice` here.
- [ ] T009b [P] Implement `tests/unit/test_materials.py` to verify `MATERIAL_CONSTANTS` values.
- [ ] T012a [P] [Foundational] Implement `src/data_ingestion/verify_data.py` to check for the existence of paired real datasets.
 - **PURE STATUS CHECKER**: This script MUST NOT trigger synthetic data generation. It MUST ONLY check for real data and write `state/data_status.json` with `has_real_data: true/false`, `is_unpaired: true/false`, `fallback_mode: synthetic/none`.
 - If `has_real_data` is false, the script MUST exit cleanly. The pipeline orchestration (external to this task) must decide whether to proceed to T017.
 - **Deliverable**: `state/data_status.json` with keys `has_real_data`, `is_unpaired`, `fallback_mode`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Graph Construction (Priority: P1) 🎯 MVP

**Goal**: Ingest raw defect coordinate datasets and convert them into network graphs where nodes represent defects and edges represent proximity.

**Independent Test**: Load a known sample dataset (500x500 pixel graphene simulation with 100 known defects) and verify the resulting graph has exactly 100 nodes and edge density matches the threshold logic.

### Tests for User Story 1 ⚠️

- [X] T010 [P] [US1] Unit test for coordinate parsing and missing value handling in `tests/unit/test_data_ingestion.py`.
- [X] T011 [P] [US1] Integration test for graph construction with known threshold in `tests/integration/test_graph_construction.py`.
- [ ] T012 [P] [US1] Contract test validating output against `graph.schema.yaml` in `tests/contract/test_graph_schema.py`.

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement `src/data_ingestion/loader.py` to load CSV/Parquet with `chunksize` streaming; drop rows with missing x/y and log warnings (FR-001, US1-Scenario 2). **Deliverables**:
 - Log message format: `"[US1] Dropped row {row_id}: missing coordinate"`
 - Exception class: `DataIngestionError` if ALL rows are dropped
 - Artifact: `data/processed/dropped_rows.csv` for auditability (Constitution III)
- [ ] T014 [US1] Implement `src/data_ingestion/threshold.py` to calculate threshold: MUST retrieve material-specific lattice constants from `src/data/materials.py` (T009) AND the statistical_override flag from config.yaml (T005). Apply statistical multiplier if `statistical_override` is active; otherwise use fixed nanoscale (FR-009, US1-Scenario 3). **DEPENDS**: Phase 2 (T005, T009) MUST be complete. **BLOCKING**: This task cannot start until T005 and T009 are marked complete.
- [X] T015 [US1] Implement `src/graphs/constructor.py` using `scipy.spatial.cKDTree` for O(N log N) edge creation within threshold (US1-Scenario 1)
- [ ] T016 [US1] Implement `src/graphs/serializer.py` to convert NetworkX graphs to JSON-compatible dicts conforming to `graph.schema.yaml`
- [ ] T017 [P] [US1] Implement `src/data_ingestion/generate_synthetic.py` for validation-only mode (seeded, versioned, checksummed). **CRITICAL SAFETY GUARD**: This script is for PIPELINE VALIDATION ONLY. It MUST NOT be used for hypothesis testing. If invoked, the pipeline MUST skip all statistical analysis steps (Phase 5) and log a warning that no scientific conclusions are drawn. **DEPENDS**: T012a (to check status).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Topological Metric Calculation (Priority: P2)

**Goal**: Calculate specific network topology metrics (clustering, path length, degree distribution, LCC, percolation) for each generated graph.

**Independent Test**: Run metric calculator on a synthetic Erdos-Renyi graph and verify calculated metrics match theoretical expectations within tolerance.

### Tests for User Story 2 ⚠️

- [X] T018 [P] [US2] Unit test for clustering coefficient and LCC fraction calculation in `tests/unit/test_metrics.py`.
- [X] T019 [P] [US2] Unit test for disconnected graph handling (path length on LCC only) in `tests/unit/test_disconnected_graphs.py`.
- [ ] T020 [P] [US2] Integration test for percolation threshold binary search in `tests/integration/test_percolation.py`.

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement `src/metrics/clustering.py` for global clustering coefficient and density-normalized variant (Plan Section 3)
- [ ] T022b [US2] [FR-002] Implement `src/metrics/edge_cases.py` to handle the "zero defects" (perfect crystal) scenario:
 - Detect when `node_count == 0`
 - Assign `null` (JSON null) to clustering, `null` to average_path_length (UNIFIED REPRESENTATION)
 - Set `zero_defect_flag: true` in metadata
 - Log specific warning: `"[US2] Zero defects detected for sample {sample_id}. Assigning null metrics."` (Spec Edge Cases)
 - **Output**: `average_path_length` MUST be `null` (not 'infinity' or NaN) to match T022.
- [ ] T022 [US2] Implement `src/metrics/paths_and_lcc.py` to calculate:
 1. Average Path Length ONLY on the Largest Connected Component (LCC); handle disconnected graphs by flagging `is_connected=false` and setting path length to `null` (UNIFIED REPRESENTATION with T022b).
 2. LCC Fraction (nodes in LCC / total nodes) (FR-002, US2-Scenario 1).
 (Consolidated from T022a to resolve arbitrary split confusion). **Deliverables**: `TopologyGraph` dict entries for `average_path_length`, `is_connected`, and `lcc_fraction`. **DEPENDS**: T022b.
- [ ] T023 [US2] Implement `src/metrics/percolation.py` to estimate critical distance `d_c` via binary search where LCC fraction exceeds threshold; MUST serialize `d_c` to the TopologyGraph JSON dict (Constitution VI)
- [ ] T025b [US2] [FR-002] Implement `src/metrics/lattice_correction.py` to apply the "Background lattice correction" (series-parallel resistance formula) to metrics before correlation. **Deliverables**:
 - Implement formula: `1/R_total = 1/R_defect + 1/R_lattice`
 - **Read `R_lattice` from `config.yaml`** as defined in T005.
 - **Stability Verification**: Read `lattice_variance_threshold` from `config.yaml` (default 0.05). Calculate variance of corrected metrics across samples; if variance > threshold, log a warning. **DO NOT HARDCODE THRESHOLD**. This addresses the gap between the plan's methodology and the spec's sensitivity requirements.
 - **Dependencies**: T005 (config.yaml).
- [ ] T025 [US2] Implement `src/metrics/aggregator.py` to combine all metrics (clustering, path, LCC fraction, percolation, degree) into a single `TopologyGraph` dict. MUST depend on T022b (zero defects), T022 (LCC metrics), T023 (percolation), and T025b (lattice correction). Load `R_lattice` from `config.yaml` (via T005) and apply the series-parallel resistance correction to the raw metrics before they are passed to the correlation phase (Plan Section 3) **DEPENDS**: T025b.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Correlation Analysis and Statistical Validation (Priority: P3)

**Goal**: Perform correlation analysis (linear/non-linear, Pearson/Spearman) between topological metrics and thermal conductivity, including bootstrap and multiple-comparison correction.

**Independent Test**: Run analysis on a synthetic dataset with injected correlation (r=0.8) and verify detection with p < 0.05.

### Tests for User Story 3 ⚠️

- [ ] T026 [P] [US3] Unit test for bootstrap resampling confidence intervals in `tests/unit/test_bootstrap.py`.
- [ ] T027 [P] [US3] Unit test for Bonferroni correction logic in `tests/unit/test_pvalue_correction.py`.
- [ ] T028 [P] [US3] Integration test for full correlation pipeline with known inputs in `tests/integration/test_correlation_pipeline.py`.

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement `src/analysis/confounders.py` for partial correlation and ANCOVA controlling for defect density, purity, and temperature (Plan Section 4)
- [ ] T030 [US3] Implement `src/analysis/dimensionality.py` to perform PCA on metrics, retaining components explaining ≥95% variance (Plan Section 4)
- [ ] T031 [US3] Implement `src/analysis/correlation.py` for Pearson/Spearman tests on retained PCs; include linear and polynomial regression (FR-003, US3-Scenario 1)
- [ ] T031b [US3] Implement `src/analysis/gp_regressor.py` for Gaussian Process regression (kernel selection, hyperparameter optimization) as explicitly required by FR-003
- [ ] T031d [US3] [FR-008] Implement `src/analysis/population_correlation.py` to handle FR-008:
 - **CRITICAL CHECK**: Read `state/data_status.json`. If `has_real_data` is false, SKIP hypothesis testing immediately and log a warning.
 - If `is_unpaired` is true (and `has_real_data` is true), aggregate mean topology metrics and mean thermal conductivity per source dataset.
 - Perform population-level correlation analysis.
 - Output results to `results/population_correlation.json`.
 - **Dependencies**: T012a (data status).
- [ ] T032 [US3] Implement `src/analysis/bootstrap.py` for resampling to generate confidence intervals (FR-004, US3-Scenario 2)
- [ ] T033 [US3] Implement `src/analysis/correction.py` for Bonferroni or Benjamini-Hochberg FDR on p-values (FR-005, US3-Scenario 4)
- [ ] T034 [US3] Implement `src/analysis/sensitivity.py` to repeat the full pipeline (T029-T033) for thresholds **x (baseline), 2.0x, and 2.5x** the baseline (per FR-010/SC-005).
 - Calculate standard deviation of the correlation coefficient across these thresholds.
 - **FAIL CONDITION**: If `std_dev > 0.05`, the task MUST fail the build (exit code 1) and log an error. This is a mandatory success criterion (SC-005).
 - Output `std_dev` field in `AnalysisResult` JSON (FR-010, SC-005).
 - **Dependencies**: T031, T031b, T031d.
- [ ] T035 [US3] Implement `src/analysis/visualizer.py` to generate scatter plots with regression lines and save to `results/` (US3-Scenario 5)
- [ ] T036 [US3] Implement `src/analysis/reporter.py` to aggregate results into `AnalysisResult` JSON objects.
 - **CRITICAL SAFETY GUARD**: At the start of execution, read `state/data_status.json`. If `has_real_data` is false, HALT execution immediately and log: "Synthetic data detected. Hypothesis testing skipped." Do NOT generate statistical reports.
 - **Synthetic Detection**: Check `config.yaml` flag `is_synthetic` or file hash; if true, skip hypothesis testing
 - **Artifact**: Generate `results/synthetic_warning.log` with specific message if synthetic data is detected (Plan Section 4, Section 5)
 - **Unpaired Data**: Route to T031d output if `state/data_status.json` indicates unpaired data (FR-008).
 - **Dependencies**: T031, T031b, T031d, T034.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Update `docs/quickstart.md` with data ingestion examples and synthetic fallback instructions
- [ ] T038 [P] Ensure type safety: run `mypy --strict` on `src/`, fix all errors, and verify 0 errors remain (Consolidated from T038a/b/c)
- [ ] T039 Performance optimization: verify streaming ingestion keeps RAM < 7GB for 50 samples
- [ ] T040 [P] Add comprehensive docstrings to all public API functions
- [ ] T041 Run `quickstart.md` validation to ensure end-to-end pipeline execution
- [ ] T042 Verify `state/` hashes update correctly on any data or code change

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (graphs)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (metrics) and US1 (if direct pairing needed)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utilities before services
- Services before endpoints/aggregators
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Unit test for coordinate parsing in tests/unit/test_data_ingestion.py"
Task: "Integration test for graph construction in tests/integration/test_graph_construction.py"

# Launch implementation tasks in parallel where files don't conflict:
Task: "Implement loader.py"
Task: "Implement threshold.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (Graph construction works)
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
 - Developer A: User Story 1 (Ingestion/Graphs)
 - Developer B: User Story 2 (Metrics)
 - Developer C: User Story 3 (Stats)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Data Integrity**: If real data is unavailable, use synthetic data ONLY for pipeline validation; explicitly skip hypothesis testing and log warnings (Plan Section 5).
- **Compute**: Ensure streaming is used for large datasets to stay within 7GB RAM limit.
- **Threshold**: Default to 2.0nm (phonon MFP based) unless statistical override is active.
- **LCC Fraction**: Calculated in T022 (merged), not T022a.
- **Zero Defects**: Handled in T022b with unified `null` representation.
- **GP Regression**: Implemented in T031b, unified in T036.
- **Sensitivity**: Tests x, 2.0x, 2.5x. Outputs `std_dev` field. FAILS build if std_dev > 0.05 (SC-005).
- **Data Source Gap**: No verified real dataset exists pairing defect coordinates with thermal conductivity. T017 and T036 must handle synthetic fallback gracefully; T013 must fail loudly if a real source is specified but unreachable, never substituting fake data. T031d handles population-level analysis for unpaired real data. T012a verifies data availability to resolve plan/spec contradictions.
- **Lattice Correction**: Implemented and verified in T025b. `R_lattice` is fetched from literature in T005 and read from config.yaml.
- **Ordering**: T022b before T022; T025b before T025; T031d before T034; T034 before T036.