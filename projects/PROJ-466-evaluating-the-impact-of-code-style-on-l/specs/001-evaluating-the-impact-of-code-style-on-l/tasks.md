# Tasks: Evaluating the Impact of Code Style on LLM Code Generation Diversity

**Input**: Design documents from `/specs/001-eval-code-style-diversity/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure.

- [X] T001 Create project structure per implementation plan (`code/`, `tests/`, `data/`, `config/`, `specs/`)
- [X] T002 [P] Initialize Python 3.11 virtual environment and create `code/requirements.txt` with pinned versions (transformers, torch-cpu, datasets, networkx, scipy, pandas, pytest)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. **Depends on Phase 1 completion.**

- [X] T004 [P] Create prompt templates in `code/prompts/neutral.txt`, `code/prompts/pep8.txt`, `code/prompts/minified.txt` matching style profiles in spec
- [X] T005 [P] Create `config/analysis.yaml` defining seeds (42), thresholds (α), **batch size start = 1**, and timeout limits (moderate duration)
- [X] T006 [P] Implement `code/config/loader.py` to load YAML config and validate required keys
- [X] T007 [P] Create `code/utils/logger.py` for structured logging (memory, timeouts, errors) and `memory_log.json` initialization
- [X] T008 [P] Implement `code/utils/timeout_decorator.py` to enforce **5-minute** per-task limits and handle graceful skips
- [X] T009 [P] Implement `code/utils/metrics_utils.py` for AST parsing safety and zero-variance detection **utility functions** (helper logic, not full pipeline logic)
 - **Verification**: Ensure `metrics_utils.py` exports `calculate_zero_variance` and `safe_ast_parse` functions.

**Checkpoint**: Foundation ready - spec is aligned with plan, user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute Generation & Filtering Pipeline (Priority: P1) 🎯 MVP

**Goal**: Generate code samples for HumanEval tasks under style constraints and filter for functional correctness.

**Independent Test**: Run the pipeline for HumanEval tasks with the "Strict PEP8" profile; verify that the system outputs a CSV containing only samples that pass the associated unit tests, along with their raw source code.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Write failing unit test for prompt loading and validation in `tests/unit/test_prompts.py`
- [X] T012a [P] [US1] **Write** failing integration test in `tests/integration/test_generation.py`. **Specific Assertion**: The test must assert that the generation loop triggers a timeout error when a task takes >5 minutes. **Dependencies**: None (Writing phase). **Note**: This task is for **writing** the test only.
- [X] T012b [US1] **Run** the integration test written in T012a. **Dependencies**: T013, T014, T014b, T015, T015a, T016a. **Note**: This task is for **execution** of the test, which must occur AFTER implementation tasks.

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/generation/loader.py` to download `openai/human-eval` via `datasets` library and cache to `data/raw/humaneval/`. **Dependency**: T004, T005.
- [X] T014 [US1] Implement `code/generation/generator.py` generation loop: generate **20** samples per task per style (T=0.7, seed=42). **Dependency**: T013.
- [X] T014b [US1] **Verify Sample Count**: Implement `code/generation/generator.py` to explicitly verify that the generated sample count per task/style is exactly **20**. **Logic**: If count != 20, **LOG** "Sample Count Mismatch: Expected 20, Got {count}", **ABORT** the generation for that task, and raise an exception to halt the pipeline. **Dependency**: T014. **Traceability**: Satisfies FR-003 strict sampling constraint.
- [X] T015 [US1] Implement `code/generation/generator.py` timeout integration using `code/utils/timeout_decorator.py` to enforce a **5-minute** timeout per task. **Log timeout errors** to `data/logs/pipeline.log` with format `ERROR [TIMEOUT] Task {task_id} timed out after 5m` and skip the task. **Dependency**: T008, T014.
- [X] T015a [US1] Implement `code/generation/tester.py` to execute generated code against HumanEval unit tests and capture pass/fail status. **Dependency**: T014. **Traceability**: Satisfies FR-004 and Plan.md Phase 2 T014.
- [X] T016a [US1] Implement `code/generation/pipeline.py` to atomically write the raw samples from the buffer to `data/processed/samples_all.csv`. **Implementation Detail**: Write to a temporary file (e.g., `samples_all.tmp.csv`), then rename to `samples_all.csv` to ensure atomicity. **This task creates the final `samples_all.csv` artifact.** **Verification**: Before writing, verify that the count of samples per task/style is balanced (per FR-003). If count != 20, log error and abort. **Dependency**: T015a.
- [X] T017a [US1] Implement `code/generation/pipeline.py` to create a **new file** `data/processed/samples_valid.csv` by filtering `data/processed/samples_all.csv`. **Implementation Detail**: Read `samples_all.csv`, filter rows where `pass_status` is True, write to `samples_valid.csv`. **Do NOT modify `samples_all.csv` in place.** **Verification**: Verify that the filtered file contains only rows with `pass_status=True` and log the final count of valid samples. **Dependency**: T016a.
- [ ] T024a [US1] **Compute Pre-Filter Metrics**: Implement `code/analysis/metrics.py` to compute metrics for **ALL generated samples** by reading `data/processed/samples_all.csv` (ignoring `pass_status` column) and saving to `data/processed/metrics_all.csv`. **Aggregation**: Metrics must be **aggregated per task/style** (mean AST, mean entropy). **Dependency**: T016a. **Note**: This runs BEFORE the pass rate check to ensure survivorship bias data is available.
- [ ] T017b [US1] **Compute Valid Metrics**: Implement `code/analysis/metrics.py` to compute metrics for **VALID samples only** by reading `data/processed/samples_valid.csv` produced by T017a and saving to `data/processed/metrics_valid.csv`. **Aggregation**: Metrics must be **aggregated per task/style** (mean AST, mean entropy). **Dependency**: T017a. **Note**: This runs BEFORE the pass rate check to ensure survivorship bias data is available.
- [ ] T018 [US1] **Check Pass Rate & Survivorship Bias**: Implement `code/generation/pipeline.py` to calculate pass rates and survivorship bias. **Logic 1 (Halt)**: Calculate `pass_rate` for each style group using `samples_all.csv` (count_generated) and `samples_valid.csv` (count_passed). If **any** style group has `pass_rate < 0.01`, **LOG** "Model Incapability: Pass rate < 1%" to `data/logs/pipeline.log`, **SET** a "Model Incapability" flag, and **HALT** the pipeline immediately by calling `sys.exit(1)`. **Logic 2 (Bias)**: Compute the difference in diversity metrics between `samples_all.csv` and `samples_valid.csv` (survivorship bias) and log the result to `data/logs/pipeline.log`. **Verification**: Verify that the process exits with code 1 on incapability and that the log contains the specific error string "Model Incapability: Pass rate < 1%". **This task MUST execute after T016a and T017a**. **Dependency**: T016a, T017a. **Note**: This task enforces the safety gate and FR-012; if triggered, no further analysis proceeds.
- [X] T019 [US1] **Flag Bias**: Implement `code/generation/pipeline.py` to calculate pass rates; if the difference between any two style groups exceeds a substantial threshold (**0.10** or 10 percentage points), set a `bias_flag` variable. **Dependency**: T018 (Status=OK). **Note**: T019 runs after T018.
- [ ] T019b [US1] **Persist Bias Flag**: Implement `code/generation/pipeline.py` to write the `bias_flag` from T019 to a JSON file `data/processed/bias_flag.json` with schema `{"flag": <bool>}`. **Verification**: Assert `bias_flag.json` exists and contains the correct boolean value. **Dependency**: T019. **Traceability**: Ensures T056 can read the bias flag.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compute Structural Diversity Metrics (Priority: P2)

