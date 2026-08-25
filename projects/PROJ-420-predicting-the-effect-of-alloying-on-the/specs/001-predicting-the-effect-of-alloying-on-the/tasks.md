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
- [X] T002 Initialize a Python project with dependencies (pandas, numpy, scikit-learn, requests, pyyaml, seaborn, matplotlib, compositional, statsmodels, datasets, periodictable, joblib, pytest, pytest-cov, ruff, black) in `code/requirements.txt`.
- [X] T003 [P] Configure linting (ruff==0.1.6) and formatting (black==23.12.1) tools in `code/` using `pyproject.toml` as the configuration source.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/__init__.py` and basic project scaffolding
- [X] T005 [P] Setup environment configuration management in `code/config.py` (loading `data/`, `models/`, `results/` paths, random seeds, `VALID_MEASUREMENT_METHODS` regex list).
- [X] T006 [P] Implement logging infrastructure in `code/logging_config.py` (JSON logging, error levels).
- [X] T007 Create data schema definitions in `code/schemas/alloy_record.py` (Pydantic models for AlloyRecord, ModelMetrics). **Requirement**: The `measurement_method` field MUST be **Optional** in the raw schema. If the field is missing in the raw data, the record is NOT excluded immediately; instead, the plan's T1.4b logic (attempt inference) is applied in T014. (satisfies FR-009).
- [X] T008 Implement checksum utility in `code/utils/checksum.py` for verifying raw data integrity.
- [X] T008b [P] Implement Data Source Verification: Consolidate API checks into a single script `code/data_verification.py`. **Logic**: 1) Verify network reachability of MP and NIST. 2) Verify raw API response structure (JSON paths for `poisson_ratio`, `composition`, `young_modulus`, `measurement_method`). 3) **Validate the normalized merged structure against `contracts/dataset.schema.yaml`**. **Verification Step**: Before validation, **verify that `contracts/dataset.schema.yaml` exists and explicitly defines the fields required for the merged dataset (Cu, Mg, Si, Zn, Mn, poisson_ratio, young_modulus, etc.)**. If the schema is missing or incomplete, raise `RuntimeError`. **Fail Condition**: If any check fails, raise `RuntimeError` with a clear message. (Replaces T008c, T008e).
- [X] T008d [P] Implement Merge & Deduplicate logic in `code/merge.py`. **Deduplication Logic**: Merge on exact match of normalized atomic fractions (tolerance within a negligible range) and Young's Modulus (tolerance within a negligible range). **Conflict Resolution**: If duplicates exist, prefer the record where `measurement_method` string contains 'Ultrasonic' or 'Direct'; if both or neither, prefer the source 'NIST' over 'Materials Project'. (satisfies FR-001).
- [X] T009 [US1] Implement data extraction for Materials Project in `code/_download_logic.py`. **Endpoint**: Use `https://next-gen.materialsproject.org/api/v2/materials/` with query parameters `?elements=Al&property_ids=poisson_ratio&property_ids=young_modulus`. **Authentication**: The script MUST read `MP_API_KEY` from environment variables. **Logic**: Fetch data. If zero entries found, log warning but DO NOT halt; proceed to T009b. (satisfies FR-001).
- [X] T009b [US1] Implement data extraction for NIST in `code/_download_logic.py`. **Requirement**: This task implements the plan's verified source strategy (FR-001). **Dataset**: Use `datasets.load_dataset("materials/alloy-elastic", split="train")`. **Note**: This dataset serves as the verified proxy for the NIST data mentioned in the Spec's Assumptions. **Verification**: The script MUST verify that the dataset ID corresponds to the canonical `materials/alloy-elastic` dataset. **Logic**: Fetch data. **HALT CONDITION**: If the dataset is unavailable (e.g., 404, timeout), raise `RuntimeError("CRITICAL: Verified source 'materials/alloy-elastic' unavailable. Cannot proceed.")`. Do NOT fallback to guessing URLs. (satisfies FR-001, resolves Edge Case).
- [X] T010 [US1] Implement data extraction validation in `code/data/clean.py`. **Requirement**: Verify the raw data (from T009, T009b) contains all required fields (Poisson's ratio, Young's modulus, Cu, Mg, Si, Zn, Mn, **measurement_method**) at the **schema level**. **Field Mappings**: Map `poisson_ratio` -> `poisson_ratio`, `young_modulus` -> `young_modulus`, `elements` -> `composition` (dict). **Logic**: If a required field is missing from the **schema**, raise a `ValueError`. If a field is present but **null/missing for a specific row**, do NOT raise; defer handling to T014. (satisfies FR-009, resolves T010/T014 conflict).
- [X] T011 [US1] Implement monolithic filtering in `code/data/clean.py`. **Definition**: `alloy_type == 'monolithic'` OR `is_composite == False` OR `composite_fraction == 0.0`. **Priority**: Check `alloy_type` first, then `is_composite`, then `composite_fraction`. If neither field exists, the record is excluded. (satisfies FR-002).
- [X] T012 [US1] Implement unit normalization in `code/data/clean.py`. **Source Units**: Detect if `composition` is in wt% or at%. If wt%, convert to at% using atomic weights from `periodictable` package. If at%, verify sum is ~1.0. `young_modulus` expected in GPa (convert from MPa using the standard conversion factor). (satisfies FR-003).
- [X] T013 [US1] Implement exclusion logic in `code/data/clean.py` for entries where major element sum < 0.95. **Calculation**: `major_sum = sum(Cu, Mg, Si, Zn, Mn)` in atomic fractions. **Al Balance**: `Al balance = 1.0 - major_sum`. If `major_sum < 0.95`, exclude row with log warning. (satisfies FR-003).
- [X] T016 [P] [US1] Implement exclusion logging utility in `code/data/clean.py`. **Purpose**: Standalone utility function. **Logic**: Append exclusion records to `data/logs/exclusion_log.txt` (CSV format: `step,count,reason`). **Output**: `data/logs/exclusion_log.txt`. (satisfies T018b, resolves circular dependency).
- [ ] T014 [US1] Implement independence verification in `code/data/clean.py`. **Requirement**: If `measurement_method` is missing/null in the raw data, **ATTEMPT INFERENCE** before exclusion. **Inference Logic**: 1) Check source metadata fields for keywords 'Ultrasonic', 'Direct', 'Resonant', 'Impulse'. 2) If keyword found, set `measurement_method` to the matched keyword and mark as 'inferred'. 3) If no keyword found, EXCLUDE the record. **Traceability**: This task explicitly implements the mitigation strategy authorized by `plan.md` T1.4b to satisfy `spec.md` FR-009 and Edge Cases. **Constraint Gap Note**: This task implements a *mitigation* (inference) for a missing verification; it does not fully satisfy the strict "verify" requirement of FR-009 if inference fails. **Output**: Append to `data/logs/exclusion_log.txt` with reason 'missing_measurement_method' or 'inference_failed'. **Note**: Inference is a mitigation, not a replacement for verification; records failing inference are excluded to uphold FR-009. (satisfies FR-009, resolves T010/T014 conflict).
- [ ] T015 [US1] Implement final validation and orchestration in `code/data/clean.py`. **Requirement**: Orchestrate the full pipeline (T010-T014). **Step 1**: Run T010-T014 functions in sequence. **Step 2**: Invoke T016 utility to ensure all exclusions are logged. **Step 3**: Read `data/logs/exclusion_log.txt` (Schema: CSV with columns `step,count,reason`) and count valid rows in the final dataset. **Step 4**: If row count < 50, **HALT** with error "Insufficient data after filtering (<50 entries)" and `sys.exit(1)`. **Step 5**: If count >= 50, save the cleaned dataset to `data/processed/alloys_clean.parquet`. **Output**: `data/processed/alloys_clean.parquet` (ONLY if count >= 50). **Blocked by**: T014, T016. (satisfies SC-001, resolves T018 conflict).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Regression Model Training and Validation (Priority: P2)

