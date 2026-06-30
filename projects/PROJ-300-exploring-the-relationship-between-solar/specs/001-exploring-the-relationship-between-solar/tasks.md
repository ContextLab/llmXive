# Tasks: Exploring the Relationship Between Solar Wind Speed and Geomagnetic Tail Reconnection Rates

**Input**: Design documents from `/specs/PROJ-300-01-solar-wind-reconnection/`
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

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-300-exploring-the-relationship-between-solar/`) by executing the following commands to ensure the exact directory tree:
  ```bash
  mkdir -p projects/PROJ-300-exploring-the-relationship-between-solar/{code/{data,analysis,viz},data/{raw,processed},tests/{unit,integration}}
  touch projects/PROJ-300-exploring-the-relationship-between-solar/code/__init__.py
  touch projects/PROJ-300-exploring-the-relationship-between-solar/code/data/__init__.py
  touch projects/PROJ-300-exploring-the-relationship-between-solar/code/analysis/__init__.py
  touch projects/PROJ-300-exploring-the-relationship-between-solar/code/viz/__init__.py
  touch projects/PROJ-300-exploring-the-relationship-between-solar/tests/__init__.py
  ```
  The resulting tree must match:
  ```
  projects/PROJ-300-exploring-the-relationship-between-solar/
  ├── code/
  │   ├── __init__.py
  │   ├── config.py
  │   ├── data/
  │   │   ├── __init__.py
  │   │   ├── ingest.py
  │   │   ├── clean.py
  │   │   └── lag.py
  │   ├── analysis/
  │   │   ├── __init__.py
  │   │   ├── correlation.py
  │   │   ├── lag_search.py
  │   │   └── sensitivity.py
  │   ├── viz/
  │   │   ├── __init__.py
  │   │   └── plots.py
  │   └── main.py
  ├── data/
  │   ├── raw/
  │   └── processed/
  ├── tests/
  │   ├── unit/
  │   └── integration/
  ├── requirements.txt
  └── README.md
  ```
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` at `projects/PROJ-300-exploring-the-relationship-between-solar/requirements.txt` containing the following exact pinned versions:
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

