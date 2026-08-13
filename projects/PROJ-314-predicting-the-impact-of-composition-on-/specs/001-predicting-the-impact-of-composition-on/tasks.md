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
- [X] T002 Initialize Python 3.11 project with requirements.txt (pandas, scikit-learn, shap, chemparse, requests, pyyaml, scipy, pymatgen, arxiv, pdfplumber, datasets)
- [X] T003 [P] Configure linting (ruff) and formatting (black)
- [X] T016a [P] Generate `quickstart.md` in `specs/001-predict-weibull-modulus/`: Document step-by-step setup, data fetch, and pipeline execution instructions. Must include sections: 1. Prerequisites & Install, 2. Data Fetch (MP, NIST, arXiv), 3. Running the Pipeline, 4. Verifying Outputs. Must be generated before T045 validation. (Addresses Plan Phase 1, Task 1.5 & Coverage Gaps)
- [X] T016b [P] Generate `docs/data_gap_protocol.md`: Document the exact steps for the Data Gap Protocol, including the schema for `data/reports/data_availability_report.json` and the halting logic. Must be generated before T047 update. (Addresses Plan Phase 1, Task 1.5 & Coverage Gaps)
- [X] T016c [P] Define `CeramicEntry` and `DescriptorSet` schemas in `code/contracts/schemas.py` using Pydantic and export to YAML files `ceramic_entry.schema.yaml` and `model_result.schema.yaml` in `code/contracts/`. (Addresses Plan Phase 1, Task 1.5)
- [X] T016c-3 [P] Generate `data-model.md` in `specs/001-predict-weibull-modulus/`: Document the `CeramicEntry` and `DescriptorSet` entities, their relationships, and validation rules. Must include YAML schema examples and field type definitions. (Addresses Plan Phase 1, Task 1.5)
- [X] T006 [P] Implement base `CeramicEntry` class in `code/__init__.py` (Dependency: T016c-3 for type hints)
- [X] T007 [P] Implement base `DescriptorSet` class in `code/__init__.py` (Dependency: T016c-3 for type hints)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T012a [P] **Validate** `ceramic_entry.schema.yaml` in `code/contracts/`: Ensure the schema generated in T016c is correctly formatted and contains all required fields: `composition`, `weibull_modulus`, `sample_count`, `is_range_flag`, `range_original`, `primary_anion_cation_group`, `sintering_temp`, `is_imputed`, `mean_atomic_radius`, `electronegativity_std`, `valence_electron_concentration`. (Addresses Plan Phase 1, Task 1.5; consumes T016c output)
- [X] T012b [P] **Validate** `model_result.schema.yaml` in `code/contracts/`: Ensure the schema generated in T016c is correctly formatted and contains all required fields: `model_type`, `mae`, `r_squared`, `feature_importance_ranking`, `cv_stability_scores`. (Addresses Plan Phase 1, Task 1.5; consumes T016c output)
- [X] T022 [P] Create `code/physics_mappings.py` with dictionary mapping descriptors to physical mechanisms (e.g., "cation_size_variance" -> "Grain boundary stability") to support US3 (Moved to Phase 2 to ensure availability before US3 work)
- [X] T004 Setup `data/raw/`, `data/processed/`, and `data/artifacts/` directories
- [X] T005 [P] Implement `code/hash_artifacts.py` for versioning and checksumming (Constitution Principle V)
- [X] T008 [P] Setup `code/ingestion.py` skeleton file structure
- [X] T009 [P] Implement URL validation logic in `code/ingestion.py`
- [X] T009b [P] Implement `validate_source_citations()` in `code/ingestion.py`: Validate source URLs/DOIs against primary sources (Constitution Principle II) by checking title overlap >= 0.7 and verifying reachability; log failures to `logs/citation_validation.log`. **Verification**: Ensure `logs/citation_validation.log` is created and populated during the first validation run. (Addresses Plan Phase 0, Task 0.3)
- [X] T010 [P] Configure logging infrastructure in `code/__init__.py` (Ensures `logs/` directory exists for T009b)
- [X] T010b [P] Verify `logs/citation_validation.log` creation: Execute `python code/ingestion.py --validate-dummy` with `dummy_urls=['https://example.com']`. Assert that `logs/citation_validation.log` exists and contains at least one entry with format `INFO: Citation validation for {url}: {status}` where status is not empty. (Addresses T009b verification gap)
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

