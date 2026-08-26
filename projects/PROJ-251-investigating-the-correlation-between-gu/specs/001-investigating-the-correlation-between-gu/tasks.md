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

- [ ] T010 [US1] **NCBI SRA Search & Verification**.
 - *Input*: Research question.
 - *Action*: Search for open-access SRA studies with paired 16S and Influenza serology. Verify the dataset contains all required variables (baseline taxa, post-vaccination titers).
 - *Output*: If found, set `config.SRA_ACCESSION` and write `data/research/sra_search_results.json` with the accession ID and URL. If not found, set `config.USE_SYNTHETIC_DATA = True`, write `data/research/sra_search_results.json` with status "No Real Data Found", **AND write `data/research/sra_status.json` with `{"status": "no_real_data", "use_synthetic": true}`**. **This is a blocking gate for biological claims**.
 - *Verification*: Verify `data/research/sra_status.json` exists and contains `use_synthetic: true` before proceeding to T011b.

---

## Phase 1: Setup & Linting (Pre-requisite)

**Purpose**: Project initialization and basic structure

- [ ] T001 [P] Create project directories explicitly: `code/`, `data/raw`, `data/processed`, `data/results`, `specs/001-investigating-the-correlation-between-gu/contracts/`.
 - *Verification*: Run `ls -R` and verify all directories exist.
 - *Note*: Paths are relative to the repository root.
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (pandas, numpy, scipy, scikit-learn, pyyaml, requests, biom-format).
 - *Note*: Removed `qiime2` and `sra-tools` to reduce bloat and installation risk. `biom-format` is sufficient for conversion.

- [ ] T039 [P] Run ruff check and black format on all files in code/ and fix all reported issues.
 - *Logic*: Run `ruff check code/` and `black code/`.
 - *Verification*: Generate `data/results/lint_report.txt` containing the exit code (0) and a summary of files fixed. If exit code != 0, the task fails.
 - *Output*: `data/results/lint_report.txt`.

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
 - *Verification*: Ensure file exists and is valid YAML.

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

## Phase 3: User Story 1 - Ingestion & Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Ingest pre-processed 16S rRNA OTU tables and serology metadata, filter for complete records, and perform necessary preprocessing steps (normalization, diversity, log-transform, CLR) in strict sequential order.

**Independent Test**: The system can be tested by running the ingestion script against a known valid subset and verifying the output CSV contains exactly N rows (N ≥ 50) with no nulls in required columns.

### Strategy A: Primary Data Fetch (NCBI SRA)

- [ ] T011a [US1] Implement Strategy A: Fetch pre-processed OTU table and serology metadata for the SRP accession series.
 - *Method*: Use `config.SRA_ACCESSION` to determine the specific accession. Fetch pre-processed OTU tables and serology metadata. If the fetch fails (404 or timeout), raise `DataUnavailableError`.
 - *Output*: `data/raw/otutable.csv` (columns: `subject_id`, `taxon_A`, `taxon_B`,...), `data/raw/serology.csv` (columns: `subject_id`, `titer_baseline`, `titer_post`).

### Strategy B: Synthetic Data Fallback (Conditional)

- [ ] T011b [US1] **Generate Synthetic Dataset** (Conditional).
 - *Condition*: Execute ONLY if `config.USE_SYNTHETIC_DATA` is True (set by T010).
 - *Input*: `config` parameters (N=50, taxa count).
 - *Action*: Generate a synthetic OTU table (relative abundances summing to a constant) and serology metadata (titers) with controlled correlations for validation.
 - *Reproducibility*: Use `random.seed(42)`. Define a specific correlation structure (e.g., 5 taxa with r=0.5, rest noise).
 - *Output*: `data/raw/synthetic_otutable.csv`, `data/raw/synthetic_serology.csv`.
 - *Note*: **Methodology Note**: This task ensures the pipeline can execute for code validation if no real data is found. **Synthetic data is used ONLY for CI/Code Correctness validation and explicitly NOT for biological claims.**

### Filtering, Sampling & Validation (Unified Flow - Strictly Ordered)

