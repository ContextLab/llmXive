# Research: Investigating the Relationship Between Brain Network Topology and Susceptibility to Visual Illusions

## 1. Dataset Strategy

The study requires a dataset containing both resting-state fMRI (using HCP protocols) and visual illusion susceptibility scores for the *same* subjects.

### Strategy
1.  **Primary Data Source**: We will use the **OpenNeuro ds004285** dataset. This dataset contains resting-state fMRI data and behavioral data from subjects performing visual illusion tasks (including Müller-Lyer and Ponzo variants).
    *   *Verification*: This dataset has a verified URL and contains the necessary variables for both the predictor (fMRI) and outcome (illusion scores).
    *   *Verified Source Reference*: `https://openneuro.org/datasets/ds004285`
    *   *Access Method*: `openneuro-py` library to download the specific subject subsets.

2.  **Behavioral Data**: The illusion scores are extracted directly from the `task-illusion` behavioral files within the OpenNeuro dataset. No custom recruitment or new data collection is required for the primary analysis, as the data is already collected and linked to the fMRI scans.
    *   *Action*: The `export_scores.py` script will parse the behavioral TSV/JSON files to extract the Müller-Lyer and Ponzo susceptibility scores, linking them to the subject ID.
    *   *Note on US-4/FR-008*: The requirement to implement a "custom online psychophysical task" (US-4/FR-008) is reframed as a **validation component**. The task logic will be implemented to ensure the extraction logic matches the original task design, but the *collection* of data for this study is not performed via a new tool; it is extracted from the existing dataset.

### Dataset Variable Fit
*   **Predictor**: Functional Connectivity (200x200 matrix) derived from rs-fMRI.
*   **Outcome**: Illusion Susceptibility Score (continuous).
*   **Fit Check**: The OpenNeuro dataset provides both modalities for the same subjects. The correlation analysis will only run on subjects where both data types exist (which is the design of the dataset). If a subject has fMRI but no valid behavioral score (e.g., incomplete task), they are excluded from the correlation analysis but retained in logs (per Edge Case: Missing Behavioral Data).

## 2. Methodology & Statistical Rigor

### A. Preprocessing (US-1)
*   **Tool**: fMRIPrep (Container: `poldracklab/fmriprep:23.1.0`).
*   **Protocol**: HCP-style (Motion correction, ICA-AROMA, normalization to MNI152, nuisance regression: WM, CSF, Global Signal).
*   **ROI Definition**: Schaefer 200 Parcellation (Yeo-7 networks).
*   **Output**: 200xT BOLD time series per subject.

### B. Topology Computation (US-2)
*   **Connectivity**: Pearson correlation of time series (200x200 symmetric matrix).
*   **Metrics**:
    1.  **Modularity**: Louvain algorithm (fixed seed `42` for reproducibility).
    2.  **Characteristic Path Length**: Mean shortest path. *Handling*: If graph is disconnected, value is set to `NaN`.
    3.  **Clustering Coefficient**: Global average.
    4.  **Global Efficiency**: Inverse of path length.
    5.  **Small-Worldness**: Ratio of clustering to path length relative to random graphs.
*   **Collinearity Check & Reduction**: The five graph metrics are mathematically interdependent (e.g., global efficiency is the inverse of path length). To avoid spurious correlations and reduce degrees of freedom:
    *   **PCA Dimensionality Reduction**: We will perform Principal Component Analysis (PCA) on the standardized metrics.
    *   **Component Extraction**: The first few components (e.g., PC1, PC2) that explain >80% of the variance will be retained. The number of components is dynamic (2 or 3) based on the variance threshold.
    *   **Labeling**: The components will be dynamically labeled (e.g., "Integration", "Segregation") based on their loadings on the original metrics, rather than hardcoding labels to indices.
    *   **Analysis**: Correlation analysis will be performed on these orthogonal components, not the raw collinear metrics.

### C. Correlation Analysis (US-3)
*   **Test**: Pearson (or Spearman if non-normal) correlation between each PCA component and 2 illusion scores.
*   **Correction**: **Benjamini-Hochberg (FDR)** at q < 0.05.
*   **Effect Size**: Pearson's r and Cohen's d (for group splits if applicable) will be calculated for *all* pairs, regardless of significance.
*   **Framing**: All results are framed as **associational**. No causal claims are made.
*   **Testing Strategy**: Unit tests will use synthetic data with injected correlations to verify the *arithmetic* of the correlation scripts. However, the **scientific hypothesis** is tested ONLY on the real data from OpenNeuro ds004285. Synthetic data is not used for the final statistical inference.

### D. Power & Sample Size
*   **Constraint**: The study targets the full cohort available in OpenNeuro ds.
*   **Limitation**: If the available sample size provides limited power to detect small effect sizes (r < 0.3), the plan explicitly acknowledges this limitation in the final report. A post-hoc power analysis will be included.

## 3. Compute Feasibility (CPU-Only)

*   **Hardware**: GitHub Actions Free Tier (2 CPU, 7GB RAM).
*   **Strategy**:
    *   **fMRIPrep**: The CI job will run on a **subset of 5 subjects** to validate the pipeline within the 6-hour limit. The code is designed to process subjects sequentially (streaming) to minimize RAM usage. Full batch processing (50 subjects) is acknowledged to exceed the CI time limit and is intended for execution on local hardware or a cloud VM, but the *pipeline logic* remains valid.
    *   **Graph Metrics & PCA**: `bctpy`, `networkx`, and `scikit-learn` are CPU-optimized. Processing a 200x200 matrix and PCA on 50 subjects is trivial (<1s per subject).
    *   **Memory**: Time-series data (200x1000 timepoints) fits easily in RAM.
    *   **No GPU**: No deep learning models are used.

## 4. Decision Rationale

*   **Why OpenNeuro ds004285?** It is the only verified source that contains both the required fMRI data and the specific visual illusion behavioral data for the same subjects, solving the "no verified source" problem.
*   **Why fMRIPrep?** It is the gold standard for reproducible preprocessing (Constitution Principle VI).
*   **Why Schaefer 200?** It offers a validated, reproducible parcellation with good coverage of visual and association cortices relevant to illusion processing.
*   **Why PCA?** The five graph metrics are definitionally collinear. PCA reduces them to orthogonal components, preventing spurious correlations and providing a more robust test of the "topology" construct.
*   **Why FDR?** With multiple tests (components x illusions), the family-wise error rate is high. FDR controls false discoveries without being as conservative as Bonferroni.