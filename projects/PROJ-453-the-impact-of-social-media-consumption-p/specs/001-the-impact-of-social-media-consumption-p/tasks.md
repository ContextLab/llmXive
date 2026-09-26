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

## Phase 0: Data Research & Feasibility (CRITICAL GATE)

**Purpose**: Verify the presence of required variables in the dataset source BEFORE any full download or processing. This phase MUST pass before Phase 1 begins.
**⚠️ CRITICAL**: If this phase fails for ALL candidate datasets, the project halts immediately with a "Data Gap" error. No data is downloaded.
**⚠️ NOTE**: This phase includes schema validation only. Schema definition is handled in Phase 1 (Setup).

- [X] T001 [P0] **Feasibility & Schema Validation**: Implement `code/00_feasibility_check.py` to perform a lightweight check (using `datasets.load_dataset(..., streaming=True)` with a 1-row peek) to verify the URL is accessible and the dataset contains tabular data.
 - **Logic**:
 1. **Define Candidates**: Loop through candidate datasets with specific HuggingFace IDs: `nrc/addhealth_wave4` (or `addhealth` if available), `hilda/hilda_2023`, `ess/ess_round10`.
 2. **Check**: Use `streaming=True` to peek at the first row. Verify `self_reported_switching_frequency` and `cognitive_flexibility_score` (or validated proxy) in the dataset schema/headers.
 3. **Validate Schema**: Load `contracts/dataset.schema.yaml` (created in T005). Load the first 1000 rows of the dataset. Compare the column names against the keys in `contracts/dataset.schema.yaml`.
 4. **Fail Fast**: If a dataset lacks required variables OR fails schema validation, log "Data Gap: [Dataset] lacks [Variable] or schema mismatch". If ALL datasets fail, halt with `sys.exit("Data Gap: No viable dataset found. Project cannot proceed per US-1 Scenario 2.")`.
 5. **Output**: Write `logs/feasibility_report.txt` (including the validated dataset ID) and `logs/schema_validation.log`.
 - **Dependency**: T005 (Setup). Must run before T015 (Ingestion).

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
 6. **Create Schema**: Create `contracts/dataset.schema.yaml` defining expected columns: switching_index, cognitive_flexibility_score, age, total_screen_time, num_platforms, switching_frequency.
 7. Create `contracts/output.schema.yaml` defining model output structure: coefficients, p_values, vif_scores, diagnostics, interpretation.

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

**⚠️ Dependency Note**: T015 and T016a require T001 (Feasibility Check) and T005 (Setup) to be completed first.

### Implementation for User Story 1

- [X] T015 [US1] **Dataset Ingestion**: Implement `code/01_ingest.py` functions `load_hilda()`, `load_ess()`, `load_addhealth()`.
 - **Logic**:
 1. **Pre-flight Check**: Verify `logs/feasibility_report.txt` exists and indicates "PASS" for the specific dataset. If not, skip with "Data Gap: [Dataset] feasibility check failed."
 2. **Fetch**: Use specific HuggingFace IDs (e.g., `nrc/addhealth_wave4`, `hilda/hilda_2023`, `ess/ess_round10`). Use `streaming=True` if dataset > 100MB to handle memory constraints robustly (datasets > 7GB are processed in chunks).
 3. **Schema Validation**: Load `contracts/dataset.schema.yaml`. Load the first 1000 rows of the fetched data. Assert that all columns in the schema exist in the data. If mismatch, raise `ValueError` with "Data Gap: Downloaded data schema mismatch."
 4. **Fail Loudly**: If fetch fails, raise exception immediately; do NOT fall back to synthetic data.
 5. **Variable Check**: Verify presence of `self_reported_switching_frequency` and `cognitive_flexibility_score`. If missing, raise `ValueError` with "Data Gap: [Dataset] lacks required variables."
 6. **Output**: Save raw data to `data/raw/[dataset]_raw.csv` and cleaned CSV to `data/processed/[dataset]_cleaned.csv`.
 - **Dependency**: T001, T005.

