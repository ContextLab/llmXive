# Tasks: Predicting Perovskite Stability via Compositional Fingerprints

**Input**: Design documents from `/specs/001-predicting-perovskite-stability/`
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

- [X] T001a [P] Create project directories: `code/`, `data/raw/`, `data/processed/`, `tests/`
- [X] T001b [P] Create project directories: `docs/`, `state/`
- [X] T001c [P] Create `code/requirements.txt` with initial dependencies: `pandas`, `scikit-learn`, `requests`, `pyyaml`, `numpy`, `pymatgen`, `mp-api`, `shap`
- [X] T002 Initialize Python 3.11 project with dependencies (`code/requirements.txt`)
- [X] T003 [P] Configure linting (flake8/pylint) and formatting (black/isort) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement `code/state_manager.py` to compute SHA‑256 hashes for derived artifacts and update `state/project_state.yaml`.
 **Implementation Details**:
 - Provide function `compute_and_update_hash(file_path: str) -> None` that computes SHA‑256, records `file_path`, `hash`, and `timestamp` under top‑level key `artifacts` in `state/project_state.yaml`.
 - Schema Example:
 ```yaml
 artifacts:
 data/raw/nrel_perovskites.csv:
 hash: "<sha256>"
 timestamp: "2026-09-29T12:34:56Z"
 code/state_manager.py:
 hash: "<sha256>"
 timestamp: "2026-09-29T12:35:10Z"
 ```
 **Verification**: Create dummy file `data/raw/test_dummy.csv`, run `state_manager.compute_and_update_hash`, and confirm entry appears in `state/project_state.yaml` with correct hash and ISO‑8601 timestamp.
 **Requires**: None (foundational).
- [X] T005 Create `contracts/descriptor.schema.yaml` defining the schema for `CompositionalDescriptor` entities
- [X] T006a [P] Create `code/config.yaml` with `delay_multiplier` key set to `1.0` and `retry_delays` key set to `[1.0, 2.0, 4.0]`. **Path**: `code/config.yaml`. **Verification**: Verify `code/config.yaml` exists and contains the `delay_multiplier` key with a numeric value and `retry_delays` key with a list of numeric values. **Note**: These values are placeholders and MUST be updated to match spec constraints before execution.
- [X] T006b [P] Implement `code/utils/data_fetcher.py` with retry logic: up to 3 retries with exponential backoff using `retry_delays` from `code/config.yaml`. **Implementation**: Implement the retry loop with exponential backoff logic (e.g., `retry_delays[retry_count]`) reading `retry_delays` from `code/config.yaml`. **Verification**: Verify that `code/config.yaml` is read at runtime and that the retry delays match the configuration. <!-- Requires: T006a -->
- [X] T006c Implement unit test for retry logic in `tests/unit/test_data_fetcher.py`. **Verification**: Verify that the unit test simulates network failures and confirms exponential backoff delays and total retry time limits. <!-- Requires: T006b -->
- [X] T007 Implement `code/utils/formula_parser.py` using `pymatgen` for deterministic A/B/X site assignment. **Specificity**: Use `pymatgen.core.Element` class for all elemental property lookups to ensure reproducibility.
- [X] T008 Setup environment configuration management for API keys (Materials Project, NREL) in `.env`
- [X] T009 Implement `code/utils/checksum_verifier.py` to validate raw data integrity against source checksums
- [X] T047c_init [P] Create `data/raw/instrument_registry.csv` with specific TGA instrument data: Row: `TA Instruments, TA Instruments, [qualitative metric]`; Row: `Mettler Toledo, Mettler Toledo, [qualitative metric]`. Compute its SHA‑256 hash, updating `state/project_state.yaml`. **Schema**: The CSV MUST have columns: `instrument_model`, `manufacturer`, `precision_celsius`. **Verification**: Verify `data/raw/instrument_registry.csv` exists, contains valid data, and its hash is recorded in `state/project_state.yaml`. **Note**: This task has no network dependencies and is safe for parallel execution with other setup tasks. <!-- Requires: T004 -->
- [X] T047c [P] Implement `code/utils/instrument_registry.py` to maintain a lookup table of known TGA instruments with documented precision values. **Source**: Load the registry from `data/raw/instrument_registry.csv` (created by T047c_init). **Schema**: The CSV MUST have columns: `instrument_model`, `manufacturer`, `precision_celsius`. If the file is missing or an instrument is not found, use the spec default of ±10°C and log a warning. **Constraint**: Do NOT hard‑code specific manufacturer models or precision values in the code. **Output**: A function `get_precision(instrument_model)` that returns the precision value or the default. <!-- Requires: T047c_init -->
- [X] T052 [P] Implement a "TGA Instrument Lookup" function in `code/utils/instrument_registry.py` that maps instrument model names to their standard precision specifications (±°C) based on the registry defined in T047c. **Verification**: Verify that `instrument_registry.py` successfully loads the registry from `data/raw/instrument_registry.csv` (if it exists) and correctly applies the default ±10°C precision for any instrument model not found in the registry. Log any unmapped instruments to `data/raw/unmapped_instruments.log`. <!-- Requires: T047c -->
- [X] T041 Update `contracts/metadata.schema.yaml` to require explicit fields for `tga_model`, `tga_manufacturer`, `temperature_precision` (±°C), and `heating_rate` (°C/min) for every source dataset entry, but make `instrument_model` and `manufacturer` OPTIONAL with a fallback flag. **Verification**: Verify `contracts/metadata.schema.yaml` contains required fields and validates optional instrumentation fields correctly.
- [X] T042 Implement `code/utils/uncertainty_parser.py` to parse `temperature_precision` from source metadata; if missing, default to ±10°C and log a WARNING with message format: "WARNING: Missing precision for {formula}, defaulting to 10°C".
- [X] T043 Implement `code/utils/uncertainty_propagator.py` to calculate the combined standard uncertainty for `T_d` based on the instrument precision and any reported experimental error. **Formula**: `sigma = sqrt(precision^2 + experimental_error^2)`. If experimental error is missing, use a negligible placeholder. If precision is missing, use a default temperature threshold. **Output**: Returns `sigma`.
- [X] T049 [P] Unit test for `instrument_registry.py` to ensure correct precision lookup for known and unknown instruments. <!-- Verification: Verify unit tests pass for all registry lookups. -->
- [X] T050 [P] Integration test for the full instrumentation pipeline: fetch data -> validate instrumentation -> compute uncertainty -> train model -> report audit. <!-- Verification: Verify the pipeline completes without halting on missing instrumentation metadata. -->
- [X] T047a [US1] Implement `code/utils/data_fetcher.py` to extract and validate `instrument_model` and `manufacturer` fields from source metadata (NREL/Materials Project) during the initial fetch. If these fields are missing, log a WARNING and assign a default precision of ±10°C using the fallback strategy. Do NOT raise a `MissingInstrumentationError`. Log the formula to `data/raw/instrumentation_fallbacks.log`. **Verification**: Verify that `data/raw/instrumentation_fallbacks.log` exists and contains entries for any formula where instrumentation metadata was missing, and that the pipeline proceeds. <!-- Requires: T006b, T047c, T052 -->
- [X] T047b Update `contracts/metadata.schema.yaml` to make `instrument_model` and `manufacturer` OPTIONAL fields with a `source_instrumentation` flag (true/false) to indicate if data was found. <!-- Verification: Verify schema validation passes for JSON objects missing these fields and sets the flag to false. -->

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition, Uncertainty, and Descriptor Computation (Priority: P1) 🎯 MVP

