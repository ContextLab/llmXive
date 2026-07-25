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
 - *Note*: Paths are relative to the repository root.
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
- [X] T008b [P] Implement `.env` loading in `code/utils/config.py` using `python-dotenv`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Validation (Priority: P1) 🎯 MVP

**Goal**: Ingest pre-processed 16S rRNA OTU tables and serology metadata, filtering for complete records.

**Independent Test**: The system can be tested by running the ingestion script against a known valid subset and verifying the output CSV contains exactly N rows (N ≥ 50) with no nulls in required columns.

### Strategy A: Primary Data Fetch (NCBI SRA)

- [X] T011a [US1] Implement Strategy A: Fetch pre-processed OTU table and serology metadata for the SRP accession series.
 - *Method*: Fetch the specific URL for accession **SRP053178**. If the fetch fails (404 or timeout), raise `DataUnavailableError` and trigger Strategy B. Do NOT fall back to synthetic data.
 - *Constraint*: If the primary fetch fails, raise `DataUnavailableError` and trigger Strategy B. Do NOT fall back to synthetic data.
 - *Output*: `data/raw/otutable.csv`, `data/raw/serology.csv`.

### Strategy B: Fallback Raw FASTQ Processing (Conditional)

> **Conditional Execution Flow**: The tasks T011b-Setup, T011b, T011c, and T011d are ONLY executed if T011a raises `DataUnavailableError`. If T011a succeeds, skip this entire block.
> **MVP Scope Note**: The Spec assumes pre-processed data is available. Strategy B is a Fail-Stop path for the MVP. If pre-processed data is missing, the pipeline halts with a clear error indicating the data source is unavailable, rather than attempting raw FASTQ processing which is out of scope for the MVP.

- [X] T011b-Setup [US1] **Setup**: Install and configure `sra-tools` and R with DADA2 package.
 - *Trigger*: ONLY if T011a fails.
 - *Logic*: Run `conda install -c bioconda sra-tools -y` and `export NCBI_API_KEY=<env_var>` (if available). Install R packages via `Rscript -e "install.packages('BiocManager'); BiocManager::install('DADA2')"` (or equivalent).
 - *Output*: Environment ready for T011b.
- [X] T011b [US1] **Fail-Stop**: Implement Strategy B: Attempt to download raw FASTQ files from NCBI SRA for the designated study accession **SRP053178**.
 - *Trigger*: ONLY if T011a fails and T011b-Setup succeeds.
 - *Method*: Use `esearch` and `efetch` with the following command: `esearch -db sra -query "SRP053178" | efetch -format runinfo | cut -d, -f1`.
 - *Logic*: Iterate over ALL returned run IDs and download each associated FASTQ file using `prefetch` or `fasterq-dump`.
 - *File Naming*: Save as `data/raw/fastq_files/{SRR_ID}.fastq.gz`.
 - *Error Handling*: If `esearch` returns no run IDs, raise `DataUnavailableError`.
 - *Depends on*: T011a failure.
 - *Output*: `data/raw/fastq_files/` (list of downloaded.fastq.gz).
 - **MVP Constraint**: If T011a fails, this task MUST raise `DataUnavailableError` with a message stating "Pre-processed data unavailable and raw FASTQ processing is out of scope for MVP. Pipeline halted." This task does NOT proceed to T011c or T011d.
- [X] T011c [US1] **REMOVED**: Raw FASTQ processing (DADA2) is out of scope for MVP.
- [X] T011d [US1] **REMOVED**: Merging raw FASTQ output is out of scope for MVP.

### Sample Size Validation & Filtering

- [X] T014b [US1] **Dynamic Sampling**: Implement simple random sampling in `code/01_ingest.py` ONLY IF the dataset exceeds available RAM.
 - *Trigger*: Execute ONLY after T012 (Filtering).
 - *Logic*:
 1. Import `psutil`.
 2. Check `if psutil.virtual_memory().available < 6 * 1024 * 1024 * 1024:` (7GB limit - 1GB OS buffer).
 3. If True: Perform simple random sampling.
 4. Method: Use `pandas.DataFrame.sample` with `random_state=42` and `frac` adjusted to fit memory.
 5. **Constraint Check**: Calculate `max_rows` based on memory. If `max_rows < 50`, RAISE `InsufficientSampleSizeError` immediately with message "Insufficient memory to retain minimum sample size (N=50).".
 6. Fallback: If dynamic frac calculation fails or results in dataset > memory, use static `frac=0.5` (subject to the check above).
 7. Output: `data/processed/filtered_sampled.csv`.
 8. If False: Do not create a temp file. Output remains `data/processed/filtered.csv`.
 9. Log the final sample size retained and the fact that sampling was performed due to memory constraints.
 - *Output*: `data/processed/filtered_sampled.csv` (if sampled) or `data/processed/filtered.csv` (if not sampled).
