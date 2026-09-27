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

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. **Note: Phase 3 depends on T042 and T051 completion explicitly.**

- [X] T005 [P] Implement `code/01_download.sh` to fetch raw FASTQ from GEO/SRA using `manifest.yaml`, verify MD checksums, and **abort with a fatal error listing missing TF-condition pairs** if any required run is absent (FR-001, Edge Cases).
- [X] T006 [P] Implement `code/02_preprocess.sh` (alias `02_preprocess_chipseq.sh`) for adapter trimming (`fastp`) and alignment (`bowtie2`, ≤2 threads, MAPQ ≥ 30) (FR-002)
- [X] T008 [P] Implement `code/03_annotate.py` to merge peaks across TFs/conditions and annotate promoter (≤500bp) vs distal (>500bp), storing result in `data/processed/CRE_merged.bed` (FR-004)
- [X] T007c [P] Implement `code/03c_extract_peak_signals.R` to extract normalized peak signal (RPKM/counts) for each TF-condition pair from the BAM files (T006) for all CREs in `data/processed/CRE_merged.bed`; **output** `data/processed/peak_signal_matrix.tsv` (columns: cre_id, tf_id, condition, signal). *Note: Required input for VIF calculation. Removed [P] tag as it depends on T008.*
- [X] T007 [P] Implement `code/03_call_peaks.sh` to run **MACS2 peak calling** with FDR sweep across a range of significance thresholds and output peak counts per threshold; **output** `data/processed/peaks_fdr_<threshold>.bed` for each threshold (FR-003). *Note: This task performs the MACS2 peak calling sweep required by FR-003.*
- [X] T042 [P] Implement `code/04b_load_hic.sh` to download Hi-C contact matrix (GSE) from Yeast 3D Genome Atlas, process to **High resolution cooler format**, and output `data/processed/hic_matrix_10kb.cool`; **abort if T052b verification fails** (FR-014). *Note: This is a strict prerequisite for T04_motif_hic_filter (Phase 3). **Explicitly aborts if placeholder accession is not resolved.*** **Dependency**: T052b.
- [X] T009a Implement `code/06a_define_null_regions.sh` to define distal null regions (>10kb from genes) and output `data/processed/null_regions.bed`
- [X] T009b Implement `code/06b_compute_null_signal.sh` to compute signal in null regions using `data/processed/null_regions.bed` and output `data/processed/null_region_signal.bed`. *Note: Depends on T009a. Removed [P] tag as it depends on T009a.*
- [X] T043 [P] Implement `code/05b_compute_delta_signal.py` to explicitly compute **ΔPeakSignal** (CRE signal minus null signal) by joining `data/processed/CRE_merged.bed` signal with `data/processed/null_region_signal.bed`, outputting `data/processed/delta_peak_signal.tsv` (FR-015). *Note: Depends on T009b. Runs in parallel with other Phase 2 tasks not dependent on T009b. Removed [P] tag as it depends on T009b.*
- [X] T019 [P] Add error handling in `code/01_download.sh` to abort if required ChIP-seq runs are missing (Edge Case) and to handle eQTL column validation (FR-011): fatal error if entire stress column missing, warning if individual genes missing
- [X] T051 [P] Implement `code/01b_validate_eqtl_schema.py` to explicitly verify the eQTL dataset contains the three required stress columns (heat-shock, osmotic, oxidative) and effect sizes; raise a **fatal error** if any entire stress column is missing (FR-011), and log warnings for individual missing genes (FR-011). *Note: Runs after T005, before T051b.*
- [X] T051b [P] Implement `code/051b_filter_genes.py` to: (1) load eQTL dataset (T045) and `cre_filtered.tsv` (T04_apply_filters); (2) **filter out genes with missing fold-changes**; (3) **log the exact number of genes dropped** and the percentage of the total cohort; (4) **output** `data/processed/cre_gene_pairs.tsv` (columns: cre_id, gene_id, fold_change, ...) ensuring the join with CREs is performed **after** gene filtering to avoid generating pairs for excluded genes (FR-011). *Note: Explicitly implements the exclusion mechanism. **Depends on T051 and T04_apply_filters.***
- [X] T010 [P] Create unit tests for data validation logic in `tests/unit/test_manifest_validation.py`
- [X] T045 [P] Implement `code/01_stream_eqtl.py` to **download the eQTL dataset to `data/raw/` as a static, checksummed file first**, then **stream it** using `datasets.load_dataset(..., streaming=True)` from the local file to process in chunks; this ensures reproducibility on fresh runners (Constitution Principle I) while preserving statistical power. *Note: Must complete before T051b and T05_weights_impl.*

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate a ranked CRE catalog (Priority: P1) 🎯 MVP

