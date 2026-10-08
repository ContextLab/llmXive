# Tasks: Predicting Molecular Permeability Coefficients Using Graph Neural Networks and Publicly Available Datasets

**Input**: Design documents from `/specs/001-molecular-permeability-gnn/`
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

- [ ] T001 [P] Create `setup_dirs.sh` script to programmatically generate the project directory structure: `projects/PROJ-422-predicting-molecular-permeability-coeffi/code/data`, `projects/PROJ-422-predicting-molecular-permeability-coeffi/code/models`, `projects/PROJ-422-predicting-molecular-permeability-coeffi/code/analysis`, `projects/PROJ-422-predicting-molecular-permeability-coeffi/data/raw`, `projects/PROJ-422-predicting-molecular-permeability-coeffi/data/processed`, `projects/PROJ-422-predicting-molecular-permeability-coeffi/data/interim`, `projects/PROJ-422-predicting-molecular-permeability-coeffi/results`, `projects/PROJ-422-predicting-molecular-permeability-coeffi/tests/unit`, `projects/PROJ-422-predicting-molecular-permeability-coeffi/tests/integration`. The script must be executable. **Verification**: Run `bash setup_dirs.sh` followed by `test -d projects/PROJ-422-predicting-molecular-permeability-coeffi/code/data && test -d projects/PROJ-422-predicting-molecular-permeability-coeffi/code/models && test -d projects/PROJ-422-predicting-molecular-permeability-coeffi/code/analysis && test -d projects/PROJ-422-predicting-molecular-permeability-coeffi/data/raw && test -d projects/PROJ-422-predicting-molecular-permeability-coeffi/data/processed && test -d projects/PROJ-422-predicting-molecular-permeability-coeffi/data/interim && test -d projects/PROJ-422-predicting-molecular-permeability-coeffi/results && test -d projects/PROJ-422-predicting-molecular-permeability-coeffi/tests/unit && test -d projects/PROJ-422-predicting-molecular-permeability-coeffi/tests/integration && echo "All 9 directories exist"`. If any check fails, the task is incomplete.

- [X] T002 Initialize Python 3.11 project with pinned dependencies in `requirements.txt`. **Method**: Use `pip freeze` to pin versions. **Verification**: Run `pip check` and ensure no conflicts.

- [X] T003 [P] Configure linting (ruff) and formatting (black) tools. **Artifacts**: Create `pyproject.toml` with specific rules (E, F, W) and `.black` config. **Verification**: Run `ruff check . && black --check .`.

- [X] T003a [P] Create `generate_config.py` script to programmatically generate `config.yaml` with configurable parameters explicitly linked to Functional Requirements:
 1. `validation.bias_threshold:` (float, default 0.85) - Controls FR-013 bias check (Pearson correlation threshold).
 2. `validation.retention_threshold:` (float, default 0.95) - Controls FR-011 retention check.
 3. **Verification**: Run `python generate_config.py && cat config.yaml` to confirm keys and default values. Note: Stratification logic (FR-003) is fixed at < 5% difference and does not require a configurable threshold; the config file must NOT contain a `validation.stratification_threshold` key.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/utils/logging.py` for structured JSON logging and result artifact generation. **Verification**: Run `pytest tests/unit/test_skeleton.py::test_logging_imports` which asserts that `Logger` class exists and has `log_metric`, `log_error` methods.

- [X] T005 [P] Create `code/data/download.py` skeleton: Define class `DataLoader` with method `fetch_dataset(source: str)` and `verify_checksum(file_path: str)`. **Contract**: Define return types and exception signatures for T013 implementation. **Verification**: Run `pytest tests/unit/test_skeleton.py::test_download_skeleton` which asserts `DataLoader` class exists and methods are callable.

- [X] T006 [P] Create `code/data/preprocess.py` skeleton: Define class `MoleculeProcessor` with method `parse_smiles(smiles: str)` and `calculate_descriptors(mol)`. **Contract**: Define return types and exception signatures for T014 implementation. **Verification**: Run `pytest tests/unit/test_skeleton.py::test_preprocess_skeleton` which asserts `MoleculeProcessor` class exists and methods are callable.

- [X] T007 [P] Create `code/data/split.py` skeleton: Define function `stratified_split(df, stratify_col)` and `random_split(df)`. **Contract**: Define return types and exception signatures for T017 implementation. **Verification**: Run `pytest tests/unit/test_skeleton.py::test_split_skeleton` which asserts functions exist and are callable.

- [X] T008 [P] Create `code/models/gnn.py` skeleton: Define class `MPNN` (PyTorch Geometric `nn.Module`) with `forward` method. **Contract**: Define input/output tensor shapes for T020 implementation. **Verification**: Run `pytest tests/unit/test_skeleton.py::test_gnn_skeleton` which asserts `MPNN` class exists and `forward` method is callable.

- [X] T009 [P] Create `code/models/rf.py` skeleton: Define function `train_random_forest(X, y)` and `predict(model, X)`. **Contract**: Define input/output types for T021 implementation. **Verification**: Run `pytest tests/unit/test_skeleton.py::test_rf_skeleton` which asserts functions exist and are callable.

- [X] T010 [P] Create `code/analysis/evaluate.py` skeleton: Define functions `calculate_metrics(y_true, y_pred)` and `paired_ttest(errors_a, errors_b)`. **Contract**: Define return types for T024/T025 implementation. **Verification**: Run `pytest tests/unit/test_skeleton.py::test_evaluate_skeleton` which asserts functions exist and are callable.

- [X] T011 [P] Create `code/analysis/explain.py` skeleton: Define functions `explain_rf(model, X)` and `explain_gnn(model, graph)`. **Contract**: Define return types for T029/T030 implementation. **Verification**: Run `pytest tests/unit/test_skeleton.py::test_explain_skeleton` which asserts functions exist and are callable.

- [X] T012 [P] Setup `tests/unit/test_preprocess.py` and `tests/integration/test_pipeline.py` scaffolding. **Verification**: Run `pytest tests/unit/test_skeleton.py` to ensure all skeleton tests pass.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest public datasets, parse SMILES to graphs/descriptors, handle invalid data, and create stratified splits. **Strict Constraint**: The system MUST attempt to find experimental permeability data. If unavailable, the pipeline MUST switch to 'Proxy Mode' using calculated logP as the target, as mandated by plan.md Phase 0 Step 2.

**Independent Test**: The pipeline runs end-to-end on a sample, producing `data/processed/train.csv`, `data/processed/test.csv`, and a log confirming the split strategy (stratified or random) and data retention.

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/data/download.py`:
 1. **Verified Dataset List**: Use the following explicit list of verified HuggingFace dataset IDs: `['moleculenet/bace', 'moleculenet/bbbp', 'moleculenet/esol', 'moleculenet/freesolv', 'moleculenet/lipo', 'chembl/chembl_v30']`.
 2. **Target Column Inspection**: For each fetched dataset, check for the presence of experimental permeability columns. The exhaustive list of acceptable experimental column names is: `['permeability', 'logP_exp', 'PC', 'p_logP']`.
 3. **Selection Logic**: Iterate through the list in order. Select the first dataset that contains valid SMILES strings and at least one column from the experimental list.
 4. **Constraint**: Do NOT raise `RuntimeError` immediately if the first dataset fails. Only raise if *all* verified sources are exhausted or none contain valid SMILES/target pairs.
 5. **Verification**: Log the successful dataset source and the detected target column name.

