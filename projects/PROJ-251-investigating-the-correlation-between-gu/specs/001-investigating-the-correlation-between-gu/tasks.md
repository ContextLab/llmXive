---
description: "Task list template for feature implementation"
---

# Tasks: Investigating the Correlation Between Gut Microbiome Composition and Immune Response to Influenza Vaccination

**Input**: Design documents from `/specs/001-investigating-the-correlation-between-gu/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `data/`, `tests/` at repository root (per plan.md structure)
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

- [ ] T001 Create project directories explicitly: `code/`, `data/raw`, `data/processed`, `data/results`, `specs/001-investigating-the-correlation-between-gu/contracts/`
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (pandas, numpy, scipy, scikit-learn, pyyaml, requests, biom-format, sra-tools, qiime2, dada2)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create configuration module `code/utils/config.py` with paths, seeds, and thresholds
- [X] T005 [P] Implement schema validators `code/utils/validators.py` for dataset, correlation, and model metrics
- [X] T006 [P] Setup logging infrastructure in `code/utils/logging_config.py` to capture exclusion counts and errors
- [X] T007 Create base data loading helpers in `code/utils/data_loader.py`
- [ ] T008 Setup environment configuration management (`.env` handling for API keys if needed)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Validation (Priority: P1) 🎯 MVP

**Goal**: Ingest pre-processed 16S rRNA OTU tables and serology metadata, filtering for complete records.

**Independent Test**: The system can be tested by running the ingestion script against a known valid subset and verifying the output CSV contains exactly N rows (N ≥ 50) with no nulls in required columns.

### Strategy A: Primary Data Fetch (NCBI SRA)

- [ ] T011a [US1] **Orchestration & Strategy A**: Implement the main ingestion logic in `code/01_ingest.py` that attempts to fetch pre-processed data for a selected accession.
  - *Source*: Use NCBI E-utilities API: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=bioproject&term=SRP053178` to verify existence, then fetch associated metadata/OTU tables if available via canonical URLs.
  - *Constraint*: If the primary fetch fails at the specific URL, raise `DataUnavailableError`. Do NOT fall back to synthetic data.
  - *Output*: `data/raw/otutable.csv`, `data/raw/serology.csv`.
- [ ] T011b [US1] **Strategy B (Fallback)**: If Strategy A fails, implement logic to download raw FASTQ files for SRP053178 using `sra-tools` (prefetch/fasterq-dump).
  - *Trigger*: ONLY if T011a fails.
  - *Output*: Raw FASTQ files in `data/raw/fastq/`.
- [ ] T011c [US1] **Strategy B (Processing)**: If T011b succeeds, run 16S processing pipeline (QIIME2 or DADA2) to generate OTU table.
  - *Trigger*: ONLY if T011b succeeds.
  - *Output*: `data/raw/otutable_raw.csv`.
- [ ] T011d [US1] **Strategy B (Merge)**: Merge generated OTU table with serology metadata using `subject_id`.
  - *Trigger*: ONLY if T011c succeeds.

### Strategy C: Filtering & Validation

- [X] T012 [US1] Implement filtering logic in `code/01_ingest.py` to exclude subjects missing baseline or post-vaccination titers.
- [ ] T013 [US1] **LOD Handling (Exclude Only)**: Implement handling for subjects with antibody titers below limit of detection (LOD).
  - *Logic*: **EXCLUDE** subjects with missing titers to satisfy FR-001.
  - *Constraint*: Imputation (LOD/2) is strictly forbidden unless a spec amendment explicitly authorizes it. The default behavior MUST be exclusion.
  - *Output*: `data/processed/filtered_data.csv`.
- [X] T014a [US1] **Validation Gate**: Implement sample size validation in `code/01_ingest.py`.
  - *Logic*: Calculate N (count of subjects with complete data) AFTER filtering (T012/T013).
  - *Check*: **Check N >= 50 BEFORE any sampling logic; if N < 50, raise ValueError immediately. **
  - *Action*: If N < 50, raise `ValueError("ERR_NO_DATA: Insufficient Sample Size (N < 50)")`.
  - *Dependency*: This check MUST occur BEFORE any sampling logic.
