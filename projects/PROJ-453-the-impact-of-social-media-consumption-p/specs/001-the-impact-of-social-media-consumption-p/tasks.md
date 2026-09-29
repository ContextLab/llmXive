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

- [ ] T000 [P0] **Schema Definition**: Create `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml`.
 - **Actions**:
 1. Create `contracts/dataset.schema.yaml` defining expected columns: `switching_index`, `cognitive_flexibility_score`, `age`, `total_screen_time`, `num_platforms`, `switching_frequency`.
 2. Create `contracts/output.schema.yaml` defining model output structure: `coefficients`, `p_values`, `r_squared`, `vif_scores`, `diagnostics`.
 - **Dependency**: None. Must run first to enable T001.

- [ ] T001 [P0] **Feasibility & Variable Check**: Implement `code/00_feasibility_check.py` to perform a lightweight check (using `datasets.load_dataset(..., streaming=True)` with a 1-row peek) to verify the URL is accessible and the dataset contains tabular data.
 - **Logic**:
 1. **Define Candidates**: Loop through candidate datasets with specific HuggingFace IDs: `nrc/addhealth_wave4` (or `addhealth` if available), `hilda/hilda_2023`, `ess/ess_round10`.
 2. **Check Primary Variables**: Use `streaming=True` to peek at the first row. Verify `self_reported_switching_frequency` and `cognitive_flexibility_score` (or validated proxy) in the dataset schema/headers.
 3. **Validate Schema**: Load `contracts/dataset.schema.yaml`. Load a representative subset of rows from the dataset. Compare the column names against the keys in `contracts/dataset.schema.yaml`.
 4. **Strict Halt (NO Proxy)**: If a dataset lacks required variables, **HALT** with error: "Data Gap: Required variable [NAME] not found in verified dataset [URL]. Project cannot proceed per US-1 Scenario 2." **DO NOT attempt to find a proxy or merge.**
 5. **Output**: If ALL datasets fail (including proxy/merge attempts), halt with `sys.exit("Data Gap: No viable dataset found. Project cannot proceed per US-1 Scenario 2.")`.
 6. **Structured Output**: Write `results/feasibility_status.json` with fields: `status` (PASS/FAIL), `dataset_id` (selected dataset or null), `message` (details). If PASS, include `proxy_used` (boolean, always false) and `merged_datasets` (list, always empty).
 - **Dependency**: T000.

- [ ] T016a [P0] **Document Instrument Sources**: Implement `code/01_ingest.py` (or a dedicated helper) to create `data/instrument_sources.yaml` **immediately after feasibility check** but **before** any ingestion or variable engineering.
 - **Schema**: Must include `survey_name`, `validation_citation`, and `variable_mapping` (list of dicts: `[{original_var: "name", derived_var: "name", source_doc: "url"}]`).
 - **Logic**:
 1. **Verify Dataset Match**: Read `results/feasibility_status.json`. Ensure the dataset being processed matches the one marked "PASS" in the report. If not, halt with `sys.exit("Data Gap: Dataset does not match verified source for instrument citations.")`.
 2. **Fetch Citations**: Look up the actual validation URLs for the specific dataset (HILDA/ESS/AddHealth) from the **official HuggingFace dataset card documentation**.
 3. **Extraction Rule**: Parse the "Citation" field in the YAML frontmatter of the dataset card. If the field is missing, raise `ValueError` with "Data Gap: Validation URL missing in dataset card frontmatter."
 4. **URL Verification**: Attempt to fetch the URL (HEAD request). If the URL returns 404 or is unreachable, raise a `ValueError` with "Data Gap: Validation URL [URL] is unreachable. Citation verification failed."
 5. **Write File**: Generate `data/instrument_sources.yaml` with the correct mapping, valid citations, and a `verified_status: true` field.
 - **Note**: This task assumes T001 has already validated the presence of required variables. If T001 failed, T016a will not run.
 - **Dependency**: T001, T000.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, basic structure, contract definitions, and schema validation.

