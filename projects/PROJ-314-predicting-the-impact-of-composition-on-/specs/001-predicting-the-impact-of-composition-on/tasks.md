---
description: "Task list template for feature implementation"
---

# Tasks: Predicting the Impact of Composition on the Weibull Modulus of Ceramics

**Input**: Design documents from `/specs/001-predict-weibull-modulus/`
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

<!--
 ============================================================================
 IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

 The /speckit-tasks command MUST replace these with actual tasks based on:
 - User stories from spec.md (with their priorities P1, P2, P3...)
 - Feature requirements from plan.md
 - Entities from data-model.md
 - Endpoints from contracts/

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure, including generation of all Phase 1 documentation artifacts required by the plan.

- [X] T001 Create project structure per implementation plan (projects/PROJ-314-predicting-the-impact-of-composition-on-)
- [X] T002 Initialize Python 3.11 project with requirements.txt (pandas, scikit-learn, shap, chemparse, requests, pyyaml, scipy, pymatgen, arxiv, pdfplumber)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools
- [X] T016a [P] Generate `quickstart.md` in `specs/001-predict-weibull-modulus/`: Document step-by-step setup, data fetch, and pipeline execution instructions. Must include sections: 1. Prerequisites & Install, 2. Data Fetch (MP, NIST, arXiv), 3. Running the Pipeline, 4. Verifying Outputs. Must be generated before T045 validation. (Addresses Plan Phase 1, Task 1.5 & Coverage Gaps)
- [X] T016b [P] Generate `docs/data_gap_protocol.md`: Document the exact steps for the Data Gap Protocol, including the schema for `data/reports/data_availability_report.json` and the halting logic. Must be generated before T047 update. (Addresses Plan Phase 1, Task 1.5 & Coverage Gaps)
- [X] T016c-1 [P] Define `CeramicEntry` and `DescriptorSet` schemas in `code/contracts/schemas.py` using Pydantic.
- [X] T016c-2 [P] Export schemas to YAML files `ceramic_entry.schema.yaml` and `model_result.schema.yaml` in `code/contracts/`.
- [X] T016c-3 [P] Generate `data-model.md` in `specs/001-predict-weibull-modulus/`: Document the `CeramicEntry` and `DescriptorSet` entities, their relationships, and validation rules. Must include YAML schema examples and field type definitions. (Addresses Plan Phase 1, Task 1.5)
- [X] T006 [P] Create base `CeramicEntry` dataclass in `code/__init__.py` (Dependency: T016c-1 must be complete for semantic definition)
- [X] T007 [P] Create base `DescriptorSet` dataclass in `code/__init__.py` (Dependency: T016c-1 must be complete for semantic definition)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T012a [P] Generate contract schema `ceramic_entry.schema.yaml` in `code/contracts/`: Use `pydantic` to define the `CeramicEntry` model and export to YAML. Include all fields: `composition`, `weibull_modulus`, `sample_count`, `is_range_flag`, `range_original`, `primary_anion_cation_group`, `sintering_temp`, `is_imputed`, `mean_atomic_radius`, `electronegativity_std`, `valence_electron_concentration`. (Addresses Plan Phase 1, Task 1.5)
- [X] T012b [P] Generate contract schema `model_result.schema.yaml` in `code/contracts/`: Use `pydantic` to define the `ModelResult` model and export to YAML. Include all fields: `model_type`, `mae`, `r_squared`, `feature_importance_ranking`, `cv_stability_scores`. (Addresses Plan Phase 1, Task 1.5)
- [X] T022 [P] Create `code/physics_mappings.py` with dictionary mapping descriptors to physical mechanisms (e.g., "cation_size_variance" -> "Grain boundary stability") to support US3 (Moved to Phase 2 to ensure availability before US3 work)
- [X] T004 Setup `data/raw/`, `data/processed/`, and `data/artifacts/` directories
- [X] T005 [P] Implement `code/hash_artifacts.py` for versioning and checksumming (Constitution Principle V)
- [X] T008 [P] Setup `code/ingestion.py` skeleton file structure
- [X] T009 [P] Implement URL validation logic in `code/ingestion.py`
- [X] T009b [P] Implement `validate_source_citations()` in `code/ingestion.py`: Validate source URLs/DOIs against primary sources (Constitution Principle II) by checking title overlap >= 0.7 and verifying reachability; log failures to `logs/citation_validation.log`. **Verification**: Ensure `logs/citation_validation.log` is created and populated during the first validation run. (Addresses Plan Phase 0, Task 0.3)
- [X] T010 [P] Configure logging infrastructure in `code/__init__.py` (Ensures `logs/` directory exists for T009b)
- [X] T010b [P] Verify `logs/citation_validation.log` creation: Execute `python code/ingestion.py --validate-dummy` with `dummy_urls=['https://example.com', ' Temporary failure in name resolution)"))]']`. Assert that `logs/citation_validation.log` exists and contains at least one entry with format `INFO: Citation validation for {url}: {status}` where status is not empty. (Addresses T009b verification gap)
- [X] T011 [P] Setup environment configuration management: Create `.env.example`, implement `load_env()` in `code/__init__.py`, and add unit test `tests/test_config.py::test_env_loading`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Descriptor Computation (Priority: P1) 🎯 MVP

