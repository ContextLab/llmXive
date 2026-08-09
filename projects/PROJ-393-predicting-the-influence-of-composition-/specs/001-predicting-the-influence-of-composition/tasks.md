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
- [X] T057 [US1] **Manual Data Curation Template**: Create `data/raw/manual_curated_template.csv` with the exact schema defined in `specs/001-predict-heusler-hysteresis/contracts/alloy_entry.schema.yaml` to serve as the fallback input for T018. **Prerequisite for T018**. **Exact Data**: The file MUST contain a header row and at least one example row with valid atomic fractions summing to a normalized total.
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
- [X] T006 [P] Create `data/raw/elemental_properties.csv` with fixed periodic table data for all elements likely found in Heusler alloys (Mn, Co, Fe, Ga, Al, Ni, Cu, Sn, In, Ti, V, Zn, Si, Ge, Sb, Pb, Mg, Cr, Nb, Ta) including columns: `element`, `electronegativity`, `atomic_radii`, `valence_electrons`, `source_reference`. **Source**: Pyykko and standard references. **Implementation**: Do NOT copy-paste unverified text. Instead, implement `code/src/utils/generate_elemental_properties.py` which contains a hardcoded dictionary of verified values (sourced from Pyykko 1988 or standard periodic table data) and writes the CSV deterministically. **Content**: The script must output the exact rows for the elements listed above with values consistent with Pyykko.
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
- [X] T024b [US1] **Imputation Strategy Rationale**: Create `docs/reports/imputation_strategy_rationale.md`. **Content**: Must explicitly state: "Spec FR-002 defines the required imputation strategy for this project (Mean Imputation/Listwise Deletion) based on the small N context (N<50). The Plan's MICE is a valid general method but not required here. This decision aligns with the 'Exploratory' nature of the study and avoids the complexity of MICE for small N." **Dependency**: Must run immediately after T061 (Plan Amendment) is completed. **Placement**: This task is moved to Phase 2 to ensure it is available before US1 implementation.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Aggregation and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Aggregate scattered experimental measurements from NIST, journal supplements, and manual curation into a single, standardized dataset.

**Independent Test**: Successfully ingest data from multiple distinct sources, standardize composition to atomic fractions, normalize hysteresis parameters, and produce a validated CSV with no DFT targets.

### Tests for User Story 1 ⚠️ (Written first per TDD, executed after Implementation)

- [X] T012 [US1] Unit test for composition parser in `code/tests/unit/test_composition_parser.py` (tests "Co2MnGa" -> atomic fractions).
- [X] T013 [US1] Unit test for unit normalizer in `code/tests/unit/test_unit_normalizer.py` (tests Oe/emu/g conversion).
- [X] T014 [US1] Integration test for DFT filter in `code/tests/integration/test_dft_filter.py` (ensures DFT targets are excluded).
- [X] T015 [US1] Integration test for imputation logic in `code/tests/integration/test_imputation_logic.py`. **Test Logic**: Implement a function `test_imputation_logic_switches_at_15_percent` that calls the imputation logic with a missing rate of 0.14 and asserts `mean_imputation` is used, then calls with 0.16 and asserts `listwise_deletion` is used. **Assertion**: `if missing_rate > 0.15: assert listwise_deletion else: assert mean_imputation`. **Note**: This test validates Spec FR-002. **Implementation Logic**: The implementation MUST follow Spec FR-002 (Mean Imputation/Listwise Deletion), ignoring the Plan's MICE mention. **Execution Order**: Code (T024a-T024c) -> Test (T015).

### Implementation for User Story 1 (Executed after tests)

