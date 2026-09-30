# Tasks: Predicting Molecular Properties from Topological Data Analysis

**Input**: Design documents from `/specs/001-predict-molecular-properties-tda/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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

- [ ] T001 Create project structure per implementation plan. **Deliverable**: Execute `mkdir -p projects/PROJ-444-predicting-molecular-properties-from-top/{code,data/raw,data/processed,data/logs,tests,reports,state}` and create `projects/PROJ-444-predicting-molecular-properties-from-top/README.md` with the text "Project: Predicting Molecular Properties from TDA". **Verification**: Verify all directories exist and `README.md` is non-empty.
- [X] T002 Initialize Python 3.11 project. **Deliverable**: Create `code/requirements.txt` containing the following pinned dependencies: `rdkit`, `gudhi`, `dionysus2`, `scikit-learn`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `pyyaml`, `requests`, `pytest`, `memory-profiler`, `statsmodels`. **Verification**: Verify `code/requirements.txt` exists and contains the listed packages.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools by creating `pyproject.toml` with valid `[tool.black]` and `[tool.ruff]` sections. **Verification**: Verify `pyproject.toml` exists and contains valid TOML syntax with the required tool sections. Do not run linters on empty codebases.
- [X] T004 [P] Implement `code/setup_dirs.py` to create `data/raw/`, `data/processed/`, and `data/logs/` directories and `state/` tracking; verify script execution creates these directories. **Dependency**: T001.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T007 [P] Implement `code/00_checksum_verify.py` to compute SHA256 hashes of raw data and record them in `data/checksums.txt` (Constitution III). **Verification**: Run script and assert `data/checksums.txt` exists, is non-empty, and contains valid SHA256 hashes for all files in `data/raw/`. The verification must compare the *content hash* of the file against the recorded hash to ensure integrity, ignoring file modification timestamps to maintain reproducibility across re-downloads. **Error Handling**: If `data/raw/` is empty or missing, the script MUST exit with `SystemExit(1)` and message "Data Hygiene Failed: No raw data found to checksum."
- [X] T005 [P] Implement `code/utils/graph_builder.py` for RDKit molecular graph construction. **Deliverable**: Implement function `build_graph(smiles: str) -> Optional[Graph]` and `validate_graph(graph: Graph) -> bool`. **Validity Checks**: `valence` (no atoms with incorrect electron count), `aromaticity` (ring detection), and `bond_order` (single/double/triple). **Verification**: Unit tests confirm invalid SMILES return `None` and valid SMILES return a graph with correct connectivity.
- [X] T006 [P] Implement `code/utils/persistence_utils.py` for shortest-path filtration and empty diagram handling. **Deliverable**: Implement `compute_filtration(graph: Graph) -> Diagram` using Dijkstra's algorithm for shortest-path distances. Implement `vectorize(diagram: Diagram, resolution: int) -> np.ndarray`. **Empty Handling**: If diagram is empty, return `np.zeros(resolution * resolution)`. **Verification**: Verify `vectorize` returns a zero-vector for linear chain molecules and valid vectors for ring structures.
- [X] T008a [P] [US1] Implement `code/01_data_ingestion.py` (Part 1): Fetch MoleculeNet ESOL, validate `smiles`/`logP` columns against schema, and perform a priori power analysis (N>=128). **Verification**: Script must exit with `SystemExit(1)` if columns are missing or N < 128. No synthetic fallback.
- [ ] T008b [P] [US1] Implement `code/01_data_ingestion.py` (Part 2): Enforce min scaffolds check (>=100 unique scaffolds per Plan.md 'Scaffold Validation'), implement a custom scaffold splitter using `rdkit.Chem.Scaffolds.MurckoScaffold.GetScaffoldForMol` to group molecules, perform a 5-fold split with `seed=42`, and save split indices to `data/processed/splits.json`. **Dependency**: T008a. **Verification**:
 1. **Power Check**: Verify script exits with `SystemExit(1)` if N < 128 (Power Insufficient).
 2. **Scaffold Check**: Verify script exits with `SystemExit(1)` if unique scaffolds < 100 (Message: "Scaffold Insufficient: <count> < 100").
 3. **Split Output**: Verify `data/processed/splits.json` exists, is valid JSON, and contains 5-fold indices.
 4. **Error Handling**: If validation fails, log specific reason ("Power Insufficient" or "Scaffold Insufficient: <count> < 100") before exiting.
- [X] T029 [P] [Foundational] Implement `code/07_resource_monitor.py` as a pipeline wrapper to enforce "fail-fast" on resource limits (SC-004). **Function**: Wrap the main pipeline execution; monitor RAM/CPU usage in real-time; if RAM > 6.3GB or CPU time > 5.4h, raise `SystemExit(1)` with a descriptive error. **Verification**: Simulate resource exhaustion (e.g., via sleep or memory allocation) and verify the script raises `SystemExit(1)` before completion.
- [ ] T010 [P] [US1] Contract test for `data/processed/tda_features.csv` schema in `tests/contract/test_tda_schema.py`. **Specification**: Validate against `specs/001-predict-molecular-properties-tda/contracts/feature_matrix.schema.yaml`. **Test Function**: `test_tda_schema_compliance`. **Verification**: Ensure test fails if columns are missing or data types mismatch.
- [X] T011 [P] [US1] Integration test for disconnected graph handling in `tests/integration/test_disconnected_graphs.py`. **Input**: `data/raw/test_disconnected.csv` (contains known disconnected SMILES). **Assertion**: `assert tda_vector == [0.0]*100` for disconnected IDs. **Verification**: Run test and confirm zero-vector output.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Compute TDA Features for Molecular Dataset (Priority: P1) 🎯 MVP

**Goal**: Ingest ESOL dataset, compute persistence diagrams via shortest-path filtration, and vectorize to persistence images with a fixed grid resolution.

**Independent Test**: Run `02_tda_computation.py` on a fixed subset; verify output CSV has non-null topological descriptors for every valid molecule AND verify that the 10x10 baseline is generated.

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/02_tda_computation.py`: Graph construction and shortest-path filtration (FR-001). **Deliverable**: Pipeline to convert SMILES to graphs and compute persistence diagrams.
- [ ] T013 [US1] Implement `code/02_tda_computation.py`: Vectorization to persistence images of **exactly 10x10 resolution** (FR-002) for the **Primary Experiment**. **Deliverable**: Generate `data/processed/persistence_images_10x10.csv`. **Verification**: Run contract test to ensure file exists, schema matches, and no NaN values in topological columns. Include zero-vector fallback for empty diagrams. **Schema**: `molecule_id` (string) + 100 float columns (`p_img_0` to `p_img_99`). **Note**: This file is the "Primary Baseline" for the study.
- [ ] T015a [US1] Implement error handling for invalid SMILES in `code/02_tda_computation.py`: Log errors to `data/logs/invalid_smiles.log` AND write exclusions to `data/excluded_smiles_manifest.csv`. **Dependency**: T004 (ensures `data/logs/` exists). **Constitution VI Compliance**: The script MUST log the exclusion. **Verification**: Verify log file is created and manifest exists.
- [X] T015b [US1] Implement sparse matrix logic with memory threshold checks in `code/utils/persistence_utils.py` to handle extremely large molecular weights (Edge Case). **Threshold**: If estimated RAM usage > 6.0GB, use `scipy.sparse.csr_matrix` format. **Verification**: Verify script handles large inputs without crashing and uses sparse structures where applicable.
- [X] T016 [US1] Generate `data/processed/tda_features.csv` (primary dimensions) and `data/processed/traditional_descriptors.csv`. **Dependency**: T008b, T012, T013. **Schema**: `molecule_id` (string), `MW` (float), `logP` (float), `p_img_0`...`p_img_99` (float). **Merge Logic**: Merge on `molecule_id`. **Verification**: Run contract test to verify schema compliance and confirm non-null values for every valid molecule. **Note**: T016 depends on T013 (Primary Baseline) to ensure all required artifacts are present.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (features computed and cached)

