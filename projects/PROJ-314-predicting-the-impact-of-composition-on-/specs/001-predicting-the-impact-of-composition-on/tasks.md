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
- [X] T016c-1 Define `CeramicEntry` and `DescriptorSet` schemas in `code/contracts/schemas.py` using Pydantic.
- [X] T016c-2 Export schemas to YAML files `ceramic_entry.schema.yaml` and `model_result.schema.yaml` in `code/contracts/`.
- [X] T016c-3 Generate `data-model.md` in `specs/001-predict-weibull-modulus/`: Document the `CeramicEntry` and `DescriptorSet` entities, their relationships, and validation rules. Must include YAML schema examples and field type definitions. (Addresses Plan Phase 1, Task 1.5)
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

- [X] T018c [US1] Implement `fetch_materials_project_data()` in `code/ingestion.py`: Use `pymatgen` (mp-api) to fetch ceramic property data. **Endpoint**: Use `MPRestClient().get_entries(elements=..., properties=['weibull_modulus'])`. Query: `{elements: {exists: true}, properties: {weibull_modulus: {exists: true}}}`. Fetch from Materials Project API. **Fail Loudly**: If API returns no Weibull data or connection fails, raise `RuntimeError` with message "Materials Project fetch failed: {error}". Do NOT fall back to local CSV. Output raw JSON to `data/raw/materials_project_raw.json`. (Addresses FR-001 coverage gap, corrected URL/logic, removed fallback)
- [X] T018d [US1] Implement `fetch_nist_data()` in `code/ingestion.py`: Fetch NIST Ceramic Data from verified URL `. **Endpoint**: Use direct CSV download if available (e.g., `) or use `requests` to scrape the table. **Fail Loudly**: If fetch fails or no data is found, raise `RuntimeError` with message "NIST fetch failed: {error}". Do NOT fall back to local CSV. Output raw JSON/CSV to `data/raw/nist_raw.json`. (Addresses FR-001 coverage gap, corrected URL, removed fallback)
- [X] T018e [US1] Implement `fetch_arxiv_data()` in `code/ingestion.py`: Use `arxiv` library to search for `all:ceramic AND all:weibull` (limit a representative sample). Use `pdfplumber` to extract tables from a representative set of PDFs (first 5 PDFs with >100KB size). **Extraction Logic**: Use regex patterns `r"(Al|Si|O|Ti|Zr|Zn|Nb|Ta|Hf|Mo|W|V|Cr|Mn|Fe|Co|Ni|Cu|Ga|In|Sn|Sb|Te|Bi|Pb|S|Se|F|Cl|Br|I)"` for composition and `r"(Weibull|Modulus)"` for target. Extract table at page, column 2. **Fail Loudly**: If no table found or no data extracted, raise `RuntimeError` with message "ArXiv extraction failed: No usable data found". Do NOT skip rows silently. Output raw JSON/CSV to `data/raw/arxiv_raw.json`. (Addresses FR-001 coverage gap, corrected logic, removed silent fallback)
- [X] T018g [US1] Implement `fetch_curated_literature_data()` in `code/ingestion.py`: Fetch the 'Curated Literature Dataset' from verified URL `. **Endpoint**: Direct CSV download. **Parsing Logic**: Parse CSV columns: `composition`, `weibull_modulus`, `sample_count`, `sintering_temp`. **Fail Loudly**: If fetch fails or no data is found, raise `RuntimeError` with message "Curated Literature Dataset fetch failed: {error}". This is the ONLY allowed fallback before hard failure. Output raw JSON/CSV to `data/raw/curated_literature_raw.json`. (Addresses Plan Phase 0, Task 0.2 fallback requirement)
- [X] T018a [US1] Implement `derive_primary_anion_cation_group()` in `code/ingestion.py`: Parse the `composition` string using `chemparse` to identify the primary anion and cation groups (e.g., 'O-Al' for Alumina). Create a new column `primary_anion_cation_group`. **Ordering**: This step MUST run after fetching (T018c/d/e/g) and after T017 (Data Gap Check) confirms N >= 30. **Dependency**: T018c, T018d, T018e, T018g must be complete. (Addresses ordering gap: Derive Group after Fetch and Gap Check)
- [X] T018f [US1] Implement `clean_data()` in `code/ingestion.py`:
 1. Filter for 'valid stoichiometry' and 'N field presence' (FR-003). **Do NOT** filter by N < 30 here; that is T017's job.
 2. Handle range values: Extract midpoint, set `is_range_flag`, store `range_original` (to be processed by T018b).
 3. Impute missing processing params (group median -> global median). Use `primary_anion_cation_group` derived in T018a.
 4. Handle non-stoichiometric phases: **Exclude** if the specific class has < 5 samples; otherwise, impute using global median.
 5. **Output Schema**: Ensure output CSV contains columns: `composition`, `weibull_modulus`, `sample_count`, `is_range_flag`, `range_original`, `primary_anion_cation_group`, `sintering_temp`, `is_imputed`. (Descriptors like `mean_atomic_radius` are populated by T019).
 **Dependency**: T018c, T018d, T018e, T018g, T018a must be complete.
- [X] T017 [US1] Implement `validate_data_gap()` in `code/ingestion.py`:
 1. Check total valid entries (N) after fetching (T018c/d/e/g).
 2. **HALT**: If N < 30, call `generate_data_availability_report()` (T017b) to create `data/reports/data_availability_report.json`, log `INFO: PROJECT_HALTED: Insufficient data (N={N})`, and **exit with code 1**.
 3. If N >= 30, proceed to T018a (Derive Group) and T018f (Clean).
 **Dependency**: T018c, T018d, T018e, T018g must be complete.
- [X] T017b [US1] Implement `generate_data_availability_report()` in `code/ingestion.py`: Generate `data/reports/data_availability_report.json` with fields `total_sources` (actual count of fetched sources), `valid_entries`, `reason_code`, `timestamp` when N < 30 (Required for Data Gap Protocol). **Output**: File must be written before halting. **Exit**: Must call `sys.exit(1)` after writing. (Addresses Data Gap Protocol)
- [X] T017c [US1] **Execute & Verify Data Gap Report**: 1. Create `data/raw/test_n29.csv` with exactly **29 rows** (total entry count) to trigger the 'total entry count < 30' halt. The `sample_count` field values in these rows must be >= 30 (to pass T018f filters), but the **row count** must be 29. Schema: `composition` (str), `weibull_modulus` (float), `sample_count` (int), `sintering_temp` (float), `primary_anion_cation_group` (str). Sample Row: `{"composition": "Al2O3", "weibull_modulus": 10.5, "sample_count": 30, "sintering_temp": 1600.0, "primary_anion_cation_group": "O-Al"}`. 2. Run `python code/ingestion.py --input data/raw/test_n29.csv --force-gap-check`. 3. Verify that `data/reports/data_availability_report.json` is generated with correct dynamic fields and that the process halts with exit code 1. **Dependency**: T017b must be complete. (Addresses Executability & Ordering Gaps)
- [X] T018b [US1] Implement `compute_range_uncertainty()` in `code/descriptors.py`:
 1. Extract midpoint from `range_original` if `is_range_flag` is true.
 2. Calculate `range_uncertainty` as (max - min) / 2.
 3. Add `range_uncertainty` column to the dataset. (Addresses Plan Phase 1, Task 1.4)
- [X] T019a [US1] Implement `compute_mean_atomic_radius()` in `code/descriptors.py`: Calculate mean atomic radius from stoichiometry. (Addresses Plan Phase 1, Task 1.2)
- [X] T019b [US1] Implement `compute_electronegativity_std()` in `code/descriptors.py`: Calculate standard deviation of electronegativity from stoichiometry. (Addresses Plan Phase 1, Task 1.2)
- [X] T019c [US1] Implement `compute_valence_electron_concentration()` in `code/descriptors.py`: Calculate VEC as `sum(valence electrons of all atoms) / total number of atoms in formula unit` (FR-002). (Addresses Plan Phase 1, Task 1.2)
- [X] T020 [US1] Implement `validate_no_missing_primary_predictors()` in `code/ingestion.py`: Check columns `mean_atomic_radius`, `electronegativity_std`, `valence_electron_concentration`, `primary_anion_cation_group`. Raise `ValueError` with message "Missing values in primary predictors: {col_names}" if any contain NaN. Add unit test `tests/test_ingestion.py::test_validate_no_missing`. **Dependency**: T019a, T019b, T019c must be complete. **Ordering**: This is the final validation step before modeling. (Addresses FR-002 validation, self-containment)
- [X] T021 [US1] Implement logging for data exclusion reasons in `code/ingestion.py`: Log format `INFO: Excluded row {row_index} due to {reason}` where `{row_index}` is the pandas index and `{reason}` is one of: 'N<30', 'missing_stoichiometry', 'non_stoichiometric_phase'. Log to `logs/ingestion.log`. (Addresses Plan Phase 1, Task 1.3)
- [X] T052 [US1] **Memory Check**: Implement `check_memory_usage()` in `code/ingestion.py`: After loading the dataset, check if the estimated memory usage exceeds a predefined threshold. If so, raise `MemoryError` with message "Dataset too large for available RAM (6GB limit)". (Addresses Constitution Rule: Large real datasets - replace T048)
- [X] T049 [US1] **Hard Fail on Synthetic Fallback**: Refactor `fetch_materials_project_data`, `fetch_nist_data`, and `fetch_arxiv_data` to ensure they raise a `RuntimeError` immediately if the primary URL/package fetch fails. Remove any `try/except` blocks that fall back to `generate_synthetic_data()` or random generation. Ensure the pipeline fails loudly if real data is unavailable, BUT retain the `fetch_curated_literature_data` (T018g) as the ONLY allowed fallback. **Dependency**: T018c, T018d, T018e, T018g must be implemented to verify no synthetic fallbacks exist. (Addresses Constitution Rule: The loader must FAIL LOUDLY, never fall back to synthetic)

---

## Phase 4: User Story 2 - Predictive Modeling and Cross-Validation (Priority: P2)

**Goal**: Train Random Forest and Gradient Boosting models with strict cross-validation to predict Weibull modulus.

**Independent Test**: Execute training on a subset; verify JSON output contains MAE, R², and stratified split report confirming distribution match.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US2] Unit test for stratified splitting logic in `tests/test_modeling.py`
- [X] T024 [P] [US2] Unit test for baseline (global mean) predictor in `tests/test_modeling.py`
- [X] T025 [P] [US2] Implement integration test `tests/integration/test_modeling.py::test_5fold_cv_stratified_split` to verify the 5-fold CV workflow and **generate `data/results/cv_split_report.json`** containing stratification distribution metrics.

### Implementation for User Story 2

- [X] T026 [US2] Implement `prepare_splits()` in `code/modeling.py`: Stratified split based on `primary_anion_cation_group` (derived from US1 output); switch to hold-out if 30 <= N < 50 (FR-005, SC-004). **Dependency**: Requires T018f completion.
- [X] T027 [US2] Implement `train_models()` in `code/modeling.py`: Train RF and GBM with **limited hyperparameter search (a constrained set of combinations)**. **Search Space**: `n_estimators` (low to moderate), `max_depth: [5, 10]`, `min_samples_split: [2, 5]`. **Fail Loudly**: If search space exceeds 50 combinations, raise `ValueError`. (Addresses Plan Phase 2, Task 2.4, FR-004)
- [X] T027b [US2] **Save Best Model**: After T027, save the best performing model (lowest CV MAE) to `data/models/best_model.pkl` and log its hash. **Dependency**: T027 must complete.
- [X] T028b [US2] Implement `run_baseline_predictor()` in `code/modeling.py`: Create a simple model that predicts the global mean Weibull modulus for all test samples. Calculate and **save its MAE to `data/results/baseline_metrics.json`** (key: `baseline_mae`). **Dependency**: Must run before T028. (Addresses Plan Phase 2, Task 2.3, T030 dependency)
- [X] T028 [US2] Implement `evaluate_models()` in `code/modeling.py`: Calculate MAE, R², and compare against global mean baseline (SC-001). **Output**: Save metrics to `data/results/model_metrics.json`, explicitly including keys `best_model_mae` and `best_model_type`. **Dependency**: T028b must be complete.
- [X] T029 [US2] Implement `run_permutation_test()` in `code/modeling.py`: Perform a permutation test (**1000 iterations**, `random_seed=42`, permute target variable y) to determine statistical significance (p < 0.05) of the model's MAE improvement over baseline. **Logic**: Flag as "Not Statistically Significant" if p >= 0.05 **OR** if Model MAE >= 90% of Baseline MAE (Combined Check for SC-001). Include a convergence check to ensure robustness. Update `data/results/model_metrics.json` with `is_significant` boolean. (Restored to satisfy SC-001 statistical significance requirement)
- [X] T030 [US2] Implement `check_leakage()` in `code/diagnostics.py`:
 1. Select the **best model** from T027/T028 (lowest validation MAE). Load from `data/models/best_model.pkl` (verify hash matches T027b log).
 2. **Retrieve Logic**: Load `data/results/model_metrics.json` to get `best_model_mae`. Load `data/results/baseline_metrics.json` to get `baseline_mae`.
 3. Re-run the best model **without** the `primary_anion_cation_group` feature to get `new_mae_without_group`.
 4. **Leakage Logic (FR-005.5)**: Calculate performance drop = (best_model_mae - new_mae_without_group) / best_model_mae.
 - If performance drop **<= 10%** (small drop): Flag **"Potential Leakage"** (The group variable was the main predictor, descriptors failed to capture signal).
 - If performance drop **> 10%** (significant drop): Flag **"Descriptors Sufficient"**.
 5. **Mandatory Output**: Write the sufficiency conclusion and the calculated drop percentage to `data/results/leakage_report.json` (FR-005.5).
 **Dependency**: T028, T028b, T027b (must be completed and verified: file exists), and T018a (for processed dataset) must be complete to provide the metric files, model artifact, and data.
- [X] T031 [US2] Generate `data/results/model_metrics.json` with all scores and stratification reports
- [X] T032 [US2] Implement `filter_rare_classes()` in `code/modeling.py` to drop classes with < 5 samples before splitting, and verify via `tests/test_modeling.py::test_rare_class_exclusion`
- [X] T050 [US2] **Add Runtime Enforcement**: Wrap the `train_models` and `run_permutation_test` execution in a `signal`-based timeout handler (or `subprocess` with timeout) to ensure the total modeling phase remains within a reasonable timeframe (leaving 2 hours for ingestion/reporting). If timeout is hit, log `CRITICAL: Modeling phase exceeded 4h limit` and save partial results to `data/results/partial_metrics.json` before exiting. (Addresses SC-005 Runtime Constraint)

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

---

## Phase 6: Reporting & Compliance (Polish)

**Purpose**: Finalize reports, ensure compliance, and update project state.

- [X] T043 [P] Implement `generate_final_report()` in `code/report.py`: Combine metrics, SHAP analysis, and disclaimers. **Include**: Calculate Confidence Intervals (CIs) for all metrics via bootstrapping (**sufficient iterations**) and export CI bounds in the final report JSON. (Addresses Plan Phase 4, Task 4.2)
- [X] T044 [P] Execute `code/hash_artifacts.py` to update `state/projects/PROJ-314-predicting-the-impact-of-composition-on-weibull-modulus.yaml` with new content hashes for all files in `data/` and `code/` (Corrected path per Constitution Principle V)
- [X] T045 [P] Run `bash scripts/validate_quickstart.sh` to validate the quickstart guide against the implemented pipeline; success condition: Exit code 0 and no errors in `logs/validation.log`. **Dependency**: Requires T016a (quickstart.md generation) to be complete.
- [X] T046 [P] **Measure Pipeline Runtime**: Execute the full pipeline (Ingestion -> Modeling -> SHAP) and log the total duration to `data/results/runtime_metrics.json`. Verify duration is < 6 hours to satisfy SC-005. If duration > 6 hours, log error "Pipeline runtime exceeded 6 hours limit" and exit with code 1. (Addresses SC-005 Verification)
- [X] T047 [P] Update `docs/data_gap_protocol.md` with the exact report generation steps defined in T017b (N < 30 halting logic and `data_availability_report.json` schema). **Dependency**: Requires T016b (docs/data_gap_protocol.md creation) to be complete.
- [X] T051 [P] **Final Compliance Audit**: Run a script `code/audit_compliance.py` that checks:
 1. `data/reports/final_report.md` and `data/reports/final_report.json` contain the required disclaimer "These results represent statistical associations only..." (FR-008).
 2. The word "cause" is absent from the `conclusion` field of `data/reports/final_report.json`.
 3. `data/processed/` contains no NaN values in primary predictor columns.
 4. All external data sources in `data/raw/` have corresponding checksums in `data/artifacts/`.
 5. Exit with code 1 if any check fails. (Addresses Constitution Principles I, III, and FR-008)

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
- **User Story 2 (P2)**: Depends on US1 (needs `data/processed/` dataset). **Specific Dependency**: T026 requires T018f to be complete.
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
- **Note on T017c**: Added to explicitly execute and verify the Data Gap Report generation. Corrected logic to use 29 rows total.
- **Note on T030**: Logic corrected to align with FR-005.5 (Drop <= 10% -> Leakage; Drop > 10% -> Sufficient) and explicit file retrieval added. Dependency on T018a added.
- **Note on T041**: Added execution trigger and verification step.
- **Note on T046**: Added to verify SC-005 runtime constraint.
- **Note on T044**: Corrected state file path.
- **Note on T029**: Specified 1000 iterations, random seed, and combined MAE/p-value check.
- **Note on T018c/d/e/g**: Added to explicitly implement FR-001 data fetching for specific repositories with "Fail Loudly" logic and removed local CSV fallbacks.
- **Note on T010b**: Added to verify citation validation log creation.
- **Note on T027b**: Added to ensure model persistence for T030.
- **Note on Ordering**: T018c/d/e/g (Fetch) -> T017 (Validate Gap) -> T018a (Derive Group) -> T018f (Clean) order enforced.
- **Note on T052**: Added to enforce memory check for large datasets (replace T048).
- **Note on T049**: Added to enforce "Fail Loudly" on data fetch failures, preventing synthetic fallbacks, but retaining T018g as the only allowed fallback.
- **Note on T050**: Added to enforce strict runtime limits on modeling tasks.
- **Note on T051**: Added final compliance audit to ensure all constitutional and functional requirements are met before project closure.
- **Note on T028b**: Moved before T028 to ensure baseline metrics are available for evaluation and leakage checks.
- **Note on T018a/T018f**: Split to ensure group derivation precedes imputation.
- **Note on T018a Status**: Changed to [ ] to reflect dependency on T018c/d/e/g and T017.
- **Note on T020**: Explicitly listed primary predictor columns for self-containment.
- **Note on T048**: Removed as it was based on a misinterpretation of the Constitution.
- **Note on T016c-1/2/3**: Removed [P] tag to reflect sequential dependencies.
- **Note on T006/007**: Removed [P] tag to reflect dependency on T016c-1.
- **Note on T018g**: Added to implement the 'Curated Literature Dataset' fallback as required by Plan Phase 0, Task 0.2.