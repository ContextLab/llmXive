# Research Plan: The Impact of Aggregate Negative News Publication Volume on Anticipatory Anxiety

## Summary
This research project investigates the correlation between aggregate negative news publication volume and anticipatory anxiety levels, as measured by search trends. We aim to determine if spikes in negative news coverage precede increases in anxiety-related search queries, using Granger causality tests with fixed-sweep lags and Bonferroni correction to ensure statistical rigor.

## Technical Context
The analysis relies on time-series data from GDELT (Global Database of Events, Language, and Tone) for news volume and Google Trends for anxiety-related search queries. Data preprocessing includes alignment to daily resolution, stationarity checks via ADF tests, and z-score normalization. Statistical analysis involves Pearson/Spearman correlation, Granger causality tests with lags {1, 2, 3, 7, 14}, and sensitivity analysis.

**Governance Note**: Per Spec FR-005 and SC-002, the methodology requires fixed-sweep lags including short-term intervals and Bonferroni-corrected alpha (0.01). The Plan's previous mention of AIC/BIC and 'no Bonferroni' is overridden by this Spec requirement.

## Data Sources
- **GDELT**: Event counts for negative sentiment events (EventCount metric).
- **Google Trends**: Search volume for keywords "anticipatory anxiety" and "worry about future".

## Methodology
1. **Data Acquisition**: Fetch historical data from GDELT and Google Trends.
2. **Preprocessing**: Align timestamps, ensure stationarity (ADF test + differencing), normalize data.
3. **Statistical Analysis**: Compute correlations, run Granger causality tests with fixed-sweep lags, apply Bonferroni correction.
4. **Reporting**: Generate visualizations and a final PDF report with proxy acknowledgments and causality disclaimers.

## Constraints
- **CPU-Only**: All computations must run on CPU (no GPU/CUDA).
- **Data Integrity**: Use real data only; no synthetic or placeholder datasets.
- **Statistical Rigor**: Fixed-sweep lags {1, 2, 3, 7, 14} and Bonferroni-corrected alpha (0.01) as mandated by Spec FR-005/SC-002.

## Deliverables
- Raw and processed CSV files in `data/raw/` and `data/processed/`.
- Analysis report in `data/reports/analysis_report.pdf`.
- Validation scripts and test suites.