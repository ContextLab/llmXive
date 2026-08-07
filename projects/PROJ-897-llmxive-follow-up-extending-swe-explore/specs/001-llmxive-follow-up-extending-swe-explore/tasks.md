# Tasks: llmXive follow-up: extending "SWE-Explore: Benchmarking How Coding Agents Explore Repositories"

**Input**: Design documents from `/specs/001-iterative-exploration-benchmark/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 0: Administrative Alignment & Data Foundation

- [ ] T001a [P] **Create Project Structure**
 - Create directories: `code/`, `data/raw/`, `data/curated/`, `data/results/`, `tests/unit/`, `tests/integration/`, `tests/contract/`.
 - Create `specs/001-llmxive-follow-up-extending-swe-explore/contracts/`.
 - **Verification**: Run `test -d code/ && test -d data/raw/ &&...` for all directories. If any fail, create them immediately and log the creation.
 - Output: Directory structure created and verified.

- [ ] T001b [P] **Configure Linting and Formatting**
 - **Prerequisite**: Run `pip install ruff black`.
 - Create `code/pyproject.toml` containing ruff and black configuration (no separate config files).
 - Run `ruff check code/` and `black --check code/` to ensure no errors.

- [ ] T002 [P] **Config Constants (Placeholders)**
 - Implement `code/config.py` with paths, seeds, model config, and **placeholder** values for deferred parameters:
 ```python
 HARD_INSTANCE_PERCENTILE = None # [deferred] - set at runtime or via validation
 COVERAGE_COLUMN_NAME = 'initial_coverage'
 SWEEP_SAMPLE_SIZE = None # [deferred] - validated by Ta
 SWEEP_SEED = 42
 TURN_LIMITS = [low, medium, high]

The specific value to remove/generalize: 'low'

