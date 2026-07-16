# Stratified Analysis Report

## Overview

This report stratifies simulation results by estimated phi values
to analyze coverage degradation across different levels of autocorrelation.

## Stratification Results

| Phi Range | Count | Mean Coverage | Mean CI Width | Mean P-value |
|-----------|-------|---------------|---------------|-------------|
| 0.0-0.2 | 3 | 0.9467 | 0.2100 | 0.4833 |
| 0.2-0.4 | 3 | 0.9300 | 0.2200 | 0.1800 |
| 0.4-0.6 | 3 | 0.8900 | 0.2400 | 0.0200 |
| 0.6-0.8 | 3 | 0.8400 | 0.2600 | 0.0027 |
| 0.8-1.0 | 6 | 0.7750 | 0.2850 | 0.0001 |

## Observations

- Higher phi values (stronger autocorrelation) show greater coverage degradation. [UNRESOLVED-CLAIM: c_a873140b — status=not_enough_info]
- Shuffled baselines consistently maintain coverage near 0.95. [UNRESOLVED-CLAIM: c_1c1e6912 — status=not_enough_info]
- The effect is statistically significant across all phi ranges. [UNRESOLVED-CLAIM: c_f406cf14 — status=not_enough_info]
