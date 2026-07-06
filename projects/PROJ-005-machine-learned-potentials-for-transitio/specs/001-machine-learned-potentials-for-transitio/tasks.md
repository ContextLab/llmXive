# Tasks: Machine-Learned Potentials for Transition-Metal Catalysis

**Input**: Design documents from `/specs/001-machine-learned-potentials/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/`, `data/`, `specs/` at repository root
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

- [ ] T001 Create project directories: `src/`, `tests/`, `data/`, `data/raw/`, `data/processed/`, `data/results/`, `specs/`
- [ ] T002 Create `.gitignore` file excluding `data/raw/*`, `__pycache__`, `*.pyc`, `.env`
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create `requirements.txt` with pinned versions: `torch`, `torch-geometric`, `scikit-learn`, `shap`, `pandas`, `numpy`, `pyyaml`, `pytest`, `pytest-cov`
- [ ] T005 Setup Python 3.11 virtualenv and install dependencies from `requirements.txt`
- [ ] T006 Implement `src/utils/config.py` for loading YAML configuration and environment variables
- [~] T007 Implement `src/utils/logging.py` for structured logging and progress tracking
- [ ] T008 Create `contracts/dataset_graph.schema.yaml` defining `TransitionStateGraph` attributes (nodes, edges, energy_dft, barrier_height)
- [ ] T009 Create `contracts/prediction_schema.yaml` defining `PredictionResult` and `EnsemblePredictionResult` structures
- [ ] T010 Setup `data/raw/` directory with checksum verification logic for downloaded artifacts
- [ ] T011 Create `src/data/splits.py` to define the interface and skeleton for 5-Fold Leave-Ligand-Scaffold-Out (LLSO) logic **(Do not implement full logic yet; define function signatures only)**
- [ ] T028 [P] [US2] Complete and integrate 5-Fold Leave-Ligand-Scaffold-Out (LLSO) logic in `src/data/splits.py` and `src/models/ensemble.py` for cross-validation (FR-008 adaptation) **(Note: T011 defined the skeleton; this task implements the full logic)**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Graph Construction (Priority: P1) 🎯 MVP

**Goal**: Ingest QM9-TS data, filter for Pd/Ni/Cu, construct graphs, and classify ligands.

**Independent Test**: Run `src/data/ingest.py` and `src/data/graph_construction.py` on the subset; verify `data/processed/graphs.parquet` exists with valid atomic features, edge attributes, and correct `ligand_class` labels (Group 13 vs. Conventional).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T012 [P] [US1] Contract test for graph schema validation in `tests/contract/test_graph_schema.py`
- [ ] T013 [US1] Integration test for data pipeline end-to-end in `tests/integration/test_pipeline.py` **(Write first (TDD); execution depends on T014, T015 completion)**

### Implementation for User Story 1

- [ ] T014 [US1] Implement `src/data/ingest.py` to fetch QM9-TS from verified HuggingFace URL and compute checksums
- [ ] T015 [US1] Implement `src/data/ingest.py` to filter for Pd, Ni, Cu elementary steps. **Logic**: 1) Count valid reactions. 2) If count >= 120, proceed (FR-001). 3) If count < 120, log warning and proceed to T015b. **(Note: T015 handles the check; T015b handles the flag)**
- [ ] T015b [US1] Implement scarcity flag logic in `src/data/ingest.py`. **Logic**: If count < 120, create `data/processed/data_scarcity_flag.json` with schema: `{ "count": <int>, "status": "scarcity" }` (FR-001b)
- [ ] T016 [US1] Implement `src/data/graph_construction.py` to convert geometries to `TransitionStateGraph`. **Attributes**: nodes (atomic number, formal charge), edges (distance-based cutoff). **Coordination Number Logic**: Calculate coordination number using a distance-based cutoff of 3.5 Angstroms (FR-002)
- [ ] T017 [US1] Implement sensitivity analysis for edge cutoffs: create `src/data/sweep_cutoff.py` to test cutoff values [2.5, 3.5, 4.0, 4.5] Angstroms and record graph density/feature stability in `data/results/cutoff_sensitivity.json` (Spec Assumption). **Depends on T016**
- [ ] T018 [US1] Add outlier handling: flag samples with >6 coordination for exclusion from training but retention in test
- [ ] T019 [US1] Validate output graphs against `contracts/dataset_graph.schema.yaml` before saving
- [ ] T020 [US1] Generate `data/processed/graphs.parquet` and `data/processed/splits.json`. **Depends on T028 completion**

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - GNN Training and Barrier Prediction (Priority: P2)

**Goal**: Train ensemble of SchNet models on CPU, generate predictions, and compute metrics.

**Independent Test**: Train 5 models (≤30 epochs, Adam lr=1e-4) on CPU; verify `data/processed/predictions.parquet` contains finite energies, MAE/RMSE/Pearson metrics in `data/processed/metrics.json`, and non-zero ensemble variance.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Contract test for prediction schema in `tests/contract/test_prediction_schema.py`
- [ ] T022 [P] [US2] Unit test for SchNet architecture initialization in `tests/unit/test_models.py`

