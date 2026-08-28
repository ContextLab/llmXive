# Tasks: Predicting Molecular Permeability Coefficients Using Graph Neural Networks and Publicly Available Datasets

**Input**: Design documents from `/specs/001-molecular-permeability-gnn/`
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

 Tasks MUST be organized by user story so each story can:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 [P] Create `setup_dirs.sh` script to programmatically generate the project directory structure: `projects/PROJ-422-predicting-molecular-permeability-coeffi/code/data`, `projects/PROJ-422-predicting-molecular-permeability-coeffi/code/models`, `projects/PROJ-422-predicting-molecular-permeability-coeffi/code/analysis`, `projects/PROJ-422-predicting-molecular-permeability-coeffi/data/raw`, `projects/PROJ-422-predicting-molecular-permeability-coeffi/data/processed`, `projects/PROJ-422-predicting-molecular-permeability-coeffi/data/interim`, `projects/PROJ-422-predicting-molecular-permeability-coeffi/results`, `projects/PROJ-422-predicting-molecular-permeability-coeffi/tests/unit`, `projects/PROJ-422-predicting-molecular-permeability-coeffi/tests/integration`. The script must be executable and verifiable via `bash setup_dirs.sh && ls`.
- [X] T002 Initialize Python 3.11 project with pinned dependencies in `requirements.txt` (rdkit, torch, torch-geometric, scikit-learn, shap, gnnexplainer, pandas, datasets, statsmodels, psutil)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools
- [ ] T003a [P] Create `generate_config.py` script to programmatically generate `config.yaml` with configurable parameters: `bias_threshold` (default 0.85), `retention_threshold` (default 0.95), `stratification_diff_threshold` (default 0.05), `proxy_target_columns` (default ['logP', 'calculated_logP']). The script must be executable and verifiable via `python generate_config.py && cat config.yaml`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/utils/logging.py` for structured JSON logging and result artifact generation
- [X] T005 [P] Create `code/data/download.py` skeleton: Define class `DataLoader` with method `fetch_dataset(source: str)` and `verify_checksum(file_path: str)`. **Contract**: Define return types and exception signatures for T013 implementation.
- [X] T006 [P] Create `code/data/preprocess.py` skeleton: Define class `MoleculeProcessor` with method `parse_smiles(smiles: str)` and `calculate_descriptors(mol)`. **Contract**: Define return types and exception signatures for T014 implementation.
- [X] T007 [P] Create `code/data/split.py` skeleton: Define function `stratified_split(df, stratify_col)` and `random_split(df)`. **Contract**: Define return types and exception signatures for T017 implementation.
- [X] T008 [P] Create `code/models/gnn.py` skeleton: Define class `MPNN` (PyTorch Geometric `nn.Module`) with `forward` method. **Contract**: Define input/output tensor shapes for T020 implementation.
- [X] T009 [P] Create `code/models/rf.py` skeleton: Define function `train_random_forest(X, y)` and `predict(model, X)`. **Contract**: Define input/output types for T021 implementation.
- [X] T010 [P] Create `code/analysis/evaluate.py` skeleton: Define functions `calculate_metrics(y_true, y_pred)` and `paired_ttest(errors_a, errors_b)`. **Contract**: Define return types for T024/T025 implementation.
- [X] T011 [P] Create `code/analysis/explain.py` skeleton: Define functions `explain_rf(model, X)` and `explain_gnn(model, graph)`. **Contract**: Define return types for T029/T030 implementation.
- [X] T012 [P] Setup `tests/unit/test_preprocess.py` and `tests/integration/test_pipeline.py` scaffolding

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest public datasets, parse SMILES to graphs/descriptors, handle invalid data, and create stratified splits (or fallback).

**Independent Test**: The pipeline runs end-to-end on a sample, producing `data/processed/train.csv`, `data/processed/test.csv`, and a log confirming the split strategy (stratified or random with warning) and data retention.

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/data/download.py`:
 1. Fetch the specific verified dataset from a real, public source (e.g., NIST Permeability Database or a verified Hugging Face dataset containing 'SMILES' and 'permeability_coefficient' columns).
 2. Log the dataset source and target validation.
 3. Raise `RuntimeError` ONLY if no valid data source is found (no synthetic fallback).
