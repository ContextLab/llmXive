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
- [ ] T006b [US1] Implement `code/extract_citations.py` to scan `spec.md`, `plan.md`, and `research.md` for citations and populate `state/citations.yaml` with a structured list of URLs and titles. **Constraint**: This task MUST run before T007a to ensure the input artifact exists. (FR-010, Plan: Pipeline Execution Order Step 1)
- [ ] T007a [US1] Implement `code/validate_citations.py` wrapper for the Reference-Validator Agent (FR-010). **Logic**: Must read citations from `state/citations.yaml`, verify against primary sources, and return exit code 0 on success, non-zero on failure. **Dependency**: T006b. (FR-010)
- [ ] T007b [US1] **Pipeline Gate**: Implement the execution logic to invoke `python code/validate_citations.py` as the first step of the pipeline. **Constraint**: If T007a returns non-zero, the pipeline MUST abort immediately with `SystemExit(1)`. **Dependency**: T007a must complete before T007b runs. **Status**: Pending until T007a is implemented. (Plan: Pipeline Execution Order Step 1)
- [X] T008 Create data directory structure: `data/raw/`, `data/generated/`, `data/analysis/`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Paired Analysis Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download HumanEval, generate LLM code, compute metrics (Complexity, Halstead, Coverage), and produce paired JSON dataset.

**Independent Test**: Run the pipeline on a local copy of HumanEval. Verify that `data/analysis/metrics.json` contains `cyclomatic_complexity`, `halstead_volume`, `branch_coverage_pct`, and `pass_rate` for every valid pair, with at least 40 valid samples.

### Implementation for User Story 1

- [ ] T010 [US1] Implement `code/download_data.py` to download HumanEval from HuggingFace using `streaming=True` to process the full dataset without loading it into RAM. Verify SHA256 and save to `data/raw/`. **Constraint**: Must NOT fall back to synthetic data; must raise a `RuntimeError` with a clear message "Failed to download verified real source" if the download fails after max retries. (FR-001, FR-011, Plan: Large real datasets: STREAM the real data)
- [ ] T011 [US1] Implement stratified sampling logic in `code/download_data.py` to select a representative subset of tasks based on human pass-rate quartiles. **Dependency**: T010. **Includes assertion**: Verify the final selected subset size is, as specified in the Plan's Sampling Strategy. **Constraint**: If T010 fails or returns insufficient data, T011 must not run (enforced by dependency). (Plan: Sampling Strategy)
- [ ] T012 [US1] Implement `code/generate_code.py` to load `Salesforce/codegen-mono` on CPU and generate code for a set of tasks with 3-retry logic (FR-002)
- [ ] T013 [US1] Implement error handling in `code/generate_code.py` to log failures to `errors.log` and mark samples as missing (Edge Cases)
- [ ] T014a [US1] Implement `code/analyze_metrics.py` to run `radon` for **Cyclomatic Complexity** on all samples. **Metric Specifics**: Extract `radon.cc` (cyclomatic complexity) and record as `cyclomatic_complexity` in the JSON. (FR-003)
- [ ] T014b [US1] Implement `code/analyze_metrics.py` to run `radon` for **Halstead Volume** on all samples. **Metric Specifics**: Extract all Halstead metrics (N, n, N, n, V, L, D, E) for completeness, but record `V` (Volume) as `halstead_volume` in the JSON as the primary metric required by FR-003. (FR-003)
- [ ] T015 [US1] Implement logic in `code/analyze_metrics.py` to execute `pytest` against the HumanEval test suite for each sample and record the binary `pass_rate` (1 = all tests passed, 0 = any failure) per sample in `metrics.json`. **JSON Schema**: `metrics.json` is an array of objects, each containing `task_id`, `source_type`, and `pass_rate` (binary). Aggregated rates are calculated in the report generation phase, not here. (FR-005)
- [ ] T042 [US1] Implement logic in `code/analyze_metrics.py` to run `pytest --cov` for `branch_coverage_pct`, recording `[deferred]` if execution fails while still recording the `pass_rate` (FR-003, Edge Cases)
- [ ] T016 [US1] Implement logic in `code/analyze_metrics.py` to handle execution failures (record `[deferred]` for coverage) (Edge Cases)
- [ ] T017 [US1] Implement aggregation in `code/analyze_metrics.py` to produce `data/analysis/metrics.json` with all required fields. **Dependencies**: T014a, T014b, T015, T042. (US-1 Independent Test)

**Sensitivity Analysis Sub-Phase (within US1)**

