# Tasks: Predicting the Solubility of Pharmaceutical Compounds in Water Using Graph Neural Networks

**Input**: Design documents from `/specs/001-predict-solubility-gnn/`
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
- **Mobile**: `api/src/`, `android/src/`
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

- [X] T001 Create project structure per implementation plan (`code/`, `data/`, `models/`, `results/`, `tests/`)
- [X] T002 Initialize Python project with `requirements.txt` (pinning `rdkit`, `torch` CPU, `torch-geometric` CPU, `scikit-learn`, `pandas`, `numpy`, `matplotlib`, `scipy`)
- [X] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Create base data models/entities (`Molecule`, `DatasetSplit`) in `code/models.py` or `code/__init__.py` to support downstream pipeline tasks.
- [X] T004 Implement `code/data/download_esol.py` to fetch ESOL dataset from MoleculeNet repository URL (`https://deepchemdata.s-us-west-1.amazonaws.com/datasets/delaney-processed.csv`). **Must include:** (1) Fallback logic to the verified HuggingFace mirror URL (`https://huggingface.co/datasets/deepchem/delaney-processed/resolve/main/delaney-processed.csv`) if the primary S source is unreachable, (2) Validation of `logS` column presence, (3) Save raw CSV to `data/raw/`. **Constraint:** If both sources fail, the script MUST raise an exception. No synthetic fallbacks allowed.
- [X] T004b Implement checksumming in `code/data/download_esol.py` or `code/utils/checksum.py` to compute SHA-256 of the raw CSV file and record it **ONLY** in `state/projects/PROJ-351-predicting-the-solubility-of-pharmaceuti.yaml` under the `artifact_hashes` map. **Depends on:** T004. **Note:** This task is sequential and must complete after T004. **Constraint:** Do NOT create secondary manifest files like `data/raw/checksums.md` to avoid scope creep; the state manifest is the single source of truth.
- [X] T005 [P] Implement `code/data/preprocess.py` to load raw CSV, parse SMILES with RDKit, exclude invalid SMILES/NaN `logS` *before* split, extract atom/bond features, and save **cleaned RDKit Mol objects** to `data/processed/cleaned_graphs.pkl`. **Must include:** (1) Error handling for RDKit failures (log count to `data/logs/exclusions.log` and raise warning), (2) Logging of exclusion counts to satisfy FR-001 and Principle VI. **(Note: This task covers the logging/exclusion scope previously assigned to T017).**
- [X] T005b Implement `code/data/graph_tensorizer.py` to load the cleaned RDKit Mol objects (from T005) and convert them into PyTorch Geometric graph tensors (atom features: atomic number, hybridization, charge; bond features: bond type, conjugation, stereochemistry). Save tensors to `data/processed/graph_tensors.pt`. **Depends on:** T005. **Note:** This task explicitly produces the GNN input format required by T021, closing the data pipeline gap.
- [X] T006 Implement `code/data/split.py` to perform **Stratified K-Fold** splitting based on `logS` using **10 quantile bins** to ensure distribution balance in each fold as mandated by Plan P1.3 and Spec FR-005. Save indices to `data/processed/`. **Depends on:** T005. **Note:** This task replaces any previous scaffold-based split logic. The stratification must use multiple bins to ensure sufficient granularity for the 5-fold split.
- [X] T008 [P] Configure logging infrastructure: Create `code/config/logging_config.py` to set up JSON-formatted logging with timestamps, writing to `data/logs/` to satisfy Constitution Principle III. **(Note: This task covers the logging integration scope previously assigned to T017).**
- [X] T009 [P] Setup environment configuration management: Implement random seed pinning for numpy, torch, and random modules in `code/` to ensure reproducibility (Constitution Principle I). Do not prescribe specific file formats; ensure seeds are applied globally before data loading.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Pipeline and Baseline Establishment (Priority: P1) 🎯 MVP

**Goal**: Download ESOL, clean invalid SMILES, preprocess to graphs, and train Random Forest baseline to establish a performance floor.

