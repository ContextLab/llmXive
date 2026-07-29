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

## Phase 0: Plan Alignment (Administrative)

**Purpose**: Acknowledge Spec vs. Plan contradictions and **update the Plan** to ensure logical consistency before execution.

- [ ] T000-Notice [P] **Spec Supremacy & Plan Correction**.
 - **Action**: Acknowledge that `plan.md` contains contradictory text regarding "Hard" instance selection (Cyclomatic Complexity vs. initial_coverage) and statistical methods (Survival Analysis vs. Wilcoxon).
 - **Action**: **Update `plan.md`**: Explicitly edit `plan.md` to remove the "Cyclomatic Complexity" selection logic in Phase 0 and the "Survival Analysis" method in Phase 2, replacing them with the Spec-mandated "initial_coverage" and "Wilcoxon/Permutation" logic respectively.
 - **Action**: Confirm that all subsequent tasks (T012, T030, etc.) implement the **Spec** logic directly, now that the Plan has been corrected.
 - **Verification**: Verify that `plan.md` no longer contains the contradictory text and `tasks.md` does not contain any tasks that wait for `plan.md` to be updated.
 - **Output**: Corrected `plan.md` and this notice.
 - **Dependency**: None.
 - **Traceability**: Resolves Spec vs. Plan contradiction by correcting the Plan document to align with the Spec as the sole execution authority.
 - **Note**: This task is administrative and non-blocking for the *logic*, but the Plan update is a prerequisite for downstream artifact consistency.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] **Create Project Structure**.
 - **Action**: Create directories `code/`, `data/raw/`, `data/curated/`, `data/results/`, `tests/unit/`, `tests/contract/`, `contracts/`, `docs/`, `paper/`.
 - **Verification**: Verify all directories exist.
 - **Output**: Directory structure.
 - **Dependency**: None.
 - **Traceability**: Implements Plan Project Structure.

- [ ] T001b [P] **Configure Linting and Formatting**.
 - **Action**: Create `code/pyproject.toml` with ruff/flake8 configuration and black configuration. **Do NOT create separate .ruff.toml or .black.toml files**.
 - **Verification**: Run `ruff check code/` and `black --check code/` and ensure no errors.
 - **Output**: `code/pyproject.toml`.
 - **Dependency**: T001a.
 - **Traceability**: Implements Plan Linting Configuration.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 [P] [P] Implement `code/config.py` to define paths (`data/raw/`, `data/curated/`, `data/results/`), random seeds, model config (CPU-only, -bit quantization default), AND critical thresholds: `COMPLEXITY_THRESHOLD` (default 50), `HARD_INSTANCE_PERCENTILE` (default 0.20), `MIN_SYNTHETIC_ISSUES` (default 10), `VALIDATION_SAMPLE_SIZE` (default 5), `COVERAGE_COLUMN_NAME` (default 'initial_coverage'), `SWEEP_SAMPLE_SIZE` (default a representative sample size), `SWEEP_SEED` (The specific value to remove/generalize: a predetermined default setting), `TURN_LIMITS` (default [1, 2, 3, 4]). **Note**: `TIE_THRESHOLD` is REMOVED; statistical routing is now deterministic based on tie presence.
- [ ] T003 [P] [P] Implement `code/utils/hash_artifacts.py` for automated SHA256 hashing of `data/` artifacts (Constitution Principle V). **Verification**: Run the script against a dummy file and verify SHA256 hash is generated and recorded in `state/`.
- [ ] T004 [P] [P] Create `contracts/` directory with `dataset_schema.yaml`, `agent_log_schema.yaml`, `result_schema.yaml`
- [ ] T005 [P] [P] Implement `code/utils/validation.py` for JSONL/Parquet schema validation against contracts
- [ ] T006 [P] [P] Setup `pytest` configuration and `tests/contract/test_schemas.py` skeleton
- [ ] T043 [P] **CPU-Quantized Model Execution Setup**.
 - **Requirement**: Create `code/agent/quantized_llm.py` to use `llama-cpp-python` with 8-bit quantization as the **PRIMARY AND ONLY** strategy to ensure compliance with SC-005 (GB RAM constraint) on free-tier runners.
 - **Logic**:
 1. **Mandatory 8-bit**: Always load the model in 8-bit quantization. This is a safety guarantee for the constrained environment.
 2. **Explicit CPU**: Use `n_gpu_layers=0` and optimized `n_ctx` for CPU inference.
 3. **Memory Check**: Add a runtime check to fail if memory usage exceeds a predefined threshold.
 - **Constraint**: **No float32 path**. Attempting to load float32 on a 7GB RAM runner risks OOM before fallback. 8-bit is the only safe path.
 - **Traceability**: Implements FR-014 and SC-005, ensuring executability on the target runner.
 - **Dependency**: Must be completed before T022 and T023.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Curation and Hard Instance Selection (Priority: P1) 🎯 MVP