- [X] T015b [US1] **Logging N**: Log N to `data/results/N_count.json`.
  - *Logic*: Write N to `data/results/N_count.json` **unconditionally** (both success and failure paths) BEFORE T014a raises an error or the pipeline continues.
  - *Output*: `data/results/N_count.json`.
  - *Constraint*: This task MUST run before T014a raises an exception to ensure the "Single Source of Truth" artifact exists even on failure.
- [ ] T014b [US1] **Dynamic Sampling**: Implement stratified random sampling in `code/01_ingest.py`.
 - *Trigger*: ONLY IF T015b passes (N >= 50) AND the dataset exceeds available RAM (defined as `psutil.virtual_memory.available < 6GB`) AND **N > 50 + [deferred] buffer**.
  - *Logic*: Perform stratified random sampling to reduce size while preserving class balance. **Stratify by 'responder_status' if available; otherwise, stratify by 'titer_post' quantiles.**
  - *Constraint*: **Pre-check**: If N <= 50 + buffer, SKIP sampling. Do NOT sample if it risks reducing N below 50.
  - *Output*: If sampled, write to `data/processed/filtered_data_sampled.csv`. If not sampled, no new file.
  - *Depends on*: T015b success.
- [ ] T016 [US1] **Write Final Validated Dataset**: Write the final dataset to `data/processed/final_validated_data.csv`.
  - *Input Logic*: Read `data/processed/filtered_data_sampled.csv` if it exists (from T014b), otherwise read `data/processed/filtered_data.csv` (from T013).
  - *Output*: `data/processed/final_validated_data.csv`.
- [ ] T017 [US1] Validate output against `specs/001-investigating-the-correlation-between-gu/contracts/dataset.schema.yaml`.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T009 [P] [US1] Contract test for data schema validation in `code/tests/test_ingest.py`: Add function `test_validate_schema_loads_yaml`.
- [ ] T010 [P] [US1] Integration test for data filtering logic in `code/tests/test_ingest.py`: Add function `test_filter_excludes_null_titers`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Correlation Analysis and Multiple Testing Correction (Priority: P2)

**Goal**: Calculate diversity metrics, apply CLR transformation, and perform Spearman correlation with BH correction.

**Independent Test**: The system can be tested by running analysis on a synthetic dataset with known correlations and verifying correct identification of significant taxa and adjusted p-values.

### Implementation for User Story 2

- [ ] T019 [US2] Implement zero-variance taxa exclusion in `code/02_preprocess.py`: Filter out taxa with negligible variance across all subjects BEFORE transformation to avoid division-by-zero.
  - *Input*: `data/processed/final_validated_data.csv`.
  - *Output*: `data/processed/filtered_no_zero_var.csv`.
- [ ] T020 [US2] Implement Centered Log-Ratio (CLR) transformation in `code/02_preprocess.py` (handle zeros with pseudocount = 1e-6).
  - *Input*: `data/processed/filtered_no_zero_var.csv`.
  - *Output*: `data/processed/cleared_default.csv`.
- [ ] T020-B [US2] Implement Pseudocount Sensitivity Analysis in `code/02_preprocess.py`:
  - *Input*: `data/processed/filtered_no_zero_var.csv` (Run directly on this file, not T020 output).
  - *Logic*: Run CLR with multiple pseudocounts spanning several orders of magnitude. Compare the stability of the most significant taxa across these runs.
  - *Metric*: Determine the 'top-10' taxa for each run by the **absolute value of the correlation coefficient (|rho|)** from the raw (unadjusted) correlation test. Calculate the **Jaccard index** of these top-10 sets across pseudocount runs.
  - *Output*: Write the Jaccard stability matrix and top-10 taxa lists to `data/results/pseudocount_sensitivity.json`.
