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
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, dependencies, and contract definitions

- [ ] T001 Create project structure per implementation plan (`code/`, `tests/`, `data/`, `results/`)
- [X] T002 Initialize project with dependencies (`pandas==2.0.3`, `numpy==1.24.3`, `scikit-learn==1.3.0`, `hrv-analysis==1.1.0`, `pybids==0.16.5`, `requests==2.31.0`, `pyyaml==6.0.1`, `jsonschema==4.19.0`, `statsmodels==0.14.0`) in `requirements.txt` with pinned versions.
- [ ] T002a [P] Create `contracts/dataset.schema.yaml` in Phase 1 to define the BIDS `events.tsv` schema. **Schema Content**: The YAML MUST define a JSON Schema for `events.tsv` with `type: object` and `properties` for `task` (string, enum: ['Schandry', 'heartbeat', 'TSST', 'rest', 'resting', 'baseline']), `onset` (number), `duration` (number), `value` (number, optional), and `trial_type` (string, optional). The `task` column is REQUIRED. **Validation**: This schema will be used by T004 to validate local BIDS files.
- [X] T003 [P] Configure linting (flake8/black) and formatting tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `code/utils/schema_validator.py` to load the **pre-existing** `contracts/dataset.schema.yaml` (created in T002a) and validate BIDS `events.tsv` files against it. **Error Contract**: Exit code indicating local file missing, schema mismatch, or invalid JSON/TSV format. **Note**: This task implements the *validation logic*, not the schema definition.
- [X] T005 [P] Implement `code/utils/hrv_utils.py` for artifact rejection (threshold < 5% valid beats) and signal validation
- [X] T007 [P] Implement `code/05_update_state.py` to compute SHA-256 hashes for `data/` and `results/` artifacts and update `state/projects/001-impact-of-interoceptive-awareness.yaml` per Constitution Principle V.
- [ ] T008 [P] Configure `pytest` environment with random seed pinning and `GITHUB_JOB_DURATION` logging. **Constraint**: Ensure data download scripts (T010, T011) enforce deterministic behavior via checksum verification as required by Constitution Principle I. **Specific Requirement**: T008 must explicitly require that `code/01_download_data.py` logs the SHA-256 checksum of every downloaded file to `results/checksums.txt` before the script exits. Seed pinning alone is insufficient for reproducibility of external fetches.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Availability Audit (Priority: P1) 🎯 MVP

**Goal**: Verify feasibility by scanning WESAD and OpenNeuro for specific behavioral interoception tasks (Schandry) and stress paradigms (TSST).

**Independent Test**: Execute `code/02_audit_metadata.py` on a mock directory structure to verify it correctly identifies missing "Schandry" tasks and outputs `results/data_audit.md`.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Implement test suite for US1 in `tests/test_audit.py`. Assertions: (1) `test_parse_metadata_handles_missing_task` asserts specific warning message for missing task labels; (2) `test_audit_flow_mock_data` asserts `results/data_audit.md` is created with "Feasibility Failure" status for Schandry task. Write tests before implementation.

### Implementation for User Story 1

