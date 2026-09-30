# Tasks: The Impact of Interoceptive Awareness on Emotional Regulation During Simulated Stress

**Input**: Design documents from `/specs/001-impact-of-interoceptive-awareness/`
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
- [ ] T002a [P] Create `requirements.txt` with pinned dependencies (`pandas==2.0.3`, `numpy==1.24.3`, `scikit-learn==1.3.0`, `hrv-analysis==1.1.0`, `pybids==0.16.5`, `requests==2.31.0`, `pyyaml==6.0.1`, `jsonschema==4.19.0`, `statsmodels==0.14.0`). **Note**: This task creates the file content only.
- [ ] T002b [P] Install dependencies from `requirements.txt` using `pip install -r requirements.txt`. **Dependency**: T002a must complete first. **Verification**: Create a virtual environment (`venv`) and verify that `import pandas` succeeds without error. **Artifact**: `venv` directory.
- [ ] T002b-verify [P] Verify that all dependencies installed correctly by running `python -c "import pandas; import numpy; import sklearn; import hrv_analysis; import pybids; import requests; import yaml; import jsonschema; import statsmodels"`. **Dependency**: T002b must complete first. **Verification**: Exit code 0 indicates success.
- [ ] T002c [P] Create `contracts/dataset.schema.yaml` and write the exact JSON Schema content. **Schema Content**: The YAML MUST define a JSON Schema for `events.tsv` with `type: object` and `properties` for `task` (string, enum: ['Schandry', 'heartbeat', 'TSST', 'rest', 'baseline']), `onset` (number), `duration` (number), `value` (number, optional), and `trial_type` (string, optional). The `task` column is REQUIRED. **Note**: 'Schandry' and 'heartbeat' are the ONLY values that indicate the presence of the behavioral task per FR-002. 'TSST', 'rest', and 'baseline' are included for phase identification but do NOT indicate the presence of the behavioral task. The validator (T002d) must explicitly reject 'TSST' as a behavioral task indicator. **Validation**: This schema will be used by T002d to validate local BIDS files. **Dependency**: Derived from design artifacts in `contracts/`.
- [ ] T002d [P] Implement `code/utils/schema_validator.py` to load the **pre-existing** `contracts/dataset.schema.yaml` (created in T002c) and validate BIDS `events.tsv` files against it. **Error Contract**: Exit code indicating local file missing, schema mismatch, or invalid JSON/TSV format. **Specific Logic**: If the `task` column contains 'TSST', 'rest', or 'baseline', the validator must flag these as valid *phase* tasks but NOT as valid *behavioral* tasks. **Note**: This task implements the *validation logic*. **Dependency**: T002c must complete first (schema file must exist).

- [ ] T003 [P] Configure linting (flake8/black) and formatting tools in `pyproject.toml`. **Specific Configuration**: Set `black --line-length` and `flake --max-line-length` in `pyproject.toml` to enforce a consistent line-length limit. under `[tool.black]` and `[tool.flake8]` sections respectively. **Verification**: Run `black --check.` and `flake8.` to ensure no configuration errors.

- [ ] T002e [P] Move or copy `requirements.txt` to the Constitution-mandated path `projects/PROJ-402-the-impact-of-interoceptive-awareness-on/code/requirements.txt`. **Verification**: Verify file exists at the specific path and is readable. **Dependency**: T002b-verify must complete (file must exist and be valid). **Note**: Required by Constitution Principle I (Reproducibility).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] Implement `code/utils/hrv_utils.py` for artifact rejection (threshold < 5% valid beats) and signal validation
- [ ] T007 [P] Implement `code/05_update_state.py` to compute SHA-256 hashes for `data/` and `results/` artifacts and update `state/projects/001-impact-of-interoceptive-awareness.yaml` per Constitution Principle V.
- [ ] T008 [P] Configure `pytest` environment with random seed pinning in `conftest.py`. **Constraint**: Ensure data download scripts (T010, T010b) enforce deterministic behavior via checksum verification as required by Constitution Principle I. **Specific Requirement**: T008 must explicitly require that `code/01_download_data.py` logs the SHA-256 checksum of every downloaded file to `results/checksums.txt` before the script exits. Seed pinning alone is insufficient for reproducibility of external fetches. **Note**: Full pipeline timing (including non-test scripts) is handled by T038c, not pytest config. **Dependency**: `requirements.txt` must be installed (T002b) and located at `projects/PROJ-402.../code/` (T002e).
- [ ] T008b [P] Implement logic in `code/05_update_state.py` (or a dedicated script) to checksum ALL files under `data/`, including derived artifacts like `data/derived/hrv_metrics.csv`. **Constraint**: Update `state/projects/.../artifact_hashes` with the new hashes. **Verification**: Run the script and verify that `data/derived/` files are included in the hash map. **Dependency**: T007.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Availability Audit (Priority: P1) 🎯 MVP