- [X] T013b [US1] Implement `code/data/download.py` target validation:
 1. **Prerequisite**: Depends on T013 completion.
 2. Check if the target column contains experimental permeability coefficients.
 3. **Proxy Mode Logic**: If the experimental column is missing, search for a column named 'logP' or 'calculated_logP'. If found, **switch to Proxy Mode**, set the target variable to this column, and log a clear "Proxy Mode Activated" warning. If neither is found, raise `RuntimeError`.
 4. **Constraint**: Do NOT halt the pipeline if experimental data is missing; the Plan explicitly requires this fallback to a feasibility study using calculated descriptors.
 5. Log the final target variable name and mode (Experimental vs Proxy).
- [X] T014 [US1] Implement `code/data/preprocess.py`:
 1. Parse SMILES using RDKit, compute standard descriptors (MW, logP, TPSA, etc.), and construct molecular graphs.
 2. **Output Requirement**: Generate a distinct feature set of "flattened graph statistics" (e.g., mean node degree, connectivity, substructure counts) as a separate column group or file (`data/processed/graph_features.csv`) for use in the Ablation Study.
 3. Handle missing values via median imputation or row exclusion with logging.
- [X] T015 [US1] Implement invalid SMILES handling in `code/data/preprocess.py`:
 1. Log errors and exclude invalid rows.
 2. **Constraint**: Enforce FR-011 strictly: If valid molecule retention < 95% AND dataset size N >= 50, trigger `SystemExit(1)` with a detailed error log.
 3. **Exception**: If dataset size N < 50, log a warning about small sample size and proceed with the available data to allow the feasibility study to run.
- [X] T016 [US1] Implement FR-013 (Bias Check) in `code/data/preprocess.py`:
 1. Calculate correlation between input descriptors and the target variable.
 2. Load the threshold parameter from `config.yaml` (default 0.85).
 3. **Conditional Logic**: If correlation exceeds the threshold, flag results as `bias_warning: "potentially confounded"` and log a warning. The pipeline must continue but the final report must highlight this flag.
- [ ] T017 [US1] Implement `code/data/split.py`:
 1. **Prerequisite**: Depends on [T013b] (Target Validation/Proxy Mode).
 2. Check if the 'polymer_type' column exists in the dataset.
 3. **Stratified Logic**: If 'polymer_type' exists, perform a stratified split ensuring distribution difference < 5% for each class.
 4. **Fallback Logic**: If 'polymer_type' is missing (common in Proxy Mode datasets), perform a random split and log a warning: "Stratification by polymer type skipped; fallback to random split due to missing metadata."
 5. Save splits to `data/processed/train.csv` and `data/processed/test.csv`.
- [X] T018 [US1] Write unit tests in `tests/unit/test_preprocess.py` for SMILES parsing, descriptor calculation, invalid handling, and graph feature flattening.
- [X] T019 [US1] Write integration test in `tests/integration/test_pipeline.py` to verify end-to-end data flow, target validation, and file outputs.

**Checkpoint**: Data pipeline functional; valid splits and features ready for modeling.

---

## Phase 4: User Story 2 - Comparative Model Training and Evaluation (Priority: P2)

**Goal**: Train CPU-optimized GNN (MPNN) and Random Forest baselines, evaluate metrics, and perform statistical significance testing.

