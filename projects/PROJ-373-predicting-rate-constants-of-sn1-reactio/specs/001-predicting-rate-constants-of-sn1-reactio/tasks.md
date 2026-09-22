---
description: "Task list template for feature implementation"
---

# Tasks: Predicting Rate Constants of SN1 Reactions from Molecular Structure

**Input**: Design documents from `/specs/001-predict-sn1-rate-constants/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
- Paths shown below assume single project - adjusted based on plan.md structure

<!--
 ============================================================================
 IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

 The /speckit-tasks command MUST replace these with actual tasks based on:
 - User stories from spec.md (with their priorities P1, P2, P3...)
 - Feature requirements from plan.md
 - Entities from data-model.md
 - Endpoints from contracts/

 Tasks MUST be organized by user story so each story can:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan (`code/`, `data/`, `tests/`, `specs/`)
- [X] T002 Initialize Python project with `requirements.txt` (rdkit, torch, scikit-learn, shap, pandas, pyyaml, datasets)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools
- [X] T007A [P] Create `pytest.ini` configuration file in project root to enable test discovery and coverage reporting. **Deliverable**: `pytest.ini` with `[pytest]` section defining test paths and markers.
- [X] T031A [P] Create `quickstart.md` v0.1 placeholder in `specs/001-predict-sn1-rate-constants/`. **Deliverable**: A draft document with project structure, dependency installation steps, and placeholder sections for results. **DEPENDS ON**: T001, T002.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/config.py` for hyperparameters, paths, and random seeds
- [X] T005 [P] Setup `code/utils/logger.py` and `code/utils/checksum.py` for logging and data integrity
- [X] T006A [P] Create `dataset.schema.yaml` in `specs/001-predict-sn1-rate-constants/contracts/`. **Deliverable**: YAML schema file defining `smiles`, `rate_constant`, `substrate_class`, `gasteiger_charges`, `topological_indices`, `source_id`. **DEPENDS ON**: T004 (requires path and hyperparameter definitions from config.py to validate schema constraints).
- [X] T006B [P] Create `model_output.schema.yaml` in `specs/001-predict-sn1-rate-constants/contracts/`. **Deliverable**: YAML schema file defining `model_id`, `hyperparameters`, `metrics` (r2, mae), `weights_path`. **DEPENDS ON**: T004 (requires configuration from config.py for model output schema validation).
- [X] T006C [P] Create `exclusion_report.schema.yaml` in `specs/001-predict-sn1-rate-constants/contracts/`. **Deliverable**: YAML schema file defining `row_index`, `reason`, `original_smiles`. **DEPENDS ON**: T004 (requires configuration values (error codes) defined in config.py).
- [X] T007B [P] Implement contract test harness in `tests/contract/`. **Deliverable**: Create `tests/contract/__init__.py` and `tests/contract/base_runner.py` containing the `ContractTestRunner` class. **DEPENDS ON**: T006A, T006B, T006C, T007A (validates data and output against the schemas defined in these tasks).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest public SN1 kinetic datasets, parse SMILES, compute electronic descriptors, and produce a clean, stratified dataset ready for modeling.

**Independent Test**: Running the ingestion script on a known subset of the NIST database produces a CSV with valid SMILES, rate constants, and descriptors, with ≥95% success rate and proper stratification.

### Tests for User Story 1

- [X] T008 [P] [US1] Contract test for dataset schema in `tests/contract/test_dataset_schema.py` (DEPENDS ON T006A, T007B)
- [X] T009 [P] [US1] Unit test for SMILES parsing and descriptor calculation in `tests/unit/test_descriptors.py`
- [X] T010 [P] [US1] Unit test for substrate filtering logic (SN2 removal) in `tests/unit/test_filtering.py`

### Implementation for User Story 1

