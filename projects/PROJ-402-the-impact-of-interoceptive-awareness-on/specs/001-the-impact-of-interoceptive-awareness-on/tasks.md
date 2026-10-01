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

- [ ] T001 Create project structure per implementation plan (`code/`, `tests/`, `data/`, `results/`, `data/raw/`, `data/derived/`, `data/audit/`, `results/logs/`). **Verification**: Verify directory tree exists.
- [X] T002a [P] Create `requirements.txt` with pinned dependencies (`pandas==2.0.3`, `numpy==1.24.3`, `scikit-learn==1.3.0`, `hrv-analysis==1.1.0`, `pybids==0.16.5`, `requests==2.31.0`, `pyyaml==6.0.1`, `jsonschema==4.19.0`, `statsmodels==0.14.0`, `wfdb==4.1.0`). **Note**: This task creates the file content only.
- [ ] T002b [P] Install dependencies from `requirements.txt` using `pip install -r requirements.txt`. **Verification**: Run `pip list` to verify packages installed. Run `python -c "import pandas; import numpy; import sklearn; import hrv_analysis; import pybids; import requests; import yaml; import jsonschema; import statsmodels; import wfdb"`. Exit code 0 indicates success. **Artifact**: `venv` directory.
- [X] T002c [P] Create `contracts/dataset.schema.yaml` and write the exact JSON Schema content. **Schema Content**: The YAML MUST define a JSON Schema for `events.tsv` with `type: object` and `properties` for `task` (string, enum: ['Schandry', 'heartbeat', 'TSST', 'rest', 'baseline']), `onset` (number), `duration` (number), `value` (number, optional), and `trial_type` (string, optional). The `task` column is REQUIRED. **Note**: 'Schandry' and 'heartbeat' are the ONLY values that indicate the presence of the behavioral task per FR-002. 'TSST', 'rest', and 'baseline' are included for phase identification. The validator (T002d) must distinguish between valid task types and behavioral indicators.
- [X] T002c-audit-schema [P] Create `contracts/audit.schema.yaml`. **Schema Content**: Define schema for `results/audit_status.json` with properties: `status` (enum: ['Success', 'Failure: Variable Missing', 'Failure: Dataset Unavailable']), `feasible` (boolean), `n_subjects` (integer), `sigma_estimate` (number, optional), `ubi_de` (number, optional), `sources_scanned` (array of strings).
- [X] T002c-hrv-schema [P] Create `contracts/hrv_metrics.schema.yaml`. **Schema Content**: Define schema for `data/derived/hrv_metrics.csv` with columns: `subject_id`, `phase`, `RMSSD`, `SDNN`.
- [X] T002c-output-schema [P] Create `contracts/output.schema.yaml`. **Schema Content**: Define schema for `results/data_audit.md` structure (markdown headers and sections).
- [X] T002c-regression-schema [P] Create `contracts/regression_output.schema.yaml`. **Schema Content**: Define schema for `results/regression_results.json` with fields: `coefficient`, `p_value`, `r_squared`, `n_obs`, `formula`.
- [ ] T002d [P] Implement `code/utils/schema_validator.py` to load the **pre-existing** `contracts/dataset.schema.yaml` (created in T002c) and validate BIDS `events.tsv` files against it. **Error Contract**: Exit code indicating local file missing, schema mismatch, or invalid JSON/TSV format. **Specific Logic**: If the `task` column contains 'TSST', 'rest', or 'baseline', the validator must flag these as valid *phase* tasks but NOT as valid *behavioral* tasks. **Note**: This task implements the *validation logic*. **Dependency**: T002c must complete first (schema file must exist).
- [X] T003 [P] Configure linting (flake8/black) and formatting tools in `pyproject.toml`. **Specific Configuration**: Set `black --line-length` and `flake --max-line-length` in `pyproject.toml` to enforce a consistent line-length limit. under `[tool.black]` and `[tool.flake8]` sections respectively. **Verification**: Run `black --check.` and `flake8.` to ensure no configuration errors.
- [ ] T002e [P] Move or copy `requirements.txt` to the Constitution-mandated path `projects/PROJ-402-the-impact-of-interoceptive-awareness-on/code/requirements.txt`. **Verification**: Verify file exists at the specific path and is readable. **Dependency**: T002b must complete first (file must exist and be valid). **Note**: Required by Constitution Principle I (Reproducibility). Note: Plan.md structure diagram shows `code/requirements.txt` at root; Constitution requires nested path. Constitution takes precedence.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Implement `code/utils/hrv_utils.py` for artifact rejection (threshold < 5% valid beats) and signal validation
- [X] T007 [P] Implement `code/05_update_state.py` to compute SHA-256 hashes for `data/` and `results/` artifacts and update `state/projects/001-impact-of-interoceptive-awareness.yaml` per Constitution Principle V.
- [ ] T008 [P] Configure `pytest` environment with random seed pinning in `conftest.py`. **Constraint**: Ensure data download scripts (T010-orchestrator) enforce deterministic behavior via checksum verification as required by Constitution Principle I. **Specific Requirement**: T008 must explicitly require that `code/01_download_data.py` logs the SHA-256 checksum of every downloaded file to `results/checksums.txt` before the script exits. Seed pinning alone is insufficient for reproducibility of external fetches. **Note**: Full pipeline timing (including non-test scripts) is handled by T006, not pytest config. **Dependency**: `requirements.txt` must be installed (T002b) and located at `projects/PROJ-402.../code/` (T002e). **Dependency**: T008-seeds must complete first.
- [X] T008-seeds [P] Implement `code/utils/seeds.py` to define and export random seeds used by production scripts and tests. **Constraint**: Ensure all production scripts (01_download_data.py, 02_audit_metadata.py, etc.) import and use seeds from this module. **Verification**: Verify that `import utils.seeds` works and seeds are accessible. **Note**: T008 (pytest config) must reference this module.
- [X] T008b [P] Implement logic in `code/05_update_state.py` (or a dedicated script) to checksum ALL files under `data/`, including derived artifacts like `data/derived/hrv_metrics.csv`. **Constraint**: Update `state/projects/.../artifact_hashes` with the new hashes. **Verification**: Run the script and verify that `data/derived/` files are included in the hash map. **Dependency**: T007.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Availability Audit (Priority: P1) 🎯 MVP

