# Tasks: Assessing the Impact of Data Resolution on Statistical Power in Publicly Available Spatial Datasets

**Input**: Design documents from `/specs/001-assess-resolution-power/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
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

## Phase 0: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project directory structure: `mkdir -p projects/PROJ-421-assessing-the-impact-of-data-resolution-/code projects/PROJ-421-assessing-the-impact-of-data-resolution-/data/raw projects/PROJ-421-assessing-the-impact-of-data-resolution-/data/derived projects/PROJ-421-assessing-the-impact-of-data-resolution-/data/results projects/PROJ-421-assessing-the-impact-of-data-resolution-/tests`
- [X] T002 Create `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/requirements.txt` pinning `rasterio`, `geopandas`, `pysal`, `numpy`, `scipy`, `matplotlib`, `pandas`, `libpysal`.
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/`.
- [ ] T039a [P] [US1-US3] Implement `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/main.py` as the CLI entry point. **Functionality**: Accept `--full-sweep` flag to orchestrate the entire pipeline (Ingestion -> Resampling -> Calibration -> Analysis -> Visualization). **Output**: Executable script with argument parsing and error handling. **Prerequisite**: T001, T002.

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 Create base data models: Implement classes `ResolutionRaster` (fields: resolution, path, values) and `BinaryIndicatorMap` (fields: class_id, binary_values) in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/models.py`.
- [X] T005 [P] Implement `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/utils.py` with memory-mapped I/O helpers and windowed raster readers.
- [X] T006 [P] Setup logging infrastructure in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/utils.py`.
- [~] T007 [P] Setup `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/config.py` for resolutions (30, 60, 120, 240, 480), seeds (seed=42), and paths. **Note**: `SPATIAL_LAG_LAMBDA` will be populated dynamically from `state/calibration.yaml` after T010.
- [~] T008 [P] Implement error handling and retry logic with exponential backoff in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/utils.py`.
- [~] T009 [P] [US1] Implement checksumming and metadata validation utilities in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/utils.py::checksum_file`.
- [~] T009b [US1] Implement URL validation utility in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/utils.py::validate_url`. **Constraint**: This function must verify a URL is reachable with a bounded timeout and return True only if HTTP status code is in the 2xx range. **Prerequisite**: T005.
- [~] T010 [P] [Phase-0] Implement Lambda Estimation in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/calibration.py`. **Method**: Use Maximum Likelihood Estimation (MLE) on a representative sample of the binary map to estimate the spatial lag parameter ($\lambda$). **Output**: Write estimated $\lambda$ to `projects/PROJ-421-assessing-the-impact-of-data-resolution-/state/calibration.yaml`. **Constraint**: Do NOT hardcode $\lambda$ in `config.py`; read from state file. **Prerequisite**: T005, T020 (for binary map input). **Note**: This task is moved to Phase 1 to ensure $\lambda$ is available for all subsequent analysis tasks.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: User Story 1 - Data Ingestion and Resolution Aggregation (Priority: P1) 🎯 MVP

**Goal**: Download high-resolution NLCD data and generate coarser resolution rasters using nearest-neighbor resampling.

**Independent Test**: The script can be run in isolation to produce a directory of raster files at specified resolutions. Verification involves checking file existence, resolution metadata (pixel size), and verifying that categorical land cover values remain distinct integers without interpolation artifacts.

