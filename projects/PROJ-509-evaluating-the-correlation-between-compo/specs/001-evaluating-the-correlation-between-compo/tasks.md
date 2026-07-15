# Tasks: Evaluating the Correlation Between Compositional Features and Predicted Formation Energy in Inorganic Materials

**Input**: Design documents from `/specs/001-evaluating-the-correlation-between-compo/`
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

- [X] T001 Create project structure per implementation plan (`projects/PROJ-509-evaluating-the-correlation-between-compo/`) by executing: `mkdir -p data/{raw,elemental_properties,processed,evaluation,logs} code tests/contract tests/unit contracts`.
- [X] T002 Create `requirements.txt` at `projects/PROJ-509-evaluating-the-correlation-between-compo/code/` with pinned versions for: `pymatgen`, `scikit-learn`, `pandas`, `numpy`, `matplotlib`, `pyyaml`.
- [X] T003 [P] Configure linting (flake8/black) and formatting tools in `pyproject.toml`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [X] T004 Create `data/` directory structure: `raw/`, `elemental_properties/`, `processed/`, `evaluation/`, `logs/` (if not done in T001).
- [X] T005 [P] Implement `contracts/` directory with `dataset.schema.yaml` and `model_output.schema.yaml` defining expected JSON/CSV schemas.
- [X] T006 [P] Setup `tests/` directory structure: `contract/`, `unit/`.
- [X] T007 Create `code/config.py` with functions `load_paths()` (returns dict of data/code paths) and `load_env()` (loads environment variables) to manage configuration.
- [X] T008 Configure error handling and logging infrastructure in `code/utils/logging.py`.
- [X] T009 [P] Implement `code/utils/sampling.py` with function `sample_by_chemical_family(df, target_rows, random_state)` including type hints, docstrings, and docstring examples. This function performs stratified sampling by the most abundant element.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Descriptor Computation (Priority: P1) 🎯 MVP

**Goal**: Download MP-2020.12.1 dataset, filter for inorganic compounds, compute multiple mean/variance descriptors, and output a clean CSV.

