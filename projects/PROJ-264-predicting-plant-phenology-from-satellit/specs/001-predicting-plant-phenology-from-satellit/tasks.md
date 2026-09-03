# Tasks: Predicting Plant Phenology from Satellite Imagery and Climate Data

**Input**: Design documents from `/specs/001-predict-plant-phenology/`
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

- [X] T001a [P] Create `src/` directory structure (subdirs: `data/`, `models/`, `cli/`, `lib/`)
- [X] T001b [P] Create `tests/` directory structure (subdirs: `contract/`, `integration/`, `unit/`)
- [X] T001c [P] Create `data/raw/` and `data/processed/` directories
- [X] T001d [P] Create `artifacts/` and `artifacts/models/` directories
- [X] T003a [P] Create `.ruff.toml` with exact configuration: `max-line-length = 100`, `ignore = ["E501"]`, `target-version = "py311"`
- [X] T003b [P] Create `.black.toml` with exact configuration: `line-length = 100`, `target-version = ["py311"]`
- [X] T002 [P] Initialize `src/lib/utils.py` with: `set_seed(seed=42)` function, `load_json(path)`, `save_json(obj, path)`, `setup_logging()` function. Ensure all functions use `json` module with `sort_keys=True` for deterministic output.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `src/config.py` adhering to JSON Schema contract defined in `contracts/config_schema.json`. The schema must define: `paths` (dict), `seeds` (dict), `api_keys` (dict, optional). The code must load this from `config/config.yaml` and validate against the schema using `jsonschema`.
- [X] T006 [P] Setup `tests/contract/` framework using `pytest-jsonschema` to validate `config.py` against `contracts/config_schema.json` and output artifacts against `data-model.md`. Create `tests/contract/test_config_schema.py` with a failing test initially.
- [X] T008 [P] Create `scripts/checksum_raw_data.py` that iterates `data/raw/`, computes SHA-256 hashes for each file, and writes `data/checksums.txt` in format: `<sha256_hash>  <relative_path>`.
- [X] T007 [P] Create `data/provenance.yaml` schema and initialization logic. The schema must include fields: `api_endpoint` (string), `date_range` (dict: start, end), `processing_params` (dict), `software_version` (string: "Python X.Y.Z; library==version"), `checksum` (string). Initialize with empty values.
- [X] T009 [P] Implement Google Earth Engine authentication setup in `src/data/ingestion.py`. The task must document the requirement for `earthengine authenticate` to be run on the runner or `GOOGLE_APPLICATION_CREDENTIALS` to be set via CI secret. Do NOT hardcode a pre-seeded key; ensure the code fails loudly if auth is missing. (Constitution Principle I).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Alignment (Priority: P1) 🎯 MVP

**Goal**: Download, process, and temporally align satellite, climate, and phenology data for a representative set of sites.

**Independent Test**: Run `src/data/ingestion.py` for a single site; verify output CSV contains synchronized rows for NDVI, EVI, temperature, precipitation, and phenology dates with no temporal gaps.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T037a [P] [US1] Contract test for `src/data/ingestion.py` output schema in `tests/contract/test_dataset_schema.py`
- [X] T010 [P] [US1] Integration test for data alignment logic in `tests/integration/test_pipeline.py`

### Implementation for User Story 1

