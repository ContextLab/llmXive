# Tasks: Predicting the Influence of Composition on the Magnetic Hysteresis of Heusler Alloys

**Input**: Design documents from `/specs/001-predict-heusler-hysteresis/`
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

- [ ] T001 Create project structure per implementation plan (`code/`, `tests/`, `data/`, `docs/`)
- [ ] T002 Initialize Python 3.11 project with pinned dependencies in `requirements.txt` (pandas, numpy, scikit-learn, matplotlib, pyyaml, requests, scikit-learn-extra)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `.pre-commit-config.yaml`
- [ ] T004 [P] Setup GitHub Actions workflow for CPU-only CI with a limited number of cores and memory, with a 6h timeout limit

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin. Includes the Verified Accuracy Gate.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] Implement citation validation gate in `code/src/utils/citation_validator.py` to verify all `research.md` citations against primary sources before data ingestion (Constitution Principle II, Plan Phase 0.2). **This task acts as a hard GATE; Phase 3 cannot start until T005 passes.**
- [ ] T006 Create `data/raw/elemental_properties.csv` with fixed periodic table data for specific elements (Mn, Co, Fe, Ga, Al, Ni, Cu, Sn, In) including columns: `element`, `electronegativity`, `atomic_radii`, `valence_electrons` (Source: Pyykko 1988 or similar verified source)
- [ ] T007 Implement `code/src/utils/periodic_table_loader.py` to load `elemental_properties.csv` with strict validation
- [ ] T008 Implement `code/src/utils/logging_config.py` for structured logging and checksum generation
- [ ] T009 Implement `code/src/utils/checksums.py` to calculate SHA256 hashes for `data/raw/` files
- [ ] T010 Define canonical schemas in `specs/001-predict-heusler-hysteresis/contracts/` (`alloy_entry.schema.yaml`, `model_result.schema.yaml`)
- [ ] T011 Implement `code/src/utils/schema_validator.py` to validate processed data against canonical schemas

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Aggregation and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Aggregate scattered experimental measurements from NIST, journal supplements, and manual curation into a single, standardized dataset.

**Independent Test**: Successfully ingest data from multiple distinct sources, standardize composition to atomic fractions, normalize hysteresis parameters, and produce a validated CSV with no DFT targets.

### Implementation for User Story 1 (Must be completed before tests can be executed)

