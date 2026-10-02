---
description: "Task list template for feature implementation"
---

# Tasks: Investigating the Correlation Between Gut Microbiome Composition and Cognitive Flexibility

**Input**: Design documents from `/specs/001-gene-regulation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, basic structure, and schema definition

- [X] T001a [P] Create project code structure: `projects/PROJ-346-investigating-the-correlation-between-gu/code/`, `projects/PROJ-346-investigating-the-correlation-between-gu/tests/`
- [X] T001b [P] Create project data structure: `projects/PROJ-346-investigating-the-correlation-between-gu/data/raw/`, `data/processed/`, `data/qc/`
- [X] T002 [P] Initialize Python 3.11 project with `requirements.txt` (pandas, numpy, scipy, scikit-learn, statsmodels, seaborn, matplotlib, requests, pyyaml, qiita-client, ukbiobank, pydantic>=2.0, spaCy) and configure linting (flake8/black)
- [X] T005 [P] Setup data schema validation: Create and output `contracts/dataset.schema.yaml` (YAML format, Pydantic v2 model dump) containing fields: `taxon_name` (str), `relative_abundance` (float), `sample_id` (str) for MicrobialTaxa and `task_type` (str), `z_score` (float), `participant_id` (str) for CognitiveScore. **Completion Criteria**: Run `pytest tests/unit/test_schema.py` to verify file exists, is valid YAML, and passes schema validation. **Note**: This task must complete before T011 and T016.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 [P] Setup environment variable management for dataset URLs (AGP, NHANES, UK Biobank)
- [X] T004 [P] Implement `code/utils.py` with shared constants (read thresholds, abundance filters, age strata) and logging helpers. **Add Constant**: `MAX_BENCHMARK_SAMPLES = 1000` (int) for T036d.
- [X] T006 [P] Create base data loading functions in `code/utils.py` with retry logic (retry up to 3 times with exponential backoff, base=1s, max=30s) for API failures. **Note**: Parameters must be explicit to ensure deterministic behavior.
- [X] T007 [P] Configure `pytest`: Create `pytest.ini`, `tests/conftest.py`, and `tests/run_tests.sh` to enable test execution.
- [X] T012b [P] **Manual Prerequisite**: Create `data/auth/ukb_token.txt` with a placeholder token string (e.g., `PLACEHOLDER_TOKEN`) and document the process for obtaining a real token in `README.md`. **Note**: This task must be completed manually before T012 can run in an automated environment.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion, Preprocessing & Meta-Analysis Fallback (Priority: P1) 🎯 MVP

**Goal**: Download, filter, and normalize publicly available gut microbiome and cognitive flexibility data; detect data linkage gaps; execute FR-008 fallback (Data Gap Report) if linkage fails.

**Independent Test**: Execute ingestion scripts and verify output files contain expected sample counts, filtered taxa, z-scored cognitive scores, and verify proper logging. If linkage fails, verify the FR-008 Data Gap Report is generated.

### Implementation for User Story 1

- [X] T011 [US1] Implement `code/01_ingest.py` to fetch microbiome data. **Source Logic**: Use `requests` library to query Qiita Study ID 10313 via endpoint ` Name or service not known)"))]. Apply FR-001 filters (<10k reads, <0.1% abundance). Save raw parquet. **Execution**: Must include specific API call parameters and error handling for rate limits.
- [ ] T012 [US1] Implement code logic to fetch cognitive data from **UK Biobank** (Field 20002) or **NHANES** (Cognitive Function Battery variables) using `ukbiobank` package. **Authentication**: Use `ukbiobank` package with `--token-file` argument pointing to `data/auth/ukb_token.txt` (created in T012b). **Validation**: Script must check existence of `data/auth/ukb_token.txt` before execution. Save raw parquet. **Note**: If UKB token is not real, this step will fail; fallback to NHANES public data if configured.
- [X] T013 [US1] Implement `code/02_preprocess.py` to load cognitive data, handle missing values via MICE (per FR-002), compute z-scores, and save processed parquet.
- [ ] T014 [US1] Implement `code/02_preprocess.py` logic: 1) Attempt individual-level merge of microbiome and cognitive data; 2) If merge results in 0 rows, **immediately trigger the Fallback Workflow** and skip T015-T033. **Conditional Check**: Explicitly check `if len(merged_df) == 0: execute_fallback_workflow()`. **Output**: Generate `data/qc/fallback_trigger.log` with message "Data Linkage Failed: No common participant IDs found".
- [ ] T015 [US1] Implement `code/02_preprocess.py` logic to add robust outlier filtering (z-score > 3 on merged dataset) with logging to `data/qc/filtering_log.json`. **Output JSON schema**: `{ "total_samples": int, "removed_outliers": int, "threshold": float }`. **Verification**: Script must generate `data/qc/filtering_log.json` with correct schema after processing. **Dependency**: Only runs if T014 merge succeeds.
- [ ] T016 [US1] Add validation using `pandera` to ensure output parquet files match `contracts/dataset.schema.yaml`. **Fail hard on schema mismatch**.
- [X] T017b [US1] Implement `code/07_gap_report.py` to generate a **Data Gap Notification**. **Logic**: 1) Set `failure_reason` to "No common participant IDs found". 2) List `affected_studies`. 3) **Trigger T017d immediately**. **Note**: This task acts as a trigger, not the final fallback.
- [X] T017d [US1] Implement `code/08_meta_analysis.py` to execute the **FR-008 Data Gap Report**. **Logic**: 1) Attempt to fetch summary statistics from public metadata APIs (Qiita/NHANES) for the specific studies. 2) If no real summary statistics are available, generate a structured "Data Gap Report" stating "No individual-level linkage possible; no valid meta-analysis possible without synthetic linkage". 3) Output `data/processed/fr008_data_gap_report.json`. **Note**: This task explicitly satisfies FR-008 by reporting the gap rather than fabricating data.

### Tests for User Story 1 (OPTIONAL) ⚠️

- [X] T008a [US1] Unit test for data filtering logic in `tests/unit/test_filtering.py`
- [X] T009a [US1] Unit test for MICE imputation in `tests/unit/test_imputation.py`
- [X] T010a [US1] Integration test for data merge logic in `tests/integration/test_merge.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (or correctly report data gap results)

---

## Phase 4: User Story 2 - Correlation and Association Analysis (Priority: P2)

**Goal**: Compute Spearman correlations, apply FDR correction, and fit regularized regression models (only if data linked). **Strictly maintain 'associational only' framing.**

**Independent Test**: Run analysis on preprocessed data; verify correlation matrix, significant taxa list (q < 0.05), regression coefficients, and verify outputs.

**DEPENDS ON**: T014 (Merge Success). If T014 fails, skip this phase.

### Implementation for User Story 2

- [X] T021 [US2] Implement `code/03_correlation.py` to compute Spearman rank correlations between taxa and cognitive scores (FR-003). **Explicitly label outputs as 'associational'**. **Conditional**: Skip if `merged_dataset.parquet` missing.
- [X] T022 [US2] Implement `code/03_correlation.py` logic to apply Benjamini-Hochberg FDR correction and flag significant taxa (q < 0.05) (FR-004). **Conditional**: Skip if `merged_dataset.parquet` missing.
- [ ] T023 [US2] Implement `code/04_regression.py` to fit LASSO/Elastic Net models with **CLR-transformed microbial taxa** as predictors, age, sex, BMI (FR-005). **Verification Step**: Script must check for `data/processed/merged_dataset.parquet`; if missing, exit gracefully with code 0 and log "N/A - Data Gap" without attempting model fitting. **Explicitly label outputs as 'associational'**.
- [ ] T025 [US2] Ensure all outputs include explicit "associational" framing labels (FR-005).
- [ ] T026 [US2] Save correlation matrix and regression results to `data/processed/` with metadata.

### Tests for User Story 2 (OPTIONAL) ⚠️

- [X] T018 [US2] Unit test for Spearman correlation calculation in `tests/unit/test_correlation.py`
- [X] T019 [US2] Unit test for Benjamini-Hochberg FDR correction in `tests/unit/test_fdr.py`
- [X] T020 [US2] Unit test for LASSO/Elastic Net regression in `tests/unit/test_regression.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (or correctly report N/A due to data gap)

