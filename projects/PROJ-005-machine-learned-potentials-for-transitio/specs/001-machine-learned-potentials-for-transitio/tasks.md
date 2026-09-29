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
- [X] T007 Implement `code/src/utils/logging.py` for structured logging and progress tracking
- [X] T008 Create `code/contracts/dataset_graph.schema.yaml` defining `TransitionStateGraph` attributes (nodes, edges, energy_dft, barrier_height, metal_center, ligand_class). **Output**: Valid YAML schema file.
- [X] T009 Create `code/contracts/prediction_schema.yaml` defining `PredictionResult` and `EnsemblePredictionResult` structures
- [ ] T010 [Foundational] Create `code/scripts/verify_checksums.py` to verify checksums of files in `code/data/raw/`. **Action**: Script must compute checksums (SHA256) and compare against stored values in `code/data/raw/checksums.json`. **Output**: `code/scripts/verify_checksums.py` executable and `code/data/raw/checksums.json` with schema `{ "file_path": "hash" }`. **Dependencies**: T004.
- [ ] T011a [P] [Foundational] Create `code/src/data/splits.py` to generate train/val/test splits using Leave-Ligand-Scaffold-Out (LLSO). **Logic**: 1) Parse `ligand_class` and `metal_center` from graphs. 2) Group samples by unique ligand scaffold ID. 3) Perform stratified split ensuring no scaffold ID appears in both train and test sets. 4) Output `code/data/processed/splits.json`. **Output**: `code/src/data/splits.py` contains executable `generate_splits()` function. **Dependencies**: T008.
- [ ] T012a [P] [Foundational] Create contract test for graph schema validation in `code/tests/contract/test_graph_schema.py`. **Action**: Write test cases to validate `TransitionStateGraph` against `code/contracts/dataset_graph.schema.yaml`. **Depends on T008**.
- [ ] T012b [Foundational] Implement integration test for data pipeline end-to-end in `code/tests/integration/test_pipeline.py`. **Action**: Write test cases to verify end-to-end flow from ingestion to graph output. **Depends on T008, T012a**.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Graph Construction (Priority: P1) 🎯 MVP

**Goal**: Ingest QM9-TS data, filter for Pd/Ni/Cu, construct graphs, and classify ligands.

**Independent Test**: Run `code/src/data/ingest.py` and `code/src/data/graph_construction.py` on the subset; verify `code/data/processed/graphs.parquet` exists with valid atomic features, edge attributes, and correct `ligand_class` labels (Group 13 vs. Conventional).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️
*Note: T012a and T012b in Phase 2 serve as the authoritative tests for this story.*

### Implementation for User Story 1

- [X] T015 [US1] Implement `code/src/data/ingest.py` to fetch QM9-TS from verified HuggingFace URL and compute checksums. **Action**: Verify checksums using `code/scripts/verify_checksums.py` before processing.
- [X] T016 [US1] Implement `code/src/data/ingest.py` to filter for Pd, Ni, Cu elementary steps and count valid reactions. **Logic**: 1) Filter for Pd, Ni, Cu. 2) Count valid reactions. 3) Return count. **Output**: `count` integer. (FR-001)
- [ ] T016b [US1] Implement scarcity flag logic in `code/src/data/ingest.py`. **Logic**: If count < 120 (threshold defined in FR-001), create `code/data/processed/data_scarcity_flag.json` with exact schema: `{ "count": <int>, "status": "scarcity", "threshold": 120 }`. **Depends on T016**. (FR-001b)
- [ ] T017a [US1] Implement sensitivity analysis sweep in `code/src/data/graph_construction.py`. **Input**: Raw geometries from T015. **Logic**: 1) Sweep cutoff values (3.0, 3.5, 4.0 Angstroms). 2) Calculate graph metrics (avg_degree, edge_count, density) for each. **Output**: Intermediate data structure in memory. **Depends on T015**.
- [ ] T017b [US1] Calculate and store sensitivity metrics. **Input**: Metrics from T017a. **Logic**: Compute variance of metrics across cutoffs. **Output**: `code/data/results/cutoff_sensitivity.json`. **Depends on T017a**.
- [ ] T017c [US1] Select optimal cutoff and generate final graphs. **Input**: `code/data/results/cutoff_sensitivity.json` (from T017b), raw geometries (T015), scarcity status (T016b). **Logic**: 1) Select cutoff minimizing metric variance. 2) Generate graphs using selected cutoff. 3) Flag samples with >6 coordination as outliers (`is_outlier` boolean). 4) Save final `code/data/processed/graphs.parquet`. **Output**: `code/data/processed/graphs.parquet`. **Depends on T017b, T016b**.
- [ ] T018 [US1] Validate output graphs against `code/contracts/dataset_graph.schema.yaml` before saving. **Action**: Run validation script on `code/data/processed/graphs.parquet`. **Depends on T008, T017c**.
- [ ] T019 [US1] Generate `code/data/processed/splits.json`. **Logic**: Combine final graphs (T017c) and splits (T011a). **Depends on T017c, T011a**.

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
- [ ] T023b [US2] Implement orchestration script to launch parallel training jobs. **Action**: Script to spawn 5 processes with distinct random seeds. **Output**: `code/scripts/train_ensemble.sh` or equivalent. **Depends on T022, T023a**.
- [ ] T023c [US2] Implement result aggregation logic. **Action**: Script to load 5 model checkpoints and aggregate predictions into `EnsemblePredictionResult`. **Output**: `code/data/processed/models/seed_{i}.pt` (5 files) and `code/data/processed/ensemble_variance.json`. **Depends on T023b**.
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

