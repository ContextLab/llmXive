# Tasks: The Impact of Aggregate Negative News Publication Volume on Anticipatory Anxiety

**Input**: Design documents from `/specs/001-news-volume-anxiety/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/`, `data/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project marker: Create `.project_init.json` in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/` with content: `{"project_id": "PROJ-487", "branch": "001-news-volume-anxiety", "created": "2026-06-27"}`.
- [ ] T002 Create data directories: Create `data/raw/`, `data/processed/`, `data/reports/` in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/` and create a `.gitkeep` file in each to ensure version control tracking.
- [ ] T003 Create code directories: Create `code/data/`, `code/tests/`, `code/utils/` in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/` and create an `__init__.py` file in each to ensure Python package recognition.
- [ ] T004a [P] Create Python virtual environment: Initialize `venv` in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/` by running `python -m venv venv`. **Verification**: Verify `venv/bin/activate` exists.
- [ ] T004b [P] Verify Python virtual environment: Verify `venv/bin/activate` exists in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/`. **Depends on: T004a**.
- [X] T005a [P] Create requirements file: Create `code/requirements.txt` in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/` with `pandas`, `numpy`, `statsmodels`, `requests`, `scikit-learn`, `matplotlib`, `seaborn`, `pyyaml`, `pytrends`, `reportlab`, `pytest`, `responses`.
- [X] T005b Install dependencies: Run `pip install -r code/requirements.txt` in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/`. **Depends on: T005a**.
- [X] T006 [P] Configure linting: Create `pyproject.toml` in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/` with the following exact content:
 ```toml
 [tool.black]
 line-length = 88
 target-version = ['py311']

 [tool.flake8]
 max-line-length = 88
 ignore = ["E203", "W503"]
 ```
 **Depends on: T004b**.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T007a [P] Create dataset schema file: Generate `contracts/dataset.schema.yaml` in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/specs/001-news-volume-anxiety/contracts/` based on `TimeSeriesRecord` entity. **Fields**: `date` (string, ISO8601), `value` (float), `source` (string). Use JSON Schema format (serialized as YAML) compatible with `jsonschema`.
- [ ] T007b [P] Create output schema file: Generate `contracts/output.schema.yaml` in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/specs/001-news-volume-anxiety/contracts/` based on `AnalysisResult` entity. **Fields**: `metric` (string), `coefficient` (float), `p_value` (float), `lag` (integer), `significance_flag` (boolean), `stationarity_status` (string). Use JSON Schema format (serialized as YAML).
- [ ] T008 [P] Create schema validation utilities: Create `projects/PROJ-487-the-impact-of-social-media-doomscrolling/code/utils/validation.py` to load and validate data against `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` using `jsonschema`. **Depends on**: Completion of both T007a AND T007b.
- [X] T009 [P] Setup logging infrastructure: Create `projects/PROJ-487-the-impact-of-social-media-doomscrolling/code/utils/logging.py` with a standard logger configuration (file + console output, JSON format).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition (Priority: P1) 🎯 MVP

**Goal**: Retrieve historical time-series data for aggregate negative news publication volume from GDELT and anxiety-related search trends from Google Trends.

**Independent Test**: Execute fetch scripts and verify output CSV files contain non-empty rows for the target date range with valid checksums.

### Implementation for User Story 1 (TDD Cycle: Write Test -> Implement)

- [ ] T010a [P] [US1] **Write Test**: Create `test_fetch_gdelt.py` file in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/code/tests/`. **Depends on: T004b, T005b**.
- [ ] T010b [P] [US1] **Write Test**: Implement mock logic in `test_fetch_gdelt.py` using `responses` to simulate 2 failed requests (500 errors) followed by a success.
- [ ] T010c [P] [US1] **Write Test**: Implement assertion in `test_fetch_gdelt.py::test_retry_logic_on_failure`. **Assertion**: Verify the function retries exactly 3 times (`mock.call_count == 3`) and returns the success response on the final attempt. **Run Test (Expect Fail)**. **Depends on: T010a, T010b**.
- [ ] T011a [P] [US1] **Write Test**: Create `test_fetch_google_trends.py` file in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/code/tests/`. **Depends on: T004b, T005b**.
- [ ] T011b [P] [US1] **Write Test**: Implement mock logic in `test_fetch_google_trends.py` to pass a list containing one invalid keyword (e.g., `"!!!!!"`) and expect a `ValueError`.
- [ ] T011c [P] [US1] **Write Test**: Implement assertion in `test_fetch_google_trends.py::test_invalid_keyword_validation`. **Assertion**: Verify the function raises a `ValueError` with a message listing the invalid keyword. **Run Test (Expect Fail)**. **Depends on: T011a, T011b**.
- [ ] T012a [P] [US1] **Implement Fetch Logic**: Implement GDELT fetch logic in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/code/data/fetch_gdelt.py`. Use `EventCount` metric for negative sentiment events. **Include retry logic**: Max 3 attempts, exponential backoff. **Save output to `data/raw/gdelt_events.csv`**. **Depends on: T004b, T005b**.
- [ ] T012b [P] [US1] **Implement Checksum**: Implement MD5 checksum generation for `data/raw/gdelt_events.csv` in `fetch_gdelt.py`. **Output**: Save checksum to `data/raw/.checksums.json` with key `gdelt_events.csv`. **Depends on: T012a**.
- [ ] T012c [P] [US1] **Verify Output**: Verify `data/raw/gdelt_events.csv` exists and is non-empty. **Depends on: T012b**.
- [ ] T013a [P] [US1] **Implement Fetch Logic**: Implement Google Trends fetch logic in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/code/data/fetch_google_trends.py` for keywords "anticipatory anxiety", "worry about future". **Include retry logic**: Max 3 attempts. **Save output to `data/raw/google_trends.csv`**. **Depends on: T004b, T005b**.
- [ ] T013b [P] [US1] **Implement Checksum**: Implement MD5 checksum generation for `data/raw/google_trends.csv` in `fetch_google_trends.py`. **Output**: Save checksum to `data/raw/.checksums.json` with key `google_trends.csv`. **Depends on: T013a**. <!-- FAILED: unspecified -->
- [ ] T013c [P] [US1] **Verify Output**: Verify `data/raw/google_trends.csv` exists and is non-empty. **Depends on: T013b**.
- [ ] T014a [P] [US1] **Write Error Test**: Create `test_fetch_error_handling.py::test_500_exit_code` in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/code/tests/`. **Mock**: Force 500 errors via `responses`. **Assertion**: Verify script logs error and exits with non-zero code. **Run Test (Expect Fail)**.
- [~] T014b [US1] **Run Error Test**: Execute `test_500_exit_code`. **Depends on: T014a**.
- [ ] T015 [US1] **Data Integrity**: Verify `data/raw/gdelt_events.csv` and `data/raw/google_trends.csv` have non-empty rows for target date range; verify MD5 checksums match recorded values. **Output**: Print validation status or exit non-zero on failure. **Depends on: T012c, T013c**. <!-- FAILED: unspecified -->
- [~] T037 [US1] **Update State File**: Read `data/raw/.checksums.json` and update `state/projects/PROJ-487-the-impact-of-social-media-doomscrolling.yaml` `artifact_hashes` map with the checksums for `gdelt_events.csv` and `google_trends.csv`. **Depends on: T012c, T013c**.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Data Preprocessing (Priority: P2)

**Goal**: Clean, normalize, and align retrieved time-series data to daily resolution, ensuring stationarity.

**Independent Test**: Run preprocessing script on raw CSVs; verify output has no missing values, aligned timestamps, and passes ADF stationarity checks (or is differenced).

### Implementation for User Story 2 (TDD Cycle: Write Test -> Implement)

