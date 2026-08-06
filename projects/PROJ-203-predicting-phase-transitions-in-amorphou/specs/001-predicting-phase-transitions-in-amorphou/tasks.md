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
- [ ] T001.3 [P] **Verify Scope Reduction Documentation**: Verify that `plan.md` Summary section documents the reduction of FR-001 target from 500 to 24 compositions due to compute constraints (Pilot Study T001). No editing required if already present.
- [ ] T001.4 [US1] **Define & Execute Pilot Sample Selection**: Implement a script `code/data/select_pilot.py` to select a stratified set of compositions (Oxides, Sulfides, Organics) from `data/raw/literature_subset.csv`. Output `data/raw/pilot_compositions.csv`. **Prerequisite**: Must run after T009.
- [ ] T021.1 [P] **Implement Global Timeout Enforcer**: Create `code/utils/timeout_enforcer.py` with a context manager that enforces a wall-clock time limit for the entire pipeline. If time > 6h, trigger graceful shutdown and save partial results. **Prerequisite**: None. **Blocking**: Must be available for T010, T015, T016, and all subsequent simulation/training tasks.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Implement `code/config.py` to manage environment variables, paths (`data/raw`, `data/processed`, `models`), simulation parameters (cooling rate, time steps), and define data entities (Composition, StructuralDescriptor, ThermalProperty) using Python dataclasses.
- [X] T004 [P] Create `code/utils/validators.py` for data integrity checks (NaN detection, physical bound validation for descriptors).
- [X] T005 [P] Setup logging infrastructure in `code/utils/logging_config.py` to capture simulation truncations and missing data events.
- [X] T007 Implement `code/utils/plots.py` helpers for SHAP and partial dependence visualization.

---

## Phase 3: User Story 1 - Data Pipeline Execution & Descriptor Generation (Priority: P1) 🎯 MVP

**Goal**: Execute the full data generation pipeline to produce a structured dataset of short-range structural descriptors and compositional features, linked to experimental thermal properties. **Scope**: Pilot Sample of 24 compositions (stratified by family).

**Independent Test**: The pipeline runs end-to-end on a CPU-only environment, producing a single Parquet file where every row contains composition, structural descriptors, and experimental Tg/crystallization labels, with no missing values for required predictors.

### Implementation for User Story 1

- [X] T009 [US1] Implement `code/data/validate_literature_subset.py` to check for the existence and integrity of the hard-coded `data/raw/literature_subset.csv`. **FAIL LOUDLY**: If the file is missing or corrupted, raise `FileNotFoundError` with message "FATAL: literature_subset.csv missing" and exit with code 1. Do NOT attempt to fetch from external sources (Zenodo/NIST).
- [X] T010 [US1] Implement `code/data/simulate.py` to run MD simulations (LAMMPS/OpenMM) for the pilot compositions (from `data/raw/pilot_compositions.csv`). Enforce a CPU time cap per composition. If exceeded, **truncate trajectory to the final portion of steps** for analysis and flag as "truncated" in metadata. Verify OpenKIM potentials are available. **Prerequisite**: T021.1.
- [X] T011 [US1] **Implement Descriptor Extraction Suite**: Implement `code/data/descriptor_utils.py` to calculate RDF peak position/width, bond-angle variance, and coordination numbers from MD trajectories. **Interface**: Function `extract_descriptors(trajectory_path: str) -> dict` returning a dictionary with keys `{'rdf_peak_pos', 'rdf_peak_width', 'bond_angle_variance', 'coordination_numbers'}`. Use sequential passes or shared memory buffers to ensure data integrity. **Prerequisite**: T010.
- [X] T012 [US1] Record the cooling rate in metadata during descriptor extraction (implemented within `code/data/descriptor_utils.py`).
- [ ] T012.2 [US1] **Implement Timescale Matching Protocol**: Implement logic in `code/config.py` or `code/data/descriptor_utils.py` to calculate the scaling factor between the MD simulation cooling rate and the experimental DSC cooling rate. Apply this factor to adjust simulation parameters to align the thermal history. Output the scaling factor and aligned parameters to `data/processed/metadata.json` with keys: `cooling_rate_K_s` (float), `scaling_factor` (float), `SRO_Invariance_Assumed` (bool, set to False if alignment performed).
- [X] T013 [US1] Implement `code/data/merge.py` to join simulation descriptors with experimental labels from `literature_subset.csv` into a temporary merged dataset.
- [ ] T013.1 [US1] **Implement Crystallization Labeling Logic**: Apply binary logic (1 if |Tx - Tg| <= 50K, else 0) to the merged dataset from T013. **Exclude row if `T_x` is null OR `Tg` is null**. Log specific composition IDs for excluded rows to `data/logs/excluded_rows.log`. Output the labeled dataset to `data/processed/labeled_dataset_temp.parquet`. **Prerequisite**: T013. **Blocking**: Must be verified before T014.
- [ ] T014 [US1] Save final processed dataset to `data/processed/final_dataset.parquet` with metadata flags for "truncated" simulations, "failed" runs, and the applied cooling rate. **Prerequisite**: T013.1.

