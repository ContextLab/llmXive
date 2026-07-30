# Tasks: llmXive follow-up: extending "SWE-Explore: Benchmarking How Coding Agents Explore Repositories"

**Input**: Design documents from `/specs/001-iterative-exploration-benchmark/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 0: Administrative Alignment

- [ ] T000-Notice [P] **Plan Alignment Update**  
  **Action**: Edit `plan.md` to replace any mention of "Cyclomatic Complexity" selection with "initial_coverage" filtering (FR‑001) and to remove "Survival Analysis" references if they contradict the primary Wilcoxon/Permutation flow, or clarify that Survival Analysis is the fallback for censored data (FR‑006).  
  **Patch**: Replace lines containing `Cyclomatic Complexity` with `initial_coverage`; ensure `Survival Analysis` is described as the fallback for censored ranking data.  
  **Verification**: Run a diff check to confirm the changes.  
  **Dependency**: None.  
  **Artifacts Changed**: `plan.md`.

## Phase 1: Setup (Shared Infrastructure)

- [ ] T001a [P] **Create Project Structure**  
  - Create directories: `code/`, `data/raw/`, `data/curated/`, `data/results/`, `tests/unit/`, `tests/integration/`, `tests/contract/`, `contracts/`, `docs/`, `paper/`.  
  - Verify existence of each directory.  
  - Output: Directory structure created.

- [ ] T001b [P] **Configure Linting and Formatting**  
  - Create `code/pyproject.toml` containing ruff and black configuration (no separate config files).  
  - Run `ruff check code/` and `black --check code/` to ensure no errors.

- [ ] T002 [P] **Config Constants**  
  - Implement `code/config.py` with paths, seeds, model config, and concrete values:  
    ```python
    HARD_INSTANCE_PERCENTILE = 0.20
    COVERAGE_COLUMN_NAME = 'initial_coverage'
    SWEEP_SAMPLE_SIZE = 50          # concrete value
    SWEEP_SEED = 42                # concrete value
    TURN_LIMITS = [1, 2, 3, 4]
    MIN_SYNTHETIC_ISSUES = 10
    VALIDATION_SAMPLE_SIZE = 5
    TIE_THRESHOLD = 0.20
    ```  
  - Verify importability.

- [ ] T003 [P] **Hash Artifacts Utility**  
  - Implement `code/utils/hash_artifacts.py` to compute SHA‑256 hashes for all files under `data/` and write a manifest to `state/`.

- [ ] T004 [P] **Create Contracts Directory & Sample Schemas**  
  - Create `contracts/` with placeholder YAML schemas: `dataset_schema.yaml`, `agent_log_schema.yaml`, `result_schema.yaml`.  
  - Ensure files are non‑empty and syntactically valid YAML.

- [ ] T005 [P] **Schema Validation Helper**  
  - Implement `code/utils/validation.py` to validate JSONL/Parquet files against the schemas in `contracts/`.

- [ ] T006 [P] **Pytest Configuration & Contract Test Skeleton**  
  - Add `pytest.ini` and create `tests/contract/test_schemas.py` skeleton that will later import `validation.py`.

- [ ] T043a [P] **Model Loading (CPU-First)**  
  - Create `code/agent/quantized_llm.py` with a function that loads the chosen model (e.g., `Qwen-1.5B`) using `llama_cpp` or `transformers`.  
  - **Primary Strategy**: Load in `float32` on `device='cpu'`.  
  - **Fallback Strategy**: If memory pressure is detected, attempt 8-bit quantization (`n_gpu_layers=0`, `load_in_8bit=True` if supported by backend).  
  - Add a runtime check that aborts with a clear `MemoryError` if process memory exceeds 6 GB.

- [ ] T043b [P] **CPU-Only Configuration**  
  - Ensure the loader forces CPU execution (`device='cpu'`) and disables any GPU fallback.

- [ ] T043 [P] **Quantized Model Orchestration**  
  - Orchestrate the three sub‑tasks above; this task must complete before any agent execution (T022, T023).

## Phase 2: Foundational (Blocking Prerequisites)

- [X] T002 (already completed above)

- [X] T003 (already completed above)

- [X] T004 (already completed above)

- [X] T005 (already completed above)

- [X] T006 (already completed above)

- [ ] T043a‑c (implemented as separate sub‑tasks)

## Phase 3: User Story 1 - Data Curation and Hard Instance Selection (Priority: P1)

### Tests (must be written first)

- [ ] T007 [P] **Contract test for dataset schema** (`tests/contract/test_dataset_schema.py`) – depends on T004.

- [ ] T008 [P] **Unit test for mutation logic** (`tests/unit/test_mutation.py`).

- [ ] T009 [P] **Unit test for synthetic issue validity** (`tests/unit/test_synthetic_validity.py`).

### Implementation

- [ ] T010 [P] **Implement Robust Data Fetcher**  
  - `code/data/download.py` uses `datasets.load_dataset(..., streaming=True)` to fetch `bench.final.public.jsonl` from HuggingFace.  
  - On any failure, raise `ConnectionError` with a clear message. No synthetic fallback.

- [ ] T011 [P] **Implement Ground Truth Derivation with Streaming**  
  - `code/data/derive_gt.py` parses solution patches, emits `ground_truth_lines`, writes to `data/raw/swe_explore_with_gt.jsonl`.  
  - Uses streaming to stay <7 GB RAM.

- [ ] T012 [US1] **Filter Hard Subset (Spec Alignment)**  
  - `code/data/filter_hard.py` reads `data/raw/swe_explore_with_gt.jsonl`, selects bottom `HARD_INSTANCE_PERCENTILE` of `COVERAGE_COLUMN_NAME` (per Spec FR-001).  
  - Calculates cyclomatic complexity as supplementary metadata (does not affect selection).  
  - Writes `data/curated/hard_subset.jsonl`.

- [ ] T012c [US1] **Generate Non‑Hard Subset**  
  - Depends on **T011** and **T012**.  
  - Reads both files, writes complement to `data/curated/non_hard_subset.jsonl`.  
  - **Validation**: If resulting file is empty, raise `ValueError('Non‑hard subset is empty after complement operation')`.

- [ ] T013 [US1] **Generate Synthetic Ambiguous Issues**  
  - Input: `data/curated/non_hard_subset.jsonl` (T012c) and original ground‑truth from `data/raw/swe_explore_with_gt.jsonl` (T011).  
  - Mutation pipeline:
    1. If input pool size < `config.MIN_SYNTHETIC_ISSUES`, generate **all** possible valid mutations, log a `WARNING`, and proceed.
    2. Apply variable renaming, comment removal, structural obfuscation via `libcst`.
    3. Validate each mutated file with `ast.parse`; **skip invalid ones with a warning** (do not crash the script).
    4. If **total valid mutations == 0**, log a `WARNING` and proceed with an empty synthetic set (or raise if Spec requires non-empty, but Spec says skip).
    5. If **0 < valid mutations < MIN_SYNTHETIC_ISSUES**, log a `WARNING` with the count and continue.
  - Store `ground_truth_lines` from the original unmutated code (FR‑008).  
  - Output: `data/curated/synthetic_issues.jsonl`.

- [ ] T014 [P] **Metadata & Versioning**  
  - Write `data/curated/synthetic_issues_meta.json` with hashes, mutation parameters, and counts.  
  - Run `hash_artifacts.py` on the curated folder.

- [ ] T015 [P] **Generate Validation Report**  
  - Randomly sample `VALIDATION_SAMPLE_SIZE` issues from `hard_subset.jsonl` and produce a markdown table. No gating effect.

- [ ] T016‑AutoValidate [US1] **Automated Validation Gate**  
  - Run `code/data/validate_hard.py` to confirm low coverage of the hard subset and embed a "Plan Override Justification" block documenting the switch from cyclomatic‑complexity to initial_coverage.  
  - Output: `data/curated/validation_report.md` and `validation_status.json` (`PASSED` or `WARNING`). Pipeline proceeds regardless of status.

## Phase 4: User Story 2 - Iterative Agent Execution Loop (Priority: P2)

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
  - Depends on **T012** and **T016‑AutoValidate** (hard subset must be validated). No dependency on T012c.

- [ ] T047 [P] **Deterministic Loop Detection & Early Exit**  
  - **CRITICAL**: Must be implemented BEFORE T023 runs to prevent infinite loops.  
  - Enhance `code/agent/iterative.py` to compare the current query against the previous two; if identical, terminate loop, log `termination_reason: "loop_detected"`.  
  - **Dependency**: Must be implemented before T023 runs.

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

- [ ] T024b [P] **Turn‑Limit Sweep**  
  - Sample `SWEEP_SAMPLE_SIZE` issues (seed `SWEEP_SEED`) stratified by complexity quartiles.  
  - Run iterative agent for each turn limit in `TURN_LIMITS`.  
  - Aggregate results to `data/results/sweep_results.json`.  
  - Depends on **T012** and **T043**.

- [ ] T025 [P] **Hash Agent Artifacts**  
  - Run `hash_artifacts.py` on `data/results/agent_logs/`.

- [ ] T050 [P] **Static Analysis Neutral Signal**  
  - Update `code/agent/static_analysis.py` to catch exceptions; on failure, emit `static_analysis_signal: "neutral_anomaly"` and continue without crashing.

## Phase 5: User Story 3 - Comparative Metric Calculation and Statistical Testing (Priority: P3)

### Tests

- [ ] T026 [P] **Contract test for result schema** (`tests/contract/test_result_schema.py`).

- [ ] T027 [P] **Unit test for statistical tests** (`tests/unit/test_stats.py`) – includes Wilcoxon and censored‑data handling.

### Implementation

- [ ] T028 [P] **Coverage Metric** (`code/metrics/coverage.py`).

- [ ] T029 [P] **Ranking Metric** (`code/metrics/ranking.py`) – applies `N+1` penalty for censored cases.

- [ ] T030‑Prep [P] **Censoring & Tie Routing**  
  - Reads `baseline_logs.jsonl` (from T022) and `iterative_logs.jsonl` (from T023).  
  - Counts ties as paired absolute differences equal to zero.  
  - Computes `tie_proportion = ties / total_pairs`.  
  - Checks for censored entries (no relevant lines found).  
  - If `tie_proportion > config.TIE_THRESHOLD` (a predefined threshold) **OR** any censored entries exist, write `statistical_routing.json` with `"PERMUTATION"` or `"SURVIVAL"`; else write `"WILCOXON"`.

- [ ] T030‑Survival [P] **Survival Analysis (Censored Data)**  
  - Executes only when routing flag indicates censored data.  
  - Applies Cox proportional hazards or modified Wilcoxon for censored data to handle "no relevant lines" cases.  
  - **Dependency**: T030-Prep.

- [ ] T030‑Primary [P] **Wilcoxon Signed‑Rank Test**  
  - Executes only when routing flag is `"WILCOXON"`.  
  - Applies continuity correction for ties.

- [ ] T030‑Permutation [P] **Exact Permutation Test**  
  - Executes only when routing flag is `"PERMUTATION"`.  
  - Used when ties exceed threshold or censored data is present (fallback).

- [ ] T030c [P] **Multiplicity Correction & Framing**  
  - Apply Bonferroni correction to both coverage and ranking p‑values.  
  - Ensure all result text uses "associational differences" phrasing.

- [ ] T031 [P] **Visualization** (`code/analysis/plots.py`).

- [ ] T032 [P] **Hash Final Metrics** – update `code/main.py` to hash `final_metrics.json` after T030c.

- [ ] T033‑Zero [P] **Report Template Creation**  
  - Create `code/analysis/report_template.j2` with placeholders matching keys in `contracts/result_schema.yaml` (e.g., `p_value`, `effect_size`, `coverage_diff`, `ranking_diff`, `n_issues`, `methodology`, `conclusion`).  
  - Include a validation step that the rendered template conforms to `result_schema.yaml`; failures abort the task.

- [ ] T033‑b [P] **Generate Report Draft**  
  - Render the template using data from `final_metrics.json`.  
  - **Dependency**: Must run **after** successful execution of T030c and T033‑Zero.  
  - **Output**: `paper/draft_unvalidated.md`.

- [ ] T033‑d [P] **Validate Report Language**  
  - Regex scan for causal verbs; fail if any match.  
  - Verify schema compliance.  
  - **Dependency**: Must run **after** T033‑b.  
  - **Output**: `paper/draft_validated.md` (if pass) or error.

- [ ] T033‑c [P] **Final Report Assembly**  
  - Assemble `paper/draft.md` from the validated draft and ensure schema compliance.  
  - **Dependency**: Must run **after** T033‑d.

- [ ] T033‑Z [P] **Results Summary**  
  - Run the pipeline T033‑b → T033‑d → T033‑c and output `paper/results_summary.md`.  
  - **Dependency**: T033-c.

- [ ] T048 [P] **Robust Mutation Fallback**  
  - Integrated into T013 logic (see T013 description).

- [ ] T049 [P] **Permutation Test Sensitivity Check**  
  - Re‑run permutation test with penalty values N+1, N+5, N+10; store variance in `data/results/sensitivity_analysis.json`.

## Phase N: Polish & Cross‑Cutting Concerns

- [ ] T035 [P] **Update Quickstart Documentation** (`docs/quickstart.md`) with execution instructions and data‑flow diagrams.

- [ ] T036 [P] **Refactor Iterative Agent** to reduce cyclomatic complexity.

- [ ] T037 [P] **Optimize Coverage Metric Memory Usage** – process lines in chunks.

- [ ] T038 [P] **Add Unit Tests for Stats Module** (`tests/unit/test_stats_logic.py`).

- [ ] T039 [P] **Runtime Monitor**  
  - Insert timing logic in `code/main.py`; if total runtime exceeds a predefined threshold, abort non‑critical sweeps or down‑sample remaining issues to stay within a reasonable time limit.

- [ ] T046‑StatsValidation [P] **Bonferroni Correction Verification** – test that `final_metrics.json` includes adjusted p‑values.

- [ ] T046‑FramingValidation [P] **Causal Language Validation** – ensure final report contains no prohibited phrasing.