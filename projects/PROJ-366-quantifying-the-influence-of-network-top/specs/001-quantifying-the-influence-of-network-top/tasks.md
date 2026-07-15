# Tasks: Quantifying the Influence of Network Topology on Thermal Conductivity in Amorphous Silicon

**Input**: Design documents from `/specs/001-topology-thermal-conductivity/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create code directories: `code/`, `code/ingest/`, `code/simulation/`, `code/metrics/`, `code/model/`, `code/analysis/`
- [X] T001b [P] Create data directories: `data/`, `data/raw/`, `data/processed/graphs/`, `data/processed/conductivities/`, `data/processed/model_outputs/`
- [X] T001c [P] Create test directories: `tests/`, `tests/contract/`, `tests/integration/`, `tests/unit/`
- [X] T002 Initialize Python 3.11 project with pinned dependencies in `requirements.txt` (numpy, scipy, pandas, torch-cpu, torch-geometric, ase, statsmodels, scikit-learn, yaml, pytest)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `.pre-commit-config.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Implement configuration management in `code/config.py` (seeds, paths, hyperparameters)
- [X] T006 [P] Setup logging infrastructure in `code/__init__.py` with file handlers for pipeline stages
- [ ] T007 Create base schema validators in `contracts/` (thermal_sample.schema.yaml, atomic_graph.schema.yaml, gnn_output.schema.yaml)
- [ ] T008 Implement contract test framework in `tests/contract/test_schemas.py` to validate against `contracts/` schemas
- [X] T009 Create simulation configuration file `code/simulation/config.yaml` (LAMMPS version, SW potential file, timestep, thermostat settings)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Graph Construction (Priority: P1) 🎯 MVP

**Goal**: Ingest pre-equilibrated amorphous silicon configurations and construct atomic graphs with a bond cutoff.