**Goal**: Quantify structural variance of valid code samples using AST edit distance and n-gram entropy.

**Independent Test**: Input a CSV of valid code samples for a single task; verify that the system calculates pairwise AST edit distances and token-level n-gram entropy, outputting a summary metric.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Unit test for AST edit distance calculation (identical samples = 0 distance) in `tests/unit/test_metrics.py`
- [X] T021 [P] [US2] Unit test for n-gram entropy calculation in `tests/unit/test_metrics.py`

### Implementation for User Story 2

- [X] T022a [P] [US2] Implement `code/analysis/metrics.py` n-gram entropy calculation function
- [X] T023a [US2] Implement `code/analysis/metrics.py` AST edit distance calculation using `networkx` graph alignment (Zhang-Shasha or similar)
- [X] T024 [US2] Implement `code/analysis/metrics.py` pairwise computation logic for all valid samples within a task/style group
- [X] T025a [US2] Implement `code/analysis/metrics.py` collinearity check: compute **Spearman** correlation coefficient between AST distance and n-gram entropy (per FR-017) using data from T017b. **Output**: **Write the JSON file** `code/analysis/collinearity_flag.json` to disk with schema `{"flag": <bool>, "suggestion": "Suggestion: Use AST Distance only"}`. **MUST WRITE FILE IN ALL CASES** (True or False) to ensure T056 can read it. **Dependency**: T017b.
- [X] T026a [US2] Implement zero-variance detection in `code/analysis/metrics.py` using logic from T009: log "Zero Variance" warning if a group has no variance. **Dependency**: T017b.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Perform Statistical Comparison & Sensitivity Analysis (Priority: P3)

