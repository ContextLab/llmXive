# Tasks: llmXive follow-up: extending "VideoKR: Towards Knowledge- and Reasoning-Intensive Video Understanding"

**Input**: Design documents from `/specs/001-video-reasoning-threshold/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[S]**: Sequential (must run in order)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

<!--
 ============================================================================
 IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

 The /speckit-tasks command MUST replace these with actual tasks based on:
 - User stories from spec.md (with their priorities P1, P2, P3...)
 - Feature requirements from plan.md
 - Entities from data-model.md
 - Endpoints from contracts/

 Tasks MUST be organized by user story so each story can:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] **Initialize Project Structure**: Create `scripts/init_project.py` to create all required directories (`code/`, `tests/`, `data/`, `data/raw/`, `data/processed/`, `code/ingest/`, `code/analysis/`, `code/utils/`, `tests/unit/`, `tests/integration/`) and `.gitkeep` files. **Verification**: Run `scripts/init_project.py` and verify all directories exist using `os.path.exists`; raise error if creation fails. **Output**: `scripts/init_project.py`.

---

## Phase 2: Foundational (Blocking Prerequisites & Utils)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin. **T034 is moved to Phase 4.**

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 [P] Implement `code/utils/config.py` for seed management and path configuration. **Schema**: Must define `sensitivity_thresholds` as a list of integers (default: `[2, 3, 4]`) to allow configurable threshold sweeps in T025.
- [X] T005 [P] Implement `code/utils/versioning.py` to write SHA-256 hashes of data artifacts (Constitution Principle V).
- [X] T006 [P] Create `code/utils/graph_utils.py` with shortest path logic (BFS) handling disconnected graphs.
- [X] T007 [P] Create `code/utils/entity_linker.py` for mapping question entities to graph nodes (fuzzy/embedding based). **Conditional Logic**: The script must first check if the input dataset already contains a `node_id` or `entity_id` column. If present, it MUST skip the linking process and use the provided IDs. If absent, it MUST implement the fuzzy/embedding linking logic. This satisfies FR-001 without assuming a specific data source structure.
- [X] T009 [P] Implement `code/ingest/checksum.py` as a utility script to be invoked by T013 for verifying raw data integrity (Constitution Principle III).

---

## Phase 3: User Story 1 - Data Ingestion and Structural Annotation (Priority: P1) 🎯 MVP

**Goal**: Download VideoKR-SFT, annotate questions with structural chain length (hops) from the ground-truth graph. **Includes mandatory streaming and verification logic.**

**Independent Test**: Run the annotation script on a small, manually verified subset; confirm `chain_length` matches manual graph traversal for a representative sample of random records.

### Tests for User Story 1 (MANDATORY)

- [X] T010 [S] [US1] Unit test for `graph_utils.py` shortest path logic in `tests/unit/test_graph_utils.py` (handles disconnected nodes, shortest path rule). **Depends on T006 completion.**
- [X] T011 [S] [US1] Integration test for `annotate_graph.py` on a sample subset in `tests/integration/test_pipeline.py` **Depends on T006, T007, T009 completion.**

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/ingest/download_data.py` to fetch VideoKR-SFT and Knowledge Graph from verified URLs (NAB/UCI/arXiv) with checksumming, invoking T009 for verification.
- [X] T013 [S] [US1] **Implementation (Producer) with Streaming & Oversampling**: Implement `code/ingest/annotate_graph.py` to:
 - **Unified Streaming & Sampling Strategy**: Implement a strict **Pilot -> Oversample** process as mandated by the Plan, using streaming for the pilot fetch:
 1. **Pilot Phase**: Run a pilot sample of exactly **1000 rows** using `datasets.load_dataset(name, split=..., streaming=True)` and `itertools.islice` to estimate the distribution of `chain_length`. **Seed**: MUST use `config.get_seed('pilot_sampling')`.
 2. **Oversampling Check**: If any bin (especially '3+') has **<50 samples** in the pilot, trigger an **Oversampling** step.
 3. **Oversampling Logic**: Use stratified resampling (with replacement) on the **pilot subset** (which fits in memory) to reach N>=50 for rare bins. **Explicitly preserve the distribution of hop counts**. **Seed**: MUST use `config.get_seed('oversampling')`.
 4. **Logging**: Log the sampling method, pilot size (1000), oversampling target, and final sample size to `data/processed/sampling_log.json`.
 - **Chunked Processing**: Implement chunked streaming (e.g., `pandas.read_csv(chunksize=...)`) to process the dataset in memory-safe batches if full load is not feasible.
 - **Pre-Retry Logging (TEMP)**: **CRITICAL**: Before executing any self-healing retry logic, the script MUST calculate and write `total_input_records`, `unresolvable_count`, and `proportion` to `data/processed/annotation_coverage.tmp.json` based on the current run's state. **Constraint**: These metrics must be **AGGREGATED** (APPEND) across all retry attempts to reflect the cumulative state of the ingestion attempt. This log must be written **BEFORE** any retry attempt to ensure traceability of failure modes. **DO NOT** write the final `annotation_coverage.json` here. **T013 must NOT write the final `annotation_coverage.json`; this is the exclusive responsibility of T013b.**
 - **Self-Healing Regeneration Logic**: If the output file `data/processed/annotated_videokr.csv` is empty, missing, or has <50 rows after the initial run, **re-run** the full annotation pipeline with adjusted parameters (pilot size doubled, max 2 retries). If 2 retries fail, raise a `DataUnavailableError`. **DO NOT** rely on a separate task to regenerate. This task MUST guarantee the artifact exists or raises a clear error.
 - **Map entities**: Map question entities to graph nodes using `entity_linker.py`. **Conditional**: If `entity_linker.py` detects pre-existing node IDs (per T007), use them directly. Otherwise, perform linking.
 - **Input**: `question` text column.
 - **Output**: `entity_node_id` (string) and `confidence` (float).
 - **Handling**: If `confidence < threshold`, mark as `unmapped` and log.
 - **Calculate Exact Hops**: Calculate the **exact integer** shortest path hops (1, 2, 3, 4, 5...) for each record. Output this as the column `chain_length` (integer type).
 - **Algorithm**: Use BFS (Breadth-First Search) for unweighted graphs. If weighted, use Dijkstra.
 - **Tie-Breaking**: If multiple shortest paths exist, use the one with the lexicographically smallest node sequence.
 - **Generate Binned Column**: Derive a second column `chain_bin` (categorical: '1', '2', '3+') from `chain_length` for categorical analysis.
 - **Handle Disconnected**: Exclude or label 'unresolvable' for disconnected graphs. For both 'unmapped' and 'unresolvable' records, **explicitly write `-1` to the `chain_length` column** to ensure integer type consistency for downstream binning.
 - **Enforce Shortest Path**: Use the shortest path rule for multiple paths.
 - **Preserve Correctness**: **Explicitly copy** the `correctness` column from the source VideoKR-SFT dataset to the output CSV. (FR-001, Data Model)
 - **Write Output**: **Explicitly write** the final artifact `data/processed/annotated_videokr.csv` with columns: `id`, `question`, `answer`, `chain_length` (integer), `chain_bin` (categorical), `correctness`. (FR-001, FR-002, SC-001) **Constraint**: **Use a temporary file for intermediate writes.** Write the final artifact to `data/processed/annotated_videokr.csv` **ONLY after successful completion (or max retries)**, renaming the temp file to the final path to prevent partial writes.
 - **Compliance: No Synthetic Data**: **Integrated Check**: The script must raise `DataUnavailableError` if the real data fetch fails or if any fallback to `generate_synthetic_*`, `mock_*`, or random data is detected. **Constraint**: This check is integrated into T013 execution flow. **Verification**: Ensure no `try/except` blocks in the data loader fall back to synthetic data.
 - **Note**: This task is strictly the **producer**. Verification of row counts and coverage is handled by T013b.
- [X] T013b [S] [US1] **Verification (Validator) & Final Aggregation**: Verify the output of T013.
 - **Input**: `data/processed/annotated_videokr.csv` (produced by T013) AND `data/processed/annotation_coverage.tmp.json` (produced by T013).
 - **Logic**: Verify that the row count matches the input (excluding unmapped/unresolvable). **Aggregate** counts from `annotation_coverage.tmp.json` (if multiple runs occurred) to calculate the final `total_input_records`, `unresolvable_count`, and `annotated_count`.
 - **Output**: **Write the definitive** `data/processed/annotation_coverage.json` with the final aggregated counts and `proportion = annotated_count / total_input_records`. (SC-001) **Constraint**: This task is the **Single Source of Truth** for coverage metrics. It MUST overwrite any temporary logs.
 - **Constraint**: **Runs ONLY if T013 completes successfully.** If T013 raised an error (including self-healing failure), T013b is skipped by the orchestrator.
 - **Depends on**: T013 completion.
- [X] T016 [US1] Write hash of `annotated_videokr.csv` to `state/projects/PROJ-961-llmxive-follow-up-extending-videokr-towa.yaml`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Accuracy Stratification and Threshold Detection (Priority: P2)

**Goal**: Calculate accuracy per hop-bin, detect non-linear "reasoning cliff" using Permutation Test (per Plan override).