- [ ] T005 [P] **Project Setup**: Create project directories and configuration files.
 - **Actions**:
 1. Create directories: `data/raw`, `data/processed`, `code`, `results/models`, `results/figures`, `tests`, `contracts`, `research`.
 2. Create `code/__init__.py`, `data/.gitkeep`, `data/raw/.gitkeep`.
 3. Create `code/requirements.txt` with specific dependencies: pandas, numpy, statsmodels, scikit-learn, pyyaml, requests, datasets, pytest.
 4. Create `.ruff.toml` (target-version="py311", line-length=88, select=["E", "F", "W"]).
 5. Create `.black.toml` (line-length=88, target-version="py311").
 - **Dependency**: None.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T010 [P] **Foundational Utilities & Logging**: Create core utility files and logging configuration.
 - **Actions**:
 1. Create `code/utils.py` with specific helpers: `log_setup()`, `checksum_file(path)`, `causal_language_scanner(text, forbidden_words)`.
 2. Create `code/__init__.py` with error handling classes and `__all__` exports.
 3. Create `code/config.py` with constants `RANDOM_SEED = 42`, `DATA_ROOT = "data"`, `RESULTS_ROOT = "results"`.
 4. **Logging Artifact**: Create `code/logging_config.py` containing the logging configuration (format: `[%(asctime)s] %(levelname)s: %(message)s`, destination: stdout). This file MUST be imported by all subsequent scripts.
 5. **Verification**: Run `pytest tests/unit/test_logging.py` (if tests exist) or manually verify that importing `logging_config` sets up the logger correctly.
 - **Dependency**: None.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 - Data Ingestion and Variable Extraction (Priority: P1) 🎯 MVP

**Goal**: Download, parse, and extract specific predictor and outcome variables from public survey datasets (AddHealth, HILDA, ESS) without manual intervention.

**Independent Test**: The pipeline runs against a subset of the target dataset and outputs a CSV containing `switching_index`, `cognitive_flexibility_score`, `age`, and `total_screen_time` without errors.

**⚠️ Dependency Note**: T015 and T017 require T001 (Feasibility Check) and T016a (Instrument Docs) to be completed first.

### Implementation for User Story 1

- [ ] T015 [US1] **Dataset Ingestion**: Implement `code/01_ingest.py` functions `load_hilda()`, `load_ess()`, `load_addhealth()`.
 - **Logic**:
 1. **Pre-flight Check**: Verify `results/feasibility_status.json` exists and indicates "PASS" for the specific dataset. **HALT** if feasibility check failed (do not skip).
 2. **Fetch**: Use **`wget` or `curl`** (standard HTTP tools) to download raw files.
 3. **Schema Validation**: Load `contracts/dataset.schema.yaml`. Load the first 1000 rows of the fetched data. Assert that all columns in the schema exist in the data. If mismatch, raise `ValueError` with "Data Gap: Downloaded data schema mismatch."
 4. **Fail Loudly**: If fetch fails, raise exception immediately; do NOT fall back to synthetic data.
 5. **Variable Check**: Verify presence of `self_reported_switching_frequency` and `cognitive_flexibility_score`. If missing, raise `ValueError` with "Data Gap: [Dataset] lacks required variables."
 6. **Output**: Save raw data to `data/raw/[dataset]_raw.csv` and cleaned CSV to `data/processed/[dataset]_cleaned.csv`.
 - **Dependency**: T001, T016a, T000, T005.

- [ ] T017 [US1] **Variable Engineering & Output**: Implement `code/02_engineer.py`:
 1. **Verify Variable Presence**: explicitly check for the presence of `self_reported_switching_frequency` before proceeding; if missing, halt with a `ValueError`.
 2. Compute `switching_index = num_platforms * self_reported_switching_frequency`. Store as derived variable.
 3. Handle missing outcomes by excluding rows and logging exclusion count (e.g., "Excluded N rows due to missing WCST data").
 4. Output `data/processed/participants_cleaned.csv`.
 5. **Validation**: Verify the output file exists and contains all required columns: `participant_id`, `age`, `total_screen_time`, `num_platforms`, `switching_frequency`, `switching_index`, `cognitive_flexibility_score`.
 - **Output Schema**: `participant_id` (int), `age` (float), `total_screen_time` (float), `num_platforms` (int), `switching_frequency` (float), `switching_index` (float), `cognitive_flexibility_score` (float).
 - **Dependency**: T015, T016a.

- [ ] T020 [US1] **Logging**: (DELETED - Merged into T010)
 - **Dependency**: None.

---

## Phase 4: User Story 2 - Associational Analysis and Model Fitting (Priority: P2)

