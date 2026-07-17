# Tasks: Evaluating the Impact of Code Style on LLM Code Generation Diversity

**Input**: Design documents from `/specs/001-eval-code-style-diversity/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]****: Which user story this task belongs to (e.g., US1, US2, US3)
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

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan (`code/`, `tests/`, `data/`, `config/`, `specs/`)
- [X] T002 [P] Initialize Python 3.11 virtual environment and create `code/requirements.txt` with pinned versions (transformers, torch-cpu, datasets, networkx, scipy, pandas, pytest)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes Spec Amendments to resolve plan/spec conflicts.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create prompt templates in `code/prompts/neutral.txt`, `code/prompts/pep8.txt`, `code/prompts/minified.txt` matching style profiles in spec
- [X] T005 [P] Create `config/analysis.yaml` defining seeds (42), thresholds (α), batch size start (50), and timeout limits (5m)
- [X] T006 [P] Implement `code/config/loader.py` to load YAML config and validate required keys
- [X] T007 [P] Implement `code/utils/logger.py` for structured logging (memory, timeouts, errors) and `memory_log.json` initialization
- [X] T008 [P] Create `code/utils/timeout_decorator.py` to enforce 5-minute per-task limits and handle graceful skips
- [X] T009 [P] Implement `code/utils/metrics_utils.py` for AST parsing safety and zero-variance detection logic
- [X] T003a [P] [Spec Amendment] Edit `spec.md` FR-003 text to reflect generating **20** samples per task (aligning with plan.md) to resolve sample size contradiction.
- [X] T003a-verify [P] [Spec Amendment] Verify `spec.md` FR-003 text has been updated to **20** samples and US-1 Acceptance Scenario 1 reflects **20** samples.
- [X] T003b [P] [Spec Amendment] Edit `spec.md` FR-017 text to reflect computing **Spearman** correlation coefficient (aligning with plan.md) to resolve statistical method contradiction.
- [X] T003b-verify [P] [Spec Amendment] Verify `spec.md` FR-017 text has been updated to **Spearman** correlation.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute Generation & Filtering Pipeline (Priority: P1) 🎯 MVP

**Goal**: Generate code samples for HumanEval tasks under style constraints and filter for functional correctness.

**Independent Test**: Run the pipeline for HumanEval tasks with the "Strict PEP8" profile; verify that the system outputs a CSV containing only samples that pass the associated unit tests, along with their raw source code.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Write failing unit test for prompt loading and validation in `tests/unit/test_prompts.py`
- [X] T011 [US1] Write failing integration test for generation loop with timeout and memory probing in `tests/integration/test_generation.py`. **Note**: The task is to *write* the test file. The *execution* of this test occurs after T012-T015 implementation.

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/generation/loader.py` to download `openai/human-eval` via `datasets` library and cache to `data/raw/humaneval/`
- [X] T013 [US1] Implement `code/generation/generator.py` generation loop: generate multiple samples per task per style (T=0.7, seed=42), enforce 5m timeout per task. **Log timeout errors** to `data/logs/pipeline.log` with format `ERROR [TIMEOUT] Task {task_id} timed out after 5m` and skip the task. Write raw samples to a **temporary buffer** (in-memory or temp file) but **DO NOT write to final CSV yet**. **Dependency: T012.**
- [X] T015 [US1] Implement `code/generation/tester.py` to execute generated code against HumanEval unit tests and capture pass/fail status. **Dependency: T013.**
- [X] T016 [US1] Implement `code/generation/pipeline.py` to atomically write the raw samples from the buffer to `data/processed/samples_all.csv` (task_id, style, sample_id, code, pass_status). **This task creates the final `samples_all.csv` artifact.** **Dependency: T015.**
- [X] T017a [US1] Implement `code/generation/pipeline.py` to create a **new file** `data/processed/samples_valid.csv` by filtering `data/processed/samples_all.csv` where `pass_status` is True. **Do NOT modify `samples_all.csv` in place.** **Dependency: T016.**
- [X] T018 [US1] Implement `code/generation/pipeline.py` to calculate pass rates; if the difference between any two style groups exceeds a substantial threshold (per FR-016), write the flag string "Potentially Biased" to the final report metadata and the output CSV. **Dependency: T017a.**
- [X] T018b [US1] Implement `code/generation/pipeline.py` to calculate pass rates; if pass rate for **any** style group is < 1%, **HALT execution immediately**, log "Model Incapability" warning, and **prevent entry into Phase 4 (Metrics)**. **This task MUST execute after T017a and before any US2 tasks.** **Dependency: T018.**

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compute Structural Diversity Metrics (Priority: P2)

**Goal**: Quantify structural variance of valid code samples using AST edit distance and n-gram entropy.

**Independent Test**: Input a CSV of valid code samples for a single task; verify that the system calculates pairwise AST edit distances and token-level n-gram entropy, outputting a summary metric.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for AST edit distance calculation (identical samples = 0 distance) in `tests/unit/test_metrics.py`
- [X] T020 [P] [US2] Unit test for n-gram entropy calculation in `tests/unit/test_metrics.py`

### Implementation for User Story 2

