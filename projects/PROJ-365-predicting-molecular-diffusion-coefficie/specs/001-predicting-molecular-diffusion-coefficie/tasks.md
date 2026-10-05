---
description: "Task list template for feature implementation"
---

# Tasks: Predicting Molecular Diffusion Coefficients in Liquids with Graph Neural Networks

**Input**: Design documents from `/specs/001-predict-molecular-diffusion/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only if explicitly requested in the feature specification.

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

- [ ] T000a Create `data/raw` directory for source CSVs (Phase 0)
- [X] T048 [P] Implement `code/ingestion/trigger_synthetic.py`: If `plan.md` does not contain a `Dataset URL:` line, execute `code/ingestion/generate_synthetic.py` and set the `data_source_flag.json` to `"synthetic"`. (Phase 0)
- [ ] T007b [P] Implement `code/ingestion/generate_synthetic.py` that creates a deterministic synthetic `data/raw/dataset.csv` with columns `smiles`, `solvent`, `diffusion_coefficient`, `viscosity`, `dielectric_constant`. Uses a fixed seed and writes a predetermined number of rows. (Phase 0)
- [ ] T007b_test [P] Contract test validating that the generated CSV matches the expected schema and contains the expected number of rows. (executability)
- [ ] T000b [P] Check `plan.md` for a line starting with `Dataset URL:`. If present, attempt to download the verified diffusion dataset from that URL and save as `data/raw/dataset.csv`. If the URL is missing or download fails, trigger T048 (synthetic generation). Upon success, immediately update `plan.md` to record the actual dataset URL. (Phase 0)
- [ ] T007 [P] Implement fallback mechanism: if `fetch_real.py` fails and no URL is in `plan.md`, invoke `code/ingestion/fallback.py` which calls `trigger_synthetic.py`. (Phase 0)
- [ ] T007_fallback_test [P] Pytest test confirming that `fallback.py` triggers synthetic generation when real download fails. (executability)
- [ ] T007c [P] Implement `code/ingestion/flag_source.py` to generate `data_source_flag.json` recording `{"source": "real"}` or `{"source": "synthetic"}` based on which ingestion path succeeded. (Phase 0)
- [ ] T007c_test [P] Unit test checking `data_source_flag.json` after each path. (executability)
- [ ] T000c [P] Add verification step to ensure `plan.md` records the dataset URL if `fetch_real.py` succeeded; otherwise verify that `data_source_flag.json` indicates `"synthetic"`. (Phase 0)
- [ ] T000d [P] Verify that `plan.md` contains a line starting with `Dataset URL:` after a successful download; if no URL exists, verify that `data_source_flag.json` indicates `"synthetic"` and proceed. **Depends on T000b or T048**. (Phase 0)
- [ ] T000d_test [P] Pytest test that reads `plan.md` and asserts a `Dataset URL:` line exists **or** that `data_source_flag.json` is `"synthetic"`. (Phase 0)
- [ ] T048_test [P] Pytest test for `trigger_synthetic.py` confirming it falls back to synthetic generation when real download fails. (Phase 0)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per `plan.md` (directories: `code/`, `data/raw`, `data/processed`, `data/checksums.json`, `data/logs`, `data/artifacts`)
- [X] T002 Initialize Python 3.11 project and generate `code/requirements.txt` with pinned versions (`rdkit`, `torch` (CPU), `torch-geometric` (CPU), `scikit-learn`, `pandas`, `pyyaml`, `psutil`, `pytest`, `thermo`)
- [X] T003 [P] Configure `pyproject.toml` for linting (ruff) and formatting (black)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [X] T004 Implement `code/utils/config.py` to manage paths, random seed (fixed), and environment variables. Include dynamic runtime limit detection: read `RUNTIME_LIMIT_SEC` from environment variable (default 21600 seconds/6 hours per plan.md) or detect CI runner capacity; default to 21600 if undetectable. (SC-003)
- [X] T005 [P] Implement `code/utils/logging.py` with specific log tags: `[MISSING_DATA_EXCLUDED]`, `[ERROR_SMILES]` (for Edge Case handling of invalid SMILES); write to `data/logs/ingestion.log` in plain text with timestamp (FR-007)
- [X] T005a [P] Add pytest test `tests/unit/test_logging_tags.py` asserting that the tags `[MISSING_DATA_EXCLUDED]` and `[ERROR_SMILES]` appear in `data/logs/ingestion.log` after processing a mixed‑validity CSV.
- [X] T006 Implement `code/utils/monitor.py` to enforce a runtime limit (dynamic, default 21600s) and a RAM limit of **4096 MB** (configurable via `config.py`); raise `ResourceLimitExceeded` if exceeded (FR-003, SC-003, SC-005)
- [X] T006c [P] Extend `monitor.py` to record total pipeline runtime to `artifacts/reports/runtime_memory.json` under key `"total_seconds"` (SC-003)
- [X] T006e Implement peak‑memory capture in `monitor.py` and store under `"peak_memory_mb"` in `runtime_memory.json`. **Depends on T006** (SC-005)
- [X] T006e_test [P] Pytest test `tests/unit/test_monitor_memory_capture.py` that runs a dummy memory‑intensive function and asserts `"peak_memory_mb"` appears in `runtime_memory.json`.
- [X] T006f [P] Add pytest test `tests/unit/test_monitor_memory.py` that simulates memory over‑use and verifies the limit exception.
- [X] T006b [P] Implement `code/utils/graph_safety.py` to detect high molecular weight molecules and implement **sampling or truncation logic during featurization** (before memory allocation) to prevent memory crashes (Spec Edge Case, SC-005)
- [X] T006b_test [P] Unit test feeding a deliberately large molecule and asserting safe handling.
- [X] T008 [P] Implement `code/ingestion/validate.py` defining SMILES validation logic and exclusion logic for missing solvent variables (FR-001, FR-007)
- [X] T008_test [P] Unit test feeding a CSV with invalid SMILES and missing solvent fields; asserts appropriate log tags are emitted.
- [X] T008b [US1] Implement `code/ingestion/run_validation.py` to execute the validation logic from T008 on fetched/generated data. **Depends on T007c** to ensure data source is resolved. (Depends on T007c, T008)
- [X] T008b_test [P] End‑to‑end pytest that runs the validation pipeline and verifies only valid records are written to `data/processed`.
- [X] T015_schema_create Create `specs/001-predict-molecular-diffusion-coefficie/contracts/dataset.schema.yaml` defining the JSONL record structure. **Required fields**: `smiles`, `graph_nodes` (list), `graph_edges` (list), `viscosity`, `dielectric_constant`, `diffusion_coefficient`. This task now runs **before** any featurization or ingestion tasks. (Foundational)
- [X] T015_test [P] Contract test `tests/contract/test_featurization.py` validating `data/processed/featurized.jsonl` against the schema created by T015_schema_create.
- [X] T010 [P] [US1] Implement `code/ingestion/featurize.py`: Convert SMILES to `MoleculeGraph` (RDKit) with atom nodes and bond edges **AND** compute `SolventDescriptor` (viscosity, dielectric constant) from CSV input. **Must call T006b (graph safety) logic to sample/truncate large molecules before graph construction.** (US1, FR-002)
- [X] T010_test [P] Unit test verifying a single SMILES conversion yields a correct `MoleculeGraph` object and proper solvent descriptor extraction.
- [X] T012 [US1] Implement `code/ingestion/ingest.py`: Main pipeline to read CSV, run validation (T008b), featurize (T010), and write `data/processed/featurized.jsonl`. Handles missing data and invalid SMILES via logging. **Depends on T006b, T008b, T010, T015_schema_create**.
- [X] T013 [US1] Add error handling in `ingest.py` to exclude records with missing solvent data and log `[MISSING_DATA_EXCLUDED]`.
- [X] T014 [US1] Add error handling in `ingest.py` to skip invalid SMILES and log `[ERROR_SMILES]` without crashing.
- [X] T013_test [P] Unit test that processes a CSV with missing solvent descriptors and asserts `[MISSING_DATA_EXCLUDED]` appears in the log.
- [X] T014_test [P] Unit test that processes a CSV with an invalid SMILES string and asserts `[ERROR_SMILES]` appears and the record is omitted.

## Phase 3: User Story 2 - CPU‑Optimized GNN Training and Baseline Comparison (Priority: P2)

**Goal**: Train a lightweight MPNN on CPU, compare against a Linear Regression baseline, and perform statistical significance testing.

- [X] T016 [P] [US2] [FR-003] Implement `code/models/mpnn.py`: Define a single‑layer Message Passing Neural Network (CPU‑only, no CUDA)
- [X] T016a [P] Add unit test `tests/unit/test_mpnn_device.py` asserting `torch.cuda.is_available() is False` and that startup logs "Device: CPU"
- [X] T016b [P] [FR-003] Implement runtime logging in `code/models/mpnn.py` or `code/main.py` to explicitly log "Device: CPU" and verify `torch.cuda.is_available() is False` at startup, raising an error if GPU is detected. (Addresses FR-003 production requirement)
- [X] T017 [P] Implement `code/models/baseline.py`: Define **Linear Regression** baseline using fingerprints + solvent descriptors (Mandatory for FR‑005 t‑test)
- [X] T041 [US2] Implement `code/training/train.py`: (Part 1) k‑fold splitter with fixed seed (depends on T019a); (Part 2) Cross‑validation loop training MPNN (T016) and Linear Regression (T017), saving checkpoints to `artifacts/models/`; includes device check log. **Depends on T019a, T016, T017**.
- [X] T019a [P] Implement `code/training/cv_strategy.py`: Enforce **strict 5‑fold cross‑validation stratified by solvent type** as required by FR‑004. **If dataset >= 50 molecules**, use this strategy. **If dataset < 50 molecules**, raise `ConfigurationError` directing to T019b. (FR‑004, Spec Edge Cases, SC‑003)
- [X] T019b [P] [US2] [Edge Case] Implement `code/training/loo_strategy.py`: Implement Leave-One-Out (LOO) cross-validation strategy for datasets with < 50 molecules. This task is triggered when T019a detects insufficient data for 5-fold CV. (Spec Edge Cases)
- [X] T019a_test [P] Test `tests/unit/test_cv_strategy.py` feeding a synthetic dataset of 40 samples and asserting a `ConfigurationError` is raised (or routed to T019b).
- [X] T019a_strat_test [P] Test `tests/unit/test_cv_strategy_strat.py` confirming that the CV splitter respects solvent‑type stratification (i.e., each fold maintains the solvent type distribution). (coverage‑b224af49)
- [X] T020 [US2] Implement `code/training/evaluate.py`: Calculate Pearson r and RMSE for GNN and Linear Regression on held‑out test set (Depends on T041)
- [X] T021 [US2] Extend `code/training/evaluate.py`:
 - If `data_source_flag.json` (T007c) indicates `"synthetic"`, skip metric calculation and do **not** create `artifacts/reports/evaluation.json`.
 - If `"real"`, compute Pearson r, RMSE, perform paired t‑test on absolute errors, and write `artifacts/reports/evaluation.json` containing `pearson_r`, `rmse`, `p_value`, and a `hypothesis_status` field (`positive` if r > 0.7, `null` if r < 0.3, `inconclusive` otherwise). (SC-001)
- [X] T021a [P] Add contract test `tests/contract/test_evaluation_report.py` verifying the JSON schema includes the `hypothesis_status` field and that the file exists when real data is present.
- [X] T021b [P] Add unit test `tests/unit/test_evaluation_synthetic_skip.py` confirming that when the `data_source_flag.json` indicates 'synthetic', the evaluation JSON is **not created**.
- [X] T023 [US2] Add integration test `tests/integration/test_training_pipeline.py` to verify end‑to‑end training and evaluation flow (including conditional metric suppression).
- [X] T044 [P] Refactor `code/ingestion/fetch_real.py` to raise `FileNotFoundError` or `ConnectionError` if the real dataset URL is unreachable **and** a `Dataset URL:` is present in `plan.md`; otherwise return `"no_url"` status. (Addresses loader must fail loudly)
- [X] T044_test [P] Unit test `tests/unit/test_fetch_real_fail.py` mocking a network failure and asserting correct exception behavior when URL is present and `"no_url"` return when absent.
- [X] T046 [P] Modify `code/training/evaluate.py` to **strictly enforce the "No Metrics on Synthetic" rule** by exiting with non‑zero status and message "Scientific metrics suppressed for synthetic data" when `data_source_flag.json` is `"synthetic"`. (Addresses synthetic metric suppression)
- [X] T046_test [P] Integration test `tests/integration/test_no_metrics_synthetic.py` that runs the full pipeline on synthetic data and asserts that `artifacts/reports/evaluation.json` is NOT created and the process exits with the expected suppression message.

## Phase 4: User Story 3 - Sensitivity Analysis and Methodological Robustness Check (Priority: P3)

**Goal**: Perform sensitivity analysis on hyperparameters and verify model robustness via ablation studies.

- [X] T024 [P] [US3] Implement `code/training/sensitivity.py` (Part 1): Define hyperparameter grid (Message Passing Steps **{1, 2, 3}**, Learning Rates: **[0.001, 0.01, 0.1]**).
- [X] T042 [P] [US3] Implement `code/training/sensitivity.py` (Part 2): Sweep loop to retrain/evaluate models across the grid (Depends on T024, T041)
- [X] T043 [P] Generate `artifacts/reports/sensitivity_report.json` with a table of metrics per hyperparameter setting.
- [X] T043_test [P] Contract test `tests/contract/test_sensitivity_report.py` verifying the JSON contains the expected metric table and fields.
- [X] T025a [P] Implement `code/training/ablation_pipeline.py`: Add `remove_solvent` flag to the training input pipeline for both MPNN and Linear Regression (FR‑006, SC‑004)
- [X] T025a_test [P] Unit test `tests/unit/test_ablation_flag.py` that runs the pipeline with `remove_solvent=True` and asserts solvent descriptors are absent from the model input.
- [X] T025c [P] [US3] Implement `code/training/ablation_gate.py`: Check `data_source_flag.json`. If `"synthetic"`, skip the ablation study and log "Ablation study skipped: synthetic data". If `"real"`, allow T025b to proceed. (Addresses FR-006 synthetic conflict)
- [X] T025b [US3] Implement `code/training/ablation_study.py`: Orchestrate re‑training using the pipeline from T025a with `remove_solvent=True` for BOTH GNN and Baseline. Calculate `variation_delta` as (full_model_r - ablated_model_r) for both models. Generate `artifacts/reports/ablation_report.json` containing `gnn_variation_delta`, `baseline_variation_delta`, and raw correlation values. **Depends on T025c**. (Depends on T041, T019a, T025a, T025c)
- [X] T025b_test [P] Contract test `tests/contract/test_ablation_report.py` verifying the JSON contains fields `gnn_variation_delta`, `baseline_variation_delta` and that values are numeric.
- [X] T026 [US3] Implement `code/training/robustness.py`: Detect dataset size (using T019a logic). **If dataset < 50 molecules, use T019b (LOO) for this analysis**. Calculate Pearson r on the full dataset and on the dataset after excluding the most extreme residuals.; write `artifacts/reports/outlier_analysis.json` (Depends on T019a, T019b, T041)
- [X] T028 [US3] Add unit test `tests/unit/test_outlier_analysis.py` confirming the JSON includes both a `full_set_r` and a `trimmed_set_r`.
- [X] T027 [US3] Generate final report `artifacts/reports/sensitivity_summary.md` summarizing stability of Pearson r > 0.7 across variations **and explicitly include a `stability` field (`stable`/`unstable`) based on whether all r values meet the threshold**. **Depends on T043 AND T025b** to ensure both sweep and ablation results are available.
- [X] T027_test [P] Contract test `tests/contract/test_sensitivity_stability.py` that checks the summary report contains a stability statement and that all reported `r` values are recorded.

## Phase 5: Polish & Cross‑Cutting Concerns (Mapping to FR/SC)

**Purpose**: Improvements that affect multiple user stories

- [X] T029 [P] Documentation updates: Write `code/README.md` with execution instructions and data source requirements. *(maps to FR‑001, FR‑002 – ensures reproducibility)*
- [X] T030 [P] Code cleanup and import refactoring; ensure zero `ruff` warnings. *(maps to SC‑003 – linting improves CI reliability)*
- [X] T030_test [P] Pytest that runs `ruff` on the codebase and asserts no warnings
- [X] T031 already completed (monitor.py tests)
- [X] T032a [P] Provide deterministic script `run_quickstart.py` that runs the full pipeline on synthetic data and asserts successful completion. *(maps to SC‑003)*
- [X] T032a_test [P] Unit test verifying `run_quickstart.py` exits with code 0 and creates expected artifacts (excluding evaluation JSON when synthetic)
- [X] T035_test_fixed [P] Contract test `tests/contract/test_resource_summary.py` verifying that `resource_summary.json` contains both `total_seconds` and `peak_memory_mb` fields with numeric values. *(addresses SC‑003 & SC‑005)*
- [X] T035_resolve_test [P] Additional test ensuring numeric fields are within reasonable bounds (e.g., `total_seconds` < 21600, `peak_memory_mb` < 7000). *(resolves previous UNRESOLVED‑CLAIM)*
- [X] T036 [P] Add pytest contract test `tests/contract/test_pearson_threshold.py` that loads `artifacts/reports/evaluation.json` and asserts the `hypothesis_status` field correctly reflects whether `pearson_r > 0.7` (positive), `< 0.3` (null), or between (inconclusive) (addresses SC‑001)
- [X] T039 [P] Add pytest contract test `tests/contract/test_sensitivity_stability_report.py` that checks `artifacts/reports/sensitivity_summary.md` includes a clear stability statement and that all reported `r` values are present (addresses SC‑004)
- [X] T040 [P] Add CI workflow `.github/workflows/ci.yml` that runs the full pipeline on synthetic data, enforces linting, runs all tests, and fails on any error. *(maps to SC‑003 & SC‑005)*

## Phase 6: Verification & Cleanup

- [X] T057 [P] Verify that the pipeline raises an error if `plan.md` has a `Dataset URL` but real data download fails.
- [X] T057_test [P] Unit test `tests/unit/test_url_validation.py` that mocks a failed download with a URL present and asserts the error is raised.
- [X] T047 [P] Implement `code/ingestion/register_dataset.py`: Upon successful real data download, writes a permanent record to `data/verified_datasets.json` containing `url`, `checksum_sha256`, `download_date_iso`, and `source_type`. Automatically updates `plan.md` to reference this file. *(satisfies Constitution Principle II)*
- [X] T047_test [P] Contract test `tests/contract/test_dataset_registry.py` verifying that `data/verified_datasets.json` is created with correct fields and that `plan.md` is updated with the correct reference.
- [X] T048_verify_plan_update_test [P] Contract test that reads `plan.md` after a successful real download and asserts the presence of a `Dataset URL:` line. *(ensures plan reflects real data source)*
- [X] T049_test_flag_source [P] Unit test ensuring `data_source_flag.json` correctly records `"source": "real"` or `"synthetic"` based on which ingestion path succeeded.

## Phase 7: Additional Revision Tasks

- [X] T035_resolve [P] Resolve UNRESOLVED‑CLAIM c_bdbf29ca by adding explicit validation of numeric fields in `resource_summary.json` and updating the test to check for proper types and ranges. *(now covered by T035_resolve_test)*
- [X] T048_verify_plan_update [P] Add contract test `tests/contract/test_plan_dataset_url.py` that reads `plan.md` and asserts a line starting with `Dataset URL:` exists after a successful real data download. *(now covered by T048_verify_plan_update_test)*
- [X] T049_test_flag_source [P] Ensure `data_source_flag.json` correctly records `"source": "real"` or `"synthetic"` based on which ingestion path succeeded. *(now covered by T049_test_flag_source)*