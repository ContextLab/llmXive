---
description: "Task list template for feature implementation"
---

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
- [X] T002 Initialize Python project with `requirements.txt` (pinned versions: `llama-cpp-python`, `pandas`, `scipy`, `jinja2`, `pyyaml`, `jsonschema`, `pytest`)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools
- [X] T004 Create `contracts/` directory and initialize valid YAML skeleton schema files (`dataset.schema.yaml`, `coverage.schema.yaml`, `generated_test.schema.yaml`, `analysis_result.schema.yaml`). If `data-model.md` is missing, derive root keys and types from the 'Key Entities' and 'Data Hygiene' sections of `plan.md`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. This phase includes data sourcing, strict pairing logic, and orchestration limits.

- [X] T005 Implement `code/config.py` to load environment variables (sample limits, timeouts, model paths, retry limits) and enforce a runtime limit.
- [X] T006 [P] Implement `code/data_loader.py` to fetch Defects4J dataset using `datasets.load_dataset("defects4j/defects4j", split="train", streaming=True)`. Implement robust `try/except` block that raises `DataFetchError` if stream fails (no synthetic fallbacks). Implement chunked processing logic to support datasets exceeding RAM.
- [X] T006b [P] Implement `compute_file_sha` in `code/data_loader.py` to download the raw dataset file to `data/` and compute the SHA-256 hash on the file bytes to ensure integrity per Constitution Principle III. **Verification**: Add unit test in `tests/unit/test_data_loader.py::test_compute_file_sha_returns_valid_hash` verifying the output matches a known input file.
- [X] T006c [P] Implement `update_state_checksum` in `code/main.py` to store the computed cryptographic hash in the project state YAML, satisfying Constitution Principle III. **Deliverable**: Write the checksum to `state/projects/PROJ-052-leveraging-llms-for-automated-test-case-.yaml` under the key `artifact_hashes.data_loader`.
- [X] T048 [R] [US1/US2] **Strict Pairing Validation**: Implement `validate_manual_baseline_existence` in `code/data_loader.py`. Function signature: `def validate_manual_baseline_existence(bug_id: str) -> bool`. Logic: Query Defects4J metadata for a specific failing test method ID. If missing, return `False`. **Integration**: Modify `main.py` loop to skip samples where this returns `False`. **Logging**: Ensure `data/exclusion_log.json` is updated with key `missing_manual_baseline` and the `bug_id`. **Rationale**: Moves the exclusion logic from Phase R to Phase 2 to ensure T051 can correctly filter samples.
- [X] T025 [P] Implement `extract_changed_lines` in `code/data_loader.py` to parse Defects4J commit diffs from the streamed data and output `data/changed_lines.json` (a set of line integers per project), which is a prerequisite for T024 and T026. Output schema: `{"project_id": {"bug_id": [line1, line2,...]}}`.
- [X] T015a [P] [US1] **Issue Description Mapping**: Implement `map_issue_description` in `code/data_loader.py`. Logic: Extract the 'issue description' field from the Defects4J stream, validate it is non-empty and > 20 chars, and raise `ValidationError` if missing. This task explicitly bridges the gap between dataset fetch and prompt generation. **Output**: Returns the validated prompt string. **Verification**: Unit test verifying `map_issue_description` raises on missing fields.
- [X] T007 Implement `code/llm_generator.py` skeleton with a compact, CPU-optimized small language model loading logic using `llama-cpp-python`.
- [X] T007b [P] Implement and verify Q4_K_M quantization format and 7GB RAM constraint logic in `code/llm_generator.py` loading phase to satisfy FR-002. Include memory monitoring using `psutil` to raise `MemoryExceededError` if RAM > 7GB.
- [X] T008 Implement `code/test_executor.py` skeleton with Java LTS subprocess wrappers, JaCoCo instrumentation setup, and timeout logic.
- [X] T009 [P] Implement `code/analyzer.py` skeleton with imports for `scipy.stats` (Shapiro-Wilk, Wilcoxon, t-test) and power analysis utilities.
- [X] T010 Implement `code/validate_schemas.py` to validate all output artifacts against `contracts/` schemas before analysis proceeds
- [X] T011a [P] Implement `check_runtime_limit()` in `code/main.py` that raises `RuntimeLimitExceeded` if elapsed time > configured limit (FR-007). Verify `main.py` raises this exception when limit exceeded.
- [X] T011b [P] Implement `check_sample_limit()` in `code/main.py` that raises `SampleLimitExceeded` if processed count > configured limit (FR-007). Verify `main.py` raises this exception when limit exceeded.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - LLM Test Generation Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest Defects4J bug fix descriptions and generate syntactically valid JUnit test code snippets using CPU-optimized Phi-2.