---

## Phase 4: User Story 2 - Train and Compare Predictive Models (Priority: P2)

**Goal**: Train Linear Regression (L2) and Random Forest on Traditional, Topological, and Combined feature sets using scaffold splits.

**Independent Test**: Execute `04_model_training.py`; verify R²/RMSE reported for all configurations and folds.

### Implementation for User Story 2

- [ ] T017 [US2] Implement `code/03_feature_engineering.py`: Merge traditional descriptors and TDA features; prepare combined feature matrix. **Input**: `data/processed/traditional_descriptors.csv`, `data/processed/tda_features.csv`. **Output**: `data/processed/combined_features.csv`. **Merge Key**: `molecule_id`. **Verification**: Verify output contains all columns and rows match input.
- [ ] T021 [US2] Add runtime GPU check (FR-008) using generic CUDA detection. **Checks**: `os.environ.get('CUDA_VISIBLE_DEVICES')`, `torch.cuda.is_available()`, and `gudhi` GPU flags. **Action**: Raise `SystemExit(1)` if any GPU acceleration is detected; do not rely on `torch`. **Verification**: Run script in a simulated GPU environment and verify it exits with `SystemExit(1)` and message "GPU Detected: FR-008 Violation".
- [ ] T018 [US2] Implement `code/04_model_training.py`: Load split indices from T008b (`data/processed/splits.json`) and apply to training data. **Dependency**: T008b, T021 (Safety Gate). **Verification**: Ensure `data/processed/splits.json` is loaded successfully and splits are applied correctly.
- [ ] T019 [US2] Implement `code/04_model_training.py`: Train Linear Regression (alpha=1.0) and Random Forest (100 trees, max_depth=10) on 3 feature sets. **Input**: `data/processed/combined_features.csv`. **Target**: `logP`. **Output**: `data/models/` (pickle files for each model). **Verification**: Verify models are saved and loadable.
- [ ] T020 [US2] Implement `code/04_model_training.py`: Calculate R² and RMSE per fold; aggregate metrics. **Aggregation**: Mean and Standard Deviation. **Deliverable**: Load pickle files from `data/models/`, extract `feature_importance_` attribute from scikit-learn models, and populate the `feature_importance` section. **Output**: `reports/metrics/model_performance.json`. **Verification**: Run `pytest tests/contract/test_metrics_schema.py`.
- [ ] T022 [US2] Generate `reports/metrics/model_performance.json`. **Schema**: `{ "traditional": { "r2_per_fold": [], "rmse_per_fold": [], "r2_mean": float, "rmse_mean": float }, "topological": { "r2_per_fold": [], "rmse_per_fold": [], "r2_mean": float, "rmse_mean": float }, "combined": { "r2_per_fold": [], "rmse_per_fold": [], "r2_mean": float, "rmse_mean": float }, "feature_importance": { "traditional": [], "topological": [] } }`. **Verification**: Run `pytest tests/contract/test_metrics_schema.py`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Validate Methodological Rigor and Sensitivity (Priority: P3)

