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

- [X] T004 Create `code/requirements.txt` with pinned versions: `torch`, `torch-geometric`, `scikit-learn`, `shap`, `pandas`, `numpy`, `pyyaml`, `pytest`, `pytest-cov`, `psi4`. **Note**: Matches plan.md Technical Context dependencies.
- [X] T005a [P] [Foundational] Create `code/scripts/setup.sh` to initialize the Python environment. **Action**: Script must create a virtualenv in `code/venv/` and install `code/requirements.txt`. **Output**: `code/scripts/setup.sh` executable.
- [X] T005b [P] [Foundational] Execute `code/scripts/setup.sh` to activate the environment and install dependencies. **Action**: Run `bash code/scripts/setup.sh`. **Depends on T005a**.
- [X] T006 Implement `code/src/utils/config.py` for loading YAML configuration and environment variables. **Action**: Define `config` dict with `THRESHOLD_DATA_SCARCITY` (default 120), `PSI4_BASIS` (default "sto-3g"), and `CUTOFF_RANGE` (default [3.0, 3.5, 4.0]).
- [X] T007 Implement `code/src/utils/logging.py` for structured logging and progress tracking
- [X] T008 Create `code/contracts/dataset_graph.schema.yaml` defining `TransitionStateGraph` attributes (nodes, edges, energy_dft, barrier_height, metal_center, ligand_class). **Output**: Valid YAML schema file.
- [X] T009 Create `code/contracts/prediction_schema.yaml` defining `PredictionResult` and `EnsemblePredictionResult` structures
- [X] T010 [Foundational] Create `code/scripts/verify_checksums.py` to verify checksums of files in `code/data/raw/`. **Action**: Script must compute checksums (SHA256) and compare against stored values in `code/data/raw/checksums.json`. **Output**: `code/scripts/verify_checksums.py` executable and `code/data/raw/checksums.json` with schema `{ "file_path": "hash" }`. **Dependencies**: T004.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Graph Construction (Priority: P1) 🎯 MVP

**Goal**: Ingest QM9-TS data, filter for Pd/Ni/Cu, construct graphs, classify ligands, and generate LLSO splits.

**Independent Test**: Run `code/src/data/ingest.py` and `code/src/data/graph_construction.py` on the subset; verify `code/data/processed/graphs.parquet` exists with valid atomic features, edge attributes, and correct `ligand_class` labels (Group 13 vs. Conventional); verify `code/data/processed/splits.json` exists with valid LLSO splits.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️
*Note: T012a and T012b in Phase 2 serve as the authoritative tests for this story.*

### Implementation for User Story 1

