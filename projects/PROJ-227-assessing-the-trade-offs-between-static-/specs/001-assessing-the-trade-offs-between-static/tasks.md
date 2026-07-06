# Tasks: Assessing the Trade-offs Between Static and Dynamic Analysis for LLM-Generated Code

**Input**: Design documents from `/specs/001-llm-analysis-tradeoffs/`
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

- [ ] T001 [P] Create project directory structure: `projects/PROJ-227-assessing-the-trade-offs-between-static-/data/raw/`, `data/processed/`, `state/`, `code/`, `tests/`

- [ ] T002 Initialize Python 3.11 project with `projects/PROJ-227-assessing-the-trade-offs-between-static-/requirements.txt` containing pinned dependencies: `datasets==2.14.0`, `pandas==2.0.3`, `scipy==1.11.0`, `pytest==7.4.0`, `requests==2.31.0`, `pyyaml==6.0.1`, `psutil==5.9.5`. Verify by running `pip install -r requirements.txt` and checking exit code 0.
- [ ] T003 [P] Configure linting and formatting: Create `.flake8` with `max-line-length=88` and `pyproject.toml` with `[tool.black] line-length = 88`. Verify by running `black --check.` and `flake8.`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement configuration management: Create `projects/PROJ-227-assessing-the-trade-offs-between-static-/code/config.yaml` with schema: `human_eval_url` (string), `codeql_path` (string), `sonar_path` (string), `max_cpu` (int), `max_ram_gb` (int). Verify by loading as dict in Python and asserting types.
- [ ] T005 [P] Create base data models and schema validators: Create `contracts/dataset.schema.yaml`, `contracts/analysis_log.schema.yaml`, `contracts/analysis_results.schema.yaml`, `contracts/dataset_manifest.schema.yaml`, `contracts/statistical_report.schema.yaml`, `contracts/tool_version.schema.yaml`. Verify by running `python -c "import jsonschema; jsonschema.validate(...)"` on sample data.
- [ ] T006 [P] Setup logging infrastructure: Create `projects/PROJ-227-assessing-the-trade-offs-between-static-/data/logs/pipeline.log`. **Format**: JSON Lines (one JSON object per line). **Hook**: Implement `psutil` hook to log `cpu_percent` and `ram_percent` every 5 seconds. **Verification**: Run script, verify `pipeline.log` exists, contains valid JSON lines, and includes CPU/RAM metrics at 5s intervals.
- [ ] T007 [P] Implement resource constraint wrapper: Create `projects/PROJ-227-assessing-the-trade-offs-between-static-/code/resource_guard.py` using `psutil` and `cgroups`. Enforce CPU ≤ 2, RAM ≤ 7GB, Time ≤ 6h. [UNRESOLVED-CLAIM: c_c537d771 — status=not_enough_info] Exit code 137 on violation. Verify by simulating resource exhaustion.
- [ ] T008 [P] Create `projects/PROJ-227-assessing-the-trade-offs-between-static-/code/hash_artifacts.py` script for versioning (Constitution V). Verify syntax only: `python -m py_compile code/hash_artifacts.py`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion & Validation (Priority: P1) 🎯 MVP

**Goal**: Download and verify ≥500 code snippets from HumanEval, CodeXGLUE, and BigCode (TheStack) across Python, JS, and Java. [UNRESOLVED-CLAIM: c_715c0a20 — status=not_enough_info]

**Independent Test**: Execute download script and verify file checksums without running analysis tools. [UNRESOLVED-CLAIM: c_ab771112 — status=not_enough_info]

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Unit test for dataset URL validation in `projects/PROJ-227-assessing-the-trade-offs-between-static-/tests/unit/test_download.py`
- [ ] T010 [P] [US1] Integration test for checksum verification in `projects/PROJ-227-assessing-the-trade-offs-between-static-/tests/integration/test_data_integrity.py`

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement `projects/PROJ-227-assessing-the-trade-offs-between-static-/code/download.py` to fetch HumanEval (Python) from `openai/human-eval` to `data/raw/humaneval.json`. **Verify**: File exists, contains ≥100 records with keys `prompt` and `test`. Calculate checksum and record in `state/checksums.json`.
- [ ] T012 [P] [US1] Implement `projects/PROJ-227-assessing-the-trade-offs-between-static-/code/download.py` to fetch CodeXGLUE (JS/Java) from `codeparrot/codeXGLUE-javascript` and `codeparrot/codeXGLUE-java` to `data/raw/`. **Logic**: If total records from HumanEval + CodeXGLUE < 500, fetch additional samples from `bigcode/the-stack` until total ≥ 500. **Verify**: Total count ≥ 500. Calculate checksums.
- [ ] T013 [P] [US1] Implement `projects/PROJ-227-assessing-the-trade-offs-between-static-/code/download.py` to fetch BigCode (TheStack) for static-only analysis if needed (see T012). Mark as `static_only` in manifest. **Verify**: Checksums recorded.
- [ ] T014 [US1] Implement stratification and manifest generation: Combine all downloaded data into `data/manifest.csv` with columns `id`, `language`, `source`, `stratum`, `static_only` (bool). **Verify**: Count ≥ 30 per language stratum (Python, JS, Java) AND total count ≥ 500. [UNRESOLVED-CLAIM: c_d75f2f79 — status=not_enough_info] If total < 500, abort with error.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Analysis Pipeline Execution (Priority: P1)

