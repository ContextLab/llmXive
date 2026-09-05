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

- [ ] T001 [P] **Initialize Project Directory Structure**: Create `data/` (`raw`, `processed`, `outputs`), `code/` (`ingestion`, `features`, `models`, `evaluation`, `visualization`, `utils`), and `tests/` (`contract`, `integration`) directories. **CRITICAL**: Verify existence of all directories using `ls -R data/`, `ls -R code/`, `ls -R tests/`.
- [ ] T002 [P] Create `requirements.txt` at `projects/PROJ-328-predicting-the-impact-of-composition-on-/requirements.txt` with dependencies (PIN MINIMUM VERSIONS): `pandas`, `scikit-learn`, `xgboost`, `shap`, `numpy`, `matplotlib`, `pyyaml`, `requests`, `compositional>=0.2.0`, `pdfplumber`, `pytest`, `flake8`, `black`, `mendeleev`.
- [X] T003a [P] Create `.flake8` and `pyproject.toml` at repository root with specific linting rules (e.g., `max-line-length = 88`, `ignore = E203, W503`). **CRITICAL**: Verify file creation and content.
- [ ] T003b **Verify linting configuration by running `flake8` on a sample file**. **CRITICAL**: Must run immediately after T003a. **Depends on T003a**.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005b [P] Create scaffolding for `code/features/` directory structure. **CRITICAL**: Verify existence of `code/features/__init__.py`, `code/features/transformer.py`, `code/features/descriptor_engine.py`, `code/features/collinearity.py`.
- [X] T006 [P] Create `code/config.py` with configuration constants: `MAX_ELEMENTS`, `ROOM_TEMP_THRESHOLD_C`, `ROOM_TEMP_TOLERANCE_C`, `COMPOSITION_SUM_THRESHOLD`, `MIN_N_FOR_POWER`, `TARGET_N`. **CRITICAL**: Verify file creation and content. Ensure `COMPOSITION_SUM_THRESHOLD` is explicitly defined as a numeric value (e.g., 95.0) or a clear placeholder that triggers a validation error if undefined.
- [X] T007 [P] Create base data models/entities in `code/models/entities.py`. **CRITICAL**: Define `SolderComposition` class with attributes: `elemental_breakdown` (dict), `hardness_hv` (float), `alloy_family` (str), `source_citation` (str). Define `CompositionalDescriptor` class with attributes: `weighted_mean_atomic_mass`, `electronegativity_variance`, `atomic_radius_variance`, `weighted_avg_melting_point`, `valence_electron_concentration`. **Verify file creation.** **Depends on T001**.
- [X] T008a [P] **Generate Research Sources**: Generate the initial draft `research.md` by programmatically querying the spec's source list and known repositories for Materials Project, NIST, OpenAlloy, and specific PDFs for literature scraping. Output a raw list of candidate URLs to `data/config/candidate_sources.txt`. **CRITICAL**: This task DOES NOT depend on any existing `research_verified.md`. It creates the initial draft from the spec.
- [ ] T008b **Verify Research Sources**: Run the Reference-Validator Agent on the draft content from T008a. Generate `specs/001-predict-solder-hardness/research_verified.md` containing only verified citations and URLs. **CRITICAL**: This task MUST run after T008a. If verification fails, the pipeline halts. **Depends on T008a**.
- [ ] T009a [P] Create scaffolding for `code/utils/` directory structure. **CRITICAL**: Verify existence of all files: `__init__.py`.
- [X] T009b [P] Create `code/utils/logger.py` with a `get_logger()` function that writes to `logs/pipeline.log` in JSON format. **CRITICAL**: This step depends on T009a. **Depends on T009a**.
- [ ] T009c [P] **Populate `sources.yaml`**: Read the **verified** `research_verified.md` from T008b and populate `data/config/sources.yaml` with the specific, verified URLs and API endpoints. **CRITICAL**: This task MUST run after T008b. **Depends on T008b**.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Aggregate and validate solder hardness dataset (Priority: P1) 🎯 MVP

**Goal**: Aggregate ≥100 unique solder alloy compositions with Vickers hardness from open sources into a unified dataset with validation.

**Independent Test**: Execute ingestion pipeline on GitHub Actions free-tier runner and verify output dataset contains ≥100 unique compositions with non-null hardness values and complete elemental breakdowns. If 50 ≤ N < 100, verify warning is emitted.

