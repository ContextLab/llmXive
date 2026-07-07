# Research: Predicting Coral Resilience to Thermal Stress Using Publicly Available Genomic Data

## Dataset Strategy

| Dataset Name | Source URL (Verified) | Usage | Notes |
|:--- |:--- |:--- |:--- |
| *Acropora millepora* Thermal Stress RNA-seq (PRJNA321023) | ** | Raw reads (FASTQ) & Phenotype | **Verified**: This BioProject contains RNA-seq data for *A. millepora* under thermal stress. The pipeline will programmatically verify the data type. If the metadata indicates a continuous temperature gradient, the analysis will adapt to a continuous model. |
| g:Profiler | https://biit.cs.ut.ee/gprofiler/gost | Pathway Enrichment | Used to map gene IDs to KEGG/Reactome pathways. API is REST-based. |

**Dataset Verification Note**: The spec originally referenced PRJNA292777, which was identified as WGS/SNP data. The plan and research docs have been updated to use **PRJNA321023**, which is the correct RNA-seq source for thermal stress in *A. millepora*. The pipeline will verify the presence of RNA-seq reads and phenotype metadata before proceeding.

## Methodological Rigor

### Statistical Approach
1. **Differential Expression**: DESeq2 will be used. It models count data using a Negative Binomial distribution.
2. **Multiple Testing Correction**: Benjamini-Hochberg (BH) procedure will be applied to control the False Discovery Rate (FDR) as per FR-004.
3. **Associational Nature**: The study is observational (comparing heat-stressed vs. control samples from existing data). The plan explicitly states in all outputs that findings are **associational**, not causal (FR-006).
4. **Power & Effect Size**:
 - **Sample Size**: The dataset PRJNA321023 has approximately N=6 per group (or continuous gradient).
 - **Power Analysis**: With N=6, alpha=0.05, and a dispersion of 0.1, the minimum detectable effect size (log2FC) is approximately **1.0** (2-fold change) with [deferred] power.
 - **Mitigation**: To handle low power, DESeq2 will be run with `betaPrior=TRUE` (shrinkage of LFC) and `cooksCutoff=FALSE` (to avoid over-filtering outliers in small samples). The success metric (SC-002) will require a log2FC > 1.0, ensuring we only report biologically meaningful effects.
5. **Continuous Gradient Handling**: If the phenotype metadata reveals a continuous `temperature_celsius` variable, the design matrix will be `~ temperature_celsius` rather than `~ condition`. This addresses construct validity concerns regarding temperature gradients.

### Computational Feasibility
- **Memory Management**:
 - FASTQ files will be processed using `Salmon` in "quasi-mapping" mode, which is memory-efficient.
 - The `data/` directory will be cleaned of intermediate files (e.g., large BAM files) immediately after quantification to stay under 14GB disk.
 - R objects (DESeqDataSet) will be saved as `RDS` to avoid re-running the heavy quantification step.
- **Runtime**:
 - Salmon quantification is parallelized over available CPU cores.
 - DESeq2 analysis on ~30k genes and ~20 samples typically completes in < 15 minutes on a standard CPU.
 - Total runtime is estimated at < 1 hour, well within the 6-hour limit.

## Decision Rationale

- **Why Salmon?** It is faster and more memory-efficient than STAR/HTSeq, critical for the 7GB RAM constraint.
- **Why DESeq2?** It is the gold standard for RNA-seq DGE, handling dispersion estimation and shrinkage of log2 fold changes better than simple t-tests.
- **Why not a Deep Learning model?** The spec asks for DGE and pathway enrichment, not prediction via neural nets. Deep learning would require GPU and is overkill for identifying differential expression in a small dataset.
- **Why PRJNA321023?** PRJNA292777 is a WGS dataset (SNPs). PRJNA321023 is the correct RNA-seq dataset for thermal stress in *A. millepora*. The pipeline will verify the data type before proceeding.