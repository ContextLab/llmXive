---
description: "Task list template for feature implementation"
---

# Tasks: Predicting Plant Disease Resistance from Publicly Available Metabolomic Data

**Input**: Design documents from `/specs/001-predicting-plant-disease-resistance/`
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

## Phase 2: Foundational & Edge-Case Handlers (Blocking Prerequisites)

**Purpose**: Core infrastructure and CRITICAL edge-case handlers that MUST be complete before ANY user story can be implemented. **Must run before Phase 0.**

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. Phase 2 tasks provide constants, contracts, utilities, and the mandatory error-handling logic (T034, T036, T039) required by all subsequent phases.

- [X] T004 [P] Implement `code/utils/constants.py` with random seeds (`random_state=42`), file paths, and hypothesis thresholds (Balanced Acc > 0.75). **Define `HOLD_OUT_FRACTION = 0.20` for T020a. Define `MAX_DEPTH_GRID` as a set of increasing grid depths for T020b. Define `N_PERMUTATIONS = 1000` for T021b. Define `N_ESTIMATORS = 500` for T020b. Define `MIN_SAMPLES_FOR_HOLDOUT = 50` for T020a. Define `LEARNING_CURVE_STEEPNESS_THRESHOLD = 0.01` (slope value) for T038. Define `STREAMING_THRESHOLD = 1024**3` (1GB) for T039. Define `MIN_METABOLITES_FOR_COMBAT = 10` for T016-impl-align.**
- [X] T005 [P] Implement `code/utils/io.py` for checksumming (MD5/SHA256) and logging artifacts to `state/artifact_hashes.yaml`
- [X] T006 [P] **Create and Validate** `contracts/metadata.schema.yaml`. **Write the file** with valid JSON Schema draft-07 syntax defining `MetaboliteProfile` and `ResistanceLabel`. **Validation Scope**: Perform **syntax-only validation** (JSON Schema validity) at that stage. **Do NOT validate against real data yet**. **Output**: `state/schema_validation_log.txt`. **Note**: Semantic validation against real data will occur in T015-exec/T014b-exec.
- [X] T007 [P] **Create and Validate** `contracts/output.schema.yaml`. **Write the file** with valid JSON Schema draft-07 syntax defining `metrics.json` and `shap_analysis.json` structures. **Validation Scope**: Perform **syntax-only validation** (JSON Schema validity) at that stage. **Do NOT validate against real data yet**. **Output**: `state/schema_validation_log.txt`. **Note**: Semantic validation against real data will occur in T024.
- [X] T008 [P] Setup `tests/unit/` structure and `pytest.ini` configuration
- [X] T009 [P] Unit test for `code/data/download.py` verifying Metabolomics Workbench HTTP fetch and file storage in `tests/unit/test_download.py`
- [X] T010 [P] Unit test for `code/data/validate_temporal.py` verifying timestamp checks in `tests/unit/test_temporal.py`
- [X] T011 [P] Integration test for full preprocessing pipeline (download → validate → preprocess → harmonize) in `tests/integration/test_full_pipeline.py`
- [X] T034 [P] [US1] **Implement** robust data fetching in `code/data/download.py` to **FAIL LOUDLY**. **Logic**: Remove any `try/except` blocks that catch network errors and fall back to `generate_synthetic_*()` or `mock_*()` data. If `requests.get()` fails or returns a non-200 status, **raise a custom `DataFetchError`** with a clear message indicating the specific study ID and URL that failed. **Verification**: Run unit test `tests/unit/test_download.py` simulating a network failure; assert that the test raises `DataFetchError` and no synthetic data is generated.
- [X] T036 [P] [US1] **Implement** ComBat strict enforcement in `code/data/preprocess.py`. **Logic**: Wrap the ComBat execution in a `try/except` block that catches `ConvergenceWarning` or `LinAlgError`. If ComBat fails to converge, **raise a `BatchCorrectionFailureError` with a detailed message and HALT the pipeline**. **Do NOT fall back to mean-centering**. **Note**: This enforces FR-004 and Principle VI strictly. **Verification**: Run integration test with a synthetic dataset designed to trigger ComBat divergence; verify that `BatchCorrectionFailureError` is raised and the pipeline stops. **This task includes the logic previously in T046.**
- [X] T039 [P] [US1] **Implement** explicit streaming and chunking logic in `code/data/download.py` for large datasets. **Logic**: If a downloaded CSV exceeds `STREAMING_THRESHOLD` (1GB), switch to a streaming reader (`pandas.read_csv(chunksize=10000)`). Process data in chunks without loading the entire file into RAM. **Output**: Update `data/processed/preprocess_log.json` to indicate if streaming was used. **Verification**: Run a test with a simulated large file (or a real large study if available) and verify that memory usage remains bounded and processing completes successfully.