**Goal**: Apply Holm-Bonferroni correction, run VIF diagnostics, and quantify feature redundancy.

**Independent Test**: Inspect logs/reports to confirm corrected p-values, VIF flags, and MI scores are present.

### Implementation for User Story 3

- [ ] T041 [US3] **Generate Sensitivity Data**: Compute persistence images for a range of resolutions, including low and moderate grid sizes, specifically for the sensitivity sweep. **Input**: `data/processed/tda_features.csv`. **Output**: `data/processed/persistence_images_20x20.csv`, `data/processed/persistence_images_30x30.csv`. **Dependency**: T012 (Graph logic), T013 (Vectorization logic). **Verification**: Ensure files exist, contain valid vectors, and are distinct from the 10x10 baseline. **Note**: This task is added to separate sensitivity data generation from the US1 baseline generation (T013).
- [ ] T023 [US3] Implement `code/05_sensitivity_analysis.py`: **Execute** the sensitivity analysis by consuming the persistence images from T013 (10x10), T041 (20x20, 30x30), and the model metrics from T019/T020. Calculate R² variance across resolutions and generate the final stability report. **Dependency**: T013, T041, T019, T020. **Deliverable**: Generate `reports/metrics/sensitivity_analysis.json` containing `resolutions`, `r2_scores`, and `r2_variance`. **Verification**: Ensure file contains the required keys and that the analysis is based on real model performance, not synthetic data.
- [ ] T025 [US3] Implement `code/06_diagnostics.py`: Apply **Holm-Bonferroni correction** to p-values generated in T019/T020. **Dependency**: T019, T020. **Note**: This task implements 'Holm-Bonferroni' as mandated by the Spec (FR-005) and Plan. **Handling N=1**: If N=1 (single property), the correction is mathematically identity; the task must log this fact and proceed without error, acknowledging the methodological limitation per Plan.md. **Verification**: Verify the correct **Holm-Bonferroni** algorithm is used and the N=1 case is handled gracefully.
- [ ] T026 [US3] Implement `code/06_diagnostics.py`: Calculate VIF; flag predictors > 5 (FR-007). **Input**: `data/processed/combined_features.csv`. **Method**: `statsmodels.stats.outliers_influence.variance_inflation_factor`. **Output**: `reports/metrics/diagnostics.json`. **Verification**: Ensure VIF values are calculated and predictors > 5 are flagged.
- [ ] T027 [US3] Implement `code/06_diagnostics.py`: Calculate Mutual Information between traditional and topological feature sets (FR-009). **Input**: `data/processed/traditional_descriptors.csv`, `data/processed/tda_features.csv`. **Method**: `sklearn.feature_selection.mutual_info_regression`. **Output**: `reports/metrics/diagnostics.json` (float value). **Verification**: Ensure the calculation is performed and reported without arbitrary threshold logic.
- [ ] T028 [US3] Generate `reports/metrics/diagnostics.json` with VIF flags, corrected p-values, MI scores, and **Methodological Summary**. **Schema**: `{ "vif": { "feature": value }, "corrected_pvalues": { "test": value }, "mutual_information": value, "methodology": { "correction_method": "Holm-Bonferroni", "controlled_alpha": 0.05 } }`. **Dependency**: T025, T026, T027. **Task Detail**: **Verification**: Ensure the output includes the `controlled_alpha` and `correction_method` fields, explicitly stating that FWER is controlled at 0.05 by the method, not calculated as a statistic.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 [P] Documentation updates: Update `docs/` and `quickstart.md` with specific sections on TDA methodology and reproducibility steps
- [ ] T031 [P] Code cleanup: Refactor `code/utils/graph_builder.py` to reduce cyclomatic complexity to < 10. **Target**: Function `build_graph`. **Tool**: `ruff check --select C901`. **Verification**: Run `ruff` and confirm max complexity < 10.
- [ ] T032 [Polish] Performance optimization: Profile `code/02_tda_computation.py` for memory usage and ensure it stays within SC-004 limits (< 6.3GB RAM). **Dependency**: Requires T012/T013 completion. **Tool**: `memory_profiler`. **Metrics**: `peak_memory`. **Output**: `reports/metrics/memory_profile.json`.
- [ ] T033 [P] Additional unit tests: Implement `tests/unit/` for graph builder and persistence utils. **Functions**: `test_graph_build`, `test_empty_diagram`. **Inputs**: `valid_smiles`, `disconnected_smiles`. **Assertions**: `assert graph is not None`, `assert len(graph.nodes) > 0`. **Verification**: Run `pytest tests/unit/`.
- [ ] T034 [P] Run quickstart.md validation to ensure full pipeline reproducibility. **Method**: `bash code/quickstart.sh`. **Success Criteria**: `exit code 0`. **Output**: `reports/logs/quickstart.log`. **Verification**: Verify log contains success message.

