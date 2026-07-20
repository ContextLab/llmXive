# Research: Single-Cell Trajectories of T-Cell Exhaustion

## Executive Summary

This research plan investigates the transcriptional trajectories of T-cell exhaustion in chronic infection and tumor microenvironments. The primary objective is to identify early "fork-points" in these trajectories that determine responsiveness to checkpoint blockade therapy. The methodology leverages RNA velocity (scVelo) to infer the directionality of transcriptional changes and pseudotime alignment to order cells along developmental paths.

## Dataset Strategy

### Verified Sources & Access Strategy

The project specification lists four specific datasets: **GSE136103**, **GSE127465**, **GSE111075**, and **GSE138852**.

**Critical Feasibility Note**: The "Verified datasets" block provided for this project indicates **NO verified source found** (and thus NO direct programmatic URL) for any of the four required GEO datasets.
- **GSE136103**: NO verified source found.
- **GSE127465**: NO verified source found.
- **GSE111075**: NO verified source found.
- **GSE138852**: NO verified source found.

**Implication**: The GitHub Actions free-tier runner cannot fetch these datasets via `wget`/`curl` if they are behind GEO login walls, require manual SRA toolkit authentication, or are only available via interactive web portals.
- **Mitigation Strategy**: The implementation plan (`download_data.py`) will attempt to fetch these using the `GEOquery` (via R) or `scraping` methods *only if* public count matrices are available via `wget` on the GEO FTP server. If data access fails, the pipeline will halt without proceeding.
- **Fallback**: If the raw count matrices cannot be fetched programmatically without credentials, the project must be re-scoped to a methodological demonstration using a verified open dataset or synthetic data.

**Decision**: For the purpose of this plan, we assume the GEO FTP server (e.g., `ftp://ftp.ncbi.nlm.nih.gov/geo/series/GSE136nnn/GSE136103/`) hosts the count matrices. If this assumption fails during execution, the pipeline halts with a clear error, preventing fabrication.

**Alternative Open Data (Verified)**:
- **PD-1 (parquet)**: `https://huggingface.co/datasets/Tippawan/pd100/resolve/main/data/test-00000-of-00001.parquet` (Contains PD-1 related data, but likely processed/embedded, not raw counts).
- **GSE (json/parquet)**: Various HuggingFace datasets listed, but these appear to be model inputs/embeddings, not raw scRNA-seq count matrices suitable for scVelo.

*Conclusion*: The project is highly dependent on the availability of raw count matrices for the four GEO datasets. If these are not directly downloadable, the plan must pivot to a "Methodological Prototype" using an open dataset or synthetic data, explicitly stating the limitation.

## Methodology

### 1. Preprocessing (Seurat v4 Parameters)
- **Input**: Raw count matrices (genes x cells).
- **QC**: Filter cells with >20% mitochondrial reads and low gene counts.
- **Normalization**: Log-normalization (Seurat `LogNormalize` with scale factor [deferred]).
- **Variable Features**: Select top [deferred] variable genes.
- **Output**: Normalized count matrix.

### 2. RNA Velocity (scVelo)
- **Model**: Stochastic model is preferred for speed on CPU. Dynamical modeling may be applied to subsets if computational resources permit.
- **Context**: Run on CPU-only environment.
- **Pseudotime**: Use `scvelo.tl.pseudotime` based on the velocity graph.

### 3. Fork-Point Detection
- **Metric**: Statistical divergence of velocity vectors, determined using a permutation test of therapy response labels. Specifically, we will randomly shuffle the associations between cells and their therapy response (responder/non-responder) to generate a null distribution of branch point divergences. The observed divergence is considered significant if it exceeds the 95th percentile of the null distribution.
- **Null Model**: Permutation of therapy response labels across cells.
- **Threshold**: Divergence > 95th percentile of permutation test results.
- **Output**: Branch points with associated p-values.

### 4. Validation
- **Bootstrap**: 1,000 iterations resampling cells.
- **Metric**: Spearman rank correlation of top 3 genes across datasets *after* functional alignment via UMAP projection using shared marker genes (e.g., PD-1, CTLA-4). Jaccard index of top 50 fork-point genes.
- **Clinical Enrichment**: Enrichment analysis against therapy response signatures from GSE138852 if valid single-cell resolution labels are available; otherwise the SC-006 success criteria will be marked as 'Not Applicable'.

## Statistical Rigor & Limitations

- **Multiple Comparisons**: Bonferroni or FDR correction applied to p-values.
- **Power Analysis**: Acknowledge limited power due to small sample size and observational data. Bootstrap confidence intervals reported.
- **Causal Claims**: Strictly forbidden. All associations are interpreted as correlational, not causal.
- **Collinearity**: Acknowledge potential co-expression of exhaustion markers.

## Compute Feasibility (CPU-First)

- **Hardware**: GitHub Actions Free Tier (2 CPU, 7GB RAM).
- **Strategy**:
    - Use `scvelo` with `mode="stochastic"` for faster computation.
    - Stream data if possible; otherwise, process datasets sequentially.
- **GPU Escape Hatch**: Not applicable.

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
| :--- | :--- | :--- | :--- |
| **Data Unavailable** | High | Critical | Pipeline halts or switches to open substitute.|
| **Memory Overflow** | Medium | High | Process datasets sequentially; use sparse matrices; subsample. |
| **Velocity Convergence Failure** | Medium | Medium | Retry with higher regularization; exclude from final report.|
| **Fabrication Risk** | High | Critical | Pipeline halts if data cannot be fetched programmatically. |

## Decision Rationale

- **CPU-Only**: Chosen to ensure reproducibility on free-tier CI.
- **Permutation Test of Response Labels**: Ensures fork-point detection is directly linked to therapy response.
- **Functional Alignment**: Addresses context dependency of T-cell trajectories.
