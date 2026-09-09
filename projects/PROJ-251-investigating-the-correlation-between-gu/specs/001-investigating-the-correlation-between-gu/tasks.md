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

- [ ] T010 [US1] [SC-001] **NCBI SRA Search & Verification**.
 - *Input*: Research question.
 - *Action*: Search for open-access SRA studies with paired 16S and Influenza serology using the NCBI E-utilities API. Use the specific search query: `"16S rRNA AND (influenza OR flu) AND (serology OR antibody OR titer) AND (human OR Homo sapiens)"`. Verify the dataset contains all required variables (baseline taxa, post-vaccination titers).
 - *Output*:
 - **If Found**: Set `config.SRA_ACCESSION` and write `data/research/sra_search_results.json` with the accession ID and URL. Write `data/research/sra_status.json` with `{"status": "real_data_found", "use_synthetic": false, "accession": "..."}`.
 - **If Not Found**: Set `config.USE_SYNTHETIC_DATA = True`, write `data/research/sra_search_results.json` with status "No Real Data Found", **AND write `data/research/sra_status.json` with `{"status": "no_real_data", "use_synthetic": true}`**. **This is a blocking gate for biological claims**.
 - *Verification*:
 - **Real Data Path**: Run `python -c "import json; d=json.load(open('data/research/sra_status.json')); assert d['use_synthetic']==False and d['accession'] is not None"`.
 - **No Real Data Path**: Run `python -c "import json; d=json.load(open('data/research/sra_status.json')); assert d['use_synthetic']==True"`.
 - *Constraint*: Pipeline cannot proceed to T011d until this task completes and verification passes.

---

## Phase 1: Setup & Linting (Pre-requisite)

**Purpose**: Project initialization and basic structure

- [ ] T001 [P] Create project root directories explicitly: `code/`, `data/raw`, `data/processed`, `data/results`, `tests/`, `data/research`.
 - *Verification*: Run `ls -R` and verify all directories exist.
 - *Note*: Paths are relative to the repository root.
- [X] T002 [P] Initialize Python 3.11 project with `requirements.txt` (pandas, numpy, scipy, scikit-learn, pyyaml, requests, biom-format).
 - *Note*: Removed `qiime2` and `sra-tools` to reduce bloat and installation risk. `biom-format` is sufficient for conversion.

- [ ] T001a [P] Create the `contracts/` directory and generate `dataset.schema.yaml`.
 - *Logic*: Write the following YAML content to `specs/001-investigating-the-correlation-between-gu/contracts/dataset.schema.yaml`:
 ```yaml
 type: object
 required:
 - subject_id
 - titer_baseline
 - titer_post
 properties:
 subject_id:
 type: string
 titer_baseline:
 type: number
 titer_post:
 type: number
 shannon_diversity:
 type: number
 log_titer:
 type: number
 # Dynamic numeric columns for taxa abundances and CLR values are allowed via additionalProperties
 additionalProperties:
 type: number
 ```
 - *Output*: `specs/001-investigating-the-correlation-between-gu/contracts/dataset.schema.yaml`
 - *Verification*: Ensure file exists and is valid YAML. **Note**: The validation logic must handle any number of taxon columns dynamically, as `additionalProperties` allows keys not explicitly listed in `properties`.
 - *Note*: This schema applies to the **processed** artifact (`cleared_final.csv`) as per the data flow.

- [ ] T008a Create `.env` template file with placeholders for `SRA_TOKEN` (if needed) and `DATA_SOURCE_URL`.
 - *Logic*: Run `python -c "f=open('.env','w'); f.write('SRA_TOKEN=YOUR_TOKEN_HERE\\nDATA_SOURCE_URL=YOUR_DATA_SOURCE_URL_HERE\\n'); f.close()"` to ensure actual newlines are written.
 - *Verification*: Run `grep -q 'SRA_TOKEN'.env` to confirm file exists and contains placeholder.
 - *Output*: `.env`
