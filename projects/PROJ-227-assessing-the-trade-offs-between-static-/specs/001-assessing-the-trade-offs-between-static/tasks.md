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

- [ ] T001a [P] Create project directory structure: `projects/PROJ-227-assessing-the-trade-offs-between-static-/data/raw/`, `data/processed/`, `state/`, `code/`, `tests/`, `tests/unit/`, `tests/integration/`, `tests/contract/`. **Verify**: `ls -R` shows all directories exist.
- [ ] T001b [P] Create `.gitignore` in `projects/PROJ-227-assessing-the-trade-offs-between-static-/` to exclude `data/raw/*`, `data/processed/*`, `*.log`, `__pycache__/`, `.venv/`, `state/*.yaml` (except template). **Verify**: `git check-ignore` confirms paths are ignored.

- [ ] T002a [P] Initialize a Python virtualenv in `projects/PROJ-227-assessing-the-trade-offs-between-static-/`.venv`. **Verify**: `source.venv/bin/activate && python --version` returns 3.11.x. <!-- ATOMIZE: requested -->
- [ ] T002b [P] Initialize `projects/PROJ-227-assessing-the-trade-offs-between-static-/requirements.txt` containing pinned dependencies: `datasets==2.14.0`, `pandas==2.0.3`, `scipy==1.11.0`, `pytest==7.4.0`, `requests==2.31.0`, `pyyaml==6.0.1`, `psutil==5.9.5`, `jsonschema==4.19.0`, `filelock==3.12.0`. **Verify**: `pip install -r requirements.txt` succeeds without errors.

- [X] T003 [P] Configure linting and formatting: Create `.flake8` with `max-line-length=88` and `pyproject.toml` with `[tool.black] line-length = 88`. Verify by running `black --check.` and `flake8.`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement configuration management: Create `projects/PROJ-227-assessing-the-trade-offs-between-static-/code/config.yaml` with schema: `human_eval_url` (string), `codeql_path` (string), `sonar_path` (string), `max_cpu` (int), `max_ram_gb` (int). Verify by loading as dict in Python and asserting types.
- [ ] T005 [P] Create base data models and schema validators: Create `contracts/dataset.schema.yaml`, `contracts/analysis_log.schema.yaml`, `contracts/analysis_results.schema.yaml`, `contracts/dataset_manifest.schema.yaml`, `contracts/statistical_report.schema.yaml`, `contracts/tool_version.schema.yaml`. Verify by running `python -c "import jsonschema; jsonschema.validate(...)"` on sample data.
- [ ] T006 [P] Setup logging infrastructure: Create `projects/PROJ-227-assessing-the-trade-offs-between-static-/data/logs/pipeline.log`. **Format**: JSON Lines (one JSON object per line). **Schema**: Each line MUST be a JSON object with keys: `timestamp` (ISO8601 string), `cpu_percent` (float), `ram_percent` (float), `pid` (int). **Hook**: Implement `psutil` hook to log `cpu_percent` and `ram_percent` at regular intervals. **Concurrency**: Use `filelock` library to ensure thread-safe writes to `pipeline.log`. **Verification**: Run script, verify `pipeline.log` exists, contains valid JSON lines with the specified schema, includes CPU/RAM metrics at 5s intervals, and handles concurrent writes without corruption.
- [X] T007 [P] Implement resource constraint wrapper: Create `projects/PROJ-227-assessing-the-trade-offs-between-static-/code/resource_guard.py` using `psutil` (monitoring and process termination). **Logic**: Monitor CPU/RAM. If CPU > 2 cores or RAM > 7GB, log warning and terminate the current analysis process (SIGKILL) after 30s grace period. **Verification**: Simulate resource exhaustion; verify process is terminated and exit code is 137 or similar.
- [X] T008 [P] Create `projects/PROJ-227-assessing-the-trade-offs-between-static-/code/hash_artifacts.py` script for versioning (Constitution V). Verify syntax only: `python -m py_compile code/hash_artifacts.py`.
- [ ] T009 [P] [Constitution VI] **Execute** `code/hash_artifacts.py` to log initial tool versions (CodeQL, SonarQube, pytest) into `state/projects/PROJ-227-assessing-the-trade-offs-between-static-.yaml` under `tool_versions` **BEFORE** any analysis begins. **Verification**: YAML file updated with `tool_versions` block containing version strings and timestamps. **Dependency**: Must run after T008 (syntax check) and before T011 (data download).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion & Validation (Priority: P1) 🎯 MVP

**Goal**: Download and verify code snippets from HumanEval, CodeXGLUE, and BigCode (TheStack) across Python, JS, and Java.

**Independent Test**: Execute download script and verify file checksums without running analysis tools.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Unit test for dataset URL validation in `projects/PROJ-227-assessing-the-trade-offs-between-static-/tests/unit/test_download.py`
- [X] T010 [P] [US1] Integration test for checksum verification in `projects/PROJ-227-assessing-the-trade-offs-between-static-/tests/integration/test_data_integrity.py`

### Implementation for User Story 1

- [ ] T011a [P] [US1] Implement `code/download.py` function `fetch_humaneval()`: Fetch **HumanEval** from `openai/human-eval` to `data/raw/humaneval.json`. **Logic**: Use `load_dataset` with `split='test'`. **Retry**: Exponential backoff (max 3 retries). **State**: On success, write count to `state/download_counts.json` key `humaneval_count`. **Verify**: File exists, checksum matches.
- [ ] T011b [P] [US1] Implement `code/download.py` function `fetch_humaneval_x()`: Fetch **HumanEval-X** (JS/Java) from `codeparrot/humaneval-x`. **Logic**: Fetch `split='js'` to `data/raw/humaneval-x-js.json` and `split='java'` to `data/raw/humaneval-x-java.json`. **Retry**: Exponential backoff. **State**: Write counts to `state/download_counts.json` keys `humaneval_x_js_count`, `humaneval_x_java_count`. **Verify**: Files exist, checksums match.

- [ ] T012a [P] [US1] Implement `code/download.py` function `fetch_codexglue()`: Fetch **CodeXGLUE** subsets from `codeparrot/codexglue`. **Logic**: Filter by language for JS/Java. **Retry**: Exponential backoff. **State**: Write counts to `state/download_counts.json` keys `codexglue_js_count`, `codexglue_java_count`. **Verify**: Files exist, checksums match.

- [ ] T013a [P] [US1] Implement `code/download.py` function `fetch_bigcode()`: Fetch **BigCode (TheStack)** subsets from `bigcode/the-stack-dedup-code`. **Logic**: Use `streaming=True` and `itertools.islice` to fetch a representative sample (e.g., first 1000 per language: Python, JS, Java) to `data/raw/the-stack-*.json`. **Retry**: Exponential backoff. **State**: Write counts to `state/download_counts.json` keys `bigcode_py_count`, `bigcode_js_count`, `bigcode_java_count`. **Verify**: Files exist, checksums match.

- [ ] T014 [US1] Implement **Aggregate Validation & Abort**: Create `code/validate_manifest.py` to combine all downloaded data into `data/manifest.csv` and perform the FR-001 check. **Dependency**: MUST wait for COMPLETION of T011a, T011b, T012a, T013a. **Logic**:
 - Read `state/download_counts.json` to retrieve all individual counts.
 - Calculate `total_snippets = sum(all_counts)`.
 - **Aggregate Validation**: If `total_snippets < 500`, **ABORT** with error "Insufficient sample size (<500)".
 - For BigCode samples, explicitly set `static_only=True` in `manifest.csv`.
 - For HumanEval/CodeXGLUE samples, set `static_only=False`.
 - **Stratification Check**: Count snippets with dynamic tests (HumanEval + HumanEval-X + CodeXGLUE) per language. If any language (Python, JS, Java) has < 30 dynamic-capable snippets, **ABORT** and log "Insufficient dynamic samples for stratified analysis".
 - **Verify**: File exists, contains all expected columns, and passes the n≥30 threshold for all dynamic languages.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Analysis Pipeline Execution (Priority: P1)

**Goal**: Execute static analysis (CodeQL/SonarQube + fallbacks) and dynamic analysis (unit tests) within resource constraints.

**Independent Test**: Run analysis container on a representative set of code snippets. and verify output logs exist.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T015 [P] [US2] Contract test for static analysis log schema in `projects/PROJ-227-assessing-the-trade-offs-between-static-/tests/contract/test_analysis_log.py`
- [ ] T016 [P] [US2] Integration test for dynamic test runner timeout handling in `projects/PROJ-227-assessing-the-trade-offs-between-static-/tests/integration/test_dynamic_oracle.py`

### Implementation for User Story 2

- [ ] T018 [P] [US2] Implement `projects/PROJ-227-assessing-the-trade-offs-between-static-/code/static_analysis.py` with **Unified Static Analysis Pipeline**.
 1. **Primary Tools**: CodeQL CLI execution wrapper and SonarQube scanner execution wrapper.
 2. **Retry Logic**: Retry up to 3 times on tool crash (non-zero exit code).
 3. **Fallback Trigger**: If CodeQL or SonarQube returns non-zero exit code after 3 retries, **immediately** invoke fallback (PyLint for Python, ESLint for JS) for that specific snippet.
 4. **Fallback Output**: Write fallback results to `data/processed/static_analysis_fallback_log.json`.
 5. **Schema Mapping**: Map CodeQL/SonarQube/PyLint/ESLint output to `analysis_log.schema.yaml` (fields: `id`, `language`, `tool`, `severity`, `rule_id`, `message`, `location`).
 6. **Output**: `data/processed/static_analysis_log.json` conforming to `analysis_log.schema.yaml`.
 7. **Dependency**: Ensure `contracts/analysis_log.schema.yaml` (T005) exists before validation.

- [ ] T020 [P] [US2] Implement `projects/PROJ-227-assessing-the-trade-offs-between-static-/code/dynamic_analysis.py` to execute unit tests via `pytest` (Python), `jest` (JS), and `junit` (Java). **Logic**: Filter out `static_only=True` samples from `data/manifest.csv` before processing. **Output Format**:
 - If no unit test exists, mark snippet as `untestable_dynamic` (set `is_untestable: true` in `data/processed/dynamic_analysis_log.json` and update `data/manifest.csv` column `is_untestable`).
 - Exclude `untestable_dynamic` snippets from functional correctness metrics.
 - **Output**: `data/processed/dynamic_analysis_log.json`.
- [ ] T021 [US2] Generate `data/processed/analysis_logs.json` with standardized schema (issues found, pass/fail status) by merging static and dynamic logs.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Results Aggregation & Statistical Reporting (Priority: P2)

**Goal**: Compute Issue Detection Rate, Pass Rate, and perform statistical correlation (Spearman/Chi-squared) with sensitivity analysis.

**Independent Test**: Process mock logs and verify report contains correlation coefficients and p-values.

**⚠️ PLAN RECONCILIATION NOTE**:
The Spec (FR-004, FR-005) originally demanded Precision/Recall/F1 and McNemar's test. The Plan explicitly rejects these as scientifically invalid. The tasks below implement the Plan's valid approach (Issue Detection Rate, Spearman/Chi-squared) directly, and T023.5 documents the rejection.

### Documentation for User Story 3 (REQUIRED)

- [ ] T023.5 [DOC] [US3] Document Methodology Deviation: Create `docs/methodology_rejection.md`. **Content**: Explicitly state that FR-004 (Precision/Recall/F1) and FR-005 (McNemar's test) are rejected due to lack of security ground truth. Document the rationale for using "Issue Detection Rate" and "Spearman's Rank Correlation" instead, citing the Plan. Explicitly state that SC-002 (McNemar's p-values) is **Not Applicable** and provide the justification. **Verification**: File exists and contains specific rationale text referencing FR-004, FR-005, and SC-002.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T022 [P] [US3] Unit test for Spearman correlation calculation in `projects/PROJ-227-assessing-the-trade-offs-between-static-/tests/unit/test_statistics.py`
- [ ] T023 [P] [US3] Integration test for stratified reporting in `projects/PROJ-227-assessing-the-trade-offs-between-static-/tests/integration/test_aggregation.py`

### Implementation for User Story 3

- [ ] T024a [P] [US3] Implement `projects/PROJ-227-assessing-the-trade-offs-between-static-/code/aggregation.py` to calculate **Issue Detection Rate** (static). **Output**: `data/processed/issue_detection_rate.json`.
- [ ] T024b [P] [US3] Implement `projects/PROJ-227-assessing-the-trade-offs-between-static-/code/aggregation.py` to calculate **Pass Rate** (dynamic). **Output**: `data/processed/pass_rate.json`.
- [ ] T025 [P] [US3] Implement `projects/PROJ-227-assessing-the-trade-offs-between-static-/code/aggregation.py` to compute **Spearman's Rank Correlation** between static issue density and dynamic pass/fail. **Output**: `data/processed/spearman_results.json` (separate file to avoid race conditions).
- [ ] T026 [P] [US3] Implement `projects/PROJ-227-assessing-the-trade-offs-between-static-/code/aggregation.py` to perform **Chi-squared Test (Wikidata Q70488676, https://www.wikidata.org/wiki/Q70488676) of Independence**. **Output**: `data/processed/chi_squared_results.json` (separate file to avoid race conditions).
- [ ] T027 [US3] Implement timeout handling for dynamic execution: **Enforce a configurable time limit per snippet**. Use `psutil` to send **SIGKILL** on timeout. **Output**: Log timeout events to `data/logs/timeouts.json`. **Verify**: Process is terminated after a predefined duration.; log entry contains `SIGKILL` and duration.
- [ ] T028 [US3] Implement stratification logic to run tests per language (if n ≥ 30). **Output**: `data/processed/stratified_test_results.json`.
- [ ] T029 [US3] Implement sensitivity analysis sweep: **Execute statistical tests for each alpha in the set {0.01, 0.05, 0.1}** as required by FR-007. **Logic**: If n < 30 for a stratum at a given alpha, skip test, log limitation, and report N/A for that stratum. **Output Format**: Write to `data/processed/detection_rate_variation.json` as a JSON array of objects with keys `alpha` (float), `detection_rate` (float), `p_value` (float), `sample_size` (int). **Verify**: Report includes rates for exactly these three values (or N/A with reason if data insufficient).
- [ ] T030 [US3] Implement Bonferroni correction for **multiple independent statistical tests** as per Plan. **Scope**: Apply correction to the **primary comparison** (Issue Detection Rate vs Pass Rate) AND **across languages** to control Type I error across all reported metrics. **Output**: `data/processed/corrected_results.json`. **Note**: Explicitly state in report: "Applied to primary comparison and cross-language tests per Plan to control Type I error across all reported metrics."
- [ ] T031 [US3] Generate `data/processed/statistical_report.json` with metrics, p-values, stratified results, and notes on methodology. **Logic**: Merge `spearman_results.json` (T025) and `chi_squared_results.json` (T026) into this report.
- [ ] T032 [US3] Execute `projects/PROJ-227-assessing-the-trade-offs-between-static-/code/hash_artifacts.py` to update `state/projects/PROJ-227-assessing-the-trade-offs-between-static-.yaml` with final hashes and tool versions. **Verify**: YAML updated with `artifact_hashes` and `tool_versions`.
- [ ] T033 [US3] Explicitly log and verify tool versions (CodeQL, SonarQube) in `state/projects/PROJ-227-assessing-the-trade-offs-between-static-.yaml` per Constitution Principle VI.

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

- **Setup (Phase 1)**: No dependencies - can start immediately.
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
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
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
Task: "Implement code/download.py to fetch HumanEval (Python), HumanEval-X (JS/Java), and BigCode"
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
- **Critical Constraint**: All tasks must run on free CPU-only CI with limited core counts and memory, without GPU acceleration. No low-bit quantization or heavy model training.
- **Data Integrity**: All datasets must be from real, verified sources (HuggingFace, GitHub). No synthetic data generation.
- **Statistical Validity**: No Precision/Recall/F for static analysis (no security ground truth). Use Issue Detection Rate. (Wikidata Q1071004, https://www.wikidata.org/wiki/Q1071004)
- **Plan Reconciliation**: Tasks implement the Plan's scientifically valid approach directly. Spec FR-004/FR-005/FR-008 are noted as contradictory in the Plan, and the Plan's methodology is followed.
- **Methodology Deviation**: FR-004, FR-005, SC-002 are explicitly rejected and documented in `docs/methodology_rejection.md` (T023.5).