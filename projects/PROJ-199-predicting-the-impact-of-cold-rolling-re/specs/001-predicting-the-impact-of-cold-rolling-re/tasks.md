# Tasks: Predicting the Impact of Cold Rolling Reduction on Texture Evolution in FCC Metals

**Input**: Design documents from `/specs/001-predicting-cold-rolling-texture/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can be developed in parallel (different files, no logical dependency)
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

- [ ] T001a [P] Create top-level directory structure: `code/`, `data/`, `tests/`, `docs/`
- [ ] T001b [P] Create `.gitignore` for Python, data, and IDE files
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (pinning `orix`, `scikit-learn`, `shap`, `pandas`, `numpy`, `pyyaml`, `requests`, `pytest`)
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create subdirectories `raw`, `processed`, `interim` within the existing `data/` folder with `.gitkeep`
- [X] T005 [P] Implement base configuration loader for environment variables and seed management (`code/__init__.py`)
- [~] T006 [P] Setup logging infrastructure to track data lineage and processing steps (`code/utils/logging.py`)
- [~] T007a [P] Implement Pydantic model for 'EBSD Sample' (`code/data/models.py`)
- [~] T007b [P] Implement Pydantic model for 'Texture Descriptor' (`code/data/models.py`)
- [~] T008 Implement unit tests for base schema validation in `tests/unit/test_models.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Pre-processing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Automatically download, filter, and standardize EBSD datasets for Al, Cu, and Ni across specific cold-rolling reductions to ensure the analysis is based on high-quality, crystallographically consistent data.

**Independent Test**: The pipeline can be tested by running the data acquisition script against the specified public repositories and verifying that the output is a tidy CSV/Parquet file containing only valid orientations with confidence indices ≥ 0.1, properly re-indexed to FCC symmetry.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Tests marked [P] can be written in parallel with implementation, but execution depends on the implementation being complete.

- [~] T009 [P] [US1] Contract test for data schema in `tests/contract/test_data_schema.py`
- [~] T010 [P] [US1] Write test stubs and assertions for the download and filter flow (can be written in parallel with T011/T012 implementation) in `tests/integration/test_data_pipeline.py`

### Implementation for User Story 1

- [~] T011 [P] [US1] Implement `code/data/download.py` to fetch EBSD data from HuggingFace (dataset ID specified in research.md Section 2.1) OR fallback to local synthetic generation (FR-001). **Priority**: Real data ingestion first.
- [~] T011b [US1] Implement `code/data/generate_synthetic.py` as a **FALLBACK ONLY** mechanism, triggered strictly if T011 (real data download) fails. Generate synthetic EBSD data with pinned seeds. Reduction levels MUST be read from `code/config.py`; if values are missing, raise a `ConfigurationError` immediately. (Plan: Dataset Fit Note)
- [~] T012 [US1] Implement `code/data/preprocess.py` to filter confidence index < 0.1 and re-index orientations to FCC symmetry using `orix`. Reduction levels MUST be read from `code/config.py`; if values are missing, raise a `ConfigurationError` immediately. (FR-002)
- [~] T013 [US1] Add error handling for missing reduction levels or corrupted files, logging warnings and proceeding (US-1 Scenario 3)
- [~] T014 [US1] Implement exclusion logic: flag samples where >50% of points are filtered as "low reliability" and EXCLUDE them from the final training set (Edge Case)
- [~] T015 [US1] Generate consolidated Parquet output to `data/processed/cleaned_ebsd.parquet` with metadata (material, reduction, confidence)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Texture Quantification and Descriptor Extraction (Priority: P2)

**Goal**: Convert raw orientation data into specific, quantifiable texture descriptors (Texture Index, Volume Fractions of Brass, Copper, S, and Goss components) to enable statistical modeling.

**Independent Test**: The quantification module can be tested by processing a known benchmark dataset and verifying that the calculated volume fractions match published values within ±0.05.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T016 [P] [US2] Unit test for Brass/Copper/S/Goss calculation logic in `tests/unit/test_descriptors.py`
- [ ] T017 [P] [US2] Benchmark test against Rosenstock et al. (2018) values in `tests/unit/test_benchmark_validation.py`

### Implementation for User Story 2

- [ ] T018 [US2] Implement `code/features/descriptors.py` to calculate Texture Index and volume fractions using MTEX-style search algorithms (Euler ranges: Brass [,45,35,45], Copper [35,45,35,45], S [35,45,35,45], Goss [35,45,35,45]) (FR-003)
- [ ] T019 [US2] Implement mass balance check: ensure sum of major components + "random" = 1.0 ± 0.01 (US-2 Scenario 2)
- [ ] T020 [US2] Integrate `orix` symmetry handling to ensure correct component identification for FCC crystals (FR-002)
- [ ] T021 [US2] Output descriptors to `data/processed/descriptors.csv` linked to original sample IDs
- [ ] T022 [US2] Add validation to flag samples where texture evolution deviates from standard FCC trends (Edge Case)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Predictive Modeling and Validation (Priority: P3)

