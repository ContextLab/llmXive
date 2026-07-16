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
 3. If n >= 80: Report calculated power in `data/processed/power_analysis.txt` as a single line: "Power: X.XX".
 4. Do NOT halt on Power < 0.20; only report it.
- [X] T006 [P] Implement `code/utils/collinearity_diag.py` for FR-010 (VIF calculation, correlation matrix)
- [X] T007 [P] Create base data schema validators for `Colony` and `SNP` entities: create `code/utils/validators/colony_schema.py` and `code/utils/validators/snp_schema.py` based on `specs/001-gene-regulation/contracts/dataset.schema.yaml` and `specs/001-gene-regulation/contracts/gwas_output.schema.yaml`
- [X] T008 [P] Create `.env.example` with keys `NCBI_API_KEY`, `ENSEMBL_API_KEY` and default values for SSL CA bundle paths
- [X] T009 [P] Implement `code/00_generate_synthetic_data.py` to create deterministic synthetic VCF + Phenotypes for validation. MUST implement CCD diagnosis validation logic that explicitly checks:
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

- [X] T012 [US1] Implement `code/01_download.py` to fetch data from NCBI BioProject PRJNA with SSL verification (FR-001). MUST halt with clear error on SSL failure. If SSL fails, fall back to synthetic path (T009). If SSL succeeds, download real data and proceed to T012b.
  - **Implementation**: Verify SSL certificates using a verified CA bundle. If verification fails, halt with error. If verification succeeds, download real data and proceed to T012b.
- [X] T012b [US1] Implement logic to route real data to alignment. If `code/01_download.py` successfully downloads real data, this task ensures the pipeline proceeds to `code/02_align_call.sh` (T014) with the real files, rather than defaulting to synthetic.
  - **Input**: Real FASTQ/VCF from T012.
  - **Output**: Trigger T014 with real data path.
  - **Depends on**: T012.
- [X] T013 [US1] Implement `code/00_generate_simulated_fastq.py` to simulate FASTQ to enable FR-002.
  - **Input**: `data/interim/synthetic.vcf` (generated by T009).
  - **Output**: `data/interim/synthetic_R1.fastq` and `data/interim/synthetic_R2.fastq`.
  - **Implementation**: Install dwgsim via conda-forge: `conda install -c bioconda dwgsim`. Use `dwgsim` with seed 42. Command: `dwgsim -e 0.02 -d 500 -s 42 -N 1000000 data/interim/synthetic.vcf data/interim/synthetic`.
  - **Verification**: Ensure output files exist and contain valid FASTQ format.
  - **Depends on**: T009.
- [X] T014 [US1] Create `code/02_align_call.sh` to wrap `bwa mem` (alignment) and `FreeBayes` (variant calling) with QUAL > 30 and depth ≥ 10 filters (FR-002). MUST accept input from either `data/interim/real_*.fastq` (T012/T012b) or `data/interim/synthetic_*.fastq` (T013).
  - **Implementation**: Ensure bwa and freebayes are installed via conda-forge (`conda install -c bioconda bwa freebayes`) and available in PATH before execution.
- [X] T015 [US1] Implement VCF to PLINK format conversion in `code/utils/vcf_to_plink.py` (FR-003)
- [X] T016 [US1] Implement LD pruning (r² < 0.2) for population structure correction only and covariate encoding (geographic region, sampling year, Varroa load) in `code/utils/preprocess_phenotype.py` (FR-003).
  - Input: Phenotype data from T009 (synthetic) or T012 (real).
  - Output: `data/processed/phenotypes_cleaned.fam` and `data/processed/phenotypes_cleaned.pheno`.
  - **MANDATORY**: MUST include geographic region, sampling year, and Varroa mite count in the model.
  - **MANDATORY**: MUST NOT substitute these covariates with PCA. This is derived from Spec FR-003 and US-1 AC1, which mandate specific covariates. The Plan's PCA fallback is an implementation detail superseded by the Spec's mandatory requirement.
  - **MANDATORY**: MUST NOT drop covariates due to collinearity.
  - **MANDATORY**: Implement a pre-check that calculates VIF; if VIF > 5, raise a custom error `ERR_COVARIATE_COLLINEARITY_HIGH` instead of proceeding to PLINK, ensuring the pipeline halts rather than dropping variables.