- [ ] T011a [US1] Implement `code/data/schema_check.py` to fetch metadata only. **Primary Source**: HuggingFace datasets `DTS-SN1-15-01-2024` (Repo ID: `author/DTS-SN1-15-01-2024`) and `SN18-All-20240204` (Repo ID: `author/SN18-All-20240204`). **Constraint**: If 'substrate_class', 'temperature', OR 'solvent' columns are missing, raise a fatal ValueError and halt the entire pipeline. **NO FALLBACK**: Do NOT fetch from UCI or derive labels. **Logic**: 1) Use `datasets.load_dataset(name, split='train', streaming=True, revision='main')` to fetch metadata only (no full download). 2) Check for required columns in the dataset info. 3) If missing, immediately raise `ValueError` with descriptive message and halt execution. 4) Handle network errors by retrying a limited number of times with exponential backoff, then failing. **Output**: `data/processed/schema_check.log`. **DEPENDS ON**: T004 (requires dataset paths and validation thresholds).
- [ ] T011b [US1] Implement `code/data/schema_validate.py` to validate schema check result and abort pipeline if needed. **Constraint**: If T011a failed, write 'ABORTED' to `.pipeline_status` and exit with code 1. **Logic**: 1) Read `data/processed/schema_check.log`. 2) If 'fatal_error' or 'missing_columns' detected, write 'ABORTED' to `data/processed/.pipeline_status` and exit with code 1. 3) If successful, write 'OK' to `data/processed/.pipeline_status`. **Output**: `data/processed/.pipeline_status`. **DEPENDS ON**: T011a.
- [ ] T011c [US1] Implement `code/data/download.py` to fetch verified SN1 data. **Constraint**: Use `datasets.load_dataset(..., streaming=True)` if size > 7GB. **Logic**: 1) Check `data/processed/.pipeline_status`. If 'ABORTED', exit with code 1 immediately. 2) If 'OK', download/stream. 3) Save raw data to `data/raw/`. 4) Handle download failures by raising an error (no synthetic fallback). **Output**: `data/raw/sn1_raw.parquet`. **DEPENDS ON**: T011b.
- [ ] T011d [US1] Initialize `data/processed/exclusion_raw.log`. **Logic**: 1) Create an empty CSV file with headers `row_index,reason,original_smiles`. 2) Ensure file exists before T011c, T012, T013 run. **Output**: `data/processed/exclusion_raw.log`. **DEPENDS ON**: None (Phase 3 start). **CRITICAL ORDERING**: T011d MUST complete before T011c, T012, and T013 begin execution.
- [ ] T011e [US1] Implement `code/data/mapping.py` to map columns and clean initial data. **Constraint**: Map `smiles` -> SMILES, `rate` -> rate_constant. **Logic**: 1) Load raw data. 2) Map columns. 3) Log rows with missing rate/SMILES to `data/processed/exclusion_raw.log` (append mode). **Output**: `data/processed/intermediate_sn1.csv`. **DEPENDS ON**: T011c, T011d.
- [ ] T012 [US1] Implement `code/data/clean.py` to canonicalize SMILES and filter primary alkyl halides. **Input**: `data/processed/intermediate_sn1.csv` (output of T011e). **Guard Clause**: If `intermediate_sn1.csv` is missing or empty, raise a fatal ValueError and log `data/processed/clean.log` with `status: 'fatal_error', reason: 'input_missing'` and exit. **Filtering Rule**: Filter rows where `substrate_class` is explicitly labeled as 'primary' (i.e., retain secondary/tertiary). **Constraint**: Do NOT use proxies. **Stereochemistry Handling**: Standardize SMILES. If fails, exclude with code 'ambiguous_stereochemistry'. **Logic**: 1) Check if `substrate_class` column exists. If missing or contains non-explicit values, raise fatal error, log `status: 'fatal_error', reason: 'missing_substrate_class'` to `data/processed/clean.log`, write 'ABORTED' to `data/processed/.pipeline_status`, and halt the entire pipeline (FR-009). 2) If column exists, filter rows where `substrate_class` == 'primary'. 3) Log all exclusions to `data/processed/clean.log`, explicitly recording the **count** of filtered primary rows to enable SC-005 verification. **Output**: `data/processed/cleaned_intermediate.csv`. **Verification**: Verify output contains no 'primary' rows. **Code Comment**: 'Filtering based on explicit substrate_class label only; no proxies used'. **DEPENDS ON**: T011e, T011d.
- [ ] T013 [US1] Implement `code/data/descriptors.py` to compute Gasteiger partial charges and topological indices. **Determinism**: Use fixed RDKit version. **Constraint**: Gasteiger charges are the approved CPU-tractable substitute for PM7 as per Plan's Constitution Check (Section: Constitution Check, Principle VI). **Logic**: Compute descriptors. If a row fails, append the failure directly to `data/processed/exclusion_raw.log` (append mode, consolidated with T011e). **Append Format**: Append a CSV row: `<row_index>,<reason_code>,<original_smiles>`. **Header Requirement**: Ensure `data/processed/exclusion_raw.log` has header `row_index,reason,original_smiles` before appending. **Output**: `data/processed/descriptors.csv`. **DEPENDS ON**: T011e (must ensure `exclusion_raw.log` exists or is created by T011d before T013 appends), T012. **CRITICAL ORDERING**: T013 must wait for T012 to complete its write operations to `exclusion_raw.log` before appending to avoid race conditions.
- [ ] T013b [US1] Validate exclusion log schema. **Input**: `data/processed/exclusion_raw.log` (from T011e, T013). **Logic**: 1) Load the log file. 2) Validate each row against `exclusion_report.schema.yaml` (from T006C). 3) If validation fails, log error and halt. **Output**: `data/processed/exclusion_validation.log`. **DEPENDS ON**: T013, T011e, T006C.
- [ ] T015 [US1] Aggregate, map, and validate exclusion logs. **Input**: `data/processed/clean.log` (from T012) and `data/processed/exclusion_raw.log` (from T011e, T013). **Guard Clause**: If `clean.log` or `exclusion_raw.log` are missing/empty, log `data/processed/exclusion_report.csv` with `status: 'blocked', reason: 'upstream_missing'` and exit. **Logic**: 1) Merge logs into `data/processed/exclusion_mapped.json`. 2) Map error strings to schema codes using the following complete mapping: {'Primary substrate': 'primary_substrate_filter', 'Ambiguous stereochemistry': 'ambiguous_stereochemistry', 'Descriptor calculation failed': 'descriptor_failure', 'Missing rate constant': 'missing_rate_constant', 'Missing SMILES': 'missing_smiles'}. 3) Validate against `exclusion_report.schema.yaml`. 4) Save final list to `data/processed/exclusion_report.csv`. **Constraint**: Must wait for T012 and T013 to finish writing their logs. **DEPENDS ON**: T012, T013b.
- [ ] T016 [US1] Save final processed dataset to `data/processed/cleaned_sn1.csv` with checksum. **Input**: `data/processed/cleaned_intermediate.csv` (from T012). **Logic**: 1) Load cleaned data. 2) Calculate `success_rate = (len(final_df) / len(input_df))` where `input_df` is `data/processed/intermediate_sn1.csv` (output of T011e). 3) **Assert**: If `success_rate < 0.95`, log failure to `data/processed/success_rate.json` with `status: 'FAIL', reason: 'success_rate_below_threshold'` and exit with code 1. **Enforcement**: This exit code 1 MUST be detected by the orchestration layer (`main.py`), which will halt the pipeline and prevent downstream tasks (e.g., T014) from executing. 4) If passed, log `success_rate` to `data/processed/success_rate.json` with `status: 'PASS'`. 5) Verify non-null descriptors in final_df. 6) Save CSV and generate checksum. **Output**: `data/processed/cleaned_sn1.csv` and `data/processed/success_rate.json`. **DEPENDS ON**: T015, T012, T013.
- [ ] T014 [US1] Implement `code/data/split.py` to perform a stratified split by substrate class. **Input**: `data/processed/cleaned_sn1.csv` (from T016). **Logic**: 1) Load cleaned dataset. 2) Stratify on `substrate_class`. 3) Split data into training, validation, and test sets. 4) Verify proportional representation matches original distribution within 5% variance. 5) Save splits to `data/processed/split_train.csv`, `data/processed/split_val.csv`, `data/processed/split_test.csv`. **Output**: Split CSV files and `data/processed/split_report.json`. **DEPENDS ON**: T016.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Graph Neural Network Training and Evaluation (Priority: P2)

