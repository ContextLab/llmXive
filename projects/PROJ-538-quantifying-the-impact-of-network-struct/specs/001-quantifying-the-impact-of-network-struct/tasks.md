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

**Purpose**: Project initialization and basic structure. **Note**: Phase 0 (Data Audit) depends on these tasks completing first.

- [X] T001.1 Create directory structure: `mkdir -p projects/PROJ-538-quantifying-the-impact-of-network-struct/{code,data/raw,data/processed,contracts,tests/unit,tests/contract}`. **Execute from repo root**. **[Depends: None]**
- [X] T002 Initialize Python 3.11 project with dependencies: `pandas`, `numpy`, `scipy`, `networkx`, `scikit-learn`, `matplotlib`, `seaborn`, `pydantic`, `ase`, `phonopy`, `statsmodels`, `pymatgen`, `requests` in `requirements.txt`. **[Depends: T001.1]**
- [X] T003.1 Initialize Ruff config: `ruff init` and configure `ruff.toml` with `target-version = "py311"`. **[Depends: T001.1]**
- [X] T004.1 Create data directories: `mkdir -p data/raw data/processed contracts`. **[Depends: T001.1]**
- [X] T005 [P] Configure data configuration management in `code/config.py` (paths, mode selection flags) - writes only to code/config.py. **[Depends: T001.1]**
- [X] T006 [P] Setup error handling infrastructure for `DataAvailabilityError` and `VoronoiFailure` in `code/utils.py` - writes only to code/utils.py; define behavior: halt with specific error code on Voronoi failure. **[Depends: T001.1]**
- [X] T007 Create base Pydantic models for `AtomicSnapshot`, `DefectGraph`, `CorrelationResult`, `SensitivityResult`, and `PowerAnalysisResult` in `code/models.py`. **[Depends: T001.1]**
- [X] T008 [P] Setup logging infrastructure in `code/logging.py` and `code/utils.py`: Initialize `logging` module to write to `data/audit_log.json` and console. **[Depends: T001.1]**
- [X] T009 [P] Setup pytest framework with `pytest-cov` in `tests/`. **[Depends: T001.1]**
- [X] T009.1 [P] Generate `contracts/atomic_snapshot.schema.yaml`, `contracts/defect_graph.schema.yaml`, `contracts/correlation_result.schema.yaml`, `contracts/sensitivity_result.schema.yaml`, and `contracts/power_analysis.schema.yaml` based on `code/models.py` (T007). **Verification**: Verify all YAML files exist and contain valid JSON Schema definitions. **[Depends: T007]**
- [X] T009.2 [P] Create `scripts/generate_schemas.py` that reads `code/models.py` and writes JSON Schema to `contracts/*.yaml`, then run it to validate existence of all files in `contracts/`. **Verification**: Verify `contracts/` contains all required schema files. If missing, raise error. **[Depends: T009.1]**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 0: Pre-Flight Data Audit (Required First Step - Runs AFTER Phase 1)

**Purpose**: Verify data availability and set execution mode (Real vs Synthetic) before any ingestion. **Note**: This phase requires Phase 1 infrastructure (directories, logging) to be initialized first. **Execution Order**: Run T000 only after T001.1 and T008 are complete.

- [X] T000 [US1] Implement `DataAudit` class in `code/ingest.py`: **Check for local file `data/raw/real_snapshots.parquet` ONLY**. **Logic**: 
  1. If file exists AND contains ≥ 20 valid snapshots with `thermal_conductivity` metadata: Set mode to **Real**.
  2. If file missing OR count < 20 OR metadata incomplete: Log `DataAvailabilityError` to `data/audit_log.json` and set mode to **Synthetic**.
  **Constraint**: Do NOT query OpenKim/Materials Cloud APIs (Plan override: No verified source exists). This task must NOT attempt external fetches. **[Depends: T001.1, T008]**

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T010 [P] [US1] Define Voronoi neighbor interface stub in `code/interfaces.py` (Explicit stub definition for T011 and T013)
- [X] T011 [US1] Stub test for Voronoi-based nearest-neighbor detection in `tests/unit/test_voronoi_neighbors.py` (Note: Depends on T010 interface stub definition)

**Checkpoint**: Foundational tasks complete. Proceed to User Story 1.

---

## Phase 3: User Story 1 - Data Ingestion and Defect Network Construction (Priority: P1) 🎯 MVP

**Goal**: Download/Generate MD snapshots and construct a graph representation where nodes are atomic sites and edges connect nearest-neighbor atoms of mismatched species.

**Independent Test**: Run ingestion on a known small subset; verify NetworkX graph has correct node count and edges exist ONLY between mismatched species pairs.

