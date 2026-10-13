# Research: Quantitative Analysis of Gene Expression Dynamics during Human Brain Development

## Problem Statement
The project aims to identify critical "rewiring events" in gene regulatory networks (GRNs) during human brain development and correlate these events with vulnerability windows for neurological disorders.

## Dataset Strategy

| Dataset | Source/URL | Role | Variables |
|----------|------------|------|-----------|
| Human Fetal Brain Atlas | [Verified scRNA-seq Source] | Primary | Cell-level counts, developmental stage, donor ID |
| Independent scRNA-seq Cohort | [Verified scRNA-seq Source] | Topological Validation | Cell-level counts, developmental stage |
| BrainSpan (GSE36520) | `GEOparse` (GSE36520) | Expression Validation | Bulk expression counts, developmental stage |
| GWAS Catalogs | [Deferred to Implementation] | Reference | Risk genes for Schizophrenia, Autism, etc. |

**Data Availability**: The primary dataset will be a verified human fetal brain single-cell atlas. To satisfy Constitution Principle VII and FR-014, we use a two-pronged validation: (1) a separate single-cell cohort to confirm topological rewiring, and (2) the BrainSpan bulk dataset to confirm that the identified rewired hubs show corresponding expression shifts across development.

## Methodological Rationale

### 1. Integration and QC
- **Harmony**: Chosen for its efficiency in removing donor-specific batch effects while preserving biological variance across developmental stages.
- **LISI (Local Inverse Simpson's Index)**: Used to quantify batch mixing. A LISI $\ge 1.2$ ensures that cells of the same type from different donors are sufficiently mixed in the embedding.

### 2. Network Inference
- **GRNBoost2**: A gradient boosting regression approach that is computationally efficient for large single-cell datasets.
- **Sliding Windows**: By applying GRNBoost2 to pseudotime-ordered windows, we capture the *evolution* of the network rather than a static average.

### 3. Statistical Rigor
- **Hypergeometric Test**: Standard for gene set enrichment analysis (GSEA) to determine if rewired hubs are over-represented in disorder risk lists.
- **Permutation Testing**: 1,000 iterations will be used to build a null distribution of enrichment scores.
- **Multiple Comparison Correction**: Benjamini-Hochberg (FDR) will be applied to all p-values.

### 4. Validation Strategy
- **Topological Validation**: Because GRN inference requires cell-to-cell variance, we validate the "rewiring" (edge changes) using an independent single-cell dataset.
- **Expression Validation**: Because bulk RNA-seq (BrainSpan) lacks cell-level variance, we cannot re-infer networks. Instead, we validate the biological relevance of the hubs by testing if the identified "rewired hubs" are differentially expressed in bulk samples across the same developmental windows.

## Compute Feasibility

- **CPU-First Approach**: 
    - `scanpy` preprocessing and `GRNBoost2` fit within 7GB RAM for the BrainSpan/Atlas size.
    - To prevent OOM (Out of Memory) errors and avoid stochastic variance in rewiring detection, the pipeline will:
 1. Use a highly variable gene (HVG) filter to reduce the feature space to $\sim [deferred]$ genes.
 2. **Global Stratified Sampling**: If memory exceeds 6GB, a single global sample of $\sim [deferred]$ cells will be taken using a fixed seed (`random_state=42`) *before* windowing. This ensures that the same sampling bias is applied across all windows, preventing sampling noise from being identified as "rewiring events."
- **GPU Escape Hatch**: Not required for the current plan as no deep learning models are utilized.

## Decision/Rationale Summary
- **Trajectory**: Monocle3/Slingshot $\rightarrow$ provides the necessary continuous time axis for windowing.
- **Network**: GRNBoost2 $\rightarrow$ balances accuracy and CPU-tractability.
- **Validation**: Dual-track (scRNA-seq topological + Bulk expression) $\rightarrow$ ensures results are robust and not dataset-specific artifacts.
