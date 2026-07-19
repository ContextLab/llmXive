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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and terminology alignment

- [ ] T001 Create project structure: Create directories `code/`, `data/raw/`, `data/processed/`, `data/results/`, `tests/unit/`, `tests/integration/`, `docs/`. **Requirement**: Initialize `state/projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate.yaml` with an empty `artifact_hashes: {}` map to satisfy Constitution Principle III (Data Hygiene) structural requirements. Create `README.md` with reproducibility instructions (referencing Constitution Principle I) and `.gitignore` with specific patterns: `data/*`, `!data/processed/*`, `!data/results/*`, `__pycache__`, `*.pyc`, `.env`.
- [ ] T002 Initialize a Python project with pinned dependencies in `code/requirements.txt`: Include `pymatgen`, `torch`, `torch-geometric`, `shap`, `pandas`, `numpy`, `scikit-learn`, `ruff`, `black`.
- [ ] T003a [Foundation] Configure linting (ruff): Create `.ruff.toml` with strict rules (E, F, W, I) and line-length=88.
- [ ] T003b [Foundation] Configure formatting (black): Create `.black.toml` with line-length=88.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure (config, logging, data models)

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup environment configuration management in `code/utils/config.py` (seeding, paths, CPU limits). **Requirement**: Implement a global seed manager that enforces pinning for `torch`, `numpy`, and `random` across all modules.
- [ ] T004a [Foundation] Verify seed pinning in pipeline: Create a script `code/utils/verify_seeds.py` that runs a dummy pipeline step and asserts that `torch`, `numpy`, and `random` seeds are consistently pinned across imports, satisfying Constitution Principle I (Reproducibility).
- [ ] T005 Implement logging infrastructure in `code/utils/logger.py` (structured logs for bias checks)
- [ ] T006 Create base constants and conversion factors in `code/utils/constants.py` (elastic modulus units)
- [ ] T007 Define the `MaterialGraph` data schema in `code/data_models/material_graph.py` (nodes, edges, targets)
- [ ] T008 Implement dynamic sampling strategy in `code/utils/memory_utils.py`. **Requirement**: Implement a unit test in `tests/unit/test_memory_utils.py` that tests the *logic* of the sampler (e.g., chunk size calculation) without mocking the full data loading pipeline. The unit test verifies the *algorithm*, not the memory usage of a full run. (required for FR-007/SC-004).
- [ ] T046 [Foundation] Implement "Surrogate Model Disclaimer" in all output artifacts: Modify the following specific scripts to include a mandatory disclaimer field: `code/model/train_logger.py`, `code/model/eval_runner.py`, `code/analysis/report_generator.py`. **Requirement**: The disclaimer must state: "These results are derived from a machine learning surrogate model interpolating pre-computed DFT data. They do not represent first-principles calculations or solutions to the Schrödinger equation." **Requirement**: This disclaimer must be included in the metadata of every JSON output and at the top of every Markdown report. **Requirement**: Include "Scientific Integrity Statement" in all reports. **Requirement**: Dependency: None.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 (MVP)

**Goal**: Data ingestion and graph construction

**Independent Test**: The script can be run to download a subset of materials, parse their CIFs into graphs using `pymatgen`, and output a JSON/CSV summary of node counts, edge counts, and target values without requiring any model training.

### Implementation for User Story 1

