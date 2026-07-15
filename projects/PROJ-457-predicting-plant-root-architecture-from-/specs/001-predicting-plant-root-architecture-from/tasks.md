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

- [ ] T001 Create project structure per implementation plan: `code/`, `tests/`, `data/raw/`, `data/processed/`, `artifacts/`, `artifacts/models/`, `artifacts/plots/`, `artifacts/reports/`. **Deliverable**: Run `ls -R` to verify directory creation and output the listing.
- [X] T002 Initialize Python 3.11+ project: Create `code/requirements.txt` with dependencies `pandas`, `scikit-learn`, `statsmodels`, `seaborn`, `matplotlib`, `pyyaml`, `geopandas`, `soilgrids`, `rasterio` and run `pip install -r code/requirements.txt`, then pin versions via `pip freeze > code/requirements.txt`
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

**Goal**: Ingest root phenotype data from RootReader/PlantPheno and soil nutrient data from ISRIC, filter for valid observations (n≥20 per species), merge with spatial interpolation, and produce a cleaned, merged dataset.

**Independent Test**: The pipeline can be fully tested by running the data ingestion script on a sample subset and verifying the output CSV contains the required columns (species, root_length, branching_density, surface_area, phosphorus, nitrogen) with no null values in the predictor columns and at least 20 rows per species.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Contract test for merged dataset schema in `tests/contract/test_schemas.py` - *Prerequisite: T007 (Schema Definition)*
- [X] T010 [P] [US1] Unit test for KNN imputation logic (k=5, Euclidean) in `tests/unit/test_preprocessing.py`
- [X] T011 [P] [US1] Unit test for log-transformation handling of zeros/negatives in `tests/unit/test_preprocessing.py`
- [X] T012 [US1] Integration test for full ingestion pipeline end-to-end in `tests/integration/test_pipeline.py`

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement `code/data_ingestion.py` to download/parse RootReader and PlantPheno data (FR-001)
 - **Constraint**: Use `datasets.load_dataset` with `streaming=True` if dataset is large; otherwise use direct URL fetch.
 - **Constraint**: MUST fail loudly (raise Exception) if real data fetch fails; NO synthetic fallback.
- [X] T014 [P] [US1] Implement `code/data_ingestion.py` logic to fetch ISRIC soil data automatically via `soilgrids` package and handle missing coordinates via nearest neighbor interpolation within a defined spatial radius using `geopandas` (FR-002, FR-012)
 - **Constraint**: Use `soilgrids` package for automated fetching. **Note**: The plan.md statement "ISRIC data requires manual provision" contradicts FR-002/FR-012; this task MUST implement automated fetching to satisfy the spec.
 - **Constraint**: Implement spatial join logic with a strict 10km radius as defined in FR-002.
 - **Constraint**: Log exclusion method if interpolation fails.
 - **Constraint**: NO user-provided file fallback; automated fetching is required for reproducibility.
 - **Research Question**: "How do soil phosphorus and nitrogen levels associate with root architectural traits across species?"
 - **Method**: "Nearest neighbor interpolation within 10km radius using `geopandas`."
 - **References**: "Hengl et al. (2017) [doi:/sdata.2017.62]."
- [X] T015 [US1] Implement filtering logic in `code/data_ingestion.py` to exclude species with n<20 AND exclude rows where `data_source_type` is 'experimental' or 'controlled' (FR-001, FR-012)
 - **Constraint**: **Data Source Type Detection**: Implement logic to detect `data_source_type` column. If missing, check for known aliases (e.g., `source_type`, `experiment_type`, `data_origin`). Raise a clear `ValueError` if no matching column is found after checking aliases.
 - **Constraint**: **Exclusion Logic**: Filter out rows where the detected column value is in `['experimental', 'controlled', 'manipulated']`.
 - **Constraint**: **Logging**: Log the exact count of rows excluded due to `data_source_type` and the specific method used for detection. Log exclusion counts for species < 20 and missing nutrients.
 - **Constraint**: Verify the exclusion logic was executed by checking the row count difference before and after filtering.
- [X] T019 [US1] Add logging for exclusion counts (species < 20, missing nutrients, experimental data) and transformation steps - *Prerequisite: T015*
- [X] T018 [US1] Merge root and soil datasets in `code/data_ingestion.py` ensuring no data leakage (species-level integrity) - *Prerequisite: T013, T014, T015*
- [X] T016 [US1] Implement `code/preprocessing.py` for log-transformation of root metrics and z-score normalization (global, across all species) of nutrients (FR-003, Const VII) - *Prerequisite: T018*
- [X] T017 [US1] Implement `code/preprocessing.py` KNN imputation (k=5, Euclidean, numeric only) with mean fallback (FR-003) - *Prerequisite: T018*

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Modeling and Association Analysis (Priority: P2)

**Goal**: Fit Linear Mixed-Effects Models (LMM) and baseline Random Forest models to quantify nutrient-architecture relationships, perform species-level cross-validation, and report statistical significance.

**Independent Test**: The modeling step can be tested by running the training script on the preprocessed dataset and verifying the output JSON contains R², RMSE, and p-values for the LMM coefficients, ensuring the random forest baseline is also evaluated.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Contract test for model output schema (R², p-values) in `tests/contract/test_schemas.py`
- [X] T021 [P] [US2] Unit test for species-level stratified split logic in `tests/unit/test_preprocessing.py`
- [X] T022 [US2] Integration test for model training and evaluation pipeline in `tests/integration/test_pipeline.py`

