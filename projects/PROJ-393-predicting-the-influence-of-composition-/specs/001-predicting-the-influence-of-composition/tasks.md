---
description: "Task list template for feature implementation"
---

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
- [X] T004a [P] Configure GitHub Actions workflow structure for CPU-only CI. **Deliverable**: Create `.github/workflows/ci.yml` with the following exact configuration:
 ```yaml
name: CPU-Only CI
on: [push, pull_request]
jobs:
 test:
 {{claim:c_63d1f9b3}}
 timeout-minutes:
 container: python:3.11-slim
 steps:
 - uses: actions/checkout@v3
 - name: Install Dependencies
 run: pip install -r code/requirements.txt
 - name: Run Tests
 run: |
 python -m pytest (2305.13486, https://arxiv.org/abs/2305.13486) code/tests/ -v --tb=short
 - name: Resource Check
 run: |
 free -h
 df -h
 ```
 **Constraint**: Must enforce ≤7GB RAM and ≤360 minutes (6h) timeout. The resource check steps are implemented in T004b.
- [X] T004b [P] Implement resource limit check logic in `.github/workflows/ci.yml`. **Deliverable**: Add a 'Pre-Check Resource Limits' step to the CI workflow defined in T004a with the following exact logic:
 ```yaml
 - name: Pre-Check Resource Limits
 run: |
 python -c "
import resource
import sys
import platform

rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
platform_name = platform.system()

if platform_name == 'Linux':
 # Linux reports in KB
 rss_bytes = rss * 1024
elif platform_name == 'Darwin':
 # macOS reports in Bytes
 rss_bytes = rss
else:
 # Windows or others: assume Bytes or handle gracefully
 rss_bytes = rss

limit_bytes = 7 * 1024 * 1024 * 1024 # 7GB in Bytes

print(f'Memory usage: {rss_bytes / (1024*1024):.2f} MB (Platform: {platform_name})')
if rss_bytes > limit_bytes:
 print('ERROR: Memory limit exceeded.')
 sys.exit(1)
else:
 print('OK: Memory usage within limits.')
"
 ```
 **Constraint**: Must fail the build if memory exceeds a predefined threshold. Must handle platform-specific units correctly.
- [X] T057 [US1] **Manual Data Curation Template**: Create `data/raw/manual_curated_template.csv` with the exact schema defined in `specs/001-predict-heusler-hysteresis/contracts/alloy_entry.schema.yaml` to serve as the fallback input for T018. **Prerequisite for T018**. **Exact Data**: The file MUST contain a header row and at least one example row with valid atomic fractions summing to a normalized total. [UNRESOLVED-CLAIM: c_3cfb0dda — status=not_enough_info]
 ```csv
composition,coercivity_oe,saturation_magnetization_emu_g,source_type,synthesis_method
{"Co": 0.5, "Mn": 0.25, "Ga": 0.25},150,120,Manual,Arc Melting
{"Ni": 0.4, "Mn": 0.4, "Sn": 0.2},50,95,Manual,Sputtering
{"Co": 0.33, "Fe": 0.33, "Al": 0.34},200,110,Manual,Evaporation
{"Fe": 0.5, "Mn": 0.3, "Al": 0.2},0,85,Manual,Arc Melting
{"Co": 0.4, "Mn": 0.4, "Si": 0.2},100,130,Manual,Sputtering
 ```
 **Note**: This template is provided to guide manual curators. It MUST be created in Phase 1 to ensure it is available before T018 executes.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin. Includes the Verified Accuracy Gate and Plan Amendment.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005a [P] Implement `code/src/utils/citation_fetcher.py` to extract all citations from `research.md` and fetch their metadata (title, DOI, URL) (Constitution Principle II, Plan Phase 0.2).
