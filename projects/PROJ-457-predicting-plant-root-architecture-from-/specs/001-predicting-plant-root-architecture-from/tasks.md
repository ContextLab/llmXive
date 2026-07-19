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

- [ ] T001 Create project structure per implementation plan: `code/`, `tests/`, `data/raw/`, `data/processed/`, `artifacts/`, `artifacts/models/`, `artifacts/plots/`, `artifacts/reports/`, and `logs/`. **Deliverable**: Execute `mkdir -p code/ tests/ data/raw data/processed artifacts/models artifacts/plots artifacts/reports logs` and verify all directories exist. Write a success confirmation message with timestamp to `logs/setup.log`. **Constraint**: Ensure `logs/` directory is created as it is required for T015 logging.
- [X] T002 Initialize Python 3.11+ project: Create `code/requirements.txt` with dependencies `pandas`, `scikit-learn`, `statsmodels`, `seaborn`, `matplotlib`, `pyyaml`, `geopandas` and run `pip install -r code/requirements.txt`, then pin versions via `pip freeze > code/requirements.txt`. **Note**: Removed `soilgrids` and `rasterio` as ISRIC merge is excluded per Plan. <!-- FAILED: unspecified -->
- [X] T003 [P] Configure linting (flake8/black): Create `.flake8` and `pyproject.toml` with black/flake8 settings and run `black --check code/`

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

