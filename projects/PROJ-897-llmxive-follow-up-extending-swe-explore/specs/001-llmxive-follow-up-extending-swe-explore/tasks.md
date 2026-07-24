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

## Phase 0: Plan Alignment & Amendment

**Purpose**: Resolve contradictions between Spec and Plan before implementation begins.

- [ ] T000 [P] **Plan Amendment: Methodology Alignment**.
 - **Action**: Edit `plan.md` (Section 'Phase 0: Data Curation') to explicitly adopt `initial_coverage` for "hard" instance selection as per Spec FR-001, removing the "Cyclomatic Complexity" mandate and the prohibition of `initial_coverage`.
 - **Action**: Edit `plan.md` (Section 'Phase 2: Metric Calculation') to remove "Survival Analysis" and replace with "Exact Permutation Test" for censored data, aligning with Spec FR-006.
 - **Action**: Edit `plan.md` (Section 'Compute Feasibility') to explicitly state that float32 is likely infeasible and the primary strategy is 8-bit quantization.
 - **Output**: Updated `plan.md`.
 - **Dependency**: Must be completed before T002 and T012.
 - **Traceability**: Resolves Spec vs Plan contradiction (FR-001 vs Plan Phase 0) and Plan vs Spec contradiction (Survival Analysis vs FR-006).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan: Create directories `code/`, `data/raw/`, `data/curated/`, `data/results/`, `tests/unit/`, `tests/contract/`, `contracts/`, `docs/`, `paper/` AND configure linting (ruff/flake8) and formatting (black) tools.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 [P] Implement `code/config.py` to define paths (`data/raw/`, `data/curated/`, `data/results/`), random seeds, model config (CPU-only), AND critical thresholds: `COMPLEXITY_THRESHOLD` (default 50), `HARD_INSTANCE_PERCENTILE` (default 0.20), `MIN_SYNTHETIC_ISSUES` (default 10), `VALIDATION_SAMPLE_SIZE` (default 5).
- [X] T003 [P] Implement `code/utils/hash_artifacts.py` for automated SHA256 hashing of `data/` artifacts (Constitution Principle V)
- [X] T004 [P] Create `contracts/` directory with `dataset_schema.yaml`, `agent_log_schema.yaml`, `result_schema.yaml`
- [X] T005 [P] Implement `code/utils/validation.py` for JSONL/Parquet schema validation against contracts
- [X] T006 [P] Setup `pytest` configuration and `tests/contract/test_schemas.py` skeleton

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Curation and Hard Instance Selection (Priority: P1) 🎯 MVP

**Goal**: Download SWE-Explore, derive ground truth, select "hard" instances based on **initial coverage scores** (Spec FR-001) to ensure alignment with the benchmark's definition of "hard" (low retrieval success), and generate a set of synthetic ambiguous issues.

**Independent Test**: Verify the existence of `data/curated/hard_subset.jsonl`, `data/curated/non_hard_subset.jsonl`, `data/curated/synthetic_issues.jsonl`, and `data/curated/validation_report.md` with correct schemas and valid AST parsing for synthetic issues.

### Test Definition for User Story 1 (MUST BE WRITTEN FIRST) ⚠️

> **NOTE**: These tasks define the tests. They must be written *before* implementation tasks but executed *after* implementation.

- [X] T007 [P] [US1] Contract test for dataset schema in `tests/contract/test_dataset_schema.py` (Depends on T004 schema output)
- [X] T008 [P] [US1] Unit test for mutation logic (variable rename, comment removal) in `tests/unit/test_mutation.py`
- [X] T009 [P] [US1] Unit test for synthetic issue validity (AST parse check) in `tests/unit/test_synthetic_validity.py`

### Implementation for User Story 1

