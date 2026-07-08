# Tasks: Predicting Molecular Diffusion Coefficients in Liquids with Graph Neural Networks

**Input**: Design documents from `/specs/001-predict-molecular-diffusion/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/`, `data/` at repository root
- Paths shown below assume single project - adjust based on plan.md structure

---

## Phase 0: Data Acquisition & Validation (Blocked until dataset source is confirmed)

- [X] T000a Create `data/raw` directory for source CSVs (Phase 0)
- [X] T000b Implement `code/ingestion/fetch_real.py` to download a verified diffusion dataset (e.g., from NIST or Zenodo) and save as `data/raw/dataset.csv`. **Upon success, immediately update `plan.md` to record the actual dataset URL.** (Phase 0)
- [X] T000c Add verification step to ensure `plan.md` records the dataset URL; if download fails, invoke synthetic generator (T007b) (Phase 0)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per `plan.md` (directories: `code/`, `data/raw`, `data/processed`, `data/checksums.json`, `data/logs`, `data/artifacts`)
- [X] T002 Initialize Python 3.11 project and generate `code/requirements.txt` with pinned versions (`rdkit`, `torch` (CPU), `torch-geometric` (CPU), `scikit-learn`, `pandas`, `pyyaml`, `psutil`, `pytest`, `thermo`)
- [X] T003 [P] Configure `pyproject.toml` for linting (ruff) and formatting (black)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [~] T004 Implement `code/utils/config.py` to manage paths, random seed (fixed), and environment variables
- [~] T005 [P] Implement `code/utils/logging.py` with specific log tags: `[MISSING_DATA_EXCLUDED]`, `[ERROR_SMILES]`; write to `data/logs/ingestion.log` in plain text with timestamp (FR-007)
- [~] T005a [P] Add pytest test `tests/unit/test_logging_tags.py` asserting that the tags `[MISSING_DATA_EXCLUDED]` and `[ERROR_SMILES]` appear in `data/logs/ingestion.log` after processing a mixed‑validity CSV (executability)
- [~] T006 Implement `code/utils/monitor.py` to enforce a fixed runtime limit of **6 hours (21600 s)** and a RAM limit of **7 GB**; raise `ResourceLimitExceeded` if exceeded (FR-003, SC-003, SC-005)
- [~] T006c [P] Extend `monitor.py` to record total pipeline runtime to `artifacts/reports/runtime_memory.json` under key `"total_seconds"` (SC-003)
- [~] T006d [P] Add pytest test `tests/unit/test_monitor_runtime.py` that runs a dummy function exceeding the time limit and asserts `ResourceLimitExceeded` is raised (executability)
- [~] T006e [P] Extend `monitor.py` to capture peak memory usage and store under `"peak_memory_mb"` in the same JSON report (SC-005)
- [~] T006f [P] Add pytest test `tests/unit/test_monitor_memory.py` that simulates memory over‑use and verifies the limit exception (executability)
- [~] T006b [P] Implement `code/utils/graph_safety.py` to detect high molecular weight molecules and implement **sampling or truncation logic during featurization** (before memory allocation) to prevent memory crashes (Spec Edge Case, SC-005)
- [~] T007 [P] Implement `code/ingestion/fetch_nist.py` to programmatically retrieve experimental diffusion data from NIST TRC via `thermo`; on failure, invoke T007b (Phase 0)
- [~] T007b [P] {{claim:c_916bfffc}} (Wikidata Q3274587, https://www.wikidata.org/wiki/Q3274587) or random structures **strictly for pipeline validation** (Phase 0)
- [~] T007c [P] Implement `code/ingestion/flag_source.py` to generate a `data_source_flag.json` artifact in `data/` recording `{"source": "real" | "synthetic"}` based on which download/generation task succeeded. This artifact serves as the synchronization point for downstream tasks. (Phase 0)
- [~] T008 [P] Implement `code/ingestion/validate.py` to define SMILES validation logic and exclusion logic for missing solvent variables (FR-001, FR-007)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Featurization Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest experimental diffusion data, validate SMILES, and convert to graph representations + solvent descriptors.

**Independent Test**: Run on a sample of molecules (real or synthetic) and verify output JSONL contains valid PyTorch Geometric Data objects and solvent descriptors, with no missing critical fields.

### Implementation for User Story 1

- [~] T008b [US1] Implement `code/ingestion/run_validation.py` to execute the validation logic from T008 on fetched/generated data. **Depends on T007c** to ensure data source is resolved. (Depends on T007c, T008)
- [~] T010 [P] [US1] Implement `code/ingestion/featurize.py`: Convert SMILES to `MoleculeGraph` (RDKit) with atom nodes and bond edges **AND** compute `SolventDescriptor` (viscosity, dielectric constant) from CSV input (US1, FR-002)
- [~] T012 [US1] Implement `code/ingestion/ingest.py`: Main pipeline to read CSV, validate (T008b), featurize, and write `data/processed/featurized.jsonl` (Depends on T008b, T010)
- [~] T013 [US1] Implement error handling in `ingest.py` to exclude records with missing data and log with `[MISSING_DATA_EXCLUDED]`
- [~] T014 [US1] Implement error handling in `ingest.py` to skip invalid SMILES and log with `[ERROR_SMILES]` without crashing
- [~] T015 [US1] Add contract test in `tests/contract/test_featurization.py` to validate JSONL schema against `specs/001-predicting-molecular-diffusion-coefficie/contracts/dataset.schema.yaml`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - CPU‑Optimized GNN Training and Baseline Comparison (Priority: P2)

**Goal**: Train a lightweight MPNN on CPU, compare against a Linear Regression baseline (with descriptors), and perform statistical significance testing.

**Independent Test**: Execute training on ≤ 5 000 molecules; verify completion in ≤ 30 min on CPU; verify model artifacts saved; verify report contains RMSE, Pearson r for both GNN and baseline, and respects synthetic‑data policy.

### Implementation for User Story 2

- [~] T016 [P] [US2] [FR-003] Implement `code/models/mpnn.py`: Define a single‑layer Message Passing Neural Network (CPU‑only, no CUDA)
- [~] T016a [P] Add unit test `tests/unit/test_mpnn_device.py` asserting `torch.cuda.is_available() is False` and that startup logs "Device: CPU"
- [~] T017 [P] [US2] Implement `code/models/baseline.py`: Define **Linear Regression** baseline using fingerprints + solvent descriptors (Mandatory for FR‑005 t‑test)
- [~] T019a [P] [US2] Implement `code/training/cv_strategy.py` (Part 1): Detect dataset size and strata sparsity; **IF dataset < 50 molecules or solvent types are sparse, default to Leave‑One‑Out (LOO) validation**; **ELSE use k‑fold stratified by solvent type** (FR‑004, Spec Edge Cases, SC‑003)
- [~] T019b [P] [US2] Implement `code/training/cv_strategy.py` (Part 2): Add logic to read a `force_5fold` configuration flag. If set, **override default LOO logic and enforce 5-fold**. If dataset < 50 and `force_5fold` is true, raise a clear `ConfigurationError` explaining that 5-fold is impossible on small datasets, satisfying FR-004's strict mandate while providing an override mechanism. (Depends on T019a)
- [ ] T019a_test [P] Add test `tests/unit/test_cv_strategy.py` that feeds a 40‑sample synthetic dataset and asserts the LOO splitter is selected
- [~] T019 [US2] Implement `code/training/train.py` (Part 1): k‑fold/LOO stratified splitter with fixed seed (FR‑004, depends on T019a, T019b)
- [~] T041 [US2] Implement `code/training/train.py` (Part 2): Cross‑validation loop training MPNN (T016) and Linear Regression (T017), saving checkpoints to `data/artifacts/`; includes device check log (depends on T019, T016, T017, T019a, T019b)
- [~] T020 [US2] Implement `code/training/evaluate.py`: Calculate Pearson r and RMSE for GNN and Linear Regression on held‑out test set (Depends on T041)
- [~] T021 [US2] Extend evaluation to (a) perform paired t‑test on absolute errors (FR‑005); (b) **Check `data_source_flag.json` (T007c)**: **IF source is synthetic, skip metric calculation and DO NOT create the evaluation JSON file**; (c) **IF source is real**, calculate metrics and generate `artifacts/reports/evaluation.json` containing `pearson_r`, `rmse`, `p_value`, and a **`hypothesis_status`** field with values: `'positive'` (if r > 0.7), `'null'` (if r < 0.3), or `'inconclusive'` (if 0.3 <= r <= 0.7), fully satisfying SC-001 (Depends on T020, T007c)
- [~] T021a [P] Add contract test `tests/contract/test_evaluation_report.py` verifying the JSON schema includes the `hypothesis_status` field and that the file exists when real data is present
- [~] T021b [P] Add unit test `tests/unit/test_evaluation_synthetic_skip.py` confirming that when the `data_source_flag.json` indicates 'synthetic' (or CLI arg `--data-source=synthetic` is set), the evaluation JSON is **not created** (executability)
- [~] T023 [US2] Add integration test in `tests/integration/test_training_pipeline.py` to verify end‑to‑end training and evaluation flow (including conditional metric suppression)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis and Methodological Robustness Check (Priority: P3)

**Goal**: Perform sensitivity analysis on hyperparameters and verify model robustness via ablation studies.

**Independent Test**: Run sensitivity script; verify output report shows metric fluctuations across hyperparameter ranges and confirms stability (or lack thereof).

### Implementation for User Story 3

- [~] T024 [P] [US3] Implement `code/training/sensitivity.py` (Part 1): Define hyperparameter grid (Message Passing Steps **{1, 2, 3}**, Learning Rates: small values will be employed to promote stable convergence during training.)
- [~] T042 [P] [US3] Implement `code/training/sensitivity.py` (Part 2): Sweep loop to retrain/evaluate models across the grid (Depends on T024, T041)
- [~] T043 [US3] Implement `code/training/sensitivity.py` (Part 3): Generate sweep report `artifacts/reports/sensitivity_report.json` with table of metrics (Depends on T042)
- [~] T025a [P] [US3] Implement `code/training/ablation_pipeline.py`: Add `remove_solvent` flag to the training input pipeline for both MPNN and Linear Regression (FR‑006, SC‑004)
- [ ] T025a_test [P] Add unit test `tests/unit/test_ablation_flag.py` that runs the pipeline with `remove_solvent=True` and asserts solvent descriptors are absent from the model input
- [~] T025b [US3] Implement `code/training/ablation_study.py`: Orchestrate re‑training using the pipeline from T025a with `remove_solvent=True` for BOTH GNN and Baseline. **Explicitly calculate `variation_delta` as (full_model_r - ablated_model_r) for both models.** Generate `artifacts/reports/ablation_report.json` containing `gnn_variation_delta`, `baseline_variation_delta`, and the raw correlation values. (Depends on T041, T019a, T019b, T025a)
- [ ] T025b_test [P] Add contract test `tests/contract/test_ablation_report.py` verifying the JSON contains fields `gnn_variation_delta`, `baseline_variation_delta` and that values are numeric
- [~] T026 [US3] Implement `code/training/robustness.py`: Detect dataset size (using T019a logic) and switch CV strategy if < 50 molecules; calculate Pearson r on full dataset and on dataset excluding the top portion of residuals; write `artifacts/reports/outlier_analysis.json` (Depends on T019a, T041)
- [~] T027 [US3] Generate final report `artifacts/reports/sensitivity_summary.md` summarizing stability of Pearson r > 0.7 across variations **and explicitly include a `stability` field (`stable`/`unstable`) based on whether all r values meet the threshold**. **Must depend on T043 AND T025b** to ensure both sweep and ablation results are available. (Depends on T043, T025b)
- [~] T027b [P] Add verification test `tests/contract/test_sensitivity_stability.py` that checks the summary report contains a stability statement and that all r values are recorded
- [~] T028 [US3] Add unit test `tests/unit/test_outlier_analysis.py` confirming the JSON includes both full‑set and trimmed‑set r values
- [~] T028a [P] Add test `tests/unit/test_sensitivity_logic.py` verifying the hyperparameter sweep logic correctly iterates over the defined grid

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T029 [P] Documentation updates: Write `code/README.md` with execution instructions and data source requirements
- [~] T030 Code cleanup and refactoring of `code/` imports and dependencies
- [~] T031 [P] Add pytest unit tests for `utils/monitor.py` to verify memory/time gating logic; explicitly implement `test_time_limit`, `test_memory_limit`, and `test_resource_limit_message` (executability)
- [~] T032a [P] Provide deterministic script `run_quickstart.py` that runs the full pipeline on synthetic data and asserts successful completion (executability)
- [~] T033a [P] Add verification step that diffs `plan.md` to ensure a dataset source URL line is present; fail the task if missing (executability)
- [~] T034 Update `plan.md` with the actual dataset source found (NIST/Zenodo) or confirm "Simulation Study" status (requires manual edit but task ensures it is recorded)
- [~] T035 [P] Aggregate runtime and memory usage into a unified `artifacts/reports/resource_summary.json` after the full pipeline completes, copying `total_seconds` and `peak_memory_mb` from `runtime_memory.json` (addresses SC‑005)
- [~] T036 [P] Add pytest contract test `tests/contract/test_resource_report.py` verifying that `resource_summary.json` contains both `total_seconds` and `peak_memory_mb` fields with numeric values
- [~] T037 [P] Add pytest unit test `tests/unit/test_pearson_threshold.py` that loads `artifacts/reports/evaluation.json` and asserts the `hypothesis_status` field correctly reflects whether `pearson_r > 0.7` (positive), `< 0.3` (null), or between (inconclusive) (addresses SC‑001)
- [~] T039 [P] Add pytest contract test `tests/contract/test_sensitivity_stability_report.py` that checks `artifacts/reports/sensitivity_summary.md` includes a clear stability statement and that all reported `r` values are present (addresses SC‑004)