- [ ] T011d [US1] **Merge Microbiome and Serology**.
 - *Input*: `data/raw/otutable.csv`, `data/raw/serology.csv` (from T011a) OR `data/raw/synthetic_otutable.csv`, `data/raw/synthetic_serology.csv` (from T011b).
 - *Dependency*: T011a OR T011b must complete first.
 - *Logic*:
 1. **Merge & Filter**: Merge datasets on `subject_id`. Filter out subjects where `titer_baseline` OR `titer_post` is **truly missing (NaN/Null)**. **Do NOT filter out valid '0' or 'ND' (Not Detected) values**.
 2. **Microbiome Completeness**: Verify that for retained subjects, microbiome taxon columns are not **truly missing (NaN)**. '0' abundance is valid.
 3. **Final Validation**: Count subjects (N) in the filtered dataset.
 4. **CRITICAL**: If N < 50 AND `config.USE_SYNTHETIC_DATA` is False (real data found but insufficient), raise `InsufficientSampleSizeError` immediately with message "Insufficient sample size (N < 50) in final dataset." **Log this error to `data/results/error_log.txt` and exit with code 1**.
 5. **Output**: Write the final filtered dataset to `data/processed/cleared_with_diversity.csv`.
 - *Output*: `data/processed/cleared_with_diversity.csv`.
 - *Note*: This task is the sole producer of the merged artifact.

- [ ] T019 [US1] **Implement zero-variance taxa exclusion**.
 - *Input*: `data/processed/cleared_with_diversity.csv` (output of T011d).
 - *Dependency*: T011d must complete first.
 - *Logic*: Filter out taxa with zero variance (all values identical, e.g., all 0) across all subjects BEFORE normalization/CLR to avoid division by zero or undefined statistics. **Note: This is a pre-processing optimization on raw data.**
 - *Output*: `data/processed/cleared_with_diversity.csv` (**Append** a column `zero_variance_removed` or update the file by removing columns; subsequent tasks read this updated file).

- [ ] T019a [US1] **Normalize to Relative Abundance**.
 - *Input*: `data/processed/cleared_with_diversity.csv` (output of T019).
 - *Dependency*: T019 must complete first.
 - *Logic*: Sum abundances per subject and divide each taxon by the sum.
 - *Output*: `data/processed/cleared_with_diversity.csv` (**Append** normalized columns `taxon_A_rel`, `taxon_B_rel`, etc.).

- [X] T020c [US1] Calculate Shannon diversity index in `code/02_preprocess.py` using `data/processed/cleared_with_diversity.csv`.
 - *Input*: `data/processed/cleared_with_diversity.csv` (output of T019a, containing normalized taxa).
 - *Dependency*: T019a must complete first.
 - *Logic*: Calculate Shannon index for each subject. (Note: Shannon depends on taxa abundances, not log-titers).
 - *Output*: `data/processed/cleared_with_diversity.csv` (**Append** `shannon_diversity` column).

- [X] T021 [US1] **Log-Transform Titers & LOD Handling**: Implement log-transformation of raw antibody titers in `code/02_preprocess.py`.
 - *Input*: `data/processed/cleared_with_diversity.csv` (from T011d).
 - *Dependency*: T011d must complete first. (Independent of T019a/T020c/T020a).
 - *Logic*:
 1. **LOD Handling**: For any titer value < Limit of Detection (LOD), impute as a fractional proportion of the LOD. Log the count of imputed values and the strategy used.
 2. Apply `np.log10(titer_post)` (or `np.log`) to `titer_post` column. (Standard log10 or ln).
 3. Add `log_titer` column to the dataset.
 - *Output*: `data/processed/cleared_with_diversity.csv` (**Append** `log_titer` column).

- [X] T020a [US1] Run CLR transformation with a default pseudocount (1e-6) in `code/02_preprocess.py`.
 - *Input*: `data/processed/cleared_with_diversity.csv` (output of T019a).
 - *Dependency*: T019a must complete first.
 - *Logic*: Apply zero-replacement (pseudocount = 1e-6 or `config.CLR_PSEUDOCOUNT`) to all zero abundances, then CLR transformation.
 - *Output*: `data/processed/cleared_with_diversity.csv` (**Append** CLR-transformed columns `taxon_A_clr`, `taxon_B_clr`, etc.).