**Independent Test**: Generate accuracy vs. hop plot and statistical report; verify trend and p-value against raw data summary.

### Tests for User Story 2 (MANDATORY)

- [X] T017 [P] [US2] Unit test for accuracy calculation logic in `tests/unit/test_stratify_accuracy.py`
- [X] T018 [P] [US2] Integration test for `detect_threshold.py` on annotated data in `tests/integration/test_pipeline.py`

### Implementation for User Story 2

- [X] T019 [S] [US2] **Implementation (Stratification)**: Implement `code/analysis/stratify_accuracy.py` to:
 - Calculate accuracy rate for bins 1-hop, 2-hop, 3+ hops (aggregating 3, 4, 5... into '3+' for the primary report as per Spec US-2).
 - **Bin Size Check**: If the '3+' bin (or any other bin) has <50 records, **raise a `BinPowerError`** immediately. This error must be caught by the orchestrator (T035) to prevent T020b from running. (FR-003)
 - **Dependency**: **Must run after T013** to access `data/processed/annotated_videokr.csv`.
 - **Compliance: Streaming & Power**: **Integrated Check**: The script must verify `streaming=True` or `chunksize` usage for large datasets and that `BinPowerError` is raised if power is insufficient. **Constraint**: This check is integrated into T019 execution flow. **Verification**: Ensure no `pandas.read_csv()` without `chunksize` or `streaming=True` for large files.
- [X] T020a [S] [US2] **Bin Preparation & Merging Logic**: Implement `code/analysis/bin_utils.py` to:
 - **Input**: Use **exact integer `chain_length` data from T013** (1, 2, 3, 4, 5...) and bin counts from T019.
 - **Logic**: Check if the highest bin (or any bin used in the test) contains a low number of samples.
 1. **Attempt Merge**: Merge the underpowered bin with the adjacent bin (e.g., 3+ with 2-hop).
 2. **Re-check**: If the merged bin has >= 50 samples, proceed with the test on the merged bin and log `bin_status: "merged"` to `data/processed/bin_status.json`.
 3. **Defer**: If the merged bin still has < 50 samples, **defer** the statistical test for this comparison. Write `status: "deferred"`, `reason: "insufficient_power"`, and `bin_status: "deferred"` to the JSON file. **Do not** fabricate data, merge blindly, or force a test.
 - **Output**: Write a JSON file `data/processed/bin_config.json` containing `{'bins': [...], 'strategy': 'merged' | 'deferred'}`. This defines the **final static binning strategy** to be used by T020b.
 - **Depends on T013** (raw data) and **T019**. **Must run after T019**.
