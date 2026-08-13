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

- [ ] T001 Create project structure per implementation plan (projects/PROJ-314-predicting-the-impact-of-composition-on-)
- [X] T002 Initialize Python 3.11 project with requirements.txt (pandas, scikit-learn, shap, chemparse, requests, pyyaml, scipy, datasets, huggingface_hub, arxiv, pdfplumber, periodictable, pymatgen)
- [ ] T003 [P] Configure linting (ruff) and formatting (black)
- [ ] T016 [P] Define `CeramicEntry` and `DescriptorSet` schemas in `code/contracts/schemas.py` using Pydantic and export to YAML files `ceramic_entry.schema.yaml` and `model_result.schema.yaml` in `code/contracts/`. (Addresses Plan Phase 1, Task 1.5)
- [ ] T016-3 [P] Generate `data-model.md` in `specs/001-predict-weibull-modulus/`: Document the `CeramicEntry` and `DescriptorSet` entities, their relationships, and validation rules. Must include YAML schema examples extracted from `code/contracts/ceramic_entry.schema.yaml` and `code/contracts/model_result.schema.yaml`. **Dependency**: T016. (Addresses Plan Phase 1, Task 1.5)
- [ ] T004 [P] Setup `data/raw/`, `data/processed/`, and `data/artifacts/` directories
- [X] T005 [P] Implement `code/hash_artifacts.py` for versioning and checksumming (Constitution Principle V)
- [X] T008 [P] Setup `code/ingestion.py` skeleton file structure
- [X] T009 [P] Implement URL validation logic in `code/ingestion.py`
- [X] T009b [P] Implement `validate_source_citations()` in `code/ingestion.py`: Validate source URLs/DOIs against primary sources (Constitution Principle II) by checking title overlap >= 0.7 and verifying reachability; log failures to `logs/citation_validation.log`. **Verification**: Ensure `logs/citation_validation.log` is created and populated during the first validation run. (Addresses Plan Phase 0, Task 0.3)
- [X] T010 [P] Configure logging infrastructure in `code/__init__.py` (Ensures `logs/` directory exists for T009b)
- [X] T010b [P] Verify `logs/citation_validation.log` creation: Execute `python code/ingestion.py --validate-dummy` with `dummy_urls=['https://example.com']`. Assert that `logs/citation_validation.log` exists and contains at least one entry with format `INFO: Citation validation for {url}: {status}` where status is not empty. (Addresses T009b verification gap)
- [X] T011 [P] Setup environment configuration management: Create `.env.example`, implement `load_env()` in `code/__init__.py`, and add unit test `tests/test_config.py::test_env_loading`
- [ ] T052-config [P] **Memory Configuration**: Implement `get_memory_limit()` in `code/config.py` returning `config.MEMORY_LIMIT_GB` (default sufficient memory capacity). Add helper `check_memory_usage()` to `code/utils.py` using `psutil`. **Dependency**: T004. (Addresses executability-a6ec9e53)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes data flow prerequisites for US1.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T012a [P] **Validate** `ceramic_entry.schema.yaml` in `code/contracts/`: Ensure the schema generated in T016 is correctly formatted and contains all required fields: `composition`, `weibull_modulus`, `sample_count`, `is_range_flag`, `range_original`, `primary_anion_cation_group`, `sintering_temp`, `is_imputed`, `mean_atomic_radius`, `electronegativity_std`, `valence_electron_concentration`. (Addresses Plan Phase 1, Task 1.5; consumes T016 output)
- [ ] T012b [P] **Validate** `model_result.schema.yaml` in `code/contracts/`: Ensure the schema generated in T016 is correctly formatted and contains all required fields: `model_type`, `mae`, `r_squared`, `feature_importance_ranking`, `cv_stability_scores`. (Addresses Plan Phase 1, Task 1.5; consumes T016 output)
- [X] T022 [P] Create `code/physics_mappings.py` with dictionary mapping descriptors to physical mechanisms (e.g., "cation_size_variance" -> "Grain boundary stability") to support US3 (Moved to Phase 2 to ensure availability before US3 work)
- [X] T006 [P] [US1] Implement base `CeramicEntry` class in `code/__init__.py` (Dependency: T012a for type hints)
- [X] T007 [P] [US1] Implement base `DescriptorSet` class in `code/__init__.py` (Dependency: T012b for type hints)
- [ ] T018a [US1] **Implement Derive Primary Anion/Cation Group**: Implement `derive_primary_anion_cation_group()` in `code/ingestion.py`: Parse the `composition` string using `chemparse` to identify the primary anion and cation groups (e.g., 'O-Al' for Alumina). Create a new column `primary_anion_cation_group`. **Dependency**: T012a. (Addresses Plan Phase 1, Task 1.2)
- [ ] T018b-cation-variance [US1] **Compute Cation Size Variance**: Implement `compute_cation_size_variance()` in `code/descriptors.py`: Calculate variance of cation atomic radii. **Output**: Add column `cation_size_variance`. **Dependency**: T018a. (Addresses coverage-833ccaec)
- [ ] T018b-range-uncertainty [US1] **Compute Range Uncertainty**: Implement `compute_range_uncertainty()` in `code/descriptors.py`: Calculate range uncertainty based on extracted midpoint. **Dependency**: T018a. (Addresses coverage-833ccaec)
- [ ] T019a [US1] **Implement Compute Mean Atomic Radius**: Implement `compute_mean_atomic_radius()` in `code/descriptors.py`: Calculate mean atomic radius from stoichiometry. **Dependency**: T018a.
- [ ] T019b [US1] **Implement Compute Electronegativity Std**: Implement `compute_electronegativity_std()` in `code/descriptors.py`: Calculate standard deviation of electronegativity from stoichiometry. **Dependency**: T018a.
- [ ] T019c [US1] **Implement Compute Valence Electron Concentration**: Implement `compute_valence_electron_concentration()` in `code/descriptors.py`: Calculate VEC as total valence electrons (using `periodictable` library for lookup) divided by the total number of atoms in the formula unit. **Verification**: Add a unit test to verify the formula logic with a known example. **Dependency**: T018a.
- [ ] T060 [US2] **Implement Rare Class Exclusion Logic**: Implement `filter_rare_classes()` in `code/modeling.py` to drop classes with < 5 samples before splitting. **Output**: List of excluded classes. **Dependency**: T018a. (Addresses SC-004, T026)