**Independent Test**: Run ingestion on a single sample file; verify output graph has expected node count and edge distribution matching the specified cutoff distance..

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for `AtomicGraph` schema in `tests/contract/test_schemas.py`
- [ ] T011 [P] [US1] Unit test for bond cutoff logic (3.0 Å) in `tests/unit/test_graph_builder.py`
- [ ] T016b [P] [US1] Unit test for node-degree stats output in `tests/unit/test_graph_builder.py` (verifies `node_degree_stats.json` schema exists)

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/ingest/graph_builder.py` to load XYZ files and construct `AtomicGraph` objects using `ase` with 3.0 Å cutoff (FR-001) <!-- FAILED: unspecified -->
- [X] T013 [US1] Implement `code/ingest/sample_generator.py` to fetch or generate pre-equilibrated samples (handling missing data error as per Edge Case)
- [X] T014 [US1] Add error handling for corrupted/missing input files in `code/ingest/graph_builder.py`: log specific error code 'ERR-001' and halt execution
- [~] T015 [US1] Implement graph serialization to `data/processed/graphs/` (pickle/parquet) with checksums
- [ ] T016 [US1] Generate node-degree distribution stats: output `data/processed/graphs/node_degree_stats.json` containing the calculated mode of the distribution and verify it falls within the expected range for amorphous silicon dynamically (no hard-coded target values in test logic).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Topological Metric Extraction and Green-Kubo Baseline (Priority: P2)

**Goal**: Compute topological metrics and run Green-Kubo simulations to generate ground-truth thermal conductivity.

**Independent Test**: Process a single sample, extract metrics, run Green-Kubo (2 cores, ≤12h), verify conductivity falls within literature range and simulation converges.

### Tests for User Story 2

- [X] T018 [P] [US2] Contract test for `ThermalSample` schema in `tests/contract/test_schemas.py` <!-- FAILED: unspecified -->
- [X] T019 [P] [US2] Unit test for metric extraction (degree, clustering, shortest-path) in `tests/unit/test_metrics.py`
- [X] T020 [P] [US2] Integration test for Green-Kubo convergence check (relative change < 1%) in `tests/integration/test_pipeline.py`

### Implementation for User Story 2

- [X] T021 [P] [US2] Implement `code/metrics/topology_extractor.py` to compute degree, clustering coefficient, and shortest-path stats per atom (FR-002)
- [ ] T022 [US2] Implement `code/simulation/green_kubo.py` wrapper to run LAMMPS Green-Kubo simulations using SW potential on 2 CPU cores (FR-003). Note: Depends on Phase 3 outputs, parallel only to T021 within Phase 4. <!-- FAILED: unspecified -->
- [~] T023 [US2] Implement convergence detection logic (relative change in heat current autocorrelation < 1% in final segment): update `ThermalSample` metadata JSON with `converged: false` if failed
- [~] T024 [US2] Implement outlier detection for extreme topological defects (>15% atoms with coord <3 or >6): write excluded IDs to `data/processed/graphs/excluded_samples.json` IF `config.yaml` flag `enforce_exclusion` is true; otherwise log warning. Downstream tasks (T033, T033a, T035) MUST filter against this file if it exists.
- [~] T025 [US2] Save `ThermalSample` objects (graph + conductivity + metadata) to `data/processed/conductivities/` with checksums
- [~] T026 [US2] Verify computed thermal conductivity output file exists and contains a value within a configurable range defined in `config.yaml` (default - W/mK): output `data/processed/conductivities/convergence_report.json`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - GNN Training and Topology-Conductivity Correlation (Priority: P3)

**Goal**: Train GNN on extracted graphs, extract feature importance, and perform correlation analysis.

**Independent Test**: Train on N samples (N=2 for Plan feasibility, N≥10 for Spec statistical power); verify model converges, and correlation results are generated.

**⚠️ CRITICAL CONSTRAINT**: Spec SC-004 requires N≥10. If N < 10, the pipeline MUST LOG A WARNING regarding statistical power but PROCEED with the Plan's N=2 proof-of-concept. Do NOT halt.

### Tests for User Story 3

- [X] T028 [P] [US3] Contract test for `GNNOutput` schema in `tests/contract/test_schemas.py`
- [X] T029 [P] [US3] Unit test for Pearson correlation analysis and Bonferroni correction in `tests/unit/test_lmm_analysis.py`
- [X] T029b [P] [US3] Unit test for LMM analysis (statsmodels) in `tests/unit/test_lmm_analysis.py`

### Implementation for User Story 3

- [ ] T035 [US3] Implement Statistical Power Check: Load sample count N from `data/processed/conductivities/` (after T024 filtering). If N < 10, write `data/processed/model_outputs/power_analysis.json` with status "INSUFFICIENT_POWER" and log a WARNING. If 2 <= N < 10, proceed to T030-T034. If N < 2, exit with code 1.
- [X] T030 [US3] Implement `code/model/gnn.py` (2-layer GNN, <1M params) to predict **Static Scattering Potential** (a topology-derived proxy) from atomic graph features, as per Plan (to avoid ill-posed heat flux mappings). Note: This proxy serves as the target for the Spec's FR-004 intent.
- [ ] T031 [US3] Implement `code/model/trainer.py` with convergence check (loss change <1e-4 for 5 epochs) and comparison against linear regression baseline (FR-004, SC-002)
- [~] T032 [US3] Implement feature importance extraction (SHAP or similar) from trained GNN
- [X] T033 [US3] Implement `code/analysis/lmm_analysis.py` to perform **Linear Mixed-Effects Model (LMM)** analysis (per Plan Summary) between topological metric variance and global thermal conductivity for the N=2 proof-of-concept.
- [ ] T033a [US3] Implement **Pearson correlation analysis** (per Spec FR-005) between feature importance and global thermal conductivity as a supplementary analysis, outputting results to `data/processed/model_outputs/correlation_pearson.json`.
- [ ] T034 [US3] Implement Pearson correlation significance testing with Bonferroni correction (FR-006, SC-001) for T033a: output `data/processed/model_outputs/correlation_pearson_corrected.json` with r, p-value, and interpretation
- [~] T036 [US3] Save LMM coefficients (from T033), correlation results (r, p-value from T033a), and interpretation to `data/processed/model_outputs/`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T037 [P] Update `README.md` with pipeline overview and execution instructions
- [~] T038 Run full integration test on representative samples to verify end-to-end pipeline within 6-hour limit (SC-005)
- [ ] T039 Verify all checksums in `data/checksums.json` match generated artifacts
- [~] T040 [P] Add documentation for `contracts/` schemas and data models
- [~] T041 Run `quickstart.md` validation to ensure all prerequisites and steps are correct

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires US1 output (graphs)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires US1 (graphs) and US2 (conductivity labels)

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

### Specific Task Dependencies

- **T035** (Power Check) MUST run **before** T030, T031, T032, T033, T033a, T034, T036.
- **T024** (Outlier Exclusion) MUST run **before** T035 to ensure the sample count N is accurate after filtering.
- **T033** (LMM) and **T033a** (Pearson) are independent but both depend on T030-T032 (Model training).
- **T036** depends on T033 (for LMM coefficients) and T034 (for Pearson results).

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for AtomicGraph schema in tests/contract/test_schemas.py"
Task: "Unit test for bond cutoff logic in tests/unit/test_graph_builder.py"
Task: "Unit test for node-degree stats output in tests/unit/test_graph_builder.py"

# Launch all models for User Story 1 together:
Task: "Implement graph_builder.py"
Task: "Implement sample_generator.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
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
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CPU Constraint**: All tasks must run on a limited number of CPU cores, limited RAM, and no GPU. Green-Kubo limited to h, full pipeline to a reduced duration.
- **Data Integrity**: No synthetic data generation for inputs; use real datasets or clearly state gaps.
- **Spec vs Plan Conflict Resolution**:
 - **Sample Size**: Spec requires N≥10, Plan uses N=2. T035 implements a warning for N<10 but proceeds (Plan's path).
 - **Analysis Method**: Spec requires Pearson (FR-005), Plan requires LMM. T033 implements LMM, T033a implements Pearson. Both are executed.
 - **GNN Target**: Spec requires heat flux (FR-004), Plan requires Static Scattering Potential. T030 implements Static Scattering Potential as a proxy.
- **Configuration**: Use `config.yaml` to control optional behaviors (e.g., outlier exclusion) to preserve Spec flexibility.