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

- [ ] T039 [P] Run ruff check and black format on all files in code/ and fix all reported issues.
 - *Logic*: Run `ruff check code/` and `black code/`.
 - *Verification*: Generate `data/results/lint_report.txt` containing the exit code (0) and a summary of files fixed. If exit code != 0, the task fails.
 - *Output*: `data/results/lint_report.txt`.

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

- [X] T004 Create configuration module `code/utils/config.py` with paths, seeds, and thresholds. **Include `SRA_ACCESSION` variable** to be populated during research phase.
- [X] T005 [P] Implement schema validators `code/utils/validators.py` for dataset, correlation, and model metrics
- [X] T006 [P] Setup logging infrastructure in `code/utils/logging_config.py` to capture exclusion counts and errors
- [X] T007 Create base data loading helpers in `code/utils/data_loader.py`
- [X] T008a [P] Create `.env` template file with placeholders for `SRA_TOKEN` (if needed) and `DATA_SOURCE_URL`.
 - *Logic*: Write a file `.env` with content: `SRA_TOKEN=YOUR_TOKEN_HERE\nDATA_SOURCE_URL=https://example.com`.
 - *Verification*: Run `grep -q SRA_TOKEN.env` to confirm file exists and contains placeholder.
 - *Output*: `.env`
- [ ] T008b Implement `.env` loading in `code/utils/config.py` using `python-dotenv`.
 - *Dependency*: T008a must complete first (sequential execution).
 - *Logic*: Import `load_dotenv()` and ensure `os.getenv` retrieves values.
 - *Output*: Updated `code/utils/config.py`.
- [ ] T008c [P] Install QIIME2/DADA2 environment for Strategy B fallback.
 - *Logic*: Create a `conda` environment or `docker` container setup script (`scripts/setup_qiime2.sh`) that installs QIIME2 (or DADA2) dependencies.
 - *Verification*: Run `scripts/setup_qiime2.sh --dry-run` or check if `qiime --version` is available in the environment.
 - *Output*: `scripts/setup_qiime2.sh` or `Dockerfile.qiime2`.
 - *Note*: This task ensures Strategy B (T011b) is executable.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Validation (Priority: P1) 🎯 MVP

**Goal**: Ingest pre-processed 16S rRNA OTU tables and serology metadata, filtering for complete records.

**Independent Test**: The system can be tested by running the ingestion script against a known valid subset and verifying the output CSV contains exactly N rows (N ≥ 50) with no nulls in required columns.

### Strategy A: Primary Data Fetch (NCBI SRA)

- [X] T011a [US1] Implement Strategy A: Fetch pre-processed OTU table and serology metadata for the SRP accession series.
 - *Method*: Use `config.SRA_ACCESSION` to determine the specific accession. If the fetch fails (404 or timeout), raise `DataUnavailableError`.
 - *Control Flow*: In `code/main.py`, wrap T011a in a try-except block: `try: strategy_a() except DataUnavailableError: strategy_b()`.
 - *Output*: `data/raw/otutable.csv`, `data/raw/serology.csv`.

### Strategy B: Fallback Raw FASTQ Processing (Conditional)

> **Conditional Execution Flow**: The tasks T011b, T011c, T011d are ONLY executed if T011a raises `DataUnavailableError`. If T011a succeeds, skip this entire block.

- [X] T011b [US1] **Execute Strategy B - Download**: Download raw FASTQ files from NCBI SRA for the accession defined in `config.SRA_ACCESSION`.
 - *Trigger*: ONLY if T011a fails.
 - *Method*:
 1. Iterate over ALL returned run IDs and download each associated FASTQ file using `prefetch` or `fasterq-dump`.
 2. Save as `data/raw/fastq_files/{SRR_ID}.fastq.gz`.
 3. If `esearch` returns no run IDs, raise `DataUnavailableError`.
 - *Output*: `data/raw/fastq_files/`.
 - *Dependency*: T011a failure.