**Goal**: Verify feasibility by scanning WESAD and OpenNeuro for specific behavioral interoception tasks (Schandry) and stress paradigms (TSST).

**Independent Test**: Execute `code/02_audit_metadata.py` on a mock directory structure to verify it correctly identifies missing "Schandry" tasks and outputs `results/data_audit.md`.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Implement test suite for US1 in `tests/test_audit.py`. **Specific Functions**: (1) `test_audit_logic_returns_failure_status` asserts that the audit logic correctly identifies missing 'Schandry' tasks and returns a 'Feasibility Failure' status using **mocked inputs** (not file I/O). **Mock Data Contract**: The mock input must be a JSON list of objects with keys `subject_id`, `task`, `phase`. Example: `[{"subject_id": "01", "task": "TSST", "phase": "stress"}]`. The assertion must check that the function returns `{"status": "Feasibility Failure", "missing_tasks": ["Schandry"]}`. (2) `test_audit_flow_mock_data` asserts the logic correctly routes to UBDE calculation or regression paths based on mock data. Write tests before implementation. **Correction**: The test must assert the logic's internal state or return value, not the final file content generated by T011.

### Implementation for User Story 1

- [ ] T011-audit-implementation [US1] Implement `code/02_audit_metadata.py` to perform the **complete** Data Availability Audit. **Logic**:
 1. **Local BIDS Scan**: Check if `data/raw/wesad/` exists (if T010-orchestrator ran successfully) or if local data is available. If yes, scan local `**/events.tsv` files for `task` labels matching 'Schandry', 'heartbeat', or 'TSST' (case-insensitive) as per FR-002. Use `code/utils/schema_validator.py` (T002d) to validate `events.tsv` structure.
 2. **Index Scan**: Download OpenNeuro index (metadata) for studies containing **BOTH** "TSST" **AND** ("heartbeat" **OR** "interoception") keywords. Scan the index for matching studies. **Note**: If T010-orchestrator fails to download WESAD, this step continues independently.
 3. **Aggregation**: Merge scan results. Determine if 'Schandry' or 'heartbeat' is present in ANY source.
 4. **Feasibility Decision**:
    - **Case 1 (Dataset Unavailable)**: If NO data sources are available (WESAD missing + OpenNeuro empty), set feasibility flag to "Failure: Dataset Unavailable". **Action**: Do NOT calculate UBDE. Report the reason as "No data available for analysis".
    - **Case 2 (Variable Missing)**: If data exists (N > 0) but 'Schandry'/'heartbeat' is NOT found, set feasibility flag to "Failure: Variable Missing". **Action**: Calculate the Upper Bound of Detectable Effect (UBDE) using the formula: `UBDE = t_(-alpha/2, df) * sqrt(2 * sigma^2 / N)`. Use a **community-standard sigma estimate** (e.g., from literature) for `sigma^2` and log the source. Inject the calculated UBDE value directly into the `data_audit.md` report.
    - **Case 3 (Data Exists)**: If 'Schandry'/'heartbeat' is found, set feasibility flag to "Success".
 5. **Output**:
    - Generate `results/audit_status.json` with fields: `status`, `feasible`, `n_subjects`, `sigma_estimate`, `ubi_de`, `sources_scanned`.
    - Generate `results/data_audit.md` explicitly stating presence/absence of required variables per FR-006.
 6. **Timing**: Enforce a time-bound hard stop for the audit phase. If timeout, log warning and exit with code 1 if no data processed, or code 0 if partial data processed.
 7. **Error Handling**: Exit with code 0 if report generated, non-zero if download failed and no local scan possible.
 **Dependency**: T002c, T002d, T002c-audit-schema must complete first. **Dependency**: T011 runs **BEFORE** T010-orchestrator to allow metadata-only audit if possible. If T011 finds local data, it proceeds; if not, it may trigger T010-orchestrator (or wait for it to run in parallel if configured). **Note**: This task is self-contained (implements the entire script).
