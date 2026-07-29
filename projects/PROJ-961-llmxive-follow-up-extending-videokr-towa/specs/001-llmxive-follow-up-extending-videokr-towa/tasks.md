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

- [ ] T001 [P] **Initialize Project Structure**: Create all required directories (`code/`, `tests/`, `data/`, `data/raw/`, `data/processed/`, `code/ingest/`, `code/analysis/`, `code/utils/`, `tests/unit/`, `tests/integration/`) and `.gitkeep` files in a single script execution. **Verification**: Script must verify all directories exist using `os.path.exists` and raise an error if creation fails.

---

## Phase 2: Foundational (Blocking Prerequisites & Utils)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **T035 is moved to Phase 6.**

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 [P] Implement `code/utils/config.py` for seed management and path configuration.
- [X] T005 [P] Implement `code/utils/versioning.py` to write SHA-256 hashes of data artifacts (Constitution Principle V).
- [X] T006 [P] Create `code/utils/graph_utils.py` with shortest path logic (BFS) handling disconnected graphs.
- [X] T007 [P] Create `code/utils/entity_linker.py` for mapping question entities to graph nodes (fuzzy/embedding based). **Conditional Logic**: The script must first check if the input dataset already contains a `node_id` or `entity_id` column. If present, it MUST skip the linking process and use the provided IDs. If absent, it MUST implement the fuzzy/embedding linking logic. This satisfies FR-001 without assuming a specific data source structure.
- [X] T009 [P] Implement `code/ingest/checksum.py` as a utility script to be invoked by T013 for verifying raw data integrity (Constitution Principle III).
- [X] T034 [S] **Refactor Scripts to Library**: Refactor `code/ingest/annotate_graph.py` (T013), `code/analysis/stratify_accuracy.py` (T019), `code/analysis/bin_utils.py` (T020a), `code/analysis/detect_threshold.py` (T020b), `code/analysis/visualize_continuous.py` (T022), and `code/analysis/sensitivity.py` (T025) to expose a `run()` function in each module. **Constraint**: Remove `if __name__ == '__main__':` execution logic from these modules; instead, they must be importable by T035. The `run()` function must accept a `config` object and return a status code. **Verification**: Import each module in a test script and call `run()` to verify it executes without `__main__` block interference.

---

## Phase 3: User Story 1 - Data Ingestion and Structural Annotation (Priority: P1) 🎯 MVP

**Goal**: Download VideoKR-SFT, annotate questions with structural chain length (hops) from the ground-truth graph. **Includes mandatory streaming and verification logic.**

**Independent Test**: Run the annotation script on a small, manually verified subset; confirm `chain_length` matches manual graph traversal for a representative sample of random records.

### Tests for User Story 1 (MANDATORY)

