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

- [ ] T001a [P] Create project directories: `code/`, `data/raw/`, `data/processed/`, `tests/`, `docs/`, `state/`
- [ ] T001b [P] Create `code/requirements.txt` with initial dependencies: `pandas`, `scikit-learn`, `requests`, `pyyaml`, `numpy`, `pymatgen`
- [ ] T002 Initialize Python 3.11 project with dependencies (`code/requirements.txt`)
- [ ] T003 [P] Configure linting (flake8/pylint) and formatting (black/isort) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `state_manager.py` to compute SHA-256 hashes for derived artifacts and update `state/...yaml`
- [ ] T005 Create `contracts/descriptor.schema.yaml` defining the schema for `CompositionalDescriptor` entities
- [ ] T006 Implement `code/utils/data_fetcher.py` with retry logic: up to 3 retries with exponential backoff (min, min, 4 min) for API unavailability
- [ ] T007 Implement `code/utils/formula_parser.py` using `pymatgen` for deterministic A/B/X site assignment
- [ ] T008 Setup environment configuration management for API keys (Materials Project, NREL) in `.env`
- [ ] T009 Implement `code/utils/checksum_verifier.py` to validate raw data integrity against source checksums
- [ ] T009b Implement `code/utils/validator.py` to perform 'title-token-overlap' validation (≥ 0.7 threshold) against primary source citations before processing data

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Descriptor Computation (Priority: P1) 🎯 MVP

**Goal**: Download perovskite data, filter for experimental TGA measurements, and compute compositional descriptors.

**Independent Test**: Run on a sample of formulas; verify output CSV contains `formula`, `T_d`, `atomic_fraction_A`, `weighted_ionic_radius`, etc., with non-null values.

### Tests for User Story 1 (OPTIONAL) ⚠️

- [X] T010 [P] [US1] Contract test for data ingestion output schema in `tests/contract/test_data_ingestion.py`
- [X] T011 [P] [US1] Integration test for API retry logic and error handling in `tests/integration/test_api_retries.py`

### Implementation for User Story 1

- [ ] T012a [US1] Fetch data from NREL API, invoke T009b validation, filter for `T_d` (TGA onset), and write to `data/raw/nrel_perovskites.csv` <!-- Requires: T009b -->
- [ ] T012b [US1] Fetch data from Materials Project API, invoke T009b validation, filter for `T_d` (TGA onset), and write to `data/raw/mp_perovskites.csv` <!-- Requires: T009b -->
- [ ] T012c [US1] Merge NREL and Materials Project data (MUST fetch both sources per FR-001): concatenate DataFrames, drop duplicates based on formula and source, log count of removed duplicates, and write final merged dataset to `data/raw/perovskites_merged.csv`
- [ ] T013 [US1] Implement metadata parsing and validation: parse TGA model/precision from source metadata, write structured metadata to `data/raw/metadata.json` and uncertainty flags (default ±10°C) to `data/raw/uncertainty_flags.json`
- [ ] T014 [US1] Implement `code/feature_engineering.py` to compute atomic fractions, weighted averages (ionic radius, electronegativity, formation enthalpy, first ionization energy), and variance metrics; verify 'first ionization energy' column is present; write output to `data/processed/descriptors.csv`
- [ ] T015 [US1] Implement logic to exclude entries with ≥2 missing descriptor values and log exclusion counts
- [X] T016 [US1] Implement VIF diagnostic computation; flag descriptors with VIF > 5 and implement feature removal or Elastic Net fallback; write report to `data/processed/vif_report.csv`
- [ ] T017 [US1] Write final processed dataset to `data/processed/descriptors.csv` including the `T_d_uncertainty` column and update `state/...yaml` with hash

**Checkpoint**: User Story 1 fully functional; dataset ready for modeling.

---

## Phase 4: User Story 2 - Model Training and Cross-Validation (Priority: P2)

**Goal**: Train baseline regressors (RF, GB, Elastic Net) with strict CPU constraints, grid search limits, and uncertainty weighting.

**Independent Test**: Run k-fold CV on a subset of the data, where k is determined by the experimental design.; verify all models complete within 30 mins with R² metrics.

### Tests for User Story 2 (OPTIONAL) ⚠️

- [X] T018 [P] [US2] Unit test for grid search hyperparameter limit enforcement (≤10 combos) in `tests/unit/test_model_training.py`
- [X] T019 [P] [US2] Integration test for full pipeline runtime (must complete ≤ 6 hours) in `tests/integration/test_pipeline_runtime.py`

### Implementation for User Story 2

- [X] T020 [US2] Implement `code/model_training.py` with Random Forest, Gradient Boosting, and Elastic Net using `scikit-learn`; apply `sample_weight` (1/σ) for Elastic Net and RF/GB where supported; ensure all training uses default precision (no 8-bit/4-bit quantization) and CPU-only execution
- [ ] T021 [US2] Update `code/model_training.py` to include stratified KFold logic with `perovskite_family` as the stratification column
- [ ] T022 [US2] Implement grid search with a hard cap of ≤10 hyperparameter combinations per model
- [ ] T023 [US2] Implement metric tracking (RMSE, R², MAE) and logging of best hyperparameters
- [ ] T025 [US2] Save trained models and metrics to `data/processed/model_runs.json` with required keys: `model_type`, `hyperparameters`, `metrics` (R², RMSE, MAE)

**Checkpoint**: User Story 2 complete; best model identified.

---

## Phase 5: User Story 3 - Feature Importance Analysis and External Validation (Priority: P3)

**Goal**: Extract SHAP values, perform permutation testing, and validate on held-out literature data (with proxy fallback).

**Independent Test**: Run SHAP on a test set.; verify top 3 features reported with p-values < 0.05.

### Tests for User Story 3 (OPTIONAL) ⚠️

- [X] T026 [P] [US3] Unit test for multiple-comparison correction (Bonferroni and Benjamini-Hochberg) in `tests/unit/test_feature_importance.py`
- [ ] T027 [P] [US3] Integration test for OOD detection and separate metric reporting in `tests/integration/test_ood_validation.py`

### Implementation for User Story 3

- [ ] T028 [US3] Implement `code/validation.py` to extract SHAP values from the best model
- [ ] T029 [US3] Implement permutation importance testing (a sufficient number of permutations) with Bonferroni or Benjamini-Hochberg correction (default to Benjamini-Hochberg) for p < 0.05 significance; report p-values in `data/processed/feature_importance.csv`
- [ ] T030 [US3] Implement logic to load held-out experimental data from literature (NREL Perovskite Stability Database); if unavailable, implement 'Internal Stratified Validation' (stratified split) as fallback: write split indices to `data/processed/internal_validation_split.yaml` and report metrics to `data/processed/internal_validation_report.md`
- [ ] T031 [US3] Implement OOD detection: Flag compositions with elements/motifs not in training set (based on T017 dataset) and prediction distance (based on T025 model)
- [ ] T032a [US3] Report separate R²/RMSE for in-distribution vs. out-of-distribution predictions (internal split)
- [ ] T032b [US3] Report separate R²/RMSE for the held-out literature dataset (external validation) distinct from cross-validation metrics
- [ ] T033 [US3] Generate ranked list of elemental properties by contribution to `T_d` prediction
- [ ] T034 [US3] Write validation report to `data/processed/validation_report.md` including sections: External R²/RMSE, OOD Metrics, Feature Importance, and Permutation P-values

**Checkpoint**: All user stories complete; external validation done.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035a [P] Update `README.md` with TGA uncertainty analysis and instrumentation details
- [ ] T035b [P] Update `docs/api.md` with endpoint signatures and data schemas
- [ ] T036a [P] Code refactor: Extract retry logic from `data_fetcher.py` to `code/utils/retry.py`
- [ ] T036b [P] Refactor `data_fetcher.py` to import and use the new `retry.py` module
- [ ] T037a [P] Profile pipeline and identify the most significant bottlenecks impacting the runtime target; write report to `docs/profiling_report.md`
- [ ] T037b [P] Optimize identified bottlenecks to ensure full pipeline completes within 6 hours
- [ ] T038 [P] Additional unit tests in `tests/unit/`
- [ ] T039 Run `quickstart.md` validation
- [ ] T040 Verify all artifacts have corresponding SHA-256 hashes in `state/...yaml`

---

## Phase 7: Instrumentation & Measurement Rigor (Revision: Marie Curie Review)

**Purpose**: Address the specific review concern regarding instrumentation uncertainty and the distinction between correlation and measurement.

**Goal**: Explicitly document the thermogravimetric analyzer (TGA) specifications, measurement precision, and propagate these uncertainties through the analysis to ensure results represent a rigorous measurement study.

### Implementation for Instrumentation Rigor

- [ ] T041 [US1] Update `contracts/metadata.schema.yaml` to require explicit fields for `tga_model`, `tga_manufacturer`, `temperature_precision` (±°C), and `heating_rate` (°C/min) for every source dataset entry
- [ ] T042 [US1] Enhance `code/data_ingestion.py` to parse and validate `temperature_precision` from source metadata; if missing, default to the conservative ±10°C bound and log a warning <!-- Requires: T041 -->
- [ ] T043 [US1] Implement `code/utils/uncertainty_propagator.py` to calculate the combined standard uncertainty for `T_d` based on the instrument precision and any reported experimental error
- [ ] T044 [US2] Update `code/model_training.py` to use the calculated uncertainty (`σ`) for each sample as a weight (`sample_weight` = 1/σ²) for Elastic Net and where supported by RF/GB implementations, ensuring high-precision measurements contribute more to the fit
- [ ] T045 [US3] Update `data/processed/validation_report.md` to include a dedicated "Measurement Uncertainty Analysis" section, explicitly stating the TGA models used, their precision, and how uncertainty was weighted in the final model
- [ ] T046 [P] [US3] Write a "Measurement vs. Correlation" narrative in `docs/measurement_rigor.md` explaining how the inclusion of instrument-specific uncertainty transforms the analysis from a simple correlation to a weighted measurement-based regression, referencing the specific TGA constraints

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
- Phase 7 tasks (T041-T046) can be implemented in parallel with US1/US2/US3 as they focus on schema updates, weighting logic, and documentation

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
 - Developer D: Phase 7 (Instrumentation Rigor)
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
- **Review Action**: T013 explicitly addresses the instrumentation metadata requirement; T009b addresses the Constitutional "Verified Accuracy" gate.
- **Review Action (Instrumentation)**: T013 and T020 ensure that both explicit and default uncertainties are propagated to model weighting, transforming the analysis into a rigorous measurement-based study.
- **Review Action (Marie Curie Revision)**: Phase 7 (T041-T046) directly addresses the reviewer's concern that without explicit instrumentation and uncertainty, the claim is merely a correlation. These tasks enforce the documentation of TGA models, precision, and the propagation of measurement error into the regression weights, ensuring the final result is a weighted measurement study.