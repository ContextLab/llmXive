# Tasks: Evaluating the Impact of Code Style on LLM Code Generation Diversity

**Input**: Design documents from `/specs/001-eval-code-style-diversity/`
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

## Phase 0: Spec Alignment (CRITICAL PREREQUISITE - BLOCKING)

**Purpose**: Verify `spec.md` aligns with the `plan.md` and `tasks.md` consensus before implementation begins. **These tasks are BLOCKING; no Phase 1 tasks can start until these are complete.**

- [ ] T001a [P] [Spec] **BLOCKING**: **VERIFY** `spec.md` FR-003: Confirm the text reads "**exactly 20 code samples**". **Action**: If the text matches, log "FR-003: PASS" to `data/logs/spec_alignment.log`. If it does not match, log "FR-003: FAIL" and halt. **Deliverable**: Verification result in `data/logs/spec_alignment.log`. **Dependency**: None. **Verification**: Confirm `data/logs/spec_alignment.log` contains "FR-003: PASS".
- [ ] T001b [P] [Spec] **BLOCKING**: **VERIFY** `spec.md` FR-017: Confirm the text reads "**Spearman correlation coefficient**" and mentions injecting a suggestion. **Action**: If the text matches, log "FR-017: PASS" to `data/logs/spec_alignment.log`. If it does not match, log "FR-017: FAIL" and halt. **Deliverable**: Verification result in `data/logs/spec_alignment.log`. **Dependency**: None. **Verification**: Confirm `data/logs/spec_alignment.log` contains "FR-017: PASS".
- [ ] T001c [P] [Spec] **BLOCKING**: **VERIFY** `spec.md` Assumptions: Confirm the Power Analysis section exists and contains the verified claim text from `plan.md`. **Action**: If the section is missing or contains placeholders, **FAIL** this task. **Deliverable**: Verification result in `data/logs/spec_alignment.log`. **Dependency**: None. **Verification**: Confirm `data/logs/spec_alignment.log` contains "Assumptions: PASS".

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure. **Depends on Phase 0 completion.**

- [X] T002 Create project structure per implementation plan (`code/`, `tests/`, `data/`, `config/`, `specs/`)
- [X] T003 [P] Initialize Python 3.11 virtual environment and create `code/requirements.txt` with pinned versions (transformers, torch-cpu, datasets, networkx, scipy, pandas, pytest)
- [X] T004 [P] Configure linting (ruff/flake8) and formatting (black) tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. **Depends on Phase 0 & 1 completion.**

- [X] T005 [P] Create prompt templates in `code/prompts/neutral.txt`, `code/prompts/pep8.txt`, `code/prompts/minified.txt` matching style profiles in spec
- [X] T006 [P] Create `config/analysis.yaml` defining seeds (42), thresholds (α), batch size start (), and timeout limits (moderate duration)
- [X] T007 [P] Implement `code/config/loader.py` to load YAML config and validate required keys
- [X] T008 [P] Create `code/utils/logger.py` for structured logging (memory, timeouts, errors) and `memory_log.json` initialization
- [X] T009 [P] Implement `code/utils/timeout_decorator.py` to enforce -minute per-task limits and handle graceful skips
- [X] T010 [P] Implement `code/utils/metrics_utils.py` for AST parsing safety and zero-variance detection logic

**Checkpoint**: Foundation ready - spec is aligned with plan (via T001a-c), user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute Generation & Filtering Pipeline (Priority: P1) 🎯 MVP

**Goal**: Generate code samples for HumanEval tasks under style constraints and filter for functional correctness.