- [ ] T028 [US3] Implement sensitivity analysis logic in `code/generate_code.py` to call HuggingFace Inference API for `CodeLlama-7B` for a subset of tasks. **Trigger**: Run only if API is available. (FR-009)
- [ ] T028a [US3] **Model Check**: Implement logic in `code/generate_code.py` to check local model availability for `CodeLlama-3B` with 4-bit quantization. **Artifact**: Write `state/model_availability.json` containing a JSON object with keys `available` (boolean), `model_id` (string), and `timestamp` (ISO8601). (FR-009)
- [ ] T028c [US3] **Fallback Initialization**: Implement logic in `code/generate_code.py` to ensure `state/model_availability.json` exists with a default state `{"available": false, "model_id": "none", "timestamp": "..."}` if T028 (API check) or T028a (local check) fail or are skipped. **Dependency**: Runs before T029. **Constraint**: This ensures T029 can read the file without FileNotFoundError. (FR-009, Plan: 4-bit Quantization Fallback)
- [ ] T028b [US3] **Fallback Generation**: Execute ONLY if T028 fails AND T028a indicates local availability is true. Load `CodeLlama-3B` locally on CPU with 4-bit quantization and generate code. (FR-009)
- [ ] T029 [US3] Implement fallback logic in `code/generate_code.py`: If `CodeLlama-7B` API is unavailable AND local 4-bit quantization is available (per `state/model_availability.json`), use `CodeLlama-3B` for generation. If T028a failed, skip sensitivity generation for this path. **Dependency**: T028c. (FR-009)
- [ ] T041a [US1/US2] **Validation**: Validate `data/analysis/metrics.json` contains all required fields and distinct `source_type` entries. **Dependency**: Runs after T017 and T028/T029. (Plan: Pipeline Execution Order)
- [ ] T041b [US1/US2] **Versioned Merge**: Merge sensitivity results into `data/analysis/metrics.json` using composite key `task_id + source_type`. **Constraint**: Instead of overwriting, append new entries to a versioned file `data/analysis/metrics_v{N}.json` and update a `state/metrics_versions.yaml` index. **Dependency**: Runs after T041a. (Plan: Data Model Traceability)
- [ ] T041c [US1/US2] **Conflict Resolution & Logging**: Detect collisions (same `task_id + source_type` across versions). **Resolution Strategy**: Keep the entry with the latest timestamp and log the discarded entry to `state/collision_log.json` with a warning. **Constraint**: This step MUST complete before T045 to ensure a unified, conflict-free dataset. (Plan: Data Model Traceability)

- [ ] T018 [US1] Write unit tests for `code/download_data.py` to verify checksum logic and sampling distribution (tests/unit/test_download.py)
- [ ] T019 [US1] Write integration test for `code/analyze_metrics.py` to verify metric extraction on a known Python snippet (tests/integration/test_metrics.py)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (including sensitivity data merged into metrics_v{N}.json)

---

## Phase 3.5: Sensitivity Analysis Computation (Blocking for US2/US3)

**Purpose**: Compute comparative metrics for sensitivity analysis before reporting.

