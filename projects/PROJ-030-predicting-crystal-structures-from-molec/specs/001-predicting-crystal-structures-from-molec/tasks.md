# Tasks: Predicting Crystal Structures from Molecular Fingerprints

**Input**: Design documents from `/specs/001-predict-crystal-structures/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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
- [ ] T006b [P] Implement Power Analysis in `docs/power_analysis.md` calculating minimum sample size (500 scaffolds) based on Cohen's w=0.15, alpha=0.05, beta=0.20, and document the justification for the 500-scaffold threshold (Plan requirement)
- [ ] T007 Setup error handling framework to catch `MemoryError` and `DownloadError` explicitly (no synthetic fallbacks)
- [ ] T008 Configure environment variables for HuggingFace token and cache paths

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Feature Extraction (Priority: P1) 🎯 MVP

**Goal**: Download filtered COD organic subset, parse CIFs, extract SMILES, generate ECFP4 fingerprints, and handle polymorphism by treating (SMILES, Space Group) as distinct samples.

**Independent Test**: Run the ingestion pipeline on a small sample and verify the output CSV contains non-null SMILES, bit fingerprints, lattice parameters, and space groups for every row.

### Implementation for User Story 1

- [ ] T009 [US1] Implement `code/ingestion/load_cod.py` to stream the `crystallography-open-database/organic` dataset from HuggingFace, enforcing the <500MB organic filter and raising an error if the source is unreachable (no synthetic fallback)
- [ ] T010 [US1] Implement `code/ingestion/parse_cif.py` to parse downloaded CIF files using `pycifrw` and `openbabel`, extracting canonical SMILES and lattice parameters, while skipping malformed files with detailed logging
- [ ] T011 [US1] Implement `code/ingestion/fingerprint.py` to generate ECFP4 fingerprints using `rdkit`, handling `MemoryError` by logging and excluding large molecules rather than crashing
- [ ] T012 [US1] Implement polymorphism handling logic in `code/ingestion/dataset_builder.py` to treat each unique (SMILES, Space Group) pair as a distinct row, producing the intermediate artifact `data/processed/polymorphic_dataset.csv`
- [ ] T013 [US1] Create the main pipeline script `code/ingestion/run_pipeline.py` that orchestrates download, parsing, fingerprinting, and outputs `data/processed/crystal_dataset.csv` (consumes `data/processed/polymorphic_dataset.csv`)
- [ ] T014 [US1] Add validation step to verify that `data/processed/crystal_dataset.csv` has no nulls in key columns and that fingerprint bit counts are of a fixed, high-dimensional magnitude

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Validation (Priority: P2)

**Goal**: Train Random Forest/Gradient Boosting classifiers and Ridge Regression models using scaffold-based splits, handling class imbalance, enforcing time limits, and verifying baselines.

**Independent Test**: Execute training on the prepared dataset and verify output metrics (Accuracy, F1, R², MAE) with zero scaffold overlap between train/test sets.

### Implementation for User Story 2

- [ ] T015 [US2] Implement `code/modeling/split.py` to perform Bemis-Murcko scaffold-based splitting, grouping rare space groups (<20 samples) into an 'Other' category prior to splitting, producing `data/processed/split_indices.json`
- [ ] T016 [US2] Implement `code/modeling/train.py` to train Random Forest and Gradient Boosting classifiers for space group prediction and Ridge Regression for lattice volume, **consuming `data/processed/split_indices.json` from T015** and outputting trained model artifacts
- [ ] T017 [US2] Implement baseline training in `code/modeling/train.py` to train a Molecular Weight baseline regressor for volume prediction, outputting `data/results/mw_baseline_metrics.json`
- [ ] T017b [US2] Implement majority-class baseline calculation in `code/modeling/train.py` to predict the most frequent space group for all test samples, outputting `data/results/majority_class_baseline_metrics.json` for SC-001 verification
- [ ] T018 [US2] Implement timeout enforcement in `code/modeling/train.py` to **automatically reduce the dataset to a manageable subset of random samples OR limit tree depth to a predefined maximum if runtime exceeds a practical threshold**, ensuring completion within the GitHub Actions time limit (FR-007)
- [ ] T019 [US2] Implement `code/modeling/evaluate.py` to calculate Accuracy, Macro-F1, R-squared, and MAE, **comparing model performance against both the MW baseline (T017) and the majority-class baseline (T017b)** to verify SC-001 ([deferred] lift) and SC-002
- [ ] T020 [US2] Add verification step to ensure zero shared Bemis-Murcko scaffolds between train and test sets in `code/modeling/validate_split.py`
- [ ] T021 [US2] Generate `data/results/model_metrics.json` containing all performance metrics and baseline comparisons

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance and Interpretability Analysis (Priority: P3)

**Goal**: Analyze trained models using permutation importance and SHAP to identify predictive molecular substructures, handling bit collisions with ambiguity notes.

**Independent Test**: Run the analysis script and verify a ranked list of top fingerprint bits with representative substructure annotations and collision flags is generated.

### Implementation for User Story 3

- [ ] T022 [US3] Implement `code/analysis/interpret.py` to compute permutation importance for the **trained Random Forest model artifact from T016**
- [ ] T023 [US3] Implement SHAP value calculation in `code/analysis/interpret.py` using the `shap` library to identify top predictive bits, **consuming the trained model artifacts from T016/T017**
- [ ] T024 [US3] Implement substructure mapping logic in `code/analysis/interpret.py` to identify representative chemical substructures for top bits, explicitly flagging bits with multiple possible mappings (collisions)
- [ ] T025 [US3] Generate the final interpretability report in `data/results/feature_importance_report.md` listing the top bits, their scores, substructures, and collision warnings
- [ ] T026 [US3] Add validation to ensure the report **contains at least 20 annotated bits AND that the list is sorted in descending order by importance score** (permutation/SHAP) as per SC-003

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T027 [P] Documentation updates in `docs/` and `README.md`
- [ ] T028 Code cleanup and refactoring based on linting feedback
- [ ] T029 Performance optimization for streaming and fingerprint generation
- [ ] T030 [P] **Execute the full end-to-end pipeline (ingestion + training + analysis) on the target GitHub Actions runner and log the total duration to `data/results/pipeline_timing.log`** to verify SC-004 (6-hour limit)
- [ ] T031 Final review of `state/projects/PROJ-030-predicting-crystal-structures-from-molec.yaml` for artifact hashes

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data output from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on model output from US2

### Within Each User Story

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
# Launch all models for User Story 1 together:
Task: "Implement load_cod.py"
Task: "Implement parse_cif.py"
Task: "Implement fingerprint.py"
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
- **Critical Constraint**: Data loading tasks MUST fail loudly on real data fetch errors; no synthetic fallbacks allowed.
- **Critical Constraint**: Polymorphism must be handled by treating (SMILES, Space Group) as distinct rows.
- **Critical Constraint**: Scaffold splits must be verified to have zero overlap before training.
- **Critical Constraint**: Timeout enforcement MUST reduce dataset to a manageable subset OR limit trees to a manageable count (FR-007).
- **Critical Constraint**: Majority-class baseline MUST be calculated and compared for classification (SC-001).
- **Critical Constraint**: Full pipeline timing MUST be logged to verify 6-hour limit (SC-004).
- **Critical Constraint**: Feature importance list MUST be ranked by score (SC-003).
- **Critical Constraint**: Power Analysis MUST be documented to justify sample size (Plan).