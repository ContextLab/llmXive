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

- [X] T001 [P] **Initialize project structure**. **Requirement**: Create all necessary directories and `.gitkeep` files for the project. **Directories**: `projects/PROJ-240-predicting-the-impact-of-cold-work-on-re/code`, `projects/PROJ-240-predicting-the-impact-of-cold-work-on-re/tests`, `projects/PROJ-240-predicting-the-impact-of-cold-work-on-re/data` (with subdirs `raw`, `processed`, `split`), `projects/PROJ-240-predicting-the-impact-of-cold-work-on-re/artifacts` (with subdirs `models`, `reports`, `figures`), AND `projects/PROJ-240-predicting-the-impact-of-cold-work-on-re/state/projects/` (create the full path and initialize `PROJ-240-predicting-the-impact-of-cold-work-on-re.yaml` with an empty `artifact_hashes` map and `updated_at` timestamp). **Config**: Create `code/config.py` with placeholders for `N_ROWS_TARGET` (default 10000), `N_PERMUTATIONS` (default 1000), `SEED` (default 42), `OUTLIER_PERCENTILE` (default 0.99), `N_ESTIMATORS` (default 100). **Verification**: Run `ls -R` and confirm all directories and files exist.
- [ ] T013 [P] **Create pipeline orchestrator**. **Script**: `code/main.py`. **Logic**: Implement a sequential runner that executes the FULL dependency chain: T011 -> T012 -> T017 -> T018 -> T019 -> T020 -> T021 -> T022 -> T023 -> T024 -> T025 -> T028 -> T029 -> T030 -> T031 -> T032 -> T033 -> T034 -> T037 -> T038 -> T039 -> T040 -> T041 -> T042 -> T043 -> T044 -> T045 -> T046 -> T047 -> T048 -> T049 -> T050 -> T051 -> T052 -> T053 -> T054 -> T055 -> T056 -> T057 -> T058 -> T059 -> T061 -> T062 -> T063 -> T069 -> T070 -> T072 -> T073 -> T074 -> T075 -> T078 -> T079 -> T081 -> T082 -> T083 -> T084 -> T085. **Requirement**: Must handle exit codes and print a summary of generated artifacts. **Dependency**: T001.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: User Story 1 - Data Ingestion and Feature Construction (Priority: P1) 🎯 MVP

**Goal**: Ingest raw experimental data (synthetic primary) and transform into a structured dataset with engineered interaction features.

**Independent Test**: The system can be tested by running the data pipeline on the synthetic generator (seed=42) and verifying the output DataFrame contains the required columns, calculated interaction features (`cold_work * Mn_content`, etc.), and no null values.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T015 [P] [US1] Write TDD unit test for physical bound validation in `tests/unit/test_validation.py`. **Function Name**: `test_physical_bounds_validation`. **Assertion**: Verify that values outside [0, 100] for cold work or negative time-to-peak raise `ValueError`.
- [ ] T016 [P] [US1] Write TDD unit test for interaction feature engineering in `tests/unit/test_engineering.py`. **Function Name**: `test_interaction_feature_engineering`. **Assertion**: Verify that `cold_work * Mn_content` is calculated correctly and present in the output DataFrame.

### Implementation for User Story 1