- [X] T016a [US1] **Document Instrument Sources**: Implement `code/01_ingest.py` (or a dedicated helper) to create `data/instrument_sources.yaml` **immediately after ingestion** but **before** variable engineering (T017).
 - **Schema**: Must include `survey_name`, `validation_citation`, and `variable_mapping` (list of dicts: `[{original_var: "name", derived_var: "name", source_doc: "url"}]`).
 - **Logic**:
 1. **Verify Dataset Match**: Read `logs/feasibility_report.txt`. Ensure the dataset being processed matches the one marked "PASS" in the report. If not, halt with `sys.exit("Data Gap: Dataset does not match verified source for instrument citations.")`.
 2. **Fetch Citations**: Look up the actual validation URLs for the specific dataset (HILDA/ESS/AddHealth) from the official documentation. **Do NOT use placeholder URLs.**
 3. **Write File**: Generate `data/instrument_sources.yaml` with the correct mapping and valid citations.
 - **Note**: This task assumes T015 has already validated the presence of required variables. If T015 failed, T016a will not run.
 - **Dependency**: T015, T005.

- [X] T017 [US1] **Variable Engineering & Output**: Implement `code/02_engineer.py`:
 1. Compute `switching_index = num_platforms * self_reported_switching_frequency`. Store as derived variable.
 2. Handle missing outcomes by excluding rows and logging exclusion count (e.g., "Excluded N rows due to missing WCST data").
 3. Output `data/processed/participants_cleaned.csv`.
 4. **Validation**: Verify the output file exists and contains all required columns: `participant_id`, `age`, `total_screen_time`, `num_platforms`, `switching_frequency`, `switching_index`, `cognitive_flexibility_score`.
 - **Output Schema**: `participant_id` (int), `age` (float), `total_screen_time` (float), `num_platforms` (int), `switching_frequency` (float), `switching_index` (float), `cognitive_flexibility_score` (float).
 - **Dependency**: T015, T016a.

- [ ] T020 [US1] **Logging**: (DELETED - Merged into T010) <!-- FAILED: unspecified -->
 - **Dependency**: T010.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T013 [P] [US1] **Test Data Schema**: Implement `tests/contract/test_dataset_schema.py::test_schema_matches_yaml`. <!-- FAILED: unspecified -->
 - **Logic**:
 1. Load `contracts/dataset.schema.yaml`.
 2. Load a sample CSV from `data/processed/`.
 3. Assert that all columns in the schema exist in the CSV.
 4. Assert that data types match (e.g., `age` is float/int).
 5. **Expected Failure**: Initially, the CSV does not exist or columns are missing.
 - **Dependency**: T001, T015.

- [X] T014 [P] [US1] **Test Missing Variable Error**: Implement `tests/unit/test_ingest_errors.py::test_missing_variable_raises_error`.
 - **Logic**:
 1. Create a mock DataFrame missing `cognitive_flexibility_score`.
 2. Call the ingestion/engineering function.
 3. Assert that a `ValueError` is raised with the message "Data Gap: [Dataset] lacks required variables."
 4. **Expected Failure**: Initially, the function might not raise or the message is wrong.
 - **Dependency**: T015.

- [X] T021a [P] [US2] **Test Load Schema**: Implement `tests/contract/test_model_output.py::test_load_schema`. <!-- ATOMIZED -->
 - **Logic**:
 1. Load `contracts/output.schema.yaml`.
 2. Assert that the schema file is valid YAML and contains expected keys.
 3. **Expected Failure**: Initially, the schema file is missing.
 - **Dependency**: T005.

- [X] T021b [P] [US2] **Test Validate JSON Keys**: Implement `tests/contract/test_model_output.py::test_validate_json_keys`. <!-- ATOMIZED -->
 - **Logic**:
 1. Load `contracts/output.schema.yaml`.
 2. Load `results/models/regression_summary.json`.
 3. Assert that all keys in the schema exist in the JSON.
 4. Assert that `vif_scores` is a list/dict and `interpretation` is a string.
 5. **Expected Failure**: Initially, the JSON file is missing or keys are wrong.
 - **Dependency**: T025, T026, T027.

- [X] T022 [P] [US2] **Test VIF Calculation**: Implement `tests/unit/test_vif.py::test_vif_calculation_correctness`.
 - **Logic**:
 1. Create a synthetic DataFrame with known collinearity (e.g., `x2 = x1 * 2 + noise`).
 2. Call the VIF function.
 3. Assert that the VIF for `x2` is > 5 (or expected high value).
 4. **Expected Failure**: Initially, the function might not be implemented or calculation is wrong.
 - **Dependency**: T010, T025.

