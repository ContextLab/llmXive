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

- [X] T001 Create project structure per implementation plan (code/, tests/, data/, models/, logs/)
- [X] T002 Initialize Python 3.11 project with requirements.txt (Flask, radon, coverage.py, pylint, scipy, statsmodels, torch, datasets)
- [X] T003 [P] Configure linting and formatting tools (black, flake8) in code/
- [X] T048 [P] Documentation updates: Create quickstart.md, README.md, and API documentation in docs/ (specific deliverables: docs/quickstart.md, docs/README.md, docs/api.md)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Configure environment configuration management for API keys, dataset paths (code/config/settings.py)
- [X] T005 [US1] Implement informed consent flow with IRB approval verification (code/experiment/consent.py) - DEPENDS ON T004
- [X] T006 [US1] Setup logging infrastructure for experiment.log with participant IDs, condition assignments, seeds (code/logs/experiment.py) - FR-012 infrastructure layer - DEPENDS ON T004
- [X] T007 Create base models/entities matching data-model.md (code/data/models.py)
- [X] T008 Setup SQLite database schema for Participant, Session, Problem, Submission, Metric entities (code/data/db_schema.py)
- [X] T009 [P] Verify HumanEval dataset URL and download script with commit hash/API snapshot capture (code/data/download_humaneval.py)
- [X] T010 [P] Verify Codeforces dataset URL and download script with commit hash/API snapshot capture (code/data/download_codeforces.py)
- [X] T011a [P] Research and document alternative Java code generation model if JaCoText unavailable (code/research/java_model_alternatives.md) - deliverable: list of multiple alternatives with CPU-tractability assessment, verified sources
- [X] T011b [P] Verify JaCoText model size ≤1GB and CPU-tractability if used [UNRESOLVED-CLAIM: c_23996b17 — status=not_enough_info]; document verification process (code/models/jacotext_cpu.py) - deliverable: model size verification, CPU inference test, performance metrics
- [X] T011c [P] Run Reference-Validator Agent on JaCoText citation per Constitution II; record verification status in research.md (code/research/reference_validation.md) - deliverable: verified/mismatch/unreachable status with citation details
- [X] T012 Verify StarCoder model size ≤1GB [UNRESOLVED-CLAIM: c_3b605e3d — status=not_enough_info]; implement CPU-only inference wrapper (code/models/starcoder_cpu.py)
- [X] T053a [P] Implement anonymization and encryption for participant data: anonymization = remove PII fields (name, email, IP), replace participant ID with SHA-256 hash; encryption = AES-256-GCM [UNRESOLVED-CLAIM: c_230bf9b4 — status=not_enough_info], keys stored in environment variables (CODEX_ENCRYPTION_KEY) (code/analysis/anonymizer.py, code/analysis/encryption.py) - MUST complete BEFORE data collection per Constitution VII
- [X] T053b [P] Implement secure deletion workflow for participant data: overwrite file content 3x with os.urandom(len) then os.fsync [UNRESOLVED-CLAIM: c_029671e4 — status=not_enough_info], then os.unlink then os.fsync, then os.unlink (code/analysis/data_deletion.py) - MUST complete BEFORE data collection per Constitution VII
- [X] T055a [P] Implement automated state file timestamp update via pre-commit hook (code/hooks/pre_commit_update.py) that triggers on git commit to update state/projects/PROJ-141-evaluating-the-impact-of-code-generation.yaml updated_at on artifact changes - Constitution V compliance
- [X] T056a [P] Write data checksums to data/checksums.csv AND state file artifact_hashes map per Constitution Principle III; implement checksum generation and state file update (data/checksums.py, state/projects/PROJ-141-evaluating-the-impact-of-code-generation.yaml)
- [X] T057 [P] Verify GitHub Actions free-tier compatibility (2 CPU, 7 GB RAM, 14 GB disk, ≤6 h) [UNRESOLVED-CLAIM: c_ea2761dd — status=not_enough_info] with full pipeline test (code/infrastructure/compatibility_test.py) - deliverable: compatibility report with resource usage metrics

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Experiment Execution (Priority: P1) 🎯 MVP

**Goal**: Implement the controlled within-subject experiment interface with problem presentation, timestamp recording, code submission, and condition management

**Independent Test**: Can be fully tested by running the experiment interface with a single participant through both conditions and verifying that timestamps, code, consent, and randomization are logged correctly

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T013 [P] [US1] Contract test for submission schema in tests/contract/test_submission.py
- [X] T014 [P] [US1] Integration test for experiment flow with single participant in tests/integration/test_experiment_flow.py

### Implementation for User Story 1