- [ ] T011 [US1] **Generate deterministic synthetic baseline data**. **Script**: `code/generate_synthetic.py`. **Logic**: Generate a deterministic synthetic dataset with **seed=42** (hard-coded). **CRITICAL**: The system MUST cap the generation at exactly **10000 rows** (as per `N_ROWS_TARGET` in config), regardless of any input size request, to satisfy FR-003 and Constitution Principle VII. This dataset is the **PRIMARY SOURCE** of truth for the project. **Schema**: Columns must include `cold_work_pct` (float, 0-100), `Mn_wt` (float), `Mg_wt` (float), `Si_wt` (float), `Cu_wt` (float), `annealing_temp_K` (float), `time_to_peak_min` (float). **Data Hygiene**: Compute SHA-256 checksum of `data/raw/synthetic_baseline.csv`, write the checksum to `data/raw/synthetic_baseline.csv.sha256`, and update `state/projects/PROJ-240-predicting-the-impact-of-cold-work-on-re.yaml` with the new checksum. **Verification**: Verify file exists, checksum matches, row count is exactly 10000, and state YAML is updated. **Error Handling**: If generation fails, raise `RuntimeError` immediately; do NOT fall back to mock data. **Dependency**: T001.
- [ ] T017 [US1] **Implement row filtering for missing "time-to-peak softening"** in `code/ingest.py` (exclude rows, do not impute target).
- [ ] T018 [US1] **Implement physical bound validation** (0 ≤ cold work ≤ 100%, positive time) in `code/ingest.py`.
- [ ] T019 [US1] **Implement missing composition value handling** in `code/ingest.py`. **Logic**: Load `data/raw/synthetic_baseline.csv` (from T011). Impute missing values in `Mn_wt`, `Mg_wt`, `Si_wt`, `Cu_wt` using the **mean of the specific column**. Do NOT use a global mean for all rows. **Output**: Save cleaned data to `data/processed/cleaned.csv`. **Verification**: Verify no null values remain in composition columns. **Dependency**: T018.
- [ ] T020 [US1] **Implement unit normalization for time-to-peak (minutes)** in `code/ingest.py`.
- [ ] T021 [US1] **Implement outlier clipping on target variable** at the 99th percentile (read `OUTLIER_PERCENTILE` from `code/config.py`, default 0.99) to mitigate extreme value influence, as required by FR-007, in `code/ingest.py`. **Input**: Load `data/processed/cleaned.csv` (from T019). **Method**: Use `np.percentile` with `method='linear'`. **Artifact**: Write `clipped_outliers_count` (int) and `clipped_values_list` (list of integer row indices) to `artifacts/reports/validation_log.json`. **Output**: Save clipped dataset to **`data/processed/clipped.csv`**. **CRITICAL**: This `clipped.csv` is the **ONLY** valid input for downstream statistical tasks (T039, T042). **Data Hygiene**: Compute SHA-256 checksum of `data/processed/clipped.csv`, write the checksum to `data/processed/clipped.csv.sha256`, and update `state/projects/PROJ-240-predicting-the-impact-of-cold-work-on-re.yaml`. **Verification**: Assert that downstream tasks (T039, T042) reference `data/processed/clipped.csv`. **Dependency**: T020.
- [ ] T022 [US1] **Implement validation and size check in `code/ingest.py`**. **Logic**: Load `data/processed/clipped.csv` (from T021). **Fail-Fast**: Immediately check if dataset size < 50 rows (FR-008). If so, raise `ValueError` immediately before any further processing. **Transformation**: Verify all required columns exist. Save the validated data to **NEW artifact `data/processed/validated_clipped.csv`**. **Output**: `data/processed/validated_clipped.csv`. **Requirement**: Explicitly update downstream tasks (T024, T037, T039) to use this path. **Dependency**: T021.
- [ ] T023 [US1] **Generate `artifacts/reports/ingestion_metrics.json` and update `artifacts/reports/validation_log.json`**. **Logic**: T023 is the **sole producer** of the final aggregated ingestion metrics. It MUST read outputs from T021 (`validation_log.json`) and T022 (row counts) and merge them into a single `ingestion_metrics.json` file. **Schema**: `ingestion_metrics.json` must contain `rows_ingested` (int), `rows_dropped_nulls` (int), `rows_dropped_other` (int, for bounds/target missing), `rows_output` (int), `clipped_outliers_count`, `clipped_values_list`, `threshold_99th_percentile`. **Requirement**: These metrics are required for SC-007. **Dependency**: Must run AFTER T022.
- [ ] T024 [US1] **Implement interaction feature engineering in `code/engineer.py`**. **Input**: Load `data/processed/validated_clipped.csv` (from T022). **Logic**: Calculate `cold_work_Mn_content` (cold_work_pct * Mn_wt), `cold_work_Mg_content`, `cold_work_Si_content`, `cold_work_Cu_content`. **Constraint**: Do NOT include `cold_work * Temperature`. **Output Schema**: The output MUST contain ALL original raw columns (`cold_work_pct`, `Mn_wt`, `Mg_wt`, `Si_wt`, `Cu_wt`, `annealing_temp_K`, `time_to_peak_min`) PLUS the engineered interaction columns (`cold_work_Mn_content`, `cold_work_Mg_content`, `cold_work_Si_content`, `cold_work_Cu_content`). **Requirement**: MUST include `annealing_temp_K` as a standalone feature. **Output Naming**: Columns are already named in snake_case. **Output**: `data/processed/engineered_features.csv`. **Dependency**: T022.
- [ ] T025 [US1] **Generate final dataset artifact** `data/processed/final_dataset.csv` ready for modeling. **Logic**: Load `data/processed/engineered_features.csv` (from T024). Select and order columns: `cold_work_pct`, `Mn_wt`, `Mg_wt`, `Si_wt`, `Cu_wt`, `annealing_temp_K`, `time_to_peak_min`, `cold_work_Mn_content`, `cold_work_Mg_content`, `cold_work_Si_content`, `cold_work_Cu_content`. **Verification**: Verify the output file contains exactly these columns and no others. **Output**: `data/processed/final_dataset.csv`. **Dependency**: T024.
- [ ] T052 [US1] **Write unit tests for `code/engineer.py` in `tests/unit/test_engineer.py`**. **Function Name**: `test_engineer_functionality`. **Assertion**: Verify engineering functions work as expected. **Requirement**: This task is MANDATORY to satisfy the US1 Independent Test requirement. **Dependency**: T024.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Predictive Model Training and Validation (Priority: P2)

**Goal**: Train a Random Forest Regressor using CPU-only execution, validate with 5-fold CV, and evaluate on a held-out test set.

**Independent Test**: The system can be tested by running the training script on `data/processed/final_dataset.csv`; it must output a trained model artifact and report mean CV R² score and held-out MAE, completing within 6 hours on 4GB RAM.

**⚠️ DEPENDENCY**: This phase MUST wait for T025 (final_dataset.csv) completion.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US2] Unit test for VIF calculation in `tests/unit/test_vif.py`. **Function Name**: `test_vif_calculation`. **Assertion**: Verify VIF values are calculated correctly for a sample dataset.
- [X] T027 [P] [US2] Unit test for model training with small subset in `tests/unit/test_train.py`. **Function Name**: `test_model_training_small_subset`. **Assertion**: Verify model trains successfully on a small subset (10 rows) without error.

### Implementation for User Story 2

- [X] T012 [US2] **Calculate synthetic baseline statistics**. **Logic**: Read `data/raw/synthetic_baseline.csv` (from T011, **raw and unclipped**). Calculate the mean of `time_to_peak_min` and store it as `baseline_mean` in `artifacts/reports/baseline_stats.json`. **Requirement**: This file is required for SC-006 (MAE threshold check) and must be derived from the *raw* data to ensure consistency with the synthetic baseline definition. **Output Schema**: Write a JSON object with key `baseline_mean` (float) to `artifacts/reports/baseline_stats.json`. **Verification**: Verify file exists and contains key `baseline_mean` as float. **Dependency**: T011.
- [X] T028 [US2] **Implement data splitting logic in `code/train.py`**: A stratified split (train/test) with random seed=42. Stratify on `time_to_peak_min` binned into multiple bins. **Requirement**: Save split indices to `data/split_indices.npy` for reproducibility and use by downstream tasks. **Dependency**: T025.
- [X] T029 [US2] **Implement Random Forest Regressor training (CPU-only) in `code/train.py`**. **Input**: Load `data/processed/final_dataset.csv` (from T025). **Model Type**: Train the Interaction Model (full feature set including interactions). **Size Constraint**: If the input dataset exceeds 10,000 rows, raise a `ValueError` immediately. **Pure Aluminum Handling**: Check if standard deviation of all composition columns (Mn, Mg, Si, Cu) is zero. If `std < 1e-9` for all composition columns, set `pure_aluminum_flag: true` in `artifacts/reports/training_metrics.json` and log a warning. **Output**: Save model to `artifacts/models/kinetic_model.pkl`. **Verification**: Verify training time < 60 min and memory usage < 4GB. **Dependency**: T028, T012, T025.
- [X] T030 [US2] **Save trained model to `artifacts/models/kinetic_model.pkl`**. **Format**: Use `pickle` protocol 4 for cross-version compatibility. **Dependency**: T029.
- [X] T031 [US2] **Implement k-fold cross-validation in `code/train.py`** and calculate mean R² and std dev. **Dependency**: T030.
- [X] T032 [US2] **Implement held-out test set evaluation in `code/train.py`**: Calculate MAE and R² on the test set. **Requirement**: Calculate the threshold as a fixed proportion of the `baseline_mean` read from `artifacts/reports/baseline_stats.json` (from T012). Compare the test MAE against this threshold. **Dependency**: T030, T012.
- [X] T033 [US2] **Generate `artifacts/reports/training_metrics.json`** containing CV scores and test set MAE/R². **Format**: JSON schema must include `cv_r2_mean`, `cv_r2_std`, `test_mae`, `test_r2`, and `pure_aluminum_flag`. **Dependency**: T031, T032.
- [X] T034 [US2] **Implement "Pure Aluminum" dataset detection in `code/train.py`**. **Requirement**: Check if standard deviation of all composition columns (Mn, Mg, Si, Cu) is zero. If `std < 1e-9` for all composition columns, set `pure_aluminum_flag` to `true` in `artifacts/reports/training_metrics.json` and log a warning. **Dependency**: T029.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Statistical Significance and Interaction Analysis (Priority: P3)

