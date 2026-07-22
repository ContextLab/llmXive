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
- [ ] T009 [P] Create results directory structure: `results/figures/` (FR-006, Plan: Project Structure)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup logging infrastructure in `code/utils.py` with timestamp and task ID tracking (FR-007)
- [X] T005 Implement SHA256 checksum utility in `code/utils.py` for dataset and artifact verification (FR-001, FR-011)
- [X] T006 Create `state/artifact_hashes.yaml` structure and update logic (FR-011)
- [ ] T006a [US1] **Citation Extraction**: Implement `code/extract_citations.py` to scan `spec.md`, `plan.md`, and `research.md` for citations and **create** `state/citations.yaml` with a structured list of URLs and titles. **Constraint**: This task MUST run before T007a to ensure the input artifact exists. (FR-010, Plan: Pipeline Execution Order Step 1)
- [ ] T007a [US1] Implement `code/validate_citations.py` wrapper for the Reference-Validator Agent (FR-010). **Logic**: Must read citations from `state/citations.yaml`, verify against primary sources, and return exit code 0 on success, non-zero on failure. **Dependency**: T006a. (FR-010)
- [ ] T007b [US1] **Pipeline Gate**: Implement `code/run_pipeline_gate.py` to invoke `python code/validate_citations.py` as the first step of the pipeline. **Logic**: Must capture the exit code of T007a; if non-zero, log the specific validation failure reason to `logs/pipeline_gate.log` and then raise `SystemExit(1)` to abort the pipeline immediately. **Dependency**: T007a. (Plan: Pipeline Execution Order Step 1)
- [X] T008 Create data directory structure: `data/raw/`, `data/generated/`, `data/analysis/`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Paired Analysis Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download HumanEval, generate LLM code, compute metrics (Complexity, Halstead, Coverage), and produce paired JSON dataset.

**Independent Test**: Run the pipeline on a local copy of HumanEval. Verify that `data/analysis/metrics.json` contains `cyclomatic_complexity`, `halstead_volume`, `branch_coverage_pct`, and `pass_rate` for every valid pair, with at least 40 valid samples.

### Implementation for User Story 1

