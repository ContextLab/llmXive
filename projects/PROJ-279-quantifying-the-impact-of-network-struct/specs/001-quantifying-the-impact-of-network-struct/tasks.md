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

- [X] T001 Create project structure per implementation plan (`projects/PROJ-279-quantifying-the-impact-of-network-struct/code/`)
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (ase, networkx, scikit-learn, pandas, numpy, matplotlib, requests, tqdm, pyyaml)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes Data Independence Validation (US-4) and Mode Selection logic definitions.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. Note: Logic is defined here, but execution occurs in Phase 3 after data ingestion.

- [X] T004 Setup `data/raw/` and `data/processed/` directories with `.gitkeep`
- [X] T005 [P] Implement `state/` YAML management for artifact checksums and versioning (Constitution Principle V)
- [X] T006 [P] Create base `AtomicConfiguration` dataclass in `code/models/atomic_config.py`
- [ ] T007a-code [P] **Write `code/validation.py`**: Implement `run_validation(configs: List[AtomicConfiguration]) -> dict` function. **Output**: `code/validation.py`. **Function Signature**: Returns a dict with keys: `validated_configs` (List[str]), `excluded_configs` (List[str]), `convergence_flags` (Dict[str, str]). **Logic**: Check system size (>=1000 atoms). If <1000, add to `excluded_configs` if not experimental, OR add to `validated_configs` with `convergence_flags[id] = "P preliminary - Unverified Convergence"` if retained for descriptive stats. **Constraint**: MUST enforce Constitution Principle VI (Active Exclusion). (FR-006, FR-007, Constitution Principle VI). **Note**: This task writes code only; it does not run on data.
- [ ] T007a-exec [US1] **Execute Validation**: Run `code/validation.py` (defined in T007a-code) on the downloaded data in `data/raw/`. **Input**: `data/raw/`. **Output**: `data/processed/validation_report.json` containing:
 - `validated_configs`: list of configuration IDs passing checks.
 - `excluded_configs`: list of configuration IDs excluded from analysis.
 - `convergence_flags`: dictionary mapping each ID in `validated_configs` to a string (e.g., "OK" or "P preliminary - Unverified Convergence").
 (FR-006, FR-007, Constitution Principle VI)
- [ ] T007ba-code [P] **Write `code/mode_selector.py`**: Implement `run_mode_selector(data_path: str) -> dict` function. **Output**: `code/mode_selector.py`. **Function Signature**: Returns a dict with keys: `mode` (str: "Full" or "Structure-Only"), `reason` (str). **Logic**: Check for existence of pre-calculated VDOS and thermal conductivity in metadata. If missing, set mode="Structure-Only". **Input Schema**: Path to `data/raw/` or metadata file. **Output Schema**: JSON with `mode` and `reason`. **Note**: This task writes code only; it does not run on data.
- [ ] T007bb-exec [US1] **Execute Mode Selection**: Run `code/mode_selector.py` (defined in T007ba-code) on the downloaded data. **Input**: `data/raw/`. **Output**: `data/processed/mode_config.json` indicating 'Full' or 'Structure-Only' mode.
- [ ] T008 Create `validation_utils.py` for checksum verification and file integrity checks (Constitution Principle III)
- [ ] T009 Configure logging infrastructure to output to `logs/analysis.log` and stdout
- [ ] T010 Configure environment configuration management (loading `cutoff_radius`, `zenodo_url` from env vars)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion, Validation, and Graph Construction (Priority: P1) 🎯 MVP

**Goal**: Download pre-existing MD trajectories of amorphous silicon (a-Si), validate them against independence and size constraints, and convert valid trajectories into graph representations.

**Independent Test**: Verify successful download, checksum match, validation exclusion of invalid configs, and construction of graphs only for validated configurations.

### Tests for User Story 1

- [X] T011 [P] [US1] Unit test for checksum verification in `tests/unit/test_validation_utils.py`
- [X] T012 [P] [US1] Unit test for graph construction with known coordinates in `tests/unit/test_graph_builder.py`
- [X] T013 [P] [US1] Integration test for end-to-end download, validation, and graph build in `tests/integration/test_download_graph.py`

### Implementation for User Story 1