---

## Phase 3: User Story 1 - Data Ingestion and Descriptor Computation (Priority: P1) 🎯 MVP

**Goal**: Ingest raw ceramic data, clean it, and compute elemental descriptors to produce a feature-rich dataset.

**Independent Test**: Run the pipeline on a sample of known entries.; verify output CSV contains `weibull_modulus` and at least 10 computed descriptors with no missing values for primary predictors.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T013 [P] [US1] Unit test for `chemparse` composition parsing in `tests/test_descriptors.py`
- [X] T014 [P] [US1] Unit test for imputation logic (group vs. global median) in `tests/test_ingestion.py`
- [X] T015 [P] [US1] Integration test for full ingestion pipeline on a small sample in `tests/integration/test_ingestion.py`

### Implementation for User Story 1

- [ ] T053 [US1] **Verify NIST URL**: Verify the reachability of the NIST Ceramic Data repository URL (` or direct CSV) before attempting to download. **Implementation**: Create `verify_nist_url()` in `code/ingestion.py` that uses `requests` to check status code 200 and content type. **Output**: Log result to `logs/url_verification.log`. **Dependency**: T009 (URL validation logic).
- [ ] T018c [US1] **Fetch Materials Project Data**: Implement `fetch_materials_project_data()` in `code/ingestion.py`: Use `requests` to query the Materials Project REST API (` Name or service not known)"))]) with API key from `.env`. **Target**: Fetch entries with `elasticity` and `composition` fields. **Query Params**: `?elasticity=true&composition=true`. **Fail Loudly**: If API returns no data or connection fails, raise `RuntimeError` with message "Materials Project fetch failed: {error}". **Output**: Save raw JSON to `data/raw/materials_project_raw.json`. (Addresses FR-001 coverage gap, corrected URL/logic, removed fallback)
- [ ] T018d-1 [US1] **Fetch NIST Data**: Implement `fetch_nist_data()` in `code/ingestion.py`: Use `requests` to fetch the specific NIST Ceramic Data CSV file (URL: `). **Target**: The NIST repository contains verified Weibull data. **Parsing Logic**: Parse the CSV directly. **Verification**: Assert file size > 0KB and row count > 0. **Fail Loudly**: If fetch fails or returns no Weibull data, raise `RuntimeError`. **Output**: Save raw CSV to `data/raw/nist_raw.csv`. **Dependency**: T053.
- [ ] T018d-1b [US1] **Parse NIST Data**: Implement `parse_nist_data()` in `code/ingestion.py`: Parse the raw data from T018d-1. **Verification**: Assert file size > 0KB and row count > 0. **Output**: Save parsed data to `data/processed/nist_parsed.csv`. **Dependency**: T018d-1.
- [ ] T018e [US1] **Fetch arXiv Data**: Implement `fetch_arxiv_data()` in `code/ingestion.py`: Use `arxiv` library to search for `all:ceramic AND all:weibull` (limit to 50 results). Use `pdfplumber` to extract tables from the top PDFs (sorted by relevance score descending). **Extraction Logic**: Select the **first valid table** where columns match expected headers: `['Composition', 'Weibull Modulus', 'N', 'Sintering Temp']` (or similar) and row count > 0. **Validation**: If `tabula-py` fails, fallback to `camelot-py`. **Fail Loudly**: If no table is found or extraction fails, raise `RuntimeError`. **Output**: Save raw JSON/CSV to `data/raw/arxiv_raw.json`.
- [ ] T018g [US1] **Fetch Curated Literature Data**: Implement `fetch_curated_literature_data()` in `code/ingestion.py`: Load the 'Curated Literature Dataset' from local file `data/raw/curated_literature.csv`. **Condition**: Execute **ONLY** if T018c, T018d-1, and T018e fail to return sufficient data. **Parsing Logic**: Parse CSV columns: `composition`, `weibull_modulus`, `sample_count`, `sintering_temp`. **Validation**: Must validate the source DOI/URL via T009b before loading. **Output**: Save raw JSON/CSV to `data/raw/curated_literature_raw.json`.
- [ ] T018f-1 [US1] **Implement Per-Entry Sample Count Filter**: Implement `filter_valid_sample_count()` in `code/ingestion.py`: Filter entries where `sample_count` (N) >= 30. **Logic**: Extract N from fields 'N', 'sample_size', 'n'. If absent, exclude entry. **Output**: Intermediate file `data/processed/step0_sample_count_filtered.csv`. **Dependency**: T018c, T018d-1b, T018e, T018g.
- [ ] T018f-2 [US1] **Implement Filter Stoichiometry**: Implement `filter_valid_stoichiometry()` in `code/ingestion.py`: Filter entries with valid, parsable stoichiometry. **Output**: Intermediate file `data/processed/step1_stoichiometry_filtered.csv`. **Dependency**: T018f-1.
- [ ] T018f-3 [US1] **Implement Handle Range Values**: Implement `handle_range_values()` in `code/ingestion.py`: Extract midpoint, set `is_range_flag`, compute `range_uncertainty`. **Output**: Intermediate file `data/processed/step2_range_handled.csv`. **Dependency**: T018f-2.
- [ ] T018f-4 [US1] **Implement Imputation**: Implement `impute_missing_params()` in `code/ingestion.py`: Impute missing `sintering_temp` with group median, add `is_imputed` flag. If group size < 5, use global median. **Dependency**: T018a, T018f-3.
- [ ] T018f-5 [US1] **Implement Handle Non-Stoichiometric Phases**: Implement `handle_non_stoichiometric()` in `code/ingestion.py`: Exclude entries where composition implies a non-stoichiometric phase that cannot be parsed. **Output**: Final cleaned file `data/processed/step_final_cleaned.csv`. **Dependency**: T018f-4.
- [ ] T017b [US1] **Implement Data Gap Validation & Report**: Implement `validate_data_gap()` in `code/ingestion.py`: Check total valid entries AFTER T018f-5 filtering. **Logic**: If total row count < 30, immediately call `generate_data_availability_report()`, log the report path, output "Power Limitation: Insufficient data (N < 30)" to stderr, and **generate the report file** `data/reports/data_availability_report.json` (schema defined in `code/contracts/ceramic_entry.schema.yaml`) before exiting with code 1. **Output**: Generate `data/reports/data_availability_report.json` and exit. **Dependency**: T018f-5. (Addresses SC-004)
- [ ] T020 [US1] **Implement Validate No Missing Primary Predictors**: Implement `validate_no_missing_primary_predictors()` in `code/ingestion.py`: Validate that essential descriptors have no missing values after cleaning and imputation. **Dependency**: T018f-5, T019a, T019b, T019c.
- [ ] T049 [US1] **Hard Fail on Synthetic Fallback**: Enforce a "Fail Loudly" policy. **Implementation**: Add a guard clause in `code/ingestion.py` at the start of the data loading function that raises `RuntimeError` with message "Synthetic data fallback detected: Failing loudly" if any synthetic data generation is attempted. **Dependency**: T018c, T018d-1, T018e, T018g.
- [ ] T054-stream-test [US1] **Test Streaming Logic**: Implement `test_streaming_ingestion()` in `tests/test_ingestion.py`: Create a mock dataset generator that yields > 100,000 rows. Verify that `fetch_materials_project_data` processes the data without exceeding 2GB RAM usage. **Dependency**: T055-stream. (Addresses Large Real Dataset Streaming Rule)
- [ ] T017c [US1] Create test data `data/raw/test_n.csv` with exactly 29 rows where the `sample_count` field is < 30. **Purpose**: Verify T017b halts when total row count < 30 even if individual sample counts are valid. (Clarified: T017b checks total rows, T018f checks sample_count field). **Dependency**: T017b.

---

## Phase 4: User Story 2 - Predictive Modeling and Cross-Validation (Priority: P2)

**Goal**: Train Random Forest and Gradient Boosting models with strict cross-validation to predict Weibull modulus.

**Independent Test**: Execute training on a subset; verify JSON output contains MAE, R², and stratified split report confirming distribution match.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US2] Unit test for stratified splitting logic in `tests/test_modeling.py` **Dependency**: T026.
- [ ] T024 [P] [US2] Unit test for baseline (global mean) predictor in `tests/test_modeling.py` **Dependency**: T028b.
- [ ] T025 [P] [US2] Implement integration test `tests/integration/test_modeling.py::test_5fold_cv_stratified_split` to verify the 5-fold CV workflow and **generate `data/results/cv_split_report.json`** containing stratification distribution metrics. **Dependency**: T026, T027b, T028.

### Implementation for User Story 2

- [ ] T026 [US2] Implement `prepare_splits()` in `code/modeling.py`: Stratified split based on `primary_anion_cation_group`. **Logic**: If N >= 50, use Stratified 5-fold CV. If 30 <= N < 50, use Stratified 80/20 Hold-out (per SC-004). If any class has < 5 samples, exclude from stratification (Rare Class Handling). **Dependency**: T018f-5, T060.
- [ ] T027a [US2] Define `hyperparameter_search_space` in `code/modeling.py`: Define the constrained set of hyperparameter combinations for RF and GBM (a limited number of combinations).
- [ ] T027b [US2] Implement `train_models()` in `code/modeling.py`: Train RF and GBM using the defined search space. **Critical**: Store feature importance scores from **each CV fold** in `data/results/fold_importances.json`. **Dependency**: T027a, T026.
- [ ] T029 [US2] Implement `run_permutation_test()` in `code/modeling.py`: Perform a permutation test to determine statistical significance of model improvement over the baseline. **Logic**: 1) Calculate MAE improvement percentage (must be >= 10% for SC-001). 2) Calculate p-value (must be < 0.05) using 1000 iterations, **seed=42** (for shuffling), and shuffling the target variable `y` (weibull_modulus). **Null Hypothesis**: Shuffle weibull_modulus values (y), **retrain the model** on the shuffled data for each iteration, and calculate MAE. **Reporting**: Generate `data/results/permutation_test_report.json` containing p-value, MAE improvement, and separate verdicts (e.g., "MAE_PASS", "SIG_PASS"). **Gating**: If p >= 0.05, log "Model not statistically significant" but **DO NOT exit**; continue to next tasks and flag the model as 'Not Significant'. **Dependency**: T027b.
- [ ] T027d [US2] **Save Best Model**: Save the best performing model to `data/models/best_model.pkl` **regardless of T029 outcome** to ensure reproducibility. If T029 fails, log "Model saved for exploratory analysis". **Dependency**: T027b.
- [ ] T028b [US2] Implement `run_baseline_predictor()` in `code/modeling.py`: Create a simple model that predicts the global mean Weibull modulus for all test samples and save the MAE. **Dependency**: T026.
- [ ] T028 [US2] Implement `evaluate_models()` in `code/modeling.py`: Calculate MAE, R², and compare against global mean baseline.
- [ ] T030b [US2] **Train Leakage Check Model**: Train a second Random Forest model excluding the 'primary_anion_cation_group' feature. **Dependency**: T027b (Run regardless of T029 outcome). **Output**: Save model and metrics to `data/models/leakage_check_model.pkl`.
- [ ] T030 [US2] **Implement Descriptor Sufficiency Check**: Implement `check_descriptor_sufficiency()` in `code/diagnostics.py`: Perform a sufficiency check by comparing model performance with and without the 'primary_anion_cation_group' feature. **Logic**: Read `data/models/leakage_check_model.pkl` and compare MAE from T027b. **Condition**: If MAE increases by < 10% (performance drop is small), flag "Potential Leakage" (model failed without proxy). If MAE increases by >= 10%, flag "DESCRIPTORS SUFFICIENT". **Output**: Generate `data/results/descriptor_sufficiency.json`. (Addresses FR-005.5, Plan Phase 2 Task 2.5). **Dependency**: T027b, T030b.
- [ ] T031 [US2] Generate `data/results/model_metrics.json` with all scores and stratification reports
- [ ] T050 [US2] **Add Runtime Enforcement**: Wrap the entire `code/modeling.py` execution in a timeout handler to ensure completion within 6 hours. **Implementation**: Use `multiprocessing` to enforce a time limit on the full pipeline execution (ingestion to reporting). **Dependency**: None (wraps full pipeline). **Action**: If timeout exceeded, kill process and log `TimeoutExceededError`. **Logging**: Log the total runtime duration upon completion or timeout.

---

## Phase 5: User Story 3 - Feature Importance and Mechanistic Interpretation (Priority: P3)

**Goal**: Extract SHAP values, rank features, and interpret results against fracture mechanics principles.

**Independent Test**: Run analysis on best model; verify output lists top descriptors, includes correlation matrix, and flags collinearity.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T033 [P] [US3] Unit test for VIF calculation in `tests/test_diagnostics.py` **Dependency**: T037.
- [ ] T034 [P] [US3] Unit test for SHAP value aggregation in `tests/test_report.py` **Dependency**: T036b.
- [ ] T035 [P] [US3] Integration test for full interpretability pipeline in `tests/integration/test_interpretability.py` **Dependency**: T036b, T037, T038, T039, T040, T041.

### Implementation for User Story 3

- [ ] T036a [US3] **Compute SHAP per Fold**: Implement `calculate_shap_per_fold()` in `code/diagnostics.py`: Generate SHAP values for the best-performing model **across all cross-validation folds**. **Output**: Return a list of SHAP value arrays, one per fold. **Dependency**: T027b.
- [ ] T036b [US3] **Aggregate SHAP Values**: Implement `aggregate_shap_values()` in `code/diagnostics.py`: Aggregate the per-fold SHAP values from T036a. **Output**: Return aggregated SHAP summary. **Dependency**: T036a.
- [ ] T037 [US3] Implement `calculate_vif()` in `code/diagnostics.py`: Compute VIF for all predictors and flag highly correlated features.
- [ ] T038 [US3] Implement `group_correlated_features()` in `code/diagnostics.py`: Cluster highly correlated features for interpretive grouping.
- [ ] T038b [US3] Implement `report_cluster_importance()` in `code/report.py`: Calculate and report aggregate importance scores for correlated feature clusters.
- [ ] T039 [US3] Implement `calculate_cv_stability()` in `code/report.py`: Calculate Coefficient of Variation (CV) for **top 5 feature importance scores** **across cross-validation folds** by aggregating the per-fold feature importance scores from T036. **Logic**: Calculate the *mean* importance of the top 5 features across folds, then compute the CV of these mean values. **Dependency**: T036b. (Addresses SC-002)
- [ ] T040 [US3] Implement `generate_interpretation()` in `code/report.py`: Rank features, map descriptors to physical mechanisms, and include correlation matrix.
- [ ] T041 [US3] **Execute & Generate Interpretability Artifacts**: Execute the analysis and generate SHAP summary plot (`data/artifacts/shap_summary.png`), feature ranking table (`data/results/feature_ranking.csv`), and stability metrics (`data/results/stability_metrics.json`). **Dependency**: T036b-T040.

---

## Phase 6: Reporting & Compliance (Polish)

**Purpose**: Finalize reports, ensure compliance, and update project state.

- [ ] T043 [P] Implement `generate_final_report()` in `code/report.py`: Combine metrics, SHAP analysis, and disclaimers. **Dependency**: T031, T041, T017b (if triggered).
- [ ] T044 [P] Execute `code/hash_artifacts.py` to update project state with new content hashes for all files in `data/` and `code/`.
- [ ] T045 [P] Run `bash scripts/validate_quickstart.sh` to validate the quickstart guide against the implemented pipeline.
- [ ] T051 [P] **Final Compliance Audit**: Run a script to ensure all requirements are met.
- [ ] T017c [US1] Create test data `data/raw/test_n.csv` with exactly 29 rows where the `sample_count` field is >= 30. **Purpose**: Verify T017b halts when total row count < 30 even if individual sample counts are valid. (Clarified: T017b checks total rows, T018f checks sample_count field).

---

## Phase 7: Revision & Stability (Post-Analysis)

**Purpose**: Address specific reviewer concerns from prior analysis rounds to ensure robustness and correctness.

- [ ] T054 [US1] **Verify Real Data Source Adoption**: If execution feedback provides a "VERIFIED REAL DATA SOURCE" (e.g., specific package + recipe), update `code/ingestion.py` to exclusively use that source. Remove all hand-rolled `load_dataset` or guessed URL fallbacks. **Dependency**: Execution feedback. (Addresses "If a verified real data source is injected, USE it").
- [ ] T056 [US2] **Enforce Collinearity Clustering in SHAP**: Ensure `group_correlated_features()` (T038) is called *before* ranking features in `generate_interpretation()`. **Logic**: If VIF > 5, group features and report *aggregate* importance for the cluster, not individual ranks. **Dependency**: T037, T040. (Addresses FR-007, T038 logic).
- [ ] T057 [US2] **Verify Permutation Test Robustness**: Ensure `run_permutation_test()` (T029) uses a sufficient number of iterations (>= 1000) and a fixed seed (42) for reproducibility. **Verification**: Check `data/results/permutation_test_report.json` for `iterations` and `seed` fields. (Addresses SC-001, T029).
- [ ] T058 [US3] **Validate CV Calculation Logic**: Ensure `calculate_cv_stability()` (T039) computes CV on the *mean* importance of the top 5 features *across folds*, not on the raw per-fold values. **Verification**: Unit test `tests/test_report.py::test_cv_stability_logic`. (Addresses SC-002, T039).
- [ ] T059 [US1] **Add Range Uncertainty to Feature Set**: Ensure `compute_range_uncertainty()` (T018b-range-uncertainty) is called and the resulting column is included in the final feature set for modeling. **Verification**: Check `data/processed/step_final_cleaned.csv` for `range_uncertainty` column. (Addresses Edge Case: Range Data Dominance).