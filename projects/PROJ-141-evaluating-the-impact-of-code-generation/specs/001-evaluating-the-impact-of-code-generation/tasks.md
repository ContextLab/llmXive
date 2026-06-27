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

- **Single project**: `code/`, `tests/` at repository root (per plan.md structure)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (code/, tests/, data/, models/)
- [ ] T002 Initialize Python 3.11 project with requirements.txt (Flask, radon, coverage.py, pylint, scipy, statsmodels, torch, datasets)
- [ ] T003 [P] Configure linting and formatting tools (black, flake8) in code/

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Configure environment configuration management for API keys, dataset paths (code/config/settings.py)
- [ ] T005 [P] Implement informed consent flow with IRB approval verification (code/experiment/consent.py)
- [ ] T006 [P] Setup logging infrastructure for experiment.log with participant IDs, condition assignments, seeds (code/logs/experiment.py) - FR-012 infrastructure layer
- [ ] T007 Create base models/entities matching data-model.md (code/data/models.py)
- [ ] T008 Setup SQLite database schema for Participant, Session, Problem, Submission, Metric entities (code/data/db_schema.py)
- [ ] T009 [P] Verify HumanEval dataset URL and download script with commit hash/API snapshot capture (code/data/download_humaneval.py)
- [ ] T010 [P] Verify Codeforces dataset URL and download script with commit hash/API snapshot capture (code/data/download_codeforces.py)
- [ ] T011 **BLOCKING**: Resolve JaCoText model source gap - document alternative OR verify CPU-tractable model in research.md (code/models/jacotext_cpu.py) - MUST guarantee resolution before proceeding
- [ ] T012 Verify StarCoder model size ≤1GB and CPU-tractable; implement CPU-only inference wrapper (code/models/starcoder_cpu.py)
- [ ] T012a [P] Verify JaCoText model size ≤1GB and CPU-tractable (code/models/jacotext_cpu.py)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Experiment Execution (Priority: P1) 🎯 MVP

**Goal**: Implement the controlled within-subject experiment interface with problem presentation, timestamp recording, code submission, and condition management

**Independent Test**: Can be fully tested by running the experiment interface with a single participant through both conditions and verifying that timestamps, code, consent, and randomization are logged correctly

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T013 [P] [US1] Contract test for submission schema in tests/contract/test_submission.py
- [ ] T014 [P] [US1] Integration test for experiment flow with single participant in tests/integration/test_experiment_flow.py

### Implementation for User Story 1

- [ ] T015 [P] [US1] Implement problem loading for HumanEval/Codeforces with ≥95% load rate (code/experiment/problem_loader.py)
- [ ] T015a [US1] Verify ≥95% problem loading rate per FR-001 (code/experiment/problem_loader.py)
- [ ] T016 [P] [US1] Implement problem validation per FR-014 (avg solution time ≥5 min, medium-difficulty) (code/experiment/problem_validator.py)
- [ ] T017 [US1] Implement Flask experiment interface (app.py) with problem presentation and code input (code/experiment/app.py)
- [ ] T018 [US1] Implement timestamp recording with ≥1 second precision in UTC format (code/experiment/timestamp_recorder.py)
- [ ] T019 [US1] Implement code submission streaming as UTF-8 with unique submission ID per problem (code/experiment/submission_handler.py)
- [ ] T020 [US1] Implement condition switching logic (LLM-assisted → baseline) with LLM assistant disable (code/experiment/condition_manager.py)
- [ ] T021 [US1] Implement randomization with participant ID, condition assignment, seed logging AND pinning random seeds in code/ for reproducibility per Constitution Principle I (code/experiment/randomization.py) - FR-012 logging layer
- [ ] T022 [US1] Implement counterbalancing (Latin square or random order swap) for carryover mitigation (code/experiment/counterbalance.py)
- [ ] T023 [US1] Implement JaCoText model integration for Java code generation (CPU-only) (code/models/jacotext_cpu.py) - MUST wait for T011 resolution confirmation
- [ ] T024 [US1] Implement StarCoder model integration for Python code generation (CPU-only) (code/models/starcoder_cpu.py) - MUST wait for T012 completion
- [ ] T024a [US1] Implement conditional model selection fallback (StarCoder for both languages if JaCoText unavailable) (code/models/model_selector.py)
- [ ] T025 [US1] Implement participant recruitment flow with ≥1 year programming experience filter (code/experiment/recruitment.py)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Code Quality Assessment Pipeline (Priority: P2)

**Goal**: Run automated quality assessment on each submitted code sample, computing pass rate, cyclomatic complexity, test coverage, and static-analysis warnings

**Independent Test**: Can be fully tested by submitting known code samples and verifying that all four quality metrics are computed and stored correctly

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US2] Contract test for metric schema in tests/contract/test_metric.py
- [ ] T027 [P] [US2] Integration test for quality assessment pipeline in tests/integration/test_quality_pipeline.py