**Independent Test**: Run the pipeline for HumanEval tasks with the "Strict PEP8" profile; verify that the system outputs a CSV containing only samples that pass the associated unit tests, along with their raw source code.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T011 [P] [US1] Write failing unit test for prompt loading and validation in `tests/unit/test_prompts.py`
- [ ] T012 [P] [US1] Write failing integration test for generation loop with timeout and memory probing in `tests/integration/test_generation.py`. **Note**: The task is to *write* the test file (parallel with T011). The *execution* of this test occurs after T013-T016 implementation.

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement `code/generation/loader.py` to download `openai/human-eval` via `datasets` library and cache to `data/raw/humaneval/`. **Dependency**: T005, T006.
- [X] T014a [US1] Implement `code/generation/generator.py` generation loop: generate **20** samples per task per style (T=0.7, seed=42). **Dependency**: T013.
- [X] T014b [US1] Implement `code/generation/generator.py` timeout integration using `code/utils/timeout_decorator.py` to enforce a 5-minute timeout per task. **Log timeout errors** to `data/logs/pipeline.log` with format `ERROR [TIMEOUT] Task {task_id} timed out after 5m` and skip the task. **Dependency**: T009, T014a.
- [X] T015a [US1] Implement `code/generation/tester.py` to execute generated code against HumanEval unit tests and capture pass/fail status. **Dependency**: T014a.
- [X] T016a [US1] Implement `code/generation/pipeline.py` to atomically write the raw samples from the buffer to `data/processed/samples_all.csv`. **Implementation Detail**: Write to a temporary file (e.g., `samples_all.tmp.csv`), then rename to `samples_all.csv` to ensure atomicity. **This task creates the final `samples_all.csv` artifact.** **Dependency**: T015a.
- [X] T017a [US1] Implement `code/generation/pipeline.py` to create a **new file** `data/processed/samples_valid.csv` by filtering `data/processed/samples_all.csv`. **Implementation Detail**: Read `samples_all.csv`, filter rows where `pass_status` is True, write to `samples_valid.csv`. **Do NOT modify `samples_all.csv` in place.** **Dependency**: T016a.
- [X] T018b [US1] **Check Pass Rate**: Implement `code/generation/pipeline.py` to calculate pass rates. **Logic**: If pass rate for **any** style group is < 1%, **LOG** "Model Incapability: Pass rate < 1%" to `data/logs/pipeline.log` and **RETURN** status code 1 (HALT_STATUS). If pass rate >= 1%, **RETURN** status code 0 (OK). **Verification**: Verify that the process returns the correct exit code (1 for fail, 0 for ok) and the log contains the specific error string "Model Incapability: Pass rate < 1%". **This task MUST execute after T017a and before any US2 tasks.** **Dependency**: T017a.
- [X] T018c [US1] **Execute Fallback**: Implement `code/generation/pipeline.py` **Subset Processing Fallback**: If T018b returns HALT_STATUS, **reduce the task set size** (e.g., to 50 tasks), **re-run** the data loading (T013) and generation loop (T014a) for the subset, and re-execute T015a-T018b. **Dependency**: T018b (Status=HALT_STATUS). **Note**: This task is conditional on T018b failing.
- [X] T018 [US1] **Flag Bias**: Implement `code/generation/pipeline.py` to calculate pass rates; if the difference between any two style groups exceeds a substantial threshold (per FR-016), write the flag string "Potentially Biased" to the final report metadata and the output CSV. **Dependency**: T018b (Status=OK). **Note**: T018 runs only if T018b does not halt.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compute Structural Diversity Metrics (Priority: P2)

**Goal**: Quantify structural variance of valid code samples using AST edit distance and n-gram entropy.

**Independent Test**: Input a CSV of valid code samples for a single task; verify that the system calculates pairwise AST edit distances and token-level n-gram entropy, outputting a summary metric.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for AST edit distance calculation (identical samples = 0 distance) in `tests/unit/test_metrics.py`
- [X] T020 [P] [US2] Unit test for n-gram entropy calculation in `tests/unit/test_metrics.py`

### Implementation for User Story 2

- [X] T021a [P] [US2] Implement `code/analysis/metrics.py` n-gram entropy calculation function
- [X] T022a [US2] Implement `code/analysis/metrics.py` AST edit distance calculation using `networkx` graph alignment (Zhang-Shasha or similar)
- [X] T023a [US2] Implement `code/analysis/metrics.py` pairwise computation logic for all valid samples within a task/style group
- [X] T024a [US2] Implement `code/analysis/metrics.py` to compute metrics for **ALL generated samples** by reading `data/processed/samples_all.csv` (ignoring `pass_status` column) and saving to `data/processed/metrics_all.csv`. **Dependency**: T016a, T018b (Status=OK). **Note**: Parallel with T025a.
- [X] T025a [US2] Implement `code/analysis/metrics.py` to compute metrics for **VALID samples only** by reading `data/processed/samples_valid.csv` produced by T017a and saving to `data/processed/metrics_valid.csv`. **Dependency**: T017a, T018b (Status=OK). **Note**: Parallel with T024a.
- [X] T026a [US2] Implement `code/analysis/metrics.py` collinearity check: compute **Spearman** correlation coefficient between AST distance and n-gram entropy (per FR-017) using data from T025a. **Output**: Write a JSON file `code/analysis/collinearity_flag.json` with `{"flag": true/false, "suggestion": "Suggestion: Use AST Distance only"}`. **MUST WRITE FILE IN ALL CASES** (True or False) to ensure T035 can read it. **Dependency**: T025a.
- [X] T028a [US2] Implement zero-variance detection in `code/analysis/metrics.py`: log "Zero Variance" warning if a group has no variance. **Dependency**: T025a.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Perform Statistical Comparison & Sensitivity Analysis (Priority: P3)

