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

- [ ] T001a [P] Create directory structure: `projects/294-evaluating-code-testability/` with subdirectories `code/`, `data/`, `state/`, `results/`, `tests/`, `docs/`. **Constraint**: Create parent directories if missing (e.g., `mkdir -p code/ data/ state/ results/ tests/ docs/`). (Plan: Project Structure)
- [ ] T001b [P] Create `__init__.py` files in `code/`, `tests/`, `tests/unit/`, `tests/integration/`. (Plan: Project Structure)
- [X] T002 [P] Initialize a Python project with pinned dependencies in `code/requirements.txt`. (FR-007, Plan: Dependencies)
- [X] T003 [P] Configure linting (flake8/black). **Deliverable**: Create `.flake8` with `max-line-length=88` and `pyproject.toml` with black configuration. (Plan: Testing)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Setup logging infrastructure in `code/utils.py` with timestamp and task ID tracking (FR-007). (FR-007)
- [X] T005 [P] Implement SHA256 checksum utility in `code/utils.py` for dataset and artifact verification (FR-001, FR-011). (FR-001, FR-011)
- [ ] T015a [P] **Execution Environment Setup**: Implement `code/sandbox.py` to create an isolated execution environment for HumanEval test suites using **subprocess with strict resource limits** (memory_limit=2GB via `resource` module, timeout=30s) to prevent network access and ensure stability, compatible with GitHub Actions Free Tier. **Output**: A reusable sandbox context manager. **Dependency**: T005. (FR-005, Plan: Testability Evaluation)
- [ ] T008 [P] Create data directory structure: `data/raw/`, `data/generated/`, `data/analysis/`. **Constraint**: Do NOT create `state/` here; it is created in T001a at the root level. (Plan: Project Structure)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Paired Analysis Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download HumanEval, generate LLM code, compute metrics (Complexity, Mutation Score, Coverage), and produce paired JSON dataset.

**Independent Test**: Run the pipeline on the full HumanEval dataset (N=164). Verify that `data/analysis/metrics.json` contains `cyclomatic_complexity`, `halstead_volume`, `branch_coverage_pct`, and `pass_rate` for every valid pair, with n=164 (or n < 164 only if specific tasks fail execution).

### Sub-Phase 3.1: Data Ingestion

- [ ] T010 [US1] Implement `code/download_data.py` to download the **full** HumanEval dataset from HuggingFace (`openai/openai_humaneval`) using **`revision="v1.0.0"`** (or a specific commit SHA if `v1.0.0` is unavailable) to ensure deterministic versioning. **Constraint**: Must NOT fall back to synthetic data; must raise a `RuntimeError` with a clear message "Failed to download verified real source" if the download fails after max retries. **Output**: Save raw data as `data/raw/humaneval_raw.json` (preserving original format) and convert to `data/generated/humaneval.parquet` (derived artifact) using `pandas` and `pyarrow`. Compute SHA256 for both. Record the exact version `v1.0.0` (or specific SHA) in `data/metadata.yaml`. (FR-001, FR-011, Plan: Large real datasets: STREAM the real data)
- [ ] T011 [US1] Implement `code/extract_human_reference.py` to extract human reference code from `data/raw/humaneval_raw.json` (or `humaneval.parquet`) and save to `data/generated/human_samples.json`. **Constraint**: Must preserve `task_id` and `prompt` fields. **Output**: JSONL file with human solutions. **Dependency**: T010. (FR-005, Plan: Paired Statistical Design)

### Sub-Phase 3.2: Code Generation

