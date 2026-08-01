# Tasks: Predicting the Effect of Alloying on the Poisson's Ratio of Aluminum Alloys

**Input**: Design documents from `/specs/001-predict-poissons-ratio/`
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

 Tasks MUST be organized by user story so each user story can be independently implemented
 and tested.

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan
- [X] T002 Initialize Python 3.11 project with dependencies (pandas, numpy, scikit-learn, requests, pyyaml, seaborn, matplotlib, compositional, statsmodels, materialsproject, datasets) in `code/requirements.txt`. **Note**: OpenML dependency removed; replaced with `materialsproject` and `datasets` for dual-source acquisition per Spec FR-001.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/__init__.py` and basic project scaffolding
- [X] T005 [P] Setup environment configuration management in `code/config.py` (loading `data/`, `models/` paths, random seeds)
- [X] T006 [P] Implement logging infrastructure in `code/logging_config.py` (JSON logging, error levels)
- [X] T007 Create data schema definitions in `code/schemas/alloy_record.py` (Pydantic models for AlloyRecord, ModelMetrics). **Requirement**: The `measurement_method` field MUST be **REQUIRED** (not optional). If the field is missing in the raw data, the record is excluded immediately. (satisfies FR-009).
- [X] T008 Implement checksum utility in `code/utils/checksum.py` for verifying raw data integrity
- [X] T008b [P] Verify data source accessibility and semantic validity: Implement a script in `code/data_verification.py` to verify the accessibility of the target Materials Project and NIST APIs. Check network reachability AND verify that the API returns a valid data structure matching the expected schema (semantic verification). **Schema Check**: The API response MUST include the `measurement_method` field and the composition fields (Cu, Mg, Si, Zn, Mn). If the API is unreachable, returns invalid data, or lacks required fields, raise a `RuntimeError` with a clear message. (Note: This task does NOT satisfy Constitution Principle II; that is handled by the external Reference-Validator Agent). **DEPENDS ON T005**.
- [X] T008e [P] Validate `measurement_method` field existence: Implement a script to fetch the *raw* API response from both sources and verify the presence of the `measurement_method` field. If the field is missing in either source, raise a `RuntimeError` with a clear message "CRITICAL: `measurement_method` field missing in source schema. FR-009 cannot be satisfied." This task runs BEFORE download to prevent silent failures. **DEPENDS ON T005**.
- [X] T008c [P] Verify Normalized Schema: Implement a script to fetch the *normalized* merged data structure and validate it against `contracts/dataset.schema.yaml` using the `jsonschema` library. **Validation Target**: Validate the Python dictionary representing the normalized record, not the raw API wrapper. If the schema does not match, raise a `RuntimeError`. (Note: This task does NOT satisfy Constitution Principle II). **DEPENDS ON T008d**.
- [X] T009a [US1] Implement data extraction for Materials Project in `code/data/download.py`. **Endpoint**: Use `https://next-gen.materialsproject.org/api/v2/materials/` with query parameters `?elements=Al&property_ids=poisson_ratio&property_ids=young_modulus`. **Requirement**: This task implements the plan's dual-source strategy (FR-001). **Authentication**: The script MUST read `MP_API_KEY` from environment variables. If the API returns zero aluminum alloy entries with Poisson's ratio, **HALT** with a clear error message "CRITICAL: Materials Project returned zero valid entries. Pipeline halted." (Exit code 1). **DEPENDS ON T008b, T008e**.
- [X] T009b [US1] Implement data extraction for NIST in `code/data/download.py`. **Endpoint**: Use `datasets.load_dataset("nist_materials_data", split="train")` or a verified public CSV URL. **Requirement**: This task implements the plan's dual-source strategy (FR-001). If the fetch fails (network error or dataset not found), log a CRITICAL warning "NIST fetch failed. Proceeding with Materials Project only." and continue with the MP dataset. Do NOT halt the pipeline unless MP also fails. **DEPENDS ON T008b, T008e**.
- [X] T008d [US1] Implement dual-source merge logic: Create `code/data/merge.py` to combine data from Materials Project and NIST. **Requirement**: Deduplicate records based on alloy composition and property values. If a record exists in both sources with conflicting values, log a warning and prefer the source with the higher `measurement_method` quality flag (Ultrasonic > Derived). If the merged dataset has zero entries, raise a `RuntimeError`. **DEPENDS ON T009a, T009b**.
- [X] T010 [US1] Implement schema validation and initial filtering in `code/data/clean.py` to verify the raw data (from T009a/T009b/T008d) contains all required fields (Poisson's ratio, Young's modulus, Cu, Mg, Si, Zn, Mn, **measurement_method**). If any required field is missing or null in the raw data, raise a `ValueError` with a clear message listing the missing fields. **Note**: This task checks for the *presence* of the field name and a non-null value. **DEPENDS ON T008d**.
- [X] T014 [US1] Implement positive verification and exclusion logic in `code/data/clean.py` for FR-009: query the `measurement_method` field for each entry in the raw dataset.
 - **Logic**:
 - **Assumption**: T010 has already ensured the field exists and is non-null.
 - **Handling Missing Field**: If the `measurement_method` field is missing or null (should be caught by T010, but re-check for safety), **EXCLUDE** the entry and log warning "Missing measurement_method, excluding record" to `data/logs/independence_check.log`.
 - If the field value is 'Derived', 'calculated_from_Youngs_modulus', or 'calculated': **EXCLUDE** the entry and log warning "Derived measurement_method, excluding record" to `data/logs/independence_check.log`.
 - If the field value is 'Ultrasonic', 'Independent', or 'Direct Measurement': **KEEP** the entry.
 - **Logging**: Log the specific value found for excluded entries to `data/logs/independence_check.log`. **OUTPUT**: Generate `data/logs/independence_metrics.json` containing counts: `{"kept": N, "excluded_derived": N, "excluded_missing": N}` to satisfy SC-006.
 - **Output**: Ensure the output dataset includes a `measurement_source` field confirming the verified method.
 - **Dependency**: This task runs AFTER T010 (schema validation) and BEFORE T011 (filtering). **DEPENDS ON T010**.
