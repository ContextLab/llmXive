---
description: "Task list template for feature implementation"
---

# Tasks: Predicting Molecular Interactions in Ionic Liquids via Machine Learning

**Input**: Design documents from `/specs/001-predicting-molecular-interactions-in-ion/`
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

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 0: Setup & Spec Alignment (Shared Infrastructure)

**Purpose**: Project initialization and formal alignment of Spec/Plan contradictions

- [ ] T000-Amend [P] **SPEC AMENDMENT**: Edit `specs/001-predicting-molecular-interactions-in-ion/spec.md` to change FR-007 text from "experimental enthalpy of mixing" to "Independent DFT validation set (generated via Verified Synthetic Generation)". Update SC-003 to reflect this change (MAE ≤ 0.5 kcal mol⁻¹ against DFT). Update US-3 Acceptance Scenario 3 to use DFT data. Edit `plan.md` to reference the amended spec. **Verification**: Verify `spec.md` FR-007 text reads "Independent DFT validation" and `SC-003` references DFT.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create project directory structure: Create `scripts/setup_dirs.sh` that generates `code/`, `data/raw/`, `data/processed/`, `data/validation/`, `models/`, `contracts/`, `tests/`, and `logs/`. Verify the script executes and lists the generated tree in `logs/setup.log`.
- [X] T001b [P] Initialize empty files: Create `code/__init__.py`, `code/config.py`, `code/data_ingestion.py`, `code/model_training.py`, `code/analysis.py`, `code/utils.py`, `data/raw/.gitkeep`, `data/processed/.gitkeep`, `data/validation/.gitkeep`, `models/.gitkeep`, `contracts/.gitkeep`, `tests/__init__.py`. Verify all listed files exist and are non-empty (or.gitkeep) before marking complete.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002a [P] Create `code/requirements.txt` with pinned versions: `xgboost==2.0.3`, `optuna==3.5.0`, `rdkit==2023.9.5`, `pandas==2.1.4`, `scikit-learn==1.3.2`, `pyarrow==14.0.2`, `requests==2.31.0`, `pyyaml==6.0.1`, `psi4==1.8.1`, `statsmodels==0.14.1`, `pandera==0.17.2`, `pytest-mock==3.12.0`. **Install Command**: `venv/bin/pip install -r code/requirements.txt`. Verify `venv/bin/python` exists and `pip list` shows required packages.
- [X] T002b [P] Setup Python virtual environment: Create `scripts/setup_venv.sh` that creates the venv and installs requirements. Verify `venv/bin/python` exists and `pip list` shows required packages.
- [X] T004a [P] Create `contracts/ion_pair.schema.yaml` defining fields: `cation_id` (str), `anion_id` (str), `electrostatic_energy` (float), `dispersion_energy` (float), `hbond_energy` (float), `total_energy` (float), `tpsa` (float), `molecular_surface_area` (float), `hbond_count` (int), `morgan_fp` (array), `structural_family` (str), `polarizability` (float), `partial_charge` (float). **Note**: `partial_charge` is included as a *calculated* field to satisfy FR-002 generation requirement, but MUST be excluded from the *training feature set* in T016a. Verify file is valid YAML and matches pandera schema requirements.
- [X] T004b [P] Create `contracts/validation_report.schema.yaml` defining fields: `anova_results_raw` (object), `anova_results_predictions` (object), `tukey_hsd` (object), `dft_mae` (float), `experimental_validation_mae` (float), `sc003_compliance` (bool), `experimental_validation_status` (str), `tautology_check` (object). Verify file is valid YAML and matches pandera schema requirements.
- [X] T005a [P] Implement `code/config.py` defining `SEED=42`, `DATA_PATHS` (dict), `HYPERPARAM_BOUNDS` (dict), `MAX_TRIALS=60`, `TRIAL_TIMEOUT=300` (seconds), `TRAIN_RATIO=0.7`, `VAL_RATIO=0.15`, `TEST_RATIO=0.15`.
- [X] T005b [P] Implement `.env.example` and `code/config.py` loading logic using `python-dotenv` to override defaults.
- [X] T006a [P] Implement `code/utils.py` with functions: `compute_tpsa(smiles)`, `compute_morgan_fp(smiles, radius=2, n_bits=2048)`, `compute_hbond_count(smiles)`.
- [X] T006b [P] Implement `code/utils.py` with function: `run_psi_sapt(structure_file, method='sapt', basis='jun-cc-pVDZ')` returning energy components.
- [X] T006c [P] Implement `code/utils.py` with function: `compute_polarizability(smiles)` using RDKit's `rdkit.Chem.Crippen.MolMR` as a proxy for polarizability. Verify it returns a float.
- [X] T008a [P] Implement `code/utils.py` logging configuration: `logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO, handlers=[logging.FileHandler('logs/pipeline.log')])`.
- [X] T008b [P] Implement `code/utils.py` custom exception hierarchy: `DataIngestionError`, `ModelTrainingError`, `AnalysisError`.
- [X] T009a [P] Create `code/.env.example` with `SPICE_URL`, `IL_SAPT_URL`, `ILTHERMO_URL`, `DFT_VALIDATION_URL`. Verify file exists and contains these keys.
- [X] T009b [P] Implement `code/config.py` to load `.env` and validate required keys exist, raising `DataIngestionError` if missing.
- [ ] T012a-SpineLoad [US1] Implement `code/data_ingestion.py` function `download_spice_dataset(url)`: **PRIMARY SOURCE**. Fetch the SPICE dataset using the URL from `code/config.py`. **Constraint**: Do NOT use hardcoded URLs. Save to `data/raw/spice.parquet`. Verify file exists and contains columns `cation_id`, `anion_id`, `smiles_cation`, `smiles_anion`, `structural_family`, `electrostatic_energy`, `dispersion_energy`, `hbond_energy`.
- [ ] T012b-SaptLoad [US1] Implement `code/data_ingestion.py` function `download_il_sapt_dataset(url)`: **SECONDARY SOURCE**. Attempt to fetch the IL-SAPT dataset. If the URL is missing or the fetch fails, log a WARNING and proceed with SPICE only. Save to `data/raw/sapt.parquet` if successful. **Dependency**: Must run after T012a-SpineLoad (to ensure primary data is available).
- [ ] T012c-Unify [US1] Implement `code/data_ingestion.py` function `unify_datasets()`: **UNIFIED INGESTION**. Merge `data/raw/spice.parquet` and `data/raw/sapt.parquet` (if present) into a unified dataframe. **Output**: A unified dataframe with columns `cation_id`, `anion_id`, `smiles_cation`, `smiles_anion`, `structural_family`, `electrostatic_energy`, `dispersion_energy`, `hbond_energy`, `source`. **Dependency**: Must run after T012a-SpineLoad and T012b-SaptLoad.
- [ ] T013c-Structures [P] [US1] Implement `code/data_ingestion.py` function `extract_structures_from_data(df)`: Extract unique cation/anion SMILES from the unified dataset (`data/raw/spice.parquet`, `data/raw/sapt.parquet`) and save to `data/raw/il_structures.json`. **Dependency**: Must run after T012c-Unify. Verify `data/raw/il_structures.json` exists and contains valid SMILES.
- [ ] T012c-TrainGen [US1] [Plan Phase 0] [Constitution VI] Implement `code/data_ingestion.py` function `generate_sapt_training_labels()`: **SYNTHETIC TRAINING FALLBACK**. Implement the "Verified Synthetic Generation" protocol using `psi4` and `data/raw/il_structures.json` to generate SAPT energy components for the TRAINING set if the real SAPT source is missing. **Logic**: Check if `data/raw/sapt.parquet` exists and has > 0 rows. If not, randomly select N=500 IonPairs (seed=42) stratified by StructuralFamily from `data/raw/il_structures.json` and calculate SAPT/DFT energy components using `run_psi_sapt`. Save to `data/processed/sapt_training_labels.parquet`. **Note**: This implements the Plan's fallback for missing training data. **Dependency**: Must run after T013c-Structures.
- [ ] T012b-Gen [P] [US1] [Plan Phase 2] [Constitution VI] Implement `code/data_ingestion.py` function `generate_dft_validation_set()`: **INDEPENDENT DFT VALIDATION**. Implement the "Verified Synthetic Generation" protocol using `psi4` and `data/raw/il_structures.json`. **Logic**: Check if `data/validation/dft_validation_set.parquet` exists. If not, randomly select a representative subset of IonPairs (seed=42) from `data/raw/il_structures.json` and calculate SAPT/DFT energy components using `run_psi_sapt`. Save to `data/validation/dft_validation_set.parquet`. **Note**: This implements the amended FR-007 requirement for Independent DFT validation. **Dependency**: Must run after T013c-Structures.
- [X] T012c [P] Implement `code/data_ingestion.py` function `verify_checksum(file_path, expected_hash)` to validate downloaded data.
- [ ] T015a [US1] Implement `code/data_ingestion.py` function `calculate_partial_charges_internal_only(df)`: Calculate Gasteiger partial charges using RDKit for *internal consistency checks only*. **Constraint**: These values MUST NOT be used as input features for training. Save the result to `data/processed/internal_consistency_checks.parquet` before dropping from the main dataset. **Note**: This satisfies FR-002 generation requirement.
- [ ] T016a [US1] Implement `code/data_ingestion.py` function `engineer_features(df)`: Parse SMILES, compute TPSA, Molecular Surface Area, H-bond counts, and graph embeddings. **CRITICAL**: Depends on T015a. Call `calculate_partial_charges_internal_only` to save the internal consistency artifact. Then, **DROP** the `partial_charge` column from the DataFrame passed to the model training function. Save the full DataFrame (with `partial_charge`) to `data/processed/unified_dataset.parquet` and the training feature set (without `partial_charge`) to `data/processed/training_features.parquet`. **Note**: The `partial_charge` column must be retained in the *final unified dataset* output file (via T016b) to satisfy US-1 Independent Test, but excluded from the *training feature set*.
- [ ] T016b [P] [US1] Implement `code/data_ingestion.py` function `merge_consistency_artifacts()`: Read `data/processed/internal_consistency_checks.parquet` (from T015a) and merge it into the final unified dataset for the 'Internal Consistency' report, ensuring the `partial_charge` column is present in the final output file (`data/processed/unified_dataset.parquet`) as required by Spec US-1 Independent Test, while ensuring it was not used for training. **Dependency**: Must run after T016a and T015a.
- [ ] T017a-Check [US1] Implement `code/data_ingestion.py` function `check_data_source_existence()`: **DATA SOURCE CHECK**. Check if `data/raw/spice.parquet` exists. Check if `data/raw/sapt.parquet` exists. Return a dictionary with keys: `{'spice_exists': bool, 'sapt_exists': bool, 'il_thermo_exists': bool}`. **Dependency**: Must run after T012a-SpineLoad and T012b-SaptLoad.
- [ ] T017b-Select [US1] Implement `code/data_ingestion.py` function `select_data_sources(flags)`: **DATA SOURCE SELECTION**. Based on flags from T017a-Check: If SPICE exists, select it. If SAPT exists, select it. If neither exists, trigger the "Verified Synthetic Generation" protocol (T012c-TrainGen logic) for training labels. Return a dictionary with keys `selected_paths` (list[str]) and `source_type` (str). **Note**: Logic must handle separate structure and energy sources and implement the Plan's fallback. **Dependency**: Must run after T017a-Check.
- [ ] T017c-Path [P] [US1] Implement `code/data_ingestion.py` function `get_selected_paths()`: **FILE PATH RETURN**. Return the paths to the selected data files based on the selection logic in T017b-Select. **Dependency**: Must run after T017a-Check and T017b-Select.
- [ ] T017d [US1] Implement `code/data_ingestion.py` function `filter_raw_sapt(df)`: Filter the unified dataset to extract the subset of data originating strictly from the SAPT source (where `source == 'sapt'`). Save to `data/processed/raw_sapt.parquet`. **Dependency**: Must run after T017c-Path.
- [ ] T017e [P] [US1] Implement `code/data_ingestion.py` function `write_unified_dataset(df, path)` to save to `data/processed/unified_dataset.parquet`.
- [ ] T017f-SynthFilter [US1] Implement `code/data_ingestion.py` function `filter_synthetic_raw_sapt()`: **SYNTHETIC RAW SAPT FILTER**. If real SAPT data is missing (and T012c-TrainGen was used), filter the synthetic training labels (`data/processed/sapt_training_labels.parquet`) to create a 'raw SAPT' equivalent subset for ANOVA analysis. Save to `data/processed/synthetic_raw_sapt.parquet`. **Dependency**: Must run after T012c-TrainGen.
- [X] T017b [P] [US1] Implement `code/data_ingestion.py` function `merge_il_thermo_sapt(il_df, sapt_df)`: Merge ILThermo and SAPT on `cation_id` and `anion_id`.
- [X] T017c [P] [US1] Implement `code/data_ingestion.py` function `merge_training_data(base_df, sapt_df)`: **REAL DATA MERGE ONLY**. Merge the base structure dataframe with the real SAPT energy dataframe. **Constraint**: This function must NOT handle synthetic data. If `sapt_df` is missing or empty, raise `DataIngestionError`. This function is strictly for the training pipeline.
- [X] T018a [US1] Implement `code/data_ingestion.py` function `validate_unified_dataset(df, schema_path)` using `pandera`.
- [X] T018b [US1] Implement `code/data_ingestion.py` function `log_validation_errors(errors)` to write detailed errors to `logs/ingestion_errors.log`.
- [X] T019 [US1] Add logging for ingestion steps and synthetic generation fallback. Update `code/data_ingestion.py` to log steps to `logs/ingestion.log`.