**Goal**: Download SWE-Explore, derive ground truth, select "hard" instances based on **initial coverage scores** (Spec FR-001) to ensure alignment with the benchmark's definition of "hard" (low retrieval success), and generate a set of synthetic ambiguous issues.

**Independent Test**: Verify the existence of `data/curated/hard_subset.jsonl`, `data/curated/non_hard_subset.jsonl`, `data/curated/synthetic_issues.jsonl`, and `data/curated/validation_report.md` with correct schemas and valid AST parsing for synthetic issues.

### Test Definition for User Story 1 (MUST BE WRITTEN FIRST) ⚠️

> **NOTE**: These tasks define the tests. They must be written *before* implementation tasks but executed *after* implementation.

- [ ] T007 [P] [US1] Contract test for dataset schema in `tests/contract/test_dataset_schema.py` (Depends on T004 schema output)
- [ ] T008 [P] [US1] Unit test for mutation logic (variable rename, comment removal) in `tests/unit/test_mutation.py`
- [ ] T009 [P] [US1] Unit test for synthetic issue validity (AST parse check) in `tests/unit/test_synthetic_validity.py`

### Implementation for User Story 1

- [ ] T010 [P] [US1] **Implement Robust Data Fetcher**.
 - **Requirement**: Implement `code/data/download.py` to fetch `bench.final.public.jsonl` from HuggingFace.
 - **Constraint**: **Fail Loudly**: If the HuggingFace `load_dataset` call fails (timeout, 404, 500), the script MUST raise a `ConnectionError` or `ValueError` with a clear message. **NO** synthetic fallback logic (`try/except` with `generate_synthetic_*`) is permitted.
 - **Streaming**: Use `datasets.load_dataset(..., streaming=True)` to process in chunks, preventing OOM on constrained runners (FR-013).
 - **Output**: `data/raw/swe_explore_raw.jsonl`.
 - **Traceability**: Implements Spec FR-001 and addresses "Fail Loudly" rule.
- [ ] T011 [P] [US1] **Implement Ground Truth Derivation with Streaming**.
 - **Requirement**: Implement `code/data/derive_gt.py` to parse solution patches and generate `ground_truth_lines` lists.
 - **Constraint**: Use `datasets.load_dataset(..., streaming=True)` to iterate through the raw dataset in chunks, deriving GT lines for each issue and writing to a temporary file or accumulating online, ensuring peak memory < 7GB.
 - **Output**: `data/raw/swe_explore_with_gt.jsonl`.
 - **Traceability**: Implements Spec FR-008 and addresses "Stream Large Datasets" rule.
