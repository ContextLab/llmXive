# Tasks: Assessing Orbital Period Dependence of the Exoplanet Radius Gap

**Input**: Design documents from `/specs/001-assessing-orbital-period-dependence/`
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

- [ ] T001a [P] Create `code/`, `data/raw/`, `data/processed/` directories per implementation plan structure
- [ ] T001b [P] Create `tests/contract/`, `tests/unit/`, `paper/`, `code/ingest/`, `code/analysis/`, `code/theory/`, `code/validation/`, `code/utils/`, `code/models/` directories per implementation plan structure

- [ ] T002a [P] Create `code/requirements.txt` with dependencies (`pandas`, `numpy`, `scipy`, `scikit-learn`, `astropy`, `astroquery`, `pyyaml`, `pytest`, `tqdm`)
- [ ] T002b [P] Install dependencies from `code/requirements.txt` in a virtual environment
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement data models `code/models/planet_record.py` and `code/models/gap_result.py` matching `contracts/planet_record.schema.yaml` and `contracts/analysis_output.schema.yaml`
- [ ] T005 [P] Setup directory structure for `data/raw/` and `data/processed/` with checksum verification utilities
- [ ] T006 [P] Implement logging infrastructure and configuration management in `code/utils/`
- [ ] T007 Create contract test suite `tests/contract/test_schemas.py` to validate data integrity against YAML schemas
- [ ] T008 Implement retry logic with exponential backoff (max 3 attempts) for external API calls in `code/utils/retry.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Pre-processing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Produce a clean, filtered CSV of confirmed Kepler exoplanets with precise radius and period measurements, excluding entries with missing critical stellar parameters.

**Independent Test**: The pipeline can be fully tested by executing the data download and filtering scripts on a subset of the Kepler DR25 catalog and verifying that the output CSV contains only planets meeting the strict uncertainty criteria (radius <20%, period <1%) with no missing critical columns.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Contract test for data ingestion output schema in `tests/contract/test_ingestion_schema.py`
- [ ] T011 [P] [US1] Unit test for duplicate resolution logic (keeping lowest radius uncertainty) in `tests/unit/test_preprocess.py`

### Implementation for User Story 1

- [ ] T012a [P] [US1] Implement `code/ingest/download_dr25.py` to fetch the Kepler DR25 Planet Table (MAST Product ID: `kplr_dr25_planet`) via `astroquery.mast` with retry logic, saving to `data/raw/dr25_raw.csv` (FR-001, Assumptions: Data Availability)
- [ ] T012b [P] [US1] Wire `code/utils/retry.py` into `code/ingest/download_dr25.py` to ensure exponential backoff is applied for the Kepler DR25 download (Edge Case: API Unavailability)
- [ ] T012c [P] [US1] Implement `code/ingest/download_kic.py` to fetch the Kepler Input Catalog (KIC) via `astroquery.mast` with retry logic, saving to `data/raw/kic_raw.csv` (FR-001, Assumptions: Data Availability)
- [ ] T012d [P] [US1] Wire `code/utils/retry.py` into `code/ingest/download_kic.py` to ensure exponential backoff is applied for the KIC download (Edge Case: API Unavailability)
- [ ] T013 [P] [US1] Implement `code/ingest/merge_catalogs.py` to merge Kepler DR25 (from T012a) and KIC (from T012c) on KIC ID to produce a unified DataFrame containing stellar parameters (FR-001, Ordering: Catalog Merge)
- [ ] T014 [P] [US1] Implement `code/ingest/preprocess.py` to parse merged catalogs, filter for radius uncertainty <20% and period uncertainty <1% (FR-002), and exclude entries with missing stellar effective temperature
- [ ] T015 [US1] Implement duplicate resolution logic in `code/ingest/preprocess.py` to keep the entry with the lowest radius uncertainty and log removed duplicates (Edge Case: duplicates)
- [ ] T016 [US1] Create `code/ingest/loaders.py` to load the filtered dataset into a unified DataFrame for downstream analysis, explicitly verifying the checksum of `data/processed/filtered_planets.csv` before loading to ensure data integrity (FR-001, Constitution Principle III)
- [ ] T017 [US1] Add validation and error handling to ensure no fabricated data or placeholder values are used (Real data requirement)
- [ ] T018 [US1] Add logging for ingestion steps, including counts of excluded planets and reasons

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Gap Location Estimation via Gaussian Mixture Modeling (Priority: P2)

**Goal**: Identify the precise location of the radius gap within specific orbital period bins using a two-component Gaussian Mixture Model (GMM) and quantify uncertainty via bootstrap resampling, adhering to CPU-only constraints.

**Independent Test**: The GMM fitting logic can be independently tested by running it against a synthetic dataset with a known bimodal distribution and a known gap location, verifying that the algorithm correctly identifies the valley between peaks within a defined tolerance.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Contract test for period bin output schema in `tests/contract/test_binning_schema.py`
- [ ] T020 [P] [US2] Unit test for GMM fitting on synthetic bimodal data in `tests/unit/test_gmm.py`

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement `code/analysis/binning.py` to bin filtered planets by orbital period using log-spaced bins (0.7 to 2.0 log(days)) and merge bins with <30 planets with adjacent bins (FR-003, US-2)
- [ ] T022 [US2] Implement `code/analysis/gmm_fitter.py` to fit a two-component Gaussian Mixture Model using K-Means++ initialization with multiple random seeds, selecting the model with the lowest BIC (FR-004)
- [ ] T023 [US2] Implement outlier handling in `code/analysis/gmm_fitter.py` to flag/exclude points >3 standard deviations from the bin's radius distribution before fitting (Edge Case: outliers)
- [ ] T024 [US2] Implement bootstrap resampling (1000 iterations) in `code/analysis/gmm_fitter.py` to estimate the 95% confidence interval for the gap location (FR-005)
- [ ] T025 [US2] Implement graceful failure handling in `code/analysis/gmm_fitter.py` for unimodal distributions (BIC diff < 10), flagging bins as "unresolved" rather than forcing a fit (Edge Case: unimodal)
- [ ] T026 [US2] Implement `code/analysis/kde_sensitivity.py` to perform sensitivity analysis using KDE with adaptive bandwidth on the cumulative distribution of radii to verify GMM results are not parametric artifacts (FR-009, SC-006, Constitution Principle VI)
- [ ] T027 [US2] Implement calculation of 'weighted mean period' using inverse variance of the gap location estimate (from T024) for each bin, outputting to `data/processed/binned_stats.csv` (FR-003, Ordering: Gap Variance Flow)
- [ ] T028 [US2] Integrate binning and GMM logic to produce `data/processed/gap_locations.csv` containing bin centers, weighted mean periods, gap locations, and uncertainties
- [ ] T029 [US2] Implement KDE validation in `code/analysis/kde_validator.py` to identify the gap location without parametric assumptions, verify it falls within the GMM 95% CI, and output `data/processed/kde_validation.json` with a boolean `validation_passed` flag (FR-008, SC-003)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Slope Calculation and Theory Comparison (Priority: P3)

**Goal**: Determine the scaling relationship (slope) between gap location and orbital period, and compare it against photoevaporation and core-powered mass loss theories using a z-test on Monte Carlo generated theoretical distributions.

**Independent Test**: The regression and comparison logic can be independently tested by feeding it a mock dataset of gap locations with known slopes and verifying that the z-test correctly identifies consistency or inconsistency with the theoretical distributions.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US3] Contract test for final results schema in `tests/contract/test_results_schema.py`
- [ ] T031 [P] [US3] Unit test for weighted linear regression and z-test logic in `tests/unit/test_regression.py`

### Implementation for User Story 3

- [ ] T032 [P] [US3] Implement `code/analysis/regression.py` to perform weighted linear regression of gap radius vs. log(period) using weighted mean periods (from T027) (FR-006)
- [ ] T033 [US3] Implement `code/theory/scaling_laws.py` to define the Owen & Wu (photoevaporation) and Ginzburg et al. (2018) (core-powered) scaling law equations, and `code/theory/simulate_theory.py` to generate theoretical slope distributions via Monte Carlo propagation of stellar parameter uncertainties through these equations (FR-007)
- [ ] T034 [US3] Implement `code/theory/theory_comparison.py` to perform a z-test comparing the measured slope against the predicted theoretical distributions, calculating p-values and applying Bonferroni correction for multiple comparisons (FR-007)
- [ ] T035 [US3] Implement sensitivity analysis in `code/analysis/sensitivity_analysis.py` to perform a grid search over planet count thresholds (25-35) AND radius uncertainty thresholds (15-25%), outputting results to `data/processed/sensitivity_analysis.csv` and verifying stability via slope variance (Assumption: threshold justification)
- [ ] T036 [US3] Generate `paper/results.md` by aggregating p-values from T034, the slope from T032, and the KDE vs. GMM gap location comparison result from `data/processed/kde_validation.json`, explicitly writing a statement of which theory is favored based on statistical consistency (SC-001, SC-003, Ordering: Results Aggregation)
- [ ] T037 [US3] Add runtime measurement and logging to ensure total pipeline execution remains ≤ 6 hours on CPU-only runners (SC-005)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Update `quickstart.md` with specific instructions for the new KIC/DR25 download and merge steps
- [ ] T039 [P] Update `README.md` with project overview and execution instructions
- [ ] T040 Code cleanup and refactoring for readability
- [ ] T041 Performance optimization (vectorization) across all analysis scripts to meet CPU constraints
- [ ] T042 [P] Additional unit tests for edge cases in `tests/unit/`
- [ ] T043 Run `quickstart.md` validation to ensure reproducibility

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 gap location output

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