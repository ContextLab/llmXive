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
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, title correction, and basic structure

- [X] T001 Create project structure: Create directories `code/`, `data/raw/`, `data/processed/`, `data/results/`, `tests/unit/`, `tests/integration/`, `docs/`. **Requirement**: Initialize `state/projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate.yaml` with an empty `artifact_hashes: {}` map to satisfy Constitution Principle III (Data Hygiene) structural requirements. Create `README.md` with reproducibility instructions (referencing Constitution Principle I) and `.gitignore` with specific patterns: `data/*`, `!data/processed/*`, `!data/results/*`, `__pycache__`, `*.pyc`, `.env`.
- [X] T002 Initialize a Python project with pinned dependencies in `code/requirements.txt`: Include `pymatgen`, `torch`, `torch-geometric`, `shap`, `pandas`, `numpy`, `scikit-learn`, `ruff`, `black`.
- [X] T003a [Foundation] Configure linting (ruff): Create `.ruff.toml` with strict rules (E, F, W, I) and line-length=88.
- [X] T003b [Foundation] Configure formatting (black): Create `.black.toml` with line-length=88.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup environment configuration management in `code/utils/config.py` (seeding, paths, CPU limits). **Requirement**: Implement a global seed manager that enforces pinning for `torch`, `numpy`, and `random` across all modules.
- [X] T004a [Foundation] Verify seed pinning in pipeline: Create a script `code/utils/verify_seeds.py` that runs a dummy pipeline step and asserts that `torch`, `numpy`, and `random` seeds are consistently pinned across imports, satisfying Constitution Principle I (Reproducibility).
- [X] T005 Implement logging infrastructure in `code/utils/logger.py` (structured logs for bias checks)
- [X] T006 Create base constants and conversion factors in `code/utils/constants.py` (elastic modulus units)
- [X] T007 Define the `MaterialGraph` data schema in `code/data_models/material_graph.py` (nodes, edges, targets)
- [X] T008 Implement dynamic sampling strategy in `code/utils/memory_utils.py`. **Requirement**: Implement a unit test in `tests/unit/test_memory_utils.py` that tests the *logic* of the sampler (e.g., chunk size calculation) without mocking the full data loading pipeline. The unit test verifies the *algorithm*, not the memory usage of a full run. (required for FR-007/SC-004).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Graph Construction (Priority: P1) 🎯 MVP

**Goal**: Download CIF files and elastic tensors from public repositories, filter for 2D materials, and convert to graph representations using a unified canonical source.

**Independent Test**: The script can be run to download a subset of materials, parse their CIFs into graphs using `pymatgen`, and output a JSON/CSV summary of node counts, edge counts, and target values without requiring any model training.

### Implementation for User Story 1