### Implementation for User Story 1

- [X] T012d [US1] **Define and Execute Systematic Literature Review**: Define the PRISMA protocol in `code/ingestion/slit_review_protocol.md` based on the **verified** sources from T008b. Then, implement the actual search, screening, and extraction logic in `code/ingestion/aggregator.py` to scrape tables from the specific PDFs listed in `research_verified.md` (from T008b) and the SLR protocol. **CRITICAL**: Logic: 1) Extract tables from specified PDFs. 2) Parse elemental composition and hardness. 3) Handle N<50: If total N < 50 after scraping, log a severe warning and proceed with a reduced N flag (do NOT halt). 4) Handle partial data: Log failures to `ingestion_log.txt` but proceed if N >= 50. **CRITICAL**: **Depends on T008b, T009c**.
- [ ] T012a [US1] **Fetch Data from APIs**: Implement `code/ingestion/aggregator.py` to fetch data from verified sources: 1) Materials Project API, 2) NIST/UCI repositories, 3) Direct URLs from `data/config/sources.yaml` (populated by T009c). **CRITICAL**: Pre-check: Verify `research_verified.md` exists and `sources.yaml` is populated. If missing, raise `ConfigError`. **Depends on T009c**.
- [ ] T012c [US1] **Fetch Data from OpenAlloy**: Implement `code/ingestion/aggregator.py` to fetch data specifically from the OpenAlloy source (or its verified mirror) as mandated by FR-001. **CRITICAL**: Must use the verified URL from `sources.yaml`. **Depends on T009c**. <!-- FAILED: unspecified -->
- [~] T012g [US1] **Write Raw Data to Immutable Store**: Implement logic in `code/ingestion/aggregator.py` to write ALL fetched/scraped data (from T012a, T012c, T012d) to `data/raw/` as immutable files (e.g., `raw_mp.json`, `raw_lit.csv`, `raw_openalloy.json`, `raw_slr.csv`) BEFORE any cleaning. **CRITICAL**: Generate SHA256 checksums for all raw files and append to `data/checksums.txt`. **Depends on T012a, T012c, T012d**.
- [ ] T013 [US1] Implement data cleaning and filtering logic in `code/ingestion/cleaner.py` to:
 - Exclude alloys with >5 elements (read threshold from `code/config.py` `MAX_ELEMENTS`)
 - Standardize hardness to HV units: **CRITICAL**: Read conversion factors from `code/config.py` (e.g., `HV_PER_GPA`). Do NOT hardcode.
 - Filter for room-temperature measurements only: verify column `measurement_temp_c` exists; filter where `abs(measurement_temp_c - config.ROOM_TEMP_THRESHOLD_C) <= config.ROOM_TEMP_TOLERANCE_C`.
 - **Manual Review Flagging**: Identify records where `abs(measurement_temp_c - config.ROOM_TEMP_THRESHOLD_C) > config.ROOM_TEMP_TOLERANCE_C` but `<= 2 * config.ROOM_TEMP_TOLERANCE_C` and write them to `data/processed/manual_review_queue.csv`.
 - **Validate Elemental Composition**: Iterate every record, sum elemental composition values. Read `COMPOSITION_SUM_THRESHOLD` from `code/config.py`. **CRITICAL**: If the value is undefined, null, or marked as "[deferred]", raise a `ConfigError` and halt execution. Do NOT use a default value. If a numeric value exists, use it. If sum < `COMPOSITION_SUM_THRESHOLD`, mark record as invalid and log to `data/processed/validation_logs/filtered_records.csv` with reason code `COMPOSITION_SUM_LOW`. **CRITICAL**: Log the specific records that failed the composition sum check to `data/processed/validation_logs/filtered_records.csv` with reason codes. **CRITICAL**: Generate a SHA256 checksum for `filtered_records.csv` and append the hash to `data/checksums.txt`.
 - **Output**: Save cleaned data to `data/processed/solder_hardness_cleaned.csv`. **CRITICAL**: This file is the ONLY input for T014.
 - **Handle N < 50**: If total N < 50 after cleaning, log a severe warning and proceed with a reduced N flag (do NOT halt). **CRITICAL**: Write `power_limitation_warning: 'N < 50'` to `data/processed/.ingestion_status.json`. **Depends on T012g**.