- [X] T034a [S] [US2] **Refactor Scripts to Library (US1)**: Refactor `code/ingest/annotate_graph.py` (T013) to expose a `run()` function. **Constraint**: Remove `if __name__ == '__main__':` execution logic; instead, it must be importable by T035. The `run()` function must accept a `config` object and return a status code. **Verification**: Import the module in a test script and call `run()` to verify it executes without `__main__` block interference. **Dependency**: Must run after T013 completion.
- [X] T034b [S] [US2] **Refactor Scripts to Library (US2-Strat)**: Refactor `code/analysis/stratify_accuracy.py` (T019) to expose a `run()` function. **Constraint**: Remove `if __name__ == '__main__':` execution logic; instead, it must be importable by T035. The `run()` function must accept a `config` object and return a status code. **Verification**: Import the module in a test script and call `run()` to verify it executes without `__main__` block interference. **Dependency**: Must run after T019 completion.
- [X] T034c [S] [US2] **Refactor Scripts to Library (US2-Threshold)**: Refactor `code/analysis/detect_threshold.py` (T020b) to expose a `run()` function. **Constraint**: Remove `if __name__ == '__main__':` execution logic; instead, it must be importable by T035. The `run()` function must accept a `config` object and return a status code. **Verification**: Import the module in a test script and call `run()` to verify it executes without `__main__` block interference. **Dependency**: Must run after T020b implementation completion.
- [X] T020b [S] [US2] **Threshold Detection (Permutation Test) & Final Output**: Implement `code/analysis/detect_threshold.py` to:
 - **Input**: Use **exact integer `chain_length` data from T013** and the **static binning strategy from T020a** (`data/processed/bin_config.json`).
 - **Methodology**: **Per Plan Complexity Tracking table**, use a **Permutation Test** (n=1000) for change-point detection to avoid inflated Type I errors from data-driven knot selection. **Note**: This overrides Spec FR-004's LRT requirement based on the Plan's explicit rejection of LRT for data-driven knot selection. **Cite Plan.md 'Complexity Tracking' table** as the authority for this deviation. **Note**: GAMs (FR-007) are explicitly removed per Plan Complexity Tracking; Permutation Test is the only approved method.
 - **Grid-Search Logic**: Iterate knot locations from **1 to 5** (fixed range per Spec FR-004). For each knot:
 1. Fit a linear model (accuracy ~ hop_count).
 2. Fit a piecewise linear model (accuracy ~ hop_count + max(0, hop_count - knot)).
 3. **Permutation Engine**: Perform the permutation test by **randomly shuffling the `correctness` labels** (n=1000 times) and recalculating the test statistic for each shuffle to build the null distribution. **CRITICAL**: The grid search is performed to find the *optimal* knot. The Permutation Test is then run *n=1000 times* where, for **each permutation**, the **maximum** test statistic across all grid points (knots 1-5) is recorded to build the null distribution. This accounts for the multiple comparisons and prevents inflated Type I errors.
 4. **Test Statistic Definition**: The test statistic is the **Difference in Residual Sum of Squares (RSS)** between the linear model and the piecewise linear model.
 5. Calculate the p-value as the proportion of permuted statistics >= observed statistic.
 - **Correction**: Apply **Bonferroni correction** for the number of tests performed (p_corrected = p_raw * num_tests).
 - **Selection**: Select the knot location with the minimum corrected p-value.
 - **Power Analysis**: If total sample size < 1000 or smallest bin < 50, log a warning to `data/processed/power_analysis.json` stating 'Insufficient power for robust inference' (do not attempt calculation without parameters).
 - **Reproducibility Check**: **Internal Step**: Run the permutation test twice with the same seed and verify p-values match exactly within a tolerance of **1e-9**. If results differ beyond tolerance, raise a `ReproducibilityError`. Log the comparison to `data/processed/reproducibility_check.json`. **Constraint**: This check must be integrated into the execution flow of T020b and halt the pipeline if it fails.
 - **Output**: Identify the optimal knot and report the corrected p-value. (FR-004)
 - **Final Artifact**: **Explicitly write** `data/processed/threshold_results.json` with the following schema:
 ```json
 {
 "p_value": float,
 "alpha": 0.05,
 "is_significant": boolean | null,
 "conclusion": string,
 "optimal_knot": int
 }
 ```
 (SC-002) **Constraint**: If `data/processed/bin_config.json` indicates `strategy: 'deferred'`, **set `is_significant` to `null` and `conclusion` to 'DEFERRED'**. This provides a definitive output state that accurately reflects the inability to compute a boolean due to underpowered bins, satisfying the 'Single Source of Truth' principle.
 - **Depends on T013** (raw data), **T006** (graph utils), **T020a** (static binning), and **T034c** (refactoring). **T019 is a transitive dependency via T020a**. **Must run after T020a and T034c**.
 - **Note**: T019 (binned accuracy) is NOT a direct dependency for the core grid search, but T020b cannot run until T020a is complete, and T020a depends on T019. **T023 is removed; this task produces the final JSON.**