**Goal**: Statistically verify that interaction terms improve prediction accuracy and identify key drivers via SHAP.

**Independent Test**: The system can be tested by running the analysis script; it must output a p-value from a Permutation Test (p < 0.05) and a SHAP interaction value report.

**⚠️ DEPENDENCY**: This phase MUST wait for T030 (kinetic_model.pkl) completion.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T035 [P] [US3] Unit test for Permutation Test logic in `tests/unit/test_permutation.py`. **Function Name**: `test_permutation_test_logic`. **Assertion**: Verify that shuffling interaction terms increases error significantly.
- [X] T036 [P] [US3] Unit test for SHAP interaction calculation in `tests/unit/test_shap.py`. **Function Name**: `test_shap_interaction_calculation`. **Assertion**: Verify SHAP values are calculated correctly for a sample model.

### Implementation for User Story 3

- [ ] T037 [US3] **Implement Baseline Model (Additive: cold work + composition, NO interactions) training in `code/evaluate.py`** for comparison. **Input**: Load `data/processed/final_dataset.csv` (from T025). **Logic**: Drop interaction columns (`cold_work_Mn_content`, `cold_work_Mg_content`, `cold_work_Si_content`, `cold_work_Cu_content`) before training. **Requirement**: Load the split indices from `data/split_indices.npy` (T028) to ensure identical validation folds. Train a Random Forest Regressor with identical hyperparameters to T029 (except no interaction features) to ensure a fair comparison. **Output**: `artifacts/models/additive_model.pkl`. **Verification**: Verify `artifacts/models/additive_model.pkl` exists and is loadable. **Dependency**: T028, T025.
- [ ] T038 [US3] **Ensure Interaction Model consistency in `code/evaluate.py`**. **Requirement**: Load the Interaction Model from `artifacts/models/kinetic_model.pkl` (T030) if it exists. **Artifact**: Ensure `artifacts/models/kinetic_model.pkl` is used for the Interaction Model. **Dependency**: T030.
- [ ] T039 [US3] **Implement Delta-Permutation Test in `code/evaluate.py`**:
 1. Load the Additive Model (T037) and Interaction Model (T038).
 2. **Re-evaluate**: Re-evaluate BOTH models on the SAME data split (from T028) and SAME clipped dataset (from T022) to generate error distributions (MAE per fold).
 3. **Permutation Logic**: For each permutation iteration (run **N_PERMUTATIONS** times, read from `code/config.py`, default 1000), **shuffle the values of ALL interaction terms jointly** (specifically: `cold_work_Mn_content`, `cold_work_Mg_content`, `cold_work_Si_content`, `cold_work_Cu_content`) in the validation set while holding main effects constant. This joint shuffling is required to isolate the incremental gain of the interaction block.
 4. Calculate the prediction error (MAE) for the Interaction Model on this shuffled data.
 5. **Comparison**: Calculate the **difference** between the Additive Model's error distribution and the Interaction Model's error distribution (both original and permuted).
 6. **Hypothesis Test**: Perform a statistical test (e.g., paired t-test or Mann-Whitney U) on the **difference** in errors (Additive Error - Interaction Error) to determine if the reduction in error provided by interactions is statistically significant (p < 0.05). **Requirement**: If p >= 0.05, raise a warning or error indicating the hypothesis was not supported. **CRITICAL**: The pipeline MUST fail if p >= 0.05 to enforce FR-005.
 7. **Output**: Write `p_value`, `method`, `interaction_term_importance`, and `additive_vs_interaction_diff` to **`artifacts/reports/permutation_intermediate.json`**. **Dependency**: T037, T038, T028, T022.
