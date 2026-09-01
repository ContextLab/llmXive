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
- [X] T006 Implement `code/utils/data_fetcher.py` with retry logic: up to 3 retries with exponential backoff (min, min, 4 min) for API unavailability
- [X] T007 Implement `code/utils/formula_parser.py` using `pymatgen` for deterministic A/B/X site assignment
- [X] T008 Setup environment configuration management for API keys (Materials Project, NREL) in `.env`
- [X] T009 Implement `code/utils/checksum_verifier.py` to validate raw data integrity against source checksums
- [X] T041 [P] Update `contracts/metadata.schema.yaml` to require explicit fields for `tga_model`, `tga_manufacturer`, `temperature_precision` (±°C), and `heating_rate` (°C/min) for every source dataset entry <!-- Verification: Verify `contracts/metadata.schema.yaml` contains required fields and validate against a sample JSON -->
- [X] T042 [P] Implement `code/utils/uncertainty_parser.py` to parse `temperature_precision` from source metadata; if missing, default to ±10°C and log a warning
- [X] T043 [P] Implement `code/utils/uncertainty_propagator.py` to calculate the combined standard uncertainty for `T_d` based on the instrument precision and any reported experimental error

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Descriptor Computation (Priority: P1) 🎯 MVP

**Goal**: Download perovskite data, filter for experimental TGA measurements, and compute compositional descriptors.

**Independent Test**: Run on a sample of formulas; verify output CSV contains `formula`, `T_d`, `atomic_fraction_A`, `weighted_ionic_radius`, etc., with non-null values.

### Tests for User Story 1 (OPTIONAL) ⚠️

- [X] T010 [P] [US1] Contract test for data ingestion output schema in `tests/contract/test_data_ingestion.py`
- [X] T011 [P] [US1] Integration test for API retry logic and error handling in `tests/integration/test_api_retries.py`

### Implementation for User Story 1

- [X] T012a [US1] Fetch data from NREL API, invoke T009 validation, filter for `T_d` (TGA onset), and write to `data/raw/nrel_perovskites.csv`. <!-- Verification: Verify file exists, row count >= 200, and columns [formula, T_d, ...] are present. --> <!-- Requires: T009 -->
- [X] T012b [US1] Fetch data from Materials Project API, invoke T009 validation, filter for `T_d` (TGA onset), and write to `data/raw/mp_perovskites.csv`. <!-- Verification: Verify file exists, row count >= 200, and columns [formula, T_d, ...] are present. --> <!-- Requires: T009 -->
- [X] T012c [US1] Merge NREL and Materials Project data (MUST fetch both sources per FR-001): concatenate DataFrames, drop duplicates based on formula and source, log count of removed duplicates, and write final merged dataset to `data/raw/perovskites_merged.csv`. <!-- Verification: Verify `data/raw/perovskites_merged.csv` exists with row count = sum of inputs minus duplicates and log specific duplicate count. -->
- [X] T013 [US1] Implement metadata parsing and validation: parse TGA model/precision from source metadata using T042, write structured metadata to `data/raw/metadata.json` and uncertainty flags to `data/raw/uncertainty_flags.json`. <!-- Requires: T042 -->
- [X] T013b [US1] Implement logic to extract `temperature_precision` from T013 output, calculate `sigma` using T043, and write `T_d_uncertainty` column to `data/processed/descriptors.csv`. <!-- Requires: T012a, T012b, T043, T014, T014b --> <!-- Verification: Verify `T_d_uncertainty` column is present in `data/processed/descriptors.csv` and values are non-null. -->
- [X] T014 [US1] Implement `code/feature_engineering.py` to compute atomic fractions, weighted averages (ionic radius, electronegativity, formation enthalpy, first ionization energy), and variance metrics; verify 'first ionization energy' column is present; write output to `data/processed/descriptors.csv`. <!-- Verification: Verify output CSV contains columns [atomic_fraction_A, weighted_ionic_radius, ...] with non-null values. -->
- [X] T014b [US1] Implement logic to derive `perovskite_family` (lead-halide, tin-halide, double perovskite) from A/B/X site elements in T014 output; write to `data/processed/descriptors.csv`. <!-- Requires: T014 --> <!-- Verification: Verify `perovskite_family` column has values in [lead-halide, tin-halide, double perovskite]. -->
- [X] T015a [US1] Implement logic to exclude entries with >= 2 missing descriptor values and log exclusion counts. <!-- Verification: Log exclusion count to `data/processed/exclusion_log.csv` and verify count matches expected threshold. -->
- [X] T016a [US1] Implement `code/utils/vif_calculator.py` to compute VIF for all descriptors; write report to `data/processed/vif_report.csv`. <!-- Verification: Verify `vif_report.csv` contains VIF values for all descriptors. -->
- [X] T016b [US1] Implement logic to flag descriptors with VIF > 5 for review; log decision rationale to `data/processed/vif_decision_log.csv`. <!-- Verification: Verify `vif_decision_log.csv` contains flagged descriptors and rationale. -->
- [X] T016c [US1] Unit test for VIF diagnostic computation and feature removal logic in `tests/unit/test_vif.py`. <!-- Requires: T016a, T016b -->
- [X] T017 [US1] Write final processed dataset to `data/processed/descriptors.csv` including the `T_d_uncertainty` and `perovskite_family` columns and update `state/...yaml` with hash.