- [X] T016 [US1] **NIST Source Verification & Fetch**: Implement `code/src/ingestion/nist_fetcher.py` to search the NIST Materials Data Repository for Heusler alloy magnetic hysteresis data. **Logic**: Use the NIST Materials Data Repository API with appropriate query parameters for Heusler alloys and hysteresis. **Validation**: If the API returns status != 200 or JSON is empty, raise `DataFetchError` (see T067) and halt. Otherwise, store raw data in `data/raw/nist_source.json`. Output `data/raw/nist_source_status.json` with verification details.
- [X] T017 [US1] **Journal Source Verification & Fetch**: Implement `code/src/ingestion/journal_supplement_parser.py` to search for and parse PDF/CSV supplements from 'Acta Materialia' or 'Journal of Alloys and Compounds' for Heusler alloy hysteresis data. **Logic**: Use `BeautifulSoup` to parse search results from ScienceDirect with DOI regex. **Validation**: On failure, raise `DataFetchError` (see T067). Successful fetch stored in `data/raw/journal_source.json`; status written to `data/raw/journal_source_status.json`.
- [X] T018 [US1] Implement `code/src/ingestion/manual_curator.py` to load `data/raw/manual_curated.csv`. If the file is missing, log a warning and proceed with 0 entries (graceful degradation). Output always written to `data/raw/manual_curated.csv`.
- [X] T019 [US1] Implement `code/src/preprocessing/composition_parser.py` to convert strings to atomic fractions (≥4 decimal places).
- [X] T020 [US1] Implement `code/src/preprocessing/unit_normalizer.py` to standardize coercivity (Oe) and saturation magnetization (emu/g).
- [X] T021 [US1] Implement `code/src/preprocessing/dft_filter.py` to exclude entries where `source_type` contains 'DFT', 'Calculated', or 'Simulation', OR `target_source` == 'Materials Project'. **Explicitly LOG/FLAG excluded entries before removal.**
- [X] T024a [US1] **Imputation Logic Implementation**: Implement `code/src/preprocessing/imputation_orchestrator.py` to handle missing data per Spec FR-002. **Logic**: Calculate missing rate per column as `null_count / total_rows`. If `missing_rate > 0.15`, perform listwise deletion of rows with nulls in that column. If `missing_rate <= 0.15`, perform mean imputation (column-wise mean of non-null values). **Documentation**: This task implements the Spec-required imputation strategy. **Dependency**: T061 (Plan Amendment) and T024b (Rationale) must be completed.
- [X] T024c [US1] **Imputation Threshold Verification**: Unit test `code/tests/unit/test_imputation_threshold.py` that asserts the [deferred] switch point is correctly implemented in `imputation_orchestrator.py`.
- [X] T025 [US1] Implement `code/src/preprocessing/validator.py` to check for elements not in periodic table and log warnings.
- [X] T026 [US1] Create `code/src/ingestion/ingest_pipeline.py` to orchestrate fetching, parsing, and saving to `data/raw/` with checksums.
- [X] T028c [US1] **FR-001 Hard Gate Enforcement (Modified)**: Implement `code/src/ingestion/fr001_gate.py` that counts distinct sources with non‑empty data (NIST, Journal, Manual). If fewer than three sources provide data, log a CRITICAL error and proceed to T046 (Scarcity Warning). **Do NOT halt the pipeline.** This ensures the required scarcity warning is generated.
- [X] T027 [US1] **Generate Preprocessed Data**: Implement `code/src/preprocessing/preprocess_pipeline.py` to:
 1. Load raw files produced by T016‑T018.
 2. Apply composition parsing (T019), unit normalization (T020), DFT filter (T021), element validation (T025), and imputation (T024a).
 3. Write the unified, validated dataset to `data/processed/alloys_raw.csv`.
 4. **Verification**: After writing, assert that the file exists, schema‑validates against `alloy_entry.schema.yaml`, and contains at least one row. Failure aborts the pipeline. **Dependency**: T028c (Gate) must pass (log only) before this writes the final artifact.
