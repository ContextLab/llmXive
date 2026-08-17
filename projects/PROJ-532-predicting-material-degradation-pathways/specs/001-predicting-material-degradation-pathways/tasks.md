---
description: "Task list template for feature implementation"
---

# Tasks: Predicting Material Degradation Pathways from Compositional Data

**Input**: Design documents from `/specs/001-predicting-material-degradation-pathways/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[S]**: Sequential (depends on previous task completion)
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
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `code/` (create `.ruff.toml`, `pyproject.toml`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/utils.py` with checksumming helpers (SHA-256) and deterministic logging
- [X] T005 [P] Create `data/` directory structure (`raw/`, `processed/`) and `data/README.md` for provenance
- [ ] T006 [P] Create `results/` directory structure (`metrics/`, `plots/`, `artifacts/`)
- [X] T007 Implement `code/__init__.py` and set `PYTHONPATH` configuration for `code/` module
- [X] T008 Configure environment variable handling for dataset URLs and random seeds in `code/utils.py`
- [X] T009a [P] **Create Static Bibliography**: Create `data/contracts/literature_dois.txt` containing a hardcoded list of a small number of specific DOIs for verified metal corrosion review papers (e.g.,). DO NOT query external APIs at runtime. This file is the single source of truth for the literature vector.
- [X] T009b [S] **Construct Reference Importance Vector**: Implement `code/literature_review.py` to load `data/contracts/literature_dois.txt`, fetch metadata for these specific DOIs (using `requests` or `pydoi`), perform a systematic review to extract ranked feature importance lists, normalize rankings to 0-1, aggregate via citation-weighted average, and save the result to `data/contracts/literature_vector.json`. **This task depends on T009a completion.**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion, Preprocessing, and OOD Split (Priority: P1) 🎯 MVP

**Goal**: Ingest raw corrosion datasets from Zenodo, filter for metallic alloys, encode elemental compositions, validate data sufficiency, and perform an alloy-class based OOD split.

**Independent Test**: The pipeline can be executed end-to-end on a sample dataset, producing `data/processed/cleaned_alloys.csv`, `data/processed/train_set.parquet`, `data/processed/test_ood_set.parquet`, and all required audit reports, verifiable by checking file dimensions and split logic.

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
- [X] T018a [US1] Implement `code/ingestion.py` to calculate retention statistics (count, percentage) from the filtered dataset.
- [ ] T018b [S] [US1] **Verify Data Sufficiency**: Implement `code/ingestion.py` to write `data/processed/retention_audit.json` with the calculated stats. **HALT** the pipeline if retention < 70% OR record count < 200. If HALT is triggered, **immediately generate** `data/processed/data_insufficiency_report.json` (T020) and stop. Target: ≥70% retention, ≥200 records. **This task depends on T018a. If targets are not met, T018b must trigger T020.**

**Checkpoint**: Data ingestion and sufficiency check complete. OOD Split logic follows immediately in this phase.

---

## Phase 3 (Continued): OOD Split Logic (Final Block of US1)

**Goal**: Generate the explicit OOD split report and alloy class map required for FR-007 and SC-006. This block must complete before US2 begins.

- [ ] T019a [S] [US1] **Generate Alloy Class Map**: Implement `code/preprocessing.py` to generate `data/contracts/alloy_class_map.json`. Use explicit composition rules: "If Fe > 10% AND Cr > 10% THEN 'Stainless Steel'", "If Fe > 80% AND C < 2% THEN 'Carbon Steel'", "If 5+ elements > 5% each THEN 'High-Entropy Alloy'". Apply these rules to `data/processed/cleaned_alloys.csv`. **This task depends on T018b.**
- [ ] T019a_val [S] [US1] **Validate Alloy Map Completeness**: Implement `code/preprocessing.py` to count records successfully classified by T019a. **HALT** the pipeline if classification coverage < 90%. Log the failure reason to `data/processed/classification_failure_log.json`. **This task depends on T019a.**
- [ ] T019 [S] [US1] **Perform OOD Split**: Implement `code/preprocessing.py` to perform **Out-of-Distribution (OOD) test set split based on alloy class** using `data/contracts/alloy_class_map.json`. **If <2 classes exist, HALT the pipeline immediately** with `error_code: OOD_SPLIT_FAILED` and `message: Insufficient alloy classes for OOD split`. Do NOT fall back to random split. Generate `data/processed/train_set.parquet` and `data/processed/test_ood_set.parquet`. **This task depends on T019a_val.**
- [X] T019b [S] [US1] **Generate OOD Split Report**: Implement `code/preprocessing.py` to generate `data/processed/ood_split_report.json` containing the split ratio, the specific alloy classes held out, and an explicit `ood_validation_passed` boolean flag. **This task depends on T019.**
- [~] T019c [S] [US1] **Generate OOD Audit Log**: Implement `code/preprocessing.py` to generate `data/processed/ood_audit.json` containing the raw logic trace of the split decision. **This task depends on T019b.**