- [ ] T012 [US1] **Filter Hard Subset (Spec Alignment)**.
 - **Requirement**: Implement filtering based on **initial coverage scores** as per **Spec FR-001** to identify "hard" instances (bottom `HARD_INSTANCE_PERCENTILE` of scores).
 - **Input**: `data/raw/swe_explore_with_gt.jsonl` (T011 output).
 - **Logic**: Select the bottom `HARD_INSTANCE_PERCENTILE` (from `config.py`, default 0.20) of `config.COVERAGE_COLUMN_NAME` scores. **Handle Missing Data**: If the coverage score is missing or null, skip the issue and log a warning. Do not impute.
 - **Plan Override Rationale**: This task implements the methodology defined in Spec FR-001, overriding the Plan's previous "Cyclomatic Complexity" mandate. This override is ratified by the Spec. **Do NOT depend on T000-Notice for logic**; the Spec is the source of truth.
 - **Diagnostic**: Calculate Cyclomatic Complexity for each issue and append as `metadata.complexity_score` to `hard_subset.jsonl` (does NOT affect selection).
 - **Deliverable**: Create `code/data/filter_hard.py` to perform this calculation and selection.
 - **Output**: `data/curated/hard_subset.jsonl`.
 - **Dependency**: **Must verify `code/config.py` (T002) exists and T011 is complete.** T002 and T011 must complete first.
 - **Traceability**: Implements Spec FR-001.
- [ ] T012c [US1] **Generate Non-Hard Subset**.
 - **Requirement**: Compute the complement of the Primary Hard Subset (T012) to provide the input pool for synthetic generation.
 - **Logic**: Select all issues from the **full dataset** (`data/raw/swe_explore_with_gt.jsonl`) that are NOT in `data/curated/hard_subset.jsonl`. **Note**: Issues skipped in T012 due to missing data are included in the Non-Hard set if they are not in the Hard set, ensuring the pool is the true complement of the *selected* Hard set.
 - **Validation**: **Explicitly validate** that `data/curated/hard_subset.jsonl` exists and is not empty before proceeding. If missing or empty, fail loudly with a clear error message.
 - **Implementation**: Create `code/data/filter_non_hard.py`. Read `data/raw/swe_explore_with_gt.jsonl` and `data/curated/hard_subset.jsonl`. Write to `data/curated/non_hard_subset.jsonl`.
 - **Output**: `data/curated/non_hard_subset.jsonl`.
 - **Dependency**: **Blocking dependency** on T012 completion.
 - **Traceability**: Resolves ordering-064eff0b by providing the correct input for T013.
- [ ] T013 [US1] **Generate Synthetic Ambiguous Issues**.
 - **Input**: `data/curated/non_hard_subset.jsonl` (T012c output).
 - **Logic**: Apply mutations to generate a set of issues.
 - **Mutation Strategies**:
 1. **Variable Rename**: Rename all local variables using a deterministic hash-based mapping.
 2. **Comment Removal**: Strip all comments (single-line and multi-line).
 3. **Structural Obfuscation**: Use `libcst` to reorder independent `if`/`else` blocks by sorting them by starting line number and reversing their order, and rename function arguments (API signature changes).
 - **Constraint**: **Dynamic Generation**: Generate ALL valid mutations from the input pool. **DO NOT** use a fixed cap (e.g., 50).
 - **Hard Fail Logic**: If the total count of valid mutations is 0, the script MUST fail loudly with a `ValueError`. If the count is > 0 but < `MIN_SYNTHETIC_ISSUES` (default 10), log a `CRITICAL` warning with the exact count and **proceed** with the available set. **Note**: Spec FR-002 does not define a minimum; this 10-count is a derived constraint for statistical validity.
 - **Safety**: If the pool is smaller than `MIN_SYNTHETIC_ISSUES`, generate all possible valid mutations.
 - **Output**: `data/curated/synthetic_issues.jsonl`.
 - **Oracle**: Derive `ground_truth_lines` from the original unmutated code (FR-008).
 - **Validity**: Ensure mutated code is syntactically valid (AST parseable). Skip invalid mutations and log warnings.
 - **Deliverable**: Create `code/data/mutate.py` to implement this logic.
 - **Dependency**: T012c.
 - **Traceability**: Aligns with Spec FR-002 and addresses runtime constraint SC-005.
- [ ] T014 [US1] **Metadata & Versioning**.
 - Save `data/curated/synthetic_issues_meta.json` containing original code hashes, mutation parameters, and the exact count generated.
 - Run `hash_artifacts.py` on `data/curated/` files.
