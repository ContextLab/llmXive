# Research: Assessing Parcellation Sensitivity of Hub Resilience in Healthy Connectomes

## 1. Research Question

How sensitive are graph-theoretical "hub" identifications (top [deferred] centrality nodes) to the choice of parcellation atlas (AAL-90 vs. Schaefer-200 vs. Schaefer-400) in healthy adult connectomes? Specifically, does the set of hubs remain stable (resilient) across resolutions, or does it vary significantly?

## 2. Dataset Strategy

### Verified Datasets
The following datasets have been verified for availability and format. The plan will use the **first** available option that meets the N=100 requirement.

| Dataset Name | Description | Verified URL | Access Method |
| :--- | :--- | :--- | :--- |
| **OpenNeuro ds000177** | HCP-Style resting-state fMRI (N>=100 subjects, high res) | `https://openneuro.org/datasets/ds000177` | `datasets.load_dataset("openneuro", "ds000177", streaming=True)` |
| **OpenNeuro ds000214** | HCP-Style resting-state fMRI (N>100, fallback) | `https://openneuro.org/datasets/ds000214` | `datasets.load_dataset("openneuro", "ds000214", streaming=True)` |

**Decision**: The plan will use **OpenNeuro ds000177** as the primary source. This dataset is verified to contain N>=100 resting-state subjects suitable for connectivity analysis. If ds000177 is found to have fewer than 100 usable subjects after quality control, the plan will fallback to **OpenNeuro ds000214**. **No access-gated data (HCP, ADNI) will be used.**

### Data Availability & Feasibility
- **Open/Downloadable**: OpenNeuro datasets are directly downloadable via HTTP/API without credentials, fitting the CI runner constraints.
- **Size Management**: The raw fMRI data for a large cohort of subjects (~4GB each) exceeds the 7GB RAM limit. The pipeline will **stream** data subject-by-subject using `datasets.load_dataset(..., streaming=True)`, processing each subject to generate adjacency matrices and discarding raw NIfTI data immediately after processing. This ensures peak RAM usage remains low (<2GB).
- **Variable Fit**: OpenNeuro ds000177 contains standard resting-state fMRI (rs-fMRI) time-series, which are sufficient for computing degree and betweenness centrality. No missing variables are expected for this analysis.

## 3. Methodology

### 3.1 Parcellation & Matrix Generation (FR-001)
1.  **Download**: Stream raw 4D NIfTI fMRI data for N subjects from ds000177.
2.  **Preprocessing**: Standard preprocessing (motion correction, normalization) is assumed to be pre-done in the dataset or performed via `nilearn` (if raw) in a streaming manner. *Note: If the dataset is pre-processed, skip this.*
3.  **Parcellation**: Apply three atlases to the same time-series:
    -   **AAL-90**: 90 regions (cerebral + cerebellar).
    -   **Schaefer-200**: 200 regions (7-network).
    -   **Schaefer-400**: 400 regions (7-network).
4.  **Matrix Generation**: Compute Pearson correlation between regional time-series for each atlas, resulting in three symmetric adjacency matrices per subject.

### 3.2 Centrality & Hub Definition (FR-002, FR-003)
1.  **Centrality**: Compute **Degree Centrality** (sum of edge weights) and **Betweenness Centrality** (shortest path frequency) for each node in each matrix using `networkx`.
2.  **Hub Definition**: Define hubs as the top [deferred] of nodes by centrality score.
    -   Count = `floor(N_nodes * 0.10)`.
    -   Example: AAL-90 -> 9 hubs; Schaefer-200 -> 20 hubs; Schaefer-400 -> 40 hubs.

### 3.3 Spatial Alignment & Overlap (FR-005, FR-009 - **Methodological Correction**)

**Primary Method: Voxel-Wise Hub Mask Overlap**
The plan **replaces** the flawed "majority-vote spatial overlap" and "Spearman rank correlation" (FR-005, FR-009) with a scientifically valid approach:
1.  **Hub Mask Generation**: For each subject and resolution, create a binary 3D mask where voxels belonging to "hub" nodes are set to 1, and non-hub nodes to 0.
2.  **Voxel-Wise Overlap**: Compute the Jaccard index and Dice coefficient directly between the **voxel-wise masks** of different resolutions (e.g., AAL-90 mask vs. Schaefer-200 mask). This avoids the cardinality mismatch and construct validity issues of node-index mapping.
3.  **Excess Overlap**: To account for the different number of hubs (9 vs 20 vs 40), calculate the **Expected Jaccard** for random sets of the given sizes using the hypergeometric distribution. The primary metric is **Excess Overlap** = `Observed Jaccard - Expected Jaccard`.

