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
 - *Action*: Search for open-access SRA studies with paired 16S and Influenza serology using the NCBI E-utilities API. Use the specific search query: `"16S rRNA AND (influenza OR flu) AND (serology OR antibody OR titer) AND (human OR Homo sapiens)"`. Verify the dataset contains all required variables (baseline taxa, post-vaccination titers).
 - *Output*: If found, set `config.SRA_ACCESSION` and write `data/research/sra_search_results.json` with the accession ID and URL. If not found, set `config.USE_SYNTHETIC_DATA = True`, write `data/research/sra_search_results.json` with status "No Real Data Found", **AND write `data/research/sra_status.json` with `{"status": "no_real_data", "use_synthetic": true}`**. **This is a blocking gate for biological claims**.
 - *Verification*: Verify `data/research/sra_status.json` exists and contains `use_synthetic: true` before proceeding to T011b.

---

## Phase 1: Setup & Linting (Pre-requisite)

**Purpose**: Project initialization and basic structure

- [ ] T001 [P] Create project root directories explicitly: `code/`, `data/raw`, `data/processed`, `data/results`, `tests/`.
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

**Goal**: Ingest pre-processed 16S rRNA OTU tables and serology metadata, filter for complete records, and perform necessary preprocessing steps (normalization, diversity, log-transform, CLR) in strict sequential order with distinct intermediate files.

**Data Flow Note**: The processing chain is strictly ordered: Merge (`data_merged.csv`) -> Normalize (`data_norm.csv`) -> Diversity (`data_div.csv`) -> Log-Transform (`data_log.csv`) -> CLR (`data_clr.csv`). Each step produces a new file with the updated suffix.

**Independent Test**: The system can be tested by running the ingestion script against a known valid subset and verifying the output CSV contains exactly N rows (N ≥ 50) with no nulls in required columns.

### Strategy A: Primary Data Fetch (NCBI SRA)

- [ ] T011a [US1] Implement Strategy A: Fetch pre-processed OTU table and serology metadata for the SRP accession series.
 - *Method*: Use `config.SRA_ACCESSION` to determine the specific accession. Fetch pre-processed OTU tables and serology metadata. The fetch must support **CSV or BIOM** formats. Construct the URL based on the study's repository structure (e.g., `). If the fetch fails (404 or timeout), raise `DataUnavailableError`.
 - *Output*: `data/raw/otutable.csv` (columns: `subject_id`, `taxon_A`, `taxon_B`,...), `data/raw/serology.csv` (columns: `subject_id`, `titer_baseline`, `titer_post`).

### Strategy B: Synthetic Data Fallback (Conditional)

- [ ] T011b [US1] **Generate Synthetic Dataset** (Conditional).
 - *Condition*: Execute ONLY if `config.USE_SYNTHETIC_DATA` is True (set by T010).
 - *Input*: `config` parameters (N=50, taxa count).
 - *Action*: Generate a synthetic OTU table (relative abundances summing to a constant) and serology metadata (titers) with controlled correlations for validation.
 - *Reproducibility*: Use `random.seed(42)`. Define a specific correlation structure: **Generate 5 taxa with r=0.5 using Cholesky decomposition of a correlation matrix where the target variable correlates with these 5 taxa at 0.5 and others at 0.0**.
 - *Output*: `data/raw/synthetic_otutable.csv`, `data/raw/synthetic_serology.csv`.
 - *Note*: **Methodology Note**: This task ensures the pipeline can execute for code validation if no real data is found. **Synthetic data is used ONLY for CI/Code Correctness validation and explicitly NOT for biological claims.**

### Filtering, Sampling & Validation (Unified Flow - Strictly Ordered)

- [ ] T011d [US1] **Merge Microbiome and Serology**.
 - *Input*: `data/raw/otutable.csv`, `data/raw/serology.csv` (from T011a) OR `data/raw/synthetic_otutable.csv`, `data/raw/synthetic_serology.csv` (from T011b).
 - *Dependency*: T011a OR T011b must complete first.
 - *Logic*:
 1. **Merge & Filter**: Merge datasets on `subject_id`. Filter out subjects where `titer_baseline` OR `titer_post` is **truly missing (NaN/Null)**.
 2. **LOD Handling**: For any titer value marked as 'ND' (Not Detected) or '0', **impute as a fraction of the limit of detection**. **Default LOD: If `config.LOD_VALUE` is not set, default to 10.0**. If LOD is undefined, exclude the row. **Ensure all titer columns are numeric**.
 3. **Microbiome Completeness**: Verify that for retained subjects, microbiome taxon columns are not **truly missing (NaN)**. '0' abundance is valid.
 4. **Final Validation**: Count subjects (N) in the filtered dataset.
 5. **CRITICAL**: If N < 50 AND `config.USE_SYNTHETIC_DATA` is False (real data found but insufficient), raise `InsufficientSampleSizeError` immediately with message "Insufficient sample size (N < 50) in final dataset." **Log this error to `data/results/error_log.txt` and exit with code 1**.
 6. **Output**: Write the final filtered dataset to `data/processed/data_merged.csv`.
 - *Output*: `data/processed/data_merged.csv`.
 - *Note*: This task is the sole producer of the merged artifact. **Verify Td_doc has been completed to document the LOD choice.**

