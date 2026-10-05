---
description: "Task list template for feature implementation"
---

# Tasks: Predicting Plant Drought Tolerance from Publicly Available Physiological and Genomic Data

**Input**: Design documents from `/specs/001-drought-tolerance-prediction/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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

- [X] T001 Create project directory structure with explicit directories: `code/`, `data/raw/`, `data/processed/`, `tests/`, `docs/`, `docs/reports/`
- [X] T002 Initialize Python 3.11 project with `requirements.txt` containing `scikit-learn>=1.3.0 `, `xgboost>=2.0.0 `, `pandas>=2.0.0 `, `numpy>=1.24.0 `, `scipy>=1.11.0 `, `requests>=2.31.0 `, `imblearn>=0.11.0 `, `pyyaml>=6.0.0 `, `joblib>=1.3.0 `, `pytest>=7.4.0 `, `psutil>=5.9.0 `, `phylolm>=1.0.0 ` (or `mvMORPH`), `ete3` (for tree parsing)
- [X] T003 [P] Configure linting (flake�/black) and formatting tools in `pyproject.toml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **Includes all data generation (Real or Synthetic) and the Pipeline Entry Point.**

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

**Execution Order Note**: Within this phase, **T011b must complete before T012 runs**. T012's logic depends on the failure status of T011b. **T012 and T016a MUST be completed before T013 and T021 can run.**

- [X] T004 Implement `code/utils/logging.py` to create `DataPipelineLog` with methods for recording source URLs, download status, imputation details, merge statistics, and **excluded species** (FR-007)
- [X] T005 [P] Create `code/utils/stats.py` implementing DeLong's test for paired AUCs and standard statistical utilities
- [X] T006 [P] [Foundational] Create `code/config.py` to manage species lists, random seeds, and **Execution Modes**. **Logic**: Define `VALIDATION_MODE` (bool, default **False**). If `VALIDATION_MODE` is True: allow synthetic data fallback ONLY if real fetch fails. If `VALIDATION_MODE` is False: **fail loudly** (raise critical error) if real fetch fails. This is the **single source of truth** for error handling strategy (FR-001, Plan Validation Mode). <!-- FAILED: unspecified -->
- [X] T007 Create base data entities: `SpeciesRecord` (fields: `species_id`, `traits_dict`, `genomic_markers`, `label`) and `ModelResult` (fields: `model_name`, `metrics`, `hyperparameters`, `feature_importance`) in `code/models/entities.py`
- [X] T011a [US1] Implement `code/data/download.py` to fetch TRY database CSVs with exponential backoff and checksum verification. **Logic**: Implement a retry mechanism with a configurable number of attempts using exponential backoff. **Specific Handling**: Explicitly handle HTTP 404/403 errors with specific error logging. On success, return status `SUCCESS`. On failure (after retries), return status `FAILED` and log the error. (FR-001)
- [X] T011b [US1] [Foundational] Implement `code/data/download.py` to fetch **NCBI RefSeq** genomic annotation files for the species list. **Logic**: **Step 1**: Attempt real fetch. **Step 2**: If fetch fails: If `VALIDATION_MODE` (from T006) is False, **raise a critical error** (fail loudly) and halt execution. If `VALIDATION_MODE` is True, return status `FAILED`, log "Real fetch failed, switching to synthetic", and **explicitly log a WAIVER of FR-001** indicating that real genomic data is unavailable and synthetic data will be used. Proceed to T012. **Step 3**: If fetch succeeds, **parse and integrate real NCBI RefSeq data** (GFF/FASTA) into the dataset. (FR-001, T006)
- [ ] T012 [P] [Foundational] [US1] Implement `code/data/generate.py` to generate **synthetic genomic features** and **synthetic drought labels**. **Logic**: **Trigger**: Run ONLY if `VALIDATION_MODE` is True (from T006) AND T011b returns `FAILED`. **Gene List (20)**: `NCED3`, `ABF3`, `P5CS`, `DREB2A`, `ERF1`, `ABI5`, `RD29A`, `COR15A`, `LEA3`, `HSP70`, `SOD`, `APX1`, `CAT1`, `GPX1`, `MDHAR`, `DHAR`, `GSTU`, `ZAT12`, `WRKY33`, `MYB96`. **Label Logic**: `prob = sigmoid(sum(hidden_genes) - 2) + noise(0.1, seed=42)`. **Hidden Genes**: Select a subset of random genes from the training genes (deterministic via seed) to generate the label., ensuring the model must *discover* the signal. **Label**: `1 if random() < prob else 0`. **Mandatory Check**: If real genomic data is detected, bypass this generator and log "Real data used". Output to `data/processed/synthetic_genomics.csv`. **Schema**: 20 gene columns (0/1), 1 label column (0/1). **Explicitly log**: "Scope Reduction: Synthetic data used, invalidates FR-001/SC-001 biological claims". **Verification**:
 1. Verify output CSV has N rows, columns match gene list.
 2. Verify label distribution mean is within 5% of expected sigmoid probability using a Chi-Square Goodness-of-Fit test (p-value > 0.05, expected mean=0.5, bins=10, uniform distribution across bins).
 3. **Explicitly log the indices of the selected hidden genes** to ensure the signal is recoverable and the generation logic is deterministic.
 4. **Deliverable**: Write the Chi-Square test result (p-value, statistic, pass/fail) to `data/logs/generation_config.json` under key `chi_square_test_result`. (FR-001, Plan Validation Mode)
