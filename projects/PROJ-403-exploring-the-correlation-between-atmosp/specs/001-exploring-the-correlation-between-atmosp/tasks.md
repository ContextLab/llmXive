# Tasks: Exploring the Correlation Between Atmospheric River Frequency and Global Geopotential Height Variability

**Input**: Design documents from `/specs/001-atmospheric-river-geopotential-correlation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are MANDATORY - the feature specification requires independent testing of each user story.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[S]**: Sequential (depends on previous tasks)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Initialize project structure: Create `src/`, `tests/`, `data/`, `figures/`, `logs/`, `report/`, `artifacts/` directories at repository root and create `__init__.py` files in `src/` and `tests/` subdirectories.
- [X] T002 [P] Configure linting (ruff/flake8) and formatting (black/isort) tools in `pyproject.toml`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Create `requirements.txt` with pinned dependencies: xarray>=2023.9.0, numpy>=1.26.0, pandas>=2.1.0, scipy>=1.11.0, statsmodels>=0.14.0, cartopy>=0.22.0, netCDF4>=1.6.5, cftime>=1.6.2, dask[complete]>=2023.9.0, h5netcdf>=0.14.0, requests>=2.31.0, tqdm>=4.66.0, nitime>=0.10.0, pytest-cov
- [X] T004 [P] Setup `pyproject.toml` for Python 3.11 project configuration.
- [X] T005 [P] Setup `src/utils/logger.py` for logging and `src/utils/config.py` for environment variable management (data paths, thresholds).
- [X] T006 [S] [FR-001] [FR-009] **Override Plan Phase 0**: Implement `src/data/download.py` with `cdsapi` wrappers to fetch ERA IVT and Z for **1979–2023**, **full global grid (90°S-90°N, 180°W-180°E)**. **Specific CDS API parameters**: dataset='reanalysis-era5-single-levels-monthly-means', variable=['integrated_water_vapor_transport', 'z'], level=['500'], product_type='reanalysis', resolution='high', format='netcdf', start_date='1979-01-01', end_date='2023-12-31', area=[90, -180, -90, 180]. Include logic to convert 'z' from m²/s² to meters if necessary.
- [X] T007 [S] [FR-001] Implement `src/data/download.py` checksum verification (`sha256`) for raw NetCDF files and store in `data/metadata.yaml`. **Depends on T006 completion.**
- [X] T008 [P] Create base data processing utilities in `src/data/preprocess.py` for loading chunked NetCDFs with `dask`.
- [X] T009a [P] [FR-009] Setup `src/cli/run_analysis.py` entry point with Click CLI framework structure.
- [X] T009b [P] [FR-009] Implement `src/cli/run_analysis.py` domain filtering logic to process the **full global grid** (90°S-90°N, 180°W-180°E) using streaming/chunked operations to satisfy FR-009.
- [X] T010 [P] [FR-009] Implement `src/cli/run_analysis.py` phase routing logic for all phases (0-9).
- [X] T011 [P] Create `data/processed/` and `figures/` directory structures with READMEs.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Global AR Frequency and Z500 Anomaly Correlation Analysis (Priority: P1) 🎯 MVP

**Goal**: Compute temporal correlation between monthly AR frequency and Z500 anomalies per grid cell, applying monthly climatology subtraction, and controlling for multiple comparisons via Benjamini-Hochberg FDR as mandated by Spec FR-005.

### Methodology Override
**⚠️ CRITICAL**: The Plan Summary proposes Spearman correlation and Cluster-based FDR. **This implementation strictly overrides the Plan** to adhere to Spec FR-004 (Pearson correlation) and FR-005 (Benjamini-Hochberg FDR). All tasks in this phase must follow the Spec.

**Independent Test**: Execute on a 1-year subset of the global dataset; verify `data/processed/corr_fdr_{band}_{season}.nc` contains valid Pearson coefficients, raw p-values, and BH-FDR adjusted p-values.

**Note on TDD**: Tasks T012-T014 are marked [P] for *authoring* (Test-Driven Development), but their *execution* depends on the implementation tasks (T015-T023). Tests must run after code is written.

### Tests for User Story 1 (MANDATORY)

- [X] T012 [P] [US1] Unit test for AR detection logic in `tests/unit/test_preprocess.py` (mock IVT data).
- [X] T013 [P] [US1] Unit test for Z500 anomaly calculation (climatology subtraction) in `tests/unit/test_preprocess.py`.
- [X] T014 [P] [US1] Integration test for full correlation pipeline on a 1-year sample in `tests/integration/test_analysis.py`.

### Implementation for User Story 1

- [X] T015 [S] [US1] [FR-001] Implement `src/data/preprocess.py`: Compute monthly climatology (1979–2023) per grid cell on the GLOBAL dataset using streaming.
- [X] T016a [S] [US1] [FR-003] Implement `src/data/preprocess.py`: Calculate geopotential height anomalies by subtracting the multi-decadal monthly climatology from raw geopotential height data. **Depends on T015.**
- [X] T017 [S] [US1] [FR-001] [FR-004] Implement `src/data/preprocess.py`: Slice the global data into **10° latitudinal bands** covering the **full globe** (90°S-80°S, 80°S-70°S,..., 80°N-90°N). **Handle polar regions (latitudes >80°) by applying cosine(latitude) equal-area weighting** to prevent geometric distortion. Handle missing months by excluding time steps (no imputation). Output: `data/processed/global_subset_{band}.nc`. **Depends on T016a.**
- [X] T018 [S] [US1] [FR-002] [FR-008] Implement `src/data/preprocess.py`: Detect AR events using SWHAT-style logic: contiguous mask (8-connectivity, `scipy.ndimage.label` with `structure=generate_binary_structure(2, 2)`), **duration threshold >= 24 hours**, baseline threshold of **250 kg m⁻¹ s⁻¹**. **Explicitly exclude time steps with missing data before aggregating monthly frequency counts.** Output monthly frequency counts per band (`data/processed/ar_freq_{band}.nc`) with variables: 'ar_frequency', 'ar_start_time', 'ar_end_time'. **Depends on T017.**
- [X] T019 [S] [US1] [FR-004] **Override Plan Summary**: Implement `src/data/analysis.py`: Compute **Pearson correlation coefficients** and raw p-value per grid cell between AR frequency and Z500 anomaly time series. **Strictly follows Spec FR-004.** **Depends on T018, T016a.**
- [X] T020 [S] [US1] [FR-005] **Override Plan Summary**: Implement `src/data/analysis.py`: Apply **Benjamini-Hochberg False Discovery Rate (FDR)** procedure using `statsmodels.stats.multitest.multipletests` (method='fdr_bh') to control the expected proportion of false discoveries across all grid cells within a band-season, using an adjusted p-value threshold of < 0.05. **Strictly follows Spec FR-005.** **Depends on T019.**
- [X] T022 [S] [US1] Implement `src/data/analysis.py`: Save results to `data/processed/corr_fdr_{band}_{season}.nc` including coefficient, raw p, and adjusted p (BH-FDR). **Depends on T020.**
- [X] T023a [S] [US1] [FR-010] Implement `src/data/analysis.py`: **Spatial Validation**: Compute spatial correlation coefficients between the significant AR-Z500 pattern and canonical teleconnection templates (PNA/NAO spatial maps) from NOAA CPC (URL: `). Output: `data/processed/validation_spatial_{band}_{season}.json`.
- [X] T023b [S] [US1] [FR-010] Implement `src/data/analysis.py`: **Scalar Regression**: Regress the AR-Z500 fields against scalar PNA/NAO index time series from NOAA CPC (URL: `). Output: `data/processed/validation_scalar_{band}_{season}.json`. **Note: Implements Spec FR-010 and Plan FR-010 requirements.**

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Spatial Visualization of Significant Covariation (Priority: P2)

**Goal**: Generate spatial maps highlighting regions where AR frequency significantly covaries with Z500 anomalies.

**Independent Test**: Run on pre-computed correlation data; verify `figures/corr_map_{band}_{season}.png` exists with masked non-significant regions and valid color bar.

### Tests for User Story 2 (MANDATORY)

- [X] T024 [P] [US2] Unit test for map masking logic in `tests/unit/test_viz.py` (verify non-significant pixels are NaN/transparent).
- [X] T025 [P] [US2] Integration test for map generation pipeline in `tests/integration/test_viz.py`.

### Implementation for User Story 2

- [X] T026 [S] [US2] Implement `src/viz/maps.py`: Load `corr_fdr_{band}_{season}.nc` and mask cells with adjusted p > 0.05 (post BH-FDR).
- [X] T027 [S] [US2] Implement `src/viz/maps.py`: Generate global maps using Cartopy, ensuring poles and ocean gaps are transparent/masked. **Depends on T026.**
- [X] T028 [S] [US2] Implement `src/viz/maps.py`: Add color bar legend (ranging from negative to positive extremes) and metadata titles to `figures/corr_map_{band}_{season}.png`. **Depends on T027.**
- [X] T029 [S] [US2] Implement `src/viz/maps.py`: Ensure output files are named with content-hash suffixes (SHA-256 of file contents) using algorithm: generate file to temporary name -> compute SHA-256 -> rename to final name with hash suffix (`corr_map_{band}_{season}_{hash}.png`). **Depends on T028.**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Threshold Sensitivity and Robustness Analysis (Priority: P3)

**Goal**: Verify robustness by sweeping AR detection thresholds and reporting variation in significant correlation counts.

**Independent Test**: Run analysis with a range of thresholds to evaluate sensitivity across varying parameter settings; verify `data/processed/sensitivity_summary.csv` shows percentage changes and flags sensitive bands.

### Tests for User Story 3 (MANDATORY)

- [X] T030 [P] [US3] Unit test for sensitivity aggregation logic in `tests/unit/test_analysis.py`.

### Implementation for User Story 3

- [X] T031 [S] [US3] [FR-007] **Override Plan Summary**: Implement `src/data/analysis.py`: Create a wrapper function to **re-run the entire correlation and FDR pipeline (T019-T022)** by **invoking the parameterized AR detection function from T018** with thresholds adjusted by ±5.0 and ±10.0 kg m⁻¹ s⁻¹ **relative to the baseline 250 kg m⁻¹ s⁻¹**. **Note: This task defines the wrapper logic.** **Depends on T018.**
- [X] T032 [S] [US3] Implement `src/data/analysis.py`: **Regenerate monthly frequency counts** for each threshold variation. Output files: `data/processed/ar_freq_{band}_{threshold}.nc`. **Depends on T031.**
- [X] T033 [S] [US3] Implement `src/data/analysis.py`: Re-compute **Pearson correlations** and apply **Benjamini-Hochberg FDR** for each threshold variation. **Note: Implements Spec FR-004 and FR-005.** **Depends on T032.**
- [X] T034 [S] [US3] Implement `src/data/analysis.py`: Aggregate counts of significant correlation cells for each threshold variation. **Depends on T033.**
- [X] T035 [S] [US3] Implement `src/data/analysis.py`: Calculate percentage change relative to baseline and flag bands/seasons with >10% change as "threshold-sensitive". **Depends on T034.**
- [X] T036 [S] [US3] Implement `src/data/analysis.py`: Output `data/processed/sensitivity_summary.csv` with all metrics and flags. **Depends on T035.**

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and ensure constraints are met

- [X] T037 [P] [FR-009] Implement `src/cli/run_analysis.py` wrappers for `time` and `memory_profiler` to log wall-clock time and peak RAM per phase (FR-009).
- [X] T038 [P] [FR-009] Generate `logs/performance.yaml` with timing and memory stats for all phases.
- [X] T039 [P] Collate all artifacts into `report/report.md` and archive reproducible ZIP in `artifacts/analysis_bundle.zip`.
- [X] T040 [P] [SC-003] [SC-004] Run full pipeline on 'ubuntu-latest' runner to verify execution time ≤6h **measured via wall-clock time** and RAM ≤7GB (SC-003, SC-004).
- [X] T041 [P] Update `quickstart.md` with instructions for running specific phases and interpreting outputs.

---

## Phase 7: Data Integrity & Execution Safety (Revision Pass)

**Goal**: Address specific execution risks regarding data sourcing, memory constraints, and statistical validity identified during plan review.

**Rationale**: Ensures the pipeline fails loudly on missing real data (no synthetic fallbacks), handles the global dataset via streaming to respect RAM limits, and aligns statistical methods with the Spec while preparing for Plan amendment.

- [X] T042 [P] [FR-001] Implement `src/data/download.py`: Enforce **strict real-data sourcing**. Remove any `try/except` blocks that might fall back to synthetic/mock data. If the CDS fetch fails, the script must raise a `DataFetchError` and terminate. Add explicit logging of the CDS query parameters and file checksums.
- [X] T043 [P] [FR-009] Implement `src/data/preprocess.py`: Refactor global data loading to use **Dask streaming** (`chunks={'time': 1, 'lat': 180, 'lon': 360}` or similar) to ensure peak RAM never exceeds a moderate threshold during the 45-year global load. Verify that `xarray.open_mfdataset` uses `combine='by_coords'` with `parallel=True`.
- [X] T044 [P] [FR-003] Implement `src/data/preprocess.py`: Add explicit handling for **polar regions** (latitudes > 80°) to **apply cosine(latitude) equal-area weighting** to prevent geometric distortion in the correlation matrix, ensuring full 90°S-90°N coverage as per Spec FR-001.
- [X] T045 [P] [FR-005] Implement `src/data/analysis.py`: Add a **fallback check** for the Benjamini-Hochberg procedure: if the adjusted p-value threshold yields *zero* significant cells, the script must output a specific "No significant correlations found" flag in the JSON report rather than failing silently or producing an empty array without explanation.
- [X] T046 [P] [FR-010] Implement `src/data/analysis.py`: Integrate a **teleconnection index loader** (NOAA CPC) that fetches scalar PNA/NAO indices via verified URL ` (CSV format, monthly alignment) and matches the time alignment (monthly) with the AR/Z500 data before performing regression validation.
- [X] T047 [P] [Plan Amendment] Update `plan.md` to explicitly document the conflict between Spec FR-004/FR-005 (Pearson/BH-FDR) and the Plan's proposed Spearman/Cluster-FDR. Add a "Methodology Resolution" section stating that the current implementation adheres to the Spec, and a formal amendment request is pending for the next review cycle.

**Checkpoint**: Data integrity, memory safety, and methodological alignment confirmed.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete
- **Data Integrity (Phase 7)**: Can run in parallel with Implementation tasks, but must be completed before the final full-pipeline run (T040).

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
- Phase 7 (Data Integrity) tasks can run in parallel with US1-3 implementation tasks.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Unit test for AR detection logic in tests/unit/test_preprocess.py"
Task: "Unit test for Z500 anomaly calculation in tests/unit/test_preprocess.py"

# Launch preprocessing tasks:
Task: "Compute monthly climatology on global dataset in src/data/preprocess.py"
Task: "Calculate Z500 anomalies (climatology subtraction) in src/data/preprocess.py"
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
 - Developer D: Phase 7 (Data Integrity & Safety)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [S] tasks = sequential dependencies (must follow specific predecessors)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Data Integrity**: Ensure all tasks consume REAL ERA5 data from Copernicus CDS; never synthesize fake inputs.
- **Resource Constraints**: All tasks must run on CPU-only CI (limited cores, 7GB RAM) using chunked Dask operations.
- **Global Scope**: All tasks must process the **full global grid** (90°S-90°N, 180°W-180°E) as required by Spec FR-001 and FR-004. Streaming logic is used to handle data volume. Polar regions (>80°) are included with equal-area weighting.
- **Statistical Method**: All tasks must use **Pearson correlation** and **Benjamini-Hochberg FDR** as mandated by Spec FR-004 and FR-005. **This overrides the Plan's conflicting methodology.**
- **Anomaly Definition**: Z500 anomalies must be calculated by subtracting the monthly climatology as per Spec FR-003.
- **Validation**: Validation must include both **spatial pattern correlation** and **scalar regression** as mandated by Spec FR-010 and Plan FR-010.
- **Methodological Alignment**: Tasks strictly implement Spec requirements. The Plan's alternative methodology (Spearman, Cluster-based tests) is flagged as conflicting and requires a formal Spec/Plan amendment.
- **Sequential Dependencies**: Task T031 (Sensitivity Analysis start) is marked [S] (Sequential) relative to T018 because it depends on the base AR detection logic.
- **Execution Safety**: Phase 7 tasks (T042-T047) are critical to prevent the "fabrication gate" rejection by ensuring no synthetic fallbacks and proper memory management.