- [X] T008b [Story] Implement `.env` loading in `code/utils/config.py` using `python-dotenv`.
 - *Dependency*: T008a must complete first (sequential execution).
 - *Logic*: Import `load_dotenv()` and ensure `os.getenv` retrieves values.
 - *Output*: Updated `code/utils/config.py`.
 - *Note*: Removed [P] tag as this is sequential.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create configuration module `code/utils/config.py` with paths, seeds, and thresholds. **Include `SRA_ACCESSION`, `LOD_VALUE`, `SEROCONVERSION_THRESHOLD` (default), `NUM_SYNTHETIC_TAXA` (default 20), `TARGET_CORRELATION`, and `SAMPLING_FACTOR` (default 0.1) variables** to be populated during research phase.
- [X] T005 [P] Implement schema validators `code/utils/validators.py` for dataset, correlation, and model metrics
- [X] T006 [P] Setup logging infrastructure in `code/utils/logging_config.py` to capture exclusion counts and errors
- [X] T007 [P] Create base data loading helpers in `code/utils/data_loader.py`

**Phase 1b: Linting (Sequential)**
- [ ] T039 [P] Run ruff check and black format on all files in code/ and fix all reported issues.
 - *Dependency*: T004, T005, T006, T007, T008b must complete first.
 - *Logic*: Run `ruff check code/ 2>&1 | tee /tmp/ruff_out.txt; echo "Exit code: $?" >> /tmp/ruff_out.txt; ruff check code/ --output-format=full 2>&1 | tee -a /tmp/ruff_out.txt; black code/ 2>&1 | tee -a /tmp/ruff_out.txt; echo "Black Exit: $?" >> /tmp/ruff_out.txt; cp /tmp/ruff_out.txt data/results/lint_report.txt`.
 - *Verification*: Generate `data/results/lint_report.txt` containing the exit code (0) and a summary of files fixed. If exit code != 0, the task fails.
 - *Output*: `data/results/lint_report.txt`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Ingestion & Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Ingest pre-processed 16S rRNA OTU tables and serology metadata, filter for complete records, and perform necessary preprocessing steps (normalization, diversity, log-transform, CLR) in strict sequential order on **distinct immutable artifacts** to ensure a valid derivation chain.

**Data Flow Note**: All preprocessing steps (Merge -> Diversity -> Log -> CLR) are performed sequentially, each writing to a **new file** to preserve immutable derivation chains.
- T011d -> `data/processed/cleared.csv`
- T020c -> `data/processed/cleared_shannon.csv`
- T021 -> `data/processed/cleared_log.csv` (Log Titers only)
- T020a -> `data/processed/cleared_final.csv` (Merges Shannon and Log, adds CLR)

**Design Decision**: The Plan describes preprocessing as updating a single file `cleared_with_diversity.csv` in place. The tasks implement a distinct immutable file strategy (`cleared_shannon.csv`, etc.) to ensure reproducibility and prevent in-place modification errors. This deviation is documented here; a task (T032_plan_update) is added to eventually update the Plan artifact to reflect this correct architecture.

**Independent Test**: The system can be tested by running the ingestion script against a known valid subset and verifying the output CSV contains exactly N rows (N ≥ 50) with no nulls in required columns.

### Strategy A: Primary Data Fetch (NCBI SRA)

- [ ] T011a [US1] Implement Strategy A: Fetch pre-processed OTU table and serology metadata for the SRP accession series.
 - *Method*: Use `config.SRA_ACCESSION` to determine the specific accession. **Deterministic Fetch Priority**: 1. Attempt direct FTP URL construction: `ftp://ftp-trace.ncbi.nlm.nih.gov/sra/sra-instant/reads/ByStudy/sra/SRP/{accession}/`. 2. If 404, attempt `sratoolkit prefetch` if available. 3. If both fail, attempt to fetch from a known GitHub/GitLab mirror specified in study metadata. **Fail loudly** if all methods fail.
 - *Output*: `data/raw/otutable.csv` (columns: `subject_id`, `taxon_A`, `taxon_B`,...), `data/raw/serology.csv` (columns: `subject_id`, `titer_baseline`, `titer_post`).

### Strategy B: Synthetic Data Fallback (Conditional)

- [ ] T011b [US1] **Generate Synthetic Dataset** (Conditional).
 - *Condition*: Execute ONLY if `config.USE_SYNTHETIC_DATA` is True (set by T010 or T011a failure).
 - *Input*: `config` parameters (`NUM_SYNTHETIC_TAXA`, `TARGET_CORRELATION`, `N=50`). **Default `NUM_SYNTHETIC_TAXA` = 20**.
 - *Action*: Generate a synthetic OTU table (relative abundances summing to a constant) and serology metadata (titers) with controlled correlations for validation.
 - *Algorithm*: Use `numpy.random.multivariate_normal` with Cholesky decomposition of a correlation matrix where the target variable correlates with **`config.NUM_SYNTHETIC_TAXA` specific taxa** (indices 0 to `NUM_SYNTHETIC_TAXA-1`) at `r=config.TARGET_CORRELATION` and others at 0.0. **Generate exactly `config.NUM_SYNTHETIC_TAXA` taxa columns**.
 - *Column Naming*: Columns MUST be named `taxon_0`, `taxon_1`,..., `taxon_{N-1}` to match the schema validation (T013) and correlation logic (T032).
 - *Permutation Support*: The synthetic data must be generated such that it can be permuted for validation (e.g., by shuffling the `log_titer` column relative to taxa).
 - *Reproducibility*: Use a fixed random seed to ensure reproducibility.
 - *Output*: `data/raw/synthetic_otutable.csv`, `data/raw/synthetic_serology.csv`.
 - *Note*: **Methodology Note**: This task ensures the pipeline can execute for code validation if no real data is found. **Synthetic data is used ONLY for CI/Code Correctness validation and explicitly NOT for biological claims.**

### Filtering, Sampling & Validation (Unified Flow - Strictly Ordered)

- [ ] T011c [P] **Create Sampling Utility**.
 - *Input*: None.
 - *Action*: Create `code/utils/sampling.py` with a function `stratified_sample(df, target_col, retain_ratio, seed=42)` that performs stratified random sampling by quartiles of `target_col` to preserve distribution.
 - *Output*: `code/utils/sampling.py`.
 - *Verification*: Import and run a dummy test.

- [ ] T011d [US1] **Merge Microbiome and Serology**.
 - *Input*: `data/raw/otutable.csv`, `data/raw/serology.csv` (from T011a) OR `data/raw/synthetic_otutable.csv`, `data/raw/synthetic_serology.csv` (from T011b).
 - *Dependency*: T011a OR T011b must complete first.
 - *Logic*:
 1. **Merge & Filter**: Merge datasets on `subject_id`. Filter out subjects where `titer_baseline` OR `titer_post` is **truly missing (NaN/Null)**.
 2. **LOD Handling**:
 - Read `config.LOD_VALUE` from `code/utils/config.py` (loaded from `.env`).
 - **CRITICAL**: If `config.LOD_VALUE` is **not set (None)**: **Raise `ConfigurationError`** with message "LOD_VALUE must be explicitly set in config. No default allowed." **Do NOT default to 10.0**.
 - Impute 'ND' or '' values as `0.5 * config.LOD_VALUE`.
 - **Ensure all titer columns are numeric**.
 3. **Microbiome Completeness**: Verify that for retained subjects, microbiome taxon columns are not **truly missing (NaN)**. '0' abundance is valid.
 4. **Final Validation**: Count subjects (N) in the filtered dataset.
 5. **Sample Size Check**:
 - **If N < 50 AND `config.USE_SYNTHETIC_DATA` is False (real data found but insufficient)**:
 - **HALT EXECUTION**: Write `data/results/sampling_error.json` with `{"error_type": "InsufficientSampleSize", "count": N, "message": "Insufficient sample size (N < 50). Execution halted as per Spec Edge Cases."}`.
 - Write `data/results/error_log.txt` with the same error message.
 - **Exit with code 1**. **NO DOWNSTREAM TASKS RUN**.
 - **If N >= 50**: Proceed.
 - **If N < 50 AND `config.USE_SYNTHETIC_DATA` is True**: Proceed (Synthetic data is valid for code validation).
 6. **Output**: Write the final filtered dataset to `data/processed/cleared.csv` (initial state: only merged data, no transformations yet).
 - **Documentation**: **Immediately write** a section to `data/results/assumptions.md` documenting the LOD handling choice (impute as 0.5 * LOD) and the sample size outcome.
 - *Output*: `data/processed/cleared.csv`.
 - *Verification*:
 - **File Existence**: If N >= 50 (or synthetic), verify `data/processed/cleared.csv` exists.
 - **Error Path**: If N < 50 (real data), verify `data/results/sampling_error.json` and `data/results/error_log.txt` exist and exit code is 1.
 - **Row Count**: Verify `len(df) >= 50` OR `config.USE_SYNTHETIC_DATA` is True.
 - **Schema Check**: Verify columns `subject_id`, `titer_baseline`, `titer_post` exist.
 - *Note*: This task is the sole producer of the merged artifact.

