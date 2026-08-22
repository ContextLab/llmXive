# Tasks: Quantifying the Influence of Topological Defects on 2D Material Properties

**Input**: Design documents from `/specs/001-quantify-defect-influence/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[S]**: Sequential (must run after specific dependencies)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3)
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

 Tasks MUST be organized by user story so each story can be independently completable and testable.

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Initialize project directory structure: Create `src/`, `data/raw/`, `data/processed/`, `scripts/`, `tests/`, `notebooks/`, `data/validation/`, and `code/` directories

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `scripts/update_state_hashes.py` to record SHA-256 checksums for raw/processed data and feature matrices
- [X] T005 [P] Implement `src/config.py` for environment configuration (API keys, paths, seeds, and runtime parameters like N_PERMUTATIONS=1000, N_TARGET, N_STABILITY_RUNS)
- [X] T006 [P] Create `src/logging_config.py` for structured logging of workflow steps and errors
- [X] T007 Create base data models: `src/models/defect_entry.py` (DefectEntry entity) and `src/models/material_property.py` (MaterialProperty entity)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Synthetic Generation (Priority: P1) 🎯 MVP

**Goal**: Download pristine structures from Materials Project, attempt to fetch the Defect Dataset, and generate a physics-based synthetic fallback if the real data is missing/invalid.

**Independent Test**: Can be fully tested by successfully downloading pristine structures, attempting to parse the defect dataset (or generating synthetic data if missing), and verifying that all required fields (defect type, defect density, conductivity, elastic tensor, fracture energy) are present and non-null in the resulting dataset.

### Implementation for User Story 1

- [X] T010a [S] [US1] Implement `code/01_data_acquisition.py`: Step 1a - **Pristine Structure API Query & Cache Fallback**. Query **Materials Project REST API** for ≥50 pristine graphene and MoS₂ structures. **Endpoint**: `https://next-gen.materialsproject.org/api/v2/structures`. **Parameters**: `formula=graphene`, `formula=MoS2`, `num_structures=50`. **Logic**: Implement exponential backoff with a configurable retry limit for API calls. **On Success**: Write `data/raw/pristine_structures.csv` and `data/state/data_source.json` (initially `{"status": "real", "source": "materials_project"}`). **On Failure**: Write error details to `data/state/api_error_log.json`. **Then**: Check for local cache at `data/raw/pristine_structures.csv`. **If cache exists**: Validate schema and load. **If cache missing**: **HALT** workflow with `[ERROR: API access unavailable and no cache present]` (do NOT generate synthetic pristine structures). **Verification**: **MUST** verify `data/raw/pristine_structures.csv` contains ≥1 row; if empty after cache load, write error to `data/state/api_error_log.json` and set `data_source.json` status to `error`. **Guaranteed Output**: **MUST** write `data/raw/pristine_structures.csv`, `data/state/data_source.json`, and `data/state/api_error_log.json` (if error) in all cases.
- [X] T011a [S] [US1] Implement `code/01_data_acquisition.py`: Step 2a - **Defect Dataset Download & Validation**. Attempt to download the **Defect Dataset** to `data/raw/defect_dataset_2022.csv`. **Logic**: Validate file existence and basic schema (presence of required columns: `defect_type`, `defect_density`, `conductivity`, `elastic_tensor`, `fracture_energy`). **Guaranteed Output**: **MUST** write `data/raw/defect_dataset_2022.csv` (even if empty) and `data/state/source_validation.json` (schema: `{"valid": boolean, "reason": "string", "exclusions": int}`) in all cases. **Dependency**: T010a (output existence).
- [X] T011b [S] [US1] Implement `code/01_data_acquisition.py`: Step 2b - **Source Validity Check**. **Dependency**: T011a. **Logic**: Read `data/state/source_validation.json`. If `valid: false` OR file missing, set `data/state/generation_status.json` to `{status: pending_synthetic, reason: "source_missing"}` and `data/state/data_source.json` to `{source_type: "synthetic"}`. If `valid: true`, proceed to T011c1. **Guaranteed Output**: **MUST** write `data/state/generation_status.json` and `data/state/data_source.json` in all cases.
- [X] T011c1 [S] [US1] Implement `code/01_data_acquisition.py`: Step 2c-1 - **Exclusion & Logging for Missing Values**. **Dependency**: T011b. **Condition**: Run ONLY if T011b determines `valid: true` AND missing values exist in the dataset. **Logic**:
 - **If entries missing required fields**: Flag the entry as `[MISSING: requires exclusion]` and exclude it from the dataset.
 - **Implementation Detail**: Do NOT perform any imputation or mock computation. Simply remove the row from the working dataset.
 - **Constraint**: Ensure no synthetic or mock data is generated to fill gaps.
 - **Preservation**: **MUST preserve the original `data/raw/defect_dataset_2022.csv` unchanged**. Write the cleaned dataset to a NEW file: `data/raw/defect_dataset_2022_cleaned.csv`.
 - **Derivation Log**: Log the derivation chain in `data/state/derivation_log.json` (input file, output file, exclusion method).
 - **Output**: `data/raw/defect_dataset_2022_cleaned.csv` (if exclusions occurred) and `data/state/derivation_log.json`.