- [ ] T016 [US1] Implement `code/src/ingestion/nist_fetcher.py` to download from NIST Materials Data Repository using specific API endpoint ` (verify URL before use)
- [ ] T017 [US1] Implement `code/src/ingestion/journal_supplement_parser.py` to parse PDF/CSV supplements from 'Acta Materialia' and 'Journal of Alloys and Compounds' (search for 'supplement' or 'dataset' keywords)
- [ ] T018 [US1] Implement `code/src/ingestion/manual_curator.py` to load manually curated data from raw literature
- [ ] T019 [US1] Implement `code/src/preprocessing/composition_parser.py` to convert strings to atomic fractions (≥4 decimal places)
- [ ] T020 [US1] Implement `code/src/preprocessing/unit_normalizer.py` to standardize coercivity (Oe) and saturation magnetization (emu/g)
- [ ] T021 [US1] Implement `code/src/preprocessing/dft_filter.py` to exclude entries with DFT-derived targets (FR-008) and explicitly LOG/FLAG excluded entries before removal
- [ ] T022 [US1] Implement `code/src/preprocessing/listwise_deletion.py` to remove rows if missing rate > 15% (Spec FR-002)
- [ ] T023 [US1] Implement `code/src/preprocessing/mean_imputer.py` to apply mean imputation if missing rate ≤ 15% (Spec FR-002)
- [ ] T024 [US1] Implement `code/src/preprocessing/imputation_orchestrator.py` to calculate missing rate and trigger T022 (>15%) or T023 (≤15%) based on Spec FR-002 logic
- [ ] T025 [US1] Implement `code/src/preprocessing/validator.py` to check for elements not in periodic table and log warnings
- [ ] T026 [US1] Create `code/src/ingestion/ingest_pipeline.py` to orchestrate fetching, parsing, and saving to `data/raw/` with checksums
- [ ] T027 [US1] Create `code/src/preprocessing/preprocess_pipeline.py` to standardize, impute (via Orchestrator), filter, and save to `data/processed/alloys_raw.csv`
- [ ] T028 [US1] Generate `data/processed/completeness_report.json` (SC-004) reporting data proportions per source

### Tests for User Story 1 ⚠️ (Must be written first per TDD, but EXECUTED only after Implementation tasks T016-T028 are complete)

- [ ] T012 [US1] Unit test for composition parser in `code/tests/unit/test_composition_parser.py` (tests "Co2MnGa" -> atomic fractions)
- [ ] T013 [US1] Unit test for unit normalizer in `code/tests/unit/test_unit_normalizer.py` (tests Oe/emu/g conversion)
- [ ] T014 [US1] Integration test for DFT filter in `code/tests/integration/test_dft_filter.py` (ensures DFT targets are excluded)
- [ ] T015 [US1] Integration test for imputation logic in `code/tests/integration/test_imputation_logic.py` (tests Listwise vs Mean selection)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Feature Engineering and Model Training (Priority: P2)

**Goal**: Transform elemental compositions into meaningful descriptors and train regression models (Linear, Random Forest) to quantify the composition-hysteresis relationship.

**Independent Test**: Compute ≥5 descriptors, train models with cross-validation, and produce performance metrics (R², MAE).

### Implementation for User Story 2

- [ ] T031 [P] [US2] Implement `code/src/features/descriptor_calculator.py` to compute: Average Electronegativity, VEC, Atomic Radii Variance, Avg d-electrons, Atomic Size Mismatch (FR-003)
- [ ] T032 [US2] Implement `code/src/features/feature_engineering_pipeline.py` to apply descriptors to `data/processed/alloys_raw.csv` and save to `data/processed/alloys_features.csv`
- [ ] T033 [US2] Implement `code/src/models/linear_regressor.py` for baseline linear regression with hyperparameter tuning
- [ ] T034 [US2] Implement `code/src/models/random_forest_regressor.py` for Random Forest with hyperparameter tuning
- [ ] T035 [US2] Implement `code/src/models/training_pipeline.py` to orchestrate 5-fold CV, GridSearchCV, and save models to `code/models/`
- [ ] T036 [US2] Implement `code/src/models/feature_importance.py` to calculate permutation importance and rank top 3 descriptors
- [ ] T037 [US2] Generate `data/processed/model_metrics.json` with R² and MAE for both models

### Tests for User Story 2 ⚠️ (Must be written first per TDD, but EXECUTED only after Implementation tasks T031-T037 are complete)

- [ ] T029 [P] [US2] Unit test for descriptor calculator in `code/tests/unit/test_descriptor_calculator.py` (tests VEC, electronegativity, etc.)
- [ ] T030 [P] [US2] Integration test for model training pipeline in `code/tests/integration/test_model_training.py` (tests 5-fold CV)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation and Interpretation (Priority: P3)

**Goal**: Validate model performance against a null hypothesis, assess statistical significance, and interpret composition-property relationships.

**Independent Test**: Perform F-test, compute 95% CI via bootstrapping, generate PDPs, and include mandatory limitation reports.

### Implementation for User Story 3

- [ ] T041 [P] [US3] Implement `code/src/validation/null_model_comparison.py` to perform F-test against mean prediction (SC-001)
- [ ] T042 [US3] Implement `code/src/validation/bootstrap_validation.py` to compute a confidence interval for R² with 1000 resamples (SC-002)
- [ ] T043 [US3] Implement `code/src/validation/pdp_generator.py` to generate Partial Dependence Plots for top 3 features (SC-003)
- [ ] T044 [US3] Implement `code/src/validation/stratified_analysis.py` to group by `synthesis_method` and run models within strata (addressing microstructure confounders)
- [ ] T045 [US3] Implement `code/src/validation/stratified_reporter.py` to report stratified results as SUPPLEMENTARY analysis to global SC-006 metrics (Plan Phase 3.3 vs Spec SC-006)
- [ ] T046 [US3] Generate `docs/reports/data_scarcity_warning.md` if N < 50 (FR-008)
- [ ] T047 [US3] Generate `docs/reports/statistical_limitations.md` with mandatory disclaimer: "F-test validates statistical fit, not physical mechanism" (FR-009)
- [ ] T048 [US3] Generate `docs/reports/microstructure_note.md` logging synthesis methods and noting microstructure influence (FR-010)
- [ ] T049 [US3] Implement `code/src/validation/final_evaluator.py` to run held-out test evaluation, calculate F-test p-value and R², enforce SC-006 gate (p < 0.05 AND R² >= 0.6), and generate report regardless of gate result (marking gate status as FAIL/PASS)
- [ ] T050 [US3] Generate `docs/reports/final_report.md` combining all metrics, plots, and disclaimers

### Tests for User Story 3 ⚠️ (Must be written first per TDD, but EXECUTED only after Implementation tasks T041-T050 are complete)

- [ ] T038 [P] [US3] Unit test for F-test calculator in `code/tests/unit/test_f_test.py`
- [ ] T039 [P] [US3] Unit test for bootstrapping CI in `code/tests/unit/test_bootstrap_ci.py`
- [ ] T040 [P] [US3] Integration test for partial dependence plots in `code/tests/integration/test_pdp_generation.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final verification