- [ ] T010 [US1] Download the WESAD dataset archive from Zenodo (DOI: 10.5281/zenodo.1292932) [UNRESOLVED-CLAIM: c_369b3a73 — status=not_enough_info] to data/raw/wesad/. to `data/raw/wesad/`. **Constraint**: Use `requests` with a timeout of 10 minutes. If the download fails or times out, the script MUST raise a standard `requests.exceptions.Timeout` or `TimeoutError`, **delete any partial file**, log the error, and **IMMEDIATELY EXIT WITH NON-ZERO CODE**. **No Fallback**: Do NOT attempt a "Metadata-Only" mode here. If the download fails, the pipeline halts completely. The Audit (T011) will only proceed if this download succeeds.
- [ ] T011 [US1] Implement `code/02_audit_metadata.py` to perform a two-part scan. **CRITICAL FLOW**: This script must first perform a **Remote Metadata Pre-Check** (independent of download) to query Zenodo REST API (`) for 'Schandry' or 'heartbeat' in the file list. **IF** the remote check confirms the absence of these tasks, the script MUST log "Feasibility Failure: Missing Behavioral Task" and **TERMINATE THE PIPELINE** (exit 0 with failure status in report) without proceeding to local scan or further steps. **IF** remote check passes OR is inconclusive, proceed to **Local BIDS Scan** (Conditional): Only if T010 succeeded, scan local BIDS `**/events.tsv` files. **Validation Criteria**: The `task` column MUST contain the exact string 'Schandry' or 'heartbeat' (case-insensitive). If not found, the study is a "Feasibility Failure". Validate against `contracts/dataset.schema.yaml` (T002a). **Constraint**: This task performs the definitive verification required by FR-002. The pipeline MUST NOT proceed to HRV preprocessing if the Remote Pre-Check or Local Scan fails.
- [ ] T014 [US1] Generate final `results/data_audit.md` report explicitly stating presence/absence of required variables per FR-006. This report must include a "Feasibility Status" section.
 - **Logic**: If data is missing (Schandry not found in Remote Pre-Check or Local Scan), state "Feasibility Failure: Missing Behavioral Task" and **TERMINATE THE PIPELINE**. Do NOT calculate UBDE. Do NOT proceed to HRV preprocessing.
 - **Logic**: If data exists (Schandry found), state "Feasibility Success" and allow the pipeline to proceed to Phase 4 (Preprocessing).
 - **Dependency**: This task must be run after T011. It consolidates the audit findings.
- [ ] T015 [US1] Add error handling to ensure the script exits with code 0 (if report generated) or non-zero (if download failed and no local scan possible) and generates the report within 15 minutes regardless of data findings, logging any fetch failures.
- [ ] T017 [US1] Implement strict "fail loud" logic in `code/01_download_data.py`: remove any `try/except` blocks that fallback to synthetic/mock data on **dataset download** failure; ensure `requests` calls raise exceptions immediately on network or 404 errors. **Exception**: If the download succeeds but the data is incomplete for a **subset of subjects**, the system must exclude those subjects and continue processing (per Edge Cases), rather than terminating the entire pipeline.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Physiological Signal Preprocessing (Priority: P2)

**Goal**: Extract and compute HRV metrics (RMSSD, SDNN) from ECG/PPG signals for baseline and stress phases.

**Independent Test**: Run `code/03_preprocess_hrv.py` on a small subset of WESAD data and verify output CSV contains valid RMSSD/SDNN values with no NaNs for complete subjects.

**Dependency**: This phase ONLY executes if T014 reports "Feasibility Success".

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test `test_compute_rmssd_against_mitbih` in `tests/test_hrv.py` asserting calculated RMSSD matches PhysioNet reference within 1% tolerance. **Note**: Ensure MIT-BIH dataset is downloaded or mocked for this specific validation test as per SC-002.
- [ ] T019 [P] [US2] Integration test `test_artifact_rejection_threshold` in `tests/test_hrv.py` asserting subjects with <5% valid beats are flagged and excluded.

### Implementation for User Story 2

- [ ] T020 [US2] Implement `code/03_preprocess_hrv.py` to load raw ECG/PPG signals from WESAD/OpenNeuro derived data.
- [ ] T021 [US2] Implement signal cleaning using `hrv-analysis` library with artifact rejection thresholds (< 5% valid beats) per Edge Cases. **Explicit Requirement**: Use `hrv-analysis` functions for both cleaning AND calculation of RMSSD/SDNN. Do not implement manual calculations.
- [ ] T022 [US2] Compute HRV metrics (RMSSD, SDNN) for "Baseline" (resting) and "Stress" (TSST) phases per FR-003.
- [ ] T023 [US2] Extract Stress HRV metric as the outcome variable per FR-004.
- [ ] T024 [US2] Write output CSV to `data/derived/hrv_metrics.csv` with columns: `subject_id`, `phase`, `RMSSD`, `SDNN`.
- [ ] T025 [US2] Log exclusion of subjects with incomplete data or noisy signals without crashing the pipeline.
- [ ] T026 [US2] Ensure the preprocessing script explicitly handles the case where the downloaded WESAD data is missing the `ECG` or `PPG` channels required for HRV calculation, raising a descriptive error rather than proceeding with empty data.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Regression Analysis & Reporting (Priority: P3)

**Goal**: Perform ANCOVA-style linear regression (Stress HRV ~ Interoception + Baseline HRV) or generate sensitivity report (UBDE).

**Independent Test**: Run `code/04_analyze_regression.py` on a synthetic dataset with known coefficients to verify regression output.

**Dependency**: This phase ONLY executes if T014 reports "Feasibility Success" AND T024 (HRV metrics) is complete.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test `test_ancova_model_fitting` in `tests/test_regression.py` asserting coefficients match expected synthetic values.
- [ ] T028 [P] [US3] Integration test `test_mdes_calculation` in `tests/test_regression.py` asserting UBDE is calculated using observed variance and sample size with R²=0.10 assumption. **Correction**: This test is only valid if the spec is changed to allow UBDE. As per current spec, this test should assert that the script **terminates** if Interoception data is missing, and only runs regression if data exists.

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement `code/04_analyze_regression.py` to load `data/derived/hrv_metrics.csv` (output of T024) and `results/data_audit.md` (output of T014). **Dependency**: This task is **CONDITIONAL**. It MUST check the "Feasibility Status" in `data_audit.md`. If "Feasibility Failure", the script exits immediately with a success code (0) and logs "Pipeline Terminated: Data Gap". It MUST NOT proceed to regression or UBDE calculation.
- [ ] T030 [US3] **Critical Logic**: Check for Interoception Accuracy data availability based on T014 output. **IF** data is missing: **TERMINATE IMMEDIATELY** with exit code 0 and log "Feasibility Failure: Missing Behavioral Task". **Do NOT calculate UBDE**. **Do NOT proceed to regression**. **IF** data exists: proceed to T031.
- [ ] T031 [US3] **Primary Logic**: If Interoception data exists (verified in T030): Perform linear regression (Stress HRV ~ Interoception + Baseline HRV) per FR-005 using `statsmodels.formula.api.ols`. **Output Format**: Write results to `results/regression_results.json` with fields: `coefficient`, `p_value`, `r_squared`, `n_obs`, `formula`. **Constraint**: Do NOT calculate UBDE. **Constraint**: Do NOT proceed if T030 did not confirm data existence.
- [ ] T034 [US3] Ensure results are framed strictly as associational/predictive, not causal, per Assumptions.
- [ ] T035 [US3] Add validation to ensure the regression calculation explicitly logs the sample size (N) and the observed variance used, to satisfy the "Theoretical Sensitivity Bound" requirement in the plan (if applicable, otherwise log N for the regression).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Documentation updates in `quickstart.md` and `research.md`
- [ ] T037 Code cleanup and refactoring of `utils/` modules
- [ ] T038 [P] Implement timing instrumentation in `main.py`: Log `GITHUB_JOB_DURATION` timestamps and **verify** the measured duration against the 15-minute limit for the audit script (Phase 3) and the time limit for the full pipeline (Phases 1-5) defined in SC-004 and FR-007. The logic must distinguish between the audit-only run and the full run.
- [ ] T039 [P] Additional unit tests for versioning logic in `tests/test_versioning.py`
- [ ] T040 [P] Run `main.py` end-to-end validation and verify `state/projects/...yaml` integrity
- [ ] T041 [P] Verify that the pipeline correctly handles the scenario where the OpenNeuro API returns a (Too Many Requests) error by implementing a retry-with-backoff strategy for metadata queries only, ensuring the audit does not fail prematurely due to rate limits.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable. **Constraint**: Only runs if US1 reports "Feasibility Success".
- **User Story 3 (P3)**: **Strictly depends on** the completion of User Story 1 (Audit) and User Story 2 (Preprocessing).
 - *Note*: US3 logic depends on the *output* of US1 (audit result) to decide between Regression or Termination.
 - *Note*: US3 **MUST NOT** start until T024 (HRV metrics) and T014 (Audit report) are complete.
 - *Note*: If T014 reports "Feasibility Failure", US3 terminates immediately.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utilities before services
- Services before endpoints/scripts
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 and US2 can start in parallel (if team capacity allows)
- US3 must wait for US1 and US2 completion
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (except US3)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for metadata parsing logic in tests/test_audit.py"
Task: "Integration test for end-to-end audit flow (mock data) in tests/test_audit.py"

# Launch all implementation tasks for User Story 1 together:
Task: "Implement code/02_audit_metadata.py to download WESAD metadata..."
Task: "Implement logic to scan BIDS events.tsv files..."
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently. If "Feasibility Failure" is reported, the MVP is complete.
5. Deploy/demo if ready (Feasibility Report).

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP! Feasibility Report)
3. Add User Story 2 → Test independently → Deploy/Demo (HRV Pipeline) - **Only if US1 passes**.
4. Add User Story 3 → Test independently → Deploy/Demo (Regression) - **Only if US1 and US2 pass**.
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Audit)
 - Developer B: User Story 2 (Preprocessing) - **Conditional on US1 success**
3. Once US1 and US2 are complete:
 - Developer C: User Story 3 (Regression) - **Conditional on US1 and US2 success**
4. Stories complete and integrate independently

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
- **Statistical Constraint**: **NO UBDE calculation** for missing data. If data is missing, report "Feasibility Failure" and terminate.
- **Time Constraint**: Audit phase must complete within 15 minutes. [UNRESOLVED-CLAIM: c_ae71f7e1 — status=not_enough_info] (SC-001, FR-007). {{claim:c_2d54c102}} (Wikipedia: Pipeline (computing), https://en.wikipedia.org/wiki/Pipeline_(computing)) T010 includes a timeout to enforce this.
- **Validation Constraint**: MIT-BIH dataset must be available for HRV validation (SC-002) or mocked appropriately in tests.
- **Rate Limit Constraint**: OpenNeuro API queries must include retry logic for 429 errors to prevent premature audit failure.
- **Download Constraint**: T010 attempts a full download but respects time limits; if it fails, the pipeline terminates immediately. T011's Remote Pre-Check runs independently to confirm the data gap, but the pipeline does not proceed to local scan or further steps if T010 fails.
- **File Naming Correction**: All audit outputs must be written to `results/data_audit.md` (not `data/audit/`) to match the plan's `results/` directory structure and FR-006 requirements.
- **Script Naming Correction**: Audit script is `code/02_audit_metadata.py` (not `01_audit_data.py`) to align with the sequential numbering in `plan.md`.
- **State Update Script Correction**: State update script is `code/05_update_state.py` (not `04_update_state.py`) to align with the sequential numbering in `plan.md`.
- **Regression Script Correction**: Regression script is `code/04_analyze_regression.py` (not `03_analyze_regression.py`) to align with the sequential numbering in `plan.md`.
- **Preprocessing Script Correction**: Preprocessing script is `code/03_preprocess_hrv.py` (not `02_preprocess_hrv.py`) to align with the sequential numbering in `plan.md`.
- **Report Consolidation**: T014 generates the complete `data_audit.md` report. T033 has been removed.
- **Schema Correction**: T002a defines the schema for BIDS `events.tsv` columns.
- **Logic Correction**: T010 deletes partial files on timeout. T011 explicitly reports download failures.
- **Subset Handling**: T017 allows subject-level exclusion for missing data while maintaining "fail loud" for missing datasets.
- **Termination Logic**: If T014 reports "Feasibility Failure", the pipeline terminates. T029, T030, T031, T032 are skipped.
- **Output Format**: Regression results (T031) MUST be written to `results/regression_results.json`.