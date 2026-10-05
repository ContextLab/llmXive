# Tasks: Assessing the Impact of Data Resolution on Statistical Power in Publicly Available Spatial Datasets

**Input**: Design documents from `/specs/001-assess-resolution-power/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

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

- [X] T001 Create project directory structure: `mkdir -p projects/PROJ-421-assessing-the-impact-of-data-resolution-/code projects/PROJ-421-assessing-the-impact-of-data-resolution-/data/raw projects/PROJ-421-assessing-the-impact-of-data-resolution-/data/derived projects/PROJ-421-assessing-the-impact-of-data-resolution-/data/results projects/PROJ-421-assessing-the-impact-of-data-resolution-/tests`
- [X] T002 Create `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/requirements.txt` pinning `rasterio`, `geopandas`, `pysal`, `numpy`, `scipy`, `matplotlib`, `pandas`, `libpysal`.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/`.

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 Create base data models: Implement classes `ResolutionRaster` (fields: resolution, path, values) and `BinaryIndicatorMap` (fields: class_id, binary_values) in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/models.py`.
- [X] T005 [P] Implement `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/utils.py` with memory-mapped I/O helpers and windowed raster readers.
- [X] T006 [P] Setup logging infrastructure in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/utils.py`.
- [X] T007 Setup `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/config.py` for resolutions (30, 60, 120, 240, 480), seeds (seed=42), and paths.
- [X] T008 [P] Implement error handling and retry logic with exponential backoff in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/utils.py`.
- [X] T009 [P] [US1] Implement checksumming and metadata validation utilities in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/utils.py::checksum_file`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: User Story 1 - Data Ingestion and Resolution Aggregation (Priority: P1) 🎯 MVP

**Goal**: Download high-resolution NLCD data and generate coarser resolution rasters using nearest-neighbor resampling.

**Independent Test**: The script can be run in isolation to produce a directory of raster files at specified resolutions. Verification involves checking file existence, resolution metadata (pixel size), and verifying that categorical land cover values remain distinct integers without interpolation artifacts.

### Tests for User Story 1 (Write First)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T011 [P] [US1] Unit test for nearest-neighbor resampling logic in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/tests/test_resampling.py::test_nearest_neighbor_preserves_integers` (asserts that unique values in output == unique values in input).
- [X] T012 [P] [US1] Integration test for download and aggregation pipeline in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/tests/test_integration.py`.

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/data_ingestion.py` to download NLCD 30m subset for Colorado. **Primary Source**: USGS EarthExplorer API (FR-001). **Fallback**: If API fails or key is missing, fetch from verified HuggingFace mirror `https://huggingface.co/datasets/nlcd-30m/resolve/main/nlcd_2019_colorado_30m.tif` with checksum validation. Validate checksum using `utils.py::checksum_file`. Implement retry logic using `utils.py` utilities. **Prerequisite**: T039 (URL validation) must pass.
- [ ] T014 [US1] Implement `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/resampling.py::generate_resolution(input_path, factor)` function to generate a single coarser resolution raster using nearest-neighbor resampling, and implement the CLI loop to call it for factors [2, 4, 8, 16] (60m, 120m, 240m, 480m). **CLI Interface**: `python -m code.resampling --input <path> --factors 2,4,8,16 --output <dir>`. **Output Naming**: Files MUST be named `nlcd_{state}_res_{factor}m.tif` (e.g., `nlcd_co_res_60m.tif`) in the `data/derived/` directory. **Constraint**: MUST use chunked processing (windowed reads) with 2000x2000 pixel windows to stay within 7GB RAM. **Prerequisite**: T004 (Data Models), T005 (IO Utils), T013 (Data Ingestion).
- [ ] T015 [US1] Implement bounds checking to skip invalid resolutions that exceed dataset bounds in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/resampling.py`.
- [X] T016 [US1] Apply checksumming and metadata validation for all generated rasters using `code/utils.py::checksum_file`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: Calibration & Binary Transformation (Pre-US2)

**Purpose**: Prepare data for statistical analysis by transforming to binary and estimating the spatial lag parameter ($\lambda$) for the Alternative Hypothesis.

- [X] T020 [P] [US2] Implement binary indicator map transformation in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/analysis.py` (e.g., Forest=1, Others=0). **Input**: 30m raster from T013. **Output**: `data/derived/nlcd_30m_binary.tif`.
- [ ] T010 [US2] [FR-005] Implement `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/calibration.py::estimate_lambda` to perform Maximum Likelihood Estimation (MLE) on a **fixed sample of [deferred] of pixels (or minimum 10,000 pixels)** randomly selected from the 30m binary map. **Input**: `data/derived/nlcd_30m_binary.tif`. **Output**: Save estimated $\lambda$ value to `data/results/calibration_lambda.json`. **Prerequisite**: T013 (Data Ingestion), T020 (Binary Map). **Constraint**: Do NOT use a pre-defined fixed value; the value MUST be estimated from data.