- [X] T016 [US1] **Write Filtered Dataset**: Write the final filtered dataset to `data/processed/filtered_data.csv`.
 - *Input*: `data/processed/filtered.csv` (from T012) OR `data/processed/filtered_sampled.csv` (from T014b if it ran).
 - *Logic*: Check if `data/processed/filtered_sampled.csv` exists. If yes, use it. If no, use `data/processed/filtered.csv`. Write the selected file to `data/processed/filtered_data.csv`.
 - *Output*: `data/processed/filtered_data.csv`.
- [X] T015 [US1] **Sample Size Validation Gate**: Implement sample size validation in `code/01_ingest.py`.
 - *Input*: `data/processed/filtered_data.csv` (output of T016).
 - *Depends on*: T016.
 - *Logic*:
 1. Count subjects (N) in `filtered_data.csv`.
 2. Log N to `data/results/N_count.json`.
 3. If N < 50, raise `InsufficientSampleSizeError` with message including N.
 4. If N >= 50, proceed.
 - *Output*: `data/results/N_count.json` (if N >= 50) or error (if N < 50).
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
- [X] T020a [US2] Run CLR transformation with a default pseudocount in `code/02_preprocess.py`.
 - *Input*: `data/processed/filtered_normalized.csv`.
 - *Output*: `data/processed/cleared_default.csv`.
 - *Verification*: Verify file exists and contains N rows with CLR-transformed columns.
 - *Mandatory Logging (T050 Integrated)*: Log the exact pseudocount value used to `data/results/pseudocount_sensitivity.json` immediately after transformation. This log is a mandatory artifact for Constitution Principle I verification.
- [X] T020c [US2] Calculate Shannon diversity index in `code/02_preprocess.py` using `data/processed/cleared_default.csv`.
 - *Input*: `data/processed/cleared_default.csv` (CLR-transformed data).
 - *Output*: `data/processed/cleared_with_diversity.csv` (Append Shannon index column).
- [X] T021 [US2] **Log-Transform Titers**: Implement log-transformation of raw antibody titers in `code/02_preprocess.py`.
 - *Input*: `data/processed/filtered_data.csv` (or `cleared_with_diversity.csv` if titers are merged there).
 - *Logic*: Apply `np.log(titer_post + 1)` (or similar base) to `titer_post` column. Handle zeros/LOD as per spec (half LOD or exclude).
 - *Output*: Add `log_titer` column to the dataset. Save to `data/processed/cleared_with_diversity.csv` (merged with T020c output).
 - *Dependency*: Must run before T022.
- [X] T022 [US2] Implement Spearman rank correlation test in `code/03_correlation.py`.
 - *Input*: `data/processed/cleared_with_diversity.csv` (contains CLR taxa and `log_titer`).
 - *Logic*: Iterate over all taxon columns (CLR-transformed) and correlate with the single `log_titer` column using `scipy.stats.spearmanr`.
 - *Output*: DataFrame with columns `[taxon, coefficient, raw_pvalue]`.
- [X] T023 [US2] Implement Benjamini-Hochberg FDR correction in `code/03_correlation.py`.
 - *Input*: Output DataFrame from T022 (specifically `raw_pvalue` column).
 - *Logic*: Use `statsmodels.stats.multitest.multipletests` with method `fdr_bh`.
 - *Output*: DataFrame with added `adj_pvalue` column.
- [X] T024 [US2] Write correlation results (coeff, raw p, adj p) to `data/results/correlation_results.csv`.
 - *Schema*: Columns `[taxon, coefficient, raw_pvalue, adj_pvalue]`.
