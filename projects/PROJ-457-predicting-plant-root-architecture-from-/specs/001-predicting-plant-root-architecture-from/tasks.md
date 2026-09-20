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

- [X] T001 Create project structure per implementation plan: `code/`, `tests/`, `data/raw/`, `data/processed/`, `artifacts/`, `artifacts/models/`, `artifacts/plots/`, `artifacts/reports/`, and `logs/`. **Deliverable**: Execute `mkdir -p code/ tests/ data/raw data/processed artifacts/models artifacts/plots artifacts/reports logs` and verify all directories exist. **Verification**: Run `tree -d.` and save the output to `logs/setup_tree.log`. Write a success confirmation message with timestamp to `logs/setup.log`. **Constraint**: Ensure `logs/` directory is created as it is required for T015 logging.
- [X] T002a [P] Install dependencies: Run `pip install -r code/requirements.txt` where `requirements.txt` contains `pandas`, `scikit-learn`, `statsmodels`, `seaborn`, `matplotlib`, `pyyaml`, `geopandas`. **Verification**: Run `pip list` and confirm all packages are installed.
- [X] T002b [P] Pin dependency versions: Run `pip freeze > code/requirements.txt` to ensure exact versions are recorded. **Verification**: Confirm `requirements.txt` contains version specifiers (e.g., `pandas==2.0.0`).
- [X] T003a [P] Create linting configuration: Create `.flake8` and `pyproject.toml` with black/flake8 settings. **Verification**: Confirm files exist and contain valid configuration.
- [ ] T003b [P] Run linting check: Run `black --check code/` and `flake8 code/`. **Verification**: Ensure no linting errors are reported.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/config.py` to load paths, seeds, and constants from `config.yaml`
- [X] T007 [P] Create base data models/classes for `RootPhenotypeRecord` and `SoilNutrientRecord` in `code/models.py`
- [X] T006 [P] Setup logging infrastructure in `code/config.py` (file + console handlers)
- [X] T008 Setup environment configuration management: Create `code/config.yaml.template` with keys: `DATA_PATH`, `SEED`, `LOG_LEVEL`, `LITERATURE_RANGES`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest root phenotype data from PlantPheno, check for nutrient columns, filter for valid observations (n≥20 per species, no missing P/N), and produce a cleaned, merged dataset. **Note**: Per Plan "Spec Deviation", ISRIC merging is excluded; missing nutrients are excluded, not imputed.

**Independent Test**:

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Contract test for merged dataset schema in `tests/contract/test_schemas.py` - **Function**: `test_merged_dataset_schema_validates_columns` - Validates `contracts/dataset.schema.yaml` columns (species, root_length, branching_density, surface_area, phosphorus, nitrogen). *Prerequisite: T009a (Schema Definition)*
- [X] T010 [P] [US1] Unit test for log-transformation handling of zeros/negatives in `tests/unit/test_preprocessing.py`
- [X] T012 [US1] Integration test for full ingestion pipeline end-to-end in `tests/integration/test_pipeline.py`

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/data_ingestion.py` to download/parse RootReader and PlantPheno data (FR-001). **Function Signatures**: `fetch_plantpheno() -> pd.DataFrame`, `fetch_rootreader() -> pd.DataFrame`, `parse_rootreader(df: pd.DataFrame) -> pd.DataFrame`. **Constraint**: Use `datasets.load_dataset` with `streaming=True` if dataset is large; otherwise use direct URL fetch. **Constraint**: MUST fail loudly (raise Exception) if real data fetch fails; NO synthetic fallback. **Constraint**: If RootReader source is unverified or missing, proceed with PlantPheno only and log a warning.
- [ ] T014a [US1] Initialize State File: Create `artifacts/state.json` with initial empty structure. **Verification**: Confirm file exists and is valid JSON.
- [ ] T014 [US1] Check for Phosphorus/Nitrogen columns in PlantPheno data. **Action**: Verify existence of columns `phosphorus` and `nitrogen` (or aliases). **Constraint**: If P/N columns are missing, DO NOT halt. Instead, set a flag `p_n_available=False` in `artifacts/state.json` (via T014b), log a warning that the hypothesis is "Unverifiable" per Plan, and proceed to T015 with root-only data. **Constraint**: If P/N columns exist, set `p_n_available=True` and proceed. **Verification**: Confirm the `p_n_available` flag is set correctly in `artifacts/state.json`. **Prerequisite**: T013. <!-- ATOMIZE: requested -->
- [ ] T014b [US1] Update State File: Write the `p_n_available` flag to `artifacts/state.json`. **Prerequisite**: T014.
- [ ] T014c [US1] Check P/N Availability and Flag: If `p_n_available` is False, explicitly log the "Hypothesis Unverifiable" status to `logs/deviation.log` and set a flag in `artifacts/state.json`. **Prerequisite**: T014b.
- [X] T015g [US1] Verify ISRIC Source: Check for a verified ISRIC source in the project's `# Verified datasets` block or `code/config.py`. **Action**: If no verified source exists, log "FR-002: ISRIC merge excluded due to lack of verified source" to `logs/deviation.log`. **Constraint**: This task must run BEFORE T015 to establish the deviation policy. **Verification**: Confirm log entry exists.
- [ ] T015h [US1] Record FR-003 Deviation: Log "FR-003: KNN imputation excluded to preserve statistical validity; missing nutrients are excluded" to `logs/deviation.log`. **Constraint**: This task must run BEFORE T015c to establish the deviation policy. **Verification**: Confirm log entry exists.
- [X] T015a [US1] Detect Data Source Type Column: Implement logic to detect `data_source_type` column in `code/data_ingestion.py`. **Action**: Check for column or aliases (`source_type`, `experiment_type`, `data_origin`). Raise `ValueError` if not found. **Prerequisite**: T013.
- [ ] T015b [US1] Filter by Data Source Type: Filter out rows where `data_source_type` indicates 'manipulated' or 'controlled' nutrient conditions (FR-012). **Constraint**: Filter out rows where the detected column value is in `['manipulated', 'controlled', 'nutrient_manipulation', 'treatment']`. **Do NOT** exclude rows simply labeled 'experimental' unless they imply manipulation. **Prerequisite**: T015a.
- [ ] T015c [US1] Filter by Missing Nutrients: If `p_n_available` is True, exclude rows where Phosphorus or Nitrogen values are missing (NaN). **Do NOT impute**. **Constraint**: Log the exact count of rows excluded. **Prerequisite**: T014b, T015h.
- [ ] T015d [US1] Filter by Sample Size: Exclude species with n < 20. **Constraint**: Log the exact count of species and rows excluded. **Prerequisite**: T015b, T015c.
- [ ] T015e [US1] Log Counts: Write a JSON file `artifacts/reports/species_counts.json` containing keys: `total_species_input` (integer), `excluded_species_count` (integer), `excluded_species_list` (list of species names), `rows_excluded_by_source` (integer), `rows_excluded_by_missing_nutrients` (integer), `rows_excluded_by_sample_size` (integer). **Prerequisite**: T015b, T015c, T015d.
- [ ] T015i [US1] Consolidate Deviation Log: Ensure `logs/deviation.log` contains entries for FR-002 and FR-003 deviations. **Prerequisite**: T015g, T015h.
- [ ] T015 [US1] (Consolidated) Implement filtering logic in `code/data_ingestion.py` to exclude species with n<20 AND exclude rows where `data_source_type` indicates 'manipulated' or 'controlled' nutrient conditions (FR-001, FR-012). **Prerequisite**: T014, T015a, T015b, T015c, T015d. **Constraint**: **Data Source Type Detection**: Implement logic to detect `data_source_type` column. If missing, check for known aliases (e.g., `source_type`, `experiment_type`, `data_origin`). Raise a clear `ValueError` if no matching column is found after checking aliases. **Constraint**: **Exclusion Logic**: Filter out rows where the detected column value is in `['manipulated', 'controlled', 'nutrient_manipulation', 'treatment']`. **Do NOT** exclude rows simply labeled 'experimental' unless they imply manipulation. **Constraint**: **Missing Nutrient Exclusion**: If `p_n_available` is True, also exclude rows where Phosphorus or Nitrogen values are missing (NaN). **Do NOT impute**. **Constraint**: **Logging**: Log the exact count of rows excluded due to `data_source_type`, missing nutrients, and species < 20 directly within this function. **Constraint**: **Output**: Write a JSON file `artifacts/reports/species_counts.json` containing keys: `total_species_input` (integer), `excluded_species_count` (integer), `excluded_species_list` (list of species names). This file is required for T035b.
- [ ] T035c [US1] **Measure Original SC-001 Failure**: Calculate the original SC-001 metric (proportion of datasets merged with ISRIC) which is [deferred] due to exclusion. Write result to `artifacts/reports/metrics.json` with key `sc001_original_merge_rate` = 0.0 and note `reason: "ISRIC source unavailable; FR-002 excluded"`. **Prerequisite**: T015g.
- [ ] T035a [US1] **Calculate P/N Availability Rate**: Calculate 'P/N Availability Rate' (rows with P/N / total rows) as a redefinition of SC-001 due to ISRIC exclusion. Write result to `artifacts/reports/metrics.json`. **Constraint**: **Denominator**: Total rows in raw PlantPheno dataset. **Constraint**: **Output**: Write the calculated rate to `artifacts/reports/metrics.json` under key `pn_availability_rate` and include a note `original_sc001_metric: merge_success_rate (unavailable due to scope deviation)`. **Constraint**: Explicitly link this calculation to the formal amendment record in `artifacts/sc_amendments.json` (AM-001) by reading that file first. **Prerequisite**: T015, T035c.
- [ ] T035b [US1] **Calculate SC-005 Ratio**: Calculate SC-005 ratio (number of species excluded due to n < 20 / total number of species in input) and write to `artifacts/reports/metrics.json`. **Constraint**: **Input**: Read `artifacts/reports/species_counts.json` (from T015) to get `total_species_input` and `excluded_species_count`. **Constraint**: **Output**: Write the calculated ratio to `artifacts/reports/metrics.json` under key `species_exclusion_ratio`. **Prerequisite**: T015.
- [X] T016 [US1] Implement `code/preprocessing.py` for log-transformation of root metrics and z-score normalization (global, across all species) of nutrients (FR-003, Const VII). **Prerequisite**: T014, T015. **Constraint**: **Order of Operations**: Normalize nutrients ONLY after T015 has excluded rows with missing nutrients. **Constraint**: **Conditional Execution**: If `p_n_available` is False (should not happen per T014), skip nutrient normalization but still perform root log-transform. If `p_n_available` is True, calculate z-score on the *remaining* valid rows (after T015 exclusion) and apply.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Modeling and Association Analysis (Priority: P2)