### Implementation for User Story 1

- [X] T012 [US1] **REMOVED** (Consolidated into T000).
- [X] T013 [US1] **Conditional Stub for Real Data**. Implement `RealDataLoader` in `code/ingest.py`: 
  1. **Check**: If `data/raw/real_snapshots.parquet` exists and is valid (per T000 audit), parse MD snapshots, extract species/coordinates, check for key `thermal_conductivity_W_m_K`.
  2. **Failure Path**: If file missing or invalid (but T000 expected Real Mode due to config), raise `DataAvailabilityError` immediately with **code E_DATA_MISSING** and message "Real data file missing or incomplete; switching to Synthetic". **Verify that Orchestrator (T045) catches this specific error code and switches to Synthetic Mode (T014)**. This intentional error triggers the Orchestrator to switch to Synthetic Mode (T014).
  3. **Success Path**: If file exists and valid, return parsed data.
  **Note**: This task is a stub for future Real Mode support. In current "Synthetic Validation Mode", T000 will likely trigger Synthetic, making T013 raise an error (as designed) to confirm the fallback path. **[Depends: T000 - Conditional]**
- [X] T014 [US1] Implement `SyntheticDataGenerator` in `code/synthetic.py`: Generate **N=50** statistically independent snapshots using Lennard-Jones potentials (`ase`) with unique random seeds (-49) and NVT thermalization steps. Use LJ parameters: Cu-Ni (epsilon=0.104 eV, sigma=2.56 A), Au-Ag (epsilon=0.103 eV, sigma=2.89 A). **CRITICAL**: **Embed a known ground truth correlation (r=0.6) between defect density and thermal conductivity** as defined in Plan.md "Validation Strategy". **Verification**: Verify that running the generator with seed=42 produces a dataset where the correlation between defect density and thermal conductivity is recoverable within ±0.05 of 0.6. **[Depends: T000 - Conditional]**
- [X] T015 [US1] Implement `ThermalConductivityEstimator` in `code/synthetic.py`: Estimate conductivity via Callaway phonon-scattering model (based on defect density/mass diff, NOT graph metrics) to avoid tautology. **Per Plan.md "Synthetic Override", derive conductivity from Callaway model (defect density) to avoid tautology, NOT from graph metrics.** **Validation Context**: This step is critical for the "Synthetic Validation Mode" to ensure the recovered correlation matches the known ground truth (r=0.6) defined in the Plan. **[Depends: T014]**
- [X] T016a [US1] **Conditional**: Implement `DefectGraphBuilder` for Real Data in `code/ingest.py`: Use `pymatgen` or `ase` neighbors with periodic box data to define nearest neighbors via Voronoi tessellation. **CRITICAL**: Must handle Periodic Boundary Conditions explicitly using `pymatgen.analysis.sites.VoronoiNN(pbc=True)` or `ase.neighborlist.neighbor_list` with periodic box. Draw edges ONLY between mismatched species. **Execute ONLY if T000 detected Real Mode AND T013 succeeded**. **[Depends: T013, Mode=Real]**
- [X] T016b [US1] **Conditional**: Implement `DefectGraphBuilder` for Synthetic Data in `code/ingest.py`: Use `pymatgen` or `ase` neighbors with periodic box data to define nearest neighbors via Voronoi tessellation. **CRITICAL**: Must handle Periodic Boundary Conditions explicitly using `pymatgen.analysis.sites.VoronoiNN(pbc=True)` or `ase.neighborlist.neighbor_list` with periodic box. Draw edges ONLY between mismatched species. **Execute ONLY if T000 detected Synthetic Mode**. **[Depends: T014, Mode=Synthetic]**
- [X] T017 [US1] Add validation logic to `code/ingest.py`: Verify edge existence constraints, log specific file errors for corrupted data, and **handle edge cases (N=1, missing metadata, undefined metrics) by logging to `data/audit_log.json` with error codes and exiting gracefully**. **[Depends: T016a OR T016b]**
- [X] T017.1 [US1] Validate all constructed graphs against `contracts/defect_graph.schema.yaml`. **[Depends: T017, T009.1]**

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
- [X] T029 [US3] Implement Bonferroni correction for p-values in `code/stats.py` (FR-006). **Mandate**: **Calculate Bonferroni-corrected p-values** for all tests. **Artifact**: **Update `CorrelationResult` schema** to include `corrected_p_value` and **write the corrected values to `data/processed/correlation_results.json`**. **Verification**: Append warning to `data/processed/stats_report.json` if uncorrected p < 0.05 but corrected p > 0.05. **[Depends: T028]**
- [X] T030 [US3] Implement Post-hoc Power Analysis and generate `data/processed/power_analysis_report.json` in `code/stats.py`: Report minimum detectable effect size using `statsmodels.stats.power.FTestPower` for correlation tests; flag if N < 20 (FR-007). **Verification**: Verify `data/processed/power_analysis_report.json` exists, contains `minimum_detectable_effect_size` and `power` fields, and is written to disk. **[Depends: T029]**
- [X] T031 [US3] Implement Sensitivity Analysis and generate `data/processed/sensitivity_report.csv` in `code/stats.py`: Sweep significance thresholds **{0.01, 0.05, 0.10}**, **calculate magnitude difference** for each threshold sweep, **enforce the 0.1 constraint** (SC-004), and **flag the result as 'PASS' or 'FAIL'** in the CSV. **Output**: `data/processed/sensitivity_report.csv` with columns `threshold`, `correlation_coefficient`, `p_value`, `magnitude_difference`, `rank_stability_flag`, `consistency_flag`. **Verification**: Verify `data/processed/sensitivity_report.csv` exists and contains `consistency_flag` column with correct PASS/FAIL values based on the 0.1 threshold. **[Depends: T030]**
- [X] T032 [P] [US3] Implement `VisualizationEngine` in `code/viz.py`
- [X] T033 [US3] Generate scatter plots with regression lines in `code/viz.py` (300 DPI) (FR-005)
- [X] T034 [US3] Generate correlation heatmaps in `code/viz.py` (300 DPI) (FR-005). **Logic**: If Real Data exists, generate heatmap. If Synthetic Mode is active, generate heatmap with title "Methodological Validation: Synthetic Data". **Verification**: Verify `data/processed/correlation_heatmap.png` exists, is 300 DPI, and contains a grid with labels. **[Depends: T032, T029]**
- [X] T035 [US3] Add unit test in `tests/unit/test_edge_cases.py` that asserts graceful exit for N=1, missing metadata, and NaN metrics (Replaces vague T035.4). **[Depends: T017]**

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [X] T039 [P] Documentation updates in `README.md` and `docs/`
- [X] T040 [P] Code cleanup and refactoring in `code/`
- [X] T041 [P] Additional unit tests for edge cases in `tests/unit/`
- [X] T042 [P] Run `quickstart.md` validation and ensure all scripts execute without error
- [X] T043 [P] Generate final `data/processed/results_summary.json` with all metrics and correlation tables. **[Depends: T031, T030, T033, T034]**
- [X] T044 [P] Verify `contracts/` schemas match generated data structures. **[Depends: T043, T009.1]**