- [ ] T011c [US1] **Execute Strategy B - Process**: Run a lightweight 16S processing pipeline (QIIME2 or DADA2) on the downloaded FASTQ files.
 - *Trigger*: After T011b completes.
 - *Method*:
 1. Run QIIME2/DADA2 pipeline on `data/raw/fastq_files/` using the environment setup in T008c.
 2. Generate OTU table and taxonomy.
 - *Output*: `data/raw/otutable_raw.tsv`, `data/raw/taxonomy.tsv`.
 - *Dependency*: T011b.

- [ ] T011d [US1] **Execute Strategy B - Merge**: Merge the OTU table and serology metadata.
 - *Trigger*: After T011c completes.
 - *Method*:
 1. Merge `otutable_raw.tsv` and `taxonomy.tsv` into `data/raw/otutable.csv`.
 2. Merge with serology metadata into `data/raw/serology.csv`.
 - *Output*: `data/raw/otutable.csv`, `data/raw/serology.csv`.
 - *Dependency*: T011c.

### Filtering & Validation

- [ ] T012 [US1] **Filter for Complete Records & Memory Check**: Implement data filtering logic in `code/01_ingest.py`.
 - *Input*: `data/raw/otutable.csv`, `data/raw/serology.csv` OR `data/processed/filtered_sampled.csv` (from T014a if it ran).
 - *Logic*:
 1. **Memory Check**: Import `psutil` and `pandas`. Estimate the memory footprint of the raw data (or a small sample thereof).
 2. **Step 1: Check Memory**: If `psutil.virtual_memory().available` < 6GB:
 a. Estimate the maximum number of rows (`max_rows`) that can be safely loaded while leaving a sufficient memory headroom using the formula: `max_rows = floor(available_memory_gb * 1e9 / estimated_row_size_bytes)`.
 b. **CRITICAL**: If `max_rows < 50`, raise `InsufficientSampleSizeError` immediately with message "Memory constraints force sample size < 50. Pipeline cannot proceed." and halt execution.
 c. If `max_rows >= 50`, perform simple random sampling using `pandas.DataFrame.sample` with `random_state=42` and `n=max_rows`.
 d. Log the final sample size retained.
 e. Output: `data/processed/filtered_sampled.csv` (if sampled) or proceed to filtering (if not sampled).
 3. If memory is sufficient (N >= 50 and available RAM > 6GB), proceed to filtering without sampling.
 4. Merge datasets on `subject_id`.
 5. Filter out subjects where `titer_baseline` OR `titer_post` is null/missing.
 6. Log the count of excluded subjects.
 - *Output*: `data/processed/filtered.csv` (or `data/processed/filtered_sampled.csv` if sampled).
 - *Dependency*: T011a (success) OR T011d (if fallback).

- [X] T013-EXPLICIT [US1] **Mandatory Merge of OTU and Serology**: Unconditionally merge the filtered OTU table and serology metadata into a single unified dataset.
 - *Input*: `data/raw/otutable.csv`, `data/raw/serology.csv` (or `data/processed/filtered.csv` if T012 already merged them, otherwise merge raw files).
 - *Logic*:
 1. Ensure both `data/raw/otutable.csv` and `data/raw/serology.csv` exist.
 2. Perform an inner join on `subject_id` to create a single DataFrame containing all taxa columns and all serology columns.
 3. Write the result to `data/processed/merged_complete.csv`.
 4. **Verification**: Assert that `merged_complete.csv` contains at least one column from the OTU table and at least one column from the serology table.
 - *Output*: `data/processed/merged_complete.csv`.
 - *Dependency*: T012 (Filtering) must complete first to ensure data quality.

- [X] T015 [US1] **Sample Size Validation Gate (Full Dataset)**: Implement sample size validation in `code/01_ingest.py`.
 - *Input*: `data/processed/merged_complete.csv` (output of T013-EXPLICIT).
 - *Logic*:
 1. Count subjects (N) in the input file.
 2. Log N to `data/results/N_count.json`.
 3. **CRITICAL**: If N < 50, raise `InsufficientSampleSizeError` immediately with message "Insufficient sample size (N < 50) in final dataset." and halt execution.
 4. If N >= 50, proceed to T014b.
 - *Output*: `data/results/N_count.json` (if N >= 50) or error (if N < 50).

- [ ] T014b [US1] **Dynamic Sampling (Memory Optimization)**: Implement memory-aware sampling in `code/01_ingest.py` ONLY IF the dataset exceeds available RAM.
 - *Trigger*: Execute AFTER T015 (only if N >= 50).
 - *Logic*:
 1. Import `psutil`.
 2. Check file size of `data/processed/merged_complete.csv`.
 3. **Step 1: Check Memory**: If `psutil.virtual_memory().available` < 6GB:
 a. **First, attempt streaming** (see T054 logic) to process the full dataset without loading it all into memory. Streaming feasibility is defined as: `pandas.read_csv` supports `chunksize` and file size > 5GB.
 b. If streaming is not feasible (e.g., `chunksize` not supported or file size < 5GB but memory is critically low), calculate `max_rows` using the formula: `max_rows = floor(5.5GB / 50KB)` (where 50KB is the estimated bytes per row).
 c. If `max_rows < 50`, raise `InsufficientSampleSizeError` with message "Memory constraints force sample size < 50." and halt immediately.
 d. Perform simple random sampling using `pandas.DataFrame.sample` with `random_state=42` and `frac` adjusted to fit memory.
 e. Log the final sample size retained.
 f. Output: `data/processed/filtered_sampled.csv`.
 4. If N >= 50 and memory is sufficient: Output remains `data/processed/merged_complete.csv`.
 - *Output*: `data/processed/filtered_sampled.csv` (if sampled) or `data/processed/merged_complete.csv` (if not sampled).
 - *Note*: This task ensures we do not violate the N >= 50 constraint by sampling too aggressively, and prioritizes streaming over sampling.

- [X] T016 [US1] **Write Filtered Dataset**: Write the final filtered dataset to `data/processed/filtered_data.csv`.
 - *Input*: `data/processed/merged_complete.csv` (from T013-EXPLICIT) OR `data/processed/filtered_sampled.csv` (from T014b if it ran).
 - *Logic*: Check if `data/processed/filtered_sampled.csv` exists. If yes, use it. If no, use `data/processed/merged_complete.csv`. Write the selected file to `data/processed/filtered_data.csv`.
 - *Output*: `data/processed/filtered_data.csv`.

- [ ] T017 [US1] **Validation Gate**: Validate output against `specs/001-investigating-the-correlation-between-gu/contracts/dataset.schema.yaml`.
 - *Pre-check*: Verify `contracts/dataset.schema.yaml` exists.
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
 - *Input*: `data/processed/filtered_data.csv`.
 - *Output*: `data/processed/filtered_no_zero_var.csv`.

- [ ] T019a [US2] **Normalization**: Convert `filtered_no_zero_var.csv` to relative abundance.
 - *Input*: `data/processed/filtered_no_zero_var.csv`.
 - *Logic*: Sum abundances per subject and divide each taxon by the sum.
 - *Output*: `data/processed/filtered_normalized.csv`.

- [ ] T020a [US2] Run CLR transformation with a default pseudocount in `code/02_preprocess.py`.
 - *Input*: `data/processed/filtered_normalized.csv`.
 - *Output*: `data/processed/cleared_default.csv`.
 - *Verification*: Verify file exists and contains N rows with CLR-transformed columns.
 - *Mandatory Logging (T050 Integrated)*: Log the exact pseudocount value used to `data/results/pseudocount_sensitivity.json` immediately after transformation. This log is a mandatory artifact for Constitution Principle I verification.

- [X] T021 [US2] **Log-Transform Titers & LOD Handling**: Implement log-transformation of raw antibody titers in `code/02_preprocess.py`.
 - *Input*: `data/processed/merged_complete.csv` (from T013-EXPLICIT).
 - *Logic*:
 1. **LOD Handling**: For any titer value < Limit of Detection (LOD), impute as `0.5 * LOD`. Log the count of imputed values and the strategy used.
 2. Apply `np.log(titer_post + 1)` (or similar base) to `titer_post` column.
 3. Add `log_titer` column to the dataset.
 4. Merge with CLR-transformed data if necessary.
 - *Output*: Save to `data/processed/cleared_with_diversity.csv` (merged with T020c output).
 - *Dependency*: Must run after T013-EXPLICIT (Merge) and before T020c.

