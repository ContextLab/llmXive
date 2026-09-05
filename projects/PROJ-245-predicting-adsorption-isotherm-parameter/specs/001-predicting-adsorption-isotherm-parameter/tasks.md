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

- [X] T060 [US1] **Implement Streaming Data Loader**: Update `code/data/download.py` to use `datasets.load_dataset("nasa/nist-adsorption-isotherms", split="train", streaming=True)`. **Constraint**: Filter for Type I isotherms. **Dependencies**: None.
- [X] T061 [US1] **Merge Chunks**: Create `code/data/merge.py` to combine `data/raw/streamed_chunk_*.parquet` into `data/raw/merged_dataset.parquet`. **Dependencies**: T060.
- [X] T061a [US1] **Generate Reference Hash**: Create `code/data/verify_real.py` to compute checksum of first 100 rows. **Dependencies**: T061.
- [X] T061b [US1] **Verify Against Reference**: Update `code/data/verify_real.py` to compare current hash. **Dependencies**: T061a.
- [X] T043a [P] [US1] Implement `code/data/loader.py`: **Fetch & Validate**. **Constraint**: Raise `DataFetchError` if fetch fails. **Dependencies**: T060.
- [X] T014f [P] [US1] **Define Configurable Descriptor Registry**: Create `code/data/descriptor_registry.py` and `config/descriptors.yaml`. **Logic**: 1. Define a YAML schema for descriptor configuration (name, method, parameters). 2. Implement a loader that reads `config/descriptors.yaml` to determine which descriptors to calculate. 3. **Output**: Generate `config/descriptors.yaml` with default entries for all required descriptors (Kinetic Diameter, LJ Epsilon, Quadrupole, Polarizability, VdW Volume). **Constraint**: This task must run FIRST in Phase 2. **Dependencies**: None.
- [X] T014g [P] [US1] **Validate Descriptor Config Against FR-001**: Create `code/data/validate_config.py` function `validate_descriptors`. **Logic**: 1. Load `config/descriptors.yaml`. 2. Compare keys against the mandatory list from FR-001 (polarizability, VdW volume, etc.). 3. Raise `ConfigValidationError` if any mandatory descriptor is missing. **Output**: Pass/Fail status. **Dependencies**: T014f.
- [X] T015a-1 [US1] **Filter & Normalize Data (Target Filter)**: Create `code/data/preprocess.py` function `filter_targets`. **Logic**: 1. Load `data/raw/merged_dataset.parquet`. 2. Filter entries to include ONLY Type I isotherms. 3. **Hard Exclude** rows where `langmuir_capacity` OR `henry_constant` is missing (NaN/Null). 4. Normalize `surface_area` to m²/g. 5. Log excluded entries (reason: missing_target) to `data/validation/exclusion_log.json`. **Output**: `data/processed/target_filtered.parquet`. **Schema**: Same as input, minus excluded rows. **Dependencies**: T060, T061.
- [X] T015b [US1] **Implement Imputation**: Create `code/data/imputation.py` function `impute_pore_volume`. **Logic**: 1. Load `data/processed/target_filtered.parquet`. 2. Group by `(material_type, surface_area_bin)`. 3. If group size > 0, assign group mean. 4. If group size == 0, assign `material_type` global mean. 5. If no `material_type` exists, assign global dataset mean. 6. If imputation fails, exclude row and log to `data/validation/exclusion_log.json` (reason: imputation_failed). **Output**: `data/processed/imputed_dataset.parquet`. **Dependencies**: T015a-1.
- [X] T014ba [P] [US1] **Implement Kinetic Diameter Calculation**: Create `code/data/descriptors.py` function `calc_kinetic_diameter`. **Logic**: Calculate using RDKit (preferred) or formula `d = sqrt(4 * CalcTPSA(mol) / PI)`. **Constraint**: CALCULATE ONLY. Do NOT use metadata fallback. **Error Handling**: If molecule cannot be processed, raise descriptive error and log to `data/validation/missing_descriptors_kinetic.json`. **Output**: Update `data/processed/descriptors.parquet` with column `kinetic_diameter`. **Dependencies**: T014f, T060, T061, T015a-1, T015b.
- [X] T014bb [P] [US1] **Implement Lennard-Jones Energy Parameter**: Create `code/data/descriptors.py` function `calc_lj_epsilon`. **Logic**: Extract `critical_pressure` and `critical_volume` from `data/processed/imputed_dataset.parquet`. Estimate Tc using `Tc = 1.5 * (Pc * Vc / R)`, then `epsilon = 0.75 * Tc`. **Constraint**: If Pc or Vc are missing AFTER imputation, exclude the row and log to `data/validation/exclusion_log.json`. **Error Handling**: If estimation fails, raise descriptive error and log to `data/validation/missing_descriptors_lj.json`. **Output**: Update `data/processed/descriptors.parquet` with column `lj_epsilon`. **Dependencies**: T014f, T060, T061, T015a-1, T015b.
- [X] T014bc [P] [US1] **Implement Quadrupole Moment Calculation**: Create `code/data/descriptors.py` function `calc_quadrupole_moment`. **Logic**: 1. Extract coordinates from `coordinates` column. 2. If 2D, use RDKit `EmbedMolecule` to generate 3D. 3. Use `psi4` with `b3lyp`/`def2-svp`, Charge=0, Multiplicity=1, Origin=Center of Mass. 4. Extract `properties["quadrupole_moment"][0,0]`. **Constraint**: CALCULATE ONLY. Do NOT use metadata fallback. **Timeout**: If psi4 calculation > 10 mins, skip and log to exclusion_log.json. **Error Handling**: If psi4 fails, raise descriptive error and log to `data/validation/missing_descriptors_quadrupole.json`. **Output**: Update `data/processed/descriptors.parquet` with column `quadrupole_moment`. **Dependencies**: T014f, T060, T061, T015a-1, T015b.
- [X] T014fa [P] [US1] **Implement Polarizability Calculation**: Create `code/data/descriptors.py` function `calc_polarizability`. **Logic**: Use RDKit to calculate polarizability. **Constraint**: CALCULATE ONLY. Do NOT use metadata fallback. **Output**: Update `data/processed/descriptors.parquet` with column `polarizability`. **Dependencies**: T014f, T060, T061, T015a-1, T015b.
- [X] T014fb [P] [US1] **Implement Van der Waals Volume Calculation**: Create `code/data/descriptors.py` function `calc_vdw_volume`. **Logic**: Use RDKit to calculate van der Waals volume. **Constraint**: CALCULATE ONLY. Do NOT use metadata fallback. **Output**: Update `data/processed/descriptors.parquet` with column `vdw_volume`. **Dependencies**: T014f, T060, T061, T015a-1, T015b.
- [X] T014d [P] [US1] **Merge Descriptor Logs**: Create `code/data/descriptors.py` function to merge `missing_descriptors_kinetic.json`, `missing_descriptors_lj.json`, `missing_descriptors_quadrupole.json` into `data/validation/missing_descriptors_report.json`. **Dependencies**: T014ba, T014bb, T014bc, T014fa, T014fb.
- [X] T016 [US1] **Implement Outlier Detection & Exclusion List**: Create `code/data/preprocess.py` function `detect_outliers`. **Logic**: 1. Group rows by `descriptor_hash`. 2. For each group with size > 1, calculate mean and std of the **primary target variable** (default `langmuir_capacity`). 3. Flag entries where `|value - group_mean| > 3 * group_std`. 4. **Output**: Generate `data/validation/exclusion_list.csv` with columns [material_id, descriptor_hash, target_value, group_mean, group_std, exclusion_reason]. **Constraint**: These rows MUST be excluded from training in T020/T021. **Edge Case**: If NO groups have size > 1, log "No identical descriptors found" and proceed. **Dependencies**: T014e, T015a-1, T015b.
- [X] T015c [US1] **Validate Dataset Size**: Create `code/data/validate.py` to assert that the final dataset size N > 500 after T015a-1, T015b, and T014h. **Requirement**: If N <= 500, raise `DatasetSizeError`. **Dependencies**: T015a-1, T015b, T014h.
- [X] T014c [US1] **Implement Parameter Fitting**: Create `code/data/fitting.py` to fit Langmuir/Henry parameters from raw isotherm points. **Dependencies**: T015a-1.
- [X] T014e [US1] **Generate Descriptor Hash**: Create `code/data/descriptors.py` function `generate_descriptor_hash`. **Logic**: Compute hash of sorted tuple of all calculated descriptor values. **Dependencies**: T014ba, T014bb, T014bc, T014fa, T014fb, T015b.
- [X] T045 [US2] Implement `code/models/audit.py` for **Data Leakage Audit**. **Dependencies**: T020.
- [X] T014h [P] [US1] **Implement Descriptor Caching**: Create `code/data/descriptors.py` function `cache_descriptors`. **Logic**: Cache calculated descriptors to `data/processed/descriptors_cache.parquet` to avoid re-calculation. **Dependencies**: T014f, T014ba, T014bb, T014bc, T014fa, T014fb.
- [X] T039e [US2] [P] **Time Budgeting & Profiling**: Create `code/utils/profiler.py`. **Logic**: Profile T014bc execution time. If > 30 mins per batch, trigger alert. **Dependencies**: T014bc.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Curate and Prepare the Adsorption Dataset (Priority: P1) 🎯 MVP

