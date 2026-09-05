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

**Note on Spec vs Plan Conflict**: The Spec (FR-004, FR-005) mandates Benjamini-Hochberg (BH) FDR correction on the full set of high-quality SNPs. The Plan's "Complexity Tracking" section argues for Candidate-Gene pre-filtering to reduce the multiple testing burden. **Per the Constitution, the Spec is the governing requirement.** Tasks T063 implements Candidate-Gene logic ONLY for annotation/visualization, NOT for the primary GWAS filtering. The Plan is flagged for revision to align with the Spec.

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
samtools
```
**Note**: `dwgsim` is a system binary, not a Python package. It must be installed via conda/bioconda, not pip. Do NOT include it in requirements.txt. T013a handles system binary installation.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create data directory structure with immutable raw data constraints (mkdir -p data/raw, data/processed, data/interim)
- [X] T039 [P] Implement `code/utils/checksum_verify.py` to verify checksums of raw data files against recorded hashes
- [X] T040 [P] Create `docs/data_policy.md` defining the 'immutable' constraint for raw data
- [X] T005 [P] Implement `code/utils/power_analysis.py` for FR-012. MUST:
 1. Calculate power using non-central chi-squared distribution.
 2. **HALT ONLY IF n < 80** with error code `ERR_SAMPLE_SIZE_INSUFFICIENT`.
 3. If n >= 80: Calculate power and **REPORT** it by writing a JSON object to `data/processed/power_analysis_report.json` with keys: `power_value`, `status: "PASS"`, `n_samples`.
 4. **Verification**: The script MUST verify the existence of `data/processed/power_analysis_report.json` after writing.
 5. Output: Write power value and status to `data/processed/power_analysis.txt` (summary) and `data/processed/power_analysis_report.json` (structured).
- [X] T006 [P] Implement `code/utils/collinearity_diag.py` for FR-010 (VIF calculation, correlation matrix)
- [X] T007 [P] Create base data schema validators for `Colony` and `SNP` entities: create `code/utils/validators/colony_schema.py` and `code/utils/validators/snp_schema.py` based on `specs/001-gene-regulation/contracts/dataset.schema.yaml` and `specs/001-gene-regulation/contracts/gwas_output.schema.yaml`
- [X] T008 [P] Create `.env.example` with keys `NCBI_API_KEY`, `ENSEMBL_API_KEY` and default values for SSL CA bundle paths
- [X] T009 [P] Implement `code/00_generate_synthetic_data.py` to create deterministic synthetic VCF + Phenotypes for validation. MUST implement CCD diagnosis validation logic that explicitly checks:
 1. Presence of dead adult bees in the hive.
 2. Absence of dead pupae.
 3. Live bee population < 10% relative to peak season.
 Logic MUST fail validation if any of these criteria are not met in the synthetic data generation process (FR-011).
- [X] T013a [P] [Foundational] Install `dwgsim` in the environment.
 - **Implementation**: Add `dwgsim` to `code/environment.yml` or create a `setup.sh` script that runs: `conda config --add channels bioconda && conda install -c bioconda dwgsim`.
 - **Note**: `dwgsim` is a system binary, not a Python package.
- [X] T013b [P] [Foundational] Verify `dwgsim` availability.
 - **Implementation**: Run `dwgsim --help` and verify it exits with code 0.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - GWAS Pipeline Execution (Priority: P1) 🎯 MVP

**Goal**: Execute the complete GWAS analysis pipeline on honeybee genomic data to identify SNPs associated with CCD susceptibility.

**Independent Test**: Can be fully tested by running the pipeline on a small sample dataset and verifying that SNP association statistics are produced.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Contract test for VCF schema validation in `tests/contract/test_vcf_schema.py`
- [X] T011 [P] [US1] Integration test for full synthetic pipeline run in `tests/integration/test_synthetic_gwas.py`

### Implementation for User Story 1

- [X] T043 [P] [US1] [Gate] Implement `code/04_check_power_and_halt.sh` to execute `code/utils/power_analysis.py` (T005) immediately after data loading.
 - **Note**: This task MUST be executed BEFORE T012a to prevent unnecessary data fetch if power is insufficient.
 - **Implementation**: Run `code/utils/power_analysis.py`. If exit code is non-zero, halt pipeline. If exit code is 0, verify `data/processed/power_analysis_report.json` exists.
- [X] T012a [US1] Implement `code/01_download.py` to fetch data from the verified Hugging Face dataset `bee_genome_variants` (derived from NCBI BioProject PRJNA/566029) with associated metadata.
 - **Implementation**:
 1. **Primary Source**: Use `datasets.load_dataset("bee_genome_variants", split="train")` to fetch data into `data/raw`.
 2. **SSL Hard-Stop**: Validate SSL certificates using a verified CA bundle. If verification fails, the system MUST halt with `sys.exit(1)` and a clear error message: "SSL Verification Failed: [Error Details]". Do NOT proceed.
 3. **Data Size Check**: If the dataset exceeds 14GB (unexpected for ~A substantial number of colonies), HALT with error `ERR_DATA_SIZE_EXCEEDED` and log the discrepancy.
 4. **Output Artifacts**: `data/raw/fastq_files`, `data/processed/ncbi_fetch_log.json`.
 - **Note**: This task enforces HF priority as per Plan Phase 0 and Spec Assumptions. No fallback paths allowed.

- [X] T014 [US1] Implement alignment and variant calling pipeline in `code/02_align_call.sh` (FR-002).
 - **Input**: `data/raw/fastq_files` (from T012a).
 - **Output**: `data/interim/raw_variants.vcf`.
 - **Implementation**:
 1. Align reads to reference genome `Amel_HAv3.1 (Wikipedia: Western honey bee, https://en.wikipedia.org/wiki/Western_honey_bee)` using `bwa mem`.
 2. Call variants using `FreeBayes`.
 3. Filter to high-quality biallelic SNPs (QUAL > 30, depth ≥ 10) using `bcftools`.
 - **Note**: This task is critical for producing the VCF required by T015.

- [X] T045 [P] [US1] [Validation Only] Implement `code/00_generate_simulated_fastq.py` to simulate FASTQ for *validation/testing* of the alignment pipeline (FR-002).
 - **Input**: `data/interim/synthetic.vcf` (generated by T009).
 - **Output**: `data/interim/synthetic_R1.fq` and `data/interim/synthetic_R2.fq`.
 - **Implementation**: Use `dwgsim` with a fixed random seed to ensure reproducibility.
 - **Command Example**: `dwgsim -e -l 150 -1 350 -2 50 -N 10 -s 42 data/interim/synthetic.vcf data/interim/synthetic_R1.fq data/interim/synthetic_R2.fq`. (Insert size distribution: Normal(mean=350, std=50)).
 - **Note**: This task provides the synthetic data path required by Plan Phase 0 for toolchain validation when real data is unavailable, without relaxing T012a's strict real data constraints.

- [X] T046 [P] [US1] [Verification] Verify `code/00_generate_simulated_fastq.py` output.
 - **Implementation**: Run `fastqc` or simple validation on FASTQ files.

- [X] T015 [US1] Implement VCF to PLINK format conversion in `code/utils/vcf_to_plink.py` (FR-003).
 - **Input**: `data/interim/raw_variants.vcf` (from T014) OR `data/interim/synthetic.vcf` (from T009).
 - **Output**: `data/interim/bed.bim`, `data/interim/bed.fam`, `data/interim/bed.bed`.

- [X] T016 [US1] Implement `code/utils/preprocess_phenotype.py` for LD pruning (r² < 0.2) and covariate encoding (geographic region, sampling year, Varroa mite count) (FR-003).
 - **Input**: `data/interim/bed.*` (from T015).
 - **Output**: `data/interim/bed_pruned.bim` (for LD pruning reference), `data/interim/phenotypes_cleaned.fam`.
 - **Implementation**: Perform LD pruning using PLINK `--indep-pairwise 50 5 0.2` and output the pruned bim file.

- [X] T062 [US1] Implement `code/02_harmonize_phenotypes.py` to map CCD diagnosis codes to CCD Working Group criteria (FR-011).
 - **Input**: `data/interim/phenotypes_cleaned.fam`.
 - **Output**: `data/interim/phenotypes_harmonized.fam`.
 - **Implementation**:
 1. Map CCD diagnosis codes to binary (CCD=1, Healthy=0).
 2. **Varroa Check**: Calculate the percentage of samples with Varroa data. If < 80%, exit with code `ERR_VARROA_COVARIATE_MISSING` and a clear error message.

- [X] T063 [US1] Implement `code/03_filter_snps.py` to pre-filter SNPs to immune pathway (Candidate-Gene approach) **for annotation purposes only** (FR-003).
 - **Note**: This filtered list is NOT used for the primary GWAS run (T017) which must use all high-quality SNPs per Spec. This list is used for T032 (Annotation).
 - **Input**: `data/interim/bed.bim`.
 - **Output**: `data/interim/immune_pathway_snps.txt`.

- [X] T064 [US1] Implement `code/05_collinearity_diag.py` to perform collinearity diagnostics (FR-010).

- [X] T017 [US1] Create `code/03_gwas.sh` to execute PLINK logistic regression with mandatory covariates (from T046) and output raw association statistics (FR-004). Do NOT include FDR logic here; that is handled by T020. Output to `data/interim/gwas_raw.tsv`.
 - **Input**: `data/interim/bed.bim`, `data/interim/bed.fam`, `data/interim/phenotypes_cleaned.fam`.
 - **Output**: `data/interim/gwas_raw.tsv`.

- [X] T020 [US2] Implement Benjamini-Hochberg FDR correction in `code/utils/fdr_correction.py` (FR-004).
 - **Depends on**: T017.
 - **Input**: `data/interim/gwas_raw.tsv`. MUST sort by p-value in **ascending order** before processing. P-values must be formatted to **10 decimal places**.
 - **Output**: `data/interim/gwas_fdr.tsv`.
 - **Output Schema**: Columns must be: `rank`, `raw_p`, `q_value`, `significant` (boolean).
 - **Logic**: Apply BH correction.

- [X] T052 [P] [US1] [Review Fix] Implement `code/utils/gwas_thresholds.py` to calculate the "Effective Number of Independent Tests (Me)" for documentation.
 - **Depends on**: T016.
 - **Rationale**: Address reviewer concern in Assumptions regarding the genome-wide significance threshold. The Spec mentions "effective number of independent tests" but the tasks only implement BH. We need a specific task to calculate Me for the honeybee genome to document the Me value used for BH context (NOT for Bonferroni correction).
 - **Implementation**:
 1. Implement a script that estimates Me using the spectral decomposition of the LD matrix (or a standard approximation for honeybee LD).
 2. **Input**: `data/interim/bed_pruned.bim` (from T016).
 3. Output `data/processed/me_estimate.txt` with the calculated Me value.
 4. Update `code/utils/fdr_correction.py` (T020) to log this Me value in the output metadata.
 5. Update `code/utils/threshold_sensitivity.py` (T021) to log this Me value in the output metadata.
 6. **MANDATORY**: This task is for documentation ONLY. It must not alter the FDR method (BH).
 - **Verification**: Verify `me_estimate.txt` exists and contains a plausible integer value for honeybee genome.

- [X] T022 [US1] Create `code/04_apply_fdr.sh` to merge PLINK raw results (T017) with FDR-corrected results (T020) into the final artifact `data/processed/gwas_results_fdr.tsv`.
 - **Depends on**: T017 and T020.
 - **Implementation**:
 1. Read `data/interim/gwas_raw.tsv` and `data/interim/gwas_fdr.tsv`.
 2. Merge on SNP ID.
 3. Write to `data/processed/gwas_results_fdr.tsv` with columns: `snp_id`, `chrom`, `pos`, `ref`, `alt`, `freq`, `p_value`, `q_value`, `significant`.
 4. Ensure all SNPs from the raw file are present, with `significant` flag set based on q-value < 0.05.
 - **Verification**: Verify `data/processed/gwas_results_fdr.tsv` exists and contains the expected columns and data.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Multiple Testing Correction & Threshold Sensitivity (Priority: P2)

**Goal**: Apply Benjamini-Hochberg FDR correction and test threshold sensitivity to identify robust genetic associations.

**Independent Test**: Can be tested independently by running the correction on the GWAS output and verifying q-values and threshold counts.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for Benjamini-Hochberg implementation in `tests/unit/test_fdr_correction.py`
- [X] T019 [P] [US2] Contract test for threshold sensitivity output format in `tests/contract/test_threshold_sensitivity.py`

### Implementation for User Story 2

**Note on Redundancy**: Tasks T068 and T069 were removed to resolve duplication. **T020 and T021 are the single source of truth** for FDR correction and threshold sensitivity.

- [X] T021 [US2] Implement threshold sensitivity sweep across a specific set of thresholds in `code/utils/threshold_sensitivity.py` (FR-005).
 - **Input**: `data/interim/gwas_fdr.tsv` (from T020).
 - **Output**: `data/processed/threshold_sensitivity.json`.
 - **Logic**: For each threshold, count SNPs passing and list corresponding q-values.
- [X] T023 [US2] Create `code/05_document_study_design.py` to document the study design, associational nature, and covariate handling.
 - **Implementation**: Generate `data/processed/study_design.md` with explicit disclaimers (FR-009).
 - **Note**: This task replaces the ambiguous T023 shell script reference.

---

## Phase 5: User Story 3 - Machine Learning Validation & Polygenic Risk Scoring (Priority: P3)

**Goal**: Validate GWAS findings using LASSO logistic regression and compute polygenic risk scores to assess predictive performance.

**Independent Test**: Can be tested by running LASSO on a held-out test set (or synthetic equivalent) and verifying AUC is computed correctly.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US3] Unit test for LASSO AUC calculation in `tests/unit/test_lasso_auc.py`
- [X] T026 [P] [US3] Contract test for threshold sensitivity output format in `tests/contract/test_threshold_sensitivity.py`

