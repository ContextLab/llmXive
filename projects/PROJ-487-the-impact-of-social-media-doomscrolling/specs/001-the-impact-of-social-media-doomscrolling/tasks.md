# Tasks: The Impact of Aggregate Negative News Publication Volume on Anticipatory Anxiety

**Input**: Design documents from `/specs/001-the-impact-of-social-media-doomscrolling/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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

- [ ] T001 [P] Create project root directory: `projects/PROJ-487-the-impact-of-social-media-doomscrolling/` (Check for existence first; create if missing).
- [ ] T002 [P] Create data directories: `data/raw/`, `data/processed/`, `data/reports/` in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/` (Verify directories exist after creation).
- [ ] T003 [P] Create code directories: `code/data/`, `code/tests/`, `code/utils/` in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/` (Verify directories exist after creation).
- [ ] T004 [P] Create Python virtual environment in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/` (Verify `bin/activate` exists).
- [X] T005 [P] Install dependencies from `code/requirements.txt` in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/`: `pandas`, `numpy`, `statsmodels`, `requests`, `scikit-learn`, `matplotlib`, `seaborn`, `pyyaml`, `pytrends`.
 - **Verification**: Run `pip list` and explicitly verify the presence of `pandas`, `numpy`, `statsmodels`, `requests`, `scikit-learn`, `matplotlib`, `seaborn`, `pyyaml`, `pytrends` using `pip list | grep <package_name>` for each. Exit non-zero if any are missing.
- [X] T006 [P] Configure linting (flake8/black) and formatting tools in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/` (Verify config files `.flake8`, `pyproject.toml` exist).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Setup logging infrastructure in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/code/utils/logging.py`
- [ ] T008a [P] Generate schema files: Create `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` based on `data-model.md` entities in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/`.
- [X] T008b [P] Implement validation utility: Create `projects/PROJ-487-the-impact-of-social-media-doomscrolling/code/utils/validation.py` using `pyyaml` to load schemas and validate data.
- [ ] T008c [P] Verify schemas: Run a validation script to ensure `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` are valid YAML and loadable by `validation.py`.

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

- [X] T011 [US1] Implement GDELT fetch script in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/code/data/fetch_gdelt.py` using `EventCount` metric for negative sentiment events; save to `data/raw/gdelt_events.csv`
- [X] T012 [US1] Implement Google Trends fetch script in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/code/data/fetch_google_trends.py` for keywords "anticipatory anxiety", "worry about future"; save to `data/raw/google_trends.csv`
- [ ] T013 [US1] Implement error handling for API failures in `fetch_gdelt.py` and `fetch_google_trends.py`:
 1. Wrap API calls in `try/except` blocks catching `requests.exceptions.Timeout` and `requests.exceptions.HTTPError`.
 2. Log errors using the configured logger.
 3. Exit with a non-zero status code (exit code 1) if retries (max 3) are exhausted.
- [X] T014 [US1] Add data integrity checks: verify CSVs have non-empty rows for target date range by reading from `data/raw/gdelt_events.csv` and `data/raw/google_trends.csv`; write `validation_status.json` with fetch status or exit non-zero on failure.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Data Preprocessing (Priority: P2)

**Goal**: Clean, normalize, and align retrieved time-series data to daily resolution, ensuring stationarity.

**Independent Test**: Run preprocessing script on raw CSVs; verify output has no missing values, aligned timestamps, and passes ADF stationarity checks (or is differenced).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T015 [P] [US2] Unit test for timestamp alignment (intersection logic) in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/code/tests/test_preprocess.py`
- [X] T016 [P] [US2] Unit test for ADF test and differencing logic in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/code/tests/test_preprocess.py`

### Implementation for User Story 2