**Checkpoint**: User Story 1 fully functional; dataset ready for modeling.

---

## Phase 4: User Story 2 - Model Training and Cross-Validation (Priority: P2)

**Goal**: Train baseline regressors (RF, GB, Elastic Net) with strict CPU constraints, grid search limits, and uncertainty weighting.

**Independent Test**: Run k-fold CV on a subset of the data, where k is determined by the experimental design.; verify all models complete within 30 mins with R² metrics.

### Tests for User Story 2 (OPTIONAL) ⚠️

- [X] T018 [P] [US2] Unit test for grid search hyperparameter limit enforcement (<= 10 combos) in `tests/unit/test_model_training.py`
- [X] T019 [P] [US2] Integration test for full pipeline runtime (must complete <= 4 hours) in `tests/integration/test_pipeline_runtime.py`

### Implementation for User Story 2

- [X] T020a [US2] Implement `code/model_training.py` with Random Forest, Gradient Boosting, and Elastic Net using `scikit-learn`; ensure all training uses default precision (no 8-bit/4-bit quantization) and CPU-only execution. <!-- Requires: T014b, T013b -->
- [X] T020b [US2] Implement `sample_weight` (1/σ²) for uncertainty weighting using `T_d_uncertainty` from T013b in `code/model_training.py`. <!-- Requires: T013b --> <!-- Verification: Verify `model_runs.json` includes `sample_weight` logic and that training logs show weighted loss calculation. -->
- [X] T020c [US2] Implement stratified KFold logic using `perovskite_family` column from T014b in `code/model_training.py`. <!-- Requires: T014b -->
- [X] T022 [US2] Implement grid search with a hard cap of <= 10 hyperparameter combinations per model. <!-- Verification: Verify `model_runs.json` shows <= 10 combinations per model and assert max iterations in logs. -->
- [X] T023 [US2] Implement metric tracking (RMSE, R², MAE) and logging of best hyperparameters. <!-- Verification: Verify metrics are logged for each fold and model. -->
- [X] T025 [US2] Save trained models and metrics to `data/processed/model_runs.json` with required keys: `model_type`, `hyperparameters`, `metrics` (R², RMSE, MAE). <!-- Verification: Verify `model_runs.json` exists and contains required keys. -->

**Checkpoint**: User Story 2 complete; best model identified.

---

## Phase 5: User Story 3 - Feature Importance Analysis and External Validation (Priority: P3)

**Goal**: Extract SHAP values, perform permutation testing, and validate on held-out literature data (with proxy fallback).

**Independent Test**: Run SHAP on a test set.; verify top 3 features reported with p-values < 0.05.

### Tests for User Story 3 (OPTIONAL) ⚠️

- [X] T026 [P] [US3] Unit test for multiple-comparison correction (Bonferroni and Benjamini-Hochberg) in `tests/unit/test_feature_importance.py`
- [X] T027 [P] [US3] Integration test for OOD detection and separate metric reporting in `tests/integration/test_ood_validation.py`

### Implementation for User Story 3

