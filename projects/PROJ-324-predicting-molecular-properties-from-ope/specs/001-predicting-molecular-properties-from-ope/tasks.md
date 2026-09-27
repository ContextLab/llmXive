---
description: "Task list template for feature implementation"
---

# Tasks: Predicting Molecular Properties from Open Babel Fingerprints with Random Forests

**Input**: Design documents from `/specs/001-predicting-molecular-properties-from-ope/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

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

**Purpose**: Project initialization, linting, and performance configuration.

- [X] T001 Create `projects/PROJ-324-predicting-molecular-properties-from-ope/` directory structure including `code/`, `tests/`, `data/raw`, `data/processed`, `data/derived` subdirectories
- [X] T002 Initialize Python 3.10+ project with `requirements.txt` (rdkit, scikit-learn, shap, pandas, numpy, datasets, requests, obabel-wrapper)
- [X] T003 [P] **Configure linting and formatting**: Implement `pyproject.toml` (Black config) and `.ruff.toml` (Ruff config) at repository root. **Requirements**:
 1. `pyproject.toml`: Set `target-version = "py310"`, `line-length = 88`.
 2. `.ruff.toml`: Set `select = ["E", "F", "W", "D"]`, `ignore = ["D100", "D104"]`.
 3. Verify configuration by running `ruff check code/` and `black --check code/`.
 *Dependency: None.*

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes data download, preprocessing, critical train/test split, and configuration.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create base `code/__init__.py` and utility modules for logging and seed management
- [X] T008 [P] [US1] **Data Download**: Implement `code/data/download.py` using **PubChemPy** to fetch a diverse dataset of molecules with SMILES and experimental logP, solubility, boiling point. **CRITICAL**: This task supersedes any reference to `molecule-net` or GitHub URLs. Use `pubchempy.get_compounds` or `pubchempy.get_cids` to fetch data. Ensure real data only. **Target**: Fetch [deferred] CIDs with a query: "molecular weight > 200 AND < 500". **Output**: `data/raw/pubchem_raw.csv` with columns: `smiles`, `property_name`, `value`, `source_type` (Experimental/Computed).
- [X] T009 [P] [US1] Implement `code/data/preprocess.py` to filter for **high-confidence measurements**. **Logic**:
 1. Exclude entries where `confidence_score < 0.8` (if available) or where target properties (logP, solubility, boiling point) are missing.
 2. **Explicitly check for physical covariates**: Detect missing pH, temperature, and pressure fields in the source data. If these fields are absent, log them as "Missing" in the report. Do NOT conflate missing metadata flags with missing physical covariates.
 3. **Calculate Experimental Ratio**: Compute the ratio of 'Experimental' entries to total entries. If ratio < 0.5, set a flag `experimental_threshold_failed = True` and log the exact percentage to `data/derived/data_quality_report.csv`. This flag will trigger the fallback analysis in T021.2.
 **Schema**: `data/derived/data_quality_report.csv` must include columns: `smiles`, `exclusion_reason`, `missing_covariate_list` (list of missing physical fields), `experimental_flag`, `experimental_ratio`.
- [X] T010 [P] [US1] **Define MaxMin Strategy**: Implement `code/data/preprocess.py::define_maxmin_strategy` to define the algorithm to select a diverse subset (Tanimoto < 0.7) from the raw fetched data. **Constraint**: **Target: a substantial number of molecules (adaptive)**. The algorithm must select the maximum subset satisfying the diversity constraint OR the full set if <5000 exist, OR a larger set if resource telemetry (RAM/CPU) permits. **Method**: Use **RDKit's `MaxMinPicker`** to execute the selection deterministically. The task must check available RAM/CPU using `psutil.virtual_memory().available` (threshold: <6GB RAM or <2 cores) and adjust the target count accordingly. **Dependency**: Must wait for T009 completion.
- [X] T010.1 [US1] **Execute MaxMin Sampling**: Implement `code/data/preprocess.py::execute_maxmin_sampling` to **execute** the diversity filtering using the strategy defined in T010, producing the final diverse dataset and generating the `data/derived/data_quality_report.csv`. **Constraint**: Target: ~5000 molecules (adaptive: stop when N=5000 OR Tanimoto < 0.7 for all pairs OR time > 45 mins). **Output**: `data/derived/diverse_subset.csv`. If the dataset is <5000, the task completes but the final report (T029.1) must flag the reduced statistical power. **Critical Check**: Re-run the experimental ratio calculation from T009 on the final subset. If ratio < 0.5, set `experimental_threshold_failed = True` and **halt the pipeline** for fallback analysis. **Dependency**: T009, T010.
- [X] T011.5 [US1/US2] **Split Dataset**: Implement `code/data/preprocess.py::split_dataset` to **split** the diverse dataset into a training set and a strictly held-out test set. **Logic**:
 1. Perform a random, stratified split (stratify by `source_type`) with a fixed seed.
 2. Target split: a majority for training, a minority for testing.
 3. Output `data/derived/train_set.csv` and `data/derived/test_set.csv`.
 **Dependency**: Must wait for T010.1 completion. **Hard Block**: T014.5, T019.1, T020, T021 cannot run until T011.5 is complete.
- [X] T031 [P] [US1/US2] Enhance `code/data/download.py` to explicitly document the **experimental source**, **measurement conditions** (e.g., temperature, pH if available), and **source confidence** in the dataset metadata (`data/raw/dataset_metadata.json`). **CRITICAL**: Perform a runtime schema check for the presence of `measurement_uncertainty` and `quantity_of_substance` fields. If absent, the code MUST derive and record `"measurement_uncertainty_status": "Not Available in Source"` and `"quantity_of_substance_status": "Not Available in Source"` based on the actual fetched schema. This task MUST produce `data/raw/dataset_metadata.json` with the following schema:
 ```json
 {
 "source": "PubChem",
 "query_parameters": {...},
 "measurement_uncertainty_status": "Available" | "Not Available in Source",
 "quantity_of_substance_status": "Available" | "Not Available in Source",
 "experimental_ratio": 0.0-1.0
 }
 ```
 **Dependency**: Must wait for T008 completion. **Note**: If fields are missing, the task is considered COMPLETE (not failed) upon generating this metadata file. **Parallel**: Parallel to other Phase 2 tasks, but strictly sequential to T008.
- [X] T030.1 [P] [US3] **Create Rules File**: Implement `code/data/rules.py` to define and export the required SMARTS patterns (hydroxyl, carbonyl, aromatic, etc.) as a list of dictionaries. **Schema**: Each dict must have keys: `name` (str), `smarts` (str), `description` (str). **Example**: `[{"name": "hydroxyl", "smarts": "[OX2H]", "description": "Hydroxyl group"}]`. **Dependency**: None.
- [X] T036 [P] **Performance Configuration**: Implement specific runtime constraints in `code/utils/config.py`. **Requirements**:
 1. Run a preliminary grid search to determine the optimal `MAX_DEPTH` (<=15) for the Random Forest model on a **sample of 100 molecules** from the training set (T011.5).
 2. **Optimize metric**: MAE.
 3. **Hard Timeout**: 30 minutes. If exceeded, default to `MAX_DEPTH=10`.
 4. Configure `joblib` parallel backend for fingerprint generation with `n_jobs=-1` but `max_memory=6GB`.
 5. Implement a hard timeout check for `obabel` subprocess (max a limited duration per run) to ensure the full pipeline completes within the -hour window (Constitution VII) and targets the research question.
 **Dependency**: Must be completed after T011.5 (Split) and before T019/T020.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel. **Note**: T011.5 (Split) must be completed before T019 (Fingerprints) to ensure valid data separation.

---

## Phase 3: User Story 1 - Baseline Error Quantification (Priority: P1) 🎯 MVP

**Goal**: Generate a baseline prediction for logP, solubility, and boiling point using Random Forests and evaluate performance via k-fold cross-validation on the **held-out test set**.

**Independent Test**: Can be fully tested by running the Crippen's additive fragment algorithm on the provided dataset and outputting a CSV of predicted vs. experimental values with a calculated Mean Absolute Error (MAE).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T012 [P] [US1] Contract test for data schema validation in `tests/contract/test_data_schema.py`
- [X] T013 [P] [US1] Unit test for Crippen's atomic contribution calculation in `tests/unit/test_crippen.py`

### Implementation for User Story 1

- [X] T014a [US1] **Generate Baseline Features (Raw)**: Implement `code/models/baseline.py::compute_crippen_contributions` to compute Crippen's atomic contributions for **ALL molecules in the full diverse dataset** (both training and test sets). **Schema**: `smiles`, `property_name`, `predicted_value`. **Algorithm**: Use standard Crippen atomic contributions (per Plan).
- [X] T014b [US1] **Impute Undefined Atoms**: Implement `code/models/baseline.py::impute_undefined_atoms` to handle undefined atoms by setting their predicted values to the mean of the training set for the corresponding property. **Dependency**: T014a and T011.5.
- [X] T014.5 [US1] **Extract Test Set Predictions**: Implement `code/models/baseline.py::extract_test_predictions` to **extract** the test set predictions from the full dataset output of T014b, saving specifically to `data/derived/baseline_test_predictions.csv` for use in the final statistical test (T021.1). **Logic**:
 1. Load `data/derived/test_set.csv` (from T011.5).
 2. Filter T014b output for these SMILES.
 3. Merge with experimental labels from `data/derived/test_set.csv`.
 4. Output `data/derived/baseline_test_predictions.csv` with columns: `smiles`, `property_name`, `experimental_value`, `predicted_value`, `residual`.
 **Dependency**: **Hard Block**: Must wait for T011.5, T014a, and T014b.
- [X] T015 [US1] **Calculate Baseline Metrics**: Implement `code/analysis/stats.py::calculate_baseline_metrics` to calculate MAE/RMSE for baseline predictions **on the held-out test set** (consuming `baseline_test_predictions.csv` from T014.5) and generate residual distribution plots (`data/derived/baseline_residuals.png`). **Dependency**: **Hard Block**: Must wait for T014.5.
- [X] T016.1 [US1] **Log Additive Failure Magnitude**: Implement `code/analysis/stats.py::log_additive_failure` to calculate and log the mean absolute error of the baseline model. **Output**: Append to `data/derived/additive_failure_log.txt`.
- [X] T016.2 [US1] **Generate Failure Report**: Implement `code/analysis/stats.py::generate_additive_failure_report` to generate a summary report of the baseline failure magnitude. **Output**: `data/derived/additive_failure_report.md`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently, establishing the additive ground truth.

---

## Phase 4: User Story 2 - Non-Linear Model Training and Validation (Priority: P2)

**Goal**: Train Random Forest regressors using Open Babel fingerprints and evaluate performance via k-fold cross-validation on the **training set**, then evaluate on the **held-out test set** to quantify improvement over the additive baseline.

**Independent Test**: Can be fully tested by training the Random Forest model, performing k-fold cross-validation, and reporting the RMSE and MAE, comparing them numerically to the P1 baseline metrics.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Contract test for fingerprint generation in `tests/contract/test_fingerprint_schema.py`
- [X] T018 [P] [US2] Integration test for full training pipeline in `tests/integration/test_rf_pipeline.py`

### Implementation for User Story 2

- [X] T019 [US2] **Generate Fingerprints (Full Set)**: Implement `code/data/fingerprint.py::generate_fingerprints` to generate Open Babel fingerprints (MACCS, ECFP4, FP2) by **invoking the `obabel` command-line tool via subprocess** (per FR-003). **Execution Logic**:
 1. Generate ECFP4, MACCS, and FP2 for **all molecules** in the **full diverse dataset** (both training and test sets) to prevent data leakage.
 2. **Command**: Use `obabel -i smiles -o txt -xf ECFP4`, `obabel -i smiles -o txt -xf MACCS`, `obabel -i smiles -o txt -xf FP2`.
 3. **Error Handling**: If `obabel` fails to complete within the time limit, the script MUST exit with code 1 and log "Partial progress saved" to `data/derived/fingerprint_log.txt`. No silent fallback.
 4. **Output**: `data/processed/full_fingerprints.csv`. *Dependency: Must wait for T011.5 completion.*
- [X] T019.1 [US2] **Split Fingerprints**: Implement `code/data/fingerprint.py::split_fingerprints` to **split** the full fingerprint array (T019) into training and test sets based on the SMILES lists from T011.5. **Output**: `data/processed/train_fingerprints.csv` and `data/processed/test_fingerprints.csv`. **Dependency**: T019 and T011.5.
- [X] T020a [US2] **Define Nested CV Config**: Implement `code/models/random_forest.py::setup_nested_cv` to define the nested cross-validation structure (outer loop for test set, inner loop for hyperparameter tuning) to generate valid error pairs for statistical testing. **Output**: Configuration object for nested CV. **Dependency**: Must wait for T019.1.
- [X] T020b [US2] **Run Hyperparameter Tuning**: Implement `code/models/random_forest.py::run_hyperparameter_tuning` to run hyperparameter tuning on the training set. **Dependency**: T020a.
- [X] T020c [US2] **Retrain on Full Set**: Implement `code/models/random_forest.py::retrain_on_full_set` to retrain the Random Forest model on the entire training set using the best hyperparameters found during tuning.
- [X] T020d [US2] **Save Final Model**: Implement `code/models/random_forest.py::save_final_model` to save the trained model to `data/derived/final_model.pkl`.
- [X] T020.1 [US2] **Evaluate on Test Set**: Implement `code/models/random_forest.py::evaluate_on_test_set` to perform the **final model evaluation** on the **held-out test set** using the trained model (`final_model.pkl`) and save to `data/derived/rf_test_predictions.csv`. **Logic**:
 1. Load `data/derived/test_set.csv`.
 2. Load `data/processed/test_fingerprints.csv` (from T019.1).
 3. Predict and compute residuals against experimental values.
 4. Output `data/derived/rf_test_predictions.csv` with columns: `smiles`, `property_name`, `experimental_value`, `predicted_value`, `residual`.
 **Dependency**: **Hard Block**: Must wait for T011.5, T019.1, and T020d.
- [X] T021a [US2] **Check Experimental Threshold**: Implement `code/analysis/stats.py::check_experimental_threshold` to determine if the experimental data ratio is substantial (>=50%). **Dependency**: T009/T010.1.
- [X] T021.1 [US2] **Perform Wilcoxon Test**: Implement `code/analysis/stats.py::perform_wilcoxon_test` to perform paired Wilcoxon signed-rank test on absolute errors (Baseline vs. RF) using the valid error pairs from the **held-out test set** (consuming `baseline_test_predictions.csv` from T014.5 and `rf_test_predictions.csv` from T020.1). **Output**: Generate `data/derived/statistical_test_report.md` containing the p-value, effect size, and conclusion. **Dependency**: **Hard Block**: Must wait for T021a, T014.5, and T020.1.
- [X] T021.2 [US2] **Perform Model Consistency Analysis (Fallback)**: Implement `code/analysis/stats.py::perform_model_consistency_analysis` to perform the restricted analysis when experimental data <50%. **Logic**:
 1. Filter the full dataset for entries where `source_type == Computed`.
 2. Compare RF predictions vs. Crippen baseline on this filtered set.
 3. Calculate MAE/RMSE for both models on the computed subset.
 4. Generate `data/derived/model_consistency_report.md` explicitly stating the limitation: "Analysis restricted to computed data due to insufficient experimental data (<50%)."
 **Dependency**: **Hard Block**: Must wait for T021a.
- [X] T022 [US2] **Generate Comparison Plots**: Implement `code/analysis/stats.py::generate_model_comparison_plot` to generate comparison plots (Baseline vs. RF MAE/RMSE) **using the held-out test set** (or computed subset if T021.2) and save to `data/derived/model_comparison.png`. **Dependency**: **Hard Block**: Must wait for T015 and T021 (and T021.1 or T021.2).
- [X] T023 [US2] Implement `code/models/random_forest.py` to include a runtime monitor that automatically reduces dataset size or skips lower-priority fingerprints if the 6-hour limit is approached (per Edge Cases).

**Checkpoint**: At this point, User Story 1 AND 2 should both be independently functional.

---

## Phase 5: User Story 3 - Interaction Zone Mapping (Priority: P3)

**Goal**: Identify specific fingerprint bit pairs contributing to error reduction using SHAP values, map them to chemical substructures, and validate against known chemical rules (using RDKit built-ins).

**Independent Test**: Can be fully tested by generating SHAP summary plots, interaction strength heatmaps, and mapping the top interacting fingerprint bits back to chemical substructures using RDKit.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Contract test for interaction context schema in `tests/contract/test_interaction_schema.py`
- [X] T025 [P] [US3] Unit test for SHAP bit-to-substructure mapping in `tests/unit/test_shap_mapping.py`

### Implementation for User Story 3

- [X] T026 [US3] **Calculate SHAP Interaction Values**: Implement `code/analysis/explainability.py` to calculate SHAP interaction values for the trained RF model (T020) using the `final_model.pkl` artifact (FR-006). **Method**: Use `shap.TreeExplainer` with a background dataset of a randomly selected sample of molecules from the training set. **Dependency**: T020 (Model), T019.1 (Test Fingerprints).
- [X] T027 [US3] **Generate SHAP Heatmap**: Implement `code/analysis/explainability.py::generate_shap_heatmap` to generate heatmaps of the top interacting fingerprint bit pairs and save to `data/derived/shap_interactions.png`.
- [X] T029 [US3] **Map Bits to Substructures**: Implement `code/analysis/explainability.py::map_bits_to_substructures` to map the top interacting bits back to chemical substructures using RDKit, outputting `data/derived/deviation_contexts.csv` (FR-007). **Logic**:
 1. Load SMARTS patterns from `code/data/rules.py` (T030.1).
 2. **Explicitly use RDKit's GetBitInfo()** to map fingerprint bits to atom indices in SMILES.
 3. **Disambiguation**: If a bit maps to multiple atoms, select the one with the highest SHAP value. If no atoms map, mark as "unmapped".
 4. **Validation**: Verify that the SMARTS patterns in `rules.py` correspond to the bit definitions used by Open Babel (e.g., by checking bit indices against known ECFP4 definitions).
 5. Output CSV with columns: `smiles`, `bit_index`, `matched_substructure`, `interaction_strength`.
 **Dependency**: T026, T030.1.
- [X] T030 [US3] **Compute Steric Descriptors**: Implement `code/analysis/explainability.py` to cross-reference identified substructures with **RDKit's built-in functional group detection** (`rdkit.Chem.Fragments`) and **steric descriptors** (`rdkit.Chem.rdMolDescriptors` - e.g., Molecular Weight, TPSA, NumRotatableBonds) to correlate **topological proxies** for steric effects with model deviations (FR-010). **Requirement**: Explicitly compute and output steric descriptors for the molecules. **Constraint**: **DO NOT claim these are physical mechanisms**. All outputs must explicitly label these as "topological proxies" for steric effects.
- [X] T030.2 [US3] **Calculate Local Non-Additivity Index (LNAI)**: Implement `code/analysis/explainability.py::calculate_lnai` to compute the LNAI as the correlation between RF residuals and Crippen baseline deviations, identifying specific **interaction zones** where RF outperforms the additive baseline, per Constitution Principle VI.
- [X] T029.1 [US3] **Generate Interaction Zone Map Report**: Implement `code/analysis/explainability.py::generate_interaction_zone_report` to aggregate SHAP values (T026), substructure mappings (T029), steric descriptors (T030), and LNAI (T030.2) into the final **Interaction Zone Map Report** (`data/derived/interaction_zone_map.md`). **Requirement**: Explicitly frame findings as **associational** correlations, not causal mechanisms, in the output report.

**Checkpoint**: At this point, User Stories 1, 2, and 3 should all be independently functional.

---

## Phase 6: Reviewer Concerns & Data Integrity (Revision Tasks)

**Purpose**: Address specific feedback from Marie Curie (simulated) and Rosalind Franklin (simulated) regarding experimental validation, measurement uncertainty, and conformational limitations.

- [X] T033 [P] [US3] Implement `code/analysis/explainability.py` to generate a "Conformational Limitation Report" that identifies molecules where 2D topology (fingerprints) likely fails to capture solution-phase conformational ensembles. **Method**: Use a topological proxy heuristic (specifically `NumRotatableBonds > 10` via RDKit) to flag potential 3D failures, addressing Rosalind Franklin's concern on static vs. dynamic structures. **Output**: `data/derived/conformational_limitations.csv` with columns: `smiles`, `num_rotatable_bonds`, `deviation_magnitude`.
- [X] T057 [P] [US1/US2/US3] **Comprehensive Validation Audit & Conformational Analysis**: Implement `code/analysis/stats.py` and `code/analysis/explainability.py` to generate a unified **Validation Protocol Audit** and **Conformational Sensitivity Analysis**. **Requirements**:
 1. **Data Provenance**: Iterate through the final dataset and create a structured log (`data/derived/validation_audit.md`) that explicitly maps each molecule's property values to their specific source record.
 2. **Uncertainty Handling**: If uncertainty data is missing (as detected in T031), the audit MUST explicitly record "Uncertainty: Not Reported in Source" for those entries. This is a valid state.
 3. **Conformational Proxy**: Implement `estimate_conformational_impact` to generate a proxy metric for solution-phase conformational ensembles using `NumRotatableBonds` and `TPSA`. Identify molecules where 2D fingerprints likely fail and report the deviation magnitude for this subset.
 4. **Output**: `data/derived/validation_audit.md` and `data/derived/conformational_sensitivity_report.md`.
 **Dependency**: T031, T011.5, T014.5, T020.1, T033.

**Checkpoint**: At this point, all reviewer concerns regarding validation and conformational limitations are addressed.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T037 [P] **Code Quality**: Add docstrings to all public functions in `code/` (including `models/`, `analysis/`, and `data/`).
- [X] T038 [P] **Documentation Updates**: Update `docs/quickstart.md` and `docs/research.md` with final implementation details.
- [X] T041 [P] **Security Hardening**: Run `bandit -r code/` to scan for security issues.
- [X] T042 [P] **Validation**: Run `python -m pytest tests/` and `black --check code/` to ensure all tests pass and formatting is correct.