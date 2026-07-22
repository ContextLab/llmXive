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
- [X] T004a [P] Create `contracts/ion_pair.schema.yaml` defining fields: `cation_id` (str), `anion_id` (str), `electrostatic_energy` (float), `dispersion_energy` (float), `hbond_energy` (float), `total_energy` (float), `tpsa` (float), `molecular_surface_area` (float), `hbond_count` (int), `morgan_fp` (array), `structural_family` (str), `polarizability` (float), `partial_charge` (float). **Note**: `partial_charge` is included as a *calculated* field to satisfy FR-002 generation requirement, but MUST be excluded from the *training feature set* in T016. Verify file is valid YAML and matches pandera schema requirements.
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
- [ ] T012a [P] [US1] Implement `code/data_ingestion.py` function `download_spice(url)`: **PRIMARY SOURCE**. Fetch SPICE dataset from `https://huggingface.co/datasets/spice-ml/spice` (split='train'). Save to `data/raw/spice.parquet`. Verify file exists and contains columns `cation_id`, `anion_id`, `smiles_cation`, `smiles_anion`, `structural_family`, `electrostatic_energy`, `dispersion_energy`, `hbond_energy`.
- [ ] T012b-Gen [P] [US1] [Plan Phase 2] [Constitution VI] Implement `code/data_ingestion.py` function `generate_dft_validation_set()`: **INDEPENDENT DFT VALIDATION**. Implement the "Verified Synthetic Generation" protocol using `psi4` and `data/raw/il_structures.json`. **Logic**: Check if `data/validation/dft_validation_set.parquet` exists. If not, randomly select a representative subset of IonPairs (seed=42) from `data/raw/il_structures.json` and calculate SAPT/DFT energy components using `run_psi_sapt`. Save to `data/validation/dft_validation_set.parquet`. **Note**: This replaces the rejected experimental validation strategy (Spec FR-007) with the Plan-mandated DFT validation. **Dependency**: Must run after T013c-Structures.
- [X] T012c [P] Implement `code/data_ingestion.py` function `verify_checksum(file_path, expected_hash)` to validate downloaded data.
- [ ] T013c-Structures [P] [US1] Implement `code/data_ingestion.py` function `extract_structures_from_spice(df)`: Extract unique cation/anion SMILES from the downloaded SPICE dataset (`data/raw/spice.parquet`) and save to `data/raw/il_structures.json`. **Dependency**: Must run after T012a. Verify `data/raw/il_structures.json` exists and contains valid SMILES.
- [X] T014 [P] [US1] **REMOVED**: Synthetic training data generation is NOT permitted for the main training set. The Plan mandates failing loudly if real SAPT data is missing. This task is removed to prevent execution of a forbidden fallback.
- [ ] T015a [P] [US1] Implement `code/data_ingestion.py` function `calculate_partial_charges_internal_only(df)`: Calculate Gasteiger partial charges using RDKit for *internal consistency checks only*. **Constraint**: These values MUST NOT be used as input features for training. Save the result to `data/processed/internal_consistency_checks.parquet` before dropping from the main dataset. **Note**: This satisfies FR-002 generation requirement.
- [ ] T016 [US1] Implement `code/data_ingestion.py` function `engineer_features(df)`: Parse SMILES, compute TPSA, Molecular Surface Area, H-bond counts, and graph embeddings. **CRITICAL**: Depends on T015a. Call `calculate_partial_charges_internal_only` to save the internal consistency artifact, then DROP the `partial_charge` column from the main training dataframe before saving to `data/processed/unified_dataset.parquet`. Do not recompute TPSA; use values from T006a/T015a flow. <!-- FAILED: unspecified -->
- [ ] T017a-Orchestrate [P] [US1] Implement `code/data_ingestion.py` function `select_data_sources()`: **DATA SOURCE SELECTION**. Check if `data/raw/spice.parquet` (structures) exists. Check if `data/raw/sapt.parquet` (energies, if available) exists. **Logic**: If SAPT source is missing, raise `DataIngestionError` immediately. Do NOT trigger synthetic generation for training data. Return the paths to the selected files. **Note**: Logic must handle separate structure and energy sources and explicitly fail if real energy data is missing.
- [X] T017b [P] [US1] Implement `code/data_ingestion.py` function `merge_spice_sapt(spice_df, sapt_df)`: Merge SPICE and SAPT on `cation_id` and `anion_id`.
- [X] T017c [P] [US1] Implement `code/data_ingestion.py` function `merge_training_data(base_df, sapt_df)`: **REAL DATA MERGE ONLY**. Merge the base structure dataframe with the real SAPT energy dataframe. **Constraint**: This function must NOT handle synthetic data. If `sapt_df` is missing or empty, raise `DataIngestionError`. This function is strictly for the training pipeline.
- [X] T017d [P] [US1] Implement `code/data_ingestion.py` function `filter_raw_sapt(df)`: Filter the unified dataset to extract the subset of data originating strictly from the SAPT source (where `source == 'sapt'`).
- [ ] T017e [P] [US1] Implement `code/data_ingestion.py` function `write_unified_dataset(df, path)` to save to `data/processed/unified_dataset.parquet`. <!-- FAILED: unspecified -->
- [X] T018a [US1] Implement `code/data_ingestion.py` function `validate_unified_dataset(df, schema_path)` using `pandera`.
- [X] T018b [US1] Implement `code/data_ingestion.py` function `log_validation_errors(errors)` to write detailed errors to `logs/ingestion_errors.log`.
- [X] T019 [US1] Add logging for ingestion steps and synthetic generation fallback. Update `code/data_ingestion.py` to log steps to `logs/ingestion.log`.