**Independent Test**: The pipeline can be fully tested by running the data download, cleaning, preprocessing, and Random Forest training script, verifying that a model is saved and metrics are logged.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for SMILES validation logic in `tests/unit/test_preprocess.py`
- [X] T011 [P] [US1] Unit test for Stratified Split logic in `tests/unit/test_split.py`
- [X] T012 [P] [US1] Integration test for full RF baseline pipeline in `tests/integration/test_baseline_pipeline.py`

### Implementation for User Story 1

- [X] T012a [US1] Implement `code/data/featurize.py` to load cleaned RDKit Mol objects (from T005) and convert them into Morgan fingerprints (radius=2, 2048 bits) for the Random Forest baseline. Save to `data/processed/fingerprints.npz`. **Depends on:** T005. **Note:** This task explicitly handles the RF-specific feature extraction, distinct from the GNN graph tensors in T005b.
- [X] T013 [US1] Define Random Forest baseline architecture in `code/models/baseline_rf.py` using Morgan fingerprints (radius=2, 2048 bits). **Depends on:** T012a.
- [X] T016 [US1] Implement a **Nested Cross-Validation** loop in `code/training/train_baseline_cv.py`:
 - **Outer Loop**: 5 folds (Stratified by logS using 10 bins).
 - **Inner Loop**: 5 folds for hyperparameter tuning (n_estimators, max_depth).
 - **Execution**: For each Outer Fold, train on Inner Train/Val, select best model, predict on Outer Test.
 - **Output**: Save **per-fold** predictions and metrics to `data/processed/rf_fold_predictions.json` (list of 5 fold objects).
 - **Aggregation**: **MUST** concatenate all outer fold predictions into a single vector and save this aggregated error vector to `data/processed/rf_aggregated_errors.json`.
 - **Final Metrics**: **MUST** calculate the final RMSE and R² from the aggregated vector and save them to `results/baseline_metrics.json`.
 **Depends on:** T013, T006. This task replaces the single-split training task to ensure robust performance estimation and prevent data leakage.
- [ ] T016a [US1] **Train Final RF Baseline Model**: Implement `code/training/train_final_rf.py` to train a **single** Random Forest model on the **entire** cleaned training set (using the best hyperparameters found in T016) to serve as the final baseline artifact. Save model to `data/artifacts/final_rf_baseline.pkl`. **Depends on:** T016. **Note:** This satisfies FR-003's requirement for a "Random Forest baseline" artifact (singular model) for direct comparison in the report.
- [X] T015 [US1] Log R-squared and RMSE metrics to `results/baseline_metrics.json` after the Nested CV completes. **Constraint:** Baseline training is a component of the full pipeline which must complete within 6 hours (SC-003).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - GNN Model Training and Evaluation (Priority: P2)

**Goal**: Implement and train a Message Passing Neural Network (MPNN) configured strictly for CPU execution and evaluate against the Random Forest baseline.

**Independent Test**: The GNN training script can be run independently (assuming data exists), and the resulting model must produce a test set RMSE that is recorded and compared to the baseline.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for MPNN architecture (CPU-only verification) in `tests/unit/test_gnn_arch.py`
- [X] T019 [P] [US2] Integration test for GNN training loop with early stopping in `tests/integration/test_gnn_training.py`

### Implementation for User Story 2

- [X] T020 [US2] Define Message Passing Neural Network (MPNN) architecture in `code/models/gnn_mpnn.py` using PyTorch Geometric, ensuring NO CUDA/GPU calls. Architecture parameters (layers, hidden dim) MUST be configurable via `code/config.py`.
- [X] T021 [US2] Implement a **Nested Cross-Validation** loop in `code/training/train_gnn_cv.py`:
 - **Outer Loop**: 5 folds (Stratified by logS using 10 bins).
 - **Inner Loop**: 5 folds for hyperparameter tuning (learning_rate, hidden_dim, patience).
 - **Execution**: For each Outer Fold, train on Inner Train/Val with Early Stopping, select best model, predict on Outer Test.
 - **Output**: Save **per-fold** predictions and metrics to `data/processed/gnn_fold_predictions.json` (list of 5 fold objects).
 - **Aggregation**: **MUST** concatenate all outer fold predictions into a single vector and save this aggregated error vector to `data/processed/gnn_aggregated_errors.json` for statistical testing.
 **Depends on:** T020, T005b, T006. This task replaces the single-split training task.
