# Tasks: Predicting Yield Strength of BCC Alloys

**Input**: Design documents from `/specs/001-bcc-yield-strength/`
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

- [ ] T001 Create project structure: `mkdir -p data/raw data/processed data/logs code tests reports state`
- [ ] T002 Initialize Python 3.11 project with scikit-learn, pandas, numpy, periodictable, skbio, scipy, requests, pymatgen dependencies
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on plan.md structure):

- [ ] T004 Setup `data/raw`, `data/processed`, `data/logs` directories with `.gitkeep` and checksum scripts
- [X] T007 [P] Define `AlloyRecord` and `CompositionalDescriptor` data classes in `code/models.py`; define `ilr_transformed_features` as a list of floats (schema definition only)
- [X] T008 Configure `requirements.txt` with pinned versions for reproducibility, explicitly including `pymatgen`
- [X] T009 [P] Setup environment configuration management for local vs. CI paths

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Curation and BCC Filtering (Priority: P1) 🎯 MVP

**Goal**: Obtain a clean, filtered dataset containing only BCC alloys with valid yield strength and complete compositions.

**Independent Test**: The system can be tested by executing the data ingestion pipeline and verifying that the output CSV contains zero entries with missing yield strength, zero entries with non-BCC crystal structures, and that all composition rows sum to 1.0 (atomic fraction).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010_test [P] [US1] Unit test `test_bcc_filtering` in `tests/unit/test_data_ingestion.py`: Filter a mock dataframe for BCC phase; assert count matches expected and non-BCC are removed.
- [X] T011_test [P] [US1] Unit test `test_composition_normalization` in `tests/unit/test_data_ingestion.py`: Normalize a mock composition row; assert sum is normalized within a specified tolerance.
- [X] T012_test [P] [US1] Unit test `test_non_numeric_yield` in `tests/unit/test_data_ingestion.py`: Pass a dataframe with non-numeric yield; assert row is excluded and logged.

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/data_ingestion.py` to download MPEA database using canonical DOI resolver (e.g., `doi.org/10.1038/s41597-020-00768-9`) and save to `data/raw/mpea_raw.xlsx`; verify SHA-256 checksum
- [X] T014 [US1] Implement filtering logic in `code/data_ingestion.py` to exclude non-BCC phases and null yield strength
- [X] T015 [US1] Implement composition normalization in `code/data_ingestion.py` to ensure rows sum to 1.0 with logging
- [X] T016 [US1] [MANDATORY] Implement logic to average duplicate compositions or select median, logging the method used (US-4 requirement); MUST be executed
- [X] T017 [US1] [MANDATORY] Implement data scarcity check: Halt with exit code 1 and "DATA_SCARCITY: Insufficient BCC alloys (N < 80)" if N < 80 (FR-004 requirement); MUST be executed
- [X] T018 [US1] Save filtered dataset to `data/processed/bcc_filtered.csv` and rejected entries to `data/logs/rejected_entries.log`
- [X] T045 [P] [US1] Add explicit error handling in `code/data_ingestion.py` to raise a clear exception if the MPEA DOI resolver fails or returns an empty dataset, ensuring no silent fallback to synthetic data (Constitution Principle III).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Compositional Feature Engineering (Priority: P2)

**Goal**: Generate derived compositional descriptors and ILR-transformed features for regression modeling.

**Independent Test**: The system can be tested by running the feature engineering module on a fixed reference alloy (Mo-25Nb-25Ta-25W) and verifying that the calculated descriptors (δ, VEC, mixing entropy, mixing enthalpy, electronegativity difference) match the manually calculated reference values within a relative tolerance of ≤ 1e-6.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019_test [P] [US2] Unit test `test_atomic_radius_mismatch` in `tests/unit/test_feature_engineering.py`: Calculate δ for a mock alloy; assert value matches expected within 1e-6.
- [X] T020_test [P] [US2] Unit test `test_vec_and_entropy` in `tests/unit/test_feature_engineering.py`: Calculate VEC and mixing entropy for a mock alloy; assert values match expected within 1e-6.
- [X] T021_test [P] [US2] Unit test `test_ilr_transformation` in `tests/unit/test_feature_engineering.py`: Apply ILR to a mock composition; assert output dimensions and sum of squares properties.
- [X] T022_test [P] [US2] Unit test `test_missing_element` in `tests/unit/test_feature_engineering.py`: Pass a composition with a missing element; assert error is logged and row is skipped.
- [X] T050 [P] [US2] [MANDATORY] Add a unit test in `tests/unit/test_feature_engineering.py` to verify that the `Residualization` step in T029b correctly removes the linear correlation between scalar descriptors and ILR coordinates, ensuring the residuals have near-zero correlation. (Source: plan.md Complexity Tracking)

### Implementation for User Story 2

- [X] T023 [US2] Implement `code/feature_engineering.py` to load periodic table data (atomic radius, electronegativity, valence)
- [X] T025a [US2] Download `NIST_JANAF.json` containing binary interaction parameters (Ω_ij) from the NIST-JANAF public repository (or a verified mirror) to `data/raw/thermo_params.json`; verify SHA-256 checksum. **MUST source parameters from 'NIST-JANAF' or a documented thermodynamic database distinct from the MPEA yield strength source** (FR-003). If the file is small, hardcode the known values in a comment linking to the source.
- [X] T024 [US2] Implement calculation of scalar descriptors: δ, VEC, mixing entropy, mixing enthalpy (using sourced Ω_ij from T025a), electronegativity difference
- [X] T023b_test [US2] [TEST] [MANDATORY] Embed and execute automated assertion for fixed reference alloy (Mo-25Nb-25Ta-25W) verifying all calculated descriptors match manual values within tolerance ≤ 1e-6; **calculate expected values dynamically from the periodic table data loaded in T023**; **fail pipeline with exit code 1 if tolerance exceeded**; **runs AFTER T023**; **runs AFTER T024**. **Expected Values**: Must be calculated dynamically, not hardcoded.
- [X] T026 [US2] Implement Isometric Log-Ratio (ILR) transformation on compositional features using `skbio`
- [X] T027a [US2] Implement concatenation of ILR-transformed features and scalar descriptors into a single combined feature matrix (runs AFTER T026, T024)
- [X] T027c [US2] Populate `ilr_transformed_features` in the `CompositionalDescriptor` data class with the output from T026
- [X] T028 [US2] Implement pre-analysis independence check to detect circular validation between thermodynamic parameters and yield strength (runs BEFORE T029)
- [X] T029a [US2] [DEPENDS ON T028] Implement Pre-Filter Dimensionality Reduction (PCA) on the combined feature matrix. **Target variance threshold: (95% of variance retained)**. Output: `data/processed/features_pca.csv`. (Source: plan.md Complexity Tracking)
- [X] T029b [US2] [DEPENDS ON T029a] Implement Residualization: Regress scalar descriptors against ILR coordinates using `LinearRegression` and extract residuals to mitigate multicollinearity. Output: `data/processed/features_residualized.csv`. (Source: plan.md Complexity Tracking)
- [X] T029c [US2] [DEPENDS ON T029b] Apply L1 regularization or Recursive Feature Elimination (RFE) on the **residualized features (from T029b)** to select the most predictive subset (FR-003.2). Output: `data/processed/features_selected.csv`.
- [X] T032 [US2] Save engineered dataset to `data/processed/features_engineered.csv` with full traceability log
- [X] T046 [P] [US2] Add a validation step in `code/feature_engineering.py` to verify that the `thermo_params.json` file loaded in T025a contains valid float entries for all required binary pairs before proceeding to T024.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Regression Modeling and Validation (Priority: P3)

**Goal**: Train models, evaluate performance, and generate confidence intervals using 80/20 split and 5-fold CV.

**Independent Test**: The system can be tested by running the training script with a fixed random seed and verifying that the reported R², MAE, and RMSE values match expected values within a predefined tolerance threshold, and that the bootstrapped confidence intervals are generated using the specified method.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T033_test [P] [US3] Unit test for stratified split logic in `tests/unit/test_modeling.py`
- [X] T034_test [P] [US3] Unit test for 5-fold cross-validation implementation in `tests/unit/test_modeling.py`
- [X] T035_test [P] [US3] Unit test for bootstrap confidence interval calculation in `tests/unit/test_modeling.py`

### Implementation for User Story 3

- [X] T033_impl [US3] Implement `code/modeling.py` to perform a **stratified train-test split based on multiple quantile bins of the target variable (yield strength)**; save `train_split` and `test_split` artifacts
- [X] T049 [P] [US3] [MANDATORY] Implement explicit validation in `code/modeling.py` to confirm that the stratified split bins contain a minimum of 5 samples each before proceeding to CV; if any bin is under-represented, log a warning and adjust binning strategy or halt with a specific "STRATIFICATION_FAILURE" error code. **Note: If N < 80, defer to FR-004 hard halt (exit code 1) per spec.**
- [X] T034_impl [US3] Implement Random Forest, Gradient Boosting, and Ridge Regression training using **Repeated Stratified K-Fold** with a fixed random seed on the `train_split` from T033_impl; **generate base CV scores required for the subsequent bootstrap resampling step (T036b)**
- [X] T035 [US3] Generate a distribution of RAW 5-fold R² scores (list of floats, not aggregated) from the Repeated 5-fold CV repeats (output of T034_impl)
- [X] T036b [US3] Perform **multiple bootstrap resamples** on the RAW k-fold CV scores (from T035) using the percentile method to generate a distribution of **confidence intervals**; **explicitly output the 'bootstrap resampled datasets' (prediction arrays) to `data/processed/bootstrap_resamples.pkl` for T038a consumption**.
- [X] T041_calc [US3] [CALCULATION ONLY] Calculate the standard deviation of feature importance ranks across multiple bootstrap resamples.; write the raw float value to `data/logs/sc003_stability_metric.log`; **DO NOT evaluate threshold or halt pipeline**
- [X] T041_gate [US3] [GATE ENFORCEMENT] **RUN BEFORE T038a and T038b**. Read `data/logs/sc003_stability_metric.log`; if value >= 2.0, **HALT PIPELINE with exit code 1** and error message "SC-003 FAILURE: Feature importance stability metric (std_dev) >= 2.0"; otherwise, write "STABLE" to `reports/model_comparison_report.json` under `sc003_status`. **Enforces SC-003 as a verifiable gate.**
- [X] T038a [US3] Implement permutation importance testing: Run on EACH of the bootstrap resampled datasets (from T036b) to generate multiple sets of feature importance ranks
- [X] T038b [US3] Generate final report comparing R², MAE, RMSE for all models and identifying the best performer; **read the existing report file (if any) and append/merge the `sc003_status` field from T041_gate**; save to `reports/model_comparison_report.json`
- [X] T051 [US3] [MANDATORY] Implement a "Null Model" baseline in `code/modeling.py` that predicts the mean yield strength of the training set for every test sample; calculate its R² (expected to be low) and MAE to serve as the absolute floor for SC-001 comparison. **Include a t-test or F-test to verify if the best model's R² is significantly better than the null model's R².**
- [X] T052 [US3] [MANDATORY] Implement a wrapper in `code/main.py` to capture the total pipeline execution time (from start of T013 to end of T051); log the total time in seconds to `data/logs/pipeline_runtime.log` and include it in `reports/model_comparison_report.json` to satisfy SC-004.
- [X] T039 [US3] Implement `code/traceability.py` to extract metrics from logs and update `state/projects/PROJ-525-predicting-the-yield-strength-of-bcc-all.yaml`
- [X] T047 [P] [US3] Add a pre-flight check in `code/modeling.py` to verify that the `train_split` and `test_split` artifacts from T033_impl contain at least 1 sample per class/bin before attempting CV.
- [X] T048 [P] [US3] Implement a fallback logging mechanism in `code/traceability.py` to capture the exact SHA-256 hash of the input `features_engineered.csv` used for the final model run, ensuring full provenance in `state/projects/PROJ-525...yaml`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T040 [P] Documentation updates in `README.md` and `quickstart.md`
- [X] T041 [P] Code cleanup and refactoring for readability
- [X] T042 [P] Performance optimization to ensure full pipeline runs < 6 hours on CI
- [X] T043 [P] Additional unit tests for edge cases (log domain errors, missing elements)
- [X] T044 [P] Run quickstart.md validation to ensure end-to-end reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 feature output

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

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for BCC filtering logic in tests/unit/test_data_ingestion.py"
Task: "Unit test for composition normalization (sum=1.0) in tests/unit/test_data_ingestion.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data_ingestion.py to download MPEA database"
Task: "Implement filtering logic in code/data_ingestion.py"
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
- **Note on T029**: T029 is now split into T029a (PCA), T029b (Residualization), and T029c (L1/RFE) to explicitly define the order of operations and align with plan.md Complexity Tracking. Explicit 'depends on' markers added.
- **Note on T017**: This task enforces the hard gate required by FR-004. If the plan's "conditional" analysis for N < 80 is required, it must be implemented as a separate branch or the spec amended.
- **Note on T041**: Split into T041_calc (pure calculation) and T041_gate (enforcement) to separate metric generation from success criterion reporting. T041_gate now includes the logic to enforce the threshold and halt the pipeline if SC-003 is not met. T041_gate runs BEFORE T038a and T038b.
- **Note on T049**: Addresses the specific concern that stratified bins may be under-represented in small N regimes, ensuring robust CV splits. Note: FR-004 hard halt takes precedence if N < 80.
- **Note on T050**: Addresses the specific concern that Residualization must be verified to actually remove linear correlation, ensuring the geometric independence claim holds.
- **Note on T051**: Addresses the specific concern that SC-001 (statistical significance vs null) requires a concrete Null Model baseline to compare against, including a t-test for significance.
- **Note on T023b_test**: Removed hardcoded placeholder values. Expected values must be calculated dynamically from the periodic table data loaded in T023.
- **Note on T029a**: Updated to specify a concrete variance threshold (0.95) to avoid ambiguity.
- **Note on T052**: Added to explicitly capture and report total pipeline runtime for SC-004.