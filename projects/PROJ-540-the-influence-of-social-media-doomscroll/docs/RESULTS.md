# Results Summary

## Executive Summary
This document summarizes the findings of the analysis on the influence of social media doomscrolling on anticipatory anxiety.

## Key Findings
- **Correlation**: A significant positive correlation was observed between news exposure frequency and anxiety scores.
- **Regression**: The multiple linear regression model indicates that `news_exposure_freq` is a significant predictor of `anxiety_score`, even after controlling for `baseline_anxiety`, `age`, and `gender`.
- **Robustness**: The relationship holds strong in the high-engagement subset, confirming the robustness of the finding.

## Limitations
- **Causality**: This study is correlational; causal inferences cannot be made.
- **Proxy Measures**: `anxiety_score` may be a proxy for general anxiety rather than strictly anticipatory anxiety.
- **Sample Size**: The analysis is limited by the available public dataset size.

## Data Artifacts
- **Cleaned Data**: `data/processed/analysis_data.csv`
- **Regression Results**: `outputs/regression_results.json`
- **Correlation Results**: `outputs/correlation_results.json`
- **Robustness Results**: `outputs/robustness_results.json`
- **Visualizations**: `outputs/plot.png`, `outputs/robustness_comparison.png`
- **Final Report**: `outputs/final_report.md`

## Next Steps
- Replicate with longitudinal data to establish causality.
- Refine anxiety measures to specifically target anticipatory anxiety.
- Expand the dataset to include more diverse demographics.
