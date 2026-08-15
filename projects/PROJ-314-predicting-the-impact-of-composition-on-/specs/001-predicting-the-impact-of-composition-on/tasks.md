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

- [X] T001 Create project structure per implementation plan: Create directories `projects/PROJ-314-predicting-the-impact-of-composition-on-/code/`, `projects/PROJ-314-predicting-the-impact-of-composition-on-/data/raw/`, `data/processed/`, `data/artifacts/`, `data/models/`, `data/results/`, `data/reports/`, `tests/`, `specs/001-predict-weibull-modulus/contracts/`. Create files `requirements.txt`, `README.md`, `code/__init__.py`, `code/ingestion.py`, `code/descriptors.py`, `code/modeling.py`, `code/diagnostics.py`, `code/report.py`, `code/hash_artifacts.py`, `tests/test_descriptors.py`, `tests/test_ingestion.py`, `tests/test_modeling.py`. Generate `specs/001-predict-weibull-modulus/data-model.md` and `quickstart.md`.
- [X] T002 Initialize Python 3.11 project with requirements.txt (pandas, scikit-learn, shap, chemparse, requests, pyyaml, scipy, datasets, huggingface_hub, arxiv, pdfplumber, periodictable, pymatgen)
- [ ] T003 [P] Configure linting (ruff) and formatting (black)
- [ ] T016 [P] Define `CeramicEntry` and `DescriptorSet` schemas in `code/contracts/schemas.py` using Pydantic and **export to YAML files** `code/contracts/ceramic_entry.schema.yaml` and `code/contracts/model_result.schema.yaml`. (Addresses Plan Phase 1, Task 1.5)
- [ ] T016-3 [P] Generate `data-model.md` in `specs/001-predict-weibull-modulus/`: Document the `CeramicEntry` and `DescriptorSet` entities, their relationships, and validation rules. Must include YAML schema examples extracted from `code/contracts/ceramic_entry.schema.yaml` and `code/contracts/model_result.schema.yaml`. **Dependency**: T016. (Addresses Plan Phase 1, Task 1.5)
- [ ] T004 [P] Setup `data/raw/`, `data/processed/`, and `data/artifacts/` directories
- [X] T005 [P] Implement `code/hash_artifacts.py` for versioning and checksumming (Constitution Principle V)
- [X] T008 [P] Setup `code/ingestion.py` skeleton file structure
- [X] T009 [P] Implement URL validation logic in `code/ingestion.py`
- [X] T009b [P] Implement `validate_source_citations()` in `code/ingestion.py`: Validate source URLs/DOIs against primary sources (Constitution Principle II) by checking title overlap >= 0.7 and verifying reachability; log failures to `logs/citation_validation.log`. **Verification**: Ensure `logs/citation_validation.log` is created and populated during the first validation run. (Addresses Plan Phase 0, Task 0.3)
- [X] T010 [P] Configure logging infrastructure in `code/__init__.py` (Ensures `logs/` directory exists for T009b)
- [X] T010b [P] Verify `logs/citation_validation.log` creation: Execute `python code/ingestion.py --validate-dummy` with `dummy_urls=['https://example.com']`. Assert that `logs/citation_validation.log` exists and contains at least one entry with format `INFO: Citation validation for {url}: {status}` where status is not empty. (Addresses T009b verification gap)
- [X] T011 [P] Setup environment configuration management: Create `.env.example`, implement `load_env()` in `code/__init__.py`, and add unit test `tests/test_config.py::test_env_loading`
- [ ] T052-config [P] **Memory Configuration**: Implement `get_memory_limit()` in `code/config.py` returning `config.MEMORY_LIMIT_GB` (defaulting to a configurable memory limit in gigabytes). Add helper `check_memory_usage()` to `code/utils.py` using `psutil`. **Environment Variable**: `MEMORY_LIMIT_GB`. **Dependency**: T004. (Addresses executability-a6ec9e53)
- [ ] T017c [US1] **Create Test Data for Data Gap**: Create test data `data/raw/test_n.csv` with a representative number of rows. **Schema**: Columns must be `composition` (string), `weibull_modulus` (float), `sample_count` (int), `sintering_temp` (float), `primary_anion_cation_group` (string). **Data Values**: Use a fixed list of valid compositions: `['Al2O3', 'ZrO2', 'SiC', 'Si3N4', 'MgO', 'TiC', 'HfC', 'B4C', 'WC', 'AlN']` repeated cyclically to ensure 29 valid rows. **Purpose**: Verify T017b halts when total row count < 30 even if individual sample counts are valid. **Dependency**: None (Setup Task). (Addresses SC-004, T017b)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes data flow prerequisites for US1.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T016 [P] **Define Schemas**: Implement `CeramicEntry` and `DescriptorSet` schemas in `code/contracts/schemas.py` using Pydantic. **Output**: Export to YAML files `code/contracts/ceramic_entry.schema.yaml` and `code/contracts/model_result.schema.yaml`. **Dependency**: T016-3 (if generated later, but T016 must be first in execution order). (Addresses Plan Phase 1, Task 1.5)
- [ ] T012a [P] **Validate** `ceramic_entry.schema.yaml` in `code/contracts/`: Ensure the schema generated in T016 is correctly formatted and contains all required fields: `composition`, `weibull_modulus`, `sample_count`, `is_range_flag`, `range_original`, `primary_anion_cation_group`, `sintering_temp`, `is_imputed`, `mean_atomic_radius`, `electronegativity_std`, `valence_electron_concentration`. **Dependency**: T016 (verify file exists). (Addresses Plan Phase 1, Task 1.5; consumes T016 output)
- [ ] T012b [P] **Validate** `model_result.schema.yaml` in `code/contracts/`: Ensure the schema generated in T016 is correctly formatted and contains all required fields: `model_type`, `mae`, `r_squared`, `feature_importance_ranking`, `cv_stability_scores`. **Dependency**: T016 (verify file exists). (Addresses Plan Phase 1, Task 1.5; consumes T016 output) <!-- ATOMIZE: requested -->
- [X] T022 [P] Create `code/physics_mappings.py` with dictionary mapping descriptors to physical mechanisms (e.g., "cation_size_variance" -> "Grain boundary stability") to support US3 (Moved to Phase 2 to ensure availability before US3 work)
- [X] T006 [P] [US1] Implement base `CeramicEntry` class in `code/__init__.py` **Dependency**: T016.
- [X] T007 [P] [US1] Implement base `DescriptorSet` class in `code/__init__.py` **Dependency**: T016.
- [X] T018a [US1] **Implement Derive Primary Anion/Cation Group**: Implement `derive_primary_anion_cation_group()` in `code/ingestion.py`: Parse the `composition` string using `chemparse` to identify the primary anion and cation groups (e.g., 'O-Al' for Alumina). Create a new column `primary_anion_cation_group`. **Dependency**: T012a. (Addresses Plan Phase 1, Task 1.2)
- [X] T018b-cation-variance [US1] **Compute Cation Size Variance (Required)**: Implement `compute_cation_size_variance()` in `code/descriptors.py`: Calculate variance of cation atomic radii. **Output**: Add column `cation_size_variance`. **Note**: This is a **REQUIRED** descriptor per FR-002 and US1 acceptance scenarios. **Dependency**: T018a. (Addresses coverage-833ccaec)
- [X] T018b-range-uncertainty [US1] **Compute Range Uncertainty (Required)**: Implement `compute_range_uncertainty()` in `code/descriptors.py`: Calculate range uncertainty based on extracted midpoint (width of the range). **Output**: Add column `range_uncertainty`. **Note**: This is a **REQUIRED** descriptor per FR-002 and Edge Cases. **Dependency**: T018a. (Addresses coverage-833ccaec)
- [X] T019a [US1] **Implement Compute Mean Atomic Radius**: Implement `compute_mean_atomic_radius()` in `code/descriptors.py`: Calculate mean atomic radius from stoichiometry. **Dependency**: T018a.
- [X] T019b [US1] **Implement Compute Electronegativity Std**: Implement `compute_electronegativity_std()` in `code/descriptors.py`: Calculate standard deviation of electronegativity from stoichiometry. **Dependency**: T018a.
- [X] T019c [US1] **Implement Compute Valence Electron Concentration**: Implement `compute_valence_electron_concentration()` in `code/descriptors.py`: Calculate VEC as total valence electrons (using `periodictable` library for lookup) divided by the total number of atoms in the formula unit. **Verification**: Add a unit test to verify the formula logic with a known example. **Dependency**: T018a.
- [X] T060 [US2] **Implement Rare Class Exclusion Logic**: Implement `filter_rare_classes()` in `code/modeling.py` to drop classes with < 5 samples before splitting. **Output**: List of excluded classes. **Dependency**: T018f-5a (Count Final Entries). (Addresses SC-004, T026)

