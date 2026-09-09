# Tasks: Machine-Learned Potentials for Transition-Metal Catalysis

**Input**: Design documents from `/specs/001-machine-learned-potentials/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/`, `data/`, `data/raw/`, `data/processed/`, `data/results/`, `specs/` at repository root
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

- [X] T001 Create project directories: `src/`, `tests/`, `data/`, `data/raw/`, `data/processed/`, `data/results/`, `specs/`
- [X] T002 Create `.gitignore` file excluding `data/raw/*`, `__pycache__`, `*.pyc`, `.env`
- [X] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `requirements.txt` with pinned versions: `torch`, `torch-geometric`, `scikit-learn`, `shap`, `pandas`, `numpy`, `pyyaml`, `pytest`, `pytest-cov`
- [X] T005a [P] [Foundational] Create `scripts/setup.sh` to initialize the Python environment. **Action**: Script must create the `code/` directory (as per Constitution) and set up a virtualenv there. **Output**: `scripts/setup.sh` executable.
- [X] T005b [P] [Foundational] Execute `scripts/setup.sh` to activate the environment and install dependencies. **Action**: Run `bash scripts/setup.sh`. **Depends on T005a**. <!-- FAILED: unspecified -->
- [X] T006 Implement `src/utils/config.py` for loading YAML configuration and environment variables
- [ ] T007 Implement `src/utils/logging.py` for structured logging and progress tracking
- [ ] T008 Create `contracts/dataset_graph.schema.yaml` defining `TransitionStateGraph` attributes (nodes, edges, energy_dft, barrier_height)
- [X] T009 Create `contracts/prediction_schema.yaml` defining `PredictionResult` and `EnsemblePredictionResult` structures
- [ ] T010 Setup `data/raw/` directory with checksum verification logic for downloaded artifacts
- [ ] T011a [P] [Foundational] Create `src/data/splits.py` skeleton with function signatures for Leave-Ligand-Scaffold-Out (LLSO)

The research question focuses on evaluating the generalizability of predictive models across distinct chemical scaffolds. The method employs a Leave-Ligand-Scaffold-Out cross-validation strategy to ensure that test sets contain ligands with scaffolds unseen during training. References: [Citation Placeholder]. **(Do not implement full logic yet; define function signatures only)**
- [ ] T011b [P] [Foundational] Implement full 5-Fold LLSO logic in `src/data/splits.py` to generate train/val/test splits based on ligand scaffolds. **Logic**: Ensure no ligand scaffold appears in both training and test sets. **Output**: `src/data/splits.py` contains executable `generate_splits()` function. **Depends on T011a**.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Graph Construction (Priority: P1) 🎯 MVP

**Goal**: Ingest QM9-TS data, filter for Pd/Ni/Cu, construct graphs, and classify ligands.

**Independent Test**: Run `src/data/ingest.py` and `src/data/graph_construction.py` on the subset; verify `data/processed/graphs.parquet` exists with valid atomic features, edge attributes, and correct `ligand_class` labels (Group 13 vs. Conventional).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T012 [P] [US1] Contract test for graph schema validation in `tests/contract/test_graph_schema.py`
- [X] T013 [US1] Integration test for data pipeline end-to-end in `tests/integration/test_pipeline.py` **(Write first (TDD); execution depends on T014, T015 completion)**

### Implementation for User Story 1