- [X] T015 [P] [US1] Implement problem loading for HumanEval/Codeforces with ≥95% load rate [UNRESOLVED-CLAIM: c_84db99a7 — status=not_enough_info] (code/experiment/problem_loader.py)
- [X] T015a [P] [US1] Verify ≥95% problem loading rate per FR-001: run 100-sample load test, count successful loads, compute rate = successes/100, verify ≥0.95 (code/experiment/problem_loader.py)
- [X] T016 [P] [US1] Implement problem validation per FR-014 (avg solution time ≥5 min, medium-difficulty) (code/experiment/problem_validator.py)
- [X] T017 [US1] Implement Flask experiment interface (app.py) with problem presentation and code input (code/experiment/app.py)
- [X] T018 [US1] Implement timestamp recording with ≥1 second precision in UTC format [UNRESOLVED-CLAIM: c_9300aa17 — status=not_enough_info] (code/experiment/timestamp_recorder.py)
- [ ] T019 [US1] Implement code submission streaming as UTF-8 with unique submission ID per problem (code/experiment/submission_handler.py)
- [ ] T020 [US1] Implement condition switching logic (LLM-assisted → baseline) with LLM assistant disable (code/experiment/condition_manager.py)
- [X] T021 [US1] Implement randomization with participant ID, condition assignment, seed logging AND pinning random seeds in code/ for reproducibility per Constitution Principle I (code/experiment/randomization.py) - FR-012 logging layer
- [X] T022 [US1] Implement counterbalancing (Latin square or random order swap) for carryover mitigation (code/experiment/counterbalance.py)
- [X] T023 [US1] Implement JaCoText model integration for Java code generation (CPU-only): load model from code/models/jacotext_cpu.py, call inference API with prompt, catch model loading/inference errors, log submission with model response (code/models/jacotext_cpu.py) - MUST wait for T011b/T011c resolution confirmation <!-- FAILED: unspecified -->
- [X] T024 [US1] Implement StarCoder model integration for Python code generation (CPU-only) (code/models/starcoder_cpu.py) - MUST wait for T012 completion
- [X] T024a [US1] Implement conditional model selection fallback: unavailable = model load failure OR size >1GB; trigger = config flag in settings.py; fallback = StarCoder for both languages with warning logged (code/models/model_selector.py)
- [X] T025 [US1] Implement participant recruitment flow with ≥1 year programming experience filter [UNRESOLVED-CLAIM: c_9f0411de — status=not_enough_info] (code/experiment/recruitment.py)

### User Story 1 Test Execution

- [X] T050a [P] Run contract tests for US1 schemas (tests/contract/test_submission.py) <!-- FAILED: unspecified -->
- [X] T051a [P] Run integration tests for US1 (tests/integration/test_experiment_flow.py) <!-- FAILED: unspecified -->
- [~] T052a [P] Run unit tests for US1 components (tests/unit/test_experiment_*.py) <!-- ATOMIZE: requested -->

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Code Quality Assessment Pipeline (Priority: P2)

**Goal**: Run automated quality assessment on each submitted code sample, computing pass rate, cyclomatic complexity, test coverage, and static-analysis warnings

**Independent Test**: Can be fully tested by submitting known code samples and verifying that all four quality metrics are computed and stored correctly

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US2] Contract test for metric schema in tests/contract/test_metric.py
- [~] T027 [P] [US2] Integration test for quality assessment pipeline in tests/integration/test_quality_pipeline.py

### Implementation for User Story 2