- [ ] T012 [US1] Implement `code/generate_code.py` to load `Salesforce/codegen-350M-mono` on CPU and generate code for **all tasks** in `data/generated/humaneval.parquet`. **Constraint**: Must implement **batched processing (batch_size=8)** to respect CPU memory limits and the Extended-duration performance goal. Must implement **retry logic with exponential backoff** as mandated by FR-002. Must use prompt template from `code/prompt_templates/humaneval.txt`. **Output**: Save generated code to `data/generated/codegen_samples.json`. **GPU Escape Hatch**: If CPU execution fails (timeout > 300s or OOM regex match: "OutOfMemory", "CUDA out of memory"), log error and exit with `EXIT_GPU_RETRY = 184` to signal execution stage to re-run on GPU. **Dependency**: T010. (FR-002)
- [ ] T013 [US1] Implement error handling in `code/generate_code.py` to log failures to `code/errors.log` and mark samples as missing. **Logic**: Catch `RuntimeError`, `TimeoutError`, and `MemoryError`. Log the task_id and error message. In the output JSON, set `generated_code` to `null` and `status` to `'failed'` for the specific task. (FR-002)

### Sub-Phase 3.3: Metric Extraction

- [ ] T014a [US1] **Metric Extraction (Static)**: Implement `code/analyze_metrics.py` to run `radon cc --json` and `radon hal --json` on all samples (Human, CodeGen) from `data/generated/human_samples.json` and `data/generated/codegen_samples.json`. **Constraint**: Must operate on **all tasks** in the full HumanEval dataset. **Output**: Intermediate JSON with `cyclomatic_complexity`, `halstead_volume`, `halstead_components`. **Dependency**: T011, T012. (FR-003)
- [X] T014b [US1] **Metric Processing**: Implement logic in `code/analyze_metrics.py` to parse `radon` output, map `cc` to `cyclomatic_complexity`, and calculate `halstead_volume` from `hal` components. **Constraint**: Store all extracted Halstead components. **Dependency**: T014a. (FR-003)
- [X] T015 [US1] Implement logic in `code/analyze_metrics.py` to execute `pytest` against the HumanEval test suite for **both human reference samples (from T011) and LLM samples (from T012)** using the sandbox from T015a and record the binary `pass_rate` (1 = all tests passed, 0 = any failure) per sample. **Constraint**: Operate on **all tasks** in the full HumanEval dataset. **Output**: Intermediate JSON with `pass_rate`. **Dependency**: T014a, T015a, T011. (FR-005)
- [X] T015b [US1] **Pairing Logic**: Implement logic in `code/analyze_metrics.py` to explicitly link `pass_rate` records to the `task_id` and `source_type` in a paired structure. **Constraint**: Ensure the data structure supports paired analysis (e.g., dictionary keyed by `task_id`). **Dependency**: T015. (FR-005, Plan: Paired Statistical Design)
- [X] T016 [US1] **Coverage Extraction**: Implement logic in `code/analyze_metrics.py` to execute `pytest --cov` for `branch_coverage_pct` on **both human reference samples (from T011) and LLM samples (from T012)** using the sandbox from T015a. **Constraint**: Operate on **all tasks** in the full HumanEval dataset. **Output**: Intermediate JSON with `branch_coverage_pct`. **Dependency**: T015, T015a, T011. (FR-003, Plan: Testability Evaluation)
- [ ] T042 [US1] **Pairwise Exclusion Gate**: Implement logic in `code/analyze_metrics.py` to identify all task IDs where *either* the human reference OR the LLM sample has `null` coverage (non-executable). **Action**: If the number of valid pairs `n` is less than 30, **FAIL THE PIPELINE** with exit code `EXIT_INVALID_DATA = 1` and log a clear error message: "Insufficient valid pairs (n < 30). Full dataset constraint violated. Check execution logs for failures. NO SUBSETTING ALLOWED." **Constraint**: This ensures statistical validity by avoiding biased subsets. **DO NOT** generate a random subset. **Dependency**: T016, T015b. (FR-003, FR-004, Plan: Pipeline Execution Order Step 6, FR-008)
- [ ] T017 [US1] Implement aggregation in `code/analyze_metrics.py` to produce `data/analysis/metrics.json` with all required fields. **Dependencies**: T042, T014a, T014b, T015, T015b, T016. **Schema**: Must contain `task_id`, `source_type`, `cyclomatic_complexity`, `halstead_volume`, `branch_coverage_pct`, and `pass_rate`. **Constraint**: Verify no record has `null` for `cyclomatic_complexity` OR `halstead_volume`. **Note**: Conditional: Only runs if T042 passes. If T042 aborts, pipeline terminates. (US-1 Independent Test, FR-008)
- [ ] T029 [US1] **Sensitivity Analysis (MDES)**: Implement logic in `code/statistical_tests.py` to calculate the **Minimum Detectable Effect Size (MDES)** for the fixed sample size (N=164) using `statsmodels.stats.power`. **Parameters**: Use `alpha=0.05`, `power=0.8`, and observed standard deviations from the metrics. **Output**: Save MDES results to `data/analysis/power_results.yaml`. **Constraint**: This task explicitly implements Sensitivity Analysis (MDES) **in place of** the "A Priori" requirement of FR-008 due to the fixed N=164 constraint, as per the Plan's Methodological Note. **Dependency**: T017. (FR-008, Plan: Methodological Note)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (including MDES data in `power_results.yaml`)