**Goal**: Fit multiple linear regression models, compute diagnostics (VIF), and apply sensitivity analysis.

**Independent Test**: The analysis script runs on the cleaned CSV and produces a JSON report with coefficients, p-values, VIF scores, and corrected p-values.

### Implementation for User Story 2

- [ ] T025 [US2] **Core Model Fitting & Diagnostics**: Implement `code/03_model.py` (Part 1: Core OLS).
 - **Steps**:
 1. **Load Data**: Read `data/processed/participants_cleaned.csv`.
 2. **Mean-center** `switching_index` and `age` **THEN create interaction term** `switching_index * age`.
 3. **Check Collinearity**: Calculate correlation between `switching_index` and `total_screen_time`. If > 0.7, generate a distinct warning flag "Potential Mathematical Coupling" and log it to `logs/collinearity_check.log`.
 4. **Residual Model (OPTIONAL DIAGNOSTIC per FR-006)**:
 - **IF** correlation > 0.7:
 - Regress `switching_index` on `total_screen_time`.
 - Extract residuals and save to `results/models/residuals.csv`.
 - Fit `cognitive_flexibility_score` on residuals + `age` + interaction.
 - Store secondary coefficients in `results/models/residualized_coefficients.json`.
 - **ELSE**:
 - Log "Skipping residual model (correlation <= 0.7). Primary model used."
 - Do NOT create `results/models/residuals.csv` or `results/models/residualized_coefficients.json`.
 - **Primary Output**: Write `results/models/core_model.json` with standard coefficients in this case.
 5. **Fit OLS (Baseline)**: Fit model with outcome `cognitive_flexibility_score` and predictors `switching_index` (or residuals), `total_screen_time`, `age`.
 6. **Fit OLS (Interaction)**: If US-2 acceptance criteria require, fit model with interaction term.
 7. **VIF**: Compute Variance Inflation Factor (VIF) for all predictors. Construct a `diagnostics` dictionary containing `vif_scores`, the `correlation_matrix`, and the `correlation_flag` (boolean).
 8. **Verification**: Assert `results/models/residuals.csv` exists if correlation > 0.7, else assert it does not exist. Log the specific outcome.
 9. **Output**: Write intermediate model summary to `results/models/core_model.json`.
 - **Dependency**: T017 (Data), T001 (Schema).

- [ ] T026 [US2] **Sensitivity Analysis & FDR**: Implement `code/03_model.py` (Part 2: Sensitivity).
 - **Steps**:
 1. **Check Residuals**: Check if `results/models/residuals.csv` exists.
 - **IF exists**: Use the residualized switching index as the predictor.
 - **IF missing**: Use the original `switching_index` as the predictor (this is the primary execution path when correlation is low).
 2. **Sensitivity Runs**: Run regression with alternative definitions: `platform_count` only, `switching_frequency` only.
 3. **FDR Correction**: Apply Benjamini-Hochberg (FDR) correction to p-values from all three runs (main + 2 sensitivity).
 4. **Write Results**: Write results to `results/sensitivity_comparison.csv` with columns: `definition`, `beta`, `p_value`, `sign`, `n`, `fdr_p_value`.
 5. **Verify Robustness (SC-003)**: Read `results/sensitivity_comparison.csv` and verify:
 - Beta sign does not flip across operationalizations.
 - **IF** signs flip: Log a CRITICAL warning "SC-003 Violation: Beta sign instability detected." and **set `status` to FAIL** in `results/robustness_evidence.json`.
 - If p > 0.10 for any variant but sign is stable, log "Warning: Variant p > 0.10 but sign stable; robustness maintained."
 6. **Generate Evidence**: Create `results/robustness_evidence.json` containing:
 - `sc003_status`: "PASS" (if p < 0.10 for all variants and signs stable) or "FAIL" (if any variant p >= 0.10 or signs flip).
 - `details`: List of p-values and signs.
 - `message`: "SC-003 Met: p < 0.10 across operationalizations" or "SC-003 FAIL: Sign instability or p > 0.10 detected".
 - **Dependency**: T025.

