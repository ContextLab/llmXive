# Tasks: Predicting Molecular Properties from Topological Data Analysis

**Input**: Design documents from `/specs/001-predict-molecular-properties-tda/`
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

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-444-predicting-molecular-properties-from-top/`)
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (rdkit, gudhi/dionysus2, scikit-learn, pandas, numpy, matplotlib, seaborn, pyyaml, requests)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup `data/` directory structure (`raw/`, `processed/`) and `state/` tracking
- [X] T005 [P] Implement `code/utils/graph_builder.py` for RDKit molecular graph construction with validity checks
- [ ] T006 [P] Implement `code/utils/persistence_utils.py` for shortest-path filtration and empty diagram handling
- [~] T007 Implement `code/00_checksum_verify.py` to compute SHA256 hashes of raw data and record them in `data/checksums.txt` (Constitution III)
- [ ] T008 Implement `code/01_data_ingestion.py` to fetch MoleculeNet ESOL, validate `smiles`/`logP` columns against schema, perform a priori power analysis (N>=128) [UNRESOLVED-CLAIM: c_d8f70333 — status=not_enough_info], enforce min scaffolds check, and ensure random seed pinning (fixed value)
- [~] T010 [P] [US1] Contract test for `data/processed/tda_features.csv` schema in `tests/contract/test_tda_schema.py`
- [X] T011 [P] [US1] Integration test for disconnected graph handling in `tests/integration/test_disconnected_graphs.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Compute TDA Features for Molecular Dataset (Priority: P1) 🎯 MVP

**Goal**: Ingest ESOL dataset, compute persistence diagrams via shortest-path filtration, and vectorize to persistence images with a fixed grid resolution.

**Independent Test**: Run `02_tda_computation.py` on a fixed subset; verify output CSV has non-null topological descriptors for every valid molecule.

### Pre-Implementation Tests for User Story 1 (MUST FAIL BEFORE IMPLEMENTATION)

- [~] T010 [US1] Contract test for `data/processed/tda_features.csv` schema in `tests/contract/test_tda_schema.py`
- [X] T011 [US1] Integration test for disconnected graph handling in `tests/integration/test_disconnected_graphs.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/02_tda_computation.py`: Graph construction and shortest-path filtration (FR-001)
- [X] T013 [US1] Implement `code/02_tda_computation.py`: Vectorization to persistence images of appropriate resolution

The research question, method, and references remain unchanged as per the planning document requirements. (FR-002) for the **Primary Experiment**; include zero-vector fallback for empty diagrams; implement `run_sweep(resolutions=[10, 20, 30])` function to support sensitivity analysis (FR-006)
- [ ] T015 [US1] Add error handling for invalid SMILES (log to `data/logs/invalid_smiles.log` and skip) and implement sparse matrix logic with memory threshold checks for shortest-path computation to handle extremely large molecular weights (Edge Case)
- [ ] T016 [US1] Generate `data/processed/tda_features.csv` (primary dimensions) and `data/processed/traditional_descriptors.csv`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train and Compare Predictive Models (Priority: P2)

**Goal**: Train Linear Regression (L2) and Random Forest on Traditional, Topological, and Combined feature sets using -fold scaffold splits.

**Independent Test**: Execute `04_model_training.py`; verify R²/RMSE reported for all 3 configurations and 5 folds [UNRESOLVED-CLAIM: c_33f33c24 — status=not_enough_info].

### Implementation for User Story 2

- [ ] T017 [US2] Implement `code/03_feature_engineering.py`: Merge traditional descriptors and TDA features; prepare combined feature matrix
- [ ] T018 [US2] Implement `code/04_model_training.py`: Stratified scaffold split

The research question, method, and references remain unchanged as per the planning document requirements, with the specific fold count replaced by a qualitative description of the cross-validation strategy. (Bemis-Murcko) with **explicit ScaffoldSplitter(seed=42)** initialization (FR-004)
- [ ] T019 [US2] Implement `code/04_model_training.py`: Train Linear Regression (alpha=1.0) and Random Forest (100 trees, max_depth=10) on 3 feature sets [UNRESOLVED-CLAIM: c_c934dfb3 — status=not_enough_info] (FR-003)
- [ ] T020 [US2] Implement `code/04_model_training.py`: Calculate R² and RMSE per fold; aggregate metrics
- [ ] T021 [US2] Add runtime GPU check (FR-008) using generic CUDA detection (checking `CUDA_VISIBLE_DEVICES` and library-specific GPU flags) to raise `SystemExit(1)` if any GPU acceleration is detected; do not rely on `torch`
- [ ] T022 [US2] Generate `reports/metrics/model_performance.json` with all metrics and feature importance

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Validate Methodological Rigor and Sensitivity (Priority: P3)

**Goal**: Perform sensitivity analysis on grid resolution, apply Holm-Bonferroni correction, and run VIF diagnostics.

**Independent Test**: Inspect logs/reports to confirm sensitivity sweep, corrected p-values, and VIF flags are present.

### Implementation for User Story 3

- [ ] T023 [US3] Implement `code/05_sensitivity_analysis.py`: Execute sensitivity sweeps on resolutions including low, medium, and high settings. using the pipeline from T013; measure and report R² variance (FR-006, SC-002); requires outputs from Phase 4 (US2)
- [ ] T024 [US3] Generate `reports/metrics/sensitivity_analysis.json` aggregating sweep results
- [ ] T025 [US3] Implement `code/06_diagnostics.py`: Apply Holm-Bonferroni correction to p-values (per plan.md amendment to FR-005, replacing spec's Bonferroni for correlated tests)
- [ ] T026 [US3] Implement `code/06_diagnostics.py`: Calculate VIF; flag predictors > 5 [UNRESOLVED-CLAIM: c_4937c469 — status=not_enough_info] (FR-007)
- [ ] T027 [US3] Implement `code/06_diagnostics.py`: Calculate Mutual Information between traditional and topological feature sets (FR-009)
- [ ] T028 [US3] Generate `reports/metrics/diagnostics.json` with VIF flags, corrected p-values, and MI scores
- [ ] T029 [US3] Implement `code/07_resource_monitor.py` to log RAM/CPU usage to `reports/metrics/resource_usage.json`; integrate into main pipeline execution context (SC-004)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 [P] Documentation updates: Update `docs/` and `quickstart.md` with specific sections on TDA methodology and reproducibility steps
- [ ] T031 [P] Code cleanup: Refactor `code/utils/graph_builder.py` to reduce cyclomatic complexity to < 10 [UNRESOLVED-CLAIM: c_316e1e43 — status=not_enough_info]
- [ ] T032 [P] Performance optimization: Profile `code/02_tda_computation.py` and optimize memory usage to ensure total runtime < 5.4h [UNRESOLVED-CLAIM: c_020a066c — status=not_enough_info] (SC-004)
- [ ] T033 [P] Additional unit tests: Implement `tests/unit/` for graph builder and persistence utils
- [ ] T034 [P] Run quickstart.md validation to ensure full pipeline reproducibility

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
- **User Story 2 (P2)**: Depends on US1 completion (requires `tda_features.csv` and `traditional_descriptors.csv`)
- **User Story 3 (P3)**: Depends on US2 completion (requires model metrics for statistical testing)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
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
Task: "Contract test for data/processed/tda_features.csv schema in tests/contract/test_tda_schema.py"
Task: "Integration test for disconnected graph handling in tests/integration/test_disconnected_graphs.py"

# Launch all models for User Story 1 together:
Task: "Implement code/00_checksum_verify.py to record hashes in data/checksums.txt"
Task: "Implement code/01_data_ingestion.py: Fetch MoleculeNet ESOL, validate columns"
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