---

## Phase 4: User Story 2 - Statistical Comparison and Hypothesis Testing (Priority: P2)

**Goal**: Perform Wilcoxon, McNemar, Fisher, and Permutation tests on the paired dataset (Baseline: Human vs CodeGen).

**Independent Test**: Feed mock paired datasets; verify p-values are calculated correctly and power analysis reports required n ≥ 38 and achieved power ≥ 0.8.

### Implementation for User Story 2

- [ ] T020 [US2] Implement `code/statistical_tests.py` with Wilcoxon Signed-Rank test for continuous metrics: **Cyclomatic Complexity and Halstead Volume ONLY**. **Parameters**: Use a **two-tailed** test with `alpha=0.05`. **Dependencies**: T017. (FR-004)
- [ ] T021 [US2] Implement `code/statistical_tests.py` with McNemar's test for binary pass-rate. **Parameters**: Use `alpha=0.05`. **Dependencies**: T017. (FR-004, Plan: Complexity Tracking)
- [ ] T022 [US2] Implement `code/statistical_tests.py` with Fisher's Exact Test for binary pass-rate (as an alternative to McNemar for small samples). **Parameters**: Use `alpha=0.05`. **Dependencies**: T017. (FR-004)
- [ ] T040 [US2] Implement `code/statistical_tests.py` with Permutation Test specifically for paired branch coverage data. **Dependencies**: T017, T042. (FR-004)
- [ ] T024 [US2] Implement Post-Hoc Power Analysis in `code/statistical_tests.py` based on observed effect sizes. **Dependencies**: T020, T021, T022, T040. (FR-008)
- [ ] T046 [US2] **Success Criteria Validation**: Implement logic in `code/statistical_tests.py` to evaluate the results against the **Functional Requirements** (FR-004 for statistical significance, FR-008 for power analysis) and the Plan's **Key Methodological Corrections** (paired analysis, complete-case coverage). Generate a `state/validation_results.yaml` file with boolean PASS/FAIL status for each requirement. **Dependencies**: T020, T021, T022, T040, T024, T042, T029. (FR-004, FR-008, Plan: Key Methodological Corrections)
- [ ] T026 [US2] Write unit tests for statistical functions using mock data with known p-values (tests/unit/test_statistics.py). (Plan: Testing)
- [ ] T027 [US2] Write integration test verifying the full statistical report generation from `metrics.json` (tests/integration/test_stats_pipeline.py). (Plan: Testing)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (Baseline analysis complete)

---

## Phase 5: User Story 3 - Visualization, Reporting, and Sensitivity Analysis (Priority: P3)

**Goal**: Generate automated Markdown report with figures, and perform sensitivity analysis using CodeLlama models.

**Independent Test**: Verify `results_report.md` contains all figures, tables, and sensitivity analysis results; verify API fallback logic works.

### Implementation for User Story 3

- [ ] T030 [US3] Implement `code/report_generator.py` to create histograms and boxplots using `matplotlib` for all continuous metrics. **Constraint**: Ensure `results/figures/` directory exists (create if missing) before writing files. (FR-006)
- [ ] T031a [US3] **Citation Extraction**: Implement `code/extract_citations.py` to scan `report.md` (or report template) and `state/` for all citations, extract them into a structured format, and save to `state/citations.yaml`. **Constraint**: Must include title, URL, and source for each citation. **Output**: `state/citations.yaml`. **Dependency**: T030. (FR-010, Constitution Principle II)
- [ ] T031 [US3] Implement `code/report_generator.py` with Jinja2 template to compile `results_report.md` including figures, tables, and power analysis. **Constraint**: The template must explicitly render the MDES results (from T029) and the validation status (from T046) in a dedicated "Sensitivity Analysis" and "Validation Status" section. **Dependency**: T030, T017, T046, T029, T031a. (FR-006, Plan: Data Model Traceability)
- [ ] T031b [US3] **Sensitivity Visualization Verification**: Implement logic in `code/report_generator.py` to verify that MDES results are correctly rendered in the report with distinct labels and that the `source_type` mapping matches the data in `metrics.json`. **Dependency**: T031, T017. (FR-006, Plan: Data Model Traceability)
- [ ] T033 [US3] Write unit tests for `code/report_generator.py` to verify figure generation and template rendering (tests/unit/test_report.py). (Plan: Testing)
- [ ] T034 [US3] Write integration test for the full pipeline from `metrics.json` to `results_report.md` (tests/integration/test_full_pipeline.py). (Plan: Testing)
- [ ] T056 [US3] **Citation Validation Wrapper**: Implement `code/validate_citations.py` as a wrapper script that invokes the external **Reference-Validator Agent** via `subprocess.run`. **Logic**: Parse `state/citations.yaml`, construct the subprocess command (`reference-validator --input state/citations.yaml --output state/validation_report.yaml`), capture the YAML report, and parse the results. **Constraint**: Must NOT implement validation logic internally; must strictly delegate to the external agent. **Output**: `state/validation_report.yaml`. **Gate Behavior**: If any citation is invalid OR if the subprocess fails (non-zero exit), raise `SystemExit(1)` and log the error. **Dependency**: T031a. (FR-010, Constitution Principle II, Plan: Citation Validation Workflow)
- [ ] T050 [US3] **Artifact Integrity Verification**: Implement `code/validate_artifacts.py` to compute SHA256 hashes for all files in `data/generated/` and `data/analysis/` and store them in `state/artifact_hashes.yaml`. **Constraint**: Must run after T017 and T031. **Dependency**: T005, T017, T031. (FR-011, Plan: Artifact Integrity)

### Sub-Phase 5.1: CodeLlama Sensitivity Analysis (Mandatory for FR-009)

**Purpose**: Implement sensitivity analysis with CodeLlama models as mandated by FR-009. These tasks require GPU execution.

**Note**: The primary model (CodeGen-350M) is CPU-tractable and handled in Phase 3. This sub-phase is strictly for the CodeLlama sensitivity analysis (FR-009) which requires GPU resources. **Execution Strategy**: The execution stage will detect `device="cuda"` requirements or exit code 184 and auto-offload these tasks to a free GPU runner.

