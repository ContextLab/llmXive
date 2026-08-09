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
 - **Verification**: Run `test -d code/ && test -d data/raw/ && test -d data/curated/ && test -d data/results/ && test -d tests/unit/ && test -d tests/integration/ && test -d tests/contract/ && test -d specs/001-llmxive-follow-up-extending-swe-explore/contracts/`. If any fail, create them immediately and log the creation.
 - Output: Directory structure created and verified.

- [ ] T001b [P] **Configure Linting and Formatting**
 - **Prerequisite**: Run `pip install ruff black`.
 - Create `code/pyproject.toml` containing ruff and black configuration.
 - **Specific Config**: Set `line-length = 88` and `target-version = "py310"` for both tools to ensure deterministic generation.
 - Run `ruff check code/` and `black --check code/` to ensure no errors.

- [ ] T002 [P] **Config Constants (Placeholders)**
 - Implement `code/config.py` with paths, seeds, model config, and **placeholder** values for deferred parameters.
 - **Resolution Mechanism**: All `None` values MUST be resolved at runtime via CLI arguments (e.g., `argparse`) or environment variables. The module must handle `None` gracefully until these are provided.
 ```python
 HARD_INSTANCE_PERCENTILE = None # [deferred] - set at runtime or via CLI
 COVERAGE_COLUMN_NAME = 'initial_coverage'
 SWEEP_SAMPLE_SIZE = None # [deferred] - validated by T024a
 SWEEP_SEED = 42 [UNRESOLVED-CLAIM: c_bb21b2d6 — status=not_enough_info]
 TURN_LIMITS = [1, 2, 3]
 MIN_SYNTHETIC_ISSUES = None # [deferred]
 VALIDATION_SAMPLE_SIZE = None # [deferred]
 TIE_THRESHOLD = 0.50 [UNRESOLVED-CLAIM: c_ba0e5b2d — status=not_enough_info] # Concrete threshold for statistical routing (FR-006)
 MAX_RUNTIME_HOURS = 6 [UNRESOLVED-CLAIM: c_617d0afd — status=not_enough_info]
 MODEL_PRECISION = '8-bit'
 ```
 - Verify importability.

- [ ] T003a [P] **Create Hash Artifacts Utility Script**
 - Implement `code/utils/hash_artifacts.py` to compute SHA‑256 hashes for all files under `data/` and write a manifest to `state/`.
 - **Constitution Compliance**: The utility MUST record checksums in `state/` and enforce that derivations are written to new filenames (no in-place modification).
 - **Note**: This task only creates the script; it does not run it on empty data.

- [ ] T004 [P] **Create Contract Schemas**
 - Create `specs/001-llmxive-follow-up-extending-swe-explore/contracts/` with valid YAML schemas: `dataset_schema.yaml`, `agent_log_schema.yaml`, `result_schema.yaml`.
 - **Source of Truth**: Derive schema fields strictly from `data-model.md`. Copy the structure defined there.
 - Ensure files are non-empty and syntactically valid YAML.
 - **Validation**: Run a syntax check on all YAML files as part of this task (merged from T004-Validate).

- [ ] T005 [P] **Schema Validation Helper**
 - Implement `code/utils/validation.py` to validate JSONL/Parquet files against the schemas in `specs/.../contracts/`.
 - **Scope**: This utility ONLY validates file structure and schema compliance. It does NOT filter data, generate synthetic issues, implement agents, or compute metrics.
 - **Function**: `validate_file(file_path, schema_path) -> bool`.
 - **Dependency**: T004.

- [ ] T006 [P] **Pytest Configuration & Contract Test Skeleton**
 - Add `pytest.ini` and create `tests/contract/test_schemas.py` skeleton that will later import `validation.py`.

- [ ] T043 [P] **Quantized Model Orchestration**
 - Create `code/agent/quantized_llm.py` with a function that loads the chosen model (e.g., `Qwen-1.5B`) using `transformers` with `bitsandbytes`.
 - **Strategy**: Load in 8-bit precision (`load_in_8bit=True`) on `device='cpu'` as defined in `config.py`.
 - **Memory Check**: Use `psutil` to check process memory.
 - **Offload Logic**: If memory > 6 GB, DO NOT raise a hard error. [UNRESOLVED-CLAIM: c_316a63f7 — status=not_enough_info] Instead, write a `gpu_offload_request.json` flag to `data/results/` and exit gracefully. The execution stage will detect this flag and re-run on Kaggle GPU.
 - **Constraint**: No dynamic fallback to different precision within the task; the offload is handled by the execution environment.
 - This task must complete before any agent execution (T022a, T022b, T023).

## Phase 1: Data Curation (User Story 1)

### Tests (must be written first, but depend on implementation)

- [X] T007 [P] **Contract test for dataset schema** (`tests/contract/test_dataset_schema.py`) – depends on T004, T010, T011.
 - **Note**: This test validates the structure of the downloaded/curated dataset. It cannot run until data exists.
 - **Dependency**: T010, T011.

- [X] T008 [P] **Unit test for mutation logic** (`tests/unit/test_mutation.py`). <!-- ATOMIZE: requested -->
 - **Note**: This test validates the synthetic generation logic. It cannot run until T013 is implemented.
 - **Dependency**: T013.

- [X] T009 [P] **Unit test for synthetic issue validity** (`tests/unit/test_synthetic_validity.py`).
 - **Note**: This test validates the output of T013. It cannot run until T013 is implemented.
 - **Dependency**: T013.

### Implementation

- [ ] T010 [P] **Implement Robust Data Fetcher**
 - `code/data/download.py` uses `datasets.load_dataset(..., streaming=True)` to fetch `bench.final.public.jsonl` from HuggingFace.
 - On any failure, raise `ConnectionError` with a clear message. No synthetic fallback.
 - **Output**: `data/raw/swe_explore_raw.jsonl`.
 - **Dependency**: T001b, T002, T003a, T004, T005, T006.
 - **Note**: This task ONLY fetches raw data. It does not derive coverage scores.

- [ ] T011 [P] **Implement Ground Truth Derivation with Streaming**
 - `code/data/derive_gt.py` parses solution patches, emits `ground_truth_lines`, writes to `data/raw/swe_explore_with_gt.jsonl`.
 - Uses streaming to stay <7 GB RAM. [UNRESOLVED-CLAIM: c_95e8ccdc — status=not_enough_info]
 - **Dependency**: T010.

- [ ] T011b [P] **Implement AST-Based Coverage Simulation (Fallback)**
 - **Trigger**: Only if `COVERAGE_COLUMN_NAME` is missing from the dataset (T010/T011 output).
 - `code/data/simulate_coverage.py` implements a local AST-based retrieval simulation to compute a proxy coverage score for each issue.
 - Writes proxy scores to `data/raw/swe_explore_with_coverage.jsonl`.
 - **Dependency**: T010. (Does NOT depend on T011, as it is a fallback for missing data).

- [ ] T012 [US1] **Filter Hard Subset (Spec Alignment)**
 - `code/data/filter_hard.py` reads `data/raw/swe_explore_with_gt.jsonl` (or `swe_explore_with_coverage.jsonl` if T011b ran), selects bottom `HARD_INSTANCE_PERCENTILE` of `COVERAGE_COLUMN_NAME` (per Spec FR-001).
 - Calculates cyclomatic complexity as supplementary metadata (does not affect selection).
 - Writes `data/curated/hard_subset.jsonl`.
 - **Dependency**: T011 OR T011b (whichever provides the coverage metric), T001b, T002, T003a, T004, T005, T006.

