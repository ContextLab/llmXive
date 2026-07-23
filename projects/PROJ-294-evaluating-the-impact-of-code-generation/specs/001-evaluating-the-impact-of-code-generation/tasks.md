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

- [X] T001 Create project structure per implementation plan (`projects/PROJ-294-evaluating-the-impact-of-code-generation/`)
- [X] T002 Initialize a Python project with pinned dependencies in `code/requirements.txt`
- [X] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup logging infrastructure in `code/utils.py` with timestamp and task ID tracking (FR-007)
- [X] T005 Implement SHA256 checksum utility in `code/utils.py` for dataset and artifact verification (FR-001, FR-011)
- [X] T005b [US1] **Install Reference-Validator Agent**: Add `reference-validator` (or equivalent verified package) to `code/requirements.txt` and ensure it is installed in the virtualenv. **Constraint**: This package MUST provide a CLI entry point (e.g., `reference-validate`) that accepts `--input` and `--output` arguments. **Dependency**: T002. (Constitution Principle II, Plan: Pipeline Execution Order Step 1)
- [X] T006 [US1] **Citation Validation Gate**: Implement `code/validate_citations.py` as a wrapper to invoke the external `Reference-Validator Agent`. **CLI Args**: `--input state/citations.yaml --output state/validation_report.yaml`. **Logic**: The wrapper must call the agent (now installed via T005b) and capture its exit code. **Output Schema**: `state/citations.yaml` must contain a list of objects with keys `id`, `url`, and `title`. **Constraint**: If the agent is not found or returns non-zero, log the error and raise `SystemExit(1)`. **Dependency**: T005b. (FR-010, Plan: Pipeline Execution Order Step 1)
- [X] T007 [US1] **Pipeline Gate**: Implement `code/run_pipeline_gate.py` as the entry point script to invoke `python -m code.validate_citations`. **Logic**: Must capture the exit code; if non-zero, log the specific validation failure reason to `logs/pipeline_gate.log` and then raise `SystemExit(1)` to abort the pipeline immediately. **Dependency**: T006. (Plan: Pipeline Execution Order Step 1)
- [X] T008 Create data directory structure: `data/raw/`, `data/generated/`, `data/analysis/`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Paired Analysis Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download HumanEval, generate LLM code, compute metrics (Complexity, Halstead, Coverage), and produce paired JSON dataset.

**Independent Test**: Run the pipeline on a local copy of HumanEval. Verify that `data/analysis/metrics.json` contains `cyclomatic_complexity`, `halstead_volume`, `branch_coverage_pct`, and `pass_rate` for every valid pair, with at least 40 valid samples.

### Implementation for User Story 1