**Independent Test**: Training completes within 6h/7GB RAM, outputs metrics to `results/metrics.json`, and reports a p-value for the performance gap.

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement `code/models/gnn.py`: Define MPNN architecture (multiple layers) compatible with CPU execution; include early stopping logic based on validation loss.
- [X] T021 [P] [US2] Implement `code/models/rf.py`: Configure Random Forest regressor for baseline comparison.
- [ ] T022 [US2] Implement `code/analysis/train.py`:
 1. Implement the full training loop for GNN and RF on `data/processed/train.csv`.
 2. **Constraint**: Enforce CPU-only execution (no CUDA device assignment) to adhere to the free-tier runner constraints.
 3. Implement early stopping logic based on validation loss with patience parameter.
 4. Save model checkpoints to `data/interim/gnn_checkpoint.pt` and `data/interim/rf_checkpoint.pkl` upon completion or early stopping.
 5. **Logging**: Log training duration and peak memory usage (using `psutil`) to `results/training_log.json` to verify SC-004 constraints.
- [ ] T023 [US2] Implement FR-012 (Ablation Study): Train a Random Forest baseline using **ONLY** the "flattened graph statistics" feature set (produced in T014 at `data/processed/graph_features.csv`).
 1. **Prerequisite**: Depends on [T022] (Training Infrastructure) and [T014] (Graph Features Generation).
 2. **Constraint**: Strictly exclude all standard molecular descriptors (MW, logP, TPSA) in the input matrix to isolate the incremental value of topology.
 3. **Scientific Framing**: Acknowledge that in Proxy Mode (logP target), this compares 'topology-only' vs 'descriptors-only' against a descriptor target. Frame the result as a feasibility check of the GNN architecture's ability to learn from topology, rather than a claim of superiority for permeability prediction.
- [ ] T024 [US2] Implement `code/analysis/evaluate.py`:
 1. Calculate RMSE, MAE, R² for all models (GNN, RF-Baseline, RF-Ablation) on `data/processed/test.csv`.
 2. Generate a structured JSON artifact `results/metrics.json` containing all metrics per model.
 3. Ensure the output schema includes fields for `model_name`, `rmse`, `mae`, `r2`, `training_time`, and `peak_memory_gb`.
- [ ] T025 [US2] Implement FR-007: Paired t-test on prediction errors between GNN and RF-Baseline.
 1. **Prerequisite**: Depends on [T024] (Evaluation).
 2. **Requirement**: Explicitly calculate and log Cohen's d (effect size) and 95% Confidence Intervals for the mean difference to `results/metrics.json`.
 3. **Success Criteria Alignment**: This task implements the measurable outcomes defined in SC-002 (Statistical Significance), SC-002b (Effect Size), and SC-002c (Confidence Intervals).
 4. **Constraint**: Use `scipy.stats` for t-test and manual calculation for Cohen's d to ensure reproducibility without heavy dependencies.
- [X] T026 [US2] Implement post-hoc power analysis in `code/analysis/evaluate.py` using observed effect size and sample size.
- [ ] T027 [P] [US2] Write unit tests for `code/models/gnn.py` and `code/models/rf.py` (forward pass, shape checks).
- [ ] T028 [P] [US2] Write integration test in `tests/integration/test_pipeline.py` for full training and evaluation flow.

**Checkpoint**: Models trained, metrics logged, and statistical significance determined.

---

## Phase 5: User Story 3 - Feature Attribution and Interpretability Analysis (Priority: P3)

**Goal**: Apply GNNExplainer to GNN and SHAP to RF to identify and rank predictive features/substructures.

**Independent Test**: Analysis generates ranked feature lists and visualizations highlighting topological features unique to GNN.

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement `code/analysis/explain.py`:
 1. Apply SHAP to the Random Forest model.
 2. Generate a ranked list of standard descriptors by absolute mean SHAP value.
 3. Save the ranked list to `results/feature_importance_rf.json`.
- [ ] T030 [US3] Implement `code/analysis/explain.py`:
 1. Apply GNNExplainer to the GNN model.
 2. Identify top influential node-level substructures (e.g., aromatic rings, functional groups) across the test set.
 3. Save the identified substructures and their importance scores to `results/feature_importance_gnn.json`.