### Implementation for User Story 3

**Note on Redundancy**: Tasks T070, T071, T072 were removed to resolve duplication. **T027-T032 are the single source of truth** for US3 implementation.

- [X] T027 [US3] Implement LASSO logistic regression with 5-fold cross-validation in `code/04_ml_validation.py` (FR-006) and report out-of-sample AUC value.
 - **Depends on**: T022.
 - **Implementation**:
 1. Split data: **[deferred] for training, [deferred] for testing** using `train_test_split` with `random_state=42`.
 2. Train LASSO on the designated training set using k-fold cross-validation.
 3. Compute AUC on the held-out test set.
 4. Report AUC value. If AUC < 0.75, flag as low predictive power.
 - **Input**: `data/processed/gwas_results_fdr.tsv` (from T022).
 - **Output**: `data/processed/lasso_auc_report.json`.

- [X] T028 [US3] Implement Polygenic Risk Score (PRS) calculation in `code/04_ml_validation.py` (FR-007).
 - **Depends on**: T022.
 - **Input**: `data/processed/gwas_results_fdr.tsv` (from T022).
 - **Output**: `data/processed/prs_scores.tsv`.
 - **Implementation**: Calculate PRS for each colony based on significant SNPs.

- [X] T029 [US3] Implement likelihood-ratio test for PRS improvement over covariates-only model in `code/04_ml_validation.py` (FR-007).
 - **Depends on**: T028.
 - **Input**: `data/processed/prs_scores.tsv` (from T028).
 - **Output**: `data/processed/prs_lr_test.json`.