- [ ] T020c [US1] [FR-003] **Shannon Diversity Calculation**.
 - *Input*: `data/processed/cleared.csv` (output of T011d).
 - *Dependency*: T011d must complete first.
 - *Action*: Calculate Shannon index on microbiome columns. Add column `shannon_diversity`.
 - *Output*: `data/processed/cleared_shannon.csv` (NEW FILE).
 - *Note*: This task produces a distinct file to preserve immutable derivation chain.

- [ ] T021 [US1] **Log-Transform Titers & LOD Handling**.
 - *Input*: `data/processed/cleared.csv` (output of T011d). **Note**: Independent of T020c.
 - *Dependency*: T011d must complete first.
 - *Action*: Log-transform titers, impute LOD (0.5 * LOD) for values below detection. Add column `titer_pre_log`, `titer_post_log`.
 - *Output*: `data/processed/cleared_log.csv` (NEW FILE).
 - *Note*: This task produces a distinct file to preserve immutable derivation chain.

- [ ] T020a [US1] **CLR Transformation**.
 - *Input*: `data/processed/cleared_shannon.csv` (output of T020c) AND `data/processed/cleared_log.csv` (output of T021).
 - *Dependency*: T020c AND T021 must complete first.
 - *Action*:
 1. **Merge**: Merge `cleared_shannon.csv` and `cleared_log.csv` on `subject_id`.
 2. **Normalize**: Convert raw counts to relative abundances (sum=1) for each sample.
 3. **Zero-Replacement**: Apply a small pseudo-count to all zero abundances..
 4. **CLR**: Apply Centered Log-Ratio transformation.
 5. Add columns `taxa_clr` (new columns for each taxon).
 - *Output*: `data/processed/cleared_final.csv` (NEW FILE).
 - *Note*: This task produces a distinct file to preserve immutable derivation chain.

- [ ] T013 [US1] **Schema Validation**: Validate output against `specs/001-investigating-the-correlation-between-gu/contracts/dataset.schema.yaml`.
 - *Input*: `data/processed/cleared_final.csv` (output of T020a), `specs/001-investigating-the-correlation-between-gu/contracts/dataset.schema.yaml` (output of T001a).
 - *Dependency*: T020a AND T001a must complete first.
 - *Logic*: Validate the merged dataset against the schema defined in `specs/001-investigating-the-correlation-between-gu/contracts/dataset.schema.yaml`.
 - *Output*: `data/results/schema_validation_report.json`.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T009 [P] [US1] Contract test for data schema validation in `code/tests/test_ingest.py`: Add function `test_validate_schema_loads_yaml`.
- [X] T010b [P] [US1] Integration test for data filtering logic in `code/tests/test_ingest.py`: Add function `test_filter_excludes_null_titers`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Correlation Analysis and Multiple Testing Correction (Priority: P2)

**Goal**: Calculate diversity metrics, apply CLR transformation, and perform **Spearman Rank Correlation** with BH correction as mandated by FR-004 and US-2. **Permutation testing is NOT used as the primary method.**

