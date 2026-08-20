# Tasks: Evaluating the Impact of Code Generation Models on Code Testability

**Input**: Design documents from `/specs/294-evaluating-the-impact-of-code-generation/`
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
- [ ] T015a [ ] **Execution Environment Setup**: Implement `code/sandbox.py` to create an isolated execution environment for HumanEval test suites using **subprocess with strict resource limits** (memory_limit=2GB via `resource` module, timeout=30s) to prevent network access and ensure stability, compatible with GitHub Actions Free Tier. **Output**: A reusable sandbox context manager. **Constraint**: This task MUST create its own `data/sandbox/` directory if needed to avoid implicit dependency on T008's directory structure. **Dependency**: T005, T008. (FR-005, Plan: Testability Evaluation)
- [ ] T008 [P] Create data directory structure: `data/raw/`, `data/generated/`, `data/analysis/`. **Constraint**: Do NOT create `state/` here; it is created in T001a at the root level. (Plan: Project Structure)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Paired Analysis Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download HumanEval, generate LLM code, compute metrics (Complexity, Mutation Score, Coverage), and produce paired JSON dataset.

**Independent Test**: Run the pipeline on the full HumanEval dataset (N=164). Verify that `data/analysis/metrics.json` contains `cyclomatic_complexity`, `halstead_volume`, `branch_coverage_potential`, and `pass_rate` for every valid pair, with n=164 (or n < 164 only if specific tasks fail execution).

### Sub-Phase 3.1: Data Ingestion

- [ ] T010 [US1] Implement `code/download_data.py` to download the **full** HumanEval dataset from HuggingFace (`openai/openai_humaneval`) using **`revision="v1.0.0"`** (or a specific commit SHA if `v1.0.0` is unavailable) to ensure deterministic versioning. Save raw data directly as `data/raw/humaneval.parquet`. Compute SHA256 for the parquet file. Record the exact version `v1.0.0` (or specific SHA) in `data/metadata.yaml`. **Constraint**: Implement exponential-backoff retry logic and a fixed timeout per task. (FR-001, FR-011, Plan: Large real datasets: STREAM the real data)
- [ ] T011 [US1] Implement `code/extract_human_reference.py` to extract human reference code from `data/raw/humaneval.parquet` and save to `data/generated/human_samples.json`. **Constraint**: Must preserve `task_id` and `prompt` fields. **Output**: JSONL file with human solutions. **Dependency**: T010. (FR-005, Plan: Paired Statistical Design)

### Sub-Phase 3.2: Code Generation

- [ ] T012 [US1] Implement `code/generate_code.py` to load **Primary Model: `Salesforce/codegen-mono-4b`** on CPU and generate code for **all tasks** in `data/generated/humaneval.parquet`. **Fallback**: If the 4B model fails (OOM or timeout), fall back to `Salesforce/codegen-350M-mono`. Implement exponential backoff retry logic with a fixed timeout per task. Use prompt template from `code/prompt_templates/humaneval.txt`. **Output**: Save generated code to `data/generated/codegen_samples.json`. (FR-002)
- [ ] T013 [US1] Implement error handling in `code/generate_code.py` to log failures to `code/errors.log` and mark samples as missing. **Logic**: Catch `RuntimeError`, `TimeoutError`, and `MemoryError`. Log the task_id and error message. In the output JSON, set `generated_code` to `null` and `status` to `'failed'` for the specific task. (FR-002)

### Sub-Phase 3.3: Metric Extraction