- [ ] T021 [US2] Implement Shannon diversity index calculation in `code/02_preprocess.py` using `data/processed/cleared_default.csv` (CLR-transformed data).
- [ ] T022 [US2] Implement log-transformation of antibody titers in `code/02_preprocess.py`.
- [ ] T023 [US2] Implement Spearman rank correlation test in `code/03_correlation.py` (exclude zero-variance taxa).
- [ ] T024 [US2] Implement Benjamini-Hochberg FDR correction in `code/03_correlation.py`.
- [ ] T025 [US2] Write correlation results (coeff, raw p, adj p) to `data/results/correlation_results.csv`.
  - *Validation*: Count taxa with adj-p < 0.05. Compare against the expected range of low to high single-digit values. Log a warning if count is outside this range and flag result as "OUT_OF_EXPECTED_RANGE" in `data/results/significant_taxa_count.json`.
  - *Action*: If the count falls outside this range, log a warning and flag the result as "OUT_OF_EXPECTED_RANGE" in `data/results/significant_taxa_count.json`.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for CLR transformation logic in `code/tests/test_correlation.py`: Add function `test_clr_transform_handles_zeros`.
- [ ] T019 [P] [US2] Unit test for Benjamini-Hochberg correction in `code/tests/test_correlation.py`: Add function `test_bh_correction_adjusts_pvalues`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Predictive Modeling and Nested Cross-Validation (Priority: P3)

**Goal**: Train Random Forest classifier with nested CV, ensuring feature selection occurs inside the training loop.

**Independent Test**: The system can be tested by running training on the ingested dataset and verifying that feature selection is logged within each fold and accuracy is reported.

### Implementation for User Story 3

- [ ] T030a [US3] Implement seroconversion logic (≥4-fold rise in titer) in `code/04_modeling.py` using columns `titer_baseline` and `titer_post` with formula `post / pre >= 4`.
- [ ] T030b [US3] Implement absolute titer logic (e.g., HAI ≥ 40) in `code/04_modeling.py`.
- [ ] T030c [US3] Implement threshold parameterization for responder definition in `code/04_modeling.py`.
- [ ] T030d [US3] Apply responder definition to dataset in `code/04_modeling.py`.
- [ ] T031 [US3] Implement an outer k-fold cross-validation split loop in `code/04_modeling.py`.
- [ ] T032 [US3] Implement an inner cross-validation loop for feature selection and hyperparameter tuning in `code/04_modeling.py`.
  - *Constraint*: Feature selection (identifying top taxa) MUST be performed dynamically within each inner fold using **ONLY the training split data from the current outer fold**. Do NOT use the global dataset or the test split of the outer fold for feature selection to prevent data leakage.
- [ ] T033 [US3] Implement Random Forest classifier training in `code/04_modeling.py` (CPU-only, default precision).
- [ ] T034a [US3] Implement permutation baseline testing: Generate null distribution of accuracy scores by permuting microbiome rows relative to serology labels (feature permutation) multiple times with `random_seed=42` in `code/04_modeling.py`. Output `data/results/null_distribution.csv`.
- [ ] T034b [US3] Implement Threshold Sweep & Robustness Check in `code/04_modeling.py`:
  - *Depends on*: T031, T032, T033, T034a.
  - *Logic*: Sweep responder threshold ±10% of the defined cutoff (4-fold rise) in **5 steps** (0.9x, 0.95x, 1.0x, 1.05x, 1.1x). Re-run the nested CV pipeline for each threshold step, and compare accuracy against the null distribution generated in T034a.
  - *Optimization*: If estimated runtime > 5.5h, reduce inner CV folds to 3 or use a subset of thresholds to ensure completion within 6h.
  - *Output Schema*: Write to `data/results/sensitivity_analysis.csv` with columns: `threshold_factor`, `accuracy_mean`, `accuracy_std`, `p_value_vs_null`.
- [ ] T035 [US3] Implement Statistical Comparison in `code/04_modeling.py`:
  - *Depends on*: T034a.
  - *Logic*: Calculate p-value comparing Random Forest accuracy (from T033/T031/T032) against the null distribution generated in T034a. If p < 0.05, set `status='significant'`. Else, set `status='not_significant'`. Write status to `data/results/model_significance.json`.
  - *Constraint*: **Do NOT halt the pipeline** if the result is not significant. A non-significant result is a valid scientific outcome. Log result as significant or not significant; do not halt.
  - *Output*: `data/results/model_significance.json`.