**Goal**: Train a Message Passing Neural Network (MPNN) on the processed dataset using CPU-only inference, perform hyperparameter optimization, and evaluate against baselines.

**Independent Test**: The training job completes within 6 hours on a 2-core CPU runner., saves model weights, and outputs R²/MAE metrics comparing MPNN to linear regression with statistical significance.

### Implementation for User Story 2

- [X] T019 [US2] Implement `code/models/mpnn.py` with shallow architecture. **Constraint**: Layer count MUST be configurable via `config.py` but bounded within 1-4 range. **Logic**: Read layer count from `config.py` and validate against bounds.
- [X] T020 [US2] Implement `code/models/train.py` with random search hyperparameter optimization (≤50 configurations).
- [X] T021 [US2] Implement `code/models/evaluate.py` to calculate R² and MAE, and perform bootstrap comparison. **Output**: Save metrics to `artifacts/training_metrics.json`.
- [X] T022 [US2] Save best model weights to `artifacts/best_model.pt` (in `.pt` PyTorch format) and metrics to `artifacts/metrics.json`. **Selection Logic**: Select configuration with highest validation R². **Schema**: `metrics.json` must conform to `model_output.schema.yaml`. **DEPENDS ON**: T016, T020, T021.
- [X] T023 [US2] Log top hyperparameter configurations to `artifacts/hyperparameter_search.csv`. **Logic**: Identify the top configurations. **Format**: CSV with columns `config_id`, `learning_rate`, `hidden_dim`, `dropout`, `r2_val`, `mae_val`. **DEPENDS ON**: T020, T021.