- [X] T029 [P] [US3] Contract test for statistical test logic in `code/tests/unit/test_statistics.py`
- [ ] T030 [P] [US3] Integration test for analysis pipeline in `code/tests/integration/test_analysis.py`

### Implementation for User Story 3

- [ ] T031 [US3] Implement `code/src/analysis/feature_importance.py` using Integrated Gradients and SHAP on prediction error residuals (ML - DFT) from `code/data/processed/residuals.parquet`
- [ ] T032 [US3] Implement logic to rank descriptors and calculate cumulative variance. **Specific Logic**: Calculate cumulative `variance_explained` for sorted descriptors. **Output**: Intermediate ranking data. **Depends on T031**. (FR-005, SC-002)
- [ ] T033 [US3] Select top descriptors and write results. **Logic**: Select smallest subset where cumulative `variance_explained` >= 0.60. Write `code/data/results/top_descriptors_subset.json` and `code/data/results/feature_importance.csv`. **Schema**: `{ "descriptors": [...], "cumulative_variance": float, "total_variance_explained": float }`. **Depends on T032**. (FR-005, SC-002, Constitution Principle VII)
- [ ] T034 [US3] Implement `code/src/analysis/statistics.py` with unpaired Welch's t-test for Group 13 vs. Conventional error distributions (FR-006 adaptation). **Action**: Generate statistical test results (p-value, t-statistic) and log deviation in `code/data/results/deviation_log.md`. **Depends on T027b**. (FR-006 adaptation)
- [ ] T035 [US3] Create `code/data/results/deviation_log.md` documenting the deviation from FR-006 (paired test) to unpaired Welch's t-test. **Required sections**: `Spec Requirement`, `Implemented Logic`, `Statistical Justification`, `Spec Update Request` (Constitution Principle IV). **Depends on T034**.
- [ ] T036a [US3] Perform single-point DFT baseline calculation. **Action**: Extract sample with median barrier height from `code/data/processed/graphs.parquet`. Use `psi4` to calculate B3LYP/STO-3G energy and wall-clock time. **Output**: `code/data/baseline_dft_time.json` with schema `{ "reference_time_seconds": float, "hardware_info": string, "geometry_source": string }`. **Dependencies**: `psi4` installed (T004), `graphs.parquet` (T017c).
- [ ] T036b [US3] Implement speed analysis: measure GNN inference time vs. the DFT baseline. **Input**: `code/data/baseline_dft_time.json` (from T036a) and prediction results from T027a. **Logic**: Compare GNN inference time against the `reference_time_seconds` from T036a. **Output**: `code/data/results/speed_metrics.json` with `speedup_factor`. **Depends on T036a, T027a**.
- [ ] T036c [US3] Generate `code/data/results/statistical_tests.json`. **Input**: T034. **Output**: `code/data/results/statistical_tests.json`.
- [ ] T036d [US3] Generate `code/data/results/speed_metrics.json`. **Input**: T036b. **Output**: `code/data/results/speed_metrics.json`.
- [ ] T037 [US3] Create visualizations of error distributions in `code/src/analysis/visualizations.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Final Validation & Spec Sync. **Action**: 1) Generate `code/data/results/final_metrics_table.csv` comparing SC metrics against community standards. 2) Run constitution check (citations, checksums). 3) Update `spec.md` to reflect deviations (FR-006, FR-008) using `code/data/results/deviation_log.md` (T035) as source. **Output**: Finalized artifacts and updated `spec.md`. **Dependencies**: T036c, T036d, T035, T039 (Constitution Check).

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
- **Speed Analysis Chain**: T036a -> T036b are strictly sequential.

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
- **Deviations**: Any deviation from Spec FRs (e.g., LOOCV -> LLSO) MUST be logged in `code/data/results/deviation_log.md` as per task T034/T035.
- **Spec Updates**: Deviations MUST be reflected in `spec.md` via T038 to maintain the Single Source of Truth.
- **Parallel Execution**: T036a (Phase 5) is designed to run after T017c (Phase 3) data is available, allowing the DFT baseline calculation to proceed in parallel with US3 analysis tasks to optimize the critical path.