- [ ] T015 [US1] Implement `code/src/data/ingest.py` to fetch QM9-TS from verified HuggingFace URL and compute checksums. **Action**: Fetch from `huggingface-datasets/qm9-ts` (SHA256 to be resolved and recorded in `code/data/raw/checksums.json` via T010). Verify checksums using `code/scripts/verify_checksums.py` before processing. (Constitution Principle I, II) **Dependencies**: T010.
- [ ] T016 [US1] Implement `code/src/data/ingest.py` to filter for Pd, Ni, Cu elementary steps and count valid reactions. **Logic**: 1) Filter for Pd, Ni, Cu. 2) Count valid reactions. 3) Return count. **Output**: `count` integer. (FR-001) **Dependencies**: T015.
- [ ] T016b [US1] Implement scarcity flag logic in `code/src/data/ingest.py`. **Logic**: If count < `THRESHOLD_DATA_SCARCITY` (from `config.py`), write `code/data/processed/data_scarcity_flag.json` with exact schema: `{ "count": <int>, "status": "scarcity", "threshold": <int> }`. **CRITICAL**: Also update `code/data/processed/graphs.parquet` metadata to include `scarcity_flag: true` if applicable. **Action**: Log a warning to stdout/stderr: "Data scarcity detected: {count} < {threshold}. Proceeding with limited data." **Dependencies**: T016. (FR-001b)
- [ ] T017 [US1] Perform cutoff sensitivity analysis and generate final graphs. **Input**: Raw geometries from T015. **Logic**: 1) Load cutoff range from `config.yaml` (default 3.0, 3.5, 4.0 Angstroms). 2) Calculate graph metrics (avg_degree, edge_count, density) for each. 3) Write results to `code/data/results/cutoff_sensitivity_raw.json`. 4) Select cutoff minimizing metric variance (justification required in log). 5) Generate graphs using selected cutoff. 6) Flag samples with >6 coordination as outliers (`is_outlier` boolean). 7) Save final `code/data/processed/graphs.parquet`. **Output**: `code/data/processed/graphs.parquet`, `code/data/results/cutoff_sensitivity.json`. **Dependencies**: T015, T016.
- [ ] T018 [US1] Validate output graphs against `code/contracts/dataset_graph.schema.yaml` before saving. **Action**: Run validation script on `code/data/processed/graphs.parquet`. **Dependencies**: T008, T017.
- [ ] T011 [US1] Implement `code/src/data/splits.py` for LLSO Split Generation. **Action**: 1) Implement `extract_ligand_scaffold_id(graph)` using RDKit to derive SMILES of coordination sphere ligands. 2) Implement `generate_llso_splits(graphs, scaffold_ids)` that groups samples by unique SMILES string and performs stratified split ensuring no SMILES string appears in both train and test sets (Leave-Ligand-Scaffold-Out). 3) Implement `write_splits_json(splits_dict)` to write `code/data/processed/splits.json`. **Output**: `code/data/processed/splits.json`. **Dependencies**: T017, T018.
- [ ] T019 [US1] Validate and load splits. **Action**: Load `code/data/processed/splits.json` generated by T011. Verify that the splits file exists and contains valid train/val/test keys. **Output**: Validation log. **Dependencies**: T011.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - GNN Training and Barrier Prediction (Priority: P2)

**Goal**: Train ensemble of SchNet models on CPU, generate predictions, compute metrics, and amend spec for deviations.

**Independent Test**: Train 5 models (≤30 epochs, Adam lr=1e-4) on CPU; verify `code/data/processed/predictions.parquet` contains finite energies, MAE/RMSE/Pearson metrics in `code/data/processed/metrics.json`, and non-zero ensemble variance.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Contract test for prediction schema in `code/tests/contract/test_prediction_schema.py`
- [X] T021 [P] [US2] Unit test for SchNet architecture initialization in `code/tests/unit/test_models.py`

### Implementation for User Story 2

