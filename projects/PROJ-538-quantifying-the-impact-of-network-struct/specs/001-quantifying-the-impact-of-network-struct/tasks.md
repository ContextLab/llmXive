# Tasks: Quantifying the Impact of Network Structure on Heat Transport in Disordered Alloys

**Input**: Design documents from `/specs/001-quantify-network-heat-transport/`
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

## Phase 0: Data Audit & Mode Selection (NEW - Required First Step)

**Purpose**: Verify data availability and set execution mode (Real vs Synthetic) before any ingestion.

- [X] T000 [P] Implement `DataAudit` class in `code/ingest.py`: Query OpenKim API (` Name or service not known)"))] with `q=elements:Cu,Ni`) and Materials Cloud API (` Name or service not known)"))] with `q=elements:Au,Ag`) for Cu-Ni and Au-Ag snapshots. **Verification**: Generate `data/audit_log.json` with fields `query_status`, `found_count`, `metadata_completeness`. Verify specific query parameters `elements=Cu,Ni` and `elements=Au,Ag` are used and recorded. If no data found, log `DataAvailabilityError` and proceed to Synthetic Mode.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-538-quantifying-the-impact-of-network-struct/`)
- [X] T002 Initialize Python 3.11 project with dependencies: `pandas`, `numpy`, `scipy`, `networkx`, `scikit-learn`, `matplotlib`, `seaborn`, `pydantic`, `ase`, `phonopy`, `statsmodels`, `pymatgen` in `requirements.txt`
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Setup `data/` directory structure: `raw/`, `processed/`, `contracts/`
- [X] T005 [P] Configure data configuration management in `code/config.py` (paths, mode selection flags) - writes only to code/config.py
- [X] T006 [P] Setup error handling infrastructure for `DataAvailabilityError` and `VoronoiFailure` in `code/utils.py` - writes only to code/utils.py; define behavior: halt with specific error code on Voronoi failure
- [X] T007 Create base Pydantic models for `AtomicSnapshot`, `DefectGraph`, `CorrelationResult`, `SensitivityResult`, and `PowerAnalysisResult` in `code/models.py`
- [X] T008 [P] Implement logging infrastructure to `data/audit_log.json` and console. **Verification**: Verify `data/audit_log.json` is created with valid JSON structure and initial entry for T000 execution. **[Depends: T007]**
- [ ] T009 [P] Setup pytest framework with `pytest-cov` in `tests/`
- [ ] T009.1 [P] Generate `contracts/atomic_snapshot.schema.yaml`, `contracts/defect_graph.schema.yaml`, `contracts/correlation_result.schema.yaml`, `contracts/sensitivity_result.schema.yaml`, and `contracts/power_analysis.schema.yaml` based on `code/models.py` (T007). **Verification**: Verify all YAML files exist and contain valid JSON Schema definitions. **[Depends: T007]**
- [ ] T009.2 [P] (Consolidated) Ensure all schema contracts are generated in Phase 2. **Verification**: Verify `contracts/` contains all required schema files. **[Depends: T009.1]**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Defect Network Construction (Priority: P1) 🎯 MVP

**Goal**: Download/Generate MD snapshots and construct a graph representation where nodes are atomic sites and edges connect nearest-neighbor atoms of mismatched species.

