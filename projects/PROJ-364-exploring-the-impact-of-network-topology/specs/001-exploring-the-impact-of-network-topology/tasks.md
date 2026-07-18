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

- [ ] T001 Create project structure: `src/`, `tests/`, `data/raw/`, `data/processed/`, `results/`, `state/`, `contracts/`, `logs/`, `docs/`. Initialize `requirements.txt`, `config.yaml`, and `pyproject.toml`.
- [ ] T002 Initialize Python 3.11 project with dependencies: `networkx`, `pandas`, `numpy`, `scipy`, `scikit-learn`, `matplotlib`, `seaborn`, `pyyaml`, `jsonschema`
- [ ] T003 [P] Configure linting (flake8/ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup `data/` (raw, processed) and `results/` directory structure
- [ ] T005 [P] Implement configuration management (`config.yaml`) with defaults for threshold (2.0 nm), seed (42), and material constants
- [ ] T006 [P] Setup logging infrastructure to `logs/` with distinct levels for data ingestion warnings and statistical results
- [ ] T007 Create base schema validators in `contracts/` (`dataset.schema.yaml`, `graph.schema.yaml`, `analysis.schema.yaml`)
- [ ] T008 Implement checksum utility in `src/utils/checksum.py` (SHA-256 for data integrity)
- [ ] T009 Create material constants lookup table in `src/data/materials.py` (graphene, MoS2 lattice constants, R_lattice values)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Graph Construction (Priority: P1) 🎯 MVP

**Goal**: Ingest raw defect coordinate datasets and convert them into network graphs where nodes represent defects and edges represent proximity.

**Independent Test**: Load a known sample dataset (500x500 pixel graphene simulation with 100 known defects) and verify the resulting graph has exactly 100 nodes and edge density matches the threshold logic.

### Tests for User Story 1 ⚠️

- [ ] T010 [P] [US1] Unit test for coordinate parsing and missing value handling in `tests/unit/test_data_ingestion.py`
- [ ] T011 [P] [US1] Integration test for graph construction with known threshold in `tests/integration/test_graph_construction.py`
- [ ] T012 [P] [US1] Contract test validating output against `graph.schema.yaml` in `tests/contract/test_graph_schema.py`
- [ ] T012a [P] [US1] **Data Availability Verification**: Implement `src/data_ingestion/verify_data.py` to check for the existence of paired real datasets (defect coords + thermal conductivity) vs. unpaired aggregate data. 
  - If no real data exists, generate a flag in `state/data_status.json` to trigger synthetic fallback or population-level analysis.
  - Log specific warning if the plan's "no data" assumption conflicts with the spec's "assume data" assumption, forcing a manual review or fallback path (Plan vs Spec Contradiction Resolution).
  - **Deliverable**: `state/data_status.json` with keys `has_real_data`, `is_unpaired`, `fallback_mode`.

### Implementation for User Story 1

- [ ] T013 [P] [US1] Implement `src/data_ingestion/loader.py` to load CSV/Parquet with `chunksize` streaming; drop rows with missing x/y and log warnings (FR-001, US1-Scenario 2). **Deliverables**: 
  - Log message format: `"[US1] Dropped row {row_id}: missing coordinate"`
  - Exception class: `DataIngestionError` if ALL rows are dropped
  - Artifact: `data/processed/dropped_rows.csv` for auditability (Constitution III)
- [ ] T014 [US1] Implement `src/data_ingestion/threshold.py` to calculate threshold: MUST retrieve material-specific lattice constants from `src/data/materials.py` (T009) AND the statistical_override flag from config.yaml (T005). Apply statistical multiplier if `statistical_override` is active; otherwise use fixed 2.0nm (FR-009, US1-Scenario 3). **Dependencies**: T005, T009.
- [ ] T015 [US1] Implement `src/graphs/constructor.py` using `scipy.spatial.cKDTree` for O(N log N) edge creation within threshold (US1-Scenario 1)
- [ ] T016 [US1] Implement `src/graphs/serializer.py` to convert NetworkX graphs to JSON-compatible dicts conforming to `graph.schema.yaml`
- [ ] T017 [P] [US1] Implement `src/data_ingestion/generate_synthetic.py` for validation-only mode (seeded, versioned, checksummed); explicitly NOT for scientific hypothesis testing (Plan Section 5)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Topological Metric Calculation (Priority: P2)

**Goal**: Calculate specific network topology metrics (clustering, path length, degree distribution, LCC, percolation) for each generated graph.

**Independent Test**: Run metric calculator on a synthetic Erdos-Renyi graph and verify calculated metrics match theoretical expectations within tolerance.

### Tests for User Story 2 ⚠️

- [ ] T018 [P] [US2] Unit test for clustering coefficient and LCC fraction calculation in `tests/unit/test_metrics.py`
- [ ] T019 [P] [US2] Unit test for disconnected graph handling (path length on LCC only) in `tests/unit/test_disconnected_graphs.py`
- [ ] T020 [P] [US2] Integration test for percolation threshold binary search in `tests/integration/test_percolation.py`

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement `src/metrics/clustering.py` for global clustering coefficient and density-normalized variant (Plan Section 3)
- [ ] T022 [US2] Implement `src/metrics/paths_and_lcc.py` to calculate:
  1. Average Path Length ONLY on the Largest Connected Component (LCC); handle disconnected graphs by flagging `is_connected=false` and setting path length to NaN (FR-006, US2-Scenario 2).
  2. LCC Fraction (nodes in LCC / total nodes) (FR-002, US2-Scenario 1).
  (Consolidated from T022a to resolve arbitrary split confusion). **Deliverables**: `TopologyGraph` dict entries for `average_path_length`, `is_connected`, and `lcc_fraction`.
- [ ] T022b [US2] Implement `src/metrics/edge_cases.py` to handle the "zero defects" (perfect crystal) scenario: 
  - Detect when `node_count == 0`
  - Assign `null` to clustering, `infinity` to average_path_length
  - Set `zero_defect_flag: true` in metadata
  - Log specific warning: `"[US2] Zero defects detected for sample {sample_id}. Assigning null/infinity metrics."` (Spec Edge Cases)
- [ ] T023 [US2] Implement `src/metrics/percolation.py` to estimate critical distance `d_c` via binary search where LCC fraction exceeds threshold; MUST serialize `d_c` to the TopologyGraph JSON dict (Constitution VI)
- [ ] T024 [US2] Implement `src/metrics/degree.py` to output degree distribution as histogram-ready (degree, frequency) pairs (US2-Scenario 3)
- [ ] T025b [US2] Implement `src/metrics/lattice_correction.py` to apply the "Background lattice correction" (series-parallel resistance formula) to metrics before correlation. **Deliverables**:
  - Implement formula: `1/R_total = 1/R_defect + 1/R_lattice`
  - **Stability Verification**: Calculate variance of corrected metrics across samples; log warning if variance > threshold (Plan Constitution Check). This addresses the gap between the plan's methodology and the spec's sensitivity requirements.
- [ ] T025 [US2] Implement `src/metrics/aggregator.py` to combine all metrics (clustering, path, LCC fraction, percolation, degree) into a single `TopologyGraph` dict. MUST depend on T022b (zero defects), T022 (LCC metrics), T023 (percolation), and T025b (lattice correction). Load `R_lattice` from `src/data/materials.py` (T009) and apply the series-parallel resistance correction to the raw metrics before they are passed to the correlation phase (Plan Section 3)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Correlation Analysis and Statistical Validation (Priority: P3)

**Goal**: Perform correlation analysis (linear/non-linear, Pearson/Spearman) between topological metrics and thermal conductivity, including bootstrap and multiple-comparison correction.

**Independent Test**: Run analysis on a synthetic dataset with injected correlation (r=0.8) and verify detection with p < 0.05.

### Tests for User Story 3 ⚠️

- [ ] T026 [P] [US3] Unit test for bootstrap resampling confidence intervals in `tests/unit/test_bootstrap.py`
- [ ] T027 [P] [US3] Unit test for Bonferroni correction logic in `tests/unit/test_pvalue_correction.py`
- [ ] T028 [P] [US3] Integration test for full correlation pipeline with known inputs in `tests/integration/test_correlation_pipeline.py`

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement `src/analysis/confounders.py` for partial correlation and ANCOVA controlling for defect density, purity, and temperature (Plan Section 4)
- [ ] T030 [US3] Implement `src/analysis/dimensionality.py` to perform PCA on metrics, retaining components explaining ≥95% variance (Plan Section 4)
- [ ] T031 [US3] Implement `src/analysis/correlation.py` for Pearson/Spearman tests on retained PCs; include linear and polynomial regression (FR-003, US3-Scenario 1)
- [ ] T031b [US3] Implement `src/analysis/gp_regressor.py` for Gaussian Process regression (kernel selection, hyperparameter optimization) as explicitly required by FR-003
- [ ] T031c [US3] Implement `src/analysis/regression_unifier.py` to:
  - Aggregate results from T031 and T031b
  - Perform model selection/comparison (e.g., AIC/BIC)
  - Output a single unified `RegressionResult` artifact to `results/regression_comparison.json`
  - Define schema for `RegressionResult` (metric_name, model_type, params, score) to satisfy FR-003 "fit" requirement
- [ ] T031d [US3] Implement `src/analysis/population_correlation.py` to handle FR-008: 
  - Detect unpaired real datasets (missing sample_id pairing) via `state/data_status.json` (T012a)
  - Aggregate mean topology metrics and mean thermal conductivity per source dataset
  - Perform population-level correlation analysis
  - Output results to `results/population_correlation.json`
- [ ] T032 [US3] Implement `src/analysis/bootstrap.py` for resampling to generate 95% CIs (FR-004, US3-Scenario 2)
- [ ] T033 [US3] Implement `src/analysis/correction.py` for Bonferroni or Benjamini-Hochberg FDR on p-values (FR-005, US3-Scenario 4)
- [ ] T034 [US3] Implement `src/analysis/sensitivity.py` to repeat the full pipeline (T029-T033) for thresholds 1.5x, 2.0x, 2.5x the baseline. 
  - Calculate standard deviation of the correlation coefficient across thresholds
  - **Validation Step**: Assert `std_dev <= 0.05` (SC-005 target); FAIL the run and log error if target is exceeded. This makes the success criterion measurable.
  - Output `std_dev` field in `AnalysisResult` JSON (FR-010, SC-005)
- [ ] T035 [US3] Implement `src/analysis/visualizer.py` to generate scatter plots with regression lines and save to `results/` (US3-Scenario 5)
- [ ] T036 [US3] Implement `src/analysis/reporter.py` to aggregate results into `AnalysisResult` JSON objects. 
  - **Synthetic Detection**: Check `config.yaml` flag `is_synthetic` or file hash; if true, skip hypothesis testing
  - **Artifact**: Generate `results/synthetic_warning.log` with specific message if synthetic data is detected (Plan Section 4, Section 5)
  - **Unpaired Data**: Route to T031d output if `state/data_status.json` indicates unpaired data (FR-008).
  - **Dependencies**: MUST depend on T031c (regression_unifier) to aggregate results from T031 and T031b before generating AnalysisResult JSON.

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
- **Zero Defects**: Handled in T022b with specific null/infinity values.
- **GP Regression**: Implemented in T031b, unified in T031c.
- **Sensitivity**: Outputs `std_dev` field and asserts SC-005 target in T034.
- **Data Source Gap**: No verified real dataset exists pairing defect coordinates with thermal conductivity. T017 and T036 must handle synthetic fallback gracefully; T013 must fail loudly if a real source is specified but unreachable, never substituting fake data. T031d handles population-level analysis for unpaired real data. T012a verifies data availability to resolve plan/spec contradictions.
- **Lattice Correction**: Implemented and verified in T025b.