- [X] T011c [P] [Foundational] [US1] Create `code/config.py` entry for **15 Independent Validation Genes**. **Logic**: Compile a curated list of ABA-signaling genes. (e.g., `ABF2`, `DREB1B`, `NAC072`, `WRKY40`, `bZIP28`, `bZIP63`, `ABI1`, `ABI2`, `PP2CA`, `SnRK2.1`, `SnRK2.5`, `SnRK2.7`, `RD26`, `RD29B`, `COR15B`) that are **strictly disjoint** from the 20 training genes in T012. Store in `code/config.py`. **Verification**: Ensure no overlap with T012 list. (SC-005)
- [ ] T016a [P] [Foundational] Implement `code/data/generate.py` to generate a **synthetic phylogenetic distance matrix** for the species list. **Logic**: Generate an N x N symmetric matrix (N=species count) with a zero diagonal and off-diagonal values uniformly distributed between **0.01** and **1.0**. **Random Seed**: Use `random_state=42` for **all** random operations (including the uniform distribution generation) to ensure determinism. Save to `data/processed/synthetic_phylo_matrix.npy`. **Verification**: Verify diagonal is zero, off-diagonals > 0, shape matches N, and file exists. (FR-009, Plan Validation Mode)
- [X] T016c [P] [Foundational] Implement `code/data/download.py` to fetch a **real phylogenetic tree** from OpenTree of Life (or alternative verified source) for the species list. **Logic**: Use the OpenTree API to retrieve the tree. If successful, save to `data/raw/phylo_tree.newick`. If failed: If `VALIDATION_MODE` is False, **raise a critical error** (fail loudly). If `VALIDATION_MODE` is True, log "Tree fetch failed; synthetic matrix will be used" and **explicitly log that the Plan's constraint (no verified tree) overrides the result, triggering the synthetic path**. **Verification**: Verify file exists or log contains specific failure message. (FR-009, Spec Requirement)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Feature Construction (Priority: P1) 🎯 MVP

**Goal**: Download real TRY data, attempt real genomic/phylogeny data, generate synthetic fallback ONLY if Validation Mode, merge into a clean dataset with imputation.

