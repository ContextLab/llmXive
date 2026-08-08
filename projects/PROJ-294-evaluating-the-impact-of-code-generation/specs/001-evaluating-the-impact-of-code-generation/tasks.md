---
description: "Task list template for feature implementation"
---

# Tasks: Evaluating the Impact of Code Generation Models on Code Testability

**Input**: Design documents from `/specs/294-evaluating-impact-code-gen-testability/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `data/`, `state/`, `results/`, `tests/`, `docs/` at repository root (per `plan.md` structure)
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project structure defined in `plan.md`

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
- [X] T008 Create data directory structure: `data/raw/`, `data/generated/`, `data/analysis/`. (Plan: Project Structure)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Paired Analysis Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download HumanEval, generate LLM code, compute metrics (Complexity, Mutation Score, Coverage), and produce paired JSON dataset.

**Independent Test**: Run the pipeline on a local copy of HumanEval. Verify that `data/analysis/metrics.json` contains `cyclomatic_complexity`, `halstead_volume`, `mutation_score`, and `pass_rate` for every valid pair, with at least 40 valid samples.

### Implementation for User Story 1

- [ ] T010 [US1] Implement `code/download_data.py` to download HumanEval from HuggingFace (`openai_humaneval`) using `revision="main"` to ensure deterministic versioning. Use `streaming=True` to process the full dataset without loading it into RAM. **Constraint**: Must NOT fall back to synthetic data; must raise a `RuntimeError` with a clear message "Failed to download verified real source" if the download fails after max retries. **Timeout Logic**: Implement a runtime watchdog using `subprocess.run` with `timeout=14400s` (4 hours). If `TimeoutExpired` occurs, abort the full stream, select a random subset of **N=80** tasks (using seed 42) from the already downloaded data (or **re-run the download logic restricted to the first 80 indices determined by seed 42** if the stream was incomplete) to ensure completion within the Plan's budget. **Output**: Save raw data to `data/raw/humaneval.parquet` and compute SHA256. **Dependency**: T005. (FR-001, FR-011, Plan: Large real datasets: STREAM the real data, Plan: Worst-Case Budget)
- [ ] T010b [US1] **Human Reference Extraction**: Implement logic in `code/download_data.py` to extract `solution` and `test` strings from the raw HumanEval data into `data/raw/human_references.json`. **Constraint**: Must preserve the `task_id` for every entry. **Output**: `data/raw/human_references.json`. **Dependency**: T010. (Plan: Ordering, FR-001)
- [ ] T011 [US1] **Defined Subset Selection**: Implement logic in `code/download_data.py` to select a reproducible subset of tasks from the full HumanEval dataset. **Method**: Use a **fixed random seed (42)** to select **N=80** tasks. **Constraint**: Do NOT implement stratified sampling by pass-rate (unauthorized scope creep). The subset must be deterministic. **Output**: Save the filtered subset to `data/raw/sampled_subset.json`. **Dependency**: T010b. (Plan: Sampling Strategy, FR-001)
- [ ] T012 [US1] Implement `code/generate_code.py` to load `Salesforce/codegen-350M-mono` on CPU and generate code for the tasks in `data/raw/sampled_subset.json`. **Constraint**: Must implement **retry logic with exponential backoff** as mandated by FR-002. **Output**: Save generated code to `data/generated/codegen_samples.json`. **Dependency**: T011. (FR-002)
- [X] T013 [US1] Implement error handling in `code/generate_code.py` to log failures to `errors.log` and mark samples as missing (Edge Cases). (FR-002)
- [ ] T028 [US1] **Sensitivity Generation (GPU Escape Hatch)**: Implement logic in `code/generate_code.py` to handle sensitivity analysis. **Logic**: First, attempt to load `CodeLlama-7b` (or 13b) on GPU if `torch.cuda.is_available()` is True and VRAM >= 8GB. **Constraint**: If GPU is unavailable, model load fails, or VRAM is insufficient, **immediately fallback** to `Salesforce/codegen-350M-mono` (CPU) for the **full subset (N=80)**. Do NOT use `codegen-2.7B-mono` or other models not specified in the Plan. **Output**: Save to `data/generated/sensitivity_samples.json`. **Dependency**: T011. (FR-009, Plan: GPU Offload Logic, Constitution: Compute Feasibility)
- [ ] T014a [US1] **Metric Extraction (Static)**: Implement `code/analyze_metrics.py` to run `radon cc --json` and `radon hal --json` on all samples (Human, CodeGen, Sensitivity) from `data/generated/` and `data/raw/human_references.json` (Human reference). **Constraint**: Must operate ONLY on the tasks present in `data/raw/sampled_subset.json`. **Output**: Intermediate JSON with `cyclomatic_complexity`, `halstead_volume`, `halstead_components`. **Dependency**: T012, T028, T010b. (FR-003)
- [X] T014b [US1] **Metric Processing**: Implement logic in `code/analyze_metrics.py` to parse `radon` output, map `cc` to `cyclomatic_complexity`, and calculate `halstead_volume` from `hal` components. **Constraint**: Store all extracted Halstead components. **Dependency**: T014a. (FR-003)
- [X] T014c [US1] **Branch Coverage Calculation**: Implement logic in `code/analyze_metrics.py` to execute `coverage.py` on the human reference code (from `human_references.json`) to calculate `branch_coverage_pct`. **Constraint**: This is a secondary metric for correctness. **Output**: Intermediate JSON with `branch_coverage_pct`. **Dependency**: T010b. (FR-003, Spec: Data Model)
- [~] T015 [US1] **Correctness Metric (Pass Rate)**: Implement logic in `code/analyze_metrics.py` to execute `pytest` against the HumanEval test suite for each sample and record the binary `pass_rate` (1 = all tests passed, 0 = any failure) per sample. **Constraint**: Operate ONLY on the tasks in `data/raw/sampled_subset.json`. **Semantic Clarification**: This metric measures **correctness**, not testability. It is a secondary metric distinct from the primary testability metric (Mutation Score). **Output**: Intermediate JSON with `pass_rate`. **Dependency**: T014a. (FR-005, Plan: Key Methodological Correction)
- [X] T015b [US1] **Pairing Logic**: Implement logic in `code/analyze_metrics.py` to explicitly link `pass_rate` records to the `task_id` and `source_type` in a paired structure. **Constraint**: Ensure the data structure supports paired analysis (e.g., dictionary keyed by `task_id`). **Dependency**: T015. (FR-005, Plan: Paired Statistical Design) <!-- FAILED: unspecified -->
- [~] T016 [US1] **Mutation Score Extraction (Testability)**: Implement `code/analyze_metrics.py` to run `mutmut` on the generated code samples to compute the **Mutation Score** as the primary metric for "testability" (replacing branch_coverage_pct as per Plan). **Logic**: Run `mutmut` on a subset of tasks first to estimate runtime; if runtime exceeds budget, scale down the mutation depth or sample size explicitly (Algorithm: reduce mutation depth from a higher baseline to a lower value; if still > 2h, sample [deferred] of tasks). **Output**: Append `mutation_score` to the intermediate JSON. **Schema**: Key `mutation_score`, Type `float`, Value range from the minimum possible to the maximum possible, Formula: `(killed_mutants / total_mutants * 100)`. **Constraint**: Operate ONLY on the tasks in `data/raw/sampled_subset.json`. **FR Mapping**: This task explicitly fulfills the **testability** aspect of FR-005 ("Execute test suites and record pass rates" interpreted as executing mutation tests to record testability rates). **Dependency**: T012, T028, T010b. (Plan: Key Methodological Correction, FR-003, FR-005) <!-- FAILED: unspecified -->
- [X] T045 [US1] **Sensitivity Analysis Update**: Implement logic in `code/analyze_metrics.py` to merge sensitivity results (from T028) with the base results (from T012) into a single canonical intermediate structure. **Constraint**: Must verify that the merged rows include the correct `source_type` mapping and that all task IDs from T011 are present in both sources (or explicitly marked as failed). **Dependency**: T014a, T014b, T014c, T015, T015b, T016, T028. (Plan: Data Model Traceability)
- [X] T042 [US1] **Pairwise Exclusion Gate**: Implement logic in `code/analyze_metrics.py` to identify all task IDs where *either* the human reference OR the LLM sample has `null` coverage (non-executable). **Action**: Write the list of excluded pairs to `logs/pairwise_exclusions.log`. **Constraint**: If the number of excluded pairs results in a remaining sample size **n < 30**, log a **warning** (do NOT halt) and allow the pipeline to proceed to Power Analysis (T023/T024) to calculate Post-Hoc power on the reduced sample. If the exclusion rate (excluded_pairs / total_pairs) indicates a systematic pipeline failure (e.g., >50% of pairs excluded due to non-executability), log a critical error and raise `SystemExit(1)` to halt the pipeline **before** aggregation. **Dependency**: T045, T014c, T015. (FR-003, FR-004, Plan: Pipeline Execution Order Step 6, FR-008)
- [~] T017 [US1] Implement aggregation in `code/analyze_metrics.py` to produce `data/analysis/metrics.json` with all required fields. **Dependencies**: T042, T014a, T014b, T014c, T015, T015b, T016, T045. **Schema**: Must contain `task_id`, `source_type`, `cyclomatic_complexity`, `halstead_volume`, `mutation_score`, `branch_coverage_pct`, and `pass_rate`. **Constraint**: Verify no record has `null` for `cyclomatic_complexity`, `halstead_volume`, OR `mutation_score`. **Note**: This task aggregates the complete dataset ONLY AFTER T042 passes. (US-1 Independent Test, FR-008)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (including sensitivity data merged into `metrics.json`). **Verification Command**: Run `python code/main.py --us1 --verify` and check exit code 0.

---

## Phase 4: User Story 2 - Statistical Comparison and Hypothesis Testing (Priority: P2)

**Goal**: Perform Wilcoxon, McNemar, and Permutation tests, and Power Analysis (A Priori/Post-Hoc) on the paired dataset.

**Independent Test**: Feed mock paired datasets; verify p-values are calculated correctly and power analysis reports required n ≥ 38 and achieved power ≥ 0.8.

### Implementation for User Story 2

- [ ] T020 [US2] Implement `code/statistical_tests.py` with Wilcoxon Signed-Rank test for continuous metrics: **Cyclomatic Complexity, Halstead Volume, and Mutation Score**. **Parameters**: Use a **two-tailed** test with `alpha=0.05`. **Dependencies**: T017. (FR-004)
- [ ] T021 [US2] Implement `code/statistical_tests.py` with McNemar's test for binary pass-rate. **Parameters**: Use `alpha=0.05`. **Dependencies**: T017. (FR-004, Plan: Complexity Tracking)
- [ ] T040 [US2] Implement `code/statistical_tests.py` with Permutation Test specifically for paired mutation score data. **Dependencies**: T017, T042. (FR-004)
- [ ] T023 [US2] Implement A Priori Power Analysis in `code/statistical_tests.py` (d=0.5, α=0.05, power≥0.8) to validate sample size. **Dependencies**: T017, T042. (FR-008)
- [ ] T024 [US2] Implement Post-Hoc Power Analysis in `code/statistical_tests.py` based on observed effect sizes, **even if sample size is reduced**. **Dependencies**: T020, T021, T040. (FR-008)
- [ ] T046 [US2] **Success Criteria Validation**: Implement logic in `code/statistical_tests.py` to evaluate the results against the **Functional Requirements** (FR-004 for statistical significance, FR-008 for power analysis) and the Plan's **Key Methodological Corrections** (paired analysis, complete-case coverage). Generate a `state/validation_results.yaml` file with boolean PASS/FAIL status for each requirement. **Dependencies**: T020, T021, T040, T024, T042. (FR-004, FR-008, Plan: Key Methodological Corrections)
- [X] T026 [US2] Write unit tests for statistical functions using mock data with known p-values (tests/unit/test_statistics.py). (Plan: Testing)
- [ ] T027 [US2] Write integration test verifying the full statistical report generation from `metrics.json` (tests/integration/test_stats_pipeline.py). (Plan: Testing)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization, Reporting, and Sensitivity Analysis (Priority: P3)

**Goal**: Generate automated Markdown report with figures, and perform sensitivity analysis using CodeLlama models.

**Independent Test**: Verify `results_report.md` contains all figures, tables, and sensitivity analysis results; verify API fallback logic works.

### Implementation for User Story 3

- [ ] T030 [US3] Implement `code/report_generator.py` to create histograms and boxplots using `matplotlib` for all continuous metrics. **Constraint**: Ensure `results/figures/` directory exists (create if missing) before writing files. (FR-006)
- [ ] T031 [US3] Implement `code/report_generator.py` with Jinja2 template to compile `results_report.md` including figures, tables, and power analysis. **Constraint**: The template must explicitly check `source_type` for "codegen-350m" and "sensitivity-model" and render them with distinct colors/labels. **Dependency**: T030, T017. (FR-006, Plan: Data Model Traceability)
- [ ] T031b [US3] **Sensitivity Visualization Verification**: Implement logic in `code/report_generator.py` to verify that sensitivity data (from T028) is correctly rendered in the report with distinct labels and that the `source_type` mapping matches the data in `metrics.json`. **Dependency**: T031, T017. (FR-006, Plan: Data Model Traceability)
- [X] T032 [US3] Implement logic to include sensitivity analysis comparison in the final report. **Dependencies**: T017, T023, T024. (FR-006)
- [ ] T033 [US3] Write unit tests for `code/report_generator.py` to verify figure generation and template rendering (tests/unit/test_report.py). (Plan: Testing)
- [ ] T034 [US3] Write integration test for the full pipeline from `metrics.json` to `results_report.md` (tests/integration/test_full_pipeline.py). (Plan: Testing)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T035a [P] **Documentation**: Update `README.md` with setup instructions, usage examples, and contribution guidelines. (Plan: Documentation)
- [X] T035b [P] **Documentation**: Generate API documentation for `code/` modules using Sphinx or similar. (Plan: Documentation)
- [X] T035c [P] **Documentation**: Create `docs/CONTRIBUTING.md` with coding standards and pull request process. (Plan: Documentation)
- [X] T036 Code cleanup and refactoring of `code/utils.py`. (Plan: Testing)
- [ ] T037 [P] **Performance Optimization**: Implement parallel processing for `code/analyze_metrics.py` if safe. **Constraint**: Must include a verification step to ensure memory usage does not exceed the budget on CPU-only runners before execution. **Implementation Detail**: Use **file-per-task output** (e.g., `data/analysis/temp/task_id.json`) to avoid race conditions when writing intermediate results. (Plan: Performance Goals)
- [X] T038 [P] Additional unit tests for edge cases (e.g., 0 coverage, missing LLM samples) in `tests/unit/`. (Plan: Testing)
- [ ] T043 [US1] Implement robust retry logic with exponential backoff for HuggingFace dataset downloads in `code/download_data.py` to handle transient network failures. (FR-001)
- [ ] T044 [US2] Add explicit handling in `code/statistical_tests.py` for zero-variance cases in the Permutation Test to prevent division-by-zero errors when coverage is `null` for all samples. (FR-004)
- [X] T050a [US1] **Artifact Integrity (Download)**: Implement `code/utils.py` to compute SHA256 for `data/raw/humaneval.parquet` immediately after download. **Dependency**: T010. (FR-011, Plan: Artifact Integrity)
- [X] T050b [US1] **Artifact Integrity (Generation)**: Implement `code/utils.py` to compute SHA256 for `data/generated/` files immediately after generation. **Dependency**: T012, T028. (FR-011, Plan: Artifact Integrity)
- [ ] T050c [US1] **Artifact Integrity (Aggregation)**: Implement `code/utils.py` to compute SHA256 for `data/analysis/metrics.json` immediately after aggregation. **Dependency**: T017. (FR-011, Plan: Artifact Integrity)
- [ ] T051 [US3] **Mutation Score Visualization**: Update `code/report_generator.py` to include a specific visualization (e.g., boxplot) comparing `mutation_score` between Human and LLM generated code. **Constraint**: Ensure the figure is clearly labeled as "Testability (Mutation Score)". **Dependency**: T016. (FR-006, Plan: Key Methodological Correction)
- [ ] T052 [US2] **Statistical Test for Mutation Score**: Extend `code/statistical_tests.py` to include Wilcoxon Signed-Rank test for the `mutation_score` metric (already covered in T020, this task ensures it is prioritized). **Constraint**: Ensure this test is prioritized in the report as the primary finding for "testability" impact. **Dependency**: T016. (FR-004, Plan: Key Methodological Correction)
- [ ] T053 [US3] **Sensitivity Analysis Report**: Implement `code/report_generator.py` to specifically compare `codegen-350m` vs `sensitivity-model` metrics in a dedicated "Sensitivity Analysis" section of `results_report.md`. **Constraint**: Must include a table showing p-values and effect sizes for the sensitivity comparison. **Dependency**: T031, T045. (FR-009, Plan: Sensitivity Analysis)
- [ ] T054a [US3] **Citation Validation Logic (Bibliography)**: Implement `code/validate_citations.py` to programmatically verify that all external citations in the report match the bibliography and that title-token-overlap is ≥ 0.7. **Constraint**: Must fail the pipeline if any citation is invalid. **Dependency**: T031. (FR-010, Plan: Constitution Check II)
- [ ] T054b [US3] **Citation Validation Logic (Internal Consistency)**: Implement `code/validate_citations.py` to verify that statistical claims in the report (e.g., p-values) match the values in `state/validation_results.yaml`. **Constraint**: Use regex `p-value\s*[=:]\s*([\d\.e+-]+)` and tolerance `1e-6`. **Dependency**: T046, T031. (QA Scope)

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