- [X] T015 [US1] [P] Implement `filter_sites_by_coverage` in `src/data/ingestion.py`. Input: list of candidate sites (lat/lon). Logic: Query GEE for cloud cover in spring (March-May) 2020. Filter to sites with >80% cloud-free coverage. Output: `data/processed/selected_sites.csv` (site_id, lat, lon) and `data/processed/excluded_sites.log`. (FR-001, Edge Case). **Dependency**: Must run before T011.
- [X] T011 [US1] Implement `src/data/ingestion.py` to download Sentinel data via Google Earth Engine API for the sites listed in `data/processed/selected_sites.csv` (2018-2023). **Requirement**: Extract NDVI/EVI at regular intervals. **Requirement**: Implement streaming/chunking (using `ee.ImageCollection.limit()` or `dataset.iterate()`) to ensure RAM usage remains <6GB. (FR-001). **Dependency**: T015.
- [X] T012 [US1] Implement `src/data/ingestion.py` to retrieve daily climate data (temp, precip, solar) from NOAA GHCN and NASA POWER APIs using coordinate-based station lookup. Align with satellite timestamps (10-day intervals). (FR-002).
- [X] T013 [US1] Implement `src/data/ingestion.py` to fetch ground-truth phenology observations from Nature's Notebook API using radius search to map observations to the selected sites defined in `data/processed/selected_sites.csv`. (FR-003).
- [X] T014 [US1] Implement `src/data/preprocessing.py` to handle missing satellite data: 1) Linearly interpolate if ≤1 consecutive 10-day intervals are missing. 2) Exclude rows if >1 consecutive 10-day intervals are missing. 3) Flag and exclude sites with zero cloud-free observations in critical windows. (FR-008, Edge Case). **Dependency**: Runs after T011-T013.
- [X] T020 [US1] Implement `src/data/preprocessing.py` to create Lagged Feature Windows (e.g., Jan-Mar data to predict April event) to prevent data leakage. **Note**: Operates on the dataset *after* T014 has handled gaps. (Plan: Feature Independence).
- [X] T021 [US1] Implement `src/data/preprocessing.py` to exclude `gdd_cumulative` from raw inputs to avoid multicollinearity with temperature. **Note**: Operates on the dataset *after* T014 has handled gaps. (Plan: Feature Independence).
- [X] T016 [US1] Implement `mask_missing_labels` in `src/data/preprocessing.py`. Logic: Create a boolean mask array for rows with missing phenology labels. Ensure these rows are excluded during training (mask=True) rather than imputed. (Edge Case). **Dependency**: Runs after T014.
- [X] T019b [US1] [P] Implement `calculate_data_coverage` in `src/data/preprocessing.py`. Logic: Calculate the percentage of 10-day intervals with valid (non-interpolated and non-null) satellite data across all sites. Output: `artifacts/reports/data_coverage.json` with metrics per site and aggregate. (SC-005).
- [X] T017 [US1] Implement `data/provenance.yaml` population with GEE endpoints, date ranges, processing_params, **software_version** (Python + library versions), and checksums for all downloaded data. Update immediately after T011-T013 steps. (Constitution Principle VI).
- [X] T041 [US1] Implement strict error handling in `src/data/ingestion.py` for NOAA/NASA API calls: REMOVE any `try/except` blocks that fall back to synthetic/mock data. Ensure `raise` is called on fetch failure to trigger a loud failure. (Rule: Loader must fail loudly).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Predictive Model Training and Validation (Priority: P2)

**Goal**: Train XGBoost/LightGBM models with Spatial Block CV and Temporal Holdout.

**Independent Test**: Train model on subset; evaluate on held-out test site/year; verify numeric predictions and calculated RMSE/R².

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for model artifact schema in `tests/contract/test_output_schema.py`
- [X] T019 [P] [US2] Integration test for Spatial Block Cross-Validation logic in `tests/integration/test_pipeline.py`

### Implementation for User Story 2

- [X] T023 [US2] Implement `src/models/train.py` using **Spatial Block Cross-Validation (K=5 geographic clusters)** and **Temporal Holdout (train on a multi-year historical period, test 2022-2023)**. Use `sklearn.cluster.KMeans` on lat/lon coordinates for clustering. Log cluster assignments to `data/processed/spatial_clusters.json`. (Plan: Validation Strategy).
- [X] T022 [US2] Implement `src/models/train.py` with XGBoost training logic. Function: `train_model(data, params) -> artifacts/models/xgb_model_v1.pkl`. Serialization: `joblib.dump` with protocol=5. (FR-004).
- [X] T022b [US2] Implement `src/models/train.py` fallback logic to LightGBM if XGBoost fails to converge. Select the model with lower 5-fold cross-validation RMSE. (FR-004).
- [X] T025b [US2] [P] Implement `check_climate_overlap` in `src/models/evaluate.py`. Logic: Perform Kolmogorov-Smirnov test on temperature and precipitation distributions between train and test sets. Gate the overfitting report on the condition that p-value > 0.05 (overlap within 1 SD). Output: `data/processed/climate_overlap_check.json`. (SC-002).
- [X] T024 [US2] Implement `src/models/evaluate.py` to calculate RMSE, MAE, and R² on held-out test sets. Generate `artifacts/reports/metrics.json`. (FR-005).
- [X] T025 [US2] Implement logic to compare training set error vs test set error to quantify overfitting. **Dependency**: Must check `data/processed/climate_overlap_check.json` from T025b first. If overlap condition fails, report "Overfitting analysis invalid due to climate distribution shift". (SC-002).
- [X] T024a [US2] [US2] Implement `src/models/evaluate.py` to train a simple linear regression baseline model using temperature data and compare its performance against the primary model. Output: `artifacts/reports/baseline_comparison.json`. (SC-001).
- [X] T026a [US2] Implement separate model training for budburst events, saving to `artifacts/models/budburst_model.pkl`. (US-2 Scenario 2).
- [X] T026b [US2] Implement separate model training for flowering events, saving to `artifacts/models/flowering_model.pkl`. (US-2 Scenario 2).
- [X] T026c [US2] Implement separate model training for senescence events, saving to `artifacts/models/senescence_model.pkl`. (US-2 Scenario 2).
- [X] T039 [P] [US2] Implement `src/models/train.py` to enforce `max_depth=4` and `subsample=0.8` defaults to prevent overfitting on the small sample size (-15 sites) and ensure CPU tractability. (Plan: Small Sample Size).
- [X] T040 [US2] Implement `src/models/train.py` to log and report the specific spatial clusters formed for the 5-fold Spatial Block Cross-Validation, ensuring geographic separation. (Plan: Spatial Block CV).
- [X] T042 [US2] Implement `src/models/train.py` to explicitly log the exact random seed used for each CV fold split and model initialization to `data/processed/training_log.txt` in format: `seed=42; fold=0; split_date=...`. (Constitution Principle I).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis and Predictor Importance (Priority: P3)