- [ ] T011d_doc [US1] **Document LOD Handling Choice**.
 - *Input*: T011d logic.
 - *Action*: Write a section to `data/results/assumptions.md` explicitly documenting the choice to impute LOD values as 0.5 * LOD (default 10.0) rather than excluding subjects, citing the Spec's Edge Cases requirement to "treat these as a specific value... with the choice documented".
 - *Output*: `data/results/assumptions.md`.
 - *Verification*: Verify `assumptions.md` contains the specific LOD handling rationale.

- [ ] T019a [US1] **Normalize to Relative Abundance**.
 - *Input*: `data/processed/data_merged.csv` (output of T011d).
 - *Dependency*: T011d must complete first.
 - *Logic*: Sum abundances per subject and divide each taxon by the sum.
 - *Output*: Write normalized data to `data/processed/data_norm.csv` (**Do not append to existing file; write new file**).

- [ ] T020c [US1] Calculate Shannon diversity index in `code/02_preprocess.py` using `data/processed/data_norm.csv`.
 - *Input*: `data/processed/data_norm.csv` (output of T019a, containing normalized taxa).
 - *Dependency*: T019a must complete first.
 - *Logic*: Calculate Shannon index for each subject. (Note: Shannon depends on taxa abundances, not log-titers).
 - *Output*: Write data with `shannon_diversity` column to `data/processed/data_div.csv`.

- [X] T021 [US1] **Log-Transform Titers & LOD Handling**: Implement log-transformation of raw antibody titers in `code/02_preprocess.py`.
 - *Input*: `data/processed/data_norm.csv` (output of T019a).
 - *Dependency*: **T019a must complete first**. (Note: T021 does NOT depend on T020c; it reads from `data_norm.csv` directly to avoid dependency on Shannon calculation).
 - *Logic*:
 1. **LOD Handling**: Verify all titer values are numeric (imputed in T011d).
 2. Apply `np.log10(titer_post)` (or `np.log`) to `titer_post` column. (Standard log10 or ln).
 3. Add `log_titer` column to the dataset.
 - *Output*: Write data with `log_titer` column to `data/processed/data_log.csv`.

- [X] T020a [US1] Run CLR transformation with a default pseudocount (1e-6) in `code/02_preprocess.py`.
 - *Input*: `data/processed/data_log.csv` (output of T021).
 - *Dependency*: **T021 must complete first**. **Note: T020a depends on T021 to ensure log-transformed titers are present, though CLR applies to abundances.**
 - *Logic*: Apply zero-replacement (pseudocount = 1e-6 or `config.CLR_PSEUDOCOUNT`) to all zero abundances, then CLR transformation.
 - *Output*: Write data with CLR-transformed columns (`taxon_A_clr`, etc.) to `data/processed/data_clr.csv`.

- [ ] T013 [US1] **Schema Validation**: Validate output against `specs/001-investigating-the-correlation-between-gu/contracts/dataset.schema.yaml`.
 - *Input*: `data/processed/data_clr.csv` (output of T020a), `contracts/dataset.schema.yaml` (output of T001a).
 - *Dependency*: T020a AND T001a must complete first.
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

- [ ] T032 [US2] **Correlation & Feature Selection (Spearman Primary)**.
 - *Input*: `data/processed/data_clr.csv` (contains CLR taxa and `log_titer`). **Requires T020a (CLR) and T021 (Log-Transform) to have completed**.
 - *Dependency*: T019a, T021, T020a must complete first. (T020c is NOT required).
 - *Logic*:
 1. **Global Unsupervised Filter (Conditional Fallback)**: Remove taxa with zero variance (variance < 1e-9) across the full dataset. **This is a fallback only if BH yields no features later**.
 2. **Primary Correlation**: Perform **Spearman Rank Correlation** between CLR-transformed taxa and log-transformed titers to generate raw p-values. **This is the primary method** as per Spec FR-004.
 3. **BH Correction**: Apply Benjamini-Hochberg correction to the **raw p-values**.
 4. **Selection**: Select taxa with $p_{adj} < 0.05$. If none, fallback to **top-k (k=10)** by raw magnitude from the *variance-filtered* set.
 5. **Secondary Comparison**: Run a **Permutation Test** (1000 permutations, shuffling `log_titer` labels) to generate empirical p-values for comparison. Save this to a separate artifact.
 6. **Output**: Write primary results (Spearman p-values) to `data/results/correlation_results.json`. Write secondary comparison results to `data/results/permutation_comparison.json`.
 - *Methodology Note*: This task prioritizes Spearman Correlation as the primary method to align with Spec FR-004. Permutation testing is secondary for robustness.
 - *Output*: `data/results/correlation_results.json`.

- [ ] T024 [US2] Write correlation results (coeff, raw p, adj p) to `data/results/correlation_results.csv`.
 - *Schema*: Columns `[taxon, coefficient, raw_pvalue, adj_pvalue]`.
 - *Logic*: Load `correlation_results.json` and write to CSV.

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
 - *Dependency*: T011d must complete first.