- [X] T010 [P] [US1] **Implement Robust Data Fetcher**.
 - **Requirement**: Implement `code/data/download.py` to fetch `bench.final.public.jsonl` from HuggingFace.
 - **Constraint**: **Fail Loudly**: If the HuggingFace `load_dataset` call fails (timeout, 404, 500), the script MUST raise a `ConnectionError` or `ValueError` with a clear message. **NO** synthetic fallback logic (`try/except` with `generate_synthetic_*`) is permitted.
 - **Streaming**: Use `datasets.load_dataset(..., streaming=True)` to process in chunks, preventing OOM on constrained runners (FR-013).
 - **Output**: `data/raw/swe_explore_raw.jsonl`.
 - **Traceability**: Implements Spec FR-001 and addresses "Fail Loudly" rule.
- [X] T011 [P] [US1] **Implement Ground Truth Derivation with Streaming**.
 - **Requirement**: Implement `code/data/derive_gt.py` to parse solution patches and generate `ground_truth_lines` lists.
 - **Constraint**: Use `datasets.load_dataset(..., streaming=True)` to iterate through the raw dataset in chunks, deriving GT lines for each issue and writing to a temporary file or accumulating online, ensuring peak memory < 7GB.
 - **Output**: `data/raw/swe_explore_with_gt.jsonl`.
 - **Traceability**: Implements Spec FR-008 and addresses "Stream Large Datasets" rule.
- [X] T012 [US1] **Filter Hard Subset (Spec Alignment)**.
 - **Requirement**: Implement filtering based on **initial coverage scores** as per **Spec FR-001** to identify "hard" instances (bottom `HARD_INSTANCE_PERCENTILE` of scores).
 - **Input**: `data/raw/swe_explore_with_gt.jsonl` (T011 output).
 - **Logic**: Select the bottom `HARD_INSTANCE_PERCENTILE` (configurable, default 0.20) of `initial_coverage` scores. **Handle Missing Data**: If `initial_coverage` is missing or null, skip the issue and log a warning. Do not impute.
 - **Plan Override**: This task implements the methodology defined in Spec FR-001, overriding the Plan's previous "Cyclomatic Complexity" mandate. This override is ratified by T000-PlanAmend.
 - **Diagnostic**: Calculate Cyclomatic Complexity for each issue and append as `metadata.complexity_score` to `hard_subset.jsonl` (does NOT affect selection).
 - **Deliverable**: Create `code/data/filter_hard.py` to perform this calculation and selection.
 - **Output**: `data/curated/hard_subset.jsonl`.
 - **Dependency**: **Must verify `code/config.py` (T002) exists and T000-PlanAmend is complete.** T002 must complete first.
 - **Traceability**: Implements Spec FR-001.
- [X] T012c [US1] **Generate Non-Hard Subset**.
 - **Requirement**: Compute the complement of the Primary Hard Subset (T012) to provide the input pool for synthetic generation.
 - **Logic**: Select all issues from the full dataset that are NOT in `data/curated/hard_subset.jsonl`.
 - **Implementation**: Create `code/data/filter_non_hard.py`. Read `data/raw/swe_explore_with_gt.jsonl` and `data/curated/hard_subset.jsonl`. Write to `data/curated/non_hard_subset.jsonl`.
 - **Output**: `data/curated/non_hard_subset.jsonl`.
 - **Dependency**: **Blocking dependency** on T012 completion.
 - **Traceability**: Resolves ordering-064eff0b by providing the correct input for T013.