- [ ] T013 [US1] **Generate Synthetic Ambiguous Issues**
 - **Input**: `data/curated/hard_subset.jsonl` (T012) to identify excluded IDs, and `data/raw/swe_explore_with_gt.jsonl` (T011) as the source pool.
 - **Dependencies**: `libcst` must be installed.
 - Logic:
 1. Filter the raw dataset (`data/raw/swe_explore_with_gt.jsonl`) to form the **candidate pool**: Include only issues that are **NOT** in `hard_subset.jsonl` (T012) AND have valid ground truth (solvable tasks).
 2. If input pool size < `config.MIN_SYNTHETIC_ISSUES`, generate **all** possible valid mutations, log a `WARNING`, and proceed.
 3. Apply **variable renaming**, **comment removal**, and **structural obfuscations** (specifically: control flow reordering and API signature changes) via `libcst`.
 4. Validate each mutated file with `ast.parse`; **skip invalid ones with a warning** (do not crash the script).
 5. If **total valid mutations == 0**, raise `FatalError('No valid synthetic issues generated. Pipeline halted.')` to break the study design.
 6. If **0 < valid mutations < MIN_SYNTHETIC_ISSUES**, log a `WARNING` with the count and continue.
 - Store `ground_truth_lines` from the original unmutated code (FR‑008).
 - Output: `data/curated/synthetic_issues.jsonl`.
 - **Dependency**: T012, T011, T001b, T002, T003a, T004, T005, T006.

- [ ] T014 [P] **Metadata & Versioning**
 - Write `data/curated/synthetic_issues_meta.json` with hashes, mutation parameters, and counts.
 - Run `hash_artifacts.py` (T003a) on the curated folder.

- [ ] T015 [US1] **Automated Validation & Reporting**
 - Randomly sample `VALIDATION_SAMPLE_SIZE` issues from `hard_subset.jsonl`.
 - **Automated Protocol**:
 1. Generate a structured report `data/curated/validation_report.md` containing:
 - A markdown table of sampled issues.
 - Specific code snippets showing the ambiguity.
 - Automated pre-checks: Syntax validity, complexity score change, AST hash difference.
 - A placeholder section for human review (e.g., `[ ] Human Review Pending`).
 2. **Output**: The report is generated automatically. The pipeline proceeds immediately. Human review is an out-of-band step and does not block execution.
 - **Note**: This task replaces the manual blocking step. Downstream tasks (T016, T021) proceed immediately.
 - **Dependency**: T012, T001b, T002, T003a, T004, T005, T006.

- [ ] T016-ValidateHardSubset [US1] **Automated Validation Gate**
 - Run `code/data/validate_hard.py` to confirm low coverage of the hard subset.
 - Output: `data/results/validation_status.json` (`PASSED` or `WARNING`). Pipeline proceeds regardless of status.
 - **Dependency**: T012.

## Phase 2: Foundational (Blocking Prerequisites)

- [ ] T003b [P] **Run Hash Utility on Curated Data**
 - Execute `hash_artifacts.py` (T003a) on `data/curated/` after T014.
 - **Dependency**: T014.

## Phase 3: Iterative Agent Execution Loop (User Story 2)

### Tests

- [ ] T017 [P] **Contract test for agent log schema** (`tests/contract/test_agent_log_schema.py`).
 - **Dependency**: T004, T022a, T022b, T023 (to have data to validate).

- [ ] T018 [P] **Integration test for agent loop termination** (`tests/integration/test_agent_loop.py`).
 - **Dependency**: T023.

### Implementation

- [ ] T019 [P] **Static Analysis Wrapper**
 - Implement `code/agent/static_analysis.py` to run `pylint` and `ast` checks, returning error messages or a `neutral_anomaly` flag on unexpected failures (see T050).
 - **Dependency**: T001b, T002, T003a, T004, T005, T006.

- [ ] T020 [P] **Prompt Templates**
 - Create `code/agent/prompts.py` with Jinja2 templates for query reformulation that embed detected error messages.
 - **Dependency**: T001b, T002, T003a, T004, T005, T006.

- [ ] T021 [P] **Data Locking & Subset Consistency**
 - Copy `data/curated/hard_subset.jsonl` to `data/results/locked_hard_subset.jsonl` under a file lock.
 - Depends on **T012**. (T016 is a parallel validation step, not a blocker for locking).
 - **Dependency**: T012.

