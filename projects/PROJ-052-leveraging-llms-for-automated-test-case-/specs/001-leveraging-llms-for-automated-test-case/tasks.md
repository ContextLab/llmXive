# Tasks: Leveraging LLMs for Automated Test Case Generation from Natural Language Requirements

**Input**: Design documents from `/specs/001-llm-test-generation/`
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

- [X] T001 Create project structure per implementation plan: Create directories `code/`, `specs/`, `data/`, `contracts/`, `tests/unit/`, `tests/integration/` and create empty `__init__.py` files in `code/`, `tests/`, `tests/unit/`, and `tests/integration/`.
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (pinned versions: `llama-cpp-python`, `pandas`, `scipy`, `jinja2`, `pyyaml`, `jsonschema`, `pytest`)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools
- [X] T004 Create `contracts/` directory and initialize valid YAML skeleton schema files (`dataset.schema.yaml`, `coverage.schema.yaml`, `generated_test.schema.yaml`, `analysis_result.schema.yaml`) with root keys and types defined in `data-model.md`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Implement `code/config.py` to load environment variables (sample limits, timeouts, model paths) and enforce a runtime limit.
- [X] T006 [P] Implement `code/data_loader.py` to fetch Defects4J parquet data from verified HuggingFace URL `defects4j/defects4j-parquet` file `v1.0.parquet` and cache to `data/defects4j_v1.0.parquet`.
- [ ] T006b [P] Implement checksum recording in `code/data_loader.py` to compute SHA-256 hash of `data/defects4j_v1.0.parquet` and store in project state, satisfying Constitution Principle III.
- [~] T025 [P] Implement `extract_changed_lines` in `code/data_loader.py` to parse Defects4J commit diffs from the cached parquet file and output `data/changed_lines.json` (a set of line integers per project), which is a prerequisite for T024 and T026.
- [X] T007 Implement `code/llm_generator.py` skeleton with a compact, CPU-optimized small language model loading logic using `llama-cpp-python`.
- [X] T007b [P] Implement and verify Q4_K_M quantization format and 7GB RAM constraint logic in `code/llm_generator.py` loading phase to satisfy FR-002.
- [X] T008 Implement `code/test_executor.py` skeleton with Java LTS subprocess wrappers, JaCoCo instrumentation setup, and timeout logic.
- [ ] T009 Implement `code/analyzer.py` skeleton with imports for `scipy.stats` (Shapiro-Wilk, Wilcoxon, t-test) and power analysis utilities
- [ ] T010 Implement `code/validate_schemas.py` to validate all output artifacts against `contracts/` schemas before analysis proceeds
- [ ] T011a [P] Implement `main.py` orchestration logic for hard stop when cumulative execution time exceeds a predefined threshold.
- [ ] T011b [P] Implement `main.py` orchestration logic for hard stop when sample count reaches the configured limit (FR-007).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - LLM Test Generation Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest Defects4J bug fix descriptions and generate syntactically valid JUnit test code snippets using CPU-optimized Phi-2.

**Independent Test**: Run the generation script on a fixed subset of requirements; verify output directory contains valid Java files that compile without syntax errors.

### Implementation for User Story 1

- [ ] T015 [US1] Implement `extract_bug_fix_description` in `code/data_loader.py` to parse Defects4J metadata, format as prompt per FR-001, and return the prompt string.
- [ ] T016 [US1] Implement `generate_test_code` in `code/llm_generator.py` using Phi-2 with deterministic settings (seed=42, temp=0).
- [ ] T017 [US1] Implement `validate_syntax` in `code/llm_generator.py` using `javac` to check generated `.java` files for syntax errors.
- [ ] T018 [US1] Implement error handling for ambiguous inputs: If prompt length < 20 chars, load `data/templates/default_test.java` (class `DefaultBugFixTest`) and return it as a syntactic fallback, acknowledging it may result in low coverage.
- [ ] T018b [US1] Implement logging and metric tracking in `code/llm_generator.py` to record WARNING for default template usage and count it in SC-005 metrics.
- [ ] T019 [US1] Implement memory monitoring in `code/llm_generator.py` to ensure no OOM on a limited-core runner with constrained memory.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T012 [P] [US1] Unit test in `tests/unit/test_prompting.py::test_format_bug_description_returns_valid_prompt` verifying that a bug description string is formatted into a valid prompt string.
- [ ] T013 [P] [US1] Unit test in `tests/unit/test_llm_load.py::test_phi_loads_within_7gb_ram` verifying that Phi-2 loading does not exceed 7GB RAM on CPU.
- [ ] T014 [P] [US1] Integration test in `tests/integration/test_gen_single.py::test_generate_single_valid_java` verifying that a known bug description produces a syntactically valid Java file.