- [X] T028 [P] [US2] Implement HumanEval test suite execution and pass rate calculation (≥0.01 precision) [UNRESOLVED-CLAIM: c_20f40018 — status=not_enough_info] (code/quality/pass_rate.py)
- [X] T029 [P] [US2] Implement cyclomatic complexity computation using radon cc (integer ≥1 (Wikidata Q6007191, https://www.wikidata.org/wiki/Q6007191)) [UNRESOLVED-CLAIM: c_3e8fc3c4 — status=not_enough_info] (code/quality/complexity.py)
- [X] T030 [P] [US2] {{claim:c_d6f9e3b9}} (code/quality/coverage.py)
- [X] T031 [P] [US2] Implement static analysis warning count using pylint (Python) or checkstyle (Java) (code/quality/static_analysis.py)
- [X] T032 [US2] Implement quality metric aggregation and storage per submission (code/quality/metric_aggregator.py)
- [X] T033 [P] [US2] Set 300s timeout for test suite execution [UNRESOLVED-CLAIM: c_06c1d1f2 — status=not_enough_info], catch subprocess.TimeoutExpired/Exception, log error with submission ID and traceback, return error response to client (code/quality/execution_sandbox.py)
- [X] T034 [P] [US2] Implement syntax error detection and handling for invalid submissions: parse with ast.parse(), catch SyntaxError, log submission ID with error details and line number, return 400 response to user with error message (code/quality/syntax_validator.py)
- [X] T035 [P] [US2] Implement GitHub Actions job-level session timeout handling: set session limits with appropriate warning thresholds and force-stop mechanisms with graceful submission save, distinct from inference-level timeouts (code/quality/llm_timeout_handler.py)

### User Story 2 Test Execution

- [X] T050b [P] Run contract tests for US2 schemas (tests/contract/test_metric.py)
- [~] T051b [P] Run integration tests for US2 (tests/integration/test_quality_pipeline.py) <!-- FAILED: unspecified -->
- [~] T052b [P] Run unit tests for US2 components (tests/unit/test_quality_*.py)

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
- [ ] T041 [P] [US3] Implement Cohen's d effect size computation with 95% CI (±0.01 precision) [UNRESOLVED-CLAIM: c_dfc0f22c — status=not_enough_info] (code/analysis/statistical_tests.py)
- [ ] T042 [P] [US3] Implement Bonferroni multiple-comparison correction (code/analysis/correction.py)
- [ ] T043 [P] [US3] Implement Holm multiple-comparison correction (code/analysis/correction.py)
- [ ] T043a [US3] Verify multiple-comparison correction achieves family-wise error rate ≤0.05 per SC-004 (code/analysis/correction.py)
- [ ] T044 [P] [US3] Implement sensitivity analysis for a time reduction threshold range (sweep diff ∈ {0.01, 0.05, 0.1}) with coefficient of variation reporting with coefficient of variation reporting (FR-011 combined output with verification) (code/analysis/sensitivity.py)
- [ ] T045 [US3] Implement results export with all statistics and 95% CIs; generate trace_id (hash of data_row_id + code_block_file:line + timestamp) for each statistic to ensure single-source-of-truth per Constitution IV (code/analysis/export.py)
- [ ] T045a [P] [US3] Generate trace_id for each statistic: hash(data_row_id + code_block_file:line + timestamp) to create unique identifier for traceability (code/analysis/traceability.py)
- [ ] T045b [P] [US3] Validate traceability constraint enforcement: verify each exported statistic has valid trace_id that maps to exactly one data row and one code block (code/analysis/traceability_validator.py)
- [ ] T046 [P] [US3] Implement dropout handling for incomplete within-subject data: exclude incomplete pairs from paired analysis, document exclusion criteria in data/metadata.yaml with participant IDs, flag excluded participants for manual review (code/analysis/dropout_handler.py)
- [ ] T047 [P] [US3] Implement fast-completion detection for tasks <30 seconds [UNRESOLVED-CLAIM: c_f70241fe — status=not_enough_info]: log task ID with completion time, flag for manual review if time <30s, record in experiment.log (code/analysis/fast_completion.py)

### User Story 3 Test Execution

- [ ] T050c [P] Run contract tests for US3 schemas (tests/contract/test_analysis_result.py)
- [ ] T051c [P] Run integration tests for US3 (tests/integration/test_analysis_pipeline.py)
- [ ] T052c [P] Run unit tests for US3 components (tests/unit/test_analysis_*.py)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T049 Code cleanup and refactoring across code/: Run black formatting, flake8 cleanup, remove dead code (specific deliverables: all.py files formatted with black, flake8 passes)
- [ ] T054 Run quickstart.md validation and document any gaps
- [ ] T055 [P] Create metadata.yaml with dataset versions, commit hashes, timestamps (data/metadata.yaml)
- [ ] T056 [P] Implement checksum verification for all files under data/ (data/checksums.py)
- [ ] T057a [P] Document separate server execution requirement for experiment runtime in docs/architecture.md (plan.md Compute Feasibility Decision constraint)
- [ ] T058 [P] Create constraints.md documenting all constraints and assumptions in paper-ready format (specific deliverable: docs/constraints.md)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
 - **T011a/T011b/T011c (JaCoText gap)** must be resolved before proceeding with model integration tasks
 - **T009, T010 (dataset URLs)** must be verified with version capture before problem loading implementation
 - **T012 (StarCoder verification)** must be completed before LLM integration
 - **T007 (base models)** must precede T008 (database schema) - schema depends on entity definitions
 - **T006 (logging infrastructure)** must succeed T004 (environment config) - infrastructure before usage
 - **T005 (consent flow)** must succeed T004 (environment config) - config before consent
 - **T053a/T053b (data protection)** must complete BEFORE any data collection in Phase 3 per Constitution VII
 - **T057 (compatibility test)** must complete before user story implementation to verify infrastructure feasibility
- **User Stories (Phase 3+)**: Data-flow dependencies exist between stories
 - **US1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
 - **US2 (P2)**: Depends on US1 submissions being available (T019 code submission must complete first)
 - **US3 (P3)**: Depends on US2 metrics being available (T032 metric aggregation must complete first)
 - Stories can proceed in parallel ONLY if data dependencies are satisfied
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
 - T023 (JaCoText integration) depends on T011b/T011c resolution confirmation
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
 - T045/T045a/T045b (export + traceability) can run in parallel after statistical tests

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority
- **Test execution tasks (T050a/b/c, T051a/b/c, T052a/b/c) MUST run after each story's implementation completes**

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
 - T004, T009, T010, T011a, T011b, T011c, T012, T053a, T053b, T055a, T056a, T057 can run in parallel (config, dataset/model verification, data protection, checksums, compatibility)
 - T005/T006 depend on T004 completion
- Once Foundational phase completes, US1 can start independently
- US2 can start once US1 submission infrastructure is complete
- US3 can start once US2 metric infrastructure is complete
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel (T028-T031, T039-T041)
- Different user stories can be worked on in parallel by different team members IF data dependencies are satisfied
- T046/T047 marked [P] as they have no dependencies on statistical tests
- T058 marked [P] as documentation task with no dependencies

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for submission schema in tests/contract/test_submission.py"
Task: "Integration test for experiment flow with single participant in tests/integration/test_experiment_flow.py"

# Launch all foundation verification tasks together:
Task: "Verify HumanEval dataset URL and download script with commit hash/API snapshot capture "
Task: "Verify Codeforces dataset URL and download script with commit hash/API snapshot capture "
Task: "Verify StarCoder model size ≤1GB [UNRESOLVED-CLAIM: c_3b605e3d — status=not_enough_info] "
Task: "Research and document alternative Java code generation model if JaCoText unavailable"
Task: "Verify JaCoText model size ≤1GB and CPU-tractable if used"
Task: "Run Reference-Validator Agent on JaCoText citation"
Task: "Verify GitHub Actions free-tier compatibility"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
 - **Must resolve T011a/T011b/T011c (JaCoText gap)** before proceeding
 - **Must complete T053a/T053b (data protection)** before any data collection
3. Complete Phase 3: User Story 1
4. Run T050a/T051a/T052a (US1 tests)
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Run T050a/T051a/T052a → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Run T050b/T051b/T052b → Test independently → Deploy/Demo
4. Add User Story 3 → Run T050c/T051c/T052c → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (experiment interface)
 - Developer B: User Story 2 (quality assessment) - waits for US1 submissions
 - Developer C: User Story 3 (statistical analysis) - waits for US2 metrics
3. Stories complete and integrate independently
4. Each developer runs their story's test tasks immediately after implementation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **CRITICAL**: T011a/T011b/T011c (JaCoText gap) must be RESOLVED (not just documented) before model integration tasks proceed
- **CRITICAL**: All dataset/model URLs must be verified with version capture and documented in data/metadata.yaml
- **CRITICAL**: All tasks MUST run on GitHub Actions free-tier (2 CPU, 7 GB RAM, 14 GB disk, NO GPU, ≤6 h)
- **CRITICAL**: US2 depends on US1 submissions; US3 depends on US2 metrics - data-flow ordering must be respected
- **CRITICAL**: T023 (JaCoText) and T024 (StarCoder) are NOT parallel-safe - must wait for T011a/T011b/T011c and T012 resolution
- **CRITICAL**: Constitution Principle I (seed pinning), III (checksums to state), V (timestamp updates), VII (secure deletion) have dedicated tasks
- **CRITICAL**: FR-001 (≥95% load rate), FR-011 (sensitivity analysis), SC-004 (error rate ≤0.05) have verification tasks
- **CRITICAL**: Edge cases from spec all have corresponding tasks (T033, T034, T035, T046, T047)
- **CRITICAL**: T053a/T053b moved to Phase 2 - data protection MUST complete before data collection
- **CRITICAL**: T055a/T056a are Constitution compliance tasks, not US3-specific
- **CRITICAL**: T057 moved to Phase 2 - infrastructure feasibility must be verified before implementation
- **CRITICAL**: T050a/b/c, T051a/b/c, T052a/b/c run after each US checkpoint, not Phase 6
- **CRITICAL**: T046/T047 marked [P] - parallel-safe edge case handlers
- **CRITICAL**: T058 marked [P] - documentation task with no dependencies
- **CRITICAL**: T045/T045a/T045b implement traceability per Constitution IV with explicit validation
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence