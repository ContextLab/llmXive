# Tasks: Predicting the Impact of Composition on the Vickers Hardness of Solder Alloys

**Input**: Design documents from `/specs/001-predict-solder-hardness/`
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

 Tasks MUST be organized by user story so each story can:
 - Be implemented independently
 - Be tested independently
 - Be delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create `data/` directory structure: `data/raw`, `data/processed`, `data/outputs`. **CRITICAL**: Verify existence of all three directories using `ls -R data/`.
- [ ] T001b [P] Create `code/` directory structure: `code/`, `code/ingestion`, `code/features`, `code/models`, `code/evaluation`, `code/visualization`, `code/utils`. **CRITICAL**: Verify existence of all directories using `ls -R code/`.
- [ ] T001c [P] Create `tests/` directory structure: `tests/`, `tests/contract`, `tests/integration`. **CRITICAL**: Verify existence of all directories using `ls -R tests/`.
- [ ] T002 Create `requirements.txt` at `projects/PROJ-328-predicting-the-impact-of-composition-on-/code/` with dependencies (PIN EXACT VERSIONS): `pandas`, `scikit-learn`, `xgboost`, `shap`, `numpy`, `matplotlib`, `pyyaml`, `requests`, `compositional==0.2.0`, `pdfplumber`, `pytest`, `flake8`, `black`, `mendeleev`.
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools. **CRITICAL**: Must run after T001a, T001b, T001c. **Depends on T001a, T001b, T001c**.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005a [P] Create scaffolding for `code/ingestion/` directory structure. **CRITICAL**: This task establishes the folder structure and placeholder files: `__init__.py`, `aggregator.py`, `cleaner.py`, `validator.py`. **Verify existence of all files.**
- [ ] T005b [P] Create scaffolding for `code/features/` directory structure. **CRITICAL**: Verify existence of `code/features/__init__.py`, `code/features/transformer.py`, `code/features/descriptor_engine.py`, `code/features/collinearity.py`.
- [ ] T007 [P] Create base data models/entities (`SolderComposition`, `CompositionalDescriptor`) in `code/models/`. **CRITICAL**: Verify file creation. **Depends on T005a**.
- [ ] T008a [P] **Search and Identify Sources**: Conduct initial search for candidate URLs for Materials Project, NIST, OpenAlloy, and specific PDFs for literature scraping. Output a raw list of candidate URLs to a temporary file `data/config/candidate_sources.txt`. **CRITICAL**: This task does NOT generate the final `research.md` yet. **Depends on T001a, T001b, T001c**.
- [ ] T008b [P] **Verify Research Sources**: Run the Reference-Validator Agent on the draft content from T008a. Generate `specs/001-predict-solder-hardness/research_verified.md` containing only verified citations and URLs. **CRITICAL**: This task MUST run after T008a. If verification fails, the pipeline halts. **Depends on T008a**.
- [ ] T009a [P] Create scaffolding for `code/utils/` directory structure. **CRITICAL**: Verify existence of all files: `__init__.py`, `logger.py`.
- [ ] T009b [P] Configure error handling and logging infrastructure in `code/utils/`. **CRITICAL**: This step depends on T009a.
- [ ] T009c [P] **Populate `sources.yaml`**: Read the **verified** `research_verified.md` from T008b and populate `data/config/sources.yaml` with the specific, verified URLs and API endpoints. **CRITICAL**: This task MUST run after T008b. **Depends on T008b**.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Aggregate and validate solder hardness dataset (Priority: P1) 🎯 MVP

**Goal**: Aggregate ≥100 unique solder alloy compositions with Vickers hardness from open sources into a unified dataset with validation.

**Independent Test**: Execute ingestion pipeline on GitHub Actions free-tier runner and verify output dataset contains ≥100 unique compositions with non-null hardness values and complete elemental breakdowns. If 50 ≤ N < 100, verify warning is emitted.

### Implementation for User Story 1

