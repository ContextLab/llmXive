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

- [X] T001a [P] Create code directories: `code/data`, `code/models`, `code/analysis`, `code/utils`
- [X] T001b [P] Create data directories: `data/raw`, `data/processed`, `data/results`
- [X] T001c [P] Create test directories: `tests`, `tests/integration`, `tests/unit`
- [X] T002 Initialize Python project with `requirements.txt` (pinning `torch` CPU version, `networkx`, `scikit-learn`, `xgboost`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `captum`, `pytest`, `pytest-memory-profiler`)
- [X] T003 [P] Configure linting (`ruff`) and formatting (`black`) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/utils/seed.py` to manage deterministic random seeds
- [X] T005 Implement `code/utils/memory_monitor.py` wrapper using `tracemalloc` to enforce a hard memory limit
- [X] T002c [P] Implement `code/utils/verify_hashes.py`: Script that scans `data/processed/*.hash`, reads the hash, recalculates the file hash, compares them, and if valid, updates `state/projects/PROJ-041-evaluating-the-use-of-graph-neural-netwo.yaml` `artifact_hashes` map.
- [X] T006 Create `contracts/dataset.schema.yaml` and `contracts/graph.schema.yaml` defining data structures
- [ ] T007a [P] Download CTU dataset from direct URL: ` (or specific scenario zip) and validate checksum. **Note**: Use the direct file link from the Stratosphere IPS repository, not the landing page.
- [ ] T007b [P] Download the NF-BoT-IoT dataset from direct release URL: ` and validate the checksum (Fallback).
- [X] T007c [P] Implement fallback logic in `code/data/ingest_netflow.py`: Check CTU availability; if missing, switch to BoT-IoT. **Requirement**: Upon switching, immediately write the specific dataset URL, version, and checksum to `state/projects/PROJ-041-evaluating-the-use-of-graph-neural-netwo.yaml` to preserve Single Source of Truth.
- [X] T007d [P] Define `Target AUC Threshold` in `code/config.yaml` (key: `target_auc`, default:). **Note**: Per Plan.md (Research Section), the specific value is defined in the research plan; `config.yaml` acts as the implementation carrier. The Plan mandates this parameter exists in config.yaml as the source of truth for the threshold.
- [ ] T009 [P] [US2] [Depends on T007a/T007b] Implement Temporal Holdout split in `code/data/splits.py`. **Logic**: 1) Load raw flows. 2) Sort by timestamp. 3) Split into Train (majority portion) and Test (remaining portion). 4) **CRITICAL**: Construct the graph *only* on the Train subset flows to prevent temporal leakage. 5) Validate that no edges in the Train graph connect to nodes that appear *only* in the Test period. **Output**: Write `data/processed/train_split.csv`, `data/processed/test_split.csv`, and `data/processed/graph_train_split.graphml`. **Rule**: Graph construction MUST occur after the split.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Construct and Validate Network Traffic Graphs (Priority: P1) 🎯 MVP

**Goal**: Ingest raw NetFlow records, construct directed communication graphs, and verify memory safety (<7GB) and node limits (≤5,000).

**Independent Test**: Run `code/data/ingest_netflow.py` and `code/data/preprocess.py` on a single scenario; verify peak memory <7GB and graph object integrity.

### Implementation for User Story 1 (Interface First)

- [X] T013 [US1] [P] Define Graph Builder Interface in `code/data/preprocess.py`. **Action**: Define the function signatures, input data contracts (schema), and output data contracts (graph object structure, metadata) for the graph builder. **Output**: Write interface stubs to `code/data/preprocess.py` (no full implementation yet). **Note**: This task defines the API for T010-T012 tests.

### Tests for User Story 1 (Write Skeletons First)

> **NOTE**: Write these test **skeletons** FIRST (T010-T012), then implement code (T013b), then run tests.
> **Dependency**: T010-T012 depend on T013 Interface definition (not full implementation).

- [ ] T010 [US1] Write test skeleton for graph construction memory limit in `tests/test_memory_limits.py` (asserts `tracemalloc` < 7GB). **Invocation**: Wrap the call to `preprocess.py` with `memory_monitor.py` to capture peak memory. [Depends on T013 Interface]
- [ ] T011 [US1] Write test skeleton for node count subsampling in `tests/test_graph_construction.py` (asserts nodes ≤ 5,000, LCC rule) [Depends on T013 Interface]
- [ ] T012 [US1] Write test skeleton for data ingestion pipeline in `tests/integration/test_ingest.py` (verifies real data fetch and schema compliance) [Depends on T013 Interface]

### Implementation for User Story 1 (Full Logic)

- [X] T013b [US1] [Depends on T013] Implement full graph builder logic in `code/data/preprocess.py`: Nodes=IPs, Edges=flows, Weights=packet counts. **Output**: Write raw graph to `data/processed/graph_{scenario}_raw.graphml`.
- [X] T015 [US1] [P] Implement memory guard in `code/utils/memory_monitor.py`: Raise controlled error if limit exceeded. **Note**: T008a and T008c depend on this logic.
- [X] T016 [US1] Add validation checks in `code/data/preprocess.py`: Ensure edge weights are non-negative integers, handle missing labels

### Subsampling Logic (Plan Deviation Authorized)

- [ ] T008c [US1] [P] **Authorize Degree-Based Subsampling**: **Input**: `plan.md` (Plan Deviation section). **Action**: Document the Plan Deviation that authorizes the secondary heuristic (degree-based selection) when LCC > 5000. **Rationale**: Explicitly state that retaining only LCC may discard critical anomaly hubs; degree-based selection preserves topological meaningfulness and anomaly distribution. **Output**: Write `data/processed/subsampling_authorization.md` containing the deviation citation and rationale. **Dependency**: Depends on T015 (for memory check logic).
- [ ] T008a [US1] [P] [Depends on T013b, T015, T008c] Implement LCC extraction in `code/data/preprocess.py`. **Input**: `data/processed/graph_{scenario}_raw.graphml`. **Logic**: 1) Check `node_count > 5000` OR `peak_memory > 7GB`. 2) **If True**: Extract Largest Connected Component (LCC). 3) Write intermediate LCC graph to `data/processed/graph_{scenario}_lcc.graphml`. **Output**: LCC graph. **Dependency**: Depends on T015 (memory check) and T008c (authorization).
- [ ] T008b [US1] [P] [Depends on T008a, T008c] Implement degree-based subsampling in `code/data/preprocess.py`. **Input**: `data/processed/graph_{scenario}_lcc.graphml`. **Logic**: 1) If LCC > 5000: Retain top 5000 nodes with highest degree centrality. 2) **Tie-breaking**: Use global seed from `code/utils/seed.py` (sort by degree desc, then by IP string asc). 3) Write final graph to `data/processed/graph_{scenario}_subsampled.graphml`. **Output**: Final graph. **Dependency**: Depends on T008c (authorization).
- [ ] T017 [US1] [Depends on T008b] Write graph artifacts to `data/processed/graph_{scenario}_subsampled.graphml`. **Requirement**: For each written file, calculate SHA256 hash and write it to a sidecar file `data/processed/graph_{scenario}_subsampled.hash` containing only the hash string.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compare GNN Performance Against Feature-Engineered Baselines (Priority: P2)

**Goal**: Train a multi-layer GCN (CPU-only) and baselines (RF, XGBoost) to compare predictive value of graph structure.

**Independent Test**: Train models on fixed split, evaluate on held-out test set, record metrics (Precision, Recall, F1, AUC-ROC).

### Tests for User Story 2 (Write Skeletons First)

> **Dependency**: T018-T020 depend on T021/T022 interface definition.

- [ ] T018 [US2] Write test skeleton for GCN convergence on CPU in `tests/test_models.py` (asserts no CUDA errors, converges ≤30 epochs) [Depends on T021 Interface]
- [ ] T019 [US2] Write test skeleton for baseline training in `tests/test_models.py` (asserts RF/XGBoost produce predictions) [Depends on T022 Interface]
- [ ] T020 [US2] Write test skeleton for Temporal Holdout split in `tests/integration/test_splits.py` (verifies no data leakage) [Depends on T009]

### Implementation for User Story 2

- [X] T021 [P] [US2] [Depends on T017] Implement a multi-layer Graph Convolutional Network (GCN). in `code/models/gcn.py`: CPU-only, 30 epochs, early stopping (patience=5, delta=1e-4)
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
- [ ] T028 [US3] Write test skeleton for Benjamini-Hochberg correction in `tests/test_significance_tests.py` (validates FDR < 0.05 threshold) [Depends on T031b]
- [ ] T029 [US3] Write test skeleton for Integrated Gradients attribution in `tests/integration/test_attribution.py` [Depends on T033]

### Implementation for User Story 3

- [ ] T032a [P] [US3] [Independent of T022] **Define A Priori Hypothesis Set**: **Action**: Define the list of comparisons required by FR-006. **Features**: `degree`, `betweenness_centrality`, `clustering_coefficient`, `edge_weight_variance`, `page_rank`. **Comparisons**: (1) GCN vs RF, (2) GCN vs XGB, (3-7) Top 5 features vs. null baseline. **Output**: Write `data/results/hypothesis_set_definition.json` listing the a fixed number of comparisons. **Constraint**: This task MUST NOT depend on T022 or model outputs.
- [ ] T030a [US3] [P] [Depends on T032a] **Justify Statistical Power & Deviation**: **Action**: Document the statistical power comparison between Wilcoxon (Spec FR-006) and Permutation Tests (Plan Deviation 1). **Justification**: Explicitly state that with N<13 scenarios, Wilcoxon has insufficient power to detect differences, whereas Permutation Tests are robust for small samples. **Trace**: Cite `plan.md` 'Plan Deviation 1'. **Output**: Write `data/results/statistical_power_justification.md`. **Note**: This task creates the audit trail for the method deviation.
- [ ] T030b [US3] [P] [Depends on T030a, T032a] Implement Permutation Tests in `code/analysis/significance_tests.py`: permutations, alpha=0.05. **Hypothesis Set**: Must explicitly target the comparisons defined in T032a: (1) GCN vs RF, (2) GCN vs XGB. **Trace**: [Plan Deviation 1: Wilcoxon->Permutation for N<13]. **Output**: Write `data/results/model_pair_pvalues.json` containing p-values for the model pair comparisons.
- [ ] T032b [P] [US3] [Depends on T030a, T032a] Implement Permutation Tests for Features: **Input**: `data/results/hypothesis_set_definition.json`. **Logic**: For each of the top structural features defined in T032a, perform a Permutation Test against a null baseline (shuffle labels repeatedly to assess statistical significance). **Trace**: [Plan Deviation 1]. **Output**: Write `data/results/feature_pvalues.json`.
- [ ] T031b [P] [US3] [Depends on T030b, T032b] Apply Benjamini-Hochberg correction: **Input**: `data/results/model_pair_pvalues.json` and `data/results/feature_pvalues.json`. **Logic**: Merge p-values into a single list. Sort by p-value ascending. Apply BH correction formula. **Output**: Write `data/results/bh_corrected_pvalues.json`. **Verification**: Ensure a set of comparisons are processed.
- [ ] T033 [US3] [P] Implement Integrated Gradients for GNN in `code/analysis/attribution.py`: Map embeddings to structural proxies. **Output**: Write `data/results/gnn_attribution_{scenario}.json`.
- [ ] T033c [US3] [P] [Depends on T033] Define Proxy Mapping: **Action**: Define the mapping logic from GNN Integrated Gradients to the **same structural proxy names** used by RF (degree, betweenness, etc.). **Output**: Write `data/results/proxy_mapping.json`.
- [ ] T033d [US3] [P] [Depends on T033c] Implement Bootstrap Confidence Intervals: **Input**: `data/results/gnn_attribution_{scenario}.json`, `data/results/proxy_mapping.json`. **Logic**: Resample predictions multiple times to assess stability.. Compute % confidence interval for the rank difference of each feature between GNN and RF. **Output**: Write `data/results/rank_diff_ci.json`.
- [ ] T033e [US3] [P] [Depends on T033d] Generate Distinct Ranking Artifact: **Input**: `data/results/rank_diff_ci.json`, `data/results/gnn_attribution_{scenario}.json`, `data/results/proxy_mapping.json`. **Logic**: **Step 1**: Map GNN Integrated Gradients to structural proxy names. **Step 2**: A pattern is "distinct" if and only if the 95% CI for its rank difference **excludes 0**. **Output**: Write `data/results/distinct_ranking.json` listing only these statistically distinct patterns. **Note**: Non-statistical heuristics (e.g., presence/absence) are descriptive but do not qualify a pattern as "distinct" for SC-003.
- [ ] T034 [US3] Implement correlation analysis in `code/analysis/significance_tests.py`: Degree-based vs temporal-based patterns
- [ ] T035 [US3] Write final statistical report to `data/results/significance_report.json` and plots to `data/results/`
- [ ] T035c [US3] [P] Enforce Target AUC Threshold: **Input**: `research.md` (from `specs/.../research.md`), `code/config.yaml`. **Logic**: 1) Read `target_auc` value from `research.md`. 2) Verify `config.yaml` matches. 3) If mismatch, raise error. 4) Enforce threshold in metrics evaluation. **Output**: Update `code/config.yaml` with verified value. **Note**: `research.md` is the source of truth for the threshold value.

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
- [ ] T040 [P] Run `quickstart.md` validation: Execute `python code/utils/verify_hashes.py` to verify all artifacts in `data/processed` have corresponding `.hash` sidecar files and that the `state/projects/PROJ-041-...yaml` file is up to date. [Depends on T002c]
- [ ] T041 [P] Implement `code/utils/state_manager.py`: Function to read `data/processed/*.hash` sidecar files, verify hash against source file, aggregate hashes into a JSON map, update the `artifact_hashes` map in `state/projects/PROJ-041-evaluating-the-use-of-graph-neural-netwo.yaml`, **AND UPDATE THE `updated_at` TIMESTAMP** in the same operation. **Dependency**: Depends on T017, T025, T035.

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

- Test Skeletons (T010-T012, T018-T020, T027-T029) MUST be written AFTER their respective interface definitions (T013, T021/T022, T030/T033) to ensure interface definitions are available.
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
# Launch all Test Skeletons for User Story 1 together (after T013 interface is defined):
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
- **Statistical Deviation**: T030a/T030b implement Permutation Tests instead of Wilcoxon (Spec FR-006) as per Plan.md deviation for small sample sizes [Plan Deviation 1]. T030a explicitly documents the statistical power justification.
- **Subsampling Rule**: T008c (Authorization), T008a (LCC), and T008b (Degree Subsampling) strictly enforce the subsampling logic with explicit Plan Deviation citation for the degree-based fallback.
- **Temporal Split Clarity**: T009 and T020 explicitly enforce the "Split first, then construct graph on train subset" strategy to prevent leakage.
- **Small Sample Robustness**: T030a, T030b, T032a, T032b, and T031b explicitly implement Permutation Tests and BH correction to ensure validity given N < 13 scenarios, preserving the 7-comparison hypothesis set defined a priori in T032a.
- **Target AUC Threshold**: T035c enforces the threshold defined in `research.md` (source of truth) with mandatory verification against `code/config.yaml`.
- **Artifact Hashing**: T017 writes sidecar `.hash` files; T040/T041 read these to update state.
- **Distinct Patterns**: T033e defines "distinct" ONLY if the 95% CI for rank difference excludes 0 (statistical significance), removing non-statistical heuristics as validity gates for SC-003.
- **P-Value Chain**: T032b explicitly generates p-values for the top features via permutation testing to satisfy the 7-comparison hypothesis set required by FR-006 and T031b, with explicit JSON output format.
- **Notes Correction**: The "Rejected" section previously mentioned T001a; this was corrected to T001 in the main task list.