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
- [X] T002 Initialize a Python project with dependencies (pandas, numpy, scikit-learn, requests, pyyaml, seaborn, matplotlib, compositional, statsmodels, datasets, periodictable, joblib, pytest, pytest-cov, ruff, black, shap) in `code/requirements.txt`.
- [X] T003 [P] Configure linting (ruff==0.1.6) and formatting (black==23.12.1) tools in `code/` using `pyproject.toml` as the configuration source.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/__init__.py` and basic project scaffolding
- [X] T005 [P] Setup environment configuration management in `code/config.py` (loading `data/`, `models/`, `results/` paths, random seeds, `VALID_MEASUREMENT_METHODS` regex list).
- [X] T006 [P] Implement logging infrastructure in `code/logging_config.py` (JSON logging, error levels).
- [X] T007 Create data schema definitions in `code/schemas/alloy_record.py` (Pydantic models for AlloyRecord, ModelMetrics). **Requirement**: The `measurement_method` field MUST be **Required** in the schema. If the field is missing in the raw data, the record is excluded immediately. (satisfies FR-009).
- [X] T008 Implement checksum utility in `code/utils/checksum.py` for verifying raw data integrity.
- [X] T008d [P] Implement Merge & Deduplicate logic in `code/merge.py`. **Deduplication Logic**: Merge on exact match of normalized atomic fractions (tolerance within a negligible range) and Young's Modulus (tolerance within a negligible range). **Conflict Resolution**: If duplicates exist, prefer the record where `measurement_method` string contains 'Ultrasonic' or 'Direct'; if both or neither, prefer the source 'NIST' over 'Materials Project'. (satisfies FR-001).
- [X] T008b [P] Implement Data Source Verification: Consolidate API checks into a single script `code/data_verification.py`. **Logic**: 1) Verify network reachability of MP and NIST. 2) Verify raw API response structure (JSON paths for `poisson_ratio`, `composition`, `young_modulus`, `measurement_method`). 3) **Validate the normalized merged structure against `contracts/dataset.schema.yaml`**. **Verification Step**: Before validation, **verify that `contracts/dataset.schema.yaml` exists and explicitly defines the fields required for the merged dataset (Cu, Mg, Si, Zn, Mn, poisson_ratio, young_modulus, etc.)**. If the schema is missing or incomplete, raise `RuntimeError`. **Fail Condition**: If any check fails, raise `RuntimeError` with a clear message. (Replaces T008c, T008e).
- [X] T009 [US1] Implement data extraction for Materials Project in `code/_download_logic.py`. **Endpoint**: Use `https://next-gen.materialsproject.org/api/v2/materials/` with query parameters `?elements=Al&property_ids=poisson_ratio&property_ids=young_modulus`. **Authentication**: The script MUST read `MP_API_KEY` from environment variables. **Logic**: Fetch data. **HALT CONDITION**: If zero entries found, raise `RuntimeError("CRITICAL: Materials Project returned zero entries. Cannot proceed.")`. (satisfies FR-001).
- [X] T009b [US1] Implement data extraction for NIST in `code/_download_logic.py`. **Requirement**: This task implements the plan's verified source strategy (FR-001). **Dataset**: Use `datasets.load_dataset("materials/alloy-elastic", split="train")`. **Verification**: The script MUST verify that the dataset ID corresponds to the canonical `materials/alloy-elastic` dataset by checking `ds.info.config_name`. **Code Snippet**: `ds = datasets.load_dataset("materials/alloy-elastic", split="train"); assert ds.info.config_name == "materials/alloy-elastic"`. **Logic**: Fetch data. **HALT CONDITION**: If the dataset is unavailable (e.g., 404, timeout) or returns zero entries, raise `RuntimeError("CRITICAL: Verified source 'materials/alloy-elastic' unavailable or empty. Cannot proceed.")`. Do NOT fallback to guessing URLs. (satisfies FR-001, resolves Edge Case).
- [X] T014 [US1] Implement independence verification in `code/data/clean.py`. **Requirement**: If `measurement_method` is missing/null in the raw data, **EXCLUDE** the record immediately. **Logic**: 1) Check if `measurement_method` is present and non-null. 2) If missing, exclude row with log warning 'missing_measurement_method'. 3) If present, verify it matches `VALID_MEASUREMENT_METHODS` (Ultrasonic, Direct, Resonant, Impulse). 4) If not matching, exclude row with log warning 'invalid_measurement_method'. **Traceability**: This task explicitly implements the strict verification requirement of `spec.md` FR-009. **Constraint**: No inference logic is permitted. **Output**: Append to `data/logs/exclusion_log.txt` with reason 'missing_measurement_method' or 'invalid_measurement_method'. **Note**: This task MUST run BEFORE T010 and T011 to ensure the field is populated or the record excluded before downstream processing. **Verification**: 1) Assert that records with missing methods are NOT in the output parquet. 2) Assert `data/logs/exclusion_log.txt` contains entries for failed verifications. (satisfies FR-009, resolves T010/T014 conflict).
- [X] T010 [US1] Implement data extraction validation in `code/data/clean.py`. **Requirement**: Verify the raw data (from T009, T009b) contains all required fields (Poisson's ratio, Young's modulus, Cu, Mg, Si, Zn, Mn, **measurement_method**) at the **schema level**. **Field Mappings**: Map `poisson_ratio` -> `poisson_ratio`, `young_modulus` -> `young_modulus`, `elements` -> `composition` (dict). **Logic**: If a required field is missing from the **schema**, raise a `ValueError`. If a field is present but **null/missing for a specific row**, do NOT raise; defer handling to T014 (which excludes such rows). (satisfies FR-009, resolves T010/T014 conflict).
- [X] T011 [US1] Implement monolithic filtering in `code/data/clean.py`. **Definition**: `alloy_type == 'monolithic'` OR `is_composite == False` OR `composite_fraction == 0.0`. **Priority**: Check `alloy_type` first, then `is_composite`, then `composite_fraction`. If neither field exists, the record is excluded. (satisfies FR-002).
- [X] T012 [US1] Implement unit normalization in `code/data/clean.py`. **Source Units**: Detect if `composition` is in wt% or at%. If wt%, convert to at% using atomic weights from `periodictable` package. If at%, verify sum is ~1.0. `young_modulus` expected in GPa (convert from MPa using the standard conversion factor). (satisfies FR-003).
- [X] T013 [US1] Implement exclusion logic in `code/data/clean.py` for entries where major element sum < 0.95. **Calculation**: `major_sum = sum(Cu, Mg, Si, Zn, Mn)` in atomic fractions. **Al Balance**: `Al balance = 1.0 - major_sum`. If `major_sum < 0.95`, exclude row with log warning. (satisfies FR-003).
- [X] T016 [P] [US1] Implement exclusion logging utility in `code/data/clean.py`. **Purpose**: Standalone utility function. **Logic**: Append exclusion records to `data/logs/exclusion_log.txt` (CSV format: `step,count,reason`). **Output**: `data/logs/exclusion_log.txt`. (satisfies T018b, resolves circular dependency).
- [X] T015 [US1] Implement final validation and orchestration in `code/data/clean.py`. **Requirement**: Orchestrate the full pipeline (T014-T016). **Step 1**: Run T014-T016 functions in sequence. **Step 2**: Invoke T016 utility to ensure all exclusions are logged. **Step 3**: Read `data/logs/exclusion_log.txt` (Schema: CSV with columns `step,count,reason`) and count valid rows in the final dataset. **Step 4**: If row count < 50, **HALT** with error "Insufficient data after filtering (<50 entries)" and `sys.exit(1)`. **Step 5**: If count >= 50, save the cleaned dataset to `data/processed/alloys_clean.parquet`. **Output**: `data/processed/alloys_clean.parquet` (ONLY if count >= 50). **Blocked by**: T014, T016. **Verification**: 1) Verify `sys.exit(1)` is called and error message logged if row count < 50. 2) Assert `data/processed/alloys_clean.parquet` exists and matches schema if count >= 50. (satisfies SC-001, resolves T018 conflict).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Regression Model Training and Validation (Priority: P2)