- [X] T024 [US2] Save GNN predictions to `results/gnn_predictions.csv` and metrics to `results/gnn_metrics.json`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance and Interpretability (Priority: P3)

**Goal**: Perform paired t-test on prediction errors, calculate statistical power, and generate feature importance visualizations.

**Independent Test**: The analysis script takes the prediction files from US-1 and US-2, runs the t-test and power analysis, and generates a plot or table of feature importance.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Unit test for paired t-test and power analysis logic in `tests/unit/test_stats.py`
- [X] T027b [P] [US3] Unit test for visualization generation (file size > 1KB) in `tests/unit/test_viz.py`

### Implementation for User Story 3

- [X] T033 [US3] Implement `code/evaluation/aggregate_predictions.py` to load **per-fold** predictions from T016 (`rf_fold_predictions.json`) and T021 (`gnn_fold_predictions.json`), concatenate them into single vectors, and save to `data/processed/aggregated_predictions.json`. **Requires:** T016 (RF CV), T021 (GNN CV). **Note:** This task is the explicit aggregation step, resolving the redundancy with T016/T021.
- [X] T023 [P] [US3] Implement evaluation script in `code/evaluation/metrics.py` to calculate RMSE and R-squared for GNN on aggregated test set (input from T033). **Depends on:** T033.
- [X] T025 [US3] **Model Comparison**: Implement `code/evaluation/compare_models.py` to calculate the RMSE delta between Baseline (from T016) and GNN (from T021). Save to `results/model_comparison.json`. **Depends on:** T016, T021, T033.
- [X] T028 [P] [US3] Implement `code/evaluation/statistical_test.py` to:
 1. **Execute Shapiro-Wilk normality test** on the concatenated absolute error vectors.
 2. **Execute Nadeau's Corrected Resampled t-test** (using **k=5** fold ratio correction) on the concatenated absolute error vectors from the Outer Loop (input from T033).
 3. Calculate post-hoc statistical power and Cohen's d effect size.
 4. **Mandatory**: If Shapiro-Wilk indicates non-normality, **MUST** calculate a non-parametric alternative (Wilcoxon signed-rank test) and report it with a cautionary note.
 5. **Validate Output**: Ensure the resulting JSON object contains `normality_test`, `effect_size_cohens_d`, `p_value`, and `statistical_power` keys.
 6. **Write Output**: Save results to `results/statistical_test.json`.
 7. **Write to Metrics**: Explicitly write the calculated `statistical_power` value to `results/metrics.json`.
 **Requires:** T033 (Aggregated predictions).
- [X] T029 [US3] Implement `code/evaluation/interpretability.py` to generate attention heatmaps or node importance rankings for sample molecules using GNNExplainer. **Depends on:** T033 (for molecule selection).
- [X] T030 [US3] **Generate Visualizations**: Implement `code/evaluation/visualize_molecules.py` to generate attention heatmaps for sample molecules.
 - **Selection Logic**: Select a representative subset of molecules via **deterministic quantile-based selection** from the aggregated Outer Loop predictions (bottom [deferred], 40-60%, top [deferred]).
 - **Fallback Mechanism**: **MUST** check if quantile selection yields fewer than 5 unique molecules. If so, randomly sample the remaining required count to guarantee the minimum of 5.
 - **Output**: Save PNG files to `docs/reports/interpretability_plots/` (minimum 5 files, >1KB each).
 - **Manifest**: **MUST** save `results/viz_manifest.json` listing the 5 selected molecule IDs and their corresponding file paths.
 **Requires:** T033, T029.
- [X] T032 [US3] Implement `code/evaluation/write_metrics.py` to write aggregated RMSE, R², p-value, and **statistical power** to `results/metrics.json` (SSoT). **Requires:** T028, T024, T025.
- [X] T031 [US3] Implement `code/evaluation/report_generator.py` to compile RMSE, R², p-value, power, and delta into a final summary table reading **only** from `results/metrics.json`. **Requires:** T032.
- [X] T034 [US3] Add logic to detect and report "ceiling effect" if Baseline R² > 0.9 (as per spec Edge Cases): Append `ceiling_effect` flag to `results/final_report.json`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T035 [P] Documentation updates in `docs/` and `README.md`
- [X] T036 Performance optimization for GNN training loop (CPU efficiency)
- [X] T037 [P] Additional unit tests for edge cases (malformed SMILES, non-convergent GNN) in `tests/unit/`
- [X] T038 Run quickstart.md validation

---

## Phase P: Final Integration & Verification

**Purpose**: Ensure all components work together and verify the full pipeline meets all success criteria.

- [X] T045 [P] **End-to-End Pipeline Verification**: Execute `code/main_pipeline.py` to run the full workflow (Download -> Clean -> Split -> RF CV -> GNN CV -> Stats -> Report) and verify completion within 6 hours on a **2-core CPU runner**. **Depends on:** All Phase 2-5 tasks. **Reason**: Validates SC-003 (Computational Feasibility) and ensures all components integrate correctly. **Note**: Runtime logging must be captured to confirm the 6-hour limit is met.
- [ ] T046 [US3] **Final Report Generation**: Generate `docs/reports/final_report.md` containing the following **mandatory sections** (read data from `results/metrics.json`, `results/statistical_test.json`, `results/viz_manifest.json`):
 1. **Executive Summary**: Brief overview of findings.
 2. **Methodology**: Description of Nested CV and Nadeau's test.
 3. **Performance Comparison**: Table with RF vs GNN RMSE, R², and Delta (from `results/metrics.json`).
 4. **Statistical Significance**: P-value, effect size, and **statistical power** (from `results/statistical_test.json`).
 5. **Interpretability**: Reference to 5 visualization files (from `results/viz_manifest.json`).
 6. **Limitations**: Discussion of ceiling effect (if `ceiling_effect` flag is set) and power < 0.8.
 **Constraint**: This task is **NOT parallel-safe** (depends on T031, T030). **Do NOT mark as [P]**.
 **Note**: This task defines the content schema explicitly to ensure FR-007 is fulfilled.
- [ ] T047 [US3] **Artifact Validation**: Execute `python code/utils/validate_artifacts.py` against `contracts/model_output.schema.yaml`.
 - **Input**: `results/*.json`, `data/processed/*.json`, `docs/reports/*.png`.
 - **Output Schema**: Generate `results/validation_report.json` with the following structure:
 ```json
 {
   "status": "PASS" | "FAIL",
   "artifacts": [
     { "path": "...", "status": "PASS" | "FAIL", "error_code": "..." | null }
   ],
   "errors": ["..."]
 }
 ```
 **Constraint**: The script MUST produce this exact JSON structure.
 **Depends on:** T045.
- [ ] T048 [US3] **Edge Case Stress Test**: Implement `tests/integration/test_failure_modes.py` that mocks network errors and asserts exception raising, producing `results/failure_test_log.txt` confirming the exception behavior. **Depends on:** T004, T005. **Reason**: Validates the "Fail Loudly" rule and prevents fabrication.
- [ ] T049 [US3] **Statistical Power Review & Reporting**: Analyze the output of T028 to confirm statistical power > 0.8 or document the limitation. **Depends on:** T028. **Action**: Append `power_analysis_summary` section to `docs/reports/final_report.md` containing the calculated power value and a mandatory interpretation string if power < 0.8.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Final Integration (Phase P)**: Depends on completion of Phase N tasks

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Relies on data pipeline from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Relies on results from US1 and US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T004, T005, T008, T009) can run in parallel (within Phase 2, except T004b, T005b, T006 which are sequential)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- Phase P tasks (T045, T048) can run in parallel as they are distinct verification steps. T046, T047, T049 are sequential dependencies of the final report.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for SMILES validation logic in tests/unit/test_preprocess.py"
Task: "Unit test for Stratified Split logic in tests/unit/test_split.py"

# Launch all models for User Story 1 together:
Task: "Define Random Forest baseline architecture in code/models/baseline_rf.py"
Task: "Log R-squared and RMSE to results/baseline_metrics.json"
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
 - Developer A: User Story 1 (Data + RF)
 - Developer B: User Story 2 (GNN)
 - Developer C: User Story 3 (Stats + Viz)
