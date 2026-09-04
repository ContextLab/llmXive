# Tasks: Predicting Perovskite Stability via Compositional Fingerprints

**Input**: Design documents from `/specs/001-predicting-perovskite-stability/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create project directories: `code/`, `data/raw/`, `data/processed/`, `tests/`, `docs/`, `state/`
- [X] T001b [P] Create `code/requirements.txt` with initial dependencies: `pandas`, `scikit-learn`, `requests`, `pyyaml`, `numpy`, `pymatgen`
- [X] T002 Initialize Python 3.11 project with dependencies (`code/requirements.txt`)
- [X] T003 [P] Configure linting (flake8/pylint) and formatting (black/isort) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `state_manager.py` to compute SHA-256 hashes for derived artifacts and update `state/...yaml`
- [X] T005 Create `contracts/descriptor.schema.yaml` defining the schema for `CompositionalDescriptor` entities
- [ ] T006 [P] Implement `code/utils/data_fetcher.py` with retry logic: up to 3 retries with exponential backoff. **Implementation**: Implement the retry loop with exponential backoff logic (e.g., base delay * 2^retry_count) but DO NOT hard-code specific delay values in the task description. The logic must be configurable. **Verification**: Verify `config.yaml` contains `delay_multiplier` key and that `code/utils/data_fetcher.py` reads from it. <!-- Requires: T008 --> <!-- Verification: See T056 -->
- [X] T007 Implement `code/utils/formula_parser.py` using `pymatgen` for deterministic A/B/X site assignment. **Specificity**: Use `pymatgen.core.Element` class for all elemental property lookups to ensure reproducibility.
- [X] T008 Setup environment configuration management for API keys (Materials Project, NREL) in `.env`
- [X] T009 Implement `code/utils/checksum_verifier.py` to validate raw data integrity against source checksums
- [X] T041 [P] Update `contracts/metadata.schema.yaml` to require explicit fields for `tga_model`, `tga_manufacturer`, `temperature_precision` (±°C), and `heating_rate` (°C/min) for every source dataset entry, but make `instrument_model` and `manufacturer` OPTIONAL with a fallback flag. <!-- Verification: Verify `contracts/metadata.schema.yaml` contains required fields and validates optional instrumentation fields correctly. -->
- [X] T042 [P] Implement `code/utils/uncertainty_parser.py` to parse `temperature_precision` from source metadata; if missing, default to ±10°C and log a WARNING with message format: "WARNING: Missing precision for {formula}, defaulting to 10°C". [RESOLVED]
- [X] T043 [P] Implement `code/utils/uncertainty_propagator.py` to calculate the combined standard uncertainty for `T_d` based on the instrument precision and any reported experimental error. **Formula**: `sigma = sqrt(precision^2 + experimental_error^2)`. If experimental error is missing, use 0. If precision is missing, use 10°C (from T042). **Output**: Returns `sigma`.
- [X] T047c [P] Implement `code/utils/instrument_registry.py` to maintain a lookup table of known TGA instruments with documented precision values. **Source**: Load the registry from `data/raw/instrument_registry.csv`. **Schema**: The CSV MUST have columns: `instrument_model`, `manufacturer`, `precision_celsius`. If the file is missing or an instrument is not found, use the spec default of ±10°C and log a warning. **Constraint**: Do NOT hard-code specific manufacturer models or precision values in the code. **Output**: A function `get_precision(instrument_model)` that returns the precision value or the default. <!-- Verification: See T052 -->
- [X] T052 [P] Implement a "TGA Instrument Lookup" function in `code/utils/instrument_registry.py` that maps instrument model names to their standard precision specifications (±°C) based on the registry defined in T047c. **Verification**: Verify that `instrument_registry.py` successfully loads the registry from `data/raw/instrument_registry.csv` (if it exists) and correctly applies the default ±10°C precision for any instrument model not found in the registry. Log any unmapped instruments to `data/raw/unmapped_instruments.log`. <!-- Requires: T047c -->
- [X] T047a [US1] Implement `code/utils/data_fetcher.py` to extract and validate `instrument_model` and `manufacturer` fields from source metadata (NREL/Materials Project) during the initial fetch. If these fields are missing, log a WARNING and assign a default precision of ±10°C using the fallback strategy. Do NOT raise a `MissingInstrumentationError`. Log the formula to `data/raw/instrumentation_fallbacks.log`. **Verification**: Verify that `data/raw/instrumentation_fallbacks.log` exists and contains entries for any formula where instrumentation metadata was missing, and that the pipeline proceeds. <!-- Requires: T006, T012a, T012b, T047c, T052 -->
- [X] T047b [US1] Update `contracts/metadata.schema.yaml` to make `instrument_model` and `manufacturer` OPTIONAL fields with a `source_instrumentation` flag (true/false) to indicate if data was found. <!-- Verification: Verify schema validation passes for JSON objects missing these fields and sets the flag to false. -->

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Descriptor Computation (Priority: P1) 🎯 MVP

**Goal**: Download perovskite data, filter for experimental TGA measurements, and compute compositional descriptors.

**Independent Test**: Run on a sample of formulas; verify output CSV contains `formula`, `T_d`, `atomic_fraction_A`, `weighted_ionic_radius`, etc., with non-null values.

### Tests for User Story 1 (OPTIONAL) ⚠️

- [X] T010 [P] [US1] Contract test for data ingestion output schema in `tests/contract/test_data_ingestion.py` <!-- Verification: Verify output CSV contains columns [formula, T_d, atomic_fraction_A, atomic_fraction_B, atomic_fraction_X, weighted_ionic_radius, weighted_electronegativity, weighted_formation_enthalpy, variance_ionic_radius, variance_electronegativity] with non-null values. -->
- [X] T011 [P] [US1] Integration test for API retry logic and error handling in `tests/integration/test_api_retries.py`

### Implementation for User Story 1

- [ ] T012a [US1] Fetch data from NREL API, invoke T009 validation, filter for `T_d` (TGA onset), and write to `data/raw/nrel_perovskites.csv`. <!-- Requires: T009 --> <!-- Verification: Verify `data/raw/nrel_perovskites.csv` exists and contains `T_d` column with non-null values. -->
- [ ] T012b [US1] Fetch data from Materials Project API, invoke T009 validation, filter for `T_d` (TGA onset), and write to `data/raw/mp_perovskites.csv`. <!-- Requires: T009 --> <!-- Verification: Verify `data/raw/mp_perovskites.csv` exists and contains `T_d` column with non-null values. -->
- [ ] T012c [US1] Implement merge logic: Concatenate `data/raw/nrel_perovskites.csv` and `data/raw/mp_perovskites.csv` based on `formula` and `source`. **Constraint**: If either input file is missing or empty, the task MUST fail with a specific error code. <!-- Requires: T012a, T012b --> <!-- Verification: Verify merge logic handles missing files correctly and logs duplicate count. -->
- [ ] T012d [US1] Implement duplicate removal: Drop duplicates from the merged dataset based on `formula` and `source`, logging the count of removed duplicates. **Constraint**: {{claim:c_6385fda1}} (Wikidata Q16872930, https://www.wikidata.org/wiki/Q16872930) <!-- Requires: T012c --> <!-- Verification: Verify duplicate count is logged. -->
- [ ] T012e [US1] Write final merged dataset to `data/raw/perovskites_merged.csv`. **Constraint**: {{claim:c_6385fda1}} <!-- Requires: T012d --> <!-- Verification: Verify `data/raw/perovskites_merged.csv` exists with row count >= 200. -->
- [ ] T013 [US1] Implement metadata parsing and validation: parse TGA model/precision from source metadata using T042, extract `instrument_model` and `manufacturer` from source metadata or assign default 'Unknown' with a warning, and write structured metadata to `data/raw/metadata.json`. **Schema**: The JSON must be a list of objects, each with keys: `formula`, `instrument_model`, `manufacturer`, `precision_source` (value="source" or "registry"). <!-- Requires: T042, T047a --> <!-- Verification: Verify `metadata.json` exists and conforms to the schema. -->
- [ ] T013b [US1] Implement logic to extract `temperature_precision` from T013 output, calculate `sigma` using T043 (formula: `sigma = sqrt(precision^2 + experimental_error^2)` where precision comes from T047c/T052 registry and experimental_error from source metadata), and write a NEW derived file `data/processed/descriptors_v1.csv` containing the original data plus the `T_d_uncertainty` column. **Constraint**: Do NOT append to existing files; create a new file. <!-- Requires: T012a, T012b, T012c, T012d, T012e, T043, T013, T047c, T052 --> <!-- Verification: Verify `descriptors_v1.csv` exists and contains `T_d_uncertainty` column with non-null values. -->
- [ ] T014 [US1] Implement `code/feature_engineering.py` to compute atomic fractions, weighted averages (ionic radius, electronegativity, formation enthalpy, first ionization energy), and variance metrics. **Specificity**: Use `pymatgen.core.Element.X.ionization_energy` for first ionization energy, using the version of pymatgen pinned in `code/requirements.txt`. Append `instrument_model`, `manufacturer`, and `precision_source` columns to the output; write to `data/processed/descriptors_v2.csv`. **Constraint**: Do NOT append to existing files; create a new file. <!-- Requires: T013b, T047c --> <!-- Verification: Verify output CSV contains columns [atomic_fraction_A, weighted_ionic_radius,..., instrument_model, manufacturer, precision_source] with non-null values (or 'Unknown' if missing). -->
- [ ] T014b [US1] Implement logic to derive `perovskite_family` (lead-halide, tin-halide, double perovskite) from A/B/X site elements in T014 output; write to `data/processed/descriptors_v2.csv`. **Constraint**: Do NOT append to existing files; create a new file. <!-- Requires: T014 --> <!-- Verification: Verify `perovskite_family` column has values in [lead-halide, tin-halide, double perovskite]. -->
- [X] T015a [US1] Implement logic to exclude entries with >= 2 missing descriptor values and log exclusion counts. **Output**: Write filtered dataset to `data/processed/descriptors_filtered.csv`. <!-- Verification: Log exclusion count to `data/processed/exclusion_log.csv` and verify count matches expected threshold (n >= 10 * features). -->
- [ ] T016a [US1] Implement `code/utils/vif_calculator.py` to compute VIF for all descriptors with a threshold > 5 to identify multicollinearity. **Input**: Must operate on the filtered dataset from T015a (`data/processed/descriptors_filtered.csv`). Write report to `data/processed/vif_report.csv`. <!-- Verification: Verify `vif_report.csv` contains VIF values for all descriptors and flags those > 5. -->
- [X] T016b [US1] Log decision rationale for VIF > 5 descriptors to `data/processed/vif_decision_log.csv`. <!-- Verification: Verify `vif_decision_log.csv` contains flagged descriptors and rationale. -->
- [X] T016c [US1] Unit test for VIF diagnostic computation and feature removal logic in `tests/unit/test_vif.py`. <!-- Requires: T016a, T016b -->
- [ ] T017 [US1] Write final processed dataset to `data/processed/descriptors_final.csv` including the `T_d_uncertainty`, `perovskite_family`, `instrument_model`, `manufacturer`, and `precision_source` columns and update `state/...yaml` with hash. <!-- Requires: T016a --> <!-- Verification: Verify `descriptors_final.csv` exists and `state/...yaml` is updated. -->

**Checkpoint**: User Story 1 fully functional; dataset ready for modeling.

---

## Phase 4: User Story 2 - Model Training and Cross-Validation (Priority: P2)

**Goal**: Train baseline regressors (RF, GB, Elastic Net) with strict CPU constraints, grid search limits, and uncertainty weighting.

**Independent Test**: Run k-fold CV on a subset of the data, where k=5; verify all models complete within 30 mins with R² metrics.

### Tests for User Story 2 (OPTIONAL) ⚠️

- [ ] T018 [P] [US2] Unit test for grid search hyperparameter limit enforcement (<= 10 combos) in `tests/unit/test_model_training.py`
- [X] T019 [P] [US2] Integration test for full pipeline runtime (must complete <= 4 hours) in `tests/integration/test_pipeline_runtime.py`

### Implementation for User Story 2

- [ ] T020a [US2] Implement `code/model_training.py` with Random Forest using `scikit-learn`; ensure all training uses default precision (no reduced-precision quantization) and CPU-only execution. <!-- Requires: T014b, T013b, T053, T054 -->
- [ ] T020b [US2] Implement `code/model_training.py` with Gradient Boosting using `scikit-learn`; ensure all training uses default precision (no reduced-precision quantization) and CPU-only execution. <!-- Requires: T014b, T013b, T053, T054 -->
- [ ] T020c [US2] Implement `code/model_training.py` with Elastic Net using `scikit-learn`; ensure all training uses default precision (no reduced-precision quantization) and CPU-only execution. <!-- Requires: T014b, T013b, T053, T054 -->
- [ ] T053 [US2] Implement a "Missing Instrumentation Report" generator in `code/utils/instrument_registry.py` that aggregates all entries from `data/raw/instrumentation_fallbacks.log` and writes a summary report to `data/processed/missing_instrumentation_report.csv` with columns: `formula`, `source`, `default_precision_used`, `confidence_flag`. **Verification**: Verify `missing_instrumentation_report.csv` exists and correctly aggregates all fallback entries with their default precision values. <!-- Requires: T013b, T047a -->
- [ ] T054 [US2] Update `code/model_training.py` to apply a configurable `low_confidence_weight` based on `confidence_flag` from T053. **Configuration**: The weight MUST be read from `code/config.yaml` under the key `low_confidence_weight` with a configurable default value. **Verification**: Verify `model_runs.json` includes logic for down-weighting low-confidence samples and that training logs reflect this adjustment. <!-- Requires: T053 -->
- [ ] T020d [US2] Implement `sample_weight` (1/σ²) for uncertainty weighting using `T_d_uncertainty` from T013b in `code/model_training.py`. <!-- Requires: T013b --> <!-- Verification: Verify `model_runs.json` includes `sample_weight` logic and that training logs show weighted loss calculation. -->
- [ ] T020e [US2] Implement stratified KFold logic with k=5 using `perovskite_family` column from T014b (specifically [lead-halide, tin-halide, double perovskite]) in `code/model_training.py`. <!-- Requires: T014b -->
- [ ] T020f [US2] Verify stratified split balance: Run a test case on the dataset to ensure the resulting train/test splits contain all three families (lead-halide, tin-halide, double perovskite) in every fold. Fail if any family is missing from a fold. <!-- Requires: T020e --> <!-- Verification: Verify the test passes only if all families are present in all folds. -->
- [ ] T022 [US2] Implement grid search with a hard cap of <= 10 hyperparameter combinations per model. **Verification**: Verify `model_runs.json` shows <= 10 combinations per model and assert max iterations in logs. [RESOLVED]
- [X] T023 [US2] Implement metric tracking (RMSE, R², MAE) and logging of best hyperparameters. <!-- Verification: Verify metrics are logged for each fold and model. -->
- [ ] T025 [US2] Save trained models and metrics to `data/processed/model_runs.json` with required keys: `model_type`, `hyperparameters`, `metrics` (R², RMSE, MAE). <!-- Verification: Verify `model_runs.json` exists and contains required keys. -->

**Checkpoint**: User Story 2 complete; best model identified.

---

## Phase 5: User Story 3 - Feature Importance Analysis and External Validation (Priority: P3)

**Goal**: Extract SHAP values, perform permutation testing, and validate on held-out literature data. **Constraint**: Proxy validation is NOT permitted; if literature data is missing, the task MUST fail.

**Independent Test**: Run SHAP on a test set.; verify top 3 features reported with p-values < 0.05.

### Tests for User Story 3 (OPTIONAL) ⚠️

- [X] T026 [P] [US3] Unit test for multiple-comparison correction (Bonferroni and Benjamini-Hochberg) in `tests/unit/test_feature_importance.py`
- [X] T027 [P] [US3] Integration test for OOD detection and separate metric reporting in `tests/integration/test_ood_validation.py`

### Implementation for User Story 3

- [X] T028 [US3] Implement `code/validation.py` to extract SHAP values from the best model. <!-- Verification: Verify SHAP values are extracted and reported for top features. -->
- [X] T029 [US3] Implement permutation importance testing with a sufficient number of permutations to ensure statistical stability. The task MUST use Benjamini-Hochberg correction for p < 0.05 significance; report p-values in `data/processed/feature_importance.csv`. **Constraint**: Perform permutations. <!-- Verification: Verify `feature_importance.csv` contains p-values, 1000 permutations were executed, and the selected correction method is documented. -->
- [ ] T030 [US3] Implement external validation: Attempt to load held-out experimental data from literature from `data/raw/literature_validation.csv`. **Logic**: If the file is missing or empty, the task MUST fail with a specific error code. Do NOT proceed with proxy validation. Report separate R²/RMSE for external data in `data/processed/external_metrics.csv`. **Ultimate Failure**: Fail if the literature data file is missing or empty. <!-- Verification: Verify `external_metrics.csv` exists and contains metrics for external data, or the task fails if the file is missing. -->
- [ ] T031 [US3] Implement OOD detection: Flag compositions with elements NOT in the training set (based on T017 dataset) or with a Mahalanobis distance > 3.0 from the training distribution. Add `is_ood` boolean column to `data/processed/descriptors_final.csv`. <!-- Verification: Add `is_ood` boolean column and verify logic. -->
- [X] T032a [US3] Report separate R²/RMSE for in-distribution vs. out-of-distribution predictions (internal split). <!-- Verification: Write in-distribution and OOD metrics to `data/processed/ood_metrics.csv` with columns [split, R2, RMSE]. -->
- [X] T032b [US3] Report separate R²/RMSE for the held-out literature dataset (external validation) distinct from cross-validation metrics. <!-- Verification: Write external validation metrics to `data/processed/external_metrics.csv`. -->
- [X] T033 [US3] Generate ranked list of elemental properties by contribution to `T_d` prediction. <!-- Verification: Write ranked list to `data/processed/feature_ranking.csv` with columns [feature, contribution_score, rank]. -->
- [X] T034 [US3] Write validation report to `data/processed/validation_report.md` including sections: External R²/RMSE, OOD Metrics, Feature Importance, and Permutation P-values. <!-- Verification: Verify `validation_report.md` contains all required sections. -->

**Checkpoint**: All user stories complete; external validation done.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T035a [P] Update `README.md` with TGA uncertainty analysis and instrumentation details
- [X] T035b [P] Update `docs/api.md` with endpoint signatures and data schemas
- [X] T036a [P] Code refactor: Extract retry logic from `data_fetcher.py` to `code/utils/retry.py` (Note: T006 implemented the initial logic; this is a refactor).
- [X] T036b [P] Refactor `data_fetcher.py` to import and use the new `retry.py` module
- [X] T037a [P] Profile pipeline using `cProfile` on `main.py` to identify the top functions by cumulative time; write report to `docs/profiling_report.md`. <!-- Verification: Verify `docs/profiling_report.md` contains the top functions and their cumulative time. -->
- [X] T037b [P] Optimize identified bottlenecks to ensure full pipeline completes within 4 hours (performance goal). <!-- Verification: Verify pipeline runtime report shows <= 4 hours. -->
- [X] T038 [P] Additional unit tests in `tests/unit/`
- [X] T039 Run `quickstart.md` validation
- [X] T040 Verify all artifacts have corresponding SHA-256 hashes in `state/...yaml`
- [X] T051 [P] Implement a runtime monitor in `code/main.py` that logs the elapsed time for each phase and the total pipeline, comparing it against the allocated time budget and writing the result to `data/processed/runtime_report.json`. <!-- Verification: Verify `data/processed/runtime_report.json` contains phase timings, total time, and budget status (pass/fail against the defined time threshold). -->

---

## Phase 7: Instrumentation & Measurement Rigor (Revision: Marie Curie Review)

**Purpose**: Address the specific review concern regarding instrumentation uncertainty and the distinction between correlation and measurement.

**Goal**: Explicitly document the thermogravimetric analyzer (TGA) specifications, measurement precision, and propagate these uncertainties through the analysis to ensure results represent a rigorous measurement study.

### Implementation for Instrumentation Rigor

- [X] T044a [US2] Update `code/model_training.py` to use the calculated uncertainty (σ) for each sample as a weight (`sample_weight` = 1/σ²) for Elastic Net and where supported by RF/GB implementations. <!-- Verification: Verify `model_runs.json` includes `sample_weight` logic and that training logs show weighted loss calculation. -->
- [X] T044b [US2] Verify uncertainty weighting implementation by running a test case with known uncertainties and checking loss calculation.
- [X] T045a [US3] Update `data/processed/validation_report.md` to include a dedicated "Measurement Uncertainty Analysis" section, explicitly stating the TGA models used, their precision, and how uncertainty was weighted in the final model. <!-- Verification: Verify `validation_report.md` contains a section "Measurement Uncertainty Analysis" with TGA model details and uncertainty weighting explanation. -->
- [X] T046a [P] [US3] Write a "Measurement vs. Correlation" narrative in `docs/measurement_rigor.md` explaining how the inclusion of instrument-specific uncertainty transforms the analysis from a simple correlation to a weighted measurement-based regression, referencing the specific TGA constraints. <!-- Verification: Verify `docs/measurement_rigor.md` contains a narrative explaining the shift from correlation to weighted measurement, referencing TGA constraints. -->

---

## Phase 8: Revision: Explicit Instrumentation Traceability (Revision: Marie Curie Review)

**Purpose**: Directly address the Marie Curie review concern that "Without this, the claim is merely a correlation, not a measurement" by ensuring every data point carries explicit, traceable instrumentation metadata.

**Goal**: Create a robust audit trail that links every `T_d` value in the final dataset to the specific TGA instrument, manufacturer, and reported precision used to measure it, ensuring the analysis is grounded in physical measurement standards rather than abstract correlation.

### Implementation for Explicit Instrumentation Traceability

- [X] T047e [US3] Update `data/processed/validation_report.md` to include a "Instrumentation Audit" table listing the distribution of TGA models used across the dataset (e.g., "TA Instruments: 120 entries ", "Mettler Toledo: 80 entries ") and their respective precision ranges. <!-- Verification: Verify `validation_report.md` contains a table with instrument distribution and precision ranges. -->
- [X] T047f [US3] Implement a "Measurement Confidence Score" in `code/validation.py` that calculates a composite score for each prediction based on the known precision of the instrument used for the training data point and the uncertainty propagation model. <!-- Verification: Verify `data/processed/feature_importance.csv` includes a `measurement_confidence_score` column. -->
- [X] T048 [US3] Write a "Measurement Integrity Statement" in `docs/measurement_integrity.md` that explicitly argues why the inclusion of instrument-specific metadata and uncertainty weighting elevates the study from a statistical correlation to a physical measurement analysis, citing the specific TGA models and their precision limits. <!-- Verification: Verify `docs/measurement_integrity.md` contains the argument and references specific instrument models. -->
- [X] T049 [P] Unit test for `instrument_registry.py` to ensure correct precision lookup for known and unknown instruments. <!-- Verification: Verify unit tests pass for all registry lookups. -->
- [X] T050 [P] Integration test for the full instrumentation pipeline: fetch data -> validate instrumentation -> compute uncertainty -> train model -> report audit. <!-- Verification: Verify the pipeline completes without halting on missing instrumentation metadata. -->

---

## Phase 9: Review Action: Instrumentation Fallback Handling (Revision: Marie Curie Review)

**Purpose**: Explicitly address the Marie Curie review concern regarding missing instrumentation data by ensuring the pipeline handles missing data gracefully while maintaining measurement integrity.

**Goal**: Ensure that when instrumentation metadata is missing, the pipeline logs the specific missing entries, applies a documented default precision, and clearly distinguishes these entries in the final analysis to prevent them from being treated as high-precision measurements.

**Note**: Tasks T053 and T054 have been moved to Phase 4 (US2) to ensure they are available for model training. This phase now focuses on reporting and documentation.

### Implementation for Fallback Handling

- [X] T055 [US3] Update `data/processed/validation_report.md` to include a "Data Quality Assessment" section that quantifies the proportion of high-confidence vs. low-confidence measurements and discusses the impact on model generalizability. <!-- Verification: Verify `validation_report.md` contains a "Data Quality Assessment" section with quantitative metrics on confidence distribution. -->

---

## Phase 10: Verification & Testing

**Purpose**: Explicit verification tasks for foundational logic

- [ ] T056 [P] Verify retry logic implementation in `code/utils/data_fetcher.py`. **Verification**: Run a unit test that simulates network failures and verifies that the retry logic implements exponential backoff (e.g., delays following an exponential sequence) and that the total retry time fits within the designated budget. <!-- Requires: T006 -->

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete
- **Instrumentation Rigor (Phase 7)**: Can run in parallel with US1/US2 implementation but must complete before final validation reporting
- **Explicit Instrumentation Traceability (Phase 8)**: Integrated into US1 (T012, T014) to ensure instrumentation validation happens at the source.
- **Review Action: Instrumentation Fallback Handling (Phase 9)**: Depends on Phase 8 completion to ensure fallback logic is in place before applying weights.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output

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
- Phase 7 tasks (T044-T046) can be implemented in parallel with US1/US2/US3 as they focus on schema updates, weighting logic, and documentation
- Phase 8 tasks (T047-T050, T052) are integrated into Phase 3 (US1) to ensure instrumentation validation is enforced at the source.
- Phase 9 tasks (T055) can be implemented in parallel with US3 as they focus on data quality reporting.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data ingestion output schema in tests/contract/test_data_ingestion.py"
Task: "Integration test for API retry logic and error handling in tests/integration/test_api_retries.py"

# Launch all models for User Story 1 together:
Task: "Fetch NREL data (T012a)"
Task: "Fetch Materials Project data (T012b)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 8: Explicit Instrumentation Traceability (Integrated into US1 data ingestion)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (with integrated instrumentation) → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (with integrated instrumentation)
 - Developer B: User Story 2
 - Developer C: User Story 3
 - Developer D: Phase 7 (Instrumentation Rigor)
 - Developer E: Phase 8 (Instrumentation Specifics)
 - Developer F: Phase 9 (Fallback Handling)
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
- **Critical Constraint**: All tasks must run on CPU-only free-tier CI (a minimal number of cores, limited RAM). No GPU/CUDA, no 8-bit quantization, no large LLMs.
- **Critical Constraint**: Real data only. No synthetic/fake datasets. All metrics must be derived from real experimental measurements.
- **Review Action**: T013 and T042 explicitly address the instrumentation metadata requirement; T009b was removed as it was a scope violation.
- **Review Action (Instrumentation)**: T013, T013b, T043, and T044 ensure that both explicit and default uncertainties are propagated to model weighting, transforming the analysis into a rigorous measurement-based study.
- **Review Action (Marie Curie Revision)**: Phase 7 (T044-T046) directly addresses the reviewer's concern that without explicit instrumentation and uncertainty, the claim is merely a correlation. These tasks enforce the documentation of TGA models, precision, and the propagation of measurement error into the regression weights, ensuring the final result is a weighted measurement study.
- **Review Action (Stratification)**: T014b, T020e, and T020f ensure that the `perovskite_family` column is derived and used for stratified cross-validation with specific families [lead-halide, tin-halide, double perovskite], with explicit verification of split balance.
- **Review Action (OOD Validation)**: T030 ensures that external literature data is used for validation, and if unavailable, the task fails, ensuring the validation step never fails silently.
- **Review Action (Explicit Instrumentation Traceability)**: Phase 8 (T047-T050, T052) directly addresses the Marie Curie review concern by enforcing that every data point must have explicit, traceable instrumentation metadata (instrument model, manufacturer, precision) or a default fallback applied during the data fetch (T012), ensuring the analysis is grounded in physical measurement standards.
- **Review Action (Runtime Monitoring)**: T051 ensures that SC-002 can be empirically verified by logging the actual pipeline runtime.
- **Review Action (Permutation Rigor)**: T029 explicitly mandates 1000 permutations to satisfy Constitution Principle VII.
- **Review Action (Data Hygiene)**: T013b and T014b now explicitly create new derived files (`descriptors_v1.csv`, `descriptors_v2.csv`) to satisfy immutable derivation constraints.
- **Review Action (Versioning)**: T004 is now marked complete and placed in Phase 2 to ensure versioning discipline is enforced.
- **Review Action (Fallback Handling)**: Phase 9 (T055) explicitly addresses the handling of missing instrumentation data by generating reports, applying down-weighting, and documenting data quality, ensuring that low-confidence measurements do not skew the results.
- **Review Action (T012d Removal)**: T012d was removed; its logic (dual-source verification) was integrated into T012c, T012d, T012e.
- **Review Action (T053/T054 Ordering)**: T053 and T054 have been moved to Phase 4 to ensure correct dependency flow for model training.
- **Review Action (T016a Threshold)**: T016a now explicitly states 'threshold > 5'.
- **Review Action (T054 Weight)**: T054 now uses a configurable `low_confidence_weight` parameter with a defined default.
- **Review Action (Retry Logic Separation)**: T006 now implements logic only; T056 verifies the exponential backoff behavior, resolving the mixed implementation/verification concern.
- **Review Action (Instrument Registry Source)**: T047c now requires loading the registry from a local file (`data/raw/instrument_registry.csv`) with a defined schema instead of an ambiguous external source, resolving the constraint preservation concern. T052 verifies the loading mechanism and fallback behavior.
