# Methodology Documentation

## Research Question

Do topological properties of structural brain networks derived from diffusion MRI predict the prevalence, stability, and switching speed of recurrent activity patterns?

**Note**: All findings are framed as "associational" (correlational) only. No causal claims are made.

## Data Source

**HCP 1200 Subjects Dataset** (OpenNeuro ds000224)
- Diffusion MRI (dMRI) for structural connectivity
- Resting-state fMRI for functional connectivity

Data is downloaded programmatically at runtime. No synthetic data is used.

## Structural Network Construction

1. **Tractography**: Fiber tracts derived from dMRI
2. **Parcellation**: Brain regions defined by an atlas (e.g., AAL)
3. **Adjacency Matrix**: Edge weights = number of streamlines between regions
4. **Thresholding**: Apply density threshold to ensure sparsity < 90%

### Graph Metrics

- **Global Efficiency**: Inverse of average shortest path length
- **Average Clustering Coefficient**: Local interconnectedness
- **Modularity**: Degree of community structure

## Dynamic Functional Connectivity

1. **Sliding Window**: 30 TR window, 1 TR step
2. **Correlation**: Pearson correlation within each window
3. **Concatenation**: All windows across all subjects concatenated
4. **LOO K-Means**: k=5 clusters, computed with subject left out

### Dynamic Metrics

- **Visited States**: Number of unique states occupied
- **Mean Dwell Time**: Average duration in each state

## Correlation Analysis

1. **Normality Test**: Shapiro-Wilk (α=0.05)
 - Normal → Pearson correlation
 - Non-normal → Spearman correlation
2. **Correlation**: Pairwise between structural and dynamic metrics
3. **FDR Correction**: Benjamini-Hochberg (q=0.05)

## Sensitivity Analysis

### Window Length Sensitivity
- Baseline: 30 TR
- Sensitivity: 20 TR
- Metric: Absolute difference in correlation coefficients

### Density Threshold Sensitivity
- Baseline: Configured threshold
- Variation: ±5%
- Metric: Stability of graph metrics

## Computational Constraints

- **CPU-only**: No GPU acceleration
- **Memory**: ~7 GB RAM, ~14 GB disk
- **Streaming**: Large datasets processed in chunks

## Validation

- **Unit Tests**: Individual functions (structural, functional, correlation)
- **Integration Tests**: Single-subject pipeline, full correlation analysis
- **Schema Validation**: Output files match `contracts/output.schema.yaml`
- **Language Audit**: No causal language in reports

## Limitations

- Tractography limitations (false positives/negatives)
- Window length arbitrariness
- Association does not imply causation
