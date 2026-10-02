# Tasks: The Impact of Social Media Consumption Patterns on Cognitive Flexibility

**Input**: Design documents from `/specs/001-social-media-cognitive-flexibility/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 0: Data Research, Schema Definition & Feasibility (CRITICAL GATE)

**Purpose**: Define the data schema, verify the presence of required variables in the dataset source, AND document instrument sources BEFORE any full download or processing. This phase MUST pass before Phase 1 begins.
**⚠️ CRITICAL**: If this phase fails for ALL candidate datasets (including proxy/merge attempts), the project halts immediately with a "Data Gap" error. No data is downloaded.
**⚠️ NOTE**: This phase includes schema definition (T000) and instrument documentation (T016a) to break circular dependencies with Phase 1.

- [X] T000 [P0] **Schema Definition**: Create `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml`.
 - **Actions**:
 1. Create `contracts/dataset.schema.yaml` defining expected columns: `switching_index`, `cognitive_flexibility_score`, `age`, `total_screen_time`, `num_platforms`, `switching_frequency`.
 2. Create `contracts/output.schema.yaml` defining model output structure: `coefficients`, `p_values`, `r_squared`, `vif_scores`, `diagnostics`.
 - **Dependency**: T005 (Setup must exist to create `contracts/` directory).

- [X] T001 [P0] **Feasibility & Variable Check**: Implement `code/00_feasibility_check.py` to perform a lightweight check to verify the URL is accessible and the dataset contains tabular data.
 - **Logic**:
 1. **Define Candidates**: Loop through the following specific candidate datasets: `nrc/addhealth_wave4`, `hilda/hilda_2023`, `ess/ess_round10`.
 2. **Verify IDs & Fetch**: For each candidate, verify the ID exists by attempting to fetch the dataset card via `wget` or `curl` from `. If invalid, fallback to the next candidate or halt. **DO NOT use `datasets` library.**
 3. **Check Primary Variables**: Parse the fetched sample (first 10 lines or a small JSON/XML file). Verify `self_reported_switching_frequency` and `cognitive_flexibility_score` (or validated proxy like WCST) in the dataset schema/headers.
 4. **Validate Schema**: Load `contracts/dataset.schema.yaml`. Load the sample. Compare column names against the keys in the schema.
 5. **Proxy Check**: If primary variables are missing, **check for validated proxies (e.g., WCST)**. If a proxy is found, log it. If not, **HALT** with error: "Data Gap: Required variable [NAME] not found in verified dataset [URL]. Project cannot proceed per US-1 Scenario 2." **DO NOT attempt to find a proxy or merge if the primary is missing AND no proxy is found.**
 6. **Structured Output**: Write `results/feasibility_status.json` with fields: `status` (PASS/FAIL), `dataset_id` (selected dataset or null), `message` (details), `proxy_used` (boolean), `merged_datasets` (list). If PASS, include `proxy_used` (true/false) and `merged_datasets` (list).
 - **Dependency**: T005, T000.

- [X] T004 [P0] **Schema Validation**: Implement `code/00_schema_validation.py` to validate the fetched data against `contracts/dataset.schema.yaml` after feasibility (T001) but before full ingestion (T015).
 - **Logic**:
 1. **Read Feasibility**: Read `results/feasibility_status.json`. Ensure status is PASS.
 2. **Fetch Sample**: Use **`wget` or `curl`** to fetch the same sample used in T001.
 3. **Validate**: Load `contracts/dataset.schema.yaml`. Load the sample. Assert that all columns in the schema exist in the data. If mismatch, raise `ValueError` with "Data Gap: Downloaded data schema mismatch."
 4. **Output**: Write `results/schema_validation_status.json` with `status` (PASS/FAIL) and `details`.
 - **Dependency**: T001, T000, T005.