**Goal**: Determine if differences in diversity scores between styles are statistically significant and robust.

**Independent Test**: Run the analysis on the full set of computed metrics; verify that the statistical module executes, reports p-values, and includes sensitivity plots.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US3] Unit test for Kruskal-Wallis H-test setup and execution in `tests/unit/test_stats.py`
- [X] T030 [P] [US3] Unit test for sensitivity analysis threshold sweep in `tests/unit/test_stats.py`

### Implementation for User Story 3

- [X] T031a [US3] Implement `code/analysis/stats.py` **Kruskal-Wallis H-test** using `scipy` to compare diversity distributions across three style groups (FR-006, US-3)
- [X] T032a [US3] Implement `code/analysis/stats.py` post-hoc analysis: perform **Dunn's test with Bonferroni correction** if Kruskal-Wallis is significant (US-3 Acceptance Scenario 1)
- [X] T033a [US3] Implement sensitivity analysis: sweep α over a specific set of small positive values and record the count of significant tasks for each. **Output**: Write results to `data/processed/sensitivity_results.json`. **MUST WRITE FILE IN ALL CASES** (even if analysis fails, write error status). **Dependency**: T031a.
- [X] T034a [US3] Implement survivorship bias comparison in `code/analysis/stats.py`: compare 'Valid' (from T025a) vs 'All Generated' (from T024a) results and quantify difference. **Dependency**: T024a, T025a.
- [X] T037a [US3] **Implement Power Analysis Calculation**: Implement a script in `code/analysis/power.py` that calculates the required sample size for Kruskal-Wallis (Power analysis uses alpha=0.05, power=0.8, effect_size=0.25) using `statsmodels.stats.power`. **Deliverable**: Log the calculation steps and the result "Power analysis confirmed: N={calculated_value} tasks is sufficient" to `data/logs/power_analysis.log`. **Dependency**: T007, T008.
- [X] T035 [US3] Implement `code/analysis/reporter.py` to generate PDF/HTML report with H-statistic, p-value, post-hoc results, **specific sensitivity plot (count vs threshold) saved as image (matplotlib/seaborn)**, survivorship bias section, **bias flag ("Potentially Biased")**, and **collinearity suggestion text**. **Input**: Read `code/analysis/collinearity_flag.json` from T026a. If `flag` is true, inject "Suggestion: Use AST Distance only" into the report. **Dependencies**: T026a, T031a, T032a, T033a, T034a. **Input files**: metrics_valid.csv, sensitivity_results.json, collinearity_flag.json.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T038 [P] Create `code/main.py` orchestrator to run full pipeline (Setup → Gen → Metrics → Stats → Report)
- [X] T039 [P] Implement `data/processed/` directory structure and ensure all CSVs (samples_all, samples_valid, metrics_all, metrics_valid) are written correctly
- [X] T040 [P] Add SHA256 checksumming for **HumanEval downloaded cached file in `data/raw/` and all processed CSVs (samples_all, samples_valid, metrics_all, metrics_valid)** and record in `state/projects/PROJ-466-evaluating-the-impact-of-code-style-on-l.yaml` under `artifact_hashes` (Data Hygiene). **Clarification**: Checksum the local cached file in `data/raw/`, not the remote source.
- [X] T041 [P] Update `state/` file with execution status, memory logs, and final report path
- [X] T042 [P] Documentation updates in `specs/001-evaluating-the-impact-of-code-style-on-l/quickstart.md`
- [X] T043a [P] Run `pytest` suite and generate JUnit XML report to `tests/results/junit.xml`. **Dependency**: T011, T019, T020, T029, T030.
- [ ] T043b [P] **Verify** `tests/results/junit.xml` exists and contains no failures; **Attach** file as completion evidence. **Dependency**: T043a.
- [X] T044a [P] Run pipeline subset and log execution duration to `data/logs/timing.log`. **Dependency**: T038.
- [X] T044b [P] **Verify** `data/logs/timing.log` exists and contains duration < 6 hours; **Attach** file as completion evidence. **Dependency**: T044a.
- [X] T045 [P] [Review Concern] **Implement** dynamic batch sizing logic in `code/generation/generator.py` that probes memory usage and reduces batch size iteratively until RAM limit is respected, logging each reduction step to `data/logs/memory_log.json`. **Dependency**: T014a.
- [X] T047 [P] [Review Concern] **Implement** AST parsing error handling in `code/analysis/metrics.py` (try/except around `ast.parse`) for individual samples, log the task_id and style to `data/logs/pipeline.log`, and skip only the failed sample without halting the batch. **Dependency**: T022a.
- [X] T048 [P] [Review Concern] **Implement** zero variance detection in `code/analysis/stats.py` before running Kruskal-Wallis, skip the test for that group, log "Zero Variance" warning, and do not raise a runtime error. **Dependency**: T031a.
- [X] T049 [P] [Review Concern] **Implement** strict error handling in `code/generation/loader.py` using `datasets.load_dataset("openai/human-eval")` that raises an exception if the download fails (no synthetic fallback), ensuring the run fails loudly if the real source is unreachable. **Dependency**: T013.
- [X] T050 [P] [Review Concern] **Implement** a dedicated section in `code/analysis/reporter.py` for the final PDF/HTML report showing the "Sensitivity Analysis" sweep of α thresholds and the corresponding count of significant tasks, as required by FR-007. **Dependency**: T033a.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately (after Phase 0)
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on US1 completion** (specifically T016a for T024a and T017a for T025a) and T018b (Status=OK)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Depends on US2 completion** (specifically T025a/T026a)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, **only US1 can start**. **US2 and US3 must wait for US1 to finish**.
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members **only if dependencies are met**.
- **Note**: T012 (Integration Test) is NOT parallel with T013-T015 for execution; it must run after implementation, but can be written (as a TDD task) before implementation.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Write failing unit test for prompt loading and validation in tests/unit/test_prompts.py"
Task: "Write failing integration test for generation loop with timeout and memory probing in tests/integration/test_generation.py"
# Note: T012 (Integration Test) must run AFTER T013-T015, not in parallel.

