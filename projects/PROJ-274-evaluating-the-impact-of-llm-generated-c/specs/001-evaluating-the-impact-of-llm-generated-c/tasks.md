# Tasks: Evaluating the Impact of LLM-Generated Code Documentation on Developer Onboarding

**Input**: Design documents from `/specs/001-evaluating-the-impact-of-llm-generated-c/`
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

**Purpose**: Project initialization, basic structure, and shared utilities.

- [ ] T001 Create project structure per implementation plan: `projects/PROJ-274-evaluating-the-impact-of-llm-generated-c/` including `code/`, `data/raw/`, `data/processed/`, `data/reports/`, `tests/unit/`, `tests/integration/`, `tests/contract/`, `specs/`. Verification: Run a Python script `scripts/verify_structure.py` that asserts `os.path.isdir` for `data/raw/`, `code/`, `tests/` and exits with code 0.
- [ ] T002 Create `requirements.txt` containing: `requests`, `pandas`, `scipy`, `statsmodels`, `scikit-learn`, `openai`, `transformers`, `llama-cpp-python`, `tiktoken`, `pyyaml`, `psutil`, `gitpython`, `ruff`, `black` with pinned versions (e.g., `pip freeze` or explicit versions). Verification: Run `pip check` to ensure no conflicts.
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools by creating `pyproject.toml` with configuration and running `ruff check.` and `black --check.` to ensure exit code 0.
- [ ] T010 [P] [Setup] Implement active monitoring context manager in `code/utils/monitor.py` using `psutil` and `time` to log peak memory and wall-clock time during execution. (Required for FR-010 and available for all phases). <!-- SKIPPED: YAML+regex parse failed (mapping values are not allowed here
 in "<unicode string>", line 2, column 13:
 contents: |
 ^) -->

---

## Phase 2: Repository Selection & Rubric Validation (Blocking Prerequisite)

**Purpose**: Select repositories and validate human documentation quality per FR-009. This phase MUST complete before US2.

**⚠️ CRITICAL**: No User Story 2 work can begin until this phase is complete.

- [ ] T047 [P] Consolidate validation logic for repository selection and schema validation into `code/validation.py` to ensure a single source of truth for all validation tasks. (Moved from Phase 8 to ensure logic is available for T021a/b). <!-- SKIPPED: YAML+regex parse failed (while scanning an alias
 in "<unicode string>", line 4, column 1:
 **Task**: Consolidate validation...
 ^
expected alphabetic or numeric character, but found '*'
 in "<unicode string>", line 4, column 2:
 **Task**: Consolidate validation...
 ^) -->
- [X] T021a [P] Implement repository selection rubric logic (criteria: setup instructions, API ref, architecture) in `code/validation.py` (DEPENDS on T047).
- [~] T021b [US2] Execute rubric on candidate repos, calculate Lines of Code (LOC) and Cyclomatic Complexity (CC) metrics for each repo, generate `data/raw/repo_selection_rubric.json` and `data/raw/repo_metrics.json`, implement exclusion logic for failing repos, generate a checksum of `data/raw/repo_selection_rubric.json` and record it in `data/checksums.txt`. Verification: Ensure JSONs exist, metrics are numeric, and checksum is in `data/checksums.txt`. (DEPENDS on T021a).
- [~] T021c [P] Implement metric collection for covariate adjustment in `code/validation.py` (DEPENDS on T021b). Output: `data/raw/repo_covariates.json`. This task replaces "quantitative matching" with metric collection for ANCOVA as per Plan updates.
- [~] T024 [P] Implement codebase fetching (≤500 files) and commit pinning logic in `code/repo_utils.py` (DEPENDS on T021c).

---

## Phase 3: User Story 1 - Controlled Onboarding Experiment Execution (Priority: P1) 🎯 MVP

**Goal**: Manage participant assignment, track metrics (time, questions), and handle study session logic.

**Independent Test**: Run a mock study with simulated participants across multiple conditions, verifying that task start/end times are logged, clarification questions are counted, and the study concludes without data loss.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests after Schema Definition (Phase 1) but before Implementation tasks. Ensure they FAIL before implementation.

- [~] T012 [P] [US1] Contract test for data logging schema in `tests/contract/test_logging_schema.py`
- [~] T013 [P] [US1] Integration test for full mock participant session in `tests/integration/test_mock_session.py`

### Implementation for User Story 1