**Goal**: Ingest raw ceramic data, clean it, and compute elemental descriptors to produce a feature-rich dataset.

**Independent Test**: Run the pipeline on a sample of known entries.; verify output CSV contains `weibull_modulus` and at least 10 computed descriptors with no missing values for primary predictors.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T013 [P] [US1] Unit test for `chemparse` composition parsing in `tests/test_descriptors.py`
- [X] T014 [P] [US1] Unit test for imputation logic (group vs. global median) in `tests/test_ingestion.py`
- [X] T015 [P] [US1] Integration test for full ingestion pipeline on a small sample in `tests/integration/test_ingestion.py`

### Implementation for User Story 1

- [X] T018c [US1] Implement `fetch_materials_project_data()` in `code/ingestion.py`: Use `pymatgen` to fetch ceramic property data (stoichiometry, Weibull modulus if available) from Materials Project API (` Name or service not known)"))]). Query for entries with 'ceramic' in description and 'weibull' in properties. If API returns no Weibull data, validate `data/raw/curated_literature.csv` (if exists) against its DOI/URL (Constitution Principle II) and load it as fallback. Output raw JSON/CSV to `data/raw/materials_project_raw.json`. (Addresses FR-001 coverage gap)
- [X] T018d [US1] Implement `fetch_nist_data()` in `code/ingestion.py`: Fetch NIST Ceramic Data from verified URL `. If fetch fails, validate `data/raw/curated_literature.csv` against its DOI/URL (Constitution Principle II) and load it as fallback. Output raw JSON/CSV to `data/raw/nist_raw.json`. (Addresses FR-001 coverage gap)
- [X] T018e [US1] Implement `fetch_arxiv_data()` in `code/ingestion.py`: Use `arxiv` library to search for `all:ceramic AND all:weibull` (limit 50). Use `pdfplumber` to extract tables from the top 50 PDFs, looking for columns 'Composition', 'Weibull Modulus', 'N'. Match extracted data to the paper's DOI/title for verification (Constitution Principle II). If no table found, skip row and log warning. Output raw JSON/CSV to `data/raw/arxiv_raw.json`. (Addresses FR-001 coverage gap)
- [X] T018a [US1] Implement `clean_data()` in `code/ingestion.py`:
 1. Filter for `N >= 30` by explicitly extracting sample count from fields named 'N', 'sample_size', or 'n' (FR-003).
 2. Handle range values: Extract midpoint, set `is_range_flag`, store `range_original` (to be processed by T018b).
 3. Impute missing processing params (group median -> global median).
 4. Handle non-stoichiometric phases: **Exclude** if the specific class has < 5 samples; otherwise, impute using global median.
 5. **Derive `primary_anion_cation_group`** directly from stoichiometry (parsing the formula string to identify primary anion/cation groups) - this step is independent of T019's elemental descriptors.
 6. **Output Schema**: Ensure output CSV contains columns: `composition`, `weibull_modulus`, `sample_count`, `is_range_flag`, `range_original`, `primary_anion_cation_group` (derived grouping feature, not elemental descriptor), `sintering_temp`, `is_imputed`. (Descriptors like `mean_atomic_radius` are populated by T019).
 **Dependency**: T018c, T018d, T018e must be complete to provide the raw data inputs.
- [X] T017 [US1] Implement `validate_data_gap()` in `code/ingestion.py`:
 1. Check total valid entries (N) after fetching (T018c/d/e) and applying per-entry filters (T018a).
 2. **HALT**: If N < 30, call `generate_data_availability_report()` (T017b) to create `data/reports/data_availability_report.json`, log `INFO: PROJECT_HALTED: Insufficient data (N={N})`, and exit with code 1.
 3. If N >= 30, proceed to cleaning.
 **Dependency**: T018c, T018d, T018e, T018a must be complete.
- [X] T017b [US1] Implement `generate_data_availability_report()` in `code/ingestion.py`: Generate `data/reports/data_availability_report.json` with fields `total_sources` (actual count of fetched sources, not hardcoded), `valid_entries`, `reason_code`, `timestamp` when N < 30 (Required for Data Gap Protocol). **Output**: File must be written before halting.
- [X] T017c [US1] **Execute & Verify Data Gap Report**: 1. Create `data/raw/test_n29.csv` with exactly 29 rows where each row has `sample_count >= 30` (e.g., 30) to ensure total N=29. Schema: `composition` (str), `weibull_modulus` (float), `sample_count` (int), `sintering_temp` (float), `primary_anion_cation_group` (str). Sample Row: `{"composition": "Al2O3", "weibull_modulus": 10.5, "sample_count": 30, "sintering_temp": 1600.0, "primary_anion_cation_group": "O-Al"}`. 2. Run `python code/ingestion.py --input data/raw/test_n29.csv --force-gap-check`. 3. Verify that `data/reports/data_availability_report.json` is generated with correct dynamic fields (`total_sources`, `valid_entries`) and that the process halts with exit code 1. (Addresses Executability & Ordering Gaps)
- [X] T018b [US1] Implement `compute_range_uncertainty()` in `code/descriptors.py`:
 1. Extract midpoint from `range_original` if `is_range_flag` is true.
 2. Calculate `range_uncertainty` as (max - min) / 2.
 3. Add `range_uncertainty` column to the dataset. (Addresses Plan Phase 1, Task 1.4)
- [X] T019 [US1] Implement `compute_descriptors()` in `code/descriptors.py`:
 1. Calculate mean atomic radius and electronegativity std.
 2. Calculate Cation Size Variance.
 3. **Explicitly Calculate Valence Electron Concentration (VEC)** as: `sum(valence electrons of all atoms) / total number of atoms in formula unit` (FR-002).
- [X] T020 [US1] Implement `validate_no_missing_primary_predictors()` in `code/ingestion.py` that raises `ValueError` with message "Missing values in primary predictors: {col_names}" if any primary predictor column (mean_atomic_radius, electronegativity_std, valence_electron_concentration) contains NaN, and add unit test `tests/test_ingestion.py::test_validate_no_missing`.
- [X] T021 [US1] Implement logging for data exclusion reasons in `code/ingestion.py`: Log format `INFO: Excluded row {row_index} due to {reason}` where `{row_index}` is the pandas index and `{reason}` is one of: 'N<30', 'missing_stoichiometry', 'non_stoichiometric_phase'. Log to `logs/ingestion.log`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Predictive Modeling and Cross-Validation (Priority: P2)

**Goal**: Train Random Forest and Gradient Boosting models with strict cross-validation to predict Weibull modulus.

**Independent Test**: Execute training on a subset; verify JSON output contains MAE, R², and stratified split report confirming distribution match.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US2] Unit test for stratified splitting logic in `tests/test_modeling.py`
- [X] T024 [P] [US2] Unit test for baseline (global mean) predictor in `tests/test_modeling.py`
- [X] T025 [P] [US2] Implement integration test `tests/integration/test_modeling.py::test_5fold_cv_stratified_split` to verify the 5-fold CV workflow and **generate `data/results/cv_split_report.json`** containing stratification distribution metrics.

