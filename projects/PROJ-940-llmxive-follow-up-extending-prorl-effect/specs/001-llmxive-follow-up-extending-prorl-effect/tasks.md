# Tasks: llmXive Follow-up: Extending ProRL for Zero-Shot Proactive Recommendation

**Input**: Design documents from `/specs/001-llmxive-prorl-zero-shot/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure: Create directories `src/`, `tests/unit/`, `tests/integration/`, `data/raw/`, `data/processed/`, `results/`. Create empty `__init__.py` in `src/` and `tests/`.
- [X] T002 Initialize Python 3.11 project with dependencies (`pandas`, `numpy`, `scikit-learn`, `networkx`, `scipy`, `datasets`, `pyyaml`, `pytest`) in `requirements.txt`. Content: `pandas`, `numpy`, `scikit-learn`, `networkx`, `scipy`, `datasets`, `pyyaml`, `pytest`.
- [X] T003 [P] Configure linting (`ruff`) and formatting (`black`) tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes data loading, splitting, and resource enforcement.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `src/config.py` to define hyperparameters (path length L=5, alpha=0.1, beam_width=50, random_seed=42) and load via `pyyaml`
- [ ] T005 [P] Create data directory structure (`data/raw/`, `data/processed/`, `results/`) with `.gitkeep` files
- [X] T006 Implement `src/utils/io.py` for deterministic file I/O (JSON/Parquet) and checksum verification
- [X] T007 Create `src/entities.py` defining `ItemNode`, `SimilarityEdge`, `RecommendationPath`, and `EvaluationMetric` dataclasses
- [X] T008 Setup error handling infrastructure in `src/exceptions.py` (e.g., `GraphDisconnectionError`, `DataFetchError`)
- [X] T009a [P] [Foundational] Implement resource enforcement logic in `src/utils/resource.py` to detect dataset size and apply sampling/capping if >7GB RAM. If size > 7GB, sample to 500k items. Log enforcement actions (e.g., 'Sampling applied: 500k items') to `results/resource_log.json` (optional debug log).
- [X] T009b [P] [Foundational] Implement CLI argument parsing in `src/main.py` to support dataset selection and parameter overrides (moved from Phase N).
- [X] T013a [P] [Foundational] Implement data loader in `src/data_loader.py` for **Amazon Books** dataset using `datasets.load_dataset('amazon_books', streaming=True)`; ensure it fails loudly on fetch errors without synthetic fallback (FR-001).
- [X] T013b [P] [Foundational] Implement data loader in `src/data_loader.py` for **Last.fm** dataset using `datasets.load_dataset('lastfm', streaming=True)`; ensure it fails loudly on fetch errors without synthetic fallback (FR-001).
- [X] T013c [P] [Foundational] Implement data loader in `src/data_loader.py` for **MovieLens** dataset using `datasets.load_dataset('ml-latest-small', streaming=True)`; ensure it fails loudly on fetch errors without synthetic fallback (FR-001).
- [X] T013d [Foundational] Implement data splitting logic in `src/data_loader.py` to generate a held-out test set of user sessions (seed -> next item) for cold-start evaluation. **Must use a time-based split**: Sort sessions by timestamp per user (MovieLens: 'timestamp', Amazon Books: 'reviewTime', Last.fm: 'date'; raise error if no timestamp column exists), then take a portion of the most recent sessions as the test set. This ensures the split respects the 'next item' cold-start logic (FR-001, US2 dependency).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Zero-Shot Path Generation and Scoring (Priority: P1) 🎯 MVP

**Goal**: Ingest a cold-start seed, construct a static similarity graph, generate candidate paths, and apply ProRL rectification formulas (SRC/PSA) as a post-hoc filter.

**Independent Test**: Run the pipeline on a small subset of the Amazon Books or MovieLens dataset with a fixed seed, verifying that the output is a ranked list of paths where the scores differ from the raw greedy scores due to the applied formulas.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for SRC formula in `tests/unit/test_scoring.py`
- [X] T011 [P] [US1] Unit test for PSA formula in `tests/unit/test_scoring.py`
- [X] T012 [P] [US1] Integration test for disconnected graph handling in `tests/integration/test_graph.py`

### Implementation for User Story 1

- [X] T014 [US1] Implement `src/graph_builder.py` to construct a static item-similarity graph using cosine similarity on genre/features; handle zero-overlap neighbors by assigning score 0.0 and skipping them (FR-009).
- [X] T015 [US1] Implement `src/graph_builder.py` logic to handle disconnected components by truncating paths or returning null results without crashing (FR-007).
- [X] T016a [US1] Implement `src/path_generator.py` function `generate_greedy_paths` to generate the **standard greedy heuristic** baseline paths of length L=5 based on immediate similarity to the seed (FR-003).
- [X] T016b [US1] Implement `src/path_generator.py` function `generate_beam_paths` to generate a diverse candidate pool of paths using **Beam Search** (B=50) for extended analysis (secondary to Greedy baseline).
- [X] T017 [US1] Implement `src/path_generator.py` function `apply_prorl_rectification` to calculate Stepwise Reward Centering ($S_{rect} = S_{raw} - \mu_{batch}$) and Position-Specific Advantage ($S_{final} = S_{rect} \times (1 + \alpha \times pos)$) on the output of T016a (Greedy paths - PRIMARY HYPOTHESIS TEST) and T016b (Beam pool - secondary).
- [X] T018 [US1] Implement `src/main.py` orchestration logic to chain data loading, graph building, path generation (both Greedy and Beam), and rectification for a single cold-start seed item.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Baseline Comparison and Metric Calculation (Priority: P2)

**Goal**: Compare ProRL-scored paths against Greedy-scored paths, calculating Precision@K, Recall@K, Diversity, and Coverage against a held-out test set.

**Independent Test**: Run the evaluation module on a fixed test set, comparing the metric values of the "ProRL-scored" list against the "Greedy" list, and verifying that the output includes the calculated metrics for both methods.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for Precision@K and Recall@K calculation in `tests/unit/test_metrics.py`
- [X] T020 [P] [US2] Unit test for Diversity and Coverage calculation in `tests/unit/test_metrics.py`

### Implementation for User Story 2

- [X] T021 [US2] Implement `src/evaluator.py` to load held-out test sessions (from T013d) and identify the "next item" ground truth for cold-start seeds.
- [X] T022 [US2] Implement `src/evaluator.py` function `calculate_precision_recall` (FR-004) to compute Precision@K and Recall@K.
- [X] T023 [US2] Implement `src/evaluator.py` function `calculate_diversity_coverage` (FR-004) to compute Diversity ($1 - \text{avg cosine sim}$) and Coverage.
- [ ] T024 [US2] Implement `src/main.py` logic to run the evaluation pipeline on the full test set, generating `results/greedy_paths.json` (Greedy), `results/greedy_rectified_paths.json` (Greedy+ProRL), and `results/beam_rectified_paths.json` (Beam+ProRL). **This task depends on T021-T023 being defined.**
- [ ] T025 [US2] Implement `src/main.py` validation logic to check SC-005: verify mean absolute difference between rectified and raw scores ≥ 0.01. **Must create or overwrite** `results/sc005_status.json` with the status (pass/fail) to ensure T032 can read it.
- [ ] T025b [US2] Implement `src/evaluator.py` function `compare_metrics` to perform the side-by-side metric comparison (Precision@K, Diversity, etc.) between `results/greedy_paths.json` and `results/greedy_rectified_paths.json`, outputting the comparison results to `results/metrics_comparison.json` as required by US-2 and SC-001.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance and Sensitivity Analysis (Priority: P3)

**Goal**: Perform statistical significance testing (Shapiro-Wilk -> Wilcoxon/T-test) and sensitivity analysis on decision cutoffs.

**Independent Test**: Modify the sensitivity analysis configuration to sweep a parameter and verify that the output includes a report of how metrics change across the sweep range.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Unit test for Shapiro-Wilk and Wilcoxon test selection logic in `tests/unit/test_stats.py`
- [X] T027 [P] [US3] Unit test for sensitivity sweep aggregation in `tests/unit/test_stats.py`

### Implementation for User Story 3

- [ ] T028 [US3] Implement `src/stats.py` function `perform_significance_test` (FR-005) to run Shapiro-Wilk, then conditionally run Paired T-test or Wilcoxon signed-rank test on metric differences per seed item.
- [ ] T028b [US3] Implement `src/stats.py` function `execute_significance_test` to run the test from T028 on the metric differences from T025b, and explicitly record the p-values, confidence intervals, and conclusion (significant/not) to `results/statistical_significance.json` as required by SC-001.
- [ ] T029 [US3] Implement `src/stats.py` function `run_sensitivity_analysis` (FR-006) to sweep **decision cutoffs**: **path length** (e.g., L=3,4,5) and **similarity threshold** (specifically {0.01, 0.05, 0.1}) and record headline rate variations.
- [ ] T029b [US3] Implement `src/stats.py` function `aggregate_sensitivity_report` to aggregate the sweep results from T029 and generate a summary report showing how the false-positive/negative rates or inconsistency rates vary across these values, outputting to `results/sensitivity_report.json` as required by SC-002.
- [ ] T030 [US3] Implement `src/main.py` logic to aggregate results and generate `results/statistical_report.json` including p-values, confidence intervals, and sweep summaries.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T031 [P] Implement resource monitoring in `src/main.py` to log peak RAM usage, total runtime, and **resource enforcement actions taken** (SC-003, SC-004).
- [ ] T032 [P] Write `results/final_report.md` generation logic summarizing all metrics, statistical findings, SC-005 pass/fail status (read from `results/sc005_status.json`), and sensitivity reports.
- [ ] T033 [P] Add comprehensive docstrings to all public functions in `src/` modules
- [ ] T034 Run `pytest` suite and ensure all tests pass (exit code 0).
- [ ] T035 Validate `quickstart.md` instructions against the implemented pipeline

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 outputs (paths) and T013d (test set)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 outputs (metrics)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Entities before services
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2), except T013d which depends on T013a-c
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for SRC formula in tests/unit/test_scoring.py"
Task: "Unit test for PSA formula in tests/unit/test_scoring.py"

# Launch all models for User Story 1 together:
Task: "Create ItemNode entity in src/entities.py"
Task: "Create SimilarityEdge entity in src/entities.py"
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