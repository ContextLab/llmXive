# Tasks: Quantifying the Impact of Network Structure on Heat Transport in Amorphous Silicon

**Input**: Design documents from `/specs/001-quantify-heat-transport/`
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

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-279-quantifying-the-impact-of-network-struct/`)
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (ase, networkx, scikit-learn, pandas, numpy, matplotlib, requests, tqdm, pyyaml)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes Data Independence Validation (US-4) and Mode Selection logic definitions.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. Note: Logic is defined here, but execution occurs in Phase 3 after data ingestion.

- [ ] T004 Setup `data/raw/` and `data/processed/` directories with `.gitkeep`
- [ ] T005 [P] Implement `state/` YAML management for artifact checksums and versioning (Constitution Principle V)
- [ ] T006 [P] Create base `AtomicConfiguration` dataclass in `code/models/atomic_config.py`
- [ ] T007 [P] **Definition Only**: Implement `validation.py` logic for data independence, source, and convergence checks (FR-006, FR-007, Constitution Principle VI). **Output: NONE (Execution deferred to Phase 3, T007-exec)**. This task defines the logic but does not run it, as the input data (downloaded trajectories) does not exist yet.
- [ ] T007b [P] **Definition Only**: Implement `mode_selector.py` logic to check for pre-calculated VDOS/k availability and set execution mode (Full vs. Structure-Only) *before* pipeline start. **Output: NONE (Execution deferred to Phase 3, T007b-exec)**. This task defines the logic but does not run it.
- [ ] T008 Create `validation_utils.py` for checksum verification and file integrity checks (Constitution Principle III)
- [ ] T009 Configure logging infrastructure to output to `logs/analysis.log` and stdout
- [ ] T010 Configure environment configuration management (loading `cutoff_radius`, `zenodo_url` from env vars)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion, Validation, and Graph Construction (Priority: P1) 🎯 MVP

**Goal**: Download pre-existing MD trajectories of amorphous silicon (a-Si), validate them against independence and size constraints, and convert valid trajectories into graph representations.

**Independent Test**: Verify successful download, checksum match, validation exclusion of invalid configs, and construction of graphs only for validated configurations.

### Tests for User Story 1

- [ ] T011 [P] [US1] Unit test for checksum verification in `tests/unit/test_validation_utils.py`
- [ ] T012 [P] [US1] Unit test for graph construction with known coordinates in `tests/unit/test_graph_builder.py`
- [ ] T013 [P] [US1] Integration test for end-to-end download, validation, and graph build in `tests/integration/test_download_graph.py`

### Implementation for User Story 1

- [ ] T014 [P] [US1] Implement `download.py` to fetch trajectories from Zenodo/HuggingFace with checksum verification (FR-001)
- [ ] T007-exec [US1] **Execution of Validation**: Execute `validation.py` (defined in T007) on the downloaded data in `data/raw/`. **Input**: `data/raw/`. **Output**: `data/processed/validation_report.json` containing:
  - `excluded_configs`: list of configuration IDs excluded from analysis.
  - `reasons`: dictionary mapping each excluded ID to a string reason (e.g., "Size < 1000 atoms", "Source not independent").
  - `validated_configs`: list of configuration IDs passing checks.
  (FR-006, FR-007, Constitution Principle VI)
- [ ] T007b-exec [US1] **Execution of Mode Selection**: Execute `mode_selector.py` (defined in T007b) on the downloaded data. **Input**: `data/raw/`. **Output**: `data/processed/mode_config.json` indicating 'Full' or 'Structure-Only' mode.
- [ ] T015 [US1] **Execution of Sensitivity Analysis**: Implement the sensitivity analysis loop in `graph_builder.py` that calls the builder logic for radii {2.8, 3.0, 3.2} Å. **Constraint**: Run this loop **ONLY** on the `validated_configs` list generated by T007-exec. **Generate `data/processed/sensitivity_report.json`** containing a table of cutoff radius vs. average degree and component count (FR-002).
- [ ] T016 [US1] Add validation logic to detect disconnected components and log warnings (Spec US-1, Scenario 3)
- [ ] T017 [US1] Handle edge cases: corrupted files (abort with error), unexpected coordination numbers (flag/drop)
- [ ] T018 [US1] Save constructed graphs and metadata to `data/processed/graphs/` in JSON/GraphML format

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Topological and Vibrational Descriptor Calculation (Priority: P2)

**Goal**: Compute specific topological metrics (ring statistics, bond orientational order parameters, clustering coefficients) AND vibrational spectral descriptors (VDOS, participation ratios) for each configuration.

**Independent Test**: Calculate descriptors on a known crystal structure and compare against theoretical expectations; verify output format.

### Tests for User Story 2

- [ ] T019 [P] [US2] Unit test for ring statistics calculation on a simple lattice in `tests/unit/test_descriptors.py`
- [ ] T020 [P] [US2] Unit test for Steinhardt Q6 parameter calculation in `tests/unit/test_descriptors.py`
- [ ] T021 [P] [US2] Integration test for full descriptor pipeline on a small sample in `tests/integration/test_descriptor_pipeline.py`

### Implementation for User Story 2

- [ ] T022 [P] [US2] Implement `descriptors.py` with `calculate_ring_statistics()` (distribution of ring sizes 3-10) (FR-003)
- [ ] T023 [US2] Implement `calculate_steinhardt_parameters()` (Q6) and clustering coefficients (FR-003)
- [ ] T024 [US2] **VDOS Handling**: Implement `load_vdos()` and `calculate_participation_ratios()`. **Constraint**: Attempt to load pre-calculated VDOS data from the dataset. If missing for a configuration, **log `ERR-VDOS-MISSING` and EXCLUDE the configuration** from the final descriptor dataset. Do NOT calculate VDOS internally (Plan Constraint). **Generate `data/processed/vdos_missing_report.json`** listing excluded Config IDs and reasons to satisfy the "no silent drift" principle for FR-003 (Plan: Structure-Only Mode, FR-003).
- [ ] T025 [US2] Aggregate all descriptors into a structured CSV/JSON dataset linking Config ID to metrics vector (only for configs with complete data)
- [ ] T026 [US2] Handle missing thermal conductivity values: skip configuration and log count (Spec Edge Cases)
- [ ] T027 [US2] Save processed descriptors to `data/processed/descriptors.csv`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Correlation and Visualization (Priority: P3)

**Goal**: Perform statistical analysis (Ridge regression, non-linear model comparison) to correlate descriptors with thermal conductivity, validate via cross-validation, and generate visualizations.

**Independent Test**: Run regression on synthetic data with known relationship; verify model recovers coefficients and R² within margin.

### Tests for User Story 3

- [ ] T028 [P] [US3] Unit test for cross-validation logic (LOOCV vs 5-fold switch) in `tests/unit/test_models.py`
- [ ] T029 [P] [US3] Unit test for feature importance extraction and p-value calculation in `tests/unit/test_models.py`
- [ ] T030 [P] [US3] Integration test for full regression pipeline on synthetic data in `tests/integration/test_regression.py`

### Implementation for User Story 3

- [ ] T031 [P] [US3] Implement `models.py` with Ridge Regression and Random Forest/Kernel Ridge (FR-004)
- [ ] T032 [US3] Implement dimensionality reduction (PCA/Lasso) **as a preprocessing step for small N** to prevent overfitting, followed by stability selection (Plan: Complexity Tracking)
- [ ] T033 [US3] Implement cross-validation logic: 5-fold if N ≥ 30, else LOOCV (FR-004, Spec US-3, Scenario 1)
- [ ] T034 [US3] Calculate and log mean R², std dev, and p-values for top 3 features (FR-004, Spec US-3, Scenario 1)
- [ ] T035 [US3] Implement `viz.py` to generate scatter plot (top predictor vs. k) with regression line and Pearson r (FR-005)
- [ ] T036 [US3] Generate feature importance bar chart with error bars (std dev across folds) (FR-005)
- [ ] T037 [US3] Implement Tiered Execution logic: if k/VDOS missing, skip regression, **Update `data/processed/results/hypothesis_status.json`**. 
  - **H-001/H-002**: Mark 'UNTESTABLE' if regression is skipped.
  - **H-003**: Mark 'TESTED' if ring statistics were successfully computed (Structure-Only Mode OK).
  - **H-004**: Mark 'TESTED' if topological feature importance was computed (Structure-Only Mode OK).
  - The JSON must contain keys H-001 through H-004, with values 'TESTED', 'UNTESTABLE', or 'FAILED', and a 'reason' field for non-TESTED statuses (Plan: Summary).
- [ ] T038 [US3] Save results (metrics, plots) to `data/processed/results/` and update `state/`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Data Independence Verification (Priority: P1)

**Goal**: Verify that thermal conductivity target values are from an independent source and converged to thermodynamic limit.

**Independent Test**: Verify metadata explicitly states source method and system size.

### Tests for User Story 4

- [ ] T039 [P] [US4] Unit test for metadata validation logic in `tests/unit/test_validation.py`

### Implementation for User Story 4

- [ ] T040 [P] [US4] **Integrate** `validation.py` and `mode_selector.py` into the main pipeline entry point (`main.py`) to execute *after* download (T014) and *before* graph construction (T015).
- [ ] T041 [US4] Implement logic to exclude systems < 1000 atoms from hypothesis testing (Constitution Principle VI)
- [ ] T042 [US4] Log specific warnings for "Preliminary - Unverified Convergence" if small systems are used for descriptive stats only
- [ ] T043 [US4] Ensure `main.py` enforces the "Tiered Execution" mode based on validation results (Mode Selection from T007b-exec)

**Checkpoint**: Data independence and convergence checks are active and blocking invalid hypotheses

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T044 [P] Documentation updates: Update `quickstart.md` with execution examples
- [ ] T045 Code cleanup and refactoring (remove dead code, ensure type hints)
- [ ] T046 [P] **Profile `main.py` using `cProfile`** to identify top 3 slowest functions (SC-004)
- [ ] T047 [P] **Implement specific optimizations** (e.g., caching, vectorization) based on T046 profiling to **reduce runtime to satisfy SC-004 (6-hour limit)** (SC-004)
- [ ] T048 [P] Add final integration test for the full pipeline in `tests/integration/test_full_pipeline.py`
- [ ] T049 [P] Run `quickstart.md` validation and **assert that `data/processed/results/hypothesis_status.json` exists** with valid entries for H-001 to H-004

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
  - **T007 (Validation Definition)** and **T007b (Mode Selection Definition)** are critical for US4 and Tiered Execution.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - **US1 (Data/Graph)** and **US4 (Validation)** are P1. 
  - **US1 Execution (T014, T007-exec, T007b-exec)**: T014 (Download) must complete first. T007-exec and T007b-exec depend on T014.
  - **T015 (Sensitivity Analysis)**: Depends on **T007-exec** (Validation) completion to ensure only validated configs are processed.
  - **US2 (Descriptors)**: Depends on US1 (needs graphs).
  - **US3 (Regression)**: Depends on US2 (needs descriptors) and US4 (needs validated targets).
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories (except Download).
- **User Story 4 (P1)**: Logic (T007/T007b) is defined in Phase 2. Execution (T007-exec, T007b-exec) is in Phase 3 and must run *before* T015 (Phase 3) and T024 (Phase 4).
- **User Story 2 (P2)**: Can start after Foundational + US1 (needs graphs). **US2 cannot start until T015 (sensitivity report generation) is complete**.
- **User Story 3 (P3)**: Can start after Foundational + US2 + US4 (needs descriptors and validated targets).

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- **US1 (Download/Graph)** and **US4 (Validation Logic Definition)** can run in parallel after Foundational
- **US2 (Descriptors)** can run in parallel for different descriptor types (if modularized)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (once dependencies met)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for checksum verification in tests/unit/test_validation_utils.py"
Task: "Unit test for graph construction in tests/unit/test_graph_builder.py"

# Launch all models for User Story 1 together:
Task: "Implement download.py"
Task: "Implement graph_builder.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 + 4 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories, includes Validation & Mode Selection definitions)
3. Complete Phase 3: User Story 1 (Data/Graph) - **Must include T007-exec and T007b-exec execution**.
4. **STOP and VALIDATE**: Test Data Ingestion and Independence checks (Phase 2 logic execution) independently
5. If data is invalid, project halts or switches to Structure-Only Mode immediately

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 + 4 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Data Ingestion)
   - Developer B: User Story 2 (Descriptors) (Starts after A completes T016)
   - (Once B is done): Developer C: User Story 3 (Regression)
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
- **Critical Constraint**: No GPU usage; no large-LLM inference; strict checksum verification; sensitivity analysis on cutoff radius; no internal VDOS calculation (record absence if missing).
- **Validation Logic**: Defined in Phase 2, Executed in Phase 3 to ensure P1 priority for US-4 and correct data flow.