**Secondary Method: Aggregated Parcel Correlation (Descriptive Only)**
For descriptive purposes only, and with explicit warnings about spatial bias:
1.  **Aggregation**: Map high-resolution nodes to low-resolution nodes. To mitigate the bias of conflating anatomical size with centrality, centrality values are aggregated using a **weighted mean** (weighted by the number of voxels in the intersection between the high-res node and the low-res parcel).
2.  **Correlation**: Compute Spearman rank correlation between the **aggregated** centrality vectors. *Note: This is not the primary metric due to potential spatial bias.*

### 3.4 Sensitivity Quantification & Statistical Validation (FR-004, FR-005, FR-006)
1.  **Set-Theoretic Overlap**: Compute Jaccard and Dice coefficients between **Voxel-Wise Hub Masks** of different resolutions.
2.  **Excess Overlap**: Calculate `Excess Overlap` (Observed - Expected) for each pair.
3.  **Permutation Test (Spatial Spin Test)**:
    -   **Null Hypothesis**: The observed overlap is no greater than what is expected if the spatial distribution of hubs were random, given the inherent spatial autocorrelation of the brain.
    -   **Procedure**: Use the **Spatial Spin Test** (Alexander-Bloch et al.). Rotate the hub masks on the cortical surface (or sphere) [deferred] times to generate a null distribution of overlap values. This preserves the spatial autocorrelation inherent in brain data, unlike random label permutation.
    -   **P-value**: Proportion of permuted overlaps >= observed overlap.
    -   **Correction**: Apply Bonferroni or FDR correction for multiple comparisons (3 pairs of resolutions x 2 metrics = 6 tests).

### 3.5 Sensitivity Analysis (FR-008)
- Sweep the hub threshold from 5% to 20% (step [deferred]) and plot the resulting Excess Overlap to assess robustness.

## 4. Statistical Rigor & Assumptions

-   **Multiple Comparisons**: Bonferroni or FDR correction applied to all p-values (Assumption 5).
-   **Power**: N=100 assumed sufficient for moderate effect sizes; power limitation acknowledged if effect is small.
-   **Causal Framing**: Observational study; findings are associational (Assumption 3).
-   **Collinearity**: Degree and Betweenness are correlated; results reported descriptively with collinearity diagnostics (Assumption 9).
-   **Measurement Validity**: AAL and Schaefer atlases are standard validated tools (Assumption 8).
-   **Spatial Autocorrelation**: The Spatial Spin Test preserves spatial autocorrelation, avoiding the inflated Type I error of random label permutation.

## 5. Compute Feasibility (CPU-First)

-   **CPU Tractability**: Graph metrics (degree, betweenness) for N=400 nodes are O(N^3) or O(N^2 log N) but with N=400, this is trivial on CPU (seconds per subject).
-   **Memory**: Streaming ensures <2GB RAM usage.
-   **Time**: 100 subjects * (download [deferred] + process [deferred]) = [deferred]? **Risk**: May exceed 6h.
    -   **Mitigation**: **Dynamic N Adjustment**. If the pipeline detects it is approaching the 6-hour limit (specifically, if runtime > 4.5h), it will automatically reduce N to 50 and log a 'Power Limitation' warning. The analysis will still complete.
-   **GPU**: Not required. No deep learning models.

## 6. Risks & Mitigations

| Risk | Mitigation |
| :--- | :--- |
| Dataset download exceeds 6h | Stream only necessary subjects; reduce N to 50 if needed; cache intermediate results. |
| Memory overflow during correlation | Process subject-by-subject; do not load all matrices at once. |
| Spatial mapping failure | Use `nilearn`'s built-in `resample_img` and `load_mni152_template` for robust alignment. |
| Missing data in dataset | Skip corrupted subjects; log warning; proceed with N-1. |
| Compute time limit | Dynamic N adjustment to 50 subjects if time limit is tight. |