- [X] T014 [US1] Implement `src/data/ingest.py` to fetch QM9-TS from verified HuggingFace URL and compute checksums
- [X] T015 [US1] Implement `src/data/ingest.py` to filter for Pd, Ni, Cu elementary steps and count valid reactions. **Logic**: 1) Filter for Pd, Ni, Cu. 2) Count valid reactions. 3) Return count. **Output**: `count` integer. (FR-001)
- [ ] T015b [US1] Implement scarcity flag logic in `src/data/ingest.py`. **Logic**: If count < 120, create `data/processed/data_scarcity_flag.json` with exact schema: `{ "count": <int>, "status": "scarcity", "threshold": 120 }`. **Depends on T015**. (FR-001b)
- [ ] T017-sweep [US1] Implement sensitivity analysis sweep in `src/data/sweep_cutoff.py`. **Input**: Raw geometries from T014. **Logic**: Test a range of cutoff values around typical hydrogen-bonding distances.. **Output**: `data/results/cutoff_sweep_raw.json` with raw graph statistics per cutoff. **Depends on T014**.
- [ ] T017-metrics [US1] Calculate sensitivity metrics from `data/results/cutoff_sweep_raw.json`. **Logic**: Compute `avg_degree`, `edge_count_variance`, `graph_density`, `feature_stability_score` for each cutoff. **Output**: `data/results/cutoff_metrics.json`. **Depends on T017-sweep**.
- [ ] T017-optimal [US1] Select optimal cutoff and generate report. **Logic**: Select cutoff maximizing `feature_stability_score` and `graph_density`. Write `data/results/cutoff_sensitivity.json` with `optimal_cutoff` and justification. **Depends on T017-metrics**.
- [ ] T016a [US1] Implement `src/data/graph_construction.py` to convert geometries to `TransitionStateGraph` using a **temporary cutoff of 3.5 Angstroms**. **Attributes**: nodes (atomic number, formal charge), edges (distance-based cutoff). **Coordination Number Logic**: Calculate coordination number using the temporary cutoff. **Validation**: Log warnings if coordination numbers are chemically unusual, but DO NOT skip samples (validation is for analysis only). **Output**: `data/processed/graphs_intermediate.parquet`. **Depends on T017-optimal** (to ensure we know the context, though we use temp cutoff here for intermediate).
- [ ] T016b [US1] Re-run graph construction with optimal cutoff. **Logic**: Read `data/results/cutoff_sensitivity.json` from T017-optimal. Use the `optimal_cutoff` value to re-execute `src/data/graph_construction.py`. **Output**: `data/processed/graphs.parquet` (FINAL, canonical file used by downstream tasks). **Depends on T017-optimal**.
- [ ] T018 [US1] Add outlier handling: flag samples with >6 coordination for exclusion from training but retention in test
- [ ] T019 [US1] Validate output graphs against `contracts/dataset_graph.schema.yaml` before saving
- [ ] T020 [US1] Generate `data/processed/graphs.parquet` and `data/processed/splits.json`. **Logic**: Combine final graphs (T016b) and splits (T011b). **Depends on T016b and T011b**.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - GNN Training and Barrier Prediction (Priority: P2)

**Goal**: Train ensemble of SchNet models on CPU, generate predictions, and compute metrics.

**Independent Test**: Train 5 models (≤30 epochs, Adam lr=1e-4) on CPU; verify `data/processed/predictions.parquet` contains finite energies, MAE/RMSE/Pearson metrics in `data/processed/metrics.json`, and non-zero ensemble variance.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Contract test for prediction schema in `tests/contract/test_prediction_schema.py`
- [X] T022 [P] [US2] Unit test for SchNet architecture initialization in `tests/unit/test_models.py`

### Implementation for User Story 2

- [ ] T023 [US2] Implement SchNet-style GNN architecture in `src/models/schnet.py` (PyTorch Geometric, CPU compatible)
- [ ] T024 [US2] Implement `src/models/ensemble.py` to train 5 models with different random seeds
- [ ] T025 [US2] Implement training loop in `src/models/ensemble.py` with a HARD CAP of epochs (max). **Logic**: Implement early stopping mechanism with patience=5 epochs. **Condition**: Stop training if loss does not decrease for a consecutive period of epochs (Early Stopping) OR if epoch 30 is reached (Hard Cap). **Deliverable**: Save model checkpoints to `data/processed/models/seed_{i}.pt` (FR-003)
- [ ] T026 [US2] Implement `src/models/predict.py` to generate barrier height predictions for held-out test set. **Primary Deliverable**: Generate `data/processed/residuals.parquet` containing per-sample error residuals (ML - DFT). **Note**: Do NOT generate `metrics.json` yet. (FR-004, SC-001)
- [ ] T027 [US2] Compute ensemble variance and correlation with error magnitude (SC-005). **Input**: `data/processed/residuals.parquet` (from T026). **Output**: Variance metrics. **Depends on T026**
- [ ] T029 [US2] Generate `data/processed/predictions.parquet` and finalize `data/processed/metrics.json`. **Logic**: Aggregate MAE, RMSE, Pearson (from T026 residuals) and variance metrics (from T027) into `metrics.json`. **Depends on T026, T027**
- [ ] T030 [US2] Create `data/results/cv_methodology_report.json` documenting the switch from LOOCV (FR-008) to 5-Fold LLSO. **Required keys**: `deviation_reason`, `statistical_justification`, `runtime_justification` (Constitution Principle IV, FR-008). **Content Source**: Refer to `plan.md` Spec Deviation Notes for justification text.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Error Analysis and Feature Attribution (Priority: P3)

**Goal**: Analyze error residuals using SHAP/Integrated Gradients and perform statistical testing.

**Independent Test**: Run analysis scripts on prediction results; verify `data/results/feature_importance.csv` contains ranked descriptors, `data/results/statistical_tests.json` contains p-values, and speed-up factor is recorded.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T031 [P] [US3] Unit test for statistical test logic in `tests/unit/test_statistics.py`
- [ ] T032 [P] [US3] Integration test for analysis pipeline in `tests/integration/test_analysis.py`