- [ ] T013 [US1] **Schema Validation**: Validate output against `specs/001-investigating-the-correlation-between-gu/contracts/dataset.schema.yaml`.
 - *Input*: `data/processed/cleared_with_diversity.csv` (output of T011d), `contracts/dataset.schema.yaml` (output of T001a).
 - *Dependency*: T011d AND T001a must complete first.
 - *Logic*: Validate the merged dataset against the schema defined in `contracts/dataset.schema.yaml`.
 - *Output*: `data/results/schema_validation_report.json`.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T009 [P] [US1] Contract test for data schema validation in `code/tests/test_ingest.py`: Add function `test_validate_schema_loads_yaml`.
- [X] T010b [P] [US1] Integration test for data filtering logic in `code/tests/test_ingest.py`: Add function `test_filter_excludes_null_titers`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Correlation Analysis and Multiple Testing Correction (Priority: P2)

**Goal**: Calculate diversity metrics, apply CLR transformation, and perform Spearman correlation with BH correction.

**Independent Test**: The system can be tested by running analysis on a synthetic dataset with known correlations and verifying that the output correctly identifies the expected significant taxa and reports the corrected p-values.

### Implementation for User Story 2

- [ ] T032 [US2] **Permutation Testing & Feature Selection**: Implement Spearman rank correlation with Permutation Testing and BH correction in `code/03_correlation.py`.
 - *Input*: `data/processed/cleared_with_diversity.csv` (contains CLR taxa and `log_titer`). **Requires T021 to have successfully added log_titer column**.
 - *Dependency*: T019, T019a, T020a, **T021** must complete first.
 - *Logic*:
 1. **Global Unsupervised Filter**: Remove taxa with zero variance (already done in T019, but verify).
 2. **Permutation Test**: Calculate Spearman correlation between each taxon and `log_titer`. Generate empirical p-values by shuffling the `log_titer` labels 1000 times (`n_permutations=1000`) and calculating the proportion of permuted correlations that exceed the observed correlation.
 3. **Intermediate Artifact**: Save empirical p-values to `data/results/permutation_pvalues.csv`. **Verify file exists before proceeding**.
 4. **BH Correction**: Apply Benjamini-Hochberg correction to the **empirical** p-values from the permutation test.
 5. **Selection**: Select taxa with $p_{adj} < 0.05$.
 - *Methodology Override*: **Note**: This task implements "Permutation Testing" to generate empirical p-values. This is a deviation from FR-005 (which specifies standard BH on correlation p-values) **authorized by the Plan** to generate empirical p-values for robustness.
 - *Output*: `data/results/correlation_results.json`.

- [ ] T024 [US2] Write correlation results (coeff, raw p, adj p) to `data/results/correlation_results.csv`.
 - *Schema*: Columns `[taxon, coefficient, raw_pvalue, adj_pvalue]`.
 - *Logic*: Load `correlation_results.json` and write to CSV.

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
 - *Dependency*: T011d must complete first.

- [ ] T032a [US3] **Implement Feature Selection Inside Training Loop**.
 - *Input*: `data/processed/cleared_with_diversity.csv`, `data/processed/responder_labels.csv`.
 - *Dependency*: T030d must complete first.
 - *Logic*: Implement a function `select_features_inner_loop(train_X, train_y)` that performs variance filtering + BH correction strictly on the training set only. This function will be called inside the nested CV loop in T034d.
 - *Output*: `code/04_modeling.py` (updated with `select_features_inner_loop` function).

- [ ] T034d [US3] **Nested CV & Sensitivity Analysis**.
 - *Input*: `data/processed/cleared_with_diversity.csv`, `data/processed/responder_labels.csv`.
 - *Dependency*: T030d, **T032**, **T032a** must complete first. (T020c is NOT required).
 - *Logic*:
 1. **Threshold Loop**: Loop through responder thresholds across a representative range (slightly below to slightly above the default threshold in equal steps). The 'default threshold' is defined by `config.SEROCONVERSION_THRESHOLD` if the active mode is seroconversion, or `config.HAI_THRESHOLD` if the active mode is absolute titer. Sweep range: ±10% in 5 steps.
 2. **For EACH threshold**:
 a. Define the NEW responder labels based on the current threshold.
 b. **Regenerate Outer Folds**: Generate a set of NEW folds for the current threshold split (do NOT reuse folds from previous thresholds).
 c. **Inner Loop**: For each outer fold:
 i. **Feature Selection**: Call `select_features_inner_loop` (from T032a) strictly within the training set of this fold.
 ii. **Model**: Train Random RF on selected features.
 iii. **Evaluate**: Test on the held-out fold.
 d. **Null Distribution**: Generate a null distribution by permuting labels (or features) for the current threshold's outer folds.
 e. **Log Metrics**: Record accuracy, precision, recall, F1 for this threshold.
 f. **Output**: Save null distribution to `data/results/null_distribution.csv` (**Append** with a `threshold_id` column for each threshold iteration).
 3. **Output**: `data/results/sensitivity_analysis.csv` and `data/results/model_metrics.json`.

