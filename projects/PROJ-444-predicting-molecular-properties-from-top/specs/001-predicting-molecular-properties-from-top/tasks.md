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

## Phase 0: Prerequisites (COMPLETED)

**Purpose**: Tasks required before Phase 1 begins. These are marked as completed and serve as a reference.

- [X] T009 [P] [Foundational] Generate Contract Schemas. **Deliverable**: Create `specs/001-predict-molecular-properties-tda/contracts/dataset.schema.yaml`, `feature_matrix.schema.yaml`, and `model_metrics.schema.yaml` based on the plan's data model. **Verification**: Verify all three YAML files exist and contain valid schema definitions (properties, types, required fields). **Status**: COMPLETED. Reference only.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create project directory structure. **Deliverable**: Execute `mkdir -p projects/PROJ-444-predicting-molecular-properties-from-top/{code,data/raw,data/processed,data/logs,tests,reports,state}`. **Verification**: Verify all directories exist.
- [X] T001b [P] Create project README. **Deliverable**: Create `projects/PROJ-444-predicting-molecular-properties-from-top/README.md` with the text "Project: Predicting Molecular Properties from TDA". **Verification**: Verify `README.md` is non-empty.
- [X] T002 [P] Initialize Python 3.11 project. **Deliverable**: Create `code/requirements.txt` containing the following pinned dependency list: `rdkit`, `gudhi`, `dionysus2`, `scikit-learn`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `pyyaml`, `requests`, `pytest`, `memory-profiler`, `statsmodels`. **Verification**: Verify `code/requirements.txt` exists and contains the listed packages.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools by creating `pyproject.toml` with valid `[tool.black]` and `[tool.ruff]` sections. **Verification**: Verify `pyproject.toml` exists and contains valid TOML syntax with the required tool sections. Do not run linters on empty codebases.
- [X] T004 [P] Implement `code/setup_dirs.py` to create `data/raw/`, `data/processed/`, and `data/logs/` directories and `state/` tracking; verify script execution creates these directories. **Dependency**: T001a.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T007 [Foundational] Implement `code/00_checksum_verify.py` to compute SHA256 hashes of raw data and record them in `data/checksums.txt` (Constitution III) AND update `state/projects/PROJ-444-predicting-molecular-properties-from-top.yaml` with `artifact_hashes`. **Dependency**: T009. **Verification**: Run script and assert `data/checksums.txt` exists, is non-empty, and contains valid SHA256 hashes for all files in `data/raw/`. **State Check**: Verify `state/projects/PROJ-444-predicting-molecular-properties-from-top.yaml` is updated with `artifact_hashes` and that the *content hash* of the recorded entry matches the computed hash of the file to ensure integrity. **Error Handling**: If `data/raw/` is empty or missing, the script MUST exit with `SystemExit(1)` and message "Data Hygiene Failed: No raw data found to checksum." **Note**: This task must be executed AFTER T008a populates `data/raw/`.
- [ ] T008a [Foundational] [US1] Implement `code/01_data_ingestion.py` (Part 1): Fetch MoleculeNet ESOL from `https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/dataset_esol.csv`, validate `smiles`/`logP` columns against `specs/001-predict-molecular-properties-tda/contracts/dataset.schema.yaml`, and perform a priori power analysis (N>=128). **Parameters**: alpha=0.05, power=0.8, effect_size=0.5 (scipy.stats.power). **Deliverable**: Generate `data/processed/power_analysis_report.json` containing the calculated minimum N and the result of the check. **Verification**: Script must exit with `SystemExit(1)` if columns are missing or N < 128. No synthetic fallback. **Dependency**: T009.
- [ ] T008c [Foundational] [US1] Implement `code/01_data_ingestion.py` (Part 2.5): **Pre-filter** molecules with extremely large molecular weights (> 1000 Da) to prevent RAM overflow during scaffold splitting and ensure data integrity. **Deliverable**: Generate `data/processed/filtered_esol.csv` (subset of ESOL) and `data/logs/large_molecule_exclusions.log`. **Logic**: Calculate MW for each molecule; exclude if > 1000 Da. **Verification**:
 1. **Active Assertion**: Script MUST assert that the output file `filtered_esol.csv` contains NO molecules with MW > 1000 Da. If any are found, exit with `SystemExit(1)` and message "Data Filter Integrity Failed: Large molecules present in output."
 2. **Logging**: Verify the script logs the count of excluded molecules and the total input count to `data/logs/large_molecule_exclusions.log`.
 3. **Input Validation**: If the input file from T008a is empty or missing, exit with `SystemExit(1)`.
 **Dependency**: T008a.