**Checkpoint**: US1 Complete. Data ingestion, sufficiency check, and OOD split artifacts are ready. US2 can now begin.

---

## Phase 4: User Story 2 - Model Training and Evaluation (Priority: P2)

**Goal**: Train a multi-label Random Forest classifier on CPU, evaluate against a stratified random baseline using macro-F1 and permutation tests, and generate confusion matrices.

**Independent Test**: The training script executes on a CPU-only environment, produces a trained model artifact, and generates a report containing the macro-F1 score and confusion matrix, which can be compared against a stratified random baseline.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Unit test for stratified split logic in `tests/unit/test_training.py`
- [X] T022 [P] [US2] Unit test for permutation test implementation in `tests/unit/test_evaluation.py` (verify n=1000 iterations)
- [X] T023 [S] [US2] Write integration test code for training and evaluation pipeline in `tests/integration/test_model_pipeline.py`. **Note: Execution of this test requires artifacts from T024-T029.**

### Implementation for User Story 2

- [X] T024 [US2] Implement `code/training.py` to train a Random Forest multi-label classifier (CPU-only, default precision) using the pre-split `train_set.parquet` generated in T019.
- [X] T025 [US2] Implement `code/evaluation.py` to generate a stratified random baseline preserving class distribution **and explicitly preserving the multi-label correlation structure during shuffling by shuffling the joint label vector**, defining the null hypothesis as "no predictive power beyond label correlation".
- [X] T026 [US2] Implement `code/evaluation.py` to perform permutation test (n=1,000, shuffle the joint label vector per sample) to validate p < 0.05.
- [~] T026c [S] [US2] **Enforce Permutation Test Stop Condition**: Implement `code/evaluation.py` to check the p-value from T026. **HALT** the pipeline if p >= 0.05. Log failure to `results/metrics/permutation_test_failure.json`. **This task depends on T026.**
- [~] T026b [S] [US2] **Generate Permutation Test Report**: Implement `code/evaluation.py` to generate `results/metrics/permutation_test_report.json` containing the p-value, the null distribution plot (`results/plots/null_distribution.png`), and an explicit `permutation_test_passed` boolean flag. **Plot must use matplotlib, x-axis='Permutation Score', y-axis='Frequency'.** **This task depends on T026c.**
- [X] T027 [US2] Implement `code/evaluation.py` to calculate macro-F1 score and compare against baseline (Baseline: stratified random shuffle of joint labels; Target: margin ≥ 0.05).
- [X] T028 [US2] Implement `code/evaluation.py` to generate confusion matrix identifying error modes (e.g., pitting vs. SCC).
- [X] T029 [US2] Save trained `ModelArtifact` (model + metrics) to `results/artifacts/model.pkl` and `results/metrics/training_report.json`
- [ ] T030a [US2] Implement timing instrumentation in `code/training.py` to log execution time to `results/metrics/timing_log.json`.
- [ ] T030b [US2] Verify execution time of full training/eval cycle is ≤ 6 hours on CPU runner by checking `results/metrics/timing_log.json`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance and Sensitivity Analysis (Priority: P3)

**Goal**: Identify alloying elements driving predictions using SHAP, perform threshold sensitivity analysis, and validate against a literature-derived Reference Importance Vector.

**Independent Test**: The analysis script generates a ranked list of feature importances (via SHAP) and a plot showing model performance stability across a range of threshold values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T031 [P] [US3] Unit test for SHAP value calculation in `tests/unit/test_explainability.py`
- [X] T032 [P] [US3] Unit test for threshold sensitivity sweep logic in `tests/unit/test_explainability.py`
- [X] T033 [P] [US3] Unit test for Spearman rank correlation calculation in `tests/unit/test_explainability.py`

### Implementation for User Story 3

