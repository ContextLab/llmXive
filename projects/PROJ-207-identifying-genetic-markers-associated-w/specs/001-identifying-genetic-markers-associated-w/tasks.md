---
description: "Task list template for feature implementation"
---

# Tasks: Identifying Genetic Markers Associated with Honeybee Colony Collapse Disorder

**Input**: Design documents from `/specs/001-gene-regulation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
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

- [X] T001 Create project structure by executing: `mkdir -p code/ data/raw/ data/processed/ data/interim/ state/ docs/ tests/`
- [X] T003a [P] Create `code/pyproject.toml` with ruff and black configuration sections
- [X] T003b [P] Initialize pre-commit hooks by creating `.pre-commit-config.yaml` with ruff and black hooks
- [X] T002 [P] Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt`. Content MUST be:
```
plink2
freebayes
bwa
scikit-learn
pandas
numpy
statsmodels
dwgsim
pyyaml
requests
```

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create data directory structure with immutable raw data constraints (mkdir -p data/raw, data/processed, data/interim)
- [X] T039 [P] Implement `code/utils/checksum_verify.py` to verify checksums of raw data files against recorded hashes
- [X] T040 [P] Create `docs/data_policy.md` defining the 'immutable' constraint for raw data
- [X] T005 [P] Implement `code/utils/power_analysis.py` for FR-012. MUST:
 1. Calculate power using non-central chi-squared distribution.
 2. If n < 80: HALT with error code `ERR_SAMPLE_SIZE_INSUFFICIENT`.
 3. If n >= 80 AND Power < 0.20: HALT with error code `ERR_POWER_INSUFFICIENT` and report the calculated power.
 4. If n >= 80 AND Power >= 0.20: Report the calculated power in `data/processed/power_analysis.txt` as a single line: "Power: X.XX".
- [X] T006 [P] Implement `code/utils/collinearity_diag.py` for FR-010 (VIF calculation, correlation matrix)
- [X] T007 [P] Create base data schema validators for `Colony` and `SNP` entities: create `code/utils/validators/colony_schema.py` and `code/utils/validators/snp_schema.py` based on `specs/001-gene-regulation/contracts/dataset.schema.yaml` and `specs/001-gene-regulation/contracts/gwas_output.schema.yaml`
- [X] T008 [P] Create `.env.example` with keys `NCBI_API_KEY`, `ENSEMBL_API_KEY` and default values for SSL CA bundle paths
- [X] T009 [P] Implement `code/00_generate_synthetic_data.py` to create deterministic synthetic VCF + Phenotypes for validation. MUST implement CCD diagnosis validation logic that explicitly checks: <!-- FAILED: unspecified -->
 1. Presence of dead adult bees in the hive.
 2. Absence of dead pupae.
 3. Live bee population < 10% relative to peak season.
 Logic MUST fail validation if any of these criteria are not met in the synthetic data generation process (FR-011).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - GWAS Pipeline Execution (Priority: P1) 🎯 MVP

**Goal**: Execute the complete GWAS analysis pipeline on honeybee genomic data (real or synthetic) to identify SNPs associated with CCD susceptibility.

**Independent Test**: Can be fully tested by running the pipeline on the synthetic dataset and verifying that SNP association statistics are produced with correct schema.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: These tests ensure the pipeline handles data ingestion, alignment, and variant calling correctly.

- [X] T010 [P] [US1] Contract test for VCF schema validation in `tests/contract/test_vcf_schema.py`
- [X] T011 [P] [US1] Integration test for full synthetic pipeline run in `tests/integration/test_synthetic_gwas.py`

### Implementation for User Story 1