- [X] T020c [US2] Calculate Shannon diversity index in `code/02_preprocess.py` using `data/processed/cleared_default.csv`.
 - *Input*: `data/processed/cleared_default.csv` (CLR-transformed data) and `data/processed/merged_complete.csv` (for titers if not merged).
 - *Logic*: Calculate Shannon index for each subject. Merge with `log_titer` if not already present.
 - *Output*: `data/processed/cleared_with_diversity.csv` (Append Shannon index column and `log_titer`).
 - *Dependency*: T020a, T021.

- [ ] T022 [US2] Implement Spearman rank correlation test in `code/03_correlation.py`.
 - *Input*: `data/processed/cleared_with_diversity.csv` (contains CLR taxa and `log_titer`).
 - *Logic*: Iterate over all taxon columns (CLR-transformed) and correlate with the single `log_titer` column using `scipy.stats.spearmanr`.
 - *Output*: DataFrame with columns `[taxon, coefficient, raw_pvalue]`.

- [ ] T023 [US2] Implement Benjamini-Hochberg FDR correction in `code/03_correlation.py`.
 - *Input*: Output DataFrame from T022 (specifically `raw_pvalue` column).
 - *Logic*: Use `statsmodels.stats.multitest.multipletests` with method `fdr_bh`.
 - *Output*: DataFrame with added `adj_pvalue` column.

- [ ] T024 [US2] Write correlation results (coeff, raw p, adj p) to `data/results/correlation_results.csv`.
 - *Schema*: Columns `[taxon, coefficient, raw_pvalue, adj_pvalue]`.

- [ ] T020b [US2] Run CLR transformation with varying pseudocounts and calculate Jaccard Index for pseudocount sensitivity analysis.
 - *Trigger*: Execute AFTER T022-T024.
 - *Depends on*: T021 (Log-Transform Titers) and T019a (Normalized) and T013-EXPLICIT (Merge).
 - *Logic*: For each pseudocount in a range of **1e-4 to 1e-1 in 5 log-spaced steps**:
 1. Re-load `filtered_normalized.csv`.
 2. Apply CLR with current pseudocount.
 3. **Re-apply T021 logic** (log-transform titers) to ensure titers are log-transformed for this run. **Note**: Load raw titers from `data/raw/serology.csv` and re-apply LOD handling to ensure independence from T021's output.
 4. Run correlation (T022 logic) and BH correction (T023 logic) internally.
 5. **Write intermediate correlation results** to `data/processed/corr_pseudocount_X.csv` (where X is the pseudocount value) to ensure reproducibility.
 6. Identify the set of significant taxa (adj-p < 0.05).
 7. Calculate Jaccard Index (intersection over union) between the *sets of significant taxa* from different pseudocount runs.
 8. **Runtime Check**: Perform a pilot run of the *first* pseudocount step. Measure its wall-clock time. Calculate `estimated_total_time = time_pilot * 5`. If `estimated_total_time > 5.5 hours`, skip remaining runs and log a warning.
 - *Output*: `data/results/pseudocount_sensitivity.json`.

- [ ] T025 [US2] Count taxa with adj-p < 0.05 and compare against the expected range.
 - *Logic*:
 1. Count significant taxa.
 2. **Verify BH Method**: Check that adjusted p-values are monotonically increasing when sorted by raw p-value. **AND** Verify the calculation matches the BH formula by comparing the output of `statsmodels.stats.multitest.multipletests` against a known reference or by checking the specific rank-based formula implementation. If not, raise `StatisticalRigorError`.
 3. **Threshold Verification**: Verify that all reported significant taxa strictly meet `adj_pvalue < 0.05`. If any fail, raise `StatisticalRigorError`.
 4. Log the count and the *expected range description* from the spec ("low single-digit to high single-digit").
 5. If count < 1 or count > 20, **raise `HypothesisFailureError`** with message "Significant taxa count (N) is outside expected range (1-20). Hypothesis or data quality may be invalid." and flag for immediate review. **HALT EXECUTION**.
 - *Output*: `data/results/significant_taxa_count.json` with `count`, `expected_range_description`, `within_expected_range`, and `method_verified` (boolean).