- [ ] T040 [US3] **Implement Permutation Importance calculation in `code/evaluate.py`**: Calculate permutation importance (drop in R² score) for interaction terms and verify > 0.01 threshold (SC-003). Pass results to T042. **Dependency**: T039.
- [ ] T041 [US3] **Implement SHAP Interaction Value analysis in `code/evaluate.py`** to rank features by unique contribution (FR-006). **Prerequisites**: `data/processed/engineered_features.csv` (from T024) and `artifacts/models/kinetic_model.pkl` (from T030). **Parameters**: Use `TreeExplainer` with `nsamples=1000` for determinism and `random_state=42`. **Conditional Logic**: **READ** `pure_aluminum_flag` from `artifacts/reports/training_metrics.json` (T033). If `pure_aluminum_flag` is true, **DO NOT SKIP**; instead, generate an empty report with schema: `{"status": "N/A", "features": [], "interaction_terms": []}` and write it to the output path. **Output Requirement**: The output report MUST explicitly separate 'interaction term contributions' from 'main effects'. **Output**: `artifacts/reports/shap_interaction_report.json`. **Dependency**: T024, T030, T033.
- [X] T042 [US3] **Generate `artifacts/reports/statistical_significance.json`**. **Schema**: Must contain `p_value` (float), `method` (string: "delta_permutation_test"), `interaction_term_importance` (float), `conclusion` (string). **Logic**: Read results from T039 and T040. **Requirement**: The `conclusion` field MUST explicitly state that the results are associative and do not imply causation, as per the "Assumptions" section of the spec. **Dependency**: T039, T040.
- [X] T043 [US3] **Generate `artifacts/reports/shap_interaction_report.json`** with top features and interaction terms. Include `pure_aluminum_flag` status if detected in T034. **Dependency**: T041.
- [X] T044 [US3] **Verify Success Criteria**:
 1. Check p-value < 0.05 (from T042).
 2. Check Permutation Importance > 0.01 (from T040).
 3. Check R² > 0.6 (SC-001). **Logic**: Read `test_r2` from `artifacts/reports/training_metrics.json`. **Artifact**: Write results to `artifacts/reports/success_criteria_verification.json` with schema: `r2_pass` (bool), `p_value_pass` (bool), `mae_pass` (bool), `overall_status` (string: "PASS" or "FAIL"). **Dependency**: T033, T042.

