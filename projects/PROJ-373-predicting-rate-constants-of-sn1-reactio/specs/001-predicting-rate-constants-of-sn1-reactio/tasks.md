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
- [X] T012 [US1] Implement `code/data/clean.py` to canonicalize SMILES and filter primary alkyl halides. **Filtering Rule**: Calculate `steric_hindrance_proxy` using RDKit. **Implementation**: Use `rdkit.Chem.rdMolDescriptors.CalcNumRotatableBonds` and `rdkit.Chem.Crippen.CalcCrippenDescriptors(mol)[0]` (LogP). **Formula**: `proxy = CalcNumRotatableBonds(mol) + CalcCrippenDescriptors(mol)[0]`. **Filter**: Row if `proxy > 2.0` OR if substrate class is explicitly 'primary'. **Justification**: This is a project-defined proxy for the undefined 'steric hindrance index' in the spec Edge Cases, as documented in the Plan's Constitution Check. **Logic**: Log all exclusions with reason. **DEPENDS ON**: T011 (data structure). **Note**: T013 is NOT required for this proxy calculation.
- [ ] T015A [US1] Aggregate exclusion logs from T012 and T013 into a raw list. **Logic**: Merge log entries from `clean.py` and `descriptors.py` into a single list of dicts with fields `row_index`, `reason`, `original_smiles`. **Constraint**: MUST wait for completion of BOTH T012 and T013 before executing. **Schema**: Output must be a JSON list of objects: `[{ "row_index": int, "reason": str, "original_smiles": str }]`. **Artifact**: Save raw list to `data/processed/exclusion_logs_raw.json`. **DEPENDS ON**: T012, T013.
- [ ] T015B [US1] Map raw exclusion reasons to standardized schema codes. **Logic**: Transform raw error strings into schema-compliant codes: 'SMILES canonicalization failed' -> 'canonicalization_error', 'Gasteiger convergence error' -> 'gasteiger_convergence_error', 'Primary substrate' -> 'primary_substrate_filter'. **DEPENDS ON**: T015A.
- [ ] T015C [US1] Validate aggregated exclusion data against `exclusion_report.schema.yaml` and save to `data/processed/exclusion_report.csv`. **Logic**: Load the mapped data from T015B, validate against schema, and save as CSV. **DEPENDS ON**: T015B.
- [X] T016 [US1] Save final processed dataset to `data/processed/cleaned_sn1.csv` with checksum and verify success rate. **Logic**: 1) Load the cleaned data from T012/T013. 2) Calculate `success_rate = (len(final_df) / len(input_df)) * 100`. 3) **FAIL TASK** if `success_rate < 95%` by raising `SystemExit(1)`. 4) Save CSV and generate checksum. **DEPENDS ON**: T015C, T012, T013.
- [X] T014 [US1] Implement `code/data/split.py` to perform a stratified split by substrate class (secondary/tertiary) into training, validation, and test sets. **Logic**: 1) Load cleaned dataset from T016. 2) Identify unique substrate classes present (expected: secondary, tertiary). **Note: If primary substrates were filtered in T012, stratify ONLY on the remaining classes (secondary, tertiary)**. 3) Stratify on these *remaining* classes. 4) Calculate variance of split distributions against the *original distribution of the filtered dataset* (post-T012) to ensure variance ≤ 5%. **DEPENDS ON**: T016.

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
- [ ] T023 [US2] Log top hyperparameter configurations to `artifacts/hyperparameter_search.csv`. **Logic**: Identify top 10 configurations based on validation R² from T021. **Format**: CSV with columns `config_id`, `learning_rate`, `hidden_dim`, `dropout`, `r2_val`, `mae_val`. **Requirement**: This artifact is **REQUIRED** for traceability per FR-003. **Verification**: Verify `hyperparameter_search.csv` is saved and non-empty. **DEPENDS ON**: T020, T021.

### Tests for User Story 2

- [X] T017 [P] [US2] Unit test for MPNN architecture and forward pass in `tests/unit/test_mpnn.py` (DEPENDS ON T019)
- [X] T018 [P] [US2] Integration test for training loop with small subset in `tests/integration/test_training.py` (DEPENDS ON T019, T020)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4.5: User Story 3 - Interpretability and Sensitivity Analysis (Parallel Task)

