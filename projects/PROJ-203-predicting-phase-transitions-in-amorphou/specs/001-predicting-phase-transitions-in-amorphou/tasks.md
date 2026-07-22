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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001.1 Create project directory structure relative to the project root: `code/`, `code/data/`, `code/models/`, `code/utils/`, `data/raw/`, `data/processed/`, `data/logs/`, `artifacts/models/`, `artifacts/figures/`, `artifacts/reports/`, `tests/`, `docs/`.
- [ ] T002.1 [P] Configure linting in `code/pyproject.toml` and `.ruff.toml` with rules for flake8, isort, and complexity.
- [ ] T002.2 [P] Configure formatting in `code/pyproject.toml` for black and isort.
- [ ] T001.2 Create `code/requirements.txt` with pinned dependencies: `numpy`, `pandas`, `scikit-learn`, `scipy`, `matplotlib`, `seaborn`, `shap`, `mdtraj`, `openmm`, `pyyaml`, `lammps`, `datasets`, `pydantic`.
- [ ] T001.3 Update `plan.md` Summary section to formally document the reduction of FR-001 target from 500 to 24 compositions due to compute constraints (Pilot Study T001) and the plan to implement scaling logic in T010.2.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Implement `code/config.py` to manage environment variables, paths (`data/raw`, `data/processed`, `models`), simulation parameters (cooling rate, time steps), and define data entities (Composition, StructuralDescriptor, ThermalProperty) using Python dataclasses.
- [X] T004 [P] Create `code/utils/validators.py` for data integrity checks (NaN detection, physical bound validation for descriptors).
- [X] T005 [P] Setup logging infrastructure in `code/utils/logging_config.py` to capture simulation truncations and missing data events.
- [X] T007 Implement `code/utils/plots.py` helpers for SHAP and partial dependence visualization.
- [ ] T012.2 [US1] **Implement Active Timescale Matching Protocol**: Calculate the scaling factor to align MD cooling rate with experimental DSC cooling rate using Arrhenius scaling (E_a from literature). Update `code/config.py` with the corrected cooling rate parameters. Write the `SRO_Invariance_Assumed` flag (set to False) and scaling factors to `data/processed/metadata.json` and as global attributes in the final Parquet file. **Prerequisite**: Must run after T003. **Blocking**: Must complete before T010.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Pipeline Execution & Descriptor Generation (Priority: P1) 🎯 MVP

**Goal**: Execute the full data generation pipeline to produce a structured dataset of short-range structural descriptors and compositional features, linked to experimental thermal properties. **Scope**: Pilot Sample of compositions (stratified by family), with logic for full 500.

**Independent Test**: The pipeline runs end-to-end on a CPU-only environment, producing a single Parquet file where every row contains composition, structural descriptors, and experimental Tg/crystallization labels, with no missing values for required predictors.

### Implementation for User Story 1

- [X] T009 [US1] Implement `code/data/validate_literature_subset.py` to check for the existence and integrity of the hard-coded `data/raw/literature_subset.csv`. **FAIL LOUDLY**: If the file is missing or corrupted, raise `FileNotFoundError` with message "FATAL: literature_subset.csv missing or corrupted" and exit with code 1. Do NOT attempt to fetch from external sources (Zenodo/NIST).
- [X] T010 [US1] Implement `code/data/simulate.py` to run MD simulations (LAMMPS/OpenMM) for the pilot compositions. Enforce a CPU time cap per composition. If exceeded, **truncate trajectory to the final 500 steps** for analysis (per Constitution Principle VII) and flag as "truncated" in metadata. Verify OpenKIM potentials are available. **Prerequisite**: Must read corrected cooling rate from `code/config.py` (T012.2).
- [ ] T010.1 [US1] Implement timing logging in `code/data/simulate.py`: Write simulation start/end timestamps and duration for each composition to `data/logs/simulation_times.json`. **Schema**: `{ "composition_id": str, "start_time": ISO8601, "end_time": ISO8601, "duration_s": float, "status": "success" | "truncated" | "failed" }`. **Note**: This task runs sequentially after T010 simulation loop.
- [ ] T010.2 [US1] **Implement Full-Scale Scaling Logic**: Implement a config-driven batching framework in `code/data/simulate.py` to support processing up to 500 compositions as required by FR-001, while maintaining a time cap per run. **Verification**: Run on the 24-composition pilot to verify batching logic and queue management.
- [X] T011 [US1] **Implement Descriptor Extraction Suite**: Implement `code/data/descriptor_utils.py` to calculate RDF peak position/width, bond-angle variance, and coordination numbers from MD trajectories in a single pass. **Note**: All descriptors must be computed in one function call to avoid race conditions.
- [X] T012 [US1] **Implement Cooling Rate Metadata Recording**: Update `code/data/descriptor_utils.py` to record the actual simulated cooling rate (from `config.py`) in the intermediate descriptor metadata.
- [X] T013 [US1] Implement `code/data/merge.py` to join simulation descriptors with experimental labels from `literature_subset.csv` into a temporary merged dataset.
- [ ] T013.1 [US1] **Implement Crystallization Labeling Logic**: Apply binary logic (1 if |Tx - Tg| <= 50K, else 0) to the merged dataset from T013. **Exclude row if `T_x` is null OR `Tg` is null**. Log specific composition IDs for excluded rows to `data/logs/excluded_rows.log`.
- [ ] T014 [US1] Save final processed dataset to `data/processed/final_dataset.parquet` with metadata flags for "truncated" simulations, "failed" runs, `SRO_Invariance_Assumed`, and the applied cooling rate scaling factor. **Prerequisite**: Consumes output of T013.1.

**Checkpoint**: User Story 1 should be fully functional and testable independently (producing valid `final_dataset.parquet`)

---

## Phase 4: User Story 2 - Model Training & Performance Validation (Priority: P2)

**Goal**: Train Random Forest regression and classification models on the generated dataset to predict Tg and crystallization propensity, achieving RMSE ≤15 K and ROC-AUC > 0.7. **Scope**: Pilot Sample of compositions

The research question, method, and references remain unchanged as required.

**Independent Test**: The training script executes on a 2-CPU runner within 6 hours, outputting a model file and performance report meeting the RMSE and ROC-AUC targets.

### Implementation for User Story 2

- [ ] T015 [US2] Implement `code/models/train.py` to load `data/processed/final_dataset.parquet` (which now includes pre-computed labels from T013.1) and split data (stratified by chemical family) into training/test sets. <!-- FAILED: unspecified -->
- [X] T016 [US2] Implement Random Forest regression training in `code/models/train.py` with hyperparameter grid search (capped to complete within 2 hours). Target: RMSE ≤15 K.
- [ ] T017 [US2] Implement Random Forest classifier training in `code/models/train.py` using the pre-computed crystallization labels from `data/processed/final_dataset.parquet`. Ensure the confusion matrix is saved to verify the "low stability" labeling logic. <!-- FAILED: unspecified -->
- [ ] T018 [US2] Implement k-fold cross-validation in `code/models/train.py` and save `models/tg_regressor.pkl` and `models/crystallization_classifier.pkl`. <!-- FAILED: unspecified -->
- [ ] T019 [US2] **Implement Sensitivity Analysis**: Iterate over thresholds ranging from low to high values. Report FPR, Class Balance, accuracy, and **calculate the derivative of FPR change** to verify the discrete range captures instability trends. **Output Schema**: `{ "threshold_K": int, "fpr": float, "class_balance": float, "accuracy": float, "fpr_derivative": float }`. Output `data/processed/sensitivity_report.json`. **Prerequisite**: Must consume `data/processed/final_dataset.parquet` (T014) and trained models (T018).
- [ ] T020 [US2] Generate `docs/reports/metrics.json` containing RMSE, ROC-AUC, and cross-validation fold scores (SC-001, SC-002).
- [X] T022 [US2] **Implement Null Model & Permutation Test (Supplementary Validation)**: Train a mean predictor baseline and run a permutation test with **exactly 1000 shuffles** to establish statistical significance for the small sample size (N=24). This is a supplementary check for model significance, distinct from FR-006 threshold sensitivity. Output `docs/reports/null_model_report.json`.
- [ ] T023 [US2] **Implement Collinearity Report**: Calculate VIF for all predictors and output `docs/reports/collinearity_report.json` (FR-007). **Prerequisite**: Must consume `data/processed/final_dataset.parquet` (T014).

**Checkpoint**: User Stories 1 AND 2 should both work independently; model artifacts and metrics reports generated.

---

## Phase 5: User Story 3 - Interpretability & Cross-Family Analysis (Priority: P3)

**Goal**: Generate SHAP values to rank structural descriptors and visualize family-specific vs. universal predictors. **Scope**: Pilot Sample of compositions.

**Independent Test**: Analysis script generates SHAP summary plots and partial dependence plots distinguishing top predictors for each chemical family.

### Implementation for User Story 3

- [X] T024 [US3] Implement SHAP value computation in `code/models/evaluate.py` for both regressor and classifier, stratified by chemical family (oxide, sulfide, organic).
- [ ] T025 [US3] Generate SHAP summary plots and ranked feature importance lists for each family in `docs/reports/shap_plots/`.
- [ ] T026 [US3] Implement partial dependence plots for top predictors per family to verify monotonic/non-linear relationships with Tg.
- [ ] T027 [US3] **Implement Multiple-Comparison Correction**: Apply Bonferroni/FDR correction to feature importance comparisons across families (FR-005). Output `corrected_p_values`.
- [ ] T027.1 [US3] **Implement Stability Metrics & Confidence Intervals**: Calculate the stability of the top 3 structural descriptors across families using **bootstrapping (1000 iterations)** and report **95% confidence intervals**. Output `docs/reports/stability_report.json`.
- [ ] T028 [US3] Generate final report identifying universal predictors vs. family-specific drivers in `docs/reports/interpretability_report.md`.
- [ ] T029 [US3] Verify statistical significance of family differences and log confidence intervals for top descriptors (SC-003). **Method**: Bootstrapping (sufficient iterations) for 95% CI.

**Checkpoint**: All user stories should now be independently functional; interpretability analysis complete.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 [P] Documentation updates in `docs/` including `quickstart.md` for running the pipeline
- [ ] T031 Code cleanup and refactoring in `code/`
- [ ] T032 Performance optimization for data loading and SHAP calculation
- [ ] T033 [P] Additional unit tests for data validators and labeling logic in `tests/unit/`
- [ ] T034 [P] Run End-to-End Validation: **Execute the pipeline using `code/main.py` (or the entry point defined in `quickstart.md` if it exists, otherwise `code/main.py`) and verify the output Parquet file is valid and complete.**
- [ ] T021 [P] **Implement Total Pipeline Timing Aggregation**: Read `data/logs/simulation_times.json` (T010.1) and training logs to compute total end-to-end wall-clock time. Verify ≤6 hour limit (SC-005) and output `docs/reports/pipeline_timing.json`. **Prerequisite**: Depends on completion of T010.1 and T018. **Note**: Requires T021.1 (Global Timeout Enforcer) to be active.

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
Task: "Implement code/data/descriptor_utils.py (All descriptors in one pass)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify `final_dataset.parquet` is valid and complete)
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
- **Small Sample Size Mitigation**: The project uses N=24 compositions. [UNRESOLVED-CLAIM: c_6f64ef5b — status=not_enough_info] Tasks T022 (Null Model/Permutation Test) and T023 (Collinearity Report) are mandatory and MUST be executed in Phase 4 after data generation to ensure statistical validity.
- **Timescale Matching**: Task T012.2 implements the active protocol to calculate scaling factors using Arrhenius logic, satisfying FR-008.
- **Scope Change**: Task T001.3 updates `plan.md` to document the reduction from 500 to 24 compositions; T010.2 implements the scaling logic for the full 500.
- **Total Pipeline Time**: Task T021 aggregates simulation (T010.1) and training times to verify SC-005. **Note**: T021.1 (Global Timeout Enforcer) is required for active enforcement.