- [X] T017a [US2] Implement timestamp alignment in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/code/data/preprocess.py`:
 - **Input**: `data/raw/gdelt_events.csv`, `data/raw/google_trends.csv`
 - **Output**: `data/processed/aligned_raw.csv`
 - **Logic**:
 1. Align both datasets to daily intervals.
 2. Use intersection of timestamps (preserve only dates present in both).
 3. Preserve zero-event days as valid zeros (DO NOT interpolate zeros).
- [ ] T017b [US2] Implement interpolation in `preprocess.py`:
 - **Input**: `data/processed/aligned_raw.csv` (Output of T017a)
 - **Output**: `data/processed/aligned_interpolated.csv`
 - **Logic**:
 1. Identify null/missing values (NaN) ONLY.
 2. Apply linear interpolation ONLY for these null values.
 3. Ensure zero-event counts remain untouched.
 4. **Verification**: Explicitly verify in the output file that rows corresponding to zero-event days in the input still have value 0.0 (not interpolated).
 - **Dependency**: Requires T017a to complete first.
 - **Spec-Driven Exception**: This task implements linear interpolation as per Spec FR-002, superseding the Plan's "forward fill" instruction.
- [ ] T018 [US2] Implement stationarity testing (Augmented Dickey-Fuller) in `preprocess.py`:
 1. Use `statsmodels.tsa.stattools.adfuller`.
 2. If p-value ≥ 0.05, apply differencing (`np.diff`) iteratively until p < 0.05.
 3. Log the number of differences applied.
- [ ] T019 [US2] Implement normalization in `preprocess.py`:
 1. After stationarity is achieved, convert the series to z-scores (mean=0, std=1) using `sklearn.preprocessing.StandardScaler`.
 2. Save the normalized series.
- [ ] T020 [US2] Save aligned, stationary, normalized data to `data/processed/aligned_timeseries.csv` and `data/processed/stationarity_check.csv`.
- [ ] T021 [US2] Implement edge-case validation in `preprocess.py`:
 1. Check the length of the time-series after alignment.
 2. If length < 20, exit with error code 1.
 3. **Verification**: Confirm the log contains the exact message: "Insufficient data for Granger causality".
- [ ] T022 [US2] Implement Post-Interpolation Completeness Check in `preprocess.py`:
 1. Calculate completeness percentage: (count of non-null values / total rows) *.
 2. Verify completeness ≥ 95% (0.95).
 3. Write `validation_status.json` with key `completeness_pct` if passed, or exit non-zero if failed.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis & Reporting (Priority: P3)

**Goal**: Compute correlation, perform Granger causality tests with wide lag window, conduct sensitivity analysis, and generate visualizations.

**Independent Test**: Execute analysis script; verify output reports contain correlation values, p-values (fixed-sweep), and plot images.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US3] Unit test for correlation calculation in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/code/tests/test_analyze.py`
- [X] T024 [P] [US3] Unit test for Granger causality fixed-sweep (lags {1, 2, 3, 7, 14}) in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/code/tests/test_analyze.py`

### Implementation for User Story 3

- [X] T025 [US3] Implement correlation analysis in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/code/data/analyze.py`: compute Pearson and Spearman coefficients with p-values. Read from `data/processed/aligned_timeseries.csv`.
- [ ] T026 [US3] Implement Granger causality test in `analyze.py`:
 1. Perform a FIXED SWEEP of lags: short-term intervals and longer horizons such as 2, 3, 7, and 14 days as mandated by Spec FR-005.
 2. Use `statsmodels.tsa.stattools.grangercausalitytests` for each lag.
 3. Collect p-values for all specified lags.
 4. Save results to `data/processed/granger_results.csv`.
 5. **Spec-Driven Exception**: This task implements fixed-sweep lags as per Spec FR-005, superseding the Plan's "AIC/BIC" constraint.
- [ ] T027 [US3] Implement sensitivity analysis in `analyze.py`:
 1. **Dependency**: Requires T026 to complete first.
 2. Read p-values from `data/processed/granger_results.csv`.
 3. Calculate the significance rate (count of lags in {1, 2, 3, 7, 14} where p < 0.05).
 4. Calculate the significance rate (count of lags in {1, 2, 3, 7, 14} where p < 0.01, Bonferroni-corrected).
 5. Report BOTH rates and explicitly describe the variation trend across the lag sweep in the final output.
 6. *Note*: This task proceeds regardless of T028's result.
