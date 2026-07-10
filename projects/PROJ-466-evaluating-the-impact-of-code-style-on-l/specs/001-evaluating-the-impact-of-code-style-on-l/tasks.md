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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`code/`, `tests/`, `data/`, `config/`, `specs/`)
- [ ] T002 [P] Initialize Python 3.11 virtual environment and create `code/requirements.txt` with pinned versions (transformers, torch-cpu, datasets, networkx, scipy, pandas, pytest)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create prompt templates in `code/prompts/neutral.txt`, `code/prompts/pep8.txt`, `code/prompts/minified.txt` matching style profiles in spec
- [ ] T005 [P] Create `config/analysis.yaml` defining seeds (42), thresholds (α), batch size start (50), and timeout limits (5m)
- [ ] T006 [P] Implement `code/config/loader.py` to load YAML config and validate required keys
- [ ] T007 [P] Implement `code/utils/logger.py` for structured logging (memory, timeouts, errors) and `memory_log.json` initialization
- [ ] T008 [P] Create `code/utils/timeout_decorator.py` to enforce -minute per-task limits and handle graceful skips
- [ ] T009 [P] Implement `code/utils/metrics_utils.py` for AST parsing safety and zero-variance detection logic

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute Generation & Filtering Pipeline (Priority: P1) 🎯 MVP

**Goal**: Generate code samples for HumanEval tasks under style constraints and filter for functional correctness.

**Independent Test**: Run the pipeline for HumanEval tasks with the "Strict PEP8" profile; verify that the system outputs a CSV containing only samples that pass the associated unit tests, along with their raw source code.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for prompt loading and validation in `tests/unit/test_prompts.py`
- [ ] T011 [US1] Integration test for generation loop with timeout and memory probing in `tests/integration/test_generation.py` (Note: Sequential dependency - must run after T012-T014 implementation)

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `code/generation/loader.py` to download `openai/human-eval` via `datasets` library and cache to `data/raw/humaneval/`
- [ ] T013 [US1] Implement `code/generation/generator.py` with dynamic batch sizing: probe memory, reduce batch size if >7GB, log every reduction step to `memory_log.json`
- [ ] T014 [US1] Implement `code/generation/generator.py` generation loop: generate 5 samples/task/style (T=0.7, seed=42), enforce 5m timeout per task, and **immediately write raw samples to `data/processed/samples_all.csv`** (task_id, style, sample_id, code, pass_status=null) **before any testing or filtering occurs**
- [ ] T015 [US1] Implement `code/generation/tester.py` to execute generated code against HumanEval unit tests and capture pass/fail status
- [ ] T016 [US1] Implement `code/generation/tester.py` error handling: catch AST parsing errors, log Task ID/Style, skip sample without crashing
- [ ] T017a [US1] Implement `code/generation/pipeline.py` to **update `data/processed/samples_all.csv`** with `pass_status` (True/False) based on T015 results
- [ ] T017b [US1] Implement `code/generation/pipeline.py` to create `data/processed/samples_valid.csv` by filtering `samples_all.csv` where `pass_status` is True
- [ ] T018 [US1] Implement `code/generation/pipeline.py` to calculate pass rates; flag "Potentially Biased" if difference >10pp
- [ ] T018b [US1] Implement `code/generation/pipeline.py` to **HALT execution and log "Model Incapability"** if pass rate for any style group is < 1% (FR-008)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compute Structural Diversity Metrics (Priority: P2)

**Goal**: Quantify structural variance of valid code samples using AST edit distance and n-gram entropy.