- [X] T028 [US1] Generate `data/processed/completeness_report.json` (SC-004) reporting data proportions per source. **Logic**: Compute `total_rows`, `valid_rows`, and `completeness_pct` for each source and overall. **Verification**: Ensure JSON is written and conforms to the documented schema.
- [X] T028b [US1] **Scarcity Handling**: Count rows in `data/processed/alloys_raw.csv` after T021 filtering. **Dependency**: Must run AFTER T027. **Logic**: If `N < 50`, write `data/.scarcity_warning` containing JSON `{"n": N, "threshold": 50}`. If `N >= 50`, write an empty file. **Note**: This file-based flag is read by T046.
- [X] T046 [US1] **Data Scarcity Warning Generation**: Generate `docs/reports/data_scarcity_warning.md` when `data/.scarcity_warning` exists and contains `N < 50`. The markdown must include count `N`, a statement of reduced statistical power, an overfitting warning, and reference FR-008.
- [X] T063 [US1] **Enhanced Manual Curation Workflow**: Implement `code/src/ingestion/manual_curation_guide.md` and a corresponding `code/tests/unit/test_manual_curation_validation.py`. **Logic**: Create a step‑by‑step guide for researchers to manually extract data from PDFs into `manual_curated.csv`, including a validation script that checks the CSV format against the schema before ingestion.

---

## Phase 4: User Story 2 - Feature Engineering and Model Training (Priority: P2)

**Goal**: Transform elemental compositions into meaningful descriptors and train regression models (Linear, Random Forest) to predict magnetic hysteresis parameters (coercivity, saturation magnetization).

**Independent Test**: Compute ≥5 descriptors, train models with cross-validation, and produce performance metrics (R², MAE).

### Tests for User Story 2 ⚠️ (Written first per TDD, executed after Implementation)

- [X] T029 [P] [US2] Unit test for descriptor calculator in `code/tests/unit/test_descriptor_calculator.py` (tests VEC, electronegativity, etc.).
- [X] T030 [US2] Integration test for model training pipeline in `code/tests/integration/test_model_training.py`. **Test Logic**: Verify k-fold cross-validation is performed, models are trained, and metrics (R², MAE) are generated for both Linear and RF models. **Assertions**: Check that `model_metrics.json` exists and contains valid R² and MAE values for both models. **Dependency**: T035, T037.

### Implementation for User Story 2

- [X] T031 [P] [US2] Implement `code/src/features/descriptor_calculator.py` to compute: Average Electronegativity, VEC, Atomic Radii Variance, Avg d-electrons, Atomic Size Mismatch (FR-003).
- [X] T032 [US2] **Feature Engineering Pipeline**: Implement `code/src/features/feature_engineering_pipeline.py` to:
 1. Verify `data/processed/alloys_raw.csv` exists; if missing or empty, raise `FileNotFoundError` with clear message.
 2. Load the CSV and apply `descriptor_calculator` (T031) to each row.
 3. Append the five descriptor columns and write to `data/processed/alloys_features.csv`.
 4. **Verification**: Confirm the output file exists, contains the expected descriptor columns, and schema‑validates against `alloy_entry.schema.yaml` (extended with descriptor fields). Failure aborts the pipeline.
- [X] T033 [US2] Implement `code/src/models/linear_regressor.py` for baseline linear regression with hyperparameter tuning.
- [X] T034 [US2] Implement `code/src/models/random_forest_regressor.py` for Random Forest with hyperparameter tuning.
- [X] T035 [US2] Implement `code/src/models/training_pipeline.py` to orchestrate k-fold cross-validation, GridSearchCV, and save trained models to `code/models/`.
- [X] T036 [US2] Implement `code/src/models/feature_importance.py` to calculate permutation importance and rank top descriptors.
- [X] T037 [US2] **Generate Model Metrics**: Implement `code/src/models/generate_metrics.py` to:
 1. Load trained models from `code/models/`.
 2. Evaluate on the held‑out test set.
 3. Compute R², MAE, RMSE, CV score for each model.
 4. Write results to `data/processed/model_metrics.json` following the JSON schema:
 ```json
 {
 "LinearRegression": {"r2": number, "mae": number, "rmse": number, "cv_score": number},
 "RandomForest": {"r2": number, "mae": number, "rmse": number, "cv_score": number}
 }
 ```
 5. **Verification**: Validate the JSON against the schema and ensure both model entries are present.

- [X] T036 [US2] (Already listed) – permutation importance already covered.

