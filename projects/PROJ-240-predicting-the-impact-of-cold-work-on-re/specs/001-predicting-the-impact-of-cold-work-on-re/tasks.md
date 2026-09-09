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

- [ ] T001 [P] Create directory `projects/PROJ-240-predicting-the-impact-of-cold-work-on-re/code`. **Requirement**: Ensure the directory exists. **Verification**: Run `ls -d projects/PROJ-240-predicting-the-impact-of-cold-work-on-re/code`.
- [ ] T002 [P] Create `.gitkeep` file in `projects/PROJ-240-predicting-the-impact-of-cold-work-on-re/code`. **Verification**: Run `ls projects/PROJ-240-predicting-the-impact-of-cold-work-on-re/code`.
- [ ] T003 [P] Create directory `projects/PROJ-240-predicting-the-impact-of-cold-work-on-re/tests`. **Requirement**: Ensure the directory exists. **Verification**: Run `ls -d projects/PROJ-240-predicting-the-impact-of-cold-work-on-re/tests`.
- [ ] T004 [P] Create `.gitkeep` file in `projects/PROJ-240-predicting-the-impact-of-cold-work-on-re/tests`. **Verification**: Run `ls projects/PROJ-240-predicting-the-impact-of-cold-work-on-re/tests`.
- [ ] T005 [P] Create directory `projects/PROJ-240-predicting-the-impact-of-cold-work-on-re/data`. **Requirement**: Ensure the directory exists. **Verification**: Run `ls -d projects/PROJ-240-predicting-the-impact-of-cold-work-on-re/data`.
- [ ] T006 [P] Create `.gitkeep` file in `projects/PROJ-240-predicting-the-impact-of-cold-work-on-re/data`. **Verification**: Run `ls projects/PROJ-240-predicting-the-impact-of-cold-work-on-re/data`.
- [ ] T007 [P] Create directory `projects/PROJ-240-predicting-the-impact-of-cold-work-on-re/artifacts`. **Requirement**: Ensure the directory exists. **Verification**: Run `ls -d projects/PROJ-240-predicting-the-impact-of-cold-work-on-re/artifacts`.
- [ ] T008 [P] Create `.gitkeep` file in `projects/PROJ-240-predicting-the-impact-of-cold-work-on-re/artifacts`. **Verification**: Run `ls projects/PROJ-240-predicting-the-impact-of-cold-work-on-re/artifacts`.
- [ ] T009 [P] Create data subdirectories: `data/raw`, `data/processed`, `data/split`. **Requirement**: Create `.gitkeep` files. **Verification**: Run `ls -R data` and confirm subdirectories exist.
- [ ] T010 [P] Create artifacts subdirectories: `artifacts/models`, `artifacts/reports`, `artifacts/figures`. **Requirement**: Create `.gitkeep` files. **Verification**: Run `ls -R artifacts` and confirm subdirectories exist.
- [ ] T011 [P] Generate deterministic synthetic baseline data using `code/generate_synthetic.py` with seed=42 and output `data/raw/synthetic_baseline.csv`. **Schema**: Columns must include `cold_work_pct` (float, 0-100), `Mn_wt` (float), `Mg_wt` (float), `Si_wt` (float), `Cu_wt` (float), `annealing_temp_K` (float), `time_to_peak_min` (float). **Logic**: Use a deterministic physical kinetics model + noise. **Reproducibility**: MUST hard-code `seed=42` inside the `generate_synthetic.py` script logic (not just as a CLI argument) to satisfy Constitution Principle I. **Data Hygiene**: MUST compute the SHA-256 checksum of the generated CSV using the `sha256sum` command (e.g., `sha256sum data/raw/synthetic_baseline.csv > data/raw/synthetic_baseline.csv.sha256`) and write it to `data/raw/synthetic_baseline.csv.sha256` in the format `hash filename` (two spaces, `filename` is the basename only). **Versioning**: MUST record this checksum in the project's state YAML (`state/projects/PROJ-240-predicting-the-impact-of-cold-work-on-re.yaml`) under `artifact_hashes`. **Error Handling**: If generation fails, raise `RuntimeError` immediately; do NOT fall back to mock data. **Dataset Cap**: Generate exactly 1000 rows, but enforce a hard cap of [deferred] rows using `n_rows = min(requested, 10000)` to satisfy FR-003 and Constitution Principle VII.
- [ ] T012 [P] Calculate synthetic baseline statistics and write `artifacts/reports/baseline_stats.json`. **Logic**: Read `data/raw/synthetic_baseline.csv` (generated by T011), calculate the mean of `time_to_peak_min` (in minutes) from the synthetic generator output, and store it as `baseline_mean`. **Requirement**: This file is required for SC-006 (MAE threshold check). **Dependency**: Must run AFTER T011. **Verification**: Ensure T011 has completed and the file exists before reading.
- [ ] T013 [P] Implement orchestration in `code/main.py`. **Logic**: This script must be the single entry point that calls the ingestion, feature engineering, training, and evaluation scripts in sequence. **Requirement**: Must handle errors and exit with non-zero code on failure. **Scope**: This is a skeleton orchestrator; full functionality depends on downstream tasks (T022, T024, etc.) being implemented.
- [ ] T014 [P] Implement dataset size validation in `code/ingest.py`: Raise `ValueError` immediately if the dataset size is < 50 rows (FR-008) to ensure 'fail-fast' behavior. **Requirement**: This check must occur BEFORE any feature engineering or model training.

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

- [ ] T017 [US1] Implement row filtering for missing "time-to-peak softening" in `code/ingest.py` (exclude rows, do not impute target).
- [ ] T018 [US1] Implement physical bound validation (0 ≤ cold work ≤ 100%, positive time) in `code/ingest.py`.
- [ ] T019 [US1] Implement missing composition value handling in `code/ingest.py`: Impute using the mean of the specific alloy series (group by alloy type or concentration range) or flag for exclusion as per spec Edge Cases. Do NOT use a global mean for all rows.
- [ ] T020 [US1] Implement unit normalization for time-to-peak (minutes) in `code/ingest.py`.
- [ ] T021 [US1] Implement outlier clipping on target variable at the 99th percentile to mitigate extreme value influence, as required by FR-007, in `code/ingest.py` (FR-007) before any statistical analysis. Log clipped values to `artifacts/reports/validation_log.json`. **Requirement**: The clipped data must be the ONLY data used for subsequent statistical tests. **Method**: Use `np.percentile` with `interpolation='linear'` (or `method='linear'` in newer numpy) to calculate the 99th percentile threshold. **Artifact**: Write `clipped_outliers_count` (int) and `clipped_values_list` (list of integer row indices) to `validation_log.json`. **Dependency**: T018.
- [ ] T022 [US1] Implement orchestration in `code/ingest.py`: Load `data/raw/synthetic_baseline.csv` (from T011) as the PRIMARY and mandatory source. **Logic**: Load the synthetic data. If T055 (external fetch) has successfully generated a merged dataset (containing synthetic + external), load that dataset directly. Otherwise, load the synthetic baseline. Output `data/processed/validated.csv` and `artifacts/reports/validation_log.json`. **Requirement**: Ensure the dataset size is >= 50 rows (T014) and <= 10000 rows (T011 cap). **Fail-Fast**: If the dataset size is < 50 rows after loading, raise `ValueError` immediately (FR-008) before any further processing. **Dependency**: T011.
- [ ] T023 [US1] Generate `artifacts/reports/ingestion_metrics.json` and update `artifacts/reports/validation_log.json`. **Schema**: `ingestion_metrics.json` must contain `rows_ingested` (int), `rows_filtered` (int), `null_handling_success_rate` (float, calculated as `rows_output / rows_input`), `rows_output` (int). `validation_log.json` must contain `rows_ingested`, `rows_filtered`, `null_counts`, `clipped_outliers_count`, `clipped_values_list` (list of integer row indices), `threshold_99th_percentile` (float). **Requirement**: These metrics are required for SC-007. **Dependency**: Must run AFTER T022 (ingestion logic). **Logic**: Read `validation_log.json` from T022 and append metrics, do not overwrite.
- [ ] T024 [US1] Implement interaction feature engineering in `code/engineer.py`: Calculate `cold_work * Mn_content`, `cold_work * Mg_content`, `cold_work * Si_content`, `cold_work * Cu_content`. **Constraint**: Do NOT include `cold_work * Temperature`. Use exact column names from T011 (e.g., `cold_work_pct`, `Mn_wt`, `annealing_temp_K`). **Output Naming**: Rename interaction columns to snake_case (e.g., `cold_work_Mn_content`, `cold_work_Mg_content`). **Requirement**: MUST include `annealing_temp_K` as a standalone direct predictor feature in the output `engineered_features.csv`. Include annealing temperature as a direct feature. **Data Cap**: Assume dataset is already capped at 10000 rows by T011/T022. Output `data/processed/engineered_features.csv`. **Dependency**: T021.
- [ ] T025 [US1] Generate final dataset artifact `data/processed/final_dataset.csv` ready for modeling. **Dependency**: T024.

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