- [ ] T010 [US1] Implement `code/download_data.py` to download HumanEval from HuggingFace using `streaming=True` to process the full dataset without loading it into RAM. Verify SHA256 and save to `data/raw/`. **Constraint**: Must NOT fall back to synthetic data; must raise a `RuntimeError` with a clear message "Failed to download verified real source" if the download fails after max retries. (FR-001, FR-011, Plan: Large real datasets: STREAM the real data)
- [ ] T010b [US1] **Sampling Configuration**: Implement logic in `code/download_data.py` to generate `state/sampling_config.yaml` containing the exact stratified sampling parameters (quartile boundaries, target count per quartile) derived from the full HumanEval dataset pass-rates. **Dependency**: T010. (Plan: Sampling Strategy)
- [ ] T011 [US1] Implement stratified sampling logic in `code/download_data.py` to select a representative subset of tasks based on human pass-rate quartiles. **Dependency**: T010, T010b. **Includes assertion**: Verify the final selected subset distribution matches the stratified configuration in `state/sampling_config.yaml` (i.e., proportional representation across quartiles). **Constraint**: If T010 fails or returns insufficient data, T011 must not run. Do NOT assert a specific fixed sample size; verify the *method* was followed. (Plan: Sampling Strategy)
- [ ] T012 [US1] Implement `code/generate_code.py` to load `Salesforce/codegen-mono` on CPU and generate code for a set of tasks with 3-retry logic (FR-002)
- [ ] T013 [US1] Implement error handling in `code/generate_code.py` to log failures to `errors.log` and mark samples as missing (Edge Cases)
- [ ] T014 [US1] Implement `code/analyze_metrics.py` to run `radon` for **Cyclomatic Complexity** AND **Halstead Volume** on all samples in a single atomic operation. **Metric Specifics**: Extract `radon.cc` and all Halstead metrics (N, n, N, n, V, L, D, E), recording `cyclomatic_complexity` and `halstead_volume` (V) in the intermediate JSON. **Constraint**: If extraction fails for a specific sample, record `null` for that metric (do not halt the script). Ensure both fields exist in the output record for every sample. (FR-003)
- [ ] T015 [US1] Implement logic in `code/analyze_metrics.py` to execute `pytest` against the HumanEval test suite for each sample and record the binary `pass_rate` (1 = all tests passed, 0 = any failure) per sample in the intermediate JSON. **JSON Schema**: Intermediate JSON is an array of objects, each containing `task_id`, `source_type`, `cyclomatic_complexity`, `halstead_volume`, and `pass_rate`. Aggregated rates are calculated in the report generation phase, not here. (FR-005)
- [ ] T042 [US1] Implement logic in `code/analyze_metrics.py` to run `pytest --cov` for `branch_coverage_pct`, recording `null` if execution fails. (FR-003, Edge Cases)
- [ ] T042a [US1] Implement logic in `code/analyze_metrics.py` to filter out any individual samples where `branch_coverage_pct` is `null` before producing the final `data/analysis/metrics.json`. (FR-003, FR-004)
- [ ] T042b [US1] **Pairwise Exclusion Logic**: Implement logic in `code/analyze_metrics.py` to identify task IDs where *either* the human reference OR the LLM sample has `null` coverage (after T042a). Remove the entire pair from the dataset to ensure strict pairing for statistical tests. **Output**: Log the count of removed pairs and the final valid pair count to `logs/pairwise_filter.log`. **Constraint**: The final dataset must only contain complete pairs. (FR-004, Plan: Paired Statistical Design)
- [ ] T017 [US1] Implement aggregation in `code/analyze_metrics.py` to produce `data/analysis/metrics.json` with all required fields. **Dependencies**: T014, T015, T042, T042a, T042b. **Schema**: Must contain `task_id`, `source_type`, `cyclomatic_complexity`, `halstead_volume`, `branch_coverage_pct`, and `pass_rate`. **Constraint**: Verify no record has `null` for `cyclomatic_complexity` OR `halstead_volume` (if both are null, the pair should have been removed by T042b logic if applicable, or flagged). (US-1 Independent Test)

**Sensitivity Analysis Sub-Phase (within US1)**

