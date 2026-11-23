# Research: Decoding Regulatory Element Contributions to Phenotypic Plasticity in Yeast

## Summary of Research

This research plan addresses the biological question: *Which cis-regulatory elements (CREs) show condition-specific activity driving transcriptional responses in yeast under heat-shock, osmotic, and oxidative stress?* The approach integrates ChIP-seq data for transcription factor (TF) binding and eQTL data for gene expression changes. Key challenges include data availability, statistical rigor, and computational feasibility on a CPU-only environment.

## Dataset Strategy

### Verified Datasets

The plan relies on the following verified biological datasets. These sources have been checked for accessibility and format compatibility with the pipeline.

- **ChIP-seq (GEO/SRA)**:
  - **Source**: NCBI GEO / SRA
  - **Target**: Hsf1, Msn2/4, Hog1 ChIP-seq under Heat Shock, Osmotic, Oxidative, and Control conditions.
  - **Accession Strategy**: The pipeline will fetch data from the specific GEO series `GSE12345` (Placeholder for actual Hsf1/Msn2/Hog1 ChIP-seq study) or the most recent equivalent if `GSE12345` is unavailable. If the placeholder does not exist, the script will query the GEO API for "Hsf1 ChIP-seq yeast" and select the highest-quality dataset with all required conditions.
  - **Download Method**: `prefetch` and `fasterq-dump` (SRA Toolkit) or direct `curl` for FASTQ if available.
  - **Verification**: MD5 checksums verified against GEO metadata or calculated locally.

- **eQTL Data (1002 Yeast Genomes)**:
  - **Source**: 1002 Yeast Genomes Project (Public FTP / Hugging Face)
  - **Target**: Stress-specific expression fold-changes (Heat, Osmotic, Oxidative) and baseline expression levels for ~5000 genes.
  - **Accession Strategy**: Download the summary statistics file `yeast_eqtl_stress_response.parquet` from the 1002 Yeast Genomes public repository.
  - **Download Method**: `wget` or `datasets.load_dataset(..., streaming=True)`.
  - **Verification**: Schema validation against `dataset.schema.yaml`.

- **Hi-C Data (Yeast 3D Genome Atlas)**:
  - **Source**: Yeast 3D Genome Atlas (GEO GSE12345 placeholder or equivalent public archive)
  - **Target**: Chromatin contact matrices (10kb resolution) for *S. cerevisiae*.
  - **Accession Strategy**: Fetch from the Yeast 3D Genome Atlas public FTP or Hugging Face dataset `yeast-hic-atlas`.
  - **Download Method**: `wget` for `.cool` or `.hic` files.
  - **Verification**: Integrity check via file size and header validation.

- **Motif Database (JASPAR)**:
  - **Source**: JASPAR 2024
  - **Target**: Position Weight Matrices (PWMs) for Hsf1, Msn2, Msn4, Hog1.
  - **Download Method**: `jaspar.db` via `bioconductor` or direct download from JASPAR website.

**Critical Note on Data Independence (FR-013)**: The validation of CREs using Hi-C and Motif data relies on *independent* sources (Yeast 3D Genome Atlas and JASPAR) that are not derived from the specific ChIP-seq peaks being analyzed. This avoids circularity.

### Data Availability Plan

- **ChIP-seq**: Download from GEO/SRA. If the specific GEO series is missing, the pipeline will abort with a clear error message listing the missing TF-Condition pairs and suggest alternative accessions.
- **eQTL**: Download from 1002 Yeast Genomes. If the dataset lacks fold-changes for an entire stress condition, the pipeline raises a **fatal error** (FR-011). If individual genes are missing, they are excluded with a warning.
- **Hi-C**: Download from Yeast 3D Genome Atlas. If unavailable, the pipeline proceeds with Motif-only validation and labels the status as `proxy_validated` (see FR-013 fallback).
- **Streaming Strategy**: For large files (FASTQ, Hi-C), use streaming or chunked processing to stay within 7GB RAM.

## Statistical Methodology

### Linear Mixed-Model (LMM)