- [X] T013b [US1] Implement `code/data/download.py` target validation and Proxy Mode:
 1. **Prerequisite**: Depends on T013 completion.
 2. Check if the target column contains **experimental** permeability coefficients (using the list from T013).
 3. **Proxy Mode Logic**: If no experimental target is found, check for a calculated `logP` column (or standard `logP` descriptor). If found, switch to **Proxy Mode**: set `is_proxy_target: true` in `results/metrics.json`, log "Switching to Proxy Mode: using calculated logP", and **continue** the pipeline.
 4. **Strict Constraint**: Only raise `RuntimeError("No experimental or proxy permeability target found. Pipeline halted.")` if neither experimental nor proxy targets are available.
 5. **Output Requirement**: Explicitly set a flag `is_proxy_target: false` (or `true` if Proxy Mode is active) in the final `results/metrics.json`. **Schema**: `{"is_proxy_target": <bool>, ...}`. Do NOT update `config.yaml` (read-only).
 6. **Verification**: Run `python -c "import json; d=json.load(open('results/metrics.json')); assert 'is_proxy_target' in d"` AND verify the pipeline continues to T014a.

- [X] T014a [US1] Implement `code/data/preprocess.py` (Part 1):
 1. **Prerequisite**: Depends on T013b (Target Validation).
 2. Parse SMILES using RDKit.
 3. Compute the following **exact** set of standard molecular descriptors: `MW`, `logP`, `TPSA`, `NumRotatableBonds`, `NumHDonors`, `NumHAcceptors`, `NumAromaticRings`, `NumAliphaticRings`, `NumSaturatedRings`, `FractionCSP3`.
 4. Handle missing values via median imputation or row exclusion with logging.

- [X] T014b [US1] Implement `code/data/preprocess.py` (Part 2):
 1. **Prerequisite**: Depends on T013b (Target Validation).
 2. Construct molecular graphs.
 3. **Unified Output**: Generate a single processed dataset file `data/processed/processed_data.csv` containing SMILES, target, standard descriptors (from T014a), and graph representations (as adjacency matrices or edge lists in separate columns). Do NOT generate a separate `graph_features.csv` file.
 4. **Verification**: Run `python -c "import pandas as pd; df=pd.read_csv('data/processed/processed_data.csv'); assert 'logP' in df.columns and 'TPSA' in df.columns"`.

- [X] T015 [US1] Implement invalid SMILES handling in `code/data/preprocess.py`:
 1. Log errors and exclude invalid rows.
 2. **Constraint**: Enforce FR-011 strictly: If valid molecule retention < 95%, log a warning "Data Integrity Warning: Retention < 95% (X%)", set `data_integrity_warning: true` in `results/metrics.json`, AND **trigger `SystemExit(1)`** to halt the pipeline immediately. The pipeline must NOT continue if retention is below the threshold.
 3. **Verification**: Run `python -c "import json; d=json.load(open('results/metrics.json')); assert 'data_integrity_warning' in d"`. (Note: This task ensures the exit occurs before metrics are written in a failure state).

- [X] T016 [US1] Implement FR-013 (Bias Check) in `code/data/preprocess.py`:
 1. Calculate **Pearson correlation** between input descriptors and the target variable.
 2. Load the threshold parameter from `config.yaml` key `validation.bias_threshold` (default 0.85).
 3. **Conditional Logic**: If the **maximum absolute correlation** across all descriptors exceeds the threshold, flag results as `bias_warning: "potentially confounded"` and log a warning. The pipeline must continue but the final report must highlight this flag.

- [X] T017 [US1] Implement `code/data/split.py` and Stratification Report:
 1. **Prerequisite**: Depends on T013b (Target Validation), T014a/T014b (Preprocessing).
 2. **Column Discovery**: Check for stratification columns in this order: `polymer_type`, `membrane_type`, `material`. If found, use the first available one.
 3. **Stratification Logic**: If a stratification column is found, perform a stratified split ensuring distribution difference < 5% for each class.
 4. **Fallback**: If NO stratification column is found, perform a random split and log a warning: "Stratification column missing. Fallback to random split. Data leakage risk acknowledged for feasibility study."
 5. Save splits to `data/processed/train.csv` and `data/processed/test.csv`.
 6. **Report Generation**: Immediately after splitting, generate `results/stratification_report.md` with required sections: "Split Strategy", "Stratification Column", "Distribution Diff", "Retention Rate".
 7. **Verification**: Run `grep -q "Split Strategy" results/stratification_report.md && grep -q "Stratification Column" results/stratification_report.md && grep -q "Distribution Diff" results/stratification_report.md && grep -q "Retention Rate" results/stratification_report.md`.