- [ ] T028 [US1] Implement sensitivity analysis logic in `code/generate_code.py` to call HuggingFace Inference API for `CodeLlama-7B` for a subset of tasks. **Trigger**: Run only if API is available. (FR-009)
- [ ] T028a [US3] Implement local model availability check in `code/generate_code.py`. **Artifact**: Write `state/model_availability.json` with availability status.
- [ ] T028c [US1] Initialize `state/model_availability.json`.
- [ ] T029 [US1] Implement fallback logic in `code/generate_code.py`: Use `CodeLlama-3B` if API fails and local model is available.
- [ ] T045 [US1] **Sensitivity Analysis Update**: Implement logic to compute effect sizes (Cohen's d) and delta calculations between CodeGen and CodeLlama variants, and **update** `data/analysis/metrics.json` (the canonical file) by appending sensitivity results or merging them into the existing dataset. **Dependencies**: T017, T028, T029. **Constraint**: Must preserve the canonical nature of `metrics.json` by overwriting the file with the augmented dataset. (FR-009)
- [ ] T046 [US1] **Sensitivity Comparison Logic**: Generate comparative summary of sensitivity analysis results and append it to the end of `data/analysis/metrics.json` as a metadata block or separate section, ensuring traceability. **Dependencies**: T045. (FR-009)

- [ ] T018 [US1] Write unit tests for `code/download_data.py` to verify checksum logic and sampling distribution (tests/unit/test_download.py)
- [ ] T019 [US1] Write integration test for `code/analyze_metrics.py` to verify metric extraction on a known Python snippet (tests/integration/test_metrics.py)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (including sensitivity data merged into `metrics.json`)

---

## Phase 4: User Story 2 - Statistical Comparison and Hypothesis Testing (Priority: P2)

**Goal**: Perform Wilcoxon, McNemar, Fisher, and Permutation tests, and Power Analysis (A Priori/Post-Hoc) on the paired dataset.

**Independent Test**: Feed mock paired datasets; verify p-values are calculated correctly and power analysis reports required n ≥ 38 and achieved power ≥ 0.8.

### Implementation for User Story 2

- [ ] T020 [US2] Implement `code/statistical_tests.py` with Wilcoxon Signed-Rank test for continuous metrics: **Cyclomatic Complexity and Halstead Volume ONLY**. **Dependencies**: T017, T045. (FR-004)
- [ ] T021 [US2] Implement `code/statistical_tests.py` with McNemar's test for binary pass-rate (FR-004). **Dependencies**: T017, T045. (FR-004)
- [ ] T022 [US2] Implement `code/statistical_tests.py` with Fisher's Exact Test for **unpaired exploratory checks ONLY** (FR-004). **Dependencies**: T017, T045. (FR-004)
- [ ] T040 [US2] Implement `code/statistical_tests.py` with Permutation Test specifically for paired branch coverage data. **Dependencies**: T017, T045, T042b. (FR-004)
- [ ] T023 [US2] Implement A Priori Power Analysis in `code/statistical_tests.py` (d=0.5, α=0.05, power≥0.8) to validate sample size. **Dependencies**: T017, T045, T042b. (FR-008)
- [ ] T024 [US2] Implement Post-Hoc Power Analysis in `code/statistical_tests.py` based on observed effect sizes. **Dependencies**: T020, T021, T022, T040. (FR-008)
- [ ] T026 [US2] Write unit tests for statistical functions using mock data with known p-values (tests/unit/test_statistics.py)
- [ ] T027 [US2] Write integration test verifying the full statistical report generation from `metrics.json` (tests/integration/test_stats_pipeline.py)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization, Reporting, and Sensitivity Analysis (Priority: P3)

**Goal**: Generate automated Markdown report with figures, and perform sensitivity analysis using CodeLlama models.

**Independent Test**: Verify `results_report.md` contains all figures, tables, and sensitivity analysis results; verify API fallback logic works.

### Implementation for User Story 3

- [ ] T030 [US3] Implement `code/report_generator.py` to create histograms and boxplots using `matplotlib` for all continuous metrics. (FR-006)
- [ ] T031 [US3] Implement `code/report_generator.py` with Jinja2 template to compile `results_report.md` including figures, tables, and power analysis (FR-006)
- [ ] T032 [US3] Implement logic to include sensitivity analysis comparison in the final report. **Dependencies**: T045, T046. (FR-006)
- [ ] T033 [US3] Write unit tests for `code/report_generator.py` to verify figure generation and template rendering (tests/unit/test_report.py)
- [ ] T034 [US3] Write integration test for the full pipeline from `metrics.json` to `results_report.md` (tests/integration/test_full_pipeline.py)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T035 [P] Documentation updates in `docs/` and `README.md`
- [X] T036 Code cleanup and refactoring of `code/utils.py`
- [X] T037 Performance optimization for `code/analyze_metrics.py` (parallel processing if safe)
- [ ] T038 [P] Additional unit tests for edge cases (e.g., 0 coverage, missing LLM samples) in `tests/unit/`
- [ ] T043 [US1] Implement robust retry logic with exponential backoff for HuggingFace dataset downloads in `code/download_data.py` to handle transient network failures.
- [ ] T044 [US2] Add explicit handling in `code/statistical_tests.py` for zero-variance cases in the Permutation Test to prevent division-by-zero errors when coverage is `null` for all samples.

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