- [ ] T052 [US3] **CodeLlama Sensitivity Implementation**: Implement `code/generate_code_llama.py` to generate code samples using `CodeLlama-Instruct-hf` (8-bit quantized) for sensitivity analysis. **Constraint**: Must target a GPU environment (auto-detected). **Logic**: Use `transformers` with `device_map="auto"` and `torch_dtype=torch.float16`. **Prompt**: Read from `code/prompt_templates/humaneval.txt`. **Input**: Read task list from `data/generated/humaneval.parquet`. **Parameters**: `temperature=0.0`, `max_tokens=1024`. **Output**: Save to `data/generated/llama_samples.json`. **Output Schema**: `{"task_id": str, "source_type": "llama_7b", "generated_code": str, "timestamp": str}`. **Exit Code Contract**: If GPU is unavailable, exit with `EXIT_GPU_RETRY = 184` and log `ERROR: GPU_UNAVAILABLE_EXIT_CODE`. **Dependency**: T010. (FR-009, Plan: Sensitivity Analysis)
- [ ] T053a [US3] **CodeLlama Metric Extraction**: Implement `code/analyze_metrics.py` to run `radon` (static) and `coverage.py` (dynamic) specifically on `data/generated/llama_samples.json` to generate `cyclomatic_complexity`, `halstead_volume`, and `branch_coverage_pct` for the `llama_7b` source type. **Constraint**: Must strictly reuse the logic from T014a/T016 to ensure consistency. **Output**: Intermediate metrics for llama samples. **Dependency**: T052, T014a (logic reuse), T015a, T011. (FR-009, FR-003)
- [ ] T053b [US3] **Sensitivity Comparison Logic**: Implement logic in `code/analyze_metrics.py` to aggregate the llama metrics (from T053a) into `data/analysis/metrics.json` with the new `source_type` value `llama_7b`. **Dependency**: T053a, T017. (FR-009)
- [ ] T054 [US3] **Cross-Model Statistical Tests**: Extend `code/statistical_tests.py` to perform Wilcoxon and McNemar tests comparing `codegen_350m` vs `llama_7b` in addition to the baseline `human` vs `codegen_350m` comparison. **Dependency**: T053b, T017. (FR-009)
- [ ] T055 [US3] **GPU Execution Wrapper**: Create `code/run_gpu_pipeline.py` as a script entry point that orchestrates the GPU-dependent tasks (T052, T053a, T053b, T054) and handles environment detection for the execution stage. **Constraint**: Must exit cleanly if no GPU is detected, signaling the execution stage to provision a GPU runner. **Dependency**: T010, T012 (Logic Pattern: T055 depends on the GPU logic pattern established in T012). **Note**: T055 is an independent orchestrator that checks for GPU availability at runtime. (Plan: GPU Escape Hatch, FR-009)

**Checkpoint**: All user stories should now be independently functional (Baseline report complete + Sensitivity Analysis)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **GPU Expansion (Sub-Phase 5.1)**: Depends on Foundational phase completion; can run in parallel with US2/US3 if GPU resources are available.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable (Baseline only)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable (Baseline only)
- **GPU Expansion (Sub-Phase 5.1)**: Depends on T010 (Data) and T012 (Logic Pattern). Runs after US1/US2 baseline.

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
- GPU tasks (T052-T055) can be executed on a separate GPU runner in parallel with CPU tasks.

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
3. Add User Story 2 → Test independently → Deploy/Demo (Baseline Stats)
4. Add User Story 3 → Test independently → Deploy/Demo (Baseline Report)
5. Add Sub-Phase 5.1 (GPU) → Test independently → Deploy/Demo (Sensitivity Analysis)
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
 - Developer D (or Auto): GPU Expansion Tasks (T052-T055)
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
- **GPU Note**: Tasks T052-T055 are reserved for GPU execution. The execution stage will detect `device="cuda"` requirements or exit code 184 and offload these specific tasks to a free GPU runner. Do not attempt to run these on the standard CPU runner.
- **A Priori Note**: A Priori Power Analysis is N/A for fixed N=164; replaced by Sensitivity Analysis (MDES) as documented in T029.
- **T051 Removal**: Task T051 (CodeGen-350M on GPU) was removed because the primary model is CPU-tractable. The GPU path is exclusively for CodeLlama (T052) as per FR-009.
- **FR-009 Compliance**: CodeLlama sensitivity analysis is now a mandatory part of User Story 3 (Sub-Phase 5.1), not an optional phase.
- **T042 Constraint**: T042 enforces the full dataset constraint; pipeline fails if valid pairs < 30. No sampling logic is implemented.
- **T010 Revision**: T010 now uses `revision="v1.0.0"` for reproducibility.
- **T016 Coverage**: T016 now explicitly processes both human and LLM samples.