**Goal**: Determine if differences in diversity scores between styles are statistically significant and robust.

**Independent Test**: Run the analysis on the full set of computed metrics; verify that the statistical module executes, reports p-values, and includes sensitivity plots.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Unit test for Kruskal-Wallis H-test setup and execution in `tests/unit/test_stats.py`
- [X] T028 [P] [US3] Unit test for sensitivity analysis threshold sweep in `tests/unit/test_stats.py`

### Implementation for User Story 3

- [X] T029a [US3] Implement `code/analysis/stats.py` **Kruskal-Wallis H-test** using `scipy` to compare diversity distributions across three style groups (FR-006, US-3) on the full N=164 dataset.
- [X] T030a [US3] Implement `code/analysis/stats.py` post-hoc analysis: perform **Dunn's test with Bonferroni correction** if Kruskal-Wallis is significant (US-3 Acceptance Scenario 1)
- [ ] T031a [US3] Implement sensitivity analysis: sweep α over the set **[0.01, 0.05, 0.1]** and record the count of significant tasks for each. **Output**: **Write the JSON file** `data/processed/sensitivity_results.json` to disk. **MUST WRITE FILE IN ALL CASES** (even if analysis fails, write error status). **Dependency**: T029a.
- [X] T032a [US3] Implement survivorship bias comparison in `code/analysis/stats.py`: compare 'Valid' (from T017b) vs 'All Generated' (from T024a) results and quantify difference. **Dependency**: T017b, T024a.
- [X] T033a [US3] **Implement Power Analysis Calculation**: Implement a script in `code/analysis/power.py` that calculates the required sample size for Kruskal-Wallis (Power analysis uses alpha=0.05, power=0.8, **effect_size=0.25** [Standard Medium Effect]) using `statsmodels.stats.power`. **Deliverable**: Log the calculation steps and the result " (Wikidata Q42506454, https://www.wikidata.org/wiki/Q42506454)" to `data/logs/power_analysis.log`. **Verification**: Assert `data/logs/power_analysis.log` contains the string "Wikidata Q42506454". **Dependency**: T006, T007.
- [X] T033b [US3] **Write Power Analysis Documentation**: Implement a script or manual step to generate the "Power Analysis" section in `specs/001-evaluating-the-impact-of-code-style-on-l/quickstart.md` (or the final report) confirming that N=164 is sufficient for the intended statistical power (0.8) at alpha=0.05, based on the calculation in T033a. **Deliverable**: The text section in the documentation. **Dependency**: T033a. **Traceability**: Satisfies FR-011.
- [X] T033c [US3] **Implement Power Analysis Visualization**: Implement a script in `code/analysis/plotting.py` to read `data/logs/power_analysis.log` and generate a plot showing the relationship between sample size (N) and statistical power (1-β). **Output**: Save to `artifacts/plots/power_analysis.png`. **Verification**: Assert `artifacts/plots/power_analysis.png` exists and size > 0KB. **Dependency**: T033a.
- [ ] T051 [US3] **Implement Sensitivity Analysis Plot Generator**: Implement a script in `code/analysis/plotting.py` to read `data/processed/sensitivity_results.json` (T031a) and generate a line plot (x-axis: α threshold, y-axis: count of significant tasks). **Output**: Save to `artifacts/plots/sensitivity_analysis.png`. **Verification**: Assert `artifacts/plots/sensitivity_analysis.png` exists and size > 0KB. **Dependency**: T031a.
- [ ] T052 [US3] **Implement Bias Flag Visualization**: Implement a script in `code/analysis/plotting.py` to read `data/processed/bias_flag.json` (T019b) and generate a bar chart comparing pass rates per style group with a "Potentially Biased" annotation if flag is true. **Output**: Save to `artifacts/plots/bias_flag.png`. **Verification**: Assert `artifacts/plots/bias_flag.png` exists and size > 0KB. **Dependency**: T019b.
- [X] T053 [US3] **Implement Collinearity Heatmap**: Implement a script in `code/analysis/plotting.py` to read `code/analysis/collinearity_flag.json` (T025a) and the full correlation matrix of all metrics. Generate a heatmap. **Output**: Save to `artifacts/plots/collinearity_heatmap.png`. **Verification**: Assert `artifacts/plots/collinearity_heatmap.png` exists and size > 0KB. **Dependency**: T025a.
- [ ] T054 [US3] **Implement Survivorship Bias Comparison Plot**: Implement a script in `code/analysis/plotting.py` to read `data/processed/metrics_all.csv` (T024a) and `data/processed/metrics_valid.csv` (T017b). Generate a side-by-side boxplot comparing diversity metrics for "All Generated" vs "Valid" samples per style. **Output**: Save to `artifacts/plots/survivorship_bias.png`. **Verification**: Assert `artifacts/plots/survivorship_bias.png` exists and size > 0KB. **Dependency**: T024a, T017b.
- [ ] T055 [US3] **Implement Final Report Assembly**: Implement `code/analysis/reporter.py` to aggregate all generated plots (`artifacts/plots/*.png`), data tables, and statistical results into a single HTML/PDF document. **Logic**: Ensure the report includes: Summary Stats, H-Statistic, Post-hoc, Sensitivity Plot, Survivorship Plot, Bias Flag, Collinearity Suggestion, Power Analysis Plot, and Methodology. **Output**: `artifacts/report.html` and `artifacts/report.pdf`. **Verification**: Assert `artifacts/report.html` and `artifacts/report.pdf` exist and size > 0KB. **Dependencies**: T017b, T024a, T025a, T029a, T030a, T031a, T032a, T033c, T051, T052, T053, T054.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Create `code/main.py` orchestrator to run full pipeline (Setup → Gen → Metrics → Stats → Report)
- [X] T036 [P] Implement `data/processed/` directory structure and ensure all CSVs (samples_all, samples_valid, metrics_all, metrics_valid) are written correctly
- [X] T037 [P] Add SHA256 checksumming for **HumanEval downloaded cached file in `data/raw/`**, all processed CSVs (samples_all, samples_valid, metrics_all, metrics_valid), **final report artifacts (`artifacts/report.html`, `artifacts/report.pdf`)**, and **all generated plots (`artifacts/plots/*.png`)** and record in `state/projects/PROJ-466-evaluating-the-impact-of-code-style-on-l.yaml` under `artifact_hashes` (Data Hygiene). **Clarification**: Checksum the local cached file in `data/raw/`, not the remote source. Do not checksum undefined directories.
- [X] T038 [P] Update `state/` file with execution status, memory logs, and final report path
- [X] T039 [P] Documentation updates in `specs/001-evaluating-the-impact-of-code-style-on-l/quickstart.md`
- [X] T040a [P] Run `pytest` suite and generate JUnit XML report to `tests/results/junit.xml`. **Dependency**: T010, T020, T021, T027, T028.
- [X] T040b [P] **Verify** `tests/results/junit.xml` exists and contains no failures; **Attach** file as completion evidence. **Dependency**: T040a.
- [X] T041a [P] Run pipeline subset and log execution duration to `data/logs/timing.log`. **Dependency**: T035.
- [X] T041b [P] **Verify** `data/logs/timing.log` exists and contains duration < 6 hours; **Enforce**: If duration >= 6 hours, **exit with code 1** and log "Performance Constraint Violated: Runtime exceeded 6 hours". **Attach** file as completion evidence. **Dependency**: T041a.
- [X] T042 [P] [Review Concern] **Implement** dynamic batch sizing logic in `code/generation/generator.py` that probes memory usage and reduces batch size iteratively until RAM limit is respected, logging each reduction step to `data/logs/memory_log.json`. **Dependency**: T014.
- [X] T043 [P] [Review Concern] **Implement** AST parsing error handling in `code/analysis/metrics.py` (try/except around `ast.parse`) for individual samples, log the task_id and style to `data/logs/pipeline.log`, and skip only the failed sample without halting the batch. **Dependency**: T023a.
- [X] T044 [P] [Review Concern] **Implement** zero variance detection in `code/analysis/stats.py` before running Kruskal-Wallis, skip the test for that group, log "Zero Variance" warning, and do not raise a runtime error. **Dependency**: T029a.
- [X] T045 [P] [Review Concern] **Implement** strict error handling in `code/generation/loader.py` using `datasets.load_dataset("openai/human-eval")` that raises an exception if the download fails (no synthetic fallback), ensuring the run fails loudly if the real source is unreachable. **Dependency**: T013.
- [ ] T046 [P] [Review Concern] **Implement** a dedicated section in `code/analysis/reporter.py` for the final PDF/HTML report showing the "Sensitivity Analysis" sweep of α thresholds and the corresponding count of significant tasks, as required by FR-007. **Dependency**: T031a.
- [X] T047 [P] [Review Concern] **Implement** robust error handling in `code/analysis/power.py` to gracefully handle cases where the `statsmodels` power calculation fails due to missing effect size data, logging a clear warning and defaulting to the documented N=164 assumption with an explicit note in the log. **Dependency**: T033a.
- [ ] T048 [P] [Review Concern] **Implement** a validation step in `code/main.py` that checks for the existence of all required intermediate artifacts (samples_all.csv, samples_valid.csv, metrics_all.csv, metrics_valid.csv, collinearity_flag.json, sensitivity_results.json, bias_flag.json) before proceeding to the reporting phase, failing loudly with a descriptive error if any are missing. **Dependency**: T035, T025a, T031a, T019b.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on US1 completion** (specifically T016a for T017b and T017a for T017c)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Depends on US2 completion** (specifically T017b/T025a)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, **only US1 can start**. **US2 and US3 must wait for US1 to finish**.
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members **only if dependencies are met**.
- **Note**: T012a (Integration Test Write) is parallel with T013-T016. T012b (Integration Test Run) must run AFTER T013-T016.

