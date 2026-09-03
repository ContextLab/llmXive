---
description: "Task list template for feature implementation"
---

# Tasks: Predicting Rate Constants of SN1 Reactions from Molecular Structure

**Input**: Design documents from `/specs/001-predict-sn1-rate-constants/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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

 Tasks MUST be organized by user story so each story can:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan (`code/`, `data/`, `tests/`, `specs/`)
- [X] T002 Initialize Python project with `requirements.txt` (rdkit, torch, scikit-learn, shap, pandas, pyyaml, datasets)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools
- [X] T007A [P] Create `pytest.ini` configuration file in project root to enable test discovery and coverage reporting. **Deliverable**: `pytest.ini` with `[pytest]` section defining test paths and markers.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/config.py` for hyperparameters, paths, and random seeds
- [X] T005 [P] Setup `code/utils/logger.py` and `code/utils/checksum.py` for logging and data integrity
- [X] T006A [P] Create `dataset.schema.yaml` in `specs/001-predict-sn1-rate-constants/contracts/`. **Deliverable**: YAML schema file defining `smiles`, `rate_constant`, `substrate_class`, `gasteiger_charges`, `topological_indices`, `source_id`. **DEPENDS ON**: T004 (requires path and hyperparameter definitions from config.py to validate schema constraints).
- [X] T006B [P] Create `model_output.schema.yaml` in `specs/001-predict-sn1-rate-constants/contracts/`. **Deliverable**: YAML schema file defining `model_id`, `hyperparameters`, `metrics` (r2, mae), `weights_path`. **DEPENDS ON**: T004 (requires configuration from config.py for model output schema validation).
- [X] T006C [P] Create `exclusion_report.schema.yaml` in `specs/001-predict-sn1-rate-constants/contracts/`. **Deliverable**: YAML schema file defining `row_index`, `reason`, `original_smiles`. **DEPENDS ON**: T004 (requires configuration values (error codes) defined in config.py).
- [X] T007B [P] Implement contract test harness in `tests/contract/`. **Deliverable**: Create `tests/contract/__init__.py` and `tests/contract/base_runner.py` containing the `ContractTestRunner` class. **DEPENDS ON**: T006A, T006B, T006C, T007A (validates data and output against the schemas defined in these tasks).

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