---

## Phase 7: Execution & Reporting (NEW - Required for Final Output)

**Purpose**: Execute the full pipeline, aggregate results, and generate the final research report.

- [X] T045 [P] Implement `PipelineOrchestrator` in `code/main.py`: **Execute Logic**:
  1. Run T000 (DataAudit).
  2. **IF** T000 triggers Synthetic Mode (file missing or count < 20): **SKIP T013**. Execute T014 (Synthetic Data) -> T016b (Synthetic Graph) -> T024 -> T028 -> T031 -> T033/T034.
  3. **ELSE IF** T000 finds valid Real Data: Execute T013 (Real Data). **IF T013 raises `DataAvailabilityError` (e.g., file corrupt)**: Catch error, fallback to T014 (Synthetic). **IF T013 succeeds**: Execute T016a (Real Graph) -> T024 -> T028 -> T031 -> T033/T034.
  4. **Note**: T016a and T016b are mutually exclusive. Only one path is taken based on T000/T013 result.
  **[Depends: T013, T014, T016a, T016b, T020, T027, T028, T032]**
- [X] T046 [P] Create `run_pipeline.sh` script to execute the full pipeline with `python code/main.py --mode auto`. **[Depends: T045]**
- [X] T047 [P] Implement `ReportGenerator` in `code/reports.py`: Aggregate `data/processed/*.json` and `data/processed/*.png` into a single `data/processed/final_report.md`. **[Depends: T043, T031]**
- [X] T048 [P] Verify final report contains: Ground truth correlation (Synthetic Mode) or Data Source URL (Real Mode), Recovered Correlation, Power Analysis Result, Sensitivity Stability Flag, and Visualizations. **[Depends: T047]**

---

## Phase 8: Revision & Robustness (NEW - Addressing Review Concerns)

**Purpose**: Address specific reviewer concerns regarding data integrity, edge case handling, and validation rigor.