---

## Parallel Example: User Story 1

```bash
# Launch all tasks for User Story 1 together (if tests requested):
Task: "Write failing unit test for prompt loading and validation in tests/unit/test_prompts.py"
Task: "Write failing integration test in tests/integration/test_generation.py asserting timeout triggers on >5m generation"
# Note: T012b (Integration Test Run) must run AFTER T013-T016, not in parallel.

# Launch all models for User Story 1 together:
Task: "Implement code/generation/loader.py to download openai/human-eval..."
Task: "Implement code/generation/generator.py with dynamic batch sizing..."
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (generate tasks, filter, verify CSV)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Metrics on valid samples)
4. Add User Story 3 → Test independently → Deploy/Demo (Stats & Report)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Generation & Filtering)
 - Developer B: Prepare US2 code (write tests, skeleton) but **WAIT for US1 completion**
 - Developer C: Prepare US3 code (write tests, skeleton) but **WAIT for US2 completion**
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
- **Critical Alignment**: This task list aligns with **plan.md (20 samples)** and **FR-017 (Spearman correlation)**. The spec.md FR-003 and FR-017 have been **verified** in the planning phase.
- **Data Hygiene**: T016a generates to buffer, T016a writes final `samples_all.csv`. T017a creates new `samples_valid.csv`. No in-place updates.
- **Gate Logic**: T018 is a check task (returns status). **No fallback** (T018c removed). T018 runs after T017a (not T024a) to ensure data exists for survivorship bias. **CRITICAL**: T018 HALTS on low pass rate.
- **Review Concerns Addressed**: Tasks T042-T048 explicitly address edge cases (memory, timeout, AST errors, zero variance, data source failure, sensitivity reporting, power analysis robustness, artifact validation) to ensure robust execution on the free-tier runner.
- **Spec Alignment**: Phase 0 (T001a-c) removed. Spec is immutable.
- **Data Flow**: T025a writes `collinearity_flag.json`; T056 reads it. T017b and T024a are parallel; T018 runs after T017a/T016a.
- **Statistical Power**: N=164 is mandatory [Resolved: effect_size=0.25 used]. No subset fallback is permitted.
- **New Tasks**: T014b (Count Verification), T033b (Power Analysis Documentation), T033c (Power Analysis Visualization), T019b (Persist Bias Flag) added to address FR-003, FR-011, and FR-016 gaps.
- **Removed Redundancy**: Tasks T049-T100 removed to eliminate scope creep and circular dependencies. Logic consolidated into primary tasks (T042, T059, T056).
- **Visualization Tasks**: T051-T055 added to Phase 5 to ensure required plots are generated for the final report (T056).
- **T034 Removal**: T034 (Final Report Generation) was removed and replaced by T056 (Final Report Assembly) to resolve circular dependencies. T056 is the final aggregation step.
- **T009 vs T026a**: T009 provides utility functions; T026a implements pipeline logic.
- **T012 Split**: T012a (Write) and T012b (Run) to clarify execution order.
