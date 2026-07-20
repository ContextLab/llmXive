---
description: "Task list template for feature implementation"
---

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

## Phase 1: Setup (Shared Infrastructure & Terminology Alignment)

**Purpose**: Project initialization and mandatory terminology alignment to satisfy Constitution FR-030 before any implementation begins.

- [X] T001 Create project structure: Create directories `code/`, `data/raw/`, `data/processed/`, `data/results/`, `tests/unit/`, `tests/integration/`, `docs/`. **Requirement**: Initialize `state/projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate.yaml` with an empty `artifact_hashes: {}` map to satisfy Constitution Principle III (Data Hygiene) structural requirements. Create `README.md` with reproducibility instructions (referencing Constitution Principle I) and `.gitignore` with specific patterns: `data/*`, `!data/processed/*`, `!data/results/*`, `__pycache__`, `*.pyc`, `.env`. **Requirement**: Add the Feynman quote "Don't fool yourself — and you are the easiest to fool." and a "What This Is Not" table to the top of `README.md` explicitly distinguishing the Surrogate Model from First-Principles calculations.
- [X] T002 Initialize a Python project with pinned dependencies in `code/requirements.txt`: Include `pymatgen`, `torch`, `torch-geometric`, `shap`, `pandas`, `numpy`, `scikit-learn`, `ruff`, `black`.
- [ ] T003a [Foundation] Configure linting (ruff): Create `.ruff.toml` with strict rules (E, F, W, I) and line-length=88. **Requirement**: Verify configuration against a sample linting run to ensure correctness.
- [ ] T003b [Foundation] Configure formatting (black): Create `pyproject.toml` with `[tool.black]` section setting `line-length = 88`. **Requirement**: Verify configuration against a sample formatting run.
- [ ] T001a [Foundation] Implement "What This Is Not" section in `spec.md`: Create Section 5.1 in `spec.md` with the comparative table (Method, Cost, Physics Solved, Input Data, Underlying Equation) explicitly stating the model is a "Structure-Only Surrogate" and does NOT solve the Schrödinger equation. **Requirement**: This section must be present before T009 is executed.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure (config, logging, data models)

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup environment configuration management in `code/utils/config.py` (seeding, paths, CPU limits). **Requirement**: Implement a global seed manager that enforces pinning for `torch`, `numpy`, and `random` across all modules.
- [X] T004a [Foundation] Verify seed pinning in pipeline: Create a script `code/utils/verify_seeds.py` that runs a dummy pipeline step and asserts that `torch`, `numpy`, and `random` seeds are consistently pinned across imports, satisfying Constitution Principle I (Reproducibility).
- [X] T005 Implement logging infrastructure in `code/utils/logger.py` (structured logs for bias checks)
- [X] T006 Create base constants and conversion factors in `code/utils/constants.py` (elastic modulus units)
- [X] T007 Define the `MaterialGraph` data schema in `code/data_models/material_graph.py` (nodes, edges, targets)
- [X] T008 Implement dynamic sampling strategy in `code/utils/memory_utils.py`. **Requirement**: Implement a unit test in `tests/unit/test_memory_utils.py` that tests the *logic* of the sampler (e.g., chunk size calculation) without mocking the full data loading pipeline. The unit test verifies the *algorithm*, not the memory usage of a full run. (required for FR-007/SC-004).
- [X] T046 [Foundation] Implement "Surrogate Model Disclaimer" in all output artifacts: Modify the following specific scripts to include a mandatory disclaimer field: `code/model/train_logger.py`, `code/model/eval_runner.py`, `code/analysis/report_generator.py`. **Requirement**: The disclaimer must state: "These results are derived from a machine learning surrogate model interpolating pre-computed DFT data. They do not represent first-principles calculations or solutions to the Schrödinger equation." **Requirement**: This disclaimer must be included in the metadata of every JSON output and at the top of every Markdown report. **Requirement**: Include "Scientific Integrity Statement" in all reports. **Requirement**: Dependency: None.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 (MVP)

**Goal**: Data ingestion and graph construction

**Independent Test**: The script can be run to download a subset of materials, parse their CIFs into graphs using `pymatgen`, and output a JSON/CSV summary of node counts, edge counts, and target values without requiring any model training.

