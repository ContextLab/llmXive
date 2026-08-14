# Tasks: Understanding Oceanic Phytoplankton Communities through Remote Sensing and Oceanographic Data

**Input**: Design documents from `/specs/001-phytoplankton-vlm-analysis/`
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

 Tasks MUST be organized by user story so each story can:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan (`projects/PROJ-021-understanding-oceanic-phytoplankton-comm/`)
- [X] T002 Initialize Python 3.11 project with dependencies in `code/requirements.txt` (pandas, numpy, scikit-learn, torch, transformers, xarray, netCDF4, matplotlib, seaborn, datasets)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create configuration manager in `code/utils/config.py` (seeds, paths, hyperparameters, memory limits)
- [X] T005 [P] Implement CPU-only data loader utilities in `code/utils/data_loaders.py` (streaming, sampling to fit available RAM, strict error handling: NO synthetic fallback)
- [X] T006 Create base schema definitions in `specs/001-phytoplankton-vlm-analysis/contracts/` (phytoplankton_sample.schema.yaml, model_performance.schema.yaml)
- [X] T007 [P] Implement versioning utility in `code/05_versioning_state.py` (SHA-256 hashing logic to be called by Advancement-Evaluator Agent, not standalone script)
- [X] T008 Setup logging infrastructure in `code/utils/logging_config.py` (structured logs for pipeline monitoring)
- [ ] T009a [P] Create `aligned_dataset.schema.yaml` in `specs/001-phytoplankton-vlm-analysis/contracts/` defining the unified schema for the preprocessed dataset (lat, lon, timestamp, basin, temp, salinity, nutrients, chlorophyll-a, quality_flags).
- [ ] T009 [P] [US1] Contract test for schema validation in `tests/contract/test_schemas.py` (validates `aligned_dataset.schema.yaml` created in T009a). **Depends on T009a**.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest, align, and preprocess multi-modal satellite and oceanographic data into a unified, CPU-tractable dataset.

**Independent Test**: Run the pipeline script on a sample subset; verify output is a single aligned CSV/NetCDF with <5% missing values, correct basin stratification, and memory usage <7GB.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Integration test for data alignment in `tests/integration/test_pipeline.py` (verifies temporal/spatial alignment logic)

### Implementation for User Story 1

- [X] T011a [US1] Fetch NOAA/Copernicus Reanalysis data (Temperature, Salinity, Nutrients) from verified source to `data/raw/reanalysis.nc`. **Depends on T005**.
- [ ] T011b [US1] Fetch MODIS Aqua/Terra ocean color data from verified source to `data/raw/modis.nc`. **Depends on T005**.
- [ ] T011c [US1] Fetch SeaBASS in-situ data (Chl-a, SST, Salinity) from verified source `seabass/seabass` on HuggingFace to `data/raw/seabass.csv`. Handle authentication if required. **Depends on T005**. <!-- FAILED: unspecified -->
- [ ] T015 [US1] Implement strict quality flag filtering in `code/01_data_ingestion.py` to exclude MODIS pixels with "cloud" or "high aerosol" flags and Reanalysis anomalies from the fetched data (T011a, T011b, T011c) BEFORE preprocessing. Output filtered dataset to `data/raw/seabass_filtered.csv`. **Depends on T011a, T011b, T011c**. <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [X] T013a [US1] Validate ≥10-year temporal overlap in `code/02_preprocessing.py` on the filtered dataset and implement stratified train/val/test split logic by ocean basin, outputting split indices to `data/processed/split_indices.json`. **Depends on T015**.
- [X] T012 [US1] Implement spatial/temporal alignment in `code/02_preprocessing.py` (grid reanalysis and MODIS to a coarser resolution, create monthly composites). **Depends on T015, T013a**. <!-- FAILED: unspecified -->
- [X] T012a [US1] Implement linear interpolation for gaps ≤ 2 months and error quantification in `code/02_preprocessing.py`. Save interpolation error to `data/logs/interpolation_error.log`. **Depends on T012**.
- [X] T012b [US1] Implement logic to flag gaps > 2 months for EXCLUSION (not imputation) in `code/02_preprocessing.py`. Update dataset mask. **Depends on T012a**.
- [X] T013 [US1] Implement basin stratification and unified masking in `code/02_preprocessing.py` (retain basin ID, apply unified missing data mask across all sources, exclude grid cells with missing in-situ data). **Depends on T012b**.
- [ ] T013b [US1] Implement memory enforcement and logging in `code/02_preprocessing.py` to monitor RAM usage and enforce GB limit, logging to `data/logs/memory_enforcement.log`. **Depends on T013**.
- [X] T017 [US1] Generate final aligned dataset artifact in `data/processed/aligned_dataset.nc` (verify no missing values due to misalignment). **Depends on T013b**.
- [ ] T017a [US1] Calculate missing value percentage in `code/02_preprocessing.py` and verify SC-004 compliance (≤5% missing). Log result to `data/logs/missing_value_report.json`. **Depends on T017**.

---

## Phase 4: User Story 2 - Baseline and VLM Model Training (Priority: P2)

**Goal**: Train and evaluate a Random Forest baseline and a lightweight CLIP-based VLM (<500M params) on CPU.