- [X] T016 [P] [US2] **Write Test**: Unit test for timestamp alignment (intersection logic) in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/code/tests/test_preprocess.py`. **Function Name**: `test_timestamp_alignment_intersection`. **Mock**: Two DataFrames with different date ranges (e.g., 2020-01 to 2020-06 vs 2020-03 to 2020-09). **Assertion**: Verify the output DataFrame contains only dates present in both (2020-03 to 2020-06) and preserves zero values. **Run Test (Expect Fail)**.
- [X] T017 [P] [US2] **Write Test**: Unit test for ADF test and differencing logic in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/code/tests/test_preprocess.py`. **Function Name**: `test_adf_differencing`. **Mock**: A non-stationary series (e.g., random walk). **Assertion**: Verify the function detects non-stationarity (p >= 0.05) and returns the differenced series which passes ADF. **Run Test (Expect Fail)**.
- [~] T018 [US2] **Implement Alignment**: Implement timestamp alignment in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/code/data/preprocess.py`: align to daily intervals (intersection), **interpolate ONLY null/missing values (NaN) using linear interpolation; DO NOT interpolate zero-event counts (treat 0 as a valid data point and skip during interpolation)**. Read from `data/raw/gdelt_events.csv` and `data/raw/google_trends.csv`. **Note**: This task enforces Spec FR-002 (linear interpolation) over Plan.md's "forward fill" note; see T036 for plan kickback. **Depends on: T012c, T013c**.
- [~] T019a [US2] **Implement ADF**: Implement Augmented Dickey-Fuller test function in `preprocess.py`: return p-value and stationarity status. **Depends on: T018**.
- [~] T019b [US2] **Implement Differencing**: Implement differencing loop in `preprocess.py`: if p ≥ 0.05, apply differencing until stationary. Then proceed to T020 for normalization. **Depends on: T019a**.
- [ ] T020a [US2] **Implement Z-Score**: Implement z-score normalization function in `preprocess.py`: return z-scored values for output to `data/processed/stationarity_check.csv` with columns [date, news_zscore, anxiety_zscore]. **Depends on: T019b**.
- [ ] T020b [US2] **Apply and Save**: Apply z-score normalization and save to `data/processed/stationarity_check.csv` with columns [date, news_zscore, anxiety_zscore]. **Depends on: T020a**. <!-- FAILED: unspecified -->
- [ ] T021 [US2] **Save Aligned Data**: Save aligned, stationary, normalized data to `data/processed/aligned_timeseries.csv` and `data/processed/stationarity_check.csv`. **Depends on: T018, T019b, T020b**.
- [~] T022 [US2] **Implement Data Length Check**: Implement validation in `preprocess.py` to exit with code 1 and message "Insufficient data for Granger causality" if time-series length < 20. **Depends on: T018**.
- [ ] T023 [US2] **Post-Interpolation Completeness Check**: Verify `data/processed/aligned_timeseries.csv` has ≥95% data completeness (per Spec SC-001) after interpolation. **Calculation**: (Count of non-null rows) / (Total days in the aligned intersection range). **Output**: Print validation status or exit non-zero if failed. **Depends on: T021, T012c, T013c**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis & Reporting (Priority: P3)

**Goal**: Compute correlation, perform Granger causality tests with wide lag window, conduct sensitivity analysis, and generate visualizations.

**Independent Test**: Execute analysis script; verify output reports contain correlation values, p-values (fixed-sweep), and plot images.

### Implementation for User Story 3 (TDD Cycle: Write Test -> Implement)

- [X] T024 [P] [US3] **Write Test**: Unit test for correlation calculation in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/code/tests/test_analyze.py`. **Function Name**: `test_correlation_calculation`. **Mock**: Two perfectly correlated series (y=x) and two uncorrelated series (y=random). **Assertion**: Verify Pearson coefficient is ~1.0 for the first and ~0.0 for the second. **Run Test (Expect Fail)**.
- [ ] T025 [P] [US3] **Write Test**: Unit test for Granger causality fixed-sweep (lags {1, 2, 3, 7, 14}) in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/code/tests/test_analyze.py`. **Function Name**: `test_granger_fixed_sweep`. **Mock**: A dataset where lag 1 is significant (p=0.001) and lag 14 is not (p=0.5). **Assertion**: Verify the function returns a list of results with correct p-values for each lag. **Run Test (Expect Fail)**.
- [ ] T026 [P] [US3] **Implement Correlation**: Implement correlation analysis in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/code/data/analyze.py`: compute Pearson and Spearman coefficients with p-values. Read from `data/processed/aligned_timeseries.csv`. **Depends on: T021**.
- [ ] T027a [P] [US3] **Implement Granger Function**: Implement `run_granger_lag(lag)` function in `analyze.py`: perform Granger causality test for a single lag. **Depends on: T021**.
- [ ] T027b [US3] **Implement Sweep Loop**: Implement fixed-sweep loop in `analyze.py`: iterate lags {1, 2, 3, 7, 14} and collect results. **Depends on: T027a**.
- [ ] T027c [US3] **Serialize Results**: Save Granger results to `data/processed/granger_results.csv` with columns: `lag`, `p_value`, `is_significant`. **Depends on: T027b**.
- [ ] T028 [P] [US3] **Implement Sensitivity Analysis**: Implement sensitivity analysis in `analyze.py`: Calculate the significance rate (count of lags in {1, 2, 3, 7, 14} where p < 0.01 **after Bonferroni correction**) and report this rate. Read from `data/processed/granger_results.csv`. **Depends on: T027c**.
- [ ] T029a [P] [US3] **Implement Statistical Validity Check**: Verify at least one lag in the specific set {1, 2, 3, 7, 14} has p < 0.01 (Bonferroni-corrected alpha α = 0.05 / 5 = 0.01) as per **Spec SC-002**. **Criterion**: Minimum p-value across the set < 0.01. **Depends on: T027c**.
- [ ] T029b [US3] **Report Result**: Report the Bonferroni check result in the final analysis report (as a 'Statistical Validity' section). If condition fails, **exit with non-zero code and flag a critical failure state in the report (Add a red banner to the PDF)**. **Depends on: T029a, T027c**.
- [ ] T030a [US3] **Generate Plots**: Implement plot generation in `analyze.py`: create lag plots, correlation heatmaps, sensitivity summaries. Save to `data/reports/figures/`. **Depends on: T029b**.
- [ ] T030b [US3] **Assemble PDF**: Implement report generation in `analyze.py`: create `data/reports/analysis_report.pdf` using `reportlab` with images from `data/reports/figures/`. **Depends on: T030a**.
- [ ] T031 [US3] **Ensure CPU Feasibility**: Ensure all analysis runs on CPU-only environment within ≤ 6 hours. **Verification**: Run `nvidia-smi` (expect exit code 1 or "command not found") and verify `torch.cuda.is_available()` returns `False` in the Python script. **Depends on: T030b**.
- [ ] T036 [US3] **Update Plan for Kickback**: Update `projects/PROJ-487-the-impact-of-social-media-doomscrolling/specs/001-news-volume-anxiety/plan.md` to explicitly acknowledge the Spec's mandatory Bonferroni requirement and fixed-sweep lags, overriding the Plan's previous "AIC/BIC" constraint. **Action**: Add a "Plan Kickback" section in `plan.md` stating: "Plan updated to comply with Spec FR-005/SC-002: Bonferroni correction and fixed-sweep lags {1, 2, 3, 7, 14} are mandatory." **Depends on: T029b**.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] **Create Documentation**: Update README.md with CLI usage and create `quickstart.md` with environment setup steps in `projects/PROJ-487-the-impact-of-social-media-doomscrolling/`.
- [ ] T033a [P] **Refactor Utils**: Extract `validate_data` function to `utils/validation.py` and ensure all data loading uses it.
- [ ] T033b [P] **Cleanup Code**: Remove unused imports and variables in `code/`.
- [ ] T034 [P] **Additional Tests**: Additional unit tests for edge cases (zero-event days, API failures) in `code/tests/`.
- [ ] T035 [P] **Run Quickstart**: Run `quickstart.md` validation to ensure full pipeline reproducibility (depends on T032 completion).

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (T012c, T013c)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 processed data (T021)