- [X] T010 [S] [US1] Unit test for `graph_utils.py` shortest path logic in `tests/unit/test_graph_utils.py` (handles disconnected nodes, shortest path rule). **Depends on T006 completion.**
- [X] T011 [S] [US1] Integration test for `annotate_graph.py` on a sample subset in `tests/integration/test_pipeline.py` **Depends on T006, T007, T009 completion.**

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/ingest/download_data.py` to fetch VideoKR-SFT and Knowledge Graph from verified URLs (NAB/UCI/arXiv) with checksumming, invoking T009 for verification.
- [X] T040 [S] [US1] **Explicit Data Source Verification**: Implement a strict check in `code/ingest/download_data.py` that verifies the existence of the **exact** VideoKR-SFT URL and Knowledge Graph source before attempting download. If the primary source is unreachable, **raise a `DataUnavailableError`** immediately. **Do not** implement any fallback to synthetic/mock data. Log the exact URL and checksum of the source used. **Dependency**: Must run before T013.
- [X] T013 [S] [US1] **Implementation (Producer) with Streaming & Oversampling**: Implement `code/ingest/annotate_graph.py` to:
 - **Unified Streaming & Sampling Strategy**: Implement a strict **Pilot -> Oversample** process as mandated by the Plan, using streaming for the pilot fetch:
 1. **Pilot Phase**: Run a pilot sample of exactly **1000 rows** using `datasets.load_dataset(name, split=..., streaming=True)` and `itertools.islice` to estimate the distribution of `chain_length`. **Seed**: MUST use `config.get_seed('pilot_sampling')`.
 2. **Oversampling Check**: If any bin (especially '3+') has **<50 samples** in the pilot, trigger an **Oversampling** step.
 3. **Oversampling Logic**: Use stratified resampling (with replacement) on the **pilot subset** (which fits in memory) to reach N>=50 for rare bins. **Explicitly preserve the distribution of hop counts**. **Seed**: MUST use `config.get_seed('oversampling')`.
 4. **Logging**: Log the sampling method, pilot size (1000), oversampling target, and final sample size to `data/processed/sampling_log.json`.
 - **Chunked Processing**: Implement chunked streaming (e.g., `pandas.read_csv(chunksize=...)`) to process the dataset in memory-safe batches if full load is not feasible.
 - **Self-Healing Regeneration Logic**: If the output file `data/processed/annotated_videokr.csv` is empty, missing, or has <50 rows after the initial run, **re-run** the full annotation pipeline with adjusted parameters (pilot size doubled, max 2 retries). If 2 retries fail, raise a `DataUnavailableError`. **DO NOT** rely on a separate task to regenerate. This task MUST guarantee the artifact exists or raises a clear error.
 - **Map entities**: Map question entities to graph nodes using `entity_linker.py`. **Conditional**: If `entity_linker.py` detects pre-existing node IDs (per T007), use them directly. Otherwise, perform linking.
 - **Input**: `question` text column.
 - **Output**: `entity_node_id` (string) and `confidence` (float).
 - **Handling**: If `confidence < threshold`, mark as `unmapped` and log.
 - **Calculate Exact Hops**: Calculate the **exact integer** shortest path hops (1, 2, 3, 4, 5...) for each record. Output this as the column `chain_length` (integer type).
 - **Algorithm**: Use BFS (Breadth-First Search) for unweighted graphs. If weighted, use Dijkstra.
 - **Tie-Breaking**: If multiple shortest paths exist, use the one with the lexicographically smallest node sequence.
 - **Generate Binned Column**: Derive a second column `chain_bin` (categorical: '1', '2', '3+') from `chain_length` to satisfy FR-002's requirement for binned categories.
 - **Handle Disconnected**: Exclude or label 'unresolvable' for disconnected graphs.
 - **Enforce Shortest Path**: Use the shortest path rule for multiple paths.
 - **Preserve Correctness**: **Explicitly copy** the `correctness` column from the source VideoKR-SFT dataset to the output CSV. (FR-001, Data Model)
 - **Write Output**: **Explicitly write** the final artifact `data/processed/annotated_videokr.csv` with columns: `id`, `question`, `answer`, `chain_length` (integer), `chain_bin` (categorical), `correctness`. (FR-001, FR-002, SC-001)
 - **Note**: This task is strictly the **producer**. Verification of row counts and coverage is handled by T013b.
- [X] T013b [S] [US1] **Verification (Validator)**: Verify the output of T013.
 - **Input**: `data/processed/annotated_videokr.csv` (produced by T013).
 - **Logic**: Verify that the row count matches the input (excluding unmapped/unresolvable). Log `total_input_records` (count BEFORE any exclusion), `unresolvable_count`, and `annotated_count`.
 - **Output**: Write `data/processed/annotation_coverage.json` with the counts and `proportion = annotated_count / total_input_records`. (SC-001)
 - **Constraint**: If `annotated_videokr.csv` is missing, this task **FAILS** and reports the error to the orchestrator (T035). It does NOT attempt to regenerate (that is T013's self-healing logic).
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
 - **Bin Size Check**: If the '3+' bin (or any other bin) has <50 records, **raise a `BinPowerError`** immediately. This error must be caught by the orchestrator (T035) to prevent T020b from running. **Do not** just prepare a flag; the pipeline must halt or defer. (FR-003)
 - **Dependency**: **Must run after T013** to access `data/processed/annotated_videokr.csv`.
- [X] T020a [S] [US2] **Bin Preparation & Merging Logic**: Implement `code/analysis/bin_utils.py` to:
 - **Input**: Use **exact integer `chain_length` data from T013** (1, 2, 3, 4, 5...) and bin counts from T019.
 - **Logic**: Check if the highest bin (or any bin used in the test) contains a low number of samples.
 1. **Attempt Merge**: Merge the underpowered bin with the adjacent bin (e.g., 3+ with 2-hop).
 2. **Re-check**: If the merged bin has >= 50 samples, proceed with the test on the merged bin and log `bin_status: "merged"` to `data/processed/bin_status.json`.
 3. **Defer**: If the merged bin still has < 50 samples, **defer** the statistical test for this comparison. Write `status: "deferred"`, `reason: "insufficient_power"`, and `bin_status: "deferred"` to the JSON file. **Do not** fabricate data, merge blindly, or force a test.
 - **Output**: Write a JSON file `data/processed/bin_config.json` containing `{'bins': [...], 'strategy': 'merged' | 'deferred'}`. This defines the **final static binning strategy** to be used by T020b.
 - **Depends on T013** (raw data) and **T019** (bin counts). **Must run after T019**.
- [X] T042 [S] [US2] **Permutation Test Reproducibility Check**: Implement a distinct validation step in `code/analysis/detect_threshold.py` (T020b) that runs the permutation test twice with the same seed and verifies the p-values match exactly. **Constraint**: If results differ, raise a `ReproducibilityError`. **Verification**: Log the comparison to `data/processed/reproducibility_check.json`. **Dependency**: Must be integrated into T020b execution flow, but executed as a pre-check before the main T020b logic runs. **Must run after T020a**.
- [X] T020b [S] [US2] **Threshold Detection (Permutation Test) & Final Output**: Implement `code/analysis/detect_threshold.py` to:
 - **Input**: Use **exact integer `chain_length` data from T013** and the **static binning strategy from T020a** (`data/processed/bin_config.json`).
 - **Methodology**: **Per Plan Complexity Tracking table**, use a **Permutation Test** (n=1000) for change-point detection to avoid inflated Type I errors from data-driven knot selection. **Note**: This overrides Spec FR-004's LRT requirement based on the Plan's explicit rejection of LRT for data-driven knot selection. **Cite Plan.md 'Complexity Tracking' table** as the authority for this deviation.
 - **Grid-Search Logic**: Iterate knot locations from **1 to 5** (fixed range per Spec FR-004). For each knot:
 1. Fit a linear model (accuracy ~ hop_count).
 2. Fit a piecewise linear model (accuracy ~ hop_count + max(0, hop_count - knot)).
 3. **Permutation Engine**: Perform the permutation test by **randomly shuffling the `correctness` labels** (n=1000 times) and recalculating the test statistic for each shuffle to build the null distribution. **DO NOT** rely on asymptotic approximations.
 4. **Test Statistic Definition**: The test statistic is the **Difference in Residual Sum of Squares (RSS)** between the linear model and the piecewise linear model.
 5. Calculate the p-value as the proportion of permuted statistics >= observed statistic.
 - **Correction**: Apply **Bonferroni correction** for the number of tests performed (p_corrected = p_raw * num_tests).
 - **Selection**: Select the knot location with the minimum corrected p-value.
 - **Power Analysis**: If total sample size < 1000 or smallest bin < 50, log a warning to `data/processed/power_analysis.json` stating 'Insufficient power for robust inference' (do not attempt calculation without parameters). **Note**: The Permutation Test inherently handles power via empirical distribution; no separate parametric power analysis task (T041) is required or implemented.
 - **Output**: Identify the optimal knot and report the corrected p-value. (FR-004)
 - **Final Artifact**: **Explicitly write** `data/processed/threshold_results.json` with the following schema: `p_value` (float), `alpha` (0.05), `is_significant` (boolean), `conclusion` (string), `optimal_knot` (int). (SC-002)
 - **Depends on T013** (raw data), **T006** (graph utils), **T020a** (static binning), and **T042** (reproducibility). **T019 is a transitive dependency via T020a**. **Must run after T020a**.
 - **Note**: T019 (binned accuracy) is NOT a direct dependency for the core grid search, but T020b cannot run until T020a is complete, and T020a requires T019. **T023 is removed; this task produces the final JSON.**
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

- [X] T025 [S] [US3] **Sensitivity Analysis Implementation & Final Outputs**: Implement `code/analysis/sensitivity.py` to:
 - **Input**: Use **existing `chain_length` values from `data/processed/annotated_videokr.csv` (T013 output)** and **`threshold_results.json` from T020b**.
 - **Constraint**: **DO NOT re-sample** or re-annotate. The structural chain length is immutable.
 - **Action**: Re-bin the existing data for each threshold iteration across multiple hop counts.
 - **Logic**: **Import and reuse the threshold detection logic (grid-search, permutation test) from `code/analysis/detect_threshold.py` functions** (stable, tested functions from T020b implementation) to ensure consistency. **Note**: This reuses the Permutation Test implementation (Plan override) from T020b, not the Spec's original LRT. Do not re-implement. **Code Dependency**: Requires T020b to be completed. **Execution**: Runs in **sequential** order after Phase 4 completion.
 - **Threshold Definitions**: Explicitly sweep thresholds for **2, 3, and 4 hops** to satisfy SC-003's requirement for "3 threshold definitions".
 - **Intermediate Output**: **Explicitly write** `data/processed/sensitivity_intermediate.json` containing a list of results for each threshold: `{'threshold_hop': int, 'p_value': float, 'effect_size': float, 'is_significant': bool}`.
 - **Final Output**:
 1. **Comparison Table**: Generate `data/processed/sensitivity_thresholds.csv` with columns: `threshold_hop`, `p_value`, `effect_size`, `is_significant`. (FR-005)
 2. **Summary Report**: Generate `data/processed/sensitivity_summary.md` interpreting the table, including a 'Robustness Conclusion' section. If T020a flagged any merged/deferred bins, include a "Limitations" section. (SC-003)
 3. **Overlay Plot**: Create `data/processed/sensitivity_overlay.png` overlaying accuracy curves for different threshold definitions (2, 3, 4 hops). (FR-005)
 4. **Stability Metric**: Calculate the count of significant thresholds (p < 0.05). If count >= 2, set `robustness_status` to 'PASS', else 'FAIL'. Write to `data/processed/stability_metric.json`. (SC-003)
 - **Output**: `data/processed/sensitivity_intermediate.json`, `data/processed/sensitivity_thresholds.csv`, `data/processed/sensitivity_summary.md`, `data/processed/sensitivity_overlay.png`, `data/processed/stability_metric.json`.
 - **Depends on T020b** (for initial results and logic reuse) and **T013**. **Must run after T020b**.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish, Execution & Reporting

**Goal**: Finalize reporting, documentation, runtime measurement, and orchestration.

- [ ] T031a [P] Remove unused imports from all scripts in `code/`. **Verification**: Run `ruff check code/`. **Fail if exit code != 0**. Log output to `data/processed/lint_log.txt`.
- [ ] T031b [P] Add type hints to all public functions in `code/`. **Verification**: Run `mypy code/`. **Fail if exit code != 0**. Log output to `data/processed/type_log.txt`.
- [ ] T031c1 [P] **Docstring Linting**: Run `pydocstyle code/` (excluding `tests/` and `__init__.py`). **Fail if exit code != 0**. Log output to `data/processed/docstring_log.txt`.
- [ ] T031c2 [P] **Docstring Coverage**: Ensure all public functions in `code/` have docstrings. **Verification**: Run `pydocstyle --count` and ensure coverage > 90%.
- [X] T029 [P] [US3] **Documentation updates in `specs/001-video-reasoning-threshold/`**:
 - Update `quickstart.md` (located at `specs/001-video-reasoning-threshold/quickstart.md`) to include:
 1. **Usage Section**: Instructions on how to run `code/main.py` end-to-end.
 2. **Data Requirements**: List of required datasets (VideoKR-SFT, Knowledge Graph) and their sources.
 3. **Output Artifacts**: List of all generated files: `data/processed/annotated_videokr.csv`, `data/processed/accuracy_binned.png`, `data/processed/accuracy_vs_hop_raw.png`, `data/processed/threshold_results.json`, `data/processed/sensitivity_summary.md`, `data/processed/stability_metric.json`, `data/processed/runtime_log.json`, `data/processed/memory_log.json`, `data/processed/sensitivity_thresholds.csv`.
 - Ensure usage instructions are clear and reproducible.
 - Ensure `quickstart.md` exists and is up-to-date.
- [X] T033 Run `quickstart.md` validation to ensure reproducibility
- [X] T035 [S] **Orchestrator Entry Point**: Implement `code/main.py` as the **single entry point** that wraps the execution of the entire pipeline.
 - **Logic**: This task is the **driver**. It must:
 1. Start a timer and memory monitor (`tracemalloc`) at the very beginning.
 2. **Pre-Execution Memory Check**: Verify initial memory usage is within limits. If > 6GB, raise `MemoryLimitError` immediately.
 3. **Invoke T013, T019, T020a, T020b, T022, T025 as sub-routines (Python function calls)**, importing the `run()` functions refactored in T034.
 4. **Error Handling**: Wrap the execution of analysis tasks (T013-T025) in a `try/except` block.
 - **Critical Constraint**: If a `MemoryLimitError` or `BinPowerError` is raised, **log the error to `data/processed/error_log.txt`** and **exit immediately with code 1**. **Do NOT continue to the next task**. The task MUST include a **Watchdog Mechanism** (e.g., a signal handler or external shell wrapper) that catches OOM kills or memory limit breaches and writes `memory_log.json` with `limit_exceeded=true` before the process terminates.
 - For non-fatal logic errors, log the error and continue if possible.
 5. Stops the timer and memory monitor at the end.
 6. Writes `data/processed/runtime_log.json` with `total_runtime_seconds`, `limit_exceeded` (boolean), `peak_memory_gb`, `pipeline_success` (boolean), and `error_count`.
 7. Writes `data/processed/memory_log.json` with `peak_memory_gb` and `limit_exceeded`.
 - **Constraint**: This task **MUST** wrap the execution of all previous phases to satisfy SC-004 (End-to-end runtime) and SC-005 (Peak memory). It is **NOT** a post-hoc check. It **MUST** produce logs even if the analysis pipeline fails.
 - **Dependency**: This task **depends on** T034 (Refactor Scripts to Library) and **Phase 5 completion**.
 - **Output**: `data/processed/runtime_log.json`, `data/processed/memory_log.json`, `data/processed/error_log.txt` (if errors occur).
- [X] T037 [S] **Final Report Aggregation**: Implement `code/analysis/generate_final_report.py` to:
 - **Input**: Aggregate all outputs from US1 (T013b, T016), US2 (T020b, T022, T022c), US3 (T025), and logs (T035).
 - **Action**: Combine these into a single Markdown file `data/processed/final_report.md`.
 - **Output**: Write `data/processed/final_report.md`.
 - **Depends on**: Completion of Phase 5 and T035.

---

## Phase 7: Revision & Compliance (Addressing Analysis Findings)

**Goal**: No mandatory tasks remain. This phase is reserved for future analysis-driven revisions.

---

## Dependencies & Execution Order

### Execution Flow

1. **Setup (Phase 1)**: T001 (Initialize Project Structure)
2. **Foundational (Phase 2)**: T004, T005, T006, T007, T009 (Parallel) -> T034 (Refactor Scripts)
3. **User Stories (Phase 3-5)**:
   - **US1 (T012, T040, T013, T013b, T016)**: Runs first (data ingestion).
   - **US2 (T019, T020a, T042, T020b, T022)**: Runs after US1 (T019 depends on T013; T020a depends on T019; T020b depends on T020a).
   - **US3 (T025)**: Runs after US2 (depends on T020b).
4. **Polish & Execution (Phase 6)**: T031a-c, T029, T033, T035 (Orchestrator), T037 (Report).
5. **Revision (Phase 7)**: Reserved.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (annotated data)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 logic and data (T013, T019, **T020b**, **T025**)
- **Polish (Phase 6)**: Depends on completion of Phase 5.
- **Revision (Phase 7)**: Reserved.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation. **Tests are part of the 'Implementation' block for the story.**
- Models/Utils before Services
- Services before Endpoints/Analysis scripts
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- **Note**: T035 (Orchestrator Logger) is **NOT** parallel-safe and must run last, after T028. However, it **starts** at the beginning of the pipeline execution, not after Phase 5 completion.
- **Revision Tasks**: Reserved.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for graph_utils.py shortest path logic in tests/unit/test_graph_utils.py"
Task: "Integration test for annotate_graph.py on a sample subset in tests/integration/test_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement code/ingest/download_data.py"
Task: "Implement code/utils/entity_linker.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
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
- [S] tasks = Sequential (must run in order)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Constraint**: All tasks must run on CPU-only CI (limited cores, limited RAM, h limit). No GPU, no low-bit models, no large LLMs.
- **Data Integrity**: No fake data. All datasets must be fetched from real, verified sources.
- **Dual-Method Analysis**: Non-linearity is tested via Permutation Test (T020b, discrete) only. GAMs (FR-007) are explicitly rejected by the Plan's 'Complexity Tracking' table as statistically invalid for discrete ordinal variables; T034 removed.
- **Orchestrator**: T035 is the **only** task that executes the pipeline. T013-T025 are functions called by T035.
- **Revision Compliance**: Phase 7 tasks (T040, T041, T042) have been moved to their correct phases (3, 4) to resolve logical contradictions and ensure core logic is validated before execution.