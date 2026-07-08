# Tasks: Assessing the Predictive Power of Machine Learning for Organic Reaction Outcomes

**Input**: Design documents from `/specs/001-assess-ml-predictive-power/`
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

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a Create `code/`, `data/raw/`, `data/processed/`, `data/results/`, `tests/` directories
- [ ] T001b Create `code/config.py`, `code/__init__.py`, `code/requirements.txt`, `tests/__init__.py`
- [X] T002 Initialize Python 3.11 project with `pandas`, `scikit-learn`, `rdkit`, `pyyaml`, `pytest` in `code/requirements.txt`
- [ ] T003 [P] Configure linting (`ruff`) and formatting (`black`) tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/config.py` with pinned random seeds, path constants, and hyperparameter grids for RF/SVM
- [ ] T005 [P] Implement `code/utils/io.py` for robust Parquet/CSV loading, checksumming, and batch processing to manage memory < 7GB
- [~] T006 [P] Create `code/preprocessing/__init__.py` and `code/modeling/__init__.py` package structures
- [~] T007 Implement data schema validation contracts in `specs/001-assess-ml-predictive-power/contracts/dataset.schema.yaml`
- [~] T008 Implement output schema validation contracts in `specs/001-assess-ml-predictive-power/contracts/output.schema.yaml`
- [~] T009 Create `data/raw/.gitkeep` and `data/processed/.gitkeep` directories to ensure directory structure exists

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Feature Extraction Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw USPTO data, sanitize structures, and generate ECFP4/MACCS fingerprints for a clean, analysis-ready dataset.

**Independent Test**: Run the preprocessing script on a small subset and verify the output CSV contains valid SMILES, non-null fingerprint vectors, and correct yield values without training a model.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T011 [P] [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py`
- [~] T012 [P] [US1] Unit test for salt removal and SMILES standardization in `tests/unit/test_sanitize.py`
- [~] T013 [P] [US1] Unit test for fingerprint dimensionality (ECFP4=2048, MACCS=167) in `tests/unit/test_fingerprints.py`

### Implementation for User Story 1

- [~] T019 [US1] Implement `code/preprocessing/download.py`: Download USPTO dataset from canonical source DOI ``, verify checksum against canonical manifest, and perform Constitution Principle II (Verified Accuracy) gate check before saving to `data/raw/uspto_raw.parquet` (FR-001, Constitution II) <!-- FAILED: unspecified -->
- [~] T014 [US1] Implement `code/preprocessing/sanitize.py`: Load USPTO parquet from `data/raw/uspto_raw.parquet`, remove salts, standardize reactions using RDKit (FR-002)
- [~] T015 [US1] Implement `code/preprocessing/sanitize.py`: Handle yield parsing (ranges vs. single values) and exclude malformed entries with logging (Edge Cases)
- [~] T016 [US1] Implement `code/preprocessing/fingerprints.py`: Generate ECFP and MACCS vectors for all reactants/reagents (FR-003)
- [ ] T017 [US1] Implement `code/preprocessing/ingest.py`: Orchestrate sanitization, fingerprinting, and save to `data/processed/cleaned_reactions.parquet` (FR-001)
- [ ] T018 [US1] Add logging for exclusion reasons and data quality metrics (SC-005) in `code/preprocessing/ingest.py` and generate `data/results/data_quality_report.json`
- [ ] T010 [US1] Implement `code/preprocessing/scaffold.py`: Generate Murcko scaffold grouping keys from sanitized reactions in `data/processed/cleaned_reactions.parquet` using `rdkit.Chem.Scaffolds` to produce `data/processed/scaffold_groups.parquet` (FR-004, Constitution VI)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (clean dataset generated)

---

## Phase 4: User Story 2 - Model Training and Hyperparameter Optimization (Priority: P2)

**Goal**: Train Random Forest and SVM regressors with grid search/CV to identify optimal configurations under CPU constraints.

