# Tasks: Predicting the Elastic Moduli of 2D Materials from Structure-Only Models

**Input**: Design documents from `/specs/001-predicting-the-elastic-moduli/`
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

**Purpose**: Project initialization, title correction, and basic structure

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate/`)
- [x] T001a Update project title and terminology in `spec.md`, `plan.md`, and this `tasks.md` to "Structure-Only Surrogate Model" (replacing "First-Principles Calculations" to resolve contradiction)
- [X] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup environment configuration management in `code/utils/config.py` (seeding, paths, CPU limits)
- [X] T005 Implement logging infrastructure in `code/utils/logger.py` (structured logs for bias checks)
- [X] T006 Create base constants and conversion factors in `code/utils/constants.py` (elastic modulus units)
- [X] T007 Define the `MaterialGraph` data schema in `code/data_models/material_graph.py` (nodes, edges, targets)
- [ ] T008 Implement dynamic sampling strategy and data volume verification in `code/utils/memory_utils.py` to guarantee 7GB RAM limit (required for FR-007/SC-004)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Graph Construction (Priority: P1) 🎯 MVP

**Goal**: Download CIF files and elastic tensors from public repositories, filter for 2D materials, and convert to graph representations using a unified canonical source.

**Independent Test**: The script can be run to download a subset of materials, parse their CIFs into graphs using `pymatgen`, and output a JSON/CSV summary of node counts, edge counts, and target values without requiring any model training.

### Implementation for User Story 1

- [X] T009 [US1] Implement unified dataset loader in `code/ingest/download.py` that abstracts Materials Project/AFLOW into a single canonical source per run (satisfying Constitution Principle I) and explicitly documents data is from *existing* DFT (not generated here)
- [ ] T010 [US1] Implement CIF parser in `code/ingest/parse_cif.py` (convert to `MaterialGraph` using `pymatgen`, extract node/edge features)
- [X] T011 [US1] Implement 2D filter and tensor validator in `code/ingest/filter.py` (exclude entries with missing 6-component tensors or non-2D layers)
- [X] T012 [US1] Implement bias check for excluded entries in `code/ingest/bias_check.py` (log reasons for exclusion, flag small families)
- [~] T013 [US1] Create data pipeline orchestration script in `code/ingest/pipeline.py` (download -> parse -> filter -> save to `data/processed/graphs_v1.parquet`)
- [X] T014 [US1] Add unit tests for CIF parsing logic in `tests/unit/test_parse_cif.py` (verify disconnected graph handling)
- [X] T015 [US1] Add unit tests for tensor validation in `tests/unit/test_filter.py` (verify 6-component requirement)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Lightweight GNN Training and Evaluation (Priority: P2)

**Goal**: Train a lightweight GNN on the constructed dataset to predict elastic moduli and evaluate performance against held-out DFT values, including intra-family baseline and inter-family drop.

**Independent Test**: The training script can be executed on a CPU-only environment, training for a specified number of epochs, and outputting a JSON report with MAPE, RMSE, and R² scores for the test set.

### Implementation for User Story 2

- [X] T016 [P] [US2] Define lightweight GNN architecture in `code/model/gnn.py` (2-3 layers, hidden dim ≤64, CPU-only `torch_geometric`)
- [X] T017 [US2] Implement stratified splitting logic in `code/model/splitter.py` (split by chemical prototype/space group to ensure family separation)
- [ ] T018 [US2] Implement training loop with early stopping in `code/model/train.py` (patience=3, CPU execution, logging to `data/results/training_logs.json`, explicit warning that model is a *surrogate* for DFT)
- [ ] T019 [US2] Implement evaluation and metrics calculation in `code/model/eval.py` (MAPE, RMSE, R² for Young's, Shear, Poisson)
- [X] T020 [US2] Implement a k-fold cross-validation runner in `code/model/cv_runner.py`
- [ ] T020a [US2] Implement intra-family baseline metric generation in `code/model/baseline_metrics.py` (compute MAPE/RMSE on random splits within families to establish baseline for SC-002)
- [~] T021 [US2] Implement inter-family generalization test in `code/model/generalization_test.py` (measure MAPE drop on unseen families vs intra-family baseline; output `data/results/generalization_metrics.json`)
- [X] T022 [US2] Add integration test for full training pipeline on sample data in `tests/integration/test_pipeline.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance and Ablation Analysis (Priority: P3)

**Goal**: Identify which structural descriptors most strongly influence predicted elastic moduli and understand the contribution of different descriptor classes.

**Independent Test**: The analysis script can run on the trained model to generate SHAP values and ablation study results, outputting a single unified ranked list and performance deltas.

### Implementation for User Story 3

- [ ] T025 [US3] Implement composition-only baseline model in `code/analysis/ablation.py` (feed-forward network on Magpie descriptors, no topology)
- [X] T023 [US3] Implement SHAP interaction value calculation in `code/analysis/importance.py` (using `shap` library on GNN inputs, must run after T018/T025)
- [ ] T024 [US3] Implement permutation importance calculation in `code/analysis/importance.py` (rank top 5 structural descriptors, must run after T018/T025)
- [ ] T026 [US3] Implement ablation study runner in `code/analysis/ablation.py` (compare full GNN vs. composition-only, report MAPE delta)
- [ ] T027 [US3] Generate final analysis report in `code/analysis/report_generator.py` (must synthesize SHAP and permutation into a **single unified ranked list**; output `data/results/feature_importance_report.md` with ablation deltas; frame findings as correlations)
- [ ] T028 [US3] Add unit tests for SHAP value aggregation in `tests/unit/test_importance.py`

**Checkpoint**: All user stories should now be independently functional

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 (needs `data/processed/` graphs)
- **User Story 3 (P3)**: Depends on US2 (needs trained model and metrics)

### Within Each User Story

- **US1**: T009 -> T010 -> T011 -> T012 -> T013 (Sequential data flow)
- **US2**: T017 (Split) -> T018 (Train) -> T020a (Baseline) -> T021 (Generalization)
- **US3**: T025 (Baseline Train) -> T018 (Main Train) -> T023/T024 (Importance) -> T026 (Ablation) -> T027 (Report)

### Parallel Opportunities

- **Setup**: T002, T003 can run in parallel after T001/T001a.
- **Foundational**: T004-T007 can run in parallel.
- **US1**: T014, T015 can run in parallel after T009-T012.
- **US2**: T016, T022 can run in parallel; T020a and T021 depend on T018.
- **US3**: T028 can run in parallel with T027 after T023-T026.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (including T001a title correction)
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify data download and graph construction)
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
- **CRITICAL**: All artifacts now correctly use "Structure-Only Surrogate Model" terminology.
- **Memory Constraint**: T008 must implement dynamic sampling to guarantee 7GB limit.
- **Data Constraint**: T009 must enforce single canonical source per run.
- **Metric Constraint**: T020a + T021 must compute intra/inter family drop for SC-002.
- **Report Constraint**: T027 must output a single unified ranked list.
- **Review Address**: T001a explicitly resolves the "First-Principles" vs "Curve-Fitting" contradiction raised by the Feynman review by renaming the project to "Structure-Only Surrogate Model" and ensuring all documentation reflects that the model interpolates DFT data rather than solving the Schrödinger equation.
