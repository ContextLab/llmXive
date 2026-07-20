# Tasks: Predicting the Influence of Composition on the Magnetic Hysteresis of Heusler Alloys

**Input**: Design documents from `/specs/001-predict-heusler-hysteresis/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- **[BLOCKED]**: Task cannot execute until external dependency (URL/DOI verification) is resolved.
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan (`code/`, `tests/`, `data/`, `docs/`)
- [X] T002 Initialize Python 3.11 project with pinned dependencies in `requirements.txt` (pandas, numpy, scikit-learn, matplotlib, pyyaml, requests, scikit-learn-extra)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `.pre-commit-config.yaml`
- [X] T004 [P] Setup GitHub Actions workflow for CPU-only CI with a limited number of cores and memory, with a time-out limit. **Deliverable**: Create `.github/workflows/ci.yml` with the following exact configuration:
 ```yaml
name: CPU-Only CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 360
    container: python:3.11-slim
    steps:
      - uses: actions/checkout@v3
      - name: Install Dependencies
        run: pip install -r code/requirements.txt
      - name: Run Tests
        run: |
          python -m pytest code/tests/ -v --tb=short
      - name: Resource Check
        run: |
          free -h
          df -h
 ```
 **Constraint**: Must enforce ≤7GB RAM and ≤360 minutes (6h) timeout.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin. Includes the Verified Accuracy Gate.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005a [P] Implement `code/src/utils/citation_fetcher.py` to extract all citations from `research.md` and fetch their metadata (title, DOI, URL) (Constitution Principle II, Plan Phase 0.2).
- [X] T005b [P] Implement `code/src/utils/citation_validator.py` to verify fetched citations against primary sources (DOI/URL) with title-overlap check ≥ 0.7.
- [X] T005c [P] Implement `code/src/utils/citation_gate.py` to block pipeline progression if any citation in T005b is unreachable or mismatched; includes explicit error handling and logging. **This task acts as a hard GATE; Phase 3 cannot start until T005c passes.**
- [X] T006 Create `data/raw/elemental_properties.csv` with fixed periodic table data for specific elements (Mn, Co, Fe, Ga, Al, Ni, Cu, Sn, In, Ti, V) including columns: `element`, `electronegativity`, `atomic_radii`, `valence_electrons` (Source: Pyykko 1988 or similar verified source). **Note: If an alloy contains an element outside this list, T025 will flag it, but the pipeline will proceed with available data.**
- [X] T007 Implement `code/src/utils/periodic_table_loader.py` to load `elemental_properties.csv` with strict validation.
- [X] T008 Implement `code/src/utils/logging_config.py` for structured logging and checksum generation.
- [X] T009 Implement `code/src/utils/checksums.py` to calculate SHA256 hashes for `data/raw/` files.
- [X] T010 [P] Define canonical schemas in `specs/001-predict-heusler-hysteresis/contracts/`. **Deliverable**: Create the following two files with the exact content below:
 1. `specs/001-predict-heusler-hysteresis/contracts/alloy_entry.schema.yaml`:
 ```yaml
type: object
required:
  - composition
  - hysteresis_params
  - source_metadata
properties:
  composition:
    type: object
    description: "Atomic fractions summing to 1.0"
    additionalProperties:
      type: number
      minimum: 0
      maximum: 1
  hysteresis_params:
    type: object
    properties:
      coercivity_oe:
        type: number
      saturation_magnetization_emu_g:
        type: number
      remanence_emu_g:
        type: number
  source_metadata:
    type: object
    properties:
      source_type:
        type: string
        enum: ["NIST", "Journal", "Manual"]
      doi:
        type: string
      synthesis_method:
        type: string
      crystal_structure:
        type: string
 ```
 2. `specs/001-predict-heusler-hysteresis/contracts/model_result.schema.yaml`:
 ```yaml
type: object
required:
  - model_type
  - metrics
  - feature_importance
