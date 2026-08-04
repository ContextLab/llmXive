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
- [ ] T002 Initialize project with dependencies (`pandas==2.0.3`, `numpy==1.24.3`, `scikit-learn==1.3.0`, `hrv-analysis==1.1.0`, `pybids==0.16.5`, `requests==2.31.0`, `pyyaml==6.0.1`, `jsonschema==4.19.0`) in `requirements.txt` with pinned versions.
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `code/utils/schema_validator.py` to enforce `contracts/dataset.schema.yaml` inputs. **Schema Definition**: The task MUST create `contracts/dataset.schema.yaml` with the following content:
  ```yaml
  type: object
  required: [subject_id, task, phase]
  properties:
    subject_id: {type: string}
    task: {type: string, enum: ["Schandry", "heartbeat", "TSST", "rest"]}
    phase: {type: string}
  ```
  **Error Contract**: Exit code 1 on local file missing, schema mismatch, or invalid JSON/TSV format. MUST verify checksum immediately upon download (if used locally).
- [ ] T005 [P] Implement `code/utils/hrv_utils.py` for artifact rejection (threshold < 5% valid beats) and signal validation
- [ ] T006 [P] Create base schema validation logic in `code/utils/schema_validator.py` to enforce `contracts/*.yaml` inputs
- [ ] T007 [P] Implement `code/04_update_state.py` to compute SHA-256 hashes for `data/` and `results/` artifacts and update `state/projects/PROJ-402-the-impact-of-interoceptive-awareness-on.yaml` per Constitution Principle V.
- [ ] T008 [P] Configure `pytest` environment with random seed pinning and `GITHUB_JOB_DURATION` logging. **Constraint**: Ensure data download scripts (T010, T011) enforce deterministic behavior via checksum verification as required by Constitution Principle I.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Availability Audit (Priority: P1) 🎯 MVP

**Goal**: Verify feasibility by scanning WESAD and OpenNeuro for specific behavioral interoception tasks (Schandry) and stress paradigms (TSST).

**Independent Test**: Execute `code/01_audit_data.py` on a mock directory structure to verify it correctly identifies missing "Schandry" tasks and outputs `data/audit/data_audit.md`.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Implement test suite for US1 in `tests/test_audit.py`. Assertions: (1) `test_parse_metadata_handles_missing_task` asserts specific warning message for missing task labels; (2) `test_audit_flow_mock_data` asserts `data_audit.md` is created with "Not Found" status for Schandry task. Write tests before implementation.

### Implementation for User Story 1

- [ ] T010 [US1] Download the WESAD dataset archive from Zenodo (DOI: 10.5281/zenodo.1292932) to `data/raw/wesad/`. **Constraint**: Use `requests` with a timeout of 10 minutes and a maximum file size check. If the download fails or times out, the script MUST raise a `DownloadTimeoutError` and exit. The audit (T011) will proceed in "Metadata-Only" mode if this task fails, but T010 must attempt the download first.
- [ ] T011 [US1] Implement `code/01_audit_data.py` to perform a two-part scan: 
  1. **Metadata Scan**: Query Zenodo file-list API (`GET https://zenodo.org/api/records/1292932/files`) to parse JSON and extract filenames for patterns ('events.tsv', 'Schandry', 'heartbeat').
  2. **Local BIDS Scan**: If T010 succeeded, scan local BIDS `**/events.tsv` files (flexible glob) specifically for the `task` column containing values matching 'Schandry' or 'heartbeat' (case-insensitive) per FR-002. If T010 failed, skip local scan and log "Local scan skipped: download timeout/failure".
  **Constraint**: This task performs the definitive verification required by FR-002. It must NOT rely solely on metadata if local data is available.
- [ ] T014 [US1] Generate initial `data/audit/data_audit.md` explicitly stating presence/absence of required variables per FR-006. This report must include a "Feasibility Status" section. If data is missing, state "Missing: [variable]". **Note**: This task creates the *skeleton* of the report. The final UBDE calculation (if data is missing) is appended in T031/T032. **Dependency**: This task must be run after T011.
- [ ] T015 [US1] Add error handling to ensure the script exits with code 0 and generates the report within 15 minutes regardless of data findings, logging any fetch failures.
- [ ] T017 [US1] Implement strict "fail loud" logic in `code/utils/data_loader.py`: remove any `try/except` blocks that fallback to synthetic/mock data on download failure; ensure `requests` or `openneuro` calls raise exceptions immediately on network or 404 errors.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Physiological Signal Preprocessing (Priority: P2)

**Goal**: Extract and compute HRV metrics (RMSSD, SDNN) from ECG/PPG signals for baseline and stress phases.

**Independent Test**: Run `code/02_preprocess_hrv.py` on a small subset of WESAD data and verify output CSV contains valid RMSSD/SDNN values with no NaNs for complete subjects.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test `test_compute_rmssd_against_mitbih` in `tests/test_hrv.py` asserting calculated RMSSD matches PhysioNet reference within 1% tolerance. **Note**: Ensure MIT-BIH dataset is downloaded or mocked for this specific validation test as per SC-002.
- [ ] T019 [P] [US2] Integration test `test_artifact_rejection_threshold` in `tests/test_hrv.py` asserting subjects with <5% valid beats are flagged and excluded.

### Implementation for User Story 2