- [X] T011c2 [S] [US1] Implement `code/01_data_acquisition.py`: Step 2c-2 - **Exclusion Verification**. **Dependency**: T011c1. **Logic**: Count the number of entries excluded. **Verify** this count matches the number of entries in `data/state/derivation_log.json`. **Fail loudly** with `[ERROR: Exclusion count mismatch]` if they do not match. **Write** `data/state/exclusion_verification.json` with `{count: N, verified: true}`. **Output**: `data/state/exclusion_verification.json`.
- [X] T011c3 [S] [US1] Implement `code/01_data_acquisition.py`: Step 2c-3 - **Completion Signal**. **Dependency**: T011b, T011c2. **Logic**: **Always run**. If T011c1/2 were skipped (due to no missing values), write `data/state/completion_signal.json` with `{status: 'skipped', reason: 'no_missing_values'}`. If T011c1/2 ran, write `{status: 'completed', result: 'success'}`. **Output**: `data/state/completion_signal.json`.
- [X] T012 [S] [US1] Implement `code/01_data_acquisition.py`: Step 3 - **Source Validity Check & Branching**. **Dependency**: T011b, T011c3. Read `data/state/source_validation.json` and `data/state/completion_signal.json`.
 - **If `valid: false` OR `status: pending_synthetic`**: Mark source as invalid. **Write `data/state/generation_status.json` with `{status: pending_synthetic, reason: "source_invalid"}`**. **Write `data/state/data_source.json` with `{source_type: "synthetic", holdout_filename: "synthetic_holdout.csv", test_only: true}`**. Trigger T013.
 - **If `valid: true`**: Mark source as valid. **Write `data/state/generation_status.json` with `{status: valid, source: real}`**. **Write `data/state/data_source.json` with `{source_type: "real", holdout_filename: "real_holdout.csv", test_only: false}`**. Trigger T015.
 **Guaranteed Output**: **MUST** write `data/state/generation_status.json`, `data/state/source_status.json`, and **`data/state/data_source.json`** in all cases. **Output**: `data/state/generation_status.json`, `data/state/source_status.json`, `data/state/data_source.json`.