### Implementation for User Story 1

- [X] T009 [US1] Implement unified dataset loader in `code/ingest/download.py` that abstracts Materials Project/AFLOW into a single canonical source per run (satisfying Constitution Principle I) and explicitly documents data is from *existing* DFT (not generated here). **Requirement**: Include a "Warning" docstring stating: "WARNING: This model is a surrogate interpolator trained on pre-computed DFT data. It does NOT solve the Schrödinger equation or perform first-principles calculations."
- [ ] T009a [US1] Implement runtime source enforcement in `code/ingest/validator.py`: Add a check that raises a hard error if more than one data source is active in a single run, satisfying the "single canonical source" constraint. **Requirement**: Use a lock file at `data/.source_state.lock` and check for its existence before writing. **Requirement**: If check fails, raise `SystemExit(1)` with a clear error message. **Requirement**: Implement logic to persist the source identity to a state file (e.g., `data/.source_state`) and compare it across runs to enforce the constraint against user error.
- [ ] T009b [US1] Implement Unified Loader Abstraction: Create `code/ingest/loader_base.py` defining an abstract base class `DataLoader` with methods `fetch_data()`, `validate_source()`, and `get_metadata()`. **Requirement**: This class must support dynamic switching between 'materials_project' and 'aflow' via a configuration key. **Requirement**: Concrete implementations for each source must inherit from this base.
- [X] T010 [US1] Implement CIF parser in `code/ingest/parse_cif.py` (convert to `MaterialGraph` using `pymatgen`, extract node/edge features)
- [X] T011 [US1] Implement 2D filter and tensor validator in `code/ingest/filter.py`. **Requirement**: Explicitly filter for entries with **independent elastic tensor components** as mandated by Constitution Principle VI (DFT Ground-Truth Fidelity). Log exclusion reasons for entries with incomplete tensors.
- [X] T012 [US1] Implement bias check for excluded entries in `code/ingest/bias_check.py` (log reasons for exclusion, flag small families)
- [ ] T013d [US1] Create data pipeline orchestration script in `code/ingest/pipeline.py` (download -> parse -> filter -> save to `data/processed/graphs_v1.parquet`). **Requirement**: Output schema MUST include `node_features`, `edge_features`, `target_moduli`, `family_id`. Implement error handling for missing tensors. **Requirement**: **Atomic Write Verification**: Before exiting, the script MUST validate the written file: check file size > 0, verify it is a valid parquet file with the expected schema, and ensure no rows are null in critical columns. If validation fails, exit with code 1 immediately. **Requirement**: This task performs internal validity checks; T013e performs external checksum verification. **Dependency**: T009a, T009b, T010, T011, T012.
- [ ] T013e [US1] Verify Volume Constraint and Checksum: Create `code/ingest/verify_data.py` to perform two checks: 1) Count unique 2D material entries in `data/processed/graphs_v1.parquet`; if < 1,000, exit with code 1 and log "SC-001 Violation". 2) Generate SHA256 checksum for `graphs_v1.parquet` and record it in `state/projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate.yaml` under `artifact_hashes.data_processed.graphs_v1_parquet`. **Requirement**: This task must run AFTER T013d and fail the pipeline if checks do not pass. **Requirement**: If T013d did not produce the file or exited with code 1, this task MUST exit with code 1. **Requirement**: **Pre-flight Check**: Verify T013d exit code was 0 before proceeding. **Dependency**: T013d.
- [ ] T017 [US1] Implement stratified splitting logic in `code/ingest/split_generator.py`: Generate a final family-separated split by consuming `graphs_v1.parquet` directly (ignoring any previous split files). **Requirement**: Ensure no training family appears in the test set. Implement a runtime assertion: if any family is present in both sets, exit with code 1 and log an error message. **Requirement**: Output `data/processed/split_indices.json` with the final split. **Requirement**: This split MUST satisfy SC-002 (inter-family generalization). **Requirement**: Verify `family_id` column exists in `graphs_v1.parquet` before proceeding; if missing, exit with error. **Dependency**: T013d, T013e.
- [ ] T008a [US1] Implement integration test for full-pipeline memory usage: Create `tests/integration/test_memory_full_pipeline.py` that runs the **actual data loading pipeline (T013d)** with a representative sample of real data to verify peak memory < 7GB. **Requirement**: Use a representative sample from `graphs_v1.parquet`. **Requirement**: Consume `split_indices.json` from T017. **Requirement**: Output memory usage stats to `data/results/memory_test.log`. **Requirement**: Do NOT generate splits; only consume the existing split. **Dependency**: T013d, T017.
- [X] T014 [US1] Add unit tests for CIF parsing logic in `tests/unit/test_parse_cif.py` (verify disconnected graph handling)
- [X] T015 [US1] Add unit tests for tensor validation in `tests/unit/test_filter.py` (verify 6-component requirement)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Lightweight GNN Training and Evaluation