- [ ] T020 [US2] Implement `code/02_preprocess_hrv.py` to load raw ECG/PPG signals from WESAD/OpenNeuro derived data.
- [ ] T021 [US2] Implement signal cleaning using `hrv-analysis` library with artifact rejection thresholds (< 5% valid beats) per Edge Cases.
- [ ] T022 [US2] Compute HRV metrics (RMSSD, SDNN) for "Baseline" (resting) and "Stress" (TSST) phases per FR-003.
- [ ] T023 [US2] Extract Stress HRV metric as the outcome variable per FR-004.
- [ ] T024 [US2] Write output CSV to `data/derived/hrv_metrics.csv` with columns: `subject_id`, `phase`, `RMSSD`, `SDNN`.
- [ ] T025 [US2] Log exclusion of subjects with incomplete data or noisy signals without crashing the pipeline.
- [ ] T026 [US2] Ensure the preprocessing script explicitly handles the case where the downloaded WESAD data is missing the `ECG` or `PPG` channels required for HRV calculation, raising a descriptive error rather than proceeding with empty data.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Regression Analysis & Reporting (Priority: P3)

**Goal**: Perform ANCOVA-style linear regression (Stress HRV ~ Interoception + Baseline HRV) or generate sensitivity report (UBDE).

**Independent Test**: Run `code/03_analyze_regression.py` on a synthetic dataset with known coefficients to verify regression output and UBDE logic.

**Dependency**: This phase MUST wait for T024 (HRV metrics) and T014 (Audit skeleton) to complete. **T029 explicitly requires T024 and T014 to be finished before execution.**

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test `test_ancova_model_fitting` in `tests/test_regression.py` asserting coefficients match expected synthetic values.
- [ ] T028 [P] [US3] Integration test `test_mdes_calculation` in `tests/test_regression.py` asserting UBDE is calculated using observed variance and sample size with R²=0.10 assumption.

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement `code/03_analyze_regression.py` to load `data/derived/hrv_metrics.csv` (output of T024) and `data/audit/data_audit.md` (output of T014). If `data_audit.md` is missing, allow synthetic data loading for testing. **Dependency**: This task cannot start until T024 and T014 are complete.
- [ ] T030 [US3] Implement logic to check for Interoception Accuracy data availability based on T014 output.
- [ ] T031 [US3] If data missing: Calculate Upper Bound of Detectable Effect (UBDE) using **only** the observed Stress HRV variance (from T023 if available) and sample size. **Formula**: `UBDE = t_crit * sqrt(2 * s^2 / N)`, where `s^2` is observed variance, `N` is sample size, and `t_crit` is from `scipy.stats.t.ppf(0.975, df=N-2)`. Assume R² = 0.10 for the theoretical bound. If no Stress HRV variance is available, report UBDE as "Undeterminable". **BLOCKING DEPENDENCY**: This task MUST NOT run until T024 and T014 are complete.
- [ ] T032 [US3] **Primary Logic**: If Interoception data exists: Perform linear regression (Stress HRV ~ Interoception + Baseline HRV) per FR-005. **Fallback Logic**: If Interoception data is MISSING: Execute the UBDE calculation defined in T031. **Terminology**: Use "Upper Bound of Detectable Effect (UBDE)" as the primary term in the output report per FR-006, explicitly noting it corresponds to the MDES concept. **BLOCKING DEPENDENCY**: This task MUST NOT run until T024 and T014 are complete.
- [ ] T033 [US3] Generate final report by appending the calculated UBDE (or regression results) to `data/audit/data_audit.md` per FR-006. Ensure the file is updated (appended/merged) to produce the *complete* deliverable satisfying FR-006.
- [ ] T034 [US3] Ensure results are framed strictly as associational/predictive, not causal, per Assumptions.
- [ ] T035 [US3] Add validation to ensure the UBDE calculation explicitly logs the sample size (N) and the observed variance used, to satisfy the "Theoretical Sensitivity Bound" requirement in the plan.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Documentation updates in `quickstart.md` and `research.md`
- [ ] T037 Code cleanup and refactoring of `utils/` modules
- [ ] T038 [P] Implement timing instrumentation in `main.py`: Log `GITHUB_JOB_DURATION` timestamps and **verify** the measured duration against the 15-minute (audit) and 45-minute (full) limits defined in SC-004 and FR-007.
- [ ] T039 [P] Additional unit tests for versioning logic in `tests/test_versioning.py`
- [ ] T040 [P] Run `main.py` end-to-end validation and verify `state/projects/...yaml` integrity
- [ ] T041 [P] Verify that the pipeline correctly handles the scenario where the OpenNeuro API returns a 429 (Too Many Requests) error by implementing a retry-with-backoff strategy for metadata queries only, ensuring the audit does not fail prematurely due to rate limits.

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
 - *Note*: US3 logic depends on the *output* of US1 (audit result) to decide between Regression or UBDE path.
 - *Note*: US3 UBDE calculation depends on the output of US2 (T023: observed Stress HRV variance).
 - *Note*: US3 **MUST NOT** start until T024 (HRV metrics) and T014 (Audit skeleton) are complete.

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
4. Add User Story 3 → Test independently → Deploy/Demo (Regression/UBDE)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Audit)
 - Developer B: User Story 2 (Preprocessing)
 - Developer C: User Story 3 (Regression/UBDE)
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
- **Statistical Constraint**: UBDE calculation (T031/T032) must use observed variance (if available) and R²=0.10; report "Undeterminable" if no variance data exists. **Terminology**: Use "UBDE" (Upper Bound of Detectable Effect) as the primary term in the output report per FR-006, acknowledging "MDES" as the underlying statistical concept.
- **Time Constraint**: Audit phase must complete within 15 minutes (SC-001, FR-007). Full pipeline within 45 minutes. T010 includes a timeout to enforce this.
- **Validation Constraint**: MIT-BIH dataset must be available for HRV validation (SC-002) or mocked appropriately in tests.
- **Rate Limit Constraint**: OpenNeuro API queries must include retry logic for 429 errors to prevent premature audit failure.
- **Download Constraint**: T010 attempts a full download but respects time limits; if it fails, T011 proceeds with metadata-only and reports the gap.