**Goal**: Fit Linear Mixed-Effects Models (LMM) and baseline Random Forest models to quantify nutrient-architecture relationships, perform species-level cross-validation, and report statistical significance.

**Independent Test**: The modeling step can be tested by running the training script on the preprocessed dataset and verifying the output JSON contains R², RMSE, and p-values for the LMM coefficients, ensuring the random forest baseline is also evaluated.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T020 [P] [US2] Contract test for model output schema (R², p-values) in `tests/contract/test_schemas.py` - **Function**: `test_model_metrics_schema_validates_fields` - Validates `contracts/model_results.schema.yaml` fields (lmm.adjusted_r_squared, lmm.p_values, etc.). *Prerequisite: T020a (Schema Definition)*
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
- [ ] T026b [US2] Verify F-Test Results: Ensure F-test results are logged and valid. **Action**: Read F-test p-values and verify they are within [0, 1]. Log "F-test verification passed" or "F-test verification failed". **Prerequisite**: T026.
- [X] T027 [US2] Implement multiple-comparison correction (Bonferroni or FDR) for hypothesis testing in `code/modeling.py` (FR-010)
- [ ] T028a [US2] **Fetch Literature Ranges**: Implement a local verification script to fetch and verify physiological ranges for Phosphorus and Nitrogen coefficients from a specific, verified public dataset (e.g., HuggingFace 'plant-physiology' or similar). **Output**: Write verified ranges to `artifacts/literature_ranges.json`. **Constraint**: Must cite specific literature sources. **Verification**: Ensure script runs without external agent dependency. <!-- FAILED: unspecified -->
- [~] T028b [US2] **Implement Sensitivity Analysis**: Implement sensitivity analysis of nutrient coefficients against literature ranges (FR-011). **Action**: Re-calculate coefficients with ±10% variation in input nutrients. **Output**: Generate `artifacts/sensitivity/sensitivity_analysis.json`. **Required Keys**: `percent_deviation` (float), `literature_mean` (float), `observed_coefficient` (float), `confidence_interval` (list of 2 floats), `literature_overlap` (boolean). **Constraint**: Use physiological ranges from `artifacts/literature_ranges.json` (verified by T028a). **Prerequisite**: T024, T028a.
- [~] T028c [US2] **Report Sensitivity**: Update `artifacts/sensitivity/sensitivity_analysis.json` with final sensitivity report. **Prerequisite**: T028b.
- [~] T029a [US2] **Generate Raw Metrics**: Generate output JSON with adjusted R², RMSE, p-values, and cross-validation mean R² for both models. **Constraint**: Consume `artifacts/sensitivity/sensitivity_analysis.json` (from T028b). **Prerequisite**: T023, T024, T025, T028b.
- [~] T029b [US2] **Calculate Derived Metrics**: Calculate R² difference (LMM - RF) and report raw values (FR-004, FR-005, FR-006, SC-002). **Constraint**: Explicitly calculate `sc002_met` = `abs(lmm_r2 - rf_r2) <= 0.05` and write this boolean to the JSON. **Prerequisite**: T029a.
- [ ] T029c [US2] **Write Final JSON**: Write the final JSON to `artifacts/reports/model_metrics.json`. **Prerequisite**: T029b.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate partial dependence plots, compile final report with statistical findings, and ensure output size constraints are met.

