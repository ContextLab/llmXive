# Tasks: The Impact of Aggregate Negative News Publication Volume on Anticipatory Anxiety

**Input**: Design documents from `/specs/001-the-impact-of-social-media-doomscrolling/`
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

- [ ] T001 Create project root directory: `projects/PROJ-487-the-impact-of-social-media-doomscrolling/`
- [ ] T002 Create data directories: `data/raw/`, `data/processed/`, `data/reports/` in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/`
- [ ] T003 Create code directories: `code/data/`, `code/tests/`, `code/utils/` in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/`
- [ ] T004 [P] Create Python virtual environment in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/` <!-- FAILED: unspecified -->
- [ ] T005 [P] Install dependencies from `requirements.txt` in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/`: `pandas`, `numpy`, `statsmodels`, `requests`, `scikit-learn`, `matplotlib`, `seaborn`, `pyyaml`, `pytrends`
- [ ] T006 [P] Configure linting (flake8/black) and formatting tools in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Setup logging infrastructure in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/code/utils/logging.py`
- [~] T008 [P] Create schema validation utilities using `pyyaml` to validate against `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/code/utils/validation.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition (Priority: P1) 🎯 MVP

**Goal**: Retrieve historical time-series data for aggregate negative news publication volume from GDELT and anxiety-related search trends from Google Trends.

**Independent Test**: Execute fetch scripts and verify output CSV files contain non-empty rows for the target date range with valid checksums.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [US1] Unit test for GDELT API retry logic (with a configurable maximum number of attempts) in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/code/tests/test_fetch_gdelt.py`
- [X] T010 [US1] Unit test for Google Trends keyword validation in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/code/tests/test_fetch_google_trends.py`

### Implementation for User Story 1

- [~] T011 [US1] Implement GDELT fetch script in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/code/data/fetch_gdelt.py` using `EventCount` metric for negative sentiment events; save to `data/raw/gdelt_events.csv`
- [~] T012 [US1] Implement Google Trends fetch script in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/code/data/fetch_google_trends.py` for keywords "anticipatory anxiety", "worry about future"; save to `data/raw/google_trends.csv`
- [~] T013 [US1] Add error handling for API failures in `fetch_gdelt.py` and `fetch_google_trends.py` (exit non-zero on failure after retries)
- [ ] T014 [US1] Add data integrity checks: verify CSVs have non-empty rows for target date range by reading from `data/raw/gdelt_events.csv` and `data/raw/google_trends.csv`; write `validation_status.json` with fetch status or exit non-zero on failure.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Data Preprocessing (Priority: P2)

**Goal**: Clean, normalize, and align retrieved time-series data to daily resolution, ensuring stationarity.

**Independent Test**: Run preprocessing script on raw CSVs; verify output has no missing values, aligned timestamps, and passes ADF stationarity checks (or is differenced).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T015 [P] [US2] Unit test for timestamp alignment (intersection logic) in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/code/tests/test_preprocess.py`
- [X] T016 [P] [US2] Unit test for ADF test and differencing logic in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/code/tests/test_preprocess.py`

### Implementation for User Story 2

