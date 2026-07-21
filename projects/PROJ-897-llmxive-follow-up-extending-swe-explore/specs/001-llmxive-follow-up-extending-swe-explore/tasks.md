# Tasks: llmXive follow-up: extending "SWE-Explore: Benchmarking How Coding Agents Explore Repositories"

**Input**: Design documents from `/specs/001-iterative-exploration-benchmark/`
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
 - Delivered as a MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan: Create directories `code/`, `data/raw/`, `data/curated/`, `data/results/`, `tests/unit/`, `tests/contract/`, `contracts/`, `docs/`, `paper/` AND configure linting (ruff/flake8) and formatting (black) tools.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 [P] Implement `code/config.py` to define paths (`data/raw/`, `data/curated/`, `data/results/`), random seeds, model config (CPU-only), AND critical thresholds: `COMPLEXITY_THRESHOLD` (for hard instance selection), `HARD_INSTANCE_PERCENTILE`, `VALIDATION_SAMPLE_SIZE` (See T012, T013).
- [X] T003 [P] Implement `code/utils/hash_artifacts.py` for automated SHA256 hashing of `data/` artifacts (Constitution Principle V)
- [X] T004 [P] Create `contracts/` directory with `dataset_schema.yaml`, `agent_log_schema.yaml`, `result_schema.yaml`
- [X] T005 [P] Implement `code/utils/validation.py` for JSONL/Parquet schema validation against contracts
- [X] T006 [P] Setup `pytest` configuration and `tests/contract/test_schemas.py` skeleton

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Curation and Hard Instance Selection (Priority: P1) 🎯 MVP

**Goal**: Download SWE-Explore, derive ground truth, select "hard" instances based on **initial coverage scores** (Spec FR-001) to ensure alignment with the benchmark's definition of "hard" (low retrieval success), and generate synthetic ambiguous issues with dynamic power-based sizing.

**Independent Test**: Verify the existence of `data/curated/hard_subset.jsonl`, `data/curated/non_hard_subset.jsonl`, `data/curated/synthetic_issues.jsonl`, and `data/curated/validation_report.md` with correct schemas and valid AST parsing for synthetic issues.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T007 [US1] Contract test for dataset schema in `tests/contract/test_dataset_schema.py` (Depends on T004 schema output)
- [X] T008 [P] [US1] Unit test for mutation logic (variable rename, comment removal) in `tests/unit/test_mutation.py`
- [X] T009 [P] [US1] Unit test for synthetic issue validity (AST parse check) in `tests/unit/test_synthetic_validity.py`

### Implementation for User Story 1

- [X] T010 [P] [US1] Implement `code/data/download.py` to fetch `bench.final.public.jsonl` from HuggingFace
- [X] T011 [P] [US1] Implement `code/data/derive_gt.py` to parse solution patches and generate `ground_truth_lines` lists
- [X] T012 [US1] **Filter Hard Subset (Spec Alignment)**.
 - **Requirement**: Implement filtering based on **initial coverage scores** as per **Spec FR-001** to identify "hard" instances (bottom [deferred] of scores).
 - **Rationale**: The Spec explicitly defines "hard" as low initial coverage. While the Plan suggested complexity to avoid tautology, the benchmark's core definition relies on the static baseline's failure rate. We implement Spec FR-001 as the primary path. The Plan's complexity metric will be computed as a diagnostic (T012-Coverage) but not used for selection.
 - **Logic**: Select the bottom [deferred] of initial coverage scores.
 - **Deliverable**: Create `code/data/filter_hard.py` to perform this calculation and selection.
 - **Output**: `data/curated/hard_subset.jsonl` (Primary deliverable).
 - **Dependency**: Must verify `code/config.py` (T002) exists before execution.
 - **Traceability**: Implements Spec FR-001.
- [X] T012-Complexity [US1] **Diagnostic: Complexity Metric**.
 - **Requirement**: Calculate Cyclomatic Complexity for each issue as a diagnostic metric only.
 - **Logic**: Compute complexity but do NOT use it for filtering the "hard" subset.
 - **Output**: Append complexity scores to `data/curated/hard_subset.jsonl` as a metadata field for later correlation analysis.
 - **Traceability**: Aligns with Plan Phase 0 as a diagnostic, not a selection criteria.
- [X] T012c [US1] **Generate Non-Hard Subset**.
 - **Requirement**: Compute the complement of the Primary Hard Subset (T012) to provide the input pool for synthetic generation.
 - **Logic**: Select all issues from the full dataset that are NOT in `data/curated/hard_subset.jsonl`.
 - **Output**: `data/curated/non_hard_subset.jsonl`.
 - **Dependency**: Depends on T012 completion.
 - **Traceability**: Resolves ordering-064eff0f by providing the correct input for T013.