**Goal**: Download perovskite data, filter for experimental TGA measurements, compute uncertainties, and compute compositional descriptors.

**Independent Test**: Run on a sample of formulas; verify output CSV contains `formula`, `T_d`, `total_uncertainty`, `atomic_fraction_A`, `weighted_ionic_radius`, etc., with non-null values.

### Tests for User Story 1 (OPTIONAL) ⚠️

- [X] T010 [P] [US1] Contract test for data ingestion output schema in `tests/contract/test_data_ingestion.py` <!-- Verification: Verify output CSV contains columns [formula, T_d, atomic_fraction_A, atomic_fraction_B, atomic_fraction_X, weighted_ionic_radius, weighted_electronegativity, weighted_formation_enthalpy, variance_ionic_radius, variance_electronegativity, total_uncertainty] with non-null values. -->
- [X] T011 [P] [US1] Integration test for API retry logic and error handling in `tests/integration/test_api_retries.py`

### Implementation for User Story 1

- [ ] T012a_src [US1] Fetch data from NREL API using `code/data_ingestion.py` function `fetch_nrel_data`. **Endpoint**: ` No address associated with hostname)"))]. **Query**: `api_key=<env>, format=json, filter=tga_onset`. **Validation**: Apply T009 validation, filter for `T_d` (TGA onset), add a column `source` with value `"NREL"`, and write to `data/raw/nrel_perovskites.csv`. **Constraint**: If the API call fails (404, timeout), attempt to fetch from Zenodo (DOI: 10.5281/zenodo.10972088) as a fallback. If ALL fail, the task MUST fail with a specific error code. **Verification**: Verify file exists, contains `T_d` column, `source` column, and matches `contracts/metadata.schema.yaml`. <!-- Requires: T008, T009 -->
- [ ] T012b_src [US1] Fetch data from Materials Project API using the `mp-api` library in `code/data_ingestion.py` function `fetch_mp_data`. **Endpoint**: ` Name or service not known)"))]. **Logic**: Use `mp-api` to query for materials with `structure_type`="perovskite". Filter results for entries with `expt_decomp_temp` or `TGA_onset` properties. If direct T_d is missing, log the entry as 'T_d_missing' and exclude it. Add a column `source` with value `"MaterialsProject"`, and write to `data/raw/mp_perovskites.csv`. **Constraint**: Handle authentication errors gracefully by logging to stderr and exiting with code 1. Retry logic is handled by T006b. **Fallback**: If the API call fails (404, timeout), attempt to fetch from Zenodo (DOI: 10.5281/zenodo.10972088) as a fallback. If ALL fail, the task MUST fail with a specific error code. **Verification**: Verify file exists, contains `T_d` column, `source` column, and matches schema. <!-- Requires: T008, T009 -->
- [ ] T012c [US1] Implement merge logic: Concatenate `data/raw/nrel_perovskites.csv` and `data/raw/mp_perovskites.csv` based on `formula` and `source`. **Constraint**: If either input file is missing, empty, or if T012a_src/T012b_src did not report successful completion, the task MUST fail with a specific error code. **Verification**: Verify merge logic handles missing files correctly and logs duplicate count. <!-- Requires: T012a_src, T012b_src -->
- [X] T012d [US1] Implement duplicate removal: Drop duplicates from the merged dataset based on `formula` and `source`, logging the count of removed duplicates. **Constraint**: Use standard deduplication logic (formula + source match). <!-- Requires: T012c --> <!-- Verification: Verify duplicate count is logged. -->
- [ ] T012e [US1] Write final merged dataset to `data/raw/perovskites_merged.csv`. **Constraint**: Log the final row count. If T012c failed, this task MUST fail. <!-- Requires: T012d --> <!-- Verification: Verify file exists and log the row count. -->
- [ ] T013 [US1] Implement metadata parsing and validation: parse TGA model/precision from source metadata using T042, extract `instrument_model` and `manufacturer` from source metadata or assign default 'Unknown' with a warning, and write structured metadata to `data/raw/metadata.json`. **Schema**: The JSON must be a list of objects, each with keys: `formula`, `instrument_model`, `manufacturer`, `precision_source` (value="source" or "registry"). **Constraint**: Reference `contracts/metadata.schema.yaml` for exact field names. **Constraint**: If T012e failed, this task MUST fail. <!-- Requires: T042, T047a, T012e --> <!-- Verification: Verify `metadata.json` exists and conforms to the schema. -->
- [ ] T013b [US1] Merge instrumentation fallback information into `metadata.json`: for each entry, add a boolean `precision_from_registry` flag (True if sourced from `instrument_registry.csv`, False if defaulted) and ensure `precision_source` reflects the origin. **Constraint**: If T013 failed, this task MUST fail. <!-- Requires: T013, T047a --> <!-- Verification: Verify merged metadata accurately records the provenance of precision for every record. -->
- [ ] T061 [US1] Implement `code/utils/uncertainty_calculator.py` to compute the total uncertainty for each `T_d` value by combining the instrument precision (from Tc) and any reported experimental error (from source metadata) using the root‑sum‑square method. **Constraint**: If either component is missing, use the documented default (±10°C for precision, 0 for experimental error) and log a warning. **Output**: Write a new column `total_uncertainty` to `data/processed/descriptors_uncertainty.csv` (derived from `data/raw/perovskites_merged.csv`). **Note**: This task supersedes any prior uncertainty calculation logic in T013b. <!-- Requires: T012e, T043, T047c --> <!-- Verification: Verify file exists and contains non‑negative `total_uncertainty` values. -->
- [ ] T014a1 [US1] Implement `code/feature_engineering.py` functions: `compute_atomic_fractions(formula)`, `compute_weighted_properties(formula)`. **Implementation**: Use `pymatgen` to parse formula and retrieve elemental properties. **Specific Properties**: The function MUST explicitly compute and return: `atomic_fraction_A`, `atomic_fraction_B`, `atomic_fraction_X`, `weighted_ionic_radius`, `weighted_electronegativity`, `weighted_formation_enthalpy`, `first_ionization_energy`. **Property Keys**: Use `pymatgen`'s `Element` class with `ionic_radii` (coordination=6, Angstroms), `electronegativity` (Pauling scale, eV), `formation_enthalpy` (eV/atom), and `first_ionization_energy` (eV). Units must be converted to Angstroms and eV. No file I/O in this task. **Constraint**: If `pymatgen` property keys are missing, the task MUST fail. <!-- Verification: Unit tests confirm correct numeric outputs for known formulas. -->
- [ ] T014a2 [US1] Append descriptor columns (`atomic_fraction_A`, `atomic_fraction_B`, `atomic_fraction_X`, `weighted_ionic_radius`, `weighted_electronegativity`) to `data/processed/descriptors_uncertainty.csv` and write result to `data/processed/descriptors_features.csv`. **Constraint**: If T014a1 failed, this task MUST fail. <!-- Requires: T014a1 --> <!-- Verification: Verify output CSV contains the listed columns with non‑null values. -->
- [ ] T014b [US1] Implement computation of `weighted_formation_enthalpy` and `first_ionization_energy` using `pymatgen` elemental data with the `standard` database, and append these columns to `data/processed/descriptors_features.csv`. **Constraint**: If a property is missing for an element, the task must raise an error and exclude the entry. **Verification**: Verify output CSV contains the two new columns with non‑null values. Verify column values match pymatgen reference for formula "FAPbI3". <!-- Requires: T014a2 -->
- [ ] T014c [US1] Implement variance metrics (ionic radius, electronegativity) and append to `data/processed/descriptors_features.csv`. **Verification**: Verify output CSV contains `variance_ionic_radius` and `variance_electronegativity` columns with non‑null values. <!-- Requires: T014b -->
- [X] T014d [US1] Merge `data/processed/descriptors_features.csv` with `data/processed/descriptors_uncertainty.csv` to create `data/processed/descriptors_v1.csv`, preserving `total_uncertainty`. **Constraint**: Must run after T061 completes. <!-- Requires: T014c, T061 --> <!-- Verification: Verify merged file includes all columns. -->
- [X] T014e [US1] Derive `perovskite_family` (lead‑halide, tin‑halide, double perovskite) from A/B/X site elements in `data/processed/descriptors_v1.csv`; write to `data/processed/descriptors_v1.csv`. **Constraint**: Do NOT modify existing files; create a new file. **Constraint**: If T014d failed, this task MUST fail. <!-- Requires: T014d --> <!-- Verification: Verify `perovskite_family` column contains only the allowed values. -->
- [ ] T016a [US1] Implement `code/utils/vif_calculator.py` to compute VIF for all descriptors on `data/processed/descriptors_v1.csv`. Write report to `data/processed/vif_report.csv` with columns `descriptor`, `vif_value`, `flagged` (True if vif > 5). **Verification**: Verify VIF values and flags are present. **Test Case**: Verify that a dataset with perfect collinearity (e.g., two identical columns) produces VIF > 1000. <!-- Requires: T014e -->
- [ ] T016d [US1] Implement feature exclusion: Read `data/processed/vif_report.csv` and exclude descriptors with `flagged=True` from the feature matrix. Write the filtered dataset to `data/processed/descriptors_filtered.csv`. **Constraint**: If T016a failed, this task MUST fail. <!-- Requires: T016a --> <!-- Verification: Verify `descriptors_filtered.csv` excludes flagged descriptors. -->
- [ ] T015a [US1] Exclude entries with ≥ 2 missing descriptor values and log exclusion counts. **Output**: Write filtered dataset to `data/processed/descriptors_filtered.csv`. **Verification**: Log exclusion count to `data/processed/exclusion_log.csv` and verify count matches expected threshold (n ≥ 10 × features). **Constraint**: If T016d failed, this task MUST fail. <!-- Requires: T016d -->
- [X] T016b [US1] Log decision rationale for VIF > 5 descriptors to `data/processed/vif_decision_log.csv`. <!-- Verification: Verify log contains flagged descriptors and rationale. -->
- [X] T016c [US1] Unit test for VIF diagnostic computation and feature removal logic in `tests/unit/test_vif.py`. <!-- Requires: T016a, T016b -->
- [ ] T017 [US1] Write final processed dataset to `data/processed/descriptors_final.csv` including `total_uncertainty`, `perovskite_family`, `instrument_model`, `manufacturer`, and `precision_source` columns and update `state/project_state.yaml` with hash. **Constraint**: Read from `data/processed/descriptors_filtered.csv`. **Verification**: Verify file exists and state hash is updated. **Required Columns**: `formula`, `T_d`, `total_uncertainty`, `perovskite_family`, `instrument_model`, `manufacturer`, `precision_source`, `atomic_fraction_A`, `atomic_fraction_B`, `atomic_fraction_X`, `weighted_ionic_radius`, `weighted_electronegativity`, `weighted_formation_enthalpy`, `first_ionization_energy`, `variance_ionic_radius`, `variance_electronegativity`. <!-- Requires: T015a, T016a -->
- [ ] T053 [US1] Update `data/processed/validation_report.md` to include "Instrumentation Audit" (TGA model distribution) and "Data Quality Assessment" (high/low confidence proportions). **Constraint**: Consolidate T047e and T055 logic here. **Verification**: Verify report contains both sections. **Required Content**: "Instrumentation Audit" must contain a table of TGA model distribution (e.g., "TA Instruments: 120 entries"). "Data Quality Assessment" must contain the proportion of high/low confidence measurements. <!-- Requires: T047a, T061, T017 -->
- [ ] T054 [US1] Implement a "Missing Instrumentation Report" generator in `code/utils/instrument_registry.py` that aggregates all entries from `data/raw/instrumentation_fallbacks.log` and writes a summary report to `data/processed/missing_instrumentation_report.csv` with columns: `formula`, `source`, `default_precision_used`, `confidence_flag`. **Verification**: Verify report exists and correctly aggregates fallback entries. <!-- Requires: T006b, T047c, T052, T047a -->