---

## Phase 5: User Story 3 - Statistical Validation and Interpretation (Priority: P3)

**Goal**: Validate model performance against a null hypothesis, assess statistical significance, and interpret composition-property relationships.

**Independent Test**: Perform F-test, compute 95% CI via bootstrapping, generate PDPs, and include mandatory limitation reports.

### Implementation for User Story 3

- [X] T041 [P] [US3] Implement `code/src/validation/null_model_comparison.py` to perform F-test against mean prediction (SC-001). Outputs `validation/null_test_results.json` with `f_statistic`, `p_value`, and `r2_null`.
- [X] T042 [US3] Implement `code/src/validation/bootstrap_validation.py` to Compute a confidence interval for R² using a sufficient number of resamples. **Verification**: Ensure `n_resamples >= 1000`; otherwise raise `ValueError`. Output `validation/bootstrap_ci.json`.
- [X] T059 [P] **Bootstrapping Resample Count Verification**: Unit test `code/tests/unit/test_bootstrap_resample_count.py` asserts that `bootstrap_validation` raises when `n_resamples < 1000`.
- [X] T043 [US3] Implement `code/src/validation/pdp_generator.py` to generate Partial Dependence Plots for the top features (based on permutation importance). Saves PNG files to `docs/figures/pdp_<feature>.png`.
- [X] T044 [US3] Implement `code/src/validation/stratified_analysis.py` to group by `synthesis_method` and run models within each stratum, outputting `validation/stratified_results.json`.
- [X] T045 [US3] Implement `code/src/validation/stratified_reporter.py` to compile stratified results into a markdown section. The report is included in the final report as the **PRIMARY INTERPRETATION** if global SC-006 is not met; otherwise it is supplemental.
- [X] T069b [US3] **Expert Review Note Generation**: Generate `docs/reports/expert_review_note.md` explicitly stating that "Expert review is required for physical plausibility" and that composition does not causally determine $H_c$ without microstructure. **Dependency**: Must run before T050.
- [X] T047 [US3] Generate `docs/reports/statistical_limitations.md` with mandatory disclaimer: "F-test validates statistical fit, not physical mechanism" (FR-009) and a note on microstructural confounders.
- [X] T048 [US3] Generate `docs/reports/microstructure_note.md` logging synthesis methods and noting hysteresis influence (FR-010). Includes a table of observed synthesis methods.
- [X] T049 [US3] **Final Evaluator**: Implement `code/src/validation/final_evaluator.py` to evaluate SC-006 as an **Exploratory Benchmark** (R² ≥ 0.6 and p < 0.05). Generates `docs/reports/final_evaluation.md` summarizing the benchmark result and linking to the stratified interpretation. If SC-006 is not met, generate the narrative "Consistent with Physical Reality".
- [X] T050 [US3] Generate `docs/reports/final_report.md` combining all metrics, plots, and mandatory sections (Executive Summary, Dataset Completeness, Model Performance, Feature Importance, PDPs, Statistical Limitations, Data Scarcity Warning, Microstructure Note, Expert Review Note, Final Evaluation). **Dependency**: T069b must be completed.

### Tests for User Story 3 ⚠️ (Written first per TDD, executed after Implementation)

- [X] T038 [P] [US3] Unit test for F-test calculator in `code/tests/unit/test_f_test.py`. **Test Logic**: Verify F‑statistic and p‑value calculation against a known null model. **Assertions**: Check p‑value < 0.05 for significant results.
- [X] T039 [P] [US3] Unit test for bootstrapping CI in `code/tests/unit/test_bootstrap_ci.py`. **Test Logic**: Verify confidence interval bounds calculation with a sufficient number of resamples. **Assertions**: Check CI bounds are calculated correctly.
- [X] T040 [P] [US3] Integration test for partial dependence plots in `code/tests/integration/test_pdp_generation.py`. **Test Logic**: Verify PDPs are generated for top features and saved as images. **Assertions**: Check image files exist and contain valid plots.

---

## Phase 6: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final verification