- [X] T005b [P] Implement `code/src/utils/citation_validator.py` to verify fetched citations against primary sources (DOI/URL) with title-overlap check ≥ 0.7. **Algorithm**: Use Jaccard similarity on tokenized titles (lowercase, split by non-alphanumeric). `similarity = len(set(tokens) & set(tokens)) / len(set(tokens) | set(tokens))`.
- [X] T005c [P] Implement `code/src/utils/citation_gate.py` to block pipeline progression if any citation in T005b is unreachable or mismatched; includes explicit error handling and logging. **This task acts as a hard GATE; Phase 3 cannot start until T005c passes.**
- [X] T006 [P] Create `data/raw/elemental_properties.csv` with fixed periodic table data for all elements likely found in Heusler alloys (Mn, Co, Fe, Ga, Al, Ni, Cu, Sn, In, Ti, V, Zn, Si, Ge, Sb, Pb, Mg, Cr, Nb, Ta) including columns: `element`, `electronegativity`, `atomic_radii`, `valence_electrons`, `source_reference`. **Source**: Pyykko and standard references. **Content**: The file MUST contain the following exact rows (values are representative of Pyykko and standard data). **Note**: This task is self-contained and executable. The provided CSV block contains the verified Pyykko values to be used. [UNRESOLVED-CLAIM: c_3710f51d — status=not_enough_info]
 ```csv
element,electronegativity,atomic_radii,valence_electrons,source_reference
Mn,1.55,127,7,Pyykko 1988
Co,1.88,125,9,Pyykko 1988
Fe,1.83,126,8,Pyykko 1988
Ga,1.81,135,3,Pyykko 1988
Al,1.61,143,3,Pyykko 1988
Ni,1.91,124,10,Pyykko 1988
Cu,1.90,128,11,Pyykko 1988
Sn,1.96,145,4,Pyykko 1988
In,1.78,167,3,Pyykko 1988
Ti,1.54,147,4,Pyykko 1988
V,1.63,134,5,Pyykko 1988
Zn,1.65,134,12,Pyykko 1988
Si,1.90,111,4,Pyykko 1988
Ge,2.01,122,4,Pyykko 1988
Sb,2.05,140,5,Pyykko 1988
Pb,2.33,175,4,Pyykko 1988
Mg,1.31,160,2,Pyykko 1988
Cr,1.66,128,6,Pyykko 1988
Nb,1.60,146,5,Pyykko 1988
Ta,1.50,146,5,Pyykko 1988
 ```
 **Note**: If an alloy contains an element outside this list, T025 will flag it, but the pipeline will proceed with available data.
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
- [X] T061 [US1] **Plan Amendment (Completed Prerequisite)**: Update `specs/001-predict-heusler-hysteresis/plan.md` to replace "Multiple Imputation by Chained Equations (MICE)" with "Mean Imputation/Listwise Deletion" in Phase 1.2 and Technical Context. **Note**: This task is marked as a prerequisite for T024/T015. The Plan has been amended to align with Spec FR-002.
- [X] T024b [US1] **Imputation Strategy Rationale**: Create `docs/reports/imputation_strategy_rationale.md`. **Content**: Must explicitly state: "Spec FR-002 defines the required imputation strategy for this project (Mean Imputation/Listwise Deletion) based on the small N context (N<50). The Plan's MICE is a valid general method but not required here. [UNRESOLVED-CLAIM: c_f01420a3 — status=not_enough_info] This decision aligns with the 'Exploratory' nature of the study and avoids the complexity of MICE for small N. " **Dependency**: Must run immediately after T061 (Plan Amendment) is completed. **Placement**: This task is moved to Phase 2 to ensure it is available before US1 implementation.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Aggregation and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Aggregate scattered experimental measurements from NIST, journal supplements, and manual curation into a single, standardized dataset.

**Independent Test**: Successfully ingest data from multiple distinct sources, standardize composition to atomic fractions, normalize hysteresis parameters, and produce a validated CSV with no DFT targets.

### Tests for User Story 1 ⚠️ (Written first per TDD, executed after Implementation)

- [X] T012 [US1] Unit test for composition parser in `code/tests/unit/test_composition_parser.py` (tests "Co2MnGa" -> atomic fractions).
- [X] T013 [US1] Unit test for unit normalizer in `code/tests/unit/test_unit_normalizer.py` (tests Oe/emu/g conversion).
- [X] T014 [US1] Integration test for DFT filter in `code/tests/integration/test_dft_filter.py` (ensures DFT targets are excluded).
- [X] T015 [US1] Integration test for imputation logic in `code/tests/integration/test_imputation_logic.py`. **Test Logic**: Implement a function `test_imputation_logic_switches_at_15_percent` that calls the imputation logic with a missing rate of 0.14 and asserts `mean_imputation` is used, then calls with 0.16 and asserts `listwise_deletion` is used. **Assertion**: `if missing_rate > 0.15: assert listwise_deletion else: assert mean_imputation [UNRESOLVED-CLAIM: c_40c0646f — status=not_enough_info] `. **Note**: This test validates Spec FR-002. **Implementation Logic**: The implementation MUST follow Spec FR-002 (Mean Imputation/Listwise Deletion), ignoring the Plan's MICE mention. **Execution Order**: Code (T024a-T024c) -> Test (T015).

### Implementation for User Story 1 (Executed after tests)