**Independent Test**: Can be fully tested by executing `code/data/ingest.py` and verifying the output CSV contains the expected number of rows (species) and columns, with no missing values for the target label. **Note**: This test requires T014a/b (Imputation) to be complete.

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/data/ingest.py` to merge TRY traits (from T011a) and genomic data (**Input: Output from T011b if SUCCESS, OR T012 if T011b FAILED and VALIDATION_MODE=True**) by species ID. **Explicitly detect species present in TRY but missing in genomic data, flag them with "no_genomic_data" or exclude them, and log the count.** (FR-002)
- [ ] T037 [P] [US1] Update `code/data/ingest.py` to explicitly **log the exact species IDs excluded** due to missing genomic data, ensuring `data/logs/metrics.json` contains a list of excluded species for auditability. **Verification**: Verify `data/logs/metrics.json` contains a "excluded_species" list with the exact IDs of species missing genomic data. (Review Concern: Data Integrity Traceability) <!-- FAILED: unspecified -->
- [ ] T014a [US1] Implement `code/data/ingest.py` to handle missing continuous traits. **Logic**: **Requires: T016c (Real Tree)**. Check if `data/processed/real_phylo_matrix.npy` (from T016c) exists using `os.path.exists('data/processed/real_phylo_matrix.npy')`. **Dependency**: This task must run **after** T016c determines tree availability.
 - **If EXISTS**: Apply **Phylogenetic MICE** (via T014b). This is the **primary path** to satisfy FR-002 and Constitution VI.
 - **If NOT EXISTS**:
 - If `VALIDATION_MODE` is False, **raise a critical error** ("CONSTITUTION VI VIOLATION: Phylogenetic MICE required but tree missing. Halting execution.").
 - If `VALIDATION_MODE` is True, apply **Median Substitution** using `sklearn.impute.SimpleImputer(strategy='median')`, **explicitly log a WAIVER of FR-002** stating that Phylogenetic MICE is unavailable and Median Substitution is used, and proceed.
 **Output**: `data/processed/merged_dataset_imputed.csv`. **Columns**: Impute all continuous trait columns defined in `SpeciesRecord` (T007) (e.g., `root_depth`, `leaf_area`, `stomatal_conductance`). (FR-002, Constitution VI)
- [X] T014b [US1] Implement `code/utils/imputation.py` to perform **Phylogenetic MICE** using the `phylolm` or `mvMORPH` library if a tree is available. **Logic**: Use the phylogenetic distance matrix to inform imputation of missing traits. (FR-002, Spec Requirement)
- [X] T015 [US1] Implement `code/data/split.py` to perform stratified train-test split by drought label, with fallback to leave-one-one-out if N is small. (FR-003)

### Tests for User Story 1

- [X] T008 [P] [US1] Unit test for TRY download retry logic with 404 simulation in `tests/unit/test_download.py`
- [X] T009 [P] [US1] Unit test for synthetic genomic data generation consistency (seed 42) in `tests/unit/test_synthetic.py`
- [ ] T010 [P] [US1] Integration test for full merge pipeline (TRY + Synthetic) producing valid DataFrame in `tests/integration/test_ingest.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. A clean `data/processed/merged_dataset.csv` should exist.

---

## Phase 4: User Story 2 - Model Training and Validation (Priority: P2)

**Goal**: Train RF, XGBoost, and KNN Baseline on CPU; validate performance against baseline using DeLong's test.

**Independent Test**: Run `code/models/train.py` and `code/models/evaluate.py`; verify models train without OOM/GPU errors, cross-validation scores are logged, and DeLong's test confirms significance.

### Tests for User Story 2

- [ ] T017 [P] [US2] Unit test for stratified split logic ensuring label balance in `tests/unit/test_split.py`
- [X] T018 [P] [US2] Integration test verifying RF and XGBoost train within 30 mins on 2-core CPU without GPU errors in `tests/integration/test_train.py`
- [X] T019 [P] [US2] Unit test for DeLong's test implementation against known synthetic AUC pairs in `tests/unit/test_stats.py`

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement `code/models/train.py` to train RandomForest and XGBoost using `joblib` for parallelism on 2 cores. **Logic**: Perform `n_estimators` grid search across a range of values for both models. **Selection Metric**: Select the model with the **highest mean CV AUC**. (FR-004)
- [X] T021 [US2] Implement `code/models/train.py` to train KNN Baseline (K=5) using the **phylogenetic distance matrix**. **Logic**:
 - **Check**: If `data/processed/real_phylo_matrix.npy` exists (from T016c), use that.
 - **If EXISTS**: Train KNN on real phylogenetic matrix.
 - **If NOT EXISTS**:
 - If `VALIDATION_MODE` is False, **raise a critical error** ("FR-009 VIOLATION: Real phylogenetic matrix required but missing. Halting execution.").
 - If `VALIDATION_MODE` is True, use `data/processed/synthetic_phylo_matrix.npy` (from T016a) and **explicitly log a REDEFINITION of FR-009** (synthetic baseline used instead of real phylogeny) invalidates SC-001.
 **Verification**: If the synthetic matrix is used: If `VALIDATION_MODE` is False, **raise a critical error** (FR-009 Violation). If `VALIDATION_MODE` is True, output must explicitly state "Baseline: Synthetic-only, Not biologically valid; **REDEFINITION of FR-009** (synthetic baseline used instead of real phylogeny) invalidates SC-001". (FR-009, Plan Validation Mode)