**Goal**: Verify SHAP consistency across random seeds (independent of T022) and perform sensitivity analysis.

- [ ] T035 [US3] Implement `code/analysis/consistency.py` to verify SHAP consistency across random seeds (SC-004). **Logic**: 1) Load the data from T016 and the best config from T023. 2) Re-train a **shallow MPNN (2 layers)** 3 times from scratch with seeds `[42, 123, 456]` on a **stratified subset of 1000 rows** to ensure execution within the 6-hour budget. 3) For each trained model, run SHAP analysis on the test set to extract **node-level** SHAP values. 4) Aggregate node-level SHAP to global feature rankings and compute Kendall's Tau correlation of the resulting feature rankings across the 3 seeds. 5) Validate that the top 5 features are consistent (Kendall's Tau > 0.7). **Deliverable**: Save report to `artifacts/shap_consistency_report.md`. **DEPENDS ON**: T016, T020, T021, T023. **Note**: This task satisfies SC-004 without duplicating the full training cost.

---

## Phase 5: User Story 3 - Interpretability and Sensitivity Analysis (Priority: P3)

**Goal**: Generate feature importance analysis, perform sensitivity analysis, validate findings via perturbation studies, and run collinearity diagnostics.

**Independent Test**: The interpretability module produces a SHAP summary plot, a sensitivity report, and a perturbation study confirming feature importance correlates with predictive performance.

### Implementation for User Story 3