- [ ] T003 [P] Create `projects/PROJ-300-exploring-the-relationship-between-solar/code/config.py` defining constants: `LAG_WINDOW_MIN=30`, `LAG_WINDOW_MAX=90`, `LAG_STEP=5`, `EARTH_RADIUS_KM=6371`, `TAIL_DISTANCE_RE=60`, `BOOTSTRAP_ITERATIONS=1000`, `PERMUTATION_ITERATIONS=10000`. The file path must be explicitly stated in the docstring.
- [ ] T004 [P] Implement `projects/PROJ-300-exploring-the-relationship-between-solar/code/data/ingest.py` to fetch OMNIWeb data (Vsw, Bz) via `requests` (FR-001) and THEMIS data (Ey) via `cdaweb` (FR-002).
- [ ] T005 [P] Implement `projects/PROJ-300-exploring-the-relationship-between-solar/code/data/clean.py` for NaN removal and resampling to 5-minute cadence using pandas (FR-003).
- [ ] T006 [P] Implement `projects/PROJ-300-exploring-the-relationship-between-solar/code/data/lag.py` to calculate physics-based lag `L_phys` using formula `L_phys = (60 * 6371) / Vsw_mean / 60` (FR-012) and apply lag shifts to time series.
- [ ] T007 [P] Implement `projects/PROJ-300-exploring-the-relationship-between-solar/code/analysis/correlation.py` function `calculate_correlation` for Pearson/Spearman calculation (used by FR-005/FR-006).
- [ ] T008 [P] Implement `projects/PROJ-300-exploring-the-relationship-between-solar/code/analysis/correlation.py` function `circular_block_permutation` with 10,000 iterations for empirical p-values (FR-005).
- [ ] T009 [P] Implement `projects/PROJ-300-exploring-the-relationship-between-solar/code/analysis/correlation.py` function `moving_block_bootstrap` with 1,000 iterations for 95% confidence intervals (FR-006).
- [ ] T010 [P] Implement `projects/PROJ-300-exploring-the-relationship-between-solar/code/analysis/lag_search.py` function `find_optimal_lag` to sweep the 30–90 min window and identify optimal lag `L*` (FR-010).
- [ ] T011 [P] Implement `projects/PROJ-300-exploring-the-relationship-between-solar/code/analysis/sensitivity.py` function `analyze_thresholds` to sweep thresholds T ∈ {400, 500, 600} km/s and recompute correlations (FR-007).
- [ ] T012 [P] Implement `projects/PROJ-300-exploring-the-relationship-between-solar/code/viz/plots.py` function `plot_scatter` to generate scatter plot of lag-adjusted Vsw vs. Ey with regression line (FR-008a).
- [ ] T013 [P] Implement `projects/PROJ-300-exploring-the-relationship-between-solar/code/viz/plots.py` function `plot_timeseries` to generate dual-axis time-series overlay of Vsw and Ey (FR-008b).
- [ ] T014 [P] Add docstring to `projects/PROJ-300-exploring-the-relationship-between-solar/code/analysis/lag_search.py` documenting the multiple-comparison correction method (permutation test) and total lag candidate count (FR-011).
- [ ] T015 [P] Implement `projects/PROJ-300-exploring-the-relationship-between-solar/code/main.py` to insert the FR-013 narrative note into the "notes" field of the JSON report. The exact string must be: "Note: Bonferroni correction is conservative for autocorrelated lag searches; the permutation test (FR-005) is the primary method for significance testing. Future work should consider adaptive FDR control." (FR-013).
- [ ] T016 [P] Implement `projects/PROJ-300-exploring-the-relationship-between-solar/code/main.py` to log data-quality warnings to `projects/PROJ-300-exploring-the-relationship-between-solar/data/processed/quality_log.json` in JSON format (FR-009).
- [ ] T017 [P] Implement logic in `projects/PROJ-300-exploring-the-relationship-between-solar/code/main.py` to calculate and report `|L* - L_phys|` (SC-002) using the optimal lag L* from FR-010 and L_phys from FR-012.
- [ ] T018 [P] Implement logic in `projects/PROJ-300-exploring-the-relationship-between-solar/code/main.py` to generate sensitivity table and append to JSON report (SC-003).
- [ ] T019 [P] Ensure all plots in `projects/PROJ-300-exploring-the-relationship-between-solar/code/viz/plots.py` include correct axis labels, units, and optimal lag annotation (SC-005).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Quantify Lag‑Adjusted Coupling (Priority: P1) 🎯 MVP

**Goal**: Compute correlation between solar-wind speed (Vsw) and tail-reconnection proxy (Ey) after applying propagation lag, including permutation tests for significance.

**Independent Test**: Run the analysis pipeline on a multi-day interval and verify output includes Pearson/Spearman coefficients, p-values, and significance flags.

### Implementation for User Story 1

- [ ] T020 [US1] Integrate `data/clean.py`, `data/lag.py`, and `analysis/correlation.py` into a cohesive pipeline for US-1 in `main.py`.
- [ ] T021 [US1] Execute the pipeline on a sample date range to verify output includes numeric correlation coefficients and empirical p-values (US-1 Acceptance Scenario 1).
- [ ] T022 [US1] Verify pipeline handles NaN gaps by cleaning, resampling, and producing correlation output without error (US-1 Acceptance Scenario 2).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Identify Optimal Propagation Lag (Priority: P2)

**Goal**: Search a plausible lag window (30–90 min) and report the lag that maximizes the absolute correlation.

**Independent Test**: Execute the lag-search on a known synthetic dataset where the true lag is 45 min; the pipeline must report 45 min (±1 min) as the optimal lag.

### Implementation for User Story 2

