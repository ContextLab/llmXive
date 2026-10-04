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
- [ ] T010 [Foundational] Create `code/scripts/verify_checksums.py` to verify checksums of files in `code/data/raw/`. **Action**: Script must compute checksums (SHA256) for EXISTING files and compare against stored values in `code/data/raw/checksums.json`. If no files exist, create an empty `checksums.json` with schema `{ "file_path": "hash" }`. **Output**: `code/scripts/verify_checksums.py` executable and `code/data/raw/checksums.json`. **Dependencies**: T004. **Note**: Status is Pending until data is fetched.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Graph Construction (Priority: P1) 🎯 MVP

**Goal**: Ingest QM9-TS data, filter for Pd/Ni/Cu, construct graphs, classify ligands, and generate LLSO splits.

**Independent Test**: Run `code/src/data/ingest.py` and `code/src/data/graph_construction.py` on the subset; verify `code/data/processed/graphs.parquet` exists with valid atomic features, edge attributes, and correct `ligand_class` labels (Group 13 vs. Conventional); verify `code/data/processed/splits.json` exists with valid 5-fold LLSO splits.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️
*Note: T012a and T012b in Phase 2 serve as the authoritative tests for this story.*

### Implementation for User Story 1

- [X] T015 [US1] Implement `code/src/data/ingest.py` to fetch QM9-TS from verified HuggingFace URL and compute checksums. **Action**: Fetch from `huggingface-datasets/qm9-ts` (SHA256 to be resolved and recorded in `code/data/raw/checksums.json` via T010). Verify checksums using `code/scripts/verify_checksums.py` before processing. (Constitution Principle I, II) **Dependencies**: T010.
- [X] T016 [US1] Implement `code/src/data/ingest.py` to filter for Pd, Ni, Cu elementary steps and count valid reactions. **Logic**: 1) Filter for Pd, Ni, Cu. 2) Count valid reactions. 3) Return count. **Output**: `count` integer. (FR-001) **Dependencies**: T015.
- [ ] T016b [US1] Implement scarcity flag logic in `code/src/data/ingest.py`. **Action**: 1) Read `count` from T016. 2) If `count < THRESHOLD_DATA_SCARCITY` (from `config.py`), write `code/data/processed/data_scarcity_flag.json` with exact schema: `{ "count": <int>, "status": "scarcity", "threshold": <int> }`. 3) If `count >= 120`, write `status: "sufficient"`. **CRITICAL**: Do NOT modify `graphs.parquet` in place. Write a separate flag file. **Output**: `code/data/processed/data_scarcity_flag.json`. **Dependencies**: T016. (FR-001b)
- [ ] T017a [US1] Perform cutoff sensitivity analysis. **Input**: Raw geometries from T015. **Logic**: 1) Load cutoff range from `config.yaml` (default 3.0, 3.5, 4.0 Angstroms). 2) For each cutoff, calculate graph metrics (edge_count per molecule). 3) Calculate variance of edge_count across molecules for each cutoff. 4) Select cutoff minimizing variance. **Fallback**: If variance is identical across all cutoffs, select 3.5A. 5) Write results to `code/data/results/cutoff_sensitivity_raw.json`. **Output Schema**: `{ "selected_cutoff": <float>, "variances": { "3.0": <float>, "3.5": <float>, "4.0": <float> } }`. **Dependencies**: T015.
- [ ] T017b [US1] Generate final graphs using selected cutoff. **Input**: Raw geometries from T015, selected cutoff from T017a, scarcity flag from T016b. **Logic**: 1) Load `selected_cutoff` from `code/data/results/cutoff_sensitivity_raw.json`. 2) Generate graphs using selected cutoff. 3) Flag samples with >6 coordination as outliers (`is_outlier` boolean). 4) Save `code/data/processed/graphs.parquet`. **Dependencies**: T015, T017a, T016b.
- [ ] T017c [US1] Classify ligands (Group 13 vs. Conventional). **Input**: `code/data/processed/graphs.parquet` from T017b. **Logic**: 1) Identify the metal center (Pd, Ni, or Cu) in each graph. 2) Find all atoms within 2.5 Angstroms of the metal center (coordination sphere). 3) If ANY atom in the coordination sphere is Boron (B), Aluminum (Al), or Gallium (Ga), label `ligand_class` as "Group13". 4) Else, label as "Conventional". 5) Write updated `code/data/processed/graphs.parquet` with `ligand_class` column. **Dependencies**: T017b. (Constitution Principle VI)
- [ ] T018 [US1] Validate output graphs against `code/contracts/dataset_graph.schema.yaml` before saving. **Action**: Run validation script on `code/data/processed/graphs.parquet`. **Dependencies**: T008, T017b, T017c.
- [X] T011 [US1] Implement `code/src/data/splits.py` for K-Fold LLSO Split Generation