- [X] T011 [US1] Implement filtering logic in `code/data/clean.py` to select monolithic alloys with non-missing Poisson's ratio, Young's modulus, and Cu/Mg/Si/Zn/Mn composition (runs AFTER T014). **Note**: Operates on the output of T014. **DEPENDS ON T014**.
- [X] T012 [US1] Implement unit normalization in `code/data/clean.py` (convert elastic constants to GPa, calculate atomic fractions summing to unity) (runs AFTER T011, operates on the output of T011). **DEPENDS ON T011**.
- [X] T013 [US1] Implement exclusion logic in `code/data/clean.py` for entries where major element sum < 0.95 (log warning, drop row) (runs AFTER T012, operates on the the output of T012). **Note**: T013 must run after T012 to ensure the sum check is performed on normalized atomic fractions. **DEPENDS ON T012**.
- [X] T018 [US1] Implement final validation and orchestration in `code/data/clean.py` (run full pipeline -> save `data/processed/alloys_clean.parquet`). INCLUDE validation to HALT with a clear error message if valid entries == 0 (per spec Edge Cases). **Exit code MUST be 1 and error message MUST be "CRITICAL: No valid entries found after filtering. Pipeline halted."** if valid entries == 0. **Logic**: If valid entries < 50, **HALT** with a clear error message "CRITICAL: Insufficient data (<50 entries). Pipeline halted." (Exit code 1). **Do NOT proceed with model complexity adjustment**. Ensure the file `data/processed/alloys_clean.parquet` is actually created and contains >0 rows before exiting. **DEPENDS ON T014, T013**.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 2b: CLI Orchestration (Enabling Independent Testing)

**Purpose**: Provide CLI entry points for US1 and US2 to enable independent testing before US3 is complete.

- [X] T045 [US1] Implement CLI entry point for data extraction: Create the script `code/cli/download_cli.py` that orchestrates the data extraction steps (T009a, T009b, T008d). This script MUST be callable from the CLI as referenced in `docs/quickstart.md` with flags `--extract`. It must import the core logic functions from `code/data/download.py` and `code/data/merge.py`. **DEPENDS ON T009a, T009b, T008d**.
- [X] T046 [US1] Implement CLI entry point for data cleaning: Create the script `code/cli/clean_cli.py` that orchestrates the data cleaning steps (T010, T014, T011, T012, T013, T018). This script MUST be callable from the CLI as referenced in `docs/quickstart.md` with flags `--clean`. It must import the core logic functions from `code/data/clean.py`. **DEPENDS ON T010, T014, T011, T012, T013, T018**.

**Checkpoint**: CLI access to US1 and US2 is now available.

---

## Phase 3: User Story 2 - Regression Model Training and Validation (Priority: P2)

**Goal**: Train a Random Forest regressor using ILR-transformed features, perform k-fold cross-validation, and evaluate on a held-out test set.

**Independent Test**: Can be fully tested by training the model on the filtered dataset, running 5-fold cross-validation, and verifying the mean absolute error is computed and logged on the held-out test set.

### Implementation for User Story 2