- [X] T043 [US1] Implement `code/04_check_power_and_halt.sh` to execute `code/utils/power_analysis.py` (T005) immediately after data loading. MUST halt the pipeline with `ERR_SAMPLE_SIZE_INSUFFICIENT` if n < 80 BEFORE any GWAS execution (T017) runs. This task enforces FR-012 halt logic for insufficient sample size (n < 80) and reports power for n >= 80.
  - **Depends on**: T009, T012, T012b.
- [X] T017 [US1] Create `code/03_gwas.sh` to execute PLINK logistic regression with covariates and output raw association statistics (FR-004). Do NOT include FDR logic here; that is handled by T022. Output to `data/interim/gwas_raw.tsv`.

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
  - **MANDATORY**: MUST implement BH correction. This overrides any plan.md deviation (Complexity Tracking) to comply with Spec FR-004.
  - Output: q-values for all SNPs.
- [X] T021 [US2] Implement threshold sensitivity sweep across specific thresholds: 1×10⁻⁷, 5×10⁻⁸, 1×10⁻⁸ in `code/utils/threshold_sensitivity.py` (FR-005).
  - **Implementation**: Explicitly sweep the thresholds {1×10⁻⁷, 5×10⁻⁸, 1×10⁻⁸}. Do not use a generic range.
  - Output: Write a report to `data/processed/threshold_sensitivity_report.tsv` containing counts and q-values for each threshold.
- [X] T022 [US2] Create `code/04_apply_fdr.sh` to post-process `data/interim/gwas_raw.tsv` using T020. Pipe PLINK output to `code/utils/fdr_correction.py` and write final results to `data/processed/gwas_results_fdr.tsv` (FR-004, FR-005).
- [X] T023 [US2] Update `code/04_apply_fdr.sh` to flag SNPs with q < 0.05 as significant.
  - **MANDATORY**: MUST inject the mandatory disclaimer text "Findings are associational, not causal..." into the final report output (FR-009, US-2 AC4).
  - **MANDATORY**: MUST modify the output generation function to prepend this text to the header of `data/processed/gwas_results_fdr.tsv`.
  - **MANDATORY**: Document the correction method used (BH) and its impact on discovery rate.

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
    - Load PRS and covariates from `data/processed/gwas_results_fdr.tsv` and `data/processed/phenotypes_cleaned.fam`.
    - Fit full model (PRS + covariates) and reduced model (covariates only).
    - Perform likelihood-ratio test.
    - Assert p-value < 0.05 if PRS is predictive, or report non-significance.
    - Save test results to `data/processed/prs_validation_results.json`.
    - Assert output matches schema in `contracts/gwas_output.schema.yaml`.
  - **Verification**: Ensure the test file exists and runs successfully with `pytest`.
  - **Depends on**: T027, T028, T029, T030, T031.

### Implementation for User Story 3

- [X] T027 [P] [US3] Implement LASSO logistic regression with k-fold cross-validation. in `code/04_ml_validation.py` (FR-006) and report out-of-sample AUC value
- [X] T028 [US3] Implement Polygenic Risk Score (PRS) calculation in `code/04_ml_validation.py` (FR-007)
- [X] T029 [US3] Implement likelihood-ratio test for PRS improvement over covariates-only model in `code/04_ml_validation.py` (FR-007)
- [X] T030 [US3] Add AUC threshold logic in `code/04_ml_validation.py`:
  - Generate null distribution via 1000 phenotype permutations (seed=42).
  - Compare AUC against a high quantile of the null distribution.
  - **MANDATORY**: Use random seed 42 for the 1000 permutations to ensure reproducible null distribution generation.
  - **MANDATORY**: Report the AUC value and the comparison result. Do NOT flag based on an arbitrary 0.75 threshold; the spec requires reporting and comparison, not a hard fail on a specific value.
  - **Depends on**: T027, T028, T029.