- [ ] T014 [P] [US1] Implement `download.py` to fetch trajectories from Zenodo/HuggingFace with checksum verification (FR-001). **Constraint**: If download fails, raise an explicit error; do NOT fall back to synthetic data.
- [ ] T007-exec [US1] **Execute Validation**: Run `code/validation.py` (defined in T007a-code) on the downloaded data. **Input**: `data/raw/`. **Output**: `data/processed/validation_report.json`. (FR-006, FR-007, Constitution Principle VI). **Depends on**: T014 (Download) and T007a-code.
- [ ] T007bb-exec [US1] **Execute Mode Selection**: Run `code/mode_selector.py` (defined in T007ba-code) on the downloaded data. **Input**: `data/raw/`. **Output**: `data/processed/mode_config.json`. **Depends on**: T014 (Download) and T007ba-code.
- [X] T015a [US1] **Implement Sensitivity Loop**: Implement the sensitivity analysis loop logic in `code/graph_builder.py`. **Requirement**: The loop MUST iterate over the EXACT discrete set of cutoff radii: **{2.8, 3.0, 3.2} Å**. **Constraint**: The code MUST fail or raise an error if any other value is used. **Output**: `code/graph_builder.py` updated with the loop. (FR-002).
- [ ] T015b [US1] **Execute Sensitivity Loop**: Run the sensitivity loop defined in T015a **ONLY** on the `validated_configs` list generated by T007-exec. **Input**: `data/processed/validation_report.json`. **Output**: `data/processed/sensitivity_report.json` containing a table of cutoff radius (2.8, 3.0, 3.2) vs. average degree and component count (FR-002). **Depends on**: T014, T007-exec, T015a.
- [ ] T015c [US1] **Write Sensitivity Report**: Ensure `data/processed/sensitivity_report.json` is written with the correct schema, explicitly listing results for 2.8, 3.0, and 3.2.
- [ ] T016 [US1] Add validation logic to detect disconnected components and log warnings (Spec US-1, Scenario 3)
- [ ] T017 [US1] Handle edge cases: corrupted files (abort with error), unexpected coordination numbers (flag/drop)
- [ ] T018 [US1] Save constructed graphs and metadata to `data/processed/graphs/` in JSON/GraphML format

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Topological and Vibrational Descriptor Calculation (Priority: P2)

**Goal**: Compute specific topological metrics (ring statistics, bond orientational order parameters, clustering coefficients) AND vibrational spectral descriptors (VDOS, participation ratios) for each configuration.

**Independent Test**: Calculate descriptors on a known crystal structure and compare against theoretical expectations; verify output format.

### Tests for User Story 2

- [X] T019 [P] [US2] Unit test for ring statistics calculation on a simple lattice in `tests/unit/test_descriptors.py`
- [X] T020 [P] [US2] Unit test for Steinhardt Q6 parameter calculation in `tests/unit/test_descriptors.py`
- [X] T021 [P] [US2] Integration test for full descriptor pipeline on a small sample in `tests/integration/test_descriptor_pipeline.py`

### Implementation for User Story 2