**Checkpoint**: At this point, User Stories 1, 2, and 3 are all independently functional

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T045 [P] **Documentation updates**: Update `README.md` installation steps. **Requirement**: Update `README.md` with a 5-step execution guide. **Steps to document**: 1. Install deps (`pip install -r requirements.txt`), 2. Generate data (`python code/generate_synthetic.py`), 3. Ingest & Engineer (`python code/ingest.py`), 4. Train (`python code/train.py`), 5. Evaluate (`python code/evaluate.py`).
- [ ] T046 [P] **Documentation updates**: Update `quickstart.md` with a 5-step execution guide. **Requirement**: Update `quickstart.md` with a 5-step execution guide. **Steps to document**: 1. Install deps (`pip install -r requirements.txt`), 2. Generate data (`python code/generate_synthetic.py`), 3. Ingest & Engineer (`python code/ingest.py`), 4. Train (`python code/train.py`), 5. Evaluate (`python code/evaluate.py`).
- [X] T047 [P] **Refactor `code/utils.py`** for clarity and performance. **Metric**: Reduce cyclomatic complexity score of `utils.py` functions to < 5 using `radon cc code/utils.py -a`.
- [ ] T048 [P] **Refactor `code/ingest.py`** to ensure strict error handling on data fetch. **Logic**: If external data fetch fails, proceed with the synthetic dataset already loaded; do NOT halt.
- [X] T049 [P] **Ensure model training parameters** are set to `n_estimators=config.N_ESTIMATORS` (read from `code/config.py`, default 100) and `max_depth=None` (default) in `code/train.py` to ensure runtime < 60 min on 10k rows. **Metric**: Verify training time < 60 min on CI runner.
- [ ] T050 [P] **Implement chunked data loading** in `code/engineer.py` and `code/evaluate.py` if file size > 5MB. **Requirement**: Use `chunksize=1000` for `pandas.read_csv` to reduce memory peak usage.
- [X] T051 [P] **Write unit tests** for `code/utils.py` in `tests/unit/test_utils.py`. **Function Name**: `test_utils_functionality`. **Assertion**: Verify utility functions work as expected.
- [ ] T053 [P] **Write unit tests** for `code/evaluate.py` in `tests/unit/test_evaluate.py`. **Function Name**: `test_evaluate_functionality`. **Assertion**: Verify evaluation functions work as expected.
- [X] T054 [P] **Security hardening** (input sanitization). **Requirement**: Implement `pandas.read_csv` with explicit `dtype` enforcement and `na_filter=True` to sanitize inputs and prevent type confusion.
- [ ] T055 [P] **Implement external data fetching logic** in `code/ingest_external.py` to attempt fetching from NIST/HuggingFace. **Logic**: **After** synthetic data is generated and loaded (T011/T022), attempt to fetch external data. **Constraint**: Synthetic data is the PRIMARY source. External data is ONLY ingested if it passes schema validation (matching column names and types) AND is merged (appended) to the synthetic dataset, NOT replacing it. **CRITICAL**: If external data fetch fails (e.g., network error, missing repo), the script MUST log a warning and **continue** using only the synthetic data. It MUST NOT raise an exception or halt the pipeline. **Dependency**: T011.
- [ ] T056 [P] **Run `quickstart.md` validation** to ensure end-to-end execution of the full pipeline (US1 + US2 + US3). **Command**: `python code/main.py`. **Success Criteria**: Exit code 0, and files `data/raw/synthetic_baseline.csv`, `data/processed/final_dataset.csv`, `artifacts/models/kinetic_model.pkl`, `artifacts/reports/training_metrics.json`, `artifacts/reports/statistical_significance.json`, `artifacts/reports/shap_interaction_report.json` must exist. **Requirement**: No CLI arguments required. **Dependency**: T013.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Revision & Analysis Resolution (Post-Analysis)

**Purpose**: Address specific reviewer concerns and ensure strict adherence to the "No Fabrication" and "Real Data" rules.