- [ ] T013b [US2] Implement LOD Handling Sensitivity Analysis.
 - *Trigger*: Execute AFTER T022-T024.
 - *Depends on*: T012 (Filtering).
 - *Logic*: Run the full correlation analysis pipeline (T022-T024) twice:
 1. **Branch A (Exclude)**: Drop subjects with titers < LOD.
 2. **Branch B (Impute)**: Impute titers < LOD as half the limit of detection.
 3. **Runtime Check**: If estimated cumulative time > 5.5 hours, skip and log a warning.
 - *Output*: Generate a comparison report `data/results/lod_sensitivity.json` containing:
 - The count of subjects in each branch.
 - The Jaccard Index of the *sets of significant taxa* (adj-p < 0.05) between Branch A and Branch B.
 - A boolean flag `robust` if Jaccard > 0.5.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for CLR transformation logic in `code/tests/test_correlation.py`: Add function `test_clr_transform_handles_zeros`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Predictive Modeling and Nested Cross-Validation (Priority: P3)

**Goal**: Train Random Forest classifier with nested CV, ensuring feature selection occurs inside the training loop.

**Independent Test**: The system can be tested by running training on the ingested dataset and verifying that feature selection is logged within each fold and accuracy is reported.

### Implementation for User Story 3

- [ ] T030a [US3] Implement seroconversion logic (≥4-fold rise in titer) in `code/04_modeling.py`.
 - *Formula*: `post_titer >= 4 * baseline_titer`.

- [ ] T030b [US3] Implement absolute titer logic (e.g., HAI ≥ 40) in `code/04_modeling.py`.
 - *Formula*: `post_titer >= 40`.

- [ ] T030c [US3] Implement threshold parameterization for responder definition in `code/04_modeling.py`.

- [ ] T030d [US3] Apply responder definition to dataset and output `data/processed/responder_labels.csv`.
 - *Output*: `data/processed/responder_labels.csv` with columns `[subject_id, responder_status]`.
 - *Logic*: Use seroconversion if pre-vaccination titers exist; else use absolute titer. Log mode used.

- [ ] T031 [US3] Implement an outer k-fold cross-validation split loop in `code/04_modeling.py`.
 - *Dependency*: Requires `data/processed/responder_labels.csv` from **T030d**.
 - *Depends on*: T030d.

- [ ] T032 [US3] Implement an inner cross-validation loop for feature selection and hyperparameter tuning in `code/04_modeling.py`.
 - *Logic*: Feature selection MUST occur within each training fold.
 - *Method*: On the **training split only**:
 1. Calculate Spearman correlation between taxa and labels using the reusable function from `code/03_correlation.py`.
 2. **Apply Benjamini-Hochberg correction to the correlation p-values** for the training split.
 3. **Select the top 10 taxa** based on a combination of absolute Spearman coefficient and adjusted p-value (e.g., sort by coefficient, then filter by adj-p < 0.2, or select top 10 by coefficient if fewer than 10 pass). **Justification**: If raw coefficients are used without BH, document this as a trade-off for power in small N, but prefer BH.
 4. **Constraint**: **DO NOT** use global correlation results from T022. Correlation must be recalculated from scratch on the training split data for each fold to prevent data leakage.
 - *Mandatory Output (T051 Integrated)*: Log the list of selected features for *each* outer fold to `data/results/feature_selection_log.csv` with columns `[fold_id, selected_features]`. This artifact is required to verify FR-007 and is a mandatory output of this task, not optional.
 - *Fail-safe*: If feature selection results in zero features for a fold, skip that fold or log a warning and proceed (do not crash).

- [ ] T033 [US3] Implement Random Forest classifier training in `code/04_modeling.py` (CPU-only, default precision).
 - *Hyperparameters*: `n_estimators=100`, `max_depth=None`.