---

## Phase 3: User Story 1 - Data Ingestion and Descriptor Computation (Priority: P1) 🎯 MVP

**Goal**: Ingest raw ceramic data, clean it, and compute elemental descriptors to produce a feature-rich dataset.

**Independent Test**: Run the pipeline on a sample of known entries.; verify output CSV contains `weibull_modulus` and at least 10 computed descriptors with no missing values for primary predictors.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T013 [P] [US1] Unit test for `chemparse` composition parsing in `tests/test_descriptors.py`
- [X] T014 [P] [US1] Unit test for imputation logic (group vs. global median) in `tests/test_ingestion.py`
- [X] T015 [P] [US1] Integration test for full ingestion pipeline on a small sample in `tests/integration/test_ingestion.py`

### Implementation for User Story 1

- [X] T053 [US1] **Verify NIST URL**: Verify the reachability of the NIST Ceramic Data repository URL (or a valid NIST Materials Data API endpoint) before attempting to download. **Implementation**: Create `verify_nist_url()` in `code/ingestion.py` that uses `requests` to check status code 200 and content type. **Output**: Log result to `logs/url_verification.log`. **Dependency**: T009 (URL validation logic).
- [X] T018c [US1] **Fetch Ceramic Reliability Data (DOI 10.1111/jace.18342)**: Implement `fetch_curated_literature_data()` in `code/ingestion.py`: Fetch data from the verified DOI-linked CSV ` (or its raw GitHub mirror if DOI resolves to one). **Target**: Entries with `weibull_modulus` and `sample_count`. **Validation**: Must validate the source DOI/URL via T009b before loading. **Fail Loudly**: If fetch fails or data lacks required fields, raise `RuntimeError`. **Output**: Save raw JSON/CSV to `data/raw/curated_literature_raw.json`. (Addresses FR-001, replaces non-functional MP endpoint)
- [X] T018d-1 [US1] **Fetch NIST Ceramic Data**: Implement `fetch_nist_data()` in `code/ingestion.py`: Fetch data from the verified NIST CSV URL `. **Target**: Entries with `weibull_modulus` and `sample_count`. **Validation**: Must validate the source URL via T009b. **Fail Loudly**: If fetch fails or data lacks required fields, raise `RuntimeError`. **Output**: Save raw CSV to `data/raw/nist_raw.csv`. **Dependency**: T053. (Addresses FR-001, replaces placeholder URL)
- [X] T018d-1b [US1] **Parse NIST Data**: Implement `parse_nist_data()` in `code/ingestion.py`: Parse the raw data from T018d-1. **Verification**: Assert file size > 0KB and row count > 0. **Output**: Save parsed data to `data/processed/nist_parsed.csv`. **Dependency**: T018d-1.
- [X] T018e [US1] **Fetch ArXiv Supplementary Data**: Implement `fetch_arxiv_supplementary_data()` in `code/ingestion.py`: Fetch a pre-curated CSV dataset of ceramic Weibull data from the arXiv supplementary materials repository: `. **Target**: Entries with `weibull_modulus` and `sample_count`. **Logic**: Use `requests` to fetch the CSV directly. **Fail Loudly**: If fetch fails or data lacks required fields, raise `RuntimeError`. **Output**: Save raw JSON/CSV to `data/raw/arxiv_raw.json`. (Addresses FR-001, replaces non-deterministic PDF extraction)
- [X] T018e-1 [US1] **Validate ArXiv Extracted Tables**: Implement `validate_arxiv_tables()` in `code/ingestion.py`: Validate extracted tables against the `CeramicEntry` schema. **Logic**: Check for valid stoichiometry (parsable) and `sample_count` (>= 30). **Output**: Save validated data to `data/processed/arxiv_validated.csv`. **Dependency**: T018e. (Addresses FR-001 coverage gap for arXiv)
- [X] T018g-gen [US1] **Generate Curated Literature Dataset**: Implement `generate_curated_literature_data()` in `code/ingestion.py`: Load data from a verified DOI/URL source (e.g., DOI: 10.1111/jace.18342 - "Ceramic Reliability Database" supplementary material) and save to `data/raw/curated_literature.csv`. **Condition**: Execute **ONLY** if T018c, T018d-1, and T018e fail to return sufficient data. **Validation**: Must validate the source DOI/URL via T009b before loading. **Output**: Save raw JSON/CSV to `data/raw/curated_literature.csv`.
- [X] T018g [US1] **Load Curated Literature Data**: Implement `load_curated_literature_data()` in `code/ingestion.py`: Load the 'Curated Literature Dataset' from local file `data/raw/curated_literature.csv`. **Condition**: Execute **ONLY** if T018c, T018d-1, and T018e fail to return sufficient data. **Parsing Logic**: Parse CSV columns: `composition`, `weibull_modulus`, `sample_count`, `sintering_temp`. **Validation**: Must validate the source DOI/URL via T009b before loading (verify T018g-gen completed successfully). **Output**: Save raw JSON/CSV to `data/raw/curated_literature_raw.json`. **Dependency**: T018g-gen.
- [X] T018f-1 [US1] **Implement Per-Entry Sample Count Filter**: Implement `filter_valid_sample_count()` in `code/ingestion.py`: Filter entries where `sample_count` (N) >= 30. **Logic**: Extract N from fields 'N', 'sample_size', 'n'. If absent, exclude entry. **Output**: Intermediate file `data/processed/step0_sample_count_filtered.csv`. **Dependency**: T018c, T018d-1b, T018e-1, T018g.
- [X] T018f-2 [US1] **Implement Filter Stoichiometry**: Implement `filter_valid_stoichiometry()` in `code/ingestion.py`: Filter entries with valid, parsable stoichiometry. **Output**: Intermediate file `data/processed/step1_stoichiometry_filtered.csv`. **Dependency**: T018f-1.
- [X] T018f-5 [US1] **Implement Handle Non-Stoichiometric Phases**: Implement `handle_non_stoichiometric()` in `code/ingestion.py`: Exclude entries where composition implies a non-stoichiometric phase that cannot be parsed. **Output**: Intermediate file `data/processed/step2_non_stoichiometric_filtered.csv`. **Dependency**: T018f-2.
- [X] T018f-3 [US1] **Implement Handle Range Values**: Implement `handle_range_values()` in `code/ingestion.py`: Extract midpoint, set `is_range_flag`, compute `range_uncertainty`. **Output**: Intermediate file `data/processed/step3_range_handled.csv`. **Dependency**: T018f-5.
- [X] T059a [US1] **Flag/Exclude High-Variance Range Entries**: Implement `flag_high_variance_ranges()` in `code/ingestion.py`: Exclude entries where the range width exceeds a threshold (e.g., > 50% of the midpoint). **Output**: Generate `data/processed/step_range_filtered.csv`. **Dependency**: T018f-3. (Addresses Plan.md 'Range Data Dominance' risk)
- [X] T018f-4 [US1] **Implement Imputation**: Implement `impute_missing_params()` in `code/ingestion.py`: Impute missing `sintering_temp` with group median, add `is_imputed` flag. If group size < 5, use global median. **Output**: Save to `data/processed/step_final_cleaned.csv`. **Dependency**: T018a, T018f-3, T059a.
- [X] T018f-5a [US1] **Count Final Entries**: Implement `count_final_entries()` in `code/ingestion.py`: Read `step_final_cleaned.csv` (produced by T018f-4), count rows, and write the count to `data/processed/final_count.txt`. **Output**: `data/processed/final_count.txt` containing the integer count. **Dependency**: T018f-4. (Addresses SC-004, T017b)
- [X] T017b [US1] **Implement Data Gap Validation & Report**: Implement `validate_data_gap()` in `code/ingestion.py`: Read the count from `data/processed/final_count.txt` (T018f-5a). **Logic**: If total row count < 30, immediately call `generate_data_availability_report()`, log the report path, output "Power Limitation: Insufficient data (N < 30)" to stderr, and **generate the report file** `data/reports/data_availability_report.json` (schema defined in `code/contracts/ceramic_entry.schema.yaml`) before exiting with code 1. If 30 <= N < 50, log "Warning: Small dataset (30 <= N < 50). Hold-out validation will be used." and exit with code 0 (pass). **Output**: Generate `data/reports/data_availability_report.json` and exit. **Dependency**: T018f-5a, T017c. (Addresses SC-004)
- [X] T020 [US1] **Implement Validate No Missing Primary Predictors**: Implement `validate_no_missing_primary_predictors()` in `code/ingestion.py`: Validate that essential descriptors have no missing values after cleaning and imputation. **Dependency**: T018f-4, T019a, T019b, T019c, T018b-cation-variance.
- [X] T049 [US1] **Hard Fail on Synthetic Fallback**: Enforce a "Fail Loudly" policy. **Implementation**: Add a guard clause in `code/ingestion.py` at the start of the data loading function that raises `RuntimeError` with message "Synthetic data fallback detected: Failing loudly" if any synthetic data generation is attempted. **Dependency**: T018c, T018d-1, T018e, T018g.
- [X] T054-stream-test [US1] **Test Streaming Logic**: Implement `test_streaming_ingestion()` in `tests/test_ingestion.py`: Create a mock dataset generator that yields > 100,000 rows. Verify that `fetch_materials_project_data` processes the data within reasonable memory constraints. **Dependency**: T018c. (Addresses Large Real Dataset Streaming Rule - Note: Streaming is out of scope per Assumptions, but this test verifies robustness)

---

## Phase 4: User Story 2 - Predictive Modeling and Cross-Validation (Priority: P2)

**Goal**: Train Random Forest and Gradient Boosting models with strict cross-validation to predict Weibull modulus.

**Independent Test**: Execute training on a subset; verify JSON output contains MAE, R², and stratified split report confirming distribution match.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US2] Unit test for stratified splitting logic in `tests/test_modeling.py` **Dependency**: T026.
- [X] T024 [P] [US2] Unit test for baseline (global mean) predictor in `tests/test_modeling.py` **Dependency**: T028b.
- [ ] T025 [P] [US2] Implement integration test `tests/integration/test_modeling.py::test_5fold_cv_stratified_split` to verify the 5-fold CV workflow and **generate `data/results/cv_split_report.json`** containing stratification distribution metrics. **Schema**: `{"fold_sizes": [int], "class_distribution": {"class_name": {"train": int, "test": int}}, "total_samples": int}`. **Dependency**: T026, T027b, T028.

### Implementation for User Story 2

- [X] T026 [US2] Implement `prepare_splits()` in `code/modeling.py`: Stratified split based on `primary_anion_cation_group`. **Logic**: If N >= 50, use Stratified 5-fold CV. If 30 <= N < 50, use Stratified 80/20 Hold-out (per SC-004). **Dependency**: T018f-5a, T060, T017b. (Note: Rare class exclusion is handled by T060; T026 consumes the pre-filtered dataset).
- [X] T027a [US2] **Define Hyperparameter Search Space**: Define the constrained set of hyperparameter combinations for RF and GBM in `code/modeling.py`. **Concrete Grid**: `n_estimators`: [50, 100, 200], `max_depth`: [None, 10, 20], `min_samples_split`: [2, 5, 10]. **Constraint**: The total number of combinations must remain within a manageable scope. **Output**: A dictionary `hyperparameter_search_space` with these exact values. **Verification**: Add a unit test `tests/test_modeling.py::test_hyperparameter_grid_constraints` that asserts `len(list(itertools.product(*hyperparameter_search_space.values()))) <= 50`. **Dependency**: None (Setup Task). (Addresses Plan Phase 2, Task 2.2 constraints and executability-41272025)
- [ ] T027b [US2] **Train Models**: Implement `train_models()` in `code/modeling.py`: Train RF and GBM using the defined search space from T027a. **Critical**: Store feature importance scores from **each CV fold** in `data/results/fold_importances.json`. **Schema**: `{"model_type": "RF|GBM", "fold_id": int, "feature_importance": {"feature_name": float}}`. **Dependency**: T027a, T026.
- [X] T029 [US2] Implement `run_permutation_test` in `code/modeling.py`: Perform a permutation test to determine statistical significance of model improvement over the baseline. **Logic**: 1) Calculate MAE improvement percentage (must be >= 10% for SC-001). 2) Calculate p-value using 1000 iterations, **seed=42** (for shuffling), and shuffling the target variable `y` (weibull_modulus). **Null Hypothesis**: Shuffle weibull_modulus values (y), **retrain the model** on the shuffled data for each iteration, and calculate MAE. **Reporting**: Generate `data/results/permutation_test_report.json` containing p-value, MAE improvement, `mae_threshold_pass` (boolean). **Gating**: If p >= 0.05 OR MAE improvement < 10%, **generate `data/results/model_success_flag.json` with `{"success": false, "reason": "Not Significant"}`** and **log "Model not statistically significant"**. The pipeline **MUST NOT** proceed to T031 (Generate Model Metrics) for the 'Success' claim; instead, T031 must read this flag and generate a report indicating "Model Failed Significance Check". **Dependency**: T027b.
- [X] T027d [US2] **Save Best Model**: Save the best performing model to `data/models/best_model.pkl` **regardless of T029 outcome** to ensure reproducibility. If T029 fails, log "Model saved for exploratory analysis". **Dependency**: T027b.
- [X] T028b [US2] Implement `run_baseline_predictor()` in `code/modeling.py`: Create a simple model that predicts the global mean Weibull modulus for all test samples and save the MAE. **Dependency**: T026.
- [X] T028 [US2] Implement `evaluate_models()` in `code/modeling.py`: Calculate MAE, R², and compare against global mean baseline.
- [X] T030b [US2] **Train Leakage Check Model**: Train a second Random Forest model excluding the 'primary_anion_cation_group' feature. **Dependency**: T027b (Run regardless of T029 outcome). **Output**: Save model and metrics to `data/models/leakage_check_model.pkl`.
- [X] T030 [US2] **Implement Descriptor Sufficiency Check**: Implement `check_descriptor_sufficiency()` in `code/diagnostics.py`: Perform a sufficiency check by comparing model performance with and without the 'primary_anion_cation_group' feature. **Logic**: Read `data/models/leakage_check_model.pkl` and compare MAE from T027b. **Condition**: If MAE increases (performance drop) by >= 10%, flag "POTENTIAL LEAKAGE" (the model relied on the proxy). If MAE increases by < 10%, flag "DESCRIPTORS SUFFICIENT" (the descriptors did the work). **Output**: Generate `data/results/descriptor_sufficiency.json`. (Addresses FR-005.5, Plan Phase 2 Task 2.5). **Dependency**: T027b, T030b.
- [X] T031 [US2] Generate `data/results/model_metrics.json` with all scores and stratification reports. **Logic**: If `data/results/model_success_flag.json` exists and `success` is false, generate a report indicating the model failed the significance check. **Dependency**: T029, T028.
- [X] T050 [US2] **Add Runtime Enforcement**: Wrap the entire `code/modeling.py` execution in a timeout handler to ensure completion within 6 hours. **Implementation**: Use `multiprocessing` to enforce a time limit on the full pipeline execution (ingestion to reporting). **Dependency**: None (wraps full pipeline). **Action**: If timeout exceeded, kill process and log `TimeoutExceededError`. **Logging**: Log the total runtime duration upon completion or timeout.

---

## Phase 5: User Story 3 - Feature Importance and Mechanistic Interpretation (Priority: P3)

**Goal**: Extract SHAP values, rank features, and interpret results against fracture mechanics principles.

**Independent Test**: Run analysis on best model; verify output lists top descriptors, includes correlation matrix, and flags collinearity.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T033 [P] [US3] Unit test for VIF calculation in `tests/test_diagnostics.py` **Dependency**: T037.
- [X] T034 [P] [US3] Unit test for SHAP value aggregation in `tests/test_report.py` **Dependency**: T036b.
- [X] T035 [P] [US3] Integration test for full interpretability pipeline in `tests/integration/test_interpretability.py` **Dependency**: T036b, T037, T038, T039, T040, T041. <!-- FAILED: unspecified -->

### Implementation for User Story 3

- [X] T036a [US3] **Compute SHAP per Fold**: Implement `calculate_shap_per_fold()` in `code/diagnostics.py`: Generate SHAP values for the best-performing model **across all cross-validation folds**. **Output**: Return a list of SHAP value arrays, one per fold. **Dependency**: T027b.
- [X] T036b [US3] **Aggregate SHAP Values**: Implement `aggregate_shap_values()` in `code/diagnostics.py`: Aggregate the per-fold SHAP values from T036a. **Output**: Return aggregated SHAP summary. **Dependency**: T036a.
- [X] T039a [US3] **Derive Feature Importance Scores**: Implement `derive_feature_importance_scores()` in `code/diagnostics.py`: Convert aggregated SHAP values into a ranked list of feature importance scores (e.g., mean absolute SHAP). **Output**: Return a sorted list of (feature, score) tuples. **Dependency**: T036b.
- [X] T039 [US3] **Calculate CV Stability**: Implement `calculate_cv_stability()` in `code/report.py`: Calculate Coefficient of Variation (CV) for **top 5 feature importance scores** **across cross-validation folds** by aggregating the per-fold feature importance scores from T039a. **Logic**: Calculate the *mean* importance of the top-ranked features across folds, then compute the CV of these mean values. **Dependency**: T039a. (Addresses SC-002)
- [X] T037 [US3] Implement `calculate_vif()` in `code/diagnostics.py`: Compute VIF for all predictors and flag highly correlated features.
- [X] T038 [US3] **Group Correlated Features**: Implement `group_correlated_features()` in `code/diagnostics.py`: Cluster highly correlated features (VIF > 5) into groups for interpretive grouping. **Output**: List of feature clusters. **Dependency**: T037.
- [X] T038b [US3] Implement `report_cluster_importance()` in `code/report.py`: Calculate and report aggregate importance scores for correlated feature clusters.
- [X] T040 [US3] **Generate Interpretation**: Implement `generate_interpretation()` in `code/report.py`: Rank features, map descriptors to physical mechanisms, and include correlation matrix. **Validation**: Explicitly compare the top 5 SHAP-ranked features against `code/physics_mappings.py` (T022) and log a "Physical Plausibility" check. **Dependency**: T039, T038.
- [ ] T041 [US3] **Execute & Generate Interpretability Artifacts**: Execute the analysis and generate SHAP summary plot (`data/artifacts/shap_summary.png`), feature ranking table (`data/results/feature_ranking.csv` with columns `rank`, `feature`, `importance`, `cluster_id`), and stability metrics (`data/results/stability_metrics.json`). **Dependency**: T036b-T040.

---

## Phase 6: Reporting & Compliance (Polish)

**Purpose**: Finalize reports, ensure compliance, and update project state.

- [X] T043 [P] **Generate Final Report**: Implement `generate_final_report()` in `code/report.py`: Combine metrics, SHAP analysis, and disclaimers. **Logic**: Read `data/results/model_metrics.json`, `data/results/descriptor_sufficiency.json`, and `data/results/stability_metrics.json`. Append the disclaimer "These results represent statistical associations only and do not imply causal relationships" to all text outputs. Remove the word "cause" from the 'conclusion' field. **Output**: `data/reports/final_report.md`. **Dependency**: T031, T041, T017b (if triggered).
- [X] T044 [P] **Update Project State**: Execute `code/hash_artifacts.py` to update project state with new content hashes for all files in `data/` and `code/`. **Logic**: Run `python code/hash_artifacts.py --update-state`. Verify `state/projects/PROJ-314-predicting-the-impact-of-composition-on-.yaml` is updated with `updated_at` and `artifact_hashes`. **Dependency**: T043.
- [X] T045 [P] **Validate Quickstart**: Run `bash scripts/validate_quickstart.sh` to validate the quickstart guide against the implemented pipeline. **Logic**: The script must execute `python code/ingestion.py --dry-run` and `python code/modeling.py --dry-run` to ensure all entry points are functional. **Output**: `logs/quickstart_validation.log`. **Dependency**: T044.
- [X] T051 [P] **Final Compliance Audit**: Run a script to ensure all requirements are met.

---

## Phase 7: Revision & Stability (Post-Analysis)

**Purpose**: Address specific reviewer concerns from prior analysis rounds to ensure robustness and correctness.

- [X] T054 [US1] **Verify Real Data Source Adoption**: If execution feedback provides a "VERIFIED REAL DATA SOURCE" (e.g., specific package + recipe), update `code/ingestion.py` to exclusively use that source. Remove all hand-rolled `load_dataset` or guessed URL fallbacks. **Dependency**: Execution feedback. (Addresses "If a verified real data source is injected, USE it"). Note: If T018d-1 fails in Phase 3, this task automates the fix for subsequent runs. <!-- FAILED: unspecified -->
- [ ] T056 [US2] **Enforce Collinearity Clustering in SHAP**: Ensure `group_correlated_features()` (T038) is called *before* ranking features in `generate_interpretation()`. **Logic**: If VIF > 5, group features and report *aggregate* importance for the cluster, not individual ranks. **Dependency**: T037, T040. (Addresses FR-007, T038 logic). <!-- FAILED: unspecified -->
- [ ] T057 [US2] **Verify Permutation Test Robustness**: Ensure `run_permutation_test()` (T029) uses a sufficient number of iterations (>= 1000) and a fixed seed (42) for reproducibility. **Verification**: Check `data/results/permutation_test_report.json` for `iterations` and `seed` fields. (Addresses SC-001, T029). <!-- ATOMIZE: requested -->
- [X] T058 [US3] **Validate CV Calculation Logic**: Ensure `calculate_cv_stability()` (T039) computes CV on the *mean* importance of the top 5 features *across folds*, not on the raw per-fold values. **Verification**: Unit test `tests/test_report.py::test_cv_stability_logic`. (Addresses SC-002, T039).
- [ ] T059 [US1] **Add Range Uncertainty to Feature Set**: Ensure `compute_range_uncertainty()` (T018b-range-uncertainty) is called and the resulting column is included in the final feature set for modeling. **Verification**: Check `data/processed/step_final_cleaned.csv` for `range_uncertainty` column. (Addresses Edge Case: Range Data Dominance).
- [ ] T062 [US1] **Add Dataset Power Analysis**: Implement `calculate_dataset_power()` in `code/ingestion.py` to estimate statistical power based on the final dataset size and variance. **Formula**: Use Cohen's d based power analysis with effect size = 0.5, alpha = 0.05. **Output**: Add `statistical_power` field to `data/reports/data_availability_report.json`. **Dependency**: T017b. (Addresses SC-004).
- [ ] T063 [US2] **Explicitly Define Hyperparameter Search Space**: In `code/modeling.py`, replace the placeholder `hyperparameter_search_space` (T027a) with a concrete dictionary defining `n_estimators` (e.g., [50, 100, 200]), `max_depth` (e.g., [None, 10, 20]), and `min_samples_split` (e.g., [2, 5, 10]) for both Random Forest and Gradient Boosting, ensuring the total combinations do not exceed 50. **Dependency**: T027a. (Addresses Plan Phase 2, Task 2.2 constraints).
- [ ] T064 [US3] **Implement Collinearity-Aware Ranking**: Modify `derive_feature_importance_scores()` (T039a) to accept the output of `group_correlated_features()` (T038). If a feature belongs to a high-VIF cluster, assign it the *cluster's* aggregate importance rather than its individual score, and mark it as `clustered` in the output ranking table. **Dependency**: T037, T038, T039a. (Addresses FR-007, SC-003).
- [ ] T065 [US1] **Stream Large Dataset Validation**: Update `fetch_materials_project_data()` (T018c) to accept a `streaming=True` flag. When enabled, use `datasets.load_dataset(..., streaming=True)` to iterate over the dataset chunk-by-chunk, computing running statistics (count, mean, std) without loading the full dataset into RAM. **Verification**: Run a test with a mock generator yielding 1M rows; assert peak memory usage < 2GB. **Dependency**: T018c. (Addresses Large Real Dataset Streaming Rule).
- [ ] T066 [US2] **Stratification Fallback for Rare Classes**: In `prepare_splits()` (T026), if a class has < 5 samples, log a warning and remove it from the stratification list (forcing simple random split for that class) rather than crashing. **Dependency**: T026, T060. (Addresses Plan Phase 2, Task 2.1 "Rare Class Handling").
- [ ] T067 [US3] **Generate Correlation Matrix Artifact**: In `generate_interpretation()` (T040), explicitly compute and save the Pearson correlation matrix of all descriptors to `data/results/descriptor_correlation_matrix.csv`. **Dependency**: T040. (Addresses US3 Acceptance Scenario 3).