- [X] T013 [US1] **Generate Synthetic Ambiguous Issues (Power-Based)**.
 - **Input**: `data/curated/non_hard_subset.jsonl` (T012c output).
 - **Logic**: Apply mutations (rename variables, remove all comments, and apply structural obfuscation via control flow reordering) to generate a representative set of issues.
 - **Constraint**: **Dynamic Generation Loop**: Continue generating issues until `power_analysis` (using `statsmodels.stats.power` with effect size 0.5, alpha=0.05) confirms statistical power >= 0.8. **Hard Safety Cap**: Stop at a predefined maximum number of issues if power is not reached to prevent runaway generation. Log warnings if cap is hit.
 - **Output**: `data/curated/synthetic_issues.jsonl`.
 - **Oracle**: Derive `ground_truth_lines` from the original unmutated code (FR-008).
 - **Validity**: Ensure mutated code is syntactically valid (AST parseable). Skip invalid mutations and log warnings.
 - **Deliverable**: Create `code/data/mutate.py` to implement this logic.
 - **Traceability**: Aligns with Spec FR-002 and SC-003 (Statistical Power).
- [X] T014 [US1] **Metadata & Versioning**.
 - Save `data/curated/synthetic_issues_meta.json` containing original code hashes, mutation parameters, and the exact count generated.
 - Run `hash_artifacts.py` on `data/curated/` files.
- [X] T015 [US1] **Generate Validation Report**.
 - Input: `data/curated/hard_subset.jsonl`.
 - Logic: Select `VALIDATION_SAMPLE_SIZE` (from config.py T002) random issues.
 - Output: Markdown table with columns [IssueID, CoverageScore, ComplexityScore, Notes].
 - **Note**: This report is a **tool for manual inspection**, not an automated validation result.
- [X] T016-AutoValidate [US1] **Automated Validation Gate**.
 - **Action**: Run `code/data/validate_hard.py` to automatically verify the "hard" subset against the coverage threshold and generate a validation report.
 - **Logic**: The script checks if the selected "hard" issues (by Coverage) exhibit low coverage (as a sanity check) and **includes a "Plan Override Justification" block** documenting the decision to use Coverage over Complexity to align with Spec FR-001.
 - **Output**: `data/curated/validation_report.md` and `data/curated/validation_status.json` (status: "PASSED" or "WARNING").
 - **Constraint**: The pipeline proceeds automatically regardless of status; manual review is optional.
 - **Dependency**: Phase 4 agents depend on T016-AutoValidate completion.
 - **Traceability**: Replaces manual gate T016 to ensure reproducibility (Constitution Principle I) and documents Spec Alignment.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Iterative Agent Execution Loop (Priority: P2)

**Goal**: Implement a CPU-tractable iterative agent loop with a bounded number of turns, static analysis feedback, and a Static Multi-Query Baseline. Ensure both produce compatible schemas for pairing.

**Independent Test**: Run a single "hard" issue through the iterative loop and verify a limited number of turns, reformulated queries containing error messages, and correct logging of `query_history` and `error_signals`.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Contract test for agent log schema in `tests/contract/test_agent_log_schema.py`
- [X] T018 [P] [US2] Integration test for agent loop termination (3-turn limit, loop detection) in `tests/integration/test_agent_loop.py`

### Implementation for User Story 2

- [X] T019 [P] [US2] Implement `code/agent/static_analysis.py` wrapper for `pylint`/`ast` to detect "missing import", "undefined variable", parse errors
- [X] T020 [P] [US2] Implement `code/agent/prompts.py` with templates for query reformulation based on static analysis signals
- [X] T021 [US2] **Data Locking & Subset Consistency**.
 - **Action**: Before running agents, copy `data/curated/hard_subset.jsonl` to a locked execution directory (e.g., `data/results/locked_hard_subset.jsonl`).
 - **Purpose**: Ensure T022 (Baseline) and T023 (Iterative) consume the **exact same** file instance to enable 1:1 pairing.
 - **Dependency**: Depends on T012 (data generation) and T016-AutoValidate. **Not parallel**: Must wait for T016-AutoValidate.
 - **Prerequisite**: Phase 4 agents depend on this task.
