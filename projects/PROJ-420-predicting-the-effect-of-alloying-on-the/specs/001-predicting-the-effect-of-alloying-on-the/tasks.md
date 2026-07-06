# Tasks: Predicting the Effect of Alloying on the Poisson's Ratio of Aluminum Alloys

**Input**: Design documents from `/specs/001-predict-poissons-ratio/`
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

- [ ] T001 Create project structure per implementation plan
- [ ] T002 Initialize Python 3.11 project with dependencies (pandas, numpy, scikit-learn, requests, pyyaml, seaborn, matplotlib, compositional, statsmodels) in `code/requirements.txt`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `code/__init__.py` and basic project scaffolding
- [ ] T005 [P] Setup environment configuration management in `code/config.py` (loading `data/`, `models/` paths, random seeds)
- [ ] T006 [P] Implement logging infrastructure in `code/logging_config.py` (JSON logging, error levels)
- [ ] T007 Create data schema definitions in `code/schemas/alloy_record.py` (Pydantic models for AlloyRecord, ModelMetrics) including fields to store provenance metadata for independence verification (FR-009) and the specific source method if available.
- [ ] T008 Implement checksum utility in `code/utils/checksum.py` for verifying raw data integrity

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Extraction and Filtering (Priority: P1) 🎯 MVP

**Goal**: Download compositional and property data from public repositories, filter to valid monolithic aluminum alloys, and ensure unit consistency.

**Independent Test**: Can be fully tested by running the data extraction script against the source databases and verifying the script reports the count of filtered entries and that all entries have complete composition and property records.

### Implementation for User Story 1