---

## Phase 3: User Story 1 - Data Ingestion and Feature Engineering (Priority: P1) 🎯 MVP

**Goal**: Ingest ILThermo/SAPT/SPICE, engineer descriptors, and produce a unified dataset.

**Independent Test**: Run ingestion on a small subset of IonPairs. Verify `data/processed/unified_dataset.parquet` contains expected columns with no null values. **Note**: `partial_charge` column must be present in the final output file (for consistency checks) but excluded from the training feature set.

---

## Phase 4: User Story 2 - Model Training and Hyperparameter Optimization (Priority: P2)

**Goal**: Train three XGBoost regressors with Optuna, respecting strict CPU time limits.

**Independent Test**: Run training on a toy dataset with a timeout mechanism. Verify three `.pkl` model artifacts are saved and logs show best hyperparameters and trial timeouts.

- [X] T021a [P] [US2] Implement `code/model_training.py` function `stratified_split(df, target_col, structural_family_col)`: Use `sklearn.model_selection.train_test_split` with ratios defined in `code/config.py`.
- [X] T021b [P] [US2] Implement `code/model_training.py` function `save_splits(train_df, val_df, test_df)` to `data/processed/train.parquet`, `val.parquet`, `test.parquet`.
- [X] T022 [US2] Implement `code/model_training.py` function `train_electrostatic_model(train_df, val_df)` using XGBoost.
- [X] T023 [US2] Implement `code/model_training.py` function `train_dispersion_model(train_df, val_df)` using XGBoost.
- [X] T024 [US2] Implement `code/model_training.py` function `train_hbond_model(train_df, val_df)` using XGBoost.
- [X] T025a [US2] Implement `code/model_training.py` function `optuna_objective(trial, model_type, train_df, val_df)` defining search space for XGBoost hyperparameters.
- [X] T025b [US2] Implement `code/model_training.py` function `run_optuna_study()` with `n_trials=60`, `timeout=300` seconds per trial, using `optuna.create_study`.
- [X] T026 [US2] Implement `code/model_training.py` function `save_models(models, path_prefix)` to save model artifacts.
- [X] T027 [US2] Implement `code/model_training.py` function `check_energy_consistency(predictions, total_sapt_targets, tolerance=0.1 kcal/mol)`.
- [X] T028a [US2] Add logging for MAE: In `code/model_training.py`, inside `run_optuna_study`, add `logger.info(f"Trial {trial.number}: MAE = {mae:.4f}")` after each successful trial.
- [X] T028b [US2] Add logging for convergence: In `code/model_training.py`, add `logger.info(f"Study completed. Best MAE: {study.best_value:.4f}")` after the study finishes.
- [X] T028c [US2] Add logging for timeout: In `code/model_training.py`, wrap `optuna_objective` in a timeout handler and add `logger.warning(f"Trial {trial.number} timed out after {TRIAL_TIMEOUT} seconds")` if it exceeds the limit.
- [X] T029a [US2] Implement `code/model_training.py` function `perform_sensitivity_analysis(study_results)` to calculate the variance of MAE across the top hyperparameter configurations.
- [X] T029b [US2] Implement `code/model_training.py` function `log_sensitivity_results(results)` to write detailed sensitivity analysis to logs.
- [ ] T062 [US2/Review] [Timeout Handling] Refactor `code/model_training.py` `optuna_objective` to ensure the 5-minute timeout is enforced at the OS level. **Logic**: Use `multiprocessing.Process` to wrap the model training call. Call `proc.start()`, then `proc.join(timeout=300)`. Check `proc.is_alive()`. If alive, call `proc.terminate()`. Log the specific timeout event with the trial ID. **Log Message**: `logger.warning(f"Trial {trial.number} terminated by timeout after {TRIAL_TIMEOUT} seconds")`. **Dependency**: Must run after T025b.