- [X] T019 [US2] Implement ILR transformation in `code/data/clean.py` using the `compositional` package's `ilr` function for Cu, Mg, Si, Zn, Mn atomic fractions (DEPENDS ON T018 artifact; operates on `data/processed/alloys_clean.parquet` produced by T018). **Output**: `data/processed/alloys_ilr.parquet` containing the transformed features. **Verification**: Verify the output file exists, contains the expected ILR columns, and has >0 rows. **DEPENDS ON T018**.
- [X] T021 [US2] Implement Stratified Train/Test Split: Implement a script in `code/modeling.py` to perform an 80/20 split on the **ILR-transformed data** (from `data/processed/alloys_ilr.parquet` produced by T019).
 - **Logic**:
 - Use `train_test_split` with `stratify` on binned Poisson's ratio values (target variable) to ensure chemical space representation.
 - **Parameters**: Set `test_size=0.2`, `random_state=42`, and `stratify` on 4 bins of the target variable.
 - **Requirement**: Explicitly set `test_size=0.2` to ensure 80/20 ratio as per FR-005.
 - **Output**: `data/processed/train_split.parquet`, `data/processed/test_split.parquet`.
 - **DEPENDS ON T019**.
- [X] T022 [US2] Implement Random Forest training with k-fold cross-validation in `code/modeling.py` (log CV MAE). **DEPENDS ON T021**.
- [X] T023 [US2] Implement test set evaluation in `code/modeling.py` (compute and log test-set MAE). **DEPENDS ON T022**.
- [X] T024 [US2] Implement model serialization in `code/modeling.py` (save trained model to `models/rf_model.pkl` and verify file creation). **DEPENDS ON T022**.
- [X] T025b [US2] Implement results logging in `code/modeling.py` (save ModelMetrics to `results/metrics.json`). **DEPENDS ON T023, T022**. The JSON schema MUST include `cv_mae` and `test_mae` fields.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Feature Importance and Associational Interpretation (Priority: P3)

**Goal**: Extract feature importance scores, back-transform to compositional space, compute VIF diagnostics, and frame findings as associational.

**Independent Test**: Can be fully tested by running the feature importance extraction and verifying the output contains ranked elements with non-zero importance scores and an associational framing statement.

### Implementation for User Story 3

