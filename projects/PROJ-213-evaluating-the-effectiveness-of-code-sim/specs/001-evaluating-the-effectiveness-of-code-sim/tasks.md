# Tasks: Evaluating the Effectiveness of Code Simplification on LLM Performance

**Input**: Design documents from `/specs/001-eval-code-simplification/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/`, `data/` at repository root
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

## Phase 0: Research (Blocking Prerequisites)

**Purpose**: Dataset verification, model feasibility check, power analysis (FR-010), statistical design, constitutional compliance

**⚠️ CRITICAL**: No Phase 1 work can begin until this phase is complete

**Output Format**: research.md MUST contain:
- Section 1: Dataset version (HumanEval version number from HuggingFace)
- Section 2: Model feasibility table (RAM usage, disk space, expected runtime)
- Section 3: Power analysis table (sample size, effect size, power, minimum detectable effect, constraint_mismatch if applicable)
- Section 4: Statistical design (test names, hypotheses, correction method)
- Section 5: Constitutional compliance checklist (seeds, checksums, citation verification)

- [ ] T001 [P] Verify {{claim:c_c8fb960d}} availability and version from HuggingFace Datasets; record version in data/README.md with explicit output format: research.md Section 1 must include dataset_name, version_number, fetch_date, source_url
- [ ] T001a [P] Generate MD5/SHA256 checksums for {{claim:c_c8fb960d}} files; record checksums in state/map.json under data/raw/ with artifact_id, checksum, timestamp, hash fields (Constitution Principle III)
- [X] T002 [P] Verify StarCoder-1.3B 4-bit GGUF model source and CPU feasibility; document in research.md Section 2 with model_name, quantization_level, estimated_ram_gb, estimated_runtime_hours
- [X] T003 [P] Create power/sample-size justification in research.md Section 3 (FR-010: document minimum detectable effect forn=164 at power≥0.8; include constraint_mismatch field noting spec requires n≥200)
- [ ] T003a [P] Document power analysis constraint mismatch in research.md Section 3: spec FR-010 requires n≥200 but {{claim:c_c9ee2ab8}} (2410.12381 [UNRESOLVED-CLAIM: c_7f09d437 — status=not_enough_info], https://arxiv.org/abs/2410.12381 [UNRESOLVED-CLAIM: c_7f09d437 — status=not_enough_info]); propose mitigation (document limitation in final report, note reduced power)
- [ ] T004 [P] Document statistical design in research.md Section 4 (Wilcoxon for pass@1 and latency per spec FR-005, Bonferroni for 2 hypotheses [UNRESOLVED-CLAIM: c_1337c086 — status=not_enough_info]) <!-- FAILED: unspecified -->
- [ ] T004a [P] Implement Reference-Validator Agent verification gate for external citations in code/verify_citations.py (Constitution Principle II: verify all citations before Phase 1; fail if unreachable/mismatch)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T005 Create project structure per implementation plan: data/raw/, data/processed/, data/logs/, code/, tests/, state/
- [ ] T006 [P] Initialize Python version project with requirements.txt dependencies (datasets, transformers, llama-cpp-python, ast, scipy, matplotlib, pandas, pytest)
- [ ] T007 [P] Configure linting and formatting tools (ruff, black) with concrete deliverables: create.ruff.toml ({{claim:c_8aff098e}}), pyproject.toml with black version pin ({{claim:c_8371c8ed}}); verification: run ruff code/ --exit-zero and black --check code/ with zero warnings/errors
- [~] T008 [P] Create quickstart.md in specs/001-eval-code-simplification/ with setup instructions and CLI usage examples

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

**⚠️ ORDERING**: T009 MUST precede T012 (data models before schema validation tests)

- [ ] T009 Create base data models in code/models.py for three Key Entities: HumanEvalProblem (problem_id, prompt_code, reference_solution), SimplifiedProblem (problem_id, simplified_code), InferenceResult (problem_id, pass@1, token_count, inference_time_ms, status)
- [ ] T009a [P] Implement random seed pinning in code/ per Constitution Principle I: create code/seeds.py with RANDOM_SEED constant (e.g., 42); pin in code/download.py, code/simplify.py, code/inference.py, code/analyze.py; verify deterministic output across runs
- [ ] T010 [P] Setup environment configuration management in code/config.py (paths, timeouts, model settings)
- [ ] T011 [P] Configure error handling and logging infrastructure in code/logger.py
- [ ] T012 [P] Create schema validation tests in tests/contract/test_schemas.py and contracts/ directory structure with schema definitions (contracts/data_schemas.py: HumanEvalProblem, SimplifiedProblem, InferenceResult; contracts/metrics_schemas.py: metrics_raw.csv, metrics_simplified.csv; validation rules: required fields, types, non-negative constraints)
- [ ] T013 [P] Setup state tracking for artifact versioning in state/map.json with explicit schema: artifact_id (string), checksum (string), timestamp (ISO8601), hash (string), artifact_type (string), file_path (string)

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Benchmark Comparison (Priority: P1) 🎯 MVP

**Goal**: Execute full end-to-end pipeline on HumanEval subset with raw and AST-simplified inputs, producing paired result tables for accuracy and latency comparison

**Independent Test**: Run the "run-benchmark" command and verify two CSV files are produced (one for raw inputs, one for simplified inputs) each containing pass@1 scores and per-sample latency with matching problem IDs

**⚠️ DEPENDENCY ORDERING**:
- T018-T019 depend on T017 (simplify must complete before logging failures/semantic changes)
- T020-T022 depend on T016-T017 (download and simplify must complete before inference)
- T023 depends on T022 (orchestration must complete before result table generation)

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation
> **NOTE**: Tests CANNOT run until implementation tasks complete (remove [P] if tests depend on implementation)

- [ ] T014 [US1] Contract test for data schema validation in tests/contract/test_data_schemas.py (DEPENDS ON T009)
- [ ] T015 [US1] Integration test for full benchmark pipeline in tests/integration/test_benchmark_pipeline.py (DEPENDS ON T016-T023)

### Implementation for User Story 1

- [ ] T016 [P] [US1] Implement {{claim:c_c8fb960d}} download in code/download.py (FR-001: load from datasets.load_dataset('openai_humaneval'))
- [ ] T017 [US1] Implement AST-based simplification pipeline in code/simplify.py (FR-002: dead-code removal, boolean reduction)
- [ ] T018 [US1] Implement parse failure logging in code/simplify.py (FR-007: log to data/logs/parse_failures.log with problem_id, error_type, timestamp, stack_trace; VERIFY all fields present in output; DEPENDS ON T017)
- [ ] T019 [US1] Implement semantic change detection in code/simplify.py (FR-008: run test harness, write to data/logs/flagged_snippets.csv with problem_id, error_type, code_diff; VERIFY all fields present in output; DEPENDS ON T017)
- [ ] T020 [US1] Implement CPU-only inference runner in code/inference.py (FR-003: 4-bit StarCoder-1.3B via llama.cpp on CPU, respecting 7GB RAM limit [UNRESOLVED-CLAIM: c_416da1da — status=not_enough_info]; NO CUDA/device_map="cuda"; DEPENDS ON T016-T017)
- [ ] T021 [US1] Implement per-sample timeout enforcement in code/inference.py (FR-009: 30-second timeout, log failure with inference_time_ms=30000 [UNRESOLVED-CLAIM: c_666785a1 — status=not_enough_info]; DEPENDS ON T020)
- [ ] T022 [US1] Implement paired benchmark execution in code/main.py (orchestrate raw and simplified runs with matching problem IDs; DEPENDS ON T016-T021)
- [ ] T023 [US1] Create result table generation in code/main.py (output data/processed/results_raw.csv and data/processed/results_simplified.csv with problem_id, pass@1, token_count, inference_time_ms; DEPENDS ON T022)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Metric Logging & Token Accounting (Priority: P2)

**Goal**: Log precise token counts and wall-clock inference time for every sample to support statistical testing and visualization

**Independent Test**: After a benchmark run, open the generated log file and confirm that for every problem there is a line containing both token_count and inference_time_ms

**⚠️ DEPENDENCY**: This phase requires US1 inference output (T020 completed); CANNOT run in parallel with US1. US2 is independently testable AFTER US1 completion.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [US2] Contract test for metrics schema in tests/contract/test_metrics_schema.py (DEPENDS ON T009)
- [ ] T025 [US2] Unit test for token counting accuracy in tests/unit/test_token_counter.py (DEPENDS ON T026)

### Implementation for User Story 2

- [ ] T026 [US2] Implement token counter in code/inference.py (count tokens of input prompt for each sample; DEPENDS ON T020)
- [ ] T027 [US2] Implement wall-clock timer in code/inference.py (measure inference_time_ms for each sample; DEPENDS ON T020)
- [ ] T028 [US2] Implement metrics CSV writer in code/inference.py (FR-004: write metrics_raw.csv and metrics_simplified.csv with problem_id, pass@1, token_count, inference_time_ms; VERIFY all required columns present; DEPENDS ON T026-T027)
- [ ] T029 [US2] Add validation for non-negative integer token_count in code/inference.py
- [ ] T030 [US2] Add validation for numeric inference_time_ms in code/inference.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (US2 after US1 completion)

---

## Phase 5: User Story 3 - Statistical Analysis & Visualization (Priority: P3)

**Goal**: Generate reproducible statistical report (Wilcoxon signed-rank test for pass@1 and latency with Bonferroni correction for 2 hypotheses) and Matplotlib plot comparing accuracy and latency improvements

**Independent Test**: Run the "analyze-results" script and verify that a file analysis_report.pdf is created containing test statistics, p-values, effect sizes, and visualizations

**⚠️ DEPENDENCY**: This phase requires US1 and US2 CSV outputs (T023, T028 completed); CANNOT start until US1 and US2 complete. US3 is independently testable AFTER US1 and US2 completion.

**⚠️ SPEC ALIGNMENT NOTE**:
- SC-001/SC-002 use deferred effect-size thresholds; threshold values will be defined in research.md Section 3
- T033: Use Wilcoxon signed-rank test per spec FR-005 (plan.md uses McNemar's but spec is authoritative; plan flagged for amendment)
- T035: Use Bonferroni correction for 2 hypotheses (accuracy, latency) per spec FR-005 (token reduction is descriptive, not gating hypothesis)
- T036: Use Cohen's d per spec FR-006 (rank-biserial may be supplementary for Wilcoxon but Cohen's d is required)
- T037a: Implement SC-003 gating check per spec (verify token reduction threshold before analysis proceeds)
- T038a: Implement SC-005 under-sampled validation per spec (calculate drop rate, enforce 5% threshold [UNRESOLVED-CLAIM: c_e71916e7 — status=not_enough_info])

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T031 [US3] Contract test for report schema in tests/contract/test_report_schema.py (DEPENDS ON T033-T040)
- [ ] T032 [US3] Unit test for statistical calculations in tests/unit/test_statistical_tests.py (DEPENDS ON T033-T036)

### Implementation for User Story 3

- [ ] T033 [US3] Implement paired Wilcoxon signed-rank test for pass@1 scores in code/analyze.py (FR-005 per spec; NOTE: spec FR-005 requires Wilcoxon, plan.md uses McNemar's - follow spec, flag plan for amendment; SC-001 uses deferred threshold from research.md Section 3)
- [ ] T034 [US3] Implement paired Wilcoxon signed-rank test for inference times in code/analyze.py (FR-005 per spec; SC-002 uses deferred threshold from research.md Section 3)
- [ ] T035 [US3] Implement Bonferroni correction for 2 hypotheses (accuracy, latency) in code/analyze.py (FR-005 per spec; token reduction is descriptive, not a gating hypothesis)
- [ ] T036 [US3] Implement effect size calculation (Cohen's d) in code/analyze.py (FR-006 per spec; rank-biserial correlation may be reported supplementary for Wilcoxon but Cohen's d is required)
- [ ] T037 [US3] Implement token count ratio computation in code/analyze.py (SC-003: ratio for all paired problems; descriptive metric; uses deferred reduction threshold from research.md Section 3)
- [ ] T037a [US3] Implement SC-003 gating validation in code/analyze.py (VERIFY token reduction threshold achieved before accuracy/latency analysis proceeds per spec; if threshold not met, halt analysis and log SC-003 violation; NOTE: spec requires gating, plan's descriptive approach contradicts spec and requires amendment)
- [ ] T038 [US3] Implement drop rate calculation in code/analyze.py (SC-005: parse failures + semantic changes)
- [ ] T038a [US3] Implement SC-005 under-sampled validation in code/analyze.py (CALCULATE drop rate; if >5%, mark experiment as under-sampled in report per spec SC-005; document limitation; NOTE: plan's remediation allows proceeding but spec requires under-sampled status - spec is authoritative)
- [ ] T039 [US3] Implement Matplotlib visualization in code/analyze.py (FR-006: two side-by-side bar charts for accuracy and latency)
- [ ] T040 [US3] Implement PDF report generation in code/analyze.py (FR-006: analysis_report.pdf with test statistics, p-values, effect sizes, figures)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

**⚠️ ORDERING**: Tests (T041-T043) require implementation tasks complete; remove [P] if tests depend on implementation

- [ ] T041 [US3] Run unit tests for all modules in code/ (tests/unit/); PASS CRITERIA: pytest exit code 0, minimum 80% coverage [UNRESOLVED-CLAIM: c_622f6dc1 — status=not_enough_info], all tests pass
- [ ] T042 [US3] Run contract tests for data schemas (tests/contract/); PASS CRITERIA: pytest exit code 0, all schema validations pass
- [ ] T043 [US3] Run integration tests for full pipeline (tests/integration/); PASS CRITERIA: pytest exit code 0, end-to-end pipeline completes successfully
- [ ] T044 [P] Documentation updates in README.md with concrete sections: project overview, setup instructions, CLI usage, expected outputs, known limitations; ACCEPTANCE: all sections present, no dead links
- [ ] T045 [P] Code cleanup: ruff linting pass (zero warnings/errors); ACCEPTANCE: ruff code/ returns exit code 0
- [ ] T046 [P] Code cleanup: black formatting pass (no formatting diffs); ACCEPTANCE: black --check code/ returns exit code 0
- [ ] T047 [P] Code cleanup: no TODO/FIXME comments remaining in code/; ACCEPTANCE: grep -r "TODO\|FIXME" code/ returns no matches
- [ ] T048 [P] Verify quickstart.md validation passes; ACCEPTANCE: quickstart.md sections match README.md, CLI examples work
- [ ] T049 Run end-to-end benchmark on full HumanEval and verify output files; ACCEPTANCE: data/processed/results_raw.csv, data/processed/results_simplified.csv, data/processed/metrics_raw.csv, data/processed/metrics_simplified.csv, analysis_report.pdf all exist with correct schemas
- [ ] T050 [P] Verify analysis_report.pdf contains all required statistical tables and figures; ACCEPTANCE: PDF includes Wilcoxon test statistics, Bonferroni-corrected p-values, Cohen's d effect sizes, accuracy/latency bar charts, SC-003 gating status, SC-005 drop rate status

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Research)**: No dependencies - can start immediately
- **Phase 1 (Setup)**: Depends on Phase 0 completion - BLOCKS all user stories
- **Phase 2 (Foundational)**: Depends on Phase 1 completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
 - User Story 1 (Phase 3): Can start after Phase 2 - No dependencies on other stories
 - User Story 2 (Phase 4): Requires US1 inference output (T020); CANNOT run in parallel with US1
 - User Story 3 (Phase 5): Requires US1 and US2 CSV outputs (T023, T028); CANNOT run in parallel with US1 or US2
- **Phase 6 (Polish)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
 - Requires T016 (download) before T017 (simplify) before T020 (inference)
 - T018-T019 depend on T017
 - T020-T022 depend on T016-T017
- **User Story 2 (P2)**: Requires US1 inference output (T020) - CANNOT run in parallel with US1
 - Requires T020 (inference) before T026-T030 (metrics logging)
 - Independently testable AFTER US1 completion
- **User Story 3 (P3)**: Requires US1 and US2 CSV outputs (T023, T028) - CANNOT run in parallel with US1 or US2
 - Requires T023, T028 (result CSVs) before T033-T040 (analysis)
 - Independently testable AFTER US1 and US2 completion
 - T037a (SC-003 gating) and T038a (SC-005 validation) are mandatory per spec

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Phase 0 tasks marked [P] can run in parallel
- All Phase 1 tasks marked [P] can run in parallel
- All Phase 2 tasks marked [P] can run in parallel (within Phase 2)
- All tests for a user story marked [P] can run in parallel
- **IMPORTANT**: User stories CANNOT run in parallel due to data dependencies (US1→US2→US3)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data schema validation in tests/contract/test_data_schemas.py"
Task: "Integration test for full benchmark pipeline in tests/integration/test_benchmark_pipeline.py"

# Launch foundational tasks for User Story 1:
Task: "Implement {{claim:c_c8fb960d}} download in code/download.py"
Task: "Implement AST-based simplification pipeline in code/simplify.py"
Task: "Implement CPU-only inference runner in code/inference.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Research
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Phase 0-2 → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Sequential Team Strategy

Due to data dependencies, sequential execution is required:

1. Team completes Phase 0-2 together
2. Once Foundational is done:
 - Developer A: User Story 1 (benchmark pipeline) → BLOCKS US2/US3
 - After US1 complete: Developer B: User Story 2 (metrics logging) → BLOCKS US3
 - After US2 complete: Developer C: User Story 3 (statistical analysis)
3. Stories complete and integrate sequentially

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable (after dependencies met)
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Feasibility Check**: StarCoder-1.3B 4-bit via llama.cpp on CPU fits within 7GB RAM limit [UNRESOLVED-CLAIM: c_416da1da — status=not_enough_info]; HumanEval (the complete problem set) can be processed within maximum job duration limit
- **Avoid**: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Path**: T016 → T017 → T020 → T023 → T028 → T033-T040 (download → simplify → infer → results → metrics → report)
- **Statistical Test Clarification**: Wilcoxon signed-rank test for pass@1 (per spec FR-005; plan.md uses McNemar's - follow spec, flag plan for amendment); Wilcoxon for continuous latency metrics; Bonferroni for 2 hypotheses [UNRESOLVED-CLAIM: c_1337c086 — status=not_enough_info] (accuracy, latency)
- **Token Reduction Clarification**: SC-003 is GATING per spec - analysis proceeds ONLY IF token reduction threshold achieved (T037a implements gating check); plan's descriptive approach contradicts spec and requires amendment
- **Effect Size Clarification**: Cohen's d required per spec FR-006; rank-biserial may be supplementary for Wilcoxon
- **Drop Rate Clarification**: SC-005 requires experiment marked under-sampled if >5% drop rate (T038a implements threshold validation); plan's remediation allows proceeding but spec is authoritative
- **Constitutional Compliance**: Random seeds pinned (T009a), dataset checksums recorded (T001a), citation verification gate (T004a)
- **Plan Amendment Flags**:
 1. plan.md uses McNemar's for pass@1 and 3 hypotheses for Bonferroni; spec FR-005 requires Wilcoxon and 2 hypotheses - tasks follow spec, plan flagged for amendment
 2. plan.md SC-003 describes token reduction as descriptive; spec SC-003 requires gating - tasks follow spec, plan flagged for amendment
 3. plan.md SC-005 allows proceeding with >5% drop rate; spec SC-005 requires under-sampled status - tasks follow spec, plan flagged for amendment
 4. plan.md uses 164 problems [UNRESOLVED-CLAIM: c_56207708 — status=not_enough_info]; spec FR-010 requires n≥200 - tasks document constraint mismatch, plan flagged for amendment