**Checkpoint**: Foundation and Edge Handlers ready - user story implementation can now begin in parallel

---

## Phase 0: Data Acquisition & Verification (FR-001, FR-014)

**Purpose**: Identify, verify, download, and validate public datasets. **Depends on T004, T006, T039 (Phase 2).**
**Ordering Note**: Phase 2 tasks (T004, T006, T039) MUST be completed before starting this phase. The chain is: T012a -> T012a-ser -> T012a-val -> T013c -> T013c-verify -> T012b -> T013 -> T013-verify -> T015a -> T015a-exec -> T015b -> T015b-exec -> T016-impl-log -> T016-impl-align -> T016-impl-missing -> T016-impl-combat -> T015-exec -> T017b.

- [X] T012a [P] **Discover** available plant metabolomics studies. **Logic**: Query the Metabolomics Workbench **search** API (endpoint: `) to retrieve a list of studies. **Output**: Write a JSON list to `data/raw/study_manifest_raw.json` containing an array of objects with keys `study_id` (string), `title` (string), and `download_url` (string). **Verification**: Run script and verify `data/raw/study_manifest_raw.json` exists, is non-empty, and contains the required keys. **Note**: This task does NOT filter for resistance metadata yet; that is handled in T013c.

- [ ] T012a-ser [P] **Serialize** study manifest. **Pre-requisite**: T012a must complete. **Logic**: Read `data/raw/study_manifest_raw.json`. Write to `data/raw/study_manifest.json` with sorted keys. **Output**: `data/raw/study_manifest.json`. **Verification**: Verify file exists and is valid JSON.

- [ ] T012a-val [P] **Validate** study manifest against contracts/metadata.schema.yaml. **Pre-requisite**: T012a-ser and T006 must complete. **Logic**: Load `data/raw/study_manifest.json` and validate against `contracts/metadata.schema.yaml`. **Output**: Write `state/schema_validation_log.txt` with pass/fail status. **Verification**: Verify log file exists.

- [ ] T012b [P] **Download** Phenotype and Intensity data for discovered studies. **Pre-requisite**: T012a-val must complete. **Logic**: For each study in `data/raw/study_manifest.json`, fetch the phenotype and raw intensity files using the `download_url` and study-specific endpoints (e.g., `https://www.metabolomicsworkbench.org/data/study.php?STUDY_ID={id}`). **Output**: Save raw files to `data/raw/{study_id}_phenotype.csv` and `data/raw/{study_id}_raw_intensity.csv`. **Verification**: Verify files exist and are non-empty.

- [ ] T013c [US1] **Filter** studies for resistance metadata. **Pre-requisite**: T012a-val must complete successfully. **Pre-check**: Verify `data/raw/study_manifest.json` exists. **Logic**: Implement script `code/data/filter_studies.py` to read `data/raw/study_manifest.json`. For each study, fetch phenotype metadata. Filter for studies containing both `pre-challenge`/`baseline` metabolite profiles and `disease resistance`/`phenotype` metadata. **Specific Column Checks**: Search for columns named 'phenotype', 'resistance_score', 'disease_status', or 'challenge_outcome' in the phenotype file. **Value Mapping**: Map {'resistant', 'R', 1, 'Yes', 'YES', 'Resistant'} -> 1; {'susceptible', 'S', 0, 'No', 'NO', 'Susceptible'} -> 0 (case-insensitive). **Output**: Write `data/raw/filtered_study_manifest.json` containing all studies (even if count is 0). **Verification**: Verify file exists, is valid JSON, and contains an array of objects with the correct keys. **Note**: This task does NOT halt on zero count; that is handled by T013c-verify.

- [ ] T013c-verify [US1] **Verify** study count for FR-001. **Pre-requisite**: T013c must complete. **Logic**: Read `data/raw/filtered_study_manifest.json`. Count entries. **If count < 1**: **Write `data/raw/error_log.txt`** with message "No studies found with required resistance metadata. FR-001 not met." and **raise `DataAvailabilityError`** to halt. **If count >= 1**: Proceed. **Output**: Log success to `data/raw/study_count_verification.log`. **Verification**: Verify log file exists and contains success message OR verify `error_log.txt` exists if halted.

- [X] T013 [US1] **Implement** `code/data/validate_temporal.py` to verify FR-014: **Explicitly check metadata for 'pre-challenge', 'baseline', or timestamps prior to pathogen inoculation.** **Specific Fields**: Check for fields named 'timepoint', 'sample_date', 'collection_date', or 'inoculation_date'. **Logic**: **Guarantee**: Write `data/processed/temporal_validation_log.json` with empty entries for all studies immediately upon script start. For each study, check fields. If fields are missing or timestamps are ambiguous, **mark the study as 'unverified' and log a `TemporalVerificationWarning`** (do NOT halt the pipeline for the whole project, but flag the specific study). **Output**: Write `data/processed/temporal_validation_log.json` indicating pass/fail/warning per study. **Exit Code**: Exit with a success indicator if at least one study is verified; Exit with a failure indicator only if NO studies are verified. **Verification**: Run script and ensure it correctly flags studies and logs warnings for ambiguous metadata without crashing the entire pipeline. **Ensure `temporal_validation_log.json` is always written.**

- [X] T013-verify [US1] **Verify** temporal validation results. **Pre-requisite**: T013 must complete. **Logic**: Read `data/processed/temporal_validation_log.json`. Count 'verified' studies. **If count < 1**: Raise `TemporalVerificationError` with message "No studies verified for pre-challenge distinctness. FR-014 not met." and halt. **If count >= 1**: Proceed. **Output**: Log success to `data/processed/temporal_verification_log.log`. **Verification**: Verify log file exists and contains success message. **Also check `data/raw/error_log.txt` if T013c-verify halted.**

- [ ] T015a [US1] **Detect** label heterogeneity. **Pre-requisite**: T013-verify must complete successfully. **Pre-check**: Verify `data/raw/{study_id}_phenotype.csv` exists for each study. If missing, raise `DataUnavailableError` with message "Raw phenotype files missing. Run T012b first." **Logic**: Implement script `code/data/detect_heterogeneity.py` to load raw labels. Analyze `measurement_method` and `assay_score` distribution to detect heterogeneity (defined as >2 unique methods OR mixed binary/ordinal scales). **Output Schema**: Generate `data/processed/heterogeneity_report.json` containing `study_id`, `heterogeneity_detected` (bool), `methods` (list of strings), `score_types` (list of strings: 'binary', 'ordinal'). **Verification**: Run script and verify output file exists and contains valid JSON with required keys.

- [ ] T015a-exec [US1] **Execute** Heterogeneity Detection. **Pre-requisite**: T015a must complete. **Logic**: Run `python code/data/detect_heterogeneity.py`. **Output**: Generate `data/processed/heterogeneity_report.json`. **Verification**: Verify file exists and is non-empty.

- [ ] T015b [US1] **Implement** `code/data/harmonize.py` for label harmonization (FR-013). **Pre-requisite**: T015a-exec must complete. **Input**: `data/raw/{study_id}_phenotype.csv` and `data/processed/heterogeneity_report.json`. **Logic**:
 1. **If heterogeneity exists (including multi-study binary scenarios)**: Stratify labels by `measurement_method` OR apply z-scoring within study **ONLY for ORDINAL labels**.
 2. **If binary labels are present**: Map directly to 0/1 (Susceptible/Resistant) without z-scoring.
 3. **If no heterogeneity (single binary method, single study)**: Apply global alignment logic (0/1).
 4. **Output**: Generate `data/processed/harmonized_labels.csv` containing standardized binary (0/1) or z-scored labels.
 **Verification**: Run script and verify output file contains harmonized labels with no missing values.

- [X] T015b-exec [US1] **Execute** Label Harmonization. **Pre-requisite**: T015b must complete. **Logic**: Run `python code/data/harmonize.py`. **Output**: Generate `data/processed/harmonized_labels.csv`. **Verification**: Verify file exists and is non-empty.

- [ ] T016-impl-log [US1] **Implement** log-transformation in `code/data/preprocess.py`. **Pre-requisite**: T012b must complete. **Logic**: Implement function `log_transform()` in `code/data/preprocess.py` and a CLI entry point `run_log_transform()` that reads `data/raw/{study_id}_raw_intensity.csv` and writes `data/processed/log_transformed_matrix.csv`. **Output**: Generate `data/processed/log_transformed_matrix.csv`. **Verification**: Verify file exists and contains log-transformed values.

- [ ] T016-impl-align [US1] **Implement** InChIKey alignment in `code/data/preprocess.py`. **Pre-requisite**: T016-impl-log must complete. **Logic**: Implement function `align_metabolites()` in `code/data/preprocess.py` and a CLI entry point that reads `data/processed/log_transformed_matrix.csv` and writes `data/processed/aligned_matrix.csv`. **Handle InChIKey alignment failures**: Log missing metabolites to `results/alignment_missing.json`. **Check intersection**: If intersection < `MIN_METABOLITES_FOR_COMBAT` (10) AND the number of studies combined is >= 2, **raise a `DataAlignmentError` with message 'Alignment reduced to {count} metabolites. Minimum required: 10. HALTING.' and HALT the pipeline**. **Do NOT proceed**. **Output**: Generate `data/processed/aligned_matrix.csv`. **Verification**: Verify file exists and contains aligned metabolites. **Verification**: Run with studies having <10 common metabolites (and >=2 studies); verify pipeline halts with the specific error.

- [ ] T016-impl-missing [US1] **Implement** missing value filtering in `code/data/preprocess.py`. **Pre-requisite**: T016-impl-align must complete. **Logic**: Implement function `filter_missing_values()` in `code/data/preprocess.py` and a CLI entry point that reads `data/processed/aligned_matrix.csv` and writes `data/processed/filtered_matrix.csv`. **Output**: Generate `data/processed/filtered_matrix.csv`. **Verification**: Verify file exists and contains only features with <30% missing values.

- [ ] T016-impl-combat [US1] **Implement** ComBat batch-effect correction in `code/data/preprocess.py`. **Pre-requisite**: T016-impl-missing must complete. **Logic**: Implement function `apply_combat()` in `code/data/preprocess.py` and a CLI entry point that reads `data/processed/filtered_matrix.csv` and writes `data/processed/batch_corrected_matrix.csv`. **Pre-requisite**: T036 must complete. **Output**: Generate `data/processed/batch_corrected_matrix.csv`. **Verification**: Verify file exists and contains batch-corrected values.

- [ ] T015-exec [US1] **Execute** Preprocessing. **Pre-requisite**: T016-impl-combat must complete. **Pre-check**: Verify `data/raw/filtered_study_manifest.json` (from T013c) and `data/processed/harmonized_labels.csv` (from T015b-exec) exist. If missing, raise `DataUnavailableError`. **Logic**: Run `python code/data/preprocess.py --step all`. **Output**: Generate `data/processed/batch_corrected_matrix.csv`, `data/processed/labels.csv` (merged with harmonized), and `data/processed/preprocess_log.json`. **Verification**: Verify file existence, non-empty content, and record SHA256 checksums. **Explicitly check** that `preprocess_log.json` contains `batch_correction: applied` if study count >= 2. **Verify compliance with Constitution Principle VI** (Metabolomic Data Integration) by ensuring batch correction is applied when required.

- [X] T017b [US1] **Verify** preprocessing outputs. **Pre-requisite**: T015-exec must complete. **Logic**: Verify file existence, non-empty content, and record SHA256 checksums in `state/artifact_hashes.yaml`. If files are missing or empty, raise an error and halt.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download, normalize, align, and harmonize public metabolomics datasets from Metabolomics Workbench containing pre-challenge profiles and resistance metadata.

**Independent Test**: Verify data downloads (≥1 study), normalization outputs (log-transformed, missing >30% discarded), label harmonization (z-scoring/stratification), and batch-effect correction (ComBat) via script execution.

### Implementation for User Story 1

- [X] T016 [P] Add logging functions for data acquisition and preprocessing steps to `code/utils/io.py`. **Ensure functions exist before T015 is implemented.**

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Validation (Priority: P2)

**Goal**: Train a constrained Random Forest classifier with rigorous stratified cross-validation, permutation testing, and sensitivity analysis to test the predictive relationship without circular validation.

**Independent Test**: Verify balanced accuracy on hold-out set, feature selection within CV folds, permutation testing (≥1000), FDR correction, and sensitivity analysis sweeps.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for `code/modeling/train.py` verifying stratified split and hold-out reservation (FR-006) in `tests/unit/test_modeling.py`
- [X] T019 [P] [US2] Unit test for `code/modeling/evaluate.py` verifying permutation distribution generation in `tests/unit/test_modeling.py`

### Implementation for User Story 2

- [X] T020a [US2] **Data Splitting & Learning Curve Config**. **Pre-requisite**: T017b must complete. **Pre-check**: Verify `data/processed/batch_corrected_matrix.csv` exists. If missing, raise `DataUnavailableError` with message "Preprocessed data missing. Run T015-exec first." **Logic**: Implement script `code/modeling/split_data.py` to load `data/processed/batch_corrected_matrix.csv` and `data/processed/labels.csv`. Count samples (N). **Output**:
 * If N >= `MIN_SAMPLES_FOR_HOLDOUT` (from T004): Generate `data/processed/split_config.json` containing `hold_out_fraction` and `random_state`.
 * If N < `MIN_SAMPLES_FOR_HOLDOUT` (from T004): Generate `data/processed/learning_curve_config.json` containing `fractions` (list of floats), `min_samples`, `max_samples`, and `random_state`. **Action**: **Route to T038 (Learning Curve Analysis)**. **Do NOT raise DataSufficiencyError**. **Flag this as a Power Limitation** but proceed with T038.
 **Verification**: Verify output file exists and contains the correct keys. Verify that the pipeline routes to T038 if N < 50.
- [X] T020a-exec [US2] **Execute** Data Splitting. **Pre-requisite**: T020a must complete. **Logic**: Run `python code/modeling/split_data.py --config data/processed/split_config.json` (or `learning_curve_config.json`).
 * If N >= `MIN_SAMPLES_FOR_HOLDOUT` (from T004): Execute stratified split using `split_config.json` to create `train_indices` and `holdout_indices`. Save to `data/processed/split_indices.json`.
 * If N < `MIN_SAMPLES_FOR_HOLDOUT` (from T004): **Skip splitting**. **Set `route_to_learning_curve=true` in `split_config.json` and exit with code 0 to trigger T038**.
 **Output**: Save `data/processed/split_indices.json` (if N>=50).
 **Verification**: Verify output file exists and contains the correct keys if N>=50.
- [X] T038 [US2] **Implement** learning curve power analysis. **Pre-requisite**: T020a must complete. **Logic**: In `code/modeling/evaluate.py`, if N < 50, perform the learning curve analysis. Implement function `run_learning_curve_analysis()` and a CLI entry point that reads `data/processed/batch_corrected_matrix.csv` and writes `results/learning_curve.json`. Calculate the slope of the learning curve using linear regression (scikit-learn `LinearRegression`) on (sample_size, accuracy) points. **Compare** the calculated slope against `LEARNING_CURVE_STEEPNESS_THRESHOLD` from T004. **If** the slope > threshold, **flag the result in `results/learning_curve.json` with a `power_limitation_warning`** and **do NOT** proceed to claim statistical significance for the model performance. **Output**: Save `results/learning_curve.json` containing `accuracy_vs_sample_size`, `slope`, and `power_warning` fields. **Verification**: Run integration test with a small dataset (N=30) and verify the warning is present in the output JSON and the slope is calculated correctly.
- [X] T020b-train [US2] **Model Training**. **Pre-requisite**: T020a-exec must complete (if N>=50) or T038 (if N<50). **Logic**: Implement script `code/modeling/train.py` to read `data/processed/split_indices.json` (or full data), train Random Forest (n_estimators=500, max_depth=10) with Stratified k-fold CV (FR-005). Use a `param_grid` specifying a range of `max_depth` values for `GridSearchCV`. If N<50, run training on subsamples for learning curve. **Use `N_ESTIMATORS` from `code/utils/constants.py`**.
 **Output**: Save trained model object to `results/model.pkl`.
- [X] T020b-extract [US2] **Feature Importance Extraction**. **Pre-requisite**: T020b-train must complete. **Logic**: Implement script `code/modeling/extract_importance.py` to read `results/model.pkl` and write `results/feature_importance_ranking.json`. Extract feature importances from the trained model. Rank metabolites by mean decrease in impurity.
 **Output**: Save `results/feature_importance_ranking.json` containing the top-ranked metabolites.
- [X] T021a [US2] **Compute Correlations & FDR**. **Pre-requisite**: T015-exec must complete. **Logic**: Implement script `code/modeling/correlation_analysis.py` to read `data/processed/batch_corrected_matrix.csv` and `data/processed/labels.csv`. Compute pairwise correlations (metabolite vs. resistance). Apply Benjamini-Hochberg FDR correction to p-values before filtering. Filter for |r| > 0.4, p < 0.01.
 **Output**: Save `results/correlation_analysis_fdr_corrected.json` containing the filtered correlation data with **FDR-corrected p-values**.
 **Verification**: Verify output file exists and contains the correct keys. **Explicitly verify** that the output JSON includes entries meeting the |r| > 0.4 and p < 0.01 thresholds as required by SC-002.
- [X] T021b [US2] **Model Validation & Permutation Testing**. **Pre-requisite**: T020b-train must complete. **Logic**: Implement script `code/modeling/validate_model.py` to read `results/model.pkl` and `data/processed/split_indices.json` (if N>=50).
 * **If N >= `MIN_SAMPLES_FOR_HOLDOUT` (from T004)**: Compute Balanced Accuracy, ROC-AUC, Precision-Recall on the independent hold-out set. Run permutation testing with ≥1,000 permutations. **Use `random_state` from `code/utils/constants.py`**.
 * **If N < `MIN_SAMPLES_FOR_HOLDOUT` (from T004)**: **Skip hold-out validation**. **Route to T038**.
 **Output**: Save `results/model_validation.json`.
 **Verification**: Verify output file contains `balanced_accuracy`, `roc_auc`, and `permutation_p_value`. Ensure `random_state` was used.
- [X] T021b-exec [US2] **Execute** Model Validation & Permutation Testing. **Pre-requisite**: T021b must complete. **Logic**: Run `python code/modeling/validate_model.py`.
 * **If N >= `MIN_SAMPLES_FOR_HOLDOUT` (from T004)**: Before validation, check the distribution of `binary_label` in the hold-out set. If `holdout_positive_count == 0`, **raise `ClassImbalanceError` with message 'Class imbalance detected: 0 positive samples in hold-out set.'** and HALT. **Use the logic from T048 (now merged here)**. If valid, run validation script.
 * **If N < `MIN_SAMPLES_FOR_HOLDOUT` (from T004)**: **Skip**.
 **Output**: Save `results/model_validation.json`.
 **Verification**: Verify output file exists and contains the correct keys if N>=50.
- [X] T021d [US2] **Sensitivity Analysis**. **Pre-requisite**: T020b-train must complete. **Pre-requisite**: **T038 (if N < 50)**. **Logic**: Implement script `code/modeling/sensitivity_analysis.py` to read `results/model.pkl` and `data/processed/split_indices.json` (if N>=50) or `data/processed/batch_corrected_matrix.csv` (if N<50).
 * **If N >= `MIN_SAMPLES_FOR_HOLDOUT` (from T004)**: **Explicitly sweep probability decision thresholds over baseline +/- diff where diff is strictly the set {0.01, 0.05, 0.1} as required by FR-009**. (from FR-009). **Define `baseline = 0.5`** (or optimal threshold from T020b if available). Report False Positive Rate (FPR) and False Negative Rate (FNR) at each threshold using the hold-out set.
 * **If N < `MIN_SAMPLES_FOR_HOLDOUT` (from T004)**: **Do NOT skip**. Perform sensitivity analysis on the training set (via cross-validation) by sweeping thresholds on the predicted probabilities from the CV folds. **Explicitly sweep probability decision thresholds over baseline +/- diff where diff is strictly the set {0.01, 0.05, 0.1} as required by FR-009**. Report FPR and FNR at each threshold. **This ensures FR-009 is met for small datasets.**
 **Output**: Save `results/sensitivity_analysis.json`.
 **Output Schema**: `{"thresholds": [float], "fpr": [float], "fnr": [float]}`.
 **Verification**: Verify output file contains sensitivity metrics for all specified diff values **{0.01, 0.05, 0.1}**.
- [X] T021d-exec [US2] **Execute** Sensitivity Analysis. **Pre-requisite**: T021d must complete. **Logic**: Run `python code/modeling/sensitivity_analysis.py`. **Output**: Save `results/sensitivity_analysis.json`.
 **Verification**: Verify output file exists and contains the correct keys.
- [X] T022 [US2] **Implement** collinearity diagnostics (VIF calculation) for ALL features in the processed dataset. **Logic**: Implement script `code/modeling/vif_analysis.py` to read `data/processed/batch_corrected_matrix.csv` and write `results/vif_scores.json`. **Explicit Constraint**: **VIF scores are logged for biological interpretation ONLY and MUST NOT trigger feature removal or re-training**. This is for biological interpretation only and MUST NOT trigger feature removal or re-training, as per FR-012. **Verification**: Verify output file exists and contains VIF scores for all features. Ensure no feature filtering logic is applied based on VIF scores.
- [X] T022-exec [US2] **Execute** collinearity diagnostics. **Pre-requisite**: T022 must complete. **Logic**: Run `python code/modeling/vif_analysis.py`. **Output**: Save `results/vif_scores.json`.
 **Verification**: Verify output file exists and contains the correct keys.
- [X] T024-final-report [US2] **Generate Final Report**. **Pre-requisite**: T020b-extract, T021a, T022-exec, T021b-exec, T021d-exec must complete. **Logic**: Implement script `code/modeling/generate_report.py` to read `results/feature_importance_ranking.json`, `results/correlation_analysis_fdr_corrected.json`, `results/vif_scores.json`, `results/model_validation.json`, and `results/sensitivity_analysis.json`. Merge all data into a single canonical report. **Output**: Write `results/analysis_summary.json`. **Include `configuration` section** with `random_state_split`, `random_state_train`, `random_state_permutation`, `max_depth`, `n_estimators`. **Verification**: Ensure the aggregated file contains all keys and is valid JSON.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Biological Interpretation and Pathway Mapping (Priority: P3)

**Goal**: Extract feature importances and map top metabolites to known pathways via KEGG/MetaCyc to assess biological plausibility.

**Independent Test**: Verify top metabolites are extracted, mapped to ≥1 pathway each, and documented with literature references.

### Implementation for User Story 3

- [X] T025b [US3] **Generate** `data/mappings/synonyms.json`. **Logic**: Create a mapping file for metabolite synonyms to support fallback lookup. **Output**: Save `data/mappings/synonyms.json`.
- [X] T026a [US3] **Extract Top Metabolites**. **Pre-requisite**: T020b-extract must complete. **Pre-check**: Verify `results/feature_importance_ranking.json` exists. **Logic**: Implement script `code/modeling/extract_top_metabolites.py` to read `results/feature_importance_ranking.json` (output of T020b). Extract the top-ranked metabolites ranked by mean decrease in impurity.
 **Output**: Save `results/top_metabolites.json` containing the list of top 10 metabolites.
 **Verification**: Verify output file exists and contains the correct keys.
- [X] T026a-exec [US3] **Execute** Top Metabolites Extraction. **Pre-requisite**: T026a must complete. **Logic**: Run `python code/modeling/extract_top_metabolites.py`. **Output**: Save `results/top_metabolites.json`.
 **Verification**: Verify output file exists and contains the correct keys.
- [X] T026b [US3] **Map Pathways**. **Pre-requisite**: T026a-exec and T025b must complete. **Logic**: Implement script `code/modeling/map_pathways.py` to read `results/top_metabolites.json`. Map metabolites to KEGG/MetaCyc pathways using the KEGG REST API (` compound/{inchikey}`) with `inchikey` as the query parameter. **Fallback Strategy**: If primary mapping fails, attempt secondary lookup via metabolite synonyms from `data/mappings/synonyms.json`. **Retry Logic**: If KEGG API returns timeout/error, retry with exponential backoff (base delay 1s, multiplier 2, max delay 10s, up to 3 retries). **Strict Enforcement**: If after all retries and fallbacks, **zero metabolites are mapped**, **raise a `PathwayMappingError`** with message "Failed to map any top metabolites. FR-010 not met." and halt. **If >0 but <10 are mapped**, **log a warning** and **proceed** with partial mapping, updating the report to reflect the success rate. **Output**: Save `results/pathway_mappings.json` containing mapped pathways and a `mapping_success_rate` field. **Verification**: Verify output file exists and contains the correct keys. **If error is raised, verify `results/pathway_error.log` exists.**
- [X] T026b-exec [US3] **Execute** Pathway Mapping. **Pre-requisite**: T026b must complete. **Logic**: Run `python code/modeling/map_pathways.py`. **Output**: Save `results/pathway_mappings.json`.
 **Verification**: Verify output file exists and contains the correct keys.
- [X] T026c [US3] **Generate Report**. **Pre-requisite**: T026b-exec must complete. **Logic**: Implement script `code/modeling/generate_pathway_report.py` to read `results/pathway_mappings.json` and `results/top_metabolites.json`. Generate interpretation report discussing biological plausibility. Include the mandatory "framing" text: "These findings represent statistical associations between pre-challenge metabolite profiles and disease resistance phenotypes. No causal claims are made."
 **Output**: Save `results/pathway_report.json` containing the narrative report.
 **Verification**: Verify output file exists and contains the correct keys.
- [X] T026c-exec [US3] **Execute** Report Generation. **Pre-requisite**: T026c must complete. **Logic**: Run `python code/modeling/generate_pathway_report.py`. **Output**: Save `results/pathway_report.json`.
 **Verification**: Verify output file exists and contains the correct keys.
- [X] T027 [US3] **Execute** generation of `results/pathway_analysis.json` by merging results from T026a-exec (`top_metabolites.json`), T026b-exec (`pathway_mappings.json`), and T026c-exec (`pathway_report.json`) into a single canonical output file. **Logic**: Implement script `code/modeling/merge_pathway_results.py` to read `results/top_metabolites.json`, `results/pathway_mappings.json`, and `results/pathway_report.json`, and write `results/pathway_analysis.json`. **Verification**: Ensure the merged file contains all keys and is valid JSON.
- [X] T028 [US3] **Execute** generation of visualization `results/plots/pathway_barplot.png` based on data from `results/pathway_analysis.json`. **Pre-requisite**: T027 must complete. **Pre-check**: Verify `results/pathway_analysis.json` exists. **Logic**: Implement script `code/modeling/generate_pathway_plot.py` to read `results/pathway_analysis.json` and write `results/plots/pathway_barplot.png`. Generate a bar plot showing the number of mapped pathways per metabolite. **Output**: Save `results/plots/pathway_barplot.png`. **Verification**: Verify the plot file exists and is non-empty.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T029a [P] **Update** `README.md` with execution instructions and quickstart validation. Include the exact text "These findings represent statistical associations between pre-challenge metabolite profiles and disease resistance phenotypes. No causal claims are made." in the 'Limitations' or 'Warning' section of the README.
- [X] T029b [P] **Generate** `results/report_framing.md`, a human-readable narrative report.
- [X] T030a [P] **Configure** GitHub Actions workflow (`.github/workflows/ci.yml`) to define the pipeline environment, dependencies, and execution steps for the free-tier runner. **Content**: Create `.github/workflows/ci.yml` with:
 - `name: CI Pipeline`
 - `on: [push, pull_request]`
 - `jobs: build`
 - `runs-on: ubuntu-latest`
 - `steps`:
 - `Checkout code`
 - `Setup a compatible Python environment.`
 - `Install dependencies: pip install -r code/requirements.txt`
 - `Run Pipeline: python code/main.py`
 - `Upload artifacts: results/`
 - `timeout-minutes: [configured according to experimental constraints]`
 - `Note: See spec.md for research question, method, and references.`
 - **Verification**: Validate YAML syntax and ensure all steps are executable.
- [X] T030b [P] **Implement** `code/utils/ci_trigger.py` to write a self-contained Python script that triggers the GitHub Actions workflow and polls for completion with a timeout. **Logic**: Use GitHub API to trigger workflow_dispatch, then poll `runs` endpoint at regular intervals until status is 'completed' or timeout (min) is reached. **Pre-requisite**: T030a must be complete.
- [X] T030c [P] **Execute** `code/utils/ci_trigger.py` to trigger CI and verify success. **Logic**: Run `python code/utils/ci_trigger.py` to trigger the CI workflow and verify success. **Pre-requisite**: T030b must be complete. **Verification**: Verify the script returns success or a timeout error after polling the GitHub API. Do not rely on manual triggers.
- [X] T031 [P] **Verify Runtime Constraints**. **Logic**: Implement script `code/utils/profile_runtime.py` to run the permutation testing step (T021b) and sensitivity analysis (T021d) steps, measure time, and write `state/runtime_profile.json` with timing results and optimization decisions. **Implementation**: If profiling indicates risk, implement optimization strategies (e.g., `n_jobs=-1` for parallel permutations, chunking large datasets). **Output**: Write `state/runtime_profile.json` with timing results and optimization decisions. **Verification**: Ensure the profile confirms the time constraint is met. or mitigation strategies are in place.
- [X] T033 [P] **Verify** `state/artifact_hashes.yaml` tracks all data and model artifacts correctly. **Logic**: Implement script `code/utils/verify_artifacts.py` to check all data and model artifacts against `state/artifact_hashes.yaml`. **Verification**: Verify all artifacts are tracked.
- [X] T044 [P] **Verify** streaming logic in `code/data/download.py`. **Pre-requisite**: T039 must complete. **Logic**: This task explicitly verifies the implementation in T039. Run integration test with a simulated large file to verify streaming behavior. **Verification**: Ensure memory usage remains bounded and the streaming logic in T039 is functioning as intended.

**Checkpoint**: All reviewer concerns have been addressed and integrated into the main workflow.
