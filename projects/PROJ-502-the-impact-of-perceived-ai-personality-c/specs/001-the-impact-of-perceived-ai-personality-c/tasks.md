# Tasks: The Impact of Perceived AI Personality Consistency on User Trust

**Input**: Design documents from `/specs/001-ai-personality-consistency-trust/`
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

- [X] T001a Create `code/` directory (`code/__init__.py`)
- [ ] T001b Create `tests/` directory (`tests/__init__.py`)
- [ ] T001c Create `tests/unit/` directory
- [ ] T001d Create `tests/contract/` directory
- [ ] T001e Create `tests/integration/` directory
- [ ] T001f Create `data/` directory (`data/raw/`, `data/processed/`)
- [~] T001g Create `output/` directory (`output/figures/`, `output/reports/`)
- [X] T002a Create `code/requirements.txt` with pinned versions: datasets==2.14.0 [UNRESOLVED-CLAIM: c_df95789a — status=not_enough_info], pandas==2.0.3 [UNRESOLVED-CLAIM: c_1d2fa06d — status=not_enough_info], numpy==1.24.3 [UNRESOLVED-CLAIM: c_2a36a529 — status=not_enough_info], scikit-learn==1.3.0 [UNRESOLVED-CLAIM: c_2d2a80ac — status=not_enough_info], statsmodels==0.14.0 [UNRESOLVED-CLAIM: c_6daca785 — status=not_enough_info], torch==2.0.1+cpu [UNRESOLVED-CLAIM: c_06d9e788 — status=not_enough_info], transformers==4.30.2 [UNRESOLVED-CLAIM: c_5f15c112 — status=not_enough_info], seaborn==0.12.2 [UNRESOLVED-CLAIM: c_66932fd3 — status=not_enough_info], matplotlib==3.7.2 [UNRESOLVED-CLAIM: c_2a89cbfd — status=not_enough_info], pyyaml==6.0 [UNRESOLVED-CLAIM: c_7f1e2cb0 — status=not_enough_info], pytest==7.4.0 [UNRESOLVED-CLAIM: c_e4b6de38 — status=not_enough_info], pytest-cov==4.1.0 [UNRESOLVED-CLAIM: c_16c2e4d8 — status=not_enough_info]
- [~] T002b Initialize git repository in the project root <!-- FAILED: unspecified -->
- [~] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/config.py` for environment variable loading (including fallback model config)
- [X] T005 [P] Implement `code/utils.py` with dynamic batch size calculator (ensuring <7GB RAM usage)
- [ ] T006 [P] Implement `code/utils.py` memory monitoring wrapper for batch processing loops
- [ ] T007 Create base data schemas in `specs/contracts/dataset.schema.yaml` and `specs/contracts/metrics.schema.yaml`
- [ ] T008 Setup logging infrastructure in `code/utils.py` (error logging for skipped responses)
**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Session Extraction (Priority: P1) 🎯 MVP

**Goal**: Download {{claim:c_3ed349d2}} (Wikidata Q115139582, https://www.wikidata.org/wiki/Q115139582), filter for valid sessions (≥3 turns), and persist clean data.

**Independent Test**: Run ingestion script on a small subset; verify sessions <3 turns are excluded, sessions ≥3 turns included, no null text, and output matches schema.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Unit test for session filtering logic in `tests/unit/test_ingestion.py` (verify <3 turns excluded, ≥3 included)
- [ ] T010 [P] [US1] Contract test for data output schema in `tests/contract/test_schemas.py` (function: `test_sessions_schema_matches_yaml` validating `specs/contracts/dataset.schema.yaml`)
- [ ] T011 [P] [US1] Integration test for download retry logic in `tests/integration/test_end_to_end.py` (mock `datasets.load_dataset` to raise HTTPError on first call; assert retry count == 3 [UNRESOLVED-CLAIM: c_0bec590c — status=not_enough_info] and final state is failure)

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `code/ingestion.py` to download {{claim:c_3ed349d2}} from HuggingFace `datasets` library
- [ ] T013 [US1] Implement session filtering logic in `code/ingestion.py` (keep only sessions with ≥3 turns [UNRESOLVED-CLAIM: c_19582a1d — status=not_enough_info])
- [ ] T014 [US1] Implement null-value check and error handling in `code/ingestion.py` (fail gracefully if row count is 0)
- [ ] T016 [US1] Persist filtered data to `data/processed/sessions.json` (or CSV)
- [ ] T015 [US1] Implement checksumming of raw data in `code/ingestion.py` (Cryptographic hash validation

The research question investigates whether cryptographic hash functions can ensure data integrity in distributed systems. The method involves a systematic literature review and comparative analysis of hash algorithm properties. ({{claim:c_aad724a3}} (golden_ratio, https://en.wikipedia.org/wiki/Golden_ratio);) on raw download BEFORE filtering, placed after T016 execution in pipeline)
- [ ] T017 [US1] Add logging for download status and filtering results

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Engagement and Consistency Metric Computation (Priority: P2)

**Goal**: Compute "Consistency Score" (sentiment variance + lexical diversity) and "Engagement Indicators" (interaction length, session count). *Note: 'Trust' and 'Session Frequency (days)' are replaced per Plan constraints due to missing timestamps.*

**Independent Test**: Run on hardcoded reference data; verify metrics match pre-calculated values within 0.01 tolerance [UNRESOLVED-CLAIM: c_5a53edfa — status=not_enough_info].

### Tests for User Story 2

- [ ] T018 [P] [US2] Unit test for Type-Token Ratio (TTR) calculation in `tests/unit/test_metrics.py`
- [ ] T019 [P] [US2] Unit test for sentiment variance calculation (including zero-variance edge case) in `tests/unit/test_metrics.py`
- [ ] T020 [P] [US2] Unit test for Lagged Engagement Indicator logic in `tests/unit/test_metrics.py` (Given input: list of turns [T1, T2, T3]; assert output: predictor=T1, outcome=T2,T3)
- [ ] T021 [P] [US2] Contract test for metrics output schema in `tests/contract/test_schemas.py`

### Implementation for User Story 2

- [ ] T022 [P] [US2] Implement `code/metrics.py` with sentiment analysis using `{{claim:c_bbc37927}} (2511.22313, 2511.22313)` (CPU mode) and fallback model loading logic (via config/env var) if default fails
- [ ] T024 [US2] Implement Type-Token Ratio (TTR) calculation for lexical diversity in `code/metrics.py`
- [ ] T025[US2] Implement variance aggregation logic and 'Session Count' (total sessions per user) calculation in `code/metrics.py`. *Note: 'Session Frequency (days)' is NOT computable due to missing timestamps; replaced by 'Session Count' (column name: session_count). Spec FR-004/SC-001 acknowledged as unfulfillable.*
- [ ] T025b [US2] Implement sequential grouping logic for Lagged calculation (Turns 1 to N-1 vs 2 to N) in `code/metrics.py`
- [ ] T026 [US2] Implement "Lagged Engagement Indicator" calculation (predictor: Turns 1 to N-1, outcome: Turns 2 to N) in `code/metrics.py`. *Note: Strictly implements 'Within-Session Lag' as a proxy for FR-009's cross-session logic, due to lack of longitudinal user IDs in {{claim:c_3ed349d2}}.*
- [ ] T027 [US2] Implement error handling for missing sentiment scores (skip response, log error, continue) in `code/metrics.py`
- [ ] T028 [US2] Integrate dynamic batching (from T005) into the metric computation loop in `code/metrics.py`
- [ ] T029 [US2] Persist computed metrics to `data/processed/metrics.csv`
- [ ] T030 [US2] Add logging for skipped responses and batch progress

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Reporting (Priority: P3)

**Goal**: Perform Poisson Regression for count data (Session Count) and generate visualizations. *Note: Survival Analysis (FR-005) is impossible without time-to-event data; replaced by Poisson Regression.*

**Independent Test**: Run on synthetic mock data (r=0.5, n=1000); verify coefficients and p-values match theoretical results within 5%.

### Tests for User Story 3

- [ ] T031 [P] [US3] Unit test for Poisson Regression model fitting on synthetic data in `tests/unit/test_analysis.py` (generate data with r=0.5, n=1000; assert coefficients match within 5% tolerance [UNRESOLVED-CLAIM: c_49f3c317 — status=not_enough_info])
- [ ] T032 [P] [US3] Unit test for Regression logic in `tests/unit/test_analysis.py` (function: `test_regression_fit_returns_expected_model`; input: list of predictors/outcomes; assert output: GLM object with expected parameters)
- [ ] T033 [P] [US3] Integration test for end-to-end visualization generation in `tests/integration/test_end_to_end.py`

### Implementation for User Story 3

- [ ] T034 [P] [US3] Implement `code/analysis.py` with GLM (Poisson/Negative Binomial) for count data (interaction length)
- [ ] T035 [US3] Implement `code/analysis.py` with Poisson Regression for 'Session Count' (replacing impossible Survival Analysis) in `code/analysis.py`. *Note: Spec FR-005/SC-002 acknowledged as unfulfillable; Poisson Regression used as valid alternative for count data.*
- [ ] T036 [US3] Implement correlation coefficient (r) and p-value calculation for consistency vs. engagement in `code/analysis.py`
- [ ] T037 [US3] Implement regression summary table generation (coefficients, SE, p-values) in `code/analysis.py`
- [ ] T038 [US3] Implement `code/viz.py` to generate scatter plot with regression line
- [ ] T039 [US3] Implement `code/viz.py` to generate histogram of consistency scores
- [ ] T040 [US3] Save visualizations as PNG to `output/figures/`
- [ ] T041 [US3] Generate final JSON report in `output/reports/summary.json` including keys: `correlation_r`, `p_value`, `model_summary`, `scope_limitations` (documenting removed analyses). *Note: 'validity_flag' and 'proxy_status' removed as T019b was deleted.*
- [ ] T042 [US3] Implement main orchestration script `code/main.py` to run pipeline sequentially

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T043a Update `README.md` with usage instructions and scope limitations (AI Personality removed, Survival Analysis replaced by Poisson Regression)
- [ ] T043b Add docstrings to `code/ingestion.py`, `code/metrics.py`, and `code/analysis.py`
- [ ] T044 Code cleanup and refactoring
- [ ] T045 Performance optimization (verify runtime ≤ 6 hours [UNRESOLVED-CLAIM: c_47a2c9c9 — status=not_enough_info] on free-tier)
- [ ] T046 [P] Additional unit tests (if requested) in `tests/unit/`
- [ ] T047 Security hardening (ensure no PII leakage in logs)
- [ ] T048 Run `quickstart.md` validation

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data from US1 (T016)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on metrics from US2 (T029)

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
Task: "Unit test for session filtering logic in tests/unit/test_ingestion.py"
Task: "Contract test for data output schema in tests/contract/test_schemas.py"
Task: "Integration test for download retry logic in tests/integration/test_end_to_end.py"

# Launch all implementation for User Story 1 together:
Task: "Implement code/ingestion.py to download {{claim:c_3ed349d2}} from HuggingFace"
Task: "Implement session filtering logic in code/ingestion.py"
Task: "Implement null-value check and error handling in code/ingestion.py"
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
- **Critical Constraint**: Ensure all sentiment models run in CPU mode (no CUDA/quantization) to meet free-tier constraints.
- **Critical Constraint**: All data must be real ({{claim:c_3ed349d2}}); no synthetic input data generation for the main analysis.
- **Data Limitation Note**: 'Session Frequency (days between sessions)' cannot be computed due to lack of timestamps in {{claim:c_3ed349d2}}. Replaced by 'Session Count' in T025/T035.
- **Proxy Validity Note**: T019b (Proxy Validity Check) has been REMOVED as scientifically invalid per Plan. Spec FR-010/SC-006 acknowledged as unfulfillable.
- **Survival Analysis Note**: T035 implements Poisson Regression instead of Survival Analysis due to lack of time-to-event data. Spec FR-005/SC-002 acknowledged as unfulfillable.
- **Lagged Logic Note**: T026 implements 'Within-Session Lag' as a proxy for Spec FR-009's 'Cross-Session Lag' due to lack of longitudinal user IDs.