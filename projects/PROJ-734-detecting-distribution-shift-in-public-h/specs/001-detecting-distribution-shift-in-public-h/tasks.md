# Tasks: Detecting Distribution Shift in Public Health Surveillance Data via Kernel Two‑Sample Tests

**Input**: Design documents from `/specs/001-detect-distribution-shift/`
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

- [X] T001 Create project structure: `mkdir -p data/raw data/processed code tests code/contracts`
- [X] T002 Create `requirements.txt` at root with: `numpy, scipy, pandas, scikit-learn, matplotlib, seaborn, pyyaml, pytest, pydantic`
- [X] T003 [P] Create `.flake8` and `pyproject.toml` with black/flake8 settings (max-line-length=88, exclude=venv)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin.
**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 Create `code/config.yaml` with keys: `seed: 42`, `permutations: 1000`, `window_size: 12`, `stride: 1`, `alpha: 0.01`
- [X] T005 [P] Create `contracts/config.schema.yaml` and implement validation in `code/main.py` using `pydantic`. **Status**: Implemented. Validates all config keys and types.
- [X] T006 Create `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` for data integrity. **Status**: Implemented. Defines schema for FluView and Ground Truth datasets.
- [X] T007 Setup logging infrastructure in `code/__init__.py` to record runtime params and seeds (FR-009)
- [X] T008 Implement synthetic data generator in `code/synthetic_data.py` for unit tests ONLY. MUST generate data with: (a) missing weeks (NaNs), (b) constant segments (zero variance), and (c) outliers. Must NOT be used for final report; reference E-NO-DATA fallback.
- [X] T009 Define `E-NO-DATA` exception class in `code/exceptions.py`. Implement a validation script in `code/main.py` that checks for the existence of `data/raw/fluview_ili.csv` and `data/raw/ground_truth_events.csv`. If either is missing, raise `E-NO-DATA` with log message "Pipeline halted: Real CDC data unavailable" and exit. (FR-001, FR-006, Constitution Principle VI)
- [X] T012a [P] [US1] Implement `code/download_data.py` to fetch CDC FluView ILI CSV from the verified NAB repository (Numenta Anomaly Benchmark) which hosts the canonical CDC FluView dataset: `. Save to `data/raw/fluview_ili.csv`. **MUST** verify file checksum against a known hash if available, or log the exact URL and retrieval date to `data/raw/.metadata.json`. Do NOT use third-party mirrors as primary source. (FR-001, Constitution Principle VI)
- [X] T012b [P] [US1] Implement `code/download_data.py` (or separate function) to fetch CDC Virological/Hospitalization ground truth from the verified NAB repository: `. Save to `data/raw/ground_truth_events.csv` with columns `start_week, end_week, event_name`. **MUST NOT** allow a fallback to a local file provided by the user. If the fetch fails, raise `E-NO-DATA` exception. (FR-006, Constitution Principle IV)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Automated shift detection for public‑health analysts (Priority: P1) 🎯 MVP

**Goal**: Run a reproducible pipeline that flags weeks where the ILI distribution has changed using MMD, producing `flags.csv` and `report.pdf`.

**Independent Test**: Execute the full pipeline on the FluView dataset and verify that a CSV of flagged weeks is produced together with a summary report containing the required metrics.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation. Execution depends on code existing.**
> **Prerequisite**: T008 (synthetic data generator) must be complete.

