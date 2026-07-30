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

## Phase 0: Data Search & Validation (Blocking Gate)

**Purpose**: Verify the existence of a real dataset and set the fallback flag if none is found.

- [ ] T010 [US1] **NCBI SRA Search & Verification**. <!-- ATOMIZE: requested -->
 - *Input*: Research question.
 - *Action*: Search NCBI SRA for open-access studies with paired 16S and Influenza serology. Verify the dataset contains all required variables (baseline taxa, post-vaccination titers).
 - *Output*: If found, set `config.SRA_ACCESSION` and proceed. If not found, set `config.USE_SYNTHETIC_DATA = True` and log "No Real Data Found". **This is a blocking gate for biological claims**.
 - *Constraint*: If no real data is found, the pipeline proceeds with synthetic data for CI validation only.

---

## Phase 1: Setup & Linting (Pre-requisite)

**Purpose**: Project initialization and basic structure

- [ ] T001 [P] Create project directories explicitly: `code/`, `data/raw`, `data/processed`, `data/results`, `specs/001-investigating-the-correlation-between-gu/contracts/`.
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

- [ ] T008a [P] Create `.env` template file with placeholders for `SRA_TOKEN` (if needed) and `DATA_SOURCE_URL`.
 - *Logic*: Write a file `.env` with content: `SRA_TOKEN=YOUR_TOKEN_HERE\nDATA_SOURCE_URL=YOUR_DATA_SOURCE_URL_HERE`.
 - *Verification*: Run `grep -q SRA_TOKEN.env` to confirm file exists and contains placeholder.
 - *Output*: `.env`
- [X] T008b [P] Implement `.env` loading in `code/utils/config.py` using `python-dotenv`.
 - *Dependency*: T008a must complete first (sequential execution).
 - *Logic*: Import `load_dotenv()` and ensure `os.getenv` retrieves values.
 - *Output*: Updated `code/utils/config.py`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create configuration module `code/utils/config.py` with paths, seeds, and thresholds. **Include `SRA_ACCESSION` variable** to be populated during research phase.