- [X] T012a [US1] Implement `code/01_download.py` to fetch data from NCBI BioProject PRJNA with SSL verification (FR-001).
 - **Primary Strategy**: The system MUST attempt to fetch real data from NCBI BioProject using `requests` with SSL verification.
 - **Implementation**:
 1. **Default Action**: Attempt to fetch real data from NCBI BioProject using `requests` with SSL verification.
 2. **On Success**: If fetch succeeds and data is valid, verify checksums, write `artifact_hash` to `state/verified_sources.yaml`, and proceed to T014.
 3. **On Failure** (SSL error, network error, missing file): HALT with error code `ERR_DATA_FETCH_FAILED` and a clear error message indicating the certificate validation failure or fetch failure. **DO NOT** continue with synthetic data unless `USE_SYNTHETIC_DATA=true` is explicitly set in the environment.
 4. **Optional Synthetic Mode**: If `USE_SYNTHETIC_DATA=true` is set, invoke the synthetic data generator (`code/00_generate_synthetic_data.py` from T009) to generate the baseline dataset. Log this as the synthetic mode execution. Do NOT write to `state/verified_sources.yaml` in this mode.
 - **Verification**: Simulate a network failure and verify the script halts with a clear error message. Simulate `USE_SYNTHETIC_DATA=true` and verify the script uses the synthetic dataset.
 - **Note**: The Plan's "Synthetic Validation Strategy" is now an optional mode triggered by environment variable, not the default.
- [X] T053 [P] [Review Fix] Update `code/01_download.py` to align with T012a's strict halt requirement.
 - **Implementation**:
 - **Mandatory**: The primary path is real data fetch. If the real data fetch fails for any reason (network, SSL, missing file), the script MUST raise an exception and halt the pipeline unless `USE_SYNTHETIC_DATA=true` is set.
 - **Mandatory**: If `USE_SYNTHETIC_DATA=true` is set, the script MUST invoke the synthetic data generator and proceed.
 - **Verification**: Simulate a real fetch failure without the env var and verify the system halts. Simulate with the env var and verify the system proceeds with synthetic data.
 - **Depends on**: T012a.
- [X] T013 [US1] Implement `code/00_generate_simulated_fastq.py` to simulate FASTQ to enable FR-002.
 - **Input**: `data/interim/synthetic.vcf` (generated by T009).
 - **Output**: `data/interim/synthetic_R1.fastq` and `data/interim/synthetic_R2.fastq`.
 - **Implementation**: Install dwgsim via conda-forge: `conda install -c bioconda dwgsim`. Use `dwgsim` with a fixed random seed to ensure reproducibility. Command: `dwgsim -e 0.02 -d 500 -s SEED -N 1000000 data/interim/synthetic.vcf data/interim/synthetic`.
 - **Verification**: Ensure output files exist and contain valid FASTQ format.
 - **Depends on**: T009.
- [X] T014 [US1] Create `code/02_align_call.sh` to wrap `bwa mem` (alignment) and `FreeBayes` (variant calling) with QUAL > 30 and depth ≥ 10 filters (FR-002). MUST accept input from either `data/interim/real_*.fastq` (T012a) or `data/interim/synthetic_*.fastq` (T013).
 - **Implementation**: Ensure bwa and freebayes are installed via conda-forge (`conda install -c bioconda bwa freebayes`) and available in PATH before execution.
- [X] T015 [US1] Implement VCF to PLINK format conversion in `code/utils/vcf_to_plink.py` (FR-003)
- [X] T016 [US1] Implement `code/utils/preprocess_phenotype.py` for LD pruning (r² < 0.2) and covariate encoding (geographic region, sampling year, Varroa load) (FR-003). <!-- FAILED: unspecified -->
 - **Input**: Phenotype data from T009 (synthetic) or T012a (real).
 - **Output**: `data/processed/phenotypes_cleaned.fam` and `data/processed/phenotypes_cleaned.pheno`.
 - **MANDATORY**: MUST include geographic region, sampling year, and Varroa mite count in the model (unless PCA is triggered by T046, which is now a halt condition).
 - **MANDATORY**: Do NOT perform VIF calculation or PCA here; this task only prepares the data.
 - **Depends on**: T009, T012a.
- [X] T043 [US1] Implement `code/04_check_power_and_halt.sh` to execute `code/utils/power_analysis.py` (T005) immediately after data loading and preprocessing.
 - **Logic**: Run `code/utils/power_analysis.py`.
 - **Mandatory Behavior**: If `n < 80` or `Power < 0.20`, halt the pipeline with the respective error code (`ERR_SAMPLE_SIZE_INSUFFICIENT` or `ERR_POWER_INSUFFICIENT`) BEFORE any GWAS execution (T017) runs.
 - **Depends on**: T009, T012a, T016.
- [X] T054 [P] [Review Fix] Implement `code/11_verify_real_data_source.py` to enforce the "VERIFIED REAL DATA SOURCE" rule and define the schema.
 - **Schema Definition**: The task MUST define and enforce the schema for `state/verified_sources.yaml`:
 ```yaml
 package_name: "<string>"
 access_recipe: "<string>"
 artifact_hash: "<string>"
 source_url: "<string>"
 ```
 - **Logic**: Scan `data/processed/` and `state/` for a "VERIFIED REAL DATA SOURCE" block (package name + access recipe).
 - **Constraint**: If such a block exists, `code/01_download.py` (T012a) and `code/10_real_data_streaming.py` (T052) MUST adopt this exact package/recipe as the **single** source of input.
 - **Constraint**: If a verified source exists, the system MUST NOT attempt to use hand-rolled `load_dataset("<guessed-id>")`, guessed raw URLs, or invented mirrors.
 - **Constraint**: If `USE_SYNTHETIC_DATA=true` is set, skip verification and log synthetic mode.
 - **Verification**: Ensure that when a verified source is injected, the pipeline uses it exclusively and ignores other fetch attempts.
 - **Depends on**: T012a, T052.
- [X] T046 [US1] [Foundational Logic Moved to US1] Implement `code/08_collinearity_guard.py` to enforce the collinearity handling strategy (FR-003, Constitution Check VII).
 - **Implementation**:
 - Input: Read `data/processed/phenotypes_cleaned.fam` (Output of T016).
 - Logic: Calculate VIF using `code/utils/collinearity_diag.py` (T006).
 - **Condition**: If VIF **>= 5** (inclusive boundary):
 - Log "High collinearity detected (VIF >= 5). HALTING pipeline per Spec FR-010. Results without specific covariates are invalid."
 - **Output**: HALT the pipeline with error code `ERR_COLLINEARITY_HIGH`. Do NOT generate `model_config.yaml`.
 - **Condition**: If VIF < 5:
 - Log "Collinearity check passed."
 - **Output**: Generate `data/processed/model_config.yaml` containing:
 - `strategy: "Covariates"`
 - `covariate_columns: ["geographic_region", "sampling_year", "Varroa_mite_count"]`
 - `pc_columns: []`
 - **Verification**: Ensure the script exits with code 0 and the `model_config.yaml` file exists and is readable when VIF < 5. Ensure the script halts with `ERR_COLLINEARITY_HIGH` when VIF >= 5.
 - **Depends on**: T006, T016.
- [ ] T017 [US1] Create `code/03_gwas.sh` to execute PLINK logistic regression with covariates (or PCs from T046) and output raw association statistics (FR-004). Do NOT include FDR logic here; that is handled by T022. Output to `data/interim/gwas_raw.tsv`.
 - **Implementation**:
 1. **Required Artifacts**: `data/processed/model_config.yaml` (Output of T046), `data/processed/phenotypes_cleaned.fam` (Output of T016).
 2. **Execution Gates**: T043 (Power Analysis) MUST pass (exit code 0) before this task executes. T046 (Collinearity Guard) MUST pass (exit code 0) before this task executes.
 3. Read `data/processed/model_config.yaml`.
 4. If `strategy` is "PCA": Extract `pc_columns` and pass them to PLINK `--covar` (using the PCA file from T046).
 5. If `strategy` is "Covariates": Extract `covariate_columns` and pass them to PLINK `--covar` (using the phenotype file from T016).
 6. Run PLINK2 `--logistic` with the determined covariates.
 7. **Output**: Write results to `data/interim/gwas_raw.tsv`. **MUST** ensure this file is created with columns: `SNP`, `CHR`, `POS`, `P`, `Odds_Ratio`, `SE`.
 - **Verification**: Verify `data/interim/gwas_raw.tsv` exists and contains the required columns.
 - **Depends on**: T016 (Artifact), T043 (Gate), T046 (Gate).
