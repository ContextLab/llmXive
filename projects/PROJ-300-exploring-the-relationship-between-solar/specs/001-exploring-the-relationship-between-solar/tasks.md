# Tasks: Exploring the Relationship Between Solar Wind Speed and Geomagnetic Tail Reconnection Rates

**Input**: Design documents from `/specs/PROJ-300-01-solar-wire-reconnection/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are REQUIRED to satisfy the Independent Tests in US-1 and US-2.

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

- [X] T001 Create project structure per implementation plan (`projects/PROJ-300-exploring-the-relationship-between-solar/`) by executing the following commands.
 **Target Structure**: The final directory tree must match:
 ```
 projects/PROJ-300-exploring-the-relationship-between-solar/
 ├── code/
 │ ├── __init__.py
 │ ├── config.py
 │ ├── data/
 │ │ ├── __init__.py
 │ │ ├── ingest.py
 │ │ ├── clean.py
 │ │ └── lag.py
 │ ├── analysis/
 │ │ ├── __init__.py
 │ │ ├── correlation.py
 │ │ ├── lag_search.py
 │ │ └── sensitivity.py
 │ ├── viz/
 │ │ ├── __init__.py
 │ │ └── plots.py
 │ └── main.py
 ├── data/
 │ ├── raw/
 │ └── processed/
 ├── tests/
 │ ├── unit/
 │ └── integration/
 ├── requirements.txt
 └── README.md
 ```
 **Execution**: Run the following commands to create the directory skeleton and empty `__init__.py` files. Note: The source code files (e.g., `config.py`, `ingest.py`) must be created in subsequent tasks (T003-T019).
 ```bash
 mkdir -p projects/PROJ-300-exploring-the-relationship-between-solar/{code/{data,analysis,viz},data/{raw,processed},tests/{unit,integration}}
 touch projects/PROJ-300-exploring-the-relationship-between-solar/code/__init__.py
 touch projects/PROJ-300-exploring-the-relationship-between-solar/code/data/__init__.py
 touch projects/PROJ-300-exploring-the-relationship-between-solar/code/analysis/__init__.py
 touch projects/PROJ-300-exploring-the-relationship-between-solar/code/viz/__init__.py
 touch projects/PROJ-300-exploring-the-relationship-between-solar/tests/__init__.py
 ```

- [X] T002 Initialize Python 3.11 project with `requirements.txt` at `projects/PROJ-300-exploring-the-relationship-between-solar/requirements.txt` containing the following exact pinned versions:
 ```
 pandas==2.0.3
 numpy==1.24.3
 scipy==1.11.1
 matplotlib==3.7.2
 requests==2.31.0
 tqdm==4.65.0
 pyyaml==6.0.1
 cdaweb==0.4.0
 pytest==7.4.0
 ```

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 [P] Create `projects/PROJ-300-exploring-the-relationship-between-solar/code/config.py` defining constants: `LAG_WINDOW_MIN=30 [UNRESOLVED-CLAIM: c_dfb15390 — status=not_enough_info] `, `LAG_WINDOW_MAX=90 [UNRESOLVED-CLAIM: c_36fbb06b — status=not_enough_info] `, `LAG_STEP=5 [UNRESOLVED-CLAIM: c_174d0e4f — status=not_enough_info] `, `{{claim:c_c7fa9e4a}} (Wikipedia: Earth radius, https://en.wikipedia.org/wiki/Earth_radius)`, `TAIL_DISTANCE_RE=60 [UNRESOLVED-CLAIM: c_ab3c7670 — status=not_enough_info] `, `BOOTSTRAP_ITERATIONS=1000 [UNRESOLVED-CLAIM: c_48f0ca5f — status=not_enough_info] `, `PERMUTATION_ITERATIONS=10000 [UNRESOLVED-CLAIM: c_809d3da7 — status=not_enough_info] `. The file path must be explicitly stated in the docstring.
- [X] T004a [P] Implement `projects/PROJ-300-exploring-the-relationship-between-solar/code/data/ingest.py` function `fetch_omni_sw(date_range)` to fetch solar wind data (Vsw, Bz) from NASA OMNIWeb API v2 via `requests` (FR-001).
 - **Deliverable**: Function returning a `pandas.DataFrame` with columns `[timestamp, Vsw, Bz]`.
 - **Verification**: Run a unit test to verify the function returns a DataFrame with the correct columns for a 1-day range.
- [X] T004b [P] Implement `projects/PROJ-300-exploring-the-relationship-between-solar/code/data/ingest.py` function `fetch_themis_ey(date_range)` to fetch THEMIS data (Ey) from NASA CDAWeb via `cdaweb` (FR-002).
 - **Deliverable**: Function returning a `pandas.DataFrame` with columns `[timestamp, Ey]`.
 - **Verification**: Run a unit test to verify the function returns a DataFrame with the correct columns for a 1-day range.
- [X] T005 [P] Implement `projects/PROJ-300-exploring-the-relationship-between-solar/code/data/clean.py` for NaN removal and resampling to a fixed short-interval cadence using pandas (FR-003).
 - **Deliverable**: Function `clean_and_resample(df1, df2)` returning aligned DataFrames.
- [X] T006 [P] Implement `projects/PROJ-300-exploring-the-relationship-between-solar/code/data/lag.py` to calculate physics-based lag `L_phys` using formula `L_phys = (k * 6371) / Vsw_mean / k

The specific value to remove/generalize: 'k'

Rewritten passage:
L_phys = (k * 6371) / Vsw_mean / k ` (FR-012) and apply lag shifts to time series.
 - **Verification**: Ensure the code correctly handles the unit conversion (km/s to minutes) and includes the 60 factor.
- [X] T007 [P] Implement `projects/PROJ-300-exploring-the-relationship-between-solar/code/analysis/correlation.py` function `calculate_correlation` for Pearson/Spearman calculation (used by FR-005/FR-006).
- [X] T008 [P] Implement `projects/PROJ-300-exploring-the-relationship-between-solar/code/analysis/correlation.py` function `circular_block_permutation` with iterations for empirical p-values (FR-005).
 - **Block Size**: Calculate block size based on the first lag where autocorrelation < 0.5, or use a default of a sufficient number of samples if autocorrelation is weak.
- [X] T009 [P] Implement `projects/PROJ-300-exploring-the-relationship-between-solar/code/analysis/correlation.py` function `moving_block_bootstrap` with A sufficient number of iterations for 95% confidence intervals (FR-006).
 - **Block Size**: Use the same block size logic as T008 to preserve temporal dependence.
- [X] T010 [P] Implement `projects/PROJ-300-exploring-the-relationship-between-solar/code/analysis/lag_search.py` function `find_optimal_lag` to sweep the early-to-mid duration window and identify optimal lag `L*` (FR-010).
- [X] T011 [P] Implement `projects/PROJ-300-exploring-the-relationship-between-solar/code/analysis/sensitivity.py` function `analyze_thresholds` to sweep thresholds T ∈ {high, medium, low} km/s and recompute correlations (FR-007).
- [X] T012 [P] Implement `projects/PROJ-300-exploring-the-relationship-between-solar/code/viz/plots.py` function `plot_scatter` to generate scatter plot of lag-adjusted Vsw vs. Ey with regression line (FR-008a).
- [X] T013 [P] Implement `projects/PROJ-300-exploring-the-relationship-between-solar/code/viz/plots.py` function `plot_timeseries` to generate dual-axis time-series overlay of Vsw and Ey (FR-008b).
- [X] T014 [P] Add docstring to `projects/PROJ-300-exploring-the-relationship-between-solar/code/analysis/lag_search.py` documenting the multiple-comparison correction method (permutation test) and total lag candidate count (FR-011).
- [X] T015 [P] Implement `projects/PROJ-300-exploring-the-relationship-between-solar/code/main.py` to insert the FR-013 narrative note into the "notes" field of the JSON report **only if** the permutation test (FR-005) was successfully executed. The exact string must be: "Note: Bonferroni correction is conservative for autocorrelated lag searches; the permutation test (FR-005) is the primary method for significance testing. Future work should consider adaptive FDR control." (FR-013).
- [X] T016 [P] Implement `projects/PROJ-300-exploring-the-relationship-between-solar/code/main.py` to log data-quality warnings to `projects/PROJ-300-exploring-the-relationship-between-solar/data/processed/quality_log.json` in JSON format (FR-009).
- [X] T017 [P] Implement logic in `projects/PROJ-300-exploring-the-relationship-between-solar/code/main.py` to calculate and report `|L* - L_phys|` (SC-002) using the optimal lag L* from FR-010 and L_phys from FR-012.
- [X] T018 [P] Implement logic in `projects/PROJ-300-exploring-the-relationship-between-solar/code/main.py` to generate sensitivity table and append to JSON report (SC-003).
- [X] T019 [P] Ensure all plots in `projects/PROJ-300-exploring-the-relationship-between-solar/code/viz/plots.py` include correct axis labels, units, and optimal lag annotation (SC-005).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Quantify Lag‑Adjusted Coupling (Priority: P1) 🎯 MVP

**Goal**: Compute correlation between solar-wind speed (Vsw) and tail-reconnection proxy (Ey) after applying propagation lag, including permutation tests for significance.

**Independent Test**: Run the analysis pipeline on a multi-day interval and verify output includes Pearson/Spearman coefficients, p-values, and significance flags.

### Implementation for User Story 1

- [X] T020 [US1] Integrate `data/clean.py`, `data/lag.py`, and `analysis/correlation.py` into a cohesive pipeline for US-1 in `main.py`.
 - **Deliverable**: `results/us1_correlation.json` containing keys: `pearson`, `spearman`, `p_val_permutation`, `significant_flag`.
- [X] T021 [US1] Execute the pipeline on a sample date range to verify output includes numeric correlation coefficients and empirical p-values (US-1 Acceptance Scenario 1).
 - **Verification**: Run `pytest tests/integration/test_us1.py`.
- [X] T022 [US1] Verify pipeline handles NaN gaps by cleaning, resampling, and producing correlation output without error (US-1 Acceptance Scenario 2).
 - **Verification**: Run `pytest tests/integration/test_us1.py` with a synthetic gap dataset.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Identify Optimal Propagation Lag (Priority: P2)

**Goal**: Search a plausible lag window (30–90 min) and report the lag that maximizes the absolute correlation.

**Independent Test**: Execute the lag-search on a known synthetic dataset where the true lag is min; the pipeline must report 45 min (±1 min) as the optimal lag.

### Implementation for User Story 2

- [X] T023 [US2] Integrate `analysis/lag_search.py` with the US-1 pipeline to identify optimal lag `L*` (FR-010).
 - **Deliverable**: Update `results/us1_correlation.json` to include `optimal_lag` and `lag_correlation_value`.
- [X] T024 [US2] Verify the lag-sweep reports `L*` and corresponding correlation values (FR-010).
 - **Verification**: Run `pytest tests/integration/test_us2.py`.
- [X] T025 [US2] Verify the pipeline calculates and reports `|L* - L_phys|` (SC-002).
 - **Verification**: Check `results/us1_correlation.json` for `lag_difference` key.
- [X] T026 [US2] Execute the lag-search on a synthetic dataset (true lag 45 min) and verify the pipeline reports 45 min (±1 min) (US-2 Independent Test).
 - **Verification**: Run `pytest tests/integration/test_synthetic.py`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualise Relationship and Sensitivity (Priority: P3)

**Goal**: Generate scatter plots, time-series overlays, and sensitivity analysis for high-speed thresholds.

**Independent Test**: After a successful run, verify PNG files (scatter, time-series) and sensitivity table (T ∈ {, 500, 600} km/s) are generated.

### Implementation for User Story 3

- [X] T027 [US3] Integrate `viz/plots.py` (scatter and time-series) with the main pipeline.
 - **Deliverable**: Generate `results/plot_scatter.png` and `results/plot_timeseries.png`.
- [X] T028 [US3] Integrate `analysis/sensitivity.py` to compute correlations for T ∈ {400, 500, 600} km/s (FR-007).
 - **Deliverable**: Update `results/us1_correlation.json` to include `sensitivity_table`.
- [X] T029 [US3] Generate PNG files (scatter, time-series) and sensitivity table for a sample run.
 - **Verification**: Run `pytest tests/integration/test_us3.py`.
- [X] T030 [US3] Verify all plots load without error, include correct labels/units, and show the optimal lag annotation (SC-005).
 - **Verification**: Run `pytest tests/unit/test_plots.py`.
- [ ] T031 [US3] Verify the sensitivity table correctly reports correlation magnitude for each threshold (US-3 Acceptance Scenario 2).
 - **Verification**: Check `results/us1_correlation.json` for correct values.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Testing & Validation

**Purpose**: Unit and integration tests required by plan.md and spec.md Independent Tests. Tests are written alongside implementation to ensure verification during development.

- [ ] T032 [P] Write unit tests for `data/clean.py` in `tests/unit/test_clean.py` (FR-003).
 - **Test Functions**: `test_clean_removes_nan`, `test_clean_resamples_to_5min`, `test_clean_handles_empty_input`.
- [ ] T033 [P] Write unit tests for `data/lag.py` in `tests/unit/test_lag.py` (FR-012).
 - **Test Functions**: `test_lag_calculation_formula`, `test_lag_shift_applies_correctly`.
- [ ] T034 [P] Write integration test for lag-adjusted correlation pipeline in `tests/integration/test_pipeline.py` (US-1 Independent Test).
 - **Test Function**: `test_us1_full_pipeline` verifying JSON output keys.
- [ ] T035 [P] Write unit tests for permutation test logic in `tests/unit/test_correlation.py` (FR-005).
 - **Test Functions**: `test_permutation_block_size`, `test_permutation_p_value_calculation`.
- [ ] T036 [P] Write unit tests for lag sweep logic in `tests/unit/test_lag_search.py` (FR-010).
 - **Test Functions**: `test_lag_sweep_window`, `test_optimal_lag_identification`.
- [ ] T037 [P] Write integration test for synthetic dataset validation in `tests/integration/test_synthetic.py` (US-2 Independent Test).
 - **Test Function**: `test_synthetic_lag_45min` verifying ±1 min accuracy.
- [ ] T038 [P] Write unit tests for sensitivity threshold filtering in `tests/unit/test_sensitivity.py` (FR-007).
 - **Test Functions**: `test_threshold_filtering`, `test_sensitivity_correlation_calculation`.
- [ ] T039 [P] Write unit tests for bootstrap resampling logic in `tests/unit/test_correlation.py` (FR-006).
 - **Test Functions**: `test_bootstrap_block_size`, `test_bootstrap_ci_calculation`.
- [ ] T040 [P] Write unit tests for data cleaning edge cases (empty input, all-NaN column) in `tests/unit/test_clean.py` (FR-003).
 - **Test Functions**: `test_clean_all_nan`, `test_clean_single_value`.
- [ ] T041 [P] Run end-to-end validation on a multi-day interval to ensure reproducibility and all outputs (JSON, PNGs) are generated correctly (Constitution Principle I).
 - **Verification**: Run `pytest tests/integration/` and verify `results/` directory contains all expected artifacts.
- [ ] T042 [P] Verify all artifacts (data, code, reports) are checksummed and recorded in the project state (Constitution Principle V).

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories. (Note: Phases 8 and 9 were removed as they introduced scope creep contradicting the Spec.)

- [ ] T043 [P] Final review of all output artifacts to ensure they match the Spec's Success Criteria (SC-001 to SC-005).
- [ ] T044 [P] Update `README.md` with instructions on how to run the full pipeline and interpret the results.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Testing (Phase 6)**: Can run in parallel with User Story implementation once modules are created
- **Polish (Phase 7)**: Depends on all desired user stories, tests, and review fixes being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tasks within a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- Testing tasks (Phase 6) can run in parallel with implementation tasks once the target modules exist
- Physics/Review tasks (Phases 8-9) have been removed as they were out of scope.

---

## Parallel Example: User Story 1

```bash
# Launch all models for User Story 1 together:
Task: "Implement projects/.../code/analysis/correlation.py with Pearson/Spearman calculation"
Task: "Implement projects/.../code/analysis/correlation.py Circular Block Permutation test"
Task: "Implement projects/.../code/analysis/correlation.py Moving Block Bootstrap"
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
5. Add Physics/Review fixes (Phases 8-9) → **REMOVED** as out of scope.
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
 - Developer D: Testing (Phase 6)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All data ingestion must use verified URLs (OMNIWeb, CDAWeb) and no GPU libraries. Permutation tests must be optimized for CPU-only execution.
- **Removed Scope Creep**: Tasks related to Lorentz transformations, Alfvén speed modeling, non-linear saturation fitting, and reference frame analysis (formerly Phases 8 & 9) have been removed as they lack FR/SC anchors and contradict the Spec.
- **Test Coverage**: All Independent Tests from US-1 and US-2 are now explicitly mapped to test tasks (T034, T037) with specific function names and verification commands.
- **Review Integration**: The scope has been strictly limited to the Spec's authorized methods (linear correlation, permutation tests, fixed 60 Re distance).