- [ ] T047 [P] **Implement Loop Detection Logic**
 - **CRITICAL**: Must be implemented BEFORE T023 runs to prevent infinite loops.
 - Create the core loop detection logic in `code/agent/iterative.py` that compares the current query against the previous two; if identical, sets `termination_reason: "loop_detected"`.
 - **Dependency**: T043 (Quantized Model). Does NOT depend on T022.
 - **Note**: This task is NOT parallel-safe with T023.

- [ ] T022a [P] **Static One-Shot Baseline**
 - **Goal**: Implement the strict "one-shot" baseline required by SC-001 and US-3.
 - **Logic**: Run a single retrieval turn per issue. No feedback loop.
 - Input: `locked_hard_subset.jsonl` (T021).
 - Output: `data/results/baseline_onshot_logs.jsonl`.
 - **Dependency**: T021, T043, T001b, T002, T003a, T004, T005, T006.

- [ ] T022b [P] **Static Multi-Query Baseline (Optional)**
 - **Goal**: Implement a multi-query baseline (same total query budget as iterative) for secondary comparisons.
 - Input: `locked_hard_subset.jsonl` (T021).
 - Output: `data/results/baseline_multi_logs.jsonl`.
 - **Dependency**: T021, T043, T001b, T002, T003a, T004, T005, T006.

- [ ] T023 [P] **Iterative Agent**
 - Implements a multi-turn loop with query → retrieve → static analysis → reformulate.
 - **Loop detection** (T047) is incorporated here.
 - Input: `locked_hard_subset.jsonl`.
 - Output: `data/results/iterative_logs.jsonl`.
 - **Dependency**: T021, T043, T047, T022a (for baseline comparison), T001b, T002, T003a, T004, T005, T006.

- [ ] T024a [P] **Power Analysis for Sensitivity Sweep**
 - **Purpose**: Verify that `SWEEP_SAMPLE_SIZE` is statistically sufficient. to represent the `hard_subset` size.
 - `code/analysis/power_analysis.py` calculates the power of the sensitivity test given the subset size and expected effect size.
 - Output: `data/results/power_analysis_report.md`. If insufficient, log a `WARNING` but proceed (as per plan constraints).
 - **Dependency**: T012.

- [ ] T024b [P] **Turn‑Limit Sweep**
 - Sample `SWEEP_SAMPLE_SIZE` issues (seed `SWEEP_SEED`) stratified by complexity quartiles.
 - Run iterative agent for each turn limit in `TURN_LIMITS`.
 - Aggregate results to `data/results/sweep_results.json`.
 - **Validation Step**: Explicitly compare sweep results against the 3-turn limit constraint to verify stability.
 - Depends on **T024a** and **T043**.

- [ ] T024c [P] **Sensitivity Validation**
 - Read `data/results/sweep_results.json`.
 - Verify if the 3-turn limit yields stable results compared to the sweep (e.g., no significant drop in coverage after 3 turns).
 - If unstable, flag a `WARNING` in `data/results/sensitivity_validation.json`.
 - **Dependency**: T024b.

- [ ] T025 [P] **Hash Agent Artifacts**
 - Run `hash_artifacts.py` (T003a) on `data/results/agent_logs/`.

- [ ] T050 [P] **Static Analysis Neutral Signal**
 - Update `code/agent/static_analysis.py` to catch exceptions; on failure, emit `static_analysis_signal: "neutral_anomaly"` and continue without crashing.

## Phase 4: Comparative Metric Calculation and Statistical Testing (User Story 3)

### Tests

- [ ] T026 [P] **Contract test for result schema** (`tests/contract/test_result_schema.py`).
 - **Dependency**: T004, T030-Bonferroni.

- [ ] T027 [P] **Unit test for statistical tests** (`tests/unit/test_stats.py`) – includes Wilcoxon and tie-handling.

### Implementation