---

## Phase 5: User Story 3 - Sensitivity Analysis and Visualization (Priority: P3)

**Goal**: Stratify results by age, test normalization robustness, and generate visualizations. **Strictly maintain 'associational only' framing.**

**Independent Test**: Execute sensitivity scripts; verify stratified tables and plot files (heatmap, forest plot) are generated.

**DEPENDS ON**: T014 (Merge Success). If T014 fails, skip this phase.

### Implementation for User Story 3

- [ ] T029 [US3] Implement `code/05_sensitivity.py` to stratify correlations by age groups (<40, ≥40-<60, ≥60) (FR-006); Check for `data/processed/merged_dataset.parquet`; skip if missing.
- [ ] T030 [US3] Implement `code/05_sensitivity.py` to compare significant taxa counts across normalization methods (DESeq2 vs rarefaction); Check for `data/processed/merged_dataset.parquet`; skip if missing. <!-- FAILED: unspecified -->
- [ ] T031 [US3] Implement `code/06_visualize.py` to generate heatmap of taxa-cognition correlation matrix (FR-007); Check for `data/processed/merged_dataset.parquet`; skip if missing.
- [~] T032 [US3] Implement `code/06_visualize.py` to generate forest plot of regression coefficients with confidence intervals (FR-007); Check for `data/processed/merged_dataset.parquet`; skip if missing.
- [ ] T033 [US3] Ensure all visualizations include clear labels for age groups and confidence intervals.

**Checkpoint**: All user stories should now be independently functional (or correctly report N/A due to data gap)

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T034 [P] Documentation updates in `README.md` explaining the FR-008 fallback behavior and the strict 'associational only' framing.
- [X] T035 [P] Code cleanup and refactoring for CPU efficiency (memory chunking if needed)
- [X] T036a [P] **Performance Optimization**: Implement memory chunking in `code/03_correlation.py`. **Strategy**: Process data in fixed-size chunks. **Output**: Updated `code/03_correlation.py`.
- [X] T036b [US2] **Performance Benchmark**: Run the full analysis pipeline on a subset of N=10,000 samples (or the maximum feasible sample size) and measure total runtime. **Command**: `time python code/03_correlation.py`. **Output**: `data/qc/benchmark_results.json` containing `total_runtime_seconds` (float), `max_memory_mb` (float), `n_samples` (int), `status` (str: "pass" if < 6h, "fail" if >= 6h). **Verification**: Script must validate JSON schema and report "pass" if runtime < 21600 seconds. **Dependency**: **MUST run after T036a** to measure the optimized performance.
- [X] T036c [P] **Performance Documentation**: If runtime exceeds a significant duration, document the specific N-value used and the sampling strategy in `code/utils.py` and `reports/performance_report.md`. **Output**: Updated `code/utils.py` and `reports/performance_report.md`.
- [X] T036d [P] **Real Data Subset Benchmark**: Run the correlation/regression pipeline on a deterministic subset of the raw microbiome/cognitive files (using `MAX_BENCHMARK_SAMPLES` from `code/utils.py`) to measure performance when real data linkage fails. **Command**: `time python code/03_correlation.py --subset`. **Output**: `data/qc/benchmark_subset_results.json`. **Purpose**: Ensures SC-003 is measurable even if real data linkage fails, without using synthetic data.
- [X] T037 [P] Additional unit tests for edge cases (zero significant taxa, rate-limiting) in `tests/unit/`
- [X] T038 [P] Security hardening: Sanitize all external URLs and file paths
- [X] T039 [P] Run `quickstart.md` validation to ensure end-to-end reproducibility and verify that all outputs are explicitly labeled 'associational only' as per SC-005.

---

**Phase 8, 9 and User Story 4 have been removed from the tasks.md to align with the Plan’s constraints and resolve broken dependencies.**