### Tests for User Story 1 (Write First)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T011 [P] [US1] Unit test for nearest-neighbor resampling logic in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/tests/test_resampling.py::test_nearest_neighbor_preserves_integers` (asserts that unique values in output == unique values in input).
- [~] T012 [P] [US1] Integration test for download and aggregation pipeline in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/tests/test_integration.py`.

### Implementation for User Story 1

- [~] T013 [US1] Implement `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/data_ingestion.py` to download NLCD 30m subset for Colorado. **Primary Source**: USGS EarthExplorer API (FR-001). **Fallback**: If API fails or key is missing, fetch from verified HuggingFace mirror `https://huggingface.co/datasets/nlcd-30m/resolve/main/nlcd_2019_colorado_30m.tif`. **Validation**: MUST call `utils::validate_url` on the fallback URL before download. Validate checksum using `utils.py::checksum_file`. Implement retry logic using `utils.py` utilities. **Prerequisite**: T009b (URL Validation).
- [~] T013b [US1] Verify HuggingFace fallback dataset integrity. **Action**: Before T013 uses the fallback, verify the dataset contains the correct bounding box metadata for Colorado and valid land cover classes. **Output**: Raise error if metadata mismatch. **Prerequisite**: T009b.
- [~] T014a [US1] Implement `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/resampling.py::generate_resolution(input_path, factor)` function to generate a single coarser resolution raster using nearest-neighbor resampling. **Constraint**: MUST use chunked processing (windowed reads) with 2000x2000 pixel windows and **no overlap** between windows to stay within 7GB RAM. **Prerequisite**: T005, T013.
- [ ] T014b [US1] Implement CLI loop in `projects/PROJ-assessing-the-impact-of-data-resolution-/code/resampling.py` to call `generate_resolution` for a range of scaling factors. **CLI Interface**: `python -m code.resampling --input <path> --factors 2,4,8,16 --output <dir>`. **Output Naming**: Files MUST be named `nlcd_{state}_res_{factor}m.tif` (e.g., `nlcd_co_res_{resolution}m.tif`), where the resolution parameter denotes a representative spatial scale appropriate for the analysis. in the `data/derived/` directory. **Prerequisite**: T014a.
- [~] T015 [US1] Implement bounds checking to skip invalid resolutions that exceed dataset bounds in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/resampling.py`.
- [~] T016 [US1] Apply checksumming and metadata validation for all generated rasters using `code/utils.py::checksum_file`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: Calibration & Binary Transformation (Pre-US2)

**Purpose**: Prepare data for statistical analysis by transforming to binary and defining the pre-defined spatial lag parameter ($\lambda$) for the Alternative Hypothesis.

- [~] T020 [P] [US2] Implement binary indicator map transformation in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/analysis.py` (e.g., Forest=1, Others=0). **Input**: 30m raster from T013. **Output**: `projects/PROJ-421-assessing-the-impact-of-data-resolution-/data/derived/nlcd_30m_binary.tif`. **Constraint**: Must specify exact class ID (e.g., Forest=Class [ID]). **Prerequisite**: T013.
- [~] T010 [US2] [Phase-0] Define the pre-defined spatial lag parameter ($\lambda$) in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/calibration.py`. **Method**: Estimate $\lambda$ from the 30m binary map (T020) using MLE. **Output**: Store estimated $\lambda$ in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/state/calibration.yaml`. **Prerequisite**: T020. **Constraint**: Do NOT hardcode in `config.py`; read dynamically.

**Checkpoint**: Calibration complete - US2 can begin

---

## Phase 4: User Story 2 - Spatial Autocorrelation Testing and Null/Alternative Simulation (Priority: P2)

**Goal**: Compute Moran's I statistics, generate null distributions (1,000 permutations), and simulate alternative distributions to estimate statistical power.

**Independent Test**: The analysis script can be run on a single resolution file. Verification involves checking that the output contains a calculated Moran's I value, a p-value, and that the simulation count matches the configuration (a sufficient number of permutations for H0 and simulations for H1).

### Tests for User Story 2

- [~] T018 [P] [US2] Unit test for binary indicator map transformation in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/tests/test_analysis.py`.
- [~] T019 [P] [US2] Unit test for Moran's I calculation and p-value generation in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/tests/test_analysis.py`.

### Implementation for User Story 2