- [X] T013 [S] [US1] Implement `code/01_data_acquisition.py`: Step 4 - **Synthetic Data Generation (Test Only)**. **Dependency**: T012. **Condition**: Read `data/state/generation_status.json`. If `status: pending_synthetic`, generate `data/raw/synthetic_train.csv` using seed=42. **Parameters**: **N_TARGET=100**. **Logic**: Generate rows until N_TARGET is reached. **Runtime Check**: Estimate time = N_TARGET * avg_time_per_sample (calculated from a pilot sample of 10 rows). **If estimated time > 1 hour**, **FAIL THE BUILD** with `[ERROR: N=100 synthetic generation exceeds runtime limit]`. Do NOT scale down. **Surrogate Model**: Analytical signal = Continuum elasticity (`E = E0 * (1 - k*density)`) with **DFT-calibrated noise**. **Noise**: **Generate `data/raw/surrogate_noise_params.json` if missing** using default DFT-calibrated parameters (variance=0.05, mean=0.0). **Reproducibility**: Write the specific random seed, N_actual, and analytical formula parameters to `data/state/synthetic_config.json`. **Verification**: **MUST** verify `data/raw/synthetic_train.csv` has ≥100 rows and `data/state/synthetic_config.json` exists. **Guaranteed Output**: **MUST** write `data/raw/synthetic_train.csv`, `data/raw/surrogate_noise_params.json` (if generated), and `data/state/synthetic_config.json` even if generation encounters errors (write empty files with error logs). **Output**: `data/raw/synthetic_train.csv`, `data/state/synthetic_config.json`.
- [X] T013b [S] [US1] Implement `code/01_data_acquisition.py`: Step 4b - **Confounding Field Generation**. **Dependency**: T013. **Condition**: **Only if `data_source` is synthetic**. **Logic**: Check if `synthesis_method` or `grain_size` fields exist in `data/raw/synthetic_train.csv`. **If missing**: Generate synthetic values for these fields using a categorical distribution (e.g., 'Method A', 'Method B', 'Method C') and a continuous distribution for grain size (log-normal with parameters derived from typical 2D material synthesis: mean=100nm, std=50nm). **Output**: Update `data/raw/synthetic_train.csv` and `data/raw/synthetic_holdout.csv` (if generated) to include these fields. **Guaranteed Output**: **MUST** ensure `synthesis_method` and `grain_size` fields are present in synthetic datasets.
- [X] T014 [S] [US1] Implement `code/01_data_acquisition.py`: Step 4c - **Synthetic Hold-Out Generation**. **Dependency**: T012, T013. **Condition**: **Only if `data_source` is synthetic**. **Logic**: Generate a distinct synthetic hold-out set. **Physics Engine**: Use the **same analytical model family** (Continuum Elasticity) with a **different random seed** (read from `data/state/synthetic_config.json` to verify distinctness) to ensure distribution consistency. **Do NOT** rename synthetic files; retain the `synthetic_` prefix. **Output**: `data/raw/synthetic_holdout.csv`. **Guaranteed Output**: **MUST** write `data/raw/synthetic_holdout.csv` and update `data/state/data_source.json` with `holdout_filename`.
- [X] T015 [S] [US1] Implement `code/01_data_acquisition.py`: Step 5 - **Hold-Out Set Generation (Real)**. **Dependency**: T012, T011a. **Condition**: **Only if `data_source` is real**. **Logic**: Split `data/raw/defect_dataset_2022.csv` (or `defect_dataset_2022_cleaned.csv` if T011c ran) into train and hold-out using seed=42. Save hold-out to `data/raw/real_holdout.csv`. **This is a distinct split**. **Output**: `data/raw/real_holdout.csv`. **Guaranteed Output**: **MUST** write `data/raw/real_holdout.csv` and update `data/state/data_source.json` with `holdout_filename`.
- [X] T015b [S] [US1] Implement `code/01_data_acquisition.py`: Step 5b - **Real Data Confounding Field Handling**. **Dependency**: T015, T012. **Condition**: **Only if `data_source` is real**. **Logic**: Check if `synthesis_method` or `grain_size` fields exist in `data/raw/real_holdout.csv`. **If missing**: **Log a warning** that FR-013 confounding control is incomplete (cannot stratify or use covariates) and proceed without these controls. **Do NOT** generate synthetic values for real data. **Output**: `data/state/real_confounding_log.json` with `status: 'control_incomplete'`.
- [X] T016a [S] [US1] Implement `code/01_data_acquisition.py`: Step 6 - **Data Integrity & Hygiene**. **Dependency**: T012 (specifically `data/state/data_source.json`). **Logic**: Read `data/state/data_source.json` (T012) to determine which file to validate (T011a's output vs T013's output). Verify checksums, **verify all required fields**, flag missing values. Filter entries with defect density ≤0 or NaN; log count of excluded entries to `data/state/exclusion_log.json` (schema: `{filtered_count: N, reason: "density_leq_0_or_nan"}`). **Conditional Dependency**: **If T011c ran (real data), verify its exclusion log; if T011c was skipped (synthetic), skip verification of that specific artifact**. **Guaranteed Output**: **MUST** write `data/state/exclusion_log.json` and the validated raw file (even if empty). **Output**: `data/state/exclusion_log.json`, `data/raw/pristine_structures.csv` (validated).
- [X] T016b [S] [US1] Implement `code/01_data_acquisition.py`: Step 7 - **Synthetic Data Validation**. **Dependency**: T012, T013, T013b, T014. **Condition**: **Only if `data_source` is synthetic**. **Action**: **READ** `data/raw/synthetic_train.csv` (from T013) and `data/raw/synthetic_holdout.csv` (from T014). **READ** `data/state/data_source.json` (from T012) to determine the condition. Validate for **physical bounds** (e.g., conductivity > 0, defect density ∈ [low, moderate]). **Action**: **Automatically exclude** any entries violating bounds and log them to `data/state/synthetic_exclusions.json`. **Mandatory Derivation**: **MUST** create a distinct file `data/state/synthetic_exclusion_log.json` containing a list of excluded entry IDs and the specific reason for each exclusion (e.g. `{"id": "row_123", "reason": "conductivity <= 0"}`). **Do NOT** flag for manual review. **Output**: Write the cleaned dataset to **`data/raw/synthetic_train_cleaned.csv`** and generate **`data/state/synthetic_exclusion_derivation.json`** documenting the exclusion step and **`data/state/synthetic_exclusion_log.json`**. **Guaranteed Output**: **MUST** write `data/state/synthetic_exclusions.json`, `data/state/synthetic_exclusion_derivation.json`, `data/state/synthetic_exclusion_log.json`, and `data/raw/synthetic_train_cleaned.csv` (even if empty). **Output**: `data/state/synthetic_exclusions.json`, `data/state/synthetic_exclusion_derivation.json`, `data/state/synthetic_exclusion_log.json`, `data/raw/synthetic_train_cleaned.csv`.
- [X] T017 [US1] Implement `scripts/update_state_hashes.py` integration to record checksums of raw files, synthetic generator version (git hash), **and generator output parameters** in `state/projects/PROJ-209-...yaml`; also record `data_source` flag.

**Sequential Execution Note**: T010a runs first (including cache check/halt logic). T011a downloads and validates. T011b checks validity. T011c1 handles exclusion (conditional). T011c2 handles exclusion verification. T011c3 emits a completion signal (always runs). T012 checks validity and branches. T013 generates synthetic data if needed. T013b ensures confounding fields exist (synthetic only). T014/T015 generate hold-out sets. T015b handles real data confounding fields. T016a and T016b handle integrity and synthetic validation.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (real or synthetic data ready)

---

## Phase 4: User Story 2 - Statistical Modeling and Permutation Inference (Priority: P2)

**Goal**: Train Random Forest regressors for conductivity, Young's modulus, fracture strength; perform k-fold CV; generate p-values via permutation testing; apply Benjamini-Hochberg FDR control.

**Independent Test**: Can be fully tested by training the random forest models on a random split (80/20, seed=42), evaluating on the test split, and reporting R² and MAPE for all three target properties, including a comparison against a null model baseline.

### Implementation for User Story 2

- [X] T018 [S] [US2] Implement `code/02_data_processing.py`: **Dependency: T010a, T013, T014, T015, T016a, T016b**. Extract scalar reference values (σ₀, E₀, σ_f₀) from `data/raw/pristine_structures.csv` (T010a). **Normalization**: Compute relative changes (Δσ/σ₀, ΔE/E₀, Δσ_f/σ_f₀). **Exclusion**: **If pristine reference values are missing for an entry, exclude it from normalization and log it** per FR-003. **Logic**: **MUST write the list of excluded entries to `data/state/normalization_log.json`**. **Guaranteed Output**: **MUST** write `data/processed/features.csv`, `data/processed/targets.csv`, and `data/state/normalization_log.json` (even if empty). **Output**: `data/processed/features.csv`, `data/processed/targets.csv`, `data/state/normalization_log.json` (schema: `{excluded_ids: [string], count: int}`).
- [X] T019 [P] [US2] Implement `code/02_data_processing.py`: Update state file with SHA-256 checksums of processed features/targets
- [X] T020a [S] [US2] Implement `code/03_modeling.py`: Step 2a - **Compute Pairwise Stability**. **Dependency: T018**. **Action**: Compute Permutation Importance Stability for ALL predictor pairs by running **N_STABILITY_RUNS** (read from `config.py`, default 10) permutation runs for each feature pair. **Stability Metric**: **Variance of importance scores across N_STABILITY_RUNS**. **Store intermediate stability scores** in `data/processed/pairwise_stability.json`. **Output**: `data/processed/pairwise_stability.json`.
- [X] T020b [S] [US2] Implement `code/03_modeling.py`: Step 2b - **VIF Sensitivity Analysis**. **Dependency: T020a**. **Logic**: **If VIF > 5**:
 1. Load `data/processed/pairwise_stability.json` (from T020a).
 2. Identify features with VIF > 5.
 3. **Train two models**: Model A (with correlated features) and Model B (without correlated features).
 4. **Compare** R² and MAPE between Model A and Model B.
 5. **Log** the comparison results in `data/processed/feature_selection_log.json` (include iteration count, VIF, excluded features, R²/MAPE difference).
 6. **Do NOT automatically exclude** features. Proceed with the full feature set for the final model, but report the collinearity and the sensitivity analysis results.
 **Termination Logic**: If VIF ≤ 5, log `status: 'SUCCESS'`. If VIF > 5, log `status: 'COLLINEARITY_DETECTED'` and proceed with the full feature set.
 **Guaranteed Output**: **MUST** write `data/processed/feature_selection_log.json` with a `status` key set to either `'SUCCESS'` or `'COLLINEARITY_DETECTED'` and a `final_features` list, and `data/processed/pairwise_stability.json`. **Output**: `data/processed/final_features.csv` (list of selected features), `data/processed/feature_selection_log.json` (with `status` key), `data/processed/pairwise_stability.json`. **Constraint**: If VIF > 5, **report collinearity and perform sensitivity analysis**, do NOT automatically exclude.
- [X] T020c [S] [US2] Implement `code/03_modeling.py`: Step 2c - **Final Feature Set Logging**. **Dependency: T020b**. **Action**: Log the final feature set and VIF status. **Output**: `data/processed/final_features.csv`.
- [X] T021 [S] [US2] Implement `code/03_modeling.py`: Step 3 - **Model Training**. **Dependency: T020c, T018**. **Read** `data/processed/final_features.csv` (T020c) and `data/processed/features.csv` (T018). **CRITICAL CHECK**: **MUST** read `data/processed/feature_selection_log.json` (from T020b) and verify the `status` field.
 - **If `status` is 'COLLINEARITY_DETECTED'**: **MUST** log a high-severity warning to `data/state/modeling_warnings.json` indicating that collinearity was detected and sensitivity analysis was performed. Proceed with training using the full feature set.
 - **If `status` is 'SUCCESS'**: Proceed with training.
 **Execute**: Train Random Forest regressors (conductivity, Young's modulus, fracture strength) with **a standard train-test split (seed=42)** using the **final feature set** from T020c. **Note**: Feature selection (T020) is complete; use the final feature set. **Guaranteed Output**: **MUST** write `data/processed/final_models.pkl` and `data/processed/training_metrics.json` even if training fails (write empty/error files). **Output**: `data/processed/final_models.pkl`, `data/processed/training_metrics.json`.
- [X] T022a [S] [US2] Implement `code/03_modeling.py`: Step 4a - **Stratification Logic (Synthetic)**. **Dependency: T018, T020c, T012**. **Condition**: **Only if `data_source` is synthetic**. **Read** `data/processed/features.csv` (T018). **Logic**: Check if 'synthesis_method' or 'grain_size' is present (guaranteed by T013b if synthetic) and has >= 3 distinct values with sufficient sample size. **Check Config**: Read `config.py` for `STRATIFY_PREFERRED` (default True).
 - **If `STRATIFY_PREFERRED` is True AND fields exist AND have >= 3 distinct values**: **Execute** training of separate models per stratum and **report** metrics per stratum.
 - **Else (fields missing or insufficient)**: **Proceed with covariate inclusion** (include fields as covariates if present, or log `status: 'covariate_attempted (field_missing)'`). **Do NOT abort**. Log `status: 'covariate_path'` to `data/processed/stratification_results.json`.
 **Guaranteed Output**: **MUST** write `data/processed/stratification_results.json` in all cases.
- [X] T022b [S] [US2] Implement `code/03_modeling.py`: Step 4b - **Confounding Control Logic (Real)**. **Dependency: T018, T020c, T015b, T012**. **Condition**: **Only if `data_source` is real**. **Read** `data/processed/features.csv` (T018). **Logic**: Check if 'synthesis_method' or 'grain_size' fields exist. **If fields are missing entirely**: **Log warning that FR-013 control is incomplete** (cannot stratify or use covariates) and proceed. **If fields exist**: **Execute** training of separate models per stratum or include as covariates. **Output**: `data/processed/stratification_results.json` with `status: 'stratified'`, `status: 'covariate'`, or `status: 'control_incomplete'`. **Guaranteed Output**: **MUST** write `data/processed/stratification_results.json` in all cases.
- [X] T022c [S] [US2] Implement `code/03_modeling.py`: Step 4c - **Stratification Complete Signal**. **Dependency**: T022a OR T022b (whichever is applicable based on `data_source`). **Logic**: **Always run**. Write a unified signal `data/processed/stratification_complete.json` with `status: 'complete'` to indicate that stratification/confounding logic has finished. **Output**: `data/processed/stratification_complete.json`.
- [X] T023 [S][US2] Implement `code/04_inference.py`: **Permutation Testing & p-value Generation**. **Dependency: T021, T020c**. **Action**: Generate p-values via **N_PERMUTATIONS** (dynamically determined, minimum 1000) permutations (shuffling target values) for **every feature for every target property**. **Seed**: Use seed=42 for permutation shuffling to ensure reproducibility. **Convergence Verification Step**: **Run a pilot set (N=100 permutations)** to estimate variance. **If variance > threshold**, increase N_PERMUTATIONS dynamically until convergence is reached, but **N=1000 is the minimum floor**. **Log** the result in `data/processed/permutation_sufficiency.json` with `n_permutations_used`, `sufficiency_justification`, and `convergence_status`. **Justification**: N_PERMUTATIONS is dynamically adjusted to ensure statistical power as mandated by FR-011 and SC-004, with a hard floor of 1000. **Output**: `data/processed/permutation_pvalues.json` containing raw p-values and feature importance scores. **Constraint**: This step MUST complete before T024.
- [X] T023a [S] [US2] Implement `code/04_inference.py`: **Model Evaluation & Baseline Comparison**. **Dependency: T021**. **Action**:
 1. Train a null model (predict mean of target) on the training set. Evaluate on the test set. **Output**: `data/processed/baseline_metrics.json` with `R2_null` and `MAPE_null` for all three properties.
 2. Compare model R² against `R2_null`. **Compute** `improvement_over_null` and assign `label` ('Method Validation' if synthetic, 'External Validation' if real). **Output**: `data/processed/scope_note.json` with `improvement_over_null` and `label`.
 **Guaranteed Output**: **MUST** write `data/processed/baseline_metrics.json` and `data/processed/scope_note.json`.
- [X] T023b [S] [US2] Implement `code/04_inference.py`: **P-Value Completeness Verification**. **Dependency: T023**. **Action**: **Verify** that the input p-values in `data/processed/permutation_pvalues.json` cover **all features** (from `data/processed/final_features.csv`) and **all target properties** (conductivity, Young's modulus, fracture strength). **Log** verification result in `data/processed/pvalue_completeness.json` with `status: 'complete'` or `status: 'incomplete'` and `missing_features` list. **Constraint**: T024 MUST NOT run if `status: 'incomplete'`. **Output**: `data/processed/pvalue_completeness.json`.
- [X] T024 [S] [US2] Implement `code/04_inference.py`: **FDR Correction**. **Dependency: T023b**. **Input**: Read `data/processed/permutation_pvalues.json`. **Verification**: **Verify that input p-values are derived from 'permutation testing'** (check source metadata). If not, fail with `[ERROR: p-values not from permutation testing]`. **Action**: Apply Benjamini-Hochberg FDR control at q ≤ 0.05 to p-values across all hypothesis tests. **Output**: Update `data/processed/model_outputs.json` with `fdr_adjusted_p` and `is_significant` fields.
- [X] T025 [S] [US2] Implement `code/04_inference.py`: **Hold-Out Evaluation**. **Dependency: T012, T021, T014 (if synthetic) OR T015 (if real)**. **Logic**: Read `data/state/data_source.json` (from **T012**) to determine `data_source`. **Verification**: **MUST verify that the file specified in `data/state/data_source.json` (`holdout_filename`) exists and matches the expected schema**. **If synthetic**: **Verify distinct seed** by reading `data/state/synthetic_config.json` and confirming the hold-out seed differs from the train seed. **If real**: Verify split metadata. **If missing or invalid seed**: fail with `[ERROR: Hold-out file missing or not distinct]`.
 - **If `source: real`**: Evaluate final models on `data/raw/real_holdout.csv` (from T015).
 - **If `source: synthetic`**: Evaluate final models on `data/raw/synthetic_holdout.csv` (from T014).
 **Output**: `data/processed/holdout_metrics.json` with `{"source_type": "synthetic|real", "R2":..., "MAPE":..., "label": "Method Validation|External Validation"}`. **Constraint**: Must run on the distinct physics engine split or distinct real data split. **Note**: T025 depends on T021 (Model Training) and T012 (Source Selection); T021 does not depend on T025, so no circular dependency exists.
- [X] T027 [S] [US2/US3] Implement `code/04_inference.py`: **Sensitivity Analysis**. **Dependency: T022c**. **Input**: Read `data/processed/model_outputs.json` and `data/processed/stratification_results.json` (from T022). **Trigger**: **If T022 reports stratification OR if a decision cutoff exists**. **Action**: **Sweep decision cutoffs**:
 - **Step 1**: Attempt to calculate **deciles** of defect density.
 - **Step 2**: **Feasibility Check**: If dataset is too small (<10 samples per bin) or deciles are not feasible, **fallback to sparse thresholds** (e.g., {10th, 50th, 90th percentile} or {low, medium, high}). **Log** the decision (deciles vs. sparse) and the specific thresholds used in `data/validation/sensitivity_config.json`.
 - **Binary Definition**: Define binary target: **'True' if actual relative change (ΔP/P₀) < -threshold**, **'False' otherwise**. **Threshold Unit**: **fraction, e.g., 0.1**.
 - **Report**: **R² and MAPE** variation across the swept set. **R²** = Coefficient of Determination, **MAPE** = Mean Absolute Percentage Error, calculated for each threshold bin.
 **Output**: `data/validation/sensitivity_table.csv`. **Dependency**: T022 (for cv_std and stratification status).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (models trained, inference complete)

---

## Phase 5: User Story 3 - Validation, Sensitivity Analysis, and Reproducibility (Priority: P3)

**Goal**: Conduct permutation importance stability analysis, sensitivity analysis on thresholds, and generate the Validation Report. Package workflow in a reproducible Jupyter notebook.

**Independent Test**: Can be fully tested by running the complete notebook end-to-end on a CPU-only runner, verifying that all analyses complete within 6 hours and the sensitivity analysis produces a table showing how R² and MAPE vary across the swept thresholds.

### Implementation for User Story 3

- [X] T029 [P] [US3] Implement `code/05_validation.py`: **Permutation Importance Stability**. Compute stability metrics for top influential descriptors; report ranked list; **flag collinearity if VIF > 5**. (Note: Stability metrics are already computed in T020a; this task focuses on reporting final stability metrics).
- [X] T031 [S] [US3] Implement `code/05_validation.py`: **External Validation Logic**. **Dependency: T010a, T011a, T018, T011c3**. Read `data/state/data_source.json`. **External Search Logic**: **Check `data/validation/external/` for any valid dataset** and **scan pre-defined list of candidate datasets** (read list from `data/validation/external_sources.json`). **Log** the search attempt (keywords used, repositories queried, results) in `data/validation/search_log.json`.
 - **If External Data Found**: Run validation and report results.
 - **If No External Data Found**: Generate `data/validation/Validation_Report.json` with **status: NO_EXTERNAL_DATA**, **method: internal_only**, **data_source** flag, and **exclusion_count**.
 - **Exclusion Count Logic**: **Check if `derivation_log.json` exists**. **If exists**: use its count. **If not exists**: set `exclusion_count` to 0.
 **Guaranteed Output**: **MUST** write `data/validation/Validation_Report.json` and `data/validation/search_log.json` in all cases. **Output**: `data/validation/Validation_Report.json`, `data/validation/search_log.json`.
- [X] T032 [US3] Implement `notebooks/01_full_workflow.ipynb`: **Reproducible Jupyter notebook** integrating all steps (Data Acquisition → Processing → Modeling → Inference → Validation).
- [X] T033 [US3] Implement `notebooks/01_full_workflow.ipynb`: Ensure notebook runs within **6-hour** runtime limit on GitHub Actions free-tier (CPU, ≤7 GB RAM). **Action**: **Measure and record** actual runtime and peak RAM usage during execution. **Output**: `data/validation/runtime_metrics.json` containing `p95_latency`, `peak_ram_gb`, and `total_runtime`.
- [X] T033b [S] [US3] Implement `scripts/run_ci_validation.sh`: **Runtime Enforcement**. **Dependency: T033**. **Action**: Read `data/validation/runtime_metrics.json`. **If `total_runtime` > 6 hours**: **Fail the build** with `[ERROR: Runtime limit exceeded (SC-006)]`. **Output**: Exit code 0 if pass, 1 if fail.
- [X] T034 [US3] Implement `scripts/run_ci_validation.sh`: CI script to execute the full workflow and validate runtime constraints (≤6h) and memory usage (≤7GB).
- [X] T035 [S] [US3] Implement `code/run_workflow.py`: **Orchestration Script**. **Action**: Create `code/run_workflow.py` to orchestrate the pipeline steps in the correct order (T010a → T011a → T012 → T013/15 → T018 → T020b → T021 → T022 → T023 → T024 → T025 → T027 → T031). **Logic**: Read `data/state/data_source.json` to determine which data files to use. **Output**: A single executable script that runs the full workflow end-to-end. **Verification**: **MUST** run successfully from a clean state. **Output**: `code/run_workflow.py`. **Note**: This script also reconciles the run-book with the implementation.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T035a [P] Update `docs/README.md` with project overview and setup instructions
- [X] T035b [P] Update `docs/API.md` with synthetic generator API documentation
- [X] T036 [P] Refactor `code/01_data_acquisition.py` to remove hardcoded paths and use `config.py`
- [X] T037 [P] Add unit test `tests/unit/test_synthetic_generator.py` for synthetic data generation logic
- [X] T038 [P] Add unit test `tests/unit/test_data_processing.py` for normalization logic
- [X] T039 [P] Run `quickstart.md` validation to ensure end-to-end reproducibility
- [X] T040 [S] [US3] Implement `code/run_workflow.py`: **Reconcile run-book vs implementation**: **Dependency: T036**. **Action**: Verify that `code/run_workflow.py` (T035) correctly orchestrates the pipeline steps as defined in the run-book, ensuring no hardcoded paths remain and all dependencies are resolved. **Output**: A validated `code/run_workflow.py` that matches the run-book. **Note**: This task is sequential to T036 to ensure the codebase is in the expected state before reconciliation.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on models from US2

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
- Different models within a story marked [P] can run in parallel

---

## Summary

```bash
# Launch all tasks for User Story 1 together (data acquisition and generation):
# Note: T010a is Sequential (S) and starts first.
# T011a runs after T010a (output).
# T011b runs after T011a.
# T011c1 runs after T011a (if valid).
# T011c2 runs after T011c1.
# T011c3 runs after T011c2.
# T012 runs after T011b and T011c3.
# T013 and T016 run after T012, conditional on T012's output.
# T013b runs after T013.
# T014 and T015 depend on T012.
# T016a and T016b depend on T012.
Task: "Query Materials Project REST API for ≥50 pristine graphene and MoS₂ structures. " (T010a)
# T011a runs after T010a (output).
# T011b runs after T011a.
# T011c1 runs after T011a (if valid).
# T011c2 runs after T011c1.
# T011c3 runs after T011c2.
# T012 runs after T011b and T011c3.
# T013 and T016 run after T012, conditional on T012's output.
# T013b runs after T013.
# T014 and T015 depend on T012.
# T016a and T016b depend on T012.
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify data real or synthetic with correct fields)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Models trained, inference done)
4. Add User Story 3 → Test independently → Deploy/Demo (Validation complete)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data)
 - Developer B: User Story 2 (Modeling)
 - Developer C: User Story 3 (Validation)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [S] tasks = Sequential (must run after specific dependencies)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [X] T035 [P] [US3] Implement `code/run_workflow.py`: **Orchestration Script**: The quickstart run-book invokes this script. This task creates `code/run_workflow.py` to orchestrate the pipeline steps in the correct order (T010a → T011a → T012 → T013/15 → T018 → T020b → T021 → T022 → T023 → T024 → T025 → T027 → T031). **Logic**: Read `data/state/data_source.json` to determine which data files to use. **Output**: A single executable script that runs the full workflow end-to-end. **Verification**: **MUST** run successfully from a clean state. **Output**: `code/run_workflow.py`. **Note**: This task also serves to reconcile the run-book with the implementation.

---

## Phase Revision: Addressing Reviewer Concerns (Mode B)

**Goal**: Resolve specific issues raised by `/speckit.analyze` regarding data provenance, synthetic data contamination, and missing validation steps.

- [ ] T041 [S] [US1] **Implement Strict Real Data Fetch with No Synthetic Fallback**: **Dependency: T010a, T011a**. **Action**: Modify `code/01_data_acquisition.py` to **remove any logic that generates or uses synthetic data if the real "2022 supplementary CSV/JSON" is missing**. **Logic**: If `data/raw/defect_dataset_2022.csv` is missing or invalid, the script MUST **HALT immediately** with `[ERROR: Primary real dataset missing; scientific analysis cannot proceed]`. **Constraint**: **Do NOT** invoke `mock_dftb_simulate` or generate synthetic data for scientific analysis. Synthetic data generation (T013) is **ONLY** for pipeline testing if explicitly triggered by a `--test-only` flag, and the resulting `Validation_Report.json` MUST explicitly state `status: NO_REAL_DATA`. **Rationale**: The spec requires scientific analysis to halt if the real dataset is unavailable; synthetic data is strictly for testing, not for deriving scientific conclusions.
- [ ] T042 [S] [US1] **Add Explicit Synthetic Data Flagging and Exclusion**: **Dependency: T013**. **Action**: Ensure that any synthetic data generated (for testing only) is **explicitly flagged** in the metadata. **Logic**: When `data/raw/synthetic_train.csv` is generated, write a metadata file `data/state/synthetic_data_flag.json` with `is_synthetic: true`, `purpose: "pipeline_testing_only"`, and `excluded_from_science: true`. **Action**: Update `code/04_inference.py` and `code/05_validation.py` to **read this flag** and **exclude** any results derived from synthetic data from the final scientific report. **Output**: `data/state/synthetic_data_flag.json` and updated `data/validation/Validation_Report.json` with a `synthetic_data_included: false` field. **Rationale**: Prevents accidental inclusion of synthetic data in scientific conclusions, addressing the "fabrication" concern.
- [ ] T043 [S] [US3] **Implement Mandatory External Data Search with Detailed Logging**: **Dependency: T031**. **Action**: Enhance the external validation logic to **perform a detailed, logged search** for external datasets. **Logic**: Read a list of candidate dataset sources (e.g., specific URLs, package names) from `data/validation/external_sources.json`. **Action**: For each source, attempt to fetch or verify existence. **Log** every attempt (source, method, result) in `data/validation/search_log.json`. **If no external data is found**, the `Validation_Report.json` MUST include a `search_summary` field detailing the sources checked and the outcome. **Output**: Updated `data/validation/search_log.json` and `data/validation/Validation_Report.json`. **Rationale**: Ensures transparency and rigor in the validation process, proving that external data was actively sought.
- [ ] T044 [S] [US2] **Enforce Permutation Testing Convergence Check**: **Dependency: T023**. **Action**: Strengthen the convergence check in `code/04_inference.py`. **Logic**: The pilot set (N=100) must **explicitly calculate** the standard deviation of p-values. **If the standard deviation exceeds a defined threshold**, the script MUST **automatically increase N_PERMUTATIONS** (e.g., double it) and re-run until convergence or a maximum limit (e.g., N=5000) is reached. **Log** the final N_PERMUTATIONS and the convergence status in `data/processed/permutation_sufficiency.json`. **Constraint**: If convergence is not reached within the maximum limit, the workflow MUST **FAIL** with `[ERROR: Permutation testing did not converge]`. **Output**: Updated `data/processed/permutation_sufficiency.json` and `data/processed/permutation_pvalues.json`. **Rationale**: Ensures statistical robustness of p-values, addressing concerns about the reliability of the FDR control.
- [ ] T045 [S] [US3] **Add Runtime and Memory Profiling to Notebook**: **Dependency: T033**. **Action**: Integrate `memory_profiler` and `time` modules into `notebooks/01_full_workflow.ipynb`. **Logic**: Wrap each major step (data acquisition, modeling, inference) with timing and memory usage decorators. **Action**: Write the detailed profile (step name, duration, peak memory) to `data/validation/runtime_metrics.json`. **Constraint**: The notebook must **abort** if any single step exceeds a substantial duration or memory footprint, logging the specific step and resource usage. **Output**: Updated `notebooks/01_full_workflow.ipynb` and `data/validation/runtime_metrics.json`. **Rationale**: Proactively manages resource constraints, ensuring the workflow stays within the 6-hour/7 GB limit.