- [X] T026 [US3] Implement `code/analysis/interpret.py` to generate SHAP values, rank the most salient structural features, and create summary plots for a single model. **Logic**: Aggregate graph-level SHAP values to global **tabular descriptors** (e.g., mean absolute SHAP per descriptor type) for downstream analysis. **Additionally**: Extract **node-level** SHAP values for each molecule to support perturbation studies. **DEPENDS ON**: T020, T021.
- [ ] T029 [US3] Implement perturbation study in `code/analysis/interpret.py`. **Method**: Identify top SHAP-ranked **atoms (nodes)** using the **node-level** SHAP values extracted in T026. **Logic**: 1) For each molecule in the test set, identify the top atoms with the highest absolute SHAP value. 2) Create a mask for these specific nodes by setting their node features to zero in the graph input. 3) Re-run inference on the **fixed best model** (from T022) using the masked graphs. 4) Measure the drop in R² compared to the unmasked baseline. 5) **Save results to `artifacts/perturbation_results.csv`**. **Note**: This satisfies FR-008's requirement for structural perturbation. **DEPENDS ON**: T022, T026.
- [ ] T030 [US3] Verify artifact existence and schema compliance. **Logic**: 1) Verify `artifacts/feature_importance.png` exists and is non-empty (generated by T026). 2) Verify `artifacts/sensitivity_report.csv` exists and has correct columns: `threshold_type` (str), `threshold_value` (float), `r2` (float), `mae` (float), `variance` (float). 3) Verify `artifacts/perturbation_results.csv` exists and has correct columns (generated by T029). **Aggregation**: Map T036 cutoffs to CSV rows, aggregate T037 variances. **Verification**: Verify all files exist and have non-zero size. **Note**: SC-006 (Power Analysis) is excluded from this project. **DEPENDS ON**: T026, T029, T036, T037.
- [X] T036 [US3] Implement `code/analysis/sensitivity_runner.py` to perform sensitivity analysis by sweeping **descriptor value thresholds**. **Logic**: Load the **fixed best model from T022** (trained once on full data) and the cleaned dataset (T016). 1) Calculate the 10th and 90th percentile of the max absolute Gasteiger charge in the dataset. 2) Define a sweep range from the lower to upper percentiles in equal steps. 3) For each threshold in the range: Filter the dataset to include only molecules where `abs(max_gasteiger_charge) <= threshold`. 4) Perform **inference-only evaluation** on this filtered subset using the fixed model. 5) Record R² and MAE. **Requirement**: This measures the model's sensitivity to descriptor value thresholds **without re-training**. **Constraint**: Do NOT re-train the model. **Constraint**: DO NOT filter by steric_hindrance_proxy (data sensitivity). **DEPENDS ON**: T016, T022.
- [X] T037 [US3] Implement `code/analysis/hyperparameter_sensitivity.py` to measure model robustness to hyperparameter changes. **Logic**: 1) Select a **stratified sample** of the dataset (size: 2000 rows, stratify by `substrate_class`, seed=42). 2) Test the following **5 configurations** explicitly: (1) LR=0.01, Dropout=0.0; (2) LR=0.01, Dropout=0.5; (3) LR=0.001, Dropout=0.0; (4) LR=0.001, Dropout=0.5; (5) LR=0.1, Dropout=0.2. 3) Train a **shallow MPNN (2 layers)** on the subset for each configuration. 4) Evaluate on a held-out subset of the sample. 5) Calculate variance in R² across the sweep. 6) **Compare variance against the full-model baseline** (from T022) to ensure robustness. **Deliverable**: Save to `artifacts/hyperparameter_sensitivity_report.csv`. **DEPENDS ON**: T022, T016.
- [X] T027 [US3] Implement `code/analysis/sensitivity.py` to aggregate results from T036 and T037 and generate the sensitivity report. **Logic**: Aggregate R² and MAE from T036's data-threshold evaluations and T037's hyperparameter sweeps. Report the variance in performance as a function of the descriptor threshold and hyperparameter values. **Constraint**: Do NOT modify descriptor magnitudes; only filter molecules or re-train on subsets. **DEPENDS ON**: T036, T037.
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
- [ ] T033A [P] Execute full pipeline integration test on a small subset of rows. **Deliverable**: Raw execution logs. **DEPENDS ON**: T016, T022.
- [ ] T033B [P] Validate exit codes and artifact existence from T033A. **Deliverable**: Validation status. **DEPENDS ON**: T033A.
- [ ] T033C [P] Generate `artifacts/integration_test_report.md` based on T033A/B results. **Logic**: If T033A/B pass, document success. If T033A/B fail (exit code != 0 or artifacts missing), document failure with error logs. **DEPENDS ON**: T033A, T033B.
- [ ] T031B [P] Finalize `quickstart.md` in `specs/001-predict-sn1-rate-constants/`. **Dependencies**: T033C. **Logic**: Update `quickstart.md` with actual paths, command examples, and verified output descriptions from T033C. **Fallback**: If T033C fails or produces no report, update `quickstart.md` based on manual verification of code paths and standard defaults. **DEPENDS ON**: T033C.
- [ ] T034 [P] Validate `quickstart.md` against actual execution. **Dependencies**: T031B. **Logic**: 1) If T033C succeeded, validate `quickstart.md` against T033C's execution evidence. 2) If T033C failed and T031B used the fallback, validate `quickstart.md` against the manual verification evidence generated by T031B's fallback. **Note**: This ensures T034 always has evidence to validate against, breaking the circular dependency. **DEPENDS ON**: T031B, T033C (or T031B fallback evidence).

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
- **Revision Note 3 (R2)**: T015, T016, T022, T023, T030, T033, T034 added to ensure strict data flow and artifact validation. T015 now explicitly aggregates logs from T012 and T013 before generating the exclusion report. T022 and T030 ensure schema validation and artifact generation are explicit steps. T033 and T034 break the circular dependency on T036 for documentation validation.
- **Revision Note 4 (R3 - Corrected)**: T015 split into T015A/B/C for executability. T016 added [deferred] success rate check. T023 made required. T035 fixed to re-train from scratch (no T022 dependency). T037 added for hyperparameter sensitivity with stratified sampling. T014 clarified stratification baseline. T034 updated to handle fallback scenarios.
- **Revision Note 5 (R4 - Final)**: T035 updated to explicitly require re-training and remove stale comments. T027 updated to aggregate both data and hyperparameter sensitivity. T033/T031/T034 chain clarified for linear execution. T035 moved to Phase 4.5 for parallel execution with T022. T036 updated to sweep descriptor thresholds instead of steric filtering. T029 updated to use ablation (zeroing) instead of mean-setting. T012 updated to remove T013 dependency.
- **Revision Note 6 (R5 - Corrected)**: T035 redefined to use shallow model on small subset for SC-004 consistency check. T029 redefined to use node-level graph masking. T036 range updated to dynamic percentiles. T037 configurations explicitly defined. T012 formula clarified. T030 SC-006 reference removed.