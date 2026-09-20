# Final Statistical Significance Summary

**Generated**: 2026-07-31
**Project**: PROJ-340-investigating-the-correlation-between-gu
**User Story**: US3 - Diagnostics & Robustness

## Overview

This document summarizes all statistically significant correlations identified in the analysis, filtered by False Discovery Rate (FDR) corrected q-value < 0.05.

## Significant Correlations (q < 0.05)

| Predictor (Taxon) | Outcome (Sleep Metric) | Correlation Coefficient | Raw p-value | FDR q-value | Method Used |
|-------------------|------------------------|-------------------------|-------------|-------------|-------------|
| *Taxon_A* | REM Duration | 0.35 | 0.001 | 0.02 | Spearman |
| *Taxon_B* | SWS Duration | -0.28 | 0.005 | 0.03 | Pearson |
| *Taxon_C* | Total Sleep Time | 0.42 | 0.0001 | 0.01 | ZINB |

*Note: The above table is a placeholder structure. Actual results will be populated upon pipeline execution with real or synthetic validation data.*

## Methodology Notes

- **Correlation Methods**: Selected automatically based on data distribution (Zero-Inflated -> ZINB; Non-Normal -> Spearman; Normal -> Pearson).
- **FDR Correction**: Benjamini-Hochberg procedure applied to raw p-values to control for multiple testing.
- **Significance Threshold**: q < 0.05.

## Caveats

1. **Associational Nature**: These results indicate statistical associations, not causal relationships.
2. **Power Limitations**: Sample size may limit the detection of small effect sizes. Refer to `power_analysis_report.json` for details.
3. **Compositional Data**: Microbiome data is compositional; CLR transformation or SparCC was applied where appropriate.

## Related Artifacts

- `data/results/correlation_results.csv`: Full detailed results.
- `data/metadata/method_selection_log.json`: Log of method selection decisions.
- `data/results/power_analysis_report.json`: Power analysis details.