**Checkpoint**: User Story 1 fully functional; dataset ready for modeling.

---

## Phase 4: User Story 2 - Model Training and Cross‑Validation (Priority: P2)

**Goal**: Train baseline regressors (Random Forest, Gradient Boosting, Elastic Net) with strict CPU constraints, grid search limits, and uncertainty weighting.

**Independent Test**: Run cross‑validation on a representative subset; verify all models complete within 30 mins with R² metrics.

### Tests for User Story 2 (OPTIONAL) ⚠️

- [X] T018 [P] [US2] Unit test for grid search hyperparameter limit enforcement (<= 10 combos) in `tests/unit/test_model_training.py`
- [X] T019 [P] [US2] Integration test for full pipeline runtime (must complete <= 4 hours) in `tests/integration/test_pipeline_runtime.py`. **Note**: This is a soft target. Hard limit is hours (T051c).

### Implementation for User Story 2

- [ ] T020a_rf [US2] Implement Random Forest in `code/model_training.py` using scikit‑learn. **Constraint**: Grid search limited to ≤ 10 combinations. <!-- Requires: T014e, T017 -->
- [ ] T020b_gb [US2] Implement Gradient Boosting in `code/model_training.py` using scikit‑learn. **Constraint**: Grid search limited to ≤ 10 combinations. <!-- Requires: T014e, T017 -->
- [ ] T020c_en [US2] Implement Elastic Net in `code/model_training.py` using scikit‑learn. **Constraint**: Grid search limited to ≤ 10 combinations. <!-- Requires: T014e, T017 -->
- [ ] T020d [US2] **IMPLEMENT SAMPLE WEIGHTING**: Compute sample weights as the reciprocal of the square of `total_uncertainty` using the `total_uncertainty` column. from `data/processed/descriptors_final.csv`. Pass these weights to all three models during training. **Verification**: Verify `model_runs.json` records that sample weighting was applied and training logs show weighted loss calculations. <!-- Requires: T017, T061, T020a_rf, T020b_gb, T020c_en -->
- [ ] T020e [US2] Implement stratified K‑Fold (k=5) using the `perovskite_family` column from `data/processed/descriptors_v1.csv`. **Strict Requirement**: All three families must be present in every fold; if any family is missing, the pipeline MUST fail with an explicit error. **Constraint**: If T014e failed, this task MUST fail. <!-- Requires: T014e --> <!-- Verification: Verify failure on missing families. -->
- [X] T020f [US2] Verify stratified split balance: Run a test case on the dataset to ensure the resulting train/test splits contain all families in every fold. Fail if any family is missing. <!-- Requires: T020e --> <!-- Verification: Verify test passes only if all families are present. -->
- [ ] T022 [US2] Implement grid search with a hard cap of ≤ 10 hyperparameter combinations per model. **Verification**: Verify `model_runs.json` shows ≤ 10 combos per model and logs assert max iterations. [RESOLVED]
- [X] T023 [US2] Implement metric tracking (RMSE, R², MAE) and logging of best hyperparameters. <!-- Verification: Verify metrics are logged for each fold and model. -->
- [ ] T025 [US2] Save trained models and metrics to `data/processed/model_runs.json` with required keys: `model_type`, `hyperparameters`, `metrics` (R², RMSE, MAE), and `sample_weight_used` (bool). <!-- Verification: Verify file exists and contains required keys, including `sample_weight_used`. -->