**Independent Test**: The system can be tested by running analysis on a synthetic dataset with known correlations and verifying the output correctly identifies the expected significant taxa and reports the corrected p-values.

### Implementation for User Story 2

- [ ] T032a [US2] **Global Unsupervised Variance Filter**.
 - *Input*: `data/processed/cleared_final.csv` (output of T020a).
 - *Dependency*: T020a must complete first.
 - *Logic*:
 1. Identify taxa columns.
 2. Calculate variance for each taxon across all subjects.
 3. Remove taxa with variance < 1e-9 (zero variance).
 4. **Edge Case**: If the filtered set has fewer than `k` taxa (default k=10), take **all available taxa**. If the set is empty, raise `NoFeaturesError` with message "NoFeaturesError: No taxa with variance > 1e-9 found." and log to `data/results/error_log.txt`.
 - *Output*: `data/results/variance_filtered_taxa.json` (list of taxon names).
 - *Note*: This is the **primary feature set** for modeling if correlation yields no results.

- [ ] T032 [US2] [FR-004] [FR-005] **Correlation & Feature Selection (Spearman Primary)**.
 - *Input*: `data/processed/cleared_final.csv`, `data/results/variance_filtered_taxa.json` (from T032a).
 - *Dependency*: T020a AND T032a must complete first.
 - *Logic*:
 1. **Primary Correlation**: Perform **Spearman Rank Correlation** tests between each CLR-transformed taxon (from the variance-filtered set) and `log_titer`. **DO NOT use permutation testing as the primary method.** This aligns with Spec FR-004, overriding the Plan's mention of permutation testing.
 2. **BH Correction**: Apply Benjamini-Hochberg correction to the **standard Spearman p-values**.
 3. **Selection**: Select taxa with $p_{adj} < 0.05$.
 4. **Fallback**: If no taxa are significant, use the **entire variance-filtered set** (from T032a) as the feature list.
 5. **Output**: Write results to `data/results/correlation_results.json` with columns `[taxon, coefficient, raw_pvalue, adj_pvalue]`.
 6. **Documentation**: Update `data/results/assumptions.md` to explicitly document the resolution of the conflict between the Plan (Permutation) and Spec FR-004 (Spearman). State that **Spec FR-004 takes precedence** and Spearman was used. Explicitly note that the Plan's "Constitution Check VI" claim of "Permutation testing is the primary method" is overridden by the Spec's FR-004 mandate.
 - *Methodology Note*: This task implements the mandated Spearman test as the primary method per FR-004 and US-2. **Permutation testing is NOT used.**
 - *Output*: `data/results/correlation_results.json`.

- [ ] T032_plan_update [US2] **Update Plan Artifact to Resolve Contradiction (PLAN KICKBACK REQUIRED)**.
 - *Input*: `plan.md`.
 - *Dependency*: T032 must complete first.
 - *Action*: 
 1. **Check Plan Consistency**: Verify if `plan.md`'s "Constitution Check VI" states "Permutation testing is the primary method" AND if "Phase 3/4" describes a single mutable file `cleared_with_diversity.csv`.
 2. **If Inconsistent**: **HALT EXECUTION**. Write `data/results/plan_kickback_error.json` with `{"status": "kickback", "reason": "Plan artifact contradicts implemented Spearman/Immutable flow. Manual update of plan.md required."}`. **Exit with code 1**. **DO NOT proceed to Phase 5**.
 3. **If Consistent (Plan Updated)**: Edit `plan.md` to remove the contradictory claim in "Constitution Check VI" that "Permutation testing is the primary method". Replace it with "Spearman rank correlation with Benjamini-Hochberg correction is the primary method, as mandated by Spec FR-004". Also update "Phase 3/4" description to remove the reference to a single mutable file and reflect the immutable chain (`cleared_shannon.csv`, etc.).
 - *Output*: Updated `plan.md` (if consistent) OR `data/results/plan_kickback_error.json` (if inconsistent).
 - *Verification*: Run `grep -q "Spearman rank correlation" plan.md` and ensure "Permutation testing" is not listed as the primary method in Constitution Check VI. If kickback triggered, verify error file exists.
 - *Note*: This task enforces that the Plan artifact must be updated to match the implemented Spearman/Immutable flow. If the Plan is not updated, the project halts to prevent documentation drift.