- [ ] T022 [US1] Create `code/04_apply_fdr.sh` to post-process `data/interim/gwas_raw.tsv` using T020. Pipe PLINK output to `code/utils/fdr_correction.py` and write final results to `data/processed/gwas_results_fdr.tsv` (FR-004, FR-005).
 - **Verification**: Verify `data/processed/gwas_results_fdr.tsv` exists and contains the `q_value` column.
 - **Depends on**: T017.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Multiple Testing Correction & Threshold Sensitivity (Priority: P2)

**Goal**: Apply Benjamini-Hochberg FDR correction and test threshold sensitivity to identify robust genetic associations.

**Independent Test**: Can be tested independently by running the correction on the GWAS output and verifying q-values and threshold counts.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for Benjamini-Hochberg implementation in `tests/unit/test_fdr_correction.py`
- [X] T019 [P] [US2] Contract test for threshold sensitivity output format in `tests/contract/test_threshold_sensitivity.py`

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement Benjamini-Hochberg FDR correction in `code/utils/fdr_correction.py` (FR-004).
 - **MANDATORY**: MUST implement BH correction as required by Spec FR-004.
 - Output: q-values for all SNPs.
- [X] T021 [US2] Implement threshold sensitivity sweep across a range of specific thresholds. in `code/utils/threshold_sensitivity.py` (FR-005).
 - **Implementation**: Explicitly sweep the thresholds across a range of low-magnitude values.
 - **MANDATORY**: MUST apply Benjamini-Hochberg (BH) correction as required by Spec FR-004 and FR-005.
 - **Note**: The Plan's 'Complexity Tracking' section suggests Bonferroni on Me, but the Spec FR-004/FR-005 explicitly mandates BH. This task implements the Spec requirement. The Plan's mention of Bonferroni is flagged as a conflict requiring plan revision.
 - **Output**: Write a report to `data/processed/threshold_sensitivity_report.tsv` containing columns: `threshold`, `snp_count`, `min_q_value`, `significant_count`.
 - **Depends on**: T020.
- [X] T023 [US2] Update `code/04_apply_fdr.sh` to flag SNPs with q < 0.05 as significant and document the study design.
 - **MANDATORY**: MUST create `data/processed/gwas_results_metadata.json` containing:
 - `disclaimer`: "Findings are associational, not causal. This is an observational study without randomization."
 - `correction_method`: "Benjamini-Hochberg FDR"
 - `impact`: "Number of SNPs passing q < 0.05"
 - **MANDATORY**: Do NOT inject the disclaimer into the TSV header. The TSV must remain a clean data file.
 - **MANDATORY**: Document the correction method used (BH) and its impact on discovery rate.
 - **Depends on**: T022.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Machine Learning Validation & Polygenic Risk Scoring (Priority: P3)

**Goal**: Validate GWAS findings using LASSO logistic regression and compute polygenic risk scores to assess predictive performance.

**Independent Test**: Can be tested by running LASSO on a held-out test set (or synthetic equivalent) and verifying AUC is computed correctly.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US3] Unit test for LASSO AUC calculation in `tests/unit/test_lasso_auc.py`
- [X] T026 [US3] Implement `tests/integration/test_prs_validation.py` to verify FR-007.
 - **Implementation**:
 - Import `statsmodels.stats.diagnostic` for likelihood-ratio test.
 - Load PRS and covariates from `data/processed/gwas_results_fdr.tsv` (T022) and `data/processed/phenotypes_cleaned.fam` (T016).
 - Fit full model (PRS + covariates) and reduced model (covariates only).
 - Perform likelihood-ratio test.
 - **Verification**: Assert that the test runs successfully and the p-value is reported in the output artifact `data/processed/prs_validation_results.json`.
 - **Note**: Do NOT assert that p-value < 0.05. The test verifies the *method* works, not the *outcome* of the specific dataset.
 - Assert output matches schema in `contracts/gwas_output.schema.yaml`.
 - **Verification**: Ensure the test file exists and runs successfully with `pytest`.
 - **Depends on**: T016, T022, T027, T028, T029, T030, T031.
 - **Note**: This test is written first (Test First methodology) and depends on the Spec, not the implementation tasks. The implementation tasks T027-T031 will be written to make this test pass.

### Implementation for User Story 3

- [X] T027 [P] [US3] Implement LASSO logistic regression with k-fold cross-validation. in `code/04_ml_validation.py` (FR-006) and report out-of-sample AUC value <!-- FAILED: unspecified -->
- [X] T028 [US3] Implement Polygenic Risk Score (PRS) calculation in `code/04_ml_validation.py` (FR-007)
- [ ] T029 [US3] Implement likelihood-ratio test for PRS improvement over covariates-only model in `code/04_ml_validation.py` (FR-007)
- [ ] T030 [US3] Add AUC threshold logic in `code/04_ml_validation.py`:
 - Generate null distribution via 1000 phenotype permutations (seed=42).
 - Compare AUC against a high quantile of the null distribution.
 - **MANDATORY**: Use random seed 42 for the 1000 permutations to ensure reproducible null distribution generation.
 - **MANDATORY**: Report the AUC value and the comparison result.
 - **MANDATORY**: If AUC < 0.75, the system MUST **report** the result as "low predictive power" in the output artifact. This is a **reporting flag** for biological interpretation, NOT a pipeline failure condition. The pipeline must continue successfully regardless of the AUC value.
 - **Depends on**: T027, T028, T029.
- [ ] T031 [US3] Implement collinearity diagnostics (VIF) for covariates (geographic region, sampling year) in `code/04_ml_validation.py` (FR-010, US-3 AC4).
 - **MANDATORY**: MUST implement VIF calculation and flag relationships where r² > 0.8 in the output artifact `data/processed/collinearity_report.tsv`.
 - **MANDATORY**: Document findings descriptively, framing joint relationships as such rather than independent effects.
