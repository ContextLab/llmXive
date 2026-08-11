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
- [X] T004 Setup `data/raw/`, `data/processed/`, and `data/artifacts/` directories
- [X] T005 [P] Implement `code/hash_artifacts.py` for versioning and checksumming (Constitution Principle V)
- [X] T008 [P] Setup `code/ingestion.py` skeleton file structure
- [X] T009 [P] Implement URL validation logic in `code/ingestion.py`
- [X] T009b [P] Implement `validate_source_citations()` in `code/ingestion.py`: Validate source URLs/DOIs against primary sources (Constitution Principle II) by checking title overlap >= 0.7 and verifying reachability; log failures to `logs/citation_validation.log`. **Verification**: Ensure `logs/citation_validation.log` is created and populated during the first validation run. **Scope**: Must cover Materials Project, NIST (Zenodo), arXiv, and Curated Literature Dataset URLs. (Addresses Plan Phase 0, Task 0.3)
- [X] T010 [P] Configure logging infrastructure in `code/__init__.py` (Ensures `logs/` directory exists for T009b)
- [X] T010b [P] Verify `logs/citation_validation.log` creation: Execute `python code/ingestion.py --validate-dummy` with `dummy_urls=['https://example.com']`. Assert that `logs/citation_validation.log` exists and contains at least one entry with format `INFO: Citation validation for {url}: {status}` where status is not empty. (Addresses T009b verification gap)
- [X] T011 [P] Setup environment configuration management: Create `.env.example`, implement `load_env()` in `code/__init__.py`, and add unit test `tests/test_config.py::test_env_loading`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T012a [P] **Validate** `ceramic_entry.schema.yaml` in `code/contracts/`: Ensure the schema generated in T016c is correctly formatted and contains all required fields: `composition`, `weibull_modulus`, `sample_count`, `is_range_flag`, `range_original`, `primary_anion_cation_group`, `sintering_temp`, `is_imputed`, `mean_atomic_radius`, `electronegativity_std`, `valence_electron_concentration`. (Addresses Plan Phase 1, Task 1.5; consumes T016c output)
- [X] T012b [P] **Validate** `model_result.schema.yaml` in `code/contracts/`: Ensure the schema generated in T016c is correctly formatted and contains all required fields: `model_type`, `mae`, `r_squared`, `feature_importance_ranking`, `cv_stability_scores`. (Addresses Plan Phase 1, Task 1.5; consumes T016c output)
- [X] T022 [P] Create `code/physics_mappings.py` with dictionary mapping descriptors to physical mechanisms (e.g., "cation_size_variance" -> "Grain boundary stability") to support US3 (Moved to Phase 2 to ensure availability before US3 work)
- [X] T016d [P] Create `data/mappings/mp_weibull_proxy.yaml`: A curated internal table mapping known ceramic compositions (e.g., "Al2O3", "ZrO2") to their Weibull modulus values, to be used as a fallback for Materials Project fetches where the API does not expose the target variable. (Addresses T018c executability)
- [X] T016e [P] Create `data/mappings/arxiv_targets.yaml`: A curated list of specific high-impact paper DOIs (e.g., 10.1016/j.jeurceramsoc.2020.01.001) known to contain Weibull data, to be used as the primary source for arXiv fetches. (Addresses T018e executability)
- [X] T052 [US1] **Memory Check**: Implement memory usage check to prevent exceeding the memory limit. **Implementation**: Use `psutil` to monitor RSS and raise `MemoryError` if > 6GB. **Output**: Log to `logs/memory_monitor.log`. **Dependency**: T017 (Gate Pass). **Threshold**: Use `config.MEMORY_LIMIT_GB` (6GB). This task must be executed before any heavy data processing to ensure stability on the runner. (Addresses Plan Phase 2 & Constitution Principle I)

---

## Phase 3: User Story 1 - Data Ingestion and Descriptor Computation (Priority: P1) 🎯 MVP

**Goal**: Ingest raw ceramic data, clean it, and compute elemental descriptors to produce a feature-rich dataset.

**Independent Test**: Run the pipeline on a sample of known entries.; verify output CSV contains `weibull_modulus` and at least 10 computed descriptors with no missing values for primary predictors.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T013 [P] [US1] Unit test for `chemparse` composition parsing in `tests/test_descriptors.py`
- [X] T014 [P] [US1] Unit test for imputation logic (group vs. global median) in `tests/test_ingestion.py`
- [X] T015 [P] [US1] Integration test for full ingestion pipeline on a small sample in `tests/integration/test_ingestion.py`

### Implementation for User Story 1