---

## Phase O: Review Resolution & Final Verification

**Purpose**: Address specific unresolved claims and ensure strict adherence to the "Real Data Only" constitution.

- [ ] T035 [P] [US1/US2] **Resolve Data Ingestion Validation**: Update `code/01_data_ingestion.py` to explicitly handle missing data by adding a runtime assertion that halts execution if the MoleculeNet ESOL dataset cannot be fetched or validated against the `dataset.schema.yaml` columns (`smiles`, `logP`). **Specifics**: Raise `SystemExit(1)` with message "Data Gap: Missing required columns or fetch failed. No synthetic fallback." Log validation errors to `data/logs/ingestion_errors.log`. **Verification**: Run script with invalid URL and assert SystemExit(1).
- [ ] T036 [P] [US2] **Resolve Model Logging**: Update `code/04_model_training.py` to explicitly log the exact seed (42) and split methodology (ScaffoldSplitter) used for the Random Forest and Linear Regression models. **Log Format**: `INFO: Seed: 42`, `INFO: Splitter: ScaffoldSplitter`. **Log File**: `data/logs/training.log`. **Verification**: Check logs for required strings.
- [ ] T037 [P] [US3] **Resolve VIF Reporting**: Update `code/06_diagnostics.py` to output a detailed VIF report in `reports/metrics/diagnostics.json` that explicitly lists the VIF value for every predictor. **Schema**: `{ "vif": { "feature_name": float } }`. **Verification**: Ensure JSON contains all predictors.
- [ ] T040 [P] [US3] **Statistical Rigor Check**: Implement unit tests for Holm-Bonferroni correction in `tests/unit/test_correction.py`. **Verification Method**: Unit test with known p-values. **Expected Output**: `corrected_pvalues.json`. **Verification**: Ensure the implementation uses **Holm-Bonferroni** and not standard Bonferroni.

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

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