- [X] T030 [US3] Add AUC reporting logic in `code/04_ml_validation.py`:
 - **Input**: `data/processed/lasso_auc_report.json`.
 - **Output**: `data/processed/validation_metrics.json`.

- [X] T031 [US3] Implement collinearity diagnostics (VIF) for covariates (geographic region, sampling year) in `code/04_ml_validation.py` (FR-010, US-3 AC4).
 - **Input**: `data/interim/phenotypes_cleaned.fam`.
 - **Output**: `data/processed/collinearity_report.json`.

- [X] T032 [US3] Implement `code/05_annotation.py` to map significant SNPs to genes using Ensembl Bees API and query GO terms (FR-008).
 - **Input**: `data/interim/immune_pathway_snps.txt` (from T063).
 - **Output**: `data/processed/annotation_results.tsv`.
 - **Implementation**:
 1. Use Ensembl Bees API **version**.
 2. If a SNP maps to multiple genes, select the one with the shortest genomic distance.
 3. If a SNP maps to **no genes**, assign the value **'INTERGENIC'** in the output schema.
 4. If the API is unavailable, assign **'UNAVAILABLE'**.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T033a [P] Create `docs/pipeline_execution_guide.md` with step-by-step execution instructions.
 - **Update**: Ensure instructions reference `code/utils/fdr_correction.py` (T020) and `code/04_ml_validation.py` (T027) directly, not wrapper scripts.