### Tests for User Story 2

- [X] T017 [P] [US2] Unit test for MPNN architecture and forward pass in `tests/unit/test_mpnn.py` (DEPENDS ON T019)
- [X] T018 [P] [US2] Integration test for training loop with small subset in `tests/integration/test_training.py` (DEPENDS ON T019, T020)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Interpretability and Sensitivity Analysis (Priority: P3)

**Goal**: Generate feature importance analysis, perform sensitivity analysis, validate findings via perturbation studies, and run collinearity diagnostics.

**Independent Test**: The interpretability module produces a SHAP summary plot, a sensitivity report, and a perturbation study confirming feature importance correlates with predictive performance.

### Implementation for User Story 3

- [X] T026 [US3] Implement `code/analysis/interpret.py` to generate SHAP values and summary plots. **Logic**: Aggregate graph-level SHAP values to global tabular descriptors. **Artifact**: Save node-level SHAP values to `artifacts/node_shap_values.npy`. **Artifact**: Generate `node_to_atom_mapping.json` mapping node indices to atom features. **DEPENDS ON**: T022, T020, T021.
- [X] T035A [US3] Implement `code/analysis/multi_seed_runner.py` to execute training across multiple random seeds. **Logic**: 1) Load best configuration from T023. 2) Define a list of distinct random seeds. 3) For each seed, re-run the training pipeline by invoking: `python code/models/train.py --seed {seed} --config-path code/config.py`. 4) If training fails for a specific seed, log failure to `artifacts/seeds/seed_{seed_id}/failure.log` and continue to the next seed (do not halt). 5) Save model weights and metrics for each successful seed to `artifacts/seeds/seed_{seed_id}/`. **Output**: Directory of models and metrics per seed. **DEPENDS ON**: T023, T016, T020.
- [X] T035 [US3] Implement `code/analysis/consistency.py` to verify SHAP consistency across random seeds (SC-004). **Logic**: 1) Load data from T016 and best config from T023. 2) Load models from T035A (multiple seeds). 3) Run SHAP analysis on test set for each seed. 4) Compute Kendall's Tau correlation of feature rankings across these runs. **SC-004 Scope**: This task covers the seed consistency part of SC-004. The perturbation study drop is covered by T029B. 5) **Feasibility Check**: Before running, run a single epoch on [deferred] of data and extrapolate to estimate full training time. If > 5.5 hours, dynamically select the largest feasible subset (max rows within 5.5 hours) and use that for the consistency check. **Deliverable**: Save report to `artifacts/shap_consistency_report.md`. **DEPENDS ON**: T016, T023, T022, T035A.
- [ ] T029A [US3] Implement `code/analysis/shap_aggregation.py` to aggregate node-level SHAP values to atom-level features. **Input**: `artifacts/node_shap_values.npy` (from T026), `data/processed/split_test.csv` (from T014), `artifacts/node_to_atom_mapping.json` (from T026). **Logic**: 1) Map node SHAP values to atoms using `node_to_atom_mapping.json`. 2) Sum absolute SHAP values for each unique atom across the test set. 3) Sort atoms by total absolute SHAP. 4) Select top-k=10 atoms. 5) Save mapping to `artifacts/top_k_atoms.json` with columns `atom_id`, `total_shap`, `rank`. **Output**: `artifacts/top_k_atoms.json`. **DEPENDS ON**: T026, T014.
- [ ] T029B [US3] Implement perturbation study in `code/analysis/perturbation.py`. **Input**: `data/processed/split_test.csv` (from T014), `artifacts/best_model.pt` (from T022), `artifacts/top_k_atoms.json` (from T029A). **Method**: Direct implementation of feature removal. **Logic**: 1) Load top-k atoms from T029A. 2) **Mapping**: Identify the node indices in the graph tensor corresponding to the `atom_id` from the JSON (e.g., via `node_to_atom_mapping.json` in T026). 3) Set node features of these atoms to zero in the test set. 4) Re-run inference on fixed best model using the perturbed test set. 5) Measure drop in R² by comparing against baseline R². 6) Save results to `artifacts/perturbation_results.csv` with columns `baseline_r2`, `perturbed_r2`, `delta_r2`. 7) **Verification**: Scan `perturbation_results.csv` and logs for forbidden causal language (e.g., 'causes', 'determines'). If found, log a warning and flag the result. 8) **Framing**: Explicitly log the delta (drop) in R² to verify FR-008, and frame the result as a "robustness check" (associational), NOT as "causality". **Verification**: Explicitly log the delta (drop) in R² to verify FR-008. **DEPENDS ON**: T022, T029A, T014, T021.
- [X] T036 [US3] Implement `code/analysis/sensitivity_runner.py` to perform sensitivity analysis by sweeping top-k descriptors (linear range starting from a minimum threshold). **Logic**: 1) Load best model and cleaned dataset. 2) Sort descriptors by absolute SHAP magnitude. 3) For k in a range of small integers starting from a minimal value: Select top k descriptors. 4) Perform inference-only evaluation. 5) Calculate variance. **Verification Step**: Explicitly calculate the variance of R² across the sweep and log a **PASS** if variance < 0.01 (SC-003) or **FAIL** otherwise. **Artifact**: Save to `artifacts/top_k_sensitivity.csv` with `variance` column and `status` column. **DEPENDS ON**: T016, T022.
- [X] T037 [US3] Implement `code/analysis/hyperparameter_sensitivity.py` to measure model robustness. **Logic**: 1) Select a stratified sample of a representative size. 2) Test explicit configurations. 3) Train shallow MPNN on subset. 4) Evaluate on held-out subset. 5) Calculate variance. **Verification Step**: Explicitly calculate the variance and log a **PASS** if variance < 0.01 (SC-003) or **FAIL** otherwise. **Artifact**: Save to `artifacts/hyperparameter_sensitivity_report.csv` with `variance` column and `status` column. **DEPENDS ON**: T022, T016.
- [X] T027 [US3] Implement `code/analysis/interpret.py` to aggregate results from T036 and T037. **Logic**: Aggregate R² and MAE. Calculate overall variance from the `variance` columns in the upstream CSVs. **Verification Step**: Explicitly calculate the overall variance and log a **PASS** if variance < 0.01 (SC-003) or **FAIL** otherwise. **Artifact**: Save to `artifacts/sensitivity_report.csv` with `overall_variance` column and `status` column. **DEPENDS ON**: T036, T037.
- [ ] T028 [US3] Implement `code/analysis/collinearity.py` to calculate VIF and generate JSON report. **Input**: Feature matrix from `data/processed/cleaned_sn1.csv`. **Guard Clause**: If `cleaned_sn1.csv` is missing or empty, raise a fatal ValueError and log `artifacts/collinearity_report.json` with `status: 'fatal_error', reason: 'input_missing'` and exit. **Logic**: 1) Check dataset size. If < 2 features, log `status: 'skip', reason: 'insufficient_features'` and exit. 2) **Filtering**: Explicitly exclude Gasteiger charges from the feature matrix before calculation. 3) Calculate VIF for all remaining predictors. 4) Identify pairs with VIF > 5. 5) Generate strict JSON report (`collinearity_report.json`) with keys: `descriptor_a`, `descriptor_b`, `vif_score`, `flag_reason`. **Constraint**: Do NOT generate descriptive text or `is_flagged` boolean. **Flag Reason Logic**: Set `flag_reason` to "VIF > 5" for flagged pairs. **Verification**: Ensure `collinearity_report.json` is generated with valid JSON. **Artifact**: Save to `artifacts/collinearity_report.json`. **DEPENDS ON**: T016.

