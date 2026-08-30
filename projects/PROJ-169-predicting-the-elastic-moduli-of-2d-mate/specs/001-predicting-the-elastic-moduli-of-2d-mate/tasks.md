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

**Purpose**: Project initialization, mandatory terminology alignment, and Constitutional Title Amendment to satisfy Constitution Principle III (Data Hygiene) structural requirements before any implementation begins.

- [X] T001a [Setup] Create project directories: Create directories `code/`, `data/raw/`, `data/processed/`, `data/results/`, `tests/unit/`, `tests/integration/`, `docs/`.
- [X] T001b [Setup] Initialize state file: Initialize `state/projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate.yaml` with an empty `artifact_hashes: {}` map to satisfy Constitution Principle III (Data Hygiene) structural requirements. The YAML schema must include `artifact_hashes` as a dictionary mapping file paths to SHA256 checksums. **Template**: `artifact_hashes: {}`. **Requirement**: This task is a prerequisite for T001c.
- [X] T001c [Setup] Compute and Record Artifact Hashes: Create `code/utils/hash_manager.py` to compute SHA256 checksums for all files under `data/` (specifically `graphs_v1.parquet`, `split_indices.json`, `model_v1.pt`, and all files in `data/results/`) and update `state/projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate.yaml` under `artifact_hashes`. **Requirement**: This task must run after any data generation task to satisfy Constitution Principle IV (Single Source of Truth). **Requirement**: Dependency: T001b.
- [X] T001d [Setup] Create README and.gitignore: Create `README.md` with reproducibility instructions (referencing Constitution Principle I) and `.gitignore` with specific patterns: `data/*`, `!data/processed/*`, `!data/results/*`, `__pycache__`, `*.pyc`, `.env`.
- [X] T002 [Setup] Initialize Python project: Create `code/requirements.txt` with pinned dependencies: `pymatgen`, `torch`, `torch-geometric`, `shap`, `pandas`, `numpy`, `scikit-learn`, `ruff`, `black`.
- [X] T003a [Setup] Configure linting (ruff): Create `.ruff.toml` with strict rules (E, F, W, I) and line-length=88.
- [X] T003b [Setup] Configure formatting (black): Create `.black.toml` with line-length=88.

### Constitutional Title Amendment (Phase 1 Critical Path)

- [X] T060a [Setup] Draft Constitutional Amendment: Create `state/amendments/Constitutional_Amendment_01.md` documenting the formal amendment of the Constitution (FR-030) title. **Requirement**: Document the rationale (contradiction between 'First-Principles' title and 'Surrogate' Spec). **Requirement**: Generate a Sync Impact Report as required by FR-030. **Requirement**: **Artifact Path**: `state/amendments/Sync_Impact_Report_01.md`. **Requirement**: **Schema**: `{"amendment_id": "01", "rationale": "string", "impact": "list of files"}`. **Requirement**: Dependency: None.
- [X] T060b [Setup] Edit Constitution File: Create `code/utils/constitution_editor.py` to perform the title replacement. **Requirement**: Use the regex pattern `^#\s+.*First-Principles.*$` to locate the title line in `constitution.md` and replace it with `# Structure-Only Surrogate Model for 2D Material Elastic Moduli`. **Requirement**: Update the version line in `constitution.md` to reflect the amendment. **Requirement**: **Process**: This task must NOT directly edit the file without a PR. It must generate a diff or patch file for the formal amendment procedure (open PR, update version line, record Sync Impact Report). **Requirement**: This task resolves the 'Single Source of Truth' contradiction by physically updating the governing document. **Requirement**: Dependency: T060a.
- [X] T060c [Setup] Verify Constitution Update: Create `code/utils/verify_constitution_title.py` to scan `constitution.md` for the exact phrase "Structure-Only Surrogate Model" in the title. **Requirement**: If "First-Principles" is found in the title, exit with code 1 and message "FATAL: Constitution title still claims 'First-Principles'". **Requirement**: If correct, output `data/results/constitution_title_audit.json` with status "PASS". **Requirement**: This task is a HARD GATE; all subsequent tasks depend on its success. **Requirement**: Dependency: T060b.