- [ ] T036 [US3] Calculate and log confusion matrix, precision, recall, F1-score for high/low responders.
- [ ] T037 [US3] Write model metrics to `data/results/model_metrics.json`.
- [ ] T038 [US3] Validate output against `specs/001-investigating-the-correlation-between-gu/contracts/model_metrics.schema.yaml`.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Unit test for nested CV structure in `code/tests/test_modeling.py`: Add function `test_nested_cv_feature_selection_is_isolated`.
- [ ] T029 [P] [US3] Integration test for model performance metrics in `code/tests/test_modeling.py`: Add function `test_model_metrics_match_expected_format`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T039 Run ruff check and black format on all files in code/ and fix all reported issues
- [ ] T040a [P] [US1] Unit test for zero-variance taxa exclusion in `code/tests/test_preprocess.py`: Add function `test_zero_variance_taxa_exclusion`.
- [ ] T040b [P] [US1] Unit test for LOD handling in `code/tests/test_ingest.py`: Add function `test_lod_exclusion_logic`.
- [ ] T040c [P] [US2] Unit test for CLR pseudocount edge cases in `code/tests/test_correlation.py`: Add function `test_clr_pseudocount_handles_extreme_zeros`.
- [ ] T041 Run quickstart.md validation
- [ ] T042 Implement runtime monitoring in code/utils.py to log total runtime to `data/results/resource_usage.json` and assert < 21600s (6h).
- [ ] T043 Implement memory monitoring in code/utils.py to log peak memory to `data/results/resource_usage.json` and assert < 7340 MB (7GB).
- [ ] T044 [US1] Address FR-001 requirement: Verify data validation error messages provide actionable guidance to the user, including specific details about missing values or invalid formats in `code/01_ingest.py`. Rationale: Improve usability and debugging experience for users encountering data quality issues.
- [ ] T045 [US2] Address SC-004 requirement: Implement the **Significant Taxa Count** check. Count taxa with adj-p < 0.05 and compare against the expected range (low to high single-digit). Log the count and flag if outside range in `data/results/significant_taxa_count.json`. Rationale: Ensure statistical findings align with biological expectations.
- [ ] T046 [US3] Address FR-006 requirement: Implement a permutation baseline test to statistically validate the predictive power of the Random Forest model, minimizing the risk of false positives due to random chance in `code/04_modeling.py`. Rationale: Strengthen confidence in the model's ability to accurately predict responder status.

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
- **User Story 2 (P2)**: Depends on User Story 1 (requires `data/processed/final_validated_data.csv`)
- **User Story 3 (P3)**: Depends on User Story 2 (requires `data/results/correlation_results.csv` for feature selection validation, though feature selection itself is local to the loop)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services (N/A for data pipeline)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (code-wise), but execution remains sequential.
- **CRITICAL SEQUENTIAL DEPENDENCY**: Within Phase 5, Task T034a (Permutation Baseline) must finish before Task T034b (Threshold Sweep) and T035 (Statistical Comparison) can begin. T034b re-runs the entire nested CV for each threshold step.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (Verify N ≥ 50)
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
 - Developer A: User Story 1 (Data Ingestion)
 - Developer B: User Story 2 (Correlation Logic)
 - Developer C: User Story 3 (Modeling Logic)
3. Stories complete and integrate independently (execution order enforced by data flow)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All tasks must run on CPU-only GitHub Actions free-tier runners (≤7GB RAM, ≤6h). No GPU, no 8-bit quantization.
- **Data Strategy**: T011a (Strategy A) is preferred; T011b-d (Strategy B) is conditional fallback if T011a fails.
- **Sequential Dependency**: T034b depends on the output of T034a.
- **Data Integrity**: Real data must be streamed or sampled honestly. Synthetic fallbacks are strictly forbidden.