- [X] T034b [US3] Implement permutation baseline testing: Generate null distribution of accuracy scores by permuting microbiome rows relative to serology labels with `random_seed=42`. Perform **dynamic number of permutations** (min(upper_bound, floor(time_budget / estimated_time_per_perm))).
 - *Trigger*: Parallel with T034a.
 - *Logic*:
 1. Permute microbiome rows relative to serology labels.
 2. Train RF on permuted data.
 3. Repeat until `num_permutations` is reached or time budget exhausted (must be at least 100).
 4. **Verification**: Check that `null_distribution.csv` has at least 100 rows. If not, raise `StatisticalRigorError`.
 - *Output*: `data/results/null_distribution.csv`.
 - *Dependency*: T030d.

- [ ] T034a [US3] Implement the main nested cross-validation run to generate observed accuracy.
 - *Logic*: Run the full nested CV (T031-T033) on the unpermuted data.
 - *Output*: `data/results/observed_metrics.json` containing the mean accuracy and standard deviation.

- [X] T034d [US3] Implement Threshold Sweep and Robustness Check.
 - *Depends on*: T030d (Responder Labels), T020c (Cleared Data).
 - *Logic*: Loop through responder thresholds across a **representative range (slightly below to slightly above the default threshold in 5 equal steps)**. The 'default threshold' is defined by `config.SEROCONVERSION_THRESHOLD` (default 4.0) if the active mode is seroconversion, or `config.HAI_THRESHOLD` (default 40) if the active mode is absolute titer. For EACH threshold:
 1. Define the range: from 0.9x to 1.1x of the **active** default threshold, divided into equal steps.
 2. For EACH threshold:
 a. Generate a NEW set of responder labels based on the current threshold.
 b. **Re-run the outer fold splits (T031 logic)** to ensure independence from the original splits.
 c. **Re-run the inner CV loop (T032 logic)** to perform feature selection and hyperparameter tuning on the new labels. **Crucial**: This MUST re-execute the full nested loop (outer split -> inner feature selection -> train) for the new labels.
 d. Train the Random Forest classifier using the features selected in step (c).
 e. **Re-generate the null distribution (T034b logic)** for the current threshold to ensure a valid baseline.
 f. Evaluate the model on the held-out test sets (from the new outer CV splits) to get a new accuracy metric.
 g. Compare this new accuracy against the new null distribution.
 - *Output*: `data/results/sensitivity_analysis.csv` with threshold, accuracy, and p-value per step.
 - *Dependency*: Independent of T034b (re-runs it per threshold). **Re-runs T031, T032, and T034b logic** per threshold.

- [ ] T036a [US3] Calculate and log confusion matrix, precision, recall, F1-score for high/low responders.
 - *Input*: Model predictions from T034a.
 - *Output*: Metrics included in `data/results/model_metrics.json`.

- [ ] T036b [US3] **Success Criterion Check**: Verify if the model's cross-validated accuracy meets the SC-003 target of >60%.
 - *Input*: Mean accuracy from T034a (nested CV).
 - *Logic*:
 1. **Verify Metric Source**: Explicitly verify that the accuracy value used is the **mean of the 5 outer folds** (not a single fold or training metric).
 2. Compare mean accuracy against a baseline threshold. Set `meets_accuracy_target` to `True` or `False` in the output JSON.
 - *Output*: Update `data/results/model_metrics.json` with `meets_accuracy_target` and `mean_outer_fold_accuracy`.

- [ ] T035 [US3] Implement Statistical Comparison. Calculate p-value comparing Random Forest accuracy (from T034a) against the null distribution (from T034b).
 - *Dependency*: **Depends on T034b and T034a**. Requires `data/results/null_distribution.csv` and `data/results/observed_metrics.json`.
 - *Logic*:
 1. Extract the list of observed accuracies from `data/results/observed_metrics.json` (or the single mean if aggregated).
 2. Extract the list of null accuracies from `data/results/null_distribution.csv`.
 3. Perform a **permutation-based p-value calculation**: Count how many null accuracies are >= observed accuracy. Divide by the total number of permutations.
 4. **Mandatory Verification (T052 Integrated)**: Verify that the null distribution was generated correctly (non-empty, variance > 0) and that the comparison logic was executed. If verification fails, raise `StatisticalRigorError`.
 - *Output*: `data/results/model_significance.json` with `p_value`, `significant` (boolean), and `method_verified`.