- [X] T023 [P] [US2] **Test Causal Language Scanner**: Implement `tests/unit/test_causal_language.py::test_scanner_detects_forbidden_terms`.
 - **Logic**:
 1. Call `causal_language_scanner("This variable causes the outcome", ["causes"])`.
 2. Assert that the function returns `True` (or raises an error).
 3. **Expected Failure**: Initially, the scanner might not detect the term.
 - **Dependency**: T010.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently.

---

## Phase 4: User Story 2 - Associational Analysis and Model Fitting (Priority: P2)

**Goal**: Fit multiple linear regression models, compute diagnostics (VIF), and apply sensitivity analysis.

**Independent Test**: The analysis script runs on the cleaned CSV and produces a JSON report with coefficients, p-values, VIF scores, and corrected p-values.

### Implementation for User Story 2

- [X] T025 [US2] **Core Model Fitting & Diagnostics**: Implement `code/03_model.py` (Part 1: Core OLS). <!-- FAILED: unspecified -->
 - **Steps**:
 1. **Load Data**: Read `data/processed/participants_cleaned.csv`.
 2. **Mean-center** `switching_index` and `age` **THEN create interaction term** `switching_index * age`.
 3. **Check Collinearity**: Calculate correlation between `switching_index` and `total_screen_time`. If > 0.7, generate a distinct warning flag "Potential Mathematical Coupling" and log it to `logs/collinearity_check.log` with `flag=true`.
 4. **Residual Model (MANDATORY per FR-006)**:
 - **IF** correlation > 0.7:
 - Regress `switching_index` on `total_screen_time`.
 - Extract residuals and save to `results/models/residuals.csv`.
 - Fit `cognitive_flexibility_score` on residuals + `age` + interaction.
 - Store secondary coefficients in `results/models/residualized_coefficients.json`.
 - **ELSE**:
 - Log "Skipping residual model (correlation <= 0.7)".
 - Do NOT create `results/models/residuals.csv` or `results/models/residualized_coefficients.json`.
 5. **Fit OLS (Baseline)**: Fit model with outcome `cognitive_flexibility_score` and predictors `switching_index` (or residuals), `total_screen_time`, `age`.
 6. **Fit OLS (Interaction)**: If US-2 acceptance criteria require, fit model with interaction term.
 7. **VIF**: Compute Variance Inflation Factor (VIF) for all predictors. Construct a `diagnostics` dictionary containing `vif_scores` and the `correlation_matrix`.
 8. **Output**: Write intermediate model summary to `results/models/core_model.json`.
 - **Dependency**: T017 (Data), T001 (Schema).

- [X] T026 [US2] **Sensitivity Analysis & FDR**: Implement `code/03_model.py` (Part 2: Sensitivity).
 - **Steps**:
 1. **Sensitivity Runs**: Run regression with alternative definitions: `platform_count` only, `switching_frequency` only.
 2. **FDR Correction**: Apply Benjamini-Hochberg (FDR) correction to p-values from all three runs (main + 2 sensitivity).
 3. **Write Results**: Write results to `results/sensitivity_comparison.csv` with columns: `definition`, `beta`, `p_value`, `sign`, `n`, `fdr_p_value`.
 4. **Verify Robustness (SC-003)**: Read `results/sensitivity_comparison.csv` and verify:
 - Beta sign does not flip across operationalizations.
 - If signs flip: Log a CRITICAL warning "SC-003 Violation: Beta sign instability detected." and ensure the instability is recorded in the final report. **Do NOT halt the pipeline.**
 - If p > 0.10 for any variant but sign is stable, log "Warning: Variant p > 0.10 but sign stable; robustness maintained."
 5. **Generate Evidence**: Create `results/robustness_evidence.json` containing:
 - `sc003_status`: "PASS" (if p < 0.10 for all variants) or "FAIL" (if any variant p >= 0.10).
 - `details`: List of p-values and signs.
 - `message`: "SC-003 Met: p < 0.10 across operationalizations" or "SC-003 Warning: p > 0.10 detected".
 - **Note**: The task is complete upon generation of this file, regardless of the `sc003_status` value.
 6. **Conditional Artifact Handling**: If T025 generated `results/models/residuals.csv`, use the residualized switching index for these sensitivity runs. If not, use the original `switching_index`. Check for file existence before loading.
 - **Dependency**: T025.

