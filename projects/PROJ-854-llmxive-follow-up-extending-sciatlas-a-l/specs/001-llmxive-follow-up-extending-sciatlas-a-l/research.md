# Research: Interdisciplinary Bridging Coefficient Analysis

## Problem Statement & Hypothesis

**Hypothesis**: Nodes in a scientific knowledge graph with a higher "bridging coefficient" (ratio of edges connecting to different structural communities) will exhibit higher future citation counts and higher novelty scores (semantic distance from the nearest *other* topic cluster).

**Rationale**: Interdisciplinary work often bridges disparate communities. If such work is novel and impactful, the topological metric of "bridging" should correlate with outcome metrics of "impact" (citations) and "novelty" (semantic distance to other clusters).

## Dataset Strategy

The study relies on an **OpenAlex-derived Subgraph**. As noted in the project inputs, no verified URL for a direct download of the full "PubGraph" dataset exists.

**Strategy**:
1.  **Primary Source**: The implementation will fetch publication metadata and citation links via the OpenAlex API (`pyalex`).
    *   **Reconstruction Algorithm**: The graph will be constructed by:
        *   **Nodes**: Papers from OpenAlex with titles and citation counts.
        *   **Edges**: Directed citation links (`cites`) between papers. Self-citations and intra-cluster citations (post-clustering) will be filtered out to ensure valid "bridging" potential.
        *   **Attributes**: `title`, `cited_by_count`, `publication_year`.
2.  **Sampling**: To ensure feasibility and preserve local topology, a **snowball sampling** strategy will be used. Starting from a random seed set of nodes, neighbors are recursively added until the target size is reached. This preserves the local neighborhood structure critical for accurate bridging coefficient estimation, unlike degree-stratified random sampling which artificially constrains local edge topology.
3.  **Fallback**: If OpenAlex streaming fails, the pipeline will fall back to a local file if provided in `data/raw/` (checksummed).

**Verified Datasets Reference**:
*   *OpenAlex-derived Subgraph*: Source is the OpenAlex API (public, programmatic). No static URL exists; reconstruction is defined in the plan.
*   *Embeddings Model*: `sentence-transformers/all-MiniLM-L6-v2` (Source: arXiv 2607.07974).

## Methodological Rigor & Statistical Plan

### 1. Predictor: Bridging Coefficient
*   **Definition**: For a node $i$, $BC_i = \frac{E_{inter}}{E_{total}}$, where $E_{inter}$ is the number of edges connecting $i$ to nodes in a *different* structural cluster, and $E_{total}$ is the total degree.
*   **Cluster Definition**: Structural clusters are defined via the **Louvain algorithm** applied to the graph topology. This represents "disciplines" or "communities" based on connectivity.
*   **Edge Cases**: Nodes with degree 0 are assigned $BC = 0.0$ (or excluded if they cannot contribute to edge analysis).
*   **Validity**: This metric is purely topological and independent of text content.

### 2. Outcome: Novelty Score
*   **Definition**: The **minimum cosine distance** between a node's title embedding and the centroid of any **other** text-based topic cluster (excluding its assigned cluster).
*   **Rationale**: This metric distinguishes "bridging" (being far from the nearest *other* cluster) from simple "outlier-ness" (being far from the assigned centroid). A node that is simply "weird" within its own cluster will have a high distance to its assigned centroid but might be close to another cluster. The "distance to nearest other" metric specifically captures the potential to bridge.
*   **Cluster Definition**: Text clusters are defined via **K-Means** on title embeddings (using `all-MiniLM-L6-v2`).
*   **Independence**: This ensures the outcome is derived *only* from text, preventing circular validation with the topological predictor. The metric is not a tautology of the clustering loss because it measures distance to a *different* cluster, not the assigned one.
*   **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2`. This model is small enough for CPU inference (~80MB) and fast (<50ms/node).

### 3. Outcome: Citation Impact
*   **Metric**: Raw citation count from metadata.
*   **Handling**: Log-transformed (`log1p`) for regression to handle heavy-tailed distribution.

### 4. Statistical Analysis
*   **Correlation**: Spearman rank correlation ($\rho$) between $BC$ and (Citations, Novelty).
*   **Regression**: Linear regression (Citations ~ BC, Novelty ~ BC) **with covariates**: `publication_year` (to control for age bias) and `cluster_size` (to control for the "rich-get-richer" effect in large communities). Robust standard errors will be used.
*   **Multiplicity Correction**: **Benjamini-Hochberg (FDR)** correction applied to all p-values to control the false discovery rate, as multiple hypotheses (Citations vs BC, Novelty vs BC) are tested.
*   **Causal Framing**: All results will be explicitly labeled as **associational**. No causal claims will be made due to the observational nature of the data (lack of randomization).

## Edge Filtering Logic
To ensure valid "bridging" definition:
*   **Self-Citations**: Removed (a paper cannot bridge to itself).
*   **Intra-Cluster Citations**: Filtered out *after* Louvain clustering to ensure only edges crossing cluster boundaries contribute to the "inter-cluster" count.

## Feasibility Check
*   **Size Estimation**: The reconstructed OpenAlex subgraph is expected to be of substantial size if fully streamed. Snowball sampling will limit the active graph to [deferred] nodes.
*   **Streaming**: `pyalex` with `chunk_size=1000` and `streaming=True` will be used to avoid OOM.
*   **Memory**: Peak memory will be monitored; if >7GB, the sample size will be reduced.

## Compute Feasibility (CPU-First)

*   **Ingestion**: Streaming via `pyalex` or `datasets` with `streaming=True`. No full graph load.
*   **Graph Processing**: `networkx` on the sampled subgraph. With [deferred] nodes, memory usage is projected < 2GB.
*   **Embeddings**: Batched inference (batch size ~32-64) using CPU. Estimated time: [deferred] nodes * 50ms = [deferred] hours. Fits within 6h limit if sample size is < 40,000 nodes.
*   **Clustering**: Louvain (fast) and K-Means (scales linearly with nodes). CPU-tractable.
*   **GPU Escape Hatch**: Not required. The `all-MiniLM-L6-v2` model runs efficiently on CPU. If the sample size exceeds limits, the sampling strategy will be adjusted, not the hardware.

## Decision Rationale

| Decision | Rationale |
|----------|-----------|
| **Snowball Sampling** | Preserves local neighborhood topology, avoiding selection bias in bridging coefficient. |
| **Distance to Nearest Other Cluster** | Distinguishes "bridging" from "outlier-ness", avoiding tautology. |
| **Covariates in Regression** | Controls for age and cluster size confounds to prevent spurious correlations. |
| **Benjamini-Hochberg** | Preferred over Bonferroni for power in exploratory research with multiple correlated tests. |
| **CPU-Only** | The chosen models and sample size fit within the 6h/7GB constraint. No GPU needed. |