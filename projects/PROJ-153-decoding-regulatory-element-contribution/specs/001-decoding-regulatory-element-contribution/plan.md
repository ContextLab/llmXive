# Implementation Plan: Decoding Regulatory Element Contributions to Phenotypic Plasticity in Yeast

**Branch**: `001-yeast-cre-analysis` | **Date**: 2026-06-25 | **Spec**: `spec.md`

## Summary

This project implements a computational pipeline to **identify cis‑regulatory elements (CREs) that are *associated* with stress‑specific transcriptional responses** in *Saccharomyces cerevisiae* under heat‑shock, osmotic, and oxidative stress. 

**Critical Clarification**: The term "drive" in the research question is interpreted as "statistically predicts" in the context of observational data. **No causal claims are made.** The pipeline tests whether CRE activity (ΔPeakSignal) is a significant predictor of gene expression change (log₂FC) *conditional* on promoter-proximal binding, while explicitly acknowledging that confounding and reverse causality cannot be ruled out without perturbation data.

## Technical Context

- **Languages**: Python 3.11 (pipeline orchestration), R 4.3+ (mixed‑model analysis)
- **Core Tools**: `fastp`, `bowtie2`, `MACS2`, `bedtools`, `deepTools`, `lme4`, `clusterProfiler`
- **Compute Target**: GitHub Actions free tier (2 CPU, ≤7 GB RAM, ≤6 h)
- **Data Strategy**: 
  - **Real Data Mode**: Requires user-supplied GEO ChIP-seq, 1002 Yeast Genomes eQTL, and ATAC-seq data. If ATAC is missing, the pipeline runs in **ATAC-Deferred Mode** (results flagged as unvalidated).
  - **Synthetic Modes**: 
    1. **Standard synthetic** (`--generate-synthetic`) – generates mock data with a modest correlation for pipeline sanity checks.
    2. **Null synthetic** (`--null-synthetic`) – generates mock data with **zero correlation** between ΔPeakSignal and expression to validate false-positive control.

## Constitution Check

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | All scripts version‑controlled; random seeds pinned; deterministic data fetch. |
| **II. Verified Accuracy** | **FAIL** (missing verified GEO/eQTL/ATAC sources) | Pipeline aborts if real data is missing; synthetic modes used for CI only. |
| **III. Data Hygiene** | PASS | Raw data immutable; checksums recorded; every transformation writes a new file. |
| **IV. Single Source of Truth** | PASS | All statistics generated directly from processed files; no manual entry. |
| **V. Versioning Discipline** | PASS | Content hashes stored in `state/`. |
| **VI. Computational Pipeline Transparency** | PASS | `run_pipeline.sh` orchestrates each step; each tool logs version and parameters. |
| **VII. Statistical Reporting Rigor** | **CONDITIONAL PASS** | LMM, likelihood‑ratio test, BH correction, 10 k permutation, and SIMEX are scripted. **ATAC validation** is deferred if data is missing, and results are flagged accordingly. |

## Project Structure

```
code/
├── pipeline/
│   ├── 01_download.sh                # FR-001: download & MD5 verification
│   ├── 02_preprocess.py              # FR-002: fastp + bowtie2
│   ├── 03_peak_calling.py            # FR-003: MACS2 sweep (0.01,0.05,0.10)
│   ├── 04_merge_annotate.py          # FR-004: merge peaks, annotate context
│   ├── 05_atac_validation.py        # FR-013: ATAC validation (skipped if missing)
│   ├── 06_me_error_correction.py    # FR-012 extension: SIMEX correction (Poisson-based)
│   ├── 07_summit_match.py            # SC-005: summit‑match % calculation
│   ├── 08_visualize.py               # FR-009: deepTools bigWig generation
│   └── 09_stats.py                   # FR-005, FR-006, FR-007, FR-008
├── utils/
│   ├── config.py                     # thresholds, seeds, paths
│   └── validators.py                 # FR-011, FR-012, FR-014 checks
├── reports/
│   └── generate_pdf.py               # FR-010: summary PDF (includes ATAC status)
├── main.py                           # entry point
└── tests/...
data/
├── raw/                               # GEO FASTQs (git‑ignored / LFS)
├── processed/                         # BAM, BED, tables
└── external/                          # eQTL CSVs, ATAC narrowPeak (optional)
results/
├── CRE_ranked_<stress>.md
├── Statistical_summary.pdf
└── tracks/<stress>_CRE_signal.bw
```