- [X] T010 [US1] Implement `code/download_data.py` to download HumanEval from HuggingFace (`openai_humaneval`) using `revision="main"` to ensure deterministic versioning. Use `streaming=True` to process the full dataset without loading it into RAM. Verify SHA256 and save to `data/raw/`. **Constraint**: Must NOT fall back to synthetic data; must raise a `RuntimeError` with a clear message "Failed to download verified real source" if the download fails after max retries. **Dependency**: T007 (execution gate must pass). (FR-001, FR-011, Plan: Large real datasets: STREAM the real data)
- [X] T010b [US1] **Sampling Configuration**: Implement logic in `code/download_data.py` to generate `state/sampling_config.yaml` containing the exact stratified sampling parameters (quartile boundaries, target count per quartile) derived from the full HumanEval dataset pass-rates. **Dependency**: T010. (Plan: Sampling Strategy)
- [X] T011 [US1] Implement stratified sampling logic in `code/download_data.py` to select a representative subset of tasks based on human pass-rate quartiles. **Dependency**: T010, T010b. **Includes assertion**: Verify the final selected subset distribution matches the stratified configuration in `state/sampling_config.yaml` (i.e., proportional representation across quartiles). **Constraint**: If T010 fails or returns insufficient data, T011 must not run. Do NOT assert a specific fixed sample size; verify the *method* was followed. (Plan: Sampling Strategy)
- [X] T012 [US1] Implement `code/generate_code.py` to load `Salesforce/codegen-350M-mono` on CPU and generate code for a set of tasks. **Constraint**: Must implement **3-retry logic with exponential backoff** as mandated by FR-002. **Dependency**: T011. (FR-002)
- [X] T013 [US1] Implement error handling in `code/generate_code.py` to log failures to `errors.log` and mark samples as missing (Edge Cases)
- [X] T028 [US1] **Sensitivity Generation (7B)**: Implement logic in `code/generate_code.py` to call HuggingFace Inference API for `CodeLlama-7B` for a subset of tasks. **Trigger**: Run only if API is available. **Constraint**: Must write `source_type: "codellama-7b"` to metadata for these samples. **Retry Logic**: Implement 3-retry logic with exponential backoff for API calls. If API fails after retries, log the error, record `source_type: null` for these specific samples, and **continue** (do not raise SystemExit). **Dependency**: T011. (FR-009, Plan: Sensitivity Analysis)
- [X] T014a [US1] **Metric Extraction (Radon Runner)**: Implement `code/analyze_metrics.py` to run `radon cc --json` and `radon hal --json` on all samples (Human, CodeGen, and Sensitivity) to extract raw metrics. **Dependency**: T012, T028, T015. (FR-003)
- [X] T014b [US1] **Metric Processing**: Implement logic in `code/analyze_metrics.py` to parse `radon` output, map `cc` to `cyclomatic_complexity`, and calculate `halstead_volume` from `hal` components (N, n, L, D, E). **Constraint**: Must **store all extracted Halstead components** (N, n, L, D, E) in the intermediate JSON for preservation (Single Source of Truth), while using only Volume for the final report. If extraction fails for a specific sample, record `null` for that metric (do not halt the script). **Dependency**: T014a. (FR-003, Constitution Principle IV)
- [X] T015 [US1] Implement logic in `code/analyze_metrics.py` to execute `pytest` against the HumanEval test suite for each sample and record the binary `pass_rate` (1 = all tests passed, 0 = any failure) per sample in the intermediate JSON. **Constraint**: Record pass_rate linked to `task_id` in the raw intermediate JSON **before** any filtering or pairing logic is applied. **JSON Schema**: Intermediate JSON is an array of objects, each containing `task_id`, `source_type`, `cyclomatic_complexity`, `halstead_volume`, `halstead_components` (object), and `pass_rate`. **Dependency**: T014a, T014b. (FR-005)
- [X] T015b [US1] **Pairing Logic**: Implement logic in `code/analyze_metrics.py` to explicitly link `pass_rate` records to the `task_id` and `source_type` in a paired structure before aggregation. **Constraint**: Ensure the data structure supports paired analysis (e.g., dictionary keyed by `task_id` with nested `human`, `codegen`, `sensitivity` entries). **Dependency**: T015. (FR-005, Plan: Paired Statistical Design)
- [X] T045 [US1] **Sensitivity Analysis Update**: Implement logic in `code/analyze_metrics.py` to append sensitivity results (from T028) to the canonical `metrics.json` intermediate structure. **Constraint**: Must verify that the appended rows include the correct `source_type` mapping ("codellama-7b" or `null` if failed). **Dependency**: T014a, T014b, T015, T028. (Plan: Data Model Traceability)
- [X] T042 [US1] **Pairwise Exclusion Gate**: Implement logic in `code/analyze_metrics.py` to execute `pytest --cov` for `branch_coverage_pct`, record `null` if execution fails. **Logic**: Identify all task IDs where *either* the human reference OR the LLM sample has `null` coverage. **Action**: Write the list of excluded pairs to `logs/pairwise_exclusions.log`. **Constraint**: If the number of excluded pairs exceeds 5% of the total, log a warning and raise `SystemExit(1)` to halt the pipeline for manual review. **Do not** silently filter the dataset for subsequent steps; the pipeline must stop if the exclusion rate is too high. **Dependency**: T014a, T014b, T015, T015b, T045. (FR-003, FR-004, Plan: Pipeline Execution Order Step 6)
- [X] T017 [US1] Implement aggregation in `code/analyze_metrics.py` to produce `data/analysis/metrics.json` with all required fields. **Dependencies**: T014a, T014b, T015, T015b, T042, T045. **Schema**: Must contain `task_id`, `source_type`, `cyclomatic_complexity`, `halstead_volume`, `branch_coverage_pct`, and `pass_rate`. **Constraint**: Verify no record has `null` for `cyclomatic_complexity` OR `halstead_volume`. **Note**: This task aggregates the complete dataset (Primary + Sensitivity) after T042 gate passes. (US-1 Independent Test)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (including sensitivity data merged into `metrics.json`)

---

## Phase 4: User Story 2 - Statistical Comparison and Hypothesis Testing (Priority: P2)

**Goal**: Perform Wilcoxon, McNemar, Fisher, and Permutation tests, and Power Analysis (A Priori/Post-Hoc) on the paired dataset.

**Independent Test**: Feed mock paired datasets; verify p-values are calculated correctly and power analysis reports required n ≥ 38 and achieved power ≥ 0.8.