- [X] T022 [P] [US2] **Static Multi-Query Baseline**.
 - **Requirement**: Run **5 parallel queries** per issue (matching the *maximum* turn limit of the sweep in T024) to match iterative budget.
 - **Input**: `data/results/locked_hard_subset.jsonl` (T021).
 - **Deliverable**: Create `code/agent/static_baseline.py` to perform this execution.
 - **Output**: `data/results/baseline_logs.jsonl` (Unique path to avoid race conditions).
 - **Logging**: Explicitly log `issue_id`, `query_count`, `retrieved_context_ids`, and `coverage_score`.
 - **Dependency**: Depends on T021 completion.
- [X] T023 [P] [US2] **Iterative Agent**.
 - **Requirement**: Enforce configurable turn limit (default value, variable for sweep).
 - **Turn Logic**: Query -> Retrieve -> Static Analysis -> Reformulate (if error).
 - **Loop Detection**: Detect repeated queries to break loops early.
 - **Input**: `data/results/locked_hard_subset.jsonl` (T021).
 - **Output**: `data/results/iterative_logs.jsonl` (Unique path to avoid race conditions).
 - **Logging**: Explicitly log `issue_id`, `query_history`, `static_analysis_signals`, `turn_reasons`.
 - **Dependency**: Depends on T021 completion.
- [X] T024a [US2] **Turn-Limit Sweep: Sampling**.
 - **Logic**: Generate a specific sample list file for **N=100** issues (random sample with **seed 42**, stratified by complexity quartiles from `data/curated/hard_subset.jsonl`). **Power Check**: Run a power analysis to verify N=100 is sufficient for SC-006 stability claims.
 - **Output**: `data/results/sweep_sample_list.json`.
 - **Dependency**: Depends on T012 (stratification).
- [X] T024b [US2] **Turn-Limit Sweep: Execution**.
 - **Logic**: Execute the iterative agent loop for each turn limit in a range of low to moderate values.
 - **Parameter**: Pass `max_turns` dynamically to the agent execution script for each iteration.
 - **Output**: `data/results/sweep_execution_logs.json` (aggregated logs for all turn limits).
 - **Dependency**: Depends on T024a.
- [X] T024c [US2] **Turn-Limit Sweep: Aggregation**.
 - **Logic**: Aggregate results into `data/results/sweep_results.json` containing columns: `issue_id`, `turns_used`, `coverage`, `stability_flag` for each turn limit.
 - **Dependency**: Depends on T024b.
- [X] T025 [US2] **Hash Artifacts**.
 - Integrate `hash_artifacts.py` to hash `data/results/agent_logs/`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Comparative Metric Calculation and Statistical Testing (Priority: P3)

**Goal**: Compute line-level coverage and ranking efficiency, apply **Survival Analysis** (mandatory for censored data) or Wilcoxon (conditional), with Bonferroni correction, and frame results associatively.

**Independent Test**: Provide pre-computed metrics for a small set and verify the statistical test returns a p-value and correct conclusion (significant vs. non-significant) at p < 0.05 threshold.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Contract test for result schema in `tests/contract/test_result_schema.py`
- [X] T027 [P] [US3] Unit test for statistical tests in `tests/unit/test_stats.py`. **Includes**: Wilcoxon signed-rank test implementation AND **censored data handling logic (N+1 penalty assignment) for Survival Analysis validation**. This task explicitly validates the logic required for T030-Survival, ensuring that censored entries are handled correctly before the main analysis runs.

### Implementation for User Story 3

- [X] T028 [P] [US3] Implement `code/metrics/coverage.py` to calculate % of `ground_truth_lines` retrieved
- [X] T029 [P] [US3] Implement `code/metrics/ranking.py` to calculate position of first relevant line (handle censored data with penalty N+1)
- [X] T030-Prep [US3] **Censoring Check & Routing**.
 - **Requirement**: Analyze `data/results/baseline_logs.jsonl` and `data/results/iterative_logs.jsonl` to determine if "Ranking Efficiency" data contains censored values (no relevant lines found).
 - **Logic**: If censored data exists (>0%), route to T030-Survival. If no censored data, route to T030-Wilcoxon.
 - **Output**: `data/results/statistical_routing.json` (flag: "SURVIVAL" or "WILCOXON").
 - **Dependency**: Depends on T022, T023.
- [X] T030-Wilcoxon [P] [US3] **Coverage & Ranking Analysis (Conditional)**.
 - **Requirement**: Implement **Wilcoxon signed-rank test** as per **Spec FR-006** and **SC-003** ONLY if T030-Prep confirms no censored data.
 - **Method**: Apply Wilcoxon signed-rank test to paired coverage data and paired ranking data (with continuity correction for ties).
 - **Output**: P-values and effect sizes for both metrics.
 - **Traceability**: Implements Spec FR-006/SC-003 conditionally.
