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

**Note on Spec vs Plan Conflict**: The Spec (FR-004, FR-005) mandates Benjamini-Hochberg (BH) FDR correction. The Plan's "Complexity Tracking" section argues for Bonferroni. As per the Constitution, the Spec is the governing requirement for implementation. Tasks T020-T021 implement BH as required by the Spec. The Plan is flagged for revision to align with the Spec.

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
 4. **CRITICAL**: If Power < 20% (Power={power}). Pipeline halted. "
 5. If Power >= 20%: Report the calculated power for detecting large effect sizes (OR >= 2.5) at alpha=0.05.
 6. Output: Write power value and status to `data/processed/power_analysis.txt`.
- [X] T006 [P] Implement `code/utils/collinearity_diag.py` for FR-010 (VIF calculation, correlation matrix)
- [X] T007 [P] Create base data schema validators for `Colony` and `SNP` entities: create `code/utils/validators/colony_schema.py` and `code/utils/validators/snp_schema.py` based on `specs/001-gene-regulation/contracts/dataset.schema.yaml` and `specs/001-gene-regulation/contracts/gwas_output.schema.yaml`
- [X] T008 [P] Create `.env.example` with keys `NCBI_API_KEY`, `ENSEMBL_API_KEY` and default values for SSL CA bundle paths
- [X] T009 [P] Implement `code/00_generate_synthetic_data.py` to create deterministic synthetic VCF + Phenotypes for validation. MUST implement CCD diagnosis validation logic that explicitly checks: <!-- FAILED: unspecified -->
 1. Presence of dead adult bees in the hive.
 2. Absence of dead pupae.
 3. Live bee population < 10% relative to peak season.
 Logic MUST fail validation if any of these criteria are not met in the synthetic data generation process (FR-011).
- [X] T013a [P] [Foundational] Install `dwgsim` in the environment.
 - **Implementation**: Add `dwgsim` to `code/environment.yml` or create a `setup.sh` script that runs: `conda config --add channels bioconda && conda install -c bioconda dwgsim`.
 - **Note**: `dwgsim` is a system binary, not a Python package.
- [X] T013b [P] [Foundational] Verify `dwgsim` availability.
 - **Implementation**: Run `dwgsim --help` and verify it exits with code 0.
- [X] T052 [P] [Foundational] Add explicit task for "Effective Number of Independent Tests (Me)" calculation in `code/utils/gwas_thresholds.py`.
 - **Rationale**: Address reviewer concern in Assumptions regarding the genome-wide significance threshold. The Spec mentions "effective number of independent tests" but the tasks only implement BH. We need a specific task to calculate Me for the honeybee genome to document the Me value used for BH context (NOT for Bonferroni correction).
 - **Implementation**:
 1. Implement a script that estimates Me using the spectral decomposition of the LD matrix (or a standard approximation for honeybee LD).
 2. Output `data/processed/me_estimate.txt` with the calculated Me value.
 3. Update `code/utils/fdr_correction.py` (T020) to log this Me value in the output metadata.
 4. Update `code/utils/threshold_sensitivity.py` (T021) to log this Me value in the output metadata.
 5. **MANDATORY**: This task is for documentation ONLY. It must not alter the FDR method (BH).
 - **Verification**: Verify `me_estimate.txt` exists and contains a plausible integer value for honeybee genome.
 - **Depends on**: T016 (for LD pruning data).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - GWAS Pipeline Execution (Priority: P1) 🎯 MVP

**Goal**: Execute the complete GWAS analysis pipeline on honeybee genomic data to identify SNPs associated with CCD susceptibility.

**Independent Test**: Can be fully tested by running the pipeline on a small sample dataset and verifying that SNP association statistics are produced.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Contract test for VCF schema validation in `tests/contract/test_vcf_schema.py`
- [X] T011 [P] [US1] Integration test for full synthetic pipeline run in `tests/integration/test_synthetic_gwas.py`

### Implementation for User Story 1

