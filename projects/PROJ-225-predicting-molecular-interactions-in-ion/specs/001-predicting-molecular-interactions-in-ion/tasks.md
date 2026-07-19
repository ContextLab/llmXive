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

- [X] T002a [P] Create `code/requirements.txt` with pinned versions: `xgboost==2.0.3`, `optuna==3.5.0`, `rdkit==2023.9.5`, `pandas==2.1.4`, `scikit-learn==1.3.2`, `pyarrow==14.0.2`, `requests==2.31.0`, `pyyaml==6.0.1`, `psi4==1.8.1`, `statsmodels==0.14.1`, `pandera==0.17.2`. **Install Command**: `venv/bin/pip install -r code/requirements.txt`. Verify `venv/bin/python` exists and `pip list` shows required packages.
- [X] T002b [P] Setup Python virtual environment: Create `scripts/setup_venv.sh` that creates the venv and installs requirements. Verify `venv/bin/python` exists and `pip list` shows required packages.
- [X] T004a [P] Create `contracts/ion_pair.schema.yaml` defining fields: `cation_id` (str), `anion_id` (str), `electrostatic_energy` (float), `dispersion_energy` (float), `hbond_energy` (float), `total_energy` (float), `tpsa` (float), `molecular_surface_area` (float), `hbond_count` (int), `morgan_fp` (array), `structural_family` (str). **Note**: `partial_charge` is excluded from this schema as per Plan Phase 0. Verify file is valid YAML and matches pandera schema requirements.
- [X] T004b [P] Create `contracts/validation_report.schema.yaml` defining fields: `anova_results` (object), `tukey_hsd` (object), `dft_validation_mae` (float), `experimental_validation_mae` (float), `sc003_compliance` (bool), `experimental_validation_status` (str), `tautology_check` (object). Verify file is valid YAML and matches pandera schema requirements.
- [X] T005a [P] Implement `code/config.py` defining `SEED=42`, `DATA_PATHS` (dict), `HYPERPARAM_BOUNDS` (dict), `MAX_TRIALS=60`, `TRIAL_TIMEOUT=300` (seconds), `TRAIN_RATIO=0.7`, `VAL_RATIO=0.15`, `TEST_RATIO=0.15`.
- [X] T005b [P] Implement `.env.example` and `code/config.py` loading logic using `python-dotenv` to override defaults.
- [X] T006a [P] Implement `code/utils.py` with functions: `compute_tpsa(smiles)`, `compute_morgan_fp(smiles, radius=2, n_bits=2048)`, `compute_hbond_count(smiles)`.
- [X] T006b [P] Implement `code/utils.py` with function: `run_psi_sapt(structure_file, method='sapt', basis='jun-cc-pVDZ')` returning energy components.
- [X] T008a [P] Implement `code/utils.py` logging configuration: `logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO, handlers=[logging.FileHandler('logs/pipeline.log')])`.
- [X] T008b [P] Implement `code/utils.py` custom exception hierarchy: `DataIngestionError`, `ModelTrainingError`, `AnalysisError`.
- [X] T009a [P] Create `code/.env.example` with `SPICE_URL`, `IL_SAPT_URL`, `DFT_VALIDATION_URL`. Verify file exists and contains these keys.
- [X] T009b [P] Implement `code/config.py` to load `.env` and validate required keys exist, raising `DataIngestionError` if missing.
- [X] T013c-Structures [P] [US1] Implement `code/data_ingestion.py` function `extract_structures_from_raw(df, source_type)`: Extract unique cation/anion SMILES from raw sources (SPICE or ILThermo) and save to `data/raw/il_structures.json`. **Dependency**: T012a (SPICE) or T013 (ILThermo). **Note**: This task runs BEFORE unification to break circular dependency. Verify `data/raw/il_structures.json` exists and contains valid SMILES.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Feature Engineering (Priority: P1) 🎯 MVP

**Goal**: Ingest SPICE (Primary per Plan) and ILThermo/SAPT (Secondary), engineer descriptors, and produce a unified, schema-validated training dataset. **Note**: Partial charges are calculated for internal checks but EXCLUDED from model input per Plan Phase 0.

