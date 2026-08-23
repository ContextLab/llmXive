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

- [ ] T001 [P] Create project directory structure: `code/data`, `code/models`, `code/analysis`, `code/utils`, `data/raw`, `data/processed`, `data/results`, `tests`, `tests/integration`, `tests/unit`
- [X] T002 Initialize Python project with `requirements.txt` (pinning `torch` CPU version, `networkx`, `scikit-learn`, `xgboost`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `captum`, `pytest`, `pytest-memory-profiler`)
- [ ] T003 [P] Configure linting (`ruff`) and formatting (`black`) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/utils/seed.py` to manage deterministic random seeds
- [X] T005 Implement `code/utils/memory_monitor.py` wrapper using `tracemalloc` to enforce a hard memory limit
- [ ] T006 Create `contracts/dataset.schema.yaml` and `contracts/graph.schema.yaml` defining data structures
- [ ] T007a [P] Download CTU dataset from canonical URL: ` and validate checksum
- [ ] T007b [P] Download the NF-BoT-IoT dataset from its canonical URL (`) and validate the checksum (Fallback).
- [X] T007c [P] Implement fallback logic in `code/data/ingest_netflow.py`: Check CTU availability; if missing, switch to BoT-IoT and log source
- [X] T007d [P] Define `Target AUC Threshold` in `code/config.yaml` (key: `target_auc`, default: a threshold value). **Note**: Per Plan.md (Research Section), the specific value is defined in the research plan; `config.yaml` acts as the implementation carrier. The Plan mandates this parameter exists in config.yaml as the source of truth for the threshold.
- [X] T008 [P] Implement `code/data/preprocess.py` subsampling logic: **Input**: `data/raw/*.csv`. **Lib**: `networkx`, `tracemalloc`. **Logic**: 1) Build graph. 2) Write raw graph to `data/processed/graph_{scenario}_prelim.graphml`. 3) **If `node_count > 5000` OR `peak_memory > 7GB`**: Extract Largest Connected Component (LCC). If LCC node count > 5000 or memory still > 7GB, randomly subsample edges/nodes within LCC to reach 5000 nodes and < 7GB. **4) If `node_count <= 5000` AND `peak_memory <= 7GB`**: Retain graph as-is. **Output**: Write final graph to `data/processed/graph_{scenario}_subsampled.graphml` and write SHA256 hash to `data/processed/graph_{scenario}_subsampled.hash`. **Rule**: Ensure logic explicitly branches on the 5000 nodes OR 7GB RAM thresholds to avoid unnecessary processing of valid small graphs.
- [X] T009 Implement `code/data/splits.py` for Temporal Holdout validation strategy (Train on first [deferred] of time-windowed flows, test on remaining [deferred], configurable via `config.temporal_split_ratio`). **Output**: Write `data/processed/train_split.csv` and `data/processed/test_split.csv`.
- [X] T041 [P] Implement `code/utils/state_manager.py`: Function to read `data/processed/*.hash` sidecar files, verify hash against source file, aggregate hashes into a JSON map, and update the `artifact_hashes` map in `state/projects/PROJ-041-evaluating-the-use-of-graph-neural-netwo.yaml`. **Dependency**: Depends on T017, T025, T035.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Construct and Validate Network Traffic Graphs (Priority: P1) 🎯 MVP

**Goal**: Ingest raw NetFlow records, construct directed communication graphs, and verify memory safety (<7GB) and node limits (≤5,000).

**Independent Test**: Run `code/data/ingest_netflow.py` and `code/data/preprocess.py` on a single scenario; verify peak memory <7GB and graph object integrity.

### Tests for User Story 1 (Write Skeletons First)

> **NOTE**: Write these test **skeletons** FIRST (T010-T012), then implement code (T013-T017), then run tests.
> **Dependency**: T010-T012 depend on T013 interface definition.

- [X] T010 [US1] Write test skeleton for graph construction memory limit in `tests/test_memory_limits.py` (asserts `tracemalloc` < 7GB) [Depends on T013]
- [X] T011 [US1] Write test skeleton for node count subsampling in `tests/test_graph_construction.py` (asserts nodes ≤ 5,000, LCC rule) [Depends on T008, T013]
- [X] T012 [US1] Write test skeleton for data ingestion pipeline in `tests/integration/test_ingest.py` (verifies real data fetch and schema compliance) [Depends on T013]

### Implementation for User Story 1

- [X] T013 [US1] Implement graph builder in `code/data/preprocess.py`: Nodes=IPs, Edges=flows, Weights=packet counts. **Output**: Write raw graph to `data/processed/graph_{scenario}_raw.graphml`.
- [X] T015 [US1] Implement memory guard in `code/utils/memory_monitor.py`: Raise controlled error if limit exceeded
- [X] T016 [US1] Add validation checks in `code/data/preprocess.py`: Ensure edge weights are non-negative integers, handle missing labels
- [ ] T017 [US1] Write graph artifacts to `data/processed/graph_{scenario}_subsampled.graphml`. **Requirement**: For each written file, calculate SHA256 hash and write it to a sidecar file `data/processed/graph_{scenario}_subsampled.hash` containing only the hash string.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compare GNN Performance Against Feature-Engineered Baselines (Priority: P2)

**Goal**: Train a multi-layer GCN (CPU-only) and baselines (RF, XGBoost) to compare predictive value of graph structure.

**Independent Test**: Train models on fixed split, evaluate on held-out test set, record metrics (Precision, Recall, F1, AUC-ROC).

### Tests for User Story 2 (Write Skeletons First)

> **Dependency**: T018-T020 depend on T021/T022 interface definition.

- [X] T018 [US2] Write test skeleton for GCN convergence on CPU in `tests/test_models.py` (asserts no CUDA errors, converges ≤30 epochs) [Depends on T021]
- [X] T019 [US2] Write test skeleton for baseline training in `tests/test_models.py` (asserts RF/XGBoost produce predictions) [Depends on T022]
- [X] T020 [US2] Write test skeleton for Temporal Holdout split in `tests/integration/test_splits.py` (verifies no data leakage) [Depends on T009]

### Implementation for User Story 2

- [X] T021 [P] [US2] [Depends on T017] Implement 2-layer GCN in `code/models/gcn.py`: CPU-only, a limited number of epochs, early stopping (patience=5, delta=1e-4)
- [ ] T022 [P] [US2] [Depends on T017] Implement Random Forest and XGBoost wrappers in `code/models/baselines.py`: Use structural features (degree, centrality, variance)
- [ ] T023 [US2] [Depends on T021, T022] Implement evaluation metrics in `code/models/metrics.py`: Precision, Recall, F1-Score, AUC-ROC calculation
- [ ] T024 [US2] [Depends on T021, T022] Implement training loop in `code/main.py`: Orchestrates GCN and Baseline training with multiple random seeds. **Output**: Write model artifacts to `data/models/gcn_{seed}.pt` and `data/models/baseline_{seed}.pkl`.
- [ ] T025 [US2] Write results to `data/results/metrics_{scenario}_{model}.json`
- [ ] T026 [US2] Add logging for model convergence failures and fallback to baseline

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Identify Predictive Structural Patterns and Validate Significance (Priority: P3)

**Goal**: Analyze feature importance, apply statistical corrections (Permutation Tests + Benjamini-Hochberg), and identify predictive patterns.

**Note on Statistical Method**: The Plan deviates from Spec FR-006 (Wilcoxon) to **Permutation Tests** for small N (<13). This task implements Permutation Tests as per Plan.

**Independent Test**: Run significance tests on model outputs; verify adjusted p-values and feature rankings.

### Tests for User Story 3 (Write Skeletons First)

> **Dependency**: T027-T029 depend on T030/T031b implementation details.

- [ ] T027 [US3] Write test skeleton for Permutation Test logic in `tests/test_significance_tests.py` (validates p-value calculation for small N) [Depends on T030]
- [ ] T028 [US3] Write test skeleton for Benjamini-Hochberg correction in `tests/test_significance_tests.py` (validates FDR < 0.05 (1906.01701, https://arxiv.org/abs/1906.01701) threshold) [Depends on T031b]
- [ ] T029 [US3] Write test skeleton for Integrated Gradients attribution in `tests/integration/test_attribution.py` [Depends on T033]

### Implementation for User Story 3

- [ ] T030 [P] [US3] [Depends on T025] Implement Permutation Tests in `code/analysis/significance_tests.py`: permutations, alpha=0.05. **Hypothesis Set**: Must explicitly target the comparisons required by FR-006: (1) GCN vs RF, (2) GCN vs XGB, and (3-7) Top 5 structural features vs null baseline. **Trace**: [Plan Deviation 1: Wilcoxon->Permutation for N<13]. **Output**: Write `data/results/model_pair_pvalues.json` containing p-values for the model pair comparisons.
- [ ] T032 [P] [US3] Implement Random RF feature importance ranking in `code/analysis/attribution.py`. **Logic**: 1) Extract top structural features by importance score. 2) **Output Constraint**: Must write `data/results/feature_importance_ranking.json` containing **a subset of the top features** in the format: `{"features": ["feat1",...], "importance_scores": [val,...], "p_values": [val,...]}`. 3) For each of these top 5 features, perform a Permutation Test against a null baseline (shuffled labels) to generate a p-value. **Dependency**: Output format must be strictly parsable by T031b.
- [ ] T031b [P] [US3] [Depends on T030, T032] Construct the exact multi-comparison hypothesis set: **Input**: `data/results/model_pair_pvalues.json` (Statistical significance assessment via p-values) + `data/results/feature_importance_ranking.json` (p-values

The specific value to remove/generalize: 'a small set of'

Rewritten passage:
A small set of p-values from T032). **Action**: Merge these into a single list of p-values. **Action**: Apply Benjamini-Hochberg correction to this list. **Output**: Write `data/results/bh_corrected_pvalues.json`. **Verification**: Ensure the A series of comparisons will be conducted to address the research question using the established method, as outlined in the relevant literature (DOI/arXiv/author-year). match FR-006 exactly.
- [ ] T033 [US3] Implement Integrated Gradients for GNN in `code/analysis/attribution.py`: Map embeddings to structural proxies. **Output**: Write `data/results/gnn_attribution_{scenario}.json`.
- [ ] T033b [US3] [Depends on T032, T033] Implement "Distinct Ranking Artifact" generation: **Input**: RF Top-5 (from T032) and GNN Top-5 (from T033). **Logic**: **Step 1**: Map GNN Integrated Gradients to the **same structural proxy names** used by RF to ensure valid comparison. **Step 2**: A pattern is "distinct" if (1) its rank in GNN list differs by >2 positions from its rank in RF list, OR (2) it appears in GNN Top-5 but not RF Top-5. **Output**: Write `data/results/distinct_ranking.json` listing only these distinct patterns.
- [ ] T034 [US3] Implement correlation analysis in `code/analysis/significance_tests.py`: Degree-based vs temporal-based patterns
- [ ] T035 [US3] Write final statistical report to `data/results/significance_report.json` and plots to `data/results/`
- [ ] T035b [US3] Enforce Target AUC Threshold in `code/models/metrics.py`: Read threshold from `code/config.yaml` (key: `target_auc`, default a threshold value). **Note**: Per Plan.md (Research Section), this value is defined in the research plan's config section; 0.75 is the default placeholder.

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
- [ ] T040 [P] Run `quickstart.md` validation: Execute `python code/utils/verify_hashes.py` to verify all artifacts in `data/processed` have corresponding `.hash` sidecar files and that the `state/projects/PROJ-041-...yaml` file is up to date.
- [ ] T002b [P] Implement `code/utils/verify_hashes.py`: Script that scans `data/processed/*.hash`, reads the hash, recalculates the file hash, compares them, and if valid, updates `state/projects/PROJ-041-evaluating-the-use-of-graph-neural-netwo.yaml` `artifact_hashes` map.

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

- Test Skeletons (T010-T012, T018-T020, T027-T029) MUST be written AFTER their respective implementation tasks (T013, T021/T022, T030/T033) to ensure interface definitions are available.
- Implementation follows Test Skeletons (once interfaces are defined).
- Tests are executed after Implementation.
- Story complete before moving to next priority.

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all Test Skeletons for User Story 1 together (after T013 is defined):
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
- Verify test skeletons are written after interface definition (implementation tasks)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Data Integrity**: All tasks consuming data must use the real dataset fetched in T007a/T007b; no synthetic data generation.
- **Hardware Constraints**: All model training (T021, T022) must run on CPU without CUDA/quantization.
- **Statistical Deviation**: T030 implements Permutation Tests instead of Wilcoxon (Spec FR-006) as per Plan.md deviation for small sample sizes [Plan Deviation 1].
- **Subsampling Rule**: T008 strictly enforces "Largest Connected Component only" (no padding, no anomaly-preservation heuristics) per FR-002 and Constitution Principle VI, with explicit logic to trigger on `node_count > 5000` OR `peak_memory > 7GB`.
- **Temporal Split Clarity**: T009 and T020 explicitly enforce the "Train on first [deferred] (config.temporal_split_ratio=0.8), Test on remaining [deferred]" split to prevent leakage.
- **Small Sample Robustness**: T030 and T031 explicitly implement Permutation Tests and BH correction to ensure validity given N < 13 scenarios, preserving the 7-comparison hypothesis set.
- **Target AUC Threshold**: T035b enforces the threshold defined in `code/config.yaml` (default 0.75) as per SC-005 and Plan.md.
- **Artifact Hashing**: T017 writes sidecar `.hash` files; T040/T041 read these to update state.
- **Distinct Patterns**: T033b defines "distinct" as rank-diff > 2 or presence in GNN Top-5 but not RF Top-5, with mandatory proxy-name alignment.
- **P-Value Chain**: T032 explicitly generates p-values for the top 5 features via permutation testing to satisfy the 7-comparison hypothesis set required by FR-006 and T031b, with explicit JSON output format.
- **Notes Correction**: The "Rejected" section previously mentioned T001a; this was corrected to T001 in the main task list.