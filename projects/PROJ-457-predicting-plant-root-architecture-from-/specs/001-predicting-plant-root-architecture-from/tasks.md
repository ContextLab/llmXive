# Tasks: Predicting Plant Root Architecture from Soil Nutrient Availability

**Input**: Design documents from `/specs/001-predict-root-architecture/`
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

- [X] T001 Create project directory structure, initialize logging, and Git repository: Execute `mkdir -p code/ tests/ data/raw data/processed artifacts/models artifacts/plots artifacts/reports logs`, create `code/logging_config.py` with file and console handlers, run `git init`, and create `.gitignore` for Python/data. **Verification**: Run `tree -d .` and save output to `logs/setup_tree.log`, confirm `code/logging_config.py` imports successfully, confirm `.git` directory exists.

- [X] T002a [P] Create initial `requirements.txt`: Create `code/requirements.txt` with base dependencies: `pandas`, `scikit-learn`, `statsmodels`, `seaborn`, `matplotlib`, `pyyaml`, `geopandas`, `datasets`. **Verification**: Confirm file exists and contains package names.
- [X] T002b [P] Pin dependency versions: Run `pip install -r code/requirements.txt` then `pip freeze > code/requirements.txt` to ensure exact versions are recorded. **Verification**: Confirm `requirements.txt` contains version specifiers (e.g., `pandas==2.0.0`). **Prerequisite**: T002a.
- [X] T003a [P] Create linting configuration: Create `.flake8` and `pyproject.toml` with black/flake8 settings. **Verification**: Confirm files exist and contain valid configuration.
- [X] T003b [P] Run Black check: Run `black --check code/`. **Verification**: Ensure no linting errors are reported.
- [X] T003c [P] Run Flake8 check: Run `flake8 code/`. **Verification**: Ensure no linting errors are reported.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/config.py` to load paths, seeds, and constants from `config.yaml`
- [X] T007 [P] Create base data models/classes for `RootPhenotypeRecord` and `SoilNutrientRecord` in `code/models.py`
- [X] T006 [P] Setup logging infrastructure in `code/config.py` (file + console handlers)
- [X] T008 Setup environment configuration management: Create `code/config.yaml.template` with keys: `DATA_PATH`, `SEED`, `LOG_LEVEL`, `LITERATURE_RANGES`
- [X] T014a [P] Initialize State File: Create `artifacts/state.json` with initial structure: `{"p_n_available": null, "is_isric_verified": null, "spec_deviations": []}`. **Verification**: Confirm file exists and is valid JSON.
- [X] T015g [P] Verify ISRIC Source: Check for a verified ISRIC source in the project's `# Verified datasets` block or `code/config.py`. **Action**: If no verified source exists, log "FR-002: ISRIC merge excluded due to lack of verified source" to `logs/deviation.log` and set `is_isric_verified: false` in `artifacts/state.json`. **Constraint**: This task must run BEFORE T013 to establish the deviation policy. **Verification**: Confirm log entry exists and state file is updated.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest root phenotype data from PlantPheno, check for nutrient columns, filter for valid observations (n≥20 per species, no missing P/N), and produce a cleaned, merged dataset. **Note**: Per Plan "Spec Deviation", ISRIC merging is excluded; missing nutrients are excluded, not imputed.

