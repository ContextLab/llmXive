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
- [X] T052a [P] Validate `research.md` to extract **verified, actual GEO/SRA accessions** for ChIP-seq, eQTL, Hi-C, and ATAC-seq; **if placeholders (e.g., GSE####) are found, log them as expected template values** and output `data/verified_accessions.yaml`; **do NOT abort** on placeholders (FR-001, Constitution Principle II, Spec Assumptions) AND output `data/validation_log.yaml` confirming all accessions (real or placeholder) are recorded (FR-001).
- [X] T052 [P] Populate `manifest.yaml` using the **verified accessions** (including placeholders) from `data/verified_accessions.yaml` (output of T052a); **abort only if required fields are missing** (FR-001, Spec Assumptions)
- [X] T003 Implement `code/00_verify_manifest.py` to validate `manifest.yaml` and **log warnings if any accession is a placeholder (e.g., GSE####)** but **do NOT abort**; ensure the pipeline can proceed with template data (FR-001, Constitution Principle II, Spec Assumptions).
- [X] T052b [P] Implement `code/00_verify_data_accessions.py` to **automatically verify** `manifest.yaml` against `data/verified_accessions.yaml` and **abort with a fatal error** if any required accession remains a placeholder (e.g., GSE####) before pipeline execution; **do NOT** rely on manual verification (FR-001, Constitution Principle II). *Note: Replaces manual check in T057.*
- [X] T004 [P] Setup Git hooks for large file tracking (LFS) for raw data references; explicitly configure `.gitattributes` to track `data/raw/*` and `tracks/*`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. **Note: Phase 3 depends on T042 and T051 completion explicitly.**

- [X] T005 Implement `code/01_download_data.sh` to fetch raw FASTQ from GEO/SRA using `manifest.yaml`, verify MD checksums, and **abort with a fatal error listing missing TF-condition pairs** if any required run is absent (FR-001, Edge Cases).
- [X] T006 Implement `code/02_preprocess_chipseq.sh` for adapter trimming (`fastp`) and alignment (`bowtie2`, ≤2 threads, MAPQ ≥ 30) (FR-002)
- [X] T007 [P] Implement `code/03_call_peaks.sh` to run **MACS2 peak calling** with FDR sweep across a range of significance thresholds and output peak counts per threshold; **output** `data/processed/peaks_fdr_<threshold>.bed` for each threshold (FR-003). *Note: This task performs the MACS2 peak calling sweep required by FR-003.*
- [X] T007_sweep [P] Implement `code/03_sweep_analysis.R` to: (1) extract top-20 CREs from each FDR threshold (0.01, 0.05, 0.10) **sorted by adjusted p-value (primary) and absolute β₁ magnitude (tie-breaker)**; (2) compute the **top-20 CRE overlap percentage** (Jaccard index) between thresholds; (3) re-run the **Linear Mixed-Model (LMM)** analysis on each peak set to generate β₁ estimates; (4) **output** `data/processed/top_cres_threshold_<threshold>.tsv`, `results/cre_intersections.tsv`, `results/fdr_overlap_stats.csv`, and `results/fdr_sweep_summary.tsv` (FR-003, SC-004). *Note: Consolidated T007b1-b3 and T007c1-c3 into a single task. Explicitly defines output schema and sorting logic.*
- [X] T007c [P] Implement `code/03c_extract_peak_signals.R` to extract normalized peak signal (RPKM/counts) for each TF-condition pair from the BAM files (T006) for all CREs in `data/processed/CRE_merged.bed`; **output** `data/processed/peak_signal_matrix.tsv` (columns: cre_id, tf_id, condition, signal). *Note: Required input for VIF calculation (T013b). Removed [P] tag as it depends on T006.*
- [X] T008 Implement `code/04_merge_annotate.sh` to merge peaks across TFs/conditions and annotate promoter (≤500bp) vs distal (>500bp), storing result in `data/processed/CRE_merged.bed` (FR-004)
- [X] T042 [P] Implement `code/04b_load_hic.sh` to download Hi-C contact matrix (GSE) from Yeast 3D Genome Atlas, process to **High resolution cooler format**, and output `data/processed/hic_matrix_10kb.cool`; **abort if T003 verification fails** (FR-014). *Note: This is a strict prerequisite for T013a2 (Phase 3). **Explicitly aborts if placeholder accession is not resolved.***
- [X] T009a Implement `code/06a_define_null_regions.sh` to define distal null regions (>10kb from genes) and output `data/processed/null_regions.bed`
- [X] T009b Implement `code/06b_compute_null_signal.sh` to compute signal in null regions using `data/processed/null_regions.bed` and output `data/processed/null_region_signal.bed`. *Note: Depends on T009a. Removed [P] tag as it depends on T009a.*
- [X] T043 Implement `code/05b_compute_delta_signal.py` to explicitly compute **ΔPeakSignal** (CRE signal minus null signal) by joining `data/processed/CRE_merged.bed` signal with `data/processed/null_region_signal.bed`, outputting `data/processed/delta_peak_signal.tsv` (FR-015). *Note: Depends on T009b. Runs in parallel with other Phase 2 tasks not dependent on T009b. Removed [P] tag as it depends on T009b.*
- [X] T019 [P] Add error handling in `code/01_download_data.sh` to abort if required ChIP-seq runs are missing (Edge Case) and to handle eQTL column validation (FR-011): fatal error if entire stress column missing, warning if individual genes missing
- [X] T051 [P] Implement `code/01b_validate_eqtl_schema.py` to explicitly verify the eQTL dataset contains the three required stress columns (heat-shock, osmotic, oxidative) and effect sizes; raise a **fatal error** if any entire stress column is missing (FR-011), and log warnings for individual missing genes (FR-011). *Note: Runs after T005, before T013a.*
- [X] T010 [P] Create unit tests for data validation logic in `tests/unit/test_manifest_validation.py`
- [X] T045 [P] Implement `code/01_stream_eqtl.py` to **download the eQTL dataset to `data/raw/` as a static, checksummed file first**, then **stream it** using `datasets.load_dataset(..., streaming=True)` from the local file to process in chunks; this ensures reproducibility on fresh runners (Constitution Principle I) while preserving statistical power. *Note: Must complete before T013a and T016.*

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate a ranked CRE catalog (Priority: P1) 🎯 MVP

**Goal**: Produce `results/CRE_ranked_<stress>.md` with significant CREs (q ≤ 0.05) including coordinates, TFs, log₂FC, β₁, and q-value.

**Independent Test**: Execute `run_pipeline.sh` on sample manifest; verify `results/CRE_ranked_heatshock.md` exists, contains headers, and lists at least one CRE with q ≤ 0.05.

### Tests for User Story 1 (OPTIONAL) ⚠️

- [X] T011 [P] [US1] Contract test for output schema in `tests/contract/test_cre_schema.py`
- [X] T012 [P] [US1] Integration test for pipeline end-to-end on mock data in `tests/integration/test_pipeline_us1.py`: **Input**: `tests/data/mock/synthetic_fastq/*`; **Output**: `results/CRE_ranked_heatshock_mock.md`; **Assertion**: File exists, header matches schema, row count > 0 (FR-008)

### Implementation for User Story 1

- [X] T013a Implement `code/05a1_validate_motif.py` to: (1) perform motif scanning (FIMO, p < 1e-4) on distal CREs (>500 bp); (2) **output** `data/processed/motif_validation_flags.tsv` containing columns `cre_id`, `motif_validated`, `motif_score` (FR-014). *Note: Depends on T008 and T045. **Removed [P] tag as it depends on T008 and T045 (Phase 2). Must run sequentially after Phase 2 completion.** Split from T013a. **Corrected**: Does NOT depend on T042 (Hi-C).*
- [X] T013a2 [P] Implement `code/05a2_validate_hic.py` to: (1) load Hi-C data from `data/processed/hic_matrix_10kb.cool` (output of T042); (2) validate distal CREs; **set `hic_validated=TRUE` if contact frequency > 100 reads**; (3) **output** `data/processed/hic_validation_flags.tsv` containing columns `cre_id`, `hic_validated`, `hic_score` (FR-014). *Note: Depends on T042 and T008. **Removed [P] tag as it depends on T042 and T008 (Phase 2). Explicit dependency on T042 added.** If T042 fails, this task is skipped and T013a2b generates a placeholder.*
- [X] T013a2b [P] Implement `code/05a2b_handle_hic_skip.py` to **generate a placeholder `hic_validation_flags.tsv`** with `hic_validated=FALSE` for all CREs if T042 fails or Hi-C data is missing, ensuring T013c has a valid input file (FR-014, Ordering). *Note: Handles the case where T042 fails, preventing T013c from failing due to missing file.*
- [X] T013b Implement `code/05b_check_collinearity.py` to calculate VIF for each CRE by regressing the signal of each TF against all other TFs binding that specific CRE using `data/processed/peak_signal_matrix.tsv` (T007c); **flag** CREs with VIF > 5 as "collinear" and **output** `data/processed/vif_flags.tsv` containing columns `cre_id`, `vif_score`, `is_collinear` (FR-012). *Note: Depends on T008 and T007c. **Removed [P] tag as it depends on T008 and T007c (Phase 2). Must run sequentially after Phase 2 completion.** Runs in parallel with T013a/T013a2.*
- [X] T013c_pre [P] Implement `code/05c_pre_filter.py` to generate the **'full set' (pre-FR-014)** artifact `data/processed/cre_all_vif_filtered.tsv` by applying only FR-011 and FR-012 filters, **before** applying FR-014 (Motif/Hi-C) (FR-017). *Note: Required input for T026 (bias analysis). Ensures T026 compares pre-FR-014 vs post-FR-014.*
- [X] T013c Implement `code/05c_compute_weights.py` to: (1) join `data/processed/motif_validation_flags.tsv` (T013a), `data/processed/hic_validation_flags.tsv` (T013a2 or T013a2b), and `data/processed/vif_flags.tsv` (T013b); (2) **retain CRE if `motif_validated` is TRUE OR `hic_validated` is TRUE** (inclusive OR); **if neither is TRUE, exclude**; (3) exclude collinear CREs; (4) compute weights: **if** `motif_validated` is true, `weight = -log10(motif_score)`; **else if** `hic_validated` is true, `weight = log10(hi_c_score + 1)`; **else** exclude; (5) apply weights to `ΔPeakSignal` from `data/processed/delta_peak_signal.tsv` (T043); (6) **output** `data/processed/weights.tsv` containing columns `cre_id`, `gene_id`, `weighted_delta_peak_signal`, `weight_source`, `weight_value` (FR-015). *Note: Depends on T013a, T013a2/T013a2b, T013b, and T043. **Corrected logic to implement inclusive OR.** Note: Waits for T013a and T013a2 (or one if the other fails/skips) to complete to merge flags, but logic handles OR.*
- [X] T013c_test [P] [US1] Contract test for `data/processed/weights.tsv` schema in `tests/contract/test_weights_schema.py`
- [X] T016 Implement `code/06_fit_lmm.R` to fit a **Linear Mixed-Model (LMM)** per stress using the `lme4` R package (`lmer` function), specifying a fixed effect for `weighted_ΔPeakSignal` and **random intercepts for genes** (`(1|gene_id)`) to account for gene-specific variance (FR-005). **Explicitly avoids GLS approximation.** (FR-005, Plan Phase 6)
- [X] T023 Implement Likelihood-Ratio Test (LRT) in `code/06_fit_lmm.R` comparing full vs reduced model (FR-005)
- [X] T017 Implement Benjamini-Hochberg FDR correction in `code/06_fit_lmm.R` and enforce q ≤ 0.05 cutoff, **ensuring T018 consumes only this filtered subset** (FR-007)
- [X] T018 Implement `code/10_generate_reports.R` to generate `results/CRE_ranked_<stress>.md` sorted by q-value and |β₁|, containing **all significant CREs (q ≤ 0.05) derived from the FDR ≤ 0.05 threshold** (primary output), and **merge sweep results** from T007_sweep for robustness analysis (FR-008, SC-001, FR-003). *Note: Primary table uses FDR ≤ 0.05. Sweep results used for SC-004.*
- [X] T027 Add explicit disclaimer "results are associational, not causal" to all report outputs (FR-016), programmatically injecting into Markdown tables and PDFs

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical evidence of CRE contribution (Priority: P2)

**Goal**: Generate `results/Statistical_summary.pdf` with LRT results, empirical p-values, and variance explained (ΔR²).

**Independent Test**: Inspect PDF for β₁ significance (p < 0.05), empirical p-value from a sufficient number of shuffles, and ΔR² statement.

### Tests for User Story 2 (OPTIONAL) ⚠️

- [X] T020 [P] [US2] Contract test for statistical report schema in `tests/contract/test_stats_schema.py`
- [X] T021 [P] [US2] Integration test for permutation test logic in `tests/integration/test_permutation.py`

### Implementation for User Story 2

- [X] T022 Implement `code/07_permutation_test.R` for **spatially-constrained block permutation** (shuffles) to generate empirical p-value, outputting `results/permutation_pvalue.csv` (FR-006, US-2). *Note: Depends on T016 and T023 completion to obtain observed β₁.*
- [X] T049 [P] Implement `code/07_permutation_checkpoint.R` to include a **progress bar and checkpointing mechanism** for the shuffles; **checkpoint every fixed number of shuffles** to `results/permutation_checkpoint.pkl` (JSON schema: `{last_shuffle: int, p_values: array}`); **resume logic**: load last saved state and continue from the next shuffle (FR-006). *Note: Explicitly implements the shuffle requirement from FR-006 and SC-002, removing any '[deferred]' placeholders.*
- [X] T024 Implement variance explained (ΔR²) calculation in `code/06_fit_lmm.R` and `code/10_generate_reports.R`
- [X] T025 Implement GO enrichment analysis (hypergeometric test) in `code/10_generate_reports.R` for stress-response genes (FR-010)
- [X] T026 Implement bias sensitivity analysis in `code/08_sensitivity_analysis.R` comparing the **full set (pre-FR-014, i.e., `data/processed/cre_all_vif_filtered.tsv` from T013c_pre)** against the **filtered set (post-FR-014, i.e., `data/processed/weights.tsv` from T013c)** to explicitly **quantify selection bias** (calculate delta_beta1, delta_r2), outputting `results/bias_sensitivity.csv` (FR-017). *Note: Inputs: `data/processed/cre_all_vif_filtered.tsv` (full) vs `data/processed/weights.tsv` (filtered).*

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualize top CREs in genome browser (Priority: P3)

**Goal**: Generate bigWig tracks `tracks/<stress>_CRE_signal.bw` for IGV visualization.

**Independent Test**: Execute `run_pipeline.sh` on a sample manifest that has produced at least 10 significant CREs in `results/CRE_ranked_<stress>.md` (T018). **Verify** that `tracks/<stress>_CRE_signal.bw` exists, can be loaded into IGV, and that for the top 10 CREs (or all available if <10), the signal peaks match summit positions and correlate with log₂FC (ρ ≥ 0.8). **Note**: This test is dependent on the successful completion of US1 (T018) and assumes a sufficient number of significant CREs exist. If fewer than 10 CREs are found, the test validates all available rows.

### Tests for User Story 3 (OPTIONAL) ⚠️

- [X] T029 [P] [US3] Contract test for bigWig file generation in `tests/contract/test_bigwig_schema.py`: **Validate** `tracks/*.bw` against `contracts/bigwig_schema.yaml` using `bigWigSummary`
- [X] T030 [P] [US3] Integration test for summit match verification in `tests/integration/test_summit_match.py`: **Input**: `tracks/heatshock_CRE_signal.bw`, `results/CRE_ranked_heatshock.md`; **Output**: `results/summit_match_stats.txt`; **Assertion**: ρ ≥ 0.8 for top-10 (or all available if <10)

### Implementation for User Story 3

- [X] T031 Implement `code/11_create_bigwig.sh` using `deepTools bamCoverage` with `--normalizeUsing RPKM`, `--binSize`, input BAMs from T006, output `tracks/<stress>_CRE_signal.bw` (FR-009)
- [X] T032 [US3] Implement `code/09_summit_match.R` to: (1) **filter the ranked CRE table from T018 to the top 10 rows** (by q-value and |β₁|), or **all rows if fewer than 10 exist**; (2) compute Spearman ρ between `log₂FC` and `bigWig_signal` for these **top 10 (or all) CREs**; (3) explicitly calculate the **percentage of summit matches within ±5 bp** for these **top 10 (or all) CREs**. **Output** `results/summit_match_stats.txt` as TSV with columns `correlation_rho`, `match_percentage`, `exit_code` (always 0). **Log a warning** if `match_percentage` < 90% (SC-005). **Pipeline continues; warning logged** (Edge Case). *Note: Depends on T031 and T018. Does NOT exit with error code on low match percentage; matches SC-005 which states low match is a data quality observation, not a pipeline error. Explicitly filters to top-10 or all available.*
- [X] T032_test [P] [US3] Contract test for `results/summit_match_stats.txt` schema in `tests/contract/test_summit_match_schema.py`
- [X] T033 Integrate summit match results from `results/summit_match_stats.txt` into `results/Statistical_summary.pdf` (append as a new table in Section 4) (US-3)
- [X] T034 Implement optional ATAC-seq validation in `code/05_fetch_atac.sh` and `code/05_validate_cre_gating.py`: **If** ATAC-seq data exists in `data/raw/atac/`, run validation; **else** log "ATAC-seq validation skipped: data not found". Update `data/processed/CRE_validated.bed` with `validated_by_atac` column (FR-013)
- [X] T028 Generate `results/Statistical_summary.pdf` containing all required tables, plots, **and summit match integration from T033 (explicit table)**, **variance explained from T024**, **GO enrichment from T025**, and **bias analysis from T026** (FR-010). *Note: Depends on T024, T025, T026 (Phase 4) and T032, T033 (Phase 5). Use `ggplot2` for plots, `gridExtra` for layout. **Explicitly renders summit match stats from T032 as a table.***

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T035 Implement `code/12_generate_manifest.R` to record traceability for all outputs (Principle IV); **Output**: `results/traceability_manifest.json` with fields: input_hash, script_version, output_path
- [X] T036 Update `code/run_pipeline.sh` to orchestrate all phases in correct dependency order (Phase 2 → Phase 3 → Phase 4 → Phase 5); **Include** error handling (set -e), logging, and status checks
- [X] T037 Add comprehensive logging to all scripts; **Format**: ISO8601 timestamp, level, message; **Location**: `logs/pipeline.log`
- [X] T038 Run full pipeline on sample manifest to verify runtime ≤ 6h and memory ≤ 7GB; **Output**: `results/performance_report.csv` with metrics: total_time, peak_memory
- [X] T039 Update `quickstart.md` with final instructions and troubleshooting steps; **Include**: dependency installation, manifest creation, common errors
- [X] T040 [P] Cleanup temporary files and optimize disk usage in `data/processed/`; **Policy**: Delete `*.tmp`, `*.bam` (keep `*.bed`, `*.tsv`); **Command**: `find data/processed/ -name "*.tmp" -delete`

---

## Phase N+1: Revision & Robustness (Addressing Review Concerns)

**Purpose**: Improvements that affect multiple user stories

- [X] T044 [P] Refactor `code/01_download_data.sh` to **remove any `try/except` blocks that fallback to synthetic/mock data**; instead, ensure that any download failure or checksum mismatch raises a fatal error immediately with a clear message listing the missing accession (Constitution Principle II, FR-001).
- [X] T046 [P] Update `code/05_validate_cre_gating.py` to **explicitly state the sample size and representativeness limitation** in the output log if the eQTL dataset was streamed and filtered; ensure the code does not silently drop genes without logging a warning (FR-011 compliance).
- [X] T047 [P] Add a **pre-flight check** in `code/run_pipeline.sh` to verify that the `manifest.yaml` contains **real or placeholder URLs** (e.g., accept `GSE####` as a valid template); **do NOT abort** on placeholders, but log them as expected (FR-001, Spec Assumptions).
- [X] T048 [P] Implement `code/00_verify_data_integrity.py` to perform a **one-time sanity check** on the downloaded ChIP-seq and eQTL files (e.g., check file sizes, verify header columns) before processing begins, ensuring the data is not corrupted or empty before the pipeline proceeds.
- [X] T050 [P] Update `code/10_generate_reports.R` to **automatically detect and report** if the number of significant CREs is zero (q ≤ 0.05) and provide a diagnostic message suggesting potential causes (e.g., "No significant CREs found; check FDR threshold or data quality") rather than generating an empty table without context (US-1 Edge Case).
- [X] T053 [P] Implement `code/00_streaming_documentation.py` to **dynamically generate a `streaming_strategy.md` report** that explicitly documents the chunk size, total estimated rows, and the exact `datasets` streaming code snippet used in `code/01_stream_eqtl.py`. **Report Schema**: Must include fields `chunk_size`, `total_rows`, `code_snippet`. (Constitution Principle I, FR-011).
- [X] T054 [P] Add a **final assertion** in `code/04_filter.py` that verifies **zero** synthetic or mock data sources were loaded during the entire pipeline execution by scanning the `logs/pipeline.log` for keywords like "synthetic", "mock", "fallback", or "placeholder" (case-insensitive, regex `(?i)(synthetic|mock|fallback|placeholder)`); **abort** if any are found (Constitution Principle II, FR-001).
- [X] T055 [P] Refactor `code/01b_validate_eqtl_schema.py` to **explicitly log the exact number of genes dropped** due to missing fold-changes and the **percentage of the total cohort** this represents, ensuring the "warning" requirement in FR-011 is quantifiable and auditable (FR-011).
- [X] T056 [P] Implement `code/13_final_integrity_check.sh` to run a **comprehensive post-hoc validation** that compares the MD5 checksums of all final output files against a reference manifest generated at the start of the run, ensuring no data was altered or replaced during the pipeline execution (Constitution Principle III).
- [X] T057 [P] Update `quickstart.md` to include a **mandatory "Data Source Verification" section** that instructs users to manually verify the `manifest.yaml` accessions against the `data/verified_accessions.yaml` before running the pipeline, reinforcing the "No Placeholders" rule (FR-001, Edge Cases). *Note: Updated to accept placeholders as valid template inputs, but T052b now handles automated verification.*
- [X] T058 [P] Add a **runtime flag** `--strict-data-mode` to `code/run_pipeline.sh` that, when enabled, **disables all warnings** and forces a **fatal error** on any data anomaly (e.g., missing gene, low coverage), ensuring the pipeline never silently degrades to a lower-quality dataset (FR-011, FR-001).

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [X] T059_create Reconcile run-book vs implementation for `code/03_annotate.py`: **create** the missing script `code/03_annotate.py` with the logic to merge peaks and annotate genomic context as described in the plan (FR-004). *Note: Replaces T059. Script created to match plan.*
- [X] T060_create Reconcile run-book vs implementation for `code/05_weights.py`: **create** the missing script `code/05_weights.py` with the logic to compute weights as described in the plan (FR-015). *Note: Replaces T060. Script created to match plan.*
- [X] T061_create Reconcile run-book vs implementation for `code/08_visualize.py`: **create** the missing script `code/08_visualize.py` with the logic to generate bigWig tracks as described in the plan (FR-009). *Note: Replaces T061. Script created to match plan.*