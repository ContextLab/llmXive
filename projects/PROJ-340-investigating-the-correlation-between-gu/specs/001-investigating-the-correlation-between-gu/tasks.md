# Tasks: Investigating the Correlation Between Gut Microbiome Composition and Sleep Architecture

**Input**: Design documents from `/specs/001-gut-microbiome-sleep-architecture/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
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

**Purpose**: Project initialization and basic structure

- [ ] T001a Create `code/` directory and `__init__.py`
- [ ] T001b Create `tests/` directory structure (`contract/`, `unit/`, `integration/`)
- [ ] T001c Create `data/` directory structure (`raw/`, `processed/`, `results/`, `config/`)
- [X] T002a Generate `requirements.txt` with pinned versions for `pandas`, `scipy`, `statsmodels`, `numpy`, `scikit-learn`, `pyyaml`, `pytest`, `spiec-easi`, `sparcc`
- [ ] T002b Create `.gitignore` and initialize virtualenv configuration
- [ ] [P] T003 Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin. Includes mode-switching logic, synthetic data generation, and pipeline validation setup.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004c **CREATE SCHEMA FILE**: Create `data/config/required_variables.yaml` with the initial schema structure (`required_predictors: [string], required_outcomes: [string]`). **Constraint**: Do NOT hardcode specific variable names. The file must define the *types* of variables required. **Output**: `data/config/required_variables.yaml` with schema. **This is the Single Source of Truth for variable lists used in T012/T078.**
- [X] T004a Define predictor schema (taxa) in `specs/001-gut-microbiome-sleep-architecture/contracts/dataset.schema.yaml` **referencing `data/config/required_variables.yaml` for the explicit list of required predictor variables.** **DEPENDS ON T004c.**
- [X] T004b Define outcome schema (sleep metrics) in `specs/001-gut-microbiome-sleep-architecture/contracts/dataset.schema.yaml` **referencing `data/config/required_variables.yaml` for the explicit list of required outcome variables.** **DEPENDS ON T004c.**
- [X] T005a Define output schema (CorrelationResult structure) in `specs/001-gut-microbiome-sleep-architecture/contracts/output.schema.yaml`
- [X] T006 Implement data loading utilities in `code/ingest.py` (CSV/TSV reader, column validation)
- [X] T006d_schema [P] **IMPLEMENT SCHEMA VALIDATION**: Define the checksum schema in `code/reference_validator.py`.
- [X] T006d_impl [P] **IMPLEMENT CHECKSUM RECORDING**: Implement `record_artifact_checksum(file_path, state_file)` in `code/reference_validator.py`.
- [X] T006d_init [P] **INITIALIZE CHECKSUM STATE**: Create `state/projects/PROJ-340-investigating-the-correlation-between-gu.yaml` with an empty `artifact_hashes` map.
- [X] T007 Configure CI workflow in `.github/workflows/analysis.yml` to run on `ubuntu-latest` with CPU/GB RAM limits
- [X] T008 Setup environment configuration management (`.env` template, `requirements.txt`)
- [X] T009a [P] Define Reference-Validator Agent schema in `code/reference_validator.py`
- [X] T009b [P] **IMPLEMENT REFERENCE-VALIDATOR AGENT**: Implement Reference-Validator Agent logic and integrate gate in CI (`.github/workflows/analysis.yml`).
- [X] T081a [P] **IMPLEMENT VALIDATION MODE LOGIC**: Implement `set_validation_mode()` in `code/ingest.py` to enable synthetic data generation.
- [X] T091 [P] **IMPLEMENT REAL-DATA SOURCE CONFIGURATION**: Create `data/config/real_data_sources.yaml`.
- [X] T092 [P] **UPDATE FETCH LOGIC TO USE CONFIG**: Refactor `code/ingest.py` to read from `data/config/real_data_sources.yaml`.
- [X] T085_init [P] **INITIALIZE VERIFIED CITATIONS LIST**: Create `data/citations/verified_dois.yaml`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion, Validation, and Pipeline Execution (Priority: P1) 🎯 MVP

**Goal**: Ingest raw data, validate variable presence, and ensure pipeline runs within 6 hours on CPU-only CI.

**Independent Test**: Run ingestion against a mock dataset missing "SWS duration"; verify system halts with specific error. Run dummy pipeline on CI; verify completion < 6h.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py`.
- [ ] [P] T011 [US1] Integration test for missing variable error handling in `tests/integration/test_missing_variable.py`.

### Implementation for User Story 1

