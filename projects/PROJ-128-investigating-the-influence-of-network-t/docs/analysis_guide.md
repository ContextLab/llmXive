# Analysis Guide

This document details the methodological choices and statistical procedures implemented in this pipeline.

## Structural Connectivity Analysis

### Graph Construction
Structural connectivity matrices are derived from diffusion MRI tractography. Edge weights represent streamline counts or confidence scores.

### Thresholding
To ensure comparability across subjects, we apply **proportional density thresholding**. We retain the top X% of edges (where X = 10%, 15%, 20%) and discard the rest. This sensitivity analysis is performed to verify robustness (FR-008).

### Metrics
- **Global Efficiency**: Inverse of the average shortest path length.
- **Clustering Coefficient**: Degree to which nodes tend to cluster together.
- **Modularity**: Strength of division of a network into modules.

## Functional Connectivity Analysis

### Sliding Window Correlation
Dynamic functional connectivity is computed using a sliding window approach:
- **Window Length**: 30 TR (baseline), with validation at 20, 25, 35 TR.
- **Step Size**: 1 TR.

### State Extraction (LOO K-Means)
To avoid circularity, we use **Leave-One-Out K-Means**:
1. For subject *i*, centroids are computed from the windowed correlations of all other subjects (*j != i*).
2. Subject *i*'s windows are then assigned to these external centroids.
3. This ensures that the state definitions are independent of the subject's own data.

### Dynamic Metrics
- **Mean Dwell Time**: Average duration spent in each state.
- **Number of Visited States**: Count of unique states visited.

## Statistical Analysis

### Normality Testing
We test the distribution of metrics using the **Shapiro-Wilk test** (α=0.05).
- If p < 0.05: Use **Spearman's rank correlation**.
- Else: Use **Pearson's correlation**.

### Multiple Comparison Correction
All p-values are corrected using the **Benjamini-Hochberg FDR** procedure (q=0.05).

## Robustness & Sensitivity

### Tractography Noise
To address concerns about false-positive edges in dMRI, we vary the **tractography confidence threshold** (0.0 to 0.8). We re-run the correlation analysis at each threshold to determine if findings are driven by noisy edges.

### Associational Framing
All reports are automatically audited to ensure language remains "associational" (e.g., "predicts" is replaced with "is associated with") to comply with the project's scope constraints.