- [ ] T012a [US1] **Fetch Data from APIs**: Implement `code/ingestion/aggregator.py` to fetch data from verified sources: 1) Materials Project API, 2) NIST/UCI repositories, 3) Direct URLs from `data/config/sources.yaml` (populated by T009c). **CRITICAL**: Pre-check: Verify `research_verified.md` exists and `sources.yaml` is populated. If missing, raise `ConfigError`. **Depends on T009c**.
- [ ] T012b [US1] **Scrape Literature PDFs**: Implement PDF scraping in `code/ingestion/aggregator.py` using `pdfplumber` based on `research_verified.md`. **CRITICAL**: Logic: 1) Extract tables from specified PDFs. 2) Parse elemental composition and hardness. 3) Handle N<50: If total N < 50 after scraping, log a severe warning and proceed with a reduced N flag (do NOT halt). 4) Handle partial data: Log failures to `ingestion_log.txt` but proceed if N >= 50. **Depends on T012a**.
- [ ] T013 [US1] Implement data cleaning and filtering logic in `code/ingestion/cleaner.py` to:
 - Exclude alloys with >5 elements (read threshold from `code/config.py` `MAX_ELEMENTS`)
 - Standardize hardness to HV units: **CRITICAL**: Use explicit conversion factors: 1 GPa = 10.197 HV, 1 kgf/mm² = 9.807 HV.
 - Filter for room-temperature measurements only: verify column `measurement_temp_c` exists; filter where `abs(measurement_temp_c - config.ROOM_TEMP_THRESHOLD_C) <= config.ROOM_TEMP_TOLERANCE_C`.
 - **Manual Review Flagging**: Identify records where `abs(measurement_temp_c - config.ROOM_TEMP_THRESHOLD_C) > config.ROOM_TEMP_TOLERANCE_C` but `<= 2 * config.ROOM_TEMP_TOLERANCE_C` and write them to `data/processed/manual_review_queue.csv`.
 - Validate elemental composition sums to ≥95% of total alloy composition (read threshold from `code/config.py`).
 - **Record Validation**: Log the specific records that failed the composition sum check to `data/processed/validation_logs/filtered_records.csv` with reason codes. **CRITICAL**: Generate a SHA256 checksum for `filtered_records.csv` and append the hash to `data/checksums.txt`.
 - **Output**: Save cleaned data to `data/processed/solder_hardness_cleaned.csv`. **CRITICAL**: This file is the ONLY input for T014.
 - **Handle N < 50**: If total N < 50 after cleaning, log a severe warning and proceed with a reduced N flag (do NOT halt). **Depends on T012a, T012b**.
- [ ] T014 [US1] Implement validation logic in `code/ingestion/validator.py` to check for non-null hardness and complete composition. **CRITICAL**:
 1. **Input**: Read ONLY `data/processed/solder_hardness_cleaned.csv` (output of T013).
 2. **Calculate Composition Sums**: Explicitly calculate the sum of elemental compositions for every record.
 3. **Enforce Threshold**: If a record's composition sum is <95%, mark it as invalid.
 4. **Threshold Check**: If total N < 50, log a severe warning and proceed with a reduced N flag (do NOT halt). If 50 <= N < 100, proceed but flag for power limitation.
 5. **Write Status**: Explicitly write `threshold_status` ('N>=100', '50<=N<100', 'N<50'), `exact_N`, and `warning_text` to `data/processed/.ingestion_status.json`. **This file is the single source of truth for SC-004 metrics.**
- [ ] T016b [US1] **Generate Validation Report Script**: Write a Python script `code/ingestion/generate_validation_report.py` that reads `data/processed/.ingestion_status.json` and generates `data/processed/validation_report.yaml`. **CRITICAL**:
 - **Input Schema**: `threshold_status` (str), `exact_N` (int), `warning_text` (str).
 - **Output Schema**: `status` (str), `count` (int), `power_limitation_warning` (str).
 - **Logic**: Read JSON, map to YAML, write file.
 - **CRITICAL**: Ensure no undefined variables.
- [ ] T016c [US1] **Verify Validation Report Generation**: Run `code/ingestion/generate_validation_report.py` with a mock `data/processed/.ingestion_status.json` to ensure it executes without errors and produces valid YAML. **CRITICAL**: If script fails, halt. **Depends on T016b**.
- [ ] T019 [US1] **Execute Validation Report Generation**: Run the script from T016b (verified by T016c) to produce `data/processed/validation_report.yaml`. **Depends on T016c**.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---
## Phase 4: User Story 2 - Train and compare composition-to-hardness regression models (Priority: P2)

**Goal**: Train XGBoost and linear regression models with cross-validation, bootstrap comparison, SHAP analysis, and VIF diagnostics.

### Test-First: User Story 2 (OPTIONAL - only if tests requested) ⚠️
*Note: These tasks define contracts for T020-T021 and must be written before implementation code exists.*

