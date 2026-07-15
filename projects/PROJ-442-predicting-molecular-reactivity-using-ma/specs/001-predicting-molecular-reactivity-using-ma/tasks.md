# Tasks: Predicting Molecular Reactivity Using Machine Learning and Public Reaction Databases

**Input**: Design documents from `/specs/001-molecular-reactivity/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: {{claim:c_513b5f9f}} (Wikidata Q18615098, https://www.wikidata.org/wiki/Q18615098)

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

- [X] T001 Execute `scripts/setup_dirs.sh` (or Python equivalent) to create `data/raw/`, `data/processed/`, `data/models/`, `src/data/`, `src/modeling/`, `src/utils/`, `tests/unit/`, `tests/integration/`, `tests/contract/`, `scripts/`
- [X] T002 Initialize Python 3.10 project with `rdkit`, `xgboost`, `pandas`, `scikit-learn`, `pyarrow`, `requests` dependencies in `requirements.txt`
- [X] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Implement centralized logging setup in `src/utils/logging.py`
- [X] T006 [P] Implement state management system (create `src/utils/state_manager.py` and `scripts/update_state.py`) to handle `state/projects/PROJ-442-predicting-molecular-reactivity-using-ma.yaml` updates and artifact checksums
- [X] T007 Create base data schemas and validation helpers in `src/data/schemas.py` (ReactionRecord, FeatureVector, ModelResult)
- [ ] T008 Setup environment configuration management (load `config.yaml` from `src/modeling/config.yaml`)
- [ ] T009 Create `src/main.py` orchestration script to call `scripts/update_state.py` after major stages

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Reaction Class Filtering (Priority: P1) 🎯 MVP

**Goal**: Download USPTO subset, parse SMILES, filter into SN1, SN2, Diels-Alder classes, and handle malformed data.

**Independent Test**: Can be fully tested by executing the data ingestion script and verifying that the output CSV contains a single `reaction_type` column containing exactly three distinct values ("SN1", "SN2", "Diels-Alder") where present, and that the total row count is ≥ 90% of the input file row count.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for SMILES normalization and error logging in `tests/unit/test_ingestion.py`
- [ ] T011 [P] [US1] Unit test for reaction template matching logic in `tests/unit/test_templates.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `src/data/ingestion.py` to The USPTO-MIT subset is available at https://zenodo.org/record/3969375 [UNRESOLVED-CLAIM: c_25c15d06 — status=not_enough_info] and parse raw data
- [ ] T013c [US1] Define SMARTS patterns for SN1, SN2, and Diels-Alder in `src/modeling/config.yaml` (under `reaction_templates`) to ensure deterministic template matching. Explicit patterns: SN1 (e.g., `[C:1]([O:2])>>[C:1]+[O:2]-`), SN2 (e.g., `[C:1]([O:2])>>[C:1]=[O:2]` with backside attack logic), Diels-Alder (e.g., `[C:1]=[C:2].[C:3]=[C:4]>>[C:1]1[C:3][C:4][C:2]1`).
- [~] T013 [US1] Implement reaction template matching in `src/utils/chemistry.py` using patterns from `config.yaml` to classify reactions into SN1, SN2, Diels-Alder
- [~] T014 [US1] Implement filtering logic in `src/data/ingestion.py` to exclude non-matching rows, log malformed SMILES to error file, and strictly derive target variable: use `yield_pct` if present, otherwise fallback to `success_flag` (binary) as per Spec Assumptions (FR-004)
- [~] T015 [US1] Implement batch processing logic in `src/data/ingestion.py` to handle memory limits (process in chunks)
- [~] T016 [US1] Add logic to check sample size per class (<1,000) and log warning; explicitly physically remove those rows from the output CSV for classes with <1,000 samples to satisfy the Independent Test's distinct value requirement (FR-006)
- [~] T017 [US1] Save filtered dataset to `data/processed/filtered_reactions.csv` with checksum and provenance metadata
- [~] T018 [US1] Integrate logging and state update calls in `src/data/ingestion.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Feature Extraction and Model Training (Priority: P2)

**Goal**: Convert reactants to features (RDKit), apply dimensionality reduction, and train XGBoost on CPU within 30 mins.

**Independent Test**: Can be fully tested by running the training script ona sample of reaction records and verifying that the model outputs a prediction file with a Spearman correlation coefficient > 0.5 and that the (2408.08592, https://arxiv.org/abs/2408.08592).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T019 [P] [US2] Unit test for RDKit feature extraction (MW, atom counts, topological indices) in `tests/unit/test_features.py`
- [~] T020 [P] [US2] Unit test for dimensionality reduction pipeline (Variance Threshold + SelectKBest) in `tests/unit/test_features.py`

### Implementation for User Story 2

- [~] T021 [US2] Implement `src/data/preprocessing.py` to extract molecular weight, atom counts, bond types, and topological indices using RDKit
- [~] T022 [US2] Implement batch processing in `src/data/preprocessing.py` to handle memory constraints during feature extraction
- [~] T023 [US2] Implement Variance Thresholding and SelectKBest (scoring function: `f_regression` or `mutual_info_regression`, k=100) dimensionality reduction in `src/data/preprocessing.py` to reduce feature count for regression targets
- [~] T024 [US2] Save feature matrix to `data/processed/feature_matrix.parquet` with checksum
- [~] T025 [US2] Implement `src/modeling/train.py` to load features, normalize target (Z-score), and train XGBoost model
- [~] T026 [US2] Implement 5-fold Cross-Validation loop with Leave-One-Scaffold-Out (LOSO) validation in `src/modeling/train.py` to ensure generalization to new chemistry (Plan Complexity Tracking)
- [~] T026b [US2] Implement runtime tracking and enforcement in `src/modeling/train.py`: abort training if runtime exceeds a predefined threshold (FR-003)
- [ ] T027 [US2] Save trained model artifact to `data/models/xgboost_model.json` and training logs to `data/processed/training_log.json`
- [ ] T028 [US2] Integrate logging, state update, and error handling in `src/modeling/train.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Comparative Analysis and Significance Testing (Priority: P3)