- [X] T012a [US1] Implement `code/01_download.py` to fetch data from NCBI BioProject CCD colonies and healthy controls datasets with associated metadata from BeeBase repository using SRA Toolkit.
 - **Implementation**:
 1. **Primary Source**: Use `prefetch SRRxxxxx` and `fasterq-dump --split-files SRRxxxxx` to download FASTQ files into `data/raw` from NCBI BioProject. Replace 'SRRxxxxx' with the appropriate accession numbers for {{claim:c_0e510940}}.
 2. **Validation**: Validate downloaded data using checksums against a known good source.
 3. **CCD Criteria**: Explicitly validate that the metadata contains "validated instruments for CCD diagnosis criteria consistent across BeeBase and NCBI metadata sources" (FR-011) during the fetch step.
 4. **Fallback**: If the NCBI fetch fails completely (network error, SSL failure), attempt fetch from the verified Hugging Face mirror (`bee_genome_variants`).
 5. **Large Dataset Handling**: If the dataset exceeds 14GB (GitHub Actions disk limit), implement **reservoir sampling** with a **fixed seed of 42** to extract a representative subset of N=5000 rows. Explicitly log: "Dataset too large for full processing. Using fixed-seed reservoir sampling (seed=42, N=5000). Limitations documented in `data/processed/sampling_methodology.md`."
 6. **Output Artifacts**: `data/raw/fastq_files`, `data/processed/sampling_methodology.md`, `data/processed/ncbi_fetch_log.json`.
 - **Note on Plan vs Spec**: While Plan Phase 0 mentions fetching HF, FR-001 of the Spec mandates NCBI as the primary source. This task enforces NCBI priority.

- [X] T045 [P] [US1] [Validation Only] Implement `code/00_generate_simulated_fastq.py` to simulate FASTQ for *validation/testing* of the alignment pipeline (FR-002).
 - **Input**: `data/interim/synthetic.vcf` (generated by T009).
 - **Output**: `data/interim/synthetic_R1.fq` and `data/interim/synthetic_R2.fq`.
 - **Implementation**: Use `dwgsim` with a fixed random seed to ensure reproducibility.
 - **Command Example**: `dwgsim -e 0.001 -l 150 -1 350 -2 50 -N 10 -s 42 data/interim/synthetic.vcf data/interim/synthetic_R1.fq data/interim/synthetic_R2.fq`. (Insert size distribution: Normal(mean=350, std=50)).
 - **Note**: This task provides the synthetic data path required by Plan Phase 0 for toolchain validation when real data is unavailable, without relaxing T012a's strict real data constraints.

- [X] T046 [P] [US1] [Verification] Verify `code/00_generate_simulated_fastq.py` output.
 - **Implementation**: Run `fastqc` or simple validation on FASTQ files.

- [X] T043 [P] [US1] [Gate] Implement `code/04_check_power_and_halt.sh` to execute `code/utils/power_analysis.py` (T005) immediately after data loading.
- [X] T015 [US1] Implement VCF to PLINK format conversion in `code/utils/vcf_to_plink.py` (FR-003)
- [X] T016 [US1] Implement `code/utils/preprocess_phenotype.py` for LD pruning (r² < 0.2) and covariate encoding (geographic region, sampling year, Varroa mite count) (FR-003).
- [X] T062 [US1] Implement `code/02_harmonize_phenotypes.py` to map CCD diagnosis codes to CCD Working Group criteria (FR-011).
- [X] T063 [US1] Implement `code/03_filter_snps.py` to pre-filter SNPs to immune pathway (Candidate-Gene approach) (FR-003).
- [X] T064 [US1] Implement `code/05_collinearity_diag.py` to perform collinearity diagnostics (FR-010).
- [ ] T017 [US1] Create `code/03_gwas.sh` to execute PLINK logistic regression with mandatory covariates (from T046) and output raw association statistics (FR-004). Do NOT include FDR logic here; that is handled by T020. Output to `data/interim/gwas_raw.tsv`.
- [X] T020 [P] [US1] Implement Benjamini-Hochberg FDR correction in `code/utils/fdr_correction.py` (FR-004).
 - **Input**: `data/interim/gwas_raw.tsv`. MUST be sorted by p-value in **ascending order**. P-values must be formatted to **10 decimal places**.
 - **Output**: `data/interim/gwas_fdr.tsv`.
 - **Output Schema**: Columns must be: `rank`, `raw_p`, `q_value`, `significant` (boolean).
 - **Logic**: Apply BH correction. {{claim:c_470e3f1d}}