- [ ] T014a [US1] **Metric Extraction (Static)**: Implement `code/analyze_metrics.py` to run `radon cc --json` and `radon hal --json` on all samples (Human, CodeGen) from `data/generated/human_samples.json` and `data/generated/codegen_samples.json`. **Constraint**: Must operate on **all tasks** in the full HumanEval dataset. **Output**: Intermediate JSON with `cyclomatic_complexity`, `halstead_volume`, `halstead_components`. **Dependency**: T011, T012. (FR-003)
- [ ] T014b [US1] **Metric Processing**: Implement logic in `code/analyze_metrics.py` to parse `radon` output, map `cc` to `cyclomatic_complexity`, and calculate `halstead_volume` from `hal` components. **Constraint**: Store all extracted Halstead components. **Dependency**: T014a. (FR-003)
- [ ] T015 [US1] Implement logic in `code/analyze_metrics.py` to execute test suites against the HumanEval test suite for **both human reference samples (from T011) and LLM samples (from T012)** using the sandbox from T015a. **Metric**: Record `pass_rate` as a **float** (`passed_tests / total_tests`) per sample. **Constraint**: Operate on **all tasks** in the full HumanEval dataset. Do NOT filter out tasks based on pass_rate at this stage. **Output**: Intermediate JSON with `pass_rate` as a float. **Dependency**: T014a, T015a, T011. (FR-005)
- [ ] T015b [US1] **Filter Implementation**: Implement logic in `code/analyze_metrics.py` to filter tasks with `pass_rate` < 0.80 and generate `data/analysis/valid_task_ids.json`. **Constraint**: This task implements the FR-005 filter requirement. **Output**: JSON file containing list of valid task IDs. **Dependency**: T015. (FR-005)
- [ ] T016 [US1] **Coverage Extraction (Static)**: Implement logic in `code/analyze_metrics.py` to compute `branch_coverage_potential` (static branch count) using `radon -b` on **both human reference samples (from T011) and LLM samples (from T012)**. **Constraint**: Operate on **all tasks** in the full HumanEval dataset. **Output**: Intermediate JSON with `branch_coverage_potential`. **Dependency**: T011, T012, T014a. (FR-003, Constitution Principle VI)
- [ ] T017 [US1] Implement aggregation in `code/analyze_metrics.py` to produce `data/analysis/metrics.json` with all required fields. **Dependencies**: T014a, T015, T015b, T016. **Schema**: Must contain `task_id`, `source_type`, `cyclomatic_complexity`, `halstead_volume`, `branch_coverage_potential`, and `pass_rate`. **Constraint**: **Include ALL tasks** in the aggregated dataset (including those with `pass_rate` < 0.8) to perform Full-Sample Analysis (Primary). Use `valid_task_ids.json` from T015b to mark validity for Secondary Analysis. Verify no record has `null` for `cyclomatic_complexity` OR `halstead_volume`. (FR-005, Plan: Full-Sample Analysis)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (including MDES data in `power_results.yaml` via T024)

---

## Phase 4: User Story 2 - Statistical Comparison and Hypothesis Testing (Priority: P2)

**Goal**: Perform Wilcoxon Signed-Rank tests on the paired dataset (Baseline: Human vs CodeGen).

**Independent Test**: Feed mock paired datasets; verify p-values are calculated correctly and power analysis reports required n ≥ 38 and achieved power ≥ 0.8.

### Implementation for User Story 2