- [X] T028 [US3] Implement `code/validation.py` to extract SHAP values from the best model. <!-- Verification: Verify SHAP values are extracted and reported for top features. -->
- [X] T029 [US3] Implement permutation importance testing with a sufficient number of permutations with Bonferroni or Benjamini-Hochberg correction (default to Benjamini-Hochberg) for p < 0.05 significance; report p-values in `data/processed/feature_importance.csv`. <!-- Verification: Verify `feature_importance.csv` contains p-values and that A sufficient number of permutations were used.. -->
- [X] T030 [US3] Implement logic to load held-out experimental data from literature (NREL Perovskite Stability Database or specific literature source). If unavailable, log an error and proceed with internal OOD split (no hard failure). Write error/status to `data/processed/validation_status.json`. <!-- Verification: If data unavailable, raise `FileNotFoundError` with message 'External validation data missing' and write error to `data/processed/validation_status.json`. -->
- [X] T031 [US3] Implement OOD detection: Flag compositions with elements/motifs not in training set (based on T017 dataset) and prediction distance (based on T025 model). <!-- Verification: Add `is_ood` boolean column to `data/processed/descriptors.csv` and verify logic. -->
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
- [X] T036a [P] Code refactor: Extract retry logic from `data_fetcher.py` to `code/utils/retry.py`
- [X] T036b [P] Refactor `data_fetcher.py` to import and use the new `retry.py` module
- [X] T037a [P] Profile pipeline and identify the most significant bottlenecks impacting the runtime target; write report to `docs/profiling_report.md`
- [X] T037b [P] Optimize identified bottlenecks to ensure full pipeline completes within 4 hours
- [X] T038 [P] Additional unit tests in `tests/unit/`
- [X] T039 Run `quickstart.md` validation
- [X] T040 Verify all artifacts have corresponding SHA-256 hashes in `state/...yaml`

---

## Phase 7: Instrumentation & Measurement Rigor (Revision: Marie Curie Review)

**Purpose**: Address the specific review concern regarding instrumentation uncertainty and the distinction between correlation and measurement.

**Goal**: Explicitly document the thermogravimetric analyzer (TGA) specifications, measurement precision, and propagate these uncertainties through the analysis to ensure results represent a rigorous measurement study.

### Implementation for Instrumentation Rigor

- [X] T044a [US2] Update `code/model_training.py` to use the calculated uncertainty (σ) for each sample as a weight (`sample_weight` = 1/σ²) for Elastic Net and where supported by RF/GB implementations. <!-- Verification: Verify `model_runs.json` includes `sample_weight` logic and that training logs show weighted loss calculation. -->
- [X] T044b [US2] Verify uncertainty weighting implementation by running a test case with known uncertainties and checking loss calculation.
- [X] T045a [US3] Update `data/processed/validation_report.md` to include a dedicated "Measurement Uncertainty Analysis" section, explicitly stating the TGA models used, their precision, and how uncertainty was weighted in the final model. <!-- Verification: Verify `validation_report.md` contains a section "Measurement Uncertainty Analysis" with TGA model details and uncertainty weighting explanation. -->
- [X] T045b [US3] Verify the "Measurement Uncertainty Analysis" section is present and accurate.
- [X] T046a [P] [US3] Write a "Measurement vs. Correlation" narrative in `docs/measurement_rigor.md` explaining how the inclusion of instrument-specific uncertainty transforms the analysis from a simple correlation to a weighted measurement-based regression, referencing the specific TGA constraints. <!-- Verification: Write `docs/measurement_rigor.md` containing a narrative explaining the shift from correlation to weighted measurement, referencing TGA constraints. -->
- [X] T046b [P] [US3] Verify the "Measurement vs. Correlation" narrative is present and accurate.

---

## Phase 8: Revision: Explicit Instrumentation Traceability (Revision: Marie Curie Review)

**Purpose**: Directly address the Marie Curie review concern that "Without this, the claim is merely a correlation, not a measurement" by ensuring every data point carries explicit, traceable instrumentation metadata.

**Goal**: Create a robust audit trail that links every `T_d` value in the final dataset to the specific TGA instrument, manufacturer, and reported precision used to measure it, ensuring the analysis is grounded in physical measurement standards rather than abstract correlation.

### Implementation for Explicit Instrumentation Traceability