- [ ] T020 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output.py`
- [ ] T021 [P] [US2] Integration test for model training pipeline in `tests/integration/test_model_training.py`

### Implementation for User Story 2

- [ ] T023a [US2] Implement CLR transform utility in `code/features/transformer.py` using `compositional` library to handle closure problem. **Output**: A function to apply CLR to a vector of values.
- [ ] T023b [US2] Implement descriptor computation in `code/features/descriptor_engine.py` to calculate weighted mean atomic mass, electronegativity variance, atomic radius variance, weighted average melting point, and valence electron concentration. **Method**:
 1. **Use RAW Percentages**: Use the raw elemental composition percentages as weights for calculating weighted means of physical properties (e.g., atomic mass).
 2. **Compute Physical Descriptors**: Calculate physical descriptors using standard elemental property tables from the `mendeleev` library and the raw percentages.
 3. **Feature Matrix**: The final feature matrix consists of the CLR-transformed composition values and the computed physical descriptors.
 4. Ensure the output is a clean, tabular feature matrix ready for T024 and T025.
- [ ] T024 [US2] Implement VIF calculation in `code/features/collinearity.py` to flag predictors with VIF ≥ 5 (requires output from T023b).
- [ ] T024b [US2] **Configure CPU-Only Execution**: Create `code/models/config_cpu.py` to explicitly set all XGBoost and Linear Regression parameters to enforce CPU-only execution (e.g., `n_jobs=1`, `device='cpu'`, disable GPU acceleration flags).
- [ ] T025 [US2] Implement XGBoost training with grid search (≤10 combinations) in `code/models/xgboost_trainer.py`. **CRITICAL**: This script MUST import and use the configuration from `code/models/config_cpu.py` to enforce CPU-only execution.
- [ ] T026 [US2] Implement Linear Regression baseline training in `code/models/linear_trainer.py`. **CRITICAL**: This script MUST import and use the configuration from `code/models/config_cpu.py` to enforce CPU-only execution.
- [ ] T027 [US2] Implement k-fold cross-validation for both models in `code/evaluation/cv.py` (requires T025/T026)
- [ ] T028 [US2] Implement bootstrap resampling for confidence intervals on held-out test set in `code/evaluation/bootstrap.py`
- [ ] T029a [US2] **Define Sensitivity Thresholds**: Create `code/evaluation/thresholds.py` to define the specific set of R² thresholds for the sensitivity analysis (e.g., {low: 0.4, medium: 0.6, high: 0.7} or a configurable range). Output to `data/config/sensitivity_thresholds.yaml`. **CRITICAL**: This task defines the input for the sweep. **Depends on T028**.
- [ ] T029b [US2] **Compute Bootstrap Model Comparison**: Implement Bootstrap Model Comparison in `code/evaluation/bootstrap.py` to compare XGBoost vs Linear Regression using a resampling approach. Output metrics to `data/processed/bootstrap_comparison.yaml`. **CRITICAL**: This task is independent of the threshold sweep. **Depends on T028**.
- [ ] T029c [US2] **Compute Sensitivity Metrics**: Implement Sensitivity Analysis in `code/evaluation/sensitivity.py`. Generate output to `data/processed/sensitivity_analysis.yaml` and `data/outputs/sensitivity_plot.png`. **CRITICAL**: Use thresholds defined in T029a. **Depends on T029a, T028**.
- [ ] T030 [US2] Implement SHAP value calculation and top-3 feature ranking in `code/evaluation/shap_analysis.py`
- [ ] T031 [US2] Save model artifacts, metrics, and diagnostics to `models/` and `data/processed/`
- [ ] T031b [US2] **Generate Predictions**: Implement inference script in `code/evaluation/predict.py` to run the trained models (from T025/T026) on the test set and save results to `data/processed/predictions.csv`. **CRITICAL**: This task produces the `predictions.csv` artifact required by T032. **Depends on T025, T026**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate interpretable visualizations and partial dependence plots (Priority: P3)

**Goal**: Generate scatter plot of predicted vs. measured hardness with error bars and partial dependence plots for top features.

- [ ] T032 [US3] **Embed Associational Warning**: Update `data/processed/predictions.csv` (produced by T031b) and `data/processed/report.yaml` to include an explicit "Associational Analysis Only" warning in metadata. **CRITICAL**: **Depends on T031b**.
- [ ] T035 [US3] **Generate Paper Draft**: Create `docs/paper_draft.md` containing the methodology, results, and discussion sections.
- [ ] T036 [US3] Implement scatter plot generation in `code/visualization/scatter.py` with % CI error bars (requires T031b predictions).
- [ ] T037 [US3] Implement partial dependence plot generation in `code/visualization/pdp.py` for top-ranked SHAP features (requires T030 output).
- [ ] T038 [US3] Save all plots to `data/outputs/` with correct labels and units.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Documentation updates in `README.md` and `docs/`
- [ ] T041 Code cleanup and refactoring
- [ ] T042 Performance optimization to ensure <6h runtime on free-tier
- [ ] T043 [P] Additional unit tests in `tests/unit/`
- [ ] T044 Run quickstart.md validation