- [ ] T037 [US3] Write model metrics to `data/results/model_metrics.json`.
 - *Schema*: Includes accuracy, precision, recall, F1, `meets_accuracy_target`, and significance p-value.

- [ ] T038 [US3] Validate output against `specs/001-investigating-the-correlation-between-gu/contracts/model_metrics.schema.yaml`.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Unit test for nested CV structure in `code/tests/test_modeling.py`: Add function `test_nested_cv_feature_selection_is_isolated`.
- [ ] T029 [P] [US3] Integration test for model performance metrics in `code/tests/test_modeling.py`: Add function `test_model_metrics_match_expected_format`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T040a [P] [US1] Unit test for zero-variance taxa exclusion in `code/tests/test_preprocess.py`: Add function `test_zero_variance_taxa_exclusion`.
- [X] T040b [P] [US1] Unit test for LOD handling in `code/tests/test_ingest.py`: Add function `test_lod_exclusion_logic`.
- [X] T040c [P] [US2] Unit test for CLR pseudocount edge cases in `code/tests/test_correlation.py`: Add function `test_clr_pseudocount_handles_extreme_zeros`.
- [X] T041 Run quickstart.md validation
- [X] T042 Implement runtime monitoring in `code/main.py`.
 - *Logic*: Integrate into `code/main.py` orchestration script. Use `time` module to measure total runtime at the end of execution. Log to `data/results/resource_usage.json` with key `total_runtime_seconds`. Assert < 6h (21600s). If violated, raise `RuntimeError`.
 - *Depends on*: Completion of Phase 3, 4, 5.
 - *Note*: This task now enforces a hard limit.
- [X] T043 Implement memory & runtime verification.
 - *Logic*: Integrate into `code/main.py` orchestration script. Use `psutil.Process().memory_info().rss` to measure peak memory at the end of execution. Log to `data/results/resource_usage.json` with key `peak_memory_mb`. Assert < 7GB (7340 MB). If violated, raise `RuntimeError`.
 - *Depends on*: Completion of Phase 3, 4, 5.
 - *Note*: Sequential after T042 to avoid race condition on `resource_usage.json`.
- [X] T045 Generate Final Report.
 - *Input*: All result JSONs/CSVs from previous phases.
 - *Output*: `data/results/final_report.md` aggregating N count, correlation results, model metrics, and success criterion checks.
 - *Dependency*: T037, T035, T042, T043.

---

## Phase 7: Revision & Gap Resolution (Post-Analysis)

**Purpose**: Address specific unresolved claims and data availability gaps identified during analysis.

- [X] T052 [US3] **Verify Null Distribution Robustness**: Enhance `code/04_modeling.py` to validate the null distribution generation.
 - *Rationale*: Ensuring the statistical baseline is valid and the null distribution has sufficient variance.
 - *Logic*:
 1. Add a check in T034b to ensure the null distribution has non-zero variance and a sufficient number of samples (e.g., > 100 permutations).
 2. If the null distribution is degenerate (e.g., all zeros), raise `StatisticalRigorError` and halt.
 3. Log the null distribution mean and variance to `data/results/null_distribution_stats.json`.
 - *Output*: `data/results/null_distribution_stats.json` and updated validation logic.

- [ ] T053 [US3] **Verify Runtime Feasibility (Removed)**: Replaced by hard runtime check in T042.
 - *Rationale*: Predictive runtime estimation requires undefined model parameters. The hard check in T042 is sufficient.