**Checkpoint**: Calibration complete - US2 can begin

---

## Phase 4: User Story 2 - Spatial Autocorrelation Testing and Null/Alternative Simulation (Priority: P2)

**Goal**: Compute Moran's I statistics, generate null distributions (1,000 permutations), and simulate alternative distributions to estimate statistical power.

**Independent Test**: The analysis script can be run on a single resolution file. Verification involves checking that the output contains a calculated Moran's I value, a p-value, and that the simulation count matches the configuration (a sufficient number of permutations for H0 and simulations for H1).

### Tests for User Story 2

- [X] T018 [P] [US2] Unit test for binary indicator map transformation in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/tests/test_analysis.py`.
- [X] T019 [P] [US2] Unit test for Moran's I calculation and p-value generation in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/tests/test_analysis.py`.

### Implementation for User Story 2

- [X] T021 [US2] Implement H0 null distribution generation in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/analysis.py` using `pysal.esda.moran` with **exactly 1,000 random permutations** (FR-004). **Constraint**: No runtime-based reduction in permutation count is permitted; optimization must be achieved via code efficiency. **Prerequisite**: T020 (Binary Map), T014 (Resampling).
- [ ] T022a [US2] Implement `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/analysis.py::gibbs_sampler(binary_map, lambda_val, seed)` using a **Gibbs Sampler** for a binary spatial autoregressive process. **Mathematical Formulation**: Use the conditional probability $P(y_i=1 | y_{-i}) = \Phi(\lambda \sum_j w_{ij} y_j + \beta_0)$ where $\Phi$ is the standard normal CDF (Probit link). **Parameters**: **Burn-in**: [deferred] iterations; **Thinning**: a fixed interval of iterations. **Input**: MLE-estimated $\lambda$ from `data/results/calibration_lambda.json`. **Output**: Synthetic binary rasters. **Prerequisite**: T010 (Calibration).
- [X] T022 [US2] Implement statistical power calculation in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/analysis.py`: compute the rejection rate of the H1 simulations (proportion where p < 0.05) by comparing against the critical value derived from the H0 distribution. This metric represents the statistical power (FR-005). **Input**: H1 data from T022a. **Prerequisite**: T021, T022a.
- [X] T023 [US2] Implement `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/analysis.py::validate_h1_structure` to compare synthetic H1 data's spatial autocorrelation against observed 30m data. The metric is the **absolute difference in Moran's I**; ensure it is within 5% error.
- [X] T025 [US2] Save results (Moran's I, p-values, power estimates) to CSV in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/data/results/`. **Schema**: `results.csv` with columns `resolution, moran_i, p_value, power, seed, class_id`. **Prerequisite**: T022, T023.
- [X] T025a [P] [US2] Validate existence and schema of `results.csv` before downstream tasks. **Output**: Log "Schema Validated" or raise error. **Prerequisite**: T025.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Power Curve Generation and Threshold Identification (Priority: P3)

**Goal**: Generate a power-vs-resolution plot, identify the threshold where power < 0.80, and perform sensitivity analysis.

**Independent Test**: The plotting module can be run on pre-computed power data. Verification involves checking that a power curve is generated and that a specific resolution point is annotated where the power metric crosses the 0.80 line.

### Tests for User Story 3

- [X] T026 [P] [US3] Unit test for threshold identification logic in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/tests/test_analysis.py`.
- [X] T027 [P] [US3] Unit test for sensitivity analysis (±10% sweep) in `projects/PROJ-421-assessing-the-impact-of-data-resolution-/tests/test_analysis.py`.

### Implementation for User Story 3

- [X] T028 [P] [US3] Implement `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/visualization.py` to generate Power-vs-Resolution curve.
- [X] T029 [US3] Implement `projects/PROJ-421-assessing-the-impact-of-data-resolution-/code/visualization.py::find_threshold(power_csv_path)` which returns the resolution string (e.g., '240m') where power < 0.80, and writes this to `projects/PROJ-421-assessing-the-impact-of-data-resolution-/data/results/threshold_report.txt`. **Prerequisite**: T025a.
- [ ] T030 [US3] Calculate Type II error delta (1 - power) relative to 30m baseline. **Output**: Append a series of rows to `results.csv` with columns `resolution, type_ii_error_delta` (percentage point increase relative to 30m baseline). **Prerequisite**: T025a.
- [X] T032 [US3] Generate sensitivity analysis report confirming threshold stability. **Filename**: `sensitivity_report.md`. **Content**: Verify that the identified threshold falls within one discrete resolution step of the inflection point when the aggregation factor is varied. **Prerequisite**: T025a.
- [X] T033 [US3] Generate `projects/PROJ-421-assessing-the-impact-of-data-resolution-/data/results/final_report.md` containing the specific resolution threshold, Type II error delta, and sensitivity analysis results.
- [X] T034 [US3] Ensure p-value = 0.05 is treated as significant but flagged. **Mechanism**: Add column `is_boundary` to `results.csv` and log warning.
- [ ] T035 [US2] [US3] [FR-005] Implement Multi-Class Sensitivity: Repeat the analysis for a second land cover class (Urban=1, Others=0) using the same pipeline. **Output**: Append results to `results.csv` with a `class_id` column. **Note**: This is a mandatory robustness check for 'Scientific Soundness' (Plan Phase 2). **Prerequisite**: T025a.
- [X] T036 [US2] [FR-005] Apply Benjamini-Hochberg correction for multiple testing if multiple classes are analyzed. **Implementation**: Update `results.csv` to include corrected p-values or adjust the power calculation logic accordingly. **Prerequisite**: T035.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5.5: MAUP & Topological Narrative Analysis (Review Revision)

**Goal**: Address the "Modifiable Areal Unit Problem" (MAUP) not just as a statistical nuisance, but as a fundamental narrative limit. Explicitly analyze phase transitions and the "story" of aggregation.

- [ ] T042 [P] [US3] [Rev] Implement `code/analysis.py::compute_topological_features` to calculate non-linear metrics beyond Moran's I (e.g., Euler characteristic, cluster count, perimeter-area fractal dimension) for each resolution level. **Rationale**: To detect "phase transitions" where the nature of the pattern changes, as suggested by the reviewer. **Input**: `data/derived/` rasters. **Output**: `data/results/topological_metrics.csv`. **Prerequisite**: T014.
- [ ] T043 [US3] [Rev] Implement `code/visualization.py::plot_maup_narrative` to generate a composite visualization overlaying the Power Curve (from T028) with the Topological Metrics (from T042). **Goal**: Visually identify if the drop in statistical power correlates with a topological phase transition (e.g., sudden drop in cluster count) rather than a smooth linear decay. **Output**: `data/results/maup_narrative_plot.png`. **Prerequisite**: T028, T042.
- [ ] T044 [US3] [Rev] Generate `data/results/maup_narrative_report.md`. **Content**: Explicitly discuss the "story" of the aggregation. Does the landscape "lose its voice" at a specific scale? Does the narrative shift from "patchy" to "homogeneous" abruptly? **Constraint**: Must reference the specific resolution where the topological shift occurs and compare it to the power threshold identified in T029. **Prerequisite**: T043.

**Checkpoint**: MAUP narrative and topological limits explicitly addressed.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final verification

- [ ] T035a [P] [Doc] [US1-US3] Update `README.md` with CLI usage examples covering the full pipeline from ingestion to final report.
- [X] T035b [P] Update `docs/api.md` with function signatures.
- [X] T036 Code cleanup and refactoring. **Criteria**: Enforce line length < 88 (black) and remove unused imports (ruff).
- [X] T037 Performance optimization (verify < 6h runtime on CPU-only runner). **Target**: Reduce peak memory usage to < 6GB and runtime < 5.5h.
- [ ] T039 [P] [Polish] Runtime Profiling: Implement a runtime monitor in `code/main.py` to log execution time per phase. **Goal**: Ensure 1,000 permutations (T021) can complete within 6h total runtime without reducing sample size. **Prerequisite**: T021.
- [X] T040 Run full pipeline on GitHub Actions runner to verify < 6h runtime and < 7GB RAM. **Command**: `python -m code.main --full-sweep`. **Verification**: Check `data/results/threshold_report.txt` exists.
- [X] T041 Run `quickstart.md` validation. **Procedure**: Execute all commands in `quickstart.md` and verify success exit codes.

**Note**: MAUP effects are now explicitly captured in the new Phase 5.5 analysis; the previous implicit assumption is replaced by active topological investigation.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 0)**: No dependencies - can start immediately
- **Foundational (Phase 1)**: Depends on Setup completion - **BLOCKS all user stories**
 - **Calibration (Task T010)**: Must complete before Phase 4 (US2) as it provides the $\lambda$ parameter. **Prerequisite**: T013 (Data Ingestion), T020 (Binary Map).
 - **Reference-Validator (Task T039)**: Must complete before any data ingestion (T013) to ensure URL validity.
- **User Stories (Phase 2+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **MAUP Narrative (Phase 5.5)**: Depends on T014 (Resampling) and T028 (Power Curve) to correlate topological shifts with power loss.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 1) - No dependencies on other stories
 - **T013**: Depends on T039 (URL Validation)
 - **T014**: Depends on T004 (Data Models), T005 (IO Utils), T013 (Data Ingestion)
- **User Story 2 (P2)**: Can start after Foundational (Phase 1) - Depends on T010 (Lambda) and T013-T017 for input data
 - **T021**: Depends on T020 (Binary Map), T014 (Resampling)
 - **T022a**: Depends on T010 (Calibration)
 - **T022**: Depends on T021, T022a
 - **T025**: Depends on T022
 - **T025a**: Depends on T025
- **User Story 3 (P3)**: Can start after Foundational (Phase 1) - Depends on T018-T025 for power data
 - **T029**: Depends on T025a
 - **T030**: Depends on T025a
 - **T032**: Depends on T025a
 - **T035**: Depends on T025a
 - **T036**: Depends on T035
- **MAUP Narrative (Phase 5.5)**:
 - **T042**: Depends on T014 (Resampling)
 - **T043**: Depends on T028 (Power Curve), T042
 - **T044**: Depends on T043

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
5. Add MAUP Narrative (Phase 5.5) → Synthesize topological insights with power data
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2 (requires T010 first)
 - Developer C: User Story 3
 - Developer D: MAUP Narrative (Phase 5.5) (can start once T014 is done)
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
- **Removed Tasks**: T017 (merged into T014), T031 (removed due to ambiguity), T044 (MAUP report removed as scope creep - now replaced by T044 in Phase 5.5), T045-T048 (Topological/Cultural analysis removed as scope creep - now integrated in Phase 5.5).
- **Updated Tasks**: T010 (Fixed sample size), T014 (Added output naming and chunking constraint), T021 (Strict 1000 permutations), T035 (Mandatory), T036 (Mandatory).
- **New Tasks**: T042, T043, T044 added to address Dan Rockmore's review regarding MAUP, topological phase transitions, and the "story" of aggregation.
