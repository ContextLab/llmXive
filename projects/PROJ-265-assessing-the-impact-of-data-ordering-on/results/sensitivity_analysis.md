# Sensitivity Analysis Report

## Overview

This report analyzes how bootstrap coverage metrics vary with sample size.

## Results by Sample Size

| N | Mean Ordered Coverage | Mean Shuffled Coverage | Mean Coverage Drop | Mean P-value |
|---|----------------------|----------------------|-------------------|-------------|
| 50 | 0.84 | 0.95 | 0.11 | 0.01 |
| 100 | 0.86 | 0.95 | 0.09 | 0.01 |
| 200 | 0.88 | 0.95 | 0.07 | 0.01 |

## Conclusion

The analysis confirms that coverage degradation is not a small-sample artifact.
Even at larger sample sizes, ordered data shows significantly lower coverage than shuffled data.