- [~] T017 [US2] Implement timestamp alignment in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/code/data/preprocess.py`: align to daily intervals, preserve zero-event days as valid zeros (DO NOT interpolate zeros), use **linear interpolation** ONLY for null/missing values. Read from `data/raw/gdelt_events.csv` and `data/raw/google_trends.csv`.
- [~] T018 [US2] Implement stationarity testing (Augmented Dickey-Fuller) in `preprocess.py`: if p ≥ 0.05, apply differencing until stationary
- [ ] T019 [US2] Implement normalization in `preprocess.py`: convert to z-scores (mean=0, std=1) after stationarity is achieved
- [ ] T020 [US2] Save aligned, stationary, normalized data to `data/processed/aligned_timeseries.csv` and `data/processed/stationarity_check.csv`
- [ ] T021 [US2] Add validation to exit with error "Insufficient data for Granger causality" if time-series length < 20
- [ ] T022 [US2] **Post-Interpolation Completeness Check**: Verify `data/processed/aligned_timeseries.csv` has ≥95% data completeness (per Spec SC-001) after interpolation; write `validation_status.json` or exit non-zero if failed.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis & Reporting (Priority: P3)

**Goal**: Compute correlation, perform Granger causality tests with wide lag window, conduct sensitivity analysis, and generate visualizations.

**Independent Test**: Execute analysis script; verify output reports contain correlation values, p-values (fixed-sweep), and plot images.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US3] Unit test for correlation calculation in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/code/tests/test_analyze.py`
- [ ] T024 [P] [US3] Unit test for Granger causality fixed-sweep (lags {1, 2, 3, 7, 14}) in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/code/tests/test_analyze.py`

### Implementation for User Story 3

- [ ] T025 [US3] Implement correlation analysis in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/code/data/analyze.py`: compute Pearson and Spearman coefficients with p-values. Read from `data/processed/aligned_timeseries.csv`.
- [ ] T026 [US3] **Spec Override**: Implement Granger causality test in `analyze.py`: perform a **FIXED SWEEP** of lags {1, 2, 3, 7, 14} as per Spec FR-005. **Note**: This task overrides the Plan's AIC/BIC constraint to strictly follow Spec FR-005. Report p-values for ALL specified lags. Save results to `data/processed/granger_results.csv`.
- [ ] T027 [US3] Implement sensitivity analysis in `analyze.py`: Calculate the significance rate (count of lags in {1, 2, 3, 7, 14} where p < 0.05) and report this rate. Read from `data/processed/granger_results.csv`.
- [ ] T028 [US3] **Statistical Validity Check (Spec Override)**: Verify at least one lag in the specific set {1, 2, 3, 7, 14} has p < 0.01 (Bonferroni-corrected alpha α = 0.05 / 5 = 0.01) as per Spec SC-002. **Note**: This task overrides the Plan's "avoid Bonferroni" constraint. If condition fails, exit with code 1 and log error: "Statistical validity failed: no lag met Bonferroni threshold".
- [ ] T029 [US3] Implement report generation in `analyze.py`: create `data/reports/analysis_report.pdf` containing lag plots, correlation heatmaps, sensitivity summaries, and the validity check result.
- [ ] T030 [US3] Ensure all analysis runs on CPU-only environment within ≤ 6 hours (verify no CUDA/GPU dependencies)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031 [P] Documentation updates: Update README.md with CLI usage and quickstart.md with environment setup steps in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/`
- [ ] T032 Code cleanup and refactoring in `code/`
- [ ] T033 [P] Additional unit tests for edge cases (zero-event days, API failures) in `code/tests/`
- [ ] T034 Run quickstart.md validation to ensure full pipeline reproducibility

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 processed data

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services (N/A for data pipeline)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (with data dependencies respected)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for GDELT API retry logic in code/tests/test_fetch_gdelt.py"
Task: "Unit test for Google Trends keyword validation in code/tests/test_fetch_google_trends.py"

# Launch all models for User Story 1 together:
Task: "Implement GDELT fetch script in code/data/fetch_gdelt.py"
Task: "Implement Google Trends fetch script in code/data/fetch_google_trends.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (data fetch & completeness)
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
 - Developer A: User Story 1 (Data Fetch)
 - Developer B: User Story 2 (Preprocessing) - can start once US1 data is available
 - Developer C: User Story 3 (Analysis) - can start once US2 data is available
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
- **CPU Feasibility**: All tasks MUST run on 2-core CPU, ≤7GB RAM, ≤6h runtime. No GPU/CUDA.
- **Data Integrity**: All data must be from real sources (GDELT, Google Trends). No synthetic data.
- **Statistical Rigor**: Use fixed-sweep lags {1, 2, 3, 7, 14} and Bonferroni correction (α=0.01) as mandated by Spec FR-005 and SC-002.
- **Spec vs Plan Note**: This task list strictly follows Spec FR-005/SC-002 (Bonferroni, fixed-sweep), overriding conflicting instructions in plan.md.