- [X] T031 [US3] Implement collinearity diagnostics (VIF) for covariates (geographic region, sampling year) in `code/04_ml_validation.py` (FR-010, US-3 AC4).
  - **MANDATORY**: MUST implement VIF calculation and flag relationships where r² > 0.8 in the output artifact `data/processed/collinearity_report.tsv`.
  - **MANDATORY**: Document findings descriptively, framing joint relationships as such rather than independent effects.
- [X] T032 [US3] Implement `code/05_annotation.py` to map significant SNPs to genes using Ensembl Bees API and query GO terms (FR-008).
  - **MANDATORY**: Output `data/processed/annotated_snps.tsv` with columns: rs_id, gene_symbol, go_terms, pathway.

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
  - **Implementation**: Run `python -m cProfile -o data/processed/profile.prof code/utils/gwas_core.py` (the Python entry point called by `code/03_gwas.sh`). Use `pstats` to generate `data/processed/profile_report.txt`.
  - **Output**: `data/processed/profile_report.txt`.
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
  - Read metadata from T009/T012.
  - If < 80% of the total cohort has Varroa data (i.e., > 20% missing), raise `ERR_VARROA_COVARIATE_MISSING`.
  - If missing for ≤ 20%, exclude those samples from the covariate model but retain for genotype-only analysis.
  - Log all exclusions to `data/processed/exclusion_log.txt`.
- [X] T046 [P] Implement `code/08_collinearity_guard.py` to enforce the "No PCA substitution" rule (T016):
  - Parse `data/processed/collinearity_report.tsv` (T031).
  - If VIF > 5 for any covariate pair, raise a hard error `ERR_COVARIATE_COLLINEARITY_HIGH` unless the covariates are explicitly flagged as "definitional" in `docs/data_dictionary.md`.
  - Ensure the pipeline never silently switches to PCA if VIF is high; it must fail loudly to force manual review of the covariate strategy.
  - **Note**: This task depends on T031 and is NOT marked [P].
- [X] T047 [P] [Polish] Implement `code/07_runbook_generator.py` to generate a deterministic execution runbook for GitHub Actions (FR-004, US-1 AC3).
  - **Implementation**:
    - Assume Ubuntu 22.04 runner.
    - Read `code/requirements.txt` and `code/00_generate_simulated_fastq.py` (T013).
    - Generate a single bash script `runbook.sh` that:
      1. Installs dependencies (Include `apt-get install` or `conda install` commands for bwa, freebayes, plink2).
      2. Generates synthetic data (T009).
      3. Generates FASTQ (T013).
      4. Runs alignment/calling (T014).
      5. Converts to PLINK (T015).
      6. Runs power analysis (T043) and halts if needed.
      7. Runs GWAS (T017).
      8. Applies FDR (T022).
      9. Runs ML validation (T027-T031).
      10. Runs annotation (T032).
    - Include explicit `set -e` and timeout checks to ensure 6h limit compliance.
  - **Output**: `runbook.sh` and `docs/runbook_validation.md`.
  - **Depends on**: T009, T013, T014, T017, T022, T027, T028, T029, T030, T031.
- [X] T048 [P] [Polish] Implement `tests/unit/test_runbook_idempotency.py` to verify the runbook produces identical results on re-run (Constitution Principle I).
  - **Implementation**:
    - Execute `runbook.sh` twice in isolated directories.
    - Compare checksums of all output artifacts in `data/processed/`.
    - Assert all checksums match.
  - **Output**: `data/processed/idempotency_report.txt`.

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