- [X] T030-Survival [P] [US3] **Ranking Efficiency Analysis (Mandatory for Censored Data)**.
 - **Requirement**: Implement **Survival Analysis (Cox proportional hazards)** as per **Plan Phase 2** and **SC-003** if T030-Prep detects censored data.
 - **Method**: Apply Survival Analysis to handle censored ranking data (where no relevant lines found). **Validation**: Ensure the implementation correctly handles the N+1 penalty for censored entries as tested in T027.
 - **Output**: Hazard ratio and p-value.
 - **Traceability**: Aligns with Plan Phase 2 rationale for censored data; mandatory path.
- [X] T030c [US3] **Multiplicity Correction & Framing**.
 - **Correction**: Apply **Bonferroni correction** to the family of tests: **Coverage**, **Ranking (Wilcoxon or Survival)**.
 - **Framing**: Frame all results as **"associational differences"** per FR-007.
 - **Output**: `data/results/final_metrics.json`.
 - **Dependency**: Depends on T030-Wilcoxon or T030-Survival.
- [X] T031 [US3] Implement `code/analysis/plots.py` for visualization of coverage and survival curves
- [X] T032 [US3] Integrate `hash_artifacts.py` to hash final `data/results/final_metrics.json`
- [X] T033-Zero [US3] **Create Report Template**.
 - **Action**: Create `code/analysis/report_template.j2` using a Jinja2 template.
 - **Logic**: Define sections: Abstract, Methods, Results, Discussion.
 - **Constraint**: Ensure all placeholders are mapped to fields in `data/results/final_metrics.json`.
 - **Output**: `code/analysis/report_template.j2`.
 - **Dependency**: Must exist before T033b.
- [X] T033a [US3] **Report Generation: Data Extraction**.
 - Logic: Extract p-values, effect sizes, and metrics from `data/results/final_metrics.json`.
 - **Output**: `data/results/report_extract.json` (intermediate artifact).
 - **Dependency**: Depends on T030c.
- [X] T033b [US3] **Report Generation: Template Filling**.
 - Logic: Populate sections: Abstract, Methods, Results, Discussion using extracted data from T033a and `code/analysis/report_template.j2` (T033-Zero).
 - **Constraint**: Enforce "associational differences" language in Results/Discussion.
 - **Output**: `data/results/report_draft.md` (intermediate artifact).
 - **Dependency**: Depends on T033a and T033-Zero.
- [X] T033d [US3] **Validate Report Language**.
 - **Requirement**: Implement a validator to ensure `paper/draft.md` does not contain causal language.
 - **Logic**: Run a regex scan and an LLM-based check (using a lightweight prompt) for keywords like "proves", "causes", "guarantees". Fail the build if found.
 - **Output**: `data/results/report_validation_report.json` (status: "PASSED" or "FAILED").
 - **Dependency**: Depends on T033b.
- [X] T033c [US3] **Report Generation: Final Assembly & Validation**.
 - Logic: Assemble `paper/draft.md` and validate against schema using `report_draft.md` and T033d results.
 - **Output**: `paper/draft.md` and `data/results/report_validation_report.json`.
 - **Dependency**: Depends on T033b and T033d.
- [X] T034 [US3] **Generate Results Summary**.
 - **Action**: Execute T033a -> T033b -> T033d -> T033c pipeline.
 - **Output**: `paper/results_summary.md` (containing Abstract draft, Methods summary, Results, Discussion).
 - **Constraint**: Scope limited to spec requirements (SC-004, FR-007); no full manuscript generation.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T035 [P] Update `docs/quickstart.md` with execution instructions and data flow diagrams.
- [X] T036 Refactor `code/agent/iterative.py` to reduce cyclomatic complexity.
- [X] T037 Optimize memory usage in `code/metrics/coverage.py` by processing lines in chunks.
- [X] T038 [P] Add unit tests for `code/analysis/stats.py` (Wilcoxon and Survival Analysis logic).
- [X] T039 [US2/US3] Implement runtime monitor in `code/main.py` to track total execution time. **Logic**: If elapsed time > 5.5 hours (SC-005), abort remaining non-critical sweeps or reduce sample size to ensure completion within 6 hours.
- [X] T040-Auto [US3] **Automate Quickstart Execution**.
 - **Action**: Create `code/tests/run_quickstart.py` to automate the execution of `docs/quickstart.md`.
 - **Logic**: Run the quickstart script, capture exit code, and save logs.
 - **Output**: `data/validation/quickstart_run.log`.
 - **Traceability**: Implements new FR-011 (Quickstart Validation) and SC-007 (Validation Execution).