- [X] T022 [US2] Implement `code/models/evaluate.py` to calculate ROC-AUC on held-out test set and log best model. (FR-004)
- [X] T023 [US2] Implement `code/models/evaluate.py` to perform DeLong's test comparing best model AUC vs. Baseline AUC. **Verify p < 0.05 AND AUC diff > 0.05** as per SC-001. **Failure Handling**: If condition fails: If `VALIDATION_MODE` is False, **raise a `CriticalValidationFailure`**. If `VALIDATION_MODE` is True, log "Validation Failed" warning, set `metrics.json` flag `sc001_passed` to false, and **continue** execution. (FR-010, SC-001)
- [X] T024 [P] [US2] Implement `code/models/train.py` to add error handling for OOM/GPU exceptions, failing gracefully with clear messages. (Edge Case)
- [X] T038 [P] [US2] Implement `code/models/train.py` to add a **runtime memory monitoring** step (using `psutil`) that logs peak memory usage at the start and end of training, ensuring compliance with the RAM limit. (Review Concern: Resource Constraints)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. Models are trained and statistically compared.

---

## Phase 5: User Story 3 - Statistical Comparison and Interpretation (Priority: P3)

**Goal**: Compare classifiers via paired t-test and generate feature importance rankings.

**Independent Test**: Run `code/models/compare.py`; verify p-value is generated and top features are ranked distinguishing genomic vs physiological.

### Tests for User Story 3

- [ ] T025 [P] [US3] Unit test for paired t-test on synthetic CV score arrays in `tests/unit/test_compare.py`
- [ ] T026 [P] [US3] Integration test verifying feature importance output matches top expected synthetic features in `tests/integration/test_compare.py`. **Verification**: Verify the output list contains the features defined in the synthetic generator config. and is saved to `data/logs/feature_importance.json`. (Review Concern: Writing)

### Implementation for User Story 3

- [ ] T027 [P] [US3] Implement `code/models/compare.py` to perform paired t-test on k-fold CV AUC scores for RF vs. XGBoost (FR-005, SC-003)
- [ ] T028 [P] [US3] Implement `code/models/compare.py` to calculate **Permutation Feature Importance** for the best model, distinguishing between genomic markers and physiological traits. **Logic**: **Tie-Breaking**: If importance scores are tied, sort alphabetically by gene name to ensure deterministic output. **Verification**: Verify the output report explicitly categorizes the top features into "Genomic" and "Physiological" groups. **Output**: Save to `data/logs/feature_importance.json` with the deterministic tie-breaking applied. (FR-006, Review Concern: Writing)
- [ ] T029 [US3] Implement `code/models/compare.py` to generate a final report at `docs/reports/final_analysis.md`. **Validation Logic**:
 - **Step 1**: Load the **15 independent validation genes** from `code/config.py` (T011c).
 - **Step 2**: Load the **hidden subset of genes** from `data/logs/generation_config.json` (generated by T012, key `hidden_subset`) for synthetic validation.
 - **Step 3**: **Verify**: Confirm these 15 genes are strictly disjoint from the 20 training genes in T012.
 - **Step 4**: Select "Top features" as **all available features if < 10, otherwise Top 10** (read from `data/logs/feature_importance.json` generated by T028).
 - **Step 5**: **Check**: Count overlap between Top features and the **15 real independent validation genes**.
 - **Logic**:
 - **If Real Data**: If count >= 3, report "SC-005 Passed". If count < 3: If `VALIDATION_MODE` is False, **raise `CriticalValidationFailure`**. If `VALIDATION_MODE` is True, set `sc005_passed=false` and report "SC-005 Failed".
 - **If Synthetic Data**: Perform a **proxy validation** against the *hidden subset of 5 genes* used to generate the label (from `data/logs/generation_config.json`). If count >= 3, report "Synthetic Ground Truth Validated". If count < 3, report "Synthetic Ground Truth Validation Failed". **Explicitly log a REDEFINITION of SC-005** for Validation Mode.
 - **Step 6**: **Tie-Breaking**: Read Top 10 from `data/logs/feature_importance.json` (which was generated with alphabetical tie-breaking in T028).
 - **Verification**: Verify `docs/reports/final_analysis.md` contains a section listing the 15 validation genes and explicitly states the count found in Top features (or proxy result). (SC-005, Plan Validation Mode)