- [ ] T018c [US1] Implement `fetch_materials_project_data()` in `code/ingestion.py`: **Strategy**: The MP API does not expose 'weibull_modulus'. Fetch `formation_energy_per_atom` and `band_gap` for ceramic entries. **Fallback**: Use `data/mappings/mp_weibull_proxy.yaml` to map compositions to Weibull values. **Filter**: Explicitly filter results to include ONLY entries where a Weibull value is found in the proxy map. **Auth**: Read `MP_API_KEY` from `os.getenv('MP_API_KEY')`; raise `RuntimeError("MP_API_KEY not found")` if missing. **Fail Loudly**: If no Weibull data is found in the proxy map for any fetched entry, raise `RuntimeError("Materials Project fetch failed: No Weibull data in proxy map")`. **Output**: Raw JSON to `data/raw/materials_project_raw.json`. (Addresses FR-001 coverage gap, corrected URL/logic, removed fallback)
- [ ] T018d [US1] Implement `fetch_nist_data()` in `code/ingestion.py`: **Source**: Fetch from verified dataset on Hugging Face: `ucimlrepo/ceramic-weibull` (or equivalent verified ceramic Weibull dataset ID). **Validation**: Use `validate_source_citations()` to verify the dataset ID resolves and matches the expected title. **Parsing Logic**: Use `datasets.load_dataset` with `streaming=True` to handle large data; parse columns: `composition`, `weibull_modulus`, `sample_count`, `sintering_temp`. **Fail Loudly**: If the fetch fails, returns no data, or the dataset ID is invalid, raise a `RuntimeError`. **Output**: Raw JSON/CSV to `data/raw/nist_raw.json`. (Addresses FR-001 coverage gap, corrected URL, added streaming)
- [ ] T018e [US1] Implement `fetch_arxiv_data()` in `code/ingestion.py`: **Primary Source**: Use the curated list in `data/mappings/arxiv_targets.yaml` (3 specific DOIs). **Secondary Source**: If primary source yields < 5 entries, search arXiv with query `all:(ceramic AND weibull) AND all:(modulus)`, sort by `relevance` (citation count), and select top 10. **Extraction**: Use `pdfplumber` to extract the **first table** containing both a composition column and a Weibull/Modulus column. **Fail Loudly**: If no valid table is found in primary or secondary sources, raise `RuntimeError`. **Output**: Raw JSON/CSV to `data/raw/arxiv_raw.json`. (Addresses FR-001 coverage gap, corrected logic, removed silent fallback)
- [ ] T018g [US1] Implement `fetch_curated_literature_data()` in `code/ingestion.py`: **Source**: Fetch the 'Curated Literature Dataset' from verified DOI: ` (Ceramic Mechanical Properties Dataset). **Validation**: Use `validate_source_citations()` to verify the DOI resolves and matches the expected title. **Parsing Logic**: Parse CSV columns: `composition`, `weibull_modulus`, `sample_count`, `sintering_temp`. **Fallback**: If the external fetch fails due to network issues, attempt to load `data/local/curated_literature_fallback.csv` (a static copy of the same dataset). **Fail Loudly**: If both external fetch and local fallback fail or return no data, raise `RuntimeError`. **Trigger Logic**: This task is ONLY executed if T018c, T018d, or T018e fail or return no data. Output raw JSON/CSV to `data/raw/curated_literature_raw.json`. (Addresses Plan Phase 0, Task 0.2 fallback requirement, corrected URL)
- [ ] T018f [US1] Implement `combine_raw_data()` in `code/ingestion.py`: **Logic**: Read all raw JSON/CSV files from `data/raw/` (T018c, T018d, T018e, T018g outputs). Concatenate into a single `data/raw/combined_raw.csv`. **Deduplication**: Remove duplicate entries based on `composition` and `sintering_temp`. **Dependency**: T018c, T018d, T018e, T018g. (Addresses T017 data flow requirement)
- [ ] T018a [US1] Implement `derive_primary_anion_cation_group()` in `code/ingestion.py`: Parse the `composition` string using `chemparse` to identify the primary anion and cation groups (e.g., 'O-Al' for Alumina). Create a new column `primary_anion_cation_group`. **Dependency**: T018f (Combine Raw Data). **Execution Order**: Runs on combined raw data before cleaning. (Addresses ordering violation)
- [X] T017c [US1] Create test data `data/raw/test_n.csv` with exactly 29 rows where the `sample_count` field is >= 30. **Purpose**: Verify T017 halts when total row count < 30 even if individual sample counts are valid. (Clarified: T017 checks total rows, T018f checks sample_count field). **Dependency**: T018a (to ensure column exists for validation logic).
- [ ] T017 [US1] Implement `validate_data_gap()` in `code/ingestion.py`: Check total valid entries after fetching (raw count) and deriving groups. **Input**: `data/raw/combined_raw.csv`. **Logic**: Halt execution if N < 30 and generate a "Data Availability Report". **Dependency**: T018c, T018d, T018e, T018g, T018f, T018a, T017c.
- [ ] T017b [US1] Implement `generate_data_availability_report()` in `code/ingestion.py`: Generate the `data/reports/data_availability_report.json` file when halting due to insufficient data. **Dependency**: T017.
- [ ] T018f-clean [US1] Implement `clean_data_pipeline()` in `code/ingestion.py`: Consolidated data cleaning pipeline. **Steps**: 1. `filter_valid_stoichiometry()` -> `data/processed/step1_cleaned.csv`. 2. `handle_range_values()` (extract midpoint, set `is_range_flag`, compute `range_uncertainty`) -> `data/processed/step2_range.csv`. 3. `impute_missing_params()` -> `data/processed/step3_imputed.csv`. 4. `handle_non_stoichiometric_phases()` -> `data/processed/step4_final.csv`. **Dependency**: T018f, T018a, T017.
- [X] T019a [US1] Implement `compute_mean_atomic_radius()` in `code/descriptors.py`: Calculate mean atomic radius from stoichiometry. **Dependency**: T018f-clean (Step 4).
- [X] T019b [US1] Implement `compute_electronegativity_std()` in `code/descriptors.py`: Calculate standard deviation of electronegativity from stoichiometry. **Dependency**: T018f-clean (Step 4).
- [X] T019c [US1] Implement `compute_valence_electron_concentration()` in `code/descriptors.py`: Calculate VEC as total valence electrons divided by the total number of atoms. **Dependency**: T018f-clean (Step 4).
- [X] T020 [US1] Implement `validate_no_missing_primary_predictors()` in `code/ingestion.py`: Validate that essential descriptors have no missing values after cleaning and imputation. **Dependency**: T018f-clean, T019a, T019b, T019c.
- [ ] T054 [US1] **Implement Streaming Data Loader**: Refactor `fetch_materials_project_data()` and `fetch_nist_data()` to use streaming where possible. **Threshold**: Use `datasets.load_dataset(name, split=..., streaming=True)` for ALL real data fetches (e.g., 'materials-project/ceramics', 'ucimlrepo/ceramic-weibull'). **Constraint**: Ensure no single chunk exceeds a large, system-appropriate size limit. **Hygiene**: Explicitly checksum each chunk and aggregate into a final `data/raw/streamed_final.csv` with a global checksum before processing. **Output**: Log chunk processing stats to `logs/streaming_stats.log`. (Addresses Rule: "Large real datasets: STREAM the real data" + Constitution Principle III)
- [ ] T055 [US1] **Implement Sample Fallback for Streaming**: If streaming is not possible or the dataset is too large for the compute budget, implement a well-defined sampling strategy. **Implementation**: Use `itertools.islice` to take a fixed-seed random sample of [deferred] of the dataset (minimum 500 rows). **Requirement**: State the sample size and its representativeness limitation in the log. **Output**: Log sampling details to `logs/sampling_log.txt`. (Addresses Rule: "Only if the full dataset genuinely cannot be processed... fall back to a well-defined REAL sample")
- [ ] T059 [US1] **Implement UCI Dataset Fetch**: Implement `fetch_uci_data()` in `code/ingestion.py` using `datasets.load_dataset('ucimlrepo/ceramic-weibull')` or a specific verified URL. **Strategy**: Use this as a primary source if MP/NIST fail. **Fail Loudly**: If fetch fails, raise `RuntimeError`. **Output**: Raw JSON/CSV to `data/raw/uci_raw.json`. (Addresses executability)

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
- [ ] T029 [US2] Implement `run_permutation_test()` in `code/modeling.py`: Perform a permutation test to determine statistical significance of model improvement over the baseline. **Logic**: 1) Calculate MAE improvement percentage (must be >= 10% for SC-001). 2) Calculate p-value (must be < 0.05) using 1000 iterations and seed=42. **Reporting**: Generate `data/results/permutation_test_report.json` containing p-value, MAE improvement, and separate verdicts (e.g., "MAE_PASS", "SIG_PASS"). Do NOT halt pipeline; report partial results. **Dependency**: T027b.
- [ ] T027d [US2] **Save Best Model**: Save the best performing model to `data/models/best_model.pkl` ONLY if T029 reports statistical significance (p < 0.05). **Dependency**: T029. **Logic**: If p >= 0.05, skip save and log "Model not statistically significant; skipping save".
- [X] T028b [US2] Implement `run_baseline_predictor()` in `code/modeling.py`: Create a simple model that predicts the global mean Weibull modulus for all test samples and save the MAE. **Dependency**: T026.
- [X] T028 [US2] Implement `evaluate_models()` in `code/modeling.py`: Calculate MAE, R², and compare against global mean baseline.
- [~] T030 [US2] Implement `check_leakage()` in `code/diagnostics.py`: Perform a leakage check by comparing model performance with and without the 'primary_anion_cation_group' feature. **Logic**: Re-run best model without 'primary_anion_cation_group'. If performance drops by **> 10% MAE**, flag "Potential Leakage" with exact warning message. **Output**: Generate `data/results/leakage_check.json`. (Addresses FR-005.5).
- [X] T031 [US2] Generate `data/results/model_metrics.json` with all scores and stratification reports
- [X] T032 [US2] Implement `filter_rare_classes()` in `code/modeling.py` to drop classes with < 5 samples before splitting, and verify via `tests/test_modeling.py::test_rare_class_exclusion`
- [~] T050 [US2] **Add Runtime Enforcement**: Wrap the `train_models` and `run_permutation_test` execution in a timeout handler to ensure completion within 6 hours.

---

## Phase 5: User Story 3 - Feature Importance and Mechanistic Interpretation (Priority: P3)

**Goal**: Extract SHAP values, rank features, and interpret results against fracture mechanics principles.

**Independent Test**: Run analysis on best model; verify output lists top descriptors, includes correlation matrix, and flags collinearity.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T033 [P] [US3] Unit test for VIF calculation in `tests/test_diagnostics.py`
- [X] T034 [P] [US3] Unit test for SHAP value aggregation in `tests/test_report.py`
- [X] T035 [P] [US3] Integration test for full interpretability pipeline in `tests/integration/test_interpretability.py`

### Implementation for User Story 3

- [X] T036 [US3] Implement `calculate_shap()` in `code/diagnostics.py`: Generate SHAP values for the best-performing model
- [X] T037 [US3] Implement `calculate_vif()` in `code/diagnostics.py`: Compute VIF for all predictors and flag highly correlated features.
- [X] T038 [US3] Implement `group_correlated_features()` in `code/diagnostics.py`: Cluster highly correlated features for interpretive grouping.
- [X] T038b [US3] Implement `report_cluster_importance()` in `code/report.py`: Calculate and report aggregate importance scores for correlated feature clusters.
- [ ] T039 [US3] **Calculate CV Stability**: Implement `calculate_cv_stability()` in `code/report.py`: Calculate Coefficient of Variation for top-ranked features **across cross-validation folds** by reading `data/results/fold_importances.json` generated in T027b. **Dependency**: T027b. **Status**: Actionable now that T027b is complete.
- [X] T040 [US3] Implement `generate_interpretation()` in `code/report.py`: Rank features, map descriptors to physical mechanisms, and include correlation matrix.
- [ ] T041 [US3] **Execute & Generate Interpretability Artifacts**: Execute the analysis and generate SHAP summary plot (`data/artifacts/shap_summary.png`), feature ranking table (`data/results/feature_ranking.csv`), and stability metrics (`data/results/stability_metrics.json`). **Dependency**: T036-T040, T027d (if model saved).

---

## Phase 6: Reporting & Compliance (Polish)

**Purpose**: Finalize reports, ensure compliance, and update project state.

- [X] T043 [P] Implement `generate_final_report()` in `code/report.py`: Combine metrics, SHAP analysis, and disclaimers.
- [X] T044 [P] Execute `code/hash_artifacts.py` to update project state with new content hashes for all files in `data/` and `code/`.
- [X] T045 [P] Run `bash scripts/validate_quickstart.sh` to validate the quickstart guide against the implemented pipeline.
- [~] T045b [P] **Final Quickstart Sync**: Explicitly regenerate `quickstart.md` in `specs/001-predict-weibull-modulus/` to reflect the final pipeline state after all modeling and interpretation tasks are complete. Ensure all paths and steps match the final implementation. **Dependency**: T043, T044, T056 (Full Pipeline Run). (Addresses Plan Phase 1, Task 1.5 & Coverage Gaps)
- [~] T045c [P] **Update Quickstart**: After Phase 7/8 changes, update `quickstart.md` to reflect the final pipeline steps and ensure accuracy. (Addresses Plan Phase 1, Task 1.5)
- [~] T046 [P] **Measure Pipeline Runtime**: Execute the full pipeline and log the total duration.
- [X] T047 [P] Update `docs/data_gap_protocol.md` with the exact report generation steps.
- [~] T051 [P] **Final Compliance Audit**: Run a script to ensure all requirements are met.

---

## Phase 7: Data Streaming & Large Dataset Handling (Revision)

**Purpose**: Ensure the pipeline can handle large real datasets by streaming them instead of loading them all into memory, adhering to the "Real data + real results only" rule.

(See T054 and T055 in Phase 3 for implementation details)

---

## Phase 8: Final Validation & Execution (Revision)

**Purpose**: Ensure the pipeline executes correctly and all requirements are met before finalizing.

- [ ] T056 [US2] **Execute Full Pipeline**: Run the entire pipeline from ingestion to reporting on a small subset of data to verify end-to-end functionality. **Output**: Generate `data/results/full_pipeline_run.json` with timestamps and success/failure status for each step. (Addresses Rule: "Task ordering MUST respect data flow").
- [~] T057 [US3] **Verify SHAP Interpretability**: Run the SHAP analysis and verify that the top features are indeed compositional descriptors and not processing parameters. **Output**: Log verification results to `logs/shap_verification.log`. (Addresses Rule: "Task ordering MUST respect data flow").
- [~] T058 [US1] **Verify Data Source**: Confirm that the data source used is a real, verified source and not a synthetic fallback. **Implementation**: Check `logs/citation_validation.log` and `logs/streaming_stats.log` for evidence of real data fetch. **Output**: Log verification results to `logs/data_source_verification.log`. (Addresses Rule: "If a verified real data source is injected, USE it").

---

## Phase 9: Revision - Resolve Analyze Findings (New)

**Purpose**: Address specific issues raised by the `/speckit.analyze` pass regarding data flow, URL validity, and task dependencies.

- [ ] T060 [US1] **Resolve Data Flow Dependency**: Ensure `validate_data_gap()` (T017) runs AFTER all fetch tasks (T018c, T018d, T018e, T018g) have attempted to populate `data/raw/`. **Action**: Modify `code/ingestion.py` main execution flow to call fetchers first, then T017. **Dependency**: T017, T018c, T018d, T018e, T018g. **Verification**: Confirm T017 is executed after T018f in the main script. (Addresses ordering-acc9020a, ordering-68432ac7)
- [ ] T061 [US2] **Resolve Model Save Logic**: Ensure T027d (Save Best Model) is strictly gated by T029 (Permutation Test). **Action**: Add explicit conditional logic in `code/modeling.py` to prevent saving `best_model.pkl` if `p_value >= 0.05`. **Dependency**: T027d, T029.
- [ ] T062 [US3] **Resolve SHAP Execution**: Ensure T041 (Execute & Generate Artifacts) runs only after T027d (Model Save) and T039 (CV Stability) are complete. **Action**: Add dependency check in `code/report.py` or execution script. **Dependency**: T041, T027d, T039.
- [ ] T063 [US1] **Resolve Memory/Streaming Logic**: Ensure T054 (Streaming) and T055 (Sampling) are integrated into `fetch_materials_project_data` and `fetch_nist_data` rather than being separate tasks. **Action**: Refactor T018c and T018d to include streaming/sampling logic internally, removing T054/T055 as separate top-level tasks if they are now internal implementation details. **Dependency**: T054, T055, T018c, T018d. **Verification**: Confirm T054/T055 logic is present in T018c/d. (Addresses constraint_preservation-dacf1e12, constraint_preservation-494d3b57)
- [ ] T064 [US2] **Resolve Runtime Enforcement**: Implement T050 (Runtime Enforcement) by adding a `timeout` wrapper to the `train_models` function. **Action**: Use `signal` module or `concurrent.futures` to enforce a 5-hour limit (leaving 1 hour for report generation). **Dependency**: T050, T027b.
- [ ] T065 [US1] **Resolve Data Source Verification**: Ensure T058 (Verify Data Source) is executed as part of the main pipeline run, not just a manual check. **Action**: Add a `verify_real_data_source()` function called in `code/ingestion.py` before any processing begins. **Dependency**: T058, T017. **Verification**: Confirm T058 is called before T017. (Addresses ordering-8cfdaab1)
- [ ] T066 [US2] **Resolve Quickstart Sync**: Ensure T045b and T045c are executed automatically after T056 (Full Pipeline Run). **Action**: Add a hook in `scripts/validate_quickstart.sh` to regenerate `quickstart.md` if the pipeline succeeds. **Dependency**: T045b, T045c, T056.