- [X] T013 [US1] **Generate Synthetic Ambiguous Issues**.
 - **Input**: `data/curated/non_hard_subset.jsonl` (T012c output).
 - **Logic**: Apply mutations to generate a set of issues.
 - **Mutation Strategies**:
   1. **Variable Rename**: Rename all local variables using a deterministic hash-based mapping.
   2. **Comment Removal**: Strip all comments (single-line and multi-line).
   3. **Structural Obfuscation**: Use `libcst` to reorder independent `if`/`else` blocks and rename function arguments (API signature changes).
 - **Constraint**: **Dynamic Generation**: Generate ALL valid mutations from the input pool. **DO NOT** use a fixed cap (e.g., 50).
 - **Hard Fail Logic**: If the total count of valid mutations is 0, the script MUST fail loudly with a `ValueError`. If the count is > 0 but < `MIN_SYNTHETIC_ISSUES` (default 10), log a `CRITICAL` warning with the exact count and **proceed** with the available set.
 - **Safety**: If the pool is smaller than `MIN_SYNTHETIC_ISSUES`, generate all possible valid mutations.
 - **Output**: `data/curated/synthetic_issues.jsonl`.
 - **Oracle**: Derive `ground_truth_lines` from the original unmutated code (FR-008).
 - **Validity**: Ensure mutated code is syntactically valid (AST parseable). Skip invalid mutations and log warnings.
 - **Deliverable**: Create `code/data/mutate.py` to implement this logic.
 - **Traceability**: Aligns with Spec FR-002 and addresses runtime constraint SC-005.
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
 - **Logic**: The script checks if the selected "hard" issues (by Coverage) exhibit low coverage (as a sanity check) and **includes a "Plan Override Justification" block** documenting the decision to use Coverage over Complexity to align with Spec FR-001 (ratified by T000).
 - **Output**: `data/curated/validation_report.md` and `data/curated/validation_status.json`.
 - **Schema**: `validation_status.json` MUST contain keys: `status` (string: "PASSED" or "WARNING"), `message` (string), `sample_size` (int).
 - **Constraint**: The pipeline proceeds automatically regardless of status; manual review is optional. "WARNING" logs an issue but does not block Phase 4.
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
 - **Dependency**: Depends on T012 (data generation), T012c (non-hard), and T016-AutoValidate (manual review flag). **Not parallel**: Must wait for T016-AutoValidate.
 - **Prerequisite**: Phase 4 agents depend on this task.
- [X] T022 [P] [US2] **Static Multi-Query Baseline**.
 - **Requirement**: Run **parallel queries** per issue (matching the iterative limit of 3 turns defined in Spec FR-003) to ensure a fair comparison of feedback mechanisms vs. search volume.
 - **Input**: `data/results/locked_hard_subset.jsonl` (T021).
 - **Deliverable**: Create `code/agent/static_baseline.py` to perform this execution.
 - **Output**: `data/results/baseline_logs.jsonl` (Unique path to avoid race conditions).
 - **Logging**: Explicitly log `issue_id`, `query_count`, `retrieved_context_ids`, and `coverage_score`.
 - **Dependency**: Depends on T021 completion.
- [X] T043-MemCheck [US2] **Memory Pre-Flight Check**.
 - **Requirement**: Create `code/agent/memory_check.py` to profile available RAM and estimate model load requirements.
 - **Logic**: Calculate `available_ram = total_ram - os_overhead`. If `available_ram < 7GB`, set `force_quantization = True` in output `data/results/memory_profile.json`. If `available_ram >= 7GB`, set `force_quantization = False`.
 - **Output**: `data/results/memory_profile.json` (flags: `force_quantization`, `estimated_ram`).
 - **Dependency**: Must run before T043-Execution.
- [X] T043-Execution [US2] **Implement CPU-Quantized Model Execution**.
 - **Requirement**: Create `code/agent/quantized_llm.py` to use `llama-cpp-python` with a **strict binary decision** based on T043-MemCheck output.
 - **Logic**: Read `data/results/memory_profile.json`.
   1. If `force_quantization` is **True**: Load **8-bit quantized** model immediately.
   2. If `force_quantization` is **False**: Load **float32** model. **Do not fallback** to quantization inside this task; the pre-flight check is the sole decision maker.
 - **Constraint**: Explicitly use `n_gpu_layers=0` and optimized `n_ctx` for CPU inference. Add runtime check to fail if memory > 7GB.
 - **Traceability**: Implements FR-014 and SC-005, aligning with Plan's risk mitigation strategy (updated by T000).
 - **Dependency**: Depends on T043-MemCheck completion.