- [X] T019 [US2] Implement ILR transformation in `code/data/clean.py` using the `compositional.ilr` function for Cu, Mg, Si, Zn, Mn atomic fractions. **Order**: Fixed order `['Cu', 'Mg', 'Si', 'Zn', 'Mn']` to ensure reproducibility.
- [X] T022 [US2] Implement Random Forest training with k-fold cross-validation in `code/modeling.py`. **Hyperparameters**: `n_estimators=100`, `max_depth=None`, `random_state=42`.
- [X] T021 [US2] Implement Repeated 5-Fold Cross-Validation in `code/modeling.py`. **Logic**: Perform multiple repeats of k-fold CV. **Architectural Decision**: This is the **primary** validation strategy per `plan.md` (to handle small datasets). **Output**: Compute and log mean CV-MAE and confidence intervals. Save to `results/model_metrics.json` (to be aggregated by T023d). **Verification**: Assert `results/model_metrics.json` contains `cv_mae` and `cv_ci` fields with numeric values. (satisfies Plan Phase 2).
- [X] T025 [US2] Implement 80/20 Held-Out Test Set Split in `code/modeling.py`. **Requirement**: This task satisfies the Spec's FR-005 and US2 Scenario 3 which mandate a held-out test set. **Architectural Decision**: The Spec's FR-005 takes precedence over the Plan's text regarding "no single held-out set". **Logic**: Perform a split on the full dataset (stratified if possible). Train a separate RF on the training set and evaluate on the test set. **Output**: Compute and log Test-Set MAE. Save to `results/model_metrics.json` (to be aggregated by T023d). **Verification**: Assert `results/model_metrics.json` contains `test_mae` field. (satisfies FR-005, resolves Spec/Plan contradiction by implementing both with clear priority).
- [X] T023c [US2] Implement MAE Calculation and Logging: In `code/modeling.py`, compute the cross-validation MAE and the held-out test MAE (from T025). Check if CV MAE > 0.05. **Condition**: Set `mae_flag` to `True` if `cv_mae > 0.05`. **Logic**: If `mae_flag` is True, ensure `results/` directory exists (`os.makedirs('results', exist_ok=True)`) and write a flag to `results/methodological_flags.json` (create if needed) to be consumed by the report generator (T030a). **Output**: `results/methodological_flags.json`. **Verification**: Assert `results/methodological_flags.json` exists and contains `mae_flag` boolean. (satisfies Edge Cases, resolves T023c path issue).
- [X] T023d [US2] Aggregate Model Metrics: Combine outputs from T021 and T025 into a single file `results/model_metrics.json`. **Schema**: JSON object containing `cv_mae`, `cv_ci_lower`, `cv_ci_upper`, `test_mae`. **Output**: `results/model_metrics.json`. **Verification**: Assert `results/model_metrics.json` matches `contracts/model_metrics.schema.yaml`. (Required for T030a).
- [X] T024 [US2] Implement model serialization in `code/modeling.py` (save trained model to `models/rf_model.pkl` using `joblib.dump(model,..., compress=3, protocol=3)`). **Requirement**: Ensure directory `models/` exists using `os.makedirs('models', exist_ok=True)` before saving. **Verification**: Assert `models/rf_model.pkl` exists and can be loaded without error.

---

## Phase 4: User Story 3 - Feature Importance and Associational Interpretation (Priority: P3)

- [X] T028 [US3] Implement VIF calculation in `code/analysis.py`. **Input**: **Raw (non-ILR) atomic fractions** of Cu, Mg, Si, Zn, Mn. **Threshold**: Flag if VIF > 5.0. **Output**: Save to `results/collinearity_diagnostic.json` containing VIF scores per element and a pass/fail flag. **Verification**: Assert `results/collinearity_diagnostic.json` matches `contracts/collinearity_diagnostic.schema.yaml`. (satisfies FR-007).
- [X] T027a [US3] Implement Permutation Importance of Feature Importance in `code/analysis.py`. **Logic**: Extract feature importance weights from the trained Random Forest model (based on ILR-transformed features) using `sklearn.inspection.permutation_importance`. **Requirement**: This method satisfies FR-006 by providing a mathematically valid importance ranking in the compositional space without attempting invalid back-transformation. **Output**: Save to `results/feature_importance.json` as per schema. **Verification**: Assert `results/feature_importance.json` contains `importance_scores` for all 5 elements and matches `contracts/feature_importance.schema.yaml`. (satisfies FR-006).
- [X] T029 [US3] Implement result ranking and comparison logic in `code/analysis.py`. **Input**: `results/feature_importance.json` from T027a. **Output**: JSON `results/feature_importance_summary.json` with `top_element`, `second_element`, `ratio`, `comparison_statement`. **Verification**: Assert `results/feature_importance_summary.json` exists and contains valid comparison logic. (satisfies US3 Scenario 3).
- [X] T030a [US3] Implement final report generation in `code/main.py`. **Inputs**: `results/model_metrics.json` (from T023d), `results/collinearity_diagnostic.json` (from T028), `results/feature_importance_summary.json` (from T029), `results/methodological_flags.json` (from T023c). **Output**: `results/final_report.md`. **Verification**: 1) Verify `results/final_report.md` contains section "Methodological Limitations". 2) Assert report contains "associational (not causal)" phrase. 3) Validate report against `contracts/final_report.schema.yaml`. (satisfies SC-005, resolves T030a FAILED status).
- [X] T030b [US3] Implement report validation in `code/main.py`.
- [X] T030c [US3] Implement Limitation Statement Generation: Update `results/final_report.md` with a "Methodological Limitations" section, consuming output from T023c (methodological_flags.json) and T028. **Verification**: Assert the section exists and references the specific flags.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Verification & Testing

- [X] T040 [P] Run `pytest --cov=code` and verify coverage report exists and contains numeric values for line and branch coverage using `pytest-cov`.
- [X] T041 [US2] Unit tests for modeling logic: Add tests in `tests/test_modeling.py` including `test_ilr_transform_handles_zero_sum`, `test_rf_training_converges`, `test_cv_split_reproducibility`.
- [X] T042 [US1] Contract tests for data schemas: Add tests in `tests/test_schemas.py` including `test_alloy_record_schema_validation`, `test_missing_field_handling`, `test_unit_normalization`.
- [X] T043 [US3] Unit tests for analysis logic: Add tests in `tests/test_analysis.py` including `test_vif_calculation_flags_high_collinearity`, `test_shap_importance_aggregation`, `test_ranking_logic`.
- [X] T044 [P] Run `pytest` on all CLI scripts and verify CLI flags work.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

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
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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