- [ ] T027 [US2] **Final Validation & Report**: Implement `code/03_model.py` (Part 3: Final Report).
 - **Steps**:
 1. **Merge Results**: Combine core model and sensitivity results.
 2. **Validate Output Schema**: Validate `results/models/regression_summary.json` against `contracts/output.schema.yaml`. If missing, fail with "Schema file missing".
 3. **Causal Language Validation**: Programmatically scan the entire `interpretation` string AND the generated textual summary for forbidden terms (causes, leads to, impacts). If found, **FAIL** the run.
 4. **Output**: Write `results/models/regression_summary.json` with standardized betas, p-values, VIF, and FDR-corrected p-values. Ensure `vif_scores` and **raw correlation matrix** are nested inside a `diagnostics` object.
 - **Dependency**: T026.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] **Test Model Output Schema**: Implement `tests/contract/test_model_output.py::test_output_matches_schema`.
 - **Logic**:
 1. Load `contracts/output.schema.yaml`.
 2. Load `results/models/regression_summary.json`.
 3. Assert that all keys in the schema exist in the JSON.
 4. Assert that `vif_scores` is a list/dict and `interpretation` is a string.
 5. **Expected Failure**: Initially, the JSON file is missing or keys are wrong.
 - **Dependency**: T025, T026, T027.

- [ ] T022 [P] [US2] **Test VIF Calculation**: Implement `tests/unit/test_vif.py::test_vif_calculation_correctness`.
 - **Logic**:
 1. Create a synthetic DataFrame with known collinearity (e.g., `x2 = x1 * 2 + noise`).
 2. Call the VIF function.
 3. Assert that the VIF for `x2` is > 5 (or expected high value).
 4. **Expected Failure**: Initially, the function might not be implemented or calculation is wrong.
 - **Dependency**: T010, T025.

- [ ] T023 [P] [US2] **Test Causal Language Scanner**: Implement `tests/unit/test_causal_language.py::test_scanner_detects_forbidden_terms`.
 - **Logic**:
 1. Call `causal_language_scanner("This variable causes the outcome", ["causes"])`.
 2. Assert that the function returns `True` (or raises an error).
 3. **Expected Failure**: Initially, the scanner might not detect the term.
 - **Dependency**: T010.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently.

---

## Phase 5: User Story 3 - Sensitivity Analysis and Visualization (Priority: P3)

**Goal**: Perform sensitivity analysis on switching index definition and generate publication-ready visualizations.

**Independent Test**: The script generates PDF/PNG files containing the regression plot, stratified plots, and a sensitivity table.

### Implementation for User Story 3

- [ ] T036 [US3] **Scatter Plot**: Implement `code/04_visualize.py` (Part 1).
 - **Actions**:
 1. **Scatter Plot**: Generate scatter plot with `switching_index` (X) vs `cognitive_score` (Y) and save to `results/figures/regression_plot.png`.
 2. **Confidence Interval**: Overlay fitted regression line with 95% confidence intervals.
 - **Dependency**: T025.

- [ ] T037 [US3] **Stratified Plot**: Implement `code/04_visualize.py` (Part 2).
 - **Actions**:
 1. **Significance Check**: Extract the p-value for the interaction term from `results/models/core_model.json`.
 2. **Threshold**: Use **p < 0.05** as the threshold for significance.
 3. **Stratified Plot**: Generate stratified plot showing regression lines for distinct age groups (<30 and >30) **only if the interaction term is significant** (p < 0.05).
 4. **Significance Label**: If the interaction term is significant (p < 0.05), label the plot "Significant Interaction". If not, label it "Non-Significant Interaction."
 - **Dependency**: T025.

- [ ] T038 [US3] **Sensitivity Table**: Implement `code/04_visualize.py` (Part 3).
 - **Actions**:
 1. **Input**: Read `results/sensitivity_comparison.csv` (generated by T026).
 2. **Sensitivity Table**: Generate `results/figures/sensitivity_table.png` containing beta coefficients, p-values, n, and sign for all operationalizations.
 3. **Columns**: Ensure the visual table includes: `definition`, `beta`, `p_value`, `fdr_p_value`, `n`, `sign`.
 - **Dependency**: T026.

- [ ] T039 [US3] **Final Report**: Implement `code/04_visualize.py` (Part 4).
 - **Actions**:
 1. **Final Report**: Write final JSON report (`results/final_report.json`) merging model summary with the associational text summary.
 2. **Validation**: Run `causal_language_scanner` on the `interpretation` field and fail if matches found.
 3. **Structure**: Reference `contracts/output.schema.yaml`.
 4. **Dependencies**: Ensure `results/models/regression_summary.json` (from T027) exists before merging.
 - **Dependency**: T036, T037, T038, T027.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T035a [P] [US3] **Test Visuals Generation - Regression**: Implement `tests/integration/test_visuals.py::test_regression_plot_exists`.
 - **Logic**:
 1. Run the visualization script.
 2. Assert that `results/figures/regression_plot.png` exists and is not empty.
 3. **Expected Failure**: Initially, file is missing.
 - **Dependency**: T036, T037, T038, T039.