- [ ] T028 [US2] Implement data splitting logic in `code/train.py`: A stratified split (train/test) with random seed=42. Stratify on `time_to_peak_min` binned into multiple bins. **Requirement**: Save split indices or ensure reproducibility for use in Phase 4. **Dependency**: T025.
- [ ] T029 [US2] Implement Random Forest Regressor training (CPU-only) in `code/train.py`. **Model Type**: Train the **Interaction Model** (full feature set including interactions) to serve as the primary predictive model. Ensure dataset size ≤ 10000 rows (FR-003). **Pure Aluminum Handling**: Check if standard deviation of all composition columns (Mn, Mg, Si, Cu) is zero. If `std < 1e-9` for all composition columns, set `pure_aluminum_flag: true` in `artifacts/reports/training_metrics.json`, **SKIP interaction importance calculation** (do not run SHAP interaction analysis or permutation importance for interactions), and log a warning. **Output**: Write `pure_aluminum_flag` as a boolean field in the JSON report. **Requirement**: This task requires T025 completion. **Artifact**: Save model to `artifacts/models/kinetic_model.pkl`. **Dependency**: T028.
- [ ] T030 [US2] Save trained model to `artifacts/models/kinetic_model.pkl`. **Format**: Use `pickle` protocol 4 for cross-version compatibility. **Dependency**: T029.
- [ ] T031 [US2] Implement k-fold cross-validation in `code/train.py` and calculate mean R² and std dev. **Dependency**: T030.
- [ ] T032 [US2] Implement held-out test set evaluation in `code/train.py`: Calculate MAE and R² on the test set. **Requirement**: Calculate the threshold as a fixed proportion of the baseline mean. (read from `artifacts/reports/baseline_stats.json` from T012) and compare the test MAE against this threshold. **Dependency**: T030, T012.
- [ ] T033 [US2] Generate `artifacts/reports/training_metrics.json` containing CV scores and test set MAE/R². **Format**: JSON schema must include `cv_r2_mean`, `cv_r2_std`, `test_mae`, `test_r2`, and `pure_aluminum_flag`. **Dependency**: T031, T032.
- [ ] T034 [US2] Implement "Pure Aluminum" dataset detection in `code/train.py`: Check if standard deviation of all composition columns (Mn, Mg, Si, Cu) is zero. If `std < 1e-9` for all composition columns, set `pure_aluminum_flag` to `true` in `artifacts/reports/training_metrics.json` and `artifacts/reports/shap_interaction_report.json` (if applicable) and log a warning. **Requirement**: The `pure_aluminum_flag` must be a structured field in the JSON report, not just a log message, to ensure testability per Edge Cases. **Conditional Path**: If `pure_aluminum_flag` is true, **exclude interaction terms from SHAP analysis (T042)** and **exclude interaction terms from Permutation Test (T040)** to prevent invalid results on zero-variance data. **Dependency**: T029.

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