- [ ] T015 [P] [US1] **Generate Validation Report**.
 - **Action**: Select `VALIDATION_SAMPLE_SIZE` (from config.py T002) random issues from `data/curated/hard_subset.jsonl`.
 - **Output**: Markdown table with columns [IssueID, CoverageScore, ComplexityScore, Notes].
 - **Note**: This report is a **tool for manual inspection**, generated in parallel. It does **NOT** gate the pipeline. T016-AutoValidate will proceed independently.
 - **Dependency**: T012 completion.
- [ ] T016-AutoValidate [US1] **Automated Validation Gate**.
 - **Action**: Run `code/data/validate_hard.py` to automatically verify the "hard" subset against the coverage threshold and generate a validation report.
 - **Logic**: The script checks if the selected "hard" issues (by Coverage) exhibit low coverage (as a sanity check) and **includes a "Plan Override Justification" block** documenting the decision to use Coverage over Complexity to align with Spec FR-001.
 - **Gate Logic**: The pipeline **MUST PROCEED** after this task. The automated script generates the report and **does NOT wait** for human intervention. The report is saved for human review in the UI, but the CI/CD pipeline continues.
 - **Output**: `data/curated/validation_report.md` and `data/curated/validation_status.json`.
 - **Schema**: `validation_status.json` MUST contain keys: `status` (string: "PASSED" or "WARNING"), `message` (string), `sample_size` (int).
 - **Dependency**: T012 completion. **Does NOT depend on T015**.
 - **Traceability**: Replaces manual gate T016b to ensure reproducibility (Constitution Principle I) and documents Spec Alignment.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Iterative Agent Execution Loop (Priority: P2)

**Goal**: Implement a CPU-tractable iterative agent loop with a bounded number of turns, static analysis feedback, and a Static Multi-Query Baseline. Ensure both produce compatible schemas for pairing.

**Independent Test**: Run a single "hard" issue through the iterative loop and verify a limited number of turns, reformulated queries containing error messages, and correct logging of `query_history` and `error_signals`.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T017 [P] [US2] Contract test for agent log schema in `tests/contract/test_agent_log_schema.py`
- [ ] T018 [P] [US2] Integration test for agent loop termination (3-turn limit, loop detection) in `tests/integration/test_agent_loop.py`

### Implementation for User Story 2

- [ ] T019 [P] [US2] Implement `code/agent/static_analysis.py` wrapper for `pylint`/`ast` to detect "missing import", "undefined variable", parse errors
- [ ] T020 [P] [US2] Implement `code/agent/prompts.py` with templates for query reformulation based on static analysis signals
- [ ] T021 [US2] **Data Locking & Subset Consistency**.
 - **Action**: Before running agents, copy `data/curated/hard_subset.jsonl` to a locked execution directory (e.g., `data/results/locked_hard_subset.jsonl`) and acquire a file lock to prevent concurrent writes.
 - **Purpose**: Ensure T022 (Baseline) and T023 (Iterative) consume the **exact same** file instance to enable 1:1 pairing.
 - **Dependency**: Depends on T012 (data generation), T012c (non-hard), and T016-AutoValidate (Automated Validation). **Not parallel**: Must wait for T016-AutoValidate. The copy operation is parallel-safe, but the lock acquisition must precede T022/T023.
 - **Prerequisite**: Phase 4 agents depend on this task.
- [ ] T022 [P] [US2] **Static Multi-Query Baseline**.
 - **Requirement**: Run **parallel queries** per issue (matching the iterative limit of 3 turns defined in Spec FR-003) to ensure a fair comparison of feedback mechanisms vs. search volume.
 - **Input**: `data/results/locked_hard_subset.jsonl` (T021).
 - **Deliverable**: Create `code/agent/static_baseline.py` to perform this execution.
 - **Output**: `data/results/baseline_logs.jsonl` (Unique path to avoid race conditions).
 - **Logging**: Explicitly log `issue_id`, `query_count`, `retrieved_context_ids`, and `coverage_score`.
 - **Dependency**: Depends on T021 completion and T043 (Quantized Model).