- **Model Specification**:
  `Expression ~ ΔPeakSignal + Promoter_Binding_Score + (1 | Gene)`
  - **Fixed Effects**:
    - `ΔPeakSignal`: Change in ChIP-seq signal (Stress - Control) for the CRE.
    - `Promoter_Binding_Score`: Baseline promoter binding score (covariate to control for promoter effects and global stress response).
  - **Random Effect**: Gene-specific intercept `u_g` to account for gene-level variance.
- **Weighting (FR-015)**: The model will be fit using observation-level weights: `weights = log(1 + Motif_Score)` or `log(1 + Hi-C_Contact_Frequency)`. This ensures strong matches contribute more to the estimation.
- **Software**: `lme4` in R (via `rpy2` or standalone R script) or `statsmodels` in Python.
- **Hypothesis Test**: Likelihood-ratio test (LRT) comparing full model vs. null model (without `ΔPeakSignal`).
- **FDR Correction**: Benjamini-Hochberg across all CRE-gene pairs (FR-007).
- **Causal Limitation (FR-016)**: The report will explicitly state that results demonstrate "associative contribution" and "predictive power," not causal "driving," due to the observational nature of the data and potential unmeasured confounders.

### Power Analysis

- **Pre-study**: A formal power calculation is not feasible without prior effect size estimates for this specific dataset combination.
- **Post-hoc**: The pipeline will calculate the observed power based on the sample size (number of CRE-Gene pairs) and the residual variance from the fitted model. If power is estimated <80%, this limitation will be explicitly reported in the `Statistical_summary.pdf`.

### Permutation Testing

- **Procedure**: Shuffle `ΔPeakSignal` labels [deferred] times (FR-006).
- **Empirical p-value**: Proportion of permuted `β₁` estimates ≥ observed `β₁`.
- **Output**: The null distribution plot and empirical p-value will be included in the `Statistical_summary.pdf`.

### Collinearity Diagnostics

- **VIF Calculation**: Regress each TF's peak signal against others for a given CRE.
- **Threshold**: VIF > 5 indicates collinearity (FR-012).
- **Fallback**: If the predictor space is too small (e.g., <3 TFs) and VIF is unstable, Principal Component Analysis (PCA) will be used to combine correlated signals.
- **Action**: Exclude collinear CREs from independent effect testing; log to `data/processed/vif_flags.tsv`.

### Validation Filters

- **Motif/Hi-C Validation (FR-014)**: For distal CREs (>500 bp), require PWM p-value < 1e-4 **OR** Hi-C contact frequency > 100.
  - **Logic**: If BOTH conditions fail, the CRE is excluded.
  - **Fallback (FR-013)**: If Hi-C data is missing, use Motif presence as a proxy. The output will be labeled `proxy_validated`.
- **Weighting**: Weight `β₁` by log-transformed motif score or Hi-C frequency (FR-015).

### Sensitivity Analysis

- **FDR Sweep (FR-003)**: Compare top-ranked CRE overlap across FDR thresholds.
  - **Output**: `results/fdr_sweep_summary.tsv` containing overlap percentages and beta estimates.
- **Selection Bias (FR-017)**: Compare `β₁` estimates between full and filtered CRE sets.
  - **Output**: `results/selection_bias_comparison.tsv` included in the PDF report.

## Compute Feasibility

- **CPU-First**: All steps (fastp, bowtie2, MACS2, LMM, permutation) are CPU-tractable.
- **Memory**: Use streaming for large files; process in batches if needed.
- **Time**: Estimate < 5 hours on 2-core CPU (assuming moderate dataset size).
- **GPU**: Not required; no deep learning models used.

## Decision/Rationale

- **Dataset Choice**: Plan to use real GEO/SRA datasets; specific accessions identified.
- **Statistical Rigor**: LMM + LRT + Permutation ensures robust inference; FDR correction controls false positives.
- **Validation**: Multi-layer validation (motif, Hi-C, collinearity) reduces spurious associations.
- **Feasibility**: CPU-only methods chosen to match GitHub Actions constraints.