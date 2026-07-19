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
- [X] T004a [P] Create `contracts/ion_pair.schema.yaml` defining fields: `cation_id` (str), `anion_id` (str), `electrostatic_energy` (float), `dispersion_energy` (float), `hbond_energy` (float), `total_energy` (float), `tpsa` (float), `molecular_surface_area` (float), `hbond_count` (int), `morgan_fp` (array), `structural_family` (str), `polarizability` (float). **Note**: `partial_charge` is excluded from this schema as per Plan Phase 0, but calculated internally. Verify file is valid YAML and matches pandera schema requirements.
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
- [ ] T013c-Structures [P] [US1] Implement `code/data_ingestion.py` function `extract_structures_from_raw(config)`: Extract unique cation/anion SMILES from the source definitions in `code/config.py` (or generate a dummy set if no data exists) and save to `data/raw/il_structures.json`. **Note**: This task runs BEFORE unification to break circular dependency. Verify `data/raw/il_structures.json` exists and contains valid SMILES.
- [ ] T012a [P] [US1] Implement `code/data_ingestion.py` function `download_spice(url)`: **PRIMARY SOURCE**. Fetch SPICE dataset from `https://huggingface.co/datasets/spice-ml/spice` (split='train'). Save to `data/raw/spice.parquet`. Verify file exists and contains columns `cation_id`, `anion_id`, `smiles_cation`, `smiles_anion`, `structural_family`, `electrostatic_energy`, `dispersion_energy`, `hbond_energy`.
- [ ] T012b-Exp [P] [US1] Implement `code/data_ingestion.py` function `download_ilthermo_exp(url)`: **SPEC COMPLIANCE**. Fetch ILThermo experimental enthalpy of mixing data from ` (tag='v1.0'). Save to `data/validation/experimental_validation_set.parquet`. **Note**: This satisfies Spec FR-007/SC-003.
- [ ] T012b-DFT [P] [US1] Implement `code/data_ingestion.py` function `download_dft_validation(url)`: Fetch the Independent DFT Validation set from `https://huggingface.co/datasets/spice-ml/spice-validation` (split='test'). Save to `data/validation/dft_validation_set.parquet`. **Note**: This supplements Spec FR-007 (Experimental Enthalpy) with Constitution VI (DFT) validation.
- [X] T012c [P] Implement `code/data_ingestion.py` function `verify_checksum(file_path, expected_hash)` to validate downloaded data.
- [ ] T014 [P] [US1] Implement `code/data_ingestion.py` function `generate_synthetic_sapt()`: **FALLBACK ONLY**. Trigger "Verified Synthetic Generation" using `psi4` and `data/raw/il_structures.json`. **Logic**: Randomly select 50 IonPairs from the list in `data/raw/il_structures.json` using `seed=42`. Calculate SAPT components for these 50 pairs. Save to `data/raw/sapt_fallback.parquet`. Verify file exists and contains non-NaN energy values.
- [ ] T015 [US1] Implement `code/data_ingestion.py` function `calculate_partial_charges(df)`: Calculate Gasteiger partial charges using RDKit for internal consistency checks.
- [ ] T016 [US1] Implement `code/data_ingestion.py` function `engineer_features(df)`: Parse SMILES, compute TPSA, Molecular Surface Area, H-bond counts, and graph embeddings. **CRITICAL**: Drop the `partial_charge` column before saving.
- [ ] T017a [P] [US1] Implement `code/data_ingestion.py` function `select_data_source()`: **DATA SOURCE SELECTION**. Check if `data/raw/sapt.parquet` exists. If yes, use it as the primary source. If no, check if `data/raw/sapt_fallback.parquet` (from T014) exists. If yes, use the fallback. If neither, raise `DataIngestionError`. Return the path to the selected file.
- [ ] T017b [P] [US1] Implement `code/data_ingestion.py` function `merge_spice_sapt(spice_df, sapt_df)`: Merge SPICE and SAPT on `cation_id` and `anion_id`.
- [ ] T017c [P] [US1] Implement `code/data_ingestion.py` function `handle_missing_data(base_df, sapt_df, synth_df)`: **MISSING DATA HANDLING**. Identify rows where SAPT data is missing. If synthetic data is available, merge it and mark rows with a `source` flag ('sapt' or 'synthetic'). If no synthetic data, flag rows for exclusion.
- [ ] T017d [P] [US1] Implement `code/data_ingestion.py` function `filter_raw_sapt(df)`: Filter the unified dataset to extract the subset of data originating strictly from the SAPT source (where `source == 'sapt'`).
- [ ] T017e [P] [US1] Implement `code/data_ingestion.py` function `write_unified_dataset(df, path)` to save to `data/processed/unified_dataset.parquet`.
- [X] T018a [US1] Implement `code/data_ingestion.py` function `validate_unified_dataset(df, schema_path)` using `pandera`.
- [X] T018b [US1] Implement `code/data_ingestion.py` function `log_validation_errors(errors)` to write detailed errors to `logs/ingestion_errors.log`.