- [ ] T023 [P] [US2] **Iterative Agent**.
 - **Requirement**: Enforce a configurable turn limit with a defined default.
 - **Turn Logic**: Query -> Retrieve -> Static Analysis -> Reformulate (if error).
 - **Loop Detection**: Implement `detect_loop` to break infinite loops if reformulated query matches a previous turn's query string within a limited conversation history window.
 - **Input**: `data/results/locked_hard_subset.jsonl` (T021).
 - **Output**: `data/results/iterative_logs.jsonl` (Unique path to avoid race conditions).
 - **Logging**: Explicitly log `issue_id`, `query_history`, `static_analysis_signals`, `turn_reasons`.
 - **Dependency**: Depends on T021 completion and T043 (Quantized Model).
- [ ] T024b [US2] **Turn-Limit Sweep**.
 - **Logic**:
 1. **Sampling**: Generate a specific sample list file for **N=`config.SWEEP_SAMPLE_SIZE`** issues (random sample with **seed `config.SWEEP_SEED`**, stratified by `complexity_score` quartiles from `data/curated/hard_subset.jsonl`). Output: `data/results/sweep_sample_list.json`.
 2. **Execution**: Execute the iterative agent loop for each turn limit in the range **[1, 2, 3, 4]**. Pass `max_turns` dynamically to the agent execution script. Output: `data/results/sweep_execution_logs.json` (aggregated logs for all turn limits).
 3. **Aggregation**: Aggregate results into `data/results/sweep_results.json` containing columns: `issue_id`, `turns_used`, `coverage`, `stability_flag` for each turn limit.
 - **Dependency**: Depends on T012 (stratification) and T043 (Quantized Model).
 - **Traceability**: Implements SC-006 (threshold sensitivity).
- [ ] T025 [US2] **Hash Artifacts**.
 - Integrate `hash_artifacts.py` to hash `data/results/agent_logs/`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Comparative Metric Calculation and Statistical Testing (Priority: P3)

**Goal**: Compute line-level coverage and ranking efficiency, apply **Wilcoxon signed-rank test** as the primary success criterion (Spec SC-003), with **Exact Permutation Test** as the fallback for ties/censored data.

**Independent Test**: Provide pre-computed metrics for a small set and verify the statistical test returns a p-value and correct conclusion (significant vs. non-significant) at p < 0.05 threshold.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Contract test for result schema in `tests/contract/test_result_schema.py`
- [ ] T027 [P] [US3] Unit test for statistical tests in `tests/unit/test_stats.py`. **Includes**: Wilcoxon signed-rank test implementation AND **censored data handling logic (N penalty assignment) for Permutation Test validation**. This task explicitly validates the logic required for T030-Permutation, ensuring that censored entries are handled correctly before the main analysis runs.

### Implementation for User Story 3

- [ ] T028 [P] [US3] Implement `code/metrics/coverage.py` to calculate % of `ground_truth_lines` retrieved
- [ ] T029 [P] [US3] Implement `code/metrics/ranking.py` to calculate position of first relevant line (handle censored data with penalty N+1)
- [ ] T030-Prep [US3] **Censoring Check & Routing**.
 - **Requirement**: Analyze `data/results/baseline_logs.jsonl` and `data/results/iterative_logs.jsonl` to determine if "Ranking Efficiency" data contains censored values.
 - **Logic**: Check for `coverage_score == 0.0` or `retrieved_lines == []` to identify censored data.
 - **Tie Definition**: Calculate "ties" as ties in the **absolute difference scores** of the paired data. Include censored pairs (N+1 penalty) in this calculation.
 - **Routing**:
 - If **any ties are detected (count > 0)** OR censored data exists: Route to T030-Permutation.
 - Otherwise: Route to T030-Primary (Wilcoxon).
 - **Output**: `data/results/statistical_routing.json` (flag: "PERMUTATION" or "WILCOXON").
 - **Execution Logic**: The runner script must read this file and **execute ONLY the routed task**, skipping the other. This enforces mutual exclusivity.
 - **Dependency**: Depends on T022, T023.
 - **Traceability**: Implements Spec FR-006 with a deterministic "ties > 0" threshold, removing hidden configuration.