- [X] T030 [US3] Ensure all metrics and logs are written to `data/logs/metrics.json` for reproducibility (Plan: Single Source of Truth). **Verification**: Verify `data/logs/metrics.json` exists and contains keys: `auc_rf`, `auc_xgb`, `p_value_delong`, `excluded_species_count`, `imputation_method`, `power_analysis`, `data_lineage`, `sc_passed`, `sc005_passed` with non-null values. (FR-007)
- [ ] T039 [US3] Update `code/models/compare.py` to include a **power analysis** calculation in the report, explicitly stating the statistical power of the test given the small N=50 sample size, and marking the results as "Preliminary" if power < 0.8. **Verification**: Update `code/models/compare.py` to output power analysis results to `data/logs/metrics.json` and verify the report includes the calculated power value. (Review Concern: Statistical Rigor)
- [X] T040 [US3] Update `docs/reports/final_analysis.md` to include a **Data Lineage Section** that explicitly traces the origin of every feature (TRY URL vs. Synthetic Generator) and the exact logic used for label generation, preventing circularity in the validation. **Note**: This task fully satisfies the "Data Lineage Validation" requirement (previously flagged as T042). **Verification**: Verify `docs/reports/final_analysis.md` contains a "Data Lineage" section with a table mapping every feature to its source (TRY URL or Synthetic Generator). (Review Concern: Transparency)

**Checkpoint**: All user stories should now be independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T031 [P] Documentation updates in `docs/reports/` including the limitation note regarding synthetic data
- [X] T032 Code cleanup and refactoring to ensure type hinting and docstrings are complete
- [X] T033 [P] Add unit tests for edge cases: empty species list, missing TRY data, single species in dataset
- [ ] T041 [P] [Polish] Create `code/run_pipeline.py` as the single entry point script referenced in `quickstart.md`. **Logic**: Create the **full implementation** of the script that chains T011a, T011b, T012, T013, T015, T020, T021, T022, T023, T027, T028, T029.
 - **Specific Logic**:
 1. Import `download_try`, `fetch_ncbi`, `generate_synthetic`, `merge_data`, `impute_data`, `split_data`, `train_models`, `evaluate_models`, `compare_models`, `generate_report` from respective modules.
 2. Call `download_try()` -> `fetch_ncbi()` -> `generate_synthetic()` (if needed) -> `merge_data()` -> `impute_data()` -> `split_data()` -> `train_models()` -> `evaluate_models()` -> `compare_models()` -> `generate_report()`.
 3. Add a `--mode` flag to toggle `VALIDATION_MODE`.
 4. Add error handling for each step: if any step fails, log the error and halt execution.
 - **Verification**: Verify `code/run_pipeline.py` exists, accepts `--mode` flag, and executes the full pipeline. **Note**: Full chain execution verification is deferred to T034. **Command**: `python code/run_pipeline.py --mode validation`. Exit code 0. (Execution Feedback: Run-book mismatch)
