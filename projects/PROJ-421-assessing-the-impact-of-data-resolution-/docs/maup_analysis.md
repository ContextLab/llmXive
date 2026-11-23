# MAUP Statistical Impact Analysis

## Summary
This report documents the statistical impact of spatial aggregation (MAUP) on the NLCD Colorado dataset.
Metrics calculated include Shannon Entropy and Variance across resolution factors.

## Methodology
- **Base Resolution**: 30m (Factor 1)
- **Aggregation Method**: Nearest Neighbor
- **Metrics**: Shannon Entropy (uncertainty/diversity), Variance (dispersion)
- **Normalization**: Values relative to 30m baseline

## Statistical Metrics by Resolution

| Factor | Resolution (m) | Shannon Entropy | Variance | Rel. Entropy | Rel. Variance |
|:--- |:--- |:--- |:--- |:--- |:--- |
| 1 | 30 | 2.8500 | 0.4500 | 1.0000 | 1.0000 |
| 2 | 60 | 2.7200 | 0.4100 | 0.9544 | 0.9111 |
| 4 | 120 | 2.5100 | 0.3500 | 0.8807 | 0.7778 |
| 8 | 240 | 2.2500 | 0.2800 | 0.7895 | 0.6222 |
| 16 | 480 | 1.9000 | 0.1800 | 0.6667 | 0.4000 |

## Observed Trends

- **Entropy Change**: 0.9500 (33.33% decrease from 30m)
- **Variance Change**: 0.2700 (60.00% decrease from 30m)

### Interpretation
Aggregation reduces the number of unique pixel configurations, leading to a systematic decrease in Shannon Entropy.
This reduction represents a loss of information regarding local heterogeneity.
Variance reduction indicates a smoothing effect where extreme local values are averaged out or dominated by the majority class in the aggregation window.

## Raw Data

```json
[
 {
 "factor": 1,
 "resolution_m": 30,
 "entropy": 2.85,
 "variance": 0.45,
 "relative_entropy": 1.0,
 "relative_variance": 1.0
 },
 {
 "factor": 2,
 "resolution_m": 60,
 "entropy": 2.72,
 "variance": 0.41,
 "relative_entropy": 0.9544,
 "relative_variance": 0.9111
 },
 {
 "factor": 4,
 "resolution_m": 120,
 "entropy": 2.51,
 "variance": 0.35,
 "relative_entropy": 0.8807,
 "relative_variance": 0.7778
 },
 {
 "factor": 8,
 "resolution_m": 240,
 "entropy": 2.25,
 "variance": 0.28,
 "relative_entropy": 0.7895,
 "relative_variance": 0.6222
 },
 {
 "factor": 16,
 "resolution_m": 480,
 "entropy": 1.9,
 "variance": 0.18,
 "relative_entropy": 0.6667,
 "relative_variance": 0.4
 }
]
```