- [X] T024a [US2] **Implement Filter & Fallback Logic**: Implement `filter_and_fallback()` in `code/descriptors.py`. **Logic**: Attempt to load pre-calculated VDOS. If missing, **mark config as VDOS-MISSING** but **DO NOT exclude**; **proceed to calculate topological descriptors (T022/T023)** for this configuration. If VDOS present, calculate both. **Output**: `code/descriptors.py` updated with this logic. **Depends on**: T007-exec (Validation Report).
- [ ] T024b [US2] **Execute Filter**: Run the filter logic defined in T024a on the validated configs from T007-exec. **Input**: `data/processed/validation_report.json`. **Output**: `data/processed/filtered_config_ids.json` (list of IDs to process) and internal flags for VDOS status. **Depends on**: T007-exec, T024a.
- [ ] T024c [US2] **Write VDOS Retention Report**: Generate `data/processed/vdos_retention_report.json` listing configs with missing VDOS that are **retained** for topological-only analysis. **Schema**: `{ "retained_configs": [ { "id": "string", "status": "VDOS-MISSING", "reason": "string" } ] }`. **Constraint**: This report confirms retention, NOT exclusion. (Plan: Structure-Only Mode, FR-003). **Depends on**: T024b.
- [ ] T024-exec [US2] **Execute VDOS Load**: Run `load_vdos()` and `calculate_participation_ratios()` on configs where VDOS is available. **Depends on**: T024b.
- [ ] T022-exec [US2] **Execute Ring Stats**: Run `calculate_ring_statistics()` on the filtered configs from T024b. **Input**: `data/processed/filtered_config_ids.json`. **Input**: `data/processed/vdos_retention_report.json` (to ensure retained VDOS-missing configs are included). **Depends on**: T024b.
- [ ] T023-exec [US2] **Execute Steinhardt**: Run `calculate_steinhardt_parameters()` on the filtered configs from T024b. **Input**: `data/processed/filtered_config_ids.json`. **Input**: `data/processed/vdos_retention_report.json` (to ensure retained VDOS-missing configs are included). **Depends on**: T024b.
- [X] T025a [US2] **Aggregate Descriptors**: Implement aggregation logic to produce `data/processed/descriptors.csv`. **Schema**: `config_id`, `ring_dist`, `q6`, `clustering`, `vdos_vector` (list of floats or null), `data_quality` (str: "full" or "topological_only"). **Logic**: For configs in `vdos_retention_report.json` (VDOS-MISSING), set `vdos_vector` to `null` and `data_quality` to "topological_only". **Mechanism**: Concatenate ring stats, Q6, and VDOS vectors into a single row per Config ID. (FR-003).
- [ ] T025b [US2] **Execute Aggregation**: Run the aggregation logic from T025a on the results of T022-exec, T023-exec, and T024-exec. **Depends on**: T022-exec, T023-exec, T024-exec.
- [ ] T026 [US2] Handle missing thermal conductivity values: skip configuration and log count (Spec Edge Cases)
- [ ] T027 [US2] Save processed descriptors to `data/processed/descriptors.csv` (Output artifact defined in T025a). **Depends on**: T025b.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Correlation and Visualization (Priority: P3)

**Goal**: Perform statistical analysis (Ridge regression, non-linear model comparison) to correlate descriptors with thermal conductivity, validate via cross-validation, and generate visualizations.

**Independent Test**: Run regression on synthetic data with known relationship; verify model recovers coefficients and R² within margin.

### Tests for User Story 3

- [X] T028 [P] [US3] Unit test for cross-validation logic (LOOCV vs 5-fold switch) in `tests/unit/test_models.py`
- [X] T029 [P] [US3] Unit test for feature importance extraction and p-value calculation in `tests/unit/test_models.py`
- [X] T030 [P] [US3] Integration test for full regression pipeline on synthetic data in `tests/integration/test_regression.py`

### Implementation for User Story 3

- [ ] T031 [P] [US3] Implement `models.py` with Ridge Regression and Random Forest/Kernel Ridge (FR-004)
- [ ] T032 [US3] Implement dimensionality reduction (PCA/Lasso) **as a preprocessing step for small N** to prevent overfitting, followed by stability selection (Plan: Complexity Tracking)
- [ ] T033 [US3] Implement cross-validation logic: 5-fold if N ≥ 30, else LOOCV (FR-004, Spec US-3, Scenario 1)
- [ ] T034 [US3] Calculate and log mean R², std dev, and p-values for top 3 features (FR-004, Spec US-3, Scenario 1)
- [ ] T035 [US3] Implement `viz.py` to generate scatter plot (top predictor vs. k) with regression line and Pearson r (FR-005)
- [ ] T036 [US3] Generate feature importance bar chart with error bars (std dev across folds) (FR-005)
- [ ] T037a [US3] **Execute Regression**: Run the regression models on the descriptors from T027. **Input**: `data/processed/descriptors.csv`. **Output**: `data/processed/results/regression_metrics.json`. **Depends on**: T027.
- [ ] T037b [US3] **Aggregate Hypothesis Status**: Read `data/processed/validation_report.json`, `data/processed/vdos_retention_report.json`, and `data/processed/mode_config.json` to generate `data/processed/results/hypothesis_status.json`. **Input Schemas**:
 - `validation_report.json`: Contains `validated_configs`, `excluded_configs`, `convergence_flags`.
 - `vdos_retention_report.json`: Contains `retained_configs` with `VDOS-MISSING` status.
 - `mode_config.json`: Contains `mode` ("Full" or "Structure-Only").
 **Output Schema**:
 ```json
 {
 "H-001": { "status": "TESTED|UNTESTABLE", "reason": "string" },
 "H-002": { "status": "TESTED|UNTESTABLE", "reason": "string" },
 "H-003": { "status": "TESTED|UNTESTABLE", "reason": "string" },
 "H-004": { "status": "TESTED|UNTESTABLE", "reason": "string" }
 }
 ```
 **Logic**: If mode is 'Structure-Only', set H-001/H-002 to 'UNTESTABLE' with reason "VDOS or k missing". If mode is 'Full', set to 'TESTED' if regression succeeded. Set H-003/H-004 based on descriptor availability.
