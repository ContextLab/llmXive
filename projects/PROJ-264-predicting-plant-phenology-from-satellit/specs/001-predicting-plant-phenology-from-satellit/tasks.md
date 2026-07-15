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

- [X] T001a [P] Create `src/` directory structure
- [X] T001b [P] Create `tests/` directory structure
- [X] T001c [P] Create `data/raw/` and `data/processed/` directories
- [X] T001d [P] Create `artifacts/` and `artifacts/models/` directories
- [ ] T002 {{claim:c_1ed3d08c}}
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `src/config.py` adhering to JSON Schema contract defined in `contracts/config_schema.json` for paths, seeds, and API keys (no hardcoded secrets)
- [ ] T005 [P] Create `src/lib/utils.py` with logging setup, random seed initialization, and deterministic file I/O helpers
- [~] T006 [P] Setup `tests/contract/` framework using `pytest-jsonschema` to validate `config.py` against `contracts/config_schema.json` and output artifacts against `data-model.md`
- [ ] T007 Create `data/provenance.yaml` schema and initialization logic to record API endpoints, checksums, and processing params
- [~] T008 Implement data directory structure with checksumming scripts for `data/raw/` and `data/processed/`
- [X] T009a Implement Google Earth Engine Service Account authentication setup in `src/data/ingestion.py` using a pre-seeded Service Account JSON key via environment variable `GOOGLE_EARTH_ENGINE_CREDENTIALS` (not interactive auth) to enable API access for CI reproducibility (Constitution Principle I)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Alignment (Priority: P1) 🎯 MVP

**Goal**: Download, process, and temporally align satellite, climate, and phenology data for a representative set of sites.

**Independent Test**: Run `src/data/ingestion.py` for a single site; verify output CSV contains synchronized rows for NDVI, EVI, temperature, precipitation, and phenology dates with no temporal gaps.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T037a [P] [US1] Contract test for `src/data/ingestion.py` output schema in `tests/contract/test_dataset_schema.py`
- [X] T010 [P] [US1] Integration test for data alignment logic in `tests/integration/test_pipeline.py`

### Implementation for User Story 1

- [X] T011a [US1] Implement logic in `src/data/ingestion.py` to calculate cloud-free coverage for spring (March-May) 2020 and select 10-15 study sites deterministically based on >80% coverage [UNRESOLVED-CLAIM: c_90eee386 — status=not_enough_info] from candidate sites list defined in config.py (FR-001) <!-- FAILED: unspecified -->
- [X] T011 [US1] Implement `src/data/ingestion.py` to download Sentinel data via Google Earth Engine API for the selected 10-15 sites (2018-2023), extracting NDVI/EVI at regular intervals, relying on authentication established in T009a (FR-001)
- [X] T012 [US1] Implement `src/data/ingestion.py` to retrieve daily climate data (temp, precip, solar) from NOAA GHCN and NASA POWER APIs using coordinate-based station lookup and align with satellite timestamps (FR-002)
- [ ] T013 [US1] Implement `src/data/ingestion.py` to fetch ground-truth phenology observations from Nature's Notebook API using radius search to map observations to the selected sites defined in T011a (FR-003)
- [ ] T020 [US1] Implement `src/data/preprocessing.py` to create Lagged Feature Windows (e.g., Jan-Mar data to predict April event) to prevent data leakage (Plan: Feature Independence)
- [ ] T021 [US1] Implement `src/data/preprocessing.py` to exclude `gdd_cumulative` from raw inputs to avoid multicollinearity with temperature (Plan: Feature Independence)
- [ ] T014 [US1] Implement interpolation logic in `src/data/preprocessing.py`: Linear interpolate if ≤1 consecutive 10-day gaps; exclude rows if >1 gap; flag and exclude sites with zero cloud-free observations in critical windows (FR-008, Edge Case)
- [ ] T015 [US1] Implement logic to flag sites with <80% cloud-free coverage or zero observations in critical windows as "insufficient data" and exclude from training (Edge Case)
- [ ] T016 [US1] Implement logic to handle missing phenology labels by masking rows during training rather than imputation (Edge Case)
- [ ] T017 [US1] Implement `data/provenance.yaml` population with GEE endpoints, date ranges, processing_params, software_version, and checksums for all downloaded data, updating immediately after each T011-T013 step (Constitution Principle VI)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Predictive Model Training and Validation (Priority: P2)