**Independent Test**: Run ingestion on a small subset of IonPairs. Verify `data/processed/unified_dataset.parquet` contains expected columns (cation_id, anion_id, electrostatic_energy, dispersion_energy, hbond_energy, tpsa, molecular_surface_area, hbond_count, graph_embedding, structural_family) with no null values in critical columns. **Note**: `partial_charge` column must NOT be present in final output.

> **TDD Note**: The task list order reflects TDD workflow: Tests (T010, T011) are written FIRST, before implementation (T012-T019). This ensures tests fail initially and pass after implementation.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Contract test for unified dataset schema in `tests/contract/test_ion_pair_schema.py` using `pandera`. Specific test function: `test_ion_pair_schema_validates_nulls`.
- [X] T011 [P] [US1] Integration test for data pipeline on samples in `tests/integration/test_ingestion_small.py`. Specific test function: `test_ingestion_pipeline_small_subset`.

### Implementation for User Story 1

- [X] T012a [P] [US1] Implement `code/data_ingestion.py` function `download_spice(url)`: **PRIMARY SOURCE**. Fetch SPICE dataset from ` (split='train'). Save to `data/raw/spice.parquet`. **Plan Override**: This supersedes Spec FR-001's ILThermo requirement as per Plan Summary. Verify file exists and contains columns `cation_id`, `anion_id`, `smiles_cation`, `smiles_anion`, `structural_family`, `electrostatic_energy`, `dispersion_energy`, `hbond_energy`.
- [X] T012b-DFT [P] [US1] Implement `code/data_ingestion.py` function `download_dft_validation(url)`: Fetch the Independent DFT Validation set from `. Save to `data/validation/dft_validation_set.parquet`. **Plan Override**: This replaces Spec FR-007 (Experimental Enthalpy) which is deemed scientifically invalid per Plan Summary. **Verification**: Ensure file contains 20 IonPairs with DFT energy components. Raise `DataIngestionError` if fetch fails.
- [X] T012c [P] [US1] Implement `code/data_ingestion.py` function `verify_checksum(file_path, expected_hash)` to validate downloaded data.
- [X] T013 [P] [US1] Implement `code/data_ingestion.py` function `download_sapt(url)`: **SECONDARY SOURCE**. Fetch curated SAPT/DFT repository from ` (tag='v1.0'). Save to `data/raw/sapt.parquet`. **Plan Override**: This is secondary to SPICE per Plan Summary. Verify file exists and contains columns `cation_id`, `anion_id`, `electrostatic_energy`, `dispersion_energy`, `hbond_energy`, `total_energy`. Raise `DataIngestionError` if download fails.
- [X] T014 [US1] Implement `code/data_ingestion.py` function `generate_synthetic_sapt(structures_file, count=50)`: **FALLBACK ONLY**. Trigger "Verified Synthetic Generation" using `psi4` and `data/raw/il_structures.json` **ONLY IF** T013 (IL-SAPT) fails to provide energy components for specific ion pairs. **Selection Logic**: Select the first 50 IonPairs from `structures_file` missing energy components. Save to `data/raw/sapt_synth.parquet`. **Verification**: Log `psi4` version and parameters. Raise `DataIngestionError` if `psi4` fails.
- [X] T015 [US1] Implement `code/data_ingestion.py` function `calculate_partial_charges(df)`: Calculate Gasteiger partial charges using RDKit for internal consistency checks. **Note**: These are calculated but **EXCLUDED** from the final model input features per Plan Phase 0. Store in `partial_charge` column temporarily.
- [X] T017a [US1] Implement `code/data_ingestion.py` function `unify_datasets(spice_df, sapt_df, synth_df)`: **Primary Path**: Join SPICE (T012a) with SAPT (T013) on `cation_id` and `anion_id`. **Fallback**: If SAPT is missing, use Synthetic (T014). **Dependency**: Requires T012a, T013, T014, and T013c-Structures. **Output**: Unified dataframe with all energy components.
- [X] T016 [US1] Implement `code/data_ingestion.py` function `engineer_features(df)`: Parse SMILES, compute TPSA, Molecular Surface Area, H-bond counts, and Morgan fingerprints. **CRITICAL**: **DROP** the `partial_charge` column before saving (as per Plan Phase 0 exclusion). Save to `data/processed/unified_dataset.parquet`. **Verification Requirement**: Verify output `data/processed/unified_dataset.parquet` contains **EXACTLY** these columns: `cation_id`, `anion_id`, `electrostatic_energy`, `dispersion_energy`, `hbond_energy`, `total_energy`, `tpsa`, `molecular_surface_area`, `hbond_count`, `morgan_fp`, `structural_family`. **Dependency**: Requires T017a to have produced the unified dataset and T015 to have calculated charges (for internal check only).
- [X] T017b [US1] Implement `code/data_ingestion.py` function `write_unified_dataset(df, path)` to save to `data/processed/unified_dataset.parquet`. Verify file exists, is readable by pandas, and matches schema `contracts/ion_pair.schema.yaml`.
- [X] T017c [US1] Implement `code/data_ingestion.py` function `filter_raw_sapt(df)` to extract the subset of data originating strictly from the SAPT source (T013) into `data/processed/raw_sapt_subset.parquet`. This artifact is required for ANOVA analysis (T029).
- [X] T018a [US1] Implement `code/data_ingestion.py` function `validate_unified_dataset(df, schema_path)` using `pandera`.
- [X] T018b [US1] Implement `code/data_ingestion.py` function `log_validation_errors(errors)` to write detailed errors to `logs/ingestion_errors.log`.
- [X] T019 [US1] Add logging for ingestion steps and synthetic generation fallback. Update `code/data_ingestion.py` to log steps to `logs/ingestion.log`. Verify log file exists and contains entries for exact strings: 'Downloading SPICE', 'Downloading SAPT', 'Unifying datasets', 'Validating schema', 'Excluding partial charges'.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Hyperparameter Optimization (Priority: P2)

**Goal**: Train three XGBoost regressors (Electrostatic, Dispersion, H-bond) with Optuna tuning, respecting strict CPU time limits.

**Independent Test**: Run training on a toy dataset with a timeout mechanism. Verify three `.pkl` model artifacts are saved and logs show best hyperparameters and trial timeouts.

### Implementation for User Story 2

- [X] T021a [P] [US2] Implement `code/model_training.py` function `stratified_split(df, target_col, structural_family_col)`: Use `sklearn.model_selection.train_test_split` with ratios defined in `code/config.py` (`TRAIN_RATIO=0.7`, `VAL_RATIO=0.15`, `TEST_RATIO=0.15`). Verify split is stratified by `StructuralFamily`.
- [X] T021b [P] [US2] Implement `code/model_training.py` function `save_splits(train_df, val_df, test_df)` to `data/processed/train.parquet`, `val.parquet`, `test.parquet`.
- [X] T022 [US2] Implement `code/model_training.py` function `train_electrostatic_model(train_df, val_df)` using XGBoost.
- [X] T023 [US2] Implement `code/model_training.py` function `train_dispersion_model(train_df, val_df)` using XGBoost.
- [X] T024 [US2] Implement `code/model_training.py` function `train_hbond_model(train_df, val_df)` using XGBoost. Verify model file `models/hbond.pkl` exists and can be loaded by `joblib`/`pickle` without error.
- [X] T025a [US2] Implement `code/model_training.py` function `optuna_objective(trial, model_type, train_df, val_df)` defining search space for XGBoost hyperparameters (max_depth, eta, gamma, etc.). Verify function returns a float (loss) when called with a mock trial and dummy data.
- [X] T025b [US2] Implement `code/model_training.py` function `run_optuna_study()` with `n_trials=60`, `timeout=300` seconds per trial, using `optuna.create_study`. Verify it creates a study, runs trials, and saves best params to `models/hyperparams.json`.
- [X] T026 [US2] Implement `code/model_training.py` function `save_models(models, path_prefix)` to save `models/electrostatic.pkl`, `models/dispersion.pkl`, `models/hbond.pkl` and hyperparameter logs. Verify `models/electrostatic.pkl`, `models/dispersion.pkl`, `models/hbond.pkl` exist and `models/hyperparams.json` contains the best params.
- [X] T027 [US2] Implement `code/model_training.py` function `check_energy_consistency(predictions, total_sapt_targets, tolerance=0.1 kcal/mol)` where **both predictions and targets are in kcal/mol**. Write result to `models/consistency_log.json` with pass/fail status. Verify `models/consistency_log.json` is created with pass/fail status and the sum of predictions approximates targets within tolerance.
- [X] T028 [US2] Add logging for MAE on validation set and trial convergence status. Update `code/model_training.py` to log MAE and trial status to `logs/training.log`. Verify log contains entries for each trial and final MAE.
- [X] T029a [US2] Implement `code/model_training.py` function `perform_sensitivity_analysis(study_results)` to calculate the variance of MAE across the top hyperparameter configurations. Write result to `models/sensitivity_analysis.json`. **Verification**: Ensure variance < 0.1 kcal/mol as per SC-005.
- [X] T029b [US2] Implement `code/model_training.py` function `log_sensitivity_results(results)` to write detailed sensitivity analysis to `logs/sensitivity.log`. Verify log contains variance metrics.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Systematic Variation Analysis and Validation (Priority: P3)

**Goal**: Perform ANOVA on raw SAPT data and model predictions, apply corrections, validate against Independent DFT dataset (Plan Override), and report results.

**Independent Test**: Run analysis on test set predictions and the DFT validation set. Verify `contracts/validation_report.json` contains ANOVA p-values, Tukey HSD results, and DFT MAE.

> **Dependencies Note**: Tasks T029-T034 (ANOVA on raw data) are **independent** of US2 (models) and can run in parallel. Tasks T035a-T037 (Model Validation) **depend** on US2 (models) and must wait for US2 completion.

### Implementation for User Story 3

- [X] T029a [P] [US3] Implement `code/analysis.py` function `run_anova(df, energy_col, family_col)` using `scipy.stats.f_oneway`. **Input**: `df` MUST be the `raw_sapt_subset.parquet` from T017c. **Dependency**: T017c. **Verification**: Check if `data/processed/raw_sapt_subset.parquet` exists; if not, raise `DataIngestionError`. Verify it returns a dictionary with F-statistic and p-value, and can be called on a mock dataframe.
- [X] T029b [P] [US3] Implement `code/analysis.py` function `save_anova_results(results, path)` to `analysis/anova_electrostatic.json`, `analysis/anova_dispersion.json`, `analysis/anova_hbond.json`. Verify `analysis/anova_electrostatic.json` (and others) are created and contain valid JSON with expected keys.
- [X] T030 [US3] Execute ANOVA on electrostatic energy. Verify `analysis/anova_electrostatic.json` is updated with results.
- [X] T031 [US3] Execute ANOVA on dispersion energy. Verify `analysis/anova_dispersion.json` is updated.
- [X] T032 [US3] Execute ANOVA on H-bond energy. Verify `analysis/anova_hbond.json` is updated.
- [X] T033a [US3] Implement `code/analysis.py` function `apply_bonferroni_correction(p_values, n_tests)` to calculate corrected p-values. Verify it returns corrected p-values and handles edge cases (e.g., p=0, p=1).
- [X] T033b [US3] Implement `code/analysis.py` function `run_tukey_hsd(df, energy_col, family_col)` using `statsmodels.stats.multicomp`. Verify it returns a result object with significant groups and can be called on mock data.
- [X] T033c [US3] Write corrected results to `analysis/anova_corrected.json` with explicit p-value threshold logic. **Definition**: `N_tests` = number of structural families * 3 (energy components). Target threshold = 0.01 / N_tests. Verify file exists and contains corrected p-values and threshold logic.
- [X] T034 [US3] Implement `code/analysis.py` function `calculate_cohens_d(group1, group2)` for significant families. Verify it returns a float effect size and handles empty groups.
- [X] T035a [US3] [Plan-Modified] Implement `code/analysis.py` function `validate_against_dft(models, dft_validation_set)`: Compare model predictions against `data/validation/dft_validation_set.parquet` (ingested in T012b-DFT). Calculate MAE and write to `analysis/dft_validation.json`. **Dependency**: T012b-DFT must have produced this file. **Note**: This is the primary validation per Plan. Verify `analysis/dft_validation.json` is created with MAE and matches schema.
- [X] T035b [US3] [Plan-Modified] Implement `code/analysis.py` function `calculate_sc003_compliance(dft_mae, test_mae)`: Verify if `dft_mae <= 2.0 * test_mae`. Write result to `analysis/sc003_compliance.json`. **Note**: Replaces experimental validation per Plan.
- [X] T036a [US3] Implement `code/analysis.py` function `calculate_correlation_matrix(descriptors, targets)`. Verify it returns a correlation matrix and handles NaNs.
- [X] T036b [US3] Implement `code/analysis.py` function `check_tautology(correlation_matrix, threshold=0.95)` to flag if any descriptor-target correlation > threshold; write to `analysis/tautology_report.json`. Verify `analysis/tautology_report.json` is created with pass/fail status based on threshold.
- [X] T037a [US3] Implement `code/analysis.py` function `aggregate_validation_results(anova, tukey, dft_mae, sc003_status, tautology)`. Verify it aggregates inputs into a single report object.
- [X] T037b [US3] Implement `code/analysis.py` function `write_validation_report(report, path)` to `contracts/validation_report.json` per schema. Verify `contracts/validation_report.json` is created and matches `contracts/validation_report.schema.yaml`.
- [X] T038 [US3] Add logging for p-values, effect sizes, and validation MAE. Update `code/analysis.py` to log p-values and effect sizes to `logs/analysis.log`. Verify log contains these entries.
- [X] T039a [US3] Implement `code/analysis.py` function `run_anova_on_predictions(predictions_df, family_col)` to perform ANOVA on model predictions grouped by family. **Dependency**: US2 models.
- [X] T039b [US3] Implement `code/analysis.py` function `save_prediction_anova_results(results)` to `analysis/anova_predictions.json`.
- [X] T039c [US3] Implement `code/analysis.py` function `compare_raw_vs_prediction_anova(raw_results, prediction_results)` to highlight differences.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 0 (Revised): Data Ingestion Fallback & Validation Set Generation

**Purpose**: Handle missing primary data and generate validation sets early in the pipeline.

- [X] T039d [US1] [Plan-Modified] Implement `code/data_ingestion.py` function `generate_dft_validation_set(structures_df)`: **FALLBACK ONLY**. Execute **ONLY IF** T013 (IL-SAPT) fails to provide sufficient data. Use `psi4` to calculate SAPT/DFT energies for a hold-out set. **Count**: Generate a set of structures (random seed). Save to `data/validation/dft_validation_set.parquet`. **Dependency**: T013c-Structures. **Note**: This task is moved to Phase 0 to ensure data is available before Model Training. Verify file exists and contains 20 entries.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T041 [P] Documentation updates in `specs/001-predicting-molecular-interactions-in-ion/` (update research.md with findings). Update `specs/001-predicting-molecular-interactions-in-ion/research.md` with findings from ANOVA and DFT validation. Verify file is updated with specific sections.
- [X] T042a [P] Code cleanup: Run `flake8` on `code/` to identify unused imports. Remove unused imports from `code/utils.py`. Verify `flake8` passes.
- [X] T042b [P] Code cleanup: Refactor `code/utils.py` function `compute_tpsa` to use RDKit's vectorized `Descriptors.TPSA` on a DataFrame of SMILES. Verify a significant speedup on 10k rows.
- [X] T043 [P] Performance optimization across all scripts (ensure < 6h runtime). Profile `code/model_training.py` using `cProfile`: `python -m cProfile -o logs/profile.prof code/model_training.py`. **Target**: Ensure total runtime < 6h on 2-core CPU. If > 5.5h, reduce MAX_TRIALS from 60 to 30 in `code/config.py`. Verify runtime is < 6h on a standard runner.
- [X] T044 [P] Additional unit tests for RDKit descriptors in `tests/unit/test_descriptors.py`.
- [X] T045 [P] Run `quickstart.md` validation (if generated). Execute `quickstart.md` instructions. Verify all steps complete successfully and no errors are logged.

---

## Phase 7: Revision & Review Resolution (Priority: P1)

**Goal**: Address specific concerns raised in the `analyze` phase regarding data integrity, streaming, and error handling.

**Independent Test**: Re-run the data ingestion pipeline on a large dataset to verify streaming behavior and error handling without synthetic fallbacks.

### Implementation for Revision Concerns

- [X] T047 [P] [US1/Review] Hard-code "fail-loud" behavior for data loaders in `code/data_ingestion.py`. Remove any `try/except` blocks that fallback to `generate_synthetic_*` or mock data. If `download_spice` or `download_sapt` fails (network error, 404, checksum mismatch), the script MUST raise `DataIngestionError` and halt execution. Verify that a simulated network failure (mock `requests` library to raise `ConnectionError`) causes the script to exit with a non-zero code and an error log, rather than proceeding with dummy data.
- [X] T048 [P] [US1/Review] Explicitly document the "Verified Synthetic Generation" fallback in `code/data_ingestion.py` and `plan.md`. Ensure the fallback ONLY triggers if the *verified* IL-SAPT URL returns 404/403, not on network glitches. Add a check to verify the `psi4` calculation produces valid energy values (non-NaN, non-infinite) before accepting the synthetic data. **CRITICAL**: Verify and log the `psi4` version and calculation parameters (method='sapt', basis='jun-cc-pVDZ') to satisfy Constitution Principle II (Verified Accuracy) for synthetic data. If `psi4` fails, the script must raise `DataIngestionError` and NOT proceed.
- [X] T049 [US2/Review] Update `code/model_training.py` to log the exact dataset size (number of IonPairs) and the number of samples per `StructuralFamily` used in the stratified split. Verify the log output includes these counts to ensure the split is valid and no family is empty in the test set.
- [X] T050 [US3/Review] Add a "Data Provenance" section to `contracts/validation_report.json`. This section must explicitly state the source of the training data (SPICE/IL-SAPT) and the source of the validation data (Independent DFT). Verify the report includes these source strings.
- [X] T051 [P] [US1/Review] Implement streaming data loader in `code/data_ingestion.py`. Replace any full-load `pd.read_csv` or `pd.read_parquet` for datasets exceeding 1GB with `datasets.load_dataset(..., streaming=True)` or chunked reading (`pd.read_csv(chunksize=...)`). Ensure the ingestion logic accumulates statistics or writes intermediate results without holding the entire dataset in RAM. **Test Data**: Use `data/raw/sample_5gb.parquet` (generated by `scripts/generate_sample.py` if missing). Verify the script processes a large sample dataset without exceeding acceptable RAM usage limits.
- [X] T052 [US1/Review] Add explicit "Sample Definition" logging to `code/data_ingestion.py`. If the dataset is sampled (either via streaming limit or random subset), the script MUST log the exact sampling rule used (e.g., "First [deferred] rows of stream" or "Random seed 42, subset") and the resulting sample size. Verify the log contains the string "Sampling Rule" with the specific parameters used.
- [X] T053 [US1/Review] Implement a "Real Data Verification" check in `code/data_ingestion.py`. After fetching the dataset, compute a simple checksum or hash of a representative subset of rows and compare it against a known reference (if available) or log the hash as a fingerprint. Verify the log contains a "Data Fingerprint" entry to confirm the data is real and not synthetic.
- [X] T054 [US3/Review] Update `code/analysis.py` to explicitly report the "Statistical Power" of the ANOVA test. Calculate and log the effect size and sample size per family to ensure the ANOVA results are statistically meaningful (not just significant due to massive N). Verify the log contains a "Statistical Power" section with per-family metrics.
- [X] T055 [P] [US2/Review] Refactor `code/model_training.py` to handle "Stratification Failure". If a `StructuralFamily` has too few samples to support the requested split (e.g., < 5 samples), the script must log a warning, exclude that family from the split, and re-balance the remaining data, rather than crashing or silently dropping the family. Verify the log contains a "Stratification Warning" with the excluded family name.

---

### Notes on Plan Overrides

- **FR-001 (Data Source)**: Spec mandates ILThermo/SAPT. Plan mandates SPICE as primary. Tasks T012a/T013 implement Plan (SPICE primary, SAPT secondary).
- **FR-002 (Partial Charges)**: Spec mandates generating partial charges as descriptors. Plan mandates excluding them from model input. Tasks T015/T016 implement Plan (calculate for internal check, exclude from model).
- **FR-007 (Validation)**: Spec mandates experimental enthalpy. Plan mandates Independent DFT. Tasks T012b-DFT/T035a implement Plan (DFT validation).
- **T039d (DFT Gen)**: Plan defines as fallback. Task T039d implements conditional logic and is moved to Phase 0.