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

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-203-predicting-phase-transitions-in-amorphou/`)
- [ ] T002 Initialize Python 3.11 project with dependencies: `numpy`, `pandas`, `scikit-learn`, `scipy`, `matplotlib`, `seaborn`, `shap`, `mdtraj`, `openmm`, `pyyaml` in `code/requirements.txt`
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `code/config.py` to manage environment variables, paths (`data/raw`, `data/processed`, `models`), and simulation parameters (cooling rate, time steps)
- [ ] T005 [P] Create `code/utils/validators.py` for data integrity checks (NaN detection, physical bound validation for descriptors)
- [ ] T006 [P] Setup logging infrastructure in `code/utils/logging_config.py` to capture simulation truncations and missing data events
- [ ] T007 Create base data entities (`Composition`, `StructuralDescriptor`, `ThermalProperty`) in `code/models/`
- [ ] T008 Implement `code/utils/plots.py` helpers for SHAP and partial dependence visualization
- [ ] T009 Setup directory structure for `data/raw/`, `data/processed/`, `models/`, and `docs/reports/`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Pipeline Execution & Descriptor Generation (Priority: P1) 🎯 MVP

**Goal**: Execute the full data generation pipeline to produce a structured dataset of short-range structural descriptors and compositional features, linked to experimental thermal properties.

**Independent Test**: The pipeline runs end-to-end on a CPU-only environment, producing a single Parquet file where every row contains composition, structural descriptors, and experimental Tg/crystallization labels, with no missing values for required predictors.

### Implementation for User Story 1

- [ ] T010 [US1] Implement `code/data/download.py` to fetch experimental Tg/Tx data from verified sources (Zenodo "Glass Data" or NIST). **FAIL LOUDLY** if real data fetch fails: raise `FileNotFoundError` with message "Real data fetch failed: <source>" and log to `logs/data_fetch.log`; do NOT use synthetic fallbacks.
- [ ] T011 [US1] Implement `code/data/simulate.py` to run MD simulations (LAMMPS/OpenMM) for a curated list of compositions. Enforce a fixed CPU time cap per composition.; if exceeded, **truncate trajectory to the final portion of steps** for analysis (per Constitution Principle VII) and flag as "truncated" in metadata.
- [ ] T012 [US1] Implement `code/data/extract.py` to generate structural descriptors (RDF peak position/width, bond-angle variance, coordination numbers) from MD trajectories.
- [ ] T013 [US1] Implement cooling rate metadata recording in `code/data/simulate.py`: **Do NOT attempt to implement a timescale matching protocol** to align MD cooling rate with experimental DSC rates (as this is physically impossible per spec assumptions). Instead, record the actual simulated cooling rate in metadata and explicitly acknowledge the "Cooling-Rate Invariance" assumption.
- [ ] T014 [US1] Implement `code/data/merge.py` to join simulation descriptors with experimental labels. **Implement crystallization labeling logic here**: label as 1 if experimental Tx (fetched in T010) is within 50 K of Tg, else 0. **If experimental T_x is missing for a composition (per T010 failure), exclude the row; do NOT compute a synthetic label.** Log specific composition IDs for excluded rows.
- [ ] T015 [US1] Implement collinearity diagnostics (VIF calculation) in `code/utils/validators.py` to verify no predictor is definitionally derived from the target (FR-007).
- [ ] T016 [US1] Save final processed dataset to `data/processed/descriptors.parquet` with metadata flags for "truncated" simulations and "failed" runs.

**Checkpoint**: User Story 1 should be fully functional and testable independently (producing valid `descriptors.parquet`)

---

## Phase 4: User Story 2 - Model Training & Performance Validation (Priority: P2)

**Goal**: Train Random Forest regression and classification models on the generated dataset to predict Tg and crystallization propensity, achieving RMSE ≤15 K and ROC-AUC > 0.7.

**Independent Test**: The training script executes on a 2-CPU runner within 6 hours, outputting a model file and performance report meeting the RMSE and ROC-AUC targets.

### Implementation for User Story 2

- [ ] T017 [US2] Implement `code/models/train.py` to load `data/processed/descriptors.parquet` (which now includes pre-computed labels from T014) and split data (stratified by chemical family) into training/test sets.
- [ ] T018 [US2] Implement Random Forest regression training in `code/models/train.py` with hyperparameter grid search (capped to complete within 2 hours). Target: RMSE ≤15 K.
- [ ] T019 [US2] Implement Random Forest classifier training in `code/models/train.py` using the pre-computed crystallization labels from `data/processed/descriptors.parquet`. Ensure the confusion matrix is saved to verify the "low stability" labeling logic.
- [ ] T020 [US2] Implement k-fold cross-validation in `code/models/train.py` and save `models/tg_regressor.pkl` and `models/crystallization_classifier.pkl`.
- [ ] T021 [US2] Implement sensitivity analysis in `code/models/evaluate.py` varying the crystallization threshold across a **specific range: low to high temperatures with moderate increments**. Report FPR, Class Balance, and accuracy for each step **to distinguish model instability from threshold arbitrariness as per FR-006**.
- [ ] T022 [US2] Generate `docs/reports/metrics.json` containing RMSE, ROC-AUC, and cross-validation fold scores (SC-001, SC-002).
- [ ] T023 [US2] Implement timing logger in `code/models/train.py` to record total wall-clock time and verify ≤6 hour limit (SC-005).

**Checkpoint**: User Stories 1 AND 2 should both work independently; model artifacts and metrics reports generated.

---

## Phase 5: User Story 3 - Interpretability & Cross-Family Analysis (Priority: P3)

**Goal**: Generate SHAP values to rank structural descriptors and visualize family-specific vs. universal predictors.

**Independent Test**: Analysis script generates SHAP summary plots and partial dependence plots distinguishing top predictors for each chemical family.

### Implementation for User Story 3

- [ ] T024 [US3] Implement SHAP value computation in `code/models/evaluate.py` for both regressor and classifier, stratified by chemical family (oxide, sulfide, organic).
- [ ] T025 [US3] Generate SHAP summary plots and ranked feature importance lists for each family in `docs/reports/shap_plots/`.
- [ ] T026 [US3] Implement partial dependence plots for top predictors per family to verify monotonic/non-linear relationships with Tg.
- [ ] T027 [US3] Implement multiple-comparison correction (Bonferroni/FDR) in `code/models/evaluate.py` when comparing feature importance across families (FR-005).
- [ ] T028 [US3] Generate final report identifying universal predictors vs. family-specific drivers in `docs/reports/interpretability_report.md`.
- [ ] T029 [US3] Verify statistical significance of family differences and log confidence intervals for top descriptors (SC-003).
- [ ] T034 [US3] Implement SHAP value computation in `code/models/evaluate.py` for both regressor and classifier, stratified by chemical family (oxide, sulfide, organic). **Note: Renamed from T023 to resolve ID collision with Phase 4 T023.**

**Checkpoint**: All user stories should now be independently functional; interpretability analysis complete.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 [P] Documentation updates in `docs/` including `quickstart.md` for running the pipeline
- [ ] T031 Code cleanup and refactoring in `code/`
- [ ] T032 Performance optimization for data loading and SHAP calculation
- [ ] T033 [P] Additional unit tests for data validators and labeling logic in `tests/unit/`
- [ ] T035 [P] Run `quickstart.md` validation: **execute the end-to-end pipeline script defined in quickstart.md and verify the output Parquet file** is valid and complete.

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
# Launch data fetching and simulation setup in parallel:
Task: "Implement code/data/download.py to fetch experimental data"
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
4. **STOP and VALIDATE**: Test User Story 1 independently (verify `descriptors.parquet` is valid and complete)
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
- **Critical Data Rule**: `code/data/download.py` MUST fail loudly if real data is unavailable; no synthetic fallbacks allowed.