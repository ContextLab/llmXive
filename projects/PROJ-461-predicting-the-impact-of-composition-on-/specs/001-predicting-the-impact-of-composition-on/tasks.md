# Tasks: Predicting the Impact of Composition on the Density of Metallic Glasses

**Input**: Design documents from `/specs/001-predict-metallic-glass-density/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-461-predicting-the-impact-of-composition-on-/`) by executing: `mkdir -p code/data code/features code/models code/analysis data models reports tests/unit tests/contract tests/integration`

- [X] T002 Initialize Python 3.10+ project with `pyproject.toml`. Create `pyproject.toml` with:
 - `[build-system]` using `setuptools`
 - `[project]` with `name`, `version`, `dependencies` (pandas, numpy, scikit-learn, lightgbm, mendeleev, shap, matplotlib, seaborn, requests, pytest)
 - `[tool.setuptools.packages.find]`
 - `[project.scripts]` entry point `mg-density-predict = code.main:main`
 - **T002-PIN**: Explicitly pin `mendeleev` to a specific version (e.g., `mendeleev==1.0.0`) to ensure Verified Accuracy.

- [ ] T003 [P] Configure linting and formatting tools. Create `.ruff.toml` with `line-length = 88`, `target-version = "py310"`. Create `pyproject.toml` section `[tool.black]` with `line-length = 88`, `target-version = ['py310']`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup data directory structure (`data/`, `models/`, `reports/`) and `.gitignore` for artifacts (exclude `*.csv`, `*.pkl`, `*.png`, `*.html` except `metrics.json`).

- [X] T005 [P] Implement logging infrastructure. Create `code/utils/logger.py` with a `get_logger(name: str) -> logging.Logger` function that returns a configured `logging.Logger` instance with JSON formatting and a file handler writing to `logs/run.log`.

- [ ] T006 [P] Create schema validation utilities for `contracts/`. Implement `code/utils/schema_validator.py` with `load_schema(path: str) -> jsonschema.Draft7Validator` returning a validator instance for `contracts/dataset.schema.yaml`, `contracts/model_output.schema.yaml`, and `contracts/output.schema.yaml`.

- [X] T007 Create base constants module for periodic table references (`code/features/constants.py`) using `mendeleev` library to expose `get_atomic_mass`, `get_atomic_radius`, `get_electronegativity` functions.

- [X] T008 Configure environment configuration management. Create `code/config.py` with a `Config` dataclass containing `seed: int`, `data_dir: Path`, `model_dir: Path`, `report_dir: Path`. Implement `load_config()` to read from `.env` or `config.yaml`.

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Automatically download, parse, and clean metallic glass data from Zenodo/Materials Cloud, with a robust synthetic fallback for validation.

**Independent Test**: The pipeline can be fully tested by running the data script against target repositories and verifying `clean_data.csv` has ≥50 rows (or synthetic ≥100) with no missing density values.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T010 [P] [US1] Contract test for data schema in `tests/contract/test_dataset_schema.py`. Verify `clean_data.csv` matches `contracts/dataset.schema.yaml`.
- [ ] T011 [US1] Integration test for download fallback logic in `tests/integration/test_data_fallback.py`. **Must run after T012**. Mock network failures to verify fallback to synthetic generation. <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested -->

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement `code/data/download.py` to fetch from Zenodo (primary) and Materials Cloud (secondary) with exponential backoff (3 retries). Output `data/raw_data.csv`. <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->

- [ ] T014 [US1] Implement `code/data/preprocess.py` to normalize elemental symbols to IUPAC standards (1-2 chars). **Strategy**: Filter rows with missing density values. **Critical Logic**: If filtering reduces the row count to < 50, the system MUST immediately trigger 'Pipeline Validation Mode' (synthetic generation) as per FR-001. Output `data/clean_data.csv` (or `data/synthetic_data.csv` if fallback triggered).

- [ ] T015 [US1] Verify `data/clean_data.csv` (or `synthetic_data.csv`) has zero missing values in target column and valid numeric types for all elemental mass fractions. **Output**: Generate `data/validation_log.json` containing row counts, missing value stats, and source status.

- [ ] T014-IMPUTE [US1] (OPTIONAL) Implement `code/data/preprocess.py` alternative path for documented imputation of missing density values (e.g., KNN imputation) if the project team chooses to retain rows instead of filtering. **Must log** the imputation method used.

- [ ] T013 [US1] Implement `code/data/download.py` fallback logic: If T014 filtering results in < 50 rows, generate `data/synthetic_data.csv` (≥100 rows) with columns `composition` (dict), `density` (float). **Logic**: If real data exists (even if filtered), mimic 'dominant element' distribution from the *clean* real data; if not, use uniform distribution. Use linear mixing rule + Gaussian noise (σ=0.05). **Use fixed seed=42**.