- [X] T022 [S] [US2] **Continuous Visualization & Raw Data Generation**: Implement `code/analysis/visualize_continuous.py` to:
 - **Input**: `data/processed/annotated_videokr.csv` (T013 output) AND `data/processed/accuracy_binned.csv` (from T019).
 - **Logic**:
 1. **Raw CSV Generation**: Read the annotated CSV, group by `chain_length`, calculate mean accuracy and count per hop. Write this to `data/processed/accuracy_vs_hop_raw.csv`. (FR-005, SC-003)
 2. **Continuous Plot**: Generate a scatter plot of individual data points (accuracy vs. hop count) and overlay a **LOESS smooth trend line** (using `scipy.stats.lowess` or `statsmodels`). Save as `data/processed/accuracy_vs_hop_raw.png`. (FR-005)
 3. **Binned Plot**: Generate a bar plot of accuracy vs. hop bin (1, 2, 3+) using the data from T019/T020a. Save as `data/processed/accuracy_binned.png`. (FR-003)
 - **Output**: `data/processed/accuracy_vs_hop_raw.csv`, `data/processed/accuracy_vs_hop_raw.png`, `data/processed/accuracy_binned.png`.
 - **Depends on T013** and **T019**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis of Threshold Definition (Priority: P3)

**Goal**: Verify robustness of the "cliff" by sweeping thresholds (multiple hops) and visualizing stability.

**Independent Test**: Change threshold config parameter; verify output report shows variation in p-values and effect sizes.

### Tests for User Story 3 (MANDATORY)

- [X] T024 [P] [US3] Unit test for sensitivity sweep logic in `tests/unit/test_sensitivity.py`

### Implementation for User Story 3

- [X] T034d [S] [US3] **Refactor Scripts to Library (US3)**: Refactor `code/analysis/sensitivity.py` (T025) to expose a `run()` function. **Constraint**: Remove `if __name__ == '__main__':` execution logic; the module must be importable by T035. The `run()` function must accept a `config` object and return a status code. **Verification**: Import the module in a test script and call `run()` to verify it executes without `__main__` block interference. **Verification**: Create `tests/unit/test_refactored_us3.py` that imports `code/analysis/sensitivity.py` and calls `run()` with a mock config, verifying it returns a status code without side effects. **Dependency**: Must run after T025 implementation.
- [X] T025 [S] [US3] **Sensitivity Analysis Implementation & Final Outputs**: Implement `code/analysis/sensitivity.py` to:
 - **Input**: Use **existing `chain_length` values from `data/processed/annotated_videokr.csv` (T013 output)** and **`threshold_results.json` from T020b**.
 - **Constraint**: **DO NOT re-sample** or re-annotate. The structural chain length is immutable.
 - **Action**: Re-bin the existing data for each threshold iteration across multiple hop counts.
 - **Logic**: **Import and reuse the threshold detection logic (grid-search, permutation test) from `code/analysis/detect_threshold.py` functions** (stable, tested functions from T020b implementation) to ensure consistency. **Note**: This reuses the Permutation Test implementation (Plan override) from T020b, not the Spec's original LRT. Do not re-implement. **Code Dependency**: Requires T020b to be completed. **Execution**: Runs in **sequential** order after Phase 4 completion. **Dependency**: **Must run after T034c** (Refactor US2-Threshold) and **T034d** (Refactor US3) to ensure functions are importable.
 - **Threshold Definitions**: Read threshold values from `config.sensitivity_thresholds` (defined in T004). **Default**: `[2, 3, 4]`. **Constraint**: Do not hard-code values; use the config key.
 - **Intermediate Output**: **Explicitly write** `data/processed/sensitivity_intermediate.json` containing a list of results for each threshold: `{'threshold_hop': int, 'p_value': float, 'effect_size': float, 'is_significant': bool}`.
 - **Final Output**:
 1. **Comparison Table**: Generate `data/processed/sensitivity_thresholds.csv` with columns: `threshold_hop`, `p_value`, `effect_size`, `is_significant`. (FR-005)
 2. **Summary Report**: Generate `data/processed/sensitivity_summary.md` interpreting the table, including a 'Robustness Conclusion' section. If T020a flagged any merged/deferred bins, include a "Limitations" section. (SC-003)
 3. **Overlay Plot**: Create `data/processed/sensitivity_overlay.png` overlaying accuracy curves for different threshold definitions (2, 3, 4 hops). (FR-005)
 4. **Stability Metric**: Calculate the count of significant thresholds (p < 0.05). If count >= 2, set `robustness_status` to 'PASS', else 'FAIL'. Write to `data/processed/stability_metric.json`. (SC-003)
 - **Output**: `data/processed/sensitivity_intermediate.json`, `data/processed/sensitivity_thresholds.csv`, `data/processed/sensitivity_summary.md`, `data/processed/sensitivity_overlay.png`, `data/processed/stability_metric.json`.
 - **Depends on T020b** (for initial results and logic reuse), **T013**, **T034c**, and **T034d**. **Must run after T020b and T034d**.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish, Execution & Reporting