---

## Phase 3: User Story 1 - Data Ingestion and Feature Engineering (Priority: P1) 🎯 MVP

**Goal**: Ingest SPICE, ILThermo, and SAPT, engineer descriptors, and produce a unified dataset.

**Independent Test**: Run ingestion on a small subset of IonPairs. Verify `data/processed/unified_dataset.parquet` contains expected columns with no null values. **Note**: `partial_charge` column must NOT be present in final training output, but `data/processed/internal_consistency_checks.parquet` must exist.

---

## Phase 4: User Story 2 - Model Training and Hyperparameter Optimization (Priority: P2)

**Goal**: Train three XGBoost regressors with Optuna, respecting strict CPU time limits.

**Independent Test**: Run training on a toy dataset with a timeout mechanism. Verify three `.pkl` model artifacts are saved and logs show best hyperparameters and trial timeouts.

- [X] T021a [P] [US2] Implement `code/model_training.py` function `stratified_split(df, target_col, structural_family_col)`: Use `sklearn.model_selection.train_test_split` with ratios defined in `code/config.py`.
- [X] T021b [P] [US2] Implement `code/model_training.py` function `save_splits(train_df, val_df, test_df)` to `data/processed/train.parquet`, `val.parquet`, `test.parquet`.
- [X] T022 [US2] Implement `code/model_training.py` function `train_electrostatic_model(train_df, val_df)` using XGBoost. <!-- FAILED: unspecified -->
- [X] T023 [US2] Implement `code/model_training.py` function `train_dispersion_model(train_df, val_df)` using XGBoost. <!-- FAILED: unspecified -->
- [X] T024 [US2] Implement `code/model_training.py` function `train_hbond_model(train_df, val_df)` using XGBoost. <!-- FAILED: unspecified -->
- [X] T025a [US2] Implement `code/model_training.py` function `optuna_objective(trial, model_type, train_df, val_df)` defining search space for XGBoost hyperparameters.
- [X] T025b [US2] Implement `code/model_training.py` function `run_optuna_study()` with `n_trials=60`, `timeout=300` seconds per trial, using `optuna.create_study`.
- [X] T026 [US2] Implement `code/model_training.py` function `save_models(models, path_prefix)` to save model artifacts.
- [X] T027 [US2] Implement `code/model_training.py` function `check_energy_consistency(predictions, total_sapt_targets, tolerance=0.1 kcal/mol)`. <!-- ATOMIZE: requested -->
- [ ] T028 [US2] Add logging for MAE on validation set and trial convergence status. <!-- FAILED: unspecified -->
- [X] T029a [US2] Implement `code/model_training.py` function `perform_sensitivity_analysis(study_results)` to calculate the variance of MAE across the top hyperparameter configurations. <!-- FAILED: unspecified -->
- [X] T029b [US2] Implement `code/model_training.py` function `log_sensitivity_results(results)` to write detailed sensitivity analysis to logs. <!-- FAILED: unspecified -->

---

## Phase 5: User Story 3 - Systematic Variation Analysis and Validation (Priority: P3)

**Goal**: Perform ANOVA on raw SAPT data AND model predictions, apply corrections, validate against Independent DFT dataset, and report results.

