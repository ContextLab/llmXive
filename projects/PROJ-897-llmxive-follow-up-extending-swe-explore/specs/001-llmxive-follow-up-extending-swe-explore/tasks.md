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

- [X] T001a [P] Create project structure: Run `mkdir -p code/ data/raw/ data/curated/ data/results/ tests/unit/ tests/contract/ contracts/ docs/ paper/`. Verify existence of all required directories by running `code/utils/verify_structure.py` (which checks `os.path.isdir` for each path).
- [X] T001b [P] Configure Linting: Create `.ruff.toml` or `pyproject.toml` with ruff/flake8 configuration for the project.
- [X] T001c [P] Configure Formatting: Create `.black.toml` or `pyproject.toml` with black formatting configuration for the project.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 [P] Implement `code/config.py` to define paths (`data/raw/`, `data/curated/`, `data/results/`), random seeds, model config (CPU-only), and critical thresholds: `HARD_INSTANCE_PERCENTILE` (default 0.2), `VALIDATION_SAMPLE_SIZE`, `BASELINE_QUERY_COUNT` (default 5, configurable), `SWEEP_SAMPLE_SIZE` (default 20), `SYNTHETIC_COUNT` (default 50).
- [X] T003 [P] Implement `code/utils/hash_artifacts.py` for automated SHA256 hashing of `data/` artifacts (Constitution Principle V)
- [X] T004 [P] Create `contracts/` directory with `dataset_schema.yaml`, `agent_log_schema.yaml`, `result_schema.yaml`
- [X] T005 [P] Implement `code/utils/validation.py` for JSONL/Parquet schema validation against contracts
- [X] T006 [P] Setup `pytest` configuration and `tests/contract/test_schemas.py` skeleton

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Curation and Hard Instance Selection (Priority: P1) 🎯 MVP

**Goal**: Download SWE-Explore, derive ground truth, compute initial coverage, select "hard" instances based on **initial coverage scores** (Spec FR-001), and generate a fixed set of synthetic ambiguous issues with mapped ground truth.

**Independent Test**: Verify the existence of `data/curated/hard_subset.jsonl`, `data/curated/non_hard_subset.jsonl`, `data/curated/synthetic_issues.jsonl`, and `data/curated/validation_report.md` with correct schemas and valid AST parsing for synthetic issues.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T007 [US1] Contract test for dataset schema in `tests/contract/test_dataset_schema.py` (Depends on T004 schema output)
- [X] T008 [P] [US1] Unit test for mutation logic (variable rename, comment removal) in `tests/unit/test_mutation.py`
- [X] T009 [P] [US1] Unit test for synthetic issue validity (AST parse check) in `tests/unit/test_synthetic_validity.py`

### Implementation for User Story 1

- [X] T010 [P] [US1] **Download Dataset**.
 - **Action**: Implement `code/data/download.py` to fetch `bench.final.public.jsonl` from the verified HuggingFace URL.
 - **Constraint**: If the fetch fails (HTTP 404/500), raise a `ValueError` immediately. Do NOT fall back to synthetic data.
 - **Output**: `data/raw/bench.final.public.jsonl`.
 - **Traceability**: Implements Spec FR-001 (Data Source).
- [X] T011 [P] [US1] **Derive Ground Truth**.
 - **Action**: Implement `code/data/derive_gt.py` to parse solution patches and generate `ground_truth_lines` lists.
 - **Constraint**: Use `datasets.load_dataset(..., streaming=True)` to process large files in chunks to prevent OOM.
 - **Output**: `data/raw/bench.final.public.gt.jsonl`.
 - **Traceability**: Implements Spec FR-008 (Oracle Derivation).
- [X] T012a-Impl [P] [US1] **Implement Baseline Retrieval**.
 - **Requirement**: Implement `code/data/derive_coverage.py::run_baseline` to run a lightweight static baseline retrieval on the original code.
 - **Logic**: The function iterates through `data/raw/bench.final.public.gt.jsonl` (T011) and retrieves context for each issue.
 - **Output**: Intermediate list of retrieved contexts.
 - **Dependency**: Depends on T011.
 - **Traceability**: Provides the producer for Spec FR-001 (Filter by Coverage).
- [X] T012a-Calc [P] [US1] **Compute Coverage Percentage**.
 - **Requirement**: Implement `code/data/derive_coverage.py::calc_coverage` to calculate the percentage of ground-truth lines retrieved.
 - **Logic**: Compare retrieved lines against `ground_truth_lines` for each issue.
 - **Output**: List of coverage percentages.
 - **Dependency**: Depends on T012a-Impl.
 - **Traceability**: Provides the metric for Spec FR-001.
- [X] T012a-Append [P] [US1] **Append Coverage to Dataset**.
 - **Requirement**: Implement `code/data/derive_coverage.py::append_coverage` to append `initial_coverage` to each record in a single pass.
 - **Output**: `data/raw/bench.final.public.gt.coverage.jsonl`.
 - **Dependency**: Depends on T012a-Calc.
 - **Traceability**: Provides the final dataset for T012.
- [X] T012 [US1] **Filter Hard Subset & Compute Complexity**.
 - **Requirement**: Filter the dataset to select the bottom `HARD_INSTANCE_PERCENTILE` (e.g., [deferred]) based on **initial coverage scores** (Spec FR-001).
 - **Diagnostic**: Compute Cyclomatic Complexity for each issue and append as a metadata field `complexity_score`.
 - **Logic**: Select the bottom % by `initial_coverage` (from T012a-Append). Append complexity scores for diagnostic purposes only (do NOT use for filtering).
 - **Deliverable**: Create `code/data/filter_hard.py` to perform this calculation and selection.
 - **Output**: `data/curated/hard_subset.jsonl` (includes `initial_coverage` and `complexity_score`).
 - **Dependency**: Depends on T012a-Append.
 - **Traceability**: Implements Spec FR-001. Resolves contradiction with Plan by following Spec (Plan updated to align).
- [X] T012c [US1] **Generate Non-Hard Subset**.
 - **Requirement**: Compute the complement of the Hard Subset (T012) to provide the input pool for synthetic generation.
 - **Logic**: Select all issues from `data/raw/bench.final.public.gt.coverage.jsonl` (T012a-Append) that are NOT in `data/curated/hard_subset.jsonl`.
 - **Output**: `data/curated/non_hard_subset.jsonl`.
 - **Dependency**: Depends on T012a-Append and T012.
 - **Traceability**: Resolves ordering-3673b074 by providing correct input for T013a.
- [X] T013a [US1] **Derive GT for Synthetic Issues**.
 - **Input**: `data/curated/non_hard_subset.jsonl` (T012c).
 - **Action**: For each issue in the non-hard subset, prepare the original code and its `ground_truth_lines` (from T011) to be used as the oracle for the *mutated* version.
 - **Logic**: Store the original code and its GT lines in a temporary mapping. This ensures that when T013 mutates the code, the GT lines refer to the original indices (as per FR-008) or are mapped correctly if line numbers shift.
 - **Output**: `data/curated/non_hard_subset_with_gt_map.jsonl`.
 - **Dependency**: Depends on T011 and T012c.
 - **Traceability**: Ensures GT validity for synthetic issues (FR-008).
- [X] T013-Mutate [P] [US1] **Implement Mutation Logic**.
 - **Input**: `data/curated/non_hard_subset_with_gt_map.jsonl` (T013a).
 - **Logic**: Implement `code/data/mutate.py::apply_mutations` to apply mutations (rename variables, remove all comments, and apply **structural obfuscation** via control flow reordering or API signature changes) to generate a set of issues.
 - **Constraint**: Generate `min(SYNTHETIC_COUNT, len(non_hard_subset))` synthetic issues (from config.py T002). Do NOT exceed the available input pool.
 - **Output**: List of mutated issues with original code hashes.
 - **Traceability**: Aligns with Spec FR-002 and FR-009.
- [X] T013-GTMap [P] [US1] **Map Ground Truth for Mutations**.
 - **Input**: Output from T013-Mutate and `data/curated/non_hard_subset_with_gt_map.jsonl` (T013a).
 - **Logic**: Assign the `ground_truth_lines` from the original unmutated code to the mutated issue, adjusting for line shifts if necessary (or storing original indices as per FR-008).
 - **Output**: List of synthetic issues with mapped GT lines.
 - **Dependency**: Depends on T013-Mutate.
 - **Traceability**: Ensures GT validity (FR-008).
- [X] T013-Validate [P] [US1] **Validate AST Parseability**.
 - **Input**: Output from T013-GTMap.
 - **Logic**: Ensure mutated code is syntactically valid (AST parseable). Skip invalid mutations and log warnings.
 - **Output**: List of valid synthetic issues.
 - **Dependency**: Depends on T013-GTMap.
 - **Traceability**: Ensures syntactic validity.
- [X] T013-Output [US1] **Generate Synthetic Issues Output**.
 - **Input**: Output from T013-Validate.
 - **Logic**: Write valid synthetic issues to `data/curated/synthetic_issues.jsonl`.
 - **Output**: `data/curated/synthetic_issues.jsonl`.
 - **Dependency**: Depends on T013-Validate.
 - **Traceability**: Final output for synthetic issues.
- [X] T014 [US1] **Metadata & Versioning**.
 - Save `data/curated/synthetic_issues_meta.json` containing original code hashes, mutation parameters, and the exact count generated.
 - Run `hash_artifacts.py` on `data/curated/` files.
- [X] T015 [US1] **Generate Validation Report**.
 - Input: `data/curated/hard_subset.jsonl`.
 - Logic: Select `VALIDATION_SAMPLE_SIZE` (from config.py T002) random issues.
 - Output: Markdown table with columns [IssueID, CoverageScore, ComplexityScore, Notes].
 - **Note**: This report is a **tool for manual inspection**, not an automated validation result.
- [X] T016-AutoValidate [US1] **Automated Validation Gate with Manual Review**.
 - **Action**: Run `code/data/validate_hard.py` to automatically verify the "hard" subset against the coverage threshold and generate a validation report.
 - **Logic**: The script checks if the selected "hard" issues (by Coverage) exhibit low coverage (as a sanity check), generates a CSV report for manual notes, and **includes a "Plan Alignment Justification" block** documenting the decision to use Coverage over Complexity to align with Spec FR-001.
 - **Output**: `data/curated/validation_report.md`, `data/curated/validation_manual_review.csv` (for human notes), and `data/curated/validation_status.json` (status: "PASSED" or "WARNING").
 - **Constraint**: The pipeline **MUST NOT proceed** to Phase 4 until a human reviewer manually inspects `validation_report.md`, adds notes to the CSV, and sets a flag `MANUAL_REVIEWED=true` in `data/curated/validation_status.json`.
 - **Dependency**: Phase 4 agents depend on T016-AutoValidate completion (specifically the manual review flag).
 - **Traceability**: Resolves FR-010 by enforcing manual inspection and consolidating T052 logic.

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
 - **Dependency**: Depends on T012 (data generation), T012c (non-hard), and T016-AutoValidate (manual review flag). **Not parallel**: Must wait for T016-AutoValidate.
 - **Prerequisite**: Phase 4 agents depend on this task.
- [X] T022 [P] [US2] **Static Multi-Query Baseline**.
 - **Requirement**: Run a configurable number of parallel queries per issue, as defined by `BASELINE_QUERY_COUNT` in `config.py`. to match iterative budget.
 - **Input**: `data/results/locked_hard_subset.jsonl` (T021).
 - **Deliverable**: Create `code/agent/static_baseline.py` to perform this execution.
 - **Output**: `data/results/baseline_logs.jsonl` (Unique path to avoid race conditions).
 - **Logging**: Explicitly log `issue_id`, `query_count`, `retrieved_context_ids`, and `coverage_score`.
 - **Dependency**: Depends on T021 completion.
- [X] T023 [P] [US2] **Iterative Agent**.
 - **Requirement**: Enforce a configurable turn limit with a defined default.
 - **Turn Logic**: Query -> Retrieve -> Static Analysis -> Reformulate (if error).
 - **Loop Detection**: Detect repeated queries to break loops early.
 - **Input**: `data/results/locked_hard_subset.jsonl` (T021).
 - **Output**: `data/results/iterative_logs.jsonl` (Unique path to avoid race conditions).
 - **Logging**: Explicitly log `issue_id`, `query_history`, `static_analysis_signals`, `turn_reasons`.
 - **Dependency**: Depends on T021 completion.
- [X] T024a [US2] **Turn-Limit Sweep: Sampling**.
 - **Logic**: Generate a specific sample list file for `SWEEP_SAMPLE_SIZE` (from config.py, default unspecified) issues (random sample with **a fixed seed**, stratified by `complexity_score` quartiles from `data/curated/hard_subset.jsonl`).
 - **Output**: `data/results/sweep_sample_list.json`.
 - **Dependency**: Depends on T012 (stratification).
- [X] T024b-Driver [US2] **Turn-Limit Sweep: Driver Implementation**.
 - **Logic**: Implement `code/analysis/sweep_driver.py::run_sweep` to load the sample and iterate through a range of turn limits.
 - **Output**: Intermediate state for execution.
 - **Dependency**: Depends on T024a.
- [X] T024b-Exec [US2] **Turn-Limit Sweep: Execution**.
 - **Logic**: Invoke the iterative agent for each turn limit in the loop defined by T024b-Driver.
 - **Output**: Raw execution logs per turn limit.
 - **Dependency**: Depends on T024b-Driver.
- [X] T024b-Agg [US2] **Turn-Limit Sweep: Aggregation**.
 - **Logic**: Aggregate results from T024b-Exec into `data/results/sweep_execution_logs.json`.
 - **Output**: `data/results/sweep_execution_logs.json`.
 - **Dependency**: Depends on T024b-Exec.
- [X] T024c [US2] **Turn-Limit Sweep: Final Aggregation**.
 - **Logic**: Aggregate results into `data/results/sweep_results.json` containing columns: `issue_id`, `turns_used`, `coverage`, `stability_flag` for each turn limit.
 - **Dependency**: Depends on T024b-Agg.
- [X] T025 [US2] **Hash Artifacts**.
 - Integrate `hash_artifacts.py` to hash `data/results/agent_logs/`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Comparative Metric Calculation and Statistical Testing (Priority: P3)

**Goal**: Compute line-level coverage and ranking efficiency, apply **Wilcoxon signed-rank test** (with exact permutation for ties/censoring as per Spec FR-006), apply **Survival Analysis** for ranking efficiency (per Plan), with Bonferroni correction, and frame results associatively.

**Independent Test**: Provide pre-computed metrics for a small set and verify the statistical test returns a p-value and correct conclusion (significant vs. non-significant) at p < 0.05 threshold.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Contract test for result schema in `tests/contract/test_result_schema.py`
- [X] T027 [P] [US3] Unit test for statistical tests in `tests/unit/test_stats.py`. **Includes**: Wilcoxon signed-rank test implementation AND **exact permutation test logic for censored/tied data** (as per Spec FR-006) to validate the implementation before the main analysis runs.

### Implementation for User Story 3

- [X] T028 [P] [US3] Implement `code/metrics/coverage.py` to calculate % of `ground_truth_lines` retrieved
- [X] T029 [P] [US3] Implement `code/metrics/ranking.py` to calculate position of first relevant line (handle censored data with penalty N+1)
- [X] T030-Wilcoxon [US3] **Coverage & Ranking Analysis (Primary)**.
 - **Requirement**: Implement **Wilcoxon signed-rank test** as per **Spec FR-006** and **SC-003** for **Coverage** metrics.
 - **Method**: Apply Wilcoxon signed-rank test to paired coverage data.
 - **Censoring Handling**: If censored data exists (ranking == N+1), apply an **exact permutation test** (as authorized by FR-006 for ties/censoring) instead of Survival Analysis for the **Coverage** metric if ties dominate.
 - **Output**: P-values and effect sizes for coverage.
 - **Traceability**: Implements Spec FR-006/SC-003.
- [X] T030-Survival [US3] **Ranking Efficiency Analysis (Survival)**.
 - **Requirement**: Implement **Survival Analysis (Cox proportional hazards)** as per **Plan Phase 2** for **Ranking Efficiency** metrics to handle censored data.
 - **Method**: Fit a Cox model to the ranking data (time-to-event) with censoring indicators.
 - **Output**: Hazard ratios, p-values, and confidence intervals for ranking efficiency.
 - **Traceability**: Implements Plan Phase 2 requirement for Survival Analysis on ranking data.
- [X] T030c [US3] **Multiplicity Correction, Framing & Hashing**.
 - **Correction**: Apply **Bonferroni correction** to the family of tests: **Coverage** (Wilcoxon/Permutation), **Ranking** (Survival).
 - **Framing**: Frame all results as **"associational differences"** per FR-007.
 - **Hashing**: Hash `data/results/final_metrics.json` immediately after generation.
 - **Output**: `data/results/final_metrics.json` (includes adjusted p-values) and `data/results/final_metrics.hash`.
 - **Dependency**: Depends on T030-Wilcoxon and T030-Survival.
- [X] T031 [US3] Implement `code/analysis/plots.py` for visualization of coverage and ranking distributions
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
- [X] T033b-Vars [US3] **Report Generation: Define Variables**.
 - **Logic**: Map extracted data to Jinja2 template variables.
 - **Output**: Variable mapping object.
 - **Dependency**: Depends on T033a.
- [X] T033b-Populate [US3] **Report Generation: Populate Sections**.
 - **Logic**: Populate Abstract, Methods, Results, and Discussion sections with mapped variables.
 - **Constraint**: Enforce "associational differences" language in Results/Discussion.
 - **Output**: Populated section strings.
 - **Dependency**: Depends on T033b-Vars.