**Goal**: Generate a clean, normalized CSV linking molecular descriptors to isotherm parameters using real experimental data only.

**Independent Test**: Run `code/data/preprocess.py` on the real dataset and verify the output CSV contains exactly `polarizability`, `langmuir_capacity`, `henry_constant`, `surface_area` (m²/g) with no missing values.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T012 [P] [US1] Contract test for schema compliance in `tests/contract/test_dataset_schema.py`
- [X] T013 [P] [US1] Unit test for RDKit descriptor calculation in `tests/unit/test_descriptors.py`

### Implementation for User Story 1

- [X] T017 [US1] Update `code/main.py` orchestrator to run the full data curation pipeline; depends on T014ba, T014bb, T014bc, T060, T015a-1, T014c, T015b, T014d, T014e, T016, T015c, T014h

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train and Evaluate Predictive Models (Priority: P2)

**Goal**: Train baseline models (Linear, RF, GB) with strict material-level splitting and evaluate performance on real data.

**Independent Test**: Run training on real data; verify that the test set contains no materials present in the training set and that metrics (R², RMSE) are logged.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output.py`
- [X] T019 [P] [US2] Integration test for material-level data splitting in `tests/integration/test_data_split.py`

### Implementation for User Story 2

- [X] T020 [US2] Implement `split_data()` in `code/models/train.py` to perform **Material-Level Split**. **Logic**: Group by `adsorbent_structure_id` (not material_id). Split groups **stratified by material_id**. **Constraint**: Ensure no `adsorbent_structure_id` appears in both train and test. Exclude rows listed in `data/validation/exclusion_list.csv` (from T016). **Dependencies**: T060, T061, T016.
- [X] T067 [US2] **Implement Cluster-Aware Cross-Validation**: Create `code/models/train.py` function `cluster_kfold_split`. **Logic**: Ensure no `adsorbent_structure_id` appears in both train and validation folds. **Constraint**: Must replace standard KFold in T022. **Dependencies**: T020.
- [X] T021 [P] [US2] Implement `train_models()` in `code/models/train.py` to **Train Models**: Train Linear Regression, Random Forest, and Gradient Boosting models using the split from T020 and CV from T067. Exclude rows flagged in T016. **Dependencies**: T020, T067.
- [X] T022 [P] [US2] Implement `tune_hyperparameters()` in `code/models/train.py` to perform **5-fold Cross-Validation** using `cluster_kfold_split`. **Output**: Save `folds.json`. **Dependencies**: T020, T067.
- [X] T065 [US2] **Implement Robust Null Model Baseline**: Create `code/models/null_model.py`. **Logic**: 1. Load `folds.json` from T022. 2. Load dataset. 3. For each fold index, map indices to row indices, train null model (predict mean) on training split, predict on test split. 4. Calculate RMSE for each fold. 5. Output `data/results/null_model_fold_rmses.json`. **Dependencies**: T022.
- [X] T023 [P] [US2] Implement `code/models/evaluate.py` to calculate R², RMSE, MAE on test set **AND** report confidence intervals (using T025 bootstrapping). **Dependencies**: T022, T025.
- [X] T024 [P] [US2] **Implement null model comparison**. **Logic**: Perform paired t-test (`scipy.stats.ttest_rel`) or Wilcoxon (`scipy.stats.wilcoxon`) on paired RMSEs. Require p-value < 0.05. **Constraint**: Verify RMSE is at least 20% lower than null model. **Output**: `data/validation/null_model_comparison.json` with 95% CIs (`n_resamples=1000`, `random_state=42`). **Schema**: `{ "rmse_full": float, "rmse_null": float, "p_value": float, "ci_95": [float, float] }`. **Dependencies**: T023, T065, T025.
- [X] T025 [P] [US2] **Implement Bootstrapping for Confidence Intervals**: Create `code/models/evaluate.py` function. **Dependencies**: T021, T022.
- [X] T034 [US2] Implement diagnostic report generation for R² < 0.5. **Dependencies**: T023.
- [X] T051 [US2] **Implement Cluster-Aware Permutation Engine**: Create `code/analysis/cluster_permutation.py`. **Logic**: Shuffle values within `adsorbent_structure_id` clusters. **Dependencies**: T020, T021.
- [X] T026 [P] [US2] **Implement Benjamini-Hochberg FDR Correction**: Create `code/models/evaluate.py` function. **Dependencies**: T051.
- [X] T052 [US2] **Integrate Cluster Permutation & FDR**: Create `code/analysis/cluster_permutation.py` function `run_fdr_pipeline`. **Logic**: 1. Run permutation on top features. 2. Apply Benjamini-Hochberg correction. 3. Output `data/results/adjusted_pvalues.json`. **Schema**: `{ "feature_name": float }`. **Dependencies**: T051, T026.
- [X] T068 [US2] **Implement Null Model Baseline for Reduced Features**: Create `code/models/null_model.py` function `null_model_top3`. **Logic**: 1. Load top 3 features from `data/results/shap_summary.json`. 2. Filter dataset to these 3 features. 3. Train null model (predict mean) on training split. 4. Calculate RMSE on test split. 5. Output `data/results/null_model_top3_rmses.json`. **Dependencies**: T020, T022.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Interpret Model Drivers via SHAP Analysis (Priority: P3)

**Goal**: Generate SHAP plots and validate feature importance against physicochemical consensus using internal data only.

**Independent Test**: Run SHAP analysis on the best model; verify the top 3 features include at least 2 from the consensus list.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [P] [US3] Contract test for SHAP output format in `tests/contract/test_shap_output.py`
- [X] T029 [P] [US3] Integration test for feature ranking validation in `tests/integration/test_feature_ranking.py`

### Implementation for User Story 3

- [X] T030 [P] [US3] Implement `code/interpret/shap_analysis.py` to generate SHAP summary plots. **Output**: Write `data/results/shap_summary.json` as a list of objects with keys `name` (str) and `mean_abs_shap_value` (float64), sorted by value descending. **Dependencies**: T021.
- [X] T069 [US3] **Implement Literature Consensus Loader**: Create `code/interpret/consensus.py` to load `LiteratureConsensusList` from `config/consensus_list.yaml`. **Schema**: YAML list of strings or objects `{ name: str, description: str }`. **Dependencies**: None.
- [X] T070 [US3] **Implement Divergence Report Generator**: Create `code/interpret/report.py` to generate a structured report comparing `data/results/shap_summary.json` against `LiteratureConsensusList`. **Logic**: Explicitly list features in consensus but not in top 3, and vice versa. **Output**: `data/results/consensus_divergence_data.json`. **Dependencies**: T030, T069.
- [X] T071 [US3] **Generate Narrative Consensus Report**: Create `code/interpret/report.py` function `generate_narrative_report`. **Logic**: 1. Load `data/results/consensus_divergence_data.json`. 2. Generate a Markdown narrative discussing alignment/divergence, explicitly identifying at least one point of convergence and one divergence. 3. **Output**: `data/results/consensus_narrative_report.md`. **Dependencies**: T070.
- [X] T031 [US3] Implement `code/interpret/shap_analysis.py` to generate partial dependence plots. **Requirement**: Verify monotonicity (Spearman's rho > 0.9). **Range**: 10th-90th percentile. **Dependencies**: T030.
- [X] T033 [US3] **Retrain on Top 3 Features**: Extract Top 3 features from `data/results/shap_summary.json`. Retrain model using ONLY these 3 features. Measure R² vs **T068** (Reduced Null Model). **Constraint**: Verify R² improvement over null is ≥ 0.2. **Output**: `data/results/reduced_model_metrics.json`. **Schema**: `{ "r2": float, "rmse": float, "null_rmse": float, "improvement": float }`. **Dependencies**: T030, T023, T025, T052, T068.
- [X] T032 [US3] **Unified Consensus Analysis**: Implement comparative analysis logic. **Requirement**: Programmatically verify at least one point of convergence/divergence. **Dependencies**: T052, T033.
- [X] T064 [US3] **Validate SHAP Stability**: Implement stability check via bootstrap resamples. **Dependencies**: T030, T025.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T037 [P] Documentation updates in `README.md` and `docs/`
- [X] T038 Code cleanup and refactoring of `code/main.py` orchestrator
- [X] T054 [US2] [P] **Implement Runtime Logger**: Create `code/utils/runtime_logger.py`. **Logic**: Initialize logger at start of `main.py` execution. **Constraint**: Must run unconditionally on every pipeline run, not just benchmark mode. **Dependencies**: None.
- [X] T055 [US2] **Persist Runtime Log**: Ensure logger writes `data/benchmarks/runtime_log.json`. **Dependencies**: T054.
- [X] T040a [US1] [P] Unit test for empty dataset edge case in `tests/unit/test_preprocess_empty.py::test_empty_dataset`
- [X] T040b [US1] [P] Unit test for single material edge case in `tests/unit/test_preprocess_single.py`
- [X] T041 Security hardening: Sanitize inputs in `code/data/download.py`
- [X] T042 Run `quickstart.md` validation if available
- [X] T062 [US1] [P] **Implement Robust Data Source Fallback Detection**: Update `code/data/download.py` to detect network vs ID errors. **Dependencies**: T043a.
- [X] T066 [US1] **Add Data Leakage Check for Descriptors**: Extend audit (T045). **Dependencies**: T014ba, T014bb, T014bc, T045.
- [X] T039a [US2] [P] Verify runtime metrics with benchmark run on real data. **Dependencies**: T054, T055.
- [X] T039c [US2] [P] **Benchmark Full Pipeline**: Create `code/main.py` CLI flag `--mode benchmark`. **Dependencies**: T054, T055, T033.
- [X] T039b [US2] [P] **Performance Optimization**: Refactor `code/data/descriptors.py` to use multiprocessing for psi4 calls, targeting >50% runtime reduction. **Output**: `data/benchmarks/optimization_report.json`. **Dependencies**: T039c.

---

## Revision Concerns & New Tasks

**Purpose**: Address specific reviewer concerns from prior analysis regarding data integrity, statistical rigor, and edge case handling.

- [X] T062 [US1] **Implement Robust Data Source Fallback Detection**: (See Phase 6). **Dependencies**: T043a.
- [X] T064 [US3] **Validate SHAP Stability**: (See Phase 5). **Dependencies**: T030, T025.
- [X] T066 [US1] **Add Data Leakage Check for Descriptors**: (See Phase 6). **Dependencies**: T014ba, T014bb, T014bc, T045.
- [X] T015a-1 [US1] **Filter & Normalize Data (Target Filter)**: (See Phase 2). **Dependencies**: T060, T061.
- [X] T015b [US1] **Implement Imputation**: (See Phase 2). **Dependencies**: T015a-1.
- [X] T024 [US2] **Implement null model comparison**: (See Phase 4). **Dependencies**: T023, T065, T025.
- [X] T039b [US2] **Performance Optimization**: (See Phase 6). **Dependencies**: T039c.
- [X] T067 [US2] **Implement Cluster-Aware Cross-Validation**: (See Phase 4). **Dependencies**: T020.
- [X] T068 [US2] **Implement Null Model Baseline for Reduced Features**: (See Phase 4). **Dependencies**: T020, T022.
- [X] T069 [US3] **Implement Literature Consensus Loader**: (See Phase 5). **Dependencies**: None.
- [X] T070 [US3] **Implement Divergence Report Generator**: (See Phase 5). **Dependencies**: T030, T069.
- [X] T071 [US3] **Generate Narrative Consensus Report**: (See Phase 5). **Dependencies**: T070.

---

## Dependencies & Execution Order

1. Phase 1: Setup
2. Phase 2: Foundational (T060 -> T061 -> T014f -> T014g -> T015a-1 -> T015b -> T014ba/14bb/14bc/14fa/14fb -> T014d -> T014e -> T016 -> T015c -> T014h -> T039e)
3. Phase 3: User Story 1 - Curate and Prepare the Adsorption Dataset
4. Phase 4: User Story 2 - Train and Evaluate Predictive Models (T020 -> T067 -> T021 -> T022 -> T065 -> T023 -> T024 -> T051 -> T052 -> T068)
5. Phase 5: User Story 3 - Interpret Model Drivers via SHAP Analysis (T030 -> T069 -> T070 -> T071 -> T031 -> T033)
6. Phase 6: Polish & Cross-Cutting Concerns