**Goal**: Verify feasibility by scanning WESAD and OpenNeuro for specific behavioral interoception tasks (Schandry) and stress paradigms (TSST).

**Independent Test**: Execute `code/02_audit_metadata.py` on a mock directory structure to verify it correctly identifies missing "Schandry" tasks and outputs `results/data_audit.md`.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Implement test suite for US1 in `tests/test_audit.py`. **Specific Functions**: (1) `test_audit_logic_returns_failure_status` asserts that the audit logic correctly identifies missing 'Schandry' tasks and returns a 'Feasibility Failure' status using **mocked inputs** (not file I/O). **Mock Data Contract**: The mock input must be a JSON list of objects with keys `subject_id`, `task`, `phase`. Example: `[{"subject_id": "01", "task": "TSST", "phase": "stress"}]`. The assertion must check that the function returns `{"status": "Feasibility Failure", "missing_tasks": ["Schandry"]}`. (2) `test_audit_flow_mock_data` asserts the logic correctly routes to UBDE calculation or regression paths based on mock data. Write tests before implementation. **Correction**: The test must assert the logic's internal state or return value, not the final file content generated by T014.

### Implementation for User Story 1

- [ ] T010 [US1] Download the WESAD dataset archive from Zenodo (DOI: 10.5281/zenodo.1292932) to `data/raw/wesad/WESAD.zip`. **Constraint**: Use `requests` with a timeout of 10 minutes. **Strict Requirement**: If the download fails or times out, the script MUST log a CRITICAL error, **delete any partial file**, and **ABORT the WESAD-specific scan path**. Do NOT proceed to T011a for WESAD data. The pipeline may continue to check other sources (OpenNeuro) but must explicitly log that WESAD was unavailable. **Specific Path**: The downloaded file MUST be named `WESAD.zip` and extracted to `data/raw/wesad/`. **Verification**: Verify that the directory `data/raw/wesad/` exists and contains the expected extracted files. **Note**: "Fail loud" logic (no synthetic fallback) is enforced here. **Dependency**: T010 is NOT [P] relative to T011a.
- [ ] T010b [US1] Download the OpenNeuro dataset index (metadata) for studies containing **BOTH** "TSST" **AND** ("heartbeat" **OR** "interoception") keywords. **Endpoint**: Use ` Name or service not known)"))] with a GraphQL query or REST filter to fetch a JSON list of studies matching the intersection of keywords. **Output**: Save the JSON index to `data/raw/openneuro/index.json`. **Constraint**: If the download fails, log the error but **DO NOT EXIT**. The pipeline must continue to the Local BIDS Scan (T011a) to check for available local data. **Verification**: Verify file size > 0 and validate JSON schema. **Logic**: The query MUST filter for studies containing 'TSST' and ('heartbeat' OR 'interoception') to avoid irrelevant datasets. **Dependency**: T011a depends on T010b (cannot be parallel). **Note**: T010b is NOT [P] relative to T011a.
- [ ] T011a [US1] Implement `code/02_audit_metadata.py` to perform a **Local BIDS Scan** for WESAD (if downloaded). **Logic**:
 1. Check if `data/raw/wesad/` exists and contains extracted files.
 2. If yes, scan local `**/events.tsv` files for `task` labels matching 'Schandry', 'heartbeat', or 'TSST' (case-insensitive) as per FR-002.
 3. If no (WESAD download failed), skip this step and log "WESAD Unavailable".
 4. **Dependency**: T010 must complete (success or failure) before T011a runs.
 5. **Output**: Generate an intermediate JSON file `data/audit/wesad_scan_results.json` containing the list of found tasks and their locations (or "Unavailable" status).
- [ ] T011b [US1] Implement `code/02_audit_metadata.py` to perform an **Index Scan** for OpenNeuro. **Logic**:
 1. Load the downloaded OpenNeuro index (from T010b).
 2. Scan the index for studies containing 'TSST' and ('heartbeat' OR 'interoception').
 3. **Dependency**: T010b must complete before T011b runs.
 4. **Output**: Generate an intermediate JSON file `data/audit/openneuro_scan_results.json` containing the list of found studies and tasks.
- [ ] T011c [US1] Implement **Result Aggregation** logic in `code/02_audit_metadata.py`. **Logic**:
 1. Merge `wesad_scan_results.json` and `openneuro_scan_results.json`.
 2. Determine if 'Schandry' or 'heartbeat' is present in ANY source.
 3. **Constraint**: If WESAD was unavailable (T010 failed) AND OpenNeuro has no 'Schandry'/'heartbeat', set feasibility flag to "Feasibility Failure: Dataset Unavailable".
 4. **Dependency**: T011a and T011b must complete first.
 5. **Output**: Generate an intermediate JSON file `data/audit/scan_results.json` containing the aggregated list of found tasks and the feasibility flag.
- [ ] T014 [US1] Generate final `results/data_audit.md` report explicitly stating presence/absence of required variables per FR-006. This report must include a "Feasibility Status" section.
 - **Logic**:
 - **Case 1 (Dataset Unavailable)**: If the aggregated scan shows NO data (WESAD missing + OpenNeuro empty), state "Feasibility Failure: Dataset Unavailable". **Action**: Do NOT calculate UBDE. Report the reason as "No data available for analysis".
 - **Case 2 (Variable Missing)**: If data exists (N > 0) but 'Schandry'/'heartbeat' is NOT found, state "Feasibility Failure: Missing Behavioral Task". **Action**: Calculate the Upper Bound of Detectable Effect (UBDE) using the formula: `UBDE = t_(-alpha/2, df) * sqrt(2 * sigma^2 / N)`, where `sigma^2` is the estimated noise variance (use a conservative estimate, e.g., a standard baseline value, if not available), `N` is the sample size, and `df` is degrees of freedom. Inject the calculated UBDE value directly into the `data_audit.md` report. **Note**: This satisfies FR-006 requirement to "include the calculated UBDE" in the primary feasibility report. **Do NOT terminate the pipeline here**; the pipeline continues to generate the UBDE report.
 - **Case 3 (Data Exists)**: If 'Schandry'/'heartbeat' is found, state "Feasibility Success" and allow the pipeline to proceed to Phase 4 (Preprocessing).
 - **Dependency**: This task must be run after T011c. It consolidates the audit findings and calculates UBDE if needed.
 - **Verification**: Verify that `data_audit.md` contains the string "UBDE" if feasibility failed (Case 2) and does NOT contain UBDE if dataset was unavailable (Case 1).
- [ ] T015 [US1] Add error handling to ensure the script exits with code 0 (if report generated) or non-zero (if download failed and no local scan possible) and generates the report within 15 minutes regardless of data findings, logging any fetch failures.
- [ ] T038b [P] [US1] Implement specific logic in `code/02_audit_metadata.py` to enforce a **time-bound hard stop** for the audit phase. **Logic**: Start a timer at the beginning of the audit. If the timer exceeds 15 minutes, log a warning, force the audit to complete with whatever data is available, and **exit with code 1** (indicating timeout) if no data was processed, or code 0 if some data was processed but the full scan was incomplete. **Dependency**: SC-004 and FR-007. **Note**: This task is moved here from Phase 6 to ensure US1 is self-contained. **Constraint**: Do NOT exit with code 0 if the timeout prevented meaningful analysis, to avoid masking pipeline failures.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Physiological Signal Preprocessing (Priority: P2)

**Goal**: Extract and compute HRV metrics (RMSSD, SDNN) from ECG/PPG signals for baseline and stress phases.

**Independent Test**: Run `code/03_preprocess_hrv.py` on a small subset of WESAD data and verify output CSV contains valid RMSSD/SDNN values with no NaNs for complete subjects.

**Dependency**: This phase ONLY executes if T014 reports "Feasibility Success".

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test `test_compute_rmssd_against_mitbih` in `tests/test_hrv.py` asserting calculated RMSSD matches PhysioNet reference within 1% tolerance. **Note**: Ensure MIT-BIH dataset is downloaded from PhysioNet via `wfdb` library. **Specifics**: Use records '' and '101'. The test must download the ECG signal and the annotation file for these records, compute RMSSD using `hrv-analysis`, and compare the result against the known ground-truth RMSSD values derived from the annotations (or a verified reference value from the literature/PhysioNet database). **Constraint**: Do NOT generate mock data; use real MIT-BIH data. **Verification**: Assert that the computed RMSSD is within 1% of the reference value.
- [ ] T019 [P] [US2] Integration test `test_artifact_rejection_threshold` in `tests/test_hrv.py` asserting subjects with <5% valid beats are flagged and excluded.

### Implementation for User Story 2

- [ ] T020 [US2] Implement `code/03_preprocess_hrv.py` to load raw ECG/PPG signals from WESAD/OpenNeuro derived data.
- [ ] T021 [US2] Implement signal cleaning using `hrv-analysis` library with artifact rejection thresholds (< 5% valid beats) per Edge Cases. **Explicit Requirement**: Use `hrv-analysis` functions for both cleaning AND calculation of RMSSD/SDNN. Do not implement manual calculations.
- [ ] T022 [US2] Compute HRV metrics (RMSSD, SDNN) for "Baseline" (resting) and "Stress" (TSST) phases per FR-003.
- [ ] T023 [US2] Extract Stress HRV metric as the outcome variable per FR-004.
- [ ] T024 [US2] Write output CSV to `data/derived/hrv_metrics.csv` with columns: `subject_id`, `phase`, `RMSSD`, `SDNN`.
- [ ] T025 [US2] Log exclusion of subjects with incomplete data or noisy signals without crashing the pipeline.
- [ ] T026 [US2] Ensure the preprocessing script explicitly handles the case where the downloaded WESAD data is missing the `ECG` or `PPG` channels required for HRV calculation. **Error Contract**: Raise a descriptive error and log the exclusion to `results/data_audit.md` (format: "Excluded Subject {ID}: Missing {CHANNEL} channel"), rather than proceeding with empty data. This aligns with T017's subject-exclusion logic.
- [ ] T017b [US2] Implement strict "fail loud" logic in `code/03_preprocess_hrv.py`: remove any `try/except` blocks that fallback to synthetic/mock data on **dataset download** or **signal processing** failure; ensure exceptions are raised immediately. **Exception**: If the download succeeds but the data is incomplete for a **subset of subjects** (e.g., missing ECG channels for specific subjects), the system must **exclude those subjects** and continue processing (per Edge Cases), rather than terminating the entire pipeline. Log excluded subjects to `results/data_audit.md`. **Clarification**: "Fail loud" applies to synthetic fallbacks; dataset download failures are logged and the pipeline continues to check other sources (OpenNeuro).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Regression Analysis & Reporting (Priority: P3)

**Goal**: Perform ANCOVA-style linear regression (Stress HRV ~ Interoception + Baseline HRV) or generate sensitivity report (UBDE).

**Independent Test**: Run `code/04_analyze_regression.py` on a synthetic dataset with known coefficients to verify regression output.

**Dependency**: This phase ONLY executes if T014 reports "Feasibility Success" AND T024 (HRV metrics) is complete. **IF** T014 reports "Feasibility Failure", the pipeline has already completed the UBDE calculation (in T014) and this phase is skipped.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test `test_ancova_model_fitting` in `tests/test_regression.py` asserting coefficients match expected synthetic values. **Specifics**: Generate a synthetic CSV with N=50, X=Interoception (random 0-1), Y=Stress_HRV (random 0-10), and assert coefficients match the expected values calculated from the synthetic data.
- [ ] T028 [P] [US3] Integration test `test_ubde_termination` in `tests/test_regression.py`. **Assertion**: Assert that if Interoception data is missing (simulated by empty input), the script calculates UBDE and outputs the result, **NOT** "Feasibility Failure" termination. **Correction**: The task must assert that UBDE is calculated, not that the script terminates.

### Implementation for User Story 3

- [ ] T029 [US3] Implement `code/04_analyze_regression.py` as a **Gatekeeper**. **Logic**:
 1. Check for the existence of `data/derived/hrv_metrics.csv` (output of T024).
 2. **If missing**: Log "SKIPPED: HRV metrics not found (US1 likely failed)". Exit with code 0 (no-op). **Do NOT attempt to parse `data_audit.md`**.
 3. **If present**: Load `data/derived/hrv_metrics.csv` and `results/data_audit.md` (output of T014).
 4. Parse `data_audit.md` for the exact string pattern `Feasibility Status: `.
 5. If "Feasibility Success", proceed to T031b.
 6. If "Feasibility Failure", **skip regression** (UBDE already calculated in T014). Exit with code 0.
 7. **Constraint**: T029 must NOT terminate the pipeline; it must route to the appropriate worker (T031b) or skip. **Verification**: If "Feasibility Success", verify that the model formula `Stress_HRV ~ Interoception + Baseline_HRV` is used. **Artifact**: `results/routing_decision.json` containing the decision path.
- [ ] T030 [US3] (REMOVED) UBDE calculation is now handled in T014.
- [ ] T031b [US3] **Primary Logic**: If Interoception data exists (verified in T029): Perform linear regression (Stress HRV ~ Interoception + Baseline HRV) per FR-005 using `statsmodels.formula.api.ols`. **Model Formula**: Explicitly use `Stress_HRV ~ Interoception + Baseline_HRV` to ensure baseline HRV is a covariate. **Verification**: Log the formula used to ensure it matches the requirement. **Output Format**: Write results to `results/regression_results.json` with fields: `coefficient`, `p_value`, `r_squared`, `n_obs`, `formula`.
- [ ] T031c [US3] **Output Writer**: Implement JSON output writer for `results/regression_results.json`.
- [ ] T034 [US3] Ensure results are framed strictly as associational/predictive, not causal, per Assumptions.
- [ ] T035 [US3] Add validation to ensure the regression calculation explicitly logs the sample size (N) and the observed variance used. **Log Format**:
 - **If Regression path**: Write to `results/regression.log` with message pattern: `Sample Size: {N}, Observed Variance: {Var}, R-Squared: {R2}`.
 - **Constraint**: This log is written in the regression path.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Documentation updates in `quickstart.md` and `research.md`
- [ ] T037 Code cleanup and refactoring of `utils/` modules
- [ ] T038 [P] Implement timing instrumentation in `main.py`: Log `GITHUB_JOB_DURATION` timestamps and **verify** the measured duration against the 45-minute limit for the full pipeline (Phases 1-5) defined in SC-004 and FR-007. **Specifics**: Log format: `Pipeline Start: {timestamp}, End: {timestamp}, Duration: {duration}`. **Threshold**: If duration > 45 minutes, raise `RuntimeError` and exit with code 1. **Note**: This task handles the full pipeline timing requirement.
- [ ] T038c [P] [US1] Implement specific logic in `main.py` to enforce a **reasonable time limit** for the total pipeline (Phases 1-5). **Logic**: Start a timer at the beginning of the pipeline. If the timer exceeds 45 minutes, log a warning, force the pipeline to complete with whatever data is available, and **exit with code 1** (indicating timeout) if the pipeline was not fully completed, or code 0 if it was. **Dependency**: SC-004 and FR-007. **Note**: This task complements T038b (audit-only timing).
- [ ] T039 [P] Additional unit tests for versioning logic in `tests/test_versioning.py`
- [ ] T040 [P] Run `main.py` end-to-end validation and verify `state/projects/...yaml` integrity
- [ ] T041 [P] Verify that the pipeline correctly handles the scenario where the OpenNeuro API returns a (Too Many Requests) error by implementing a retry-with-backoff strategy for metadata queries only, ensuring the audit does not fail prematurely due to rate limits. **Constraint**: This retry logic applies ONLY to metadata queries, not to the full WESAD download.

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
 - *Note*: US3 logic depends on the *output* of US1 (audit result) to decide between Regression or UBDE calculation.
 - *Note*: US3 **MUST NOT** start until T024 (HRV metrics) and T014 (Audit report) are complete.
 - *Note*: If T014 reports "Feasibility Failure", US3 skips regression (UBDE already calculated in T014).

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
4. **STOP and VALIDATE**: Test User Story 1 independently. If "Feasibility Failure" is reported, the pipeline must calculate UBDE (in T014) and generate the report. The MVP is complete.
5. Deploy/demo if ready (Feasibility Report + UBDE).

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP! Feasibility Report + UBDE)
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
 - Developer C: User Story 3 (Regression/UBDE) - **Conditional on US1 and US2 success**
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
- **Statistical Constraint**: **UBDE CALCULATION IS MANDATORY** if interoception data is missing (FR-006, US-3). The pipeline must calculate UBDE and report it in `data_audit.md`, NOT terminate silently. **Note**: UBDE is calculated only if the dataset exists (N > 0) but lacks the variable. If the dataset is missing (N=0), report "Dataset Unavailable" without UBDE.
- **Time Constraint**: Audit phase must complete within 15 minutes. (SC-001, FR-007). T038b enforces this.
- **Total Pipeline Time Constraint**: Full pipeline must complete within 45 minutes. T038c enforces this.
- **Validation Constraint**: MIT-BIH dataset must be available for HRV validation (SC-002) or mocked appropriately in tests.
- **Rate Limit Constraint**: OpenNeuro API queries must include retry logic for 429 errors to prevent premature audit failure.
- **Download Constraint**: T010 attempts a full download but respects time limits; if it fails, the pipeline logs the error and continues to T011a (OpenNeuro scan) only for OpenNeuro, skipping WESAD scan. T011a explicitly reports download failures and scans available data.
- **File Naming Correction**: All audit outputs must be written to `results/data_audit.md` (not `data/audit/`) to match the plan's `results/` directory structure and FR-006 requirements.
- **Script Naming Correction**: Audit script is `code/02_audit_metadata.py` (not `01_audit_data.py`) to align with the sequential numbering in `plan.md`.
- **State Update Script Correction**: State update script is `code/05_update_state.py` (not `04_update_state.py`) to align with the sequential numbering in `plan.md`.
- **Regression Script Correction**: Regression script is `code/04_analyze_regression.py` (not `03_analyze_regression.py`) to align with the sequential numbering in `plan.md`.
- **Preprocessing Script Correction**: Preprocessing script is `code/03_preprocess_hrv.py` (not `02_preprocess_hrv.py`) to align with the sequential numbering in `plan.md`.
- **Report Consolidation**: T014 generates the complete `data_audit.md` report immediately after the audit scan, including UBDE if needed.
- **Schema Correction**: T002 defines the schema for BIDS `events.tsv` columns, now including 'TSST', 'rest', and 'baseline', but explicitly notes that only 'Schandry'/'heartbeat' indicate the behavioral task.
- **Logic Correction**: T010 logs the error and continues to T011a (OpenNeuro scan) only. T011a explicitly reports download failures and scans available data.
- **Subset Handling**: T017a/T017b allows subject-level exclusion for missing data while maintaining "fail loud" for missing datasets.
- **Termination Logic**: If T014 reports "Feasibility Failure", the pipeline calculates UBDE internally and reports it (if N > 0). **NO TERMINATION WITHOUT UBDE** (if N > 0).
- **Output Format**: Regression results (T031b) AND UBDE results (T014) MUST be written to `results/data_audit.md` (UBDE) and `results/regression_results.json` (Regression).
- **UBDE Path Added**: T014 is the dedicated task for UBDE calculation, ensuring FR-006 compliance.
- **Log Correction**: T035 log messages are distinct for the regression path.
- **OpenNeuro Download**: T010b ensures the OpenNeuro index is downloaded for the audit with intersection logic (TSST AND (heartbeat OR interoception)).
- **Flow Correction**: T029 routes to T031b (Regression) if data exists. If data is missing, T014 has already handled UBDE.
- **Constitution Compliance**: T002e ensures `requirements.txt` is at the correct path. T008b ensures derived artifacts are checksummed.
- **Timing Compliance**: T038b handles audit timing; T038c handles total pipeline timing.
- **Parallelism Correction**: T010b is not [P] relative to T011a. T002b is not [P] relative to T002a. T010 is not [P] relative to T011a. T002e is not [P] relative to T002b.
- **Task Split**: T002c (Schema) and T002d (Validator) are split. T011b is merged into T011a. T017a is merged into T010. T041 is consolidated. T002b-verify is split. T011a is split into T011a, T011b, T011c. T038c is split into T038c and T038c-handoff (logic clarified).