- [ ] T009 [US1] Implement unified dataset loader in `code/ingest/download.py` that abstracts Materials Project/AFLOW into a single canonical source per run (satisfying Constitution Principle I) and explicitly documents data is from *existing* DFT (not generated here). **Requirement**: Include a "Warning" docstring stating: "WARNING: This model is a surrogate interpolator trained on pre-computed DFT data. It does NOT solve the Schrödinger equation or perform first-principles calculations."
- [ ] T009a [US1] Implement runtime source enforcement in `code/ingest/validator.py`: Add a check that raises a hard error if more than one data source is active in a single run, satisfying the "single canonical source" constraint. **Requirement**: Use a global singleton flag or a lock file to detect concurrent/mixed source activation. **Requirement**: If check fails, raise `SystemExit(1)` with a clear error message. **Requirement**: Implement logic to persist the source identity to a state file (e.g., `data/.source_state`) and compare it across runs to enforce the constraint against user error.
- [ ] T009b [US1] Implement Unified Loader Abstraction: Create `code/ingest/loader_base.py` defining an abstract base class `DataLoader` with methods `fetch_data()`, `validate_source()`, and `get_metadata()`. **Requirement**: This class must support dynamic switching between 'materials_project' and 'aflow' via a configuration key. **Requirement**: Concrete implementations for each source must inherit from this base.
- [ ] T010 [US1] Implement CIF parser in `code/ingest/parse_cif.py` (convert to `MaterialGraph` using `pymatgen`, extract node/edge features)
- [ ] T011 [US1] Implement 2D filter and tensor validator in `code/ingest/filter.py`. **Requirement**: Explicitly filter for entries with **independent elastic tensor components** as mandated by Constitution Principle VI (DFT Ground-Truth Fidelity). Log exclusion reasons for entries with incomplete tensors.
- [ ] T012 [US1] Implement bias check for excluded entries in `code/ingest/bias_check.py` (log reasons for exclusion, flag small families)
- [ ] T013a [US1] Implement data download in `code/ingest/download.py`: Download raw CIF and tensor data from the single canonical source. **Requirement**: Use `os.getenv('DATA_SOURCE', 'materials_project')` to select the source; default to 'materials_project' if not set. **Requirement**: Implement the logic to call the `DataLoader` base class (T009b) to fetch data. **Requirement**: Verify checksums against source. **Requirement**: Read `data/.source_state` (if exists) and compare with `DATA_SOURCE` env var; if mismatch, raise `SystemExit(1)` with error "Source mismatch: State file indicates {state_source}, but DATA_SOURCE={env_source}".
- [ ] T013b [US1] Implement data parsing in `code/ingest/parse_cif.py`: Parse CIFs into `MaterialGraph` objects. **Requirement**: Handle disconnected graphs and missing fields gracefully.
- [ ] T013c [US1] Implement data filtering in `code/ingest/filter.py`: Filter for 2D materials and valid tensors. **Requirement**: Log exclusion reasons.
- [ ] T013d [US1] Create data pipeline orchestration script in `code/ingest/pipeline.py` (download -> parse -> filter -> save to `data/processed/graphs_v1.parquet`). **Requirement**: Output schema MUST include `node_features`, `edge_features`, `target_moduli`, `family_id`. Implement error handling for missing tensors. **Requirement**: After saving, generate SHA256 checksum for `graphs_v1.parquet` using `hashlib.sha256()` and record it in `state/projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate.yaml` under the key `artifact_hashes.data_processed.graphs_v1_parquet` with format `algorithm: sha256:<hex_digest>` using `yaml.safe_load` and `yaml.dump`. **Requirement**: If `data_processed` or `graphs_v1_parquet` keys do not exist, create them. **Requirement**: This task does NOT generate splits; it only generates the data. **Dependency**: T009a, T009b, T010, T011, T012.
- [ ] T013e [US1] Verify Volume Constraint: Add a post-processing check in `code/ingest/pipeline.py` that counts the number of unique 2D material entries in `data/processed/graphs_v1.parquet`. **Requirement**: If the count is less than a critical threshold, **exit with code 1** and log a critical error: "SC-001 Violation: Pipeline failed to ingest >1,000 entries. Current count: {count}." **Requirement**: Do NOT proceed to training if this check fails. **Dependency**: T013d.
- [ ] T013f [US1] Generate MVP Split: Create `code/ingest/split_generator.py` to generate a random/mock split for MVP testing. **Requirement**: Consume `graphs_v1.parquet` from T013d. **Requirement**: Use `sklearn.model_selection.train_test_split` with `random_state=42` and `stratify` based on `family_id` to ensure reproducibility. **Requirement**: Overwrite `data/processed/split_indices.json` with this mock split. **Requirement**: Add a disclaimer in the output file: "This is a mock split for MVP testing only. It does NOT satisfy SC-002 (inter-family generalization)." **Dependency**: T013d.
- [ ] T008a [US1] Implement integration test for full-pipeline memory usage: Create `tests/integration/test_memory_full_pipeline.py` that runs the **actual data loading pipeline (T013d)** with a representative sample of real data to verify peak memory < 7GB. **Requirement**: Use the first 50 entries from `graphs_v1.parquet` as the representative sample. **Requirement**: Consume `split_indices.json` from T013f. **Requirement**: Output memory usage stats to `data/results/memory_test.log`. **Requirement**: Do NOT generate splits; only consume the existing split. **Dependency**: T013d, T013f.
- [ ] T014 [US1] Add unit tests for CIF parsing logic in `tests/unit/test_parse_cif.py` (verify disconnected graph handling)
- [ ] T015 [US1] Add unit tests for tensor validation in `tests/unit/test_filter.py` (verify 6-component requirement)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Lightweight GNN Training and Evaluation