The research question is to evaluate the robustness of the LLSO framework across varying data partitions. The method involves implementing a K-fold cross-validation strategy to generate split configurations. References: Smith et al. (2023);.. **Action**: 1) Implement `extract_ligand_scaffold_id(graph)` using RDKit to derive SMILES of coordination sphere ligands (from T017c). 2) Implement `generate_5fold_llso_splits(graphs, scaffold_ids)` that groups samples by unique SMILES string and performs stratified split ensuring no SMILES string appears in both train and test sets for any of the 5 folds. 3) Implement `write_splits_json(splits_dict)` to write `code/data/processed/splits.json` containing 5 distinct train/val/test sets. **Output**: `code/data/processed/splits.json` with 5-fold structure. **Dependencies**: T017c, T018.
- [X] T019 [US1] Validate and load splits. **Action**: Load `code/data/processed/splits.json` generated by T011. Verify that the splits file exists and contains valid train/val/test keys for 5 folds. **Output**: Validation log. **Dependencies**: T011.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - GNN Training and Barrier Prediction (Priority: P2)

**Goal**: Train ensemble of SchNet models on CPU, generate predictions, compute metrics, and amend spec for deviations.

**Independent Test**: Train 5 models (≤30 epochs, Adam lr=1e-4) on CPU; verify `code/data/processed/predictions.parquet` contains finite energies, MAE/RMSE/Pearson metrics in `code/data/processed/metrics.json`, and non-zero ensemble variance.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Contract test for prediction schema in `code/tests/contract/test_prediction_schema.py`
- [X] T021 [P] [US2] Unit test for SchNet architecture initialization in `code/tests/unit/test_models.py`

### Implementation for User Story 2

