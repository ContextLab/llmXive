# Tasks: Predicting the Impact of Alloying on High-Temperature Oxidation Resistance

**Input**: Design documents from `/specs/001-predicting-oxidation-resistance/`
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

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create directory tree structure `projects/PROJ-277-predicting-oxidation-resistance/` (code/, data/, tests/, logs/)
- [ ] T001b [P] Create empty `__init__.py` files for all Python packages in `projects/PROJ-277-predicting-oxidation-resistance/`
- [ ] T001c [P] Create empty `.gitignore` with Python/DS patterns in `projects/PROJ-277-predicting-oxidation-resistance/`
- [X] T002a [P] Create `requirements.txt` with pinned versions for pandas, scikit-learn, shap, pyyaml, requests, numpy, matplotlib, statsmodels in `projects/PROJ-277-predicting-oxidation-resistance/code/requirements.txt`
- [ ] T002b [P] Create `pyproject.toml` or `setup.cfg` for project metadata in `projects/PROJ-277-predicting-oxidation-resistance/`
- [ ] T003a [P] Configure flake8 and black settings in `projects/PROJ-277-predicting-oxidation-resistance/pyproject.toml`
- [~] T003b [P] Create pre-commit hook configuration for linting in `projects/PROJ-277-predicting-oxidation-resistance/.pre-commit-config.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [~] T004 [P] Create base data models (`AlloySample`, `PredictionResult`, `GapAnalysisReport`) in `projects/PROJ-277-predicting-oxidation-resistance/code/models/__init__.py`. **Schema**: `AlloySample` (elemental_composition: dict, thermodynamic_descriptors: dict, microstructural_features: optional dict, observed_weight_gain: float); `PredictionResult` (predicted_weight_gain: float, confidence_interval: tuple, model_type: string, feature_contributions: dict); `GapAnalysisReport` (composition_only_rmse: float, augmented_rmse: float, error_reduction_pct: float, sensitive_samples: list of IDs).
- [~] T005 [P] Implement configuration management with `--mode` flag (ci/local) and mode-specific constants in `projects/PROJ-277-predicting-oxidation-resistance/code/config.py`
- [~] T006 [P] Setup logging infrastructure and error codes (including `EXIT_CODE_DATA_VALIDATION_FAILURE`) in `projects/PROJ-277-predicting-oxidation-resistance/code/utils/logger.py`
- [~] T007 [P] Create CLI entry point `main.py` with argument parsing in `projects/PROJ-277-predicting-oxidation-resistance/code/main.py`
- [~] T008 [P] Setup directory structure for `data/raw` and `data/processed` in `projects/PROJ-277-predicting-oxidation-resistance/`
- [~] T017 [P] **CRITICAL**: Implement dataset downsampling logic in `projects/PROJ-277-predicting-oxidation-resistance/code/data/processor.py`. **Logic**: If `--mode=ci` and rows > 500, downsample to 500. If `--mode=local` and rows > 1000, downsample to 1000. **Ordering**: This logic MUST execute BEFORE any data processing (T013) or model training (T015) to prevent leakage.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Composition-Only Predictive Screening (Priority: P1) 🎯 MVP

**Goal**: Implement the core screening pipeline to predict oxidation weight gain from elemental composition and thermodynamic descriptors.

**Independent Test**: Upload a CSV of 10 known alloy compositions (no microstructure) and verify the system outputs a CSV with `predicted_weight_gain` and `prediction_uncertainty`.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T009 [P] [US1] Contract test for data fetcher validation (schema, checksums) in `projects/PROJ-277-predicting-oxidation-resistance/tests/contract/test_fetcher.py`
- [~] T041 [P] [US1] Contract test for Synthetic Data Fallback trigger (generation logic, gap report creation) in `projects/PROJ-277-predicting-oxidation-resistance/tests/contract/test_fallback.py`
- [~] T010 [P] [US1] Integration test for full prediction pipeline on synthetic data AND verification of fallback trigger in `projects/PROJ-277-predicting-oxidation-resistance/tests/integration/test_prediction_pipeline.py`

### Implementation for User Story 1

- [~] T011 [US1] Implement `fetcher.py` to download data from NIST/Zenodo URLs with checksum validation in `projects/PROJ-277-predicting-oxidation-resistance/code/data/fetcher.py`
- [~] T012 [US1] Implement `SyntheticDataGenerator` fallback logic for pipeline validation only in `projects/PROJ-277-predicting-oxidation-resistance/code/data/fetcher.py`. **Requirement**: MUST generate and log a formal `logs/data_gap_report.txt` if real data is unavailable.
- [~] T013 [US1] Implement `processor.py` to calculate thermodynamic descriptors (oxide formation enthalpies) and periodic table features (atomic radius, electronegativity, valence electron count) using CPU-efficient lookup tables in `projects/PROJ-277-predicting-oxidation-resistance/code/data/processor.py`. **Dependency**: Requires data from T011/T012 and T017.
- [ ] T040 [US1] Implement data validation logic in `projects/PROJ-277-predicting-oxidation-resistance/code/data/processor.py`. **Logic**: Halt execution immediately with `EXIT_CODE_DATA_VALIDATION_FAILURE` if *any* required predictor (Ni, Cr, Al, weight gain) is missing. If an unknown element is present: if > 0.5 wt%, flag and exclude; if ≤ 0.5 wt%, impute using periodic table average and attach high uncertainty flag (±20%).
- [ ] T044 [US1] Implement imputation logic for unknown elements ≤ 0.5 wt% in `projects/PROJ-277-predicting-oxidation-resistance/code/data/processor.py`. **Logic**: Impute value using periodic table average and attach high uncertainty flag (±20%) to the prediction. This task complements T040.
- [ ] T015 [US1] Implement `trainer.py` with 5x2 Nested Cross-Validation (k=5) for Random Forest, Gradient Boosting, and Gaussian Process models to prevent data leakage in `projects/PROJ-277-predicting-oxidation-resistance/code/models/trainer.py`
- [ ] T036 [US1] Implement Gaussian Process (GP) model training logic specifically in `projects/PROJ-277-predicting-oxidation-resistance/code/models/trainer.py` (distinct from RF/GB).
- [ ] T016 [US1] Implement model selection logic using RMSE to compare all three models (RF, GB, GP) and generate `PredictionResult` objects with confidence intervals in `projects/PROJ-277-predicting-oxidation-resistance/code/models/trainer.py`. **Dependency**: Requires trained models from T015/T036.
- [ ] T018 [US1] Implement prediction output generation (CSV with `predicted_weight_gain` and `prediction_uncertainty`) in `projects/PROJ-277-predicting-oxidation-resistance/code/main.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Microstructural Gap Quantification (Priority: P2)