- [X] T051 [P] Run outlier detection (Isolation Forest) and sensitivity analysis in `code/src/validation/outlier_detection.py`. **Logic**: Identify outliers, run models with/without them, report sensitivity.
- [X] T052 [P] Update `docs/data_dictionary.md` with field definitions, units, and source metadata.
- [X] T053 [P] Implement `code/src/versioning/state_manager.py` to record artifact hashes in `state/projects/PROJ-393...yaml` (FR-005).
- [X] T054 [P] Run full pipeline end‑to‑end test in `code/tests/integration/test_full_pipeline.py`. **Logic**: Execute ingestion → preprocessing → feature engineering → model training → validation → report generation.
- [X] T055 [P] Verify pipeline execution time < 6 hours and memory < 7 GB on local CPU (SC-005). Add timing hooks and memory checks.
- [X] T056 [P] Update `quickstart.md` with instructions to run the full pipeline.
- [X] T058 [US2] **Feature Engineering Error Handling**: Update `code/src/features/feature_engineering_pipeline.py` (T032) to include explicit handling for missing elements in the periodic table CSV. **Logic**: If an element is encountered in the composition that is not in `data/raw/elemental_properties.csv`, the task must log a WARNING, set the corresponding feature values to NaN, and continue (do not crash). **Dependency**: T006, T031.

---

## Phase 7: Revision & Analysis Resolution (Addressing Reviewer Concerns)

**Goal**: Resolve specific issues raised by the `/speckit.analyze` agent regarding data sourcing, edge case handling, and scientific rigor.

- [ ] T070 [US1] **Fix Data Fetcher Robustness (FR-001)**: Update `code/src/ingestion/nist_fetcher.py` and `code/src/ingestion/journal_supplement_parser.py` to implement **streaming** or **chunked downloading** for large datasets if available, and add explicit **timeout handling** and **retry logic** (with exponential backoff) for network requests. **Rationale**: Prevents CI timeouts on large or slow-to-fetch datasets and ensures robustness against transient network failures.
- [ ] T071 [US1] **Implement Strict "Fail Loudly" Data Loader (Correction)**: Modify `code/src/ingestion/manual_curator.py` and `code/src/ingestion/ingest_pipeline.py` to **remove any fallback logic** that substitutes synthetic data if the real fetch fails. If `manual_curated.csv` is missing or empty, and no other source is available, the pipeline MUST **log a warning and proceed** (do NOT halt). **Rationale**: Ensures the pipeline handles data scarcity gracefully as per Spec Assumptions, preventing a hard stop that violates the spec's tolerance for N<50. **Note**: This task corrects the previous requirement for a hard halt to align with Spec Edge Cases.
- [ ] T072 [US2] **Add Explicit Element Missing Handling in Descriptor Calc (Correction)**: Update `code/src/features/descriptor_calculator.py` to **log a WARNING** and **exclude the entry from analysis** if an element in the composition is not found in `data/raw/elemental_properties.csv`, rather than raising a `ValueError`. **Rationale**: Ensures data integrity by following Spec Edge Cases (graceful degradation) and aligns with T058 behavior. **Note**: This task corrects the previous requirement for a hard failure to match T058 and Spec Edge Cases.
- [ ] T073 [US3] **Enhance Stratified Analysis Robustness**: Update `code/src/validation/stratified_analysis.py` to **skip strata with insufficient samples** and log a warning, rather than attempting to train a model on insufficient data which would cause errors or unreliable results. **Rationale**: Prevents statistical artifacts from small sample sizes within strata, ensuring the stratified analysis remains scientifically valid.
- [ ] T074 [US1] **Update Manual Curation Guide with Specific Instructions**: Revise `code/src/ingestion/manual_curation_guide.md` to include **explicit instructions** on how to handle ambiguous data points (e.g., "not measurable", "zero", "variable thickness") and **specific examples** of valid CSV entries based on the schema. **Rationale**: Reduces human error in manual curation, ensuring consistency and accuracy in the manually curated dataset.
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
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

**End of tasks.md**