- [~] T016 [US1] Add logging for data source selection and `E_DATA_INSUFFICIENT` warnings when switching to synthetic mode. **Log Format**: `LOG: Data source selected: {source} | Rows: {count} | Status: {status}`.

- [X] T017 [US1] Add unit tests for `code/data/download.py` mocking network failures to verify fallback to synthetic generation.

**Checkpoint**: User Story 1 is fully functional; `data/clean_data.csv` or `data/synthetic_data.csv` is ready for feature engineering

---

## Phase 4: User Story 2 - Compositional Feature Engineering and Model Training (Priority: P2)

**Goal**: Compute atomic-level descriptors from composition and train a Gradient Boosting Regressor on residual density.

**Independent Test**: Verify model object is saved, top 3 descriptors contribute >5% to R² improvement, and model trains on CPU within 600s.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for feature schema in `tests/contract/test_feature_schema.py`.
- [X] T019 [P] [US2] Unit test for atomic fraction conversion and radius-based descriptor logic in `tests/unit/test_engineering.py`.

### Implementation for User Story 2

- [X] T024-DEV-DRAFT [US2] Document and validate the Group K-Fold deviation. Create `docs/deviations/group_kfold_rationale.md` explaining the scientific rationale (data leakage prevention) and generating a formal "Kickback Request" JSON object to update FR-003 in the Spec. **Output**: `docs/deviations/group_kfold_rationale.md`. <!-- FAILED: unspecified -->

- [X] T024-DEV-EXEC [US2] Submit the Kickback Request. Create a formal request artifact (e.g., `docs/kickback_requests/FR003_group_kfold.json`) and log the request for review. **Depends on**: T024-DEV-DRAFT.

- [X] T024 [US2] Implement `code/models/train.py` to split data using **Group K-Fold** (k=5). **Deviation**: Overrides Spec FR-003 (Stratified K-Fold) per Plan.md to prevent data leakage. **Grouping Logic**: Derive `dominant_element` column (element with highest mass fraction) and use it as the `groups` array. **Note**: This implementation is pending formal Spec approval via T024-DEV-EXEC. **Depends on**: T024-DEV-DRAFT.

- [X] T022 [US2] Implement `code/features/engineering.py` to convert mass fractions to atomic fractions specifically for radius-based calculations to mitigate collinearity. **Logic**: `atomic_fraction_i = (mass_fraction_i / atomic_mass_i) / sum(mass_fraction_j / atomic_mass_j)`. **Must run before T020/T021**. **Input**: `clean_data.csv`. **Output**: Updated DataFrame with atomic fractions.

- [X] T020 [US2] Implement `code/features/engineering.py` to compute 5 specific descriptors required by FR-002: 1) Mean Atomic Mass, 2) Mean Atomic Radius, 3) Electronegativity Variance, 4) Atomic Radius Mismatch, 5) Packing Efficiency Proxy. **Input**: `clean_data.csv` (with atomic fractions from T022). **Output**: DataFrame with new columns.

- [~] T021 [US2] Implement `code/features/engineering.py` to compute Packing Efficiency Proxy: `PE = 1 - (σ_r / r_mean)^2 * (1 - 0.5 * (Δr/r_mean)^2)`. **Guard Clause**: If σ_r = 0, set PE = 1.0. **Output**: Add `packing_efficiency` column to DataFrame and save to `data/clean_data.csv`. (Note: This is the specific implementation of the 5th descriptor listed in T020).

- [~] T023 [US2] Implement `code/features/engineering.py` to calculate baseline density (Linear Mixing Rule: `ρ_baseline = Σ(w_i × ρ_element_i)`) and derive residual target (`ρ_residual = ρ_actual - ρ_baseline`). Save to `data/clean_data.csv`. <!-- FAILED: unspecified -->

- [~] T025 [US2] Implement `code/models/train.py` to train LightGBM Gradient Boosting Regressor on `ρ_residual` (CPU-only). Save model to `models/model.pkl`. Log MAE/R² on test set. <!-- FAILED: unspecified -->

- [ ] T025-ALT-SPEC [US2] Implement `code/models/train.py` to train a **Linear Mixing Rule Baseline** (Linear Regression on raw mass fractions to predict `ρ_baseline` directly) to satisfy SC-003. Calculate its MAE. **Purpose**: Compare against the main model per Spec SC-003 (Model vs Linear Mixing Rule).

- [ ] T025-ALT [US2] Implement `code/models/train.py` to train a **Mass-Only Model** (Linear Regression on `mean_atomic_mass`) on `ρ_residual`. Calculate its MAE. **Purpose**: Compare against the main model per Plan.md Complexity Tracking as an *additional* comparison (Model vs Mass-Only).

- [ ] T026 [US2] Save metrics (Model MAE, Linear Mixing Rule Baseline MAE, Mass-Only Baseline MAE, R²) to `reports/metrics.json` (SSoT).

- [ ] T026-STAT [US2] Implement `code/analysis/statistics.py` to perform a **paired t-test** comparing Model MAE vs Linear Mixing Rule Baseline MAE on residuals (per SC-003). Calculate p-value. If p < 0.05, log statistical significance. Output to `reports/statistics.json`.

- [~] T027 [US2] Add unit tests verifying atomic fraction conversion logic and packing efficiency guard clause.

**Checkpoint**: User Story 2 complete; `models/model.pkl` trained on residuals with Group K-Fold; Baselines computed

---

## Phase 5: User Story 3 - Interpretability and Validation Reporting (Priority: P3)

**Goal**: Generate report visualizing predictions, SHAP values, and sensitivity analysis, with specific focus on radius mismatch if MAE > 0.1.

**Independent Test**: Report contains scatter plot, feature importance bar chart, and sensitivity analysis table.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [P] [US3] Contract test for report schema in `tests/contract/test_report_schema.py`.
- [ ] T029 [P] [US3] Integration test for report generation with mock model in `tests/integration/test_report_generation.py`. <!-- FAILED: unspecified -->

### Implementation for User Story 3

- [ ] T030 [P] [US3] Implement `code/analysis/report.py` to generate scatter plot (Predicted vs Actual) with R² in title. Save to `reports/predicted_vs_actual.png`.

- [ ] T031 [US3] Implement `code/analysis/report.py` to perform SHAP analysis and generate summary plot ranking features (explicitly comparing Mean Atomic Mass vs Radius Mismatch). Save to `reports/shap_summary.png`.

- [ ] T032 [US3] Implement `code/analysis/report.py` to run sensitivity analysis (add Gaussian noise with varying small magnitudes to target) and log MAE variance. Output table to `reports/sensitivity_analysis.json`.

- [ ] T033 [US3] Implement `code/analysis/report.py` conditional logic: If MAE > 0.1, generate Partial Dependence Plots for radius mismatch. **Output**: `reports/pdp_radius_mismatch.png`. Include explicit variance analysis as a distinct finding.

- [ ] T034 [US3] Implement `code/analysis/report.py` to compile `reports/analysis_report.html` and `reports/metrics.json` (SSoT).

- [ ] T035 [US3] Add unit tests for sensitivity analysis logic and MAE > 0.1 conditional report generation.

**Checkpoint**: All user stories complete; comprehensive report generated with interpretability data

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036-README [P] Documentation updates. Add "Usage" section to `README.md` with example CLI commands (`python -m code.main`).
- [ ] T036-API [P] Documentation updates. Document CLI arguments and environment variables in `docs/api.md`.
- [ ] T037-LINT [P] Code cleanup. Remove unused imports, enforce line length < 88, fix type hints.
- [ ] T037-FORMAT [P] Code cleanup. Run `black` and `ruff format` on all Python files.
- [ ] T038-OPT [P] Performance optimization. Optimize `code/features/engineering.py` vectorization to ensure pipeline completes ≤ 2 hours.
- [ ] T039-DOWNLOAD [P] Unit tests for `code/data/download.py` (network retries, fallback logic).
- [ ] T039-ENG [P] Unit tests for `code/features/engineering.py` (atomic fraction conversion, descriptor formulas).
- [ ] T039-TRAIN [P] Unit tests for `code/models/train.py` (Group K-Fold split, model training).
- [ ] T039-REPORT [P] Unit tests for `code/analysis/report.py` (plot generation, sensitivity analysis).
- [ ] T040 [P] Run `python -m code.main --validate` and verify exit code 0 and `state/` hash match. Verify all artifacts are reproducible.

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
- **User Story 2 (P2)**: Depends on US1 (requires `clean_data.csv`)
- **User Story 3 (P3)**: Depends on US2 (requires `model.pkl` and test set metrics)

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
- All tests for a user story marked [P] can run in parallel (except T011 which depends on T012)
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data schema in tests/contract/test_dataset_schema.py"
# T011 (Integration test) is NOT parallel; it depends on T012.

# Launch all models for User Story 1 together:
Task: "Implement code/data/download.py to fetch from Zenodo (primary) and Materials Cloud (secondary)"
Task: "Implement code/data/preprocess.py to normalize elemental symbols and handle missing density values"
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
- **Plan Deviation**: T024 implements Group K-Fold instead of Stratified K-Fold (FR-003) per Plan.md. T024-DEV-DRAFT documents this, and T024-DEV-EXEC submits the Kickback Request.
- **Baseline Deviation**: T025-ALT implements Mass-Only Model baseline per Plan.md Complexity Tracking (as an *additional* comparison), while T025-ALT-SPEC implements the Spec-defined Linear Mixing Rule baseline for SC-003.