**Goal**: Quantify the "microstructural effect gap" by comparing composition-only models against models augmented with microstructural features.

**Independent Test**: Run "Gap Analysis" on a dataset with a mix of composition-only and composition+microstructure samples, verifying the system calculates the error reduction (ΔRMSE).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Contract test for gap analysis schema validation in `projects/PROJ-277-predicting-oxidation-resistance/tests/contract/test_gap_analysis.py`
- [ ] T020 [P] [US2] Integration test for gap analysis with insufficient data (n < 50) in `projects/PROJ-277-predicting-oxidation-resistance/tests/integration/test_gap_analysis.py`

### Implementation for User Story 2

- [ ] T021 [US2] Extend `processor.py` to handle optional microstructural features (grain size, precipitate fraction) if present in input data in `projects/PROJ-277-predicting-oxidation-resistance/code/data/processor.py`
- [ ] T022 [US2] Implement `evaluator.py` to perform comparative error analysis (RMSE comparison) between composition-only and augmented models in `projects/PROJ-277-predicting-oxidation-resistance/code/models/evaluator.py`. **Dependency**: Requires extended features from T021 and trained models from T015/T036.
- [ ] T023 [US2] Implement logic to flag "Inconclusive" if microstructural subset size n < 50 and calculate statistical power in `projects/PROJ-277-predicting-oxidation-resistance/code/models/evaluator.py`
- [ ] T024 [US2] Implement logic to identify and flag "High Microstructural Sensitivity" samples (error > 2x median) in `projects/PROJ-277-predicting-oxidation-resistance/code/models/evaluator.py`
- [ ] T025 [US2] Generate `GapAnalysisReport` artifacts including `error_reduction_pct` and `sensitive_samples` list in `projects/PROJ-277-predicting-oxidation-resistance/code/models/evaluator.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Interpretability and Feature Importance (Priority: P3)

**Goal**: Generate SHAP plots and feature importance tables to validate that the model learns physical relationships (Al, Cr influence).

**Independent Test**: Generate SHAP summary plots and verify Al and Cr appear in top 3 features.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Contract test for SHAP report schema in `projects/PROJ-277-predicting-oxidation-resistance/tests/contract/test_shap.py`
- [ ] T027 [P] [US3] Unit test for feature importance ranking logic in `projects/PROJ-277-predicting-oxidation-resistance/tests/unit/test_shap.py`

### Implementation for User Story 3

- [ ] T028 [US3] Implement `shap_plots.py` to generate SHAP summary plots and waterfall plots using CPU-only backend in `projects/PROJ-277-predicting-oxidation-resistance/code/viz/shap_plots.py`. **Dependency**: Requires trained model from T015/T036.
- [ ] T029 [US3] Implement feature importance table generation (top features with mean absolute SHAP values) in `projects/PROJ-277-predicting-oxidation-resistance/code/viz/shap_plots.py`. **Dependency**: Requires trained model from T015/T036.
- [ ] T030 [US3] Implement collinearity check between Al content and Al2O3 enthalpy to prevent independent effect claims in `projects/PROJ-277-predicting-oxidation-resistance/code/viz/shap_plots.py`. **Dependency**: Requires feature matrix from T013/T021.
- [ ] T031 [US3] Implement local explanation generation (waterfall plot) for specific alloy predictions in `projects/PROJ-277-predicting-oxidation-resistance/code/viz/shap_plots.py`. **Dependency**: Requires trained model from T015/T036.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reporting & Output (Cross-Cutting)

**Purpose**: Generate final reports and ensure scientific validity warnings are applied.

- [ ] T032a [US2] Generate `gap_analysis_report.json` artifact (depends on T025) in `projects/PROJ-277-predicting-oxidation-resistance/data/processed/`
- [ ] T032b [US1] Generate `predictions.csv` artifact (depends on T018) in `projects/PROJ-277-predicting-oxidation-resistance/data/processed/`
- [ ] T032c [US3] Generate `shap_summary_plot.png` artifact (depends on T028) in `projects/PROJ-277-predicting-oxidation-resistance/data/processed/`
- [ ] T033 [US1] Append "Scientific Validity Warning" to all reports if synthetic data was used in `projects/PROJ-277-predicting-oxidation-resistance/code/main.py`
- [ ] T034 [P] Log formal deviation report to `logs/data_gap_report.txt` if real data fetch fails in `projects/PROJ-277-predicting-oxidation-resistance/code/data/fetcher.py`
- [ ] T043 [US1] Enforce associational framing for ALL runs (not just synthetic). **Implementation**: Prepend warning header to all JSON/CSV outputs and set metadata flag `framing: associational` in `projects/PROJ-277-predicting-oxidation-resistance/code/main.py`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Reporting (Phase 6)**: Depends on all desired user stories being complete

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
Task: "Contract test for data fetcher validation in tests/contract/test_fetcher.py"
Task: "Contract test for Synthetic Data Fallback trigger in tests/contract/test_fallback.py"
Task: "Integration test for full prediction pipeline on synthetic data in tests/integration/test_prediction_pipeline.py"

# Launch independent implementation tasks (after T017):
Task: "Implement fetcher.py in code/data/fetcher.py"
Task: "Implement SyntheticDataGenerator in code/data/fetcher.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (including T017, T040, T044, T015, T036)
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
 - Developer A: User Story 1 (T017, T011, T012, T040, T044, T013, T015, T036, T016)
 - Developer B: User Story 2 (T021, T022, T023, T024, T025)
 - Developer C: User Story 3 (T028, T029, T030, T031)
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
- **Critical Ordering**: T017 (downsampling) MUST run before T013 (processing) and T015 (training). T016 depends on T015/T036. T022 depends on T021. T028-T031 depend on T015/T036. T032a-c depend on T025, T018, T028 respectively.