**Goal**: Produce `results/CRE_ranked_<stress>.md` with significant CREs (q ≤ 0.05) including coordinates, TFs, log₂FC, β₁, and q-value.

**Independent Test**: Execute `run_pipeline.sh` on sample manifest; verify `results/CRE_ranked_heatshock.md` exists, contains headers, and lists at least one CRE with q ≤ 0.05.

### Tests for User Story 1 (OPTIONAL) ⚠️

- [X] T011 [P] [US1] Contract test for output schema in `tests/contract/test_cre_schema.py`
- [X] T012 [P] [US1] Integration test for pipeline end-to-end on mock data in `tests/integration/test_pipeline_us1.py`: **Input**: `tests/data/mock/synthetic_fastq/*`; **Output**: `results/CRE_ranked_heatshock_mock.md`; **Assertion**: File exists, header matches schema, row count > 0 (FR-008)

### Implementation for User Story 1

- [X] T04_vif_calc [P] Implement `code/04a_vif_calc.py` to: (1) load `data/processed/peak_signal_matrix.tsv` (T007c); (2) **perform VIF calculation** (FR-012) on peak signals for each CRE; (3) **output** `data/processed/vif_flags.tsv` (columns: cre_id, vif_score, is_collinear) (FR-012). *Note: **Depends on T007c.***
- [X] T04_motif_hic_filter [P] Implement `code/04b_motif_hic_filter.py` to: (1) perform Motif scanning (FIMO, p < 1e-4) on distal CREs (>500 bp) (FR-014); (2) perform Hi-C validation (contact freq > 100) on distal CREs (FR-014); (3) **output** `data/processed/motif_validation_flags.tsv` and `data/processed/hic_validation_flags.tsv` (FR-014). *Note: **Depends on T008 and T042.***
- [X] T04_apply_filters [P] Implement `code/04c_apply_filters.py` to: (1) join `data/processed/peak_signal_matrix.tsv` (T007c), `data/processed/vif_flags.tsv` (T04_vif_calc), `data/processed/motif_validation_flags.tsv` (T04_motif_hic_filter), and `data/processed/hic_validation_flags.tsv` (T04_motif_hic_filter); (2) **apply FR-014 filter**: retain CRE if `motif_validated` is TRUE OR `hic_validated` is TRUE (inclusive OR); **if neither is TRUE, exclude**; (3) **exclude collinear CREs** (VIF > 5); (4) **output** `data/processed/cre_filtered.tsv` (full set post-filter) (FR-014). *Note: **CRITICAL**: This task **ABORTS** if T042 (Hi-C download) fails. No placeholder files are generated. **Depends on T008, T007c, T042, T043, T045, T04_vif_calc, T04_motif_hic_filter.***
- [X] T05_weights_impl [P] Implement `code/05_weights.py` to: (1) consume `data/processed/delta_peak_signal.tsv` (T043) and `data/processed/cre_filtered.tsv` (T04_apply_filters); (2) **calculate weights**: `weight = log(motif_score)` or `log(hic_frequency)` for pairs passing FR-014; (3) **compute weighted predictor**: `weighted_signal = ΔPeakSignal * weight`; (4) **output** `data/processed/weighted_delta_signal.tsv` (columns: cre_id, gene_id, weighted_signal, weight_value) (FR-015). *Note: Explicitly defines the mathematical operation. **Depends on T043 and T04_apply_filters.***
- [X] T06_lmm_impl [P] Implement `code/06_lmm.R` to: (1) fit a **Linear Mixed-Model (LMM)** per stress using the `lme4` R package (`lmer` function), specifying a fixed effect for `weighted_signal` (from T05_weights_impl) and **random intercepts for genes** (`(1|gene_id)`) to account for gene-specific variance (FR-005); (2) perform **Likelihood-Ratio Test (LRT)** comparing full vs reduced model (FR-005); (3) apply **Benjamini-Hochberg FDR correction** and enforce q ≤ 0.05 cutoff (FR-007); (4) **output** `data/processed/lmm_results.tsv` (columns: cre_id, gene_id, beta1, adj_pval, q_val, lrt_pval) (FR-005, FR-007). *Note: Merged T016 and T023. Explicitly avoids GLS approximation.*
- [X] T007_sweep_run_lmm [P] Implement `code/03_sweep_run_lmm.R` to: (1) **re-run the LMM analysis** (using the logic from T06_lmm_impl) on the filtered subsets defined by each FDR threshold (0.01, 0.05, 0.10) from `data/processed/peaks_fdr_<threshold>.bed`; (2) **re-apply T04_apply_filters logic** to each subset to ensure robustness on validated sets; (3) **output** `data/processed/lmm_sweep_results.tsv` containing β₁ estimates, adjusted p-values for each threshold (FR-003). *Note: **Depends on T06_lmm_impl and T04_apply_filters. This is where the LMM is actually run for the sweep.***
- [X] T007_sweep_calc_overlap [P] Implement `code/03_sweep_calc_overlap.R` to: (1) extract the top-ranked CREs from each FDR threshold **sorted by adjusted p-value (primary) and absolute β₁ magnitude (tie-breaker)** from `data/processed/lmm_sweep_results.tsv`; (2) compute the **top-20 CRE overlap percentage** (Jaccard index) between thresholds; (3) **output** `results/fdr_sweep_summary.tsv` (columns: threshold, beta1, adj_pval, overlap_pct) (FR-003, SC-004). *Note: Performs overlap analysis ONLY on **real LMM results**. **Depends on T007_sweep_run_lmm.***
- [X] T018 [P] Implement `code/10_generate_reports.R` (alias `07_report.R` for US1) to: (1) **consume `results/fdr_sweep_summary.tsv`** to validate robustness of FDR ≤ 0.05; (2) **filter `data/processed/lmm_sweep_results.tsv` to FDR ≤ 0.05**; (3) **isolate the FDR ≤ 0.05 subset** and generate `results/CRE_ranked_<stress>.md` sorted by q-value and |β₁|, containing **all significant CREs (q ≤ 0.05) derived from the FDR ≤ 0.05 threshold** (primary output); (4) **merge sweep results** for robustness analysis (FR-008, SC-001, FR-003). *Note: Primary table uses FDR ≤ 0.05. Sweep results used for SC-004. **Depends on T06_lmm_impl and T007_sweep_calc_overlap.***
- [X] T027 [P] Add explicit disclaimer "results are associational, not causal" to all report outputs (FR-016), programmatically injecting into Markdown tables and PDFs. *Note: Logic internal to T07_report_impl.*

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical evidence of CRE contribution (Priority: P2)

**Goal**: Generate statistical components for the final report (LRT, permutation, variance explained). Note: The final PDF generation is moved to Phase 5 to include visualization stats.

**Independent Test**: Inspect intermediate outputs for β₁ significance (p < 0.05), empirical p-value from a sufficient number of shuffles, and ΔR² statement.

### Tests for User Story 2 (OPTIONAL) ⚠️

- [X] T020 [P] [US2] Contract test for statistical report schema in `tests/contract/test_stats_schema.py`
- [X] T021 [P] [US2] Integration test for permutation test logic in `tests/integration/test_permutation.py`

### Implementation for User Story 2

- [X] T022 [P] Implement `code/07_permutation_test.R` for **spatially-constrained block permutation** (shuffles) to generate empirical p-value, outputting `results/permutation_pvalue.csv` (FR-006, US-2). *Note: Depends on T06_lmm_impl completion to obtain observed β₁.*
- [X] T049 [P] Implement `code/07_permutation_checkpoint.R` to include a **progress bar and checkpointing mechanism** for the shuffles; **checkpoint every fixed number of shuffles** to `results/permutation_checkpoint.pkl` (JSON schema: `{last_shuffle: int, p_values: array}`); **resume logic**: load last saved state and continue from the next shuffle (FR-006). *Note: Explicitly implements the shuffle requirement from FR-006 and SC-002, removing any '[deferred]' placeholders.*
- [X] T024_internal [P] Implement internal logic for variance explained (ΔR²) calculation within `code/06_lmm.R` or a helper script, outputting `results/variance_explained.tsv`. *Note: Logic internal to LMM phase, output used in final report.*
- [X] T025_internal [P] Implement internal logic for GO enrichment (hypergeometric test) within `code/07_report.R` (moved to Phase 5), outputting `results/go_enrichment.tsv`. *Note: Logic internal to report phase.*
- [X] T026_internal [P] Implement internal logic for bias sensitivity analysis (full vs filtered) within `code/07_report.R` (moved to Phase 5), outputting `results/bias_sensitivity.csv`. *Note: Logic internal to report phase.*

**Checkpoint**: Statistical components ready for final report generation

---

## Phase 5: User Story 3 & Final Report (Priority: P3)

**Goal**: Generate bigWig tracks, calculate summit matches, and produce the final `results/Statistical_summary.pdf` combining all statistical and visualization results.

**Independent Test**: Execute `run_pipeline.sh` on a sample manifest that has produced at least 10 significant CREs in `results/CRE_ranked_heatshock.md` (T018). **Verify** that `tracks/heatshock_CRE_signal.bw` exists, can be loaded into IGV, and that for the top 10 CREs (or all available if <10), the signal peaks match summit positions and correlate with log₂FC (ρ ≥ 0.8). **Note**: This test is dependent on the successful completion of US1 (T018) and assumes a sufficient number of significant CREs exist. If fewer than 10 CREs are found, the test validates all available rows.

### Tests for User Story 3 (OPTIONAL) ⚠️

- [X] T029 [P] [US3] Contract test for bigWig file generation in `tests/contract/test_bigwig_schema.py`: **Validate** `tracks/*.bw` against `contracts/bigwig_schema.yaml` using `bigWigSummary`
- [X] T030 [P] [US3] Integration test for summit match verification in `tests/integration/test_summit_match.py`: **Input**: `tracks/heatshock_CRE_signal.bw`, `results/CRE_ranked_heatshock.md`; **Output**: `results/summit_match_stats.txt`; **Assertion**: ρ ≥ 0.8 for top-10 (or all available if <10)

### Implementation for User Story 3 & Final Report

- [X] T08_visualize_impl [P] Implement `code/08_visualize.py` to: (1) generate bigWig tracks using `deepTools bamCoverage` with `--normalizeUsing RPKM`, `--binSize`, input BAMs from T006, output `tracks/<stress>_CRE_signal.bw` (FR-009); (2) **filter the ranked CRE table from T018 to the top 10 rows** (by q-value and |β₁|), or **all rows if fewer than 10 exist**; (3) compute Spearman ρ between `log₂FC` and `bigWig_signal` for these **top 10 (or all) CREs**; (4) explicitly calculate the **percentage of summit matches within ±5 bp** for these **top 10 (or all) CREs**; (5) **output** `results/summit_match_stats.tsv` (TSV format, columns: correlation_rho, match_percentage, exit_code) and **log a warning** if `match_percentage` < 90% (SC-005); (6) **explicitly include the match_percentage in the final `results/Statistical_summary.pdf` and `results/CRE_ranked_<stress>.md` header** (SC-005). **Pipeline continues; warning logged** (Edge Case). *Note: Consolidates T031, T032, T033. Explicitly filters to top-10 or all available. **Depends on T018, T006.***
- [X] T034 [P] Implement optional ATAC-seq validation in `code/05_validate_cre_gating.py` (T05_validate_cre_gating_impl logic): **If** ATAC-seq data exists in `data/raw/atac/`, run validation; **else** log "ATAC-seq validation skipped: data not found". Update `data/processed/CRE_validated.bed` with `validated_by_atac` column (FR-013). *Note: Logic internal to T05_validate_cre_gating_impl.*
- [X] T05_validate_cre_gating_impl [P] Implement `code/05_validate_cre_gating.py` to: (1) perform ATAC-seq validation if data exists; (2) update `data/processed/CRE_validated.bed`; (3) **output** `data/processed/cre_validation_log.yaml` (FR-013). *Note: Consolidates T034. **Depends on T008.***
- [X] T07_report_impl [P] Implement `code/07_report.R` to: (1) generate `results/Statistical_summary.pdf` containing (i) number of peaks per TF/condition, (ii) variance explained (ΔR²) by CRE signal (T024_internal), (iii) enrichment test results for GO stress‑response categories (T025_internal), (iv) bias sensitivity analysis comparing full set (pre-FR-014) vs filtered set (post-FR-014) (T026_internal), (v) **summit match stats from T08_visualize_impl (including match_percentage)**, and (vi) disclaimer (FR-016) (FR-010, FR-003, FR-017, FR-016); (2) **output** `results/bias_sensitivity.csv`, `results/fdr_sweep_summary.tsv` (merged from T007_sweep_calc_overlap), `results/summit_match_stats.tsv` (merged from T08_visualize_impl). *Note: **Moved from Phase 4 to Phase 5** to ensure dependency on T08_visualize_impl. Consolidates T024, T025, T026, T027, T028, T033.*

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T12_generate_manifest_impl [P] Implement `code/12_generate_manifest.R` to record traceability for all outputs (Principle IV); **Output**: `results/traceability_manifest.json` with fields: input_hash, script_version, output_path
- [X] T36_run_pipeline_impl [P] Update `code/run_pipeline.sh` to orchestrate all phases in correct dependency order (Phase 2 → Phase 3 → Phase 4 → Phase 5); **Include** error handling (set -e), logging, and status checks
- [X] T37_logging_impl [P] Add comprehensive logging to all scripts; **Format**: ISO8601 timestamp, level, message; **Location**: `logs/pipeline.log`
- [X] T38_perf_test_impl [P] Run full pipeline on sample manifest to verify runtime ≤ 6h and memory ≤ 7GB; **Output**: `results/performance_report.csv` with metrics: total_time, peak_memory
- [X] T39_quickstart_impl [P] Update `quickstart.md` with final instructions and troubleshooting steps; **Include**: dependency installation, manifest creation, common errors
- [X] T40_cleanup_impl [P] Cleanup temporary files and optimize disk usage in `data/processed/`; **Policy**: Delete `*.tmp`, `*.bam` (keep `*.bed`, `*.tsv`); **Command**: `find data/processed/ -name "*.tmp" -delete`

---

## Phase N+1: Revision & Robustness (Addressing Review Concerns)

**Purpose**: Improvements that affect multiple user stories

