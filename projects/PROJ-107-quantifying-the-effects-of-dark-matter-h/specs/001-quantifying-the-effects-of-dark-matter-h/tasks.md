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
- [X] T002 [P] Initialize Python 3.11 project with `requirements.txt` (numpy, pandas, scipy, scikit-learn, h5py, requests, pyyaml, pytest). **Dependency**: T001. **Action**: Create `docs/` directory if missing, then create `docs/sampling_protocol.md` defining the sampling strategy (ratio, seed, chunking algorithm) as a formal artifact to satisfy FR-001 deviation documentation. **Deliverable**: `docs/sampling_protocol.md`.
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Setup configuration management (`code/utils/config.py`) with `random.seed()` and path constants
- [X] T005 [P] Implement chunked data I/O utilities (`code/utils/io.py`) to handle <7GB RAM constraints
- [ ] T006 [P] Create base logging infrastructure for pipeline tracking
- [X] T007 [P] Setup `data/metadata.yaml` schema for checksums and version tracking
- [X] T008 [P] Implement `code/main.py` entry point for pipeline orchestration

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Data Ingestion and Halo Shape Computation (Priority: P1) 🎯 MVP

**Goal**: Download TNG-100 data, compute reduced inertia tensors, and derive axial ratios/triaxiality for valid haloes. Also ingest central galaxy properties.

**Independent Test**: Verify the pipeline retrieves the TNG-100 catalog, computes inertia tensors for a random subset of haloes, and outputs CSVs with valid axial ratios (0 < b/a ≤ 1, 0 < c/a ≤ 1) and triaxiality (0 ≤ T ≤ 1), excluding haloes with <10k particles.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [US1] Unit test for inertia tensor singularity handling in `code/tests/test_inertia.py`. **Test**: `test_singular_matrix_raises_error` must raise `ValueError` when particles < 10,000 or matrix is singular. **Dependency**: T012 (interface definition).
- [X] T010 [P] [US1] Integration test for TNG-100 download and chunk processing in `code/tests/test_pipeline.py`

### Implementation for User Story 1

- [X] T011 [P] [US1] Implement TNG-100 data fetcher in `code/ingestion/tng_loader.py`: Fetch static HDF files from `https://www.tng-project.org/api/v2/snapshots/000/halos` (specifically the list of HDF5 files for Snapshot 000) using `requests`, handling pagination and checksums. **Note**: Use the API to retrieve the list of files, then download specific HDF5 files.
- [X] T012 [P] [US1] **Define Interface First**: Implement reduced inertia tensor calculation interface in `code/processing/inertia_tensor.py` (eigenvalue decomposition). **Action**: Define the function signatures and input/output contracts before implementing the full logic to satisfy T009.
- [X] T013 [US1] Implement shape metrics derivation (axial ratios, triaxiality) in `code/processing/shape_metrics.py`
- [X] T014 [US1] Implement halo filtering logic (exclude N < 10,000 particles) in `code/processing/shape_metrics.py`
- [X] T015 [US1] Implement chunked loop logic in `code/processing/pipeline_runner.py`: Read input chunks (configurable size), iterate over haloes, and yield processed records. Includes T016 logic.
- [X] T016 [US1] **Mandatory**: Formalize sampling strategy. Update `data/metadata.yaml` with exact sampling ratio, random seed, and chunking algorithm. Create `docs/sampling_protocol.md` detailing the deviation from FR-001 "every FoF halo" to ensure reproducibility. **Mechanism**: Use stratified random sampling based on halo mass bins to ensure representativeness. **Deliverable**: `docs/sampling_protocol.md` and `data/metadata.yaml` update.
- [ ] T017 [US1] **BLOCKING**: Implement aggregation and validation in `code/processing/pipeline_runner.py`: Merge chunks, validate 0 < b/a ≤ 1 and 0 < c/a ≤ 1, log excluded haloes to `data/processed/exclusion_log.json`, and output `data/processed/halo_shapes.csv`. **Schema**: `halo_id` (int), `mass` (float), `b_a_ratio` (float), `c_a_ratio` (float), `triaxiality` (float), `particle_count` (int). **Deliverable**: `data/processed/halo_shapes.csv` and `data/processed/exclusion_log.json`.
- [ ] T018 [US1] **CRITICAL ADDITION**: Implement central galaxy property ingestion in `code/ingestion/tng_loader.py`. **Action**: Extract SFR, effective radius, and stellar mass for the most massive subhalo (central) within each halo. **Dependency**: T011. **Deliverable**: `data/processed/galaxy_properties.csv` with schema: `galaxy_id` (int), `halo_id` (int), `sfr` (float), `effective_radius` (float), `stellar_mass` (float). **Note**: This task must complete before T036/T038 in Phase 6.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Correlation, Binning, and Mass Control (Priority: P2)