- [ ] T024 [US2] Write correlation results (coeff, raw p, adj p) to `data/results/correlation_results.csv`.
 - *Schema*: Columns `[taxon, coefficient, raw_pvalue, adj_pvalue]`.
 - *Logic*: Load `correlation_results.json` and write to CSV.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for CLR transformation logic in `code/tests/test_correlation.py`: Add function `test_clr_transform_handles_zeros`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Predictive Modeling and Nested Cross-Validation (Priority: P3)

**Goal**: Train Random Forest classifier with nested CV, ensuring feature selection occurs inside the training loop. **Outer folds are regenerated for each threshold.**

**Independent Test**: The system can be tested by running training on the ingested dataset and verifying that feature selection is logged within each fold and accuracy is reported.

### Implementation for User Story 3

- [ ] T030a [US3] [FR-006] [FR-007] Implement seroconversion logic (≥4-fold rise in titer) in `code/04_modeling.py`.
 - *Formula*: `post_titer >= 4 * baseline_titer`.

- [ ] T030b [US3] [FR-006] [FR-007] Implement absolute titer logic (e.g., HAI ≥ 40) in `code/04_modeling.py`.
 - *Formula*: `post_titer >= 40`.

- [ ] T030c [US3] [FR-006] [FR-007] Implement threshold parameterization for responder definition in `code/04_modeling.py`.

- [ ] T030d [US3] [FR-006] [FR-007] Apply responder definition to dataset and output `data/processed/responder_labels.csv`.
 - *Output*: `data/processed/responder_labels.csv` with columns `[subject_id, responder_status]`.
 - *Logic*: Implement sensitivity analysis by generating labels for multiple thresholds (seroconversion, absolute titer, and ±10% sweeps). Log the mode used for each threshold.
 - *Dependency*: T011d must complete first.

- [ ] T032b_model [US3] **Implement Feature Selection Inside Training Loop**.
 - *Input*: `data/processed/cleared_final.csv`, `data/processed/responder_labels.csv`, `data/results/variance_filtered_taxa.json`.
 - *Dependency*: T030d must complete first.
 - *Logic*: Implement a function `select_features_inner_loop(train_X, train_y)` in `code/04_modeling.py` that:
 1. Calculates **Spearman Rank Correlation** between each taxon in `train_X` and `train_y` **strictly within the training fold**.
 2. Applies **BH correction** to these training-fold p-values.
 3. Selects taxa with $p_{adj} < 0.05$.
 4. **Fallback**: If no taxa are significant, use the **variance-filtered set** from `data/results/variance_filtered_taxa.json` (intersected with `train_X` columns).
 5. **Isolation**: Explicitly ensure that this function does NOT read `data/results/correlation_results.json` (global results) to prevent data leakage.
 - *Output*: `code/04_modeling.py` (updated with `select_features_inner_loop` function).
 - *Note*: This ensures feature selection is isolated and prevents data leakage. **MUST use Spearman as primary method**. This function is called dynamically inside the T034d loop for each new label set.

