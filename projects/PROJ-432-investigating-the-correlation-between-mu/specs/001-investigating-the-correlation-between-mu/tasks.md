# Tasks: Investigating the Correlation Between Muon Flux and Atmospheric Temperature Profiles

**Input**: Design documents from `/specs/001-muon-temp-correlation/`
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

**Purpose**: Project initialization and basic structure.
**Note on Execution Order**: While marked [P] for parallel safety in terms of file conflicts, the logical execution order is: (1) Directory Structure, (2) Git Init, (3) Venv, (4) Requirements, (5) Lint/Format.

- [ ] T001a [P] Create project directory structure (`src/`, `tests/`, `data/raw/`, `data/processed/`, `data/results/`, `logs/`, `config/`) per implementation plan
- [ ] T001b [P] Initialize git repository and create `.gitignore` for Python/Project data artifacts
- [ ] T002a [P] Create Python 3.11 virtual environment and activate script
- [ ] T002b [P] Generate `requirements.txt` with pinned versions (pandas, numpy, scipy, scikit-learn, statsmodels, requests, h5py, pyyaml, cdsapi)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create `src/data/utils.py` with logging, checksum, and date-parsing utilities
- [~] T005 [P] Create `src/config/constants.yaml` defining T_eff weighting parameters (Grieder 1985), thresholds, and interpolation settings
- [~] T006 [P] Create `src/data/ingest.py` implementing full download logic for IceCube (via URL/API) and ERA5 (via `cdsapi`), caching to `data/raw/`, with checksum validation **AND explicit capture of the 'original release identifier' from the source portal in the artifact metadata** to satisfy Constitution Data Hygiene requirements.
- [~] T007 [P] Setup `tests/unit/` and `tests/integration/` directory structure
- [~] T008 [P] Configure `pytest` and `conftest.py` for CPU-only execution environment

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion, Preprocessing & Alignment (Priority: P1) 🎯 MVP

**Goal**: Ingest IceCube muon flux and ERA5 atmospheric data, calculate T_eff, align to daily bins, and verify completeness.

**Independent Test**: Run ingestion script on a 1-week sample; verify output CSV has matching dates, non-null counts, non-null temperatures, and valid T_eff values.

### Implementation for User Story 1

- [~] T009 [US1] Implement `src/data/ingest.py` to download IceCube muon flux (via `icecube_daily_counts` or direct URL fetch) and cache to `data/raw/icecube.csv`
- [~] T010 [US1] Implement `src/data/ingest.py` to fetch ERA5 data (via `cdsapi` or HuggingFace mirror) for pressure levels 1000hPa-10hPa and cache to `data/raw/era5.csv`
- [~] T011 [US1] Implement data validation in `src/data/ingest.py` to check for `date` column, non-negative counts, and valid pressure/temperature ranges
- [~] T012 [US1] Implement temporal alignment logic in `src/data/ingest.py`: resample muon counts to daily sums, average temperature metrics, and drop dates with missing data in either source
- [~] T013 [US1] Implement logging of exclusion events to `logs/alignment.json` (JSON format) with **explicit format**: a list of objects `{ "date": "YYYY-MM-DD", "reason": "missing_era5|icecube_maintenance|other", "source": "icecube|era5" }` to satisfy FR-007 transparency requirements for **all** data exclusion events, including non-contiguous gaps and specific reasons per date.
- [~] T017 [US1] Implement `calculate_t_eff(df: pd.DataFrame) -> pd.Series` in `src/data/preprocess.py` using Grieder (1985) weight function; **include linear interpolation for missing pressure levels** as per spec assumptions; save results to `data/processed/t_eff_values.csv`
- [ ] T014b [US1] Generate final `data/processed/aligned_daily.csv` by **merging the output of T012 (aligned daily data) with `t_eff_values.csv` (from T017)**, ensuring `t_eff_value` is populated; verify that the output contains non-null temperature metrics to satisfy US1 Independent Test; **Depends on T012 and T017**
- [ ] T015 [P] [US1] Unit test for alignment logic in `tests/unit/test_ingest.py` (verify date matching and gap handling)
- [ ] T016 [P] [US1] Integration test for end-to-end ingestion in `tests/integration/test_ingest_flow.py` (verify sample subset output)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently with complete T_eff data

---

## Phase 4: User Story 2 - Statistical Correlation and Regression Analysis (Priority: P2)

**Goal**: Compute Pearson/Spearman correlations and fit linear regression (OLS) with confidence intervals using Effective Temperature on pre-whitened data.

**Independent Test**: Run analysis on aligned dataset; verify output includes r-values, p-values, slope, intercept, and R-squared.

### Implementation for User Story 2

