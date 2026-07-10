# Tasks: Exploring the Relationship Between Cosmic Ray Composition and Solar Activity Cycles

**Input**: Design documents from `/specs/001-cosmic-ray-composition-solar-cycle/`
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

- [ ] T001 Create project structure per implementation plan (`code/`, `tests/`, `data/`)
- [ ] T002 Initialize Python 3.11 project with dependencies: `pandas`, `numpy`, `scikit-learn`, `scipy`, `matplotlib`, `requests`, `pyyaml`, `statsmodels`, `pytest`
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/utils/config.py` to manage dataset URLs (AMS-02, NOAA) and run parameters
- [X] T005 [P] Implement `code/utils/logging.py` for structured logging of data gaps and fetch errors
- [X] T006 [P] Setup `code/data/__init__.py` and data directory structure (`data/raw/`, `data/processed/`, `data/checksums.txt`)
- [~] T007 Create base data entities in `code/data/models.py` (CosmicRayFlux, SolarActivityIndex, CompositionRatio). **CRITICAL**: The `CosmicRayFlux` entity MUST explicitly include a `rigidity` attribute (float) to support Constitution Principle VI (Rigidity-Dependent Flux Calibration) and FR-001. The model must enforce that every flux measurement is tied to a specific rigidity bin.
- [~] T008 Implement checksum verification script `code/utils/verify_checksums.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Retrieve and Preprocess Multi-Species Cosmic Ray Flux Data (Priority: P1) 🎯 MVP

**Goal**: Download daily averaged, rigidity-binned differential flux data for protons, helium, and heavier nuclei (CNO/Fe) from AMS and align with NOAA sunspot numbers (recent solar cycles).

**Independent Test**: A script can be run that downloads the specified AMS-02 and NOAA/SWPC data, performs the time-alignment, and outputs a single CSV file containing columns for date, rigidity bin, proton flux, helium flux, heavy flux, and sunspot number. The test passes if the file exists, contains no missing dates in the specified historical range (or explicitly flags gaps), and the row count matches the expected daily resolution.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T009 [P] [US1] Unit test for date alignment logic in `tests/test_data_alignment.py`
- [~] T010 [P] [US1] Unit test for missing data flagging (gaps > 30 days) in `tests/test_data_alignment.py`

### Implementation for User Story 1

- [~] T011 [P] [US1] Implement `code/data/fetch_ams02.py` to download daily averaged, rigidity-binned differential fluxes for protons, helium, and CNO/Fe from the public AMS-02 repository (2011-2024). **Constraint**: Use `requests` with explicit error handling for 404/503. If the public API returns HTML or requires login, implement a fallback to the verified GitHub mirror of AMS-02 public data (e.g., `) or `ucimlrepo` if available, logging the fallback per Assumptions.
- [~] T012 [P] [US1] Implement `code/data/fetch_noaa.py` to download daily sunspot numbers from NOAA/SWPC (e.g., ` or verified CSV mirror).
- [~] T013 [US1] Implement `code/data/align_data.py` to merge flux and solar data, handling time zones and date formats; must flag gaps > 30 days as "Data Gap" and exclude from correlation later.
- [~] T014 [US1] Implement `code/data/preprocess.py` to calculate composition ratios: explicitly calculate **He/p** and **Fe/p** (and CNO/p if available). For any row where the denominator flux (proton) is zero or missing, log the event as "Below Detection Limit" and exclude it from the ratio calculation, as required by FR-003. Ensure the output artifact explicitly lists the calculated ratios for both He/p and Fe/p species.
- [~] T015 [US1] Create `code/main.py` entry point to orchestrate the full data pipeline and output `data/processed/unified_timeseries.csv`
- [~] T016 [US1] Add validation to ensure the unified dataset contains sufficient data coverage. **Logic**: If coverage is < 100% for the 2011-2024 period, do NOT fail. Instead, identify the most populated rigidity bin available for each species, log the fallback action per the spec's Assumptions, and proceed with analysis using that bin. If coverage is < 50% for all bins, log a critical error and exit.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compute Composition Ratios and Correlation with Solar Activity (Priority: P2)

**Goal**: Compute composition ratios and perform time-lagged Pearson/Spearman correlation analyses against sunspot numbers (±12 months lag) per rigidity bin, including a control analysis for absolute fluxes.

**Independent Test**: The system generates a correlation matrix and a set of time-lag plots for both ratios and absolute fluxes. The test passes if the output includes correlation coefficients for lags ranging from negative to positive months for both He/p and Fe/p ratios AND absolute fluxes against sunspot numbers, calculated per rigidity bin, and if the statistical significance (p-value) is calculated for each.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T017 [P] [US2] Unit test for lag calculation logic in `tests/test_correlation.py`
- [~] T018 [P] [US2] Unit test for rigidity-bin specific analysis in `tests/test_correlation.py`

### Implementation for User Story 2