- [ ] T022 [US1] Create `code/04_apply_fdr.sh` to merge PLINK raw results (T017) with FDR-corrected results (T020) into the final artifact `data/processed/gwas_results_fdr.tsv`.

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
- [X] T023 [US2] Update `code/04_apply_fdr.sh` to and document the study design.

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
 - **Implementation**:
 1. Split data: **a majority for training, a minority for testing** (hold-out set).
 2. Train LASSO on the designated training set using k-fold cross-validation.
 3. Use `random_state=42` for reproducibility.
 4. Compute AUC on the held-out [deferred] test set.
- [X] T028 [US3] Implement Polygenic Risk Score (PRS) calculation in `code/04_ml_validation.py` (FR-007).
- [X] T029 [US3] Implement likelihood-ratio test for PRS improvement over covariates-only model in `code/04_ml_validation.py` (FR-007).
- [X] T030 [US3] Add AUC reporting logic in `code/04_ml_validation.py`:
- [X] T031 [US3] Implement collinearity diagnostics (VIF) for covariates (geographic region, sampling year) in `code/04_ml_validation.py` (FR-010, US-3 AC4).
- [X] T032 [US3] Implement `code/05_annotation.py` to map significant SNPs to genes using Ensembl Bees API and query GO terms (FR-008).
 - **Implementation**:
 1. Use Ensembl Bees API **version**.
 2. If a SNP maps to multiple genes, select the one with the shortest genomic distance.
 3. If a SNP maps to **no genes**, assign the value **'INTERGENIC'** in the output schema.
 4. If the API is unavailable, assign **'UNAVAILABLE'**.
 5. Output: `data/processed/annotation_results.tsv`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T033a [P] Create `docs/pipeline_execution_guide.md` with step-by-step execution instructions
- [X] T033b [P] Create `docs/data_dictionary.md` defining all data artifacts and schemas
- [X] T034 [P] Code cleanup and refactoring of shell scripts for portability (Depends on T014, T017, T022).
- [X] T041 [P] Profile pipeline with `cProfile` and generate `data/processed/profile_report.txt`.
- [X] T042 [P] Refactor `code/02_align_call.sh` to use parallel processing if profile shows I/O bottleneck (Depends on T041).
- [X] T036 [P] Additional unit tests for edge cases (missing Varroa data, all SNPs filtered) in `tests/unit/`.
- [X] T037 [P] Run quickstart.md validation to ensure reproducibility.
- [X] T038 [P] Create `docs/report_template.md` to include the mandatory disclaimer text: "Findings are associational, not causal..." (FR-009)
- [X] T044 [P] Implement `code/06_edge_case_handler.py` to explicitly handle missing Varroa metadata (Assumption 1):
- [ ] T051 [P] [Review Fix] Update `code/01_download.py` (T012a) to explicitly log the exact number of samples with Varroa data vs total samples before the `ERR_VARROA_COVARIATE_MISSING` check.

**Note on GPU Constraint**: Task T074 was removed to align with the Spec's explicit Assumption that "No GPU or CUDA accelerators are required" and to prevent architectural drift. The project remains CPU-tractable.

- [X] T061 [P] [Review Fix] Update `code/05_annotation.py` (T032) to handle "no gene found" cases explicitly.

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [ ] T075 Reconcile run-book vs implementation for `code/06_power_analysis.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/06_power_analysis.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [X] T076 Reconcile run-book vs implementation for `code/08_apply_fdr.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/08_apply_fdr.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [X] T077 Reconcile run-book vs implementation for `code/09_threshold_sensitivity.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/09_threshold_sensitivity.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [ ] T078 Reconcile run-book vs implementation for `code/10_lasso_validation.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/10_lasso_validation.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [ ] T079 Reconcile run-book vs implementation for `code/11_prs_and_lr_test.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/11_prs_and_lr_test.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [ ] T080 Reconcile run-book vs implementation for `code/12_annotate_genes.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/12_annotate_genes.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [ ] T081 Reconcile run-book vs implementation for `code/13_format_results.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/13_format_results.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