- [ ] T010-orchestrator [US1] Implement `code/01_download_data.py` to download WESAD and OpenNeuro index. **Logic**:
 1. **Download WESAD**: Download from Zenodo (DOI: 10.5281/zenodo.1292932) to `data/raw/wesad/WESAD.zip`. **Constraint**: Use `requests` with timeout. **Strict Requirement**: If download fails, log CRITICAL error, delete partial file, and **ABORT WESAD path**. Continue to OpenNeuro path. **Note**: "Fail loud" logic (no synthetic fallback).
 2. **Download OpenNeuro**: Download index (metadata) for studies with "TSST" and ("heartbeat" OR "interoception"). Save to `data/raw/openneuro/index.json`. **Constraint**: If download fails, log error but **DO NOT EXIT**. Continue to local scan.
 3. **Validation**: After download, extract WESAD (if successful) and call `code/utils/schema_validator.py` (T002d) to validate `events.tsv` files in the extracted BIDS structure. Log checksums to `results/checksums.txt`.
 4. **Output**: Downloaded files and checksum log.
 **Dependency**: T002c, T002d, T002c-dataset-schema must complete first. **Dependency**: T010-orchestrator can run in parallel with T011-audit-implementation **IF** local data exists. If T011 finds no local data, T010-orchestrator is required. **Note**: T011 (audit) runs first to check for local data; T010 (download) runs if local data is missing.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Physiological Signal Preprocessing (Priority: P2)

**Goal**: Extract and compute HRV metrics (RMSSD, SDNN) from ECG/PPG signals for baseline and stress phases.

**Independent Test**: Run `code/03_preprocess_hrv.py` on a small subset of WESAD data and verify output CSV contains valid RMSSD/SDNN values with no NaNs for complete subjects.

**Dependency**: This phase ONLY executes if T011-audit-implementation reports "Success" in `results/audit_status.json`.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test `test_compute_rmssd_against_mitbih` in `tests/test_hrv.py` asserting calculated RMSSD matches PhysioNet reference within 1% tolerance. **Note**: Ensure MIT-BIH dataset is downloaded from PhysioNet via `wfdb` library. **Specifics**: Use records '100' and '101'. The test must download the ECG signal and the annotation file for these records, compute RMSSD using `hrv-analysis`, and compare the result against the known ground-truth RMSSD values derived from the annotations (or a verified reference value from the literature/PhysioNet database). **Constraint**: Do NOT generate mock data; use real MIT-BIH data. **Verification**: Assert that the computed RMSSD is within 1% of the reference value.
- [ ] T019 [P] [US2] Integration test `test_artifact_rejection_threshold` in `tests/test_hrv.py` asserting subjects with <5% valid beats are flagged and excluded.

### Implementation for User Story 2

