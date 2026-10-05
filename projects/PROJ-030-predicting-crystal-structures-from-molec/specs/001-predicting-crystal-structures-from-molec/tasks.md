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

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-030-predicting-crystal-structures-from-molec/`)
- [ ] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools in `code/.pre-commit-config.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup configuration management in `code/config.py` (paths, seeds, hyperparameters)
- [ ] T005 [P] Implement logging infrastructure with structured JSON output to `logs/`
- [ ] T006 Create base data models (`MoleculeRecord`, `ModelMetrics`, `FeatureImportance`) in `code/ingestion/models.py`
- [ ] T007 [P] Implement `code/utils/error_handlers.py` to catch `MemoryError` and `DownloadError` explicitly (no synthetic fallbacks) and add unit test `tests/unit/test_error_handling.py::test_catches_memory_error`
- [ ] T008 [P] Create `code/.env.example` and implement `code/validate_env.py` to verify `HF_TOKEN` and cache paths are set before execution
- [ ] T008b [P] Implement Reference-Validator integration in `code/ingestion/validate_source.py` to verify the HuggingFace dataset citation against the primary source before processing (Constitution Principle II compliance)
- [ ] T001b [P] Implement directory creation script `code/utils/init_dirs.py` to create all required data directories (`data/processed`, `data/results`, `data/validation`, `data/models`, `logs`) and write a confirmation log to `data/.initialized`. **Dependency**: Must run before any task that writes to these directories (e.g., T036, T009). **Constraint**: Explicitly creates the full directory tree for a CPU-only environment; no CUDA-specific cache directories are created.
- [ ] T036 [P] [Dep: T001b] Implement `code/validate_env.py` to verify the environment is CPU-only per Plan constraints; write `training_device="cpu"` to `data/results/runtime_config.json`. **Constraint**: This task strictly enforces CPU-only execution as per Plan constraints; it does NOT enable GPU offloading or detect GPU drivers.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Feature Extraction (Priority: P1) 🎯 MVP

**Goal**: Download filtered COD organic subset, parse CIFs, extract SMILES, generate ECFP4 fingerprints, and handle polymorphism by treating (SMILES, Space Group) as distinct samples.

**Independent Test**: Run the ingestion pipeline on a small sample and verify the output CSV contains non-null SMILES, bit fingerprints, lattice parameters, and space groups for every row.

### Implementation for User Story 1

- [ ] T009 [US1] [Dep: T008b] Implement `code/ingestion/load_cod.py` to **stream** the `crystallography-open-database/organic` dataset from HuggingFace (`streaming=True`), enforcing the <500MB organic filter and raising an error if the source is unreachable (no synthetic fallback). **Hard Gate**: The script must abort if Tb (Reference-Validator) has not successfully validated the source. The script must process data in chunks to stay within 7GB RAM limits.
- [ ] T010 [US1] [Dep: T009] Implement `code/ingestion/parse_cif.py` to parse downloaded CIF files using `pycifrw` and `openbabel`, extracting canonical SMILES and lattice parameters, while skipping malformed files with detailed logging
- [ ] T011 [US1] [Dep: T010] Implement `code/ingestion/fingerprint.py` to generate ECFP4 fingerprints using `rdkit`, using chunked streaming to handle memory limits; if a molecule is too large to process, log the exclusion count to `data/processing/exclusion_log.json` rather than silently dropping data (Constitution Principle III)
- [ ] T012 [US1] [Dep: T011] Implement polymorphism handling logic in `code/ingestion/dataset_builder.py` to treat each unique (SMILES, Space Group) pair as a distinct row, producing the intermediate artifact `data/processed/polymorphic_dataset.csv`
- [ ] T013 [US1] [Dep: T012] Create the main pipeline script `code/ingestion/run_pipeline.py` that orchestrates download (T009), parsing (T010), fingerprinting (T011), and dataset building (T012), outputting `data/processed/crystal_dataset.csv`
- [ ] T014 [US1] [Dep: T013] Add validation step to verify that `data/processed/crystal_dataset.csv` has no nulls in key columns and that fingerprint bit counts are of a fixed, high-dimensional magnitude, outputting `data/validation/fingerprint_check.json` with pass/fail status

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Validation (Priority: P2)