- [X] T033b-Render [US3] **Report Generation: Template Rendering**.
 - **Logic**: Load the template (T033-Zero) and render the populated sections into `data/results/report_draft.md`.
 - **Output**: `data/results/report_draft.md` (intermediate artifact).
 - **Dependency**: Depends on T033b-Populate.
- [X] T033d [US3] **Validate Report Language**.
 - **Requirement**: Implement a validator to ensure `paper/draft.md` does not contain causal language.
 - **Logic**: Run a regex scan and an LLM-based check (using a lightweight prompt) for keywords like "proves", "causes", "guarantees". Fail the build if found.
 - **Output**: `data/results/report_validation_report.json` (status: "PASSED" or "FAILED").
 - **Dependency**: Depends on T033b-Render.
- [X] T033c [US3] **Report Generation: Final Assembly & Validation**.
 - Logic: Assemble `paper/draft.md` and validate against schema using `report_draft.md` and T033d results.
 - **Output**: `paper/draft.md` and `data/results/report_validation_report.json`.
 - **Dependency**: Depends on T033b-Render and T033d.
- [X] T034 [US3] **Generate Results Summary**.
 - **Action**: Execute T033a -> T033b -> T033d -> T033c pipeline.
 - **Output**: `paper/results_summary.md` (containing Abstract draft, Methods summary, Results, Discussion).
 - **Constraint**: Scope limited to spec requirements (SC-004, FR-007); no full manuscript generation.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T035 [P] Update `docs/quickstart.md` with execution instructions and data flow diagrams. **Includes**: Quickstart validation steps.
- [X] T036 Refactor `code/agent/iterative.py` to reduce cyclomatic complexity.
- [X] T037 Optimize memory usage in `code/metrics/coverage.py` by processing lines in chunks.
- [X] T038 [P] Add unit tests for `code/analysis/stats.py` (Wilcoxon and Permutation test logic).
- [X] T051 [US3] **Implement Deterministic Runtime Monitor**.
 - **Requirement**: Refactor `code/main.py` to implement a "Sample Size Lock" mechanism.
 - **Logic**: Before execution, estimate the time required for the full sample size. If the estimate exceeds 5.5 hours, **reduce the sample size** to a fixed value that guarantees completion within 6 hours. This ensures the final N is fixed and reproducible *before* execution starts, avoiding runtime-dependent aborts.
 - **Traceability**: Fixes SC-005 (Compute Feasibility) and Constitution Principle I (Reproducibility) by ensuring fixed N.
- [X] T042 [US1] **Stream Large Datasets**.
 - **Requirement**: Refactor `code/data/derive_gt.py::load_dataset_streaming` to use `datasets.load_dataset(..., streaming=True)` and process ground truth derivation in chunks to prevent OOM errors on constrained-memory runners.
 - **Traceability**: Implements SC-005 (Compute Feasibility) and ensures reproducibility.
- [X] T043 [US2] **Implement CPU-Quantized Model Wrapper**.
 - **Requirement**: Create `code/agent/quantized_llm.py` to use `llama-cpp-python` with a 4-bit quantized model (e.g., `Qwen-2.5-1.5B-Instruct-GGUF`) to ensure inference fits within 7GB RAM, replacing any default precision assumptions.
 - **Traceability**: Implements SC-005 (Compute Feasibility).
- [X] T044 [US2] **Add Turn-Loop Detection Logic**.
 - **Requirement**: Update `code/agent/iterative.py::detect_loop` to explicitly detect and break infinite loops if the reformulated query matches a previous turn's query string within a limited conversation history window.
 - **Traceability**: Implements Spec Edge Case (loop detection) and FR-003 (Turn Limit).
- [X] T046 [US3] **Verify Bonferroni Correction**.
 - **Requirement**: Implement `tests/contract/test_result_schema.py::test_bonferroni_adjusted_pvalue` to validate that the `final_metrics.json` explicitly includes the adjusted p-value and the correction factor used, ensuring FR-007 compliance.
 - **Traceability**: Implements SC-004 (Multiplicity Correction).
- [X] T050 [US3] **Document Streaming Strategy for Large Datasets**.
 - **Requirement**: Update `docs/quickstart.md` to explicitly describe the streaming strategy used in T042.
 - **Logic**: Explain how `datasets.load_dataset(..., streaming=True)` is used to process the SWE-Explore dataset without loading it entirely into RAM, and how chunks are processed online.
 - **Traceability**: Implements SC-005 (Compute Feasibility) and ensures reproducibility.