- [~] T013a [US1] Enforce N≥15 Recruitment Gate: Halt study execution if recruited count < 15 in `code/data_collection.py`. Verification: Log exact error message "Recruitment count < 15" and exit with code 1. (Moved before T014).
- [~] T014 [P] [US1] Implement participant assignment logic (randomized to LLM/Human/None) in `code/data_collection.py`
- [~] T015 [US1] Implement session start/end logging with precise timestamps in `code/data_collection.py`
- [~] T016 [US1] Implement clarification question logging (timestamp + content) AND calculate the derived 'Cognitive Load Proxy' composite score. Logic: Redefine "Clarification Questions" as "Help Requests" (independent of struggle) by filtering for keywords ('how', 'why', 'what', 'explain') OR moderator tags. Composite Score = (Count of Help Requests) * (Average Time per Request). Output: Both raw logs and composite score written to JSON. Verification: Ensure both raw logs and the composite score are written to the output JSON.
- [~] T017 [US1] Implement subjective helpfulness survey capture in `code/data_collection.py`
- [~] T018 [US1] Implement "Stop-Loss" intervention logic: flag `intervention_flag=True`, `time_capped=True`, set `final_time=MAX_TIME` (minutes), or record as failed if docs are unusable in `code/data_collection.py`. (Corrected timeout to 45m per spec Edge Case).
- [~] T019 [US1] Implement handling for incomplete/abandoned records (exclude from time analysis, retain for dropout reporting) in `code/data_collection.py`
- [~] T020 [US1] Create raw data export function to `data/raw/participant_logs.json` with checksum generation in `code/data_collection.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Automated Documentation Generation Pipeline (Priority: P2)

**Goal**: Generate consistent, high-quality documentation artifacts from source code using LLMs with fallback logic.

**Independent Test**: Feed a known small Python utility codebase into the pipeline and verify that the output documentation covers architecture, API usage, and setup instructions without hallucinating non-existent functions.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T025 [P] [US2] Contract test for documentation output format in `tests/contract/test_doc_format.py`
- [~] T026 [P] [US2] Integration test for repo fetch and commit pinning in `tests/integration/test_repo_fetch.py`

### Implementation for User Story 2

- [ ] T027 [P] [US2] Implement primary LLM API integration (e.g., OpenAI) for documentation generation in `code/doc_generation.py`
- [ ] T028 [US2] Implement fallback logic to local CPU-optimized model. If API fails, load a quantized language model using `llama-cpp-python`. MUST pin the model to a specific HuggingFace commit hash (use `HF_COMMIT_HASH` env var or constant). Max a limited number of retries with exponential backoff (s base, max bounded interval). NO paid API fallbacks allowed. Log generation config (model, temp, prompt, commit hash) to `data/llm_config.yaml` and generate a checksum recorded in `data/checksums.txt` to satisfy Constitution Principle VII.
- [ ] T029 [US2] Implement prompt engineering to ensure coverage of architecture, API, and setup steps in `code/doc_generation.py`
- [ ] T030 [US2] Implement generation config logging (model, temp, prompt, commit hash) to `data/llm_config.yaml` (Note: Config is now logged in T028).
- [ ] T031 [US2] Save generated Markdown docs to `data/raw/llm_docs/` with checksums in `code/doc_generation.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: Data Processing & Contract Validation

**Purpose**: Clean, anonymize, and validate data before analysis. Produces `cleaned_dataset.csv` for Phase 6.

- [ ] T033 [P] Run schema validation on `data/raw/participant_logs.json` against `contracts/dataset.schema.yaml` in `code/validation.py`. Ensure validation passes before cleaning. **Gate**: Abort pipeline if validation fails. Output: `data/processed/validation_report.json`.
- [ ] T032a [P] [US1/3] Implement PII removal logic (remove names, emails, etc.) in `code/analysis.py` (DEPENDS on T033).
- [ ] T032b [US1/3] Implement incomplete record handling (flagging, exclusion logic) in `code/analysis.py` (DEPENDS on T033).
- [ ] T032 [US1/3] Aggregate cleaning steps (T032a, T032b) to produce `data/processed/cleaned_dataset.csv`. Read validation status from T033's output (`validation_report.json`) before proceeding. (Note: Essential for US3 readiness).

**Checkpoint**: Cleaned dataset ready for analysis.

---

## Phase 6: User Story 3 - Statistical Analysis and Reporting (Priority: P3)

**Goal**: Aggregate study data, perform statistical analysis (Spec-Mandated Decision Tree PRIMARY, LMM SECONDARY), and generate final reports.

**Independent Test**: Feed a synthetic dataset with known effect sizes into the analysis script and verify that the calculated p-values and confidence intervals match the expected theoretical values.

**NOTE**: Per FR-005 and Plan, the primary analysis MUST follow the 'Pre-specified' robust flow: **Pre-specified Welch's ANOVA** (no Levene's gate) with ANCOVA adjustment.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T034 [P] [US3] Contract test for analysis output schema in `tests/contract/test_analysis_schema.py`
- [ ] T035 [P] [US3] Integration test for synthetic data analysis pipeline in `tests/integration/test_synthetic_analysis.py`

### Implementation for User Story 3