**Goal**: Finalize reporting, documentation, runtime measurement, and orchestration.

- [X] T031c [P] **Generate mypy.ini**: Create `mypy.ini` in the project root with `ignore_missing_imports = True` and `disable_error_code = import-untyped` to handle external dependencies (`pyyaml`, `requests`, `sentence-transformers`) that lack complete stubs. **Verification**: Run `mypy --config-file=mypy.ini code/` and verify it passes without failing on external imports. **Output**: `mypy.ini`.
- [X] T031a [P] **Linting (Strict)**: Run `ruff check code/`. **Verification**: If `ruff` returns a non-zero exit code (including style warnings or missing docstrings), the pipeline **MUST FAIL immediately**. This is a hard block for the 'Polish' phase. **Output**: **Write `data/processed/lint_log.txt` containing the full ruff output regardless of exit code**. If exit code != 0, the orchestrator halts. **Dependency**: Must run after completion of **Phase 5** and **T034d**. The pipeline cannot be marked as successful if this task fails.
- [X] T031b [P] **Type Checking (Strict)**: Run `mypy` using the configuration generated in **T031c**. **Verification**: If `mypy` returns a non-zero exit code **for project code** (excluding missing import errors handled by T031c config), the pipeline **MUST FAIL immediately**. This is a hard block for the 'Polish' phase. **Output**: **Capture stdout/stderr to `data/processed/type_log.txt` unconditionally; if exit code != 0, raise an error to halt the pipeline**. **Dependency**: Must run after completion of **Phase 5**, **T034d**, and **T031c**. The pipeline cannot be marked as successful if this task fails.
- [X] T029 [P] [US3] **Documentation updates in `specs/001-video-reasoning-threshold/`**:
 - Update `quickstart.md` (located at `specs/001-video-reasoning-threshold/quickstart.md`) to include:
 1. **Usage Section**: Instructions on how to run `code/main.py` end-to-end.
 2. **Data Requirements**: List of required datasets (VideoKR-SFT, Knowledge Graph) and their sources.
 3. **Output Artifacts**: List of all generated files: `data/processed/annotated_videokr.csv`, `data/processed/accuracy_binned.png`, `data/processed/accuracy_vs_hop_raw.png`, `data/processed/threshold_results.json`, `data/processed/sensitivity_summary.md`, `data/processed/stability_metric.json`, `data/processed/runtime_log.json`, `data/processed/memory_log.json`.
 - Ensure usage instructions are clear and reproducible.
 - Ensure `quickstart.md` exists and is up-to-date.
- [X] T033 Run `quickstart.md` validation to ensure reproducibility
- [X] T035 [S] **Orchestrator Entry Point**: Implement `code/main.py` as the **single entry point** that wraps the execution of the entire pipeline.
 - **Logic**: This task is the **driver**. It must:
 1. Start a timer and memory monitor (`tracemalloc`) at the very beginning.
 2. **Pre-Execution Memory Check**: Verify initial memory usage is within limits. If > 6GB, raise `MemoryLimitError` immediately.
 3. **Invoke T013, T019, T020a, T020b, T022, T025 as sub-routines (Python function calls)**, importing the `run()` functions refactored in T034a, T034b, T034c, and T034d.
 4. **Error Handling**: Wrap the execution of analysis tasks (T013-T025) in a `try/except` block.
 - **Critical Constraint**: If a `MemoryLimitError` or `BinPowerError` is raised, **log the error to `data/processed/error_log.txt`** and **exit immediately with code 1**. **Do NOT continue to the next task**. The task MUST include a **Watchdog Mechanism** (e.g., a signal handler or external shell wrapper) that catches OOM kills or memory limit breaches and writes `memory_log.json` with `limit_exceeded=true` before the process terminates.
 - **Constraint**: If `pipeline_success` is false (due to OOM or error), **delete or rename partial artifacts** (e.g., `threshold_results.json.invalid`) to ensure they are not treated as reproducible results. Set `pipeline_success=false` in logs.
 5. Stops the timer and memory monitor at the end.
 6. Writes `data/processed/runtime_log.json` with `total_runtime_seconds`, `limit_exceeded` (boolean), `peak_memory_gb`, `pipeline_success` (boolean), and `error_count`.
 7. Writes `data/processed/memory_log.json` with `peak_memory_gb` and `limit_exceeded`.
 - **Constraint**: This task **MUST** wrap the execution of all previous phases to satisfy SC-004 (End-to-end runtime) and SC-005 (Peak memory). It is **NOT** a post-hoc check. It **MUST** produce logs even if the analysis pipeline fails.
 - **Dependency**: This task **depends on** T034a, T034b, T034c, T034d, and **Phase 5 completion**.
 - **Output**: `data/processed/runtime_log.json`, `data/processed/memory_log.json`, `data/processed/error_log.txt` (if errors occur).