- [ ] T020 [US2] Implement `code/statistical_tests.py` with Wilcoxon Signed-Rank test for continuous metrics: **Cyclomatic Complexity and Halstead Volume ONLY**. **Parameters**: Use a **two-tailed** test with `alpha=0.05`. **Dependencies**: T017. (FR-004)
- [ ] T024 [US2] **Sensitivity Analysis (MDES) & Power**: Implement Post-Hoc Power Analysis and **Minimum Detectable Effect Size (MDES)** calculation in `code/statistical_tests.py` based on observed effect sizes and the fixed N=164 sample size. **Dependencies**: T017, T020. **Output**: Save MDES results to `data/analysis/statistical_results.json`. **Constraint**: This task replaces the deprecated T029. (FR-008, SC-005)
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
- [ ] T031 [US3] Implement `code/report_generator.py` with Jinja2 template to compile `results_report.md` including figures, tables, and power analysis. **Constraint**: The template must explicitly render the MDES results from T024 and the validation status from T046 in a dedicated "Sensitivity Analysis" and "Validation Status" section. **Dependency**: T030, T017, T046, T024, T031a. (FR-006)
- [ ] T031b [US3] **Sensitivity Visualization Verification**: Implement logic in `code/report_generator.py` to verify that MDES results are correctly rendered in the report with distinct labels and that the `source_type` mapping matches the data in `metrics.json`. **Dependency**: T031, T017. (FR-006)
- [ ] T033 [US3] Write unit tests for `code/report_generator.py` to verify figure generation and template rendering (tests/unit/test_report.py). (Plan: Testing)
- [ ] T034 [US3] Write integration test for the full pipeline from `metrics.json` to `results_report.md` (tests/integration/test_full_pipeline.py). (Plan: Testing)
- [ ] T056 [US3] **Citation Validation Wrapper**: Implement `code/validate_citations.py` as a wrapper script that invokes the external **Reference-Validator Agent** via `subprocess.run`. **Logic**: Parse `state/citations.yaml`, construct the subprocess command (`reference-validator --input state/citations.yaml --output state/validation_report.yaml`), capture the YAML report, and parse the results. **Constraint**: Must NOT implement validation logic internally; must strictly delegate to the external agent. **Output**: `state/validation_report.yaml`. (FR-010)
- [ ] T050 [US3] **Artifact Integrity Verification**: Implement `code/validate_artifacts.py` to compute SHA256 hashes for all files in `data/generated/` and `data/analysis/` and store them in `state/artifact_hashes.yaml`. **Constraint**: Must run after T017 and T031. (FR-011)

### Sub-Phase 5.1: CodeLlama Sensitivity Analysis (Mandatory for FR-009)

**Purpose**: Implement sensitivity analysis with CodeLlama models as mandated by FR-009. These tasks require CPU execution.

**Note**: The primary model (CodeGen-350M) is CPU-tractable and handled in Phase 3. This sub-phase is strictly for the CodeLlama sensitivity analysis (FR-009) which requires CPU execution.

- [ ] T052 [US3] **CodeLlama Sensitivity Implementation**: Implement `code/generate_code_llama.py` to generate code samples using **`CodeLlama-3B-Quantized`** (GGUF format, CPU-feasible) and save them to `data/generated/llama_samples.json`. Use prompt template from `code/prompt_templates/humaneval.txt`. **Output**: JSONL file containing generated code with task ID, source type (llama_3b), and timestamp. (FR-009)
- [ ] T053a [US3] **CodeLlama Metric Extraction**: Implement `code/analyze_metrics.py` to run `radon` (static) and `coverage.py` (dynamic) specifically on `data/generated/llama_samples.json` to generate `cyclomatic_complexity`, `halstead_volume`, and `branch_coverage_potential`. **Constraint**: Reuse existing logic from T014a and T016. **Output**: Intermediate metrics for llama samples. (FR-009)
- [ ] T053b [US3] **Sensitivity Comparison Logic**: Implement logic in `code/analyze_metrics.py` to aggregate the llama metrics into `data/analysis/metrics.json` with the new `source_type` value `llama_3b`. (FR-009)
- [ ] T054 [US3] **Cross-Model Statistical Tests**: Extend `code/statistical_tests.py` to perform **Levene's Test** for variance differences between `codegen_350m` and `llama_3b` in addition to the baseline `human` vs `codegen_350m` comparison. **Dependency**: T017, T053b. (FR-009, SC-006)
- [ ] T055 [US3] **CPU Execution Wrapper**: Create `code/run_cpu_pipeline.py` as a script entry point that orchestrates the CPU-dependent tasks (T052, T053a, T053b) and handles environment detection for the execution stage. **Constraint**: Must use `llama-cpp-python` with quantized GGUF on CPU. (FR-009)

**Checkpoint**: All user stories should now be independently functional (Baseline report complete + Sensitivity Analysis)