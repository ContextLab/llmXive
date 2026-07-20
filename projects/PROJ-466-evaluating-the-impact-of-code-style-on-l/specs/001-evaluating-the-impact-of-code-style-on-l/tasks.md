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

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure.

- [X] T001 Create project structure per implementation plan (`code/`, `tests/`, `data/`, `config/`, `specs/`)
- [X] T002 [P] Initialize Python 3.11 virtual environment and create `code/requirements.txt` with pinned versions (transformers, torch-cpu, datasets, networkx, scipy, pandas, pytest)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. **Depends on Phase 1 completion.**

- [X] T004 [P] Create prompt templates in `code/prompts/neutral.txt`, `code/prompts/pep8.txt`, `code/prompts/minified.txt` matching style profiles in spec
- [X] T005 [P] Create `config/analysis.yaml` defining seeds (42), thresholds (α), **batch size start = 1**, and timeout limits (5 minutes)
- [X] T006 [P] Implement `code/config/loader.py` to load YAML config and validate required keys
- [X] T007 [P] Create `code/utils/logger.py` for structured logging (memory, timeouts, errors) and `memory_log.json` initialization
- [X] T008 [P] Implement `code/utils/timeout_decorator.py` to enforce **5-minute** per-task limits and handle graceful skips
- [X] T009 [P] Implement `code/utils/metrics_utils.py` for AST parsing safety and zero-variance detection logic

**Checkpoint**: Foundation ready - spec is aligned with plan, user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute Generation & Filtering Pipeline (Priority: P1) 🎯 MVP

**Goal**: Generate code samples for HumanEval tasks under style constraints and filter for functional correctness.

