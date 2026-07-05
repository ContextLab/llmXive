# Research: Predicting Coral Resilience to Thermal Stress Using Publicly Available Genomic Data

## Dataset Strategy

The project relies on NCBI BioProject **PRJNA292777** for *Acropora millepora* RNA-seq data.
**Verified Source**: NCBI SRA (BioProject PRJNA292777).
**Access Method**: `curl`/`wget` for streaming FASTQ downloads to avoid large local storage and RAM spikes.

### Reference Transcriptome Strategy
Quantification (Salmon) requires a reference transcriptome. PRJNA292777 contains raw reads but not the reference assembly.
**Source**: NCBI RefSeq Assembly **GCF_000163615.2** (*Acropora millepora* v2.0).
**Action**: The pipeline MUST explicitly download this reference assembly as a distinct step before quantification.
**Fallback**: If the BioProject metadata does not explicitly link a transcriptome, the pipeline defaults to GCF_000163615.2, the standard reference for this species.
**Memory Management**: The reference index is built once and stored on disk. FASTQ files are streamed against this index; the index is memory-mapped to stay within a constrained memory limit.

### Metadata Extraction Strategy
**Primary**: Parse SRA Run Selector metadata or BioSample CSV linked to PRJNA292777 to extract "Heat" vs "Control" labels.
**Fallback**: If automated parsing fails (e.g., unstructured text), the pipeline attempts to map samples using BioSample Accession IDs found in the BioProject summary.
**Failure Mode**: If neither method yields a valid "treatment" label for a sample, that sample is excluded, and a structured error log reports the exclusion count. The pipeline does not assume a CSV exists; it derives the phenotype record from the source metadata.

## Statistical Rigor & Methodology

### Differential Expression (DE)
- **Method**: Negative Binomial GLM with **Empirical Bayes Dispersion Shrinkage**.
- **Implementation**: `pydeseq2` (Python). This is the verified Python port of DESeq2. It replicates the dispersion shrinkage mechanism essential for stabilizing variance in low-replication RNA-seq data, avoiding the inflated false positives of generic `statsmodels` GLMs.
- **Design**: The model uses `~ treatment` (Heat vs. Control). The dataset is a controlled laboratory experiment; the analysis treats "treatment" as the primary factor, acknowledging the experimental design while noting that causal inference depends on the original randomization (assumed from metadata).
- **Multiple Testing**: Benjamini-Hochberg (FDR) correction applied to all p-values (FR-004, SC-005).

### Pathway Enrichment (GSEA)
- **Method**: Gene Set Enrichment Analysis (GSEA) using `gseapy`.
- **Input**: Ranked list of all genes (sorted by signal-to-noise ratio or log2FC), not just a binary "significant" cutoff.
- **Rationale**: GSEA detects subtle, coordinated shifts in pathways that binary ORA (Over-Representation Analysis) misses, addressing the statistical fragility of the "Top N" approach.
- **Correction**: FDR applied to pathway enrichment scores (NES).
- **Threshold**: FDR < 0.1 for biological plausibility (SC-003).

## Compute Feasibility Plan

- **RAM Constraint (7 GB)**:
  - **FASTQ Handling**: Stream data. Do not load entire FASTQ files into memory.
  - **Reference Index**: Memory-mapped index; built once, reused.
  - **Count Matrix**: Store as sparse matrix (CSR format) in `scipy.sparse`.
  - **DESeq2**: `pydeseq2` is optimized for CPU and low RAM.
  - **Parallelism**: Use `--threads 1` or `--jobs 1` for all tools to prevent memory fragmentation.
- **Disk Constraint (GB)**:
  - Delete intermediate FASTQ files after quantification.
  - Compress intermediate files (`.gz`).
- **Time Constraint (h)**:
  - Quantification (Salmon) is fast.
  - DE analysis is fast for < 20k genes.
  - Network download is the bottleneck. Retry logic (exponential backoff) implemented.

## Rationale & Decisions

1. **Why `pydeseq2`?** It provides the necessary dispersion shrinkage of DESeq2 without the memory overhead of `rpy2` or R, ensuring statistical rigor and CPU feasibility.
2. **Why `gseapy` (GSEA)?** It uses the full ranked gene list, increasing power to detect pathway shifts compared to binary ORA.
3. **Why separate Reference Download?** The raw reads in PRJNA292777 cannot be quantified without a reference transcriptome. This step is critical and must be explicit.
4. **Why streaming?** To prevent OOM on the CI runner during the download/quantification phase.