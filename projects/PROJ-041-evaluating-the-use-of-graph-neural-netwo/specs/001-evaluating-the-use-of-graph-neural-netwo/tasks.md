# Tasks: Evaluating the Use of Graph Neural Networks for Anomaly Detection in Network Traffic

**Input**: Design documents from `/specs/001-evaluating-gnn-anomaly-detection/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create directory `code/data`
- [ ] T001b [P] Create directory `code/models`
- [ ] T001c [P] Create directory `code/analysis`
- [ ] T001d [P] Create directory `code/utils`
- [ ] T001e [P] Create directory `data/raw`
- [ ] T001f [P] Create directory `data/processed`
- [~] T001g [P] Create directory `data/results`
- [~] T001h [P] Create directory `tests`
- [~] T001i [P] Create directory `tests/integration`
- [X] T002 Initialize Python project with `requirements.txt` (pinning `torch` CPU version, `networkx`, `scikit-learn`, `xgboost`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `captum`, `pytest`, `pytest-memory-profiler`)
- [~] T003 [P] Configure linting (`ruff`) and formatting (`black`) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/utils/seed.py` to manage deterministic random seeds
- [X] T005 Implement `code/utils/memory_monitor.py` wrapper using `tracemalloc` to enforce a hard memory limit
- [ ] T006 Create `contracts/dataset.schema.yaml` and `contracts/graph.schema.yaml` defining data structures
- [~] T007a [P] Download CTU dataset from canonical URL: and validate checksum
- [~] T007b [P] Download the NF-BoT-IoT dataset from its canonical URL () and validate the checksum (Fallback).
- [X] T007c [P] Implement fallback logic in `code/data/ingest_netflow.py`: Check CTU availability; if missing, switch to BoT-IoT and log source
- [X] T007d [P] Define `Target AUC Threshold` in `code/config.yaml` (key: `target_auc`, default: 0.75) per SC-005
- [X] T008 Implement `code/data/preprocess.py` for strict subsampling: **Rule**: Extract ONLY the Largest Connected Component (LCC). If LCC < 5,000 nodes, retain LCC as-is. **Do NOT pad**.
- [X] T009 Implement `code/data/splits.py` for Temporal Holdout validation strategy (Train on the majority of time-windowed flows, test on the remaining minority., configurable via `config.temporal_split_ratio`)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Construct and Validate Network Traffic Graphs (Priority: P1) 🎯 MVP

**Goal**: Ingest raw NetFlow records, construct directed communication graphs, and verify memory safety (<7GB) and node limits (≤5,000).

**Independent Test**: Run `code/data/ingest_netflow.py` and `code/data/preprocess.py` on a single scenario; verify peak memory <7GB and graph object integrity.

### Tests for User Story 1 (Write Skeletons First)

> **NOTE**: Write these test **skeletons** FIRST (T010-T012), then implement code (T013-T017), then run tests.

- [X] T010 [P] [US1] Write test skeleton for graph construction memory limit in `tests/test_memory_limits.py` (asserts `tracemalloc` < 7GB) [Depends on T005, T013]
- [ ] T011 [P] [US1] Write test skeleton for node count subsampling in `tests/test_graph_construction.py` (asserts nodes ≤ 5,000, LCC rule) [Depends on T008, T013]
- [ ] T012 [P] [US1] Write test skeleton for data ingestion pipeline in `tests/integration/test_ingest.py` (verifies real data fetch and schema compliance)

### Implementation for User Story 1

- [ ] T013 [US1] Implement graph builder in `code/data/preprocess.py`: Nodes=IPs, Edges=flows, Weights=packet counts
- [ ] T014 [US1] Implement subsampling logic in `code/data/preprocess.py`: **Strict Rule** - Retain ONLY Largest Connected Component. Do NOT pad. If LCC < 5,000, keep LCC.
- [ ] T015 [US1] Implement memory guard in `code/utils/memory_monitor.py`: Raise controlled error if limit exceeded
- [ ] T016 [US1] Add validation checks in `code/data/preprocess.py`: Ensure edge weights are non-negative integers, handle missing labels
- [ ] T017 [US1] Write graph artifacts to `data/processed/graph_{scenario}_subsampled.graphml` with content hashes

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compare GNN Performance Against Feature-Engineered Baselines (Priority: P2)

**Goal**: Train 2-layer GCN (CPU-only) and baselines (RF, XGBoost) to compare predictive value of graph structure.

**Independent Test**: Train models on fixed split, evaluate on held-out test set, record metrics (Precision, Recall, F1, AUC-ROC).

### Tests for User Story 2 (Write Skeletons First)

- [ ] T018 [P] [US2] Write test skeleton for GCN convergence on CPU in `tests/test_models.py` (asserts no CUDA errors, converges ≤30 epochs)
- [ ] T019 [P] [US2] Write test skeleton for baseline training in `tests/test_models.py` (asserts RF/XGBoost produce predictions)
- [ ] T020 [P] [US2] Write test skeleton for Temporal Holdout split in `tests/integration/test_splits.py` (verifies no data leakage)

### Implementation for User Story 2

