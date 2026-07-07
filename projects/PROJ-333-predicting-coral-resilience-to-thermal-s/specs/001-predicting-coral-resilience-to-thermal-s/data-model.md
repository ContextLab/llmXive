# Data Model: Predicting Coral Resilience to Thermal Stress

## Overview

This document defines the data structures used throughout the pipeline, ensuring traceability from raw input to final statistical output.

## Entities

### 1. Raw FASTQ
-   **Source**: NCBI SRA (PRJNA321023)
-   **Format**: `.fastq` (gzipped)
-   **Constraints**: Must pass SHA256 checksum validation.
-   **Storage**: `data/raw/<sample_id>.fastq.gz`

### 2. Phenotype Metadata
-   **Format**: CSV
-   **Schema**:
    -   `sample_id`: String (matches FASTQ filename)
    -   `condition`: String (Optional, e.g., "Heat", "Control", or "Ambient")
    -   `temperature_celsius`: Float (Optional, continuous temperature value)
    -   `replicate`: Integer
    -   `batch`: String (Optional, if available)
-   **Storage**: `data/raw/phenotype.csv`
-   **Note**: The pipeline will automatically detect if `temperature_celsius` is present. If so, the analysis will use a continuous model; otherwise, it will default to a binary/grouped model based on `condition`.

### 3. Expression Matrix (Quantified)
-   **Source**: Salmon output (`quant.sf`) aggregated.
-   **Format**: TSV / Pandas DataFrame
-   **Schema**:
    -   Rows: Gene IDs (e.g., `Ammi_0001`)
    -   Columns: Sample IDs
    -   Values: Estimated counts (Integer/Float)
-   **Storage**: `data/processed/count_matrix.tsv`

### 4. DGE Results
-   **Source**: DESeq2 `results()` function.
-   **Format**: CSV
-   **Schema**:
    -   `gene_id`: String
    -   `baseMean`: Float (mean normalized count)
    -   `log2FoldChange`: Float
    -   `lfcSE`: Float (Standard Error)
    -   `stat`: Float (Wald statistic)
    -   `pvalue`: Float (Raw p-value)
    -   `padj`: Float (BH-adjusted p-value)
-   **Storage**: `data/processed/dge_results.csv`

### 5. Enrichment Results
-   **Source**: g:Profiler API
-   **Format**: JSON / CSV
-   **Schema**:
    -   `term_id`: String (e.g., `GO:0006950`)
    -   `term_name`: String (e.g., "Heat shock protein binding")
    -   `p_value`: Float
    -   `adjusted_p_value`: Float
    -   `genes`: List[String]
-   **Storage**: `data/processed/enrichment_results.csv`

## Data Flow Diagram

```mermaid
graph TD
    A[NCBI SRA PRJNA321023] -->|Download| B(Raw FASTQ + Phenotype)
    B -->|SHA256 Verify| C{Valid?}
    C -->|No| D[Error: Checksum Mismatch]
    C -->|Yes| E[Salmon Quantification]
    E -->|Output| F[Count Matrix]
    F -->|Filter Low Count| G[Filtered Matrix]
    G -->|DESeq2 (Continuous or Binary)| H[DGE Results]
    H -->|Filter FDR < 0.05| I[Significant Genes]
    I -->|g:Profiler API| J[Enrichment Report]
    J -->|Plot| K[Volcano Plot]
```