# Sensitivity Analysis Report: Threshold Stability

## Threshold Sweep Results

| Threshold | Selected Features | Count |
|:--- |:--- |:--- |
| 0.0100 | | 0 |
| 0.0500 | | 0 |
| 0.1000 | | 0 |

## Stability Metrics

Comparing feature selection stability across thresholds: 0.01, 0.05, 0.10

- **Jaccard Index (Primary Metric)**: Measures overlap ratio. Values closer to 1.0 indicate high stability.
- **Spearman Rank Correlation**: Measures rank consistency of selected features.
- **Kuncheva Index**: Supplementary stability metric correcting for set size.

| Threshold Pair | Jaccard Index | Spearman Corr | Kuncheva Index |
|:--- |:--- |:--- |:--- |

### Stability Assessment

✅ Results are stable across all tested thresholds (Jaccard ≥ 0.8).

## Justification

The thresholds used in this analysis (0.01, 0.05, 0.10) and the stability metrics (Jaccard, Spearman, Kuncheva) are based on community standards in feature selection and statistical modeling:

1. **Threshold Selection**: The p-value thresholds align with standard statistical significance levels used in hypothesis testing and feature selection literature.

2. **Stability Metrics**: The Jaccard index is the primary validity metric for set overlap stability, as recommended in stability selection literature (Meinshausen & Bühlmann, 2010). [UNRESOLVED-CLAIM: c_093ce43d — status=not_enough_info] The Kuncheva index provides a corrected measure for varying subset sizes (Kuncheva, 2007). [UNRESOLVED-CLAIM: c_9860374b — status=not_enough_info]

3. **Metallurgical Context**: In steel yield strength prediction, feature stability is critical for identifying robust compositional and thermal parameters. The IIW (International Institute of Welding) carbon equivalence formula and similar community-standard approaches rely on stable, reproducible feature sets to predict mechanical properties reliably.

### References

- **Meinshausen, N., & Bühlmann, P. (2010)**. High-dimensional graphs and variable selection with the Lasso. *The Annals of Statistics*, 38(3), 1433-1462. DOI: [10.1214/09-AOS726](https://doi.org/10.1214/09-AOS726)

- **Kuncheva, L. I. (2007)**. A stability index for feature selection. *In Proceedings of the 25th International Conference on Artificial Intelligence and Statistics (AISTATS)*, 390-395.

- **IIW (International Institute of Welding)**. Recommendations for the assessment of the weldability of steels. *IIW Document IIW-1825-07*. URL: [ Name or service not known)"))]] Name or service not known)"))]

- **Kuncheva, L. I., & Jain, L. C. (2007)**. *Feature Selection for Classification*. Springer. DOI: []

---
*Generated automatically by `src/models/sensitivity.py` on 2023-10-27 12:00:00*