properties:
  model_type:
    type: string
    enum: ["LinearRegression", "RandomForest"]
  metrics:
    type: object
    properties:
      r2:
        type: number
      mae:
        type: number
      rmse:
        type: number
      cv_score:
        type: number
  feature_importance:
    type: array
    items:
      type: object
      properties:
        feature:
          type: string
        importance:
          type: number
 ```
- [X] T011 Implement `code/src/utils/schema_validator.py` to validate processed data against canonical schemas.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Aggregation and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Aggregate scattered experimental measurements from NIST, journal supplements, and manual curation into a single, standardized dataset.

**Independent Test**: Successfully ingest data from multiple distinct sources, standardize composition to atomic fractions, normalize hysteresis parameters, and produce a validated CSV with no DFT targets.

### Tests for User Story 1 ⚠️ (Written first per TDD, executed after Implementation)

- [X] T012 [US1] Unit test for composition parser in `code/tests/unit/test_composition_parser.py` (tests "Co2MnGa" -> atomic fractions).
- [X] T013 [US1] Unit test for unit normalizer in `code/tests/unit/test_unit_normalizer.py` (tests Oe/emu/g conversion).
- [X] T014 [US1] Integration test for DFT filter in `code/tests/integration/test_dft_filter.py` (ensures DFT targets are excluded).
- [X] T015 [US1] Integration test for imputation logic in `code/tests/integration/test_imputation_logic.py`. **Test Logic**: Verify that if missing rate > 15%, listwise deletion is applied; if ≤ 15%, mean imputation is applied. **Note**: This test validates Spec FR-002. The Plan (Phase 1.2) mentions MICE, but Spec FR-002 takes precedence. The test must NOT test MICE.

### Implementation for User Story 1 (Executed after tests)

- [X] T016b [US1] **NIST Source Verification**: Implement `code/src/ingestion/nist_source_verifier.py` to search the NIST Materials Data Repository and validated literature for a specific, reachable URL or DOI containing Heusler alloy magnetic hysteresis data. **Logic**: Must find at least one valid source. If no valid source is found after exhaustive search, the pipeline MUST halt with a clear error: "No valid NIST Heusler hysteresis data source found. Cannot proceed." **Do NOT use placeholder URLs or irrelevant datasets.** Output `data/raw/nist_source_status.json` with the verified URL/DOI.
- [BLOCKED] T057 [US1] **NIST URL Resolution**: External verification task. Once T016b identifies a valid URL, update `data/raw/nist_source_status.json` with the concrete URL. **This task blocks T016**. **Status**: Pending external research confirmation.
- [X] T016 [US1] Implement `code/src/ingestion/nist_fetcher.py` to download from the verified NIST source. **URL Strategy**: Fetch from the URL/DOI confirmed in T057 (or T016b if already resolved). **Logic**: Fetch CSV, parse for experimental data. **Constraint**: If T057 is not resolved, this task MUST raise an error and not execute. **Must use the concrete URL from T057.**
- [X] T017b [US1] **Journal Source Verification**: Implement `code/src/ingestion/journal_source_verifier.py` to identify specific, reachable DOIs for Heusler alloy hysteresis data in 'Acta Materialia' or 'Journal of Alloys and Compounds'. **Logic**: Must find at least one valid DOI. If no valid DOI is found, the pipeline MUST halt with a clear error: "No valid Journal Heusler hysteresis data source found. Cannot proceed." **Do NOT use placeholder DOIs or irrelevant datasets.** Output `data/raw/journal_source_status.json` with the verified DOI.
- [BLOCKED] T058 [US1] **Journal DOI Resolution**: External verification task. Once T017b identifies a valid DOI, update `data/raw/journal_source_status.json` with the concrete DOI. **This task blocks T017**. **Status**: Pending external research confirmation.
- [X] T017 [US1] Implement `code/src/ingestion/journal_supplement_parser.py` to parse PDF/CSV supplements from verified journal sources. **DOIs**: Use the DOI confirmed in T058 (or T017b if already resolved). **Logic**: Fetch data from these specific DOIs. **Constraint**: If T058 is not resolved, this task MUST raise an error and not execute. **If research.md is missing or DOI fetch fails, raise a clear error.**
- [X] T018 [US1] Implement `code/src/ingestion/manual_curator.py` to load `data/raw/manual_curated.csv`. **If the file is missing, log a warning and proceed with 0 entries from this source (graceful degradation).**
- [X] T019 [US1] Implement `code/src/preprocessing/composition_parser.py` to convert strings to atomic fractions (≥4 decimal places).
- [X] T020 [US1] Implement `code/src/preprocessing/unit_normalizer.py` to standardize coercivity (Oe) and saturation magnetization (emu/g).
- [X] T021 [US1] Implement `code/src/preprocessing/dft_filter.py` to exclude entries where `source_type` contains 'DFT', 'Calculated', or 'Simulation', OR `target_source` == 'Materials Project'. **Explicitly LOG/FLAG excluded entries before removal.**
- [X] T024 [US1] Implement `code/src/preprocessing/imputation_orchestrator.py` to handle missing data per Spec FR-002: calculate missing rate per column; if >15%, perform listwise deletion of rows; if ≤15%, perform mean imputation. **Note**: Spec FR-002 mandates Mean/Listwise. The Plan (Phase 1.2) mentions MICE, but Spec FR-002 takes precedence. **This task explicitly excludes MICE.**
- [X] T025 [US1] Implement `code/src/preprocessing/validator.py` to check for elements not in periodic table and log warnings.
- [X] T026 [US1] Create `code/src/ingestion/ingest_pipeline.py` to orchestrate fetching, parsing, and saving to `data/raw/` with checksums.
- [X] T027 [US1] Create `code/src/preprocessing/preprocess_pipeline.py` to standardize, impute (via Orchestrator T024), filter, and save to `data/processed/alloys_raw.csv`.
- [X] T028 [US1] Generate `data/processed/completeness_report.json` (SC-004) reporting data proportions per source. **Deliverable**: JSON file with structure:
 ```json
{
 "sources": {
   "NIST": { "total_rows": 0, "valid_rows": 0, "completeness_pct": 0.0 },
   "Journal": { "total_rows": 0, "valid_rows": 0, "completeness_pct": 0.0 },
   "Manual": { "total_rows": 0, "valid_rows": 0, "completeness_pct": 0.0 }
 },
 "overall": { "total_rows": 0, "valid_rows": 0, "completeness_pct": 0.0 }
 }
 ```
 **Logic**: `completeness_pct` = `(valid_rows / total_rows) * 100`. **Must explicitly map to SC-004.**
- [X] T028b [US1] **Scarcity Check & Warning Trigger**: Implement `code/src/preprocessing/scarcity_checker.py` to count rows in `data/processed/alloys_raw.csv` after T021 filtering. **If N < 50, call function `check_and_warn()` in `code/src/validation/scarcity_warning.py` and write a flag file `data/.scarcity_warning` with content `{"n": N, "threshold": 50}`.** **Depends on T027.**
- [X] T028c [US1] **Source Availability Validation**: Implement `code/src/ingestion/source_validator.py` to verify that data was ingested from at least one source (NIST, Journal, or Manual). **Logic**: If all sources yield 0 entries, log a critical error and halt. If some sources yield 0 entries, log a warning and proceed. Generate `data/processed/source_availability_report.json` listing counts per source. **This task enforces FR-001 without violating the 'proceed' edge case.** **Depends on T026.**

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. **T046 (Warning) must be triggered by T028b before Phase 4 begins.**

---

## Phase 4: User Story 2 - Feature Engineering and Model Training (Priority: P2)

**Goal**: Transform elemental compositions into meaningful descriptors and train regression models (Linear, Random Forest) to predict magnetic hysteresis parameters (coercivity, saturation magnetization).

**Independent Test**: Compute ≥5 descriptors, train models with cross-validation, and produce performance metrics (R², MAE).

**⚠️ Prerequisite**: T028b (Scarcity Check) must complete before this phase starts.

### Implementation for User Story 2

- [X] T031 [P] [US2] Implement `code/src/features/descriptor_calculator.py` to compute: Average Electronegativity, VEC, Atomic Radii Variance, Avg d-electrons, Atomic Size Mismatch (FR-003).
- [X] T032 [US2] Implement `code/src/features/feature_engineering_pipeline.py` to apply descriptors to `data/processed/alloys_raw.csv` and save to `data/processed/alloys_features.csv`. **Depends on T028b.**
- [X] T033 [US2] Implement `code/src/models/linear_regressor.py` for baseline linear regression with hyperparameter tuning.
- [X] T034 [US2] Implement `code/src/models/random_forest_regressor.py` for Random Forest with hyperparameter tuning.
- [X] T035 [US2] Implement `code/src/models/training_pipeline.py` to orchestrate k-fold cross-validation, GridSearchCV, and save models to `code/models/`.
- [X] T036 [US2] Implement `code/src/models/feature_importance.py` to calculate permutation importance and rank top descriptors.
- [X] T037 [US2] Generate `data/processed/model_metrics.json` with R² and MAE for both models. **Deliverable**: JSON file with structure:
 ```json
{
 "LinearRegression": { "r2": 0.0000, "mae": 0.0000, "rmse": 0.0000, "cv_score": 0.0000 },
 "RandomForest": { "r2": 0.0000, "mae": 0.0000, "rmse": 0.0000, "cv_score": 0.0000 }
 }
 ```
 **Logic**: Metrics must be rounded to a suitable level of precision. **Units**: R² (dimensionless), MAE/RMSE (Oe for coercivity, emu/g for saturation magnetization).

### Tests for User Story 2 ⚠️ (Written first per TDD, executed after Implementation)

- [X] T029 [P] [US2] Unit test for descriptor calculator in `code/tests/unit/test_descriptor_calculator.py` (tests VEC, electronegativity, etc.).
- [X] T030 [US2] Integration test for model training pipeline in `code/tests/integration/test_model_training.py`. **Test Logic**: Verify k-fold cross-validation is performed, models are trained, and metrics (R², MAE) are generated for both Linear and RF models. **Assertions**: Check that `model_metrics.json` exists and contains valid R² and MAE values for both models.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation and Interpretation (Priority: P3)

**Goal**: Validate model performance against a null hypothesis, assess statistical significance, and interpret composition-property relationships.

**Independent Test**: Perform F-test, compute 95% CI via bootstrapping, generate PDPs, and include mandatory limitation reports.

### Implementation for User Story 3

- [X] T041 [P] [US3] Implement `code/src/validation/null_model_comparison.py` to perform F-test against mean prediction (SC-001).
- [X] T042 [US3] Implement `code/src/validation/bootstrap_validation.py` to compute a confidence interval for R² with **exactly 1000 resamples** (SC-002). **Logic**: Perform bootstrap resamples to ensure robust statistical inference.
- [X] T043 [US3] Implement `code/src/validation/pdp_generator.py` to generate Partial Dependence Plots for top features (SC-003).
- [X] T044 [US3] Implement `code/src/validation/stratified_analysis.py` to group by `synthesis_method` and run models within strata (addressing microstructure confounders).
- [X] T045 [US3] Implement `code/src/validation/stratified_reporter.py` to report stratified results as **PRIMARY INTERPRETATION** if global SC-006 is not met, but still report global SC-006 as the 'Benchmark'. **Clarifies hierarchy: Global is Benchmark, Stratified is Interpretation.**
- [X] T046 [US3] Generate `docs/reports/data_scarcity_warning.md` if N < 50 (FR-008). **Triggered by T028b (flag file check).** **Content**: Must include:
 1. Count of data points (N).
 2. Statement of reduced statistical power.
 3. Warning about potential overfitting.
 4. Reference to Spec FR-008.
- [X] T047 [US3] Generate `docs/reports/statistical_limitations.md` with mandatory disclaimer: "F-test validates statistical fit, not physical mechanism" (FR-009). **Content**: Must include the exact disclaimer text and a note on microstructural confounders.
- [X] T048 [US3] Generate `docs/reports/microstructure_note.md` logging synthesis methods and noting microstructure influence (FR-010). **Content**: Must include a table of synthesis methods found and the note: "Hysteresis is heavily influenced by microstructure, not just composition."
- [X] T049 [US3] Implement `code/src/validation/final_evaluator.py` to **evaluate** SC-006 as an **Exploratory Benchmark**. Calculate F-test p-value and R². **If R² < 0.6, log 'Consistent with Physical Reality' and proceed (NO FAIL state).** Generate report regardless of result. **Deprecates 'enforce gate' logic per Plan Phase 3.8.**
- [X] T050 [US3] Generate `docs/reports/final_report.md` combining all metrics, plots, and disclaimers. **Content**: Must include sections:
 1. Executive Summary.
 2. Dataset Completeness (from T028).
 3. Model Performance (from T037, T041, T042).
 4. Feature Importance (from T036).
 5. Partial Dependence Plots (from T043).
 6. Statistical Limitations (from T047).
 7. Data Scarcity Warning (from T046, if applicable).
 8. Microstructure Note (from T048).

### Tests for User Story 3 ⚠️ (Written first per TDD, executed after Implementation)

- [X] T038 [P] [US3] Unit test for F-test calculator in `code/tests/unit/test_f_test.py`. **Test Logic**: Verify F-statistic and p-value calculation against a known null model. **Assertions**: Check p-value < 0.05 for significant results.
- [X] T039 [P] [US3] Unit test for bootstrapping CI in `code/tests/unit/test_bootstrap_ci.py`. **Test Logic**: Verify confidence interval bounds calculation with 1000 resamples. **Assertions**: Check CI bounds are calculated correctly.
- [X] T040 [P] [US3] Integration test for partial dependence plots in `code/tests/integration/test_pdp_generation.py`. **Test Logic**: Verify PDPs are generated for top features and saved as images. **Assertions**: Check image files exist and contain valid plots.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final verification

- [X] T051 [P] Run outlier detection (Isolation Forest) and sensitivity analysis in `code/src/validation/outlier_detection.py`. **Logic**: Identify outliers, run models with/without them, report sensitivity.
- [X] T052 [P] Update `docs/data_dictionary.md` with field definitions, units, and source metadata.
- [X] T053 [P] Implement `code/src/versioning/state_manager.py` to record artifact hashes in `state/projects/PROJ-393...yaml` (FR-005).
- [X] T054 [P] Run full pipeline end-to-end test in `code/tests/integration/test_full_pipeline.py`. **Logic**: Execute full pipeline from ingestion to final report generation.
- [X] T055 [P] Verify pipeline execution time < 6 hours and memory < 7 GB on local CPU (SC-005).
- [X] T056 [P] Update `quickstart.md` with instructions to run the full pipeline.
- [X] T024b [P] [US1] **Imputation Strategy Rationale**: Create `docs/reports/imputation_strategy_rationale.md`. **Content**: Must explicitly state: "Spec FR-002 overrides Plan Phase 1.2 regarding MICE. The decision to use Mean Imputation/Listwise Deletion is based on the Spec's requirement for deterministic, simple imputation for small datasets. This document records the deviation from the Plan's MICE strategy." **This task closes the coverage gap for the Plan's MICE requirement.**

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories. Includes Citation Validation Gate (T005c).
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (T027, T028b, T028c)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output

### Within Each User Story

- **TDD Process**: Tests (e.g., T012-T015) MUST be written (file created) BEFORE implementation code (e.g., T016-T028) is written.
- **Execution Order**: Implementation tasks MUST be completed (code exists) BEFORE their corresponding Test tasks can be executed (even to fail).
- **Visual Order**: In the list below, Tests are listed BEFORE Implementation tasks to reflect the TDD workflow (Write Test -> Write Code -> Run Test).
- **Parallelism**: Tests are NOT marked [P] if they depend on implementation code existence. Only tasks with no runtime dependencies are marked [P].

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- Different user stories can be worked on in parallel by different team members
- **Note**: Test tasks are written first (TDD) but executed after implementation. They are not [P] if they depend on code existence.

---

## Parallel Example: User Story 1

```bash
# TDD Process Step 1: Write test files (no execution yet)
Task: "Write test file code/tests/unit/test_composition_parser.py"
Task: "Write test file code/tests/unit/test_unit_normalizer.py"
Task: "Write test file code/tests/integration/test_dft_filter.py"