- [ ] T036 [P] [US3] Implement **Pre-specified Welch's ANOVA** (no Levene's gate) to avoid test-then-select bias. Use this as the primary test regardless of variance homogeneity. Output: `data/reports/welch_results.json`. (Replaces T036/T037 decision tree).
- [ ] T037 [US3] Implement Games-Howell post-hoc tests for Welch's ANOVA to control for family-wise error rate (FR-006). Output: `data/reports/welch_posthoc.json`.
- [ ] T037c [US3] Implement ANCOVA (Analysis of Covariance) with Repository Complexity (LOC, CC) and Human Doc Quality Score as covariates, as mandated by Plan's "Key Methodological Updates". Output: `data/reports/ancova_results.json`.
- [ ] T039 [US3] Implement **Sensitivity Analysis** for alpha thresholds across a range of standard significance levels. instead of observed power. Explicitly report that N=15-20 is underpowered for medium effects. Output: `data/reports/sensitivity_analysis.json`.
- [ ] T041 [US3] Generate `data/reports/analysis_results.json` with all metrics and traceability to raw data in `code/analysis.py`.
- [ ] T042 [US3] Isolate and report specific pairwise comparison against "No Documentation" baseline as primary metric per SC-001 AND include "Human Documentation" condition as a secondary comparison per Plan assumptions in `code/analysis.py`.
- [ ] T043 [US3] Generate `data/reports/final_report.md` summarizing means, SDs, p-values, and explicitly noting power limitations (N=15-20) in `code/analysis.py`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Validation & Resource Checks

**Purpose**: Verify constraints and perform final checks.

- [ ] T044 [P] Verify **Analysis Phase** execution time < 6 hours and RAM < 7GB using the active monitoring context manager from T010. Verification: Assert `wall_clock_time < 21600` and `peak_RSS < 7GB` in the logged analysis report.
- [ ] T045a [P] Verify **Generation Phase** execution time < 15 minutes per repo (US-2 constraint) using `scripts/measure_generation_resources.py`. Verification: Assert `total_time_per_repo < 900s` and log `context_window_usage`. (Corrected from 6h/7GB analysis constraints).

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T046 [P] Documentation updates in `docs/` including `quickstart.md`
- [ ] T048a [P] Run `ruff check --select F401.` to identify unused imports in `code/` and remove them.
- [ ] T048b [P] Run `ruff check.` to identify other linting issues and fix them.
- [ ] T049 Optimize data loading in `code/analysis.py` to reduce memory footprint
- [ ] T050 Add unit tests for `Participant` class in `tests/unit/test_data_models.py`
- [ ] T051 Add unit tests for `doc_generation` functions in `tests/unit/test_doc_generation.py`
- [ ] T052 Run `quickstart.md` validation: Execute all code blocks in `quickstart.md` using `pytest --doctest-glob=quickstart.md` and assert zero failures.
- [ ] T053 Verify all artifacts have checksums in `data/checksums.txt`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Repository Selection (Phase 2)**: Depends on Setup - BLOCKS US2
- **User Story 1 (Phase 3)**: Depends on Setup - Can run in parallel with Phase 2
- **User Story 2 (Phase 4)**: Depends on Phase 2 (Repo Selection) and Setup
- **Data Processing (Phase 5)**: Depends on Phase 3 (Data Collection)
- **User Story 3 (Phase 6)**: Depends on Phase 5 (Clean Data)
- **Validation (Phase 7)**: Depends on Phases 4 & 6
- **Polish (Phase 8)**: Depends on all functional phases

### User Story Dependencies

- **User Story 1 (P1)**: Independent after Setup.
- **User Story 2 (P2)**: Depends on Phase 2 (Repo Selection).
- **User Story 3 (P3)**: Depends on Data Processing (Phase 5) which depends on US1.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- Phase 2 (Repo Selection) can run in parallel with Phase 3 (US1 Implementation)
- Tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (after their prerequisites are met)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for logging schema in tests/contract/test_logging_schema.py"
Task: "Integration test for full mock participant session in tests/integration/test_mock_session.py"

# Launch all models for User Story 1 together:
Task: "Implement participant assignment logic in code/data_collection.py"
Task: "Implement session start/end logging in code/data_collection.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 3: User Story 1 (skip Phase 2 if no docs needed for MVP, but Phase 2 is required for full study)
3. **STOP and VALIDATE**: Test User Story 1 independently
4. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup → Foundation ready
2. Add Phase 2 (Repo Selection) → Repos ready
3. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
4. Add User Story 2 → Test independently → Deploy/Demo
5. Add Phase 5 + User Story 3 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup together
2. Once Setup is done:
 - Developer A: Phase 2 (Repo Selection)
 - Developer B: User Story 1
3. Once Phase 2 is done:
 - Developer C: User Story 2
4. Once US1 is done:
 - Developer D: Data Processing & User Story 3
5. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CRITICAL**: Plan mandates "Pre-specified Welch's ANOVA" (no Levene's gate). T036 implements this directly.
- **CRITICAL**: T033 (Validation) MUST run before T032 (Cleaning). T032 explicitly consumes T033's output.
- **CRITICAL**: T044 checks Analysis Phase resources using active monitoring (T010). T045a checks Generation Phase resources (15 min/repo).
- **CRITICAL**: T021b must produce LOC/CC metrics for T021c covariate collection.
- **CRITICAL**: T013a (Recruitment Gate) MUST precede T014 (Assignment).
- **CRITICAL**: T028 must log config to `data/llm_config.yaml` and generate a checksum.