Rewritten passage:
 MIN_SYNTHETIC_ISSUES = 10
 VALIDATION_SAMPLE_SIZE = 5
 TIE_THRESHOLD = None # [deferred] - validated by Ta
 MAX_RUNTIME_HOURS = 6
 MODEL_PRECISION = '-bit'
 ```
 - Verify importability.

- [ ] T003a [P] **Create Hash Artifacts Utility Script**
 - Implement `code/utils/hash_artifacts.py` to compute SHA‑256 hashes for all files under `data/` and write a manifest to `state/`.
 - **Note**: This task only creates the script; it does not run it on empty data.

- [ ] T004 [P] **Create Contract Schemas**
 - Create `specs/001-llmxive-follow-up-extending-swe-explore/contracts/` with valid YAML schemas: `dataset_schema.yaml`, `agent_log_schema.yaml`, `result_schema.yaml`.
 - Ensure files are non-empty and syntactically valid YAML.
 - **Constraint**: Must match the structure defined in `data-model.md`.
 - **Validation**: Run a syntax check on all YAML files as part of this task (merged from T004-Validate).

- [ ] T005 [P] **Schema Validation Helper**
 - Implement `code/utils/validation.py` to validate JSONL/Parquet files against the schemas in `specs/.../contracts/`.

- [ ] T006 [P] **Pytest Configuration & Contract Test Skeleton**
 - Add `pytest.ini` and create `tests/contract/test_schemas.py` skeleton that will later import `validation.py`.

- [ ] T043 [P] **Quantized Model Orchestration**
 - Create `code/agent/quantized_llm.py` with a function that loads the chosen model (e.g., `Qwen-1.5B`) using `transformers` with `bitsandbytes`.
 - **Strategy**: Load in -bit precision (`load_in_8bit=True`) on `device='cpu'` as defined in `config.py`.
 - **Memory Check**: Use `psutil` to check process memory; if > 6 GB, raise `MemoryError` with a clear message.
 - **Constraint**: No dynamic fallback to different precision; precision is fixed to ensure reproducibility.
 - Add a runtime check that aborts with a clear `MemoryError` if process memory exceeds 6 GB.
 - This task must complete before any agent execution (T022, T023).

## Phase 1: Data Curation (User Story 1)

### Tests (must be written first)

- [X] T007 [P] **Contract test for dataset schema** (`tests/contract/test_dataset_schema.py`) – depends on T004. <!-- FAILED: unspecified -->

- [X] T008 [P] **Unit test for mutation logic** (`tests/unit/test_mutation.py`). <!-- FAILED: unspecified -->

- [X] T009 [P] **Unit test for synthetic issue validity** (`tests/unit/test_synthetic_validity.py`).

### Implementation

- [ ] T010 [P] **Implement Robust Data Fetcher**
 - `code/data/download.py` uses `datasets.load_dataset(..., streaming=True)` to fetch `bench.final.public.jsonl` from HuggingFace.
 - On any failure, raise `ConnectionError` with a clear message. No synthetic fallback.

- [ ] T011 [P] **Implement Ground Truth Derivation with Streaming**
 - `code/data/derive_gt.py` parses solution patches, emits `ground_truth_lines`, writes to `data/raw/swe_explore_with_gt.jsonl`.
 - Uses streaming to stay <7 GB RAM.

- [ ] T011b [P] **Implement AST-Based Coverage Simulation (Fallback)**
 - **Trigger**: Only if `COVERAGE_COLUMN_NAME` is missing from the dataset.
 - `code/data/simulate_coverage.py` implements a local AST-based retrieval simulation to compute a proxy coverage score for each issue.
 - Writes proxy scores to `data/raw/swe_explore_with_coverage.jsonl`.
 - **Dependency**: T011.

- [ ] T012 [US1] **Filter Hard Subset (Spec Alignment)**
 - `code/data/filter_hard.py` reads `data/raw/swe_explore_with_gt.jsonl` (or `swe_explore_with_coverage.jsonl` if T011b ran), selects bottom `HARD_INSTANCE_PERCENTILE` of `COVERAGE_COLUMN_NAME` (per Spec FR-001).
 - Calculates cyclomatic complexity as supplementary metadata (does not affect selection).
 - Writes `data/curated/hard_subset.jsonl`.

- [ ] T013 [US1] **Generate Synthetic Ambiguous Issues**
 - **Input**: `data/curated/hard_subset.jsonl` (T012) to identify excluded IDs, and `data/raw/swe_explore_with_gt.jsonl` (T011) as the source pool.
 - **Dependencies**: `libcst` must be installed.
 - Logic:
 1. Filter the raw dataset (`data/raw/swe_explore_with_gt.jsonl`) to exclude issues present in `hard_subset.jsonl` (T012) based on unique issue IDs to form the candidate pool for synthetic generation.
 2. If input pool size < `config.MIN_SYNTHETIC_ISSUES`, generate **all** possible valid mutations, log a `WARNING`, and proceed.
 3. Apply **variable renaming**, **comment removal**, and **structural obfuscations** (specifically: control flow reordering and API signature changes) via `libcst`.
 4. Validate each mutated file with `ast.parse`; **skip invalid ones with a warning** (do not crash the script).
 5. If **total valid mutations == 0**, raise `FatalError('No valid synthetic issues generated. Pipeline halted.')` to break the study design.
 6. If **0 < valid mutations < MIN_SYNTHETIC_ISSUES**, log a `WARNING` with the count and continue.
 - Store `ground_truth_lines` from the original unmutated code (FR‑008).
 - Output: `data/curated/synthetic_issues.jsonl`.
 - **Dependency**: T012, T011.

- [~] T014 [P] **Metadata & Versioning**
 - Write `data/curated/synthetic_issues_meta.json` with hashes, mutation parameters, and counts.
 - Run `hash_artifacts.py` (T003a) on the curated folder.

- [ ] T015 [US1] **Manual Validation & Evidence Generation (Human Protocol)**
 - Randomly sample `VALIDATION_SAMPLE_SIZE` issues from `hard_subset.jsonl`.
 - **Human Validation Protocol**:
 1. Generate a structured report `data/curated/validation_report_template.md` containing:
 - A markdown table of sampled issues.
 - Specific code snippets showing the ambiguity.
 - A placeholder for human verification (e.g., `[ ] Ambiguity Confirmed`).
 2. **Output**: The report must be manually reviewed by a human. The final output `data/curated/validation_evidence.md` must include a `human_verified: true` flag and a timestamp.
 3. **Constraint**: An automated script cannot set `human_verified: true`; this requires a manual step in the pipeline.
 - **Dependency**: T012.

- [ ] T016-ValidateHardSubset [US1] **Automated Validation Gate**
 - Run `code/data/validate_hard.py` to confirm low coverage of the hard subset.
 - Output: `data/results/validation_status.json` (`PASSED` or `WARNING`). Pipeline proceeds regardless of status.

## Phase 2: Foundational (Blocking Prerequisites)

- [ ] T003b [P] **Run Hash Utility on Curated Data**
 - Execute `hash_artifacts.py` (T003a) on `data/curated/` after T014.
 - **Dependency**: T014.

## Phase 3: Iterative Agent Execution Loop (User Story 2)

### Tests

- [ ] T017 [P] **Contract test for agent log schema** (`tests/contract/test_agent_log_schema.py`).

- [ ] T018 [P] **Integration test for agent loop termination** (`tests/integration/test_agent_loop.py`).

### Implementation

- [ ] T019 [P] **Static Analysis Wrapper**
 - Implement `code/agent/static_analysis.py` to run `pylint` and `ast` checks, returning error messages or a `neutral_anomaly` flag on unexpected failures (see T050).

- [ ] T020 [P] **Prompt Templates**
 - Create `code/agent/prompts.py` with Jinja2 templates for query reformulation that embed detected error messages.

- [ ] T021 [P] **Data Locking & Subset Consistency**
 - Copy `data/curated/hard_subset.jsonl` to `data/results/locked_hard_subset.jsonl` under a file lock.
 - Depends on **T012** and **T016-ValidateHardSubset** (hard subset must be validated).

- [ ] T047 [P] **Implement Loop Detection Logic**
 - **CRITICAL**: Must be implemented BEFORE T023 runs to prevent infinite loops.
 - Create the core loop detection logic in `code/agent/iterative.py` that compares the current query against the previous two; if identical, sets `termination_reason: "loop_detected"`.
 - **Dependency**: T022 (Static Baseline must be ready to define baseline behavior).
 - **Note**: This task is NOT parallel-safe with T023.

- [ ] T022 [P] **Static Multi‑Query Baseline**
 - Uses the same total query budget as the iterative agent (a limited, fixed number of queries).
 - Input: `locked_hard_subset.jsonl`.
 - Output: `data/results/baseline_logs.jsonl`.
 - Depends on **T021** and **T043** (quantized model).

- [ ] T023 [P] **Iterative Agent**
 - Implements the 3‑turn loop with query → retrieve → static analysis → reformulate.
 - **Loop detection** (T047) is incorporated here.
 - Input: `locked_hard_subset.jsonl`.
 - Output: `data/results/iterative_logs.jsonl`.
 - Depends on **T021**, **T043**, and **T047**.

- [ ] T024a [P] **Power Analysis for Sensitivity Sweep**
 - **Purpose**: Verify that `SWEEP_SAMPLE_SIZE` is statistically sufficient. to represent the `hard_subset` size.
 - `code/analysis/power_analysis.py` calculates the power of the sensitivity test given the subset size and expected effect size.
 - Output: `data/results/power_analysis_report.md`. If insufficient, log a `WARNING` but proceed (as per plan constraints).
 - **Dependency**: T012.

- [ ] T024b [P] **Turn‑Limit Sweep**
 - Sample `SWEEP_SAMPLE_SIZE` issues (seed `SWEEP_SEED`) stratified by complexity quartiles.
 - Run iterative agent for each turn limit in `TURN_LIMITS`.
 - Aggregate results to `data/results/sweep_results.json`.
 - Depends on **T024a** and **T043**.

- [ ] T025 [P] **Hash Agent Artifacts**
 - Run `hash_artifacts.py` (T003a) on `data/results/agent_logs/`.

- [ ] T050 [P] **Static Analysis Neutral Signal**
 - Update `code/agent/static_analysis.py` to catch exceptions; on failure, emit `static_analysis_signal: "neutral_anomaly"` and continue without crashing.

## Phase 4: Comparative Metric Calculation and Statistical Testing (User Story 3)

### Tests

- [ ] T026 [P] **Contract test for result schema** (`tests/contract/test_result_schema.py`).

- [ ] T027 [P] **Unit test for statistical tests** (`tests/unit/test_stats.py`) – includes Wilcoxon and tie-handling.

### Implementation

- [ ] T028 [P] **Coverage Metric** (`code/metrics/coverage.py`).

- [ ] T029 [P] **Ranking Metric** (`code/metrics/ranking.py`) – applies `N+1` penalty for censored cases.

- [ ] T030a [P] **Analyze Tie Distribution & Justify Threshold**
 - Reads `baseline_logs.jsonl` (from T022) and `iterative_logs.jsonl` (from T023).
 - Counts ties as paired absolute differences equal to zero.
 - Computes `tie_proportion = ties / total_pairs`.
 - Checks for censored entries (defined as `log['relevant_lines'] == 0`).
 - **Output**: `data/results/tie_analysis.json` containing:
 - `tie_proportion`: float.
 - `censored_count`: int.
 - `justification`: A string explaining why the threshold (e.g., 20%) is appropriate for this distribution, or if the data requires the permutation test.
 - **Dependency**: T022, T023.

- [ ] T030b [P] **Route Statistical Test**
 - Reads `data/results/tie_analysis.json` (from T030a).
 - **Logic**:
 - If `tie_proportion > config.TIE_THRESHOLD` OR any censored entries exist: write `statistical_routing.json` with `"PERMUTATION"`.
 - Else: write `"WILCOXON"`.
 - **Dependency**: T030a.

- [ ] T030-Wilcoxon [P] **Wilcoxon Signed‑Rank Test**
 - Executes **only** when routing flag is `"WILCOXON"`.
 - Applies continuity correction for ties as mandated by FR-006.
 - **Dependency**: T030b.
 - **Note**: This task is conditional; it should not run if the flag is PERMUTATION.

- [ ] T030-Permutation [P] **Exact Permutation Test**
 - Executes **only** when routing flag is `"PERMUTATION"`.
 - Used when ties exceed threshold or censored data is present (fallback).
 - **Dependency**: T030b.
 - **Note**: This task is conditional; it should not run if the flag is WILCOXON.

- [ ] T030-Bonferroni [P] **Multiplicity Correction & Framing**
 - Apply Bonferroni correction to both coverage and ranking p‑values (SC-004).
 - Ensure all result text uses "associational differences" phrasing (FR-007).
 - **Dependency**: T030-Wilcoxon OR T030-Permutation.

- [ ] T031 [P] **Visualization** (`code/analysis/plots.py`).

- [ ] T032 [P] **Hash Final Metrics** – update `code/main.py` to hash `final_metrics.json` after T030-Bonferroni.

- [ ] T033-GenerateReport [P] **Generate and Validate Report**
 - Create `code/analysis/report_template.j2` with placeholders matching keys in `contracts/result_schema.yaml`.
 - Render the template using data from `final_metrics.json`.
 - Validate the rendered report against `result_schema.yaml` and scan for prohibited causal language.
 - **Dependency**: T030-Bonferroni.
 - **Output**: `paper/draft_validated.md` (if pass) or error.

- [ ] T033-Summary [P] **Results Summary**
 - Assemble `paper/results_summary.md` from the validated draft.
 - **Dependency**: T033-GenerateReport.

- [ ] T039a [P] **Runtime Timer**
 - Insert timing logic in `code/main.py` to measure total pipeline runtime.
 - **Constraint**: If runtime exceeds `MAX_RUNTIME_HOURS`, the run **FAILS** (does not down-sample) to preserve reproducibility (Constitution Principle I).
 - **Dependency**: All previous tasks.

- [ ] T039b [P] **Feasibility Report**
 - Log the *total* pipeline runtime from T039a.
 - Compare against the maximum runtime threshold defined in `config.MAX_RUNTIME_HOURS`.
 - Write `data/results/feasibility_report.md` with `status: "PASS"` or `status: "FAIL"` and the exact runtime.
 - **Dependency**: T039a.

- [ ] T048 [P] **Robust Mutation Fallback**
 - Integrated into T013 logic (see T013 description).

- [ ] T049 [P] **Permutation Test Sensitivity Check**
 - Re‑run permutation test with penalty values N and higher increments; store variance in `data/results/sensitivity_analysis.json`.

## Phase N: Polish & Cross‑Cutting Concerns

- [ ] T035 [P] **Update Quickstart Documentation** (`docs/quickstart.md`) with execution instructions and data‑flow diagrams.

- [ ] T036 [P] **Refactor Iterative Agent** to reduce cyclomatic complexity.

- [ ] T037 [P] **Optimize Coverage Metric Memory Usage** – process lines in chunks.

- [ ] T038 [P] **Add Unit Tests for Stats Module** (`tests/unit/test_stats_logic.py`).

- [ ] T046-StatsValidation [P] **Bonferroni Correction Verification** – test that `final_metrics.json` includes adjusted p‑values.

- [ ] T046-FramingValidation [P] **Causal Language Validation** – ensure final report contains no prohibited phrasing.