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

- [X] T001 Create project structure: Create directories `code/`, `data/raw/`, `data/processed/`, `data/results/`, `tests/unit/`, `tests/integration/`, `docs/`. **Requirement**: Initialize `state/projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate.yaml` with an empty `artifact_hashes: {}` map to satisfy Constitution Principle III (Data Hygiene) structural requirements. Create `README.md` with reproducibility instructions (referencing Constitution Principle I) and `.gitignore` with specific patterns: `data/*`, `!data/processed/*`, `!data/results/*`, `__pycache__`, `*.pyc`, `.env`. **Requirement**: **Pre-Flight Spec Check**: Before proceeding, validate that `spec.md` contains Section 5 "Limitations" and the "Scientific Integrity" warning. If missing, exit with code 1 and message "Spec.md is non-compliant: Missing Limitations/Warnings".
- [X] T002 Initialize a Python project with pinned dependencies in `code/requirements.txt`: Include `pymatgen`, `torch`, `torch-geometric`, `shap`, `pandas`, `numpy`, `scikit-learn`, `ruff`, `black`.
- [X] T003a [Foundation] Configure linting (ruff): Create `.ruff.toml` with strict rules (E, F, W, I) and line-length=88.
- [X] T003b [Foundation] Configure formatting (black): Create `.black.toml` with line-length=88.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure (config, logging, data models)

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup environment configuration management in `code/utils/config.py` (seeding, paths, CPU limits). **Requirement**: Implement a global seed manager that enforces pinning for `torch`, `numpy`, and `random` across all modules. **Requirement**: Define `MIN_ENTRY_THRESHOLD = 1000`, `MAX_MEMORY_GB = 7.0`, `BOOTSTRAP_ITERATIONS = 1000`, `PERMUTATION_SHUFFLES = 1000` constants in this file.
- [X] T004a [Foundation] Verify seed pinning in pipeline: Create a script `code/utils/verify_seeds.py` that runs a dummy pipeline step and asserts that `torch`, `numpy`, and `random` seeds are consistently pinned across imports, satisfying Constitution Principle I (Reproducibility).
- [X] T005 Implement logging infrastructure in `code/utils/logger.py` (structured logs for bias checks)
- [X] T006 Create base constants and conversion factors in `code/utils/constants.py` (elastic modulus units)
- [X] T007 Define the `MaterialGraph` data schema in `code/data_models/material_graph.py` (nodes, edges, targets)
- [X] T008 Implement dynamic sampling strategy in `code/utils/memory_utils.py`. **Requirement**: Implement a unit test in `tests/unit/test_memory_utils.py` that tests the *logic* of the sampler (e.g., chunk size calculation) without mocking the full data loading pipeline. The unit test verifies the *algorithm*, not the memory usage of a full run. (required for FR-007/SC-004).
- [X] T046 [Foundation] Implement "Surrogate Model Disclaimer" in all output artifacts: Modify the following specific scripts to include a mandatory disclaimer field: `code/model/train_logger.py`, `code/model/eval_runner.py`, `code/analysis/report_generator.py`. **Requirement**: The disclaimer must state: "These results are derived from a machine learning surrogate model interpolating pre-computed DFT data. They do not represent first-principles calculations or solutions to the Schrödinger equation." **Requirement**: This disclaimer must be included in the metadata of every JSON output and at the top of every Markdown report. **Requirement**: Include "Scientific Integrity Statement" in all reports. **Requirement**: Dependency: None.
- [X] T037 [Foundation] Implement automated terminology scanner in `code/utils/terminology_scanner.py`: Create a script that scans all source files and documentation (`code/`, `docs/`) for forbidden terms ("First-Principles", "Schrödinger", "Hamiltonian" in the context of the ML model). **Requirement**: This script must be added to the `pre-commit` hooks (or equivalent) to prevent future violations. **Requirement**: Update existing comments in `code/` to replace forbidden terms with "Surrogate" or "Interpolation".

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 (MVP)

**Goal**: Data ingestion and graph construction

**Independent Test**: The script can be run to download a subset of materials, parse their CIFs into graphs using `pymatgen`, and output a JSON/CSV summary of node counts, edge counts, and target values without requiring any model training.

### Implementation for User Story 1

- [X] T009 [US1] Implement unified dataset loader in `code/ingest/download.py` that abstracts Materials Project/AFLOW into a single canonical source per run (satisfying Constitution Principle I) and explicitly documents data is from *existing* DFT (not generated here). **Requirement**: Include a "Warning" docstring stating: "WARNING: This model is a surrogate interpolator trained on pre-computed DFT data. It does NOT solve the Schrödinger equation or perform first-principles calculations."
- [X] T009a [US1] Implement runtime source enforcement in `code/ingest/validator.py`: Add a check that raises a hard error if more than one data source is active in a single run, satisfying the "single canonical source" constraint. **Requirement**: Use a global singleton flag or a lock file to detect concurrent/mixed source activation. **Requirement**: If check fails, raise `SystemExit(1)` with a clear error message. **Requirement**: Implement logic to persist the source identity to a state file (e.g., `data/.source_state`) and compare it across runs to enforce the constraint against user error.
- [X] T009b [US1] Implement Unified Loader Abstraction: Create `code/ingest/loader_base.py` defining an abstract base class `DataLoader` with methods `fetch_data()`, `validate_source()`, and `get_metadata()`. **Requirement**: This class must support dynamic switching between 'materials_project' and 'aflow' via a configuration key. **Requirement**: Concrete implementations for each source must inherit from this base.
- [X] T010 [US1] Implement CIF parser in `code/ingest/parse_cif.py` (convert to `MaterialGraph` using `pymatgen`, extract node/edge features)
- [X] T011 [US1] Implement 2D filter and tensor validator in `code/ingest/filter.py`. **Requirement**: Explicitly filter for entries with **independent elastic tensor components** as mandated by Constitution Principle VI (DFT Ground-Truth Fidelity). Log exclusion reasons for entries with incomplete tensors.
- [X] T012 [US1] Implement bias check for excluded entries in `code/ingest/bias_check.py` (log reasons for exclusion, flag small families)
- [ ] T013d [US1] Create data pipeline orchestration script in `code/ingest/pipeline.py` (download -> parse -> filter -> save to `data/processed/graphs_v1.parquet`). **Requirement**: Output schema MUST include `node_features` (List[List[float32]]), `edge_features` (List[List[float32]]), `target_moduli` (Dict[str, float64]), `family_id` (str). Implement error handling for missing tensors. **Requirement**: Include a `validate_schema.py` script that verifies the generated `graphs_v1.parquet` matches the required schema before the pipeline proceeds. **Requirement**: Dependency: Phase 2 (Foundational) completion.
- [ ] T013e [US1] Verify Volume Constraint: Add a post-processing check in `code/ingest/pipeline.py` that counts the number of unique 2D material entries in `data/processed/graphs_v1.parquet`. **Requirement**: Use `config.MIN_ENTRY_THRESHOLD` (defined in T004). If the count is **less than or equal to 1000** (`count <= 1000`), **exit with code 1** and log "SC-001 Failed: Insufficient data entries (>1000 required)". **Requirement**: Do NOT continue the pipeline if the count is insufficient. **Requirement**: Dependency: T013d.
- [ ] T013f [US1] Generate Real Family-Based Split: Create `code/ingest/split_generator.py` to generate a stratified split based on chemical prototype/family. **Requirement**: Consume `graphs_v1.parquet` from T013d. **Requirement**: Derive `family_id` by loading structures and using `pymatgen.core.structure.StructureMatcher` to group them by prototype (e.g., 'MXene', 'TMD', 'Graphene'). **Requirement**: Use `sklearn.model_selection.train_test_split` with `random_state=42` and `stratify` based on `family_id` to ensure reproducibility and family separation. **Requirement**: Ensure no training family appears in the test set. Implement a runtime assertion: if any chemical family is present in both train and test sets, exit with code 1. **Requirement**: Overwrite `data/processed/split_indices.json` with this final stratified split. **Requirement**: This split MUST satisfy SC-002 (inter-family generalization). **Requirement**: Dependency: T013d, T013e.
- [ ] T017b [US1] Validate Stratified Split: Create `code/model/splitter.py` to **strictly consume** `split_indices.json` from T013f. **Requirement**: **Do NOT regenerate or overwrite the split**. This task validates that the split provided by T013f is a valid JSON file with required keys. **Requirement**: If `split_indices.json` is missing or invalid, exit with code 1. **Requirement**: Dependency: T013f.
- [ ] T008a [US1] Implement integration test for full-pipeline memory usage: Create `tests/integration/test_memory_full_pipeline.py` that runs the **actual data loading pipeline (T013d)** with a representative sample of real data to verify peak memory < 7GB. **Requirement**: Use a representative sample from `graphs_v1.parquet`. **Requirement**: Consume `split_indices.json` from T017b. **Requirement**: Output memory usage stats to `data/results/memory_test.log`. **Requirement**: Do NOT generate splits; only consume the existing split. **Requirement**: This task explicitly consumes output from T013d and T017b. **Requirement**: **Dependency**: T013d, T017b.
- [X] T014 [US1] Add unit tests for CIF parsing logic in `tests/unit/test_parse_cif.py` (verify disconnected graph handling)
- [X] T015 [US1] Add unit tests for tensor validation in `tests/unit/test_filter.py` (verify 6-component requirement)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Lightweight GNN Training and Evaluation