- [ ] T028 [P] **Coverage Metric** (`code/metrics/coverage.py`).
 - **Dependency**: T001b, T002, T003a, T004, T005, T006.

- [ ] T029 [P] **Ranking Metric** (`code/metrics/ranking.py`) – applies `N+1` penalty for censored cases.
 - **Dependency**: T001b, T002, T003a, T004, T005, T006.

- [ ] T030a [P] **Analyze Tie Distribution & Justify Threshold**
 - Reads `baseline_onshot_logs.jsonl` (from T022a) and `iterative_logs.jsonl` (from T023).
 - {{claim:c_327c1457}} (Wikidata Q1424533, https://www.wikidata.org/wiki/Q1424533)
 - **Censored Definition**: Explicitly checks for `missing_data` flags in logs, NOT `relevant_lines == 0`. Zero coverage is a valid metric, not censored data.
 - **Output**: `data/results/tie_analysis.json` containing:
 - `tie_proportion`: float.
 - `censored_count`: int (based on missing data flags).
 - `justification`: A string explaining why the threshold (e.g., 20%) is appropriate for this distribution, or if the data requires the permutation test.
 - **Dependency**: T022a, T023.

- [ ] T030b [P] **Route Statistical Test**
 - Reads `data/results/tie_analysis.json` (from T030a).
 - **Logic**:
 - If `tie_proportion > config.TIE_THRESHOLD` (0.50) OR any censored entries (missing data) exist: write `statistical_routing.json` with `"PERMUTATION"`.
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
 - **Constraint**: If runtime exceeds `MAX_RUNTIME_HOURS`, the run logs the partial runtime and writes a `FAIL` status to `data/results/feasibility_report.md` with the exact runtime value. It does NOT exit silently. This ensures SC-005 (measuring feasibility) is satisfied by recording the data point.
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

## Phase O: Revision & Review Resolution

- [ ] T051 [P] **Resolve Review: Synthetic Data Validation**
 - Address reviewer concern regarding the lack of explicit validation for synthetic issue quality.
 - Enhance `code/data/curate.py` (T013) to output a `validation_metrics.json` containing:
 - Count of valid vs. invalid mutations.
 - Average syntactic complexity change.
 - Average semantic distance (using AST hash difference).
 - **Dependency**: T013.

- [ ] T052 [P] **Resolve Review: Turn Limit Sensitivity**
 - Address reviewer concern that a fixed 3-turn limit may be arbitrary.
 - Ensure `code/analysis/power_analysis.py` (T024a) explicitly calculates the minimum detectable effect size for the chosen `SWEEP_SAMPLE_SIZE`.
 - Add a task to run the sweep on a small subset (N=5) to verify the `TURN_LIMITS` configuration before full execution.
 - **Dependency**: T024a, T024b.

- [ ] T053 [P] **Resolve Review: Statistical Power & Tie Handling**
 - Address reviewer concern about the robustness of the Wilcoxon test with potential ties.
 - Implement a fallback mechanism in `code/metrics/stats.py` that automatically switches to the exact permutation test if the tie proportion is substantial (configurable).
 - Add a unit test in `tests/unit/test_stats.py` specifically for the tie-handling logic.
 - **Dependency**: T030a, T030b, T027.

- [ ] T054 [P] **Resolve Review: Human Validation Protocol**
 - Address reviewer concern about the manual validation step (T015) being a bottleneck.
 - Refine the `validation_report_template.md` (T015) to include automated pre-checks (e.g., syntax validity, complexity score) to guide the human reviewer.
 - Ensure the pipeline logic does NOT block on a `human_verified` flag (as T015 is now automated).
 - **Dependency**: T015.

- [ ] T055 [P] **Resolve Review: Data Source Integrity**
 - Address reviewer concern about the reliability of the SWE-Explore dataset source.
 - Add a checksum verification step in `code/data/download.py` (T010) that compares the downloaded file against a known cryptographic hash from the official repository.
 - If the checksum fails, raise a `DataIntegrityError` and halt the pipeline.
 - **Dependency**: T010.