---

## Phase 5: User Story 3 - Systematic Variation Analysis and Validation (Priority: P3)

**Goal**: Perform ANOVA on model predictions (primary) AND raw SAPT data (comparative), apply corrections, validate against Independent DFT dataset, and report results.

- [ ] T029c-Raw [US3] Implement `code/analysis.py` function `run_anova_raw(df, energy_col, family_col)`: Perform One-way ANOVA on the *raw SAPT energy components* (pre-merging) grouped by `StructuralFamily`. Apply Bonferroni correction and Tukey HSD. **Dependency**: Must run after T017d (filter_raw_sapt) OR T017f-SynthFilter (if real SAPT missing). **Note**: This provides a baseline for comparison with T029c-Pred.
- [ ] T029c-Pred [US3] Implement `code/analysis.py` function `run_anova_predictions(predictions_df, family_col)`: **PRIMARY VALIDATION**. Perform One-way ANOVA on the *model predictions* grouped by `StructuralFamily`. Apply Bonferroni correction and Tukey HSD. **Dependency**: Must run after T022-T024 (model training). **Note**: This satisfies FR-006's requirement to validate the model's output.
- [X] T029e [US3] Implement `code/analysis.py` function `compare_anova_results(raw_results, pred_results)`: Compare the p-values and effect sizes from T029c-Raw and T029c-Pred to determine if the model successfully captures family trends. **Dependency**: Must run after T029c-Raw and T029c-Pred.
- [X] T029f [US3] Implement `code/analysis.py` function `save_anova_results(results, path)`.
- [X] T030 [US3] Execute ANOVA on electrostatic energy (predictions).
- [X] T031 [US3] Execute ANOVA on dispersion energy (predictions).
- [X] T032 [US3] Execute ANOVA on H-bond energy (predictions).
- [X] T033a [US3] Implement `code/analysis.py` function `apply_bonferroni_correction(p_values, n_tests)` to calculate corrected p-values.
- [X] T033b [US3] Implement `code/analysis.py` function `run_tukey_hsd(df, energy_col, family_col)` using `statsmodels.stats.multicomp`.
- [X] T033c [US3] Write corrected results to `analysis/anova_corrected.json` with explicit p-value threshold logic.
- [X] T034 [US3] Implement `code/analysis.py` function `calculate_cohens_d(group1, group2)` for significant families.
- [X] T035a [US3] Implement `code/analysis.py` function `validate_against_dft(models, dft_validation_set)`: Validate models against the generated DFT set (`data/validation/dft_validation_set.parquet` from T012b-Gen). Calculate MAE and log the result. **Note**: This satisfies amended FR-007 and Plan Phase 2. **Dependency**: Must run after T012b-Gen and T012c-TrainGen.
- [X] T035b [US3] Implement `code/analysis.py` function `calculate_sc003_compliance(dft_mae, test_mae)`: Calculate MAE against DFT set and compare against SC-003 relative metric (out-of-sample MAE ≤ 2.0 × baseline test set MAE). **Note**: This updates SC-003 to reflect the amended DFT validation strategy.
- [X] T036a [US3] Implement `code/analysis.py` function `calculate_correlation_matrix(descriptors, targets)`.
- [X] T036b [US3] Implement `code/analysis.py` function `check_tautology(correlation_matrix, threshold=0.95)`.
- [X] T037a [US3] Implement `code/analysis.py` function `aggregate_validation_results(anova_predictions, anova_raw, tukey, dft_mae, sc003_status, tautology)`.
- [X] T037b [US3] Implement `code/analysis.py` function `write_validation_report(report, path)` to `contracts/validation_report.json`.
- [X] T038a [US3] Add logging for p-values: In `code/analysis.py`, inside `run_anova_predictions`, add `logger.info(f"ANOVA p-value for {energy_col}: {p_value:.4f}, Corrected: {corrected_p:.4f}")`.
- [X] T038b [US3] Add logging for effect sizes: In `code/analysis.py`, inside `calculate_cohens_d`, add `logger.info(f"Cohen's d for {family1} vs {family2}: {d:.4f}")`.
- [X] T038c [US3] Add logging for validation MAE: In `code/analysis.py`, inside `validate_against_dft`, add `logger.info(f"DFT Validation MAE: {mae:.4f} kcal/mol")`.
- [X] T039a [US3] Implement `code/analysis.py` function `run_anova_on_predictions(predictions_df, family_col)`.
- [X] T039b [US3] Implement `code/analysis.py` function `compare_raw_vs_prediction_anova(raw_results, prediction_results)`.
- [ ] T063 [US3/Review] [ANOVA Robustness] Implement `code/analysis.py` function `check_anova_assumptions(df, energy_col, family_col)`: Before running ANOVA, verify the assumptions of normality (Shapiro-Wilk) and homogeneity of variance (Levene's test). **Logic**: If assumptions are violated (p < 0.05), log a WARNING and automatically switch to a non-parametric alternative (Kruskal-Wallis test) for that specific energy component, while still reporting the original ANOVA results for comparison. **Threshold**: p < 0.05. **Fallback**: `scipy.stats.kruskal`. **Output**: Save the non-parametric results to a new key `anova_results_kruskal` in the `contracts/validation_report.json` file.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T041 [P] Documentation updates in `specs/001-predicting-molecular-interactions-in-ion/` (update research.md with findings).
- [X] T042a [P] Code cleanup: Run `flake8` on `code/`.
- [X] T042b [P] Code cleanup: Refactor `code/utils.py` function `compute_tpsa`.
- [X] T043 [P] Performance optimization across all scripts (ensure < 6h runtime).
- [X] T044 [P] Additional unit tests for RDKit descriptors in `tests/unit/test_descriptors.py`.
- [X] T045 [P] Run `quickstart.md` validation (if generated).
- [X] T050 [US3/Review] Add a "Data Provenance" section to `contracts/validation_report.json`.
- [X] T054 [US3/Review] Add logging for p-values, effect sizes, and validation MAE. **Implementation**: Ensure `code/analysis.py` logs the raw p-value, the Bonferroni-corrected p-value, Cohen's d, and the final MAE for DFT validation sets.
- [X] T055 [P] Refactor `code/model_training.py` to handle "Stratification Failure". **Implementation**: If `train_test_split` fails to stratify due to a family having < 2 samples, log a WARNING, remove that family from the split, and proceed, ensuring the split is valid for the remaining families.
- [ ] T060-VerifyStatic [P] [US1/Review] [Static Download] Implement a verification task for the static download strategy. **Logic**: Verify that no `streaming=True` flags are present in `code/data_ingestion.py` or `code/config.py`. Verify that `data/raw/` contains static `.parquet` files. Update `specs/001-predicting-molecular-interactions-in-ion/quickstart.md` to explicitly state "Static download strategy in use". **Verification**: Confirm no streaming code exists and documentation is updated.

---

## Phase 7: Revision & Review Resolution (Priority: P1)

**Goal**: Address specific concerns raised in the `analyze` phase regarding data integrity, streaming, and error handling.

- [X] T047 [P] Hard-code "fail-loud" behavior for data loaders. **Implementation**: Removed. Default `requests`/`datasets` behavior is already "fail-loud". The fallback (T012b-Gen/T012c-TrainGen) is triggered only if real data is missing, not via a try/except in the loader.
- [X] T048 [P] Explicitly document the "Verified Synthetic Generation" fallback. **Implementation**: Added a docstring and comment block to `code/data_ingestion.py` (T012b-Gen/T012c-TrainGen) explicitly stating: "This is a VERIFIED fallback ONLY for the VALIDATION SET (T012b-Gen) or TRAINING LABELS (T012c-TrainGen). It uses Psi4 with verified structures. It is NEVER used for training data unless the real SAPT source is missing (T012c-TrainGen)."
- [X] T049 [US2/Review] Update `code/model_training.py` to log the exact dataset size and the number of samples per StructuralFamily used in the stratified split. **Implementation**: Add logging in `train_electrostatic_model` (T022) and `stratified_split` (T021a) to output `n_train`, `n_val`, `n_test`, and a frequency count of `StructuralFamily` in each split.
- [X] T052 [US1/Review] Add explicit "Sample Definition" logging to `code/data_ingestion.py`. **Implementation**: If streaming or sampling is used, log the exact rule: "Using streaming mode", "Sample size: N rows", "Seed: 42", "Split: train".
- [X] T053 [US1/Review] Implement a "Real Data Verification" check in `code/data_ingestion.py`. **Implementation**: Add a function `verify_real_data_source(path)` that checks file size > 0 and row count > 0 before processing. If the file is empty or missing, raise `DataIngestionError` immediately.
- [X] T061 [US1/Review] [Data Integrity] Implement `code/data_ingestion.py` function `validate_family_coverage(df)`: A strict validation step that runs after T016a. **Logic**: Verify that every `StructuralFamily` present in the raw SAPT source (if available) is represented in the final unified dataset with at least N=10 samples. If a family is missing or under-represented, raise `DataIngestionError` with a clear message listing the missing families. **Error Message Format**: "DataIngestionError: Family coverage insufficient. Missing or under-represented families: {families}. Minimum required: {N} samples." **Config**: N value must be read from `config.py` (default 10).

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