**Independent Test**: Run grid search on a small fixed validation subset and verify best hyperparameters are selected and R² is measurable.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T020 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output.py`
- [ ] T021 [P] [US2] Integration test for training pipeline on a subset in `tests/integration/test_training_pipeline.py`

### Implementation for User Story 2

- [ ] T022 [US2] Implement `code/modeling/split.py`: Implement **Stratified-by-Class + Intra-Class Scaffold Grouping** split using scaffold keys from T010 to prevent leakage (FR-004, Constitution VI); output `data/processed/split_indices.parquet` containing train/val/test indices
- [ ] T023 [US2] Implement `code/modeling/split.py`: Extract the **held-out validation set** from `data/processed/split_indices.parquet` generated by T022 to create `data/processed/validation_set.parquet` specifically for SC-003 substructure frequency checks (this is the same set used for hyperparameter tuning, ensuring 'held-out' status) (SC-003)
- [ ] T024 [US2] Implement `code/modeling/train.py`: Train Random Forest with grid search (k-fold CV) for `n_estimators` and `max_depth` (FR-005)
- [ ] T025 [US2] Implement `code/modeling/train.py`: Train SVM with grid search for `C` and `kernel` (linear/RBF) (FR-005)
- [ ] T026 [US2] Implement `code/modeling/evaluate.py`: Evaluate best models on held-out test set; report R², RMSE, MAE (FR-006)
- [ ] T027 [US2] Ensure all training operations are CPU-only and batched to respect ≤ 7GB RAM limit (FR-009, FR-010)
- [ ] T028 [US2] Save best model artifacts and hyperparameters to `data/results/best_models/`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (models trained and validated)

---

## Phase 5: User Story 3 - Generalization and Feature Importance Analysis (Priority: P3)

**Goal**: Evaluate generalization across reaction classes and identify predictive substructures.

**Independent Test**: Run evaluation script on test set to generate per-class metrics and a ranked list of predictive bits/substructures.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T029 [P] [US3] Contract test for feature importance report schema in `tests/contract/test_importance_report.py`
- [ ] T030 [P] [US3] Integration test for generalization analysis in `tests/integration/test_generalization.py`

### Implementation for User Story 3

- [ ] T031 [US3] Implement `code/modeling/evaluate.py`: Compute per-reaction-class R² and RMSE metrics (FR-007, SC-002)
- [ ] T032 [US3] Implement `code/modeling/evaluate.py`: Compute permutation importance for Random Forest (FR-008)
- [ ] T033 [US3] Implement `code/modeling/evaluate.py`: Map top fingerprint bits to molecular substructures and **reaction centers** using `rdkit.Chem.rdFMCS` to identify the Maximum Common Substructure between reactants and products; the reaction center is defined as the atoms/bonds in reactants/products NOT present in the MCS. Aggregate importance across bits mapping to the same substructure (FR-008, SC-003)
- [ ] T034 [US3] Generate final `data/results/final_report.json` containing all metrics, split ratios, and feature importance (FR-006, FR-007, FR-008)
- [ ] T035 [US3] Validate that all metrics meet Success Criteria (SC-001: R² ≥ 0.40, SC-002: Gap ≤ 0.10, SC-003: Substructure frequency >80% in the held-out validation set from T023, SC-005: Exclusion fraction measured from `data/results/data_quality_report.json`). Explicitly calculate the percentage of high-yield reactions in the validation set containing the top substructures and write this value to `data/results/final_report.json` under key `sc003_substructure_frequency` (FR-006, FR-007, FR-008, SC-001, SC-002, SC-003, SC-005)

**Checkpoint**: All user stories should now be independently functional and results aggregated

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T036 [P] Update `README.md` with quickstart instructions and dependency installation
- [ ] T037 Code cleanup: Run `ruff check --fix` and `black` on `code/` directory
- [ ] T038 Performance optimization: Ensure full pipeline runs within 6 hours on 2-CPU runner
- [ ] T039 [P] Run full test suite (`pytest`) to ensure all contract and unit tests pass
- [ ] T040 Run `quickstart.md` validation to ensure reproducibility from scratch

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on clean data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on trained models from US2

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
Task: "Contract test for dataset schema validation in tests/contract/test_dataset_schema.py"
Task: "Unit test for salt removal in tests/unit/test_sanitize.py"

# Launch all models for User Story 1 together:
Task: "Implement sanitize.py in code/preprocessing/sanitize.py"
Task: "Implement fingerprints.py in code/preprocessing/fingerprints.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (Clean dataset generated)
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
 - Developer B: User Story 2 (Modeling)
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
- **Constraint Reminder**: All tasks must run on free-tier CI (CPU, 7GB RAM, no GPU). Use `scikit-learn` and `rdkit` only.