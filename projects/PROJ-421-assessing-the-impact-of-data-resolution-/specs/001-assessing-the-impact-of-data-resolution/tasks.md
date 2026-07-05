# Tasks: Assessing the Impact of Data Resolution on Statistical Power in Publicly Available Spatial Datasets

**Input**: Design documents from `/specs/001-assess-resolution-power/`
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

- [X] T001 Create project directory structure: `mkdir -p projects/PROJ-421-assessing-the-impact-of-data-resolution-/code projects/PROJ-421-assessing-the-impact-of-data-resolution-/data/raw projects/PROJ-421-assessing-the-impact-of-data-resolution-/data/derived projects/PROJ-421-assessing-the-impact-of-data-resolution-/data/results projects/PROJ-421-assessing-the-impact-of-data-resolution-/tests`
- [X] T002 Create `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/requirements.txt` pinning `rasterio`, `geopandas`, `pysal`, `numpy`, `scipy`, `matplotlib`, `pandas`, `libpysal`.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes Calibration (formerly Phase 0).

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. **Phase 2 is a hard prerequisite for Phase 4.**

- [X] T004 Create base data models: Implement classes `ResolutionRaster` (fields: resolution, path, values) and `BinaryIndicatorMap` (fields: class_id, binary_values) in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/models.py`.
- [X] T005 [P] Implement `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/utils.py` with memory-mapped I/O helpers and windowed raster readers.
- [X] T006 [P] Setup logging infrastructure in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/utils.py`.
- [X] T007 Setup `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/config.py` for resolutions (30, 60, 120, 240, 480), seeds (seed=42), and paths.
- [X] T008 [P] Implement error handling and retry logic with exponential backoff in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/utils.py`.
- [ ] T009 [P] [US1] Implement checksumming and metadata validation utilities in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/utils.py::checksum_file`.
- [ ] T010 [US2] Implement `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/calibration.py::estimate_lambda(sample_path)` to estimate spatial lag parameter ($\lambda$) via MLE on a **[deferred] random sample (seed=42)** of the 30m data located at `data/raw/`. **Output**: Save fixed $\lambda$ value to `projects/PROJ-421-assessing-the-impact-of-data-resolution-/data/results/calibration_lambda.json`. <!-- FAILED: unspecified -->

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Resolution Aggregation (Priority: P1) 🎯 MVP

**Goal**: Download high-resolution NLCD data and generate coarser resolution rasters using nearest-neighbor resampling.

**Independent Test**: The script can be run in isolation to produce a directory of raster files at specified resolutions. Verification involves checking file existence, resolution metadata (pixel size), and verifying that categorical land cover values remain distinct integers without interpolation artifacts.

### Tests for User Story 1 (Write First)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T011 [P] [US1] Unit test for nearest-neighbor resampling logic in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/tests/test_resampling.py::test_nearest_neighbor_preserves_integers` (asserts that unique values in output == unique values in input).
- [ ] T012 [P] [US1] Integration test for download and aggregation pipeline in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/tests/test_integration.py`.

### Implementation for User Story 1

- [ ] T013 [P] [US1] Implement `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/data_ingestion.py` to download NLCD 30m subset for Colorado from verified HuggingFace URL: ` (configurable via `code/config.py` for API keys). Validate checksum using `utils.py::checksum_file`. Implement retry logic using `utils.py` utilities.
- [ ] T014 [US1] Implement `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/resampling.py::generate_resolution(input_path, factor)` function to generate a single coarser resolution raster using nearest-neighbor resampling, and implement the CLI loop to call it for factors [2, 4, 8, 16] (60m, 120m, 240m, 480m).
- [~] T015 [US1] Implement bounds checking to skip invalid resolutions that exceed dataset bounds in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/resampling.py`.
- [~] T016 [US1] Apply checksumming and metadata validation for all generated rasters using `code/utils.py::checksum_file`.
- [~] T017 [US1] Ensure chunked processing (windowed reads) is used in `code/resampling.py` to stay within 7GB RAM limit.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Spatial Autocorrelation Testing and Null/Alternative Simulation (Priority: P2)

**Goal**: Compute Moran's I statistics, generate null distributions (1,000 permutations), and simulate alternative distributions (Gibbs Sampler) to estimate statistical power.

**Independent Test**: The analysis script can be run on a single resolution file. Verification involves checking that the output contains a calculated Moran's I value, a p-value, and that the simulation count matches the configuration (1,000 permutations for H0, 1,000 simulations for H1).

### Tests for User Story 2

- [~] T018 [P] [US2] Unit test for binary indicator map transformation in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/tests/test_analysis.py`.
- [~] T019 [P] [US2] Unit test for Moran's I calculation and p-value generation in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/tests/test_analysis.py`.

### Implementation for User Story 2