- [ ] T047a [US1] Enhance `code/utils/data_fetcher.py` to extract and validate `instrument_model` and `manufacturer` fields from source metadata (NREL/Materials Project) during the initial fetch. If these fields are missing, the task must raise a `MissingInstrumentationError` and halt processing for that specific entry, logging the formula to `data/raw/instrumentation_failures.log`. <!-- Verification: Verify that `data/raw/instrumentation_failures.log` exists and contains entries for any formula where instrumentation metadata was missing. --> <!-- Requires: T012a, T012b -->
- [ ] T047b [US1] Update `contracts/metadata.schema.yaml` to make `instrument_model` and `manufacturer` REQUIRED fields (not optional) for any entry to be included in the final training set. <!-- Verification: Verify schema validation fails for any JSON object missing these fields. -->
- [ ] T047c [US1] Implement `code/utils/instrument_registry.py` to maintain a lookup table of known TGA instruments (e.g., "TA Instruments Q500", "Mettler Toledo TGA/DSC 3+") with their standard precision specifications (±°C) if the source metadata does not explicitly state the precision. <!-- Verification: Verify `instrument_registry.py` contains at least 5 common TGA models with documented precision values. -->
- [ ] T047d [US1] Modify `code/feature_engineering.py` to append `instrument_model` and `manufacturer` as columns to `data/processed/descriptors.csv` for every row, ensuring the final dataset is fully instrument-annotated. <!-- Verification: Verify `data/processed/descriptors.csv` contains `instrument_model` and `manufacturer` columns with no null values. -->
- [ ] T047e [US3] Update `data/processed/validation_report.md` to include a "Instrumentation Audit" table listing the distribution of TGA models used across the dataset (e.g., "TA Instruments: 120 entries", "Mettler Toledo: 80 entries") and their respective precision ranges. <!-- Verification: Verify `validation_report.md` contains a table with instrument distribution and precision ranges. -->
- [ ] T047f [US3] Implement a "Measurement Confidence Score" in `code/validation.py` that calculates a composite score for each prediction based on the known precision of the instrument used for the training data point and the uncertainty propagation model. <!-- Verification: Verify `data/processed/feature_importance.csv` includes a `measurement_confidence_score` column. -->
- [ ] T048 [US3] Write a "Measurement Integrity Statement" in `docs/measurement_integrity.md` that explicitly argues why the inclusion of instrument-specific metadata and uncertainty weighting elevates the study from a statistical correlation to a physical measurement analysis, citing the specific TGA models and their precision limits. <!-- Verification: Verify `docs/measurement_integrity.md` contains the argument and references specific instrument models. -->
- [ ] T049 [P] Unit test for `instrument_registry.py` to ensure correct precision lookup for known and unknown instruments. <!-- Verification: Verify unit tests pass for all registry lookups. -->
- [ ] T050 [P] Integration test for the full instrumentation pipeline: fetch data -> validate instrumentation -> compute uncertainty -> train model -> report audit. <!-- Verification: Verify the pipeline completes without `MissingInstrumentationError` on the provided test dataset. -->

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
- **Explicit Instrumentation Traceability (Phase 8)**: Must run after Phase 2 (Foundational) and before Phase 3 (US1) data ingestion to ensure instrumentation validation happens at the source.

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
- Phase 8 tasks (T047-T050) must be completed before Phase 3 (US1) data ingestion to ensure instrumentation validation is enforced at the source.

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
3. Complete Phase 8: Explicit Instrumentation Traceability (MUST complete before US1 data ingestion)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Complete Phase 8: Explicit Instrumentation Traceability (Enforce instrumentation at source)
3. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
4. Add User Story 2 → Test independently → Deploy/Demo
5. Add User Story 3 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: Phase 8 (Explicit Instrumentation Traceability)
 - Developer B: User Story 1
 - Developer C: User Story 2
 - Developer D: User Story 3
 - Developer E: Phase 7 (Instrumentation Rigor)
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
- **Review Action (Stratification)**: T014b and T020 ensure that the `perovskite_family` column is derived and used for stratified cross-validation.
- **Review Action (OOD Validation)**: T030 ensures that external literature data is used for validation, failing if unavailable, rather than using an invalid internal split.
- **Review Action (Explicit Instrumentation Traceability)**: Phase 8 (T047-T050) directly addresses the Marie Curie review concern by enforcing that every data point must have explicit, traceable instrumentation metadata (instrument model, manufacturer, precision) before it can be included in the training set. This ensures the analysis is grounded in physical measurement standards.