- [ ] T025 [US2] [SC-004] **Measure & Log SC-004 Outcome (Hard Stop for Real Data)**.
 - *Input*: `data/results/correlation_results.json`.
 - *Dependency*: T032 must complete first.
 - *Action*: Count significant taxa (adj p < 0.05).
 - *Logic*: **If data is REAL** (config.USE_SYNTHETIC_DATA is False):
 1. Count significant taxa.
 2. **If count is outside expected range (low single-digit to higher single-digit)**:
 - **HALT EXECUTION**: Write `data/results/sc004_error.json` with `{"status": "error", "count": N, "message": "Significant taxa count outside expected range for real data. Execution halted."}`.
 - **Exit with code 1**. **NO DOWNSTREAM TASKS RUN**.
 3. **If count is within range**:
 - Write `data/results/sc004_status.json` with `{"status": "proceed", "count": N, "expected_range": "low single-digit to higher single-digit"}`.
 - Continue to next task.
 - **If synthetic data**:
 1. Write `data/results/sc004_status.json` with `{"status": "proceed", "count": N, "expected_range": "N/A (Synthetic)"}`.
 2. Continue to next task.
 - *Output*: `data/results/sc004_status.json` or `data/results/sc004_error.json`.
 - *Dependency*: Must run BEFORE T034d.
 - *Note*: This task is a **hard stop gate** for real data.

- [ ] T034d [US3] [FR-007] **Nested CV & Sensitivity Analysis**.
 - *Input*: `data/processed/cleared_final.csv`, `data/processed/responder_labels.csv`, `data/results/variance_filtered_taxa.json`, `data/results/sc004_status.json`, `code/04_modeling.py`.
 - *Dependency*: T030d, **T032**, **T032b_model**, **T025** must complete first.
 - *Logic*:
 1. **Status Check**: Check for `data/results/sc004_error.json`. If exists, **exit with code 1**.
 2. **Threshold Loop**: Loop through responder thresholds across a representative range.
 - **Base Threshold**: Use `config.SEROCONVERSION_THRESHOLD` (default 4.0 if not set).
 - **Sweep Range**: `for i in range(-2, 3): factor = 0.1 * i; threshold = base_threshold * (1 + factor)`. (i.e., -2, -1, 0, 1, 2). **Factor = 0.1**.
 - **Runtime Guard**: If estimated runtime (Multiple thresholds * multiple folds * inner loop) > 1 hour, **proactively reduce folds to 3** for all thresholds to ensure total runtime < 2 hours (SC-005).
 3. **For EACH threshold**:
 a. Define the NEW responder labels based on the current threshold.
 b. **Regenerate Folds**: Generate a **NEW set of outer folds** specifically for this threshold. **Store these folds in `data/results/folds_threshold_{i}.json`** (where {i} is the threshold index). **DO NOT reuse folds from previous thresholds.** The schema for these files must be a list of lists of subject IDs (or indices), e.g., `[[fold1_indices], [fold2_indices],...]`.
 c. **Inner Loop**: For each outer fold:
 i. **Feature Selection**: Call `select_features_inner_loop` (from T032b_model) strictly within the training set of this fold, using the **newly generated labels** for this threshold. **Must use Spearman as primary method**. **If T032 yielded no features, use the variance-filtered set from `data/results/variance_filtered_taxa.json` as the primary feature set**.
 ii. **Model**: Train Random RF on selected features.
 iii. **Evaluate**: Test on the held-out fold.
 d. **Log Isolation**: **Explicitly log** that feature selection was isolated within the training set for this threshold and fold, verifying FR-007 compliance.
 e. **Log Metrics**: Record accuracy, precision, recall, F1 for this threshold.
 4. **Output**: `data/results/sensitivity_analysis.csv` and `data/results/model_metrics.json`.

- [ ] T036a [US3] [SC-003] Calculate and log confusion matrix, precision, recall, F1-score, and **standard deviation of accuracy** for high/low responders.
 - *Input*: Model predictions from T034d.
 - *Output*: Metrics included in `data/results/model_metrics.json`. **Must include `mean_accuracy` and `std_accuracy`**.

- [ ] T036b [US3] [SC-003] **Success Criterion Check**: Verify if the model's cross-validated accuracy meets the SC-003 target of >60%.
 - *Input*: Mean accuracy from T034d (nested CV).
 - *Logic*: Compare mean accuracy against a baseline threshold. Set `meets_accuracy_target` to `True` or `False` in the output JSON.
 - *Output*: Update `data/results/model_metrics.json`.

- [ ] T037 [US3] [SC-003] Write model metrics to `data/results/model_metrics.json`.
 - *Schema*: Includes accuracy, precision, recall, F1, `meets_accuracy_target`, `mean_accuracy`, `std_accuracy`, and significance p-value.

