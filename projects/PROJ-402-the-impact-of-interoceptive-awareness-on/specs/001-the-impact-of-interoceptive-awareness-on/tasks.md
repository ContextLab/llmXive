# Tasks: The Impact of Interoceptive Awareness on Emotional Regulation During Simulated Stress

**Input**: Design documents from `/specs/001-impact-of-interoceptive-awareness-on/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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
 - Delivered as a MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`code/`, `tests/`, `data/`, `results/`)
- [X] T002 Initialize {{claim:c_208d3e66}} (Wikipedia: History of Python, https://en.wikipedia.org/wiki/History_of_Python) project with dependencies (`pandas`, `numpy`, `scikit-learn`, `hrv-analysis`, `pybids`, `requests`, `pyyaml`, `jsonschema`) in `requirements.txt`
- [X] T003 [P] Configure linting (flake8/black) and formatting tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 {{claim:c_6d2a1597}} Error contract: Exit code 1 on HTTP 404, timeout > 60s, or schema mismatch (validate against `contracts/dataset.schema.yaml`). MUST verify checksum immediately upon download to ensure reproducibility.
- [X] T005 Implement `code/utils/hrv_utils.py` for artifact rejection (threshold < 5% valid beats) and signal validation
- [X] T006 Create base schema validation logic in `code/utils/schema_validator.py` to enforce `contracts/*.yaml` inputs
- [ ] T007 Implement `code/04_update_state.py` to compute SHA-256 hashes for `data/` and `results/` artifacts and update `state/projects/...yaml`
- [ ] T008 Configure `pytest` environment with random seed pinning and `GITHUB_JOB_DURATION` logging. **Constraint**: Ensure data download scripts (T004, T011) enforce deterministic behavior via checksum verification as required by Constitution Principle I.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Availability Audit (Priority: P1) 🎯 MVP

**Goal**: Verify feasibility by scanning WESAD and OpenNeuro for specific behavioral interoception tasks (Schandry) and stress paradigms (TSST).

**Independent Test**: Execute `code/01_audit_data.py` on a mock directory structure to verify it correctly identifies missing "Schandry" tasks and outputs `data/audit/data_audit.md`.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Implement test suite for US1 in `tests/test_audit.py`. Assertions: (1) `test_parse_metadata_handles_missing_task` asserts specific warning message for missing task labels; (2) `test_audit_flow_mock_data` asserts `data_audit.md` is created with "Not Found" status for Schandry task. Write tests before implementation.

### Implementation for User Story 1

- [X] T011 [US1] Implement `code/01_audit_data.py` to query the Zenodo file-list API (metadata only) to scan file names for patterns ('events.tsv', 'Schandry', 'heartbeat') and check OpenNeuro metadata for 'TSST'. **Constraint**: Do NOT download the full WESAD archive in this step; only download the specific file list or small metadata index to verify presence within the 15-minute limit (SC-001, FR-007).
- [ ] T012 [US1] Implement logic to scan BIDS `events.tsv` files locally (if downloaded for validation) specifically for the `task` column containing values matching 'Schandry' or 'heartbeat' (case-insensitive) per FR-002.
- [ ] T013 [US1] Implement logic to detect presence of TSST stress markers in metadata.
- [X] T014 [US1] Generate initial `data/audit/data_audit.md` explicitly stating presence/absence of required variables per FR-006. This report must include a "Feasibility Status" section. If data is missing, state "Missing: [variable]". **Note**: Do NOT calculate MDES in this task; MDES is calculated in T029/T030.
- [ ] T015 [US1] Add error handling to ensure the script exits with code 0 and generates the report within 15 minutes regardless of data findings, logging any fetch failures.
- [ ] T016 [US1] Validate that the audit report correctly reflects the local scan results of the full WESAD dataset (if downloaded) or metadata scan (if not).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Physiological Signal Preprocessing (Priority: P2)

**Goal**: Extract and compute HRV metrics (RMSSD, SDNN) from ECG/PPG signals for baseline and stress phases.

**Independent Test**: Run `code/02_preprocess_hrv.py` on a small subset of WESAD data and verify output CSV contains valid RMSSD/SDNN values with no NaNs for complete subjects.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Unit test `test_compute_rmssd_against_mitbih` in `tests/test_hrv.py` asserting calculated RMSSD matches PhysioNet reference within 1% tolerance. **Note**: Ensure MIT-BIH dataset is downloaded or mocked for this specific validation test as per SC-002.
- [X] T018 [P] [US2] Integration test `test_artifact_rejection_threshold` in `tests/test_hrv.py` asserting subjects with <5% valid beats are flagged and excluded.

### Implementation for User Story 2

- [X] T019 [US2] Implement `code/02_preprocess_hrv.py` to load raw ECG/PPG signals from WESAD/OpenNeuro derived data.
- [ ] T020 [US2] Implement signal cleaning using `hrv-analysis` library with artifact rejection thresholds (< 5% valid beats) per Edge Cases.
- [ ] T021 [US2] Compute HRV metrics (RMSSD, SDNN) for "Baseline" (resting) and "Stress" (TSST) phases per FR-003.
- [ ] T022 [US2] Extract Stress HRV metric as the outcome variable per FR-004.
- [X] T023 [US2] Write output CSV to `data/derived/hrv_metrics.csv` with columns: `subject_id`, `phase`, `RMSSD`, `SDNN`.
- [ ] T024 [US2] Log exclusion of subjects with incomplete data or noisy signals without crashing the pipeline.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Regression Analysis & Reporting (Priority: P3)

**Goal**: Perform ANCOVA-style linear regression (Stress HRV ~ Interoception + Baseline HRV) or generate sensitivity report (MDES).

**Independent Test**: Run `code/03_analyze_regression.py` on a synthetic dataset with known coefficients to verify regression output and MDES logic.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US3] Unit test `test_ancova_model_fitting` in `tests/test_regression.py` asserting coefficients match expected synthetic values.
- [ ] T026 [P] [US3] Integration test `test_mdes_calculation` in `tests/test_regression.py` asserting MDES is calculated using observed variance and sample size with R²=0.10 assumption.

### Implementation for User Story 3

- [ ] T027 [P] [US3] Implement `code/03_analyze_regression.py` to load `data/derived/hrv_metrics.csv` and `data/audit/data_audit.md`. If `data_audit.md` is missing, allow synthetic data loading for testing.
- [ ] T028 [US3] Implement logic to check for Interoception Accuracy data availability based on T014 output.
- [ ] T029 [US3] If data missing: Calculate Minimum Detectable Effect Size (MDES) using **only** the observed Stress HRV variance (from T023 if available) and sample size, with an assumed R² = 0.10. If no Stress HRV variance is available (T023 not run), report MDES as "Undeterminable" (do not use synthetic defaults).
- [ ] T030 [US3] **Primary Logic**: If Interoception data exists: Perform linear regression (Stress HRV ~ Interoception + Baseline HRV) per FR-005. **Fallback Logic**: If Interoception data is MISSING: Execute the MDES calculation defined in T029. **Terminology**: Use "Minimum Detectable Effect Size (MDES)" exclusively. Do NOT use "UBDE". The calculation must assume R² = 0.10 as per the Plan and FR-006. Note: If spec.md mentions "UBDE", treat it as a typo and follow the Plan's "MDES" definition.
- [ ] T031 [US3] Generate final report by appending the calculated MDES or regression results to `data/audit/data_audit.md` per FR-006. Ensure the file is updated (appended/merged) rather than overwritten if it already exists.
- [ ] T032 [US3] Ensure results are framed strictly as associational/predictive, not causal, per Assumptions.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Documentation updates in `quickstart.md` and `research.md`
- [ ] T034 Code cleanup and refactoring of `utils/` modules
- [ ] T035 [P] Implement timing instrumentation in `main.py`: Log `GITHUB_JOB_DURATION` timestamps and **verify** the measured duration against the 15-minute (audit) and 45-minute (full) limits defined in SC-004 and FR-007.
- [ ] T036 [P] Additional unit tests for versioning logic in `tests/test_versioning.py`
- [ ] T037 Run `main.py` end-to-end validation and verify `state/projects/...yaml` integrity

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable
 - *Note*: US3 logic depends on the *output* of US1 (audit result) to decide between Regression or MDES path.
 - *Note*: US3 MDES calculation depends on the output of US2 (T023: observed Stress HRV variance).

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utilities before services
- Services before endpoints/scripts
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
Task: "Unit test for metadata parsing logic in tests/test_audit.py"
Task: "Integration test for end-to-end audit flow (mock data) in tests/test_audit.py"

# Launch all implementation tasks for User Story 1 together:
Task: "Implement code/01_audit_data.py to download WESAD metadata..."
Task: "Implement logic to scan BIDS events.tsv files..."
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready (Feasibility Report)

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP! Feasibility Report)
3. Add User Story 2 → Test independently → Deploy/Demo (HRV Pipeline)
4. Add User Story 3 → Test independently → Deploy/Demo (Regression/MDES)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Audit)
 - Developer B: User Story 2 (Preprocessing)
 - Developer C: User Story 3 (Regression/MDES)
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
- **Critical Data Constraint**: Data loaders MUST fail loudly on missing real data; no synthetic fallbacks allowed.
- **Compute Constraint**: All tasks must be feasible on CPU-only GitHub Actions runner (no GPU).
- **Statistical Constraint**: MDES calculation (T029/T030) must use observed variance (if available) and R²=0.10; report "Undeterminable" if no variance data exists. **Terminology**: Use "MDES" (Minimum Detectable Effect Size) exclusively. "UBDE" is a known typo in spec.md and must not be used in code or output.
- **Time Constraint**: Audit phase must complete within 15 minutes (SC-001, FR-007). Full pipeline within 45 minutes.
- **Validation Constraint**: MIT-BIH dataset must be available for HRV validation (SC-002) or mocked appropriately in tests.