### Implementation for User Story 2

- [ ] T023 [US2] Implement SchNet-style GNN architecture in `src/models/schnet.py` (PyTorch Geometric, CPU compatible)
- [ ] T024 [US2] Implement `src/models/ensemble.py` to train 5 models with different random seeds
- [ ] T025 [US2] Implement training loop in `src/models/ensemble.py` with a HARD CAP of 30 epochs (max). No early stopping based on convergence criteria that extends beyond 30 epochs; if loss stalls, stop at 30. **Deliverable**: Save model checkpoints to `data/processed/models/seed_{i}.pt` (FR-003)
- [ ] T026 [US2] Implement `src/models/predict.py` to generate barrier height predictions for held-out test set. **Primary Deliverable**: Generate `data/processed/metrics.json` containing aggregated MAE, RMSE, Pearson correlation (FR-004, SC-001). **Secondary**: Generate `data/processed/residuals.parquet` containing per-sample error residuals (ML - DFT)
- [ ] T027 [US2] Compute ensemble variance and correlation with error magnitude (SC-005)
- [ ] T029 [US2] Generate `data/processed/predictions.parquet` and finalize `data/processed/metrics.json`. **Depends on T026**
- [ ] T030 [US2] Create `data/results/cv_methodology_report.json` documenting the switch from LOOCV (FR-008) to 5-Fold LLSO. **Required keys**: `deviation_reason`, `statistical_justification`, `runtime_justification` (Constitution Principle IV, FR-008)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Error Analysis and Feature Attribution (Priority: P3)

**Goal**: Analyze error residuals using SHAP/Integrated Gradients and perform statistical testing.

**Independent Test**: Run analysis scripts on prediction results; verify `data/results/feature_importance.csv` contains ranked descriptors, `data/results/statistical_tests.json` contains p-values, and speed-up factor is recorded.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T031 [P] [US3] Unit test for statistical test logic in `tests/unit/test_statistics.py`
- [ ] T032 [P] [US3] Integration test for analysis pipeline in `tests/integration/test_analysis.py`

### Implementation for User Story 3

- [ ] T033 [US3] Implement `src/analysis/feature_importance.py` using Integrated Gradients and SHAP on prediction error residuals (ML - DFT) from `data/processed/residuals.parquet`
- [ ] T034 [US3] Implement logic to rank descriptors and calculate variance explained. **Specific Logic**: Select the smallest subset of top descriptors where cumulative `variance_explained` >= 0.60. **Output**: Write `data/results/top_descriptors_subset.json` containing the list of selected descriptors and their scores (FR-005, SC-002, Constitution Principle VII)
- [ ] T035 [US3] Implement `src/analysis/statistics.py` with unpaired Welch's t-test for Group 13 vs. Conventional error distributions (FR-006 adaptation). **Action**: Update `spec.md` FR-006 text to reflect unpaired test implementation and document the deviation.
- [ ] T036 [US3] Create `data/results/deviation_log.md` documenting the deviation from FR-006 (paired test) to unpaired Welch's t-test. **Required sections**: `Spec Requirement`, `Implemented Logic`, `Statistical Justification`, `Spec Update Request` (Constitution Principle IV)
- [ ] T037 [US3] Implement speed analysis: measure GNN inference time vs. a FRESH single-point DFT calculation (or a clearly defined standardized baseline) for speed-up factor (SC-004). **Note**: Do NOT use cached times.
- [ ] T038 [US3] Generate `data/results/feature_importance.csv`, `data/results/statistical_tests.json`, and `data/results/speed_metrics.json`
- [ ] T039 [US3] Create visualizations of error distributions in `src/analysis/visualizations.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Generate `data/results/final_metrics_table.csv` containing columns: [metric_name, value, unit, reference] comparing all SC metrics against community standards
- [ ] T041 Run constitution check to verify citations, checksums, and reproducibility steps
- [ ] T042 Update `research.md` with final findings on ligand generalization and structural features
- [ ] T043 Run `quickstart.md` validation to ensure full pipeline reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for data
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 for predictions

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
Task: "Contract test for graph schema validation in tests/contract/test_graph_schema.py"
Task: "Integration test for data pipeline end-to-end in tests/integration/test_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement src/data/ingest.py to fetch QM9-TS..."
Task: "Implement src/data/graph_construction.py to convert geometries..."
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
- **CPU Constraint**: All tasks must run on free CPU-only CI with limited resources (no GPU). No 8-bit/4-bit quantization or CUDA-specific code.
- **Data Integrity**: No synthetic data generation. All inputs must come from real, verified sources (QM9-TS).
- **Deviations**: Any deviation from Spec FRs (e.g., LOOCV -> LLSO, Paired -> Unpaired) MUST be logged in `data/results/deviation_log.md` or `data/results/cv_methodology_report.json` as per tasks T030/T036.