- [ ] T037 [US3] Implement Baseline Model (Additive: cold work + composition, NO interactions) training in `code/evaluate.py` for comparison. **Requirement**: Use the SAME data split (seed=42) as T028. Train a Random Forest Regressor with identical hyperparameters to T029 (except no interaction features) to ensure a fair comparison. **Artifact**: Save model to `artifacts/models/additive_model.pkl` to ensure a distinct artifact for the comparison. **Dependency**: T028.
- [ ] T038 [US3] Ensure Interaction Model consistency in `code/evaluate.py`. **Requirement**: Load the Interaction Model from `artifacts/models/kinetic_model.pkl` (T030) if it exists and matches the expected parameters. If retraining is necessary for consistency, retrain with the EXACT same parameters and data split as T029. **Artifact**: Ensure `artifacts/models/kinetic_model.pkl` is used for the Interaction Model in the subsequent test. **Dependency**: T030.
- [ ] T039 [US3] Implement Delta-Permutation Test in `code/evaluate.py`:
 1. Load the Additive Model (T037) and Interaction Model (T038).
 2. Generate error distributions (MAE per fold) for BOTH models using k-fold cross-validation on the same split.
 3. **Permutation Logic**: For each permutation iteration (run `n_permutations=1000`), shuffle the values of the interaction terms (e.g., `cold_work_Mn_content`) in the validation set while holding main effects constant.
 4. Calculate the prediction error (MAE) for the Interaction Model on this shuffled data.
 5. Compare the distribution of these permuted errors against the original (unshuffled) error distribution of the Interaction Model.
 6. **Crucially**: Also compare the error distribution of the Interaction Model (unshuffled) against the error distribution of the Additive Model (T037) to determine if the interaction terms provide a statistically significant improvement over the additive baseline.
 7. Calculate the p-value (FR-005) as the proportion of permuted errors that are **LESS THAN OR EQUAL TO** the original error (assuming lower error is better). This determines if interaction terms provide statistically significant improvement (p < 0.05).
 8. Output to `artifacts/reports/statistical_significance.json`. **Requirement**: This p-value determines if interaction terms provide statistically significant improvement (p < 0.05). **Dependency**: T037, T038.
- [ ] T040 [US3] Implement Permutation Importance calculation in `code/evaluate.py`: Calculate permutation importance (drop in R² score) for interaction terms and verify > 0.01 threshold (SC-003). Update `artifacts/reports/statistical_significance.json` with key `permutation_importance`. **Dependency**: T039.
- [ ] T041 [US3] Implement SHAP Interaction Value analysis in `code/evaluate.py` to rank features by unique contribution (FR-006). **Prerequisites**: `data/processed/engineered_features.csv` (from T024) and `artifacts/models/kinetic_model.pkl` (from T030). **Parameters**: Use `TreeExplainer` with `nsamples=1000` for determinism and `random_state=42` to ensure reproducibility. **Output Requirement**: The output report MUST explicitly separate 'interaction term contributions' from 'main effects' in the JSON structure (e.g., `main_effects_ranking` and `interaction_terms_ranking` keys). **Dependency**: T024, T030.
- [ ] T042 [US3] Generate `artifacts/reports/statistical_significance.json` containing p-value, test statistic, and conclusion. **Dependency**: T039, T040.
- [ ] T043 [US3] Generate `artifacts/reports/shap_interaction_report.json` with top features and interaction terms. Include `pure_aluminum_flag` status if detected in T034. **Dependency**: T041.
- [ ] T044 [US3] Verify Success Criteria:
 1. Check p-value < 0.05 (from T039/T042).
 2. Check Permutation Importance > 0.01 (from T040).
 3. Check R² > 0.6 (SC-001). **Logic**: Read `test_r2` from `artifacts/reports/training_metrics.json`. If R² <= 0.6, flag failure. Do NOT flag if R² > 0.6.
 Flag in report if any criteria fail (do not crash, but document failure). **Dependency**: T033, T042.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T045 [P] Documentation updates: Update `README.md` installation steps. **Requirement**: Update `README.md` with a 5-step execution guide. **Steps to document**: 1. Install deps (`pip install -r requirements.txt`), 2. Generate data (`python code/generate_synthetic.py`), 3. Ingest & Engineer (`python code/ingest.py`), 4. Train (`python code/train.py`), 5. Evaluate (`python code/evaluate.py`).