### Within Each User Story

- **TDD Cycle**: Write Test (T010, T011, etc.) -> Run Test (Expect Fail) -> Implement (T012, T013, etc.) -> Verify Test (Pass)
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
Task: "Write Test: Unit test for GDELT API retry logic in code/tests/test_fetch_gdelt.py"
Task: "Write Test: Unit test for Google Trends keyword validation in code/tests/test_fetch_google_trends.py"

# Launch all models for User Story 1 together:
Task: "Implement GDELT fetch logic in code/data/fetch_gdelt.py"
Task: "Implement Google Trends fetch logic in code/data/fetch_google_trends.py"
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
- **TDD Order**: Tests (Write & Run Fail) are listed BEFORE Implementation in the task list to reflect the "Write-Run-Fail-Implement" cycle.
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CPU Feasibility**: All tasks MUST run on 2-core CPU, ≤7GB RAM, ≤6h runtime. No GPU/CUDA.
- **Data Integrity**: All data must be from real sources (GDELT, Google Trends). No synthetic data.
- **Statistical Rigor**: Use fixed-sweep lags {1, 2, 3, 7, 14} and Bonferroni correction (α=0.01) as mandated by Spec FR-005 and SC-002.
- **Spec vs Plan Note**: This task list strictly follows Spec FR-005/SC-002 (Bonferroni, fixed-sweep), overriding conflicting instructions in plan.md. Plan.md has been amended to acknowledge this override (see T036).
- **Plan Kickback**: Flagged for plan kickback due to conflict between Plan.md (AIC/BIC) and Spec.md (Fixed Sweep/Bonferroni).