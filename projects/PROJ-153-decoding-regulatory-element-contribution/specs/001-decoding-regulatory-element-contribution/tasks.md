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

- [X] T001 Create project directory structure per `plan.md` (code/, tests/, data/, results/) AND generate `.gitattributes` for LFS tracking of data/ and tracks/
- [X] T002 Initialize Conda environment with `environment.yml` (fastp, bowtie2, MACS2, R, Python)
- [X] T52a1 [P] Extract accessions from `research.md` and output `data/extracted_accessions.yaml` with fields: `accession_type`, `accession_id`, `source_url`.
- [X] T52a2 [P] Validate `data/extracted_accessions.yaml` against a schema (required fields, valid format for GEO/SRA) and output `data/validation_log.yaml` with status: `valid` or `invalid`.
- [X] T52a3 [P] Generate `data/verified_accessions.yaml` from `data/extracted_accessions.yaml` if validation is `valid`. If `invalid`, log error and abort.
- [X] T052 [P] Populate `manifest.yaml` using the **verified accessions** from `data/verified_accessions.yaml` (output of T52a3); **ABORT if any accession is a placeholder (e.g., GSE####)** (FR-001, Spec Assumptions). *Note: Strictly enforces no placeholders.*
- [X] T052b [P] Implement `code/00_verify_data_accessions.py` to **automatically verify** `manifest.yaml` against `data/verified_accessions.yaml` and **abort with a fatal error** if any required accession remains a placeholder (e.g., GSE####) before pipeline execution; **do NOT** rely on manual verification (FR-001, Constitution Principle II). *Note: Replaces manual check in T057.*
- [X] T004 [P] Setup Git hooks for large file tracking (LFS) for raw data references; explicitly configure `.gitattributes` to track `data/raw/*` and `tracks/*`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. **Note: Phase 3 depends on T042_exec and T051b_exec completion explicitly.**

- [X] T005 [P] Implement `code/01_download.sh` to fetch raw FASTQ from GEO/SRA using `manifest.yaml`, verify MD checksums, and **abort with a fatal error listing missing TF-condition pairs** if any required run is absent (FR-001, Edge Cases).
- [X] T006 [P] Implement `code/02_preprocess.sh` (alias `02_preprocess_chipseq.sh`) for adapter trimming (`fastp`), alignment (`bowtie2`, ≤2 threads, MAPQ ≥ 30) **(FR-002)**; **explicitly preserve MACS2 narrowPeak files** (summit coordinates) for downstream summit match validation (SC-005).
- [ ] T007c_logic [P] Implement `code/03c_extract_peak_signals.R` (logic) to extract normalized peak signal (RPKM/counts) for each TF-condition pair from the BAM files (T006) for all CREs; **output** `data/processed/peak_signal_matrix.tsv` (columns: cre_id, tf_id, condition, signal). *Note: Required input for VIF calculation. **Depends on T006.***
- [X] T007c_exec [P] Implement `code/03c_extract_peak_signals.R` (exec) to run the logic defined in T007c_logic.
- [X] T007 [P] Implement `code/03_call_peaks.sh` to run **MACS2 peak calling** with FDR sweep across a range of significance thresholds and output peak counts per threshold; **output** `data/processed/peaks_fdr_<threshold>.bed` for each threshold (FR-003). *Note: This task performs the MACS2 peak calling sweep required by FR-003.*
- [ ] T008_logic [P] Implement `code/03_annotate.py` (logic) to: (1) **merge overlapping peaks** across TFs/conditions from `data/processed/peaks_fdr_*.bed`; (2) **annotate genomic context** (promoter ≤ 500 bp upstream vs. distal > 500 bp); (3) **output** `data/processed/merged_peaks_annotated.bed` (FR-004). *Note: **Centralizes FR-004 logic**. **Depends on T007.***
- [ ] T008_exec [P] Implement `code/03_annotate.py` (exec) to run the logic defined in T008_logic.
- [X] T042a [P] Implement `code/04a_resolve_hic_accession.py` to **verify the Yeast 3D Genome Atlas accession** in `data/verified_accessions.yaml`; **ABORT if the accession is a placeholder (e.g., GSE####)** (FR-014, Spec Assumptions). *Note: Strictly forbids placeholders. Does NOT query external sources.*
- [X] T042_logic [P] Implement `code/04b_load_hic.sh` (logic) to download Hi-C contact matrix (from `data/verified_accessions.yaml`) from Yeast 3D Genome Atlas, process to **High resolution cooler format**, and output `data/processed/hic_matrix_10kb.cool`; **abort if T052b verification fails** (FR-014). *Note: This is a strict prerequisite for T04_motif_hic_filter (Phase 3). **Explicitly aborts if placeholder accession is not resolved.*** **Dependency**: T042a, T052b.
- [X] T042_exec [P] Implement `code/04b_load_hic.sh` (exec) to run the logic defined in T042_logic.
- [X] T009a [P] Implement `code/03c_extract_peak_signals.R` to define distal null regions (>10kb from genes) and output `data/processed/null_regions.bed`
- [X] T009b [P] Implement `code/03c_extract_peak_signals.R` to compute signal in null regions using `data/processed/null_regions.bed` and output `data/processed/null_region_signal.bed`. *Note: Depends on T009a.*
- [ ] T043_weights_logic [P] Implement `code/043_calc_delta_signal.py` (logic) to compute ΔPeakSignal by joining `merged_peaks_annotated.bed` (T008_exec) with `null_region_signal.bed` (T009b); **output** `data/processed/delta_peak_signal.tsv`. *Note: **Depends on T008_exec, T009b**. Corrected file path from 04a_resolve_hic_accession.py.*
- [X] T043_weights_exec [P] Implement `code/043_calc_delta_signal.py` (exec) to run the logic defined in T043_weights_logic.
- [X] T019 [P] Add error handling in `code/01_download.sh` to abort if required ChIP-seq runs are missing (Edge Case) and to handle eQTL column validation (FR-011): fatal error if entire stress column missing, warning if individual genes missing
- [X] T045 [P] Implement `code/01_stream_eqtl.py` to **download the eQTL dataset to `data/raw/` as a static, checksummed file first**, then **stream it** using `datasets.load_dataset(..., streaming=True)` from the local file to process in chunks; this ensures reproducibility on fresh runners (Constitution Principle I) while preserving statistical power. *Note: Must complete before T051b_exec and T05_weights_impl.*
- [X] T051b_logic [P] Implement `code/051b_filter_genes.py` (logic) to filter genes, log the exact number of dropped genes, and output `data/processed/filtered_genes.tsv`
- [X] T051b_exec [P] Implement `code/051b_filter_genes.py` (exec) to run the logic defined in T051b_logic.
- [X] T007c_narrowpeak_extract_logic [P] Implement `code/03d_extract_narrowpeak_summits.py` (logic) to **extract summit coordinates** from the MACS2 narrowPeak files (preserved by T006) for all CREs; **output** `data/processed/cre_summits.bed` (columns: cre_id, summit_start, summit_end). *Note: Required for SC-005 summit match validation. **Depends on T006.***
- [X] T007c_narrowpeak_extract_exec [P] Implement `code/03d_extract_narrowpeak_summits.py` (exec) to run the logic defined in T007c_narrowpeak_extract_logic.
- [X] T010 [P] Create unit tests for data validation logic in `tests/unit/test_manifest_validation.py`
- [X] T051 [P] Implement `code/01b_validate_eqtl_schema.py` to explicitly verify the eQTL dataset contains the three required stress columns (heat-shock, osmotic, oxidative) and effect sizes; raise a **fatal error** if any entire stress column is missing (FR-011), and log warnings for individual genes missing. *Note: Runs after T005, before T051b.*

---

## Phase 3: User Story 1 - Generate a ranked CRE catalog (Priority: P1) 🎯 MVP

**Goal**: Produce `results/CRE_ranked_<stress>.md` with significant CREs (q ≤ 0.05) including coordinates, TFs, log₂FC, β₁, and q-value.

**Independent Test**: Execute `run_pipeline.sh` on sample manifest; verify `results/CRE_ranked_heatshock.md` exists, contains headers, and lists at least one CRE with q ≤ 0.05.

### Tests for User Story 1 (OPTIONAL) ⚠️

- [X] T011 [P] [US1] Contract test for output schema in `tests/contract/test_cre_schema.py`
- [X] T012 [P] [US1] Integration test for pipeline end-to-end on minimal real data subset in `tests/integration/test_pipeline_us1.py`: **Input**: `data/raw/minimal_subset/*` (real data); **Output**: `results/CRE_ranked_heatshock_minimal.md`; **Assertion**: File exists, header matches schema, row count > 0 (FR-008)

### Implementation for User Story 1

- [ ] T04_vif_logic [P] Implement `code/04_vif_calc.R` (logic) to diagnose multicollinearity (VIF > 5) among TF peak signals for each CRE (FR-012); **output** `data/processed/vif_flags.tsv`. *Note: **Depends on T007c_exec.***
- [X] T04_vif_exec [P] Implement `code/04_vif_calc.R` (exec) to run the logic defined in T04_vif_logic.
- [ ] T04_filter_logic [P] Implement `code/04_motif_hic_filter.py` (logic) to validate distal CREs via motif (PWM p-value < 1e-4) or Hi-C (reads > 100) (FR-014); **output** `data/processed/hic_validation_flags.tsv`. *Note: **Depends on T042_exec, T008_exec.***
- [X] T04_filter_exec [P] Implement `code/04_motif_hic_filter.py` (exec) to run the logic defined in T04_filter_logic.
- [ ] T04_apply_filters [P] Implement `code/04_apply_filters.py` to apply VIF and Motif/Hi-C filters; **output** `data/processed/cre_filtered.tsv`. *Note: **Depends on T04_vif_exec, T04_filter_exec, T051b_exec.** (FR-012, FR-014)*
- [X] T05_calc_hic_weights_logic [P] Implement `code/05_calc_hic_weights.py` (logic) to compute weights based on motif scores or Hi-C frequency (FR-015); **output** `data/processed/hic_weights.tsv`. *Note: **Depends on T04_filter_exec.** (FR-015)*
- [X] T05_calc_hic_weights_exec [P] Implement `code/05_calc_hic_weights.py` (exec) to run the logic defined in T05_calc_hic_weights_logic.
- [X] T05_weights_impl_logic [P] Implement `code/05_weights_impl.py` (logic) to calculate final weights for LMM; **output** `data/processed/cre_weights.tsv`. *Note: **Depends on T04_apply_filters, T05_calc_hic_weights_exec.** (FR-015)*
- [X] T05_weights_impl_exec [P] Implement `code/05_weights_impl.py` (exec) to run the logic defined in T05_weights_impl_logic.
- [ ] T06_lmm_impl_logic [P] Implement `code/06_lmm.R` (logic) to fit LMM on filtered subset with weights (FR-005); **output** `data/processed/lmm_results.tsv`. *Note: **Depends on T051b_exec, T05_weights_impl_exec, T043_weights_exec.** (FR-005)*
- [X] T06_lmm_impl_exec [P] Implement `code/06_lmm.R` (exec) to run the logic defined in T06_lmm_impl_logic.
- [X] T06_lmm_full_set_logic [P] Implement `code/06_lmm_full_set.R` (logic) to fit LMM on full set (for bias analysis); **output** `data/processed/lmm_full_set_results.tsv`. *Note: **Depends on T051b_exec, T05_weights_impl_exec, T043_weights_exec.** (FR-017)*
- [X] T06_lmm_full_set_exec [P] Implement `code/06_lmm_full_set.R` (exec) to run the logic defined in T06_lmm_full_set_logic.
- [X] T007_sweep_logic [P] Implement `code/03_sweep_run_lmm.R` (logic) to iterate over FDR thresholds (, 0.05, 0.10) and run LMM (FR-003); **output** `data/processed/fdr_sweep_results.tsv`. *Note: **Depends on T04_apply_filters, T06_lmm_impl_exec.** (FR-003)*
- [X] T007_sweep_exec [P] Implement `code/03_sweep_run_lmm.R` (exec) to run the logic defined in T007_sweep_logic.
- [X] T007_overlap_logic [P] Implement `code/03_sweep_calc_overlap.R` (logic) to compute top-N CRE overlap percentage between FDR thresholds (FR-003); **output** `data/processed/fdr_overlap.tsv`. *Note: **Depends on T007_sweep_exec.** (FR-003)*
- [X] T007_overlap_exec [P] Implement `code/03_sweep_calc_overlap.R` (exec) to run the logic defined in T007_overlap_logic.
- [X] T018_logic [P] Implement `code/10_generate_reports.R` (logic) to generate final ranked tables and report components; **output** `results/CRE_ranked_<stress>.md`. *Note: **Depends on T007_overlap_exec.** (FR-008, SC-001)*
- [X] T018_exec [P] Implement `code/10_generate_reports.R` (exec) to run the logic defined in T018_logic.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 4: User Story 2 - Statistical evidence of CRE contribution (Priority: P2)

**Goal**: Generate statistical components for the final report (LRT, permutation, variance explained). Note: The final PDF generation is moved to Phase 5 to include visualization stats.

### Tests for User Story 2 (OPTIONAL) ⚠️

- [X] T020 [P] [US2] Contract test for statistical report schema in `tests/contract/test_stats_schema.py`
- [X] T021 [P] [US2] Integration test for permutation test logic in `tests/integration/test_permutation.py`

### Implementation for User Story 2

- [X] T022 [P] Implement `code/07_permutation_test.R` for spatially-constrained block permutation (shuffles) to generate empirical p-value, outputting `results/permutation_pvalue.csv` (FR-006). *Note: Depends on T06_lmm_impl_exec completion to obtain observed β₁.*
- [X] T022b [P] Implement `code/07b_compute_empirical_pvalue.R` to compute the final empirical p-value from the shuffled distribution.
- [X] T049 [P] Implement `code/07_permutation_checkpoint.R` to implement a checkpointing mechanism for the shuffles.
- [X] T024_internal [P] Implement internal logic for variance explained (ΔR²) calculation.
- [X] T025_internal [P] Implement internal logic for GO enrichment.
- [X] T026_bias_logic [P] Implement `code/07c_bias_sensitivity.R` (logic) to compare β₁ estimates between the full set and filtered set (FR-017); **output** `results/bias_sensitivity.csv`. *Note: **Depends on T06_lmm_impl_exec, T06_lmm_full_set_exec.** (FR-017)*
- [X] T026_bias_exec [P] Implement `code/07c_bias_sensitivity.R` (exec) to run the logic defined in T026_bias_logic.

**Checkpoint**: Statistical components ready for final report generation

---

## Phase 5: User Story 3 & Final Report (Priority: P3)

**Goal**: Generate bigWig tracks, calculate summit matches, and produce the final `results/Statistical_summary.pdf` combining all statistical and visualization results.

**Independent Test**: Execute `run_pipeline.sh` on a sample manifest that has produced at least 10 significant CREs in `results/CRE_ranked_heatshock.md` (T018_exec). **Verify** that `tracks/heatshock_CRE_signal.bw` exists, can be loaded into IGV, and that for the top 10 CREs (or all available if <10), the signal peaks match summit positions and correlate with log₂FC (ρ ≥ 0.8). **Note**: This test is dependent on the successful completion of US1 (T018_exec) and assumes a sufficient number of significant CREs exist. If fewer than 10 CREs are found, the test validates all available rows.

### Tests for User Story 3 (OPTIONAL) ⚠️

- [X] T029 [P] [US3] Contract test for bigWig file generation in `tests/contract/test_bigwig_schema.py`: **Validate** `tracks/*.bw` against `contracts/bigwig_schema.yaml` using `bigWigSummary`.
- [X] T030 [P] [US3] Integration test for summit match verification in `tests/integration/test_summit_match.py`.

### Implementation for User Story 3 & Final Report

- [ ] T08_viz_logic [P] Implement `code/08_visualize.py` (logic) to generate bigWig tracks and compute Spearman correlation (FR-009, SC-005); **output** `tracks/<stress>_CRE_signal.bw`. *Note: **Depends on T018_exec, T007c_narrowpeak_extract_exec.** (FR-009, SC-005)*
- [ ] T08_viz_exec [P] Implement `code/08_visualize.py` (exec) to run the logic defined in T08_viz_logic.
- [X] T034 [P] Implement optional ATAC-seq validation.
- [X] T05_validate_cre_gating_impl [P] Implement ATAC-seq validation logic.
- [X] T07_report_logic [P] Implement `code/07_report.R` (logic) to generate the final PDF report (FR-010); **output** `results/Statistical_summary.pdf`. *Note: **Depends on T08_viz_exec, T026_bias_exec.** (FR-010)*
- [X] T07_report_exec [P] Implement `code/07_report.R` (exec) to run the logic defined in T07_report_logic.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T62a_create_minimal_subset [P] **Create Minimal Real Data Subset**:
- [X] T62c_real_dry_run [P] **Dry-Run on Real Data (Minimal Subset)**:
- [X] T63_contrib_impl [P] Generate a final `CONTRIBUTING.md` file.
- [X] T64 [P] Create a `run_pipeline.sh` wrapper.
- [X] T65_validate_outputs_impl [P] Implement a `validate_outputs.py` script.

---

## Phase N+1: Final Verification & Handoff

**Purpose**: Ensure the pipeline is robust, documented, and ready for real data execution.

- [X] T064_run_pipeline [P] Execute `run_pipeline.sh` end-to-end on full dataset and verify all outputs (FR-001 to FR-017).
- [X] T065_final_validation [P] Run `validate_outputs.py` to ensure all schemas and checksums match.

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [ ] T066 Reconcile run-book vs implementation for `code/05_weights.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/05_weights.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
