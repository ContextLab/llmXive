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

- [ ] T001 Create project structure: `mkdir -p data/raw data/processed code tests code/contracts`
- [ ] T002 Create `requirements.txt` at root with: `numpy, scipy, pandas, scikit-learn, matplotlib, seaborn, pyyaml, pytest, pydantic`
- [ ] T003 [P] Create `.flake8` and `pyproject.toml` with black/flake8 settings (max-line-length=88, exclude=venv)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/config.yaml` with keys: `seed: 42`, `permutations: 1000`, `window_size: 12`, `stride: 1`, `alpha: 0.01`
- [ ] T005 [P] Create `contracts/config.schema.yaml` and implement validation in `code/main.py` using `pydantic`
- [ ] T006 Create `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` for data integrity
- [X] T007 Setup logging infrastructure in `code/__init__.py` to record runtime params and seeds (FR-009)
- [X] T008 Implement synthetic data generator in `code/synthetic_data.py` for unit tests ONLY. MUST generate data with: (a) missing weeks (NaNs), (b) constant segments (zero variance), and (c) outliers. Must NOT be used for final report; reference E-NO-DATA fallback.
- [~] T009 Define `E-NO-DATA` exception class in `code/exceptions.py`. Implement a validation script in `code/main.py` that checks for the existence of `data/raw/fluview_ili.csv` and `data/raw/ground_truth_events.csv`. If either is missing, raise `E-NO-DATA` with log message "Pipeline halted: Real CDC data unavailable" and exit. (FR-001, FR-006, Constitution Principle VI)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Automated shift detection for public‑health analysts (Priority: P1) 🎯 MVP

**Goal**: Run a reproducible pipeline that flags weeks where the ILI distribution has changed using MMD, producing `flags.csv` and `report.pdf`.

**Independent Test**: Execute the full pipeline on the FluView dataset and verify that a CSV of flagged weeks is produced together with a summary report containing the required metrics.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation. Execution depends on code existing.**
> **Prerequisite**: T008 (synthetic data generator) must be complete.

- [X] T010 [P] [US1] Write unit test `tests/unit/test_mmd.py` with function `test_mmd_stat_correctness` using synthetic data from T008 to verify MMD logic.
- [ ] T011 [P] [US1] Write integration test `tests/integration/test_pipeline.py` with function `test_full_pipeline_flags` to verify full flow. <!-- FAILED: unspecified -->

### Implementation for User Story 1

- [~] T012a [US1] Implement `code/download_data.py` to fetch CDC FluView ILI CSV from the canonical CDC source (e.g., ` API or verified direct CSV) and save to `data/raw/fluview_ili.csv`. **MUST** verify file checksum against a known hash if available, or log the exact URL and retrieval date. Do NOT use third-party mirrors (NAB) as the primary source. (FR-001, Constitution Principle VI)
- [~] T012b [US1] Implement `code/download_data.py` (or separate function) to fetch CDC Virological/Hospitalization ground truth from a verified CDC URL (e.g., specific API endpoint or direct CSV). **MUST NOT** allow a fallback to a local file provided by the user. If the fetch fails, raise `E-NO-DATA` exception. Save to `data/raw/ground_truth_events.csv` with columns `start_week, end_week, event_name`. (FR-006, Constitution Principle IV)
- [X] T013 [US1] Implement `code/preprocess.py` to handle missing weeks (remove), log-transform, and standardize (FR-002)
- [X] T014 [US1] Implement `code/mmd_detector.py` with Gaussian-kernel MMD, multi-week windows, and dynamic permutation count. **Internal Logic**: Include a runtime monitor that checks elapsed time. If time > 30 mins, reduce `permutations` in config (e.g., halve it), log "Permutations reduced to X", and re-calculate the MMD statistic. **Do NOT** change the Bonferroni threshold `p < 0.01/N`; the threshold remains strict. (FR-003, FR-004, FR-008)
- [X] T015 [US1] Implement Bonferroni correction in `code/mmd_detector.py`: calculate `N` (number of window pairs) dynamically, apply `p < 0.01/N`, and output `flags.csv`. Ensure `N` is recalculated for each sensitivity run (different window sizes). (FR-004)
- [~] T016 [US1] Implement `code/evaluate.py` to load `data/raw/ground_truth_events.csv`, verify source independence (URL whitelist check, ensure no ILI columns), and parse ±2-week tolerance (FR-006)
- [X] T017 [US1] Implement metrics calculation (precision, recall, detection delay within ±2 weeks) in `code/evaluate.py`
- [X] T018 [US1] Implement `code/report_generator.py` to produce `report.pdf` with metrics (FR-006)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Baseline change‑point comparison (Priority: P2)