- [X] T021 [P] [US2] Implement `code/analysis/metrics.py` n-gram entropy calculation function
- [X] T022 [US2] Implement `code/analysis/metrics.py` AST edit distance calculation using `networkx` graph alignment (Zhang-Shasha or similar)
- [X] T023 [US2] Implement `code/analysis/metrics.py` pairwise computation logic for all valid samples within a task/style group
- [X] T024 [US2] Implement `code/analysis/metrics.py` to compute metrics for **ALL generated samples** by reading `data/processed/samples_all.csv` (ignoring `pass_status` column) and saving to `data/processed/metrics_all.csv`. **Dependency: T016.**
- [X] T025 [US2] Implement `code/analysis/metrics.py` to compute metrics for **VALID samples only** by reading `data/processed/samples_valid.csv` produced by T017a and saving to `data/processed/metrics_valid.csv`. **Dependency: T017a.**
- [X] T026 [US2] Implement `code/analysis/metrics.py` collinearity check: compute **Spearman** correlation coefficient between AST distance and n-gram entropy (per FR-017) using data from T025. If r > 0.9, flag "Redundant Metrics" and recommend AST distance as primary. **Dependency: T003b, T025.**
- [X] T028 [US2] Implement zero-variance detection in `code/analysis/metrics.py`: log "Zero Variance" warning if a group has no variance

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Perform Statistical Comparison & Sensitivity Analysis (Priority: P3)

**Goal**: Determine if differences in diversity scores between styles are statistically significant and robust.

**Independent Test**: Run the analysis on the full set of computed metrics; verify that the statistical module executes, reports p-values, and includes sensitivity plots.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US3] Unit test for Kruskal-Wallis H-test setup and execution in `tests/unit/test_stats.py`
- [X] T030 [P] [US3] Unit test for sensitivity analysis threshold sweep in `tests/unit/test_stats.py`

### Implementation for User Story 3

- [X] T031 [US3] Implement `code/analysis/stats.py` **Kruskal-Wallis H-test** using `scipy` to compare diversity distributions across three style groups (FR-006, US-3)
- [X] T032 [US3] Implement `code/analysis/stats.py` post-hoc analysis: perform **Dunn's test with Bonferroni correction** if Kruskal-Wallis is significant (US-3 Acceptance Scenario 1)
- [X] T033 [US3] Implement sensitivity analysis: sweep α over a specific set of small positive values and record the count of significant tasks for each. Write results to `data/processed/sensitivity_results.json`. **Dependency: T031.**
- [X] T034 [US3] Implement survivorship bias comparison in `code/analysis/stats.py`: compare 'Valid' (from T025) vs 'All Generated' (from T024) results and quantify difference. **Dependency: T024, T025.**
- [X] T035 [US3] Implement `code/analysis/reporter.py` to generate PDF/HTML report with H-statistic, p-value, post-hoc results, **specific sensitivity plot (count vs threshold)**, survivorship bias section, **bias flag ("Potentially Biased")**, and **collinearity suggestion text** (inject "Suggestion: Use AST Distance only" if Spearman r > 0.9). **Dependencies: T026, T031, T032, T033, T034, input files: metrics_valid.csv, sensitivity_results.json.**
- [X] T037 [US3] Implement power confirmation log in `code/analysis/reporter.py`: Log the confirmed power analysis result (N=164 is sufficient) to `data/logs/power_analysis.log` with message "Power analysis confirmed: N=164 tasks is sufficient for robust conclusion."

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T038 [P] Create `code/main.py` orchestrator to run full pipeline (Setup → Gen → Metrics → Stats → Report)
- [X] T039 [P] Implement `data/processed/` directory structure and ensure all CSVs (samples_all, samples_valid, metrics_all, metrics_valid) are written correctly
- [X] T040 [P] Add SHA256 checksumming for **HumanEval raw dataset and all processed CSVs (samples_all, samples_valid, metrics_all, metrics_valid)** and record in `state/projects/PROJ-466-evaluating-the-impact-of-code-style-on-l.yaml` under `artifact_hashes` (Data Hygiene)
- [X] T041 [P] Update `state/` file with execution status, memory logs, and final report path
- [X] T042 [P] Documentation updates in `specs/001-evaluating-the-impact-of-code-style-on-l/quickstart.md`
- [~] T043 [P] Run `pytest` suite to verify all unit and integration tests pass
- [~] T044 [P] Performance optimization: verify total runtime < 6 hours on CI (simulate with subset if needed)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on US1 completion** (specifically T016 for T024 and T017a for T025)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Depends on US2 completion** (specifically T025/T026)

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
- **Note**: T011 (Integration Test) is NOT parallel with T012-T014 for execution; it must run after implementation, but can be written (as a TDD task) before implementation.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Write failing unit test for prompt loading and validation in tests/unit/test_prompts.py"
Task: "Write failing integration test for generation loop with timeout and memory probing in tests/integration/test_generation.py"
# Note: T011 (Integration Test) must run AFTER T012-T014, not in parallel.

# Launch all models for User Story 1 together:
Task: "Implement code/generation/loader.py to download openai/human-eval..."
Task: "Implement code/generation/generator.py with dynamic batch sizing..."
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (generate 10 tasks, filter, verify CSV)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Metrics on valid samples)
4. Add User Story 3 → Test independently → Deploy/Demo (Stats & Report)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
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
- **Critical Alignment**: This task list aligns with **plan.md (20 samples)** and **FR-017 (Spearman correlation)**. The spec.md FR-003 and FR-017 have been updated via T003a/T003b to match.
- **Data Hygiene**: T014 generates to buffer, T016 writes final `samples_all.csv`. T017a creates new `samples_valid.csv`. No in-place updates.
- **Gate Logic**: T018b is a hard gate after filtering and before metrics.