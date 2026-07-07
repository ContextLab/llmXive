# Tasks: Characterization of Exoplanetary Atmospheres through Advanced Spectroscopic Techniques

**Input**: Design documents from `/specs/001-characterization-of-exoplanetary-atmosph/`
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

- [X] T001a [P] Create project directory structure: `projects/PROJ-554-characterization-of-exoplanetary-atmosph/`, `code/`, `data/`, `tests/`, `results/`
- [X] T001b [P] Initialize `requirements.txt` with pinned versions: `petitRADTRANS`, `astropy`, `statsmodels`, `scipy`, `pandas`, `numpy`, `requests`, `tqdm`, `lifelines`, `synphot`, `scikit-survival`
- [X] T001c [P] Configure linting (ruff) and formatting (black) tools by creating `.ruff.toml` and `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Setup `code/config.py` for configuration loading (paths, seeds, CPU thread limits)
- [X] T005a [P] Implement logging setup in `code/utils.py` (logging configuration, log levels)
- [X] T005b [P] Implement error handling wrapper in `code/utils.py` (custom exceptions, retry logic)
- [X] T005c [P] Implement censored data helpers in `code/utils.py` (upper limit handling functions)
- [X] T006a [P] Create data directories: `data/raw/`, `data/processed/`; verify existence
- [X] T006b [P] Create code and test directories: `code/`, `tests/unit/`, `tests/contract/`, `tests/integration/`; verify existence
- [ ] T007 [P] Create base data models in `code/data_models.py` (Exoplanet Spectrum, Retrieval Result)
- [ ] T008 [P] Configure environment variable handling for API keys (if needed) and random seeds

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Pre-processing (Priority: P1) 🎯 MVP

**Goal**: Download publicly available transmission spectra from NASA Exoplanet Archive for hot Jupiters and super-Earths, extracting metadata (temperature, metallicity, SNR, Resolution) and ensuring sample size targets (sufficient for statistical power) are met without halting if counts differ.

**Independent Test**: The system can be tested by verifying that the output directory contains a metadata CSV with non-null values for temperature, metallicity, SNR, Resolution, and planet category, and that the total count of unique planets falls within a moderate range (or logs a warning if outside).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [US1] Contract test for metadata schema in `tests/contract/test_metadata_schema.py` implementing `validate_metadata_schema` function. **Depends on T011b**.
- [ ] T010 [US1] Integration test for API download in `tests/integration/test_download.py` implementing `test_download_returns_valid_metadata` with specific mock parameters. **Depends on T011b**.

### Implementation for User Story 1

- [X] T011a [P] [US1] Create `code/api_config.py` defining `QUERY_PARAMS` dictionary for NASA Exoplanet Archive API (Hot Jupiters and Super-Earths filters)
- [~] T011b [P] [US1] Implement `code/download.py` fetch logic to retrieve spectrum files and raw metadata using `QUERY_PARAMS`
- [~] T011c [P] [US1] Implement parsing logic in `code/download.py` to extract equilibrium temperature (K), host star metallicity ([Fe/H]), spectral resolution (R), and signal-to-noise ratio (SNR)
- [~] T012 [US1] Save raw spectrum files to `data/raw/` and metadata CSV (including SNR, R) to `data/processed/metadata.csv`
- [~] T013 [US1] Implement `validate_sample_size` in `code/download.py` to count unique planets. If count < 30 or > 45, log `logging.warning` but proceed (do not raise error) to satisfy FR-001 "download ALL". If count is absent or null, raise `RuntimeError`.
- [~] T014 [US1] Add logging for download progress and API response handling

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Atmospheric Retrieval and Water Abundance Derivation (Priority: P2)

**Goal**: Run `petitRADTRANS` in CPU-optimized mode on each spectrum to derive water vapor mixing ratios with uncertainty estimates, handling low S/N data as censored upper limits using SNR/Resolution metadata.

**Independent Test**: The system can be tested by running the retrieval on a single, known test spectrum and verifying that the output includes a water vapor mixing ratio value (or an upper limit flag) and a 1-sigma uncertainty interval.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T016 [P] [US2] Contract test for retrieval output schema in `tests/contract/test_retrieval_schema.py`
- [~] T017 [P] [US2] Integration test for retrieval on sample spectrum in `tests/integration/test_retrieval.py`

### Implementation for User Story 2

- [~] T018a [P] [US2] Configure `petitRADTRANS` for CPU-optimized mode (single-threaded, memory limit GB) in `code/retrieval.py`
- [~] T018b [P] [US2] Implement wrapper function in `code/retrieval.py` to run retrieval on a single spectrum file
- [~] T018c [P] [US2] Define output schema mapping: log10 water mixing ratio, standard deviation, or upper limit flag
- [~] T019 [US2] Implement logic to detect low S/N spectra using SNR/Resolution metadata and derive upper limits (censored values) instead of false precision
- [~] T020 [US2] Implement output generation: save results to `data/processed/retrieval_results.csv`
- [~] T021 [US2] Add error handling for non-convergent retrievals: log failure, attempt upper limit derivation, proceed without halting
- [~] T022 [US2] Implement `test_upper_limit_flags_reflect_noise` in `code/validation.py` to verify upper limit flags reflect physical noise floors. **Depends on T019**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Correlation and Regression Analysis (Priority: P3)

**Goal**: Compute Kendall's tau correlation for censored data (including upper limits), perform bootstrap resampling, and fit Tobit regression controlling for mass and metallicity.

**Independent Test**: The system can be tested by running the analysis on a mock dataset with known censored values and verifying that the calculated Kendall's tau matches the expected value within the bootstrap confidence interval.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T023 [P] [US3] Contract test for analysis output schema in `tests/contract/test_analysis_schema.py`
- [~] T024 [P] [US3] Integration test for correlation and regression on mock data in `tests/integration/test_analysis.py`

### Implementation for User Story 3

- [~] T025a [P] [US3] Import `scikit-survival` in `code/analysis.py` and verify import availability
- [~] T025b [US3] Implement `compute_censored_kendall_tau` in `code/analysis.py` using `scikit-survival`'s `kendall_tau` function for censored data (Hot Jupiters vs Super-Earths). **Note**: This supersedes the "Akritas-Theil-Sen" mention in plan.md Complexity Tracking; plan.md must be updated to reflect Kendall's tau as the primary estimator for FR-003.
- [~] T025c [US3] Implement a bootstrap resampling loop to estimate confidence intervals
- [~] T026 [US3] Compute and report the % CI width of the water mixing ratio distribution as a measure of robustness per SC-003
- [~] T027 [US3] Implement Tobit regression model (using `lifelines` or `statsmodels`) with water abundance as dependent variable and temperature, mass, metallicity as predictors. **Depends on T020**.
- [~] T028 [US3] Implement fallback to Tobit regression with L2 (Ridge) regularization if VIF > 5 to handle collinearity while maintaining censored-data validity. **Note**: Do NOT use L1 (Lasso) or Elastic Net; only L2 is authorized by plan.md.
- [~] T029 [US3] Implement diagnostic plot generation (water abundance vs. temperature with error bars/limits, residuals, correlation matrix) to `results/plots/`
- [~] T030 [US3] Output final statistics: Kendall's tau, p-values, CI width, model fit statistics to `data/processed/analysis_results.json`
- [~] T031 [US3] Implement `calculate_statistical_power` in `code/analysis.py` using the **actual** sample size (N) from `metadata.csv` and observed effect size (or conservative estimate) to verify power ≥ 0.8 per SC-004. Generate `results/quality_report.md` with resolved vs. upper limits count and power verification.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Revision & Review Response (Addressing Prior Research-Stage Reviews)

**Goal**: Address specific concerns raised by Marie Curie and Rosalind Franklin simulated reviewers regarding spectral resolution, signal-to-noise ratios, detection limits, and evidentiary standards.

### Implementation for Review Responses

- [~] T032 [US3] **Review Response**: Implement `compute_correlation_uncertainty` in `code/analysis.py` to calculate standard error of the slope and CI width per FR-003/SC-003.
- [~] T033 [US3] **Review Response**: Implement `quality_control_filter` in `code/analysis.py` to flag low SNR spectra and include them as censored values per FR-002. <!-- SKIPPED: YAML+regex parse failed (while scanning an alias
 in "<unicode string>", line 3, column 1:
 **Task**: T033 - Implement `qual...
 ^