- [ ] T008b [Foundational] [US1] Implement `code/01_data_ingestion.py` (Part 3): Enforce min scaffolds check (>=100 unique scaffolds per Plan.md 'Scaffold Validation'), implement a custom scaffold splitter using `rdkit.Chem.Scaffolds.MurckoScaffold.GetScaffoldForMol` to group molecules, perform a 5-fold split with `seed=42`, and save split indices to `data/processed/splits.json`. **Algorithm**: Count unique Bemis-Murcko frameworks on the **pre-filtered** dataset. **Deliverable**: Generate `data/processed/scaffold_counts.json` (fail-fast artifact) and `data/processed/splits.json`. **Dependency**: T008c. **Verification**:
 1. **Power Check**: Verify script exits with `SystemExit(1)` if N < 128 (Power Insufficient).
 2. **Scaffold Check**: Verify script exits with `SystemExit(1)` if unique scaffolds < 100 (Message: "Scaffold Insufficient: <count> < 100").
 3. **Split Output**: Verify `data/processed/splits.json` exists, is valid JSON, and contains 5-fold indices.
 4. **Split Validity**: Verify that if the count is met, the split results in a consistent number of scaffolds per fold.
 5. **Data Integrity Pre-flight**: **CRITICAL**: Before splitting, the script MUST re-calculate MW for every molecule in the input file (`data/processed/filtered_esol.csv`) and assert that NO molecule exceeds 1000 Da. If any large molecule is detected, exit with `SystemExit(1)` and message "Data Integrity Violation: Large molecules detected in input to splitter. Upstream filter failed." This ensures the split logic does not trust upstream blindly.
 6. **Error Handling**: If validation fails, log specific reason ("Power Insufficient", "Scaffold Insufficient", or "Data Integrity Violation") before exiting.
- [X] T015b [Foundational] [US1] Implement sparse matrix logic with memory threshold checks in `code/utils/persistence_utils.py` to handle **intra-molecule graph memory spikes** (Edge Case: Large Graphs). **Threshold**: If estimated RAM usage for a single molecule's persistence calculation > 6.0GB, use `scipy.sparse.csr_matrix` format. **Verification**: Verify script handles large individual graphs without crashing and uses sparse structures where applicable. **Test Case**: Use a synthetic SMILES string of a large number of repeating benzene rings to trigger the sparse logic. **Note**: This task addresses memory limits within a single molecule's graph construction, distinct from T008c's dataset-level exclusion. **Dependency**: T006.
- [X] T005 [P] [Foundational] Implement `code/utils/graph_builder.py` for RDKit molecular graph construction. **Deliverable**: Implement function `build_graph(smiles: str) -> Optional[Graph]` and `validate_graph(graph: Graph) -> bool`. **Validity Checks**: `valence` (no atoms with incorrect electron count), `aromaticity` (ring detection), and `bond_order` (single/double/triple). **Verification**: Unit tests confirm invalid SMILES return `None` and valid SMILES return a graph with correct connectivity.
- [X] T006 [P] [Foundational] Implement `code/utils/persistence_utils.py` for shortest-path filtration and empty diagram handling. **Deliverable**: Implement `compute_filtration(graph: Graph) -> Diagram` using Dijkstra's algorithm for shortest-path distances. Implement `vectorize(diagram: Diagram, resolution: int) -> np.ndarray`. **Empty Handling**: If diagram is empty, return `np.zeros(resolution * resolution)`. **Verification**: Verify `vectorize` returns a zero-vector for linear chain molecules and valid vectors for ring structures.
- [X] T021 [P] [Foundational] Add runtime GPU check (FR-008) using generic CUDA detection AND static library check. **Checks**: `os.environ.get('CUDA_VISIBLE_DEVICES')`, `torch.cuda.is_available()`, and `gudhi` GPU flags. **Static Check**: Verify no GPU-specific libraries are imported in `code/` and `tests/` by running `grep -r 'cuda'` and `grep -r 'torch'`. **Action**: Raise `SystemExit(1)` if any GPU acceleration is detected; do not rely on `torch`. **Verification**: Run script in a simulated GPU environment and verify it exits with `SystemExit(1)` and message "GPU Detected: FR-008 Violation". **Dependency**: T001a, T002.
- [X] T029 [P] [Foundational] Implement `code/07_resource_monitor.py` as a pipeline wrapper to enforce "fail-fast" on resource limits (SC-004). **Function**: Wrap the main pipeline execution; monitor RAM/CPU usage in real-time; if RAM > 6.3GB or CPU time > 5.4h, raise `SystemExit(1)` with a descriptive error. **Verification**: Simulate resource exhaustion (e.g., via sleep or memory allocation) and verify the script raises `SystemExit(1)` before completion.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Compute TDA Features for Molecular Dataset (Priority: P1) 🎯 MVP