**Goal**: Perform sensitivity analysis on regularization parameters and rank predictors.

**Independent Test**: Run sensitivity script; verify plot/table shows RMSE variation across alpha sweep {0.01, 0.05, 0.1}.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Contract test for sensitivity report schema in `tests/contract/test_output_schema.py`

### Implementation for User Story 3

- [X] T028 [US3] Implement `src/models/sensitivity.py` to sweep regularization parameter (alpha) over a discrete set of values. Calculate RMSE/R² on the held-out test set for each alpha. Report variation to `artifacts/reports/sensitivity_report.json`. (FR-006).
- [X] T029 [US3] Implement `src/models/sensitivity.py` to calculate Permutation Importance for all predictors. Use `n_permutations=10` and `random_seed=42`. Explicitly measure the increase in RMSE when features are permuted. Rank those with score > 0.01. (FR-007, SC-004).
- [X] T030 [US3] Implement statistical summary generation to identify variables with highest predictive power across CV folds. (US-3 Scenario 3).
- [X] T031 [US3] Generate visualization of RMSE variation across the alpha sweep and save to `artifacts/plots/sensitivity_plot.png`. (SC-003).
- [X] T043 [US3] Implement `src/models/sensitivity.py` to output a detailed `artifacts/reports/feature_importance_details.json`. Schema: `{"feature": str, "importance_score": float, "rmse_delta": float, "fold_scores": [float]}`. (US-3 Scenario 3).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T032a [P] Update `README.md` with installation steps, usage instructions, and a "Quick Start" section that runs T015 -> T011 -> T022 -> T024.
- [X] T032b [P] Add docstrings to `src/data/ingestion.py`, `src/models/train.py`, and `src/models/sensitivity.py` following Google Style Guide.
- [X] T033a [P] Refactor `src/data/` for code clarity and modularity (extract API clients into `src/data/clients/`).
- [X] T033b [P] Refactor `src/models/` for code clarity and modularity (extract metrics into `src/models/metrics.py`).
- [X] T034 [P] Profile `src/data/ingestion.py` and optimize chunking to reduce memory usage to <6GB. Verify by `tests/integration/test_memory.py` (asserts peak RAM < 6GB). (Plan: Performance).
- [X] T035 [P] Add `tests/unit/test_preprocessing.py::test_interpolation_handles_edge_cases` to cover FR-008 logic (1 gap vs >1 gap). (Plan: Testing).
- [X] T036 [P] Create `tests/integration/test_quickstart.py` that executes `quickstart.md` steps and asserts exit code 0 and artifact existence. (Plan: Validation).
- [X] T044 [P] Update `data/provenance.yaml` with a "Methodology Notes" section explicitly documenting the "Exploratory" nature of the study, the small sample size limitation, and the specific streaming/sampling rules used for data ingestion. (Plan: Exploratory Framing).

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on trained models from US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services (preprocessing)
- Services before endpoints (training/evaluation)
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
Task: "Contract test for ingestion output schema in tests/contract/test_dataset_schema.py"
Task: "Integration test for data alignment logic in tests/integration/test_pipeline.py"

# Launch preprocessing and ingestion tasks (Sequential):
Task: "T015: Filter sites by cloud coverage" -> "T011: Ingest data" -> "T014: Interpolate/Exclude" -> "T020: Feature Engineering"
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
 - Developer A: User Story 1 (Data Ingestion)
 - Developer B: User Story 2 (Model Training) - *Can start once data schema is defined*
 - Developer C: User Story 3 (Sensitivity Analysis) - *Can start once model API is defined*
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
- **CRITICAL**: All data downloads must use real, reachable URLs or API endpoints (GEE, NOAA, Nature's Notebook). No synthetic data.
- **CRITICAL**: All models must run on CPU-only CI (limited CPU and memory resources). No GPU, no 8-bit quantization.
- **CRITICAL**: Ensure data flow order: **T015 (Filter)** → **T011 (Ingest)** → **T014 (Interpolate/Exclude)** → **T020/T021 (Feature Engineering)** → **T016 (Mask Labels)** → **T022 (Train)** → **T025b (Check Overlap)** → **T025 (Report Overfitting)** → **T028 (Sensitivity)**.
- **CRITICAL**: Authentication (T009) MUST precede any API calls (T011).
- **CRITICAL**: Model hyperparameters (T039) must be constrained to ensure convergence on small datasets and prevent overfitting.
- **NEW**: T025b ensures SC-002 condition (climate overlap) is checked before overfitting reports.
- **NEW**: T019b ensures SC-005 (Data Coverage) is measured and reported.
- **NEW**: T009 ensures reproducibility by removing hardcoded secrets.
- **NEW**: T014 description explicitly matches FR-008 phrasing ("consecutive intervals").