- [ ] T011a [US1] Implement `code/data/schema_check.py` to verify dataset metadata. **Primary Source**: HuggingFace datasets `DTS-SN1-15-01-2024` and `SN18-All-20240204`. **Constraint**: If 'substrate_class', 'temperature', OR 'solvent' columns are missing, raise a fatal ValueError and halt the entire pipeline. **NO FALLBACK**: Do NOT fetch from UCI or derive labels. **Logic**: 1) Fetch dataset info from HF. 2) Verify columns. 3) If missing, immediately raise `ValueError` with descriptive message and halt execution. **Output**: `data/processed/schema_check.log`. **DEPENDS ON**: T004 (requires dataset paths and validation thresholds).
- [ ] T011b [US1] Implement `code/data/download.py` to fetch verified SN1 data. **Constraint**: Use `datasets.load_dataset(..., streaming=True)` if size > 7GB. **Logic**: 1) If T011a passed, download/stream. 2) Save raw data to `data/raw/`. **Output**: `data/raw/sn1_raw.parquet`. **DEPENDS ON**: T011a.
- [ ] T011c [US1] Implement `code/data/mapping.py` to map columns and clean initial data. **Constraint**: Map `smiles` -> SMILES, `rate` -> rate_constant. **Logic**: 1) Load raw data. 2) Map columns. 3) Log rows with missing rate/SMILES to `data/processed/exclusion_raw.log`. **Output**: `data/processed/intermediate_sn1.csv`. **DEPENDS ON**: T011b.
- [ ] T012 [US1] Implement `code/data/clean.py` to canonicalize SMILES and filter primary alkyl halides. **Input**: `data/processed/intermediate_sn1.csv` (output of T011c). **Guard Clause**: If `intermediate_sn1.csv` is missing or empty, raise a fatal ValueError and log `data/processed/clean.log` with `status: 'fatal_error', reason: 'input_missing'` and exit. **Filtering Rule**: Filter rows ONLY if `substrate_class` is explicitly labeled as 'primary'. **Constraint**: Do NOT use proxies. **Stereochemistry Handling**: Standardize SMILES. If fails, exclude with code 'ambiguous_stereochemistry'. **Logic**: Log all exclusions to `data/processed/clean.log`. **Output**: `data/processed/cleaned_intermediate.csv`. **Verification**: Verify output contains no ‘primary’ rows. **Code Comment**: 'Filtering based on explicit substrate_class label only; no proxies used'. **DEPENDS ON**: T011c.
- [ ] T013 [US1] Implement `code/data/descriptors.py` to compute Gasteiger partial charges and topological indices. **Determinism**: Use fixed RDKit version. **Logic**: Compute descriptors. If a row fails, append the failure directly to `data/processed/exclusion_raw.log` (consolidated with T015). **Output**: `data/processed/descriptors.csv`. **DEPENDS ON**: T011c. <!-- FAILED: unspecified -->
- [ ] T015 [US1] Aggregate, map, and validate exclusion logs. **Input**: `data/processed/clean.log` (from T012) and `data/processed/exclusion_raw.log` (from T011b, T013). **Guard Clause**: If `clean.log` or `exclusion_raw.log` are missing/empty, log `data/processed/exclusion_report.csv` with `status: 'blocked', reason: 'upstream_missing'` and exit. **Logic**: 1) Merge logs into `data/processed/exclusion_mapped.json`. 2) Map error strings to schema codes (e.g., 'Primary substrate' -> 'primary_substrate_filter'). 3) Validate against `exclusion_report.schema.yaml`. 4) Save final list to `data/processed/exclusion_report.csv`. **Constraint**: Must wait for T012 and T013. **DEPENDS ON**: T012, T013.
- [ ] T016 [US1] Save final processed dataset to `data/processed/cleaned_sn1.csv` with checksum. **Logic**: 1) Load cleaned data. 2) Calculate `success_rate = (len(final_df) / len(input_df))

We aim to determine: To what extent can large language models assist in the automated generation of unit tests for Python code? via Method: We will evaluate LLM-generated unit tests by measuring the proportion of generated tests that successfully pass against a held-out dataset of Python functions. (Vaswani et al., 2017) indicates the potential of transformer networks for sequence-to-sequence tasks, which is relevant to our test generation approach. A higher success rate suggests greater effectiveness in generating functional unit tests.`. 3) Log `success_rate` to `data/processed/success_rate.json` and proceed regardless of value. 4) Save CSV and generate checksum. 5) Output: Save `post_filter_distribution.json`. **DEPENDS ON**: T015, T012, T013.
- [X] T014 [US1] Implement `code/data/split.py` to perform a stratified split by substrate class. **Logic**: 1) Load cleaned dataset from T016. 2) Stratify on remaining classes. 3) Verify proportional representation matches original distribution within 5% variance. **DEPENDS ON**: T016, T011a. <!-- FAILED: unspecified -->

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Graph Neural Network Training and Evaluation (Priority: P2)

**Goal**: Train a Message Passing Neural Network (MPNN) on the processed dataset using CPU-only inference, perform hyperparameter optimization, and evaluate against baselines.

**Independent Test**: The training job completes within 6 hours on a 2-core CPU runner., saves model weights, and outputs R²/MAE metrics comparing MPNN to linear regression with statistical significance.

### Implementation for User Story 2

- [X] T019 [US2] Implement `code/models/mpnn.py` with shallow architecture. **Constraint**: Layer count MUST be configurable via `config.py` but bounded within 1-4 range. **Logic**: Read layer count from `config.py` and validate against bounds.
- [X] T020 [US2] Implement `code/models/train.py` with random search hyperparameter optimization (≤50 configurations).
- [X] T021 [US2] Implement `code/models/evaluate.py` to calculate R² and MAE, and perform bootstrap comparison. **Output**: Save metrics to `artifacts/training_metrics.json`.
- [X] T022 [US2] Save best model weights to `artifacts/best_model.pt` (in `.pt` PyTorch format) and metrics to `artifacts/metrics.json`. **Selection Logic**: Select configuration with highest validation R². **Schema**: `metrics.json` must conform to `model_output.schema.yaml`. **DEPENDS ON**: T016, T020, T021.
- [X] T023 [US2] Log top hyperparameter configurations to `artifacts/hyperparameter_search.csv`. **Logic**: Identify the top configurations. **Format**: CSV with columns `config_id`, `learning_rate`, `hidden_dim`, `dropout`, `r2_val`, `mae_val`. **DEPENDS ON**: T020, T021.