- [ ] T030-Primary [P] [US3] **Coverage & Ranking Analysis (Wilcoxon - Spec Primary)**.
 - **Requirement**: Implement **Wilcoxon signed-rank test** as per **Spec FR-006** and **SC-003** as the PRIMARY success criterion.
 - **Method**: Apply Wilcoxon signed-rank test to paired coverage data and paired ranking data (with continuity correction for ties).
 - **Output**: P-values and effect sizes for both metrics.
 - **Traceability**: Implements Spec FR-006/SC-003 as the primary path.
 - **Dependency**: Depends on T030-Prep routing to "WILCOXON".
- [ ] T030-Permutation [US3] **Exact Permutation Test for Ties/Censoring**.
 - **Requirement**: Implement **Exact Permutation Test** as per **Spec FR-006** if ties >= 0 (i.e., any ties present) or censored data is present.
 - **Method**: Apply exact permutation test to paired data to handle dominant ties and censored entries (using N+1 penalty).
 - **Output**: P-values and effect sizes.
 - **Traceability**: Implements Spec FR-006 (ties/censoring handling).
 - **Dependency**: Depends on T030-Prep routing to "PERMUTATION".
- [ ] T030c [US3] **Multiplicity Correction & Framing**.
 - **Correction**: Apply **Bonferroni correction** to the family of tests: **Coverage**, **Ranking (Wilcoxon/Permutation)**.
 - **Framing**: Frame all results as **"associational differences"** per FR-007.
 - **Output**: `data/results/final_metrics.json`.
 - **Dependency**: Depends on T030-Primary or T030-Permutation.
- [ ] T031 [US3] Implement `code/analysis/plots.py` for visualization of coverage and permutation curves
- [ ] T032 [US3] **Integrate hash_artifacts.py**.
 - **Action**: Update `code/main.py` to call `hash_artifacts.py` on `data/results/final_metrics.json` after T030c completes.
 - **Output**: `data/results/final_metrics.json` with hash recorded in `state/`.
 - **Dependency**: Depends on T030c completion.
- [ ] T033-Zero [US3] **Create Report Template**.
 - **Action**: Create `code/analysis/report_template.j2` with sections: Abstract, Methods, Results, Discussion.
 - **Logic**: Define sections: Abstract, Methods, Results, Discussion.
 - **Variables**: The template MUST support the following Jinja2 variables: `p_value`, `effect_size`, `coverage_diff`, `ranking_diff`, `n_issues`, `methodology`, `conclusion`.
 - **Constraint**: Ensure all placeholders are mapped to fields in `data/results/final_metrics.json`.
 - **Output**: `code/analysis/report_template.j2`.
 - **Dependency**: Must exist before T033b.
- [ ] T033b [US3] **Generate Report Draft**.
 - **Logic**:
 1. Extract p-values, effect sizes, and metrics from `data/results/final_metrics.json` (T030c).
 2. Map extracted data to Jinja2 template variables.
 3. Load the template (T033-Zero) and render the populated sections into `data/results/report_draft.md`.
 4. Enforce "associational differences" language in Results/Discussion.
 - **Output**: `data/results/report_draft.md`.
 - **Dependency**: Depends on T030c and T033-Zero.
- [ ] T033d [US3] **Validate Report Language (Regex)**.
 - **Requirement**: Implement a deterministic validator to ensure `data/results/report_draft.md` does not contain causal language.
 - **Logic**: Run a regex scan `r'\b(proves|causes|guarantees|demonstrates causality)\b'` against the draft. Fail the build if any match is found.
 - **Output**: `data/results/report_validation_report.json` (status: "PASSED" or "FAILED").
 - **Dependency**: Depends on T033b.
 - **Traceability**: Implements FR-007 (Causal Language Validation).
- [ ] T033c [US3] **Report Generation: Final Assembly & Validation**.
 - Logic: Assemble `paper/draft.md` and validate against schema using `report_draft.md` and T033d results.
 - **Output**: `paper/draft.md` and `data/results/report_validation_report.json`.
 - **Dependency**: Depends on T033b and T033d.
