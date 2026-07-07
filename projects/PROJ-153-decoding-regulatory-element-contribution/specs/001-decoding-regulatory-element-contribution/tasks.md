# Tasks: Decoding Regulatory Element Contributions to Phenotypic Plasticity in Yeast

**Input**: Design documents from `/specs/001-yeast-cre-analysis/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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

- [ ] T001 Create project directory structure per `plan.md` (code/, tests/, data/, results/)
- [ ] T002 Initialize Conda environment with `environment.yml` (fastp, bowtie2, MACS2, R, Python)
- [ ] T003 [P] Create `manifest.yaml` with **verified, actual GEO/SRA accessions** for ChIP-seq, eQTL, Hi-C, and ATAC-seq; the pipeline MUST abort if any accession cannot be verified or data is missing (FR-001, Constitution Principle II)
- [ ] T004 [P] Setup Git hooks for large file tracking (LFS) for raw data references

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Implement `code/01_download_data.sh` to fetch raw FASTQ from GEO/SRA using `manifest.yaml` and verify MD5 checksums (FR-001)
- [ ] T006 Implement `code/02_preprocess_chipseq.sh` for adapter trimming (`fastp`) and alignment (`bowtie2`, ≤2 threads, MAPQ ≥ 30) (FR-002)
- [~] T007 [P] Implement `code/03_call_peaks.sh` to run MACS with FDR sweep (0.01, 0.05, 0.10) and output peak counts per threshold; **do not** calculate top-20 CRE overlap here (FR-003)
- [~] T008 Implement `code/04_merge_annotate.sh` to merge peaks across TFs/conditions and annotate promoter (≤500bp) vs distal (>500bp), storing result in `CRE_merged.bed` (FR-004)
- [~] T042 [P] Implement `code/04b_load_hic.sh` to download and process the Hi-C contact matrix (e.g., `.cool` format) from the Yeast 3D Genome Atlas (GSE12345) and output a query-ready matrix for FR-014 validation (FR-014) <!-- FAILED: unspecified -->
- [~] T009a Implement `code/06a_define_null_regions.sh` to define distal null regions (>10kb from genes) and output `null_regions.bed`
- [~] T009b Implement `code/06b_compute_null_signal.sh` to compute signal in null regions using `null_regions.bed` and output `null_region_signal.bed`
- [~] T019 [P] Add error handling in `code/01_download_data.sh` to abort if required ChIP-seq runs are missing (Edge Case) and to handle eQTL column validation (FR-011): fatal error if entire stress column missing, warning if individual genes missing
- [~] T010 [P] Create unit tests for data validation logic in `tests/unit/test_manifest_validation.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate a ranked CRE catalog (Priority: P1) 🎯 MVP

**Goal**: Produce `results/CRE_ranked_<stress>.md` with significant CREs (q ≤ 0.05) including coordinates, TFs, log₂FC, β₁, and q-value.

**Independent Test**: Execute `run_pipeline.sh` on sample manifest; verify `results/CRE_ranked_heatshock.md` exists, contains headers, and lists at least one CRE with q ≤ 0.05.

### Tests for User Story 1 (OPTIONAL) ⚠️

- [~] T011 [P] [US1] Contract test for output schema in `tests/contract/test_cre_schema.py`
- [ ] T012 [P] [US1] Integration test for pipeline end-to-end on mock data in `tests/integration/test_pipeline_us1.py`

### Implementation for User Story 1

- [ ] T013 Implement `code/05_validate_cre_gating.py` to perform motif scanning (FIMO, p < 1e-4) and **load Hi-C data from T042** to validate distal CREs (>100 reads), **explicitly excluding** CREs failing FR-014, and output `CRE_validated_filtered.bed` (FR-014)
- [ ] T014 Implement VIF calculation in `code/05_validate_cre_gating.py` to flag collinear CREs (VIF > 5) and **explicitly exclude** them from modeling, outputting updated `CRE_validated_filtered.bed` (FR-012). *Note: Depends on T013 output.*
- [ ] T043 Implement `code/05b_compute_delta_signal.py` to explicitly compute **ΔPeakSignal** (CRE signal minus null signal) by joining `CRE_merged.bed` signal with `null_region_signal.bed` (T009b), outputting `delta_peak_signal.tsv` (FR-015)
- [ ] T015 Implement weight calculation in `code/05_validate_cre_gating.py` using conditional logic to choose `log(motif_score + 1)` OR `log(hi_c_score + 1)` based on which validation passed, **applied to the ΔPeakSignal from T043** (FR-015)
- [ ] T016 Implement `code/06_fit_gls.R` to fit a **Fixed-Effects GLS model (no random intercepts)** per stress, testing the fixed effect β₁ for `weighted_ΔPeakSignal`. *Note: This substitutes the spec's Linear Mixed-Model due to CPU constraints (Plan e001), but preserves the statistical goal of testing β₁.* (FR-005, Methodology-5525a25f)
- [ ] T023 Implement Likelihood-Ratio Test (LRT) in `code/06_fit_gls.R` comparing full vs reduced model (FR-005)
- [ ] T017 Implement Benjamini-Hochberg FDR correction in `code/06_fit_gls.R` and enforce q ≤ 0.05 cutoff, **ensuring T018 consumes only this filtered subset** (FR-007)
- [ ] T018 Implement `code/10_generate_reports.R` to generate `results/CRE_ranked_<stress>.md` sorted by q-value and |β₁|, containing ONLY significant CREs (FR-008, SC-001)
- [ ] T041 [P] Implement `code/07b_fdr_overlap_analysis.R` to calculate the **top-20 CRE overlap percentage** between FDR thresholds (0.01, 0.05, 0.10) **using the GLS outputs (adjusted p-value, |β₁|)** from T016/T017, outputting `results/fdr_overlap_stats.csv` (FR-003, SC-004)
- [ ] T027 Add explicit disclaimer "results are associational, not causal" to all report outputs (FR-016), programmatically injecting into Markdown tables and PDFs

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical evidence of CRE contribution (Priority: P2)