**Independent Test**: Run ingestion on a known small subset; verify NetworkX graph has correct node count and edges exist ONLY between mismatched species pairs.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Define Voronoi neighbor interface stub in `code/interfaces.py` (Explicit stub definition for T011 and T013)
- [X] T011 [US1] Stub test for Voronoi-based nearest-neighbor detection in `tests/unit/test_voronoi_neighbors.py` (Note: Depends on T010 interface stub definition)
- [X] T012 [US1] Implement `DataAudit` class structure in `code/ingest.py` to query OpenKim/Materials Cloud APIs for Cu-Ni and Au-Ag snapshots. **Verification**: Verify JSON schema compliance of `data/audit_log.json` and ensure it records API query status (success/empty/fail). **[Depends: T007]** <!-- FAILED: unspecified -->
- [ ] T012.1 [US1] (Depends: T012) Sub-task: Implement variable completeness calculation and `data/completeness_report.json` generation in `code/ingest.py`. **MUST wait for T012 calculation results** and **MUST raise `DataAvailabilityError` with specific message "Completeness < 90%: <details>" if completeness < 90%**, allowing the orchestrator to catch this and switch to Synthetic Mode (Enforces SC-003). **[Depends: T012, T007, T005]**
- [ ] T013 [US1] Implement `RealDataLoader` in `code/ingest.py`: Parse MD snapshots, extract species/coordinates, check for key `thermal_conductivity_W_m_K`, and **raise `DataAvailabilityError` with specific message "Missing thermal conductivity" if missing** (Constitution Principle III). **Output**: `AtomicSnapshot` objects in `data/processed/raw_snapshots.parquet`. **[Depends: T012.1]**
- [X] T014 [US1] Implement `SyntheticDataGenerator` in `code/synthetic.py`: Generate **N=50** statistically independent snapshots using Lennard-Jones potentials (`ase`) with unique random seeds (0-49) and NVT thermalization steps. Use LJ parameters: Cu-Ni (epsilon=0.104 eV, sigma=2.56 A), Au-Ag (epsilon=0.103 eV, sigma=2.89 A). **[Depends: T007]**
- [X] T015 [US1] Implement `ThermalConductivityEstimator` in `code/synthetic.py`: Estimate conductivity via Callaway phonon-scattering model (based on defect density/mass diff, NOT graph metrics) to avoid tautology
- [X] T016 [US1] Implement `DefectGraphBuilder` in `code/ingest.py`: Use `pymatgen` or `ase` neighbors with periodic box data to define nearest neighbors via Voronoi tessellation. **CRITICAL**: Must handle Periodic Boundary Conditions explicitly using `pymatgen.analysis.sites.VoronoiNN(pbc=True)` or `ase.neighborlist.neighbor_list` with periodic box. Draw edges ONLY between mismatched species. **[Depends: T014, T013]**
- [X] T017 [US1] Add validation logic to `code/ingest.py`: Verify edge existence constraints, log specific file errors for corrupted data, and **handle edge cases (N=1, missing metadata, undefined metrics) by logging to `data/audit_log.json` with error codes and exiting gracefully**. **[Depends: T016]**
- [ ] T017.1 [US1] Validate all constructed graphs against `contracts/defect_graph.schema.yaml`. **[Depends: T017, T004]**

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (Real or Synthetic mode)

---

## Phase 4: User Story 2 - Topological Metric Extraction (Priority: P2)

**Goal**: Compute a vector of network descriptors (clustering coefficient, mean degree, degree distribution moments, percolation threshold) for each constructed defect network.

**Independent Test**: Run extraction on a synthetic graph with known properties (e.g., Erdős-Rényi) and verify metrics match theoretical expectations within < 1e-6 tolerance.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for metric calculation on known graph topologies in `tests/unit/test_metric_accuracy.py`

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement `MetricCalculator` class in `code/metrics.py`
- [X] T021 [US2] Implement calculation for Clustering Coefficient and Mean Degree in `code/metrics.py`
- [X] T022 [US2] Implement calculation for Degree Distribution Moments (mean, variance) in `code/metrics.py`
- [X] T023 [US2] Implement Percolation Threshold calculation in `code/metrics.py`: Handle disconnected graphs by calculating on largest component; return NaN with warning if undefined. **Handle edge case: undefined metrics by assigning NaN and flagging for review in `data/audit_log.json`**. **[Depends: T020]**
- [X] T024 [US2] Integrate metric extraction into the main pipeline in `code/main.py` (Prerequisite: T021-T023 output available; acts as integration checkpoint)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Correlation and Visualization (Priority: P3)

**Goal**: Correlate topological metrics with thermal conductivity, generate visualizations, and perform significance testing (Bonferroni corrected).

**Independent Test**: Run correlation on synthetic data with known linear relationship; verify Pearson/Spearman coefficients and p-values are correct.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Unit test for correlation calculation and p-value accuracy in `tests/unit/test_correlation_stats.py`

### Implementation for User Story 3