**Independent Test**: Run `code/ingest.py` and `code/descriptors.py` against the Zenodo mirror; {{claim:c_331c9c49}} (Wikidata Q47604, https://www.wikidata.org/wiki/Q47604), no nulls in descriptor columns, and matches `contracts/dataset.schema.yaml`.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAILbefore implementation**

- [X] T010 [P] [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py`.
- [X] T011 [P] [US1] Unit test for descriptor calculation logic (mean/variance of elemental properties) in `tests/unit/test_descriptors.py`.

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/ingest.py` to Download MP-2020.12.1 dataset from Zenodo (DOI: 10.5281/zenodo.4053859) [UNRESOLVED-CLAIM: c_eb27361c — status=not_enough_info], filter for inorganic compounds with complete formation energy/composition, and log excluded rows.
- [X] T013 [US1] Implement stratified sampling logic in `code/ingest.py` (calling `code/utils/sampling.py`) to sample the raw dataset by **Chemical Family** if it exceeds memory threshold. **Output**: Save the sampled raw dataset to `data/processed/sampled_raw_data.csv` and generate a versioned manifest `data/processed/sampling_manifest.json` containing the row count, random seed, and SHA256 checksum. Log sampling stats to `data/logs/sampling.log`.
- [X] T014 [US1] Implement `code/descriptors.py` to load `data/processed/sampled_raw_data.csv` and load elemental properties (electronegativity, radius, valence, melting point, ionization energy) using `pymatgen` or `matminer`.
- [X] T015 [US1] Implement `code/descriptors.py` to compute mean and variance for the 5 descriptors for every compound and handle missing elemental properties by excluding rows.
- [X] T016 [US1] Implement outlier detection in `code/descriptors.py` to calculate 1st and 99th percentiles of formation energy. **Condition**: If any values are outside these bounds, cap them to the bounds. **Output**: Save the resulting dataset (capped or uncapped) to `data/processed/computed_descriptors.csv` and log the count of capped rows to `data/logs/outliers.log`.
- [X] T017 [US1] Implement `code/descriptors.py` to validate the final processed dataset against `contracts/dataset.schema.yaml` and ensure all descriptor columns are non-null numeric values.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Validation (Priority: P2)

**Goal**: Train Random Forest and Gradient Boosting models on CPU, evaluate with R²/MAE/RMSE, and verify stratified split integrity.

**Independent Test**: Run `code/train.py` and `code/evaluate.py`; verify models complete within 3h on 2-core CPU, R² > 0.0, and crystal system distribution TVD ≤ 0.05.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output_schema.py`.
- [ ] T019 [P] [US2] Unit test for stratified split logic (TVD calculation) in `tests/unit/test_split_validation.py`.

### Implementation for User Story 2

- [X] T020 [US2] Implement `code/train.py` to load `data/processed/computed_descriptors.csv` and perform an 80/20 stratified split by **Crystal System** (as required by Spec FR-004) to ensure structural diversity in the validation set.
- [ ] T021 [US2] Implement `code/train.py` to train Random Forest Regressor (`n_estimators=200`, `max_depth=20`) on the training split.
- [ ] T022 [US2] Implement `code/train.py` to train Gradient Boosting Regressor (`n_estimators=100`) on the training split.
- [ ] T023 [US2] Implement `code/evaluate.py` to calculate R², MAE, and RMSE for both models on the validation split.
- [X] T024 [US2] Implement `code/evaluate.py` to calculate Total Variation Distance (TVD) between training and validation crystal system distributions; flag if TVD > 0.05.
- [~] T025 [US2] Implement `code/evaluate.py` to detect overfitting by calculating `overfitting_ratio = train_r2 / val_r2` (handle division by zero). **Output**: Append `overfitting_ratio` to `data/evaluation/model_metrics.json`.
- [ ] T026 [US2] Save model artifacts to `data/evaluation/trained_models.pkl` and metrics to `data/evaluation/model_metrics.json` (Single Source of Truth).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance Ranking and Sensitivity Analysis (Priority: P3)

**Goal**: Extract feature importances, validate with permutation importance, and generate Partial Dependence Plots (PDPs) for top features.

**Independent Test**: Run `code/importance.py` and `code/plots.py`; verify top ranked features, correlation r ≥ 0.8 between methods, and PDPs generated for top-ranked instances.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T032 [P] [US3] Unit test for feature importance correlation calculation in `tests/unit/test_importance_validation.py`.
- [ ] T033 [P] [US3] Integration test for PDP generation in `tests/integration/test_pdp_generation.py`.

### Implementation for User Story 3

- [ ] T038 [US3] Implement `code/importance.py` to extract feature importances from the trained Random Forest model (artifact: `data/evaluation/trained_models.pkl`). **Note**: This task depends on T026.
- [ ] T039 [US3] Implement `code/importance.py` to calculate permutation importance and verify correlation (r ≥ 0.8) with tree-based importances. **Output**: Save the correlation metric `r` and the permutation importance scores to `data/evaluation/permutation_importance.json` to satisfy SC-002.
- [ ] T040 [US3] Implement `code/importance.py` to rank and output the top descriptors to `data/evaluation/feature_ranking.json`.
- [ ] T041 [US3] Implement `code/plots.py` to generate Partial Dependence Plots (PDPs) for the top features using `sklearn.inspection`.
- [ ] T042 [US3] Implement `code/plots.py` to save PDP visualizations to `data/evaluation/pdp_plots/` and include them in the final report.
- [ ] T047 [US3] Implement a Multi-Collinearity Check (VIF) in `code/importance.py` to diagnose descriptor stability. **Threshold**: Flag if VIF > 10. **Output**: Save VIF scores to `data/evaluation/vif_scores.json`. (Diagnostic support for FR-005).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T048 [P] Documentation updates in `README.md` and `quickstart.md` including run instructions for the full pipeline.
- [ ] T049 Code cleanup and refactoring of `code/utils/` modules.
- [ ] T050a [P] Implement chunked reading in `code/descriptors.py` to handle large datasets without loading the entire file into memory at once.
- [ ] T050b [P] Add memory monitoring logic in `code/descriptors.py` to trigger chunked processing if RAM usage > 3GB.
- [ ] T051 [P] Additional unit tests for edge cases (missing elements, extreme outliers) in `tests/unit/`.
- [ ] T052 Run `quickstart.md` validation to ensure end-to-end reproducibility.
- [ ] T053 Generate final `research.md` summary including metrics, VIF results, and PDP interpretations.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (`computed_descriptors.csv`)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output (`trained_models.pkl`)

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
Task: "Contract test for dataset schema validation in tests/contract/test_dataset_schema.py"
Task: "Unit test for descriptor calculation logic in tests/unit/test_descriptors.py"

# Launch all models for User Story 1 together:
Task: "Implement code/ingest.py to download and filter dataset"
Task: "Implement code/descriptors.py to compute features"
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