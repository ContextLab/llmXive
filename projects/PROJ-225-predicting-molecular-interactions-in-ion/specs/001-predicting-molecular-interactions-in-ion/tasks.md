# Tasks: Predicting Molecular Interactions in Ionic Liquids via Machine Learning

**Input**: Design documents from `/specs/001-predicting-molecular-interactions/`
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

- [ ] T001a [P] Create project directory structure: `mkdir -p code/ data/raw/ data/processed/ data/validation/ models/ contracts/ tests/contract/ tests/unit/ tests/integration/ specs/001-predicting-molecular-interactions-in-ion/`
- [ ] T001b [P] Initialize empty files: `touch code/__init__.py code/config.py code/data_ingestion.py code/model_training.py code/analysis.py code/utils.py data/raw/.gitkeep data/processed/.gitkeep data/validation/.gitkeep models/.gitkeep contracts/.gitkeep tests/__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002a [P] Create `code/requirements.txt` with pinned versions: `xgboost==2.0.3`, `optuna==3.5.0`, `rdkit==2023.9.5`, `pandas==2.1.4`, `scikit-learn==1.3.2`, `pyarrow==14.0.2`, `requests==2.31.0`, `pyyaml==6.0.1`, `psi4==1.8.1`, `statsmodels==0.14.1`, `pandera==0.17.2`
- [ ] T002b [P] Setup Python virtual environment: `python3.11 -m venv venv && source venv/bin/activate && pip install -r code/requirements.txt`
- [ ] T004a [P] Create `contracts/ion_pair.schema.yaml` defining fields: `cation_id` (str), `anion_id` (str), `electrostatic_energy` (float), `dispersion_energy` (float), `hbond_energy` (float), `total_energy` (float), `tpsa` (float), `molecular_surface_area` (float), `hbond_count` (int), `morgan_fp` (array), `structural_family` (str)
- [ ] T004b [P] Create `contracts/validation_report.schema.yaml` defining fields: `anova_results` (object), `tukey_hsd` (object), `dft_validation_mae` (float), `experimental_validation_status` (str), `tautology_check` (object)
- [ ] T005a [P] Implement `code/config.py` defining `SEED=42`, `DATA_PATHS` (dict), `HYPERPARAM_BOUNDS` (dict), `MAX_TRIALS=60`, `TRIAL_TIMEOUT=300` (seconds)
- [ ] T005b [P] Implement `.env.example` and `code/config.py` loading logic using `python-dotenv` to override defaults
- [ ] T006a [P] Implement `code/utils.py` with functions: `compute_tpsa(smiles)`, `compute_morgan_fp(smiles, radius=2, n_bits=2048)`, `compute_hbond_count(smiles)`
- [ ] T006b [P] Implement `code/utils.py` with function: `run_psi_sapt(structure_file, method='sapt0', basis='jun-cc-pVDZ')` returning energy components
- [ ] T008a [P] Implement `code/utils.py` logging configuration: `logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO, handlers=[logging.FileHandler('logs/pipeline.log')])`
- [ ] T008b [P] Implement `code/utils.py` custom exception hierarchy: `DataIngestionError`, `ModelTrainingError`, `AnalysisError`
- [ ] T009a [P] Create `.env.example` with `SPICE_URL=...`, `IL_SAPT_URL=...`, `IL_THERMO_URL=...`
- [ ] T009b [P] Implement `code/config.py` to load `.env` and validate required keys exist, raising `DataIngestionError` if missing

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Feature Engineering (Priority: P1) 🎯 MVP

**Goal**: Ingest SPICE, IL-SAPT (or synthetic fallback), and ILThermo (for validation subset), engineer descriptors (including partial charges and polarizability), and produce a unified, schema-validated training dataset.

**Independent Test**: Run ingestion on a small subset of IonPairs. Verify `data/processed/unified_dataset.parquet` contains expected columns (cation_id, anion_id, electrostatic_energy, dispersion_energy, hbond_energy, tpsa, molecular_surface_area, hbond_count, graph_embedding, structural_family) with no null values in critical columns. **Note: partial_charge column must be present in raw processing but DROPPED in final training set.**

> **TDD Note**: The task list order reflects TDD workflow: Tests (T010, T011) are written FIRST, before implementation (T012-T019). This ensures tests fail initially and pass after implementation.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T010 [P] [US1] Contract test for unified dataset schema in `tests/contract/test_ion_pair_schema.py` using `pandera`
- [ ] T011 [P] [US1] Integration test for data pipeline on samples in `tests/integration/test_ingestion_small.py`

### Implementation for User Story 1

- [ ] T012a [P] [US1] Implement `code/data_ingestion.py` function `download_spice(url)` to fetch SPICE dataset and save to `data/raw/spice.parquet`
- [ ] T012b [P] [US1] Implement `code/data_ingestion.py` function `verify_checksum(file_path, expected_hash)` to validate downloaded SPICE data
- [ ] T013 [US1] Implement `code/data_ingestion.py` function `download_ilthermo(url)` to fetch ILThermo dataset for structure extraction and experimental validation subset; save to `data/raw/ilthermo.parquet`. **Note: Per Plan, this data is NOT used for model validation but for structure extraction and FR-007 compliance check.**
- [ ] T014 [US1] Implement `code/data_ingestion.py` function `attempt_il_sapt_download(url)` to fetch IL-SAPT. If HTTP 404, trigger "Verified Synthetic Generation" using `psi4` and `data/raw/il_structures.json`. **Output**: Save to `data/raw/sapt.parquet` with columns: `cation_id`, `anion_id`, `electrostatic_energy`, `dispersion_energy`, `hbond_energy`, `total_energy`.
- [ ] T015 [US1] Implement `code/data_ingestion.py` function `calculate_partial_charges(df)` using RDKit Gasteiger method. If Gasteiger fails, attempt MMFF94. **Store** calculated charges in a temporary column `partial_charge` but **DO NOT** include in final training features yet. Flag rows where calculation fails.
- [ ] T016 [US1] Implement `code/data_ingestion.py` function `engineer_features(df)`: Parse SMILES, compute TPSA, Molecular Surface Area, H-bond counts, **polarizability**, and Morgan fingerprints. **CRITICAL**: **DROP** the `partial_charge` column from the final dataframe to satisfy Plan constraint (avoid circular validation). **DO NOT** filter out rows with unreliable charges; only drop the feature. Save to `data/processed/unified_dataset.parquet` with a `charge_reliability` column set to 'unreliable' for rows where calculation failed (for logging only).
- [ ] T017a [US1] Implement `code/data_ingestion.py` function `unify_datasets(spice_df, sapt_df, ilthermo_df)`: Join on `cation_id` and `anion_id`. Handle missing values by imputation or flagging.
- [ ] T017b [US1] Implement `code/data_ingestion.py` function `write_unified_dataset(df, path)` to save to `data/processed/unified_dataset.parquet`
- [ ] T018a [US1] Implement `code/data_ingestion.py` function `validate_unified_dataset(df, schema_path)` using `pandera`
- [ ] T018b [US1] Implement `code/data_ingestion.py` function `log_validation_errors(errors)` to write detailed errors to `logs/ingestion_errors.log`
- [ ] T019 [US1] Add logging for ingestion steps and synthetic generation fallback

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Hyperparameter Optimization (Priority: P2)

**Goal**: Train three XGBoost regressors (Electrostatic, Dispersion, H-bond) with Optuna tuning, respecting strict CPU time limits.

**Independent Test**: Run training on a toy dataset with a timeout mechanism. Verify three `.pkl` model artifacts are saved and logs show best hyperparameters and trial timeouts.

### Implementation for User Story 2

- [ ] T021a [P] [US2] Implement `code/model_training.py` function `stratified_split(df, target_col, structural_family_col, ratios=(, 0.15, 0.15))` using `sklearn.model_selection.train_test_split`
- [ ] T021b [P] [US2] Implement `code/model_training.py` function `save_splits(train_df, val_df, test_df)` to `data/processed/train.parquet`, `val.parquet`, `test.parquet`
- [ ] T022 [US2] Implement `code/model_training.py` function `train_electrostatic_model(train_df, val_df)` using XGBoost
- [ ] T023 [US2] Implement `code/model_training.py` function `train_dispersion_model(train_df, val_df)` using XGBoost
- [ ] T024 [US2] Implement `code/model_training.py` function `train_hbond_model(train_df, val_df)` using XGBoost
- [ ] T025a [US2] Implement `code/model_training.py` function `optuna_objective(trial, model_type, train_df, val_df)` defining search space for XGBoost hyperparameters (max_depth, eta, gamma, etc.)
- [ ] T025b [US2] Implement `code/model_training.py` function `run_optuna_study()` with `n_trials=60`, `timeout=300` seconds per trial, using `optuna.create_study`
- [ ] T026 [US2] Implement `code/model_training.py` function `save_models(models, path_prefix)` to save `models/electrostatic.pkl`, `models/dispersion.pkl`, `models/hbond.pkl` and hyperparameter logs
- [ ] T027 [US2] Implement `code/model_training.py` function `check_energy_consistency(predictions, total_sapt_targets, tolerance=0.1)` where **both predictions and targets are in kcal/mol**. Write result to `models/consistency_log.json` with pass/fail status.
- [ ] T028 [US2] Add logging for MAE on validation set and trial convergence status

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Systematic Variation Analysis and Validation (Priority: P3)

**Goal**: Perform ANOVA on raw SAPT data by family, apply corrections, validate against Independent DFT dataset (per plan.md), and report results.

**Independent Test**: Run analysis on test set predictions and the Independent DFT set. Verify `contracts/validation_report.json` contains ANOVA p-values, Tukey HSD results, and DFT validation MAE.

> **Dependencies Note**: Tasks T029-T034 (ANOVA on raw data) are **independent** of US2 (models) and can run in parallel. Tasks T035a-T037 (Model Validation) **depend** on US2 (models) and must wait for US2 completion.

### Implementation for User Story 3

- [ ] T029a [P] [US3] Implement `code/analysis.py` function `run_anova(df, energy_col, family_col)` using `scipy.stats.f_oneway`
- [ ] T029b [P] [US3] Implement `code/analysis.py` function `save_anova_results(results, path)` to `analysis/anova_electrostatic.json`, `analysis/anova_dispersion.json`, `analysis/anova_hbond.json`
- [ ] T030 [US3] Run ANOVA for **Electrostatic** energy component (uncorrected p-value)
- [ ] T031 [US3] Run ANOVA for **Dispersion** energy component (uncorrected p-value)
- [ ] T032 [US3] Run ANOVA for **Hydrogen-bond** energy component (uncorrected p-value)
- [ ] T033a [US3] Implement `code/analysis.py` function `apply_bonferroni_correction(p_values, n_tests)` to calculate corrected p-values
- [ ] T033b [US3] Implement `code/analysis.py` function `run_tukey_hsd(df, energy_col, family_col)` using `statsmodels.stats.multicomp`
- [ ] T033c [US3] Write corrected results to `analysis/anova_corrected.json` with explicit p-value threshold logic (targeting corrected p < 0.01/N_tests)
- [ ] T034 [US3] Implement `code/analysis.py` function `calculate_cohens_d(group1, group2)` for significant families
- [ ] T035a [US3] [Plan-Modified] Implement `code/analysis.py` function `validate_against_dft(models, dft_validation_set)` to compare model predictions against `data/validation/dft_validation_set.parquet`; calculate MAE and write to `analysis/dft_validation.json`
- [ ] T035b [US3] Implement `code/analysis.py` function `validate_against_experimental(models, experimental_set)` to compare predictions against `data/raw/ilthermo_validation.parquet` (a set of IonPairs). **CRITICAL**: Calculate MAE, then **immediately flag** this result as "INVALID FOR SAPT COMPONENTS" per Plan/Constitution due to entropic contributions. Write report to `analysis/experimental_validation_status.json` stating the metric is calculated but scientifically invalid for this task.
- [ ] T036a [US3] Implement `code/analysis.py` function `calculate_correlation_matrix(descriptors, targets)`
- [ ] T036b [US3] Implement `code/analysis.py` function `check_tautology(correlation_matrix, threshold=0.95)` to flag if any descriptor-target correlation > threshold; write to `analysis/tautology_report.json`
- [ ] T037a [US3] Implement `code/analysis.py` function `aggregate_validation_results(anova, tukey, dft_mae, experimental_status, tautology)`
- [ ] T037b [US3] Implement `code/analysis.py` function `write_validation_report(report, path)` to `contracts/validation_report.json` per schema
- [ ] T038 [US3] Add logging for p-values, effect sizes, and validation MAE

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041 [P] Documentation updates in `specs/001-predicting-molecular-interactions-in-ion/` (update research.md with findings)
- [ ] T042 Code cleanup and refactoring
- [ ] T043 Performance optimization across all scripts (ensure < 6h runtime)
- [ ] T044 [P] Additional unit tests for RDKit descriptors in `tests/unit/test_descriptors.py`
- [ ] T045 Run `quickstart.md` validation (if generated)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (unified dataset)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (trained models) and US1 output (raw data for ANOVA)
  - **Note**: T029-T034 (ANOVA on raw data) are **independent** of US2 (models) and can run in parallel with US2.
  - **Note**: T035a-T037 (Model Validation) **depend** on US2 (models) and must wait for US2 completion.

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
- **Specific Parallelism**: T030, T031, T032 (ANOVA per term) can run in parallel as they output intermediate uncorrected values.
- **Specific Parallelism**: T029-T034 (ANOVA on raw data) can run in parallel with T021-T028 (Model Training).

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for unified dataset schema in tests/contract/test_ion_pair_schema.py"
Task: "Integration test for data pipeline on a representative sample set in tests/integration/test_ingestion_small.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data_ingestion.py to download SPICE dataset"
Task: "Implement code/data_ingestion.py to download ILThermo dataset (validation subset)"
Task: "Implement code/data_ingestion.py to attempt IL-SAPT download or synthetic fallback"
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
   - Developer C: User Story 3 (ANOVA tasks T029-T034 can start immediately; Validation tasks T035a/035b wait for Developer B)
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
- **Critical**: T015 (Charge Generation) must precede T016 (Feature Engineering & Inclusion) to ensure charges are generated before being processed, but T016 must DROP the column.
- **Critical**: T030-T032 (ANOVA per term) output uncorrected values; T033 performs global correction.
- **Critical**: T029-T034 (ANOVA on raw data) are independent of US2 (models).
- **Critical**: T035a-T037 (Model Validation) depend on US2 (models).
- **Critical**: T035b implements Spec FR-007 but flags the result as scientifically invalid per Plan.
- **Critical**: T035a implements Plan's DFT validation.
- **Critical**: T015 is NOT [P] as it depends on T012-T014.