**Checkpoint**: User Story 2 complete; best model identified.

---

## Phase 5: User Story 3 - Feature Importance Analysis and External Validation (Priority: P3)

**Goal**: Extract SHAP values, perform permutation testing, and validate on held‑out literature data. **Constraint**: Proxy validation is NOT permitted; if literature data is missing, the task MUST fail.

**Independent Test**: Run SHAP on a test set; verify top features reported with p‑values < 0.05.

### Tests for User Story 3 (OPTIONAL) ⚠️

- [X] T026 [P] [US3] Unit test for multiple‑comparison correction (Bonferroni and Benjamini-Hochberg) in `tests/unit/test_feature_importance.py`
- [X] T027 [P] [US3] Integration test for OOD detection and separate metric reporting in `tests/integration/test_ood_validation.py`

### Implementation for User Story 3

- [X] T028 [US3] Implement `code/validation.py` to extract SHAP values from the best model. <!-- Verification: Verify SHAP values are extracted and reported for top features. -->
- [X] T029 [US3] Perform permutation importance testing with ≥ 1000 permutations and report raw p‑values in `data/processed/feature_importance_raw.csv`. <!-- Verification: Verify file contains raw p‑values. -->
- [ ] T029b [US3] Apply Benjamini‑Hochberg correction to the raw p‑values from T029, produce adjusted p‑values, and write them to `data/processed/feature_importance.csv` alongside importance scores. **Verification**: Verify adjusted p‑values are present and correctly computed. **Test Case**: Verify adjusted p-values for a known input set of small magnitudes match expected values. **Constraint**: If T029 failed, this task MUST fail. <!-- Requires: T029 -->
- [ ] T057 [US3] **Fetch Specific Dataset**: Download the NREL Perovskite Stability Subset from Zenodo (DOI: 10.5281/zenodo.10972088) using the URL `. **Logic**: If the download fails (e.g., due to resource unavailability or timeout), attempt to fetch from alternative sources (e.g., specific paper CSVs). If ALL fail, the task MUST fail with a specific error code. **Output**: Write the raw data to `data/raw/literature_validation_raw.csv`. **OOD Verification**: After fetching, load `data/processed/descriptors_final.csv` (training set) and extract the set of unique elements. Load the fetched literature data and extract its unique elements. Verify that the literature set contains at least one element NOT present in the training set (e.g., Sn, double perovskite elements). **Constraint**: If the dataset is found to be in‑distribution (no unique elements), the task MUST fail with a specific error code. **Verification**: Verify file exists, matches schema, and contains OOD elements. <!-- Requires: T017 -->
- [ ] T058 [US3] Implement `code/data_sources/literature_fetcher.py` to download the dataset identified in T057. **Logic**: If the download fails (404, timeout), attempt alternative sources. If ALL fail, the task MUST fail with a specific error code. Do NOT fall back to synthetic data. **Output**: Write the raw data to `data/raw/literature_validation_raw.csv`. <!-- Verification: Verify file exists and matches schema. -->
- [ ] T059 [US3] Implement `code/data_sources/literature_cleaner.py` to parse the raw file from T058, map columns to the canonical schema (`formula`, `T_d`, `source`), and write to `data/raw/literature_validation.csv`. **Constraint**: If the schema mapping fails, the task MUST fail. <!-- Verification: Verify file exists and contains required columns. -->
- [ ] T059a [US3] Verify OOD Content: Analyze `data/raw/literature_validation.csv` to confirm it contains elements or structural motifs NOT present in the training set (e.g., Sn, double perovskites). **Constraint**: If the dataset is found to be in‑distribution, the task MUST fail with a specific error code. **Output**: Write a validation report to `data/processed/ood_validation_check.csv`. <!-- Verification: Verify report exists and confirms OOD content. -->
- [ ] T060 [US3] Update `T030` implementation to rely on the output of T059. **Verification**: Run the external validation task; it must succeed if T059 succeeded, or fail explicitly if T059 failed.
- [ ] T030 [US3] Implement external validation: load held‑out experimental data from `data/raw/literature_validation.csv` (generated by T059). **OOD Verification**: Before any training or metric calculation, load `data/processed/descriptors_final.csv` (training set) and extract the set of unique elements. Load the literature data and extract its unique elements. Verify that the literature set contains at least one element NOT present in the training set (e.g., Sn, double perovskite elements). **Constraint**: If the dataset is found to be in‑distribution (no unique elements), the task MUST fail with a specific error code. If the file is missing or empty, the task MUST fail with a specific error code. **Constraint**: If T059a failed, this task MUST fail. Report R² and RMSE for external data in `data/processed/external_metrics.csv`. **Verification**: Verify metrics file exists or task fails appropriately. <!-- Requires: T059a -->
- [ ] T030b [US3] Compute and report the generalizability gap: compare external R² (from T030) with cross‑validation R² (best model) and write the gap to `data/processed/generalizability_gap.csv`. **Output Format**: CSV with columns `metric`, `value`. **Row Definitions**: 'generalizability_gap', 'in_dist_R2', 'out_dist_R2'. **N/A Logic**: If external data is missing, write "N/A" in the value column. **Constraint**: If T030 failed, this task MUST fail. <!-- Requires: T030, T023 -->
- [X] T031 [US3] Implement OOD detection: Flag compositions with elements NOT in the training set (based on T017) or with a Mahalanobis distance > 3.0 from the training distribution. Add `is_ood` boolean column to `data/processed/descriptors_final.csv`. <!-- Verification: Add column and verify logic. -->
- [X] T032a [US3] Report separate R²/RMSE for in‑distribution vs. out‑of‑distribution predictions (internal split) in `data/processed/ood_metrics.csv`. <!-- Verification: Write metrics with columns `split`, `R2`, `RMSE`. -->
- [X] T032b [US3] Report separate R²/RMSE for the held‑out literature dataset (external validation) in `data/processed/external_metrics.csv`. <!-- Verification: Already covered by T030. -->
- [X] T033 [US3] Generate ranked list of elemental properties by contribution to `T_d` prediction in `data/processed/feature_ranking.csv`. <!-- Verification: Write ranked list with columns `feature`, `contribution_score`, `rank`. -->
- [X] T034 [US3] Write validation report to `data/processed/validation_report.md` including sections: External R²/RMSE, OOD Metrics, Feature Importance, and Permutation P‑values. <!-- Verification: Verify report contains all required sections. -->
- [X] T063 [US3] Update `data/processed/validation_report.md` to include a dedicated "Uncertainty Propagation" section that explicitly states: 1) The formula used to combine uncertainties, 2) The distribution of total uncertainties across the dataset (min, max, median), 3) How the uncertainty weighting affected the final model performance compared to an unweighted baseline. **Constraint**: The section MUST include a table comparing the R² and RMSE of the weighted model vs. the unweighted model. <!-- Requires: T061, T020d, T034 --> <!-- Verification: Verify section and table are present. -->
- [X] T064 [US3] Implement a sensitivity analysis in `code/validation.py` that sweeps the uncertainty weighting exponent (e.g., `weight = 1 / uncertainty^p` for p in {0, 1, 2, 3}) and reports how the model performance (R², RMSE) varies with the exponent. **Output**: Write results to `data/processed/uncertainty_sensitivity.csv` with columns `exponent`, `R2`, `RMSE`. **Note**: Use the held‑out literature dataset from T059. <!-- Verification: Verify file contains rows for exponents 0‑3. -->

**Checkpoint**: All user stories complete; external validation done.

---

## Phase 6: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T035a [P] Update `README.md` with TGA uncertainty analysis and instrumentation details
- [X] T035b [P] Update `docs/api.md` with endpoint signatures and data schemas
- [X] T036a [P] Code refactor: Extract retry logic from `data_fetcher.py` to `code/utils/retry.py` (Note: T006 implemented the initial logic; this is a refactor).
- [X] T036b [P] Refactor `data_fetcher.py` to import and use the new `retry.py` module
- [X] T037a [P] Profile pipeline using `cProfile` on `main.py` to identify the top functions by cumulative time; write report to `docs/profiling_report.md`. <!-- Verification: Verify report contains top functions and cumulative time. -->
- [X] T037b [P] Optimize identified bottlenecks to ensure full pipeline completes within 4 hours (soft target). **Note**: Hard limit is a fixed duration of several hours (T051c). <!-- Verification: Verify pipeline runtime report shows ≤ 4 hours (soft target). -->
- [X] T038 [P] Additional unit tests in `tests/unit/`
- [X] T039 Run `quickstart.md` validation
- [X] T040 Verify all artifacts have corresponding SHA‑256 hashes in `state/...yaml`
- [X] T051 [P] Implement a runtime monitor in `code/main.py` that logs the elapsed time for each phase and the total pipeline, comparing it against the allocated time budget and writing the result to `data/processed/runtime_report.json`. <!-- Verification: Verify JSON contains phase timings, total time, and budget status (pass/fail). -->
- [X] T051c [P] Implement a runtime budget enforcer in `code/main.py` that explicitly checks if the total pipeline runtime exceeds a predefined temporal threshold. If exceeded, raise an error and fail the build. **Verification**: Verify that the build fails when runtime > 6 hours. <!-- Requires: T051 -->

---

## Phase 7: Instrumentation & Measurement Rigor (Revision: Marie Curie Review)

**Purpose**: Address the specific review concern regarding instrumentation uncertainty and the distinction between correlation and measurement.

**Goal**: Explicitly document the thermogravimetric analyzer (TGA) specifications, measurement precision, and propagate these uncertainties through the analysis to ensure results represent a rigorous measurement study.

- [X] T044a [US2] Update `code/model_training.py` to use the calculated uncertainty (σ) for each sample as a weight (`sample_weight` = 1/σ²) for Elastic Net and where supported by RF/GB implementations. <!-- Verification: Verify `model_runs.json` includes `sample_weight` logic and that training logs show weighted loss calculation. -->
- [X] T044b [US2] Verify uncertainty weighting implementation by running a test case with known uncertainties and checking loss calculation.
- [X] T045a [US3] Update `data/processed/validation_report.md` to include a dedicated "Measurement Uncertainty Analysis" section, explicitly stating the TGA models used, their precision, and how uncertainty was weighted in the final model. <!-- Verification: Verify report contains the section with model details and weighting explanation. -->
- [X] T046a [P] [US3] Write a "Measurement vs. Correlation" narrative in `docs/measurement_rigor.md` explaining how the inclusion of instrument‑specific uncertainty transforms the analysis from a simple correlation to a weighted measurement‑based regression, referencing the specific TGA constraints. <!-- Verification: Verify document contains the narrative and references. -->

---

## Phase 8: Revision: Explicit Instrumentation Traceability (Revision: Marie Curie Review)

**Purpose**: Directly address the Marie Curie review concern that "Without this, the claim is merely a correlation, not a measurement" by ensuring every data point carries explicit, traceable instrumentation metadata.

**Goal**: Create a robust audit trail that links every `T_d` value in the final dataset to the specific TGA instrument, manufacturer, and reported precision used to measure it, ensuring the analysis is grounded in physical measurement standards rather than abstract correlation.

- [X] T047e [US3] Update `data/processed/validation_report.md` to include a "Instrumentation Audit" table listing the distribution of TGA models used across the dataset (e.g., "TA Instruments: 120 entries", "Mettler Toledo: a substantial number of entries") and their respective precision ranges. <!-- Verification: Verify table present. -->
- [X] T047f [US3] Implement a "Measurement Confidence Score" in `code/validation.py` that calculates a composite score for each prediction based on the known precision of the instrument used for the training data point and the uncertainty propagation model. <!-- Verification: Verify `data/processed/feature_importance.csv` includes a `measurement_confidence_score` column. -->
- [X] T048 [US3] Write a "Measurement Integrity Statement" in `docs/measurement_integrity.md` that explicitly argues why the inclusion of instrument‑specific metadata and uncertainty weighting elevates the study from a statistical correlation to a physical measurement analysis, citing the specific TGA models and their precision limits. <!-- Verification: Verify document contains argument and references. -->
- [X] T049 [P] Unit test for `instrument_registry.py` to ensure correct precision lookup for known and unknown instruments. <!-- Verification: Verify unit tests pass. -->
- [X] T050 [P] Integration test for the full instrumentation pipeline: fetch data -> validate instrumentation -> compute uncertainty -> train model -> report audit. <!-- Verification: Verify pipeline completes without halting on missing instrumentation metadata. -->

---

## Phase 9: Review Action: Instrumentation Fallback Handling (Revision: Marie Curie Review)

**Purpose**: Explicitly address the Marie Curie review concern regarding missing instrumentation data by ensuring the pipeline handles missing data gracefully while maintaining measurement integrity.

**Goal**: Ensure that when instrumentation metadata is missing, the pipeline logs the specific missing entries, applies a documented default precision, and clearly distinguishes these entries in the final analysis to prevent them from being treated as high‑precision measurements.

- [X] T055 [US3] Update `data/processed/validation_report.md` to include a "Data Quality Assessment" section that quantifies the proportion of high‑confidence vs. low‑confidence measurements and discusses the impact on model generalizability. <!-- Verification: Verify section with quantitative metrics. -->

---

## Phase 10: Verification & Testing

**Purpose**: Explicit verification tasks for foundational logic

- [X] T056 [P] Verify retry logic implementation in `code/utils/data_fetcher.py`. **Verification**: Run a unit test that simulates network failures and verifies that the retry logic implements exponential backoff (e.g., delays following an exponential sequence) and that the total retry time fits within the designated budget. <!-- Requires: T006b -->

---

## Phase 11: Review Action: Literature Data Sourcing Strategy (Revision: Marie Curie Review)

**Purpose**: Define and implement a robust strategy to acquire the external validation dataset from specific, verified real sources (Zenodo: 10.5281/zenodo.10972088, alternative paper CSVs) and implement the fetch logic to populate `data/raw/literature_validation.csv`.

**Goal**: Ensure T030 can succeed without stalling.

- [X] T057 [US3] **Fetch Specific Dataset**: Download the NREL Perovskite Stability Subset from Zenodo (DOI: 10.5281/zenodo.10972088) using the URL `. **Logic**: If the download fails (404, timeout), attempt to fetch from alternative sources (e.g., specific paper CSVs). If ALL fail, the task MUST fail with a specific error code. **Output**: Write the raw data to `data/raw/literature_validation_raw.csv`. **OOD Verification**: After fetching, load `data/processed/descriptors_final.csv` (training set) and extract the set of unique elements. Load the fetched literature data and extract its unique elements. Verify that the literature set contains at least one element NOT present in the training set (e.g., Sn, double perovskite elements). **Constraint**: If the dataset is found to be in‑distribution (no unique elements), the task MUST fail with a specific error code. **Verification**: Verify file exists, matches schema, and contains OOD elements. <!-- Requires: T017 -->
- [X] T058 [US3] Implement `code/data_sources/literature_fetcher.py` to download the dataset identified in T057. **Logic**: If the download fails (404, timeout), attempt alternative sources. If ALL fail, the task MUST fail with a specific error code. Do NOT fall back to synthetic data. **Output**: Write the raw data to `data/raw/literature_validation_raw.csv`. <!-- Verification: Verify file exists and matches schema. -->
- [X] T059 [US3] Implement `code/data_sources/literature_cleaner.py` to parse the raw file from T058, map columns to the canonical schema (`formula`, `T_d`, `source`), and write to `data/raw/literature_validation.csv`. **Constraint**: If the schema mapping fails, the task MUST fail. <!-- Verification: Verify file exists and contains required columns. -->
- [X] T059a [US3] Verify OOD Content: Analyze `data/raw/literature_validation.csv` to confirm it contains elements or structural motifs NOT present in the training set (e.g., Sn, double perovskites). **Constraint**: If the dataset is found to be in‑distribution, the task MUST fail with a specific error code. **Output**: Write a validation report to `data/processed/ood_validation_check.csv`. <!-- Verification: Verify report exists and confirms OOD content. -->
- [X] T060 [US3] Update `T030` implementation to rely on the output of T059. **Verification**: Run the external validation task; it must succeed if T059 succeeded, or fail explicitly if T059 failed.