- [ ] T038 [US3] [FR-008] Validate output against `specs/001-investigating-the-correlation-between-gu/contracts/model_metrics.schema.yaml`.
 - *Input*: `data/results/model_metrics.json`.
 - *Dependency*: T037 must complete first.
 - *Logic*: Validate the model metrics JSON against the schema.
 - *Output*: `data/results/model_metrics_validation.json`.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Unit test for nested CV structure in `code/tests/test_modeling.py`: Add function `test_nested_cv_feature_selection_is_isolated`.
- [ ] T029 [P] [US3] Integration test for model performance metrics in `code/tests/test_modeling.py`: Add function `test_model_metrics_match_expected_format`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Validation & Reporting

**Purpose**: Success criterion checks and final report generation

- [ ] T045 [US3] [FR-008] **Final Report Generation**.
 - *Input*: All result JSONs/CSVs from previous phases, `data/results/assumptions.md`.
 - *Output*: `data/results/final_report.md` aggregating N count, correlation results, and model metrics.
 - *Template Requirements*: Must include sections for "Data Overview", "Correlation Results", "Model Performance", "Sensitivity Analysis", and "Conclusion". Must cite specific file paths for all data artifacts. **Must explicitly include the content of `data/results/assumptions.md` (including LOD handling and methodology conflict resolution) in the "Methodology" or "Assumptions" section.**

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040a [P] [US1] Unit test for zero-variance taxa exclusion in `code/tests/test_preprocess.py`: Add function `test_zero_variance_taxa_exclusion`.
- [ ] T040b [P] [US1] Unit test for LOD handling in `code/tests/test_ingest.py`: Add function `test_lod_exclusion_logic`.
- [ ] T040c [P] [US2] Unit test for CLR pseudocount edge cases in `code/tests/test_correlation.py`: Add function `test_clr_pseudocount_handles_extreme_zeros`.
- [ ] T041 [P] Run quickstart.md validation
- [ ] T042 [P] Implement runtime & memory monitoring in `code/main.py`.
 - *Logic*: Integrate into `code/main.py` orchestration script.
 - **Memory Check**: Monitor RAM/Disk usage using `psutil.Process().memory_info().rss`. **If memory > 6 GB**: Trigger sampling fallback (call `code/utils/sampling.py` with `seed=42, retain_ratio=0.8`) to downsample. **Sampling Algorithm**: Perform **stratified random sampling by titer quartile** to preserve distribution. Write output to `data/processed/cleared_sampled.csv`. **Re-run pipeline**: Invoke `python code/main_pipeline.py --input data/processed/cleared_sampled.csv` to restart the pipeline on the new artifact. If memory > 7 GB, raise `RuntimeError`.
 - **Runtime Check**: If runtime > 7200 seconds (2 hours), **raise RuntimeError and exit with code 1** to satisfy SC-005. If runtime > 1.5 hours **AND** memory/disk limits were NOT exceeded, **log a warning** (do not raise RuntimeError) to avoid harsh failures on variable CI performance. Sampling is **only** authorized if RAM/Disk limits are exceeded per Spec Assumptions.
 - *Depends on*: Completion of Phase 3, 4, 5.
 - *Output*: `data/results/resource_usage.json` with keys `total_runtime_seconds` and `peak_memory_mb`.
- [ ] T056 [US3] **Document Sampling Strategy and Limitations**: If sampling is used (T042), document the exact sampling rule and its limitations in `data/results/sampling_report.md`.
 - *Dependency*: T042.
- [ ] T057 [US3] **Verify Feature Selection Isolation in Nested CV**: Add a specific test to ensure feature selection is strictly isolated within each fold.
 - *Action*: Add function `test_feature_selection_isolation_in_nested_cv` in `code/tests/test_modeling.py`.
- [ ] T058 [US3] **Verify Threshold Sweep Implementation**: Ensure the threshold sweep (T034d) correctly re-runs the inner CV loop for each threshold.