**Independent Test**: Run the generation script on a fixed subset of requirements; verify output directory contains valid Java files that compile without syntax errors.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️
> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation (TDD)

- [X] T012 [P] [US1] Unit test in `tests/unit/test_prompting.py::test_format_bug_description_returns_valid_prompt` verifying that a bug description string is formatted into a valid prompt string.
- [X] T013 [P] [US1] Unit test in `tests/unit/test_llm_load.py::test_phi_loads_within_7gb_ram` verifying that Phi-2 loading does not exceed 7GB RAM on CPU.
- [X] T014 [P] [US1] Integration test in `tests/integration/test_gen_single.py::test_generate_single_valid_java` verifying that a known bug description produces a syntactically valid Java file.

### Implementation for User Story 1

- [X] T015 [US1] Implement `extract_bug_fix_description` in `code/data_loader.py` to parse Defects4J metadata, format as prompt per FR-001, and return the prompt string. Include security hardening (input validation for prompts) here. **Depends on T015a**.
- [X] T018 [US1] **Ambiguous Prompt Handling Wrapper**: Implement `handle_ambiguous_prompt` in `code/data_loader.py`. Logic: If prompt length < 20 chars or validation fails, retry generation up to 3 times with a deterministic template. If all retries fail, **generate a syntactically valid minimal JUnit test class** (e.g., an empty test class with a single `@Test` method containing a placeholder `assertTrue(true)`) instead of dropping the sample. Log a WARNING to `data/metrics.json` with key `ambiguous_prompt_count` and `status: fallback_generated`. **Depends on T015a**.
- [X] T016 [US1] Implement `generate_test_code` in `code/llm_generator.py` to generate JUnit test code using Phi-2 with deterministic settings (seed=42, temperature=0).
- [X] T017 [US1] Implement `validate_syntax` in `code/llm_generator.py` using `javac` to check generated `.java` files for syntax errors.

**STOP**: Verify T012, T013, T014 are defined and failing before proceeding to next phases.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Coverage Measurement and Comparison (Priority: P2)

**Goal**: Execute generated tests against target source code, calculate JaCoCo coverage on changed lines, and compare against manual baselines.

**Independent Test**: Run execution pipeline on pre-generated tests; verify `coverage_metrics.csv` is produced with columns `project_id`, `test_type`, `coverage_percentage`.

### Implementation for User Story 2