- [ ] T051 [P] Run outlier detection (Isolation Forest) and sensitivity analysis in `code/src/validation/outlier_detection.py`
- [ ] T052 [P] Update `docs/data_dictionary.md` with field definitions, units, and source metadata
- [ ] T053 [P] Implement `code/src/versioning/state_manager.py` to record artifact hashes in `state/projects/PROJ-393...yaml` (FR-005)
- [ ] T054 [P] Run full pipeline end-to-end test in `code/tests/integration/test_full_pipeline.py`
- [ ] T055 [P] Verify pipeline execution time < 6 hours and memory < 7 GB on local CPU (SC-005)
- [ ] T056 [P] Update `quickstart.md` with instructions to run the full pipeline

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories. Includes Citation Validation Gate (T005).
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output

### Within Each User Story

- **TDD Process**: Tests (e.g., T012-T015) MUST be written (file created) BEFORE implementation code (e.g., T016-T028) is written.
- **Execution Order**: Implementation tasks MUST be completed (code exists) BEFORE their corresponding Test tasks can be executed (even to fail).
- **Visual Order**: In the list below, Implementation tasks are listed BEFORE Test tasks to reflect the execution dependency graph, even though the TDD process dictates writing tests first.
- **Parallelism**: Tests are NOT marked [P] if they depend on implementation code existing. Only tasks with no runtime dependencies are marked [P].

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
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories, includes Citation Gate T005)
3. Complete Phase 3: User Story 1 (Implementation T016-T028, then Tests T012-T015)
4. **STOP and VALIDATE**: Test User Story 1 independently (ingestion, cleaning, standardization)
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
 - Developer A: User Story 1 (Data)
 - Developer B: User Story 2 (Features/Models)
 - Developer C: User Story 3 (Validation/Reports)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies (except for Tests which depend on Impl existence)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- **TDD Process**: Write tests first (file creation), then implement code. Execute tests only after code exists.
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical**: Ensure all data fetchers use real, reachable URLs. Do not fabricate data.
- **Critical**: Ensure all models run on CPU-only CI (no CUDA, no 8-bit quantization).
- **Critical**: Ensure `synthesis_method` is logged as metadata to address microstructure confounders.
- **Critical**: Imputation logic MUST follow Spec FR-002: Listwise (>15%) or Mean (≤15%). No MICE.
- **Critical**: SC-006 (R² ≥ 0.6 AND p < 0.05) is a measurable gate. Report status explicitly.
- **Critical**: Citation validation (T005) is a hard gate in Phase 2. No data ingestion (Phase 3) occurs until T005 passes.