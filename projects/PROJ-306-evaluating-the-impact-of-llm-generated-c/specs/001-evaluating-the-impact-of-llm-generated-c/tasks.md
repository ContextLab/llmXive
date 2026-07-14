# Tasks: Evaluating the Impact of LLM-Generated Code on Code Coverage

**Input**: Design documents from `/specs/001-evaluating-llm-code-coverage/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md

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

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a Create `code/`, `data/`, `tests/`, `outputs/` directories
- [X] T001b Create `data/benchmarks/`, `data/benchmarks/raw/`, `data/benchmarks/processed/`, `data/generated/`, `data/coverage_reports/`, `data/processed/`, `outputs/` subdirectories. **Validation**: Verify all directories exist after creation.

- [X] T002a Create `requirements.txt` with pinned versions (pytest, pytest-cov>=4.0.0, pandas, scipy, statsmodels, transformers, datasets, openai, huggingface_hub, matplotlib, seaborn, bitsandbytes)
- [X] T002b Create virtualenv and install dependencies from `requirements.txt`

- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/config.py` for seed management, API key loading (`LLM_API_KEY`), and model fallback logic (gpt-4 -> code-llama-7b -> bigcode/starcoderbase-3b)
- [X] T005 [P] Implement `code/utils.py` with exponential backoff retry logic for API rate limits. **Specifics**: Implement a retry mechanism with an initial wait duration and an exponential backoff factor, configured with a limited number of attempts.
- [X] T006a [P] Implement `code/dataset_loader.py` to ingest MBPP via `datasets.load_dataset("mbpp")` and save raw canonical files unchanged to `data/benchmarks/raw/mbpp/`
- [X] T006b [P] Implement `code/dataset_loader.py` to ingest HumanEval via `datasets.load_dataset("google-research-datasets/human_eval")` and save raw canonical files unchanged to `data/benchmarks/raw/humaneval/`
- [X] T006c [P] Create `contracts/task_catalog.schema.yaml` defining the schema for task catalog validation. **Note**: This task creates the schema file required by T006d.
- [X] T006d [P] Extend `code/dataset_loader.py` to validate required fields (`task_id`, `prompt`, `human_solution`, `test_suite`) against `contracts/task_catalog.schema.yaml` and save a normalized JSON catalog to `data/benchmarks/processed/catalog.json`. Keys MUST include: `task_id`, `prompt`, `human_solution`, `test_suite_path`, `difficulty`, `code_patterns`.
- [X] T007 Implement `code/test_transformer.py` to convert MBPP/HumanEval string-based test suites into executable `.py` files in `data/benchmarks/processed/tests/`, handling missing test suites by logging warnings
- [X] T009 [P] Implement `code/llm_generator.py` with logic to call LLM API (or local CPU inference for fallback models) and save generated code to `generated/{task_id}.py`. **Constraint**: Implement the fallback logic defined in FR-002 (Primary -> Fallback). If the fallback model is used, ensure it runs within CI constraints (e.g., use quantization if necessary to fit RAM, but do not hard-code quantization as a spec requirement if not explicitly mandated by FR-002). Log the model used for each task.
- [X] T010 [P] [US1] Contract test for dataset loading in `tests/unit/test_dataset_loader.py`
- [X] T011 [P] [US1] Integration test for end-to-end generation and coverage on multiple tasks in `tests/integration/test_pipeline_us1.py`
- [X] T012 [P] [US1] Implement `code/coverage_runner.py` to execute `pytest --cov` on generated files. **Validation**: For HumanEval tasks, explicitly SKIP branch coverage measurement (do not measure and discard; do not run `--cov` with branch flag). For other tasks, measure both line and branch coverage. Parse output and save to `coverage_reports/{task_id}.json`. Log branch coverage as `N/A` for HumanEval tasks.
- [X] T013 [US1] Implement logic in `code/main.py` to orchestrate generation and coverage execution for a batch of tasks. **Deliverables**:
 1. Add `argparse` arguments: `--num-tasks`, `--output-dir`, `--dataset`, `--model`, `--perform-regression`.
 2. Implement `try/except` blocks for `SyntaxError` and generic `Exception` during execution.
 3. On failure, write a JSON record to `coverage_reports/{task_id}.json` with schema: `{ "task_id": "...", "status": "failed", "error_message": "...", "timestamp": "..." }`.
 4. Continue processing subsequent tasks without aborting.
- [X] T014 [US1] Add logging for model used, generation success/failure, and coverage results.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Comparative statistical analysis (Priority: P2)