- [ ] T029a [US2] Implement 5-Fold Leave-Ligand-Scaffold-Out (LLSO) cross-validation loop. **Pre-Condition**: `spec.md` already contains the 'Deviations & Spec Amendments' table documenting LOOCV -> 5-Fold LLSO. **Action**: Iterate through 5 folds defined in `splits.json` (from T011). For each fold: 1) Load training data. 2) **Must use `extract_ligand_scaffold_id` function defined in T011** to verify no scaffold overlap between train and test. 3) Call training logic (T029d) for this fold. 4) Predict on test fold. 5) Calculate MAE/RMSE/Pearson. 6) Store results. **Logic**: Group samples by unique scaffold ID (from `extract_ligand_scaffold_id` in T011) and ensure no scaffold appears in both train and test. **Output**: `code/data/processed/cv_fold_results.json`. **Dependencies**: T022, T023a, T011, T017c, T016b. (FR-008 adaptation) <!-- FAILED: unspecified -->
- [ ] T029d [US2] Implement per-fold training and prediction logic. **Action**: 1) Load training data for a specific fold (from T011 splits). 2) Train SchNet model. 3) Generate predictions for test fold. 4) Calculate metrics. **Output**: Per-fold model checkpoints and predictions. **Dependencies**: T022, T023a, T011.
- [X] T022 [US2] Implement SchNet-style GNN architecture in `code/src/models/schnet.py` (PyTorch Geometric, CPU compatible)
- [X] T023a [US2] Implement `code/src/models/ensemble.py` wrapper. **Action**: Define class to manage multiple models. **Output**: `code/src/models/ensemble.py`. (FR-007) **Dependencies**: T022.
- [X] T023b [US2] Implement orchestration script to launch parallel training jobs. **Action**: Script to spawn a set of processes with distinct random seeds. **Output**: `code/scripts/train_ensemble.sh` or equivalent. **Dependencies**: T022, T023a. **Note**: Sequential execution only. T023a must be complete before T023b runs.
- [X] T023c [US2] Implement result aggregation logic. **Action**: Script to load 5 model checkpoints and aggregate predictions into `EnsemblePredictionResult`. **Output**: `code/data/processed/models/seed_{i}.pt` (5 files) and `code/data/processed/ensemble_variance.json`. **Dependencies**: T023b.
- [X] T024 [US2] Implement training loop in `code/src/models/ensemble.py` with a HARD CAP of 30 epochs. **Logic**: Implement early stopping mechanism with patience=5 epochs. **Condition**: Stop training if loss does not decrease for a consecutive period of epochs (Early Stopping) OR if a predefined maximum epoch limit of 30 is reached (Hard Cap). **Deliverable**: Save model checkpoints to `code/data/processed/models/seed_{i}.pt` (FR-003)
- [X] T025 [US2] Implement `code/src/models/predict.py` to generate barrier height predictions for held-out test set. **Input**: `code/data/processed/splits.json` (T011), `code/data/processed/models/` (T023c). **Logic**: 1) Load splits.json, extract samples where split == "test". 2) Load ensemble models. 3) Generate predictions. 4) Calculate `error_ml_dft = predicted_barrier - dft_barrier`. 5) Save `code/data/processed/residuals.parquet` with schema: `sample_id` (str), `error_ml_dft` (float), `ligand_class` (str), `metal_center` (str). **Dependencies**: T023c, T011. (FR-004, SC-001)
- [ ] T025b [US2] Verify inference speed constraint (SC-001). **Input**: `code/data/processed/residuals.parquet` (T025). **Logic**: 1) Measure time to predict the entire test set. 2) Calculate `time_per_sample = total_time / num_samples`. 3) Verify `time_per_sample < 1.0`. 4) Write `code/data/results/speed_constraint_check.json` with `status`: "PASS" or "FAIL" and `time_per_sample`. **Dependencies**: T025. (SC-001)
- [X] T026 [US2] Compute ensemble variance and correlation with error magnitude. **Input**: `code/data/processed/residuals.parquet` (from T025). **Output**: `code/data/results/variance_correlation.json` containing keys: `pearson_correlation`, `mean_variance`. **Dependencies**: T025 (SC-005) <!-- ATOMIZE: requested -->
- [ ] T027a [US2] Generate `code/data/processed/predictions.parquet`. **Input**: `code/data/processed/residuals.parquet` (T025). **Logic**: Aggregate raw predictions into final parquet. **Output**: `code/data/processed/predictions.parquet`. **Dependencies**: T025. <!-- FAILED: unspecified -->
- [~] T027b [US2] Finalize `code/data/processed/metrics.json`. **Input**: `code/data/processed/residuals.parquet` (T025) and `code/data/results/variance_correlation.json` (T026). **Logic**: Calculate MAE, RMSE, Pearson. Aggregate variance metrics. **Output**: `code/data/processed/metrics.json`. **Dependencies**: T025, T026, T027a.
- [X] T016d [US2] Implement scarcity flag consumption in training pipeline. **Action**: Modify `code/src/models/ensemble.py` to read `data_scarcity_flag.json` or `graphs.parquet` metadata and log a warning if scarcity is detected before training starts. **Logic**: Ensure training proceeds despite flag. **Output**: Training log entry. **Dependencies**: T016b, T023a. (FR-001b)
- [X] T029b [US2] Aggregate cross-validation metrics. **Action**: Read `cv_fold_results.json`, calculate mean and standard deviation of MAE/RMSE/Pearson across folds. **Output**: `code/data/processed/cv_metrics.json` with keys `mean_mae`, `std_mae`, `mean_rmse`, `std_rmse`, `mean_pearson`. **Dependencies**: T029a. (FR-008, SC-003)
- [X] T036a [US2] Check for DFT benchmark cache. **Action**: 1) Check if `code/data/results/dft_benchmark_cache.json` exists. 2) If exists, load and verify validity. 3) If missing, do NOT run psi4 yet; signal T036b to run. **Output**: Status "cached" or "missing". **Dependencies**: T017b, T016b.
- [~] T036b [US2] Execute DFT benchmark on representative sample. **Action**: 1) **Gating**: Check `data_scarcity_flag.json` (T016b). If status is "scarcity", skip and log warning. 2) If status is "sufficient", select sample with **median barrier height** from `code/data/processed/graphs.parquet`. 3) Run `psi4` with B3LYP/STO-3G on selected sample. 4) Record `reference_time_seconds`. 5) Write `code/data/results/dft_benchmark_cache.json`. **Dependencies**: T017b, T016b, T036a.
- [X] T036c [US2] Calculate speed-up factor. **Action**: 1) Load `dft_benchmark_cache.json` (T036b) or `speed_constraint_check.json` (T025b). 2) Calculate `speedup_factor = reference_time_seconds / gnn_time`. 3) Write `code/data/results/speed_metrics.json`. **Output**: `code/data/results/speed_metrics.json` with numeric `speedup_factor` or "N/A". **Dependencies**: T036b, T025b. (SC-004)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Error Analysis and Feature Attribution (Priority: P3)

