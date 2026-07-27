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

- [ ] T001a [P] Create `code/`, `tests/`, and `data/` directories at repository root
- [ ] T001b [P] Create `code/ingest/`, `code/analysis/`, `code/utils/` subdirectories
- [ ] T001c [P] Create `tests/unit/` and `tests/integration/` subdirectories
- [ ] T008a [P] Create `.gitkeep` in `data/raw/` directory
- [ ] T008b [P] Create `.gitkeep` in `data/processed/` directory

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `code/utils/config.py` for seed management and path configuration
- [ ] T005 [P] Implement `code/utils/versioning.py` to write SHA-256 hashes of data artifacts (Constitution Principle V)
- [ ] T006 [P] Create `code/utils/graph_utils.py` with shortest path logic (BFS) handling disconnected graphs
- [ ] T007 [P] Create `code/utils/entity_linker.py` for mapping question entities to graph nodes (fuzzy/embedding based)
- [ ] T009 [P] Implement `code/ingest/checksum.py` as a utility script to be invoked by T012 for verifying raw data integrity (Constitution Principle III)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Structural Annotation (Priority: P1) 🎯 MVP

**Goal**: Download VideoKR-SFT, annotate questions with structural chain length (hops) from the ground-truth graph.

**Independent Test**: Run the annotation script on a small, manually verified subset; confirm `chain_length` matches manual graph traversal for a representative sample of random records.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation. These are part of the 'Implementation' block for US1.**

- [ ] T010 [US1] Unit test for `graph_utils.py` shortest path logic in `tests/unit/test_graph_utils.py` (handles disconnected nodes, shortest path rule). **Depends on T006 completion.**
- [ ] T011 [US1] Integration test for `annotate_graph.py` on a sample subset in `tests/integration/test_pipeline.py`

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `code/ingest/download_data.py` to fetch VideoKR-SFT and Knowledge Graph from verified URLs (NAB/UCI/arXiv) with checksumming, invoking T009 for verification.
- [ ] T013 [P] [US1] **Implementation (Producer)**: Implement `code/ingest/annotate_graph.py` to:
 - **Two-Stage Sampling Strategy**: Implement a strict **Pilot -> Oversample** process as mandated by the Plan:
 1. **Pilot Phase**: Run a pilot sample (e.g., [deferred] or 1000 rows) using `datasets.load_dataset(name, split=..., streaming=True)` and `itertools.islice` to estimate the distribution of `chain_length`.
  2. **Oversampling Check**: If any bin (especially '3+') has <50 samples in the pilot, trigger an **Oversampling** step.
  3. **Oversampling Logic**: Use `sklearn.model_selection.train_test_split` with `strata=chain_length` on the full dataset (if loadable) or continue streaming with `islice` until the target N>=50 for the rare bin is reached. **Explicitly preserve the distribution of hop counts**.
  4. **Logging**: Log the sampling method, pilot size, oversampling target, and final sample size.
 - **Chunked Processing**: Implement chunked streaming (e.g., `pandas.read_csv(chunksize=...)`) to process the dataset in memory-safe batches if full load is not feasible.
 - **Fallback Sampling**: If the full dataset cannot be processed within 7GB RAM (detected via memory monitoring) or pilot phase indicates >6h runtime, **MUST** fall back to the **Two-Stage Sampling** (Pilot -> Oversample) described above. **DO NOT** use generic `islice` without ensuring statistical power. Log the sampling method and size.
 - **Map entities**: Map question entities to graph nodes using `entity_linker.py`.
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
- [ ] T013b [S] [US1] **Verification (Validator)**: Verify the output of T013.
 - **Input**: `data/processed/annotated_videokr.csv` (produced by T013).
 - **Logic**: Verify that the row count matches the input (excluding unmapped/unresolvable). Log `total_input_records` (count BEFORE any exclusion), `unresolvable_count`, and `annotated_count`.
 - **Output**: Write `data/processed/annotation_coverage.json` with the counts and `proportion = annotated_count / total_input_records`. (SC-001)
 - **Depends on**: T013 completion.
- [ ] T015 [US1] **Coverage Log**: (Merged into T013b logic, but kept for traceability) Calculate and log the proportion of questions successfully annotated to `data/processed/annotation_coverage.json`. **Logic**: `proportion = annotated_count / total_input_records`. **Mandatory**: Explicitly log `total_input_records` (count BEFORE any exclusion), `unresolvable_count`, and `annotated_count` as separate fields in the JSON to enable independent verification of SC-001. (SC-001)
- [ ] T016 [US1] Write hash of `annotated_videokr.csv` to `state/projects/PROJ-961-llmxive-follow-up-extending-videokr-towa.yaml`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Accuracy Stratification and Threshold Detection (Priority: P2)

**Goal**: Calculate accuracy per hop-bin, detect non-linear "reasoning cliff" using Permutation Test (per Plan override).

**Independent Test**: Generate accuracy vs. hop plot and statistical report; verify trend and p-value against raw data summary.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T017 [P] [US2] Unit test for accuracy calculation logic in `tests/unit/test_stratify_accuracy.py`
- [ ] T018 [P] [US2] Integration test for `detect_threshold.py` on annotated data in `tests/integration/test_pipeline.py`

### Implementation for User Story 2

- [ ] T019 [P] [US2] Implement `code/analysis/stratify_accuracy.py` to:
 - Calculate accuracy rate for bins 1-hop, 2-hop, 3+ hops (aggregating 3, 4, 5... into '3+' for the primary report as per Spec US-2).
 - **Bin Size Check**: If the '3+' bin (or any other bin) has <50 records, prepare a flag for T020a. (FR-003)
- [ ] T020a [S] [US2] **Bin Preparation & Merging Logic**: Implement `code/analysis/bin_utils.py` to:
 - **Input**: Use **exact integer `chain_length` data from T013** (1, 2, 3, 4, 5...) and bin counts from T019.
 - **Logic**: Check if the highest bin (or any bin used in the test) contains a low number of samples.
 1. **Attempt Merge**: Merge the underpowered bin with the adjacent bin (e.g., 3+ with 2-hop).
 2. **Re-check**: If the merged bin has >= 50 samples, proceed with the test on the merged bin and log `bin_status: "merged"` to `data/processed/bin_status.json`.
 3. **Defer**: If the merged bin still has < 50 samples, **defer** the statistical test for this comparison. Write `status: "deferred"`, `reason: "insufficient_power"`, and `bin_status: "deferred"` to the JSON file. **Do not** fabricate data, merge blindly, or force a test.
 - **Output**: A configuration object or file defining the **final static binning strategy** to be used by T020b.
 - **Depends on T013** (raw data) and **T019** (bin counts).
- [ ] T020b [P] [US2] **Threshold Detection (Permutation Test)**: Implement `code/analysis/detect_threshold.py` to:
 - **Input**: Use **exact integer `chain_length` data from T013** and the **static binning strategy from T020a**.
 - **Methodology**: **Per Plan Complexity Tracking table**, use a **Permutation Test** (n=1000) for change-point detection to avoid inflated Type I errors from data-driven knot selection. **Note**: This overrides Spec FR-004's LRT requirement based on the Plan's explicit rejection of LRT for data-driven knot selection. **Cite Plan.md 'Complexity Tracking' table** as the authority for this deviation.
 - **Grid-Search Logic**: Iterate knot locations from **1 to 5** (fixed range per Spec FR-004). For each knot:
 1. Fit a linear model (accuracy ~ hop_count).
 2. Fit a piecewise linear model (accuracy ~ hop_count + max(0, hop_count - knot)).
 3. Perform the permutation test to derive the p-value for the improvement in fit.
 - **Correction**: Apply **Bonferroni correction** for the number of tests performed (p_corrected = p_raw * num_tests).
 - **Selection**: Select the knot location with the minimum corrected p-value.
 - **Output**: Identify the optimal knot and report the corrected p-value. (FR-004)
 - **Depends on T013** (raw data), **T006** (graph utils), and **T020a** (static binning).
 - **Note**: T019 (binned accuracy) is NOT a dependency for the core grid search; T019 and T020b can run in parallel (T020b depends on T020a, not T019).