### Implementation for User Story 2

- [X] T023 [US2] Implement `code/modeling.py` to perform k-fold cross-validation split strictly by species (FR-006) - *Prerequisite: T018 (US1 output)*
 - **Constraint**: Use `GroupKFold` from `scikit-learn` with `groups=species`.
- [X] T024 [US2] Implement LMM fitting in `code/modeling.py` using `statsmodels` (REML, Satterthwaite p-values, species as random intercept) (FR-004)
 - **Constraint**: Ensure CPU-only execution (no GPU); use REML estimation.
- [X] T025 [US2] Implement Random Forest baseline in `code/modeling.py` (max_depth=5) for comparison (FR-005)
 - **Constraint**: Ensure CPU-only execution; limit `n_estimators` to ensure runtime < 6h.
- [X] T026 [US2] Implement F-test for overall model significance and coefficient p-values in `code/modeling.py` (FR-008)
- [X] T027 [US2] Implement multiple-comparison correction (Bonferroni or FDR) for hypothesis testing in `code/modeling.py` (FR-010)
- [X] T028 [US2] Implement sensitivity analysis of nutrient coefficients against literature ranges (FR-011)
 - **Constraint**: Use physiological ranges defined in `code/config.py` (hardcoded from literature).
 - **Constraint**: **Output**: Generate `artifacts/reports/sensitivity.csv` containing percent deviation from literature mean for each coefficient. This file MUST exist and be non-empty.
- [X] T029 [US2] Generate output JSON with adjusted R², RMSE, p-values, and cross-validation mean R² for both models; include logic to calculate R² difference (LMM - RF), evaluate against a predetermined threshold, set `sc002_status` to "PASS" or "FAIL", and update final report artifacts (FR-004, FR-005, FR-006, SC-002) - *Prerequisite: T023, T024, T025, T028*
 - **Constraint**: Explicitly flag success/failure of SC-002 in the output artifact.
 - **Constraint**: Calculate `r2_delta` and `sc002_status` internally before writing the JSON. The JSON MUST contain a key `sc002_status` with value "PASS" or "FAIL".
 - **Constraint**: Ensure the output JSON is written to `artifacts/reports/model_metrics.json`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate partial dependence plots, compile final report with statistical findings, and ensure output size constraints are met.

**Independent Test**: The reporting step can be tested by running the visualization script and verifying that PNG files are generated for partial dependence plots and that the total output size is ≤100MB.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T030 [P] [US3] Contract test for report schema in `tests/contract/test_schemas.py`
- [X] T031 [P] [US3] Unit test for file size constraint enforcement in `tests/unit/test_reporting.py`

### Implementation for User Story 3

- [X] T032 [P] [US3] Implement `code/visualization.py` to generate partial dependence plots (wide percentile range) for nutrient-architecture relationships (FR-007)
 - **Constraint**: Use `seaborn` or `matplotlib`; range of a broad central percentile distribution.
- [X] T033 [US3] Implement `code/visualization.py` to save figures as PNGs, enforcing total size ≤100MB (FR-007, SC-004)
 - **Constraint**: Compress images or reduce DPI if size exceeds limit; log final size.
- [X] T034 [US3] Implement `code/reporting.py` to compile final report including R², p-values, plots, and associational framing (FR-009)
 - **Constraint**: Explicitly state "associational" not "causal".
- [X] T035 [US3] Implement `code/reporting.py` to document excluded species and data coverage metrics (SC-001, SC-005)
 - **Constraint**: Calculate merge success rate (merged_count / total_available) and write to `artifacts/reports/metrics.json` under key `merge_success_rate`.
- [X] T036 [US3] Verify biological plausibility of coefficients against literature in final report (FR-011, SC-006)
 - **Constraint**: **Output**: Include a Markdown table in the final report comparing coefficients to literature ranges. This table MUST be generated from `artifacts/reports/sensitivity.csv` (created in T028) and `code/config.py`.
 - **Constraint**: Ensure the report explicitly states whether coefficients fall within the expected physiological ranges.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates in `docs/` and `README.md`
- [ ] T038 Code cleanup and refactoring (ensure PEP8 compliance)
- [ ] T039 Performance optimization (ensure execution ≤ 6 hours, RAM ≤ 6GB)
- [ ] T040 [P] Additional unit tests for edge cases (zero values, missing coords) in `tests/unit/`
- [ ] T041 Run `quickstart.md` validation to ensure reproducibility

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
Task: "Unit test for KNN imputation logic in tests/unit/test_preprocessing.py"

# Launch all models for User Story 1 together:
Task: "Implement data_ingestion.py to download/parse RootReader and PlantPheno data"
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
- **Constraint Check**: All tasks designed for CPU-only (a limited number of cores, 7GB RAM), no GPU, ≤6h runtime. No 8-bit/4-bit quantization or large model training.
- **Data Integrity**: All data loaders MUST fail loudly on fetch error; no synthetic fallbacks.
- **Streaming**: Large datasets MUST be streamed or sampled explicitly; no synthetic stand-ins.