- [X] T004d [US1] **POPULATE REQUIRED VARIABLES**: Read the variable list from the synthetic data generator and write it to `data/config/required_variables.yaml`.
- [X] T012 [US1] **IMPLEMENT VALIDATION LOGIC AND METRIC PERSISTENCE**: Implement `validate_variables()` in `code/ingest.py` to check for required predictors and outcomes.
- [X] T012b [US1] **IMPLEMENT ARTIFACT PERSISTENCE**: Ensure `validate_variables()` writes `data/results/variable_load_metrics.json`.
- [X] T013 [US1] **IMPLEMENT IMMEDIATE HALT LOGIC AND SUCCESS FINALIZATION**: Implement `load_data()` in `code/ingest.py` to call T012.
- [X] T014 Implement outlier detection logic in `code/ingest.py`.
- [X] T014b [US1] **IMPLEMENT OUTLIER FILTERING AND REPORT GENERATION**: Implement data filtering step and output the filtered dataset.
- [X] T014c [US1] Register the checksum for `data/processed/filtered_data.parquet`.
- [X] T015 [US1] **IMPLEMENT PIPELINE ORCHESTRATION WITH ATOMIC TIMEOUT**: Implement `run_pipeline()` in `code/main.py`.
- [X] T016 [US1] **IMPLEMENT EXECUTION TIMING CHECK AND EVIDENCE VALIDATION**: Implement a validation step to verify the timing evidence.
- [X] T017 [US1] Add logging for ingestion and validation steps in `code/ingest.py`
- [X] T081 [US1] **IMPLEMENT REAL-DATA FETCHING WITH STRICT FAIL-LOUD BEHAVIOR**: Refactor `code/ingest.py`.
- [X] T082 [US1] **IMPLEMENT REAL-DATA GATE IN ORCHESTRATION**: Update `code/main.py` to check for real data.

**Checkpoint**: User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Robust Associational Correlation Analysis (Priority: P2) & User Story 3 - Diagnostics

**Goal**: Compute correlations with automatic method selection, perform sensitivity, collinearity, and power analysis.

- [X] T020 Implement data distribution checks in `code/analysis.py`.
- [X] T020a Implement compositionality detection in `code/transform.py`.
- [X] T020b [P] **IMPLEMENT COMPOSITIONAL FALLBACK LOGIC**: Implement a recommendation to use SparCC or SpiecEasi if available.
- [X] T022a [P] **IMPLEMENT COMPOSITIONALITY CHECK**: Verify `data/metadata/compositionality_flag.json`.
- [X] T021f_algo [P] **IMPLEMENT DYNAMIC COLLINEARITY DETECTION**: Implement matrix rank check in `code/diagnostics.py`.
- [X] T021f_io [P] **WRITE COLLINEARITY OUTPUT**: Write the `static_collinearity_map.json` file.
- [X] T021 **IMPLEMENT CORRELATION METHOD SELECTION**: Implement `select_correlation_method()` in `code/analysis.py`.
- [X] T022 Implement compositional correction logic in `code/transform.py`.
- [X] T023 Implement ZINB/Hurdle model fitting in `code/analysis.py`.
- [X] T024 Implement Spearman and Pearson correlation functions in `code/analysis.py`
- [X] T025 **IMPLEMENT FDR CORRECTION AND OUTPUT**: Implement Benjamini-Hochberg FDR correction in `code/analysis.py`.
- [X] T078 [US3] **IMPLEMENT SENSITIVITY ANALYSIS**: Implement sensitivity analysis logic.
- [X] T079 [US3] **IMPLEMENT VIF CALCULATION**: Implement Variance Inflation Factor calculation in `code/diagnostics.py`.
- [X] T080 [US3] **IMPLEMENT POWER ANALYSIS**: Implement power analysis in `code/diagnostics.py`.
- [X] T026 [US2] **IMPLEMENT LOG SANITIZATION**: Implement `sanitize_logs()` in `code/report.py`.
- [X] T105 [P] **IMPLEMENT CAUSAL LANGUAGE SCANNER**: Create `code/report.py` function `scan_causal_language()`.
- [X] T106 [P] **DOCUMENT DESIGN DECISION: Stability Threshold Removal**: Document the rationale for removing the 'stability' threshold.

**Checkpoint**: US1 and US2 are integrated; Diagnostics complete.

---

## Phase 5: Real-Data Readiness & Verification (Priority: P8)

**Goal**: Prepare the pipeline for immediate execution on real data once a verified source is identified.

- [X] T083 [US1] **IMPLEMENT REAL-DATA VALIDATION**: Extend `code/ingest.py`.
- [X] T086 [US1] **UPDATE DOCUMENTATION FOR REAL-DATA EXECUTION**: Update documentation.

**Checkpoint**: The pipeline is now strictly "Real-Data Only" with a clear failure path for missing data.

---

## Phase 6: Data Acquisition & Synthetic Data Logic (Priority: P4)

**Goal**: Implement the specific logic for fetching real data and generating synthetic data.

## Phase 7: Integration & End-to-End Validation (Priority: P5)

**Goal**: Verify the entire pipeline executes correctly in both synthetic and real-data modes.

## Phase 8: Review Resolution & Robustness Enhancements (Priority: P6)

**Goal**: Address specific reviewer concerns regarding data integrity, error handling, and statistical rigor.

- [X] T100 [P] [US1] **IMPLEMENT STRICT REAL-DATA FETCH GUARD**: Refactor `code/ingest.py`.
- [X] T101 [P] [US2] **IMPLEMENT ROBUST ZINB FALLBACK LOGIC**: Add a specific error handler in `code/analysis.py`.
- [X] T102 [P] [US3] **ENHANCE POWER ANALYSIS REPORTING**: Update `code/diagnostics.py`.
- [X] T103 [P] **IMPLEMENT DATA STREAMING STUB FOR FUTURE SCALABILITY**: Create a placeholder function in `code/ingest.py`.
- [X] T104 [P] [US2] **ADD STATISTICAL CAVEATS TO REPORT**: Implement `generate_report()` in `code/report.py`.
