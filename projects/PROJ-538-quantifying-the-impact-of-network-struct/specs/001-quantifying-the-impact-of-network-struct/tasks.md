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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-538-quantifying-the-impact-of-network-struct/`)
- [X] T002 Initialize Python 3.11 project with dependencies: `pandas`, `numpy`, `scipy`, `networkx`, `scikit-learn`, `matplotlib`, `seaborn`, `pydantic`, `ase`, `phonopy`, `statsmodels` in `requirements.txt`
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup `data/` directory structure: `raw/`, `processed/`, `contracts/`
- [X] T005 [P] Configure data configuration management in `code/config.py` (paths, mode selection flags) - writes only to code/config.py
- [X] T006 [P] Setup error handling infrastructure for `DataAvailabilityError` and `VoronoiFailure` in `code/utils.py` - writes only to code/utils.py; define behavior: halt with specific error code on Voronoi failure
- [X] T007 Create base Pydantic models for `AtomicSnapshot` and `DefectGraph` in `code/models.py`
- [ ] T008 Implement logging infrastructure to `data/audit_log.json` and console
- [ ] T009 Setup pytest framework with `pytest-cov` in `tests/`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Defect Network Construction (Priority: P1) 🎯 MVP

**Goal**: Download/Generate MD snapshots and construct a graph representation where nodes are atomic sites and edges connect nearest-neighbor atoms of mismatched species.

**Independent Test**: Run ingestion on a known small subset; verify NetworkX graph has correct node count and edges exist ONLY between mismatched species pairs.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Define Voronoi neighbor interface stub in `code/interfaces.py` (Explicit stub definition for T011 and T013)
- [X] T011 [US1] Stub test for Voronoi-based nearest-neighbor detection in `tests/unit/test_voronoi_neighbors.py` (Note: Depends on T010 interface stub definition)
- [X] T012 [US1] Implement `DataAudit` class structure in `code/ingest.py` to query OpenKim/Materials Cloud APIs for Cu-Ni and Au-Ag snapshots <!-- FAILED: unspecified -->
- [ ] T012.1 [US1] (Depends: T012) Sub-task: Implement variable completeness calculation and `data/completeness_report.json` generation in `code/ingest.py`. **MUST wait for T012 calculation results** and **MUST raise `DataAvailabilityError` with specific message if completeness < 90%**, halting execution (Enforces SC-003)
- [X] T013 [US1] Implement `RealDataLoader` in `code/ingest.py`: Parse MD snapshots, extract species/coordinates, check for key `thermal_conductivity_W_m_K`, and **raise `DataAvailabilityError` with specific message if missing** (Constitution Principle III) <!-- FAILED: unspecified -->
- [X] T014 [US1] Implement `SyntheticDataGenerator` in `code/synthetic.py`: Generate a statistically significant set of independent snapshots using Lennard-Jones potentials (`ase`) with unique random seeds and NVT thermalization steps
- [X] T015 [US1] Implement `ThermalConductivityEstimator` in `code/synthetic.py`: Estimate conductivity via Callaway phonon-scattering model (based on defect density/mass diff, NOT graph metrics) to avoid tautology
- [X] T016 [US1] Implement `DefectGraphBuilder` in `code/ingest.py`: Use `scipy.spatial.Voronoi` with explicit periodic boundary condition handling to define nearest neighbors; draw edges ONLY between mismatched species
- [X] T017 [US1] Add validation logic to `code/ingest.py`: Verify edge existence constraints and log specific file errors for corrupted data
- [ ] T018 [US1] Add logging for data ingestion and graph construction operations

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
- [X] T023 [US2] Implement Percolation Threshold calculation in `code/metrics.py`: Handle disconnected graphs by calculating on largest component; return NaN with warning if undefined
- [X] T024 [US2] Integrate metric extraction into the main pipeline in `code/main.py` (Prerequisite: T021-T023 output available; acts as integration checkpoint)
- [X] T025 [US2] Implement explicit verification of Bonferroni-corrected p-values in `code/metrics.py`: Ensure the family-wise error rate is controlled and flag any instance where an uncorrected p < 0.05 but the corrected p > 0.05, directly enforcing FR-006 requirements.

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
- [X] T029 [US3] Implement Bonferroni correction for p-values in `code/stats.py` (FR-006)
- [X] T030 [US3] Implement Post-hoc Power Analysis in `code/stats.py`: Report minimum detectable effect size using `statsmodels.stats.power.FTestPower` for correlation tests; flag if N < 20 (FR-007)
- [X] T031 [US3] Implement Sensitivity Analysis in `code/stats.py`: Sweep significance thresholds (0.01, 0.05, 0.10), **verify and report rank-order stability** of correlation coefficients, calculate magnitude difference, and ensure no change > 0.1 (Enforces SC-004)
- [X] T032 [US3] Implement `VisualizationEngine` in `code/viz.py`
- [X] T033 [US3] Generate scatter plots with regression lines in `code/viz.py` (300 DPI) (FR-005)
- [ ] T034 [US3] Generate correlation heatmaps in `code/viz.py` (300 DPI) (FR-005)
- [ ] T035.1 [US3] Handle edge case: N=1 (graceful exit with specific message)
- [ ] T035.2 [US3] Handle edge case: Missing metadata (skip sample and log exclusion count)
- [ ] T035.3 [US3] Handle edge case: Undefined metrics (assign NaN and flag for review)
- [ ] T037 [US3] Add unit test in `tests/unit/test_edge_cases.py` that asserts graceful exit for N=1, missing metadata, and NaN metrics (Replaces vague T035.4)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T036 [P] Documentation updates in `README.md` and `docs/`
- [ ] T037 [P] Code cleanup and refactoring in `code/`
- [ ] T038 [P] Additional unit tests for edge cases in `tests/unit/`
- [ ] T039 [P] Run `quickstart.md` validation and ensure all scripts execute without error
- [ ] T040 Generate final `data/processed/results_summary.json` with all metrics and correlation tables
- [ ] T041 Verify `contracts/` schemas match generated data structures

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
- **Critical Data Rule**: If real data fetch fails, the system MUST halt with `DataAvailabilityError`. Do NOT fall back to synthetic data automatically in the ingestion script; the `main.py` orchestrator handles the mode switch based on the audit log.
- **Synthetic Integrity**: Synthetic thermal conductivity must be derived from the Callaway model (phonon scattering), NOT from the graph metrics, to prevent tautological correlation.
- **Voronoi Handling**: Must use `scipy.spatial.Voronoi` with periodic boundary condition handling for disordered alloys.
- **Statistical Rigor**: Use `statsmodels.stats.power.FTestPower` for power analysis and explicitly check magnitude differences and rank order for sensitivity analysis.