- [X] T005 [P] Implement schema validators `code/utils/validators.py` for dataset, correlation, and model metrics
- [X] T006 [P] Setup logging infrastructure in `code/utils/logging_config.py` to capture exclusion counts and errors
- [X] T007 Create base data loading helpers in `code/utils/data_loader.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Validation (Priority: P1) 🎯 MVP

**Goal**: Ingest pre-processed 16S rRNA OTU tables and serology metadata, filtering for complete records.

**Independent Test**: The system can be tested by running the ingestion script against a known valid subset and verifying the output CSV contains exactly N rows (N ≥ 50) with no nulls in required columns.

### Strategy A: Primary Data Fetch (NCBI SRA)

- [ ] T011a [US1] Implement Strategy A: Fetch pre-processed OTU table and serology metadata for the SRP accession series.
 - *Method*: Use `config.SRA_ACCESSION` to determine the specific accession. Fetch pre-processed OTU tables and serology metadata. If the fetch fails (404 or timeout), raise `DataUnavailableError`.
 - *Output*: `data/raw/otutable.csv`, `data/raw/serology.csv`.

### Filtering, Sampling & Validation (Unified Flow)

- [ ] T011d [US1] **Merge Microbiome and Serology**.
 - *Input*: `data/raw/otutable.csv`, `data/raw/serology.csv`.
 - *Logic*:
 1. **Memory Check**: Import `psutil` and `pandas`. Estimate the memory footprint of the raw data.
 2. **CRITICAL**: If estimated memory > available RAM (6GB), raise `InsufficientSampleSizeError` immediately with message "Memory constraints prevent loading full dataset. Pipeline cannot proceed." and halt execution. **NO SAMPLING**.
 3. **Merge & Filter**: Merge datasets on `subject_id`. Filter out subjects where `titer_baseline` OR `titer_post` is null/missing. Log the count of excluded subjects.
 4. **Final Validation**: Count subjects (N) in the filtered dataset.
 5. **CRITICAL**: If N < 50, raise `InsufficientSampleSizeError` immediately with message "Insufficient sample size (N < 50) in final dataset." and halt execution.
 6. **Output**: Write the final filtered dataset to `data/processed/cleared_with_diversity.csv`.
 - *Output*: `data/processed/cleared_with_diversity.csv`.
 - *Note*: This task is the sole producer of the merged artifact.

- [X] T013 [US1] **Schema Validation**: Validate output against `specs/001-investigating-the-correlation-between-gu/contracts/dataset.schema.yaml`.
 - *Pre-check*: Verify `contracts/dataset.schema.yaml` exists.
 - *Logic*: Load schema and validate `data/processed/cleared_with_diversity.csv`.
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
 - *Input*: `data/processed/cleared_with_diversity.csv`.
 - *Output*: `data/processed/cleared_with_diversity.csv` (updated with zero-variance taxa removed).

- [ ] T019a [US2] **Normalization**: Convert `cleared_with_diversity.csv` to relative abundance.
 - *Input*: `data/processed/cleared_with_diversity.csv`.
 - *Logic*: Sum abundances per subject and divide each taxon by the sum.
 - *Output*: `data/processed/cleared_with_diversity.csv` (updated with relative abundances).

- [X] T020a [US2] Run CLR transformation with a default pseudocount (1e-6) in `code/02_preprocess.py`.
 - *Input*: `data/processed/cleared_with_diversity.csv`.
 - *Logic*: Apply zero-replacement (pseudocount = 1e-6 or `config.CLR_PSEUDOCOUNT`) to all zero abundances, then CLR transformation.
 - *Output*: `data/processed/cleared_with_diversity.csv` (updated with CLR-transformed columns).
 - *Verification*: Verify file exists and contains N rows with CLR-transformed columns.
 - *Mandatory Logging*: Log the exact pseudocount value used to `data/results/pseudocount_sensitivity.json` immediately after transformation. Verify that zero-replacement was applied by checking for non-zero values in the output where input had zeros.

- [X] T021 [US2] **Log-Transform Titers & LOD Handling**: Implement log-transformation of raw antibody titers in `code/02_preprocess.py`.
 - *Input*: `data/processed/cleared_with_diversity.csv` (from T020a).
 - *Logic*:
 1. **LOD Handling**: For any titer value < Limit of Detection (LOD), impute as `0.5 * LOD`. Log the count of imputed values and the strategy used.
 2. Apply `np.log(titer_post + 1)` (or similar base) to `titer_post` column.
 3. Add `log_titer` column to the dataset.
 - *Output*: `data/processed/cleared_with_diversity.csv` (updated with log-titers).
 - *Dependency*: Must run after T020a.

- [ ] T020c [US2] Calculate Shannon diversity index in `code/02_preprocess.py` using `data/processed/cleared_with_diversity.csv`.
 - *Input*: `data/processed/cleared_with_diversity.csv` (output of T021, containing CLR taxa and log-titers).
 - *Logic*: Calculate Shannon index for each subject.
 - *Output*: `data/processed/cleared_with_diversity.csv` (Append Shannon index column).
 - *Dependency*: T021, T020a.

- [X] T032 [US2] **Permutation Testing & Feature Selection**: Implement Spearman rank correlation with Permutation Testing and BH correction in `code/03_correlation.py`.
 - *Input*: `data/processed/cleared_with_diversity.csv` (contains CLR taxa and `log_titer`).
 - *Logic*:
 1. **Global Unsupervised Filter**: Remove taxa with zero variance (already done in T019, but verify).
 2. **Permutation Test**: Calculate Spearman correlation between each taxon and `log_titer`. Generate empirical p-values by shuffling the `log_titer` labels 1000 times (`n_permutations=1000`) and calculating the proportion of permuted correlations that exceed the observed correlation.
 3. **BH Correction**: Apply Benjamini-Hochberg correction to the empirical p-values.
 4. **Selection**: Select taxa with $p_{adj} < 0.05$.
 - *Output*: `data/results/correlation_results.json`.
 - *Dependency*: T020c.

- [ ] T024 [US2] Write correlation results (coeff, raw p, adj p) to `data/results/correlation_results.csv`.
 - *Schema*: Columns `[taxon, coefficient, raw_pvalue, adj_pvalue]`.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for CLR transformation logic in `code/tests/test_correlation.py`: Add function `test_clr_transform_handles_zeros`.

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

- [ ] T030d [US3] Apply responder definition to dataset and output `data/processed/responder_labels.csv`.
 - *Output*: `data/processed/responder_labels.csv` with columns `[subject_id, responder_status]`.
 - *Logic*: Use seroconversion if pre-vaccination titers exist; else use absolute titer. Log mode used.

- [ ] T034d [US3] **Nested CV & Sensitivity Analysis**.
 - *Input*: `data/processed/cleared_with_diversity.csv`, `data/processed/responder_labels.csv`.
 - *Logic*:
 1. **Outer Loop**: 5 folds.
 2. **Inner Loop**: Feature selection (variance filter + BH) strictly within the training set.
 3. **Model**: Random Forest trained on **unsupervised variance-filtered features** (primary) or top correlated (secondary).
 4. **Sensitivity**: Loop through responder thresholds across a **representative range (slightly below to slightly above the default threshold in 5 equal steps)**. The 'default threshold' is defined by `config.SEROCONVERSION_THRESHOLD` if the active mode is seroconversion, or `config.HAI_THRESHOLD` if the active mode is absolute titer. For EACH threshold:
 a. Define the range: from 0.9x to 1.1x of the **active** default threshold, divided into equal steps.
 b. For EACH threshold:
 i. Generate a NEW set of responder labels based on the current threshold.
 ii. **Re-run the outer fold splits** to ensure independence from the original splits.
 iii. **Re-run the inner CV loop** to perform feature selection and hyperparameter tuning on the new labels. **Crucial**: This MUST re-execute the full nested loop (outer split -> inner feature selection -> train) for the new labels.
 iv. Train the Random Forest classifier using the features selected in step (iii).
 v. **Re-generate the null distribution** for the current threshold to ensure a valid baseline.
 vi. Evaluate the model on the held-out test sets (from the new outer CV splits) to get a new accuracy metric.
 vii. Compare this new accuracy against the new null distribution.
 5. **Output**: `data/results/sensitivity_analysis.csv` with threshold, accuracy, and p-value per step. Also write `data/results/observed_metrics.json` and `data/results/null_distribution.csv` for the final run.
 - *Dependency*: T030d, T020c.
 - *Constraint*: Re-runs T031, T032, and T034b logic per threshold.

- [ ] T036a [US3] Calculate and log confusion matrix, precision, recall, F1-score for high/low responders.
 - *Input*: Model predictions from T034d.
 - *Output*: Metrics included in `data/results/model_metrics.json`.

- [ ] T036b [US3] **Success Criterion Check**: Verify if the model's cross-validated accuracy meets the SC-003 target of >60%.
 - *Input*: Mean accuracy from T034d (nested CV).
 - *Logic*:
 1. **Verify Metric Source**: Explicitly verify that the accuracy value used is the **mean of the 5 outer folds** (not a single fold or training metric).
 2. Compare mean accuracy against a baseline threshold. Set `meets_accuracy_target` to `True` or `False` in the output JSON.
 - *Output*: Update `data/results/model_metrics.json` with `meets_accuracy_target` and `mean_outer_fold_accuracy`.

- [ ] T035 [US3] Implement Statistical Comparison. Calculate p-value comparing Random Forest accuracy (from T034d) against the null distribution (from T034d).
 - *Dependency*: **Depends on T034d**. Requires `data/results/null_distribution.csv` and `data/results/observed_metrics.json`.
 - *Logic*:
 1. Extract the list of observed accuracies from `data/results/observed_metrics.json`.
 2. Extract the list of null accuracies from `data/results/null_distribution.csv`.
 3. Perform a **permutation-based p-value calculation**: Count how many null accuracies are >= observed accuracy. Divide by the total number of permutations.
 4. **Mandatory Verification**: Verify that the null distribution was generated correctly (non-empty, variance > 0) and that the comparison logic was executed. If verification fails, raise `StatisticalRigorError`.
 - *Output*: `data/results/model_significance.json` with `p_value`, `significant` (boolean), and `method_verified`.

- [ ] T037 [US3] Write model metrics to `data/results/model_metrics.json`.
 - *Schema*: Includes accuracy, precision, recall, F1, `meets_accuracy_target`, and significance p-value.

- [ ] T038 [US3] Validate output against `specs/001-investigating-the-correlation-between-gu/contracts/model_metrics.schema.yaml`.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Unit test for nested CV structure in `code/tests/test_modeling.py`: Add function `test_nested_cv_feature_selection_is_isolated`.
- [ ] T029 [P] [US3] Integration test for model performance metrics in `code/tests/test_modeling.py`: Add function `test_model_metrics_match_expected_format`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Validation & Reporting

**Purpose**: Success criterion checks and final report generation

- [ ] T025 [US2] **Success Criterion Check (SC-004)**.
 - *Input*: `data/results/correlation_results.json`.
 - *Action*: Count significant taxa. **HALT execution** if count is outside expected range (low/high single-digit) AND data is real. If synthetic, log "Exploratory" and proceed.
 - *Output*: Log entry or Error.
 - *Dependency*: T032.

- [ ] T045 [US3] **Final Report Generation**.
 - *Input*: All result JSONs/CSVs from previous phases.
 - *Output*: `data/results/final_report.md` aggregating N count, correlation results, model metrics, and success criterion checks.
 - *Dependency*: T037, T035, T025.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T040a [P] [US1] Unit test for zero-variance taxa exclusion in `code/tests/test_preprocess.py`: Add function `test_zero_variance_taxa_exclusion`.
- [X] T040b [P] [US1] Unit test for LOD handling in `code/tests/test_ingest.py`: Add function `test_lod_exclusion_logic`.
- [X] T040c [P] [US2] Unit test for CLR pseudocount edge cases in `code/tests/test_correlation.py`: Add function `test_clr_pseudocount_handles_extreme_zeros`.
- [X] T041 Run quickstart.md validation
- [X] T042 Implement runtime monitoring in `code/main.py`.
 - *Logic*: Integrate into `code/main.py` orchestration script. Use `time` module to measure total runtime at the end of execution. Log to `data/results/resource_usage.json` with key `total_runtime_seconds`. Assert < 6h (21600s). If violated, raise `RuntimeError`.
 - *Depends on*: Completion of Phase 3, 4, 5.
- [X] T043 Implement memory & runtime verification.
 - *Logic*: Integrate into `code/main.py` orchestration script. Use `psutil.Process().memory_info().rss` to measure peak memory at the end of execution. Log to `data/results/resource_usage.json` with key `peak_memory_mb`. Assert < 7GB (7340 MB). If violated, raise `RuntimeError`.
 - *Depends on*: Completion of Phase 3, 4, 5.
- [X] T052 [US3] **Verify Null Distribution Robustness**: Enhance `code/04_modeling.py` to validate the null distribution generation.
 - *Rationale*: Ensuring the statistical baseline is valid and the null distribution has sufficient variance.
 - *Logic*:
 1. Add a check in T034d to ensure the null distribution has non-zero variance and a sufficient number of samples (e.g., > 100 permutations).
 2. If the null distribution is degenerate (e.g., all zeros), raise `StatisticalRigorError` and halt.
 3. Log the null distribution mean and variance to `data/results/null_distribution_stats.json`.
 - *Output*: `data/results/null_distribution_stats.json` and updated validation logic.

- [X] T056 [US2] **Document Sampling Strategy and Limitations**: If sampling is used (T011d), document the exact sampling rule and its limitations in `data/results/sampling_report.md`.
 - *Rationale*: Transparency regarding data sampling is required to maintain scientific rigor and reproducibility.
 - *Logic*:
 1. If T011d (Memory Check) is executed, generate a report `data/results/sampling_report.md`.
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