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

- [ ] T001a [P] Create `projects/PROJ-314-predicting-the-impact-of-composition-on-/data/raw/` directory
- [ ] T001b [P] Create `projects/PROJ-314-predicting-the-impact-of-composition-on-/data/processed/` directory
- [ ] T001c [P] Create `projects/PROJ-314-predicting-the-impact-of-composition-on-/data/artifacts/` directory
- [ ] T001d [P] Create `projects/PROJ-314-predicting-the-impact-of-composition-on-/code/` directory
- [X] T002 Initialize Python 3.11 project with requirements.txt (pandas, scikit-learn, shap, chemparse, requests, pyyaml, scipy, datasets, huggingface_hub, arxiv, pdfplumber)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) - create `pyproject.toml` with ruff/black config
- [ ] T016a [P] Generate `quickstart.md` in `specs/001-predict-weibull-modulus/`: Document step-by-step setup, data fetch, and pipeline execution instructions. Must include sections: 1. Prerequisites & Install, 2. Data Fetch (HuggingFace 'materials-science/ceramic-reliability'), 3. Running the Pipeline, 4. Verifying Outputs. Must be generated before T045 validation. (Addresses Plan Phase 1, Task 1.5 & Coverage Gaps)
- [ ] T016b [P] [P] Generate `docs/data_gap_protocol.md`: Document the exact steps for the Data Gap Protocol, including the schema for `data/reports/data_availability_report.json` and the halting logic. Must be generated before T047 update. (Addresses Plan Phase 1, Task 1.5 & Coverage Gaps)
- [ ] T016c [P] **Define and Export Schemas**: Define `CeramicEntry` and `DescriptorSet` Pydantic schemas in `code/contracts/schemas.py` and export them to `ceramic_entry.schema.yaml` and `model_result.schema.yaml` in `code/contracts/`. **Idempotency**: This task MUST be idempotent; running it multiple times must overwrite the YAML files with the current definition without corruption. **Verification**: Add a post-run check to assert that both YAML files exist and are valid YAML. (Addresses Plan Phase 1, Task 1.5)
- [ ] T016c-3a [P] Generate `data-model.md` in `specs/001-predict-weibull-modulus/`: Document the `CeramicEntry` and `DescriptorSet` entities, their relationships, and validation rules. Must include YAML schema examples and field type definitions. **Dependency**: T016c. (Addresses Plan Phase 1, Task 1.5)
- [ ] T004 [P] Setup `data/raw/`, `data/processed/`, and `data/artifacts/` directories (Refactored into T001a-d)
- [X] T005 [P] Implement `code/hash_artifacts.py` for versioning and checksumming (Constitution Principle V)
- [X] T008 [P] Setup `code/ingestion.py` skeleton file structure
- [X] T009 [P] Implement URL validation logic in `code/ingestion.py`
- [X] T009b [P] Implement `validate_source_citations()` in `code/ingestion.py`: Validate source URLs/DOIs against primary sources (Constitution Principle II) by checking title overlap >= 0.7 and verifying reachability; log failures to `logs/citation_validation.log`. **Verification**: Ensure `logs/citation_validation.log` is created and populated during the first validation run. **Dependency**: T010. (Addresses Plan Phase 0, Task 0.3)
- [X] T010 [P] Configure logging infrastructure in `code/__init__.py` (Ensures `logs/` directory exists for T009b)
- [X] T010b [P] Verify `logs/citation_validation.log` creation: Execute `python code/ingestion.py --validate-dummy` with `dummy_urls=['https://example.com']`. Assert that `logs/citation_validation.log` exists and contains at least one entry with format `INFO: Citation validation for {url}: {status}` where status is not empty. (Addresses T009b verification gap)
- [X] T011 [P] Setup environment configuration management: Create `.env.example`, implement `load_env()` in `code/__init__.py`, and add unit test `tests/test_config.py::test_env_loading`
- [ ] T052-config [P] **Memory Configuration**: Implement `get_memory_limit()` in `code/config.py` returning `config.MEMORY_LIMIT_GB` (default 6GB). Add helper `check_memory_usage()` to `code/utils.py` using `psutil`. **Dependency**: T004. (Addresses executability-a6ec9e53)
- [ ] T055-stream [P] **Streaming Data Loader**: Implement `load_dataset_streaming()` in `code/ingestion.py` using `datasets.load_dataset(..., streaming=True)`. **Logic**: If the dataset size exceeds 2GB (configurable), use the streaming iterator to process rows one-by-one or in chunks, accumulating statistics online without loading the full dataset into RAM. **Fallback**: Only if streaming fails (e.g., dataset not streamable) AND the dataset is < 2GB, fall back to standard loading. **Fail Loudly**: If the dataset is > 2GB and streaming is not supported, raise `RuntimeError` "Dataset too large for memory and streaming not supported". **Output**: Log memory usage peaks to `logs/memory_monitor.log`. **Dependency**: T052-config. (Addresses Large Real Dataset Streaming Rule)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T012a [P] **Validate** `ceramic_entry.schema.yaml` in `code/contracts/`: Ensure the schema generated in T016c is correctly formatted and contains all required fields: `composition`, `weibull_modulus`, `sample_count`, `is_range_flag`, `range_original`, `primary_anion_cation_group`, `sintering_temp`, `is_imputed`, `mean_atomic_radius`, `electronegativity_std`, `valence_electron_concentration`. (Addresses Plan Phase 1, Task 1.5; consumes T016c output)
- [ ] T012b [P] **Validate** `model_result.schema.yaml` in `code/contracts/`: Ensure the schema generated in T016c is correctly formatted and contains all required fields: `model_type`, `mae`, `r_squared`, `feature_importance_ranking`, `cv_stability_scores`. (Addresses Plan Phase 1, Task 1.5; consumes T016c output)
- [X] T022 [P] Create `code/physics_mappings.py` with dictionary mapping descriptors to physical mechanisms (e.g., "cation_size_variance" -> "Grain boundary stability") to support US3 (Moved to Phase 2 to ensure availability before US3 work)
- [ ] T006 [P] [US1] Implement base `CeramicEntry` class in `code/entities.py` (Dependency: T012a for type hints)
- [ ] T007 [P] [US1] Implement base `DescriptorSet` class in `code/entities.py` (Dependency: T012b for type hints)

