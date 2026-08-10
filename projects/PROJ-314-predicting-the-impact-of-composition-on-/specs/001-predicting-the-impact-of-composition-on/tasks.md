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
- [X] T003 [P] Configure linting (ruff) and formatting (black)
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
- [X] T010b [P] Verify `logs/citation_validation.log` creation: Execute `python code/ingestion.py --validate-dummy` with `dummy_urls=['https://example.com', ' Name or service not known)"))]']`. Assert that `logs/citation_validation.log` exists and contains at least one entry with format `INFO: Citation validation for {url}: {status}` where status is not empty. (Addresses T009b verification gap)
- [X] T011 [P] Setup environment configuration management: Create `.env.example`, implement `load_env()` in `code/__init__.py`, and add unit test `tests/test_config.py::test_env_loading`

---

## Phase 3: User Story 1 - Data Ingestion and Descriptor Computation (Priority: P1) 🎯 MVP

**Goal**: Ingest raw ceramic data, clean it, and compute elemental descriptors to produce a feature-rich dataset.

**Independent Test**: Run the pipeline on a sample of known entries.; verify output CSV contains `weibull_modulus` and at least 10 computed descriptors with no missing values for primary predictors.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T013 [P] [US1] Unit test for `chemparse` composition parsing in `tests/test_descriptors.py`
- [X] T014 [P] [US1] Unit test for imputation logic (group vs. global median) in `tests/test_ingestion.py`
- [X] T015 [P] [US1] Integration test for full ingestion pipeline on a small sample in `tests/integration/test_ingestion.py`

### Implementation for User Story 1

