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

- [ ] T008 [P] (Research) Create `research.md` in `specs/001-predict-strain-rate-yield/` verifying dataset availability (NIST, OpenML, Materials Project) and Johnson-Cook/Zerilli-Armstrong parameters (Plan Task 0.1/0.2). **MUST complete before Phase 1.**
- [ ] T051 [P] (Research) Estimate total sample size (N) and per-alloy-family counts from NIST/OpenML metadata (Plan Task 0.5.1)
- [ ] T052 [P] (Research) Perform power analysis: If N < 1000 or any alloy family N < 50, flag as "Underpowered" and recommend scope adjustment (Plan Task 0.5.2)
- [ ] T053 [P] (Research) Confirm CPU feasibility: Ensure the estimated data subset fits in available RAM. (Plan Task 0.5.3)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure.

- [ ] T001.1 [P] Create directory structure: `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/`, `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/tests/`, `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/data/`
- [ ] T001.2 [P] Create `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/ingestion/`, `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/modeling/`, `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/visualization/`
- [ ] T001.3 [P] Create `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/tests/unit/`, `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/tests/contract/`, `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/tests/integration/`
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
- [ ] T007.2 [P] Implement `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/utils/validation.py`: Create `validate_research.py` script that reads `research.md` and halts if datasets are missing (Depends on T008)

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest heterogeneous tensile test data, standardize units, and perform two-step imputation (composition then grain size) to create a clean, unified dataset.

**Independent Test**: Can be fully tested by running the ingestion script against a mock dataset and verifying that the output CSV contains standardized units, imputed values for missing grain sizes, and correctly encoded composition vectors.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Unit test for unit conversion logic in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/tests/unit/test_ingestion.py`
- [ ] T010 [P] [US1] Unit test for two-step KNN imputation logic in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/tests/unit/test_imputation.py`
- [ ] T011 [P] [US1] Contract test for dataset schema validation in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/tests/contract/test_dataset_schema.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `fetchers.py` in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/ingestion/` to fetch data from NIST, OpenML, and Materials Project using `config.NIST_URL`, `config.OPENML_ID`, and `config.MATERIALS_PROJECT_API_KEY`. **MUST resolve these config variables to real, reachable URLs/APIs before execution. No fabrication.** (FR-001)
- [ ] T013 [US1] Implement `preprocess.py` in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/ingestion/` to standardize units (MPa, s⁻¹, µm) and drop records missing Yield Strength or Strain Rate (FR-003)
- [ ] T013.1 [US1] Save the pre-imputation dataset state (post-filtering, pre-imputation) to `data/processed/grain_size_raw.csv` immediately after T013 filtering. **This artifact is required for T038 Sensitivity Analysis.** (Critical for FR-008)
- [ ] T014 [US1] Implement composition imputation logic in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/ingestion/preprocess.py`: If alloy composition is missing, impute using Alloy Family average (FR-003)
- [ ] T015.0 [US1] Implement correlation validation in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/ingestion/preprocess.py`: Compute correlation between **raw** composition and grain size. If r < 0.3, flag records in `imputation_confidence` column or drop them; generate `data/processed/low_confidence_records.csv`. **Do not proceed to KNN if r < 0.3** (FR-003, Plan Task 1.3)
- [ ] T015 [US1] Implement KNN grain size imputation logic in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/ingestion/preprocess.py` with k=5, **only if T015.0 passes**. **If r < 0.3, records MUST be dropped or flagged; do not proceed with imputation.** (FR-003)
- [ ] T016 [US1] Implement -dimensional elemental fraction vector encoding in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/ingestion/preprocess.py`
- [ ] T017 [US1] Implement stratified split logic (by Alloy Family, N≥20 per stratum) in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/ingestion/preprocess.py`

---

## Phase 4: User Story 2 - Model Training and Baseline Comparison (Priority: P2)

**Goal**: Train ML models (RF, GB, Linear, Ridge) with hyperparameter tuning and compare against empirical models (Johnson-Cook, Zerilli-Armstrong) using nested cross-validation.

**Independent Test**: Can be fully tested by training models on a subset of the data and verifying that the output includes performance metrics for both ML and empirical models, with the ML models showing tunable hyperparameters.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for ML model training loop in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/tests/unit/test_ml_models.py`
- [ ] T020 [P] [US2] Unit test for empirical model fitting (Johnson-Cook, Zerilli-Armstrong) in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/tests/unit/test_empirical_models.py`
- [ ] T021 [P] [US2] Contract test for model output schema in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/tests/contract/test_model_output_schema.py`

### Implementation for User Story 2

- [ ] T022 [P] [US2] Implement `ml_models.py` in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/modeling/` for RF, GB, Linear, Ridge with Grid Search
- [ ] T023 [P] [US2] Implement `empirical_models.py` in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/modeling/` for Johnson-Cook and Zerilli-Armstrong fitting/prediction
- [ ] T024 [US2] Implement nested cross-validation logic in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/modeling/evaluation.py` to ensure independent test sets
- [ ] T025 [US2] Implement robustness analysis (multiple random seeds) in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/modeling/evaluation.py` (SC-004)
- [ ] T026 [US2] Implement calculation of R², MAE, RMSE for all models in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/modeling/evaluation.py` (SC-001)
- [ ] T038 [US2] Implement Sensitivity Analysis (FR-008, SC-005): Train models on `data/processed/grain_size_raw.csv` (raw) and `data/processed/grain_size_imputed.csv` (imputed); compare R² to quantify bias. Save results to `data/processed/sensitivity_analysis.csv`. **Depends on T013.1 (raw data) and T022-T026 (model training).** (FR-008)

---

## Phase 5: User Story 3 - Interpretability and Failure Regime Analysis (Priority: P3)

**Goal**: Interpret the best-performing model, generate partial dependence plots, and perform statistical significance tests to identify where empirical models fail.

**Independent Test**: Can be fully tested by generating partial dependence plots for a specific alloy family and verifying that the plot shows the expected non-linear relationship between strain rate and yield strength.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test for SHAP value extraction in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/tests/unit/test_evaluation.py`
- [ ] T028 [P] [US3] Unit test for Wilcoxon signed-rank test implementation in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/tests/unit/test_evaluation.py`

### Implementation for User Story 3

- [ ] T029.0 [P] [US3] Create `data/config/literature_expectations.yaml` with expected SHAP thresholds (≥0.1) and expected top 3 features: `["strain_rate", "composition", "grain_size"]` (SC-002)
- [ ] T029 [P] [US3] Implement SHAP feature importance extraction in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/modeling/evaluation.py`. **Verify specifically** that `strain_rate`, `composition`, and `grain_size` rank in the top 3. Assert `top_3_features == ["strain_rate", "composition", "grain_size"]` or log failure. **Verify SHAP values ≥ 0.1 or p-values < 0.05.** (US-3, SC-002)
- [ ] T030 [US3] Implement Wilcoxon signed-rank test with Benjamini-Hochberg correction in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/modeling/evaluation.py` to compare ML vs. Empirical errors (FR-007, SC-003)
- [ ] T031 [US3] Implement Partial Dependence Plot generation for strain rate vs. yield strength for multiple alloy families in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/visualization/plots.py` (FR-006)
- [ ] T032 [US3] Implement logic to detect and report non-monotonic regimes in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/code/visualization/plots.py`
- [ ] T033 [US3] Implement failure regime identification (high strain rate, specific alloys) and **save results to `data/processed/failure_regimes.csv`** (FR-006, US-3)

---

## Phase 6: Reporting & Polish

**Purpose**: Compile results, generate figures, and finalize documentation

- [ ] T034 [P] Compile `metrics.json` and `wilcoxon_test.csv` in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/data/processed/`
- [ ] T035 Generate final figures (PDP, Error Distribution) in `projects/PROJ-244-predicting-the-impact-of-strain-rate-on-/data/processed/`
- [ ] T036 Append Section 4.2 to `research.md` documenting regimes where empirical models fail, using data from `data/processed/failure_regimes.csv` (T033)
- [ ] T037 [P] Run quickstart.md validation and ensure full pipeline execution ≤ 4 hours

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0**: No dependencies - can start immediately. T008 (Research) must complete before T007.2 (Validation).
- **Phase 0.5**: Depends on Phase 0 completion.
- **Phase 1**: Depends on Phase 0.5 completion.
- **Phase 2**: Depends on Phase 1 completion. T006 must complete before T012-T017.
- **Phase 3 (US1)**: Depends on Phase 2 completion.
- **Phase 4 (US2)**: Depends on Phase 3 completion (data output).
- **Phase 5 (US3)**: Depends on Phase 4 completion (model output).
- **Phase 6**: Depends on Phase 5 completion.

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

- All Phase 0 research tasks (T008, T051-T053) can run in parallel.
- All Phase 1 setup tasks (T001.1-T003.2) can run in parallel.
- All Phase 2 foundational tasks (T004.1-T007.2) can run in parallel, **except** T007.2 depends on T008, and T006 must complete before T012-T017.
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
- **Critical Constraint**: All data fetches must use real, reachable URLs/APIs. No synthetic data or fabrication allowed.
- **Critical Constraint**: All models must run on CPU-only (limited cores, 7GB RAM). No GPU or 8-bit quantization.
- **Critical Constraint**: T015.0 correlation check must use **raw** composition data (pre-imputation) to ensure FR-003 compliance.
- **Critical Constraint**: T013.1 must save the raw state immediately after filtering to enable T038 sensitivity analysis.
- **Critical Constraint**: T006 (entities) is a hard prerequisite for T012-T017; do not treat as parallel with downstream consumers.
- **Critical Constraint**: T029 must explicitly verify that `strain_rate`, `composition`, and `grain_size` are the top 3 features.