- [ ] T054 [US2] **Enforce Strict Data Streaming for Large OTU Tables**: Update `code/02_preprocess.py` to stream data if the OTU table exceeds RAM, preventing OOM crashes without fabricating data.
 - *Rationale*: Addressing concerns regarding large real datasets and preventing OOM crashes.
 - *Logic*:
 1. Check the size of `data/processed/filtered_no_zero_var.csv` before loading into memory.
 2. **If the file size > 5GB**, implement a chunked processing strategy using `pandas.read_csv(..., chunksize=...)` or `datasets.load_dataset(..., streaming=True)`.
 3. Process CLR transformation and diversity metrics in chunks, accumulating results in a temporary file or database.
 4. Ensure no synthetic data is generated; if the full dataset cannot be processed within the available time window even with streaming, log a warning and proceed with a documented, reproducible sample rather than halting or faking data.
 - *Output*: Updated `code/02_preprocess.py` with streaming logic and a log entry detailing the processing strategy used (full stream vs. sampled).

- [X] T055 [US1] **Enforce Strict Real Data Fetch with No Synthetic Fallback**: Refactor `code/01_ingest.py` to ensure no synthetic data is ever generated if real data fetch fails.
 - *Rationale*: The specification explicitly forbids synthetic fallbacks to prevent fabrication. A failed real fetch must raise an error immediately.
 - *Logic*:
 1. Search `code/01_ingest.py` for `try/except` blocks catching `DataUnavailableError` (regex: `except DataUnavailableError:`).
 2. Remove any code within these blocks that returns synthetic/mock data.
 3. Ensure that if Strategy A (NCBI SRA fetch) and Strategy B (Raw FASTQ processing) both fail, the script raises `DataUnavailableError` and halts execution immediately.
 4. Add a comment in `code/01_ingest.py` explicitly stating: "NO SYNTHETIC FALLBACK: Real data fetch failure is a hard stop."
 - *Output*: Updated `code/01_ingest.py` with removed synthetic fallback logic and added verification comments.

- [X] T056 [US2] **Document Sampling Strategy and Limitations**: If sampling is used (T014b), document the exact sampling rule and its limitations in `data/results/sampling_report.md`.
 - *Rationale*: Transparency regarding data sampling is required to maintain scientific rigor and reproducibility.
 - *Logic*:
 1. If T014b (Dynamic Sampling) is executed, generate a report `data/results/sampling_report.md`.
 2. The report must include:
 - The original dataset size (N).
 - The sampled dataset size (N_sampled).
 - The sampling method (e.g., simple random sampling with `random_state=42`).
 - The reason for sampling (e.g., "Memory constraints: available RAM < 6GB").
 - The estimated impact on statistical power (qualitative description).
 3. Log the path to this report in `data/results/resource_usage.json`.
 - *Output*: `data/results/sampling_report.md` (if sampling occurred) and updated `resource_usage.json`.

- [X] T057 [US3] **Verify Feature Selection Isolation in Nested CV**: Add a specific test to ensure feature selection is strictly isolated within each fold.
 - *Rationale*: Data leakage in feature selection is a common source of overfitting and invalid results.
 - *Logic*:
 1. In `code/tests/test_modeling.py`, add a test function `test_feature_selection_isolation`.
 2. The test should:
 - Create a mock dataset with a known strong correlation between a specific taxon and the label.
 - Run the nested CV pipeline (T032-T033).
 - Verify that the strong correlation is only detected in the training folds where the taxon is actually present in the training split.
 - Verify that the test folds do not influence the feature selection in the training folds.
 3. If the test fails, raise `StatisticalRigorError`.
 - *Output*: Updated `code/tests/test_modeling.py` with `test_feature_selection_isolation`.

- [X] T058 [US3] **Verify Threshold Sweep Implementation**: Ensure the threshold sweep (T034d) correctly re-runs the inner CV loop for each threshold.
 - *Rationale*: Re-using features from a previous threshold sweep can introduce bias and invalidate the robustness check.
 - *Logic*:
 1. Review `code/04_modeling.py` to ensure T034d re-calls the feature selection logic (T032) for each threshold.
 2. Add a log entry in `data/results/sensitivity_analysis.csv` indicating whether feature selection was re-run for each threshold.
 3. If the log indicates that feature selection was NOT re-run for any threshold, raise `StatisticalRigorError`.
 - *Output*: Updated `code/04_modeling.py` and `data/results/sensitivity_analysis.csv` with verification logs.