- [ ] T032 [US3] Implement `code/05_annotation.py` to map significant SNPs to genes using Ensembl Bees API and query GO terms (FR-008).
 - **MANDATORY**: Output `data/processed/annotated_snps.tsv` with columns: rs_id, gene_symbol, go_terms, pathway.
 - **Implementation**: Use ` API. Implement retry logic on failure. If all attempts fail, log error and exit with code 1.
 - **Verification**: Verify `data/processed/annotated_snps.tsv` exists and contains at least 10 rows with non-null `go_terms` (for synthetic data with known annotations).
 - **Depends on**: T022.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T033a [P] Create `docs/pipeline_execution_guide.md` with step-by-step execution instructions
- [X] T033b [P] Create `docs/data_dictionary.md` defining all data artifacts and schemas
- [X] T034 [P] Code cleanup and refactoring of shell scripts for portability (Depends on T014, T017, T022).
 - **Implementation**: Run `shellcheck` on all `.sh` files. Refactor any warnings.
 - **Output**: `data/processed/shellcheck_report.txt`.
- [X] T041 [P] Profile pipeline with `cProfile` and generate `data/processed/profile_report.txt`.
 - **Implementation**: Run `python -m cProfile -o data/processed/profile.prof code/03_gwas.py` (invoking the Python logic directly, not the shell script). Use `pstats` to generate `data/processed/profile_report.txt`.
 - **Output**: `data/processed/profile_report.txt`.
 - **Note**: Ensure the target `code/03_gwas.py` exists and is executable before profiling.
- [X] T042 [P] Refactor `code/02_align_call.sh` to use parallel processing if profile shows I/O bottleneck (Depends on T041).
 - **Implementation**: Read `data/processed/profile_report.txt`. If I/O bottleneck detected, add `parallel` or `xargs` to the alignment step.
 - **Output**: Updated `code/02_align_call.sh`.
 - **Depends on**: T041.
- [X] T036 [P] Additional unit tests for edge cases (missing Varroa data, all SNPs filtered) in `tests/unit/`.
 - **Implementation**: Create `tests/unit/test_missing_varroa.py` and `tests/unit/test_all_snps_filtered.py`.
 - **Output**: Test files and `data/processed/edge_case_test_results.txt`.
- [X] T037 [P] Run quickstart.md validation to ensure reproducibility.
 - **Implementation**: Execute `docs/quickstart.md` steps in a fresh environment. Capture logs.
 - **Output**: `data/processed/quickstart_validation_log.txt`.
- [X] T038 [P] Create `docs/report_template.md` to include the mandatory disclaimer text: "Findings are associational, not causal..." (FR-009)
- [X] T044 [P] Implement `code/06_edge_case_handler.py` to explicitly handle missing Varroa metadata (Assumption 1):
 - Read metadata from T009/T012a.
 - **Mandatory**: If < 80% of the total cohort has Varroa data (i.e., > 20% missing), raise `ERR_VARROA_COVARIATE_MISSING` and halt.
 - **Mandatory**: If missing for ≤ 20%, exclude those samples from the covariate model but retain for genotype-only analysis.
 - Log all exclusions to `data/processed/exclusion_log.txt`.
- [X] T047 [P] [Polish] Implement `code/07_runbook_generator.py` to generate a deterministic execution runbook for GitHub Actions (FR-004, US-1 AC3).
 - **Implementation**:
 - Assume Ubuntu 22.04 runner.
 - Read `code/requirements.txt` and `code/00_generate_simulated_fastq.py` (T013).
 - Generate a single bash script `runbook.sh` that:
 1. Installs dependencies (Include `apt-get install` or `conda install` commands for bwa, freebayes, plink2).
 2. Generates synthetic data (T009) OR fetches real data (T012a) based on `USE_SYNTHETIC_DATA` env var.
 3. Generates FASTQ (T013).
 4. Runs alignment/calling (T014).
 5. Converts to PLINK (T015).
 6. Runs power analysis (T043) and halts if needed.
 7. Runs GWAS (T017).
 8. Applies FDR (T022).
 9. Runs ML validation (T027-T031).
 10. Runs annotation (T032).
 - Include explicit `set -e` and timeout checks to ensure compliance with the specified time limit.
 - **Output**: `runbook.sh` and `docs/runbook_validation.md`.
 - **Depends on**: T009, T013, T014, T017, T022, T027, T028, T029, T030, T031.
 - **Note**: T047 is no longer marked [P] as it depends on all US1-US3 tasks.
- [X] T048 [P] [Polish] Implement `tests/unit/test_runbook_idempotency.py` to verify the runbook produces identical results on re-run (Constitution Principle I).
 - **Implementation**:
 - Execute `runbook.sh` twice in isolated directories.
 - Compare checksums of all output artifacts in `data/processed/`.
 - Assert all checksums match.
 - **Output**: `data/processed/idempotency_report.txt`.
- [X] T049 [P] [Review Fix] Implement `code/09_data_streaming_loader.py` to replace any direct full-load logic with `datasets.load_dataset(..., streaming=True)` for NCBI/BioProject sources, ensuring chunked processing to respect ~7GB RAM limits while using real data (Spec Rule: "Large real datasets: STREAM the real data").
 - **Implementation**: Replace any `load_dataset` calls without `streaming=True` in `code/01_download.py` and `code/10_real_data_streaming.py`. Implement an iterator that accumulates statistics online without holding the full dataset in memory.
 - **Verification**: Ensure the pipeline runs successfully with a sample subset via streaming and logs the streaming chunk size.
 - **Depends on**: T012a.
- [ ] T051 [P] [Review Fix] Update `code/03_gwas.sh` and `code/04_ml_validation.py` to explicitly document the sample size (N) and the specific streaming/sampling rule used (e.g., "First [deferred] rows of streamed dataset" or "Full dataset processed in 1MB chunks") in their output headers (Spec Rule: "State the exact streaming/sampling rule... in the task").
 - **Implementation**: Modify the header generation in output files to include a metadata line: `# Sample_Rule: <description>`.
 - **Verification**: Check that `data/processed/gwas_results_fdr.tsv` and `data/processed/ml_validation_report.json` contain the `Sample_Rule` metadata line.
 - **Depends on**: T017, T027.
- [X] T052 [P] [Review Fix] Implement `code/10_real_data_streaming.py` to handle the specific case of streaming the full NCBI BioProject dataset if real data is successfully fetched in T012a.
 - **Implementation**:
 - **Input**: Real data paths from T012a (if successful).
 - **Logic**: Do NOT load the entire dataset into memory. Use `datasets.load_dataset` with `streaming=True` or `itertools.islice` on the downloaded file shards to process data in chunks (e.g., [deferred] rows at a time).
 - **Mandatory Validation**: Before processing, validate the **first streamed chunk** against `specs/001-gene-regulation/contracts/dataset.schema.yaml`. Explicitly check for the presence of columns: `Varroa_mite_count`, `geographic_region`, `sampling_year`. If any are missing, log an error and halt.
 - **Constraint**: Ensure the streaming logic accumulates necessary statistics (counts, allele frequencies) online without storing the full dataframe.
 - **Fallback**: If the dataset is too large to stream within the 6-hour limit even with chunking, explicitly log the limitation and switch to a deterministic sample (e.g., first [deferred] rows) with a clear `Sample_Rule` header in outputs.
 - **Verification**: Confirm that the script processes real data without memory errors on the free-tier runner.
 - **Depends on**: T012a, T054.
