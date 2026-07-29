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
- [X] T005 [P] Implement `src/config.py` for environment configuration (API keys, paths, seeds, and runtime parameters like N_PERMUTATIONS, N_TARGET, MIN_DENSITY=1e-6)
- [X] T006 [P] Create `src/logging_config.py` for structured logging of workflow steps and errors
- [X] T007 Create base data models: `src/models/defect_entry.py` (DefectEntry entity) and `src/models/material_property.py` (MaterialProperty entity)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Synthetic Generation (Priority: P1) 🎯 MVP

**Goal**: Download pristine structures from Materials Project, attempt to fetch the 2022 Supplementary Defect Dataset, and generate a physics-based synthetic fallback if the real data is missing/invalid.

**Independent Test**: Can be fully tested by successfully downloading pristine structures, attempting to parse the defect dataset (or generating synthetic data if missing), and verifying that all required fields (defect type, defect density, conductivity, elastic tensor, fracture energy) are present and non-null in the resulting dataset.

### Implementation for User Story 1

- [ ] T010a [S] [US1] Implement `code/01_data_acquisition.py`: Step 1a - **Pristine Structure API Query**. Query **Materials Project REST API** for ≥50 pristine graphene and MoS₂ structures. **Logic**: Implement exponential backoff with a configurable retry limit for API calls. **Output**: `data/raw/pristine_structures.csv` (even if empty or error-filled) and `data/state/data_source.json` (initially `{"status": "real", "source": "materials_project"}` or `{"status": "error", "source": "none"}`). **Guaranteed Output**: **MUST** write `data/raw/pristine_structures.csv` and `data/state/data_source.json` in all cases.
- [ ] T010b [S] [US1] Implement `code/01_data_acquisition.py`: Step 1b - **Cache Fallback Logic**. **Dependency**: T010a. **Conditional Execution**: **Execute ONLY IF T010a fails after retries**. **Logic**: If API fails after retries, attempt to load cached pristine structures from `data/raw/pristine_structures.csv` (if it exists and is valid). **On Success**: Write `data/state/cache_load_log.json` with `{source: 'cache', timestamp:...}`. **On Failure**: Abort with `[ERROR: API access unavailable and no cache present]`. **Output**: `data/state/abort_log.json` (schema: `{status: 'ABORT', reason: string, timestamp: string}`) or `data/state/cache_load_log.json`. **Guaranteed Output**: **MUST** write `data/state/abort_log.json` on failure.
- [ ] T011a [S] [US1] Implement `code/01_data_acquisition.py`: Step 2a - **Defect Dataset Download & Validation**. Attempt to download the **2022 Supplementary Defect Dataset** to `data/raw/defect_dataset_2022.csv`. **Logic**: Validate file existence and basic schema (presence of required columns: `defect_type`, `defect_density`, `conductivity`, `elastic_tensor`, `fracture_energy`). **Flagging**: **UNCONDITIONALLY** flag missing values and exclude entries if mock DFTB+ fallback is not available (see T011b-2). **Guaranteed Output**: **MUST** write `data/raw/defect_dataset_2022.csv` (even if empty) and `data/state/source_validation.json` (schema: `{"valid": boolean, "reason": "string", "exclusions": int}`) in all cases.
- [ ] T011b-1 [S] [US1] Implement `code/01_data_acquisition.py`: Step 2b-1 - **Missing Value Identification**. **Dependency**: T011a. **Logic**: Scan `data/raw/defect_dataset_2022.csv` for missing `fracture_energy` values. **Action**: Create `data/state/missing_fracture_energy_ids.json` (list of entry IDs). **Guaranteed Output**: **MUST** write `data/state/missing_fracture_energy_ids.json` (even if empty). **Output**: `data/state/missing_fracture_energy_ids.json`.
- [ ] T011b-2 [S] [US1] Implement `code/01_data_acquisition.py`: Step 2b-2 - **Mock DFTB+ Fallback & Exclusion**. **Dependency**: T011a, T011b-1. **Condition**: **Execute if**: `data/state/data_source.json` indicates **REAL** data AND `data/state/missing_fracture_energy_ids.json` is not empty. **Logic**: For entries in `data/state/missing_fracture_energy_ids.json`, attempt a **mock DFTB+ fallback** (best effort, ≤300 seconds). **Constraint**: The fallback MUST use a physics-constrained generator (not random) and must return values within physical bounds (`[MIN_DENSITY, 10.0] J/m²`). **Algorithm**: **If fallback succeeds**: Update the in-memory row with the imputed value. Write the updated row to `data/raw/defect_dataset_2022.csv` before completing. **If fallback fails**: Exclude the entry from the dataset. **Verification**: **MUST** write `data/state/mock_dftb_exclusions.json` containing a list of excluded IDs AND a `count` field that matches the number of excluded entries. **Action**: If mock DFTB+ fails, calculate the **mean of existing fracture_energy values** in the dataset and use that as the imputed value. If no existing values exist, exclude the entry. **Guaranteed Output**: **MUST** write `data/state/mock_dftb_exclusions.json` (if exclusions occurred) or an empty file. **MUST** write `data/raw/defect_dataset_2022.csv` (updated) in the success case. **Output**: `data/state/mock_dftb_exclusions.json`, `data/raw/defect_dataset_2022.csv`. **Note**: This task is skipped if `data_source.json` indicates synthetic data or if no missing values exist.
- [ ] T012 [S] [US1] Implement `code/01_data_acquisition.py`: Step 3 - **Source Validity Check & Branching**. **Dependency**: T011a, T011b-1. Read `data/state/source_validation.json`.
 - **If `valid: false`** (Source missing or invalid): Mark source as invalid. Write `data/state/generation_status.json` with `{status: pending_synthetic, reason: "source_invalid"}`. Write `data/state/data_source.json` with `{source_type: "synthetic", holdout_filename: "synthetic_holdout.csv"}`. Trigger T013 (Synthetic Generation).
 - **If `valid: true`** (Source exists but may have minor gaps handled in T011b-2): Mark source as valid. Write `data/state/generation_status.json` with `{status: valid, source: real}`. Write `data/state/data_source.json` with `{source_type: "real", holdout_filename: "real_holdout.csv"}`. Trigger T016a (Data Integrity).
 **Guaranteed Output**: **MUST** write `data/state/generation_status.json`, `data/state/source_status.json` (schema: `{valid: boolean, source_type: string, reason: string}`) and `data/state/data_source.json` in all cases. **Output**: `data/state/generation_status.json`, `data/state/source_status.json`, `data/state/data_source.json`.