- [X] T027 [US2] **Final Validation & Report**: Implement `code/03_model.py` (Part 3: Final Report).
 - **Steps**:
 1. **Merge Results**: Combine core model and sensitivity results.
 2. **Validate Output Schema**: Validate `results/models/regression_summary.json` against `contracts/output.schema.yaml`. If missing, fail with "Schema file missing".
 3. **Causal Language Validation**: Programmatically scan the entire `interpretation` string AND the generated textual summary for forbidden terms (causes, leads to, impacts). If found, **FAIL** the run.
 4. **Output**: Write `results/models/regression_summary.json` with standardized betas, p-values, VIF, and FDR-corrected p-values. Ensure `vif_scores` and **raw correlation matrix** are nested inside a `diagnostics` object.
 - **Dependency**: T026.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] **Test Model Output Schema**: Implement `tests/contract/test_model_output.py::test_output_matches_schema`. <!-- ATOMIZED: requested -->
 - **Logic**:
 1. Load `contracts/output.schema.yaml`.
 2. Load `results/models/regression_summary.json`.
 3. Assert that all keys in the schema exist in the JSON.
 4. Assert that `vif_scores` is a list/dict and `interpretation` is a string.
 5. **Expected Failure**: Initially, the JSON file is missing or keys are wrong.
 - **Dependency**: T025, T026, T027.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently.

---

## Phase 5: User Story 3 - Sensitivity Analysis and Visualization (Priority: P3)

**Goal**: Perform sensitivity analysis on switching index definition and generate publication-ready visualizations.

**Independent Test**: The script generates PDF/PNG files containing the regression plot, stratified plots, and a sensitivity table.

### Implementation for User Story 3

- [X] T036 [US3] **Scatter Plot**: Implement `code/04_visualize.py` (Part 1). <!-- FAILED: unspecified -->
 - **Actions**:
 1. **Scatter Plot**: Generate scatter plot with `switching_index` (X) vs `cognitive_score` (Y) and save to `results/figures/regression_plot.png`.
 2. **Confidence Interval**: Overlay fitted regression line with 95% confidence intervals.
 - **Dependency**: T025.

- [X] T037 [US3] **Stratified Plot**: Implement `code/04_visualize.py` (Part 2).
 - **Actions**:
 1. **Stratified Plot**: Generate stratified plot showing regression lines for distinct age groups (<30 and >30) if interaction term is significant.
 - **Dependency**: T025.

- [X] T038 [US3] **Sensitivity Table**: Implement `code/04_visualize.py` (Part 3). <!-- FAILED: unspecified -->
 - **Actions**:
 1. **Input**: Read `results/sensitivity_comparison.csv` (generated by T026).
 2. **Sensitivity Table**: Generate `results/figures/sensitivity_table.png` containing beta coefficients, p-values, n, and sign for all operationalizations.
 3. **Columns**: Ensure the visual table includes: `definition`, `beta`, `p_value`, `fdr_p_value`, `n`, `sign`.
 - **Dependency**: T026.

- [X] T039 [US3] **Final Report**: Implement `code/04_visualize.py` (Part 4).
 - **Actions**:
 1. **Final Report**: Write final JSON report (`results/final_report.json`) merging model summary with the associational text summary.
 2. **Validation**: Run `causal_language_scanner` on the `interpretation` field and fail if matches found.
 3. **Structure**: Reference `contracts/output.schema.yaml`.
 4. **Dependencies**: Ensure `results/models/regression_summary.json` (from T027) exists before merging.
 - **Dependency**: T036, T037, T038, T027.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T035a [P] [US3] **Test Visuals Generation - Regression**: Implement `tests/integration/test_visuals.py::test_regression_plot_exists`. <!-- ATOMIZED -->
 - **Logic**:
 1. Run the visualization script.
 2. Assert that `results/figures/regression_plot.png` exists and is not empty.
 3. **Expected Failure**: Initially, file is missing.
 - **Dependency**: T036, T037, T038, T039.

- [X] T035b [P] [US3] **Test Visuals Generation - Sensitivity**: Implement `tests/integration/test_visuals.py::test_sensitivity_table_exists`. <!-- ATOMIZED -->
 - **Logic**:
 1. Run the visualization script.
 2. Assert that `results/figures/sensitivity_table.png` exists and is not empty.
 3. **Expected Failure**: Initially, file is missing.
 - **Dependency**: T036, T037, T038, T039.

**Checkpoint**: All user stories should now be independently functional.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories.