**STOP**: Verify T012, T013, T014 are defined and failing before proceeding to next phases.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Coverage Measurement and Comparison (Priority: P2)

**Goal**: Execute generated tests against target source code, calculate JaCoCo coverage on changed lines, and compare against manual baselines.

**Independent Test**: Run execution pipeline on pre-generated tests; verify `coverage_metrics.csv` is produced with columns `project_id`, `test_type`, `coverage_percentage`.

### Implementation for User Story 2

- [ ] T023 [US2] Implement `compile_test` in `code/test_executor.py` using `javac` with a configurable timeout threshold.
- [ ] T023b [US2] Implement retry loop logic in `code/test_executor.py` to execute compilation/execution up to 3 attempts before marking as failed, satisfying FR-006.
- [ ] T024 [US2] Implement `run_with_jacoco` in `code/test_executor.py` to instrument target classes and execute tests, capturing line-level coverage on changed lines only (consumes `data/changed_lines.json` from T025).
- [ ] T026 [US2] Implement `calculate_coverage_ratio` in `code/test_executor.py` to calculate coverage percentage on the specific changed lines only (as defined by the Plan's Strict Pairing Unit), consuming parsed changed lines set from T025 and line-level coverage from T024.
- [ ] T027 [US2] Implement `generate_coverage_csv` in `code/test_executor.py` to write `data/coverage_metrics.csv` with `project_id`, `test_type`, `coverage_percentage`.
- [ ] T028a [US2] Implement logic to extract specific compilation error strings from `test_executor` logs or JaCoCo output for failed tests.
- [ ] T028b [US2] Implement logic to update `data/coverage_metrics.csv` row for failed tests, setting `coverage_percentage` to null, `status` to 'failed_to_compile' (per FR-003), and `error_msg` to the extracted string from T028a.
- [ ] T029a [US2] Implement `parse_assertions` in `code/test_executor.py` using regex to count assertions in generated Java files.
- [ ] T029b [US2] Implement `calculate_assertion_density` in `code/test_executor.py` to aggregate assertion counts per line of code for generated tests.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T020 [P] [US2] Unit test in `tests/unit/test_jacoco_parser.py::test_parse_jacoco_xml_returns_coverage` verifying XML parsing returns correct coverage percentages.
- [ ] T021 [P] [US2] Unit test in `tests/unit/test_timeout_retry.py::test_retry_logic_retries__times` verifying the retry loop executes exactly 3 attempts before failure.
- [ ] T022 [P] [US2] Integration test in `tests/integration/test_exec_coverage.py::test_run_with_jacoco_returns_coverage` verifying a generated test runs and returns coverage data.

**STOP**: Verify T020, T021, T022 are defined and failing before proceeding to next phases.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Reporting (Priority: P3)

**Goal**: Perform statistical tests (Wilcoxon primary, t-test sensitivity) on coverage metrics and generate final report with effect size and power analysis.

**Independent Test**: Provide `coverage_metrics.csv`; verify output includes p-value, test type, mean difference, and conclusion statement.

### Implementation for User Story 3

- [ ] T033 [US3] Implement `check_normality` in `code/analyzer.py` using Shapiro-Wilk test on coverage differences.
- [ ] T034 [US3] Implement `run_statistical_test` in `code/analyzer.py`: if normality holds (p ≥ 0.05 per Spec US-3/FR-008), run paired t-test; else run Wilcoxon signed-rank.
- [ ] T035 [US3] Implement `calculate_effect_size` in `code/analyzer.py` (Cohen's d or Rank-biserial correlation).
- [ ] T036 [US3] Implement `run_power_analysis` in `code/analyzer.py` to calculate required N and report achieved power *only* as a descriptive limitation metric, not for validation.
- [ ] T037a [US3] Implement `calculate_confidence_intervals` in `code/analyzer.py` to compute 95% confidence intervals for the mean ratio, as required by the Plan's 'Statistical Interpretation Note'.
- [ ] T037 [US3] Implement `generate_final_report` in `code/report_generator.py` to output Markdown/JSON with p-value, ratio, test type, hypothesis benchmark (40-60%) comparison (as descriptive), confidence intervals, and conclusion.
- [ ] T038 [US3] Implement logic to handle small sample sizes: If N < 30, prepend the report with a warning block: "WARNING: Sample size (N={N}) < 30. Results are exploratory.", satisfying FR-010/US-3.
- [ ] T039 [US3] Integrate `validate_schemas.py` to ensure `data/analysis_results.json` conforms to `contracts/analysis_result.schema.yaml` after T037 generates the artifact.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US3] Unit test in `tests/unit/test_normality.py::test_shapiro_wilk_returns_p_value` verifying Shapiro-Wilk returns a valid p-value.
- [ ] T031 [P] [US3] Unit test in `tests/unit/test_test_selection.py::test_select_wilcoxon_when_p_le_010` verifying that if p <= 0.10, Wilcoxon is selected.
- [ ] T032 [P] [US3] Unit test in `tests/unit/test_power_analysis.py::test_power_analysis_returns_power_value` verifying power analysis calculation returns a valid power value.

**STOP**: Verify T030, T031, T032 are defined and failing before proceeding to next phases.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040a [P] Update `README.md` with project overview, prerequisites, and quickstart instructions.
- [ ] T040b [P] Update `docs/` with API documentation for `code/` modules.
- [ ] T041 [P] Refactor `code/` to remove code duplication and improve readability.
- [ ] T042a [P] Optimize LLM inference loop in `code/llm_generator.py` for performance.
- [ ] T042b [P] Optimize JaCoCo execution in `code/test_executor.py` for performance.
- [ ] T043a [P] Add unit tests for `code/config.py` in `tests/unit/test_config.py`.
- [ ] T043b [P] Add unit tests for `code/data_loader.py` in `tests/unit/test_data_loader.py`.
- [ ] T044 [P] Security hardening (input validation for prompts) in `code/data_loader.py`.
- [ ] T045 Run quickstart.md validation.
- [ ] T046 Verify CI workflow `ci.yml` includes Reference-Validator Agent gate.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for generated tests
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 for coverage data

### Within Each User Story

- Implementation tasks MUST be written and completed BEFORE Test tasks (TDD process: write test code, run test after implementation)
- Models/Utilities before Services
- Services before Endpoints/Report Generation
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for prompt formatting in tests/unit/test_prompting.py::test_format_bug_description_returns_valid_prompt"
Task: "Unit test for llama-cpp-python CPU loading constraints in tests/unit/test_llm_load.py::test_phi2_loads_within_7gb_ram"

# Launch core implementation for User Story 1:
Task: "Implement extract_bug_fix_description in code/data_loader.py"
Task: "Implement generate_test_code in code/llm_generator.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (generate valid Java)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Coverage metrics)
4. Add User Story 3 → Test independently → Deploy/Demo (Statistical report)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Generation)
 - Developer B: User Story 2 (Execution/Coverage)
 - Developer C: User Story 3 (Analysis/Reporting)
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
- **Critical Constraint**: All tasks must run on CPU-only free-tier CI with limited cores, constrained RAM, and a 6h max runtime. No GPU, no 8-bit quantization requiring CUDA, no large model training.