- [X] T033b [P] Create `docs/data_dictionary.md` defining all data artifacts and schemas
- [X] T034 [P] Code cleanup and refactoring of shell scripts for portability (Depends on T014, T017, T022).
- [X] T041 [P] Profile pipeline with `cProfile` and generate `data/processed/profile_report.txt`.
 - **Verification**: MUST verify runtime < 6h and RAM < 7GB; halt if limits exceeded.
- [X] T042 [P] Refactor `code/02_align_call.sh` to use parallel processing if profile shows I/O bottleneck (Depends on T041).
- [X] T036 [P] Additional unit tests for edge cases (missing Varroa data, all SNPs filtered) in `tests/unit/`.
- [X] T037 [P] Run quickstart.md validation to ensure reproducibility.
- [X] T038 [P] Create `docs/report_template.md` to include the mandatory disclaimer text: "Findings are associational, not causal..." (FR-009)
- [X] T044 [P] Implement `code/06_edge_case_handler.py` to explicitly handle missing Varroa metadata (Assumption 1):
- [X] T051 [P] [Review Fix] Update `code/01_download.py` (T012a) to explicitly log the exact number of samples with Varroa data vs total samples before the `ERR_VARROA_COVARIATE_MISSING` check.

**Note on GPU Constraint**: Task T074 was removed to align with the Spec's explicit Assumption that "No GPU or CUDA accelerators are required" and to prevent architectural drift. The project remains CPU-tractable.