- [ ] T022a [US2] [P] **Continuous Plot Data**: Generate a **CSV file `data/processed/accuracy_vs_hop_raw.csv`** containing the raw data points and mean accuracy per hop count for the continuous plot. **Constraint**: Use **raw, un-binned data** from `data/processed/annotated_videokr.csv` (T013 output). (FR-005)
 - **Depends on T013**.
- [ ] T022b [US2] [P] **Continuous Plot Image**: Generate a **scatter plot image `data/processed/accuracy_vs_hop_raw.png`** using the data from T022a. **Constraint**: Plot **raw scatter points** AND a **LOESS smooth trend line** (or spline fit) to represent the continuous relationship between hop count and accuracy, satisfying FR-005's 'continuous plot' requirement without binning artifacts. **Write the plot to `data/processed/accuracy_vs_hop_raw.png`**. (FR-005, SC-003)
 - **Depends on T022a**.
- [ ] T022c [US2] **Binned Summary & Plot**: Generate a summary table and a **binned bar plot `data/processed/accuracy_binned.png`** of accuracy vs. hop bin using data from T019. **Depends on T019**. (FR-003)
- [ ] T023 [US2] Output `data/processed/threshold_results.json` with p-value, effect size, optimal knot location, deferral reasons (if any), and an explicit `conclusion` field (PASS/FAIL). **Logic**: Explicitly compare the calculated p-value against alpha=0.05. The JSON must include: `p_value` (float), `alpha` (0.05), `is_significant` (boolean), and `conclusion` (string). (SC-002)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis of Threshold Definition (Priority: P3)

**Goal**: Verify robustness of the "cliff" by sweeping thresholds (multiple hops) and visualizing stability.

**Independent Test**: Change threshold config parameter; verify output report shows variation in p-values and effect sizes.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Unit test for sensitivity sweep logic in `tests/unit/test_sensitivity.py`

### Implementation for User Story 3

- [ ] T025 [P] [US3] Implement `code/analysis/sensitivity.py` to:
 - **Input**: Use **existing `chain_length` values from `data/processed/annotated_videokr.csv` (T013 output)**.
 - **Constraint**: **DO NOT re-sample** or re-annotate. The structural chain length is immutable.
 - **Action**: Re-bin the existing data for each threshold iteration across multiple hop counts.
 - **Logic**: **Import and reuse the threshold detection logic (grid-search, permutation test) from `code/analysis/detect_threshold.py` functions** (stable, tested functions from T020b implementation) to ensure consistency. **Note**: This reuses the Permutation Test implementation (Plan override) from T020b, not the Spec's original LRT. Do not re-implement. **Code Dependency**: Requires T020b to be completed. **Execution**: Runs in parallel within Phase 5 once Phase 4 is complete.
 - Compare significance (p-value) and effect size (accuracy drop).
- [ ] T026a [US3] **Comparison Table**: Generate a CSV file `data/processed/sensitivity_thresholds.csv` with columns: `threshold_hop`, `p_value`, `effect_size`, `is_significant`. (FR-005)
- [ ] T026b [US3] **Summary Report**: Generate a Markdown summary `data/processed/sensitivity_summary.md` interpreting the table. (FR-005)
- [ ] T027a [US3] **Overlay Plot**: Create a plot `data/processed/sensitivity_overlay.png` overlaying accuracy curves for different threshold definitions (2, 3, 4 hops) using `matplotlib`. (FR-005)
- [ ] T028a [US3] **Comparison Table & Report**: Generate a Markdown summary `data/processed/sensitivity_report.md` interpreting the table from T026a. **Content Structure**: Must include a table of thresholds, p-values, effect sizes, and a final 'Robustness Conclusion' section stating 'Robust' (if count >= 2) or 'Not Robust' (if count < 2). **Limitations**: If T020a flagged any merged/deferred bins, this report MUST include a "Limitations" section explicitly stating the merged bin definition and the reason for deferral. (SC-003)
- [ ] T028b [US3] **Stability Metric**: Programmatically calculate and log the **count of significant thresholds** to `data/processed/stability_metric.json`. **Logic**: Count thresholds where p < 0.05; verify if count >= 2. Output a field `robustness_status` with value 'PASS' if count >= 2, else 'FAIL'. (SC-003)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish

**Goal**: Finalize reporting, documentation, and runtime measurement. (GAM Implementation removed per Plan decision).

- [ ] T031a [P] Remove unused imports from all scripts in `code/`.
- [ ] T031b [P] Add type hints to all public functions in `code/`.
- [ ] T031c [P] Ensure all scripts in `code/` have docstrings.
- [ ] T029 [P] Documentation updates in `docs/`:
 - Update `README.md` to include:
 1. **Usage Section**: Instructions on how to run `code/main.py` end-to-end.
 2. **Data Requirements**: List of required datasets (VideoKR-SFT, Knowledge Graph) and their sources.
 3. **Output Artifacts**: List of all generated files (CSV, JSON, MD) and their locations.
 - Ensure usage instructions are clear and reproducible.
 - Ensure `quickstart.md` exists and is up-to-date.
- [ ] T032 [P] Additional unit tests in `tests/unit/` (if requested)
- [ ] T033 Run `quickstart.md` validation to ensure reproducibility
- [ ] T035 [S] Implement `code/utils/runtime_logger.py` (or update main.py) to:
 - Instrument and log the **end-to-end runtime** of the full pipeline (ingestion to final report) to `data/processed/runtime_log.json`.
 - **Logic**: Record `total_runtime_seconds` and explicitly compare against a specified CI limit. Write `limit_exceeded: true/false`.
 - **Purpose**: Satisfy FR-006 and SC-004's 'measured against' requirement. (FR-006, SC-004)
 - **Constraint**: **NOT parallel-safe**. This task MUST run **after the completion of Phase 5**.
- [ ] T036 [S] **Memory Constraint Verification**: Implement `code/utils/memory_logger.py` (or update main.py) to measure peak memory usage during the full pipeline. **Logic**: This task must implement a **wrapper/decorator** that instruments memory usage (e.g., using `tracemalloc`) during the execution of T013 and T020b (and other heavy tasks). **It must NOT be a post-hoc check**. Log `peak_memory_gb` to `data/processed/memory_log.json` and explicitly compare against the 7GB limit (SC-005). Write `limit_exceeded: true/false`. **Depends on T035** (as T035 wraps the pipeline execution). (SC-005, FR-006)
- [ ] T034 [S] **Methodology Override Note**: Write a section to the final report `data/processed/final_report.md` (generated by T037) explicitly documenting the rejection of Generalized Additive Models (GAMs) in favor of the Permutation Test. **Content**: Cite the **Plan's 'Complexity Tracking' table** and **Methodology Notes** as the authority for rejecting GAMs due to statistical invalidity on discrete ordinal variables. **Output**: Write `data/processed/methodology_override.md` containing this note, and ensure it is included in the final report aggregation. (Plan Override, Methodology Notes)
- [ ] T037 [S] **Final Report Aggregation**: Implement `code/analysis/generate_final_report.py` to:
 - **Input**: Aggregate all outputs from US1 (T013b, T016), US2 (T023, T022b, T022c), US3 (T028a, T028b), and logs (T035, T036).
 - **Action**: Combine these into a single Markdown file `data/processed/final_report.md`.
 - **Integration**: Include the output from T034 (Methodology Override Note) as a dedicated section in this report.
 - **Output**: Write `data/processed/final_report.md`.
 - **Depends on**: Completion of Phase 5 and T034, T035, T036.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on completion of Phase 5. **T035 (Runtime Logger), T036 (Memory Logger), and T037 (Final Report) MUST run last.**

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (annotated data)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 logic and data (T013, T019, **T020b**)
- **Polish (Phase 6)**: Depends on completion of Phase 5.

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
- **Note**: T035 (Runtime Logger), T036 (Memory Logger), and T037 (Final Report) are **NOT** parallel-safe and must run last, after T028a/T028b.

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
- **Dual-Method Analysis**: Non-linearity is tested via Permutation Test (T020b, discrete) only. GAMs (FR-007) are explicitly rejected by the Plan's 'Complexity Tracking' table as statistically invalid for discrete ordinal variables; T034 documents it in the final report.