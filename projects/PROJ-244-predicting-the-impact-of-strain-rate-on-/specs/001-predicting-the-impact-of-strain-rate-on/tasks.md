# Tasks: Predicting the Impact of Strain Rate on the Yield Strength of Metals

**Input**: Design documents from `/specs/001-predict-strain-rate-yield/`
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

---

## Phase 0: Data Discovery & Feasibility (Research)

**Purpose**: Verify data availability and feasibility before coding begins.

- [ ] T008.1 (Research) **Fetch NIST Data**: Attempt to fetch data from NIST Materials Data Repository as defined in `config.py`. Log success or failure to `data/fetch_log.txt`. If unreachable, log the specific error. (FR-001)
- [ ] T008.2 (Research) **Fetch OpenML Data**: Attempt to fetch data from OpenML as defined in `config.py`. Log success or failure to `data/fetch_log.txt`. If unreachable, log the specific error. (FR-001)
- [ ] T008.3 (Research) **Fetch Materials Project Data**: Attempt to fetch data from Materials Project API as defined in `config.py`. Log success or failure to `data/fetch_log.txt`. If unreachable, log the specific error. (FR-001)
- [ ] T008.4 (Research) **Update Research Documentation**: Create or update `research.md` in `specs/001-predict-strain-rate-yield/` with the results of T008.1-T008.3. **MUST update the Verified Datasets table** with specific data source paths or document the fallback to the Physics-Consistent Simulated Data generator with a "Data Unavailable" artifact ONLY IF T008.1-T008.3 all failed. (FR-001) **MUST complete before Phase 1.**
- [X] T009 [P] (Research) Estimate total sample size (N) and per-alloy-family counts from simulated generator parameters or research.md feasibility report (Plan Task 0.5.1) <!-- FAILED: unspecified -->
- [X] T010 [P] (Research) Perform power analysis: If N < 1000 or any alloy family N < 50, flag as "Underpowered" and recommend scope adjustment (Plan Task 0.5.2)
- [X] T011 [P] (Research) Confirm CPU feasibility: Ensure the estimated data subset fits in available RAM. (Plan Task 0.5.3)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure.

- [ ] T001.1 [P] **Initialize Directory Structure**: Create all required directories in one step: `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/`, `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/tests/`, `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/data/`, `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/ingestion/`, `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/modeling/`, `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/visualization/`, `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/tests/unit/`, `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/tests/contract/`, `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/tests/integration/`.
- [ ] T002.1 [P] Initialize `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/requirements.txt` with pinned versions: `pandas`, `scikit-learn`, `scipy`, `numpy`, `matplotlib`, `seaborn`, `pyyaml`, `statsmodels`, `pytest`, `pytest-cov`
- [ ] T002.2 [P] Initialize `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/pyproject.toml` or `setup.py` for package installation
- [ ] T003.1 [P] Configure `flake8` or `pylint` in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/.flake8` or `pyproject.toml`
- [ ] T003.2 [P] Configure `black` and `isort` in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. T006 must complete before T012-T017.

- [ ] T004.1 [P] Implement `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/config.py`: Define `NIST_URL`, `OPENML_ID`, `MATERIALS_PROJECT_API_KEY`, `RANDOM_SEED`, and path constants (`DATA_RAW`, `DATA_PROCESSED`)
- [ ] T004.2 [P] Implement `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/config.py`: Define `UNIT_CONVERSIONS` (MPa, s⁻¹, µm) and `IMPUTATION_THRESHOLD` (r=0.3)
- [ ] T004.3 [P] Implement `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/config.py`: Define `LITERATURE_EXPECTATIONS_PATH` pointing to `data/config/literature_expectations.yaml`
- [ ] T005.1 [P] Implement `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/main.py`: Create `main()` entry point that sequences phases (0->1->2->3->4)
- [ ] T005.2 [P] Implement `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/main.py`: Add logging setup and argument parsing for `--phase` and `--seed`
- [ ] T006.1 Implement `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/entities.py`: Define `TensileTestRecord` dataclass with fields: `yield_strength_mpa`, `strain_rate_s_inv`, `temperature_k`, `grain_size_um`, `alloy_composition`, `alloy_family`
- [ ] T006.2 Implement `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/entities.py`: Define `AlloyFamily` enum or class with common families (AA-6061, AISI-4340, etc.)
- [ ] T006.3 Implement `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/entities.py`: Define `ConstitutiveModel` and `MLModel` base classes/interfaces
- [ ] T007.1 [P] Implement `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/utils/logging.py`: Setup logging to file and console with levels
- [ ] T007.2 (Sequential) Implement `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/utils/validation.py`: Create `validate_research.py` script that reads `research.md` and halts if datasets are missing (Depends on T008.4). **MUST run AFTER T008.4.**

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest heterogeneous tensile test data, standardize units, and perform two-step imputation (composition then grain size) to create a clean, unified dataset.

**Independent Test**: Can be fully tested by running the ingestion script against a mock dataset and verifying that the output CSV contains standardized units, imputed values for missing grain sizes, and correctly encoded composition vectors.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Unit test for unit conversion logic in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/tests/unit/test_ingestion.py` <!-- SKIPPED: YAML+regex parse failed (while scanning a simple key
 in "<unicode string>", line 4, column 1:
 1. **Yield strength conversion**...
 ^
could not find expected ':'
 in "<unicode string>", line 5, column 1:
 2. **Strain rate conversion** (s...
 ^) -->
- [X] T010 [P] [US1] Unit test for two-step KNN imputation logic in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/tests/unit/test_imputation.py` <!-- FAILED: unspecified -->
- [X] T011 [P] [US1] Contract test for dataset schema validation in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/tests/contract/test_dataset_schema.py`

### Implementation for User Story 1

- [ ] T012.1 [US1] **Fetch NIST Data**: Implement `fetchers.py` in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/ingestion/` to attempt fetching data from NIST. **Must log success or failure to `data/fetch_log.txt`.** (FR-001)
- [ ] T012.2 [US1] **Fetch OpenML Data**: Implement `fetchers.py` in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/ingestion/` to attempt fetching data from OpenML. **Must log success or failure to `data/fetch_log.txt`.** (FR-001)
- [ ] T012.3 [US1] **Fetch Materials Project Data**: Implement `fetchers.py` in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/ingestion/` to attempt fetching data from Materials Project. **Must log success or failure to `data/fetch_log.txt`.** (FR-001)
- [ ] T012.4 [US1] **Activate Simulated Generator**: Implement `fetchers.py` in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/ingestion/` to conditionally activate the Physics-Consistent Simulated Data generator **only if** T012.1-T012.3 all fail. **Must write `data/fallback_reason.txt` documenting the failure.** (FR-001)
- [ ] T013 [US1] Implement `preprocess.py` in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/ingestion/` to standardize units (MPa, s⁻¹, µm) and **drop records missing Yield Strength or Strain Rate** (FR-003).
- [ ] T013.1 [US1] Save the pre-imputation dataset state (post-filtering, pre-imputation) to `data/processed/raw_for_sensitivity.csv` immediately after T013 filtering. **This artifact is required for T038 Sensitivity Analysis.** (Critical for FR-008)
- [ ] T015.0 [US1] **Correlation Validation & Flagging**: Implement correlation validation in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/ingestion/preprocess.py`: Compute correlation between the **joint vector of [raw composition, strain_rate]** and grain size (using `data/processed/raw_for_sensitivity.csv`). If r < 0.3, flag records in `imputation_confidence` column; **DO NOT drop them from the main dataset** (retain in `imputed.csv`) but **exclude them from the sensitivity dataset** (T013.2). **Output: `data/processed/correlation_check.log` (contains 'r' value) and `data/processed/low_confidence_records.csv`.** (FR-003, Plan Task 1.3)
- [ ] T013.2 [US1] **Create Sensitivity Dataset**: Filter `data/processed/raw_for_sensitivity.csv` to **exclude records flagged as low-confidence by T015.0**. **Output: `data/processed/sensitivity_dataset.csv`.** **MUST run AFTER T015.0.** (FR-008)
- [ ] T014 [US1] **Composition Imputation**: Implement composition imputation logic in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/ingestion/preprocess.py`: If alloy composition is missing, impute using Alloy Family average (FR-003). **Must run AFTER T015.0.** **Output: `data/processed/composition_imputed.csv`.**
- [ ] T015 [US1] **KNN Grain Size Imputation**: Implement KNN grain size imputation logic in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/ingestion/preprocess.py` with k=5, **using imputed composition (from T014) AND strain_rate (from raw data) as predictors**. **Must run AFTER T014.** **Gate: T014 must have generated `composition_imputed.csv`.** **Output: `data/processed/imputed.csv`.** (FR-003)
- [ ] T016 [US1] **Elemental Fraction Encoding**: Implement high-dimensional elemental fraction vector encoding in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/ingestion/preprocess.py`. **Output: `data/processed/encoded_features.csv` (10-dimensional float array of elemental mass fractions).**
- [ ] T017 [US1] **Stratified Split**: Implement stratified split logic (by Alloy Family, N≥20 per stratum) in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/ingestion/preprocess.py`. **Output: `data/processed/train.csv`, `data/processed/test.csv` (using RANDOM_SEED from config).**

### **Sequential Execution Block for Phase 3 (CRITICAL)**
**Execute strictly in this order:**
1. T013 (Standardize & Drop)
2. T013.1 (Save Raw State)
3. T015.0 (Correlation Check & Flag)
4. T013.2 (Create Sensitivity Dataset)
5. T014 (Impute Composition)
6. T015 (Impute Grain Size)
7. T016 (Encode Features)
8. T017 (Split Data)

---

## Phase 4: User Story 2 - Model Training and Baseline Comparison (Priority: P2)

**Goal**: Train ML models (RF, GB, Linear, Ridge) with hyperparameter tuning and compare against empirical models (Johnson-Cook, Zerilli-Armstrong) using nested cross-validation.

**Independent Test**: Can be fully tested by training models on a subset of the data and verifying that the output includes performance metrics for both ML and empirical models, with the ML models showing tunable hyperparameters.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T019 [P] [US2] Unit test for ML model training loop in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/tests/unit/test_ml_models.py`
- [~] T020 [P] [US2] Unit test for empirical model fitting (Johnson-Cook, Zerilli-Armstrong) in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/tests/unit/test_empirical_models.py`
- [~] T021 [P] [US2] Contract test for model output schema in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/tests/contract/test_model_output_schema.py`

### Implementation for User Story 2

- [~] T022 [P] [US2] **Train ML Models**: Implement `ml_models.py` in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/modeling/` for RF, GB, Ridge with Grid Search. **Output: `data/models/ml_rf.pkl`, `data/models/ml_gb.pkl`, etc.** (FR-004)
- [ ] T022.1 [P] [US2] **Train Linear Models**: Implement `ml_models.py` in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/modeling/` for Linear Regression with Grid Search (FR-004, Plan Task T016.1)
- [~] T023 [P] [US2] **Fit Empirical Models**: Implement `empirical_models.py` in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/modeling/` for Johnson-Cook and Zerilli-Armstrong fitting/prediction. **Output: `data/models/empirical_params.yaml`.** (FR-005)
- [~] T024 [US2] **Nested Cross-Validation**: Implement nested cross-validation logic in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/modeling/evaluation.py` to ensure independent test sets. **Output: `data/processed/cv_scores.csv`.** (FR-004)
- [~] T025 [US2] **Robustness Analysis**: Implement robustness analysis (multiple random seeds) in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/modeling/evaluation.py` (SC-004). **Aggregate stability metrics (variance of R² across seeds) and save to `results/robustness_metrics.json`.** (SC-004)
- [ ] T025.1 [US2] **Stability Reporting**: Ensure `results/robustness_metrics.json` contains the aggregated stability metrics. (SC-004)
- [~] T026 [US2] **Calculate Metrics**: Implement calculation of R², MAE, RMSE for all models in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/modeling/evaluation.py` (SC-001)

### Sequential Phase 4 Tasks (Dependent on T022-T026)

- [~] T038 [US1+US2] **Sensitivity Analysis**: Implement Sensitivity Analysis (FR-008, SC-005): **Re-train models (distinct from T022-T026)** on `data/processed/raw_for_sensitivity.csv` (raw) and `data/processed/sensitivity_dataset.csv` (imputed, low-confidence excluded); compare R² to quantify bias. Save results to `results/sensitivity_analysis.json`. **MUST run AFTER T022-T026 complete.** (FR-008)

---

## Phase 5: User Story 3 - Interpretability and Failure Regime Analysis (Priority: P3)

**Goal**: Interpret the best-performing model, generate partial dependence plots, and perform statistical significance tests to identify where empirical models fail.

**Independent Test**: Can be fully tested by generating partial dependence plots for a specific alloy family and verifying that the plot shows the expected non-linear relationship between strain rate and yield strength.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T027 [P] [US3] Unit test for SHAP value extraction in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/tests/unit/test_evaluation.py`
- [~] T028 [P] [US3] Unit test for Wilcoxon signed-rank test implementation in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/tests/unit/test_evaluation.py`

### Implementation for User Story 3

- [~] T029.0 [P] [US3] Create `data/config/literature_expectations.yaml` with expected SHAP thresholds (≥0.1) and expected top 3 features: `["strain_rate", "composition", "grain_size"]` (SC-002)
- [~] T029 [P] [US3] **SHAP Feature Importance**: Implement SHAP feature importance extraction in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/modeling/evaluation.py`. **Gate: Assert PASS if `strain_rate`, `composition`, and `grain_size` rank in the top 3 with SHAP values ≥ 0.1; else FAIL.** **Output: `data/processed/shap_values.csv`, `results/feature_importance_report.json` (PASS/FAIL).** (US-3, SC-002)
- [~] T030 [US3] **Statistical Tests**: Implement Wilcoxon signed-rank test with Benjamini-Hochberg correction in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/modeling/evaluation.py` to compare ML vs. Empirical errors (FR-007, SC-003)
- [~] T031 [US3] **Partial Dependence Plots**: Implement Partial Dependence Plot generation for strain rate vs. yield strength for **at least three** representative alloy families (e.g., largest N per family OR families with diverse physics) in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/visualization/plots.py`. **Output: `results/plots/pdp_[alloy_family].png`.** (FR-006)
- [~] T032 [US3] **Non-Monotonic Detection**: Implement logic to detect and report non-monotonic regimes in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/visualization/plots.py`
- [~] T033 [US3] **Failure Regime Identification**: Implement failure regime identification (high strain rate, specific alloys) and **save results to `data/processed/failure_regimes.csv`** (FR-006, US-3)

---

## Phase 6: Reporting & Polish

**Purpose**: Compile results, generate figures, and finalize documentation

- [~] T034 [P] Compile `metrics.json` and `wilcoxon_test.csv` in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/data/processed/`
- [~] T035 **Generate Final Figures**: Generate final figures (PDP, Error Distribution) in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/data/processed/`. **Output: `results/plots/pdp_summary.png`, `results/plots/error_dist.png`.**
- [~] T036 Append Section 4.2 to `research.md` documenting regimes where empirical models fail, using data from `data/processed/failure_regimes.csv` (T033)
- [~] T037 [P] Run quickstart.md validation and ensure full pipeline execution ≤ 4 hours

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0**: No dependencies - can start immediately. T008.1-T008.3 must complete before T008.4, and T008.4 must complete before T007.2 (Validation).
- **Phase 0.5**: Depends on Phase 0 completion.
- **Phase 1**: Depends on Phase 0.5 completion.
- **Phase 2**: Depends on Phase 1 completion. T006 must complete before T012-T017.
- **Phase 3 (US1)**: Depends on Phase 2 completion. **Follow Sequential Execution Block strictly.**
- **Phase 4 (US2)**: Depends on Phase 3 completion (data output). **Includes T038 which depends on T022-T026 completion.**
- **Phase 5 (US3)**: Depends on Phase 4 completion (model output).
- **Phase 6**: Depends on Phase 5 completion.

### Intra-Phase Ordering for Phase 3
- **CRITICAL**: Execute T013 -> T013.1 -> T015.0 -> T013.2 -> T014 -> T015 -> T016 -> T017 sequentially.
- T013.1 reads raw data (from T013).
- T015.0 reads raw data (from T013.1) to flag low-confidence records.
- T013.2 filters T013.1 based on T015.0 flags (Depends on T015.0).
- T014 overwrites raw composition with imputed values (Depends on T015.0).
- T015 uses the imputed composition from T014 and strain rate.
- T013.1 must run before T015.0.

### Intra-Phase Ordering for Phase 4
- **Critical**: Execute T022, T022.1, T023, T024, T025, T026 sequentially (or in parallel if independent files, but T038 must wait).
- **Critical**: T038 (Sensitivity Analysis) MUST run strictly AFTER T022-T026 are complete. T038 cannot run in parallel with T022-T026 as it requires their outputs for comparison.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 2.
- **User Story 2 (P2)**: Depends on US1 data output.
- **User Story 3 (P3)**: Depends on US2 model output.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation.
- Models before services.
- Services before endpoints.
- Core implementation before integration.
- Story complete before moving to next priority.

### Parallel Opportunities

- All Phase 0 research tasks (T008.1-T008.3) can run in parallel, **except** T008.4 depends on T008.1-T008.3.
- All Phase 1 setup tasks (T001.1-T003.2) can run in parallel.
- All Phase 2 foundational tasks (T004.1-T007.1) can run in parallel, **except** T007.2 depends on T008.4, and T006 must complete before T012-T017.
- Once Phase 2 completes, all user stories can start in parallel (if team capacity allows).
- All tests for a user story marked [P] can run in parallel.
- Models within a story marked [P] can run in parallel.
- Different user stories can be worked on in parallel by different team members.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for unit conversion logic in projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/tests/unit/test_ingestion.py"
Task: "Unit test for two-step KNN imputation logic in projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/tests/unit/test_imputation.py"

# Launch all models for User Story 1 together:
Task: "Implement fetchers.py in projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/ingestion/"
Task: "Implement preprocess.py in projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/ingestion/"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Data Discovery
2. Complete Phase 0.5: Power & Feasibility
3. Complete Phase 1: Setup
4. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
5. Complete Phase 3: User Story 1
6. **STOP and VALIDATE**: Test User Story 1 independently
7. Deploy/demo if ready

### Incremental Delivery

1. Complete Phase 0 + Phase 0.5 + Phase 1 + Phase 2 → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0 + Phase 0.5 + Phase 1 + Phase 2 together
2. Once Phase 2 is done:
 - Developer A: User Story 1 (Data)
 - Developer B: User Story 2 (Modeling)
 - Developer C: User Story 3 (Interpretability)
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
- **Critical Constraint**: All data fetches must use real, reachable URLs/APIs. If unavailable, use the simulated generator. No synthetic data or fabrication allowed.
- **Critical Constraint**: All models must run on CPU-only (limited cores, constrained RAM). No GPU or 8-bit quantization.
- **Critical Constraint**: T015.0 correlation check must use **joint vector of raw composition and strain rate** to ensure FR-003 compliance.
- **Critical Constraint**: T013.1 must save the raw state immediately after filtering to enable T038 sensitivity analysis.
- **Critical Constraint**: T013.2 must create a distinct artifact for sensitivity analysis excluding low-confidence records.
- **Critical Constraint**: T006 (entities) is a hard prerequisite for T012-T017; do not treat as parallel with downstream consumers.
- **Critical Constraint**: T029 must explicitly verify that `strain_rate`, `composition`, and `grain_size` are in the top 3, and report PASS/FAIL against the threshold.
- **Critical Constraint**: Phase 3 ordering: T013 -> T013.1 -> T015.0 -> T013.2 -> T014 -> T015.
- **Critical Constraint**: Phase 4 ordering: T038 must run AFTER T022-T026.
- **Critical Constraint**: T015 must use **strain rate** as a predictor for KNN imputation.
- **Critical Constraint**: T025.1 must aggregate and report stability metrics.
- **Critical Constraint**: T012.1-T012.4 must attempt real fetches before simulation.