**Goal**: Execute static analysis (CodeQL/SonarQube + fallbacks) and dynamic analysis (unit tests) within resource constraints.

**Independent Test**: Run analysis container on a representative set of code snippets. and verify output logs exist.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T015 [P] [US2] Contract test for static analysis log schema in `projects/PROJ-227-assessing-the-trade-offs-between-static-/tests/contract/test_analysis_log.py`
- [ ] T016 [P] [US2] Integration test for dynamic test runner timeout handling in `projects/PROJ-227-assessing-the-trade-offs-between-static-/tests/integration/test_dynamic_oracle.py`

### Implementation for User Story 2

- [ ] T017 [US2] Implement logic to filter BigCode samples (static-only) from the manifest BEFORE dynamic analysis. Update `data/manifest.csv` to flag `static_only=True` samples. **Verify**: No `static_only=True` samples are passed to dynamic analysis tasks.
- [ ] T018 [P] [US2] Implement `projects/PROJ-227-assessing-the-trade-offs-between-static-/code/static_analysis.py` with CodeQL CLI execution wrapper. **Retry**: Max 3 retries, initial delay 2s, multiplier 2.0. **Output**: `data/processed/static_analysis_log.json` conforming to `analysis_log.schema.yaml`.
- [ ] T019 [P] [US2] Implement `projects/PROJ-227-assessing-the-trade-offs-between-static-/code/static_analysis.py` with SonarQube scanner execution wrapper. **Fallback**: PyLint (Python), ESLint (JS) if primary tools fail. **Output**: Append to `data/processed/static_analysis_log.json`.
- [ ] T020 [P] [US2] Implement `projects/PROJ-227-assessing-the-trade-offs-between-static-/code/dynamic_analysis.py` to execute unit tests via `pytest` (Python), `jest` (JS), and `junit` (Java). **Logic**: Mark snippets as `untestable_dynamic` if no test exists. **Output**: `data/processed/dynamic_analysis_log.json`.
- [ ] T021 [US2] Generate `data/processed/analysis_logs.json` with standardized schema (issues found, pass/fail status) by merging static and dynamic logs.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Results Aggregation & Statistical Reporting (Priority: P2)

**Goal**: Compute Issue Detection Rate, Pass Rate, and perform statistical correlation (Spearman/Chi-squared) with sensitivity analysis.

**Independent Test**: Process mock logs and verify report contains correlation coefficients and p-values.

**⚠️ PLAN RECONCILIATION NOTE**:
The Spec (FR-004, FR-005) demands Precision/Recall/F1 and McNemar's test. However, the Plan (Methodology) explicitly rejects these as scientifically invalid due to lack of security ground truth and distinct constructs. The tasks below implement the Plan's valid approach (Issue Detection Rate, Spearman/Chi-squared) AND include a formal Spec Amendment record.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T022 [P] [US3] Unit test for Spearman correlation calculation in `projects/PROJ-227-assessing-the-trade-offs-between-static-/tests/unit/test_statistics.py`
- [ ] T023 [P] [US3] Integration test for stratified reporting in `projects/PROJ-227-assessing-the-trade-offs-between-static-/tests/integration/test_aggregation.py`

### Implementation for User Story 3