- [X] T010 [P] [US1] Write unit test `tests/unit/test_mmd.py` with function `test_mmd_stat_correctness` using synthetic data from T008 to verify MMD logic.
- [X] T011 [US1] Write integration test `tests/integration/test_pipeline.py` with function `test_full_pipeline_flags` to verify full flow. **Dependency**: Requires T012a/b (data download) and T013-T018 (implementation) to be complete.

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/preprocess.py` to handle missing weeks (remove), log-transform, and standardize (FR-002). **Dependency**: T012a.
- [X] T014 [US1] Implement `code/mmd_detector.py` with Gaussian-kernel MMD, multi-week windows, and dynamic permutation count. **Internal Logic**: Include a runtime monitor that checks elapsed time. If time > 30 mins, reduce `permutations` in config (e.g., halve it), log "Permutations reduced to X", and re-calculate the MMD statistic. **MUST** enforce `min_permutations=100` to preserve statistical validity. Do NOT change the Bonferroni threshold `p < 0.01/N`. (FR-003, FR-004, FR-008)
- [X] T015 [US1] Implement Bonferroni correction in `code/mmd_detector.py`: calculate `N` (number of window pairs) dynamically, apply `p < 0.01/N`, and output `flags.csv`. Ensure `N` is recalculated for each sensitivity run (different window sizes). (FR-004)
- [X] T016 [US1] Implement `code/evaluate.py` to load `data/raw/ground_truth_events.csv`, verify source independence (URL whitelist check: `['', 'https://ftp.cdc.gov']`), and parse ±2-week tolerance. **Dependency**: T012b. (FR-006)
- [X] T017 [US1] Implement metrics calculation (precision, recall, detection delay within ±2 weeks) in `code/evaluate.py`
- [X] T018 [US1] Implement `code/report_generator.py` to produce `report.pdf` with metrics (FR-006)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Baseline change‑point comparison (Priority: P2)

**Goal**: Compare MMD performance against Pettitt and Bayesian Online Change-Point Detection (BOCPD).

**Independent Test**: Run the baseline methods on the same pre‑processed series and verify that their detected change points are reported alongside the MMD results.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Write unit test `tests/unit/test_baselines.py` with function `test_pettitt_rolling_window` for Pettitt rolling-window.
- [X] T021 [P] [US2] Write unit test `tests/unit/test_baselines.py` with function `test_bocpd_gaussian` for BOCPD.

### Implementation for User Story 2

- [X] T022 [P] [US2] Implement Pettitt **rolling-window** test in `code/pettitt.py`: window=12, stride=1, compute Pettitt statistic for every window (FR-005)
- [X] T023 [P] [US2] Implement BOCPD (Gaussian observation model) in `code/bocpd.py` (FR-005)
- [X] T025 [US2] Output `baselines.csv` containing detected change weeks and statistics (test statistic, posterior run-length). **Schema**: `method, week_id, statistic, run_length`. (FR-005)
- [X] T026a [US2] Implement logic in `code/evaluate.py` to compute detection delays from `baselines.csv` alone (independent of MMD). **Dependency**: T025.
- [X] T024 [US2] Integrate baselines execution into `code/main.py` after preprocessing

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: Cross-Story Integration (Priority: P2/P3)

**Purpose**: Combine results from US1 and US2 for final comparison and sensitivity analysis.

- [X] T026b [US1+US2] Implement cross-comparison in `code/evaluate.py`: Load MMD delays (from T017) and Baseline delays (from T026a). Perform a two-sample t-test using `scipy.stats.ttest_ind` on these delay arrays. Report the resulting p-value in `report.pdf` to compare detection delays (SC-004). (FR-005, SC-004)

---

## Phase 6: User Story 3 - Robustness & sensitivity analysis (Priority: P3)

**Goal**: Assess sensitivity to kernel bandwidth, window length, and week-alignment tolerance.

**Independent Test**: Execute the sensitivity module, which reruns the detector over a grid of bandwidths and window lengths, and verify that a `sensitivity.csv` summarising metric variation is produced.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [P] [US3] Write unit test `tests/unit/test_sensitivity.py` with function `test_grid_generation` for sensitivity grid generation.

### Implementation for User Story 3

- [X] T029 [P] [US3] Implement `code/sensitivity.py` to handle grid search: bandwidths=[median, cv], windows=[multiple values including 12 and 16], output `sensitivity.csv` (FR-007)
- [X] T030 [US3] Implement week-alignment tolerance sweep (±1, ±2, ±3 weeks) in `code/sensitivity.py` and output `tolerance_sensitivity.csv` with metric variations (FR-010)
- [X] T031a [P] [US3] Implement `code/sensitivity.py` function `generate_grid()` to create the parameter combinations (2 bandwidths x 3 windows x 3 tolerances).
- [X] T031b [US3] Execute sensitivity grid in `code/main.py` using the grid from T031a. **Dependency**: T031a.
- [X] T032 [US3] Aggregate metrics for all configurations into `sensitivity.csv`. **Schema**: `bandwidth_type, window_size, tolerance_weeks, precision, recall, detection_delay, fpr`. (FR-007, FR-010)
- [X] T033 [US3] Update `report.pdf` to include sensitivity analysis summary and variation plots: (1) Line plot of precision vs window size, (2) Heatmap of recall vs bandwidth. (SC-005)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T034 [P] Update `quickstart.md` (add run instructions) and `README.md` (add project overview)
- [X] T036a [P] Refactor `code/mmd_detector.py` to implement vectorized MMD kernel function using NumPy broadcasting.
- [X] T036b [P] Benchmark `code/mmd_detector.py` before and after vectorization; verify runtime reduction of at least 50% on a standard dataset.
- [X] T037 [P] Add unit tests `test_constant_series` and `test_outlier_handling` in `tests/unit/` using synthetic data from T008.
- [X] T038 Run `pytest` in `code/` and verify exit code 0
- [X] T039 [P] Verify all `data/` artifacts have `sha256sum` and update `state/projects/PROJ-734-detecting-distribution-shift-in-public-h.yaml` with hashes. **Logic**: If data files are missing (E-NO-DATA), hash the `data/raw/.metadata.json` file instead and log "Data unavailable, hashed metadata". (Constitution Principle V)

---

## Phase O: Review & Final Validation

**Purpose**: Address specific reviewer concerns regarding data provenance, statistical rigor, and edge-case handling before final merge.

- [ ] T040 [US1] [Review] Implement explicit "Data Source Verification" step in `code/download_data.py`. If the CDC URL returns a 404 or 500, the script MUST raise `E-NO-DATA` immediately. **MUST NOT** contain any `try/except` block that falls back to `synthetic_data.py` or a local mock file. Add a comment block citing Constitution Principle VI and FR-001. (Review Concern: Preventing silent synthetic fallbacks)
- [ ] T041 [US1] [Review] Update `code/preprocess.py` to explicitly handle the "Constant Series" edge case. If `std(log_ili) == 0` over a window, the script MUST raise a `ValueError` with message "Zero variance detected in window; cannot compute MMD". Log this event and skip the window rather than producing a NaN p-value. (Review Concern: Handling constant ILI series)
- [ ] T042 [US1] [Review] Enhance `code/evaluate.py` to implement the "Extreme Outlier" handling strategy. Before calculating metrics, scan for ILI values > 3 standard deviations from the median. If found, log a warning "Outlier detected: Week X, Value Y" and apply a robust scaling (e.g., Winsorization at 99th percentile) ONLY for the baseline comparison, while keeping the MMD test on the raw log-transformed data as per FR-002. Document this divergence in `report.pdf`. (Review Concern: Outlier robustness)
- [ ] T043 [US2] [Review] Verify Pettitt implementation in `code/pettitt.py` uses a sliding window of 12 weeks with stride 1, matching the MMD window configuration exactly. Add a unit test `test_pettitt_window_alignment` to ensure the Pettitt statistic is computed for the exact same time intervals as the MMD detector. (Review Concern: Baseline method alignment)
- [ ] T044 [US3] [Review] Update `code/sensitivity.py` to ensure the "Cross-Validated Bandwidth" strategy uses a 5-fold cross-validation on the *training* split of the window pairs, not the entire dataset, to prevent data leakage in the sensitivity analysis. (Review Concern: Preventing data leakage in CV bandwidth selection)
- [ ] T045 [US1] [Review] Add a "Reproducibility Manifest" generation step in `code/main.py`. After the pipeline completes, generate `data/processed/reproducibility_manifest.json` containing: exact git commit hash, full `requirements.txt` content, random seed, and the exact URLs used for data download. (Review Concern: Reproducibility verification)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Cross-Story Integration (Phase 5)**: Depends on US1 and US2 completion
- **Polish (Phase N)**: Depends on all desired user stories being complete
- **Review (Phase O)**: Depends on Phase N completion; final gate before merge

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Independent of US1 implementation (except for T026b)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services (Data loading before processing)
- Services before endpoints (Processing before evaluation)
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
Task: "Write unit test tests/unit/test_mmd.py for MMD logic (requires T008)"
Task: "Write integration test tests/integration/test_pipeline.py for full flow (requires T012-T018)"

# Launch core implementation for User Story 1 together:
Task: "Implement code/download_data.py to fetch CDC FluView ILI CSV (canonical source)"
Task: "Implement code/preprocess.py to handle missing weeks, log-transform, and standardize"
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
4. Add Cross-Story Integration → Test independently → Deploy/Demo
5. Add User Story 3 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (MMD Core)
 - Developer B: User Story 2 (Baselines - T022, T023, T025, T026a)
 - Developer C: User Story 3 (Sensitivity)
3. Stories complete and integrate independently (T026b is the final integration point)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CPU Constraint**: Ensure no task requires GPU or >7GB RAM; use permutation reduction if needed (FR-008) without altering statistical thresholds.
- **Data Constraint**: Real CDC data (via NAB benchmark) is required for final results; synthetic data is for unit tests only.
- **Data Availability**: If direct CDC URLs for ground truth are unstable, T012b must raise E-NO-DATA; no local fallback allowed.
- **Statistical Integrity**: Bonferroni threshold `p < 0.01/N` is immutable; only permutation count can be adjusted for time (min 100).
- **Review Compliance**: Tasks T040-T045 address specific reviewer concerns regarding data provenance, edge-case handling, and statistical rigor. These must be completed before final merge.