- [ ] T020-preprocess [US2] Implement `code/03_preprocess_hrv.py` to load raw ECG/PPG signals from WESAD/OpenNeuro derived data. **Logic**:
 1. Load signals from `data/raw/`.
 2. Apply signal cleaning using `hrv-analysis` library with artifact rejection thresholds (< 5% valid beats) per Edge Cases.
 3. Compute HRV metrics (RMSSD, SDNN) for "Baseline" (resting) and "Stress" (TSST) phases per FR-003.
 4. Extract Stress HRV metric as the outcome variable per FR-004.
 5. Write output CSV to `data/derived/hrv_metrics.csv` with columns: `subject_id`, `phase`, `RMSSD`, `SDNN`.
 6. **Fail Loud**: Remove any `try/except` blocks that fallback to synthetic/mock data on dataset download or signal processing failure. Raise exceptions immediately. **Exception**: If data is incomplete for a **subset of subjects** (e.g., missing ECG channels), exclude those subjects and continue processing (per Edge Cases). Log excluded subjects to `results/data_audit.md` (format: "Excluded Subject {ID}: Missing {CHANNEL} channel").
 7. **Error Handling**: Explicitly handle missing ECG/PPG channels. Raise descriptive error if required channels are missing for a subject.
 **Dependency**: T011-audit-implementation must report "Success". **Dependency**: T005 (hrv_utils) must complete first. **Note**: This task is self-contained (implements the entire script).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Regression Analysis & Reporting (Priority: P3)

**Goal**: Perform ANCOVA-style linear regression (Stress HRV ~ Interoception + Baseline HRV) or generate sensitivity report (UBDE).

**Independent Test**: Run `code/04_analyze_regression.py` on a synthetic dataset with known coefficients to verify regression output.

**Dependency**: This phase ONLY executes if T011-audit-implementation reports "Success" AND T020-preprocess (HRV metrics) is complete. **IF** T011 reports "Failure", the pipeline has already completed the UBDE calculation (in T011) and this phase is skipped.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test `test_ancova_model_fitting` in `tests/test_regression.py` asserting coefficients match expected synthetic values. **Specifics**: Generate a synthetic CSV with N=50, X=Interoception (random 0-1), Y=Stress_HRV (random 0-10), and assert coefficients match the expected values calculated from the synthetic data.
- [ ] T028 [P] [US3] Integration test `test_ubde_termination` in `tests/test_regression.py`. **Assertion**: Assert that if Interoception data is missing (simulated by empty input), the script calculates UBDE and outputs the result, **NOT** "Feasibility Failure" termination. **Correction**: The task must assert that UBDE is calculated, not that the script terminates.

### Implementation for User Story 3

- [ ] T029 [US3] Implement `code/04_analyze_regression.py` as a **Gatekeeper** and **Analyzer**. **Logic**:
 1. Check for the existence of `data/derived/hrv_metrics.csv` (output of T020-preprocess).
 2. Load `results/audit_status.json` (output of T011-audit-implementation). **Note**: Do NOT parse `data_audit.md`. Use structured JSON.
 3. **If `audit_status.json` status is "Failure"**: Log "SKIPPED: Feasibility Failure (UBDE already calculated in T011)". Exit with code 0 (no-op).
 4. **If `audit_status.json` status is "Success"**: Proceed to regression.
 5. **Regression**: Perform linear regression (Stress HRV ~ Interoception + Baseline HRV) per FR-005 using `statsmodels.formula.api.ols`. **Model Formula**: Explicitly use `Stress_HRV ~ Interoception + Baseline_HRV` to ensure baseline HRV is a covariate.
 6. **Output**: Write results to `results/regression_results.json` with fields: `coefficient`, `p_value`, `r_squared`, `n_obs`, `formula`.
 7. **Validation**: Ensure results are framed strictly as associational/predictive, not causal, per Assumptions. Log sample size (N) and observed variance.
 **Dependency**: T011-audit-implementation and T020-preprocess must complete first. **Note**: T029 depends on T011's structured JSON output, not the markdown report.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Documentation updates in `quickstart.md` and `research.md`