---

## Phase 3: User Story 1 - Data Ingestion and Descriptor Computation (Priority: P1) 🎯 MVP

**Goal**: Ingest raw ceramic data, clean it, and compute elemental descriptors to produce a feature-rich dataset.

**Independent Test**: Run the pipeline on a sample of known entries.; verify output CSV contains `weibull_modulus` and at least 10 computed descriptors with no missing values for primary predictors.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T013 [P] [US1] Unit test for `chemparse` composition parsing in `tests/test_descriptors.py`
- [X] T014 [P] [US1] Unit test for imputation logic (group vs. global median) in `tests/test_ingestion.py`
- [X] T015 [P] [US1] Integration test for full ingestion pipeline on a small sample in `tests/integration/test_ingestion.py`

### Implementation for User Story 1

- [ ] T053 [US1] **Implement NIST URL Verification**: Verify the reachability and content of the HuggingFace dataset 'materials-science/ceramic-reliability' before attempting to download it. **Implementation**: Create `verify_hf_dataset()` in `code/ingestion.py` that uses `huggingface_hub` to check dataset existence and metadata. **Output**: Log result to `logs/url_verification.log`. **Dependency**: T009 (URL validation logic).
- [ ] T018c [US1] **Fetch Materials Project Data**: Implement `fetch_materials_project_data()` in `code/ingestion.py`: Use `datasets.load_dataset('materials-science/ceramic-reliability', split='train', streaming=True)` to fetch ceramic property data including Weibull modulus. **Note**: This dataset aggregates data from MP, NIST, and literature. **Fail Loudly**: If API returns no data or connection fails, raise `RuntimeError` with message "Materials Project fetch failed: {error}". **Output**: Save raw JSON to `data/raw/materials_project_raw.json`. (Addresses FR-001 coverage gap, corrected URL/logic, removed fallback, implements streaming)
- [ ] T018d-1 [US1] **Fetch NIST Data**: Implement `fetch_nist_data()` in `code/ingestion.py`: Use `datasets.load_dataset('materials-science/ceramic-reliability', split='train', streaming=True)` to fetch NIST ceramic data. **Target**: The HuggingFace dataset contains the verified Weibull data. **Parsing Logic**: Parse the dataset directly. **Verification**: Assert file size > 0KB and row count > 0. **Fail Loudly**: If fetch fails or returns no Weibull data, raise `RuntimeError`. **Output**: Save raw JSON/CSV to `data/raw/nist_raw.json`. **Dependency**: T053.
- [ ] T018d-1b [US1] **Parse NIST Data**: Implement `parse_nist_data()` in `code/ingestion.py`: Parse the raw data from T018d-1. **Verification**: Assert file size > 0KB and row count > 0. **Output**: Save parsed data to `data/processed/nist_parsed.csv`. **Dependency**: T018d-1.
- [ ] T018e [US1] **Fetch arXiv Data**: Implement `fetch_arxiv_data()` in `code/ingestion.py`: Use `arxiv` library to fetch data from 3 specific verified DOIs: [DOI1, DOI2, DOI3] (to be filled from research.md). Use `pdfplumber` or `tabula-py` to extract tables from the PDFs. **Extraction Logic**: Use `tabula-py` with `pages=1-3` and `multiple_tables=True` to extract tables. **Validation**: Iterate through extracted tables and select the **first valid table** where columns match the expected headers: `['Composition', 'Weibull Modulus', 'N', 'Sintering Temp']` (or similar variations) and row count > 0. **Fail Loudly**: If no table is found or extraction fails, raise `RuntimeError`. Do NOT skip rows silently. **Output**: Save raw JSON/CSV to `data/raw/arxiv_raw.json`.
- [ ] T018g [US1] **Fetch Curated Literature Data**: Implement `fetch_curated_literature_data()` in `code/ingestion.py`: Fetch the 'Curated Literature Dataset' from verified URL. **Parsing Logic**: Parse CSV columns: `composition`, `weibull_modulus`, `sample_count`, `sintering_temp`. **Trigger Logic**: Execute as a primary source alongside T018c, T018d-1, T018e. Merge data from all sources. **Output**: Save raw JSON/CSV to `data/raw/curated_literature_raw.json`.
- [ ] T017a [US1] **Implement Per-Entry Sample Count Filter**: Implement `filter_valid_sample_count()` in `code/ingestion.py`: Filter entries where `sample_count` (N) >= 30. **Logic**: Extract N from fields 'N', 'sample_size', 'n'. If absent, exclude entry. **Output**: Intermediate file `data/processed/step0_sample_count_filtered.csv`. (Addresses FR-003)
- [ ] T018f [US1] **Implement Data Cleaning Pipeline**: Implement `clean_data_pipeline()` in `code/ingestion.py`: A single pipeline function that orchestrates: 1) Call T017a (Sample Count Filter), 2) Filter valid stoichiometry, 3) Handle range values (midpoint, flag), 4) Impute missing params (group/global median), 5) Handle non-stoichiometric phases. **Dependencies**: T018c, T018d-1b, T018e, T018g, T017a (as internal sub-routine). **Output**: Save to `data/processed/step_final_cleaned.csv`. (Addresses FR-003, FR-002, FR-001)
- [ ] T017b [US1] **Implement Data Gap Validation & Report**: Implement `validate_data_gap()` in `code/ingestion.py`: Check total valid entries AFTER T017a filtering. **Logic**: If total row count < 30, immediately call `generate_data_availability_report()`, log the report path, output "Power Limitation: Insufficient data (N < 30)" to stderr, and **exit with code 1**. **Output**: Generate `data/reports/data_availability_report.json`. **Dependency**: T017a. (Addresses SC-004)
- [ ] T018a [US1] **Implement Derive Primary Anion/Cation Group**: Implement `derive_primary_anion_cation_group()` in `code/ingestion.py`: Parse the `composition` string using `chemparse` to identify the primary anion and cation groups (e.g., 'O-Al' for Alumina). Create a new column `primary_anion_cation_group`. **Dependency**: T018f.
- [ ] T018b-cation-variance [US1] **Compute Cation Size Variance**: Implement `compute_cation_size_variance()` in `code/descriptors.py`: Calculate variance of cation atomic radii. **Output**: Add column `cation_size_variance`. **Dependency**: T018a, T018f. (Addresses coverage-833ccaec)
- [ ] T018b-range-uncertainty [US1] **Compute Range Uncertainty**: Implement `compute_range_uncertainty()` in `code/descriptors.py`: Calculate range uncertainty based on extracted midpoint. **Dependency**: T018f. (Addresses coverage-833ccaec)
- [ ] T019a [US1] **Implement Compute Mean Atomic Radius**: Implement `compute_mean_atomic_radius()` in `code/descriptors.py`: Calculate mean atomic radius from stoichiometry. **Dependency**: T018a, T018f.
- [ ] T019b [US1] **Implement Compute Electronegativity Std**: Implement `compute_electronegativity_std()` in `code/descriptors.py`: Calculate standard deviation of electronegativity from stoichiometry. **Dependency**: T018a, T018f.
- [ ] T019c [US1] **Implement Compute Valence Electron Concentration**: Implement `compute_valence_electron_concentration()` in `code/descriptors.py`: Calculate VEC as total valence electrons divided by the total number of atoms in the formula unit. **Verification**: Add a unit test to verify the formula logic with a known example. **Dependency**: T018a, T018f.
- [ ] T020 [US1] **Implement Validate No Missing Primary Predictors**: Implement `validate_no_missing_primary_predictors()` in `code/ingestion.py`: Validate that essential descriptors have no missing values after cleaning and imputation. **Dependency**: T018f, T019a, T019b, T019c.
- [ ] T052-inline [US1] **Inline Memory Check**: Implement `check_memory_usage()` calls **inline** within `code/ingestion.py` inside T018c, T018d-1, T018e, T018g. **Implementation**: Use `psutil` to monitor RSS and raise `MemoryError` if > 6GB. **Output**: Log to `logs/memory_monitor.log`. **Dependency**: T052-config. **Threshold**: Use `config.MEMORY_LIMIT_GB` (default 6GB if env var unset). **Note**: This is NOT a separate task; it is code added to the fetch tasks. (Addresses ordering-374cf769)
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