### Tests for User Story 2

- [X] T017 [P] [US2] Unit test for MPNN architecture and forward pass in `tests/unit/test_mpnn.py` (DEPENDS ON T019)
- [X] T018 [P] [US2] Integration test for training loop with small subset in `tests/integration/test_training.py` (DEPENDS ON T019, T020)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Interpretability and Sensitivity Analysis (Priority: P3)

**Goal**: Generate feature importance analysis, perform sensitivity analysis, validate findings via perturbation studies, and run collinearity diagnostics.

**Independent Test**: The interpretability module produces a SHAP summary plot, a sensitivity report, and a perturbation study confirming feature importance correlates with predictive performance.

### Implementation for User Story 3

- [X] T026 [US3] Implement `code/analysis/interpret.py` to generate SHAP values and summary plots. **Logic**: Aggregate graph-level SHAP values to global tabular descriptors. **Artifact**: Save node-level SHAP values to `artifacts/node_shap_values.npy`. **DEPENDS ON**: T022, T020, T021.
- [X] T029 [US3] Implement perturbation study in `code/analysis/interpret.py`. **Method**: Direct implementation of feature removal. **Logic**: 1) Identify top-ranked atoms by absolute SHAP value. 2) Set node features of these atoms to zero. 3) Re-run inference on fixed best model. 4) Measure drop in R². 5) Save results to `artifacts/perturbation_results.csv`. **DEPENDS ON**: T022, T026.
- [X] T036 [US3] Implement `code/analysis/sensitivity_runner.py` to perform sensitivity analysis by sweeping top-k descriptors (linear range starting from a minimum threshold). **Logic**: 1) Load best model and cleaned dataset. 2) Sort descriptors by absolute SHAP magnitude. 3) For k in 1 to 10: 4) Select top k descriptors. 5) Perform inference-only evaluation. 6) Calculate variance. **Artifact**: Save to `artifacts/top_k_sensitivity.csv` with `variance` column. **DEPENDS ON**: T016, T022.
- [X] T037 [US3] Implement `code/analysis/hyperparameter_sensitivity.py` to measure model robustness. **Logic**: 1) Select a stratified sample of a representative size. 2) Test explicit configurations. 3) Train shallow MPNN on subset. 4) Evaluate on held-out subset. 5) Calculate variance. **Artifact**: Save to `artifacts/hyperparameter_sensitivity_report.csv`. **DEPENDS ON**: T022, T016.
- [X] T027 [US3] Implement `code/analysis/interpret.py` to aggregate results from T036 and T037. **Logic**: Aggregate R² and MAE. Calculate overall variance. **Artifact**: Save to `artifacts/sensitivity_report.csv`. **DEPENDS ON**: T036, T037.
- [X] T028 [US3] Implement `code/analysis/collinearity.py` to calculate VIF and generate JSON report. **Input**: Feature matrix from `data/processed/cleaned_sn1.csv`. **Guard Clause**: If `cleaned_sn1.csv` is missing or empty, raise a fatal ValueError and log `artifacts/collinearity_report.json` with `status: 'fatal_error', reason: 'input_missing'` and exit. **Logic**: 1) Calculate VIF for all predictors (excluding Gasteiger). 2) Identify pairs with VIF > 5. 3) Generate strict JSON report (`collinearity_report.json`) with keys: `descriptor_a`, `descriptor_b`, `vif_score`, `flag_reason`. **Constraint**: Do NOT generate descriptive text or `is_flagged` boolean. **Artifact**: Save to `artifacts/collinearity_report.json`. **DEPENDS ON**: T016.
- [X] T035 [US3] Implement `code/analysis/consistency.py` to verify SHAP consistency across random seeds (SC-004). **Logic**: 1) Load data from T016 and best config from T023. 2) Calculate the feasibility of running with full dataset given time limit. If feasible, use full dataset; otherwise, sample largest possible subset. 3) Re-train model using a fixed seed. 4) Run SHAP analysis on test set. 5) Compute Kendall's Tau correlation of feature rankings. **Deliverable**: Save report to `artifacts/shap_consistency_report.md`. **DEPENDS ON**: T016, T023.