- [X] T034 [S] [US3] Implement `code/explainability.py` to compute SHAP values for the trained Random Forest model
- [X] T035 [S] [US3] Implement `code/explainability.py` to generate ranked feature importance lists for each degradation pathway
- [ ] T036 [S] [US3] Implement `code/explainability.py` to perform threshold sensitivity sweep (baseline level, deltas Δ ∈ {small, medium, large values})
- [ ] T037 [S] [US3] Implement `code/explainability.py` to report FP/FN rate variations and stability check (within 5% variance)
- [ ] T038 [S] [US3] Implement `code/explainability.py` to load the `data/contracts/literature_vector.json` (constructed in T009b) and calculate Spearman rank correlation (ρ) between SHAP results and Reference Vector (Target: ρ ≥ 0.6).
- [ ] T038c [S] [US3] **Enforce Literature Validation Stop Condition**: Implement `code/explainability.py` to check the correlation coefficient from T038. **HALT** the pipeline if ρ < 0.6. Log failure to `results/metrics/literature_validation_failure.json`. **This task depends on T038.**
- [ ] T038b [S] [US3] **Generate Literature Validation Report**: Implement `code/explainability.py` to generate `results/metrics/literature_validation_report.json` documenting the correlation coefficient, the reference vector source, and an explicit `literature_validation_passed` boolean flag. **This task depends on T038c.**
- [ ] T039 [S] [US3] **Calculate Provisional Metrics**: Implement `code/explainability.py` to calculate a deterministic "provisional" metric for unobserved confounders (e.g., missing pH/temp) by applying a **an appropriate scaling factor** to the missing variable estimate. **Explicitly flag the result as [provisional] and [estimated] in all outputs.**
- [ ] T039b [S] [US3] **Generate Confounding Factor Audit**: Implement `code/explainability.py` to generate `results/metrics/confounding_factor_audit.json` listing the missing variables (pH, temp), the applied provisional logic, and update the final `explainability_report.json` with the specific `[deferred]` flags for these variables. **This task must run before T040.**
- [ ] T040 [S] [US3] **Generate Final Reports**: Implement `code/explainability.py` to generate `results/plots/shap_summary.png`, `results/plots/threshold_sensitivity.png`, and `results/metrics/explainability_report.json`. **This task must incorporate the deferred flags from T039b into the final report.**
- [ ] T041 [S] [US3] Ensure all findings are explicitly framed as associational, not causal. **Add the following text to all reports: "These findings are associational and do not imply causation."**

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
 - **T009a/T009b** depends on **Spec Assumptions** (fixed list of papers) and must complete before US3.
 - **T009b** explicitly depends on **T009a** (Sequential).
 - **T018a/T018b** depend on **T015** (Preprocessing).
 - **T019a** depends on **T018b** (Cleaned Data).
 - **T019a_val** depends on **T019a** (Map Generation).
 - **T019** depends on **T019a_val** (Validation Passed).
 - **T019b** depends on **T019** (Split Logic).
 - **T019c** depends on **T019b** (Report Generation).
 - **T020** is conditionally dependent on **T018b** (Failure Path).
 - **T019 is the final task of US1.**
- **User Story 2 (P2)**: **BLOCKED** until **T019c** (OOD Audit) completion - requires `data/processed/train_set.parquet` and `data/processed/test_ood_set.parquet`. T024 explicitly depends on T019c.
- **User Story 3 (P3)**: Depends on US2 completion (requires trained model artifact) and T009b (Literature Vector).

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services (Data logic before training logic)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
 - **Note: T009a and T009b are sequential ([S]) and cannot run in parallel.**
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
3. Complete Phase 3: User Story 1 (including OOD Split T019)
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
 - Developer B: User Story 2 (Model) - *Can start once T019c (OOD Audit) is complete*
 - Developer C: User Story 3 (Explainability) - *Can start once model is ready*
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [S] tasks = sequential (must wait for previous task)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CRITICAL**: Ensure all data tasks use REAL Zenodo datasets; no synthetic data generation is permitted.
- **CRITICAL**: All model training must be CPU-only; do not use GPU-specific libraries or 8-bit quantization.
- **CRITICAL**: T019 must implement an **alloy class-based** OOD split (e.g., high-entropy alloys) as per FR-007, NOT a source-based split, and must occur BEFORE training. It MUST include a HALT condition if <2 classes exist (no random fallback).
- **CRITICAL**: T009a must create a static `literature_dois.txt` with specific DOIs; T009b constructs the vector from it. No generic titles.
- **CRITICAL**: T039 must calculate a deterministic provisional value (factor 1.0) and flag it as [provisional]/[estimated]; the 'deferred' nature is captured in T039b.
- **CRITICAL**: T025 must preserve the multi-label correlation structure by shuffling the joint label vector, defining the null hypothesis as such.
- **CRITICAL**: T036 must use the explicit delta set {0.01, 0.05, 0.1}.
- **CRITICAL**: T019a must generate the `alloy_class_map.json` before T019 runs, using explicit composition rules.
- **CRITICAL**: T018 is split into T018a (calc) and T018b (write) for granularity.
- **CRITICAL**: T030 is split into T030a (instrument) and T030b (verify) for clarity.
- **CRITICAL**: T023 is marked [S] to prevent premature execution.
- **CRITICAL**: T026c, T038b, T039b are added to generate explicit validation reports.
- **CRITICAL**: T039b must run before T040, and T040 must incorporate the flags from T039b.
- **CRITICAL**: T026c (Enforce) must run BEFORE T026b (Report).
- **CRITICAL**: T038c (Enforce) must run BEFORE T038b (Report).
- **CRITICAL**: T019a_val (Validate Map) must run before T019 (Split).
- **CRITICAL**: T019a, T019a_val, T019, T019b, T019c are ALL sequential ([S]) and cannot run in parallel.
- **CRITICAL**: T009b is sequential ([S]) and depends on T009a.
- **CRITICAL**: T020 is conditionally dependent on T018b failure.