- [ ] T013 [S] [US1] Implement `code/01_data_acquisition.py`: Step 4 - **Synthetic Data Generation**. **Dependency**: T012. **Condition**: Read `data/state/generation_status.json`. If `status: pending_synthetic`, generate `data/raw/synthetic_train.csv` using seed=42. **Parameters**: **N_TARGET=1000**, **N_MIN=100**. **Logic**: Generate rows until N_TARGET is reached. **Runtime Check**: Measure time for first 10 rows. If projected total runtime > 4 hours, scale down to N_MIN=100. **Surrogate Model**: Analytical signal = Continuum elasticity (`E = E0 * (1 - k*density)`); Noise = DFT-calibrated noise parameters (Gaussian, sigma derived from DFT dataset variance). **Reproducibility**: Write the specific random seed, N_actual, and analytical formula parameters to `data/state/synthetic_config.json`. **Guaranteed Output**: **MUST** write `data/raw/synthetic_train.csv` and `data/state/synthetic_config.json` even if generation encounters errors (write empty files with error logs). **Output**: `data/raw/synthetic_train.csv`, `data/state/synthetic_config.json`.
- [ ] T015 [S] [US1] Implement `code/01_data_acquisition.py`: Step 5 - **Hold-Out Set Generation**. **Dependency**: T012. **Conditional Dependency**: T013 (**ONLY IF** `data/state/data_source.json` indicates synthetic). **Logic**: Read `data/state/data_source.json` to determine source type.
 - **If Real Data**: Split `data/raw/defect_dataset_2022.csv` into train and hold-out using seed=42. Save hold-out to `data/raw/real_holdout.csv`.
 - **If Synthetic Data**: Generate a distinct synthetic hold-out set. Physics Engine: Use a Lattice Model (`E = E0 * (1 - k2*density^2)`) with `k2` distinct from the training model. **Validation**: Perform a Kolmogorov-Smirnov (KS) test to confirm the hold-out distribution is statistically distinct from the training set (p < 0.05). **Fallback**: If KS test fails, regenerate with increased noise variance (up to 3 attempts). If all attempts fail, log 'KS_DISTINCTNESS_UNREACHABLE' and proceed with the last generated set.
 - **Conditional Output**: If real, write `data/raw/real_holdout.csv`; else, write `data/raw/synthetic_holdout.csv`. Traceability: Explicitly write the `data_source` flag (real vs. synthetic) and the exact hold-out filename to `data/state/data_source.json`. **Guaranteed Output**: MUST write `data/state/data_source.json` with keys `source_type` ('real' or 'synthetic') and `holdout_filename` in all cases. **Output**: `data/raw/real_holdout.csv` (if real) or `data/raw/synthetic_holdout.csv` (if synthetic), `data/state/data_source.json`.
- [ ] T016a [S] [US1] Implement `code/01_data_acquisition.py`: Step 6 - **Data Integrity & Hygiene**. Dependency: T011a, T011b-2 (conditional), T012, T015. Verify checksums, verify all required fields, flag missing values. Filter entries with defect density ≤0 or NaN; log count of excluded entries to `data/state/exclusion_log.json` (schema: `{filtered_count: N, reason: "density_leq_0_or_nan"}`). Logic: Read `data/state/data_source.json` to determine which file to validate. Conditional Dependency: If T011b-2 ran (real data), verify its exclusion log; if T011b-2 was skipped (synthetic), skip verification of that specific artifact. Guaranteed Output: MUST write `data/state/exclusion_log.json` and the validated raw file (even if empty). Output: `data/state/exclusion_log.json`, `data/raw/pristine_structures.csv` (validated).
- [ ] T016b [S] [US1] Implement `code/01_data_acquisition.py`: Step 7 - **Synthetic Data Validation**. Dependency: T012, T013, T015. Condition: Only if `data_source` is synthetic. Action: READ `data/raw/synthetic_train.csv`. Validate for physical bounds (e.g., conductivity > 0, defect density ∈ [`config.MIN_DENSITY`, 0.1]). Action: Exclude any entries violating bounds and log them to `data/state/synthetic_exclusions.json`. Guaranteed Output: MUST write `data/state/synthetic_exclusions.json` and cleaned `data/raw/synthetic_train.csv` (even if empty). Output: `data/state/synthetic_exclusions.json`, `data/raw/synthetic_train.csv`.
- [X] T017 [US1] Implement `scripts/update_state_hashes.py` integration to record checksums of raw files and synthetic generator version (git hash) in `state/projects/PROJ-209-...yaml`; also record `data_source` flag.
- [ ] T017b [S] [US1] Implement `code/01_data_acquisition.py`: Step 8 - **Synthetic Provenance Metadata**. **Dependency**: T013. **Logic**: If `data_source` is synthetic, generate `data/state/synthetic_provenance.json` containing: exact analytical formulas used, noise parameters (sigma, seed), and the specific DFT dataset used for calibration (if any). **Guaranteed Output**: **MUST** write `data/state/synthetic_provenance.json` if synthetic data is used. **Output**: `data/state/synthetic_provenance.json`.

**Sequential Execution Note**: T010a runs first. T010b handles cache fallback (conditional). T011a downloads and validates. T011b-1 identifies missing values. T012 checks validity and branches. T011b-2 runs ONLY IF T012 confirms real data and missing values exist. T013 generates synthetic data if needed. T015 generates hold-out set. T016a and T016b handle integrity and synthetic validation. T017b generates provenance metadata.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (real or synthetic data ready)

---

## Phase 4: User Story 2 - Statistical Modeling and Permutation Inference (Priority: P2)

**Goal**: Train Random Forest regressors for conductivity, Young's modulus, fracture strength; perform k-fold CV; generate p-values via permutation testing; apply Benjamini-Hochberg FDR control.

**Independent Test**: Can be fully tested by training the random forest models on a random split (80/20, seed=42), evaluating on the test split, and reporting R² and MAPE for all three target properties, including a comparison against a null model baseline.

### Implementation for User Story 2