- [ ] T041 [P] **Documentation**: Implement final documentation. <!-- ATOMIZE: requested -->
 - **Actions**:
 1. Create `docs/README.md` with project overview.
 2. Create `docs/quickstart.md` with pipeline instructions.
 3. **Verification**: Run `pydocstyle code/` and ensure 0 errors. If errors exist, fix them.
 - **Gate**: This task can only start after T017 and T025 are marked "Complete" and their schema tests (T013, T021b) pass.
 - **Dependency**: All previous phases.

- [ ] T042 [P] **Refactor**: Refactor code for clarity.
 - **Actions**:
 1. Refactor `code/*.py` to add Google-style docstrings to **all public functions and classes**.
 2. Refactor `code/02_engineer.py` for clarity and performance.
 3. **Verification**: Run `pytest --cov=code --cov-fail-under=80`. If coverage < 80%, refactor until met.
 4. **Gate**: This task can only start after T017 and T025 are marked "Complete" and their schema tests (T013, T021b) pass.
 - **Dependency**: T017, T025.

- [ ] T043 [P] **Edge Cases**: Implement edge case tests. <!-- ATOMIZE: requested -->
 - **Actions**:
 1. Implement `tests/unit/test_edge_cases.py::test_empty_dataframe_handling`:
 - Pass an empty DataFrame to `code/02_engineer.py`.
 - Assert that a `ValueError` is raised with "No data to process".
 2. Implement `tests/unit/test_edge_cases.py::test_missing_value_exclusion`:
 - Pass a DataFrame with missing `cognitive_flexibility_score`.
 - Assert that the output file is empty and a log entry "Excluded [count] rows" exists.
 3. **Verification**: Run `pytest tests/unit/test_edge_cases.py` and ensure all tests pass.
 4. **Gate**: This task can only start after T017 and T025 are marked "Complete" and their schema tests (T013, T021b) pass.
 - **Dependency**: T017, T025.

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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation.
- Models before services.
- Services before endpoints.
- Core implementation before integration.
- Story complete before moving to next priority.

### Specific Execution Chains

- **Phase 0 Chain**: T001 (Feasibility) -> T005 (Setup) -> T010 (Foundational).
- **User Story 1 Chain**: T015 (Ingestion) -> T016a (Instrument Docs) -> T017 (Engineering) -> T020 (Logging).
- **User Story 2 Chain**: T025 (Core Model) -> T026 (Sensitivity) -> T027 (Final Report).
- **User Story 3 Chain**: T036 (Scatter) -> T037 (Stratified) -> T038 (Sensitivity Table) -> T039 (Final Report).

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel.
- All Foundational tasks marked [P] can run in parallel (within Phase 2).
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows).
- All tests for a user story marked [P] can run in parallel.
- Models within a story marked [P] can run in parallel.
- Different user stories can be worked on in parallel by different team members.
- **Phase 0 tasks** can be executed in parallel as they involve independent research on different datasets (now merged into T001).

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data schema validation in tests/contract/test_dataset_schema.py::test_schema_matches_yaml"
Task: "Unit test for missing variable error handling in tests/unit/test_ingest_errors.py::test_missing_variable_raises_error"

# Launch all models for User Story 1 together:
Task: "Create utils.py with helpers for logging and checksums"
Task: "Implement data ingestion script in code/01_ingest.py"
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
- **Streaming**: If datasets exceed available RAM, use `streaming=True` and process in chunks (implemented in T015).
- **Causal Language**: Strictly enforce associational framing; any causal terms trigger a failure.
- **Phase 0 is Mandatory**: The pipeline MUST check for variables before downloading data.
- **Schema Validation**: Moved to Phase 0 to avoid circular dependency with Phase 1.
- **Residual Model**: T025 explicitly implements and saves the residualized model ONLY IF correlation > 0.7 (REQUIRED CHECK per FR-006).
- **Robustness Verification**: T026 explicitly verifies SC-003 criteria and generates `results/robustness_evidence.json`.
- **Unified Ingestion**: T015 handles each dataset separately to prevent merge conflicts and ensure parallel availability.
- **Instrument Documentation**: T016a ensures instrument validity is documented immediately after ingestion (Phase 3) before engineering.
- **Phase 0 Added**: Explicit research tasks (T046-T050) added to prevent "Data Gap" failures by validating variable existence in public datasets before implementation. (Now merged into T001).
- **T044 Removed**: The streaming robustness logic is already implemented in T015.
- **T042/T043 Gates**: T042 and T043 are now gated behind T017/T025 completion and schema test validation.