- [X] T004 [Foundation] Configure environment: Create `code/utils/config.py` (seeding, paths, CPU limits). **Requirement**: Implement a global seed manager that enforces pinning for `torch`, `numpy`, and `random` across all modules. **Requirement**: Define `MIN_ENTRY_THRESHOLD = 1000`, `MAX_MEMORY_GB = 7.0`, `BOOTSTRAP_ITERATIONS = 1000`, `PERMUTATION_SHUFFLES = 1000` constants in this config file. **Requirement**: Full import path: `code.utils.config`.
- [X] T004a [Foundation] Verify seed pinning: Create `code/utils/verify_seeds.py` that runs a dummy pipeline step and asserts that `torch`, `numpy`, and `random` seeds are consistently pinned across imports, satisfying Constitution Principle I (Reproducibility).
- [X] T005 [Foundation] Implement logging: Create `code/utils/logger.py` (structured logs for bias checks).
- [X] T006 [Foundation] Define constants: Create `code/utils/constants.py` (elastic modulus units).
- [X] T007 [Foundation] Define data schema: Create `code/data_models/material_graph.py` (nodes, edges, targets).
- [X] T008 [Foundation] Implement memory utils: Create `code/utils/memory_utils.py` for dynamic sampling. **Requirement**: Implement a unit test in `tests/unit/test_memory_utils.py` that tests the *logic* of the sampler (e.g., chunk size calculation) without mocking the full data loading pipeline. The unit test verifies the *algorithm*, not the memory usage of a full run. (required for FR-007/SC-004).
- [X] T046a [Foundation] Create disclaimer template: Create `code/utils/disclaimer_template.py` containing the mandatory disclaimer string and the Richard Feynman quote as a shared constant. **Requirement**: This constant must be imported by all reporting modules to ensure a Single Source of Truth for project-wide text.
- [X] T037 [Foundation] Implement terminology scanner: Create `code/utils/terminology_scanner.py` to scan `code/`, `docs/` for forbidden terms ("First-Principles", "Schrödinger", "Hamiltonian" in the context of the ML model). **Requirement**: Add to `pre-commit` hooks. **Requirement**: Update existing comments in `code/` to replace forbidden terms with "Surrogate" or "Interpolation".
- [X] T009b [US1] Implement Lock Manager: Create `code/ingest/lock_manager.py` to handle `data/.source_state` lock file lifecycle. **Requirement**: Implement `acquire_lock()`, `release_lock()`, and `cleanup_expired_locks()` functions using `filelock`. **Requirement**: Implement logic to automatically delete lock files older than a configurable threshold to prevent permanent blocks on re-runs. **Requirement**: This task has NO dependencies and must be completed before T009a.
- [X] T009a [US1] Implement runtime source enforcement: Create `code/ingest/validator.py` to raise a hard error if more than one data source is active in a single run. **Requirement**: Use the lock file at `data/.source_state` managed by `code/ingest/lock_manager.py` (T009b). **Requirement**: Explicitly define the JSON schema: `data/.source_state` must contain `{"active_source": "string"}`. **Requirement**: If `active_source` is null, missing, or contains >1 entry, raise `SystemExit(1)`. **Requirement**: Explicitly state: "Switching sources is only allowed between runs, not within a run." **Requirement**: **Constitutional Reference**: This task enforces Constitution Principle IV (Single Source of Truth) as a pre-condition for the pipeline's validity. **Requirement**: Dependency: T009b.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 (MVP)

**Goal**: Data ingestion and graph construction

**Independent Test**: The script can be run to download a subset of materials, parse their CIFs into graphs using `pymatgen`, and output a JSON/CSV summary of node counts, edge counts, and target values without requiring any model training.

### Implementation for User Story 1