- [ ] T046 [P] Documentation updates: Update `quickstart.md` with a 5-step execution guide. **Requirement**: Update `quickstart.md` with a 5-step execution guide. **Steps to document**: 1. Install deps (`pip install -r requirements.txt`), 2. Generate data (`python code/generate_synthetic.py`), 3. Ingest & Engineer (`python code/ingest.py`), 4. Train (`python code/train.py`), 5. Evaluate (`python code/evaluate.py`).
- [ ] T047 [P] Refactor `code/utils.py` for clarity and performance. **Metric**: Reduce cyclomatic complexity score of `utils.py` functions to < 5 using `radon cc code/utils.py -a`.
- [ ] T048 [P] Refactor `code/ingest.py` to ensure strict error handling on data fetch. **Logic**: If external data fetch fails, proceed with the synthetic dataset already loaded; do not halt. (Note: Synthetic is primary per FR-001).
- [ ] T049 [P] Ensure model training parameters are set to `n_estimators=100` and `max_depth=None` (default) in `code/train.py` to ensure runtime < 60 min on 10k rows. **Metric**: Verify training time < 60 min on CI runner.
- [ ] T050 [P] Implement chunked data loading in `code/engineer.py` and `code/evaluate.py` if file size > 5MB. **Requirement**: Use `chunksize=1000` for `pandas.read_csv` to reduce memory peak usage.
- [ ] T051 [P] Write unit tests for `code/utils.py` in `tests/unit/test_utils.py`.
- [ ] T052 [P] Write unit tests for `code/engineer.py` in `tests/unit/test_engineer.py`.
- [ ] T053 [P] Write unit tests for `code/evaluate.py` in `tests/unit/test_evaluate.py`.
- [ ] T054 [P] Security hardening (input sanitization). **Requirement**: Implement `pandas.read_csv` with explicit `dtype` enforcement and `na_filter=True` to sanitize inputs and prevent type confusion.
- [ ] T055 [P] [Optional] Implement external data fetching logic in `code/ingest_external.py` to attempt fetching from NIST/HuggingFace. **Logic**: If fetch fails, log a warning and proceed with the synthetic dataset already loaded in T011/T022; do NOT halt the pipeline. Synthetic is the primary source per FR-001. If a public dataset is available and fetch succeeds, append it to the synthetic data. This task is non-blocking and separate from the primary ingestion flow.
- [ ] T056 [P] Run `quickstart.md` validation to ensure end-to-end execution of the full pipeline (US1 + US2 + US3). **Command**: `python code/main.py`. **Success Criteria**: Exit code 0, and files `data/raw/synthetic_baseline.csv`, `data/processed/final_dataset.csv`, `artifacts/models/kinetic_model.pkl`, `artifacts/reports/training_metrics.json`, `artifacts/reports/statistical_significance.json` must exist. **Requirement**: No CLI arguments required.

---

## Phase 6: Revision & Analysis Resolution (Post-Analysis)

**Purpose**: Address specific reviewer concerns and ensure strict adherence to the "No Fabrication" and "Real Data" rules.