**Goal**: Train a lightweight GNN on the constructed dataset to predict elastic moduli and evaluate performance against held-out DFT values, including intra-family baseline and inter-family drop.

### Implementation for User Story 2

- [X] T016 [P] [US2] Define lightweight GNN architecture in `code/model/gnn.py` (-3 layers, hidden dim ≤64, CPU-only `torch_geometric`)
- [ ] T018b [US2] Implement training loop in `code/model/train.py`: Train the GNN on the dataset. **Requirement**: Consume `split_indices.json` from T017b. **Requirement**: Enforce CPU-only execution. **Requirement**: Use `tracemalloc` to measure peak memory: `tracemalloc.get_traced_memory()[1]` at each epoch. **Requirement**: If `memory_peak` > 7GB, **dynamically reduce batch size/chunk size**. If memory still exceeds 7GB at minimum batch size (1), exit with code 1. **Requirement**: Save model weights to `data/processed/model_v1.pt`. **Requirement**: Output `predictions.json` for the test set. **Requirement**: If training fails, exit with code 1; do NOT generate a synthetic model. **Requirement**: **Dependency Chain**: T013d -> T013f -> T017b -> T018b. **Requirement**: Dependency: T017b, T046.
- [ ] T018c [US2] Implement training logging and checkpointing in `code/model/train_logger.py`: Log metrics to `data/results/training_logs.json`. **Requirement**: Log schema MUST include `epoch: int`, `loss: float`, `metrics: {mape, rmse}`, `memory_peak: float`. Include metadata key `disclaimer`: "These results are ML interpolations of DFT data, not first-principles solutions." **Dependency**: T018b, T046.
- [X] T019 [US2] Implement evaluation and metrics calculation in `code/model/eval.py` (MAPE, RMSE, R² for Young's, Shear, Poisson)
- [X] T019a [P] [US2] Implement validation and logging of success criteria in `code/model/eval_runner.py`: Calculate MAPE against held-out families and log the result against the threshold. **Requirement**: Load `predictions.json` from T018b and `test_indices` from T017b. **Requirement**: This task can run in parallel with T036b and T021a once T018b is complete. **Dependency**: T017b, T018b.
- [ ] T020a [US2] Implement intra-family baseline metric generation in `code/analysis/ablation.py` (compute MAPE/RMSE on random splits within families to establish baseline for SC-002). **Requirement**: Output `data/results/intra_family_baseline.json`. **Requirement**: Dependency: T018b, T017b.
- [ ] T021b [US2] Inter-Family Validation Gate: Create `code/model/inter_family_validator.py` to **explicitly verify** that the test set contains **ONLY** families NOT present in the training set. **Requirement**: Load `split_indices.json` from T017b. **Requirement**: Assert intersection of train/test family_ids is empty. If not, exit with code 1. **Requirement**: Calculate MAPE on the test set. **Requirement**: Assert MAPE < 0.15. **If MAPE >= 0.15, exit with code 1** and log "SC-002 Failed: Inter-family MAPE >= 15%". **Requirement**: Output `data/results/inter_family_validation.json`. **Requirement**: Dependency: T017b, T018b.
- [ ] T021a [P] [US2] Implement inter-family generalization test in `code/model/generalization_test.py`: Measure MAPE on unseen families; output `data/results/generalization_metrics.json`. **Requirement**: Test set MUST consist of entirely excluded families. Implement a runtime check to ensure no training family appears in the test set: load `split_indices.json`, extract unique `family_id` sets for train and test, assert intersection is empty. **Requirement**: This task can run in parallel with T019a and T036b once T018b is complete. **Requirement**: Dependency: T021b, T018b.
- [X] T021b [US2] Implement metrics aggregation and logging in `code/analysis/aggregate.py`: Combine SHAP, permutation, and generalization metrics into a single intermediate JSON. **Requirement**: Aggregate existing metrics (T020a, T021a) without overwriting. **Dependency**: T046.
- [ ] T036a [US2] Inference Readiness Check: Create `code/model/inference_readiness.py` to estimate inference complexity based on model architecture (T016) and dataset size. **Requirement**: Runs independently of T018b completion to estimate feasibility. **Requirement**: Output `data/results/inference_readiness.json`. **Requirement**: Dependency: T017b.
- [ ] T036b [P] [US2] Verify inference time constraint (SC-003): Implement `code/model/inference_benchmark.py` to measure latency per material on CPU. **Requirement**: Measure latency averaged over multiple runs on the available CPU environment. **Requirement**: Detect and log the specific CPU model (e.g., via `psutil` or `lscpu`) to ensure portability. **Requirement**: Assert `inference_time_ms` < 100. **If >= 100ms, exit with code 1** and log "SC-003 Failed: Inference time >= 100ms". **Requirement**: Output `data/results/inference_benchmark.json`. **Requirement**: This task can run in parallel with T019a and T021a once T018b is complete. **Requirement**: Dependency: T018b, T036a.
- [ ] T027d [US2] Success Criteria Aggregator: Create `code/analysis/success_aggregator.py` to merge `generalization_metrics.json` (T021a) and `inference_benchmark.json` (T036b) into `data/results/final_metrics.json`. **Requirement**: **Hard Gate**: If any underlying metric fails its assertion (MAPE > 15% or Time > 100ms), exit with code 1. **Requirement**: Dependency: T021a, T036b.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance and Ablation Analysis

**Goal**: Identify which structural descriptors most strongly influence predicted elastic moduli and understand the contribution of different descriptor classes.

### Implementation for User Story 3

- [X] T025 [US3] Implement composition-only baseline model in `code/analysis/ablation.py` (feed-forward network on Magpie descriptors, no topology)
- [ ] T023 [US3] Implement SHAP interaction value calculation in `code/analysis/importance.py`: **Requirement**: Dependency: T018b (produces trained model weights artifact), T017b. **Requirement**: Calculate SHAP values for each descriptor. **Requirement**: Perform a bootstrap test with `config.BOOTSTRAP_ITERATIONS` (default 1000) iterations to generate a null hypothesis distribution and calculate p-values for each descriptor. **Requirement**: **Crucial**: Use `random_state=42` for the bootstrap loop to ensure deterministic, reproducible p-values. **Requirement**: Use `random_state=42` for reproducibility. **Requirement**: Output `data/results/shap_pvalues.json` with schema `{descriptor: float (p-value)}`. **Requirement**: Dependency: T018b, T017b.
- [ ] T024 [US3] Implement permutation importance calculation in `code/analysis/importance.py`: **Requirement**: Dependency: T018b (produces trained model weights artifact), T017b. **Requirement**: Calculate permutation importance scores. **Requirement**: Perform a permutation test with `config.PERMUTATION_SHUFFLES` (default 1000) shuffles using a **feature-wise permutation strategy** to generate a null hypothesis distribution and calculate p-values for each descriptor. **Requirement**: **Crucial**: Use `random_state=42` for the permutation shuffles to ensure deterministic, reproducible p-values. **Requirement**: Use `random_state=42` for reproducibility. **Requirement**: Output `data/results/permutation_pvalues.json` with schema `{descriptor: float (p-value)}`. **Requirement**: Dependency: T018b, T017b.
- [X] T026 [US3] Implement ablation study runner in `code/analysis/ablation.py` (compare full GNN vs. composition-only, report MAPE delta). Dependency: T025 AND T018b.
- [X] T027a [US3] Implement data aggregation script in `code/analysis/aggregate.py`: Combine SHAP, permutation, and generalization metrics into a single intermediate JSON.
- [X] T027b [US3] Implement report template generation in `code/analysis/template.py`: Create the Markdown template for the final report.
- [ ] T027c3 [US3] Implement final report assembly in `code/analysis/report_generator.py`: Dependency: T027a, T027b, T021b. Synthesize into a single unified ranked list; output `data/results/feature_importance_report.md` with ablation deltas; frame findings as correlations. **Requirement**: Output format MUST be a Markdown table with columns: `Descriptor`, `Importance Score`, `p-value`, `Description`. **Requirement**: Filter the table to include ONLY descriptors where `p < 0.05`. If fewer than 3 descriptors have p < 0.05, generate a report stating "SC-005 Not Met: Fewer than 3 significant descriptors found" and list the top 3 non-significant descriptors with their p-values, sorted by p-value ascending. **Requirement**: The report MUST state: "The identified descriptors are statistical correlations learned by the surrogate model from DFT data, not fundamental quantum mechanical variables derived from the Hamiltonian." **Requirement**: **Executes immediately after T027b completes**. **Requirement**: Dependency: T046.
- [ ] T027d [US3] Success Criteria Aggregator (Feature Importance): Create `code/analysis/sc5_enforcer.py` to consume `shap_pvalues.json` and `permutation_pvalues.json`. **Requirement**: Count unique descriptors with p < 0.05 across both methods. **Requirement**: **Hard Gate**: If count < 3, exit with code 1 and log "SC-005 Failed: Fewer than 3 significant descriptors found". **Requirement**: Output `data/results/sc5_validation.json`. **Requirement**: Dependency: T023, T024.
- [X] T028 [US3] Add unit tests for SHAP value aggregation in `tests/unit/test_importance.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Documentation & Compliance (Priority: P4)

**Goal**: Finalize all documentation to prevent the "First-Principles" vs "Curve-Fitting" contradiction identified in research reviews.

### Implementation for Phase 6

- [X] T029 [P4] Update `README.md` to explicitly define the project as a "Surrogate Model" that interpolates DFT data. **Requirement**: Must explicitly state: "Random seeds are pinned in `code/utils/config.py`" (referencing the specific file path defined in T004). **Requirement**: Include the Richard Feynman quote: "The first principle is that you must not fool yourself — and you are the easiest person to fool." in a "Scientific Integrity" section. **Requirement**: Add a prominent "Scientific Integrity" banner at the top of the README stating: "This project implements a machine learning surrogate model to interpolate pre-computed DFT data. It does NOT solve the Schrödinger equation or perform first-principles calculations." (Merged scope from T050).
- [X] T030 [P4] Create `docs/methodology.md` detailing the distinction between "First-Principles" and "Surrogate" methods, citing the specific DFT sources used. **Requirement**: Include a "What This Is Not" table comparing DFT and Surrogate methods.
- [X] T031 [P4] Update `docs/contributing.md` to enforce terminology guidelines: forbid the use of "First-Principles" to describe the ML model.
- [X] T032 [P4] Verify Limitations section: Ensure `spec.md` contains Section 5 "Limitations" describing extrapolation failure and lack of physics discovery. **Requirement**: If missing, flag for manual review (Note: T001 already blocks if missing). **Requirement**: Add a bold warning in Section 1: "CRITICAL: This is NOT a first-principles calculation. It is a machine learning surrogate." **Requirement**: Expand Section 5 to explicitly state the model cannot discover new physics or solve the Hamiltonian. (Merged scope from T052).
- [X] T034 [P4] **Review Response**: Audit all source code for "First-Principles" or "Schrödinger" references: Scan `code/`, `docs/` for any remaining instances of forbidden terminology using `grep -r` or a Python script with regex. **Requirement**: Do NOT scan `data/results/`. If found, replace with "Surrogate" or "Interpolation" and log the change in `state/projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate.yaml` under `terminology_audit`. **Requirement**: Dependency: T037.
- [X] T035 [P4] **Review Response**: Update `docs/methodology.md` to include a dedicated section "What This Model Is Not". **Requirement**: Explicitly list: "Not a solution to the Schrödinger equation", "Not a first-principles calculation", "Not a discovery of new quantum mechanical laws", "Not capable of extrapolation to unseen chemical spaces". **Requirement**: Cite the specific review from Richard Feynman (simulated) that prompted this clarification. **Requirement**: Dependency: T030. (Merged scope from T051).

**Checkpoint**: Terminology compliance verified across code, docs, and specification.

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
- **Removed Duplicates**: Tasks T050, T051, T052 have been removed; their scope is fully merged into T029, T034, T035.
- **Removed Orphans**: Task T020 has been removed; its logic is now handled by T017b, T020a, and T021a.
- **Removed Orphans**: Task T053 has been removed; its scope is handled by T001 pre-flight check.
- **New Revision Tasks**: Task T021b (Inter-Family Validation Gate) added to enforce SC-002. Task T027d (Success Criteria Aggregator) added to enforce SC-005. Task T036a (Readiness Check) added to validate inference feasibility.