**Goal**: Bin haloes, perform mass-matching, execute statistical tests (KW, MWU, KS, Regression), and apply Bonferroni correction.

**Independent Test**: Verify output includes correlation coefficients, p-values, and regression coefficients with evidence of mass-matching/stratification and Bonferroni correction.

**⚠️ DEPENDENCY**: Phase 4 MUST WAIT for Phase 3 completion (specifically T017 and T018 output).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for binning logic (prolate/triaxial/spherical) in `code/tests/test_stats.py`
- [X] T020 [P] [US2] Unit test for Bonferroni correction application in `code/tests/test_stats.py`

### Implementation for User Story 2

- [X] T021 [US2] Implement mass-matching algorithm in `code/analysis/stats.py`: Use Nearest-Neighbor Matching with a moderate mass tolerance to control for confounding. **Do not use Propensity Score Stratification**.
- [X] T022 [US2] Implement non-parametric tests (Kruskal-Wallis, Mann-Whitney U, KS) in `code/analysis/stats.py`
- [ ] T023 [US2] **BLOCKING**: Implement linear regression with mass control in `code/analysis/stats.py`: Perform regression of galaxy property ~ continuous shape parameters (**specifically 'triaxiality' and 'b_a_ratio'**) AND **categorical shape bins** controlling for halo mass. **Model**: `SFR ~ triaxiality + b_a_ratio + mass` using `statsmodels`. **Dependency**: T017, T018, T026. **Note**: Regression can run independently of T020 (binning) as it uses continuous parameters; T020 is a parallel task for visualization. **Deliverable**: `data/processed/regression_results.csv` (columns: predictor, coefficient, p_value, r_squared, ci_lower, ci_upper).
- [X] T020 [US2] Implement shape binning logic (c/a < 0.5, 0.5-0.8, > 0.8) in `code/processing/shape_metrics.py`. **Dependency**: T017 output. **Note**: This is secondary to regression but required for visualization and KS tests.
- [X] T024 [US2] Implement Bonferroni correction for multiple comparisons in `code/analysis/stats.py`
- [ ] T025 [US2] Create analysis script to generate `data/processed/statistical_results.csv`. **Dependency**: T021, T022, T023, T024, T026.
- [X] T026 [US2] **Mandatory Utility**: Implement shared metadata flag injection in `code/utils/io.py`. **Mechanism**: All CSV writers must add a comment header `# associational_only=true` and JSON writers must include `"associational_only": true`. **Deliverable**: Updated `code/utils/io.py` and `code/ingestion/` writers. **Note**: This task must be completed before T023, T025, T030, and T038 generate their files.
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

- [ ] T029 [US3] Implement Millennium-II and WDM variant data fetcher in `code/ingestion/millennium_loader.py`. **Action**: Attempt to fetch Millennium-II and WDM variant snapshots. **If URLs are unverified or data is missing**: Call T031-LogGap immediately. **Do not skip by design**; the task is to attempt fetch and trigger the gap protocol.
- [ ] T030 [US3] Implement sensitivity analysis script in `code/analysis/sensitivity.py`: Perform a **multi-dimensional sweep** using nested loops over the Cartesian product of threshold sets {a lower bound value, 0.55} and {0.75, 0.85} (for upper bound). Compute stats for each. **Verification**: Calculate p-value variance AND check if significance rank order is preserved. **Deliverable**: `data/processed/sensitivity_report.csv` (columns: threshold_low, threshold_high, p_value, significance, variance, rank_preserved). **Depends on T026** to ensure flag is applied.
- [ ] T031-Fetch [US3] Create script to fetch Millennium-II data (if available) and output `data/raw/millennium/halo_catalog.hdf5`. **Dependency**: T029. **Action**: If fetch fails (HTTP 404/500 or file not found), **immediately trigger T031-LogGap** and skip downstream tasks. **Deliverable**: `data/raw/millennium/halo_catalog.hdf5`.
- [ ] T031-Process [US3] Run ingestion and shape computation pipeline on Millennium-II data (if fetched) and output `data/processed/millennium_shapes.csv`. **Action**: Extract galaxy properties (SFR, radius) from subhalo catalogs and output `data/processed/millennium_galaxy_properties.csv`. **Dependency**: T031-Fetch.
- [ ] T031-Analyze [US3] Run full statistical analysis on Millennium-II data (if processed) and output `data/processed/millennium_results.csv`. **Dependency**: T031-Process.
- [ ] T031-WDM-Fetch [US3] Attempt to fetch WDM variant snapshots (if available). **Dependency**: T029. **Action**: If missing or fetch fails, **immediately trigger T031-LogGap** and skip downstream tasks.
- [ ] T031-WDM-Process [US3] Run ingestion and shape computation pipeline on WDM data (if fetched) and output `data/processed/wdm_shapes.csv`. **Action**: Extract galaxy properties (SFR, radius) from subhalo catalogs and output `data/processed/wdm_galaxy_properties.csv`. **Dependency**: T031-WDM-Fetch.
- [ ] T031-WDM-Analyze [US3] Run full statistical analysis on WDM data (if processed) and output `data/processed/wdm_results.csv`. **Dependency**: T031-WDM-Process.
- [ ] T031-LogGap [US3] **Mandatory**: If T029/T031-Fetch/T031-WDM-Fetch fail, log the specific gap to `data/metadata.yaml`, update `outputs/reports/gap_log.md`, and mark SC-004 as 'Not Measurable' in the final report. **This task ensures FR-007 has a concrete implementation path even if data is missing.** **Trigger**: Called by T029, T031-Fetch, or T031-WDM-Fetch on failure.
- [ ] T032 [US3] Generate sensitivity report comparing significance rates and p-value variance across thresholds. **Dependency**: T030.
- [ ] T033 [US3] Implement cross-dataset comparison logic (TNG-100 vs Millennium-II vs WDM). **Deliverable**: `outputs/reports/cross_dataset_comparison.md` containing correlation diff, p-value diff, and conclusion on consistency. **Dependency**: T031-Analyze and T031-WDM-Analyze (or T031-LogGap if skipped).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Orientation Misalignment Analysis (Priority: P3)

**Goal**: Compute orientation misalignment angles (spin-spin, major-major) and correlate with galaxy properties.

**Independent Test**: Verify pipeline outputs CSV with misalignment angles (degrees) and correlation results with SFR/radius.

**⚠️ DEPENDENCY**: Phase 6 MUST WAIT for Phase 3 (Data: T017, T018) AND Phase 4 (Stats/Properties) completion.

### Tests for User Story 4 (OPTIONAL - only if tests requested) ⚠️

- [ ] T035 [P] [US4] Unit test for angle calculation (dot product/arccos) in `code/tests/test_alignment.py`

### Implementation for User Story 4

- [ ] T036 [US4] **BLOCKING**: Implement spin vector and major axis calculation in `code/processing/alignment.py`. **Dependency**: T017 (halo data), T018 (galaxy data). **Action**: Compute spin vectors for haloes (from T017) and galaxies (from T018).
- [ ] T037 [US4] Implement misalignment angle computation (halo-galaxy pairs) in `code/processing/alignment.py`. **Dependency**: T036, T018. **Action**: Join halo and galaxy data on `halo_id`, compute angles (halo spin vs galaxy spin, halo major axis vs galaxy major axis).
- [ ] T038 [US4] **WAIT FOR T026**: Create script to generate `data/processed/alignment_angles.csv`. **Schema**: `halo_id` (int), `galaxy_id` (int), `spin_angle_deg` (float), `axis_angle_deg` (float). **Dependency**: T037, T026. **Verification**: Ensure file contains valid angles (non-negative to 180) and row count > 0. **Note**: Ensure file contains `associational_only=true` flag via T026.
- [ ] T039 [US4] Implement correlation analysis for misalignment angles vs galaxy properties (SFR, radius). **Dependency**: T038. **Deliverable**: `data/processed/alignment_correlations.csv` (columns: metric, correlation_coeff, p_value, method).
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
# Note: T009 (Test) must wait for T012 interface definition.
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
- **Critical Constraint**: All tasks must run on CPU-only CI (a limited number of cores, 7GB RAM). No GPU, no 8-bit quantization, no large model loading. Use chunking and sampling.
- **Data Gap Protocol**: If a required dataset (e.g., Millennium-II, WDM variants) does not have a verified, public URL in `data/metadata.yaml`, the pipeline MUST attempt to fetch, trigger T031-LogGap, log the specific gap to `data/metadata.yaml` and the final report, mark the associated Success Criterion (SC-004) as 'Not Measurable', and proceed with available data. This prevents unverified data from entering the results while ensuring the gap is documented.
- **WDM Variants**: WDM variant snapshots are NOT included unless a verified URL is found in `data/metadata.yaml`. If missing, the project proceeds with TNG-100 and Millennium-II (if available) only, with SC-004 marked 'Not Measurable'.
- **Sampling Constraint**: Due to hardware limits (7GB RAM), the pipeline uses chunked processing and sampling. This is a documented deviation from FR-001 "every FoF halo" to satisfy SC-005 "feasibility". The project acknowledges this limitation in the final report via `docs/sampling_protocol.md`.