### Implementation for User Story 2

- [X] T026 [US2] Implement `prepare_splits()` in `code/modeling.py`: Stratified split based on `primary_anion_cation_group` (derived from US1 output); switch to hold-out if 30 <= N < 50 (FR-005, SC-004). **Dependency**: Requires T018a completion.
- [X] T027 [US2] Implement `train_models()` in `code/modeling.py`: Train RF and GBM with **limited hyperparameter search (max 50 combinations)** to fit 6h runtime (FR-004)
- [X] T027b [US2] **Save Best Model**: After T027, save the best performing model (lowest CV MAE) to `data/models/best_model.pkl` and log its hash. **Dependency**: T027 must complete.
- [X] T028b [US2] Implement `run_baseline_predictor()` in `code/modeling.py`: Create a simple model that predicts the global mean Weibull modulus for all test samples. Calculate and **save its MAE to `data/results/baseline_metrics.json`** (key: `baseline_mae`). (Addresses Plan Phase 2, Task 2.3)
- [X] T028 [US2] Implement `evaluate_models()` in `code/modeling.py`: Calculate MAE, R², and compare against global mean baseline (SC-001). **Output**: Save metrics to `data/results/model_metrics.json`, explicitly including keys `best_model_mae` and `best_model_type`.
- [X] T029 [US2] Implement `run_permutation_test()` in `code/modeling.py`: Perform a permutation test (**1000 iterations**) to determine statistical significance (p < 0.05) of the model's MAE improvement over baseline. **Logic**: Flag as "Not Statistically Significant" if p >= 0.05 **OR** if Model MAE >= 90% of Baseline MAE (Combined Check for SC-001). Update `data/results/model_metrics.json` with `is_significant` boolean. (Restored to satisfy SC-001 statistical significance requirement).
- [X] T030 [US2] Implement `check_leakage()` in `code/diagnostics.py`:
 1. Select the **best model** from T027/T028 (lowest validation MAE). Load from `data/models/best_model.pkl` (verify hash matches T027b log).
 2. **Retrieve Logic**: Load `data/results/model_metrics.json` to get `best_model_mae`. Load `data/results/baseline_metrics.json` to get `baseline_mae`.
 3. Re-run the best model **without** the `primary_anion_cation_group` feature to get `new_mae_without_group`.
 4. **Leakage Logic (FR-005.5)**: Calculate performance drop = (best_model_mae - new_mae_without_group) / best_model_mae.
 - If performance drop **<= 10%** (small drop): Flag **"Potential Leakage"** (The group variable was the main predictor, descriptors failed to capture signal).
 - If performance drop **> 10%** (significant drop): Flag **"Descriptors Sufficient"**.
 5. **Mandatory Output**: Write the sufficiency conclusion and the calculated drop percentage to `data/results/leakage_report.json` (FR-005.5).
 **Dependency**: T028, T028b, and T027b must be complete to provide the metric files and model artifact.