---

## Phase 3: User Story 1 - Data Ingestion and Feature Engineering (Priority: P1) 🎯 MVP

**Goal**: Ingest SPICE, ILThermo, and SAPT, engineer descriptors, and produce a unified dataset.

**Independent Test**: Run ingestion on a small subset of IonPairs. Verify `data/processed/unified_dataset.parquet` contains expected columns with no null values. **Note**: `partial_charge` column must NOT be present in final output.

- [X] T019 [US1] Add logging for ingestion steps and synthetic generation fallback. Update `code/data_ingestion.py` to log steps to `logs/ingestion.log`.

## Phase 4: User Story 2 - Model Training and Hyperparameter Optimization (Priority: P2)

**Goal**: Train three XGBoost regressors with Optuna, respecting strict CPU time limits.

**Independent Test**: Run training on a toy dataset with a timeout mechanism. Verify three `.pkl` model artifacts are saved and logs show best hyperparameters and trial timeouts.

- [ ] T021a [P] [US2] Implement `code/model_training.py` function `stratified_split(df, target_col, structural_family_col)`: Use `sklearn.model_selection.train_test_split` with ratios defined in `code/config.py`.
- [ ] T021b [P] [US2] Implement `code/model_training.py` function `save_splits(train_df, val_df, test_df)` to `data/processed/train.parquet`, `val.parquet`, `test.parquet`.
- [ ] T022 [US2] Implement `code/model_training.py` function `train_electrostatic_model(train_df, val_df)` using XGBoost.
- [ ] T023 [US2] Implement `code/model_training.py` function `train_dispersion_model(train_df, val_df)` using XGBoost.
- [ ] T024 [US2] Implement `code/model_training.py` function `train_hbond_model(train_df, val_df)` using XGBoost.
- [ ] T025a [US2] Implement `code/model_training.py` function `optuna_objective(trial, model_type, train_df, val_df)` defining search space for XGBoost hyperparameters.
- [ ] T025b [US2] Implement `code/model_training.py` function `run_optuna_study()` with `n_trials=60`, `timeout=300` seconds per trial, using `optuna.create_study`.
- [ ] T026 [US2] Implement `code/model_training.py` function `save_models(models, path_prefix)` to save model artifacts.
- [ ] T027 [US2] Implement `code/model_training.py` function `check_energy_consistency(predictions, total_sapt_targets, tolerance=0.1 kcal/mol)`.
- [ ] T028 [US2] Add logging for MAE on validation set and trial convergence status.
- [ ] T029a [US2] Implement `code/model_training.py` function `perform_sensitivity_analysis(study_results)` to calculate the variance of MAE across the top hyperparameter configurations.
- [ ] T029b [US2] Implement `code/model_training.py` function `log_sensitivity_results(results)` to write detailed sensitivity analysis to logs.

## Phase 5: User Story 3 - Systematic Variation Analysis and Validation (Priority: P3)

**Goal**: Perform ANOVA on raw SAPT data AND model predictions, apply corrections, validate against Independent DFT dataset and Experimental data, and report results.