**Checkpoint**: User Story 1 should be fully functional and testable independently (producing valid `final_dataset.parquet`)

---

## Phase 4: User Story 2 - Model Training & Performance Validation (Priority: P2)

**Goal**: Train Random Forest regression and classification models on the generated dataset to predict Tg and crystallization propensity, achieving RMSE ≤15 K and ROC-AUC > 0.7. **Scope**: Pilot Sample of 24 compositions.

The research question, method, and references remain unchanged as required.

**Independent Test**: The training script executes on a 2-CPU runner within 6 hours, outputting a model file and performance report meeting the RMSE and ROC-AUC targets.

### Implementation for User Story 2

- [ ] T015 [US2] Implement `code/models/train.py` to load `data/processed/final_dataset.parquet` and split data (stratified by chemical family) into training/test sets (standard ratio). **Prerequisite**: T014, T021.1. <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [X] T016 [US2] Implement Random Forest regression training in `code/models/train.py` with hyperparameter grid search (capped to complete within 2 hours). Target: RMSE ≤15 K. **Prerequisite**: T015. <!-- ATOMIZE: requested -->
- [ ] T017 [US2] Implement Random Forest classifier training in `code/models/train.py` using the pre-computed crystallization labels from `data/processed/final_dataset.parquet**. Ensure the confusion matrix is saved to `docs/reports/confusion_matrix.png` (PNG format) to verify the "low stability" labeling logic. **Prerequisite**: T014. <!-- FAILED: unspecified -->
- [ ] T018 [US2] Implement k-fold cross-validation in `code/models/train.py` and save `models/tg_regressor.pkl` and `models/crystallization_classifier.pkl`. **Prerequisite**: T017. <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [ ] T019 [US2] **Implement Sensitivity Analysis**: Iterate over a range of thresholds, beginning with relatively low values and increasing to higher values in discrete steps. Report FPR, Class Balance, and accuracy for each threshold. Output `data/processed/sensitivity_report.json`. **Prerequisite**: T014. <!-- ATOMIZE: requested -->
- [ ] T020 [US2] Generate `docs/reports/metrics.json` containing RMSE, ROC-AUC, and cross-validation fold scores (SC-001, SC-002). **Prerequisite**: T018.
- [X] T022 [US2] **Implement Null Model & Permutation Test (Supplementary Validation)**: Train a mean predictor baseline and run a permutation test with a sufficient number of iterations to establish statistical significance for the small sample size. Output `docs/reports/null_model_report.json`. **Prerequisite**: T014.
- [ ] T023 [US2] **Implement Collinearity Report**: Calculate VIF for all predictors (threshold VIF > 5). Output `docs/reports/collinearity_report.json` with schema: `{ "feature": str, "vif": float, "flagged": bool }`. **Prerequisite**: T014.

**Checkpoint**: User Stories 1 AND 2 should both work independently; model artifacts and metrics reports generated.

---

## Phase 5: User Story 3 - Interpretability & Cross-Family Analysis (Priority: P3)

**Goal**: Generate SHAP values to rank structural descriptors and visualize family-specific vs. universal predictors. **Scope**: Pilot Sample of 24 compositions.

**Independent Test**: Analysis script generates SHAP summary plots and partial dependence plots distinguishing top predictors for each chemical family.

### Implementation for User Story 3

- [ ] T024 [US3] Implement SHAP value computation in `code/models/evaluate.py` for both regressor and classifier, stratified by chemical family (oxide, sulfide, organic). **Prerequisite**: T018.
- [ ] T025 [US3] Generate SHAP summary plots and ranked feature importance lists for each family in `docs/reports/shap_plots/`. **Prerequisite**: T024.
- [ ] T026 [US3] Implement partial dependence plots for top predictors per family to verify monotonic/non-linear relationships with Tg. **Prerequisite**: T024.
- [ ] T027 [US3] **Implement Multiple-Comparison Correction**: Apply Bonferroni correction (alpha=0.05 (Wikipedia: Bonferroni correction, https://en.wikipedia.org/wiki/Bonferroni_correction)) to the statistical significance of *differences* in SHAP importance ranks across families. Input: SHAP values per family. Output: `docs/reports/corrected_p_values.json` containing the corrected p-values for family-wise error control. **Prerequisite**: T025.
- [ ] T027.1 [US3] **Implement Stability Metrics & Confidence Intervals**: Calculate the stability of the top structural descriptors across families using stratified bootstrapping with a sufficient number of iterations. Report confidence intervals on the mean SHAP value rank. Output `docs/reports/stability_report.json` with schema: `{ "feature": str, "family": str, "mean_rank": float, "ci_lower": float, "ci_upper": float }`. **Prerequisite**: T024.
- [ ] T028 [US3] Generate final report identifying universal predictors vs. family-specific drivers in `docs/reports/interpretability_report.md`. **Prerequisite**: T027, T027.1.
- [ ] T029 [US3] Verify statistical significance of family differences and log confidence intervals for top descriptors (SC-003). **Prerequisite**: T027.

**Checkpoint**: All user stories should now be independently functional; interpretability analysis complete.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 [P] Documentation updates in `docs/` including `quickstart.md` for running the pipeline
- [ ] T031 Code cleanup and refactoring in `code/`
- [ ] T032 Performance optimization for data loading and SHAP calculation
- [ ] T033 [P] Additional unit tests for data validators and labeling logic in `tests/unit/`
- [ ] T034 [P] Run End-to-End Validation: Execute the pipeline using `code/main.py` (or the entry point defined in `quickstart.md` if it exists, otherwise `code/main.py`) and verify the output Parquet file is valid and complete.
- [ ] T021 [P] **Implement Total Pipeline Timing Aggregation**: Read `data/logs/simulation_times.json` (from T010) and training logs to compute total end-to-end wall-clock time. Verify ≤6 hour limit (SC-005) and output `docs/reports/pipeline_timing.json`. **Prerequisite**: T021.1.

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
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch data validation and simulation setup in parallel:
Task: "Implement code/data/validate_literature_subset.py to check static file"
Task: "Implement code/data/simulate.py to run MD simulations"

# Launch descriptor extraction and validation in parallel:
Task: "Implement code/data/descriptor_utils.py (Unified pipeline with shared buffers)"
```

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
- **Timescale Matching**: Task T012.2 implements the active scaling factor calculation to satisfy FR-008.
- **Scope Change**: Task T001.3 verifies the reduction from 500 to 24 compositions in `plan.md`.