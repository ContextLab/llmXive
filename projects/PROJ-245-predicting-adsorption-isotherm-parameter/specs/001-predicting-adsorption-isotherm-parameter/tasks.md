# Tasks: Predicting Adsorption Isotherm Parameters from Molecular Features

**Input**: Design documents from `/specs/001-predicting-adsorption-isotherm-params/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `data/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project structure per `plan.md`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per `plan.md` (code/, data/, tests/, contracts/)
- [X] T002 Initialize Python project with `requirements.txt` (rdkit, scikit-learn, pandas, numpy, shap, pyyaml, pytest, datasets, huggingface_hub, psi4)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. All data processing must use real experimental data. Synthetic data is strictly prohibited.

- [X] T014z [P] [US1] **Define Descriptor Provenance Registry**: Create `docs/descriptor_provenance.md`. This task does NOT create a runtime configuration file. It MUST document the exact mathematical formulas and literature citations (DOI/URL) for Kinetic Diameter, Lennard-Jones epsilon, and Quadrupole Moment as implemented in `code/data/descriptors.py`. **CRITICAL**: This file is for provenance tracking only. **NO** values are to be stored here for runtime lookup. All runtime descriptor calculations MUST be performed dynamically by RDKit/external libs in `code/data/descriptors.py`.
- [X] T004 Define `contracts/dataset.schema.yaml` and `contracts/model_output.schema.yaml`
- [X] T008 [US1] Create base data classes/entities in `code/models/entities.py` for Adsorbate, Adsorbent, and IsothermParameter with all required attributes (molecular weight, surface area, etc.)
- [X] T009 Configure environment variable management and logging infrastructure in `code/__init__.py`
- [X] T010 [US1] Setup pytest configuration and test directory structure: Create `pytest.ini` with seed pinning and `tests/__init__.py` to enable test execution
- [ ] T014ba-1 [US1] **Implement Kinetic Diameter Calculation**: Create `code/data/descriptors.py` function `calc_kinetic_diameter`. **Logic**: 1. Check metadata column `molecular_diameter` or `kinetic_diameter`. If present, return it. 2. If missing, estimate via `d = sqrt(4 * CalcTPSA(mol) / PI)` using RDKit. **Output**: Return float or None. **Dependencies**: T014z.
- [ ] T014ba-2 [US1] **Implement Kinetic Diameter Error Handling**: Create `code/data/descriptors.py` wrapper function `safe_calc_kinetic_diameter`. **Logic**: Wrap T014ba-1 in try/except. If calculation fails or returns None, return None and log the specific molecule ID to `data/validation/missing_descriptors_report.json` with reason "Missing Kinetic Diameter Data". **Dependencies**: T014ba-1.
- [ ] T014ba-3 [US1] **Implement Kinetic Diameter Logging**: Create `code/data/descriptors.py` utility `log_missing_kinetic_diameter`. **Logic**: Append entry to `data/validation/missing_descriptors_report.json` with structure `{id, reason, timestamp}`. **Dependencies**: T014ba-2.
- [ ] T014bb-1 [US1] **Implement Lennard-Jones Energy Parameter (epsilon) Calculation**: Create `code/data/descriptors.py` function `calc_lj_epsilon`. **Logic**: 1. Check metadata columns `critical_temperature`, `Tc`, or `critical_temp`. If present, use `epsilon = 0.75 * Tc`. 2. If missing, attempt to estimate Tc using `critical_pressure` and `critical_volume` via corresponding states correlations. **Output**: Return float or None. **Dependencies**: T014z.
- [ ] T014bb-2 [US1] **Implement Lennard-Jones Error Handling**: Create `code/data/descriptors.py` wrapper function `safe_calc_lj_epsilon`. **Logic**: Wrap T014bb-1 in try/except. If estimation fails or returns None, return None and log the specific molecule ID to `data/validation/missing_descriptors_report.json` with reason "Missing Lennard-Jones Data". **Dependencies**: T014bb-1.
- [ ] T014bb-3 [US1] **Implement Lennard-Jones Logging**: Create `code/data/descriptors.py` utility `log_missing_lj_epsilon`. **Logic**: Append entry to `data/validation/missing_descriptors_report.json` with structure `{id, reason, timestamp}`. **Dependencies**: T014bb-2.
- [ ] T014bc-1 [US1] **Implement Quadrupole Moment Calculation**: Create `code/data/descriptors.py` function `calc_quadrupole_moment`. **Logic**: 1. Extract coordinates from `coordinates` column (list of floats or string). 2. If 2D data, use RDKit `EmbedMolecule` to generate 3D. 3. Use `psi4` with `b3lyp`/`def2-svp` on input coordinates (save to temporary .xyz). **Output**: Return float or None. **Dependencies**: T014z.
- [ ] T014bc-2 [US1] **Implement Quadrupole Moment Error Handling**: Create `code/data/descriptors.py` wrapper function `safe_calc_quadrupole_moment`. **Logic**: Wrap T014bc-1 in try/except. If `psi4` fails or coordinates are invalid, return None and log the specific molecule ID to `data/validation/missing_descriptors_report.json` with reason "Missing Quadrupole Data". **Dependencies**: T014bc-1.
- [ ] T014bc-3 [US1] **Implement Quadrupole Moment Logging**: Create `code/data/descriptors.py` utility `log_missing_quadrupole_moment`. **Logic**: Append entry to `data/validation/missing_descriptors_report.json` with structure `{id, reason, timestamp}`. **Dependencies**: T014bc-2.
- [ ] T014c [US1] **Implement Parameter Fitting**: Create `code/data/fitting.py` to fit Langmuir/Henry parameters from raw isotherm points (P vs V) if the source data lacks pre-fitted `langmuir_capacity` or `henry_constant` columns. Use non-linear least squares (scipy.optimize). **Output**: Append fitted values to the dataset or create a new column. **Dependency**: T060 (Streaming).
- [ ] T014d [US1] **Merge Descriptor Logs**: Create `code/data/descriptors.py` function to sequentially merge individual logs from T014ba-2, T014bb-2, T014bc-2 into a single `data/validation/missing_descriptors_report.json`. **Dependency**: T014ba-2, T014bb-2, T014bc-2.
- [ ] T060 [US1] **Implement Streaming Data Loader with Filtering**: Update `code/data/download.py` to use `datasets.load_dataset("nasa/nist-adsorption-isotherms", split="train", streaming=True)`. **Constraint**: Do NOT load the full dataset. Iterate over the streaming iterator to write chunks to `data/raw/streamed_chunk_*.parquet` or process on-the-fly. **CRITICAL**: Implement "Filter & Fit" logic (Plan Phase 1 Step 2) directly here: Filter entries to include ONLY Type I isotherms. Check column `isotherm_type` or `IsothermType` for value 'I' or 1. If the specific dataset ID is incorrect, the script MUST raise `ValueError` with the exact correct ID or a verified alternative URL. **NO** synthetic fallback permitted. **Output**: Write chunks to Parquet for merging.
- [ ] T061 [US1] **Merge Chunks**: Create `code/data/merge.py` to combine `data/raw/streamed_chunk_*.parquet` files into a single `data/raw/merged_dataset.parquet`. **Dependency**: T060.
- [ ] T061a [US1] **Generate Reference Hash**: Create `code/data/verify_real.py` to compute a checksum or sample hash of the first 100 rows of the streamed data and write it to `data/validation/reference_hash.json`. **Requirement**: This task establishes the baseline. **Dependencies**: T061.
- [ ] T061b [US1] **Verify Against Reference**: Update `code/data/verify_real.py` to compare the current data hash against the reference hash in `data/validation/reference_hash.json`. **Requirement**: If the hash mismatches, raise `DataIntegrityError`. **Dependencies**: T061a.
- [X] T043a [P] [US1] Implement `code/data/loader.py`: **Fetch & Validate**. Attempt to fetch real data from NIST/MOF-1000 using `code/data/download.py`. Validate schema. **CRITICAL**: If fetch fails, the script MUST raise a `DataFetchError` and terminate. **NO** synthetic fallback is permitted. Write `verification_log.json` with status "REAL_DATA_FETCH_FAILED" and rationale.
- [X] T045 [US2] Implement `code/models/audit.py` to perform a **Data Leakage Audit**: Before training, this script must verify that the material-level split (T020) is correct by checking the intersection of `adsorbent_structure_id` between train and test sets. If any overlap is found, it must abort training and log the specific leaking IDs to `data/audit/leakage_report.json`. **Dependencies**: T020.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Curate and Prepare the Adsorption Dataset (Priority: P1) 🎯 MVP