- [X] T023 [P] [US2] **Iterative Agent**.
 - **Requirement**: Enforce a configurable turn limit with a defined default.
 - **Turn Logic**: Query -> Retrieve -> Static Analysis -> Reformulate (if error).
 - **Loop Detection**: Implement `detect_loop` to break infinite loops if reformulated query matches a previous turn's query string within a limited conversation history window.
 - **Input**: `data/results/locked_hard_subset.jsonl` (T021).
 - **Output**: `data/results/iterative_logs.jsonl` (Unique path to avoid race conditions).
 - **Logging**: Explicitly log `issue_id`, `query_history`, `static_analysis_signals`, `turn_reasons`.
 - **Dependency**: Depends on T021 completion and T043-Execution (Quantized Model).
- [X] T024a [US2] **Turn-Limit Sweep: Sampling**.
 - **Logic**: Generate a specific sample list file for **N=100** issues (random sample with **seed 42**, stratified by `complexity_score` quartiles from `data/curated/hard_subset.jsonl`).
 - **Data Source**: Read `complexity_score` from the `metadata` field of `hard_subset.jsonl` (generated in T012).
 - **Output**: `data/results/sweep_sample_list.json`.
 - **Dependency**: Depends on T012 (stratification).
- [X] T024b [US2] **Turn-Limit Sweep: Execution**.
 - **Logic**: Execute the iterative agent loop for each turn limit in the range **[1, 2, 3]**.
 - **Parameter**: Pass `max_turns` dynamically to the agent execution script for each iteration.
 - **Command**: Run `python code/main.py --turn-limit 1`, then `--turn-limit 2`, etc.
 - **Output**: `data/results/sweep_execution_logs.json` (aggregated logs for all turn limits).
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

**Goal**: Compute line-level coverage and ranking efficiency, apply **Wilcoxon signed-rank test** as the primary success criterion (Spec SC-003), with **Exact Permutation Test** as the fallback for ties/censored data.

**Independent Test**: Provide pre-computed metrics for a small set and verify the statistical test returns a p-value and correct conclusion (significant vs. non-significant) at p < 0.05 threshold.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Contract test for result schema in `tests/contract/test_result_schema.py`
- [X] T027 [P] [US3] Unit test for statistical tests in `tests/unit/test_stats.py`. **Includes**: Wilcoxon signed-rank test implementation AND **censored data handling logic (N penalty assignment) for Permutation Test validation**. This task explicitly validates the logic required for T030-Permutation, ensuring that censored entries are handled correctly before the main analysis runs.

### Implementation for User Story 3

- [X] T028 [P] [US3] Implement `code/metrics/coverage.py` to calculate % of `ground_truth_lines` retrieved
- [X] T029 [P] [US3] Implement `code/metrics/ranking.py` to calculate position of first relevant line (handle censored data with penalty N+1)
- [X] T030-Prep [US3] **Censoring Check & Routing**.
 - **Requirement**: Analyze `data/results/baseline_logs.jsonl` and `data/results/iterative_logs.jsonl` to determine if "Ranking Efficiency" data contains censored values.
 - **Logic**: Check for `coverage_score == 0.0` or `retrieved_lines == []` to identify censored data.
 - **Tie Definition**: Calculate "ties" as ties in the **absolute difference scores** of the paired data. Include censored pairs (N+1 penalty) in this calculation.
 - **Thresholds**: Define "ties > 10%" as `tie_proportion > 0.10`.
 - **Routing**:
 - If censored data exists (>0%) AND Wilcoxon is invalid (ties > 10%): Route to T030-Permutation.
 - If ties > 10% (even if no censoring): Route to T030-Permutation.
 - Otherwise: Route to T030-Primary (Wilcoxon).
 - **Output**: `data/results/statistical_routing.json` (flag: "PERMUTATION" or "WILCOXON").
 - **Dependency**: Depends on T022, T023.