- [ ] T025 [US2] **Measure & Log SC-004 Outcome**.
 - *Input*: `data/results/correlation_results.json`.
 - *Action*: Count significant taxa (adj p < 0.05).
 - *Logic*: **If data is REAL** (config.USE_SYNTHETIC_DATA is False) AND count is outside expected range (1 to 9), **log a WARNING** to `data/results/error_log.txt`. **DO NOT HALT**. Write a status report to `data/results/sc004_status.json` with the count and a flag indicating "outside_expected_range". **Proceed to next task**.
 - *Output*: Log entry and `data/results/sc004_status.json`.
 - *Dependency*: Must run BEFORE T034d.
 - *Note*: This task is a **non-blocking validation**. It confirms data readiness but does not stop the pipeline.

- [ ] T032a [US3] **Implement Feature Selection Inside Training Loop**.
 - *Input*: `data/processed/data_clr.csv`, `data/processed/responder_labels.csv`.
 - *Dependency*: T030d must complete first.
 - *Logic*: Implement a function `select_features_inner_loop(train_X, train_y)` that performs variance filtering + BH correction strictly on the training set only. This function will be called inside the nested CV loop in T034d.
 - *Output*: `code/04_modeling.py` (updated with `select_features_inner_loop` function).

- [ ] T034d [US3] **Nested CV & Sensitivity Analysis**.
 - *Input*: `data/processed/data_clr.csv`, `data/processed/responder_labels.csv`.
 - *Dependency*: T030d, **T032**, **T032a**, **T025** must complete first. (T020c is NOT required).
 - *Logic*:
 1. **Status Check**: Read `data/results/sc004_status.json`. If T025 flagged "outside_expected_range" for real data, log a **WARNING** that the model is being trained on a dataset with low correlation signal, but **CONTINUE** execution.
 2. **Threshold Loop**: Loop through responder thresholds across a representative range.
 - **Base Threshold**: Use **4.0** (seroconversion) as the starting point.
 - **Sweep Range**: Calculate 5 steps: `base_threshold * (1 + i * 0.05)` for i in a set of integer values spanning from negative to positive indices, including zero. (±10%).
 3. **For EACH threshold**:
 a. Define the NEW responder labels based on the current threshold.
 b. **Regenerate Outer Folds**: Generate a set of NEW folds for the current threshold split (do NOT reuse folds from previous thresholds).
 c. **Inner Loop**: For each outer fold:
 i. **Feature Selection**: Call `select_features_inner_loop` (from T032a) strictly within the training set of this fold.
 ii. **Model**: Train Random RF on selected features.
 iii. **Evaluate**: Test on the held-out fold.
 d. **Log Isolation**: **Explicitly log** that feature selection was isolated within the training set for this threshold and fold, verifying FR-007 compliance.
 e. **Null Distribution**: Generate a null distribution by permuting labels (or features) for the current threshold's outer folds.
 f. **Log Metrics**: Record accuracy, precision, recall, F1 for this threshold.
 g. **Output**: Save null distribution to `data/results/null_distribution.csv` (**Append** with a `threshold_id` column for each threshold iteration).
 4. **Resource Check**: Monitor runtime/memory. If limits are approached, trigger sampling fallback (see T042/T043).
 5. **Output**: `data/results/sensitivity_analysis.csv` and `data/results/model_metrics.json`.

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
 - *Logic*: Integrate into `code/main.py` orchestration script. Use `time` module to measure total runtime at the end of execution. Log to `data/results/resource_usage.json` with key `total_runtime_seconds`. **If runtime > 1.5 hours, trigger sampling fallback (call `code/00_sample.py` with `seed=42, retain_ratio=0.8`) to downsample) and re-run**. If still > 2 hours, raise `RuntimeError`.
 - *Depends on*: Completion of Phase 3, 4, 5.
- [X] T043 Implement memory & runtime verification.
 - *Logic*: Integrate into `code/main.py` orchestration script. Use `psutil.Process().memory_info().rss` to measure peak memory at the end of execution. Log to `data/results/resource_usage.json` with key `peak_memory_mb`. **If memory > 6 GB, trigger sampling fallback (call `code/00_sample.py` with `seed=42, retain_ratio=0.8`)**. If still > 7 GB, raise `RuntimeError`.
 - *Depends on*: Completion of Phase 3, 4, 5.
- [X] T052 [US3] **Verify Null Distribution Robustness**: Enhance `code/04_modeling.py` to validate the null distribution generation.
- [X] T056 [US3] **Document Sampling Strategy and Limitations**: If sampling is used (T011d), document the exact sampling rule and its limitations in `data/results/sampling_report.md`.
- [X] T057 [US3] **Verify Feature Selection Isolation in Nested CV**: Add a specific test to ensure feature selection is strictly isolated within each fold.
- [X] T058 [US3] **Verify Threshold Sweep Implementation**: Ensure the threshold sweep (T034d) correctly re-runs the inner CV loop for each threshold.