- [ ] T009 [US1] Implement data extraction for Materials Project in `code/data_extraction.py` (fetch aluminum alloys via `GET https://next-gen.materialsproject.org/api/v2/materials/` with query params `elements=Al` and filtering for `elastic_properties` in response; validate against AlloyRecord schema from T007 ensuring `measurement_method` field is present; save to `data/raw/mp_aluminum.json`)
- [ ] T010 [US1] Implement data extraction for NIST Materials Data Repository in `code/data_extraction.py` (fetch aluminum alloys via `GET or specific dataset API endpoint; validate against AlloyRecord schema from T007 ensuring `measurement_method` field is present; save to `data/raw/nist_aluminum.json`)
- [ ] T014 [US1] Implement positive verification and exclusion logic in `code/data_cleaning.py` for FR-009: query the `measurement_method` field for each entry; explicitly EXCLUDE entries where the method is 'calculated', 'derived', 'derived_from_Youngs_modulus', OR missing/unknown (as independence cannot be verified); log the specific exclusion reason for each dropped entry; ensure the output dataset includes a `measurement_source` field confirming the verified method
- [ ] T014b [US1] Implement computational independence check in `code/data_cleaning.py`: if `measurement_method` is missing but Young's Modulus and Bulk Modulus are available, calculate derived Poisson's ratio; if the derived value matches the reported value within 1% tolerance, EXCLUDE the entry as dependent; if Bulk Modulus is missing, exclude the entry; log the exclusion reason
- [ ] T011 [US1] Implement filtering logic in `code/data_cleaning.py` to select monolithic alloys with non-missing Poisson's ratio, Young's modulus, and Cu/Mg/Si/Zn/Mn composition (runs AFTER T014/T014b)
- [ ] T012 [US1] Implement unit normalization in `code/data_cleaning.py` (convert elastic constants to GPa, calculate atomic fractions summing to unity) (runs AFTER T014/T014b)
- [ ] T013 [US1] Implement exclusion logic in `code/data_cleaning.py` for entries where major element sum < 0.95 (log warning, drop row)
- [ ] T016 [US1] Implement main orchestration for data pipeline in `code/main.py` (run extraction -> cleaning -> save `data/processed/filtered_alloys.csv`); INCLUDE validation to HALT with a clear error message if valid entries < 50 (per spec.md Edge Cases); do not proceed to modeling if threshold not met
- [ ] T018 [US1] [DEPRECATED - logic moved to T016]

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Regression Model Training and Validation (Priority: P2)

**Goal**: Train a Random Forest regressor using ILR-transformed features, perform k-fold cross-validation, and evaluate on a held-out test set.

**Independent Test**: Can be fully tested by training the model on the filtered dataset, running 5-fold cross-validation, and verifying the mean absolute error is computed and logged on the held-out test set.

### Implementation for User Story 2

- [ ] T019 [US2] Implement ILR transformation in `code/data_cleaning.py` using the `compositional` package for Cu, Mg, Si, Zn, Mn atomic fractions (DEPENDS ON T012/T013 completion; operates on `data/processed/filtered_alloys.csv` produced by T016)
- [ ] T020 [US2] Implement feature vector construction in `code/modeling.py` (combine ILR features with target Poisson's ratio)
- [ ] T021 [US2] Implement a standard train/test split logic in `code/modeling.py` with fixed random seed (operates on the ILR-transformed feature set from T019)
- [ ] T022 [US2] Implement Random Forest training with k-fold cross-validation in `code/modeling.py` (log CV MAE)
- [ ] T023 [US2] Implement test set evaluation in `code/modeling.py` (compute and log test-set MAE)
- [ ] T024 [US2] Implement model serialization in `code/modeling.py` (save trained model to `models/rf_model.pkl`)
- [ ] T025 [US2] Implement results logging in `code/modeling.py` (save ModelMetrics to `docs/outputs/model_metrics.json`)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance and Associational Interpretation (Priority: P3)

**Goal**: Extract feature importance scores, back-transform to compositional space, compute VIF diagnostics, and frame findings as associational.

**Independent Test**: Can be fully tested by running the feature importance extraction and verifying the output contains ranked elements with non-zero importance scores and an associational framing statement.

### Implementation for User Story 3

- [ ] T026 [P] [US3] Implement feature importance extraction from Random Forest in `code/analysis.py`
- [ ] T027a [US3] Implement baseline Permutation Importance on ILR features in `code/analysis.py` (as mandated by plan.md Methodology Step 2)
- [ ] T027b [US3] Implement Perturbation-Based Sensitivity Analysis in `code/analysis.py` to map ILR-importance back to original elemental importance scores. DO NOT back-transform ILR splits (mathematically invalid per plan.md). Instead, perturb raw composition by adding independent Gaussian noise with standard deviation = 1% of the atomic fraction value to each element, re-transform to ILR, predict, and measure loss change to derive importance.
- [ ] T028 [US3] Implement VIF calculation in `code/analysis.py` for raw predictors (Cu, Mg, Si, Zn, Mn). Compute VIF and log values where VIF > 5 as expected diagnostic confirmation of collinearity in raw space (per plan.md Methodology Step 4). Do NOT halt pipeline.
- [ ] T029 [US3] Implement result ranking and comparison logic in `code/analysis.py` (identify top elements, compare magnitudes)
- [ ] T030 [US3] Implement final report generation in `code/main.py` (aggregate metrics, VIF, importance, and framing into `docs/outputs/final_report.md`); PROGRAMMATICALLY inject the exact phrase "associational, not causal" into every result statement in the generated reports by modifying the Markdown template before rendering; VERIFY that this phrase exists in all result sections via regex check before finalizing the report (per spec.md SC-005 and FR-008); if verification fails, raise an error to prevent report generation

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031a [P] Update `docs/quickstart.md` with new CLI flags for extraction and modeling steps
- [ ] T031b [P] Update `docs/data-model.md` with new schema fields for measurement provenance
- [ ] T031c [P] Update `docs/README.md` with updated execution steps and dependencies
- [ ] T032a [P] Remove unused imports in `code/` modules
- [ ] T032b [P] Enforce black formatting on all `code/` Python files
- [ ] T032c [P] Simplify nested loops in `code/data_cleaning.py` to maximum depth of 3
- [ ] T033a [P] Optimize data extraction runtime in `code/data_extraction.py` to target < 30s per source
- [ ] T033b [P] Optimize modeling runtime in `code/modeling.py` to target < 10min for full pipeline
- [ ] T033c [P] Reduce memory usage in `code/` to target < 4GB peak
- [ ] T034 [P] Unit tests for data cleaning logic in `tests/unit/test_data_cleaning.py`
- [ ] T035 [P] Unit tests for modeling logic in `tests/unit/test_modeling.py`
- [ ] T036 [P] Contract tests for data schemas in `tests/contract/test_schemas.py`
- [ ] T037 [P] Unit tests for analysis logic in `tests/unit/test_analysis.py`
- [ ] T045 [P] Run quickstart.md validation

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on T016 (clean data artifact)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on T024 (trained model)

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
# Launch all tasks for User Story 1 data extraction in parallel:
Task: "Implement data extraction for Materials Project in code/data_extraction.py"
Task: "Implement data extraction for NIST Materials Data Repository in code/data_extraction.py"
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
- Phase 6 (Computational Universe Exploration) has been removed as it constituted unmandated scope creep with no corresponding FR/SC in spec.md.
- T018 logic has been integrated into T016 to ensure hard failure on insufficient data.
- T014/T014b now precede T011/T012 to ensure invalid data is excluded before processing.
- T019 uses `compositional` package as per plan.md.
- T027a and T027b implement the full two-step importance strategy.
- T031, T032, T033 have been split into specific, executable tasks.