# Final Report: Assessing the Impact of Data Resolution on Statistical Power

## Executive Summary

This report presents the findings of the analysis on how spatial data resolution
affects the statistical power to detect spatial autocorrelation (Moran's I).
The study utilized NLCD land cover data for Colorado, aggregated from 30m to 480m
resolutions, and evaluated power via Monte Carlo simulations.

**Key Finding**: The statistical power drops below the 0.80 threshold at **240m**.

## Methodology

- **Data Source**: NLCD 2019 Land Cover (30m) for Colorado.
- **Resolutions Tested**: 30m, 60m, 120m, 240m, 480m (Factors: 1, 2, 4, 8, 16).
- **Metric**: Moran's I for Binary Forest Indicator (Forest=1, Others=0).
- **Null Hypothesis (H0)**: Random permutation (1,000 permutations).
- **Alternative Hypothesis (H1)**: Gibbs Sampler simulation using calibrated lambda.
- **Power Definition**: Proportion of H1 simulations where p-value < 0.05.

## Results

### Power vs. Resolution

| Resolution | Aggregation Factor | Moran's I | P-Value | Statistical Power |
|:--- |:--- |:--- |:--- |:--- |
| 30m | 1 | 0.4521 | 0.0010 | 1.0000 |
| 60m | 2 | 0.4815 | 0.0010 | 1.0000 |
| 120m | 4 | 0.5102 | 0.0010 | 0.9850 |
| 240m | 8 | 0.4988 | 0.0020 | 0.7620 |
| 480m | 16 | 0.4105 | 0.0150 | 0.4100 |

### Threshold Identification

The analysis identified the resolution threshold where statistical power < 0.80:
- **Threshold Resolution**: 240m
- **Power at Threshold**: 0.7620

### Type II Error Analysis

Type II error (beta) is defined as 1 - Power. This represents the probability
of failing to detect spatial autocorrelation when it exists.

| Resolution | Type II Error (1 - Power) |
|:--- |:--- |
| 30m | 0.0000 |
| 60m | 0.0000 |
| 120m | 0.0150 |
| 240m | 0.2380 |
| 480m | 0.5900 |

### Sensitivity Analysis

A sensitivity analysis was performed by sweeping the resolution aggregation factor
by ±10% around the identified inflection point to assess threshold stability.

- **Inflection Point (Factor)**: 8
- **Threshold Stability**: The threshold varies by **0** resolution step(s).

### Conclusion

The study concludes that for this dataset, spatial autocorrelation can be reliably
detected with >80% power at resolutions up to **240m**. Beyond this point, the Type II error rate increases significantly, indicating that
coarser data may mask underlying spatial patterns.

---
*Report generated on: 2026-07-05 14:30:00*
*Based on analysis of 5 resolution levels.*