- [X] T018 [US1] Write unit tests in `tests/unit/test_preprocess.py` for SMILES parsing, descriptor calculation, invalid handling, and graph feature flattening.

- [X] T019 [US1] Write integration test in `tests/integration/test_pipeline.py` to verify end-to-end data flow, target validation, and file outputs.

**Checkpoint**: Data pipeline functional; valid splits and features ready for modeling.

---

## Phase 4: User Story 2 - Comparative Model Training and Evaluation (Priority: P2)

**Goal**: Train CPU-optimized GNN (MPNN) and Random Forest baselines, evaluate metrics, and perform statistical significance testing. **Strict Constraint**: Models must be trained on the selected target (experimental permeability or proxy logP).

**Independent Test**: Training completes within 6h/7GB RAM, outputs metrics to `results/metrics.json`, and reports a p-value for the performance gap.

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement `code/models/gnn.py`: Define MPNN architecture (multiple layers) compatible with CPU execution; include early stopping logic based on validation loss.

- [X] T021 [P] [US2] Implement `code/models/rf.py`: Configure Random Forest regressor for baseline comparison.

- [X] T022 [US2] Implement `code/analysis/train.py`:
 1. Implement the full training loop for GNN and RF on `data/processed/train.csv`.
 2. **Constraint**: Enforce CPU-only execution (no CUDA device assignment) to adhere to the free-tier runner constraints.
 3. Implement early stopping logic based on validation loss with patience parameter.
 4. Save model checkpoints to `data/interim/gnn_checkpoint.pt` and `data/interim/rf_checkpoint.pkl` upon completion or early stopping.
 5. **Logging**: Log training duration (`total_training_time_hours`) and peak memory usage (`peak_memory_gb`) to `results/training_log.json` and `results/metrics.json`. **Schema**: `{"total_training_time_hours": <float>, "peak_memory_gb": <float>}`. **Verification**: Run `python -c "import json; d=json.load(open('results/training_log.json')); assert 'total_training_time_hours' in d and 'peak_memory_gb' in d"`.

- [X] T023 [US2] Implement FR-012 (Ablation Study - Training):
 1. **Prerequisite**: Depends on T014b (Unified Data Generation), **T017 (Data Splits)**, and T022 (Training).
 2. Train a Random Forest baseline using **ONLY** graph-derived features (e.g., `mean_node_degree`, `graph_connectivity`, `aromatic_ring_count`, `substructure_counts`, `max_path_length`) extracted from the unified dataset.
 3. **Strict Constraint**: Explicitly exclude all standard molecular descriptors (MW, logP, TPSA) in the input matrix to isolate the incremental value of topology.
 4. **Scientific Framing**: This is a mandatory requirement (FR-012), not exploratory. The results must be included in the primary metrics.
 5. Save model to `data/interim/rf_ablation_checkpoint.pkl`.

- [X] T023b [US2] Implement FR-012 (Ablation Study - Reporting):
 1. **Prerequisite**: Depends on T023 (Ablation Training) and T024 (Evaluation).
 2. Calculate metrics (RMSE, MAE, R²) for the ablation model on `data/processed/test.csv`.
 3. **Output Artifact**: Save results to `results/metrics.json` (merged with primary metrics) and generate `results/ablation_report.md`.

- [X] T024 [US2] Implement `code/analysis/evaluate.py`:
 1. Calculate RMSE, MAE, R² for all models (GNN, RF-Baseline, RF-Ablation) on `data/processed/test.csv`.
 2. Generate a structured JSON artifact `results/metrics.json` containing all metrics per model.
 3. **Crucial**: Generate `results/predictions_errors.json` containing the raw prediction errors for each model to enable T025 and T025b.
 4. Ensure the output schema includes fields for `model_name`, `rmse`, `mae`, `r2`, `training_time`, and `peak_memory_gb`.

- [X] T025 [US2] Implement FR-007: Paired t-test on prediction errors between GNN and **Standard RF** (trained on standard descriptors).
 1. **Prerequisite**: Depends on T021 (Standard RF Training) and T024 (Evaluation).
 2. **Precondition**: Verify the target variable type (experimental vs proxy) and log it in the statistical report.
 3. **Requirement**: Perform a paired t-test on the prediction errors of the GNN and the **Standard RF** model (trained on standard descriptors). Explicitly calculate and log Cohen's d (effect size) and 95% Confidence Intervals for the mean difference to `results/metrics.json`.
 4. **Formula**: 
    - **Cohen's d**: `d = (mean_error_gnn - mean_error_rf) / pooled_std`, where `pooled_std = sqrt(((n1-1)*std1^2 + (n2-1)*std2^2) / (n1+n2-2))`.
    - **95% CI**: `mean_diff ± t_crit * sqrt((std1^2/n1) + (std2^2/n2))`, using `scipy.stats.t.ppf`.
 5. **Success Criteria Alignment**: This task implements the measurable outcomes defined in SC-001 (Performance Gap), SC-002 (Statistical Significance), SC-002b (Effect Size), and SC-002c (Confidence Intervals).
 6. **Constraint**: Use `scipy.stats` for t-test and manual calculation for Cohen's d to ensure reproducibility without heavy dependencies.

- [X] T025c [US2] Implement FR-005: Paired t-test on prediction errors between GNN and RF-Ablation (Graph-derived features only).
 1. **Prerequisite**: Depends on T023 (Ablation Training), and T024 (Evaluation).
 2. **Requirement**: Perform a paired t-test on the prediction errors of the GNN and the **RF-Ablation** model. Calculate Cohen's d and 95% CI.
 3. **Rationale**: This is a secondary analysis to isolate the value of topology vs. the standard baseline, distinct from the primary FR-007 hypothesis.
 4. **Output**: Append results to `results/metrics.json` under a new key `gnn_vs_rf_ablation`.

- [X] T025b [US2] Implement post-hoc power analysis:
 1. **Prerequisite**: Depends on T025 (T-test results) and T024 (specifically `results/predictions_errors.json` for sample size verification).
 2. **Implementation**: Calculate statistical power using the observed effect size (Cohen's d) and sample size. This is required to interpret SC-002b/c (Effect Size/CI) in the context of sample adequacy, as mandated by Plan Phase 2, Step 4.
 3. **Output Artifact**: Generate `results/power_analysis.json` containing power value, effect size, sample size, and alpha level. **Schema**: `{"power": <float>, "effect_size": <float>, "sample_size": <int>, "alpha": 0.05}`. **Verification**: Run `python -c "import json; d=json.load(open('results/power_analysis.json')); assert all(k in d for k in ['power', 'effect_size', 'sample_size', 'alpha'])"`.
 4. Ensure this artifact is explicitly linked to the study's statistical validity.

- [X] T027 [P] [US2] Write unit tests for `code/models/gnn.py` and `code/models/rf.py` (forward pass, shape checks).

- [X] T028 [P] [US2] Write integration test in `tests/integration/test_pipeline.py` for full training and evaluation flow.

**Checkpoint**: Models trained, metrics logged, and statistical significance determined.

---

## Phase 5: User Story 3 - Feature Attribution and Interpretability Analysis (Priority: P3)

**Goal**: Apply GNNExplainer to GNN and SHAP to RF to identify and rank predictive features/substructures. **Strict Constraint**: Analysis must proceed with the selected target (experimental permeability or proxy logP).

**Independent Test**: Analysis generates ranked feature lists and visualizations highlighting topological features unique to GNN.

### Implementation for User Story 3

- [X] T029 [P] [US3] Implement `code/analysis/explain.py`:
 1. Apply SHAP to the Random Forest model.
 2. Generate a ranked list of standard descriptors by absolute mean SHAP value.
 3. Save the ranked list to `results/feature_importance_rf.json`.

- [X] T030 [US3] Implement `code/analysis/explain.py`:
 1. Apply GNNExplainer to the GNN model.
 2. Identify top influential node-level substructures (e.g., aromatic rings, functional groups) across the test set.
 3. Save the identified substructures and their importance scores to `results/feature_importance_gnn.json`.

- [X] T031 [US3] Implement FR-009: Comparative Feature Report Logic.
 1. **Prerequisites**: Requires model outputs from US2 (T022-T024) to map features to performance context, and feature importance from T029/T030.
 2. **Precondition**: Verify the target variable type and note it in the report context.
 3. **Comparison Logic**: Compare the top SHAP features vs. the top GNNExplainer substructures. Identify substructures with high GNNExplainer scores that correspond to low-ranked SHAP descriptors.
 4. **Output**: Prepare data structures for the report.

- [X] T031b [US3] Generate Comparative Report (FR-009).
 1. **Prerequisite**: Depends on T031 (Mapping Logic), T023b (Ablation Reporting) to ensure ablation results are included.
 2. **Output Format**: Generate a Markdown report `results/comparative_report.md`.
 3. **Required Sections**: "Top SHAP Features", "Top GNN Substructures", "Comparative Analysis", "Ablation Study Results".
 4. **Scientific Framing**: Highlight substructures identified by GNNExplainer that are *not* captured by standard descriptors, framing this as "Topological features learned by GNN beyond standard descriptors" for the selected target (permeability).
 5. **Verification**: Run `grep -q "Top SHAP Features" results/comparative_report.md && grep -q "Top GNN Substructures" results/comparative_report.md && grep -q "Comparative Analysis" results/comparative_report.md && grep -q "Ablation Study Results" results/comparative_report.md`.

- [X] T032 [US3] Generate visualizations (heatmaps/bar charts) for feature importance in `results/figures/`.
 1. Create a bar chart comparing top SHAP features vs. top GNNExplainer substructures.
 2. Save figures as PNG files with high resolution.

- [X] T033 [P] [US3] Write unit tests for `code/analysis/explain.py` (mock models for explainability checks).

**Checkpoint**: Interpretability analysis complete; comparative report generated.

---

## Phase 6: Validation & Reporting (Priority: P3)

**Goal**: Ensure results align with Success Criteria and report findings.

- [X] T034a [US1] Documentation: Update `README.md` with "Data Pipeline Usage" section. **Content**: Add section `## Data Pipeline` with command `python code/data/download.py` and `python code/data/preprocess.py`. **Verification**: Run `grep -q "## Data Pipeline" README.md`.

- [X] T034b [US2] Documentation: Update `README.md` with "Model Training & Evaluation" section. **Content**: Add section `## Model Training` with command `python code/analysis/train.py` and `python code/analysis/evaluate.py`. **Verification**: Run `grep -q "## Model Training" README.md`.

- [X] T034c [US3] Documentation: Update `README.md` with "Interpretability Analysis" section. **Content**: Add section `## Interpretability` with command `python code/analysis/explain.py`. **Verification**: Run `grep -q "## Interpretability" README.md`.

- [X] T034d [US1, US2, US3] Documentation: Update `results/ablation_report.md` with "Experimental Setup" section. **Content**: Add section `## Experimental Setup` detailing dataset source, target variable (experimental/proxy), and split strategy. **Verification**: Run `grep -q "## Experimental Setup" results/ablation_report.md`.

- [X] T034e [US1, US2, US3] Documentation: Update `results/comparative_report.md` with "Results & Discussion" section. **Content**: Add section `## Results & Discussion` explicitly addressing SC-001 through SC-005 with measured values and power analysis context. **Verification**: Run `grep -q "## Results & Discussion" results/comparative_report.md`.

- [X] T035a [P] Run `ruff check --fix code/` to resolve all PEP8/linting violations in the code directory.

- [X] T035b [P] Run `black code/` to format all Python files according to project standards.

- [X] T036 [P] Run full pipeline end-to-end on CI to verify reproducibility and artifact generation.

- [X] T037a [P] Create `code/utils/verify_metrics.py` script and `schema/metrics.schema.json` file. **Content**: `verify_metrics.py` must load `results/metrics.json` and validate against `schema/metrics.schema.json` using `jsonschema`. The schema must include fields for `is_proxy_target`, `data_integrity_warning`, `bias_warning`, `total_training_time_hours`, `peak_memory_gb`, `rmse`, `mae`, `r2`, `p_value`, `cohen_d`, `ci_lower`, `ci_upper`. 
  **Schema Content**: 
  ```json
  {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
      "is_proxy_target": {"type": "boolean"},
      "data_integrity_warning": {"type": "boolean"},
      "bias_warning": {"type": ["string", "null"]},
      "total_training_time_hours": {"type": "number"},
      "peak_memory_gb": {"type": "number"},
      "rmse": {"type": "number"},
      "mae": {"type": "number"},
      "r2": {"type": "number"},
      "p_value": {"type": "number"},
      "cohen_d": {"type": "number"},
      "ci_lower": {"type": "number"},
      "ci_upper": {"type": "number"}
    },
    "required": ["is_proxy_target", "data_integrity_warning", "rmse", "mae", "r2", "p_value", "cohen_d", "ci_lower", "ci_upper"]
  }
  ```
  **Verification**: Run `python code/utils/verify_metrics.py` to ensure it exits with code 0.

- [X] T037 [US2, US3] Verify Success Criteria Alignment: Ensure the final report and `results/metrics.json` explicitly state the measured outcomes against the defined Success Criteria for US2 (SC-001, SC-002, SC-002b, SC-002c, SC-004, SC-005) and US3 (SC-003). **Verification**: Run `python code/utils/verify_metrics.py`.

- [X] T038 [US2, US3] Verify Success Criteria Alignment: Ensure the final report and `results/metrics.json` explicitly state the measured outcomes against the defined Success Criteria for US2 (SC-001, SC-002, SC-002b, SC-002c, SC-004, SC-005) and US3 (SC-003).

---

## Success Criteria (Updated)

- **SC-001**: The reduction in RMSE of the GNN model compared to the Random Forest baseline (trained on standard descriptors) is measured against the null hypothesis of no difference (See FR-007).
- **SC-002**: The statistical significance of the performance gap is measured against a conventional significance threshold using a paired t-test (p-value).
- **SC-002b**: The magnitude of the performance gap is measured by calculating Cohen's d (effect size) for the difference in prediction errors.
- **SC-002c**: The precision of the performance gap estimate is measured by calculating the Confidence Interval for the mean difference.
- **SC-003**: The interpretability of the GNN is measured by the ability to rank specific topological substructures by GNNExplainer, compared to the ranked standard descriptors from SHAP.
- **SC-004**: The computational feasibility is measured by the total training time (must be ≤ 6 hours) and peak memory usage (must be ≤ 7 GB) on a CPU-only runner.
- **SC-005**: The data integrity is measured by the percentage of valid molecules retained after preprocessing.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires US1 data outputs
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires US2 model outputs

### Explicit Task Dependencies

- **T013**: Performs flexible fetch and column inspection.
- **T013b**: Depends on **T013** to determine target availability and enforce strict failure if missing.
- **T014a/T014b**: Depends on **T013b** (Target Validation).
- **T017**: Depends on **T013b** (Target Validation), **T014a/T014b** (Preprocessing) to ensure split logic adapts to data availability.
- **T022**: Depends on **T017** (Data Split) to ensure training/test sets are available.
- **T023 (Ablation Training)**: Depends on **T014b** (Unified Data Generation), **T017** (Data Splits), and **T022** (Training).
- **T023b (Ablation Reporting)**: Depends on **T023** and **T024**.
- **T024**: Depends on **T022** (Training) to ensure models are trained before evaluation.
- **T025**: Depends on **T021** (Standard RF Training) and **T024** (Evaluation). **Note**: T023b is NOT required.
- **T025c**: Depends on **T023** (Ablation Training) and **T024** (Evaluation).
- **T025b**: Depends on **T025** (T-test) and **T024** (prediction errors for sample size).
- **T031 (Mapping Logic)**: Depends on **T029**, **T030**, and **T024** (Model Evaluation).
- **T031b (Report Generation)**: Depends on **T031**, **T023b** (Ablation Reporting) to ensure ablation results are included.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- **Note**: T013 and T013b are sequential and cannot be parallelized with T014a. T025b is strictly sequential after T025. T025c can run in parallel with T025b.
- **Note**: T013 is marked [P] in the list but is strictly sequential with T013b and T014a. The [P] tag applies only to tasks within Phase 1 (Setup) or tasks with no inter-dependencies.

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

---

## Revision Concerns & New Tasks

The following tasks address specific reviewer concerns regarding data sourcing, streaming capabilities, and strict adherence to the "Real Data Only" constitution.

- [ ] T039 [US1] Implement `code/data/download.py` with **Streaming Support** for large datasets:
 1. **Prerequisite**: Depends on T013 (Source Fetch).
 2. **Size Check**: Before fetching, use `datasets.get_dataset_size()` or the dataset's `dataset_size` metadata field to determine if the dataset size exceeds 7GB (or the configured `max_memory_gb`).
 3. **Streaming Logic**: If the detected dataset size exceeds 7GB, implement `datasets.load_dataset(name, streaming=True)` to iterate over the dataset in chunks.
 4. **Chunked Processing**: Accumulate statistics (counts, means) online without loading the full dataset into RAM. Do NOT attempt to materialize the full DataFrame.
 5. **Verification**: Ensure the pipeline runs without OOM errors on a sample of [deferred] rows from a large stream. Log "Streaming Mode: Active" to `results/metrics.json`.

- [ ] T040 [US1] Implement **Strict Real Data Loader** with **NO Synthetic Fallback**:
 1. **Prerequisite**: Depends on T013 (Source Fetch).
 2. **Remove Fallbacks**: Ensure `code/data/download.py` contains NO `try/except` blocks that fall back to `generate_synthetic_*()`, `mock_*()`, or random data generation if a real fetch fails.
 3. **Fail Loudly**: If a real fetch fails (network error, missing column, invalid URL), the script MUST raise a `RuntimeError` with a clear message indicating the specific verified source that failed.
 4. **Verification**: Run `pytest tests/unit/test_download.py::test_no_synthetic_fallback` which asserts that no synthetic generation functions are called in the `DataLoader` class when a fetch fails.

- [ ] T041 [US1] Implement **Verified Real Data Source Injection** Handling:
 1. **Prerequisite**: Depends on T040 (Strict Loader).
 2. **Injection Check**: Before attempting any fetch, check for an environment variable or config flag `VERIFIED_DATA_SOURCE` (e.g., `package_name::dataset_id::access_recipe`).
 3. **Adoption**: If `VERIFIED_DATA_SOURCE` is present, the loader MUST use that exact package/recipe as the *only* source, bypassing the list of verified IDs in T013.
 4. **Verification**: Run `python -c "import os; os.environ['VERIFIED_DATA_SOURCE']='test_pkg::test_ds'; import code.data.download as dl; assert dl.DataLoader().source == 'test_pkg::test_ds'"`.

- [ ] T042 [US2] Implement **CPU-First Feasibility Check** for GNN:
 1. **Prerequisite**: Depends on T020 (GNN Implementation).
 2. **Feasibility Logic**: Before training, perform a dry-run forward pass on a small batch (e.g., 10 molecules) to estimate memory usage.
 3. **Threshold**: If the estimated memory usage > 7GB, log a warning "GNN may exceed memory limits on CPU runner" but proceed (as per CPU-first rule).
 4. **GPU Escape Hatch**: Do NOT task a GPU escape hatch here unless the dry-run explicitly fails with a CUDA error (which implies the runner has a GPU but the code requested CUDA). Since we are CPU-first, the default is CPU. If the project *requires* GPU (e.g., model too large for CPU), this task should flag it for manual review rather than auto-switching.
 5. **Verification**: Ensure `results/metrics.json` contains `cpu_feasibility_check: "passed"` or `"warning"`.

- [ ] T043 [US1] Implement **Bias Check Validation** (FR-013) with **Correlation Threshold**:
 1. **Prerequisite**: Depends on T016 (Bias Check).
 2. **Threshold Logic**: Ensure the correlation check uses the `validation.bias_threshold` from `config.yaml` (default 0.85).
 3. **Flagging**: If |r| > threshold, set `bias_warning: "potentially confounded"` in `results/metrics.json` and generate a specific section in `results/comparative_report.md` titled "Bias Warning".
 4. **Verification**: Run `python -c "import json; d=json.load(open('results/metrics.json')); assert 'bias_warning' in d or d.get('bias_warning') is None"`.

- [ ] T044 [US1] Implement **Data Retention Threshold** (FR-011) with **Warning vs Failure**:
 1. **Prerequisite**: Depends on T015 (Invalid SMILES Handling).
 2. **Threshold Logic**: If valid molecule retention < 95%, log a warning and set `data_integrity_warning: true` in `results/metrics.json` AND **trigger `SystemExit(1)`**.
 3. **No Continue**: Ensure the pipeline DOES trigger `SystemExit(1)` if retention is < 95%, halting the study (per FR-011 and SC-005).
 4. **Verification**: Run `python -c "import json; d=json.load(open('results/metrics.json')); assert d.get('data_integrity_warning') == True"`.

- [ ] T045 [US1] Implement **Stratification Column Discovery** (FR-003) with **Fallback**:
 1. **Prerequisite**: Depends on T017 (Split Logic).
 2. **Discovery**: Check for `polymer_type`, `membrane_type`, `material` in that order.
 3. **Fallback**: If none found, use random split and log "Stratification column missing. Fallback to random split."
 4. **Verification**: Run `grep -q "Stratification column missing" results/stratification_report.md` (if no column found) or verify the correct column is listed.

# Analyze report (current R1 output — drives the panel concerns)

- (severity: CRITICAL) (tasks.md:T013b vs spec.md:FR-003/FR-004 & plan.md:Phase 0) — tasks.md T013b enforces a hard `RuntimeError` if experimental permeability data is missing, directly contradicting the spec's "Assumptions" (which allow fallbacks for small datasets) and the plan's explicit "Proxy Mode" strategy (Phase 0, Step 2) to use calculated logP if experimental data is absent; this creates an implementation deadlock where the pipeline cannot run if the primary assumption (≥200 experimental samples) fails.

- (severity: HIGH) (tasks.md:T015/T044 vs spec.md:FR-011) — tasks.md T015 and T044 explicitly instruct the system to log a warning and continue if molecule retention falls below [deferred] (setting `data_integrity_warning: true`), whereas spec.md FR-011 mandates that the pipeline **must halt and report the cause** if retention falls below this threshold; this violates the spec's data integrity requirement and creates a "pass" state for a condition the spec defines as a failure.

- (severity: HIGH) (tasks.md:T025 vs spec.md:FR-007 & plan.md:Phase 2) — tasks.md T025 mandates a paired t-test between the GNN and the **RF-Ablation** model (trained on graph-derived features only), while spec.md FR-007 and plan.md Phase 2 explicitly require the t-test to be performed against the **Random Forest baseline** (trained on standard descriptors) to assess the GNN's improvement over the standard non-topological baseline; this shifts the statistical comparison to a different hypothesis (GNN vs. Topology-only RF) than the one defined in the requirements.

- (severity: MEDIUM) (tasks.md:T014b vs spec.md:FR-002) — tasks.md T014b requires generating a *separate* file `data/processed/graph_features.csv` containing only flattened graph topology features and explicitly excluding standard descriptors, while spec.md FR-002 and User Story 1 imply the primary processed dataset should contain *both* graph representations and standard descriptors for the baseline model; the plan to split these into distinct files introduces a data schema divergence not authorized in the spec's "Key Entities" or "Requirements".

- (severity: MEDIUM) (tasks.md:T003a vs spec.md:FR-013 & plan.md:Phase 1) — tasks.md T003a defines a config key `validation.stratification_threshold` to control "FR-003 stratification check," but spec.md FR-003 defines the constraint as an "absolute percentage point difference < 5%" (a fixed logic requirement), not a configurable threshold; furthermore, the plan.md Phase 1 Step 3 defines the bias threshold as 0.85, yet T003a conflates stratification logic with a "significance threshold" in its description, creating ambiguity in the configuration schema that does not map cleanly to the spec's fixed constraints.

- (severity: LOW) (tasks.md:T025b vs spec.md:SC-006) — tasks.md T025b introduces a new Success Criterion "SC-006" (statistical power) and mandates its calculation, but spec.md **only** defines SC-001 through SC-005; while the plan.md Phase 2 mentions power analysis, the spec does not list it as a measurable success criterion, creating an orphan success criterion in the tasks that is not grounded in the approved spec.

- (severity: LOW) (tasks.md:T037 vs spec.md:SC-007) — tasks.md T037 and the "Success Criteria" section in tasks.md list "SC-007" (incremental value of topology) as a measured outcome, but this criterion is absent from the spec.md "Success Criteria" section; SC-007 appears to be derived from the plan's ablation study requirements but was never formally added to the spec's list of measurable outcomes, creating a traceability gap.

# Prior reviews (per-round history; outstanding concerns)

(no prior reviews)

# Panel concerns to address (R1 output)

- [concern coverage-1818dd70] severity=requirement reviewer=coverage location=tasks.md:T013b
  Task T013b enforces a hard RuntimeError if experimental permeability data is missing. This contradicts the Plan (Phase 0, Step 2) which explicitly mandates a 'Proxy Mode' fallback to calculated logP if experimental data is absent. The spec (Assumptions) also allows for fallbacks. This task blocks the implementation of the approved plan strategy.
- [concern coverage-9a28d717] severity=requirement reviewer=coverage location=tasks.md:T015, T044
  Tasks T015 and T044 instruct the system to log a warning and continue if molecule retention < 95%. This directly contradicts Spec FR-011 which states: 'if retention falls below this threshold, the pipeline must halt and report the cause'. The task implements a 'pass' state for a requirement-defined failure condition.
- [concern coverage-6ef914c7] severity=requirement reviewer=coverage location=tasks.md:T025
  Task T025 mandates a paired t-test between GNN and the RF-Ablation model (graph-derived features only). Spec FR-007 and Plan Phase 2 explicitly require the t-test to be performed against the Random Forest baseline (trained on standard descriptors) to assess the GNN's improvement over the standard non-topological baseline. This task tests a different hypothesis than the spec requires.
- [concern coverage-14fbb1ca] severity=requirement reviewer=coverage location=tasks.md:T014b
  Task T014b requires generating a separate file 'graph_features.csv' excluding standard descriptors. Spec FR-002 and US-1 imply the primary processed dataset should contain both graph representations and standard descriptors. The plan to split these into distinct files introduces a data schema divergence not authorized in the spec's 'Key Entities' or 'Requirements'.
- [concern coverage-724042c8] severity=requirement reviewer=coverage location=tasks.md:T003a
  Task T003a defines a config key 'validation.stratification_threshold' to control FR-003. Spec FR-003 defines the constraint as a fixed logic requirement ('absolute percentage point difference < 5%'), not a configurable threshold. This task introduces a configuration element that misrepresents the spec's fixed constraint.
- [concern coverage-d2891f5d] severity=writing reviewer=coverage location=tasks.md:Success Criteria
  The tasks.md 'Success Criteria' section lists SC-006 (statistical power) and SC-007 (incremental value of topology). These IDs are not present in the spec.md 'Success Criteria' section (which only lists SC-001 to SC-005). While the plan mentions these concepts, the tasks should not define new Success Criterion IDs that do not exist in the spec.
- [concern ordering-d9248d0c] severity=requirement reviewer=ordering location=tasks.md:T013b
  T013b enforces a hard `RuntimeError` if experimental permeability data is missing, blocking the pipeline. However, plan.md Phase 0 Step 2 explicitly mandates a 'Proxy Mode' fallback to calculated logP if experimental data is absent. T013b must be reordered/modified to allow the fallback flow before halting, otherwise the consumer (T014a) cannot execute if the primary assumption fails.
- [concern ordering-51e735b0] severity=requirement reviewer=ordering location=tasks.md:T015, T044
  T015 and T044 instruct the pipeline to log a warning and continue if molecule retention < 95%. This violates the data-flow dependency on spec.md FR-011, which mandates the pipeline MUST halt (SystemExit) if retention falls below this threshold. The task order implies a 'success' state for a condition defined as a failure in the spec, breaking the artifact-flow contract.
- [concern ordering-b60f2b26] severity=requirement reviewer=ordering location=tasks.md:T025
  T025 performs a t-test between GNN and RF-Ablation (graph features only). However, spec.md FR-007 and plan.md Phase 2 explicitly require the t-test to be against the Random Forest baseline (standard descriptors) to assess the GNN's improvement over the standard non-topological baseline. The task order implements the wrong statistical comparison, consuming the wrong artifact (Ablation model) for the primary hypothesis test.
- [concern ordering-a7348190] severity=requirement reviewer=ordering location=tasks.md:T014b
  T014b generates a separate `graph_features.csv` excluding standard descriptors. This creates a data-flow split not authorized in spec.md FR-002 (which implies a unified processed dataset) or the plan. The downstream tasks (T023, T025) depend on this split file, but the spec's 'Key Entities' do not define this separate artifact, creating a schema dependency mismatch.
- [concern ordering-b5339a78] severity=requirement reviewer=ordering location=tasks.md:T003a
  T003a defines `validation.stratification_threshold` to control FR-003. However, spec.md FR-003 defines the constraint as a fixed logic requirement ('absolute percentage point difference < 5%'), not a configurable threshold. This task introduces a configuration dependency that contradicts the fixed logic in the spec, potentially allowing invalid stratification if the config is misaligned.
- [concern ordering-a4a8d4c9] severity=requirement reviewer=ordering location=tasks.md:T037, T038
  T037 and T038 verify alignment with 'SC-007' (incremental value of topology). This criterion is absent from spec.md Success Criteria (only SC-001 to SC-005 exist). The tasks depend on a non-existent upstream artifact (SC-007), creating a broken dependency chain.
- [concern executability-1c131879] severity=requirement reviewer=executability location=tasks.md:T013
  Task T013 instructs the implementer to 'Iterate through a list of verified dataset IDs (e.g., huggingface.co/datasets/chembl/chembl_v30...)' but does not provide the actual list of IDs or the logic to determine which are 'verified'. The task assumes context (the list of valid datasets) that is not present in the tasks.md, spec.md, or plan.md. An implementer cannot execute this deterministically without guessing the dataset IDs.
- [concern executability-45b3b008] severity=requirement reviewer=executability location=tasks.md:T013b
  Task T013b requires checking for 'experimental permeability columns (e.g., logP_exp, permeability_coefficient)'. The task does not define the exhaustive list of acceptable column names or the logic to map them. Without a defined schema or explicit list, the implementer cannot deterministically decide if a column qualifies as 'experimental permeability' versus a proxy, leading to non-deterministic execution.
- [concern executability-45f30cbb] severity=requirement reviewer=executability location=tasks.md:T014a
  Task T014a instructs to 'compute standard descriptors (MW, logP, TPSA, etc.)'. The term 'etc.' is ambiguous. The task does not specify the exact set of descriptors to compute, nor does it reference a specific RDKit function or configuration file that defines this set. This makes the deliverable (the feature vector) non-deterministic across different implementers.
- [concern executability-3f879d15] severity=requirement reviewer=executability location=tasks.md:T016
  Task T016 requires calculating 'correlation between input descriptors and the target variable' but does not specify which correlation metric to use (Pearson, Spearman, Kendall) or how to handle multivariate correlations (e.g., max correlation across all descriptors vs. average). This ambiguity prevents deterministic implementation of the bias check logic.
- [concern executability-103b4801] severity=requirement reviewer=executability location=tasks.md:T025
  Task T025 requires calculating 'Cohen's d' and '95% Confidence Intervals' but does not specify the formula or library function to use for these calculations (e.g., pooled standard deviation method vs. other variants). While standard, the lack of explicit definition in the task description creates a risk of implementation variance, especially for the CI calculation which has multiple methods.
- [concern executability-c62b849b] severity=writing reviewer=executability location=tasks.md:T003a
  Task T003a defines a config key `validation.stratification_threshold` but describes it as 'The specific value to remove/generalize is the significance threshold'. This description is confusing and does not clearly map to the functional requirement FR-003 (stratification by polymer type). The task description needs editing to clarify what this threshold actually controls (e.g., minimum class size for stratification) to be executable.
- [concern executability-54e4c6a1] severity=writing reviewer=executability location=tasks.md:T037a
  Task T037a requires creating `schema/metrics.schema.json` but does not provide the schema content or a reference to where it should be defined. The task assumes the implementer knows the exact JSON schema structure for `results/metrics.json` (which includes fields from T013b, T015, T022, T024, T025, etc.). Without the schema definition or a reference to a contract, the task is not self-contained.
- [concern executability-d828c2e9] severity=writing reviewer=executability location=tasks.md:T039
  Task T039 requires implementing streaming logic if 'dataset size exceeds 7GB'. The task does not specify how the implementer is to determine the dataset size *before* fetching it (e.,g., via a metadata API call, a config file, or a heuristic). The condition for triggering streaming is not executable without a defined method to check the size.
- [concern constraint_preservation-1b069d2c] severity=requirement reviewer=constraint_preservation location=tasks.md:T013b
  T013b enforces a hard `RuntimeError` if experimental permeability data is missing, directly contradicting the plan.md (Phase 0, Step 2) which explicitly mandates a 'Proxy Mode' switch to calculated logP if experimental data is absent. This task creates an implementation deadlock that violates the approved fallback strategy.
- [concern constraint_preservation-4d960bf7] severity=requirement reviewer=constraint_preservation location=tasks.md:T015, T044
 T015 and T044 instruct the system to log a warning and continue if molecule retention falls below [deferred], whereas spec.md FR-011 mandates that the pipeline 'must halt and report the cause' if retention falls below this threshold. This silently weakens a hard constraint into a soft warning.
- [concern constraint_preservation-001ae5d2] severity=requirement reviewer=constraint_preservation location=tasks.md:T025
  T025 mandates a paired t-test between the GNN and the RF-Ablation model (trained on graph-derived features only). However, spec.md FR-007 and plan.md Phase 2 explicitly require the t-test to be performed against the Random Forest baseline (trained on standard descriptors) to assess the GNN's improvement over the standard non-topological baseline. This shifts the statistical hypothesis.
- [concern constraint_preservation-1a5120d5] severity=requirement reviewer=constraint_preservation location=tasks.md:T003a
  T003a defines a config key `validation.stratification_threshold` to control 'FR-003 stratification check,' but spec.md FR-003 defines the constraint as a fixed logic requirement ('absolute percentage point difference < 5%'), not a configurable threshold. This introduces a silent drift from a fixed spec constraint to a tunable parameter.
- [concern constraint_preservation-b3d4d56d] severity=requirement reviewer=constraint_preservation location=tasks.md:T014b
  T014b requires generating a *separate* file `data/processed/graph_features.csv` explicitly excluding standard descriptors. Spec.md FR-002 and User Story 1 imply the primary processed dataset should contain *both* graph representations and standard descriptors. This splits the data schema in a way not authorized by the spec's 'Key Entities'.
- [concern constraint_preservation-7418a392] severity=requirement reviewer=constraint_preservation location=tasks.md:Success Criteria section
  The tasks.md lists 'SC-007' (incremental value of topology) as a measured outcome, but this criterion is absent from spec.md's 'Success Criteria' section (which only lists SC-001 through SC-005). This introduces a new success criterion not grounded in the approved spec.

# Recent reviewer / personality comments

(no recent comments)