- [X] T037 [S] **Final Report Aggregation**: Implement `code/analysis/generate_final_report.py` to:
 - **Input**: Aggregate all outputs from US1 (T013b, T016), US2 (T020b, T022, T022c), US3 (T025), and logs (T035).
 - **Action**: Combine these into a single Markdown file `data/processed/final_report.md`.
 - **Output**: Write `data/processed/final_report.md`.
 - **Depends on**: Completion of Phase 5 and T035.
- [X] T038 [S] [US3] **Generate Final Report Narrative**: Implement `code/analysis/generate_narrative.py` to:
 - **Input**: `data/processed/threshold_results.json`, `data/processed/stability_metric.json`, `data/processed/sensitivity_summary.md`.
 - **Action**: Synthesize a human-readable narrative interpreting the "reasoning cliff" findings, discussing limitations (e.g., bin merging), and stating the final conclusion. **Constraint**: The narrative must be strictly derived from the JSON outputs; no hand-typed statistics.
 - **Output**: Append the narrative to `data/processed/final_report.md` (or create a separate `data/processed/narrative.md` if preferred).
 - **Depends on**: T025 and T037.

---

## Phase 7: Revision & Compliance (Addressing Analysis Findings)

**Goal**: This phase is reserved for future analysis-driven revisions.

- [X] T070 [S] **Validate Removal of T050/T051**: Implement a script `code/utils/validate_removal.py` that scans the codebase and `data/processed/` directory to verify that **no artifacts** (plots, logs, JSONs) related to the removed T050/T051 (GAM/Compliance scans) exist. **Output**: Write `data/processed/removal_validation.json` with `status: "PASS"` if no artifacts are found, or `status: "FAIL"` if artifacts exist. **Constraint**: This task explicitly validates the "Removed" status of T050/T051 to satisfy the "REDO" instruction without violating the removal constraint. **Dependency**: Must run after Phase 6 completion.

**Constraint**: The implementer should not attempt to produce artifacts for T050 or T051 as these requirements are explicitly deleted from the specification. The "Phase 7" gate validates that no contradictory requirements exist (i.e., it checks that the code does NOT produce artifacts for T050/T051), rather than requiring their execution. Do not attempt to produce artifacts for removed tasks. If new analysis findings arise, new tasks will be added here.

---

## Phase 8: Analysis-Driven Revisions (Pending)

**Goal**: Address specific findings from `/speckit.analyze` that require code or spec changes.

- [ ] **T080 [P] [Analysis] Resolve T050/T051 Contradiction**: **Action**: Verify that T070 correctly validates the absence of T050/T051 artifacts and that the "REDO" instruction is satisfied by this validation. If T070 fails, update the specification to clarify the removal or re-implement the validation logic. **Dependency**: Depends on T070 completion.
- [ ] **T081 [P] [Analysis] Resolve T031b Log Logic**: **Action**: Verify that T031b correctly writes `type_log.txt` unconditionally even on failure. If the log is missing in failure cases, modify T031b to enforce unconditional writing. **Dependency**: Depends on T031b completion.
- [ ] **T082 [P] [Analysis] Resolve T034 Dependency Gap**: **Action**: Verify that T025 can successfully import the `run()` function from T020b (refactored in T034c). If import fails, update T034c or T025 to resolve the dependency. **Dependency**: Depends on T034c and T025 completion.

**Constraint**: Do not invent tasks in this phase. Only add tasks that directly resolve a specific `issue_id` from the `analyze_report`.