- [ ] T031 [US3] Implement FR-009: Generate comparative report mapping GNN substructures to RF descriptors.
 1. **Prerequisites**: Requires model outputs from US2 (T022-T024) to map features to performance context, and feature importance from T029/T030.
 2. **Mapping Logic**: Compare the rank of SHAP features vs. the rank of GNNExplainer substructures. Identify substructures with high GNNExplainer scores that correspond to low-ranked SHAP descriptors.
 3. **Output Format**: Generate a Markdown report `results/comparative_report.md`.
 4. **Scientific Framing**: In Proxy Mode, acknowledge that high correlation between logP (target) and standard descriptors may dominate SHAP rankings. The report should highlight substructures identified by GNNExplainer that are *not* captured by standard descriptors, framing this as "Topological features learned by GNN beyond standard descriptors" rather than "Incremental value for permeability".
- [ ] T032 [US3] Generate visualizations (heatmaps/bar charts) for feature importance in `results/figures/`.
 1. Create a bar chart comparing top 10 SHAP features vs. top 10 GNNExplainer substructures.
 2. Save figures as PNG files with high resolution..
- [ ] T033 [P] [US3] Write unit tests for `code/analysis/explain.py` (mock models for explainability checks).

**Checkpoint**: Interpretability analysis complete; comparative report generated.

---

## Phase 6: Validation & Reporting (Priority: P3)

**Goal**: Ensure results align with Success Criteria and report findings.

- [ ] T034 [P] Documentation updates: Update `README.md` with pipeline usage and `results.md` with final findings.
- [ ] T035 Code cleanup and refactoring for PEP8 compliance.
- [ ] T036 [P] Run full pipeline end-to-end on CI to verify reproducibility and artifact generation.
- [ ] T037 Verify `results/metrics.json` contains all required fields (RMSE, MAE, R², p-value, Cohen's d, CI, power, bias_warning).
- [ ] T038 [US3] Verify Success Criteria Alignment: Ensure the final report and `results/metrics.json` explicitly state the measured outcomes against the defined Success Criteria (SC-001 through SC-002c).

---

## Success Criteria (Updated)

- **SC-001**: The reduction in RMSE of the GNN model compared to the Random Forest baseline (trained on graph-derived features) is measured against the null hypothesis of no difference (See FR-007).
- **SC-002**: The statistical significance of the performance gap is measured against a conventional significance threshold using a paired t-test (p-value).
- **SC-002b**: The magnitude of the performance gap is measured by calculating Cohen's d (effect size) for the difference in prediction errors.
- **SC-002c**: The precision of the performance gap estimate is measured by calculating the Confidence Interval for the mean difference.
- **SC-003**: The interpretability of the GNN is measured by the ability to rank specific topological substructures by GNNExplainer, compared to the ranked standard descriptors from SHAP.
- **SC-004**: The computational feasibility is measured by the total training time (must be ≤ 6 hours) and peak memory usage (must be ≤ 7 GB) on a CPU-only runner.
- **SC-005**: The data integrity is measured by the percentage of valid molecules retained after preprocessing.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires US1 data outputs
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires US2 model outputs

### Explicit Task Dependencies

- **T013b**: Depends on **T013** (Data Fetch) to ensure target configuration is set before preprocessing.
- **T017**: Depends on **T013b** (Target Validation) to ensure split logic adapts to Proxy Mode or missing metadata.
- **T023 (Ablation Study)**: Depends on **T022** (Training Infrastructure) and **T014** (Graph Features Generation). T023 cannot execute until training infrastructure is ready and `data/processed/graph_features.csv` is present.
- **T031 (Comparative Report)**: Depends on **T029**, **T030**, and **T024** (Model Evaluation).
- **T022**: Depends on **T017** (Data Split) to ensure training/test sets are available.
- **T024**: Depends on **T022** (Training) to ensure models are trained before evaluation.
- **T025**: Depends on **T024** (Evaluation) to ensure prediction errors are available for statistical testing.

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
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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