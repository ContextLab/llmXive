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

## Phase 0: Data Feasibility Check (CRITICAL GATE)

**Purpose**: Verify the presence of required variables in the dataset source BEFORE any full download or processing. This phase MUST pass before Phase 1 begins.
**⚠️ CRITICAL**: If this phase fails, the project halts immediately with a "Data Gap" error. No data is downloaded.
**⚠️ NOTE**: Schema validation (T004) is now here to ensure Phase 0 can execute.

- [X] T001 [P0] **Header/Stream Check**: Implement `code/00_feasibility_check.py` to perform a lightweight check (using `requests.head` or `datasets.load_dataset(..., streaming=True)` with a 1-row peek) to verify the URL is accessible and the dataset contains tabular data. Output `logs/feasibility_report.txt`.
- [X] T002 [P0] **Variable Presence Check**: Update `code/00_feasibility_check.py` to verify the presence of `self_reported_switching_frequency` and `cognitive_flexibility_score` (or validated proxy) in the dataset schema/headers. Log variable presence to stdout.
- [X] T003 [P0] **Fail Fast Logic**: Implement fail-fast logic in `code/00_feasibility_check.py`. If T002 fails, halt execution immediately with error: "Data Gap: Required variable [NAME] not found in verified dataset [URL]. Project cannot proceed per US-1 Scenario 2."
- [X] T004 [P0] **Schema Validation**: Implement validation logic in `code/00_feasibility_check.py` to validate the dataset structure against `contracts/dataset.schema.yaml` (Plan Task 0.4). **Dependency**: Requires T008 (Schema Creation) to be completed first. Write logs/schema_validation.log.
- [X] T008 [P0] **Schema Creation**: Setup `contracts/dataset.schema.yaml` defining expected columns: switching_index, cognitive_flexibility_score, age, total_screen_time, num_platforms, switching_frequency. **Moved from Phase 1 to Phase 0 to resolve circular dependency.**

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, basic structure, contract definitions, and schema validation.

- [X] T005a [P] Create project directories: `data/raw`, `data/processed`, `code`, `results/models`, `results/figures`, `tests`, `contracts` in `projects/PROJ-453-.../`.
- [X] T005b [P] Create `code/__init__.py` and `data/.gitkeep`.
- [X] T005c [P] Create `data/raw/.gitkeep`.
- [X] T006a [P] Create `code/requirements.txt` with specific dependencies: pandas, numpy, statsmodels, scikit-learn, pyyaml, requests, datasets, pytest.
- [X] T006b [P] Create `setup.py` if needed for package structure.
- [X] T007a [P] Create `.ruff.toml` with specific rules: set `target-version = "py311"`, `line-length = 88`, `select = ["E", "F", "W"]`.
- [X] T007b [P] Create `.black.toml` with specific rules: set `line-length = 88`, `target-version = "py311"`, `include = "\\.pyi?$"`.
- [X] T009 [P] Setup `contracts/output.schema.yaml` defining model output structure: coefficients, p_values, vif_scores, diagnostics, interpretation.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T010 [P] Create `code/utils.py` with specific helpers: `log_setup()` (returns logger), `checksum_file(path)` (returns SHA256 string), and `causal_language_scanner(text, forbidden_words)` (returns list of matches).
- [X] T011 [P] Implement `code/__init__.py` with error handling classes and `__all__` exports.
- [X] T012 [P] Create `code/config.py` with constants `RANDOM_SEED = 42`, `DATA_ROOT = "data"`, `RESULTS_ROOT = "results"`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Variable Extraction (Priority: P1) 🎯 MVP

**Goal**: Download, parse, and extract specific predictor and outcome variables from public survey datasets (AddHealth, HILDA, ESS) without manual intervention.

**Independent Test**: The pipeline runs against a subset of the target dataset and outputs a CSV containing `switching_index`, `cognitive_flexibility_score`, `age`, and `total_screen_time` without errors.

**⚠️ Dependency Note**: T013 and T014 require T008 (Schema Setup) to be completed first.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T013 [P] [US1] Implement `tests/contract/test_dataset_schema.py::test_schema_matches_yaml` to validate data schema against `contracts/dataset.schema.yaml`.
- [X] T014 [P] [US1] Implement `tests/unit/test_ingest_errors.py::test_missing_variable_raises_error` to test missing variable error handling.

### Implementation for User Story 1

- [X] T015 [US1] **Unified Ingestion**: Implement `code/01_ingest.py` to download and parse **all three** designated public datasets (HILDA, ESS, AddHealth) in a single script.
 - **Logic**:
 1. **Pre-flight Check**: Verify `logs/feasibility_report.txt` exists and indicates a "PASS" status from Phase 0. If not, halt immediately with "Data Gap: Phase 0 feasibility check failed."
 2. Iterate through the list of datasets using **verified** sources:
 - **HILDA**: Use HuggingFace ID `hilda` (or specific verified URL if ID changes).
 - **ESS**: Use ESS data portal URL or verified HuggingFace equivalent.
 - **AddHealth**: Use direct URL ` (or specific file path) as a valid source.
 3. **Fail Loudly**: If a fetch fails, raise an exception immediately; do NOT fall back to synthetic data.
 4. **Variable Check**: After download, verify the downloaded dataset contains `self_reported_switching_frequency` and `cognitive_flexibility_score`. If missing, raise `ValueError` with "Data Gap: Downloaded dataset [URL] lacks required variables."
 5. **Output**: Save raw data to `data/raw/` and cleaned CSVs to `data/processed/` for each valid dataset.
 6. **Instrument Documentation**: Generate `data/instrument_sources.yaml` **after** ingestion. Use verified sources only. Schema: `survey_name`, `validation_citation`, `variable_mapping`.
- [X] T016a [US1] **Document Instrument Sources**: Implement `code/01_ingest.py` (or a dedicated helper) to create `data/instrument_sources.yaml` **immediately after ingestion** but **before** variable engineering (T017/T018). **Schema**: Must include `survey_name`, `validation_citation`, and `variable_mapping` (list of dicts: `[{original_var: "name", derived_var: "name", source_doc: "url"}]`). **Constitution**: Explicitly satisfies Constitution Principle VI and Plan Task 1.4 by ensuring instrument validity is documented before engineering. **Dependency**: Runs after T015 (Ingestion) and before T017 (Engineering).
- [X] T017 [US1] Implement `code/02_engineer.py`: Compute `switching_index = num_platforms * self_reported_switching_frequency`. Store as derived variable.
- [X] T018 [US1] Implement `code/02_engineer.py`: Handle missing outcomes by excluding rows and logging exclusion count (e.g., "Excluded N rows due to missing WCST data").
- [ ] T019 [US1] Implement `code/02_engineer.py`: Output `data/processed/participants_cleaned.csv`.
- [X] T020 [US1] Add logging for data ingestion and variable engineering operations (level=INFO, destination=stdout, format: `[%(asctime)s] %(levelname)s: %(message)s`).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Associational Analysis and Model Fitting (Priority: P2)

**Goal**: Fit multiple linear regression models, compute diagnostics (VIF), and apply sensitivity analysis.

**Independent Test**: The analysis script runs on the cleaned CSV and produces a JSON report with coefficients, p-values, VIF scores, and corrected p-values.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Implement `tests/contract/test_model_output.py::test_output_matches_schema` to validate model output schema.
- [X] T022 [P] [US2] Implement `tests/unit/test_vif.py::test_vif_calculation_correctness` to test VIF calculation.
- [X] T023 [P] [US2] Implement `tests/unit/test_causal_language.py::test_scanner_detects_forbidden_terms` to test causal language scanner.

### Implementation for User Story 2

- [X] T025 [US2] Implement `code/03_model.py`: **Mean-center** `switching_index` and `age` **THEN create interaction term** `switching_index * age` (Plan Task 2.2).
- [X] T026 [US2] **Check Collinearity**: Implement `code/03_model.py`: Calculate correlation between `switching_index` and `total_screen_time`. If > 0.7, generate a distinct warning flag "Potential Mathematical Coupling" and log it to `logs/collinearity_check.log` with `flag=true`. **Output**: Write to `logs/collinearity_check.log` and update `results/models/regression_summary.json` with a `collinearity_flag` field.
- [X] T027a [US2] **Fit Residual Model (Mandatory if flagged)**: **Dependency: T026**. **If T026 flag is true**:
 1. Read `logs/collinearity_check.log` to confirm flag.
 2. Regress `switching_index` on `total_screen_time`.
 3. Extract residuals and save to `results/models/residuals.csv`.
 4. Fit `cognitive_flexibility_score` on residuals + `age` + interaction.
 5. Store secondary coefficients in `results/models/residualized_coefficients.json`.
 **Output**: JSON file containing `residuals`, `secondary_coefficients`, `r_squared`, and `vif_scores`. **No skip flag allowed**; execution is mandatory if T026 flags high collinearity.
- [X] T027b [US2] **Save Residual Model**: **Dependency: T027a**. If T027a executed, serialize the residualized model results to `results/models/residualized_model.json`. **Output**: JSON file containing `residuals`, `secondary_coefficients`, `r_squared`, and `vif_scores`. **Skip if T026 flag is false**.
- [X] T028 [US2] Implement `code/03_model.py`: Fit OLS model with outcome `cognitive_flexibility_score` and predictors `switching_index` (or residuals), `total_screen_time`, `age`, and interaction term.
- [X] T029 [US2] Implement `code/03_model.py`: Compute Variance Inflation Factor (VIF) for all predictors. **Crucially**: Immediately construct a `diagnostics` dictionary containing `vif_scores` and the `correlation_matrix` (raw values) and assign it to the output object before validation.
- [X] T030 [US2] Implement `code/03_model.py`: Run Sensitivity Analysis (FR-005) with alternative definitions (`platform_count` only, `switching_frequency` only). <!-- FAILED: unspecified -->
- [ ] T030a [US2] **Generate Sensitivity Table**: Implement `code/03_model.py` to generate `results/sensitivity_comparison.csv` containing beta coefficients, p-values, and signs for all operationalizations (primary, platform_count, switching_frequency). **Verification**: Must explicitly verify SC-003 (beta sign stability, p < 0.10) and log success/failure. <!-- FAILED: unspecified -->
- [ ] T030c [US2] **Verify Robustness (SC-003)**: **Dependency: T030a**. Implement logic in `code/03_model.py` to read `results/sensitivity_comparison.csv` and verify: (1) Beta sign does not flip across operationalizations (strictly same sign: both positive or both negative), (2) Corrected p-value (Benjamini-Hochberg adjusted from T030a) < 0.10 for all. **Action**: If criteria fail, log "SC-003 Violation: Robustness not demonstrated" and halt execution. **Output**: Log entry confirming success or failure. <!-- FAILED: unspecified -->
- [ ] T031 [US2] Implement `code/03_model.py`: **Validate output against contracts/output.schema.yaml** (Plan Task 2.6). **Dependency**: Requires T009.
- [X] T032a [US2] **Scan Intermediate JSON**: Programmatically scan the intermediate `results/models/regression_summary.json` (output of T033) for forbidden causal terms (causes, leads to, impacts). If found, **FAIL** the run.
- [X] T032 [US2] **Causal Language Validation**: Programmatically scan the entire interpretation string AND the generated textual summary for forbidden terms (causes, leads to, impacts). If found, **FAIL** the run.
- [X] T033 [US2] Output `results/models/regression_summary.json` with standardized betas, p-values, VIF, and FDR-corrected p-values. **Structure**: Ensure `vif_scores` and **raw correlation matrix** are nested inside a `diagnostics` object as required by SC-002.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis and Visualization (Priority: P3)

**Goal**: Perform sensitivity analysis on switching index definition and generate publication-ready visualizations.

**Independent Test**: The script generates PDF/PNG files containing the regression plot, stratified plots, and a sensitivity table.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T035 [P] [US3] Implement `tests/integration/test_visuals.py::test_plots_generated_correctly` to test visualization generation.

### Implementation for User Story 3

- [X] T036 [US3] Implement `code/04_visualize.py`: Generate scatter plot with `switching_index` (X) vs `cognitive_score` (Y), fitted regression line, and confidence intervals. <!-- ATOMIZE: requested -->
- [X] T037 [US3] Implement `code/04_visualize.py`: Generate stratified plot showing regression lines for distinct age groups (<30 and >30) if interaction term is significant.
- [X] T038 [US3] Implement `code/04_visualize.py`: Generate sensitivity table comparing beta coefficients across alternative operationalizations (`platform_count`, `switching_frequency`, `switching_index`). <!-- FAILED: unspecified -->
- [X] T039 [US3] Output `results/figures/regression_plot.png`, `results/figures/stratified_plot.png`, and `results/figures/sensitivity_table.png`.
- [X] T039a [US3] Write final JSON report (`results/final_report.json`) merging model summary (T033) with the associational text summary. **Structure**: Reference `contracts/output.schema.yaml`. **Validation**: Run `causal_language_scanner` on the `interpretation` field and fail if matches found. Ensure zero causal terms in `interpretation` field.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T041a [P] Create `docs/README.md` with project overview.
- [X] T041b [P] Create `docs/quickstart.md` with pipeline instructions.
- [X] T042a [P] **Add Docstrings**: Refactor `code/*.py` to add Google-style docstrings to **all public functions and classes**. **Metric**: **[deferred] of public functions** must have docstrings.
- [X] T042b [P] Refactor `code/02_engineer.py` for clarity and performance.
- [X] T043a [P] **Implement Chunked Reading**: Optimize `code/01_ingest.py` to use `streaming=True` or chunked reading for datasets > 100MB. **Metric**: Memory usage must remain < 2GB during ingestion of 1GB+ dataset.
- [X] T043b [P] **Add Memory Profiling**: Add memory profiling logs to `code/03_model.py` to track peak memory usage during model fitting. **Metric**: Log peak memory usage in `logs/memory_profile.log` with format "Peak Memory: X MB".
- [X] T044 [P] Implement `tests/unit/test_edge_cases.py::test_empty_dataframe_handling` and `tests/unit/test_edge_cases.py::test_missing_value_exclusion`.
- [X] T045 [P] Run `docs/quickstart.md` validation to ensure full pipeline reproducibility.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Data Feasibility)**: No dependencies - MUST run first. Blocks all other phases.
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

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel.
- All Foundational tasks marked [P] can run in parallel (within Phase 2).
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows).
- All tests for a user story marked [P] can run in parallel.
- Models within a story marked [P] can run in parallel.
- Different user stories can be worked on in parallel by different team members.

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
- **Streaming**: If datasets exceed available RAM, use `streaming=True` and process in chunks.
- **Causal Language**: Strictly enforce associational framing; any causal terms trigger a failure.
- **Phase 0 is Mandatory**: The pipeline MUST check for variables before downloading data.
- **Schema Validation**: Moved to Phase 0 to avoid circular dependency with Phase 1.
- **Residual Model**: T027a/T027b explicitly implement and save the residualized model if collinearity is high (mandatory if flagged).
- **Robustness Verification**: T030a/T030c explicitly verify SC-003 criteria and halt if not met.
- **Unified Ingestion**: T015 handles all three datasets in one script to prevent merge conflicts and ensure parallel availability.
- **Instrument Documentation**: T016a ensures instrument validity is documented immediately after ingestion (Phase 3) before engineering.
- **Removed Phase O**: Meta-task T046 merged into T015 for direct executability.