- [ ] T018c [US1] Implement `fetch_materials_project_data()` in `code/ingestion.py`: Use `pymatgen` (mp-api) to fetch ceramic property data. **Endpoint**: Use `MPRestClient().get_entries(elements=..., properties=['weibull_modulus'])`. Query: `{elements: {exists: true}, properties: {weibull_modulus: {exists: true}}}`. Fetch from Materials Project API. **Fail Loudly**: If API returns no Weibull data or connection fails, raise `RuntimeError` with message "Materials Project fetch failed: {error}". **Fallback**: If no data is found, immediately trigger the T018g fallback logic. Output raw JSON to `data/raw/materials_project_raw.json`. (Addresses FR-001 coverage gap, corrected URL/logic, removed fallback)
- [ ] T018d [US1] Implement `fetch_nist_data()` in `code/ingestion.py`: Use `requests` to fetch NIST ceramic data from verified URL: `. **Fail Loudly**: If the fetch fails or returns no Weibull data, raise a `RuntimeError` with an appropriate error message. **Fallback**: If fetch fails, immediately trigger the T018g fallback logic. Output raw JSON/CSV to `data/raw/nist_raw.json`. (Addresses FR-001 coverage gap, corrected URL)
- [ ] T018e [US1] Implement `fetch_arxiv_data()` in `code/ingestion.py`: Use `arxiv` library to search for `all:ceramic AND all:weibull` (limit a representative sample). Use `pdfplumber` to extract tables from the top 5 PDFs returned by the search (sorted by relevance). **Extraction Logic**: Use regex patterns `r"(Al|Si|O|Ti|Zr|Zn|Nb|Ta|Hf|Mo|W|V|Cr|Mn|Fe|Co|Ni|Cu|Ga|In|Sn|Sb|Te|Bi|Pb|S|Se|F|Cl|Br|I)"` for composition and `r"(Weibull|Modulus)"` for target. Extract the **first valid table** found in the PDF. **Fail Loudly**: If no table is found or extraction fails, raise `RuntimeError`. Do NOT skip rows silently. Output raw JSON/CSV to `data/raw/arxiv_raw.json`. (Addresses FR-001 coverage gap, corrected logic, removed silent fallback)
- [ ] T018g [US1] Implement `fetch_curated_literature_data()` in `code/ingestion.py`: Fetch the 'Curated Literature Dataset' from verified URL: `. **Parsing Logic**: Parse CSV columns: `composition`, `weibull_modulus`, `sample_count`, `sintering_temp`. **Fail Loudly**: If fetch fails or no data is found, raise `RuntimeError`. **Trigger Logic**: This task is ONLY executed if T018c, T018d, or T018e fail or return no data. Output raw JSON/CSV to `data/raw/curated_literature_raw.json`. (Addresses Plan Phase 0, Task 0.2 fallback requirement)
- [ ] T018a [US1] Implement `derive_primary_anion_cation_group()` in `code/ingestion.py`: Parse the `composition` string using `chemparse` to identify the primary anion and cation groups (e.g., 'O-Al' for Alumina). Create a new column `primary_anion_cation_group`. **Dependency**: T018c, T018d, T018e, T018g must be complete. **Execution Order**: T017 (Gate Pass) must be true (N >= 30) before this task runs.
- [ ] T018f-clean [US1] Implement `clean_data_pipeline()` in `code/ingestion.py`: Consolidated data cleaning pipeline. **Steps**: 1. `filter_valid_stoichiometry()` -> `data/processed/step1_cleaned.csv`. 2. `handle_range_values()` -> `data/processed/step2_range.csv`. 3. `impute_missing_params()` -> `data/processed/step3_imputed.csv`. 4. `handle_non_stoichiometric_phases()` -> `data/processed/step4_final.csv`. **Dependency**: T018c, T018d, T018e, T018g, T018a, T017 (Gate Pass).
- [ ] T017 [US1] Implement `validate_data_gap()` in `code/ingestion.py`: Check total valid entries after fetching (raw count) and cleaning. Halt execution if N < 30 and generate a "Data Availability Report". **Dependency**: T018c, T018d, T018e, T018g.
- [ ] T017b [US1] Implement `generate_data_availability_report()` in `code/ingestion.py`: Generate the `data/reports/data_availability_report.json` file when halting due to insufficient data. **Dependency**: T017.
- [ ] T018b-impl [US1] Implement `compute_range_uncertainty()` in `code/descriptors.py`: Calculate range uncertainty based on extracted midpoint. **Dependency**: T018f-clean (Step 2).
- [ ] T019a [US1] Implement `compute_mean_atomic_radius()` in `code/descriptors.py`: Calculate mean atomic radius from stoichiometry. **Dependency**: T018f-clean (Step 4).
- [ ] T019b [US1] Implement `compute_electronegativity_std()` in `code/descriptors.py`: Calculate standard deviation of electronegativity from stoichiometry. **Dependency**: T018f-clean (Step 4).
- [ ] T019c [US1] Implement `compute_valence_electron_concentration()` in `code/descriptors.py`: Calculate VEC as total valence electrons divided by the total number of atoms. **Dependency**: T018f-clean (Step 4).
- [ ] T020 [US1] Implement `validate_no_missing_primary_predictors()` in `code/ingestion.py`: Validate that essential descriptors have no missing values after cleaning and imputation. **Dependency**: T018f-clean, T019a, T019b, T019c.
- [ ] T052 [US1] **Memory Check**: Implement memory usage check to prevent exceeding the memory limit. **Implementation**: Use `psutil` to monitor RSS and raise `MemoryError` if > 6GB. **Output**: Log to `logs/memory_monitor.log`. **Dependency**: T017 (Gate Pass). **Threshold**: Use `config.MEMORY_LIMIT_GB` (6GB).
- [ ] T049 [US1] **Hard Fail on Synthetic Fallback**: Enforce a "Fail Loudly" policy, preventing any fallback to synthetic data generation. **Implementation**: Add a guard clause in `code/ingestion.py` that raises `RuntimeError` with message "Synthetic data fallback detected: Failing loudly" if any synthetic data generation is attempted. **Dependency**: T018c, T018d, T018e, T018g.
- [ ] T053 [US1] **Implement NIST URL Verification**: Verify the reachability and content of the NIST ceramic data URL (`) before attempting to download it.

---

## Phase 4: User Story 2 - Predictive Modeling and Cross-Validation (Priority: P2)

**Goal**: Train Random Forest and Gradient Boosting models with strict cross-validation to predict Weibull modulus.

**Independent Test**: Execute training on a subset; verify JSON output contains MAE, R², and stratified split report confirming distribution match.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US2] Unit test for stratified splitting logic in `tests/test_modeling.py`
- [X] T024 [P] [US2] Unit test for baseline (global mean) predictor in `tests/test_modeling.py`
- [X] T025 [P] [US2] Implement integration test `tests/integration/test_modeling.py::test_5fold_cv_stratified_split` to verify the 5-fold CV workflow and **generate `data/results/cv_split_report.json`** containing stratification distribution metrics.

### Implementation for User Story 2

- [X] T026 [US2] Implement `prepare_splits()` in `code/modeling.py`: Stratified split based on `primary_anion_cation_group`; switch to hold-out if N < 50.
- [X] T027a [US2] Define `hyperparameter_search_space` in `code/modeling.py`: Define the constrained set of hyperparameter combinations for RF and GBM (a limited number of combinations).
- [X] T027b [US2] Implement `train_models()` in `code/modeling.py`: Train RF and GBM using the defined search space. **Dependency**: T027a.
- [ ] T027d [US2] **Save Best Model**: Save the best performing model to `data/models/best_model.pkl`. **Dependency**: T027b.
- [X] T028b [US2] Implement `run_baseline_predictor()` in `code/modeling.py`: Create a simple model that predicts the global mean Weibull modulus for all test samples and save the MAE. **Dependency**: T026.
- [X] T028 [US2] Implement `evaluate_models()` in `code/modeling.py`: Calculate MAE, R², and compare against global mean baseline.
- [ ] T029 [US2] Implement `run_permutation_test()` in `code/modeling.py`: Perform a permutation test to determine statistical significance of model improvement over the baseline. **Logic**: 1) Calculate MAE improvement percentage (must be >= 10% for SC-001). 2) Calculate p-value (must be < 0.05). **Combined Gate**: If MAE improvement < 10% OR p-value >= 0.05, flag as "Not Statistically Significant" and halt or report failure. **Output**: Generate `data/results/permutation_test_report.json` containing p-value, MAE improvement, and combined verdict. (Addresses SC-001 logic separation).
- [ ] T030 [US2] Implement `check_leakage()` in `code/diagnostics.py`: Perform a leakage check by comparing model performance with and without the 'primary_anion_cation_group' feature. **Logic**: Re-run best model without 'primary_anion_cation_group'. If performance drops by **less than 10%**, flag "Potential Leakage" with exact warning message. **Output**: Generate `data/results/leakage_check.json`. (Addresses FR-005.5).
- [X] T031 [US2] Generate `data/results/model_metrics.json` with all scores and stratification reports
- [X] T032 [US2] Implement `filter_rare_classes()` in `code/modeling.py` to drop classes with < 5 samples before splitting, and verify via `tests/test_modeling.py::test_rare_class_exclusion`
- [ ] T050 [US2] **Add Runtime Enforcement**: Wrap the `train_models` and `run_permutation_test` execution in a timeout handler to ensure completion within 6 hours.

---

## Phase 5: User Story 3 - Feature Importance and Mechanistic Interpretation (Priority: P3)

**Goal**: Extract SHAP values, rank features, and interpret results against fracture mechanics principles.

**Independent Test**: Run analysis on trained model; verify output lists top descriptors, includes correlation matrix, and flags collinearity.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T033 [P] [US3] Unit test for VIF calculation in `tests/test_diagnostics.py`
- [X] T034 [P] [US3] Unit test for SHAP value aggregation in `tests/test_report.py`
- [X] T035 [P] [US3] Integration test for full interpretability pipeline in `tests/integration/test_interpretability.py`

### Implementation for User Story 3

- [ ] T036 [US3] Implement `calculate_shap()` in `code/diagnostics.py`: Generate SHAP values for the best-performing model
- [ ] T037 [US3] Implement `calculate_vif()` in `code/diagnostics.py`: Compute VIF for all predictors and flag highly correlated features.
- [ ] T038 [US3] Implement `group_correlated_features()` in `code/diagnostics.py`: Cluster highly correlated features for interpretive grouping.
- [ ] T038b [US3] Implement `report_cluster_importance()` in `code/report.py`: Calculate and report aggregate importance scores for correlated feature clusters.
- [ ] T039 [US3] Implement `calculate_cv_stability()` in `code/report.py`: Calculate Coefficient of Variation for top 5 features **across cross-validation folds** by aggregating feature importance scores from individual folds.
- [ ] T040 [US3] Implement `generate_interpretation()` in `code/report.py`: Rank features, map descriptors to physical mechanisms, and include correlation matrix.
- [ ] T041 [US3] **Execute & Generate Interpretability Artifacts**: Execute the analysis and generate SHAP summary plot (`data/artifacts/shap_summary.png`), feature ranking table (`data/results/feature_ranking.csv`), and stability metrics (`data/results/stability_metrics.json`). **Dependency**: T036-T040.

---

## Phase 6: Reporting & Compliance (Polish)

**Purpose**: Finalize reports, ensure compliance, and update project state.

- [ ] T043 [P] Implement `generate_final_report()` in `code/report.py`: Combine metrics, SHAP analysis, and disclaimers.
- [X] T044 [P] Execute `code/hash_artifacts.py` to update project state with new content hashes for all files in `data/` and `code/`.
- [ ] T045 [P] Run `bash scripts/validate_quickstart.sh` to validate the quickstart guide against the implemented pipeline.
- [ ] T046 [P] **Measure Pipeline Runtime**: Execute the full pipeline and log the total duration.
- [ ] T047 [P] Update `docs/data_gap_protocol.md` with the exact report generation steps.
- [ ] T051 [P] **Final Compliance Audit**: Run a script to ensure all requirements are met.
- [ ] T017c [US1] Create test data `data/raw/test_n29.csv` with exactly 29 rows where the `sample_count` field is >= 30. **Purpose**: Verify T017 halts when total row count < 30 even if individual sample counts are valid. (Clarified: T017 checks total rows, T018f checks sample_count field).