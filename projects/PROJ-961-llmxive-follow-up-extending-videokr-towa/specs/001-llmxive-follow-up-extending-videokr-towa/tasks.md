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
 - **Process ALL records**: Load the full dataset and graph. **DO NOT** default to sampling.
 - **Pilot Phase (Optional)**: If memory constraints require, run a pilot on a small subset (e.g., 1000 records) to estimate bin sizes.
 - **Map entities**: Map question entities to graph nodes using `entity_linker.py`.
 - **Calculate Exact Hops**: Calculate the **exact integer** shortest path hops (1, 2, 3, 4, 5...) for each record. Output this as the column `chain_length` (integer type).
 - **Generate Binned Column**: Derive a second column `chain_bin` (categorical: '1', '2', '3+') from `chain_length` to satisfy FR-002's requirement for binned categories.
 - **Handle Disconnected**: Exclude or label 'unresolvable' for disconnected graphs.
 - **Enforce Shortest Path**: Use the shortest path rule for multiple paths.
 - **Stratified Oversampling Logic**: If the pilot phase reveals any hop bin (1-5) has <50 records, perform **stratified oversampling with replacement** ONLY on that specific bin to ensure n>=50. Log the method used. This ensures n>=50 without violating data hygiene (no synthetic data).
 - **Output**: Write `data/processed/annotated_videokr.csv` with columns: `id`, `question`, `answer`, `chain_length` (integer), `chain_bin` (categorical), `correctness`. (FR-001, FR-002, SC-001)
- [ ] T014a [US1] Ensure output file `data/processed/annotated_videokr.csv` contains all input records with `chain_length` and original `correctness` labels (FR-002). <!-- FAILED: unspecified -->
- [ ] T014b [US1] Calculate and log the proportion of questions successfully annotated to `data/processed/annotation_coverage.json`. **Logic**: `proportion = (total_input_records - unresolvable_count) / total_input_records`. This explicitly measures against the total input records as required by SC-001. (SC-001)
- [X] T016 [US1] Write hash of `annotated_videokr.csv` to `state/projects/PROJ-961-llmxive-follow-up-extending-videokr-towa.yaml`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Accuracy Stratification and Threshold Detection (Priority: P2)

**Goal**: Calculate accuracy per hop-bin, detect non-linear "reasoning cliff" using Permutation Test and GAM.

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
 - **Grid-Search Logic**: Iterate knot locations from 1 to 4. For each knot:
 1. Fit a linear model (accuracy ~ hop_count).
 2. Fit a piecewise linear model (accuracy ~ hop_count + max(0, hop_count - knot)).
 3. Calculate the Likelihood Ratio Test (LRT) statistic.
 - **Correction**: Apply Bonferroni correction for the 4 tests performed (p_corrected = p_raw * 4).
 - **Selection**: Select the knot location with the minimum corrected p-value.
 - **Output**: Identify the optimal knot and report the corrected p-value. (FR-004)
 - **Depends on T019** (requires binned accuracy data for reporting, but uses raw data for grid search).
- [ ] T021 [US2] Handle small bin sizes in `detect_threshold.py`:
 - **Logic**: If the 3+ hop bin (or any bin used in the test) contains fewer than 50 samples:
 1. **Attempt Merge**: Merge the underpowered bin with the adjacent bin (e.g., 3+ with 2-hop).
 2. **Re-check**: If the merged bin has >= 50 samples, proceed with the test on the merged bin and log `bin_status: "merged"` in `data/processed/threshold_results.json`.
 3. **Defer**: If the merged bin still has < 50 samples, **defer** the statistical test for this comparison. Write `status: "deferred"`, `reason: "insufficient_power"`, and `bin_status: "deferred"` to the JSON file. **Do not** fabricate data, merge blindly, or force a test.
 - **Output**: The JSON file `data/processed/threshold_results.json` must explicitly contain the `status`, `bin_status`, `reason`, and `merged_bin_definition` fields to flag the limitation as required by the Spec Edge Cases. (Edge Cases)
- [ ] T022 [US2] Generate summary table and plots:
 - **Binned Plot**: Use data from T019 to plot accuracy vs. hop bin.
 - **Continuous Plot**: Generate a **scatter plot with a smoothed trend line (LOESS or spline)** of accuracy vs. **exact `chain_length`** using the **raw, un-binned data** from `data/processed/annotated_videokr.csv` (T013 output). This is required by FR-005 and SC-003 to visualize the cliff as a continuous relationship. (FR-005, SC-003)
 - **Depends on T013** (requires annotated data for continuous plot) and **T019** (for binned data).
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
 - **Action**: Re-bin the existing data for each threshold iteration (2, 3, 4 hops).
 - **Logic**: Re-run threshold detection logic for each offset (depends on T020 logic). **Depends on T020 (Phase 4) completion.**
 - Compare significance (p-value) and effect size (accuracy drop).
 - **Depends on T013** (raw annotated data) and **T020** (threshold detection logic).
- [ ] T026 [US3] Generate comparison table for varying hop thresholds
- [ ] T027 [US3] Create overlay plot of accuracy curves for different threshold definitions
- [X] T028a [US3] Output `data/processed/sensitivity_report.md` stating if "cliff" remains significant (p < 0.05) in ≥2 of 3 thresholds (SC-003). **Content Structure**: Must include a table of thresholds, p-values, effect sizes, and a final 'Robustness Conclusion' section stating 'Robust' (if count >= 2) or 'Not Robust' (if count < 2). (SC-003)
- [ ] T028b [US3] Programmatically calculate and log the **count of significant thresholds** to `data/processed/stability_metric.json`. **Logic**: Count thresholds where p < 0.05; verify if count >= 2. Output a field `robustness_status` with value 'PASS' if count >= 2, else 'FAIL'. (SC-003)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: GAM Implementation (FR-007 Compliance) & Polish

**Goal**: Implement the Generalized Additive Model to test for non-linearity in the continuous domain, satisfying FR-007, and finalize reporting.

- [X] T034 [US2] Implement `code/analysis/fit_gam.py` to:
 - **Mandatory Execution**: Attempt to fit a Generalized Additive Model (GAM) with a smooth spline term for hop count **regardless of data cardinality**. Do NOT skip if cardinality is low.
 - **Methodological Integrity**: If the data cardinality is low (<5 distinct values), the model fit may fail or be invalid. In this case, the task must **not skip**. Instead, capture the error, log `status: "failed"`, `reason: "low_cardinality_discrete"`, and `error_message: "<specific error>"` to `data/processed/gam_results.json`. This ensures the 'MUST fit' requirement is honored by attempting the operation and reporting the failure state explicitly.
 - **Conditional Execution**: If distinct values >= 5, fit the GAM normally.
 - **Output**: Write `data/processed/gam_results.json` with `p_value`, `smoothness_parameters`, `status` ('success' or 'failed'), and `reason` (if failed). (FR-007)
 - **Fail-Safe**: If the model fit fails or produces nonsensical results (e.g., negative p-values), write `status: "failed"`, `error_message: "<error>"` to the JSON file. (FR-007)
- [ ] T031a [P] Remove unused imports from all scripts in `code/`.
- [ ] T031b [P] Add type hints to all public functions in `code/`.
- [ ] T031c [P] Ensure all scripts in `code/` have docstrings.
- [ ] T035 [P] Implement `code/utils/runtime_logger.py` (or update main.py) to:
 - Instrument and log the **end-to-end runtime** of the full pipeline (ingestion to final report) to `data/processed/runtime_log.json`.
 - **Logic**: Record `total_runtime_seconds` and explicitly compare against the 6-hour CI limit (21600 seconds). Write `limit_exceeded: true/false`.
 - **Purpose**: Satisfy FR-006 and SC-004's 'measured against' requirement. (FR-006, SC-004)
 - **Note**: This task must run **after** all analysis tasks (T013, T019, T020, T025, T034) are complete. It is **not** parallel-safe.
- [ ] T029 [P] Documentation updates in `docs/`:
 - Update `README.md` to include:
 1. **Usage Section**: Instructions on how to run `code/main.py` end-to-end.
 2. **Data Requirements**: List of required datasets (VideoKR-SFT, Knowledge Graph) and their sources.
 3. **Output Artifacts**: List of all generated files (CSV, JSON, MD) and their locations.
 - Ensure usage instructions are clear and reproducible.
- [ ] T032 [P] Additional unit tests in `tests/unit/` (if requested)
- [ ] T033 Run `quickstart.md` validation to ensure reproducibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **GAM (Phase 4/6)**: Depends on Foundational and US1 data (T013). **Moved to Phase 4** to be part of core threshold detection.
- **Polish (Final Phase)**: Depends on all desired user stories being complete. **T035 (Runtime Logger) must run last.**

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (annotated data)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 logic and data (T013, T019, **T020**)
- **GAM (Phase 4)**: Depends on US1 output (annotated data).
- **Polish (Phase 6)**: Depends on completion of Phase 4 (including GAM) and Phase 5.

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
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Constraint**: All tasks must run on CPU-only CI (limited cores, limited RAM, 6h limit). No GPU, no low-bit models, no large LLMs.
- **Data Integrity**: No fake data. All datasets must be fetched from real, verified sources.
- **Dual-Method Analysis**: Non-linearity is tested via both Permutation Test (T020, discrete) and GAM (T034, continuous, mandatory attempt) to satisfy all spec requirements (FR-004, FR-007).