- [X] T052 [US1] **Implement Hard Instance Proxy Validation Script**. [DEPRECATED: Logic merged into T016-AutoValidate]
 - **Note**: This task is deprecated. Its logic (CSV generation, manual review flag) has been consolidated into Task T016-AutoValidate to avoid duplication. No further action required.
- [X] T053 [US2] **Implement Static Analysis Fallback Handler**.
 - **Requirement**: Update `code/agent/static_analysis.py` to handle cases where `pylint` returns no output or crashes.
 - **Logic**: If `pylint` fails or returns empty, catch the `PylintError` or empty output, log a `NEUTRAL_SIGNAL` in the turn log, and proceed to the next turn without reformulating the query based on that specific turn's analysis, as per Spec Edge Case "static analysis tool returning no output".
 - **Traceability**: Implements Spec Edge Case (Static Analysis Failure) and FR-004. Depends on T019.
- [X] T054 [US2] **Implement Query Repetition Breaker**.
 - **Requirement**: Enhance `code/agent/iterative.py` to detect if the reformulated query is identical (or >95% similar) to the previous turn's query.
 - **Logic**: If a repeat is detected (similarity > 95%), terminate the loop early, log `TERMINATION_REASON: QUERY_LOOP_DETECTED`, and record the final state.
 - **Traceability**: Implements Spec Edge Case (Loop Detection) and FR-003. Depends on T023.
- [X] T055 [US3] **Implement Exact Permutation Test Fallback**.
 - **Requirement**: Create `code/analysis/permutation.py` to perform an exact permutation test for paired data when ties dominate (as per FR-006).
 - **Logic**: If the number of non-zero differences is < 10 or ties > 50%, switch from Wilcoxon to exact permutation test. Log the switch reason.
 - **Traceability**: Implements Spec FR-006 (Tie Handling) and SC-003. Depends on T030-Wilcoxon.
- [X] T056 [US3] **Implement Censoring Penalty Logic**.
 - **Requirement**: Update `code/metrics/ranking.py` to handle the "no relevant lines found" case.
 - **Logic**: Assign a penalty score of `N+1` (where N is the total number of lines in the repository) for censored data points to ensure they are ranked last but included in the statistical test.
 - **Traceability**: Implements Spec FR-005 (Ranking Efficiency) and FR-006 (Censoring Handling). Depends on T029.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for data (specifically `hard_subset.jsonl` and `validation_status.json` with manual review flag)
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
4. **STOP and VALIDATE**: Test User Story 1 independently (and pass automated gate T016-AutoValidate with manual review)
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
- **CPU Feasibility**: Ensure all model tasks use CPU-only, <1B param or 4-bit quantized models on 2-core/7GB RAM. No CUDA/GPU.
- **Constraint Preservation**: All tasks must strictly implement the metrics and counts defined in FR-001, FR-002, SC-004, and FR-007.
 - **Hard Instance Selection**: Must use **initial coverage scores** (Spec FR-001) as the primary path (T012) to align with the benchmark definition. Complexity is diagnostic (T012).
 - **Synthetic Issues**: Must generate min(SYNTHETIC_COUNT, len(non_hard_subset)) issues (T013).
 - **Statistics**: Coverage uses Wilcoxon signed-rank test with exact permutation for ties/censoring (T030-Wilcoxon) as per Spec FR-006. Ranking uses Survival Analysis (T030-Survival) as per Plan.
 - **Correction**: Bonferroni applied to Coverage, Ranking tests.
- **Data Integrity**: All analysis tasks must consume REAL data from `data/curated/`. No synthetic/fake input data generation tasks are permitted.
- **Execution Order**: Tasks producing results (T023) MUST follow tasks generating those results (T021, T022). Tasks verifying results (T030) MUST follow result generation.
- **Automated Validation**: Phase 4 cannot start until T016-AutoValidate completes successfully with manual review.
- **Real Data Enforcement**: Tasks T010, T011, T012, T013, T042, T043, T044, T046, T050, T051 specifically address the requirement to use real data streams, fail loudly on fetch errors, and avoid synthetic fallbacks or fake GPU simulations.
- **New Revision Tasks**: T053-T056 address specific reviewer concerns regarding manual validation of the "hard" proxy, robustness of the static analysis loop, handling of censored data in ranking metrics, and the fallback logic for statistical tests when ties dominate.