# Research Document: The Impact of Aggregate Negative News Publication Volume on Anticipatory Anxiety

## Summary

This research project investigates the correlation between aggregate negative news publication volume and anticipatory anxiety levels. The study leverages time-series data from GDELT (Global Database of Events, Language, and Tone) for negative news volume and Google Trends for anxiety-related search queries ("anticipatory anxiety", "worry about future"). The primary objective is to determine if spikes in negative news consumption precede increases in anxiety-related search behavior, suggesting a causal or strongly correlated relationship.

The methodology adheres to strict statistical rigor, employing fixed-sweep lag analysis and Bonferroni-corrected significance thresholds to minimize Type I errors. The project aims to provide empirical evidence on the psychological impact of media consumption patterns.

## Technical Context

The analysis pipeline is designed to run on standard CPU infrastructure (2-core, ≤7GB RAM) without GPU acceleration. The workflow consists of three main phases:

1. **Data Acquisition**: Retrieval of historical time-series data from GDELT (EventCount of negative sentiment events) and Google Trends (search interest indices).
2. **Preprocessing**: Data cleaning, timestamp alignment to daily resolution, handling of missing values via linear interpolation (preserving zero-event counts), and stationarity enforcement using the Augmented Dickey-Fuller (ADF) test and differencing.
3. **Statistical Analysis**: Computation of Pearson and Spearman correlation coefficients, followed by Granger Causality tests.

**Methodological Constraints & Governance**:
Per Specification FR-005 and SC-002, the analysis utilizes a **fixed-sweep lag window** of {1, 2, 3, 7, 14} days. Significance is determined using a **Bonferroni-corrected alpha threshold** of 0.01 (derived from 0.05/5 tests). This approach overrides any previous documentation suggesting AIC/BIC lag selection or the omission of Bonferroni corrections. The fixed-sweep method ensures a transparent, reproducible evaluation of short-to-medium term causal effects.

Data integrity is maintained through schema validation (JSON Schema) and checksum verification at each pipeline stage. All outputs are generated in standardized CSV and PDF formats for reporting.

## Data Sources

- **GDELT**: Global Database of Events, Language, and Tone. Metric: `EventCount` for negative sentiment events.
- **Google Trends**: Search interest indices for keywords "anticipatory anxiety" and "worry about future".

## Statistical Methods

- **Correlation**: Pearson and Spearman rank correlation coefficients.
- **Stationarity**: Augmented Dickey-Fuller (ADF) test. Non-stationary series are differenced until stationary (p < 0.05).
- **Causality**: Granger Causality test with fixed lags {1, 2, 3, 7, 14}.
- **Significance**: Bonferroni correction applied (α = 0.01).

## Expected Outcomes

The project will produce:
- Processed, aligned time-series datasets.
- Correlation matrices with p-values.
- Granger causality test results indicating significant lags.
- A comprehensive PDF report containing visualizations and statistical findings.