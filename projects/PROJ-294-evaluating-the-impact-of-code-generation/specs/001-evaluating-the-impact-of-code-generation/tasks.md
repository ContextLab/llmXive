# Tasks: Evaluating the Impact of Code Generation Models on Code Testability

**Input**: Design documents from `/specs/294-evaluating-the-impact-of-code-generation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. [UNRESOLVED-CLAIM: c_018388b7 — status=not_enough_info] Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `data/`, `results/`, `tests/`, `docs/` at repository root (per `plan.md` structure)
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project structure defined in `plan.md`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create directory structure at `projects/PROJ-294-evaluating-the-impact-of-code-generation/`: `code/`, `data/`, `results/`, `tests/`, `docs/`. **Constraint**: Create parent directories if missing (e.g., `mkdir -p projects/PROJ-294-evaluating-the-impact-of-code-generation/code/`). **Constitution**: Aligns with Constitution Reproducibility Requirements (Principle V) path structure. (Plan: Project Structure)
- [ ] T001b [P] Create `state/` directory at `projects/PROJ-294-evaluating-the-impact-of-code-generation/`. **Constraint**: Distinct from T001a to ensure clear separation of state tracking from data/results. (Plan: Project Structure)
- [ ] T001c [P] Create `__init__.py` files in `code/`, `tests/`, `tests/unit/`, `tests/integration/`. (Plan: Project Structure)
- [X] T002 [P] Initialize a Python project with pinned dependencies in `code/requirements.txt`. (FR-007, Plan: Dependencies)
- [X] T003 [P] Configure linting (flake8/black). **Deliverable**: Create `.flake8` with `max-line-length=88` and `pyproject.toml` with black configuration. (Plan: Testing)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Setup logging infrastructure in `code/utils/logger.py` with timestamp and task ID tracking (FR-007). (FR-007)
- [ ] T004b [P] **Performance Instrumentation (Hooks)**: Implement logging hooks in `code/utils/logger.py` to capture `generation_duration_ms` and `tasks_per_minute` for each generation task. **Constraint**: Hooks must emit structured log events. Do NOT implement aggregation logic here. (SC-001, SC-002)
- [ ] T004c [P] **Performance Instrumentation (Aggregation)**: Implement logic to aggregate metrics from logs, write them to `data/analysis/performance.json`, and validate against a documented capacity threshold (e.g., >= 10 tasks/min). **Constraint**: This task implements the threshold validation previously in T004b. (SC-001, SC-002)
- [X] T005 [P] Implement SHA256 checksum utility in `code/utils/hash_utils.py` for dataset and artifact verification (FR-001, FR-011). (FR-001, FR-011)
- [ ] T015a [US1] **Execution Environment Setup**: Implement `code/sandbox.py` to create an isolated execution environment for HumanEval test suites. **Implementation**: Use Python's `subprocess` module with `preexec_fn` to call `resource.setrlimit(resource.RLIMIT_AS, (2*1024*1024*2*1024*1024*1024, 2*1024*1024*1024))` to enforce a **memory limit**, ensuring sufficient headroom on the GitHub Actions runner for OS and Python overhead. **Timeout**: Enforce a strict **timeout** per task execution (per FR-005). **Output**: A reusable sandbox context manager class `TestSandbox` in `code/sandbox.py`. **Constraint**: This task MUST create `data/sandbox/` directory if needed. **Dependency**: T001a, T005. **Note**: This task ONLY provides the execution environment; it does NOT compute metrics. (FR-005, Plan: Testability Evaluation)
- [ ] T008 [P] Create data directory structure: `data/raw/`, `data/generated/`, `data/analysis/`. **Constraint**: Do NOT create `state/` here; it is created in T001b at the root level. (Plan: Project Structure)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Paired Analysis Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download HumanEval, generate LLM code, compute metrics (Complexity, Halstead, Static/Dynamic Coverage), and produce paired JSON dataset.

**Independent Test**: Run the pipeline on the full HumanEval dataset (N=164). [UNRESOLVED-CLAIM: c_3e6cf316 — status=not_enough_info] Verify the following:
1. `data/analysis/base_metrics.json` exists and contains `cyclomatic_complexity`, `halstead_volume`, `branch_coverage_potential`, and `pass_rate` for **all tasks** (unfiltered).
2. `data/analysis/valid_metrics.json` exists and contains **only** tasks with `pass_rate` >= 0.80.
3. `data/analysis/valid_task_ids.json` exists and contains the exact list of task IDs filtered by the 0.80 threshold.
4. All metrics are floats >= 0, and `pass_rate` is a float between 0 and 1.

### Sub-Phase 3.1: Data Ingestion

- [ ] T010 [US1] Implement `code/download_data.py` to download the **full** HumanEval dataset from HuggingFace (`openai/openai_humaneval`) using a **specific commit SHA** resolved dynamically from the dataset card or `data/metadata.yaml` (not hardcoded). Save raw data directly as `data/raw/humaneval.parquet`. **Implementation**: Use `datasets.load_dataset(...)` to fetch, convert the resulting Dataset object to a `pandas.DataFrame`, and use `df.to_parquet('data/raw/humaneval.parquet')`. Compute SHA256 for the parquet file. **Verification**: The script MUST verify that the recorded SHA in `metadata.yaml` matches the actual dataset fetched; if mismatch, **raise a critical exception and halt execution** to enforce Constitution Principle I (Reproducibility). **Constraint**: Implement exponential-backoff retry logic and a fixed timeout per task. **FAIL LOUDLY**: If the download fails, raise an exception. (FR-001, FR-011, Plan: Large real datasets: STREAM the real data)
- [ ] T011 [US1] Implement `code/extract_human_reference.py` to extract human reference code from `data/raw/humaneval.parquet` and save to `data/generated/human_samples.json`. **Constraint**: Must preserve `task_id` and `prompt` fields. **Output**: JSONL file with human solutions. **Dependency**: T010. (FR-005, Plan: Paired Statistical Design)

### Sub-Phase 3.2: Code Generation

- [ ] T012 [US1] Implement `code/generate_code.py` to load **Primary Model: `Salesforce/codegen-mono-4b`** (8-bit quantized) on CPU. **Fallback**: If the large model fails (OOM or timeout), fall back to `Salesforce/codegen-mono-350M`. **Constraint**: Ensure `device="cpu"` is explicitly set. **Template**: Create `code/prompt_templates/humaneval.txt` if missing, using the standard HumanEval prompt format. **Timeout**: Implement exponential backoff retry logic with a **60-second timeout** per task. **Output**: Save generated code to `data/generated/codegen_samples.json`. (FR-002)
- [ ] T013 [US1] Implement error handling in `code/generate_code.py` to log failures to `code/errors.log` and mark samples as missing. **Logic**: Catch `RuntimeError`, `TimeoutError`, and `MemoryError`. Log the task_id and error message. In the output JSON, set `generated_code` to `null` and `status` to `'failed'` for the specific task. (FR-002)

### Sub-Phase 3.3: Metric Extraction

- [ ] T015 [US1] **Test Execution**: Implement logic in `code/analyze_metrics.py` to execute test suites against the HumanEval test suite for **both human reference samples (from T011) and LLM samples (from T012)** using the sandbox from T015a. **Metric**: Record `pass_rate` as a **float** (`passed_tests / total_tests`) per sample. **Constraint**: Operate on **all tasks** in the full HumanEval dataset. Do NOT filter out tasks based on pass_rate at this stage. **Output**: Intermediate JSON with `pass_rate` as a float. **Dependency**: T011, T012, T015a. (FR-005)
- [ ] T014a [US1] **Metric Extraction (Static - Cyclomatic)**: Implement `code/analyze_metrics.py` to run `radon cc --json` on samples from `data/generated/human_samples.json` and `data/generated/codegen_samples.json` for **ALL 164 tasks** (unfiltered). **Constraint**: Must operate on the **full dataset** to support the 'Full-Sample Analysis' requirement. Do NOT restrict to filtered tasks. **Output**: Intermediate JSON with `cyclomatic_complexity`. **Dependency**: T011, T012, T015. (FR-003)
- [ ] T014b [US1] **Metric Extraction (Static - Halstead)**: Implement `code/analyze_metrics.py` to run `radon hal --json` on samples from `data/generated/human_samples.json` and `data/generated/codegen_samples.json` for **ALL 164 tasks** (unfiltered). **Constraint**: Must operate on the **full dataset**. Do NOT restrict to filtered tasks. **Output**: Intermediate JSON with `halstead_volume`. **Dependency**: T011, T012, T015. (FR-003)
- [ ] T016a [US1] **Metric Extraction (Static - Branch Coverage)**: Implement `code/analyze_metrics.py` to run `radon` to count branches on samples from `data/generated/human_samples.json` and `data/generated/codegen_samples.json` for **ALL 164 tasks** (unfiltered). **Constraint**: Must operate on the **full dataset**. Do NOT restrict to filtered tasks. **Output**: Intermediate JSON with `branch_coverage_potential`. **Dependency**: T011, T012, T015. (FR-003, Constitution Principle VI)
- [ ] T016b [US1] **Metric Processing (Branch Coverage)**: Implement logic in `code/analyze_metrics.py` to ensure the output field is named exactly `branch_coverage_potential` (matching the Spec Data Model). **Constraint**: Ensure `branch_coverage_potential` is a float >= 0. **Dependency**: T016a. (FR-003)
- [ ] T017a [US1] **Aggregation (Full Sample)**: Implement aggregation in `code/analyze_metrics.py` to produce `data/analysis/base_metrics.json` containing **ALL 164 tasks** (unfiltered, including those with pass_rate < 0.80). Used for **Primary Analysis** to avoid selection bias. **Schema**: Must contain `task_id`, `source_type` (values: `'human'`, `'codegen'`), `cyclomatic_complexity`, `halstead_volume`, `branch_coverage_potential`, and `pass_rate`. **Constraint**: Ensure `branch_coverage_potential` is the final field name. Verify no record has `null` for `cyclomatic_complexity` OR `halstead_volume`. **Dependency**: T014a, T014b, T016b, T015. (FR-005, Plan: Full-Sample Analysis)
- [ ] T017b [US1] **Aggregation (Filtered)**: Implement logic in `code/analyze_metrics.py` to read `data/analysis/base_metrics.json`, filter tasks with `pass_rate` >= 0.80, and generate `data/analysis/valid_metrics.json` and `data/analysis/valid_task_ids.json`. **Constraint**: This task implements the FR-005 filter requirement for the Secondary Analysis. **Output**: JSON file containing list of valid task IDs as a JSON array of strings (e.g., `["HumanEval/0", "HumanEval/1"]`). **Dependency**: T017a. (FR-005)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (including MDES data in `power_results.yaml` via T024)

---

## Phase 4: User Story 2 - Statistical Comparison and Hypothesis Testing (Priority: P2)

**Goal**: Perform Wilcoxon Signed-Rank tests on the paired dataset (Baseline: Human vs CodeGen).

**Independent Test**: Feed mock paired datasets; verify p-values are calculated correctly and power analysis reports required n ≥ 38 and The power analysis reports achieved power ≥ 0.8.

### Implementation for User Story 2

- [ ] T020 [US2] Implement `code/statistical_tests.py` with Wilcoxon Signed-Rank test for continuous metrics: **Cyclomatic Complexity, Halstead Volume, AND branch_coverage_potential**. **Parameters**: Use a **two-tailed** test with `alpha=0.05 (1501.05788, https://arxiv.org/abs/1501.05788)` (Wikipedia: P-value). **Dependency**: T017a (Reads `base_metrics.json`). (FR-004)
- [ ] T024 [US2] **Sensitivity Analysis (MDES & Achieved Power)**: Implement Minimum Detectable Effect Size (MDES) calculation in `code/statistical_tests.py` for the **fixed sample size N=164**, alpha=0.05, power=0.80. **Constraint**: This is a **Fixed-Sample Sensitivity Analysis** to validate the study design. **Additional Requirement**: Implement **Achieved Power** (post-hoc) calculation with **% Confidence Intervals** based on the **actual observed effect sizes** and the **bias-adjusted sample size** (accounting for missing data as per Plan's Missing Data & Bias Analysis Protocol). **Output**: Save MDES and Achieved Power results to `data/analysis/statistical_results.json`. **Dependency**: T017a, T020. (FR-008, SC-005)
- [ ] T046 [US2] **Success Criteria Validation**: Implement logic in `code/statistical_tests.py` to evaluate the results against the **Functional Requirements** (FR-004 for statistical significance, FR-008 for power analysis) and the Plan's **Key Methodological Corrections** (paired analysis, complete-case coverage). Generate a `state/validation_results.yaml` file with boolean PASS/FAIL status for each requirement. **Dependencies**: T020, T024. (FR-004, FR-008)
- [ ] T026 [US2] Write unit tests for statistical functions using mock data with known p-values (tests/unit/test_statistics.py). (Plan: Testing)
- [ ] T027 [US2] Write integration test verifying the full statistical report generation from `metrics.json` (tests/integration/test_stats_pipeline.py). (Plan: Testing)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (Baseline analysis complete)

---

## Phase 5: User Story 3 - Visualization, Reporting, and Sensitivity Analysis (Priority: P3)

**Goal**: Generate automated Markdown report with figures, and perform sensitivity analysis using CodeLlama models.

**Independent Test**: Verify `results_report.md` contains all figures, tables, and sensitivity analysis results; verify API fallback logic works.

### Implementation for User Story 3

- [ ] T030 [US3] Implement `code/report_generator.py` to create histograms and boxplots using `matplotlib` for all continuous metrics. **Constraint**: Ensure `results/figures/` directory exists (create if missing) before writing files. (FR-006)
- [ ] T031a [US3] **Citation Extraction**: Implement `code/extract_citations.py` to scan the Jinja2 template (`results_report.md.j2`) and `state/` for all citations, extract them into a structured format, and save to `state/citations.yaml`. **Constraint**: Must include title, URL, and source for each citation. **Output**: `state/citations.yaml`. **Dependency**: T030. (FR-010)
- [ ] T031 [US3] Implement `code/report_generator.py` with Jinja2 template to compile `results_report.md` including figures, tables, and power analysis. **Constraint**: The template must explicitly render the MDES results from T024 and the validation status from T046 in a dedicated "Sensitivity Analysis" and "Validation Status" section. **Dependency**: T030, T017a, T046, T024, T031a. (FR-006)
- [ ] T031b [US3] **Sensitivity Visualization Verification**: Implement logic in `code/report_generator.py` to verify that MDES results are correctly rendered in the report with distinct labels and that the `source_type` mapping matches the data in `metrics.json`. **Dependency**: T031, T017a. (FR-006)
- [ ] T033 [US3] Write unit tests for `code/report_generator.py` to verify figure generation and template rendering (tests/unit/test_report.py). (Plan: Testing)
- [ ] T034 [US3] Write integration test for the full pipeline from `metrics.json` to `results_report.md` (tests/integration/test_full_pipeline.py). (Plan: Testing)
- [ ] T056 [US3] **Citation Validation Wrapper**: Implement `code/validate_citations.py` as a wrapper script that invokes the external **Reference-Validator Agent** via `subprocess.run`. **Logic**: Parse `state/citations.yaml`, construct the subprocess command (`reference-validator --input state/citations.yaml --output state/validation_report.yaml`), capture the YAML report, and parse the results. **Constraint**: **FAIL LOUDLY**: If the agent is missing (`FileNotFoundError`) or returns a failure status, raise a critical exception and halt execution immediately. This enforces Constitution Principle II (Verified Accuracy) as a blocking gate. **Output**: `state/validation_report.yaml`. (FR-010)
- [ ] T050 [US3] **Artifact Integrity Verification**: Implement `code/validate_artifacts.py` to compute SHA256 hashes for all files in `data/generated/` and `data/analysis/` and store them in `state/artifact_hashes.yaml`. **Constraint**: Must run after T017a and T031. (FR-011)

### Sub-Phase 5.1: CodeLlama Sensitivity Analysis (Mandatory for FR-009)

**Purpose**: Implement sensitivity analysis with CodeLlama models as mandated by FR-009. These tasks require CPU execution.

**Note**: The primary model (CodeGen-350M) is CPU-tractable and handled in Phase 3. This sub-phase is strictly for the CodeLlama sensitivity analysis (FR-009) which requires CPU execution.

- [ ] T052 [US3] **CodeLlama Sensitivity Implementation**: Implement `code/generate_code_llama.py` to generate code samples using a **quantized CodeLlama model** (specifically from repository **`TheBloke/CodeLlamaB-GGUF`**, commit hash **`main`** or specific commit if pinned) and save them to `data/generated/llama_samples.json`. Use prompt template from `code/prompt_templates/humaneval.txt`. **Output**: JSONL file containing generated code with task ID, source type (llama), and timestamp. **Constraint**: Use `llama-cpp-python` with `n_ctx=2048` and `n_threads=4`. **Verification**: The script MUST verify that the loaded model has a parameter count consistent with the target scale (large) and matches the pinned repository/commit; if mismatch, **raise an error** to ensure CPU feasibility and reproducibility compliance (Constitution Principle VII). **Dependency**: T015 (Test Execution on full sample). (FR-009)
- [ ] T053a [US3] **CodeLlama Metric Extraction**: Implement `code/analyze_metrics.py` to run `radon` (static) and `coverage.py` (dynamic) specifically on `data/generated/llama_samples.json` to generate `cyclomatic_complexity`, `halstead_volume`, and `branch_coverage_potential`. **Constraint**: Reuse existing logic from T014a, T014b, T016b. **Output**: Intermediate metrics for llama samples. **Dependency**: T015. (FR-009)
- [ ] T053b [US3] **Sensitivity Comparison Logic**: Implement logic in `code/analyze_metrics.py` to **merge** the llama metrics into `data/analysis/base_metrics.json` (read from T017a) and write the result to `data/analysis/full_sample_metrics.json` (appending to existing Human/CodeGen data) with the new `source_type` value `'llama'`. **Constraint**: Do not overwrite existing data. **Dependency**: T017a, T053a. (FR-009)
- [ ] T054 [US3] **Cross-Model Statistical Tests**: Extend `code/statistical_tests.py` to perform **Levene's Test** for variance differences between `codegen` and `llama` in addition to the baseline `human` vs `codegen` comparison. **Additional Logic**: Explicitly calculate the **observed variance difference magnitude** (absolute value) and compare it against the **0.05 threshold** defined in FR-009/SC-006. Report both the p-value, the **measured variance difference magnitude**, and a boolean `variance_exceeds_threshold` status in `statistical_results.json`. **Dependency**: T017a, T053b. (FR-009, SC-006)
- [ ] T055 [US3] **CPU Execution Wrapper**: Create `code/run_cpu_pipeline.py` as a script entry point that orchestrates the CPU-dependent tasks (T052, T053a, T053b) and handles environment detection for the execution stage. **Constraint**: Must use `llama-cpp-python` with quantized GGUF on CPU. (FR-009)

**Checkpoint**: All user stories should now be independently functional (Baseline report complete + Sensitivity Analysis)

---

## Phase 6: Revision & Correction (Addressing Reviewer Concerns)

**Purpose**: Address specific unresolved claims and review concerns regarding data flow, metric naming, and statistical rigor.

- [ ] T061 [US1] **Metric Naming Consistency**: Audit `code/analyze_metrics.py` to ensure the field name `branch_coverage_potential` is used consistently in all output JSON files (`base_metrics.json`, `valid_metrics.json`, `statistical_results.json`). Replace any instances of `static_branch_count` or `branch_coverage` with `branch_coverage_potential`. **Rationale**: Ensures alignment with Spec Data Model and FR-003. (Spec: Data Model, FR-003)
- [ ] T062 [US2] **Statistical Rigor Update**: Update `code/statistical_tests.py` to explicitly calculate and report **Achieved Power** (post-hoc) with % Confidence Intervals for the Wilcoxon test, in addition to the Fixed-Sample MDES (T024). **Constraint**: Use `statsmodels.stats.power` or equivalent. **Rationale**: Addresses Plan requirement for "Achieved Power and Confidence Intervals" to complement the MDES. (Plan: Statistical Comparison, FR-008)
- [ ] T063 [US3] **Bias Analysis Implementation**: Implement `code/bias_analysis.py` to perform Little's MCAR test on task difficulty proxies (e.g., prompt length) comparing included vs. excluded tasks (those with generation failures or parse errors). **Additional Requirement**: Generate a **narrative report** in `data/analysis/bias_report.json` that explicitly describes the **direction and magnitude** of potential bias, comparing the distribution of task difficulty between included and excluded pairs, as required by the Plan's 'Missing Data & Bias Analysis Protocol'. **Output**: Save results to `data/analysis/bias_report.json` (including a `narrative_summary` field). **Rationale**: Addresses "Missing Data & Bias Analysis Protocol" in Plan. (Plan: Missing Data & Bias Analysis Protocol)
- [ ] T064 [US3] **Dynamic Coverage Verification**: Add a specific test task in `tests/integration/test_metrics.py` to verify that `coverage.py` is actually generating dynamic branch coverage traces (not just static counts) for a known sample. **Constraint**: The test must assert that the `branch_coverage_potential` value differs from the static `radon` branch count for a sample with conditional logic. **Rationale**: Ensures Constitution Principle VI (Testability Evaluation) is met by verifying dynamic vs. static distinction. (Constitution: Principle VI)

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