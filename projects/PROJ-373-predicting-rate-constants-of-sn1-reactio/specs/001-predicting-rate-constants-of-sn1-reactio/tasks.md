# Tasks: Predicting Rate Constants of SN1 Reactions from Molecular Structure

**Input**: Design documents from `/specs/001-predict-sn1-rate-constants/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
- Paths shown below assume single project - adjusted based on plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan (`code/`, `data/`, `tests/`, `specs/`)
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (rdkit, torch, scikit-learn, shap, pandas, pyyaml, datasets)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools
- [X] T007A [P] Create `pytest.ini` configuration file in project root to enable test discovery and coverage reporting. **Deliverable**: `pytest.ini` with `[pytest]` section defining test paths and markers.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/config.py` for hyperparameters, paths, and random seeds
- [X] T005 [P] Setup `code/utils/logger.py` and `code/utils/checksum.py` for logging and data integrity
- [X] T006 [P] Create base data schemas in `specs/001-predict-sn1-rate-constants/contracts/`.
 **Mandatory Schema Definitions** (Must be written as YAML files):
 1. `dataset.schema.yaml`:
 ```yaml
 type: object
 required:
 - smiles
 - rate_constant
 - substrate_class
 properties:
 smiles:
 type: string
 description: Canonical SMILES string
 rate_constant:
 type: number
 description: Experimental rate constant
 substrate_class:
 type: string
 enum: [secondary, tertiary]
 description: Substrate classification
 gasteiger_charges:
 type: array
 items:
 type: number
 description: Gasteiger partial charges
 topological_indices:
 type: array
 items:
 type: number
 description: Topological indices
 source_id:
 type: string
 description: Source database ID
 ```
 2. `model_output.schema.yaml`:
 ```yaml
 type: object
 required:
 - model_id
 - metrics
 properties:
 model_id:
 type: string
 hyperparameters:
 type: object
 metrics:
 type: object
 properties:
 r2:
 type: number
 mae:
 type: number
 weights_path:
 type: string
 ```
 3. `exclusion_report.schema.yaml`:
 ```yaml
 type: object
 required:
 - row_index
 - reason
 - original_smiles
 properties:
 row_index:
 type: integer
 reason:
 type: string
 enum: [parsing_error, missing_rate, invalid_substrate]
 original_smiles:
 type: string
 ```
- [ ] T007B [P] Implement contract test harness in `tests/contract/`. **Deliverable**: Create `tests/contract/__init__.py` and a base test runner that loads YAML schemas from `contracts/` and validates JSON/CSV data against them. **DEPENDS ON**: T006, T007A.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest public SN1 kinetic datasets, parse SMILES, compute electronic descriptors, and produce a clean, stratified dataset ready for modeling.

**Independent Test**: Running the ingestion script on a known subset of the NIST database produces a CSV with valid SMILES, rate constants, and descriptors, with ≥95% success rate and proper stratification.

### Tests for User Story 1

- [X] T008 [P] [US1] Contract test for dataset schema in `tests/contract/test_dataset_schema.py` (DEPENDS ON T006, T007B)
- [X] T009 [P] [US1] Unit test for SMILES parsing and descriptor calculation in `tests/unit/test_descriptors.py`
- [X] T010 [P] [US1] Unit test for substrate filtering logic (SN2 removal) in `tests/unit/test_filtering.py`

### Implementation for User Story 1