### Implementation for User Story 2

- [ ] T028 [P] [US2] Implement HumanEval test suite execution and pass rate calculation (≥0.01 precision) (code/quality/pass_rate.py)
- [ ] T029 [P] [US2] Implement cyclomatic complexity computation using radon cc (integer ≥1) (code/quality/complexity.py)
- [ ] T030 [P] [US2] Implement test coverage measurement via coverage.py (percentage 0-100%) (code/quality/coverage.py)
- [ ] T031 [P] [US2] Implement static analysis warning count using pylint (Python) or checkstyle (Java) (code/quality/static_analysis.py)
- [ ] T032 [US2] Implement quality metric aggregation and storage per submission (code/quality/metric_aggregator.py)
- [ ] T033 [US2] Implement timeout/crash handling for test suite execution (edge case: participant code crashes environment) (code/quality/execution_sandbox.py)
- [ ] T034 [US2] Implement syntax error detection and handling for invalid submissions (edge case: code fails to compile) (code/quality/syntax_validator.py)
- [ ] T035 [US2] Implement LLM inference timeout handling for 6-hour GitHub Actions limit (code/quality/llm_timeout_handler.py) - Edge Case 3 (LLM model exceeds 6-hour job time limit during participant sessions)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Reporting (Priority: P3)

**Goal**: Run statistical analysis comparing LLM-assisted vs baseline conditions with paired t-tests, effect sizes, confidence intervals, and multiple-comparison correction

**Independent Test**: Can be fully tested by running the analysis script on a CSV dataset with known values and verifying that p-values, effect sizes, and confidence intervals are computed correctly

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T036 [P] [US3] Contract test for analysis_result schema in tests/contract/test_analysis_result.py
- [ ] T037 [P] [US3] Integration test for full analysis pipeline on sample data in tests/integration/test_analysis_pipeline.py

### Implementation for User Story 3

- [ ] T038 [P] [US3] Implement CSV dataset loading for paired participant data (code/analysis/data_loader.py)
- [ ] T039 [P] [US3] Implement paired t-test computation for time and quality metrics (code/analysis/statistical_tests.py)
- [ ] T040 [P] [US3] Implement Wilcoxon signed-rank test for non-normal distributions (code/analysis/statistical_tests.py)
- [ ] T041 [P] [US3] Implement Cohen's d effect size computation with 95% CI (±0.01 precision) (code/analysis/statistical_tests.py)
- [ ] T042 [P] [US3] Implement Bonferroni multiple-comparison correction (code/analysis/correction.py)
- [ ] T043 [P] [US3] Implement Holm multiple-comparison correction (code/analysis/correction.py)
- [ ] T043a [US3] Verify multiple-comparison correction achieves family-wise error rate ≤0.05 per SC-004 (code/analysis/correction.py)
- [ ] T044 [US3] Implement sensitivity analysis for a time reduction threshold range (sweep diff ∈ {0.01, 0.05, 0.1}) with coefficient of variation reporting (FR-011 combined output with verification) (code/analysis/sensitivity.py)
- [ ] T045 [US3] Implement results export with all statistics and 95% CIs (code/analysis/export.py)
- [ ] T046 [US3] Implement dropout handling for incomplete within-subject data (edge case: participant drops out mid-experiment) (code/analysis/dropout_handler.py)
- [ ] T047 [US3] Implement fast-completion detection for tasks <30 seconds (edge case: participant completes significantly faster than expected) (code/analysis/fast_completion.py)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T048 [P] Documentation updates: Create quickstart.md, README.md, and API documentation in docs/ (specific deliverables: docs/quickstart.md, docs/README.md, docs/api.md)
- [ ] T049 Code cleanup and refactoring across code/: Run black formatting, flake8 cleanup, remove dead code (specific deliverables: all .py files formatted with black, flake8 passes)
- [ ] T050 [P] Run contract tests for all schemas (tests/contract/)
- [ ] T051 [P] Run integration tests for all user stories (tests/integration/)
- [ ] T052 [P] Run unit tests for quality metrics and statistical tests (tests/unit/)
- [ ] T053a [US3] Implement anonymization and encryption for participant data (code/analysis/anonymizer.py, code/analysis/encryption.py)
- [ ] T053b [US3] Implement secure deletion workflow for participant data per Constitution Principle VII (code/analysis/data_deletion.py)
- [ ] T054 Run quickstart.md validation and document any gaps
- [ ] T055 [P] Create metadata.yaml with dataset versions, commit hashes, timestamps (data/metadata.yaml)
- [ ] T055a [US3] Update state file updated_at timestamp per Constitution Principle V when artifacts change (state/projects/PROJ-141-evaluating-the-impact-of-code-generation.yaml)
- [ ] T056 [P] Implement checksum verification for all files under data/ (data/checksums.py)
- [ ] T056a [US3] Write data checksums to state file artifact_hashes map per Constitution Principle III (state/projects/PROJ-141-evaluating-the-impact-of-code-generation.yaml)
- [ ] T057 Verify GitHub Actions free-tier compatibility (2 CPU, 7 GB RAM, 14 GB disk, ≤6 h) with full pipeline test
- [ ] T057a [P] Document separate server execution requirement for experiment runtime in docs/architecture.md (plan.md Compute Feasibility Decision constraint)
- [ ] T058 Create constraints.md documenting all constraints and assumptions in paper-ready format (specific deliverable: docs/constraints.md)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
  - **T011 (JaCoText gap)** must be resolved before proceeding with model integration tasks
  - **T009, T010 (dataset URLs)** must be verified with version capture before problem loading implementation
  - **T012 (StarCoder verification)** must be completed before LLM integration
  - **T012a (JaCoText verification)** must be completed before JaCoText integration
  - **T007 (base models)** must precede T008 (database schema) - schema depends on entity definitions
  - **T006 (logging infrastructure)** must precede T021 (randomization logging) - infrastructure before usage