- [ ] T014 [US1] Implement validation reporting logic in `code/ingestion/validator.py` to check for non-null hardness and complete composition. **CRITICAL**:
 1. **Input**: Read `data/processed/.ingestion_status.json` (output of T013).
 2. **Calculate Composition Sums**: Explicitly calculate the sum of elemental columns for every record in the cleaned file to confirm no invalid records remain.
 3. **Enforce Threshold**: Confirm no records in `cleaned.csv` have composition sum < `COMPOSITION_SUM_THRESHOLD` (read from `code/config.py`).
 4. **Count Non-Null Hardness**: Count records where `hardness_hv` is not null in `cleaned.csv`.
 5. **Threshold Check**: If total N < 50, log a severe warning and proceed with a reduced N flag (do NOT halt). If 50 <= N < 100, proceed but flag for power limitation.
 6. **Write Status**: Explicitly write `threshold_status` ('N>=100', '50<=N<100', 'N<50'), `exact_N`, and `power_limitation_warning` (if applicable) to `data/processed/.ingestion_status.json`. **This file is the single source of truth for SC-004 metrics.** **CRITICAL**: If N < 50, ensure `power_limitation_warning` is set to 'N < 50'. **Depends on T013**.
- [ ] T016b [US1] **Generate Validation Report Script**: Write a Python script `code/ingestion/generate_validation_report.py` that reads `data/processed/.ingestion_status.json` and generates `data/processed/validation_report.yaml`. **CRITICAL**:
 - **Input Schema**: `threshold_status` (str), `exact_N` (int), `power_limitation_warning` (str).
 - **Output Schema**: `status` (str), `count` (int), `power_limitation_warning` (str).
 - **Logic**: Read JSON, map to YAML, write file.
 - **CRITICAL**: Ensure no undefined variables. **Depends on T014**.
- [ ] T016c [US1] **Verify Validation Report Generation**: Run `code/ingestion/generate_validation_report.py` with a mock `data/processed/.ingestion_status.json` to ensure it executes without errors and produces valid YAML. **CRITICAL**: If script fails, halt. **Depends on T016b**.
- [ ] T019 [US1] **Execute Validation Report Generation**: Run the script from T016b (verified by T016c) to produce `data/processed/validation_report.yaml`. **Depends on T016c**.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---
## Phase 4: User Story 2 - Train and compare composition-to-hardness regression models (Priority: P2)

**Goal**: Train XGBoost and linear regression models with cross-validation, bootstrap comparison, SHAP analysis, and VIF diagnostics.

### Test-First: User Story 2 (OPTIONAL - only if tests requested) ⚠️
*Note: These tasks define contracts for T020-T021 and must be written before implementation code exists.*

