# Tasks: Evaluating the Impact of Code Generation Models on Developer Productivity

**Input**: Design documents from `/specs/001-code-gen-productivity/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
- **Web app**: `code/experiment/`, `code/quality/`, `code/analysis/`
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

- [ ] T001 Create project structure with exact directories: code/, code/experiment/, code/quality/, code/analysis/, code/data/, code/models/, code/logs/, tests/, tests/contract/, tests/integration/, tests/unit/, data/raw/, data/derived/, data/configs/

- [ ] T002 Initialize Python 3.11 project with Flask, radon, coverage.py, pylint, scipy, statsmodels, torch, datasets dependencies in requirements.txt

- [ ] T003 [P] Configure linting and formatting tools (black, flake8) in .flake8, pyproject.toml

- [ ] T044 [P] Verify compute feasibility on GitHub Actions free-tier (2 CPU, ~7 GB RAM, ~14 GB disk, NO GPU, ≤6 h) with test script in tests/unit/test_compute_feasibility.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T007 Create base data models/entities matching data-model.md (Participant, Session, Problem, Submission, Metric) in code/data/models.py

- [ ] T004-DB Create SQLite database schema with Participant, Session, Problem, Submission, Metric tables in code/data/database.py (depends on T007)

- [ ] T004-S Create Session table in SQLite database schema with fields: session_id, participant_id, condition, start_time, end_time, problem_order, counterbalancing_order (depends on T007)

- [ ] T008 Configure environment configuration management (API keys, dataset paths) in code/config.py

- [ ] T005 Implement consent flow infrastructure with informed consent validation in code/experiment/consent.py (depends on T007, T008)

- [ ] T006 Setup logging infrastructure for experiment.log with participant ID, session ID, condition assignments, seeds in code/experiment/logger.py (depends on T008)

- [ ] T009 Setup randomization module with fixed seed for reproducibility and Latin square counterbalancing in code/experiment/randomization.py

- [ ] T016 Add timestamp logging with UTC format and ≥1 second precision (FR-002) in code/experiment/logger.py

- [ ] T017 Add submission ID generation and UTF-8 source code storage (FR-003) in code/experiment/submission.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Experiment Execution (Priority: P1) 🎯 MVP

**Goal**: Execute the controlled within-subject experiment where participants complete coding tasks under LLM-assisted and baseline conditions, recording timestamps, code submissions, consent, and randomization

**Independent Test**: Can be fully tested by running the experiment interface with a single participant through both conditions and verifying that timestamps, code, consent, and randomization are logged correctly

### Implementation for User Story 1

- [ ] T012 [US1] Implement problem_loader.py to download HumanEval from https://github.com/openai/human-eval (commit hash) and Codeforces medium problems from https://codeforces.com/api/problemset.problems (filter: medium difficulty) in code/experiment/problem_loader.py. Add SHA256 checksum verification and record commit hash in data/metadata.yaml per Constitution VI.

- [ ] T013 [US1] Implement Flask experiment interface (app.py) with problem presentation, timestamp recording, and code submission streaming in code/experiment/app.py (depends on T016, T017). Note: Experiment runs on participant devices; data streamed to server for analysis on GitHub Actions.

- [ ] T015 [US1] Add validation for problem complexity (FR-014): verify average solution time ≥5 minutes and medium-difficulty level. Include FR-001 verification: ≥95% successful problem loading rate with retry logic and failure logging in code/experiment/problem_loader.py

- [ ] T018 [US1] Implement StarCoder model for Python code generation (CPU-only, ≤1GB) in code/models/starcoder_cpu.py

- [ ] T018-JaCoText [US1] Implement JaCoText model for Java code generation in code/models/jacotext_cpu.py. Include Constitution II verification: confirm verified public source exists. If verification fails, document fallback to StarCoder for both languages and flag spec revision for kickback.

- [ ] T019 [US1] Implement baseline condition with LLM assistant disabled and condition switch logging in code/experiment/app.py

- [ ] T020 [US1] Handle edge cases: timeout/crash protection for test execution, participant dropout tracking, syntax error handling in code/experiment/error_handler.py

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [US1] Contract test for submission schema in tests/contract/test_submission.py (validates FR-003, FR-012) - depends on T012-T020 implementation

- [ ] T011 [US1] Integration test for experiment flow with consent, randomization, and condition switch in tests/integration/test_experiment.py - depends on T012-T020 implementation

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Code Quality Assessment Pipeline (Priority: P2)

**Goal**: Run automated quality assessment on each submitted code sample, computing pass rate, cyclomatic complexity, test coverage, and static-analysis warnings

**Independent Test**: Can be fully tested by submitting known code samples and verifying that all four quality metrics are computed and stored correctly

### Implementation for User Story 2

- [ ] T023 [P] [US2] Implement pass_rate.py to execute HumanEval test suite and compute pass rate with ≥0.01 precision (FR-004) in code/quality/pass_rate.py

- [ ] T024 [P] [US2] Implement complexity.py to compute cyclomatic complexity using radon cc with integer ≥1 (FR-005) in code/quality/complexity.py

- [ ] T025 [P] [US2] Implement coverage.py to measure test coverage via coverage.py with percentage ≥0% and ≤100% (FR-006) in code/quality/coverage.py

- [ ] T026 [P] [US2] Implement static_analysis.py to count pylint warnings (Python) with integer ≥0 (FR-007) in code/quality/static_analysis.py

- [ ] T027 [US2] Add timeout handling for code execution that causes test suite to timeout or crash in code/quality/executor.py

- [ ] T028 [US2] Add error handling for syntax errors and non-compilable code submissions in code/quality/executor.py

- [ ] T029 [US2] Integrate quality metrics with Submission entity and store in database with submission ID linkage in code/data/models.py (depends on T023-T026)

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [US2] Contract test for metric schema in tests/contract/test_metric.py (validates FR-004 to FR-007) - depends on T023-T026 implementation

- [ ] T022 [US2] Integration test for quality assessment pipeline with end-to-end metric computation in tests/integration/test_quality.py - depends on T023-T026 implementation

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Reporting (Priority: P3)

**Goal**: Run statistical analysis comparing LLM-assisted vs baseline conditions, computing paired t-tests (or Wilcoxon signed-rank if non-normal), effect sizes (Cohen's d), and 95% confidence intervals for all metrics

**Independent Test**: Can be fully tested by running the analysis script on a CSV dataset with known values and verifying that p-values, effect sizes, and confidence intervals are computed correctly

### Implementation for User Story 3

- [ ] T032 [P] [US3] Implement statistical_tests.py with paired t-test and Wilcoxon signed-rank (if non-normal) with p-value and Cohen's d effect size (FR-008, FR-010) in code/analysis/statistical_tests.py

- [ ] T033 [P] [US3] Implement correction.py with Bonferroni or Holm multiple-comparison correction to control family-wise error rate at α ≤ 0.05 (FR-009) in code/analysis/correction.py

- [ ] T034 [US3] Implement sensitivity.py with threshold sensitivity analysis sweeping absolute diff ∈ {0.01, 0.05, 0.1} and reporting coefficient of variation (FR-011) in code/analysis/sensitivity.py

- [ ] T035 [US3] Add 95% confidence interval computation with ±0.01 precision for all comparisons (FR-010) in code/analysis/statistical_tests.py

- [ ] T036 [US3] Generate analysis report as Markdown at code/analysis/report.md with sections: executive_summary, time_analysis, quality_metrics, statistical_significance, sensitivity_analysis, recommendations (SC-001, SC-002) (depends on T035)

- [ ] T037 [US3] Export results to data/derived/analysis_results.csv with checksum and metadata in data/derived/ (depends on T036). Ensure reproducibility: analysis pipeline must run end-to-end on fresh GitHub Actions runner.

- [ ] T038 [US3] Handle incomplete within-subject data (participant dropout >20%) with exclusion from paired analysis in code/analysis/data_cleaning.py

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [US3] Contract test for analysis_result schema in tests/contract/test_analysis_result.py (validates FR-008 to FR-011) - depends on T032-T038 implementation

- [ ] T031 [US3] Integration test for statistical analysis pipeline with paired data and multiple-comparison correction in tests/integration/test_analysis.py - depends on T032-T038 implementation

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Constitution Agents & Cross-Cutting Concerns

**Purpose**: Implement Constitution-mandated agents and polish improvements

- [ ] T050 [P] Implement Reference-Validator Agent per Constitution II (Verified Accuracy Gate) with citation title-token-overlap ≥0.7 threshold in code/agents/reference_validator.py

- [ ] T051 [P] Implement Advancement-Evaluator Agent per Constitution Governance (sole writer of current_stage) in code/agents/advancement_evaluator.py

- [ ] T052 [P] Add Reference-Validator integration to artifact write workflow (blocks on unverified citations) in code/workflows/

- [ ] T053 [P] Add Advancement-Evaluator integration to stage transition workflow in code/workflows/

- [ ] T039 [P] Documentation updates: quickstart.md (setup, run experiment, run analysis), README.md (project overview, architecture, dependencies), data-model.md (entity definitions, schema) - verify all files contain required content

- [ ] T040 Code cleanup and refactoring: remove TODO comments, standardize snake_case naming, enforce max line length 100, remove unused imports (verified by flake8)

- [ ] T041 Security hardening: use cryptography.fernet for file encryption at rest, store keys in environment variables (not committed), verify with test_data_encrypted.py - no PII in committed data

- [ ] T042 [P] Additional unit tests: tests/unit/test_pass_rate.py, tests/unit/test_complexity.py, tests/unit/test_coverage.py, tests/unit/test_static_analysis.py, tests/unit/test_statistical_tests.py, tests/unit/test_correction.py, tests/unit/test_sensitivity.py

- [ ] T043 Run quickstart.md validation and verify full pipeline execution

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Constitution Agents & Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 submissions being available for quality assessment
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 data being available for statistical analysis

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- T007, T008, T009 in Phase 2 can run in parallel (once T008 is before T005/T006)
- All quality metric tasks (T023-T026) marked [P] can run in parallel
- All statistical analysis core tasks (T032, T033) marked [P] can run in parallel
- All Constitution Agent tasks (T050-T053) marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 2 Quality Metrics

```bash
# Launch all quality metric implementations together (no dependencies between them):
Task: "Implement pass_rate.py in code/quality/pass_rate.py"
Task: "Implement complexity.py in code/quality/complexity.py"
Task: "Implement coverage.py in code/quality/coverage.py"
Task: "Implement static_analysis.py in code/quality/static_analysis.py"
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
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Compute Feasibility**: All tasks MUST run on GitHub Actions free-tier (2 CPU, ~7 GB RAM, ~14 GB disk, NO GPU, ≤6 h)
- **Dataset URLs**: All dataset downloads MUST use real, reachable URLs from official repos per Constitution VI (HumanEval: GitHub openai/human-eval, Codeforces: public API codeforces.com/api/problemset.problems)
- **Model Constraints**: StarCoder for Python (CPU-only, ≤1GB); JaCoText requires verified source per Constitution II - if unavailable, document fallback and flag spec revision
- **Data Flow**: Tasks producing data (T012, T013, T023-T026) MUST come before tasks consuming that data (T032-T038)
- **Constitution Compliance**: Reference-Validator and Advancement-Evaluator agents (T050-T053) are blocking gates for artifact transitions per Constitution II and Governance

## Plan-Root Cause Flags

The following concerns require plan/spec revision before proceeding:

1. **JaCoText Model (FR-013)**: JaCoText has no verified public source per Constitution II. Task T018-JaCoText includes verification step; if verification fails, task documents fallback to StarCoder for both languages and flags spec revision for kickback.

2. **Experiment Execution Platform**: Plan currently assigns experiment to "separate server" but Constitution I requires all results reproducible on fresh GitHub Actions runner. T013 Flask interface updated for GitHub Actions-compatible deployment; plan revision required to resolve 6-hour job limit for 30 participants.

3. **Session Entity**: Session entity now explicitly created in T004-S and T004-DB; data-model.md must be verified to match.