- [ ] T053 [US1] **Implement NIST URL Verification**: Verify the reachability and content of the NIST ceramic data URL (`) before attempting to download it. **Implementation**: Create `verify_nist_url()` in `code/ingestion.py` that sends a HEAD/GET request, checks for HTTP 200, and verifies the content type is `text/html` (landing page) or `text/csv` if a direct link is found. **Output**: Log result to `logs/url_verification.log`. **Dependency**: T009 (URL validation logic).
- [ ] T018c [US1] **Fetch Materials Project Data**: Implement `fetch_materials_project_data()` in `code/ingestion.py`: Use `pymatgen` (mp-api) to fetch ceramic property data. **Endpoint**: Use `MPRestClient().get_entries(elements=['Al', 'Si', 'O', 'Ti', 'Zr', 'Zn', 'Nb', 'Ta', 'Hf', 'Mo', 'W', 'V', 'Cr', 'Mn', 'Fe', 'Co', 'Ni', 'Cu', 'Ga', 'In', 'Sn', 'Sb', 'Te', 'Bi', 'Pb', 'S', 'Se', 'F', 'Cl', 'Br', 'I'], properties=['formation_energy_per_atom'])`. Query: Fetch entries for known ceramic elements. **Post-Processing**: Filter for entries where `weibull_modulus` field is explicitly present and non-null. **Fail Loudly**: If API returns no data or connection fails, raise `RuntimeError` with message "Materials Project fetch failed: {error}". **Output**: Save raw JSON to `data/raw/materials_project_raw.json`. (Addresses FR-001 coverage gap, corrected URL/logic, removed fallback)
- [ ] T018d-1 [US1] **Fetch NIST Data**: Implement `fetch_nist_data()` in `code/ingestion.py`: Use `requests` to fetch NIST ceramic data from verified URL: `. **Parsing Logic**: Parse the landing page or specific ceramic dataset endpoint if available. **Verification**: Assert file size > 0KB and row count > 0. **Fail Loudly**: If fetch fails or returns no Weibull data, raise `RuntimeError`. **Output**: Save raw JSON/CSV to `data/raw/nist_raw.json`. **Dependency**: T053.
- [ ] T018d-2 [US1] **Parse NIST Data**: Implement `parse_nist_data()` in `code/ingestion.py`: Parse the raw data from T018d-1. **Verification**: Assert file size > 0KB and row count > 0. **Output**: Save parsed data to `data/processed/nist_parsed.csv`. **Dependency**: T018d-1.
- [ ] T018e [US1] **Fetch arXiv Data**: Implement `fetch_arxiv_data()` in `code/ingestion.py`: Use `arxiv` library to search for `all:ceramic AND all:weibull` (limit a representative sample). Use `pdfplumber` to extract tables from the top few PDFs returned by the search (sorted by relevance). **Extraction Logic**: Use regex patterns `r"(Al|Si|O|Ti|Zr|Zn|Nb|Ta|Hf|Mo|W|V|Cr|Mn|Fe|Co|Ni|Cu|Ga|In|Sn|Sb|Te|Bi|Pb|S|Se|F|Cl|Br|I)"` for composition and `r"(Weibull|Modulus)"` for target. Extract the **first valid table** found in the PDF where columns match expected headers and row count > 0. **Fail Loudly**: If no table is found or extraction fails, raise `RuntimeError`. Do NOT skip rows silently. **Output**: Save raw JSON/CSV to `data/raw/arxiv_raw.json`. (Addresses FR-001 coverage gap, corrected logic, removed silent fallback)
- [ ] T018g [US1] **Fetch Curated Literature Data**: Implement `fetch_curated_literature_data()` in `code/ingestion.py`: Fetch the 'Curated Literature Dataset' from verified URL: `. **Parsing Logic**: Parse CSV columns: `composition`, `weibull_modulus`, `sample_count`, `sintering_temp`. **Fail Loudly**: If fetch fails or no data is found, raise `RuntimeError`. **Trigger Logic**: This task is ONLY executed if (T018c, T018d, AND T018e ALL fail) OR (Total valid entries N < 30 after primary fetches). **Output**: Save raw JSON/CSV to `data/raw/curated_literature_raw.json`. (Addresses Plan Phase 0, Task 0.2 fallback requirement)
- [ ] T018f-1 [US1] **Filter Valid Stoichiometry**: Implement `filter_valid_stoichiometry()` in `code/ingestion.py`: Filter entries with valid composition strings. **Output**: Save to `data/processed/step1_cleaned.csv`. **Dependency**: T018c, T018d-2, T018e, T018g.
- [ ] T018f-2 [US1] **Handle Range Values**: Implement `handle_range_values()` in `code/ingestion.py`: Extract midpoint, set `is_range_flag`, store original string. **Output**: Save to `data/processed/step2_range.csv`. **Dependency**: T018f-1.
- [ ] T018f-3 [US1] **Impute Missing Params**: Implement `impute_missing_params()` in `code/ingestion.py`: Impute `sintering_temp` with group median or global median. **Output**: Save to `data/processed/step3_imputed.csv`. **Dependency**: T018f-2.
- [ ] T018f-4 [US1] **Handle Non-Stoichiometric Phases**: Implement `handle_non_stoichiometric_phases()` in `code/ingestion.py`: Remove invalid entries. **Output**: Save to `data/processed/step4_final.csv`. **Dependency**: T018f-3.
- [ ] T017 [US1] **Implement Data Gap Validation & Report**: Implement `validate_data_gap()` in `code/ingestion.py`: Check total valid entries after fetching and cleaning. **Logic**: If N < 30, immediately call `generate_data_availability_report()`, log the report path, output "Power Limitation: Insufficient data (N < 30)" to stderr, and exit with code 1. **Output**: Generate `data/reports/data_availability_report.json` inline before exit. **Dependency**: T018f-4.
- [ ] T018a [US1] **Implement Derive Primary Anion/Cation Group**: Implement `derive_primary_anion_cation_group()` in `code/ingestion.py`: Parse the `composition` string using `chemparse` to identify the primary anion and cation groups (e.g., 'O-Al' for Alumina). Create a new column `primary_anion_cation_group`. **Dependency**: T018f-4.
- [ ] T018b-impl [US1] **Implement Compute Range Uncertainty**: Implement `compute_range_uncertainty()` in `code/descriptors.py`: Calculate range uncertainty based on extracted midpoint. **Dependency**: T018f-2.
- [X] T019a [US1] **Implement Compute Mean Atomic Radius**: Implement `compute_mean_atomic_radius()` in `code/descriptors.py`: Calculate mean atomic radius from stoichiometry. **Dependency**: T018a, T018f-4.
- [X] T019b [US1] **Implement Compute Electronegativity Std**: Implement `compute_electronegativity_std()` in `code/descriptors.py`: Calculate standard deviation of electronegativity from stoichiometry. **Dependency**: T018a, T018f-4.
- [X] T019c [US1] **Implement Compute Valence Electron Concentration**: Implement `compute_valence_electron_concentration()` in `code/descriptors.py`: Calculate VEC as total valence electrons divided by the total number of atoms in the formula unit. **Dependency**: T018a, T018f-4.
- [X] T020 [US1] **Implement Validate No Missing Primary Predictors**: Implement `validate_no_missing_primary_predictors()` in `code/ingestion.py`: Validate that essential descriptors have no missing values after cleaning and imputation. **Dependency**: T018f-4, T019a, T019b, T019c.
- [ ] T052 [US1] **Memory Check**: Implement memory usage check to prevent exceeding the memory limit. **Implementation**: Use `psutil` to monitor RSS and raise `MemoryError` if > 6GB. **Output**: Log to `logs/memory_monitor.log`. **Dependency**: T017 (Gate Pass). **Threshold**: Use `config.MEMORY_LIMIT_GB` (default 6GB if env var unset). **Placement**: Wrap ingestion tasks T018c-e.
- [X] T049 [US1] **Hard Fail on Synthetic Fallback**: Enforce a "Fail Loudly" policy. **Implementation**: Add a guard clause in `code/ingestion.py` at the start of the data loading function that raises `RuntimeError` with message "Synthetic data fallback detected: Failing loudly" if any synthetic data generation is attempted. **Dependency**: T018c, T018d, T018e, T018g.
- [ ] T054 [US1] **Implement Streaming Data Loader**: Implement `load_data_streaming()` in `code/ingestion.py` to handle large datasets by processing in chunks using `datasets.load_dataset(..., streaming=True)` or `pandas.read_csv(chunksize=...)`. **Logic**: If the dataset file size (`os.path.getsize()`) exceeds a substantial threshold, automatically switch to streaming mode to accumulate statistics without loading the full dataset into RAM. **Fallback**: If streaming is not feasible (e.g., non-standard file format), use a deterministic random sample with a fixed seed (`random.seed(42); random.sample(...)`). **Dependency**: T018f-4. (Addresses "Large real datasets: STREAM" rule).

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
- [X] T027b [US2] Implement `train_models()` in `code/modeling.py`: Train RF and GBM using the defined search space. **Critical**: Store feature importance scores from **each CV fold** in `data/results/fold_importances.json`. **Dependency**: T027a.
- [ ] T029 [US2] Implement `run_permutation_test()` in `code/modeling.py`: Perform a permutation test to determine statistical significance of model improvement over the baseline. **Logic**: 1) Calculate MAE improvement percentage (must be >= 10% for SC-001). 2) Calculate p-value (must be < 0.05) using 1000 iterations and seed=42. **Reporting**: Generate `data/results/permutation_test_report.json` containing p-value, MAE improvement, and separate verdicts (e.g., "MAE_PASS", "SIG_PASS"). **Gating**: If not significant, flag as "Not Statistically Significant" and prevent downstream model saving. **Dependency**: T027b.
- [ ] T027d [US2] **Save Best Model**: Save the best performing model to `data/models/best_model.pkl` ONLY if T029 reports statistical significance (p < 0.05). If T029 fails, skip save and log "Model not statistically significant; skipping save". **Dependency**: T029.
- [X] T028b [US2] Implement `run_baseline_predictor()` in `code/modeling.py`: Create a simple model that predicts the global mean Weibull modulus for all test samples and save the MAE. **Dependency**: T026.
- [X] T028 [US2] Implement `evaluate_models()` in `code/modeling.py`: Calculate MAE, R², and compare against global mean baseline.
- [ ] T030b [US2] **Train Leakage Check Model**: Train a second Random Forest model excluding the 'primary_anion_cation_group' feature. **Dependency**: T027d (Skip if T027d skipped). **Output**: Save model and metrics to `data/models/leakage_check_model.pkl`.
- [ ] T030 [US2] **Implement Leakage Check**: Implement `check_leakage()` in `code/diagnostics.py`: Perform a leakage check by comparing model performance with and without the 'primary_anion_cation_group' feature. **Logic**: Read `data/models/leakage_check_model.pkl` and compare metrics from T027b. If performance drops by **less than 10%**, flag "Potential Leakage" with exact warning message. **Output**: Generate `data/results/leakage_check.json`. (Addresses FR-005.5).
- [X] T031 [US2] Generate `data/results/model_metrics.json` with all scores and stratification reports
- [X] T032 [US2] Implement `filter_rare_classes()` in `code/modeling.py` to drop classes with < 5 samples before splitting, and verify via `tests/test_modeling.py::test_rare_class_exclusion`
- [ ] T050 [US2] **Add Runtime Enforcement**: Wrap the entire `code/modeling.py` execution in a timeout handler to ensure completion within 6 hours. **Implementation**: Use `multiprocessing` to enforce a time limit on the full pipeline execution (ingestion to reporting). **Dependency**: None (wraps full pipeline). **Action**: If timeout exceeded, kill process and log `TimeoutExceededError`. **Logging**: Log the total runtime duration upon completion or timeout. (Consolidated from T050/T057).

---

## Phase 5: User Story 3 - Feature Importance and Mechanistic Interpretation (Priority: P3)

**Goal**: Extract SHAP values, rank features, and interpret results against fracture mechanics principles.

**Independent Test**: Run analysis on best model; verify output lists top descriptors, includes correlation matrix, and flags collinearity.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T033 [P] [US3] Unit test for VIF calculation in `tests/test_diagnostics.py`
- [X] T034 [P] [US3] Unit test for SHAP value aggregation in `tests/test_report.py`
- [X] T035 [P] [US3] Integration test for full interpretability pipeline in `tests/integration/test_interpretability.py`

### Implementation for User Story 3

- [X] T036a [US3] **Compute SHAP per Fold**: Implement `calculate_shap_per_fold()` in `code/diagnostics.py`: Generate SHAP values for the best-performing model **across all cross-validation folds**. **Output**: Return a list of SHAP value arrays, one per fold. **Dependency**: T027d.
- [X] T036b [US3] **Aggregate SHAP Values**: Implement `aggregate_shap_values()` in `code/diagnostics.py`: Aggregate the per-fold SHAP values from T036a. **Output**: Return aggregated SHAP summary. **Dependency**: T036a.
- [X] T037 [US3] Implement `calculate_vif()` in `code/diagnostics.py`: Compute VIF for all predictors and flag highly correlated features.
- [X] T038 [US3] Implement `group_correlated_features()` in `code/diagnostics.py`: Cluster highly correlated features for interpretive grouping.
- [X] T038b [US3] Implement `report_cluster_importance()` in `code/report.py`: Calculate and report aggregate importance scores for correlated feature clusters.
- [X] T039 [US3] Implement `calculate_cv_stability()` in `code/report.py`: Calculate Coefficient of Variation (CV) for top features **across cross-validation folds** by aggregating the per-fold feature importance scores from T036. **Dependency**: T036b.
- [X] T040 [US3] Implement `generate_interpretation()` in `code/report.py`: Rank features, map descriptors to physical mechanisms, and include correlation matrix.
- [ ] T041 [US3] **Execute & Generate Interpretability Artifacts**: Execute the analysis and generate SHAP summary plot (`data/artifacts/shap_summary.png`), feature ranking table (`data/results/feature_ranking.csv`), and stability metrics (`data/results/stability_metrics.json`). **Dependency**: T036b-T040.

---

## Phase 6: Reporting & Compliance (Polish)

**Purpose**: Finalize reports, ensure compliance, and update project state.

- [X] T043 [P] Implement `generate_final_report()` in `code/report.py`: Combine metrics, SHAP analysis, and disclaimers.
- [X] T044 [P] Execute `code/hash_artifacts.py` to update project state with new content hashes for all files in `data/` and `code/`.
- [X] T045 [P] Run `bash scripts/validate_quickstart.sh` to validate the quickstart guide against the implemented pipeline.
- [X] T051 [P] **Final Compliance Audit**: Run a script to ensure all requirements are met.
- [X] T017c [US1] Create test data `data/raw/test_n.csv` with exactly 29 rows where the `sample_count` field is >= 30. **Purpose**: Verify T017 halts when total row count < 30 even if individual sample counts are valid. (Clarified: T017 checks total rows, T018f checks sample_count field).