- [X] T020b [US2] Run CLR transformation with varying pseudocounts across multiple orders of magnitude and calculate Jaccard Index for pseudocount sensitivity analysis.
 - *Logic*: For each pseudocount in a range of small positive values:
 1. Re-load `filtered_normalized.csv`.
 2. Apply CLR with current pseudocount.
 3. **Re-apply T021 logic** (log-transform titers) to ensure titers are log-transformed for this run.
 4. Run correlation (T022 logic) and BH correction (T023 logic) internally.
 5. Identify the set of significant taxa (adj-p < 0.05).
 6. Calculate Jaccard Index (intersection over union) between the *sets of significant taxa* from different pseudocount runs.
 - *Output*: `data/results/pseudocount_sensitivity.json`.
- [X] T025 [US2] Count taxa with adj-p < 0.05 and compare against the expected range.
 - *Logic*:
 1. Count significant taxa.
 2. **Verify BH Method**: Check that adjusted p-values are monotonically increasing when sorted by raw p-value. If not, raise `StatisticalRigorError`.
 3. **Threshold Verification**: Verify that all reported significant taxa strictly meet `adj_pvalue < 0.05`. If any fail, raise `StatisticalRigorError`.
 4. Log the count and the *expected range description* from the spec ("low single-digit to high single-digit").
 5. If count < 1 or count > 20, set `within_expected_range` to `False (Wikidata Q105812849, https://www.wikidata.org/wiki/Q105812849)` in the output JSON and log a warning. Do NOT halt execution, but flag for review.
 - *Output*: `data/results/significant_taxa_count.json` with `count`, `expected_range_description`, `within_expected_range`, and `method_verified` (boolean).
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

- [X] T018 [P] [US2] Unit test for CLR transformation logic in `code/tests/test_correlation.py`: Add function `test_clr_transform_handles_zeros`.
- [X] T019 [P] [US2] Unit test for Benjamini-Hochberg correction in `code/tests/test_correlation.py`: Add function `test_bh_correction_adjusts_pvalues`.

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
 - *Constraint*: **DO NOT** use global correlation results from T022. Correlation must be recalculated from scratch on the training split data for each fold to prevent data leakage.
 - *Fail-safe*: If feature selection results in zero features for a fold, skip that fold or log a warning and proceed (do not crash).
 - *Mandatory Output (T051 Integrated)*: Log the list of selected features for *each* outer fold to `data/results/feature_selection_log.csv` with columns `[fold_id, selected_features]`. This artifact is required to verify FR-007 and is a mandatory output of this task, not optional.
- [X] T033 [US3] Implement Random Forest classifier training in `code/04_modeling.py` (CPU-only, default precision).
 - *Hyperparameters*: `n_estimators=100`, `max_depth=None`.
- [X] T034a-Null [US3] Implement permutation baseline testing: Generate null distribution of accuracy scores by permuting microbiome rows relative to serology labels with `random_seed=42`. Perform a sufficient number of permutations to ensure statistical robustness. Output `data/results/null_distribution.csv`.
 - *Blocking*: This task is a **BLOCKING** prerequisite for T035. If T034a-Null fails to generate the null distribution, the pipeline must halt with `Null Baseline Missing` error.
 - *Depends on*: T030d.
 - *Output*: `data/results/null_distribution.csv`.
- [X] T034a-Model [US3] Implement the main nested cross-validation run to generate observed accuracy.
 - *Logic*: Run the full nested CV (T031-T033) on the unpermuted data.
 - *Output*: `data/results/observed_metrics.json` containing the mean accuracy and standard deviation.
- [X] T034b [US3] Implement Threshold Sweep and Robustness Check.
 - *Depends on*: T030d (Responder Labels), T020c (Cleared Data).
 - *Logic*: Loop through responder thresholds across a representative range in regular steps. For EACH threshold:
 1. Define the range: from a value below the default to a value above the default, divided into equal steps.
 2. For EACH threshold:
 a. Generate a NEW null distribution by permuting microbiome rows (internal to this loop).
 b. **Re-run the entire nested 5-fold CV loop (T031-T033) including the inner feature selection step** on the permuted data for this specific threshold.
 c. Compare model accuracy against this specific null distribution.
 - *Output*: `data/results/sensitivity_analysis.csv` with threshold, accuracy, and p-value per step.
 - *Dependency*: Independent of T034a-Null. Generates its own nulls and re-runs the inner loop.