- [X] T020 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output.py`
- [X] T021 [P] [US2] Integration test for model training pipeline in `tests/integration/test_model_training.py`

### Implementation for User Story 2

- [ ] T023a [US2] Implement CLR transform utility in `code/features/transformer.py` using `compositional` library to handle closure problem. **Output**: A function to apply CLR to a vector of values.
- [ ] T023b [US2] Implement descriptor computation in `code/features/descriptor_engine.py` to calculate weighted mean atomic mass, electronegativity variance, atomic radius variance, weighted average melting point, and valence electron concentration. **Method**:
 1. **Load Raw Composition**: Read raw elemental composition percentages (which sum to 1.0).
 2. **Compute Physical Descriptors**: Calculate physical descriptors using standard elemental property tables from the `mendeleev` library and the **raw elemental composition percentages** as weights. **CRITICAL**: Use the raw percentages (normalized to sum to 1) as weights for weighted averages/variances. Do NOT use CLR-transformed values as weights, as they can be negative and do not sum to 1.
 3. **Generate CLR Feature Vector**: Apply the CLR transform (from T023a) to the raw elemental composition percentages to create the feature vector for the ML model.
 4. **Feature Matrix**: The final feature matrix consists of the CLR-transformed composition values AND the computed physical descriptors derived from the raw percentages.
 5. Ensure the output is a clean, tabular feature matrix ready for T024 and T025. **Depends on T023a**.
- [ ] T024 [US2] Implement VIF calculation in `code/features/collinearity.py` to flag predictors with VIF ≥ 5 (requires output from T023b).
- [ ] T024b [US2] **Configure CPU-Only Execution**: Create `code/models/config_cpu.py` to explicitly set all XGBoost and Linear Regression parameters to enforce CPU-only execution (e.g., `n_jobs=1`, `device='cpu'`, disable GPU acceleration flags).
- [ ] T024c [US2] **Verify CPU Execution**: Implement `code/models/verify_cpu.py` to run a small dummy training loop and assert that no GPU/CUDA devices are detected or used (e.g., check `torch.cuda.is_available()` or XGBoost device logs). **CRITICAL**: This task ensures FR-010 is verifiable. **Depends on T024b**.
- [ ] T025 [US2] Implement XGBoost training with grid search (≤10 combinations) in `code/models/xgboost_trainer.py`. **CRITICAL**: This script MUST import and use the configuration from `code/models/config_cpu.py` to enforce CPU-only execution. **Depends on T024c**.
- [ ] T026 [US2] Implement Linear Regression baseline training in `code/models/linear_trainer.py`. **CRITICAL**: This script MUST import and use the configuration from `code/models/config_cpu.py` to enforce CPU-only execution. **Depends on T024c**.
- [ ] T027 [US2] Implement k-fold cross-validation for both models in `code/evaluation/cv.py` (requires T025/T026)
- [ ] T028 [US2] Implement bootstrap resampling for confidence intervals on held-out test set in `code/evaluation/bootstrap.py`
- [ ] T029a [US2] **Configure Sensitivity Thresholds**: Create `code/evaluation/thresholds.py` to define the specific set of R² thresholds for the sensitivity analysis. **CRITICAL**: Do NOT hard-code values. Instead, read thresholds from `data/config/sensitivity_config.yaml` or generate a dynamic range based on the observed R² distribution (e.g., min to max in steps of 0.1). Output to `data/config/sensitivity_thresholds.yaml`. **Depends on T025, T026**.
- [ ] T029b [US2] **Compute Bootstrap Model Comparison**: Implement Bootstrap Model Comparison in `code/evaluation/bootstrap.py` to compare XGBoost vs Linear Regression using a resampling approach. Output metrics to `data/processed/bootstrap_comparison.yaml`. **CRITICAL**: This task is independent of the threshold sweep. **Depends on T028**.
- [ ] T029c [US2] **Compute Sensitivity Metrics**: Implement Sensitivity Analysis in `code/evaluation/sensitivity.py`. **CRITICAL**: For each threshold T in `data/config/sensitivity_thresholds.yaml` (generated by T029a), calculate `fraction = (count of bootstrap R² > T) / total_bootstrap_samples`. Generate output to `data/processed/sensitivity_analysis.yaml` and `data/outputs/sensitivity_plot.png`. **Depends on T029a, T028**.
- [ ] T030 [US2] Implement SHAP value calculation and top-k feature ranking in `code/evaluation/shap_analysis.py`. **CRITICAL**: Save ranked features to `data/processed/shap_ranking.yaml` with keys: `feature_name`, `mean_abs_shap_value`, `rank`. **Depends on T025, T026**.
- [ ] T031 [US2] Save model artifacts, metrics, and diagnostics to `models/` and `data/processed/`
- [ ] T031b [US2] **Generate Predictions and Bootstrap CIs**: Implement inference script in `code/evaluation/predict.py` to run the trained models (from T025/T026) on the test set. **CRITICAL**: Combine held-out test predictions with the bootstrap resampling logic (from T028) to calculate R² and RMSE with confidence intervals. Save predictions to `data/processed/predictions.csv` and the calculated metrics (including CIs) to `data/processed/test_metrics.yaml`. **CRITICAL**: This task produces the `test_metrics.yaml` artifact required by T035. **Depends on T025, T026, T028**.
- [ ] T031c [US2] **Generate Report YAML**: Create `code/evaluation/generate_report.py` to produce `data/processed/report.yaml` containing summary metrics and associational framing. **CRITICAL**: This task MUST include the "Associational Analysis Only" warning in the metadata of the report. **Depends on T025, T026, T030**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate interpretable visualizations and partial dependence plots (Priority: P3)

**Goal**: Generate scatter plot of predicted vs. measured hardness with error bars and partial dependence plots for top features.

- [ ] T036 [US3] Implement scatter plot generation in `code/visualization/scatter.py` with % CI error bars (requires T031b predictions).
- [ ] T037 [US3] Implement partial dependence plot generation in `code/visualization/pdp.py` for top-ranked SHAP features (requires T030 output).
- [ ] T038 [US3] Save all plots to `data/outputs/` with correct labels and units.
- [ ] T035 [US3] **Generate Paper Draft**: Create `docs/paper_draft.md` containing the methodology, results, and discussion sections. **CRITICAL**: **Depends on T031b, T036, T037, T038, T029c, T054, T031c**. (Added dependencies on Sensitivity, VIF, and Report).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Documentation updates in `README.md` and `docs/`
- [ ] T041 Code cleanup and refactoring
- [ ] T042 Performance optimization to ensure <6h runtime on free-tier
- [ ] T043 [P] Additional unit tests in `tests/unit/`
- [ ] T044 Run quickstart.md validation

---

## Revision Tasks (Addressing Analysis Findings)

**Purpose**: New tasks added to resolve specific issues identified in the analysis phase.

### Revision: Data Ingestion Robustness

- [ ] T050 [US1] **Implement Strict Data Fetching**: Modify `code/ingestion/aggregator.py` to remove ALL `try/except` blocks that fall back to synthetic data generation. **CRITICAL**: If a real data fetch fails (network error, 404, API limit), the script MUST raise a `DataFetchError` for that specific source and skip it. If *any* source succeeds but the total aggregated N < 50, the pipeline must proceed with a reduced N flag. If *no* sources succeed (total N = 0), halt execution with a fatal error. **Rationale**: Prevents silent fabrication of data which triggers the fabrication gate rejection, while allowing the 'reduced N' path for N > 0. **Depends on T012a**.
- [ ] T051 [US1] **Add Streaming Support for Large Datasets**: Update `code/ingestion/aggregator.py` to support `streaming=True` when loading datasets from HuggingFace or large CSV sources. **CRITICAL**: If a dataset exceeds available RAM capacity, the loader must iterate in chunks using `datasets.load_dataset(..., streaming=True)` and accumulate statistics online, never loading the full dataset into memory. **Rationale**: Ensures real data can be processed within CI constraints without resorting to toy datasets. **Depends on T012a**.
- [ ] T052 [US1] **Verify Real Data Source Adoption**: If the execution stage provides a "VERIFIED REAL DATA SOURCE" block, update `code/ingestion/aggregator.py` to exclusively use the provided package/recipe and remove any hand-rolled URL fetchers or guessed IDs. **CRITICAL**: This task ensures alignment with the execution stage's verified sources. **Depends on T012a**.

### Revision: Model Training & Diagnostics

- [ ] T053 [US2] **Explicitly Document CLR vs. Physical Descriptors**: Update `code/features/descriptor_engine.py` to add inline comments clarifying that CLR transforms are applied to raw percentages to address closure, while physical descriptors (atomic mass, etc.) are computed using the RAW percentages as weights. **CRITICAL**: Prevents confusion about the dual usage of composition data. **Depends on T023a, T023b**.
- [ ] T054 [US2] **Enhance VIF Reporting**: Extend `code/features/collinearity.py` to output a detailed report `data/processed/vif_report.yaml` listing all predictors, their VIF scores, and a boolean `is_collinear` flag for VIF ≥ 5. **CRITICAL**: Ensures compliance with FR-013 and SC-006 by providing explicit collinearity diagnostics. **Depends on T024**.
- [ ] T055 [US2] **Add Sensitivity Analysis Visualization**: Update `code/evaluation/sensitivity.py` to ensure `data/outputs/sensitivity_plot.png` clearly labels the x-axis as "R² Threshold" and y-axis as "Fraction of Bootstrap Samples Exceeding Threshold". **CRITICAL**: Ensures the visualization meets SC-005 requirements for interpretability. **Depends on T029c**.

### Revision: Documentation & Reporting

- [ ] T056 [US3] **Standardize Associational Framing**: Update `docs/paper_draft.md` and `data/processed/report.yaml` (produced by T031c) to include a prominent "Limitations" section explicitly stating that findings are associational, not causal, due to the observational nature of the data. **CRITICAL**: Ensures compliance with FR-007 and prevents causal over-interpretation. **Depends on T031c, T035**.
- [ ] T057 [US3] **Add Power Limitation Warning to Final Report**: If `data/processed/.ingestion_status.json` indicates N < 100, update `docs/paper_draft.md` and `data/processed/report.yaml` to include a specific "Statistical Power Limitation" warning referencing the exact N value. **CRITICAL**: Ensures compliance with FR-001 and SC-004 by transparently reporting reduced statistical power. **Depends on T014, T035**.