**Independent Test**: Execute training script; verify RF completes <2h, VLM completes <4h with early stopping if needed, and output metrics (RMSE, R², MAE) for both.

### Tests for User Story 2 ⚠️

- [ ] T032 [P] [US2] Contract test for model metrics schema in `tests/contract/test_schemas.py` (validates model_performance.schema.yaml)
- [ ] T039 [P] [US2] Integration test for CPU feasibility in `tests/integration/test_pipeline.py` (verifies runtime <6h and RAM <7GB for full training)

### Implementation for User Story 2

- [ ] T018 [US2] Implement Random RF baseline in `code/03_model_training.py` (≤500 trees, scikit-learn, CPU-only, train/val split). **Depends on T017 (US1)**.
- [ ] T019 [US2] Implement lightweight CLIP-based VLM fine-tuning in `code/03_model_training.py` (concatenated image/text inputs). Text prompt template: "Temperature: {temp}, Salinity: {sal}, Nutrients: {nut}". Image preprocessing: resize to 224x224, normalize. CPU-only, early stopping after a small number of epochs if no convergence. If convergence fails, log failure and default to baseline model performance metrics, explicitly flagging the artifact as "VLM Failed (Baseline Used)". **Depends on T017 (US1)**.
- [ ] T020 [US2] Generate model performance artifact in `data/artifacts/model_comparison.csv` (includes basin-stratified R² scores, RMSE, MAE for both RF and VLM). **Depends on T018, T019**.
- [ ] T019a [US2] Perform statistical significance test in `code/04_evaluation.py` (paired t-test or bootstrap to validate if VLM R² exceeds baseline by ≥0.05, output p-value and confidence interval to `data/artifacts/significance_test.json`). **Depends on T020**.
- [ ] T020a [US2] Calculate basin variance metrics in `code/04_evaluation.py` (compute variance in R² scores across basins and difference between highest/lowest, output to `data/artifacts/basin_variance.json`). **Depends on T020**.

---

## Phase 5: User Story 3 - Feature Importance and Driver Quantification (Priority: P3)

**Goal**: Quantify driver contributions using permutation importance and generate spatial visualization maps.

**Independent Test**: Run feature importance analysis; verify output includes ranked driver list (sum=1.0) and spatial maps (GeoTIFF/PNG) for each basin.

### Tests for User Story 3 ⚠️

- [ ] T021 [P] [US3] Contract test for feature importance output in `tests/contract/test_schemas.py` (validates The importance scores sum to unity within a small tolerance.).
- [ ] T022 [P] [US3] Integration test for visualization generation in `tests/integration/test_pipeline.py` (verifies map files are generated correctly)

### Implementation for User Story 3

- [ ] T023 [US3] Implement permutation importance analysis in `code/04_evaluation.py` (rank drivers, normalize scores to sum=1.0, verify sum equals unity within a specified tolerance., record verification result in `data/logs/importance_verification.log`). Handle multicollinearity using VIF threshold (VIF > 5); if triggered, log warning and proceed without PCA to preserve spec assumptions. **Depends on T018, T020**.
- [ ] T025 [US3] Implement in-situ correlation analysis in `code/04_evaluation.py` (calculate correlation coefficient r between predictions and in-situ measurements per basin, AND compute and output the difference between highest and lowest basin R² to `data/artifacts/basin_r2_difference.json`). **Depends on T020**.
- [ ] T026 [US3] Generate final driver attribution artifacts in `data/artifacts/feature_importance_maps/` (include legend and basin labels). Implement spatial aggregation logic to ensure maps are at the same resolution as the aligned dataset, handling necessary resampling without introducing artifacts. **Depends on T023, T025**.
- [ ] T024 [US3] Implement spatial visualization generation in `code/04_evaluation.py` (create GeoTIFF/PNG maps of top driver importance per basin). **Depends on T023**.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T050 [P] [Orchestration] Implement End-to-End Pipeline Orchestration in `code/06_pipeline_orchestrator.py` to measure total runtime from T011a to T026, enforce time limit

The research question, method, and references remain as specified in the planning document., and aggregate memory logs from T013b and T018. Output `data/logs/pipeline_summary.json`. **Depends on T026**.
- [ ] T041 [P] Update `quickstart.md` with execution instructions for the full pipeline, including specific commands (`python code/06_pipeline_orchestrator.py`), environment variables (`MEMORY_LIMIT_GB`, `RUNTIME_LIMIT_HOURS`), and expected runtime outputs (summary JSON).
- [ ] T028 Code cleanup and refactoring in `code/` (remove debug prints, optimize memory usage)
- [ ] T029 [P] Run full integration test suite and verify all acceptance scenarios pass
- [ ] T030 [P] Update `state/projects/PROJ-021-understanding-oceanic-phytoplankton-comm.yaml` with final artifact hashes
- [ ] T031 [P] Validate `research.md` and `data-model.md` against generated artifacts

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
- Ingestion before preprocessing
- Preprocessing before training
- Training before evaluation
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
Task: "Contract test for schema validation in tests/contract/test_schemas.py"
Task: "Integration test for data alignment in tests/integration/test_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement SeaBASS data ingestion in code/01_data_ingestion.py"
Task: "Implement spatial/temporal alignment in code/02_preprocessing.py"
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