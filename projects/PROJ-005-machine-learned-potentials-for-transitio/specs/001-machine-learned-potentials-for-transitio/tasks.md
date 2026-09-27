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

- **Single project**: `code/` at repository root containing `src/`, `tests/`, `data/`, `data/raw/`, `data/processed/`, `data/results/`, `specs/`
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

- [X] T001 Create project root `code/` directory and subdirectories: `code/src/`, `code/tests/`, `code/data/`, `code/data/raw/`, `code/data/processed/`, `code/data/results/`, `code/specs/`
- [X] T002 Create `.gitignore` file in `code/` excluding `data/raw/*`, `__pycache__`, `*.pyc`, `.env`, `*.pt`
- [X] T003 [P] Configure linting (flake8/black) and formatting tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/requirements.txt` with pinned versions: `torch`, `torch-geometric`, `scikit-learn`, `shap`, `pandas`, `numpy`, `pyyaml`, `pytest`, `pytest-cov`, `psi4`
- [X] T005a [P] [Foundational] Create `code/scripts/setup.sh` to initialize the Python environment. **Action**: Script must create a virtualenv in `code/venv/` and install `code/requirements.txt`. **Output**: `code/scripts/setup.sh` executable.
- [X] T005b [P] [Foundational] Execute `code/scripts/setup.sh` to activate the environment and install dependencies. **Action**: Run `bash code/scripts/setup.sh`. **Depends on T005a**.
- [X] T006 Implement `code/src/utils/config.py` for loading YAML configuration and environment variables
- [ ] T007 Implement `code/src/utils/logging.py` for structured logging and progress tracking
- [ ] T008 [P] [Foundational] Create `code/contracts/dataset_graph.schema.yaml` defining `TransitionStateGraph` attributes (nodes, edges, energy_dft, barrier_height, metal_center, ligand_class). **Output**: Valid YAML schema file.
- [X] T009 Create `code/contracts/prediction_schema.yaml` defining `PredictionResult` and `EnsemblePredictionResult` structures
- [ ] T010 Setup `code/data/raw/` directory with checksum verification logic for downloaded artifacts
- [ ] T011a [P] [Foundational] Create `code/src/data/splits.py` skeleton with function signatures for Leave-Ligand-Scaffold-Out (LLSO)
    The research question focuses on evaluating the generalizability of predictive models across distinct chemical scaffolds. The method employs a Leave-Ligand-Scaffold-Out cross-validation strategy to ensure that test sets contain ligands with scaffolds unseen during training. References: [Citation Placeholder]. **(Do NOT implement full logic yet; define function signatures only)**
- [ ] T011b [Foundational] Implement full 5-Fold LLSO logic in `code/src/data/splits.py` to generate train/val/test splits based on ligand scaffolds. **Logic**: Ensure no ligand scaffold appears in both training and test sets. **Output**: `code/src/data/splits.py` contains executable `generate_splits()` function. **Depends on T011a**.
- [ ] T012a [P] [Foundational] Create contract test for graph schema validation in `code/tests/contract/test_graph_schema.py`. **Action**: Write test cases to validate `TransitionStateGraph` against `code/contracts/dataset_graph.schema.yaml`. **Depends on T008**.
- [ ] T012b [Foundational] Implement integration test for data pipeline end-to-end in `code/tests/integration/test_pipeline.py`. **Action**: Write test cases to verify end-to-end flow from ingestion to graph output. **Depends on T008, T012a**.
- [ ] T037a [Foundational] Perform a single-point DFT baseline calculation. **Action**: Extract a representative transition-state geometry from `code/data/processed/graphs.parquet` (select sample with median barrier height). Verify `graphs.parquet` contains at least one valid transition state; if empty, halt with error. Use `psi4` to calculate B3LYP/STO-3G energy and wall-clock time for this geometry on the current runner. **Output**: `code/data/baseline_dft_time.json` with `reference_time_seconds`, `hardware_info` (CPU model), and `geometry_source` (sample ID). **Dependencies**: `psi4` installed (T004). **CRITICAL**: This task MUST be marked Ready immediately upon completion of T004 to allow parallel execution with US2 training (T024b/T025) while US3 logic is being developed.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Graph Construction (Priority: P1) 🎯 MVP

**Goal**: Ingest QM9-TS data, filter for Pd/Ni/Cu, construct graphs, and classify ligands.

**Independent Test**: Run `code/src/data/ingest.py` and `code/src/data/graph_construction.py` on the subset; verify `code/data/processed/graphs.parquet` exists with valid atomic features, edge attributes, and correct `ligand_class` labels (Group 13 vs. Conventional).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T013 [P] [US1] Contract test for graph schema validation in `code/tests/contract/test_graph_schema.py`
- [X] T014 [US1] Integration test for data pipeline end-to-end in `code/tests/integration/test_pipeline.py` **(Write first (TDD); execution depends on T015, T016 completion)**

### Implementation for User Story 1

- [X] T015 [US1] Implement `code/src/data/ingest.py` to fetch QM9-TS from verified HuggingFace URL and compute checksums
- [X] T016 [US1] Implement `code/src/data/ingest.py` to filter for Pd, Ni, Cu elementary steps and count valid reactions. **Logic**: 1) Filter for Pd, Ni, Cu. 2) Count valid reactions. 3) Return count. **Output**: `count` integer. (FR-001)
- [ ] T016b [US1] Implement scarcity flag logic in `code/src/data/ingest.py`. **Logic**: If count < 120 (threshold defined in FR-001), create `code/data/processed/data_scarcity_flag.json` with exact schema: `{ "count": <int>, "status": "scarcity", "threshold": 120 }`. **Depends on T016**. (FR-001b)
- [ ] T017a [US1] Implement sensitivity analysis in `code/src/data/graph_construction.py`. **Input**: Raw geometries from T015. **Logic**: 1) Sweep cutoff values (, 4.0 Angstroms). 2) Calculate graph metrics (avg_degree, edge_count, density) for each. 3) Output `code/data/results/cutoff_sensitivity.json`. **Output**: `code/data/results/cutoff_sensitivity.json`. **Depends on T015**.
- [ ] T017b [US1] Select optimal cutoff in `code/src/data/graph_construction.py`. **Input**: `code/data/results/cutoff_sensitivity.json` (from T017a). **Logic**: Select cutoff from swept values that maximizes stability (min variance in metrics). **Output**: Selected cutoff value. **Depends on T017a**.
- [ ] T017c [US1] Generate final graphs and flag outliers. **Input**: Raw geometries (T015), selected cutoff (T017b), and scarcity status (T016b). **Logic**: 1) Generate graphs using selected cutoff. 2) Flag samples with >6 coordination as outliers (`is_outlier` boolean). 3) Save final `code/data/processed/graphs.parquet`. 4) If scarcity flag is present, adjust batch sizes or logging verbosity accordingly. **Output**: `code/data/processed/graphs.parquet`. **Depends on T017b, T016b**.
- [ ] T018 [US1] Validate output graphs against `code/contracts/dataset_graph.schema.yaml` before saving. **Action**: Run validation script on `code/data/processed/graphs.parquet`. **Depends on T008, T017c**.
- [ ] T019 [US1] Generate `code/data/processed/splits.json`. **Logic**: Combine final graphs (T017c) and splits (T011b). **Depends on T017c, T011b**.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - GNN Training and Barrier Prediction (Priority: P2)

**Goal**: Train ensemble of SchNet models on CPU, generate predictions, and compute metrics.

**Independent Test**: Train 5 models (≤30 epochs, Adam lr=1e-4) on CPU; verify `code/data/processed/predictions.parquet` contains finite energies, MAE/RMSE/Pearson metrics in `code/data/processed/metrics.json`, and non-zero ensemble variance.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Contract test for prediction schema in `code/tests/contract/test_prediction_schema.py`
- [X] T021 [P] [US2] Unit test for SchNet architecture initialization in `code/tests/unit/test_models.py`

### Implementation for User Story 2

- [ ] T022 [US2] Implement SchNet-style GNN architecture in `code/src/models/schnet.py` (PyTorch Geometric, CPU compatible)
- [ ] T023a [US2] Implement `code/src/models/ensemble.py` wrapper. **Action**: Define class to manage multiple models. **Output**: `code/src/models/ensemble.py`. (FR-007)
- [ ] T023b [US2] Orchestrate parallel training of 5 seeds and aggregate results. **Action**: Run multiple training instances with varying random seeds. Aggregate predictions into `EnsemblePredictionResult`. **Output**: `code/data/processed/models/seed_{i}.pt` (5 files) and `code/data/processed/ensemble_variance.json`. **Depends on T022, T023a**.
- [ ] T024 [US2] Implement training loop in `code/src/models/ensemble.py` with a HARD CAP of epochs (max). **Logic**: Implement early stopping mechanism with patience=5 epochs. **Condition**: Stop training if loss does not decrease for a consecutive period of epochs (Early Stopping) OR if a predefined maximum epoch limit is reached (Hard Cap). **Deliverable**: Save model checkpoints to `code/data/processed/models/seed_{i}.pt` (FR-003)
- [ ] T025 [US2] Implement `code/src/models/predict.py` to generate barrier height predictions for held-out test set. **Primary Deliverable**: Generate `code/data/processed/residuals.parquet` containing per-sample error residuals (ML - DFT). **Note**: Do NOT generate `metrics.json` yet. (FR-004, SC-001)
- [ ] T026 [US2] Compute ensemble variance and correlation with error magnitude. **Input**: `code/data/processed/residuals.parquet` (from T025). **Output**: `code/data/results/variance_correlation.json` containing keys: `pearson_correlation`, `mean_variance`. **Depends on T025** (SC-005)
- [ ] T027a [US2] Generate `code/data/processed/predictions.parquet`. **Input**: `code/data/processed/residuals.parquet` (T025). **Logic**: Aggregate raw predictions into final parquet. **Output**: `code/data/processed/predictions.parquet`. **Depends on T025**.
- [ ] T027b [US2] Finalize `code/data/processed/metrics.json`. **Input**: `code/data/processed/residuals.parquet` (T025) and `code/data/results/variance_correlation.json` (T026). **Logic**: Calculate MAE, RMSE, Pearson. Aggregate variance metrics. **Output**: `code/data/processed/metrics.json`. **Depends on T025, T026, T027a**.
- [ ] T028 [US2] [REMOVED] (Redundant with plan.md Spec Deviation Notes).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Error Analysis and Feature Attribution (Priority: P3)

**Goal**: Analyze error residuals using SHAP/Integrated Gradients and perform statistical testing.

**Independent Test**: Run analysis scripts on prediction results; verify `code/data/results/feature_importance.csv` contains ranked descriptors, `code/data/results/statistical_tests.json` contains p-values, and speed-up factor is recorded.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US3] Unit test for statistical test logic in `code/tests/unit/test_statistics.py`
- [ ] T030 [P] [US3] Integration test for analysis pipeline in `code/tests/integration/test_analysis.py`

### Implementation for User Story 3

- [ ] T031 [US3] Implement `code/src/analysis/feature_importance.py` using Integrated Gradients and SHAP on prediction error residuals (ML - DFT) from `code/data/processed/residuals.parquet`
- [ ] T032 [US3] Implement logic to rank descriptors and calculate variance explained. **Specific Logic**: Select the smallest subset of top descriptors where cumulative `variance_explained` >= 0.60. **Output**: Write `code/data/results/top_descriptors_subset.json` containing the list of selected descriptors, their scores, and `total_variance_explained` (variance of the full set relative to the original feature space). **Schema**: `{ "descriptors": [...], "cumulative_variance": float, "total_variance_explained": float }`. (FR-005, SC-002, Constitution Principle VII)
- [ ] T033 [US3] Implement `code/src/analysis/statistics.py` with unpaired Welch's t-test for experimental groups vs. Conventional error distributions (FR-006 adaptation). **Action**: Generate statistical test results (p-value, t-statistic) and log deviation in `code/data/results/deviation_log.md` (T034). (FR-006 adaptation)
- [X] T034 [US3] Create `code/data/results/deviation_log.md` documenting the deviation from FR-006 (paired test) to unpaired Welch's t-test. **Required sections**: `Spec Requirement`, `Implemented Logic`, `Statistical Justification`, `Spec Update Request` (Constitution Principle IV)
- [ ] T035 [US3] Implement speed analysis: measure GNN inference time vs. the DFT baseline. **Input**: `code/data/baseline_dft_time.json` (from T037a in Phase 2) and prediction results from T027a. **Logic**: Compare GNN inference time against the `reference_time_seconds` from T037a. **Output**: `code/data/results/speed_metrics.json` with `speedup_factor`. **Depends on T027a, T037a (Phase 2)**
- [ ] T036a [US3] Generate `code/data/results/feature_importance.csv`. **Input**: T032. **Output**: `code/data/results/feature_importance.csv`.
- [ ] T036b [US3] Generate `code/data/results/statistical_tests.json`. **Input**: T033. **Output**: `code/data/results/statistical_tests.json`.
- [ ] T036c [US3] Generate `code/data/results/speed_metrics.json`. **Input**: T035. **Output**: `code/data/results/speed_metrics.json`.
- [ ] T037 [US3] Create visualizations of error distributions in `code/src/analysis/visualizations.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Generate `code/data/results/final_metrics_table.csv` containing columns: [metric_name, value, unit, reference] comparing all SC metrics against community standards
- [ ] T039 Run constitution check to verify citations, checksums, and reproducibility steps
- [ ] T040 Update `research.md` with final findings on ligand generalization and structural features
- [ ] T041 Run `quickstart.md` validation to ensure full pipeline reproducibility
- [ ] T042a [US3] Update `spec.md` to reflect deviations from FR-006 and FR-008. **Logic**: Ensure spec.md reflects the changes already made in T034. **Content Source**: Use `code/data/results/deviation_log.md`. **Depends on T034**.
- [ ] T042b [Foundational] Update `spec.md` to reflect deviations from FR-006 and FR-008. **Action**: Update FR-006 to specify "unpaired Welch's t-test" and FR-008 to specify "5-Fold LLSO". **Content Source**: Use `code/data/results/deviation_log.md` (T034). **Depends on T034 (Deviation Log Creation)**.

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
- All Foundational tasks marked [P] can run in parallel (within Phase 2) **EXCEPT T005a and T005b which are sequential**.
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- **Sensitivity Analysis Chain**: T017a -> T017b -> T017c is strictly sequential.
- **Speed Analysis Chain**: T037a (Phase 2) -> T035 (Phase 5) are strictly sequential (cross-phase).

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for graph schema validation in code/tests/contract/test_graph_schema.py"
Task: "Integration test for data pipeline end-to-end in code/tests/integration/test_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement code/src/data/ingest.py to fetch QM9-TS..."
Task: "Implement code/src/data/graph_construction.py to convert geometries..."
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
 - Developer C: User Story 3 (including T037a execution in parallel)
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
- **Deviations**: Any deviation from Spec FRs (e.g., LOOCV -> LLSO, Paired -> Unpaired) MUST be logged in `code/data/results/deviation_log.md` as per task T034.
- **Spec Updates**: Deviations MUST be reflected in `spec.md` via T042a (Polish) and T042b (Foundational) to maintain the Single Source of Truth.
- **Reproducibility**: Speed-up metrics (SC-004) MUST be measured by running a real DFT calculation (psi4) on a representative transition-state geometry from the dataset, not by using static literature values or irrelevant molecules like Methane.
- **Directory Structure**: All paths are relative to `code/` (the project root) to ensure Constitution Principle I (Reproducibility) is met.
- **Parallel Execution**: T037a (Phase 2) is designed to run immediately after T004, allowing the DFT baseline calculation to proceed in parallel with US2 training (T023b/T024) to optimize the critical path.