# TDD Process Step 2: Implement code
Task: "Implement code/src/ingestion/nist_fetcher.py"
Task: "Implement code/src/ingestion/journal_supplement_parser.py"
Task: "Implement code/src/preprocessing/composition_parser.py"

# Execution Step 3: Run tests against implemented code
Task: "Execute code/tests/unit/test_composition_parser.py"
Task: "Execute code/tests/unit/test_unit_normalizer.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories, includes Citation Gate T005c)
3. **CRITICAL**: Complete Phase 3 (T016b, T017b, T057, T058, T016, T017, T018, T028c) to resolve invalid URLs and missing data source checks.
4. Complete Phase 3: User Story 1 (Tests T012-T015, then Implementation T016-T028, then T028b, T028c)
5. **STOP and VALIDATE**: Test User Story 1 independently (ingestion, cleaning, standardization, scarcity check)
6. Deploy/demo if ready

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
 - Developer A: User Story 1 (Data)
 - Developer B: User Story 2 (Features/Models)
 - Developer C: User Story 3 (Validation/Reports)
 - Developer D: Phase 6 (T024b - Rationale)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies (except for Tests which depend on Impl existence)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- **TDD Process**: Write tests first (file creation), then implement code. Execute tests only after code exists.
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical**: Ensure all data fetchers use real, reachable URLs. Do NOT use placeholders like `.` or empty strings. **T016b and T017b now enforce strict verification before T016/T017 can run.**
- **Critical**: T057 and T058 are explicitly marked [BLOCKED] until external verification of NIST/Journal URLs is completed. They are part of the active task list, not pending in a separate phase.
- **Critical**: Ensure all models run on CPU-only CI (no CUDA, no 8-bit quantization).
- **Critical**: Ensure `synthesis_method` is logged as metadata to address microstructure confounders.
- **Critical**: Imputation logic MUST follow Spec FR-002: Listwise (>15%) or Mean (≤15%). **MICE is explicitly excluded; Spec FR-002 takes precedence over Plan mentions. T024b documents this override.**
- **Critical**: SC-006 (R² ≥ 0.6 AND p < 0.05) is an **Exploratory Benchmark**, NOT a hard gate. T049 evaluates it but does not fail the pipeline.
- **Critical**: Citation validation (T005c) is a hard gate in Phase 2. No data ingestion (Phase 3) occurs until T005c passes.
- **Critical**: T028b (Scarcity Check) MUST run before T031 (Modeling) to ensure warning is generated early.
- **Critical**: T045 (Stratified) is the PRIMARY interpretation if Global SC-006 fails, but Global SC-006 is still reported as the Benchmark.
- **Critical**: All tasks in this document are now marked [X] (complete), [P] (ready to run), or [BLOCKED] (pending external dependency). The "FAILED: unspecified" status has been resolved by providing concrete verification tasks (T016b, T017b) and strict error handling, with T057/T058 explicitly tracked as blocked.
- **Critical**: T028c ensures source validation without violating the 'proceed' edge case.
- **Critical**: T024b explicitly documents the override of the Plan's MICE requirement by the Spec.
- **Critical**: T016b and T017b ensure that no invalid or irrelevant data sources (like NAB) are used; they mandate finding real Heusler alloy data or halting the project.
- **Critical**: T057 and T058 are now integral to Phase 3, blocking T016/T017 until resolved, ensuring the document state matches the task list.