**Goal**: Compare performance across classes, compute Spearman ρ, and run permutation test for significance (p < 0.01).

**Independent Test**: Can be fully tested by running the analysis script on the cross-validation results and verifying that the output report contains a ranked list of reaction classes by Spearman ρ, with SN1/SN2/Diels-Alder labels clearly distinguished, and a p-value < 0.01 for the permutation test.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T029 [P] [US3] Unit test for Spearman correlation calculation and permutation test logic in `tests/unit/test_evaluate.py`

### Implementation for User Story 3

- [ ] T030 [US3] Implement `src/modeling/evaluate.py` to load model results and compute Spearman rank correlation (ρ) between predicted and observed reactivity
- [ ] T031 [US3] Implement logic to verify target variable derivation (strictly from experimental yield/success flags) using upstream data from T014
- [ ] T032 [US3] Implement permutation test (iterations, class-conditional: shuffle targets within each class) in `src/modeling/evaluate.py` to calculate p-values against the null hypothesis of ρ = 0
- [ ] T033 [US3] Generate summary report ranking SN1, SN2, Diels-Alder by Spearman ρ with p-values in `data/processed/analysis_report.json`
- [ ] T034 [US3] Implement logic in report generation to flag "Not Significant" if p-value ≥ 0.01, ensuring FR-005 and SC-002 thresholds are explicitly reported/enforced
- [ ] T035 [US3] Implement logic to skip classes in the final report if sample size < 1,000 (reusing logic from T016) to satisfy FR-006
- [ ] T036 [US3] Integrate logging, state update, and final report generation in `src/modeling/evaluate.py`
- [ ] T037 [US3] Verify that `main.py` orchestrates the full pipeline (Ingestion → Features → Train → Evaluate)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Generate README.md sections: Setup, Data Sources (with citations), Pipeline Execution
- [ ] T040 Run `flake8` on `src/` and fix reported errors to ensure code cleanup is deterministic
- [ ] T041 Performance optimization: verify batch sizes and chunking logic to stay within available RAM constraints
- [ ] T042 [P] Additional unit tests for edge cases (malformed SMILES, missing classes) in `tests/unit/`
- [ ] T043 Run `quickstart.md` validation and ensure all scripts run end-to-end on CPU-only runner

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (filtered data) for feature extraction
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (model results) for evaluation

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
Task: "Unit test for SMILES normalization and error logging in tests/unit/test_ingestion.py"
Task: "Unit test for reaction template matching logic in tests/unit/test_templates.py"

# Launch all models for User Story 1 together:
Task: "Implement src/data/ingestion.py to download USPTO subset"
Task: "Implement reaction template matching in src/utils/chemistry.py"
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
- **Critical Constraint**: All tasks must run on CPU-only (limited core count, constrained RAM). No GPU, no 8-bit/4-bit quantization, no large LLMs. Use small models and sampled data if necessary.