**Goal**: Train Random Forest/Gradient Boosting classifiers and Ridge Regression models using scaffold-based splits, handling class imbalance, enforcing time limits, and verifying baselines.

**Independent Test**: Execute training on the prepared dataset and verify output metrics (Accuracy, F1, R², MAE) with zero scaffold overlap between train/test sets.

### Implementation for User Story 2

- [ ] T006b-exec [US2] [Dep: T013] Implement `code/analysis/power.py` to calculate target sample size (Cohen's w=0.15) using the actual dataset size from T013, write the result to `data/results/power_analysis.json`, and DO NOT modify static `code/config.py`. The power metrics are loaded dynamically at runtime. **Constraint**: This task must generate the `power_analysis.json` artifact as a distinct, verifiable step before T017a-exec.
- [ ] T015a-exec [US2] [Dep: T013] Implement `code/modeling/group_rare.py` to read `data/processed/crystal_dataset.csv`, group rare space groups (<20 samples) into an 'Other' category, and write the result to `data/processed/grouped_dataset.csv`. **Validation**: If input is missing or invalid, raise a clear error. **Retry Logic**: Internal to script (re-fetch if missing), not a separate task.
- [ ] T015b-exec [US2] [Dep: T015a-exec] Implement `code/modeling/split.py` to perform a scaffold-based split using the Bemis-Murcko algorithm on `data/processed/grouped_dataset.csv`, outputting `data/processed/split_indices.json`
- [ ] T015c-exec [US2] [Dep: T015b-exec] Implement `code/modeling/validate_split.py` to verify zero scaffold overlap between train/test sets, generate `data/validation/scaffold_overlap_report.json`, and **exit with code 1** if overlap > 0 (Hard Gate for SC-002).
- [ ] T016-exec [US2] [Dep: T015c-exec] Implement `code/modeling/train.py` to train Random RF, GB, and Ridge models. **Integrated Logic**:
 - Read `data/results/runtime_config.json` for `training_device` (CPU only).
 - Implement **hard timeout enforcement** (6-hour limit) with a `signal` handler or `timeout` decorator. If timeout exceeded, log to `data/results/timeout_action.log` and exit with code 1.
 - Train models using `data/processed/split_indices.json`.
 - Output `data/models/rf_model.pkl`, `data/models/gb_model.pkl`, `data/models/ridge_model.pkl`.
- [ ] T017-exec [US2] [Dep: T016-exec] Implement `code/modeling/baseline_mw.py` to calculate Molecular Weight baseline regression for the 'Lattice Parameters' target and output `data/results/mw_baseline_metrics.json` as a standalone deliverable.
- [ ] T017b-exec [US2] [Dep: T016-exec] Implement majority-class baseline calculation in `code/modeling/baseline_majority.py` specifically for the 'Space Group' (classification) target, outputting `data/results/majority_class_baseline_metrics.json`.
- [ ] T017a-exec [US2] [Dep: T006b-exec] Implement `code/analysis/define_lift.py` to read `data/results/power_analysis.json` (wait for file existence and non-empty size) and calculate a **conservative lift threshold** (e.g., a small effect size over baseline based on Cohen's w) if empirical lift is unknown. Write this numeric threshold to `data/results/power_analysis_threshold.json`. **Constraint**: If empirical power analysis is inconclusive, use a conservative heuristic ([deferred] lift) and explicitly document this as a conservative estimate in the output JSON. **Do NOT output 'DEFERRED'**.
- [ ] T017c-exec [US2] [Dep: T017-exec, T017b-exec, T017a-exec, T019-exec] Implement `code/modeling/verify_success.py` to read `data/results/majority_class_baseline_metrics.json`, `data/results/model_metrics_partial.json` (to be used by T019), and `data/results/power_analysis_threshold.json`. Calculate `Accuracy > Majority Baseline + [threshold]`. **Fail explicitly** if lift is not met. Output `data/validation/success_criterion_check.json`.
- [ ] T019-exec [US2] [Dep: T016-exec] Calculate classification metrics (Accuracy, Macro-F1) and regression metrics (R-squared, MAE) in `code/modeling/evaluate.py`, comparing against baselines. Output `data/results/model_metrics_partial.json` (to be used by T017c).
- [ ] T019d-exec [US2] [Dep: T016-exec] Implement `code/modeling/polymorphism_metrics.py` to calculate Top-K Accuracy (K=5) and Prediction Entropy using `data/processed/split_indices.json` and trained models. **Integrated Logic**: Use predicted probability distribution to handle polymorphism. Output `data/results/polymorphism_metrics.json`. **Constraint**: This task must generate the `polymorphism_metrics.json` artifact as a distinct, high-priority output.
- [ ] T019c-exec [US2] [Dep: T019-exec, T019d-exec, T017c-exec] Implement `code/modeling/final_metrics.py` to generate the final metrics file `data/results/model_metrics.json` containing all performance metrics, baseline comparisons, and success criterion verifications.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance and Interpretability Analysis (Priority: P3)

**Goal**: Analyze trained models using permutation importance and SHAP to identify predictive molecular substructures, handling bit collisions with ambiguity notes.

**Independent Test**: Run the analysis script and verify a ranked list of top fingerprint bits with representative substructure annotations and collision flags is generated.

### Implementation for User Story 3

- [ ] T022-exec [US3] [Dep: T016-exec, T015c-exec] Compute and save permutation importance for the trained Random RF model (`data/models/rf_model.pkl`) in `code/analysis/interpret.py`, outputting `data/results/permutation_importance.json`.
- [ ] T023-exec [US3] [Dep: T016-exec] Compute and save SHAP values for the Random RF model (Space Group) and Ridge Regression model (Lattice Parameters) in `code/analysis/interpret.py` to identify top bits for both targets, outputting `data/results/shap_analysis.json`.
- [ ] T024-exec [US3] [Dep: T023-exec] Implement substructure mapping logic in `code/analysis/interpret.py` to identify representative chemical substructures for top bits. **Integrated Logic**: Explicitly use **RDKit's `GetMorganFingerprint`** and `rdkit.Chem.rdMolDescriptors` to map bits to subgraphs. Flag bits with multiple mappings (collisions) and report the *most frequent* substructure while listing alternatives.
- [ ] T025-exec [US3] [Dep: T024-exec] Implement `code/analysis/report_generator.py` to generate the final interpretability report in `data/results/feature_importance_report.md` listing the top bits, their scores, substructures, and collision warnings, explicitly enforcing sorting by importance and ensuring >= 20 annotated bits (SC-003).
- [ ] T026-exec [US3] [Dep: T025-exec] Implement `code/analysis/validate_report.py` to ensure the report contains at least 20 annotated bits sorted by importance, outputting `data/validation/report_check.json`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T027a [P] Update `README.md` with pipeline usage instructions and project overview
- [ ] T027b [P] Add comprehensive docstrings to all `code/ingestion/*.py` and `code/modeling/*.py` files
- [ ] T028a [P] Run `ruff --fix` on the entire codebase and commit changes
- [ ] T028b [P] Refactor `code/ingestion/fingerprint.py` to use streaming generator for memory efficiency
- [ ] T029a [P] Optimize fingerprint generation to reduce memory usage via batch processing (specify batch size in config)
- [ ] T029b [P] Profile and optimize data loading pipeline for streaming efficiency
- [ ] T030 [P] [Dep: T016-exec] Execute the full end-to-end pipeline (ingestion + training + analysis) on the target GitHub Actions runner and log the total duration to `data/results/pipeline_timing.log` to verify SC-004 (6-hour limit).
- [ ] T030a [Dep: T030] Implement explicit build failure mechanism: if T030 detects a timeout, mark the project as 'failed' and exit with code 1 to enforce SC-004 as a hard pass/fail gate.
- [ ] T031 Final review of `state/projects/PROJ-030-predicting-crystal-structures-from-molec.yaml` for artifact hashes
- [ ] T006c [P] [Dep: T006b-exec] Invoke the Advancement-Evaluator Agent to update `state/projects/PROJ-030-predicting-crystal-structures-from-molec.yaml` with the content hash of the power analysis output and update `updated_at` timestamp (Constitution Principle V compliance)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **US1 (Phase 3)**: No dependencies on other stories.
 - **US2 (Phase 4)**: **Strictly depends on US1 completion** (T013). T015a-exec explicitly requires T013 output.
 - **US3 (Phase 5)**: **Strictly depends on US2 completion** (T016-exec). T022-exec/T023-exec require model artifacts.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2).
- **User Story 2 (P2)**: Can start **only after** T013 (US1) is complete.
- **User Story 3 (P3)**: Can start **only after** T016-exec (US2) is complete.

### Within Each User Story

- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- T017-exec, T017b-exec can run in parallel within US2 (after T016-exec)
- T022-exec, T023-exec can run in parallel within US3 (after T016-exec)

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
- **Critical Constraint**: Power Analysis MUST be documented as a planning artifact (Plan) and executed after dataingestion.
- **Critical Constraint**: Rare space groups MUST be grouped into 'Other' PRIOR to splitting (Plan/SC-005).
- **Critical Constraint**: Reference-Validator MUST verify the dataset citation before processing (Constitution Principle II).
- **Critical Constraint**: Data exclusion (if any) must be formally logged in a derivation file (Constitution Principle III).
- **Critical Constraint**: State file updates MUST be performed by the Advancement-Evaluator Agent (Constitution Principle V).
- **Critical Constraint**: NO static `code/config.py` modification at runtime. All dynamic values go to `data/results/*.json`.
- **Critical Constraint**: T017a-exec MUST calculate a numeric threshold (no 'DEFERRED') to unblock T017c-exec.
- **Critical Constraint**: T036 MUST default to 'cpu' if GPU detection fails to prevent runtime crashes. (Note: Task updated to strictly enforce CPU-only per Plan).
- **Critical Constraint**: T015a-exec MUST regenerate T013 output if T015a fails to break circular dependencies. (Note: Removed circular dependency; retry logic internal to script).
- **Critical Constraint**: All tasks marked `[X]` in previous versions have been reset to `[ ]` (pending) to resolve contradictions with missing artifacts.
- **Critical Constraint**: T037 and T041 (GPU offload) have been removed to preserve Plan constraints (CPU-only).

---

## Phase O: Revision & Analysis Resolution (Post-Analysis)

**Purpose**: Address specific findings from the `/speckit.analyze` review cycle to ensure scientific validity and execution compliance.

**Goal**: Resolve flagged issues regarding data sampling, GPU offloading logic, and metric calculation precision.

- [ ] T038 [P] [US1] Add explicit chunk-size logging to `code/ingestion/load_cod.py` to record the exact number of rows processed per stream chunk in `data/processing/streaming_metrics.json` for reproducibility.
- [ ] T039 [P] [US2] Refactor `code/modeling/evaluate.py` to explicitly calculate and report the **standard error** for all metrics (Accuracy, F1, R²) alongside the point estimates to satisfy statistical rigor requirements.
- [ ] T040 [P] [US3] Implement `code/analysis/collision_resolver.py` to apply a deterministic tie-breaking rule (e.g., alphabetical substructure name) when multiple substructures map to the same fingerprint bit, ensuring the final report is strictly sorted and reproducible.