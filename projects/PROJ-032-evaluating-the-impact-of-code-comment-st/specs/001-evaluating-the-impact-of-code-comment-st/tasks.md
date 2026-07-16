---
description: "Task list for Evaluating the Impact of Code Comment Style on Maintainability"
---

# Tasks: Evaluating the Impact of Code Comment Style on Maintainability

**Input**: Design documents from `/specs/101-eval-comment-maintainability/`
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

- [X] T001 Create project structure: Execute `mkdir -p src/code src/data/raw src/data/processed src/data/schemas tests/unit tests/integration docs` to establish the directory tree.
- [X] T002 Initialize Python 3.9+ project:
 1. Run `python -m venv venv`.
 2. Create `requirements.txt` containing runtime dependencies: `datasets`, `tree-sitter`, `tree-sitter-python`, `textstat`, `textblob`, `pylint`, `gitpython`, `scikit-learn`, `pandas`, `numpy`, `statsmodels`, `radon`, `psutil` (pinned versions).
 3. Create `dev-requirements.txt` containing development tools: `pip-audit`, `bandit`, `pytest`, `pytest-cov`.
 4. Install runtime deps: `pip install -r requirements.txt`.
 5. Install dev deps: `pip install -r dev-requirements.txt`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Schemas and utilities defined here are consumed by Phase 3+.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T009 Create base data models and CSV schemas: Create `data/schemas/metrics_schema.json` and `data/schemas/analysis_results_schema.json` with the following exact JSON Schema definitions:
 1. `metrics_schema.json`:
 ```json
 {
 "$schema": "http://json-schema.org/draft-07/schema#",
 "title": "Repository Metrics",
 "type": "object",
 "properties": {
 "repo_id": {"type": "string"},
 "readability": {"type": "number", "minimum": 0},
 "sentiment": {"type": "number", "minimum": -1, "maximum": 1},
 "density": {"type": "number", "minimum": 0},
 "churn": {"type": "number", "minimum": 0},
 "bug_fix_rate": {"type": "number", "minimum": 0, "maximum": 1},
 "complexity": {"type": "number", "minimum": 0},
 "age": {"type": "integer"},
 "contributors": {"type": "integer"}
 },
 "required": ["repo_id", "readability", "sentiment", "density", "churn", "bug_fix_rate", "complexity", "age", "contributors"]
 }
 ```
 2. `analysis_results_schema.json`:
 ```json
 {
 "$schema": "http://json-schema.org/draft-07/schema#",
 "title": "Analysis Results",
 "type": "object",
 "properties": {
 "model_type": {"type": "string"},
 "r_squared": {"type": "number"},
 "p_values": {"type": "array", "items": {"type": "number"}},
 "is_significant": {"type": "boolean"},
 "sensitivity_data": {"type": "array", "items": {"type": "object"}}
 },
 "required": ["model_type", "r_squared", "p_values", "is_significant", "sensitivity_data"]
 }
 ```
- [X] T004a [P] Implement `src/code/utils.py`: Logging - Create function `configure_logging(log_path="logs/pipeline.log")` to set up file and console handlers with INFO/ERROR levels.
- [X] T004b [P] Implement `src/code/utils.py`: Batching - Create class `BatchIterator` with semaphore logic to enforce max concurrent clones; implement `__iter__` and `__next__`.
- [X] T004c [P] Implement `src/code/utils.py`: Memory monitoring - Create class `MemoryMonitor` using `psutil` with method `check_limit(limit_gb=7)` that raises `MemoryError` if exceeded.
- [X] T004d [P] Implement `src/code/utils.py`: Commit sampling - Create class `CommitSampler` with method `sample_commits(commits, n=10)` to select representative commits for static analysis.
- [ ] T006 [P] Implement `src/code/extract.py`: `extract_comments_ast()` using `tree-sitter` to isolate comments from string literals; handle empty files and syntax errors gracefully.
- [X] T006b [P] Implement `src/code/metrics.py`: `calc_complexity()` using `radon` or `ast` module to compute average cyclomatic complexity per function for a repository.
- [X] T007a [P] Implement `src/code/metrics.py`: `calc_readability()` using `textstat.flesch_kincaid_grade` on extracted comments; handle empty comment sets by returning 0.0 and log event.
- [X] T007b [P] Implement `src/code/metrics.py`: `calc_sentiment()` using `TextBlob` polarity on extracted comments; handle empty comment sets by returning 0.0 and log event.
- [X] T007c [P] Implement `src/code/metrics.py`: `calc_churn()` using `git log --numstat` to calculate total lines changed per commit; aggregate to repository level.
- [ ] T007d [P] Implement `src/code/metrics.py`: `calc_quality_rate()` using `pylint` on sampled commits; calculate ratio of commits with error-level warnings; validate against `data/manual_labels.csv` (global stratified sample N=50) and calculate 95% CI for accuracy.
- [ ] T007e [P] Implement `src/code/metrics.py`: `generate_manual_labels()` - Create a script to generate `data/manual_labels.csv` by stratified sampling a representative subset of commits from the 500 repos, manually labeling them as 'bug_fix' or 'not_bug_fix' (simulated via commit message keywords for automation), and saving the ground truth.
- [X] T008a [P] Implement `src/code/analysis.py`: `run_regression()`: Implement Multiple Linear Regression (MLR) with robust standard errors (using `statsmodels` or `scikit-learn` with `White` covariance) to model maintainability vs. comment metrics, controlling for age, LOC, and complexity. (Note: Negative Binomial/Beta are prohibited by Constitution Principle VII).
- [X] T008b [P] Implement `src/code/analysis.py`: `apply_fdr_correction()`: Implement Benjamini-Hochberg FDR correction on p-values from multiple hypothesis tests.
- [X] T008c [P] Implement `src/code/analysis.py`: `run_sensitivity()`: Implement sensitivity analysis sweeping thresholds over a range of small values for exploratory purposes only; ensure final report uses fixed p < 0.05.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition & Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Identify 500 high-star Python repos and clone full git history locally.