- [ ] T029c [US2] **Spec Amendment**: Update `spec.md` to reflect FR-008 deviation (LOOCV -> 5-Fold LLSO). **Action**: 1) Edit `spec.md` in `specs/001-machine-learned-potentials/`. 2) Add entry to "Spec Deviation Notes" table. 3) Commit updated `spec.md`. **Output**: Updated `spec.md`. **Dependencies**: (None - based on plan decision). **MUST BE COMPLETED BEFORE T029a**.
- [ ] T029a [US2] Implement 5-Fold Leave-Ligand-Scaffold-Out (LLSO) cross-validation loop. **Action**: Iterate through 5 folds defined in `splits.json` (from T011). For each fold: 1) Train model on train fold. 2) Predict on test fold. 3) Calculate MAE/RMSE/Pearson. 4) Store results. **Logic**: Group samples by unique scaffold ID (from `extract_ligand_scaffold_id` in T011) and ensure no scaffold appears in both train and test. **Output**: `code/data/processed/cv_fold_results.json`. **Dependencies**: T022, T011, T029c. (FR-008 adaptation)
- [ ] T022 [US2] Implement SchNet-style GNN architecture in `code/src/models/schnet.py` (PyTorch Geometric, CPU compatible)
- [ ] T023a [US2] Implement `code/src/models/ensemble.py` wrapper. **Action**: Define class to manage multiple models. **Output**: `code/src/models/ensemble.py`. (FR-007) **Dependencies**: T022.
- [ ] T023b [US2] Implement orchestration script to launch parallel training jobs. **Action**: Script to spawn a set of processes with distinct random seeds. **Output**: `code/scripts/train_ensemble.sh` or equivalent. **Dependencies**: T022, T023a. **Note**: Sequential execution only. T023a must be complete before T023b runs.
- [ ] T023c [US2] Implement result aggregation logic. **Action**: Script to load 5 model checkpoints and aggregate predictions into `EnsemblePredictionResult`. **Output**: `code/data/processed/models/seed_{i}.pt` (5 files) and `code/data/processed/ensemble_variance.json`. **Dependencies**: T023b.
- [ ] T024 [US2] Implement training loop in `code/src/models/ensemble.py` with a HARD CAP of 30 epochs. **Logic**: Implement early stopping mechanism with patience=5 epochs. **Condition**: Stop training if loss does not decrease for a consecutive period of epochs (Early Stopping) OR if a predefined maximum epoch limit of 30 is reached (Hard Cap). **Deliverable**: Save model checkpoints to `code/data/processed/models/seed_{i}.pt` (FR-003)
- [ ] T025 [US2] Implement `code/src/models/predict.py` to generate barrier height predictions for held-out test set. **Primary Deliverable**: Generate `code/data/processed/residuals.parquet` containing per-sample error residuals (ML - DFT). **Schema**: `sample_id` (str), `error_ml_dft` (float), `ligand_class` (str), `metal_center` (str). **Note**: Do NOT generate `metrics.json` yet. (FR-004, SC-001)
- [ ] T026 [US2] Compute ensemble variance and correlation with error magnitude. **Input**: `code/data/processed/residuals.parquet` (from T025). **Output**: `code/data/results/variance_correlation.json` containing keys: `pearson_correlation`, `mean_variance`. **Dependencies**: T025 (SC-005)
- [ ] T027a [US2] Generate `code/data/processed/predictions.parquet`. **Input**: `code/data/processed/residuals.parquet` (T025). **Logic**: Aggregate raw predictions into final parquet. **Output**: `code/data/processed/predictions.parquet`. **Dependencies**: T025.
- [ ] T027b [US2] Finalize `code/data/processed/metrics.json`. **Input**: `code/data/processed/residuals.parquet` (T025) and `code/data/results/variance_correlation.json` (T026). **Logic**: Calculate MAE, RMSE, Pearson. Aggregate variance metrics. **Output**: `code/data/processed/metrics.json`. **Dependencies**: T025, T026, T027a.
- [ ] T016d [US2] Implement scarcity flag consumption in training pipeline. **Action**: Modify `code/src/models/ensemble.py` to read `data_scarcity_flag.json` or `graphs.parquet` metadata and log a warning if scarcity is detected before training starts. **Logic**: Ensure training proceeds despite flag. **Output**: Training log entry. **Dependencies**: T016b, T023a. (FR-001b)
- [ ] T029b [US2] Aggregate cross-validation metrics. **Action**: Read `cv_fold_results.json`, calculate mean and standard deviation of MAE/RMSE/Pearson across folds. **Output**: `code/data/processed/cv_metrics.json` with keys `mean_mae`, `std_mae`, `mean_rmse`, `std_rmse`, `mean_pearson`. **Dependencies**: T029a. (FR-008, SC-003)
- [ ] T036 [P] [US2] Perform DFT baseline and calculate speed-up factor. **Action**: 1) Extract sample with median barrier height from `code/data/processed/graphs.parquet`. 2) Generate XYZ input file. 3) Run `psi4` with B3LYP/STO-3G (if available; skip with warning on CI). 4) Record `reference_time_seconds`. 5) Measure GNN inference time for same sample from `code/data/processed/predictions.parquet`. 6) Calculate `speedup_factor = reference_time_seconds / gnn_time`. 7) Write `code/data/results/speed_metrics.json`. **CRITICAL**: If `psi4` fails, load `code/data/results/dft_benchmark_cache.json` (verified cached time) and use that value to calculate `speedup_factor`. **Output**: `code/data/results/speed_metrics.json` with a numeric `speedup_factor`. **Dependencies**: T017, T027a. (SC-004)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Error Analysis and Feature Attribution (Priority: P3)

**Goal**: Analyze error residuals using SHAP/Integrated Gradients and perform statistical testing.

**Independent Test**: Run analysis scripts on prediction results; verify `code/data/results/feature_importance.csv` contains ranked descriptors, `code/data/results/statistical_tests.json` contains p-values, and speed-up factor is recorded.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US3] Contract test for statistical test logic in `code/tests/unit/test_statistics.py`
- [ ] T030 [P] [US3] Integration test for analysis pipeline in `code/tests/integration/test_analysis.py`

### Implementation for User Story 3

- [ ] T034b [US3] **Spec Amendment**: Update `spec.md` to reflect FR-006 deviation (Paired -> Unpaired Welch's t-test). **Action**: 1) Edit `spec.md` in `specs/001-machine-learned-potentials/`. 2) Add entry to "Spec Deviation Notes" table. 3) Commit updated `spec.md`. **Output**: Updated `spec.md`. **Dependencies**: (None - based on plan decision). **MUST BE COMPLETED BEFORE T034**.
- [ ] T034 [US3] Implement `code/src/analysis/statistics.py` with unpaired Welch's t-test for Group 13 vs. Conventional error distributions (FR-006 adaptation). **Action**: Perform t-test on error residuals using `scipy.stats.welch_ttest`. Log deviation in `code/data/results/deviation_log.md` immediately upon execution (mandatory). **Output**: `code/data/results/statistical_tests.json` and `code/data/results/deviation_log.md`. **Dependencies**: T027b, T034b. (FR-006 adaptation)
- [ ] T031 [US3] Implement `code/src/analysis/feature_importance.py` using Integrated Gradients and SHAP on prediction error residuals (ML - DFT) from `code/data/processed/residuals.parquet`
- [ ] T032 [US3] Implement logic to rank descriptors and calculate cumulative variance. **Specific Logic**: Calculate cumulative `variance_explained` for sorted descriptors. **Output**: Intermediate ranking data. **Dependencies**: T031. (FR-005, SC-002)
- [ ] T033 [US3] Select top descriptors and write results. **Logic**: Select smallest subset where cumulative `variance_explained` >= 0.60. Write `code/data/results/top_descriptors_subset.json` and `code/data/results/feature_importance.csv`. **Schema**: `{ "descriptors": [...], "cumulative_variance": float, "total_variance_explained": float }`. **Dependencies**: T032. (FR-005, SC-002, Constitution Principle VII)
- [ ] T037 [US3] Create visualizations of error distributions in `code/src/analysis/visualizations.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038a [P] Final Validation & Metric Compilation. **Action**: 1) Generate `code/data/results/final_metrics_table.csv` comparing SC metrics against community standards. 2) Run constitution check (citations, checksums). **Output**: Finalized artifacts. **Dependencies**: T034, T029b, T036.
- [ ] T038b [P] Spec Amendment & Deviation Documentation. **Action**: 1) Verify `spec.md` contains all deviation notes (T029c, T034b). 2) Ensure `code/data/results/deviation_log.md` is referenced. 3) Commit updated `spec.md`. **Output**: Updated `spec.md`. **Dependencies**: T034, T038a.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Phase 4 -> Phase 5**: Phase 5 tasks (T031-T037) are blocked until Phase 4 (T022-T029b) is fully complete.

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
- **Parallel Execution**: T036 is designed to run after T017c (Phase 3) data is available, allowing the DFT baseline calculation to proceed in parallel with US3 analysis tasks to optimize the critical path, but must wait for T017c completion.
- **Sensitivity Analysis Chain**: T017 is a single cohesive task.

### Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CPU Constraint**: All tasks must run on free CPU-only CI with limited resources (no GPU). No 8-bit/4-bit quantization or CUDA-specific code.
- **Data Integrity**: No synthetic data generation. All inputs must come from real, verified sources (QM9-TS).
- **Deviations**: Any deviation from Spec FRs (e.g., LOOCV -> LLSO, Paired -> Unpaired) MUST be logged in `code/data/results/deviation_log.md` as per task T034 and updated in `spec.md` via T038b.
- **Spec Updates**: Deviations MUST be reflected in `spec.md` via T029c and T034b to maintain the Single Source of Truth.
- **Parallel Execution**: T036 is marked [P] and can run in parallel with Phase 5 tasks once its dependencies (T017, T027a) are met.
- **CI Constraints**: T036 includes a fallback to cached data if `psi4` is skipped to prevent runtime violations and ensure SC-004 is met.