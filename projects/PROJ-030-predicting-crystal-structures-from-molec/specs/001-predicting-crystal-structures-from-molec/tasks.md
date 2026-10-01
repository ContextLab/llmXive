# Tasks: Predicting Crystal Structures from Molecular Fingerprints

**Input**: Design documents from `/specs/001-predict-crystal-structures/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan (`projects/PROJ-030-predicting-crystal-structures-from-molec/`)
- [X] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt`
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools in `code/.pre-commit-config.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup configuration management in `code/config.py` (paths, seeds, hyperparameters)
- [X] T005 [P] Implement logging infrastructure with structured JSON output to `logs/`
- [X] T006 Create base data models (`MoleculeRecord`, `ModelMetrics`, `FeatureImportance`) in `code/ingestion/models.py`
- [X] T007 [P] Implement `code/utils/error_handlers.py` to catch `MemoryError` and `DownloadError` explicitly (no synthetic fallbacks) and add unit test `tests/unit/test_error_handling.py::test_catches_memory_error`
- [X] T008 [P] Create `code/.env.example` and implement `code/validate_env.py` to verify `HF_TOKEN` and cache paths are set before execution
- [X] T008b [P] Implement Reference-Validator integration in `code/ingestion/validate_source.py` to verify the HuggingFace dataset citation against the primary source before processing (Constitution Principle II compliance)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Feature Extraction (Priority: P1) 🎯 MVP

**Goal**: Download filtered COD organic subset, parse CIFs, extract SMILES, generate ECFP4 fingerprints, and handle polymorphism by treating (SMILES, Space Group) as distinct samples.

**Independent Test**: Run the ingestion pipeline on a small sample and verify the output CSV contains non-null SMILES, bit fingerprints, lattice parameters, and space groups for every row.

### Implementation for User Story 1

- [X] T009 [US1] Implement `code/ingestion/load_cod.py` to stream the `crystallography-open-database/organic` dataset from HuggingFace, enforcing the <500MB organic filter and raising an error if the source is unreachable (no synthetic fallback)
- [X] T010 [US1] Implement `code/ingestion/parse_cif.py` to parse downloaded CIF files using `pycifrw` and `openbabel`, extracting canonical SMILES and lattice parameters, while skipping malformed files with detailed logging
- [X] T011 [US1] Implement `code/ingestion/fingerprint.py` to generate ECFP4 fingerprints using `rdkit`, using chunked streaming to handle memory limits; if a molecule is too large to process, log the exclusion count to `data/processing/exclusion_log.json` rather than silently dropping data (Constitution Principle III)
- [X] T012 [US1] Implement polymorphism handling logic in `code/ingestion/dataset_builder.py` to treat each unique (SMILES, Space Group) pair as a distinct row, producing the intermediate artifact `data/processed/polymorphic_dataset.csv`
- [X] T013 [US1] Create the main pipeline script `code/ingestion/run_pipeline.py` that orchestrates download (T009), parsing (T010), fingerprinting (T011), and dataset building (T012), outputting `data/processed/crystal_dataset.csv`
- [X] T014 [US1] Add validation step to verify that `data/processed/crystal_dataset.csv` has no nulls in key columns and that fingerprint bit counts are of a fixed, high-dimensional magnitude, outputting `data/validation/fingerprint_check.json` with pass/fail status

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Validation (Priority: P2)

**Goal**: Train Random Forest/Gradient Boosting classifiers and Ridge Regression models using scaffold-based splits, handling class imbalance, enforcing time limits, and verifying baselines.

**Independent Test**: Execute training on the prepared dataset and verify output metrics (Accuracy, F1, R², MAE) with zero scaffold overlap between train/test sets.

### Implementation for User Story 2

- [X] T006b [US2] [Dep: T013] Implement `code/analysis/power.py` to calculate target sample size (Cohen's w=0.15) using the actual dataset size from T013, write the result to `data/power_analysis.json`, and then update `code/config.py` with the derived power metrics (removed [P] tag as this is sequential)
- [X] T015a [US2] [Dep: T013] Implement `code/modeling/group_rare.py` to group rare space groups (<20 samples) into an 'Other' category in `data/processed/crystal_dataset.csv`, outputting `data/processed/grouped_dataset.csv`
- [X] T015b [US2] [Dep: T015a] Implement `code/modeling/split.py` to perform a scaffold-based split using the Bemis-Murcko algorithm on `data/processed/grouped_dataset.csv`, outputting `data/processed/split_indices.json`
- [X] T015c [US2] [Dep: T015b] Implement `code/modeling/validate_split.py` to verify zero scaffold overlap between train/test sets, outputting `data/validation/scaffold_overlap_report.json`
- [X] T015d [US2] [Dep: T015c] Implement `code/modeling/validate_split.py` to generate the 'zero scaffold overlap' report artifact required by SC-002, ensuring it acts as a hard pass/fail gate before training (T016). If overlap > 0, exit with code 1.
- [X] T018a [US2] [Dep: T015d] Implement `code/modeling/timeout_handler.py` to configure per-model time limits and tree reduction strategy (e.g., max_trees parameter) based on a fixed time budget, writing configuration to `code/config.py` and logging the plan to `data/results/timeout_plan.log`. This task runs BEFORE training to set static limits.
- [X] T016 [US2] [Dep: T015d, T018a] Implement `code/modeling/train.py` to train Random Forest, Gradient Boosting, and Ridge Regression models using `data/processed/split_indices.json` and the timeout configuration from T018a, outputting `data/models/rf_model.pkl`, `data/models/gb_model.pkl`, and `data/models/ridge_model.pkl`
- [X] T017 [US2] [Dep: T016] Implement Molecular Weight baseline regression logic in `code/modeling/train.py` specifically for the 'Lattice Parameters' (regression) target and output `data/results/mw_baseline_metrics.json`
- [X] T017b [US2] [Dep: T016] Implement majority-class baseline calculation in `code/modeling/train.py` specifically for the 'Space Group' (classification) target, outputting `data/results/majority_class_baseline_metrics.json`
- [X] T017a [US2] [Dep: T006b] Implement `code/analysis/define_lift.py` to read power analysis results from `data/power_analysis.json` and write the threshold value (or 'DEFERRED') to `code/config.py`
- [X] T017c [US2] [Dep: T017, T017b, T017a] Implement `code/modeling/verify_success.py` to read `data/results/majority_class_baseline_metrics.json` and `data/results/model_metrics.json`, calculate `Accuracy > Majority Baseline + [config.lift_threshold]`, output the specific 'lift' value, and handle the '[deferred]' state to prevent silent acceptance, outputting `data/validation/success_criterion_check.json`
- [X] T019 [US2] [Dep: T016] Calculate classification metrics (Accuracy, Macro-F1) and regression metrics (R-squared, MAE) in `code/modeling/evaluate.py`, comparing against baselines
- [X] T019d [US2] [Dep: T016] Calculate Top-K Accuracy (K=5) and Prediction Entropy as primary metrics to handle polymorphism ambiguity, outputting `data/results/polymorphism_metrics.json`
- [X] T019c [US2] [Dep: T019, T019d] Generate the final metrics file `data/results/model_metrics.json` containing all performance metrics, baseline comparisons, and success criterion verifications

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance and Interpretability Analysis (Priority: P3)

**Goal**: Analyze trained models using permutation importance and SHAP to identify predictive molecular substructures, handling bit collisions with ambiguity notes.

**Independent Test**: Run the analysis script and verify a ranked list of top fingerprint bits with representative substructure annotations and collision flags is generated.

### Implementation for User Story 3

- [X] T022 [US3] [Dep: T016] Compute and save permutation importance for the trained Random Forest model (`data/models/rf_model.pkl`) in `code/analysis/interpret.py`, outputting `data/results/permutation_importance.json`
- [X] T023 [US3] [Dep: T016] Compute and save SHAP values for the Random Forest model (Space Group) and Ridge Regression model (Lattice Parameters) in `code/analysis/interpret.py` to identify top bits for both targets, outputting `data/results/shap_analysis.json`
- [X] T024 [US3] [Dep: T023] Implement substructure mapping logic in `code/analysis/interpret.py` to identify representative chemical substructures for top bits, explicitly flagging bits with multiple possible mappings (collisions)
- [X] T025 [US3] [Dep: T024] Implement `code/analysis/report_generator.py` to generate the final interpretability report in `data/results/feature_importance_report.md` listing the top bits, their scores, substructures, and collision warnings, explicitly enforcing sorting by importance
- [X] T026 [US3] [Dep: T025] Implement `code/analysis/validate_report.py` to ensure the report contains at least 20 annotated bits sorted by importance, outputting `data/validation/report_check.json`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T027a [P] Update `README.md` with pipeline usage instructions and project overview
- [X] T027b [P] Add comprehensive docstrings to all `code/ingestion/*.py` and `code/modeling/*.py` files
- [X] T028a [P] Run `ruff --fix` on the entire codebase and commit changes
- [X] T028b [P] Refactor `code/ingestion/fingerprint.py` to use streaming generator for memory efficiency
- [X] T029a [P] Optimize fingerprint generation to reduce memory usage by [deferred] via batch processing
- [X] T029b [P] Profile and optimize data loading pipeline for streaming efficiency
- [X] T030 [P] Execute the full end-to-end pipeline (ingestion + training + analysis) on the target GitHub Actions runner and log the total duration to `data/results/pipeline_timing.log` to verify SC-004 (6-hour limit)
- [X] T030a [Dep: T030] Implement explicit build failure mechanism: if T030 detects a timeout, mark the project as 'failed' and exit with code 1 to enforce SC-004 as a hard pass/fail gate
- [X] T031 Final review of `state/projects/PROJ-030-predicting-crystal-structures-from-molec.yaml` for artifact hashes
- [X] T006c [P] [Dep: T006b] Invoke the Advancement-Evaluator Agent to update `state/projects/PROJ-030-predicting-crystal-structures-from-molec.yaml` with the content hash of the power analysis output and update `updated_at` timestamp (Constitution Principle V compliance)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **US1 (Phase 3)**: No dependencies on other stories.
 - **US2 (Phase 4)**: **Strictly depends on US1 completion** (T013). T015a explicitly requires T013 output.
 - **US3 (Phase 5)**: **Strictly depends on US2 completion** (T016). T022/T023 require model artifacts.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2).
- **User Story 2 (P2)**: Can start **only after** T013 (US1) is complete.
- **User Story 3 (P3)**: Can start **only after** T016 (US2) is complete.

### Within Each User Story

- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- T009, T010, T011, T012 can run in parallel within US1 (if data flow allows)
- T017, T017b can run in parallel within US2 (after T016)
- T022, T023 can run in parallel within US3 (after T016)

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
 - Developer B: User Story 2 (waits for US1)
 - Developer C: User Story 3 (waits for US2)
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
- **Critical Constraint**: Data loading tasks MUST fail loudly on real data fetch errors; no synthetic fallbacks allowed.
- **Critical Constraint**: Polymorphism must be handled by treating (SMILES, Space Group) as distinct rows.
- **Critical Constraint**: Scaffold splits must be verified to have zero overlap before training.
- **Critical Constraint**: Timeout enforcement MUST reduce tree count to a manageable, optimized quantity (no data sampling); NO hardcoded '100' trees.
- **Critical Constraint**: Majority-class baseline MUST be calculated and compared for classification (SC-001), including a [deferred] lift verification.
- **Critical Constraint**: Full pipeline timing MUST be logged to verify 6-hour limit (SC-004); explicit failure mechanism required.
- **Critical Constraint**: Feature importance list MUST be ranked by score (SC-003).
- **Critical Constraint**: Power Analysis MUST be documented as a planning artifact (Plan) and executed after data ingestion.
- **Critical Constraint**: Rare space groups MUST be grouped into 'Other' PRIOR to splitting (Plan/SC-005).
- **Critical Constraint**: Reference-Validator MUST verify the dataset citation before processing (Constitution Principle II).
- **Critical Constraint**: Data exclusion (if any) must be formally logged in a derivation file (Constitution Principle III).
- **Critical Constraint**: State file updates MUST be performed by the Advancement-Evaluator Agent (Constitution Principle V).