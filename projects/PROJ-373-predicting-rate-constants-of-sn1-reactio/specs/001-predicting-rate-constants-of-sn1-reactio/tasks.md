---
description: "Task list template for feature implementation"
---

# Tasks: Predicting Rate Constants of SN1 Reactions from Molecular Structure

**Input**: Design documents from `/specs/001-predict-sn1-rate-constants/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
- Paths shown below assume single project - adjusted based on plan.md structure

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
 - Delivered as a MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

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
- [X] T006A [P] Create `dataset.schema.yaml` in `specs/001-predict-sn1-rate-constants/contracts/`. **Deliverable**: YAML schema file defining `smiles`, `rate_constant`, `substrate_class`, `gasteiger_charges`, `topological_indices`, `source_id`. **DEPENDS ON**: T006 (Foundational setup).
- [X] T006B [P] Create `model_output.schema.yaml` in `specs/001-predict-sn1-rate-constants/contracts/`. **Deliverable**: YAML schema file defining `model_id`, `hyperparameters`, `metrics` (r2, mae), `weights_path`. **DEPENDS ON**: T006 (Foundational setup).
- [X] T006C [P] Create `exclusion_report.schema.yaml` in `specs/001-predict-sn1-rate-constants/contracts/`. **Deliverable**: YAML schema file defining `row_index`, `reason`, `original_smiles`. **DEPENDS ON**: T006 (Foundational setup).
- [X] T007B [P] Implement contract test harness in `tests/contract/`. **Deliverable**: Create `tests/contract/__init__.py` and a base test runner that loads YAML schemas from `contracts/` and validates JSON/CSV data against them. **DEPENDS ON**: T006A, T006B, T006C, T007A.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest public SN1 kinetic datasets, parse SMILES, compute electronic descriptors, and produce a clean, stratified dataset ready for modeling.

**Independent Test**: Running the ingestion script on a known subset of the NIST database produces a CSV with valid SMILES, rate constants, and descriptors, with ≥95% success rate and proper stratification.

### Tests for User Story 1

- [X] T008 [P] [US1] Contract test for dataset schema in `tests/contract/test_dataset_schema.py` (DEPENDS ON T006A, T007B)
- [X] T009 [P] [US1] Unit test for SMILES parsing and descriptor calculation in `tests/unit/test_descriptors.py`
- [X] T010 [P] [US1] Unit test for substrate filtering logic (SN2 removal) in `tests/unit/test_filtering.py`

### Implementation for User Story 1

- [X] T011 [US1] Implement `code/data/ingest.py` to fetch verified SN1 data. **Primary Source**: HuggingFace dataset `chemistry/dts-sn1`. **Fallback**: UCI `ucimlrepo` SN subset. **Column Mapping**: Map `smiles` -> SMILES, `rate` -> rate_constant, `substrate` -> substrate_class. **Logic**: If HuggingFace columns differ, apply transformation: `rate_constant = abs(row['rate'])`, `substrate_class = row['substrate'].lower()`. Handle missing values by logging to exclusion report.
- [X] T013 [US1] Implement `code/data/descriptors.py` to compute Gasteiger partial charges and topological indices using RDKit (CPU-only, approved alternative to PM7 per Constitution Amendment).
- [X] T012 [US1] Implement `code/data/clean.py` to canonicalize SMILES and filter primary alkyl halides. **Filtering Rule**: Calculate `steric_hindrance_proxy = CalcNumRotatableBonds + CalcCrippenDescriptors[0]` (LogP) **locally within this task** using RDKit. **Implementation**: Use `rdkit.Chem.rdMolDescriptors.CalcNumRotatableBonds` and `rdkit.Chem.Crippen.CalcCrippenDescriptors`. **Justification**: This composite is the **project-defined proxy** for the undefined 'steric hindrance index' in the spec Edge Cases. **Filter**: Row if `steric_hindrance_proxy > 2.0` OR if substrate class is explicitly 'primary'. **Units**: Both components are dimensionless (counts or logP). **Logic**: Log all exclusions with reason. **DEPENDS ON**: T011 (data structure), T013 (for Gasteiger charges and final dataset structure, NOT for proxy calculation).
- [ ] T015 [US1] Generate exclusion report for invalid rows and save to `data/processed/exclusion_report.csv`. **Logic**: Aggregate exclusion logs from T012 (filtering) and T013 (descriptor calculation failures) into a single CSV with columns `row_index`, `reason`, `original_smiles`. Ensure the report matches `exclusion_report.schema.yaml`. Map specific errors: 'SMILES canonicalization failed' -> 'canonicalization_error', 'Gasteiger convergence error' -> 'gasteiger_convergence_error'. **Synchronization**: Wait for completion of T012 and T013 before aggregating. **DEPENDS ON**: T011, T012, T013.
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
- [ ] T022 [US2] Save best model weights to `artifacts/best_model.pt` and metrics to `artifacts/metrics.json`. **Selection Logic**: Select the configuration with the highest validation R² from T021's output. **Schema**: `metrics.json` must conform to `model_output.schema.yaml`. **Validation**: Explicitly run schema validation on `metrics.json` before saving. **DEPENDS ON**: T016, T020, T021.
- [ ] T023 [US2] Log top hyperparameter configurations to `artifacts/hyperparameter_search.csv`. **Logic**: Identify top 10 configurations based on validation R² from T021. **Format**: CSV with columns `config_id`, `learning_rate`, `hidden_dim`, `dropout`, `r2_val`, `mae_val`. **Note**: This is optional but recommended for reproducibility. **DEPENDS ON**: T020, T021.

### Tests for User Story 2

- [X] T017 [P] [US2] Unit test for MPNN architecture and forward pass in `tests/unit/test_mpnn.py` (DEPENDS ON T019)
- [X] T018 [P] [US2] Integration test for training loop with small subset in `tests/integration/test_training.py` (DEPENDS ON T019, T020)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Interpretability and Sensitivity Analysis (Priority: P3)

**Goal**: Generate feature importance analysis, perform sensitivity analysis, validate findings via perturbation studies, and run collinearity diagnostics.

**Independent Test**: The interpretability module produces a SHAP summary plot, a sensitivity report, and a perturbation study confirming feature importance correlates with predictive performance.

### Implementation for User Story 3

- [X] T026 [US3] Implement `code/analysis/interpret.py` to generate SHAP values, rank the most salient structural features, and create summary plots for a single model. **Logic**: Aggregate graph-level SHAP values to global **tabular descriptors** (e.g., mean absolute SHAP per descriptor type) for downstream analysis. **DEPENDS ON**: T020, T021.
- [X] T029 [US3] Implement perturbation study in `code/analysis/interpret.py`. **Method**: Identify top SHAP-ranked **global TABULAR descriptors** (aggregated from graph-level SHAP in T026). **Logic**: 1) Perturb the values of the top-ranked **tabular descriptors** in the *tabular feature matrix* (e.g., ±10% noise or set to mean) for the test set. 2) Re-run inference on the **fixed best model** (from T022) and measure the drop in R². **Constraint**: Do NOT modify the model weights or require masked graph inference. **DEPENDS ON**: T022, T026.
- [ ] T030 [US3] Generate `artifacts/feature_importance.png`, `artifacts/sensitivity_report.csv`, and `artifacts/perturbation_results.csv`. **Format**: `sensitivity_report.csv` columns: `cutoff` (float), `r2` (float), `mae` (float). `perturbation_results.csv` columns: `feature_id` (int), `original_r2` (float), `perturbed_r2` (float), `delta` (float). **Note**: SC-006 (Power Analysis) is excluded from this project. **DEPENDS ON**: T026, T029.
- [X] T035 [US3] Implement `code/analysis/consistency.py` to verify SHAP consistency across random seeds. **Logic**: Load the **single fixed model from T022** and the test set. Run SHAP analysis **5 times** with different random seeds (perturbation seeds only, **no re-training**). Compute Kendall's Tau correlation of the resulting feature rankings. **Constraint**: Do NOT re-train the model. **Fallback**: If time budget is exceeded, reduce to a minimal set of runs and log the reduction. **Deliverable**: `artifacts/shap_consistency_report.md` confirming stability. **DEPENDS ON**: T022, T026. <!-- FAILED: unspecified -->
- [X] T036 [US3] Implement `code/analysis/sensitivity_runner.py` to perform sensitivity analysis by varying descriptor thresholds. **Logic**: Load the **fixed best model from T022** (trained once on full data) and the cleaned dataset (T016). For each threshold in {0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0}: 1) Filter the dataset to include only molecules with `steric_hindrance_proxy <= threshold`. 2) Perform **inference-only evaluation** on this filtered subset using the fixed model. 3) Record R² and MAE. **Requirement**: This measures the model's sensitivity to the chemical threshold **without re-training**. **Constraint**: Do NOT re-train the model. **DEPENDS ON**: T016, T022.
- [X] T027 [US3] Implement `code/analysis/sensitivity.py` to aggregate results from T036 and generate the sensitivity report. **Logic**: Aggregate R² and MAE from T036's evaluations. Report the variance in performance as a function of the steric index cutoff. **Constraint**: Do NOT modify descriptor magnitudes; only filter molecules. **DEPENDS ON**: T036.
- [X] T028 [US3] Implement `code/analysis/collinearity.py` to calculate VIF, flag pairs > 5, and perform PCA if necessary (DEPENDS ON T020, T021)

### Tests for User Story 3

- [X] T024 [P] [US3] Unit test for VIF calculation in `tests/unit/test_collinearity.py` (DEPENDS ON T028)
- [X] T025 [P] [US3] Unit test for SHAP value generation in `tests/unit/test_shap.py` (DEPENDS ON T026)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031A [P] Create `quickstart.md` v0.1 placeholder in `specs/001-predict-sn1-rate-constants/`. **Deliverable**: A draft document with project structure, dependency installation steps, and placeholder sections for results. **DEPENDS ON**: T001, T002.
- [X] T032 Code cleanup and refactoring of `code/main.py` orchestration script
- [ ] T033 [US2] Run full pipeline integration test on **small subset** to verify end-to-end flow. **Dependencies**: T016 (Data), T022 (Model). **Logic**: Use a subset of 50 rows for this test to ensure speed. **Deliverable**: `artifacts/integration_test_report.md` confirming all phases execute without error. **Note**: This task is sequential, dependent on T016 and T022. **DEPENDS ON**: T016, T022.
- [ ] T031B [P] Finalize `quickstart.md` in `specs/001-predict-sn1-rate-constants/`. **Dependencies**: T033 (integration test report). **Logic**: Update `quickstart.md` with actual paths, command examples, and verified output descriptions from the integration test. **Fallback**: If T033 fails or produces no report, update `quickstart.md` based on manual verification of code paths and standard defaults. **DEPENDS ON**: T033.
- [ ] T034 [P] Validate `quickstart.md` against actual execution. **Dependencies**: T031B. **Logic**: Verify that `quickstart.md` instructions match the steps and outputs generated in T033. **Note**: This task does NOT depend on T036 (full sensitivity sweep), breaking the circular dependency. **DEPENDS ON**: T031B.

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Strictly depends on T020/T021/T022 (Training/Evaluation/Model Save)**

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
# Launch all tests for User Story 1 together (IF T006A, T006B, T006C, T007B are complete):
# Note: T008 depends on T006A, T007B, so those must finish first.
Task: "Contract test for dataset schema in tests/contract/test_dataset_schema.py" (DEPENDS ON T006A, T007B)
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
- **Revision Note**: Tasks T015, T016, T022, T023, T030, T031A, T031B, T033, T034 were added/updated to address review concerns regarding artifact generation, schema validation, and documentation flow. T012, T035, T036, T029 were updated to address chemical rule and sensitivity analysis concerns. T035 and T036 were re-implemented to use inference-time perturbation to meet the 6h runtime constraint.
- **Revision Note 2 (R1)**: T036, T035, T029, T012 updated to explicitly resolve ordering and executability concerns by clarifying "fixed model" usage, "local calculation" dependencies, and "inference-only" logic. T035 now includes a fallback strategy for time budget.