**Goal**: Compare MMD performance against Pettitt and Bayesian Online Change-Point Detection (BOCPD).

**Independent Test**: Run the baseline methods on the same pre‑processed series and verify that their detected change points are reported alongside the MMD results.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T020 [P] [US2] Write unit test `tests/unit/test_baselines.py` with function `test_pettitt_rolling_window` for Pettitt rolling-window.
- [ ] T021 [P] [US2] Write unit test `tests/unit/test_baselines.py` with function `test_bocpd_gaussian` for BOCPD.

### Implementation for User Story 2

- [ ] T022 [P] [US2] Implement Pettitt **rolling-window** test in `code/pettitt.py`: window=12, stride=1, compute Pettitt statistic for every window (FR-005)
- [ ] T023 [P] [US2] Implement BOCPD (Gaussian observation model) in `code/bocpd.py` (FR-005)
- [ ] T024 [US2] Integrate baselines execution into `code/main.py` after preprocessing
- [ ] T025 [US2] Output `baselines.csv` containing detected change weeks and statistics (FR-005)
- [ ] T026a [US2] Implement logic in `code/evaluate.py` to compute detection delays from `baselines.csv` alone (independent of MMD)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: Cross-Story Integration (Priority: P2/P3)

**Purpose**: Combine results from US1 and US2 for final comparison and sensitivity analysis.

- [ ] T026b [US1+US2] Implement cross-comparison in `code/evaluate.py`: Load MMD delays (from T017) and Baseline delays (from T026a). Perform a two-sample t-test using `scipy.stats.ttest_ind` on these delay arrays. Report the resulting p-value in `report.pdf` to compare detection delays (SC-004). (FR-005, SC-004)

---

## Phase 6: User Story 3 - Robustness & sensitivity analysis (Priority: P3)

**Goal**: Assess sensitivity to kernel bandwidth, window length, and week-alignment tolerance.

**Independent Test**: Execute the sensitivity module, which reruns the detector over a grid of bandwidths and window lengths, and verify that a `sensitivity.csv` summarising metric variation is produced.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Write unit test `tests/unit/test_sensitivity.py` with function `test_grid_generation` for sensitivity grid generation.

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement `code/sensitivity.py` to handle grid search: bandwidths=[median, cv], windows=[8, 12, 16], output `sensitivity.csv` (FR-007)
- [ ] T030 [US3] Implement week-alignment tolerance sweep (±1, ±2, ±3 weeks) in `code/sensitivity.py` and output `tolerance_sensitivity.csv` with metric variations (FR-010)
- [ ] T031 [US3] Execute sensitivity grid in `code/main.py` (after US1/US2 completion)
- [ ] T032 [US3] Aggregate metrics for all configurations into `sensitivity.csv` (FR-007, FR-010)
- [ ] T033 [US3] Update `report.pdf` to include sensitivity analysis summary and variation plots (SC-005)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Update `quickstart.md` (add run instructions) and `README.md` (add project overview)
- [ ] T036a [P] Refactor `code/mmd_detector.py` to implement vectorized MMD kernel function using NumPy broadcasting.
- [ ] T036b [P] Benchmark `code/mmd_detector.py` before and after vectorization; verify runtime reduction of at least 50% on a standard dataset.
- [ ] T037 [P] Add unit tests `test_constant_series` and `test_outlier_handling` in `tests/unit/` using synthetic data from T008.
- [ ] T038 Run `pytest` in `code/` and verify exit code 0
- [ ] T039 Verify all `data/` artifacts have `sha256sum` and update `state/` JSON with hashes (Constitution Principle V)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Cross-Story Integration (Phase 5)**: Depends on US1 and US2 completion
- **Polish (Final Phase)**: Depends on all desired user stories being complete

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
Task: "Write integration test tests/integration/test_pipeline.py for full flow"

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
- **Data Constraint**: Real CDC data is required for final results; synthetic data is for unit tests only.
- **Data Availability**: If direct CDC URLs for ground truth are unstable, T012b must raise E-NO-DATA; no local fallback allowed.
- **Statistical Integrity**: Bonferroni threshold `p < 0.01/N` is immutable; only permutation count can be adjusted for time.