- [ ] T045 [US1/US3] **Sensitivity Analysis Computation**: Implement logic to compute effect sizes (Cohen's d) and delta calculations between `codegen-350M` and `codellama` variants. **Input**: `data/analysis/metrics_v{N}.json` (canonical merged file from T041c). **Output**: Update `data/analysis/metrics_v{N}.json` with new sensitivity analysis fields (e.g., `effect_size_complexity`, `delta_coverage`). **Constraint**: Do NOT create a separate intermediate file; update the canonical source directly. (FR-009, Plan: Single Source of Truth)
- [ ] T046 [US3] **Sensitivity Comparison Logic**: Implement the comparative analysis logic required by FR-009. **Logic**: Aggregate results from `data/analysis/metrics_v{N}.json` to generate a comparative summary (e.g., mean difference in complexity, coverage delta) between CodeGen and CodeLlama models. **Output**: Update `data/analysis/metrics_v{N}.json` with comparative summary fields. **Dependency**: T045. (FR-009)

---

## Phase 4: User Story 2 - Statistical Comparison and Hypothesis Testing (Priority: P2)

**Goal**: Perform Wilcoxon, McNemar, Fisher, and Permutation tests, and Power Analysis (A Priori/Post-Hoc) on the paired dataset.

**Independent Test**: Feed mock paired datasets; verify p-values are calculated correctly and power analysis reports required n ≥ 38 and achieved power ≥ 0.8.

### Implementation for User Story 2

- [ ] T020 [US2] Implement `code/statistical_tests.py` with Wilcoxon Signed-Rank test for continuous metrics: **Cyclomatic Complexity and Halstead Volume ONLY**. **Note**: Branch Coverage is excluded per Plan Complexity Tracking; use T040 for coverage. (FR-004, US-2)
- [ ] T021 [US2] Implement `code/statistical_tests.py` with McNemar's test for binary pass-rate (FR-004)
- [ ] T022 [US2] Implement `code/statistical_tests.py` with Fisher's Exact Test for **unpaired exploratory checks ONLY** (FR-004). **Note**: Paired coverage data uses T040 (Permutation Test) as per Plan Complexity Tracking.
- [ ] T040 [US2] Implement `code/statistical_tests.py` with Permutation Test specifically for paired branch coverage data (Plan: Complexity Tracking)
- [ ] T023 [US2] Implement A Priori Power Analysis in `code/statistical_tests.py` (d=0.5, α=0.05, power≥0.8) to validate sample size (FR-008)
- [ ] T024 [US2] Implement Post-Hoc Power Analysis in `code/statistical_tests.py` based on observed effect sizes (FR-008)
- **Note**: Independence of structural complexity from functional success is verified via T020 (Wilcoxon) and T021 (McNemar) tests as per the Plan. T025 (Spearman correlation) was removed as it was scope creep not in the Plan.
- [ ] T026 [US2] Write unit tests for statistical functions using mock data with known p-values (tests/unit/test_statistics.py)
- [ ] T027 [US2] Write integration test verifying the full statistical report generation from `metrics.json` (tests/integration/test_stats_pipeline.py)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization, Reporting, and Sensitivity Analysis (Priority: P3)

**Goal**: Generate automated Markdown report with figures, and perform sensitivity analysis using CodeLlama models.

**Independent Test**: Verify `results_report.md` contains all figures, tables, and sensitivity analysis results; verify API fallback logic works.

### Implementation for User Story 3

- [ ] T030 [US3] Implement `code/report_generator.py` to create histograms and boxplots using `matplotlib` for all continuous metrics. **Dependency**: T009 (results/figures/ directory must exist). (US-3)
- [ ] T031 [US3] Implement `code/report_generator.py` with Jinja2 template to compile `results_report.md` including figures, tables, and power analysis (FR-006)
- [ ] T032 [US3] Implement logic to include sensitivity analysis comparison (7B/3B vs 350M) in the final report. **Logic**: Extract data from `data/analysis/metrics_v{N}.json` (canonical merged file from T041c, T045, T046), generate comparative boxplots for complexity/coverage, and include a summary table of effect sizes. **Verification**: Ensure the report contains comparative visualizations and a summary table as required by the US3 independent test. **Constraint**: Do NOT read from intermediate files; use only the canonical `metrics_v{N}.json`. (FR-009, Plan: Single Source of Truth)
- [ ] T033 [US3] Write unit tests for `code/report_generator.py` to verify figure generation and template rendering (tests/unit/test_report.py)
- [ ] T034 [US3] Write integration test for the full pipeline from `metrics.json` to `results_report.md` (tests/integration/test_full_pipeline.py)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Documentation updates in `docs/` and `README.md`
- [X] T036 Code cleanup and refactoring of `code/utils.py`
- [X] T037 Performance optimization for `code/analyze_metrics.py` (parallel processing if safe)
- [ ] T038 [P] Additional unit tests for edge cases (e.g., 0 coverage, missing LLM samples) in `tests/unit/`
- [X] T043 [US1] Implement robust retry logic with exponential backoff for HuggingFace dataset downloads in `code/download_data.py` to handle transient network failures. **Constraint**: Must NOT fall back to synthetic data; must raise an explicit error if the verified real source is unreachable after max retries. (Plan: Data Hygiene, FR-001)
- [X] T044 [US2] Add explicit handling in `code/statistical_tests.py` for zero-variance cases in the Permutation Test to prevent division-by-zero errors when coverage is [deferred] or [deferred] for all samples. (Plan: Complexity Tracking, FR-004)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **Phase 3 (US1)**: **Depends on Phase 2 (Foundational) completion**. T007b must complete before T010 starts. **Includes T041c** which must complete before Phase 4 starts.
- **Phase 3.5 (Sensitivity Computation)**: **Depends on Phase 3 (US1) completion**. T046 is the blocking task for Phase 5.
- **Phase 4 (US2)**: **Depends on Phase 3 (T041c) completion** (requires `metrics_v{N}.json` from T017 and T041c).
- **Phase 5 (US3)**: **Depends on Phase 4 (US2) completion** and **T046 completion** (requires statistical results and sensitivity analysis data from `metrics_v{N}.json`).
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. Includes sensitivity generation and analysis (T028a, T028, T029, T041c).
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (`metrics_v{N}.json` including sensitivity data).
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 data, US2 results, and T046 for report generation.

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
3. Complete Phase 3: User Story 1 (including T041c for sensitivity data merge)
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