- [X] T036a [US3] Calculate and log confusion matrix, precision, recall, F1-score for high/low responders.
 - *Input*: Model predictions from T034a-Model.
 - *Output*: Metrics included in `data/results/model_metrics.json`.
- [X] T036b [US3] **Success Criterion Check**: Verify if the model's cross-validated accuracy meets the SC-003 target of >60%.
 - *Input*: Mean accuracy from T034a-Model (nested CV).
 - *Logic*: Compare mean accuracy against 0.60. Set `meets_accuracy_target` to `True` or `False` in the output JSON.
 - *Output*: Update `data/results/model_metrics.json` with `meets_accuracy_target`.
- [X] T035 [US3] Implement Statistical Comparison. Calculate p-value comparing Random Forest accuracy (from T034a-Model) against the null distribution (from T034a-Null).
 - *Dependency*: **Depends on T034a-Null and T034a-Model**. Requires `data/results/null_distribution.csv` and `data/results/observed_metrics.json`.
 - *Logic*:
 1. Extract the list of observed accuracies from `data/results/observed_metrics.json` (or the single mean if aggregated).
 2. Extract the list of null accuracies from `data/results/null_distribution.csv`.
 3. Perform a **one-tailed Wilcoxon rank-sum test** comparing the observed accuracy against the null distribution.
 4. If T034b results are available, use the more conservative null distribution for comparison.
 5. **Mandatory Verification (T052 Integrated)**: Verify that the null distribution was generated correctly (non-empty, variance > 0) and that the comparison logic was executed. If verification fails, raise `StatisticalRigorError`.
 - *Output*: `data/results/model_significance.json`.
- [X] T037 [US3] Write model metrics to `data/results/model_metrics.json`.
 - *Schema*: Includes accuracy, precision, recall, F1, `meets_accuracy_target`, and significance p-value.
- [X] T038 [US3] Validate output against `specs/001-investigating-the-correlation-between-gu/contracts/model_metrics.schema.yaml`.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [P] [US3] Unit test for nested CV structure in `code/tests/test_modeling.py`: Add function `test_nested_cv_feature_selection_is_isolated`.
- [X] T029 [P] [US3] Integration test for model performance metrics in `code/tests/test_modeling.py`: Add function `test_model_metrics_match_expected_format`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T039 Run ruff check and black format on all files in code/ and fix all reported issues
- [X] T040a [P] [US1] Unit test for zero-variance taxa exclusion in `code/tests/test_preprocess.py`: Add function `test_zero_variance_taxa_exclusion`.
- [X] T040b [P] [US1] Unit test for LOD handling in `code/tests/test_ingest.py`: Add function `test_lod_exclusion_logic`.
- [X] T040c [P] [US2] Unit test for CLR pseudocount edge cases in `code/tests/test_correlation.py`: Add function `test_clr_pseudocount_handles_extreme_zeros`.
- [X] T041 Run quickstart.md validation
- [X] T042 [P] Implement runtime monitoring in `code/main.py`.
 - *Logic*: Integrate into `code/main.py` orchestration script. Use `time` module to measure total runtime at the end of execution. Log to `data/results/resource_usage.json` with key `total_runtime_seconds`. Assert < 6h (21600s). If violated, raise `RuntimeError`.
 - *Depends on*: Completion of Phase 3, 4, 5.
- [X] T043 [P] Implement memory & runtime verification.
 - *Logic*: Integrate into `code/main.py` orchestration script. Use `psutil.Process().memory_info().rss` to measure peak memory at the end of execution. Log to `data/results/resource_usage.json` with key `peak_memory_mb`. Assert < 7GB (7340 MB). If violated, raise `RuntimeError`.
 - *Depends on*: Completion of Phase 3, 4, 5.
- [X] T045 [P] Generate Final Report.
 - *Input*: All result JSONs/CSVs from previous phases.
 - *Output*: `data/results/final_report.md` aggregating N count, correlation results, model metrics, and success criterion checks.
 - *Dependency*: T037, T035, T042, T043.

---