**Goal**: Train XGBoost/LightGBM models with Spatial Block CV and Temporal Holdout.

**Independent Test**: Train model on subset; evaluate on held-out test site/year; verify numeric predictions and calculated RMSE/R².

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Contract test for model artifact schema in `tests/contract/test_output_schema.py`
- [ ] T019 [P] [US2] Integration test for Spatial Block Cross-Validation logic in `tests/integration/test_pipeline.py`

### Implementation for User Story 2

- [ ] T022 [US2] Implement `src/models/train.py` with XGBoost training logic, including fallback to LightGBM if XGBoost fails to converge (FR-004)
- [ ] T023 [US2] Implement `src/models/train.py` using {{claim:c_2ff485b7}} (golden_ratio, https://en.wikipedia.org/wiki/Golden_ratio) and Temporal Holdout (train on 2018-2021, test 2022-2023 [UNRESOLVED-CLAIM: c_8b981720 — status=not_enough_info]) as defined in Plan (Plan: Validation Strategy)
- [ ] T024 [US2] Implement `src/models/evaluate.py` to calculate RMSE, MAE, and R² on held-out test sets (FR-005)
- [ ] T024a [US2] [US2] Implement `src/models/evaluate.py` to train a simple linear regression baseline model using only 10-day aggregated mean temperature (matching T020 feature schema) and compare its performance against the primary model (SC-001)
- [ ] T025 [US2] Implement logic to calculate training set error, perform comparison with test set error to quantify overfitting, and report results (SC-002)
- [ ] T026 [US2] Implement separate model training or multi-output handling for distinct phenological events (budburst, flowering, senescence) (US-2 Scenario 2)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis and Predictor Importance (Priority: P3)

**Goal**: Perform sensitivity analysis on regularization parameters and rank predictors.

**Independent Test**: Run sensitivity script; verify plot/table shows RMSE variation across alpha sweep {0.01, 0.05, 0.1}.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Contract test for sensitivity report schema in `tests/contract/test_output_schema.py`

### Implementation for User Story 3

- [ ] T028 [US3] Implement `src/models/sensitivity.py` to sweep regularization parameter (alpha) over the discrete set {0.01, 0.05, 0.1} [UNRESOLVED-CLAIM: c_084c5d36 — status=not_enough_info] and report RMSE/R² variation (FR-006)
- [ ] T029 [US3] Implement `src/models/sensitivity.py` to calculate Permutation Importance for all predictors, explicitly measuring the increase in RMSE when features are permuted, and rank those with score > 0.01 (FR-007, SC-004)
- [ ] T030 [US3] Implement statistical summary generation to identify variables with highest predictive power across CV folds (US-3 Scenario 3)
- [ ] T031 [US3] Generate visualization of RMSE variation across the alpha sweep (SC-003)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032a [P] Update `README.md` with installation steps and usage instructions
- [ ] T032b [P] Add docstrings to `src/data/ingestion.py`, `src/models/train.py`, and `src/models/sensitivity.py`
- [ ] T033a [P] Refactor `src/data/` for code clarity and modularity
- [ ] T033b [P] Refactor `src/models/` for code clarity and modularity
- [ ] T034 Performance optimization to ensure pipeline runs within 6-hour CI limit
- [ ] T035 [P] Additional unit tests in `tests/unit/`
- [ ] T036 Run `quickstart.md` validation to ensure end-to-end reproducibility

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

# Launch preprocessing and ingestion tasks:
Task: "Implement ingestion script in src/data/ingestion.py"
Task: "Implement interpolation logic in src/data/preprocessing.py"
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
- **CRITICAL**: Ensure data flow order: Ingestion (T011-T013) → Feature Engineering (T020, T021) → Filtering (T014, T015, T016) → Training (T022-T023) → Evaluation (T024-T025) → Sensitivity (T028-T030).
- **CRITICAL**: Authentication (T009a) MUST precede any API calls (T011a, T011).