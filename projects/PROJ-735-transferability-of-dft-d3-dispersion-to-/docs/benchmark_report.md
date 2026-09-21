# Benchmark Report: Transferability of DFT-D3 Dispersion to Ionic Liquids

## Executive Summary

This report presents the results of benchmarking DFT-D3 (B3LYP/def2-TZVP with Becke-Johnson damping and Counterpoise correction) interaction energies against high-level CCSD(T)/CBS reference values for a set of 20 ionic liquid ion pairs. A simple scaling correction was derived to minimize systematic bias, and correlations with bulk properties were analyzed.

**Statistical Power Warning**: The dataset consists of 20 ion pairs, which is significantly below the Spec requirement of ≥100 pairs for robust statistical power. Consequently, the confidence intervals and hypothesis tests presented here are for descriptive purposes only and should not be interpreted as definitive evidence of statistical significance. The results are primarily indicative of trends and systematic biases.

## 1. Raw Energy Metrics

The raw DFT-D3 interaction energies were computed for 20 ion pairs and compared to CCSD(T)/CBS references.

### 1.1 Error Statistics (Raw DFT-D3)

| Metric | Value (kcal/mol) |
|:--- |:--- |
| Mean Absolute Error (MAE) | 2.15 |
| Root Mean Square Error (RMSE) | 2.87 |
| Mean Signed Error (MSE) | -1.92 |
| Mean Squared Error (MSE) | 8.24 |

### 1.2 Bootstrap Confidence Intervals (Raw MAE)

| Metric | Estimate | 95% CI Lower | 95% CI Upper |
|:--- |:--- |:--- |:--- |
| MAE | 2.15 | 1.45 | 3.12 |

*Note: CIs derived from 1,000 bootstrap replicates.*

## 2. Scaling Correction Results

A scalar `s` was optimized to minimize the MAE of the corrected energies (E_corrected = E_base + s * E_D3).

### 2.1 Optimal Scaling Factor

| Parameter | Value |
|:--- |:--- |
| Scaling Factor (`s`) | 1.12 |
| 95% CI Lower | 0.98 |
| 95% CI Upper | 1.28 |

### 2.2 Hypothesis Test

The hypothesis that `s = 1.0` (no scaling needed) was tested.
- **Result**: The 95% confidence interval for `s` [0.98, 1.28] includes 1.0.
- **Conclusion**: We cannot reject the null hypothesis that the default D3 scaling (s=1.0) is adequate for this dataset. However, the point estimate suggests a slight upward adjustment (12%) may reduce bias.

### 2.3 Error Statistics (Scaled DFT-D3)

| Metric | Value (kcal/mol) |
|:--- |:--- |
| Mean Absolute Error (MAE) | 1.98 |
| Root Mean Square Error (RMSE) | 2.65 |
| Mean Signed Error (MSE) | -1.75 |

## 3. Calibration Procedure

**No calibration was performed against ionic liquid data.**
The DFT-D3 parameters (s8, sr, etc.) were used with their standard values derived from neutral organic molecules. The scaling factor `s` derived in this study is a post-hoc correction to the total dispersion term, not a re-parameterization of the D3 model itself. This approach aligns with the Plan's methodology to test transferability without altering the underlying D3 functional form.

## 4. Limitations and Future Work

- **Dataset Size**: The primary limitation is the small dataset size (20 pairs) compared to the Spec's requirement of ≥100. This limits the statistical power of the analysis.
- **Systematic Bias**: The negative Mean Signed Error indicates that DFT-D3 systematically underestimates interaction energies (less negative) compared to CCSD(T)/CBS.
- **Bulk Properties**: Correlation with bulk properties (density, viscosity) is explored in the separate correlation report.

## 5. Conclusion

The DFT-D3 method shows reasonable transferability to ionic liquids, with an MAE of ~2.15 kcal/mol. A simple scaling factor of 1.12 slightly improves the agreement, but the difference is not statistically significant at the 95% level given the small dataset. The results suggest that while DFT-D3 is a useful tool, systematic biases exist that may require system-specific corrections or more advanced treatments for high-precision applications.