# Tasks: The Impact of Social Media Consumption Patterns on Cognitive Flexibility

**Input**: Design documents from `/specs/001-social-media-cognitive-flexibility/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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

## Phase 0: Data Feasibility Check (CRITICAL GATE)

**Purpose**: Verify the presence of required variables in the dataset source BEFORE any full download or processing. This phase MUST pass before Phase 1 begins.

**⚠️ CRITICAL**: If this phase fails, the project halts immediately with a "Data Gap" error. No data is downloaded.

- [X] T001 [P0] **Header/Stream Check**: Implement `code/00_feasibility_check.py` to perform a lightweight check (using `requests.head` or `datasets.load_dataset(..., streaming=True)` with a 1-row peek) to verify the URL is accessible and the dataset contains tabular data. Output `logs/feasibility_report.txt`.
- [X] T002 [P0] **Variable Presence Check**: Update `code/00_feasibility_check.py` to verify the presence of `self_reported_switching_frequency` and `cognitive_flexibility_score` (or validated proxy) in the dataset schema/headers. Log variable presence to stdout.
- [X] T003 [P0] **Fail Fast Logic**: Implement fail-fast logic in `code/00_feasibility_check.py`. If T002 fails, halt execution immediately with error: "Data Gap: Required variable [NAME] not found in verified dataset [URL]. Project cannot proceed per US-1 Scenario 2."
- [ ] T004 [P0] **Schema Validation**: Implement validation logic in `code/00_feasibility_check.py` to validate the dataset structure against `contracts/dataset.schema.yaml` (Plan Task 0.4). Write logs/schema_validation.log.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T005a [P] Create project directories: `data/raw`, `data/processed`, `code`, `results/models`, `results/figures`, `tests`, `contracts` in `projects/PROJ-453-.../`. <!-- FAILED: unspecified -->
- [X] T005b [P] Create `code/__init__.py` and `data/.gitkeep`.
- [X] T005c [P] Create `data/raw/.gitkeep`.
- [X] T006a [P] Create `code/requirements.txt` with specific dependencies: pandas, numpy, statsmodels, scikit-learn, pyyaml, requests, datasets, pytest.
- [X] T006b [P] Create `setup.py` if needed for package structure.
- [ ] T007a [P] Create `.ruff.toml` with linting configuration.
- [ ] T007b [P] Create `.black.toml` with formatting configuration.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T008 [P] Setup `contracts/dataset.schema.yaml` defining expected columns: switching_index, cognitive_flexibility_score, age, total_screen_time, num_platforms, switching_frequency.
- [ ] T009 [P] Setup `contracts/output.schema.yaml` defining model output structure: coefficients, p_values, vif_scores, diagnostics, interpretation.
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

- [ ] T013 [P] [US1] Implement `tests/contract/test_dataset_schema.py::test_schema_matches_yaml` to validate data schema against `contracts/dataset.schema.yaml`.
- [X] T014 [P] [US1] Implement `tests/unit/test_ingest_errors.py::test_missing_variable_raises_error` to test missing variable error handling.

### Implementation for User Story 1

- [X] T015a [US1] Implement download logic in `code/01_ingest.py`: Download raw data from verified public URLs (HILDA/ESS/AddHealth) using `requests` or `wget` as the PRIMARY method. **Strictly use public URLs; do NOT use datasets.load_dataset**. **FAIL LOUDLY** if fetch fails; do NOT fall back to synthetic data.
- [X] T015b [US1] Implement parse logic in `code/01_ingest.py`: Parse raw files and extract required columns.
- [ ] T015c [US1] Implement validation logic in `code/01_ingest.py`: Validate parsed data against `contracts/dataset.schema.yaml`.
- [X] T016a [US1] Implement `code/02_engineer.py`: **Document instrument validation sources** in `data/` (Constitution Principle VI). Record original validation sources for survey instruments used in a `data/instrument_sources.txt` file.
- [ ] T016b [US1] Implement `code/02_engineer.py`: Parse raw files and validate against `contracts/dataset.schema.yaml`.
- [X] T017 [US1] Implement `code/02_engineer.py`: Compute `switching_index = num_platforms * self_reported_switching_frequency`. Store as derived variable.
- [X] T018 [US1] Implement `code/02_engineer.py`: Handle missing outcomes by excluding rows and logging exclusion count (e.g., "Excluded N rows due to missing WCST data").
- [ ] T019 [US1] Implement `code/02_engineer.py`: Output `data/processed/participants_cleaned.csv`.
- [ ] T020 [US1] Add logging for data ingestion and variable engineering operations (level=INFO, destination=stdout, format: `[%(asctime)s] %(levelname)s: %(message)s`).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Associational Analysis and Model Fitting (Priority: P2)

**Goal**: Fit multiple linear regression models, compute diagnostics (VIF), and apply sensitivity analysis.

**Independent Test**: The analysis script runs on the cleaned CSV and produces a JSON report with coefficients, p-values, VIF scores, and corrected p-values.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Implement `tests/contract/test_model_output.py::test_output_matches_schema` to validate model output schema.
- [X] T022 [P] [US2] Implement `tests/unit/test_vif.py::test_vif_calculation_correctness` to test VIF calculation.
- [ ] T023 [P] [US2] Implement `tests/unit/test_causal_language.py::test_scanner_detects_forbidden_terms` to test causal language scanner.

### Implementation for User Story 2

- [X] T025 [US2] Implement `code/03_model.py`: **Mean-center** `switching_index` and `age` **THEN create interaction term** `switching_index * age` (Plan Task 2.2).
- [ ] T026 [US2] **Check Collinearity**: Implement `code/03_model.py`: Calculate correlation between `switching_index` and `total_screen_time`. If > 0.7, generate a distinct warning flag "Potential Mathematical Coupling" and log it.
- [ ] T027 [US2] **Conditional Residual Model**: **IF T026 flag is true** THEN run Residualized Model (regress switching on screen_time, use residuals as predictor). **Skip if T026 flag is false**.
- [ ] T028 [US2] Implement `code/03_model.py`: Fit OLS model with outcome `cognitive_flexibility_score` and predictors `switching_index` (or residuals), `total_screen_time`, `age`, and interaction term.
- [ ] T029 [US2] Implement `code/03_model.py`: Compute Variance Inflation Factor (VIF) for all predictors.
- [ ] T030 [US2] Implement `code/03_model.py`: Run Sensitivity Analysis (FR-005) with alternative definitions (`platform_count` only, `switching_frequency` only).
- [ ] T030a [US2] Implement `code/03_model.py`: Apply Benjamini-Hochberg (FDR) correction to p-values from sensitivity runs (FR-007). **Compare corrected p-values against 0.10 threshold and log failure if exceeded** (Plan Task 2.5 / SC-003).
- [ ] T031 [US2] Implement `code/03_model.py`: **Validate output against contracts/output.schema.yaml** (Plan Task 2.6).
- [ ] T032 [US2] **Causal Language Validation**: Programmatically scan the entire interpretation string AND the generated textual summary for forbidden terms (causes, leads to, impacts). If found, **FAIL** the run.
- [ ] T033 [US2] Output `results/models/regression_summary.json` with standardized betas, p-values, VIF, and FDR-corrected p-values. **Structure**: Ensure `vif_scores` and **raw correlation matrix** are nested inside a `diagnostics` object as required by SC-002.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis and Visualization (Priority: P3)

**Goal**: Perform sensitivity analysis on switching index definition and generate publication-ready visualizations.

**Independent Test**: The script generates PDF/PNG files containing the regression plot, stratified plots, and a sensitivity table.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T035 [P] [US3] Implement `tests/integration/test_visuals.py::test_plots_generated_correctly` to test visualization generation.

### Implementation for User Story 3

- [ ] T036 [US3] Implement `code/04_visualize.py`: Generate scatter plot with `switching_index` (X) vs `cognitive_score` (Y), fitted regression line, and 95% confidence intervals.
- [ ] T037 [US3] Implement `code/04_visualize.py`: Generate stratified plot showing regression lines for distinct age groups (<30 and >30) if interaction term is significant.
- [ ] T038 [US3] Implement `code/04_visualize.py`: Generate sensitivity table comparing beta coefficients across alternative operationalizations (`platform_count`, `switching_frequency`, `switching_index`).
- [ ] T039 [US3] Output `results/figures/regression_plot.png`, `results/figures/stratified_plot.png`, and `results/figures/sensitivity_table.png`.
- [ ] T039a [US3] Write final JSON report (results/final_report.json) merging model summary (T033) with the associational text summary. Ensure zero causal terms in `interpretation` field.
- [ ] T039b [US3] **Write final JSON report with associational language only** (Plan Task 3.4). Validate `interpretation` field for zero causal terms.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T041a [P] Create `docs/README.md` with project overview.
- [ ] T041b [P] Create `docs/quickstart.md` with pipeline instructions.
- [ ] T042a [P] Refactor `code/01_ingest.py` for clarity and performance.
- [ ] T042b [P] Refactor `code/02_engineer.py` for clarity and performance.
- [ ] T043a [P] Optimize `code/01_ingest.py` for streaming large datasets.
- [ ] T043b [P] Optimize `code/03_model.py` for memory usage.
- [ ] T044 [P] Implement `tests/unit/test_edge_cases.py::test_empty_dataframe_handling` and `tests/unit/test_edge_cases.py::test_missing_value_exclusion`.
- [ ] T045 [P] Run `docs/quickstart.md` validation to ensure full pipeline reproducibility.

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
- **Streaming**: If datasets exceed 7GB RAM, use `streaming=True` and process in chunks.
- **Causal Language**: Strictly enforce associational framing; any causal terms trigger a failure.
- **Phase 0 is Mandatory**: The pipeline MUST check for variables before downloading data.