- [X] T027 [P] [US3] Implement `CorrelationAnalyzer` class in `code/stats.py`
- [X] T028 [US3] Implement Pearson and Spearman correlation analysis in `code/stats.py` (FR-004)
- [X] T029 [US3] Implement Bonferroni correction for p-values in `code/stats.py` (FR-006). **Verification**: Append warning to `data/processed/stats_report.json` if uncorrected p < 0.05 but corrected p > 0.05. **[Depends: T028]**
- [X] T030 [US3] Implement Post-hoc Power Analysis and generate `data/processed/power_analysis_report.json` in `code/stats.py`: Report minimum detectable effect size using `statsmodels.stats.power.FTestPower` for correlation tests; flag if N < 20 (FR-007). **Verification**: Verify `data/processed/power_analysis_report.json` exists, contains `minimum_detectable_effect_size` and `power` fields, and is written to disk. **[Depends: T029]**
- [X] T031 [US3] Implement Sensitivity Analysis and generate `data/processed/sensitivity_report.csv` in `code/stats.py`: Sweep significance thresholds (representative values such as standard and relaxed levels), **verify and report rank-order stability** of correlation coefficients, calculate magnitude difference, and ensure no change > 0.1 (Enforces SC-004). **Output**: `data/processed/sensitivity_report.csv` with columns `threshold`, `correlation_coefficient`, `p_value`, `rank_stability_flag`. **Verification**: Verify `data/processed/sensitivity_report.csv` exists and contains `rank_stability_flag` column with correct values. **[Depends: T030]**
- [X] T032 [US3] Implement `VisualizationEngine` in `code/viz.py`
- [X] T033 [US3] Generate scatter plots with regression lines in `code/viz.py` (300 DPI) (FR-005)
- [ ] T034 [US3] Generate correlation heatmaps in `code/viz.py` (300 DPI) (FR-005). **Verification**: Verify `data/processed/correlation_heatmap.png` exists, is 300 DPI, and contains a grid with labels. **[Depends: T032]**
- [X] T035 [US3] Add unit test in `tests/unit/test_edge_cases.py` that asserts graceful exit for N=1, missing metadata, and NaN metrics (Replaces vague T035.4). **[Depends: T017]**

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T039 [P] Documentation updates in `README.md` and `docs/`
- [ ] T040 [P] Code cleanup and refactoring in `code/`
- [ ] T041 [P] Additional unit tests for edge cases in `tests/unit/`
- [ ] T042 [P] Run `quickstart.md` validation and ensure all scripts execute without error
- [ ] T043 [P] Generate final `data/processed/results_summary.json` with all metrics and correlation tables. **[Depends: T031, T030, T033]**
- [ ] T044 [P] Verify `contracts/` schemas match generated data structures. **[Depends: T043, T009.1]**

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on T016 (Graph Construction)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on T024 (Metric Extraction)

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

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Define Voronoi neighbor interface stub in code/interfaces.py" (T010)
Task: "Stub test for Voronoi-based nearest-neighbor detection in tests/unit/test_voronoi_neighbors.py" (T011, depends on T010)

# Launch all models for User Story 1 together:
Task: "Implement DataAudit class structure in code/ingest.py" (T012)
Task: "Implement SyntheticDataGenerator in code/synthetic.py" (T014)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Data Ingestion + Graph Construction)
4. **STOP and VALIDATE**: Test US1 independently (verify edges are mismatched species only)
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
 - Developer A: User Story 1 (Ingestion/Graph)
 - Developer B: User Story 2 (Metrics)
 - Developer C: User Story 3 (Stats/Viz)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies (ensure file-level isolation as noted in T005/T006)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical Data Rule**: If real data fetch fails, the system MUST raise `DataAvailabilityError`. The `main.py` orchestrator must catch this and switch to Synthetic Mode.
- **Synthetic Integrity**: Synthetic thermal conductivity must be derived from the Callaway model (phonon scattering), NOT from the graph metrics, to prevent tautological correlation.
- **Voronoi Handling**: Must use PBC-aware Voronoi (via `pymatgen` or `ase` with periodic box) for nearest neighbors. Fallback to distance-cutoff only if PBC data is missing, with a warning.
- **Statistical Rigor**: Use `statsmodels.stats.power.FTestPower` for power analysis and explicitly check magnitude differences and rank order for sensitivity analysis.
- **Edge Cases**: N=1, missing metadata, and undefined metrics are handled within T017, T023, and T035, not as separate top-level tasks.
- **Schema Generation**: All schema contracts (correlation, sensitivity, power analysis) are generated in Phase 2 (T009.1) to avoid premature dependencies.
- **Dependency Fix**: T012.1 (Completeness Check) now depends on T012 and T007, but NOT T008 (Logging), ensuring SC-003 enforcement is not blocked by logging setup.