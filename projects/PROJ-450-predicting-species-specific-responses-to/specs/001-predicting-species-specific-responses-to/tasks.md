# Tasks: Predicting Species-Specific Responses to Climate Change from Museum Collection Data

**Input**: Design documents from `/specs/450-predicting-species-niche-shifts/`
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

- [X] T001 Create project structure per implementation plan (`src/`, `data/`, `results/`, `tests/`)
- [X] T002 Initialize R 4.3+ project with `renv` and install dependencies: `rgbif`, `raster`, `sf`, `ggplot2`, `dplyr`, `tidyr`, `caper`, `phylolm`, `pwr`, `tibble`, `lubridate`, `here`, `testthat`
- [X] T003 [P] Configure `.Rprofile` to set `options(stringsAsFactors = FALSE)` and define project root via `here::here()`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `src/code/utils.R` with logging infrastructure (timestamped logs, error capture), helper functions for directory creation, checksum validation, and validation functions for handling missing climate values (NA) and coordinate precision checks (>10km uncertainty) (FR-002, Data Hygiene)
- [X] T005 Create `data/metadata.yaml` schema definition to store query timestamps, API parameters, and file checksums
- [X] T006 [P] Implement `src/code/fetch_gbif.R` skeleton with `rgbif::occ_search` wrapper, ensuring `occurrenceStatus == "PRESERVED_SPECIMEN` filter and taxonomic key resolution
- [ ] T007 [P] Implement `src/code/download_worldclim.R` to check for local WorldClim v2 rasters in `data/raw/worldclim_v2/*.tif` (mean annual temp and precip for 1970-2000 and 1991-2020); if missing, download from WorldClim v2, verify checksums, and save to `data/raw/` (Spec Assumptions)
- [ ] T009 Create `tests/unit/test_utils.R` to verify logging, directory creation, checksum functions, and coordinate validation logic

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Extract and Compute Niche Centroids (Priority: P1) 🎯 MVP

**Goal**: Retrieve GBIF museum records, filter by date/coordinates, extract climate data, and compute centroids for two periods.

**Independent Test**: Run pipeline on multiple test species (plant, bird, insect); verify CSV output with Multiple rows per species (one per period) and log file generation.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensuring they FAIL before implementation. Use mocks/stubs for dependencies.**

- [ ] T010 [P] [US1] Unit test for GBIF filtering logic in `tests/unit/test_fetch_gbif.R::test_filters_records_by_date_span_and_coordinates` (using mocks/stubs)
- [ ] T011 [P] [US1] Unit test for climate extraction on synthetic coordinates in `tests/unit/test_extract_climate.R` (using mocks/stubs)
- [ ] T012 [US1] Integration test: Verify full centroid generation for multiple species produces correct CSV schema in `tests/integration/test_us1_centroids.R`

### Implementation for User Story 1

- [ ] T013 [US1] Implement `src/code/fetch_gbif.R` to query GBIF for `PRESERVED_SPECIMEN` using species list from `data/species_list.csv` (or CLI arg), parse dates, filter by ≥50 year span, and save raw CSV to `data/raw/`
- [~] T014 [US1] Implement `src/code/extract_climate.R` to extract mean annual temp (°C) and precip (mm) from WorldClim v2 layers (loaded via T007) for 1970-2000 and 1991-2020, handling NAs
- [~] T015a [US1] Implement `src/code/compute_centroids.R` to calculate arithmetic mean of climate variables per species/period and output `data/processed/centroids.csv` (aggregated means)
- [~] T015b [US1] Implement `src/code/compute_centroids.R` to also output `data/processed/points_with_climate.csv` (raw occurrence points with climate values) as an intermediate artifact specifically for FR-005 global z-scoring
- [~] T017 [US1] Enhance logging in `src/code/fetch_gbif.R` and `compute_centroids.R` to record record counts, filtering decisions, and species warnings (FR-010) <!-- FAILED: unspecified -->

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Relate Niche Shifts to Regional Warming (Priority: P2)

**Goal**: Calculate niche shift magnitude (ΔN), regional warming (ΔT), perform PGLS regression, generate plots, and run power analysis.

**Independent Test**: Execute regression module on centroid data; verify slope, 95% CI, R², p-value, and a 1200x800px PNG plot are generated.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T018 [P] [US2] Unit test for Euclidean distance calculation in standardized climate space in `tests/unit/test_shifts.R`
- [~] T019 [P] [US2] Unit test for regional warming calculation (independent grid) in `tests/unit/test_regional_warming.R`
- [~] T020 [P] [US2] Integration test: Verify PGLS regression output schema and plot generation in `tests/integration/test_us2_regression.R` <!-- ATOMIZE: requested -->

### Implementation for User Story 2

- [~] T021 [US2] Implement `src/code/compute_shifts.R` to perform global z-scoring (temp, precip) across ALL species occurrence points pooled (from `data/processed/points_with_climate.csv`) and calculate Euclidean distance (ΔN) between periods (FR-005) <!-- ATOMIZE: requested -->
- [~] T022 [US2] Implement `src/code/compute_regional_warming.R` to calculate ΔT from WorldClim rasters by computing the zonal mean over the species' occurrence envelope (bounding box from min/max lat/lon of species points) using an *independent regional climate grid* to avoid circularity (FR-006)
- [~] T023a [US2] Implement `src/code/analyze_shifts.R` to perform regression of ΔN vs ΔT: If `data/phylogeny.tre` exists and is valid, run PGLS (primary method); else run WLS (fallback per Plan). Output slope, 95% CI, R², p-value, and per-region summaries (FR-007, FR-011, Plan Statistical Rigor)
- [~] T023c [US2] Implement `src/code/analyze_shifts.R` output formatting for regression results (slope, CI, R², p-value) and per-region summaries (FR-011)
- [~] T023d [US2] Implement `src/code/analyze_shifts.R` logic to assign species to latitudinal bands (10° intervals) and run regression loop per region, outputting summary table of coefficients with 95% CI (FR-011)
- [~] T025 [US2] Implement `src/code/power_analysis.R` to conduct a priori power analysis for n≥30 species using alpha=0.05, power=0.8, effect_size read from `config.yaml` (default set to a moderate magnitude). Calculate required n to achieve Margin of Error (MoE) ≤ 0.15 for slope estimate, report MoE, and save to `results/power_analysis_report.csv` (FR-012, SC-007) <!-- FAILED: unspecified -->
- [~] T026 [US2] Implement `src/code/plotting.R` to generate scatter plot (ΔN vs ΔT) colored by taxonomic group, ensuring resolution ≥1200x800px (FR-008)
- [~] T027 [US2] Add logging to `analyze_shifts.R` and `plotting.R` to record regression steps, per-region results, and plot generation details (FR-010)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis of Sampling Effort (Priority: P3)

**Goal**: Subsample occurrence records (50%, 10 replicates), recompute shifts, and report variability metrics.

**Independent Test**: Run sensitivity module on a species with a sufficient number of records; verify 10 replicate shift values and SD calculation match sample variance.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T028 [P] [US3] Unit test for subsampling logic (random [deferred] selection) in `tests/unit/test_sensitivity.R`
- [~] T029 [P] [US3] Unit test for SD calculation and flagging logic (≥0.2 threshold) in `tests/unit/test_sensitivity.R`
- [~] T030 [P] [US3] Integration test: Verify full sensitivity run produces mean/SD and flags high-variability species in `tests/integration/test_us3_sensitivity.R`

### Implementation for User Story 3

- [~] T031 [US3] Implement `src/code/sensitivity.R` to perform a set of random subsamples of [deferred] of records per species using `set.seed(42)` for reproducibility (FR-009) <!-- FAILED: unspecified -->
- [~] T032 [US3] Implement `src/code/sensitivity.R` to recompute niche shift magnitude for each replicate and calculate mean/SD of shifts
- [~] T033 [US3] Add logic in `src/code/sensitivity.R` to flag species with SD ≥ 0.2 climate-space units and skip species with <80 records (FR-009)
- [~] T034 [US3] Output `results/sensitivity_summary.csv` and append detailed log entries for subsampling outcomes (FR-010)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T035 [P] Run `testthat` suite for all unit and integration tests
- [~] T036a [P] Validate SC-001: Check logs to confirm ≥90% of supplied species with ≥50 valid records produced a complete `centroids.csv` record for both periods
- [~] T036b [P] Validate SC-006: Check per-region regression summary to confirm ≥80% of regions produced computable results (count of regions with valid results / total regions)
- [~] T037 [P] Verify all PNG plots meet 1200x800px resolution requirement (SC-004)
- [~] T038 [P] Validate log file warning ratio is ≤5% of total processed records (SC-005)
- [~] T039 [P] Run `quickstart.md` validation to ensure end-to-end pipeline execution completes within 6 hours <!-- FAILED: unspecified -->
- [~] T040 [P] Final documentation update: Ensure `research.md` and `data-model.md` reflect final query parameters and checksums

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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **Produces `data/processed/centroids.csv` and `data/processed/points_with_climate.csv`**.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on `data/processed/points_with_climate.csv`** from US1 for global z-scoring and `centroids.csv` for regression input.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Depends on `data/raw/`** (raw records) from US1 for subsampling.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation (using mocks/stubs)
- Models before services (R scripts)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (provided data dependencies are managed via file outputs)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for GBIF filtering logic in tests/unit/test_fetch_gbif.R (mocks)"
Task: "Unit test for climate extraction in tests/unit/test_extract_climate.R (mocks)"
Task: "Integration test for centroid generation in tests/integration/test_us1_centroids.R"

# Launch implementation tasks (sequential within story due to data flow):
Task: "Implement fetch_gbif.R" -> produces data/raw
Task: "Implement extract_climate.R" -> reads data/raw
Task: "Implement compute_centroids.R" -> reads climate data
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Fetch, Extract, Centroids)
4. **STOP and VALIDATE**: Test User Story 1 independently (verify CSV and logs)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Requires US1 output)
4. Add User Story 3 → Test independently → Deploy/Demo (Requires US1 raw data)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Ingestion & Centroids)
 - Developer B: User Story 2 (Regression & Analysis - can start mock data, then switch to real US1 output)
 - Developer C: User Story 3 (Sensitivity - can start mock data, then switch to real US1 raw data)
3. Stories complete and integrate independently via shared `data/` and `results/` artifacts

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (using mocks/stubs)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **CRITICAL**: Ensure `src/code/fetch_gbif.R` strictly filters for `PRESERVED_SPECIMEN` and ≥50 year span before passing data downstream.
- **CRITICAL**: Ensure `src/code/compute_shifts.R` uses **global** z-scoring across ALL species for standardization as per FR-005, reading from `points_with_climate.csv`.
- **CRITICAL**: Ensure `src/code/analyze_shifts.R` uses **independent** regional climate grids for ΔT to avoid circularity (FR-006) and prioritizes PGLS (Plan) with WLS fallback.
- **CRITICAL**: Ensure all plots are saved as PNG with resolution ≥1200x800px.
- **CRITICAL**: Ensure power analysis is performed before final regression interpretation and reports MoE target ≤ 0.15.
- **CRITICAL**: Ensure sensitivity analysis subsamples 50% of records, 10 replicates, with `set.seed(42)`.
- **CRITICAL**: Ensure `src/code/download_worldclim.R` (T007) checks for local rasters in `data/raw/worldclim_v2/*.tif` before downloading.