- [ ] T057 [P] [Review] Ensure T034 correctly flags pure aluminum datasets in the report artifacts. **Requirement**: Verify `pure_aluminum_flag` is present in `training_metrics.json` and `shap_interaction_report.json` when applicable.
- [ ] T058 [P] [Review] Verify T039 implements the specific Permutation Test (shuffling interaction terms) logic. **Requirement**: Confirm the test shuffles interaction terms while holding main effects constant, not a Mann-Whitney U test.
- [ ] T059 [P] [Review] Verify T024 does not include `cold_work * Temperature` but DOES include `annealing_temp_K` as a standalone feature. **Requirement**: Confirm feature engineering strictly follows FR-002.
- [ ] T060 [P] [Review] Verify T011 generates checksums. **Requirement**: Confirm `synthetic_baseline.csv.sha256` exists and is recorded in state YAML.
- [ ] T061 [P] [Review] Verify T055 logic for data source failures. **Requirement**: Confirm that T055 correctly distinguishes between:
 1. **Local Synthetic Generator Failure** (T011): Must raise an error (Fail-Loud).
 2. **External Data Fetch Failure** (T055): Must proceed with synthetic data (Fail-Safe/Fallback).
 Ensure no task requires raising an error for external fetch failures, as this contradicts FR-001 and T055.
- [ ] T062 [P] [Review] Verify T013 (main.py) implementation. **Requirement**: Confirm `code/main.py` exists and correctly orchestrates the pipeline (T011 -> T022 -> T024 -> T029 -> T039).
- [ ] T063 [P] [Review] Verify T022 does not contain any `try/except` blocks that fallback to synthetic data if the primary load fails. **Requirement**: The load of `data/raw/synthetic_baseline.csv` must be a direct read; if the file is missing, the script must crash with a clear `FileNotFoundError` to satisfy the "Fail-Loud" principle for the primary source.
- [ ] T064 [P] [Review] Verify T021 outlier clipping is applied BEFORE T037/T039 statistical tests. **Requirement**: Confirm the data passed to the Permutation Test is the clipped version from `data/processed/validated.csv` (post-T021), not the raw version.
- [ ] T065 [P] [Review] Verify T028 stratification logic handles the case where `time_to_peak_min` has low variance. **Requirement**: Ensure `train_test_split` does not crash if binning results in empty bins; implement a fallback to non-stratified split with a warning if stratification is impossible.
- [ ] T066 [P] [Review] Verify T011 dataset size cap logic. **Requirement**: Confirm `generate_synthetic.py` enforces a hard cap on row count (e.g., `n_rows = min(requested, 10000)`) to prevent memory overflow on the CI runner, as mandated by FR-003 and Constitution Principle VII.
- [ ] T067 [P] [Review] Verify T029 handles the "Pure Aluminum" edge case without crashing. **Requirement**: Confirm that if `std < 1e-9` for composition columns, the model training either skips interaction feature importance calculation or handles the zero-variance input gracefully (e.g., by excluding interaction features from the model input for that specific run) while still producing a valid `pure_aluminum_flag: true` in the report.
- [ ] T068 [P] [Review] Verify T041 SHAP calculation parameters. **Requirement**: Confirm `TreeExplainer` is used with `nsamples=1000` and `random_state=42` to ensure deterministic and reproducible SHAP values, avoiding stochastic variance in the interaction analysis.

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
- **Critical Constraint**: All tasks must run on free CPU-only CI (limited cores, constrained RAM, no GPU). No 8-bit/4-bit quantization, no CUDA, no large LLMs.
- **Data Integrity**: Use `code/generate_synthetic.py` for baseline data if real data is unavailable; **synthetic is the PRIMARY source**. If external fetch fails, proceed with synthetic (do not halt).
- **Data Flow**: Ensure data ingestion (US1) completes before model training (US2), and model training completes before validation (US3).
- **Statistical Rigor**: Permutation Test (shuffling interaction terms) and SHAP Interaction Values are mandatory for US3 to validate the "pinning effect" hypothesis.
- **Imputation Logic**: Missing composition values must be imputed using the mean of the specific alloy series, not a global mean.
- **Interaction Terms**: Explicitly calculate `cold_work * Mn_content`, `cold_work * Mg_content`, `cold_work * Si_content`, `cold_work * Cu_content`. **Do NOT** calculate `cold_work * Temperature`. **MUST** include `annealing_temp_K` as a standalone feature.
- **Revision Focus**: Phase 6 tasks specifically address the "No Fabrication" rule by ensuring data loaders fail loudly on local generation errors but fall back to synthetic data on external fetch errors, maintaining the synthetic generator as the guaranteed primary source.