**Independent Test**: Input a CSV of valid code samples for a single task; verify that the system calculates pairwise AST edit distances and token-level n-gram entropy, outputting a summary metric.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for AST edit distance calculation (identical samples = 0 distance) in `tests/unit/test_metrics.py`
- [ ] T020 [P] [US2] Unit test for n-gram entropy calculation in `tests/unit/test_metrics.py`

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement `code/analysis/metrics.py` n-gram entropy calculation function
- [ ] T022 [US2] Implement `code/analysis/metrics.py` AST edit distance calculation using `networkx` graph alignment (Zhang-Shasha or similar)
- [ ] T023 [US2] Implement `code/analysis/metrics.py` pairwise computation logic for all valid samples within a task/style group
- [ ] T024 [US2] Implement `code/analysis/metrics.py` collinearity check: compute Pearson correlation between AST distance and n-gram entropy
- [ ] T024b [US2] Implement logic to inject "Suggestion: Use AST Distance only" into the report generation if collinearity (r > 0.9) is detected
- [ ] T025 [US2] Implement `code/analysis/metrics.py` to compute metrics for **ALL generated samples** (reading from `data/processed/samples_all.csv` produced by T014/T017a) and save to `data/processed/metrics_all.csv`
- [ ] T026 [US2] Implement `code/analysis/metrics.py` to compute metrics for **VALID samples only** (reading from `data/processed/samples_valid.csv` produced by T017b) and save to `data/processed/metrics_valid.csv`
- [ ] T027 [US2] Implement zero-variance detection in `code/analysis/metrics.py`: log "Zero Variance" warning if a group has no variance

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Perform Statistical Comparison & Sensitivity Analysis (Priority: P3)

**Goal**: Determine if differences in diversity scores between styles are statistically significant and robust.

**Independent Test**: Run the analysis on the full set of computed metrics; verify that the statistical module executes, reports p-values, and includes sensitivity plots.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Unit test for Kruskal-Wallis H-test setup and execution in `tests/unit/test_stats.py`
- [ ] T029 [P] [US3] Unit test for sensitivity analysis threshold sweep in `tests/unit/test_stats.py`

### Implementation for User Story 3

- [ ] T030 [P] [US3] Implement `code/analysis/stats.py` data normalization (Z-score relative to Neutral baseline) to control for task difficulty
- [ ] T031 [US3] Implement `code/analysis/stats.py` **Kruskal-Wallis H-test** using `scipy` to compare diversity distributions across three style groups (FR-006, US-3)
- [ ] T032 [US3] Implement `code/analysis/stats.py` post-hoc analysis: perform **Dunn's test with Bonferroni correction** if Kruskal-Wallis is significant (US-3 Acceptance Scenario 1)
- [ ] T033 [US3] Implement `code/analysis/stats.py` sensitivity analysis: sweep α over a range of small values and report range of significant tasks
- [ ] T034 [US3] Implement survivorship bias comparison in `code/analysis/stats.py`: compare 'Valid' (from T026) vs 'All Generated' (from T025) results and quantify difference
- [ ] T035 [US3] Implement `code/analysis/reporter.py` to generate PDF/HTML report with H-statistic, p-value, post-hoc results, **specific sensitivity plot (count vs threshold)**, survivorship bias section, and **collinearity suggestion text**
- [ ] T036 [US3] Implement power limitation warning in `code/analysis/reporter.py`: flag if effect sizes are small or N=5 samples

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Create `code/main.py` orchestrator to run full pipeline (Setup → Gen → Metrics → Stats → Report)
- [ ] T038 [P] Implement `data/processed/` directory structure and ensure all CSVs (samples_all, samples_valid, metrics_all, metrics_valid) are written correctly
- [ ] T039 [P] Add SHA256 checksumming for raw dataset and record in `state/checksums.json` (Data Hygiene)
- [ ] T040 [P] Update `state/` file with execution status, memory logs, and final report path
- [ ] T041 [P] Documentation updates in `specs/001-eval-code-style-diversity/quickstart.md`
- [ ] T042 [P] Run `pytest` suite to verify all unit and integration tests pass
- [ ] T043 [P] Performance optimization: verify total runtime < 6 hours on CI (simulate with subset if needed)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data (samples_all.csv from T014)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 data (metrics.csv)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- **Note**: T011 (Integration Test) is NOT parallel with T012-T014; it must run after implementation.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for prompt loading and validation in tests/unit/test_prompts.py"
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
   - Developer B: User Story 2 (Metrics Calculation)
   - Developer C: User Story 3 (Stats & Reporting)
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