- [~] T020 [P] [US2] Implement binary indicator map transformation in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/analysis.py` (e.g., Forest=1, Others=0).
- [~] T021 [US2] Implement H0 null distribution generation in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/analysis.py` using `pysal.esda.moran` with **EXACTLY 1,000 random permutations** to estimate p-values (FR-004).
- [~] T022 [US2] Implement `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/analysis.py::simulate_h1_gibbs(fixed_lambda, binary_map, seed)` using a **Gibbs Sampler (binary spatial autoregressive process)** to generate synthetic H1 data, and implement the execution loop to run **1,000 simulations** using the fixed $\lambda$ read from `data/results/calibration_lambda.json` with **seed=42** (from config) for reproducibility.
- [~] T023 [US2] Implement statistical power calculation in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/analysis.py`: compute the rejection rate of the H1 simulations (proportion where p < 0.05) by comparing against the critical value derived from the H0 distribution. This metric represents the statistical power (FR-005).
- [~] T024 [US2] Implement `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/analysis.py::validate_h1_structure` to compare synthetic H1 data's spatial autocorrelation against observed 30m data. The metric is the **absolute difference in Moran's I**; ensure it is within 5% error.
- [~] T025 [US2] Save results (Moran's I, p-values, power estimates) to CSV in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/data/results/`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Power Curve Generation and Threshold Identification (Priority: P3)

**Goal**: Generate a power-vs-resolution plot, identify the threshold where power < 0.80, and perform sensitivity analysis.

**Independent Test**: The plotting module can be run with pre-computed power data. Verification involves checking that a power curve is generated and that a specific resolution point is annotated where the power metric crosses the 0.80 line.

### Tests for User Story 3

- [~] T026 [P] [US3] Unit test for threshold identification logic in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/tests/test_analysis.py`.
- [~] T027 [P] [US3] Unit test for sensitivity analysis (±10% sweep) in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/tests/test_analysis.py`.

### Implementation for User Story 3

- [~] T028 [P] [US3] Implement `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/visualization.py` to generate Power-vs-Resolution curve.
- [~] T029 [US3] Implement `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/visualization.py::find_threshold(power_csv_path)` which returns the resolution string (e.g., '240m') where power < 0.80, and writes this to `projects/PROJ-421-assessing-the-impact-of-data-resolution-/data/results/threshold_report.txt`.
- [~] T030 [US3] Calculate Type II error delta (1 - power) relative to 30m baseline.
- [~] T031 [US3] Implement sensitivity analysis: sweep resolution aggregation factor by ±10% around inflection point. Verify the threshold does not vary by more than **one resolution step** (defined as the transition between adjacent levels in the geometric series, e.g., 30m->60m, 60m->120m).
- [~] T032 [US3] Generate sensitivity analysis report confirming threshold stability.
- [~] T033 [US3] Generate `projects/PROJ-421-assessing-the-impact-of-data-resolution-/data/results/final_report.md` containing the specific resolution threshold, Type II error delta, and sensitivity analysis results.
- [~] T034 [US3] Ensure p-value = 0.05 is treated as significant but flagged (add specific log flag and output column for p=0.05 cases).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final verification

- [~] T035 [P] Documentation updates in `docs/` and `README.md`.
- [~] T036 Code cleanup and refactoring.
- [~] T037 Performance optimization (verify < 6h runtime on CPU-only runner). <!-- ATOMIZE: requested -->
- [~] T038 [P] Additional unit tests in `tests/unit/`.
- [~] T039 [P] Execute Reference-Validator Agent to confirm NLCD URLs (verified HuggingFace/proxy URLs) are reachable and match primary sources (Title-token-overlap ≥ 0.7 where applicable) using command: `python -m code.reference_validator --input data/ --config code/config.py`.
- [~] T040 Run full pipeline on GitHub Actions runner to verify < 6h runtime and < 7GB RAM. <!-- ATOMIZE: requested -->
- [~] T041 Run `quickstart.md` validation.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - **BLOCKS all user stories**
 - **Calibration (Task T010)**: Must complete before Phase 4 (US2) as it provides the $\lambda$ parameter. **Phase 2 is a hard prerequisite for Phase 4.**
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on T010 (Lambda) and T013-T017 for input data
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on T018-T025 for power data

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
Task: "Unit test for nearest-neighbor resampling logic in tests/test_resampling.py::test_nearest_neighbor_preserves_integers"
Task: "Integration test for download and aggregation pipeline in tests/test_integration.py"

# Launch all implementation for User Story 1 together:
Task: "Implement data_ingestion.py to download NLCD 30m subset..."
Task: "Implement resampling.py to generate 60m, 120m, 240m, 480m rasters..."
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
 - Developer B: User Story 2 (requires T010 first)
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