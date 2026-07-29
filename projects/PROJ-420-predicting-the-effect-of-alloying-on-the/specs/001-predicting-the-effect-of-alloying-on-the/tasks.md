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

 Tasks MUST be organized by user story so each story can be independently implemented
 and tested.

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan
- [X] T002 Initialize Python 3.11 project with dependencies (pandas, numpy, scikit-learn, requests, pyyaml, seaborn, matplotlib, compositional, statsmodels, openml, materialsproject, requests) in `code/requirements.txt`
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/__init__.py` and basic project scaffolding
- [X] T005 [P] Setup environment configuration management in `code/config.py` (loading `data/`, `models/` paths, random seeds)
- [X] T006 [P] Implement logging infrastructure in `code/logging_config.py` (JSON logging, error levels)
- [X] T007 Create data schema definitions in `code/schemas/alloy_record.py` (Pydantic models for AlloyRecord, ModelMetrics) including `measurement_method` as a **REQUIRED** field for independence verification (FR-009). If the field is missing in the source data, the record must be excluded.
- [X] T008 Implement checksum utility in `code/utils/checksum.py` for verifying raw data integrity
- [X] T008b [P] Verify data source accessibility: Implement a script in `code/data_extraction.py` (or standalone) to verify the accessibility of the target OpenML dataset (ID: 42347), Materials Project API, and NIST repository endpoints. Check that they contain the required schema fields: Poisson's ratio, Young's modulus, Cu, Mg, Si, Zn, Mn. If any source is unreachable or missing required fields, raise a `RuntimeError` with a clear message listing the failed source. (satisfies Constitution Principle II).
- [X] T008c Generate `data/verified_sources.yaml`. Create a YAML file defining the canonical sources for this project: `sources: [ {id: "openml", value: "<openml_id>"}, {id: "materials_project", value: "mp-123"}, {id: "nist", value: "nist-repo-id"} ]`. Include a comment instructing the researcher that this is the single source of truth per `plan.md` Phase 0. **DEPENDS ON T008b**.
- [X] T009a [US1] Implement data extraction for Materials Project in `code/data_extraction.py` (fetch dataset via Materials Project API; validate against AlloyRecord schema from T007; save to `data/raw/mp_aluminum.json`). **Requirement**: This task implements the plan's multi-source strategy. If the API returns zero aluminum alloy entries with Poisson's ratio, the script MUST halt with error "CRITICAL: Materials Project returned zero valid aluminum alloy entries. Pipeline halted per spec Edge Cases." (satisfies FR-001 and Edge Cases).
- [X] T009b [US1] Implement data extraction for NIST Materials Data Repository in `code/data_extraction.py` (fetch dataset via NIST API/URL; validate against AlloyRecord schema from T007; save to `data/raw/nist_aluminum.json`). **Requirement**: This task implements the plan's multi-source strategy. If the API returns zero aluminum alloy entries with Poisson's ratio, the script MUST halt with error "CRITICAL: NIST Repository returned zero valid aluminum alloy entries. Pipeline halted per spec Edge Cases." (satisfies FR-001 and Edge Cases).
- [ ] T009c [US1] Implement data extraction for an OpenML dataset in `code/data_extraction.py` (fetch dataset via `openml.datasets.get_dataset()`).; validate against AlloyRecord schema from T007; save to `data/raw/openml_aluminum.json`). **Requirement**: This task implements the plan's multi-source strategy. If the API returns zero aluminum alloy entries with Poisson's ratio, the script MUST halt with error "CRITICAL: OpenML dataset 42347 returned zero valid aluminum alloy entries. Pipeline halted per spec Edge Cases." (satisfies FR-001 and Edge Cases).
- [X] T010 [US1] Implement schema validation in `code/data_cleaning.py` to verify the downloaded data (from T009a, T009b, T009c) contains all required fields (Poisson's ratio, Young's modulus, Cu, Mg, Si, Zn, Mn). If any required field is missing in the raw data, raise a `ValueError` with a clear message listing the missing fields. **Note**: This task checks for the *presence* of the field name in the schema, not the *value* (null/missing).
- [ ] T014 [US1] Implement positive verification and exclusion logic in `code/data_cleaning.py` for FR-009: query the `measurement_method` field for each entry.
 - **Logic**: 
   - If the field is **MISSING** (not present in the row): **HALT** with error "CRITICAL: `measurement_method` field is missing in source data. Verification failed per spec Edge Cases." (Do not proceed).
   - If the field is **PRESENT** but value is 'missing', 'null', or empty: **HALT** with error "CRITICAL: `measurement_method` value is missing/null. Verification failed per spec Edge Cases."
   - If the field is **PRESENT** and value indicates 'Derived' from Young's modulus or is explicitly 'calculated_from_Youngs_modulus': **EXCLUDE** the entry.
   - If the field is **PRESENT** and value is 'Ultrasonic' or 'Independent': **KEEP** the entry.
 - **Logging**: Log the specific value found for excluded entries to `data/logs/independence_check.log`.
 - **Output**: Ensure the output dataset includes a `measurement_source` field confirming the verified method.
 - **Dependency**: This task runs AFTER T010 (schema validation) and BEFORE T012 (unit normalization) to avoid wasting compute on invalid records.
- [X] T011 [US1] Implement filtering logic in `code/data_cleaning.py` to select monolithic alloys with non-missing Poisson's ratio, Young's modulus, and Cu/Mg/Si/Zn/Mn composition (runs AFTER T014). **Note**: Operates on the filtered output of T014.
- [X] T012 [US1] Implement unit normalization in `code/data_cleaning.py` (convert elastic constants to GPa, calculate atomic fractions summing to unity) (runs AFTER T014, operates on the filtered output of T014).
- [X] T013 [US1] Implement exclusion logic in `code/data_cleaning.py` for entries where major element sum < 0.95 (log warning, drop row) (runs AFTER T014, operates on the filtered output of T014).
- [ ] T016 [US1] Implement data extraction orchestration in `code/main.py` (run T009a, T009b, T009c extraction functions). **Output**: Intermediate raw files `data/raw/mp_aluminum.json`, `data/raw/nist_aluminum.json`, `data/raw/openml_aluminum.json`. **DEPENDS ON T009a, T009b, T009c**.
- [ ] T017 [US1] Implement cleaning pipeline in `code/main.py` (run T010, T014, T011, T012, T013 logic on raw data). **Execution Order**: T010 -> T014 -> T011 -> T012 -> T013. **Output**: `data/processed/filtered_alloys.csv`.
- [ ] T018 [US1] Implement final validation and orchestration in `code/main.py` (run full pipeline -> save `data/processed/filtered_alloys.csv`). INCLUDE validation to HALT with a clear error message if valid entries == 0 (per spec Edge Cases). **Exit code MUST be 1 and error message MUST be "CRITICAL: No valid entries found. Pipeline halted."** if valid entries == 0. **Logic**: If valid entries < 50, **LOG A WARNING** "Sample size < 50: Limiting model complexity per plan.md Assumptions" and set `max_depth=5`. Do NOT halt for < 50 entries. Ensure the file `data/processed/filtered_alloys.csv` is actually created and contains >0 rows before exiting.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Regression Model Training and Validation (Priority: P2)

**Goal**: Train a Random Forest regressor using ILR-transformed features, perform k-fold cross-validation, and evaluate on a held-out test set.

**Independent Test**: Can be fully tested by training the model on the filtered dataset, running 5-fold cross-validation, and verifying the mean absolute error is computed and logged on the held-out test set.

### Implementation for User Story 2

- [ ] T019 [US2] Implement ILR transformation in `code/data_cleaning.py` using the `compositional` package's `ilr` function for Cu, Mg, Si, Zn, Mn atomic fractions (DEPENDS ON T012/T013 completion; operates on `data/processed/filtered_alloys.csv` produced by T016/T017). **Output**: `data/processed/filtered_alloys_ilr.csv` containing the transformed features. **Note**: This task depends on the successful completion of T017 and the existence of `data/processed/filtered_alloys.csv`.
- [X] T020 [US2] Implement feature vector construction in `code/modeling.py` (combine ILR features with target Poisson's ratio).
- [X] T021 [US2] Implement a **train/test split** logic in `code/modeling.py` with fixed random seed (operates on the ILR-transformed feature set from T019). **Requirement**: Explicitly set `test_size=0.2` to ensure 80/20 ratio as per FR-005.
- [X] T022 [US2] Implement Random Forest training with k-fold cross-validation in `code/modeling.py` (log CV MAE).
- [X] T023 [US2] Implement test set evaluation in `code/modeling.py` (compute and log test-set MAE).
- [X] T024 [US2] Implement model serialization in `code/modeling.py` (save trained model to `models/rf_model.pkl` and verify file creation).
- [X] T025b [US2] Implement results logging in `code/modeling.py` (save ModelMetrics to `results/metrics.json`). **DEPENDS ON T023, T022**. The JSON schema MUST include `cv_mae` and `test_mae` fields.

**Checkpoint**: At this point, At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Feature Importance and Associational Interpretation (Priority: P3)

**Goal**: Extract feature importance scores, back-transform to compositional space, compute VIF diagnostics, and frame findings as associational.

**Independent Test**: Can be fully tested by running the feature importance extraction and verifying the output contains ranked elements with non-zero importance scores and an associational framing statement.

### Implementation for User Story 3

- [X] T026 [P] [US3] Implement feature importance extraction from Random Forest in `code/analysis.py`
- [X] T027a [US3] Implement **baseline Permutation Importance on ILR features** in `code/analysis.py` (as mandated by plan.md Methodology Step 2). This must be a distinct, verifiable unit. Run permutation importance on the ILR-transformed features, save the scores to `results/baseline_permutation_importance.csv`, and log the results.
- [X] T027b [US3] Implement Perturbation-Based Sensitivity Analysis in `code/analysis.py` to map ILR-importance back to original elemental importance scores. DO NOT back-transform ILR splits (mathematically invalid per plan.md). Instead, perturb raw composition by adding independent Gaussian noise with standard deviation = 1% of the atomic fraction value to each element, re-transform to ILR, predict, and measure loss change to derive importance. **Compare results against the baseline from T027a**. Save importance scores to `results/element_importance.csv`.
- [X] T028 [US3] Implement VIF calculation in `code/analysis.py` for raw predictors. **Exclude the Al balance** from the calculation to avoid infinite VIF values (per plan.md Methodology Step 4). Compute VIF for Cu, Mg, Si, Zn, Mn only. **Generate a log flag for each predictor with VIF > 5** as required by FR-007, but do NOT halt the pipeline (per plan.md clarification).
- [X] T029 [US3] Implement result ranking and comparison logic in `code/analysis.py` (identify top elements, compare magnitudes)
- [ ] T030 [US3] Implement final report generation in `code/main.py` (aggregate metrics, VIF, importance, and framing into `results/final_report.md`); **CREATE** the `results/final_report.md` file with a defined Markdown structure including sections for Results, Diagnostics, and Framing. Ensure the report naturally frames all predictive findings as associational (not causal) by explicitly referencing the observational nature of the data, the lack of randomization, and the limitations of the dataset. **Verification**: Generate `results/associational_framing_check.json` containing a boolean `framing_verified` and a list of any detected causal phrases (e.g., "causes", "leads to") found in the report. If any causal phrases are detected, set `framing_verified` to false.
 **Dependency**: Runs after T027b and T028.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T031a [P] Update `docs/quickstart.md` with new CLI flags for extraction and modeling steps
- [X] T031b [P] Update `docs/data-model.md` with new schema fields for measurement provenance
- [X] T031c [P] Update `docs/README.md` with updated execution steps and dependencies
- [X] T032a [P] Run `ruff check --fix code/` to remove unused imports and enforce linting rules
- [X] T032b [P] Run `black code/` to enforce formatting on all Python files
- [X] T032c [P] Simplify nested loops in `code/data_cleaning.py` to a maximum depth parameter. **Target**: Refactor any loops exceeding depth 2 in the data cleaning logic.
- [X] T033a [P] Optimize data extraction runtime in `code/data_extraction.py` to target < 30s per source
- [X] T033b [P] Optimize modeling runtime in `code/modeling.py` to target < 10min for full pipeline
- [ ] T034 [P] Unit tests for data cleaning logic in `tests/unit/test_data_cleaning.py`. **Requirement**: Achieve comprehensive branch coverage on filtering logic (T010, T014, T013).
- [X] T035 [P] Unit tests for modeling logic in `tests/unit/test_modeling.py`
- [X] T036 [P] Contract tests for data schemas in `tests/contract/test_schemas.py`
- [X] T037 [P] Unit tests for analysis logic in `tests/unit/test_analysis.py`
- [X] T045 [P] Run quickstart.md validation: Execute all code blocks in `docs/quickstart.md` and verify CLI flags match implementation.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on T016/T017 (clean data artifact)
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
Task: "Implement data extraction for OpenML in code/data_extraction.py"
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
- [Story] label maps task to traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- T009a/T009b added to align with spec FR-001 multi-source requirement.
- T014 now uses strict logic for measurement_method validation: HALT on missing, EXCLUDE on Derived.
- T018 now includes <50 warning (not halt) logic.
- T030 now includes `results/associational_framing_check.json` for objective verification.
- Phase O (Computational Universe) removed as unauthorized scope creep.
- T019 now explicitly defines ILR implementation path and output artifact.
- T032c and T034 clarified with specific targets.
- T017 execution order corrected to T010 -> T014 -> T011 -> T012 -> T013.
- T009a/T009b/T009c status corrected to active extraction tasks.
- T016/T017/T018 marked pending to await implementation of dependencies.
- T021 explicitly mandates 80/20 split.

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [X] T046 Reconcile run-book vs implementation for `code/data/download.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/data/download.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [X] T047 Reconcile run-book vs implementation for `code/data/clean.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/data/clean.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.