**Goal**: Ingest ESOL dataset, compute persistence diagrams via shortest-path filtration, and vectorize to persistence images with a fixed grid resolution.

**Independent Test**: Run `02_tda_computation.py` on a fixed subset; verify output CSV has non-null topological descriptors for every valid molecule AND verify that the 10x10 baseline is generated.

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/02_tda_computation.py`: Graph construction and shortest-path filtration (FR-001). **Deliverable**: Pipeline to convert SMILES to graphs and compute persistence diagrams. **Dependency**: T005, T015b.
- [ ] T013a [US1] Implement `code/02_tda_computation.py`: Vectorization to persistence images for the **primary baseline** (fixed 10x10 grid resolution as per FR-002). **Parameters**: Kernel bandwidth (sigma=0.1). **Deliverable**: Generate `data/processed/persistence_images_10x10.csv` (Primary Baseline). **Schema**: `molecule_id` (string) + 100 float columns (`p_img_0` to `p_img_99`). **Verification**: Run contract test to ensure file exists, schema matches, and no NaN values in topological columns. Include zero-vector fallback for empty diagrams. **Primary Check**: Verify that this file is the default input for T019 (Model Training). **Dependency**: T012.
- [ ] T013b [US1] Implement `code/02_tda_computation.py`: Vectorization to persistence images for **sensitivity sweep** (variable resolutions: 20x20, 30x30). (FR-006). **Parameters**: Kernel bandwidth (sigma=0.1). **Deliverable**: Generate `data/processed/persistence_images_20x20.csv` and `persistence_images_30x30.csv`. **Verification**: Run contract test to ensure files exist and schema matches. **Dependency**: T012.
- [ ] T014 [P] [US1] Implement `code/03_feature_engineering.py` (Part 1): Compute Traditional Descriptors. **Deliverable**: Generate `data/processed/traditional_descriptors.csv` using RDKit (MW, fingerprints, atom counts, etc.). **Verification**: Verify output contains standard RDKit descriptors and matches molecule IDs from T008a. **Dependency**: T008a, T005.
- [ ] T015a [US1] Implement error handling for invalid SMILES in `code/02_tda_computation.py`: Log errors to `data/logs/invalid_smiles.log` AND write exclusions to `data/excluded_smiles_manifest.csv`. **Schema**: `molecule_id`, `error_message`, `original_smiles`. **Dependency**: T004, T012. **Constitution VI Compliance**: The script MUST log the exclusion. **Verification**: Verify log file is created and manifest exists with correct schema.
- [ ] T016 [US1] Implement `code/02_tda_computation.py`: Generate `data/processed/tda_vectors_10x10.csv` (TDA vectors only). **Input**: `data/processed/splits.json` (for molecule IDs), `persistence_images_10x10.csv`. **Output**: `data/processed/tda_vectors_10x10.csv` containing `molecule_id` and `p_img_0`...`p_img_99`. **Dependency**: T013a. **Verification**: Run contract test to verify schema compliance and confirm non-null values for every valid molecule.
- [ ] T017 [US1] Implement `code/03_feature_engineering.py`: Merge traditional descriptors and TDA features. **Input**: `data/processed/traditional_descriptors.csv` (from T014), `data/processed/tda_vectors_10x10.csv`. **Output**: `data/processed/combined_features.csv`. **Merge Key**: `molecule_id`. **Verification**: Verify output contains all columns and rows match input. **Dependency**: T016, T014.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (features computed and cached)

---

## Phase 4: User Story 2 - Train and Compare Predictive Models (Priority: P2)

**Goal**: Train Linear Regression (L2) and Random Forest on Traditional, Topological, and Combined feature sets using scaffold splits.

**Independent Test**: Execute `04_model_training.py`; verify R²/RMSE reported for all configurations and folds.

### Implementation for User Story 2

- [ ] T018 [US2] Implement `code/04_model_training.py`: Load split indices from T008b (`data/processed/splits.json`) and apply to training data. **Dependency**: T008b, T021 (Safety Gate). **Verification**: Ensure `data/processed/splits.json` is loaded successfully and splits are applied correctly.
- [ ] T019 [US2] Implement `code/04_model_training.py`: Train Linear Regression (alpha=1.0) and Random Forest (100 trees, max_depth=10) on 3 feature sets. **Input**: `data/processed/combined_features.csv` (and subsets), `data/processed/tda_vectors_10x10.csv` (Primary Baseline). **Target**: `logP`. **Output**: `data/models/` (pickle files for each model). **Verification**: Verify models are saved and loadable. **Dependency**: T013a, T017.
- [ ] T020 [US2] Implement `code/04_model_training.py`: Calculate R² and RMSE per fold; aggregate metrics. **Aggregation**: Mean and Standard Deviation. **Feature Importance**: Extract `coefficients_` for LR and `feature_importances_` for RF. **Deliverable**: Generate `reports/metrics/model_performance.json`. **Schema**: `{ "traditional": { "r2_per_fold": [], "rmse_per_fold": [], "r2_mean": float, "rmse_mean": float, "feature_importance": [] }, "topological": {... }, "combined": {... } }`. **Verification**: Run `pytest tests/contract/test_metrics_schema.py`. **Dependency**: T019.
- [X] T022 [US2] **Removed**: Merged into T020 to avoid schema duplication.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Validate Methodological Rigor and Sensitivity (Priority: P3)

**Goal**: Apply Holm-Bonferroni correction, run VIF diagnostics, and quantify feature redundancy.

**Independent Test**: Inspect logs/reports to confirm corrected p-values, VIF flags, and MI scores are present.

### Implementation for User Story 3

- [ ] T023 [US3] Implement `code/05_sensitivity_analysis.py`: **Execute** the sensitivity analysis by consuming the persistence images from T013b (20x20, 30x30) and the model metrics from T020. Calculate R² variance across resolutions using **Coefficient of Variation (CV)** and generate the final stability report. **Dependency**: T013b, T020. **Deliverable**: Generate `reports/metrics/sensitivity_analysis.json` containing `resolutions`, `r2_scores`, and `r2_variance` (CV). **Verification**: Ensure file contains the required keys and that the analysis is based on real model performance, not synthetic data.
- [ ] T025 [US3] Implement `code/06_diagnostics.py`: Apply **Holm-Bonferroni correction** to p-values generated in T020. **Note**: This task implements 'Holm-Bonferroni' as mandated by the Plan.md 'Critical Methodological Update' (replacing the Spec's 'Bonferroni' to address correlated tests). **Algorithm**: Sort p-values, multiply by N/i, compare to alpha, ensure monotonicity. **Reporting**: The final `diagnostics.json` MUST explicitly document the method used ("Holm-Bonferroni") and the justification for deviating from Spec FR-005 (citing Plan.md). **Dependency**: T020. **Verification**: Verify the correct **Holm-Bonferroni** algorithm is used and the N=1 case is handled gracefully. Log the deviation from Spec FR-005 citing Plan.md in the report.
- [ ] T026 [US3] Implement `code/06_diagnostics.py`: Calculate VIF; flag predictors > 5 (FR-007). **Input**: `data/processed/combined_features.csv`. **Method**: `statsmodels.stats.outliers_influence.variance_inflation_factor`. **Handling**: Exclude intercept column. **Formula**: 1/(1-R²). **Output**: `reports/metrics/diagnostics.json`. **Verification**: Ensure VIF values are calculated and predictors > 5 are flagged.
- [ ] T027 [US3] Implement `code/06_diagnostics.py`: Calculate Mutual Information between traditional and topological feature sets (FR-009). **Input**: `data/processed/traditional_descriptors.csv`, `data/processed/tda_vectors_10x10.csv`. **Method**: `sklearn.feature_selection.mutual_info_regression`. **Output**: `reports/metrics/diagnostics.json` (float value). **Verification**: Ensure the calculation is performed and reported without arbitrary threshold logic.
- [ ] T028 [US3] Generate `reports/metrics/diagnostics.json` with VIF flags, corrected p-values, MI scores, and **Methodological Summary**. **Schema**: `{ "vif": { "feature": value }, "corrected_pvalues": { "test": value }, "mutual_information": value, "methodology": { "correction_method": "Holm-Bonferroni", "controlled_alpha": a standard significance level, "justification": "Plan.md update for correlated tests" } }`. **Dependency**: T025, T026, T027. **Task Detail**: **Verification**: Ensure the output includes the `controlled_alpha` and `correction_method` fields, explicitly stating that FWER is controlled at a conventional significance level.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030a [P] Documentation updates: Update `quickstart.md` with TDA methodology. **Deliverable**: Add a section "TDA Methodology" referencing FR-001 and FR-002. **Verification**: Verify `quickstart.md` contains the section and correct references.
- [ ] T030b [P] Documentation updates: Update `docs/` with reproducibility steps. **Deliverable**: Add a section "Reproducibility" referencing Constitution Principle I and the fixed seed (42). **Verification**: Verify `docs/` contains the section and correct references.
- [ ] T031 [P] Code cleanup: Refactor `code/utils/graph_builder.py` to reduce cyclomatic complexity to < 10. **Target**: Function `build_graph`. **Tool**: `ruff check --select C901`. **Verification**: Run `ruff` and confirm max complexity < 10.
- [ ] T032 [Polish] Performance optimization: Profile `code/02_tda_computation.py` for memory usage and ensure it stays within SC-004 limits (< 6.3GB RAM). **Dataset**: Full ESOL dataset (not subset). **Dependency**: Requires T012/T013 completion. **Tool**: `memory_profiler`. **Metrics**: `peak_memory`. **Output**: `reports/metrics/memory_profile.json`.
- [ ] T033 [P] Additional unit tests: Implement `tests/unit/` for graph builder and persistence utils. **Functions**: `test_graph_build`, `test_empty_diagram`. **Inputs**: `valid_smiles`, `disconnected_smiles`. **Assertions**: `assert graph is not None`, `assert len(graph.nodes) > 0`. **Verification**: Run `pytest tests/unit/`.
- [ ] T034 [P] Run quickstart.md validation to ensure full pipeline reproducibility. **Method**: `bash code/quickstart.sh`. **Success Criteria**: `exit code 0`. **Output**: `reports/logs/quickstart.log`. **Verification**: Verify log contains success message.
- [ ] T041 [P] [Spec Amendment] Formally amend Spec.md FR-005 to "Holm-Bonferroni" and update Plan.md to reflect this change. **Deliverable**: Update `specs/001-predict-molecular-properties-tda/spec.md` and `projects/PROJ-444-predicting-molecular-properties-from-top/specs/001-predicting-molecular-properties-from-top/plan.md`. **Verification**: Verify text matches "Holm-Bonferroni" and cites the rationale for correlated tests. **Dependency**: T025.

---

## Phase O: Review Resolution & Final Verification

**Purpose**: Address specific unresolved claims and ensure strict adherence to the "Real Data Only" constitution.

- [ ] T035 [P] [US1/US2] **Resolve Data Ingestion Validation**: Update `code/01_data_ingestion.py` to explicitly handle missing data by adding a runtime assertion that halts execution if the MoleculeNet ESOL dataset cannot be fetched or validated against the `dataset.schema.yaml` columns (`smiles`, `logP`). **Specifics**: Raise `SystemExit(1)` with message "Data Gap: Missing required columns or fetch failed. No synthetic fallback." Log validation errors to `data/logs/ingestion_errors.log`. **Owner**: This task is the sole owner of 'Data Gap' handling. **Verification**: Run script with invalid URL and assert SystemExit(1). **Dependency**: T008a.
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
- **User Story 2 (P2)**: Depends on US1 completion (requires `tda_vectors_10x10.csv` and `traditional_descriptors.csv`)
- **User Story 3 (P3)**: Depends on US2 completion (requires model metrics for statistical testing)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2) **EXCEPT** T007, T008a, T008c, T008b which have sequential dependencies.
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