expected alphabetic or numeric character, but found '*'
 in "<unicode string>", line 3, column 2:
 **Task**: T033 - Implement `quali...
 ^) -->
- [~] T034 [US1] **Review Response**: Enhance `code/download.py` to log and store spectral resolution (R) and SNR for every spectrum per FR-001.
- [~] T035 [US3] **Review Response**: Implement `calculate_detection_limit` in `code/analysis.py` taking SNR and Resolution as inputs, outputting to `data/processed/detection_limits.csv` per FR-002.
- [~] T036 [US3] **Review Response**: Generate "Instrumental Noise vs. Signal" plot in `results/plots/` visualizing SNR distribution and threshold per SC-003.
- [~] T037 [US3] **Review Response**: Implement `run_loo_correlation_check` in `code/analysis.py` to calculate `max_correlation_drift` metric per SC-004.

**Checkpoint**: All review responses implemented and verified

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T038 [P] Documentation updates in `README.md` and `quickstart.md`
- [~] T039 Code cleanup and refactoring
- [~] T040 Performance optimization across all stories (ensure pipeline runs < 6 hours) <!-- ATOMIZE: requested -->
- [~] T041 [P] Additional unit tests (if requested) in `tests/unit/`
- [~] T042 Run quickstart.md validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Revision (Phase 6)**: Depends on completion of US1-US3 to generate initial results for review response

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires data from US1 (T012)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires data from US1 (T012) and US2 (T020)
- **Revision (Phase 6)**: Requires results from US1, US2, and US3 to address reviewer concerns

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
- All tests for a user story marked [P] can run in parallel **EXCEPT** T009 and T010, which depend on T011b and are NOT parallel-safe with implementation.
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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
- **CPU Constraint**: All tasks must run on a limited number of CPU cores, constrained memory, and no GPU.. `petitRADTRANS` must be configured for single-threaded execution.
- **Data Integrity**: All data must be fetched programmatically; no static data commits.
- **Censored Data**: All statistical methods must handle upper limits correctly (Kendall's tau via scikit-survival, Tobit).
- **Constraint Preservation**: Do not exclude censored data; always derive upper limits. Do not use OLS-based Ridge for censored outcomes; use Tobit with L2 if fallback needed.
- **Review Compliance**: All tasks in Phase 6 directly address the specific quantitative and evidentiary standards raised by Marie Curie and Rosalind Franklin simulated reviewers regarding spectral resolution, SNR, and detection limits.