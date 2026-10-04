# Tasks: Quantifying the Effects of Dark Matter Halo Shapes on Galaxy Formation

**Input**: Design documents from `/specs/001-quantifying-the-effects-of-dark-matter-h/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, P3)
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

- [ ] T001 Create project structure per implementation plan (`code/`, `data/`, `outputs/`, `docs/`, `state/`). **Action**: Create all root directories and subdirectories defined in `plan.md` Project Structure. **Deliverable**: Empty directory tree.
- [ ] T002 [P] Create `docs/` directory structure. **Action**: Ensure `docs/` directory exists. **Deliverable**: `docs/` directory.
- [ ] T003a [P] Create `.ruff.toml` configuration file for linting. **Action**: Create `.ruff.toml` with rules for Python 3.11, including `E`, `F`, `W`, `I` rules. **Deliverable**: `.ruff.toml`.
- [X] T003b [P] Create `pyproject.toml` configuration file for formatting. **Action**: Create `pyproject.toml` with `[tool.black]` section and `line-length = 88`. **Deliverable**: `pyproject.toml`.
- [X] T004 [P] Setup configuration management (`code/utils/config.py`) with `random.seed()` and path constants
- [X] T005 [P] Implement chunked data I/O utilities (`code/utils/io.py`) to handle <7GB RAM constraints
- [ ] T006 [P] Create base logging infrastructure for pipeline tracking
- [X] T007 [P] Setup `data/metadata.yaml` schema for checksums and version tracking
- [X] T008 [P] Implement `code/main.py` entry point for pipeline orchestration

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T026 [P] **Mandatory Utility**: Implement shared metadata flag injection in `code/utils/io.py`. **Mechanism**: All CSV writers must add a comment header `# associational_only=true` and JSON writers must include `"associational_only": true`. **Deliverable**: Updated `code/utils/io.py` and `code/ingestion/` writers. **Verification**: Add a validation step to ensure all downstream scripts (T017, T018, T023, T025, T030, T038, T039) invoke this utility. **Note**: This task must be completed before T023, T025, T030, T038, and T039 generate their files.
- [X] T010 [P] [US1] Integration test for TNG-100 download and chunk processing in `code/tests/test_pipeline.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Data Ingestion and Halo Shape Computation (Priority: P1) 🎯 MVP

**Goal**: Download TNG-100 data, compute reduced inertia tensors, and derive axial ratios/triaxiality for valid haloes. Also ingest central galaxy properties.

**Independent Test**: Verify the pipeline retrieves the TNG-100 catalog, computes inertia tensors for a random subset of haloes, and outputs CSVs with valid axial ratios (0 < b/a ≤ 1, 0 < c/a ≤ 1) and triaxiality (0 ≤ T ≤ 1), excluding haloes with <10k particles.

### Implementation for User Story 1

- [X] T011 [P] [US1] Implement TNG-100 data fetcher in `code/ingestion/tng_loader.py`: Fetch static HDF files from `https://www.tng-project.org/api/v2/snapshots/000/halos` (specifically the list of HDF5 files for Snapshot 000) using `requests`, handling pagination and checksums. **Note**: Use the API to retrieve the list of files, then download specific HDF5 files.
- [X] T012 [P] [US1] **Define Interface First**: Create `code/processing/inertia_tensor.py` with stub functions and docstrings for eigenvalue decomposition. **Action**: Define the function signatures and input/output contracts before implementing the full logic. **Deliverable**: `code/processing/inertia_tensor.py` with stub functions.
- [X] T013 [US1] Implement shape metrics derivation (axial ratios, triaxiality) in `code/processing/shape_metrics.py`
- [X] T014 [US1] **BLOCKING**: Implement halo filtering logic (exclude N < 10,000 particles) in `code/processing/shape_metrics.py`. **Dependency**: T013. **Deliverable**: `code/processing/shape_metrics.py` with filtering logic.
- [X] T016 [US1] **PRIMARY**: Implement Chunked Streaming pipeline to process EVERY FoF halo in TNG without loading into RAM. **Action**: Use `datasets.load_dataset(..., streaming=True)` and iterate in chunks. **Dependency**: T014. **Deliverable**: `code/processing/pipeline_runner.py` with streaming logic. **Note**: This satisfies FR-001 "every FoF halo" within 7GB RAM limits. This task consolidates the logic previously split between T015 and T016b.
- [ ] T017 [US1] **BLOCKING**: Implement aggregation and validation in `code/processing/pipeline_runner.py`: Merge chunks, validate 0 < b/a ≤ 1 and 0 < c/a ≤ 1, log excluded haloes to `data/processed/exclusion_log.json`, and output `data/processed/halo_shapes.csv`. **Schema**: `halo_id` (int), `mass` (float), `b_a_ratio` (float), `c_a_ratio` (float), `triaxiality` (float), `particle_count` (int). **Deliverable**: `data/processed/halo_shapes.csv` and `data/processed/exclusion_log.json`.
- [ ] T018 [US1] **CRITICAL ADDITION**: Implement central galaxy property ingestion in `code/ingestion/tng_loader.py`. **Action**: Extract SFR, effective radius, and stellar mass for the most massive subhalo (central) within each halo. **Dependency**: T011. **Deliverable**: `data/processed/galaxy_properties.csv` with schema: `galaxy_id` (int), `halo_id` (int), `sfr` (float), `effective_radius` (float), `stellar_mass` (float). **Note**: This task must complete before T036/T038 in Phase 6.
- [X] T009 [US1] Unit test for inertia tensor singularity handling in `code/tests/test_inertia.py`. **Test**: `test_singular_matrix_raises_error` must raise `ValueError` when particles < 10,000 or matrix is singular. **Dependency**: T014 (Filtering logic implementation). **Note**: Moved from Phase 2 to Phase 3 to resolve circular dependency.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Correlation, Binning, and Mass Control (Priority: P2)