**Goal**: Generate a clean, normalized CSV linking molecular descriptors to isotherm parameters using real experimental data only.

**Independent Test**: Run `code/data/preprocess.py` on the real dataset and verify the output CSV contains exactly `polarizability`, `langmuir_capacity`, `henry_constant`, `surface_area` (m²/g) with no missing values.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T012 [P] [US1] Contract test for schema compliance in `tests/contract/test_dataset_schema.py`
- [X] T013 [P] [US1] Unit test for RDKit descriptor calculation in `tests/unit/test_descriptors.py`

### Implementation for User Story 1

- [ ] T015 [US1] Implement `code/data/preprocess.py` to filter Type I isotherms, remove entries with missing targets, normalize units (m²/g), and **handle missing pore volume** (FR-002, Edge Cases). **Logic**: 1. If `pore_volume` is missing, attempt imputation using mean of similar materials (clustered by `material_type` or `surface_area` bin). 2. If imputation fails or is not configured, exclude the entry and log to `data/validation/exclusion_log.json` with reason "Missing Pore Volume". **Requirement**: If exclusion count > 10%, trigger T015b (Imputation). **Dependencies**: T014a, T014ba-2, T014bb-2, T014bc-2, T014d, T061, T014c, T043a.
- [ ] T015b [US1] **Implement Imputation**: Create `code/data/imputation.py` to impute missing pore volume using the mean of similar materials (clustered by `material_type` or `surface_area` bin). **Requirement**: If triggered by T015, apply it and log to `data/validation/imputation_log.json`. **Dependencies**: T015.
- [ ] T015c [US1] **Validate Dataset Size**: Create `code/data/validate.py` to assert that the final dataset size N > 500 after T015 and T015b. **Requirement**: If N <= 500, raise `DatasetSizeError` and halt pipeline. **Dependencies**: T015, T015b.
- [ ] T016 [US1] Implement outlier detection in `code/data/preprocess.py` to flag adsorbates with identical descriptors but conflicting targets: Group by `descriptor_hash` (SHA256 of sorted tuple of all calculated descriptor values), calculate variance of target. **Threshold**: Flag if `|value - mean_group| > 3 * std_group` (3-sigma rule). **Action**: Exclude flagged entries from the final training set and log the exclusion reason. Output `data/processed/outliers.csv` with columns [material_id, descriptor_hash, target_variance, exclusion_reason] (Edge Cases); depends on T014a, T014ba-2, T014bb-2, T014bc-2, T015, T015b, T015c
- [X] T017 [US1] Update `code/main.py` orchestrator to run the full data curation pipeline (Download -> Preprocess -> Outlier Check); depends on T014a, T014ba-2, T014bb-2, T014bc-2, T060, T015, T016

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train and Evaluate Predictive Models (Priority: P2)