- [X] T011 [US1] Implement `code/data/ingest.py` to fetch verified SN1 data. **Primary Source**: HuggingFace dataset `chemistry/dts-sn1`. **Fallback**: UCI `ucimlrepo` SN subset. **Column Mapping**: Map `smiles` -> SMILES, `rate` -> rate_constant, `substrate` -> substrate_class. **Logic**: If HuggingFace columns differ, apply transformation: `rate_constant = abs(row['rate'])`, `substrate_class = row['substrate'].lower()`. Handle missing values by logging to exclusion report.
- [X] T013 [US1] Implement `code/data/descriptors.py` to compute Gasteiger partial charges and topological indices using RDKit (CPU-only, approved alternative to PM7 per Constitution Amendment).
- [ ] T012 [US1] Implement `code/data/clean.py` to canonicalize SMILES and filter primary alkyl halides. **Filtering Rule**: Calculate `steric_hindrance_index = (CalcNumRotatableBonds + CalcMolMR) / MolecularWeight`. Filter row if `steric_hindrance_index > 2.0` OR if substrate class is explicitly 'primary'. **Justification**: This formula is the RDKit-compliant proxy for the spec's "steric hindrance index" requirement, normalized to ensure dimensional consistency with the threshold 2.0. Log all exclusions with reason. **DEPENDS ON**: T011, T013.
- [ ] T015 [US1] Generate exclusion report for invalid rows and save to `data/processed/exclusion_report.csv`. **Logic**: Aggregate exclusion logs from T012 (filtering) and T013 (descriptor calculation failures) into a single CSV with columns `row_index`, `reason`, `original_smiles`. Ensure the report matches `exclusion_report.schema.yaml`. **DEPENDS ON**: T011, T012, T013.
- [ ] T016 [US1] Save final processed dataset to `data/processed/cleaned_sn1.csv` with checksum. **DEPENDS ON**: T015.
- [X] T014 [US1] Implement `code/data/split.py` to perform a stratified split by substrate class (secondary/tertiary) into training, validation, and test sets with a majority portion allocated to training. **DEPENDS ON**: T016.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Graph Neural Network Training and Evaluation (Priority: P2)

**Goal**: Train a Message Passing Neural Network (MPNN) on the processed dataset using CPU-only inference, perform hyperparameter optimization, and evaluate against baselines.

**Independent Test**: The training job completes within 6 hours on a 2-core CPU runner, saves model weights, and outputs R²/MAE metrics comparing MPNN to linear regression with statistical significance.

### Implementation for User Story 2

- [X] T019 [US2] Implement `code/models/mpnn.py` with shallow architecture. **Constraint**: Layer count MUST be configurable via `config.py` but bounded between 1 and 4 layers. **Rationale**: The spec requires "configurable" layers, but the plan justifies the 1-4 bound as a CPU-tractable deviation. The code MUST allow configuration within these bounds. Enforce this via config validation.
- [X] T020 [US2] Implement `code/models/train.py` with random search hyperparameter optimization (≤50 configurations).
- [X] T021 [US2] Implement `code/models/evaluate.py` to calculate R² and MAE, and perform bootstrap comparison with a sufficient number of resamples against linear regression baseline.
- [ ] T022 [US2] Save best model weights to `artifacts/best_model.pt` and metrics to `artifacts/metrics.json`. **Selection Logic**: Select the configuration with the highest validation R² from T021's output. **Schema**: `metrics.json` must conform to `model_output.schema.yaml`. **DEPENDS ON**: T016, T020, T021.
- [ ] T023 [US2] Log top hyperparameter configurations and their validation scores to `artifacts/hyperparameter_search.log`. **Logic**: Identify top 10 configurations based on validation R² from T021. **DEPENDS ON**: T020, T021.

### Tests for User Story 2

- [X] T017 [P] [US2] Unit test for MPNN architecture and forward pass in `tests/unit/test_mpnn.py` (DEPENDS ON T019)
- [X] T018 [P] [US2] Integration test for training loop with small subset in `tests/integration/test_training.py` (DEPENDS ON T019, T020)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Interpretability and Sensitivity Analysis (Priority: P3)

**Goal**: Generate feature importance analysis, perform sensitivity analysis, validate findings via perturbation studies, and run collinearity diagnostics.

**Independent Test**: The interpretability module produces a SHAP summary plot, a sensitivity report, and a perturbation study confirming feature importance correlates with predictive performance.

### Implementation for User Story 3