- [ ] T035b [P] [US3] **Test Visuals Generation - Sensitivity**: Implement `tests/integration/test_visuals.py::test_sensitivity_table_exists`.
 - **Logic**:
 1. Run the visualization script.
 2. Assert that `results/figures/sensitivity_table.png` exists and is not empty.
 3. **Expected Failure**: Initially, file is missing.
 - **Dependency**: T036, T037, T038, T039.

**Checkpoint**: All user stories should now be independently functional.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories.

- [ ] T041 [P] **Create Documentation**: Implement `docs/README.md` and `docs/quickstart.md`.
 - **Actions**:
 1. Create `docs/README.md` with project overview.
 2. Create `docs/quickstart.md` with pipeline instructions.
 3. **Associational Disclaimer**: **MUST** include the mandatory "associational" framing disclaimer required by FR-004 in both documents (e.g., "This study reports associational estimates only; no causal claims are made.").
 4. **Gate**: This task can only start after T017 and T025 are marked "Complete" and their schema tests (T013, T021b) **PASS**.
 - **Dependency**: T017, T025, T013 (must pass), T021b (must pass).

- [ ] T046 [P] **Validate Documentation Style**: Run `pydocstyle` and style checks.
 - **Actions**:
 1. Run `pydocstyle code/` and ensure 0 errors. If errors exist, fix them.
 2. Run `ruff check docs/` to ensure consistent formatting.
 - **Gate**: This task can only start after T041 is complete.
 - **Dependency**: T041.

- [ ] T042 [P] **Add Docstrings**: Refactor code for clarity by adding docstrings.
 - **Actions**:
 1. Refactor `code/*.py` to add Google-style docstrings to **all public functions and classes**.
 2. Refactor `code/02_engineer.py` for clarity and performance.
 3. **Verification**:
 - Run `pydocstyle code/` to ensure all public functions have docstrings.
 - Run `pytest --cov=code --cov-fail-under=80`. If coverage < 80%, refactor until met.
 4. **Gate**: This task can only start after T017 and T025 are marked "Complete" and their schema tests (T013, T021b) **PASS**.
 - **Dependency**: T017, T025.

- [ ] T047 [P] **Performance Refactoring**: Refactor code for performance.
 - **Actions**:
 1. Optimize loops and data processing in `code/02_engineer.py` and `code/03_model.py`.
 2. Verify memory usage stays within limits.
 - **Gate**: This task can only start after T042 is complete.
 - **Dependency**: T042.

- [ ] T043 [P] **Test Empty DataFrame**: Implement edge case tests for empty data.
 - **Actions**:
 1. Implement `tests/unit/test_edge_cases.py::test_empty_dataframe_handling`:
 - Pass an empty DataFrame to `code/02_engineer.py`.
 - Assert that a `ValueError` is raised with "No data to process".
 2. **Verification**: Run `pytest tests/unit/test_edge_cases.py::test_empty_dataframe_handling` and ensure the test passes.
 - **Gate**: This task can only start after T017 and T025 are marked "Complete" and their schema tests (T013, T021b) **PASS**.
 - **Dependency**: T017, T025.

- [ ] T048 [P] **Test Missing Value Exclusion**: Implement edge case tests for missing values.
 - **Actions**:
 1. Implement `tests/unit/test_edge_cases.py::test_missing_value_exclusion`:
 - Pass a DataFrame with missing `cognitive_flexibility_score`.
 - Assert that the output file is empty and a log entry "Excluded [count] rows" exists.
 2. **Verification**: Run `pytest tests/unit/test_edge_cases.py::test_missing_value_exclusion` and ensure the test passes.
 - **Gate**: This task can only start after T017 and T025 are marked "Complete" and their schema tests (T013, T021b) **PASS**.
 - **Dependency**: T017, T025.

- [ ] T044 [P] **Data Streaming Verification**: Verify that `code/01_ingest.py` correctly handles datasets exceeding 7GB RAM using `streaming=True` and chunked processing.
 - **Actions**:
 1. **Test Logic**: Implement `tests/unit/test_streaming.py::test_streaming_chunking` to mock a large dataset iterator and verify that `load_hilda()` (or equivalent) processes data in chunks without loading the entire set into memory.
 2. **Memory Check**: Use `tracemalloc` to verify peak memory usage stays below 6GB during processing of the mocked large dataset (simulate 10GB of data via an iterator yielding 1M rows).
 3. **Gate**: This task ensures compliance with the "Large real datasets: STREAM the real data" rule and prevents memory overflow in CI. Note: While the spec assumes datasets fit in RAM, this test provides a robustness check for edge cases.
 - **Dependency**: T015, T017.

- [ ] T045 [P] **Residual Model Validation**: Verify that the residualized model logic in `code/03_model.py` (T025) is correctly triggered only when correlation > 0.7.
 - **Actions**:
 1. **Unit Test**: Implement `tests/unit/test_residual_logic.py::test_residual_trigger_condition`.
 2. **Scenario A**: Create a synthetic dataset with correlation 0.6. Assert that `results/models/residuals.csv` is NOT created.
 3. **Scenario B**: Create a synthetic dataset with correlation 0.8. Assert that `results/models/residuals.csv` IS created and used in the final model.
 4. **Verification**: Ensure the "Potential Mathematical Coupling" warning is logged only in Scenario B.
 - **Dependency**: T025, T026.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Data Research & Feasibility)**: No dependencies - MUST run first. Blocks all other phases.
- **Setup (Phase 1)**: No dependencies - can start immediately (in parallel with Phase 0 if resources allow, but logically independent).
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion.
 - User stories can then proceed in parallel (if staffed).
 - Or sequentially in priority order (P1 → P2 → P3).
- **Polish (Final Phase)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other user stories.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation.
- Models before services.
- Services before endpoints.
- Core implementation before integration.
- Story complete before moving to next priority.

### Specific Execution Chains

- **Phase 0 Chain**: T000 (Schema) -> T001 (Feasibility) -> T016a (Instrument Docs) -> T005 (Setup) -> T010 (Foundational).
- **User Story 1 Chain**: T015 (Ingestion) -> T017 (Engineering) -> T020 (Logging).
- **User Story 2 Chain**: T025 (Core Model) -> T026 (Sensitivity) -> T027 (Final Report).
- **User Story 3 Chain**: T036 (Scatter) -> T037 (Stratified) -> T038 (Sensitivity Table) -> T039 (Final Report).

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel.
- All Foundational tasks marked [P] can run in parallel (within Phase 2).
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows).
- All tests for a user story marked [P] can run in parallel.
- Different user stories can be worked on in parallel by different team members.
- **Phase 0 tasks** can be executed in parallel as they involve independent research on different datasets (now merged into T001 and T016a).

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
 - Developer D: Phase 0 (Research & Data Validation)
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
- **Data Integrity**: Never use synthetic data as a fallback. If real data fetch fails, the pipeline must fail loudly.
- **Streaming**: If datasets exceed available RAM, use `streaming=True` and process in chunks (implemented in T015, verified in T044).
- **Causal Language**: Strictly enforce associational framing; any causal terms trigger a failure.
- **Phase 0 is Mandatory**: The pipeline MUST check for variables before downloading data.
- **Schema Validation**: Moved to Phase 0 (T000) to avoid circular dependency with Phase 1.
- **Phase 0 Added**: Explicit research tasks (T046-T050) added to prevent "Data Gap" failures by validating variable existence in public datasets before implementation. (Now merged into T001 and T016a).
- **T044 Added**: Explicit streaming robustness verification to ensure memory constraints are respected for large datasets.
- **T045 Added**: Explicit validation of the conditional residual model logic to ensure it only triggers when mathematically necessary.
- **T042/T043 Gates**: T042 and T043 are now gated behind T017/T025 completion and schema test validation.
- **Documentation Disclaimer**: T041 explicitly requires the FR-004 associational disclaimer.
- **Stratified Plot**: T037 always generates the plot, regardless of significance, but labels it based on p < 0.05 threshold.
- **Task Splitting**: T041, T042, T043 split into atomic tasks (T041/T046, T042/T047, T043/T048).