- [ ] T019 [US2] Implement `src/analysis/correlation.py` to compute Pearson and Spearman correlation coefficients between `muon_count` and `t_eff_value`
- [ ] T020 [US2] Implement pre-whitening (AR(1) model fit) on `muon_count` and `t_eff_value` to generate residuals; **save residuals to `data/processed/residuals.csv`** to satisfy time-series requirements for FR-004; **justification**: This step addresses time-series autocorrelation inherent in temporal data, ensuring that the 'associational' correlations calculated in subsequent steps are statistically valid and not artifacts of serial dependence, consistent with standard practice for time-series analysis even when randomization is absent.
- [ ] T021 [US2] Implement OLS linear regression on `residuals.csv` using `statsmodels` with **Newey-West standard errors** to calculate slope/intercept confidence intervals; **explicitly document** that Newey-West SEs are used to mitigate autocorrelation and heteroscedasticity in the time-series residuals, ensuring robust temperature coefficient quantification as required by FR-004.
- [ ] T022 [US2] Implement logic to flag statistical significance (p < 0.01) and handle exact p=0.05 edge cases as specified
- [ ] T023 [P] [US2] Unit test for T_eff calculation in `tests/unit/test_preprocess.py` (verify weighted integral logic and interpolation)
- [ ] T024 [P] [US2] Unit test for correlation/regression in `tests/unit/test_analysis.py` (verify r-values, p-values, and CI calculation)
- [ ] T025 [US2] Generate `data/results/correlation_results.json` containing r-values, p-values, slope, intercept, and R-squared from the OLS model

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis and Seasonal Stratification (Priority: P3)

**Goal**: Validate robustness via parameter sweeps and seasonal comparison (Summer vs. Winter).

**Independent Test**: Run sensitivity/stratification scripts; verify output tables show variation in coefficients across seasons and parameters.

### Implementation for User Story 3

- [ ] T026 [US3] Implement `src/analysis/stratify.py` to split data into Summer (Jun-Aug) and Winter (Dec-Feb) subsets
- [ ] T027 [US3] Implement power check in `src/analysis/stratify.py`: skip Fisher's r-to-z test if subset size < 30, report "Insufficient Data"
- [ ] T028 [US3] Implement seasonal correlation/regression in `src/analysis/stratify.py` to compute separate metrics for each season; **consume `data/processed/residuals.csv` and `data/results/correlation_results.json`** for baseline context
- [ ] T029 [US3] Implement Fisher's r-to-z transformation in `src/analysis/stratify.py` to test significance of difference between Summer/Winter correlations; **consume `data/results/correlation_results.json`**
- [ ] T030 [US3] Implement `src/analysis/sensitivity.py` to sweep T_eff weighting function parameters (e.g., $z_{peak}$, $\sigma$) by **calling `calculate_t_eff()` from `src/data/preprocess.py`** with modified parameters; **DO NOT re-implement logic**
- [ ] T031 [US3] Implement sensitivity comparison logic to report correlation coefficient and slope variations across parameter sets
- [ ] T032 [US3] Implement outlier detection (>3$\sigma$) and re-run analysis to compare filtered vs. unfiltered results
- [ ] T036 [US3] **Implement ANOVA test** (scipy.stats.f_oneway) on the slope values generated from the sensitivity sweep (T030/T031) to confirm no significant difference (p > 0.05) as required by SC-002; **include fallback logic**: if fewer than 3 parameter sets are generated, skip ANOVA and log "Insufficient Parameter Sets" to `data/results/anova_results.json`; save results to `data/results/anova_results.json`
- [ ] T033 [P] [US3] Unit test for seasonal stratification in `tests/unit/test_stratify.py`
- [ ] T034 [P] [US3] Unit test for sensitivity analysis in `tests/unit/test_sensitivity.py`
- [ ] T035 [US3] Generate `data/results/sensitivity_results.csv` and `data/results/seasonal_results.json`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Generate final summary report in `data/results/summary.json` aggregating all metrics
- [ ] T038 [P] Validate all outputs against `contracts/analysis_output.schema.yaml`
- [ ] T039 Run end-to-end reproducibility test with fixed random seed
- [ ] T040 Update `README.md` with execution instructions and expected outputs
- [ ] T041 Run quickstart.md validation

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires aligned data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires correlation results from US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utilities before Services/Logic
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (subject to logical order: Dir -> Git -> Venv -> Req -> Lint)
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for alignment logic in tests/unit/test_ingest.py"
Task: "Integration test for end-to-end ingestion in tests/integration/test_ingest_flow.py"

# Launch all models for User Story 1 together:
Task: "Implement data validation in src/data/ingest.py"
Task: "Implement temporal alignment logic in src/data/ingest.py"
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

- [P] tasks = different files, no dependencies (subject to logical execution order in Phase 1)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence