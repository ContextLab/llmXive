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

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [US1] Unit test for `graph_utils.py` shortest path logic in `tests/unit/test_graph_utils.py` (handles disconnected nodes, shortest path rule). **Depends on T006 completion.**
- [X] T011 [US1] Integration test for `annotate_graph.py` on a sample subset in `tests/integration/test_pipeline.py`

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/ingest/download_data.py` to fetch VideoKR-SFT and Knowledge Graph from verified URLs (NAB/UCI/arXiv) with checksumming <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [X] T013 [US1] Implement `code/ingest/annotate_graph.py` to:
 - Load graph and dataset
 - Map question entities to graph nodes using `entity_linker.py`
 - Calculate shortest path hops (1, 2, 3+) for each record
 - Handle disconnected graphs (exclude or label "unresolvable")
 - Enforce "shortest path" rule for multiple paths
- [ ] T014 [US1] Ensure output file `data/processed/annotated_videokr.csv` contains all input records with `chain_length` and original `correctness` labels (FR-002) <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested -->
- [ ] T015 [US1] Implement a **proactive two-stage sampling strategy** in `annotate_graph.py` to guarantee the analysis completes within 6 hours on a 2-core CPU runner (FR-006). <!-- FAILED: unspecified -->
 - **Step 1 (Pilot)**: Load and process a pilot sample of exactly **1000 records** to estimate hop distribution.
 - **Step 2 (Oversample)**: Based on pilot results, oversample the dataset to ensure **at least 50 records per hop bin** (1, 2, 3+). If the full dataset is required to reach this target, process in chunks; otherwise, use the oversampled subset.
 - **Constraint**: This strategy must be implemented as the default execution path, not a fallback. The script must log the final sample size and bin counts to `data/processed/sampling_log.json`. (FR-006)
- [X] T016 [US1] Write hash of `annotated_videokr.csv` to `state/projects/PROJ-961-llmxive-follow-up-extending-videokr-towa.yaml`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Accuracy Stratification and Threshold Detection (Priority: P2)

**Goal**: Calculate accuracy per hop-bin, detect non-linear "reasoning cliff" using Permutation Test.

**Independent Test**: Generate accuracy vs. hop plot and statistical report; verify trend and p-value against raw data summary.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Unit test for accuracy calculation logic in `tests/unit/test_stratify_accuracy.py`
- [X] T018 [P] [US2] Integration test for `detect_threshold.py` on annotated data in `tests/integration/test_pipeline.py`

### Implementation for User Story 2

- [X] T019 [P] [US2] Implement `code/analysis/stratify_accuracy.py` to calculate accuracy rate for bins 1-hop, 2-hop, 3+ hops (FR-003)
- [X] T020 [US2] Implement `code/analysis/detect_threshold.py` to:
 - Perform grid-search change-point detection over hops 1-5
 - Compare linear vs. piecewise linear models at optimal knot
 - Apply Bonferroni correction for multiple comparisons (FR-004)
 - **Note**: This task implements the Permutation Test for discrete change-point detection.
 - **Depends on T019** (requires binned accuracy data).
- [ ] T021 [US2] Handle small bin sizes in `detect_threshold.py`:
 - **Logic**: If the 3+ hop bin contains fewer than 50 samples:
 1. Attempt to merge 3+ hop records into the 2-hop bin.
 2. If the merged bin (2+3+ hops) has >= 50 samples, proceed with the test on the merged bin and log `bin_status: "merged"` in `data/processed/threshold_results.json`.
 3. If the merged bin still has < 50 samples, **defer** the statistical test for this comparison and log `bin_status: "deferred"` with the specific reason (insufficient power) in `data/processed/threshold_results.json`.
 - **Output**: The JSON file must explicitly contain the `bin_status` field to flag the limitation as required by the Spec Edge Cases. (Edge Cases)
- [ ] T022 [US2] Generate summary table and plots:
 - **Binned Plot**: Use data from T019 to plot accuracy vs. hop bin.
 - **Continuous Plot**: Generate a plot of accuracy vs. **exact `chain_length`** using the **raw, un-binned data** from `data/processed/annotated_videokr.csv` (FR-005). This must NOT use the binned data from T019.
 - **Depends on T013** (requires annotated data for continuous plot) and **T019** (for binned data).
- [X] T023 [US2] Output `data/processed/threshold_results.json` with p-value, effect size, optimal knot location, and deferral reasons (if any)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis of Threshold Definition (Priority: P3)

**Goal**: Verify robustness of the "cliff" by sweeping thresholds (2, 3, 4 hops) and visualizing stability.

**Independent Test**: Change threshold config parameter; verify output report shows variation in p-values and effect sizes.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Unit test for sensitivity sweep logic in `tests/unit/test_sensitivity.py`

### Implementation for User Story 3

- [X] T025 [US3] Implement `code/analysis/sensitivity.py` to:
 - **Re-apply Two-Stage Sampling**: For *each* threshold iteration (2, 3, 4 hops), re-run the **two-stage sampling strategy** (pilot=1000, oversample to min 50 per bin) to ensure sufficient power for the specific bin definition being tested.
 - Sweep thresholds across multiple hops (FR-005)
 - Re-run threshold detection logic for each offset (depends on T020 logic)
 - Compare significance (p-value) and effect size (accuracy drop)
 - **Note**: This task must run sequentially after T020 completes; [P] tag removed to indicate dependency on Phase 4 completion.
- [ ] T026 [US3] Generate comparison table for varying hop thresholds
- [ ] T027 [US3] Create overlay plot of accuracy curves for different threshold definitions
- [ ] T028 [US3] Output `data/processed/sensitivity_report.md` stating if "cliff" remains significant (p < 0.05) in ≥2 of 3 thresholds (SC-003)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: GAM Implementation (FR-007 Compliance)

**Goal**: Implement the Generalized Additive Model to test for non-linearity in the continuous domain, satisfying FR-007.

- [X] T034 [US2] Implement `code/analysis/fit_gam.py` to:
 - Fit a Generalized Additive Model (GAM) with a smooth spline term for hop count using `data/processed/annotated_videokr.csv`
 - Test for non-linearity in the continuous domain (FR-007)
 - Compare GAM fit against a linear baseline
 - **Statistical Validity Warning**: Explicitly include a warning in the output and report stating that GAMs are typically considered invalid for low-cardinality discrete ordinal variables (per Plan.md), but this implementation is required by Spec FR-007. Interpret results with extreme caution.
 - Output `data/processed/gam_results.json` with p-value for non-linearity and smoothness parameters
 - **Note**: This task complements T020 (Permutation Test) by addressing the continuous domain requirement as mandated by FR-007, overriding the Plan's "Complexity Tracking" note which suggested removal. The Spec's functional requirement (FR-007) takes precedence.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T029 [P] Documentation updates in `docs/` (README, usage instructions)
- [ ] T030 Code cleanup and refactoring
- [ ] T031 [P] Performance optimization: Ensure **annotation step (T015) and full pipeline** complete within 6 hours on 2-core CPU (FR-006). **Explicitly verify that T015's 6-hour constraint is met before proceeding to T020/T025.**
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
- **GAM (Phase 6)**: Depends on Foundational and US1 data (T013)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (annotated data)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 logic and data
- **GAM (Phase 6)**: Depends on US1 output (annotated data)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
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
- **Dual-Method Analysis**: Non-linearity is tested via both Permutation Test (T020, discrete) and GAM (T034, continuous) to satisfy all spec requirements (FR-004, FR-007).