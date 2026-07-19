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

**Independent Test**: The system can be tested by running the ingestion script against a known valid subset and verifying the output CSV contains exactly N rows (N ≥ 50) with no nulls in required columns. [UNRESOLVED-CLAIM: c_428dfbd2 — status=not_enough_info]

### Strategy A: Primary Data Fetch (NCBI SRA)

- [ ] T011a [US1] Implement Strategy A: Fetch pre-processed OTU table and serology metadata for accession SRP053178 from NCBI SRA. <!-- FAILED: unspecified -->
 - *Method*: Use `sra-tools` (prefetch/fasterq-dump) or E-utilities API to retrieve metadata and raw data. If a pre-processed CSV/Parquet is available via a verified public mirror at `, use that; otherwise, download raw FASTQ and process via Strategy B logic.
 - *Constraint*: If the primary fetch fails at the specific URL, raise `DataUnavailableError` immediately. Do NOT fall back to synthetic data.
 - *Output*: `data/raw/otutable.csv`, `data/raw/serology.csv` (or raw FASTQ if pre-processed unavailable).

### Strategy B: Fallback Raw FASTQ Processing (Conditional)

- [ ] T011b [US1] Implement Strategy B: Download raw FASTQ files from NCBI SRA for the target study accession. <!-- FAILED: unspecified -->
 - *Trigger*: ONLY if Strategy A (T011a) fails to retrieve pre-processed data.
 - *Depends on*: T011a failure.
 - *Method*: Use `prefetch` and `fasterq-dump` from `sra-tools` to retrieve all run IDs associated with SRP053178.
- [ ] T011c [US1] Implement Strategy B: Run 16S processing pipeline on raw FASTQ to generate OTU table.
 - *Trigger*: ONLY if T011b succeeds and Strategy A failed.
 - *Method*: Run QIIME2 (Docker: `qiime2/2023.7`) or DADA2 (Docker: `bioconductor/dada2:latest`).
 - *Parameters*: `truncLen=240`, `chimeraMethod=pooled`.
 - *Output*: `data/raw/otutable_raw.csv`.
- [ ] T011d [US1] Implement Strategy B: Merge generated OTU table with serology metadata using `subject_id`.
 - *Trigger*: ONLY if T011c succeeds.
- [X] T011e [US1] Implement orchestration logic in `code/01_ingest.py`:
 - *Logic*: Attempt T011a. If T011a fails, trigger T011b -> T011c -> T011d sequentially.
 - *CRITICAL*: If all real data fetch strategies fail, raise `DataUnavailableError` immediately. Do NOT fall back to synthetic/mock data.

### Strategy C: Dynamic Sampling & Filtering

- [X] T012 [US1] Implement filtering logic in `code/01_ingest.py` to exclude subjects missing baseline or post-vaccination titers.
- [ ] T013 [US1] Implement handling for subjects with antibody titers below limit of detection (LOD).
 - *Logic*: Default behavior is to **EXCLUDE** subjects with missing titers to satisfy FR-001.
 - *Research Variant*: Imputation with half the LOD (e.g., `LOD/2`) is ONLY allowed if explicitly enabled in `config.py` AND a spec amendment is present; this path does NOT satisfy the primary FR-001 acceptance criteria without that amendment.
 - *LOD Calculation*: If imputation is enabled, calculate `LOD = min(non-zero titer value)` across the dataset. If no non-zero value exists, raise `ValueError("LOD undefined")`.
 - *Requirement*: The choice (exclude vs impute) must be configurable via `config.py` and logged in the execution log.
 - *Output*: `data/processed/filtered_data.csv`.
- [X] T014a [US1] **Validation Gate**: Implement sample size validation in `code/01_ingest.py`.
 - *Logic*: Calculate N (count of subjects with complete data) AFTER filtering (T012/T013).
 - *Check*: **Check N >= 50 BEFORE any sampling logic; if N < 50, raise ValueError immediately. [UNRESOLVED-CLAIM: c_883f98e5 — status=not_enough_info]**
 - *Action*: If N < 50, raise `ValueError("ERR_NO_DATA: Insufficient Sample Size (N < 50)")`, log N to `data/results/N_count.json`, and HALT execution immediately.
 - *Dependency*: This check MUST occur BEFORE any sampling logic.
- [X] T014b [US1] **Dynamic Sampling**: Implement stratified random sampling in `code/01_ingest.py`.
 - *Trigger*: ONLY IF T014a passes (N >= 50) AND the dataset exceeds available RAM (defined as `psutil.virtual_memory().available < 6GB`).
 - *Logic*: Perform stratified random sampling to reduce size while preserving class balance. [UNRESOLVED-CLAIM: c_62af86d0 — status=not_enough_info] Log the sampling method, final N, and write to `data/processed/filtered_data.csv`.
 - *Constraint*: If sampling reduces N to < 50, raise `ValueError("ERR_NO_DATA: Sampling reduced N below threshold")`.
 - *Depends on*: T014a success.
- [ ] T016 [US1] Write filtered dataset to `data/processed/filtered_data.csv` and log exclusion counts.
- [ ] T017 [US1] Validate output against `specs/001-investigating-the-correlation-between-gu/contracts/dataset.schema.yaml`.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Contract test for data schema validation in `code/tests/test_ingest.py`: Add function `test_validate_schema_loads_yaml`.
- [ ] T010 [P] [US1] Integration test for data filtering logic in `code/tests/test_ingest.py`: Add function `test_filter_excludes_null_titers`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Correlation Analysis and Multiple Testing Correction (Priority: P2)

**Goal**: Calculate diversity metrics, apply CLR transformation, and perform Spearman correlation with BH correction.

**Independent Test**: The system can be tested by running analysis on a synthetic dataset with known correlations and verifying correct identification of significant taxa and adjusted p-values.

### Implementation for User Story 2

- [ ] T019 [US2] Implement zero-variance taxa exclusion in `code/02_preprocess.py`: Filter out taxa with negligible variance across all subjects BEFORE transformation to avoid division-by-zero.
- [ ] T020 [US2] Implement Centered Log-Ratio (CLR) transformation in `code/02_preprocess.py` (handle zeros with pseudocount = 1e-6).
- [ ] T020-B [US2] Implement Pseudocount Sensitivity Analysis in `code/02_preprocess.py`:
 - *Input*: Results from T020 (and other pseudocount runs: `1e-9`, `1e-6`, `1e-3`, `1e-1`).
 - *Logic*: Run CLR with multiple pseudocounts. Compare the stability of the most significant taxa across these runs, explicitly referencing the Plan's requirement to 'Compare the stability of the most significant taxa'.
 - *Metric*: Calculate the **Jaccard index** of the top-10 taxa sets across pseudocount runs to quantify stability.
 - *Output*: `data/results/pseudocount_sensitivity.json`.
- [ ] T021 [US2] Implement Shannon diversity index calculation in `code/02_preprocess.py` using `data/processed/cleared_default.csv` (CLR-transformed data).
- [ ] T022 [US2] Implement log-transformation of antibody titers in `code/02_preprocess.py`.
- [ ] T023 [US2] Implement Spearman rank correlation test in `code/03_correlation.py` (exclude zero-variance taxa).
- [ ] T024 [US2] Implement Benjamini-Hochberg FDR correction in `code/03_correlation.py`.
- [ ] T025 [US2] Write correlation results (coeff, raw p, adj p) to `data/results/correlation_results.csv`.
 - *Validation*: Count taxa with adj-p < 0.05. Compare against the expected range of low to high single-digit values.
 - *Action*: If the count falls outside this range, log a warning and flag the result as "OUT_OF_EXPECTED_RANGE" in `data/results/significant_taxa_count.json`. This is a validation check, not a hard halt, but must be reported.

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
 - *Depends on*: T034a.
 - *Logic*: Sweep responder threshold ±10% of the defined cutoff in 5 steps. [UNRESOLVED-CLAIM: c_49ae6c56 — status=not_enough_info]
 - *Action*: For each threshold, re-run the model training (T031-T033) and compare accuracy against the null distribution (T034a).
 - *Output*: `data/results/sensitivity_analysis.csv`.
- [ ] T035 [US3] Implement Statistical Comparison in `code/04_modeling.py`:
 - *Depends on*: T034a.
 - *Logic*: Calculate p-value comparing Random Forest accuracy (from T033/T031/T032) against the null distribution generated in T034a.
 - *Action*: If p < 0.05, set `status='significant'`. Else, set `status='not_significant'`. Write status to `data/results/model_significance.json`.
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
- [ ] T040 [P] Additional unit tests for edge cases (zero variance, missing data)
- [ ] T041 Run quickstart.md validation
- [ ] T042 Implement runtime monitoring in code/utils.py to log total runtime to `data/results/resource_usage.json` and assert < 21600s (6h).
- [ ] T043 Implement memory monitoring in code/utils.py to log peak memory to `data/results/resource_usage.json` and assert < 7340 MB (7GB).

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
- **User Story 2 (P2)**: Depends on User Story 1 (requires `data/processed/filtered_data.csv`)
- **User Story 3 (P3)**: Depends on User Story 2 (requires `data/results/correlation_results.csv` for feature selection validation, though feature selection itself is local to the loop)
 - *Note*: While US3 depends on US2 results for feature selection validation, the *code* for US3 can be written in parallel, but execution must be sequential.
- **Sensitivity Analysis**: Integrated into T020-B (Phase 4) and T034b (Phase 5)

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
- **CRITICAL SEQUENTIAL DEPENDENCY**: Within Phase 5, Task T034a (Permutation Baseline) MUST complete before Task T034b (Threshold Sweep) and T035 (Statistical Comparison) can begin. T034b and T035 consume the output of T034a. These tasks are **NOT** parallel.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for data schema validation in code/tests/test_ingest.py (test_validate_schema_loads_yaml)"
Task: "Integration test for data filtering logic in code/tests/test_ingest.py (test_filter_excludes_null_titers)"

# Launch all models for User Story 1 together:
Task: "Implement Strategy A: Fetch NCBI SRA data in code/01_ingest.py"
Task: "Implement Strategy B: Download raw FASTQ in code/01_ingest.py"
Task: "Implement Strategy B: Run 16S pipeline in code/01_ingest.py"
```

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
- **Critical Constraint**: All tasks must run on CPU-only GitHub Actions free-tier runners (≤7GB RAM, ≤6h). [UNRESOLVED-CLAIM: c_e9492c88 — status=not_enough_info] No GPU, no 8-bit quantization.
- **Data Strategy**: T011a (Strategy A) is preferred; T011b-d (Strategy B) is conditional fallback if T011a fails.
- **Sequential Dependency**: T034a (Permutation) must finish before T034b (Threshold Sweep) and T035 (Comparison) starts.
- **Data Integrity**: Real data must be streamed or sampled honestly. Synthetic fallbacks are strictly forbidden.
- **Hard Stop**: T014a enforces N >= 50 before any sampling (T014b) occurs.
- **No False Halts**: T035 treats non-significant results as valid outcomes.