**Goal**: Train a lightweight GNN on the constructed dataset to predict elastic moduli and evaluate performance against held-out DFT values, including intra-family baseline and inter-family drop.

### Implementation for User Story 2

- [ ] T016 [P] [US2] Define lightweight GNN architecture in `code/model/gnn.py` (-3 layers, hidden dim ≤64, CPU-only `torch_geometric`)
- [ ] T017 [US2] Implement stratified splitting logic in `code/model/splitter.py` (split by chemical prototype/space group to ensure family separation). **Requirement**: Consume `graphs_v1.parquet` from T013d and `split_indices.json` from T013f. **Requirement**: Ensure no training family appears in the test set. Implement a runtime assertion: if any family is present in both sets, exit with code 1 and log an error message. **Requirement**: Overwrite `data/processed/split_indices.json` with this final stratified split. **Requirement**: This split MUST satisfy SC-002 (inter-family generalization). **Dependency**: T013d, T013f.
- [ ] T018a [US2] Implement training configuration in `code/model/train_config.py`: Define hyperparameters, early stopping patience, and CPU constraints.
- [ ] T018b [US2] Implement training loop in `code/model/train.py`: Train the GNN on the dataset. **Requirement**: Consume `split_indices.json` from T017. **Requirement**: Enforce CPU-only execution. **Requirement**: Log `memory_peak` at each epoch. **Requirement**: If `memory_peak` > 7GB, exit with code 1. **Requirement**: Save model weights to `data/processed/model_v1.pt`. **Requirement**: Output `predictions.json` for the test set. **Requirement**: If training fails, exit with code 1; do NOT generate a synthetic model. **Dependency**: T017, T046.
- [ ] T018c [US2] Implement training logging and checkpointing in `code/model/train_logger.py`: Log metrics to `data/results/training_logs.json`. **Requirement**: Log schema MUST include `epoch: int`, `loss: float`, `metrics: {mape, rmse}`, `memory_peak: float`. Include metadata key `disclaimer`: "These results are ML interpolations of DFT data, not first-principles solutions." **Dependency**: T018b, T046.
- [ ] T019 [US2] Implement evaluation and metrics calculation in `code/model/eval.py` (MAPE, RMSE, R² for Young's, Shear, Poisson)
- [ ] T019a [US2] Implement validation and logging of success criteria in `code/model/eval_runner.py`: Calculate MAPE against held-out families and log the result against the threshold. **Requirement**: Load `predictions.json` from T018b and `test_indices` from T017. **Dependency**: T017, T018b.
- [ ] T020 [US2] Implement a k-fold cross-validation runner in `code/model/cv_runner.py`
- [ ] T020a [US2] Implement intra-family baseline metric generation in `code/analysis/ablation.py` (compute MAPE/RMSE on random splits within families to establish baseline for SC-002)
- [ ] T021a [US2] Implement inter-family generalization test in `code/model/generalization_test.py`: Measure MAPE on unseen families; output `data/results/generalization_metrics.json`. **Requirement**: Test set MUST consist of entirely excluded families. Implement a runtime check to ensure no training family appears in the test set: load `split_indices.json`, extract unique `family_id` sets for train and test, assert intersection is empty. **Dependency**: T017, T018b.
- [ ] T021b [US2] Implement metrics aggregation and logging in `code/analysis/aggregate.py`: Combine SHAP, permutation, and generalization metrics into a single intermediate JSON. **Requirement**: Aggregate existing metrics (T020a, T021a) without overwriting. **Dependency**: T046.
- [ ] T036 [US2] Verify inference time constraint (SC-003): Implement `code/model/inference_benchmark.py` to measure latency per material on CPU. **Requirement**: Measure latency averaged over multiple runs on the available CPU environment. **Requirement**: Detect and log the specific CPU model (e.g., via `psutil` or `lscpu`) to ensure portability. Ensure the output in `data/results/generalization_metrics.json` includes `inference_time_ms`, `cpu_model`, and confirms it is < 100ms. **Dependency**: T018b.
- [ ] T046 [US2] **DEPRECATED**: This task has been moved to Phase 2 (Foundational). All disclaimer logic is now implemented in T046 (Phase 2). **Dependency**: None.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance and Ablation Analysis

**Goal**: Identify which structural descriptors most strongly influence predicted elastic moduli and understand the contribution of different descriptor classes.

### Implementation for User Story 3

- [ ] T025 [US3] Implement composition-only baseline model in `code/analysis/ablation.py` (feed-forward network on Magpie descriptors, no topology)
- [ ] T023 [US3] Implement SHAP interaction value calculation in `code/analysis/importance.py`: Dependency: T018b (produces trained model weights artifact), T017. **Requirement**: Calculate and output `p-values` for each descriptor based on the SHAP values using a bootstrap method with a sufficient number of iterations and a confidence interval of 95%.
- [ ] T024 [US3] Implement permutation importance calculation in `code/analysis/importance.py`: Dependency: T018b (produces trained model weights artifact), T017. **Requirement**: Calculate and output `p-values` for each descriptor based on the permutation scores using a permutation test with a sufficient number of permutations and a null hypothesis: no correlation.
- [ ] T026 [US3] Implement ablation study runner in `code/analysis/ablation.py` (compare full GNN vs. composition-only, report MAPE delta). Dependency: T025 AND T018b.
- [ ] T027a [US3] Implement data aggregation script in `code/analysis/aggregate.py`: Combine SHAP, permutation, and generalization metrics into a single intermediate JSON.
- [ ] T027b [US3] Implement report template generation in `code/analysis/template.py`: Create the Markdown template for the final report.
- [ ] T027c3 [US3] Implement final report assembly in `code/analysis/report_generator.py`: Dependency: T027a, T027b, T021b. Synthesize into a single unified ranked list; output `data/results/feature_importance_report.md` with ablation deltas; frame findings as correlations. **Requirement**: Output format MUST be a Markdown table with columns: `Descriptor`, `Importance Score`, `p-value`, `Description`. **Requirement**: Filter the table to include ONLY descriptors where `p < 0.05`. If fewer than 3 descriptors have p < 0.05, generate a report stating "SC-005 Not Met: Fewer than 3 significant descriptors found" and list the top 3 non-significant descriptors with their p-values, sorted by p-value ascending. **Requirement**: The report MUST state: "The identified descriptors are statistical correlations learned by the surrogate model from DFT data, not fundamental quantum mechanical variables derived from the Hamiltonian." **Dependency**: T046.
- [ ] T028 [US3] Add unit tests for SHAP value aggregation in `tests/unit/test_importance.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Documentation & Compliance (Priority: P4)

**Goal**: Finalize all documentation to prevent the "First-Principles" vs "Curve-Fitting" contradiction identified in research reviews.

### Implementation for Phase 6

- [ ] T029 [P4] Update `README.md` to explicitly define the project as a "Surrogate Model" that interpolates DFT data. **Requirement**: Must explicitly state: "Random seeds are pinned in `code/utils/config.py`" (referencing the specific file path defined in T004).
- [ ] T030 [P4] Create `docs/methodology.md` detailing the distinction between "First-Principles" and "Surrogate" methods, citing the specific DFT sources used.
- [ ] T031 [P4] Update `docs/contributing.md` to enforce terminology guidelines: forbid the use of "First-Principles" to describe the ML model.
- [ ] T032 [P4] Verify Limitations section: Ensure `spec.md` contains Section 5 "Limitations" describing extrapolation failure and lack of physics discovery. If missing, flag for manual review.
- [ ] T033 [P4] **Review Response**: Audit all source code for "First-Principles" or "Schrödinger" references: Scan `code/`, `docs/` for any remaining instances of forbidden terminology using `grep -r` or a Python script with regex. **Requirement**: Do NOT scan `data/results/`. If found, replace with "Surrogate" or "Interpolation" and log the change in `state/projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate.yaml` under `terminology_audit`.
- [ ] T037 [P4] **Review Response**: Implement automated terminology scanner in `code/utils/terminology_scanner.py`: Create a script that scans all source files and documentation (`code/`, `docs/`) for forbidden terms ("First-Principles", "Schrödinger", "Hamiltonian" in the context of the ML model).

**Checkpoint**: Terminology compliance verified across code and docs.

---

## Phase 7: Review Resolution & Terminology Enforcement (Priority: P4)

**Goal**: Directly address the "Richard Feynman" review concern that the project was mislabeled as "First-Principles" when it is actually curve-fitting.

### Implementation for Review Resolution

- [ ] T049 [P4] **Review Response**: Update `spec.md` with Feynman quote and 'What This Is Not' table: Add a section titled "What This Is Not" to spec.md, including the comparative table detailing Method, Cost, Physics Solved, Input Data, and Underlying Equation. **Requirement**: This task must be completed before T041 and T042 are considered fully satisfied.

**Checkpoint**: Review resolution complete.

---

## Phase 8: Pre-Flight Validation (Priority: P4)

**Goal**: Ensure absolute adherence to the "Richard Feynman" review feedback by verifying that all documentation, code, and reports explicitly distinguish the Surrogate Model from First-Principles methods.

### Implementation for Pre-Flight Validation

- [ ] T051 [P4] **DEPRECATED**: This task is a duplicate of T037. T037 is the authoritative terminology scanner. **Requirement**: No action required.

**Checkpoint**: Pre-flight validation ready.

---

## Phase 9: Feynman Review Deep-Dive & Scientific Rigor (Priority: P5)

**Goal**: Address the specific "Richard Feynman" review critique that "curve-fitting" is being mislabeled as "First-Principles" by adding rigorous validation that the model is purely interpolative and does not claim to solve quantum mechanical equations.

### Implementation for Review Response

- [ ] T041 [P5] **Review Response**: Update `spec.md` with Feynman quote and table. **Dependency**: T049.
- [ ] T042 [P5] **Review Response**: Add "What This Is Not" section to `docs/methodology.md`. **Dependency**: T049.
- [ ] T043 [P5] **Review Response**: Implement "Interpolation Validity Check".

**Checkpoint**: Feynman review concerns fully addressed with rigorous validation and explicit disclaimers.

---

## Phase 10: Feynman Review Final Verification & Artifact Correction (Priority: P5)

**Goal**: Ensure the final implementation strictly adheres to the "Richard Feynman" review feedback by verifying that all documentation, code, and reports explicitly distinguish the Surrogate Model from First-Principles methods, and that no terminology violations remain.

### Implementation for Final Verification

- [ ] T046 [P5] **DEPRECATED**: This task has been moved to Phase 2. All disclaimer logic is implemented in T046 (Phase 2). **Requirement**: No action required.
- [ ] T047 [P5] **Review Response**: Add "Extrapolation Risk Assessment" to `data/results/feature_importance_report.md`.
- [ ] T048 [P5] **Review Response**: Implement "Feynman Integrity Audit".

**Checkpoint**: Final review compliance verified. All terminology, disclaimers, and scientific integrity checks are in place.

---

## Phase 11: Final Review Compliance & Verification (Priority: P5)

**Goal**: Ensure the final implementation strictly adheres to the "Richard Feynman" review feedback by verifying that all documentation, code, and reports explicitly distinguish the Surrogate Model from First-Principles methods, and that no terminology violations remain.

### Implementation for Final Verification

- [ ] T049 [P5] **DEPRECATED**: This task has been moved to Phase 7. T049 in Phase 7 is the authoritative update task. **Requirement**: No action required.
- [ ] T052 [P5] **Review Response**: Final verification of `spec.md` title and abstract: Scan `spec.md` to ensure the title is exactly "Structure-Only Surrogate Model for 2D Material Elastic Moduli" and the abstract explicitly states: "This project implements a machine learning surrogate model to interpolate pre-computed DFT results. It does NOT solve the Schrödinger equation or perform first-principles calculations." **Dependency**: T049.

**Checkpoint**: Final verification complete. All artifacts are corrected and verified against the "Richard Feynman" review feedback.

---

## Phase 12: Final Verification & Cleanup (Priority: P5)

**Goal**: Ensure the final implementation strictly adheres to the "Richard Feynman" review feedback by verifying that all documentation, code, and reports explicitly distinguish the Surrogate Model from First-Principles methods, and that no terminology violations remain.

### Implementation for Final Verification

- [ ] T053 [P5] **Review Response**: Verify `spec.md` and `docs/methodology.md` contain the Feynman quote and "What This Is Not" table. **Dependency**: T049.
- [ ] T054 [P5] **Review Response**: Verify `README.md` contains the Feynman quote and description. **Dependency**: T035.
- [ ] T055 [P5] **Review Response**: Verify `docs/methodology.md` "What This Is Not" section is expanded to explicitly contrast the ML approach with DFT. **Dependency**: T036.

**Checkpoint**: Final verification complete. All artifacts are corrected and verified against the "Richard Feynman" review feedback.