- [X] T009 [US1] Implement unified dataset loader in `code/ingest/download.py` that abstracts Materials Project/AFLOW into a single canonical source per run (satisfying Constitution Principle I) and explicitly documents data is from *existing* DFT (not generated here). **Requirement**: Include a "Warning" docstring stating: "WARNING: This model is a surrogate interpolating pre-computed DFT results. It does NOT solve the Schrödinger equation or perform first-principles calculations."
- [X] T009a [US1] Implement runtime source enforcement in `code/ingest/validator.py`: Add a check that raises a hard error if more than one data source is active in a single run, satisfying the "single canonical source" constraint. **Requirement**: Use a global singleton flag or a lock file to detect concurrent/mixed source activation. **Requirement**: If check fails, raise `SystemExit(1)` with a clear error message.
- [X] T009b [US1] Implement Unified Loader Abstraction: Create `code/ingest/loader_base.py` defining an abstract base class `DataLoader` with methods `fetch_data()`, `validate_source()`, and `get_metadata()`. **Requirement**: This class must support dynamic switching between 'materials_project' and 'aflow' via a configuration key. **Requirement**: Concrete implementations for each source must inherit from this base.
- [X] T010 [US1] Implement CIF parser in `code/ingest/parse_cif.py` (convert to `MaterialGraph` using `pymatgen`, extract node/edge features)
- [X] T011 [US1] Implement 2D filter and tensor validator in `code/ingest/filter.py`. **Requirement**: Explicitly filter for entries with **independent elastic tensor components** as mandated by Constitution Principle VI (DFT Ground-Truth Fidelity). Log exclusion reasons for entries with incomplete tensors.
- [X] T012 [US1] Implement bias check for excluded entries in `code/ingest/bias_check.py` (log reasons for exclusion, flag small families)
- [X] T013 [US1] **Placeholder**: Replaced by T013a-d sequence.
- [X] T013a [US1] Implement data download in `code/ingest/download.py`: Download raw CIF and tensor data from the single canonical source. **Requirement**: Use `os.getenv('DATA_SOURCE', 'materials_project')` to select the source; default to 'materials_project' if not set. **Requirement**: Implement the logic to call the `DataLoader` base class (T009b) to fetch data. **Requirement**: Verify checksums against source.
- [X] T013b [US1] Implement data parsing in `code/ingest/parse_cif.py`: Parse CIFs into `MaterialGraph` objects. **Requirement**: Handle disconnected graphs and missing fields gracefully.
- [X] T013c [US1] Implement data filtering in `code/ingest/filter.py`: Filter for 2D materials and valid tensors. **Requirement**: Log exclusion reasons.
- [ ] T013d [US1] Create data pipeline orchestration script in `code/ingest/pipeline.py` (download -> parse -> filter -> save to `data/processed/graphs_v1.parquet`). **Requirement**: Output schema MUST include `node_features`, `edge_features`, `target_moduli`, `family_id`. Implement error handling for missing tensors. **Requirement**: After saving, generate SHA256 checksum for `graphs_v1.parquet` using `hashlib.sha256()` and record it in `state/projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate.yaml` under the key `artifact_hashes.data_processed.graphs_v1_parquet` with format `algorithm: sha256:<hex_digest>` using `yaml.safe_load` and `yaml.dump`. Example: `artifact_hashes:\n data_processed:\n graphs_v1_parquet: sha256:abc123...`. **Requirement**: Output the final `split_indices` (train/val/test) used for evaluation to `data/processed/split_indices.json` as a **list of objects**: `[{\"id\": \"mp-123\", \"family_id\": \"TMD_1\"},...]`. **Requirement**: Each object MUST contain `id` (material ID) and `family_id` (string). **Dependency**: T009a, T009b, T010, T011, T012.
- [ ] T013e [US1] Verify Volume Constraint: Add a post-processing check in `code/ingest/pipeline.py` (or a separate script) that counts the number of unique 2D material entries in `data/processed/graphs_v1.parquet`. **Requirement**: If the count is less than 1,000, **exit with code 1** and log a critical error: "SC-001 Violation: Pipeline failed to ingest >1,000 entries. Current count: {count}." **Requirement**: Do NOT proceed to training if this check fails.
- [X] T014 [US1] Add unit tests for CIF parsing logic in `tests/unit/test_parse_cif.py` (verify disconnected graph handling)
- [X] T015 [US1] Add unit tests for tensor validation in `tests/unit/test_filter.py` (verify 6-component requirement)
- [X] T008a [US1] Implement integration test for full-pipeline memory usage: Create `tests/integration/test_memory_full_pipeline.py` that runs the actual data loading (T013d) with a **synthetic dataset of 1,000+ materials**. **Requirement**: The synthetic dataset generator MUST replicate the *graph topology* (node/edge counts) and *feature dimensionality* (vector sizes) of the real 2D materials to ensure the memory footprint is a valid proxy. **Requirement**: Log the synthetic data structure parameters (e.g., avg nodes, avg edges, feature dim) to verify fidelity. **Requirement**: Verify peak memory < 7GB. **Dependency**: T013d must be complete to provide `graphs_v1.parquet`. (required for SC-004). <!-- ATOMIZE: requested -->

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Lightweight GNN Training and Evaluation (Priority: P2)

**Goal**: Train a lightweight GNN on the constructed dataset to predict elastic moduli and evaluate performance against held-out DFT values, including intra-family baseline and inter-family drop.

**Independent Test**: The training script can be executed on a CPU-only environment, training for a specified number of epochs, and outputting a JSON report with MAPE, RMSE, and R² scores for the test set.

### Implementation for User Story 2

