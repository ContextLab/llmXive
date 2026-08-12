---
description: "Task list template for feature implementation"
---

# Tasks: Comparative Analysis of Molecular Fingerprints for Pesticide Toxicity Prediction

**Input**: Design documents from `/specs/001-comparative-analysis-of-molecular-fingerprints/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are included because the 'User Scenarios & Testing' section of the spec explicitly defined independent tests for each User Story.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure
- **Note**: `specs/` is at the repository root, `projects/` is a sibling directory.

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

## Pre-Phase 0: Design Artifacts

**Purpose**: Create foundational design artifacts required as inputs for the main implementation phases. **Gate**: This phase must be completed before Phase 1.

- [X] T008 Create `specs/001-comparative-analysis-of-molecular-fingerprints/data-model.md` defining Compound, Fingerprint, Model, and PerformanceMetric entities with schema. This task is a hard gate for Phase 1 and serves as a prerequisite for T011/T012. **Schema**:
  - `Compound`: {smiles: str, mol_id: str, toxicity_labels: dict}
  - `Fingerprint`: {type: str (morgan/maccs), bits: int, vector: list}
  - `Model`: {type: str, fingerprint_type: str, endpoint: str, metrics: dict}
  - `PerformanceMetric`: {name: str, value: float, ci: tuple}
  **Note**: Although it may be done early, it is NOT parallel with the pipeline start; T011/T012 depend on its completion.

**Checkpoint**: Design artifacts ready - main implementation can now begin

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure. **Gate**: Pre-Phase 0 (T008) must be complete.

- [X] T001a Create project directory structure: `projects/PROJ-678-comparative-analysis-of-molecular-fingerprints/`. Execute: `mkdir -p data/raw data/processed code tests`. **Note**: `specs/` is a sibling to `projects/` at the repository root.
- [X] T001b Initialize Python project files: `requirements.txt` (pinning rdkit, scikit-learn, pandas, numpy, requests, pytest), `pyproject.toml` (linting config), `README.md`. **Dependency**: T001a.
- [X] T002 Initialize Python project files: `requirements.txt` (pinning rdkit, scikit-learn, pandas, numpy, requests, pytest), `pyproject.toml` (linting config), `README.md`
- [X] T003 [P] Configure linting (flake8/black) and formatting tools in `pyproject.toml`
- [X] T004 [P] Create `data/raw/` and `data/processed/` directories with `.gitkeep`. Verify with: `ls -d data/raw data/processed && test -f data/raw/.gitkeep && test -f data/processed/.gitkeep`.
- [X] T005 [P] Implement `code/utils.py` with logging configuration, random seed initialization (seed=42), and environment variable loading
- [X] T006 [US1] Create `code/constants.py` with exact variable definitions: `SMARTS_PATTERN = "[P](=O)([O,SC])[O,SC]"` (str), `TANIMOTO_THRESHOLD = 0.85` (float), `MORGAN_RADIUS = 2` (int), `MORGAN_BITS = 2048` (int), `MACCS_BITS = 166` (int), `N_FOLDS = 5` (int). **MUST**: Ensure `code/filter.py` imports and applies this exact constant from `code/constants.py`; hardcoding the pattern in `code/filter.py` is strictly forbidden. **Dependency**: T005 must complete before T006. T011 and T012 depend on T006 completion.
- [X] T007 [P] Setup `tests/` directory structure (`unit/`, `integration/`)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: User Story 1 - Data Acquisition and Organophosphate Filtering (Priority: P1) 🎯 MVP

**Goal**: Download Tox21 dataset, filter for organophosphates using SMARTS, and validate labels.

**Independent Test**: Verify `data/processed/organophosphates_filtered.csv` exists, contains only compounds matching the SMARTS pattern, and has non-zero rows for at least one toxicity endpoint.

### Tests for User Story 1 (REQUIRED per Spec) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Unit test in `tests/unit/test_filter.py::test_smarts_filter_returns_empty_on_no_match`. Implement a pytest function that asserts the filtered dataframe is empty when the SMARTS pattern matches no compounds in a mock dataset.
- [ ] T010 [P] [US1] Integration test in `tests/integration/test_download.py::test_download_and_checksum_tox21` to verify dataset download and checksum validation.

### Implementation for User Story 1

- [X] T011 [US1] Implement `code/download.py` to fetch Tox dataset from HuggingFace `datasets.load_dataset("deepchem/tox")`, including checksum verification. **Depends on T008 (Data Model) and T006 (Constants)**.
- [X] T012 [US1] Implement `code/filter.py` to apply SMARTS pattern `[P](=O)([O,SC])[O,SC]` to filter compounds and save to `data/processed/organophosphates_filtered.csv`. **Implementation**:
  1. Load raw Tox21 data.
  2. Convert SMILES to RDKit Mol objects.
  3. Apply `Chem.MolFromSmarts(SMARTS_PATTERN)` match.
  4. Filter dataframe to matched rows.
  5. Save to CSV.
  **Depends on T004 (Directory Creation), T008 (Data Model), and T006 (Constants)**.
- [X] T013a [US1] Implement validation logic in `code/filter.py` to count rows per toxicity endpoint. **CRITICAL**:
 - **Execution**: Execute the filter.
 - **Verification**:
   - **Failure Path**: If total sample size < 50, verify `data/processed/filter_log.txt` contains the exact string "WARNING: Low Sample Size (n < 50)".
   - **Success Path**: If total sample size >= 50, verify `data/processed/filter_log.txt` contains "status: OK".
 - **Deliverable**: File `data/processed/filter_log.txt` must exist and contain either the warning string or "status: OK". **Depends on T012**.
- [X] T013b [US1] Implement logic in `code/filter.py` to write `data/processed/sample_size_status.json` with `{"status": "SKIP_STATS"}` if sample size < 50, or `{"status": "OK"}` otherwise. **Implementation**:
 1. Read sample count from T013a logic.
 2. Construct JSON object.
 3. Write to `data/processed/sample_size_status.json`.
 **CRITICAL**: This file is the trigger for downstream statistical tasks. **Verification**: `cat data/processed/sample_size_status.json` must return valid JSON. **Depends on T013a**.
- [X] T014 [US1] Add logging for dataset download size, filter counts, and endpoint distribution to `data/processed/filter_log.txt`. **Implementation**:
 1. Log `download_size_bytes` after T011.
 2. Log `filtered_count` after T012.
 3. Log `endpoint_distribution` (dict of label counts) after T013a.
 **Dependency**: T012, T013a.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - Fingerprint Generation and Model Training (Priority: P2)

**Goal**: Generate Morgan and MACCS fingerprints. Perform a **Single Greedy Maximal Dissimilarity Split** (Tanimoto < 0.85) for the held-out test set (FR-004), AND perform **K-Fold Cross-Validation on the Full Dataset** (with Greedy Splits per fold) for the statistical test (FR-005).

**Independent Test**: Execute training script on a sample subset to verify memory safety, artifact generation, and completion within 60 minutes on 2-core CPU.

### Tests for User Story 2 (REQUIRED per Spec) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T015 [P] [US2] Unit test in `tests/unit/test_fingerprints.py::test_morgan_fingerprint_generation` to verify Morgan fingerprint generation parameters.
- [ ] T016 [P] [US2] Unit test in `tests/unit/test_split.py::test_greedy_split_tanimoto_threshold` to verify the greedy split logic maintains Tanimoto < 0.85.

### Implementation for User Story 2

- [X] T017 [US2] Implement `code/fingerprints.py` to generate Morgan (radius=2, 2048 bits) and MACCS (bits) fingerprints for all compounds in filtered CSV; implement chunked processing (batch=500) if memory > 7GB.
- [X] T018a [US2] **Single Split Implementation & Verification**: Implement `code/split.py` to execute a **Single Greedy Maximal Dissimilarity Split** (Tanimoto < 0.85) on the **full filtered dataset** to create a held-out test set (FR-004).
 **Algorithm**:
 1. Initialize test set with the compound furthest from the mean of all compounds.
 2. Iterate through remaining compounds, selecting the one with max min-distance to current test set.
 3. Add to test set if distance > threshold and test set size < 20% of total.
 **Verification & Artifacts**:
 - Verify test set size >= 20.
 - Verify NO compound in test set has Tanimoto similarity >= 0.85 to ANY compound in training set.
 - **If VALID**: Write `data/processed/split_indices.json` with schema `{"status": "VALID", "test_indices": [int], "train_indices": [int], "tanimoto_min": float, "tanimoto_max": float}`.
 - **If INVALID**: Write `data/processed/single_split_error.log` with the specific error reason (e.g., "Test set size < 20" or "Tanimoto threshold violated") and **exit with code 1**. The orchestrator must catch this exit code. Write `data/processed/single_split_invalid_report.md` stating "Single Split Invalid: Insufficient Structural Diversity".
 **Dependency**: T017. **Parallel to T018c1**.
- [X] T018c1 [US2] **K-Fold Split Implementation**: Implement `code/split.py` to generate **K-Fold Split Indices** (where K=`N_FOLDS` from `code/constants.py`) using **Greedy Maximal Dissimilarity** *per fold*.
 **Algorithm**:
 1. Load `data/processed/organophosphates_filtered.csv`.
 2. For each fold k (0 to K-1):
 a. Identify the test fold (1/K of data) using Greedy Maximal Dissimilarity (Tanimoto < 0.85) relative to the remaining training data.
 b. Verify NO compound in the test fold has Tanimoto similarity >= 0.85 to ANY compound in the training fold.
 c. If any fold fails the Tanimoto constraint, set `status: INVALID` for the entire set.
 **Dependency**: T017.
- [X] T018c2 [US2] **K-Fold Verification**: Implement verification logic in `code/split.py`.
 **CRITICAL HARD GATE**: If the algorithm fails to find a valid split for any fold, immediately write `data/processed/kfold_split_error.log` with the specific error reason and **HALT** the K-Fold path.
 **Dependency**: T018c1.
- [X] T018c3 [US2] **K-Fold Artifacts**: Generate artifacts based on T018c2 status.
 **Deliverable**: If VALID, write `data/processed/kfold_split_indices.json` with schema `{"status": "VALID", "folds": [{"fold_id": int, "train_indices": [int], "test_indices": [int]}]}`. If INVALID, write `data/processed/kfold_split_invalid_report.md` and `data/processed/kfold_split_error.log`.
 **CRITICAL**: This task MUST enforce the Tanimoto < 0.85 constraint for *every* fold to satisfy Constitution VII. **Dependency**: T018c2. **Parallel to T018a**.
- [X] T019 [US2] **K-Fold Training**: Implement `code/train.py` to train Random Forest models (100 trees, max_depth=15) using **K-Fold Cross-Validation** on the **full filtered dataset** for the statistical test (FR-005).
 **Rationale**: This implements the Corrected Resampled t-test (FR-005/Constitution VII) which requires repeated samples.
 **MUST**:
 1. Read `N_FOLDS` from `code/constants.py`.
 2. Read `data/processed/kfold_split_indices.json`. If status is "INVALID", exit immediately with code 0.
 3. Iterate through each fold, training on the fold's training indices and validating on the test indices.
 **Deliverable**: Write `data/processed/kfold_scores.json` with schema `{"morgan": {"roc_auc": [float,...]}, "maccs": {"roc_auc": [float,...]}}`. These scores are used for the Corrected Resampled t-test.
 **Dependency**: T018c3. **Parallel to T020a**.
- [X] T020a [US2] **Train Final Model**: Implement `code/train.py` to train a **Final Model** on the **Training Set** (from T018a) and save the model object to `data/processed/final_models.pkl`. **CRITICAL**: Only execute if T018a status is "VALID". If T018a is "INVALID", skip this task. **Dependency**: T018a. **Parallel to T019**.
- [X] T020b [US2] **Evaluate Final Model**: Implement `code/train.py` to evaluate the Final Model on the **Test Set** (from T018a) and save metrics to `data/processed/final_test_metrics.json` with schema `{"morgan": {"roc_auc": float, "pr_auc": float}, "maccs": {"roc_auc": float, "pr_auc": float}}`. **Implementation**:
 1. Load `data/processed/final_models.pkl`.
 2. Load test set data (SMILES, labels) using indices from `data/processed/split_indices.json`.
 3. Generate predictions.
 4. Calculate ROC-AUC and PR-AUC.
 5. Write JSON.
 **Dependency**: T020a.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Comparative Evaluation and Statistical Validation (Priority: P3)

**Goal**: Evaluate models on the **Single Held-Out Test Set** for the report, perform a Corrected Resampled t-test on the **K-Fold Scores**, generate bootstrap confidence intervals, and map feature importance to phosphorus center.

**Independent Test**: Verify final report contains ROC-AUC for both models on the test set, p-value from paired t-test on **K-Fold ROC-AUC scores**, confidence interval, and SC-003 feature importance analysis.

**Data Flow Clarification**:
- **FR-004 (Single Split)**: Metrics for the final report (T024a/T024b) are derived **ONLY** from `data/processed/final_test_metrics.json` (T020b), which uses the **Single Held-Out Test Set** (T018a).
- **FR-005 (K-Fold)**: Statistical tests (T025a2/T025b) are derived **ONLY** from `data/processed/kfold_scores.json` (T019), which uses **K-Fold Cross-Validation**.

### Tests for User Story 3 (REQUIRED per Spec) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T022 [P] [US3] Unit test in `tests/unit/test_stats.py::test_paired_ttest_cv_scores` to verify paired t-test logic on **K-Fold scores**.
- [ ] T023 [P] [US3] Unit test in `tests/unit/test_stats.py::test_bootstrap_confidence_interval` to verify bootstrap CI calculation.

### Implementation for User Story 3

- [X] T024a [US3] **Calculate Descriptive Metrics**: Implement `code/evaluate.py` to read `data/processed/final_test_metrics.json`. Calculate ROC-AUC and PR-AUC for the **Single Held-Out Test Set** (FR-004). **CRITICAL**: These metrics are for the descriptive report ONLY and are distinct from the K-Fold statistical metrics. **Dependency**: T020b.
- [X] T024b [US3] **Write Descriptive Metrics**: Implement `code/evaluate.py` to write `data/processed/test_set_descriptive.json` with schema `{"morgan": {"roc_auc": float, "pr_auc": float}, "maccs": {"roc_auc": float, "pr_auc": float}}`. **Dependency**: T024a.
- [X] T025a1 [US3] **Load & Verify Data**: Implement `code/evaluate.py` to read `data/processed/kfold_scores.json` and `data/processed/sample_size_status.json`. Verify that the scores are derived from K-Fold splits (full dataset) and NOT the single held-out test set. If `sample_size_status.json` is "SKIP_STATS", skip execution and log "Statistical test skipped due to low sample size". **Dependency**: T019, T013b.
- [X] T025a2 [US3] **Execute Statistical Test**: Implement `code/evaluate.py` to perform the **Corrected Resampled t-test (Nadeau & Bengio)** on the **K-Fold ROC-AUC scores** from `data/processed/kfold_scores.json`. **CRITICAL**: Only ROC-AUC scores are used for this test. **Reproducibility**: Use `random_seed=42` and `n_iterations=1000`. **Dependency**: T025a1.
- [X] T025b [US3] **Bootstrap Confidence Interval**: Implement `code/evaluate.py` to generate confidence intervals via **bootstrap resamples** of the **difference** in performance (Morgan - MACCS) for **ROC-AUC** using the **K-Fold scores**. **Reproducibility**: Use `random_seed=42` and `n_iterations=1000`. **Dependency**: T025a2.
- [X] T025c0 [US3] **Re-Train Full Model for SC-003**: Implement `code/evaluate.py` to re-train a Random Forest model (100 trees, max_depth=15) on the **FULL filtered dataset** (using all indices) for the feature importance analysis. **CRITICAL**: This ensures SC-003 measures importance against the full population, not a subset. **Dependency**: T017 (Fingerprints), T012 (Filtered Data).
- [X] T025c1 [US3] **Identify Phosphorus Bits**: Implement `code/evaluate.py` to:
 1. Parse SMILES from `data/processed/organophosphates_filtered.csv`.
 2. Locate the phosphorus atom in each molecule by matching the SMARTS pattern `[P](=O)([O,SC])[O,SC]` defined in FR-001.
 3. **Determinism Rule**: If multiple phosphorus atoms match the SMARTS pattern in a single molecule, select the one with the **lowest atom index** in canonical atom order.
 4. Use RDKit `GetBitInfo()` to find Morgan fingerprint bits within radius=2 of the selected phosphorus atom index.
 **Dependencies**: T012 (Filtered Data), T017 (Fingerprints), T025c0 (Full Model).
- [X] T025c2 [US3] **Calculate Feature Importance**: Implement `code/evaluate.py` to:
 1. Load the trained model from T025c0 (Full Dataset).
 2. Read the Gini importance vectors from `model.feature_importances_`.
 3. Sum the Gini importance for the identified Morgan bits (from T025c1) and calculate the **total Gini importance** for both Morgan and MACCS models (re-train MACCS on full data if needed).
 **Dependency**: T025c1, T025c0.
- [X] T025c3 [US3] **Statistical Validation of Feature Importance (SC-003)**: Implement `code/evaluate.py` to:
 1. Calculate the difference in Gini importance between Morgan and MACCS models.
 2. **Formula**: Calculate `difference_pct = (sum_morgan - sum_maccs) / sum_maccs`.
 3. Check if `difference_pct >= 0.15`.
 4. **CRITICAL**: This is a direct arithmetic comparison as defined in SC-003. Do NOT perform a statistical test (p-value) on the importance difference.
 5. **Deliverable**: Write `data/processed/sc003_analysis.json` with schema `{"morgan_mean_importance": float, "maccs_mean_importance": float, "difference_pct": float, "threshold_met": bool}`.
 **Dependency**: T025c2.
- [X] T029a1 [US3] **Valid Path Gate**: Implement `code/evaluate.py` to read `data/processed/split_indices.json`, `data/processed/sample_size_status.json`, and `data/processed/single_split_error.log`.
 **Gate Condition**:
 - If `split_indices.json` status is "VALID" and `sample_size_status.json` is "OK", proceed to generate full metrics.
 - If `sample_size_status.json` is "SKIP_STATS", skip statistical tests but generate descriptive report with limitation.
 - If `single_split_error.log` exists (Invalid Split), skip statistical tests and generate report with invalidity statement.
 - **CRITICAL**: Proceed to generate metrics **regardless** of whether T025c3's `threshold_met` is true or false. The report must include the result even if the hypothesis failed.
 **Dependency**: T013b, T018a, T024b, T025a2, T025b, T025c3 (Completion only).
- [X] T029a2 [US3] **Valid Path**: Generate metrics table with exact Markdown syntax:
 ```markdown
 | Metric | Morgan | MACCS | P-Value | 95% CI |
 |:--- |:---: |:---: |:---: |:---: |
 | ROC-AUC |... |... |... |... |
 | ROC-AUC Difference | N/A | N/A | ... | [lower, upper] |
 ```
 **CRITICAL**:
 1. Use ONLY metrics from `data/processed/test_set_descriptive.json` (Single Split, FR-004) for the Morgan/MACCS columns.
 2. The **95% CI** column in the **ROC-AUC Difference** row must contain the confidence interval for the *difference* in ROC-AUC (Morgan - MACCS) derived from T025b.
 3. Round all floating-point values to a consistent precision.
 4. P-Value format: "<0.0001" if < 0.0001, otherwise 4 decimals.
 5. Confidence interval format: `[lower, upper]` with standard numerical precision (e.g., `[0.0512, 0.1534]`).
 **Dependency**: T029a1.
- [X] T029a3 [US3] **Valid Path**: Write final report `data/processed/research_results.md` containing:
 1. **Descriptive Metrics** (ROC-AUC and PR-AUC on Test Set from `test_set_descriptive.json`).
 2. **Statistical Test Results** (p-values for ROC-AUC from K-Fold scores).
 3. **SC-003 Analysis** (Gini importance comparison result).
 4. **Limitation Handling**:
    - **If `sample_size_status.json` is "SKIP_STATS"**: Include a section titled "Limitation: Low Sample Size" explaining the skipped statistical test.
    - **If `single_split_error.log` exists**: Include a section titled "Statistical Comparison Invalid" stating the reason for the invalid split.
 **Condition**: ALWAYS run. If conditions for statistical tests are not met, generate the report with the appropriate limitation/invalidity section.
 **Dependency**: T029a2.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Polish & Cross-Cutting Concerns (Addressing Reviewer Concerns)

**Purpose**: Address specific research-stage reviews regarding measurement uncertainty and calibration (by documenting their exclusion per spec).

- [ ] T033 Code cleanup and refactoring to ensure all random seeds are reproducible.
- [ ] T034 Run `quickstart.md` validation to ensure full pipeline execution within 60 minutes on CI.

**Checkpoint**: All documentation and reporting requirements met

---

## Phase 6: Revision & Review Response (Addressing `marie-curie-simulated` Concerns)

**Purpose**: Explicitly address the reviewer's request for measurement uncertainty and calibration details by documenting the methodological constraints and standard practices used, ensuring transparency without fabricating data.

- [X] T039 [P] [US3] Update `specs/001-comparative-analysis-of-molecular-fingerprints/research.md` to include a "Response to Reviewer" subsection. This subsection must:
 1. Acknowledge the reviewer's concern regarding "measurement uncertainty" and "calibration".
 2. State that the Spec Assumptions ("Instrument Precision" and "Algorithm Calibration") explicitly define the methodology: toxicity labels are treated as ground truth (binary, no SD), and RDKit defaults constitute the standard calibration.
 3. **Explicitly document the absence** of measurement uncertainty metrics as a methodological constraint derived from the observational nature of the study (Spec Assumptions), rather than a missing analysis.
 4. Reiterate that the **statistical methodology** (Corrected Resampled t-test) accounts for the variance in the learning process, while the study remains **purely observational and correlational** as per Spec Assumptions.
 5. **Explicitly state that the study makes NO causal claims** and align the language with the Spec's cautious tone.
 **Note**: Do not generate new methodological notes or data. Strictly document the existing assumptions from the Spec. **Depends on T029a3 (Valid Path) or T018c (Invalid Path)**.

**Checkpoint**: Reviewer concerns fully addressed with transparent documentation and methodological justification.

---

## Phase 7: Final Validation & Documentation

**Purpose**: Ensure all artifacts are consistent, the report is complete, and the project is ready for final review.

- [ ] T040 [P] [US3] Generate a comprehensive `FINAL_REPORT.md` in `data/processed/` that aggregates all findings, explicitly citing the source of every metric (Single Split vs. K-Fold) and detailing the exact statistical methods used (Nadeau & Bengio, Bootstrap). **Dependency**: T029a3.
- [ ] T041 [P] [US3] Create a `METHODOLOGY_LIMITATIONS.md` document in `data/processed/` that explicitly lists the constraints imposed by the dataset (binary labels, lack of experimental SD), the computational limits (CPU-only), and the statistical assumptions (independence of folds). **Dependency**: T039.
- [ ] T042 [P] [US3] Run a final end-to-end validation script `code/run_validation.py` that:
 1. Verifies all expected output files exist (`organophosphates_filtered.csv`, `kfold_scores.json`, `research_results.md`, etc.).
 2. Checks that no synthetic data fallbacks were triggered.
 3. Confirms the Tanimoto threshold was respected in all splits.
 4. Outputs a pass/fail status to `data/processed/validation_status.txt`. **Dependency**: T018a, T018c3, T029a3.
- [ ] T043 [P] [US3] Update the main `README.md` in the project root to include a "Key Findings" section summarizing the comparative performance of Morgan vs. MACCS fingerprints for organophosphates, referencing the `FINAL_REPORT.md`. **Dependency**: T040.

**Checkpoint**: Project fully validated, documented, and ready for final submission.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Pre-Phase 0**: No dependencies - can start immediately. **Must complete before Phase 1**.
- **Setup (Phase 1)**: Depends on Pre-Phase 0 completion (T008 required). **Gate**: T008 must be complete before T001-T007.
- **User Stories (Phase 2+)**: All depend on Foundational phase completion (Phase 1)
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 5)**: Depends on all desired user stories being complete
- **Revision (Phase 6)**: Depends on Phase 5 (T029a) to have generated the initial results report to be updated.
- **Final Validation (Phase 7)**: Depends on Phase 6 completion.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 1) - No dependencies on other stories. **Depends on T008 (Data Model) and T006 (Constants)**.
- **User Story 2 (P2)**: Depends on US1 completion (requires filtered data). **Depends on T004 (Directory Creation) and T006 (Constants)**.
- **User Story 3 (P3)**: Depends on US2 completion (requires trained models and splits). **Depends on T018 (Split)**.
- **Phase 5 (Review)**: Depends on US3 completion (requires results to analyze). **Depends on T029a (Report)**.
- **Phase 6 (Revision)**: Depends on Phase 5 completion.
- **Phase 7 (Validation)**: Depends on Phase 6 completion.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (except T006 which is now sequential).
- All Pre-Phase 0 tasks marked [P] can run in parallel.
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows).
- All tests for a user story marked [P] can run in parallel.
- Models within a story marked [P] can run in parallel.
- Different user stories can be worked on in parallel by different team members.

### Critical Sequential Dependencies (Non-Parallel)

- **US1**: T011 (Download) -> T012 (Filter) -> T013 (Validate & Write Gate).
 - T012 depends on T004 (Directory creation), T008 (Data Model), and **T006 (Constants)**.
 - T006 must complete before T012.
- **US2**: T017 (Fingerprints) -> **Parallel Branches**:
 - **Branch A (Single Split)**: T018a (Split & Verify & Artifacts) -> T020a (Train Final) -> T020b (Eval Final).
 - **Branch B (K-Fold)**: T018c1 -> T018c2 -> T018c3 (Verify) -> T019 (K-Fold Train).
 - **Note**: T018a and T018c1 are **PARALLEL** tasks both depending on T017. T019 and T020a are **PARALLEL** tasks depending on their respective split artifacts (T018c3 and T018a).
 - T018a strictly depends on T017.
 - T018c1 strictly depends on T017.
 - T019 strictly depends on T018c3.
 - T020a strictly depends on T018a.
 - **T018a and T018c3 are hard gates**: If either fails, the respective downstream tasks (T020a/T020b or T019) are skipped. **However, T029a3 (Report) is NOT skipped and handles the invalid state.**
- **US3**: T024a (Calc Descriptive) -> T024b (Write Descriptive) -> T025a1 (Load & Verify) -> T025a2 (t-test on K-Fold) -> T025b (Bootstrap) -> T025c0 (Full Model) -> T025c1/2/3 (Feature Importance) -> T029a (Report).
 - T025a1/T025a2 strictly depend on T013b (Sample Size Status) to skip if needed.
 - T025c1 strictly depends on T012 (Filtered Data), T017 (Fingerprints), and T025c0 (Full Model).
 - T029a1 strictly depends on T013b (Sample Size Status) and T018a (Split) to handle the valid path.
 - **T029a1 is a conditional gate**: It checks T013b for "SKIP_STATS" and T018a for "VALID" before proceeding. It proceeds regardless of T025c3's result.
- **Phase 5**: T033/T034 strictly depend on T029a (Report) for content verification.
- **Phase 6**: T039 strictly depends on Phase 5 completion.
- **Phase 7**: T040/T041/T042/T043 strictly depend on Phase 6 completion.

### Parallel Execution Block (Critical for US2)

To resolve ambiguity in the linear listing, the following execution block defines the parallel nature of the split and training tasks:

**Parallel Execution Block: US2 Split & Train**
1. **Start**: T017 (Fingerprints) **MUST BE FULLY COMPLETED** before this block starts.
2. **Parallel Launch**:
 - **Task A**: T018a (Single Split & Verify & Artifacts)
 - **Task B**: T018c1 -> T018c2 -> T018c3 (K-Fold Split & Verify)
3. **Parallel Launch (Consumers)**:
 - **Task A Consumer**: T020a (Train Final Model) -> **Depends ONLY on T018a**.
 - **Task B Consumer**: T019 (K-Fold Train) -> **Depends ONLY on T018c3**.
4. **Convergence**: T020b (Eval Final) depends on T020a. T024a (Calc Descriptive) depends on T020b. T025a1 (Load Data) depends on T019.
5. **Result**: Both branches (A and B) proceed independently. If T018a fails, T020a/T020b are skipped, but T029a3 (Report) is triggered to handle the invalid state. If T018c3 fails, T019 is skipped.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test in tests/unit/test_filter.py::test_smarts_filter_returns_empty_on_no_match"
Task: "Integration test in tests/integration/test_download.py::test_download_and_checksum_tox21"

# Launch all models for User Story 1 together:
Task: "Implement code/download.py to fetch Tox21 dataset"
Task: "Implement code/filter.py to apply SMARTS pattern"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Pre-Phase 0: Design Artifacts
2. Complete Phase 1: Setup
3. Complete Phase 2: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Pre-Phase 0 -> Setup -> Foundation ready
2. Add User Story 1 -> Test independently -> Deploy/Demo (MVP!)
3. Add User Story 2 -> Test independently -> Deploy/Demo
4. Add User Story 3 -> Test independently -> Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Pre-Phase 0 and Setup together
2. Once Setup is done:
 - Developer A: User Story 1
 - Developer B: User Story 2 (can start after US1 data is ready)
 - Developer C: User Story 3 (can start after US2 models are ready)
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
- **Critical Constraint**: All tasks must run on CPU-only CI (cores, limited RAM, no GPU). Do not use low-bit quantization or CUDA.
- **Data Integrity**: All data must be real. No synthetic data generation tasks are allowed.
- **Statistical Rigor**: Corrected Resampled t-test (Nadeau & Bengio) on **K-Fold ROC-AUC scores** (Full Dataset) MUST apply to ROC-AUC only. **NO PR-AUC** for the t-test.
- **Success Criteria**: SC-003 ([deferred] Gini improvement) MUST be explicitly verified using a **direct arithmetic comparison** (not a statistical test) to establish if the difference exceeds 15%. Formula: `(Morgan - MACCS) / MACCS >= 0.15`.
- **Edge Cases**: Handle n < 50 with warning/skip (T013a/T013b); handle insufficient diversity with **HALT** (T018a/T018c3) and invalid report generation (T029a3).
- **Reviewer Compliance**: T039 addresses the `marie-curie-simulated` review by confirming the Spec Assumptions are sufficient and no new justification is needed.
- **Revision Compliance**: T018 now strictly enforces the "halt execution" constraint with verification integrated into T018a and T018c1/c2/c3. T018a/T018c3 now generate the final `research_results.md` for the invalid path to ensure the report exists. T029a/T029b logic updated to reflect **K-Fold CV for t-test** and **Single Split for Report**, and to **always generate the report** even if conditions are invalid.
- **Methodology**: The project implements a **Single Held-Out Test Set** (FR-004) for the final report and a **K-Fold Cross-Validation** (Full Dataset) for the statistical test (FR-005). This satisfies both the structural constraint and the statistical validity requirement.
- **Reproducibility**: All statistical tests (T025a2, T025b) use `random_seed=42` and `n_iterations=1000`.
- **Formatting**: All floating-point values in reports are rounded to 4 decimal places. P-Values < 0.0001 are reported as "<0.0001". CIs are formatted as `[lower, upper]`.
- **T008 Gate**: T008 (Pre-Phase 0) is a hard gate for T001a (Phase 1) despite visual grouping in the file.
- **Test Order**: Tests (T009, T010, etc.) MUST be written and fail before their corresponding implementation tasks.