**Independent Test**: Run the pipeline for HumanEval tasks with the "Strict PEP8" profile; verify that the system outputs a CSV containing only samples that pass the associated unit tests, along with their raw source code.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Write failing unit test for prompt loading and validation in `tests/unit/test_prompts.py`
- [ ] T012 [P] [US1] **Write** failing integration test for generation loop with timeout and memory probing in `tests/integration/test_generation.py`. **Note**: This task is strictly to **write the test file only** (parallel with T010). The *execution* of this test occurs after T013-T016 implementation.

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/generation/loader.py` to download `openai/human-eval` via `datasets` library and cache to `data/raw/humaneval/`. **Dependency**: T004, T005.
- [X] T014 [US1] Implement `code/generation/generator.py` generation loop: generate **20** samples per task per style (T=0.7, seed=42). **Dependency**: T013.
- [X] T015 [US1] Implement `code/generation/generator.py` timeout integration using `code/utils/timeout_decorator.py` to enforce a **5-minute** timeout per task. **Log timeout errors** to `data/logs/pipeline.log` with format `ERROR [TIMEOUT] Task {task_id} timed out after 5m` and skip the task. **Dependency**: T008, T014.
- [X] T015a [US1] Implement `code/generation/tester.py` to execute generated code against HumanEval unit tests and capture pass/fail status. **Dependency**: T014.
- [X] T016a [US1] Implement `code/generation/pipeline.py` to atomically write the raw samples from the buffer to `data/processed/samples_all.csv`. **Implementation Detail**: Write to a temporary file (e.g., `samples_all.tmp.csv`), then rename to `samples_all.csv` to ensure atomicity. **This task creates the final `samples_all.csv` artifact.** **Dependency**: T015a.
- [X] T017a [US1] Implement `code/generation/pipeline.py` to create a **new file** `data/processed/samples_valid.csv` by filtering `data/processed/samples_all.csv`. **Implementation Detail**: Read `samples_all.csv`, filter rows where `pass_status` is True, write to `samples_valid.csv`. **Do NOT modify `samples_all.csv` in place.** **Dependency**: T016a.
- [X] T024a [US1] **Compute Pre-Filter Metrics**: Implement `code/analysis/metrics.py` to compute metrics for **ALL generated samples** by reading `data/processed/samples_all.csv` (ignoring `pass_status` column) and saving to `data/processed/metrics_all.csv`. **Dependency**: T016a. **Note**: This runs BEFORE the pass rate check to ensure survivorship bias data is available.
- [X] T017b [US1] **Compute Valid Metrics**: Implement `code/analysis/metrics.py` to compute metrics for **VALID samples only** by reading `data/processed/samples_valid.csv` produced by T017a and saving to `data/processed/metrics_valid.csv`. **Dependency**: T017a. **Note**: This runs BEFORE the pass rate check to ensure survivorship bias data is available.
- [X] T018 [US1] **Check Pass Rate**: Implement `code/generation/pipeline.py` to calculate pass rates. **Logic**: Calculate `pass_rate` for each style group (count_passed / count_generated). If **any** style group has `pass_rate < 0.01`, **LOG** "Model Incapability: Pass rate < 1%" to `data/logs/pipeline.log`, **SET** a "Model Incapability" flag in the report metadata, and **CONTINUE** the pipeline (do NOT halt). **Verification**: Verify that the process continues to the next phase, the log contains the specific error string "Model Incapability: Pass rate < 1%", and the report metadata contains the "Model Incapability" flag. **This task MUST execute after T017a, T017b, and T024a**. **Dependency**: T017a, T017b, T024a. **Note**: This task flags the issue but allows the *survivorship bias* calculation (T032a) to proceed if data exists.
- [X] T019 [US1] **Flag Bias**: Implement `code/generation/pipeline.py` to calculate pass rates; if the difference between any two style groups exceeds a substantial threshold (**0.10** or 10 percentage points), write the flag string "Potentially Biased" to the final report metadata and the output CSV. **Dependency**: T018 (Status=OK or Flagged). **Note**: T019 runs after T018.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compute Structural Diversity Metrics (Priority: P2)

**Goal**: Quantify structural variance of valid code samples using AST edit distance and n-gram entropy.

**Independent Test**: Input a CSV of valid code samples for a single task; verify that the system calculates pairwise AST edit distances and token-level n-gram entropy, outputting a summary metric.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Unit test for AST edit distance calculation (identical samples = 0 distance) in `tests/unit/test_metrics.py`
- [X] T021 [P] [US2] Unit test for n-gram entropy calculation in `tests/unit/test_metrics.py`

### Implementation for User Story 2

- [X] T022a [P] [US2] Implement `code/analysis/metrics.py` n-gram entropy calculation function
- [X] T023a [US2] Implement `code/analysis/metrics.py` AST edit distance calculation using `networkx` graph alignment (Zhang-Shasha or similar)
- [X] T024 [US2] Implement `code/analysis/metrics.py` pairwise computation logic for all valid samples within a task/style group
- [X] T025a [US2] Implement `code/analysis/metrics.py` collinearity check: compute **Spearman** correlation coefficient between AST distance and n-gram entropy (per FR-017) using data from T017b. **Output**: Write a JSON file `code/analysis/collinearity_flag.json` with schema `{"flag": <bool>, "suggestion": "Suggestion: Use AST Distance only"}`. **MUST WRITE FILE IN ALL CASES** (True or False) to ensure T034 can read it. **Dependency**: T017b.
- [X] T026a [US2] Implement zero-variance detection in `code/analysis/metrics.py`: log "Zero Variance" warning if a group has no variance. **Dependency**: T017b.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Perform Statistical Comparison & Sensitivity Analysis (Priority: P3)

**Goal**: Determine if differences in diversity scores between styles are statistically significant and robust.

**Independent Test**: Run the analysis on the full set of computed metrics; verify that the statistical module executes, reports p-values, and includes sensitivity plots.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Unit test for Kruskal-Wallis H-test setup and execution in `tests/unit/test_stats.py`
- [X] T028 [P] [US3] Unit test for sensitivity analysis threshold sweep in `tests/unit/test_stats.py`

### Implementation for User Story 3

- [X] T029a [US3] Implement `code/analysis/stats.py` **Kruskal-Wallis H-test** using `scipy` to compare diversity distributions across three style groups (FR-006, US-3) on the full N=164 dataset.
- [X] T030a [US3] Implement `code/analysis/stats.py` post-hoc analysis: perform **Dunn's test with Bonferroni correction** if Kruskal-Wallis is significant (US-3 Acceptance Scenario 1)
- [X] T031a [US3] Implement sensitivity analysis: sweep α over the set **[0.01, 0.05, 0.1]** and record the count of significant tasks for each. **Output**: Write results to `data/processed/sensitivity_results.json`. **MUST WRITE FILE IN ALL CASES** (even if analysis fails, write error status). **Dependency**: T029a.
- [X] T032a [US3] Implement survivorship bias comparison in `code/analysis/stats.py`: compare 'Valid' (from T017b) vs 'All Generated' (from T024a) results and quantify difference. **Dependency**: T017b, T024a.
- [X] T033a [US3] **Implement Power Analysis Calculation**: Implement a script in `code/analysis/power.py` that calculates the required sample size for Kruskal-Wallis (Power analysis uses alpha=0.05, power=0.8, effect_size=0.25) using `statsmodels.stats.power`. **Deliverable**: Log the calculation steps and the result "Power analysis confirmed: N={calculated_value} tasks is sufficient" to `data/logs/power_analysis.log`. **Dependency**: T006, T007.
- [X] T034 [US3] Implement `code/analysis/reporter.py` to generate PDF/HTML report with H-statistic, p-value, post-hoc results, **specific sensitivity plot (count vs threshold) saved as image (matplotlib/seaborn)**, survivorship bias section, **bias flag ("Potentially Biased")**, **model incapability flag**, and **collinearity suggestion text**. **Input**: Read `code/analysis/collinearity_flag.json` from T025a. **Verification**: Verify `collinearity_flag.json` exists and contains keys `flag` and `suggestion`. If `flag` is true, inject "Suggestion: Use AST Distance only" into the report. **Dependencies**: T025a, T029a, T030a, T031a, T032a. **Input files**: metrics_valid.csv, sensitivity_results.json, collinearity_flag.json.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T035 [P] Create `code/main.py` orchestrator to run full pipeline (Setup → Gen → Metrics → Stats → Report)
- [X] T036 [P] Implement `data/processed/` directory structure and ensure all CSVs (samples_all, samples_valid, metrics_all, metrics_valid) are written correctly
- [X] T037 [P] Add SHA256 checksumming for **HumanEval downloaded cached file in `data/raw/`, all processed CSVs (samples_all, samples_valid, metrics_all, metrics_valid), and raw generated code samples (stored in `data/processed/raw_samples/` or equivalent intermediate storage)** and record in `state/projects/PROJ-466-evaluating-the-impact-of-code-style-on-l.yaml` under `artifact_hashes` (Data Hygiene). **Clarification**: Checksum the local cached file in `data/raw/`, not the remote source.
- [X] T038 [P] Update `state/` file with execution status, memory logs, and final report path
- [X] T039 [P] Documentation updates in `specs/001-evaluating-the-impact-of-code-style-on-l/quickstart.md`
- [X] T040a [P] Run `pytest` suite and generate JUnit XML report to `tests/results/junit.xml`. **Dependency**: T010, T020, T021, T027, T028.
- [ ] T040b [P] **Verify** `tests/results/junit.xml` exists and contains no failures; **Attach** file as completion evidence. **Dependency**: T040a.
- [X] T041a [P] Run pipeline subset and log execution duration to `data/logs/timing.log`. **Dependency**: T035.
- [X] T041b [P] **Verify** `data/logs/timing.log` exists and contains duration < 6 hours; **Attach** file as completion evidence. **Dependency**: T041a.
- [X] T042 [P] [Review Concern] **Implement** dynamic batch sizing logic in `code/generation/generator.py` that probes memory usage and reduces batch size iteratively until RAM limit is respected, logging each reduction step to `data/logs/memory_log.json`. **Dependency**: T014.
- [X] T043 [P] [Review Concern] **Implement** AST parsing error handling in `code/analysis/metrics.py` (try/except around `ast.parse`) for individual samples, log the task_id and style to `data/logs/pipeline.log`, and skip only the failed sample without halting the batch. **Dependency**: T023a.
- [X] T044 [P] [Review Concern] **Implement** zero variance detection in `code/analysis/stats.py` before running Kruskal-Wallis, skip the test for that group, log "Zero Variance" warning, and do not raise a runtime error. **Dependency**: T029a.
- [X] T045 [P] [Review Concern] **Implement** strict error handling in `code/generation/loader.py` using `datasets.load_dataset("openai/human-eval")` that raises an exception if the download fails (no synthetic fallback), ensuring the run fails loudly if the real source is unreachable. **Dependency**: T013.
- [X] T046 [P] [Review Concern] **Implement** a dedicated section in `code/analysis/reporter.py` for the final PDF/HTML report showing the "Sensitivity Analysis" sweep of α thresholds and the corresponding count of significant tasks, as required by FR-007. **Dependency**: T031a.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on US1 completion** (specifically T016a for T017b and T017a for T017c)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Depends on US2 completion** (specifically T017b/T025a)

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
- **Note**: T012 (Integration Test) is NOT parallel with T013-T016 for execution; it must run after implementation, but can be written (as a TDD task) before implementation.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Write failing unit test for prompt loading and validation in tests/unit/test_prompts.py"
Task: "Write failing integration test for generation loop with timeout and memory probing in tests/integration/test_generation.py"
# Note: T012 (Integration Test) must run AFTER T013-T016, not in parallel.

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
4. **STOP and VALIDATE**: Test User Story 1 independently (generate tasks, filter, verify CSV)
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
- **Critical Alignment**: This task list aligns with **plan.md (20 samples)** and **FR-017 (Spearman correlation)**. The spec.md FR-003 and FR-017 have been **verified** in the planning phase.
- **Data Hygiene**: T016a generates to buffer, T016a writes final `samples_all.csv`. T017a creates new `samples_valid.csv`. No in-place updates.
- **Gate Logic**: T018 is a check task (returns status). **No fallback** (T018c removed). T018 runs after T017b/T024a to ensure data exists for survivorship bias.
- **Review Concerns Addressed**: Tasks T042-T046 explicitly address edge cases (memory, timeout, AST errors, zero variance, data source failure, sensitivity reporting) to ensure robust execution on the free-tier runner.
- **Spec Alignment**: Phase 0 (T001a-c) removed. Spec is immutable.
- **Data Flow**: T025a writes `collinearity_flag.json`; T034 reads it. T017b and T024a are parallel; T018 runs after T017b/T024a.
- **Statistical Power**: N=164 is mandatory. No subset fallback is permitted.