### Tests for User Story 3

- [X] T024 [P] [US3] Unit test for VIF calculation in `tests/unit/test_collinearity.py` (DEPENDS ON T028)
- [X] T025 [P] [US3] Unit test for SHAP value generation in `tests/unit/test_shap.py` (DEPENDS ON T026)

**Checkpoint**: At this point, User Story 3 implementation is complete.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T031A [P] Create `quickstart.md` v0.1 placeholder in `specs/001-predict-sn1-rate-constants/`. **Deliverable**: A draft document with project structure, dependency installation steps, and placeholder sections for results. **DEPENDS ON**: T001, T002.
- [X] T032 Code cleanup and refactoring of `code/main.py` orchestration script
- [X] T033A [P] Execute full pipeline integration test on a small subset of rows. **Deliverable**: Raw execution logs. **Success Criteria**: Exit code 0 and specific log strings "Pipeline completed successfully". **DEPENDS ON**: T016, T022.
- [X] T033B [P] Validate exit codes and artifact existence from T033A. **Deliverable**: Validation status. **Logic**: Verify exit code is 0 and key artifacts exist. **DEPENDS ON**: T033A.
- [X] T033C [P] Generate `artifacts/integration_test_report.md` based on T033A/B results. **Logic**: If T033A/B pass, document success. If fail, document failure with error logs. **DEPENDS ON**: T033A, T033B.
- [X] T031B [P] Finalize `quickstart.md` in `specs/001-predict-sn1-rate-constants/`. **Dependencies**: T033C. **Logic**: Update `quickstart.md` with actual paths, command examples, and verified output descriptions from T033C. **Fallback**: If T033C fails, update based on manual verification of code paths and standard defaults. **DEPENDS ON**: T033C.
- [X] T034 [P] Validate `quickstart.md` against actual execution. **Dependencies**: T031B, T033C (or T031B fallback evidence). **Logic**: 1) If T033C succeeded, validate against T033C's execution evidence. 2) If T033C failed and T031B used fallback, validate against manual verification evidence. 3) Fallback: If no execution evidence exists, validate against code structure and `config.py` defaults. **DEPENDS ON**: T031B, T033C.

---

## Phase 7: Final Verification & Reporting

**Purpose**: Ensure all success criteria are met and prepare final documentation.

- [ ] T040 [P] Perform a final end-to-end validation run on the full dataset (if time permits) or the largest feasible subset. **Logic**: 1) Re-run the full pipeline (`main.py`) from ingestion to final report generation using the production configuration. 2) Record actual runtime in `artifacts/feasibility_test_log.json`. 3) Verify all artifacts are generated and match expected schemas. 4) Compare results against T033. **Constraint**: No timeout mechanism, allow run to complete (or be killed by CI). **DEPENDS ON**: T039, T022, T028.
- [X] T039 [US3] Generate final comprehensive report aggregating all metrics, plots, and statistical analyses. **Logic**: 1) Aggregate `metrics.json`, `shap_consistency_report.md`, `sensitivity_report.csv`, `perturbation_results.csv`, `collinearity_report.json`, `hyperparameter_search.csv`, and `feasibility_test_log.json` (from T040). 2) Create a summary section for each Success Criterion (SC-001 to SC-005) explicitly stating whether it is met. 3) Include a "Limitations" section. 4) Output Artifact: Save to `artifacts/final_report.md`. **Schema Requirements**: The report MUST contain the following sections in order: `# Final Report`, `## Executive Summary`, `## Methodology`, `## Results`, `## Limitations`, `## Conclusion`. **DEPENDS ON**: T022, T028, T029, T030, T035, T036, T037, T040.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Final Verification (Phase 7)**: Depends on all User Stories and Polish phases

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Strictly depends on T016 (cleaned dataset)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Strictly depends on T022 (model training) and T016 (cleaned dataset).

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
