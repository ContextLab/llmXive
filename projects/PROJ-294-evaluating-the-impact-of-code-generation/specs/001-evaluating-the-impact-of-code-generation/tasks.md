# Tasks: Evaluating the Impact of Code Generation Models on Code Testability

**Input**: Design documents from `/specs/001-evaluating-the-impact-of-code-generation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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

- [X] T001a [P] Create directory structure: `projects/PROJ-294-evaluating-the-impact-of-code-generation/` with subdirectories `code/`, `data/`, `state/`, `results/`, `tests/`, `docs/`. (FR-001, Plan: Project Structure)
- [X] T001b [P] Create `__init__.py` files in `code/`, `tests/`, `tests/unit/`, `tests/integration/`. (Plan: Project Structure)
- [X] T002 Initialize a Python project with pinned dependencies in `code/requirements.txt`. (FR-007, Plan: Dependencies)
- [X] T003 [P] Configure linting (flake8/black) and formatting tools. (Plan: Testing)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup logging infrastructure in `code/utils.py` with timestamp and task ID tracking (FR-007). (FR-007)
- [X] T005 Implement SHA256 checksum utility in `code/utils.py` for dataset and artifact verification (FR-001, FR-011). (FR-001, FR-011)
- [X] T005b [US1] **Internal Citation Validator Implementation**: Implement `code/validate_citations.py` as an internal module to fulfill the "Reference-Validator Agent" requirement from the Plan (Constitution Principle II). **Re-architecture Note**: The Plan mentions an external "Reference-Validator Agent", but to ensure executability without undefined external dependencies, this task implements the validation logic internally using **Python standard library only** (`urllib`, `difflib`, `json`, `yaml`). **Logic**: Parse `state/citations.yaml`, fetch metadata from URLs, compute Jaccard similarity between title tokens. **Threshold**: Flag as invalid if similarity < 0.7. **Output**: `state/validation_report.yaml`. **Constraint**: Must NOT depend on external packages; do not install any `reference-validator` package. (FR-010, Constitution Principle II)
- [X] T006 [US1] **Citation Validation Gate**: Implement `code/run_citation_gate.py` as the internal CLI entry point to invoke the internal `code/validate_citations.py` module. **CLI Args**: `--input state/citations.yaml --output state/validation_report.yaml`. **Logic**: Call the internal module. **Constraint**: If any citation is invalid (similarity < 0.7), log the error and raise `SystemExit(1)`. **Dependency**: T005b. This task explicitly defines the "Agent" as an internal script, resolving the undefined external artifact concern. (FR-010, Plan: Pipeline Execution Order Step 1)
- [X] T007 [US1] **Pipeline Gate**: Implement `code/run_pipeline_gate.py` as the entry point script to invoke `python -m code.run_citation_gate`. **Logic**: Must capture the exit code; if non-zero, log the specific validation failure reason to `logs/pipeline_gate.log` and then raise `SystemExit(1)` to abort the pipeline immediately. **Dependency**: T006. (Plan: Pipeline Execution Order Step 1)
- [X] T008 Create data directory structure: `data/raw/`, `data/generated/`, `data/analysis/`. (Plan: Project Structure)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Paired Analysis Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download HumanEval, generate LLM code, compute metrics (Complexity, Halstead, Coverage), and produce paired JSON dataset.

**Independent Test**: Run the pipeline on a local copy of HumanEval. Verify that `data/analysis/metrics.json` contains `cyclomatic_complexity`, `halstead_volume`, `branch_coverage_pct`, and `pass_rate` for every valid pair, with at least 40 valid samples.

### Implementation for User Story 1

- [X] T010 [US1] Implement `code/download_data.py` to download HumanEval from HuggingFace (`openai_humaneval`) using `revision="main"` to ensure deterministic versioning. Use `streaming=True` to process the full dataset without loading it into RAM. **Constraint**: Must NOT fall back to synthetic data; must raise a `RuntimeError` with a clear message "Failed to download verified real source" if the download fails after max retries. **Output**: Save raw data to `data/raw/humaneval.parquet` and compute SHA256. **Dependency**: T007. (FR-001, FR-011, Plan: Large real datasets: STREAM the real data)
- [X] T010b [US1] **Sampling Configuration**: Implement logic in `code/download_data.py` to generate `state/sampling_config.yaml` containing the exact stratified sampling parameters (quartile boundaries, target count per quartile) derived from the full HumanEval dataset pass-rates. **Dependency**: T010. (Plan: Sampling Strategy)
- [X] T010c [US1] **Quartile Computation**: Implement logic in `code/download_data.py` to compute the pass-rate quartiles from the full HumanEval dataset (streamed) to define the stratification boundaries. **Output**: Append quartile boundaries to `state/sampling_config.yaml`. **Dependency**: T010. (Plan: Pipeline Execution Order Step 3)
- [X] T011 [US1] Implement stratified sampling logic in `code/download_data.py` to select a representative subset of tasks based on human pass-rate quartiles. **Dependency**: T010, T010b, T010c. **Includes assertion**: Verify the final selected subset distribution matches the stratified configuration in `state/sampling_config.yaml`. **Output**: Save the filtered subset to `data/raw/sampled_subset.json`. **Constraint**: This subset is the SINGLE SOURCE OF TRUTH for all subsequent generation and analysis tasks. (Plan: Sampling Strategy)
- [X] T012 [US1] Implement `code/generate_code.py` to load `Salesforce/codegen-350M-mono` on CPU and generate code for the tasks in `data/raw/sampled_subset.json`. **Constraint**: Must implement **-retry logic with exponential backoff** as mandated by FR-002. **Output**: Save generated code to `data/generated/codegen_samples.json`. **Dependency**: T011. (FR-002)
- [X] T013 [US1] Implement error handling in `code/generate_code.py` to log failures to `errors.log` and mark samples as missing (Edge Cases). (FR-002)
- [X] T028 [US1] **Sensitivity Generation (7B)**: Implement logic in `code/generate_code.py` to call HuggingFace Inference API for `CodeLlama-7B` for the **SAME task IDs** as in T012 (not disjoint) to enable paired statistical comparison. **Trigger**: Run only if API is available (check via `requests` ping to a known endpoint). **Constraint**: If API is unavailable, log a warning, set `source_type: null` for these samples, and **continue** (do not raise SystemExit). **Output**: Save to `data/generated/sensitivity_samples.json`. **Dependency**: T011. (FR-009, Plan: Sensitivity Analysis, Data Model Traceability)
- [X] T014a [US1] **Metric Extraction (Static)**: Implement `code/analyze_metrics.py` to run `radon cc --json` and `radon hal --json` on all samples (Human, CodeGen, Sensitivity) from `data/generated/` and `data/raw/` (Human reference). **Constraint**: Must operate ONLY on the tasks present in `data/raw/sampled_subset.json`. **Output**: Intermediate JSON with `cyclomatic_complexity`, `halstead_volume`, `halstead_components`. **Dependency**: T012, T028. (FR-003)
- [X] T014b [US1] **Metric Processing**: Implement logic in `code/analyze_metrics.py` to parse `radon` output, map `cc` to `cyclomatic_complexity`, and calculate `halstead_volume` from `hal` components. **Constraint**: Store all extracted Halstead components. **Dependency**: T014a. (FR-003)
- [X] T015 [US1] Implement logic in `code/analyze_metrics.py` to execute `pytest` against the HumanEval test suite for each sample and record the binary `pass_rate` (1 = all tests passed, 0 = any failure) per sample. **Constraint**: Operate ONLY on the tasks in `data/raw/sampled_subset.json`. **Output**: Intermediate JSON with `pass_rate`. **Dependency**: T014a. (FR-005)
- [X] T015b [US1] **Pairing Logic**: Implement logic in `code/analyze_metrics.py` to explicitly link `pass_rate` records to the `task_id` and `source_type` in a paired structure. **Constraint**: Ensure the data structure supports paired analysis (e.g., dictionary keyed by `task_id`). **Dependency**: T015. (FR-005, Plan: Paired Statistical Design)
- [X] T016 [US1] **Coverage Extraction**: Implement logic in `code/analyze_metrics.py` to execute `pytest --cov` for `branch_coverage_pct` on all samples. **Constraint**: Operate ONLY on the tasks in `data/raw/sampled_subset.json`. **Output**: Intermediate JSON with `branch_coverage_pct`. **Dependency**: T015. (FR-003, Plan: Testability Evaluation)
- [X] T045 [US1] **Sensitivity Analysis Update**: Implement logic in `code/analyze_metrics.py` to append sensitivity results (from T028) to the canonical intermediate structure. **Constraint**: Must verify that the appended rows include the correct `source_type` mapping. **Dependency**: T014a, T014b, T015, T016, T028. (Plan: Data Model Traceability)
- [X] T042 [US1] **Pairwise Exclusion Gate**: Implement logic in `code/analyze_metrics.py` to identify all task IDs where *either* the human reference OR the LLM sample has `null` coverage. **Action**: Write the list of excluded pairs to `logs/pairwise_exclusions.log`. **Constraint**: If the number of excluded pairs exceeds a non-negligible proportion of the total (SC-003), log a warning and raise `SystemExit(1)` to halt the pipeline **before** aggregation. **Dependency**: T014a, T014b, T015, T015b, T016, T045. (FR-003, FR-004, Plan: Pipeline Execution Order Step 6, SC-003)
- [X] T017 [US1] Implement aggregation in `code/analyze_metrics.py` to produce `data/analysis/metrics.json` with all required fields. **Dependencies**: T042, T014a, T014b, T015, T015b, T016, T045. **Schema**: Must contain `task_id`, `source_type`, `cyclomatic_complexity`, `halstead_volume`, `branch_coverage_pct`, and `pass_rate`. **Constraint**: Verify no record has `null` for `cyclomatic_complexity` OR `halstead_volume`. **Note**: This task aggregates the complete dataset ONLY AFTER T042 passes. (US-1 Independent Test, SC-003)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (including sensitivity data merged into `metrics.json`)

---

## Phase 4: User Story 2 - Statistical Comparison and Hypothesis Testing (Priority: P2)

**Goal**: Perform Wilcoxon, McNemar, and Permutation tests, and Power Analysis (A Priori/Post-Hoc) on the paired dataset.

**Independent Test**: Feed mock paired datasets; verify p-values are calculated correctly and power analysis reports required n ≥ 38 and achieved power ≥ 0.8.

### Implementation for User Story 2

- [X] T020 [US2] Implement `code/statistical_tests.py` with Wilcoxon Signed-Rank test for continuous metrics: **Cyclomatic Complexity and Halstead Volume ONLY**. **Parameters**: Use a **two-tailed** test with `alpha=0.05`. **Dependencies**: T017. (FR-004)
- [X] T021 [US2] Implement `code/statistical_tests.py` with McNemar's test for binary pass-rate. **Parameters**: Use `alpha=0.05`. **Dependencies**: T017. (FR-004, Plan: Complexity Tracking)
- [X] T040 [US2] Implement `code/statistical_tests.py` with Permutation Test specifically for paired branch coverage data. **Dependencies**: T017, T042. (FR-004)
- [X] T023 [US2] Implement A Priori Power Analysis in `code/statistical_tests.py` (d=0.5, α=0.05, power≥0.8) to validate sample size. **Dependencies**: T017, T042. (FR-008)
- [X] T024 [US2] Implement Post-Hoc Power Analysis in `code/statistical_tests.py` based on observed effect sizes. **Dependencies**: T020, T021, T040. (FR-008)
- [X] T046 [US2] **Success Criteria Validation**: Implement logic in `code/statistical_tests.py` to evaluate the results against Success Criteria **SC-002** (Statistical Significance) and **SC-003** (Coverage Integrity) and generate a `state/validation_results.yaml` file with boolean PASS/FAIL status for each criterion. **Dependencies**: T020, T021, T040, T024. (FR-004, Spec: Success Criteria SC-002, SC-003)
- [X] T026 [US2] Write unit tests for statistical functions using mock data with known p-values (tests/unit/test_statistics.py). (Plan: Testing)
- [X] T027 [US2] Write integration test verifying the full statistical report generation from `metrics.json` (tests/integration/test_stats_pipeline.py). (Plan: Testing)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization, Reporting, and Sensitivity Analysis (Priority: P3)

**Goal**: Generate automated Markdown report with figures, and perform sensitivity analysis using CodeLlama models.

**Independent Test**: Verify `results_report.md` contains all figures, tables, and sensitivity analysis results; verify API fallback logic works.

### Implementation for User Story 3

- [X] T030 [US3] Implement `code/report_generator.py` to create histograms and boxplots using `matplotlib` for all continuous metrics. **Constraint**: Ensure `results/figures/` directory exists (create if missing) before writing files. (FR-006)
- [X] T031 [US3] Implement `code/report_generator.py` with Jinja2 template to compile `results_report.md` including figures, tables, and power analysis. **Constraint**: The template must explicitly check `source_type` for "codellama-7b" and "codellama-3b" and render them with distinct colors/labels. **Dependency**: T030, T017. (FR-006, Plan: Data Model Traceability)
- [X] T031b [US3] **Sensitivity Visualization Verification**: Implement logic in `code/report_generator.py` to verify that sensitivity data (7B vs 3B) is correctly rendered in the report with distinct labels and that the `source_type` mapping matches the data in `metrics.json`. **Dependency**: T031, T017. (FR-006, Plan: Data Model Traceability)
- [X] T032 [US3] Implement logic to include sensitivity analysis comparison in the final report. **Dependencies**: T017, T023, T024. (FR-006)
- [X] T033 [US3] Write unit tests for `code/report_generator.py` to verify figure generation and template rendering (tests/unit/test_report.py). (Plan: Testing)
- [X] T034 [US3] Write integration test for the full pipeline from `metrics.json` to `results_report.md` (tests/integration/test_full_pipeline.py). (Plan: Testing)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T035a [P] **Documentation**: Update `README.md` with setup instructions, usage examples, and contribution guidelines. (Plan: Documentation)
- [X] T035b [P] **Documentation**: Generate API documentation for `code/` modules using Sphinx or similar. (Plan: Documentation)
- [X] T035c [P] **Documentation**: Create `docs/CONTRIBUTING.md` with coding standards and pull request process. (Plan: Documentation)
- [X] T036 Code cleanup and refactoring of `code/utils.py`. (Plan: Testing)
- [X] T037 [P] **Performance Optimization**: Implement parallel processing for `code/analyze_metrics.py` if safe. **Constraint**: Must include a verification step to ensure memory usage does not exceed the budget on CPU-only runners before execution. (Plan: Performance Goals)
- [X] T038 [P] Additional unit tests for edge cases (e.g., 0 coverage, missing LLM samples) in `tests/unit/`. (Plan: Testing)
- [X] T043 [US1] Implement robust retry logic with exponential backoff for HuggingFace dataset downloads in `code/download_data.py` to handle transient network failures. (FR-001)
- [X] T044 [US2] Add explicit handling in `code/statistical_tests.py` for zero-variance cases in the Permutation Test to prevent division-by-zero errors when coverage is `null` for all samples. (FR-004)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

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

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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