**Goal**: Bin haloes, perform mass-matching, execute statistical tests (KW, MWU, KS, Regression), and apply Bonferroni correction.

**Independent Test**: Verify output includes correlation coefficients, p-values, and regression coefficients with evidence of mass-matching/stratification and Bonferroni correction.

**⚠️ DEPENDENCY**: Phase 4 MUST WAIT for Phase 3 completion (specifically T017 and T018 output).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020a [P] [US2] Unit test for binning logic (prolate/triaxial/spherical) in `code/tests/test_stats.py`. **Dependency**: T020b.
- [X] T020b [US2] Unit test for Bonferroni correction application in `code/tests/test_stats.py`

### Implementation for User Story 2

- [X] T021 [US2] Implement mass-matching algorithm interface in `code/analysis/stats.py`: Define the function signatures and input/output contracts for Nearest-Neighbor Matching with a moderate mass tolerance. **Do not use Propensity Score Stratification**. **Deliverable**: `code/analysis/stats.py` with interface definitions.
- [ ] T021b [US2] **BLOCKING**: Implement Streaming Mass-Matching in `code/analysis/stats.py`. **Action**: Implement a memory-efficient matching algorithm (e.g., block-wise sorting or approximate nearest neighbor) that processes the joined dataset in chunks. **Input**: Streams from `data/processed/halo_shapes.csv` and `data/processed/galaxy_properties.csv`. **Output**: `data/processed/matched_chunks/` directory containing small CSV files (e.g., `match_001.csv`, `match_002.csv`) representing locally mass-matched blocks. **Dependency**: T017, T018, T021. **Deliverable**: `code/analysis/stats.py` with streaming-compatible matching logic. **Note**: This task resolves the memory constraint violation for FR-012 by avoiding a full in-memory join.
- [ ] T022 [US2] Implement non-parametric tests (Kruskal-Wallis, Mann-Whitney U, KS) in `code/analysis/stats.py`
- [ ] T023a [US2] **BLOCKING**: Implement linear regression with mass control in `code/analysis/stats.py`: Perform regression of galaxy property ~ continuous shape parameters (**specifically 'triaxiality' and 'b_a_ratio'**) AND **categorical shape bins** controlling for halo mass. **Model**: `SFR ~ triaxiality + b_a_ratio + mass` using `statsmodels`. **Input**: **Iterate over `data/processed/matched_chunks/`** (output of T021b) to ensure mass-matching is applied. **Dependency**: T017, T018, T021, T021b, T026. **Verification**: Ensure the regression input is explicitly the mass-matched dataset from T021b. **Deliverable**: `data/processed/regression_results.csv` (columns: predictor, coefficient, p_value, r_squared, ci_lower, ci_upper).
- [ ] T023b [US2] **PRIMARY**: Implement categorical shape binning tests (Kruskal-Wallis, Mann-Whitney U, KS) in `code/analysis/stats.py` based on FR-003/FR-004. **Action**: Implement tests for prolate (c/a < 0.5), triaxial (0.5 ≤ c/a ≤ 0.8), and spherical (c/a > 0.8) bins. **Input**: **Iterate over `data/processed/matched_chunks/`** (output of T021b). **Dependency**: T017, T018, T020b, T021b. **Deliverable**: `data/processed/binning_tests.csv`.
- [ ] T020b [US2] Implement shape binning logic (c/a < 0.5, 0.5-0.8, > 0.8) in `code/processing/shape_metrics.py`. **Dependency**: T017 output. **Note**: This is secondary to regression but required for visualization and KS tests.
- [ ] T024 [US2] Implement Bonferroni correction for multiple comparisons in `code/analysis/stats.py`
- [ ] T025 [US2] Create analysis script to generate `data/processed/statistical_results.csv`. **Dependency**: T021, T021b, T022, T023a, T023b, T024, T026.
- [ ] T027 [US2] Add logging for null hypothesis rejection flags (p < 0.01)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness Validation and Sensitivity Analysis (Priority: P3)

**Goal**: Repeat analysis on Millennium-II (if available) and perform sensitivity sweep on binning thresholds.

**Independent Test**: Verify sensitivity analysis report shows p-value stability across threshold sweeps and comparison with Millennium-II results.

**⚠️ DEPENDENCY**: Phase 5 MUST WAIT for Phase 4 completion (specifically T026 output).

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Unit test for sensitivity sweep logic in `code/tests/test_sensitivity.py`

### Implementation for User Story 3

- [ ] T029 [US3] Implement Millennium-II and WDM variant data fetcher in `code/ingestion/millennium_loader.py`. **Action**: Attempt to fetch Millennium-II and WDM variant snapshots from official public API endpoints. **If URLs are unverified or data is missing**: Trigger T031-LogGap to log the specific gap and trigger a Spec Amendment task to formally amend FR-007 to 'Conditional' before proceeding. **Do not skip by design**; the task is to attempt fetch and trigger the gap protocol. **Dependency**: T031-LogGap.
- [ ] T030 [US3] **BLOCKING**: Implement Sensitivity Logic Definition in `code/analysis/sensitivity.py`. **Action**: Define the sweep parameters across a representative range and the logic for computing stats for each. **Dependency**: T026. **Deliverable**: `code/analysis/sensitivity.py` with logic definitions. **Note**: This task defines the sweep, but does NOT execute the full pipeline.
- [ ] T030-RunSweep [US3] **PRIMARY**: Implement Sensitivity Orchestration. **Action**: Re-run the statistical pipeline (Tb, T023a, T023b) for EACH of the four threshold variations {0.45, 0.55, 0.75, 0.85}. **Input**: `data/processed/matched_chunks/` (from T021b). **Mechanism**: Pass `threshold_config` parameter to T023a/T023b to dynamically adjust binning. **Dependency**: T030, T021, T021b, T022, T023a, T023b, T024. **Deliverable**: `data/processed/sensitivity_results.csv` (columns: threshold_set, p_value, significance_status). **Note**: This task ensures FR-006 is implementable by explicitly commanding the re-execution of the analysis for each threshold.
- [ ] T031-Fetch [US3] Create script to fetch Millennium-II data (if available) and output `data/raw/millennium/halo_catalog.hdf5`. **Dependency**: T029. **Action**: If fetch fails (HTTP 404/500 or file not found), **immediately trigger T031-LogGap** and skip downstream tasks. **Deliverable**: `data/raw/millennium/halo_catalog.hdf5`.
- [ ] T031-Process [US3] Run ingestion and shape computation pipeline on Millennium-II data (if fetched) and output `data/processed/millennium_shapes.csv`. **Action**: Extract galaxy properties (SFR, radius) from subhalo catalogs and output `data/processed/millennium_galaxy_properties.csv`. **Dependency**: T031-Fetch.
- [ ] T031-MM-RunFull [US3] **BLOCKING**: Run full statistical analysis pipeline on Millennium-II data (if processed). **Action**: Execute mass-matching (T021b), binning tests (T023b), regression (T023a), and sensitivity sweep (T030-RunSweep) on the Millennium-II dataset. **Dependency**: T031-Process. **Deliverable**: `data/processed/millennium_results.csv`. **Note**: This task ensures FR-007 is implementable if data is available.
- [ ] T031-WDM-Fetch [US3] Attempt to fetch WDM variant snapshots (if available). **Dependency**: T029. **Action**: If missing or fetch fails, **immediately trigger T031-LogGap** and skip downstream tasks.
- [ ] T031-WDM-Process [US3] Run ingestion and shape computation pipeline on WDM data (if fetched) and output `data/processed/wdm_shapes.csv`. **Action**: Extract galaxy properties (SFR, radius) from subhalo catalogs and output `data/processed/wdm_galaxy_properties.csv`. **Dependency**: T031-WDM-Fetch.
- [ ] T031-WDM-Analyze-Full [US3] **BLOCKING**: Run full statistical analysis pipeline on WDM data (if processed). **Action**: Execute mass-matching (T021b), binning tests (T023b), regression (T023a), and sensitivity sweep (T030-RunSweep) on the WDM dataset. **Dependency**: T031-WDM-Process. **Deliverable**: `data/processed/wdm_results.csv`. **Note**: This task ensures FR-007 is implementable if data is available.
- [ ] T031-LogGap [US3] **Mandatory**: If T029/T031-Fetch/T031-WDM-Fetch fail, log the specific gap to `data/metadata.yaml`, update `outputs/reports/gap_log.md`, and mark SC-004 as 'Not Measurable' in the final report. **This task ensures FR-007 has a concrete implementation path even if data is missing.** **Input**: Error log from fetch. **Output**: `outputs/reports/gap_log.md` and updated `data/metadata.yaml`. **Dependency**: T029, T031-Fetch, T031-WDM-Fetch.
- [ ] T031-AmendSpec [US3] **Mandatory**: If T031-LogGap is triggered, formally amend `specs/001-quantifying-the-effects-of-dark-matter-h/spec.md` to change FR-007 from 'Mandatory' to 'Conditional' (if data unavailable). **Action**: Update the spec text and version. **Dependency**: T031-LogGap. **Deliverable**: Updated `spec.md`.
- [ ] T032 [US3] Generate sensitivity report comparing significance rates and p-value variance across thresholds. **Dependency**: T030, T030-RunSweep.
- [ ] T033 [US3] Implement cross-dataset comparison logic (TNG-100 vs Millennium-II vs WDM). **Deliverable**: `outputs/reports/cross_dataset_comparison.md` containing correlation diff, p-value diff, and conclusion on consistency. **Dependency**: T031-MM-RunFull and T031-WDM-Analyze-Full (or T031-LogGap if skipped).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Orientation Misalignment Analysis (Priority: P3)

**Goal**: Compute orientation misalignment angles (spin-spin, major-major) and correlate with galaxy properties.

**Independent Test**: Verify pipeline outputs CSV with misalignment angles (degrees) and correlation results with SFR/effective radius.

**⚠️ DEPENDENCY**: Phase 6 MUST WAIT for Phase 3 (Data: T017, T018) AND Phase 4 (Stats/Properties) completion.

### Tests for User Story 4 (OPTIONAL - only if tests requested) ⚠️

- [ ] T035 [P] [US4] Unit test for angle calculation (dot product/arccos) in `code/tests/test_alignment.py`

### Implementation for User Story 4

- [ ] T036 [US4] **BLOCKING**: Implement spin vector and major axis calculation in `code/processing/alignment.py`. **Dependency**: T017 (halo data), T018 (galaxy data). **Action**: Compute spin vectors for haloes (from T017) and galaxies (from T018).
- [ ] T037 [US4] Implement misalignment angle computation (halo-galaxy pairs) in `code/processing/alignment.py`. **Dependency**: T036, T018. **Action**: Join halo and galaxy data on `halo_id`, compute angles (halo spin vs galaxy spin, halo major axis vs galaxy major axis).
- [ ] T038 [US4] **Dependency: T026**: Create script to generate `data/processed/alignment_angles.csv`. **Schema**: `halo_id` (int), `galaxy_id` (int), `spin_angle_deg` (float), `axis_angle_deg` (float). **Dependency**: T037, T026. **Verification**: Ensure file contains valid angles (non-negative to a maximum threshold) and row count > 0. **Note**: Ensure file contains `associational_only=true` flag via T026.
- [ ] T039 [US4] **BLOCKING**: Implement correlation analysis AND mass-controlled regression for misalignment angles vs galaxy properties (SFR, **effective radius**). **Dependency**: T038. **Action**: Perform correlation analysis AND linear regression of galaxy property ~ misalignment angles **controlling for halo mass**. **Deliverable**: `data/processed/alignment_correlations.csv` (columns: metric, correlation_coeff, p_value, method, regression_coeff, regression_p_value). **Note**: This task explicitly includes the regression component required by FR-011 for US-4.
- [ ] T040 [US4] Integrate misalignment results into final statistical report. **Target**: `outputs/reports/final_report.md`. **Format**: Markdown section with embedded tables of correlation results.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041 [P] Documentation updates in `docs/` and `README.md`
- [ ] T042 Code cleanup and refactoring
- [ ] T043 Performance optimization (ensure <6h runtime on 2 CPU/7GB RAM)
- [ ] T044 [P] Additional unit tests for edge cases (singular matrices, outliers)
- [ ] T045 Run quickstart.md validation
- [ ] T046 [US4] Generate final research report: Use template in `paper/report_template.md`. Automate data pull from `data/`. Ensure all citations are present in `data/metadata.yaml`.
- [ ] T047-VerifyMetadata [P] **BLOCKING**: Implement Metadata Flag Verification in `code/utils/verification.py`. **Action**: Scan ALL generated artifacts (including `sensitivity_report.csv`, `cross_dataset_comparison.md`, `final_report.md`, and all CSVs in `data/processed/`) to ensure the `associational_only=true` flag is present or referenced. **Dependency**: T046, T032, T033. **Deliverable**: `outputs/reports/metadata_compliance_report.md`. **Note**: This task ensures FR-008 compliance is verified for all outputs.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **Phase 3 (US1)**: No dependencies on other stories.
 - **Phase 4 (US2)**: **MUST WAIT** for Phase 3 (T017, T018) - Depends on `data/processed/halo_shapes.csv` and `data/processed/galaxy_properties.csv`.
 - **Phase 5 (US3)**: **MUST WAIT** for Phase 4 (T026) - Depends on `data/processed/statistical_results.csv`.
 - **Phase 6 (US4)**: **MUST WAIT** for Phase 3 (Data: T017, T018) AND Phase 4 (Stats/Properties) - Depends on halo shapes, galaxy properties, and alignment logic.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (halo shapes, galaxy properties)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (statistical results)
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 output (halo/galaxy data) AND US2 output (statistical framework/properties)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utils before services
- Services before endpoints/scripts
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 can start. US3, US4, and US2 must wait for upstream data/artifacts as defined in Phase Dependencies.
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members ONLY IF their data dependencies are met.

