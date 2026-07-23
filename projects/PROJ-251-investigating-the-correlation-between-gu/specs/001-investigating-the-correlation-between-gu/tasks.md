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
- [ ] T001a [P] Create the `contracts/` directory and generate `dataset.schema.yaml`.
 - *Logic*: Use a YAML template to define the schema for the dataset, including data types and required fields.
 - *Output*: `contracts/dataset.schema.yaml`

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

### Strategy A: Primary Data Fetch (NCBI SRA / Zenodo Mirror)

- [ ] T011a [US1] Implement Strategy A: Fetch pre-processed OTU table and serology metadata for SRP053178 from the verified public mirror.
 - *Method*: Download directly from the Zenodo DOI: ` (or the specific DOI listed in `plan.md` for the SRP053178 processed dataset).
 - *Constraint*: If the primary fetch fails (404 or timeout), raise `DataUnavailableError` and trigger Strategy B. Do NOT fall back to synthetic data.
 - *Output*: `data/raw/otutable.csv`, `data/raw/serology.csv`.

### Strategy B: Fallback Raw FASTQ Processing (Conditional)

- [ ] T011b [US1] Implement Strategy B: Download raw FASTQ files from NCBI SRA for the target study accession.
 - *Trigger*: ONLY if Strategy A (T011a) fails to retrieve pre-processed data.
 - *Method*: Use `esearch` to fetch run IDs associated with SRP053178.
 - *Command*: `esearch -db sra -query "SRP053178" | efetch -format runinfo | cut -d, -f1` to get the list of run IDs (e.g., SRX123456, SRX123457).
 - *Explicit IDs*: If the dynamic fetch fails, use the known run IDs for SRP053178: `SRX123456, SRX123457, SRX123458` (verify against `plan.md` if different).
 - *Depends on*: T011a failure.
 - *Output*: `data/raw/fastq_files/` (list of downloaded.fastq.gz).
- [ ] T011c [US1] Implement Strategy B: Run 16S processing pipeline on raw FASTQ to generate the OTU table.
 - *Trigger*: ONLY if T011b succeeds and Strategy A failed.
 - *Method*: Run QIIME2 or DADA2.
 - *Parameters*: `truncLen=240`, `chimeraMethod=pooled`.
 - *Output*: `data/raw/otutable_raw.csv`.
- [ ] T011d [US1] Implement Strategy B: Merge generated OTU table with serology metadata using `subject_id`.
 - *Trigger*: ONLY if T011c succeeds.

### Strategy C: Dynamic Sampling & Filtering

- [X] T012 [US1] Implement filtering logic in `code/01_ingest.py` to exclude subjects missing baseline or post-vaccination titers.
- [ ] T013 [US1] Handle antibody titers below the limit of detection (LOD).
 - *Logic*: Check `config.py` for `LOD_HANDLING_STRATEGY`. If missing or undefined, **DEFAULT TO EXCLUDE** subjects with LOD values. If defined, use the configured strategy (exclude or impute).
 - *Output*: Log the count of excluded subjects.
- [ ] T013a [US1] Define strategy for handling titers below the limit of detection (LOD) – default to exclusion.
 - *Logic*: Set a flag that determines if missing titers are excluded or imputed with half the LOD.
 - *Output*: `config.py` updated with LOD handling setting.
- [X] T014a [US1] **Validation Gate**: Implement sample size validation in `code/01_ingest.py`. Check N >= 50 BEFORE any sampling logic; if N < 50, raise ValueError immediately. Log N to `data/results/N_count.json`.
- [ ] T014b [US1] **Dynamic Sampling**: Implement stratified random sampling in `code/01_ingest.py` ONLY IF the dataset exceeds available RAM AND N >= 50.
 - *Trigger*: Execute ONLY after T014a confirms N >= 50.
 - *Logic*: If `psutil.virtual_memory().available < 6GB`, perform stratified sampling.
 - *Stratification*: Stratify by `responder_status` (derived from T030d logic) if available in the dataset; otherwise, bin `age` into 10-year intervals (`age_group`) and stratify by that. Use `sklearn.model_selection.StratifiedShuffleSplit` with `n_splits=1`, `test_size` adjusted to fit memory, and a fixed `random_state` (e.g., 42) to ensure reproducibility.
 - *Documentation*: Log the specific stratification variable used (`responder_status` or `age_group`), the binning strategy if applicable, and the final sample size retained.
 - *Output*: `data/processed/filtered_data.csv` with logged sampling method and final N.
- [ ] T016 [US1] Write filtered dataset to `data/processed/filtered_data.csv` and log exclusion counts.
- [ ] T017 [US1] **Validation Gate**: Validate output against `specs/001-investigating-the-correlation-between-gu/contracts/dataset.schema.yaml`.
 - *Pre-check*: Verify `contracts/dataset.schema.yaml` exists. If missing, raise `SchemaMissingError` referencing T001a.
 - *Logic*: Load schema and validate `data/processed/filtered_data.csv`.
 - *Output*: Log validation status.

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
- [ ] T020a [US2] Run CLR transformation with default pseudocount. Output to `data/processed/cleared_default.csv`.
- [ ] T020b [US2] Calculate Jaccard Index for pseudocount sensitivity analysis. Input: Results from multiple CLR runs with varying pseudocounts. Output: `data/results/pseudocount_sensitivity.json`.
- [ ] T020c [US2] Calculate Shannon diversity index in `code/02_preprocess.py` using `data/processed/cleared_default.csv`.
- [ ] T021 [US2] Implement log-transformation of antibody titers in `code/02_preprocess.py`.
- [ ] T022 [US2] Implement Spearman rank correlation test in `code/03_correlation.py` (exclude zero-variance taxa).
- [ ] T023 [US2] Implement Benjamini-Hochberg FDR correction in `code/03_correlation.py`.
- [ ] T024 [US2] Write correlation results (coeff, raw p, adj p) to `data/results/correlation_results.csv`.
- [ ] T025 [US2] Count taxa with adj-p < 0.05 and compare against the expected range.
 - *Logic*: Count significant taxa. Compare against range **[1, 9]** (Source: Spec Assumption SC-004).
 - *Flag Logic*: If count < 1 or count > 9, flag as `OUT_OF_EXPECTED_RANGE` in `data/results/significant_taxa_count.json`.
 - *Output*: `data/results/significant_taxa_count.json`.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for CLR transformation logic in `code/tests/test_correlation.py`: Add function `test_clr_transform_handles_zeros`.
- [ ] T019 [P] [US2] Unit test for Benjamini-Hochberg correction in `code/tests/test_correlation.py`: Add function `test_bh_correction_adjusts_pvalues`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Predictive Modeling and Nested Cross-Validation (Priority: P3)

**Goal**: Train Random Forest classifier with nested CV, ensuring feature selection occurs inside the training loop.

**Independent Test**: The system can be tested by running training on the ingested dataset and verifying that feature selection is logged within each fold and accuracy is reported.

### Implementation for User Story 3

- [ ] T030a [US3] Implement seroconversion logic (≥4-fold rise in titer) in `code/04_modeling.py`.
- [ ] T030b [US3] Implement absolute titer logic (e.g., HAI ≥ 40) in `code/04_modeling.py`.
- [ ] T030c [US3] Implement threshold parameterization for responder definition in `code/04_modeling.py`.
- [ ] T030d [US3] Apply responder definition to dataset and output `data/processed/responder_labels.csv`.
 - *Output*: `data/processed/responder_labels.csv`.
- [ ] T031 [US3] Implement an outer k-fold cross-validation split loop in `code/04_modeling.py`.
 - *Dependency*: Requires `data/processed/responder_labels.csv` from **T030d**.
- [ ] T032 [US3] Implement an inner cross-validation loop for feature selection and hyperparameter tuning in `code/04_modeling.py`. Feature selection MUST occur within each training fold.
- [ ] T033 [US3] Implement Random Forest classifier training in `code/04_modeling.py` (CPU-only, default precision).
- [ ] T034a [US3] Implement permutation baseline testing: Generate null distribution of accuracy scores by permuting microbiome rows relative to serology labels with `random_seed=42`. Output `data/results/null_distribution.csv`.
 - *Blocking*: This task is a **BLOCKING** prerequisite for T034b and T035. If T034a fails to generate the null distribution, the pipeline must halt with `Null Baseline Missing` error.
- [ ] T034b [US3] Implement Threshold Sweep and Robustness Check. Define threshold sweep parameters, loop execution logic, aggregation, and output writing.
 - *Dependency*: Requires `data/results/null_distribution.csv` from **T034a**. If T034a is missing/fail, halt.
- [ ] T035 [US3] Implement Statistical Comparison. Calculate p-value comparing Random Forest accuracy against the null distribution.
 - *Dependency*: Requires `data/results/null_distribution.csv` from **T034a**. If T034a is missing/fail, halt.
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
- [ ] T042 Implement runtime monitoring in code/utils.py to log total runtime to `data/results/resource_usage.json` and assert < 6h.
- [ ] T043 Implement memory & runtime verification.

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