- [X] T040-Test [US3] **Validate Quickstart Execution**.
 - **Action**: Create `tests/unit/test_quickstart.py` to assert the success of T040-Auto.
 - **Logic**: Assert exit code is 0 and log file contains "Validation Successful".
 - **Traceability**: Implements new FR-011 and SC-007.
- [X] T041 [US1] **Fix Data Loader Robustness**.
 - **Requirement**: Update `code/data/download.py` to **remove any synthetic fallback logic** and ensure it raises a clear `ValueError` if the HuggingFace fetch fails (HTTP 404/500).
 - **Traceability**: Implements new FR-012 (Data Loader Integrity) and SC-005 (Compute Feasibility).
- [X] T042 [US1] **Stream Large Datasets**.
 - **Requirement**: Refactor `code/data/derive_gt.py::load_dataset_streaming` to use `datasets.load_dataset(..., streaming=True)` and process ground truth derivation in chunks to prevent OOM errors on constrained-memory runners.
 - **Traceability**: Implements new FR-013 (Streaming Data Handling) and SC-005 (Compute Feasibility).
- [X] T043 [US2] **Implement CPU-Quantized Model Wrapper**.
 - **Requirement**: Create `code/agent/quantized_llm.py` to use `llama-cpp-python` with a 4-bit quantized model (e.g., `Qwen-2.5-1.5B-Instruct-GGUF`) to ensure inference fits within 7GB RAM, replacing any default precision assumptions.
 - **Traceability**: Implements new FR-014 (CPU Quantized Execution) and SC-005 (Compute Feasibility).
- [X] T044 [US2] **Add Turn-Loop Detection Logic**.
 - **Requirement**: Update `code/agent/iterative.py::detect_loop` to explicitly detect and break infinite loops if the reformulated query matches a previous turn's query string within a limited conversation history window.
 - **Traceability**: Implements Spec Edge Case (loop detection) and FR-003 (Turn Limit).
- [X] T046 [US3] **Verify Bonferroni Correction**.
 - **Requirement**: Implement `tests/contract/test_result_schema.py::test_bonferroni_adjusted_pvalue` to validate that the `final_metrics.json` explicitly includes the adjusted p-value and the correction factor used, ensuring FR-007 compliance.
 - **Traceability**: Implements new FR-016 (Multiplicity Correction Validation) and SC-004 (Multiplicity Correction).

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for data (specifically `hard_subset.jsonl` and `validation_status.json`)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 for results

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
Task: "Contract test for dataset schema in tests/contract/test_dataset_schema.py"
Task: "Unit test for mutation logic in tests/unit/test_mutation.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/download.py"
Task: "Implement code/data/derive_gt.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (and pass automated gate T016-AutoValidate)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Pass Automated Gate → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Curation)
 - Developer B: User Story 2 (Agent Execution)
 - Developer C: User Story 3 (Analysis)
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
- **CPU Feasibility**: Ensure all model tasks use CPU-only, <1B param or 4-bit quantized models on -core/7GB RAM. No CUDA/GPU.
- **Constraint Preservation**: All tasks must strictly implement the metrics and counts defined in FR-001, FR-002, SC-004, and FR-007.
 - **Hard Instance Selection**: Must use **initial coverage scores** (Spec FR-001) as the primary path (T012) to align with the benchmark definition. Complexity is diagnostic (T012-Complexity).
 - **Synthetic Issues**: Must generate dynamically until statistical power >= 0.8 (T013), with a hard cap of 200.
 - **Statistics**: Coverage and Ranking use Survival Analysis (T030-Survival) if censored data exists (mandatory), otherwise Wilcoxon (T030-Wilcoxon).
 - **Correction**: Bonferroni applied to Coverage, Ranking Wilcoxon/Survival tests.
- **Data Integrity**: All analysis tasks must consume REAL data from `data/curated/`. No synthetic/fake input data generation tasks are permitted.
- **Execution Order**: Tasks producing results (T023) MUST follow tasks generating those results (T021, T022). Tasks verifying results (T030) MUST follow result generation.
- **Automated Validation**: Phase 4 cannot start until T016-AutoValidate completes successfully.
- **New Functional Requirements (FR-011 to FR-016)**: Added to address coverage gaps for Quickstart, Data Loader, Streaming, Quantization, Censored Data, and Multiplicity Validation.