- [ ] T028 [US3] Implement Statistical Validity Check in `analyze.py`:
 1. **Dependency**: Requires T026 to complete first.
 2. Read p-values from `data/processed/granger_results.csv`.
 3. Check if at least one lag has p < 0.01 (Bonferroni-corrected alpha α = 0.05 / 5 = 0.01) as per Spec SC-002.
 4. **Report** the result (pass/fail) and the specific p-values in the final report.
 5. **Do not exit** with an error code if the condition fails; the pipeline must continue to report negative results as per Spec SC-002.
 6. Log the result to `data/reports/validation_result.log`.
 7. **Spec-Driven Exception**: This task implements Bonferroni correction as per Spec SC-002, superseding the Plan's "avoiding Bonferroni" constraint.
- [ ] T029 [US3] Implement report generation in `analyze.py`: create `data/reports/analysis_report.pdf` containing:
 1. Lag plots.
 2. Correlation heatmaps.
 3. Sensitivity analysis summaries (including the trend across thresholds from T027).
 4. The validity check result (from T028).
 5. The Data Completeness Percentage (from T022).
 6. **Dependencies**: Requires T025, T026, T027, and T028 to be complete.
- [ ] T030a [US3] Implement CPU-only verification in `analyze.py`:
 1. Add a check using standard library (`sys`, `os`) to detect if any GPU/CUDA-enabled packages (e.g., `torch`, `tensorflow`, `cupy`) are imported or active in `sys.modules`.
 2. Verify that the environment variable `CUDA_VISIBLE_DEVICES` is unset or empty.
 3. If any GPU library is detected or `CUDA_VISIBLE_DEVICES` is set, exit with error code 1 and log "GPU/CUDA detected. FR-006 requires CPU-only execution."
 4. Do not import `torch` or any other GPU library to perform this check; use standard library inspection only.
- [ ] T030b [US3] Implement runtime benchmarking:
 1. Wrap the entire analysis pipeline execution with a timer.
 2. Log the total duration to `data/reports/runtime.log`.
 3. Verify duration ≤ 6 hours (21600 seconds).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031 [P] Documentation updates:
 1. Generate `README.md` with CLI usage instructions and project overview.
 2. Generate `quickstart.md` with environment setup steps and dependency installation.
 3. **Requirement**: Explicitly include the "Proxy Acknowledgment" in README.md (stating GDELT EventCount is a proxy for news exposure, not direct social media consumption, as per FR-001).
 4. Place in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/`.
- [ ] T033 [P] Additional unit tests for edge cases (zero-event days, API failures) in `code/tests/`
- [ ] T034 [P] Run quickstart.md validation: Execute `python -m pytest --tb=short` (or equivalent pipeline command) and verify exit code 0.

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

- All Setup tasks marked [P] can run in parallel (except T005 which depends on T004)
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
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

- [P] tasks = different files, no dependencies (except T005 which depends on T004)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CPU Feasibility**: All tasks MUST run on 2-core CPU, ≤7GB RAM, ≤6h runtime. No GPU/CUDA.
- **Data Integrity**: All data must be from real sources (GDELT, Google Trends). No synthetic data.
- **Statistical Rigor**: Use fixed-sweep lags {1, 2, 3, 7, 14} and Bonferroni correction (α=0.01) as mandated by Spec FR-005 and SC-002.
- **Control Flow**: T028 (Validation) is a reporting step; T027 (Sensitivity) and T029 (Reporting) proceed regardless of T028's result to ensure negative findings are preserved.
- **Spec-Driven Exceptions**: Tasks T017b, T026, and T028 explicitly supersede conflicting Plan instructions (Forward Fill, AIC/BIC, No Bonferroni) to satisfy Spec requirements.