---

## Parallel Example: User Story 1

```bash
# Launch all models for User Story 1 together:
Task: "Implement TNG-100 data fetcher in code/ingestion/tng_loader.py"
Task: "Define Interface for reduced inertia tensor calculation in code/processing/inertia_tensor.py"
# Note: T009 (Test) must wait for T014 interface definition.
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (including T018 for galaxy properties)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 & 4 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Halo & Galaxy Ingestion)
 - Developer B: User Story 3 (Millennium-II/Sensitivity) - *Wait for US2 data*
 - Developer C: User Story 4 (Alignment) - *Wait for US1/US2 data*
3. Developer A completes US1, then Developer B/C integrate US2
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All tasks must run on CPU-only CI (a limited number of cores, constrained RAM). No GPU, no 8-bit quantization, no large model loading. Use chunking and sampling.
- **Data Gap Protocol**: If a required dataset (e.g., Millennium-II, WDM variants) does not have a verified, public URL in `data/metadata.yaml`, the pipeline MUST attempt to fetch, trigger T031-LogGap, log the specific gap to `data/metadata.yaml` and the final report, mark the associated Success Criterion (SC-004) as 'Not Measurable', and **trigger a Spec Amendment task (T031-AmendSpec)** to formally amend FR-007 to 'Conditional' before proceeding. This prevents unverified data from entering the results while ensuring the gap is documented and the spec is updated.
- **WDM Variants**: WDM variant snapshots are NOT included unless a verified URL is found in `data/metadata.yaml`. If missing, the project proceeds with TNG-100 and Millennium-II (if available) only, with SC-004 marked 'Not Measurable' and FR-007 amended to 'Conditional'.
- **Sampling Constraint**: Due to hardware limits, the pipeline uses **Chunked Streaming** to process the full dataset without loading it into RAM. This satisfies FR-001 "every FoF halo" without requiring a spec amendment. The project acknowledges this implementation strategy in the final report via `docs/sampling_protocol.md`.
- **Streaming Mass-Matching**: T021b implements a streaming-compatible mass-matching algorithm that outputs **block-wise matched chunks** (`data/processed/matched_chunks/`) to ensure FR-012 is met without violating memory constraints. Downstream tasks (T023a, T023b) must iterate over these chunks.
- **Sensitivity Orchestration**: T030-RunSweep explicitly commands the re-execution of the statistical pipeline for each threshold variation to ensure FR-006 is met.
- **Metadata Flag Verification**: T047-VerifyMetadata ensures FR-008 compliance is verified for all output artifacts.