# Launch all models for User Story 1 together:
Task: "Implement code/generation/loader.py to download openai/human-eval..."
Task: "Implement code/generation/generator.py with dynamic batch sizing..."
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Spec Alignment (CRITICAL - BLOCKING)
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently (generate 10 tasks, filter, verify CSV)
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Spec Alignment + Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Metrics on valid samples)
4. Add User Story 3 → Test independently → Deploy/Demo (Stats & Report)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Spec Alignment + Setup + Foundational together
2. Once Foundational is done:
  - Developer A: User Story 1 (Generation & Filtering)
  - Developer B: Prepare US2 code (write tests, skeleton) but **WAIT for US1 completion**
  - Developer C: Prepare US3 code (write tests, skeleton) but **WAIT for US2 completion**
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
- **Critical Alignment**: This task list aligns with **plan.md (20 samples)** and **FR-017 (Spearman correlation)**. The spec.md FR-003 and FR-017 have been **verified** via T001a and T001b.
- **Data Hygiene**: T016a generates to buffer, T016a writes final `samples_all.csv`. T017a creates new `samples_valid.csv`. No in-place updates.
- **Gate Logic**: T018b is a check task (returns status). T018c is a conditional fallback. T018 runs only if T018b does not halt. T018c implements the fallback.
- **Review Concerns Addressed**: Tasks T045-T050 explicitly address edge cases (memory, timeout, AST errors, zero variance, data source failure, sensitivity reporting) to ensure robust execution on the free-tier runner.
- **Spec Alignment**: T001a-T001c tasks added to **verify** spec.md alignment. **These are BLOCKING**.
- **Data Flow**: T026a writes `collinearity_flag.json`; T035 reads it. T024a and T025a are parallel; T026a runs after T025a.