- [X] T009 [US1] Implement unified dataset loader: Create `code/ingest/loader_base.py` defining an abstract base class `DataLoader` with methods `fetch_data()`, `validate_source()`, and `get_metadata()`. **Requirement**: Support dynamic switching between 'materials_project' and 'aflow' via configuration. **Requirement**: Concrete implementations must inherit from this base.
- [X] T010 [US1] Implement CIF parser: Create `code/ingest/parse_cif.py` (convert to `MaterialGraph` using `pymatgen`, extract node/edge features).
- [X] T011 [US1] Implement 2D filter and tensor validator: Create `code/ingest/filter.py`. **Requirement**: Explicitly filter for entries with **independent elastic tensor components** as mandated by Constitution Principle VI. Log exclusion reasons.
- [X] T011a [US1] Validate DFT Ground-Truth Fidelity: Create `code/ingest/continuum_validator.py` to verify that derived Young's/Shear/Poisson values strictly follow continuum mechanics relations from the elastic tensor without hard-coding. **Requirement**: Implement the standard continuum mechanics formulas (Voigt/Reuss/Hill averaging) explicitly in code. **Requirement**: Assert that the derived values match the formulas within a tight tolerance. **Requirement**: Log any deviations. **Requirement**: Satisfies Constitution Principle VI (DFT Ground-Truth Fidelity). **Requirement**: Dependency: T011.
- [X] T012 [US1] Implement bias check: Create `code/ingest/bias_check.py` (log reasons for exclusion, flag small families).
- [X] T013d1 [US1] Implement download logic: Create `code/ingest/download_worker.py` to fetch raw data from the configured source. **Requirement**: **Acquire lock file data/.source_state using `code/ingest/lock_manager.py` (T009b) before fetching** and **Release lock on completion**. **Requirement**: Output to `data/raw/source_data.json`. **Requirement**: Dependency: T009b, T009.
- [X] T013d2 [US1] Implement parse logic: Create `code/ingest/parse_worker.py` to convert raw data to `MaterialGraph` objects. **Requirement**: Dependency: T010.
- [X] T013d3 [US1] Implement filter logic: Create `code/ingest/filter_worker.py` to apply 2D and tensor filters. **Requirement**: Dependency: T011.
- [X] T013d4 [US1] Implement save logic: Create `code/ingest/save_worker.py` to serialize graphs to `data/processed/graphs_v1.parquet`. **Requirement**: Output to `data/processed/graphs_v1.parquet`. **Requirement**: Output schema MUST include `node_features` (List[List[float]] with inner dimension representing node embeddings), `edge_features` (List[List[float]] with inner dimension), `target_moduli` (Dict[str, float64]), `family_id` (str), **`structure_pickle` (bytes, pickle protocol 4)**, and **`cif_raw` (string, UTF-8)**. **Requirement**: **Requirement**: `structure_pickle` must be serializable via `pickle.dumps(structure, protocol=4)` and `cif_raw` must be the raw CIF string. **Requirement**: Dependency: T012.
- [X] T013d0_define [US1] Define Orchestration Logic: Create `code/ingest/pipeline.py` to define the orchestration logic that imports and calls the functions defined in the worker tasks (T013d1-d4). **Requirement**: This task *defines* the orchestration logic. **Requirement**: Dependency: T013d1, T013d2, T013d3, T013d4, T009a.
- [X] T013d0_impl [US1] Implement Worker Imports: Finalize `code/ingest/pipeline.py` to import and orchestrate the worker logic defined in T013d1, T013d2, T013d3, T013d4. **Requirement**: This task *implements* the imports and calls. **Requirement**: Dependency: T013d0_define.
- [X] T013f [US1] Generate Real Family-Based Split: Create `code/ingest/split_generator.py` to generate a stratified split based on chemical prototype/family. **Requirement**: Consume `graphs_v.parquet` from T013d4. **Requirement**: **Deserialize `structure_pickle` using `pickle.load` (protocol 4) or parse `cif_raw` using `pymatgen.io.cif.CifParser`** to reconstruct `pymatgen.Structure` objects before matching. **Requirement**: Derive `family_id` by using `pymatgen.core.structure.StructureMatcher` with parameters `lattice_tol=0.01`, `position_tol=0.1`, `angle_tol=5.0` to group them by prototype. **Requirement**: Use `sklearn.model_selection.train_test_split` with `random_state=42` and `stratify` based on `family_id`. **Requirement**: Ensure no training family appears in the test set. **Guarantee**: The split generation logic MUST guarantee SC-002 compliance by design (enforcing family separation algorithmically before write). **Requirement**: **Atomically write** `data/processed/split_indices.json` with this final stratified split **using `tempfile.mkstemp` in the same directory as the target, then `os.rename` to the final path**. **Requirement**: If the file is not written successfully, exit with code 1. **Requirement**: This split MUST satisfy SC-002 (inter-family generalization). **Requirement**: Dependency: T013d4.
- [X] T017b [US1] Validate Stratified Split: Create `code/model/splitter.py` to **strictly consume** `split_indices.json` from T013f. **Requirement**: **Do NOT regenerate or overwrite the split**. This task validates that the split provided by T013f is a valid JSON file with required keys. **Requirement**: If `split_indices.json` is missing or invalid, exit with code 1. **Requirement**: Output `data/results/split_validation.json` (or exit code 1). **Requirement**: Dependency: T013f.
- [X] T008a [US1] Implement integration test: Create `tests/integration/test_memory_full_pipeline.py` that runs the **actual data loading pipeline (T013d0_impl)** with a representative sample of real data to verify peak memory < 7GB. **Requirement**: Use a representative sample from `graphs_v1.parquet`. **Requirement**: Consume `split_indices.json` from T017b. **Requirement**: Output memory usage stats to `data/results/memory_test.log`. **Requirement**: Do NOT generate splits; only consume the existing split. **Requirement**: This task explicitly consumes output from T013d0_impl and T017b. **Requirement**: **Dependency**: T013d0_impl, T013d1, T013d2, T013d3, T013d4, T017b.
- [X] T014 [US1] Add unit tests for CIF parsing: Create `tests/unit/test_parse_cif.py` (verify disconnected graph handling).
- [X] T015 [US1] Add unit tests for tensor validation: Create `tests/unit/test_filter.py` (verify 6-component requirement).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Lightweight GNN Training and Evaluation

**Goal**: Train a lightweight GNN on the constructed dataset to predict elastic moduli and evaluate performance against held-out DFT values, including intra-family baseline and inter-family drop.

### Implementation for User Story 2