- [X] T055 [P] [Review Fix] Implement `code/12_no_synthetic_fallback.py` to enforce the "Loud Failure" rule for real data fetches.
 - **Implementation**:
 - **Logic**: Review `code/01_download.py` and `code/10_real_data_streaming.py` for any `try/except` blocks or conditional logic that falls back to `generate_synthetic_*()` or `mock_*()` when a real fetch fails.
 - **Constraint**: Remove any such fallback logic. A failed real fetch MUST raise an exception and let the run fail (if real data is required) or explicitly log the failure and proceed ONLY with the synthetic default (if synthetic is the primary path as per T012a with `USE_SYNTHETIC_DATA=true`).
 - **Constraint**: Ensure no `if download_failed: return synthetic_data()` logic exists.
 - **Verification**: Simulate a real fetch failure and verify the system either fails loudly (if real data is mandatory) or proceeds with the synthetic default without silently substituting data.
 - **Depends on**: T012a, T053.
- [X] T056 [P] [Review Fix] Add explicit task to verify "Real Data + Real Results" in `tests/integration/test_real_data_integrity.py`.
 - **Implementation**:
 - **Logic**: Create a test that attempts to run the pipeline with a real dataset if `REAL_DATA_PATH` env var is set OR if `data/raw/real_data_manifest.json` exists.
 - **Constraint**: Ensure no task generates/synthesizes fake INPUT data or hard-codes placeholder datasets for analysis steps.
 - **Verification**: Assert that the pipeline output contains a `Sample_Rule` header and that the data checksums match the real source (if real data was used) by comparing against the `artifact_hash` key in `state/verified_sources.yaml`.
 - **Depends on**: T012a, T027, T052.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (GWAS results)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 output (GWAS results) and US2 (FDR correction)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for VCF schema validation in tests/contract/test_vcf_schema.py"
Task: "Integration test for full synthetic pipeline run in tests/integration/test_synthetic_gwas.py"

# Launch all models for User Story 1 together:
Task: "Implement code/01_download.py to fetch data from NCBI BioProject"
Task: "Implement code/00_generate_simulated_fastq.py to generate simulated FASTQ"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently on synthetic data
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Revision**: Tasks T049-T053 address feedback regarding data streaming, loud failure on real data fetch, and explicit sampling documentation to prevent fabrication and ensure resource compliance.
- **Correction**: T046 now correctly implements the HALT strategy for high collinearity as per Spec FR-010. T005 now enforces the halt on low power. T012a strictly defaults to real data fetch and halts on failure (unless `USE_SYNTHETIC_DATA=true`). T030 re-implements the AUC flagging with the 0.75 threshold. T052 ensures real large datasets are streamed, not shrunk to toys. T053 removes any synthetic fallback logic in favor of strict halt.
- **Updated**: T012a and T053 now implement the strict halt requirement mandated by Spec FR-001. T046 uses >= 5 threshold and halts. T023 creates a separate metadata file. T041 profiles the correct Python script. T052 explicitly validates required columns.
- **New**: Tasks T054-T056 enforce the "Verified Real Data Source" rule, "Loud Failure" on real fetches, and "Real Data + Real Results" integrity to prevent fabrication and ensure compliance with execution gate rules.
- **Note**: The Plan's 'Synthetic Validation Strategy' is now an optional mode triggered by `USE_SYNTHETIC_DATA=true`, not the default. The Plan's 'Complexity Tracking' section regarding Bonferroni vs BH and 'Constitution Check VII' regarding PCA fallback are flagged as conflicts requiring plan revision to align with the Spec and Tasks.