**Independent Test**: Verify a representative set of unique repositories exist in `data/raw/` with accessible `git log` history, independent of metric logic.

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `src/code/fetch.py` `get_candidates()`: Query HuggingFace `codeparrot/github-code` for Python repos ≥100 stars. If unreachable, fallback to `. Return list of 500 candidate IDs.
- [X] T013 [US1] Implement `src/code/fetch.py` `clone_batch()`: Use `BatchIterator` (T004b) to clone repos to `data/raw/` with full history; handle errors (skip/log); enforce batch size ≤10. <!-- FAILED: unspecified -->
- [X] T014 [US1] Implement `src/code/fetch.py` `validate_count()`: Ensure target of valid clones with git history is met; log exclusions; retry if target not met. <!-- FAILED: unspecified -->
- [ ] T015b [US1] Handle edge case: Git clone failures: Implement retry logic and skip mechanism in `clone_batch`; log error and continue to next candidate.
- [ ] T015c [US1] Handle edge case: Missing history: Implement check in `clone_batch` to exclude repos with empty git history; log exclusion.
- [ ] T016 [US1] Add logging for acquisition stats: Output success rate, excluded repos count, and total valid clones to `logs/acquisition_stats.json`.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests AFTER implementation to verify the implemented logic**

- [X] T010a [P] [US1] Unit test `test_get_candidates_returns_ids` in `tests/unit/test_fetch.py`.
- [X] T010b [P] [US1] Unit test `test_get_candidates_fallback` in `tests/unit/test_fetch.py`.
- [X] T011 [P] [US1] Integration test for batch cloning and history validation in `tests/integration/test_clone.py`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Metric Computation (Priority: P2)

**Goal**: Compute comment quality (readability, sentiment, density) and maintainability (churn, bug fix rate) metrics.

**Independent Test**: Run pipeline on a small subset; verify values match manual inspection (e.g., "This is a simple test." → Flesch-Kincaid 65.3 ± 0.1).

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement `src/code/extract.py`: Parse Python files with `tree-sitter`, extract comments, handle empty files, and save to `data/processed/comments.json`.
- [X] T021b [P] [US2] Implement `src/code/metrics.py` `calc_density()`: Calculate comment density as (lines of comment / lines of code) with precision ≥2 decimal places; handle division by zero.
- [X] T022 [P] [US2] Implement `src/code/metrics.py` `calc_readability()`: Use `textstat.flesch_kincaid_grade` on extracted comments; validate against known string "This is a simple test." (target 65.3 ± 0.1).
- [X] T023 [P] [US2] Implement `src/code/metrics.py` `calc_sentiment()`: Use `TextBlob` polarity on extracted comments; validate against known string.
- [X] T024 [US2] Implement `src/code/metrics.py` `calc_churn()`: Parse `git log --numstat` for lines changed per commit; aggregate to repository level; validate against manual spot-check.
- [ ] T025 [US2] Implement `src/code/metrics.py` `calc_quality_rate()`: Sample commits using `CommitSampler`; run `pylint` for error-level warnings; calculate ratio; validate against `data/manual_labels.csv` (global stratified sample N=50) and compute 95% CI.
- [X] T026 [US2] Implement `src/code/utils.py` memory stream processing: Ensure `MemoryMonitor` (T004c) is active during metric aggregation to stay within acceptable RAM limits.
- [~] T027 [US2] Aggregate metrics: Combine readability, sentiment, density, churn, bug_fix_rate, and complexity into `data/processed/metrics.csv` with precision ≥2 decimal places. (Note: This task depends on T021 and T021b; NOT parallel).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for `extract_comments_ast()` accuracy in `tests/unit/test_extract.py`.
- [X] T019 [P] [US2] Unit test for `calc_readability()` against known string in `tests/unit/test_metrics.py`.
- [ ] T020 [P] [US2] Integration test for full metric pipeline on a reference repo in `tests/integration/test_metrics_pipeline.py`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis & Reporting (Priority: P3)

**Goal**: Perform regression/correlation analysis, apply corrections, and generate reports with associational framing.

**Independent Test**: Run analysis on pre-computed CSV; verify output contains p-values, R², and corrected significance flags.

### Implementation for User Story 3

- [ ] T030 [P] [US3] Implement `src/code/analysis.py` `run_regression()`: Model maintainability vs. comment metrics using Multiple Linear Regression with robust standard errors (Constitution Principle VII), controlling for age, LOC, and cyclomatic complexity (T006b).
- [ ] T031 [P] [US3] Implement `src/code/analysis.py` `apply_fdr_correction()`: Apply Benjamini-Hochberg FDR correction to p-values; output corrected p-values.
- [ ] T032 [P] [US3] Implement `src/code/analysis.py` `run_sensitivity()`: Sweep significance thresholds over {0.01, 0.05, 0.1} for exploratory analysis; record rate variations; ensure final report uses fixed p < 0.05.
- [ ] T032b [US3] Generate sensitivity report: Create `data/processed/sensitivity_report.json` containing the results of the threshold sweep.
- [ ] T033 [US3] Implement report generation: Ensure `is_significant` boolean, p-values, and R² values in `data/processed/analysis_results.json` meet SC-003. (Note: Depends on T030, T031, T032; NOT parallel).
- [ ] T033b [US3] Create report template: Create `docs/report.md` with placeholders for findings, ensuring associational framing.
- [ ] T034 [US3] Enforce associational framing (FR-008): Update `analysis.py` report generation function to replace causal verbs (e.g., "causes") with correlational verbs (e.g., "is associated with") and append a disclaimer to all report sections.
- [ ] T035 [US3] Add timing and memory usage checks: Create `tests/integration/test_resource_limits.py` and add `@timeit` decorator to `run_pipeline` to verify acceptable runtime and memory limits (FR-012, FR-011).

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Unit test for FDR correction logic in `tests/unit/test_analysis.py`.
- [ ] T029 [P] [US3] Integration test for regression model on synthetic data in `tests/integration/test_regression.py`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Documentation updates: Create `docs/README.md` with installation steps and `docs/api.md` with function signatures for all public APIs.
- [ ] T038 Performance optimization: Profile `clone_batch` and `calc_churn` to identify bottlenecks; optimize I/O or parallelism if runtime is excessive.
- [ ] T039 [P] Additional unit tests for edge cases in `tests/unit/`.
- [ ] T040a [P] Security hardening (Dependencies): Run `pip-audit` specifically on `requirements.txt` and fail the build if any known vulnerabilities are found.
- [ ] T040b [P] Security hardening (Source): Run `bandit -r src/` to scan source code for security issues; fix any high-severity findings.
- [ ] T041a [P] Validation script creation: Create `docs/quickstart_validation.py` script that imports key modules and verifies basic execution flow.
- [ ] T041b [P] Validation execution: Execute `python -m docs.quickstart_validation --strict` and ensure it exits with code 0 and no errors.

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 data availability

### Within Each User Story

- Tests (if included) MUST be written AFTER implementation to verify the implemented logic
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

---

## Parallel Example: User Story 1

```bash
# Launch all implementation tasks for User Story 1 together:
Task: "Implement src/code/fetch.py get_candidates()"
Task: "Implement src/code/fetch.py clone_batch()"

# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for fetch.py candidate selection logic in tests/unit/test_fetch.py"
Task: "Integration test for batch cloning and history validation in tests/integration/test_clone.py"
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
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (if TDD approach is used)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence