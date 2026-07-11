# Tasks: Predicting Yield Strength of BCC Alloys

**Input**: Design documents from `/specs/001-predicting-the-yield-strength-of-bcc-all/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)
**Branch**: `001-bcc-yield-strength`

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root (as per `plan.md`)
- **Data**: `data/raw/`, `data/processed/`

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

- [ ] T001 Create project structure per `plan.md` (`code/`, `tests/`, `data/raw/`, `data/processed/`)
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (pandas, scikit-learn, numpy, periodictable, pyyaml, requests, joblib, scipy, pytest)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/utils/periodic_table.py` with static NIST elemental property lookup (atomic radius, valence, electronegativity) to avoid API calls
- [X] T005 Create `code/utils/metrics.py` for custom metric definitions and statistical helpers
- [ ] T006 Setup `data-model.md` definitions for `AlloyRecord`, `CompositionalDescriptor`, `ModelPerformance`
- [~] T007 Create base configuration management (`.env` support, path constants) in `code/config.py`
- [~] T008 Setup `pytest` integration structure in `tests/`
- [~] T010 [US1] Implement retrieval/parsing of MPEA experimental uncertainty metadata (target: <= 50 MPa) from the source documentation or metadata file to support SC-002

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Curation and BCC Filtering (Priority: P1) 🎯 MVP

**Goal**: Obtain a clean, filtered dataset containing only BCC alloys with valid yield strength and complete compositions.

**Independent Test**: Execute the ingestion script on a raw CSV; verify output has zero non-BCC entries, zero null yields, and all composition rows sum to 1.0.

### Implementation for User Story 1

- [~] T011 [US1] Implement manual ingestion of MPEA database: copy `data/raw/mpea_raw.csv` from local source and verify file integrity via checksum (as per plan.md "No Verified URL" constraint); do NOT attempt automated fetch <!-- FAILED: unspecified -->
- [~] T012 [US1] Implement `code/01_download.py` to load `data/raw/mpea_raw.csv`, filter for `crystal_structure` == "BCC", and exclude null/non-numeric yield strengths
- [~] T013 [US1] Implement composition normalization in `code/01_download.py`: divide by row sum, log original vs. normalized values, and flag rounding errors
- [~] T014 [US1] Implement rejection logic in `code/01_download.py`: write rejected entries to `data/rejected_entries.log` with reason codes
- [~] T015 [US1] Implement data scarcity check in `code/01_download.py`: halt pipeline with specific "Data Scarcity Warning" if N < 80
- [~] T016 [US1] Save filtered output to `data/processed/bcc_filtered.csv`

### Tests for User Story 1

- [~] T017 [P] [US1] Unit test `tests/unit/test_filters.py::test_bcc_filter_excludes_fcc` to verify BCC filtering logic
- [~] T018 [P] [US1] Unit test `tests/unit/test_filters.py::test_composition_normalization_sum_to_one` to verify normalization
- [~] T019 [P] [US1] Unit test `tests/unit/test_filters.py::test_rejection_logging_non_numeric_yield` to verify rejection logging
- [~] T020 [P] [US1] Integration test `tests/integration/test_pipeline.py::test_pipeline_halts_on_data_scarcity` verifying pipeline halts with "Data Scarcity Warning" if N < 80

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compositional Feature Engineering (Priority: P2)

**Goal**: Generate derived compositional descriptors (δ, VEC, entropy, enthalpy) OR ILR transformed features.

**Independent Test**: Verify calculated descriptors for a known alloy against manual calculation (tolerance set to a sufficiently small threshold to ensure numerical stability) and ensure ILR transformation addresses closure.

### Implementation for User Story 2

- [~] T021 [US2] Implement Circular Validation Check in `code/02_engineer.py`: detect if yield strength source is CALPHAD-derived; if so, **flag a "Circular Validation Warning"** in logs and provide a configuration toggle to either **exclude** those entries OR **use only raw composition features** (per FR-003.3)
- [ ] T022 [US2] Implement scalar descriptor calculation (δ, VEC, entropy, enthalpy) in `code/02_engineer.py` using `periodic_table.py`
- [ ] T023 [US2] Implement ILR transformation logic in `code/02_engineer.py` to address compositional closure
- [ ] T024 [US2] Implement mutual exclusivity logic in `code/02_engineer.py`: ensure the script runs two distinct passes (one for descriptors, one for ILR) and does not combine them
- [ ] T025 [US2] Handle domain errors (e.g., log(0)) by assigning 0.0 or NaN and logging specific alloy IDs in `code/02_engineer.py`
- [ ] T026 [US2] Save outputs to `data/processed/features_descriptors.csv` and `data/processed/features_ilr.csv`

### Tests for User Story 2

- [ ] T027 [P] [US2] Unit test `tests/unit/test_engineering.py::test_delta_radius_calculation` for atomic radius mismatch
- [ ] T028 [P] [US2] Unit test `tests/unit/test_engineering.py::test_valence_electron_concentration_calculation` for VEC
- [ ] T029 [P] [US2] Unit test `tests/unit/test_engineering.py::test_mixing_entropy_enthalpy_calculation` for entropy/enthalpy
- [ ] T030 [P] [US2] Unit test `tests/unit/test_engineering.py::test_ilr_transformation` for ILR transform
- [ ] T031 [P] [US2] Unit test `tests/unit/test_engineering.py::test_missing_element_error_handling` for missing element errors

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Regression Modeling and Validation (Priority: P3)

**Goal**: Train RF, GB, Ridge models with Repeated 5-Fold CV and generate confidence intervals.

**Independent Test**: Run training with fixed seed; verify R², MAE, RMSE match expected values (tolerance threshold set to a sufficiently small value to ensure convergence) and bootstrapped CIs are generated.

### Implementation for User Story 3

- [ ] T032 [US3] Implement `code/03_train.py` to load feature CSVs: perform stratified 80/20 split (quantile-based, 5 bins) **ONLY if N > 200**; **ELSE proceed with Repeated 5-Fold CV on the entire dataset** (no split) to preserve power; **DO NOT halt** for N < 80 here (handled by T015)
- [ ] T033 [US3] Implement Random Forest, Gradient Boosting, and Ridge Regression training with Repeated K-Fold CV in `code/03_train.py`
- [ ] T034 [US3] Implement bootstrapping of CV scores to calculate 95% CI for R² in `code/03_train.py`

### Tests for User Story 3

- [ ] T036 [P] [US3] Integration test `tests/integration/test_pipeline.py::test_model_training_pipeline_fixed_seed` with fixed seed
- [ ] T037 [P] [US3] Unit test `tests/unit/test_metrics.py::test_repeated_cv_implementation` for Repeated 5-Fold CV (10 reps)
- [ ] T038 [P] [US3] Unit test `tests/unit/test_metrics.py::test_bootstrap_ci_generation` for Bootstrap CI (percentile method)
- [ ] T039 [P] [US3] Integration test `tests/integration/test_pipeline.py::test_model_results_include_confidence_intervals` verifying CI generation

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Data Quality and Scarcity Handling (Priority: P4)

**Goal**: Handle edge cases (scarcity, duplicates, domain errors) robustly.

**Independent Test**: Verify pipeline halts on N < 80; verify duplicates are averaged; verify domain errors are logged.

**Note**: Logic for US-4 (scarcity check, duplicate averaging, domain errors) is **integrated** into US-1 (T015, T014) and US-2 (T025). Verification is handled by existing tests (T020, T019, T031). No separate implementation tasks are required for US-4.

---

## Phase 7: User Story 5 - Evaluation & Reporting (Priority: P3/Polish)

**Goal**: Compare models, check stability, and generate final report.

**Independent Test**: Verify Friedman test + Nemenyi post-hoc; verify Spearman correlation of importance ≥ 0.8.

### Implementation for Evaluation

- [ ] T044 [US3] Implement Friedman test + Nemenyi post-hoc (Bonferroni) on CV scores in `code/04_evaluate.py`, explicitly referencing SC-003 for feature stability tracking
- [ ] T045 [US3] Implement feature stability check in `code/04_evaluate.py`: calculate **Spearman rank correlation** of feature importance rankings across CV repetitions and verify against **threshold ≥ 0.8** as required by SC-003
- [ ] T046 [US3] Implement MAE vs. MPEA uncertainty comparison in `code/04_evaluate.py` using the value retrieved/documentated in T010
- [ ] T047 [US3] Generate `data/processed/performance_report.csv` and `data/processed/feature_importance.png`
- [ ] T048 [US3] Add "Power Disclaimer" and "Circular Validation Warning" text generation to the final report
- [ ] T055 [US3] Implement permutation importance testing for the best model in `code/04_evaluate.py` (moved from training phase per FR-006)

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T049 [P] Documentation updates in `README.md` and `docs/`
- [ ] T050 Code cleanup: Refactor high-cyclomatic functions (cyclomatic complexity < 10) in `code/` to improve maintainability
- [ ] T051 Performance optimization: Refactor loops in `code/02_engineer.py` and `code/03_train.py` to ensure runtime < 6h on 2-core CPU
- [ ] T052 [P] Run quickstart.md validation by executing `python code/main.py --validate` and verifying exit code 0
- [ ] T053 Verify all random seeds are pinned in `code/` and dependencies in `requirements.txt`
- [ ] T054 Verify checksums are recorded for `data/raw/` files

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
 - US1 (P1) must complete before US2 (P2) due to data flow (filtering → engineering)
 - US2 (P2) must complete before US3 (P3) due to data flow (features → training)
 - US4 (P4) logic is integrated into US1 and US2 but verified in Phase 6
 - US5 (Evaluation) depends on US3 (Training)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 completion (needs `bcc_filtered.csv`)
- **User Story 3 (P3)**: Depends on US2 completion (needs feature CSVs)
- **User Story 5 (Evaluation)**: Depends on US3 completion

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utilities before services
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel
- Tests within a story marked [P] can run in parallel
- Unit tests for different feature calculations (δ, VEC, ILR) can run in parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (Data Ingestion)
4. **STOP and VALIDATE**: Verify `data/processed/bcc_filtered.csv` exists and meets N ≥ 80 criteria.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Validate Data Quality
3. Add User Story 2 → Test independently → Validate Feature Engineering
4. Add User Story 3 → Test independently → Validate Model Training
5. Add User Story 5 → Test independently → Validate Reporting
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data)
 - Developer B: User Story 2 (Features) - *Can start once T016 is done*
 - Developer C: User Story 3 (Models) - *Can start once T026 is done*
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical**: Ensure `code/01_download.py` strictly enforces the N ≥ 80 rule; if data is insufficient, the pipeline MUST halt to prevent invalid training.
- **Critical**: Ensure `code/02_engineer.py` strictly enforces the ILR vs. Descriptors mutual exclusivity (FR-003.2).
- **Critical**: Ensure `code/02_engineer.py` implements the CALPHAD warning and fallback options (FR-003.3).
- **Critical**: Ensure `code/03_train.py` only splits if N > 200; otherwise uses full dataset for CV.
- **Critical**: Ensure `code/04_evaluate.py` handles permutation importance and stability analysis (SC-003).