- [X] T016 [P] [US2] Define GNN architecture: Create `code/model/gnn.py` (-3 layers, hidden dim ≤64, CPU-only `torch_geometric`). **Requirement**: Define the model as a `nn.Module` subclass named `ElasticGNN` that is instantiable without external data.
- [X] T018c-def [US2] Define Memory Enforcement Interface: Create `code/model/memory_enforcer.py` and define the static interface for memory profiling. **Requirement**: Implement a function `validate_model_interface(model_class: Type[nn.Module])` that accepts **only the model class definition** (not an instance) from T016. **Requirement**: Verify the class signature, layer count, and parameter types match the CPU constraints (hidden dim ≤64). **Requirement**: This task establishes the contract T018b must follow but does NOT perform runtime tracing. **Requirement**: Dependency: T016.
- [X] T018c-impl [US2] Implement Memory Enforcement Logic: Create `code/model/memory_enforcer.py` (extend) to implement the dynamic profiling algorithm. **Requirement**: Implement `profile_training_epoch(model_instance: nn.Module, loader: DataLoader)` which **instantiates the model** (or accepts an instance) and uses `tracemalloc` to measure peak memory during a forward/backward pass. **Requirement**: Implement the specific algorithm for dynamic batch size reduction: "Start with batch size 64. If peak memory > 7GB, halve batch size and retry epoch. Repeat until batch size = 1. If batch size = 1 and memory > 7GB, **exit with code 1** and log 'SC-004 Failed: Memory limit exceeded even with batch size 1'." **Requirement**: Log `memory_peak` and `final_batch_size` to `data/results/training_logs.json`. **Requirement**: **Requirement**: This utility must accept a model *instance* for dynamic profiling. **Requirement**: Dependency: T018c-def.
- [X] T018d [US2] End-to-End Memory Validation: Create `code/model/full_pipeline_memory_test.py` to run a **full end-to-end training cycle** (loading + training) and verify that the **combined peak memory** remains under 7GB. **Requirement**: Use `tracemalloc` to measure peak memory across the entire pipeline execution. **Requirement**: **Hard Gate**: If peak memory > 7GB, exit with code 1 and log "SC-004 Failed: Combined peak memory > 7GB". **Requirement**: Output `data/results/full_pipeline_memory.json`. **Requirement**: Dependency: T013d0_impl, T017b, T018c-impl.
- [X] T046 [US2] Implement disclaimer (Integration): Modify `code/model/train_logger.py`, `code/model/eval_runner.py` to import and use the disclaimer string from `code/utils/disclaimer_template.py` (T046a). **Requirement**: Include "Scientific Integrity Statement" and the Richard Feynman quote in all reports. **Requirement**: Dependency: T046a, T016, T018c-impl.
- [X] T018b [US2] Implement training loop: Create `code/model/train.py` to train the GNN on the dataset. **Requirement**: Consume `split_indices.json` from T017b. **Requirement**: Enforce CPU-only execution. **Requirement**: Use `tracemalloc` to measure peak memory. **Requirement**: Integrate `memory_enforcer` from T018c-impl to dynamically reduce batch size. **Requirement**: Save model weights to `data/processed/model_v1.pt`. **Requirement**: Output `predictions.json` for the test set. **Requirement**: If training fails, exit with code 1; do NOT generate a synthetic model. **Requirement**: **Compliance Constraint**: Must include T046 disclaimer in output. **Requirement**: Dependency: T017b, T016, T018c-impl.
- [X] T019 [US2] Implement evaluation: Create `code/model/eval.py` (MAPE, RMSE, R² for Young's, Shear, Poisson).
- [X] T019a [P] [US2] Implement validation and logging: Create `code/model/eval_runner.py` to calculate MAPE against held-out families and log the result against the threshold. **Requirement**: Load `predictions.json` from T018b and `test_indices` from T017b. **Requirement**: This task can run in parallel with T021a and T036b once T018b is complete. **Dependency**: T017b, T018b.
- [X] T020a [US2] Implement intra-family baseline: Create `code/analysis/ablation.py` to compute MAPE/RMSE on random splits within families to establish baseline for SC-002. **Requirement**: Output `data/results/intra_family_baseline.json`. **Requirement**: Dependency: T018b, T017b.
- [X] T020b [US2] Stratified Cross-Validation: Create `code/analysis/cross_val.py` to perform stratified cross-validation across families to substantiate claims about material family predictability. **Requirement**: Satisfies Constitution Principle VII (Structural Descriptor Attribution). **Requirement**: Output `data/results/stratified_cv_results.json`. **Requirement**: Dependency: T018b, T017b.
- [X] T021a [US2] Implement inter-family generalization test: Create `code/model/generalization_test.py` to measure MAPE on unseen families. **Requirement**: Test set MUST consist of entirely excluded families. Implement a runtime check to ensure no training family appears in the test set: load `split_indices.json`, extract unique `family_id` sets for train and test, assert intersection is empty. **Requirement**: Output `data/results/generalization_metrics.json`. **Requirement**: This task can run in parallel with T019a and T036b once T018b is complete. **Requirement**: Dependency: T018b, T017b.
- [X] T021b [US2] Inter-Family Validation Gate: Create `code/model/inter_family_validator.py` to **explicitly verify** that the test set contains **ONLY** families NOT present in the training set. **Requirement**: Load `split_indices.json` from T017b. **Requirement**: Assert intersection of train/test family_ids is empty. If not, exit with code 1. **Requirement**: Calculate MAPE on the test set. **Requirement**: **If MAPE >= 0.15, log a warning and flag the model as 'insufficient' in `inter_family_validation.json` (do NOT exit with code 1)**. **Requirement**: Output `data/results/inter_family_validation.json` with a `status` field ("PASS" or "INSUFFICIENT"). **Requirement**: Dependency: T021a, T017b.
- [X] T027a [US3] Implement data aggregation: Create `code/analysis/aggregate.py` to combine SHAP, permutation, and generalization metrics into a single intermediate JSON. **Requirement**: Aggregate existing metrics (T023, T024, T021a) directly. **Requirement**: Dependency: T023, T024, T021a.
- [X] T036a [US2] Inference Readiness Check: Create `code/model/inference_readiness.py` to estimate inference complexity based on model architecture (T016) and dataset size. **Requirement**: Runs independently of T018b completion to estimate feasibility. **Requirement**: Output `data/results/inference_readiness.json`. **Requirement**: Dependency: T017b.
- [X] T036b [US2] Verify inference time constraint: Create `code/model/inference_benchmark.py` to measure latency per material on CPU. **Requirement**: **Implement lightweight inference function** to perform actual predictions on the test set. **Requirement**: Measure latency averaged over multiple runs on the available CPU environment. **Requirement**: Detect and log the specific CPU model (e.g., via `psutil` or `lscpu`) to ensure portability. **Requirement**: Assert `inference_time_ms` < 100. **If >= 100ms, exit with code 1** and log "SC-003 Failed: Inference time >= 100ms". **Requirement**: Output `data/results/inference_benchmark.json`. **Requirement**: This task can run in parallel with T019a and T021a once T018b is complete. **Requirement**: Dependency: T018b, T017b.
- [X] T027d [US2] Success Criteria Aggregator: Create `code/analysis/success_aggregator.py` to merge `generalization_metrics.json` (T021a), `inference_benchmark.json` (T036b), and **`inter_family_validation.json` (T021b)** into `data/results/final_metrics.json`. **Requirement**: **Hard Gate**: If T021b status is "INSUFFICIENT" (MAPE >= 15%) or T036b fails, exit with code 1. **Requirement**: Dependency: T021a, T036b, **T021b**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance and Ablation Analysis

**Goal**: Identify which structural descriptors most strongly influence predicted elastic moduli and understand the contribution of different descriptor classes.

### Implementation for User Story 3

- [X] T025 [US3] Implement composition-only baseline: Create `code/analysis/ablation.py` (feed-forward network on Magpie descriptors, no topology). **Requirement**: Output `data/results/composition_baseline.json`. **Requirement**: Dependency: T018b.
- [X] T023 [US3] Implement SHAP calculation: Create `code/analysis/importance.py` to calculate SHAP values for each descriptor using `DeepExplainer` with a background sample of graphs. **Requirement**: **Use a portion of the training set as the background sample for DeepExplainer**. **Requirement**: Perform a bootstrap test with a sufficient number of iterations to generate a null hypothesis distribution and calculate p-values for each descriptor. **Requirement**: **Crucial**: Use `random_state=42` for the bootstrap loop to ensure deterministic, reproducible p-values. **Requirement**: **Note**: The iteration count is fixed at `config.BOOTSTRAP_ITERATIONS`. **Requirement**: **Calculate p-value as the proportion of shuffled scores >= original score**. **Requirement**: Output `data/results/shap_pvalues.json` with schema `{descriptor: float (p-value)}`. **Requirement**: Dependency: T018b, T017b.
- [X] T024 [US3] Implement permutation importance: Create `code/analysis/importance.py` to calculate permutation importance scores using a **graph-level permutation strategy** (shuffling entire graphs). **Requirement**: Perform a permutation test with a sufficient number of shuffles using the drop in R² as the metric. **Requirement**: **Crucial**: Use `random_state=42` for the permutation shuffles to ensure deterministic, reproducible p-values. **Requirement**: **Note**: The iteration count is fixed as defined in config; do not tune. **Requirement**: **Calculate p-value as the proportion of shuffled scores >= original score**. **Requirement**: Output `data/results/permutation_pvalues.json` with schema `{descriptor: float (p-value)}`. **Requirement**: Dependency: T018b, T017b.
- [X] T026 [US3] Implement ablation study: Create `code/analysis/ablation.py` to compare full GNN vs. composition-only, report MAPE delta. **Requirement**: Output `data/results/ablation_report.json`. **Requirement**: Dependency: T025 AND T018b.
- [X] T027c1 [US3] Generate and Filter Feature Importance: Create `code/analysis/table_generator.py` to combine `shap_pvalues.json` and `permutation_pvalues.json` into a raw data table, filter for descriptors with `p < 0.05`, and output `data/results/significant_descriptors.csv`. **Requirement**: **Output p-values with 4 decimal places**. **Requirement**: Dependency: T023, T024.
- [X] T027c2 [US3] Implement final report assembly: Create `code/analysis/report_generator.py` to synthesize into a single unified ranked list; output `data/results/feature_importance_report.md` with ablation deltas; frame findings as correlations. **Requirement**: Load `significant_descriptors.csv` from T027c1. **Requirement**: **Sort by unrounded p-values from T027c1 (before rounding for display)**. **Requirement**: Format as Markdown table with columns: `Descriptor`, `Importance Score`, `p-value`, `Description`. **Requirement**: The report MUST state: "The identified descriptors are statistical correlations learned by the surrogate model from DFT data, not fundamental quantum mechanical variables derived from the Hamiltonian." **Requirement**: **Rounding**: Round float values to **four decimal places** for display. **Requirement**: Dependency: T046a, T027c1.
- [X] T027e [US3] Success Criteria Aggregator (Feature Importance): Create `code/analysis/sc5_enforcer.py` to consume `shap_pvalues.json` and `permutation_pvalues.json`. **Requirement**: Count unique descriptors with p < 0.05 across both methods. **Requirement**: **Hard Gate**: If count < 3, exit with code 1 and log "SC-005 Failed: Fewer than 3 significant descriptors found". **Requirement**: Output `data/results/sc5_validation.json`. **Requirement**: Dependency: T023, T024.
- [X] T028 [US3] Add unit tests for SHAP: Create `tests/unit/test_importance.py`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Documentation & Compliance (Priority: P4)

**Goal**: Finalize all documentation to prevent the "First-Principles" vs "Curve-Fitting" contradiction identified in research reviews.

### Implementation for Phase 6

- [X] T029 [P4] Update README: Update `README.md` to explicitly define the project as a "Surrogate Model" that interpolates DFT data. **Requirement**: Must explicitly state: "Random seeds are pinned in `code/utils/config.py`" (referencing the specific file path defined in T004). **Requirement**: Include the Richard Feynman quote: "The first principle is that you must not fool yourself — and you are the easiest person to fool." in a "Scientific Integrity" section. **Requirement**: Add a prominent "Scientific Integrity" banner at the top of the README stating: "This project implements a machine learning surrogate model to interpolate pre-computed DFT data. It does NOT solve the Schrödinger equation or perform first-principles calculations."
- [X] T030a [P4] Verify Citations: Create `code/utils/citation_validator.py` to implement the Reference-Validator Agent logic. **Requirement**: Verify external citations in `docs/methodology.md` against primary sources before finalizing. **Requirement**: Satisfies Constitution Principle II (Verified Accuracy). **Requirement**: Output `data/results/citation_validation.json`. **Requirement**: Dependency: T030.
- [X] T030 [P4] Create methodology docs: Create `docs/methodology.md` detailing the distinction between "First-Principles" and "Surrogate" methods, citing the specific DFT sources used. **Requirement**: Include a "What This Is Not" table comparing DFT and Surrogate methods. **Requirement**: Dependency: T030a.
- [X] T031 [P4] Update contributing docs: Update `docs/contributing.md` to enforce terminology guidelines: forbid the use of "First-Principles" to describe the ML model.
- [X] T032 [P4] Verify Limitations section: Ensure `spec.md` contains Section 5 "Limitations" describing extrapolation failure and lack of physics discovery. **Requirement**: If missing, flag for manual review. **Requirement**: Add a bold warning in Section 1: "CRITICAL: This is NOT a first-principles calculation. It is a machine learning surrogate." **Requirement**: Expand Section 5 to explicitly state the model cannot discover new physics or solve the Hamiltonian.
- [X] T034 [P4] **Review Response**: Audit all source code: Scan `code/`, `docs/` for any remaining instances of forbidden terminology using `grep -r` or a Python script with regex. **Requirement**: Do NOT scan `data/results/`. If found, replace with "Surrogate" or "Interpolation" and log the change in `state/projects/PROJ-169-predicting-the-elastic-moduli-of-2d-mate.yaml` under `terminology_audit`. **Requirement**: Dependency: T037.
- [X] T035 [P4] **Review Response**: Update `docs/methodology.md` to include a dedicated section "What This Model Is Not". **Requirement**: Explicitly list: "Not a solution to the Schrödinger equation", "Not a first-principles calculation", "Not a discovery of new quantum mechanical laws", "Not capable of extrapolation to unseen chemical spaces". **Requirement**: Cite the specific review from Richard Feynman (simulated) that prompted this clarification. **Requirement**: Dependency: T030.

**Checkpoint**: Terminology compliance verified across code, docs, and specification.

---

## Phase 7: Scientific Integrity & Review Response (Priority: P5)

**Goal**: Address the specific "Richard Feynman (simulated)" review regarding the distinction between interpolation and first-principles physics.

### Implementation for Phase 7

- [X] T054 [P5] **Review Response**: Verify Title Alignment: Create `code/utils/title_verifier.py` to scan `spec.md`, `README.md`, `docs/methodology.md`, `plan.md`, and **`constitution.md`** for the exact phrase "Structure-Only Surrogate Model" in the project title or summary. **Requirement**: If "First-Principles" is found in the title, exit with code 1 and message "FATAL: Project title still claims 'First-Principles'. Review T054/T055/T056/T060". **Requirement**: If not found, output `data/results/title_audit.json` with status "PASS" and a list of files scanned. **Requirement**: This task verifies that the spec title matches the current implementation plan. **Requirement**: **Note**: The `spec.md` title is already correct in the current revision. This task verifies the title and content alignment. **Requirement**: **CRITICAL**: The Constitution (FR-030) title update is handled by Task T060. **Requirement**: Dependency: T060c.
- [X] T055 [P5] **Review Response**: Update `docs/methodology.md` to include a "Feynman's Warning" section. **Requirement**: Quote: "The first principle is that you must not fool yourself — and you are the easiest person to fool." **Requirement**: Explicitly explain that fitting a GNN to DFT data is "curve-fitting" or "interpolation" and not "first-principles" physics, acknowledging the reviewer's point that one cannot claim to solve the Hamiltonian when using a statistical surrogate. **Requirement**: Dependency: T030.
- [X] T056 [P5] **Review Response**: Add a "Scientific Integrity" validation step in `code/utils/terminology_scanner.py`. **Requirement**: Extend the scanner to specifically check for the phrase "First-Principles" in the context of the *model* (not the *data source*). **Requirement**: If the model is described as "First-Principles", raise a warning or error. **Requirement**: Dependency: T037.

**Checkpoint**: All scientific integrity concerns from the research review are addressed.

---

## Phase 8: Revision & Verification (Addressing Reviewer Concerns)

**Goal**: Explicitly verify that the project title, documentation, and codebase no longer claim "First-Principles" status for the ML model, directly addressing the Feynman review, and formally amend the Constitution.

### Implementation for Phase 8

- [X] T057 [P5] **Review Response**: Final Title Audit: Create `code/utils/final_title_audit.py` to scan `spec.md`, `README.md`, `docs/methodology.md`, `plan.md`, and **`constitution.md`** for the exact phrase "First-Principles" in the project title or summary. **Requirement**: If found, exit with code 1 and message "FATAL: Project title or summary still claims 'First-Principles'. Review T054/T055/T056/T060". **Requirement**: If not found, **write `data/results/title_audit.json`** with status "PASS" and a list of files scanned. **Requirement**: This task must run as the final gate before project completion. **Requirement**: **Dependency**: T054, T055, T056, **T060c**.
- [X] T058 [P5] **Review Response**: Methodology Consistency Check: Create `code/utils/methodology_consistency_check.py` to verify that every mention of "GNN", "Surrogate", or "Model" in `docs/methodology.md` is accompanied by the disclaimer "interpolates DFT data" or "not a first-principles calculation". **Requirement**: If a mention lacks the disclaimer, log it as a warning but do not exit. **Requirement**: **Write `data/results/methodology_consistency.json`** containing the list of warnings. **Requirement**: Dependency: T030, T055.
- [X] T059 [P5] **Review Response**: Feynman Quote Verification: Create `code/utils/feynman_quote_verifier.py` to scan all generated reports for the presence of the Feynman quote: "The first principle is that you must not fool yourself — and you are the easiest person to fool." **Requirement**: **Explicitly scan**: `data/results/feature_importance_report.md`, `data/results/training_logs.json`, `data/results/generalization_metrics.json`. **Requirement**: If missing in any report, exit with code 1. **Requirement**: Dependency: T046a, T055.

**Checkpoint**: Final verification that the project fully aligns with the "Surrogate Model" definition and addresses the Feynman review.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Scientific Integrity (Phase 7)**: Can run in parallel with Phase 6, depends on T037
- **Revision & Verification (Phase 8)**: Depends on completion of Phases 1-7, specifically T054, T055, T056, **T060c**

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
- **New Revision Tasks**: Task T021b (Inter-Family Validation Gate) added to enforce SC-002. Task T027d (Success Criteria Aggregator) added to enforce SC-005. Task T036a (Readiness Check) added to validate inference feasibility. Task T018c (Memory Enforcement) added to enforce SC-004. Task T018d (End-to-End Memory Validation) added to verify combined peak memory. Task T027c1-c3 (Report Atomization) added to improve executability.
- **New Review Response Tasks**: Tasks T054, T055, T056 added to directly address the "Richard Feynman (simulated)" review regarding the distinction between interpolation and first-principles physics.
- **New Revision Tasks (Phase 8)**: Tasks T057, T058, T059 added to perform final verification that the project title, methodology, and reports fully comply with the "Surrogate Model" definition and include the required Feynman quote, directly addressing the reviewer's concern about "fooling yourself". **New Task T060 added** to formally amend the Constitution title, resolving the 'Single Source of Truth' contradiction.
- **Dependency Corrections**: T021a now depends on T018b/T017b (not T021b). T021b now depends on T021a. T013f depends on T013d (not T013e). T036b depends on T018b/T017b (not T036a). T018b now depends on T018c. T027d (US2) now depends on T021a/T036b/T021b (corrected circular dependency). T027d (US3) renamed to T027e and depends on T023/T024. T013d0c renamed to T013d0_final; T008a dependency corrected to T013d0_impl, T013d1-d4.
- **Logic Corrections**: T013d0_impl dependencies corrected to only T013d0_define (definitions), removing T013d1-d4 from execution dependencies to prevent circular logic. T057 now audits `constitution.md` and depends on T060.
- **ID Collision Resolution**: T027d (Phase 5) renamed to T027e to resolve duplicate ID conflict.
- **Dependency Fixes**: T008a dependency corrected from non-existent T013d0 to T013d0_impl, T013d1-d4.
- **Constitution Amendment**: T054 updated to verify titles; T060 handles the formal amendment of the Constitution via a new artifact and **explicit file edit** with **PR and Sync Report steps**.
- **Atomic Writes**: T013f updated to mandate atomic writing of split indices using `tempfile.mkstemp` in the same directory and `os.rename`.
- **Task T046 Moved**: Moved from Phase 2 to Phase 4/5 to align with file creation. Added T046a to Phase 2 for template creation.
- **Task T027a Updated**: Updated to depend on T023, T024, T021a.
- **Task T027c2 Split**: Split into T027c1 (Data Aggregation) and T027c2 (Report Assembly) for better executability.
- **Task T013d0_impl Clarified**: Clarified dependencies on T013d1-d4 as module definitions, not execution steps.
- **Lock File Lifecycle**: T009a updated to include cleanup/expiration logic; T013d1 updated to acquire/release lock via T009b.
- **Iteration Count Fixed**: T023/T024 updated to use fixed 1000 iterations, removing "tune" instruction.
- **End-to-End Memory Test**: T018d added to verify combined peak memory.
- **Final Verification**: T057/T058 marked complete and executable.
- **Lock Manager**: T009b added as foundational utility with no dependencies to resolve circular dependency.
- **Parallel Clarification**: T023/T024 [P] tag removed to avoid confusion about dependency on T018b.
- **Constitutional Title Amendment**: T060 split into T060a (Draft), T060b (Edit), T060c (Verify) and moved to Phase 1 to ensure the 'Single Source of Truth' is fixed before any downstream tasks run.
- **Task T013d0_impl Restored**: Restored T013d0_impl to Phase 3 to ensure dependency chain for T008a and T018d is intact.
- **Task T018c Dependencies Fixed**: Updated T018c to depend on T004 and T016.
- **Task T027a Dependencies Fixed**: Updated T027a to depend on T023, T024, T021a.
- **Task T013f Conversion Logic Fixed**: Updated T013f to explicitly state conversion to `pymatgen.Structure`.
- **Task T023/T024 Specifications Fixed**: Updated T023/T024 to specify [deferred] background sample and 1000 iterations.
- **Task T009a Schema Fixed**: Updated T009a to explicitly define JSON schema check.
- **Task T046 Dependencies Fixed**: Updated T046 to depend on T046a.
- **Task T060 Workflow Fixed**: Split T060 into T060a/b/c to separate Draft/Edit/Verify, ensuring the workflow matches FR-030.
- **Review Response Completion**: All tasks related to the "Richard Feynman (simulated)" review (T054-T059, T060) are now marked as completed [X] to reflect that the terminology and title corrections have been fully implemented and verified.
- **New Tasks Added**: T001c (Artifact Hashing), T011a (Continuum Validation), T020b (Stratified CV), T030a (Citation Validation).
- **Task T021b Logic Fixed**: T021b now flags instead of exits; T027d now depends on T021b.
- **Task T013d0_impl Split**: Split into T013d0_define and T013d0_impl to clarify logic vs. implementation.
- **Task T013f Reconstruction Fixed**: T013f now explicitly describes deserialization of `structure_pickle` and `cif_raw`.
- **Task T060b Regex Fixed**: T060b now specifies the exact regex pattern.
- **Task T027c1/2 Precision Fixed**: T027c1 outputs 4 decimal places; T027c2 sorts by unrounded values.
- **Task T059 Paths Fixed**: T059 now explicitly lists report paths to scan.
- **Task T009a/b Order Fixed**: Visual order corrected to match dependency.
- **Task T021c Removed**: Redundant aggregation task removed.
- **Task T013d0_final Removed**: T013d0_final removed to eliminate redundancy and logical conflict; T013d0_impl now serves as the finalization step.
- **Notes Corrected**: Removed contradictory notes regarding T021c and T013d0_final dependencies.
- **Memory Enforcement Architecture**: T018c split into T018c-def (Static Interface) and T018c-impl (Dynamic Profiling) to resolve the architectural coupling risk between T016 (Model Class) and T018b (Training Loop). T018c-def defines the contract for the model class, while T018c-impl performs the actual `tracemalloc` profiling on the instantiated model.