**Goal**: Train a lightweight GNN on the constructed dataset to predict elastic moduli and evaluate performance against held-out DFT values, including intra-family baseline and inter-family drop.

### Implementation for User Story 2

- [X] T016 [P] [US2] Define lightweight GNN architecture in `code/model/gnn.py` (-3 layers, hidden dim ≤64, CPU-only `torch_geometric`)
- [ ] T018a [US2] Implement training configuration in `code/model/train_config.py`: Define hyperparameters, early stopping patience, and CPU constraints.
- [ ] T018b [US2] Implement training loop in `code/model/train.py`: Train the GNN on the dataset. **Requirement**: Consume `split_indices.json` from T017. **Requirement**: Enforce CPU-only execution. **Requirement**: Log `memory_peak` at each epoch. **Requirement**: If `memory_peak` > 7GB, exit with code 1. **Requirement**: Save model weights to `data/processed/model_v1.pt`. **Requirement**: Output `predictions.json` for the test set. **Requirement**: If training fails, exit with code 1; do NOT generate a synthetic model. **Requirement**: Load architecture from `code/model/gnn.py` and hyperparameters from `code/model/train_config.py`. **Dependency**: T017, T046.
- [ ] T018c [US2] Implement training logging and checkpointing in `code/model/train_logger.py`: Log metrics to `data/results/training_logs.json`. **Requirement**: Log schema MUST include `epoch: int`, `loss: float`, `metrics: {mape, rmse}`, `memory_peak: float`. Include metadata key `disclaimer`: "These results are ML interpolations of DFT data, not first-principles solutions." **Dependency**: T018b, T046.
- [X] T019 [US2] Implement evaluation and metrics calculation in `code/model/eval.py` (MAPE, RMSE, R² for Young's, Shear, Poisson)
- [ ] T019a [US2] Implement validation and logging of success criteria in `code/model/eval_runner.py`: Calculate MAPE against held-out families and log the result against the threshold. **Requirement**: Load `predictions.json` from T018b and `test_indices` from T017. **Dependency**: T017, T018b.
- [ ] T020 [US2] Implement k-fold cross-validation runner in `code/model/cv_runner.py`: Perform stratified k-fold cross-validation where each fold's test set consists of entirely unseen chemical families. **Requirement**: Output `data/results/cv_metrics.json` containing fold-wise MAPE, RMSE, and family separation verification. **Requirement**: If any fold contains a family in both train and test sets, exit with code 1. **Dependency**: T017.
- [X] T020a [US2] Implement intra-family baseline metric generation in `code/analysis/ablation.py` (compute MAPE/RMSE on random splits within families to establish baseline for SC-002)
- [ ] T021a [US2] Implement inter-family generalization test in `code/model/generalization_test.py`: Measure MAPE on unseen families; output `data/results/generalization_metrics.json`. **Requirement**: Test set MUST consist of entirely excluded families. Implement a runtime check to ensure no training family appears in the test set: load `split_indices.json`, extract unique `family_id` sets for train and test, assert intersection is empty. **Dependency**: T017, T018b.
- [ ] T021b [US2] Implement metrics aggregation and logging in `code/analysis/aggregate.py`: Combine SHAP, permutation, and generalization metrics into a single intermediate JSON. **Requirement**: Aggregate existing metrics (T020a, T021a) without overwriting. **Dependency**: T046, T020a, T021a.
- [ ] T036 [US2] Verify inference time constraint (SC-003): Implement `code/model/inference_benchmark.py` to measure latency per material on CPU. **Requirement**: Measure latency averaged over multiple runs on the available CPU environment. **Requirement**: Detect and log the specific CPU model (e.g., via `psutil` or `lscpu`) to ensure portability. Ensure the output in `data/results/generalization_metrics.json` includes `inference_time_ms`, `cpu_model`, and confirms it is < 100ms. **Requirement**: **Dependency**: T018b must be complete (model weights must exist) before this task can run. **Status**: Pending T018b completion. **Dependency**: T018b.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance and Ablation Analysis

**Goal**: Identify which structural descriptors most strongly influence predicted elastic moduli and understand the contribution of different descriptor classes.

### Implementation for User Story 3

- [X] T025 [US3] Implement composition-only baseline model in `code/analysis/ablation.py` (feed-forward network on Magpie descriptors, no topology)
- [ ] T023 [US3] Implement SHAP interaction value calculation in `code/analysis/importance.py`: **Requirement**: Dependency: T018b (produces trained model weights artifact), T017. **Requirement**: Calculate and output `p-values` for each descriptor based on the SHAP values using a bootstrap method with a sufficient number of iterations and a confidence interval of a standard level. **Requirement**: Output `data/results/shap_pvalues.json` with schema `{descriptor: float (p-value)}`. **Requirement**: Verify that the output file exists and contains p-values for at least 3 descriptors. **Requirement**: This calculation is required to satisfy SC-005 (p < 0.05). **Requirement**: **Status**: Pending T018b completion. **Dependency**: T018b, T017.
- [ ] T024 [US3] Implement permutation importance calculation in `code/analysis/importance.py`: **Requirement**: Dependency: T018b (produces trained model weights artifact), T017. **Requirement**: Calculate and output `p-values` for each descriptor based on the permutation scores using a permutation test with a **sufficient number of permutations** to ensure statistical robustness to ensure statistical robustness and a null hypothesis: no correlation. **Requirement**: Output `data/results/permutation_pvalues.json` with schema `{descriptor: float (p-value)}`. **Requirement**: Verify that the output file exists and contains p-values for at least 3 descriptors. **Requirement**: This calculation is required to satisfy SC-005 (p < 0.05). **Requirement**: **Status**: Pending T018b completion. **Dependency**: T018b, T017.
- [X] T026 [US3] Implement ablation study runner in `code/analysis/ablation.py` (compare full GNN vs. composition-only, report MAPE delta). Dependency: T025 AND T018b.
- [ ] T027a [US3] Implement data aggregation script in `code/analysis/aggregate.py`: Combine SHAP, permutation, and generalization metrics into a single intermediate JSON.
- [ ] T027b [US3] Implement report template generation in `code/analysis/template.py`: Create the Markdown template for the final report.
- [ ] T027c [US3] Generate Report Script: Create `code/analysis/report_generator.py` to synthesize metrics into a single unified ranked list. **Requirement**: Output format MUST be a Markdown table with columns: `Descriptor`, `Importance Score`, `p-value`, `Description`. **Requirement**: Filter the table to include ONLY descriptors where `p < 0.05`. If fewer than 3 descriptors have p < 0.05, generate a report stating "SC-005 Not Met". **Requirement**: The report MUST state: "The identified descriptors are statistical correlations learned by the surrogate model from DFT data, not fundamental quantum mechanical variables derived from the Hamiltonian." **Dependency**: T027a, T027b, T021b, T046.
- [ ] T027d [US3] Execute Report Generation: Run `code/analysis/report_generator.py` to produce `data/results/feature_importance_report.md`. **Requirement**: Verify the output file exists and contains the required disclaimer. **Dependency**: T027c.
- [X] T028 [US3] Add unit tests for SHAP value aggregation in `tests/unit/test_importance.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Documentation & Compliance (Priority: P4)

**Goal**: Finalize all documentation to prevent the "First-Principles" vs "Curve-Fitting" contradiction identified in research reviews.

### Implementation for Phase 6

- [ ] T029 [P4] Update `README.md` to explicitly define the project as a "Surrogate Model" that interpolates DFT data. **Requirement**: Must explicitly state: "Random seeds are pinned in `code/utils/config.py`" (referencing the specific file path defined in T004).
- [ ] T030 [P4] Create `docs/methodology.md` detailing the distinction between "First-Principles" and "Surrogate" methods, citing the specific DFT sources used. **Requirement**: Include the Feynman quote and the "What This Is Not" table.
- [ ] T031 [P4] Update `docs/contributing.md` to enforce terminology guidelines: forbid the use of "First-Principles" to describe the ML model.
- [ ] T032 [P4] Verify Limitations section: Ensure `spec.md` contains Section 5 "Limitations" describing extrapolation failure and lack of physics discovery. If missing, flag for manual review.
- [X] T033 [P4] **Review Response**: Audit all source code for "First-Principles" or "Schrödinger" references: Scan `code/`, `docs/` for any remaining instances of forbidden terminology using `grep -r` or a Python script with regex. **Requirement**: Do NOT scan `data/results/`. If found, replace with "Surrogate" or "Interpolation" and log the change in `state/projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate.yaml` under `terminology_audit`. **Status**: Deprecated in favor of T037 (Automated Scanner).
- [ ] T037 [P4] **Review Response**: Implement automated terminology scanner in `code/utils/terminology_scanner.py`: Create a script that scans all source files and documentation (`code/`, `docs/`) for forbidden terms ("First-Principles", "Schrödinger", "Hamiltonian" in the context of the ML model). **Requirement**: This script is the primary enforcement mechanism for terminology compliance. **Dependency**: T033 (Deprecated).

**Checkpoint**: Terminology compliance verified across code and docs.

---

## Phase 7: Research Review Response (Priority: P4)

**Goal**: Explicitly address the "Richard Feynman (simulated)" review concern regarding the distinction between "First-Principles" and "Curve-Fitting" to ensure scientific integrity.

### Implementation for Phase 7

- [ ] T038 [P4] **Review Response**: Update `spec.md` Title and Abstract: Rename the project title in `spec.md` from any "First-Principles" phrasing to "Structure-Only Surrogate Model for 2D Material Elastic Moduli". Update the Abstract to explicitly state: "This project implements a Structure-Only Surrogate Model... It is a machine learning model trained on existing DFT results to approximate the mapping from crystal structure to elastic properties." **Requirement**: Explicitly forbid the use of the phrase "First-Principles" to describe the ML model in the abstract. **Dependency**: T001a.
- [ ] T039 [P4] **Review Response**: Add "Scientific Integrity" Section to `README.md`: Create a dedicated section titled "What This Is NOT" in `README.md`. **Requirement**: Include a table comparing "First-Principles (DFT)" vs. "Surrogate (ML)" with rows for "Underlying Physics", "Computational Cost", "Input Data", and "Output Nature". **Requirement**: Explicitly state: "We are not solving the Schrödinger equation. We are interpolating pre-computed data." **Requirement**: Quote Feynman: "Don't fool yourself — and you are the easiest person to fool." **Dependency**: T001, T030.
- [ ] T040 [P4] **Review Response**: Verify "Hamiltonian" Terminology in Documentation: Scan `docs/` and `spec.md` to ensure the word "Hamiltonian" is only used when discussing the *source* DFT data or the *limitations* of the surrogate, never as a method used by the ML model. **Requirement**: If "Hamiltonian" is found in a context implying the ML model solves it, replace with "DFT source data" or "pre-computed quantum mechanical results". Log changes in `state/projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate.yaml`. **Dependency**: T033, T037.
- [ ] T041 [P4] **Review Response**: Update `docs/methodology.md` to include a "Limitations of Interpolation" section. **Requirement**: Explicitly state that the model cannot discover new physics, cannot extrapolate to unseen chemical spaces, and cannot predict properties for conditions outside the training DFT data. **Requirement**: Reiterate that "feature importance" represents statistical correlation, not causal quantum mechanical derivation. **Dependency**: T030, T027c.

**Checkpoint**: Research review concerns fully addressed; scientific integrity verified.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Research Review Response (Phase 7)**: Depends on T001a (Terminology alignment) and T030 (Methodology doc)

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
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
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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
- **Critical**: Adhere strictly to the "Surrogate Model" terminology. Do not use "First-Principles" to describe the ML model.