- [X] T026 [US3] Implement `code/analysis/interpret.py` to generate SHAP values, rank the most salient structural features, and create summary plots for a single model. **DEPENDS ON**: T020, T021.
- [ ] T035 [US3] Implement `code/analysis/consistency.py` to re-run training with 5 different random seeds (from `config.py`), generate SHAP rankings for each, and compute the consistency metric (Kendall's Tau) across seeds. **Deliverable**: `artifacts/shap_consistency_report.md` confirming stability. **DEPENDS ON**: T020, T021, T026.
- [ ] T036 [US3] Implement `code/analysis/sensitivity_runner.py` to orchestrate the re-training of models with different feature subsets for sensitivity analysis. **Logic**: For each threshold in {0.01, 0.02, 0.05, 0.1, 0.2}, filter descriptors based on variance < threshold, re-train the model (using T020 logic), and evaluate. **DEPENDS ON**: T020, T021.
- [ ] T027 [US3] Implement `code/analysis/sensitivity.py` to aggregate results from T036 and generate the sensitivity report. **Logic**: Sweep thresholds for descriptor inclusion (variance < threshold) over a range of low-to-moderate values. Report resulting R² and MAE variance. **Constraint**: Do NOT modify descriptor magnitudes; only filter which descriptors are included in the model input. **DEPENDS ON**: T036.
- [X] T028 [US3] Implement `code/analysis/collinearity.py` to calculate VIF, flag pairs > 5, and perform PCA if necessary (DEPENDS ON T020, T021)
- [ ] T029 [US3] Implement perturbation study in `code/analysis/interpret.py`. **Method**: Identify top SHAP-ranked descriptors. **Mapping**: Map these global feature indices to the corresponding node feature indices in the graph input tensor. For each, create a perturbed dataset by **zeroing out the corresponding node features** (graph masking), re-run inference, and measure the drop in R². **Justification**: Graph masking is the approved implementation of "feature removal" for MPNNs, satisfying the semantic requirement of FR-008. **Constraint**: Do NOT remove columns from feature matrix; use graph masking to align with MPNN architecture. (DEPENDS ON T020, T021, T026)
- [ ] T030 [US3] Generate `artifacts/feature_importance.png`, `artifacts/sensitivity_report.csv`, and `artifacts/perturbation_results.csv`. **Format**: `sensitivity_report.csv` columns: `cutoff`, `r2`, `mae` (comma-delimited). `perturbation_results.csv` columns: `feature_id`, `original_r2`, `perturbed_r2`, `delta` (comma-delimited). **DEPENDS ON**: T026, T027, T029.

### Tests for User Story 3

- [X] T024 [P] [US3] Unit test for VIF calculation in `tests/unit/test_collinearity.py` (DEPENDS ON T028)
- [X] T025 [P] [US3] Unit test for SHAP value generation in `tests/unit/test_shap.py` (DEPENDS ON T026)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031 [P] Documentation updates in `specs/001-predict-sn1-rate-constants/quickstart.md`
- [X] T032 Code cleanup and refactoring of `code/main.py` orchestration script
- [ ] T033 [P] Run full pipeline integration test on small subset to verify end-to-end flow. **Dependencies**: T016 (Data), T022 (Model). **Deliverable**: `artifacts/integration_test_report.md` confirming all phases execute without error. **DEPENDS ON**: T016, T022.
- [ ] T034 [P] Validate `quickstart.md` against actual execution

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Strictly depends on T016 (cleaned dataset)**
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Strictly depends on T020/T021 (Training/Evaluation)**

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data ingestion/cleaning before splitting
- Splitting before training
- Training before evaluation and interpretability

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel (once their respective implementations are complete)
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (IF T006, T007B are complete):
# Note: T008 depends on T006, T007B, so those must finish first.
Task: "Contract test for dataset schema in tests/contract/test_dataset_schema.py" (DEPENDS ON T006, T007B)
Task: "Unit test for SMILES parsing and descriptor calculation in tests/unit/test_descriptors.py"
Task: "Unit test for substrate filtering logic in tests/unit/test_filtering.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/ingest.py to fetch verified SN1 data"
Task: "Implement code/data/descriptors.py to compute Gasteiger charges"
Task: "Implement code/data/clean.py to canonicalize SMILES and filter"
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
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Model Training)
 - Developer C: User Story 3 (Analysis)
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
- **Critical Constraint**: All tasks must be executable on CPU-only CI with limited resources and a bounded time limit. No GPU, no 8-bit quantization, no heavy QM calculations.
- **Note on Constitution VI**: The Plan explicitly substitutes Gasteiger charges for PM7 to satisfy CPU constraints. This deviation is documented in the Plan's Constitution Check and is the approved implementation path for this project.