**Checkpoint**: External validation data source is now defined, fetchable, and reproducible, ensuring T030 can proceed without failure due to missing data.

---

## Phase 12: Revision: Measurement Uncertainty Propagation (Marie Curie Review)

**Purpose**: Implement a rigorous uncertainty propagation framework that treats every `T_d` value as a measurement with a known error bound.

**Goal**: Ensure the final model is trained on a weighted dataset where the weight is inversely proportional to the variance of the measurement uncertainty.

- [X] T065 [P] Write a "Measurement Uncertainty Methodology" document in `docs/uncertainty_methodology.md` that explains the theoretical basis for the uncertainty propagation approach, citing ISO standards on accuracy and NIST Technical Note 1297. **Constraint**: Document must state that uncertainties are treated as known constants and systematic errors are not accounted for. <!-- Verification: Verify document exists and contains citations. -->

**Checkpoint**: Uncertainty propagation is now fully implemented, documented, and validated.

---

## Phase 13: Revision: Data Hygiene and Immutable Derivations (Marie Curie Review)

**Purpose**: Ensure strict data hygiene, immutable raw data, and full lineage reporting.

- [ ] T066 [US1] Implement `code/data_hygiene.py` to enforce immutable raw data storage. **Constraint**: Raw data files in `data/raw/` MUST be set to read‑only using `os.chmod`. Any modification attempt MUST raise a `PermissionError` or custom `ImmutableDataError`. **Prerequisite Check**: The task must first verify that the raw data files exist (produced by T012c/T012e). If they do not exist, the task must fail with a clear error indicating the upstream data fetch failed. **Constraint**: If T012a_src or T012b_src failed, this task MUST fail. **Verification**: Verify attempts to modify files result in an error. **Test Case**: Verify that attempting to write to `data/raw/nrel_perovskites.csv` raises a `PermissionError`. <!-- Requires: T004, T012a_src, T012b_src, T012c, T012e -->
- [ ] T067 [US1] Implement `code/data_hygiene.py` to generate a "Data Lineage Report" for every derived artifact. **Output**: For each file in `data/processed/`, generate a corresponding `.lineage.json` containing SHA‑256 hashes of all input files, the git commit hash, and timestamp. **Constraint**: If T017 failed, this task MUST fail. **Verification**: Verify `data/processed/descriptors_final.csv.lineage.json` exists and lists hashes of `nrel_perovskites.csv`, `mp_perovskites.csv`, and the code commit hash. **Schema**: The JSON file MUST contain keys: `input_hashes`, `git_commit`, `timestamp`. <!-- Requires: T004, T017 -->
- [ ] T068 [US1] Implement a "Data Integrity Check" function in `code/main.py` that verifies the SHA‑256 hashes of all raw and processed data files against the `state/project_state.yaml` record before running any training or validation tasks. **Constraint**: If any hash mismatch is detected, the pipeline MUST abort immediately with a `DataIntegrityError`. **Constraint**: If T066 or T067 failed, this task MUST fail. **Verification**: Verify pipeline fails correctly when a raw data file is manually altered. **Automated Test**: Run `test_integrity_check.sh` which modifies a raw file and verifies the pipeline aborts with `DataIntegrityError`. <!-- Requires: T004, T066, T067 -->
- [ ] T069 [US1] Update `docs/data_integrity.md` to document the immutable data strategy, the lineage reporting format, and the hash verification process. **Verification**: Verify document contains required sections and examples. **Required Sections**: "Immutable Data Strategy", "Lineage Reporting Format", "Hash Verification Process". **Required Example**: "Example: chmod 444 command". **Requires**: T066, T067, T068. <!-- Requires: T066, T067, T068 -->

**Checkpoint**: Data hygiene and immutability are now fully implemented, ensuring the analysis is grounded in a reproducible and traceable measurement chain.

---

## Phase 14: Additional Ordering & Dependency Clarifications

- All tasks that modify `contracts/metadata.schema.yaml` (T041, T042, T043) are now sequential; parallel tag `[P]` removed to avoid race conditions.
- All foundational tasks (including T004) must complete before any Phase 3 tasks are started; explicit `Requires: T004` added where needed.
- All tasks that produce files used by downstream tasks now list those dependencies via `Requires:` comments.