- [ ] T038 [US3] Save results (metrics, plots) to `data/processed/results/` and update `state/`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Data Independence Verification (Priority: P1)

**Goal**: Verify that thermal conductivity target values are from an independent source and converged to thermodynamic limit.

**Independent Test**: Verify metadata explicitly states source method and system size.

### Tests for User Story 4

- [X] T039 [P] [US4] Unit test for metadata validation logic in `tests/unit/test_validation.py`

### Implementation for User Story 4

- [ ] T041 [US4] Implement logic to **exclude** systems < 1000 atoms from hypothesis testing (Constitution Principle VI). **Constraint**: If a system < 1000 atoms is retained for descriptive stats, it MUST be flagged with `convergence_flags[id] = "P preliminary - Unverified Convergence"` (as defined in T007a-code).
- [ ] T042 [US4] Log specific warnings for "P preliminary - Unverified Convergence" if small systems are used for descriptive stats only. **Constraint**: This log must match the flag set in T007a-code.
- [ ] T043 [US4] Ensure `main.py` enforces the "Tiered Execution" mode based on validation results (Mode Selection from T007bb-exec).

**Checkpoint**: Data independence and convergence checks are active and blocking invalid hypotheses

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T044 [P] Documentation updates: Update `quickstart.md` with execution examples
- [ ] T045 Code cleanup and refactoring (remove dead code, ensure type hints)
- [ ] T046a [P] **Profile `main.py`**: Run `cProfile` on the pipeline and output `profile.log`.
- [ ] T046b [P] **Analyze Profile**: Parse `profile.log` to identify the top 3 slowest functions.
- [ ] T047a [P] **Implement Caching**: Implement caching for the identified slowest function(s) if applicable.
- [ ] T047b [P] **Implement Vectorization**: Implement vectorization for the identified slowest function(s) if applicable.
- [ ] T048 [P] Add final integration test for the full pipeline in `tests/integration/test_full_pipeline.py`
- [ ] T049 [P] Run `quickstart.md` validation and **assert that `data/processed/results/hypothesis_status.json` exists** with valid entries for H-001 to H-004

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **T007a-code** and **T007ba-code** are critical for US4 and Tiered Execution.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **US1 (Data/Graph)** and **US4 (Validation)** are P1.
 - **US1 Execution (T014, T007-exec, T007bb-exec)**: T014 (Download) must complete first. T007-exec and T007bb-exec depend on T014 AND T007a-code/T007ba-code completion.
 - **T015b (Sensitivity Analysis)**: Depends on **T007-exec** (Validation) completion to ensure only validated configs are processed.
 - **US2 (Descriptors)**: Depends on US1 (needs graphs).
 - **US3 (Regression)**: Depends on US2 (needs descriptors) and US4 (needs validated targets).
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories (except Download).
- **User Story 4 (P1)**: Logic (T007a-code/T007ba-code) is defined in Phase 2. Execution (T007-exec, T007bb-exec) is in Phase 3 and must run *before* T015 (Phase 3) and T024 (Phase 4).
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
3. Complete Phase 3: User Story 1 (Data/Graph) - **Must include T007-exec and T007bb-exec execution**.
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
- **Data Integrity**: All data loaders MUST fail loudly on missing real data; no synthetic fallbacks allowed.
- **Streaming**: If the dataset exceeds runner memory, implement streaming logic in `download.py` and `descriptors.py` to process in chunks without loading the full dataset into RAM.