**Independent Test**: The reporting step can be tested by running the visualization script and verifying that PNG files are generated for partial dependence plots and that the total output size is ≤100MB.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T030 [P] [US3] Contract test for report schema in `tests/contract/test_schemas.py` - **Function**: `test_final_report_schema_validates_structure` - Validates `contracts/output.schema.yaml` structure (tables, metrics, deviations). *Prerequisite: T030a (Schema Definition)*
- [X] T031 [P] [US3] Unit test for file size constraint enforcement in `tests/unit/test_reporting.py`

### Implementation for User Story 3

- [X] T032 [P] [US3] Implement `code/visualization.py` to generate partial dependence plots (wide percentile range) for nutrient-architecture relationships (FR-007)
 - **Constraint**: Use `seaborn` or `matplotlib`; range of a broad central percentile distribution.
- [X] T033 [US3] Implement `code/visualization.py` to save figures as PNGs, enforcing total size ≤100MB (FR-007, SC-004)
 - **Constraint**: Compress images or reduce DPI if size exceeds limit; log final size.
- [ ] T034 [US3] Implement `code/reporting.py` to compile final report including R², p-values, plots, and associational framing (FR-009). **Prerequisite**: T029c, T032, T033, T035a, T035b, T035c. **Constraint**: Explicitly state "associational" not "causal". **Constraint**: Read `logs/deviation.log` (from T015i) and include the list of deviations in the report. **Constraint**: Read `artifacts/reports/model_metrics.json` (from T029c) and include the calculated metrics. **Constraint**: Read `artifacts/reports/metrics.json` (from T035a/b/c) and include the redefined success criteria.
- [ ] T036 [US3] Verify biological plausibility of coefficients against literature in final report (FR-011, SC-006). **Constraint**: **Input**: Read `artifacts/reports/metrics.json` (from T035a/b) and `artifacts/sensitivity/sensitivity_analysis.json` (from T028c). **Constraint**: **Output**: Include a Markdown table in the final report comparing coefficients to literature ranges. This table MUST be generated from the JSON files. **Constraint**: Ensure the report explicitly states whether coefficients fall within the expected physiological ranges.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories (Plan-mandated)

- [ ] T037a [P] Init State File: Create `state/projects/PROJ-457-predicting-plant-root-architecture-from-.yaml` with initial structure. **Verification**: Confirm file exists and is valid YAML.
- [ ] T037 [P] Update State File: Calculate content hashes for all artifacts in `artifacts/` and update the state file with these hashes (Constitution Principle V, Plan Task 4.3). **Action**: Run `find artifacts/ -type f -exec sha256sum {} \;` and write the output to `state/projects/PROJ-457-predicting-plant-root-architecture-from-.yaml` under `artifact_hashes`. **Constraint**: Ensure the state file is updated with the new timestamp. **Prerequisite**: T037a.
- [ ] T038 Update `README.md` and `docs/` with final results, including the `literature_comparison` findings and the `spec_deviations` list (Plan Task 4.4).
- [ ] T039 Run `quickstart.md` validation to ensure reproducibility (Plan Task 4.1).

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