- [X] T016 [P] [US2] Define lightweight GNN architecture in `code/model/gnn.py` (-3 layers, hidden dim ≤64, CPU-only `torch_geometric`)
- [X] T017 [US2] Implement stratified splitting logic in `code/model/splitter.py` (split by chemical prototype/space group to ensure family separation). **Requirement**: Output `split_indices.json` with train/val/test splits. **Requirement**: The splitting logic MUST group materials by `family_id` first, then split the groups to ensure no family appears in both train and test sets. **Requirement**: Include a runtime assertion: if any `family_id` appears in both train and test sets, **exit with code 1** and log "SC-002 Violation: Family overlap detected in split." **Requirement**: Output schema MUST be a list of objects `[{\"id\": \"...\", \"family_id\": \"...\"},...]`. **Dependency**: T013d.
- [X] T018 [US2] **Placeholder**: Replaced by T018a-c sequence.
- [X] T018a [US2] Implement training configuration in `code/model/train_config.py`: Define hyperparameters, early stopping patience, and CPU constraints.
- [ ] T018b [US2] Implement training loop in `code/model/train.py`: Train the GNN on the dataset. **Requirement**: Consume `split_indices` from T017. **Requirement**: Enforce CPU-only execution. **Requirement**: Log `memory_peak` at each epoch. **Requirement**: If `memory_peak` > 7GB, exit with code 1. **Requirement**: Save model weights to `data/processed/model_v1.pt`. **Requirement**: Output `predictions.json` for the test set.
- [ ] T018c [US2] Implement training logging and checkpointing in `code/model/train_logger.py`: Log metrics to `data/results/training_logs.json`. **Requirement**: Log schema MUST include `epoch: int`, `loss: float`, `metrics: {mape, rmse}`, `memory_peak: float`. **Requirement**: Include metadata key `disclaimer`: "These results are ML interpolations of DFT data, not first-principles solutions."
- [X] T019 [US2] Implement evaluation and metrics calculation in `code/model/eval.py` (MAPE, RMSE, R² for Young's, Shear, Poisson)
- [ ] T019a [US2] Implement validation and logging of success criteria in `code/model/eval_runner.py`: Calculate MAPE against held-out families and log the result against the threshold. **Requirement**: Load `predictions.json` from T018b and `test_indices` from T017. **Dependency**: T017. **Requirement**: If `inter_family_mape` is not in `data/results/generalization_metrics.json`, compute it from predictions and test indices. **Requirement**: Compare computed MAPE to a predefined threshold. **Requirement**: Log pass/fail status to `data/results/generalization_metrics.json`. **Requirement**: Do not halt execution; log pass/fail status. <!-- ATOMIZE: requested -->
- [X] T020 [US2] Implement a k-fold cross-validation runner in `code/model/cv_runner.py`
- [X] T020a [US2] Implement intra-family baseline metric generation in `code/model/baseline_metrics.py` (compute MAPE/RMSE on random splits within families to establish baseline for SC-002)
- [X] T021 [US2] **Placeholder**: Replaced by T021a-b sequence.
- [ ] T021a [US2] Implement inter-family generalization test in `code/model/generalization_test.py`: Dependency: T017, T018b, **T013d**. Measure MAPE on unseen families; output `data/results/generalization_metrics.json`. **Requirement**: Test set MUST consist of entirely excluded families. Implement a runtime check to ensure no training family appears in the test set using the `test_indices` from T017 and the `family_id` column in `data/processed/graphs_v1.parquet`. The check compares unique `family_id` sets between train and test splits. **Requirement**: Consume `predictions.json` from T018b and `split_indices` from T017. **Requirement**: Compute `intra_family_mape` from T020a and `inter_family_mape` from the test set. **Requirement**: If the runtime check fails (e.g., no valid test families found), output a failure report to `data/results/generalization_metrics.json` stating the error and halt. **Requirement**: Include metadata key `disclaimer`: "These results are ML interpolations of DFT data, not first-principles solutions."
- [ ] T021b [US2] Implement metrics aggregation and logging in `code/model/metrics_aggregator.py`: Combine T020a and T021a results into `data/results/generalization_metrics.json`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance and Ablation Analysis (Priority: P3)

**Goal**: Identify which structural descriptors most strongly influence predicted elastic moduli and understand the contribution of different descriptor classes.

**Independent Test**: The analysis script can run on the trained model to generate SHAP values and ablation study results, outputting a single unified ranked list and performance deltas.

### Implementation for User Story 3

- [X] T025 [US3] Implement composition-only baseline model in `code/analysis/ablation.py` (feed-forward network on Magpie descriptors, no topology)
- [X] T023 [US3] Implement SHAP interaction value calculation in `code/analysis/importance.py`: Dependency: T018b (produces trained model weights artifact), T017. (using `shap` library on GNN inputs). **Requirement**: Calculate and output `p-values` for each descriptor based on the SHAP values using a **bootstrap method** with **sufficient iterations** and **95% confidence interval**. **Dependency Note**: This task requires the trained model from T018b to be complete.
- [X] T024 [US3] Implement permutation importance calculation in `code/analysis/importance.py`: Dependency: T018b (produces trained model weights artifact), T017. (rank top structural descriptors). **Requirement**: Calculate and output `p-values` for each descriptor based on the permutation scores using a **permutation test** with a **sufficient number of permutations** and **null hypothesis: no correlation**. **Dependency Note**: This task requires the trained model from T018b to be complete.
- [ ] T026 [US3] Implement ablation study runner in `code/analysis/ablation.py` (compare full GNN vs. composition-only, report MAPE delta). Dependency: T025 AND T018b. **Dependency Note**: This task requires the trained model from T018b to be complete.
- [X] T027a [US3] Implement data aggregation script in `code/analysis/aggregate.py`: Combine SHAP, permutation, and generalization metrics into a single intermediate JSON. **Requirement**: Ensure the `p-value` for each descriptor is included in the aggregated output.
- [X] T027b [US3] Implement report template generation in `code/analysis/template.py`: Create the Markdown template for the final report.
- [ ] T027c3 [US3] Implement final report assembly in `code/analysis/report_generator.py`: Dependency: T027a, T027b, **T021b**. Synthesize into a **single unified ranked list**; output `data/results/feature_importance_report.md` with ablation deltas; frame findings as correlations. **Requirement**: Output format MUST be a Markdown table with columns: `Descriptor`, `Importance Score`, `p-value`, `Description`. **Requirement**: Filter the table to include **ONLY** descriptors where `p < 0.05`. **Requirement**: Use p-values from T024 (permutation) as primary source; T023 (SHAP) for confirmation. **Requirement**: If fewer than 3 descriptors have `p < 0.05`, generate a report stating "SC-005 Not Met: Fewer than 3 significant descriptors found" and list the top 3 non-significant descriptors with their p-values, sorted by p-value ascending. **Requirement**: **Do NOT exit with code 1**; the pipeline must complete and log the failure status. **Requirement**: The report MUST state: "The identified descriptors are statistical correlations learned by the surrogate model from DFT data, not fundamental quantum mechanical variables derived from the Hamiltonian." **Requirement**: If upstream tasks (e.g., T021b) fail, the report must reflect this error state.
- [X] T028 [US3] Add unit tests for SHAP value aggregation in `tests/unit/test_importance.py`

**Checkpoint**: All user stories should now be independently functional (Note: T027b and T027c3 are now complete, so US3 is fully shippable).

---

## Phase 6: Documentation & Compliance (Priority: P4)

**Goal**: Finalize all documentation to prevent the "First-Principles" vs "Curve-Fitting" contradiction identified in research reviews.

### Implementation for Phase 6

- [ ] T029 [P4] Update `README.md` to explicitly define the project as a "Surrogate Model" that interpolates DFT data. **Requirement**: Must explicitly state: "Random seeds are pinned in `code/utils/config.py`" (referencing the specific file path defined in T004). **Requirement**: "External datasets are fetched from the same canonical source on every run" to satisfy Constitution Principle I (Reproducibility).
- [X] T030 [P4] Create `docs/methodology.md` detailing the distinction between "First-Principles" (DFT) and "Surrogate" (ML) methods, citing the specific DFT sources used.
- [X] T031 [P4] Update `docs/contributing.md` to enforce terminology guidelines: forbid the use of "First-Principles" to describe the ML model.
- [X] T032 [P4] Verify Limitations section: Ensure `spec.md` contains Section 5 "Limitations" describing extrapolation failure and lack of physics discovery. If missing, flag for manual review.
- [X] T033 [P4] **Review Response**: Audit all source code for "First-Principles" or "Schrödinger" references: Scan `code/`, `docs/` for any remaining instances of forbidden terminology using `grep -r` or a Python script with regex. **Requirement**: Do NOT scan `data/results/`. If found, replace with "Surrogate" or "Interpolation" and log the change in `state/projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate.yaml` under `terminology_audit`. **Requirement**: **After modifying the YAML file, explicitly update the `updated_at` timestamp** to satisfy Constitution Principle V (Versioning Discipline).
- [ ] T037 [P4] **Review Response**: Implement automated terminology scanner in `code/utils/terminology_scanner.py`: Create a script that recursively scans all source files and documentation (`code/`, `docs/`) for forbidden terms ("First-Principles", "Schrödinger", "Hamiltonian" in the context of the ML model, "solve equation"). **Requirement**: The scanner must flag all occurrences for manual review. Output a JSON report to `data/results/terminology_audit.json` listing file paths, line numbers, and context of any violations. **Requirement**: Do NOT scan `data/results/`.

**Checkpoint**: Terminology compliance verified across code and docs.

---

## Phase 7: Review Resolution & Terminology Enforcement (Priority: P4)

**Goal**: Directly address the "Richard Feynman" review concern that the project was mislabeled as "First-Principles" when it is actually curve-fitting.

### Implementation for Review Resolution

- [X] T034 [P4] **Review Response**: Update `docs/methodology.md` to explicitly refute the "First-Principles" claim: Add a section titled "What This Is Not" that clearly states: "This project does NOT solve the Schrödinger equation. It does NOT calculate electron density from the Hamiltonian. It is a statistical interpolator trained on pre-computed DFT data."
- [X] T035 [P4] **Review Response**: Update `README.md` title and description: Ensure the main project title in `README.md` matches the spec ("Structure-Only Surrogate Model") and includes the Feynman quote: "Don't fool yourself — and you are the easiest person to fool" as a warning against mislabeling curve-fitting as physics.
- [ ] T036 [P4] **Review Response**: Verify inference time constraint (SC-003): Implement `code/model/inference_benchmark.py` to measure latency per material on CPU. **Requirement**: Measure latency averaged over **50 runs** on the **available CPU environment**. **Requirement**: Detect and log the specific CPU model (e.g., via `psutil` or `lscpu`) to ensure portability. Ensure the output in `data/results/generalization_metrics.json` includes `inference_time_ms`, `cpu_model`, and confirms it is < 100ms. **Dependency**: T018b (trained model).
- [X] T039 [P4] **Review Response**: Refine `docs/methodology.md` "What This Is Not" section: Expand the section to explicitly contrast the ML approach with DFT. Include a table comparing: "Method", "Computational Cost", "Physics Solved", "Input Data", "Output Type". **Requirement**: Ensure the table clearly states "Surrogate Model" solves "None (Statistical Interpolation)" for "Physics Solved" and "DFT Results" for "Input Data".
- [X] T040 [P4] **Review Response**: Add unit tests for terminology compliance in `tests/unit/test_terminology_scanner.py`: Verify the scanner correctly identifies forbidden terms and allows legitimate scientific context. Test cases must include edge cases where terms appear in citations or historical context versus active claims.

**Checkpoint**: Review resolution complete.

---

## Phase 8: Pre-Flight Validation (Priority: P4)

**Goal**: Ensure absolute adherence to the "Surrogate" vs "First-Principles" distinction across all project artifacts, addressing the specific "Richard Feynman" review feedback.

### Implementation for Pre-Flight Validation

- [ ] T038 [P4] **Review Response**: Implement pre-flight documentation compliance check in `code/utils/verify_doc_compliance.py`: Create a script that scans `README.md` and `docs/methodology.md` for the mandatory disclaimer statements defined in T034/T035. **Requirement**: The script must search for the exact strings: "This project does NOT solve the Schrödinger equation", "Random seeds are pinned", and the Feynman quote. **Requirement**: If any string is missing, the script must **exit with code 1** (do NOT raise RuntimeError inside other scripts). **Requirement**: This script is intended to be run as a pre-flight check (CI or manual) before executing the pipeline. **Requirement**: Do NOT include this check inside `code/ingest/pipeline.py` or `code/model/train.py`. **Dependency**: T034, T035.

**Checkpoint**: Pre-flight validation ready.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Documentation (Phase 6)**: Can run in parallel with US1-US2, but must be finalized before final release.
- **Review Resolution (Phase 7)**: Must be completed before final release to ensure terminology compliance.
- **Pre-Flight Validation (Phase 8)**: Must be run before final release.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 (needs `data/processed/` graphs)
- **User Story 3 (P3)**: Depends on US2 (needs trained model and metrics)

### Within Each User Story

- **US1**: T013a (Download) -> T009a (Validator) -> T013b (Parse) -> T013c (Filter) -> T013d (Orchestrate) -> T013e (Volume Check) -> T014/T015 (Tests depend on T013d) -> T008a (Memory test depends on T013d). **Note**: T009a validates the configuration used by T013a. T013d orchestrates the logic of T013a-c.
- **US2**: T017 (Split) -> T018a (Config) -> T018b (Train) -> T018c (Log) -> T020a (Baseline) -> T021a (Generalization) -> T021b (Metrics) -> T019a (Threshold Check). **Note**: T021a must run strictly after T018b completes and writes `predictions.json`.
- **US3**: T025 (Baseline Train) AND T018b (Main Train) -> T023/T024 (Importance) -> T026 (Ablation) -> T027a -> T027b -> T027c3 (Report). **Note**: T023/T024/T026 require the trained model from T018b. T027c3 requires T021b.

### Parallel Opportunities

- **Setup**: T002, T003a, T003b can run in parallel after T001.
- **Foundational**: T004-T007 can run in parallel.
- **US1**: T014, T015 can run in parallel after T009-T013d. T008a can run after T013d.
- **US2**: T016, T022 can run in parallel; T020a and T021a depend on T018b.
- **US3**: T028 can run in parallel with T027a-T027c3 after T023-T026.
- **Phase 6 & 7**: T030-T034 can run in parallel. T029 and T035 (README finalization) must be sequential after code freeze (T004, T018b, T036).
- **Phase 8**: T037, T039, T040 can run in parallel. T038 depends on T034/T035 (doc updates) and is a pre-flight check.

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
- **Memory Constraint**: T008 (Unit) and T008a (Integration) must verify 7GB limit. T008a uses a synthetic dataset of 1,000+ materials with structurally identical features to the real data.
- **Data Constraint**: T009 and T009a must enforce single canonical source per run; T001 and T013d must record checksums.
- **Metric Constraint**: T019a + T021 must compute intra/inter family MAPE and enforce % threshold.
- **Report Constraint**: T027c3 must output a single unified ranked list filtered for p < 0.05, with explicit failure handling (log status, do NOT exit).
- **Review Address**: T033-T036 explicitly resolve the "First-Principles" vs "Curve-Fitting" contradiction by enforcing terminology compliance, updating documentation to explicitly deny solving the Schrödinger equation, and verifying inference speed. T029-T032 also contribute to this resolution.
- **Phase 6 Addition**: T037 moved to Phase 6 to ensure clean codebase before review resolution.
- **Phase 8 Addition**: T038 is now a standalone pre-flight check, not a runtime assertion in pipeline scripts.
- **Constraint Clarification**: SC-004 is now explicitly defined as "Peak memory usage ≤ 7GB" for testability.
- **Dependency Clarification**: T021a strictly follows T018b; T023/T024/T026 strictly follow T018b. T004a is a foundation task. T027c3 strictly follows T021b. T008a strictly follows T013d.
- **Artifact Producer Clarification**: T013d produces `split_indices.json` (list of objects with `family_id`). T018b consumes `split_indices.json` and produces `predictions.json`. T021a consumes `predictions.json` and `split_indices.json` to produce `generalization_metrics.json`.
- **Duplicate Removal**: T036 is unique (Phase 7). T027c1/T027c2 removed; T027a/T027b retained.
- **Schema Clarification**: `split_indices.json` is now a list of objects `{\"id\": \"...\", \"family_id\": \"...\"}` to ensure T021a can access `family_id` directly.
- **Volume Constraint**: T013e enforces SC-001 as a hard gate (exit 1 if < 1000 entries).
- **Split Logic**: T017 enforces family separation at the splitting stage (exit 1 if overlap).
- **Abstraction Layer**: T009b implements the unified loader abstraction to satisfy the plan's architectural decision.