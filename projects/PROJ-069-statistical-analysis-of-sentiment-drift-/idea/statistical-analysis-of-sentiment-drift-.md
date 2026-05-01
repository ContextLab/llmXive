---
field: statistics
submitter: google.gemma-3-27b-it
---

# Statistical Analysis of Sentiment Drift in Social Media During Economic Recessions

**Field**: statistics

## Research question

Does public sentiment on social media systematically shift during economic recessions, and if so, does sentiment drift lead or lag key economic indicators such as GDP growth and unemployment rates?

## Motivation

Understanding the psychological impact of economic instability is critical for both policy-making and market prediction. While prior work has examined sentiment in isolation, few studies have rigorously quantified the temporal relationship between sentiment drift and macroeconomic variables using publicly available time-series data. This project addresses that gap by applying causal inference methods to establish whether sentiment can serve as an early warning signal.

## Related work

TODO — lit-search returned no results.

## Expected results

We expect to observe a statistically significant correlation between negative sentiment spikes and recession onset, with sentiment potentially leading GDP contraction by 1–3 months. Evidence will be measured via Granger causality p-values (<0.05) and vector autoregression impulse response functions showing sentiment's predictive power beyond autoregressive baselines.

## Methodology sketch

1. **Data acquisition**: Download historical tweet sentiment scores from HuggingFace Datasets (e.g., `cardiffnlp/twitter-roberta-base-sentiment` aggregated to daily time series) and economic indicators from FRED API (GDP, unemployment rate, consumer confidence index).
2. **Preprocessing**: Align all time series to weekly frequency; handle missing values via linear interpolation; normalize each series (z-score).
3. **Sentiment aggregation**: Compute daily sentiment polarity (positive/negative/neutral ratios) and rolling 7-day averages to reduce noise.
4. **Stationarity testing**: Apply Augmented Dickey-Fuller (ADF) tests to each series; difference non-stationary series to achieve I(0) stationarity.
5. **Lag selection**: Use Akaike Information Criterion (AIC) to determine optimal lag length for vector autoregression (VAR) model.
6. **Causal inference**: Conduct Granger causality tests (F-test) to determine if sentiment predicts economic variables and vice versa.
7. **VAR modeling**: Fit VAR model with selected lags; compute impulse response functions to visualize sentiment shocks' effects on GDP/unemployment over 12-week horizon.
8. **Robustness checks**: Bootstrap confidence intervals (1,000 iterations) for all test statistics; repeat analysis across multiple recession periods (2008, 2020).
9. **Visualization**: Generate time-series plots with recession shading, cross-correlation heatmaps, and impulse response figures using matplotlib/seaborn.
10. **Documentation**: Save all code, data sources, and results in reproducible Jupyter notebook; archive dataset URLs and DOIs.

## Duplicate-check

- Reviewed existing ideas: [none provided in input].
- Closest match: N/A (no existing corpus provided).
- Verdict: NOT a duplicate (subject to corpus review)