## Phase Plan & FR/SC Mapping

### Phase 0: Data Acquisition & Validation
| Step | Description | FR/SC |
|------|-------------|-------|
| 0.1 | **Download** raw ChIP‑seq FASTQ files from GEO (or abort) – MD5 verification. | FR‑001 |
| 0.2 | **Validate** eQTL file contains `log2FC` for all three stresses and promoter binding scores. Abort with explicit error if any column missing. | FR‑011 |
| 0.3 | **Check ATAC data**: If ATAC-seq file is missing, set `validation_mode = "ATAC-Deferred"` and proceed. If ATAC is present, set `validation_mode = "ATAC-Validated"`. **Do not abort** if ATAC is missing; instead, flag all results as unvalidated. | FR‑013 |
| 0.4 | **Synthetic modes**: `--generate-synthetic` (correlated) or `--null-synthetic` (zero correlation). | — |

### Phase 1: Preprocessing & Peak Calling
| Step | Description | FR/SC |
|------|-------------|-------|
| 1.1 | **Adapter trimming** with `fastp`; **Alignment** with `bowtie2` (≤2 threads); retain uniquely mapped reads (MAPQ ≥ 30). | FR‑002 |
| 1.2 | **Peak calling** with `MACS2` at FDR = 0.01 (primary) **and** a sensitivity sweep at 0.01, 0.05, 0.10. For each threshold, record peak counts. | FR‑003 |
| 1.3 | **Overlap calculation**: for each pair of thresholds, compute percentage overlap of the top‑20 CREs (by q‑value). If < 20 CREs exist, compute on the available set and flag as "Fallback: N < 20". Store as SC‑004 metric. | SC‑004 |
| 1.4 | **Merge** overlapping peaks across TFs/conditions; annotate as *promoter* (≤ 500 bp upstream) or *distal* (> 500 bp). Export BED. | FR‑004 |
| 1.5 | **ATAC validation**: If `validation_mode == "ATAC-Validated"`, intersect CREs with ATAC narrowPeak; retain only CREs with ATAC support. If `validation_mode == "ATAC-Deferred"`, skip this step and set `validated_by_atac = False` for all CREs. | FR‑013 |
| 1.6 | **Motif scoring**: for distal CREs, compute TF‑motif match score (e.g., FIMO). Store as `motif_score` for weighting in Phase 2. | (supports weighting in Phase 2) |

### Phase 2: Statistical Modeling
| Step | Description | FR/SC |
|------|-------------|-------|
| 2.1 | **Collinearity diagnostics**: compute VIF for all predictors per CRE; flag VIF > 5 and set `is_collinear` = True (exclude from independent testing). Report collinearity as a biological limitation, not a pipeline error. | FR‑012 |
| 2.2 | **Estimate measurement‑error variance**: If technical replicate FASTQs are present, compute per‑base coverage variance across replicates. **Otherwise**, use a **Poisson noise model** based on sequencing depth to estimate measurement error variance. This value (`error_variance_lambda`) is supplied to SIMEX. | (supports FR‑012) |
| 2.3 | **SIMEX correction**: apply SIMEX using the estimated error variance to obtain `beta_1_simex`. Record both raw and corrected estimates. | — |
| 2.4 | **Weighting**: incorporate `motif_score` as a predictor weight for distal CREs in the mixed model. | (addresses c529a358) |
| 2.5 | **Power Analysis**: Calculate detectable effect sizes given sample size (number of genes) and estimated variance. Report in PDF if power < 80% for small effects. | (addresses methodology-c529a358) |
| 2.6 | **Fit Linear Mixed Model** per stress: `Y_g ~ β0 + β1·ΔPeakSignal + β2·PromoterBinding + (1|gene)`. Test fixed effect β1 via likelihood‑ratio test; output raw p‑value, BH‑adjusted q‑value, and `beta_1_simex`. **Explicitly state**: "Association tested; causality not inferred." | FR‑005, FR‑006, FR‑007 |
| 2.7 | **Permutation test**: 10 000 shuffles of `ΔPeakSignal` (1 000 in CI mode) to generate empirical null; record empirical p‑value. | FR‑006 |
| 2.8 | **Output**: Generate a **complete** markdown table of all CRE‑gene pairs with q ≤ 0.05 (no artificial limit). Include columns: coordinates, TFs, log₂FC, β1, `beta_1_simex`, q‑value, `is_significant`, `validated_by_atac`. | FR‑008, SC‑001 |
| 2.9 | **Variance explained**: compute ΔR² for the model with and without `ΔPeakSignal`; report in stats output. | SC‑002 |
| 2.10 | **GO enrichment**: hypergeometric test for stress‑response GO terms among top‑100 CRE‑genes; report odds ratio and BH‑adjusted FDR. | SC‑003 |

### Phase 3: Visualization & Reporting
| Step | Description | FR/SC |
|------|-------------|-------|
| 3.1 | **bigWig generation** (`deepTools bamCoverage`) for each stress condition to enable IGV loading. | FR‑009 |
| 3.2 | **Summit‑match calculation** (`07_summit_match.py`): compare MACS2 narrowPeak summit positions to the generated bigWig signal for the top‑10 CREs; compute `summit_match_pct_top10`. Report in PDF. | SC‑005 |
| 3.3 | **PDF summary** (`generate_pdf.py`): includes (i) peak counts per TF/condition, (ii) ΔR², (iii) GO enrichment, (iv) measurement‑error variance, (v) `summit_match_pct_top10`, (vi) sensitivity‑sweep overlap percentages (SC‑004), (vii) **ATAC validation status**, and (viii) **Causal Limitation Disclaimer**. | FR‑010 |
| 3.4 | **Final artifacts**: `results/CRE_ranked_<stress>.md`, `results/Statistical_summary.pdf`, `results/tracks/`. All files validated against contracts. | SC‑001, SC‑002, SC‑003, SC‑004, SC‑005 |

## Compute Feasibility Strategy

1. **Synthetic mode** (`--generate-synthetic` or `--null-synthetic`) creates minimal FASTQ (10 k reads) and a synthetic eQTL table that conform to `contracts/dataset.schema.yaml`. **Synthetic data only validates pipeline logic; it does not support biological conclusions.** All downstream results will be marked as *synthetic* in the PDF.
2. **Real‑data mode** runs on full datasets; memory‑efficient streaming and `bowtie2 --threads 2` keep usage ≤6 GB.
3. **Permutation scaling**: 10 k iterations for full run; 1 k for CI (documented in logs).
4. **Parallelism** limited to 2 CPU cores throughout.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Missing ChIP‑seq files | Abort with explicit list of missing TF‑condition pairs (FR‑001). |
| No peaks at FDR 0.01 | Abort with suggestion to relax to 0.05 (FR‑003). |
| Missing eQTL variables | Abort early (FR‑011). |
| Missing ATAC validation | **Do not abort**. Run in "ATAC-Deferred Mode" and flag results as unvalidated (FR‑013). |
| High collinearity | Exclude collinear CREs and report as a biological limitation (FR‑012). |
| Measurement error bias | Apply SIMEX correction using Poisson-based error estimation (new step). |
| Synthetic null mode not distinguishing signal | `--null-synthetic` generates data with zero correlation; pipeline must return non‑significant β1, proving false‑positive control. |
| Compute limits | Sample size limited in CI; full run respects RAM/CPU caps. |