# Tasks: Structure-Only Surrogate Model for 2D Material Elastic Moduli

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

- [ ] T001 Create project structure: Create directories `code/`, `data/raw/`, `data/processed/`, `data/results/`, `tests/unit/`, `tests/integration/`, `docs/`. Create `README.md` with reproducibility instructions (referencing Constitution Principle I) and `.gitignore` with specific patterns: `data/*`, `!data/processed/*`, `!data/results/*`, `__pycache__`, `*.pyc`, `.env`.
- [ ] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt`: Include `pymatgen`, `torch`, `torch-geometric`, `shap`, `pandas`, `numpy`, `scikit-learn`, `ruff`, `black`.
- [ ] T003 Configure linting (ruff) and formatting (black) tools: Create `.ruff.toml` with strict rules (E, F, W, I) and `.black.toml` with line-length=88.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup environment configuration management in `code/utils/config.py` (seeding, paths, CPU limits)
- [ ] T005 Implement logging infrastructure in `code/utils/logger.py` (structured logs for bias checks)
- [ ] T006 Create base constants and conversion factors in `code/utils/constants.py` (elastic modulus units)
- [ ] T007 Define the `MaterialGraph` data schema in `code/data_models/material_graph.py` (nodes, edges, targets)
- [ ] T008 Implement dynamic sampling strategy and full-pipeline memory verification in `code/utils/memory_utils.py` to guarantee 7GB RAM limit. **Requirement**: Implement a unit test in `tests/unit/test_memory_utils.py` that simulates the entire data loading and training loop and asserts memory usage < 7GB. (required for FR-007/SC-004)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Graph Construction (Priority: P1) 🎯 MVP

**Goal**: Download CIF files and elastic tensors from public repositories, filter for 2D materials, and convert to graph representations using a unified canonical source.

**Independent Test**: The script can be run to download a subset of materials, parse their CIFs into graphs using `pymatgen`, and output a JSON/CSV summary of node counts, edge counts, and target values without requiring any model training.

### Implementation for User Story 1

- [ ] T009 [US1] Implement unified dataset loader in `code/ingest/download.py` that abstracts Materials Project/AFLOW into a single canonical source per run (satisfying Constitution Principle I) and explicitly documents data is from *existing* DFT (not generated here). **Requirement**: Include a "Warning" docstring stating: "WARNING: This model is a surrogate interpolating pre-computed DFT results. It does NOT solve the Schrödinger equation or perform first-principles calculations."
- [ ] T009a [US1] Implement runtime source enforcement in `code/ingest/download.py` (or separate `code/ingest/validator.py`): Add a check that raises a hard error if more than one data source is active in a single run, satisfying the "single canonical source" constraint.
- [ ] T010 [US1] Implement CIF parser in `code/ingest/parse_cif.py` (convert to `MaterialGraph` using `pymatgen`, extract node/edge features)
- [ ] T011 [US1] Implement 2D filter and tensor validator in `code/ingest/filter.py` (exclude entries with missing 6-component tensors or non-2D layers)
- [ ] T012 [US1] Implement bias check for excluded entries in `code/ingest/bias_check.py` (log reasons for exclusion, flag small families)
- [ ] T013 [US1] Create data pipeline orchestration script in `code/ingest/pipeline.py` (download -> parse -> filter -> save to `data/processed/graphs_v1.parquet`). **Requirement**: Output schema MUST include `node_features`, `edge_features`, `target_moduli`, `family_id`. Implement error handling for missing tensors.
- [ ] T014 [US1] Add unit tests for CIF parsing logic in `tests/unit/test_parse_cif.py` (verify disconnected graph handling)
- [ ] T015 [US1] Add unit tests for tensor validation in `tests/unit/test_filter.py` (verify 6-component requirement)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Lightweight GNN Training and Evaluation (Priority: P2)

**Goal**: Train a lightweight GNN on the constructed dataset to predict elastic moduli and evaluate performance against held-out DFT values, including intra-family baseline and inter-family drop.

**Independent Test**: The training script can be executed on a CPU-only environment, training for a specified number of epochs, and outputting a JSON report with MAPE, RMSE, and R² scores for the test set.

### Implementation for User Story 2

- [ ] T016 [P] [US2] Define lightweight GNN architecture in `code/model/gnn.py` (2-3 layers, hidden dim ≤64, CPU-only `torch_geometric`)
- [ ] T017 [US2] Implement stratified splitting logic in `code/model/splitter.py` (split by chemical prototype/space group to ensure family separation)
- [ ] T018 [US2] Implement training loop with early stopping in `code/model/train.py` (patience=3, CPU execution, logging to `data/results/training_logs.json`, explicit warning that model is a *surrogate* for DFT). **Requirement**: Log schema MUST include `epoch: int`, `loss: float`, `metrics: {mape, rmse}`, `memory_peak: float`.
- [ ] T019 [US2] Implement evaluation and metrics calculation in `code/model/eval.py` (MAPE, RMSE, R² for Young's, Shear, Poisson)
- [ ] T019a [US2] Implement success criteria assertion in `code/model/eval.py` or `code/model/eval_runner.py`: Calculate MAPE against held-out families and assert MAPE < 15% (or log failure if threshold not met).
- [ ] T020 [US2] Implement a k-fold cross-validation runner in `code/model/cv_runner.py`
- [ ] T020a [US2] Implement intra-family baseline metric generation in `code/model/baseline_metrics.py` (compute MAPE/RMSE on random splits within families to establish baseline for SC-002)
- [ ] T021 [US2] Implement inter-family generalization test in `code/model/generalization_test.py`: Dependency: T017, T018. Measure MAPE drop on unseen families vs intra-family baseline; output `data/results/generalization_metrics.json`. **Requirement**: Test set MUST consist of entirely excluded families. Implement a runtime check to ensure no training family appears in the test set. Output schema MUST include `intra_family_mape`, `inter_family_mape`, `drop_percentage`.
- [ ] T022 [US2] Add integration test for full training pipeline on sample data in `tests/integration/test_pipeline.py`
- [ ] T022a [US2] Add explicit "Surrogate Model" disclaimer to `data/results/training_logs.json` and `data/results/generalization_metrics.json`: Add a `metadata` key to the JSON object containing the disclaimer: "These results are ML interpolations of DFT data, not first-principles solutions."

**Checkpoint**: At this point, At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance and Ablation Analysis (Priority: P3)

**Goal**: Identify which structural descriptors most strongly influence predicted elastic moduli and understand the contribution of different descriptor classes.

**Independent Test**: The analysis script can run on the trained model to generate SHAP values and ablation study results, outputting a single unified ranked list and performance deltas.

### Implementation for User Story 3

- [ ] T025 [US3] Implement composition-only baseline model in `code/analysis/ablation.py` (feed-forward network on Magpie descriptors, no topology)
- [ ] T023 [US3] Implement SHAP interaction value calculation in `code/analysis/importance.py`: Dependency: T018 (produces trained model weights artifact), T017. (using `shap` library on GNN inputs)
- [ ] T024 [US3] Implement permutation importance calculation in `code/analysis/importance.py`: Dependency: T018 (produces trained model weights artifact), T017. (rank top structural descriptors)
- [ ] T026 [US3] Implement ablation study runner in `code/analysis/ablation.py` (compare full GNN vs. composition-only, report MAPE delta). Dependency: T025 AND T018.
- [ ] T027a [US3] Implement data aggregation script in `code/analysis/aggregate.py`: Combine SHAP, permutation, and generalization metrics into a single intermediate JSON.
- [ ] T027b [US3] Implement report template generation in `code/analysis/template.py`: Create the Markdown template for the final report.
- [ ] T027c [US3] Implement final report assembly in `code/analysis/report_generator.py`: Dependency: T027a, T027b. Synthesize into a **single unified ranked list**; output `data/results/feature_importance_report.md` with ablation deltas; frame findings as correlations. **Requirement**: Output format MUST be a Markdown table with columns: `Descriptor`, `Importance Score`, `p-value`, `Description`.
- [ ] T028 [US3] Add unit tests for SHAP value aggregation in `tests/unit/test_importance.py`
- [ ] T028a [US3] Ensure `data/results/feature_importance_report.md` explicitly states descriptors are statistical correlations: The report MUST state: "The identified descriptors are statistical correlations learned by the surrogate model from DFT data, not fundamental quantum mechanical variables derived from the Hamiltonian."

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Documentation & Compliance (Priority: P4)

**Goal**: Finalize all documentation to prevent the "First-Principles" vs "Curve-Fitting" contradiction identified in research reviews.

### Implementation for Phase 6

- [ ] T029 [P4] Update `README.md` to explicitly define the project as a "Surrogate Model" that interpolates DFT data, removing any ambiguity about solving the Schrödinger equation.
- [ ] T030 [P4] Create `docs/methodology.md` detailing the distinction between "First-Principles" (DFT) and "Surrogate" (ML) methods, citing the specific DFT sources used.
- [ ] T031 [P4] Update `docs/contributing.md` to enforce terminology guidelines: forbid the use of "First-Principles" to describe the ML model.
- [ ] T032 [P4] Add a "Limitations" section to `spec.md` explicitly stating the model cannot extrapolate beyond the chemical space of the training DFT data and does not discover new physics.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Documentation (Phase 6)**: Can run in parallel with US1-US2, but must be finalized before final release.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 (needs `data/processed/` graphs)
- **User Story 3 (P3)**: Depends on US2 (needs trained model and metrics)

### Within Each User Story

- **US1**: T009 -> T009a -> T010 -> T011 -> T012 -> T013 (Sequential data flow)
- **US2**: T017 (Split) -> T018 (Train) -> T020a (Baseline) -> T021 (Generalization) -> T019a (Threshold Check)
- **US3**: T025 (Baseline Train) AND T018 (Main Train) -> T023/T024 (Importance) -> T026 (Ablation) -> T027a -> T027b -> T027c (Report)

### Parallel Opportunities

- **Setup**: T002, T003 can run in parallel after T001.
- **Foundational**: T004-T007 can run in parallel.
- **US1**: T014, T015 can run in parallel after T009-T013.
- **US2**: T016, T022 can run in parallel; T020a and T021 depend on T018.
- **US3**: T028 can run in parallel with T027a-T027c after T023-T026.
- **Phase 6**: T029-T032 can run in parallel.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
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
- **Memory Constraint**: T008 must implement full-pipeline memory verification to guarantee 7GB limit.
- **Data Constraint**: T009 and T009a must enforce single canonical source per run.
- **Metric Constraint**: T019a + T021 must compute intra/inter family drop for SC-002 and enforce 15% threshold.
- **Report Constraint**: T027c must output a single unified ranked list in Markdown table format.
- **Review Address**: T009 (merged warning), T022a, T028a, T029-T032 explicitly resolve the "First-Principles" vs "Curve-Fitting" contradiction by ensuring all documentation and output artifacts explicitly state that the model interpolates DFT data rather than solving the Schrödinger equation. T001a removed as spec is already correct.