- **User Stories (Phase 3+)**: Data-flow dependencies exist between stories
  - **US1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
  - **US2 (P2)**: Depends on US1 submissions being available (T019 code submission must complete first)
  - **US3 (P3)**: Depends on US2 metrics being available (T032 metric aggregation must complete first)
  - Stories can proceed in parallel ONLY if data dependencies are satisfied
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
  - T023 (JaCoText integration) depends on T011 resolution confirmation
  - T024 (StarCoder integration) depends on T012 completion
  - T024a (fallback logic) depends on T023 and T024
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 submissions being available
  - T028-T031 (individual metrics) can run in parallel
  - T032 (aggregation) MUST come after T028-T031 complete
  - T033-T035 (edge case handling) can run in parallel
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 metrics being available
  - T038 (CSV data loader) MUST precede T039-T043 (statistical tests)
  - T039-T043 (statistical tests) can run in parallel after T038
  - T042-T043a (correction + verification) can run in parallel after T039-T041
  - T044 (sensitivity analysis) MUST come after T039-T043 complete

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
  - T004, T005, T006, T009, T010, T012, T012a can run in parallel (config, consent, logging, dataset/model verification)
- Once Foundational phase completes, US1 can start independently
- US2 can start once US1 submission infrastructure is complete
- US3 can start once US2 metric infrastructure is complete
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel (T028-T031, T039-T041)
- Different user stories can be worked on in parallel by different team members IF data dependencies are satisfied

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for submission schema in tests/contract/test_submission.py"
Task: "Integration test for experiment flow with single participant in tests/integration/test_experiment_flow.py"

# Launch all foundation verification tasks together:
Task: "Verify HumanEval dataset URL and download script with commit hash/API snapshot capture"
Task: "Verify Codeforces dataset URL and download script with commit hash/API snapshot capture"
Task: "Verify StarCoder model size ≤1GB and CPU-tractable"
Task: "Verify JaCoText model size ≤1GB and CPU-tractable"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
   - **Must resolve T011 (JaCoText gap)** before proceeding
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
   - Developer A: User Story 1 (experiment interface)
   - Developer B: User Story 2 (quality assessment) - waits for US1 submissions
   - Developer C: User Story 3 (statistical analysis) - waits for US2 metrics
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **CRITICAL**: T011 (JaCoText gap) must be RESOLVED (not just documented) before model integration tasks proceed
- **CRITICAL**: All dataset/model URLs must be verified with version capture and documented in data/metadata.yaml
- **CRITICAL**: All tasks MUST run on GitHub Actions free-tier (2 CPU, 7 GB RAM, 14 GB disk, NO GPU, ≤6 h)
- **CRITICAL**: US2 depends on US1 submissions; US3 depends on US2 metrics - data-flow ordering must be respected
- **CRITICAL**: T023 (JaCoText) and T024 (StarCoder) are NOT parallel-safe - must wait for T011 and T012 resolution
- **CRITICAL**: Constitution Principle I (seed pinning), III (checksums to state), V (timestamp updates), VII (secure deletion) have dedicated tasks
- **CRITICAL**: FR-001 (≥95% load rate), FR-011 (sensitivity analysis), SC-004 (error rate ≤0.05) have verification tasks
- **CRITICAL**: Edge cases from spec all have corresponding tasks (T033, T034, T035, T046, T047, T035a)
- **CRITICAL**: T053 split into T053a (anonymization/encryption) and T053b (secure deletion) with clear deliverables
- **CRITICAL**: T055a updates state file timestamp, T056a writes checksums to state file
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence