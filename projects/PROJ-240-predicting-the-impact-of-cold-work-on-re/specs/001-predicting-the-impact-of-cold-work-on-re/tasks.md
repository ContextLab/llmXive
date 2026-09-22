# Tasks: Predicting the Impact of Cold Work on Recrystallization Kinetics in Aluminum Alloys

**Input**: Design documents from `/specs/001-cold-work-recrystallization/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup & Foundational

**Purpose**: Project initialization, basic structure, and core infrastructure that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T001 [P] **Initialize project structure**. **Requirement**: Create all necessary directories and `.gitkeep` files for the project. **Directories**: `projects/PROJ-240-predicting-the-impact-of-cold-work-on-re/code`, `projects/PROJ-240-predicting-the-impact-of-cold-work-on-re/tests`, `projects/PROJ-240-predicting-the-impact-of-cold-work-on-re/data` (with subdirs `raw`, `processed`, `split`), `projects/PROJ-240-predicting-the-impact-of-cold-work-on-re/artifacts` (with subdirs `models`, `reports`, `figures`). **Config**: Create `code/config.py` with placeholders for `N_ROWS_TARGET` (default 10000), `N_PERMUTATIONS` (default 1000), `SEED` (default 42), `OUTLIER_PERCENTILE` (default 0.99), `N_ESTIMATORS` (default 100). **Verification**: Run `ls -R` and confirm all directories and files exist.
- [X] T013 [P] **Create pipeline orchestrator**. **Script**: `code/main.py`. **Logic**: Implement a sequential runner that executes: T011 -> T012 -> T021 -> T022 -> T024 -> T025 -> T029 -> T037 -> T039 -> T041 -> T042. **Requirement**: Must handle exit codes and print a summary of generated artifacts. **Dependency**: T001.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: User Story 1 - Data Ingestion and Feature Construction (Priority: P1) 🎯 MVP

**Goal**: Ingest raw experimental data (synthetic primary) and transform into a structured dataset with engineered interaction features.

**Independent Test**: The system can be tested by running the data pipeline on the synthetic generator (seed=42) and verifying the output DataFrame contains the required columns, calculated interaction features (`cold_work * Mn_content`, etc.), and no null values.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T015 [P] [US1] Write TDD unit test for physical bound validation in `tests/unit/test_validation.py` (test fails initially).
- [X] T016 [P] [US1] Write TDD unit test for interaction feature engineering in `tests/unit/test_engineering.py` (test fails initially).

### Implementation for User Story 1

- [ ] T011 [US1] **Generate deterministic synthetic baseline data**. **Script**: `code/generate_synthetic.py`. **Logic**: Generate exactly **10000 rows** using **seed=42** (hard-coded). **Schema**: Columns must include `cold_work_pct` (float, 0-100), `Mn_wt` (float), `Mg_wt` (float), `Si_wt` (float), `Cu_wt` (float), `annealing_temp_K` (float), `time_to_peak_min` (float). **Data Hygiene**: Compute SHA-256 checksum of `data/raw/synthetic_baseline.csv`, write the checksum to `data/raw/synthetic_baseline.csv.sha256`, and update `state/projects/PROJ-240-predicting-the-impact-of-cold-work-on-re.yaml` with the new checksum in `artifact_hashes`. **Verification**: Verify file exists, checksum matches, row count == 10000, and state YAML is updated. **Error Handling**: If generation fails, raise `RuntimeError` immediately; do NOT fall back to mock data. **Dependency**: T001.
- [X] T017 [US1] **Implement row filtering for missing "time-to-peak softening"** in `code/ingest.py` (exclude rows, do not impute target).
- [X] T018 [US1] **Implement physical bound validation** (0 ≤ cold work ≤ 100%, positive time) in `code/ingest.py`.
- [ ] T019 [US1] **Implement missing composition value handling** in `code/ingest.py`: Impute missing values in `Mn_wt`, `Mg_wt`, `Si_wt`, `Cu_wt` using the **mean of the specific column**. Do NOT use a global mean for all rows. **Output**: Save cleaned data to `data/processed/cleaned.csv`. **Dependency**: T018.
- [X] T020 [US1] **Implement unit normalization for time-to-peak (minutes)** in `code/ingest.py`.
- [ ] T021 [US1] **Implement outlier clipping on target variable** at the 99th percentile (read `OUTLIER_PERCENTILE` from `code/config.py`, default 0.99) to mitigate extreme value influence, as required by FR-007, in `code/ingest.py`. **Requirement**: The clipped data must be the ONLY data used for subsequent statistical tests. **Method**: Use `np.percentile` with `method='linear'`. **Artifact**: Write `clipped_outliers_count` (int) and `clipped_values_list` (list of integer row indices) to `artifacts/reports/validation_log.json`. **Output**: Save clipped dataset to **`data/processed/clipped.csv`**. **Data Hygiene**: Compute SHA-256 checksum of `data/processed/clipped.csv`, write the checksum to `data/processed/clipped.csv.sha256`, and update `state/projects/PROJ-240-predicting-the-impact-of-cold-work-on-re.yaml`. **Verification**: Assert that downstream tasks (T037, T039) reference `data/processed/validated_clipped.csv`, not raw data. **Dependency**: T020.
- [ ] T022 [US1] **Implement validation and size check in `code/ingest.py`**. **Logic**: Load `data/processed/clipped.csv` (from T021). **Fail-Fast**: Immediately check if dataset size < 50 rows (FR-008). If so, raise `ValueError` immediately before any further processing. **Transformation**: Verify all required columns exist. Save the validated data to **NEW artifact `data/processed/validated_clipped.csv`**. **Output**: `data/processed/validated_clipped.csv`. **Dependency**: T021.
- [X] T023 [US1] **Generate `artifacts/reports/ingestion_metrics.json` and update `artifacts/reports/validation_log.json`**. **Schema**: `ingestion_metrics.json` must contain `rows_ingested` (int), `rows_dropped_nulls` (int), `rows_dropped_other` (int, for bounds/target missing), `rows_output` (int). `null_handling_success_rate` must be calculated as `(rows_input - rows_dropped_nulls) / rows_input`. `validation_log.json` must contain `rows_ingested`, `rows_dropped_nulls`, `rows_dropped_other`, `clipped_outliers_count`, `clipped_values_list`, `threshold_99th_percentile`. **Requirement**: These metrics are required for SC-007. **Dependency**: Must run AFTER T022. **Logic**: Read `validation_log.json` from T022 and append metrics, do not overwrite.
- [ ] T024 [US1] **Implement interaction feature engineering in `code/engineer.py`**: Calculate `cold_work_Mn_content` (cold_work_pct * Mn_wt), `cold_work_Mg_content`, `cold_work_Si_content`, `cold_work_Cu_content`. **Constraint**: Do NOT include `cold_work * Temperature`. **Output Schema**: The output MUST contain ALL original raw columns (`cold_work_pct`, `Mn_wt`, `Mg_wt`, `Si_wt`, `Cu_wt`, `annealing_temp_K`, `time_to_peak_min`) PLUS the engineered interaction columns (`cold_work_Mn_content`, `cold_work_Mg_content`, `cold_work_Si_content`, `cold_work_Cu_content`). **Requirement**: MUST include `annealing_temp_K` as a standalone direct predictor feature. **Output Naming**: Rename interaction columns to snake_case. **Output**: `data/processed/engineered_features.csv`. **Dependency**: T021 (to ensure raw columns are present before engineering). **Verification**: Assert all raw columns exist in input before engineering.
- [ ] T025 [US1] **Generate final dataset artifact** `data/processed/final_dataset.csv` ready for modeling. **Logic**: Load `data/processed/engineered_features.csv` (from T024). Select and order columns: `cold_work_pct`, `Mn_wt`, `Mg_wt`, `Si_wt`, `Cu_wt`, `annealing_temp_K`, `time_to_peak_min`, `cold_work_Mn_content`, `cold_work_Mg_content`, `cold_work_Si_content`, `cold_work_Cu_content`. **Verification**: Verify the output file contains exactly these columns and no others. **Output**: `data/processed/final_dataset.csv`. **Dependency**: T024.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Predictive Model Training and Validation (Priority: P2)

**Goal**: Train a Random Forest Regressor using CPU-only execution, validate with 5-fold CV, and evaluate on a held-out test set.

**Independent Test**: The system can be tested by running the training script on `data/processed/final_dataset.csv`; it must output a trained model artifact and report mean CV R² score and held-out MAE, completing within 6 hours on 4GB RAM.

**⚠️ DEPENDENCY**: This phase MUST wait for T025 (final_dataset.csv) completion.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US2] Unit test for VIF calculation in `tests/unit/test_vif.py`.
- [X] T027 [P] [US2] Unit test for model training with small subset in `tests/unit/test_train.py`.

### Implementation for User Story 2

- [ ] T012 [US2] **Calculate synthetic baseline statistics**. **Logic**: Read `data/raw/synthetic_baseline.csv` (from T011, **raw and unclipped**). Calculate the mean of `time_to_peak_min` and store it as `baseline_mean` in `artifacts/reports/baseline_stats.json`. **Requirement**: This file is required for SC-006 (MAE threshold check) and must be derived from the *raw* data to ensure consistency with the synthetic baseline definition. **Output Schema**: Write a JSON object with key `baseline_mean` (float) to `artifacts/reports/baseline_stats.json`. **Verification**: Verify file exists and contains key `baseline_mean` as float. **Dependency**: T011. **Note**: This metric is for SC-006 threshold calculation only; model training uses clipped data.
- [X] T028 [US2] **Implement data splitting logic in `code/train.py`**: A stratified split (train/test) with random seed=42. Stratify on `time_to_peak_min` binned into multiple bins. **Requirement**: Save split indices to `data/split_indices.npy` for reproducibility and use by downstream tasks. **Dependency**: T025.
- [ ] T029 [US2] **Implement Random Forest Regressor training (CPU-only) in `code/train.py`**. **Model Type**: Train the **Interaction Model** (full feature set including interactions). **Size Constraint**: If the input dataset exceeds 10,000 rows, raise a `ValueError` immediately. **Pure Aluminum Handling**: Check if standard deviation of all composition columns (Mn, Mg, Si, Cu) is zero. If `std < 1e-9` for all composition columns, set `pure_aluminum_flag: true` in `artifacts/reports/training_metrics.json` and log a warning. **Output**: Save model to `artifacts/models/kinetic_model.pkl`. **Dependency**: T028, T012, T025. **Note**: Load `baseline_mean` from `artifacts/reports/baseline_stats.json` (T012) to calculate MAE threshold; use clipped data for training. If `baseline_stats.json` is missing, raise `FileNotFoundError`.
- [X] T030 [US2] **Save trained model to `artifacts/models/kinetic_model.pkl`**. **Format**: Use `pickle` protocol 4 for cross-version compatibility. **Dependency**: T029.
- [X] T031 [US2] **Implement k-fold cross-validation in `code/train.py`** and calculate mean R² and std dev. **Dependency**: T030.
- [X] T032 [US2] **Implement held-out test set evaluation in `code/train.py`**: Calculate MAE and R² on the test set. **Requirement**: Calculate the threshold as a fixed proportion of the `baseline_mean` read from `artifacts/reports/baseline_stats.json` (from T012). Compare the test MAE against this threshold. **Dependency**: T030, T012.
- [X] T033 [US2] **Generate `artifacts/reports/training_metrics.json`** containing CV scores and test set MAE/R². **Format**: JSON schema must include `cv_r2_mean`, `cv_r2_std`, `test_mae`, `test_r2`, and `pure_aluminum_flag`. **Dependency**: T031, T032.
- [X] T034 [US2] **Implement "Pure Aluminum" dataset detection in `code/train.py`**: Check if standard deviation of all composition columns (Mn, Mg, Si, Cu) is zero. If `std < 1e-9` for all composition columns, set `pure_aluminum_flag` to `true` in `artifacts/reports/training_metrics.json` and log a warning. **Requirement**: The `pure_aluminum_flag` must be a structured field in the JSON report. **Dependency**: T029.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Statistical Significance and Interaction Analysis (Priority: P3)

**Goal**: Statistically verify that interaction terms improve prediction accuracy and identify key drivers via SHAP.

**Independent Test**: The system can be tested by running the analysis script; it must output a p-value from a Permutation Test (p < 0.05) and a SHAP interaction value report.

**⚠️ DEPENDENCY**: This phase MUST wait for T030 (kinetic_model.pkl) completion.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T035 [P] [US3] Unit test for Permutation Test logic in `tests/unit/test_permutation.py`.
- [X] T036 [P] [US3] Unit test for SHAP interaction calculation in `tests/unit/test_shap.py`.

### Implementation for User Story 3

- [ ] T037 [US3] **Implement Baseline Model (Additive: cold work + composition, NO interactions) training in `code/evaluate.py`** for comparison. **Requirement**: Load the split indices from `data/split_indices.npy` (T028) to ensure identical validation folds. Train a Random Forest Regressor with identical hyperparameters to T029 (except no interaction features) to ensure a fair comparison. **Output**: `artifacts/models/additive_model.pkl`. **Verification**: Verify `artifacts/models/additive_model.pkl` exists and is loadable. **Dependency**: T028, T025.
- [ ] T038 [US3] **Ensure Interaction Model consistency in `code/evaluate.py`**. **Requirement**: Load the Interaction Model from `artifacts/models/kinetic_model.pkl` (T030) if it exists. **Artifact**: Ensure `artifacts/models/kinetic_model.pkl` is used for the Interaction Model. **Dependency**: T030.
- [X] T039 [US3] **Implement Delta-Permutation Test in `code/evaluate.py`**:
 1. Load the Additive Model (T037) and Interaction Model (T038).
 2. **Re-evaluate**: Re-evaluate BOTH models on the SAME data split (from T028) and SAME clipped dataset (from T022, `data/processed/validated_clipped.csv`) to generate error distributions (MAE per fold).
 3. **Permutation Logic**: For each permutation iteration (run `N_PERMUTATIONS` times, read from `code/config.py`), **shuffle the values of ALL interaction terms jointly** (e.g., `cold_work_Mn_content`, `cold_work_Mg_content`, etc.) in the validation set while holding main effects constant.
 4. Calculate the prediction error (MAE) for the Interaction Model on this shuffled data.
 5. **Comparison**: Calculate the **difference** between the Additive Model's error distribution and the Interaction Model's error distribution (both original and permuted).
 6. **Hypothesis Test**: Perform a statistical test (e.g., paired t-test or Mann-Whitney U) on the **difference** in errors (Additive Error - Interaction Error) to determine if the reduction in error provided by interactions is statistically significant (p < 0.05).
 7. **Output**: Write `p_value`, `method`, `interaction_term_importance`, and `additive_vs_interaction_diff` to **`artifacts/reports/permutation_intermediate.json`**. **Dependency**: T037, T038, T028, T022.
- [X] T040 [US3] **Implement Permutation Importance calculation in `code/evaluate.py`**: Calculate permutation importance (drop in R² score) for interaction terms and verify > 0.01 threshold (SC-003). Pass results to T042. **Dependency**: T039.
- [X] T041 [US3] **Implement SHAP Interaction Value analysis in `code/evaluate.py`** to rank features by unique contribution (FR-006). **Prerequisites**: `data/processed/engineered_features.csv` (from T024) and `artifacts/models/kinetic_model.pkl` (from T030). **Parameters**: Use `TreeExplainer` with `nsamples=1000` for determinism and `random_state=42`. **Conditional Logic**: **READ** `pure_aluminum_flag` from `artifacts/reports/training_metrics.json` (T033). If `pure_aluminum_flag` is true, **SKIP SHAP analysis** and generate an empty report with schema: `{"status": "N/A", "features": [], "interaction_terms": []}`. **Output Requirement**: The output report MUST explicitly separate 'interaction term contributions' from 'main effects'. **Output**: `artifacts/reports/shap_interaction_report.json`. **Dependency**: T024, T030, T033.
- [X] T042 [US3] **Generate `artifacts/reports/statistical_significance.json`**. **Schema**: Must contain `p_value` (float), `method` (string: "delta_permutation_test"), `interaction_term_importance` (float), `conclusion` (string). **Logic**: Read results from T039 and T040. **Dependency**: T039, T040.
- [X] T043 [US3] **Generate `artifacts/reports/shap_interaction_report.json`** with top features and interaction terms. Include `pure_aluminum_flag` status if detected in T034. **Dependency**: T041.
- [X] T044 [US3] **Verify Success Criteria**:
 1. Check p-value < 0.05 (from T042).
 2. Check Permutation Importance > 0.01 (from T040).
 3. Check R² > 0.6 (SC-001). **Logic**: Read `test_r2` from `artifacts/reports/training_metrics.json`. **Artifact**: Write results to `artifacts/reports/success_criteria_verification.json` with schema: `r2_pass` (bool), `p_value_pass` (bool), `mae_pass` (bool), `overall_status` (string: "PASS" or "FAIL"). **Dependency**: T033, T042.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T045 [P] **Documentation updates**: Update `README.md` installation steps. **Requirement**: Update `README.md` with a 5-step execution guide. **Steps to document**: 1. Install deps (`pip install -r requirements.txt`), 2. Generate data (`python code/generate_synthetic.py`), 3. Ingest & Engineer (`python code/ingest.py`), 4. Train (`python code/train.py`), 5. Evaluate (`python code/evaluate.py`).
- [X] T046 [P] **Documentation updates**: Update `quickstart.md` with a 5-step execution guide. **Requirement**: Update `quickstart.md` with a 5-step execution guide. **Steps to document**: 1. Install deps (`pip install -r requirements.txt`), 2. Generate data (`python code/generate_synthetic.py`), 3. Ingest & Engineer (`python code/ingest.py`), 4. Train (`python code/train.py`), 5. Evaluate (`python code/evaluate.py`).
- [X] T047 [P] **Refactor `code/utils.py`** for clarity and performance. **Metric**: Reduce cyclomatic complexity score of `utils.py` functions to < 5 using `radon cc code/utils.py -a`.
- [X] T048 [P] **Refactor `code/ingest.py`** to ensure strict error handling on data fetch. **Logic**: If external data fetch fails, proceed with the synthetic dataset already loaded; do not halt. (Note: Synthetic is primary per FR-001).
- [X] T049 [P] **Ensure model training parameters** are set to `n_estimators=config.N_ESTIMATORS` (read from `code/config.py`, default 100) and `max_depth=None` (default) in `code/train.py` to ensure runtime < 60 min on 10k rows. **Metric**: Verify training time < 60 min on CI runner.
- [X] T050 [P] **Implement chunked data loading** in `code/engineer.py` and `code/evaluate.py` if file size > 5MB. **Requirement**: Use `chunksize=1000` for `pandas.read_csv` to reduce memory peak usage.
- [X] T051 [P] **Write unit tests** for `code/utils.py` in `tests/unit/test_utils.py`.
- [X] T052 [P] **Write unit tests** for `code/engineer.py` in `tests/unit/test_engineer.py`.
- [ ] T053 [P] **Write unit tests** for `code/evaluate.py` in `tests/unit/test_evaluate.py`.
- [X] T054 [P] **Security hardening** (input sanitization). **Requirement**: Implement `pandas.read_csv` with explicit `dtype` enforcement and `na_filter=True` to sanitize inputs and prevent type confusion.
- [ ] T055 [P] **[Optional] Implement external data fetching logic** in `code/ingest_external.py` to attempt fetching from NIST/HuggingFace. **Logic**: **After** synthetic data is generated and loaded (T011/T022A), attempt to fetch external data. If fetch fails, log a warning and proceed with synthetic data only. **Constraint**: Do NOT append external data to synthetic data; if external data is used, it must **REPLACE** the synthetic data entirely. **Schema Validation**: Before replacing, **validate schema compatibility** (check for matching column names and types). If incompatible, log a warning and discard the external data. **Dependency**: T011. **Note**: This task is OPTIONAL and does not block T022A. T022A loads synthetic data directly.
- [ ] T056 [P] **Run `quickstart.md` validation** to ensure end-to-end execution of the full pipeline (US1 + US2 + US3). **Command**: `python code/main.py`. **Success Criteria**: Exit code 0, and files `data/raw/synthetic_baseline.csv`, `data/processed/final_dataset.csv`, `artifacts/models/kinetic_model.pkl`, `artifacts/reports/training_metrics.json`, `artifacts/reports/statistical_significance.json`, `artifacts/reports/shap_interaction_report.json` must exist. **Requirement**: No CLI arguments required. **Dependency**: T013.

---

## Phase 6: Revision & Analysis Resolution (Post-Analysis)

**Purpose**: Address specific reviewer concerns and ensure strict adherence to the "No Fabrication" and "Real Data" rules.

- [X] T057 [P] [Review] Ensure T034 correctly flags pure aluminum datasets in the report artifacts. **Requirement**: Verify `pure_aluminum_flag` is present in `training_metrics.json` and `shap_interaction_report.json` when applicable.
- [X] T058 [P] [Review] Verify T039 implements the specific Permutation Test (shuffling interaction terms) logic. **Requirement**: Confirm the test shuffles interaction terms while holding main effects constant, not a Mann-Whitney U test.
- [X] T059 [P] [Review] Verify T024 does not include `cold_work * Temperature` but DOES include `annealing_temp_K` as a standalone feature. **Requirement**: Confirm feature engineering strictly follows FR-002.
- [X] T061 [P] [Review] Verify T055 logic for data source failures. **Requirement**: Confirm that T055 correctly distinguishes between:
 1. **Local Synthetic Generator Failure** (T011): Must raise an error (Fail-Loud).
 2. **External Data Fetch Failure** (T055): Must proceed with synthetic data (Fail-Safe/Fallback).
 Ensure no task requires raising an error for external fetch failures, as this contradicts FR-001 and T055.
- [X] T062 [P] [Review] Verify T013 (main.py) implementation. **Requirement**: Confirm `code/main.py` exists and correctly orchestrates the pipeline (T011 -> T012 -> T021 -> T022 -> T024 -> T025 -> T029 -> T037 -> T039 -> T041 -> T042).
- [X] T063 [P] [Review] Verify T022 does not contain any `try/except` blocks that fallback to synthetic data if the primary load fails. **Requirement**: The load of `data/processed/clipped.csv` must be a direct read; if the file is missing, the script must crash with a clear `FileNotFoundError` to satisfy the "Fail-Loud" principle for the primary source.
- [X] T064 [P] [Review] Verify T021 outlier clipping is applied BEFORE T037/T039 statistical tests. **Requirement**: Confirm the data passed to the Permutation Test is the clipped version from `data/processed/validated_clipped.csv` (post-T022), not the raw version.
- [X] T065 [P] [Review] Verify T028 stratification logic handles the case where `time_to_peak_min` has low variance. **Requirement**: Ensure `train_test_split` does not crash if binning results in empty bins; implement a fallback to non-stratified split with a warning if stratification is impossible.
- [X] T067 [P] [Review] Verify T029 handles the "Pure Aluminum" edge case without crashing. **Requirement**: Confirm that if `std < 1e-9` for composition columns, the model training either skips interaction feature importance calculation or handles the zero-variance input gracefully (e.g., by excluding interaction features from the model input for that specific run) while still producing a valid `pure_aluminum_flag: true` in the report.
- [X] T068 [P] [Review] Verify T041 SHAP calculation parameters. **Requirement**: Confirm `TreeExplainer` is used with `nsamples=1000` and `random_state=42` to ensure deterministic and reproducible SHAP values, avoiding stochastic variance in the interaction analysis.
- [X] T069 [P] [Review] **Enforce "Fail-Loud" on Synthetic Generator Failure**. **Requirement**: Review `code/generate_synthetic.py` to ensure that ANY failure in generation (e.g., dependency missing, RNG error, file write error) raises a `RuntimeError` immediately. **Constraint**: This task explicitly forbids any `try/except` block that catches these errors and falls back to a mock dataset or `None`. The pipeline must halt if the primary synthetic source cannot be generated, ensuring the "No Fabrication" rule is upheld. **Dependency**: T011.
- [X] T070 [P] [Review] **Validate Data Flow for Outlier Clipping**. **Requirement**: Trace the data lineage in `code/main.py` and `code/ingest.py` to confirm that `data/processed/validated_clipped.csv` (output of T022) is the **only** file passed to `code/engineer.py` (T024) and subsequently to `code/train.py` (T028/T029) and `code/evaluate.py` (T037/T039). **Constraint**: Ensure no task accidentally re-loads `data/raw/synthetic_baseline.csv` for the training or statistical test phases, which would bypass the outlier clipping required by FR-007. **Dependency**: T021, T024, T029, T037.
- [X] T071 [P] [Review] **Verify Interaction Term Isolation in Permutation Test**. **Requirement**: Inspect `code/evaluate.py` (T039) to confirm that the permutation logic **ONLY** shuffles the columns `cold_work_Mn_content`, `cold_work_Mg_content`, `cold_work_Si_content`, and `cold_work_Cu_content`. **Constraint**: The test must explicitly verify that main effect columns (`cold_work_pct`, `Mn_wt`, etc.) and the target variable remain unshuffled during the interaction permutation step. **Dependency**: T039.
- [X] T072 [P] [Review] **Confirm Statistical Power for Small Datasets**. **Requirement**: Review `code/ingest.py` (T022) and `code/train.py` (T029) to ensure the `ValueError` for datasets < 50 rows is triggered **before** any model training or statistical testing begins. **Constraint**: Ensure the error message explicitly cites FR-008 and the requirement for 5-fold cross-validation statistical power. **Dependency**: T022.
- [X] T073 [P] [Review] **Audit External Data Fallback Logic**. **Requirement**: Review `code/ingest_external.py` (T055) to confirm that a failure to fetch external data results **only** in a log warning and the continuation of the pipeline using the synthetic data generated in T011. **Constraint**: Ensure no logic exists that attempts to generate synthetic data *inside* the external fetch failure block (redundant) or that halts the pipeline due to missing external data, as synthetic is the primary source. **Dependency**: T055.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup & Foundational (Phase 1)**: No dependencies - can start immediately
- **User Stories (Phase 2+)**: All depend on Phase 1 completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Revision (Phase 6)**: Depends on completion of Phase 5 and analysis feedback

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 1 - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Phase 1 - Depends on final_dataset.csv from US1
- **User Story 3 (P3)**: Can start after Phase 1 - Depends on trained model from US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- Once Phase 1 completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Write TDD unit test for physical bound validation in tests/unit/test_validation.py"
Task: "Write TDD unit test for interaction feature engineering in tests/unit/test_engineering.py"

# Launch all models for User Story 1 together:
Task: "Implement orchestration in code/ingest.py to load synthetic data"
Task: "Implement interaction feature engineering in code/engineer.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup & Foundational
2. Complete Phase 2: User Story 1
3. **STOP and VALIDATE**: Test User Story 1 independently
4. Deploy/demo if ready

### Incremental Delivery

1. Complete Phase 1 → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 1 together
2. Once Phase 1 is done:
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
- **Critical Constraint**: All tasks must run on free CPU-only CI (limited cores, constrained RAM, no GPU). No low-bit quantization, no CUDA, no large LLMs.
- **Data Integrity**: Use `code/generate_synthetic.py` for baseline data if real data is unavailable; **synthetic is the PRIMARY source**. If external fetch fails, proceed with synthetic (do not halt).
- **Data Flow**: Ensure data ingestion (US1) completes before model training (US2), and model training completes before validation (US3). **Crucially, outlier clipping (T021) must occur BEFORE validation (T022) and training (T029)**.
- **Statistical Rigor**: Permutation Test (shuffling interaction terms) and SHAP Interaction Values are mandatory for US3 to validate the "pinning effect" hypothesis. **T039 now implements a two-model comparison (Additive vs. Interaction)** with explicit re-evaluation on the same split.
- **Imputation Logic**: Missing composition values must be imputed using the mean of the column.
- **Interaction Terms**: Explicitly calculate `cold_work_Mn_content`, `cold_work_Mg_content`, `cold_work_Si_content`, `cold_work_Cu_content`. **Do NOT** calculate `cold_work * Temperature`. **MUST** include `annealing_temp_K` as a standalone feature.
- **Revision Focus**: Phase 6 tasks specifically address the "No Fabrication" rule by ensuring data loaders fail loudly on local generation errors but fall back to synthetic data on external fetch errors, maintaining the synthetic generator as the guaranteed primary source.