- [X] T026 [P] [US3] Implement feature importance extraction from Random Forest in `code/analysis.py` (satisfies FR-006).
- [X] T027a [US3] Implement **baseline Permutation Importance on ILR features** in `code/analysis.py` (as mandated by plan.md Methodology Step 2). This must be a distinct, verifiable unit. Run permutation importance on the ILR-transformed features, save the scores to `results/baseline_permutation_importance.csv`, and log the results. **DEPENDS ON T024**.
- [X] T027b [US3] Implement Perturbation-Based Sensitivity Analysis in `code/analysis.py` to map ILR-importance back to original elemental importance scores. DO NOT back-transform ILR splits (mathematically invalid per plan.md). Instead, perturb **raw composition** (read from `data/processed/alloys_clean.parquet` from T018) by adding independent Gaussian noise with standard deviation = 1% of the atomic fraction value (sigma=0.01) to each element, re-transform to ILR, predict, and measure loss change to derive importance. **Algorithm**: For each element `e`, compute `Importance(e) = mean(|Prediction(original) - Prediction(noised_e)|)`. **Aggregation**: Sort elements by `Importance(e)` in descending order to produce the final ranking. **Compare results against the baseline from T027a**. Save importance scores to `results/element_importance.csv` with columns: `element`, `importance_score`, `std_dev`. **Requirement**: Use `random_state=42` for noise generation. **Verification**: Verify `results/element_importance.csv` exists, has 5 rows, and contains the specified columns. **DEPENDS ON T018, T027a**.
- [X] T028 [US3] Implement VIF calculation in `code/analysis.py` for raw predictors (satisfies FR-007, SC-004). **Exclude the Al balance** from the calculation to avoid infinite VIF values (per plan.md Methodology Step 4). Compute VIF for Cu, Mg, Si, Zn, Mn only. **Generate a log flag for each predictor with VIF > 5** as required by FR-007, but do NOT halt the pipeline (per plan.md clarification). **DEPENDS ON T018**.
- [X] T029 [US3] Implement result ranking and comparison logic in `code/analysis.py` (identify top elements, compare magnitudes) (satisfies SC-003). **DEPENDS ON T027b**.
- [X] T030a [US3] Implement final report generation in `code/main.py` (aggregate metrics, VIF, importance, and framing into `results/final_report.md`); **CREATE** the `results/final_report.md` file with a defined Markdown structure including sections: "1. Executive Summary", "2. Data Quality & Independence", "3. Model Performance", "4. Feature Importance (Compositional)", "5. Diagnostics (VIF)", "6. Limitations & Associational Framing". Ensure the report naturally frames all predictive findings as associational (not causal) by explicitly referencing the observational nature of the data, the lack of randomization, and the limitations of the dataset (satisfies FR-008, SC-005). **Verification**: Verify `results/final_report.md` exists and contains the "6. Limitations & Associational Framing" section with the required text. **DEPENDS ON T029, T027b, T028**.
- [X] T030b [US3] Implement associational framing verification in `code/analysis.py`. **Logic**: Scan `results/final_report.md` for the **presence** of the "6. Limitations & Associational Framing" section. **Content Requirement**: The section MUST contain the explicit statement: "This study is observational; findings represent statistical associations, not causal relationships." **Output**: Generate `results/associational_framing_check.json` containing a boolean `framing_verified` and a list of any missing required content. If the section or statement is missing, set `framing_verified` to false. **Requirement**: This task expects `results/final_report.md` to exist (produced by T030a). **DEPENDS ON T030a**.
- [X] T044 [P] Run quickstart.md validation: Execute all code blocks in `docs/quickstart.md` and verify CLI flags match implementation.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T032 [P] Update `docs/quickstart.md` with new CLI flags for extraction and modeling steps. **Requirement**: Update CLI help text to include `--extract`, `--train`, `--analyze` flags. **DEPENDS ON T045, T046**.
- [X] T033 [P] Update `docs/data-model.md` with new schema fields for measurement provenance.
- [X] T034 [P] Update `docs/README.md` with updated execution steps and dependencies.
- [X] T035 [P] Run `ruff check --fix code/` to remove unused imports and enforce linting rules.
- [X] T036 [P] Run `black code/` to enforce formatting on all Python files.
- [X] T037 [P] Simplify nested loops in `code/data/clean.py` to a maximum depth parameter. **Target**: Refactor any loops exceeding **multiple levels deep** in the data cleaning logic.
- [X] T038 [P] Optimize data extraction runtime in `code/data/download.py` to target < 30s per source.
- [X] T039 [P] Optimize modeling runtime in `code/modeling.py` to target < 10min for full pipeline.
- [X] T040 [P] Unit tests for data cleaning logic in `tests/unit/test_data_cleaning.py`. **Requirement**: Write unit tests covering branches for T010, T014, T013 and verify coverage report shows [deferred] branch coverage for these functions.
- [X] T041 [P] Unit tests for modeling logic in `tests/unit/test_modeling.py`.
- [X] T042 [P] Contract tests for data schemas in `tests/contract/test_schemas.py`.
- [X] T043 [P] Unit tests for analysis logic in `tests/unit/test_analysis.py`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **CLI Orchestration (Phase 2b)**: Depends on Phase 2 completion - enables independent testing
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on T018 (clean data artifact)
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
Task: "Implement data extraction for Materials Project in code/data/download.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 2b: CLI Orchestration
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently via CLI
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add CLI Orchestration → Enable testing
3. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
4. Add User Story 2 → Test independently → Deploy/Demo
5. Add User Story 3 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

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
- T009a/T009b updated to enforce strict MP/NIST requirement with halt-on-zero logic and valid URLs.
- T014 updated to handle missing `measurement_method` field.
- T017a-d removed (redundant pipeline).
- T030 split into T030a (generate) and T030b (verify).
- T045/T046 moved to Phase 2b (CLI Orchestration) to enable early testing and separated into `code/cli/` to avoid naming conflicts.
- T047 (Computational Irreducibility) removed as it is an orphan task not required by the Spec or Plan.
- T021 updated to use simple stratified split on target variable.
- T007 updated to make `measurement_method` REQUIRED.
- T018 dependencies updated to include T014 and T013. Output format updated to Parquet.
- **Phase 5 (T050, T051) removed**: Removed as it was scope creep not authorized by the Spec.
- **File Path Alignment**: All tasks now reference `code/data/clean.py`, `code/data/download.py`, and `code/data/merge.py` to match the Plan.md Project Structure (with `merge.py` explicitly added).
- **T027b Updated**: Explicitly defined the perturbation algorithm and ranking logic (mean absolute loss -> sort descending) to ensure deterministic implementation. Added verification step.
- **T030b Updated**: Replaced brittle keyword regex with a semantic check for a specific "Limitations" section containing the required associational disclaimer.
- **T019 Updated**: Corrected input/output file paths to match T018 output and added verification step.
- **T045/T046 Updated**: Moved to Phase 2b and separated CLI scripts from logic modules. Fixed import paths to `code/data/download.py`, `code/data/merge.py`, and `code/data/clean.py`.
- **T008d Updated**: Moved to after T009a/T009b to fix ordering.
- **T018 Updated**: Removed fallback logic for <50 entries; now halts with error.
- **Plan Note**: Plan.md updated to remove OpenML mandate and align with Spec FR-001 dual-source requirement.
- **T008e Added**: Added to validate `measurement_method` field existence before download.
- **T009b Updated**: Replaced fake URL with `datasets.load_dataset` or verified CSV path with fallback logic.
- **T008c Updated**: Moved after T008d to fix ordering.
- **T030a Updated**: Clarified generation logic to ensure framing text is included.