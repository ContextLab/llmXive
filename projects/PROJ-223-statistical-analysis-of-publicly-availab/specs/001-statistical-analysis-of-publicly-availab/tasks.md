# Tasks: Traffic-Weather Severity Analysis

**Input**: Design documents from `/specs/001-traffic-weather-severity/`
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

- [ ] T001a [P] Create `code/` directory structure (`__init__.py`, `config.py`, `ingest.py`, `model.py`, `diagnostics.py`, `utils.py`, `main.py`)
- [ ] T001b [P] Create `tests/` directory structure (`__init__.py`, `test_ingest.py`, `test_model.py`, `test_diagnostics.py`)
- [ ] T001c [P] Create `data/` directory structure (`raw/`, `processed/`, `reports/`)
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (pinned `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `geopy`, `pyyaml`, `matplotlib`, `seaborn`, `pyarrow`, `h3`)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/config.py` for paths, `random_state=42` seed, and constants
- [~] T005 [P] Implement `code/utils.py` with helper functions for geo-matching and encoding
- [~] T006 [P] Setup `tests/` directory structure with `__init__.py` and `pytest` configuration
- [~] T007b Create `merged_dataset.schema.yaml` contract file defining required fields and types for contract validation
- [~] T008 Configure environment variable management for data paths

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Merging (Priority: P1) 🎯 MVP

**Goal**: Download FARS and NOAA ISD data, merge based on location/time, and produce a unified dataset with ≥85% weather coverage [UNRESOLVED-CLAIM: c_d126a534 — status=not_enough_info].

**Independent Test**: Run ingestion script on a deterministic sample; verify output CSV contains non-null values for `severity`, `precipitation`, `visibility`, `temperature` and matches `merged_dataset.schema.yaml`.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T009 [P] [US1] Unit test for severity encoding logic in `tests/test_ingest.py`
- [~] T010 [P] [US1] Integration test for FARS/NOAA merge logic in `tests/test_ingest.py` (mock URLs or small sample)
- [~] T011 [P] [US1] Contract test verifying `match_method` field population in `tests/test_ingest.py`

### Implementation for User Story 1

- [~] T012 [US1] Implement FARS download and pre-filtering in `code/ingest.py` (use deterministic NHTSA 2022 URL, verify checksums)
- [~] T012b [US1] Implement chunking logic for datasets >7GB in `code/ingest.py` (process in chunks, write intermediate results to disk to prevent OOM)
- [ ] T013 [US1] Implement NOAA ISD download and pre-filtering in `code/ingest.py` (use HuggingFace `noaa/isd-hourly` fallback, filter by proximity)
- [ ] T014 [US1] Implement spatial-temporal merge logic: MUST implement linear interpolation for time gaps between weather stations; fallback to nearest-hour ONLY if interpolation fails; verify output contains `match_method=interpolated` for time-delta > 0 in `code/ingest.py`
- [ ] T015 [US1] Implement severity encoding (=Property, Injury, Fatality) and exclusion logic in `code/ingest.py`
- [ ] T016 [US1] Implement contract validation step to ensure output matches `merged_dataset.schema.yaml` in `code/ingest.py`
- [ ] T017 [US1] Add logging for merge coverage rate (target ≥85%) and exclusion counts in `code/ingest.py`
- [ ] T017b [US1] Implement calculation and verification of SC-001 coverage metric (valid weather records / total FARS records) and verify ≥85% target [UNRESOLVED-CLAIM: c_22e946e3 — status=not_enough_info]; MUST log exclusion counts for records failing proximity check in `code/ingest.py`

**Checkpoint**: At this point, User Story 1 is only considered 'complete' if T017b passes (coverage ≥85% AND exclusion counts logged)

---

## Phase 4: User Story 2 - Ordinal Logistic Regression Modeling (Priority: P2)

**Goal**: Fit an Ordinal Logistic Regression (Cumulative Link Model) to quantify weather influence on severity.

**Independent Test**: Run modeling script; verify output includes coefficients table with odds ratios, AIC/BIC, and Brant test p-value > 0.05.

### Tests for User Story 2

- [ ] T018 [P] [US2] Unit test for model convergence on sample data in `tests/test_model.py`
- [ ] T019 [P] [US2] Integration test for full model fit and coefficient extraction in `tests/test_model.py`

### Implementation for User Story 2

- [ ] T020 [US2] Implement Ordinal Logistic Regression (Cumulative Logit) using `statsmodels.miscmodels.ordinal_model.OrderedModel` in `code/model.py`
- [ ] T021 [US2] Implement model fitting with weather predictors (precip, visibility, temp) and controls (hour, day, road type) in `code/model.py`
- [ ] T022 [US2] Implement extraction of odds ratios with confidence intervals in `code/model.py`
- [ ] T023 [US2] Implement Brant test for proportional odds assumption in `code/model.py`
- [ ] T024 [US2] Add convergence logging and error handling for non-convergence in `code/model.py`
- [ ] T024b [US2] Implement calculation and verification of SC-002 convergence rate (≥95% (Wikipedia: Delta (rocket family), https://en.wikipedia.org/wiki/Delta_(rocket_family)) success within 50 iterations [UNRESOLVED-CLAIM: c_6b6dbdaf — status=not_enough_info]) and fail pipeline if target missed in `code/model.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Model Diagnostics and Visualization (Priority: P3)

**Goal**: Generate diagnostic plots (VIF), perform sensitivity analysis, and validate methodological soundness.

**Independent Test**: Run diagnostics script; verify output includes VIF table (all < 5.0), coefficient plot image, and sensitivity analysis table.

### Tests for User Story 3

- [ ] T025 [P] [US3] Unit test for VIF calculation in `tests/test_diagnostics.py`
- [ ] T026 [P] [US3] Integration test for sensitivity analysis sweep in `tests/test_diagnostics.py`

### Implementation for User Story 3

- [ ] T027 [US3] Implement VIF calculation for all predictors in `code/diagnostics.py`
- [ ] T028 [US3] Implement sensitivity analysis for FR-005/SC-003: Sweep precipitation thresholds across a range of low values. on the *continuous* variable; calculate the *maximum percentage change* in odds ratios across the sweep; verify variation < 15% [UNRESOLVED-CLAIM: c_030f2fe7 — status=not_enough_info]; produce 'stability metric table' in `code/diagnostics.py`
- [ ] T029 [US3] Generate coefficient plot image using `matplotlib`/`seaborn` in `code/diagnostics.py`
- [ ] T030 [US3] Implement logic to flag VIF > 5.0 as a limitation in `code/diagnostics.py`
- [ ] T031 [US3] Generate final associational summary report in `code/diagnostics.py`; MUST include a verification step (e.g., regex scan for causal keywords like 'cause', 'effect', 'determine') to ensure *all* statistics are framed as associational per FR-006

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Documentation updates in `docs/` and `README.md`
- [ ] T033 Code cleanup and refactoring for general optimization, preserving chunking logic in `code/ingest.py` implemented in T012b
- [ ] T034a [P] Implement chunking logic in `code/ingest.py` to ensure memory usage < 6GB peak [UNRESOLVED-CLAIM: c_4c5ebbc1 — status=not_enough_info] (if not already covered by T012b)
- [ ] T034b [P] Profile full pipeline execution and {{claim:c_7a6ad4b8}} (Wikipedia: Dhurandhar, https://en.wikipedia.org/wiki/Dhurandhar); record duration in `data/reports/runtime.log`
- [ ] T035 [P] Additional unit tests for edge cases (missing severity, interpolation) in `tests/`
- [ ] T036 Run `quickstart.md` validation and verify all artifacts checksummed

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output

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
# Launch all tests for User Story 1 together:
Task: "Unit test for severity encoding logic in tests/test_ingest.py"
Task: "Integration test for FARS/NOAA merge logic in tests/test_ingest.py"
Task: "Contract test verifying match_method field population in tests/test_ingest.py"

# Launch implementation tasks (sequentially due to data flow):
Task: "Implement FARS download and pre-filtering in code/ingest.py"
Task: "Implement NOAA ISD download and pre-filtering in code/ingest.py"
Task: "Implement spatial-temporal merge logic in code/ingest.py"
Task: "Implement severity encoding and exclusion logic in code/ingest.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (ensure T017b passes)
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