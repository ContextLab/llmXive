# Tasks: llmXive follow-up: extending "VideoKR: Towards Knowledge- and Reasoning-Intensive Video Understandin"

**Input**: Design documents from `/specs/001-video-reasoning-threshold/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
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

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/utils/config.py` for seed management and path configuration
- [X] T005 [P] Implement `code/utils/versioning.py` to write SHA-256 hashes of data artifacts (Constitution Principle V)
- [X] T006 [P] Create `code/utils/graph_utils.py` with shortest path logic (BFS) handling disconnected graphs
- [X] T007 [P] Create `code/utils/entity_linker.py` for mapping question entities to graph nodes (fuzzy/embedding based)
- [ ] T008a [P] Create `.gitkeep` in `data/raw/` directory
- [ ] T008b [P] Create `.gitkeep` in `data/processed/` directory
- [X] T009 [P] Implement `code/ingest/checksum.py` for verifying raw data integrity

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Structural Annotation (Priority: P1) 🎯 MVP

**Goal**: Download VideoKR-SFT, annotate questions with structural chain length (hops) from the ground-truth graph.

**Independent Test**: Run the annotation script on a small, manually verified subset; confirm `chain_length` matches manual graph traversal for a representative sample of random records.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation. These are part of the 'Implementation' block for US1.**

- [X] T010 [US1] Unit test for `graph_utils.py` shortest path logic in `tests/unit/test_graph_utils.py` (handles disconnected nodes, shortest path rule). **Depends on T006 completion.**
- [X] T011 [US1] Integration test for `annotate_graph.py` on a sample subset in `tests/integration/test_pipeline.py`

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/ingest/download_data.py` to fetch VideoKR-SFT and Knowledge Graph from verified URLs (NAB/UCI/arXiv) with checksumming
- [X] T013 [US1] Implement `code/ingest/annotate_graph.py` to:
 - **Chunked Processing**: Implement chunked streaming (e.g., `pandas.read_csv(chunksize=...)`) to process the dataset in memory-safe batches.
 - **Fallback Sampling**: If the full dataset cannot be processed within 7GB RAM (detected via memory monitoring) or pilot phase indicates >6h runtime, **MUST** fall back to a stratified random sample (e.g., `itertools.islice` or `datasets.load_dataset(streaming=True)` with `islice`) that preserves hop distribution. **DO NOT** fabricate data. Log the sampling method and size.
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
 - **Output**: Write `data/processed/annotated_videokr.csv` with columns: `id`, `question`, `answer`, `chain_length` (integer), `chain_bin` (categorical), `correctness`. (FR-001, FR-002, SC-001)
- [X] T014 [US1] **Implementation & Verification**: Implement `code/ingest/annotate_graph.py` to:
 - Verify that the row count of the output file matches the input file (excluding unresolvable records if applicable).
 - **Action**: If mismatch, raise an error immediately.
 - **Output**: Write `data/processed/annotated_videokr.csv`. (FR-002)
- [X] T015 [US1] **Verification**: Calculate and log the proportion of questions successfully annotated to `data/processed/annotation_coverage.json`. **Logic**: `proportion = annotated_count / total_input_records`. **Mandatory**: Explicitly log `total_input_records` (count BEFORE any exclusion), `unresolvable_count`, and `annotated_count` as separate fields in the JSON to enable independent verification of SC-001. (SC-001)
- [X] T016 [US1] Write hash of `annotated_videokr.csv` to `state/projects/PROJ-961-llmxive-follow-up-extending-videokr-towa.yaml`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Accuracy Stratification and Threshold Detection (Priority: P2)

**Goal**: Calculate accuracy per hop-bin, detect non-linear "reasoning cliff" using Permutation Test (per Plan override).

**Independent Test**: Generate accuracy vs. hop plot and statistical report; verify trend and p-value against raw data summary.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Unit test for accuracy calculation logic in `tests/unit/test_stratify_accuracy.py`
- [X] T018 [P] [US2] Integration test for `detect_threshold.py` on annotated data in `tests/integration/test_pipeline.py`

### Implementation for User Story 2

- [X] T019 [P] [US2] Implement `code/analysis/stratify_accuracy.py` to:
 - Calculate accuracy rate for bins 1-hop, 2-hop, 3+ hops (aggregating 3, 4, 5... into '3+' for the primary report as per Spec US-2).
 - **Bin Size Check**: If the '3+' bin (or any other bin) has <50 records, prepare a flag for T021. (FR-003)
- [X] T020 [US2] Implement `code/analysis/detect_threshold.py` to:
 - **Input**: Use **exact integer `chain_length` data from T013** (1, 2, 3, 4, 5...).
 - **Methodology**: **Per Plan Complexity Tracking table**, use a **Permutation Test** (n=1000) for change-point detection to avoid inflated Type I errors from data-driven knot selection, overriding Spec FR-004's LRT requirement.
 - **Grid-Search Logic**: Iterate knot locations from **1 to 5** (fixed range per Spec FR-004). For each knot:
 1. Fit a linear model (accuracy ~ hop_count).
 2. Fit a piecewise linear model (accuracy ~ hop_count + max(0, hop_count - knot)).
 3. Perform the permutation test to derive the p-value for the improvement in fit.
 - **Correction**: Apply **Bonferroni correction** for the number of tests performed (p_corrected = p_raw * num_tests).
 - **Selection**: Select the knot location with the minimum corrected p-value.
 - **Output**: Identify the optimal knot and report the corrected p-value. (FR-004)
 - **Depends on T019** (requires binned accuracy data for reporting, but uses raw data for grid search).
- [ ] T021 [US2] Handle small bin sizes in `detect_threshold.py`:
 - **Logic**: If the 3+ hop bin (or any bin used in the test) contains fewer than 50 samples:
 1. **Attempt Merge**: Merge the underpowered bin with the adjacent bin (e.g., 3+ with 2-hop).
 2. **Re-check**: If the merged bin has >= 50 samples, proceed with the test on the merged bin and log `bin_status: "merged"` in `data/processed/threshold_results.json`.
 3. **Defer**: If the merged bin still has < 50 samples, **defer** the statistical test for this comparison. Write `status: "deferred"`, `reason: "insufficient_power"`, and `bin_status: "deferred"` to the JSON file. **Do not** fabricate data, merge blindly, or force a test.
 - **Output Schema**: The JSON file `data/processed/threshold_results.json` must explicitly contain: `status`, `bin_status`, `reason`, `merged_bin_definition` (list of merged bin IDs), and `p_value` (if applicable).
 - **Reporting Requirement**: If bins are merged or tests deferred, this logic MUST pass a flag to T028a (final report) to include a "Limitations" section explicitly stating the merged bin definition and the reason for deferral. (Edge Cases)
- [ ] T022a [US2] [P] **Continuous Plot**: Generate a **scatter plot of accuracy vs. exact `chain_length`** using the **raw, un-binned data** from `data/processed/annotated_videokr.csv` (T013 output). **Constraint**: Plot **raw scatter points** AND a **line connecting the mean accuracy of each discrete hop count**. **DO NOT** use smoothing splines (LOESS, spline, etc.) to ensure the visualization is artifact-free as required by FR-005. (FR-005, SC-003) <!-- FAILED: unspecified -->
 - **Depends on T013**.
- [ ] T022b [US2] **Binned Summary & Plot**: Generate a summary table and a **binned bar plot** of accuracy vs. hop bin using data from T019. **Depends on T019**. (FR-003)
- [X] T023 [US2] Output `data/processed/threshold_results.json` with p-value, effect size, optimal knot location, deferral reasons (if any), and an explicit `conclusion` field (PASS/FAIL). **Logic**: Explicitly compare the calculated p-value against alpha=0.05. The JSON must include: `p_value` (float), `alpha` (0.05), `is_significant` (boolean), and `conclusion` (string). (SC-002)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis of Threshold Definition (Priority: P3)

**Goal**: Verify robustness of the "cliff" by sweeping thresholds (2, 3, 4 hops) and visualizing stability.

**Independent Test**: Change threshold config parameter; verify output report shows variation in p-values and effect sizes.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Unit test for sensitivity sweep logic in `tests/unit/test_sensitivity.py`

### Implementation for User Story 3

- [X] T025 [US3] Implement `code/analysis/sensitivity.py` to:
 - **Input**: Use **existing `chain_length` values from `data/processed/annotated_videokr.csv` (T013 output)**.
 - **Constraint**: **DO NOT re-sample** or re-annotate. The structural chain length is immutable.
 - **Action**: Re-bin the existing data for each threshold iteration across multiple hop counts..
 - **Logic**: **Import and reuse the threshold detection logic (grid-search, permutation test) from `code/analysis/detect_threshold.py` functions** to ensure consistency. Do not re-implement. **Depends on T013** (raw annotated data) and **T020** (threshold detection logic implementation).
 - Compare significance (p-value) and effect size (accuracy drop).
- [ ] T026a [US3] **Comparison Table**: Generate a CSV file `data/processed/sensitivity_thresholds.csv` with columns: `threshold_hop`, `p_value`, `effect_size`, `is_significant`. (FR-005)
- [ ] T026b [US3] **Summary Report**: Generate a Markdown summary `data/processed/sensitivity_summary.md` interpreting the table. (FR-005)
- [ ] T027a [US3] **Overlay Plot**: Create a plot `data/processed/sensitivity_overlay.png` overlaying accuracy curves for different threshold definitions (2, 3, 4 hops) using `matplotlib`. (FR-005)
- [X] T028a [US3] Output `data/processed/sensitivity_report.md` stating if "cliff" remains significant (p < 0.05) in ≥2 of 3 thresholds (SC-003). **Content Structure**: Must include a table of thresholds, p-values, effect sizes, and a final 'Robustness Conclusion' section stating 'Robust' (if count >= 2) or 'Not Robust' (if count < 2). **Limitations**: If T021 flagged any merged/deferred bins, this report MUST include a "Limitations" section explicitly stating the merged bin definition and the reason for deferral. (SC-003)
- [ ] T028b [US3] Programmatically calculate and log the **count of significant thresholds** to `data/processed/stability_metric.json`. **Logic**: Count thresholds where p < 0.05; verify if count >= 2. Output a field `robustness_status` with value 'PASS' if count >= 2, else 'FAIL'. (SC-003)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish

**Goal**: Finalize reporting, documentation, and runtime measurement. (GAM Implementation removed per Plan decision).

- [X] T031a [P] Remove unused imports from all scripts in `code/`.
- [ ] T031b [P] Add type hints to all public functions in `code/`.
- [ ] T031c [P] Ensure all scripts in `code/` have docstrings.
- [ ] T029 [P] Documentation updates in `docs/`:
 - Update `README.md` to include:
 1. **Usage Section**: Instructions on how to run `code/main.py` end-to-end.
 2. **Data Requirements**: List of required datasets (VideoKR-SFT, Knowledge Graph) and their sources.
 3. **Output Artifacts**: List of all generated files (CSV, JSON, MD) and their locations.
 - Ensure usage instructions are clear and reproducible.
- [ ] T032 [P] Additional unit tests in `tests/unit/` (if requested)
- [ ] T033 Run `quickstart.md` validation to ensure reproducibility
- [X] T035 [S] Implement `code/utils/runtime_logger.py` (or update main.py) to:
 - Instrument and log the **end-to-end runtime** of the full pipeline (ingestion to final report) to `data/processed/runtime_log.json`.
 - **Logic**: Record `total_runtime_seconds` and explicitly compare against the 6-hour CI limit (21600 seconds). Write `limit_exceeded: true/false`.
 - **Purpose**: Satisfy FR-006 and SC-004's 'measured against' requirement. (FR-006, SC-004)
 - **Constraint**: **NOT parallel-safe**. This task MUST run **after** all analysis tasks (T013, T019, T020, T025) are complete.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on completion of Phase 5. **T035 (Runtime Logger) must run last.**

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (annotated data)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 logic and data (T013, T019, **T020**)
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
- **Note**: T035 (Runtime Logger) is **NOT** parallel-safe and must run last.

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
- **Constraint**: All tasks must run on CPU-only CI (limited cores, limited RAM, 6h limit). No GPU, no low-bit models, no large LLMs.
- **Data Integrity**: No fake data. All datasets must be fetched from real, verified sources.
- **Dual-Method Analysis**: Non-linearity is tested via Permutation Test (T020, discrete) only. GAMs (FR-007) are explicitly rejected by the Plan's 'Complexity Tracking' table as statistically invalid for discrete ordinal variables; T034 was removed to align with this architectural decision.