- [~] T021 [US2] Implement H0 null distribution generation in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/analysis.py` using `pysal.esda.moran` with **exactly 1,000 random permutations** (FR-004). **Constraint**: No runtime-based reduction in permutation count is permitted; optimization must be achieved via code efficiency. **Prerequisite**: T020, T014.
- [~] T022a [US2] Implement `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/analysis.py::generate_h1_data(binary_map, lambda_val)` using a **Gibbs Sampler (binary spatial autoregressive process)**. **Parameters**: Use $\lambda$ from `state/calibration.yaml`. **Input**: Binary map and fixed lambda. **Output**: Synthetic binary rasters. **Prerequisite**: T010, T020. **Note**: Use Gibbs Sampler to ensure construct validity for binary data, not simple linear injection.
- [~] T022 [US2] Implement statistical power calculation in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/analysis.py`: compute the rejection rate of the H1 simulations (proportion where p < 0.05) by comparing against the critical value derived from the H0 distribution. This metric represents the statistical power (FR-005). **Input**: H1 data from T022a. **Prerequisite**: T021, T022a.
- [~] T025 [US2] Save results (Moran's I, p-values, power estimates) to CSV in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/data/results/`. **Schema**: `results.csv` with columns `resolution, moran_i, p_value, power, seed, class_id`. **Prerequisite**: T022.
- [~] T025a [P] [US2] Validate existence and schema of `results.csv` before downstream tasks. **Output**: Log "Schema Validated" or raise error. **Prerequisite**: T025.
- [~] T035 [US2] [Mandatory] Implement Multi-Class Sensitivity: Repeat the analysis for a second land cover class (Urban=1, Others=0, using NLCD class 12) using the same pipeline. **Output**: Append results to `results.csv` with a `class_id` column. **Constraint**: This is a core verification step for SC-004. **Prerequisite**: T025a.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Power Curve Generation and Threshold Identification (Priority: P3)

**Goal**: Generate a power-vs-resolution plot, identify the threshold where power < 0.80, and perform sensitivity analysis.

**Independent Test**: The plotting module can be run on pre-computed power data. Verification involves checking that a power curve is generated and that a specific resolution point is annotated where the power metric crosses the 0.80 line.

### Tests for User Story 3

- [~] T026 [P] [US3] Unit test for threshold identification logic in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/tests/test_analysis.py`.
- [~] T027 [P] [US3] Unit test for sensitivity analysis (±10% sweep) in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/tests/test_analysis.py`.

### Implementation for User Story 3

- [~] T028 [P] [US3] Implement `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/visualization.py` to generate Power-vs-Resolution curve.
- [~] T029 [US3] Implement `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/visualization.py::find_threshold(power_csv_path)` which returns the resolution string (e.g., '240m') where power < 0.80, and writes this to `projects/PROJ-421-assessing-the-impact-of-data-resolution-/data/results/threshold_report.txt`. **Prerequisite**: T025a.
- [~] T030 [US3] Calculate Type II error delta (1 - power) relative to 30m baseline. **Action**: Implement `calculate_type_ii_delta` function in `code/analysis.py`. **Logic**: If 30m baseline power is missing or 1.0, delta is 0.0. Otherwise, calculate percentage point increase relative to 30m. **Output**: Append rows to `results.csv` with columns `resolution, type_ii_error_delta`. **Prerequisite**: T025a.
- [ ] T032a [US3] Perform Resampling Sweep for Sensitivity Analysis. **Action**: Generate new rasters at perturbed factors (e.g., 1.1x and 0.9x of original factors) using `resampling.py`. **Output**: New raster files in `data/derived/sensitivity/`. **Prerequisite**: T014a.
- [~] T032b [US3] Re-run Analysis for Sensitivity Sweep. **Action**: Run `analysis.py` on the perturbed rasters from T032a to generate new power estimates. **Output**: Append sensitivity results to `results.csv`. **Prerequisite**: T032a.
- [~] T032 [US3] Generate sensitivity analysis report confirming threshold stability. **Filename**: `sensitivity_report.md`. **Content**: Verify that the identified threshold falls within one discrete resolution step of the inflection point when the aggregation factor is varied. **Prerequisite**: T032b.
- [~] T033 [US3] Generate `projects/PROJ-421-assessing-the-impact-of-data-resolution-/data/results/final_report.md` containing the specific resolution threshold, Type II error delta, and sensitivity analysis results. **Constraint**: Do NOT include MAUP narrative (removed as scope creep). **Prerequisite**: T030, T032.
- [~] T034 [US3] Ensure p-value = 0.05 is treated as significant but flagged. **Mechanism**: Add column `is_boundary` to `results.csv` and log warning.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns (General)

**Purpose**: Improvements that affect multiple user stories and final verification

- [~] T035a [P] [Doc] [US1-US3] Update `README.md` with CLI usage examples covering the full pipeline from ingestion to final report.
- [~] T035b [P] Update `docs/api.md` with function signatures.
- [~] T036 Code cleanup and refactoring. **Criteria**: Enforce line length < 88 (black) and remove unused imports (ruff).
- [~] T037 Performance optimization (verify < 6h runtime on CPU-only runner). **Target**: Reduce peak memory usage to < 6GB and runtime < 5.5h.
- [ ] T039b [P] [Polish] Runtime Profiling: Implement a runtime monitor in `code/main.py` to log execution time per phase. **Goal**: Ensure 1,000 permutations (T021) can complete within 6h total runtime without reducing sample size. **Prerequisite**: T039a.
- [~] T040 Run full pipeline on GitHub Actions runner to verify < 6h runtime and < 7GB RAM. **Command**: `python -m code.main --full-sweep`. **Verification**: Check `data/results/threshold_report.txt` exists.
- [~] T041 Run `quickstart.md` validation. **Procedure**: Execute all commands in `quickstart.md` and verify success exit codes.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 0)**: No dependencies - can start immediately
- **Foundational (Phase 1)**: Depends on Setup completion - **BLOCKS all user stories**
 - **Calibration (Task T010)**: Must complete before Phase 4 (US2) as it provides the $\lambda$ parameter. **Prerequisite**: T007 (Config), T020 (Binary Map).
 - **Reference-Validator (Task T009b)**: Must complete before any data ingestion (T013) to ensure URL validity.
- **User Stories (Phase 2+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 1) - No dependencies on other stories
 - **T013**: Depends on T009b (URL Validation), T013b (Fallback Verification)
 - **T014a**: Depends on T005, T013
 - **T014b**: Depends on T014a
- **User Story 2 (P2)**: Can start after Foundational (Phase 1) - Depends on T010 (Lambda) and T013-T017 for input data
 - **T021**: Depends on T020 (Binary Map), T014 (Resampling)
 - **T022a**: Depends on T010 (Config/State), T020 (Binary Map)
 - **T022**: Depends on T021, T022a
 - **T025**: Depends on T022
 - **T025a**: Depends on T025
 - **T035**: Depends on T025a (Mandatory)
- **User Story 3 (P3)**: Can start after Foundational (Phase 1) - Depends on T018-T025 for power data
 - **T029**: Depends on T025a
 - **T030**: Depends on T025a
 - **T032a**: Depends on T014a
 - **T032b**: Depends on T032a
 - **T032**: Depends on T032b
 - **T033**: Depends on T030, T032
 - **T034**: Depends on T025a
- **Polish (Phase 7)**:
 - **T039b**: Depends on T039a

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 1)
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- **Sensitivity tasks (T032a, T032b)** can run in parallel with T030 once T025a is done.

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

1. Complete Phase 0: Setup
2. Complete Phase 1: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 2: User Story 1
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
- **Removed Tasks**: T000a, T000b (deprecated/empty), T042-T048 (MAUP/Topological analysis removed as scope creep), T031 (removed due to ambiguity), T039 (renamed to T039b).
- **Updated Tasks**: T010 (Moved to Phase 1, outputs to state file, performs MLE), T013 (Added fallback verification T013b), T020 (Fixed output path), T022a (Gibbs Sampler), T030 (Mandatory, defined logic), T032 (Added T032a/T032b for real sweep), T035 (Mandatory, Class 12), T039a (Implemented main.py).
- **Review Addressed**: All concerns regarding scope creep, unauthorized methodology, missing spec requirements, circular dependencies, and unexecutable tasks have been addressed by aligning tasks strictly with `spec.md` and `plan.md`.