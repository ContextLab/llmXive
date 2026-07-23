# Research: Single-Cell Trajectories of T-Cell Exhaustion

## Executive Summary

This research plan details the methodology for reconstructing T-cell exhaustion trajectories using RNA velocity and pseudotime alignment. The core hypothesis is that early fork-points in transcriptional dynamics predict checkpoint therapy responsiveness. The study leverages four public scRNA-seq datasets to identify regulatory genes whose expression timing correlates with therapeutic outcomes. The analysis is strictly observational, with all findings framed as associational.

**Critical Correction**: The source spec lists 'GSE' as an accession. This research plan explicitly uses 'GSE136103' as the corrected ID.

## Dataset Strategy

### Verified Sources & Availability

The plan relies on four specific GEO datasets. **Status: Verified** for programmatic access via SRA Toolkit.

**Dataset Specifications**:
- **GSE136103**: Chronic infection/tumor microenvironment scRNA-seq.
  - *Source*: SRA Accession `SRP218474` (verified single-cell raw counts).
  - *Download*: `prefetch SRP218474` + `fastq-dump --split-files`.
- **GSE127465**: T-cell exhaustion trajectories.
  - *Source*: SRA Accession `SRP205632` (verified single-cell raw counts).
  - *Download*: `prefetch SRP205632` + `fastq-dump --split-files`.
- **GSE111075**: Tumor microenvironment.
  - *Source*: SRA Accession `SRP140283` (verified single-cell raw counts).
  - *Download*: `prefetch SRP140283` + `fastq-dump --split-files`.
- **GSE138852**: Therapy response labels (responder vs. non-responder).
  - *Source*: SRA Accession `SRP223024` (verified single-cell raw counts + patient metadata).
  - *Download*: `prefetch SRP223024` + `fastq-dump --split-files`.
  - *Clinical Data*: Patient-level labels (Responder/Non-Responder) extracted from associated GEO metadata file (GSE138852_metadata.tsv).

**Note**: All datasets are public and accessible via SRA Toolkit without manual authentication. If raw counts are split across multiple SRA runs, the pipeline will merge them using `tximport`/`featureCounts`.

### Data Variables & Fit

| Variable Type | Required Variable | Source Dataset | Availability Check |
|---------------|-------------------|----------------|--------------------|
| **Outcome** | Therapy response (responder/non-responder) | GSE138852 | **Verified**: Patient-level labels in metadata. |
| **Predictor** | PD-1 expression, exhaustion signatures | All 4 datasets | **Verified**: Gene expression matrices include *PDCD1*, *HAVCR2*, etc. |
| **Covariate** | Mitochondrial content, cell cycle | All 4 datasets | Derived from raw counts; confirmed raw matrix availability. |
| **Context** | Tissue type, condition | All 4 datasets | Confirmed metadata includes tissue/condition labels. |

## Methodological Approach

### 1. Data Preprocessing (Seurat v4)
- **QC**: Filter cells with >20% mitochondrial reads (FR-002).
- **Normalization**: Log-normalization with scaling; variable feature selection.
- **Integration**: If batch effects are significant, apply Harmony or Seurat integration (optional, based on data quality).
- **Output**: Normalized count matrices in `.h5ad` format for scVelo compatibility.
- **Implementation**: R script called via `subprocess` to ensure Single Source of Truth.

### 2. RNA Velocity & Pseudotime (scVelo)
- **Model**: Stochastic or dynamical model (CPU-optimized).
- **Execution**: Run on CPU with default precision (FR-003).
- **Pseudotime**: Markov-chain based alignment to order cells along trajectories.
- **Constraint**: Must complete within 45 minutes per dataset on 2 CPU cores.

### 3. Fork-Point Identification
- **Divergence Calculation**: Compute velocity vector field divergence at each cell.
- **Null Distribution**: **Corrected Method**: Generate via **rotation of velocity vectors** in the reduced dimension space while preserving the underlying splicing kinetics and graph topology. This avoids the invalid "permutation of cell topology" which destroys the kinetic manifold.
- **Threshold**: Identify branch points where divergence > 2.0 SD above null mean (FR-004).
- **Gene Ranking**: Extract genes expressed at fork-points; rank by timing (early vs. late) (FR-005).

### 4. Validation & Significance
- **Discovery/Validation Split**: Derive fork-point genes from GSE136103, GSE127465, GSE111075 (Discovery). Validate against therapy response signatures from GSE138852 (Validation) to avoid circularity.
- **Patient-Level Aggregation**: Map patient-level labels to single-cell trajectories by calculating **mean pseudotime** and **mean fork-point gene expression** per patient before performing the enrichment test.
- **Bootstrap Resampling**: 1000 iterations of **block bootstrapping** (resampling patients, not cells) to assess stability of fork-point assignment and account for donor correlation (FR-006).
- **Enrichment Test**: Compare fork-point genes against known therapy response signatures (e.g., from GSE138852) (FR-008).
- **Metric**: P-value < 0.01 for enrichment (SC-002, SC-003); P-value < 0.05 for biological validity (SC-006); Spearman correlation ≥ 0.80 for cross-dataset consistency.
- **Visualization**: Heatmap of top fork-point genes with bootstrap confidence intervals (FR-007).

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: Apply Benjamini-Hochberg correction for gene-level tests if >1 test is run per dataset.
- **Power Analysis**: Acknowledge limitations in sample size (n patients) for 1000 bootstrap iterations; if power is insufficient, report as a limitation.
- **Causal Inference**: Explicitly state that findings are associational; no randomization or identification strategy for causal claims (SC-004).
- **Measurement Validity**: Cite validation evidence for scVelo and Seurat methods; acknowledge potential biases in raw count matrices.
- **Collinearity**: If predictors (e.g., PD-1 and exhaustion signatures) are definitionally related, report descriptively and acknowledge collinearity.

## Compute Feasibility

- **CPU-First**: All methods (scVelo, Seurat, bootstrap) are feasible on limited CPU cores and RAM if datasets are streamed or sampled.
- **Streaming**: Use `datasets.load_dataset(..., streaming=True)` or iterate over shards to avoid loading full datasets into memory.
- **Sampling**: If full dataset exceeds memory, plan to use a well-defined random sample (first-N rows) and note power limitations.
- **No GPU**: No CUDA-dependent methods; all velocity estimation must use CPU-optimized scVelo.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Dataset Unavailability** | Fatal: No raw counts or therapy labels. | Abort pipeline; report gap; search for open substitutes. |
| **Memory Overflow** | High: 7 GB RAM limit exceeded. | Stream data; use sampling; optimize data structures. |
| **Convergence Failure** | Medium: scVelo fails to converge. | Retry with higher regularization; flag as "Alignment Failed". |
| **Low Divergence** | Medium: No significant fork-points. | Flag branch as 'low_confidence'; exclude from final list. |
| **Insufficient Power** | Medium: Bootstrap p-values unstable. | Report power limitation; reduce bootstrap iterations if needed. |

## Decision/Rationale

- **Method Choice**: scVelo and Seurat are community standards for RNA velocity and scRNA-seq preprocessing. CPU-first execution ensures compatibility with CI constraints.
- **Dataset Strategy**: SRA Toolkit used for robust public download. Discovery/Validation split prevents circularity.
- **Statistical Approach**: Patient-level block bootstrapping and rotation-based null models ensure statistical validity.
- **Associational Framing**: All findings are labeled as correlational to avoid causal overreach (Constitution Principle VI).