- [X] T019 [US2] Implement ILR transformation in `code/data/clean.py` using the `compositional.ilr` function for Cu, Mg, Si, Zn, Mn atomic fractions. **Order**: Fixed order `['Cu', 'Mg', 'Si', 'Zn', 'Mn']` to ensure reproducibility.
- [ ] T021 [US2] Implement Repeated -Fold Cross-Validation in `code/modeling.py`. **Logic**: Perform multiple repeats of k-fold CV. **Note**: This task implements the plan's strategy (Repeated CV only) as the primary validation metric. **Output**: Compute and log mean CV-MAE and confidence intervals.
- [ ] T025 [US2] Implement 80/20 Held-Out Test Set Split in `code/modeling.py`. **Requirement**: This task satisfies the Spec's FR-005 and US2 Scenario 3 which mandate a held-out test set. **Logic**: Perform an /20 split on the full dataset (stratified if possible, though target is continuous). Train a separate RF on the training set and evaluate on the test set. **Output**: Compute and log Test-Set MAE. **Note**: This task exists to satisfy the Spec requirement even though the Plan prioritizes Repeated CV; both metrics will be reported. (satisfies FR-005, resolves Spec/Plan contradiction).
- [X] T022 [US2] Implement Random Forest training with k-fold cross-validation in `code/modeling.py`. **Hyperparameters**: `n_estimators=100`, `max_depth=None`, `random_state=42`.
- [ ] T023c [US2] Implement MAE Calculation and Logging: In `code/modeling.py`, compute the cross-validation MAE and the held-out test MAE (from T025). Check if CV MAE > 0.05. **Condition**: Set `mae_flag` to `True` if `cv_mae > 0.05`. **Logic**: If `mae_flag` is True, ensure `results/` directory exists (`os.makedirs('results', exist_ok=True)`) and write a flag to `results/methodological_flags.json` (create if needed) to be consumed by the report generator. **Output**: `results/methodological_flags.json`. (satisfies Edge Cases, resolves T023c path issue).
- [ ] T024 [US2] Implement model serialization in `code/modeling.py` (save trained model to `models/rf_model.pkl` using `joblib.dump(model,..., compress=3, protocol=3)`). **Requirement**: Ensure directory `models/` exists using `os.makedirs('models', exist_ok=True)` before saving.