- [ ] T034 [US3] **Generate Results Summary**.
 - **Action**: Execute T033b -> T033d -> T033c pipeline.
 - **Output**: `paper/results_summary.md` (containing Abstract draft, Methods summary, Results, Discussion).
 - **Constraint**: Scope limited to spec requirements (SC-004, FR-007); no full manuscript generation.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 [P] Update `docs/quickstart.md` with execution instructions and data flow diagrams. **Includes**: Quickstart validation steps.
- [ ] T036 Refactor `code/agent/iterative.py` to reduce cyclomatic complexity.
- [ ] T037 Optimize memory usage in `code/metrics/coverage.py` by processing lines in chunks.
- [ ] T038 [P] Add unit tests for `code/analysis/stats.py` (Wilcoxon and Permutation Test logic).
- [ ] T039 [US2/US3] Implement runtime monitor in `code/main.py` to track total execution time. **Logic**: If elapsed time > 5.5 hours (SC-005), abort remaining non-critical sweeps or reduce sample size to ensure completion within 6 hours.
- [ ] T046-StatsValidation [US3] **Verify Bonferroni Correction**.
 - **Requirement**: Implement `tests/contract/test_result_schema.py::test_bonferroni_adjusted_pvalue` to validate that the `final_metrics.json` explicitly includes the adjusted p-value and the correction factor used.
 - **Traceability**: Implements SC-004.
- [ ] T046-FramingValidation [US3] **Verify Causal Language Framing**.
 - **Requirement**: Implement `tests/contract/test_report_validation.py::test_causal_language` to validate that the final report avoids causal claims (FR-007).
 - **Traceability**: Implements FR-007.

---

## Phase N+1: Revision & Stability (Addressing Review Concerns)

**Purpose**: Address specific reviewer concerns regarding data integrity, execution robustness, and statistical validity.

- [ ] T047 [US2] **Implement Deterministic Loop Detection & Early Exit**.
 - **Requirement**: Enhance `code/agent/iterative.py` to detect when the agent enters a query loop (repeating the same query or a semantically identical query) before hitting a predefined turn limit.
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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for data (specifically `hard_subset.jsonl` and `validation_status.json` with automated validation)
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
Task: "Implement code/agent/quantized_llm.py" (T043)

# Note: T023 (Iterative Agent) depends on T043.
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
- **CPU Feasibility**: Ensure all model tasks use 8-bit quantization on constrained runners to guarantee execution. **No CUDA/GPU**.
- **Constraint Preservation**: All tasks must strictly implement the metrics and counts defined in FR-001, FR-002, SC-004, and FR-007.
 - **Hard Instance Selection**: Must use **initial coverage scores** (Spec FR-001) as the primary path (T012) to align with the benchmark definition. Complexity is diagnostic (T012-Complexity).
 - **Synthetic Issues**: Must generate all valid mutations with a hard fail if 0, proceed with warning if < 10 (T013).
 - **Statistics**: Coverage and Ranking use Wilcoxon as primary (T030-Primary), Permutation Test (T030-Permutation) if **any ties are present** or censored data is present. **Survival Analysis is removed**.
 - **Correction**: Bonferroni applied to Coverage, Ranking tests.
- **Data Integrity**: All analysis tasks must consume REAL data from `data/curated/`. No synthetic/fake input data generation tasks are permitted.
- **Execution Order**: Tasks producing results (T023) MUST follow tasks generating those results (T021, T022). Tasks verifying results (T030) MUST follow result generation.
- **Automated Validation**: Phase 4 cannot start until T016-AutoValidate completes successfully.
- **New Functional Requirements (FR-011 to FR-016)**: Removed. All valid requirements (streaming, quantization, robustness) are now integrated into primary tasks (T010, T011, T043) referencing existing FR-001/002/014.
- **Revision Concerns**: Phase N+1 added to address specific reviewer concerns regarding loop detection, mutation fallback, permutation test sensitivity, and static analysis robustness.
- **Plan Alignment**: T000-Notice is a standalone administrative task for human alignment. It **updates the Plan** to remove contradictions, ensuring the Plan is no longer flawed during execution. T012 implements the Spec logic directly.