**Goal**: Train baseline models (Linear, RF, GB) with strict material-level splitting and evaluate performance on real data.

**Independent Test**: Run training on real data; verify that the test set contains no materials present in the training set and that metrics (R², RMSE) are logged.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output.py`
- [X] T019 [P] [US2] Integration test for material-level data splitting in `tests/integration/test_data_split.py`

### Implementation for User Story 2

- [X] T020 [US2] Implement `split_data()` in `code/models/train.py` to perform **Material-Level Split**: Group rows by `adsorbent_structure_id` (the unique crystallographic identifier or MOF-177 entry ID), then split groups, ensuring no `adsorbent_structure_id` exists in both train and test sets (FR-003). This task focuses ONLY on the splitting logic.
- [X] T021 [P] [US2] Implement `train_models()` in `code/models/train.py` to **Train Models**: Train Linear Regression, Random Forest, and Gradient Boosting models (FR-004). This task focuses ONLY on the training loop.
- [X] T022 [P] [US2] Implement `tune_hyperparameters()` in `code/models/train.py` to perform **5-fold Cross-Validation and Hyperparameter Tuning** (FR-004). This task focuses ONLY on tuning logic.
- [X] T051 [US2] **Implement Cluster-Aware Permutation Engine**: Create `code/analysis/cluster_permutation.py`. This module must implement the algorithm described in FR-007: for each feature, shuffle values *strictly within* material clusters defined by `adsorbent_structure_id`. **Explicit Logic**: Use `adsorbent_structure_id` as the cluster key, matching T020. Ensure the shuffle does not cross cluster boundaries. Add a validation check to ensure no cross-cluster leakage occurs. **Dependency**: Must run AFTER T021 (Training) to access the trained model. **Dependencies**: T020, T021.
- [X] T026 [P] [US2] **Implement Benjamini-Hochberg FDR Correction**: Create `code/models/evaluate.py` function to apply Benjamini-Hochberg correction to a list of p-values. Output adjusted p-values (q-values) (FR-006).
- [X] T052 [US2] **Integrate Cluster Permutation & FDR**: Update `code/models/evaluate.py` to call `cluster_permutation.py` (T051) and consume the raw p-values, then apply the FDR correction logic from T026. Generate and persist `data/results/permutation_pvalues.json` containing a list of objects with keys: `feature_name`, `raw_p_value`, `adjusted_q_value` (Benjamini-Hochberg), and `is_significant` (boolean based on alpha=0.05). **Dependencies**: T051, T026.
- [X] T023 [P] [US2] Implement `code/models/evaluate.py` to calculate R², RMSE, MAE on the independent test set (SC-001) **AND report confidence intervals for R² (using bootstrapping logic similar to T025)**; **Execute** bootstrapping here to generate `data/results/model_metrics.json`. **Dependencies**: T022, T025.
- [ ] T024 [P] [US2] Implement null model comparison (predicting mean) and verify a significant RMSE improvement (>20% reduction). **Statistical Test**: Perform a paired t-test (or Wilcoxon signed-rank if non-normal) on the RMSEs from cross-validation folds. **Pairing**: Train the null model on the *exact same* folds as T023 to ensure valid pairing. Require p-value < 0.05 for significance. Output `data/validation/null_model_comparison.json` **including 95% confidence intervals for R² (using T025 bootstrapping logic)**; depends on T023, T025.
- [X] T025 [US2] **Implement Bootstrapping for Confidence Intervals**: Create `code/models/evaluate.py` function to perform bootstrapping (e.g., a sufficient number of resamples) to calculate 95% confidence intervals for R², RMSE, and MAE. **Usage**: This function is to be used by T023, T024, and T033. **Dependencies**: T023.
- [X] T034 [US2] Implement diagnostic report generation for cases where R² < 0.5 (suggesting non-linear effects); output `data/validation/diagnostic_report.json`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Interpret Model Drivers via SHAP Analysis (Priority: P3)

**Goal**: Generate SHAP plots and validate feature importance against physicochemical consensus using internal data only.

**Independent Test**: Run SHAP analysis on the best model; verify the top 3 features include at least 2 from the consensus list.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [P] [US3] Contract test for SHAP output format in `tests/contract/test_shap_output.py`
- [X] T029 [P] [US3] Integration test for feature ranking validation in `tests/integration/test_feature_ranking.py`

### Implementation for User Story 3

- [X] T030 [P] [US3] Implement `code/interpret/shap_analysis.py` to generate SHAP summary plots for top-ranked features (FR-005)
- [X] T031 [US3] Implement `code/interpret/shap_analysis.py` to generate partial dependence plots (PDP) for top descriptors. **Requirement**: Verify and log whether the relationship is monotonically non-decreasing (or non-increasing). **Metric**: Calculate Spearman's rank correlation coefficient. Require `abs(rho) > 0.9` and p-value < 0.05 to confirm monotonicity.
- [X] T033 [US3] **Retrain on Top 3 Features**: Extract the Top 3 features identified in T030 from `data/results/shap_summary.json` using key path `['summary']['features']` sorted by `mean_abs_shap_value` descending. **Select the model architecture with the highest R² from `data/results/model_metrics.json` (generated by T023)**. Retrain a **fresh** model using ONLY these 3 features. Measure R² against null model (SC-003) **and report confidence intervals (using T025 bootstrapping logic)**; output metrics to `data/results/reduced_model_metrics.json` with keys: `r2`, `rmse`, `mae`, `null_model_r2`, `improvement_pct`. **Dependencies**: T030, T023, T025, T052.
- [X] T032 [US3] **Unified Consensus Analysis**: Implement comparative analysis logic in `code/interpret/shap_analysis.py` to compare top-ranked features against the `LiteratureConsensusList` defined in the spec. **Requirement**: This logic applies to ALL data sources (internal NIST/MOF-1000). Generate a structured report discussing alignment/divergence (FR-008). **CRITICAL**: Programmatically verify and flag the existence of at least one point of convergence or divergence. **If none are found, raise `ConsensusValidationFailure`**. **NO** external dataset fetching is permitted. This task includes the generation of the consensus report and its integration into the final output. **Dependency**: T052 (to include adjusted p-values in the report as per SC-005).
- [X] T039a [US2] [P] Verify runtime metrics with benchmark run on real data.
- [ ] T039b [US2] [P] Performance optimization: Optimize code to ensure pipeline runtime ≤ 4 hours based on T039a results (SC-004).
- [X] T039c [US2] [P] **Benchmark Full Pipeline**: Create `code/main.py` CLI flag `--mode benchmark` to run the **full pipeline** (including training and SHAP) and measure total time. **Logic**: Ensure `data/benchmarks/runtime_log.json` is generated and checked against the ≤ 4 hours threshold. **Note**: This task must execute the full workload to verify SC-004. **Dependencies**: T054, T055.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T037 [P] Documentation updates in `README.md` and `docs/`
- [X] T038 Code cleanup and refactoring of `code/main.py` orchestrator
- [X] T054 [US2] [P] **Implement Runtime Logger**: Create `code/utils/runtime_logger.py` with `start_timer()` and `end_timer()` functions to instrument `code/main.py`.
- [X] T055 [US2] **Persist Runtime Log**: Ensure the logger writes the final JSON artifact to `data/benchmarks/runtime_log.json` containing `start_time` (ISO8601), `end_time` (ISO8601), `duration_seconds` (float), and `status` (string: success/failed). **Verification**: Validate that `duration_seconds` is recorded and check against the ≤ 4 hours threshold (SC-004) in the final report. **Dependencies**: T054.
- [X] T040a [US1] [P] Unit test for empty dataset edge case in `tests/unit/test_preprocess_empty.py::test_empty_dataset`
- [X] T040b [US1] [P] Unit test for single material edge case in `tests/unit/test_preprocess_single.py`
- [X] T041 Security hardening: Sanitize inputs in `code/data/download.py`
- [X] T042 Run `quickstart.md` validation if available

---

## Dependencies & Execution Order

1. Phase 1: Setup
2. Phase 2: Foundational
3. Phase 3: User Story 1 - Curate and Prepare the Adsorption Dataset
4. Phase 4: User Story 2 - Train and Evaluate Predictive Models
5. Phase 5: User Story 3 - Interpret Model Drivers via SHAP Analysis
6. Phase 6: Polish & Cross-Cutting Concerns