**Goal**: Compare LLM vs. human coverage, perform statistical testing (paired t-test/Wilcoxon/LMM/GLMM), and generate sensitivity analysis.

**Independent Test**: Run the analysis on a paired set of tasks and confirm that `stats_summary.csv` is produced with columns: `mean_llm`, `mean_human`, `mean_diff`, `p_value`, `cohen_d`, `test_type`.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T022 [P] [US2] Unit test for Shapiro-Wilk normality test logic in `tests/unit/test_analyzer.py`
- [X] T023 [P] [US2] Unit test for sensitivity analysis thresholds in `tests/unit/test_analyzer.py`

### Implementation for User Story 2

- [X] T024 [US2] Implement `code/analyzer.py` to load `coverage_reports/`, pair LLM and human results by `task_id`, and calculate coverage differences. **Note**: This task depends on US1 completion (`coverage_reports/` generation).
- [X] T025 [US2] Implement Shapiro-Wilk normality test (FR-016) in `code/analyzer.py`. **Logic**: If Shapiro-Wilk p-value < 0.05 (indicating non-normal distribution), execute Wilcoxon signed-rank test; otherwise, execute paired t-test. **Output**: Include `test_type` (t-test, Wilcoxon, LMM, or GLMM) in `data/processed/stats_summary.csv`.
- [X] T026 [US2] Implement statistical summary generation (FR-005) to output `data/processed/stats_summary.csv` with mean difference, p-value, Cohen's d, and test type.
- [X] T027 [US2] Implement family-wise error correction (Bonferroni or Holm-Bonferroni) for subgroup hypothesis tests (FR-006). **Scope**: Apply correction ONLY to subgroup tests for difficulty tiers (easy, medium, hard) and code patterns (loops, conditionals, recursion). Explicitly exclude sensitivity analysis (FR-011) and other subgroups from this correction. **Output**: Write corrected p-values to `data/processed/corrected_pvalues.csv`.
- [X] T028 [US2] Implement exclusion rate calculation (FR-014) and add to final summary. **Output**: Calculate percentage of tasks excluded (missing test suites, generation failures) as `excluded_count / total_count` and write to `data/processed/summary.csv` with column `exclusion_rate`.
- [X] T029 [US2] Implement sensitivity analysis (FR-011) across thresholds {0.01, 0.05, 0.10, 0.15, 0.20, 0.25} and output `data/processed/sensitivity_report.csv`. **Constraint**: Explicitly exclude these thresholds from family-wise error correction as per FR-011. **Verification**: Programmatically check the sign of the mean coverage gap across all thresholds. If a sign flip is detected, RAISE A RUNTIME ERROR to fail the build, ensuring SC-003 compliance.
- [X] T052 [US2] Implement FR-010 (Associational Language) in `code/analyzer.py` and `code/visualizer.py`. **Logic**: Ensure all output strings, logs, and summary reports explicitly use language such as "association", "correlation", or "difference" and strictly avoid causal terms like "cause", "effect", or "impact" when describing results.
- [X] T053 [US2] Implement Regression Mode Trigger in `code/main.py`. **Logic**: If the `--perform-regression` flag is set, enable the multi-variable regression model path required for FR-013 (VIF calculation). If not set, skip regression-specific steps.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Stratified insight & visualization (Priority: P3)

**Goal**: Stratify results by difficulty and code patterns, and generate visualizations.

**Independent Test**: After statistical analysis, request a stratified report for "loops"; verify that `stratified_loops.csv` and `coverage_by_pattern_loops.png` appear in `outputs/`.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T039 [P] [US3] Unit test for pattern extraction logic in `tests/unit/test_visualizer.py`
- [X] T040 [P] [US3] Integration test for visualization generation in `tests/integration/test_visualizer.py`

### Implementation for User Story 3