- [~] T019 [P] [US2] Implement `code/analysis/correlation.py` function `calculate_lagged_correlations` supporting Pearson and Spearman methods with a lag window spanning a symmetric range of months (±12).
- [ ] T020 [US2] Implement `code/analysis/correlation.py` to iterate over **all rigidity bins** and perform two distinct correlation sets in a single loop: 1) **Composition Ratios**: Calculate Pearson/Spearman correlations for He/p and Fe/p against sunspot numbers. 2) **Control Analysis**: Calculate correlations for **absolute, rigidity-normalized fluxes** against sunspot numbers. For both sets, compute p-values. After the loop, derive the modulation amplitude trend against rigidity for the absolute flux results and save all results (coefficients, p-values, trends) to `data/processed/correlation_results.json` and `data/processed/correlation_summary.csv`.
- [ ] T021 [US2] **REMOVED**: Merged into T020. The control analysis is now part of the main iteration to ensure consistent per-bin processing and explicit rigidity-dependence validation as required by FR-008.
- [ ] T022 [US2] Implement `code/analysis/visualization.py` to generate time-lag plots and correlation heatmaps. **Dependency**: This task MUST consume the merged results from `data/processed/correlation_results.csv` (output of T020) to ensure both ratio and absolute flux plots are generated correctly.
- [ ] T023 [US2] Save correlation results (coefficients, p-values) to `data/processed/correlation_results.json` and `data/processed/correlation_summary.csv` (Handled in T020, this task serves as a checkpoint for file existence).
- [ ] T024 [US2] Validate that p-values are calculated for all correlations and flag any non-significant results (p > 0.01).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Validate Results via Bootstrap Resampling and Model Fitting (Priority: P3)

**Goal**: Validate statistical robustness via bootstrap resampling (n=1000) and fit a rigidity-dependent diffusion model to modulation amplitudes.

**Independent Test**: The system outputs confidence intervals for the correlation coefficients derived from 1000 bootstrap iterations and generates a fitted curve for the diffusion model. The test passes if the confidence intervals are calculated and the model fitting converges within a practical compute limit.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US3] Unit test for bootstrap resampling logic in `tests/test_bootstrap.py`
- [ ] T026 [P] [US3] Unit test for diffusion model fitting convergence in `tests/test_model_fitting.py`

### Implementation for User Story 3

- [ ] T027 [P] [US3] Implement `code/analysis/bootstrap.py` function `run_bootstrap_resampling` with n=1000 iterations to estimate confidence intervals for max correlation coefficients. **Constraint**: Use `scipy.stats` or `numpy` vectorization to ensure this completes within the time limit on CPU-only runners. Avoid heavy parallelization overhead; use chunked processing if memory is tight.
- [ ] T028 [US3] Implement `code/analysis/model_fitting.py` to derive modulation amplitudes: perform a sinusoidal fit to the time-series for each rigidity bin, calculate the **peak-to-trough difference** explicitly, and save these intermediate values to `data/processed/modulation_amplitudes.csv`. This artifact is required for traceability (Constitution Principle IV) before the model fit.
- [ ] T029 [US3] Implement `code/analysis/model_fitting.py` to fit a rigidity-dependent diffusion model to the amplitudes loaded from `data/processed/modulation_amplitudes.csv` (output of T028) using least-squares optimization (`scipy.optimize.curve_fit`). **Constraint**: The model must be a simplified physics-based parameterization (e.g., `Amplitude = A / (Rigidity + B)`) to ensure convergence without GPU acceleration.
- [ ] T030 [US3] Calculate and report the R² value for the diffusion model fit. **CRITICAL**: Perform an F-test (or equivalent hypothesis test) on the R² value to determine if the model explains a statistically significant portion of the variance (p < 0.05). Save the R² value, F-statistic, and p-value to `data/processed/model_fit_results.json` to satisfy SC-004.
- [ ] T031 [US3] Add error handling to ensure model fitting does not exceed the designated runtime limit on CPU-only runners.
- [ ] T032 [US3] Generate final validation report in `data/processed/validation_report.md` summarizing bootstrap CIs and model fit quality (including the F-test result).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Documentation updates in `docs/` and `README.md`
- [ ] T034 Code cleanup and refactoring for efficiency
- [ ] T035 Performance optimization for bootstrap iterations (vectorization where possible)
- [ ] T036 [P] Run `quickstart.md` validation and ensure all scripts execute without GPU
- [ ] T037 Verify all data gaps > 30 days are correctly excluded from final statistical analysis

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 correlation results

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
Task: "Unit test for date alignment logic in tests/test_data_alignment.py"
Task: "Unit test for missing data flagging (gaps > 30 days) in tests/test_data_alignment.py"

# Launch all models for User Story 1 together:
Task: "Implement fetch_ams02.py"
Task: "Implement fetch_noaa.py"
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
- **Constraint**: All tasks must run on CPU-only CI (no GPU, ≤7GB RAM). No heavy model training or 8-bit quantization.
- **Data Integrity**: No synthetic data generation. All inputs must come from real URLs (AMS-02, NOAA).
- **Rigidity Handling**: Every flux measurement must be tied to a specific rigidity bin. No aggregation across bins before correlation analysis.
- **Gap Handling**: Gaps > 30 days must be flagged and excluded, not interpolated.