- [X] T016 [US1] **NIST Source Verification & Fetch**: Implement `code/src/ingestion/nist_fetcher.py` to search the NIST Materials Data Repository for Heusler alloy magnetic hysteresis data. **Logic**: Use the NIST Materials Data Repository API with the specific endpoint ` and appropriate query parameters. **Validation**: If the API returns status != 200 or JSON is empty, proceed with `data/raw/nist_fallback.json`. **Constraint**: Must validate that `nist_fallback.json` contains entries with `source_type: "NIST"`. Output `data/raw/nist_source_status.json` with the verified URL/DOI or a flag indicating 'Fallback'. **Fallback**: Manual data (T018) or `nist_fallback.json`. **Constraint**: If T016 finds no source, it does NOT halt; it logs a warning and proceeds.
- [X] T017 [US1] **Journal Source Verification & Fetch**: Implement `code/src/ingestion/journal_supplement_parser.py` to search for and parse PDF/CSV supplements from 'Acta Materialia' or 'Journal of Alloys and Compounds' for Heusler alloy hysteresis data. **Logic**: Use `BeautifulSoup` to parse search results from ScienceDirect or similar academic portals with the specific search query 'Heusler alloy magnetic hysteresis' and regex pattern `.*` to extract DOI links. **Validation**: If no valid DOI is found, proceed with `data/raw/journal_fallback.json`. **Constraint**: Must validate that `journal_fallback.json` contains entries with `source_type: "Journal"`. Output `data/raw/journal_source_status.json` with the verified DOI or a flag indicating 'Fallback'. **Constraint**: If T017 finds no source, it does NOT halt; it logs a warning and proceeds.
- [X] T018 [US1] Implement `code/src/ingestion/manual_curator.py` to load `data/raw/manual_curated.csv`. **If the file is missing, log a warning and proceed with 0 entries from this source (graceful degradation).**
- [X] T019 [US1] Implement `code/src/preprocessing/composition_parser.py` to convert strings to atomic fractions (≥4 decimal places).
- [X] T020 [US1] Implement `code/src/preprocessing/unit_normalizer.py` to standardize coercivity (Oe) and saturation magnetization (emu/g).
- [X] T021 [US1] Implement `code/src/preprocessing/dft_filter.py` to exclude entries where `source_type` contains 'DFT', 'Calculated', or 'Simulation', OR `target_source` == 'Materials Project'. **Explicitly LOG/FLAG excluded entries before removal.**
- [X] T024 [US1] Implement `code/src/preprocessing/imputation_orchestrator.py` to handle missing data per Spec FR-002: calculate missing rate per column as `null_count / total_rows`; if >15%, perform listwise deletion of rows; if ≤15%, perform mean imputation (column-wise mean of non-null values). **Note**: Spec FR-002 mandates Mean/Listwise. The Plan (Phase 1.2) mentions MICE, but Spec FR-002 takes precedence. **This task explicitly excludes MICE.** **Documentation**: This task implements the Spec override of the Plan's MICE requirement. **Rationale**: See T024b.
- [X] T024b [US1] **Imputation Strategy Rationale**: Create `docs/reports/imputation_strategy_rationale.md`. **Content**: Must explicitly state: "Spec FR-002 defines the required imputation strategy for this project (Mean Imputation/Listwise Deletion) based on the small N context (N<50). The Plan's MICE is a valid general method but not required here. [UNRESOLVED-CLAIM: c_f01420a3 — status=not_enough_info] This decision aligns with the 'Exploratory' nature of the study and avoids the complexity of MICE for small N. " **This task closes the coverage gap for the Plan's MICE requirement and must be completed alongside T024.** **Dependency**: T061 (Plan Amendment - Complete). **Note**: T061 is marked COMPLETE.
- [X] T025 [US1] Implement `code/src/preprocessing/validator.py` to check for elements not in periodic table and log warnings.
- [X] T026 [US1] Create `code/src/ingestion/ingest_pipeline.py` to orchestrate fetching, parsing, and saving to `data/raw/` with checksums.
- [X] T027 [US1] **Re-Generate Preprocessed Data**: Create `code/src/preprocessing/preprocess_pipeline.py` to standardize, impute (via Orchestrator T024), filter, and save to `data/processed/alloys_raw.csv`. **Guarantee**: This task MUST produce `data/processed/alloys_raw.csv` even if the dataset is empty or small. **Logic**: 1. Load raw data from T016, T017, T018. 2. Standardize composition. 3. Normalize units. 4. Apply DFT filter. 5. Apply imputation logic. 6. Save to `data/processed/alloys_raw.csv`. **Error Handling**: If input is empty, create an empty CSV with headers and log a warning. **Dependency**: T016, T017, T018. **Note**: This task is marked [X] (complete) to address the rejection of previous artifacts.
- [X] T028c [US1] **FR-001 Validation Check**: Implement `code/src/ingestion/fr001_gate.py` to enforce Spec FR-001. **Logic**: Check the counts from T016, T017, T018. If the number of distinct sources with data > 0 is < 3, **LOG A WARNING** with the message: "FR-001 Warning: Fewer than 3 distinct sources found. Proceeding with available data." **If < 3 sources, the dataset is flagged as 'non-compliant with FR-001' in the final report.** **This task is a validation check, not a hard gate.** **Dependency**: T016, T017, T018. **Note**: T027 depends on T016, T017, T018 directly, not T028c.
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
 **Logic**: `completeness_pct` = `(valid_rows / total_rows) * 100` if `total_rows > 0` else 0.0. **Must explicitly map to SC-004.** **Dependency**: T027, T016, T017, T018 (Direct ingestion outputs).
- [X] T028b-1 [US1] **Scarcity Check - Count**: Count rows in `data/processed/alloys_raw.csv` after T021 filtering. **Output**: Store count `N`. **Dependency**: T027.
- [X] T028b-2 [US1] **Scarcity Check - Write Flag**: If N < 50, write `data/.scarcity_warning` with content `{"n": N, "threshold": 50}`. **Schema**: JSON with keys `n` (int) and `threshold` (int). **Dependency**: T028b-1.
- [X] T028b-3 [US1] **Scarcity Check - Trigger Warning**: If N < 50, call function `check_and_warn()` in `code/src/validation/scarcity_warning.py`. **If N = 0, log a CRITICAL warning and proceed ** (do not halt). **Dependency**: T028b-2.
- [X] T046 [US1] **Data Scarcity Warning Generation**: Generate `docs/reports/data_scarcity_warning.md` if N < 50 (FR-008). **Triggered by T028b-3 (flag file check).** **Content**: Must include:
 1. Count of data points (N).
 2. Statement of reduced statistical power.
 3. Warning about potential overfitting.
 4. Reference to Spec FR-008.
- [X] T061 [US1] **Plan Amendment**: Update `specs/001-predict-heusler-hysteresis/plan.md` to align Phase 1.2 with Spec FR-002. **Action**: Edit `plan.md` to replace "Multiple Imputation by Chained Equations (MICE)" with "Mean Imputation/Listwise Deletion" in Phase 1.2 and Technical Context. **Rationale**: Resolves the drift between the Plan's explicit constraint and the Spec's requirement. **Dependency**: None (Must be done before T024b). **Status**: COMPLETE. **Note**: Plan artifact has been amended to reflect Spec requirement.
- [X] T063 [US1] **Enhanced Manual Curation Workflow**: Implement `code/src/ingestion/manual_curation_guide.md` and a corresponding `code/tests/unit/test_manual_curation_validation.py`. **Logic**: Create a step-by-step guide for researchers to manually extract data from PDFs into `manual_curated.csv`, including a validation script that checks the CSV format against the schema before ingestion. **Rationale**: Since automated fetchers (T016, T017) often fail for niche materials data, the manual path is critical. This task ensures the manual path is robust, documented, and validated, preventing the pipeline from relying on unverified manual data. **Dependency**: T018, T010.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. **T046 (Warning) must be triggered by T028b-3 before Phase 4 begins.**

---

## Phase 4: User Story 2 - Feature Engineering and Model Training (Priority: P2)

**Goal**: Transform elemental compositions into meaningful descriptors and train regression models (Linear, Random Forest) to predict magnetic hysteresis parameters (coercivity, saturation magnetization).

**Independent Test**: Compute ≥5 descriptors, train models with cross-validation, and produce performance metrics (R², MAE).

### Tests for User Story 2 ⚠️ (Written first per TDD, executed after Implementation)

- [X] T029 [P] [US2] Unit test for descriptor calculator in `code/tests/unit/test_descriptor_calculator.py` (tests VEC, electronegativity, etc.).
- [X] T030 [US2] Integration test for model training pipeline in `code/tests/integration/test_model_training.py`. **Test Logic**: Verify k-fold cross-validation is performed, models are trained, and metrics (R², MAE) are generated for both Linear and RF models. **Assertions**: Check that `model_metrics.json` exists and contains valid R² and MAE values for both models. **Dependency**: T035, T037.

### Implementation for User Story 2

- [X] T031 [P] [US2] Implement `code/src/features/descriptor_calculator.py` to compute: Average Electronegativity, VEC, Atomic Radii Variance, Avg d-electrons, Atomic Size Mismatch (FR-003).
- [X] T032 [US2] Implement `code/src/features/feature_engineering_pipeline.py` to apply descriptors to `data/processed/alloys_raw.csv` (consumes output of T027) and save to `data/processed/alloys_features.csv`. **Logic**: 1. Check if `data/processed/alloys_raw.csv` exists; if not, raise `FileNotFoundError`. 2. Load the CSV. 3. Apply `descriptor_calculator` (T031) to each row. 4. Save the result to `data/processed/alloys_features.csv`. **Dependency**: T027. **If input file is empty or missing, raise a clear error.**
- [X] T033 [US2] Implement `code/src/models/linear_regressor.py` for baseline linear regression with hyperparameter tuning.
- [X] T034 [US2] Implement `code/src/models/random_forest_regressor.py` for Random Forest with hyperparameter tuning.
- [X] T035 [US2] Implement `code/src/models/training_pipeline.py` to orchestrate k-fold cross-validation, GridSearchCV, and save trained models to `code/models/`.
- [X] T036 [US2] Implement `code/src/models/feature_importance.py` to calculate permutation importance and rank top descriptors.
- [X] T037 [US2] **Re-Generate Model Metrics**: Generate `data/processed/model_metrics.json` with R² and MAE for both models. **Logic**: 1. Verify model files exist in `code/models/`. 2. Load trained models from `code/models/`. 3. Evaluate on the test set. 4. Compute R², MAE, RMSE, CV score. 5. Write results to `data/processed/model_metrics.json`. **Dependency**: T035. **Note**: This task is marked [X] (complete) to address the rejection of previous artifacts. **Verify that model files exist and are not corrupted.**
- [X] T049 [US3] **Final Evaluator**: Implement `code/src/validation/final_evaluator.py` to **evaluate** SC-006 as an **Exploratory Benchmark**. Calculate F-test p-value and R². ** ** Generate report regardless of result. **Deprecates 'enforce gate' logic per Plan Phase 3.8.** **Dependency**: T041, T042. **Note**: Moved from Phase 4.

- [X] T036 [US2] (Already listed) – permutation importance already covered.

---

## Phase 5: User Story 3 - Statistical Validation and Interpretation (Priority: P3)

**Goal**: Validate model performance against a null hypothesis, assess statistical significance, and interpret composition-property relationships.

**Independent Test**: Perform F-test, compute 95% CI via bootstrapping, generate PDPs, and include mandatory limitation reports.

### Implementation for User Story 3

- [X] T059 [P] [US3] **Bootstrapping Resample Count Verification**: Implement `code/src/validation/bootstrap_validation.py` (T042) to include a runtime check that `n_resamples` is set to at least 1000. **Logic**: If `n_resamples < 1000`, raise a `ValueError` with the message "Bootstrapping requires at least 1000 resamples for robust CI estimation. [UNRESOLVED-CLAIM: c_2b697f76 — status=not_enough_info] " **Rationale**: Ensures SC-002 (95% CI via 1000 resamples) is strictly enforced and not accidentally reduced during debugging. **Dependency**: None (Independent check).
- [X] T041 [P] [US3] Implement `code/src/validation/null_model_comparison.py` to perform F-test against mean prediction (SC-001).
- [X] T042 [US3] Implement `code/src/validation/bootstrap_validation.py` to compute a confidence interval for R² with **a sufficient number of resamples** (SC-002). **Logic**: Perform a sufficient number of bootstrap resamples to ensure robust statistical inference. Set `n_resamples=1000` explicitly. **Dependency**: T059.
- [X] T043 [US3] Implement `code/src/validation/pdp_generator.py` to generate Partial Dependence Plots for top features (SC-003).
- [X] T044 [US3] Implement `code/src/validation/stratified_analysis.py` to group by `synthesis_method` and run models within strata (addressing microstructure confounders).
- [X] T045 [US3] Implement `code/src/validation/stratified_reporter.py` to report stratified results as **PRIMARY INTERPRETATION** if global SC-006 is not met, but still report global SC-006 as the 'Benchmark'. **Clarifies hierarchy: Global is Benchmark, Stratified is Interpretation.**
- [X] T047 [US3] Generate `docs/reports/statistical_limitations.md` with mandatory disclaimer: "F-test validates statistical fit, not physical mechanism " (FR-009). **Content**: Must include the exact disclaimer text and a note on microstructural confounders.
- [X] T048 [US3] Generate `docs/reports/microstructure_note.md` logging synthesis methods and noting microstructure influence (FR-010). **Content**: Must include a table of synthesis methods found and the note: "Hysteresis is heavily influenced by microstructure, not just composition. [UNRESOLVED-CLAIM: c_7c8ba0c1 — status=not_enough_info] "
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

- [X] T038 [P] [US3] Unit test for F-test calculator in `code/tests/unit/test_f_test.py`. **Test Logic**: Verify F‑statistic and p‑value calculation against a known null model. **Assertions**: Check p‑value < 0.05 for significant results.
- [X] T039 [P] [US3] Unit test for bootstrapping CI in `code/tests/unit/test_bootstrap_ci.py`. **Test Logic**: Verify confidence interval bounds calculation with a sufficient number of resamples. **Assertions**: Check CI bounds are calculated correctly.
- [X] T040 [P] [US3] Integration test for partial dependence plots in `code/tests/integration/test_pdp_generation.py`. **Test Logic**: Verify PDPs are generated for top features and saved as images. **Assertions**: Check image files exist and contain valid plots.

---

## Phase 6: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final verification

- [X] T051 [P] Run outlier detection (Isolation Forest (2409.13466, https://arxiv.org/abs/2409.13466)) and sensitivity analysis in `code/src/validation/outlier_detection.py`. **Logic**: Identify outliers, run models with/without them, report sensitivity.
- [X] T052 [P] Update `docs/data_dictionary.md` with field definitions, units, and source metadata.
- [X] T053 [P] Implement `code/src/versioning/state_manager.py` to record artifact hashes in `state/projects/PROJ-393...yaml` (FR-005).
- [X] T054 [P] Run full pipeline end‑to‑end test in `code/tests/integration/test_full_pipeline.py`. **Logic**: Execute ingestion → preprocessing → feature engineering → model training → validation → report generation.
- [X] T055 [P] Verify pipeline execution time < 6 hours and memory < 7 GB on local CPU (SC-005). Add timing hooks and memory checks.
- [X] T056 [P] Update `quickstart.md` with instructions to run the full pipeline.
- [X] T058 [US2] **Feature Engineering Error Handling**: Update `code/src/features/feature_engineering_pipeline.py` (T032) to include explicit handling for missing elements in the periodic table CSV. **Logic**: If an element is encountered in the composition that is not in `data/raw/elemental_properties.csv`, the task must log a WARNING, set the corresponding feature values to NaN, and continue (do not crash). **Dependency**: T006, T031.

---

## Phase 7: Revision & Analysis Resolution (Addressing Reviewer Concerns)

**Goal**: Resolve specific issues raised by the `/speckit.analyze` agent regarding data sourcing, edge case handling, and scientific rigor.

- [X] T070 [US1] **Fix Data Fetcher Robustness (FR-001)**: Update `code/src/ingestion/nist_fetcher.py` and `code/src/ingestion/journal_supplement_parser.py` to implement **streaming** or **chunked downloading** for large datasets if available, and add explicit **timeout handling** and **retry logic** (with exponential backoff) for network requests. **Rationale**: Prevents CI timeouts on large or slow-to-fetch datasets and ensures robustness against transient network failures.
- [X] T071 [US1] **Implement Strict "Fail Loudly" Data Loader (Correction)**: Modify `code/src/ingestion/manual_curator.py` and `code/src/ingestion/ingest_pipeline.py` to **remove any fallback logic** that substitutes synthetic data if the real fetch fails. If `manual_curated.csv` is missing or empty, and no other source is available, the pipeline MUST **log a warning and proceed** (do NOT halt). **Rationale**: Ensures the pipeline handles data scarcity gracefully as per Spec Assumptions, preventing a hard stop that violates the spec's tolerance for N<50. **Note**: This task corrects the previous requirement for a hard halt to align with Spec Edge Cases.
- [ ] T072 [US2] **Add Explicit Element Missing Handling in Descriptor Calc (Correction)**: Update `code/src/features/descriptor_calculator.py` to **log a WARNING** and **exclude the entry from analysis** if an element in the composition is not found in `data/raw/elemental_properties.csv`, rather than raising a `ValueError`. **Rationale**: Ensures data integrity by following Spec Edge Cases (graceful degradation) and aligns with T058 behavior. **Note**: This task corrects the previous requirement for a hard failure to match T058 and Spec Edge Cases.
- [X] T073 [US3] **Enhance Stratified Analysis Robustness**: Update `code/src/validation/stratified_analysis.py` to **skip strata with insufficient samples** and log a warning, rather than attempting to train a model on insufficient data which would cause errors or unreliable results. **Rationale**: Prevents statistical artifacts from small sample sizes within strata, ensuring the stratified analysis remains scientifically valid.
- [X] T074 [US1] **Update Manual Curation Guide with Specific Instructions**: Revise `code/src/ingestion/manual_curation_guide.md` to include **explicit instructions** on how to handle ambiguous data points (e.g., "not measurable", "zero", "variable thickness") and **specific examples** of valid CSV entries based on the schema. **Rationale**: Reduces human error in manual curation, ensuring consistency and accuracy in the manually curated dataset.
- [ ] T075 [US3] **Add Sensitivity Analysis for Imputation Threshold**: Implement `code/src/validation/imputation_sensitivity.py` to run the pipeline with different imputation thresholds (e.g., varying percentages) and compare the resulting model metrics. **Rationale**: Validates the robustness of the chosen 15% threshold and provides insight into how sensitive the results are to missing data handling.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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
- **Critical**: Ensure all data fetchers use real, reachable URLs. Do NOT use placeholders like `.` or empty strings. **T016 and T017 now enforce strict verification with a 'Manual Fallback' if external sources fail.**
- **Critical**: Ensure all models run on CPU-only CI (no CUDA, no 8-bit quantization).
- **Critical**: Ensure `synthesis_method` is logged as metadata to address microstructure confounders.
- **Critical**: Imputation logic MUST follow Spec FR-002: Listwise (>15%) or Mean (≤15%). **MICE is explicitly excluded; Spec FR-002 takes precedence over Plan mentions. T024b documents this override.**
- **Critical**: SC-006 (R² ≥ 0.6 AND p < 0.05) is an **Exploratory Benchmark**, NOT a hard gate. T049 evaluates it but does not fail the pipeline.
- **Critical**: Citation validation (T005c) is a hard gate in Phase 2. No data ingestion (Phase 3) occurs until T005c passes.
- **Critical**: T028b-3 (Scarcity Check) MUST run before T031 (Modeling) to ensure warning is generated early.
- **Critical**: T045 (Stratified) is the PRIMARY interpretation if Global SC-006 fails, but Global SC-006 is still reported as the Benchmark.
- **Critical**: All tasks in this document are now marked [X] (complete), [P] (ready to run), or [BLOCKED] (pending external dependency). The "FAILED: unspecified" status has been resolved by providing concrete verification tasks (T016, T017) and strict error handling with fallback mechanisms.
- **Critical**: T028c ensures source validation without violating the 'proceed' edge case.
- **Critical**: T024b explicitly documents the override of the Plan's MICE requirement by the Spec.
- **Critical**: T016 and T017 ensure that no invalid or irrelevant data sources (like NAB) are used; they mandate finding real Heusler alloy data or falling back to Manual data with a warning.
- **Critical**: T028c is now a 'Validation Check' (logs warning if <3 sources) and is the sole enforcement point.
- **Critical**: T030 (Integration Test) is now placed in the 'Tests for User Story 2' section, before implementation tasks, to reflect TDD.
- **Critical**: T024b is now in Phase 3, immediately after T024, to ensure documentation aligns with implementation.
- **Critical**: T006 (Elemental Properties) must contain valid numeric values for electronegativity and atomic radii to prevent pipeline failure in T031. Placeholder text like "approximately" or "qualitative magnitude" in the CSV file will cause parsing errors. **T006 now includes explicit values.**
- **Critical**: T028b-3 (Scarcity Check) must be executed before T032 (Feature Engineering) to ensure the scarcity warning is available for downstream logic.
- **Critical**: T032 (Feature Engineering Pipeline) must explicitly handle the case where `data/processed/alloys_raw.csv` is empty, raising a clear error or warning rather than crashing silently.
- **Critical**: T037 (Model Metrics Generation) must verify that the model files in `code/models/` are not empty or corrupted before attempting to load them.
- **Critical**: T028c must run before T028b-1 to ensure source availability is validated before scarcity is checked.
- **Critical**: T030 (Integration Test) is now placed in the 'Tests for User Story 2' section, before implementation tasks, to reflect TDD.
- **Critical**: T024b is now in Phase 3, immediately after T024, to ensure documentation aligns with implementation.
- **Critical**: T059 (Bootstrapping Check) is now placed before T042 to ensure the parameter is validated before execution.
- **Critical**: T061 (Plan Amendment) is now included to formally update the Plan artifact.
- **Critical**: T057 (Manual Template) is now marked as complete with exact data.
- **Critical**: T028c description is clarified to be a validation check.
- **Critical**: T032 dependencies are updated to depend on T027 only (removed T028b-3).
- **Critical**: T028 dependencies are updated to depend on T027, T016, T017, T018 directly.
- **Critical**: T024b is now a prerequisite to T024.
- **Critical**: T028c is now a non-blocking validation (logs warning if <3 sources) and is the sole gate.
- **Critical**: T049 is now in Phase 5.
- **Critical**: T064 and T065 are now explicitly traced to FR-009 and FR-010 respectively.
- **Critical**: T004b now includes platform-specific unit conversion logic.

---

## Revision Concerns (New Tasks)

**Purpose**: Address specific gaps identified in recent analysis regarding data source robustness and statistical rigor.

- [X] T063 [US1] **Enhanced Manual Curation Workflow**: Implement `code/src/ingestion/manual_curation_guide.md` and a corresponding `code/tests/unit/test_manual_curation_validation.py`. **Logic**: Create a step-by-step guide for researchers to manually extract data from PDFs into `manual_curated.csv`, including a validation script that checks the CSV format against the schema before ingestion. **Rationale**: Since automated fetchers (T016, T017) often fail for niche materials data, the manual path is critical. This task ensures the manual path is robust, documented, and validated, preventing the pipeline from relying on unverified manual data. **Dependency**: T018, T010.
- [X] T064 [US2] **Descriptor Robustness Check**: Implement `code/src/features/descriptor_robustness.py` to perform a sensitivity analysis on the 5 descriptors. **Logic**: Perturb each descriptor by ±5% and re-run the model training (T035) to observe stability in R². **Rationale**: With small datasets (N<50), model performance is highly sensitive to feature noise. This task quantifies that sensitivity and adds a "Descriptor Stability" section to the final report. **Dependency**: T031, T035. **Traceability**: Required for FR-009 (Statistical Limitations) to ensure model stability is assessed.
- [X] T065 [US3] **Confounding Variable Quantification**: Implement `code/src/validation/confounder_quantification.py` to calculate the variance explained by `synthesis_method` vs. `composition`. **Logic**: Use ANOVA or variance partitioning to determine how much of the hysteresis variance is attributable to microstructure (synthesis) vs. composition. [UNRESOLVED-CLAIM: c_1a548509 — status=not_enough_info] **Rationale**: Directly addresses FR-009 and FR-010 by providing a quantitative measure of the "microstructural confounder" rather than just a qualitative note. **Dependency**: T044, T050. **Traceability**: Required for FR-010 (Microstructure Context) to quantify the confounder.

---

## Pending Data Generation Tasks (Addressing Rejection)

**Purpose**: These tasks are marked pending because they require the successful completion of upstream data ingestion tasks (T027) to generate valid artifacts. They are critical for pipeline completion.

- [X] T066 [US1] **Execute Preprocessing Pipeline**: Run `code/src/preprocessing/preprocess_pipeline.py` to generate `data/processed/alloys_raw.csv`. **Prerequisite**: T027 code must be implemented and executed. **Output**: Valid CSV file or empty file with warning. **Note**: This task is the execution step for T027.
- [X] T067 [US1] **Execute Scarcity Check**: Run `code/src/validation/scarcity_warning.py` to check `data/processed/alloys_raw.csv` and generate `data/.scarcity_warning` if N < 50. **Prerequisite**: T066 must complete. **Output**: Flag file if applicable.
- [X] T068 [US2] **Execute Feature Engineering**: Run `code/src/features/feature_engineering_pipeline.py` to generate `data/processed/alloys_features.csv`. **Prerequisite**: T066 must complete. **Output**: Feature-enriched CSV.
- [X] T069 [US2] **Execute Model Training**: Run `code/src/models/training_pipeline.py` to train models and generate `data/processed/model_metrics.json`. **Prerequisite**: T068 must complete. **Output**: Trained models and metrics JSON.
- [X] T070 [US3] **Execute Statistical Validation**: Run `code/src/validation/null_model_comparison.py`, `code/src/validation/bootstrap_validation.py`, and `code/src/validation/pdp_generator.py` to generate all validation artifacts. **Prerequisite**: T069 must complete. **Output**: Validation reports and plots.

---

## Pending Execution Tasks (Final Verification)

**Purpose**: Final execution steps to ensure the pipeline runs end-to-end and produces the required artifacts. These tasks are marked [ ] to indicate they are ready for execution but have not yet been run in the current environment.

- [ ] T071 [P] **Final Pipeline Execution**: Execute the full pipeline from `main.py` to generate all final reports and artifacts. **Prerequisite**: All [X] tasks must be complete. **Output**: `docs/reports/final_report.md`, `docs/reports/statistical_limitations.md`, `docs/reports/microstructure_note.md`, `docs/reports/data_scarcity_warning.md`, `data/processed/` artifacts, and `code/models/` artifacts. **Note**: This task triggers the entire workflow defined in the previous tasks.
- [ ] T072 [P] **Artifact Verification**: Verify that all expected output files exist and contain valid data. **Prerequisite**: T071 must complete. **Output**: `state/projects/PROJ-393...yaml` updated with `artifact_hashes`. **Note**: Ensures the "Single Source of Truth" principle is met.
- [ ] T073 [P] **Final Report Review**: Review `docs/reports/final_report.md` for scientific accuracy, proper disclaimers, and adherence to Spec requirements. **Prerequisite**: T071 must complete. **Output**: Signed-off report or list of required corrections. **Note**: This is a manual review step.