- [ ] T018 [S] [US2] Implement `code/02_data_processing.py`: Dependency: T010a, T012, T015. Extract scalar reference values (σ₀, E₀, σ_f₀) from `data/raw/pristine_structures.csv`. Normalization: Compute relative changes (Δσ/σ₀, ΔE/E₀, Δσ_f/σ_f₀). Exclusion: If pristine reference values are missing for an entry, exclude it from normalization and log it. Logic: MUST write the list of excluded entries to `data/state/normalization_log.json`. Guaranteed Output: MUST write `data/processed/features.csv`, `data/processed/targets.csv`, and `data/state/normalization_log.json` (even if empty). Output: `data/processed/features.csv`, `data/processed/targets.csv`, `data/state/normalization_log.json` (schema: `{excluded_ids: [string], count: int}`).
- [X] T019 [P] [US2] Implement `code/02_data_processing.py`: Update state file with SHA-256 checksums of processed features/targets
- [ ] T020 [S] [US2] Implement `code/03_modeling.py`: Step 2 - **Feature Selection & Collinearity Control**. **Dependency**: T018, T012. **Conditional Dependency**: T013 (ONLY IF synthetic, handled by T018). **Phase 1 (Pruning Loop)**: While VIF > 5 AND features > 1: Train a temporary Random Forest model internally (not saved) on current features. Compute Permutation Importance (mean score) for all features using `statsmodels.stats.outliers_influence.variance_inflation_factor` for VIF. Identify feature with the lowest mean importance (tie-breaker: lowest stability/variance). Exclude the feature with the lowest mean importance. Re-calculate VIF on remaining features. Log exclusion in `data/processed/feature_selection_log.json`. **Phase 2 (Final Re-Evaluation)**: **AFTER the loop completes**, re-train the final Random Forest model on the reduced feature set. **MUST re-run full k-fold cross-validation (k=5) and permutation testing on this final model** to ensure reported metrics (R², MAPE, p-values) correspond to the final reduced feature set. Termination Logic: If VIF > 5 after features are exhausted, log `status: 'COLLINEARITY_UNRESOLVED'` and proceed with the single feature. Guaranteed Output: MUST write `data/processed/feature_selection_log.json` with a `status` key set to either `'SUCCESS'` or `'COLLINEARITY_UNRESOLVED'` and a `final_features` list. Output: `data/processed/final_features.csv`, `data/processed/feature_selection_log.json`.
- [ ] T021 [S] [US2] Implement `code/03_modeling.py`: Step 3 - **Final Model Training & Evaluation**. Dependency: T020, T018. Read `data/processed/final_features.csv` and `data/processed/features.csv`. **Action**: Train Random Forest regressors (conductivity, Young's modulus, fracture strength) with a standard train-test split (seed=42) using the **final feature set** from T020. **Re-Run**: **MUST re-run full k-fold cross-validation (k=5) and permutation testing on this final model** to ensure reported metrics (R², MAPE, p-values) correspond to the final reduced feature set. Guaranteed Output: MUST write `data/processed/final_models.pkl` and `data/processed/training_metrics.json` even if training fails (write empty/error files). Output: `data/processed/final_models.pkl`, `data/processed/training_metrics.json`.
- [ ] T022a [S] [US2] Implement `code/03_modeling.py`: Step 4a - Stratification Logic. Dependency: T021. Check if 'synthesis_method' or 'grain_size' is present and has >= 3 distinct values with sufficient sample size. If stratification fields exist and STRATIFY_PREFERRED is True, train separate models per stratum and report metrics per stratum. Output: `data/processed/stratification_log.json`.
- [ ] T022b [S] [US2] Implement `code/03_modeling.py`: Step 4b - Covariate Fallback. Dependency: T021. If no stratification fields exist, include 'synthesis_method' or 'grain_size' as covariates in the model. Output: `data/processed/stratification_log.json`.
- [ ] T022c [S] [US2] Implement `code/03_modeling.py`: Step 4c - **Synthetic Confounding Generation**. **Dependency**: T012, T013. **Condition**: **ONLY IF `data_source` is synthetic**. **Logic**: Generate synthetic 'synthesis_method' and 'grain_size' columns with realistic distributions to enable stratification/covariate control. **Verification**: **MUST verify** that the generated columns have **>= 3 distinct values**. If not, regenerate with adjusted parameters (up to 3 attempts). If all attempts fail, log `status: 'CONFUNDING_GEN_FAILED'` to `data/processed/confounding_log.json`. **Output**: `data/processed/features.csv` (updated with synthetic columns), `data/processed/confounding_log.json`.
- [ ] T022d [S] [US2] Implement `code/03_modeling.py`: Step 4d - **Real Data Confounding Flag**. **Dependency**: T012, T011a. **Condition**: **ONLY IF `data_source` is real**. **Logic**: Check if 'synthesis_method' or 'grain_size' columns exist. If missing, log 'CONFOUNDING_CONTROL_UNAVAILABLE' to `data/processed/confounding_log.json` and **flag the dataset** as unable to control for this confounder. Do not proceed with stratification/covariate control. **Output**: `data/processed/confounding_log.json`.
- [ ] T022e [S] [US2] Implement `code/03_modeling.py`: Step 4e - **Confounding Control Verification**. **Dependency**: T022a, T022b, T022c, T022d. **Logic**: **MUST verify** that confounding control (stratification or covariate inclusion) was successfully applied or explicitly logged as unavailable. **Check**: If `data/processed/confounding_log.json` indicates failure or unavailability, write `data/processed/confounding_control_status.json` with `status: 'FAILED'` and `reason: 'FR-013_CONTROL_UNMET'`. If successful, write `status: 'SUCCESS'`. **Guaranteed Output**: **MUST** write `data/processed/confounding_control_status.json` in all cases. **Output**: `data/processed/confounding_control_status.json`.
- [ ] T023 [S] [US2] Implement `code/04_inference.py`: Permutation Testing & p-value Generation. Dependency: T021. Generate p-values via N_PERMUTATIONS permutations (shuffling target values) for every feature for every target property. Sufficiency Check: Run a preliminary convergence test with a sufficient number of permutations to ensure stability. If p-value variance > 0.01, increase N_PERMUTATIONS until convergence is achieved. Output: `data/processed/permutation_pvalues.json`.
- [ ] T023a [S] [US2] Implement `code/04_inference.py`: Baseline. Dependency: T021. Train a null model (predict mean of target) on the training set. Evaluate on the test set. Output: `data/processed/baseline_metrics.json`.
- [ ] T023b [S] [US2] Implement `code/04_inference.py`: **Null Baseline Comparison & Confidence Flag**. Dependency: T023a, T021. Compare model R² against `R2_null`. Compute `improvement_over_null` = R² - R²_null. **Flag Logic**: If `improvement_over_null` > 0.1, flag as 'high-confidence'; else 'low'. **Output**: **MUST write** `improvement_over_null` and `confidence_flag` ('high' or 'low') to `data/processed/model_outputs.json` (the primary artifact). **Output**: Update `data/processed/model_outputs.json` with `improvement_over_null` and `confidence_flag`.
- [ ] T024 [S] [US2] Implement `code/04_inference.py`: FDR Correction. Dependency: T023. Apply Benjamini-Hochberg FDR control at q ≤ 0.05 to p-values across all hypothesis tests. Output: Update `data/processed/model_outputs.json` with `fdr_adjusted_p` and `is_significant` fields.
- [ ] T025 [S] [US2] Implement `code/04_inference.py`: Hold-Out Evaluation. Dependency: T015, T021, T012. Evaluate final models on the appropriate holdout set (real or synthetic). Output: `data/processed/holdout_metrics.json`.
- [ ] T027 [S] [US3] Implement `code/04_inference.py`: Sensitivity Analysis. **Dependency**: T022e, T025. Sweep decision cutoffs (deciles or sparse thresholds) and report FPR/FNR variation. Output: `data/validation/sensitivity_table.csv`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (models trained, inference complete)

---

## Phase 5: User Story 3 - Validation, Sensitivity Analysis, and Reproducibility (Priority: P3)

**Goal**: Conduct permutation importance stability analysis, sensitivity analysis on thresholds, and generate the Validation Report. Package workflow in a reproducible Jupyter notebook.

**Independent Test**: Can be fully tested by running the complete notebook end-to-end on a CPU-only runner, verifying that all analyses complete within 6 hours and the sensitivity analysis produces a table showing how False Positive Rate (FPR) and False Negative Rate (FNR) vary across the swept thresholds.

### Implementation for User Story 3

- [ ] T029 [S] [US3] Implement `code/05_validation.py`: Permutation Importance Stability. Compute stability metrics for top influential descriptors; report ranked list. Dependency: T021.
- [ ] T031 [S] [US3] Implement `code/05_validation.py`: External Validation Logic. Dependency: T010a, T011a, T018. Check for external dataset; if none, generate `Validation_Report.json`.
- [X] T032 [US3] Implement `notebooks/01_full_workflow.ipynb`: Reproducible Jupyter notebook integrating all steps (Data Acquisition → Processing → Modeling → Inference → Validation).
- [X] T033 [US3] Implement `notebooks/01_full_workflow.ipynb`: Ensure notebook runs within 6-hour runtime limit on GitHub Actions free-tier (CPU, ≤7 GB RAM).
- [X] T034 [US3] Implement `scripts/run_ci_validation.sh`: CI script to execute the full workflow and validate runtime constraints (≤6h).

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

This plan implements a computational workflow to quantify how topological defects (dislocations, grain boundaries) in 2D materials (graphene, MoS₂) alter electronic conductivity, Young's modulus, and fracture strength. The approach combines data acquisition from the Materials Project API (with a synthetic data fallback), statistical modeling via Random Forest regressors, and rigorous inference using permutation testing with Benjamini-Hochberg FDR control. The workflow is designed to run entirely on a CPU-only GitHub Actions free-tier runner, utilizing streaming where possible and sampling to fit within 7GB RAM / 6h limits.

## Notes

- [P] tasks = different files, no dependencies
- [S] tasks = Sequential (must run after specific dependencies)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group