- [X] T030-Primary [P] [US3] **Coverage & Ranking Analysis (Wilcoxon - Spec Primary)**.
 - **Requirement**: Implement **Wilcoxon signed-rank test** as per **Spec FR-006** and **SC-003** as the PRIMARY success criterion.
 - **Method**: Apply Wilcoxon signed-rank test to paired coverage data and paired ranking data (with continuity correction for ties).
 - **Output**: P-values and effect sizes for both metrics.
 - **Traceability**: Implements Spec FR-006/SC-003 as the primary path.
 - **Dependency**: Depends on T030-Prep routing to "WILCOXON".
- [X] T030-Permutation [US3] **Exact Permutation Test for Ties/Censoring**.
 - **Requirement**: Implement **Exact Permutation Test** as per **Spec FR-006** if ties > 10% or censored data is present.
 - **Method**: Apply exact permutation test to paired data to handle dominant ties and censored entries (using N+1 penalty).
 - **Output**: P-values and effect sizes.
 - **Traceability**: Implements Spec FR-006 (ties/censoring handling).
 - **Dependency**: Depends on T030-Prep routing to "PERMUTATION".
- [X] T030c [US3] **Multiplicity Correction & Framing**.
 - **Correction**: Apply **Bonferroni correction** to the family of tests: **Coverage**, **Ranking (Wilcoxon/Permutation)**.
 - **Framing**: Frame all results as **"associational differences"** per FR-007.
 - **Output**: `data/results/final_metrics.json`.
 - **Dependency**: Depends on T030-Primary or T030-Permutation.
- [X] T031 [US3] Implement `code/analysis/plots.py` for visualization of coverage and permutation curves
- [ ] T032 [US3] Integrate `hash_artifacts.py` to hash final `data/results/final_metrics.json`
- [X] T033-Zero [US3] **Create Report Template**.
 - **Action**: Create `code/analysis/report_template.j2` with sections: Abstract, Methods, Results, Discussion.
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
 - **Dependency**: Depends on T033a and T033-Zero.
- [X] T033d [US3] **Validate Report Language (Regex)**.
 - **Requirement**: Implement a deterministic validator to ensure `data/results/report_draft.md` does not contain causal language.
 - **Logic**: Run a regex scan `r'\b(proves|causes|guarantees|demonstrates causality)\b'` against the draft. Fail the build if any match is found.
 - **Output**: `data/results/report_validation_report.json` (status: "PASSED" or "FAILED").
 - **Dependency**: Depends on T033b.
 - **Traceability**: Implements FR-007 (Causal Language Validation).
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
- [X] T038 [P] Add unit tests for `code/analysis/stats.py` (Wilcoxon and Permutation Test logic).
- [X] T039 [US2/US3] Implement runtime monitor in `code/main.py` to track total execution time. **Logic**: If elapsed time > 5.5 hours (SC-005), abort remaining non-critical sweeps or reduce sample size to ensure completion within 6 hours.
- [X] T046-StatsValidation [US3] **Verify Bonferroni Correction**.
 - **Requirement**: Implement `tests/contract/test_result_schema.py::test_bonferroni_adjusted_pvalue` to validate that the `final_metrics.json` explicitly includes the adjusted p-value and the correction factor used.
 - **Traceability**: Implements SC-004.
- [X] T046-FramingValidation [US3] **Verify Causal Language Framing**.
 - **Requirement**: Implement `tests/contract/test_report_validation.py::test_causal_language` to validate that the final report avoids causal claims (FR-007).
 - **Traceability**: Implements FR-007.

---

## Phase N+1: Revision & Stability (Addressing Review Concerns)

**Purpose**: Address specific reviewer concerns regarding data integrity, execution robustness, and statistical validity.

- [ ] T047 [US2] **Implement Deterministic Loop Detection & Early Exit**.
 - **Requirement**: Enhance `code/agent/iterative.py` to detect when the agent enters a query loop (repeating the same query or a semantically identical query) before hitting the 3-turn limit.
 - **Logic**: Compare current query against the last few turns using a simple hash or string similarity. If a repeat is detected, terminate the loop immediately, log `termination_reason: "loop_detected"`, and record the current coverage.
 - **Traceability**: Addresses Edge Case "What if the 3-turn limit is reached but the agent is in a loop?".