- [X] T031 [US2] Generate `data/results/model_metrics.json` with all scores and stratification reports
- [X] T032 [US2] Implement `filter_rare_classes()` in `code/modeling.py` to drop classes with < 5 samples before splitting, and verify via `tests/test_modeling.py::test_rare_class_exclusion`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance and Mechanistic Interpretation (Priority: P3)

**Goal**: Extract SHAP values, rank features, and interpret results against fracture mechanics principles.

**Independent Test**: Run analysis on trained model; verify output lists top 5 descriptors, includes correlation matrix, and flags collinearity.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T033 [P] [US3] Unit test for VIF calculation in `tests/test_diagnostics.py`
- [X] T034 [P] [US3] Unit test for SHAP value aggregation in `tests/test_report.py`
- [X] T035 [P] [US3] Integration test for full interpretability pipeline in `tests/integration/test_interpretability.py`

### Implementation for User Story 3

- [X] T036 [US3] Implement `calculate_shap()` in `code/diagnostics.py`: Generate SHAP values for the best-performing model (FR-006)
- [X] T037 [US3] Implement `calculate_vif()` in `code/diagnostics.py`:
 1. Compute VIF for all predictors.
 2. **Output**: Report individual VIF scores for every feature in `data/results/vif_diagnostics.json`.
 3. Flag any pair with VIF > 5.0 (FR-007, SC-003).
- [X] T038 [US3] Implement `group_correlated_features()` in `code/diagnostics.py`:
 1. Cluster features with VIF > 5 for *interpretive grouping*.
 2. **Constraint**: Suppress individual causal claims for clustered features in the final report (T040). Report aggregate importance for clusters instead to prevent invalid claims (SC-003).
 3. Do NOT suppress individual VIF scores in the diagnostic report (T037), only in the interpretive summary.
- [X] T038b [US3] Implement `report_cluster_importance()` in `code/report.py`: Calculate and report aggregate importance scores for correlated feature clusters identified in T038, ensuring these are used in the final ranking instead of individual features for correlated groups. (Addresses Plan Phase 3, Task 3.3)
- [X] T039 [US3] Implement `calculate_cv_stability()` in `code/report.py`: Calculate Coefficient of Variation for top features across folds (FR-009, SC-002)
- [X] T040 [US3] Implement `generate_interpretation()` in `code/report.py`:
 1. Rank features.
 2. Map top descriptors to physical mechanisms using `code/physics_mappings.py` (created in T022).
 3. Include correlation matrix between top descriptors and Weibull modulus.
 4. **Consume clustered data from T038** to suppress individual causal claims for correlated features.
