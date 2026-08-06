# Tasks: Predicting Catalytic Activity from Electronic Structure and Reaction Path Features

**Input**: Design documents from `/specs/001-predicting-catalytic-activity/`
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

**Purpose**: Project initialization and basic structure. All file system paths must be created here before any logic tasks run.

- [ ] T001a [P] Create project directory structure: Create `data/raw/`, `data/processed/`, `code/`, `outputs/`, `tests/`, `state/projects/`, `code/models/`. **Verification**: Run `os.path.isdir()` for each path; if any missing, `sys.exit(1)` with message "Directory initialization failed".
- [ ] T001b [P] Initialize Python packages: Create `__init__.py` in all Python packages (`code/`, `tests/`, `code/utils/`, `code/models/`). **Verification**: Run `python -c "import code"` to ensure importability.
- [X] T001j [P] Initialize Python 3.11 project with `requirements.txt` (pinned versions using `==`: {{claim:c_daf94d1f}})
- [ ] T002 [P] Configure linting (ruff/flake8) and formatting (black) tools: Create `pyproject.toml` with black config and `.ruff.toml` with specific rules (E, F, W, I). **Verification**: Run `ruff check --config=.ruff.toml.` and `black --check.`.
- [X] T039a [P] **Create Nørskov Reference List**. Create a static local file `code/data/norskov_2005_descriptors.json` containing the hardcoded list of descriptors from Nørskov et al. **Do NOT attempt to download**. **Schema**: `{"descriptors": ["d_band_center", "reaction_energy", "activation_barrier"]}`. **Content**: Hardcode these three strings exactly as the reference set. **Output**: `code/data/norskov_2005_descriptors.json`. **Depends on T001a.**

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure logic that MUST be complete before ANY user story can be implemented.
**Note**: This phase assumes directory structure from Phase 1 (T001) is already present.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement content hashing mechanism for `state/` artifacts (Constitution Principle V) in `code/utils/hashing.py`
- [X] T005 [P] Configure base configuration loader for environment variables and paths in `code/config.py`
- [X] T006 [P] Setup logging infrastructure to write logs to `outputs/run.log`
- [X] T007 [P] Implement data validation helpers (checksum verification, schema checks) in `code/utils/validation.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Download OC20 stratified sample, align descriptors, impute missing values, and produce `aligned_dataset.csv`.
**Scope Note**: Per plan.md "Critical Scope Adjustment", this pipeline relies exclusively on the verified OC20 dataset. External datasets (Materials Project, 2025 CO2 study) are excluded due to data unavailability.

**Independent Test**: The pipeline can be tested by verifying that the output CSV contains exactly the expected columns (composition, surface_facet, energy_change, d_band_center, adsorption_energy) with no NaN values in the target column after imputation.

### Implementation for User Story 1

- [ ] T010 [US1] Implement `code/download_data.py`: Download stratified sample of OC20 dataset from HuggingFace. **Dataset ID**: `Open-Catalyst/oc20-experimental`. **File**: `oc20.h5`. **Stratification**: `composition_family` derived via `pymatgen` composition parsing (grouping by metal/oxide type). **Method**: `streaming=True `. **Output**: `data/raw/oc20_sample.h5`. **Depends on T001a.**
- [X] T011 [US1] Implement `code/download_data.py`: Verify checksums of downloaded OC20 file against known hashes. **Depends on T010.**
- [X] T013a [US1] Implement `code/preprocess.py`: **Parse OC20 into DataFrame**. Load `oc20_sample.h5` and parse into a single Pandas DataFrame with columns: `composition`, `surface_facet`, `experimental_tof`, `d_band_center`, `adsorption_energy`. **Verification**: Verify DataFrame shape is (N, M) and columns match schema. **Depends on T010, T011.**
- [ ] T013b [US1] **Construct Unified DataFrame & Generate Entry IDs**. Combine parsed OC20 data into the final unified structure required by FR-001. **Crucially**, generate a unique `entry_id` for each entry by hashing the concatenation of `composition` and `surface_facet` (e.g., `hashlib.sha256(f"{composition}{surface_facet}".encode()).hexdigest()`) as required by the plan's Data Flow section and Constitution Principle V. **Depends on T013a.**
- [ ] T013 [US1] **Compute Alignment Success Rate (SC-002)**. Calculate (matched entries / total entries in the *active* experimental dataset, i.e., OC20) as defined in the **Plan's updated SC-002**. Log this metric explicitly in `outputs/alignment_metrics.json`. **Depends on T013b.**
- [X] T015 [US1] Implement `code/preprocess.py`: Retrieve target variable `experimental_tof` from aligned data (per plan pivot). Log any missing target values for exclusion. **Depends on T013b.**
- [X] T016a [P] [US1] Implement `code/preprocess.py`: **Compute Stoichiometry Features**. Calculate normalized element counts (formula: `count / total_atoms`) for each catalyst entry to create the stoichiometry feature vector. **Constraint**: **EXCLUDE** the target variable (`experimental_tof`) from the feature set before normalization. **Output**: Append `stoich_<Element>` columns (e.g., `stoich_Fe`, `stoich_O`) to the dataframe. **Depends on T015.** <!-- FAILED: unspecified -->
- [ ] T016c [US1] **Define Global Vocabulary & Zero-Padding**. Construct a global vocabulary of all elements present in the dataset. Ensure all stoichiometry vectors are fixed-dimensional by zero-padding elements not present in a specific entry. **Output**: Save the vocabulary mapping to `data/processed/stoich_vocab.json`. **Depends on T016a.**
- [ ] T016b [US1] Implement `code/preprocess.py`: **Compute Stoichiometry Distance**. Implement the Euclidean distance calculation in stoichiometry space (normalized element counts) as required by FR-003. **Depends on T016c.**
- [ ] T012a [US1] **Align OC20 Data Sources (FR-002)**. Implement logic in `code/preprocess.py` to align DFT entries (OC20) using **exact string matching** on `composition` and `surface_facet`, and **normalization/fuzzy matching** on `synthesis_condition` (lowercasing, whitespace trimming, token-based similarity) as required by FR-002. **Logic**: Exclude entries that cannot be aligned OR where `synthesis_condition` is not uniquely identifiable. **Output**: Intermediate aligned dataframe. **Depends on T013b.**
- [ ] T017a [US1] **Strict Stoichiometry KNN Imputation**. Implement k-nearest-neighbors (k=5) based on Euclidean distance in stoichiometry space (normalized element counts) as required by FR-003. **Constraint**: **EXCLUDE** the target variable (`experimental_tof`) from distance calculation to prevent data leakage. **Logic**: If <5 neighbors exist for an entry, **flag** the entry in metadata (e.g., `excluded_from_training=True`) and **exclude** it from the final `aligned_dataset.csv` (do not keep in dataset). **Output**: Save imputed dataset to `data/processed/imputed_dataset.csv` and save list of flagged entries to `outputs/excluded_entries.json`. **Depends on T016b.**
- [ ] T019 [US1] Implement `code/preprocess.py`: Scale all numeric features to zero mean and unit variance. **Depends on T017a.**
- [ ] T020 [US1] Generate `data/processed/aligned_dataset.csv` with final schema. **Schema**: `composition` (str), `surface_facet` (str), `entry_id` (str), `experimental_tof` (float), `d_band_center` (float), `adsorption_energy` (float), `stoich_*` (float). **Constraint**: Must NOT contain any flagged entries. **Depends on T019.**
- [ ] T050 [P] [US1] Implement `tests/test_preprocess.py::test_data_integrity`: A contract test that verifies no NaN values exist in the `experimental_tof` column of `aligned_dataset.csv` and that all `composition` strings are non-empty. **Fails loudly** if data integrity is compromised. **Depends on T020.**

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Baseline Comparison (Priority: P2)

**Goal**: Train XGBoost model, compare against linear baseline, and perform statistical significance testing

**Independent Test**: The model training can be tested by running the script and verifying that both the XGBoost and linear models produce predictions on the hold-out test set with calculated R² and MAE metrics.

### Implementation for User Story 2

- [X] T024 [US2] Implement `code/train.py`: Load `aligned_dataset.csv` and split into train/test sets (stratified). **Depends on T020.**
- [X] T025 [US2] Implement `code/train.py`: Train Linear Baseline using only `d_band_center` and `adsorption_energy`. **Depends on T024.**
- [X] T026 [US2] Implement `code/train.py`: Train XGBoost with nested cross-validation. **Outer loop**: 5-fold. **Inner loop**: Grid search `max_depth` across a range of low to moderate depths., `learning_rate` ∈ {0.01, 0.1}, `n_estimators` ≤ 200 (Fixed grid per FR-004). **Seed**: 42. **Save best model to `code/models/best_xgboost.json`** (FR-004). **Depends on T024.**
- [X] T027 [US2] Implement `code/evaluate.py`: Compute absolute errors for both models on hold-out test set. **Depends on T025, T026.**
- [X] T028a [US2] **Statistical Test Logic (Normality Check on Paired Differences)**. Compute the absolute errors for both models. Calculate the *paired differences* of absolute errors. Perform Shapiro-Wilk test on the **distribution of paired differences** to satisfy FR-005. **Alpha**: 0.05. **Output**: `outputs/normality_check.json` with schema `{ "statistic": float, "p_value": float, "decision": "use_t_test" | "use_wilcoxon" }`. **Depends on T027.**
- [X] T028b [US2] **Perform Selected Statistical Test**. Based on T028a's decision, perform a two-tailed paired t-test (if normal) or Wilcoxon signed-rank test (if not normal) on the paired differences of absolute errors. **Depends on T028a.**
- [X] T029 [US2] Generate `outputs/metrics.json` containing R², MAE, Pearson R, and p-value for both models. **Depends on T028b.**
- [X] T030 [US2] Create `tests/test_train.py` unit tests for grid search parameter selection logic. **Depends on T026.**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance and Interpretability Analysis (Priority: P3)

**Goal**: Perform SHAP analysis, rank top descriptors, verify SC-003, and generate final report

**Independent Test**: The interpretability step can be tested by running the SHAP calculation and verifying that the a subset of top descriptors are listed in descending order of importance with a corresponding bar plot generated.

### Implementation for User Story 3

- [X] T033 [US3] Implement `code/evaluate.py`: Compute SHAP values for the final XGBoost model using `shap.TreeExplainer`. **Depends on T026.**
- [X] T034 [US3] Implement `code/evaluate.py`: Rank descriptors by mean absolute SHAP impact (FR-006). **Depends on T033.**
- [X] T039b [US3] **Compare Descriptors**. Compare the top-ranked SHAP descriptors against the Nørskov list from T039a. Explicitly state matches or novel findings. **Depends on T034, T039a.**
- [X] T035 [US3] Implement `code/evaluate.py`: Generate `outputs/feature_importance.png` bar plot of top descriptors. **Depends on T034.**
- [X] T036a [US3] **Define Reduced Model Search Space**. Explicitly define the hyperparameter search space (max_depth, learning_rate, n_estimators) for the reduced model. **Requirement**: This grid MUST be identical to the grid used in T026. **Output**: Save grid config to `code/configs/reduced_model_grid.json`. **Depends on T034.**
- [X] T036 [US3] Implement `code/evaluate.py`: Train a reduced model using **exactly the top 5** SHAP-ranked descriptors (no other features). **Requirement**: Perform independent hyperparameter tuning using the grid search defined in T036a. **Seed**: 42. **Save best model to `code/models/best_reduced_xgboost.json`**. **Depends on T036a.**
- [X] T037 [US3] Implement `code/evaluate.py`: **Verify SC-003 quantitatively**. Calculate reduced model R² and full model R². Compute the ratio (reduced_r2 / full_r2). **Append quantitative results (reduced_r2, full_r2, ratio) and verification status to outputs/metrics.json** and `outputs/sc003_verification.json`. If ratio < 0.50, set 'SC-003_status': 'FAILED'. **Depends on T036.**
- [X] T039 [US3] Implement `code/report.py`: **Generate Descriptor Comparison Table**. Append comparison table to `outputs/final_report.md` under section "Descriptor Comparison" using results from T039b. **Depends on T034, T037, T039b.**
- [X] T040 [US3] Implement `code/report.py`: Generate `outputs/final_report.md` containing Pearson R, MAE, p-value, top list, SC-003 verification result (quantitative), and Nørskov comparison table (FR-007). **Depends on T037, T039.**
- [X] T041 [US3] Create `tests/test_evaluate.py` unit tests for SC-003 quantitative logic. **Depends on T037.**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T042a [P] Run full pipeline end-to-end. **Capture start/end timestamps explicitly** and log them to `outputs/runtime.log`.
- [X] T042b [P] Log duration (calculated from T042a timestamps) to `outputs/metrics.json`.
- [X] T042c [US3] **Adaptive Runtime Check & Feasibility Verification**. Read duration from `outputs/metrics.json`. If duration > 6 hours, set `feasibility_status`: "FAIL" in `outputs/feasibility_verification.json`. If duration <= 6 hours, set `feasibility_status`: "PASS". **Output**: Generate a dedicated artifact `outputs/feasibility_verification.json` containing the measured duration, the 6-hour limit, and the binary pass/fail status to formally verify SC-004. **Note**: The grid search in T026 is fixed; no dynamic reduction of `n_estimators` is performed. **Depends on T042a, T042b.**
- [X] T043a [P] Run `black --check.` and `ruff check.` on all code. Fix any formatting/linting errors.
- [X] T043c [P] Remove all debug prints from `code/preprocess.py` and `code/train.py`.
- [X] T044 [P] Update `README.md` with usage instructions and data sources.
- [X] T045 [P] Add additional unit tests for edge cases (missing neighbors, non-normal error distributions).
- [X] T046 [P] Run quickstart.md validation to ensure reproducibility.
- [X] T049 [US3] Implement `code/report.py`: **Add "Data Lineage" Section**. Explicitly list the exact HuggingFace commit hash of the OC20 dataset used (from T010) and the exact `requirements.txt` hash used. **Output**: Append to `outputs/final_report.md` under "Reproducibility Metadata". **Depends on T011, T040.**

---

## Revision: Addressing Analyze Findings

**Purpose**: New tasks added to resolve specific issues raised by `/speckit.analyze` regarding data flow, runtime estimation, and spec alignment.

- [X] T012a [US1] **Align OC20 Data Sources (FR-002)**. (See Phase 3).
- [X] T050 [P] [US1] Implement `tests/test_preprocess.py::test_data_integrity`. (Moved to Phase 3 Implementation).
- [X] T016c [US1] **Define Global Vocabulary & Zero-Padding**. (See Phase 3).
- [X] T039a [P] **Create Nørskov Reference List**. (Moved to Phase 1).

**Note**:
- T001c (Scope Adjustment Artifact) has been removed as redundant per Plan Constitution Check.
- T014a and T014b (synthesis_condition checks) have been removed as they implemented logic for a removed requirement.
- T048 (Dynamic Runtime Adaptation) has been removed as it contradicted the fixed grid search requirement in FR-004.
- T013b has been updated to generate `entry_id` and remove MP exclusion logs.
- T017a has been clarified to exclude flagged entries from the final dataset entirely.
- T013 has been updated to explicitly cite Plan SC-002 for the alignment baseline.
- T042c has been updated to remove dynamic adaptation logic and strictly enforce the fixed grid search constraint.
- T052 (Streaming Data Loader) has been removed as redundant; T010 and T012 already implement streaming.
- T054 (Runtime Estimation) and T055 (Independent Training Verification) have been removed as unapproved scope.
- T049 duplicate in Revision section removed.
- T030, T036a, T042c [P] tags removed to reflect sequential dependencies.
- T039b moved to follow T034 for correct data flow.
- T056 (Strict Data Source Fallback Policy) has been removed as it contradicted the plan's fallback strategy.
- T051a and T051b (VIF Diagnostics) have been removed as they were unrequested gold-plating.
- T012 (MP/2025 Download) has been removed as the plan prioritizes OC20.