- [ ] T021 [P] [US2] [Depends on T017] Implement 2-layer GCN in `code/models/gcn.py`: CPU-only, max 30 epochs, early stopping (patience=5, delta=1e-4)
- [ ] T022 [P] [US2] [Depends on T017] Implement Random Forest and XGBoost wrappers in `code/models/baselines.py`: Use structural features (degree, centrality, variance)
- [ ] T023 [US2] [Depends on T021, T022] Implement evaluation metrics in `code/models/metrics.py`: Precision, Recall, F1-Score, AUC-ROC calculation
- [ ] T024 [US2] [Depends on T021, T022] Implement training loop in `code/main.py`: Orchestrates GCN and Baseline training with multiple random seeds
- [ ] T025 [US2] Write results to `data/results/metrics_{scenario}_{model}.json`
- [ ] T026 [US2] Add logging for model convergence failures and fallback to baseline

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Identify Predictive Structural Patterns and Validate Significance (Priority: P3)

**Goal**: Analyze feature importance, apply statistical corrections (Permutation Tests + Benjamini-Hochberg), and identify predictive patterns.

**Note on Statistical Method**: The Plan deviates from Spec FR-006 (Wilcoxon) to **Permutation Tests** for small N (<13). This task implements Permutation Tests as per Plan.

**Independent Test**: Run significance tests on model outputs; verify adjusted p-values and feature rankings.

### Tests for User Story 3 (Write Skeletons First)

- [ ] T027 [P] [US3] Write test skeleton for Permutation Test logic in `tests/test_significance_tests.py` (validates p-value calculation for small N)
- [ ] T028 [P] [US3] Write test skeleton for Benjamini-Hochberg correction in `tests/test_significance_tests.py` (validates FDR < 0.05 threshold)
- [ ] T029 [P] [US3] Write test skeleton for Integrated Gradients attribution in `tests/integration/test_attribution.py`

### Implementation for User Story 3

- [ ] T030 [P] [US3] [Depends on T025] Implement Permutation Tests in `code/analysis/significance_tests.py`: 10,000 permutations, alpha=0.05. Compare GCN vs RF, GCN vs XGB. [Trace: Plan.md Deviation 1]
- [ ] T031b [P] [US3] Implement specific "Structural Features vs. Null Baseline" hypothesis tests in `code/analysis/significance_tests.py`: Read top features from `data/results/feature_importance_ranking.json` (generated by T032)
- [ ] T031 [P] [US3] [Depends on T031b] Implement Benjamini-Hochberg correction in `code/analysis/significance_tests.py`: Aggregate multiple comparisons (model pairs + a set of feature tests)
- [ ] T032 [P] [US3] Implement Random Forest feature importance ranking in `code/analysis/attribution.py`
- [ ] T033 [US3] Implement Integrated Gradients for GNN in `code/analysis/attribution.py`: Map embeddings to structural proxies
- [ ] T033b [US3] Implement "Distinct Ranking Artifact" generation in `code/analysis/attribution.py`: Compare GNN vs RF rankings and output distinct patterns
- [ ] T034 [US3] Implement correlation analysis in `code/analysis/significance_tests.py`: Degree-based vs temporal-based patterns
- [ ] T035 [US3] Write final statistical report to `data/results/significance_report.json` and plots to `data/results/`
- [ ] T035b [US3] Enforce Target AUC Threshold in `code/models/metrics.py`: Read threshold from `code/config.yaml` (key: `target_auc`, default a moderate threshold)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036a [P] Write `docs/quickstart.md` with setup and run instructions
- [ ] T036b [P] Write `docs/data_model.md` with schema explanations
- [ ] T037a [P] Refactor `code/models/gcn.py` and `code/data/preprocess.py` to remove unused imports
- [ ] T037b [P] Optimize memory usage in `code/data/preprocess.py` graph construction loop
- [ ] T038a [P] Profile `code/main.py` to identify runtime bottlenecks
- [ ] T038b [P] Optimize graph construction loop in `code/data/preprocess.py` to ensure end-to-end runtime < 6 hours
- [ ] T039 [P] Additional unit tests for edge cases (missing labels, empty graphs) in `tests/unit/`
- [ ] T040 Run `quickstart.md` validation and verify all artifacts have content hashes

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for graph data
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 for model outputs

### Within Each User Story

- Test Skeletons (T010-T012, T018-T020, T027-T029) MUST be written FIRST
- Implementation follows Test Skeletons
- Tests are executed after Implementation
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All Test Skeletons for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all Test Skeletons for User Story 1 together:
Task: "Write test skeleton for graph construction memory limit in tests/test_memory_limits.py"
Task: "Write test skeleton for node count subsampling in tests/test_graph_construction.py"
Task: "Write test skeleton for data ingestion pipeline in tests/integration/test_ingest.py"

# Launch all models for User Story 1 together:
Task: "Implement graph builder in code/data/preprocess.py"
Task: "Implement subsampling logic in code/data/preprocess.py"
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
- Verify test skeletons are written before implementation
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Data Integrity**: All tasks consuming data must use the real dataset fetched in T007a/T007b; no synthetic data generation.
- **Hardware Constraints**: All model training (T021, T022) must run on CPU without CUDA/quantization.
- **Statistical Deviation**: T030 implements Permutation Tests instead of Wilcoxon (Spec FR-006) as per Plan.md deviation for small sample sizes.
- **Subsampling Rule**: T008 and T014 strictly enforce "Largest Connected Component only" (no padding, no anomaly-preservation heuristics) per FR-002 and Constitution Principle VI.
- **Temporal Split Clarity**: T009 and T020 explicitly enforce the "Train on first [deferred] (config.temporal_split_ratio=0.8), Test on remaining [deferred]" split to prevent leakage.
- **Small Sample Robustness**: T030 and T031 explicitly implement Permutation Tests and BH correction to ensure validity given N < 13 scenarios.
- **Target AUC Threshold**: T035b enforces the threshold defined in `code/config.yaml` (default 0.75) as per SC-005.