- [ ] T049 [US1] **Data Integrity Check**: Implement a strict checksum validation in `code/ingest.py` for the synthetic data generator output. **Verify that running T014 with seed=42 produces a file with hash X (pre-calculated)**. **If hash != X, raise `DataIntegrityError`**. **[Depends: T014]**
- [ ] T050 [US2] **Metric Stability Test**: Add a unit test in `tests/unit/test_metric_stability.py` that verifies the `MetricCalculator` (T020) produces identical results for the same graph input across multiple runs, ensuring no floating-point non-determinism affects the correlation analysis. **[Depends: T020]**
- [ ] T051 [US3] **Correlation Robustness Check**: Enhance `code/stats.py` to perform a bootstrap resampling (1000 iterations) of the correlation coefficient for the primary metric. If the 95% confidence interval includes zero despite the p-value < 0.05, flag this as "Unstable" in `data/processed/sensitivity_report.csv`. **[Depends: T028]**
- [ ] T052 [US1] **Graph Topology Sanity Check**: Implement a pre-analysis check in `code/ingest.py` to ensure the generated defect graphs are not fully disconnected or fully connected (which would trivialize the analysis). If > 90% of graphs are disconnected, log a `TopologyAnomaly` warning and halt, requiring a review of the synthetic generator parameters. **[Depends: T016b]**
- [ ] T053 [US3] **Visual Verification Task**: Add a manual review step in `code/reports.py` to generate a "sanity check" PDF containing the first 5 scatter plots and their corresponding raw data points. This ensures the visualization engine (T032) is not plotting NaNs or empty arrays. **[Depends: T033]**

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Pre-Flight (Phase 0)**: Depends on Phase 1 (T001.1, T008) for infrastructure - **Must run after Phase 1 completes**
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Execution (Phase 7)**: Depends on all implementation phases being complete
- **Revision (Phase 8)**: Depends on Phase 7 execution to identify specific anomalies; can run in parallel with Phase 7 implementation if concerns are known a priori.

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
- Phase 8 tasks can be implemented in parallel with Phase 7 execution tasks.

---

## Parallel Example: User Story 1

```bash
# Launch all models for User Story 1 together:
Task: "Define Voronoi neighbor interface stub in code/interfaces.py" (T010)
Task: "Implement SyntheticDataGenerator in code/synthetic.py" (T014)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 0: Pre-Flight Data Audit (T000)
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1 (Data Ingestion + Graph Construction)
5. **STOP and VALIDATE**: Test US1 independently (verify edges are mismatched species only)
6. Deploy/demo if ready

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
- **Critical Data Rule**: If T000 (DataAudit) triggers Synthetic Mode, T013 (RealDataLoader) is SKIPPED. T014 (SyntheticDataGenerator) is executed instead. If T000 expects Real but T013 fails, fallback to T014.
- **Synthetic Integrity**: Synthetic thermal conductivity must be derived from the Callaway model (phonon scattering), NOT from the graph metrics, to prevent tautological correlation.
- **Voronoi Handling**: Must use PBC-aware Voronoi (via `pymatgen` or `ase` with periodic box) for nearest neighbors. Fallback to distance-cutoff only if PBC data is missing, with a warning.
- **Statistical Rigor**: Use `statsmodels.stats.power.FTestPower` for power analysis and explicitly check magnitude differences and rank order for sensitivity analysis. **Sweep values: {0.01, 0.05, 0.10}**.
- **Edge Cases**: N=1, missing metadata, and undefined metrics are handled within T017, T023, and T035, not as separate top-level tasks.
- **Schema Generation**: All schema contracts (correlation, sensitivity, power analysis) are generated in Phase 2 (T009.1) to avoid premature dependencies.
- **Dependency Fix**: T012.1 (Completeness Check) now depends on T012 and T007, but NOT T008 (Logging), ensuring SC-003 enforcement is not blocked by logging setup.
- **Dual-Mode Logic**: T013 and T014 are mutually exclusive branches. T016a and T016b depend on the result of whichever branch is active.
- **Execution Order**: Ensure T045 (Orchestrator) is implemented last in the code phase, but T045 is the final task in the task list to ensure all components are ready.
- **Phase 0 Dependency**: T000 depends on T001.1 and T008. Phase 0 is a "Pre-Flight" step that runs after Setup but before User Stories.
- **Plan Override**: T000 does NOT query external APIs. It relies solely on local file existence check as per Plan.md "Spec Assumption Override".
- **Revision Integrity**: Phase 8 tasks (T049-T053) are mandatory to address reviewer concerns regarding data integrity, metric stability, and statistical robustness. They must be completed before the final `human_input_needed` transition.