### Implementation for User Story 2

- [X] T020 [US2] Implement `code/statistical_tests.py` with Wilcoxon Signed-Rank test for continuous metrics: **Cyclomatic Complexity and Halstead Volume ONLY**. **Parameters**: Use a **two-tailed** test with `alpha=0.05`. **Dependencies**: T017. (FR-004)
- [X] T021 [US2] Implement `code/statistical_tests.py` with McNemar's test for binary pass-rate (FR-004). **Dependencies**: T017. (FR-004)
- [X] T022 [US2] Implement `code/statistical_tests.py` with a **paired version of Fisher's Exact Test** (e.g., using a permutation approach for paired binary data) to align with the Plan's 'Paired Statistical Design'. **Dependencies**: T017. (FR-004, Plan: Paired Statistical Design)
- [X] T040 [US2] Implement `code/statistical_tests.py` with Permutation Test specifically for paired branch coverage data. **Dependencies**: T017, T042. (FR-004)
- [X] T023 [US2] Implement A Priori Power Analysis in `code/statistical_tests.py` (d=0.5, α=0.05, power≥0.8) to validate sample size. **Dependencies**: T017, T042. (FR-008)
- [X] T024 [US2] Implement Post-Hoc Power Analysis in `code/statistical_tests.py` based on observed effect sizes. **Dependencies**: T020, T021, T022, T040. (FR-008)
- [X] T046 [US2] **Success Criteria Validation**: Implement logic in `code/statistical_tests.py` to evaluate the results against Success Criteria SC-002 (Statistical Significance) and SC-003 (Visualization Quality) and generate a `state/validation_results.yaml` file with boolean PASS/FAIL status for each criterion. **Dependencies**: T020, T021, T022, T040, T030. (FR-004, Spec: Success Criteria)
- [X] T026 [US2] Write unit tests for statistical functions using mock data with known p-values (tests/unit/test_statistics.py)
- [X] T027 [US2] Write integration test verifying the full statistical report generation from `metrics.json` (tests/integration/test_stats_pipeline.py)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization, Reporting, and Sensitivity Analysis (Priority: P3)

**Goal**: Generate automated Markdown report with figures, and perform sensitivity analysis using CodeLlama models.

**Independent Test**: Verify `results_report.md` contains all figures, tables, and sensitivity analysis results; verify API fallback logic works.

### Implementation for User Story 3

- [X] T030 [US3] Implement `code/report_generator.py` to create histograms and boxplots using `matplotlib` for all continuous metrics. **Constraint**: Ensure `results/figures/` directory exists (create if missing) before writing files. (FR-006)
- [X] T031 [US3] Implement `code/report_generator.py` with Jinja2 template to compile `results_report.md` including figures, tables, and power analysis. **Constraint**: The template must explicitly check `source_type` for "codellama-7b" and "codellama-3b" and render them with distinct colors/labels in figures and tables. **Dependency**: T030, T017. (FR-006, Plan: Data Model Traceability)
- [X] T031b [US3] **Sensitivity Visualization Verification**: Implement logic in `code/report_generator.py` to verify that sensitivity data (7B vs 3B) is correctly rendered in the report with distinct labels and that the `source_type` mapping matches the data in `metrics.json`. **Dependency**: T031, T017. (FR-006, Plan: Data Model Traceability)
- [X] T032 [US3] Implement logic to include sensitivity analysis comparison in the final report. **Dependencies**: T017, T023, T024. (FR-006)
- [X] T033 [US3] Write unit tests for `code/report_generator.py` to verify figure generation and template rendering (tests/unit/test_report.py)
- [X] T034 [US3] Write integration test for the full pipeline from `metrics.json` to `results_report.md` (tests/integration/test_full_pipeline.py)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T035 [P] Documentation updates in `docs/` and `README.md`
- [X] T036 Code cleanup and refactoring of `code/utils.py`
- [X] T037 [P] **Performance Optimization**: Implement parallel processing for `code/analyze_metrics.py` if safe. **Constraint**: Must include a verification step to ensure memory usage does not exceed the budget on CPU-only runners before execution. (Plan: Performance Goals)
- [X] T038 [P] Additional unit tests for edge cases (e.g., 0 coverage, missing LLM samples) in `tests/unit/`
- [X] T043 [US1] Implement robust retry logic with exponential backoff for HuggingFace dataset downloads in `code/download_data.py` to handle transient network failures.
- [X] T044 [US2] Add explicit handling in `code/statistical_tests.py` for zero-variance cases in the Permutation Test to prevent division-by-zero errors when coverage is `null` for all samples.

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

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence