# Research: The Impact of Network Centrality on Neural Synchrony in Resting-State fMRI

## 1. Scientific Background

### 1.1 The Structure-Function Relationship
The human brain's functional connectivity (synchrony between regions) is largely constrained by its underlying structural connectivity (white matter tracts). However, the relationship is not 1:1; functional dynamics can persist without direct structural links due to polysynaptic pathways or shared inputs. This project tests the hypothesis that **node-level structural centrality** (how "central" a region is in the structural network) predicts **functional synchrony** (how strongly a region correlates with the rest of the network).

### 1.2 Network Metrics
- **Degree Centrality**: The number of direct structural connections. High degree implies high local integration.
- **Betweenness Centrality**: The fraction of shortest paths passing through a node. High betweenness implies a "hub" role in global communication.
- **Eigenvector Centrality**: A measure of a node's influence based on the influence of its neighbors.
- **Functional Synchrony**: Defined here as the mean absolute correlation of a node's time series with all other nodes.

### 1.3 Hypothesis
Regions with higher structural centrality (degree, betweenness, eigenvector) will exhibit higher functional synchrony. Given the observational nature of the data, findings will be framed as **associational**.

## 2. Dataset Strategy

### 2.1 Primary Dataset: OpenNeuro ds000224
The study relies on the **OpenNeuro ds000224** dataset (HCP Young Adult).
- **Source**: OpenNeuro (via Hugging Face mirror for CI compatibility).
- **Variables**:
  - Pre-computed Structural Connectivity (SC) matrices.
  - Pre-computed Functional Connectivity (FC) matrices.
  - Metadata: Motion parameters, acquisition details.
- **Feasibility Check**: The verified source (Parquet shard) contains pre-computed matrices but **not** raw dMRI/fMRI NIfTI files. Therefore, the **tractography pipeline is impossible** as described in the spec's original FR-002. The plan adapts to use **Pre-computed Mode** exclusively.
- **Access**: The dataset is open-access. The plan uses the Hugging Face `datasets` library to fetch the specific subset.

> **Verified datasets**:
> - OpenNeuro (parquet): https://huggingface.co/datasets/clane9/openneuro-fslr64k/resolve/main/data/test-00000-of-00016.parquet
> - **Note**: The verified URL is a Parquet shard. It likely contains pre-computed matrices or metadata. If it lacks the required SC/FC matrices, the pipeline halts with "Data Gap". No raw dMRI is available from this source.

### 2.2 Atlas
- **Schaefer 400 Atlas**: A parcellation of the cortex into 400 regions based on functional gradients. Used to reduce dimensionality from voxel-level to node-level.

## 3. Methodology

### 3.1 Data Ingestion (FR-001)
1.  **Download**: Fetch pre-computed SC and FC matrices for up to 10 subjects from the verified source.
2.  **Quality Control**: Exclude subjects with missing matrices or motion parameters > 0.5mm. Log exclusions.
3.  **Checksum**: Record SHA256 checksums of downloaded files in `state/...yaml` before processing.

### 3.2 Metric Computation (FR-003)
- **Centrality**: Compute Degree, Betweenness, and Eigenvector centrality for each node in the Structural Matrix using `networkx`.
- **Synchrony**: Compute the mean absolute correlation for each node in the Functional Matrix.

### 3.3 Statistical Analysis (FR-004, FR-005, FR-007)
- **Primary Test**: Spearman correlation between each Centrality metric and Synchrony **across subjects** (N=10).
- **Multiple Comparisons**: **Subject-Level Permutation Test (n=1000)** OR **Spatial Null Model**.
  - **Preferred**: Use `brainsmash` to generate a spatially constrained null distribution (spin tests) to preserve spatial autocorrelation.
  - **Fallback**: If `brainsmash` is unavailable, use subject-level permutation (shuffling subject IDs) but explicitly note the risk of inflated Type I error due to node non-independence.
  - **Note**: With N=10, the null distribution is discrete and coarse.
- **Sensitivity Analysis**: Sweep structural graph threshold density (e.g., 5%, 10%, [deferred], [deferred]) and report stability of the correlation coefficient (Stability Index + AUC) across these thresholds.
- **Collinearity Check**: Report Variance Inflation Factor (VIF) for the three centrality metrics.

### 3.4 Visualization (FR-006)
- Scatter plot: X-axis = Centrality, Y-axis = Synchrony.
- Overlay regression line, 95% CI, and p-value annotation.

## 4. Compute Feasibility & Data Availability

### 4.1 CPU-First Strategy
- **Tractography**: **SKIPPED**. The verified source lacks raw dMRI. The plan uses pre-computed matrices directly.
- **Memory**: All matrix operations are performed on 400x400 matrices (negligible memory).
- **Time**: 10 subjects × (Metrics + Analysis) is estimated at < 6 hours on a 2-core CPU.

### 4.2 Data Availability Constraint
- **Gap**: The verified dataset URL provided is a Parquet file. It does not contain raw NIfTI files required for the full tractography pipeline.
- **Fallback**: The plan commits to **Pre-computed Mode**. If the Parquet lacks pre-computed SC/FC matrices, the pipeline halts with a "Data Gap" error. No raw data processing is attempted.

## 5. Decision Rationale

| Decision | Rationale |
|----------|-----------|
| **n=10 Subjects** | Fits within 14 GB storage limit; sufficient for permutation test power (rho > 0.3) *if* raw data is available (but it is not). |
| **Subject-Level Permutation (n=1000)** | Non-parametric correction for multiple comparisons in network data; robust to non-Gaussian distributions. Corrects for node non-independence (with caveats). |
| **Spatial Null Model** | Preferred method to preserve spatial autocorrelation in the null distribution. |
| **Spearman Correlation** | Robust to outliers in centrality metrics; appropriate for rank-based relationships. |
| **CPU-Only** | No GPU required for matrix operations or permutation tests; avoids complexity of CUDA offloading. |
| **Pre-computed Mode** | Required because the verified source lacks raw dMRI. Tractography is impossible. |

## 6. Data Gap Protocol

If the verified dataset URL (Parquet) lacks pre-computed SC/FC matrices:
1.  **Attempt to load** the Parquet.
2.  **If Parquet contains pre-computed SC/FC matrices**: Proceed with analysis.
3.  **If Parquet lacks required data**: Halt with a "Data Gap" error. Do not fabricate data or invent a new URL.
4.  **Log**: The error is logged in `data/results/processing_summary.json` with reason "Data Gap: Pre-computed matrices missing".