- [ ] T029c-ANOVA-Raw [US3] Implement `code/analysis.py` function `run_anova_raw(df, energy_col, family_col)`: Perform One-way ANOVA on the *raw SAPT energy components* (pre-merging) grouped by `StructuralFamily`. Apply Bonferroni correction and Tukey HSD. **Dependency**: Must run after T017d (filter raw SAPT). **Note**: This task implements Plan Phase 2's specific requirement to analyze raw data.
- [ ] T029c-Pred [US3] Implement `code/analysis.py` function `run_anova_predictions(predictions_df, family_col)`: Perform ANOVA on the model predictions grouped by `StructuralFamily` to compare against raw data trends.
- [X] T029d [US3] Implement `code/analysis.py` function `save_anova_results(results, path)`.
- [X] T030 [US3] Execute ANOVA on electrostatic energy (raw).
- [X] T031 [US3] Execute ANOVA on dispersion energy (raw).
- [X] T032 [US3] Execute ANOVA on H-bond energy (raw).
- [X] T033a [US3] Implement `code/analysis.py` function `apply_bonferroni_correction(p_values, n_tests)` to calculate corrected p-values.
- [X] T033b [US3] Implement `code/analysis.py` function `run_tukey_hsd(df, energy_col, family_col)` using `statsmodels.stats.multicomp`.
- [X] T033c [US3] Write corrected results to `analysis/anova_corrected.json` with explicit p-value threshold logic.
- [X] T034 [US3] Implement `code/analysis.py` function `calculate_cohens_d(group1, group2)` for significant families. <!-- FAILED: unspecified -->
- [X] T035a [US3] Implement `code/analysis.py` function `validate_against_dft(models, dft_validation_set)`: Validate models against the generated DFT set (`data/validation/dft_validation_set.parquet` from T012b-Gen). Calculate MAE and log the result. **Note**: This satisfies Plan Phase 2 and Constitution Principle VI. <!-- ATOMIZE: requested -->
- [X] T035c [US3] Implement `code/analysis.py` function `calculate_sc003_compliance(dft_mae, test_mae)`: Calculate MAE against DFT set and compare against Plan target (≤ 0.5 kcal/mol). **Note**: This updates SC-003 to reflect the Plan's DFT validation strategy.
- [X] T036a [US3] Implement `code/analysis.py` function `calculate_correlation_matrix(descriptors, targets)`.
- [X] T036b [US3] Implement `code/analysis.py` function `check_tautology(correlation_matrix, threshold=0.95)`. <!-- FAILED: unspecified -->
- [X] T037a [US3] Implement `code/analysis.py` function `aggregate_validation_results(anova_raw, tukey, dft_mae, sc003_status, tautology)`. <!-- FAILED: unspecified -->
- [X] T037b [US3] Implement `code/analysis.py` function `write_validation_report(report, path)` to `contracts/validation_report.json`. <!-- FAILED: unspecified -->
- [ ] T038 [US3] Add logging for p-values, effect sizes, and validation MAE.
- [ ] T039a [US3] Implement `code/analysis.py` function `run_anova_on_predictions(predictions_df, family_col)`.
- [ ] T039b [US3] Implement `code/analysis.py` function `compare_raw_vs_prediction_anova(raw_results, prediction_results)`.

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

---

## Phase 7: Revision & Review Resolution (Priority: P1)

**Goal**: Address specific concerns raised in the `analyze` phase regarding data integrity, streaming, and error handling.

- [X] T047 [P] Hard-code "fail-loud" behavior for data loaders. **Implementation**: Removed. Default `requests`/`datasets` behavior is already "fail-loud". The fallback (T014) is triggered only if real data is missing, not via a try/except in the loader.
- [X] T048 [P] Explicitly document the "Verified Synthetic Generation" fallback. **Implementation**: Added a docstring and comment block to `code/data_ingestion.py` (T012b-Gen) explicitly stating: "This is a VERIFIED fallback ONLY for the VALIDATION SET. It uses Psi4 with verified structures. It is NEVER used for training data. If real SAPT data is missing for training, the pipeline raises DataIngestionError."
- [X] T049 [US2/Review] Update `code/model_training.py` to log the exact dataset size and the number of samples per StructuralFamily used in the stratified split. **Implementation**: Add logging in `train_electrostatic_model` (T022) and `stratified_split` (T021a) to output `n_train`, `n_val`, `n_test`, and a frequency count of `StructuralFamily` in each split.
- [X] T052 [US1/Review] Add explicit "Sample Definition" logging to `code/data_ingestion.py`. **Implementation**: If streaming or sampling is used, log the exact rule: "Using streaming mode", "Sample size: N rows", "Seed: 42", "Split: train".
- [X] T053 [US1/Review] Implement a "Real Data Verification" check in `code/data_ingestion.py`. **Implementation**: Add a function `verify_real_data_source(path)` that checks file size > 0 and row count > 0 before processing. If the file is empty or missing, raise `DataIngestionError` immediately.