3. Stories complete and integrate independently
4. Final team review: Execute Phase P (Final Integration & Verification) to ensure full pipeline success.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Constraint**: All GNN tasks must run on CPU-only; no CUDA/GPU calls allowed.
- **Constraint**: All tasks must complete within 6 hours on 2 vCPU.
- **Constraint**: No synthetic data; use real ESOL dataset from MoleculeNet repository or verified canonical source.
- **Critical Rule**: If a real data fetch fails, the script MUST raise an exception. No synthetic fallbacks allowed.
- **Critical Update**: Stratified 5-Fold split (T006) is now a mandatory prerequisite in Phase 2, replacing the scaffold-based split logic.
- **Critical Update**: All training tasks (T016, T021) now implement Nested Cross-Validation as per plan, replacing standard K-fold CV.
- **Critical Update**: Phase O tasks (T040-T044) have been **removed** as they were redundant with Phase 2/3 implementation. The logic for Nested CV and Nadeau's t-test resides exclusively in T016, T021, and T028.
- **Critical Update**: Task T012b (SMILES enumeration) has been removed as it violates the "No synthetic data" constraint.
- **Critical Update**: Task T005b explicitly generates GNN graph tensors, closing the pipeline gap between cleaning and GNN training.
- **Critical Update**: Task T030 uses deterministic quantile selection (10th/50th/90th) to guarantee representative coverage with a fallback mechanism.
- **Critical Update**: Task T028 performs the paired t-test with a mandatory Shapiro-Wilk normality check and conditional reporting, including a mandatory non-parametric alternative if normality is violated.
- **Critical Update**: Task T027 (timeout_handler) has been removed; 6-hour limit is enforced by the runner environment and verified via logging in T045.
- **Critical Update**: Task T049 now depends on T028 (the statistical test implementation) instead of the removed T044.
- **Critical Update**: Task T016 and T021 now save per-fold predictions, with T033 handling aggregation.
- **Critical Update**: Task T004b explicitly mandates checksum storage in state manifest only, forbidding secondary manifest files.
- **Critical Update**: Task T023 has been moved to Phase 5 to align with T033 dependency.
- **Critical Update**: Task T046-T049 status corrected to pending to reflect that these artifacts are currently missing and require implementation.
- **Critical Update**: T046 now explicitly defines the report schema and sections, removing reliance on external scripts for content definition.
- **Critical Update**: T047 now explicitly defines the output schema for the validation report.
- **Critical Update**: T049 added to explicitly append power analysis summary to the final report.
- **Critical Update**: T016b added to train the final single RF baseline model artifact.
- **Critical Update**: T025 moved to Phase 5 to resolve cross-phase dependency.
- **Critical Update**: T004 [P] tag removed to prevent confusion with sequential T004b.
- **Critical Update**: T046 [P] tag removed to reflect sequential dependency on US3 completion.
- **Critical Update**: T016 now includes saving aggregated baseline metrics to `results/baseline_metrics.json`.
- **Critical Update**: T021 now includes saving aggregated GNN errors for statistical testing.
- **Critical Update**: T028 now mandates writing statistical power to `results/metrics.json`.
- **Critical Update**: T030 now includes generation of `results/viz_manifest.json`.
- **Critical Update**: T046 now explicitly lists mandatory sections and data sources for the final report.
- **Critical Update**: T047 now explicitly defines the JSON schema for the validation report.
- **Critical Update**: T049 now includes the action to append power analysis summary to the final report.
- **Critical Update**: T004b no longer mandates `data/raw/checksums.md`, aligning with Constitution Principle III.
- **Critical Update**: T028 now mandates a non-parametric alternative if normality is violated, removing "optional" language.
- **Critical Update**: T030 now includes a mandatory fallback mechanism to ensure 5 unique molecules are selected.
- **Critical Update**: T025 moved to Phase 5 to align with T033 dependency.
- **Critical Update**: T046 is no longer marked [P] due to sequential dependencies.
- **Critical Update**: T004 is no longer marked [P] to clarify sequential dependency of T004b.