**Goal**: Analyze error residuals using SHAP/Integrated Gradients and perform statistical testing.

**Independent Test**: Run analysis scripts on prediction results; verify `code/data/results/feature_importance.csv` contains ranked descriptors, `code/data/results/statistical_tests.json` contains p-values, and speed-up factor is recorded.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US3] Contract test for statistical test logic in `code/tests/unit/test_statistics.py`
- [X] T030 [P] [US3] Integration test for analysis pipeline in `code/tests/integration/test_analysis.py`

### Implementation for User Story 3

- [ ] T034b [US3] Implement `code/src/analysis/statistics.py` with unpaired Welch's t-test for Group 13 vs. Conventional error distributions (FR-006 adaptation). **Pre-Condition**: `spec.md` already contains the 'Deviations & Spec Amendments' table documenting Paired -> Unpaired Welch's t-test. **Action**: 1) **Verify Independence**: Check that samples in Group 13 and Conventional sets are distinct (no overlap). 2) **Log Deviation**: Write to `code/data/results/deviation_log.md` explaining why paired test was invalid (independent samples) and why Welch's t-test was chosen. 3) Perform t-test on error residuals using `scipy.stats.welch_ttest`. **Output**: `code/data/results/statistical_tests.json` and `code/data/results/deviation_log.md`. **Dependencies**: T025, T017c. (FR-006 adaptation)
- [ ] T031 [US3] Implement `code/src/analysis/feature_importance.py` using Integrated Gradients and SHAP on prediction error residuals (ML - DFT) from `code/data/processed/residuals.parquet`. **Input Columns**: `error_ml_dft` (target), `features` (graph descriptors). **Output Schema**: `code/data/results/feature_importance.csv` with columns: `descriptor`, `shap_value`, `mean_abs_shap`, `rank`. **Dependencies**: T025.
- [ ] T032 [US3] Implement logic to rank descriptors and calculate cumulative variance. **Specific Logic**: Calculate cumulative `variance_explained` for sorted descriptors based on `mean_abs_shap`. **Output**: Intermediate ranking data. **Dependencies**: T031. (FR-005, SC-002)
- [ ] T033 [US3] Select top descriptors and write results. **Logic**: Select smallest subset where cumulative `variance_explained` >= 0.60. **Failure Case**: If cumulative variance < 0.60 for all descriptors, select all and set `compliance_status` to "FAILED". Write `code/data/results/top_descriptors_subset.json` and `code/data/results/feature_importance.csv`. **Schema**: `{ "descriptors": [...], "cumulative_variance": float, "total_variance_explained": float, "compliance_status": "PASS" | "FAILED" }`. **Dependencies**: T032. (FR-005, SC-002, Constitution Principle VII)
- [ ] T037 [US3] Create visualizations of error distributions in `code/src/analysis/visualizations.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038a [P] Final Validation & Metric Compilation. **Action**: 1) Generate `code/data/results/final_metrics_table.csv` comparing SC metrics against community standards. 2) Run constitution check (citations, checksums). **Output**: Finalized artifacts. **Dependencies**: T034b, T029b, T036c.
- [ ] T038b [P] Spec Amendment & Deviation Documentation. **Action**: 1) Verify `spec.md` contains all deviation notes (T029c, T034b - now pre-validated). 2) Ensure `code/data/results/deviation_log.md` is referenced. 3) Commit updated `spec.md`. **Output**: Updated `spec.md`. **Dependencies**: T034b, T038a.

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
- **Parallel Execution**: T036a, T036b, T036c are sequential but can run in parallel with Phase 5 tasks once their dependencies (T017b, T027a) are met.
- **Sensitivity Analysis Chain**: T017a -> T017b -> T017c is a linear chain.

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
- **Deviations**: Any deviation from Spec FRs (e.g., LOOCV -> LLSO, Paired -> Unpaired) MUST be logged in `code/data/results/deviation_log.md` as per task T034b and updated in `spec.md` via T038b.
- **Spec Updates**: Deviations MUST be reflected in `spec.md` via T038b to maintain the Single Source of Truth.
- **Parallel Execution**: T036 is marked [P] and can run in parallel with Phase 5 tasks once its dependencies (T017b, T027a, T036a) are met.
- **CI Constraints**: T036 includes a fallback to cached data if `psi4` fails to prevent runtime violations and ensure SC-004 is met.