---

## Phase 4: User Story 3 - Feature Importance and Associational Interpretation (Priority: P3)

- [ ] T028 [US3] Implement VIF calculation in `code/analysis.py`. **Threshold**: Flag if VIF > 5.0.
- [ ] T027a [US3] Implement Permutation Importance on ILR features in `code/analysis.py`. **Logic**: Calculate Permutation Importance in ILR space. **Constraint Gap Note**: This task implements Permutation Importance because back-transformation of RF importance is mathematically invalid for non-linear models, creating a gap with the literal text of FR-006. **Output**: Save to `results/feature_importance.json` as per schema. **Requirement**: Create `specs/001-predict-poissons-ratio/contracts/feature_importance.schema.yaml` if it does not exist, defining the schema for this output. (satisfies FR-006 intent, acknowledges FR-006 gap).
- [ ] T027b [US3] Generate Deviation Report: Create `results/deviation_report.md` documenting the scientific necessity of using Permutation Importance over back-transformation (due to ILR space constraints) and flagging this as a deviation from the literal text of FR-006 for Spec Review. (Resolves executability-9ff6adce, satisfies constraint_preservation-c9bdf1cd).
- [ ] T029 [US3] Implement result ranking and comparison logic in `code/analysis.py`. **Output**: JSON `results/feature_importance_summary.json` with `top_element`, `second_element`, `ratio`, `comparison_statement`.
- [ ] T030a [US3] Implement final report generation in `code/main.py`.
- [ ] T030b [US3] Implement report validation in `code/main.py`.
- [ ] T030c [US3] Implement Limitation Statement Generation: Update `results/final_report.md` with a "Methodological Limitations" section, consuming output from T023c (methodological_flags.json) and T028.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Verification & Testing

- [X] T040 [P] Run `pytest --cov=code` and verify coverage report exists and contains numeric values for line and branch coverage using `pytest-cov`.
- [X] T041 [US2] Unit tests for modeling logic.
- [X] T042 [US1] Contract tests for data schemas.
- [X] T043 [US3] Unit tests for analysis logic.
- [X] T044 [P] Run `pytest` on all CLI scripts and verify CLI flags work.