- [X] T016a [P0] **Instrument Documentation**: Create `data/instrument_sources.yaml` documenting survey sources AND implement the scoring logic script.
 - **Logic**:
 1. **Map URLs**: Construct a mapping of Dataset ID to Dataset Card URL using the pattern `.
 2. **Fetch Citations**: For each candidate dataset, fetch the dataset card documentation and parse the 'Citation' field to find the original validation source for the survey instruments.
 3. **Create Sources File**: Create `data/instrument_sources.yaml` with survey names, validation citations, and variable mappings. Validate URLs and ensure they are reachable.
 4. **Implement Scoring Script**: Create `code/02_score.py` (or similar) that implements the reproducible transformation logic from raw survey responses to the "platform-switching frequency" score as defined in the Constitution Principle VI. This script MUST be documented and executable.
 - **Dependency**: T001, T004, T005.

- [ ] T017a [P0] **Ingestion Setup**: Prepare `code/01_ingest.py` for instrumentation.
 - **Logic**:
 1. Define helper functions for data loading.
 2. Prepare the structure for instrument documentation integration.
 - **Dependency**: T016a

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, basic structure, contract definitions, and schema validation.

- [X] T005 [P] **Project Setup**: Create project directories and configuration files.
 - **Actions**:
 1. Create directories: `data/raw`, `data/processed`, `code`, `results/models`, `results/figures`, `tests`, `contracts`, `research`.
 2. Create `code/__init__.py`, `data/.gitkeep`.
 3. Create `code/requirements.txt` with specific dependencies: pandas, numpy, statsmodels, scikit-learn, pyyaml, requests, datasets, pytest.
 4. Create `.ruff.toml` (target-version="py311", line-length=88, select=["E", "F", "W"]).
 5. Create `.black.toml` (line-length=88, target-version="py311").
 - **Dependency**: None.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T010 [P] **Foundational Utilities & Logging**: Create core utility files and logging configuration.
 - **Actions**:
 1. Create `code/utils.py` with specific helpers: `log_setup()`, `checksum_file(path)`, `causal_language_scanner(text, forbidden_words)`.
 2. Create `code/__init__.py` with error handling classes and `__all__` exports.
 3. Create `code/config.py` with constants `RANDOM_SEED = 42`, `DATA_ROOT = "data"`, `RESULTS_ROOT = "results"`, `INTERACTION_SIG_THRESHOLD = 0.05`, and `DATA_URL` (pinned canonical URL).
 4. **Logging Artifact**: Create `code/logging_config.py` containing the logging configuration (format: `[%(asctime)s] %(levelname)s: %(message)s`, destination: stdout). This file MUST be imported by all subsequent scripts.
 5. **Verification**: Run `pytest tests/unit/test_logging.py` (if tests exist) or manually verify that importing `logging_config` sets up the logger correctly.
 - **Dependency**: T005.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Data Ingestion and Variable Extraction (Priority: P1) 🎯 MVP

**Goal**: Download, parse, and extract specific predictor and outcome variables from public survey datasets (AddHealth, HILDA, ESS) without manual intervention.

**Independent Test**: The pipeline runs against a subset of the target dataset and outputs a CSV containing `switching_index`, `cognitive_flexibility_score`, `age`, and `total_screen_time` without errors.

### Implementation for User Story 1

- [ ] T015 [US1] **Dataset Ingestion**: Implement `code/01_ingest.py`.
 - **Logic**:
 1. **Pre-flight Check**: Verify `results/feasibility_status.json` exists and indicates "PASS" for the specific dataset. **HALT** if feasibility check failed (do not skip).
 2. **Fetch**: Use **`wget` or `curl`** to download raw files from the URL pinned in `code/config.py` (`DATA_URL`). This ensures the exact same canonical source is used every run (Constitution Principle I).
 3. **Schema Validation**: Load `contracts/dataset.schema.yaml`. Load the first 1000 rows of the fetched data. Assert that all columns in the schema exist in the data. If mismatch, raise `ValueError` with "Data Gap: Downloaded data schema mismatch."
 4. **Fail Loudly**: If fetch fails, raise exception immediately; do NOT fall back to synthetic data.
 5. **Variable Check**: Verify presence of `self_reported_switching_frequency` and `cognitive_flexibility_score`. If missing, raise `ValueError` with "Data Gap: [Dataset] lacks required variables."
 6. **Output**: Save raw data to `data/raw/[dataset]_raw.csv` and cleaned CSV to `data/processed/[dataset]_cleaned.csv`.
 - **Dependency**: T001, T004, T017a.

- [ ] T017 [US1] **Variable Engineering & Output**: Implement `code/02_engineer.py`.
 - **Logic**:
 1. **Verify Variable Presence**: explicitly check for the presence of `self_reported_switching_frequency` before proceeding; if missing, halt with a `ValueError`.
 2. Compute `switching_index = num_platforms * switching_frequency`. Store as derived variable.
 3. Handle missing outcomes by excluding rows and logging exclusion count (e.g., "Excluded N rows due to missing WCST data").
 4. Output `data/processed/participants_cleaned.csv`.
 5. **Validation**: Verify the output file exists and contains all required columns: `participant_id`, `age`, `total_screen_time`, `num_platforms`, `switching_frequency`, `switching_index`, `cognitive_flexibility_score`.
 - **Output Schema**: `participant_id` (int), `age` (float), `total_screen_time` (float), `num_platforms` (int), `switching_frequency` (float), `switching_index` (float), `cognitive_flexibility_score` (float).
 - **Dependency**: T015, T017a.

- [X] T020 [US1] **Logging**: (DELETED - Merged into T010)

- [X] T024 [US1] **Correlation Calculation**: Calculate correlation for residualization.
 - **Logic**:
 1. Load `data/processed/participants_cleaned.csv`.
 2. Calculate Pearson correlation between `switching_index` and `total_screen_time`.
 3. Log the correlation coefficient to `results/correlation.txt`.
 - **Dependency**: T017

---

## Phase 4: User Story 2 - Associational Analysis and Model Fitting (Priority: P2)

**Goal**: Fit multiple linear regression models, compute diagnostics (VIF), and apply sensitivity analysis.

**Independent Test**: The analysis script runs on the cleaned CSV and produces a JSON report with coefficients, p-values, VIF scores, and corrected p-values.

### Implementation for User Story 2

- [ ] T025 [US2] **Core Model Fitting & Diagnostics**: Implement `code/03_model.py` (Part 1: Core OLS). <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
 - **Steps**:
 1. **Load Data**: Read `data/processed/participants_cleaned.csv`.
 2. **Mean-center** `switching_index` and `age` **THEN create interaction term** `switching_index * age` **IF** `config.py` `INCLUDE_INTERACTION` is set to True (default False).
 3. **Check Collinearity**: Calculate Pearson correlation between `switching_index` and `total_screen_time`. If > 0.7, generate a distinct warning log: `level=WARNING, message="Potential Mathematical Coupling: correlation > 0.7"` and log it to `logs/collinearity_check.log`.
 4. **Residual Model (OPTIONAL DIAGNOSTIC per FR-006)**:
 - **IF** correlation > 0.7:
 - Regress `switching_index` on `total_screen_time`.
 - Extract residuals and save to `results/models/residuals.csv`.
 - Fit `cognitive_flexibility_score` on residuals + `age` + interaction (if enabled).
 - Store secondary coefficients in `results/models/residualized_coefficients.json`.
 - **ELSE**:
 - Log "Skipping residual model (correlation <= 0.7). Primary model used."
 - Do NOT create `results/models/residuals.csv` or `results/models/residualized_coefficients.json`.
 - **Primary Output**: Write `results/models/core_model.json`.
 5. **Fit OLS (Baseline)**: Fit model with outcome `cognitive_flexibility_score` and predictors `switching_index` (or residuals), `total_screen_time`, `age`.
 6. **Fit OLS (Interaction)**: If `INCLUDE_INTERACTION` is True, fit model with interaction term.
 7. **VIF**: Compute Variance Inflation Factor (VIF) for all predictors. Construct a `diagnostics` dictionary containing `vif_scores`, the `correlation_matrix`, and the `correlation_flag`.
 8. **Verification**: Assert `results/models/residuals.csv` exists if correlation > 0.7, else assert it does not exist. Log the specific outcome.
 9. **Output**: Write intermediate model summary to `results/models/core_model.json`.
 - **Dependency**: T017, T024.

- [ ] T026 [US2] **Sensitivity Analysis & FDR**: Implement `code/03_model.py` (Part 2: Sensitivity). <!-- FAILED: unspecified -->
 - **Steps**:
 1. **Check Residuals**: Check if `results/models/residuals.csv` exists.
 2. **Sensitivity Runs**: Run regression with alternative definitions: `platform_count` only, `switching_frequency` only.
 3. **Calculate Variation**: Calculate `delta_beta` (the absolute difference between the main model beta and each sensitivity model beta).
 4. **FDR Correction**: Apply Benjamini-Hochberg (FDR) correction to p-values from all three runs (main + 2 sensitivity).
 5. **Write Results**: Write results to `results/sensitivity_comparison.csv` with columns: `definition`, `beta`, `p_value`, `delta_beta`, `sign`, `n`, `fdr_p_value`.
 6. **Verify Robustness (SC-003)**: Read `results/sensitivity_comparison.csv` and verify:
 - Beta sign does not flip across operationalizations.
 - **IF** signs flip: Log a CRITICAL warning "SC-003 Violation: Beta sign instability detected." and **set `status` to FAIL** in `results/robustness_evidence.json`.
 - If p > 0.10 for any variant but sign is stable, log "Warning: Variant p > 0.10 but sign stable; robustness maintained."
 7. **Generate Evidence**: Create `results/robustness_evidence.json` containing:
 - `sc003_status`: "PASS" (if p < 0.10 for all variants and signs stable) or "FAIL" (if any variant p >= 0.10 or signs flip).
 - `details`: List of p-values and signs.
 - `message`: "SC-003 Met: p < 0.10 across operationalizations" or "SC-003 FAIL: Sign instability or p > 0.10 detected".
 - **Dependency**: T025.

- [ ] T027 [US2] **Final Validation & Report**: Implement `code/03_model.py` (Part 3: Final Report). <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified -->
 - **Steps**:
 1. **Merge Results**: Combine core model and sensitivity results.
 2. **Validate Output Schema**: Validate `results/models/regression_summary.json` against `contracts/output.schema.yaml`. If missing, fail with "Schema file missing".
 3. **Causal Language Validation**: Programmatically scan the **entire** `results/models/regression_summary.json` file (all keys and values) for forbidden terms (causes, leads to, impacts). If found, **FAIL** the run.
 4. **Output**: Write `results/models/regression_summary.json` with standardized betas, p-values, VIF, and FDR-corrected p-values. Ensure `vif_scores` and `correlation_matrix` are nested inside a `diagnostics` object.
 - **Dependency**: T026.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] **Test Model Output Schema**: Implement `tests/contract/test_model_output.py::test_output_matches_schema`.
 - **Verification**: Assert that `results/models/regression_summary.json` matches `contracts/output.schema.yaml` structure.

- [X] T022 [P] [US2] **Test VIF Calculation**: Implement `tests/unit/test_vif.py::test_vif_calculation_correctness`.
 - **Verification**: Assert that VIF calculation for a known matrix (e.g., identity or simple correlation) returns expected values within tolerance.

- [X] T023 [P] [US2] **Test Causal Language Scanner**: Implement `tests/unit/test_causal_language.py::test_scanner_detects_forbidden_terms`.
 - **Verification**: Assert that the scanner returns True for strings containing "causes" and False for neutral strings.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently.

---

## Phase 5: User Story 3 - Sensitivity Analysis and Visualization (Priority: P3)

**Goal**: Perform sensitivity analysis on switching index definition and generate publication-ready visualizations.

**Independent Test**: The script generates PDF/PNG files containing the regression plot, stratified plots, and a sensitivity table.

### Implementation for User Story 3

- [ ] T036 [US3] **Scatter Plot**: Implement `code/04_visualize.py` (Part 1). <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
 - **Actions**:
 1. **Scatter Plot**: Generate scatter plot with `switching_index` (X) vs `cognitive_score` (Y) and save to `results/figures/regression_plot.png`.
 2. **Confidence Interval**: Overlay fitted regression line with 95% confidence intervals.
 - **Dependency**: T025.

- [ ] T037 [US3] **Stratified Plot**: Implement `code/04_visualize.py` (Part 2). <!-- ATOMIZE: requested --> <!-- FAILED: unspecified --> <!-- ATOMIZE: requested --> <!-- FAILED: unspecified -->
 - **Actions**:
 1. **Significance Check**: Extract the p-value for the interaction term from `results/models/core_model.json` using the key `diagnostics.interaction_p_value`.
 2. **Threshold**: Read the significance threshold from `code/config.py` (`INTERACTION_SIG_THRESHOLD`, default 0.05).
 3. **Stratified Plot**: Generate stratified plot showing regression lines for distinct age groups (<30 and >30) **ONLY IF** the interaction term is significant (p < `INTERACTION_SIG_THRESHOLD`).
 4. **Significance Label**: If the interaction term is significant, label the plot "Significant Interaction". If not, **do NOT generate the plot**.
 - **Dependency**: T025.

- [ ] T038 [US3] **Sensitivity Table**: Implement `code/04_visualize.py` (Part 3). <!-- ATOMIZE: requested -->
 - **Actions**:
 1. **Input**: Read `results/sensitivity_comparison.csv`.
 2. **Sensitivity Table**: Generate `results/figures/sensitivity_table.png` containing beta coefficients, p-values, n, and sign for all operationalizations.
 3. **Columns**: Ensure the visual table includes: `definition`, `beta`, `p_value`, `fdr_p_value`, `n`, `sign`.
 - **Dependency**: T026.

- [ ] T039 [US3] **Final Report**: Implement `code/04_visualize.py` (Part 4). <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
 - **Actions**:
 1. **Final Report**: Write final JSON report (`results/final_report.json`) merging model summary with the associational text summary.
 2. **Validation**: Run `causal_language_scanner` on the `interpretation` field and fail if matches found.
 3. **Structure**: Reference `contracts/output.schema.yaml`.
 4. **Dependencies**: Ensure `results/models/regression_summary.json` exists before merging.
 - **Dependency**: T036, T037, T038, T027.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T035a [P] [US3] **Test Visuals Generation - Regression**: Implement `tests/integration/test_visuals.py::test_regression_plot_exists`.
 - **Verification**: Assert that `results/figures/regression_plot.png` exists and is a valid image file.

- [X] T035b [P] [US3] **Test Visuals Generation - Sensitivity**: Implement `tests/integration/test_visuals.py::test_sensitivity_table_exists`.
 - **Verification**: Assert that `results/figures/sensitivity_table.png` exists and is a valid image file.

**Checkpoint**: All user stories should now be independently functional.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories.

- [X] T041 [P] **Create Documentation**: Implement `docs/README.md` and `docs/quickstart.md`.
 - **Verification**: Assert that `docs/README.md` exists and contains a "Getting Started" section with installation instructions.

- [X] T042 [P] **Add Docstrings**: Refactor code for clarity by adding docstrings.
 - **Verification**: Run `pydocstyle` or similar linter and ensure no missing docstring errors for public functions.

- [X] T043 [P] **Test Empty DataFrame**: Implement edge case tests for empty data.

- [X] T045 [P] **Verify Residual Model Validation**: Implement `tests/unit/test_residual_logic.py::test_residual_logic`.

- [X] T046 [P] **Validate Documentation Style**: Run `pydocstyle` and style checks.

- [X] T047 [P] **Performance Refactoring**: Refactor code for performance.

- [X] T048 [P] **Test Missing Value Exclusion**: Implement `tests/unit/test_edge_cases.py::test_missing_value_exclusion`.

- [X] T049 [P] **Verify Real Data Fetch Fails Loudly**: Implement `tests/unit/test_data_fetch.py::test_fetch_fails_loudly`.

- [X] T050 [P] **Verify No Synthetic Fallback in Engineering**: Implement `tests/unit/test_engineering.py::test_no_synthetic_fallback`.

## Dependencies & Execution Order

(Detailed dependency info omitted for brevity)

## Implementation Strategy

(Detailed implementation strategy omitted for brevity)

## Notes

(Notes omitted for brevity)