- [X] T041 [US3] **Execute & Generate Interpretability Artifacts**: **Execute** `python code/report.py --generate-plots` after T036 and T039 complete to produce:
 1. `data/results/shap_summary.png` using `shap.summary_plot`.
 2. `data/results/feature_ranking_table.csv` using `pandas.DataFrame.to_csv`.
 3. `data/results/stability_metrics.json` containing the Coefficient of Variation (CV) stability scores to satisfy SC-002 evidence requirements.
 4. Verify all files exist and are non-empty. (Addresses Executability & Ordering Gaps)
 **Dependency**: T036, T039 must be complete.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reporting & Compliance (Polish)

**Purpose**: Finalize reports, ensure compliance, and update project state.

- [X] T043 [P] Implement `generate_final_report()` in `code/report.py`: Combine metrics, SHAP analysis, and disclaimers. **Include**: Calculate Confidence Intervals (CIs) for all metrics via bootstrapping (**1000 iterations**) and export CI bounds in the final report JSON. (Addresses Plan Phase 4, Task 4.2)
- [X] T044 [P] Execute `code/hash_artifacts.py` to update `state/projects/PROJ-314-predicting-the-impact-of-composition-on-weibull-modulus.yaml` with new content hashes for all files in `data/` and `code/` (Corrected path per Constitution Principle V)
- [X] T045 [P] Run `bash scripts/validate_quickstart.sh` to validate the quickstart guide against the implemented pipeline; success condition: Exit code 0 and no errors in `logs/validation.log`. **Dependency**: Requires T016a (quickstart.md generation) to be complete.
- [X] T046 [P] **Measure Pipeline Runtime**: Execute the full pipeline (Ingestion -> Modeling -> SHAP) and log the total duration to `data/results/runtime_metrics.json`. Verify duration is < 6 hours to satisfy SC-005. If duration > 6 hours, log error "Pipeline runtime exceeded 6 hours limit" and exit with code 1. (Addresses SC-005 Verification)
- [X] T047 [P] Update `docs/data_gap_protocol.md` with the exact report generation steps defined in T017b (N < 30 halting logic and `data_availability_report.json` schema). **Dependency**: Requires T016b (docs/data_gap_protocol.md creation) to be complete.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately. **T016a/b/c must be complete before T045/T047**.
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete **and** T016a/b/c completion.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **Produces the dataset for US2/US3.**
- **User Story 2 (P2)**: Depends on US1 (needs `data/processed/` dataset). **Specific Dependency**: T026 requires T018a to be complete.
- **User Story 3 (P3)**: Depends on US2 (needs trained models from US2) and T022 (physics_mappings.py).

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services (logic)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- T016a, T016b, T016c-1, T016c-2, T016c-3 can run in parallel with each other, but must complete before T045/T047.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for chemparse composition parsing in tests/test_descriptors.py"
Task: "Unit test for imputation logic in tests/test_ingestion.py"

# Launch all models for User Story 1 together:
Task: "Implement fetch_data() in code/ingestion.py"
Task: "Implement compute_descriptors() in code/descriptors.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (including T016a/b/c)
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Ingestion & Descriptors)
4. **STOP and VALIDATE**: Test ingestion on sample data; verify dataset quality.
5. Deploy/demo if ready.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Modeling)
4. Add User Story 3 → Test independently → Deploy/Demo (Interpretability)
5. Each story adds value without breaking previous stories.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Modeling) - *Can start once US1 produces data*
 - Developer C: User Story 3 (Interpretability) - *Can start once US2 produces models*
3. Stories complete and integrate independently.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CRITICAL**: All data ingestion must use real URLs or package-based fetches. No synthetic data generation for training.
- **Note on Phase 1 Tasks**: T016a/b/c added to generate required documentation artifacts (quickstart, data_gap_protocol, data-model) to resolve coverage and executability gaps.
- **Note on T017c**: Added to explicitly execute and verify the Data Gap Report generation.
- **Note on T030**: Logic corrected to align with FR-005.5 (Drop <= 10% -> Leakage; Drop > 10% -> Sufficient) and explicit file retrieval added.
- **Note on T041**: Added execution trigger and verification step.
- **Note on T046**: Added to verify SC-005 runtime constraint.
- **Note on T044**: Corrected state file path.
- **Note on T029**: Specified 1000 iterations and combined MAE/p-value check.
- **Note on T043**: Specified 1000 bootstrap iterations.
- **Note on T018c/d/e**: Added to explicitly implement FR-001 data fetching for specific repositories with fallback logic and validation.
- **Note on T010b**: Added to verify citation validation log creation.
- **Note on T027b**: Added to ensure model persistence for T030.
- **Note on Ordering**: T018c/d/e (Fetch) -> T018a (Clean) -> T017 (Validate) order enforced.