### Tests for User Story 3

- [X] T024 [P] [US3] Unit test for VIF calculation in `tests/unit/test_collinearity.py` (DEPENDS ON T028)
- [X] T025 [P] [US3] Unit test for SHAP value generation in `tests/unit/test_shap.py` (DEPENDS ON T026)

**Checkpoint**: At this point, User Story 3 implementation is complete.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T032 Code cleanup and refactoring of `code/main.py` orchestration script
- [X] T033A [P] Execute full pipeline integration test on a small subset of rows. **Deliverable**: Raw execution logs. **Success Criteria**: Exit code 0 and specific log strings "Pipeline completed successfully". **DEPENDS ON**: T016, T022.
- [X] T033B [P] Validate exit codes and artifact existence from T033A. **Deliverable**: Validation status. **Logic**: Verify exit code is 0 and key artifacts exist. **DEPENDS ON**: T033A.
- [X] T033C [P] Generate `artifacts/integration_test_report.md` based on T033A/B results. **Logic**: If T033A/B pass, document success. If fail, document failure with error logs. **DEPENDS ON**: T033A, T033B.
- [X] T031B [P] Finalize `quickstart.md` in `specs/001-predict-sn1-rate-constants/`. **Dependencies**: T033C. **Logic**: Update `quickstart.md` with actual paths, command examples, and verified output descriptions from T033C. **Fallback**: If T033C fails, update based on manual verification of code paths and standard defaults. **DEPENDS ON**: T033C.
- [X] T034 [P] Validate `quickstart.md` against actual execution. **Dependencies**: T031B, T033C (or T031B fallback evidence). **Logic**: 1) If T033C succeeded, validate against T033C's execution evidence. 2) If T033C failed and T031B used fallback, validate against manual verification evidence. 3) Fallback: If no execution evidence exists, validate against code structure and `config.py` defaults. **DEPENDS ON**: T031B, T033C.

---

## Phase 7: Final Verification & Reporting

**Purpose**: Ensure all success criteria are met and prepare final documentation.

- [ ] T030 [P] Generate `artifacts/final_report.md` structure. **Logic**: Create a template with sections: `# Final Report`, `## Executive Summary`, `## Methodology`, `## Results`, `## Limitations`, `## Conclusion`. **Output**: `artifacts/final_report.md` (empty template). **DEPENDS ON**: None (Phase 7 start).
- [ ] T040 [P] Perform a final end-to-end validation run on the full dataset (if time permits) or the largest feasible subset. **Logic**: 1) Re-run the full pipeline (`main.py`) from ingestion to final report generation using the production configuration. 2) **Dynamic Budgeting**: Count rows in `data/processed/cleaned_sn1.csv` to determine N. If N >= 2000, reduce hyperparameter search configurations to a manageable limit before execution by passing `--max-configs` to `code/models/train.py`. 3) Enforce a timeout mechanism using Python's signal module with a configurable time limit. 4) If timeout exceeded, log failure to `artifacts/feasibility_test_log.json` and exit gracefully. 5) If successful, record actual runtime and verify all artifacts. 6) Compare results against T033. **Constraint**: Timeout mechanism MUST be implemented to satisfy SC-002. **Output**: `artifacts/feasibility_test_log.json`. **DEPENDS ON**: T016, T022, T028.
- [ ] T039 [US3] Generate final comprehensive report aggregating all metrics, plots, and statistical analyses. **Logic**: 1) Aggregate `metrics.json`, `shap_consistency_report.md`, `sensitivity_report.csv`, `perturbation_results.csv`, `collinearity_report.json`, `hyperparameter_search.csv`, and `feasibility_test_log.json` (from T040). 2) **Explicit SC Verification**: For each Success Criterion (SC-001 to SC-005), calculate the boolean pass/fail status:
 - SC-001: `MPNN_R2 - Linear_R2 > 0.05` AND `p < 0.05` -> PASS/FAIL.
 - SC-002: `runtime <= 6 hours` -> PASS/FAIL.
 - SC-003: `variance < 0.01` -> PASS/FAIL.
 - SC-004: `consistency_score > threshold` AND `delta_r2 > threshold` -> PASS/FAIL.
 - SC-005: `success_rate >= 0.95` -> PASS/FAIL.
 3) Create a summary section for each SC explicitly stating whether it is met (PASS/FAIL). 4) Include a "Limitations" section. 5) Output Artifact: Save to `artifacts/final_report.md`. **Schema Requirements**: The report MUST contain the following sections in order: `# Final Report`, `## Executive Summary`, `## Methodology`, `## Results`, `## Limitations`, `## Conclusion`. **DEPENDS ON**: T040, T022, T028, T029A, T029B, T030, T035, T036, T037.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Final Verification (Phase 7)**: Depends on all User Stories and Polish phases

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Strictly depends on T016 (cleaned dataset)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Strictly depends on T022 (model training) and T016 (cleaned dataset).

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data ingestion/cleaning before splitting
- Splitting before training
- Training before evaluation and interpretability

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel (once their respective implementations are complete)
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (IF T006A, T006B, T006C, T007B are complete):
# Note: T008 depends on T006A, T007B, so those must finish first.
Task: "Contract test for dataset schema in tests/contract/test_dataset_schema.py" (DEPENDS ON T006A, T007B)
Task: "Unit test for SMILES parsing and descriptor calculation in tests/unit/test_descriptors.py"
Task: "Unit test for substrate filtering logic in tests/unit/test_filtering.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/schema_check.py to verify dataset metadata"
Task: "Implement code/data/schema_validate.py to validate schema check result and abort pipeline"
Task: "Implement code/data/download.py to fetch verified SN1 data"
Task: "Implement code/data/descriptors.py to compute Gasteiger charges"
Task: "Implement code/data/clean.py to canonicalize SMILES and filter"
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
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Model Training)
 - Developer C: User Story 3 (Analysis)
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
- **Critical Constraint**: All tasks must be executable on CPU-only CI with limited resources and a bounded time limit. No GPU, no 8-bit quantization, no heavy QM calculations.
- **Note on Constitution VI**: The Plan explicitly substitutes Gasteiger charges for PM7 to satisfy CPU constraints. This deviation is documented in the Plan's Constitution Check and is the approved implementation path for this project.