**Independent Test**: The pipeline can be fully tested by running the data ingestion script on a sample subset and verifying the output CSV contains the required columns (species, root_length, branching_density, surface_area, phosphorus, nitrogen) with no null values in the predictor columns and at least 20 rows per species.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Contract test for merged dataset schema in `tests/contract/test_schemas.py` - **Function**: `test_merged_dataset_schema_validates_columns` - Validates `contracts/dataset.schema.yaml` columns (species, root_length, branching_density, surface_area, phosphorus, nitrogen). *Prerequisite: T007 (Schema Definition)*
- [X] T010 [P] [US1] Unit test for log-transformation handling of zeros/negatives in `tests/unit/test_preprocessing.py`
- [X] T012 [US1] Integration test for full ingestion pipeline end-to-end in `tests/integration/test_pipeline.py`

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/data_ingestion.py` to download/parse RootReader and PlantPheno data (FR-001). **Function Signatures**: `fetch_plantpheno() -> pd.DataFrame`, `fetch_rootreader() -> pd.DataFrame`, `parse_rootreader(df: pd.DataFrame) -> pd.DataFrame`. **Constraint**: Use `datasets.load_dataset` with `streaming=True` if dataset is large; otherwise use direct URL fetch. **Constraint**: MUST fail loudly (raise Exception) if real data fetch fails; NO synthetic fallback. **Constraint**: If RootReader source is unverified or missing, proceed with PlantPheno only and log a warning. <!-- FAILED: unspecified -->
- [ ] T014 [US1] Check for Phosphorus/Nitrogen columns in PlantPheno data. **Action**: Verify existence of columns `phosphorus` and `nitrogen` (or aliases). **Constraint**: If missing, **raise a `ValueError`** with message "Critical: P/N columns missing. Cannot proceed. Spec Deviation required." Do NOT proceed with 'root metrics only' as this violates US-1 acceptance criteria. **Constraint**: If P/N columns exist, set a flag `p_n_available=True` in the global config/state and proceed to T015.
- [ ] T015 [US1] Implement filtering logic in `code/data_ingestion.py` to exclude species with n<20 AND exclude rows where `data_source_type` indicates 'manipulated' or 'controlled' nutrient conditions (FR-001, FR-012). **Prerequisite**: T014. **Constraint**: **Data Source Type Detection**: Implement logic to detect `data_source_type` column. If missing, check for known aliases (e.g., `source_type`, `experiment_type`, `data_origin`). Raise a clear `ValueError` if no matching column is found after checking aliases. **Constraint**: **Exclusion Logic**: Filter out rows where the detected column value is in `['manipulated', 'controlled', 'nutrient_manipulation', 'treatment']`. **Do NOT** exclude rows simply labeled 'experimental' unless they imply manipulation. **Constraint**: **Missing Nutrient Exclusion**: If `p_n_available` is True, also exclude rows where Phosphorus or Nitrogen values are missing (NaN). **Do NOT impute**. **Constraint**: **Logging**: Log the exact count of rows excluded due to `data_source_type`, missing nutrients, and species < 20 directly within this function. **Constraint**: **Output**: Write a JSON file `artifacts/reports/species_counts.json` containing keys: `total_species_input` (integer), `excluded_species_count` (integer), `excluded_species_list` (list of species names). This file is required for T035b.
- [ ] T015b [US1] Record Spec Deviation FR-002 (ISRIC Merge Exclusion) in `artifacts/deviations.json`. **Constraint**: Append a JSON object `{"fr_id": "FR-002", "deviation": "ISRIC merge excluded due to lack of verified source; proceeding with PlantPheno only.", "impact": "SC-001 metric redefined as P/N Availability Rate"}` to the list in `artifacts/deviations.json`. **Prerequisite**: T015.
- [ ] T015c [US1] Record Spec Deviation FR-003 (KNN Imputation Exclusion) in `artifacts/deviations.json`. **Constraint**: Append a JSON object `{"fr_id": "FR-003", "deviation": "KNN imputation excluded to preserve statistical validity; missing nutrients are excluded.", "impact": "Data reduction, not imputation"}` to the list in `artifacts/deviations.json`. **Prerequisite**: T015.
- [X] T016 [US1] Implement `code/preprocessing.py` for log-transformation of root metrics and z-score normalization (global, across all species) of nutrients (FR-003, Const VII). **Prerequisite**: T014, T015. **Constraint**: **Order of Operations**: Normalize nutrients ONLY after T015 has excluded rows with missing nutrients. **Constraint**: **Conditional Execution**: If `p_n_available` is False (should not happen per T014), skip nutrient normalization but still perform root log-transform. If `p_n_available` is True, calculate z-score on the *remaining* valid rows (after T015 exclusion) and apply.
- [ ] T019 [US1] **REMOVED**: Logging for exclusion counts is now embedded within T015 and T016.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Modeling and Association Analysis (Priority: P2)

**Goal**: Fit Linear Mixed-Effects Models (LMM) and baseline Random Forest models to quantify nutrient-architecture relationships, perform species-level cross-validation, and report statistical significance.

**Independent Test**: The modeling step can be tested by running the training script on the preprocessed dataset and verifying the output JSON contains R², RMSE, and p-values for the LMM coefficients, ensuring the random forest baseline is also evaluated.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T020 [P] [US2] Contract test for model output schema (R², p-values) in `tests/contract/test_schemas.py` - **Function**: `test_model_metrics_schema_validates_fields` - Validates `contracts/model_results.schema.yaml` fields (lmm.adjusted_r_squared, lmm.p_values, etc.).
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
- [X] T027 [US2] Implement multiple-comparison correction (Bonferroni or FDR) for hypothesis testing in `code/modeling.py` (FR-010)
- [X] T028 [US2] Implement sensitivity analysis of nutrient coefficients against literature ranges (FR-011). **Output**: Generate `artifacts/sensitivity/sensitivity_analysis.json`. **Required Keys**: `percent_deviation` (float), `literature_mean` (float), `observed_coefficient` (float), `confidence_interval` (list of 2 floats), `literature_overlap` (boolean). **Constraint**: Use physiological ranges defined in `code/config.py` (hardcoded from literature). **Prerequisite**: T024.
- [ ] T029 [US2] Generate output JSON with adjusted R², RMSE, p-values, and cross-validation mean R² for both models; include logic to calculate R² difference (LMM - RF) and report raw values (FR-004, FR-005, FR-006, SC-002). **Prerequisite**: T023, T024, T025, T028. **Constraint**: Consume `artifacts/sensitivity/sensitivity_analysis.json` (from T028) and merge results into `artifacts/reports/model_metrics.json`. The final JSON must contain both model metrics and sensitivity findings. **Constraint**: Do NOT invent a `sc002_status` flag. Only report the calculated R² difference and the raw R² values. **Constraint**: Ensure the output JSON is written to `artifacts/reports/model_metrics.json`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate partial dependence plots, compile final report with statistical findings, and ensure output size constraints are met.

**Independent Test**: The reporting step can be tested by running the visualization script and verifying that PNG files are generated for partial dependence plots and that the total output size is ≤100MB.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US3] Contract test for report schema in `tests/contract/test_schemas.py` - **Function**: `test_final_report_schema_validates_structure` - Validates `contracts/output.schema.yaml` structure (tables, metrics, deviations).
- [X] T031 [P] [US3] Unit test for file size constraint enforcement in `tests/unit/test_reporting.py`

### Implementation for User Story 3

- [ ] T032 [P] [US3] Implement `code/visualization.py` to generate partial dependence plots (wide percentile range) for nutrient-architecture relationships (FR-007)
 - **Constraint**: Use `seaborn` or `matplotlib`; range of a broad central percentile distribution.
- [ ] T033 [US3] Implement `code/visualization.py` to save figures as PNGs, enforcing total size ≤100MB (FR-007, SC-004)
 - **Constraint**: Compress images or reduce DPI if size exceeds limit; log final size.
- [ ] T034 [US3] Implement `code/reporting.py` to compile final report including R², p-values, plots, and associational framing (FR-009). **Prerequisite**: T029, T032, T033. **Constraint**: Explicitly state "associational" not "causal". **Constraint**: Read `artifacts/deviations.json` (from T015b/c) and include the list of deviations in the report. **Constraint**: Read `artifacts/reports/model_metrics.json` (from T029) and include the calculated metrics. **Constraint**: Read `artifacts/reports/metrics.json` (from T035a/b) and include the redefined success criteria.
- [ ] T035a [US3] Calculate 'P/N Availability Rate' (rows with P/N / total rows) as a redefinition of SC-001 due to ISRIC exclusion. Write result to `artifacts/reports/metrics.json`. **Constraint**: **Denominator**: Total rows in raw PlantPheno dataset. **Constraint**: **Output**: Write the calculated rate to `artifacts/reports/metrics.json` under key `pn_availability_rate` and include a note `original_sc001_metric: merge_success_rate (unavailable due to scope deviation)`. **Constraint**: Explicitly state in the JSON that this metric replaces SC-001 due to the exclusion of ISRIC merge. **Prerequisite**: T015.
- [ ] T035b [US3] Calculate SC-005 ratio (number of species excluded due to n < 20 / total number of species in input) and write to `artifacts/reports/metrics.json`. **Constraint**: **Input**: Read `artifacts/reports/species_counts.json` (from T015) to get `total_species_input` and `excluded_species_count`. **Constraint**: **Output**: Write the calculated ratio to `artifacts/reports/metrics.json` under key `species_exclusion_ratio`. **Prerequisite**: T015, T035a.
- [ ] T036 [US3] Verify biological plausibility of coefficients against literature in final report (FR-011, SC-006). **Constraint**: **Input**: Read `artifacts/reports/metrics.json` (from T035a/b) and `artifacts/sensitivity/sensitivity_analysis.json` (from T028). **Constraint**: **Output**: Include a Markdown table in the final report comparing coefficients to literature ranges. This table MUST be generated from the JSON files. **Constraint**: Ensure the report explicitly states whether coefficients fall within the expected physiological ranges.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories (Plan-mandated)

- [ ] T037 [P] Update State File: Calculate content hashes for all artifacts in `artifacts/` and update the state file with these hashes (Constitution Principle V, Plan Task 4.3). **Action**: Run `find artifacts/ -type f -exec sha256sum {} \;` and write the output to `state/projects/PROJ-457-predicting-plant-root-architecture-from-.yaml` under `artifact_hashes`. **Constraint**: Ensure the state file is updated with the new timestamp.
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
- **State Transfer**: Deviations and metrics are written to persistent JSON files (`artifacts/deviations.json`, `artifacts/reports/metrics.json`) to ensure deterministic consumption by the reporting phase.