- [ ] T037 Code cleanup and refactoring of `utils/` modules
- [ ] T006 [P] Implement `code/06_capture_timing.py` to log `GITHUB_JOB_DURATION` timestamps and verify the measured duration against the 45-minute limit for the full pipeline (Phases 1-5) defined in SC-004 and FR-007. **Specifics**: Log format: `Pipeline Start: {timestamp}, End: {timestamp}, Duration: {duration}`. **Threshold**: If duration > 45 minutes, raise `RuntimeError` and exit with code 1. **Note**: This task handles both phase-level (15 min) and total-pipeline (45 min) timing instrumentation.
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
 - *Note*: US3 **MUST NOT** start until T020 (HRV metrics) and T011 (Audit report) are complete.
 - *Note*: If T011 reports "Feasibility Failure", US3 skips regression (UBDE already calculated in T011).

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
4. **STOP and VALIDATE**: Test User Story 1 independently. If "Feasibility Failure" is reported, the pipeline must calculate UBDE (in T011) and generate the report. The MVP is complete.
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
- **Time Constraint**: Audit phase must complete within 15 minutes. (SC-001, FR-007). T011-audit-implementation enforces this.
- **Total Pipeline Time Constraint**: Full pipeline must complete within 45 minutes. T006 enforces this.
- **Validation Constraint**: MIT-BIH dataset must be available for HRV validation (SC-002) or mocked appropriately in tests.
- **Rate Limit Constraint**: OpenNeuro API queries must include retry logic for 429 errors to prevent premature audit failure.
- **Download Constraint**: T010-orchestrator attempts a full download but respects time limits; if it fails, the pipeline logs the error and continues to T011 (OpenNeuro scan) only for OpenNeuro, skipping WESAD scan. T011 explicitly reports download failures and scans available data.
- **File Naming Correction**: All audit outputs must be written to `results/data_audit.md` (not `data/audit/`) to match the plan's `results/` directory structure and FR-006 requirements.
- **Script Naming Correction**: Audit script is `code/02_audit_metadata.py` (not `01_audit_data.py`) to align with the sequential numbering in `plan.md`.
- **State Update Script Correction**: State update script is `code/05_update_state.py` (not `04_update_state.py`) to align with the sequential numbering in `plan.md`.
- **Regression Script Correction**: Regression script is `code/04_analyze_regression.py` (not `03_analyze_regression.py`) to align with the sequential numbering in `plan.md`.
- **Preprocessing Script Correction**: Preprocessing script is `code/03_preprocess_hrv.py` (not `02_preprocess_hrv.py`) to align with the sequential numbering in `plan.md`.
- **Report Consolidation**: T011 generates the complete `data_audit.md` report immediately after the audit scan, including UBDE if needed.
- **Schema Correction**: T002 defines the schema for BIDS `events.tsv` columns, now including 'TSST', 'rest', and 'baseline', but explicitly notes that only 'Schandry'/'heartbeat' indicate the behavioral task.
- **Logic Correction**: T010 logs the error and continues to T011 (OpenNeuro scan) only. T011 explicitly reports download failures and scans available data.
- **Subset Handling**: T020 allows subject-level exclusion for missing data while maintaining "fail loud" for missing datasets.
- **Termination Logic**: If T011 reports "Feasibility Failure", the pipeline calculates UBDE internally and reports it (if N > 0). **NO TERMINATION WITHOUT UBDE** (if N > 0).
- **Output Format**: Regression results (T029) AND UBDE results (T011) MUST be written to `results/data_audit.md` (UBDE) and `results/regression_results.json` (Regression).
- **UBDE Path Added**: T011 is the dedicated task for UBDE calculation, ensuring FR-006 compliance.
- **Log Correction**: T029 log messages are distinct for the regression path.
- **OpenNeuro Download**: T010-orchestrator ensures the OpenNeuro index is downloaded for the audit with intersection logic (TSST AND (heartbeat OR interoception)).
- **Flow Correction**: T029 routes to T029 (Regression) if data exists. If data is missing, T011 has already handled UBDE.
- **Constitution Compliance**: T002e ensures `requirements.txt` is at the correct path. T008b ensures derived artifacts are checksummed.
- **Timing Compliance**: T006 handles audit and total pipeline timing.
- **Parallelism Correction**: T010-orchestrator is not [P] relative to T011-audit-implementation if local data is missing. T002b is not [P] relative to T002a. T002e is not [P] relative to T002b.
- **Task Split**: T002c (Schema) and T002d (Validator) are split. T011-audit-implementation merges T011a, T011b, T011c, T014, T015, T038b. T017a is merged into T020. T041 is consolidated. T002b-verify is merged into T002b. T000-validate-hrv is added. T006 is restored. T002c-audit-schema, T002c-hrv-schema, T002c-output-schema, T002c-regression-schema are added.