- [X] T057 [P] [Review] Ensure T034 correctly flags pure aluminum datasets in the report artifacts. **Requirement**: Verify `pure_aluminum_flag` is present in `training_metrics.json` and `shap_interaction_report.json` when applicable.
- [X] T058 [P] [Review] Verify T039 implements the specific Permutation Test (shuffling interaction terms) logic. **Requirement**: Confirm the test shuffles interaction terms while holding main effects constant, not a Mann-Whitney U test.
- [ ] T059 [P] [Review] Verify T024 does not include `cold_work * Temperature` interaction, but DOES include `annealing_temp_K` as a standalone feature. **Requirement**: Confirm feature engineering strictly follows FR-002.
- [X] T061 [P] [Review] Verify T055 logic for data source failures. **Requirement**: Confirm that T055 correctly handles external data fetch failures and merges/ignores external data without replacing synthetic.
- [X] T062 [P] [Review] Verify T013 pipeline orchestrator. **Requirement**: Confirm the pipeline executes in the correct order.
- [X] T063 [P] [Review] Verify T021 outlier handling. **Requirement**: Confirm outlier clipping is applied before downstream tasks.
- [ ] T069 [P] **Implement fail-loud logic in `code/generate_synthetic.py`**. **Requirement**: Review `code/generate_synthetic.py` to ensure that ANY failure in generation (e.g., dependency missing, RNG error, file write error) raises a `RuntimeError` immediately.
- [ ] T070 [P] **Update `code/main.py` to enforce data flow**. **Requirement**: Trace the data lineage in `code/main.py` and `code/ingest.py` to confirm that `data/processed/validated_clipped.csv` is the only file passed to `code/engineer.py` and subsequently to `code/train.py` and `code/evaluate.py`.
- [ ] T072 [P] **Implement fail-fast check in `code/ingest.py`**. **Requirement**: Review `code/ingest.py` to ensure the `ValueError` for datasets < 50 rows is triggered before any model training or statistical testing begins.
- [ ] T073 [P] **Implement fallback logic in `code/ingest_external.py`**. **Requirement**: Review `code/ingest_external.py` to confirm that a failure to fetch external data results in a log warning and the continuation of the pipeline using the synthetic data.
- [X] T074 [P] **Verify data flow for T023 metrics**. **Requirement**: Ensure T023 correctly aggregates metrics from T021 and T022.
- [X] T075 [P] **Verify T029 Pure Aluminum handling for SHAP**. **Requirement**: Ensure T029 correctly sets `pure_aluminum_flag` so that T041 can handle the flag gracefully.
- [X] T076 [P] **Verify T039 Delta-Permutation Test logic**. **Requirement**: Confirm the permutation test shuffles interaction terms correctly.
- [ ] T078 [P] [Review] **Add explicit data source verification in `code/ingest.py`**. **Requirement**: Insert a check at the start of `code/ingest.py` that verifies the existence and integrity (checksum) of `data/raw/synthetic_baseline.csv` (from T011) before proceeding. If the file is missing or checksums mismatch, raise `FileNotFoundError` immediately. **Dependency**: T011, T019.
- [ ] T079 [P] [Review] **Update `code/config.py` to enforce dataset size limits**. **Requirement**: Add a hard-coded `MAX_ROWS_ALLOWED = 10000` constant and ensure `code/generate_synthetic.py` and `code/train.py` strictly enforce this limit, raising `ValueError` if exceeded, to guarantee compliance with FR-003 and CI constraints. **Dependency**: T011, T029.
- [X] T081 [P] [Review] **Verify SHAP interaction report separates main effects and interactions**. **Requirement**: Inspect the output schema of `artifacts/reports/shap_interaction_report.json` to ensure it has distinct keys for `main_effects` and `interaction_terms`, preventing conflation of the two, as required by FR-006. **Dependency**: T041.
- [ ] T082 [P] [Review] **Ensure `code/evaluate.py` uses the exact same split indices for both models**. **Requirement**: Add a validation step in `code/evaluate.py` that asserts the training and validation indices used for the Additive Model (T037) and Interaction Model (T038) are identical to those saved in `data/split_indices.npy` (T028). **Dependency**: T037, T038, T028.
- [ ] T083 [P] [Review] **Add unit test for outlier clipping logic in `tests/unit/test_ingest.py`**. **Requirement**: Write a test that generates a dataset with known outliers (>99th percentile) and verifies that `code/ingest.py` correctly clips them and logs the count in `validation_log.json`. **Dependency**: T021.
- [ ] T084 [P] [Review] **Verify `code/engineer.py` does not normalize the target variable**. **Requirement**: Add a check in `code/engineer.py` to ensure `time_to_peak_min` is passed through unchanged (no Arrhenius normalization or log transforms), adhering to FR-002. **Dependency**: T024.
- [ ] T085 [P] [Review] **Implement a "Data Lineage" check in `code/main.py`**. **Requirement**: Add a final validation step in the orchestrator that traces the file modification timestamps and checksums of all input artifacts to ensure no task used a stale or incorrect intermediate file (e.g., using `cleaned.csv` instead of `validated_clipped.csv`). **Dependency**: T013, T070. **Note**: This task runs strictly after T013 completes.