- [X] T023 [US2] Implement `compile_test` in `code/test_executor.py` using `javac` with a configurable timeout threshold.
- [X] T023b [US2] Implement retry loop logic in `code/test_executor.py` to execute compilation/execution up to `config.RETRY_LIMIT` attempts (read from `config.py`, default 3) before marking as failed, satisfying FR-006. Implement `retry_compile()` in `code/test_executor.py` that attempts compilation multiple times with a short delay before raising `CompilationFailedError`. **Verification**: Add unit test in `tests/unit/test_timeout_retry.py::test_retry_logic_retries__times` verifying the loop executes exactly `RETRY_LIMIT` attempts.
- [X] T024 [US2] Implement `run_with_jacoco` in `code/test_executor.py` to instrument target classes and execute tests, capturing line-level coverage on changed lines only (consumes `data/changed_lines.json` from T025). **Artifact**: Produces `data/jacoco_coverage.xml`.
- [X] T026 [US2] Implement `calculate_coverage_ratio` in `code/test_executor.py` to calculate coverage percentage on the specific changed lines only (as defined by the Plan's Strict Pairing Unit), consuming parsed changed lines set from T025 and line-level coverage from T024.
- [X] T028a [US2] Implement `extract_compilation_error` in `code/test_executor.py` using regex pattern `r'(?:error:|Error:).*'` to extract specific compilation error strings from logs or JaCoCo output for failed tests. Return a list of error strings.
- [X] T028b [US2] Implement `update_csv_for_failed_test` in `code/test_executor.py` to update the in-memory record for failed tests (to be written by T027a), setting `coverage_percentage` to null, `status` to 'failed_to_compile' (per FR-003), and `error_msg` to the extracted string from T028a. **For successful tests**, set `status` to 'passed'. **Depends on T028a**.
- [X] T029a [US2] **Assertion Counting**: Implement `count_assertions` in `code/test_executor.py` using a Java AST parser (e.g., via `javap` or `tree-sitter-java`) to accurately count assertion statements. **Exclusion**: Explicitly exclude `@Test` annotations from the count. **Deliverable**: Return the integer count. **Verification**: Add unit test in `tests/unit/test_test_executor.py::test_count_assertions_returns_correct_count` verifying the AST parser matches expected assertion patterns and ignores annotations.
- [X] T029b [US2] Implement `calculate_assertion_density` in `code/test_executor.py` to aggregate assertion counts per line of code for generated tests. **Consume** the count from T029a and divide by total lines of code. Store the result in `coverage_metrics.csv` column `assertion_density`. **Depends on T029a**.
- [X] T027a [US2] Implement `collect_coverage_records` in `code/test_executor.py` to aggregate all in-memory records (from T026, T028b, T029b) into a single pandas DataFrame. **Deliverable**: Return the DataFrame ready for writing. **Depends on T026, T028b, T029b**.
- [X] T027b [US2] Implement `write_coverage_csv` in `code/test_executor.py` to write the aggregated DataFrame from T027a to `data/coverage_metrics.csv`. **Deliverable**: Write the DataFrame with columns `project_id`, `test_type`, `coverage_percentage`, `status`, `assertion_density`. **Depends on T027a**.
- [X] T051 [R] [US2/US3] Implement `filter_pairable_samples` in `code/analyzer.py` (or `code/data_loader.py` if data flow requires) that reads `data/coverage_metrics.csv` and `data/exclusion_log.json` (produced by T048). It must identify samples where a specific manual test method is known to fail on the buggy version. Samples without this specific manual baseline (flagged in T048) must be flagged as `unpaired` and excluded from the `paired_wilcoxon` calculation. **Crucially, this task must log the count of excluded samples to `data/exclusion_log.json`** with keys `total_samples`, `excluded_count`, and `pairable_count`. This log is required for T053 in Phase 5.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Unit test in `tests/unit/test_jacoco_parser.py::test_parse_jacoco_xml_returns_coverage` verifying XML parsing returns correct coverage percentages.
- [X] T021 [P] [US2] Unit test in `tests/unit/test_timeout_retry.py::test_retry_logic_retries__times` verifying the retry loop executes exactly 3 attempts before failure.
- [X] T022 [P] [US2] Integration test in `tests/integration/test_exec_coverage.py::test_run_with_jacoco_returns_coverage` verifying a generated test runs and returns coverage data.

**STOP**: Verify T020, T021, T022 are defined and failing before proceeding to next phases.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Reporting (Priority: P3)

**Goal**: Perform statistical tests (Wilcoxon primary, t-test sensitivity) on coverage metrics and generate final report with effect size and power analysis.

**Independent Test**: Provide `coverage_metrics.csv`; verify output includes p-value, test type, mean difference, and conclusion statement.

### Implementation for User Story 3

- [X] T033 [US3] Implement `check_normality` in `code/analyzer.py` using Shapiro-Wilk test on coverage differences.
- [X] T034 [US3] Implement `run_statistical_test` in `code/analyzer.py`: if normality holds (p > 0.10 per Plan's stricter threshold), run paired t-test; else run Wilcoxon signed-rank.
- [X] T035 [US3] Implement `calculate_effect_size` in `code/analyzer.py` (Cohen's d or Rank-biserial correlation).
- [X] T036 [US3] Implement `run_power_analysis` in `code/analyzer.py` to calculate required N and report achieved power *only* as a descriptive limitation metric, not for validation.
- [X] T037a [US3] Implement `calculate_confidence_intervals` in `code/analyzer.py` to compute confidence intervals for the mean ratio using `scipy.stats.t.interval`, as required by the Plan's 'Statistical Interpretation Note'.
- [X] T053 [R] [US3] **Exclusion Rate Reporting**: Implement `calculate_exclusion_rate` in `code/report_generator.py` to read `data/exclusion_log.json` (produced by T051 in Phase 4) and output the "Exclusion Rate" (percentage of samples dropped due to lack of specific manual baseline) and the "Achieved Statistical Power" (post-hoc) as a descriptive limitation. **Deliverable**: Calculate `exclusion_rate = excluded_count / total_samples` and append this value to `data/analysis_results.json`. **Rationale**: Reports a methodological limitation derived from the Plan's Strict Pairing logic, not a new Success Criterion. **Must precede T037**.
- [X] T047 [US3] **Report Assertion Density**: Implement `aggregate_assertion_density` in `code/report_generator.py` to read `assertion_density` from `data/coverage_metrics.csv`, calculate the mean/median, and include these values in the final report. **Deliverable**: Ensure `data/final_report.md` explicitly contains a section "Assertion Density Analysis" with the calculated metrics.
- [X] T037 [US3] Implement `generate_final_report` in `code/report_generator.py` to output `data/final_report.md` and `data/analysis_results.json` with p-value, ratio, test type, hypothesis benchmark (within a target range) comparison (as descriptive), confidence intervals, and conclusion. **Deliverable**: Read `data/analysis_results.json` (updated by T053) to retrieve `exclusion_rate`. **Logic**: If `exclusion_rate` > 0.5, prepend a "Study Limitation: High Exclusion Rate" warning. **Logic**: If `N < 30` or `power < 0.5`, prepend "WARNING: Sample size (N={N}) < 30. Results are exploratory." to `data/final_report.md` at line 1. Calculate `within_hypothesis_range` (boolean) based on ratio >= 0.4 and ratio <= 0.6, and append it to the JSON.
- [X] T038 [US3] Implement logic to handle small sample sizes: If N < 30, prepend the warning block "WARNING: Sample size (N={N}) < 30. Results are exploratory." to `data/final_report.md` at line 1, satisfying FR-010/US-3. (Note: Logic merged into T037).
- [X] T039 [US3] Integrate `validate_schemas.py` to ensure `data/analysis_results.json` conforms to `contracts/analysis_result.schema.yaml` after T037 and T053 have generated the artifact. **Action**: Raise an error if validation fails.
- [X] T061 [R] [US3] **Post-Hoc Power Analysis**: Implement `calculate_sample_power_sensitivity` in `code/analyzer.py` to strictly perform the post-hoc power analysis mandated by FR-010. **Constraint**: Do NOT calculate Minimum Detectable Effect Size (MDES). **Deliverable**: Append the achieved power value to `data/analysis_results.json` under key `achieved_power`. **Traceability**: Maps to FR-010 and SC-003. **Rationale**: Provides a quantitative bound on the study's sensitivity, framing the "exploratory" nature of the results. **Depends on T035, T037**.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T030 [P] [US3] Unit test in `tests/unit/test_normality.py::test_shapiro_wilk_returns_p_value` verifying Shapiro-Wilk returns a valid p-value.
- [X] T031 [P] [US3] Unit test in `tests/unit/test_test_selection.py::test_select_wilcoxon_when_p_le_010` verifying that if p <= 0.10, Wilcoxon is selected.
- [X] T032 [P] [US3] Unit test in `tests/unit/test_power_analysis.py::test_power_analysis_returns_power_value` verifying power analysis calculation returns a valid power value.

**STOP**: Verify T030, T031, T032 are defined and failing before proceeding to next phases.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040a [P] Update `README.md` with project overview, prerequisites, and quickstart instructions.
- [X] T040b [P] Update `docs/` with API documentation for `code/` modules. Run `pydoc -w code/` to generate `docs/api.md` and verify it contains docstrings for all public functions.
- [ ] T041 [P] Refactor `code/` to remove code duplication. **Specific**: Extract common retry logic from `test_executor.py` and `llm_generator.py` into `code/utils/retry.py`. **Verification**: Run `ruff check code/` and ensure no duplicate function warnings exist. <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested -->
- [X] T042a [P] Optimize LLM inference loop in `code/llm_generator.py` for performance. **Deliverable**: Implement batched inference. **Verification**: Verify inference time per sample < 10 seconds. <!-- ATOMIZE: requested -->
- [X] T042b [P] Optimize JaCoCo execution in `code/test_executor.py` for performance.
- [X] T043a [P] Add unit tests for `code/config.py` in `tests/unit/test_config.py`.
- [X] T043b [P] Add unit tests for `code/data_loader.py` in `tests/unit/test_data_loader.py`.
- [ ] T045 [P] Run quickstart.md validation. **Command**: Execute `bash scripts/validate_quickstart.sh` and verify it exits with code 0 and produces `data/quickstart_validation_report.txt` containing 'PASS'.
- [X] T046a [P] **Create CI Workflow**: Create the `.github/workflows/ci.yml` file with the necessary structure (jobs, steps, environment) to support the Reference-Validator Agent gate. **Verification**: Verify the file exists and is valid YAML.
- [X] T046b [P] **Add Reference-Validator Gate**: Edit `.github/workflows/ci.yml` (created by T046a) to add a job step invoking the Reference-Validator Agent before the `research_complete` stage. **Verification**: Run `grep -q 'Reference-Validator' .github/workflows/ci.yml` and ensure it exits with code 0.

---

## Phase R: Revision & Gap Resolution (Addressing Analyze Findings)

**Purpose**: Resolve specific gaps identified by the analysis phase regarding data sourcing, strict pairing, and statistical rigor.

*Note: Most tasks in this phase have been moved to earlier phases to ensure core functionality. T050 and T051 are now in Phase 2 and Phase 4 respectively. T055 is now in Phase 4. T053 is now in Phase 5.*

### Implementation for Revision

- [X] T050 [R] **Data Sourcing Fix**: This task is now merged into T006 in Phase 2. Mark as Complete.
- [X] T052 [R] **Statistical Rigor Update**: This logic is now in T034 in Phase 5. Mark as Complete.
- [X] T054 [R] **Timeout & Retry Verification**: This logic is now in T023b in Phase 4. Mark as Complete.
- [X] T055 [R] **Assertion Density Implementation**: This logic is now in T029a/T029b in Phase 4. Mark as Complete.
- [X] T060 [R] [US2] **Moved**: Logic moved to T048 in Phase 2. Mark as Complete.

**Checkpoint**: All analysis gaps resolved; pipeline ready for re-run with strict data and statistical constraints.

---

## Phase R2: Final Validation & Documentation

**Purpose**: Ensure all constraints are met and documentation is complete for the research phase.

- [X] T063 [R2] **Final Data Integrity Check**: Implement `verify_data_integrity` in `code/main.py` that runs a final checksum verification on all artifacts in `data/` against the stored hashes in `state/projects/PROJ-052-leveraging-llms-for-automated-test-case-.yaml`. **Action**: Fail the pipeline if any mismatch is found. **Rationale**: Ensures data hygiene (Constitution Principle III) before any final report generation.
- [ ] T064 [R2] **Documentation of Exclusion Logic**: Update `README.md` and `docs/` to explicitly document the "Strict Pairing" exclusion criteria and the rationale for dropping samples without a specific manual baseline. **Deliverable**: Add a "Methodological Constraints" section to `README.md` explaining the exclusion rate impact.
- [ ] T065 [R2] **Reproducibility Script**: Create `scripts/reproduce_analysis.sh` that sets the random seed, loads the model, and runs the full pipeline on the same sample set used for the final report, verifying that the `analysis_results.json` hash matches the original. **Action**: Include this script in the CI workflow as a non-blocking check.

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
- **Critical Constraint**: All tasks must run on CPU-only free-tier CI with limited cores, constrained RAM, and a bounded max runtime. No GPU, no 8-bit quantization requiring CUDA, no large model training.