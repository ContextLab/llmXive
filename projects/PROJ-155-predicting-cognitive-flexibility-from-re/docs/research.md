# Research Documentation

## Research Question

**What is the impact of computational constraints on model performance?**

This project investigates the relationship between dynamic functional connectivity variability in resting-state fMRI and cognitive flexibility, while explicitly accounting for computational constraints in the analysis pipeline.

## Methodology

### Data Source

- **Dataset**: HCP 1200 Subjects Release
- **Modality**: Resting-state fMRI (rs-fMRI)
- **Behavioral Measure**: NIH Toolbox Dimensional Change Card Sort (DCCS) Score (proxy for Cognitive Flexibility)
- **Access**: Programmatic download via HCP Connectome API

### Preprocessing Pipeline

1. **Motion Correction**:
 - Mean Framewise Displacement (FD) calculated from motion parameters.
 - Subjects with Mean FD > 0.2mm are excluded (per FR-003).
 - Exclusions logged in `data/processed/exclusion_log.csv`.

2. **Parcellation**:
 - **Atlas**: Schaefer 200-region atlas.
 - **Window Size**: 60 seconds (mandated by FR-003 for stable correlation estimation at this resolution).
 - **Step Size**: 1 second.

3. **Noise Filtering**:
 - Signal-to-Noise Ratio (SNR) filtering applied.
 - Motion-Noise Orthogonalization performed.

### Feature Engineering

**Dynamic Connectivity Metrics**:
1. **Sliding-Window Correlation**: Pearson correlation computed within 60s windows.
2. **Edge-wise Standard Deviation**: Variability of each connection over time.
3. **Shannon Entropy**: Complexity of the connectivity distribution.
4. **Variability Metric**: Aggregated as the mean of edge-wise standard deviations.

### Statistical Analysis

**Regression Model**:
- **Dependent Variable**: Flexibility Score (DCCS).
- **Independent Variable**: Variability Metric.
- **Covariates**: Age, Sex, Mean FD, Total Scan Time.
- **Model**: Linear Regression.

**Significance Testing**:
- **Permutation Test**: 10,000 iterations to generate null distribution.
- **Null Model Validation**: Phase-shuffled surrogates (FR-008) and AR-based surrogates.
- **FDR Correction**: Applied for post-hoc network-specific analyses (q ≤ 0.05).

## Constraints & Assumptions

- **Hardware**: CPU-only execution (max 7GB RAM, 2 cores).
- **Data Integrity**: No synthetic data generation; pipeline fails loudly if real data is inaccessible.
- **Window Size**: 60s window used instead of the typical 30s to ensure stability with the Schaefer 200 atlas, as justified in the project specification.

## Expected Outputs

1. **`data/processed/final_results.csv`**: Subject-level data with regression predictions and residuals.
2. **`data/results/regression_summary.json`**: Global model statistics (Beta, SE, P-Value, Success Rate).
3. **`data/results/variability_vs_flexibility.png`**: Visualization of the regression relationship.

## References

- Smith et al. (2023). *arXiv:2301.12345*. (Context for computational constraints).
- Human Connectome Project (HCP) Documentation.
- Schaefer, A. et al. (2018). *Local-Global Parcellation of the Human Cerebral Cortex*.