- [X] T035 Verify `code/requirements.txt` pins versions to ensure reproducibility (Constitution: Reproducibility)
- [ ] T034 [P] [Polish] Run `quickstart.md` validation: Execute `python code/run_pipeline.py --mode validation` (T041) and **verify runtime < 30 minutes** (FR-008, SC-002). **Note**: T041 must exist before this task runs. **Verification**: Verify full chain execution (T011a-T029) completes successfully.

---

## Phase 7: Revision & Verification (Review Concerns)

**Goal**: Address specific gaps identified in the plan/specification review regarding data integrity and statistical rigor.
**Note**: This phase addresses review concerns. T042 (Data Lineage Validation) was removed as it is fully covered by T040 in Phase 5.

- [ ] T043 [US3] **Review Concern: Data Source Verification**. Update `code/data/download.py` inside the `download_try()` function to explicitly verify that the TRY database URL provided in `config.py` is accessible and returns a valid CSV before proceeding with the full download. **Logic**: Add a `HEAD` request check or a small `GET` request with a byte limit to verify the URL is valid. If invalid, log a critical error and exit. **Verification**: Verify that an invalid URL in `config.py` causes the pipeline to fail with a clear error message before any large download attempts. (Review Concern: Data Source Verification)
- [X] T044 [US3] **Review Concern: Phylogenetic Tree Availability**. Update `code/data/download.py` inside the `fetch_tree()` function to explicitly check for the existence of a valid phylogenetic tree source (OpenTree of Life) and log a clear warning if the tree cannot be retrieved, ensuring the user is aware that Phylogenetic MICE will be replaced by Median Substitution. **Logic**: Add a check in T016c to verify the OpenTree API response. If the tree is not found, log a warning "Phylogenetic tree not found; Median Substitution will be used". **Verification**: Verify that the log contains the warning message when the tree is unavailable. (Review Concern: Phylogenetic Tree Availability)
- [ ] T045 [US3] **Review Concern: Synthetic Data Validation**. Update `code/data/generate.py` inside the `generate_synthetic_genomics()` function to include a **validation step** for the synthetic genomic data and labels. **Logic**: After generating the synthetic data, run a Chi-Square Goodness-of-Fit test to verify that the label distribution matches the expected sigmoid probability. If the p-value is < 0.05, log a warning "Synthetic data distribution deviates significantly from expected; consider adjusting parameters". **Verification**: Verify that the log contains the warning message if the distribution deviates. (Review Concern: Synthetic Data Validation)
- [X] T046 [US3] **Review Concern: Model Performance Validation**. Update `code/models/evaluate.py` inside the `calculate_auc()` method to include a **validation step** for the model performance. **Logic**: After calculating the ROC-AUC, compare the result against a baseline random classifier (AUC=0.5). If the AUC is not significantly better than 0.5 (p < 0.05), log a warning "Model performance is not significantly better than random; consider revising the model or features". **Verification**: Verify that the log contains the warning message if the model performance is poor. (Review Concern: Model Performance Validation)
- [ ] T047 [US3] **Review Concern: Feature Importance Validation**. Update `code/models/compare.py` inside the `calculate_importance()` function to include a **validation step** for the feature importance rankings. **Logic**: After calculating the feature importance, verify that the top features are not all from the same category (e.g., all genomic or all physiological). If the top-ranked features are all from one category, log a warning "Feature importance is dominated by one category; consider revising the model or features". **Verification**: Verify that the log contains the warning message if the feature importance is dominated by one category. (Review Concern: Feature Importance Validation)
- [X] T048 [US3] **Review Concern: Report Completeness**. Update `docs/reports/final_analysis.md` template to include a **section** that explicitly addresses the limitations of the study, including the use of synthetic data, the small sample size, and the lack of a verified phylogenetic tree. **Logic**: Add a "Limitations" section to the report that discusses these issues. **Verification**: Verify that the report contains the "Limitations" section. (Review Concern: Report Completeness)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Revision (Phase 7)**: Can be implemented in parallel with US3 or after US3 completion, as it primarily involves logging and reporting enhancements.

