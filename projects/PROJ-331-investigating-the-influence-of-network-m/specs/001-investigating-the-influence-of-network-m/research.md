# Research: Investigating the Influence of Network Motifs on Resting‑State Functional Connectivity

## Scientific Context

The human brain's structural connectome (SC) is organized by specific local wiring patterns known as **network motifs** (small, over-represented subgraphs). The central hypothesis is that these local structural constraints shape global functional connectivity (rsFC). This project tests whether the prevalence of specific 3-node motifs in SC predicts individual variation in rsFC strength and global efficiency, controlling for overall network density.

## Methodology

1. **Data Source**: Human Connectome Project (HCP) S1200 Release.
2. **Parcellation**: Schaefer atlas to define nodes.
3. **Structural Metrics**:
 * **Weighted**: Streamline count adjacency matrix (unthresholded) used for Global Efficiency.
 * **Binary**: Density-thresholded adjacency matrices (varying thresholds) used for motif counting. Final predictor is the median z-score across thresholds.
4. **Functional Metrics**: Pearson correlation matrices of BOLD time-series.
5. **Motif Analysis**: Enumeration of all 3-node subgraphs; Z-score calculation against degree-preserving random graphs (Maslov-Sneppen edge switching, multiple iterations). Aggregation of z-scores across thresholds via median.
6. **Statistical Model**: Partial Pearson/Spearman correlation between motif Z-scores and rsFC metrics, controlling for **network density**. FDR (Benjamini-Hochberg) correction for multiple testing. Permutation testing for validation.

## Verified Datasets

The following datasets have been verified for availability and format compatibility:

| Dataset Name | Description | Verified URL / Loader | Notes |
|:--- |:--- |:--- |:--- |
| **HCP S1200 Release** | Structural (DWI) and Resting-State fMRI data for a large cohort of subjects. | ` (Requires free account) | **Primary Source**. Must download DWI and rs-fMRI for same subjects. Access requires registration. **CI Note**: The CI pipeline assumes data is pre-seeded in `data/raw/` via a volume mount or secret, as interactive login is not supported. Raw NIFTI/streamline files are expected. |
| **Schaefer Atlas** | A multi-node cortical parcellation (MNI space). | ` | Must be downloaded and registered to HCP MNI space. |

*Note: The HCP dataset requires a free account and data use agreement. The pipeline will assume the user has provided credentials or the data is pre-downloaded to `data/raw/` as per CI constraints. If direct API access is blocked, the plan assumes local ingestion of the provided subject IDs.*

## Dataset Strategy

| Component | Source | Loader/Method | Variable Fit Verification |
|:--- |:--- |:--- |:--- |
| **Structural Connectome (Weighted)** | HCP S1200 (Diffusion) | `nibabel` + `dipy` (streamline counting) | **Verified**: HCP provides pre-processed tractography. We will count streamlines to create a weighted matrix. |
| **Structural Connectome (Binary)** | Derived from Weighted | Density thresholding (10%, 20%, 30%) | **Verified**: Thresholding applied uniformly to ensure comparability. Median aggregation used for final score. |
| **Functional Connectome** | HCP S1200 (rs-fMRI) | `nibabel` + Time-series extraction | **Verified**: HCP provides minimally pre-processed rs-fMRI. Time-series extraction via Schaefer-100 masks is standard. |
| **Atlas** | Schaefer 2018 | `numpy` loading of label files | **Verified**: 100-node resolution matches project scope. |

**Critical Mismatch Check**:
* *Requirement*: Post-task anxiety/rumination? -> *No*. The study focuses on **resting-state** connectivity and **structural** motifs. No behavioral covariates (anxiety) are required by the spec.
* *Requirement*: 3-node motifs? -> *Yes*. HCP data (100 nodes) supports 3-node enumeration.
* *Requirement*: Global efficiency? -> *Yes*. Derivable from adjacency matrix (calculated on weighted graph).

## Statistical Plan Details

* **Multiple Comparisons**: Benjamini-Hochberg (FDR) correction applied to the set of directed 3-node motifs to account for correlation structure. Bonferroni is avoided as it is overly conservative for correlated tests.
* **Power Analysis**: N=50, α=0.05 (FDR-adjusted). Expected detectable r of moderate magnitude (two-tailed test assumed for conservatism). The report will explicitly state this conservative estimate and the risk of Type II errors.
* **Null Model**: A sufficient number of edge switching iterations (Maslov-Sneppen) to preserve degree distribution. Reduced from 1000 to ensure CI feasibility.
* **Permutation Test**: A sufficient number of shuffles of subject labels to generate empirical p-values.
* **Assumptions**: Linearity (for Pearson), monotonicity (for Spearman), independence of subjects.
* **Circularity Avoidance**: Global Efficiency calculated on **weighted** (unthresholded) graph; Motifs on **binary** (thresholded) graph. Control variable is **network density**.
* **Collinearity**: VIF check performed. If VIF > 5, report collinearity and adjust method.

## Risks & Mitigations

* **Risk**: HCP data access blocked in CI.
 * *Mitigation*: Pipeline designed to skip if data missing (US-1). CI runs on a subset or uses a mock dataset for testing logic. Data must be pre-seeded.
* **Risk**: Motif counting > 300s.
 * *Mitigation*: Strictly limit to 3-node motifs and 100 null iterations. Use optimized `networkx`. Timeout wrapper added.
* **Risk**: Low variance in motif z-scores.
 * *Mitigation*: Detect zero-variance vectors; skip correlation; flag in report.
* **Risk**: Null model convergence failure.
 * *Mitigation*: Retry up to 5 times. If failed, set z-score to `null` for that motif (exclude from analysis) rather than assigning 0.