- [X] T044 [P] Refactor `code/01_download.sh` to **remove any `try/except` blocks that fallback to synthetic/mock data**; instead, ensure that any download failure or checksum mismatch raises a fatal error immediately with a clear message listing the missing accession (Constitution Principle II, FR-001).
- [X] T046 [P] Update `code/05_validate_cre_gating.py` to **explicitly state the sample size and representativeness limitation** in the output log if the eQTL dataset was streamed and filtered; ensure the code does not silently drop genes without logging a warning (FR-011 compliance).
- [X] T047 [P] **REMOVED**: Task removed to enforce strict no-placeholder policy.
- [X] T48_verify_integrity_impl [P] Implement `code/00_verify_data_integrity.py` to perform a **one-time sanity check** on the downloaded ChIP-seq and eQTL files (e.g., check file sizes, verify header columns) before processing begins, ensuring the data is not corrupted or empty before the pipeline proceeds.
- [X] T53_streaming_doc_impl [P] Implement `code/00_streaming_documentation.py` to **dynamically generate a `streaming_strategy.md` report** that explicitly documents the chunk size, total estimated rows, and the exact `datasets` streaming code snippet used in `code/01_stream_eqtl.py`. **Report Schema**: Must include fields `chunk_size`, `total_rows`, `code_snippet`. (Constitution Principle I, FR-011).
- [X] T054 [P] Add a **final assertion** in `code/04c_apply_filters.py` that verifies **zero** synthetic or mock data sources were loaded during the entire pipeline execution by scanning the `logs/pipeline.log` for keywords like "synthetic", "mock", "fallback" (case-insensitive, regex `(?i)(synthetic|mock|fallback)`); **abort** if any are found (Constitution Principle II, FR-001). *Note: Removed 'placeholder' from regex to avoid false aborts on valid template data.*
- [X] T1b_validate_eqtl_impl [P] Refactor `code/01b_validate_eqtl_schema.py` to **explicitly log the exact number of genes dropped** due to missing fold-changes and the **percentage of the total cohort** this represents, ensuring the "warning" requirement in FR-011 is quantifiable and auditable (FR-011).
- [X] T56_final_integrity_impl [P] Implement `code/13_final_integrity_check.sh` to run a **comprehensive post-hoc validation** that compares the MD5 checksums of all final output files against a reference manifest generated at the start of the run, ensuring no data was altered or replaced during the pipeline execution (Constitution Principle III).
- [X] T057 [P] Update `quickstart.md` to include a **mandatory "Data Source Verification" section** that instructs users to manually verify the `manifest.yaml` accessions against the `data/verified_accessions.yaml` before running the pipeline; **explicitly state that placeholders (e.g., GSE####) are FORBIDDEN and will trigger an abort** (FR-001, Edge Cases). *Note: Updated to strictly forbid placeholders.*
- [X] T058 [P] Add a **runtime flag** `--strict-data-mode` to `code/run_pipeline.sh` that, when enabled, **disables all warnings** and forces a **fatal error** on any data anomaly (e.g., missing gene, low coverage), ensuring the pipeline never silently degrades to a lower-quality dataset (FR-011, FR-001).

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [X] T059_create Reconcile run-book vs implementation for `code/03_annotate.py`: **create** the missing script `code/03_annotate.py` with the logic to merge peaks and annotate genomic context as described in the plan (FR-004). *Note: Replaces T059. Script created to match plan.*
- [X] T060_create Reconcile run-book vs implementation for `code/05_weights.py`: **create** the missing script `code/05_weights.py` with the logic to compute weights as described in the plan (FR-015). *Note: Replaces T060. Script created to match plan.*
- [X] T061_create Reconcile run-book vs implementation for `code/08_visualize.py`: **create** the missing script `code/08_visualize.py` with the logic to generate bigWig tracks as described in the plan (FR-009). *Note: Replaces T061. Script created to match plan.*

---

## Phase N+2: Final Verification & Handoff

**Purpose**: Ensure the pipeline is robust, documented, and ready for real data execution.

- [ ] T62a [P] **Syntax Validation**: Run `python -m py_compile` on all Python scripts and `R -e "source('...')"` on all R scripts to verify **zero syntax errors**. **Output**: `results/syntax_validation.log`. *Note: Must be run before final handoff.*
- [ ] T62b [P] **Path Dependency Verification**: Run a static analysis on `code/` to verify that **all file paths** referenced in scripts match the `plan.md` structure and exist (or are expected to be generated). **Output**: `results/path_dependency_report.json`. *Note: Must be run before final handoff.*
- [ ] T62c [P] **Mock Data Flow Simulation**: Run a **dry-run** of the entire pipeline using `data/raw/mock/` to verify that **all scripts execute without syntax errors** and that **all file paths in `code/` match the `plan.md` structure**. **Output**: `results/dry_run_manifest.json`. *Note: Must be run before final handoff. Uses mock data only for this verification step.*
- [ ] T63_contrib_impl [P] Generate a **final `CONTRIBUTING.md`** file that includes: (1) instructions for adding new GEO accessions to `manifest.yaml`, (2) guidelines for extending the FDR sweep in `code/03_call_peaks.sh`, and (3) a troubleshooting section for common MACS2 or LMM errors. *Note: Ensures future maintainability.*
- [X] T064 [P] Create a **`run_pipeline.sh` wrapper** that accepts a `--config` flag pointing to a custom `manifest.yaml` and `--output-dir` flag to specify the results directory, allowing for flexible execution in different environments. *Note: Enhances usability for external collaborators.*
- [ ] T65_validate_outputs_impl [P] Implement a **`validate_outputs.py`** script that checks the final `results/` directory for the presence of all expected files (ranked tables, PDF, bigWig, stats) and verifies their schema compliance against `contracts/`. *Note: Provides a final sanity check before release.*