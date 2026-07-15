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
- [X] T006 [P] Implement `code/utils/collinearity_diag.py` for FR-010 (VIF calculation, correlation matrix)
- [X] T007 [P] Create base data schema validators for `Colony` and `SNP` entities: create `code/utils/validators/colony_schema.py` and `code/utils/validators/snp_schema.py` based on `specs/001-gene-regulation/contracts/dataset.schema.yaml` and `specs/001-gene-regulation/contracts/gwas_output.schema.yaml`
- [X] T008 [P] Create `.env.example` with keys `NCBI_API_KEY`, `ENSEMBL_API_KEY` and default values for SSL CA bundle paths
- [X] T009 [P] Implement `code/00_generate_synthetic_data.py` to create deterministic synthetic VCF + Phenotypes for validation. MUST implement CCD diagnosis validation logic that explicitly checks: <!-- FAILED: unspecified -->
 1. Presence of dead adult bees in the hive.
 2. Absence of dead pupae.
 3. Live bee population < 10% relative to peak season.
 Logic MUST fail validation if any of these criteria are not met in the synthetic data generation process (FR-011).
- [ ] T043 [P] Implement `code/04_check_power_and_halt.sh` to execute `code/utils/power_analysis.py` (T005) immediately after data loading. MUST halt the pipeline with `ERR_SAMPLE_SIZE_INSUFFICIENT` if n < 80 BEFORE any GWAS execution (T017) runs. This task enforces FR-012 halt logic early in the pipeline.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - GWAS Pipeline Execution (Priority: P1) 🎯 MVP

**Goal**: Execute the complete GWAS analysis pipeline on honeybee genomic data (real or synthetic) to identify SNPs associated with CCD susceptibility.

**Independent Test**: Can be fully tested by running the pipeline on the synthetic dataset and verifying that SNP association statistics are produced with correct schema.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: These tests ensure the pipeline handles data ingestion, alignment, and variant calling correctly.

