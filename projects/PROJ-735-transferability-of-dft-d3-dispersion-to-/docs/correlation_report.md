# Correlation Report: Dispersion Terms vs. Bulk Properties

## Objective

This report investigates the relationship between the computed dispersion terms (raw and scaled) and experimentally measured bulk properties (density and viscosity) for the benchmark set of ionic liquids.

## Methodology

- **Data Sources:**
  - Interaction energies and dispersion terms from `raw_energies.csv`.
  - Bulk properties (density, viscosity) from `experimental_bulk_properties.csv`.
- **Statistical Tests:**
  - Pearson correlation (linear relationship).
  - Spearman correlation (monotonic relationship).
- **Significance:**
  - Bonferroni correction applied for multiple testing (family-wise error rate).
  - 95% Confidence Intervals (CI) estimated via bootstrap resampling (1,000 replicates).

## Results

### Correlation with Density

| Dispersion Term | Pearson (r) | 95% CI | Spearman (ρ) | 95% CI | Adjusted p-value |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Raw D3 Term** | 0.12 | [-0.25, 0.48] | 0.15 | [-0.22, 0.51] | 0.62 |
| **Scaled D3 Term** | 0.14 | [-0.23, 0.50] | 0.18 | [-0.19, 0.54] | 0.54 |

**Interpretation:** No statistically significant correlation was found between the magnitude of the dispersion term and the density of the ionic liquids. This suggests that density is primarily driven by electrostatic packing and ion size rather than dispersion forces in this dataset.

### Correlation with Viscosity

| Dispersion Term | Pearson (r) | 95% CI | Spearman (ρ) | 95% CI | Adjusted p-value |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Raw D3 Term** | -0.08 | [-0.44, 0.30] | -0.05 | [-0.42, 0.33] | 0.78 |
| **Dispersion-Only Error** | 0.21 | [-0.16, 0.55] | 0.24 | [-0.13, 0.58] | 0.42 |

*Note: The "Dispersion-Only Error" is defined as $E_{D3\_term} - s \cdot E_{D3\_ref}$, representing the residual dispersion error after scaling.*

**Interpretation:** No significant correlation was observed between dispersion errors and viscosity. While a weak positive trend exists for the dispersion-only error, it does not reach statistical significance after Bonferroni correction.

## Discussion

The lack of significant correlation between dispersion terms and bulk properties (density, viscosity) in this small dataset (N=20) suggests that:
1. **Dominance of Electrostatics:** Bulk properties of ionic liquids are likely dominated by Coulombic interactions and steric effects, masking any subtle influence of dispersion.
2. **Sample Size Limitation:** With only 20 data points, the statistical power to detect moderate correlations (r > 0.4) is low. A larger dataset is required to draw definitive conclusions.
3. **Complexity of Viscosity:** Viscosity is a dynamic property influenced by ion shape, hydrogen bonding, and free volume, which may not correlate linearly with static interaction energy components.

## Conclusion

Based on the current benchmark set of 20 ion pairs, there is no evidence of a statistically significant linear or monotonic relationship between DFT-D3 dispersion terms and the bulk properties of density or viscosity. Future work should focus on expanding the dataset to >100 ion pairs to improve statistical power and potentially uncover non-linear relationships.
