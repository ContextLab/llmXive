# Tasks: Predicting Material Degradation Pathways from Compositional Data

**Input**: Design documents from `/specs/001-predicting-material-degradation-pathways/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

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

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-532-predicting-material-degradation-pathways/`)
- [X] T002 Initialize Python 3.11 project with `code/requirements.txt` (pandas, scikit-learn, shap, requests, pyyaml, numpy, scipy)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/utils.py` with checksumming helpers (SHA-256) and deterministic logging
- [ ] T005 [P] Create `data/` directory structure (`raw/`, `processed/`) and `data/README.md` for provenance
- [ ] T006 [P] Create `results/` directory structure (`metrics/`, `plots/`, `artifacts/`)
- [ ] T007 Implement `code/__init__.py` and set `PYTHONPATH` configuration for `code/` module
- [ ] T008 Configure environment variable handling for dataset URLs and random seeds in `code/utils.py`
- [~] T009 [P] [US3] **Construct Reference Importance Vector**: Implement `code/literature_review.py` to load the fixed set of 5 review papers listed in Spec Assumptions (or their most recent equivalents), perform a systematic review to extract ranked feature importance lists for degradation pathways, normalize rankings to 0-1, aggregate via citation-weighted average, and save the result to `data/contracts/literature_vector.json` for use in SC-003 validation. This task is independent of data ingestion (T013) and must complete before US3 begins. **Note: This task is moved to Phase 2 to ensure the artifact exists before T038 (Validation) runs.**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw corrosion datasets from Zenodo, filter for metallic alloys, and encode elemental compositions into machine-readable feature vectors with proper handling of missing data.

**Independent Test**: The pipeline can be executed end-to-end on a sample dataset, producing a clean CSV file with encoded features and valid degradation labels, verifiable by checking the output file dimensions and label distribution.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for filtering logic in `tests/unit/test_ingestion.py` (verify non-metallics removed)
- [X] T011 [P] [US1] Unit test for missing value imputation in `tests/unit/test_preprocessing.py` (verify <5% median, >=5% drop)
- [X] T012 [P] [US1] Integration test for full ingestion pipeline in `tests/integration/test_ingestion_pipeline.py`

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement `code/ingestion.py` to download raw CSV from Zenodo (verify URL reachable)
- [X] T014 [US1] Implement `code/ingestion.py` logic to filter records: retain ONLY metallic alloys, discard polymers/composites
- [X] T015 [US1] Implement `code/ingestion.py` logic to calculate missing value percentages and apply imputation (median) or exclusion rules
- [X] T016 [P] [US1] Implement `code/preprocessing.py` to map elemental weight percentages to feature vectors
- [X] T017 [P] [US1] Implement `code/preprocessing.py` to calculate derived atomic properties (electronegativity, radius) for post-hoc analysis (exclude from training vector)
- [~] T018 [US1] Implement `code/ingestion.py` to generate `data/processed/cleaned_alloys.csv`, calculate retention percentage and record count, and explicitly log these stats to `data/processed/retention_audit.json` (Target: ≥70% retention, ≥200 records) to verify SC-005.
- [~] T019 [US1] Implement `code/preprocessing.py` to perform **Out-of-Distribution (OOD) test set split based on alloy class**: Identify distinct alloy families (e.g., High-Entropy Alloys, Stainless Steels, Carbon Steels) in the dataset. **If <2 classes exist, fallback to a stratified random split and explicitly flag this condition in the output report**; otherwise, hold out one full family as the test set to generate `data/processed/train_set.parquet` and `data/processed/test_ood_set.parquet`, as mandated by FR-007 and SC-006.
- [X] T020 [US1] Add "Data Insufficiency Report" generation logic in `code/ingestion.py` if record count < 200 after filtering

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Evaluation (Priority: P2)

**Goal**: Train a multi-label Random Forest classifier on CPU, evaluate against a stratified random baseline using macro-F1 and permutation tests, and generate confusion matrices.

**Independent Test**: The training script executes on a CPU-only environment, produces a trained model artifact, and generates a report containing the macro-F1 score and confusion matrix, which can be compared against a stratified random baseline.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Unit test for stratified split logic in `tests/unit/test_training.py`
- [ ] T022 [P] [US2] Unit test for permutation test implementation in `tests/unit/test_evaluation.py` (verify n=1000 iterations)
- [ ] T023 [P] [US2] Integration test for training and evaluation pipeline in `tests/integration/test_model_pipeline.py`

### Implementation for User Story 2

- [ ] T024 [US2] Implement `code/training.py` to train a Random Forest multi-label classifier (CPU-only, default precision) using the pre-split `train_set.parquet` generated in T019.
- [ ] T025 [US2] Implement `code/evaluation.py` to generate a stratified random baseline preserving class distribution **and explicitly preserving the multi-label correlation structure during shuffling by shuffling the joint label vector**, as required by SC-001 for the permutation test.
- [ ] T026 [US2] Implement `code/evaluation.py` to perform permutation test (n=1,000, shuffle the joint label vector per sample) to validate p < 0.05
- [ ] T027 [US2] Implement `code/evaluation.py` to calculate macro-F1 score and compare against baseline (Target: margin ≥ 0.05)
- [ ] T028 [US2] Implement `code/evaluation.py` to generate confusion matrix identifying error modes (e.g., pitting vs. SCC)
- [ ] T029 [US2] Save trained `ModelArtifact` (model + metrics) to `results/artifacts/model.pkl` and `results/metrics/training_report.json`
- [ ] T030 [US2] Verify execution time of full training/eval cycle is ≤ 6 hours on CPU runner

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance and Sensitivity Analysis (Priority: P3)

**Goal**: Identify alloying elements driving predictions using SHAP, perform threshold sensitivity analysis, and validate against a literature-derived Reference Importance Vector.

**Independent Test**: The analysis script generates a ranked list of feature importances (via SHAP) and a plot showing model performance stability across a range of threshold values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T031 [P] [US3] Unit test for SHAP value calculation in `tests/unit/test_explainability.py`
- [ ] T032 [P] [US3] Unit test for threshold sensitivity sweep logic in `tests/unit/test_explainability.py`
- [ ] T033 [P] [US3] Unit test for Spearman rank correlation calculation in `tests/unit/test_explainability.py`

### Implementation for User Story 3

- [ ] T034 [P] [US3] Implement `code/explainability.py` to compute SHAP values for the trained Random Forest model
- [ ] T035 [US3] Implement `code/explainability.py` to generate ranked feature importance lists for each degradation pathway
- [ ] T036 [US3] Implement `code/explainability.py` to perform threshold sensitivity sweep (baseline level, deltas Δ ∈ {0.01, 0.05, 0.1})
- [ ] T037 [US3] Implement `code/explainability.py` to report FP/FN rate variations and stability check (within 5% variance)
- [ ] T038 [US3] Implement `code/explainability.py` to load the `data/contracts/literature_vector.json` (constructed in T009) and calculate Spearman rank correlation (ρ) between SHAP results and Reference Vector (Target: ρ ≥ 0.6)
- [ ] T039 [US3] Implement `code/explainability.py` to flag missing environmental variables (pH, temp), **apply a [deferred] placeholder scaling factor** to account for unobserved confounders, and explicitly annotate all affected output metrics with `[deferred]` for unobserved confounders as per FR-009. **Do not calculate a concrete value; the factor must remain a placeholder.**
- [ ] T040 [US3] Generate `results/plots/shap_summary.png`, `results/plots/threshold_sensitivity.png`, and `results/metrics/explainability_report.json`
- [ ] T041 [US3] Ensure all findings are explicitly framed as associational, not causal (add disclaimer to reports)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T042 [P] Documentation updates in `data/README.md` and `results/README.md`
- [ ] T043 Code cleanup and refactoring in `code/` to ensure PEP8 compliance
- [ ] T044 Performance optimization: Verify memory usage stays within 7GB limit during SHAP analysis
- [ ] T045 [P] Run `pytest` suite to ensure all unit and integration tests pass
- [ ] T046 Security hardening: Verify no hardcoded credentials or API keys in `code/`
- [ ] T047 Run quickstart.md validation (if created) to ensure pipeline reproducibility

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
 - **T009** depends on **Spec Assumptions** (static list of papers) and must complete before US3.
 - **T019** (OOD Split) depends on **T018** (Cleaned Data).
- **User Story 2 (P2)**: Depends on US1 completion (requires `data/processed/train_set.parquet` from T019)
- **User Story 3 (P3)**: Depends on US2 completion (requires trained model artifact) and T009 (Literature Vector)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services (Data logic before training logic)
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
Task: "Unit test for filtering logic in tests/unit/test_ingestion.py"
Task: "Unit test for missing value imputation in tests/unit/test_preprocessing.py"

# Launch all models for User Story 1 together:
Task: "Implement code/ingestion.py to download raw CSV"
Task: "Implement code/preprocessing.py to map elemental weight percentages"
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
 - Developer A: User Story 1 (Data)
 - Developer B: User Story 2 (Model) - *Can start once data is ready*
 - Developer C: User Story 3 (Explainability) - *Can start once model is ready*
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
- **CRITICAL**: Ensure all data tasks use REAL Zenodo datasets; no synthetic data generation is permitted.
- **CRITICAL**: All model training must be CPU-only; do not use GPU-specific libraries or 8-bit quantization.
- **CRITICAL**: T019 must implement an **alloy class-based** OOD split (e.g., high-entropy alloys) as per FR-007, NOT a source-based split, and must occur BEFORE training. It MUST include a fallback to stratified random split if <2 classes exist.
- **CRITICAL**: T009 must construct the `literature_vector.json` from the fixed set of 5 papers in Spec Assumptions, independently of T013, and must complete before US3.
- **CRITICAL**: T039 must apply the `[deferred]` placeholder annotation for unobserved confounders as per FR-009; do not calculate a concrete value.
- **CRITICAL**: T025 must preserve the multi-label correlation structure by shuffling the joint label vector.
- **CRITICAL**: T036 must use the explicit delta set {0.01, 0.05, 0.1}.