- [ ] T029c [US3] Implement `code/analysis.py` function `run_anova(df, energy_col, family_col)` using `scipy.stats.f_oneway`.
- [ ] T029d [US3] Implement `code/analysis.py` function `save_anova_results(results, path)`.
- [X] T030 [US3] Execute ANOVA on electrostatic energy.
- [X] T031 [US3] Execute ANOVA on dispersion energy.
- [X] T032 [US3] Execute ANOVA on H-bond energy.
- [ ] T033a [US3] Implement `code/analysis.py` function `apply_bonferroni_correction(p_values, n_tests)` to calculate corrected p-values.
- [ ] T033b [US3] Implement `code/analysis.py` function `run_tukey_hsd(df, energy_col, family_col)` using `statsmodels.stats.multicomp`.
- [X] T033c [US3] Write corrected results to `analysis/anova_corrected.json` with explicit p-value threshold logic.
- [ ] T034 [US3] Implement `code/analysis.py` function `calculate_cohens_d(group1, group2)` for significant families.
- [ ] T035a [US3] Implement `code/analysis.py` function `validate_against_dft(models, dft_validation_set)`.
- [ ] T035b [US3] Implement `code/analysis.py` function `validate_against_experimental(models, experimental_validation_set)`.
- [ ] T035c [US3] Implement `code/analysis.py` function `calculate_sc003_compliance(dft_mae, test_mae, exp_mae)`.
- [ ] T036a [US3] Implement `code/analysis.py` function `calculate_correlation_matrix(descriptors, targets)`.
- [ ] T036b [US3] Implement `code/analysis.py` function `check_tautology(correlation_matrix, threshold=0.95)`.
- [ ] T037a [US3] Implement `code/analysis.py` function `aggregate_validation_results(anova_raw, tukey, dft_mae, exp_mae, sc003_status, tautology)`.
- [ ] T037b [US3] Implement `code/analysis.py` function `write_validation_report(report, path)` to `contracts/validation_report.json`.
- [ ] T038 [US3] Add logging for p-values, effect sizes, and validation MAE.
- [ ] T039a [US3] Implement `code/analysis.py` function `run_anova_on_predictions(predictions_df, family_col)`.
- [ ] T039b [US3] Implement `code/analysis.py` function `compare_raw_vs_prediction_anova(raw_results, prediction_results)`.

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T041 [P] Documentation updates in `specs/001-predicting-molecular-interactions-in-ion/` (update research.md with findings).
- [X] T042a [P] Code cleanup: Run `flake8` on `code/`.
- [X] T042b [P] Code cleanup: Refactor `code/utils.py` function `compute_tpsa`.
- [ ] T043 [P] Performance optimization across all scripts (ensure < 6h runtime).
- [X] T044 [P] Additional unit tests for RDKit descriptors in `tests/unit/test_descriptors.py`.
- [X] T045 [P] Run `quickstart.md` validation (if generated).

---

## Phase 7: Revision & Review Resolution (Priority: P1)

**Goal**: Address specific concerns raised in the `analyze` phase regarding data integrity, streaming, and error handling.

- [ ] T047 [P] Hard-code "fail-loud" behavior for data loaders.
- [ ] T048 [P] Explicitly document the "Verified Synthetic Generation" fallback.
- [ ] T049 [US2/Review] Update `code/model_training.py` to log the exact dataset size and the number of samples per StructuralFamily used in the stratified split.
- [X] T050 [US3/Review] Add a "Data Provenance" section to `contracts/validation_report.json`.
- [ ] T051a [P] Implement `code/data_ingestion.py` function `generate_large_sample_data(count=1000000)` to Create a test file of substantial size to evaluate system performance under realistic data loads..
- [ ] T051 [P] Implement streaming data loader in `code/data_ingestion.py`. **Dependency**: Must run after T051a to have test data.
- [ ] T052 [US1/Review] Add explicit "Sample Definition" logging to `code/data_ingestion.py`.
- [ ] T053 [US1/Review] Implement a "Real Data Verification" check in `code/data_ingestion.py`.
- [ ] T054 [US3/Review] Add logging for p-values, effect sizes, and validation MAE.
- [ ] T055 [P] Refactor `code/model_training.py` to handle "Stratification Failure".