- [ ] T048 [US1] **Implement Robust Mutation Fallback with Hard Fail**.
 - **Requirement**: Ensure `code/data/mutate.py` handles cases where the input pool is smaller than `MIN_SYNTHETIC_ISSUES`.
 - **Logic**: If the pool size < 10, generate all valid mutations, log a `WARNING` with the exact count generated, and **fail loudly** if the resulting count is 0. If count > 0 but < 10, proceed with warning.
 - **Traceability**: Addresses Edge Case "What happens when a synthetic ambiguous issue becomes unsolvable due to over-mutation?" and ensures data integrity.
- [ ] T049 [US3] **Implement Permutation Test Sensitivity Check**.
 - **Requirement**: Add a sensitivity analysis task to verify that the Permutation Test results are robust to different definitions of "censored" (e.g., N+1 vs N+10 penalty).
 - **Logic**: Re-run the permutation model with alternative penalty values and compare p-values. Log the variance to `data/results/sensitivity_analysis.json`.
 - **Traceability**: Addresses Edge Case "How does the system handle... unexpected error?" in statistical modeling and ensures result stability.
- [ ] T050 [US2] **Implement Static Analysis Error Handling & Neutral Signal**.
 - **Requirement**: Ensure `code/agent/static_analysis.py` handles cases where `pylint` or `ast` returns no output or crashes.
 - **Logic**: Wrap static analysis calls in a `try/except` block. If an error occurs, log `static_analysis_signal: "neutral_anomaly"`, do not crash the agent, and proceed to the next turn or termination.
 - **Traceability**: Addresses Edge Case "How does the system handle a static analysis tool returning no output?".

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Revision (Phase N+1)**: Depends on Phase N completion and specific reviewer feedback

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

## Parallel Example: User Story 2

```bash
# Launch all models for User Story 2 together (if dependencies met):
Task: "Implement code/agent/static_analysis.py"
Task: "Implement code/agent/prompts.py"
Task: "Implement code/agent/quantized_llm.py" (T043-Execution)

# Note: T023 (Iterative Agent) depends on T043-Execution.
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
- **CPU Feasibility**: Ensure all model tasks use CPU-only, <1B param or 8-bit quantized models on -core/7GB RAM. No CUDA/GPU.
- **Constraint Preservation**: All tasks must strictly implement the metrics and counts defined in FR-001, FR-002, SC-004, and FR-007.
 - **Hard Instance Selection**: Must use **initial coverage scores** (Spec FR-001) as the primary path (T012) to align with the benchmark definition. Complexity is diagnostic (T012-Complexity).
 - **Synthetic Issues**: Must generate all valid mutations with a hard fail if 0, proceed with warning if < 10 (T013).
 - **Statistics**: Coverage and Ranking use Wilcoxon as primary (T030-Primary), Permutation Test (T030-Permutation) if ties > 10% or censored data is present. **Survival Analysis is removed**.
 - **Correction**: Bonferroni applied to Coverage, Ranking tests.
- **Data Integrity**: All analysis tasks must consume REAL data from `data/curated/`. No synthetic/fake input data generation tasks are permitted.
- **Execution Order**: Tasks producing results (T023) MUST follow tasks generating those results (T021, T022). Tasks verifying results (T030) MUST follow result generation.
- **Automated Validation**: Phase 4 cannot start until T016-AutoValidate completes successfully.
- **New Functional Requirements (FR-011 to FR-016)**: Removed. All valid requirements (streaming, quantization, robustness) are now integrated into primary tasks (T010, T011, T043) referencing existing FR-001/002/014.
- **Revision Concerns**: Phase N+1 added to address specific reviewer concerns regarding loop detection, mutation fallback, permutation test sensitivity, and static analysis robustness.
- **Plan Alignment**: T000-PlanAmend must be completed first to resolve Spec/Plan contradictions regarding `initial_coverage` and statistical methods.