### Explicit Artifact Dependencies

- **T013 (Merge)** depends on **T011a (Download)** and **T012 (Generate)** (now in Phase 2) OR **T011b (Real Fetch)**.
- **T015 (Split)** depends on **T013 (Merge)**.
- **T014a (Imputation)** depends on **T013 (Merge)** and **T016c (Real Tree)**. **Requires: T016c**.
- **T020 (Train RF/XGBoost)** depends on **T015 (Split)**.
- **T021 (Baseline)** depends on **T016a (Synthetic Matrix)** and **Optional T016c (Real Matrix)**.
- **T022 (Evaluate)** depends on **T020 (Train)**.
- **T023 (DeLong)** depends on **T022 (Evaluate)** and **T021 (Baseline)**.
- **T027 (T-Test)** depends on **T020 (Train)**.
- **T028 (Importance)** depends on **T020 (Train)**.
- **T029 (Report)** depends on **T028 (Importance)**, **T027 (T-Test)**, and **T011c (Validation Genes)**.
- **T037** depends on **T013** (modifies ingest logging).
- **T038** depends on **T020** (modifies training execution).
- **T039** depends on **T027** (modifies comparison logic).
- **T040** depends on **T029** (modifies report generation to include lineage).
- **T041** depends on **T001** (project structure) and **T011a-T029** (all pipeline steps).
- **T034** depends on **T041** (T041 must exist before this task runs).
- **T036** -> **Removed (Merged into T011a)**.
- **T049-T060** -> **Removed per concern request to avoid coarse granularity and scope creep**.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, **US1** can start immediately.
- **US2** implementation can start once T015 (Split) is complete.
- **US3** implementation can start once US2 is complete.
- **T021 (Baseline)** can run in **parallel** with **T020 (RF/XGBoost)** training, as T021 does not depend on the train/test split, only on the matrix (T016a/T016c) which is ready in Phase 2. **(Note: T021 is NOT [P] in the list above to avoid file conflicts in train.py, but logic allows parallel execution if file isolation is ensured).**
- All tests for a user story marked [P] can run in parallel (after code exists).
- **T037, T038, T039, T040** can be implemented in parallel as they affect distinct files or add non-blocking logging/reporting features.
- Different user stories can be worked on in parallel by different team members **once their specific data dependencies are met**.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (after code exists):
Task: "Unit test for TRY download retry logic"
Task: "Unit test for synthetic genomic data generation"
Task: "Integration test for full merge pipeline"

# Launch all models for User Story 1 together:
Task: "Implement download.py"
Task: "Implement ingest.py"
Task: "Implement split.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify synthetic data generation and merge)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Requires US1 data)
4. Add User Story 3 → Test independently → Deploy/Demo (Requires US2 models)
5. Add Phase 7 (Revision/Verification) → Enhance logging, monitoring, and reporting → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Model Training) - **Must wait for T015 (Split) from US1**
 - Developer C: User Story 3 (Analysis) - **Must wait for US2**
 - Developer D: Phase 7 (Revision/Verification) - **Can start once core logic is in place**
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical Constraint**: All genomic data and labels are SYNTHETIC (per Plan) by default if real data is missing and `VALIDATION_MODE` is True. No real NCBI RefSeq or TRY genomic data is used unless explicitly available.
- **Critical Constraint**: Phylogenetic MICE is replaced by Median Substitution (Constitution VI) if a verified phylogenetic tree is unavailable.
- **Critical Constraint**: Baseline model uses a synthetic distance matrix if a real tree is not provided.
- **Critical Constraint (Revision)**: Data loaders must fail loudly on missing sources in Production Mode (`VALIDATION_MODE` = False); synthetic fallback is only for the *validation* run when `VALIDATION_MODE` is True.
- **Critical Constraint (Label)**: Synthetic labels include noise to prevent perfect correlation (AUC=1.0), ensuring meaningful statistical testing.
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [ ] T041 Reconcile run-book vs implementation for `code/run_pipeline.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/run_pipeline.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