**Goal**: Generate `results/Statistical_summary.pdf` with LRT results, empirical p-values, and variance explained (ΔR²).

**Independent Test**: Inspect PDF for β₁ significance (p < 0.05), empirical p-value from 10k shuffles, and ΔR² statement.

### Tests for User Story 2 (OPTIONAL) ⚠️

- [ ] T020 [P] [US2] Contract test for statistical report schema in `tests/contract/test_stats_schema.py`
- [ ] T021 [P] [US2] Integration test for permutation test logic in `tests/integration/test_permutation.py`

### Implementation for User Story 2

- [ ] T022 Implement `code/07_permutation_test.R` for **spatially-constrained block permutation** (shuffles) to generate empirical p-value, outputting `results/permutation_pvalue.csv` (FR-006, US-2). *Note: Depends on T016 and T023 completion to obtain observed β₁.*
- [ ] T024 Implement variance explained (ΔR²) calculation in `code/06_fit_gls.R` and `code/10_generate_reports.R`
- [ ] T025 Implement GO enrichment analysis (hypergeometric test) in `code/10_generate_reports.R` for stress-response genes (FR-010)
- [ ] T026 Implement bias sensitivity analysis in `code/08_sensitivity_analysis.R` comparing the **full set (post-FR-014)** against the **filtered set (post-VIF)** to explicitly **quantify selection bias** (FR-017)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualize top CREs in genome browser (Priority: P3)

**Goal**: Generate bigWig tracks `tracks/<stress>_CRE_signal.bw` for IGV visualization.

**Independent Test**: Load top 10 CRE tracks in IGV; verify signal peaks match summit positions and correlate with log₂FC (ρ ≥ 0.8).

### Tests for User Story 3 (OPTIONAL) ⚠️

- [ ] T029 [P] [US3] Contract test for bigWig file generation in `tests/contract/test_bigwig_schema.py`
- [ ] T030 [P] [US3] Integration test for summit match verification in `tests/integration/test_summit_match.py`

### Implementation for User Story 3

- [ ] T031 Implement `code/11_create_bigwig.sh` using `deepTools bamCoverage` to generate normalized tracks (FR-009)
- [ ] T032 Implement `code/09_summit_match.R` to compute Spearman ρ and summit match percentage (±5bp) specifically for the **top-10 CREs in the final ranked table (FDR ≤ 0.05)**. **Must explicitly verify ρ ≥ 0.8 (SC-005)**; if ρ < 0.8, log a warning and flag the result as failing the success criterion. Output `results/summit_match_stats.txt` (SC-005)
- [ ] T033 Integrate summit match results into `results/Statistical_summary.pdf` (US-3)
- [ ] T034 Implement optional ATAC-seq validation in `code/05_fetch_atac.sh` and `code/05_validate_cre_gating.py` (FR-013)
- [ ] T028 Generate `results/Statistical_summary.pdf` containing all required tables, plots, **and summit match integration from T033**, **variance explained from T024**, **GO enrichment from T025**, and **bias analysis from T026** (FR-010). *Note: Depends on T024, T025, T026 (Phase 4) and T033 (Phase 5).*

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035 Implement `code/12_generate_manifest.R` to record traceability for all outputs (Principle IV)
- [ ] T036 Update `code/run_pipeline.sh` to orchestrate all phases in correct dependency order
- [ ] T037 Add comprehensive logging to all scripts (versions, command lines, errors)
- [ ] T038 Run full pipeline on sample manifest to verify runtime ≤ 6h and memory ≤ 7GB
- [ ] T039 Update `quickstart.md` with final instructions and troubleshooting steps
- [ ] T040 [P] Cleanup temporary files and optimize disk usage in `data/processed/`

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires GLS output from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires BAMs from Phase 2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data validation (T013-T015) before GLS fitting (T016)
- GLS fitting before Report Generation (T018)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T010, T019, T042) can run in parallel
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for output schema in tests/contract/test_cre_schema.py"
Task: "Integration test for pipeline end-to-end on mock data in tests/integration/test_pipeline_us1.py"

# Launch validation logic tasks in parallel:
Task: "Implement 05_validate_cre_gating.py (motif/Hi-C)"
Task: "Implement VIF calculation in 05_validate_cre_gating.py"
Task: "Implement weight calculation in 05_validate_cre_gating.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (T013-T019, T041, T043)
4. **STOP and VALIDATE**: Test User Story 1 independently (ranked table generation)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently (statistical report) → Deploy/Demo
4. Add User Story 3 → Test independently (bigWig tracks) → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Validation + GLS + Ranking)
 - Developer B: User Story 2 (Permutation + Reporting)
 - Developer C: User Story 3 (BigWig + Summit Match)
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
- **CRITICAL**: All tasks must run on CPU-only free-tier CI (2 cores, 7GB RAM, ≤6h). No GPU/CUDA/8-bit models.
- **DATA INTEGRITY**: All tasks must use real datasets from `manifest.yaml`. No synthetic/fake data generation is permitted.