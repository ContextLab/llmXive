# Research: Assessing Parcellation Sensitivity of Hub Resilience in Healthy Connectomes

## 1. Dataset Strategy

### Verified Datasets
The project relies on the **OpenNeuro ds000224** (1000 Functional Connectomes Project) as the primary source for raw fMRI time-series data.

*   **Source**: OpenNeuro ds000224 (1000 Functional Connectomes Project)
*   **URL**: `https://openneuro.org/datasets/ds000224`
*   **Format**: NIfTI (`.nii.gz`) for functional volumes; Parcellation atlases (AAL, Schaefer) are standard MNI-space NIfTI templates available via `nilearn` or `neurovault`.
*   **Fit Verification**:
    *   **Requirement**: Raw fMRI time-series for healthy adults (N≥100).
    *   **Availability**: OpenNeuro provides high-quality, resting-state fMRI data for a large cohort of subjects.
    *   **Variables**: Contains full-brain BOLD signal required to compute connectivity matrices.
    *   **Constraint Check**: The dataset is large. The plan will implement a **downsampling strategy** (selecting the first 100 subjects) and **memory-efficient loading** (loading time-series in chunks or using `nilearn`'s memory mapping) to ensure the 7 GB RAM limit is not exceeded.
    *   **Atlas Compatibility**: The dataset may contain data in native space. The plan includes an explicit **Registration to MNI Space** step to ensure compatibility with standard AAL and Schaefer atlases (which are in MNI space).

### Data Acquisition & Preprocessing Plan
1.  **Fetch**: Use `nilearn.datasets.fetch_openneuro` to retrieve the first 100 subjects from ds000224.
2.  **Registration to MNI Space**:
    *   Check the header of the fetched NIfTI files.
    *   If the data is not in MNI space, apply a linear registration to the MNI152 template using `nilearn.image.resample_img` or `nibabel`'s resampling utilities.
    *   *Rationale*: AAL and Schaefer atlases are defined in MNI space. Direct application requires the functional data to be in the same space.
3.  **Preprocessing**: Apply standard preprocessing (motion correction, nuisance regression, bandpass filtering) using `nilearn.signal.clean`. *Note: If the dataset is already preprocessed (e.g., HCP minimal), skip heavy steps to save compute time.*
4.  **Parcellation**:
    *   **AAL-90**: Load standard AAL template (via `nilearn.datasets.fetch_atlas_aal`).
    *   **Schaefer-200/400**: Load Schaefer 2018 templates (via `nilearn.datasets.fetch_atlas_schaefer_2018`).
    *   **Extraction**: Extract mean time-series for each parcel using `nilearn.input_data.NiftiLabelsMasker`.
5.  **Matrix Generation**: Compute Pearson correlation matrix for each subject/resolution. Apply Fisher's r-to-z transform if necessary for downstream stats (though correlation is the primary metric here).

## 2. Methodological Rationale & Statistical Rigor

### Centrality & Hub Definition (FR-002, FR-003)
*   **Metric Selection**: Degree centrality (sum of edge weights) and Betweenness centrality (shortest path count) are chosen as they are the most common definitions of "hubs" in connectomics.
*   **Thresholding**: Hubs are defined as the top `floor(N * 0.10)` nodes.
    *   **Rationale**: This aligns with the "rich club" literature where the top 10-15% are often considered hubs.
    *   **Collinearity Note**: Degree and Betweenness are often highly correlated. The plan will report the correlation between these two metrics within each resolution to acknowledge this dependency, avoiding claims of independent predictive power.
*   **Handling N=90**: `floor(90 * 0.10) = 9` hubs.
*   **Handling N=200**: `floor(200 * 0.10) = 20` hubs.
*   **Handling N=400**: `floor(400 * 0.10) = 40` hubs.

### Spatial Alignment (FR-005, FR-009)
*   **Challenge**: Comparing node ranks across resolutions (e.g., AAL-90 vs Schaefer-400) requires mapping nodes to a common space.
*   **Method**: **Majority-Vote Spatial Overlap**.
    *   For each node in the high-resolution atlas (e.g., Schaefer-400), calculate the proportion of its voxels that fall within each node of the low-resolution atlas (e.g., AAL-90).
    *   Assign the high-res node to the low-res node with the maximum overlap.
    *   This creates a mapping function `f: Node_High -> Node_Low`.
*   **Validity**: This is a standard approach in multi-resolution connectomics when exact anatomical correspondence is not 1:1.

### Statistical Validation (FR-004, FR-006)
*   **Overlap Metrics**: Jaccard Index ($J = |A \cap B| / |A \cup B|$) and Dice Coefficient ($D = 2|A \cap B| / (|A| + |B|)$).
*   **Cardinality Normalization (Critical Fix)**:
    *   **Problem**: Comparing sets of size 9 (AAL) and 40 (Schaefer) directly via raw Jaccard is biased; the expected overlap for random sets of these sizes is non-zero and high due to the small universe of nodes in AAL.
    *   **Solution**: Calculate the **Expected Jaccard Index** ($J_{exp}$) for two random sets of sizes $|A|$ and $|B|$ drawn from a universe of size $N_{universe}$ (the size of the lower-resolution atlas, e.g., 90).
    *   **Primary Metric**: **Excess Overlap** ($J_{excess} = J_{obs} - J_{exp}$). This metric isolates the true signal from the statistical artifact of set size disparity.
    *   **Fixed-Cardinality Analysis**: As part of the sensitivity analysis (FR-008), we will also compare the top $K$ hubs across all resolutions where $K$ is fixed (e.g., $K=9$) to ensure that observed differences are due to resolution, not set size.
*   **Correlation**: Spearman rank correlation ($\rho$) between centrality scores of mapped nodes.
    *   **Method**: For each low-resolution node, aggregate the ranks of all high-resolution nodes that map to it (mean rank). Compute Spearman correlation between the low-resolution ranks and these aggregated high-resolution ranks.
    *   **Interpretation**: This correlation is interpreted as a "Spatial Consistency Metric" and is not claimed to prove independent hub stability, as the values are derived from the same underlying BOLD signal. High correlation is expected due to shared spatial origin.
*   **Permutation Test (Spatial Spin Test)**:
    *   **Null Hypothesis**: The observed hub overlap is no different than random chance, given the spatial structure of the brain.
    *   **Procedure**:
        1.  **Rotate**: Apply a random 3D rotation (spin) to the coordinates of the high-resolution atlas (e.g., Schaefer-400) in MNI space.
        2.  **Re-Map**: Re-compute the majority-vote mapping between the *rotated* high-res atlas and the low-res atlas.
        3.  **Re-Calculate**: Re-compute hub sets and overlap metrics for the rotated mapping.
        4.  **Repeat**: Perform a sufficient number of iterations to ensure convergence and statistical robustness.
        5.  **P-value**: Calculate p-value: $(count(overlap_{perm} \ge overlap_{obs}) + 1) / (1000 + 1)$.
    *   **Multiple Comparisons**: Since we compare 3 pairs of resolutions (AAL-Sch200, AAL-Sch400, Sch200-Sch400) and potentially 2 metrics (Degree, Betweenness), a **Bonferroni correction** (alpha = 0.05 / 6 ≈ 0.0083) will be applied to the final p-values.
*   **Power Limitation**: With N=100 subjects, the power to detect small effect sizes in the *variance* of hub stability is limited. The study will explicitly state this as a limitation if results are non-significant but the effect size is moderate.

### Computational Feasibility
*   **CPU Constraint**: `networkx` centrality algorithms are $O(N^3)$ for betweenness. For N=400, this is trivial ($400^3 = 64,000,000$ ops). For N=100 subjects, total ops are well within 6 hours on a 2-core CPU.
*   **Memory Constraint**: Storing 100 subjects $\times$ 3 resolutions $\times$ 400 nodes $\times$ 8 bytes (float64) $\approx$ 96 MB for matrices. Time-series data is the main consumer; loading one subject at a time and processing sequentially prevents RAM overflow.

## 3. Assumptions & Risks

*   **Assumption**: The downloaded data can be registered to MNI space with acceptable accuracy. *Mitigation*: Use standard `nilearn` registration tools; verify registration quality by visual inspection of a subset of subjects.
*   **Risk**: 6-hour timeout on GitHub Actions. *Mitigation*: Implement a "progress bar" and a `max_iterations` flag for the spin test. If time is running low, reduce iterations to a lower count and log a warning.
*   **Risk**: Data corruption. *Mitigation*: Implement checksum verification for downloaded files; skip corrupted subjects and log warnings.