- [ ] T026 [US2] Implement `prepare_splits()` in `code/modeling.py`: Stratified split based on `primary_anion_cation_group`. **Logic**: If N >= 50, use Stratified 5-fold CV. If 30 <= N < 50, use Stratified 80/20 Hold-out (per SC-004). If any class has < 5 samples, exclude from stratification (Rare Class Handling). **Dependency**: T018f.
- [ ] T027a [US2] Define `hyperparameter_search_space` in `code/modeling.py`: Define the constrained set of hyperparameter combinations for RF and GBM (a limited number of combinations).
- [ ] T027b [US2] Implement `train_models()` in `code/modeling.py`: Train RF and GBM using the defined search space. **Critical**: Store feature importance scores from **each CV fold** in `data/results/fold_importances.json`. **Dependency**: T027a, T026. **Seed**: Use `seed=42` for all random operations to ensure reproducibility.
- [ ] T029 [US2] Implement `run_permutation_test()` in `code/modeling.py`: Perform a permutation test to determine statistical significance of model improvement over the baseline. **Logic**: 1) Calculate MAE improvement percentage (must be >= 10% for SC-001). 2) Calculate p-value (must be < 0.05) using 1000 iterations, seed=42, and shuffling the target variable `y` (weibull_modulus). **Null Hypothesis**: Shuffle weibull_modulus values (y). **Reporting**: Generate `data/results/permutation_test_report.json` containing p-value, MAE improvement, and separate verdicts (e.g., "MAE_PASS", "SIG_PASS"). **Gating**: If p >= 0.05, log "Model not statistically significant" and **DO NOT proceed to T027d**; exit with code 0 but flag "Not Significant". **Dependency**: T027b.
- [ ] T027d [US2] **Save Best Model**: Save the best performing model to `data/models/best_model.pkl` ONLY if T029 reports statistical significance (p < 0.05). If T029 fails, skip save and log "Model not statistically significant; skipping save". **Dependency**: T029.
- [ ] T028b [US2] Implement `run_baseline_predictor()` in `code/modeling.py`: Create a simple model that predicts the global mean Weibull modulus for all test samples and save the MAE. **Dependency**: T026.
- [ ] T028 [US2] Implement `evaluate_models()` in `code/modeling.py`: Calculate MAE, R², and compare against global mean baseline. **Dependency**: T026.
- [ ] T030b [US2] **Train Leakage Check Model**: Train a second Random Forest model excluding the 'primary_anion_cation_group' feature. **Dependency**: T027b (Run regardless of T029 outcome). **Output**: Save model and metrics to `data/models/leakage_check_model.pkl`. **Verification**: Assert file exists and is valid.
- [ ] T030 [US2] **Implement Leakage Check**: Implement `check_leakage()` in `code/diagnostics.py`: Perform a leakage check by comparing model performance with and without the 'primary_anion_cation_group' feature. **Logic**: Read `data/models/leakage_check_model.pkl` and compare MAE from T027b. **Condition**: If MAE increases by < 10% (performance drop is small), flag "Potential Leakage" with exact warning message. **Output**: Generate `data/results/leakage_check.json`. (Addresses FR-005.5). **Dependency**: T027b, T030b.
- [ ] T031 [US2] Generate `data/results/model_metrics.json` with all scores and stratification reports. **Dependency**: T028, T029, T030.
- [ ] T032 [US2] Implement `filter_rare_classes()` in `code/modeling.py` to drop classes with < 5 samples before splitting, and verify via `tests/test_modeling.py::test_rare_class_exclusion`. **Dependency**: T026.
- [ ] T050 [US2] **Add Runtime Enforcement**: Wrap the entire `code/modeling.py` execution in a timeout handler to ensure completion within 6 hours. **Implementation**: Use `multiprocessing` to enforce a time limit on the full pipeline execution (ingestion to reporting). **Dependency**: T043. **Action**: If timeout exceeded, kill process and log `TimeoutExceededError`. **Logging**: Log the total runtime duration upon completion or timeout.
- [ ] T056-stream-model [US2] **Memory-Efficient Model Training**: Refactor `train_models()` in `code/modeling.py` to process data in batches if the dataset is large. **Logic**: Use `sklearn.utils.resample` or manual chunking to fit models on subsets if RAM usage exceeds 5GB, then aggregate results. **Dependency**: T055-stream, T027b. (Addresses Large Real Dataset Streaming Rule for Modeling)

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
- [ ] T038 [US3] Implement `group_correlated_features()` in `code/diagnostics.py`: Cluster highly correlated features for interpretive grouping. **Dependency**: T037.
- [ ] T038b [US3] Implement `report_cluster_importance()` in `code/report.py`: Calculate and report aggregate importance scores for correlated feature clusters. **Dependency**: T038.
- [ ] T039 [US3] Implement `calculate_cv_stability()` in `code/report.py`: Calculate Coefficient of Variation (CV) for **top 5 feature importance scores** **across cross-validation folds** by aggregating the per-fold feature importance scores from T036. **Dependency**: T036b. (Addresses SC-002)
- [ ] T040 [US3] Implement `generate_interpretation()` in `code/report.py`: Rank features, map descriptors to physical mechanisms, and include correlation matrix. **Dependency**: T036b, T037, T038, T039.
- [ ] T041 [US3] **Execute & Generate Interpretability Artifacts**: Execute the analysis and generate SHAP summary plot (`data/artifacts/shap_summary.png`), feature ranking table (`data/results/feature_ranking.csv`), and stability metrics (`data/results/stability_metrics.json`). **Dependency**: T036b-T040.

---

## Phase 6: Reporting & Compliance (Polish)

**Purpose**: Finalize reports, ensure compliance, and update project state.

- [ ] T043 [P] Implement `generate_final_report()` in `code/report.py`: Combine metrics, SHAP analysis, and disclaimers. **Dependency**: T031, T041, T017b (conditional).
- [ ] T044 [P] Execute `code/hash_artifacts.py` to update project state with new content hashes for all files in `data/` and `code/`. **Dependency**: T043.
- [ ] T045 [P] Run `bash scripts/validate_quickstart.sh` to validate the quickstart guide against the implemented pipeline. **Dependency**: T016a, T043.
- [ ] T051 [P] **Final Compliance Audit**: Run a script to ensure all requirements are met. **Dependency**: T043, T044, T045.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

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
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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
- **Critical**: All data fetching tasks MUST use streaming for large datasets or fail loudly. No synthetic fallbacks allowed.