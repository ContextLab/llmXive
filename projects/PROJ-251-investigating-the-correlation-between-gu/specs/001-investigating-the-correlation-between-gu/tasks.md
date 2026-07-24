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

- [ ] T001 Create project directories explicitly: `code/`, `data/raw`, `data/processed`, `data/results`, `specs/001-investigating-the-correlation-between-gu/contracts/`.
 - *Verification*: Run `ls -R` and verify all directories exist.
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (pandas, numpy, scipy, scikit-learn, pyyaml, requests, biom-format, sra-tools, qiime2, dada2)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools
- [X] T001a [P] Create the `contracts/` directory and generate `dataset.schema.yaml`.
 - *Logic*: Write the following YAML content to `contracts/dataset.schema.yaml`:
 ```yaml
 type: object
 required:
 - subject_id
 - taxa_abundances
 - titer_baseline
 - titer_post
 properties:
 subject_id:
 type: string
 taxa_abundances:
 type: object
 additionalProperties:
 type: number
 titer_baseline:
 type: number
 titer_post:
 type: number
 ```
 - *Output*: `contracts/dataset.schema.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create configuration module `code/utils/config.py` with paths, seeds, and thresholds
- [X] T005 [P] Implement schema validators `code/utils/validators.py` for dataset, correlation, and model metrics
- [X] T006 [P] Setup logging infrastructure in `code/utils/logging_config.py` to capture exclusion counts and errors
- [X] T007 Create base data loading helpers in `code/utils/data_loader.py`
- [ ] T008a [P] Create `.env` template file with placeholders for `SRA_TOKEN` (if needed) and `DATA_SOURCE_URL`.
- [ ] T008b [P] Implement `.env` loading in `code/utils/config.py` using `python-dotenv`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Validation (Priority: P1) 🎯 MVP

**Goal**: Ingest pre-processed 16S rRNA OTU tables and serology metadata, filtering for complete records.

**Independent Test**: The system can be tested by running the ingestion script against a known valid subset and verifying the output CSV contains exactly N rows (N ≥ 50) with no nulls in required columns.

### Strategy A: Primary Data Fetch (NCBI SRA)

- [X] T011a [US1] Implement Strategy A: Fetch pre-processed OTU table and serology metadata for the SRP accession series.
 - *Method*: Fetch the specific URL from `research.md` under the key `data_url`. If `research.md` is missing or the key is absent, raise `DataUnavailableError`.
 - *Constraint*: If the primary fetch fails (404 or timeout), raise `DataUnavailableError` and trigger Strategy B. Do NOT fall back to synthetic data.
 - *Output*: `data/raw/otutable.csv`, `data/raw/serology.csv`.

### Strategy B: Fallback Raw FASTQ Processing (Conditional)

> **Conditional Execution Flow**: The tasks T011b-Setup, T011b, T011c, and T011d are ONLY executed if T011a raises `DataUnavailableError`. If T011a succeeds, skip this entire block.

- [X] T011b-Setup [US1] **Setup**: Install and configure `sra-tools` and R with DADA2 package.
 - *Trigger*: ONLY if T011a fails.
 - *Logic*: Run `conda install -c bioconda sra-tools -y` and `export NCBI_API_KEY=<env_var>` (if available). Install R packages via `Rscript -e "install.packages('BiocManager'); BiocManager::install('DADA2')"` (or equivalent).
 - *Output*: Environment ready for T011b.
- [X] T011b [US1] Implement Strategy B: Download raw FASTQ files from NCBI SRA for the designated study accession.
 - *Trigger*: ONLY if T011a fails and T011b-Setup succeeds.
 - *Method*: Use `esearch` and `efetch` with the following command: `esearch -db sra -query "SRP[ACCESSION]" | efetch -format runinfo | cut -d, -f1`.
 - *Logic*: Iterate over ALL returned run IDs and download each associated FASTQ file using `prefetch` or `fasterq-dump`.
 - *File Naming*: Save as `data/raw/fastq_files/{SRR_ID}.fastq.gz`.
 - *Error Handling*: If `esearch` returns no run IDs, raise `DataUnavailableError`.
 - *Depends on*: T011a failure.
 - *Output*: `data/raw/fastq_files/` (list of downloaded.fastq.gz).
- [X] T011c [US1] Implement Strategy B: Run 16S processing pipeline on raw FASTQ to generate the OTU table.
 - *Trigger*: ONLY if T011b succeeds.
 - *Method*: Run DADA2 via an R script.
 - *Parameters*: `truncLen=c([deferred])`, `chimeraMethod='pooled'`.
 - *Script*: Use the following R script snippet:
   ```R
   library(DADA2)
   # Load data from data/raw/fastq_files/*.fastq.gz
   # Filter, learn error rates, dereplicate, sample inference, merge, remove chimeras, assign taxonomy
   # Output OTU table to data/raw/otutable_raw.csv
   ```
 - *Output*: `data/raw/otutable_raw.csv`.
- [X] T011d [US1] Implement Strategy B: Merge generated OTU table with serology metadata using `subject_id`.
 - *Trigger*: ONLY if T011c succeeds.
 - *Logic*: Merge `data/raw/otutable_raw.csv` with `data/raw/serology.csv` on `subject_id`.
 - *Output*: `data/raw/otutable.csv` (overwriting Strategy A's output path for consistency).

### Sample Size Validation & Filtering

- [X] T012 [US1] Implement filtering logic in `code/01_ingest.py` to exclude subjects missing baseline or post-vaccination titers.
 - *Input*: `data/raw/otutable.csv`, `data/raw/serology.csv`.
 - *Output*: `data/processed/filtered.csv` (intermediate, before sampling).
 - *Logic*: Filter for subjects with both baseline microbiome and post-vaccination titer records. Log exclusion counts.
- [X] T015 [US1] **Sample Size Validation Gate**: Implement sample size validation in `code/01_ingest.py`.
 - *Input*: `data/processed/filtered.csv` (output of T012).
 - *Depends on*: T012.
 - *Logic*:
  1. Count subjects (N) in `filtered.csv`.
  2. Log N to `data/results/N_count.json`.
  3. If N < 50, raise `InsufficientSampleSizeError` with message including N.
  4. If N >= 50, proceed.
 - *Output*: `data/results/N_count.json` (if N >= 50) or error (if N < 50).
- [X] T014b [US1] **Dynamic Sampling**: Implement simple random sampling in `code/01_ingest.py` ONLY IF the dataset exceeds available RAM.
 - *Trigger*: Execute ONLY after T015 (if N >= 50).
 - *Logic*:
  1. Import `psutil`.
  2. Check `if psutil.virtual_memory().available < 6 * 1024 * 1024 * 1024:`.
  3. If True: Perform simple random sampling.
  4. Method: Use `pandas.DataFrame.sample` with `random_state=42` and `frac` adjusted to fit memory.
  5. Output: `data/processed/filtered_sampled.csv`.
  6. If False: Do not create a temp file.
  7. Log the final sample size retained and the fact that sampling was performed due to memory constraints.
 - *Output*: `data/processed/filtered_sampled.csv` (if sampled) or no file (if not sampled).
- [X] T016 [US1] **Write Filtered Dataset**: Write the final filtered dataset to `data/processed/filtered_data.csv`.
 - *Input*: `data/processed/filtered.csv` (from T012) OR `data/processed/filtered_sampled.csv` (from T014b if it ran).
 - *Logic*: Check if `data/processed/filtered_sampled.csv` exists. If yes, use it. If no, use `data/processed/filtered.csv`. Write the selected file to `data/processed/filtered_data.csv`.
 - *Output*: `data/processed/filtered_data.csv`.
- [X] T017 [US1] **Validation Gate**: Validate output against `specs/001-investigating-the-correlation-between-gu/contracts/dataset.schema.yaml`.
 - *Pre-check*: Verify `contracts/dataset.schema.yaml` exists.
 - *Logic*: Load schema and validate `data/processed/filtered_data.csv`.
 - *Output*: Log validation status.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T009 [P] [US1] Contract test for data schema validation in `code/tests/test_ingest.py`: Add function `test_validate_schema_loads_yaml`.
- [X] T010 [P] [US1] Integration test for data filtering logic in `code/tests/test_ingest.py`: Add function `test_filter_excludes_null_titers`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Correlation Analysis and Multiple Testing Correction (Priority: P2)

**Goal**: Calculate diversity metrics, apply CLR transformation, and perform Spearman correlation with BH correction.

**Independent Test**: The system can be tested by running analysis on a synthetic dataset with known correlations and verifying correct identification of significant taxa and adjusted p-values.

### Implementation for User Story 2

- [X] T019 [US2] Implement zero-variance taxa exclusion in `code/02_preprocess.py`: Filter out taxa with negligible variance across all subjects BEFORE transformation to avoid division-by-zero.
 - *Input*: `data/processed/filtered_data.csv`.
 - *Output*: `data/processed/filtered_no_zero_var.csv`.
- [X] T019a [US2] **Normalization**: Convert `filtered_no_zero_var.csv` to relative abundance.
 - *Input*: `data/processed/filtered_no_zero_var.csv`.
 - *Logic*: Sum abundances per subject and divide each taxon by the sum.
 - *Output*: `data/processed/filtered_normalized.csv`.
- [X] T020c [US2] Calculate Shannon diversity index in `code/02_preprocess.py` using `data/processed/filtered_normalized.csv`.
 - *Input*: `data/processed/filtered_normalized.csv` (Normalized relative abundance, BEFORE CLR).
 - *Output*: `data/processed/cleared_with_diversity.csv` (Append Shannon index column).
- [X] T020a [US2] Run CLR transformation with a default pseudocount in `code/02_preprocess.py`.
 - *Input*: `data/processed/filtered_normalized.csv`.
 - *Output*: `data/processed/cleared_default.csv`.
 - *Verification*: Verify file exists and contains N rows with CLR-transformed columns.
- [X] T022 [US2] Implement Spearman rank correlation test in `code/03_correlation.py`.
 - *Input*: `data/processed/cleared_with_diversity.csv`.
 - *Logic*: Iterate over all taxon columns (CLR-transformed) and correlate with the single `log_titer` column using `scipy.stats.spearmanr`.
 - *Output*: DataFrame with columns `[taxon, coefficient, raw_pvalue]`.
- [X] T023 [US2] Implement Benjamini-Hochberg FDR correction in `code/03_correlation.py`.
 - *Input*: Output DataFrame from T022 (specifically `raw_pvalue` column).
 - *Logic*: Use `statsmodels.stats.multitest.multipletests` with method `fdr_bh`.
 - *Output*: DataFrame with added `adj_pvalue` column.
- [X] T024 [US2] Write correlation results (coeff, raw p, adj p) to `data/results/correlation_results.csv`.
 - *Schema*: Columns `[taxon, coefficient, raw_pvalue, adj_pvalue]`.
- [X] T020b [US2] Run CLR transformation with varying pseudocounts across multiple orders of magnitude and calculate Jaccard Index for pseudocount sensitivity analysis.
 - *Logic*: For each pseudocount in `[1e-6, 1e-4, 1e-2, 1e-1]`, run correlation (T022-T024). Identify the set of significant taxa (adj-p < 0.05). Calculate Jaccard Index (intersection over union) between the *sets of significant taxa* from different pseudocount runs.
 - *Output*: `data/results/pseudocount_sensitivity.json`.
- [X] T025 [US2] Count taxa with adj-p < 0.05 and compare against the expected range.
 - *Logic*: Count significant taxa. Log the count and the *expected range description* from the spec ("low single-digit to high single-digit"). Do NOT enforce a pass/fail threshold in code.
 - *Output*: `data/results/significant_taxa_count.json` with `count` and `expected_range_description`.
- [X] T013b [US2] Implement LOD Handling Sensitivity Analysis.
 - *Depends on*: T012 (Filtering).
 - *Logic*: Run the full correlation analysis pipeline (T022-T024) twice:
 1. **Branch A (Exclude)**: Drop subjects with titers < LOD.
 2. **Branch B (Impute)**: Impute titers < LOD as half the limit of detection.
 - *Output*: Generate a comparison report `data/results/lod_sensitivity.json` containing:
 - The count of subjects in each branch.
 - The Jaccard Index of the *sets of significant taxa* (adj-p < 0.05) between Branch A and Branch B.
 - A boolean flag `robust` if Jaccard > 0.5.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for CLR transformation logic in `code/tests/test_correlation.py`: Add function `test_clr_transform_handles_zeros`.
- [ ] T019 [P] [US2] Unit test for Benjamini-Hochberg correction in `code/tests/test_correlation.py`: Add function `test_bh_correction_adjusts_pvalues`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Predictive Modeling and Nested Cross-Validation (Priority: P3)

**Goal**: Train Random Forest classifier with nested CV, ensuring feature selection occurs inside the training loop.

**Independent Test**: The system can be tested by running training on the ingested dataset and verifying that feature selection is logged within each fold and accuracy is reported.

### Implementation for User Story 3

- [X] T030a [US3] Implement seroconversion logic (≥4-fold rise in titer) in `code/04_modeling.py`.
 - *Formula*: `post_titer >= 4 * baseline_titer`.
- [X] T030b [US3] Implement absolute titer logic (e.g., HAI ≥ 40) in `code/04_modeling.py`.
 - *Formula*: `post_titer >= 40`.
- [X] T030c [US3] Implement threshold parameterization for responder definition in `code/04_modeling.py`.
- [X] T030d [US3] Apply responder definition to dataset and output `data/processed/responder_labels.csv`.
 - *Output*: `data/processed/responder_labels.csv` with columns `[subject_id, responder_status]`.
 - *Logic*: Use seroconversion if pre-vaccination titers exist; else use absolute titer. Log mode used.
- [X] T031 [US3] Implement an outer k-fold cross-validation split loop in `code/04_modeling.py`.
 - *Dependency*: Requires `data/processed/responder_labels.csv` from **T030d**.
 - *Depends on*: T030d.
- [X] T032 [US3] Implement an inner cross-validation loop for feature selection and hyperparameter tuning in `code/04_modeling.py`.
 - *Logic*: Feature selection MUST occur within each training fold.
 - *Method*: On the **training split only**, calculate Spearman correlation between taxa and labels. Select a subset of taxa by correlation coefficient.
 - *Constraint*: Do NOT use global correlation (T022) to prevent data leakage.
- [X] T033 [US3] Implement Random Forest classifier training in `code/04_modeling.py` (CPU-only, default precision).
 - *Hyperparameters*: `n_estimators=100`, `max_depth=None`.
- [X] T034a [US3] Implement permutation baseline testing: Generate null distribution of accuracy scores by permuting microbiome rows relative to serology labels with `random_seed=42`. Output `data/results/null_distribution.csv`.
 - *Blocking*: This task is a **BLOCKING** prerequisite for T035. If T034a fails to generate the null distribution, the pipeline must halt with `Null Baseline Missing` error.
 - *Depends on*: T030d.
- [X] T034b [US3] Implement Threshold Sweep and Robustness Check.
 - *Depends on*: T030d (Responder Labels), T020c (Cleared Data).
 - *Logic*: Loop through responder thresholds across a representative range in regular steps. For EACH threshold:
 1. Generate a NEW null distribution by permuting microbiome rows (internal to this loop).
 2. Train RF model on permuted data.
 3. Compare model accuracy against this specific null distribution.
 - *Output*: `data/results/sensitivity_analysis.csv` with threshold, accuracy, and p-value per step.
 - *Dependency*: Independent of T034a. Generates its own nulls.
- [X] T035 [US3] Implement Statistical Comparison. Calculate p-value comparing Random Forest accuracy (from T034a main run) against the null distribution (from T034a).
 - *Dependency*: **Depends on T034a**. Requires `data/results/null_distribution.csv`. If T034a is missing/fail, halt.
 - *Logic*: Calculate p-value comparing observed accuracy against null distribution.
- [X] T036 [US3] Calculate and log confusion matrix, precision, recall, F1-score for high/low responders.
- [X] T037 [US3] Write model metrics to `data/results/model_metrics.json`.
- [X] T038 [US3] Validate output against `specs/001-investigating-the-correlation-between-gu/contracts/model_metrics.schema.yaml`.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Unit test for nested CV structure in `code/tests/test_modeling.py`: Add function `test_nested_cv_feature_selection_is_isolated`.
- [ ] T029 [P] [US3] Integration test for model performance metrics in `code/tests/test_modeling.py`: Add function `test_model_metrics_match_expected_format`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T039 Run ruff check and black format on all files in code/ and fix all reported issues
- [X] T040a [P] [US1] Unit test for zero-variance taxa exclusion in `code/tests/test_preprocess.py`: Add function `test_zero_variance_taxa_exclusion`.
- [X] T040b [P] [US1] Unit test for LOD handling in `code/tests/test_ingest.py`: Add function `test_lod_exclusion_logic`.
- [X] T040c [P] [US2] Unit test for CLR pseudocount edge cases in `code/tests/test_correlation.py`: Add function `test_clr_pseudocount_handles_extreme_zeros`.
- [X] T041 Run quickstart.md validation
- [X] T042 [P] Implement runtime monitoring in `code/utils.py`.
 - *Logic*: Use `time` module to measure total runtime at the end of `main.py`. Log to `data/results/resource_usage.json` with key `total_runtime_seconds`. Assert < 6h (21600s). If violated, raise `RuntimeError`.
 - *Depends on*: Completion of Phase 3, 4, 5.
- [X] T043 [P] Implement memory & runtime verification.
 - *Logic*: Use `psutil.Process().memory_info().rss` to measure peak memory at the end of `main.py`. Log to `data/results/resource_usage.json` with key `peak_memory_mb`. Assert < 7GB (7340 MB). If violated, raise `RuntimeError`.
 - *Depends on*: Completion of Phase 3, 4, 5.

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

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services (N/A for data pipeline)
- Core implementation before integration
- Story complete before moving to next priority