- [ ] T036a [US3] Calculate and log confusion matrix, precision, recall, F1-score for high/low responders.
 - *Input*: Model predictions from T034d.
 - *Output*: Metrics included in `data/results/model_metrics.json`.

- [ ] T036b [US3] **Success Criterion Check**: Verify if the model's cross-validated accuracy meets the SC-003 target of >60%.
 - *Input*: Mean accuracy from T034d (nested CV).
 - *Logic*: Compare mean accuracy against a baseline threshold. Set `meets_accuracy_target` to `True` or `False` in the output JSON.
 - *Output*: Update `data/results/model_metrics.json`.

- [ ] T035 [US3] Implement Statistical Comparison. Calculate p-value comparing Random Forest accuracy (from T034d) against the null distribution (from T034d).
 - *Dependency*: **Depends on T034d**. Requires `data/results/null_distribution.csv` and `data/results/model_metrics.json`.

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
 - *Action*: Count significant taxa. **Log** if count is outside expected range (1 to 9, defined in `config.SIGNIFICANT_TAXA_RANGE`) AND data is real. **Do NOT halt execution**. If synthetic, log "Exploratory" and proceed.
 - *Output*: Log entry in `data/results/final_report.md` or `data/results/success_criteria_log.txt`.

- [ ] T045 [US3] **Final Report Generation**.
 - *Input*: All result JSONs/CSVs from previous phases.
 - *Output*: `data/results/final_report.md` aggregating N count, correlation results, and model metrics.
 - *Template Requirements*: Must include sections for "Data Overview", "Correlation Results", "Model Performance", "Sensitivity Analysis", and "Conclusion". Must cite specific file paths for all data artifacts.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T040a [P] [US1] Unit test for zero-variance taxa exclusion in `code/tests/test_preprocess.py`: Add function `test_zero_variance_taxa_exclusion`.
- [X] T040b [P] [US1] Unit test for LOD handling in `code/tests/test_ingest.py`: Add function `test_lod_exclusion_logic`.
- [X] T040c [P] [US2] Unit test for CLR pseudocount edge cases in `code/tests/test_correlation.py`: Add function `test_clr_pseudocount_handles_extreme_zeros`.
- [X] T041 Run quickstart.md validation
- [X] T042 Implement runtime monitoring in `code/main.py`.
 - *Logic*: Integrate into `code/main.py` orchestration script. Use `time` module to measure total runtime at the end of execution. Log to `data/results/resource_usage.json` with key `total_runtime_seconds`. Assert < `config.RUNTIME_LIMIT` (from spec). If violated, raise `RuntimeError`.
 - *Depends on*: Completion of Phase 3, 4, 5.
- [X] T043 Implement memory & runtime verification.
 - *Logic*: Integrate into `code/main.py` orchestration script. Use `psutil.Process().memory_info().rss` to measure peak memory at the end of execution. Log to `data/results/resource_usage.json` with key `peak_memory_mb`. Assert < 7GB (7340 MB). If violated, raise `RuntimeError`.
 - *Depends on*: Completion of Phase 3, 4, 5.
- [X] T052 [US3] **Verify Null Distribution Robustness**: Enhance `code/04_modeling.py` to validate the null distribution generation.
- [X] T056 [US3] **Document Sampling Strategy and Limitations**: If sampling is used (T011d), document the exact sampling rule and its limitations in `data/results/sampling_report.md`.
- [X] T057 [US3] **Verify Feature Selection Isolation in Nested CV**: Add a specific test to ensure feature selection is strictly isolated within each fold.
- [X] T058 [US3] **Verify Threshold Sweep Implementation**: Ensure the threshold sweep (T034d) correctly re-runs the inner CV loop for each threshold.