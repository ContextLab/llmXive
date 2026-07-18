# Tasks: Predicting Phase Transitions in Amorphous Solids Using Machine Learning

**Input**: Design documents from `/specs/001-predicting-phase-transitions/`
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

- [ ] T001.1 Create project directory structure: `projects/PROJ-203-predicting-phase-transitions-in-amorphou/`, `code/`, `data/raw/`, `data/processed/`, `data/logs/`, `artifacts/`, `tests/`
- [ ] T001.2 Create `code/requirements.txt` with pinned dependencies: `numpy`, `pandas`, `scikit-learn`, `scipy`, `matplotlib`, `seaborn`, `shap`, `mdtraj`, `openmm`, `pyyaml`, `lammps`, `datasets`
- [ ] T002 [P] Configure linting (ruff/flake8) and formatting (black) tools in `code/`
- [ ] T001.3 Create `docs/scope_change_request.md` to formally document the reduction of FR-001 target from 500 to 24 compositions due to compute constraints (Pilot Study T001).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Implement `code/config.py` to manage environment variables, paths (`data/raw`, `data/processed`, `models`), and simulation parameters (cooling rate, time steps)
- [X] T004 [P] Create `code/utils/validators.py` for data integrity checks (NaN detection, physical bound validation for descriptors)
- [X] T005 [P] Setup logging infrastructure in `code/utils/logging_config.py` to capture simulation truncations and missing data events
- [ ] T006 Create base data entities (`Composition`, `StructuralDescriptor`, `ThermalProperty`) in `code/models/`
- [X] T007 Implement `code/utils/plots.py` helpers for SHAP and partial dependence visualization
- [ ] T008 Setup directory structure for `data/raw/`, `data/processed/`, `models/`, and `docs/reports/`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Pipeline Execution & Descriptor Generation (Priority: P1) 🎯 MVP

**Goal**: Execute the full data generation pipeline to produce a structured dataset of short-range structural descriptors and compositional features, linked to experimental thermal properties. **Scope**: Pilot Sample of compositions (stratified by family).

**Independent Test**: The pipeline runs end-to-end on a CPU-only environment, producing a single Parquet file where every row contains composition, structural descriptors, and experimental Tg/crystallization labels, with no missing values for required predictors.

### Implementation for User Story 1

- [X] T009 [US1] Implement `code/data/validate_literature_subset.py` to check for the existence and integrity of the hard-coded `data/raw/literature_subset.csv`. **FAIL LOUDLY**: If the file is missing or corrupted, raise `FileNotFoundError` with message "FATAL: literature_subset.csv missing or corrupted" and exit with code 1. Do NOT attempt to fetch from external sources (Zenodo/NIST).
- [X] T010 [US1] Implement `code/data/simulate.py` to run MD simulations (LAMMPS/OpenMM) for the pilot compositions. Enforce a CPU time cap per composition. If exceeded, **truncate trajectory to the final steps** for analysis (per Constitution Principle VII) and flag as "truncated" in metadata. Verify OpenKIM potentials are available.
- [ ] T010.1 [US1] Implement timing logging in `code/data/simulate.py`: Write simulation start/end timestamps and duration for each composition to `data/logs/simulation_times.json` to support SC-005 total pipeline time measurement.
- [ ] T011 [US1] Implement `code/data/extract.py` to generate structural descriptors (RDF peak position/width, bond-angle variance, coordination numbers) from MD trajectories. Log NaNs and mark as "failed".
- [ ] T012 [US1] Implement cooling rate metadata recording in `code/data/extract.py`: Record the actual simulated cooling rate in the intermediate descriptor metadata.
- [ ] T012.1 [US1] Implement the "Timescale Matching Protocol" logic in `code/data/extract.py` and `code/data/merge.py`: Explicitly set the `SRO_Invariance_Assumed` flag in the metadata of intermediate descriptor files and update the final `merged_dataset.parquet` during the merge step to satisfy FR-008's requirement for a protocol, acknowledging the conditional nature of the assumption.
- [ ] T013 [US1] Implement `code/data/merge.py` to join simulation descriptors with experimental labels from `literature_subset.csv`.
- [ ] T013.1 [US1] Implement crystallization labeling logic in `code/data/merge.py`: Apply binary logic (1 if |Tx - Tg| <= 50K, else 0) to the merged dataset [UNRESOLVED-CLAIM: c_d79f25b9 — status=not_enough_info]. **If experimental T_x is missing for a composition, exclude the row; do NOT compute a synthetic label.** Log specific composition IDs for excluded rows.
- [ ] T014 [US1] Save final processed dataset to `data/processed/merged_dataset.parquet` with metadata flags for "truncated" simulations, "failed" runs, and `SRO_Invariance_Assumed`.

**Checkpoint**: User Story 1 should be fully functional and testable independently (producing valid `merged_dataset.parquet`)

---

## Phase 4: User Story 2 - Model Training & Performance Validation (Priority: P2)

**Goal**: Train Random Forest regression and classification models on the generated dataset to predict Tg and crystallization propensity, achieving RMSE ≤15 K and ROC-AUC > 0.7. **Scope**: Pilot Sample of compositions

The research question, method, and references remain unchanged as required..

**Independent Test**: The training script executes on a 2-CPU runner within 6 hours [UNRESOLVED-CLAIM: c_acd04877 — status=not_enough_info], outputting a model file and performance report meeting the RMSE and ROC-AUC targets.

### Implementation for User Story 2

- [ ] T015 [US2] Implement `code/models/train.py` to load `data/processed/merged_dataset.parquet` (which now includes pre-computed labels from T013.1) and split data (stratified by chemical family) into training/test sets.
- [ ] T016 [US2] Implement Random Forest regression training in `code/models/train.py` with hyperparameter grid search (capped to complete within 2 hours). target: RMSE ≤15 K [UNRESOLVED-CLAIM: c_b822fd6d — status=not_enough_info].
- [ ] T017 [US2] Implement Random Forest classifier training in `code/models/train.py` using the pre-computed crystallization labels from `data/processed/merged_dataset.parquet`. Ensure the confusion matrix is saved to verify the "low stability" labeling logic.
- [ ] T018 [US2] Implement k-fold cross-validation in `code/models/train.py` and save `models/tg_regressor.pkl` and `models/crystallization_classifier.pkl`.
- [ ] T019 [US2] Implement Sensitivity Analysis in `code/models/evaluate.py` varying the crystallization threshold across the specific range: **25K, 50K, 75K, 100K**. Report FPR, Class Balance, and accuracy for each step to distinguish model instability from threshold arbitrariness as per FR-006. Output `data/processed/sensitivity_report.json`. **Prerequisite**: Must consume `data/processed/merged_dataset.parquet` (T014).
- [ ] T020 [US2] Generate `docs/reports/metrics.json` containing RMSE, ROC-AUC, and cross-validation fold scores (SC-001, SC-002).
- [ ] T021 [US2] Implement total pipeline timing aggregation in `code/utils/timing.py`: Read `data/logs/simulation_times.json` (T010.1) and training logs to compute total end-to-end wall-clock time. Verify ≤6 hour limit (SC-005) and output `docs/reports/pipeline_timing.json`.
- [ ] T022 [US2] Implement Null Model & Permutation Test in `code/models/evaluate.py`: Train a mean predictor baseline and run a permutation test (sufficient shuffles) to establish statistical significance for the small sample size (N=24) [UNRESOLVED-CLAIM: c_8040f5d3 — status=not_enough_info] as required by the risk mitigation for SC-001. Output `docs/reports/null_model_report.json`.
- [ ] T023 [US2] Implement Collinearity Report generation in `code/models/evaluate.py` to calculate VIF for all predictors and {{claim:c_23af8af6}} (Wikidata Q113106917, https://www.wikidata.org/wiki/Q113106917), outputting `docs/reports/collinearity_report.json` (FR-007). **Prerequisite**: Must consume `data/processed/merged_dataset.parquet` (T014).

**Checkpoint**: User Stories 1 AND 2 should both work independently; model artifacts and metrics reports generated.

---

## Phase 5: User Story 3 - Interpretability & Cross-Family Analysis (Priority: P3)

**Goal**: Generate SHAP values to rank structural descriptors and visualize family-specific vs. universal predictors. **Scope**: Pilot Sample of 24 compositions.

**Independent Test**: Analysis script generates SHAP summary plots and partial dependence plots distinguishing top predictors for each chemical family.

### Implementation for User Story 3

- [ ] T024 [US3] Implement SHAP value computation in `code/models/evaluate.py` for both regressor and classifier, stratified by chemical family (oxide, sulfide, organic) [UNRESOLVED-CLAIM: c_87022f35 — status=not_enough_info].
- [ ] T025 [US3] Generate SHAP summary plots and ranked feature importance lists for each family in `docs/reports/shap_plots/`.
- [ ] T026 [US3] Implement partial dependence plots for top predictors per family to verify monotonic/non-linear relationships with Tg.
- [ ] T027 [US3] Implement multiple-comparison correction (Bonferroni/FDR) logic in `code/models/evaluate.py` when comparing feature importance across families (FR-005).
- [ ] T028 [US3] Generate final report identifying universal predictors vs. family-specific drivers in `docs/reports/interpretability_report.md`.
- [ ] T029 [US3] Verify statistical significance of family differences and log confidence intervals for top descriptors (SC-003).

**Checkpoint**: All user stories should now be independently functional; interpretability analysis complete.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 [P] Documentation updates in `docs/` including `quickstart.md` for running the pipeline
- [ ] T031 Code cleanup and refactoring in `code/`
- [ ] T032 Performance optimization for data loading and SHAP calculation
- [ ] T033 [P] Additional unit tests for data validators and labeling logic in `tests/unit/`
- [ ] T034 [P] Run `quickstart.md` validation: **execute the end-to-end pipeline script defined in quickstart.md and verify the output Parquet file** is valid and complete.

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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **Produces the dataset.**
- **User Story 2 (P2)**: Depends on US1 completion. **Consumes the dataset to train models.**
- **User Story 3 (P3)**: Depends on US2 completion (requires trained models). **Analyzes model outputs.**

### Within Each User Story

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
# Launch data validation and simulation setup in parallel:
Task: "Implement code/data/validate_literature_subset.py to check static file"
Task: "Implement code/data/simulate.py to run MD simulations"

# Launch descriptor extraction and validation in parallel:
Task: "Implement code/data/extract.py to generate descriptors"
Task: "Implement code/utils/validators.py for collinearity diagnostics"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify `merged_dataset.parquet` is valid and complete)
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
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Model Training) - *Wait for US1 data*
 - Developer C: User Story 3 (Interpretability) - *Wait for US2 models*
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
- **Critical Data Rule**: `code/data/validate_literature_subset.py` MUST fail loudly if `literature_subset.csv` is missing; no synthetic fallbacks allowed.
- **Small Sample Size Mitigation**: The project uses N=24 compositions. Tasks T022 (Null Model/Permutation Test) and T023 (Collinearity Report) are mandatory and MUST be executed in Phase 4 after data generation to ensure statistical validity.
- **Timescale Matching**: Task T012.1 implements the protocol to record and flag the cooling rate assumption, satisfying FR-008 without claiming impossible physical alignment.
- **Scope Change**: Task T001.3 documents the reduction from 500 to 24 compositions.
- **Total Pipeline Time**: Task T021 aggregates simulation (T010.1) and training times to verify SC-005.