- [ ] T023 [US2] Integrate `analysis/lag_search.py` with the US-1 pipeline to identify optimal lag `L*` (FR-010).
- [ ] T024 [US2] Verify the lag-sweep reports `L*` and corresponding correlation values (FR-010).
- [ ] T025 [US2] Verify the pipeline calculates and reports `|L* - L_phys|` (SC-002).
- [ ] T026 [US2] Execute the lag-search on a synthetic dataset (true lag 45 min) and verify the pipeline reports 45 min (±1 min) (US-2 Independent Test).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualise Relationship and Sensitivity (Priority: P3)

**Goal**: Generate scatter plots, time-series overlays, and sensitivity analysis for high-speed thresholds.

**Independent Test**: After a successful run, verify PNG files (scatter, time-series) and sensitivity table (T ∈ {400, 500, 600} km/s) are generated.

### Implementation for User Story 3

- [ ] T027 [US3] Integrate `viz/plots.py` (scatter and time-series) with the main pipeline.
- [ ] T028 [US3] Integrate `analysis/sensitivity.py` to compute correlations for T ∈ {400, 500, 600} km/s (FR-007).
- [ ] T029 [US3] Generate PNG files (scatter, time-series) and sensitivity table for a sample run.
- [ ] T030 [US3] Verify all plots load without error, include correct labels/units, and show the optimal lag annotation (SC-005).
- [ ] T031 [US3] Verify the sensitivity table correctly reports correlation magnitude for each threshold (US-3 Acceptance Scenario 2).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Testing & Validation

**Purpose**: Unit and integration tests required by plan.md and spec.md Independent Tests

- [ ] T032 [P] Write unit tests for `data/clean.py` in `tests/unit/test_clean.py` (FR-003).
- [ ] T033 [P] Write unit tests for `data/lag.py` in `tests/unit/test_lag.py` (FR-012).
- [ ] T034 [P] Write integration test for lag-adjusted correlation pipeline in `tests/integration/test_pipeline.py` (US-1 Independent Test).
- [ ] T035 [P] Write unit tests for permutation test logic in `tests/unit/test_correlation.py` (FR-005).
- [ ] T036 [P] Write unit tests for lag sweep logic in `tests/unit/test_lag_search.py` (FR-010).
- [ ] T037 [P] Write integration test for synthetic dataset validation in `tests/integration/test_synthetic.py` (US-2 Independent Test).
- [ ] T038 [P] Write unit tests for sensitivity threshold filtering in `tests/unit/test_sensitivity.py` (FR-007).
- [ ] T039 [P] Write unit tests for bootstrap resampling logic in `tests/unit/test_correlation.py` (FR-006).
- [ ] T040 [P] Write unit tests for data cleaning edge cases (empty input, all-NaN column) in `tests/unit/test_clean.py` (FR-003).
- [ ] T041 [P] Run end-to-end validation on a multi-day interval to ensure reproducibility and all outputs (JSON, PNGs) are generated correctly (Constitution Principle I).
- [ ] T042 [P] Verify all artifacts (data, code, reports) are checksummed and recorded in the project state (Constitution Principle V).

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T043 [P] Run end-to-end validation on a multi-day interval to ensure reproducibility and all outputs (JSON, PNGs) are generated correctly.
- [ ] T044 [P] Verify all artifacts (data, code, reports) are checksummed and recorded in the project state (Constitution Principle V).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Testing (Phase 6)**: Can run in parallel with User Story implementation once modules are created
- **Polish (Phase 7)**: Depends on all desired user stories and tests being complete

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
5. Each story adds value without breaking previous stories

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
- **Removed Scope Creep**: Tasks related to Alfvén speed, reference_frames.md, physical interpretation (non-statistical), synthetic generator, and generic cleanup have been removed as they lack FR/SC anchors.
- **Test Coverage**: All Independent Tests from US-1 and US-2 are now explicitly mapped to test tasks (T034, T037).