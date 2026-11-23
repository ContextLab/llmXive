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
- **[S]**: Sequential (must run after dependencies)
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

- [ ] T000-Governance [S] **GATEKEEPER: SPEC/PLAN CONTRADICTION**: This task is a **GATEKEEPER** that halts execution until the `spec.md` artifact is manually amended via a Pull Request to resolve the contradiction between Spec FR-007/US-3 ("experimental enthalpy of mixing") and Plan Phase 2 ("Independent DFT data"). **Action Required**: The human operator MUST create a PR to update `spec.md` to reflect the Plan's "Independent DFT" validation strategy. **Constraint**: No code execution for this task. The implementation of all subsequent tasks (T012d, T035a, etc.) assumes the Plan's "Independent DFT" logic is the source of truth. This task verifies that the governance process for spec amendment has been initiated or completed. **Dependency**: None. **Verification**: Manual confirmation that a PR exists or the spec has been updated. **Note**: This task replaces T000-SpecFix-Execute to comply with Constitution Principle IV.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [S] Create project directory structure: Create `scripts/setup_dirs.sh` that generates `code/`, `data/raw/`, `data/processed/`, `data/validation/`, `models/`, `contracts/`, `tests/`, and `logs/`. Verify the script executes and lists the generated tree in `logs/setup.log` using `find` (not `tree`). **Dependency**: None.
- [ ] T001b [S] Initialize empty files: Create `code/__init__.py`, `code/config.py`, `code/data_ingestion.py`, `code/model_training.py`, `code/analysis.py`, `code/utils.py`, `data/raw/.gitkeep`, `data/processed/.gitkeep`, `data/validation/.gitkeep`, `models/.gitkeep`, `contracts/.gitkeep`, `tests/__init__.py`. Verify all listed files exist and are non-empty (or .gitkeep) before marking complete. **Dependency**: Must run after T001a.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002a [S] Create `code/requirements.txt` with pinned versions: `xgboost==2.0.3`, `optuna==3.5.0`, `rdkit==2023.9.5`, `pandas==2.1.4`, `scikit-learn==1.3.2`, `pyarrow==14.0.2`, `requests==2.31.0`, `pyyaml==6.0.1`, `psi4==1.8.1`, `statsmodels==0.14.1`, `pandera==0.17.2`, `pytest-mock==3.12.0`. **Install Command**: `python3.11 -m venv venv && venv/bin/pip install -r code/requirements.txt`. Verify `venv/bin/python` exists and `pip list` shows required packages. **Dependency**: Must run after T001a.
- [ ] T002b [S] Setup Python virtual environment: Create `scripts/setup_venv.sh` that creates the venv using `python3.11` and installs requirements. Verify `venv/bin/python` exists and `pip list` shows required packages. **Dependency**: Must run after T002a.
- [ ] T004a [P] Create `contracts/ion_pair.schema.yaml` defining fields: `cation_id` (str), `anion_id` (str), `electrostatic_energy` (float), `dispersion_energy` (float), `hbond_energy` (float), `total_energy` (float), `tpsa` (float), `molecular_surface_area` (float), `hbond_count` (int), `morgan_fp` (array), `structural_family` (str), `polarizability` (float), `partial_charge` (float). **Note**: `partial_charge` is included as a *calculated* field to satisfy FR-002 generation requirement, but MUST be excluded from the *training feature set* in T016a. Verify file is valid YAML and matches pandera schema requirements.
- [ ] T004b [P] Create `contracts/validation_report.schema.yaml` defining fields: `anova_results_raw` (object), `anova_results_predictions` (object), `tukey_hsd` (object), `dft_mae` (float), `experimental_validation_mae` (float), `sc003_compliance` (bool), `experimental_validation_status` (str), `tautology_check` (object). Verify file is valid YAML and matches pandera schema requirements.
- [ ] T005a [P] Implement `code/config.py` defining `SEED=42`, `DATA_PATHS` (dict), `HYPERPARAM_BOUNDS` (dict), `MAX_TRIALS=60`, `TRIAL_TIMEOUT=300` (seconds), `TRAIN_RATIO=0.7`, `VAL_RATIO=0.15`, `TEST_RATIO=0.15`.
- [ ] T005b [P] Implement `.env.example` and `code/config.py` loading logic using `python-dotenv` to override defaults.
- [ ] T006a [P] Implement `code/utils.py` with functions: `compute_tpsa(smiles)`, `compute_morgan_fp(smiles, radius=2, n_bits=2048)`, `compute_hbond_count(smiles)`.
- [ ] T006b [P] Implement `code/utils.py` with function: `run_psi_sapt(structure_file, method='sapt0', basis='jun-cc-pVDZ')` returning energy components.
- [ ] T006c [P] Implement `code/utils.py` with function: `compute_polarizability(smiles)` using RDKit's `rdkit.Chem.Crippen.MolMR` as a proxy for polarizability. Verify it returns a float.
- [ ] T008a [P] Implement `code/utils.py` logging configuration: `logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO, handlers=[logging.FileHandler('logs/pipeline.log'))`.
- [ ] T008b [P] Implement `code/utils.py` custom exception hierarchy: `DataIngestionError`, `ModelTrainingError`, `AnalysisError`.
- [ ] T009a [P] Create `code/.env.example` with `SPICE_URL`, `IL_SAPT_URL`, `ILTHERMO_URL`, `DFT_VALIDATION_URL`. Verify file exists and contains these keys.
- [ ] T009b [P] Implement `code/config.py` to load `.env` and validate required keys exist, raising `DataIngestionError` if missing.
- [ ] T012d-DownloadSPICE [S] [US1] Implement `code/data_ingestion.py` function `download_spice_dataset()`: **PRIMARY SOURCE**. Fetch the SPICE dataset using the HuggingFace API: `from datasets import load_dataset; ds = load_dataset("SPICE", split="train")`. **Constraint**: If HuggingFace is unavailable, use the specific raw URL from the HuggingFace dataset card (e.g., `https://huggingface.co/datasets/SPICE/resolve/main/train.parquet`). Save to `data/raw/spice.parquet`. Verify file exists and contains columns `cation_id`, `anion_id`, `smiles_cation`, `smiles_anion`, `structural_family`, `electrostatic_energy`, `dispersion_energy`, `hbond_energy`. **Dependency**: Must run after T002b.
- [ ] T012a-Conditional [S] [US1] Implement `code/data_ingestion.py` function `download_il_thermo_sapt()`: **SECONDARY SOURCE (Optional Supplement)**. **Logic**: Check if `IL_SAPT_URL` is defined in `code/config.py`. If defined, attempt to fetch the ILThermo/SAPT dataset. If the fetch fails (HTTPError, Timeout) OR the URL is not defined, log "IL_SAPT_URL not defined or fetch failed, skipping secondary source download" and return `None`. **Constraint**: This task is OPTIONAL. **Dependency**: Must run after T002b. **Note**: This task does NOT trigger the fallback; T017b-Select handles the fallback logic.
- [ ] T013c-Structures [S] [US1] Implement `code/data_ingestion.py` function `extract_structures_from_data(df)`: Extract unique cation/anion SMILES from the downloaded SPICE/ILThermo/SAPT dataset (`data/raw/spice.parquet`, `data/raw/il_thermo.parquet`, or `data/raw/sapt.parquet`) and save to `data/raw/il_structures.json`. **Dependency**: Must run after T012d-DownloadSPICE and T012a-Conditional. Verify `data/raw/il_structures.json` exists and contains valid SMILES.
- [ ] T012c-TrainGen [S] [US1] [Plan Phase 0] [Constitution VI] Implement `code/data_ingestion.py` function `generate_sapt_training_labels()`: **SYNTHETIC TRAINING FALLBACK**. **Conditional**: Only execute if T017b-Select determines that SPICE is missing. **Logic**: Randomly select N=500 IonPairs from `data/raw/il_structures.json`, stratified by `structural_family` (seed=42, minimum 5 samples per family). If `structural_family` is missing, infer it from SMILES patterns (e.g., 'imidazolium' if 'c1nccn1' in SMILES). Calculate SAPT/DFT energy components using `run_psi_sapt` with `method='sapt0'` and `basis='jun-cc-pVDZ'` to ensure deterministic reproducibility. Save to `data/processed/sapt_training_labels.parquet`. **Note**: This implements the Plan's fallback for missing training data. **Dependency**: Must run after T017b-Select.
- [ ] T012b-Gen [S] [US1] [Plan Phase 2] [Constitution VI] Implement `code/data_ingestion.py` function `generate_dft_validation_set()`: **INDEPENDENT DFT VALIDATION**. **Conditional**: Only execute if T017b-Select determines that SPICE is missing (or if a specific validation set is required). **Logic**: Randomly select N=20 IonPairs from `data/raw/il_structures.json`, stratified by `structural_family` (seed=42, minimum 5 samples per family). **Pre-condition**: Verify that the dataset contains at least 20 samples with valid families. If not, raise `DataIngestionError` immediately. Calculate SAPT/DFT energy components using `run_psi_sapt` with `method='sapt0'` and `basis='jun-cc-pVDZ'`. Save to `data/validation/dft_validation_set.parquet`. **Note**: This implements the amended FR-007 requirement for Independent DFT validation. **Dependency**: Must run after T017b-Select.
- [ ] T012c [S] Implement `code/data_ingestion.py` function `verify_checksum(file_path, expected_hash)` to validate downloaded data.
- [ ] T015a [S] [US1] Implement `code/data_ingestion.py` function `calculate_partial_charges_internal_only(df)`: Calculate Gasteiger partial charges using RDKit for *internal consistency checks only*. **Constraint**: These values MUST NOT be used as input features for training. Save the result to `data/processed/internal_consistency_checks.parquet` before dropping from the main dataset. **Note**: This satisfies FR-002 generation requirement. **Dependency**: Must run after T013c-Structures.
- [ ] T016a [S] [US1] Implement `code/data_ingestion.py` function `engineer_features(df)`: Parse SMILES, compute TPSA, Molecular Surface Area, H-bond counts, and graph embeddings. **CRITICAL**: Depends on T015a. Call `calculate_partial_charges_internal_only` to save the internal consistency artifact (`data/processed/internal_consistency_checks.parquet`), then DROP the `partial_charge` column from the *training feature matrix* (save to `data/processed/training_features.parquet`). **Note**: The `partial_charge` column must be retained in the *final unified dataset* output file (via T016b) to satisfy US-1 Independent Test, but excluded from the *training feature set*. Explicitly document in code: "Partial charges calculated for internal consistency only; excluded from model training." **Dependency**: Must run after T015a.
- [ ] T016b [S] [US1] Implement `code/data_ingestion.py` function `merge_consistency_artifacts()`: Read `data/processed/internal_consistency_checks.parquet` (from T015a) and merge it into the final unified dataset for the 'Internal Consistency' report, ensuring the `partial_charge` column is present in the final output file (`data/processed/unified_dataset.parquet`) as required by Spec US-1 Independent Test, while ensuring it was not used for training. **Dependency**: Must run after T016a and T015a.
- [ ] T017a-Check [S] [US1] Implement `code/data_ingestion.py` function `check_data_source_existence()`: **DATA SOURCE CHECK**. Check if `data/raw/spice.parquet` exists. Check if `data/raw/sapt.parquet` exists (from T012a-Conditional). Return a dictionary of boolean flags indicating availability. **Dependency**: Must run after T012d-DownloadSPICE and T012a-Conditional.
- [ ] T017b-Select [S] [US1] Implement `code/data_ingestion.py` function `select_data_sources(flags)`: **DATA SOURCE SELECTION**. Based on flags from T017a-Check: **Priority**: 1. If SPICE exists, select it. 2. If SPICE is missing, trigger the "Verified Synthetic Generation" protocol (T012c-TrainGen logic) for training labels. **Note**: SAPT is treated as an optional supplement ONLY if explicitly merged later, not as a fallback for SPICE absence. Return the paths to the selected files and a `source` marker string ('spice' or 'synthetic'). **Dependency**: Must run after T017a-Check.
- [ ] T017c-Path [S] [US1] Implement `code/data_ingestion.py` function `get_selected_paths()`: **FILE PATH RETURN**. Return the paths to the selected data files based on the selection logic in T017b-Select. **Dependency**: Must run after T017a-Check and T017b-Select.
- [ ] T017d [S] [US1] Implement `code/data_ingestion.py` function `filter_raw_sapt()`: **RAW SAPT FILTER**. **Logic**: Read the `source` marker from T017b-Select. If `source == 'spice'`, filter `data/raw/spice.parquet`. If `source == 'synthetic'`, filter `data/processed/sapt_training_labels.parquet`. Save the result to `data/processed/raw_sapt.parquet` (or `synthetic_raw_sapt.parquet` for synthetic). **Dependency**: Must run after T017b-Select.
- [ ] T017e [S] [US1] Implement `code/data_ingestion.py` function `write_unified_dataset(df, path)`: **UNIFIED DATASET WRITER**. **Logic**: Read the filtered data from T017d. Merge with structural families and descriptors. Validate against `contracts/ion_pair.schema.yaml`. Save to `data/processed/unified_dataset.parquet`. **Dependency**: Must run after T017d.
- [ ] T017f-SynthFilter [S] [US1] Implement `code/data_ingestion.py` function `filter_synthetic_raw_sapt()`: **SYNTHETIC RAW SAPT FILTER**. If real SAPT data is missing (and T012c-TrainGen was used), filter the synthetic training labels (`data/processed/sapt_training_labels.parquet`) to create a 'raw SAPT' equivalent subset for ANOVA analysis. Save to `data/processed/synthetic_raw_sapt.parquet`. **Dependency**: Must run after T012c-TrainGen.
- [ ] T017g-DataReadyMarker [S] [US1] Implement `code/data_ingestion.py` function `create_data_ready_marker()`: **BRANCH COMPLETION MARKER**. After T017e completes, create a file `data/processed/.data_ready` containing a JSON object with the selected source type ('spice' or 'synthetic'). **Dependency**: Must run after T017e.
- [ ] T017b [S] [US1] Implement `code/data_ingestion.py` function `merge_il_thermo_sapt(il_df, sapt_df)`: Merge ILThermo and SAPT on `cation_id` and `anion_id`.
- [ ] T017c [S] [US1] Implement `code/data_ingestion.py` function `merge_training_data(base_df, sapt_df)`: **REAL DATA MERGE ONLY**. Merge the base structure dataframe with the real SAPT energy dataframe. **Constraint**: This function must NOT handle synthetic data. If `sapt_df` is missing or empty, raise `DataIngestionError`. This function is strictly for the training pipeline.
- [ ] T018a [S] [US1] Implement `code/data_ingestion.py` function `validate_unified_dataset(df, schema_path)` using `pandera`.
- [ ] T018b [S] [US1] Implement `code/data_ingestion.py` function `log_validation_errors(errors)` to write detailed errors to `logs/ingestion_errors.log`.
- [ ] T019 [S] [US1] Add logging for ingestion steps and synthetic generation fallback. Update `code/data_ingestion.py` to log steps to `logs/ingestion.log`.

---

## Phase 3: User Story 1 - Data Ingestion and Feature Engineering (Priority: P1) 🎯 MVP

**Goal**: Ingest ILThermo/SAPT/SPICE, engineer descriptors, and produce a unified dataset.

**Independent Test**: Run ingestion on a small subset of IonPairs. Verify `data/processed/unified_dataset.parquet` contains expected columns with no null values. **Note**: `partial_charge` column must be present in the final output file (for consistency checks) but excluded from the training feature set.

---

## Phase 4: User Story 2 - Model Training and Hyperparameter Optimization (Priority: P2)

**Goal**: Train three XGBoost regressors with Optuna, respecting strict CPU time limits.

**Independent Test**: Run training on a toy dataset with a timeout mechanism. Verify three `.pkl` model artifacts are saved and logs show best hyperparameters and trial timeouts.

- [ ] T062 [S] [US2/Review] [Timeout Handling] Implement `code/model_training.py` function `run_with_timeout(func, timeout=300)`: **MEMORY-SAFE TIMEOUT**. Use the `signal` module (Linux) to wrap the model training call, ensuring the trial is killed if it exceeds `config.TRIAL_TIMEOUT` (300 seconds). **Logic**: `signal.signal(signal.SIGALRM, timeout_handler); signal.alarm(timeout); try: result = func(); signal.alarm(0); except TimeoutError:...`. **Constraint**: Do NOT use `multiprocessing` to avoid memory overhead. **Log Message**: `logger.warning(f"Trial {trial.number} terminated by timeout after {config.TRIAL_TIMEOUT} seconds")`. **Dependency**: Must run before T022-T024.
- [ ] T021a [S] [US2] Implement `code/model_training.py` function `stratified_split(df, target_col, structural_family_col)`: Use `sklearn.model_selection.train_test_split` with ratios defined in `code/config.py`.
- [ ] T021b [S] [US2] Implement `code/model_training.py` function `save_splits(train_df, val_df, test_df)` to `data/processed/train.parquet`, `val.parquet`, `test.parquet`.
- [ ] T022 [S] [US2] Implement `code/model_training.py` function `train_electrostatic_model(train_df, val_df)` using XGBoost.
- [ ] T023 [S] [US2] Implement `code/model_training.py` function `train_dispersion_model(train_df, val_df)` using XGBoost.
- [ ] T024 [S] [US2] Implement `code/model_training.py` function `train_hbond_model(train_df, val_df)` using XGBoost.
- [ ] T025a [S] [US2] Implement `code/model_training.py` function `optuna_objective(trial, model_type, train_df, val_df)` defining search space for XGBoost hyperparameters.
- [ ] T025b [S] [US2] Implement `code/model_training.py` function `run_optuna_study()` with `n_trials=60`, `timeout=300` seconds per trial, using `optuna.create_study`.
- [ ] T026 [S] [US2] Implement `code/model_training.py` function `save_models(models, path_prefix)` to save model artifacts.
- [ ] T027 [S] [US2] Implement `code/model_training.py` function `check_energy_consistency(predictions, total_sapt_targets, tolerance=0.1 kcal/mol)`.
- [ ] T028a [S] [US2] Add logging for MAE: In `code/model_training.py`, inside `run_optuna_study`, add `logger.info(f"Trial {trial.number}: MAE = {mae:.4f}")` after each successful trial.
- [ ] T028b [S] [US2] Add logging for convergence: In `code/model_training.py`, add `logger.info(f"Study completed. Best MAE: {study.best_value:.4f}")` after the study finishes.
- [ ] T028c [S] [US2] Add logging for timeout: In `code/model_training.py`, wrap `optuna_objective` in a timeout handler and add `logger.warning(f"Trial {trial.number} timed out after {TRIAL_TIMEOUT} seconds")` if it exceeds the limit.
- [ ] T029a [S] [US2] Implement `code/model_training.py` function `perform_sensitivity_analysis(study_results)` to calculate the variance of MAE across the top hyperparameter configurations.
- [ ] T029b [S] [US2] Implement `code/model_training.py` function `log_sensitivity_results(results)` to write detailed sensitivity analysis to logs.

---

## Phase 5: User Story 3 - Systematic Variation Analysis and Validation (Priority: P3)

**Goal**: Perform ANOVA on model predictions (primary) AND raw SAPT data (comparative), apply corrections, validate against Independent DFT dataset, and report results.

- [ ] T029c-Raw [S] [US3] Implement `code/analysis.py` function `run_anova_raw(df, energy_col, family_col)`: Perform One-way ANOVA on the *raw SAPT energy components* (pre-merging) grouped by `StructuralFamily`. Apply Bonferroni correction and Tukey HSD. **Dependency**: Must run after T017g-DataReadyMarker (ensures the correct branch data is available). **Constraint**: If the marker file indicates `source == 'synthetic'`, raise `AnalysisError` immediately: "ANOVA on synthetic data is forbidden for primary validation". **Note**: This provides a baseline for comparison with T029c-Pred.
- [ ] T029c-Pred [S] [US3] Implement `code/analysis.py` function `run_anova_predictions(predictions_df, family_col)`: **SECONDARY CHECK**. Perform One-way ANOVA on the *model predictions* grouped by `StructuralFamily`. Apply Bonferroni correction and Tukey HSD. **Dependency**: Must run after T022-T024 (model training). **Note**: This is a secondary check to validate model bias, not the primary physical trend analysis required by the plan.
- [ ] T029e [S] [US3] Implement `code/analysis.py` function `compare_anova_results(raw_results, pred_results)`: Compare the p-values and effect sizes from T029c-Raw and T029c-Pred to determine if the model successfully captures family trends. **Dependency**: Must run after T029c-Raw and T029c-Pred.
- [ ] T029f [S] [US3] Implement `code/analysis.py` function `save_anova_results(results, path)`.
- [ ] T030 [S] [US3] Execute ANOVA on electrostatic energy (predictions).
- [ ] T031 [S] [US3] Execute ANOVA on dispersion energy (predictions).
- [ ] T032 [S] [US3] Execute ANOVA on H-bond energy (predictions).
- [ ] T033a [S] [US3] Implement `code/analysis.py` function `apply_bonferroni_correction(p_values, n_tests)` to calculate corrected p-values.
- [ ] T033b [S] [US3] Implement `code/analysis.py` function `run_tukey_hsd(df, energy_col, family_col)` using `statsmodels.stats.multicomp`.
- [ ] T033c [S] [US3] Write corrected results to `analysis/anova_corrected.json` with explicit p-value threshold logic.
- [ ] T034 [S] [US3] Implement `code/analysis.py` function `calculate_cohens_d(group1, group2)` for significant families.
- [ ] T035a [S] [US3] Implement `code/analysis.py` function `validate_against_dft_stratified(models)`: **STRICT 20 IONPAIRS VALIDATION**. Load `data/validation/dft_validation_set.parquet` (from T012b-Gen). **Logic**: Verify the dataset contains exactly N=20 IonPairs. If N < 20, raise `DataIngestionError` immediately. Calculate MAE for each model against this set. **Dependency**: Must run after T012b-Gen. **Note**: This satisfies amended FR-007 and the 'subset of 20' constraint.
- [ ] T035b [S] [US3] Implement `code/analysis.py` function `calculate_sc003_compliance(dft_mae, test_mae)`: Calculate MAE against DFT set and compare against SC-003 relative metric (out-of-sample MAE ≤ 2.0 × baseline test set MAE). **Note**: This updates SC-003 to reflect the amended DFT validation strategy. **Constraint**: If spec.md still references experimental data, log a warning that SC-003 logic is based on the plan's DFT strategy.
- [ ] T035b-UpdateSC003 [S] [US3] Implement `code/analysis.py` function `update_sc003_metric_in_report()`: **SC-003 METRIC UPDATE**. Ensure the final validation report explicitly states the DFT baseline and the calculated MAE, replacing any reference to 'experimental' with 'Independent DFT'. **Dependency**: Must run after T035a.
- [ ] T036a [S] [US3] Implement `code/analysis.py` function `calculate_correlation_matrix(descriptors, targets)`.
- [ ] T036b [S] [US3] Implement `code/analysis.py` function `check_tautology(correlation_matrix, threshold=0.95)`.
- [ ] T037a [S] [US3] Implement `code/analysis.py` function `aggregate_validation_results(anova_predictions, anova_raw, tukey, dft_mae, sc003_status, tautology)`.
- [ ] T037b [S] [US3] Implement `code/analysis.py` function `write_validation_report(report, path)` to `contracts/validation_report.json`.
- [ ] T038a [S] [US3] Add logging for p-values: In `code/analysis.py`, inside `run_anova_predictions`, add `logger.info(f"ANOVA p-value for {energy_col}: {p_value:.4f}, Corrected: {corrected_p:.4f}")`.
- [ ] T038b [S] [US3] Add logging for effect sizes: In `code/analysis.py`, inside `calculate_cohens_d`, add `logger.info(f"Cohen's d for {family1} vs {family2}: {d:.4f}")`.
- [ ] T038c [S] [US3] Add logging for validation MAE: In `code/analysis.py`, inside `validate_against_dft`, add `logger.info(f"DFT Validation MAE: {mae:.4f} kcal/mol")`.
- [ ] T039a [S] [US3] Implement `code/analysis.py` function `run_anova_on_predictions(predictions_df, family_col)`.
- [ ] T039b [S] [US3] Implement `code/analysis.py` function `compare_raw_vs_prediction_anova(raw_results, prediction_results)`.
- [ ] T063 [S] [US3/Review] [ANOVA Robustness] Implement `code/analysis.py` function `check_anova_assumptions(df, energy_col, family_col)`: Before running ANOVA, verify the assumptions of normality (Shapiro-Wilk) and homogeneity of variance (Levene's test). **Logic**: If assumptions are violated (p < 0.05), log a WARNING and automatically switch to a non-parametric alternative (Kruskal-Wallis test) for that specific energy component, while still reporting the original ANOVA results for comparison. **Threshold**: p < 0.05. **Fallback**: `scipy.stats.kruskal`. **Output Format**: The final report must include both 'anova_raw' (original) and 'anova_fallback' (if applicable) fields.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041 [S] Documentation updates in `specs/001-predicting-molecular-interactions-in-ion/` (update research.md with findings).
- [ ] T042a [S] Code cleanup: Run `flake8` on `code/`.
- [ ] T042b [S] Code cleanup: Refactor `code/utils.py` function `compute_tpsa`.
- [ ] T043 [S] Performance optimization across all scripts (ensure < 6h runtime).
- [ ] T044 [S] Additional unit tests for RDKit descriptors in `tests/unit/test_descriptors.py`.
- [ ] T045 [S] Run `quickstart.md` validation (if generated).
- [ ] T050 [S] [US3/Review] Add a "Data Provenance" section to `contracts/validation_report.json`.
- [ ] T054 [S] [US3/Review] Add logging for p-values, effect sizes, and validation MAE. **Implementation**: Ensure `code/analysis.py` logs the raw p-value, the Bonferroni-corrected p-value, Cohen's d, and the final MAE for DFT validation sets.
- [ ] T055 [S] [P] Refactor `code/model_training.py` to handle "Stratification Failure". **Implementation**: If `train_test_split` fails to stratify due to a family having < 2 samples, log a WARNING, remove that family from the split, and proceed, ensuring the split is valid for the remaining families.

---

## Phase 7: Revision & Review Resolution (Priority: P1)

**Goal**: Address specific concerns raised in the `analyze` phase regarding data integrity, streaming, and error handling.

- [ ] T047 [S] Hard-code "fail-loud" behavior for data loaders. **Implementation**: Removed. Default `requests`/`datasets` behavior is already "fail-loud". The fallback (T012b-Gen/T012c-TrainGen) is triggered only if real data is missing, not via a try/except in the loader.
- [ ] T048 [S] Explicitly document the "Verified Synthetic Generation" fallback. **Implementation**: Added a docstring and comment block to `code/data_ingestion.py` (T012b-Gen/T012c-TrainGen) explicitly stating: "This is a VERIFIED fallback ONLY for the VALIDATION SET (T012b-Gen) or TRAINING LABELS (T012c-TrainGen). It uses Psi4 with verified structures. It is NEVER used for training data unless the real SAPT source is missing (T012c-TrainGen)."
- [ ] T049 [S] [US2/Review] Update `code/model_training.py` to log the exact dataset size and the number of samples per StructuralFamily used in the stratified split. **Implementation**: Add logging in `train_electrostatic_model` (T022) and `stratified_split` (T021a) to output `n_train`, `n_val`, `n_test`, and a frequency count of `StructuralFamily` in each split.
- [ ] T052 [S] [US1/Review] Add explicit "Sample Definition" logging to `code/data_ingestion.py`. **Implementation**: If streaming or sampling is used, log the exact rule: "Using streaming mode", "Sample size: N rows", "Seed: 42", "Split: train".
- [ ] T053 [S] [US1/Review] Implement a "Real Data Verification" check in `code/data_ingestion.py`. **Implementation**: Add a function `verify_real_data_source(path)` that checks file size > 0 and row count > 0 before processing. If the file is empty or missing, raise `DataIngestionError` immediately.
- [ ] T061 [S] [US1/Review] [Data Integrity] Implement `code/data_ingestion.py` function `validate_family_coverage(df)`: A strict validation step that runs after T016a. **Logic**: Verify that every `StructuralFamily` present in the raw SAPT source (if available) is represented in the final unified dataset with at least N=10 samples. If a family is missing or under-represented, raise `DataIngestionError` with a clear message listing the missing families. **Error Message Format**: "DataIngestionError: Family coverage insufficient. Missing or under-represented families: {families}. Minimum required: {N} samples." **Config**: N value must be read from `config.py` (default 10).