**Independent Test**:

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Contract test for merged dataset schema in `tests/contract/test_schemas.py` - **Function**: `test_merged_dataset_schema_validates_columns` - Validates `contracts/dataset.schema.yaml` columns (species, root_length, branching_density, surface_area, phosphorus, nitrogen). *Prerequisite: T009 (Schema Creation)*
- [X] T010 [P] [US1] Unit test for log-transformation handling of zeros/negatives in `tests/unit/test_preprocessing.py`
- [X] T012 [US1] Integration test for full ingestion pipeline end-to-end in `tests/integration/test_pipeline.py`

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/data_ingestion.py` to download/parse PlantPheno data (FR-001). **Function Signatures**: `fetch_plantpheno() -> pd.DataFrame`. **Constraint**: Use HuggingFace dataset ID 'plantpheno/root-reader' (MUST use this exact ID; raise Exception if not found). **Constraint**: Use `datasets.load_dataset` with `streaming=True` if dataset is large; otherwise use direct URL fetch. **Constraint**: MUST fail loudly (raise Exception) if real data fetch fails; NO synthetic fallback. **Constraint**: Check `is_isric_verified` flag from T015g. If `false`, log "FR-002: ISRIC merge excluded" and proceed with root-only data path. **Prerequisite**: T015g.
- [X] T013b [US1] Handle ISRIC Unavailable Path: Check if ISRIC source is verified (from T015g). If not, log "FR-002: ISRIC merge excluded" and set `is_isric_verified: false`. **Action**: Proceed with root-only data path. **Verification**: Confirm log entry and state file update. **Prerequisite**: T015g.
- [X] T014 [US1] Check P/N Availability and Update State: Check for Phosphorus/Nitrogen columns in PlantPheno data. If columns exist, set `p_n_available=True`. If missing, set `p_n_available=False`, log "Hypothesis Unverifiable" to `logs/deviation.log`, and write `p_n_available` flag to `artifacts/state.json`. **Constraint**: If P/N columns are missing, DO NOT halt. Proceed with root-only data. **Verification**: Confirm the `p_n_available` flag is set correctly in `artifacts/state.json`. **Prerequisite**: T013, T013b, T014a.
- [X] T014d [US1] Create Formal Amendment Record: Create `artifacts/sc_amendments.json` with entry AM-001 documenting the exclusion of FR-002 (ISRIC) and FR-003 (KNN Imputation) per Plan "Spec Deviation". **Constraint**: Must include keys: `amendment_id: "AM-001"`, `reason: "ISRIC source unavailable and KNN imputation creates circular bias"`, `affected_fr_ids: ["FR-002", "FR-003"]`, `date: "2024-05-21"`. **Constraint**: Explicitly state that SC-001 and SC-002 are redefined or marked 'unmeasurable' in this record. **Verification**: Validate JSON structure and content using a script. **Prerequisite**: T014, T014a.
- [X] T015c [US1] Filter by Data Source Type: Implement logic in `code/data_ingestion.py` to filter out rows where `data_source_type` indicates 'manipulated' or 'controlled' (FR-012). **Constraint**: Filter values: `['manipulated', 'controlled', 'nutrient_manipulation', 'treatment']`. **Prerequisite**: T013.
- [X] T015d [US1] Implement Missing Data Exclusion Logic (FR-003 Deviation): Implement logic to exclude rows where Phosphorus or Nitrogen are missing (if `p_n_available` is True). **Constraint**: This is a deviation from FR-003 (KNN Imputation) authorized by AM-001. **Verification**: Log exclusion count. **Prerequisite**: T014, T014d, T015c, T015g.
- [X] T015e [US1] Filter by Species Count: Implement logic to exclude species with n < 20. **Prerequisite**: T015d.
- [X] T015f [US1] Write Species Counts: Write `artifacts/reports/species_counts.json` with exclusion counts (total input, excluded by source, excluded by missing nutrients, excluded by count). **Prerequisite**: T015e.
- [X] T015h [US1] Record FR-003 Deviation Log: Log "FR-003: KNN imputation excluded to preserve statistical validity; missing nutrients are excluded (AM-001)" to `logs/deviation.log`. **Constraint**: This task runs AFTER T015d to confirm the deviation was applied. **Prerequisite**: T015d, T015g.
- [X] T015i [US1] Record FR-002 Deviation Log: Log "FR-002: ISRIC merge excluded due to lack of verified source (AM-001)" to `logs/deviation.log`. **Constraint**: This task runs AFTER T015g. **Prerequisite**: T015g.
- [X] T015k [US1] Count Available Datasets: Count the total number of available RootReader/PlantPheno datasets from source metadata. **Output**: Write `total_available_datasets` to `artifacts/reports/metrics.json`. **Prerequisite**: T013.
- [X] T015m [US1] Record SC-001 Status: Mark SC-001 as 'unmeasurable' due to ISRIC exclusion. Write `sc001_status: "unmeasurable"`, `reason: "ISRIC source unavailable; FR-002 excluded (AM-001)"` to `artifacts/reports/metrics.json`. **Prerequisite**: T015k, T014d.
- [X] T035a [US1] **Calculate P/N Availability Rate**: Calculate 'P/N Availability Rate' (rows with P/N / total rows) as a redefinition of SC-001 due to ISRIC exclusion. **Formula**: (count of rows where P and N are not null) / (total rows in the dataset output by T013, after FR-012 filtering, before T015d exclusion). **Output**: Write result to `artifacts/reports/metrics.json` under key `pn_availability_rate` and include a note `original_sc001_metric: merge_success_rate (unavailable due to scope deviation)`. **Constraint**: Explicitly link this calculation to the formal amendment record AM-001 in `artifacts/sc_amendments.json`. **Constraint**: Immediately write a status update to `artifacts/reports/success_criteria_status.json` marking SC-001 as 'redefined' with the reason. **Prerequisite**: T013, T014, T015f.
- [X] T035b [US1] **Calculate SC-005 Ratio**: Calculate SC-005 ratio (number of species excluded due to n < 20 / total number of species in input) and write to `artifacts/reports/metrics.json`. **Constraint**: **Input**: Read `artifacts/reports/species_counts.json` (from T015f) to get `total_species_input` and `excluded_species_count`. **Constraint**: **Output**: Write the calculated ratio to `artifacts/reports/metrics.json` under key `species_exclusion_ratio`. **Prerequisite**: T015f.
- [X] T035c [US1] **Update Success Criteria Status**: Create `artifacts/reports/success_criteria_status.json` with explicit status for SC-001 ('unmeasurable'), SC-002 ('Measured'), SC-003 ('Measured'), etc. **Constraint**: Must include the reason for SC-001 status change. **Prerequisite**: T014d, T015m, T035a.
- [X] T016 [US1] Implement `code/preprocessing.py` for log-transformation of root metrics and z-score normalization (global, across all species) of nutrients (FR-003, Const VII). **Prerequisite**: T014, T015. **Constraint**: **Order of Operations**: Normalize nutrients ONLY after T015 has excluded rows with missing nutrients. **Constraint**: **Conditional Execution**: If `p_n_available` is False, skip nutrient normalization but still perform root log-transform. If `p_n_available` is True, calculate z-score on the *remaining* valid rows.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Modeling and Association Analysis (Priority: P2)

**Goal**: Fit Linear Mixed-Effects Models (LMM) and baseline Random Forest models to quantify nutrient-architecture relationships, perform species-level cross-validation, and report statistical significance.

**Independent Test**: The modeling step can be tested by running the training script on the preprocessed dataset and verifying the output JSON contains R², RMSE, and p-values for the LMM coefficients, ensuring the random forest baseline is also evaluated.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T020 [P] [US2] Contract test for model output schema (R², p-values) in `tests/contract/test_schemas.py` - **Function**: `test_model_metrics_schema_validates_fields` - Validates `contracts/model_results.schema.yaml` fields (lmm.adjusted_r_squared, lmm.p_values, etc.). *Prerequisite: T020 (Schema Creation)*
- [X] T021 [P] [US2] Unit test for species-level stratified split logic in `tests/unit/test_preprocessing.py`
- [X] T022 [US2] Integration test for model training and evaluation pipeline in `tests/integration/test_pipeline.py`

### Implementation for User Story 2

- [X] T023 [US2] Implement `code/modeling.py` to perform k-fold cross-validation split strictly by species (FR-006) - *Prerequisite: T016 (US1 output)*
 - **Constraint**: Use `GroupKFold` from `scikit-learn` with `groups=species`.
- [X] T024 [US2] Implement LMM fitting in `code/modeling.py` using `statsmodels` (REML, Satterthwaite p-values, species as random intercept) (FR-004)
 - **Constraint**: Ensure CPU-only execution (no GPU); use REML estimation.
- [X] T025 [US2] Implement Random Forest baseline in `code/modeling.py` (max_depth=5) for comparison (FR-005)
 - **Constraint**: Ensure CPU-only execution; limit `n_estimators` to ensure runtime < 6h.
- [X] T026 [US2] Implement F-test for overall model significance and coefficient p-values in `code/modeling.py` (FR-008)
- [X] T026b [US2] Verify F-Test Results: Ensure F-test results are logged and valid. **Action**: Read F-test p-values and verify they are within [0, 1]. Log "F-test verification passed" or "F-test verification failed" to `logs/f_test_verification.log`. **Prerequisite**: T026.
- [X] T027 [US2] Implement multiple-comparison correction (Bonferroni or FDR) for hypothesis testing in `code/modeling.py` (FR-010)
- [X] T028a [US2] **Fetch Literature Ranges**: Implement a local verification script to fetch and verify physiological ranges for Phosphorus and Nitrogen coefficients from HuggingFace dataset 'plant-physiology/nutrient-ranges'. **Action**: Extract columns `phosphorus_coefficient_range` and `nitrogen_coefficient_range`. **Constraint**: If dataset is missing, log "FR-011: Literature source unavailable; skipping plausibility check" to `logs/deviation.log`, set `literature_verified: false` in `artifacts/state.json`, and proceed without failing. Do NOT use hardcoded fallback. **Output**: Write verified ranges to `artifacts/literature_ranges.json` if successful. **Prerequisite**: T024.
- [X] T028b [US2] **Implement Sensitivity Analysis**: Implement sensitivity analysis of nutrient coefficients against literature ranges (FR-011). **Action**: Re-calculate coefficients with ±10% variation in input nutrients. **Output**: Generate `artifacts/sensitivity/sensitivity_analysis.json`. **Required Keys**: `percent_deviation` (float), `literature_mean` (float), `observed_coefficient` (float), `confidence_interval` (list of 2 floats). **Constraint**: Use physiological ranges from `artifacts/literature_ranges.json` if `literature_verified` is true; otherwise, skip this step and log "Skipped: literature unavailable". **Prerequisite**: T024, T028a.
- [X] T028c [US2] **Perform Literature Comparison (FR-011)**: Compare observed coefficients to literature ranges and determine biological plausibility. **Action**: Check if confidence interval overlaps with literature range. **Output**: Add `literature_overlap` (boolean) and `plausibility_verdict` (string: "Plausible", "Implausible", or "Skipped") to `artifacts/sensitivity/sensitivity_analysis.json`. **Constraint**: If `literature_verified` is false, set `plausibility_verdict` to "Skipped". **Prerequisite**: T028b, T028a.
- [X] T029a [US2] **Generate Final Metrics**: Generate output JSON with adjusted R², RMSE, p-values, cross-validation mean R², and sensitivity analysis results. **Constraint**: Consume `artifacts/sensitivity/sensitivity_analysis.json` and `artifacts/reports/model_metrics.json` (core metrics). **Prerequisite**: T023, T024, T025, T028c.
- [X] T029b [US2] **Calculate Derived Metrics**: Calculate R² difference (LMM - RF) and report raw values (FR-004, FR-005, FR-006, SC-002). **Constraint**: Explicitly calculate `sc002_met` = `abs(lmm_r2 - rf_r2) <= 0.05` and write this boolean to the JSON. **Prerequisite**: T029a.
- [X] T029c [US2] **Write Final JSON**: Write the final JSON to `artifacts/reports/model_metrics.json`. **Prerequisite**: T029b.
- [X] T029d [US2] **Record SC-002 Success**: Explicitly write the `sc002_met` boolean result to the final report or metrics file in a way that satisfies the 'Measurable Outcomes' requirement of SC-002. **Prerequisite**: T029c.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate partial dependence plots, compile final report with statistical findings, and ensure output size constraints are met.

**Independent Test**: The reporting step can be tested by running the visualization script and verifying that PNG files are generated for partial dependence plots and that the total output size is ≤100MB.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US3] Contract test for report schema in `tests/contract/test_schemas.py` - **Function**: `test_final_report_schema_validates_structure` - Validates `contracts/output.schema.yaml` structure (tables, metrics, deviations). *Prerequisite: T030 (Schema Creation)*
- [X] T031 [P] [US3] Unit test for file size constraint enforcement in `tests/unit/test_reporting.py`

### Implementation for User Story 3

- [X] T032 [P] [US3] Implement `code/visualization.py` to generate partial dependence plots (wide percentile range) for nutrient-architecture relationships (FR-007)
 - **Constraint**: Use `seaborn` or `matplotlib`; range of a broad central percentile distribution.
- [X] T033 [US3] Implement `code/visualization.py` to save figures as PNGs, enforcing total size ≤100MB (FR-007, SC-004)
 - **Constraint**: Compress images or reduce DPI if size exceeds limit; log final size.
- [X] T034a [US3] **Read Deviation Logs**: Read `logs/deviation.log` (from T015h, T015i) and extract list of deviations. **Prerequisite**: T015h, T015i.
- [X] T034b [US3] **Read Metrics**: Read `artifacts/reports/model_metrics.json` (from T029c) and `artifacts/reports/metrics.json` (from T035a, T035b, T035c). **Prerequisite**: T029c, T035a, T035b.
- [X] T034c [US3] **Compile Final Report**: Implement `code/reporting.py` to compile final report including R², p-values, plots, and associational framing (FR-009). **Constraint**: Explicitly state "associational" not "causal". **Constraint**: Include the list of deviations from T034a. **Constraint**: Include the calculated metrics from T034b. **Prerequisite**: T034a, T034b, T032, T033.
- [X] T034e [US3] **Validate Associational Framing (FR-009)**: Scan the final report (T034c output) for causal language (e.g., "causes", "leads to", "effect of"). **Action**: If causal language is found, raise Exception and log violation. **Constraint**: Must ensure "associational" phrasing is used. **Prerequisite**: T034c.
- [X] T034d [US3] **Write Final Report**: Write the compiled report to `artifacts/reports/final_report.md`. **Prerequisite**: T034e.
- [X] T036 [US3] Verify biological plausibility of coefficients against literature in final report (FR-011, SC-006). **Constraint**: **Input**: Read `artifacts/reports/metrics.json` (from T035a/b) and `artifacts/sensitivity/sensitivity_analysis.json` (from T028c). **Constraint**: **Output**: Include a Markdown table in the final report comparing coefficients to literature ranges. This table MUST be generated from the JSON files. **Constraint**: Ensure the report explicitly states whether coefficients fall within the expected physiological ranges or if the check was skipped. **Prerequisite**: T028c, T034d.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories (Plan-mandated)

- [X] T037a [P] Init State File: Create `state/projects/PROJ-457-predicting-plant-root-architecture-from-.yaml` with initial structure: `artifact_hashes: {}`, `updated_at: null`. **Verification**: Confirm file exists and is valid YAML.
- [X] T037 [P] Update State File: Calculate content hashes for all artifacts in `artifacts/` and update the state file with these hashes (Constitution Principle V, Plan Task 4.3). **Action**: Run `find artifacts/ -type f -exec sha256sum {} \;` and write the output to `state/projects/PROJ-457-predicting-plant-root-architecture-from-.yaml` under `artifact_hashes`. **Constraint**: Ensure the state file is updated with the new timestamp. **Prerequisite**: T037a.
- [X] T038 Update `README.md` and `docs/` with final results, including the `literature_comparison` findings and the `spec_deviations` list (Plan Task 4.4).
- [X] T039 Run `quickstart.md` validation to ensure reproducibility (Plan Task 4.1).

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output

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
Task: "Contract test for merged dataset schema in tests/contract/test_schemas.py"
Task: "Unit test for log-transformation handling in tests/unit/test_preprocessing.py"

# Launch all models for User Story 1 together:
Task: "Implement data_ingestion.py to download/parse PlantPheno data"
Task: "Implement preprocessing.py for log-transformation and z-score normalization"
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
- **Constraint Check**: All tasks designed for CPU-only (a limited number of cores, limited RAM), no GPU, ≤6h runtime. No 8-bit/4-bit quantization or large model training.
- **Data Integrity**: All data loaders MUST fail loudly on fetch error; no synthetic fallbacks.
- **Streaming**: Large datasets MUST be streamed or sampled explicitly; no synthetic stand-ins.
- **Spec Deviation**: ISRIC merge and KNN imputation are excluded per Plan. Missing nutrients are excluded.
- **State Transfer**: Deviations and metrics are written to persistent JSON files (`artifacts/reports/metrics.json`) and logs (`logs/deviation.log`) to ensure deterministic consumption by the reporting phase.
- **Schema Creation**: T009, T020, T030 now include schema creation as part of their execution.

---

## Schema Definition Tasks (Merged into Contract Tests)

- [X] T009 [US1] Create Dataset Schema and Contract Test: Create `contracts/dataset.schema.yaml` with schema for merged dataset (species, root_length, branching_density, surface_area, phosphorus, nitrogen) AND implement `tests/contract/test_schemas.py` with `test_merged_dataset_schema_validates_columns`. **Verification**: Validate YAML syntax, required fields, and that the contract test passes against the schema. **Prerequisite**: T016 (for schema content reference).
- [X] T020 [US2] Create Model Schema and Contract Test: Create `contracts/model_results.schema.yaml` with schema for model metrics (lmm.adjusted_r_squared, lmm.rmse, lmm.p_values, random_forest.r_squared, random_forest.rmse) AND implement `tests/contract/test_schemas.py` with `test_model_metrics_schema_validates_fields`. **Verification**: Validate YAML syntax and required fields. **Prerequisite**: T029c.
- [X] T030 [US3] Create Output Schema and Contract Test: Create `contracts/output.schema.yaml` with schema for final report (tables, metrics, deviations) AND implement `tests/contract/test_schemas.py` with `test_final_report_schema_validates_structure`. **Verification**: Validate YAML syntax and required fields. **Prerequisite**: T034d.