**Goal**: Train predictive models (Polynomial Regression, Gaussian Process) to estimate texture descriptors based on cold-rolling reduction with high accuracy (R² ≥ 0.85).

**Independent Test**: The model training and validation pipeline can be tested by splitting the dataset and verifying that the R² on the held-out test set meets a satisfactory performance threshold.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US3] Contract test for model output schema in `tests/contract/test_model_output.py`
- [ ] T024 [P] [US3] Integration test for 5-fold CV pipeline in `tests/integration/test_model_training.py`

### Implementation for User Story 3

- [ ] T025 [US3] Implement `code/models/train.py` to fit separate polynomial (degree=2) and joint Gaussian Process (RBF kernel) models (FR-004)
- [ ] T026 [US3] Include 'Material Type' as a categorical feature in the joint model (FR-008)
- [ ] T027 [US3] Implement k-fold cross-validation in `code/models/validate.py` to output RMSE and R² metrics (FR-005)
- [ ] T028 [US3] Implement extrapolation flagging: flag predictions outside a plausible reduction range and apply a confidence penalty (FR-009)
- [ ] T029 [US3] Implement "Hold-out Physics Check" in `code/analysis/physics_check.py` to validate that trends (e.g., Brass increase) match known physics AND ensure all output reports explicitly frame findings as associational relationships (FR-006). **Note**: This task focuses on trend validation, not symmetry constraints (which are handled in T012).
- [ ] T030 [DEPRECATED - Merged into T029]

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Model Robustness and Extrapolation Bounds (Priority: P4)

**Goal**: Ensure model stability under data sparsity and quantify the impact of missing microstructural variables.

**Independent Test**: The robustness module can be tested by running sensitivity analysis on interpolation tolerance and verifying R² variation ≤ 0.02.

### Tests for User Story 4 (OPTIONAL - only if tests requested) ⚠️

- [ ] T031 [P] [US4] Unit test for sensitivity analysis logic in `tests/unit/test_robustness.py`
- [ ] T032 [P] [US4] Integration test for variance decomposition in `tests/integration/test_variance_decomposition.py`

### Implementation for User Story 4

- [ ] T033 [US4] Implement `code/analysis/robustness.py` to sweep interpolation tolerance over the **specific set {0.01, 0.05, 0.1}** as mandated by FR-007 (FR-007)
- [ ] T034 [US4] Verify R² variation remains ≤ 0.02 across swept tolerances {0.01, 0.05, 0.1} using T033 output (US-4 Scenario 2)
- [ ] T035 [US4] Implement variance decomposition (Shapley values or Hierarchical Modeling) to quantify residual variance from missing microstructural variables (FR-008)
- [ ] T036 [US4] Report the percentage of variance attributable to missing variables (e.g., grain size, SFE) in final metrics (US-4 Scenario 3)
- [ ] T037 [DELETED - Scope Creep: Physical diffraction evidence not in spec]

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T048 [P] Documentation updates in `docs/` including model limitations, associational framing, and the new pole figure validation methodology (Note: Removed pole figure section per scope review)
- [ ] T049 Code cleanup and refactoring for CPU efficiency (ensure no GPU calls)
- [ ] T050 [P] Additional unit tests for edge cases (missing data, extrapolation, symmetry errors) in `tests/unit/`
- [ ] T051 Run `quickstart.md` validation to ensure end-to-end reproducibility
- [ ] T052 Verify all artifacts (data, models, metrics) are derived via script (Constitution Principle IV)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (T015)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 descriptor output (T021)
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Depends on US3 model output (T025/T027)

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
- All tests for a user story marked [P] can run in parallel (development phase only)
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data schema in tests/contract/test_data_schema.py"
Task: "Write test stubs and assertions for the download and filter flow in tests/integration/test_data_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/download.py"
Task: "Implement code/data/preprocess.py"
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

- [P] tasks = different files, no logical dependencies (can be developed in parallel)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Review Note**: T037 removed due to scope creep (physical diffraction evidence not in spec). T014 updated to include exclusion logic. T011b added for synthetic data generation as a fallback only.
- **Critical Review Update**: Phase 7 (T043-T047) removed as it implemented unapproved pole figure validation not present in the spec. FCC symmetry is enforced in T012 (Preprocessing) per FR-002. The "Hold-out Physics Check" in T029 now focuses strictly on trend validation.
- **Executability Note**: Reduction levels are now defined via `code/config.py` with a fail-fast `ConfigurationError` if missing. T011 references `research.md` for dataset IDs.