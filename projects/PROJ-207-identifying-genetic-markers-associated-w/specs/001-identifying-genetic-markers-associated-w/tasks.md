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
scikit-learn
pandas
numpy
statsmodels
pyyaml
requests
biopython
samtools
entrez-direct
```
**Note**: `dwgsim` is a system binary, not a Python package. It must be installed via conda/bioconda, not pip. Do NOT include it in requirements.txt. T013a handles system binary installation.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

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

**Goal**: Execute the complete GWAS analysis pipeline on honeybee genomic data to identify SNPs associated with CCD susceptibility, including FDR correction and result merging.

**Independent Test**: Can be fully tested by running the pipeline on a small sample dataset and verifying that SNP association statistics with FDR correction are produced.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Contract test for VCF schema validation in `tests/contract/test_vcf_schema.py`
- [X] T011 [P] [US1] Integration test for full synthetic pipeline run in `tests/integration/test_synthetic_gwas.py`

### Implementation for User Story 1

- [X] T012a [US1] Implement `code/01_download.py` to fetch data from NCBI BioProject PRJNA639195 (CCD) and PRJNA566029 (Healthy) with associated metadata.
 - **Implementation**:
 1. **Primary Source**: Use `entrez-direct` (esearch, efetch) to download SRA metadata and FASTQ files for PRJNA639195 and PRJNA566029.
 2. **SSL Hard-Stop**: Validate SSL certificates using a verified CA bundle. If verification fails, the system MUST halt with `sys.exit(1)` and a clear error message: "SSL Verification Failed: [Error Details]". Do NOT proceed. Do NOT fallback to synthetic data.
 3. **Sample Count Check**: After fetching, count the number of unique colonies. If n < 80, exit with error `ERR_SAMPLE_SIZE_INSUFFICIENT`.
 4. **Output Artifacts**: `data/raw/fastq_files`, `data/processed/ncbi_fetch_log.json`.
 - **Note**: This task enforces NCBI as the primary source per Spec FR-001. No fallback paths allowed.

- [X] T012b [US1] [Plan Revision] Update `plan.md` to remove HuggingFace references.
 - **Implementation**: In `plan.md`, replace all mentions of "Hugging Face (bee_genome_variants)" with "NCBI BioProject PRJNA639195 and PRJNA566029". Ensure Phase 0 and Summary reflect NCBI as the sole source.
 - **Rationale**: Resolve conflict between Spec (NCBI) and Plan (HF).

- [X] T014 [US1] Implement alignment and variant calling pipeline in `code/02_align_call.sh` (FR-002).
 - **Input**: `data/raw/fastq_files` (from T012a).
 - **Output**: `data/interim/raw_variants.vcf`.
 - **Implementation**:
 1. Align reads to reference genome `Amel_HAv3.1` using `bwa mem`.
 2. Call variants using `FreeBayes`.
 3. Filter to high-quality biallelic SNPs (QUAL > 30, depth ≥ 10) using `bcftools`.
 - **Note**: This task is critical for producing the VCF required by T015.

- [X] T045 [P] [US1] [Validation Only] Implement `code/00_generate_simulated_fastq.py` to simulate FASTQ for *validation/testing* of the alignment pipeline (FR-002).
 - **Input**: `data/interim/synthetic.vcf` (generated by T009).
 - **Output**: `data/interim/synthetic_R1.fq` and `data/interim/synthetic_R2.fq`.
 - **Implementation**: Use `dwgsim` with a fixed random seed to ensure reproducibility.
 - **Command Example**: `dwgsim -e -l [READ_LENGTH] -1 350 -2 50 -N 10 -s 42 data/interim/synthetic.vcf data/interim/synthetic_R1.fq data/interim/synthetic_R2.fq`. (Insert size distribution: Normal(mean=350, std=50)).
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
 - **Note**: This task includes the logic from T044.

- [X] T063 [US1] Implement `code/03_filter_snps.py` to pre-filter SNPs to immune pathway (Candidate-Gene approach) **for annotation purposes only** (FR-003).
 - **CRITICAL WARNING**: This filtered list is **STRICTLY EXCLUDED** from the primary GWAS run (T017). T017 MUST use ALL high-quality SNPs.
 - **Input**: `data/interim/bed.bim`.
 - **Output**: `data/interim/immune_pathway_snps.txt`.
 - **Implementation**: Write a script that filters SNPs based on a provided gene list and outputs the IDs. Add a comment in the code explicitly stating: "This list is for annotation only. Do not use for GWAS."

- [X] T063b [US1] [Documentation] Add explicit exclusion note to `code/03_gwas.sh` (T017).
 - **Implementation**: Ensure T017's code comments explicitly state: "This script uses ALL SNPs from data/interim/bed.*. It does NOT use data/interim/immune_pathway_snps.txt."

- [X] T064 [US1] Implement `code/05_collinearity_diag.py` to perform collinearity diagnostics (FR-010).

- [X] T017 [US1] Create `code/03_gwas.sh` to execute PLINK logistic regression with mandatory covariates (from T046) and output raw association statistics (FR-004). Do NOT include FDR logic here; that is handled by T020. Output to `data/interim/gwas_raw.tsv`.
 - **Input**: `data/interim/bed.bim`, `data/interim/bed.fam`, `data/interim/phenotypes_cleaned.fam`.
 - **Output**: `data/interim/gwas_raw.tsv`.
 - **Note**: This task uses ALL SNPs. Do not use the filtered list from T063.

- [X] T052 [P] [US1] [Review Fix] Implement `code/utils/gwas_thresholds.py` to calculate the "Effective Number of Independent Tests (Me)" for documentation.
 - **Depends on**: T016.
 - **Rationale**: Address reviewer concern in Assumptions regarding the genome-wide significance threshold. The Spec mentions "effective number of independent tests" but the tasks only implement BH. We need a specific task to calculate Me for the honeybee genome to document the Me value used for BH context (NOT for Bonferroni correction).
 - **Implementation**:
 1. Implement a script that estimates Me using `scipy.linalg.eigh` on the correlation matrix of the LD-pruned SNPs (from T016).
 2. **Input**: `data/interim/bed_pruned.bim` (from T016).
 3. Output `data/processed/me_estimate.txt` with the calculated Me value as a **single integer**.
 4. Update `code/utils/fdr_correction.py` (T020) to read this value and log it.
 5. **MANDATORY**: This task is for documentation ONLY. It must not alter the FDR method (BH).
 - **Verification**: Verify `me_estimate.txt` exists and contains a plausible integer value for honeybee genome.

- [X] T020 [US1] Implement Benjamini-Hochberg FDR correction in `code/utils/fdr_correction.py` (FR-004).
 - **Depends on**: T017.
 - **Input**: `data/interim/gwas_raw.tsv`. MUST sort by p-value in **ascending order** before processing. P-values must be formatted to **10 decimal places**.
 - **Output**: `data/interim/gwas_fdr.tsv`.
 - **Output Schema**: Columns must be: `rank`, `raw_p`, `q_value`, `significant` (boolean).
 - **Logic**: Apply BH correction. Read Me value from `data/processed/me_estimate.txt` and log it in output metadata.

- [X] T022 [US1] Create `code/04_apply_fdr.sh` to merge PLINK raw results (T017) with FDR-corrected results (T020) into the final artifact `data/processed/gwas_results_fdr.tsv`.
 - **Depends on**: T017 and T020.
 - **Implementation**:
 1. Read `data/interim/gwas_raw.tsv` and `data/interim/gwas_fdr.tsv`.
 2. Merge on SNP ID.
 3. Write to `data/processed/gwas_results_fdr.tsv` with columns: `snp_id`, `chrom`, `pos`, `ref`, `alt`, `freq`, `p_value`, `q_value`, `significant`.
 4. Ensure all SNPs from the raw file are present, with `significant` flag set based on q-value < 0.05.
 - **Verification**: Verify `data/processed/gwas_results_fdr.tsv` exists and contains the expected columns and data.

- [X] T023 [US1] Create `code/05_document_study_design.py` to document the study design, associational nature, and covariate handling.
 - **Implementation**: Generate `data/processed/study_design.md` with explicit disclaimers (FR-009).
 - **Note**: This task replaces the ambiguous T023 shell script reference.

**Checkpoint**: US1 fully complete. Pipeline produces FDR-corrected results ready for sensitivity analysis.

---

## Phase 4: User Story 2 - Multiple Testing Correction & Threshold Sensitivity (Priority: P2)

**Goal**: Apply Benjamini-Hochberg FDR correction and test threshold sensitivity to identify robust genetic associations.

**Independent Test**: Can be independently tested by running the sensitivity analysis (T021) on the FDR-corrected GWAS output produced by Phase 3 (US1) and verifying the threshold counts and q-values are reported correctly.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for Benjamini-Hochberg implementation in `tests/unit/test_fdr_correction.py`
- [X] T019 [P] [US2] Contract test for threshold sensitivity output format in `tests/contract/test_threshold_sensitivity.py`

### Implementation for User Story 2

- [X] T021 [US2] Implement threshold sensitivity sweep across a specific set of thresholds in `code/utils/threshold_sensitivity.py` (FR-005).
 - **Depends on**: T022.
 - **Input**: `data/processed/gwas_results_fdr.tsv` (from T022).
 - **Output**: `data/processed/threshold_sensitivity.json`.
 - **Logic**: For each threshold in a set of small magnitudes, count SNPs passing and list corresponding q-values.

**Note**: FDR Correction (T020) and Merging (T022) are completed in Phase 3 (US1) to ensure US1 is self-contained. This phase focuses solely on Threshold Sensitivity (T021) and Documentation.

---

## Phase 5: User Story 3 - Machine Learning Validation & Polygenic Risk Scoring (Priority: P3)

**Goal**: Validate GWAS findings using LASSO logistic regression and compute polygenic risk scores to assess predictive performance.

**Independent Test**: Can be tested by running LASSO on a held-out test set (80/20 split) and verifying AUC is computed correctly.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US3] Unit test for LASSO AUC calculation in `tests/unit/test_lasso_auc.py`
- [X] T026 [P] [US3] Contract test for threshold sensitivity output format in `tests/contract/test_threshold_sensitivity.py`

### Implementation for User Story 3

**Note on Redundancy**: Tasks T070, T071, T072 were removed to resolve duplication. **T027-T032 are the single source of truth** for US3 implementation.

- [X] T027 [US3] Implement LASSO logistic regression with 5-fold cross-validation in `code/04_ml_validation.py` (FR-006) and report out-of-sample AUC value.
 - **Depends on**: T022.
 - **Implementation**:
 1. Split data: [deferred] training, [deferred] testing using `train_test_split` with `random_state=42` and `stratify=y`.
 2. Train LASSO on the training set using `StratifiedKFold(n_splits=5, random_state=42)` for cross-validation.
 3. Compute AUC on the held-out test set.
 4. Report AUC value. If AUC < 0.75, flag as low predictive power.
 5. **Output Artifact**: Write JSON to `data/processed/lasso_auc_report.json` with keys: `{"auc_value": float, "status": "PASS/FAIL", "flag": "low_power"}`.
 - **Input**: `data/processed/gwas_results_fdr.tsv` (from T022).
 - **Output**: `data/processed/lasso_auc_report.json`.

- [X] T027b [US3] Implement phenotype permutation to generate null distribution for AUC comparison (US-3 AC3).
 - **Depends on**: T027.
 - **Implementation**:
 1. Permute phenotype labels multiple times.
 2. For each permutation, calculate AUC using the same LASSO model.
 3. Generate null distribution and compare observed AUC.
 4. **Output Artifact**: Write JSON to `data/processed/phenotype_permutation_null.json` with keys: `{"observed_auc": float, "null_distribution": [float], "p_value": float}`.
 5. **Merged Output**: Also write `data/processed/validation_metrics.json` with keys: `{"auc": float, "null_p_value": float, "flag": "low_power"}`.
 - **Input**: `data/processed/lasso_auc_report.json`.
 - **Output**: `data/processed/phenotype_permutation_null.json`, `data/processed/validation_metrics.json`.

- [X] T028 [US3] Implement Polygenic Risk Score (PRS) calculation in `code/04_ml_validation.py` (FR-007).
 - **Depends on**: T022.
 - **Input**: `data/processed/gwas_results_fdr.tsv` (from T022).
 - **Output**: `data/processed/prs_scores.tsv`.
 - **Implementation**: Calculate PRS for each colony based on significant SNPs.
 - **Output Schema**: Columns must be: `colony_id`, `prs_score`, `p_value`.

- [X] T029 [US3] Implement likelihood-ratio test for PRS improvement over covariates-only model in `code/04_ml_validation.py` (FR-007).
 - **Depends on**: T028.
 - **Input**: `data/processed/prs_scores.tsv` (from T028).
 - **Output**: `data/processed/prs_lr_test.json`.
 - **Output Schema**: Columns must be: `chi_sq`, `p_value`, `df`, `significant`.

- [X] T031 [US3] Implement collinearity diagnostics (VIF) for covariates (geographic region, sampling year) in `code/04_ml_validation.py` (FR-010, US-3 AC4).
 - **Input**: `data/interim/phenotypes_cleaned.fam`.
 - **Output**: `data/processed/collinearity_report.json`.
 - **Output Schema**: `{"vif_values": {"region": float, "year": float}, "correlation_matrix": [[float]]}`.

- [X] T032 [US3] Implement `code/05_annotation.py` to map significant SNPs to genes using Ensembl Bees API v104 and query GO terms (FR-008).
 - **Input**: `data/interim/immune_pathway_snps.txt` (from T063).
 - **Output**: `data/processed/annotation_results.tsv`.
 - **Implementation**:
 1. Use Ensembl Bees API **v104**.
 2. If a SNP maps to multiple genes, select the one with the shortest genomic distance.
 3. If a SNP maps to **no genes**, assign the value **'INTERGENIC'** in the output schema.
 4. If the API is unavailable, assign **'UNAVAILABLE'**.
 - **Output Schema**: Columns must be: `snp_id`, `gene_symbol`, `distance`, `go_terms`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T033a [P] Create `docs/pipeline_execution_guide.md` with step-by-step execution instructions.
 - **Update**: Ensure instructions reference `code/utils/fdr_correction.py` (T020) and `code/04_ml_validation.py` (T027) directly, not wrapper scripts.
- [X] T033b [P] Create `docs/data_dictionary.md` defining all data artifacts and schemas
- [X] T034 [P] Code cleanup and refactoring of shell scripts for portability (Depends on T014, T017, T022).
- [X] T041 [P] Profile pipeline with `cProfile` and generate `data/processed/profile_report.txt`.
 - **Verification**: MUST verify CPU time; **DO NOT** verify wall-clock time here. Wall-clock verification is handled by T089.
 - **Note**: This task is for CPU profiling only.
- [X] T042 [P] Refactor `code/02_align_call.sh` to use parallel processing if profile shows I/O bottleneck (Depends on T041).
- [X] T036 [P] Additional unit tests for edge cases (missing Varroa data, all SNPs filtered) in `tests/unit/`.
- [X] T037 [P] Run quickstart.md validation to ensure reproducibility.
- [X] T038 [P] Create `docs/report_template.md` to include the mandatory disclaimer text: "Findings are associational, not causal..." (FR-009)
- [X] T051 [P] [Review Fix] Update `code/01_download.py` (T012a) to explicitly log the exact number of samples with Varroa data vs total samples before the `ERR_VARROA_COVARIATE_MISSING` check.
- [X] T061 [P] [Review Fix] Update `code/05_annotation.py` (T032) to handle "no gene found" cases explicitly.

**Note on GPU Constraint**: Task T074 was removed to align with the Spec's explicit Assumption that "No GPU or CUDA accelerators are required" and to prevent architectural drift. The project remains CPU-tractable.

- [X] T089 [P] [Final Check] Implement `code/07_wall_clock_timer.py` to wrap the full pipeline execution.
 - **Implementation**: Use `time.perf_counter` to measure total runtime from start to finish. Log results to `data/processed/runtime_log.json`.
 - **Verification**: Ensure the log includes start time, end time, and total duration.
 - **Output Schema**: `{"start_time": "ISO8601", "end_time": "ISO8601", "duration_seconds": float, "unit": "seconds"}`.

---

## Phase O: Plan Alignment & Documentation (Revision)

**Purpose**: Resolve conflicts between Spec and Plan regarding Candidate-Gene filtering and ensure documentation reflects the governing Spec requirements.

- [ ] T082 [P] [Plan Revision] Update `plan.md` to remove "Candidate-Gene Pre-filtering" from the "Complexity Tracking" table and the "Critical Methodological Adjustment" section.
 - **Specific Action**: Delete the entire "Critical Methodological Adjustment" section (lines 15-25 in plan.md) and remove the "Candidate-Gene Pre-filtering" row from the "Complexity Tracking" table.
 - **Rationale**: The Spec (FR-004) requires GWAS on all high-quality SNPs. The Plan's suggestion to pre-filter for the primary GWAS contradicts the Spec. The Candidate-Gene approach is correctly implemented in T063 *only* for annotation, not for the statistical test.

- [ ] T083 [P] [Plan Revision] Update `plan.md` Phase 3 to explicitly state that LASSO uses `StratifiedKFold(n_splits=5)` and a concrete 80/20 split, removing the "[deferred] split" language.
 - **Specific Action**: In Phase 3, replace "LASSO logistic regression on held-out validation set ([deferred] split)" with "LASSO logistic regression on held-out validation set (80/20 split, StratifiedKFold(n_splits=5))".

- [ ] T084 [P] [Plan Revision] Reorder Phase 1 in `plan.md` to ensure Power Analysis runs *before* Data Fetch, matching the task list gate (T043).
 - **Specific Action**: In Phase 1, move the "Power Analysis" bullet to appear before "Download data from HF/NCBI".

- [ ] T085 [P] [Plan Revision] Update `plan.md` to remove the Hugging Face dataset ID 'bee_genome_variants' and replace it with NCBI BioProject IDs PRJNA639195/566029.
 - **Specific Action**: In Summary and Phase 0/1, replace "Hugging Face (bee_genome_variants)" with "NCBI BioProject PRJNA639195 and PRJNA566029".

- [ ] T086 [P] [Plan Revision] Update `plan.md` Phase 2 and 3 to reflect that FDR and Merging (T020, T022) occur after the initial GWAS run, aligning with the Task list phases (US1 -> US2).
 - **Specific Action**: In Phase 2, remove "Apply FDR". In Phase 3, add "Apply FDR and Merge results".

- [ ] T087 [P] [Plan Revision] Update `plan.md` Technical Context to specify Ensembl Bees API v104.
 - **Specific Action**: In Technical Context, update "Ensembl Bees API" to "Ensembl Bees API v104".

- [ ] T088 [P] [Plan Revision] Update `plan.md` to remove the 'Critical Methodological Adjustment' section entirely, as it contradicts the Spec.
 - **Specific Action**: Delete the section titled "Critical Methodological Adjustment" and its content.

- [ ] T089 [P] [Final Check] Implement `code/07_wall_clock_timer.py` to wrap the full pipeline execution.
 - **Implementation**: Use `time.perf_counter` to measure total runtime from start to finish. Log results to `data/processed/runtime_log.json`.
 - **Verification**: Ensure the log includes start time, end time, and total duration.

- [ ] T090 [P] [Plan Revision] Update `plan.md` to reference `code/07_wall_clock_timer.py` (T089) for runtime verification, removing the claim that `cProfile` verifies wall-clock limits.
 - **Specific Action**: In Phase N, replace "cProfile verifies wall-clock limits" with "T089 (wall_clock_timer.py) verifies runtime limits".

- [ ] T091 [P] [Plan Revision] Update `plan.md` to ensure the sequence of Power Analysis -> Data Fetch is explicit in Phase 1.
 - **Specific Action**: In Phase 1, explicitly state "Run Power Analysis (T005) BEFORE Data Fetch (T012a)".

- [ ] T092 [P] [Plan Revision] Update `plan.md` to remove the 'Data Size Check' (760GB) and replace it with a 'Sample Count Check' (n < 80) in the data fetch description.
 - **Specific Action**: In Data Fetch description, replace "Check data size" with "Check sample count (n >= 80)".

---

## Phase P: Final Validation & Handoff

**Purpose**: Ensure the project is ready for execution and meets all constitutional requirements.

- [ ] T095 [P] [Final Check] Run a dry-run of the full pipeline on the synthetic dataset to verify all paths (data fetch -> alignment -> GWAS -> FDR -> ML -> Annotation) execute without error.
 - **Implementation**: Execute `code/00_generate_synthetic_data.py` -> `code/00_generate_simulated_fastq.py` -> `code/02_align_call.sh` -> `code/03_gwas.sh` -> `code/utils/fdr_correction.py` -> `code/04_ml_validation.py` -> `code/05_annotation.py`.
 - **Verification**: Verify all output artifacts exist: `data/processed/gwas_results_fdr.tsv`, `data/processed/lasso_auc_report.json`, `data/processed/prs_scores.tsv`, `data/processed/annotation_results.tsv`, `data/processed/validation_metrics.json`, `data/processed/collinearity_report.json`, `data/processed/runtime_log.json`.

- [ ] T096 [P] [Final Check] Verify that `code/01_download.py` (T012a) strictly adheres to the "fail loud" rule: if the NCBI fetch fails, it MUST raise an exception and NOT fall back to synthetic data.
 - **Implementation**: Review `code/01_download.py` for any `try/except` blocks that catch fetch errors and return synthetic data. Remove such blocks.
 - **Rationale**: The Constitution mandates that failed real data fetches must halt the pipeline, not substitute fake data.

- [ ] T097 [P] [Final Check] Confirm that the power analysis (T005) and Varroa coverage check (T062) are executed in the correct order and that their exit codes are properly propagated to the main run-book.
 - **Implementation**: Verify `docs/quickstart.md` calls `code/04_check_power_and_halt.sh` and `code/02_harmonize_phenotypes.py` in sequence before proceeding to alignment.

- [ ] T098 [P] [Final Check] Verify that `code/07_wall_clock_timer.py` (T089) correctly measures total runtime and logs it to `data/processed/runtime_log.json`.
 - **Implementation**: Run the pipeline with the timer and verify the log file contains valid start/end times and duration.

- [ ] T099 [P] [Final Check] Verify that `plan.md` has been updated to reflect NCBI as the primary source, 5-fold CV, and the removal of the 'Critical Methodological Adjustment' section.
 - **Implementation**: Check `plan.md` for the presence of PRJNA639195/566029, `StratifiedKFold`, and absence of the pre-filtering justification.

- [ ] T100 [P] [Final Check] Verify that `tasks.md` accurately reflects the dependency chain: Power Analysis (T005/T043) -> Data Fetch (T012a) -> Alignment (T014) -> GWAS (T017) -> FDR (T020) -> ML (T027).
 - **Implementation**: Review the task list to ensure no task attempts to use output from a task that hasn't been marked complete yet.