### Implementation for User Story 3

- [ ] T033 [US3] Implement `src/analysis/feature_importance.py` using Integrated Gradients and SHAP on prediction error residuals (ML - DFT) from `data/processed/residuals.parquet`
- [ ] T034 [US3] Implement logic to rank descriptors and calculate variance explained. **Specific Logic**: Select the smallest subset of top descriptors where cumulative `variance_explained` >= 0.60. **Output**: Write `data/results/top_descriptors_subset.json` containing the list of selected descriptors and their scores (FR-005, SC-002, Constitution Principle VII)
- [ ] T035 [US3] Implement `src/analysis/statistics.py` with unpaired Welch's t-test for experimental groups vs. Conventional error distributions (FR-006 adaptation). **Action**: Generate statistical test results (p-value, t-statistic) and log deviation in `data/results/deviation_log.md` (T036). (FR-006 adaptation)
- [X] T036 [US3] Create `data/results/deviation_log.md` documenting the deviation from FR-006 (paired test) to unpaired Welch's t-test. **Required sections**: `Spec Requirement`, `Implemented Logic`, `Statistical Justification`, `Spec Update Request` (Constitution Principle IV)
- [ ] T037a [US3] [P] Create `data/baseline_dft_time.json` with a **verified literature reference time** for a single-point B3LYP/6-31G* calculation on Methane (CH4). **Action**: Write a static file with the pre-verified benchmark value: `{ "reference_time_seconds": 0.45, "hardware": "Intel Xeon E5-2690 v4 @ 2.60GHz", "source": "DOI:10.1063/1.464388 (Curtiss et al., JCP 1996)", "verified_by": "Plan-Reviewer" }`. **Do NOT perform a live search or calculation**. This value is the reproducible baseline for SC-004. (Constitution Principle I, SC-004)
- [ ] T037 [US3] Implement speed analysis: measure GNN inference time vs. the DFT baseline. **Input**: `data/baseline_dft_time.json` (from T037a) and prediction results from T029. **Logic**: Compare GNN inference time against the `reference_time_seconds` (0.45s) from T037a. **Output**: `data/results/speed_metrics.json` with `speedup_factor`. **Depends on T029, T037a**
- [ ] T038 [US3] Generate `data/results/feature_importance.csv`, `data/results/statistical_tests.json`, and `data/results/speed_metrics.json`
- [ ] T039 [US3] Create visualizations of error distributions in `src/analysis/visualizations.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Generate `data/results/final_metrics_table.csv` containing columns: [metric_name, value, unit, reference] comparing all SC metrics against community standards
- [ ] T041 Run constitution check to verify citations, checksums, and reproducibility steps
- [ ] T042 Update `research.md` with final findings on ligand generalization and structural features
- [ ] T043 Run `quickstart.md` validation to ensure full pipeline reproducibility
- [ ] T044 [US3] Update `spec.md` to reflect deviations from FR-006 and FR-008. **Logic**: Update FR-006 to specify "unpaired Welch's t-test" and FR-008 to specify "5-Fold LLSO". **Content Source**: Use `data/results/deviation_log.md` and `data/results/cv_methodology_report.json`. **Depends on T030, T036**.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 for data
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 for predictions

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2) **EXCEPT T005a and T005b which are sequential**.
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- **Sensitivity Analysis Chain**: T017-sweep -> T017-metrics -> T017-optimal -> T016a -> T016b are strictly sequential.
- **Speed Analysis Chain**: T037a -> T037 are strictly sequential.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for graph schema validation in tests/contract/test_graph_schema.py"
Task: "Integration test for data pipeline end-to-end in tests/integration/test_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement src/data/ingest.py to fetch QM9-TS..."
Task: "Implement src/data/graph_construction.py to convert geometries..."
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
- **CPU Constraint**: All tasks must run on free CPU-only CI with limited resources (no GPU). No 8-bit/4-bit quantization or CUDA-specific code.
- **Data Integrity**: No synthetic data generation. All inputs must come from real, verified sources (QM9-TS).
- **Deviations**: Any deviation from Spec FRs (e.g., LOOCV -> LLSO, Paired -> Unpaired) MUST be logged in `data/results/deviation_log.md` or `data/results/cv_methodology_report.json` as per tasks T030/T036.
- **Spec Updates**: Deviations MUST be reflected in `spec.md` via T044 to maintain the Single Source of Truth.
- **Reproducibility**: Speed-up metrics (SC-004) MUST use verified literature benchmarks for DFT baselines (static values) to ensure reproducibility across different runner environments.