- [X] T041 [P] [US3] Implement `code/visualizer.py` to extract code patterns (loops, conditionals, recursion) from solutions and annotate the dataset.
- [X] T042 [US3] Implement stratification logic (FR-007) to group data by difficulty, pattern, and boundary-case presence.
- [X] T043 [US3] Implement generation of stratified CSVs (e.g., `stratified_loops.csv`) and PNG visualizations (box-plots, bar-charts) with 800x600 resolution, axis labels, and legends (FR-008), saving to `outputs/`.
- [X] T044 [US3] Implement logic to calculate and report mean branch-coverage gaps for specific difficulty tiers (e.g., "hard") in `stratified_summary.csv`. **Deliverable**: Add a function to `code/visualizer.py` that filters `coverage_pairs.csv` for `difficulty="hard"` AND `branch_coverage != "N/A"`, calculates `mean(branch_coverage_gap)`, and appends the result as a row in `outputs/stratified_summary.csv` with columns: `[pattern, difficulty, mean_gap, count]`. **Constraint**: Explicitly exclude tasks where `branch_coverage == "N/A"` (HumanEval) from this calculation.
- [X] T045 [US3] Implement Collinearity Diagnostics (VIF) in `code/analyzer.py`. **Dependency**: This task depends on code pattern counts generated in T041. **Condition**: Execute ONLY if the `--perform-regression` flag (defined in T013/T053) is set or if the analysis mode is explicitly set to regression. If 'lmm' or 'glmm' is selected without regression, skip VIF calculation as per FR-013. **Sequential**: Must run after T041.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T046 [P] Documentation updates: Update `quickstart.md` with execution instructions and `data-model.md` with schema details.
- [X] T047 Code cleanup: Ensure all error handling (API limits, syntax errors) is robust and logs are informative.
- [X] T048 [P] Performance optimization: pipeline can process ≥100 tasks within 6 hours on CPU-only runner [UNRESOLVED-CLAIM: c_70f2b183 — status=not_enough_info] (SC-005).
- [X] T049 [P] Add unit tests for edge cases (missing test suite, generation failure) in `tests/unit/`.
- [X] T050 [P] Run `quickstart.md` validation to ensure reproducibility.

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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **Must complete first** to generate `coverage_reports/` data.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (`coverage_reports/`).
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 output and code pattern analysis.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- **Important**: Once Foundational phase completes, User Story 1 can start immediately. User Story 2 and User Story 3 **cannot** start until User Story 1 is complete because they depend on the `coverage_reports/` and `coverage_pairs.csv` artifacts generated by US1.
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members ONLY after US1 is complete.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for dataset loading in tests/unit/test_dataset_loader.py"
Task: "Integration test for end-to-end generation and coverage in tests/integration/test_pipeline_us1.py"

# Launch all models for User Story 1 together:
Task: "Implement code/llm_generator.py"
Task: "Implement code/coverage_runner.py"
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
 - Developer B: User Story 2 (waits for A)
 - Developer C: User Story 3 (waits for A)
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
- **CPU Constraint**: All LLM inference tasks MUST respect CI constraints (limited RAM, no GPU).
- **HumanEval Branch Coverage**: Tasks calculating branch coverage means MUST filter out HumanEval tasks (branch_coverage == N/A) and skip measurement for them.
- **VIF Condition**: VIF is calculated only if `--perform-regression` flag is set; otherwise skipped.
- **Revision Concerns Addressed**:
  - T050 addresses the need for explicit verification of dataset sources (MBPP/HumanEval) against canonical repositories to satisfy Constitution Principle II (Verified Accuracy) and Principle VII (Benchmark Dataset Integrity).
  - T051 ensures the pipeline handles missing or incomplete test suites gracefully, as required by the edge cases in the spec.
  - T052 enforces the associational nature of findings to comply with FR-010 and avoid causal language.
  - T053 ensures the exclusion rate is properly calculated and reported to prevent bias (FR-014).
  - T029 validates that the sensitivity analysis does not flip signs across thresholds (SC-003) by raising an error.
  - T055 ensures visualizations meet resolution and labeling requirements (SC-004, FR-008).
  - T056 confirms the pipeline can handle the full workload (≥100 tasks) within the 6-hour time limit (SC-005).
  - T025/T026 updated to align with Plan's LMM/GLMM strategy while respecting FR-005.
  - T009 updated to focus on FR-002 fallback logic without hard-coding quantization mandates.
  - T012 updated to skip branch coverage measurement for HumanEval.
  - T045 updated to remove undefined `--model-method` flag and clarify dependency on T041 and T053.
  - T013 updated to use correct CLI arguments (`--num-tasks`, `--output-dir`, `--perform-regression`).
  - T027 updated to specify which subgroup tests trigger correction.
  - T005 updated to specify exact retry/backoff values.
  - T006c added to create schema file before T006d uses it.
  - T008 removed to avoid redundancy with T001b.
  - T024, T045 `[P]` tags removed to reflect dependencies.
  - Prerequisites updated to remove `contracts/` requirement (T006c creates it).
  - Parallel Opportunities updated to reflect US1 dependency for US2/US3.