- [ ] T010 [P] [US1] Contract test for VCF schema validation in `tests/contract/test_vcf_schema.py`
- [ ] T011 [P] [US1] Integration test for full synthetic pipeline run in `tests/integration/test_synthetic_gwas.py` <!-- FAILED: unspecified -->

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/01_download.py` to fetch data from NCBI BioProject PRJNA/PRJNA566029 with SSL verification (FR-001). MUST halt with clear error on SSL failure. If SSL fails and fallback is explicitly configured, proceed to synthetic path; otherwise, halt.
- [~] T013 [US1] Implement `code/00_generate_simulated_fastq.py` to simulate FASTQ to enable FR-002. Read `data/interim/synthetic.vcf` (generated by T009) and output `data/interim/synthetic_R1.fastq` and `data/interim/synthetic_R2.fastq` using `dwgsim` with seed 42.
- [X] T014 [US1] Create `code/02_align_call.sh` to wrap `bwa mem` (alignment) and `FreeBayes` (variant calling) with QUAL > 30 and depth ≥ 10 filters (FR-002). MUST accept input from either `data/interim/real_*.fastq` (T012) or `data/interim/synthetic_*.fastq` (T013).
- [X] T015 [US1] Implement VCF to PLINK format conversion in `code/utils/vcf_to_plink.py` (FR-003)
- [X] T016 [US1] Implement LD pruning (r² < 0.2) for population structure correction only and covariate encoding (geographic region, sampling year, Varroa load) in `code/utils/preprocess_phenotype.py` (FR-003).
 - Input: Phenotype data from T009 (synthetic) or T012 (real).
 - Output: `data/processed/phenotypes_cleaned.fam` and `data/processed/phenotypes_cleaned.pheno`.
 - **MANDATORY**: MUST include geographic region, sampling year, and Varroa mite count in the model.
 - **MANDATORY**: MUST NOT substitute these covariates with PCA even if VIF < 5 (overrides plan.md Constitution Check #7 to comply with Constitution Principle VII).
 - **MANDATORY**: MUST NOT drop covariates due to collinearity.
- [~] T017 [US1] Create `code/03_gwas.sh` to execute PLINK logistic regression with covariates and output raw association statistics (FR-004). Do NOT include FDR logic here; that is handled by T022. Output to `data/interim/gwas_raw.tsv`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Multiple Testing Correction & Threshold Sensitivity (Priority: P2)

**Goal**: Apply Benjamini-Hochberg FDR correction and test threshold sensitivity to identify robust genetic associations.

**Independent Test**: Can be tested independently by running the correction on the GWAS output and verifying q-values and threshold counts.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for Benjamini-Hochberg implementation in `tests/unit/test_fdr_correction.py`
- [X] T019 [P] [US2] Contract test for sensitivity analysis output format in `tests/contract/test_threshold_sensitivity.py`

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement Benjamini-Hochberg FDR correction in `code/utils/fdr_correction.py` (FR-004).
 - **MANDATORY**: MUST implement BH correction. This overrides any plan.md deviation (Complexity Tracking) to comply with Spec FR-004.
 - Output: q-values for all SNPs.
- [X] T021 [US2] Implement threshold sensitivity sweep across a range of orders of magnitude in `code/utils/threshold_sensitivity.py` (FR-005).
 - Output: Write a report to `data/processed/threshold_sensitivity_report.tsv` containing counts and q-values for each threshold.
- [~] T022 [US2] Create `code/04_apply_fdr.sh` to post-process `data/interim/gwas_raw.tsv` using T020. Pipe PLINK output to `code/utils/fdr_correction.py` and write final results to `data/processed/gwas_results_fdr.tsv` (FR-004, FR-005).
- [X] T023 [US2] Update `code/04_apply_fdr.sh` to flag SNPs with q < 0.05 as significant.
 - **MANDATORY**: MUST inject the mandatory disclaimer text "Findings are associational, not causal..." into the final report output (FR-009, US-2 AC4).
 - **MANDATORY**: MUST modify the output generation function to prepend this text to the header of `data/processed/gwas_results_fdr.tsv`.
 - **MANDATORY**: Document the correction method used (BH) and its impact on discovery rate.
- [~] T024 [US2] (Deprecated logic moved to T043).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Machine Learning Validation & Polygenic Risk Scoring (Priority: P3)

**Goal**: Validate GWAS findings using LASSO logistic regression and compute polygenic risk scores to assess predictive performance.

**Independent Test**: Can be tested by running LASSO on a held-out test set (or synthetic equivalent) and verifying AUC is computed correctly.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US3] Unit test for LASSO AUC calculation in `tests/unit/test_lasso_auc.py`
- [~] T026 [P] [US3] Integration test for PRS likelihood-ratio test in `tests/integration/test_prs_validation.py`

### Implementation for User Story 3

- [X] T027 [P] [US3] Implement LASSO logistic regression with k-fold cross-validation. in `code/04_ml_validation.py` (FR-006) and report out-of-sample AUC value
- [X] T028 [US3] Implement Polygenic Risk Score (PRS) calculation in `code/04_ml_validation.py` (FR-007)
- [X] T029 [US3] Implement likelihood-ratio test for PRS improvement over covariates-only model in `code/04_ml_validation.py` (FR-007)
- [X] T030 [US3] Add AUC threshold logic in `code/04_ml_validation.py`:
 - Generate null distribution via 1000 phenotype permutations (seed=42).
 - Compare AUC against a high quantile of the null distribution.
 - If AUC < 0.75, flag the result as low predictive power.
 - **MANDATORY**: The flagging logic is separate from the permutation test; the permutation test is for validation, the flag is for the threshold.
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
- [~] T034 Code cleanup and refactoring of shell scripts for portability (Depends on T014, T017, T022)
- [ ] T041 [P] Profile pipeline with `cProfile` and generate `data/processed/profile_report.txt`
- [X] T042 Refactor `code/02_align_call.sh` to use parallel processing if profile shows I/O bottleneck (Depends on T041)
- [~] T036 [P] Additional unit tests for edge cases (missing Varroa data, all SNPs filtered) in `tests/unit/`
- [~] T037 Run quickstart.md validation to ensure reproducibility <!-- ATOMIZE: requested -->
- [X] T038 Create `docs/report_template.md` to include the mandatory disclaimer text: "Findings are associational, not causal..." (FR-009)

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