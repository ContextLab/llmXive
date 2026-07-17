# Tasks: Predicting Molecular Surface Area from Graph Convolutional Networks

**Input**: Design documents from `/specs/001-predicting-molecular-surface-area/`
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

- [ ] T001 Create project structure: `mkdir -p code/data code/models code/eval code/utils tests/contract tests/unit tests/integration data/raw data/processed data/splits results/reports results/plots`
- [X] T002 Create `code/requirements.txt` containing pinned versions of: `rdkit`, `pandas`, `scikit-learn`, `pyyaml`, `numpy`, `pytest`, `ruff`, `black`. Install torch and torch-geometric using: `pip install torch --index-url https://download.pytorch.org/whl/cpu` and `pip install torch-geometric`. Do not use `torch (cpu)` as a package name.
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools by generating `pyproject.toml` and `.ruff.toml` configuration files with project-specific rules.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup directory structure: `code/`, `data/raw/`, `data/processed/`, `data/splits/`, `results/`
- [X] T005 [P] Implement `code/__init__.py` and environment configuration loader
- [X] T006a [P] Setup logging infrastructure in `code/utils/logging.py`
- [X] T006b [P] Implement `conformer_config.json` generator in `code/utils/conformer_config.py`
- [ ] T007 Create base data models (Molecule, Graph, EvaluationResult) in `code/models/`
- [X] T008 Implement seed pinning utility for reproducibility in `code/utils/seed.py`
- [X] T009 Setup dataset checksumming utility in `code/utils/checksum.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Ingest SMILES, convert to 2D graphs, generate 3D SASA labels, and split data.

**Independent Test**: A researcher can run the data pipeline script and verify that a CSV/Parquet file is produced containing SMILES, node/edge feature matrices, and a numeric surface area column, with no missing values in the target column for the training set.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T010 [P] [US1] Contract test for data schema in `tests/contract/test_data_schema.py` validating against the **static schema.yaml defined in spec.md** to ensure input format compliance before processing.
- [X] T011 [P] [US1] Integration test for SMILES ingestion pipeline in `tests/integration/test_ingest.py` (must run after T012-T014)

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement SMILES ingestion from ZINC15 (fetch from `https://zinc15.docking.org/subsets/filtered/drug_like/`) and validate syntax in `code/data/ingest.py`. **Do not use placeholders**; use the exact URL.
- [X] T013 [US1] Implement 2D graph feature extraction (atom type, hybridization, charge) using RDKit in `code/data/preprocess.py`
- [X] T014 [US1] Implement 3D conformer generation (lowest energy) and SASA calculation in `code/data/preprocess.py` with chunked processing; **halt with critical error if >10% of conformer generation fails**. Also, log the RDKit parameters used for conformer generation into a file named `conformer_config.json`.
- [X] T014b [US1] Validate that the RDKit parameters logged in `conformer_config.json` match the parameters actually used during conformer generation (T014).
- [ ] T015 [US1] Implement data splitting logic (stratified by Molecular Weight, KS test > 0.05) generating `data/splits/train_indices.csv` and `data/splits/test_indices.csv`
- [ ] T016 [US1] Add validation and error handling for invalid SMILES and failed conformer generation; **log failure count and halt if >10% failure rate**
- [ ] T017 [US1] Add logging for excluded molecules and dataset statistics

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - GCN Model Training and Baseline Comparison (Priority: P2)

**Goal**: Train a lightweight CPU-tractable GCN and a Geometry-Based Baseline, then compare performance.

**Independent Test**: The training script runs to completion within the CI limit, producing two model artifacts and a results report showing MAE, RMSE, R² for both, along with a statistical significance test.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output.py` validating against `model_schema.yaml`
- [X] T019 [P] [US2] Integration test for training loop and early stopping in `tests/integration/test_training.py`

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement lightweight GCN model definition (PyTorch Geometric, CPU-only) in `code/models/gcn.py` containing class `GCNModel` with `forward(input_tensor)` method
- [X] T021 [US2] Implement **Geometry-Based Baseline** using RDKit's 3D conformer generation in `code/models/baseline_3d.py`. The model directly uses the generated 3D geometry for SASA calculation, providing a comparison point to the GCN trained on 2D features only.
- [X] T022 [US2] Implement training loop with early stopping (patience=5, max 50 epochs) in `code/models/train.py`
- [X] T023 [US2] Implement evaluation metrics (MAE, RMSE, R²) in `code/eval/metrics.py`
- [X] T024 [US2] Implement paired t-test and Cohen's d calculation for model comparison in `code/eval/metrics.py`
- [ ] T025 [US2] Integrate training and evaluation to produce final comparison report generating `results/reports/model_comparison.json` containing MAE, RMSE, R², p-value, and Cohen's d

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis and Threshold Justification (Priority: P3)

**Goal**: Perform sensitivity analysis on MAE thresholds and apply multiple-comparison corrections.

**Independent Test**: The analysis script re-runs the evaluation with modified thresholds and generates a report showing how success rates change, including corrected p-values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Contract test for sensitivity report schema in `tests/contract/test_sensitivity_report.py` validating against `sensitivity_schema.yaml`
- [X] T027 [P] [US3] Unit test for Bonferroni/FDR correction logic in `tests/unit/test_statistics.py`

### Implementation for User Story 3

- [ ] T027a [US3] Calculate the mean SASA of the dataset and log it. If the mean SASA is significantly large (e.g., >> 0.1 Å²), log a warning indicating that absolute thresholds may yield unrealistic success rates, and document this scale mismatch in the final report as justification for the threshold choice
- [ ] T028 [US3] Implement sensitivity analysis script sweeping **relative** MAE thresholds {1%, 5%, 10%} of mean SASA in `code/eval/sensitivity.py`
- [ ] T029 [US3] Implement multiple-comparison correction (Bonferroni or FDR) for threshold sweep results in `code/eval/sensitivity.py`
- [X] T030 [US3] Generate sensitivity report with threshold justification and adjusted p-values writing `results/reports/sensitivity_analysis.md`. This task depends on the output of T027a, which computes the scale analysis used for justification.
- [ ] T031 [US3] Create visualization plots for sensitivity curves in `results/plots/`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Documentation updates in `docs/` and `README.md`
- [ ] T033 Code cleanup and refactoring of data processing scripts
- [ ] T034 Refactor `code/data/preprocess.py` to implement chunked processing and verify runtime < 6h on a sample of A large ensemble of molecules. **Validation Method**: Use **linear scaling** (time per molecule * total molecules) to extrapolate the full dataset runtime and confirm it meets the 6-hour constraint.
- [ ] T035 [P] Additional unit tests for edge cases (invalid SMILES, memory overflow) in `tests/unit/`
- [ ] T036 Run `quickstart.md` validation

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model outputs

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
- Different user stories can be worked on in parallel by different team members