- [ ] T024 [P] [US3] Implement `projects/PROJ-227-assessing-the-trade-offs-between-static-/code/aggregation.py` to calculate **Issue Detection Rate** (static) and **Pass Rate** (dynamic). **Output**: `data/processed/issue_detection_rate.json`. **Note**: Explicitly output 'N/A' for Precision/Recall/F1 with `deviation_note: "See SPEC_AMENDMENT_001"`.
- [ ] T025 [P] [US3] Implement `projects/PROJ-227-assessing-the-trade-offs-between-static-/code/aggregation.py` to compute **Spearman's Rank Correlation** between static issue density and dynamic pass/fail. **Output**: `data/processed/correlation_results.json`. **Note**: Explicitly output 'N/A' for McNemar's test with `deviation_note: "See SPEC_AMENDMENT_001"`.
- [ ] T026 [P] [US3] Implement `projects/PROJ-227-assessing-the-trade-offs-between-static-/code/aggregation.py` to perform **Chi-squared Test of Independence**. **Output**: Append to `data/processed/correlation_results.json`.
- [ ] T027 [US3] Implement timeout handling for dynamic execution: **Max 30 minutes per snippet**. Use `psutil` to send **SIGKILL** on timeout. **Output**: Log timeout events to `data/logs/timeouts.json`. **Verify**: Process is terminated after 30 mins; log entry contains `SIGKILL` and duration.
- [ ] T028 [US3] Implement stratification logic to run tests per language (if n ≥ 30). **Output**: `data/processed/stratified_test_results.json`.
- [ ] T029 [US3] Implement sensitivity analysis sweep: **Execute statistical tests for each alpha in the set {0.01, 0.05, 0.1}** as required by FR-007. **Output**: `data/processed/detection_rate_variation.json` containing comparative data. **Verify**: Report includes rates for exactly these three values.
- [ ] T030 [US3] Implement Bonferroni correction for **multiple independent statistical tests (across languages)** as per Plan. **Output**: `data/processed/corrected_results.json`. **Note**: Explicitly state in report: "Applied to independent tests (across languages) per Plan, deviating from FR-008 'multiple metrics' phrasing. See SPEC_AMENDMENT_001."
- [ ] T031 [US3] Generate `data/processed/statistical_report.json` with metrics, p-values, stratified results, and explicit deviation notes for FR-004/FR-005 referencing `SPEC_AMENDMENT_001`.
- [ ] T032 [US3] Execute `projects/PROJ-227-assessing-the-trade-offs-between-static-/code/hash_artifacts.py` to update `state/projects/PROJ-227-assessing-the-trade-offs-between-static-.yaml` with final hashes and tool versions. **Verify**: YAML updated with `artifact_hashes` and `tool_versions`.
- [ ] T033 [US3] Explicitly log and verify tool versions (CodeQL, SonarQube) in `state/projects/PROJ-227-assessing-the-trade-offs-between-static-.yaml` per Constitution Principle VI.
- [ ] T099 [US3] **Spec Amendment**:
 1. Create `projects/PROJ-227-assessing-the-trade-offs-between-static-/specs/001-assessing-the-trade-offs-between-static/SPEC_AMENDMENT_001.md`. Document the deviation from FR-004 (Precision/Recall/F1 -> Issue Detection Rate) and FR-005 (McNemar -> Spearman/Chi-squared) due to lack of security ground truth and distinct constructs.
 2. **Update spec.md**: Modify FR-004 and FR-005 in `spec.md` to explicitly state they are **SUPERSEDED** by the Plan's methodology (Issue Detection Rate, Spearman/Chi-squared) and reference `SPEC_AMENDMENT_001`. Ensure the Spec document itself reflects the valid approach to resolve the internal contradiction.
 3. Reference this ID in T024, T025, T031.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Documentation updates in `docs/` and `README.md`
- [ ] T035 Code cleanup and refactoring of analysis scripts
- [ ] T036 Performance optimization for parallel snippet processing (within 2 CPU limit)
- [ ] T037 [P] Additional unit tests for edge cases (timeout, missing tests, tool failures) in `projects/PROJ-227-assessing-the-trade-offs-between-static-/tests/unit/`
- [ ] T038 Security hardening of dataset download URLs and local file handling
- [ ] T039 Run `quickstart.md` validation to ensure end-to-end reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data availability
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 output
- **Polish**: Depends on all stories being complete

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Download logic before analysis logic
- Analysis logic before aggregation logic
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
Task: "Unit test for dataset URL validation in tests/unit/test_download.py"
Task: "Integration test for checksum verification in tests/integration/test_data_integrity.py"

# Launch all download implementations together:
Task: "Implement code/download.py to fetch HumanEval (Python)"
Task: "Implement code/download.py to fetch CodeXGLUE (JS/Java) and BigCode (TheStack)"
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
 - Developer A: User Story 1 (Data Ingestion)
 - Developer B: User Story 2 (Analysis Execution)
 - Developer C: User Story 3 (Aggregation & Stats)
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
- **Critical Constraint**: All tasks must run on free CPU-only CI with limited core counts and memory, without GPU acceleration. No 8-bit/4-bit quantization or heavy model training.
- **Data Integrity**: All datasets must be from real, verified sources (HuggingFace, GitHub). No synthetic data generation.
- **Statistical Validity**: No Precision/Recall/F1 for static analysis (no security ground truth). Use Issue Detection Rate. No McNemar's test (distinct constructs). Use Spearman/Chi-squared.
- **Plan Reconciliation**: Tasks implement the Plan's scientifically valid approach. Spec FR-004/FR-005 are noted as contradictory and require amendment (SPEC_AMENDMENT_001).