- [X] T061 [P] [Review Fix] Update `code/05_annotation.py` (T032) to handle "no gene found" cases explicitly.

- [X] T075 [P] Implement `code/06_power_analysis.py` (FR-012).
 - **Implementation**: Create the script `code/06_power_analysis.py` that performs the power analysis as defined in T005. Ensure it is called by the run-book.
 - **Update Run-book**: Update `docs/quickstart.md` to invoke `code/06_power_analysis.py`.
 - **Verification**: Verify the script runs and produces `data/processed/power_analysis.txt`.

**Removed Redundant Tasks**: Tasks T076 through T081 (wrapper scripts for FDR, LASSO, etc.) have been removed to avoid duplication with T020, T027, etc. The run-book now invokes the specific implementation scripts directly.

---

## Phase O: Plan Alignment & Documentation (Revision)

**Purpose**: Resolve conflicts between Spec and Plan regarding Candidate-Gene filtering and ensure documentation reflects the governing Spec requirements.

- [ ] T082 [P] [Plan Revision] Update `plan.md` to remove "Candidate-Gene Pre-filtering" from the "Complexity Tracking" table as a justification for reducing the GWAS burden.
 - **Rationale**: The Spec (FR-004) requires GWAS on all high-quality SNPs. The Plan's suggestion to pre-filter for the primary GWAS contradicts the Spec. The Candidate-Gene approach is correctly implemented in T063 *only* for annotation, not for the statistical test.
 - **Action**: Edit `plan.md` to state: "The primary GWAS (FR-004) is performed on all high-quality SNPs. Candidate-Gene filtering is applied *only* for downstream functional annotation (T032) to manage API load and focus interpretation."

- [ ] T083 [P] [Documentation] Update `docs/pipeline_execution_guide.md` to explicitly state the order of operations:
 1. Load ALL high-quality SNPs.
 2. Run GWAS on ALL SNPs.
 3. Apply FDR on ALL SNPs.
 4. *Then* apply Candidate-Gene filter (from T063) to the *significant* results for annotation.
 - **Rationale**: Prevents future confusion about whether the GWAS itself is filtered.

- [ ] T084 [P] [Review Fix] Add a specific task to `code/03_gwas.sh` (T017) to verify that the input file contains the expected number of SNPs (matching the raw VCF count after quality filters) before running PLINK.
 - **Implementation**: Add a check: `if [ $(wc -l < data/interim/bed.bim) -ne <expected_count> ]; then echo "ERROR: SNP count mismatch" && exit 1; fi`.
 - **Rationale**: Ensures no accidental pre-filtering occurs before the main statistical test.

- [ ] T085 [P] [Review Fix] Update `docs/data_dictionary.md` to clearly distinguish between `data/interim/bed.bim` (all SNPs) and `data/interim/immune_pathway_snps.txt` (filtered subset for annotation only).
 - **Rationale**: Clarifies the data flow and prevents misuse of the filtered list for statistical analysis.