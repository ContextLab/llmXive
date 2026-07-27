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
 - *Logic*: Create `pyproject.toml` with black/ruff config and `.ruff.toml` with specific rules.
 - *Verification*: Run `ruff check --version` and `black --version` to confirm installation. Run `ruff check code/` to confirm no errors (initially).
 - *Output*: `pyproject.toml`, `.ruff.toml`.
- [ ] T001a [P] Create the `contracts/` directory and generate `dataset.schema.yaml`.
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
- [ ] T005 [P] Implement schema validators `code/utils/validators.py` for dataset, correlation, and model metrics
- [ ] T006 [P] Setup logging infrastructure in `code/utils/logging_config.py` to capture exclusion counts and errors
- [ ] T007 Create base data loading helpers in `code/utils/data_loader.py`
- [ ] T008a [P] Create `.env` template file with placeholders for `SRA_TOKEN` (if needed) and `DATA_SOURCE_URL`.
 - *Logic*: Write a file `.env` with content: `SRA_TOKEN=YOUR_TOKEN_HERE\nDATA_SOURCE_URL=.
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

- [ ] T011a [US1] Implement Strategy A: Fetch pre-processed OTU table and serology metadata for the SRP accession series.
 - *Method*: If the fetch fails (404 or timeout), raise `DataUnavailableError`.
 - *Control Flow*: In `code/main.py`, wrap T011a in a try-except block: `try: strategy_a() except DataUnavailableError: strategy_b()`.
 - *Output*: `data/raw/otutable.csv`, `data/raw/serology.csv`.

### Strategy B: Fallback Raw FASTQ Processing (Conditional)

> **Conditional Execution Flow**: The tasks T011b, T011c, T011d are ONLY executed if T011a raises `DataUnavailableError`. If T011a succeeds, skip this entire block.

- [ ] T011b [US1] **Execute Strategy B - Download**: Download raw FASTQ files from NCBI SRA for the designated study accession **SRP053178**.
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

- [ ] T015 [US1] **Sample Size Validation Gate (Full Dataset)**: Implement sample size validation in `code/01_ingest.py`.
 - *Input*: `data/processed/filtered.csv` (output of T012) OR `data/processed/filtered_sampled.csv` (output of T012 if it ran).
 - *Depends on*: T012 (sequential).
 - *Logic*:
 1. Count subjects (N) in the input file.
 2. Log N to `data/results/N_count.json`.
 3. **CRITICAL**: If N < 50, raise `InsufficientSampleSizeError` immediately with message "Insufficient sample size (N < 50) in final dataset." and halt execution.
 4. If N >= 50, proceed to T016.
 - *Output*: `data/results/N_count.json` (if N >= 50) or error (if N < 50).

- [ ] T016 [US1] **Write Filtered Dataset**: Write the final filtered dataset to `data/processed/filtered_data.csv`.
 - *Input*: `data/processed/filtered.csv` (from T012) OR `data/processed/filtered_sampled.csv` (from T012 if it ran).
 - *Logic*: Check if `data/processed/filtered_sampled.csv` exists. If yes, use it. If no, use `data/processed/filtered.csv`. Write the selected file to `data/processed/filtered_data.csv`.
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

- [ ] T021 [US2] **Log-Transform Titers & LOD Handling**: Implement log-transformation of raw antibody titers in `code/02_preprocess.py`.
 - *Input*: `data/processed/filtered_data.csv` (or `cleared_with_diversity.csv` if titers are merged there).
 - *Logic*:
 1. **LOD Handling**: For any titer value < Limit of Detection (LOD), impute as `0.5 * LOD`. Log the count of imputed values and the strategy used.
 2. Apply `np.log(titer_post + 1)` (or similar base) to `titer_post` column.
 3. Add `log_titer` column to the dataset.
 - *Output*: Save to `data/processed/cleared_with_diversity.csv` (merged with T020c output).
 - *Dependency*: Must run before T022.

- [ ] T020c [US2] Calculate Shannon diversity index in `code/02_preprocess.py` using `data/processed/cleared_default.csv`.
 - *Input*: `data/processed/cleared_default.csv` (CLR-transformed data).
 - *Output*: `data/processed/cleared_with_diversity.csv` (Append Shannon index column).

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
 - *Logic*: For each pseudocount in a range of log steps (multiple values):
 1. Re-load `filtered_normalized.csv`.
 2. Apply CLR with current pseudocount.
 3. **Re-apply T021 logic** (log-transform titers) to ensure titers are log-transformed for this run.
 4. **Re-apply T022 logic** (Spearman correlation) on the current run's data.
 5. **Re-apply T023 logic (Benjamini-Hochberg correction) independently** to the raw p-values of the *current* pseudocount run. **CRITICAL: Do not reuse BH-corrected values from other runs.**
 6. **Write intermediate correlation results** to `data/processed/corr_pseudocount_X.csv` (where X is the pseudocount value) to ensure reproducibility.
 7. Identify the set of significant taxa (adj-p < 0.05) for the current run.
 8. Calculate Jaccard Index (intersection over union) between the *sets of significant taxa* from different pseudocount runs.
 9. **Runtime Check**: If estimated cumulative time > 5.5 hours, skip remaining runs and log a warning.
 - *Output*: `data/results/pseudocount_sensitivity.json`.

- [ ] T025 [US2] Count taxa with adj-p < 0.05 and compare against the expected range.
 - *Logic*:
 1. Count significant taxa.
 2. **Verify BH Method**: Check that adjusted p-values are monotonically increasing when sorted by raw p-value. If not, raise `StatisticalRigorError`.
 3. **Threshold Verification**: Verify that all reported significant taxa strictly meet `adj_pvalue < 0.05`. If any fail, raise `StatisticalRigorError`.
 4. Log the count and the *expected range description* from the spec ("low single-digit to high single-digit").
 5. If count < 1 or count > 20, set `within_expected_range` to `False (Wikidata Q105812849, https://www.wikidata.org/wiki/Q105812849)` in the output JSON and log a warning. Do NOT halt execution, but flag for review.
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
 1. Calculate Spearman correlation between taxa and labels.
 2. **Apply Benjamini-Hochberg correction** to the raw p-values.
 3. Select the **top taxa** by absolute correlation coefficient (or those with adj-p < 0.1).
 4. **Constraint**: **DO NOT** use global correlation results from T022. Correlation must be recalculated from scratch on the training split data for each fold to prevent data leakage.
 - *Mandatory Output (T051 Integrated)*: Log the list of selected features for *each* outer fold to `data/results/feature_selection_log.csv` with columns `[fold_id, selected_features]`. This artifact is required to verify FR-007 and is a mandatory output of this task, not optional.
 - *Fail-safe*: If feature selection results in zero features for a fold, skip that fold or log a warning and proceed (do not crash).

- [ ] T033 [US3] Implement Random Forest classifier training in `code/04_modeling.py` (CPU-only, default precision).
 - *Hyperparameters*: `n_estimators=100`, `max_depth=None`.

- [ ] T034b [US3] Implement permutation baseline testing: Generate null distribution of accuracy scores by permuting microbiome rows relative to serology labels with `random_seed=42`. Perform **dynamic number of permutations** (min(upper_bound, floor(6h / estimated_time_per_perm))).
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

- [ ] T034d [US3] Implement Threshold Sweep and Robustness Check.
 - *Depends on*: T030d (Responder Labels), T020c (Cleared Data), T034a (for reference).
 - *Logic*: Loop through responder thresholds across a **representative range (x to 1.2x of default threshold in 5 equal steps)**. For EACH threshold:
 1. Define the range: from a value below the default to a value above the default, divided into equal steps.
 2. For EACH threshold:
 a. Generate a NEW set of responder labels based on the current threshold.
 b. **Re-run the full inner CV loop (T032 logic)** to perform feature selection and hyperparameter tuning on the new labels.
 c. Train the Random Forest classifier using the features selected in step (b).
 d. Evaluate the model on the held-out test sets (from the outer CV splits defined in T034a) to get a new accuracy metric.
 e. **Generate a NEW null distribution** for this specific threshold by permuting the new labels relative to the microbiome data (re-implementing T034b logic for this specific threshold). **CRITICAL: Do not reuse the null distribution from T034b.**
 f. Compare the new accuracy against this **threshold-specific** null distribution.
 - *Output*: `data/results/sensitivity_analysis.csv` with threshold, accuracy, and p-value per step.
 - *Dependency*: Independent of T034b (uses its output only as a reference for the default threshold). **Re-runs T032 and T034b logic** per threshold.

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

- [ ] T039 Run ruff check and black format on all files in code/ and fix all reported issues
- [ ] T040a [P] [US1] Unit test for zero-variance taxa exclusion in `code/tests/test_preprocess.py`: Add function `test_zero_variance_taxa_exclusion`.
- [ ] T040b [P] [US1] Unit test for LOD handling in `code/tests/test_ingest.py`: Add function `test_lod_exclusion_logic`.
- [ ] T040c [P] [US2] Unit test for CLR pseudocount edge cases in `code/tests/test_correlation.py`: Add function `test_clr_pseudocount_handles_extreme_zeros`.
- [ ] T041 Run quickstart.md validation
- [ ] T042 [P] Implement runtime monitoring in `code/main.py`.
 - *Logic*: Integrate into `code/main.py` orchestration script. Use `time` module to measure total runtime at the end of execution. Log to `data/results/resource_usage.json` with key `total_runtime_seconds`. Assert < 6h (21600s). If violated, raise `RuntimeError`.
 - *Depends on*: Completion of Phase 3, 4, 5.
 - *Note*: This task now enforces a hard limit.
- [ ] T043 [P] Implement memory & runtime verification.
 - *Logic*: Integrate into `code/main.py` orchestration script. Use `psutil.Process().memory_info().rss` to measure peak memory at the end of execution. Log to `data/results/resource_usage.json` with key `peak_memory_mb`. Assert < 7GB (7340 MB). If violated, raise `RuntimeError`.
 - *Depends on*: Completion of Phase 3, 4, 5.
 - *Note*: Sequential after T042 to avoid race condition on `resource_usage.json`.
- [ ] T045 [P] Generate Final Report.
 - *Input*: All result JSONs/CSVs from previous phases.
 - *Output*: `data/results/final_report.md` aggregating N count, correlation results, model metrics, and success criterion checks.
 - *Dependency*: T037, T035, T042, T043.

---

## Phase 7: Revision & Gap Resolution (Post-Analysis)

**Purpose**: Address specific unresolved claims and data availability gaps identified during analysis.

- [ ] T052 [US3] **Verify Null Distribution Robustness**: Enhance `code/04_modeling.py` to validate the null distribution generation.
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

- [ ] T055 [US1] **Enforce Strict Data Fetching without Synthetic Fallback**: Update `code/01_ingest.py` to remove any `try/except` blocks that fallback to synthetic data generation if the real fetch fails.
 - *Rationale*: Preventing fabrication by ensuring failed real fetches raise errors rather than substituting fake data.
 - *Logic*:
 1. Audit `code/01_ingest.py` for any `generate_synthetic_*`, `mock_*`, or random data generation logic triggered on fetch failure.
 2. Remove all such fallback logic.
 3. Ensure that if `Strategy A` (pre-processed fetch) and `Strategy B` (raw FASTQ processing) both fail, the script raises `DataUnavailableError` immediately without generating any synthetic data.
 4. Update tests to verify that synthetic data is never generated.
 - *Output*: Updated `code/01_ingest.py` and `code/tests/test_ingest.py`.

- [ ] T056 [US2] **Add Explicit Streaming/Sampling Documentation to Tasks**: Update `code/02_preprocess.py` to explicitly document the streaming/sampling rule used if the dataset is processed in chunks.
 - *Rationale*: Ensuring transparency in data handling as per the "Large real datasets" rule.
 - *Logic*:
 1. If chunked processing is used, log the exact chunk size, the number of chunks, and the total rows processed to `data/results/streaming_log.json`.
 2. If a sample is taken (due to time constraints), log the sampling method (e.g., `itertools.islice` first N rows, or random seed), the sample size, and the justification (e.g., "Full dataset processing would exceed 6h time limit").
 3. Ensure this log is included in the final report.
 - *Output*: `data/results/streaming_log.json` and updated `code/02_preprocess.py`.

- [ ] T057 [US3] **Verify Feature Selection Isolation in Nested CV**: Add a specific test to `code/tests/test_modeling.py` to verify that feature selection is strictly isolated within each outer fold.
 - *Rationale*: Ensuring no data leakage in the nested cross-validation process.
 - *Logic*:
 1. Create a test case where the feature selection logic is intentionally "leaked" (e.g., using global correlation results).
 2. Verify that the test fails, confirming the isolation logic is enforced.
 3. Run the test on the actual implementation to ensure it passes.
 - *Output*: Updated `code/tests/test_modeling.py` with `test_feature_selection_isolation`.

- [ ] T058 [US1] **Validate Data Source URL Reachability**: Add a pre-flight check in `code/01_ingest.py` to verify the reachability of the NCBI SRA accession URL before attempting download.
 - *Rationale*: Preventing wasted compute time on unreachable URLs.
 - *Logic*:
 1. Before attempting Strategy A or B, send a `HEAD` request to the target URL.
 2. If the URL is unreachable (timeout, 404, etc.), log the error and raise `DataUnavailableError` immediately.
 3. Do not proceed with download attempts if the URL is invalid.
 - *Output*: Updated `code/01_ingest.py` with pre-flight check logic.