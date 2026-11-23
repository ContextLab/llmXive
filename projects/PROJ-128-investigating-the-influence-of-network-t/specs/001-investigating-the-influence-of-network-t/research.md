# Research: Investigating the Influence of Network Topology on Spontaneous Brain Activity Patterns

## Research Question

Do topological properties of structural brain networks derived from diffusion MRI predict the prevalence, stability, and switching speed of recurrent activity patterns in resting-state fMRI?

**Clarification on Causality**: As per the project constitution and FR-007, the term "predict" is used in a statistical sense (associational). The study is observational; no causal claims are made. The structural network is treated as an independent predictor variable, and dynamic functional metrics as the outcome, but the relationship is strictly correlational.

## Dataset Strategy

We utilize the **HCP (Human Connectome Project)** derivatives, specifically the **OpenNeuro ds000224** dataset, which provides preprocessed dMRI and fMRI data in BIDS format.

| Dataset Name | Source URL | Access Type | Variables Available | Notes |
|--------------|------------|-------------|---------------------|-------|
| OpenNeuro ds000224 | `https://openneuro.org/datasets/ds000224` | Open (Direct Download via BIDS) | Structural matrices, fMRI time series, metadata | Verified source. Official HCP preprocessed data. Contains the necessary dMRI and fMRI data for graph construction. |

**Dataset Selection Rationale**:
- **Open Availability**: The dataset is directly downloadable via the `datasets` library or `bids` tools, satisfying the CI runner constraints (no credentials, no gate).
- **Variable Fit**: The verified source contains structural connectivity matrices (dMRI) and fMRI time series, which are the exact inputs required for FR-001 (structural metrics) and FR-002 (dynamic states).
- **No Fabrication**: We do not use synthetic data or unverified URLs. The plan relies exclusively on the official OpenNeuro ds000224 source.

**Data Loading Strategy**:
- Use `datasets.load_dataset` or `bids` tools to fetch the dataset.
- Stream data where possible to avoid loading the entire dataset into RAM at once.
- **Missing Data Handling**: If a subject lacks either dMRI or fMRI data, they are excluded from the analysis, and the exclusion is logged (SC-005).

## Statistical Methodology

### 1. Structural Graph Construction
- **Input**: dMRI connectivity matrices.
- **Thresholding**: Proportional density (baseline [deferred] density). Sensitivity analysis performed at ±5% (FR-008).
- **Metrics**: Global Efficiency, Average Clustering Coefficient, Modularity (FR-001).
- **Tool**: `networkx`.

### 2. Dynamic Functional State Extraction (LOSO)
- **Input**: fMRI time series.
- **Method**: Sliding-window correlation (baseline window, 20 TR sensitivity).
- **Clustering**: **Leave-One-Subject-Out (LOSO)** k-means (k=5). For each subject, the state space is defined by clustering the data of all *other* subjects. This ensures the subject's own data does not define their states, preventing circular correlation (Constitution Principle VI).
- **Stability Check**: Silhouette Score and Consensus Clustering with multiple seeds to validate state stability.
- **Metrics**: Mean Dwell Time, Number of Visited States (FR-003).
- **Tool**: `scikit-learn`, `numpy`.

### 3. Correlation Analysis
- **Dimensionality Reduction**: PCA applied to dynamic metrics to reduce multiple comparisons (a few tests instead of 15).
- **Normality Test**: Shapiro-Wilk (α=0.05).
- **Correlation Method**: Pearson (if normal) or Spearman (if non-normal) (FR-004).
- **Multiple Comparisons**: Benjamini-Hochberg FDR correction (q=0.05) (FR-005).
- **Output**: Correlation coefficients (r), p-values, FDR-corrected p-values.

### 4. Robustness Checks
- **Window Length**: Compare 30 TR vs. 20 TR (FR-006).
- **Threshold Density**: Compare baseline vs. ±5% variation (FR-008). Note: Dynamic metrics are NOT re-computed for density sensitivity.
- **Framing**: Explicit "associational" label in all reports (FR-007).
- **Robustness Metric**: The absolute difference in correlation coefficients (`|r_baseline - r_sensitivity|`) is calculated. A difference < 0.05 is considered robust.

## Power & Sample Size Considerations

- **Sample Size**: The plan targets a cohort of a substantial number of subjects (as per spec assumptions).
- **Power Limitation**: With N=50, the study may have limited power to detect small effect sizes after FDR correction. The PCA dimensionality reduction step mitigates this by reducing the number of tests. The report will explicitly state this limitation if no significant findings survive correction.
- **Effect Size**: The study is framed as exploratory if power is insufficient for definitive hypothesis testing.

## Potential Confounds & Mitigations

- **Circular Correlation**: Mitigated by strict LOSO clustering strategy (Constitution Principle VI).
- **Motion Artifacts**: Assumed to be pre-processed in the HCP derivatives. If residual motion correlates with graph metrics, it may confound results. The report will acknowledge this.
- **Threshold Sensitivity**: Addressed by the density sensitivity analysis (FR-008).