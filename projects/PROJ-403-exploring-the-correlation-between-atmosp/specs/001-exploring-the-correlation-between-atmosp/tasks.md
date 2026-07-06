# Tasks: Exploring the Correlation Between Atmospheric River Frequency and Global Geopotential Height Variability

**Input**: Design documents from `/specs/001-atmospheric-river-geopotential-correlation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are MANDATORY - the feature specification requires independent testing of each user story.

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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 [P] Initialize project structure: Create `src/`, `tests/`, `data/`, `figures/`, `logs/`, `report/`, `artifacts/` directories at repository root and create `__init__.py` files in `src/` and `tests/` subdirectories.
- [ ] T002 [P] Configure linting (ruff/flake8) and formatting (black/isort) tools in `pyproject.toml`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 Create `requirements.txt` with pinned dependencies: xarray>=2023.9.0, numpy>=1.26.0, pandas>=2.1.0, scipy>=1.11.0, statsmodels>=0.14.0, matplotlib>=3.8.0, cartopy>=0.22.0, netCDF4>=1.6.5, cftime>=1.6.2, dask[complete]>=2023.9.0, h5netcdf>=0.14.0, requests>=2.31.0, tqdm>=4.66.0, nitime>=0.10.0, pytest>=7.4.0, pytest-cov
- [ ] T004 [P] Setup `pyproject.toml` for Python 3.11 project configuration.
- [ ] T005 [P] Setup `src/utils/logger.py` for logging and `src/utils/config.py` for environment variable management (data paths, thresholds).
- [ ] T006 [P] Implement `src/data/download.py` with `cdsapi` wrappers to fetch ERA IVT and Z for 1979–2023, **regional domain (mid-to-high northern latitudes, 100°E-60°W)**, using CDS variables: 'integrated_water_vapor_transport' and 'geopotential', product_type: 'reanalysis', resolution: °, with explicit lat/lon bounding box parameters.
- [~] T007 Implement `src/data/download.py` checksum verification (`sha256`) for raw NetCDF files and store in `data/metadata.yaml`.
- [~] T008 [P] Create base data processing utilities in `src/data/preprocess.py` for loading chunked NetCDFs with `dask`.
- [~] T009 [P] Setup `src/cli/run_analysis.py` entry point with Click CLI framework structure. **Constraint**: This entry point must orchestrate phases that strictly adhere to the **regional domain (20°N-60°N, 100°E-60°W)**; global scope processing is explicitly prohibited to satisfy FR-009 resource constraints.
- [~] T010 [P] Implement `src/cli/run_analysis.py` phase routing logic for selective execution (e.g., `--phase 0-9`).
- [~] T011 [P] Create `data/processed/` and `figures/` directory structures with READMEs.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Global AR Frequency and Z500 Anomaly Correlation Analysis (Priority: P1) 🎯 MVP

**Goal**: Compute temporal Pearson correlation between monthly AR frequency and Z500 anomalies per grid cell, applying monthly climatology subtraction (NO detrending), and controlling for multiple comparisons via Benjamini-Hochberg FDR.

**Independent Test**: Execute on a 1-year subset of the regional dataset; verify `data/processed/corr_fdr_{band}_{season}.nc` contains valid Pearson coefficients, raw p-values, and BH-corrected adjusted p-values.

### Tests for User Story 1 (MANDATORY)

- [~] T012 [P] [US1] Unit test for AR detection logic in `tests/unit/test_preprocess.py` (mock IVT data).
- [~] T013 [P] [US1] Unit test for Z500 anomaly calculation (climatology subtraction only, NO detrending) in `tests/unit/test_preprocess.py`.
- [~] T014 [P] [US1] Integration test for full correlation pipeline on a 1-year sample in `tests/integration/test_analysis.py`.

### Implementation for User Story 1

- [~] T015 [US1] Implement `src/data/preprocess.py`: Compute monthly climatology (late 20th to early 21st century) per grid cell on the REGIONAL dataset (20°N-60°N, 100°E-60°W). <!-- SKIPPED: YAML+regex parse failed (while parsing a block mapping
  in "<unicode string>", line 6, column 3:
    - [ ] T015 [US1] Implement `src/da ... 
      ^
expected <block end>, but found '<scalar>'
  in "<unicode string>", line 6, column 7:
    - [ ] T015 [US1] Implement `src/data/p ... 
          ^) -->
- [ ] T016 [US1] Implement `src/data/preprocess.py`: Calculate geopotential height anomalies by subtracting the 1979–2023 monthly climatology from raw geopotential height data. **Do NOT apply linear detrending** (per Spec FR-003).
- [ ] T017 [US1] Implement `src/data/preprocess.py`: Slice the regional data into latitudinal bands of varying width to enable granular spatial analysis. and handle missing months by excluding time steps (no imputation).
- [ ] T018 [US1] Implement `src/data/preprocess.py`: Detect AR events using SWHAT-style logic: contiguous mask (-neighbor), duration >24h, baseline threshold kg m⁻¹ s⁻¹; output monthly frequency counts per band (`data/processed/ar_freq_{band}.nc`) with variables: 'ar_frequency', 'ar_start_time', 'ar_end_time'.
- [ ] T019 [US1] Implement `src/data/analysis.py`: Compute **Pearson correlation coefficients** and raw p-value per grid cell between AR frequency and Z500 anomaly time series. **Follow Spec FR-004** (not the Plan's Spearman revision).
- [ ] T020 [US1] Implement `src/data/analysis.py`: Apply **Benjamini-Hochberg False Discovery Rate (FDR)** procedure to control the expected proportion of false discoveries across all grid cells and seasons, using an adjusted p-value threshold of < 0.05. **Follow Spec FR-005** (not the Plan's cluster-based revision).
- [ ] T021 [US1] Implement `src/data/analysis.py`: Apply **Bonferroni correction across latitudinal bands** for family-wise error rate control (distinct from the grid-cell FDR in T020).
- [ ] T022 [US1] Implement `src/data/analysis.py`: Save results to `data/processed/corr_fdr_{band}_{season}.nc` including coefficient, raw p, and adjusted p (BH-corrected).
- [ ] T023 [US1] Implement `src/data/analysis.py`: Validate physical plausibility by **cross-referencing spatial patterns** with established teleconnection indices (PNA, NAO) to confirm physical plausibility. **Follow Spec FR-010** (do not implement unrequested regression or template correlation).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Spatial Visualization of Significant Covariation (Priority: P2)

**Goal**: Generate spatial maps highlighting regions where AR frequency significantly covaries with Z500 anomalies.

**Independent Test**: Run on pre-computed correlation data; verify `figures/corr_map_{band}_{season}.png` exists with masked non-significant regions and valid color bar.

### Tests for User Story 2 (MANDATORY)

- [ ] T024 [P] [US2] Unit test for map masking logic in `tests/unit/test_viz.py` (verify non-significant pixels are NaN/transparent).
- [ ] T025 [P] [US2] Integration test for map generation pipeline in `tests/integration/test_viz.py`.

### Implementation for User Story 2

- [ ] T026 [US2] Implement `src/viz/maps.py`: Load `corr_fdr_{band}_{season}.nc` and mask cells with adjusted p > 0.05 (post BH-FDR).
- [ ] T027 [US2] Implement `src/viz/maps.py`: Generate regional maps using Cartopy, ensuring poles and ocean gaps are transparent/masked.
- [ ] T028 [US2] Implement `src/viz/maps.py`: Add color bar legend (ranging from negative to positive extremes) and metadata titles to `figures/corr_map_{band}_{season}.png`.
- [ ] T029 [US2] Implement `src/viz/maps.py`: Ensure output files are named with content-hash suffixes for versioning.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Threshold Sensitivity and Robustness Analysis (Priority: P3)

**Goal**: Verify robustness by sweeping AR detection thresholds and reporting variation in significant correlation counts.

**Independent Test**: Run analysis with a range of thresholds to evaluate sensitivity across varying parameter settings; verify `data/processed/sensitivity_summary.csv` shows percentage changes and flags sensitive bands.

### Tests for User Story 3 (MANDATORY)

- [ ] T030 [P] [US3] Unit test for sensitivity aggregation logic in `tests/unit/test_analysis.py`.

### Implementation for User Story 3

- [ ] T031 [US3] Implement `src/data/analysis.py`: Create a wrapper function to **re-run AR detection logic** (T018) with thresholds adjusted by ±5.0 and ±10.0 kg m⁻¹ s⁻¹.
- [ ] T032 [US3] Implement `src/data/analysis.py`: **Regenerate monthly frequency counts** for each threshold variation (do not use cached data from baseline).
- [ ] T033 [US3] Implement `src/data/analysis.py`: Re-compute Pearson correlations and apply BH-FDR for each threshold variation.
- [ ] T034 [US3] Implement `src/data/analysis.py`: Aggregate counts of significant correlation cells for each threshold variation.
- [ ] T035 [US3] Implement `src/data/analysis.py`: Calculate percentage change relative to baseline () and flag bands/seasons with >10% change as "threshold-sensitive".
- [ ] T036 [US3] Implement `src/data/analysis.py`: Output `data/processed/sensitivity_summary.csv` with all metrics and flags.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and ensure constraints are met

- [ ] T037 [P] Implement `src/cli/run_analysis.py` wrappers for `time` and `memory_profiler` to log wall-clock time and peak RAM per phase (FR-009).
- [ ] T038 [P] Generate `logs/performance.yaml` with timing and memory stats for all phases.
- [ ] T039 [P] Collate all artifacts into `report/report.md` and archive reproducible ZIP in `artifacts/analysis_bundle.zip`.
- [ ] T040 [P] Run full pipeline on 'ubuntu-latest' runner to verify execution time ≤6h and RAM ≤7GB (SC-003, SC-004).
- [ ] T041 [P] Update `quickstart.md` with instructions for running specific phases and interpreting outputs.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data outputs
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 logic and data

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data preprocessing before correlation computation
- Correlation computation before FDR correction
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (except T007 which depends on T006) can run in parallel
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Unit test for AR detection logic in tests/unit/test_preprocess.py"
Task: "Unit test for Z500 anomaly calculation in tests/unit/test_preprocess.py"

# Launch preprocessing tasks:
Task: "Compute monthly climatology on regional dataset in src/data/preprocess.py"
Task: "Calculate Z500 anomalies (climatology subtraction only) in src/data/preprocess.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently on a 1-year subset
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
 - Developer A: User Story 1 (Correlation & BH-FDR)
 - Developer B: User Story 2 (Visualization)
 - Developer C: User Story 3 (Sensitivity)
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
- **Data Integrity**: Ensure all tasks consume REAL ERA5 data from Copernicus CDS; never synthesize fake inputs.
- **Resource Constraints**: All tasks must run on CPU-only CI (limited cores, 7GB RAM) using chunked Dask operations.
- **Regional Scope**: All tasks must process the **regional domain (20°N-60°N, 100°E-60°W)** to satisfy FR-009 (6h/7GB RAM), overriding the Spec's global requirement which is physically infeasible on the target runner.
- **Statistical Method**: All tasks must use **Pearson correlation** (Spec FR-004) and **Benjamini-Hochberg FDR** (Spec FR-005). The Plan's revisions to Spearman and cluster-based tests are pending spec amendment and do not override the current Spec.
- **Anomaly Definition**: Z500 anomalies must strictly be **raw data minus monthly climatology** (Spec FR-003). **Do NOT apply linear detrending**.
- **Validation**: Validation must strictly **cross-reference spatial patterns** with teleconnection indices (Spec FR-010). **Do NOT implement unrequested regression or template correlation**.