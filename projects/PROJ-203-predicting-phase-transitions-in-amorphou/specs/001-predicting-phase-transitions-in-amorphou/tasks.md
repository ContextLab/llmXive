# Tasks: Predicting Phase Transitions in Amorphous Solids Using Machine Learning

**Input**: Design documents from `/specs/001-predicting-phase-transitions/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]****: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 0: Pre-Setup (Scope & Spec Alignment)

**Purpose**: Ensure legal scope definition and spec alignment before any code generation.

- [ ] T001.3 [P] **Verify Plan Scope Amendment**: Verify that `plan.md` contains the "Critical Scope Resolution" section documenting the reduction to 24 compositions. If missing, halt. **Prerequisite**: None.
- [ ] T001.5 [P] **Document Pilot Scope Exception (Plan Amendment)**: **Edit the `plan.md` file content directly** to explicitly document the "Critical Scope Resolution" as a formal exception for this run. State that while `spec.md` FR-001 targets 500 compositions, this implementation phase executes a "Pilot Study T001" with N=24 compositions due to compute constraints. Update the plan's "Success Criteria" section to note that RMSE/ROC-AUC targets are validated via Null Model/Permutation Tests on N=24. **Do NOT edit `spec.md`**. **Deliverable**: `plan.md` with updated "Critical Scope Resolution" and "Success Criteria" text. **Prerequisite**: T001.3. **Blocking**: No other task in this project may execute until T001.5 is verified complete.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001.1 [P] **Initialize Project Directory Structure**: Create the following directories relative to project root: `data/raw/`, `data/processed/`, `data/logs/`, `code/`, `code/data/`, `code/models/`, `code/utils/`, `artifacts/models/`, `artifacts/figures/`, `artifacts/reports/`, `tests/`, `docs/`. **Prerequisite**: T001.5.
- [ ] T002.1 [P] Configure linting in `code/pyproject.toml` and `.ruff.toml` with rules for flake8, isort, and complexity.
- [ ] T002.2 [P] Configure formatting in `code/pyproject.toml` for black and isort.
- [ ] T001.2 [P] Create `code/requirements.txt` with pinned dependencies: `numpy`, `pandas`, `scikit-learn`, `scipy`, `matplotlib`, `seaborn`, `shap`, `mdtraj`, `openmm`, `pyyaml`, `lammps`, `datasets`, `pydantic`. **Prerequisite**: T001.1.
- [X] T020.1 [P] **Implement Global Timeout Context Manager Stub**: Create `code/utils/timeout_enforcer.py` containing ONLY a context manager class `PipelineTimeout` that initializes a 6-hour timer on `__enter__` and raises `TimeoutError` if exceeded on `__exit__`. **Do NOT** implement log reading or aggregation logic here. This is a stub utility. **Prerequisite**: None. **Blocking**: Must be available for T010, T015, and all subsequent simulation/training tasks.

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
- [X] T010 [US1] Implement `code/data/simulate.py` to run MD simulations (LAMMPS/OpenMM) for the pilot compositions (from `data/raw/pilot_compositions.csv`). Enforce a CPU time cap per composition. If exceeded, **truncate trajectory to the final steps** for analysis and flag as "truncated" in metadata. Verify OpenKIM potentials are available. **Output**: Save individual simulation duration and status to `data/logs/simulation_times.json` (schema: `{ "composition_id": str, "duration_sec": float, "status": "complete" | "truncated" | "failed" }`). **Prerequisite**: T020.1, T009.
- [X] T011 [US1] **Implement Descriptor Extraction Suite**: Implement `code/data/descriptor_utils.py` to calculate RDF peak position/width, bond-angle variance, and coordination numbers from MD trajectories. **Interface**: Function `extract_descriptors(trajectory_path: str) -> dict` returning a dictionary with keys `{'rdf_peak_pos', 'rdf_peak_width', 'bond_angle_variance', 'coordination_numbers'}`. Use sequential passes or shared memory buffers to ensure data integrity. **Prerequisite**: T010.
- [X] T012 [US1] Record the cooling rate in metadata during descriptor extraction (implemented within `code/data/descriptor_utils.py`).
- [ ] T012.2 [US1] **Implement Timescale Matching Protocol (Alignment)**: Implement logic in `code/data/descriptor_utils.py` to: 1) Read `md_cooling_rate` from simulation metadata and `dsc_cooling_rate_K_s` from `data/raw/literature_subset.csv`. 2) Calculate the scaling factor `S = dsc_cooling_rate / md_cooling_rate`. 3) **Perform Alignment**: Scale the MD simulation time steps by `S` (i.e., `t_aligned = t_md * S`) to match the experimental thermal history. 4) Output `data/processed/metadata.json` with keys: `md_cooling_rate_K_s` (float), `dsc_cooling_rate_K_s` (float), `scaling_factor_S` (float), `alignment_applied: true`, `SRO_Invariance_Assumed: true`. This satisfies FR-008 by performing the alignment protocol and recording the assumption. **Prerequisite**: T010, T009.
- [X] T013 [US1] Implement `code/data/merge.py` to join simulation descriptors with **raw** Tg and Tx values from `literature_subset.csv` into a temporary merged dataset. **Schema**: Output must contain columns `composition_id`, `Tg_K`, `Tx_K`, and all structural descriptors. **Do NOT** include the crystallization label here. **Prerequisite**: T011, T012.2.
- [ ] T013.1 [US1] **Implement Crystallization Labeling Logic & Exclusion**: Apply binary logic (1 if `|Tx_K - Tg_K| <= 50K`, else 0) to the merged dataset from T013. **Exclude row if `Tg_K` is null OR `Tx_K` is null OR the row is marked as "failed simulation" (NaN/corrupted data from T010)**. Log specific composition IDs for excluded rows to `data/logs/excluded_rows.log` (CSV format: `composition_id,reason`). **Verify** that `data/logs/excluded_rows.log` is populated if any exclusions occur. Output the labeled dataset to `data/processed/labeled_dataset_temp.parquet`. **Prerequisite**: T013. **Blocking**: Must be verified before T014.1.
- [ ] T014.1 [US1] **Merge Logic**: Implement the logic to combine `data/processed/labeled_dataset_temp.parquet` with metadata flags from T010 (truncated/failed) and T012.2 (discrepancy log) into a unified dataframe. **Prerequisite**: T013.1, T010.
- [ ] T014.2 [US1] **Filter & Validate Logic**: Implement filtering to ensure no missing values for required predictors (RDF, bond angles, Tg, label). Validate physical bounds using `code/utils/validators.py`. **Prerequisite**: T014.1.
- [ ] T014.3 [US1] **Save Final Dataset**: Save the validated dataset to `data/processed/final_dataset.parquet` with metadata flags for "truncated" simulations, "failed" runs, and the recorded cooling rates. **Prerequisite**: T014.2.

**Checkpoint**: User Story 1 should be fully functional and testable independently (producing valid `final_dataset.parquet`)

---

## Phase 4: User Story 2 - Model Training & Performance Validation (Priority: P2)

**Goal**: Train Random Forest regression and classification models on the generated dataset to predict Tg and crystallization propensity, achieving RMSE ≤15 K and ROC-AUC > 0.7. **Scope**: Pilot Sample of 24 compositions.

The research question, method, and references remain unchanged as required.

**Independent Test**: The training script executes on a 2-CPU runner within 6 hours, outputting a model file and performance report meeting the RMSE and ROC-AUC targets.

### Implementation for User Story 2

- [ ] T015.1 [US2] **Implement Data Loading, Splitting & Verification**: Implement `code/models/train.py` to: 1) Load `data/processed/final_dataset.parquet`. 2) Split data (stratified by chemical family) into training/test sets (standard ratio). 3) Verify split integrity (no leakage, correct stratification). **Prerequisite**: T014.3.
- [X] T016 [US2] **Implement Model Training and Validation Pipeline**: Implement `code/models/train.py` to: 1) Train Random Forest regression (Tg) and classification (Crystallization) models with hyperparameter grid search (capped to complete within 2 hours). 2) Perform k-fold cross-validation for both tasks. 3) **Evaluate Performance**: Calculate RMSE and ROC-AUC. **Handling Low Performance**: If ROC-AUC <= 0.7, **DO NOT FAIL**. Instead, save the model, generate a confusion matrix using `sklearn.metrics.ConfusionMatrixDisplay` and `matplotlib`, save it to `docs/reports/confusion_matrix.png`, and log a "Power Limitation (N=24)" warning in the metrics report. 4) Save models (`models/tg_regressor.pkl`, `models/crystallization_classifier.pkl`) and metrics (`docs/reports/metrics.json`). **Prerequisite**: T015.1.
- [ ] T019 [US2] **Implement Sensitivity Analysis**: Iterate over a range of thresholds from **25K to 100K** in **5K increments**. Report **classification accuracy (using balanced accuracy metric)**, False Positive Rate (FPR), and Class Balance for each threshold. **Validation**: If FPR varies >10% across the range, flag threshold as unstable in the report. Output `data/processed/sensitivity_report.json`. **Prerequisite**: T014.3, T013.1.
- [ ] T020 [US2] **Implement Total Pipeline Timing Aggregation**: Read `data/logs/simulation_times.json` (from T010) and training logs to compute total end-to-end wall-clock time. Verify ≤6 hour limit (SC-005) and output `docs/reports/pipeline_timing.json`. **Prerequisite**: T020.1 (Context Manager exists), T010 (Logs exist).
- [X] T034 [US2] **Implement Null Model & Permutation Test (Consolidated)**: 1) Train a mean predictor baseline (Null Model). 2) Run a permutation test (1000 shuffles, p<0.05). 3) Calculate the final RMSE of the Random Forest model and explicitly compare it to the Null Model RMSE. 4) Output a single `docs/reports/null_model_report.json` containing the Null Model RMSE, Permutation p-value, and RF vs Null comparison. **Prerequisite**: T014.3, T013.1.

**Checkpoint**: User Stories 1 AND 2 should both work independently; model artifacts and metrics reports generated.

---

## Phase 5: User Story 3 - Interpretability & Cross-Family Analysis (Priority: P3)

**Goal**: Generate SHAP values to rank structural descriptors and visualize family-specific vs. universal predictors. **Scope**: Pilot Sample of 24 compositions.

**Independent Test**: Analysis script generates SHAP summary plots and partial dependence plots distinguishing top predictors for each chemical family.

### Implementation for User Story 3

- [X] T024 [US3] Implement SHAP value computation in `code/models/evaluate.py` for both regressor and classifier, stratified by chemical family (oxide, sulfide, organic). **Output**: Raw SHAP values AND a **Ranked Feature Importance List** (JSON) for each family. **Prerequisite**: T016, T015.1.
- [ ] T025 [US3] Generate SHAP summary plots and ranked feature importance lists for each family in `docs/reports/shap_plots/`. **Prerequisite**: T024.
- [ ] T026 [US3] Implement partial dependence plots for top predictors per family to verify monotonic/non-linear relationships with Tg. **Prerequisite**: T024.
- [X] T027 [US3] **Implement Multiple-Comparison Correction**: Apply Bonferroni correction (alpha=0.05) to the statistical significance of *differences* in SHAP importance ranks across families. Input: SHAP values per family. Output: `docs/reports/corrected_p_values.json` containing the corrected p-values for family-wise error control. **Prerequisite**: T025.
- [ ] T027.2 [US3] **Implement LOO Jackknife Resampling & Cross-Family Stability Report**: Implement a Leave-One-Out (LOO) jackknife resampling function to estimate stability of **SHAP mean rank** for each chemical family. Calculate mean rank and **95% Confidence Intervals (CI)** using the **percentile method**. **Output**: `docs/reports/stability_report.json` with schema: `{ "feature": str, "family": str, "mean_rank": float, "ci_lower": float, "ci_upper": float }`. **Crucially**, this task must also generate a **Cross-Family Comparison** section in the report that explicitly compares the mean ranks and CIs across Oxide, Sulfide, and Organic families to identify universal vs. family-specific drivers, satisfying SC-003. **Prerequisite**: T024.
- [ ] T028 [US3] Generate final report identifying universal predictors vs. family-specific drivers in `docs/reports/interpretability_report.md`. **Prerequisite**: T027, T027.2.
- [ ] T029 [US3] Verify statistical significance of family differences and log confidence intervals for top descriptors (SC-003). **Prerequisite**: T027.2.

**Checkpoint**: All user stories should now be independently functional; interpretability analysis complete.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 [P] Documentation updates in `docs/` including `quickstart.md` for running the pipeline
- [ ] T031 Code cleanup and refactoring in `code/` <!-- ATOMIZE: requested -->
- [ ] T032 Performance optimization for data loading and SHAP calculation
- [ ] T033 [P] Additional unit tests for data validators and labeling logic in `tests/unit/`
- [ ] T034 [P] Run End-to-End Validation: Execute the pipeline using `code/main.py` (or the entry point defined in `quickstart.md` if it exists, otherwise `code/main.py`) and verify the output Parquet file is valid and complete.

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
- **Small Sample Size Mitigation**: The project uses N=24 compositions. Task T034 (Null Model/Permutation Test) is mandatory and MUST be executed in Phase 4 after data generation to ensure statistical validity.
- **Timescale Matching**: Task T012.2 implements **Timescale Alignment** (scaling time steps) to satisfy FR-008, while logging the assumption of SRO invariance.
- **Scope Change**: Task T001.5 documents the N=24 reduction in `plan.md` (not `spec.md`) to preserve spec integrity.
- **Statistical Validity**: Task T027.2 uses LOO jackknife with 95% CI (percentile method) to ensure valid confidence intervals for N=24 and explicitly compares across families.
- **ROC-AUC Validation**: Task T016 handles low ROC-AUC gracefully by reporting and flagging power limitations instead of failing.
- **Sensitivity Analysis**: Task T019 reports balanced accuracy and validates threshold stability.
- **Consolidated Null Model**: Task T034 consolidates all Null Model and Permutation Test logic.
- **Directory Structure**: Task T001.1 consolidates directory creation to reduce overhead.
- **Model Training**: Task T016 consolidates training, validation, and serialization into a single atomic task.