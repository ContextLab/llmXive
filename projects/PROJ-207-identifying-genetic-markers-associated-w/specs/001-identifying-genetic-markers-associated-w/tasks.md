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

**Note on Spec vs Plan Conflict**: The Spec (FR-004, FR-005) mandates Benjamini-Hochberg (BH) FDR correction. The Plan's "Complexity Tracking" section argues for Bonferroni. As per the Constitution, the Spec is the governing requirement for implementation. Tasks T020-T023 implement BH as required by the Spec. The Plan is flagged for revision to align with the Spec.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure by executing: `mkdir -p code/ data/raw/ data/processed/ data/interim/ state/ docs/ tests/`
- [X] T003a [P] Create `code/pyproject.toml` with ruff and black configuration sections
- [X] T003b [P] Initialize pre-commit hooks by creating `.pre-commit-config.yaml` with ruff and black hooks
- [X] T002 [P] Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt`. Content MUST be:
```
plink2
freebayes
scikit-learn
pandas
numpy
statsmodels
pyyaml
requests
biopython
```
**Note**: `dwgsim` is a system binary, not a Python package. It must be installed via conda/bioconda, not pip. Do NOT include it in requirements.txt.

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
 3. If n >= 80: Calculate power.
 4. **CRITICAL**: If Power < 0.20: REPORT the power value but DO NOT HALT. The Spec requires reporting power if n >= 80 regardless of the value.
 5. If Power >= 0.20: Report the calculated power for detecting large effect sizes (OR >= 2.5) at alpha=0.05.
 6. Output: Write power value and status to `data/processed/power_analysis.txt`.
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

- [X] T010 [P] [US1] Contract test for VCF schema validation in `tests/contract/test_vcf_schema.py`
- [X] T011 [P] [US1] Integration test for full synthetic pipeline run in `tests/integration/test_synthetic_gwas.py`

### Implementation for User Story 1

- [X] T012a [US1] Implement `code/01_download.py` to fetch data from NCBI BioProject PRJNA with SSL verification (FR-001).
 - **Primary Strategy**: The system MUST attempt to fetch real data from NCBI BioProject using `requests` with SSL verification.
 - **Implementation**:
 1. **Default Action**: Attempt to fetch real data from NCBI BioProject using `requests` with SSL verification.
 2. **On SSL Error**: If SSL verification fails, the system MUST HALT with a clear error message indicating the certificate validation failure. Do NOT proceed. (Compliance with FR-001).
 3. **On Missing File (404/403) or Network Error**: If the fetch fails:
 - **MUST HALT** with error code `ERR_DATA_FETCH_FAILED` and a clear message: "Real data fetch failed. No synthetic fallback authorized for primary research pipeline. Set USE_SYNTHETIC_DATA=true ONLY for validation tasks (T009)."
 - **DO NOT** trigger synthetic data generation.
 4. **On Success**: If fetch succeeds and data is valid, verify checksums, write `artifact_hash` to `state/verified_sources.yaml`, and proceed to T012b.
 5. **Large Dataset Handling**:
 - If the real dataset size > 14GB (estimated), implement streaming logic using `datasets.load_dataset(..., streaming=True)`.
 - Process data in chunks (e.g., manageable batch sizes) to compute statistics without loading the full dataset into memory.
 - If streaming is not supported by the specific source, implement a "Fixed-Seed Sample" strategy: Use `itertools.islice` to take the first N rows (e.g., N=5000) or a random sample with a fixed seed. Explicitly log: "Dataset too large for full processing. Using fixed-seed sample of N rows. Limitations documented in `data/processed/sampling_methodology.md`."
 - **MUST NOT** use random noise or synthetic generation as a fallback for large datasets.
 6. **Output Artifacts**:
 - `data/raw/ncbi_metadata.json`: A JSON file containing:
 - `total_samples`: integer
 - `samples_with_varroa`: integer
 - `fetch_status`: "success"
 - `checksum`: string
 - `data/raw/real_data.vcf`: The downloaded VCF file.
 - **Depends on**: None.
- [X] T012b [P] [US1] Implement `code/01_varroa_check.py` to validate Varroa data coverage (FR-001, Assumption 1).
 - **Input**: `data/raw/ncbi_metadata.json` (Output of T012a).
 - **Logic**:
 1. Read `ncbi_metadata.json`.
 2. If `samples_with_varroa` / `total_samples` < 0.80:
 - Raise `ERR_VARROA_COVARIATE_MISSING` and HALT with message: "Varroa data coverage < 80% ({samples_with_varroa}/{total_samples}). Pipeline halted."
 3. If >= 0.80: Log "Varroa Data Coverage: {samples_with_varroa}/{total_samples} ({percent}%)." and proceed.
 - **Output**: `data/processed/varroa_coverage_log.txt`.
 - **Depends on**: T012a.
- [X] T013a [P] [US1] [Setup] Install `dwgsim` in the environment.
 - **Implementation**: Add `dwgsim` to `code/environment.yml` or create a `setup.sh` script that runs: `conda config --add channels bioconda && conda install -c bioconda dwgsim`.
 - **Note**: `dwgsim` is a system binary, not a Python package.
- [X] T013b [P] [US1] [Setup] Verify `dwgsim` availability.
 - **Implementation**: Run `dwgsim --help` and verify it exits with code 0.
 - **Depends on**: T013a.
- [X] T013c [US1] Implement `code/00_generate_simulated_fastq.py` to simulate FASTQ for *validation/testing* of the alignment pipeline (FR-002).
 - **Input**: `data/interim/synthetic.vcf` (generated by T009).
 - **Output**: `data/interim/synthetic_R1.fq` and `data/interim/synthetic_R2.fq`.
 - **Implementation**:
 1. Ensure `dwgsim` is installed (T013a, T013b).
 2. Use `dwgsim` with a fixed random seed (SEED=42) to ensure reproducibility. Command: `dwgsim -e -d [variable_insertion_distance] -s 42 -N [large_sample_size] data/interim/synthetic.vcf data/interim/synthetic`.
 3. **Output Verification**: Ensure output files exist and contain valid FASTQ format. If `dwgsim` outputs files with different names (e.g., `synthetic_R1.fq`), rename them to `synthetic_R1.fq` and `synthetic_R2.fq` to match the expected output.
 4. This task is the explicit fallback path triggered ONLY if T012a fails and `USE_SYNTHETIC_DATA=true` is set (for validation purposes only).
 5. **Depends on**: T009, T013a, T013b. (Triggered by T012a failure if `USE_SYNTHETIC_DATA=true`).
- [X] T013d [P] [US1] [Verification] Verify `code/00_generate_simulated_fastq.py` output.
 - **Implementation**: Run `fastqc` or simple validation on `data/interim/synthetic_R1.fq` and `data/interim/synthetic_R2.fq` to ensure valid FASTQ format.
 - **Depends on**: T013c.
- [X] T043 [P] [US1] [Gate] Implement `code/04_check_power_and_halt.sh` to execute `code/utils/power_analysis.py` (T005) immediately after data loading.
 - **Logic**: Run `code/utils/power_analysis.py`.
 - **Mandatory Behavior**: If `n < 80`, halt the pipeline with error code `ERR_SAMPLE_SIZE_INSUFFICIENT` BEFORE any preprocessing (T016) or GWAS execution (T017) runs. If `n >= 80`, report the power value and proceed regardless of the power value (do NOT halt on low power).
 - **Input**: `data/raw/ncbi_metadata.json` (if real) or `data/interim/synthetic.vcf` (if synthetic).
 - **Output**: `data/processed/power_analysis.txt`.
 - **Depends on**: T012a (primary), T013c (conditional if T012a fails).
- [X] T015 [US1] Implement VCF to PLINK format conversion in `code/utils/vcf_to_plink.py` (FR-003)
- [X] T016 [US1] Implement `code/utils/preprocess_phenotype.py` for LD pruning (r² < 0.2) and covariate encoding (geographic region, sampling year, Varroa mite count) (FR-003).
 - **Input**: Phenotype data from T009 (synthetic) or T012a (real).
 - **Output**: `data/processed/phenotypes_cleaned.fam` and `data/processed/phenotypes_cleaned.pheno`.
 - **MANDATORY**: MUST include geographic region, sampling year, and Varroa mite count in the model.
 - **MANDATORY**: (Wikidata Q48989513, https://www.wikidata.org/wiki/Q48989513)
 - **Implementation**:
 1. Run PLINK `--indep-pairwise <window_size> 0.2` on the genotype data to generate the prune list.
 2. Run PLINK `--extract` with the prune list to generate the pruned dataset.
 3. Encode covariates (geographic_region, sampling_year, Varroa_mite_count) into the `.pheno` file.
 - **Verification**:
 - Verify `data/processed/phenotypes_cleaned.fam` exists.
 - Verify `data/processed/phenotypes_cleaned.pheno` contains the required set of covariate columns (geographic_region, sampling_year, Varroa_mite_count).
 - Verify that the pruned genotype file exists.
 - **Depends on**: T009, T012a, T015, T043.
- [X] T046 [US1] [Foundational Logic Moved to US1] Implement `code/08_collinearity_guard.py` to perform collinearity diagnostics (FR-003, FR-010).
 - **Implementation**:
 - Input: Read `data/processed/phenotypes_cleaned.fam` (Output of T016).
 - Logic: Calculate VIF using `code/utils/collinearity_diag.py` (T006).
 - **Condition**: If VIF >= 5 (inclusive boundary):
 - Log "High collinearity detected (VIF >= 5). Documenting as per Spec FR-010."
 - Identify specific pairs with correlation > 0.8.
 - **Output**: Generate `data/processed/model_config.yaml` containing:
 - `strategy`: "Covariates" (Default, but flexible)
 - `covariate_columns`: ["geographic_region", "sampling_year", "Varroa_mite_count"]
 - `pc_columns`: []
 - `collinearity_warning`: "VIF >= 5 detected; covariates retained. Diagnostic report generated."
 - `collinearity_pairs`: List of specific pairs with r² > 0.8 (calculated in T046).
 - **Condition**: If VIF < 5:
 - Log "Collinearity check passed."
 - **Output**: Generate `data/processed/model_config.yaml` containing:
 - `strategy`: "Covariates"
 - `covariate_columns`: ["geographic_region", "sampling_year", "Varroa_mite_count"]
 - `pc_columns`: []
 - **MANDATORY**: The script MUST produce `model_config.yaml` with the correct structure. It does NOT enforce a specific strategy that forbids PCA; it documents the findings.
 - **MANDATORY**: Archive intermediate files. Copy `model_config.yaml` to `data/interim/model_config_archived.yaml`. Copy pruned genotype files to `data/interim/pruned_genotypes_archived.*`. Ensure these are hash-verified artifacts.
 - **Verification**: Ensure the script exits with code 0 and the `model_config.yaml` file exists. Verify that `strategy` is "Covariates" (default). Verify that archived files exist in `data/interim/`.
 - **Depends on**: T006, T016.
 - **Note**: If T043 halts, T046 is skipped, and T017 will also be skipped.
- [X] T046b [P] [US1] [Config Generation] Define schema for `model_config.yaml` and ensure generation logic in T046 matches.
 - **Implementation**: Create `docs/model_config_schema.json` with the exact keys expected. Ensure T046 writes to this schema.
 - **Depends on**: T046.
- [X] T017 [US1] Create `code/03_gwas.sh` to execute PLINK logistic regression with mandatory covariates (from T046) and output raw association statistics (FR-004). Do NOT include FDR logic here; that is handled by T020. Output to `data/interim/gwas_raw.tsv`.
 - **Implementation**:
 1. **Required Artifacts**: `data/processed/model_config.yaml` (Output of T046), `data/processed/phenotypes_cleaned.fam` (Output of T016), `data/processed/pruned_genotypes.bed` (Output of T016).
 2. **Execution Gates**: T043 (Power Analysis) MUST pass (exit code 0) before this task executes. T046 (Collinearity Guard) MUST pass (exit code 0) before this task executes.
 3. Read `data/processed/model_config.yaml`.
 4. Extract `covariate_columns` and pass them to PLINK `--covar`.
 5. Run PLINK2 `--logistic hide-covar --ci 0.95 --out data/interim/gwas_raw` with the determined covariates.
 6. **Output**: Write results to `data/interim/gwas_raw.tsv`. **MUST** ensure this file is created with columns: `SNP`, `CHR`, `POS`, `P`, `Odds_Ratio`, `SE`.
 7. **MANDATORY Post-Processing**: PLINK2 may output `OR`. You MUST add a step to rename the `OR` column to `Odds_Ratio` in the final TSV to guarantee schema compatibility with T020 and T022.
 - **Implementation Detail**: Use pandas: `import pandas as pd; df = pd.read_csv('data/interim/gwas_raw.tsv', sep='\t'); df.rename(columns={'OR': 'Odds_Ratio'}, inplace=True); df.to_csv('data/interim/gwas_raw.tsv', sep='\t', index=False)`.
 - **Verification**: Verify `data/interim/gwas_raw.tsv` exists and contains the required columns with correct names.
 - **Depends on**: T015, T016, T043, T046.
- [X] T020 [P] [US1] Implement Benjamini-Hochberg FDR correction in `code/utils/fdr_correction.py` (FR-004).
 - **MANDATORY**: MUST implement BH correction as required by Spec FR-004.
 - **Note**: The Spec (FR-004) mandates BH. The Plan's "Complexity Tracking" suggests Bonferroni, but the Spec is the governing requirement. This contradiction is flagged for Plan revision (see T049).
 - **Implementation**: Explicitly implement BH correction. Do NOT use Bonferroni or Me-based thresholds for the correction calculation.
 - **Utilize Me**: Read `data/processed/me_estimate.txt` (from T052) to log the effective number of independent tests in the output metadata, but do NOT alter the BH calculation method.
 - **Output**: Write q-values to `data/interim/gwas_raw_fdr.tsv` (appending column).
 - **Verification**: Verify `data/interim/gwas_raw_fdr.tsv` exists and contains the `q_value` column.
 - **Depends on**: T017, T052.
- [ ] T022 [US1] Create `code/04_apply_fdr.sh` to merge PLINK raw results (T017) with FDR-corrected results (T020) into the final artifact `data/processed/gwas_results_fdr.tsv`.
 - **Implementation**:
 1. Read `data/interim/gwas_raw.tsv` (Output of T017).
 2. Read `data/interim/gwas_raw_fdr.tsv` (Output of T020).
 3. Merge the two files on the `SNP` column.
 4. Write the merged result to `data/processed/gwas_results_fdr.tsv`.
 5. Ensure the final file contains all required columns: `SNP`, `CHR`, `POS`, `P`, `Odds_Ratio`, `q_value`.
 - **Verification**: Verify `data/processed/gwas_results_fdr.tsv` exists and contains the `q_value` column.
 - **Depends on**: T017, T020.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Multiple Testing Correction & Threshold Sensitivity (Priority: P2)

**Goal**: Apply Benjamini-Hochberg FDR correction and test threshold sensitivity to identify robust genetic associations.

**Independent Test**: Can be tested independently by running the correction on the GWAS output and verifying q-values and threshold counts.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for Benjamini-Hochberg implementation in `tests/unit/test_fdr_correction.py`
- [X] T019 [P] [US2] Contract test for threshold sensitivity output format in `tests/contract/test_threshold_sensitivity.py`

### Implementation for User Story 2

- [X] T021 [US2] Implement threshold sensitivity sweep across the specific set of thresholds {×⁻⁷, ×10⁻⁸, 1×10⁻⁸} in `code/utils/threshold_sensitivity.py` (FR-005).
 - **Implementation**: Explicitly sweep the thresholds across a set of orders of magnitude.
 - **MANDATORY**: MUST apply Benjamini-Hochberg (BH) correction as required by Spec FR-004 and FR-005.
 - **Utilize Me**: Read `data/processed/me_estimate.txt` (from T052) to log the effective number of independent tests in the output metadata, but do NOT alter the BH calculation method.
 - **Output**: Write a report to `data/processed/threshold_sensitivity_report.tsv` containing columns: `threshold`, `snp_count`, `min_q_value`, `significant_count`.
 - **Depends on**: T020, T052.
- [X] T023 [US2] Update `code/04_apply_fdr.sh` to and document the study design.
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
 - **Depends on**: T016, T022.
 - **Note**: This test is written first (Test First methodology) and depends on the Spec, not the implementation tasks. The implementation tasks T027-T032 will be written to make this test pass.

### Implementation for User Story 3

- [X] T027 [US3] Implement LASSO logistic regression with 5-fold cross-validation in `code/04_ml_validation.py` (FR-006) and report out-of-sample AUC value.
 - **Implementation**: Use `sklearn.linear_model.LogisticRegressionCV` with `penalty='l1'`, `solver='liblinear'`, and `cv=5`.
 - **Output**: Write `data/processed/lasso_auc_report.json` containing:
 - `auc`: float (4 decimal places)
 - `low_predictive_power`: boolean (True if auc < 0.75, False otherwise)
 - `num_features_selected`: integer (number of non-zero coefficients)
 - `total_snps`: integer (total candidates)
 - **Verification**: Assert file exists and keys are present.
 - **Depends on**: T022, T016.
- [X] T028 [US3] Implement Polygenic Risk Score (PRS) calculation in `code/04_ml_validation.py` (FR-007).
 - **Output**: Write `data/processed/prs_scores.tsv` with columns: `colony_id`, `prs_value`.
 - **Depends on**: T022.
- [X] T029 [US3] Implement likelihood-ratio test for PRS improvement over covariates-only model in `code/04_ml_validation.py` (FR-007).
 - **Output**: Write `data/processed/prs_validation_results.json` containing `p_value` and `likelihood_ratio_statistic`.
 - **Depends on**: T028, T022.
- [X] T030 [US3] Add AUC reporting logic in `code/04_ml_validation.py`:
 - **Note**: Logic for flagging low predictive power is now handled in T027. This task is for additional reporting if needed.
 - **Depends on**: T027, T028, T029.
- [X] T031 [US3] Implement collinearity diagnostics (VIF) for covariates (geographic region, sampling year) in `code/04_ml_validation.py` (FR-010, US-3 AC4).
 - **MANDATORY**: MUST implement VIF calculation and flag relationships where r² > 0.8 in the output artifact `data/processed/collinearity_report.tsv`.
 - **Output Schema**: `collinearity_report.tsv` MUST contain columns: `covariate_pair`, `r_squared`, `vif`, `status` (flagged/clear).
 - **MANDATORY**: Document findings descriptively, framing joint relationships as such rather than independent effects.
 - **Depends on**: T016, T022.
- [X] T032 [US3] Implement `code/05_annotation.py` to map significant SNPs to genes using Ensembl Bees API and query GO terms (FR-008).
 - **MANDATORY**: Output `data/processed/annotated_snps.tsv` with columns: rs_id, gene_symbol, go_terms, pathway.
 - **Implementation**: Use `biopython` and the Ensembl REST API.
 - **Retry Logic**: Implement retry logic with a configurable maximum number of attempts and exponential backoff with increasing intervals.
 - **Graceful Degradation**: If all attempts fail or service is "not known", log a clear warning "Ensembl API unavailable; skipping annotation", set `go_terms` to "UNAVAILABLE", and continue the pipeline (do not exit with code 1).
 - **Verification**: Verify `data/processed/annotated_snps.tsv` exists and contains rows with `go_terms` set to "UNAVAILABLE" if the API failed, or valid terms if successful.
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
 - **Implementation**: Run `python -m cProfile -o data/processed/profile.prof code/03_gwas.sh` (invoking the shell script logic) or the Python logic it wraps. Use `pstats` to generate `data/processed/profile_report.txt`.
 - **Output**: `data/processed/profile_report.txt`.
 - **Note**: Ensure the target `code/03_gwas.sh` exists and is executable before profiling.
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
 - **Mandatory**: If missing for <= 20%, exclude those samples from the covariate model but retain for genotype-only analysis.
 - Log all exclusions to `data/processed/exclusion_log.txt`.
 - **Output Schema**: `exclusion_log.txt` must be a CSV with columns: `sample_id`, `reason`.
- [X] T047 [P] [Polish] Implement `code/07_runbook_generator.py` to generate a deterministic execution runbook for GitHub Actions (FR-004, US-1 AC3).
 - **Implementation**:
 - Assume a standard Ubuntu runner environment.
 - Read `code/requirements.txt` and `code/00_generate_simulated_fastq.py` (T013c).
 - Generate a single bash script `runbook.sh` that:
 1. Installs dependencies (Include `apt-get install` or `conda install` commands for bwa, freebayes, plink2. MUST use pinned versions from `code/requirements.txt` or `code/environment.yml`).
 2. Generates synthetic data (T009) OR fetches real data (T012a) based on `USE_SYNTHETIC_DATA` env var.
 3. Generates FASTQ (T013c).
 4. Runs alignment/calling (T014).
 5. Converts to PLINK (T015).
 6. Runs power analysis (T043) and halts if needed.
 7. Runs GWAS (T017).
 8. Applies FDR (T022).
 9. Runs ML validation (T027-T032).
 10. Runs annotation (T032).
 - Include explicit `set -e` and timeout checks to ensure compliance with the specified time limit.
 - **Output**: `runbook.sh` and `docs/runbook_validation.md`.
 - **Depends on**: T009, T013c, T014, T017, T022, T027, T028, T029, T030, T031, T032.
- [X] T048 [P] [Polish] Implement `tests/unit/test_runbook_idempotency.py` to verify the runbook produces identical results on re-run (Constitution Principle I).
 - **Implementation**:
 - Execute `runbook.sh` twice in isolated directories.
 - Compare checksums of all output artifacts in `data/processed/`.
 - Assert all checksums match.
 - **Output**: `data/processed/idempotency_report.txt`.
- [X] T049 [P] [Polish] Implement `code/09_plan_revision_flag.py` to generate a `docs/plan_revision_notes.md` file.
 - **Rationale**: The Plan's "Complexity Tracking" (Bonferroni vs BH) and "Constitution Check VII" (PCA fallback) contradict the Spec. This task generates a formal note to be addressed in the next review cycle.
 - **Implementation**:
 1. Read `spec.md` and `plan.md`.
 2. Identify contradictions:
 - Spec FR-004/005 mandates BH; Plan suggests Bonferroni.
 - Spec FR-003/010 mandates covariates; Plan suggests PCA fallback on VIF >= 5.
 3. Write `docs/plan_revision_notes.md` with:
 - Section: "Spec vs Plan Conflicts".
 - List of specific contradictions with line references.
 - Recommendation: "Update Plan.md to align with Spec.md priorities."
 - **Output**: `docs/plan_revision_notes.md`.
 - **Depends on**: T002, T005, T006, T020, T046.
- [X] T051 [P] [Review Fix] Update `code/08_collinearity_guard.py` (T046) to explicitly log the specific covariate pairs causing high VIF.
 - **Rationale**: Address reviewer concern about "defining relationships" (FR-010). The current task calculates VIF but doesn't explicitly identify the pairs (e.g., "Region vs Year").
 - **Implementation**:
 1. In `code/08_collinearity_guard.py`, after calculating VIF, compute the correlation matrix of covariates.
 2. If VIF >= 5, identify pairs with correlation > 0.8.
 3. Log "High collinearity detected between [ColA] and [ColB] (r² = X.XX)."
 4. Include this specific pair info in `data/processed/model_config.yaml` under `collinearity_pairs`.
 - **Verification**: Verify `model_config.yaml` contains the specific pair names when VIF is high.
 - **Depends on**: T006, T046.
- [X] T052 [P] [Review Fix] Add explicit task for "Effective Number of Independent Tests (Me)" calculation in `code/utils/gwas_thresholds.py`.
 - **Rationale**: Address reviewer concern in Assumptions regarding the genome-wide significance threshold. The Spec mentions "effective number of independent tests" but the tasks only implement BH. We need a specific task to calculate Me for the honeybee genome to document the Me value used for BH context (NOT for Bonferroni correction).
 - **Implementation**:
 1. Implement a script that estimates Me using the spectral decomposition of the LD matrix (or a standard approximation for honeybee LD).
 2. Output `data/processed/me_estimate.txt` with the calculated Me value.
 3. Update `code/utils/fdr_correction.py` (T020) to log this Me value in the output metadata.
 4. Update `code/utils/threshold_sensitivity.py` (T021) to log this Me value in the output metadata.
 5. **MANDATORY**: This task is for documentation ONLY. It must NOT alter the FDR method (BH) used in T020.
 - **Verification**: Verify `me_estimate.txt` exists and contains a plausible integer value for honeybee genome.
 - **Depends on**: T016 (for LD pruning data).
- [X] T054 [P] [Polish] Implement `code/10_final_validation.py` to run a comprehensive check of all artifacts against the Spec requirements.
 - **Implementation**:
 1. Check for existence of all required output files.
 2. Verify schema compliance of all TSV/JSON outputs.
 3. Verify that all mandatory disclaimers and warnings are present.
 4. Generate `data/processed/final_validation_report.md`.
 - **Depends on**: All previous tasks.

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
- **Critical Revision**: Tasks T012a, T046, T013a/b/c updated to resolve Spec/Plan conflicts and ordering issues.
- **Correction**: T012a now distinguishes SSL errors (Halt) from missing data (Halt unless env var set). T046 now correctly implements the mandatory Covariates retention (no PCA fallback) and archiving. T013 split into Setup (T013a, T013b), Implementation (T013c), and Verification (T013d).
- **Removed**: T057, T058 (GPU logic - out of scope), T049, T052 (Streaming - unnecessary), T054 (Verified Source manifest - out of scope), T053, T055 (Redundant/Contradictory). T050, T053 merged into T012a and T005. T051, T052, T054 added/updated to address specific reviewer concerns.
- **New**: T049 added to formally document Spec/Plan contradictions for future revision.
- **Note**: The Plan's 'Complexity Tracking' section regarding Bonferroni vs BH and 'Constitution Check VII' regarding PCA fallback are flagged for Plan revision to align with the Spec. Tasks follow the Spec.
- **Note**: T050, T053 merged into T012a and T005 respectively. T051, T052, T054 added/updated to address specific reviewer concerns.
- **Note**: T055 is superseded by T012a. Logic integrated.
- **Note**: T056 is superseded by T012a. Logic integrated.
- **Note**: T057 is superseded by T043. Logic integrated.
- [X] T059 [P] [Review Fix] Update `code/01_download.py` (T012a) to explicitly log the exact number of samples with Varroa data vs total samples before the `ERR_VARROA_COVARIATE_MISSING` check.
 - **Rationale**: Address reviewer concern about transparency in data filtering. The current task checks the percentage but doesn't log the raw counts (e.g., "85/100 samples have Varroa data").
 - **Implementation**:
 1. In `code/01_download.py`, after parsing metadata, calculate `total_samples` and `samples_with_varroa`.
 2. Log "Varroa Data Coverage: {samples_with_varroa}/{total_samples} ({percent}%)." to stdout.
 3. If the percentage is < 80%, the error message `ERR_VARROA_COVARIATE_MISSING` MUST include these exact counts.
 - **Verification**: Verify the log output contains the raw counts and the error message includes them if the check fails.
 - **Depends on**: T012a.
- [X] T060 [P] [Review Fix] Update `code/04_ml_validation.py` (T027) to explicitly report the number of SNPs used in the LASSO model.
 - **Rationale**: Address reviewer concern about model transparency. The current task reports AUC but not the feature count (which is critical for interpreting the model in a high-dimensional setting).
 - **Implementation**:
 1. In `code/04_ml_validation.py`, after fitting the LASSO model, count the number of non-zero coefficients.
 2. Append this count to `data/processed/lasso_auc_report.json` under the key `num_features_selected` (read existing file, append key, write back).
 3. Log "LASSO selected {num_features_selected} SNPs out of {total_snps} candidates."
 - **Verification**: Verify the JSON output contains the `num_features_selected` key and the log message is present.
 - **Depends on**: T022, T027.
- [X] T061 [P] [Review Fix] Update `code/05_annotation.py` (T032) to handle "no gene found" cases explicitly. <!-- ATOMIZE: requested -->
 - **Rationale**: Address reviewer concern about edge cases in annotation. The current task sets `go_terms` to "UNAVAILABLE" on API failure, but doesn't handle cases where the API succeeds but no gene is found for a specific SNP.
 - **Implementation**:
 1. In `code/05_annotation.py`, after querying the API, check if a gene symbol is returned.
 2. If no gene is found, set `gene_symbol` to "INTERGENIC" and `go_terms` to "N/A".
 3. Log "SNP {rs_id} is intergenic; no gene symbol found."
 4. Ensure the output file `data/processed/annotated_snps.tsv` contains these rows with the correct markers.
 - **Verification**: Verify the TSV contains rows with `gene_symbol` = "INTERGENIC" and `go_terms` = "N/A".
 - **Depends on**: T022, T032.

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [X] T062 Reconcile run-book vs implementation for `code/02_harmonize_phenotypes.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/02_harmonize_phenotypes.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [X] T063 Reconcile run-book vs implementation for `code/04_filter_snps.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/04_filter_snps.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [X] T064 Reconcile run-book vs implementation for `code/05_collinearity_diag.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/05_collinearity_diag.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [ ] T065 Reconcile run-book vs implementation for `code/06_power_analysis.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/06_power_analysis.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [ ] T066 Reconcile run-book vs implementation for `code/08_apply_fdr.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/08_apply_fdr.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [ ] T067 Reconcile run-book vs implementation for `code/09_threshold_sensitivity.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/09_threshold_sensitivity.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [ ] T068 Reconcile run-book vs implementation for `code/10_lasso_validation.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/10_lasso_validation.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [ ] T069 Reconcile run-book vs implementation for `code/11_prs_and_lr_test.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/11_prs_and_lr_test.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [ ] T070 Reconcile run-book vs implementation for `code/12_annotate_genes.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/12_annotate_genes.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [ ] T071 Reconcile run-book vs implementation for `code/13_format_results.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/13_format_results.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
